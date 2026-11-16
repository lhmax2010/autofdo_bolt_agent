from pathlib import Path
import os,sys,json
w=Path(__file__).resolve().parents[2];d=Path(__file__).parent
sys.path.insert(0,str(w/'workflow'))
from afdo_wf import build
assert json.loads((d/'preflight-result.json').read_text())['all_exit_zero']
env=os.environ.copy()
for k,v in dict(HOME=d/'home',TMPDIR=d/'tmp',TMP=d/'tmp',TEMP=d/'tmp',XDG_CACHE_HOME=d/'cache',XDG_CONFIG_HOME=d/'config',XDG_STATE_HOME=d/'state',CCACHE_DIR=d/'cache/ccache').items():env[k]=str(v)
env.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_COUNT='2',GIT_CONFIG_KEY_0='gc.auto',GIT_CONFIG_VALUE_0='0',GIT_CONFIG_KEY_1='maintenance.auto',GIT_CONFIG_VALUE_1='false',SUDO_ASKPASS='/bin/false',PYTHONDONTWRITEBYTECODE='1',CMAKE_BUILD_PARALLEL_LEVEL='2')
for k in ['V','MAKEFLAGS','MFLAGS','CFLAGS','CXXFLAGS','LDFLAGS']:env.pop(k,None)
argv=build.command(d/'gbs.conf',d/'source',d/'root-x86_64',dict(arch='x86_64',spec='packaging/llvm-tools-subpkgs.spec'),{})
argv+=json.loads((d/'executor-parameters.json').read_text())['arguments']
(d/'planned-command.json').write_text(json.dumps(dict(argv=argv,cwd=str(d/'source'),environment={k:env[k] for k in ['HOME','TMPDIR','XDG_CACHE_HOME','XDG_CONFIG_HOME','XDG_STATE_HOME','CCACHE_DIR','CMAKE_BUILD_PARALLEL_LEVEL']},gate=dict(mem_available_min_gib=16,load_per_cpu_max=0.6,disk_free_min_gib=50,timeout_seconds=1800),resource=dict(MemoryMax='6G',MemoryHigh='5G',CPUQuota='200%',ninja_jobs=2)),indent=2)+'\n')
original_stop=build.stop_needed
def stop(r,previous):
 low,needed=original_stop(r,previous)
 events=dict((x.split()[0],int(x.split()[1])) for x in r.get('memory.events','').splitlines())
 return low,needed or any(events.get(x,0)>0 for x in ['max','oom','oom_kill','oom_group_kill'])
build.stop_needed=stop
result=build.execute(argv,d/'source',w,d/'build',env,wait_seconds=1800)
events=dict((x.split()[0],int(x.split()[1])) for x in result.get('child',{}).get('memory_events','').splitlines())
accepted=result['status']=='success' and not any(events.get(x,0)>0 for x in ['max','oom','oom_kill','oom_group_kill'])
(d/'build/acceptance.json').write_text(json.dumps(dict(accepted=accepted,events=events,no_retry=True),indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)
raise SystemExit(0 if accepted else 1)
