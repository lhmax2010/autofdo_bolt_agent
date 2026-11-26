"""Serial GBS executor with per-task scope, fresh roots and resource gates."""
from contextlib import nullcontext
import os
from pathlib import Path
import re
import shutil
import signal
import sys
import subprocess
import time
import uuid
from .common import json_load, require, save, sha256, GateError, StopRequested
from . import host_build
from .exits import failure_reason

GIB=1024**3

def recovery_limits(host):
    enabled = (host or {}).get('shared_host_recovery', False)
    require(type(enabled) is bool, 'host.shared_host_recovery must be boolean')
    return enabled


def io_pressure_waived(host):
    flag = (host or {}).get('recovery_io_pressure_waived', False)
    require(type(flag) is bool and (not flag or recovery_limits(host)),
            'I/O pressure waiver requires shared-host recovery limits')
    return flag


def resources(workdir, *, shared_host_recovery=False, waive_io_pressure=False):
    mem=Path('/proc/meminfo').read_text()
    sample = dict(time=time.time(),mem_available=int(re.search(r'MemAvailable:\s+(\d+)',mem)[1])*1024,
                  load1=os.getloadavg()[0],nproc=len(os.sched_getaffinity(0)),disk_free=shutil.disk_usage(workdir).free,meminfo=mem)
    if shared_host_recovery:
        io = re.search(r'^full avg10=\S+ avg60=(\d+(?:\.\d+)?) ', Path('/proc/pressure/io').read_text(), re.M)
        require(io is not None, 'host I/O pressure sampling unavailable', 'environment')
        sample['io_full_avg60'] = float(io[1])
        sample['io_pressure_waived'] = waive_io_pressure
    return sample

def startup_checks(sample):
    checks = {
        'mem_available': dict(value=sample['mem_available'], minimum=16 * GIB,
                              unit='bytes', passed=sample['mem_available'] >= 16 * GIB),
        'load1': dict(value=sample['load1'], exclusive_maximum=12,
                      passed=sample['load1'] < 12),
        'disk_free': dict(value=sample['disk_free'], minimum=50 * GIB,
                          unit='bytes', passed=sample['disk_free'] >= 50 * GIB),
    }
    if 'io_full_avg60' in sample and not sample.get('io_pressure_waived'):
        value = sample['io_full_avg60']
        checks['io_full_avg60'] = dict(value=value, maximum=20, unit='percent', passed=0 <= value <= 20)
    return checks


def can_start(sample):
    return all(check['passed'] for check in startup_checks(sample).values())


def wait_for_host(workdir, destination, timeout=10800, interval=600, exclusive=False, *, shared_host_recovery=False, waive_io_pressure=False):
    start = time.monotonic()
    history = []
    while True:
        sample = resources(workdir, shared_host_recovery=True, waive_io_pressure=waive_io_pressure) if shared_host_recovery else resources(workdir)
        sample['other_builds'] = host_build.active_builds() if exclusive else []
        history.append(sample)
        elapsed = time.monotonic() - start
        ready = can_start(sample) and (not exclusive or not sample['other_builds'])
        state = 'ready' if ready else 'timed_out' if elapsed >= timeout else 'waiting'
        save(destination, dict(status=state, wait_seconds=elapsed, samples=history))
        if ready:
            return
        require(state != 'timed_out', 'host startup gate timed out',
                'lock-timeout' if exclusive and sample['other_builds'] else 'gate')
        time.sleep(min(interval, timeout - elapsed))


def stop_needed(r,previous_low):
    guarded = 'io_full_avg60' in r
    pressure = guarded and not r.get('io_pressure_waived') and r['io_full_avg60'] >= 70
    low = previous_low+1 if r['mem_available'] < (8 if guarded else 6)*GIB or pressure else 0
    return low,low>=2 or r['disk_free']<20*GIB

