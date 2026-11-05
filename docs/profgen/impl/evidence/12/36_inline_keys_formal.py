from pathlib import Path
import re,json,collections,importlib.util
w=Path.cwd();d=w/'temp/profgen-patch8/independent-avg';g=w/'temp/board-round1-resume2/gnu'
spec=importlib.util.spec_from_file_location('check',d/'check.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
old=json.loads((d/'result.json').read_text());subs=json.loads((g/'subprograms.json').read_text());byoff={int(x['offset'],16):x for x in subs};roots=[next(x for x in subs if x['name']==n and 'low_pc' in x) for n in old['selected_names']];root_offsets={int(x['offset'],16):x for x in roots}
# GNU textual DIE dump supplies ancestor call-site attributes independently.
trees={};current=None;root=None;depth0=None
for line in (g/'debug-info.stdout').open():
 m=re.match(r'\s*<(\d+)><([0-9a-f]+)>: Abbrev Number: \d+(?: \((DW_TAG_\w+)\))?',line)
 if m:
  depth=int(m[1]);off=int(m[2],16)
  if off in root_offsets:root=off;depth0=depth;trees[root]=[]
  elif root is not None and depth<=depth0:root=None
  current=None
  if root is not None:
   current={'offset':off,'depth':depth,'tag':m[3]};trees[root].append(current)
  continue
 m=re.search(r'DW_AT_(\w+)\s*:\s*(.*)',line)
 if m and current is not None:current[m[1]]=m[2]
ranges=collections.defaultdict(list);bases={}
for line in (d/'gnu-ranges.stdout').open():
 m=re.fullmatch(r'\s*([0-9a-f]+) ([0-9a-f]+) ([0-9a-f]+)(.*)',line.rstrip())
 if not m:continue
 off,a,b=[int(x,16) for x in m.group(1,2,3)]
 if 'base address' in m[4]:bases[off]=b
 else:ranges[off].append((a+bases.get(off,0),b+bases.get(off,0)))
def num(x):return int(x,0)
for root,ds in trees.items():
 for x in ds:
  if x['tag'] not in ('DW_TAG_subprogram','DW_TAG_inlined_subroutine'):continue
  if x['tag']=='DW_TAG_subprogram':x['resolved']=byoff[root]
  else:x['resolved']=byoff[int(re.search(r'0x([0-9a-f]+)',x['abstract_origin'])[1],16)]
  if 'ranges' in x:x['intervals']=ranges[num(x['ranges'])]
  elif 'low_pc' in x:x['intervals']=[(num(x['low_pc']),num(x['low_pc'])+num(x['high_pc']))]
  else:x['intervals']=[]
(d/'gnu-inline-trees.json').write_text(json.dumps(trees,indent=2)+'\n')
report=json.loads((w/'temp/board-round1-resume2/runs/formal2-ffmpeg-thumb-S-sample-fixed-bbb-100000-r1-s1/quality.json').read_text());target=report['identity']['candidates'][0]['path'];samples=collections.Counter()
for line in (w/'temp/board-round1-resume2/runs/formal2-ffmpeg-thumb-S-sample-fixed-bbb-100000-r1-s1/perfscript.txt').open():
 m=re.search(r'\('+re.escape(target)+r'\+0x([0-9a-f]+)\)\s*$',line)
 if m:samples[int(m[1],16)]+=1
# PT_LOAD off==VA==0 was independently checked by original checker.
profiles={name:mod.text_profile((d/(name+'.text')).read_text()) for name in ['avg','sum','max'] if (d/(name+'.text')).exists()};results=[]
for index,rootrow in enumerate(roots):
 root=int(rootrow['offset'],16);ds=trees[root];start=num(rootrow['low_pc']);end=start+num(rootrow['high_pc'])
 addresses=[]
 for line in (d/f'function-{index}.stdout').read_text().splitlines():
  cols=line.split('\t');m=re.fullmatch(r'\s*([0-9a-f]+):',cols[0])
  if m and len(cols)>=3 and not cols[2].strip().startswith('.'):
   addr=int(m[1],16)
   if start<=addr<end:addresses.append(addr)
 groups={};cur=None
 for line in (d/f'lines-{index}.stdout').read_text().splitlines():
  if re.fullmatch(r'0x[0-9a-f]+',line):cur=int(line,16);groups[cur]=[]
  elif cur is not None:groups[cur].append(line)
 counts=collections.Counter();sums=collections.Counter();nums=collections.Counter();maxima=collections.Counter();problems=[];changes=[]
 for addr in addresses:
  raw=groups[addr];m=re.search(r':(\d+|\?)(?: \(discriminator (\d+)\))?$',raw[1]);assert m
  leafline=0 if m[1]=='?' else int(m[1]);disc=int(m[2] or 0)
  if not leafline:continue
  chain=sorted([x for x in ds if 'intervals' in x and any(a<=addr<b for a,b in x['intervals'])],key=lambda x:x['depth'])
  assert chain and chain[0]['offset']==root
  gnunames=raw[::2][::-1];dienames=[x['resolved']['name'] for x in chain]
  if gnunames!=dienames:problems.append(dict(address=hex(addr),gnu=gnunames,dies=dienames));continue
  context=(rootrow['name'],)
  for parent,child in zip(chain,chain[1:]):
   call_line=num(child['call_line']);call_disc=num(child.get('GNU_discriminator','0'));decl=num(parent['resolved']['decl_line']);context+=((((call_line-decl)&0xffff,mod.decode(call_disc)),child['resolved']['name']),)
  key=(context,((leafline-num(chain[-1]['resolved']['decl_line']))&0xffff,mod.decode(disc)))
  counts[key]+=1
  if samples[addr]:
   contribution=samples[addr]*mod.duplication(disc);sums[key]+=samples[addr];nums[key]+=contribution;maxima[key]=max(maxima[key],contribution)
 rows=[];diffs=[]
 for key,total in nums.items():
  n=counts[key];avg=max(1,(2*total+n)//(2*n));row=dict(context=key[0],location=key[1],n=n,numerator=total,avg=avg,sum=sums[key],max=maxima[key]);rows.append(row)
  for agg in profiles:
   value=profiles[agg].get(key)
   if value!=row[agg]:diffs.append(dict(aggregation=agg,row=row,actual=value))
 results.append(dict(function=rootrow['name'],instruction_count=len(addresses),keys=rows,problems=problems,differences=diffs));print(index,'keys',len(rows),'problems',len(problems),'diffs',len(diffs),flush=True)
(d/'gnu-inline-comparison.json').write_text(json.dumps(results,indent=2)+'\n')
