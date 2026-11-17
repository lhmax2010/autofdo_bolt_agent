import sys,time,os,traceback
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/"workflow"))
from afdo_wf.transport import SDB,q
from afdo_wf.receipts import Cleanup
from afdo_wf.common import save,require
p=Path(__file__).resolve().parent
t=SDB("192.168.108.26:26101",p/"transport")
identity=t.identity()
require(identity==dict(model="Raspberry Pi 4 Model B Rev 1.5",arch="armv7l",kernel="6.12.80-arm-rpi4-v7l",build_id="tizen-unified-toolchain_20261104.160709"),"identity mismatch")
c=Cleanup(p/"cleanup.json",identity)
remote="/opt/afdo_agent/work/m1-ffmpeg-rpi4-thumb-01/launch-probe"
initial=dict(root=t.root_state(),governors=t.governors(),rpm=t.shell("rpm -qa | wc -l",True))
save(p/"initial.json",initial)
results=[];error=None
try:
 if not initial['root']:
  c.register(dict(kind="root",previous=False));t.root(True)
 c.register(dict(kind="run",remote=remote,local=str(p/"pulled"),receipt=str(p/"pull-receipt.json")))
 t.shell("test ! -e "+q(remote)+" && mkdir -p "+q(remote))
 script=p/"probe.sh"
 script.write_text('#!/bin/bash\nset -u\nout=$1\nprintf "%s\\n" "$$" > "$out/pid"\ndate +%s > "$out/start"\nsleep 20\ndate +%s > "$out/end"\nprintf "0\\n" > "$out/exit"\n')
 t.push(script,remote+"/probe.sh")
 for method in ['setsid','nohup','foreground']:
  for rep in range(1,4):
   d=remote+'/'+method+'-'+str(rep);t.shell('mkdir '+q(d))
   cmd='bash '+q(remote+'/probe.sh')+' '+q(d)
   if method!='foreground':
    cmd=('nohup ' if method=='nohup' else '')+'setsid '+cmd+' > '+q(d+'/out')+' 2> '+q(d+'/err')+' < /dev/null & p=$!; printf "%s\\n" "$p" > '+q(d+'/launched-pid')+'; cat /proc/$p/cgroup > '+q(d+'/cgroup')+'; ps -o pid,pgid,sid -p "$p" > '+q(d+'/ps')
   else:cmd+=' > '+q(d+'/out')+' 2> '+q(d+'/err')
   start=time.time();body=t.shell(cmd,timeout=140);returned=time.time()
   row=dict(method=method,rep=rep,start=start,returned=returned,elapsed=returned-start,output=body,checks=[])
   for delay in ([2,25] if method!='foreground' else [0]):
    time.sleep(max(0,returned+delay-time.time()))
    check=t.shell('for f in start end exit pid launched-pid; do if test -f '+q(d)+'/$f; then printf "%s=" "$f"; cat '+q(d)+'/$f; fi; done; if test -f '+q(d+'/launched-pid')+'; then p=$(cat '+q(d+'/launched-pid')+'); if kill -0 "$p" 2>/dev/null; then printf "alive=yes\\n"; else printf "alive=no\\n"; fi; fi',True)
    row['checks'].append(dict(delay=delay,time=time.time(),raw=check))
   results.append(row);save(p/"results.json",results);print(method,rep,row['elapsed'],row['checks'],flush=True)
except BaseException as e:
 error=repr(e);save(p/"failure.json",dict(error=error,traceback=traceback.format_exc()))
finally:
 errors=c.restore(t.identity(),t.undo)
 final=dict(root=t.root_state(),governors=t.governors(),rpm=t.shell("rpm -qa | wc -l",True),errors=errors,pending=c.data['cleanup_pending'])
 save(p/"final.json",final);save(p/"end.json",dict(time=time.time(),error=error,completed=len(results)))
 print('END',error,final,flush=True)
 if error or errors:sys.exit(1)
