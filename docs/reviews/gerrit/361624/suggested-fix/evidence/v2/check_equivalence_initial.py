from pathlib import Path
import os,subprocess,json,difflib,hashlib,re,time
w=Path(__file__).resolve().parents[2];d=Path(__file__).parent;o=d/'parse';o.mkdir(exist_ok=False)
r=w/'temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0'
env=os.environ.copy();env.update(RPM_CONFIGDIR=str(r/'usr/lib/rpm'),HOME=str(r/'home/abuild'))
sources={'v1':w/'temp/verify-361624-fix-20261116/source/packaging/llvm-tools-subpkgs.spec','v2':d/'source/packaging/llvm-tools-subpkgs.spec'}
sha=lambda b:hashlib.sha256(b).hexdigest()
start=time.time();memory=Path('/proc/meminfo').read_text();assert int(re.search(r'MemAvailable:\s+(\d+)',memory)[1])*1024>=4*1024**3
(d/'meminfo-parse-start.txt').write_text(memory)
qf='%{NAME}\n[%{REQUIRENAME} %{REQUIREFLAGS:depflags} %{REQUIREVERSION}\n]---\n'
records=[];result={}
for arch in ['x86_64','aarch64']:
 mac=':'.join(str(r/x) for x in ['usr/lib/rpm/macros','usr/lib/rpm/macros.d/macros.*',f'usr/lib/rpm/platform/{arch}-linux/macros','usr/lib/rpm/fileattrs/*.attr','usr/lib/rpm/tizen/macros','etc/rpm/macros.*','etc/rpm/macros','home/abuild/.rpmmacros'])
 base=[str(r/'lib64/ld-linux-x86-64.so.2'),'--library-path',str(r/'usr/lib64')+':'+str(r/'lib64'),str(r/'usr/bin/rpmspec'),'--target',arch+'-tizen-linux','--macros',mac,'--define','_build_create_debug 1']
 values={}
 for side,p in sources.items():
  values[side]={}
  for mode,args in [('expanded',['-P']),('packages',['-q','--qf','%{NAME}\n']),('buildrequires',['-q','--srpm','--qf',qf]),('bolt-requires',['-q','--qf',qf])]:
   tag=arch+'-'+side+'-'+mode;argv=base+args+[str(p)];z=subprocess.run(argv,env=env,capture_output=True)
   (o/(tag+'.stdout')).write_bytes(z.stdout);(o/(tag+'.stderr')).write_bytes(z.stderr)
   rec=dict(argv=argv,environment={k:env[k] for k in ['RPM_CONFIGDIR','HOME']},exit=z.returncode,stdout=tag+'.stdout',stderr=tag+'.stderr',input_sha256=sha(p.read_bytes()))
   records.append(rec);(o/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
   assert z.returncode==0,(tag,z.stderr)
   data=z.stdout
   if mode=='bolt-requires':
    parts=[x for x in data.split(b'---\n') if x.startswith(b'bolt\n')];assert len(parts)==1,parts
    data=parts[0][len(b'bolt\n'):];(o/(tag+'.selected')).write_bytes(data);rec['selection']='exact package name bolt; remaining package records retained in stdout'
   values[side][mode]=data
  text=values[side]['expanded']
  for section,nextsection in [('build','install'),('install','files')]:
   match=re.search(rb'(?ms)^%'+section.encode()+rb'\b.*?(?=^%'+nextsection.encode()+rb'\b)',text);assert match,section
   values[side][section]=match[0];(o/(arch+'-'+side+'-'+section+'.expanded')).write_bytes(match[0])
  match=re.search(rb'(?ms)^%files\b.*\Z',text);assert match
  values[side]['files']=match[0];(o/(arch+'-'+side+'-files.expanded')).write_bytes(match[0])
 a,b=values['v1'],values['v2'];checks={}
 for mode in ['packages','buildrequires','bolt-requires','build','install','files']:
  assert a[mode]==b[mode],(arch,mode)
  checks[mode]=dict(equal=True,sha256=sha(a[mode]),bytes=len(a[mode]))
 diff=''.join(difflib.unified_diff(a['expanded'].decode().splitlines(True),b['expanded'].decode().splitlines(True),fromfile=arch+'-v1',tofile=arch+'-v2'));(o/(arch+'-expanded.diff')).write_text(diff)
 # Strip exactly the changed source comment block, not arbitrary comments.
 s1,s2=(sources[x].read_bytes() for x in ['v1','v2']);m=difflib.SequenceMatcher(a=s1.splitlines(True),b=s2.splitlines(True));ops=[x for x in m.get_opcodes() if x[0]!='equal'];assert len(ops)==1
 _,i,j,k,l=ops[0];old=b''.join(s1.splitlines(True)[i:j]);new=b''.join(s2.splitlines(True)[k:l]);assert all(x.startswith(b'#') for x in old.splitlines()+new.splitlines())
 assert a['expanded'].count(old)==1 and b['expanded'].count(new)==1
 assert a['expanded'].replace(old,new,1)==b['expanded'],arch
 checks['expanded_only_exact_comment_block']=True;result[arch]=checks
assert (w/'temp/verify-361624-fix-20261116/source/packaging/llvm.spec').read_bytes()==(d/'source/packaging/llvm.spec').read_bytes()
(o/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
(d/'equivalence.json').write_text(json.dumps(dict(arches=result,llvm_spec_unchanged=True,command_count=len(records),all_exit_zero=True),indent=2)+'\n')
cgroup=next(x.split(':',2)[2] for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::'));peak=Path('/sys/fs/cgroup'+cgroup)/'memory.peak'
(d/'resources.json').write_text(json.dumps(dict(start=start,end=time.time(),memory_peak=int(peak.read_text()),meminfo_start=memory,meminfo_end=Path('/proc/meminfo').read_text()),indent=2)+'\n')
print(json.dumps(result,indent=2))
