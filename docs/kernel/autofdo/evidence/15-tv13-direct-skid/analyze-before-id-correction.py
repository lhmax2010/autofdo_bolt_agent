from pathlib import Path
import re,json,statistics,collections,math,hashlib,gzip,bisect
p=Path(__file__).resolve().parent
state=json.loads((p/'result.json').read_text())
blocks=json.loads((p/'blocks.json').read_text())
starts=[b['start'] for b in blocks]
loops=json.loads((p/'loop-addresses.json').read_text())
ps=re.compile(r'^\s*(.*?)\s+(-?\d+)\s+\[(\d+)\]\s+(\S+)\s+([\d.]+):\s+(\d+)\s+(\S+):\s+((?:0x)?[0-9a-fA-F]+)\s*$')
def pct(values,pct):
 ordered=sorted(values)
 return ordered[max(0,math.ceil(pct*len(ordered))-1)] if ordered else None
def ipc(label):
 header=p/(label+'-header.out')
 dump=p/(label+'-group-read.out')
 if not header.is_file() or not dump.is_file():return {'status':'no same-segment group reads'}
 names={}
 for line in header.read_text().splitlines():
  h=re.search(r'# event : name = (r(?:0c|08|11)):[^,]+,.*?id = \{([^}]+)\}',line)
  if h:
   for i in re.findall(r'\d+',h[2]):names[int(i)]=h[1]
 if len(names)!=3 or set(names.values())!={'r0c','r08','r11'}:return {'status':'event IDs not resolved','ids':names}
 raw=dump.read_text()
 matches=[]
 for fragment in re.split(r'^\.\.\. sample_read:\s*$',raw,flags=re.M)[1:]:
  first=fragment.strip().splitlines()[:7]
  row={}
  for line in first:
   if m:=re.match(r'^\.+ id ([\da-fA-F]+), value ([\da-fA-F]+)(?:, lost (\d+))?',line):
    if int(m[1],16) in names:row[names[int(m[1],16)]]=int(m[2],16)
    if m[3] and int(m[3]):return {'status':'counter lost'}
   if m:=re.match(r'^\.+ time (enabled|running) ([\da-fA-F]+)',line):
    row[m[1]]=int(m[2],16)
  if set(row)>={'r0c','r08','r11'}:matches.append(row)
 if len(matches)<2:return {'status':'too few group READ samples','groups':len(matches)}
 a,b=matches[0],matches[-1]
 totals={k:b[k]-a[k] for k in a.keys()&b.keys()}
 n,c=totals.get('r08',0),totals.get('r11',0)
 if n<=0 or c<=0:return {'status':'invalid raw deltas','groups':len(matches),'deltas':totals}
 if 'enabled' in totals and (totals['enabled']<=0 or totals.get('running')!=totals['enabled']):
  return {'status':'incomplete pinned coverage','groups':len(matches),'deltas':totals}
 return {'status':'ok','group_samples':len(matches),'first':a,'last':b,'deltas':totals,'ipc':n/c}
def distribution(counts):
 return {str(n):counts.get(n,0) for n in range(4)}
def freqstate(row):
 return sorted({value for _,value in row.get('freq',[])})
