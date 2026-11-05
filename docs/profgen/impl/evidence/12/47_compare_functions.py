from pathlib import Path
import json,subprocess,difflib
W=Path.cwd();D=W/'temp/board-round1-patch8';R=W/'temp/GBS-ROOT-LLVM-X86/local/BUILD-ROOTS/scratch.x86_64.0';base=['nice','-n','19','ionice','-c3',str(R/'lib64/ld-linux-x86-64.so.2'),'--library-path',f'{R}/lib64:{R}/usr/lib64',str(R/'usr/bin/llvm-profdata')]
def functions(text):
 out={};current=None
 for line in text.splitlines():
  if line and not line.startswith((' ','#')):current=line.split(':')[0];out[current]=[]
  if current:out[current].append(line)
 return out
res=[]
for x in json.loads((D/'patch7-formal-comparison.json').read_text()):
 if x['patch7_profile_sha256']==x['patch8_profile_sha256']:continue
 out=D/'converted'/Path(x['run']).name;versions=[]
 for v,source in [('patch7','patch7-profile.extbinary'),('patch8','profile.extbinary')]:
  dest=out/(v+'-canonical.text');cmd=base+['merge','--sample','--text',str(out/source),'-o',str(dest)];p=subprocess.run(cmd,capture_output=True,text=True);assert not p.returncode,(cmd,p.stderr);versions.append(functions(dest.read_text()))
 a,b=versions;changes=[]
 for fn in sorted(a.keys()|b.keys()):
  if a.get(fn)!=b.get(fn):changes.append(dict(function=fn,patch7=a.get(fn),patch8=b.get(fn)))
 res.append(dict(run=x['run'],functions=changes));print(Path(x['run']).name,[c['function'] for c in changes],flush=True)
(D/'profile-function-changes.json').write_text(json.dumps(res,indent=2)+'\n')
