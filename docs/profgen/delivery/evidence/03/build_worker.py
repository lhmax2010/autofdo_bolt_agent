from pathlib import Path
import os,subprocess,time,json,datetime,signal,hashlib,shutil
W=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
now=lambda:datetime.datetime.now().astimezone().isoformat()
env=os.environ.copy();env.update(HOME=str(W/'temp/gbs-home'),GIT_CONFIG_NOSYSTEM='1',TMPDIR=str(W/'temp/gbs-tmp-llvm-x86'),GIT_CONFIG_COUNT='2',GIT_CONFIG_KEY_0='gc.auto',GIT_CONFIG_VALUE_0='0',GIT_CONFIG_KEY_1='maintenance.auto',GIT_CONFIG_VALUE_1='false',SUDO_ASKPASS='/bin/false')
cmd=['gbs','-c',str(W/'temp/gbs/gbs_llvm_x86_release.conf'),'build','-A','x86_64','--spec','llvm.spec','--buildroot',str(W/'temp/GBS-ROOT-LLVM-RELEASE-20261114c'),'--threads','1','--define','_smp_mflags -j4','--define','mlgo_build_jobs 4']
(D/'build-command.json').write_text(json.dumps(dict(command=cmd,cwd=str(W/'temp/llvm-profgen-release'),gbs_environment={k:env[k] for k in ['HOME','GIT_CONFIG_NOSYSTEM','TMPDIR','GIT_CONFIG_COUNT','SUDO_ASKPASS']},resource=dict(MemoryMax=10737418240,CPUQuota='400%',jobs=4)),indent=2))
assert hashlib.sha256((W/'temp/gbs/gbs_llvm_x86_release.conf').read_bytes()).hexdigest()=='cf82a48af046d5d5c7dbd6bb8df8dec6ff6254ea9ddda35bebe47d3844442c32'
assert hashlib.sha256((W/'temp/llvm-profgen-release/packaging/llvm.spec').read_bytes()).hexdigest()=='7962d176484920de6138d70c7e8a8e1764dfada6655abf0332e9748167e889fd'
mem=Path('/proc/meminfo').read_text();(D/'build-start-meminfo.txt').write_text(mem)
assert int(next(x.split()[1] for x in mem.splitlines() if x.startswith('MemAvailable:')))>=14*1024*1024, 'Heavy gate not met; not started'
assert not (W/'temp/GBS-ROOT-LLVM-RELEASE-20261114c').exists(),'Buildroot must be new'
cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().split('::',1)[1].strip().lstrip('/')
(D/'build-cgroup.txt').write_text(str(cg))
p=subprocess.Popen(cmd,cwd=W/'temp/llvm-profgen-release',env=env,stdin=subprocess.DEVNULL,start_new_session=True)
(D/'gbs-pid.txt').write_text(str(p.pid));print('GBS-START',now(),'PID',p.pid,'COMMAND',repr(cmd),flush=True)
low=0;minimum=None;peak=0;last=0;sample=0;reason=None
while True:
 try: peak=max(peak,int((cg/'memory.peak').read_text()))
 except FileNotFoundError: pass
 (D/'live-memory-peak.txt').write_text(str(peak))
 if time.monotonic()-last>=60:
  last=time.monotonic();raw=Path('/proc/meminfo').read_text();(D/f'meminfo-{sample:05d}.txt').write_text(raw)
  available=int(next(x.split()[1] for x in raw.splitlines() if x.startswith('MemAvailable:')))*1024;minimum=available if minimum is None else min(minimum,available);low=low+1 if available<3*1024**3 else 0
  free=shutil.disk_usage(W).free
  with (D/'resource.jsonl').open('a') as f:f.write(json.dumps(dict(time=now(),MemAvailable=available,cgroup_memory_peak=peak,disk_free=free,consecutive_low=low))+'\n')
  if sample%10==0:
   print('RESOURCE',now(),flush=True);subprocess.run(['free','-m']);subprocess.run(['uptime'])
  sample+=1
  if low>=2 or free<4*1024**3:
   reason='MemAvailable below 3GiB twice' if low>=2 else 'disk space below 4GiB';print('STOP',now(),reason,flush=True)
   os.killpg(p.pid,signal.SIGTERM)
   break
 rc=p.poll()
 if rc is not None:break
 time.sleep(1)
if reason:
 try:rc=p.wait(timeout=30)
 except subprocess.TimeoutExpired:
  try:os.killpg(p.pid,signal.SIGKILL)
  except PermissionError:pass
  rc=p.wait()
else:rc=p.wait()
events=(cg/'memory.events').read_text()
(D/'worker-result.json').write_text(json.dumps(dict(gbs_exit=rc,reason=reason,minimum_MemAvailable=minimum,cgroup_memory_peak=peak,memory_events=events,end=now()),indent=2));print('GBS-END',now(),'EXIT',rc,flush=True)
raise SystemExit(rc if rc>=0 else 128-rc)