allstats={}
for label,r in state.items():
 if not isinstance(r,dict) or 'export_status' not in r:continue
 out={'status':r['export_status'],'freq':freqstate(r)}
 allstats[label]=out
 if r['export_status']!='exported':continue
 content=(p/(label+'-raw.out')).read_text().rsplit('__TV_RC__=',1)[0]
 matches=[]
 bad=[]; lost=[]; followers=collections.Counter(); dropped_mode=collections.Counter()
 for line in content.splitlines():
  if not line.strip():continue
  if re.search(r'\b(?:PERF_RECORD_LOST(?:_SAMPLES)?|LOST)\b',line,re.I):
   lost.append(line);continue
  m=ps.fullmatch(line)
  if not m:
   bad.append(line[:200]);continue
  comm,pid,cpu,mode,stamp,period,event,ip=m.groups()
  if mode!='U':dropped_mode[mode]+=1
  if event.split(':',1)[0]!=r['event']:
   followers[event]+=1
   continue
  matches.append((ip,mode,int(cpu),int(pid),comm.strip(),stamp,int(period),event))
 out.update(samples=len(matches),nonempty_unparsed=len(bad),unparsed_examples=bad[:6],lost_lines=lost,non_user=dict(dropped_mode),synthetic_sibling_lines=dict(followers))
 if bad or dropped_mode or not matches:
  out['status']='invalid or incomplete parse';continue
 out['cpu_counts']=dict(collections.Counter(x[2] for x in matches))
 out['comm_counts']=dict(collections.Counter(x[4] for x in matches))
 out['periods']=dict(collections.Counter(x[6] for x in matches))
 out['time_span']=float(matches[-1][5])-float(matches[0][5])
 if set(out['cpu_counts'])!={3} or set(out['comm_counts'])!={r['fixture']} or set(out['periods'])!={r['period']}:
  out['status']='sample identity mismatch';continue
 seen=collections.Counter()
 if label.startswith('d-'):
  bylen=collections.Counter()
  for x in matches:
   ip=int(x[0],16)
   idx=bisect.bisect_right(starts,ip)-1
   if idx<0 or ip>=blocks[idx]['end'] or (ip-starts[idx])%4:seen['outside']+=1;continue
   seen[idx]+=1
   bylen[blocks[idx]['instructions']]+=1
  out.update(by_block={str(n):seen[n] for n in range(64)},by_length=dict(bylen),outside=seen['outside'])
 else:
  cfg=loops[r['fixture']]
  offsets=[]
  for x in matches:
   ip=int(x[0],16)
   if not cfg['start']<=ip<cfg['end_exclusive'] or (ip-cfg['start'])%4:seen['outside']+=1;continue
   offsets.append((ip-cfg['start'])//4)
  nums=collections.Counter(offsets)
  out.update(outside=seen['outside'],control=sum(n>=512 for n in offsets),within_512=len(offsets)-sum(n>=512 for n in offsets),offset_histogram=dict(sorted(nums.items())),quantiles={'median':statistics.median(offsets),'p90':pct(offsets,.90),'p99':pct(offsets,.99),'max':max(offsets)} if offsets else {})
  if r['event']=='r0c':
   out['same_segment']=ipc(label)
   if out['same_segment']['status']=='ok':
    out['estimated_skid_cycles']={k:v/out['same_segment']['ipc'] for k,v in out['quantiles'].items()}
  else:
   num_filler=out['within_512']
   out['uniform_filler_reference']={'buckets64':[sum(nums[x] for x in range(i,i+64)) for i in range(0,512,64)],
     'tv_vs_flat_512':sum(abs(nums[i]/num_filler-1/512) for i in range(512))/2 if num_filler else None}
 archived=p/(label+'-samples.tsv.gz')
 with archived.open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',fileobj=f,mtime=0) as z:
   z.write(b'ip\tcpumode\tcpu\tpid\tcomm\ttime\tperiod\tevent\n')
   for row in matches:z.write(('\t'.join(map(str,row))+'\n').encode())
 out['archive_sha256']=hashlib.sha256(archived.read_bytes()).hexdigest()
cmp={}
for a,b in [('d-cycles','d-r11'),('d-r11','d-r0c')]:
 if not all(k in allstats and allstats[k]['status']=='exported' for k in (a,b)):continue
 x,y=[allstats[k] for k in (a,b)]
 cmp[a+'/'+b]={'tv_block':sum(abs(x['by_block'][str(i)]/x['samples']-y['by_block'][str(i)]/y['samples']) for i in range(64))/2,'tv_length':sum(abs(x['by_length'].get(n,0)/x['samples']-y['by_length'].get(n,0)/y['samples']) for n in (4,16,64))/2}
analysis={'records':allstats,'comparison':cmp,'stop':state.get('stop_reason')}
(p/'analysis.json').write_text(json.dumps(analysis,indent=2)+'\n')
for k,v in allstats.items():
 print(k,{n:v[n] for n in ('status','samples','outside','time_span','by_length','quantiles','control','same_segment','estimated_skid_cycles','uniform_filler_reference','lost_lines','nonempty_unparsed','unparsed_examples') if n in v})
print(cmp)
