exec((__import__('pathlib').Path(__file__).parent/'common.py').read_text())
import shutil,random,time,sys
D=D/'measurement';D.mkdir(exist_ok=True);ops=[];uid=None;gov={};result={};rows=[];receipts=[]
class FatalGate(Exception):pass
def pull_verified(name,delete=False):
 remote=R+'/'+name;local=D/name;local.mkdir()
 before=shell('manifest-'+name,'cd '+remote+' && find . -type f -exec sha256sum {} \\;')
 run('pull-'+name,['sdb','-s','192.168.108.26:26101','pull',remote,str(local)],180)
 expected={l.split(None,1)[1].removeprefix('./'):l.split()[0] for l in before.splitlines()}
 actual={str(f.relative_to(local)):sha(f) for f in local.rglob('*') if f.is_file()};assert actual==expected,'pull verification failure'
 save('receipt-'+name+'.json',dict(time=datetime.datetime.now().astimezone().isoformat(),remote=remote,files=actual,verified=True))
 if delete:
  assert before==shell('manifest-recheck-'+name,'cd '+remote+' && find . -type f -exec sha256sum {} \\;')
  shell('delete-'+name,'rm -rf -- '+remote)
 return local
def check_maps(p,variant):
 maps=list((p/'maps').glob('*.loaded')) if (p/'maps').exists() else [p/'decoder.maps']
 if not maps:raise FatalGate('No decoder maps '+str(p))
 for mf in maps:
  text=mf.read_text()
  for lib in ['libavcodec.so','libavutil.so']:
   paths=set(l.split()[-1] for l in text.splitlines() if lib in l)
   if len(paths)!=1:raise FatalGate('Ambiguous/missing library '+str(mf))
   path=next(iter(paths));expected='/usr/lib/' if variant=='plat' else B+'/variants/m1p-'+variant+'/lib/'
   if not path.startswith(expected):raise FatalGate('Non-variant library '+path)
def oracle(name,clip,variant):
 shell('oracle-'+name,'bash '+R+'/watchdog.sh 600 bash '+R+'/oracle-variants.sh '+name+' '+B+'/inputs/'+clip+'_720p_h264_60s.mp4 '+variant.upper(),650)
 p=pull_verified(name,True);check_maps(p,variant)
 x=dict(sha256=(p/'decoded.sha256').read_text().split()[0],bytes=int((p/'decoded.bytes').read_text()),frame_notifications=int((p/'frame-notifications.count').read_text()))
 ref=json.loads((D.parent/'stage2/oracles.json').read_text())['plat-'+clip]
 if any(x[k]!=ref[k] for k in x):raise FatalGate('Correctness mismatch '+name)
 save(name+'-oracle.json',dict(variant=variant,clip=clip,match=True,**x))
def one(name,variant,block,attempt,warm=False):
 shell('measure-'+name,'bash '+R+'/watchdog.sh 1200 bash '+R+'/measure.sh '+name+' '+variant,1250)
 p=pull_verified(name,True);check_maps(p,variant)
 manifest=json.loads((D.parent/'base-manifest.json').read_text()) if variant=='base' else json.loads((D.parent/'build/afdo/artifacts.json').read_text())
 expected={P.Path(x.get('path',x.get('name'))).name:x['sha256'] for x in manifest}
 for l in (p/'runtime.sha256').read_text().splitlines():
  h,f=l.split(None,1)
  if expected.get(P.Path(f).name)!=h:raise FatalGate('runtime SHA mismatch '+f)
 wall=float(re.search(r'^real ([\d.]+)$',(p/'wall.txt').read_text(),re.M)[1]);assert wall>0
 stats={}
 for l in (p/'perf-stat.csv').read_text().splitlines():
  x=l.split(';')
  if len(x)>=3 and x[2].strip() in ['task-clock','cycles','instructions']:
   stats[x[2].strip()]=dict(value=float(x[0]),unit=x[1])
 assert set(stats)=={'task-clock','cycles','instructions'}
 samples=[];flags=[]
 for l in (p/'telemetry.txt').read_text().splitlines():
  t,*x=l.split(); samples.append((float(t),dict(s.rsplit('=',1) for s in x)))
 if not samples:flags.append('telemetry_missing')
 freqs=[];temps=[];alarms=[]
 for t,x in samples:
  for k,v in x.items():
   try:num=int(v)
   except ValueError:flags.append('telemetry_unknown');continue
   if k.endswith('_freq'):
    freqs.append(num)
    if num!=1500000:flags.append('frequency')
   elif k.endswith('/temp'):
    temps.append(num)
    if num>=80000:flags.append('temperature')
   elif k.endswith('_alarm'):
    alarms.append(num)
    if num!=0:flags.append('undervoltage')
 start=(p/'start-temperature.txt').read_text().splitlines()[-1].split();starttime=float(start[0]);starttemp=int(start[-1]);end=float((p/'end-monotonic.txt').read_text().split()[0])
 if starttemp>60000:flags.append('start_temperature')
 times=[starttime]+[x[0] for x in samples]+[end];gap=max(b-a for a,b in zip(times,times[1:]))
 if gap>2:flags.append('telemetry_gap')
 if not (freqs and temps and alarms):flags.append('telemetry_missing_source')
 row=dict(name=name,variant=variant,block=block,attempt=attempt,warmup=warm,wall_seconds=wall,perf=stats,flags=sorted(set(flags)),start_temperature=starttemp,max_temperature=max(temps,default=None),frequency_values=sorted(set(freqs)),alarm_values=sorted(set(alarms)),max_gap=gap)
 rows.append(row);save('rounds.json',rows);return row
