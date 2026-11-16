exec((__import__('pathlib').Path(__file__).parent/'common.py').read_text())
D=D/'stage3';D.mkdir(exist_ok=True);ops=[];uid=None;gov={};result={}
try:
 assert json.loads((D.parent/'stage2/result.json').read_text())['success']
 uid=shell('initial-uid','id -u');gov=dict(l.split('=',1) for l in shell('initial-governors','for p in /sys/devices/system/cpu/cpufreq/policy*/scaling_governor; do printf "%s=" "$p"; cat "$p"; done').splitlines());save('initial-state.json',dict(uid=uid,governors=gov))
 if uid!='0':run('root-on',['sdb','-s','192.168.108.26:26101','root','on'])
 # Recheck both source RPM-derived runtime manifest and restored prerequisites, retaining full audit.
 for e in json.loads((W/'docs/workflow/m1/evidence/07/deployment.json').read_text()):assert shell('prerequisite-sha','sha256sum '+e['target']).split()[0]==e['sha256']
 manifest=json.loads((D.parent/'base-manifest.json').read_text())
 for f in manifest:assert shell('base-sha','sha256sum '+B+'/variants/m1p-base/'+f['path']).split()[0]==f['sha256']
 for p in gov:shell('performance','printf performance > '+p)
 push(D.parent/'collect.sh',R+'/collect.sh')
 for i in range(1,4):
  shell('collect-'+str(i),'bash '+R+'/collect.sh '+str(i),1200)
  remote=R+'/train-'+str(i);local=D/('train-'+str(i));local.mkdir(exist_ok=True)
  before=shell('manifest-'+str(i),'cd '+remote+' && find . -type f -exec sha256sum {} \\;')
  run('pull-'+str(i),['sdb','-s','192.168.108.26:26101','pull',remote,str(local)])
  x=list(local.rglob('perf.data'));assert len(x)==1;p=x[0].parent
  expected={l.split(None,1)[1].removeprefix('./'):l.split()[0] for l in before.splitlines()}
  actual={str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file()};assert actual==expected,'pull mismatch'
  loaded=list((p/'maps').glob('*.loaded'));assert loaded
  for mf in loaded:
   for lib in ['libavcodec.so','libavutil.so']:
    paths=set(l.split()[-1] for l in mf.read_text().splitlines() if lib in l);assert len(paths)==1
    path=next(iter(paths));assert path.startswith(B+'/variants/m1p-base/lib/'),'mixed library'
  assert (p/'exit').read_text().strip()=='0'
  save('pull-receipt-'+str(i)+'.json',dict(verified=True,time=datetime.datetime.now().astimezone().isoformat(),remote=remote,local=str(p),files=actual,maps_verified=True))
  # Durable receipt precedes deletion; recheck manifest before removal.
  after=shell('manifest-recheck-'+str(i),'cd '+remote+' && find . -type f -exec sha256sum {} \\;');assert before==after
  shell('delete-verified-run-'+str(i),'rm -rf -- '+remote)
  save('deleted-'+str(i)+'.json',dict(remote=remote,deleted=True))
 result['success']=True
except BaseException as e:result['success']=False;result['error']=repr(e)
finally:restore();save('result.json',result)
print(json.dumps(result,indent=2))
