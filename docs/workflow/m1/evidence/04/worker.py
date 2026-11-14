from pathlib import Path
import sys,os,json,subprocess,time,datetime,signal,hashlib
R=Path(__file__).resolve().parent;W=R.parents[2]
out=Path(sys.argv[1]);v=sys.argv[2];root=Path(sys.argv[3])
now=lambda:datetime.datetime.now().astimezone().isoformat()
def measure():
 raw=Path("/proc/meminfo").read_text()
 return int(next(x.split()[1] for x in raw.splitlines() if x.startswith("MemAvailable:")))*1024
n=int(subprocess.check_output(["nproc"],text=True).strip())
import shutil
assert measure()>=16*1024**3 and os.getloadavg()[0]<n*0.6 and shutil.disk_usage(W).free>=50*1024**3,"Worker pre-launch gate changed"
assert not root.exists()
assert hashlib.sha256((R/"ffmpeg/packaging/ffmpeg.spec").read_bytes()).hexdigest()=="0e611e7eb95ada2c024dbea379821c5b109383f1545bcb0c86ef85f238740c27"
cg=Path("/sys/fs/cgroup")/Path("/proc/self/cgroup").read_text().split("::",1)[1].strip().lstrip("/")
(out/"cgroup.txt").write_text(str(cg))
env=os.environ.copy()
env.update(HOME=str(R/"home"),TMPDIR=str(R/"tmp"),TMP=str(R/"tmp"),TEMP=str(R/"tmp"),
 XDG_CACHE_HOME=str(R/"cache"),XDG_CONFIG_HOME=str(R/"config"),XDG_STATE_HOME=str(R/"state"),
 CCACHE_DIR=str(R/"cache/ccache"),GIT_CONFIG_NOSYSTEM="1",GIT_CONFIG_COUNT="2",
 GIT_CONFIG_KEY_0="gc.auto",GIT_CONFIG_VALUE_0="0",GIT_CONFIG_KEY_1="maintenance.auto",GIT_CONFIG_VALUE_1="false",SUDO_ASKPASS="/bin/false")
for k in ["V","MAKEFLAGS","MFLAGS"]:env.pop(k,None)
cmd=["gbs","-c",str(R/"ffmpeg-armv7l.conf"),"build","-A","armv7l","--spec","ffmpeg.spec","--include-all","--buildroot",str(root),"--threads","1","--define","_smp_mflags -j2","--define","profile_isa "+v]
(out/"command.json").write_text(json.dumps(dict(command=cmd,cwd=str(R/"ffmpeg"),environment={k:env[k] for k in ["HOME","TMPDIR","XDG_CACHE_HOME","XDG_CONFIG_HOME","CCACHE_DIR"]}),indent=2)+"\n")
start=now();tick=time.monotonic();p=None;rc=None;interrupted=None
def stop(sig,frame):
 global interrupted
 interrupted=sig
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
try:
 print("GBS-START",start,repr(cmd),flush=True)
 p=subprocess.Popen(cmd,cwd=R/"ffmpeg",env=env,stdin=subprocess.DEVNULL)
 (out/"gbs-pid.txt").write_text(str(p.pid))
 while p.poll() is None:time.sleep(0.5)
 rc=p.wait()
finally:
 result=dict(variant=v,start=start,end=now(),seconds=time.monotonic()-tick,gbs_exit=rc,interrupted_signal=interrupted,buildroot=str(root),command=cmd)
 for f in ["memory.current","memory.peak","memory.events"]:
  if (cg/f).exists():result[f]=(cg/f).read_text().strip()
 (out/"result.json").write_text(json.dumps(result,indent=2)+"\n")
 print("已结束",now(),"成功" if rc==0 else "失败","GBS_EXIT",rc,flush=True)
 print("ALL-END",now(),flush=True)
raise SystemExit(0 if rc==0 else 1)
