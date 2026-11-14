from pathlib import Path
import json,hashlib,shutil
W=Path.cwd();D=W/'temp/profgen-release-20261114c'
assert json.loads((D/'build-result.json').read_text())['gbs_exit']==0
A=W/'temp/gbs-deps-archive/llvm-release-20261114';assert not A.exists();A.mkdir(parents=True)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
rows=json.loads((D/'downloaded-dependencies.json').read_text());out=[]
for r in rows:
 src=W/r['path'];dest=A/src.name
 assert sha(src)==r['sha256'];shutil.copy2(src,dest);assert sha(dest)==r['sha256']
 out.append(dict(path=str(dest.relative_to(W)),size=dest.stat().st_size,sha256=r['sha256'],source=r['url']))
(A/'manifest.json').write_text(json.dumps(out,indent=2))
conf=W/'temp/gbs-tmp-llvm-x86/linhao-gbs/tizen_unified_standard.conf'
if conf.exists():shutil.copy2(conf,A/'tizen_unified_standard.conf')
result=dict(directory=str(A),count=len(out),bytes=sum(r['size'] for r in out),manifest_sha256=sha(A/'manifest.json'),buildconf_sha256=sha(A/'tizen_unified_standard.conf') if (A/'tizen_unified_standard.conf').exists() else None,files=out)
(D/'archive-result.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='files'}))
