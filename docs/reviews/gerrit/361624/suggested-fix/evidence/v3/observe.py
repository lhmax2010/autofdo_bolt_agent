from pathlib import Path
import time,json,subprocess,shutil
d=Path(__file__).resolve().parent
m=Path('/proc/meminfo').read_text()
r=json.loads((d/'build/resources.json').read_text())
row=dict(time=time.time(),elapsed_seconds=time.time()-r[0]['time'],meminfo=m,
 mem_available=int(next(x.split()[1] for x in m.splitlines() if x.startswith('MemAvailable:')))*1024,
 loadavg=Path('/proc/loadavg').read_text(),disk_free=shutil.disk_usage(d).free,
 build_started=(d/'build/command.json').exists())
s=subprocess.run(['systemctl','--user','show','verify-361624-v3-20261116.service','-p','ActiveState','-p','SubState','-p','ControlGroup','-p','ExecMainStatus'],capture_output=True,text=True)
row['service']=s.stdout
cg=next((x.split('=',1)[1] for x in s.stdout.splitlines() if x.startswith('ControlGroup=')), '')
if cg:
 for field in ['memory.current','memory.peak','memory.events']:
  f=Path('/sys/fs/cgroup'+cg)/field
  if f.exists():row['supervisor_'+field]=f.read_text()
with (d/'wait-observations.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
print(json.dumps({k:v for k,v in row.items() if k!='meminfo'}))
for f in ['result.json','acceptance.json']:
 if (d/'build'/f).exists():print(f,(d/'build'/f).read_text())
