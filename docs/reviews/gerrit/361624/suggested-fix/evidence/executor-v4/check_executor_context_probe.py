from pathlib import Path
import subprocess,os,json,re,hashlib,time
w=Path.cwd();d=Path(__file__).resolve().parent;o=d/'checks-final';o.mkdir(exist_ok=False)
r=w/'temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0'
env=os.environ.copy();env.update(RPM_CONFIGDIR=str(r/'usr/lib/rpm'),HOME=str(r/'home/abuild'))
mem=Path('/proc/meminfo').read_text();assert int(re.search(r'MemAvailable:\s+(\d+)',mem)[1])*1024>=4*1024**3
(d/'meminfo-start.txt').write_text(mem)
mac=':'.join(str(r/x) for x in ['usr/lib/rpm/macros','usr/lib/rpm/macros.d/macros.*','usr/lib/rpm/platform/x86_64-linux/macros','usr/lib/rpm/fileattrs/*.attr','usr/lib/rpm/tizen/macros','etc/rpm/macros.*','etc/rpm/macros','home/abuild/.rpmmacros'])
base=[str(r/'lib64/ld-linux-x86-64.so.2'),'--library-path',str(r/'usr/lib64')+':'+str(r/'lib64'),str(r/'usr/bin/rpm'),'--target','x86_64-tizen-linux','--macros',mac,'--define','_build_create_debug 1']
context=['--define','NAME llvm-tools-subpkgs','--define','VERSION 22.1.8','--define','RELEASE 1','--define','buildsubdir llvm-22.1.8','--define','buildroot /home/abuild/rpmbuild/BUILDROOT/llvm-tools-subpkgs-22.1.8-1.x86_64','--define','__debug_package 1','--define','_smp_mflags -j2']
records=[]
def cmd(tag,argv,inp=None):
 z=subprocess.run(argv,env=env,input=inp,capture_output=True)
 (o/(tag+'.stdout')).write_bytes(z.stdout);(o/(tag+'.stderr')).write_bytes(z.stderr)
 records.append(dict(tag=tag,argv=argv,environment={k:env[k] for k in ['RPM_CONFIGDIR','HOME']},exit=z.returncode))
 (o/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
 assert z.returncode==0,(tag,z.stderr)
 return z.stdout
# Preserve the entire installed Tizen definition, including optional install branch.
lines=(r/'usr/lib/rpm/tizen/macros').read_text().splitlines(True)
def raw_body(name):
 start=next(i for i,x in enumerate(lines) if x.startswith('%'+name+'\\'))
 parts=[lines[start][len(name)+1:].removesuffix('\n')]
 i=start+1
 while parts[-1].endswith('\\'):
  parts[-1]=parts[-1][:-1];parts.append(lines[i].removesuffix('\n'));i+=1
 return '\n'.join(parts),start+1,i
# Transport control characters through GBS without shell expansion; RPM expands them later.
def encode(s):
 return ''.join('%{lua:print(string.char('+str(ord(c))+'))}' if c in '\n\r\t"\'$`\\' else c for c in s)
suffix='\nninja() { command /usr/bin/ninja -j2 "$@"; }; export CMAKE_BUILD_PARALLEL_LEVEL=2\n'
args=[];bodies={}
for stage in ['build','install']:
 name='__spec_'+stage+'_pre';body,first,last=raw_body(name)
 bodies[stage]=dict(body=body,source=str(r/'usr/lib/rpm/tizen/macros'),lines=[first,last])
 args+=['--define',name+' '+encode(body+suffix)]
(d/'parameters.json').write_text(json.dumps(dict(arguments=args,original_bodies=bodies,append=suffix),indent=2)+'\n')
for extra,tag in [([], 'default'),(['--define','_enable_binutils_strip 1'],'strip-enabled')]:
 for stage in ['build','install']:
  macro='%{__spec_'+stage+'_pre}'
  original=cmd(tag+'-'+stage+'-original',base+context+extra+['--eval',macro])
  new=cmd(tag+'-'+stage+'-v4',base+context+extra+args+['--eval',macro])
  assert original.endswith(b'\n') and new==original[:-1]+suffix.encode()+b'\n',(tag,stage,'not prefix equivalent')
  if stage=='build':
   for flag in ['CFLAGS','CXXFLAGS','LDFLAGS']:assert ('export '+flag).encode() in new,flag
   cflags=re.search(rb'CFLAGS="([^\n]*)"',new)[1];assert re.search(rb'(?<!\S)-g(?:\d+)?(?!\S)',cflags),cflags
 # Correct quotes/$@ must survive even without a shell source file.
 assert b'ninja() { command /usr/bin/ninja -j2 "$@"; }' in new
# Full script reconstruction = native RPM template + cd buildsubdir + fully expanded spec section + native postlude.
spec=w/'temp/verify-361624-fix-v2-20261116/source/packaging/llvm-tools-subpkgs.spec'
parser=base.copy();parser[3]=str(r/'usr/bin/rpmspec')
expanded=cmd('spec-expanded',parser+context+args+['-P',str(spec)])
for stage,nextstage in [('build','install'),('install','files')]:
 body=re.search(rb'(?ms)^%'+stage.encode()+rb'[^\n]*\n(.*?)(?=^%'+nextstage.encode()+rb'\b)',expanded)[1]
 template=cmd(stage+'-template',base+context+args+['--eval','%{__spec_'+stage+'_template}'])
 post=cmd(stage+'-post',base+context+args+['--eval','%{__spec_'+stage+'_post}'])
 script=template+b"\ncd 'llvm-22.1.8'\n"+body+b'\n'+post+b'\n'
 path=o/(stage+'-full.sh');path.write_bytes(script)
 cmd(stage+'-syntax',['bash','-n',str(path)])
 assert set(re.findall(rb'%{[^}]+}',script)) <= {b'%{VERSION}',b'%{RELEASE}'},(stage,'unexpected unexpanded macro')
# Exercise only the added function with a synthetic command builtin, never run a full script or ninja.
test='command() { printf "<%s>\\n" "$@"; }\n'+suffix+'ninja bolt bolt_rt\nninja install\nninja "space arg" ""\n'
z=cmd('forwarding',['bash','--posix'],test.encode())
assert z==b'</usr/bin/ninja>\n<-j2>\n<bolt>\n<bolt_rt>\n</usr/bin/ninja>\n<-j2>\n<install>\n</usr/bin/ninja>\n<-j2>\n<space arg>\n<>\n'
(o/'forwarding.sh').write_text(test)
# Preserve executor command arguments through a POSIX shell round trip as GBS does; no GBS invocation.
import shlex
roundtrip='set -- '+shlex.join(args)+'; printf "%s\\0" "$@"'
z=cmd('shell-argument-roundtrip',['bash','--posix','-c',roundtrip]);assert z.split(b'\0')[:-1]==[x.encode() for x in args]
cg=next(x.split(':',2)[2] for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::'))
result=dict(prefix_equal_default=True,prefix_equal_strip_enabled=True,export_flags_preserved=True,cflags_has_debug_flag=True,full_scripts_syntax_pass=True,argument_forwarding=True,shell_argument_roundtrip=True,no_gbs_or_full_script_executed=True,memory_peak=int((Path('/sys/fs/cgroup'+cg)/'memory.peak').read_text()),meminfo_end=Path('/proc/meminfo').read_text())
(d/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
