import contextlib
import itertools
import math
import statistics as st
import sys
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import re
import shlex
import subprocess
import tarfile
import threading
import time

import board
from analyze import KINDS, boot_result, stats
from control import IDS, OUT, REMOTE, SDB, RecoveryRequired, Stop, checked, reboot, root, run, shell, snapshot
from temp_check import gate, probe

previous=Path('/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k0/k1f-2-resume')
lock_path=Path('/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/host-gbs.lock')
boot_sha='146a4e2d870f3f65fdc6c6f9ca738e3cabcb83bbf4dc6f96bbcdd18c6776ab35'
terminal=OUT/'terminal.json'
remote=board.remote

base_module='6.12.80-arm-rpi4-v7l-kbase'
plat_module='6.12.80-arm-rpi4-v7l'

class Technical(Stop):
    def __init__(self,kind,phase):
        super().__init__(f'{kind} at {phase}')
        self.kind=kind

def put(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    board.atomic_json(path,data)

def read(path):
    return json.loads(path.read_text())

def append(path,data):
    with path.open('a') as f:
        f.write(json.dumps(data)+'\n')

def host_builds():
    active=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdecimal():
            continue
        try:
            name=(p/'comm').read_text().strip()
            stat=(p/'stat').read_text().rsplit(')',1)[1].split()[0]
            if stat not in ('Z','X') and name in ('gbs','rpmbuild','depanneur'):
                active.append(dict(pid=int(p.name),comm=name))
        except (OSError,IndexError):
            continue
    return sorted(active,key=lambda x:x['pid'])

def build_status():
    return dict(utc=datetime.now(timezone.utc).isoformat(),processes=host_builds())

@contextlib.contextmanager
def no_build(d,max_wait_s=8*3600):
    d.mkdir(parents=True,exist_ok=True)
    start=time.monotonic()
    with lock_path.open('r') as lock:
        while True:
            acquired=False
            try:
                fcntl.flock(lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
                acquired=True
            except BlockingIOError:
                pass
            row=build_status()|dict(lock_acquired=acquired,lock_mode='shared')
            append(d/'wait.jsonl',row)
            if acquired and not row['processes']:
                break
            if acquired:
                fcntl.flock(lock,fcntl.LOCK_UN)
            left=max_wait_s-(time.monotonic()-start)
            if left<=0:
                raise Stop('host build gate reached eight-hour limit')
            print('Host build in progress, waiting up to ten minutes for next check',flush=True)
            time.sleep(min(600,left))
        waited=time.monotonic()-start
        done=threading.Event()
        history=d/'activity.jsonl'
        events=[json.loads(line) for line in history.read_text().splitlines()] if history.is_file() else []
        prior=read(d/'previous-summary.json') if (d/'previous-summary.json').is_file() else {}
        def sample():
            row=build_status()
            events.append(row)
            append(d/'activity.jsonl',row)
        sample()
        def monitor():
            while not done.wait(10):
                sample()
        worker=threading.Thread(target=monitor,daemon=True)
        worker.start()
        try:
            yield events
        finally:
            done.set()
            worker.join()
            sample()
            put(d/'summary.json',dict(lock_held=True,lock_mode='shared',wait_s=waited+prior.get('wait_s',0),
                 monitored_s=time.monotonic()-start-waited+prior.get('monitored_s',0),
                 samples=len(events),build_seen=any(x['processes'] for x in events)))

class HostOverlap(Stop):
    pass


def guard_boot(d,monitor):
    state=build_status()
    put(d/'before-tryboot-host.json',state|dict(lock_held=True,lock_mode='shared'))
    if state['processes'] or any(r['processes'] for r in monitor):
        raise HostOverlap('host GBS/rpmbuild activity during measurement block')

def confirm_restore(d):
    rc,s=shell(d,'state',r"tr -d '\000' </proc/device-tree/serial-number; echo; id -u; sha256sum /sys/kernel/notes",15)
    rows=s.splitlines()
    if rc or len(rows)!=3 or rows[0]!='100000004694d889' or rows[1] not in ('0','5001'):
        raise RecoveryRequired(f'RPi4 identity unavailable during recovery: {s!r}')
    if rows[1]=='0':
        root(d/'root-recovery',False)
    return rows[2].split()[0]==boot_sha

def return_plat(d,tag):
    # Run before every direct boot as well as at the terminal stop.
    if confirm_restore(d/'before-return-state'):
        return board.plat(d/'plat')
    reboot(d/'reboot-plat','plat')
    snapshot(d/'reboot-plat','plat',f'{REMOTE}/boots/k2c-gcov-plat-{tag}')
    board.assert_shared(d/'shared')
    return board.plat(d/'plat')

def pull_archive(d,md,endpoint):
    label=endpoint.rsplit('/',1)[-1]
    assert re.fullmatch(r'k2c-gcov-[a-z0-9-]+',label)
    archive=f'{remote}/{label}.receipts.tar'
    local=md/'board-receipts.tar'
    command=(f"set -eu; test ! -e {shlex.quote(archive)}; "
             f"tar -cf {shlex.quote(archive)} -C {shlex.quote(endpoint)} .; "
             f"sha256sum {shlex.quote(archive)}; echo ARCHIVE_READY")
    text=checked(md,'archive-on-board',command,'ARCHIVE_READY',100)
    expected=text.splitlines()[0].split()[0]
    assert re.fullmatch(r'[0-9a-f]{64}',expected),text
    rc,_=run(md,'pull-archive',SDB+['pull',archive,local],140)
    if rc or board.sha(local)!=expected:
        raise Stop('single-file board receipt transfer failed integrity check')
    staged=d/'board-extracted'
    staged.mkdir()
    with tarfile.open(local,mode='r:') as tar:
        tar.extractall(staged,filter='data')
    if (d/'board').is_dir():
        (d/'board').rename(d/'board-incomplete')
    staged.rename(d/'board')
    put(md/'verified-archive.json',dict(remote=archive,sha256=expected,bytes=local.stat().st_size))

def pull_clean(d,md,endpoint,boot_id):
    rc,_=run(md,'pull',SDB+['pull',endpoint,d/'board'],220)
    if not rc:
        return
    _,observed=board.recovery_for_transport(md)
    if observed!=boot_id:
        raise Stop('boot changed while trying to retrieve measurement receipt')
    rc,_=run(md,'pull-recovery',SDB+['pull',endpoint,d/'board-recovered'],220)
    if rc:
        pull_archive(d,md,endpoint)
        return
    if (d/'board').exists():
        (d/'board').rename(d/'board-incomplete')
    (d/'board-recovered').rename(d/'board')

def measured(d,variant,label):
    item=reboot(d,variant)
    endpoint=f'{REMOTE}/boots/{label}'
    snapshot(d,variant,endpoint)
    assert read(d/'direct-summary.json')['boot_id']==item['boot_id']
    md=d/'measurement'
    root(md,True)
    try:
        rc,quiet=shell(md,'quiet',f'bash {remote}/quiet.sh {endpoint}',625)
        if rc or 'QUIET_OK' not in quiet.splitlines():
            pull_clean(d,md,endpoint,item['boot_id'])
            raise Technical('quiet_timeout',label)
        print(f'{label}: quiet passed, timed procedure started',flush=True)
        rc,raw=shell(md,'measure',f'bash {remote}/measure.sh {endpoint}/measure',18000)
        pull_clean(d,md,endpoint,item['boot_id'])
        end=d/'board/measure/END'
        receipt=end.read_text().strip() if end.is_file() else ''
        visits=len(list((d/'board/measure').glob('*/time-*/accepted')))
        if receipt=='measurement=75 cleanup=0':
            put(d/'failure.json',dict(reason='temperature_timeout',timed_windows_started=visits,receipt=receipt))
            raise Technical('temperature_timeout',label)
        if receipt!='measurement=0 cleanup=0':
            raise Stop(f'Measurement did not finish cleanly: {receipt!r}, timed windows={visits}, rc={rc}')
        if rc or 'MEASURE_COMPLETE' not in raw.splitlines():
            print(f'{label}: full measurement receipt recovered, host exit {rc}',flush=True)
    finally:
        root(md,False)
    return complete_measurement(d,label)

def complete_measurement(d,label):
    result=boot_result(d)
    board_temp=d/'board/quiet-gate.tsv'
    result['quiet']['passed_mC']=int(board_temp.read_text().splitlines()[-1].split()[3])
    result['plat_preboot']=read(d/'plat-preboot.json')
    for kind,bench in result['benchmarks'].items():
        for key in ['warm-01',*(f'time-{i:02d}' for i in range(1,4))]:
            rep=d/'board/measure'/kind/key
            active=rep/(rep/'accepted').read_text().strip()
            samples=stats.parse_telemetry_tsv((active/'telemetry.tsv').read_text())
            since=float((active/'start.monotonic').read_text())
            until=float((active/'end.monotonic').read_text())
            gate_start=float((rep/'gate.tsv').read_text().splitlines()[0].split()[0])
            temps=[v for i in samples if since<=i['time']<=until for v in i['temperature'].values() if v is not None]
            extra=dict(start_mC=int((active/'prestart-mC').read_text()),window_max_C=max(temps) if temps else None,
                       gate_wait_s=since-gate_start,rejected_openings=len(list(rep.glob('attempt-*/rejected'))))
            if key=='warm-01':
                bench['warmup_thermal']=extra
            else:
                bench['rounds'][int(key[-2:])-1]['thermal']=extra
    put(d/'measurement-result.json',result)
    print(f'{label}: measurement complete',flush=True)
    return result


REPO = Path('/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent-k1f-1')
WORK=Path('/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent')
BOOT_IMAGE=Path('/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k0/k2c/gcov/artifacts/arm-rpi4/arch/arm/boot/zImage')
AFDO_SHA = 'f0cbc05b553bb16df1d78e03716c3514a97c53c6bd154852280526923df6f464'
N_SHA = '734cc949810798dcbaf1e87a4ae83c3f3645d255f204ebf748b9c1fdbf9ed84b'
STATS_SHA = '66318a939e9eb8bca7b15ae6076133431290226d27a3f0682fe8b18ef3312887'
EVENTS = ('cycles:k', 'instructions:k', 'r01', 'r02', 'r10')
MEMINFO = ('MemTotal', 'MemFree', 'MemAvailable', 'Slab', 'KernelStack', 'PageTables')
SEED = 20261126
VARIANTS = ("K-BASE", 'K-AFDO-GCOV')
TARGETS = dict(zip(VARIANTS, ('kbase','kafdo'), strict=True))


def preregister():
    n_file = OUT/'formal-N.lock.json'
    assert board.sha(n_file)==N_SHA and board.sha(Path(stats.__file__))==STATS_SHA
    n = read(n_file)['formal_N']
    prior_plan = read(previous/'phase-plan.json')
    assert n==10
    p = dict(formal=stats.order(n,SEED,VARIANTS), mechanism=stats.order(3,SEED,VARIANTS),
             seed=SEED, n=n, repetitions=20000, epsilon=0.01, primary='pipe',
             formal_N_sha256=N_SHA, workflow_stats_sha256=STATS_SHA, candidate_zImage_sha256=AFDO_SHA, candidate_profile_sha256='23693afab064fa7ebac233346446db7a647627c3c24f3bfb7b84dc3a90c02fa9',
             comparators=VARIANTS, mechanism_cpus=[3], mechanism_events=EVENTS, mechanism_workloads=['pipe','mmfault'],
             time_rule=read(OUT/'timing-definition.lock.json')['primary_time'],
             temperature=dict(opening_gate=58, opening_seconds=300, max_measurement_start=60, T_max=80),
             parameters=prior_plan['parameters'], benchmark_order=KINDS, warmups=1, timed_rounds=3,
             quiet_busy_below_pct=2.91, min_quiet_seconds=30, max_quiet_seconds=600,
             before_manifest_sha256=board.sha(OUT/'expected-before-deploy.sha256'))
    p=json.loads(json.dumps(p))
    dest=OUT/'preregistration.json'
    if dest.is_file():
        assert {k:v for k,v in read(dest).items() if k!='locked_utc'}==p
    else:
        put(dest,p|dict(locked_utc=datetime.now(timezone.utc).isoformat()))
        (OUT/'preregistration.sha256').write_text(f'{board.sha(dest)}  {dest.name}\n')
    return p


def manifest(path):
    return dict((name,digest) for digest,name in (line.split('  ',1) for line in path.read_text().splitlines()))


def initial():
    d=OUT/'preflight'
    cur=board.plat(d)
    assert cur['boot_id']==read(OUT/'start-cold/passed.json')['boot_id']
    assert board.sha(BOOT_IMAGE)==AFDO_SHA
    before=OUT/'expected-before-deploy.sha256'
    expected=manifest(before)
    assert len(expected)==418 and expected['./zImage-kgcov']=='f74fc430e35e463cd06aeee87ffebd8bda5c54194e8bc84a319bbb4933c0c698'
    assert './zImage-kafdo-gcov' not in expected and board.sha(OUT/'formal-kbase.txt')==expected['./tryboot.txt']
    for item in ('./tryboot.txt','./zImage-kgcov'):
        del expected[item]
    expected['./zImage-kafdo-gcov']=AFDO_SHA
    preserved=OUT/'expected-after-deploy-preserved.sha256'
    preserved.write_text(''.join(f'{expected[name]}  {name}\n' for name in sorted(expected)))
    root(d,True)
    try:
        checked(d,'mkdir',f'mkdir {remote} && echo MADE','MADE')
        board.provision(d,[before,preserved,OUT/'formal-kbase.txt',
                         *(OUT/x for x in ('boot-afdo.sh','quiet.sh','measure.sh','mechanism.sh','smoke.sh')),BOOT_IMAGE])
        checked(d,'image-publish-staging',f'mv -T {remote}/zImage {remote}/zImage-kafdo-gcov && printf "%s  %s\\n" {AFDO_SHA} {remote}/zImage-kafdo-gcov | sha256sum -c - && echo IMAGE_STAGED','IMAGE_STAGED')
        cmd=f'''set -eu
cd {REMOTE}/payload
grep -v '  zImage-kbase-s$' payload.sha256 | sha256sum -c -
sha256sum -c existing-inputs.sha256
findmnt -n -o OPTIONS /usr/lib/modules | grep -Eq '(^|,)ro(,|$)'
df -Pk /opt/afdo_agent
echo MEASURE_INPUTS_OK'''
        checked(d,'inputs',cmd,'MEASURE_INPUTS_OK',100)
    finally:
        root(d,False)
    put(d/'passed.json',dict(status='passed',boot_id=cur['boot_id'],artifact_SHA256=AFDO_SHA))


def select_variant(d, mode, variant, label):
    bid=board.identity(d)
    root(d,True)
    try:
        board.invoke_boot_write(d,mode,variant,label,bid)
    finally:
        root(d,False)


def quiet_metrics(path):
    rows=[line.split() for line in (path/'quiet-gate.tsv').read_text().splitlines()]
    assert len(rows)>=6 and all(float(x[1])<2.91 for x in rows[-6:])
    more=dict(passed_mC=int(rows[-1][3]),seconds=float(rows[-1][0])-float(rows[0][0])+5,
              samples=len(rows),last_six_pct=[float(x[1]) for x in rows[-6:]])
    memory={k.rstrip(':'):int(v) for k,v,_ in (line.split() for line in (path/'meminfo.quiet').read_text().splitlines())}
    assert set(memory)==set(MEMINFO)
    return more,memory


def full_first():
    tag=OUT/'afdo-first'
    with no_build(tag/'host') as live:
        if not (OUT/'deploy/receipts/exit').is_file():
            select_variant(OUT/'deploy','deploy','kafdo','deploy-kafdo')
        assert (OUT/'deploy/receipts/exit').read_text().strip()=='0'
        guard_boot(tag,live)
        put(tag/'plat-preboot.json',probe())
        boot=reboot(tag,'kafdo')
        path=f'{REMOTE}/boots/k2c-gcov-afdo-first'
        snapshot(tag,'kafdo',path)
        t=tag/'quiet'
        root(t,True)
        try:
            checked(t,'quiet',f'bash {remote}/quiet.sh {path}','QUIET_OK',625)
            pull_clean(tag,t,path,boot['boot_id'])
            quiet,memory=quiet_metrics(tag/'board')
        finally:
            root(t,False)
        board.smoke_on_candidate(tag,boot)
        return_plat(tag/'returned','afdo-first')
    put(OUT/'afdo-first.json',dict(status='passed',build_id=IDS['kafdo'],
                                  boot_id=boot['boot_id'],quiet=quiet,memory=memory))


def parse_pmu(path):
    counts={}
    for line in path.read_text().splitlines():
        fields=line.strip().split(',')
        if len(fields)<5 or fields[2] not in EVENTS:
            continue
        event=fields[2]
        assert event not in counts, (event,path)
        count=int(fields[0])
        active=float(fields[4])
        assert count>=0 and 0<active<=100.0, (event,path,line)
        counts[event]=dict(count=count,running_pct=active,time_running_ns=int(fields[3]))
    assert set(counts)==set(EVENTS), (path,counts)
    assert all(counts[event]['count']>0 for event in EVENTS[:2])
    return counts


def counter_boot(d,variant,label):
    item=reboot(d,variant)
    endpoint=f'{REMOTE}/boots/{label}'
    snapshot(d,variant,endpoint)
    md=d/'measurement'
    root(md,True)
    try:
        rc,quiet=shell(md,'quiet',f'bash {remote}/quiet.sh {endpoint}',625)
        if rc or 'QUIET_OK' not in quiet.splitlines():
            pull_clean(d,md,endpoint,item['boot_id'])
            raise Technical('quiet_timeout',label)
        print(f'{label}: quiet passed, counter-only workloads started',flush=True)
        rc,s=shell(md,'counts',f'bash {remote}/mechanism.sh {endpoint}/mechanism',1520)
        pull_clean(d,md,endpoint,item['boot_id'])
        folder=d/'board/mechanism'
        end=(folder/'END').read_text().strip() if (folder/'END').is_file() else ''
        if end=='measurement=75 cleanup=0':
            put(d/'failure.json',dict(reason='temperature_timeout',receipt=end,
                    timed_windows_started=0,counter_windows_started=len(list(folder.glob('*/accepted')))))
            raise Technical('temperature_timeout',label)
        assert end=='measurement=0 cleanup=0', (rc,s,end)
    finally:
        root(md,False)
    quiet,memory=quiet_metrics(d/'board')
    identity=read(d/'direct-summary.json')
    caps={key:[] for key in ('temperature','frequency','voltage')}
    for line in (folder/'capabilities.tsv').read_text().splitlines():
        k,v=line.split()
        caps[k].append(v)
    fixed=int((folder/'fixed-khz').read_text())
    result=dict(variants=variant,boot_id=item['boot_id'],path=str(d.relative_to(OUT)),quiet=quiet,
                counters={},memory=memory,rsts=identity['rsts'],fixed_khz=fixed,
                plat_preboot=read(d/'plat-preboot.json'),build_id=identity['build_id'])
    assert sorted(row.split()[0] for row in (folder/'modules.after').read_text().splitlines())==identity['modules']
    signature=re.compile(r'\bOops\b|\bBUG:|\bWARN(?:ING)?:|kernel panic|Unable to handle kernel|Internal error:|unknown symbol|version magic|disagrees about version|invalid module format|module verification failed',re.I)
    def failures(p):
        return {re.sub(r'^\[\s*\d+(?:\.\d+)?\]\s*','',line) for line in p.read_text().splitlines() if signature.search(line)}
    assert not failures(folder/'dmesg.after')-failures(d/'direct/dmesg')
    for line in (folder/'restored-governors.tsv').read_text().splitlines():
        _,a,b=line.split()
        assert a==b
    for name in ('pipe','mmfault'):
        r=folder/name
        assert (r/'exit').read_text().strip()=='0'
        raw=r/(r/'accepted').read_text().strip()
        samples=stats.parse_telemetry_tsv((raw/'telemetry.tsv').read_text())
        start=float((raw/'start.monotonic').read_text())
        end=float((raw/'end.monotonic').read_text())
        temperatures=[v for row in samples if start<=row['time']<=end for v in row['temperature'].values() if v is not None]
        gate_start=float((r/'gate.tsv').read_text().splitlines()[0].split()[0])
        result['counters'][name]=dict(events=parse_pmu(r/'stat.csv'),telemetry=stats.telemetry(samples,start,end,fixed,caps),
                                     start_mC=int((raw/'prestart-mC').read_text()),window_max_C=max(temperatures),
                                     gate_wait_s=start-gate_start)
    put(d/'counter-result.json',result)
    print(f'{label}: counter-only result complete',flush=True)
    return result


def run_blocks(phase, orders):
    paired=[]
    do_boot=measured if phase=='formal' else counter_boot
    for number,order in enumerate(orders,1):
        d=OUT/phase/f'block-{number:02d}'
        complete=d/'block.json'
        if complete.is_file():
            value=read(complete)
            assert value['order']==order and value['status']=='complete'
            paired.append(value)
            continue
        gate_retries={'temperature_timeout':0,'quiet_timeout':0}
        first_overlap=None
        def remember_overlap(path):
            active=[json.loads(line) for line in (path/'host/activity.jsonl').read_text().splitlines()]
            gates=[read(guard) for guard in path.rglob('before-tryboot-host.json')]
            return min(datetime.fromisoformat(event['utc']).timestamp()
                       for event in active+gates if event['processes'])
        def host_budget():
            left=8*3600 if first_overlap is None else first_overlap+8*3600-time.time()
            if left<=0:
                raise Stop(f'{phase} block {number}: host build gate reached eight-hour limit')
            return left
        for attempt in itertools.count(1):
            work=d/f'attempt-{attempt:02d}'
            attempt_file=work/'attempt.json'
            if attempt_file.is_file():
                last=read(attempt_file)
                assert last['status']=='technical_failure'
                if last['reason'] in gate_retries:
                    gate_retries[last['reason']]+=1
                if last['reason']=='host_build_overlap' and first_overlap is None:
                    first_overlap=remember_overlap(work)
                if any(count>1 for count in gate_retries.values()):
                    raise Stop(f'{phase} block {number}: repeated board gate timeout')
                continue
            tag=f'{phase}-{number:02d}-{attempt}'
            values={}
            failure=None
            with no_build(work/'host',host_budget()) as live:
                try:
                    for leg,name in enumerate(order,1):
                        leg_path=work/f'leg-{leg}-{name}'
                        result_name='measurement-result.json' if phase=='formal' else 'counter-result.json'
                        if (leg_path/result_name).is_file() and (leg_path/'returned/plat/plat.json').is_file():
                            values[name]=read(leg_path/result_name)
                            continue
                        if (leg_path/'reboot.json').is_file():
                            raise Stop(f'reconcile existing partial boot at {leg_path}')
                        assert confirm_restore(leg_path/'verify-plat')
                        guard_boot(leg_path/'before-switch',live)
                        variant=TARGETS[name]
                        select_variant(leg_path/'switch','switch',variant,f'switch-{tag}-{leg}')
                        guard_boot(leg_path,live)
                        put(leg_path/'plat-preboot.json',probe())
                        values[name]=do_boot(leg_path,variant,f'k2c-gcov-{tag}-{leg}')
                        return_plat(leg_path/'returned',f'{tag}-{leg}')
                    guard_boot(work/'complete-host-verify',live)
                except Technical as exc:
                    failure=exc.kind
                except HostOverlap as exc:
                    failure='host_build_overlap'
            if not failure and read(work/'host/summary.json')['build_seen']:
                failure='host_build_overlap'
            if failure:
                return_plat(work/'technical-return',tag+'-technical')
                put(attempt_file,dict(status='technical_failure',reason=failure,completed_legs=list(values),
                                      last_leg=leg,previous_attempts=attempt-1))
                print(f'{tag}: {failure}',flush=True)
                if failure in gate_retries:
                    gate_retries[failure]+=1
                    if gate_retries[failure]>1:
                        raise Stop(f'{tag}: second {failure}')
                    gate(work/'retry-cold')
                else:
                    if first_overlap is None:
                        first_overlap=remember_overlap(work)
                    time.sleep(min(600,host_budget()))
                continue
            row=dict(status='complete',id=number,order=order,attempt=attempt,
                     paired=[values[name] for name in VARIANTS])
            put(complete,row)
            put(attempt_file,dict(status='complete'))
            paired.append(row)
            print(f'{phase}: {len(paired)}/{len(orders)} valid blocks',flush=True)
            break
    return paired


def formal_results(rows,n):
    memory={}
    for signal in MEMINFO:
        left=[r['paired'][0]['memory'][signal] for r in rows]
        right=[r['paired'][1]['memory'][signal] for r in rows]
        delta=[b-a for a,b in zip(left,right,strict=True)]
        if left:
            memory[signal]=dict(unit='KiB',control_median=st.median(left),candidate_median=st.median(right),
                                median_paired_delta=st.median(delta),min_delta=min(delta),max_delta=max(delta),
                                paired_control=left,paired_candidate=right,paired_delta=delta)
    primary={}
    layout=read(OUT/'layout-analysis.json')
    for name in KINDS:
        cells=[]
        for row in rows:
            a,b=(boot['benchmarks'][name] for boot in row['paired'])
            cells.append(dict(id=row['id'],complete=True,control=a['geomean'],candidate=b['geomean'],
                              control_flag=a['flag'],candidate_flag=b['flag']))
        result=stats.analyze(cells,n,SEED,.01,20000)
        result['layout_reference']=layout['benchmarks'][name]['primary']
        for column,index in (('control',0),('candidate',1)):
            result[f'{column}_flagged_rounds']=sum(r['telemetry']['classification']!='clean'
                        for row in rows for r in row['paired'][index]['benchmarks'][name]['rounds'])
        primary[name]=result
    return dict(n=n,accepted=len(rows),benchmarks=primary,memory=memory,seed=SEED)


def count_results(rows):
    result={}
    for name in ('pipe','mmfault'):
        result[name]={}
        for event in EVENTS:
            left=[r['paired'][0]['counters'][name]['events'][event] for r in rows]
            right=[r['paired'][1]['counters'][name]['events'][event] for r in rows]
            a=[v['count'] for v in left]
            b=[v['count'] for v in right]
            d=[y-x for x,y in zip(a,b,strict=True)]
            if not d:
                continue
            rel=math.expm1(st.mean(math.log(y/x) for x,y in zip(a,b,strict=True))) if min(a)>0 and min(b)>0 else None
            active=[v['running_pct'] for v in left+right]
            result[name][event]=dict(control=a,candidate=b,paired_delta=d,median_paired_delta=st.median(d),
                      min_delta=min(d),max_delta=max(d),relative_geomean=rel,min_running_pct=min(active))
    return dict(accepted=len(rows),events=result)


def recover_or_record(exc):
    data=dict(status='STOP',reason=repr(exc))
    try:
        if (OUT/'preflight/passed.json').is_file():
            return_plat(OUT/'emergency-return',f'stop-{time.time_ns()}')
            if (OUT/'deploy/receipts/exit').is_file() and (OUT/'deploy/receipts/exit').read_text().strip()=='0':
                with no_build(OUT/'emergency-switch-host'):
                    select_variant(OUT/'emergency-switch','switch','kbase','emergency-finish-switch')
                board.plat(OUT/'emergency-final-plat')
    except Exception as trouble:
        data=dict(status='RECOVERY_REQUIRED',reason=repr(trouble),original=repr(exc))
    put(terminal,data)


def main():
    plan=preregister()
    board.assert_shared(OUT/f'driver-start-{time.time_ns()}')
    if not (OUT/'preflight/passed.json').is_file():
        connected,_=run(OUT/'target-connect','connect',['sdb','connect','192.168.108.26:26101'],12)
        assert connected==0
        if not (OUT/'start-cold/passed.json').is_file():
            gate(OUT/'start-cold')
        with no_build(OUT/'staging-host'):
            initial()
    if not (OUT/'afdo-first.json').is_file():
        full_first()
    print('K-AFDO first-boot checks passed',flush=True)
    rows=run_blocks('formal',plan['formal'])
    put(OUT/'formal-analysis.json',formal_results(rows,plan['n']))
    counts=run_blocks('mechanism',plan['mechanism'])
    put(OUT/'mechanism-analysis.json',count_results(counts))
    return_plat(OUT/'final','final')
    with no_build(OUT/'finish-host'):
        select_variant(OUT/'finish-switch','switch','kbase','finish-switch')
        select_variant(OUT/'finish-verify','verify','kbase','finish-verify')
    board.plat(OUT/'final-owner')
    board.assert_shared(OUT/'final-shared')
    put(terminal,dict(status='complete',formal_blocks=len(rows),mechanism_blocks=len(counts),formal_N=plan['n']))


if __name__=='__main__':
    if sys.argv[1:]==['--preregister']:
        preregister()
    else:
        try:
            main()
        except RecoveryRequired as exc:
            put(terminal,dict(status='RECOVERY_REQUIRED',reason=str(exc)))
            raise
        except Exception as exc:
            recover_or_record(exc)
            raise
