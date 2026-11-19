from pathlib import Path
import re,json,gzip,hashlib,collections,statistics,math,bisect
p=Path(__file__).resolve().parent
out=json.loads((p/'result.json').read_text())
blocks=json.loads((p/'blocks.json').read_text())
starts=[row['start'] for row in blocks]
N=2**26
counts={}
theory={'branch-0':(N-1,2*N+4),'branch-1':(N-1,4*N+4),'branch-c':(2*N-1,3*N+4),'branch-call-control':(3*N-1,4*N+4),'branch-call-return':(3*N-1,4*N+4)}
for name,(branch,slots) in theory.items():
 labels=[name] if 'call' in name else [f'{name}-{i}' for i in range(1,6)]
 accepted=[]
 for label in labels:
  row=out.get(label)
  if not row or row.get('rc') or row.get('marks') or row.get('pmumon_errors') or not row.get('tree_frames'):continue
  if any(row['verbose'].get(ev,[0,0,0])[2]<=0 for ev in ('r0c','r08','cycles')):continue
  accepted.append(label)
 info={'requested':len(labels),'accepted':accepted,'predicted_taken_branches':branch,'predicted_dynamic_instruction_slots':slots,'events':{}}
 for ev,predicted in [('r0c',branch),('r08',slots),('cycles',None)]:
  raw=[out[label]['verbose'][ev] for label in accepted]
  if not raw:continue
  vals=[v for v,_,_ in raw]
  mean=statistics.mean(vals)
  info['events'][ev]={'mean':mean,'sample_stdev':statistics.stdev(vals) if len(vals)>1 else None,'min':min(vals),'max':max(vals),'running_ratio_range':[min(r/e for _,e,r in raw),max(r/e for _,e,r in raw)],'mean_over_theory':mean/predicted if predicted else None}
 counts[name]=info
periods={}
def pct(values,p):
 return sorted(values)[max(0,math.ceil(p*len(values))-1)] if values else None
def dist(values):
 if not values:return {'n':0}
 return {'n':len(values),'m0_median':statistics.median(values),'p90':pct(values,.9),'within_pct':{str(d):100*sum(x<=d for x in values)/len(values) for d in (0,1,2,4,8)}}
