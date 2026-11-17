"""Logged SDB transport: single-shot mutations and bounded read-only retries."""
from pathlib import Path
import re
import shlex
import subprocess
import time
import uuid
import json
from .common import require, save, sha256
from .receipts import verified_pull, delete_pulled

q=shlex.quote

def board_path(path,work=False):
    prefix="/opt/afdo_agent/work/" if work else "/opt/afdo_agent/"
    require(path.startswith(prefix) and ".." not in Path(path).parts,"unsafe board path")
    return q(path)

class SDB:
    def __init__(self,serial,logs,runner=subprocess.run):
        self.serial=serial;self.logs=Path(logs);self.logs.mkdir(parents=True,exist_ok=True)
        self.runner=runner;self.sequence=len(list(self.logs.glob("*.json")));self.retries=0;self.wait_hook=None
    def invoke(self,args,timeout=900):
        self.sequence+=1;stem=self.logs/("%06d"%self.sequence)
        argv=["sdb","-s",self.serial,*args];start=time.time()
        try:
            if self.wait_hook is None:
                r=self.runner(argv,capture_output=True,timeout=timeout)
            else:
                hook=self.wait_hook;self.wait_hook=None
                child=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                try:
                    while True:
                        remaining=timeout-(time.time()-start)
                        if remaining<=0:raise subprocess.TimeoutExpired(argv,timeout)
                        try:
                            stdout,stderr=child.communicate(timeout=min(1,remaining));break
                        except subprocess.TimeoutExpired:hook()
                    r=subprocess.CompletedProcess(argv,child.returncode,stdout,stderr)
                except BaseException:
                    child.terminate()
                    try:stdout,stderr=child.communicate(timeout=5)
                    except subprocess.TimeoutExpired:child.kill();stdout,stderr=child.communicate()
                    stem.with_suffix('.stdout').write_bytes(stdout);stem.with_suffix('.stderr').write_bytes(stderr)
                    raise
                finally:self.wait_hook=hook
            stdout=r.stdout.decode(errors="replace") if isinstance(r.stdout,bytes) else r.stdout
            stderr=r.stderr.decode(errors="replace") if isinstance(r.stderr,bytes) else r.stderr
            stem.with_suffix(".stdout").write_text(stdout);stem.with_suffix(".stderr").write_text(stderr)
            save(stem.with_suffix(".json"),dict(argv=argv,start=start,end=time.time(),exit_code=r.returncode))
            return r.returncode,stdout,stderr
        except BaseException as e:
            for suffix,raw in [('stdout',getattr(e,'stdout',None)),('stderr',getattr(e,'stderr',None))]:
                if raw is not None:stem.with_suffix('.'+suffix).write_bytes(raw if isinstance(raw,bytes) else raw.encode())
            save(stem.with_suffix(".json"),dict(argv=argv,start=start,end=time.time(),error=repr(e)))
            raise
    def shell(self,command,readonly=False,timeout=900):
        previous=None
        for attempt in range(3 if readonly else 1):
            marker="__WF_RC_"+uuid.uuid4().hex+"__"
            rc,out,err=self.invoke(["shell","( "+command+" ); _wf_rc=$?; printf "+q("\n"+marker+"%s\n")+" \"$_wf_rc\""],timeout)
            text=out.replace("\r\n","\n")
            matches=list(re.finditer(r"\n"+marker+r"([0-9]+)\n?\Z",text))
            body=text[:matches[-1].start()] if matches else text.rstrip("\n")
            if matches and rc==0:
                if previous is not None:require(body.rstrip("\n")==previous,"read-only retry changed output")
                require(int(matches[-1][1])==0,"remote command failed: "+body+err,"environment")
                return body
            require(readonly,"mutating command has no trusted exit status; no retry","environment")
            if previous is not None:require(body.rstrip("\n")==previous,"inconsistent read-only retries")
            previous=body.rstrip("\n")
            if attempt<2:self.retries+=1
        require(False,"read-only command has no exit marker after two retries","environment")
    def identity(self):
        return dict(model=self.shell("tr -d '\\000' < /proc/device-tree/model",True).strip(),
            arch=self.shell("uname -m",True).strip(),kernel=self.shell("uname -r",True).strip(),
            build_id=self.shell("sed -n 's/^TZ_BUILD_ID=//p' /etc/tizen-build.conf",True).strip().strip('"'))
    def root_state(self):return self.shell("id -u",True).strip()=="0"
    def root(self,on):
        rc,out,err=self.invoke(["root","on" if on else "off"])
        require(rc==0,"sdb root failed: "+out+err,"environment")
        require(self.root_state()==on,"root state verification failed","environment")
    def governors(self):
        text=self.shell("for p in /sys/devices/system/cpu/cpufreq/policy*; do test -d \"$p\" || continue; printf '%s ' \"$p\"; cat \"$p/scaling_governor\"; done",True)
        result=dict(line.split() for line in text.splitlines());require(result,"no governors")
        return result
    def governor(self,policy,value):
        require(re.fullmatch(r"/sys/devices/system/cpu/cpufreq/policy[0-9]+",policy),"unsafe policy")
        require(re.fullmatch(r"[a-zA-Z0-9_-]+",value),"unsafe governor")
        path=policy+"/scaling_governor"
        self.shell("printf '%s\\n' "+q(value)+" > "+q(path))
        require(self.shell("cat "+q(path),True).strip()==value,"governor verify failed")
    def push(self,local,remote):
        board_path(remote)
        rc,out,err=self.invoke(["push",str(local),remote])
        require(rc==0,"push failed: "+out+err)
        require(self.shell("sha256sum "+q(remote),True).split()[0]==sha256(local),"deployment SHA mismatch","identity",3)
    def remove_host_artifact(self,action):
        remote=action['remote'];board_path(remote)
        exists=self.shell('if test -e '+q(remote)+' || test -L '+q(remote)+'; then printf yes; else printf no; fi',True)
        if exists=='no':return
        expected=action['members']
        if action['directory']:
            raw=self.shell('cd '+q(remote)+" && find . -mindepth 1 -printf '%y\\t%P\\n' | sort",True)
            actual={line.split('\t',1)[1]:line.split('\t',1)[0] for line in raw.splitlines()}
        else:actual={'': 'f'}
        for rel,kind in actual.items():
            if kind=='d':
                require(any(k.startswith(rel+'/') for k in expected),'unexpected deployment directory '+rel);continue
            require(rel in expected,'unexpected deployment member '+rel)
            member=expected[rel];path=remote+('/'+rel if rel else '')
            if kind=='l':require(member['kind']=='link' and self.shell('readlink '+q(path),True).strip()==member['target'],'deployment link changed '+path)
            else:
                require(kind=='f' and member['kind']=='file','deployment member type changed '+path)
                require(sha256(member['source'])==member['sha256'],'host original changed '+path)
                require(self.shell('sha256sum '+q(path),True).split()[0]==member['sha256'],'deployment SHA changed '+path)
        save(action['verification'],dict(remote=remote,actual=actual,expected=expected,status='verified'))
        self.shell('rm -rf -- '+board_path(remote))

    def undo(self,action):
        kind=action['kind']
        if kind=='root':self.root(action['previous'])
        elif kind=='governor':self.governor(action['policy'],action['previous'])
        elif kind=='host_artifact':self.remove_host_artifact(action)
        elif kind=='run':
            receipt=Path(action['receipt'])
            # Unpulled data is never discarded during exception cleanup.
            if not receipt.exists():
                if 'remote' not in action:require(False,'unverified run has no cleanup metadata')
                exists=self.shell('if test -d '+board_path(action['remote'],True)+'; then printf yes; else printf no; fi',True)
                if exists=='no':return
                self.pull(action['remote'],action['local'],receipt)
                return
            delete_pulled(receipt,lambda path:self.shell("rm -rf -- "+board_path(path,True)))
        elif kind=='process':
            pidfile=action['pidfile'];board_path(pidfile,True)
            self.shell("if test -f "+q(pidfile)+"; then p=$(cat "+q(pidfile)+"); case \"$p\" in ''|*[!0-9]*) exit 2;; esac; if test -r /proc/$p/cmdline; then tr '\\000' ' ' < /proc/$p/cmdline | grep -F -- "+q(action['command_token'])+" >/dev/null || exit 3; kill -TERM -- "+("$p" if action.get('single_pid') else "-$p")+"; i=0; while kill -0 \"$p\" 2>/dev/null; do sleep 1; i=$((i+1)); test \"$i\" -lt 15 || exit 4; done; fi; fi")
        else:require(False,"unknown cleanup action")
    def pull(self,remote,local,receipt):
        board_path(remote,True);local=Path(local);require(not local.exists(),"pull destination already exists")
        command="cd "+q(remote)+" && find . -type f -exec sha256sum {} \\; | sort"
        manifest_text=self.shell(command,True);manifest={}
        for line in manifest_text.splitlines():
            digest,path=line.split(None,1);path=path.lstrip(' *')
            require(re.fullmatch('[0-9a-f]{64}',digest) and path.startswith('./'),"invalid SHA manifest")
            manifest[path[2:]]=digest
        local.mkdir(parents=True)
        for path in manifest:
            require((local/path).resolve().is_relative_to(local.resolve()),"unsafe pull member")
        rc,out,err=self.invoke(["pull",remote,str(local)])
        require(rc==0,"pull failed: "+out+err)
        actual={str(p.relative_to(local)):p for p in local.rglob('*') if p.is_file()}
        if set(actual)!=set(manifest):
            nested=local/Path(remote).name
            require(nested.is_dir(),"actual pull layout differs from manifest")
            actual={str(p.relative_to(nested)):p for p in nested.rglob('*') if p.is_file()}
            require(set(actual)==set(manifest),"nested pull has missing or extra files")
            local=nested
        require(set(actual)==set(manifest),"pull has missing or extra files")
        require(self.shell(command,True)==manifest_text,"remote changed during pull")
        verified_pull(receipt,local,manifest,remote,verified_empty=not manifest)
        delete_pulled(receipt,lambda path:self.shell("rm -rf -- "+board_path(path,True)))
        return dict(files=manifest,local_root=str(local))
