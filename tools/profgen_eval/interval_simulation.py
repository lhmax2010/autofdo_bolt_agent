"""Q.5 #9 synthetic driver; all intervals/degeneracy use shared statistics.

No profile reader, no statistical reimplementation, no parallelism. Scenario
and code hashes must already be in origin/main before pilot/formal execution.
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
import time

import registration_statistics as shared

WORK = Path(__file__).resolve().parents[2]
EVIDENCE = WORK / 'docs/profgen/eval/prep/evidence/registration-checks/simulation'
MANIFEST = EVIDENCE / 'scenarios.json'
LOCK = EVIDENCE / 'prerun-lock.json'
GIT = ['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false']
RULES = 't 单独的覆盖率 ≥ 93%；Δ 为 ±0.02 与 ±0.03 时，t 单独的判等价比例 ≤ 3.0%；A4 必须 100% 退化、0% 判等价；退化重复按“不判等价、覆盖为真”计。quality_equivalence_enabled 取全部验收场景都通过且全部运行完整时的逻辑与；任一场景不通过或未完成，即为 false。'


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.datetime.now().astimezone().isoformat()


def moments(p):
    kind = p['distribution']
    if kind == 'normal':
        if p['sd'] < 0: raise ValueError('negative_sd')
        return p['mean'], p['sd'] ** 2
    if kind == 'discrete':
        if p['K'] not in (50, 200): raise ValueError('unsupported_K')
        return p['mean'], 2 / (3 * p['K'] ** 2)
    if kind == 'bernoulli':
        if not 0 < p['p'] < 1: raise ValueError('invalid_probability')
        return p['a'] * p['p'], p['a'] ** 2 * p['p'] * (1-p['p'])
    if kind == 'constant': return p['value'], 0.0
    if kind == 'lognormal':
        s = p['sigma_log']
        return (p['shift'] + p['sign'] * p['scale'] * math.exp(s*s/2),
                p['scale'] ** 2 * math.expm1(s*s) * math.exp(s*s))
    if kind == 'rare_rademacher': return .03, .99**2/33*(1-1/33)+.001**2
    if kind == 'rare_normal': return .03, .2**2*.15*.85+.001**2
    raise ValueError('unknown_distribution')


def close(a, b):
    if not math.isfinite(a) or not math.isfinite(b) or not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-15):
        raise ValueError('moment_mismatch: %r != %r' % (a, b))


def validate_row(r):
    ns = r['sizes']; ps = r['phase_parameters']; family = r['family']
    if ns not in ([15], [5, 10]) or len(ns) != len(ps): raise ValueError('invalid_structure')
    expected_kind = dict(A1='normal', A2='discrete', A3='bernoulli', A4='constant',
                         B1='lognormal', B2='rare_rademacher', B3='rare_normal')
    if family == 'A5':
        if ns != [5, 10] or [p['distribution'] for p in ps] != ['bernoulli', 'normal']:
            raise ValueError('A5_structure')
        close(ps[0]['p'], .15); close(ps[1]['mean'], 0); close(ps[1]['sd'], .001)
        close((5/15) * ps[0]['a'] * .15, r['delta'])
    elif family not in expected_kind or any(p['distribution'] != expected_kind[family] for p in ps):
        raise ValueError('family_distribution_mismatch')
    ms, vs = zip(*(moments(p) for p in ps))
    for x, y in zip(ms, r['phase_means']): close(x, y)
    for x, y in zip(vs, r['phase_variances']): close(x, y)
    mean = math.fsum(n/15*m for n, m in zip(ns, ms))
    se = math.sqrt(math.fsum((n/15)**2*v/n for n, v in zip(ns, vs)))
    close(mean, r['delta']); close(se/shared.EPSILON, r['se_ratio'])
    ratio = 'not_applicable' if len(ns) == 1 or not any(vs) else vs[0]/vs[1]
    if ratio == 'not_applicable':
        if r['variance_ratio'] != ratio: raise ValueError('ratio_not_applicable')
    else: close(ratio, r['variance_ratio'])
    if family == 'A1':
        if r['target_se_ratio'] not in (.05, .1, .25, .5): raise ValueError('A1_SE')
        if len(ns) == 2 and not any(math.isclose(ratio, v) for v in (1, 16, 1/16)):
            raise ValueError('A1_variance_ratio')
    if family in ('A2', 'A3', 'B1', 'B2', 'B3') and len(ns) == 2:
        if ps[0] != ps[1]: raise ValueError('same_phase_parameters_required')
        if not math.isclose(ratio, 1): raise ValueError('variance_ratio_must_be_one')
    if family == 'A2' and r['variance_ratio'] not in (1, 'not_applicable'):
        raise ValueError('A2_variance_ratio_16_infeasible')
    if family in ('A1', 'A2') and r['delta'] not in (0, .02, -.02, .03, -.03): raise ValueError('invalid_delta')
    if family in ('A3', 'A5') and r['delta'] not in (.02, -.02, .03, -.03): raise ValueError('invalid_delta')
    if family == 'A3' and ps[0]['p'] not in (.05, .15): raise ValueError('A3_p')
    if family == 'A4':
        close(r['delta'], 0); close(se, 0)
    if family == 'B1':
        if ps[0]['sigma_log'] not in (.17, .32, .75) or ps[0]['sign'] not in (-1, 1) or r['delta'] not in (.02, -.02): raise ValueError('B1_parameters')
        close(r['se_ratio'], .1)
    if r['target_se_ratio'] is not None: close(r['se_ratio'], r['target_se_ratio'])
    if r['role'] != ('acceptance' if family[0]=='A' else 'report'): raise ValueError('role_mismatch')
    if r['t_repeats'] != (1000000 if family[0]=='A' else 0) or r['envelope_repeats'] != 10000: raise ValueError('repeats_mismatch')
    if r['pilot_t_repeats'] != 10000 or r['pilot_envelope_repeats'] != 1: raise ValueError('pilot_size')
    if type(r['seed']) is not int or r['envelope_stream'] != str(r['seed'])+':envelope': raise ValueError('seed_mismatch')
    return dict(means=list(ms), variances=list(vs), delta=mean, se_ratio=se/shared.EPSILON, variance_ratio=ratio)


def validate_manifest(m):
    if m['epsilon'] != shared.EPSILON or m['bootstrap_seed'] != shared.SEED or m['bootstrap_resamples'] != shared.BOOTSTRAPS: raise ValueError('shared_constants_mismatch')
    if m['rules_verbatim'] != RULES: raise ValueError('rules_changed')
    rows = m['scenarios']
    if collections.Counter(r['family'] for r in rows) != dict(A1=80,A2=20,A3=16,A4=2,A5=4,B1=24,B2=2,B3=2): raise ValueError('missing_scenario')
    for field in ('id', 'seed'):
        if len({r[field] for r in rows}) != len(rows): raise ValueError('duplicate_'+field)
    signatures = [digest({k:r[k] for k in ('family','sizes','phase_parameters','delta')}) for r in rows]
    if len(set(signatures)) != len(rows): raise ValueError('duplicate_parameters')
    return {r['id']: validate_row(r) for r in rows}


def verify_lock(pushed=True):
    lock = json.loads(LOCK.read_text())
    for path, expected in lock['files'].items():
        if file_sha(WORK/path) != expected: raise ValueError('locked_SHA_changed:'+path)
        if pushed:
            remote = subprocess.check_output(GIT+['show', 'origin/main:'+path], cwd=WORK)
            if hashlib.sha256(remote).hexdigest() != expected: raise ValueError('not_pushed:'+path)
    if pushed and subprocess.check_output(GIT+['show','origin/main:'+str(LOCK.relative_to(WORK))],cwd=WORK) != LOCK.read_bytes(): raise ValueError('lock_not_pushed')
    m = json.loads(MANIFEST.read_text()); validate_manifest(m)
    if file_sha(WORK/m['shared_module']) != m['shared_module_sha256']: raise ValueError('shared_module_SHA_mismatch')
    return m, lock


def draw(p, rng):
    kind=p['distribution']
    if kind=='normal': return rng.gauss(p['mean'], p['sd'])
    if kind=='discrete': return p['mean']+(rng.randrange(3)-1)/p['K']
    if kind=='bernoulli': return p['a'] if rng.random()<p['p'] else 0.0
    if kind=='constant': return p['value']
    if kind=='lognormal': return p['shift']+p['sign']*p['scale']*rng.lognormvariate(0,p['sigma_log'])
    if kind=='rare_rademacher': return (.99 if rng.random()<1/33 else 0)+(.001 if rng.randrange(2) else -.001)
    if kind=='rare_normal': return (.2 if rng.random()<.15 else 0)+rng.gauss(0,.001)
    raise ValueError('unknown_distribution')


def sample(r, rng):
    return {str(h):[draw(p,rng) for _ in range(n)] for h,(n,p) in enumerate(zip(r['sizes'],r['phase_parameters']))}


def decision(interval, degenerate, delta):
    if degenerate: return dict(covered=True, equivalent=False, degenerate=True, no_interval=interval is None)
    if interval is None: raise ValueError('nondegenerate_missing_interval')
    lo,hi=interval
    if not (math.isfinite(lo) and math.isfinite(hi) and lo<=hi): raise ValueError('invalid_interval')
    return dict(covered=lo<=delta<=hi, equivalent=-shared.EPSILON<=lo and hi<=shared.EPSILON, degenerate=False, no_interval=False)


def evaluate(phases, delta, envelope=False):
    if not envelope:
        t=shared.stratified_t(phases)
        return {'t':decision(t['interval'],t['degenerate'],delta)}
    result=shared.intervals_joint({'difference':phases})['difference']
    t=result['t'];flat=t['degenerate']
    out={k:decision(v,flat,delta) for k,v in [('t',t['interval']),('percentile',result['bootstrap']),('envelope',result['envelope'])]}
    if out['envelope']['equivalent'] and not out['t']['equivalent']: raise AssertionError('envelope_not_subset_decision')
    if not flat and result['envelope'] is not None and not (result['envelope'][0]<=t['interval'][0]<=t['interval'][1]<=result['envelope'][1]): raise AssertionError('envelope_not_superset_interval')
    return out


def acceptance(row, counts, n):
    if n != row['t_repeats']: return False
    return (counts['covered']/n>=.93 and (abs(row['delta']) not in (.02,.03) or counts['equivalent']/n<=.03)
            and (row['family']!='A4' or (counts['degenerate']==n and counts['equivalent']==0)))


def summarize(counts, n):
    return {k:dict(count=v, proportion=v/n, mc_se=math.sqrt((v/n)*(1-v/n)/n)) for k,v in counts.items()}


def combined_switch(runs):
    complete=[r for r in runs if r['complete']]
    return bool(complete) and all(r['quality_equivalence_enabled'] for r in complete)


def summarize_run(rows, results):
    wanted={r['id']:r for r in rows};found={x['id']:x for x in results}
    complete=len(found)==len(results)==len(wanted) and set(found)==set(wanted)
    failures=[]
    for ident, row in wanted.items():
        result=found.get(ident)
        if result is None: continue
        if result['seed']!=row['seed'] or result['t_repeats']!=row['t_repeats'] or result['envelope_repeats']!=row['envelope_repeats']: complete=False
        if row['role']=='acceptance' and not result['passed']: failures.append(ident)
    return dict(complete=complete, quality_equivalence_enabled=complete and not failures,
                failed_scenarios=failures, included_in_complete_run_conjunction=complete,
                execution_status='complete' if complete else 'incomplete_not_statistical_rejection')


class Monitor:
    def __init__(self, out):
        self.out=out;self.start=time.monotonic();self.next=0;self.next_mem=0
        self.lowest=None;self.peak=0;self.strikes=0;self.samples=0;self.current={}
        cg=next(s[3:] for s in Path('/proc/self/cgroup').read_text().splitlines() if s.startswith('0::'))
        self.cgpath=Path('/sys/fs/cgroup')/cg.lstrip('/');self.cg=cg
        if (self.cgpath/'memory.max').read_text().strip()!=str(3*1024**3): raise ValueError('scope_MemoryMax_not_3G')
        quota,period=map(int,(self.cgpath/'cpu.max').read_text().split())
        if quota/period>2: raise ValueError('scope_CPUQuota_above_200')
        self.tick(force=True)
        if self.lowest<4*1024**3: raise RuntimeError('admission_MemAvailable_below_4GiB')
    def tick(self, force=False, **current):
        self.current.update(current);t=time.monotonic()
        if not force and t<self.next:return
        self.next=t+1
        self.peak=max(self.peak,int((self.cgpath/'memory.peak').read_text()))
        if force or t>=self.next_mem:
            raw=Path('/proc/meminfo').read_text();memory=int(next(x.split()[1] for x in raw.splitlines() if x.startswith('MemAvailable:')))*1024
            (self.out/('meminfo-%05d.txt'%self.samples)).write_text(raw);self.samples+=1;self.next_mem=t+60
            self.lowest=memory if self.lowest is None else min(self.lowest,memory)
            self.strikes=self.strikes+1 if memory<3*1024**3 else 0
            if self.strikes>=2:raise RuntimeError('resource_stop_two_samples_below_3GiB')
        state=dict(time=now(),elapsed=time.monotonic()-self.start,min_memavailable=self.lowest,memory_peak_bytes=self.peak,scope=self.cg,**self.current)
        (self.out/'progress.json').write_bytes(encoded(state)+b'\n')


def append(out, value):
    target=out/'results.jsonl';previous='0'*64
    if target.exists():
        lines=target.read_text().splitlines()
        if lines:previous=json.loads(lines[-1])['result_sha256']
    value=dict(value,previous_sha256=previous);value['result_sha256']=digest(value)
    with target.open('ab') as f:f.write(encoded(value)+b'\n');f.flush();os.fsync(f.fileno())
    return value


def read_results(out):
    target=out/'results.jsonl'
    if not target.exists():return []
    result=[];previous='0'*64
    for line in target.read_text().splitlines():
        r=json.loads(line);expected=r.pop('result_sha256')
        if digest(r)!=expected or r['previous_sha256']!=previous:raise ValueError('result_chain_invalid')
        r['result_sha256']=expected;result.append(r);previous=expected
    if len({r['id'] for r in result})!=len(result):raise ValueError('duplicate_result')
    return result


def run_row(row, mode, monitor):
    begin=time.monotonic();rng=random.Random(row['seed']);timings={};stats={}
    n=10000 if mode=='pilot' else row['t_repeats']
    start=time.monotonic();counts=collections.Counter(covered=0,equivalent=0,degenerate=0,no_interval=0)
    for i in range(n):
        one=evaluate(sample(row,rng),row['delta'])['t']
        counts.update({k:int(v) for k,v in one.items()})
        if i%100==0:monitor.tick(scenario=row['id'],stage='t',repeat=i,total=n)
    timings['t_seconds']=time.monotonic()-start
    if mode=='formal' and n:stats['t']=summarize(counts,n)
    passed=acceptance(row,counts,n) if row['role']=='acceptance' and mode=='formal' else None
    rng=random.Random(row['envelope_stream']);en=1 if mode=='pilot' else row['envelope_repeats']
    totals={k:collections.Counter(covered=0,equivalent=0,degenerate=0,no_interval=0) for k in ('t','percentile','envelope')}
    start=time.monotonic()
    for i in range(en):
        result=evaluate(sample(row,rng),row['delta'],envelope=True)
        for kind,c in result.items():totals[kind].update({k:int(v) for k,v in c.items()})
        monitor.tick(scenario=row['id'],stage='envelope',repeat=i+1,total=en)
    timings['envelope_seconds']=time.monotonic()-start
    if mode=='formal':stats['envelope_sample']={k:summarize(v,en) for k,v in totals.items()}
    result=dict(id=row['id'],seed=row['seed'],mode=mode,t_repeats=n,envelope_repeats=en,
                elapsed_seconds=time.monotonic()-begin,timings=timings,finished=now(),parameters=row)
    if mode=='pilot':
        result['projected_formal_seconds']=timings['t_seconds']/n*row['t_repeats']+timings['envelope_seconds']/en*row['envelope_repeats']
        result['timing_only']=True
    else:result.update(statistics=stats,passed=passed)
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['validate','pilot','formal']);parser.add_argument('--out',type=Path);a=parser.parse_args()
    manifest,lock=verify_lock(pushed=a.mode!='validate')
    if a.mode=='validate':print(json.dumps(validate_manifest(manifest),allow_nan=False));return
    out=a.out.resolve()
    if not out.is_relative_to(WORK/'temp'):raise ValueError('outputs_must_be_in_WORK_temp')
    out.mkdir(parents=True,exist_ok=True);mon=Monitor(out)
    header=dict(mode=a.mode,manifest_sha256=file_sha(MANIFEST),lock_sha256=file_sha(LOCK),files=lock['files'])
    headerpath=out/'run-header.json'
    if headerpath.exists() and json.loads(headerpath.read_text())!=header:raise ValueError('resume_header_changed')
    headerpath.write_bytes(encoded(header)+b'\n')
    def interrupted(signum,frame):raise KeyboardInterrupt('signal %s'%signum)
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
    results=[];status='失败';error=None
    try:
        results=read_results(out);seen={r['id'] for r in results};wanted={r['id']:r for r in manifest['scenarios']}
        for r in results:
            if r['id'] not in wanted or r['parameters']!=wanted[r['id']] or r['mode']!=a.mode:raise ValueError('resume_parameters_changed')
        if a.mode=='formal':
            estimate=json.loads((WORK/'temp/interval-simulation/pilot/estimate.json').read_text())
            if estimate['manifest_sha256']!=file_sha(MANIFEST) or not estimate['complete'] or estimate['projected_seconds']>12*3600:raise ValueError('formal_time_gate_rejected')
        for row in manifest['scenarios']:
            if row['id'] in seen:continue
            verify_lock(pushed=True)
            results.append(append(out,run_row(row,a.mode,mon)))
            mon.tick(force=True,completed_scenarios=len(results))
        if a.mode=='pilot':
            total=math.fsum(r['projected_formal_seconds'] for r in results)
            summary=dict(complete=len(results)==len(manifest['scenarios']),manifest_sha256=file_sha(MANIFEST),projected_seconds=total,limit_seconds=43200,formal_allowed=total<=43200,quality_equivalence_enabled=False,reason='pilot_only_no_formal_result')
            (out/'estimate.json').write_bytes(encoded(summary)+b'\n')
        else:
            summary=summarize_run(manifest['scenarios'],results)
            ledger=WORK/'temp/interval-simulation/complete-runs.jsonl'
            prior=[json.loads(x) for x in ledger.read_text().splitlines()] if ledger.exists() else []
            for old in prior:
                oldpath=Path(old['result_path'])
                if not oldpath.is_relative_to(WORK/'temp') or file_sha(oldpath)!=old['results_sha256']:raise ValueError('prior_complete_results_changed')
            if summary['complete']:
                record=dict(summary, result_path=str(out/'results.jsonl'), results_sha256=file_sha(out/'results.jsonl'), shared_module_sha256=manifest['shared_module_sha256'],lock_sha256=file_sha(LOCK))
                with ledger.open('ab') as f:f.write(encoded(record)+b'\n');f.flush();os.fsync(f.fileno())
                summary['quality_equivalence_enabled']=combined_switch(prior+[record])
                summary['complete_runs_disclosed']=prior+[record]
            (out/'summary.json').write_bytes(encoded(summary)+b'\n')
        status='完成'
    except KeyboardInterrupt as exc:status='中断';error=repr(exc);raise
    except Exception as exc:error=repr(exc);raise
    finally:
        try:mon.tick(force=True)
        except Exception as final_error:
            status='失败';error=repr(final_error)
        end=dict(time=now(),status=status,error=error,completed_scenarios=len(results),elapsed_seconds=time.monotonic()-mon.start,min_memavailable=mon.lowest,memory_peak_bytes=mon.peak,mode=a.mode)
        with (out/'end.jsonl').open('ab') as f:f.write(encoded(end)+b'\n')
        print('ALL-END 已结束 '+json.dumps(end,ensure_ascii=False,allow_nan=False),flush=True)


if __name__=='__main__':main()
