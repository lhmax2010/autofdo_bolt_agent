import subprocess as sp, pathlib as P, json, hashlib, datetime, re, shlex, os, signal
W=P.Path.cwd(); D=W/'temp/m1-pilot-v02-20261116'; B='/opt/afdo_agent'; R=B+'/work/m1p-v02-20261116'; ops=[]
def save(n,x):
 p=D/n
 with p.open('w') as f: json.dump(x,f,indent=2,ensure_ascii=False); f.write('\n'); f.flush(); os.fsync(f.fileno())
def run(n,a,timeout=120,check=True):
 t=datetime.datetime.now().astimezone().isoformat()
 try:
  q=sp.run(a,capture_output=True,text=True,timeout=timeout); d=dict(name=n,time=t,argv=a,exit=q.returncode,stdout=q.stdout,stderr=q.stderr)
 except BaseException as e:
  d=dict(name=n,time=t,argv=a,error=repr(e));ops.append(d);save('operations.json',ops);raise
 ops.append(d);save('operations.json',ops)
 if check and q.returncode: raise RuntimeError(n+': '+q.stderr+q.stdout)
 return q.stdout
def shell(n,c,timeout=120):
 o=run(n,['sdb','-s','192.168.108.26:26101','shell','( '+c+' ); rc=$?; printf "\\n__M1P_RC__=%s\\n" "$rc"'],timeout)
 m=re.search(r'\n__M1P_RC__=(\d+)\s*$',o)
 if not m or m[1]!='0':raise RuntimeError(n+': '+o)
 return o[:m.start()].replace('\r\n','\n').rstrip()
def sha(p):return hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()
def push(p,t):run('push-'+str(p),['sdb','-s','192.168.108.26:26101','push',str(p),t])
def restore():
 global uid
 errors=[]
 if gov:
  for p,v in gov.items():
   try:
    now=shell('restore-read-governor','cat '+shlex.quote(p))
    if now!=v:shell('restore-governor','printf %s '+shlex.quote(v)+' > '+shlex.quote(p))
   except BaseException as e:errors.append(repr(e))
 if uid is not None:
  try:
   now=shell('restore-read-uid','id -u')
   if now!=uid:run('root-restore',['sdb','-s','192.168.108.26:26101','root','on' if uid=='0' else 'off'])
   result['final_uid']=shell('final-uid','id -u'); assert result['final_uid']==uid
  except BaseException as e:errors.append(repr(e))
 result['cleanup_pending']=errors
