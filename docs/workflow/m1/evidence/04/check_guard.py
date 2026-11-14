from pathlib import Path
import subprocess,json,os,time,shutil,datetime
R=Path(__file__).resolve().parent;W=R.parents[2];out=R/"verification";out.mkdir()
G=1024**3;now=lambda:datetime.datetime.now().astimezone().isoformat()
cg=Path("/sys/fs/cgroup")/Path("/proc/self/cgroup").read_text().split("::",1)[1].strip().lstrip("/")
def sample(i):
 raw=Path("/proc/meminfo").read_text();(out/f"meminfo-{i:05d}.txt").write_text(raw)
 r=dict(time=now(),MemAvailable=int(next(x.split()[1] for x in raw.splitlines() if x.startswith("MemAvailable:")))*1024,loadavg=list(os.getloadavg()),nproc=int(subprocess.check_output(["nproc"],text=True).strip()),disk_free=shutil.disk_usage(W).free)
 for f in ["memory.current","memory.peak","memory.events"]:r[f]=(cg/f).read_text().strip()
 with (out/"resources.jsonl").open("a") as f:f.write(json.dumps(r)+"\n")
 return r
r=sample(0)
assert r["MemAvailable"]>=16*G and r["loadavg"][0]<r["nproc"]*.6 and r["disk_free"]>=50*G,"Light verification gate not met; no extraction started"
start=now();t=time.monotonic();last=0;i=1;low=0;results=[]
try:
 assert json.loads((R/"terminal.json").read_text())["status"]=="成功"
 for v in ["thumb","a32"]:
  with (out/(v+".log")).open("w") as log:
   p=subprocess.Popen(["python3",str(R/"verify_artifacts.py"),v],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,cwd=W)
   while True:
    if time.monotonic()-last>=60:
     last=time.monotonic();r=sample(i);i+=1;low=low+1 if r["MemAvailable"]<6*G else 0
     if low>=2 or r["disk_free"]<20*G:
      (out/"resource-stop.json").write_text(json.dumps(r,indent=2))
      subprocess.run(["systemctl","--user","stop","m1-weekend-j2-checks.scope"])
      raise RuntimeError("Resource stop")
    if p.poll() is not None:break
    time.sleep(0.5)
   rc=p.wait();results.append(dict(variant=v,exit=rc))
   if rc:raise RuntimeError(v+" artifact verification failed; do not publish")
finally:
 r=sample(i)
 (out/"terminal.json").write_text(json.dumps(dict(start=start,end=now(),seconds=time.monotonic()-t,results=results,resource=r),indent=2)+"\n")
 print("ALL-END",now(),results,flush=True)
