from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
import threading
import time

from control import OUT, IDS, DEV, SDB, RecoveryRequired, Stop, checked, reboot, root, run, save, shell, snapshot
from task import plat, sha

workspace = OUT.parents[2]
task_remote = '/opt/afdo_agent/k2b-kgcov'
art = OUT / 'artifacts'
payload = OUT / 'payload'
prefix = Path('home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/build/arm-rpi4')
prior = OUT.parent / 'k1f-3'
loads = ('pipe','mmfault','tmpfs','syscall','tos')
build_lock = workspace / 'temp/host-gbs.lock'


def read(path):
    return json.loads(path.read_text())


def shared(d):
    rc, out = run(d,'sdb-listener',['ss','-ltnp','sport = :26099'],6)
    assert not rc and 'pid=12104,' in out, out


def host_builds():
    active=[]
    for path in Path('/proc').iterdir():
        if not path.name.isdecimal():
            continue
        try:
            name=(path/'comm').read_text().strip()
            state=(path/'stat').read_text().rsplit(')',1)[1].split()[0]
        except (OSError, IndexError):
            continue
        if name in ('gbs','rpmbuild','depanneur') and state!='Z':
            active.append({'pid':int(path.name), 'comm':name})
    return active


@contextmanager
def no_build(d):
    d.mkdir(parents=True,exist_ok=False)
    deadline=time.monotonic()+8*3600
    with build_lock.open('r') as lock, (d/'activity.jsonl').open('w', buffering=1) as log:
        while True:
            acquired=False
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired=True
            except BlockingIOError:
                pass
            active=host_builds()
            log.write(json.dumps(dict(at=time.time(), acquired=acquired, processes=active))+'\n')
            if acquired and not active:
                break
            if acquired:
                fcntl.flock(lock,fcntl.LOCK_UN)
            left=deadline-time.monotonic()
            if left<=0:
                raise Stop('8-hour host build gate expired')
            print('Host build gate waiting',flush=True)
            time.sleep(min(600,left))
        finished=threading.Event()
        overlap=[]
        def monitor():
            while not finished.wait(10):
                active=host_builds()
                log.write(json.dumps(dict(at=time.time(),acquired=True,processes=active))+'\n')
                overlap.extend(active)
        watcher=threading.Thread(target=monitor,daemon=True)
        watcher.start()
        try:
            yield overlap
        finally:
            finished.set()
            watcher.join()
            active=host_builds()
            log.write(json.dumps(dict(at=time.time(),acquired=True,processes=active))+'\n')
            overlap.extend(active)


