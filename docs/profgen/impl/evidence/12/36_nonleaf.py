from pathlib import Path
import json,subprocess,re,collections
w=Path.cwd();d=w/'temp/board-round1-patch8';r=w/'temp/GBS-ROOT-LLVM-X86/local/BUILD-ROOTS/scratch.x86_64.0';l=w/'temp/llvm-profgen-enh';rows=[];total=collections.Counter();targets=usable=0
for old in json.loads((d/'reconverted.json').read_text())['runs']:
 q=old['quality'];out=d/'converted'/Path(old['source']).name;expected=int(re.search(r'usable_nonleaf_line_zero samples=(\d+)', '\n'.join(old['diagnostic_counts']))[1]);targets+=q['samples']['target']['counts']['sample_count'];usable+=q['samples']['target']['usable']['sample_count']
 counts={int(a,16):int(c) for a,c in re.findall(r'^IP-ADDRESS (0x[0-9a-f]+) sample_count=(\d+)',(out/'stdout').read_text(),re.M)}
 names=collections.Counter();involved=collections.Counter();detail=[]
 if expected:
  aliases={x['begin']:x['original_begin'] for x in q['thumb_dwarf_normalization']['top50']};cmd=['nice','-n','19','ionice','-c3',str(r/'lib64/ld-linux-x86-64.so.2'),'--library-path',f'{l}/build/lib64:{r}/lib64:{r}/usr/lib64',str(d/'nonleaf'),q['identity']['debug_binary']];inp=''.join(f'{a:x} {aliases.get(a,a):x}\n' for a in sorted(counts));(out/'nonleaf-input').write_text(inp)
  p=subprocess.run(cmd,input=inp,text=True,capture_output=True);(out/'nonleaf-raw.jsonl').write_text(p.stdout);(out/'nonleaf.stderr').write_text(p.stderr);assert not p.returncode
  for line in p.stdout.splitlines():
   x=json.loads(line)
   if x['usable'] and x['nonleaf_line_zero']:
    c=counts[x['address']];names[x['root']]+=c
    for fn in set(x['nonleaf_line_zero']):involved[fn]+=c
    detail.append(dict(address=hex(x['address']),count=c,root=x['root'],zero_line_frames=x['nonleaf_line_zero']))
  (out/'nonleaf-command.json').write_text(json.dumps(dict(command=cmd,exit=p.returncode,stdin=str(out/'nonleaf-input')),indent=2)+'\n')
 assert sum(names.values())==expected,(expected,names)
 rows.append(dict(run=old['source'],nonleaf_samples=expected,top_level_functions=names,zero_line_frame_functions=involved,addresses=detail));total.update(names)
res=dict(scope='all eight currently complete formal S RUNs; not the uncollected remainder',target_samples=targets,usable_samples=usable,nonleaf_samples=sum(total.values()),target_ratio=sum(total.values())/targets,usable_ratio=sum(total.values())/usable,top20=total.most_common(20),runs=rows)
(d/'nonleaf-summary.json').write_text(json.dumps(res,indent=2)+'\n');print({k:v for k,v in res.items() if k!='runs'})
