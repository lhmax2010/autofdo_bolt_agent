from pathlib import Path
import subprocess,datetime,time,json,hashlib,traceback
D=Path(__file__).resolve().parent;W=D.parents[1]
now=lambda:datetime.datetime.now().astimezone().isoformat()
results=[];start=now()
for variant in ["thumb","a32"]:
 out=D/("build-"+variant);out.mkdir()
 cmd=["systemd-run","--user","--scope","--unit=m1-ffmpeg-"+variant+"-20261114","-p","MemoryMax=10G","-p","CPUQuota=400%","nice","-n","19","ionice","-c3","python3","-u",str(D/"build_worker.py"),variant]
 begin=now();t=time.monotonic();rc=None
 with (out/"build.log").open("w") as log:
  print("START",begin,repr(cmd),file=log,flush=True)
  try:rc=subprocess.run(cmd,cwd=W,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT).returncode
  except BaseException:traceback.print_exc(file=log)
  finally:
   print("已结束",now(),"成功" if rc==0 else "失败","SCOPE_EXIT",rc,file=log,flush=True)
   print("ALL-END",now(),"SCOPE_EXIT",rc,file=log,flush=True)
 row={"variant":variant,"scope_exit":rc,"start":begin,"end":now(),"seconds":time.monotonic()-t}
 if (out/"result.json").exists():row.update(json.loads((out/"result.json").read_text()))
 row["log_sha256"]=hashlib.sha256((out/"build.log").read_bytes()).hexdigest()
 results.append(row);(D/"build-results.json").write_text(json.dumps(results,indent=2,ensure_ascii=False)+"\n")
 print("VARIANT-END",json.dumps(row,ensure_ascii=False),flush=True)
 if row.get("error") and "resource" in row["error"].lower():break
print("ALL-END",now(),"已结束",len(results),"variants",flush=True)
(D/"build-terminal.json").write_text(json.dumps({"start":start,"end":now(),"results":results},indent=2,ensure_ascii=False)+"\n")
