from pathlib import Path
import subprocess,json,os,time,datetime,shutil,signal,traceback
R=Path(__file__).resolve().parent;W=R.parents[2];G=1024**3
now=lambda:datetime.datetime.now().astimezone().isoformat()
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+"\n")
def append(p,x):
 with p.open("a") as f:f.write(json.dumps(x,ensure_ascii=False)+"\n");f.flush();os.fsync(f.fileno())
def sample(out,index,unit=None):
 raw=Path("/proc/meminfo").read_text();(out/f"meminfo-{index:05d}.txt").write_text(raw)
 r=dict(time=now(),MemAvailable=int(next(x.split()[1] for x in raw.splitlines() if x.startswith("MemAvailable:")))*1024,
 loadavg=list(os.getloadavg()),nproc=int(subprocess.check_output(["nproc"],text=True).strip()),disk_free=shutil.disk_usage(W).free)
 cp=out/"cgroup.txt"
 if cp.exists():
  cg=Path(cp.read_text())
  for f in ["memory.current","memory.peak","memory.events"]:
   if (cg/f).exists():r[f]=(cg/f).read_text().strip()
 return r
active=None;results=[];status="未开始";start=now();reason=None
def terminate(sig,frame):raise InterruptedError("Supervisor signal "+str(sig))
signal.signal(signal.SIGTERM,terminate);signal.signal(signal.SIGINT,terminate)
try:
 for v in ["thumb","a32"]:
  deadline=time.monotonic()+48*3600
  finished=False
  for attempt in range(3):
   out=R/(v+"-attempt-"+str(attempt));out.mkdir()
   waits=0
   while True:
    r=sample(out,waits);ok=r["MemAvailable"]>=16*G and r["loadavg"][0]<r["nproc"]*0.6 and r["disk_free"]>=50*G
    append(R/"gate.jsonl",dict(variant=v,attempt=attempt,passed=ok,**r))
    dump(R/"progress.json",dict(state="gate passed" if ok else "waiting",variant=v,attempt=attempt,time=now(),results=results))
    if ok:break
    if time.monotonic()>=deadline:raise RuntimeError("48-hour startup gate timeout for "+v)
    waits+=1;time.sleep(min(600,max(0,deadline-time.monotonic())))
   unit="m1-weekend-j2-"+v+"-a"+str(attempt);active=unit
   root=R/"roots"/(v+"-attempt-"+str(attempt))
   cmd=["systemd-run","--user","--scope","--unit",unit,"-p","MemoryMax=6G","-p","MemoryHigh=5G","-p","CPUQuota=200%",
     "nice","-n","19","ionice","-c3","python3","-u",str(R/"worker.py"),str(out),v,str(root)]
   dump(out/"scope-command.json",cmd)
   status="运行中";resource_stop=None;low=0;idx=waits+1;last=0;t=time.monotonic()
   with (out/"build.log").open("w") as log:
    print("START",now(),repr(cmd),file=log,flush=True)
    p=subprocess.Popen(cmd,cwd=W,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
    while True:
     if time.monotonic()-last>=60:
      last=time.monotonic();r=sample(out,idx);idx+=1;append(out/"resources.jsonl",r)
      low=low+1 if r["MemAvailable"]<6*G else 0
      dump(R/"progress.json",dict(state="running",variant=v,attempt=attempt,time=now(),elapsed=time.monotonic()-t,resource=r,results=results))
      if low>=2 or r["disk_free"]<20*G:
       resource_stop="MemAvailable below 6 GiB twice" if low>=2 else "disk below 20 GiB"
       q=subprocess.run(["systemctl","--user","stop",unit+".scope"],capture_output=True,text=True,timeout=60)
       dump(out/"resource-stop.json",dict(reason=resource_stop,command=["systemctl","--user","stop",unit+".scope"],exit=q.returncode,stdout=q.stdout,stderr=q.stderr,time=now()))
       if q.returncode:raise RuntimeError("Failed to stop own scope")
       break
     if p.poll() is not None:break
     time.sleep(1)
    rc=p.wait(timeout=60)
    print("已结束",now(),"成功" if rc==0 else "失败","SCOPE_EXIT",rc,"resource_stop",resource_stop,file=log,flush=True)
    print("ALL-END",now(),file=log,flush=True)
   active=None
   r=dict(variant=v,attempt=attempt,scope_exit=rc,resource_stop=resource_stop,seconds_scope=time.monotonic()-t)
   if (out/"result.json").exists():r.update(json.loads((out/"result.json").read_text()))
   else:r["gbs_exit"]=None
   append(R/"attempts.jsonl",r);results.append(r);dump(R/"results.json",results)
   if resource_stop:
    if attempt==2:raise RuntimeError(v+" resource retries exhausted (two retries)")
    continue
   # A pre-launch gate race did not start GBS; do not invent an exit code or silently retry.
   if r["gbs_exit"] is None:raise RuntimeError(v+" missing real GBS exit; requires decision")
   if r["gbs_exit"]!=0:
    text=(out/"build.log").read_text(errors="replace")
    if "DWARF version 5 unhandled" in text or "Unknown debugging section .debug_line_str" in text:
     raise RuntimeError(v+" failed with DWARF/debugedit diagnostics; stop for review")
   finished=True;break
  if not finished:raise RuntimeError(v+" did not finish")
 status="成功" if all(x.get("gbs_exit")==0 for x in results) else "失败"
except BaseException as e:
 status="失败";reason=repr(e);traceback.print_exc()
finally:
 if active:
  q=subprocess.run(["systemctl","--user","stop",active+".scope"],capture_output=True,text=True,timeout=60)
  dump(R/"exception-stop.json",dict(unit=active,exit=q.returncode,stdout=q.stdout,stderr=q.stderr))
 dump(R/"terminal.json",dict(start=start,end=now(),status=status,reason=reason,results=results))
 dump(R/"progress.json",dict(state="ended",time=now(),status=status,reason=reason,results=results))
 print("已结束",now(),status,reason,flush=True);print("ALL-END",now(),flush=True)
