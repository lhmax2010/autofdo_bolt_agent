import os,json,time,hashlib,subprocess,re,shutil
from pathlib import Path
W=Path.cwd();O=W/'temp/disk-cleanup-20261117-round2';a=json.loads((O/'audit.json').read_text());results=[]
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def run(c):
 r=subprocess.run(c,capture_output=True,text=True);return dict(command=c,rc=r.returncode,stdout=r.stdout,stderr=r.stderr)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def git(p,args):return run(['git','-c','gc.auto=0','-c','maintenance.auto=false','-C',str(p),*args])
# Refine source fixtures: tracked test files are preserved by verified source commits.
for r in a:
 if r['kind']!='source' or r.get('reference_hits') or r.get('scan_errors'):continue
 p=W/r['path'];status=git(p,['status','--porcelain','--untracked-files=all']);heads=git(p,['for-each-ref','--format=%(objectname)','refs/heads']);head=git(p,['rev-parse','HEAD']);tracked=git(p,['ls-files','-z'])
 r['git']=dict(status=status,heads=heads,head=head)
 trackedfiles=set(tracked['stdout'].split('\0'));unpreserved=[f for f in r['protected_files'] if str(Path(f).relative_to(r['path'])) not in trackedfiles]
 r['untracked_evidence']=unpreserved
 if not unpreserved:r['reasons']=[x for x in r['reasons'] if x!='contains_RPM_log_or_data_preserve']
 if status['rc'] or status['stdout'].strip() or heads['rc'] or head['rc']:r['reasons'].append('dirty_or_git_unavailable')
 else:
  repos=['src/linux-rpi','temp/linux-rpi-pmuv3'] if 'linux-rpi' in str(p) else ['src/llvm','temp/gerrit-361624-ssh'];proof=[]
  for c in sorted(set(heads['stdout'].splitlines()+head['stdout'].splitlines())):
   hits=[]
   for repo in repos:
    z=git(repo,['for-each-ref','--contains',c,'--format=%(refname)'])
    if z['rc']==0 and z['stdout'].strip():hits.append(dict(repo=repo,refs=z['stdout'].splitlines()))
    z=git(repo,['merge-base','--is-ancestor',c,'HEAD'])
    if z['rc']==0:hits.append(dict(repo=repo,refs=['HEAD']))
   proof.append(dict(commit=c,reachable_in=hits))
  r['commit_proof']=proof
  if any(not x['reachable_in'] for x in proof):r['reasons'].append('commit_not_proven_preserved')
 r['eligible']=not r['reasons']
save('refined-audit.json',a)
# Recheck every deletion candidate immediately before deletion. Never use sudo except authorized chroot removal (none eligible).
archives=[]
for r in a:
 p=W/r['path'];kind=r['kind'];reasons=r['reasons'][:]
 if kind=='cache' and set(reasons)<= {'contains_RPM_log_or_data_preserve'}:
  dest=W/'temp/gbs-deps-archive/disk-cleanup-20261117-round2';dest.mkdir(exist_ok=True)
  saved=[];errors=[]
  for d,ds,fs in os.walk(p,followlinks=False):
   if any((Path(d)/n).is_symlink() for n in ds+fs):errors.append('symlink in cache');break
   for n in fs:
    f=Path(d)/n
    try:
     h=sha(f);target=dest/(h+'-'+f.name)
     if not target.exists():shutil.copy2(f,target)
     assert sha(target)==h
     saved.append(dict(original=str(f.relative_to(W)),retained=str(target.relative_to(W)),sha256=h,bytes=f.stat().st_size))
    except Exception as e:errors.append(str(e));break
  archives.extend(saved);save('preserved-cache-files.json',archives)
  if errors:reasons.append('archive_failed:'+str(errors))
  else:reasons=[x for x in reasons if x!='contains_RPM_log_or_data_preserve']
 if reasons:
  results.append(dict(path=r['path'],status='retained',reasons=reasons,bytes=r.get('bytes',0)));continue
 # Fresh process/mount/mtime/link/reference checks.
 ps=run(['ps','-eo','pid,user,lstart,args']);mount=run(['findmnt','--json','-o','TARGET,SOURCE,FSTYPE'])
 def targets(xs):
  for x in xs:yield x['target'];yield from targets(x.get('children',[]))
 ms=[m for m in targets(json.loads(mount['stdout'])['filesystems']) if m==str(p) or m.startswith(str(p)+'/')]
 processes=[l for l in ps['stdout'].splitlines() if (str(p) in l or r['path'] in l) and re.search('gbs|build|rpmbuild|qemu|ninja|make|cmake|git|python3 -m afdo_wf',l)]
 errs=[];latest=p.lstat().st_mtime
 for d,ds,fs in os.walk(p,followlinks=False,onerror=lambda e:errs.append(str(e))) if p.is_dir() else []:
  for n in ds+fs:
   try:latest=max(latest,(Path(d)/n).lstat().st_mtime)
   except OSError as e:errs.append(str(e))
 ref_unchanged=True
 for row in json.loads((O/'reference-inputs.json').read_text()):
  if row['path'].startswith('origin/hq:'):
   rr=run(['git','show','refs/remotes/'+row['path']]);h=hashlib.sha256(rr['stdout'].encode()).hexdigest()
  else:h=sha(W/row['path'])
  if h!=row['sha256']:ref_unchanged=False
 check=dict(path=r['path'],ps=ps,mounts=mount,mount_hits=ms,process_hits=processes,mtime=latest,age_hours=(time.time()-latest)/3600,errors=errs,reference_inputs_unchanged=ref_unchanged)
 save('predelete-'+str(len(results))+'.json',check)
 if ps['rc'] or mount['rc'] or ms or processes or errs or not ref_unchanged or time.time()-latest<=43200 or p.is_symlink() or not p.resolve().is_relative_to(W):
  results.append(dict(path=r['path'],status='retained_recheck_failed',bytes=r['bytes'],check=check));continue
 if kind=='source':
  current=git(p,['status','--porcelain','--untracked-files=all'])
  if current['rc'] or current['stdout'].strip():results.append(dict(path=r['path'],status='retained_source_changed'));continue
 result=run(['rm','-rf','--one-file-system','--',str(p)])
 row=dict(path=r['path'],status='deleted' if result['rc']==0 and not p.exists() else 'delete_failed',allocated_bytes_before=r['bytes'],command_result=result,end=time.time());results.append(row)
 save('deletions.json',results);print(row['status'],r['path'],r['bytes'],flush=True)
save('deletions.json',results)
save('df-after.json',run(['df','-B1','.']))
print('RESULT',[(r['path'],r['status']) for r in results if r['status']!='retained'],flush=True)
