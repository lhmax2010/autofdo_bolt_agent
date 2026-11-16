from pathlib import Path
import json,re,shlex,hashlib
d=Path(__file__).resolve().parent;o=d/'flags';o.mkdir(exist_ok=False)
r=d/'root-x86_64/local/BUILD-ROOTS/scratch.x86_64.0'
b=r/'home/abuild/rpmbuild/BUILD/llvm-22.1.8/bolt-build'
log=d/'build-authorized/build.log';lines=log.read_text(errors='replace').splitlines()
lo=next(i for i,x in enumerate(lines) if 'Executing(%build)' in x)
hi=next((i for i,x in enumerate(lines[lo+1:],lo+1) if 'Executing(%install)' in x),len(lines))
values={};evidence={};checks={}
for name in ['CFLAGS','CXXFLAGS','LDFLAGS']:
 hits=[(i+1,x) for i,x in enumerate(lines[lo:hi],lo) if re.search(r'\+ '+name+'=',x)]
 exports=[i+1 for i,x in enumerate(lines[lo:hi],lo) if re.search(r'\+ export '+name+r'\b',x)]
 assert hits,(name,'assignment missing')
 n,line=hits[0];value=shlex.split(line.split('+ '+name+'=',1)[1]);assert len(value)==1
 values[name]=value[0];evidence[name]=dict(assignment_line=n,export_lines=exports,value=value[0]);checks[name+'_export']=bool(exports)
checks['debug_options']=all(x in shlex.split(values['CFLAGS']) for x in ['-g2','-gdwarf-4'])
def cache(path):
 data={}
 for i,x in enumerate(path.read_text().splitlines(),1):
  if re.match(r'CMAKE_(?:C_FLAGS|CXX_FLAGS|EXE_LINKER_FLAGS|SHARED_LINKER_FLAGS):',x):
   k,v=x.split('=',1);data[k.split(':')[0]]=dict(line=i,value=v)
 return data
c=cache(b/'CMakeCache.txt');rt=cache(b/'bolt_rt-bins/CMakeCache.txt')
checks['cache_CFLAGS_equal']=c['CMAKE_C_FLAGS']['value']==values['CFLAGS']
checks['cache_CXXFLAGS_equal']=c['CMAKE_CXX_FLAGS']['value']==values['CXXFLAGS']
for key in ['CMAKE_EXE_LINKER_FLAGS','CMAKE_SHARED_LINKER_FLAGS']:checks[key+'_equal']=c[key]['value']==values['LDFLAGS']+' -Wl,--build-id=sha1'
checks['bolt_rt_empty_C_CXX']=all(rt[x]['value']=='' for x in ['CMAKE_C_FLAGS','CMAKE_CXX_FLAGS'])
def snippet(path,needle,name):
 ls=path.read_text().splitlines();i=next(i for i,x in enumerate(ls) if x.startswith('build ') and needle in x);j=next((j for j in range(i+1,len(ls)) if ls[j].startswith('build ')),min(i+20,len(ls)))
 (o/name).write_text(''.join(f'{n+1}: {ls[n]}\n' for n in range(i,j)))
 flags=next(x.split('=',1)[1].strip() for x in ls[i:j] if x.strip().startswith('FLAGS ='))
 return dict(path=str(path),line=i+1,flags=flags)
rule=snippet(b/'build.ninja','BinaryFunction.cpp.o:','bolt-rule.txt')
rr=snippet(b/'bolt_rt-bins/build.ninja','instr.cpp.o:','bolt-rt-rule.txt')
tokens=shlex.split(rule['flags']);distribution=shlex.split(values['CXXFLAGS'])
checks['bolt_rule_distro_prefix']=tokens[:len(distribution)]==distribution
checks['bolt_rule_release_suffix']=tokens[len(distribution):len(distribution)+2]==['-O3','-DNDEBUG']
provider=[i+1 for i,x in enumerate(lines) if 'LLVM provider Version-Release consistency check passed: 22.1.8-4.1' in x]
checks['provider_log']=bool(provider)
version=b/'bolt-version.txt';v=version.read_text()
checks['version_targets']=bool(re.search(r'^\s*aarch64\s+-',v,re.M) and re.search(r'^\s*x86-64\s+-',v,re.M))
greps=[dict(line=i+1,text=x) for i,x in enumerate(lines) if '+ grep -Eq ' in x and 'bolt-version.txt' in x];checks['two_target_greps']=len(greps)==2
inputs=[log,b/'CMakeCache.txt',b/'build.ninja',b/'bolt_rt-bins/CMakeCache.txt',b/'bolt_rt-bins/build.ninja',version]
(o/'input-shas.json').write_text(json.dumps([dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in inputs],indent=2)+'\n')
result=dict(checks=checks,all_passed=all(checks.values()),exports=evidence,cache=c,runtime_cache=rt,bolt_rule=rule,runtime_rule=rr,provider_lines=provider,grep_lines=greps)
(o/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['all_passed'] else 1)
