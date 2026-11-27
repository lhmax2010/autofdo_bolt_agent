"""Adapt the archived K1f-3 driver to one K2c candidate and preregister its order."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys

task=Path(__file__).resolve().parent
candidate=sys.argv[1]
previous_manifest=Path(sys.argv[2])
previous_image=sys.argv[3]
args={'gcov':('K-AFDO-GCOV',20261126),'r1':('K-AFDO-R1',20261127),'hyb':('K-AFDO-HYB',20261128)}
name,seed=args[candidate]
options=sys.argv[4:]
dry_run=options==['--dry-run']
if not options or dry_run:
    board=task/candidate/('board-preflight' if dry_run else 'board')
else:
    assert len(options)==2 and options[0]=='--output-dir'
    board=Path(options[1]).resolve()
    assert board.parent==task/candidate
board.mkdir()
prior=task.parent/'k1f-3'
k2b=task.parent/'k2b-continue'
base=task.parents[1]/'kernel-afdo-k1'
variant=task/candidate/'artifacts/arm-rpi4' if not dry_run else base/'k1e/kafdo/artifacts/arm-rpi4'
physical=f'zImage-kafdo-{candidate}'
remote=f'/opt/afdo_agent/k1f-1/k2c-{candidate}'
sha=lambda p:hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
host_sdb=subprocess.check_output(['ss','-ltnp','sport = :26099'],text=True)
pid,=re.findall(r'"sdb",pid=(\d+)',host_sdb)
if dry_run:
    identity=dict(build_id='43ba5d455daec5da17e7521048767cdace012c91',
                  zImage_sha256='a663e13858334ae9bf8de1404d4965ab13856f60ee868393177a988e94eba795')
else:
    identity=json.loads((variant.parent/'variant-verification.json').read_text())['arm-rpi4']
image=variant/'arch/arm/boot/zImage'
assert sha(image)==identity['zImage_sha256']
assert (k2b/'final-plat/plat.json').is_file()
assert re.fullmatch(r'zImage-(kgcov|kafdo-(gcov|r1|hyb))',previous_image)
before=board/'expected-before-deploy.sha256'
shutil.copy2(previous_manifest,before)
files={p:h for h,p in (line.split('  ',1) for line in before.read_text().splitlines())}
assert len(files)==418 and './'+previous_image in files and './'+physical not in files
shutil.copy2(prior/'finish-verify/receipts/tryboot.txt',board/'formal-kbase.txt')
assert files['./tryboot.txt']==sha(board/'formal-kbase.txt')
for file in ('formal-N.lock.json','timing-definition.lock.json','layout-analysis.json',
             'measure.sh','mechanism.sh','smoke.sh','quiet.sh','evaluate-boot.py','fdt-compare.py','temp_check.py'):
    shutil.copy2(prior/file,board/file)

def replace_image_names(code,previous_image,physical):
    names={'zImage-kbase-s2':previous_image,'zImage-kafdo':physical}
    pattern=r'\bzImage-(?:kbase-s2|kafdo)(?![A-Za-z0-9_-])'
    return re.sub(pattern,lambda match:names[match.group()],code)


def update(file, edits, *, adapt_images=False):
    code=(prior/file).read_text()
    if adapt_images:
        code=replace_image_names(code,previous_image,physical)
    for old,new in edits:
        assert old in code,(file,old)
        code=code.replace(old,new)
    (board/file).write_text(code)

update('control.py',[
    ('43ba5d455daec5da17e7521048767cdace012c91',identity['build_id']),
])
update('analyze.py',[
    ("sys.path.insert(0,str(REPO/'workflow'))",f"sys.path.insert(0,{str(task/'locked-workflow')!r})"),
])
update('task.py',[
    ('workspace=OUT.parents[2]',f'workspace=pathlib.Path({str(task.parents[2])!r})'),
    ("prior=OUT.parent/'k1f-1b'",f'prior=pathlib.Path({str(task.parent/"k1f-1b")!r})'),
])
update('board.py',[
    ("remote=f'{REMOTE}/k1f-3'",f'remote={remote!r}'),
    ('shared_pid=276783',f'shared_pid={pid}'),
])
update('boot-afdo.sh',[
    ('task=/opt/afdo_agent/k1f-1/k1f-3',f'task={remote}'),
    ("s/^kernel=zImage-(kbase|kafdo)$/\\1/p",f"s/^kernel=zImage-(kbase|kafdo-{candidate})$/\\1/p"),
    ('[[ $existing == kbase || $existing == kafdo ]]',f'[[ $existing == kbase || $existing == kafdo-{candidate} ]]'),
    ("s/^kernel=zImage-(kbase|kafdo)$/kernel=zImage-kbase/",f"s/^kernel=zImage-(kbase|kafdo-{candidate})$/kernel=zImage-kbase/"),
    ('sed "s/^kernel=zImage-kbase$/kernel=zImage-$target/"',f'kernel_target=$target\n[[ $target != kafdo ]] || kernel_target=kafdo-{candidate}\nsed "s/^kernel=zImage-kbase$/kernel=zImage-$kernel_target/"'),
    ('$existing != "$target"', '$existing != "$kernel_target"'),
],adapt_images=True)
update('run_formal.py',[
    ("previous=OUT.parent/'k1f-2-resume'",f'previous=Path({str(task.parent/"k1f-2-resume")!r})'),
    ("lock_path=OUT.parents[1]/'host-gbs.lock'",f'lock_path=Path({str(task.parents[2]/"temp/host-gbs.lock")!r})'),
    ('WORK = OUT.parents[2]',f'WORK=Path({str(task.parents[2])!r})'),
    ("BOOT_IMAGE = WORK / 'temp/kernel-afdo-k1/k1e/kafdo/artifacts/arm-rpi4/arch/arm/boot/zImage'",f'BOOT_IMAGE=Path({str(image)!r})'),
    ('a663e13858334ae9bf8de1404d4965ab13856f60ee868393177a988e94eba795',identity['zImage_sha256']),
    ('SEED = 20261125',f'SEED = {seed}'),
    ("VARIANTS = ('K-BASE', 'K-AFDO')",f'VARIANTS = ("K-BASE", {name!r})'),
    ('stats.order(5,SEED,VARIANTS)','stats.order(3,SEED,VARIANTS)'),
    ("k_afdo_zImage_sha256=AFDO_SHA,",f"candidate_zImage_sha256=AFDO_SHA, candidate_profile_sha256={json.loads((task/candidate/'logs/result.json').read_text())['profile_sha256']!r},"),
    ('74e2d17a439d825506607b95e598b67dc78427c62d4a56385f15d19a688bb884',files['./'+previous_image]),
    ('k1f3-',f'k2c-{candidate}-'),
    ("raise Stop('quiet gate did not pass within 600 s')","raise Technical('quiet_timeout',label)"),
    ("raise Stop(f'mechanism quiet gate failed: {label}')","raise Technical('quiet_timeout',label)"),
    ("        thermal_retries=0","        gate_retries={'temperature_timeout':0,'quiet_timeout':0}"),
    ("                thermal_retries+=last['reason']=='temperature_timeout'","                if last['reason'] in gate_retries:\n                    gate_retries[last['reason']]+=1"),
    ("                if thermal_retries>1:\n                    raise Stop(f'{phase} block {number}: second temperature timeout')","                if any(count>1 for count in gate_retries.values()):\n                    raise Stop(f'{phase} block {number}: repeated board gate timeout')"),
    ("                if failure=='temperature_timeout':\n                    thermal_retries+=1\n                    if thermal_retries>1:\n                        raise Stop(f'{tag}: second temperature timeout')\n                    gate(work/'retry-cold')","                if failure in gate_retries:\n                    gate_retries[failure]+=1\n                    if gate_retries[failure]>1:\n                        raise Stop(f'{tag}: second {failure}')\n                    gate(work/'retry-cold')"),
    ("return_plat(OUT/'emergency-return',f'stop-{time.time_ns()}')","""return_plat(OUT/'emergency-return',f'stop-{time.time_ns()}')
            if (OUT/'deploy/receipts/exit').is_file() and (OUT/'deploy/receipts/exit').read_text().strip()=='0':
                select_variant(OUT/'emergency-switch','switch','kbase','emergency-finish-switch')
                board.plat(OUT/'emergency-final-plat')"""),
    ("if not (OUT/'preflight/passed.json').is_file():\n        initial()", """if not (OUT/'preflight/passed.json').is_file():
        connected,_=run(OUT/'target-connect','connect',['sdb','connect','192.168.108.26:26101'],12)
        assert connected==0
        if not (OUT/'start-cold/passed.json').is_file():
            gate(OUT/'start-cold')
        initial()"""),
],adapt_images=True)
from measurement_lock import shared_timing
formal=board/'run_formal.py'
formal.write_text(shared_timing(formal.read_text()))
script=(board/'boot-afdo.sh').read_text()
assert f'rm -- "$m/{previous_image}"' in script
assert f'publish_replace "$task/{physical}" {physical}' in script
program=formal.read_text()
assert f"expected['./{previous_image}']=='{files['./'+previous_image]}'" in program
assert f"expected['./{physical}']=AFDO_SHA" in program

for shell in board.glob('*.sh'):
    subprocess.run(['bash','-n',shell],check=True)
subprocess.run([sys.executable,board/'run_formal.py','--preregister'],check=True)
plan=json.loads((board/'preregistration.json').read_text())
assert plan['seed']==seed and plan['n']==10 and len(plan['formal'])==10 and len(plan['mechanism'])==3
assert all(set(pair)=={'K-BASE',name} for pair in plan['formal']+plan['mechanism'])
