"""Hold the shared heavy-work lock throughout a candidate's diagnostic replay."""
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

task=Path(__file__).resolve().parent
gib=1024**3
log=task/sys.argv[1]/'logs'
share=task.parents[1]/'host-gbs.lock'
group=Path('/sys/fs/cgroup'+Path('/proc/self/cgroup').read_text().strip().split('::',1)[1])

def sample():
    mem=int(re.search(r'MemAvailable:\s+(\d+)',Path('/proc/meminfo').read_text())[1])*1024
    avg=float(re.search(r'^full .*avg60=([\d.]+)',Path('/proc/pressure/io').read_text(),re.M)[1])
    out=dict(mem_available=mem,io_full_avg60=avg,disk_free=shutil.disk_usage(task).free,
             at=time.time(),memory_peak=int((group/'memory.peak').read_text()))
    return out

def append(file,row):
    with (log/file).open('a') as stream:
        stream.write(json.dumps(row)+'\n')
    print(row,flush=True)

def checked_admission(lock):
    begin=time.monotonic()
    end=begin+8*3600
    while time.monotonic()<end:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            append('proof-resources.jsonl',dict(at=time.time(),phase='wait_lock'))
            time.sleep(60)
            continue
        row=sample()
        passed=row['mem_available']>=16*gib and row['io_full_avg60']<20 and row['disk_free']>=50*gib
        append('proof-resources.jsonl',row|dict(phase='admission',passed=passed))
        if passed:
            return
        time.sleep(min(600,max(0,end-time.monotonic())))
    raise TimeoutError('diagnostic proof admission timed out')

def run(lock):
    checked_admission(lock)
    started=time.monotonic()
    child=None
    try:
        with (log/'proof.log').open('w') as output:
            child=subprocess.Popen([sys.executable,'-u',task/'prove.py',sys.argv[1]],
                                   stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
            low=0
            while child.poll() is None:
                row=sample()
                low=low+1 if row['mem_available']<6*gib else 0
                append('proof-resources.jsonl',row|dict(phase='runtime',low=low))
                if low>=2 or row['disk_free']<20*gib:
                    raise RuntimeError('runtime protection stopped diagnostic proof')
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    pass
        assert child.returncode==0, f'diagnostic proof exit {child.returncode}'
        assert (log.parent/'artifacts/variant-verification.json').is_file()
        return dict(status='passed',exit=0,wall_s=time.monotonic()-started,**sample())
    finally:
        if child and child.poll() is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:
                child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid,signal.SIGKILL)
                child.wait()

def interrupted(signum,_):
    raise RuntimeError(f'diagnostic proof received signal {signum}')

for sig in (signal.SIGTERM,signal.SIGINT):
    signal.signal(sig,interrupted)
try:
    with share.open('r') as lock:
        result=run(lock)
except Exception as error:
    result=dict(status='stopped',error=repr(error),**sample())
(log/'proof-result.json').write_text(json.dumps(result,indent=2)+'\n')
sys.exit(result['status']!='passed')