try:
 assert json.loads((D.parent/'build/gates.json').read_text())['passed']
 uid=shell('initial-uid','id -u');gov=dict(l.split('=',1) for l in shell('initial-governors','for p in /sys/devices/system/cpu/cpufreq/policy*/scaling_governor; do printf "%s=" "$p"; cat "$p"; done').splitlines());save('initial-state.json',dict(uid=uid,governors=gov))
 if uid!='0':run('root-on',['sdb','-s','192.168.108.26:26101','root','on'])
 shell('dependencies','command -v bash && command -v taskset && command -v sleep')
 push(D.parent/'watchdog.sh',R+'/watchdog.sh')
 assert 'WATCHDOG_TIMEOUT' in shell('watchdog-negative',"bash "+R+"/watchdog.sh 1 bash -c 'sleep 10'; code=$?; test \"$code\" = 143")
 tree=D/'m1p-afdo';(tree/'lib').mkdir(parents=True)
 for p in (D.parent/'build/afdo/extracted/usr/lib').glob('lib*.so*'):shutil.copy2(p,tree/'lib'/p.name,follow_symlinks=False)
 archive=D/'afdo.tar';run('tar-afdo',['tar','-C',str(tree),'-cf',str(archive),'.']);push(archive,R+'/afdo.tar')
 shell('deploy-afdo','if test ! -e '+B+'/variants/m1p-afdo; then mkdir '+B+'/variants/m1p-afdo && tar -xf '+R+'/afdo.tar -C '+B+'/variants/m1p-afdo; fi')
 for f in json.loads((D.parent/'build/afdo/artifacts.json').read_text()):assert shell('afdo-sha','sha256sum '+B+'/variants/m1p-afdo/lib/'+f['name']).split()[0]==f['sha256']
 push(D.parent/'oracle-variants.sh',R+'/oracle-variants.sh');push(D.parent/'measure.sh',R+'/measure.sh')
 shell('preserve-failed-oracle-setup','if test -d '+R+'/pre-afdo-bbb; then test ! -e '+R+'/pre-afdo-bbb-setup-failed && mv '+R+'/pre-afdo-bbb '+R+'/pre-afdo-bbb-setup-failed; fi')
 for clip in ['bbb','tos']:oracle('pre-afdo-'+clip,clip,'afdo')
 for v in ['base','afdo']:
  src=R+'/base-tos/registry.bin' if v=='base' else str(D/'pre-afdo-tos/registry.bin')
  # Pre-AFDO oracle was pulled and deleted; push its verified registry back as the timing cache.
  if v=='base':shell('registry-base','cp '+src+' '+R+'/registry-base.bin')
  else:push(src,R+'/registry-afdo.bin')
 order=['AB']*8+['BA']*7;random.Random(20261116).shuffle(order)
 plan=dict(time=datetime.datetime.now().astimezone().isoformat(),control='BASE',candidate='AFDO',input_sha256='280fbd41f8772491ebe784aa19a3caed3bb1e8b2e64daef1d2a5a284d1f38ad1',warmup_blocks=2,N=15,order=order,order_seed=20261116,bootstrap_seed=2026111601,bootstrap_repetitions=20000,epsilon=.01,wall='bash TIMEFORMAT real %R around perf stat; seconds',retry='whole block once only for technical no-value failure; originals retained',cooldown_seconds=5,frequency_khz=1500000,measure_script_sha256=sha(D.parent/'measure.sh'),oracle_script_sha256=sha(D.parent/'oracle-variants.sh'),statistics_script_sha256=sha(D.parent/'statistics_pilot.py'),profile_sha256=json.loads((D.parent/'conversion/locked-profile.json').read_text())['sha256'])
 save('plan.json',plan);save('plan-receipt.json',dict(time=datetime.datetime.now().astimezone().isoformat(),sha256=sha(D/'plan.json'),before_first_timed_round=True))
 for p in gov:shell('performance','printf performance > '+p)
 for i in range(1,3):
  for v in ['base','afdo']:
   one('warm-'+str(i)+'-'+v,v,0,i,True);shell('cooldown','sleep 5')
 blockstatus=[]
 for i,o in enumerate(order,1):
  for attempt in [1,2]:
   success=True
   for letter in o:
    v='base' if letter=='A' else 'afdo';name='block-%02d-attempt-%d-%s'%(i,attempt,v)
    try:one(name,v,i,attempt)
    except FatalGate:raise
    except Exception as e:
     success=False;save(name+'-failure.json',dict(error=repr(e),technical=True,time=datetime.datetime.now().astimezone().isoformat()));break
    shell('cooldown','sleep 5')
   if success:break
  blockstatus.append(dict(block=i,complete=success,selected_attempt=attempt));save('blocks.json',blockstatus)
 for v in ['plat','base','afdo']:
  for clip in ['bbb','tos']:oracle('post-'+v+'-'+clip,clip,v)
 result['success']=True
except BaseException as e:result['success']=False;result['error']=repr(e)
finally:restore();save('result.json',result)
print(json.dumps(result,indent=2))
