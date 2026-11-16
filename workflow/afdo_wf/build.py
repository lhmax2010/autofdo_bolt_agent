"""Serial GBS executor with per-task scope, fresh roots and resource gates."""
import fcntl
import os
from pathlib import Path
import re
import shutil
import signal
import sys
import subprocess
import time
import uuid
from .common import require, save, sha256, GateError

GIB=1024**3

def resources(workdir):
    mem=Path('/proc/meminfo').read_text()
    return dict(time=time.time(),mem_available=int(re.search(r'MemAvailable:\s+(\d+)',mem)[1])*1024,
                load1=os.getloadavg()[0],nproc=len(os.sched_getaffinity(0)),disk_free=shutil.disk_usage(workdir).free,meminfo=mem)

def can_start(r):return r['mem_available']>=16*GIB and r['load1']<.6*r['nproc'] and r['disk_free']>=50*GIB

def stop_needed(r,previous_low):
    low=previous_low+1 if r['mem_available']<6*GIB else 0
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

def execute(argv,source,workdir,out,env=None,wait_seconds=172800):
    """No automatic retry. Stop only the unique scope created by this call."""
    workdir=Path(workdir).resolve();out=Path(out).resolve()
    require(out.is_relative_to(workdir),'output outside workdir')
    out.mkdir(parents=True,exist_ok=False)
    lock=(workdir/'temp/workflow-build.lock').open('a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise GateError('another workflow build active','environment')
    events=[];start=time.monotonic();unit='afdo-wf-'+uuid.uuid4().hex+'.scope';p=None;peak=0
    result=dict(status='failed',exit_code=None,unit=unit)
    old={}
    def interrupted(signum,frame):raise KeyboardInterrupt('signal '+str(signum))
    for sig in [signal.SIGTERM,signal.SIGINT]:old[sig]=signal.signal(sig,interrupted)
    def sample():
        nonlocal peak
        r=resources(workdir)
        cg=subprocess.run(['systemctl','--user','show',unit,'-p','ControlGroup','--value'],capture_output=True,text=True)
        path=cg.stdout.strip()
        if path.startswith('/'):
            for field in ['memory.current','memory.peak','memory.events']:
                f=Path('/sys/fs/cgroup'+path)/field
                if f.exists():r[field]=f.read_text().strip()
            peak=max(peak,int(r.get('memory.peak',0)))
        events.append(r);save(out/'resources.json',events);return r
    try:
        while not can_start(sample()):
            require(time.monotonic()-start<wait_seconds,'build start gate timeout','environment')
            time.sleep(min(600,max(1,wait_seconds-(time.monotonic()-start))))
        launch=['systemd-run','--user','--scope','--unit='+unit,'-p','MemoryMax=6G','-p','MemoryHigh=5G','-p','CPUQuota=200%','nice','-n','19','ionice','-c3',sys.executable,str(Path(__file__).with_name('build_child.py')),str(out/'child-result.json'),*argv]
        save(out/'command.json',dict(argv=launch,cwd=str(source)))
        tick=time.monotonic();low=0
        with (out/'build.log').open('w') as log:
            p=subprocess.Popen(launch,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT)
            while p.poll() is None:
                r=sample();low,stop=stop_needed(r,low)
                if stop:raise GateError('build resource stop','environment')
                try:p.wait(timeout=60)
                except subprocess.TimeoutExpired:pass
        result.update(exit_code=p.returncode,build_seconds=time.monotonic()-tick,status='success' if p.returncode==0 else 'failed')
        if (out/'child-result.json').exists():
            from .common import json_load
            child=json_load(out/'child-result.json');peak=max(peak,child['memory_peak']);result['child']=child
            require(child['exit_code']==p.returncode,'scope/child exit disagreement')
        else:
            raise GateError('child final receipt absent')
    except BaseException as e:
        result.update(error=str(e),reason=getattr(e,'reason','error'))
        if p is not None and p.poll() is None:
            stopped=subprocess.run(['systemctl','--user','stop',unit],capture_output=True,text=True)
            result['stop_result']=dict(exit_code=stopped.returncode,stdout=stopped.stdout,stderr=stopped.stderr)
            try:result['exit_code']=p.wait(timeout=60)
            except subprocess.TimeoutExpired:result['cleanup_pending']=[unit]
    finally:
        result.update(ended=time.time(),elapsed_seconds=time.monotonic()-start,memory_peak=peak,
                      min_mem_available=min((r['mem_available'] for r in events),default=None))
        save(out/'result.json',result)
        with (out/'end.log').open('a') as f:f.write('ALL-END 已结束 '+str(result['ended'])+' '+result['status']+'\n')
        for sig,handler in old.items():signal.signal(sig,handler)
        lock.close()
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
