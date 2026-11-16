exec((__import__('pathlib').Path(__file__).parent/'common.py').read_text())
D=D/'conversion';D.mkdir(exist_ok=True);ops=[];result={};access=[]
root=W/'temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0';rpm=W/'temp/profgen-release-20261114c/extracted';loader=root/'lib64/ld-linux-x86-64.so.2';libs=str(rpm/'usr/lib64')+':'+str(root/'lib64')+':'+str(root/'usr/lib64')
def llvm(n,args):
 return run(n,[str(loader),'--library-path',libs,str(rpm/'usr/bin'/args[0]),*args[1:]],600)
def disclose(p,purpose):
 access.append(dict(object=str(p.relative_to(W)),time=datetime.datetime.now().astimezone().isoformat(),purpose=purpose));save('Q5-17-profile-access.json',access)
try:
 assert json.loads((D.parent/'stage3/result.json').read_text())['success']
 assert sha(rpm/'usr/bin/llvm-profgen')=='67ad21faba787d276a80673c1f324f7c0591d28d76bd37a8bd57de0d86426be6'
 save('tool-identities.json',[dict(path=str(p),sha256=sha(p)) for p in [loader,rpm/'usr/bin/llvm-profgen',rpm/'usr/bin/llvm-profdata',rpm/'usr/lib64/libLLVM.so.22.1']])
 base=W/'temp/m1-target-20261114/weekend-j2/thumb-attempt-0/extracted';manifest=json.loads((D.parent/'base-manifest.json').read_text());summary=[];merged=[]
 for dso in ['libavcodec','libavutil']:
  f=next(x for x in manifest if x['path'].startswith('lib/'+dso+'.so.') and x['symlink'] is None);real=P.Path(f['path']).name
  binary=base/'usr/lib'/real;debug=base/'usr/lib/debug/usr/lib'/(real+'.debug')
  assert sha(binary)==f['sha256'];assert debug.exists(),str(debug)
  profiles=[]
  for i in range(1,4):
   receipt=json.loads((D.parent/'stage3'/('pull-receipt-'+str(i)+'.json')).read_text());p=P.Path(receipt['local']);out=D/(dso+'-run'+str(i)+'.extbinary');q=D/(dso+'-run'+str(i)+'.quality.json')
   disclose(out,'生成：M1显式保守策略 max/none/none/none；用于消费试跑，非质量矩阵')
   a=['llvm-profgen','--ip-samples','--binary='+str(binary),'--debug-binary='+str(debug),'--perfscript='+str(p/'perfscript.txt'),'--perf-buildid-list='+str(p/'buildid-list.txt'),'--binary-match-regex=^'+re.escape(B+'/variants/m1p-base/lib/'+real)+'$','--ip-event=cycles','--ip-weight=period','--ip-period-unit=1000003','--ip-aggregation=max','--ip-skid=none','--ip-zero-fill=none','--ip-head-samples=none','--format=extbinary','--output='+str(out),'--quality-report='+str(q)]
   llvm('convert-'+dso+'-'+str(i),a)
   report=json.loads(q.read_text());assert report['verdict']['conversion']=='ok' and report['verdict']['identity']=='verified',report['verdict']
   summary.append(dict(dso=dso,run=i,sha256=sha(out),verdict=report['verdict'],samples=report['samples']));save('summary.json',summary);profiles.append(out)
  target=D/(dso+'-merged.extbinary')
  for p in profiles:disclose(p,'按DSO合并3个训练RUN（原始计数求和）')
  llvm('merge-'+dso,['llvm-profdata','merge','--sample','--extbinary','-o',str(target),*[str(p) for p in profiles]])
  disclose(target,'读取为文本：跨DSO函数/上下文同名冲突检查')
  llvm('text-'+dso,['llvm-profdata','merge','--sample','--text','-o',str(D/(dso+'.txt')),str(target)]);merged.append(target)
 # Sample text top-level records include the complete inline subtree. Comparison excludes top-level name, compares entire counts/body.
 def entries(path):
  data={};key=None;lines=[]
  for l in path.read_text().splitlines():
   if l and not l[0].isspace() and not l.startswith('#'):
    if key is not None:data[key]='\n'.join(lines)
    key=l.rsplit(':',2)[0];lines=[l[len(key):]]
   elif key is not None:lines.append(l)
  if key is not None:data[key]='\n'.join(lines)
  return data
 a=entries(D/'libavcodec.txt');b=entries(D/'libavutil.txt');collision=[dict(name=k,identical=a[k]==b[k],codec=a[k],util=b[k]) for k in sorted(a.keys()&b.keys())]
 save('cross-dso-collisions.json',collision)
 assert not any(not x['identical'] for x in collision),'cross-DSO conflicting profiles'
 for p in merged:disclose(p,'跨DSO合并为锁定消费profile')
 locked=D/'autofdo.extbinary';llvm('merge-package',['llvm-profdata','merge','--sample','--extbinary','-o',str(locked),*[str(p) for p in merged]])
 save('locked-profile.json',dict(path=str(locked),sha256=sha(locked),time=datetime.datetime.now().astimezone().isoformat()))
 result['success']=True
except BaseException as e:result['success']=False;result['error']=repr(e)
finally:save('result.json',result)
print(json.dumps(result,indent=2))
