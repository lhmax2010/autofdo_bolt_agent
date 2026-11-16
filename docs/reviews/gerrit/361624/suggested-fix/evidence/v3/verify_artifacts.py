from pathlib import Path
import subprocess,json,hashlib,shutil,sys,os,re,traceback
D=Path(__file__).resolve().parent;W=D.parents[1]
sys.path.insert(0,str(W/'workflow'))
from afdo_wf.build import extract_packages
R=D/'root-x86_64/local/BUILD-ROOTS/scratch.x86_64.0';O=D/'verification';O.mkdir(exist_ok=False)
records=[];result={'status':'failed','checks':{}}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def run(name,args,expected=0):
 z=subprocess.run(list(map(str,args)),capture_output=True,text=True)
 (O/(name+'.stdout')).write_text(z.stdout);(O/(name+'.stderr')).write_text(z.stderr)
 records.append({'name':name,'argv':list(map(str,args)),'exit':z.returncode})
 (O/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
 if expected is not None and z.returncode!=expected:raise RuntimeError(name+' exit '+str(z.returncode))
 return z
def rootrun(name,args,expected=0):return run(name,['sudo','-n','chroot',R,*args],expected)
def bid(p):
 z=run('build-id-'+str(len(records)),['readelf','-n',p]);v=re.findall(r'Build ID:\s*([0-9a-f]+)',z.stdout)
 assert len(v)==1 and len(v[0])==40,(p,v)
 return v[0]
try:
 assert json.loads((D/'build-authorized/result.json').read_text())['status']=='success'
 rpms=sorted((D/'root-x86_64/local/repos').glob('*/x86_64/RPMS/*.rpm'));assert rpms
 rows=[];bolt=None
 for i,p in enumerate(rpms):
  name=run('rpm-name-'+str(i),['rpm','-qp','--qf','%{NAME}',p]).stdout.strip()
  listing=run('rpm-list-'+str(i),['rpm','-qpl',p]).stdout
  rows.append(dict(path=str(p),name=name,sha256=sha(p),bytes=p.stat().st_size))
  if name=='bolt':bolt=p;boltfiles=listing
 assert bolt
 for n in ['libbolt_rt_instr.a','libbolt_rt_hugify.a']:assert '/usr/lib64/'+n in boltfiles
 req=run('bolt-requires',['rpm','-qpR',bolt]).stdout
 assert 'libllvm = 22.1.8' in req and 'libLLVM.so.22.1(LLVM_22.1)' in req and not any(x.startswith('compiler-rt') for x in req.splitlines())
 result['checks']['rpm_requires_and_runtime_archives']=True
 (O/'rpms.json').write_text(json.dumps(rows,indent=2)+'\n')
 E=O/'extracted';extract_packages(rpms,E)
 debug={}
 for p in (E/'usr/lib/debug').rglob('*.debug'):
  if p.is_file() and not p.is_symlink():debug.setdefault(bid(p),[]).append(str(p))
 pairs=[]
 for p in (E/'usr/bin').iterdir():
  if not p.is_file() or p.is_symlink():continue
  with p.open('rb') as f:magic=f.read(4)
  if magic!=b'\x7fELF':continue
  identity=bid(p);assert identity in debug,p
  pairs.append(dict(runtime=str(p),sha256=sha(p),build_id=identity,debug=[dict(path=q,sha256=sha(q)) for q in debug[identity]]))
 assert len(pairs)==5
 assert any(Path(x['runtime']).name=='llvm-bolt' for x in pairs)
 result['checks']['runtime_debug_build_ids']=pairs
 result['checks']['GNU_RELRO']={}
 for row in pairs:
  z=run('relro-'+Path(row['runtime']).name,['readelf','-lW',row['runtime']])
  result['checks']['GNU_RELRO'][Path(row['runtime']).name]='GNU_RELRO' in z.stdout
 z=run('llvm-bolt-dwarf',['readelf','--debug-dump=info','--dwarf-depth=1',E/'usr/lib/debug/usr/bin/llvm-bolt.debug'])
 result['checks']['bolt_source_CU']='BinaryFunction.cpp' in z.stdout and '/bolt/lib/Core' in z.stdout
 source_listing=''.join((O/('rpm-list-'+str(i)+'.stdout')).read_text() for i,row in enumerate(rows) if row['name']=='llvm-tools-subpkgs-debugsource')
 result['checks']['debugsource_nonempty_bolt']='/bolt/' in source_listing and 'BinaryFunction.cpp' in source_listing

 stage=R/'home/abuild/verify-361624-v3';assert not stage.exists()
 rootrun('create-stage',['/bin/mkdir','/home/abuild/verify-361624-v3']);rootrun('own-stage',['/bin/chown',str(os.getuid())+':'+str(os.getgid()),'/home/abuild/verify-361624-v3'])
 inside='/home/abuild/verify-361624-v3'
 result['checks']['all_ldd_version']={}
 for row in pairs:
  name=Path(row['runtime']).name
  shutil.copy2(row['runtime'],stage/name);assert sha(stage/name)==row['sha256']
  z=rootrun('ldd-'+name,['/usr/bin/ldd',inside+'/'+name]);assert 'not found' not in z.stdout+z.stderr
  ver=rootrun('version-'+name,[inside+'/'+name,'--version'])
  result['checks']['all_ldd_version'][name]=dict(ldd_exit=z.returncode,version_exit=ver.returncode)
  if name=='llvm-bolt':version=ver.stdout
 assert re.search(r'^\s*aarch64\s+-',version,re.M) and re.search(r'^\s*x86-64\s+-',version,re.M)
 result['checks']['ldd_version']=True
 versions=list(R.glob('home/abuild/rpmbuild/BUILD/*/bolt-build/bolt-version.txt'));assert len(versions)==1
 shutil.copyfile(versions[0],O/'bolt-version.txt')
 log=(D/'build-authorized/build.log').read_text(errors='replace');provider=[x for x in log.splitlines() if 'LLVM provider Version-Release consistency check passed:' in x];assert provider
 result['provider_lines']=provider
 rootrun('installed-packages',['/usr/bin/rpm','-qa','--qf','%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}\n'])
 if not (R/'usr/bin/clang').exists() or not (R/'usr/bin/ld.lld').exists():result['smoke']='not performed: root clang or ld.lld missing'
 else:
  asm={'aarch64':'.text\n.globl _start\n.type _start,%function\n_start:\n bl answer\n mov x8,#93\n svc #0\n.size _start,.-_start\n.globl answer\n.type answer,%function\nanswer:\n mov x0,#7\n ret\n.size answer,.-answer\n','x86_64':'.text\n.globl _start\n.type _start,@function\n_start:\n call answer\n mov %eax,%edi\n mov $60,%eax\n syscall\n.size _start,.-_start\n.globl answer\n.type answer,@function\nanswer:\n mov $7,%eax\n ret\n.size answer,.-answer\n'}
  result['smoke']={}
  for arch,text in asm.items():
   (stage/(arch+'.S')).write_text(text);shutil.copyfile(stage/(arch+'.S'),O/(arch+'.S'))
   assert (stage/(arch+'.S')).read_bytes()==(W/'temp/verify-361624-fix-20261116/verification-smoke'/(arch+'.S')).read_bytes()
   a=inside+'/'+arch
   rootrun(arch+'-compile',['/usr/bin/clang','--target='+arch+'-linux-gnu','-c',a+'.S','-o',a+'.o'])
   rootrun(arch+'-link',['/usr/bin/ld.lld','-static','--emit-relocs','--build-id=sha1','-e','_start',a+'.o','-o',a+'.elf'])
   rootrun(arch+'-relocations',['/usr/bin/llvm-readelf','-r',a+'.elf'])
   z=rootrun(arch+'-bolt',[inside+'/llvm-bolt',a+'.elf','-o',a+'.bolt','-reorder-blocks=none','-reorder-functions=none'])
   rootrun(arch+'-disassembly',['/usr/bin/llvm-objdump','-d',a+'.bolt'])
   result['smoke'][arch]={'bolt_exit':0,'relocation_lines':[x for x in (z.stdout+z.stderr).splitlines() if 'reloc' in x.lower()],'input_sha256':sha(stage/(arch+'.elf')),'output_sha256':sha(stage/(arch+'.bolt'))}
   if arch=='x86_64':
    first=run('x86_64-run-original',[stage/(arch+'.elf')],7);second=run('x86_64-run-bolt',[stage/(arch+'.bolt')],7)
    result['smoke'][arch]['original_exit']=first.returncode;result['smoke'][arch]['rewritten_exit']=second.returncode
 result['status']='success' if all(result['checks']['GNU_RELRO'].values()) and result['checks']['bolt_source_CU'] and result['checks']['debugsource_nonempty_bolt'] else 'failed'
except BaseException as ex:
 result['error']=str(ex);(O/'failure.txt').write_text(traceback.format_exc())
finally:(O/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
raise SystemExit(0 if result['status']=='success' else 1)
