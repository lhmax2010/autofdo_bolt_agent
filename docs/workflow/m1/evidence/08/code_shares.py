exec((__import__('pathlib').Path(__file__).parent/'common.py').read_text())
from collections import Counter
D=D/'code-shares';D.mkdir(exist_ok=True);ops=[]
root=W/'temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0';rpm=W/'temp/profgen-release-20261114c/extracted';loader=root/'lib64/ld-linux-x86-64.so.2';tool=root/'usr/bin/llvm-symbolizer';libs=str(rpm/'usr/lib64')+':'+str(root/'lib64')+':'+str(root/'usr/lib64')
save('tool.json',dict(path=str(tool),sha256=sha(tool)))
summary=[]
for dso in ['libavcodec','libavutil']:
 f=next(x for x in json.loads((D.parent/'base-manifest.json').read_text()) if x['path'].startswith('lib/'+dso+'.so.') and x['symlink'] is None);name=P.Path(f['path']).name
 binary=D.parent/'base-extracted/usr/lib'/name;debug=W/'temp/m1-target-20261114/weekend-j2/thumb-attempt-0/extracted/usr/lib/debug/usr/lib'/(name+'.debug')
 ph=run('program-headers',['readelf','-lW',str(binary)]);loads=[]
 for l in ph.splitlines():
  t=l.split()
  if t and t[0]=='LOAD':loads.append(tuple(int(t[j],16) for j in [1,2,4]))
 runs=[];addresses=set()
 for i in range(1,4):
  c=Counter();p=D.parent/'stage3'/('train-'+str(i))/'perfscript.txt'
  pat=re.compile(r'^\s*\d+/\d+\s+(\d+) cycles:\s+[0-9a-f]+ \('+re.escape(B+'/variants/m1p-base/lib/'+name)+r'\+0x([0-9a-f]+)\)$')
  for l in p.read_text().splitlines():
   m=pat.match(l)
   if not m:continue
   assert int(m[1])==1000003
   off=int(m[2],16);seg=[x for x in loads if x[0]<=off<x[0]+x[2]];assert len(seg)==1
   va=(seg[0][1]+off-seg[0][0])&~1;c[va]+=1;addresses.add(va)
  report=json.loads((D.parent/'conversion'/(dso+'-run'+str(i)+'.quality.json')).read_text());assert sum(c.values())==report['samples']['target']['counts']['sample_count'];runs.append(c)
 addresses=sorted(addresses);q=D/(dso+'-addresses.txt');q.write_text(''.join(hex(a)+'\n' for a in addresses));out=D/(dso+'-symbolizer.jsonl')
 cmd=[str(loader),'--library-path',libs,str(tool),'--obj='+str(debug),'--functions=linkage','--no-demangle','--inlines','--output-style=JSON','--verbose','--no-debuginfod']
 with q.open() as inp,out.open('w') as stdout,(D/(dso+'-symbolizer.stderr')).open('w') as err:p=sp.run(cmd,stdin=inp,stdout=stdout,stderr=err)
 save(dso+'-command.json',dict(argv=cmd,exit=p.returncode));assert p.returncode==0
 rows=[json.loads(l) for l in out.read_text().splitlines()];assert len(rows)==len(addresses)
 classification={};counts=[]
 for a,row in zip(addresses,rows):
  assert int(row['Address'],16)==a
  frames=row['Symbol'];start=[x.get('StartFileName','') for x in frames];files=[x.get('FileName','') for x in frames]
  if any(P.Path(x).suffix.lower() in ['.c','.h','.cpp','.cc','.hpp'] for x in start):kind='dwarf_c_cpp_function'
  elif any(P.Path(x).suffix.lower() in ['.s','.asm'] for x in files+start):kind='assembly_source_witness'
  else:kind='other_or_outside_dwarf_function'
  classification[a]=kind
 for i,c in enumerate(runs,1):
  cats=Counter()
  for a,n in c.items():cats[classification[a]]+=n
  total=sum(c.values());summary.append(dict(dso=dso,run=i,total=total,categories=dict(cats),shares={k:v/total for k,v in cats.items()}))
 save(dso+'-address-classification.json',[dict(address=hex(a),category=classification[a],counts=[c[a] for c in runs]) for a in addresses])
save('summary.json',summary)
print(json.dumps(summary,indent=2))
