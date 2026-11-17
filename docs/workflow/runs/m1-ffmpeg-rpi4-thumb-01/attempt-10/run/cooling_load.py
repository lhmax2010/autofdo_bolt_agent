from pathlib import Path
import sys,json,time,threading
sys.path.insert(0,'workflow')
from afdo_wf.live import Experiment
from afdo_wf.common import save,require
b=Path(__file__).resolve().parent
idle=json.loads((b/'cooling-idle/result.json').read_text());require(idle['final_at_or_below_58000'],'idle cooling target unreachable; stop')
j=json.loads((b.parent/'attempt-09/job.json').read_text());j.update(experiment='m1-ffmpeg-rpi4-thumb-01-cooling-load-10',output=str(b/'cooling-load'))
jobfile=b/'cooling-load-job.json';save(jobfile,j);e=Experiment(j,jobfile);out=Path(j['output']);resources=[];stop=threading.Event()
def monitor():
 cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split(':')[-1].lstrip('/')
 while not stop.is_set():
  row=dict(time=time.time(),meminfo=Path('/proc/meminfo').read_text())
  for name in ['memory.current','memory.peak','memory.events']:
   if (cg/name).exists():row[name]=(cg/name).read_text()
  resources.append(row);save(out/'resources.json',resources);stop.wait(60)
thread=threading.Thread(target=monitor);thread.start()
try:
 with e.session():
  e.ensure_work();e.host_artifact(e.scripts,{},True);e.transport.shell('mkdir -p '+e.scripts)
  for f in (e.w/'workflow/board').glob('*.sh'):e.push_owned(f,e.scripts+'/'+f.name)
  e.push_owned(Path(j['package']).parent/'workloads/timed.sh',e.scripts+'/timed.sh')
  pre=json.loads((b.parent/'attempt-09/formal/stages/preflight/001/result.json').read_text())
  cap=out/'capabilities.tsv';cap.write_text(''.join(k+'\t'+p+'\n' for k,v in pre['capabilities'].items() for p in v));e.push_owned(cap,e.scripts+'/capabilities.tsv')
  base=json.loads((b.parent/'attempt-09/formal/stages/build/001/result.json').read_text());dep=e.deploy_variant(base,out);dep['variant']='BASE'
  script=out/'cooling_round.sh';script.write_text('#!/bin/bash\nset -eu\nmeasure=$1; shift\nrun=$1\nset +e\nbash "$measure" "$@"\nrc=$?\nset -e\ni=0\nwhile :; do\n stamp=$(cut -d" " -f1 /proc/uptime); ready=1\n for p in /sys/class/thermal/thermal_zone*/temp; do v=$(cat "$p"); printf "%s\\t%s\\t%s\\n" "$stamp" "$p" "$v"; test "$v" -le 56000 || ready=0; done >> "$run/cooldown.tsv"\n test "$ready" -eq 0 || break\n test "$i" -lt 60 || break\n sleep 10; i=$((i+1))\ndone\nexit "$rc"\n');e.push_owned(script,e.scripts+'/cooling_round.sh')
  x=next(x for x in e.inputs if x['role']=='test');remote=e.remote+'/base-cooling'
  e.launch('base-cooling',['bash',e.scripts+'/cooling_round.sh',e.scripts+'/measure.sh',remote,e.b+'/tools/perf',str(e.package['runtime']['cpu_affinity']),'0',e.scripts+'/capabilities.tsv','600','bash',e.scripts+'/timed.sh',x['role'],dep['remote'],x['path'],remote+'/result'],out,dict(LD_LIBRARY_PATH=dep['remote']+'/usr/lib:'+e.b+'/lib',DEPLOY_MANIFEST=e.scripts+'/BASE-manifest.json'),timeout=1400)
  local=e.pull_run(remote,out/'base-cooling');require(int((local/'measure.exit').read_text())==0,'cooling BASE load failed');maps=e.verify_maps(local,dep,x['path'])
  rows=[l.split('\t') for l in (local/'cooldown.tsv').read_text().splitlines()];times=sorted(set(float(r[0]) for r in rows));last=[int(r[2]) for r in rows if float(r[0])==times[-1]]
  save(out/'result.json',dict(formal=False,maps_verified=maps,samples=len(times),elapsed=times[-1]-times[0],last_mC=last,reached_56000=all(v<=56000 for v in last),input=x['id'],load_exit=0));print((out/'result.json').read_text(),flush=True)
finally:
 stop.set();thread.join();save(out/'ended.json',dict(time=time.time()))
