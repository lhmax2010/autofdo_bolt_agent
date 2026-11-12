"""Serial two-stage scheduling of the unchanged 6946344 simulation primitives.

The original lock remains intact. This additive scheduler is separately hashed
and pushed before execution. No statistical calculation is replaced.
"""
import argparse
import collections
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import time

import interval_simulation as base

WORK=base.WORK
ROOT=WORK/'temp/interval-simulation/formal-001'
EVIDENCE=base.EVIDENCE/'phased'
SCHEDULER_LOCK=EVIDENCE/'scheduler-lock.json'
OLD_LOCK_COMMIT='6946344b0fae4c8e851fb71d1abd46abcca71029'
GIT=base.GIT


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    with temporary.open('wb') as f:
        f.write(base.encoded(value)+b'\n');f.flush();os.fsync(f.fileno())
    temporary.replace(path)


def command(args):
    return subprocess.check_output(GIT+args,cwd=WORK)


def verified(pushed=True):
    manifest,lock=base.verify_lock(pushed=pushed)
    original=command(['show',OLD_LOCK_COMMIT+':'+str(base.LOCK.relative_to(WORK))])
    if original!=base.LOCK.read_bytes():raise ValueError('original_lock_changed')
    extra=json.loads(SCHEDULER_LOCK.read_text())
    for name,sha in extra['files'].items():
        if base.file_sha(WORK/name)!=sha:raise ValueError('scheduler_SHA_changed:'+name)
        if pushed and hashlib.sha256(command(['show','origin/main:'+name])).hexdigest()!=sha:
            raise ValueError('scheduler_not_pushed:'+name)
    if pushed and command(['show','origin/main:'+str(SCHEDULER_LOCK.relative_to(WORK))])!=SCHEDULER_LOCK.read_bytes():
        raise ValueError('scheduler_lock_not_pushed')
    return manifest,lock,extra


def selected_rows(manifest,phase):
    return [r for r in manifest['scenarios'] if phase=='envelope' or r['role']=='acceptance']


def repeats(row,phase):
    return row['t_repeats'] if phase=='acceptance' else row['envelope_repeats']


def new_counts(phase):
    kinds=['t'] if phase=='acceptance' else ['t','percentile','envelope']
    return {k:collections.Counter(covered=0,equivalent=0,degenerate=0,no_interval=0) for k in kinds}


def accumulate(counts,decision):
    for kind,values in decision.items():counts[kind].update({k:int(v) for k,v in values.items()})


def validate_result(row,phase,result):
    n=repeats(row,phase)
    if result['parameters']!=row or result['seed']!=row['seed'] or result['phase']!=phase or result['repeats']!=n:
        raise ValueError('incomplete_or_parameter_mismatch:'+row['id'])
    counts=result['counts'];expected=set(new_counts(phase))
    if set(counts)!=expected:raise ValueError('statistic_kinds_changed')
    for kind,c in counts.items():
        if set(c)!=set(new_counts(phase)[kind]) or any(type(v) is not int or not 0<=v<=n for v in c.values()):
            raise ValueError('invalid_event_counts')
        if result['statistics'][kind]!=base.summarize(c,n):raise ValueError('summary_counts_mismatch')
    if phase=='acceptance' and result['passed']!=base.acceptance(row,counts['t'],n):
        raise ValueError('acceptance_decision_mismatch')
    return True


def load_complete(out,rows,phase):
    # A torn final append is never counted. Preserve its exact bytes first.
    path=out/'results.jsonl'
    if path.exists():
        raw=path.read_bytes()
        if raw and not raw.endswith(b'\n'):
            split=raw.rfind(b'\n')+1;prefix,tail=raw[:split],raw[split:]
            previous='0'*64
            for line in prefix.splitlines():
                entry=json.loads(line);sha=entry.pop('result_sha256')
                if base.digest(entry)!=sha or entry['previous_sha256']!=previous:raise ValueError('corrupted_complete_prefix')
                previous=sha
            backup=out/('interrupted-tail-'+str(time.time_ns())+'.bin');backup.write_bytes(tail)
            with path.open('r+b') as f:f.truncate(split);f.flush();os.fsync(f.fileno())
    results=base.read_results(out);wanted={r['id']:r for r in rows}
    for r in results:
        if r['id'] not in wanted:raise ValueError('unregistered_result')
        validate_result(wanted[r['id']],phase,r)
    return results


