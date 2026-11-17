from pathlib import Path
import os,json,hashlib,shutil
w=Path.cwd();src=Path(__file__).resolve().parent;dst=w/'docs/workflow/runs/m1-ffmpeg-rpi4-thumb-01/attempt-07/run';dst.mkdir(parents=True,exist_ok=True)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
raw=[];copied=[];bundles=[];batch=[];batch_size=0
skip={'roots','ffmpeg-source','extracted','home','cache','state','config','gbs-tmp','tmp','__pycache__'}
for directory,dirs,files in os.walk(src):
 dirs[:]=[d for d in dirs if d not in skip]
 for name in sorted(files):
  p=Path(directory)/name
  if not p.is_file() or p.is_symlink():continue
  rel=p.relative_to(src);digest=sha(p);record=dict(path=str(p.relative_to(w)),sha256=digest,bytes=p.stat().st_size);raw.append(record)
  if any(part.startswith('transport-') or part=='readonly-progress' for part in rel.parts):
   if p.suffix=='.json':
    item=dict(source=record,metadata=json.loads(p.read_text()))
    for suffix in ['stdout','stderr']:
     f=p.with_suffix('.'+suffix)
     if f.exists():item[suffix]=dict(sha256=sha(f),text=f.read_bytes().decode(errors='replace'))
    size=len(json.dumps(item,ensure_ascii=False).encode())
    if batch and batch_size+size>700000:
     f=dst/('transport-%03d.json'%len(bundles));f.write_text(json.dumps(batch,ensure_ascii=False,indent=2)+'\n');bundles.append(str(f));batch=[];batch_size=0
    if size<600000:batch.append(item);batch_size+=size
   continue
  if 'maps' in rel.parts and name not in ['decoder-check.json','cadence-check.json','samples.tsv','enumeration-errors.log','sha-cache.tsv','hash-attempts.tsv','hash-errors.log','hash-encounters.tsv']:continue
  allowed=p.suffix in ['.json','.csv','.tsv','.log','.txt','.stdout','.stderr','.sh','.py','.evlist','.exit','.monotonic'] or name in ['pid','exit','stdout','stderr','launch.sh','decoded.frames','decoded.bytes','decoded.sha256']
  if allowed and p.stat().st_size<700000:
   target=dst/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);copied.append(dict(path=str(target.relative_to(w)),source=record['path'],sha256=digest,bytes=record['bytes']))
if batch:
 f=dst/('transport-%03d.json'%len(bundles));f.write_text(json.dumps(batch,ensure_ascii=False,indent=2)+'\n');bundles.append(str(f))
# Shard both indices; binary/profile/perf originals stay only in temp.
for label,rows in [('raw-index',raw),('copied-index',copied)]:
 for i in range(0,len(rows),600):(dst/(label+'-%03d.json'%(i//600))).write_text(json.dumps(rows[i:i+600],ensure_ascii=False,indent=2)+'\n')
index=[]
for p in sorted(dst.rglob('*')):
 if p.is_file():
  assert p.stat().st_size<1000000,(p,p.stat().st_size)
  index.append(dict(path=str(p.relative_to(w)),sha256=sha(p),bytes=p.stat().st_size))
# Index of index files and bundles, not an unbounded recursive listing.
summary=dict(raw_files=len(raw),copied_files=len(copied),bundles=len(bundles),files=index)
f=dst.parent/'run-index.json';f.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');assert f.stat().st_size<1000000
print(len(raw),len(copied),len(bundles))
