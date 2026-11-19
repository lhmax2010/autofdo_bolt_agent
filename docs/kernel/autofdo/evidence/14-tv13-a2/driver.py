from pathlib import Path
import datetime,subprocess,os,time,re,json,shlex,hashlib,statistics,collections,gzip
p=Path(__file__).resolve().parent
project=p.parent.parent
remote='/root/afdo_probe-tv13-20261118'
serial='192.168.108.13:26101'
sdb=['sdb','-s',serial]
env=f'export LC_ALL=C HOME={remote} TMPDIR={remote} PERF_BUILDID_DIR={remote}/buildid LD_LIBRARY_PATH={remote}; cd {remote} || exit 1; '
baseline_path=p/'baseline.out'
process_row=re.compile(r'^\s*(\d+)\s+(\d+)\s+(\S+)\s+([\d.]+)\s+(\d+:\d+:\d+)\s+(.+?)\s*$',re.M)
def procrows(out):
 return {int(pid):(int(ppid),user,float(cpu),dur,comm) for pid,ppid,user,cpu,dur,comm in process_row.findall(out)}
def split_tree(out):
 return re.findall(r'^TREE ([\d.]+)\n(.*?)^TREE_END\s*$',out,re.M|re.S)
def boot_id(text):
 return next((line for line in text.splitlines() if re.fullmatch(r'[a-z0-9-]{36}',line)),'')
def ongoing_sdb():
 found=[]
 for d in Path('/proc').iterdir():
  if not d.name.isdecimal():continue
  try:
   if (d/'comm').read_text().strip()!='sdb':continue
   argv=(d/'cmdline').read_bytes().split(b'\0')
  except OSError:continue
  ops={b'shell',b'push',b'pull',b'root',b'forward',b'dlog'}
  if not ops.intersection(argv):continue
  explicit=(argv[argv.index(b'-s')+1].decode(errors='replace') if b'-s' in argv and len(argv)>argv.index(b'-s')+1 else None)
  if explicit not in (None,serial):continue
  found.append({'pid':int(d.name),'target':explicit,'operations':sorted(x.decode() for x in ops.intersection(argv))})
 return found
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def run(label,args,timeout=30,watch=False,base=sdb):
 started=utc()
 deadlines=time.monotonic()+timeout
 observations=[]
 with (p/f'{label}.out').open('wb') as out,(p/f'{label}.err').open('wb') as err:
  proc=subprocess.Popen(base+args,stdin=subprocess.DEVNULL,stdout=out,stderr=err)
  while True:
   try:
    rc=proc.wait(timeout=.5 if watch else max(.01,deadlines-time.monotonic()))
    break
   except subprocess.TimeoutExpired:
    if watch:
     others=[r for r in ongoing_sdb() if r['pid']!=proc.pid]
     if others:observations.append({'utc':utc(),'clients':others})
    if time.monotonic()>deadlines:
     proc.terminate()
     rc=proc.wait(timeout=10)
     observations.append({'timeout':True})
     break
 data={'argv':base+args,'start':started,'end':utc(),'rc':rc,'foreign_host_sdb':observations}
 (p/f'{label}.json').write_text(json.dumps(data,indent=2)+'\n')
 return rc,(p/f'{label}.out').read_text(errors='replace').replace('\r',''),observations
def shell(label,cmd,timeout=30,watch=False,required=True):
 cmd=cmd+'\nrc=$?; printf "\\n__TV_RC__=%s\\n" "$rc"; exit "$rc"'
 rc,out,obs=run(label,['shell',cmd],timeout,watch)
 m=re.search(r'^__TV_RC__=(\d+)\s*$',out,re.M)
 board_rc=int(m[1]) if m and not rc else None
 if required and board_rc!=0:raise RuntimeError(label+': board rc '+str(board_rc))
 return out,board_rc,obs
