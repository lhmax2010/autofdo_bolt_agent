import os,sys,time,json,subprocess,stat,hashlib,re
from pathlib import Path
W=Path.cwd(); O=W/'temp/disk-cleanup-20261117-round2'; now=time.time()
def save(n,x): (O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def cmd(a):
 r=subprocess.run(a,capture_output=True,text=True); return dict(command=a,rc=r.returncode,stdout=r.stdout,stderr=r.stderr)
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
refs=[]
files=[Path('docs/STATUS.md')]+list(Path('docs/profgen/delivery').rglob('*'))+list(Path('workflow').rglob('*.toml'))+list(Path('workflow').rglob('*.json'))+list(Path('workflow').rglob('*.conf'))+list(Path('temp/m1-ffmpeg-rpi4-thumb-01').glob('**/job.json'))
for f in files:
 if f.is_file():
  t=f.read_text(); refs.append((str(f),t));
hq=cmd(['git','ls-tree','-r','--name-only','refs/remotes/origin/hq']);save('hq-tree.json',hq)
if hq['rc']:raise SystemExit('hq unavailable')
for f in hq['stdout'].splitlines():
 if f.endswith(('.md','.toml','.in','.sh')):
  q=cmd(['git','show','refs/remotes/origin/hq:'+f]);assert q['rc']==0;refs.append(('origin/hq:'+f,q['stdout']))
save('reference-inputs.json',[dict(path=p,sha256=hashlib.sha256(t.encode()).hexdigest()) for p,t in refs])
ps=cmd(['ps','-eo','pid,user,lstart,args']);save('process-snapshot.json',ps)
mt=cmd(['findmnt','--json','-o','TARGET,SOURCE,FSTYPE']);save('mount-snapshot.json',mt)
def targets(xs):
 for x in xs:
  yield x['target'];yield from targets(x.get('children',[]))
mounts=list(targets(json.loads(mt['stdout'])['filesystems']))
candidates={}
parents=list(Path('temp').glob('GBS-ROOT*'))+list(Path('temp').glob('verify-361624-fix*'))+[Path('temp/m1-target-20261114'),Path('temp/m1-pilot-v02-20261116/build'),Path('temp/workflow-p1p2-20261116')]
# Only traverse shallow directory names to discover local/BUILD-ROOTS and local/cache; never chroots.
localroots=[]
for parent in parents:
 for d,ds,fs in os.walk(parent,followlinks=False):
  p=Path(d);depth=len(p.relative_to(parent).parts)
  ds[:]=[n for n in ds if not (p/n).is_symlink() and n not in ['.git','repo','repos','BUILD-ROOTS','cache','usr','proc','dev','sys']]
  if p.name=='local':
   localroots.append(p)
   for n in ['BUILD-ROOTS','cache']:
    if (p/n).is_dir():candidates[str(p/n)]='chroot' if n=='BUILD-ROOTS' else 'cache'
   ds[:]=[]
  if depth>=5:ds[:]=[]
for pat in ['temp/verify-361624-fix*/source','temp/llvm-profgen-forward-20261114','temp/llvm-profgen-sandbox-verify-20261114','temp/llvm-profgen-release','temp/linux-rpi-pmuv3-am-check','temp/linux-rpi-pmuv3-gerrit']:
 for p in Path('.').glob(pat):candidates[str(p)]='source'
for name in ['temp/llvm-profgen-enh/build','temp/profgen-patch9/prebuild-tool']:
 if Path(name).exists():candidates[name]='tool-build'
for p in Path('temp/tmp').iterdir():candidates[str(p)]='temporary'
candidates['temp/m1-ffmpeg-rpi4-thumb-01/attempt-02/ffmpeg']='failed-clone-protected-current-experiment'
results=[]
for name,kind in sorted(candidates.items()):
 p=W/name;r=dict(path=name,kind=kind,check_time=time.time(),reasons=[],reference_hits=[])
 if not p.exists():r['reasons'].append('missing');results.append(r);continue
 r['realpath']=str(p.resolve());r['symlink']=p.is_symlink();r['inside']=p.resolve().is_relative_to(W)
 if r['symlink'] or not r['inside']:r['reasons'].append('symlink_or_outside')
 for src,t in refs:
  for ln,line in enumerate(t.splitlines(),1):
   if name in line or str(p) in line:r['reference_hits'].append(dict(file=src,line=ln,text=line[:1500]))
 if r['reference_hits']:r['reasons'].append('referenced')
 r['mounts']=[m for m in mounts if m==str(p) or m.startswith(str(p)+'/')]
 if r['mounts']:r['reasons'].append('mounted')
 r['processes']=[l for l in ps['stdout'].splitlines() if (name in l or str(p) in l) and re.search(r'gbs|build|rpmbuild|qemu|ninja|make|cmake|git|python3 -m afdo_wf',l)]
 if r['processes']:r['reasons'].append('process_use')
 if 'current-experiment' in kind:r['reasons'].append('current_experiment_preserved')
 newest=p.lstat().st_mtime;blocks=0;count=0;errors=[];protected=[];seen=set()
 if not r['mounts'] and not r['symlink'] and r['inside']:
  def scan(f):
   global newest,blocks,count
   st=f.lstat();newest=max(newest,st.st_mtime);key=(st.st_dev,st.st_ino)
   if key not in seen:blocks+=st.st_blocks*512;seen.add(key)
   count+=1
   if f.is_symlink():return
   if stat.S_ISREG(st.st_mode) and (f.suffix in ['.rpm','.log','.prof','.profdata','.perf','.extbinary'] or f.name in ['perf.data','build.log']):protected.append(str(f.relative_to(W)))
  try:scan(p)
  except OSError as e:errors.append(str(e))
  if p.is_dir():
   for d,ds,fs in os.walk(p,followlinks=False,onerror=lambda e:errors.append(str(e))):
    for n in ds+fs:
     try:scan(Path(d)/n)
     except OSError as e:errors.append(str(e))
 r.update(bytes=blocks,newest_mtime=newest,age_hours=(now-newest)/3600,entries=count,scan_errors=errors,protected_files=protected)
 if errors:r['reasons'].append('mtime_or_evidence_scan_incomplete')
 if r['age_hours']<=12:r['reasons'].append('modified_within_12h')
 if protected:r['reasons'].append('contains_RPM_log_or_data_preserve')
 if kind=='source' and not r['reasons']:
  g=['git','-c','gc.auto=0','-c','maintenance.auto=false','-C',str(p)]
  status=cmd(g+['status','--porcelain']);heads=cmd(g+['for-each-ref','--format=%(objectname)','refs/heads']);head=cmd(g+['rev-parse','HEAD']);r['git']=dict(status=status,heads=heads,head=head)
  if status['rc'] or status['stdout'].strip() or heads['rc'] or head['rc']:r['reasons'].append('dirty_or_git_unavailable')
  else:
   repos=['src/linux-rpi','temp/linux-rpi-pmuv3'] if 'linux-rpi' in name else ['src/llvm','temp/gerrit-361624-ssh']
   proof=[]
   for c in sorted(set(heads['stdout'].splitlines()+head['stdout'].splitlines())):
    matches=[]
    for repo in repos:
     z=cmd(['git','-C',repo,'for-each-ref','--contains',c,'--format=%(refname)']);
     if z['rc']==0 and z['stdout'].strip():matches.append(dict(repo=repo,refs=z['stdout'].splitlines()))
    proof.append(dict(commit=c,reachable_in=matches))
   r['commit_proof']=proof
   if any(not x['reachable_in'] for x in proof):r['reasons'].append('commit_not_proven_preserved')
 if kind=='tool-build':r['reasons'].append('tool_evidence_and_runtime_dependencies_preserved_pending_review')
 r['eligible']=not r['reasons'];results.append(r);save('audit.json',results)
 print(name,round(blocks/2**30,3),r['reasons'] or 'ELIGIBLE',flush=True)
# RPMs/logs outside deletion candidates remain at exact paths. Hash only regular non-symlink files.
keep=[]; excluded=[W/n for n in candidates]
for local in localroots:
 for sub in ['repos','order']:
  q=local/sub
  if q.exists():
   for d,ds,fs in os.walk(q,followlinks=False):
    ds[:]=[n for n in ds if not (Path(d)/n).is_symlink()]
    for n in fs:
     f=Path(d)/n
     if not f.is_symlink() and (f.suffix in ['.rpm','.log'] or 'log' in n):
      try:keep.append(dict(path=str(f),bytes=f.stat().st_size,sha256=sha(f)))
      except OSError as e:keep.append(dict(path=str(f),error=str(e)))
save('preserved-rpms-logs.json',keep)
save('finish.json',dict(time=time.time(),candidates=len(results),eligible=sum(x.get('eligible',False) for x in results),preserved=len(keep)))
