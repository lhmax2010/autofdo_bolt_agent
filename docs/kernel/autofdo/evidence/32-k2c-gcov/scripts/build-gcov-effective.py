#!/usr/bin/env python3
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

task = Path(__file__).resolve().parent
workspace = task.parents[2]
repo = Path(sys.argv[2])
name = sys.argv[1]
profiles = {
    'gcov': ('31-k2b/profiles/K-AFDO-GCOV.prof','23693afab064fa7ebac233346446db7a647627c3c24f3bfb7b84dc3a90c02fa9'),
    'r1': ('29-k2a/r1/K-AFDO-R1.prof','91ea9b27da0fa9ed5bb1c3ff1ecf463d9d8fe7c7ec1f9b026cc4e8a047646418'),
    'hyb': ('31-k2b/profiles/K-AFDO-HYB.prof','f66c39f3772765d5c5f618c5d1c29f334873fbfba31b9b4efe0e12e759e745f3'),
}
relative, profile_sha = profiles[name]
profile = repo/'docs/kernel/autofdo/evidence'/relative
source = workspace/'temp/kernel-afdo-k1/k1e/source'
kbase = workspace/'temp/kernel-afdo-k1/kbase'
deps = workspace/'temp/kernel-afdo-k1/base-0fac5de6/dependencies'
frozen = task.parent/'k2b-continue'
run = task/name
run.mkdir()
logs = run/'logs'
logs.mkdir()
root = run/'gbs-root'
cgroup = Path('/sys/fs/cgroup'+Path('/proc/self/cgroup').read_text().strip().split('::',1)[1])
GiB = 1024**3
lock_path = workspace/'temp/host-gbs.lock'
result = dict(candidate=name, profile=relative, profile_sha256=profile_sha,
              source_tip='3a2602c3e12c11c4bf32f2415b02fdf8fe1ee75a', status='preflight')

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def save(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data,indent=2)+'\n')
    temp.replace(path)

def sample():
    av = int(re.search(r'MemAvailable:\s+(\d+)',Path('/proc/meminfo').read_text())[1])*1024
    io = float(re.search(r'^full .*avg60=([\d.]+)',Path('/proc/pressure/io').read_text(),re.M)[1])
    active = []
    for path in Path('/proc').iterdir():
        if not path.name.isdecimal():
            continue
        try:
            comm = (path/'comm').read_text().strip()
            if comm in {'gbs','rpmbuild','depanneur'} and (path/'stat').read_text().rsplit(')',1)[1].split()[0] != 'Z':
                active.append({'pid':int(path.name),'comm':comm})
        except (OSError,IndexError):
            pass
    return dict(at=time.time(), mem_available=av, io_full_avg60=io, load1=os.getloadavg()[0],
                nproc=len(os.sched_getaffinity(0)), disk_free=shutil.disk_usage(run).free,
                other_builds=active, memory_peak=int((cgroup/'memory.peak').read_text()),
                memory_events=(cgroup/'memory.events').read_text().strip())

def record(file, data):
    with (logs/file).open('a') as output:
        output.write(json.dumps(data)+'\n')
    print(file, data, flush=True)

def admission(lock, deadline, resource_deadline=None):
    while True:
        now = time.monotonic()
        remaining = min(deadline, resource_deadline or deadline)-now
        if remaining <= 0:
            raise TimeoutError('host gate reached the waiting limit')
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            record('admission.jsonl',dict(at=time.time(),status='waiting_lock',remaining_s=remaining))
            time.sleep(min(60,remaining))
            continue
        opening = sample()
        resource_ok = (opening['mem_available']>=16*GiB and opening['io_full_avg60']<20
                     and opening['disk_free']>=50*GiB and opening['load1']<.6*opening['nproc'])
        passed = resource_ok and not opening['other_builds']
        record('admission.jsonl',dict(passed=passed,resource_ok=resource_ok,**opening))
        if passed:
            return opening,resource_deadline
        fcntl.flock(lock,fcntl.LOCK_UN)
        if not resource_ok and resource_deadline is None:
            resource_deadline=now+10800
        delay=300 if opening['other_builds'] else 600
        time.sleep(min(delay,remaining))

