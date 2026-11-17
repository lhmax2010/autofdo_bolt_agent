from pathlib import Path
import json,time
b=Path(__file__).resolve().parent;f=b/'formal'
def read(p):return json.loads(p.read_text()) if p.exists() else None
p=read(f/'progress.json');print('stage',p['stage'],p['status'],'elapsed',round(time.time()-p['time']))
for stage in ['deploy','collect','measure']:
 d=f/'stages'/stage/'001'
 if d.exists():
  print(stage,'oracles',len(list(d.glob('*oracle.json'))),'maps',len(list(d.glob('*/maps/decoder-check.json'))))
  if stage=='measure':
   c=read(d/'telemetry-check-job/check-rows.json');print('checks',[(r['name'],r['telemetry']['classification']) for r in c] if c else None)
   print('plans/blocks',[str(p.relative_to(d)) for p in d.glob('**/*plan*.json')]+[str(p.relative_to(d)) for p in d.glob('**/*blocks*.json')])
for p in sorted((f/'stages').glob('**/execution/result.json')):
 d=read(p);print('build',p.parts[-4],d['exit_code'],round(d['build_seconds'],2),d['memory_peak'])
print('end',read(b/'driver-end.json'))
