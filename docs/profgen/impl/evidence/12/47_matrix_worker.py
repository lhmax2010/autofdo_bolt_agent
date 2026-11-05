import sys,os,time,json,re,shlex,hashlib,subprocess,signal,threading,math,datetime
from pathlib import Path
from decimal import Decimal,InvalidOperation
from connection import *
sys.path.insert(0,str(W/'tools/profgen'))
from pull_verified_run import SDB,pull_verify_delete
S=SDB(device);original=json.loads((D/'identity.json').read_text());stop=threading.Event();cancel=False;started=time.monotonic();records=[];phase='matrix'
OLD=W/'temp/board-round1-resume2';manifest={l.split('\t')[0]:l.split('\t') for l in (W/'temp/eval-prep11/payload-rpi4/eval-manifest.tsv').read_text().splitlines()}
for sub in ['runs','receipts']:(D/sub).mkdir(exist_ok=True)
def cancellation(sig,frame):
 global cancel
 cancel=True
 print('STOP REQUESTED',sig,'current RUN will finish and transfer before restoration',flush=True)
signal.signal(signal.SIGINT,cancellation);signal.signal(signal.SIGTERM,cancellation)
def monitor():
 while not stop.is_set():
  try:r={'time':datetime.datetime.now().astimezone().isoformat(),'host':subprocess.check_output(['free','-m'],text=True)+subprocess.check_output(['uptime'],text=True),'board':shell('free -m; uptime; df -k /opt')}
  except Exception as e:r={'error':str(e)}
  with (D/'resources.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
  stop.wait(600)
def eligibility(local):
 raw=(local/'perf-stat.csv').read_text();events={}
 for line in raw.splitlines():
  if line.startswith('#'):continue
  cols=[x.strip() for x in line.split(';')]
  if len(cols)>=3 and cols[2] in ['cycles','instructions','task-clock']:events[cols[2]]=cols
 errors=[];freq=None
 try:
  c=Decimal(events['cycles'][0]);ms=Decimal(events['task-clock'][0]);assert c>0 and ms>0
  assert events['task-clock'][1]=='msec'
  assert all(len(events[e])>=5 and Decimal(events[e][4])==100 for e in ['cycles','task-clock'])
  freq=c*1000/ms
 except (KeyError,AssertionError,InvalidOperation):errors.append('invalid/missing/multiplexed cycles or task-clock')
 before=(local/'environment.before').read_text();after=(local/'environment.after').read_text()
 policy_regex=r'^(/sys/devices/system/cpu/cpufreq/policy\d+)/(scaling_\w+) (\S+)$'
 def policies(text):
  out={}
  for p,k,v in re.findall(policy_regex,text,re.M):out.setdefault(p,{})[k]=v
  return out
 first,last=policies(before),policies(after);fixed=None
 if not first or first!=last or any(set(v)!={'scaling_governor','scaling_min_freq','scaling_max_freq','scaling_cur_freq'} for v in first.values()):errors.append('missing/changing policy boundaries')
 else:
  maxima={int(v['scaling_max_freq']) for v in first.values()}
  if len(maxima)!=1:errors.append('heterogeneous policy frequencies')
  else:fixed=next(iter(maxima))*1000
 temps=[];freqs=[];unknown_sensor=False
 for p in sorted((local/'telemetry').glob('*.txt')):
  text=p.read_text();t=[int(x) for x in re.findall(r'/sys/class/thermal/thermal_zone\d+/temp (-?\d+)',text)];f=[int(x) for x in re.findall(r'/sys/devices/system/cpu/cpu\d+/cpufreq/scaling_cur_freq (\d+)',text)]
  temps+=t;freqs+=f
  if not t or not f:unknown_sensor=True
 if not temps or not freqs or unknown_sensor or any(x<0 or x>110000 for x in temps):errors.append('missing/invalid sensor observation')
 swaps=[]
 for s in [before,after]:
  m=re.search(r'^pswpout (\d+)$',s,re.M);swaps.append(int(m[1]) if m else None)
 delta=(swaps[1]-swaps[0])*int((local/'page-size').read_text()) if None not in swaps and swaps[1]>=swaps[0] else None
 if delta is None:errors.append('unknown swap delta')
 abnormal=[]
 if freq is not None and fixed is not None and freq<Decimal(fixed)*Decimal('.97'):abnormal.append('effective_frequency_below_97_percent')
 if fixed and any(f*1000!=fixed for f in freqs):abnormal.append('instant_frequency_not_fixed')
 if temps and max(temps)>=75000:abnormal.append('temperature_at_or_above_75C')
 if delta is not None and delta>=4*1024*1024:abnormal.append('swapout_at_or_above_4MiB')
 result={'events':events,'effective_frequency_Hz':str(freq) if freq is not None else 'unknown','fixed_frequency_Hz':fixed,'unknown_reasons':errors,'abnormal_reasons':abnormal,'observed_no_throttling':not errors and not abnormal,'max_temperature_mC':max(temps) if temps else None,'swapout_bytes':delta,'policy_before':first,'policy_after':last,'firmware_throttling_node':'unknown'}
 (local/'eligibility-amendment1.json').write_text(json.dumps(result,indent=2)+'\n');return result

def collect(tag,variant,mode,inp,repeats=1,estimate=1000000):
 if cancel or (D/'STOP_REQUESTED').exists():raise RuntimeError('Stop requested before new RUN')
 cmd=f'RUN_ESTIMATE_BYTES={estimate} COLLECT_REPEATS={repeats} nice -n 19 ionice -c3 /bin/bash /opt/afdo_agent/scripts/collect.sh rpi4 {mode} {variant} /opt/afdo_agent/eval-manifest.tsv {shlex.quote(str(inp))}'
 print('START',tag,cmd,flush=True);t=time.monotonic();p=call(['sdb','-s',device,'shell','( '+cmd+' ); rc=$?; printf "\\n__REMOTE_RC=%s\\n" "$rc"'],7200)
 (D/(tag+'-command.json')).write_text(json.dumps(dict(command=cmd,transport_rc=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2)+'\n')
 m=re.search(r'RUNPATH (\S+)',p.stdout);rc=re.search(r'__REMOTE_RC=(\d+)',p.stdout)
 if not m:raise RuntimeError('No RUN: '+p.stdout+p.stderr)
 remote=m[1];local=D/'runs'/tag
 (D/'pending-run.json').write_text(json.dumps(dict(tag=tag,remote=remote,transport_rc=p.returncode,remote_rc=int(rc[1]) if rc else None),indent=2)+'\n')
 if p.returncode or not rc:
  (D/'interrupted-run.json').write_text((D/'pending-run.json').read_text());raise RuntimeError('SDB interruption; RUN excluded, no pull/delete attempted')
 raw=S.manifest(remote);(D/'receipts'/(tag+'.manifest')).write_text(raw)
 receipt=pull_verify_delete(remote,local,raw,lambda r,l:S.call(['pull',r,str(l)+'/']),lambda:S.manifest(remote),lambda r:S.shell('rm -rf -- '+shlex.quote(r)+' && test ! -e '+shlex.quote(r)))
 (D/'receipts'/(tag+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
 row=dict(tag=tag,variant=variant,mode=mode,input=str(inp),repeats=repeats,remote=remote,local=str(local),seconds=time.monotonic()-t,rc=int(rc[1]) if rc else -1,bytes=sum(f.stat().st_size for f in local.rglob('*') if f.is_file()))
 if p.returncode or row['rc']:(D/'pending-run.json').unlink(missing_ok=True);records.append(row);(D/'runs.json').write_text(json.dumps(records,indent=2)+'\n');raise RuntimeError('Board RUN failed: '+str(row))
 assert (local/'uname').read_text().splitlines()[-1]==original['version'],'Kernel changed'
 row['eligibility']=eligibility(local)
 if mode.startswith('sample'):
  target=manifest[variant][6];n=total=0
  for line in (local/'perfscript.txt').open():
   if re.match(r'^\s*-?\d+/-?\d+\s+\d+\s+cycles:\s+[0-9a-f]+\s+\(',line):
    total+=1
    if '('+target+'+0x' in line:n+=1
  row.update(target_samples=n,sample_lines=total)
  ev=(local/'evlist.txt').read_text();assert 'type: 0 (PERF_TYPE_HARDWARE)' in ev and 'config: 0 (PERF_COUNT_HW_CPU_CYCLES)' in ev and n>0
 (D/'pending-run.json').unlink(missing_ok=True);records.append(row);(D/'runs.json').write_text(json.dumps(records,indent=2)+'\n');print('END',json.dumps(row),flush=True)
 if cancel or (D/'STOP_REQUESTED').exists():raise RuntimeError('Stop requested; completed RUN safely archived')
 return row

def main():
 root_open=False;policies=[];success=False;error=None;mon=None
 print('BEGIN',datetime.datetime.now().astimezone().isoformat(),flush=True)
 try:
  assert shell('uname -v')==original['version'];assert shell('id -u')==original['uid']
  common=(W/'tools/profgen/board/common.sh').read_text();deps=re.search(r'BOARD_REQUIRED_COMMANDS=\((.*?)\)',common,re.S)[1].split()
  shell('missing=0; for c in '+' '.join(shlex.quote(x) for x in deps)+'; do if command -v "$c"; then :; else printf "MISSING %s\\n" "$c"; missing=1; fi; done; test "$missing" -eq 0')
  root_open=True;p=call(['sdb','-s',device,'root','on']);assert p.returncode==0;assert shell('id -u')=='0'
  # Deployment verification precedes governor and any collection perf call.
  checks=json.loads((OLD/'deployment-check.json').read_text());checked=[]
  for item in checks:
   if '/scripts/' in item['path']:continue
   actual=shell('test -r '+shlex.quote(item['path'])+' && sha256sum '+shlex.quote(item['path'])).split()[0];assert actual==item['expected'];checked.append(item)
  for p in (W/'tools/profgen/board').glob('*.sh'):
   dest='/opt/afdo_agent/scripts/'+p.name;push=call(['sdb','-s',device,'push',str(p),dest]);assert push.returncode==0
   assert shell('sha256sum '+dest).split()[0]==hashlib.sha256(p.read_bytes()).hexdigest()
  for filename,expected in [('bbb_720p_h264_60s.mp4','b5e116b9d01cec8e7f697041c53575d36bd96a5928e40faa69e731f9ae2d00a4'),('bbb_1080p_h264_60s.mp4','31f72f11eb0566e0265358a14294e5dbddf13fce4ce1507d8872b04c2596a6da'),('tos_720p_h264_60s.mp4','280fbd41f8772491ebe784aa19a3caed3bb1e8b2e64daef1d2a5a284d1f38ad1')]:assert shell('sha256sum /opt/afdo_agent/media/'+filename).split()[0]==expected
  shell('test -x /opt/afdo_agent/tools/perf && LD_LIBRARY_PATH=/opt/afdo_agent/lib HOME=/opt/afdo_agent/work TMPDIR=/opt/afdo_agent/work PERF_CONFIG=/opt/afdo_agent/work/perf.conf /opt/afdo_agent/tools/perf --buildid-dir /opt/afdo_agent/work/buildid --version')
  (D/'before.txt').write_text(shell('id; df -k /opt; rpm -qa | wc -l; cat /proc/sys/kernel/perf_event_paranoid; cat /proc/sys/kernel/kptr_restrict; getconf PAGESIZE')+'\n')
  policies=shell('for p in /sys/devices/system/cpu/cpufreq/policy*/scaling_governor; do printf "%s %s\\n" "$p" "$(cat "$p")"; done').splitlines();assert policies
  (D/'governors.json').write_text(json.dumps(policies)+'\n')
  for line in policies:
   path,old=line.split();assert re.fullmatch(r'/sys/devices/system/cpu/cpufreq/policy\d+/scaling_governor',path);assert shell('printf "performance\\n" > '+path+' && cat '+path)=='performance'
  mon=threading.Thread(target=monitor,daemon=True);mon.start()
  # Prior excluded pilot validated counters. Do not add another formal or pilot RUN.
  oldrows=json.loads((W/'docs/profgen/impl/evidence/12/19_resume2_runs.json').read_text())
  done={Path(x['run']).name.removeprefix('formal2-').rsplit('-s',1)[0] for x in oldrows if x['formal']}
  done.update(x['group'] for x in json.loads((W/'temp/board-round1-amend1/formal-groups.json').read_text()))
  refs=json.loads((OLD/'calibration-runs.json').read_text());rates={(x['variant'],'sample-fixed','bbb'):x for x in refs}
  formalold=json.loads((OLD/'formal2-runs.json').read_text())
  for x in formalold:
   if '-cal-freq-' in x['tag']:rates[(x['variant'],'sample-freq','bbb')]=x
   if x['tag']=='formal2-cal-tos':rates[('ffmpeg-thumb-S','sample-fixed','tos')]=x
  groups=[]
  for rep in range(5):
   budgets=[20000,100000,400000];budgets=budgets[rep%3:]+budgets[:rep%3]
   for budget in budgets:
    for variant in ['spike-thumb-S','spike-a32-S','ffmpeg-thumb-S']:groups.append((variant,'sample-fixed','bbb',budget,rep))
   for variant in ['spike-thumb-S','spike-a32-S','ffmpeg-thumb-S']:groups.append((variant,'sample-freq','bbb',100000,rep))
   groups.extend([('ffmpeg-thumb-S','sample-fixed','tos',100000,rep),('ffmpeg-a32-S','sample-fixed','bbb',100000,rep)])
  logical=[];bbb='/opt/afdo_agent/media/bbb_720p_h264_60s.mp4';tos='/opt/afdo_agent/media/tos_720p_h264_60s.mp4'
  for variant,mode,video,budget,rep in groups:
   group=f'{variant}-{mode}-{video}-{budget}-r{rep+1}'
   if group in done:print('PRESERVE OLD',group,flush=True);continue
   reference=rates[(variant,mode,video)];segments=[];total=0
   while total<budget:
    ratio=min(budget-total,150000)/reference['target_samples']*1.08
    if variant.startswith('spike'):inp=max(10000,math.ceil(int(reference['input'])*ratio));reps=1;scale=inp/int(reference['input'])
    else:inp=bbb if video=='bbb' else tos;reps=min(3,max(1,math.ceil(reference['repeats']*ratio)));scale=reps/reference['repeats']
    row=collect(group+'-s'+str(len(segments)+1),variant,mode,inp,reps,math.ceil(reference['bytes']*scale*1.3+1000000));segments.append(row['tag']);total+=row['target_samples'];reference=row
   logical.append(dict(group=group,variant=variant,mode=mode,video=video,budget=budget,rep=rep+1,segments=segments,target_samples=total));(D/'formal-groups.json').write_text(json.dumps(logical,indent=2)+'\n')
  for isa in ['thumb','a32']:
   for stage in ['R','C','G5']:
    collect('train-spike-'+isa+'-'+stage,'spike-'+isa+'-'+stage,stage,1000000,estimate=16000000)
    collect('train-ffmpeg-'+isa+'-'+stage,'ffmpeg-'+isa+'-'+stage,stage,bbb,estimate=80000000)
  for stage in ['R','C']:collect('test-ffmpeg-thumb-'+stage,'ffmpeg-thumb-'+stage,stage,tos,estimate=80000000)
  success=True
 except BaseException as e:
  error=repr(e);print('FAILED',error,flush=True)
  if (D/'interrupted-run.json').exists():
   try:
    reconnect=call(['sdb','connect','192.168.108.26']);assert reconnect.returncode==0
    assert shell('uname -v')==original['version'] and shell('uname -m')=='armv7l'
    shell('cat /proc/device-tree/model; ps -eo pid,ppid,args')
   except Exception as recovery:print('ONE_RECONNECT_FAILED',repr(recovery),flush=True)
   # Stop this phase; never retry an interrupted workload in place.
 finally:
  stop.set()
  if mon:mon.join(10)
  restored=[]
  for line in policies:
   path,old=line.split()
   try:restored.append({'path':path,'expected':old,'actual':shell('printf "%s\\n" '+shlex.quote(old)+' > '+path+' && cat '+path)})
   except Exception as e:restored.append({'path':path,'error':str(e)});success=False
  (D/'restore.json').write_text(json.dumps(restored,indent=2)+'\n')
  if root_open:
   try:
    p=call(['sdb','-s',device,'root','off' if original['uid']!='0' else 'on']);assert p.returncode==0
    final=shell('id; df -k /opt; for p in /sys/devices/system/cpu/cpufreq/policy*/scaling_governor; do printf "%s " "$p"; cat "$p"; done; rpm -qa | wc -l');(D/'final.txt').write_text(final+'\n')
   except Exception as e:print('RESTORE ERROR',repr(e),flush=True);success=False
  status=f'ALL-END {datetime.datetime.now().astimezone().isoformat()} {"OK" if success else "FAILED"} elapsed={time.monotonic()-started:.3f} reason={error}\n';(D/'matrix.status').write_text(status);print(status,flush=True)
if __name__=='__main__':main()
