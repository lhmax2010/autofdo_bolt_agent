from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
import time

root=Path(__file__).resolve().parent
board=root/'gcov/board'
old_board='kernel-k2c-gcov-board'
old_pipeline='kernel-k2c-pipeline'
new_board='kernel-k2c-gcov-board-shared'
new_pipeline='kernel-k2c-pipeline-shared'
barrier='kernel-k2c-lock-handover'
shared_lock=root.parents[1]/'host-gbs.lock'
log=root/'lock-handover.jsonl'

def command(*words):
    return subprocess.check_output([str(word) for word in words],text=True).strip()

def unit(name, arg):
    return command('systemctl','--user','show',name,'-p',arg,'--value')

def locks():
    return [line for line in command('lslocks','-o','COMMAND,PID,MODE,PATH').splitlines()
            if line.rstrip('*').endswith(str(shared_lock))]

def active_builds():
    p=subprocess.run(['ps','-C','gbs,rpmbuild,depanneur','-o','pid=,ppid=,stat=,comm='],
                     capture_output=True,text=True,check=False)
    return [line.strip() for line in p.stdout.splitlines() if line.split()[2][0] not in ('Z','X')]

def event(name, **fields):
    row=dict(event=name,at=datetime.now().astimezone().isoformat(),after_block=5,before_block=6,
             lock_rows=locks(),active_builds=active_builds(),**fields)
    with log.open('a') as out:
        out.write(json.dumps(row)+'\n')
    print(json.dumps(row),flush=True)

block=board/'formal/block-05/block.json'
deadline=time.monotonic()+180
while time.monotonic()<deadline:
    holder=unit(barrier,'MainPID')
    if holder!='0' and any(line.split()[1:3]==[holder,'READ'] for line in locks()) and block.is_file():
        break
    time.sleep(.4)
else:
    raise RuntimeError('The shared barrier did not obtain the boundary following block 5')

accepted=json.loads(block.read_text())
assert accepted['status']=='complete' and accepted['id']==5
assert len(list(board.glob('formal/block-*/block.json')))==5
assert not any((board/'formal/block-06').rglob('reboot.json'))
last=board/accepted['paired'][0]['path']
last_next=board/accepted['paired'][1]['path']
assert all(json.loads((leg/'returned/plat/plat.json').read_text())['uid']==5001 for leg in (last,last_next))
assert (last_next if accepted['order'][1]=='K-AFDO-GCOV' else last).joinpath('returned/plat/plat.json').is_file()
assert unit(old_board,'MainPID')=='544044' and unit(old_pipeline,'MainPID')=='130686'
event('boundary_verified_original_units',barrier_pid=int(holder),accepted_attempt=accepted['attempt'])
command('systemctl','--user','stop',old_pipeline)
command('systemctl','--user','stop',old_board)
assert unit(old_board,'MainPID')=='0' and unit(old_pipeline,'MainPID')=='0'
assert not (board/'terminal.json').exists()
assert not any((board/'formal/block-06').rglob('reboot.json'))
event('old_drivers_stopped_at_boundary')
command('systemd-run','--user','--unit='+new_pipeline,'--working-directory='+str(root),
        '/usr/bin/python3','-u',root/'pipeline.py',sys.argv[1])
deadline=time.monotonic()+120
while time.monotonic()<deadline:
    pid=unit(new_board,'MainPID')
    if pid not in ('0','') and any(line.split()[1:3]==[pid,'READ'] for line in locks()):
        break
    time.sleep(.5)
else:
    raise RuntimeError('Replacement board driver did not obtain the shared lock')
event('new_board_shared_lock_verified',new_board_pid=int(pid),new_pipeline_pid=int(unit(new_pipeline,'MainPID')))
(root/'lock-handover-release').touch()
