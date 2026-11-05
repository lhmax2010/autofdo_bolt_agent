from pathlib import Path
import json,subprocess,hashlib
W=Path.cwd();D=W/'temp/board-round1-patch8';P7=W/'temp/profgen-patch8/baseline-llvm-profgen';P8=W/'temp/llvm-profgen-enh/build/bin/llvm-profgen'
assert hashlib.sha256(P7.read_bytes()).hexdigest()=='334a09290f53eb4c793ae91759f2b6344a36e63317820eb9151771b262dc3f30'
results=[]
def diff(a,b,path=''):
 if isinstance(a,dict) and isinstance(b,dict):
  return sum([diff(a.get(k),b.get(k),path+'.'+k if path else k) for k in sorted(a.keys()|b.keys())],[])
 return [] if a==b else [dict(path=path,patch7=a,patch8=b)]
for x in json.loads((D/'reconverted.json').read_text())['runs']:
 name=Path(x['source']).name;out=D/'converted'/name;old=out/'patch7-profile.extbinary';report=out/'patch7-quality.json'
 cmd=[arg.replace(str(P8),str(P7)).replace(str(out/'profile.extbinary'),str(old)).replace(str(out/'quality.json'),str(report)) for arg in x['command']]
 with (out/'patch7.stdout').open('w') as o,(out/'patch7.stderr').open('w') as e:p=subprocess.run(cmd,stdout=o,stderr=e)
 q=json.loads(report.read_text());assert p.returncode==0
 row=dict(run=x['source'],command=cmd,exit=p.returncode,patch7_profile_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),patch8_profile_sha256=x['profile_sha256'],target_classification_changes=diff(q['samples']['target'],x['quality']['samples']['target']),alias_addresses=x['quality']['thumb_dwarf_normalization']['alias_addresses_top50'])
 results.append(row);print(name,'classification differences',len(row['target_classification_changes']),'profile_equal',row['patch7_profile_sha256']==row['patch8_profile_sha256'],flush=True)
(D/'patch7-formal-comparison.json').write_text(json.dumps(results,indent=2)+'\n')