baseline_text=baseline_path.read_text()
assert '__BASELINE_DONE__' in baseline_text
assert re.search(r'^INITIAL_UID 0$',baseline_text,re.M)
baseframes=re.findall(r'^FRAME (\d+) ([\d.]+)\n(.*?)^FRAME_END \1\s*$',baseline_text,re.M|re.S)
assert len(baseframes)==61 and float(baseframes[-1][1])-float(baseframes[0][1])>=300
known=set()
base_cpus=collections.defaultdict(list)
acm=[]
for idx,t,out in baseframes:
 rows=procrows(out)
 known.update((v[1],v[-1]) for v in rows.values())
 for pid,entry in rows.items():
  parent,user,cpu,dur,comm=entry
  base_cpus[(user,comm)].append(cpu)
  if comm=='acm-watcher':
   chain=[(pid,comm,user)]
   visited={pid}
   pp=parent
   while pp in rows and pp not in visited:
    v=rows[pp];chain.append((pp,v[-1],v[1]));visited.add(pp);pp=v[0]
   acm.append(dict(frame=int(idx),uptime=float(t),pid=pid,ppid=parent,user=user,ps_pcpu=cpu,chain=chain))
acmlines=[line for line in baseline_text.splitlines() if line.startswith(('ACM_CMD ','0::','1:name=systemd:'))]
(p/'baseline-summary.json').write_text(json.dumps({'frames':len(baseframes),'duration_s':float(baseframes[-1][1])-float(baseframes[0][1]),'load1_range':[min(float(re.search(r'^LOAD ([\d.]+)',f[2],re.M)[1]) for f in baseframes),max(float(re.search(r'^LOAD ([\d.]+)',f[2],re.M)[1]) for f in baseframes)],'acm':acm,'acm_cmdline_cgroup':sorted(set(acmlines))},indent=2)+'\n')
def inspect(out,obs):
 task=re.search(r'^TASK_ROOT (\d+)',out,re.M)
 w=re.search(r'^WATCH_ROOT (\d+)',out,re.M)
 if not task or not w:return {'observer_error':'missing task tree identity','marks':[]}
 roots={int(task[1]),int(w[1])}
 if m:=re.search(r'^WORK_ROOT (\d+)',out,re.M):roots.add(int(m[1]))
 marks=set()
 frames=split_tree(out)
 freqs=[]
 baseline_excursions=collections.Counter()
 for t,frame in frames:
  rows=procrows(frame)
  def ancestry(pid):
   seen=[]
   while pid in rows and pid not in seen:
    seen.append(pid);pid=rows[pid][0]
   return seen
  fq=re.search(r'^FREQ (\d+)',frame,re.M)
  if fq:freqs.append((float(t),int(fq[1])))
  for pid,(ppid,user,cpu,dur,comm) in rows.items():
   chain=ancestry(pid)
   if roots.intersection(chain):continue
   if any(rows[ancestor][-1] in ('sdbd','sdbd-service') for ancestor in chain[1:]):
    marks.add(f'a foreign sdbd descendant {pid}/{comm} chain {chain}')
   if (user,comm) not in known and re.search(r'^(?:perf(?:$|[-_])|gdb(?:server)?$|strace$|ltrace$|stress(?:[-_]|$)|sysbench$|fio$|.*\.sh$|python[0-9.]*$|branch-[01]$)',comm,re.I):
    marks.add(f'b new test/debug process {pid}/{comm}')
   prior=base_cpus.get((user,comm))
   if prior and cpu>max(prior)+5:baseline_excursions[comm]+=1
 if obs:marks.add('c other/unknown host SDB client or transport timeout')
 return {'tree_frames':len(frames),'freq':freqs,'marks':sorted(marks),'system_cpu_excursions':dict(baseline_excursions)}
def pre(label):
 rc,dev,_=run(label+'-devices',['devices'],base=['sdb'])
 assert not rc and any(x.split()[:2]==[serial,'device'] for x in dev.splitlines())
 external=ongoing_sdb()
 if external:
  (p/(label+'-busy.json')).write_text(json.dumps(external,indent=2)+'\n')
  raise RuntimeError('concurrent SDB client at '+label)
 out,_,_=shell(label+'-board',"printf 'PREFLIGHT_ROOT '; printf '%s\\n' \"$$\"; id -u; cat /proc/loadavg; ps -eo pid,ppid,user:24,pcpu,time,comm")
 fake=re.sub(r'^PREFLIGHT_ROOT (\d+)',r'TASK_ROOT \1\nWATCH_ROOT \1\nTREE 0.0',out,flags=re.M).split('__TV_RC__=')[0]+'\nTREE_END\n'
 gate=inspect(fake,[])
 (p/(label+'-gate.json')).write_text(json.dumps(gate,indent=2)+'\n')
 if gate['marks']:raise RuntimeError('shared board before '+label+': '+str(gate['marks']))
