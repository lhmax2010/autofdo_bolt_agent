"""Run K2c's candidates in order and publish each completed stage."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

task=Path(__file__).resolve().parent
repo=Path(sys.argv[1])
python=sys.executable
control=['systemctl','--user']
ordered=('gcov','r1','hyb')
original=task.parent/'k2b-continue/finish/receipts/boot-after.sha256'

def save(path,data):
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    temp.replace(path)

def read(path):
    return json.loads(path.read_text())

def state(stage, **fields):
    row=dict(stage=stage,epoch=time.time(),**fields)
    save(task/'pipeline-state.json',row)
    print(row,flush=True)

def start_unit(unit,argv,*,heavy):
    command=['systemd-run','--user','--wait',f'--unit={unit}',f'--working-directory={task}',
             '-p','CPUAccounting=yes','-p','MemoryAccounting=yes']
    if heavy:
        command += ['-p','MemoryMax=6G','-p','MemoryHigh=5G','-p','MemorySwapMax=0',
                    '-p','CPUQuota=200%','nice','-n','19','ionice','-c3']
    else:
        # This driver mainly waits for the device and runs bounded transfers.
        command += ['-p','MemoryMax=1G','-p','MemorySwapMax=0','-p','CPUQuota=100%',
                    'nice','-n','19','ionice','-c3']
    return subprocess.run([*command,*argv]).returncode

def wait_build(key,dest):
    if not dest.exists():
        return start_unit(f'kernel-k2c-{key}-build',[python,'-u',task/'build.py',key,repo],heavy=True)
    unit=f'kernel-k2c-{key}-build.service'
    while True:
        info=subprocess.check_output([*control,'show',unit,'-p','ActiveState','--value'],text=True).strip()
        receipt=dest/'logs/result.json'
        if info not in ('active','activating','deactivating','reloading'):
            return 0 if receipt.is_file() and read(receipt)['status']=='passed' else 1
        time.sleep(20)

def outcome(key, previous_manifest, previous_image):
    dest=task/key
    state('build',candidate=key)
    rc=wait_build(key,dest)
    if rc:
        build=dest/'logs/result.json'
        error=read(build).get('error','build unit did not finish successfully') if build.is_file() else 'missing build receipt'
        return dict(status='build_failed',error=error)
    proof=dest/'logs/proof-result.json'
    state('proof',candidate=key)
    if not proof.is_file():
        rc=start_unit(f'kernel-k2c-{key}-proof',[python,'-u',task/'guard-proof.py',key],heavy=True)
    else:
        rc=0 if read(proof)['status']=='passed' else 1
    if rc:
        error=read(proof).get('error','diagnostic proof did not finish successfully') if proof.is_file() else 'missing proof receipt'
        return dict(status='proof_failed',error=error)
    board=dest/'board'
    state('board',candidate=key)
    if not board.exists():
        subprocess.run([python,task/'prepare-board.py',key,previous_manifest,previous_image],check=True)
    terminal=board/'terminal.json'
    if not terminal.is_file():
        rc=start_unit(f'kernel-k2c-{key}-board-shared',[python,'-u',board/'run_formal.py'],heavy=False)
    else:
        rc=0 if read(terminal)['status']=='complete' else 1
    if not terminal.is_file():
        return dict(status='STOP',error='board unit terminated without a terminal receipt',board_unit_exit=rc)
    report=read(terminal)
    if report['status']=='complete':
        assert rc==0 and report['formal_blocks']==10 and report['mechanism_blocks']==3
        assert (board/'final-owner/plat.json').is_file()
        assert (board/'finish-verify/receipts/tryboot.txt').read_bytes()==(board/'formal-kbase.txt').read_bytes()
        return dict(status='complete',formal_blocks=10,mechanism_blocks=3)
    return dict(status=report['status'],error=report.get('reason','board gate failed'))

def main():
    manifest, image=original,'zImage-kgcov'
    for key in ordered:
        dest=task/key
        result=dest/'pipeline-result.json'
        if result.is_file():
            row=read(result)
        else:
            row=outcome(key,manifest,image)
            save(result,row)
        state('publish',candidate=key,result=row)
        if not (dest/'published.json').is_file():
            subprocess.run([python,task/'publish.py',repo,key],check=True)
        if row['status']=='complete':
            manifest=(dest/'board/finish-verify/receipts/after.sha256')
            image=f'zImage-kafdo-{key}'
        elif row['status'] in ('RECOVERY_REQUIRED','STOP'):
            state(row['status'],candidate=key,error=row.get('error'))
            return 2
        else:
            assert row['status'] in ('build_failed','proof_failed'),row
    state('summary')
    if not (task/'summary-published.json').is_file():
        subprocess.run([python,task/'publish.py',repo,'summary'],check=True)
    state('complete',commit=read(task/'summary-published.json')['commit'])
    return 0

with (task/'pipeline.lock').open('w') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    try:
        sys.exit(main())
    except Exception as error:
        state('infrastructure_stop',error=repr(error))
        raise
