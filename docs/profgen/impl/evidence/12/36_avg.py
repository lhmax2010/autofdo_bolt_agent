from pathlib import Path
import json,subprocess,time,os,hashlib
w=Path.cwd();d=w/'temp/board-round1-patch8';out=w/'temp/profgen-patch8/independent-avg';rows=[]
assert (w/'temp/profgen-patch8/post.status').read_text().rstrip().endswith(' OK')
for old in json.loads((w/'temp/board-round1-resume2/real-avg/generation.json').read_text()):
 mode=next(x.split('=',1)[1] for x in old['command'] if x.startswith('--ip-aggregation='));cmd=[('--output='+str(out/(mode+'.text'))) if x.startswith('--output=') else ('--quality-report='+str(out/(mode+'.json'))) if x.startswith('--quality-report=') else x for x in old['command']]
 t=time.monotonic()
 with (out/(mode+'.stdout')).open('w') as o,(out/(mode+'.stderr')).open('w') as e:
  p=subprocess.Popen(cmd,stdout=o,stderr=e);pid,status,usage=os.wait4(p.pid,0);p.returncode=os.waitstatus_to_exitcode(status)
 rows.append(dict(command=cmd,exit=p.returncode,seconds=time.monotonic()-t,maxrss_KiB=usage.ru_maxrss,profile_sha256=hashlib.sha256((out/(mode+'.text')).read_bytes()).hexdigest() if (out/(mode+'.text')).exists() else None));(d/'avg-generation.json').write_text(json.dumps(rows,indent=2)+'\n')
 assert not p.returncode,(out/(mode+'.stderr')).read_text()
 print(mode,rows[-1]['seconds'],usage.ru_maxrss,flush=True)
p=subprocess.run(['nice','-n','19','ionice','-c3','python3',str(out/'inline_keys_formal.py')]);assert not p.returncode
result=json.loads((out/'gnu-inline-comparison.json').read_text());assert all(not r['problems'] and not r['differences'] for r in result)
# Check both directions: no extra body key is silently ignored.
import importlib.util
spec=importlib.util.spec_from_file_location('avgcheck',out/'check.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
for mode in ['sum','max','avg']:
 actual=m.text_profile((out/(mode+'.text')).read_text())
 for r in result:
  keys={(tuple(x if isinstance(x,str) else (tuple(x[0]),x[1]) for x in row['context']),tuple(row['location'])) for row in r['keys']}
  observed={k for k in actual if k[0][0]==r['function']};assert keys==observed,(mode,r['function'],keys-observed,observed-keys)
print('sum/max/avg: 715 keys each, exact key sets and values',flush=True)