def acceptance_summary(rows,results,history=()):
    found={r['id']:r for r in results}
    complete=len(found)==len(results)==len(rows) and set(found)=={r['id'] for r in rows}
    failed=[]
    for row in rows:
        result=found.get(row['id'])
        if result is not None:
            validate_result(row,'acceptance',result)
            if not result['passed']:failed.append(row['id'])
    this_pass=complete and not failed
    old_complete=[r for r in history if r['complete']]
    enabled=this_pass and all(r['quality_equivalence_enabled'] for r in old_complete)
    return dict(phase='acceptance',complete=complete,scenarios=len(results),expected_scenarios=len(rows),
                this_run_passed=this_pass,quality_equivalence_enabled=enabled,failed_scenarios=failed,
                incomplete_scenarios=[r['id'] for r in rows if r['id'] not in found],
                included_in_complete_run_conjunction=complete,previous_complete_runs=old_complete)


class Progress(base.Monitor):
    def __init__(self,out,phase,rows,results):
        self.phase=phase;self.rows=rows;self.results=results;self.last_root_write=0
        pilot=base.read_results(WORK/'temp/interval-simulation/pilot')
        byid={r['id']:r for r in pilot}
        self.costs={r['id']:(byid[r['id']]['timings']['t_seconds']/10000*r['t_repeats'] if phase=='acceptance'
                            else byid[r['id']]['timings']['envelope_seconds']*r['envelope_repeats']) for r in rows}
        super().__init__(out)
        quota,period=map(int,(self.cgpath/'cpu.max').read_text().split())
        if quota!=period:raise ValueError('requires_CPUQuota_100_percent')
    def tick(self,force=False,**current):
        completed={r['id'] for r in self.results}
        current['phase']=self.phase;current['completed_scenarios']=len(completed);current['total_scenarios']=len(self.rows)
        actual=sum(r['elapsed_seconds'] for r in self.results)
        predicted=sum(self.costs[i] for i in completed)
        multiplier=actual/predicted if predicted else 1.0
        remaining=sum(self.costs[r['id']] for r in self.rows if r['id'] not in completed)
        active=current.get('scenario',self.current.get('scenario'))
        rep=current.get('repeat',self.current.get('repeat',0));total=current.get('total',self.current.get('total',1))
        if active not in completed and active in self.costs:remaining-=self.costs[active]*min(1,rep/max(1,total))
        current['estimated_remaining_seconds']=max(0,remaining*multiplier)
        super().tick(force=force,**current)
        now=time.monotonic()
        if force or now>=self.last_root_write+1:
            self.last_root_write=now
            save(ROOT/'progress.json',json.loads((self.out/'progress.json').read_text()))


def perform(row,phase,mon):
    n=repeats(row,phase);rng=random.Random(row['seed'] if phase=='acceptance' else row['envelope_stream'])
    counts=new_counts(phase);start=time.monotonic()
    for i in range(n):
        accumulate(counts,base.evaluate(base.sample(row,rng),row['delta'],envelope=phase=='envelope'))
        if i%100==0 or phase=='envelope':mon.tick(scenario=row['id'],repeat=i+1,total=n)
    result=dict(id=row['id'],phase=phase,seed=row['seed'],parameters=row,repeats=n,counts=counts,
                statistics={k:base.summarize(v,n) for k,v in counts.items()},
                elapsed_seconds=time.monotonic()-start,finished=base.now())
    if phase=='acceptance':result['passed']=base.acceptance(row,counts['t'],n)
    validate_result(row,phase,result)
    return result


def stage2_admission():
    local=ROOT/'acceptance/summary.json'
    summary=json.loads(local.read_text())
    remote_path=str((EVIDENCE/'acceptance-summary.json').relative_to(WORK))
    if command(['show','origin/main:'+remote_path])!=local.read_bytes():raise ValueError('stage1_summary_not_pushed')
    resultpath=EVIDENCE/'acceptance-results.jsonl'
    if command(['show','origin/main:'+str(resultpath.relative_to(WORK))])!=(ROOT/'acceptance/results.jsonl').read_bytes():
        raise ValueError('stage1_results_not_pushed')
    if not summary['complete']:raise ValueError('stage1_not_complete')
    return summary