uid=None;gov={};result={}
def interrupted(sig,frame):raise RuntimeError('signal '+str(sig))
for s in (signal.SIGTERM,signal.SIGINT):signal.signal(s,interrupted)
try:
 run('devices',['sdb','devices'])
 expected=json.loads((W/'docs/workflow/m1/evidence/02/board-check-02/queries.json').read_text()); ident=[]
 for e in expected:
  got=shell('identity',e['command'][-1]); ok=got==e['stdout'].replace('\r\n','\n').rstrip();ident.append(dict(command=e['command'][-1],actual=got,match=ok));assert ok,'Identity mismatch'
 save('identity.json',ident)
 uid=shell('initial-uid','id -u'); g=shell('initial-governors','for p in /sys/devices/system/cpu/cpufreq/policy*/scaling_governor; do printf "%s=" "$p"; cat "$p" || exit; done')
 gov=dict(l.split('=',1) for l in g.splitlines());save('initial-state.json',dict(uid=uid,governors=gov));result['initial_uid']=uid;result['initial_governors']=gov
 if uid!='0':run('root-on',['sdb','-s','192.168.108.26:26101','root','on'])
 assert shell('root-check','id -u')=='0'
 manifest=json.loads((W/'docs/workflow/m1/evidence/07/deployment.json').read_text())
 for e in manifest:assert shell('prerequisite-sha','sha256sum '+shlex.quote(e['target'])).split()[0]==e['sha256']
 shell('space','df -Pk /opt/afdo_agent')
 # Extract only the six runtime lib RPMs, verify original RPM identities.
 ext=D/'base-extracted';ext.mkdir(exist_ok=True)
 rpms=json.loads((W/'docs/workflow/m1/evidence/04/thumb-attempt-0/rpms.json').read_text());chosen=[]
 for e in rpms:
  if not e['name'].startswith('lib') or '-' in e['name']:continue
  p=W/e['path'];assert sha(p)==e['sha256'];chosen.append(e)
  cpio=D/(e['name']+'.cpio')
  with cpio.open('wb') as f:sp.run(['rpm2cpio',str(p)],stdout=f,check=True)
  run('extract-'+e['name'],['bash','-c','cd "$1" && cpio -idm --quiet < "$2"','bash',str(ext),str(cpio)])
 save('base-rpms.json',chosen)
 files=[]
 for p in sorted((ext/'usr/lib').glob('lib*.so*')):
  files.append(dict(path='lib/'+p.name,symlink=os.readlink(p) if p.is_symlink() else None,sha256=sha(p),bytes=p.stat().st_size))
 assert len(chosen)==6
 tree=D/'m1p-base';(tree/'lib').mkdir(parents=True,exist_ok=True)
 import shutil
 for p in (ext/'usr/lib').glob('lib*.so*'):shutil.copy2(p,tree/'lib'/p.name,follow_symlinks=False)
 save('base-manifest.json',files)
 archive=D/'base.tar';run('tar',['tar','-C',str(tree),'-cf',str(archive),'.'])
 shell('new-work','test ! -e '+R+' && mkdir '+R+' && mkdir '+R+'/home '+R+'/tmp '+R+'/cache '+R+'/buildid')
 push(archive,R+'/base.tar')
 shell('deploy-base','test ! -e '+B+'/variants/m1p-base && mkdir '+B+'/variants/m1p-base && tar -xf '+R+'/base.tar -C '+B+'/variants/m1p-base')
 for f in files:
  p=B+'/variants/m1p-base/'+f['path'];assert shell('base-sha','sha256sum '+p).split()[0]==f['sha256']
  if f['symlink']:assert shell('base-link','readlink '+p)==f['symlink']
 env='export HOME='+R+'/home TMPDIR='+R+'/tmp XDG_CACHE_HOME='+R+'/cache PERF_CONFIG='+R+'/perf.conf LD_LIBRARY_PATH='+B+'/lib; '
 shell('cycles-record',env+B+'/tools/perf --buildid-dir '+R+'/buildid record --buildid-mmap -e cycles -c 1000003 -o '+R+'/cycles.data -- taskset -c 3 sleep 1')
 ev=shell('cycles-evlist',env+B+'/tools/perf evlist -v -i '+R+'/cycles.data');save('cycles-evlist.json',ev)
 assert re.search(r'^cycles:',ev) and re.search(r'\btype\s+0\b',ev) and re.search(r'\bconfig\s+0\b',ev),'cycles event invalid'
 tele=shell('telemetry-capability','set -e; for p in /sys/devices/system/cpu/cpufreq/policy*; do for f in scaling_governor scaling_cur_freq cpuinfo_cur_freq scaling_min_freq scaling_max_freq; do printf "%s=" "$p/$f"; cat "$p/$f"; done; done; for z in /sys/class/thermal/thermal_zone*; do printf "%s " "$z"; cat "$z/type" "$z/temp"; done; for h in /sys/class/hwmon/hwmon*; do printf "%s " "$h"; cat "$h/name"; if test -e "$h/in0_lcrit_alarm"; then cat "$h/in0_lcrit_alarm"; fi; done')
 save('telemetry-capability.json',tele)
 result['success']=True
except BaseException as e:
 result['success']=False;result['error']=repr(e)
finally:
 restore();save('result.json',result)
print(json.dumps(result,ensure_ascii=False,indent=2))
