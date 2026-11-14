from pathlib import Path
import subprocess,sys,time,json,datetime,os,signal
D=Path(__file__).resolve().parent
label=sys.argv[1];cmd=sys.argv[2:];out=D/(label+'-scope');out.mkdir()
now=lambda:datetime.datetime.now().astimezone().isoformat()
raw=Path('/proc/meminfo').read_text();(out/'meminfo-start.txt').write_text(raw)
av=lambda r:int(next(x.split()[1] for x in r.splitlines() if x.startswith('MemAvailable:')))*1024
assert av(raw)>=4*1024**3
cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().split('::',1)[1].strip().lstrip('/')
start=now();t=time.monotonic();minimum=av(raw);peak=0;last=0;low=0;reason=None
with (out/'output.log').open('w') as log:
 p=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 while True:
  peak=max(peak,int((cg/'memory.peak').read_text()))
  if time.monotonic()-last>=60:
   last=time.monotonic();raw=Path('/proc/meminfo').read_text();a=av(raw);minimum=min(minimum,a)
   (out/('meminfo-'+str(int(time.monotonic()-t))+'.txt')).write_text(raw)
   with (out/'resources.jsonl').open('a') as f:f.write(json.dumps(dict(time=now(),MemAvailable=a,memory_peak=peak))+'\n')
   low=low+1 if a<2.5*1024**3 else 0
   if a<1.5*1024**3 or low>=2:
    reason='resource gate';os.killpg(p.pid,signal.SIGTERM);break
  if p.poll() is not None:break
  time.sleep(1)
 try:rc=p.wait(timeout=30)
 except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);rc=p.wait()
 print('ALL-END',now(),'EXIT',rc,'REASON',reason,file=log)
r=dict(command=cmd,start=start,end=now(),seconds=time.monotonic()-t,exit=rc,reason=reason,minimum_MemAvailable=minimum,cgroup_memory_peak=max(peak,int((cg/'memory.peak').read_text())),memory_events=(cg/'memory.events').read_text())
(out/'result.json').write_text(json.dumps(r,indent=2));print(json.dumps(r),flush=True)
raise SystemExit(rc if rc>=0 else 128-rc)