def notes():
 for label in ('d-r0c','d-cycles'):
  r=out.get(label,{})
  f=p/(label+'-raw.out')
  result={'status':r.get('export_status','not-started')}
  periods[label]=result
  if r.get('export_status')!='exported' or not f.exists():continue
  s=f.read_text()
  s=s.rsplit('__TV_RC__=',1)[0]
  pattern=re.compile(r'^\s*(.*?)\s+(-?\d+)\s+\[(\d+)\]\s+(\S+)\s+([\d.]+):\s+(\d+)\s+((?:0x)?[0-9a-fA-F]+)\s*$')
  rows=[]; lost=[]; bad=[]
  for line in s.splitlines():
   if not line.strip():continue
   if re.search(r'\b(?:PERF_RECORD_LOST(?:_SAMPLES)?|LOST)\b',line,re.I):
    lost.append(line);continue
   m=pattern.fullmatch(line)
   if not m:
    bad.append(line[:180]);continue
   comm,pid,cpu,mode,timestamp,period,ip=m.groups()
   addr=int(ip,16)
   index=bisect.bisect_right(starts,addr)-1
   block=blocks[index] if index>=0 else None
   if block is not None and (addr>=block['end'] or (addr-block['start'])%4):block=None
   rows.append({'comm':comm.strip(),'pid':int(pid),'cpu':int(cpu),'mode':mode,'time':timestamp,'period':int(period),'ip':ip,'block':block['id'] if block else None,'offset':(addr-block['start'])//4 if block else None})
  result.update({'samples':len(rows),'unparsed_nonempty_lines':len(bad),'unparsed_examples':bad[:8],'lost_lines':lost,'modes':dict(collections.Counter(x['mode'] for x in rows)),'cpu_counts':dict(collections.Counter(x['cpu'] for x in rows)),'pids':dict(collections.Counter(x['pid'] for x in rows)),'comms':dict(collections.Counter(x['comm'] for x in rows)),'period_counts':dict(collections.Counter(x['period'] for x in rows))})
  if bad or not rows or any(row['mode']!='U' for row in rows):
   result['status']='invalid parse or mode'
   continue
  target_rows=[x for x in rows if x['block'] is not None and x['comm']=='block-skid' and x['cpu']==3]
  result['target_rows']=len(target_rows)
  result['outside_target_rows']=len(rows)-len(target_rows)
  result['observed_block_groups']={str(n):dist([x['offset'] for x in target_rows if blocks[x['block']]['instructions']==n]) for n in (4,16,64)}
  result['observed_block_aggregate']=dist([x['offset'] for x in target_rows])
  if label=='d-r0c':
   exp=(r['laps']*64-1)//r['period']
   # Check entry-locked phase prerequisites before deriving a target/overflow label.
   r0c_mean=counts['branch-0']['events'].get('r0c',{}).get('mean')
   c_mean=counts['branch-c']['events'].get('r0c',{}).get('mean')
   checks={'planned_sample_count':len(rows)==exp,'all_in_d_blocks_on_cpu3':len(target_rows)==len(rows),'one_pid':len({x['pid'] for x in rows})==1,'no_lost_records':not lost,'fixed_reported_period':{x['period'] for x in rows}=={r['period']},'nondecreasing_timestamps':all(float(x['time'])<=float(y['time']) for x,y in zip(rows,rows[1:])),'branch_tests_exact':r0c_mean==N-1 and c_mean==2*N-1}
   phase_hist=collections.Counter((x['block']-((i+1)*r['period'])%64)%64 for i,x in enumerate(rows) if x['block'] is not None)
   result.update({'expected_overflows_from_entry':exp,'phase_checks':checks,'relative_phase_histogram':dict(phase_hist)})
   if all(checks.values()):
    groups={}
    for n in (4,16,64):
     values=[]; crossed=0
     for i,x in enumerate(rows):
      expected=((i+1)*r['period'])%64
      if blocks[expected]['instructions']!=n:continue
      forward=(x['block']-expected)%64
      crossed+=bool(forward)
      values.append(x['offset']+sum(blocks[(expected+j)%64]['instructions'] for j in range(forward)))
     groups[str(n)]={**dist(values),'crossed':crossed,'crossed_pct':100*crossed/len(values) if values else None}
    result['phase_derived_by_target_length']=groups
  result['raw_archive_count']=len(rows)
  fn=p/(label+'-samples.tsv.gz')
  with fn.open('wb') as stream:
   with gzip.GzipFile(filename='',mode='wb',fileobj=stream,mtime=0) as gz:
    gz.write('ip\tcpumode\tcpu\tpid\tcomm\ttime\tperiod\n'.encode())
    for row in rows:gz.write(('\t'.join(str(row[k]) for k in ('ip','mode','cpu','pid','comm','time','period'))+'\n').encode())
  result['archive_sha256']=hashlib.sha256(fn.read_bytes()).hexdigest()
notes()
pmu={}
for k,row in out.items():
 if isinstance(row,dict) and 'pmumon_after_rows' in row:
  core=[list(map(float,m.split('/'))) for l in row['pmumon_after_rows'] for m in re.findall(r'Core:\[([\d./]+)%?\]',l.replace('%',''))]
  pmu[k]={'rows':len(row['pmumon_after_rows']),'gaps':row['pmumon_gaps_s'],'errors':row['pmumon_errors'],'core_pct':core,'irq_delta':row['irq_delta']}
analysis={'counts':counts,'sampling':periods,'pmumon':pmu,'stop':out.get('stop_reason')}
(p/'analysis.json').write_text(json.dumps(analysis,indent=2)+'\n')
for k,v in counts.items():print(k,len(v['accepted']),v['events'])
for k,v in periods.items():print(k,{a:b for a,b in v.items() if a not in ('relative_phase_histogram','lost_lines')})
