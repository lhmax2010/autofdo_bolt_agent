from pathlib import Path
import os,sys,subprocess,time,datetime,json,hashlib,signal,shutil,traceback
W=Path('/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent');D=Path(__file__).resolve().parent
variant=sys.argv[1];arch="armv7l";out=D/("build-"+variant);out.mkdir(exist_ok=True)
now=lambda:datetime.datetime.now().astimezone().isoformat()
root=W/("temp/GBS-ROOT-FFMPEG-M1-"+variant.upper()+"-20261114-FIX1")
conf=D.parent/"ffmpeg-armv7l.conf";source=D.parent/"ffmpeg-fix1"
start=now();tick=time.monotonic();rc=None;p=None;error=None;peak=0;minimum=None;status="未开始";cg=None
env=os.environ.copy();env.update(HOME=str(W/"temp/gbs-home"),GIT_CONFIG_NOSYSTEM="1",TMPDIR=str(D/"gbs-tmp"),GIT_CONFIG_COUNT="2",GIT_CONFIG_KEY_0="gc.auto",GIT_CONFIG_VALUE_0="0",GIT_CONFIG_KEY_1="maintenance.auto",GIT_CONFIG_VALUE_1="false",SUDO_ASKPASS="/bin/false")
cmd=["gbs","-c",str(conf),"build","-A",arch,"--spec","ffmpeg.spec","--include-all","--buildroot",str(root),"--threads","1","--define","_smp_mflags -j4 V=1","--define","profile_isa "+variant]
(out/"command.json").write_text(json.dumps({"command":cmd,"cwd":str(source),"environment":{k:env[k] for k in ["HOME","GIT_CONFIG_NOSYSTEM","TMPDIR","GIT_CONFIG_COUNT","SUDO_ASKPASS"]}},indent=2))
def interrupt(sig,frame):raise InterruptedError("signal "+str(sig))
signal.signal(signal.SIGTERM,interrupt);signal.signal(signal.SIGINT,interrupt)
try:
 raw=Path("/proc/meminfo").read_text();(out/"meminfo-start.txt").write_text(raw)
 available=lambda r:int(next(x.split()[1] for x in r.splitlines() if x.startswith("MemAvailable:")))*1024
 assert available(raw)>=14*1024**3,"Heavy memory gate not met"
 assert shutil.disk_usage(W).free>=8*1024**3,"Insufficient free disk to start"
 assert not root.exists(),"Buildroot already exists"
 expected=json.loads((D/"source-prepare.json").read_text())["patched_spec_sha256"]
 assert hashlib.sha256((source/"packaging/ffmpeg.spec").read_bytes()).hexdigest()==expected
 cg=Path("/sys/fs/cgroup")/Path("/proc/self/cgroup").read_text().split("::",1)[1].strip().lstrip("/")
 (out/"cgroup.txt").write_text(str(cg))
 print("GBS-START",start,repr(cmd),flush=True)
 p=subprocess.Popen(cmd,cwd=source,env=env,stdin=subprocess.DEVNULL,start_new_session=True)
 (out/"gbs-pid.txt").write_text(str(p.pid));status="运行中";last=0;sample=0;low=0
 while True:
  peak=max(peak,int((cg/"memory.peak").read_text()))
  (out/"memory-peak.txt").write_text(str(peak))
  if time.monotonic()-last>=60:
   last=time.monotonic();raw=Path("/proc/meminfo").read_text();(out/f"meminfo-{sample:05d}.txt").write_text(raw)
   a=available(raw);minimum=a if minimum is None else min(minimum,a);low=low+1 if a<3*1024**3 else 0
   free=shutil.disk_usage(W).free
   with (out/"resources.jsonl").open("a") as f:f.write(json.dumps({"time":now(),"MemAvailable":a,"memory_peak":peak,"disk_free":free,"consecutive_low":low})+"\n")
   if sample%10==0:
    print("RESOURCE",now(),flush=True);subprocess.run(["free","-m"]);subprocess.run(["uptime"])
   sample+=1
   if low>=2 or free<4*1024**3:raise RuntimeError("resource stop: memory low twice or disk below 4GiB")
  if p.poll() is not None:break
  time.sleep(1)
 rc=p.wait();status="成功" if rc==0 else "失败"
except BaseException as e:
 error=repr(e);status="失败" if p else "未开始";traceback.print_exc()
 if p and p.poll() is None:
  try:os.killpg(p.pid,signal.SIGTERM);rc=p.wait(timeout=30)
  except BaseException as stop_error:print("STOP-ERROR",repr(stop_error),flush=True)
 if p and rc is None:rc=p.poll()
finally:
 result={"variant":variant,"start":start,"end":now(),"seconds":time.monotonic()-tick,"gbs_exit":rc,"status":status,"error":error,"minimum_MemAvailable":minimum,"cgroup_memory_peak":peak,"buildroot":str(root),"command":cmd}
 if cg and cg.exists():result["memory_events"]=(cg/"memory.events").read_text()
 (out/"result.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
 print("已结束",result["end"],status,"GBS_EXIT",rc,flush=True);print("ALL-END",result["end"],status,flush=True)
raise SystemExit(0 if rc==0 and error is None else 1)