def stage(d):
    d.mkdir(exist_ok=False)
    original=(prior/'finish-verify/receipts/after.sha256').read_text()
    entries={name:digest for digest,name in (line.split('  ',1) for line in original.splitlines())}
    assert len(entries)==418 and entries['./zImage-kafdo']=='a663e13858334ae9bf8de1404d4965ab13856f60ee868393177a988e94eba795'
    (d/'expected-boot-before.sha256').write_text(original)
    entries.pop('./zImage-kafdo')
    from shutil import copy2
    for f in ('deploy-board.sh','quiet.sh','train-board.sh','tmpfs-load.sh'):
        copy2(OUT/f,d/f)
    p6=OUT.parent/'k1f-1e/p6-write/receipts'
    for variant in ('plat','kbase'):
        for suffix in ('sha256','files.tsv'):
            copy2(p6/f'{variant}-after.{suffix}', d/f'expected-{variant}.{suffix}')
    for name in ('kgcov-modules.tar','kgcov.sha256','kgcov.files.tsv','expected-gcda.txt'):
        copy2(art/name,d/name)
    copy2(art/'arch/arm/boot/zImage',d/'zImage-kgcov')
    copy2(prior/'finish-verify/receipts/tryboot.txt',d/'tryboot-kbase.txt')
    line=(d/'tryboot-kbase.txt').read_bytes()
    assert line.count(b'kernel=zImage-kbase')==1
    (d/'tryboot-kgcov.txt').write_bytes(line.replace(b'kernel=zImage-kbase',b'kernel=zImage-kgcov'))
    entries['./zImage-kgcov']=sha(d/'zImage-kgcov')
    for variant, cfg in [('kgcov','kgcov'),('final','kbase')]:
        assert sha(d/'tryboot-kbase.txt')==sha(prior/'finish-verify/receipts/tryboot.txt')
        entries['./tryboot.txt']=sha(d/f'tryboot-{cfg}.txt')
        (d/f'expected-boot-{variant}.sha256').write_text(''.join(f'{entries[n]}  {n}\n' for n in sorted(entries)))
    k1=workspace/'temp/kernel-afdo-k1'
    ffmpeg=k1/'baseline-rpi4-02/BASE.tar'
    assert sha(ffmpeg)=='bc351378313b0fb71587892cfa0f1befa591e9038abfac2ef3d81bb2ea32561f'
    (d/'BASE.tar').symlink_to(ffmpeg)
    with tarfile.open(d/'kgcov-modules.tar') as archive:
        entries2=archive.getmembers()
        root_name='6.12.80-arm-rpi4-v7l-kgcov'
        for item in entries2:
            path=Path(item.name)
            assert path.parts[0]==root_name and '..' not in path.parts and not path.is_absolute()
            assert item.isfile() or item.isdir() or item.issym()
    (d/'payload.sha256').write_text(''.join(f'{sha(path)}  {path.name}\n' for path in sorted(d.iterdir())))


def push(d):
    checked(d,'staging-dir',f'mkdir {task_remote} && echo STAGING_OK','STAGING_OK',30)
    for path in sorted(payload.iterdir()):
        rc,_=run(d,'push-'+path.name,SDB+['push',path.resolve(),f'{task_remote}/{path.name}'],150)
        if rc:
            raise Stop(f'SDB push failed: {path.name}')
    checked(d,'verify-payload',f'cd {task_remote}; sha256sum -c payload.sha256 && echo PAYLOAD_OK','PAYLOAD_OK',120)


def write_board(d, mode, receipt_name=None):
    receipt_name = receipt_name or mode
    identity = plat(d/'plat')
    root(d,True)
    try:
        if mode=='modules':
            push(d)
        need=read(art/'p6-size.json')['minimum_free_bytes']
        try:
            checked(d,'write',f'bash {task_remote}/deploy-board.sh {mode} {identity["boot_id"]} {need} {receipt_name}',
                    'BOARD_WRITE_OK',270)
        finally:
            rc,_=run(d,'pull-receipt',SDB+['pull',f'{task_remote}/{receipt_name}-receipts',d/'receipts'],120)
            if rc:
                raise Stop(f'Cannot read deployment receipt: {mode}')
        assert (d/'receipts/exit').read_text().strip()=='0'
    finally:
        root(d,False)


def cool(d, limit_s=3600):
    """Opening condition before first direct boot and after a thermal failure."""
    start=time.monotonic()
    trial=0
    command=r'''set -eu
test "$(id -u)" = 5001
test "$(uname -r)" = 6.12.80-arm-rpi4-v7l
boot_id=$(cat /proc/sys/kernel/random/boot_id)
for ((i=0; i<30; i++)); do
    read -r up _ < /proc/uptime
    read -r t < /sys/class/thermal/thermal_zone0/temp
    read -r g < /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
    printf '%s\t%s\t%s\n' "$up" "$t" "$g"
    sleep 10
done
test "$(cat /proc/sys/kernel/random/boot_id)" = "$boot_id"
echo COOL_WINDOW_OK'''
    from statistics import median
    while True:
        trial+=1
        values=checked(d,f'window-{trial}',f'bash -c {shlex.quote(command)}','COOL_WINDOW_OK',325).splitlines()
        rows=[line.split() for line in values if '\t' in line]
        assert len(rows)==30,values
        temperature=median(int(line[1]) for line in rows)
        save(d/f'window-{trial}.json',dict(samples=len(rows),median_mC=temperature,elapsed_s=time.monotonic()-start))
        print(f'PLAT idle-window median {temperature/1000:.3f} C',flush=True)
        if temperature<=58000:
            save(d/'gate-result.json',dict(status='passed',median_mC=temperature,elapsed_s=time.monotonic()-start,ended_at=time.time()))
            return
        delay=600-(time.monotonic()-start)%600
        if time.monotonic()-start+delay+300>limit_s:
            save(d/'gate-result.json',dict(status='timeout',median_mC=temperature,
                 elapsed_s=time.monotonic()-start,limit_s=limit_s,windows=trial))
            raise Stop('PLAT idle temperature gate expired')
        time.sleep(delay)


