from pathlib import Path
import subprocess,json,hashlib,os,time
W=Path.cwd();D=W/'temp/profgen-release-20261114c';s=json.loads((D/'release-tool.json').read_text());scratch=W/'temp/profgen-c1-baseline';backup=D/'preserved-c1-baseline';products=D/'release-c1-scratch';assert not backup.exists() and not products.exists();had=scratch.exists();events=[]
try:
 if had:scratch.rename(backup);events.append('Renamed original scratch to backup; no deletion')
 cmd=['python3',str(W/'tools/profgen/c1_baseline.py'),'--tool',s['tool'],'--library-dir',s['libdir'],'--library-dir',str(Path(s['root'])/'lib64'),'--library-dir',str(Path(s['root'])/'usr/lib64'),'--expected-tool-sha',s['sha256'],'--manifest',str(D/'release-c1.json'),'--compare',str(W/'tools/profgen/c1-baseline.json')]
 t=time.monotonic()
 with (D/'c1.log').open('w') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 result=dict(command=cmd,exit=p.returncode,seconds=time.monotonic()-t)
finally:
 if scratch.exists():scratch.rename(products);events.append('New scratch preserved under release-c1-scratch')
 if had:backup.rename(scratch);events.append('Original scratch restored')
 (D/'c1-preservation.json').write_text(json.dumps(events,indent=2))
(D/'c1-result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));raise SystemExit(p.returncode)