def launch():
    assert sha(profile)==profile_sha
    rpm_repo = frozen/'frozen-rpm-md'
    project = frozen/'frozen-project.conf'
    manifest = json.loads((deps/'manifest.json').read_text())
    installed = json.loads((deps/'installed-matched-04.json').read_text())
    expected = {Path(row['source']).name:row['sha256'] for row in manifest}
    actual = {path.name:sha(path) for path in sorted(rpm_repo.glob('*.rpm'))}
    assert len(expected)==len(actual)==len(installed)==130 and actual==expected
    assert set(expected.values())=={row['rpm_sha256'] for row in installed}
    save(logs/'frozen.json', dict(packages=actual, project_sha256=sha(project),
                                  repomd_sha256=sha(rpm_repo/'repodata/repomd.xml')))
    exported = run/'export-src'
    subprocess.run(['git','clone','--shared','--quiet','--no-checkout',source,exported],check=True)
    subprocess.run(['git','checkout','--quiet','--detach',result['source_tip']],cwd=exported,check=True)
    packaged = exported/'packaging'/profile.name
    shutil.copy2(profile,packaged)
    assert sha(packaged)==profile_sha
    env = {key:value for key,value in os.environ.items()
           if not key.startswith(('GIT_CONFIG','KBUILD_')) and key not in
           {'LOCALVERSION','CLANG_AUTOFDO_PROFILE','VIRTUAL_ENV','KCFLAGS','KCPPFLAGS','HOSTCFLAGS'}}
    dirs = {key:run/value for key,value in [('HOME','gbs-home'),('XDG_CONFIG_HOME','xdg-config'),
                 ('XDG_CACHE_HOME','xdg-cache'),('TMPDIR','tmp')]}
    for path in dirs.values():
        path.mkdir()
    env |= {key:str(value) for key,value in dirs.items()}
    env |= dict(GIT_CONFIG_NOSYSTEM='1',SUDO_ASKPASS='/bin/false')
    config = run/'gbs.conf'
    config.write_text((kbase/'gbs-01.conf').read_text().replace(str(kbase/'tmp'),str(run/'tmp'))
                      .replace(str(kbase/'gbs-root-01'),str(root)))
    timestamp = '"Wed Nov 18 14:59:26 UTC 2026"'
    rpm_time = '%{lua:print(string.char(' + ','.join(str(ord(c)) for c in timestamp) + '))}'
    build_env = (f'JOBS=2 KBUILD_VERBOSE=1 KBUILD_BUILD_TIMESTAMP={rpm_time} '
                 'KBUILD_BUILD_USER=abuild KBUILD_BUILD_HOST=linhao-linux KBUILD_BUILD_VERSION=1')
    argv = ['/usr/bin/gbs','-c',str(config),'build','-A','armv7l','--spec','linux-rpi.spec',
            '--buildroot',str(root),'--threads','1','--skip-conf-repos','-D',str(project),
            '-R',str(rpm_repo),'--define','_smp_mflags -j2','--define','kernel_localversion -kbase',
            '--define',f'__spec_build_cmd /usr/bin/env {build_env} %{{___build_cmd}}',
            '--define',f'__spec_install_cmd /usr/bin/env {build_env} %{{___build_cmd}}',
            '--include-all','--define',f'kernel_autofdo_profile {profile.name}']
    return exported, env, argv

def interrupted(signum, _):
    raise RuntimeError(f'build wrapper received signal {signum}')

for sig in (signal.SIGTERM,signal.SIGINT):
    signal.signal(sig,interrupted)
with lock_path.open('r') as lock:
    deadline=time.monotonic()+28800
    process=None
    try:
        result['limits']={p:(cgroup/p).read_text().strip() for p in ('memory.max','memory.high','memory.swap.max','cpu.max')}
        assert result['limits']=={'memory.max':str(6*GiB),'memory.high':str(5*GiB),'memory.swap.max':'0','cpu.max':'200000 100000'},result
        assert os.getpriority(os.PRIO_PROCESS,0)==19
        assert subprocess.check_output(['ionice','-p',str(os.getpid())],text=True).strip()=='idle'
        result['status']='waiting_host'
        save(logs/'result.json',result)
        result['opening'],resource_deadline=admission(lock,deadline)
        exported,env,argv=launch()
        result['launch'],_=admission(lock,deadline,resource_deadline)
        save(logs/'command.json',dict(argv=argv,cwd=str(exported)))
        result.update(status='building',started=time.time())
        save(logs/'result.json',result)
        low=0
        with (logs/'build.log').open('w') as log:
            process=subprocess.Popen(argv,cwd=exported,env=env,stdin=subprocess.DEVNULL,
                                     stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            while process.poll() is None:
                live=sample()
                low=low+1 if live['mem_available']<6*GiB else 0
                record('resources.jsonl',dict(below_six_consecutive=low,**live))
                if low>=2 or live['disk_free']<20*GiB:
                    raise RuntimeError('running resource protection stopped the build')
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    pass
        assert process.returncode==0, f'GBS exit {process.returncode}'
        assert any(profile_sha in line and f'/SOURCES/{profile.name}' in line
                   for line in (logs/'build.log').open(errors='replace')), 'build did not print the locked profile SHA'
        result['status']='passed'
    except BaseException as error:
        result.update(status='stopped',error=repr(error))
        if process and process.poll() is None:
            os.killpg(process.pid,signal.SIGTERM)
            try:
                process.wait(timeout=35)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL)
                process.wait()
    finally:
        result.update(gbs_exit=process.returncode if process else None, ended=time.time(),final=sample())
        if 'started' in result:
            result['wall_s']=result['ended']-result['started']
        save(logs/'result.json',result)
        print(json.dumps(result,indent=2),flush=True)
sys.exit(result['status']!='passed')