def guarded(label,cmd,timeout=55):
 out,rc,obs=shell(label,env+"printf 'TASK_ROOT %s\\n' \"$$\"; ./watch.sh "+cmd,timeout,watch=True,required=False)
 result={**inspect(out,obs),'rc':rc}
 state[label]=result
 print(label,'rc',rc,'marks',result.get('marks'),'freq',len(result.get('freq',[])),flush=True)
 return out,result
irre=r'^\s*(\d+):\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+.*?arm-pmu\b'
def irq(s):return {int(m[0]):[int(n) for n in m[1:]] for m in re.findall(irre,s,re.M)}
def irq_delta(out,before,after):
 if before not in out or after not in out:return None
 parts=out.split(before,1)[1].split(after,1)
 a,b=irq(parts[0]),irq(parts[1])
 if not a or a.keys()!=b.keys():return None
 return {k:[j-i for i,j in zip(a[k],b[k])] for k in a}
busy_workload="bash -c 'SECONDS=0; while (( SECONDS < 2 )); do :; done'"
def stat(label,event,flags='',command=busy_workload):
 out,r=guarded(label,'taskset -c 3 ./perf stat -v --no-scale '+flags+' -e '+event+' -- '+command)
 reading={}
 for name,val,enabled,running in re.findall(r'^(cycles|r0c|r08):uD: (\d+) (\d+) (\d+)\s*$',out,re.M):
  reading[name]=[int(val),int(enabled),int(running)]
 r['count_value_enabled_running']=reading
 return r
def usable(row,event):
 return row.get('rc')==0 and not row.get('marks') and row.get('count_value_enabled_running',{}).get(event,[0,0,0])[2]>0
def stage_snapshot():
 return r"""printf 'UPTIME '; cat /proc/uptime
printf 'PMU_IRQ\n'; grep 'arm-pmu' /proc/interrupts
printf 'PMUMON_LOG\n'; dmesg | grep -F '[PMUMON]' | tail -n 32
true"""
def markers(out):
 a=[]
 for line in out.splitlines():
  m=re.match(r'^\[\s*([\d.]+)\].*\[PMUMON\]',line)
  if m:a.append((float(m[1]),line))
 return a
def stage(label,command,timeout=90):
 pre(label)
 before,_,_=shell(label+'-before',stage_snapshot())
 uptime=float(re.search(r'^UPTIME ([\d.]+)',before,re.M)[1])
 shell(label+'-monitor-start',env+f'printf "%s\\n" {uptime} > pmumon.start')
 try:
  out,rc,obs=shell(label,env+"printf 'TASK_ROOT %s\\n' \"$$\"; taskset -c 0 ./watch.sh "+command,timeout,watch=True,required=False)
  result={**inspect(out,obs),'rc':rc}
 finally:
  after,_,_=shell(label+'-after',stage_snapshot())
 events=[(t,line) for t,line in markers(after) if t>=uptime]
 last=[(t,line) for t,line in markers(before) if t<uptime]
 result['uptime_before']=uptime
 result['uptime_after']=float(re.search(r'^UPTIME ([\d.]+)',after,re.M)[1])
 result['pmumon_after_rows']=[line for _,line in events]
 result['pmumon_previous_row']=last[-1][1] if last else None
 result['pmumon_errors']=[line for _,line in events if re.search(r'\berror\b|\bfailed\b|\bfatal\b|\bfailure\b|overflow warning',line,re.I)]
 result['pmumon_live_interrupt']='PMUMON_LIVE_ERROR' in out
 t=[t for t,_ in last[-1:]+events]
 result['pmumon_gaps_s']=[b-a for a,b in zip(t,t[1:])]
 ia,ib=irq(before),irq(after)
 result['irq_delta']={k:[b-a for a,b in zip(ia[k],ib[k])] for k in ia} if ia and ia.keys()==ib.keys() else None
 result['verbose']={k:[int(v),int(e),int(r)] for k,v,e,r in re.findall(r'^(r0c|r08|cycles):uD:\s+(\d+) (\d+) (\d+)\s*$',out,re.M)}
 match=re.search(r'^\s*([\d.]+) seconds time elapsed',out,re.M)
 if match:result['perf_elapsed_s']=float(match[1])
 state[label]=result
 (p/'result.json').write_text(json.dumps(state,indent=2)+'\n')
 print(label,'rc',rc,'marks',result.get('marks'),'PMUMON rows/errors',len(events),len(result['pmumon_errors']),'counts',result['verbose'],flush=True)
 if result['pmumon_errors'] or result['pmumon_live_interrupt']:
  raise RuntimeError(label+' PMUMON error')
 return out,result