def run_stage(phase):
    out=ROOT/phase;out.mkdir(parents=True,exist_ok=True)
    results=[];mon=None;start=time.monotonic();status='失败';error=None
    try:
        manifest,lock,extra=verified()
        if phase=='envelope':stage2_admission()
        rows=selected_rows(manifest,phase)
        header=dict(phase=phase,manifest_sha256=base.file_sha(base.MANIFEST),original_lock_sha256=base.file_sha(base.LOCK),
                    scheduler_lock_sha256=base.file_sha(SCHEDULER_LOCK),files=lock['files'],scheduler_files=extra['files'])
        hp=out/'run-header.json'
        if hp.exists() and json.loads(hp.read_text())!=header:raise ValueError('resume_header_changed')
        save(hp,header)
        results=load_complete(out,rows,phase);mon=Progress(out,phase,rows,results)
        for row in rows:
            if row['id'] in {r['id'] for r in results}:continue
            verified()
            results.append(base.append(out,perform(row,phase,mon)))
            mon.tick(force=True,scenario=row['id'],repeat=repeats(row,phase),total=repeats(row,phase))
        if phase=='acceptance':
            ledger=WORK/'temp/interval-simulation/complete-runs.jsonl'
            history=[json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
            for old in history:
                path=Path(old['result_path'])
                if not path.is_relative_to(WORK/'temp') or base.file_sha(path)!=old['results_sha256']:raise ValueError('prior_results_changed')
            history=[h for h in history if Path(h['result_path'])!=out/'results.jsonl']
            summary=acceptance_summary(rows,results,history)
        else:
            first=stage2_admission()
            summary=dict(phase=phase,complete=len(results)==len(rows),scenarios=len(results),expected_scenarios=len(rows),
                         quality_equivalence_enabled=first['quality_equivalence_enabled'],switch_source='pushed_acceptance_summary',
                         acceptance_summary_sha256=base.file_sha(ROOT/'acceptance/summary.json'))
        summary.update(result_sha256=base.file_sha(out/'results.jsonl'),manifest_sha256=base.file_sha(base.MANIFEST),
                       shared_module_sha256=manifest['shared_module_sha256'],scheduler_lock_sha256=base.file_sha(SCHEDULER_LOCK))
        save(out/'summary.json',summary)
        if phase=='acceptance' and summary['complete']:
            old_entries=[json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
            same=[r for r in old_entries if Path(r['result_path'])==out/'results.jsonl']
            if same and any(r['results_sha256']!=summary['result_sha256'] for r in same):raise ValueError('same_run_complete_history_changed')
            if not same:
                record=dict(summary,result_path=str(out/'results.jsonl'),results_sha256=summary['result_sha256'])
                with ledger.open('ab') as f:f.write(base.encoded(record)+b'\n');f.flush();os.fsync(f.fileno())
        status='完成'
        return summary
    except KeyboardInterrupt as exc:status='中断';error=repr(exc);raise
    except BaseException as exc:error=repr(exc);raise
    finally:
        if mon is not None:
            try:mon.tick(force=True)
            except Exception as exc:status='失败';error=repr(exc)
        end=dict(time=base.now(),phase=phase,status=status,error=error,completed_scenarios=len(results),
                 elapsed_seconds=time.monotonic()-start,min_memavailable=mon.lowest if mon else None,
                 memory_peak_bytes=mon.peak if mon else None)
        with (out/'end.jsonl').open('ab') as f:f.write(base.encoded(end)+b'\n');f.flush();os.fsync(f.fileno())
        with (ROOT/'end.jsonl').open('ab') as f:f.write(base.encoded(end)+b'\n');f.flush();os.fsync(f.fileno())
        print('ALL-END 已结束 '+json.dumps(end,ensure_ascii=False),flush=True)


def proportion(stat,key):
    return '%.8f (MC SE %.8f)'%(stat[key]['proportion'],stat[key]['mc_se'])


def report_section():
    acc=ROOT/'acceptance/summary.json';env=ROOT/'envelope/summary.json'
    first=json.loads(acc.read_text())
    rows=base.read_results(ROOT/'acceptance')
    lines=['## 6. 正式结果（分阶段运行）','',
           '第一阶段结果先提交并推送，然后才允许第二阶段启动。开关只由完整验收与历史完整运行合取决定，第二阶段不改变开关。',
           '', 'quality_equivalence_enabled='+str(first['quality_equivalence_enabled']).lower(),
           '', '|验收场景|覆盖率及MC标准误|判等价比例及MC标准误|退化比例|是否通过|',
           '|---|---|---|---:|---|']
    for row in rows:
        s=row['statistics']['t'];lines.append('|%s|%s|%s|%.8f|%s|'%(row['id'],proportion(s,'covered'),proportion(s,'equivalent'),s['degenerate']['proportion'],'通过' if row['passed'] else '未通过'))
    lines+=['','未通过场景：'+(', '.join(first['failed_scenarios']) or '无')+'。','',
            'A4退化与判等价比例见上表A4-001/A4-002；退化重复按覆盖为真、判等价为否计入全部重复分母。','']
    if env.exists():
        lines+=['|包络/报告场景|t覆盖率/MCSE|percentile覆盖率/MCSE|包络覆盖率/MCSE|包络判等价/MCSE|退化比例|',
                '|---|---|---|---|---|---:|']
        for row in base.read_results(ROOT/'envelope'):
            s=row['statistics'];lines.append('|%s|%s|%s|%s|%s|%.8f|'%(row['id'],proportion(s['t'],'covered'),proportion(s['percentile'],'covered'),proportion(s['envelope'],'covered'),proportion(s['envelope'],'equivalent'),s['t']['degenerate']['proportion']))
        lines+=['','两种区间及包络的全部事件数、比例、MC标准误（含各自判等价、无区间、退化）在envelope-results.jsonl中；B只报告、不参与开关。']
    else:lines+=['第二阶段尚未运行；包络与B组值不以试跑值代填。']
    return '\n'.join(lines)+'\n\n'


def publish(phase):
    # Publication is sequential and starts only after computation has ended.
    verified();summary=json.loads((ROOT/phase/'summary.json').read_text())
    if not summary['complete']:raise ValueError('cannot_publish_incomplete_stage')
    marker=ROOT/('published-'+phase+'.json')
    remote_summary=str((EVIDENCE/(phase+'-summary.json')).relative_to(WORK))
    if marker.exists():
        record=json.loads(marker.read_text())
        if command(['show','origin/main:'+remote_summary])!=(ROOT/phase/'summary.json').read_bytes():raise ValueError('publication_marker_remote_mismatch')
        return record['commit']
    subprocess.run(GIT+['fetch','origin','main'],cwd=WORK,check=True)
    if command(['rev-parse','HEAD'])!=command(['rev-parse','origin/main']):raise ValueError('main_not_synchronized')
    status=command(['status','--porcelain']).decode().splitlines()
    if any(s not in ('?? config/','?? gbs_gcc.conf','?? gbs_llvm.conf') for s in status):raise ValueError('publication_worktree_changed')
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    additions=[]
    for name in ('results.jsonl','summary.json','run-header.json','end.jsonl'):
        path=EVIDENCE/(phase+'-'+name);path.write_bytes((ROOT/phase/name).read_bytes());additions.append(path)
    raw_index=[]
    for path in sorted((ROOT/phase).iterdir()):
        if path.is_file():raw_index.append(dict(path=str(path),sha256=base.file_sha(path),bytes=path.stat().st_size))
    index=EVIDENCE/(phase+'-raw-index.json');save(index,raw_index);additions.append(index)
    report=WORK/'docs/profgen/eval/prep/07_interval_simulation.md';text=report.read_text()
    start=text.index('## 6. ');end=text.index('## 7. ',start);text=text[:start]+report_section()+text[end:]
    endings=[json.loads(x) for x in (ROOT/'end.jsonl').read_text().splitlines()]
    finish=[x for x in endings if x['status']=='完成'];elapsed=sum(x['elapsed_seconds'] for x in endings)
    peak=max((x['memory_peak_bytes'] or 0 for x in endings),default=0)
    minimum=min(x['min_memavailable'] for x in endings if x['min_memavailable'] is not None)
    text+='\n## '+('9' if phase=='acceptance' else '10')+'. '+phase+'阶段完成\n\n'
    text+='结果、SHA链与原始资源索引：evidence/registration-checks/simulation/phased/'+phase+'-*。本阶段完成'+str(summary['scenarios'])+'场景，开关='+str(summary['quality_equivalence_enabled']).lower()+'。\n\n'
    text+='累计阶段耗时%.3f秒，记录峰值%d B，最低MemAvailable%d B。单进程3G/100%%、nice19/ionice-c3；未读真实profile、未登记修正案3。\n'%(elapsed,peak,minimum)
    report.write_text(text);additions.append(report)
    checklist=WORK/'docs/profgen/eval/prep/06_registration_checklist.md'
    checklist.write_text(checklist.read_text()+'\n### 第9项 '+phase+'阶段完成\n\n'+('122个验收场景完成，结果先推送再开始包络；第9项仍部分完成。' if phase=='acceptance' else '150行包络与报告完成，第9项已完成。Q.5为17项完成、17部分、12/18/19未开始。')+' 开关='+str(summary['quality_equivalence_enabled']).lower()+'。详见07报告第6节。未登记修正案3。\n');additions.append(checklist)
    statuspath=WORK/'docs/STATUS.md';text=statuspath.read_text();start=text.index('## 第9项区间模拟');end=text.index('## 登记前核对第三批',start)
    current='## 第9项区间模拟（'+('第一阶段已完成，第二阶段待启动' if phase=='acceptance' else '两阶段完成；停止')+'）\n\n'
    current+='- [07报告第6节](profgen/eval/prep/07_interval_simulation.md)：'+phase+'阶段完成'+str(summary['scenarios'])+'场景；quality_equivalence_enabled='+str(summary['quality_equivalence_enabled']).lower()+'。第二阶段不改变开关。\n'
    first=json.loads((ROOT/'acceptance/summary.json').read_text());current+='- 验收未通过场景：'+(', '.join(first['failed_scenarios']) or '无')+'；不讨论放宽阈值。\n'
    current+='- 累计阶段耗时%.3f秒；峰值%d B，最低MemAvailable%d B。原6946344锁及共用统计模块不变，3G/100%%单进程串行。\n'%(elapsed,peak,minimum)
    current+='- '+('第9项部分完成，先推送本阶段结果再启动第二阶段。' if phase=='acceptance' else '第9项已完成，按要求停止；其他Q.5项目未启动。')+'未读取真实profile，未登记修正案3。\n\n'
    statuspath.write_text(text[:start]+current+text[end:]);additions.append(statuspath)
    if any(p.stat().st_size>=1000000 for p in additions):raise ValueError('evidence_file_exceeds_1MB')
    subprocess.run(GIT+['add','--']+[str(p.relative_to(WORK)) for p in additions],cwd=WORK,check=True)
    staged=set(command(['diff','--cached','--name-only']).decode().splitlines())
    if not staged<=set(str(p.relative_to(WORK)) for p in additions):raise ValueError('unexpected_staged_file')
    subprocess.run(GIT+['diff','--cached','--check'],cwd=WORK,check=True)
    env=dict(os.environ,GIT_AUTHOR_NAME='Hao Lin',GIT_AUTHOR_EMAIL='hao.lin@samsung.com',GIT_COMMITTER_NAME='Hao Lin',GIT_COMMITTER_EMAIL='hao.lin@samsung.com')
    with (ROOT/('publish-'+phase+'.log')).open('ab') as log:
        subprocess.run(GIT+['commit','-m','prep: publish interval simulation '+phase+' results'],cwd=WORK,env=env,stdout=log,stderr=log,check=True)
        commit=command(['rev-parse','HEAD']).decode().strip()
        subprocess.run(GIT+['push','origin','main'],cwd=WORK,stdout=log,stderr=log,check=True)
    if command(['rev-parse','HEAD'])!=command(['rev-parse','origin/main']):raise ValueError('push_not_verified')
    save(marker,dict(commit=commit,time=base.now(),summary_sha256=base.file_sha(ROOT/phase/'summary.json')))
    print('PUBLISHED '+phase+' '+commit,flush=True)
    return commit


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['verify','both','acceptance','envelope']);a=p.parse_args()
    if a.action=='verify':verified(pushed=False);print('original and supplemental SHA checks passed');return
    ROOT.mkdir(parents=True,exist_ok=True)
    def stop(signum,frame):raise KeyboardInterrupt('signal '+str(signum))
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    start=time.monotonic();status='失败';error=None
    try:
        for phase in (['acceptance','envelope'] if a.action=='both' else [a.action]):
            run_stage(phase);publish(phase)
        status='完成'
    except KeyboardInterrupt as exc:status='中断';error=repr(exc);raise
    except BaseException as exc:error=repr(exc);raise
    finally:
        end=dict(time=base.now(),status=status,error=error,action=a.action,elapsed_seconds=time.monotonic()-start)
        with (ROOT/'controller-end.jsonl').open('ab') as f:f.write(base.encoded(end)+b'\n');f.flush();os.fsync(f.fileno())
        print('CONTROLLER 已结束 '+json.dumps(end,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
