from pathlib import Path
import os,sys,json
w=Path(__file__).resolve().parents[2];d=Path(__file__).parent
sys.path.insert(0,str(w/'workflow'))
from afdo_wf import build
env=os.environ.copy()
for k,v in dict(HOME=d/'home-retry',TMPDIR=d/'tmp-retry',TMP=d/'tmp-retry',TEMP=d/'tmp-retry',XDG_CACHE_HOME=d/'cache-retry',XDG_CONFIG_HOME=d/'config-retry',XDG_STATE_HOME=d/'state-retry',CCACHE_DIR=d/'cache-retry/ccache').items():env[k]=str(v)
env.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_COUNT='2',GIT_CONFIG_KEY_0='gc.auto',GIT_CONFIG_VALUE_0='0',GIT_CONFIG_KEY_1='maintenance.auto',GIT_CONFIG_VALUE_1='false',SUDO_ASKPASS='/bin/false',PYTHONDONTWRITEBYTECODE='1',CMAKE_BUILD_PARALLEL_LEVEL='2')
for k in ['V','MAKEFLAGS','MFLAGS']:env.pop(k,None)
argv=build.command(d/'gbs-retry.conf',d/'source',d/'root-x86_64-retry-executor',dict(arch='x86_64',spec='packaging/llvm-tools-subpkgs.spec'),{})
guard=json.loads((d/'resource-guard-v3.json').read_text())['value']
argv+=['--define','__spec_build_pre '+guard,'--define','__spec_install_pre '+guard]
(d/'planned-command-retry.json').write_text(json.dumps(dict(argv=argv,cwd=str(d/'source'),environment={k:env[k] for k in ['HOME','TMPDIR','XDG_CACHE_HOME','XDG_CONFIG_HOME','XDG_STATE_HOME','CCACHE_DIR','CMAKE_BUILD_PARALLEL_LEVEL']}),indent=2)+'\n')
# User temporary waiver: only the 16 GiB start-memory threshold.
build.can_start=lambda r: r['load1']<.6*r['nproc'] and r['disk_free']>=50*build.GIB
result=build.execute(argv,d/'source',w,d/'build-executor-retry',env,wait_seconds=172800)
print(json.dumps(result,indent=2),flush=True)
raise SystemExit(0 if result['status']=='success' else 1)