class TemperatureTimeout(Stop):
    pass


def read_done_marker(d, name, command, marker, timeout):
    rc,out=shell(d,name,command+'; rc=$?; printf "REMOTE_EXIT=%s\\n" "$rc"',timeout)
    if rc!=0 or marker not in out.splitlines() or 'REMOTE_EXIT=0' not in out.splitlines():
        if 'REMOTE_EXIT=76' in out.splitlines():
            raise TemperatureTimeout(name)
        raise Stop(f'{name} failed with SDB exit {rc}')
    return out


def load_receipt(d, load, remote):
    local=d/load
    local.mkdir()
    rc,_=run(d,f'pull-{load}-metadata',SDB+['pull',f'{remote}/{load}',local/'board'],120)
    if rc:
        raise Stop('could not pull workload metadata: '+load)
    rc,_=run(d,f'pull-{load}-archive',SDB+['pull',f'{remote}/tmp/{load}.gcda.tar',local/'gcda.tar'],180)
    if rc:
        raise Stop('could not pull gcda: '+load)
    board=local/'board'
    digest=(board/'archive.sha256').read_text().split()[0]
    assert sha(local/'gcda.tar')==digest
    assert (board/'exit').read_text().strip()=='0'
    root_path=local/'raw'
    manifest={p.removeprefix('./'):h for h,p in (row.split('  ',1) for row in (board/'gcda.sha256').read_text().splitlines())}
    with tarfile.open(local/'gcda.tar') as source:
        files={str(Path(member.name)) for member in source.getmembers() if member.isfile()}
        assert files==set(manifest)
        assert all(f.endswith('.gcda') for f in files)
        assert all(m.isfile() or m.isdir() for m in source.getmembers())
        source.extractall(root_path,filter='data')
    for relative,h in manifest.items():
        assert sha(root_path/relative)==h
    actual={Path(name).relative_to(prefix).as_posix() for name in manifest}
    expected=set((art/'expected-gcda.txt').read_text().splitlines())
    assert expected <= actual, (load, sorted(expected-actual))
    notes={str(p.relative_to(art/'gcno')) for p in (art/'gcno').rglob('*.gcno')}
    assert {str(Path(x).with_suffix('.gcno')) for x in actual} <= notes, load
    tsv=[line.split('\t') for line in (board/'telemetry.tsv').read_text().splitlines()]
    train_rows=[row for row in tsv if row[1]=='run']
    prestart=[row for row in tsv if row[1]=='prestart']
    assert len(prestart)==1 and 0<int(prestart[0][2])<=60000
    assert all(row[4]=='performance' for row in train_rows)
    save(local/'receipt.json',dict(workload=load, gcda_files=len(actual), archive_sha256=digest,
         archive_bytes=(local/'gcda.tar').stat().st_size, temp_start_mC=int(prestart[0][2]),
         temp_max_mC=max(int(x[2]) for x in train_rows), observed_freq_kHz=sorted({int(x[3]) for x in train_rows}),
         started_uptime=float((board/'workload-start.uptime').read_text()),
         stopped_uptime=float((board/'workload-stop.uptime').read_text())))
    checked(d,f'release-{load}-archive',f'rm -- {remote}/tmp/{load}.gcda.tar && echo ARCHIVE_RELEASED','ARCHIVE_RELEASED',30)


