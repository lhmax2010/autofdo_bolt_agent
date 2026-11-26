#!/usr/bin/env python3
from pathlib import Path
import fcntl
import json
import os
import signal
import subprocess
import sys
import time

work=Path(__file__).resolve().parent
tmp=work.parents[1]
GiB=1024**3
RESOURCE_RECHECK_S=600
LOCK_WAIT_LIMIT_S=8*3600
group=Path('/sys/fs/cgroup'+Path('/proc/self/cgroup').read_text().strip().split('::',1)[1])
log=work/'recovery-resources.jsonl'
result=work/'recovery-result.json'

def sample():
    available = next(int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()
                     if line.startswith('MemAvailable:'))
    def full_pressure(kind):
        row=next(line.split()[1:] for line in Path(f'/proc/pressure/{kind}').read_text().splitlines()
                 if line.startswith('full '))
        return dict(field.split('=',1) for field in row)
    io=full_pressure('io')
    memory=full_pressure('memory')
    active=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdecimal():
            continue
        try:
            name=(p/'comm').read_text().strip()
            if name in {'gbs','rpmbuild','depanneur'} and (p/'stat').read_text().rsplit(')',1)[1].split()[0]!='Z':
                active.append(int(p.name))
        except (OSError,IndexError):
            continue
    stat=os.statvfs(work)
    return dict(at=time.time(),mem_available=available,load1=os.getloadavg()[0],
                io_full_avg10=float(io['avg10']),io_full_avg60=float(io['avg60']),
                mem_full_avg10=float(memory['avg10']),
                disk_free=stat.f_bavail*stat.f_frsize,other_build_pids=active,
                memory_peak=int((group/'memory.peak').read_text()),
                memory_events=(group/'memory.events').read_text().strip())

def append(row):
    with log.open('a') as f:
        f.write(json.dumps(row)+'\n')
    print(row,flush=True)

def write(row):
    temporary=result.with_suffix('.tmp')
    temporary.write_text(json.dumps(row,indent=2)+'\n')
    temporary.replace(result)

settings={name:(group/name).read_text().strip() for name in
          ('cpu.max','memory.high','memory.max','memory.swap.max')}
assert settings['cpu.max']=='100000 100000',settings
assert int(settings['memory.high'])==1536*1024**2 and int(settings['memory.max'])==2560*1024**2, settings
assert settings['memory.swap.max']=='0',settings
settings['io.max']=(group/'io.max').read_text().strip() if (group/'io.max').is_file() else None
settings['ionice']=subprocess.check_output(['ionice','-p',str(os.getpid())],text=True).strip()
assert settings['ionice']=='idle',settings
settings['bulk_read_bytes_per_s']=12_000_000
assert os.getpriority(os.PRIO_PROCESS,0)==19
policy=dict(lock_wait_limit_s=LOCK_WAIT_LIMIT_S,resource_wait_limit_s=3*3600,
            resource_recheck_s=RESOURCE_RECHECK_S,mem_available_min_bytes=16*GiB,
            io_full_avg60_below=20,existing_io_full_avg10_max=5,
            runtime_low_memory_bytes=6*GiB,runtime_low_memory_consecutive=2)

def resources_ok(status):
    return (status['mem_available']>=16*GiB and status['io_full_avg60']<20
            and status['load1']<.6*len(os.sched_getaffinity(0))
            and status['disk_free']>=50*GiB and status['io_full_avg10']<=5
            and status['mem_full_avg10']<=1 and not status['other_build_pids'])

def wait_for_lock(lock, deadline):
    while True:
        left=deadline-time.monotonic()
        if left<=0:
            raise TimeoutError('eight-hour shared lock wait expired')
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            return
        except BlockingIOError:
            append(dict(phase='waiting_lock',at=time.time(),lock_held=False,remaining_s=left))
            time.sleep(min(60,left))

def wait_for_resources(deadline):
    previously_good=False
    while True:
        status=sample()
        passed=resources_ok(status)
        left=deadline-time.monotonic()
        if left<=0:
            append(dict(phase='opening',lock_held=True,passed=False,expired=True,**status))
            raise TimeoutError('startup resource or combined wait deadline expired')
        if passed and previously_good:
            append(dict(phase='opening',lock_held=True,passed=True,stable=True,**status))
            return
        pause=min(left,15 if passed else RESOURCE_RECHECK_S)
        append(dict(phase='opening',lock_held=True,passed=passed,stable=False,next_check_s=pause,**status))
        previously_good=passed
        time.sleep(pause)

start=time.monotonic()
with log.open() as prior:
    initial=json.loads(prior.readline())['at']
elapsed=max(0,time.time()-initial)
deadline=start+max(0,LOCK_WAIT_LIMIT_S-elapsed)
resource_deadline=min(deadline,start+max(0,policy['resource_wait_limit_s']-elapsed))
lock_path=tmp/'host-gbs.lock'
status_fields=dict(limits=settings,policy=policy,lock_path=str(lock_path),wait_started_at=initial)
write(dict(state='waiting_lock',**status_fields))
with lock_path.open('r') as lock:
    try:
        wait_for_lock(lock,deadline)
        write(dict(state='waiting_resources',lock_held=True,**status_fields))
        wait_for_resources(resource_deadline)
    except TimeoutError as error:
        write(dict(state='stopped',error=str(error),**status_fields))
        sys.exit(2)
    write(dict(state='running',lock_held=True,wait_s=time.time()-initial,**status_fields))
    n=0
    consecutive_below_six=0
    with (work/'recovery-build.log').open('w') as out:
        proc=subprocess.Popen(['/bin/bash',work/'recover-host.sh'],cwd=work,
                              stdout=out,stderr=subprocess.STDOUT,start_new_session=True,
                              pass_fds=(lock.fileno(),))
        try:
            while proc.poll() is None:
                status=sample()
                consecutive_below_six = consecutive_below_six+1 if status['mem_available']<6*GiB else 0
                append(dict(phase='working',lock_held=True,below_six_count=consecutive_below_six,**status))
                if consecutive_below_six>=2:
                    raise RuntimeError('MemAvailable fell below 6 GiB in two consecutive samples')
                unhealthy=(status['mem_available']<10*GiB or status['io_full_avg10']>=25
                           or status['mem_full_avg10']>=5 or bool(status['other_build_pids']))
                n=n+1 if unhealthy else 0
                if n>=3 or status['mem_available']<8*GiB:
                    raise RuntimeError('shared-resource pressure stopped this task')
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
        except BaseException as error:
            os.killpg(proc.pid,signal.SIGTERM)
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL)
                proc.wait()
            write(dict(state='stopped',error=repr(error),exit=proc.returncode,final=sample(),**status_fields))
            raise
    state='passed' if proc.returncode==0 and (work/'HOST_READY').is_file() else 'stopped'
    write(dict(state=state,exit=proc.returncode,final=sample(),**status_fields))
    sys.exit(state!='passed')
