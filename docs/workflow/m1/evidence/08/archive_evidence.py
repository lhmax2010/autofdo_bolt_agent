from pathlib import Path
import json,hashlib,shutil,gzip
D=Path(__file__).parent;E=Path('docs/workflow/m1/evidence/08');E.mkdir(parents=True,exist_ok=True);index=[]
def copy(p,rel=None):
 rel=rel or p.relative_to(D);dest=E/rel
 if p.stat().st_size>60000 and p.suffix not in ['.extbinary','.gz']:
  dest=dest.with_name(dest.name+'.gz');dest.parent.mkdir(parents=True,exist_ok=True)
  with p.open('rb') as f,dest.open('wb') as out:
   with gzip.GzipFile(fileobj=out,mode='wb',mtime=0) as z:shutil.copyfileobj(f,z)
 else:dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 index.append(dict(source=str(p),evidence=str(dest.relative_to(E)),source_bytes=p.stat().st_size,source_sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),evidence_sha256=hashlib.file_digest(dest.open('rb'),'sha256').hexdigest()))
for p in D.iterdir():
 if p.is_file() and p.suffix in ['.json','.py','.sh','.txt','.stderr']:copy(p)
for name in ['stage2','stage3','conversion','code-shares','measurement','measurement-preflight-timeout-missing','measurement-preflight-bash3-failed','stats-fixtures','cleanup']:
 folder=D/name
 if not folder.exists():continue
 for p in folder.rglob('*'):
  if not p.is_file() or p.is_symlink():continue
  rel=p.relative_to(folder)
  if any(x in ['home','tmp','cache','buildid','__pycache__','m1p-afdo'] for x in rel.parts):continue
  if p.name in ['registry.bin','perf.data','remaining-board-work.tar','afdo.tar']:continue
  if p.suffix in ['.pyc','.cpio']:continue
  copy(p)
B=D/'build'
for p in B.iterdir():
 if p.is_file() and p.suffix in ['.json','.txt','.conf']:copy(p)
copy(B/'repo/tizen_unified_standard.conf')
for parent in [B,B/'forensic']:
 if not parent.exists():continue
 for p in parent.iterdir():
  if p.is_file() and parent!=B and p.suffix in ['.json','.txt']:copy(p)
 for variant in ['base-r','afdo','base-r-repo-resolution-failed','base-r-file-url-failed']:
  v=parent/variant
  if not v.exists():continue
  for p in v.iterdir():
   if p.is_file() and p.suffix in ['.json','.log','.txt']:copy(p)
(E/'index.json').write_text(json.dumps(index,indent=2,ensure_ascii=False)+'\n')
# Large raw artifacts retained on host, not copied into Git.
raw=[]
for p in [*D.glob('stage3/train-*/perf.data'),D/'cleanup/remaining-board-work.tar']:
 if p.exists():raw.append(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()))
(E/'retained-raw-artifacts.json').write_text(json.dumps(raw,indent=2)+'\n')
manifest={str(p.relative_to(E)):hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for p in sorted(E.rglob('*')) if p.is_file() and p.name!='sha256.json'}
(E/'sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Evidence files:',len(manifest),'bytes:',sum(p.stat().st_size for p in E.rglob('*') if p.is_file()))
