import os,json,time,subprocess,hashlib,shutil,shlex
from pathlib import Path
w=Path.cwd().resolve();out=w/'temp/disk-cleanup-20261117-round3'
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(n,x):(out/n).write_text(json.dumps(x,indent=2)+'\n')
old=json.loads((w/'temp/disk-cleanup-20261117-round2/preserved-rpms-logs.json').read_text())
retained={};retained_records=[]
for x in old:
 p=w/x['path']
 if p.is_file():
  digest=sha(p);assert digest==x['sha256'];retained[digest]=str(p);retained_records.append(x)
save('retained-rpms-logs.json',retained_records)
patterns=['GBS-ROOT-FFMPEG-M1-A32-20261114*/local/BUILD-ROOTS','GBS-ROOT-FFMPEG-M1-THUMB-20261114*/local/BUILD-ROOTS','GBS-ROOT-RPI4-PMUV3/local/BUILD-ROOTS','GBS-ROOT-RPI4-SPIKE/local/BUILD-ROOTS','GBS-ROOT-RPI5-SPIKE/local/BUILD-ROOTS','GBS-ROOT-V04-FFMPEG/local/BUILD-ROOTS','m1-pilot-v02-20261116/build/roots/*/local/BUILD-ROOTS','m1-pilot-v02-20261116/build/forensic/roots/*/local/BUILD-ROOTS','m1-target-20261114/weekend-j2/roots/*/local/BUILD-ROOTS','verify-361624-fix-20261116/root-*/local/BUILD-ROOTS','verify-361624-fix-v3-20261116/root-x86_64/local/BUILD-ROOTS','workflow-p1p2-20261116/root-afdo-diag/local/BUILD-ROOTS']
paths=sorted(set(p for pat in patterns for p in (w/'temp').glob(pat)))
# Restrict first two patterns to the four explicitly named original/fix1 roots.
paths=[p for p in paths if not p.parts[-3].startswith('GBS-ROOT-FFMPEG-M1-') or p.parts[-3].endswith(('20261114','20261114-FIX1'))]
rows=[]
for p in paths:
 row=dict(path=str(p),checked=time.time(),reasons=[],copied=[],rpms=[])
 if p.is_symlink() or p.resolve()!=p or not p.is_relative_to(w):row['reasons'].append('path boundary')
 ps=subprocess.check_output(['ps','-eo','pid,user,lstart,args'],text=True)
 mounts=subprocess.check_output(['findmnt','-rn','-o','TARGET'],text=True).splitlines()
 row['processes']=[l for l in ps.splitlines() if str(p) in l or str(p.relative_to(w)) in l]
 row['mounts']=[m for m in mounts if m==str(p) or m.startswith(str(p)+'/')]
 if row['processes'] or row['mounts']:row['reasons'].append('in use')
 errors=[];newest=p.stat().st_mtime;size=0;files=[]
 for root,dirs,names in os.walk(p,followlinks=False,onerror=lambda e:errors.append(str(e))):
  for name in dirs+names:
   q=Path(root)/name
   try:
    st=q.lstat();newest=max(newest,st.st_mtime);size+=st.st_blocks*512
    if q.is_file() and not q.is_symlink():files.append(q)
   except OSError as e:errors.append(str(e))
 row.update(bytes_readable=size,newest_readable=newest,age_hours=(time.time()-newest)/3600,scan_errors=errors)
 if row['age_hours']<12:row['reasons'].append('readable mtime younger than 12h')
 base=p.parent.parent
 # Preserve every chroot RPM and every readable log, outside the chroot.
 if not row['reasons']:
  for scratch in p.iterdir():
   for rpmdir in ['RPMS','SRPMS']:
    d=scratch/'home/abuild/rpmbuild'/rpmdir
    if d.exists():
     err=[];rpms=[]
     for root,dirs,names in os.walk(d,onerror=lambda e:err.append(str(e))):rpms.extend(Path(root)/n for n in names if n.endswith('.rpm'))
     if err:row['reasons'].append('RPM scan incomplete');row['rpm_errors']=err
     for rpm in rpms:
      digest=sha(rpm);record=dict(path=str(rpm),sha256=digest)
      if digest in retained:record['retained']=retained[digest]
      else:
       dest=base/'kept-from-chroot'/digest/rpm.name;dest.parent.mkdir(parents=True,exist_ok=True)
       if not dest.exists():shutil.copy2(rpm,dest)
       assert sha(dest)==digest;record['retained']=str(dest);retained[digest]=str(dest);row['copied'].append(record)
      row['rpms'].append(record)
  for f in files:
   if f.suffix=='.log':
    digest=sha(f);dest=base/'kept-from-chroot/logs'/f.relative_to(p);dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():shutil.copy2(f,dest)
    assert sha(dest)==digest;row['copied'].append(dict(path=str(f),retained=str(dest),sha256=digest))
 # Build completion evidence: original preserved build log containing root path, or known terminal/result.
 candidates=[w/x['path'] for x in old if x['path'].endswith('.log')]
 candidates+=list(base.glob('**/result.json')) if 'GBS-ROOT-' not in base.name else []
 evidence=[]
 for log in candidates:
  if p in log.parents or not log.is_file() or log.stat().st_size>80*1024**2:continue
  try:
   text=log.read_text(errors='replace')
   if str(base) in text or str(base.relative_to(w)) in text:evidence.append(dict(path=str(log),sha256=sha(log),tail=text[-1500:]))
  except OSError:pass
 row['completion_logs']=evidence
 if not evidence:row['reasons'].append('completion log needs individual identification')
 row['eligible']=not row['reasons'];rows.append(row);save('audit.json',rows)
 print(p.relative_to(w),row['bytes_readable'],row['reasons'],flush=True)
save('end.json',dict(time=time.time(),status='audit completed',count=len(rows)))
