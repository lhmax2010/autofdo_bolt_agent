from pathlib import Path
import subprocess,json,hashlib,shutil,sys,os,re,traceback
D=Path(__file__).resolve().parent;W=D.parents[1]
sys.path.insert(0,str(W/'workflow'))
from afdo_wf.build import extract_packages
R=D/'root-x86_64-retry-executor/local/BUILD-ROOTS/scratch.x86_64.0';O=D/'verification-smoke';O.mkdir(exist_ok=False)
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
 result['checks']=json.loads((D/'verification/result.json').read_text())['checks']
 E=D/'verification/extracted';stage=R/'home/abuild/verify-361624'
 shutil.copy2(E/'usr/bin/llvm-bolt',stage/'llvm-bolt');assert sha(stage/'llvm-bolt')==sha(E/'usr/bin/llvm-bolt')
 inside='/home/abuild/verify-361624'
 z=rootrun('ldd',['/usr/bin/ldd',inside+'/llvm-bolt']);assert 'not found' not in z.stdout+z.stderr
 version=rootrun('version',[inside+'/llvm-bolt','--version']).stdout
 assert re.search(r'^\s*aarch64\s+-',version,re.M) and re.search(r'^\s*x86-64\s+-',version,re.M)
 result['checks']['ldd_version']=True
 versions=list(R.glob('home/abuild/rpmbuild/BUILD/*/bolt-build/bolt-version.txt'));assert len(versions)==1
 shutil.copyfile(versions[0],O/'bolt-version.txt')
 log=(D/'build-executor-retry/build.log').read_text(errors='replace');provider=[x for x in log.splitlines() if 'BOLT is built against LLVM provider' in x];assert provider
 result['provider_lines']=provider
 rootrun('installed-packages',['/usr/bin/rpm','-qa','--qf','%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}\n'])
 if not (R/'usr/bin/clang').exists() or not (R/'usr/bin/ld.lld').exists():result['smoke']='not performed: root clang or ld.lld missing'
 else:
  asm={'aarch64':'.text\n.globl _start\n.type _start,%function\n_start:\n bl answer\n mov x8,#93\n svc #0\n.size _start,.-_start\n.globl answer\n.type answer,%function\nanswer:\n mov x0,#7\n ret\n.size answer,.-answer\n','x86_64':'.text\n.globl _start\n.type _start,@function\n_start:\n call answer\n mov %eax,%edi\n mov $60,%eax\n syscall\n.size _start,.-_start\n.globl answer\n.type answer,@function\nanswer:\n mov $7,%eax\n ret\n.size answer,.-answer\n'}
  result['smoke']={}
  for arch,text in asm.items():
   (stage/(arch+'.S')).write_text(text);shutil.copyfile(stage/(arch+'.S'),O/(arch+'.S'))
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
 result['status']='success'
except BaseException as ex:
 result['error']=str(ex);(O/'failure.txt').write_text(traceback.format_exc())
finally:(O/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
raise SystemExit(0 if result['status']=='success' else 1)