def return_plat(d,label):
    current=d/'current'
    rc,out=shell(current,'verify-uid-and-id',"id -u; tr -d '\\000' </proc/device-tree/serial-number; echo; sha256sum /sys/kernel/notes",30)
    info=out.splitlines()
    assert not rc and len(info)==3 and info[1]=='100000004694d889',info
    if info[0]=='0':
        root(current/'root-recovery',False)
    elif info[0]!='5001':
        raise Stop('Unexpected UID')
    if not info[2].startswith('146a4e2d'):
        reboot(d/'boot','plat')
        snapshot(d/'boot','plat',f'{task_remote}/{label}-plat')
    return plat(d/'verified')


def session(number, retry=False, resumed=False):
    suffix = '-retry' if retry else '-resume' if resumed and number == 1 else ''
    label = f'session-{number:02d}{suffix}'
    d=OUT/label
    remote=f'{task_remote}/{label}'
    with no_build(d/'host') as overlap:
        if number==1 and not retry and not (OUT/'deploy/receipts/exit').is_file():
            write_board(OUT/'deploy','deploy')
        assert (OUT/'deploy/receipts/exit').read_text().strip()=='0'
        i=plat(d/'before')
        rc,out=shell(d/'before','start-temp','cat /sys/class/thermal/thermal_zone0/temp',30)
        assert not rc and out.strip().isdecimal()
        active=host_builds()
        save(d/'before-tryboot.json',dict(board=i, temp_mC=int(out.strip()), host_builds=active, lock_held=True))
        assert not active and not overlap, active or overlap
        boot=d/'boot'
        if number==1 and not retry and not resumed:
            ready=time.time()
            save(OUT/'first-tryboot-ready.json',dict(at=ready,boot_id=i['boot_id']))
            print('K-GCOV boot_a verified. Waiting for HDMI observation notice.',flush=True)
            notice=OUT/'first-tryboot-notified.json'
            deadline=time.monotonic()+180
            while not notice.is_file():
                if time.monotonic()>=deadline:
                    raise Stop('HDMI observation notice not received before first tryboot')
                time.sleep(0.25)
            assert read(notice)['at']>=ready and read(notice)['previous_boot_id']==i['boot_id']
        reboot(boot,'kgcov')
        try:
            snapshot(boot,'kgcov',remote)
            root(d/'training',True)
            try:
                checked(d/'training','quiet',f'bash {task_remote}/quiet.sh {remote}','QUIET_OK',630)
                checked(d/'training','init',f'bash {task_remote}/train-board.sh {label} init','GCOV_INIT_OK',80)
                if number==1 and not retry and not resumed:
                    info=read(boot/'reboot-result.json')
                    save(OUT/'first-boot-accepted.json',dict(at=time.time(),boot_id=info['boot_id'],
                         build_id=IDS['kgcov'],expected_gcda=len((art/'expected-gcda.txt').read_text().splitlines())))
                for load in loads:
                    print(f'{label} GCOV segment {load}',flush=True)
                    read_done_marker(d/'training',load,f'bash {task_remote}/train-board.sh {label} {load}',
                                     'GCOV_SEGMENT_OK',990)
                    load_receipt(d/'training',load,remote)
                for name in ('quiet-gate.tsv','quiet-top5.txt','meminfo.quiet','tos.sha256','gcda-at-boot.paths'):
                    rc,_=run(d/'training','pull-'+name,SDB+['pull',f'{remote}/{name}',d/name],70)
                    assert not rc
            finally:
                try:
                    checked(d/'training','cleanup',f'bash {task_remote}/train-board.sh {label} cleanup',
                            'GCOV_CLEANUP_OK',60)
                finally:
                    root(d/'training',False)
        except RecoveryRequired:
            raise
        except Exception:
            return_plat(d/'return',label)
            raise
        else:
            return_plat(d/'return',label)
        assert not overlap, overlap
    save(d/'session.json',dict(status='complete',boot=read(boot/'reboot-result.json'),
                              workloads=[read(d/'training'/load/'receipt.json') for load in loads]))
    return label


