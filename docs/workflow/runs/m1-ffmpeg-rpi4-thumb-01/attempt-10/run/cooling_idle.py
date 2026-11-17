from pathlib import Path
import sys,json,time,threading,os
sys.path.insert(0,'workflow')
from afdo_wf.transport import SDB,q
from afdo_wf.receipts import Cleanup
from afdo_wf.common import save,require,sha256
b=Path(__file__).resolve().parent;out=b/'cooling-idle';out.mkdir(exist_ok=False)
j=json.loads((b.parent/'attempt-09/job.json').read_text());t=SDB(j['serial'],out/'transport');c=Cleanup(out/'cleanup.json',j['identity']);t.journal=c
stop=threading.Event();resources=[]
def monitor():
 cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split(':')[-1].lstrip('/')
 while not stop.is_set():
  row=dict(time=time.time(),meminfo=Path('/proc/meminfo').read_text(),load=Path('/proc/loadavg').read_text())
  for name in ['memory.current','memory.peak','memory.events']:
   if (cg/name).exists():row[name]=(cg/name).read_text()
  resources.append(row);save(out/'resources.json',resources);stop.wait(60)
thread=threading.Thread(target=monitor);thread.start()
remote='/opt/afdo_agent/work/m1-ffmpeg-rpi4-thumb-01-cooling-idle-10'
initial={};errors=[]
try:
 require(t.identity()==j['identity'],'identity mismatch')
 initial=dict(root=t.root_state(),governors=t.governors(),rpm=t.shell('rpm -qa | wc -l',True).strip())
 save(out/'initial.json',initial)
 if not initial['root']:c.register(dict(kind='root',previous=False));t.root(True)
 for policy,value in initial['governors'].items():c.register(dict(kind='governor',policy=policy,previous=value));t.governor(policy,'performance')
 fan="for p in /sys/class/hwmon/hwmon*/name /sys/class/hwmon/hwmon*/fan*_input /sys/class/hwmon/hwmon*/pwm* /sys/class/thermal/cooling_device*/type /sys/class/thermal/cooling_device*/cur_state; do test -f \"$p\" || continue; printf '%s ' \"$p\"; cat \"$p\"; done"
 save(out/'fan-before.json',dict(raw=t.shell(fan,True),note='Read only; no fan state written. Physical fan state unknown if not exposed.'))
 c.register(dict(kind='run',remote=remote,local=str(out/'raw'),receipt=str(out/'idle.pull.json')))
 t.shell('test ! -e '+q(remote)+' && mkdir -p '+q(remote))
 script=out/'idle.sh';script.write_text('#!/bin/bash\nset -eu\nout=$1\ni=0\nwhile :; do\n stamp=$(cut -d" " -f1 /proc/uptime)\n for p in /sys/class/thermal/thermal_zone*/temp; do printf "%s\\t%s\\t%s\\n" "$stamp" "$p" "$(cat "$p")"; done >> "$out/temperature.tsv"\n test "$i" -lt 60 || break\n sleep 10; i=$((i+1))\ndone\n')
 t.push(script,remote+'/idle.sh');save(out/'started.json',dict(time=time.time(),duration=600,interval=10))
 t.shell('bash '+q(remote+'/idle.sh')+' '+q(remote),timeout=720)
 t.pull(remote,out/'raw',out/'idle.pull.json')
 rows=[line.split('\t') for line in (out/'raw/temperature.tsv').read_text().splitlines()]
 times=sorted(set(float(x[0]) for x in rows));last=[int(x[2]) for x in rows if float(x[0])==times[-1]]
 result=dict(samples=len(times),elapsed=times[-1]-times[0],minimum_mC=min(int(x[2]) for x in rows),last_mC=last,ever_at_or_below_58000=any(all(int(x[2])<=58000 for x in rows if float(x[0])==tm) for tm in times),final_at_or_below_58000=all(x<=58000 for x in last))
 save(out/'result.json',result);print(json.dumps(result),flush=True)
 save(out/'fan-after.json',dict(raw=t.shell(fan,True)))
finally:
 try:
  errors=c.restore(t.identity(),t.undo)
  save(out/'final.json',dict(errors=errors,pending=c.data['cleanup_pending'],root=t.root_state(),governors=t.governors(),rpm=t.shell('rpm -qa | wc -l',True).strip()))
 finally:stop.set();thread.join();save(out/'ended.json',dict(time=time.time(),errors=errors))
