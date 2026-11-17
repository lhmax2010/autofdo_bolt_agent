from pathlib import Path
import json
p=Path(__file__).resolve().parent
v=json.loads((p/'formal/progress.json').read_text());print(v['stage'],v['status'])
m=p/'formal/stages/measure/001'
for pattern in ['pilot-*-row.json','warm-*-row.json','formal-*-row.json']:
 fs=sorted(m.glob(pattern));print(pattern,len(fs))
for f in m.glob('*-plan.json'):
 v=json.loads(f.read_text());print('PLAN',f.name,v['N'])
for f in m.glob('*-blocks.json'):
 rows=json.loads(f.read_text());print(f.name,len(rows),rows[-1] if rows else None)
for n in ['driver-end.json','formal/stages/measure/001/failure.json']:
 f=p/n
 if f.exists():print(n,f.read_text())
print((p/'workflow-run-2.log').read_text()[-1000:])
