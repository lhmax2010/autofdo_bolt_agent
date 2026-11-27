import datetime
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import time

task=Path(__file__).resolve().parent
flock_path=task.parents[1]/'host-gbs.lock'
out=task/'lock-handover.jsonl'
go=task/'lock-handover-release'
target_pid=544044

def note(event):
    result=subprocess.run(['ps','-C','gbs,rpmbuild,depanneur','-o','pid=,ppid=,stat=,comm='],
                          capture_output=True,text=True,check=False)
    active=[line.strip() for line in result.stdout.splitlines()
            if line.split()[2][0] not in ('Z','X')]
    locks=subprocess.check_output(['lslocks','-o','COMMAND,PID,MODE,PATH'],text=True)
    row=dict(event=event,time=datetime.datetime.now().astimezone().isoformat(),
             pid=os.getpid(),board_pid=target_pid,
             lock_inode=flock_path.stat().st_ino,active_build_processes=active,
             shared_lock_rows=[line for line in locks.splitlines() if line.rstrip('*').endswith(str(flock_path))])
    with out.open('a') as f:
        f.write(json.dumps(row)+'\n')
    print(row,flush=True)
    return row

with flock_path.open('r') as fd:
    note('queued_shared_before_current_block_end')
    fcntl.flock(fd,fcntl.LOCK_SH)
    note('shared_barrier_acquired')
    deadline=time.monotonic()+900
    while time.monotonic()<deadline and not go.exists():
        time.sleep(.2)
    note('shared_barrier_releasing' if go.exists() else 'shared_barrier_timeout')
