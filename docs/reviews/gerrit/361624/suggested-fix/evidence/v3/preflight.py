from pathlib import Path
import json,subprocess,os,re,hashlib,difflib
w=Path.cwd();d=Path(__file__).resolve().parent;o=d/'parse-final';o.mkdir(exist_ok=False)
r=w/'temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0';env=os.environ.copy();env.update(RPM_CONFIGDIR=str(r/'usr/lib/rpm'),HOME=str(r/'home/abuild'))
qf='%{NAME}\n[%{REQUIRENAME} %{REQUIREFLAGS:depflags} %{REQUIREVERSION}\n]---\n';records=[];checks={}
def base(arch):
 mac=':'.join(str(r/x) for x in ['usr/lib/rpm/macros','usr/lib/rpm/macros.d/macros.*',f'usr/lib/rpm/platform/{arch}-linux/macros','usr/lib/rpm/fileattrs/*.attr','usr/lib/rpm/tizen/macros','etc/rpm/macros.*','etc/rpm/macros','home/abuild/.rpmmacros'])
 return [str(r/'lib64/ld-linux-x86-64.so.2'),'--library-path',str(r/'usr/lib64')+':'+str(r/'lib64'),str(r/'usr/bin/rpmspec'),'--target',arch+'-tizen-linux','--macros',mac,'--define','_build_create_debug 1']
def cmd(tag,args):
 z=subprocess.run(args,env=env,capture_output=True);(o/(tag+'.stdout')).write_bytes(z.stdout);(o/(tag+'.stderr')).write_bytes(z.stderr);records.append(dict(tag=tag,argv=args,environment={k:env[k] for k in ['HOME','RPM_CONFIGDIR']},exit=z.returncode));(o/'commands.json').write_text(json.dumps(records,indent=2)+'\n');assert z.returncode==0,(tag,z.stderr);return z.stdout
sources={'v2':w/'temp/verify-361624-fix-v2-20261116/source','v3':d/'source'}
for spec,arches in [('llvm-tools-subpkgs.spec',['x86_64','aarch64']),('llvm.spec',['x86_64','armv7l'])]:
 for arch in arches:
  values={}
  for side,src in sources.items():
   values[side]={}
   for mode,args in [('expanded',['-P']),('packages',['-q','--qf','%{NAME}\n']),('requires',['-q','--qf',qf]),('buildrequires',['-q','--srpm','--qf',qf])]:
    tag=spec+'-'+arch+'-'+side+'-'+mode;values[side][mode]=cmd(tag,base(arch)+args+[str(src/'packaging'/spec)])
  for mode in ['packages','requires','buildrequires']:assert values['v2'][mode]==values['v3'][mode],(spec,arch,mode)
  if spec=='llvm-tools-subpkgs.spec':
   for side in sources:
    bolt=[x for x in values[side]['requires'].split(b'---\n') if x.startswith(b'bolt\n')];assert len(bolt)==1;(o/(arch+'-'+side+'-bolt.requires')).write_bytes(bolt[0])
  delta=''.join(difflib.unified_diff(values['v2']['expanded'].decode().splitlines(True),values['v3']['expanded'].decode().splitlines(True)));(o/(spec+'-'+arch+'.diff')).write_text(delta)
  if spec=='llvm.spec':
   added=[x[1:] for x in delta.splitlines() if x.startswith('+') and not x.startswith('+++')];removed=[x for x in delta.splitlines() if x.startswith('-') and not x.startswith('---')];assert len(added)==3 and all(not x.strip() for x in added) and not removed
  checks[spec+'-'+arch]='packages, Requires and BuildRequires identical'
for arch in ['armv7l','i586']:
 text=cmd('tools-exclusive-'+arch,base(arch)+['-P',str(d/'source/packaging/llvm-tools-subpkgs.spec')]);line=re.search(rb'^ExclusiveArch:\s*(.+)$',text,re.M)[1];assert line.split()==[b'x86_64',b'aarch64'];checks['excluded-'+arch]=True
params=json.loads((w/'docs/reviews/gerrit/361624/suggested-fix/evidence/executor-v4/parameters.json').read_text());(d/'executor-parameters.json').write_text(json.dumps(params,indent=2)+'\n')
for stage in ['build','install']:
 orig=cmd(stage+'-pre-original',base('x86_64')+['--eval','%{__spec_'+stage+'_pre}'])
 new=cmd(stage+'-pre-v4',base('x86_64')+params['arguments']+['--eval','%{__spec_'+stage+'_pre}'])
 assert new==orig[:-1]+params['append'].encode()+b'\n',stage
 if stage=='build':
  for x in ['CFLAGS','CXXFLAGS','LDFLAGS']:assert ('export '+x).encode() in new
  assert b'-g2' in new and b'-gdwarf-4' in new
old=(sources['v2']/'packaging/llvm.spec').read_text().splitlines(True);new=(sources['v3']/'packaging/llvm.spec').read_text().splitlines(True)
delta=list(difflib.unified_diff(old,new))
added=[x[1:] for x in delta if x.startswith('+') and not x.startswith('+++')];removed=[x for x in delta if x.startswith('-') and not x.startswith('---')]
assert len(added)==3 and all(x.startswith('#') for x in added) and not removed
checks['llvm_source_only_three_added_comments']=True
checks['executor_v4_prefix_and_flags']=True
(d/'preflight-result.json').write_text(json.dumps(dict(checks=checks,commands=len(records),all_exit_zero=True),indent=2)+'\n');print(json.dumps(checks,indent=2))