def record(label,event,period,laps):
 out,r=stage(label,f'taskset -c 3 ./perf record -P --sample-cpu --no-buildid-cache --no-buildid -e {event}:uD -c {period} -o {label}.data -- ./block-skid {laps:09d}',timeout=105)
 if r['rc']!=0 or r.get('marks') or not r.get('tree_frames'):
  r['export_status']='skipped: record failed / shared-board mark / missing observer'
  return
 v,_,_=shell(label+'-evlist',env+f'./perf evlist -v -i {label}.data')
 # Assert the sampled attr is user-only and pinned before obtaining the IPs.
 if not re.search(r'exclude_kernel:\s*1\b',v) or not re.search(r'\bpinned:\s*1\b',v):
  r['export_status']='skipped: unverified event flags'
  print(label,'event flags unverified',v[:700],flush=True)
  return
 pulled,_,_=run(label+'-pull',['pull',remote+'/'+label+'.data',str(p/(label+'.data'))],100)
 r['raw_perf_data_pulled']=pulled==0 and (p/(label+'.data')).is_file()
 _,rc,_=shell(label+'-raw',env+f'./perf script --kallsyms /dev/null --show-lost-events -i {label}.data -F comm,pid,cpu,misc,time,period,ip',timeout=160,required=False)
 r['export_status']='exported' if rc==0 else f'perf script rc={rc}'
 r['period']=period
 r['laps']=laps
 print(label,r['export_status'],flush=True)
state=json.loads((p/'first-capture/result.json').read_text())
state['earlier_record_error']='perf script refused CPU output; original record omitted --sample-cpu'
state.pop('d-r0c',None)
state.pop('d-cycles',None)
rooted=False
owned=False
try:
 pre('initial')
 rooted=True
 run('root-on',['root','on'])
 shell('uid-root','test "$(id -u)" = 0 && id -u')
 pre('deployment')
 (p/'cleanup-journal.json').write_text(json.dumps({'path':remote,'registered_utc':utc()},indent=2)+'\n')
 shell('mkdir',f'umask 077; mkdir -- {remote}')
 owned=True
 refs=json.loads((p.parent/'board13-pmu-20261118'/'deployment.json').read_text())
 files={k:refs[k] for k in ('perf','libLLVM.so.22.1','libxml2.so.16')}
 for n in ('watch.sh','branch-0','branch-1','branch-c','branch-call-control','branch-call-return','block-skid'):
  f=p/n;files[n]=dict(source=str(f.relative_to(project)),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),size=f.stat().st_size)
 assert files['branch-0']['sha256']==refs['branch-0']['sha256'] and files['branch-1']['sha256']==refs['branch-1']['sha256']
 (p/'deployment.json').write_text(json.dumps(files,indent=2)+'\n')
 for n,v in files.items():
  src=project/v['source']
  assert hashlib.sha256(src.read_bytes()).hexdigest()==v['sha256'],n
  rc,_,_=run('push-'+n,['push',str(src),remote+'/'+n],90)
  if rc:raise RuntimeError('push '+n)
 want=''.join(f"{v['sha256']}  {n}\n" for n,v in files.items())
 shell('verify-deploy',env+'printf %s '+shlex.quote(want)+' | sha256sum -c - && chmod 700 watch.sh')
 shell('loader',env+'/lib/ld-linux.so.3 --list ./perf && ./perf --version && df -k .')
 laps=state['calibration_laps']
 assert 0<laps<1000000000,laps
 state['calibration_laps']=laps
 print('D 20s target laps',laps,flush=True)
 record('d-r0c','r0c',10007,laps)
 record('d-cycles','cycles',100003,laps)
except BaseException as exc:
 state['stop_reason']=str(exc)
 raise
finally:
 (p/'result.json').write_text(json.dumps(state,indent=2)+'\n')
 try:
  if owned:shell('cleanup',f'rm -rf -- {remote} && test ! -e {remote} && test ! -L {remote} && echo verified-absent')
 finally:
  if rooted:
   run('root-off',['root','off'])
   shell('final','test "$(id -u)" = 5001 && id -u && cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor /proc/sys/kernel/perf_event_paranoid /proc/sys/kernel/kptr_restrict')
  run('devices-final',['devices'],base=['sdb'])
