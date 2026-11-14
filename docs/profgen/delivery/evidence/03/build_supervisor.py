from pathlib import Path
import subprocess,datetime,time,json,hashlib,traceback
D=Path(__file__).resolve().parent;W=D.parents[1];now=lambda:datetime.datetime.now().astimezone().isoformat()
start=now();t=time.monotonic();rc=None
cmd=['systemd-run','--user','--scope','--unit=profgen-release-build-20261114c','-p','MemoryMax=10G','-p','CPUQuota=400%','nice','-n','19','ionice','-c3','python3','-u',str(D/'build_worker.py')]
with (D/'build.log').open('w') as log:
 print('START',start,repr(cmd),file=log,flush=True)
 try:rc=subprocess.run(cmd,cwd=W,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT).returncode
 except BaseException:traceback.print_exc(file=log)
 finally:
  status='成功' if rc==0 else '失败';end=now();print('已结束',end,status,'SCOPE_EXIT',rc,file=log,flush=True);print('ALL-END',end,status,file=log,flush=True)
  result=dict(start=start,end=end,seconds=time.monotonic()-t,scope_exit=rc,status=status,scope_command=cmd)
  if (D/'worker-result.json').exists():result.update(json.loads((D/'worker-result.json').read_text()))
  if (D/'live-memory-peak.txt').exists():result['cgroup_memory_peak']=int((D/'live-memory-peak.txt').read_text())
  (D/'build-result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
(D/'build-log.sha256').write_text(hashlib.sha256((D/'build.log').read_bytes()).hexdigest()+'  '+str(D/'build.log')+'\n')
