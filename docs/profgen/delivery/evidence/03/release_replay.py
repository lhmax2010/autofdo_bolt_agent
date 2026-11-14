from pathlib import Path
import json,subprocess,hashlib,time,sys,os
W=Path.cwd();D=W/'temp/profgen-release-20261114c';settings=json.loads((D/'release-tool.json').read_text());R=W/'temp/GBS-ROOT-LLVM-X86/local/BUILD-ROOTS/scratch.x86_64.0';dev=W/'temp/llvm-profgen-enh/build/bin/llvm-profgen';release=Path(settings['tool']);newroot=Path(settings['root']);newlib=Path(settings['libdir']);O=D/'replay';O.mkdir();shared=O/'shared';shared.mkdir()
assert hashlib.sha256(dev.read_bytes()).hexdigest()=='2e8895afce661b5fdc8cacab2b3323496fca51af7bd7b51c3753aa8328b7d0d5'
assert hashlib.sha256(release.read_bytes()).hexdigest()==settings['sha256']
prefixes=dict(development=[str(R/'lib64/ld-linux-x86-64.so.2'),'--library-path',':'.join(map(str,[dev.parent.parent/'lib64',R/'lib64',R/'usr/lib64'])),str(dev)],release=[str(newroot/'lib64/ld-linux-x86-64.so.2'),'--library-path',':'.join(map(str,[newlib,newroot/'lib64',newroot/'usr/lib64'])),str(release)])
records=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def diff(a,b,path=''):
 out=[]
 if type(a)!=type(b):return [dict(path=path,old=a,new=b)]
 if isinstance(a,dict):
  for k in sorted(a.keys()|b.keys()):
   if k not in a or k not in b:out.append(dict(path=path+'.'+k,old=a.get(k,'ABSENT'),new=b.get(k,'ABSENT')))
   else:out+=diff(a[k],b[k],path+'.'+k)
 elif isinstance(a,list):
  if len(a)!=len(b):return [dict(path=path,old=a,new=b)]
  for i,(x,y) in enumerate(zip(a,b)):out+=diff(x,y,path+f'[{i}]')
 elif a!=b:out.append(dict(path=path,old=a,new=b))
 return out
jobs=[]
for row in json.loads((W/'temp/profgen-patch9/full-replay.json').read_text()):
 cmd=row['command'];idx=cmd.index(str(dev));args=cmd[idx+1:];args=[v for v in args if not v.startswith(('--output=','--quality-report='))];jobs.append((row['label'],args,row['runs'][0]['exit'],'historical'))
I=W/'temp/llvm-profgen-release/llvm/test/tools/llvm-profgen/Inputs/ip-mode'
for name in ['a64-pie','a64-16k','a64-64k','arm-count','thumb-count','a64-multi-load']:
 for fmt in ['text','binary','extbinary']:
  args=['--ip-samples','--allow-missing-build-id','--binary-match-regex=.*','--binary='+str(I/(name+'.perfbin')),'--perfscript='+str(I/(name+'.perfscript')),'--format='+fmt,'--ip-aggregation=max','--ip-skid=none','--ip-zero-fill=none','--ip-head-samples=none'];jobs.append(('fixture-'+name+'-'+fmt,args,None,'fixture'))
for label,args,expected,kind in jobs:
 profile=shared/(label+'.profile');report=shared/(label+'.json');args=args+['--output='+str(profile),'--quality-report='+str(report)];versions={}
 for version,prefix in prefixes.items():
  target=O/version/label;target.mkdir(parents=True)
  profile.unlink(missing_ok=True);report.unlink(missing_ok=True);cmd=prefix+args;t=time.monotonic()
  with (target/'stdout').open('wb') as so,(target/'stderr').open('wb') as se:p=subprocess.run(cmd,stdout=so,stderr=se,stdin=subprocess.DEVNULL)
  assert report.exists(),(label,version,'missing report')
  for file in [profile,report]:
   if file.exists():(target/file.suffix.lstrip('.')).write_bytes(file.read_bytes())
  versions[version]=dict(command=cmd,exit=p.returncode,seconds=time.monotonic()-t,profile_sha256=sha(profile),json_sha256=sha(report),stderr_sha256=sha(target/'stderr'))
  if version=='development':old=json.loads(report.read_text())
  else:new=json.loads(report.read_text())
 differences=diff(old,new);allowed={'.tool.sha256','.tool.path','.tool.version'}
 unexpected=[x for x in differences if x['path'] not in allowed and not (x['path']=='.tool.arguments[0]' and x['old']==str(dev) and x['new']==str(release))]
 a,b=versions.values();ok=a['exit']==b['exit'] and a['profile_sha256']==b['profile_sha256'] and not unexpected and (expected is None or a['exit']==expected)
 record=dict(label=label,kind=kind,versions=versions,JSON_differences=differences,unexpected=unexpected,passed=ok);records.append(record);(D/'replay-result.json').write_text(json.dumps(records,indent=2));print(label,'pass',ok,'JSON differences',len(differences),flush=True);assert ok,record
print('ALL REPLAYS COMPLETE',len(records))