def repair_board(d):
    plat(d/'plat')
    root(d, True)
    try:
        command = f'mkdir {task_remote}/before-export-fix'
        checked(d, 'backup-dir', command+' && echo BACKUP_OK', 'BACKUP_OK', 30)
        for name in ('train-board.sh', 'deploy-board.sh'):
            rc, _ = run(d, 'push-'+name, SDB+['push', OUT/name, f'{task_remote}/{name}.next'], 40)
            if rc:
                raise Stop(f'Could not upload updated {name}')
            digest = sha(OUT/name)
            command = (f'cd {task_remote}; test "$(sha256sum -- {name}.next | cut -d" " -f1)" = {digest} && '
                       f'bash -n {name}.next && cp -- {name} before-export-fix/{name} && '
                       f'mv -- {name}.next {name} && test "$(sha256sum -- {name} | cut -d" " -f1)" = {digest} && '
                       'echo SCRIPT_OK')
            checked(d, 'activate-'+name, command, 'SCRIPT_OK', 40)
    finally:
        root(d, False)


def main(action):
    assert (OUT/'HOST_READY').is_file()
    IDS['kgcov']=read(art/'image-identity.json')['build_id']
    shared(OUT/f'board-shared-{action}')
    if action=='prepare':
        if not (OUT/'modules/receipts/exit').is_file():
            with no_build(OUT/'modules-build-gate'):
                stage(payload)
                write_board(OUT/'modules','modules')
        assert (OUT/'modules/receipts/exit').read_text().strip()=='0'
        cool(OUT/'cool-before-first',limit_s=7200)
        return
    assert action in ('train', 'resume')
    resumed = action == 'resume'
    assert read(OUT/'cool-before-first/gate-result.json')['status']=='passed'
    receipt_name = 'finish'
    if resumed:
        assert read(OUT/'first-boot-accepted.json')['build_id'] == IDS['kgcov']
        assert 'cmp: command not found' in (OUT/'session-01/training/pipe.stdout').read_text()
        assert (OUT/'failure-finish/receipts/exit').read_text().strip() == '0'
        receipt_name = 'finish-resume'
        with no_build(OUT/'resume-build-gate'):
            repair_board(OUT/'resume-scripts')
            write_board(OUT/'rearm', 'rearm')
    runs=[]
    try:
        for n in range(1,4):
            try:
                label=session(n, resumed=resumed)
            except TemperatureTimeout:
                cool(OUT/f'retry-{n}-temperature')
                label=session(n, retry=True, resumed=resumed)
            runs.append(label)
    except RecoveryRequired:
        raise
    except Exception:
        deployed=OUT/'deploy/receipts/exit'
        if deployed.is_file() and deployed.read_text().strip()=='0':
            with no_build(OUT/f'failure-{receipt_name}-build-gate'):
                write_board(OUT/f'failure-{receipt_name}', 'finish', receipt_name)
        raise
    with no_build(OUT/'finish-build-gate'):
        write_board(OUT/'finish', 'finish', receipt_name)
        plat(OUT/'final-plat')
        shared(OUT/'final-shared')
    save(OUT/'board-result.json',dict(status='complete',sessions=runs))


if __name__=='__main__':
    os.environ['PATH']=str(OUT/'bin')+':'+os.environ['PATH']
    with (OUT/'board-owner.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            main(sys.argv[1])
        except RecoveryRequired as error:
            save(OUT/'board-result.json',dict(status='RECOVERY_REQUIRED',error=repr(error)))
            raise
        except BaseException as error:
            save(OUT/'board-result.json',dict(status='STOP',error=repr(error)))
            raise
