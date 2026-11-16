from pathlib import Path
import subprocess,json,difflib,os
w=Path(__file__).resolve().parents[2];d=Path(__file__).parent;out=d/'parse-tizen';out.mkdir()
r=w/'temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0'
env=os.environ.copy();env.update(RPM_CONFIGDIR=str(r/'usr/lib/rpm'),HOME=str(r/'home/abuild'))
qf='%{NAME}\\n[%{REQUIRENAME} %{REQUIREFLAGS:depflags} %{REQUIREVERSION}\\n]---\\n'
summary={}
for spec,arches in [('llvm-tools-subpkgs.spec',['x86_64','aarch64','armv7l','i586']),('llvm.spec',['x86_64','armv7l'])]:
 for arch in arches:
  for side in (['before','after'] if spec=='llvm.spec' else ['after']):
   p=(w/'docs/reviews/gerrit/361624'/spec) if side=='before' else d/'source/packaging'/spec
   mac=':'.join(str(r/x) for x in ['usr/lib/rpm/macros','usr/lib/rpm/macros.d/macros.*',f'usr/lib/rpm/platform/{arch}-linux/macros','usr/lib/rpm/fileattrs/*.attr','usr/lib/rpm/tizen/macros','etc/rpm/macros.*','etc/rpm/macros','home/abuild/.rpmmacros'])
   base=[str(r/'lib64/ld-linux-x86-64.so.2'),'--library-path',str(r/'usr/lib64')+':'+str(r/'lib64'),str(r/'usr/bin/rpmspec'),'--target',arch+'-tizen-linux','--macros',mac,'--define','_build_create_debug 1']
   key=spec+'-'+arch+'-'+side;results={}
   for mode,args in [('expanded',['-P']),('packages',['-q','--qf',qf]),('buildrequires',['-q','--srpm','--qf',qf])]:
    argv=base+args+[str(p)];z=subprocess.run(argv,env=env,capture_output=True,text=True)
    (out/(key+'-'+mode+'.stdout')).write_text(z.stdout);(out/(key+'-'+mode+'.stderr')).write_text(z.stderr)
    results[mode]=dict(argv=argv,environment={k:env[k] for k in ['RPM_CONFIGDIR','HOME']},exit=z.returncode,stdout=key+'-'+mode+'.stdout',stderr=key+'-'+mode+'.stderr')
   (out/(key+'.json')).write_text(json.dumps(results,indent=2)+'\n')
   text=(out/(key+'-expanded.stdout')).read_text()
   summary[key]={'exit':{k:v['exit'] for k,v in results.items()},'selected_lines':[line for line in text.splitlines() if any(x in line for x in ['LLVM_TARGETS_TO_BUILD=','BOLT_TARGETS_TO_BUILD=','LLVM_LIBDIR_SUFFIX=','ExclusiveArch:'])]}
for arch in ['x86_64','armv7l']:
 for mode in ['expanded','packages','buildrequires']:
  b=out/f'llvm.spec-{arch}-before-{mode}.stdout';a=out/f'llvm.spec-{arch}-after-{mode}.stdout'
  diff=''.join(difflib.unified_diff(b.read_text().splitlines(True),a.read_text().splitlines(True),fromfile=b.name,tofile=a.name))
  (out/f'llvm.spec-{arch}-{mode}.diff').write_text(diff)
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