def command(config,source,root,unit,macros,repo=None,buildconf=None,verbose=False):
    require(not Path(root).exists(),'buildroot must be new')
    require(not {'_smp_mflags','__make'}&macros.keys(),'reserved build macro')
    argv=['gbs','-c',str(config),'build','-A',unit['arch'],'--spec',Path(unit['spec']).name,'--include-all','--buildroot',str(root),'--threads','1','--define','_smp_mflags -j2']
    if repo is not None:
        require(buildconf is not None,'resolved buildconf required')
        argv+=['--skip-conf-repos','-R',str(repo),'-D',str(buildconf)]
    for k,v in sorted(macros.items()):
        require(re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',k) is not None and '\n' not in v,'invalid macro')
        argv+=['--define',k+' '+v]
    if verbose:argv+=['--define','__make /usr/bin/make V=1']
    return argv

def execute(argv, source, workdir, out, env=None, *, host=None, workflow='workflow',
            stage='build', invocation='GBS', separate_stderr=False):
    """Serial GBS execution. Stop only the unique scope created by this call."""
    workdir = Path(workdir).resolve()
    out = Path(out).resolve()
    require(out.is_relative_to(workdir), 'output outside workdir')
    lock = host_build.lock_path(workdir, host)
    conservative = recovery_limits(host)
    waived = io_pressure_waived(host)
    out.mkdir(parents=True, exist_ok=False)
    coordination = host_build.BuildCoordination(lock, out / host_build.WAIT_FILE, workflow, stage, invocation)
    events=[];start=time.monotonic();unit='afdo-wf-'+uuid.uuid4().hex+'.scope';p=None;peak=0
    result=dict(status='failed',exit_code=None,unit=unit)
    error = None
    old={}
    def interrupted(signum,frame):raise StopRequested(signum)
    def sample_host():
        return resources(workdir, shared_host_recovery=True, waive_io_pressure=waived) if conservative else resources(workdir)
    def sample():
        nonlocal peak
        r=sample_host()
        cg=subprocess.run(['systemctl','--user','show',unit,'-p','ControlGroup','--value'],capture_output=True,text=True)
        path=cg.stdout.strip()
        if path.startswith('/'):
            for field in ['memory.current','memory.peak','memory.events']:
                f=Path('/sys/fs/cgroup'+path)/field
                if f.exists():r[field]=f.read_text().strip()
            peak=max(peak,int(r.get('memory.peak',0)))
        events.append(r);save(out/'resources.json',events);return r
    try:
        for sig in (signal.SIGTERM, signal.SIGINT):
            old[sig] = signal.signal(sig, interrupted)
        coordination.acquire()
        ready = coordination.ready(sample_host, can_start)
        events.append(ready)
        save(out/'resources.json', events)
        result.update(start_resources=ready, wait_seconds=time.monotonic()-start)
        memory_max, memory_high, cpu_quota = ('4G','3G','100%') if conservative else ('6G','5G','200%')
        launch=['systemd-run','--user','--scope','--unit='+unit,
                '-p','MemoryMax='+memory_max,'-p','MemoryHigh='+memory_high,'-p','CPUQuota='+cpu_quota,
                'nice','-n','19','ionice','-c3',sys.executable,str(Path(__file__).with_name('build_child.py')),
                str(out/'child-result.json'),*argv]
        save(out/'command.json',dict(argv=launch,cwd=str(source)))
        tick=time.monotonic();low=0
        stderr = (out/'stderr.log').open('w') if separate_stderr else nullcontext(subprocess.STDOUT)
        with stderr as diagnostics, (out/'build.log').open('w') as log:
            p=subprocess.Popen(launch,cwd=source,env=env,stdout=log,stderr=diagnostics)
            while p.poll() is None:
                r=sample();low,stop=stop_needed(r,low)
                if stop:raise GateError('build resource stop','environment')
                try:p.wait(timeout=60)
                except subprocess.TimeoutExpired:pass
        result.update(exit_code=p.returncode,build_seconds=time.monotonic()-tick,status='success' if p.returncode==0 else 'failed')
        if (out/'child-result.json').exists():
            child=json_load(out/'child-result.json');peak=max(peak,child['memory_peak']);result['child']=child
            require(child['exit_code']==p.returncode,'scope/child exit disagreement')
        else:
            raise GateError('child final receipt absent')
        if p.returncode:
            raise GateError(f'GBS exited {p.returncode}', 'environment')
    except (Exception, StopRequested, KeyboardInterrupt) as e:
        error = e
        result.update(status='failed', error=str(e), reason=failure_reason(e))
        if p is not None and p.poll() is None:
            stopped=subprocess.run(['systemctl','--user','stop',unit],capture_output=True,text=True)
            result['stop_result']=dict(exit_code=stopped.returncode,stdout=stopped.stdout,stderr=stopped.stderr)
            try:result['exit_code']=p.wait(timeout=60)
            except subprocess.TimeoutExpired:result['cleanup_pending']=[unit]
    finally:
        try:
            coordination.finish(error)
        finally:
            for sig,handler in old.items():signal.signal(sig,handler)
        result.update(ended=time.time(),elapsed_seconds=time.monotonic()-start,memory_peak=peak,
                      min_mem_available=min((r['mem_available'] for r in events),default=None))
        save(out/'result.json',result)
        with (out/'end.log').open('a') as f:f.write('ALL-END 已结束 '+str(result['ended'])+' '+result['status']+'\n')
    return result

def freeze(rpms,buildconf,dest,snapshots,runner=subprocess.run):
    """Content-addressed RPMs, a pinned manifest and local repo metadata."""
    dest=Path(dest);require(not dest.exists(),'new archive required');require(rpms,'no dependency RPMs')
    require(shutil.which('createrepo_c'),'createrepo_c unavailable','environment')
    dest.mkdir(parents=True);items=[]
    for path in sorted(map(Path,rpms)):
        digest=sha256(path);target=dest/(digest+'.rpm');shutil.copy2(path,target)
        require(sha256(target)==digest,'archive copy mismatch')
        items.append(dict(name=path.name,file=target.name,sha256=digest))
    conf=dest/'resolved.conf';shutil.copy2(buildconf,conf)
    manifest=dict(packages=items,buildconf_sha256=sha256(conf),snapshots=snapshots,resolution_time=time.time(),offline_reproducible=False)
    save(dest/'manifest.json',manifest)
    r=runner(['createrepo_c','--workers','2',str(dest)],capture_output=True,text=True)
    save(dest/'createrepo-result.json',dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
    require(r.returncode==0,'createrepo failed');return manifest

def elf_manifest(runtime,debug,isa,runner=subprocess.run):
    def read(args):
        r=runner(args,capture_output=True,text=True);require(r.returncode==0,'ELF inspection failed: '+r.stderr);return r.stdout
    def bid(p):
        ids=re.findall(r'Build ID:\s*([0-9a-f]+)',read(['readelf','-n',str(p)]))
        require(len(ids)==1 and len(ids[0])==40,'SHA-1 build-id required');return ids[0]
    rid,did=bid(runtime),bid(debug);require(rid==did,'runtime/debug build-id mismatch','identity',3)
    soname=re.findall(r'\(SONAME\).*\[(.*?)\]',read(['readelf','-d',str(runtime)]))
    require(len(soname)==1,'SONAME absent')
    return dict(path=str(Path(runtime).resolve()),debug_path=str(Path(debug).resolve()),sha256=sha256(runtime),debug_sha256=sha256(debug),build_id=rid,isa=isa,soname=soname[0],real_name=Path(runtime).resolve().name)

def rpm_manifest(root,runner=subprocess.run):
    r=runner(['rpm','--dbpath',str(Path(root)/'var/lib/rpm'),'-qa','--qf','%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH} %{SHA256HEADER}\n'],capture_output=True,text=True)
    require(r.returncode==0 and r.stdout.strip(),'RPM manifest unavailable')
    rows=sorted(r.stdout.splitlines());require(len(rows)==len(set(rows)),'duplicate package records')
    require(all(len(row.split())==2 and re.fullmatch('[0-9a-fA-F]{64}',row.split()[1]) for row in rows),'RPM header SHA unavailable')
    return rows

def verify_repository_metadata(repomd,primary,rpms):
    """Verify saved pinned metadata and RPM checksums, not directory HTTP status."""
    import gzip
    import xml.etree.ElementTree as ET
    import hashlib
    ns={'r':'http://linux.duke.edu/metadata/repo','c':'http://linux.duke.edu/metadata/common'}
    tree=ET.parse(repomd);data=tree.find("r:data[@type='primary']",ns);require(data is not None,'primary metadata absent')
    check=data.find('r:checksum',ns);require(check is not None and check.attrib.get('type')=='sha256','primary checksum must be SHA256')
    require(sha256(primary)==check.text,'primary checksum mismatch')
    raw=Path(primary).read_bytes()
    if raw[:2]==b'\x1f\x8b':raw=gzip.decompress(raw)
    records={}
    for pkg in ET.fromstring(raw).findall('c:package',ns):
        loc=pkg.find('c:location',ns);digest=pkg.find('c:checksum',ns)
        if loc is not None and digest is not None:
            require(digest.attrib.get('type')=='sha256','RPM checksum must be SHA256')
            records[loc.attrib['href']]=digest.text
    for href,path in rpms.items():require(href in records and sha256(path)==records[href],'RPM metadata checksum mismatch: '+href)
    return dict(repomd_sha256=sha256(repomd),primary_sha256=sha256(primary),verified_rpms=len(rpms))

def extract_packages(rpms,directory,runner=subprocess.run):
    """Extract only the newly built, explicitly selected RPMs; never install them."""
    directory=Path(directory);require(not directory.exists(),'new extraction directory required')
    directory.mkdir(parents=True);manifest=[]
    for i,rpm in enumerate(rpms):
        rpm=Path(rpm);archive=directory/(str(i)+'.cpio')
        with archive.open('wb') as f:
            p=runner(['rpm2cpio',str(rpm)],stdout=f,stderr=subprocess.PIPE)
        require(p.returncode==0,'rpm2cpio failed')
        with archive.open('rb') as f:
            p=runner(['cpio','-t','--quiet'],stdin=f,capture_output=True,text=True)
        require(p.returncode==0,'cpio list failed')
        for name in p.stdout.splitlines():
            require(not Path(name).is_absolute() and '..' not in Path(name).parts,'unsafe RPM member')
        with archive.open('rb') as f:
            p=runner(['cpio','-idm','--quiet','--no-absolute-filenames'],cwd=directory,stdin=f,capture_output=True,text=True)
        require(p.returncode==0,'cpio extraction failed: '+p.stderr)
        manifest.append(dict(path=str(rpm),sha256=sha256(rpm)))
    return manifest
