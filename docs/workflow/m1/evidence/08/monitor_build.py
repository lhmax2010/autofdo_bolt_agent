from pathlib import Path
import subprocess,json,time,datetime
D=Path('temp/m1-pilot-v02-20261116/build');data=[]
while True:
 row={'time':datetime.datetime.now().astimezone().isoformat(),'units':{}}
 for variant in ['base-r','afdo']:
  p=subprocess.run(['systemctl','--user','show','m1p-v02-build-'+variant+'.scope','-p','ActiveState','-p','ControlGroup','-p','MemoryMax','-p','MemoryHigh','-p','CPUQuotaPerSecUSec'],capture_output=True,text=True)
  x=dict(l.split('=',1) for l in p.stdout.splitlines() if '=' in l);cg=x.get('ControlGroup','')
  if cg:
   for f in ['memory.peak','memory.events','memory.current']:
    path=Path('/sys/fs/cgroup'+cg)/f
    try:x[f]=path.read_text()
    except FileNotFoundError:pass
  row['units'][variant]=x
 data.append(row);(D/'scope-monitor.json').write_text(json.dumps(data,indent=2)+'\n')
 if (D/'result.json').exists():break
 time.sleep(5)
