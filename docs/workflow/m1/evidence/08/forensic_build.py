exec((__import__('pathlib').Path(__file__).parent/'common.py').read_text())
import time,shutil
D=D/'build/forensic';D.mkdir(exist_ok=True);ops=[];result={};events=[]
def resources():
 m=int(next(l.split()[1] for l in P.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
 return dict(time=datetime.datetime.now().astimezone().isoformat(),mem_available=m,load1=os.getloadavg()[0],nproc=int(sp.check_output(['nproc'],text=True)),disk_free=shutil.disk_usage(W).free)
def pkglist(root):
 return '\n'.join(sorted(run('rpm-lock',['rpm','--dbpath',str(root/'var/lib/rpm'),'-qa','--qf','%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH} %{SHA256HEADER}\n']).splitlines()))+'\n'
try:
 old=W/'temp/m1-target-20261114/weekend-j2/roots/thumb-attempt-0/local/BUILD-ROOTS/scratch.armv7l.0';original=pkglist(old);(D/'BASE.rpm-lock.txt').write_text(original)
 for x in ['home','tmp','cache','config','state','roots']:(D/x).mkdir(exist_ok=True)
 for variant in ['base-r','afdo']:
  out=D/variant;out.mkdir();root=D/'roots'/(variant+'-localpath');assert not root.exists()
  start=time.monotonic()
  while True:
   r=resources();events.append(dict(phase='start-gate',variant=variant,**r));save('resources.json',events)
   if r['mem_available']>=16*1024**3 and r['load1']<.6*r['nproc'] and r['disk_free']>=50*1024**3:break
   if time.monotonic()-start>=600:raise RuntimeError('host resource start gate timeout (600 s)')
   time.sleep(30)
  env=os.environ.copy();env.update(HOME=str(D/'home'),TMPDIR=str(D/'tmp'),TMP=str(D/'tmp'),TEMP=str(D/'tmp'),XDG_CACHE_HOME=str(D/'cache'),XDG_CONFIG_HOME=str(D/'config'),XDG_STATE_HOME=str(D/'state'),CCACHE_DIR=str(D/'cache/ccache'),GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_COUNT='2',GIT_CONFIG_KEY_0='gc.auto',GIT_CONFIG_VALUE_0='0',GIT_CONFIG_KEY_1='maintenance.auto',GIT_CONFIG_VALUE_1='false',SUDO_ASKPASS='/bin/false')
  for k in ['V','MAKEFLAGS','MFLAGS']:env.pop(k,None)
  cmd=['gbs','-c',str(D.parent/'frozen.conf'),'build','-A','armv7l','--spec','ffmpeg.spec','--include-all','--skip-conf-repos','-R',str(D.parent/'repo'),'-D',str(D.parent/'repo/tizen_unified_standard.conf'),'--buildroot',str(root),'--threads','1','--define','_smp_mflags -j2','--define','profile_isa thumb']
  if variant=='afdo':cmd+=['--define','with_autofdo 1']
  cmd+=['--define','__make /usr/bin/make V=1']
  unit='m1p-v02-forensic-'+variant
  argv=['systemd-run','--user','--scope','--unit='+unit,'-p','MemoryMax=6G','-p','MemoryHigh=5G','-p','CPUQuota=200%','nice','-n','19','ionice','-c3',*cmd]
  save(variant+'/command.json',dict(command=argv,cwd=str(D.parent/'ffmpeg'),environment={k:env[k] for k in ['HOME','TMPDIR','XDG_CACHE_HOME','XDG_CONFIG_HOME','XDG_STATE_HOME','CCACHE_DIR']}))
  tick=time.monotonic();low=0;reason=None
  with (out/'build.log').open('w') as f:
   p=sp.Popen(argv,cwd=D.parent/'ffmpeg',env=env,stdout=f,stderr=sp.STDOUT)
   try:
    while p.poll() is None:
     r=resources();events.append(dict(phase='building',variant=variant,**r));save('resources.json',events)
     low=low+1 if r['mem_available']<6*1024**3 else 0
     if low>=2 or r['disk_free']<20*1024**3:
      reason='resource stop';run('stop-own-unit',['systemctl','--user','stop',unit+'.scope']);break
     try:p.wait(timeout=60)
     except sp.TimeoutExpired:pass
   except BaseException:
    run('stop-own-unit',['systemctl','--user','stop',unit+'.scope'],check=False);raise
   rc=p.wait()
  save(variant+'/result.json',dict(exit=rc,seconds=time.monotonic()-tick,reason=reason,buildroot=str(root)))
  if reason or rc:raise RuntimeError(variant+' build failed '+str(rc)+' '+str(reason))
  scratch=root/'local/BUILD-ROOTS/scratch.armv7l.0';lock=pkglist(scratch);(out/'rpm-lock.txt').write_text(lock)
  assert lock==original,variant+' installed package/header lock mismatch'
 result['success']=True
except BaseException as e:result['success']=False;result['error']=repr(e)
finally:save('result.json',result)
print(json.dumps(result,indent=2))
