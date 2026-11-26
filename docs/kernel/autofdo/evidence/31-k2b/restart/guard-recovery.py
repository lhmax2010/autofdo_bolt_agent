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
group=Path('/sys/fs/cgroup'+Path('/proc/self/cgroup').read_text().strip().split('::',1)[1])
log=work/'recovery-resources.jsonl'
result=work/'recovery-result.json'

def sample():
    available = next(int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()
                     if line.startswith('MemAvailable:'))
    def pressure(kind,field):
        row=next(line.split() for line in Path(f'/proc/pressure/{kind}').read_text().splitlines()
                 if line.startswith(field+' '))
        return float(row[1].split('=',1)[1])
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
                io_full_avg10=pressure('io','full'),mem_full_avg10=pressure('memory','full'),
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
write(dict(state='waiting',limits=settings))
start=time.monotonic()
initial=next((json.loads(line)['at'] for line in log.read_text().splitlines()),time.time()) if log.is_file() else time.time()
deadline=start+max(0,8*3600-(time.time()-initial))
resource_deadline=initial+3*3600
with (tmp/'host-gbs.lock').open('r') as lock:
    previous_good=False
    while time.monotonic()<deadline:
        status=sample()
        safe=(status['mem_available']>=16*GiB and status['load1']<.6*len(os.sched_getaffinity(0))
              and status['disk_free']>=50*GiB and status['io_full_avg10']<=5
              and status['mem_full_avg10']<=1 and not status['other_build_pids'])
        append({'phase':'opening','passed':safe,**status})
        if not safe and time.time()>=resource_deadline:
            write(dict(state='stopped',error='three-hour startup resource gate expired',limits=settings,final=status))
            sys.exit(2)
        if safe and previous_good:
            try:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:
                previous_good=False
            else:
                if not sample()['other_build_pids']:
                    break
                fcntl.flock(lock,fcntl.LOCK_UN)
        previous_good=safe
        time.sleep(15 if safe else 60)
    else:
        write(dict(state='stopped',error='opening resource/lock gate expired',limits=settings))
        sys.exit(2)
    write(dict(state='running',limits=settings,wait_s=time.monotonic()-start))
    n=0
    with (work/'recovery-build.log').open('w') as out:
        proc=subprocess.Popen(['/bin/bash',work/'recover-host.sh'],cwd=work,
                              stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            while proc.poll() is None:
                status=sample()
                append({'phase':'working',**status})
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
            write(dict(state='stopped',error=repr(error),exit=proc.returncode,limits=settings,final=sample()))
            raise
    state='passed' if proc.returncode==0 and (work/'HOST_READY').is_file() else 'stopped'
    write(dict(state=state,exit=proc.returncode,limits=settings,final=sample()))
    sys.exit(state!='passed')
