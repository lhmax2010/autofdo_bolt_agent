"""Live workflow orchestration. All board writes are journaled under /opt/afdo_agent."""
from pathlib import Path
import contextlib
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import tarfile
import time
from . import build,buildlock,config,profgen,consumption,stats,board,scheduler
from .common import TechnicalFailure,StopRequested,require,save,sha256,json_load,GateError
from .receipts import Cleanup,DAG
from .transport import SDB,q,board_path

def parse_cycles_event(text):
    """Validate one complete event; never match config1/bp_type substrings."""
    lines=[line.strip() for line in text.splitlines() if line.strip()]
    require(len(lines)==1,'expected exactly one perf event')
    name,sep,body=lines[0].partition(':')
    require(sep and name.strip()=='cycles','expected cycles event')
    fields={}
    for fragment in body.split(','):
        match=re.fullmatch(r"\s*([A-Za-z_][A-Za-z_0-9]*)\s*[:=]\s*(.*?)\s*",fragment)
        if not match or match[1] not in ['type','config']:continue
        key,value=match.groups()
        require(key not in fields,'duplicate perf field: '+key)
        integer=re.match(r"[+-]?(?:0[xX][0-9a-fA-F]+|[0-9]+)",value)
        require(integer is not None,'non-integer perf field: '+key)
        try:fields[key]=int(integer[0],0)
        except ValueError:require(False,'invalid perf integer: '+key)
    require(fields==dict(type=0,config=0),'hardware cycles type/config assertions failed')
    return dict(name='cycles',**fields)

def locate_build_source(scratch,log):
    """Resolve the source from the successful RPM trace, not a fixed RPM topdir."""
    roots=set(re.findall(r'^\[\s*[0-9]+s\] \+ cd (/[^\s]+/BUILD)$',log,re.M))
    require(len(roots)==1,'ambiguous or missing traced RPM build directory')
    directory=next(iter(roots));root=Path(scratch).resolve()
    path=(root/directory.lstrip('/')).resolve()
    require(path.is_relative_to(root) and '..' not in Path(directory).parts,'RPM build path escapes root')
    sources=[p for p in path.glob('ffmpeg-*') if p.is_dir() and (p/'ffbuild/config.mak').is_file()]
    require(len(sources)==1,'ambiguous build source')
    require(sources[0].resolve().is_relative_to(root),'build source escapes root')
    return sources[0]

def consumed_profile_path(commands):
    paths=set()
    for rows in commands.values():
        for argv in rows:
            for i,arg in enumerate(argv):
                if arg.startswith('-fprofile-sample-use='):paths.add(arg.split('=',1)[1])
                elif arg=='-fprofile-sample-use' and i+1<len(argv):paths.add(argv[i+1])
    require(len(paths)==1,'ambiguous or missing staged profile option')
    path=next(iter(paths))
    require(Path(path).is_absolute() and '..' not in Path(path).parts and Path(path).name=='autofdo.extbinary','unsafe staged profile path')
    return path

def caps_fields(text):
    """Interpret declared compact caps and GStreamer typed caps without dropping fields."""
    compact=re.fullmatch(r'([^,]+),(\d+)x(\d+),(\d+/\d+),([^,]+),(\d+/\d+)',text.strip())
    if compact:
        return dict(zip(['format','width','height','framerate','interlace-mode','pixel-aspect-ratio'],compact.groups()))
    parts=[x.strip() for x in text.split(',')]
    require(parts[0]=='video/x-raw','oracle caps media type mismatch')
    result={}
    for part in parts[1:]:
        match=re.fullmatch(r'([a-zA-Z0-9_-]+)=(?:\([^)]*\))?([^,; ]+)',part)
        require(match and match[1] not in result,'invalid or duplicate oracle caps field')
        result[match[1]]=match[2]
    require(all(k in result for k in ['format','width','height']),'required oracle caps fields missing')
    return result


def check_caps(expected,actual):
    a=caps_fields(actual);e=caps_fields(expected)
    for key,value in e.items():require(a.get(key)==value,'oracle caps mismatch '+key)
    return True


def capability_text(text):
    return text.rstrip('\n')+'\n'


def paired_block(order,run,failed):
    """Retry only predeclared technical failures, once, preserving the whole pair."""
    for attempt in range(2):
        pair={}
        try:
            for label in order:pair[label]=run(label,attempt)
            return pair
        except TechnicalFailure as e:
            failed(attempt,pair,e)
            if attempt:raise


def foreground_script(control,argv,env=None):
    """Wrapper records load status even on TERM; child scripts own their samplers."""
    return ('#!/bin/bash\nset -u\nchild=\nsampler=\n'
            'finish() { rc=$?; trap - EXIT; if test -n "$child"; then kill -TERM "$child" 2>/dev/null || :; wait "$child" 2>/dev/null || :; fi; '
            'if test -n "$sampler"; then kill -TERM "$sampler" 2>/dev/null || :; wait "$sampler" 2>/dev/null || :; fi; '
            'printf "%s\\n" "$rc" > '+q(control+'/exit')+'; }\n'
            'trap finish EXIT\ntrap "exit 143" TERM\ntrap "exit 130" INT\n'
            'printf "%s\\n" "$$" > '+q(control+'/pid')+'\n'+
            ''.join('export '+k+'='+q(v)+'\n' for k,v in (env or {}).items())+
            'if test -n "${WF_STANDALONE_SAMPLER:-}"; then taskset -c 0 bash "$WF_STANDALONE_SAMPLER" '+q(control+'/telemetry.tsv')+' "$WF_CAPABILITIES" & sampler=$!; sleep 1; fi\n'+
            shlex.join(list(map(str,argv)))+' & child=$!\nwait "$child"; rc=$?\nchild=\nif test -n "$sampler"; then sleep 2; fi\nexit "$rc"\n')

class Experiment:
    def __init__(self,job,job_path):
        self.job=job;self.job_path=Path(job_path).resolve();self.w=Path(job['workdir']).resolve()
        self.d=Path(job['output']).resolve();require(self.d.is_relative_to(self.w),'output boundary')
        self.d.mkdir(parents=True,exist_ok=True)
        self.package=config.load(job['package']);self.inputs=config.load_inputs(job['inputs'])
        self.serial=job['serial'];self.b='/opt/afdo_agent'
        self.remote=self.b+'/work/'+job['experiment']
        self.scripts=self.b+'/tools/workflow-'+job['experiment']
        self.transport=SDB(self.serial,self.d/('transport-'+str(time.time_ns())))
        self.cleanup=Cleanup(self.d/'cleanup.json',job['identity'])
        self.ops=0
    def host(self,argv,out,check=True,cwd=None,env=None):
        self.ops+=1;out=Path(out);out.mkdir(parents=True,exist_ok=True);base=out/('host-%04d'%self.ops)
        start=time.time();r=subprocess.run(list(map(str,argv)),capture_output=True,cwd=cwd,env=env)
        base.with_suffix('.stdout').write_bytes(r.stdout);base.with_suffix('.stderr').write_bytes(r.stderr)
        save(base.with_suffix('.json'),dict(argv=list(map(str,argv)),cwd=str(cwd),exit_code=r.returncode,start=start,end=time.time()))
        if check:require(r.returncode==0,'host command failed: '+str(base),'environment')
        return r
    def details(self,store,stage):return store.verify(stage)['details']
    def state(self):
        t=self.transport
        return dict(uid=t.shell('id -u',True).strip(),governors=t.governors(),
                    rpm_count=t.shell('rpm -qa | wc -l',True).strip(),
                    df=t.shell('df -Pk /opt/afdo_agent',True))
    @contextlib.contextmanager
    def session(self):
        t=self.transport
        devices=self.host(['sdb','devices'],self.d/'device-discovery').stdout.decode()
        require(any(line.startswith(self.serial+'\t') or line.startswith(self.serial+' ') for line in devices.splitlines()),'configured RPi4 is not online','environment')
        require(t.identity()==self.job['identity'],'board identity mismatch','identity',3)
        # Check all PATH tools before root; root-only deployed files are checked next.
        deps=['bash','cat','tr','uname','sed','mkdir','sha256sum','chmod','ldd','setsid','sleep','kill','date','awk','readlink','taskset','sort','grep','stat','mv','find','tar','wc','mkfifo','cut','head','tail','tee','rm','ps','gst-launch-1.0','rpm','df']
        t.shell('missing=0; for c in '+shlex.join(deps)+'; do command -v "$c" || missing=1; done; test "$missing" -eq 0',True)
        errors=self.cleanup.restore(t.identity(),t.undo);require(not errors,'pending cleanup failed: '+str(errors))
        self.initial=self.state();save(self.d/('initial-'+str(time.time_ns())+'.json'),self.initial)
        old={}
        def stop(signum,frame):raise StopRequested(signum)
        try:
            for s in [signal.SIGTERM,signal.SIGINT]:old[s]=signal.signal(s,stop)
            if self.initial['uid']!='0':
                self.cleanup.register(dict(kind='root',previous=False));t.root(True)
            for item in self.job['board_tools']:
                require(t.shell('sha256sum '+q(item['target']),True).split()[0]==item['sha256'],'board tool SHA mismatch','identity',3)
            t.shell('test -x '+q(self.b+'/tools/perf'),True)
            ldd=t.shell('LD_LIBRARY_PATH='+q(self.b+'/lib')+' ldd '+q(self.b+'/tools/perf'),True)
            require('not found' not in ldd,'perf runtime dependency missing')
            version=t.shell('LD_LIBRARY_PATH='+q(self.b+'/lib')+' '+q(self.b+'/tools/perf')+' --version',True)
            require(version.strip()=='perf version 6.12.80','perf version mismatch')
            for policy,value in self.initial['governors'].items():
                self.cleanup.register(dict(kind='governor',policy=policy,previous=value));t.governor(policy,'performance')
            yield
        finally:
            try:
                errors=self.cleanup.restore(t.identity(),t.undo)
                final=self.state()
                final.update(cleanup_pending=self.cleanup.data['cleanup_pending'],errors=errors,retries=t.retries)
                save(self.d/('final-'+str(time.time_ns())+'.json'),final)
                require(not errors and final['uid']==self.initial['uid'] and final['governors']==self.initial['governors'] and final['rpm_count']==self.initial['rpm_count'],'cleanup verification failed')
            finally:
                for s,h in old.items():signal.signal(s,h)
    def host_artifact(self,remote,members,directory=False):
        """Seal host originals and journal ownership before remote creation/push."""
        board_path(remote)
        records=self.d/'host-artifacts.json'
        registry=json_load(records) if records.exists() else {}
        if remote not in registry:
            self.transport.shell('test ! -e '+q(remote)+' && test ! -L '+q(remote),True)
        action=registry.get(remote,dict(kind='host_artifact',remote=remote,directory=directory,members={},
            verification=str(self.d/'host-cleanup'/ (hashlib.sha256(remote.encode()).hexdigest()+'.json'))))
        for name,member in members.items():
            require(name not in action['members'] or action['members'][name]==member,'host artifact changed: '+remote+'/'+name)
            action['members'][name]=member
        registry[remote]=action;save(records,registry)
        pending=next((x for x in self.cleanup.data['cleanup_pending'] if x.get('kind')=='host_artifact' and x['remote']==remote),None)
        if pending:pending.update(action);save(self.cleanup.path,self.cleanup.data)
        else:self.cleanup.register(action)
        return action

    def push_owned(self,local,remote):
        local=Path(local).resolve()
        if remote.startswith(self.scripts+'/'):
            self.host_artifact(self.scripts,{remote[len(self.scripts)+1:]:dict(kind='file',source=str(local),sha256=sha256(local))},True)
        else:self.host_artifact(remote,{'':dict(kind='file',source=str(local),sha256=sha256(local))})
        self.transport.push(local,remote)

    def ensure_work(self):
        self.register_run(self.remote,self.d/('remaining-work-'+str(time.time_ns())))
        self.transport.shell('mkdir -p '+q(self.remote))

    def restore_host_artifacts(self):
        """Rehydrate verified host artifacts after cleanup, without rerunning S0–S3."""
        records=self.d/'host-artifacts.json'
        if not records.exists():return
        for remote,action in json_load(records).items():
            self.transport.shell('test ! -e '+q(remote)+' && test ! -L '+q(remote),True)
            self.host_artifact(remote,action['members'],action['directory'])
            self.transport.shell('mkdir -p '+q(remote if action['directory'] else str(Path(remote).parent)))
            for name,item in action['members'].items():
                target=remote+('/'+name if name else '')
                if action['directory']:self.transport.shell('mkdir -p '+q(str(Path(target).parent)))
                if item['kind']=='file':
                    require(sha256(item['source'])==item['sha256'],'restore source changed')
                    self.transport.push(item['source'],target)
                else:self.transport.shell('test ! -e '+q(target)+' && test ! -L '+q(target)+' && ln -s '+q(item['target'])+' '+q(target))

    def launch(self,name,argv,out,env=None,timeout=600):
        """One foreground SDB shell owns the complete round, including cleanup."""
        free=int(self.transport.shell("df -Pk /opt/afdo_agent | tail -1 | awk '{print $4}'",True).strip())*1024
        require(free>=2*64*1024**2+200*1024**2,'board space gate failed')
        t=self.transport;control=self.remote+'/control-'+name;board_path(control,True)
        for remote,local,receipt in [(control,Path(out)/(name+'-control'),Path(out)/(name+'-control-pull.json')),
                                     (self.remote+'/'+name,Path(out)/name,Path(out)/(name+'.pull.json'))]:
            self.cleanup.register(dict(kind='run',remote=remote,local=str(local),receipt=str(receipt)))
        t.shell('test ! -e '+q(control)+' && mkdir -p '+q(control))
        script=Path(out)/(name+'-launch.sh')
        load_env=dict(env or {})
        if self.scripts+'/measure.sh' not in argv:
            load_env.update(WF_STANDALONE_SAMPLER=self.scripts+'/telemetry.sh',WF_CAPABILITIES=self.scripts+'/capabilities.tsv')
        script.write_text(foreground_script(control,argv,load_env))
        t.push(script,control+'/launch.sh')
        action=dict(kind='process',pidfile=control+'/pid',command_token=control+'/launch.sh',single_pid=True)
        self.cleanup.register(action)
        def observer():
            if 'injection' in self.job:
                active=t.shell('ps -eo pid,args | grep -F '+q(remote_token(self.remote,name))+' | grep "[p]erf stat" || test "$?" -eq 1',True)
                if active.strip():save(self.d/'injection-active.json',dict(active=True,processes=active,time=time.time()))
        old_hook=t.wait_hook;t.wait_hook=observer
        try:
            # No background operator: sdb remains attached until the entire script exits.
            t.shell('bash '+q(control+'/launch.sh')+' > '+q(control+'/stdout')+' 2> '+q(control+'/stderr')+' < /dev/null; _load_rc=$?; test -f '+q(control+'/exit'),timeout=timeout+120)
        except subprocess.TimeoutExpired as e:raise TechnicalFailure('foreground transport timeout: '+str(e)) from e
        except GateError as e:raise TechnicalFailure('foreground transport interrupted or missing exit: '+str(e)) from e
        finally:t.wait_hook=old_hook
        result=t.shell('cat '+q(control+'/exit'),True).strip()
        require(result.isdigit(),'remote task missing exit code')
        self.cleanup.data['cleanup_pending'].remove(action);save(self.cleanup.path,self.cleanup.data)
        t.pull(control,Path(out)/(name+'-control'),Path(out)/(name+'-control-pull.json'))
        if int(result)!=0:raise TechnicalFailure('board task failed '+name+' exit '+result)
    def register_run(self,remote,local):
        """Journal the exact pull destination before any remote mkdir or probe."""
        board_path(remote,True)
        receipt=Path(str(local)+'.pull.json')
        action=dict(kind='run',remote=remote,local=str(local),receipt=str(receipt))
        self.cleanup.register(action)
        return action

    def pull_run(self,remote,out):
        receipt=Path(str(out)+'.pull.json')
        self.cleanup.register(dict(kind='run',receipt=str(receipt)))
        result=self.transport.pull(remote,out,receipt)
        return Path(result['local_root'])
    def preflight(self,out,store):
        t=self.transport
        resources=build.resources(self.w);save(out/'host-resources.json',resources)
        for name,x in self.job['tools'].items():require(sha256(x['path'])==x['sha256'],'tool SHA '+name)
        self.ensure_work()
        self.host_artifact(self.scripts,{},True)
        t.shell('test -d '+q(self.b)+' && test -w '+q(self.b)+' && mkdir -p '+q(self.scripts))
        for f in (self.w/'workflow/board').glob('*.sh'):self.push_owned(f,self.scripts+'/'+f.name)
        for f in (Path(self.job['package']).parent/'workloads').glob('*.sh'):self.push_owned(f,self.scripts+'/'+f.name)
        for x in self.inputs:
            src=self.job['media'][x['id']]
            require(sha256(src)==x['sha256'],'input source SHA mismatch')
            existing=t.shell('if test -f '+q(x['path'])+'; then sha256sum '+q(x['path'])+'; else printf absent; fi',True)
            if existing=='absent':self.push_owned(src,x['path'])
            else:require(existing.split()[0]==x['sha256'],'existing input SHA mismatch')
        # Executability check and actual hardware-event probe after performance governor.
        t.shell('bash '+q(self.scripts+'/common.sh'))
        perf=self.b+'/tools/perf';remote=self.remote+'/cycles-check'
        self.register_run(remote,out/'cycles')
        t.shell('mkdir '+q(remote)+' && LD_LIBRARY_PATH='+q(self.b+'/lib')+' '+q(perf)+' record -e cycles -c 1000003 -o '+q(remote+'/perf.data')+' -- sleep 1')
        ev=t.shell('LD_LIBRARY_PATH='+q(self.b+'/lib')+' '+q(perf)+' evlist -v -i '+q(remote+'/perf.data'),True)
        (out/'cycles.evlist').write_text(ev)
        save(out/'cycles-assertions.json',parse_cycles_event(ev))
        self.pull_run(remote,out/'cycles')
        text=t.shell('for p in /sys/devices/system/cpu/cpufreq/policy*/scaling_cur_freq /sys/devices/system/cpu/cpufreq/policy*/cpuinfo_cur_freq; do test ! -r "$p" || printf "frequency\\t%s\\n" "$p"; done; for p in /sys/class/thermal/thermal_zone*/temp; do test ! -r "$p" || printf "temperature\\t%s\\n" "$p"; done; for p in /sys/class/hwmon/hwmon*/in0_lcrit_alarm; do test ! -r "$p" || printf "voltage\\t%s\\n" "$p"; done',True)
        cap={k:[] for k in ['frequency','temperature','voltage']}
        for line in text.splitlines():
            k,p=line.split();cap[k].append(p)
        require(cap['frequency'] and cap['temperature'],'telemetry frequency/temperature unavailable')
        cf=out/'capabilities.tsv';cf.write_text(capability_text(text));self.push_owned(cf,self.scripts+'/capabilities.tsv')
        values={p:int(t.shell('cat '+q(p),True)) for p in cap['frequency']}
        require(len(set(values.values()))==1,'fixed frequency differs between sources')
        return dict(identity=t.identity(),host_resources=resources,capabilities=cap,fixed_khz=next(iter(values.values())),throttle_history='unknown',inputs=self.inputs)
    def build_variant(self,variant,out,profile=None):
        j=self.job;unit=self.package['build_units'][0];macros=dict(unit['macros'])
        if profile:
            macros.update(unit['consume_macro']);macros.update(self.package['consumption']['diag_macro'])
            shutil.copyfile(profile,Path(j['source'])/unit['profile_staging'])
        root=self.d/'roots'/(variant+'-'+str(time.time_ns()))
        env=os.environ.copy();env.update(j['build_environment'])
        argv=build.command(j['config'],j['source'],root,unit,macros,j['repo'],j['buildconf'])
        r=build.execute(argv,j['source'],self.w,out/'execution',env,experiment=j['experiment'])
        require(r['status']=='success','GBS failure: '+str(out/'execution/result.json'),'environment')
        rpms=sorted(root.glob('local/repos/*/*/RPMS/*.rpm'))
        require(rpms,'no built RPMs')
        selected=[];inventory=[]
        for p in rpms:
            name=self.host(['rpm','-qp','--qf','%{NAME}',p],out).stdout.decode()
            inventory.append(dict(path=str(p),name=name,sha256=sha256(p),bytes=p.stat().st_size))
            if name in j['rpm_packages']:selected.append(p)
        save(out/'rpms.json',inventory)
        extracted=out/'extracted';build.extract_packages(selected,extracted)
        artifacts={}
        for target in self.package['targets']:
            runtime=(extracted/target['package_path']).resolve();debug=extracted/'usr/lib/debug'/str(runtime.relative_to(extracted.resolve()))
            artifacts[target['id']]=build.elf_manifest(runtime,str(debug)+'.debug',unit['isa'])
        scratch=root/'local/BUILD-ROOTS/scratch.armv7l.0';packages=build.rpm_manifest(scratch)
        require(packages==j['frozen_packages'],'frozen installed package/header list differs')
        src=locate_build_source(scratch,(out/'execution/build.log').read_text(errors='replace'))
        settings=buildlock.make_settings((src/'ffbuild/config.mak').read_text())
        commands={t:buildlock.recorded_switches(self.host(['readelf','-p','.GCC.command.line',a['debug_path']],out).stdout.decode()) for t,a in artifacts.items()}
        lock=dict(source_commit=self.package['package']['source']['commit'],patch_sha=sha256(j['patch']),
            spec_sha=sha256(Path(j['source'])/unit['spec']),source_layout='/'+str(src.relative_to(scratch)),
            frozen_repo_id=j['repo_id'],resolved_buildconf_sha=sha256(j['buildconf']),
            gbs_version=self.host(['gbs','--version'],out).stdout.decode().strip(),packages=packages,
            capture_method=self.package['command_capture']['method'],commands=commands,settings=settings,macros=macros,gbs_config_sha=sha256(j['config']))
        save(out/'build-lock.json',lock)
        text={}
        for t,a in artifacts.items():
            section=self.host(['readelf','-SW',a['path']],out).stdout.decode()
            m=re.search(r'\] \.text\s+PROGBITS\s+[0-9a-fA-F]+\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)',section)
            require(m,'ELF text section absent')
            with open(a['path'],'rb') as f:f.seek(int(m[1],16));text[t]=hashlib.sha256(f.read(int(m[2],16))).hexdigest()
        log=(out/'execution/build.log').read_text(errors='replace')
        diagnostics=[line for line in log.splitlines() if any(k in line.lower() for k in ['warning:','dwarf version 5','unknown debugging section'])]
        save(out/'diagnostics.json',diagnostics)
        return dict(variant=variant,execution=r,artifacts=artifacts,rpms=inventory,extracted=str(extracted),lock=lock,text=text,build_source=str(src),scratch=str(scratch))
    def build_base(self,out,store):return self.build_variant('BASE',out)
    def deploy_variant(self,result,out):
        variant=result['variant'];remote=self.b+'/variants/'+self.job['experiment']+'-'+variant
        root=Path(result['extracted']);manifest={}
        for pattern in self.package['runtime']['deploy_set']:
            for p in sorted(root.glob(pattern)):
                real=p.resolve();require(real.is_relative_to(root.resolve()),'deploy symlink escapes')
                name=p.name
                manifest[name]=dict(id=next((t for t,a in result['artifacts'].items() if real.name==a['real_name']),name.split('.so')[0]),
                    board_path=remote+'/'+str(real.relative_to(root.resolve())),sha256=sha256(real))
        archive=Path(out)/(variant+'.tar')
        with tarfile.open(archive,'w') as tar:
            for p in sorted((root/'usr/lib').glob('*.so*')):tar.add(p,arcname=str(p.relative_to(root)),recursive=False)
        self.push_owned(archive,self.remote+'/'+variant+'.tar')
        members={}
        for p in sorted((root/'usr/lib').glob('*.so*')):
            members[str(p.relative_to(root))]=(dict(kind='link',target=os.readlink(p)) if p.is_symlink() else dict(kind='file',source=str(p.resolve()),sha256=sha256(p)))
        self.host_artifact(remote,members,True)
        self.transport.shell('test ! -e '+q(remote)+' && mkdir -p '+q(remote)+' && tar -xf '+q(self.remote+'/'+variant+'.tar')+' -C '+q(remote))
        for item in manifest.values():
            require(self.transport.shell('sha256sum '+q(item['board_path']),True).split()[0]==item['sha256'],'deployed library SHA mismatch')
        mf=Path(out)/(variant+'-manifest.json');save(mf,manifest)
        self.push_owned(mf,self.scripts+'/'+variant+'-manifest.json')
        return dict(remote=remote,manifest=manifest)
    def verify_maps(self,local,deployment,input_path=None):
        manifest=deployment['manifest']
        if (local/'maps').exists():
            require(input_path is not None,'round input missing for decoder identity','identity',3)
            rule=json_load(Path(self.job['package']).parent/'workloads/decoder.json')
            return board.decoder_maps(local/'maps',manifest,self.package['runtime']['must_load'],self.package['runtime']['deploy_set'],rule,input_path)
        # Oracle directly records its own gst child; PLAT is checked separately.
        text=(local/'decoder.maps').read_text()
        hashes={line.split(None,1)[1].strip():line.split()[0] for line in (local/'mapped-sha256.txt').read_text().splitlines()}
        board.check_maps(text,manifest,self.package['runtime']['must_load'],self.package['runtime']['deploy_set'],hashes)
        return 1
    def oracle(self,name,x,deployment,out):
        remote=self.remote+'/'+name
        variant='PLAT' if deployment is None else deployment['remote']
        self.launch(name,['bash',self.scripts+'/watchdog.sh','600','bash',self.scripts+'/oracle.sh',remote,variant,x['path']],out)
        local=self.pull_run(remote,Path(out)/name)
        text=(local/'gst.log').read_text()
        caps=re.findall(r'GstIdentity:framecounter.GstPad:sink: caps = (.*)',text)
        require(caps,'negotiated oracle caps absent')
        actual=dict(status='ok',eos='Got EOS' in text,frames=int((local/'decoded.frames').read_text()),
            bytes=int((local/'decoded.bytes').read_text()),digest=(local/'decoded.sha256').read_text().split()[0],
            caps=caps[-1],threads=1)
        expected=x['oracle']
        actual['raw_caps']=actual['caps']
        check_caps(expected['caps'],actual['caps'])
        actual['caps']=expected['caps']
        board.oracle_check(expected,actual)
        if deployment:actual['maps_checked']=self.verify_maps(local,deployment)
        else:
            for libname in ['libavcodec.so','libavutil.so']:
                paths={l.split()[-1] for l in (local/'decoder.maps').read_text().splitlines() if libname in l}
                require(paths and all(p.startswith('/usr/lib/') for p in paths),'PLAT did not load system library')
        save(Path(out)/(name+'-oracle.json'),actual)
        return actual
    def deploy(self,out,store):
        base=self.details(store,'build');deployment=self.deploy_variant(base,out)
        oracles={}
        for x in self.inputs:
            plat=self.oracle('PLAT-'+x['id'],x,None,out)
            actual=self.oracle('BASE-'+x['id'],x,deployment,out)
            board.oracle_check(plat,actual);oracles[x['id']]=plat
        return dict(deployment=deployment,oracles=oracles)
    def collect(self,out,store):
        deployment=self.details(store,'deploy')['deployment'];rows=[]
        x=next(x for x in self.inputs if x['role']=='train')
        for i in range(1,self.package['collect']['runs']+1):
            name='train-'+str(i);remote=self.remote+'/'+name
            self.transport.shell('bash '+q(self.scripts+'/start_gate.sh')+' '+q(self.scripts+'/capabilities.tsv')+' '+q(self.remote+'/'+name+'-temperature.log'))
            env=dict(LD_LIBRARY_PATH=deployment['remote']+'/usr/lib:'+self.b+'/lib',DEPLOY_MANIFEST=self.scripts+'/BASE-manifest.json')
            self.launch(name,['bash',self.scripts+'/collect.sh',remote,self.b+'/tools/perf',str(self.package['collect']['period']),str(self.package['runtime']['cpu_affinity']),'600','bash',self.scripts+'/timed.sh','train',deployment['remote'],x['path'],remote+'/result'],out,env)
            local=self.pull_run(remote,Path(out)/name)
            require(int((local/'collect.exit').read_text())==0,'collection exit')
            require('Got EOS' in (local/'collect.log').read_text(),'training EOS absent')
            self.verify_maps(local,deployment,x['path'])
            cross=board.check_perf_buildids((local/'buildid-list.txt').read_text(),self.details(store,'build')['artifacts'],deployment['manifest'])
            save(local/'perf-buildid-check.json',cross)
            # Independently repeat untimed correctness; timed/perf run remains fakesink.
            self.oracle(name+'-correctness',x,deployment,out)
            rows.append(dict(id=name,local=str(local)))
        return dict(runs=rows)
    def convert(self,out,store):
        collection=self.details(store,'collect');base=self.details(store,'build');deployment=self.details(store,'deploy')['deployment']
        runs=[];disclosure=[]
        for row in collection['runs']:
            for target,a in base['artifacts'].items():
                artifact={**a,'board_path':next(x['board_path'] for x in deployment['manifest'].values() if x['id']==target)}
                profile=out/(row['id']+'-'+target+'.extbinary');quality=profile.with_suffix('.quality.json')
                disclosure.append(dict(object=str(profile),time=time.time(),purpose='workflow training conversion and consumption; no quality matrix'))
                save(out/'Q5-17.json',disclosure)
                args=profgen.command(self.job['profgen'],artifact,Path(row['local'])/'perf.script',Path(row['local'])/'buildid-list.txt',profile,quality,self.package['collect']['period_unit'])
                def runner(argv,**kwargs):
                    child=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                    save(self.d/'conversion-active.json',dict(pid=child.pid,time=time.time(),argv=argv))
                    try:
                        stdout,stderr=child.communicate()
                    except BaseException:
                        child.terminate()
                        try:child.wait(timeout=10)
                        except subprocess.TimeoutExpired:child.kill();child.wait()
                        raise
                    return subprocess.CompletedProcess(argv,child.returncode,stdout,stderr)
                r=profgen.convert(args,profile,quality,runner=runner)
                runs.append(dict(**r,path=str(profile),dso=target,merge_key=[self.job['repo_id'],'thumb',target,'cycles','period',self.package['collect']['period_unit'],'max/none/none/none']))
                save(out/'conversions.json',runs)
        lock=profgen.merge(self.job['profdata'],runs,out/'autofdo.extbinary',out/'merge')
        return dict(profile=str(out/'autofdo.extbinary'),lock=lock,quality=[r['quality'] for r in runs])
    def rebuild(self,out,store):
        base=self.details(store,'build');converted=self.details(store,'convert')
        repeat_dir=out/'BASE-r';repeat_dir.mkdir();repeat=self.build_variant('BASE-r',repeat_dir)
        candidate_dir=out/'AFDO';candidate_dir.mkdir();candidate=self.build_variant('AFDO',candidate_dir,converted['profile'])
        comparisons={label:buildlock.compare(base['lock'],v['lock']) for label,v in [('BASE-r',repeat),('AFDO',candidate)]}
        save(out/'buildlock.json',comparisons);require(all(x['passed'] for x in comparisons.values()),'build-lock gate failed')
        identity=lambda v:{t:{k:a[k] for k in ['sha256','debug_sha256','build_id']} for t,a in v['artifacts'].items()}
        control=buildlock.reproducible_control(identity(base),identity(repeat))
        src=Path(candidate['build_source']);remarks=[]
        for prefix in self.package['consumption']['object_to_target']:
            remarks.extend((str(p.relative_to(src)),str(p)) for p in (src/prefix).rglob('*.opt.yaml'))
        option_path=consumed_profile_path(candidate['lock']['commands'])
        staged=Path(candidate['scratch'])/option_path.lstrip('/')
        dependency_records=[];dependency_evidence=[]
        gcc=Path(candidate['scratch'])/'usr/lib/gcc'
        for dependency in sorted(gcc.rglob('*')):
            if dependency.name not in ['libgcc.a','libgcc_eh.a','crtbeginS.o','crtendS.o']:continue
            captured=self.host(['readelf','-p','.GCC.command.line',dependency],out)
            require(captured.returncode==0,'dependency command evidence failed')
            rows=buildlock.recorded_switches(captured.stdout.decode())
            dependency_records.extend(rows)
            dependency_evidence.append(dict(path=str(dependency),sha256=sha256(dependency),records=rows))
        source_commands,excluded=consumption.target_source_commands(candidate['lock']['commands'],
            self.package['consumption']['object_to_target'],dependency_records)
        save(out/'consumption-command-provenance.json',dict(dependencies=dependency_evidence,
            excluded_support_records=excluded,source_command_counts={k:len(v) for k,v in source_commands.items()},
            build_lock_unmodified=True))
        c=consumption.evaluate(list(base['artifacts']),self.package['consumption']['object_to_target'],remarks,source_commands,
            converted['lock']['sha256'],staged,base['text'],candidate['text'],option_path)
        save(out/'consumption.json',c);require(c['passed'],'consumption gate failed')
        return dict(base_repeat=repeat,candidate=candidate,control=control,buildlock=comparisons,consumption=c,offline_reproducible=True)
    def timed(self,name,x,deployment,out,preflight):
        remote=self.remote+'/'+name
        env=dict(LD_LIBRARY_PATH=deployment['remote']+'/usr/lib:'+self.b+'/lib',
                 DEPLOY_MANIFEST=self.scripts+'/'+deployment['variant']+'-manifest.json')
        self.launch(name,['bash',self.scripts+'/measure.sh',remote,self.b+'/tools/perf',
            str(self.package['runtime']['cpu_affinity']),'0',self.scripts+'/capabilities.tsv','600',
            'bash',self.scripts+'/timed.sh',x['role'],deployment['remote'],x['path'],remote+'/result'],out,env,timeout=1200)
        local=self.pull_run(remote,Path(out)/name)
        require(int((local/'measure.exit').read_text())==0,'timed exit')
        require('Got EOS' in (local/'measure.log').read_text(),'timed EOS absent')
        maps=self.verify_maps(local,deployment,x['path'])
        # Bash time writes a final numeric line after any perf diagnostics.
        wall=(local/'wall.txt').read_text().splitlines()
        require(wall and re.fullmatch(r'[0-9]+\.[0-9]+',wall[-1]),'wall timing missing')
        perf={}
        for line in (local/'perf-stat.csv').read_text().splitlines():
            fields=line.split(';')
            if len(fields)>=3 and fields[2].strip() in ['task-clock','cycles','instructions']:
                perf[fields[2].strip()]=float(fields[0])
        require(set(perf)=={'task-clock','cycles','instructions'} and all(x>0 for x in perf.values()),'perf counters missing')
        start=float((local/'start.monotonic').read_text());end=float((local/'end.monotonic').read_text())
        telemetry=stats.telemetry(stats.parse_telemetry_tsv((local/'telemetry.tsv').read_text()),start,end,
                                  preflight['fixed_khz'],preflight['capabilities'])
        row=dict(name=name,wall_seconds=float(wall[-1]),perf=perf,telemetry=telemetry,maps_checked=maps,
                 start=start,end=end,local=str(local),variant=deployment['variant'])
        save(Path(out)/(name+'-row.json'),row)
        return row
    def measure(self,out,store):
        rebuilt=self.details(store,'rebuild');base=self.details(store,'build');preflight=self.details(store,'preflight')
        deployment=self.details(store,'deploy')['deployment'];deployment['variant']='BASE'
        candidate=self.deploy_variant(rebuilt['candidate'],out);candidate['variant']='AFDO'
        if rebuilt['control']=='BASE-r':
            deployment=self.deploy_variant(rebuilt['base_repeat'],out);deployment['variant']='BASE-r'
        comparisons={};oracles={};rows=[]
        for label,dep in [('control',deployment),('candidate',candidate)]:
            for x in self.inputs:oracles['pre-'+label+'-'+x['id']]=self.oracle('pre-'+label+'-'+x['id'],x,dep,out)
        # Failure cleanup acceptance is an independent job and must finish before
        # this function creates any formal comparison plan.
        injection=self.failure_cleanup_test(out,preflight,deployment)
        tests=sorted((x for x in self.inputs if x['role'] in ['test','test-secondary']),key=lambda x:x['role']!='test')
        for ix,x in enumerate(tests):
            pilots=[]
            for i in range(10):
                pilots.append(self.timed('pilot-'+x['id']+'-'+str(i),x,deployment,out,preflight))
            n=stats.budget([r['wall_seconds'] for r in pilots])
            seed=self.job['order_seed']+ix;bootstrap_seed=self.job['bootstrap_seed']+ix
            plan=dict(input=x,control=deployment['variant'],candidate='AFDO',N=n,warmup=self.package['measure']['warmup'],
                      order=stats.order(n,seed),order_seed=seed,bootstrap_seed=bootstrap_seed,
                      epsilon=self.package['measure']['epsilon'],analysis_sha256=sha256(Path(stats.__file__)),
                      registered_time=time.time(),primary=x['role']=='test',multiple_comparison_correction=False)
            planfile=out/(x['id']+'-plan.json');save(planfile,plan)
            save(out/(x['id']+'-plan-lock.json'),dict(sha256=sha256(planfile),time=time.time()))
            for warm in range(plan['warmup']):
                for label,dep in [('BASE',deployment),('AFDO',candidate)]:
                    self.timed('warm-'+x['id']+'-'+str(warm)+'-'+label,x,dep,out,preflight)
            blocks=[]
            for i,order in enumerate(plan['order'],1):
                checkpoint=list(self.cleanup.data['cleanup_pending'])
                def one(label,attempt):
                    dep=deployment if label=='BASE' else candidate
                    row=self.timed('formal-'+x['id']+'-'+str(i)+'-try'+str(attempt)+'-'+label,x,dep,out,preflight)
                    row.update(block=i,input=x['id'],attempt=attempt)
                    return row
                def failed(attempt,pair,error):
                    save(out/(x['id']+'-'+str(i)+'-failed-'+str(attempt)+'.json'),dict(attempt=attempt,partial=pair,error=str(error)))
                    require(self.transport.identity()==self.job['identity'],'identity changed during technical cleanup','identity',3)
                    actions=[a for a in self.cleanup.data['cleanup_pending'] if a not in checkpoint]
                    for a in sorted(reversed(actions),key=lambda a:0 if a['kind']=='process' else 1):
                        self.transport.undo(a);self.cleanup.data['cleanup_pending'].remove(a);save(self.cleanup.path,self.cleanup.data)
                pair=paired_block(order,one,failed)
                rows.extend(pair.values());save(out/'rounds.json',rows)
                blocks.append(dict(id=i,complete=True,correctness=True,control=pair['BASE']['wall_seconds'],candidate=pair['AFDO']['wall_seconds'],
                    control_flag=pair['BASE']['telemetry']['classification'],candidate_flag=pair['AFDO']['telemetry']['classification']))
                save(out/(x['id']+'-blocks.json'),blocks)
            result=stats.analyze(blocks,n,bootstrap_seed,plan['epsilon'])
            freq=stats.effective_frequency([dict(control=dict(cycles=next(r for r in rows if r['input']==x['id'] and r['block']==i and r['variant']==deployment['variant'])['perf']['cycles'],
                task_clock_ms=next(r for r in rows if r['input']==x['id'] and r['block']==i and r['variant']==deployment['variant'])['perf']['task-clock']),
                candidate=dict(cycles=next(r for r in rows if r['input']==x['id'] and r['block']==i and r['variant']=='AFDO')['perf']['cycles'],
                task_clock_ms=next(r for r in rows if r['input']==x['id'] and r['block']==i and r['variant']=='AFDO')['perf']['task-clock'])) for i in range(1,n+1)])
            comparisons[x['id']]=dict(plan=plan,pilots=pilots,statistics=result,effective_frequency=freq)
            save(out/'comparisons.json',comparisons)
        for label,dep in [('control',deployment),('candidate',candidate)]:
            for x in self.inputs:oracles['post-'+label+'-'+x['id']]=self.oracle('post-'+label+'-'+x['id'],x,dep,out)
        return dict(comparisons=comparisons,oracles=oracles,rounds=rows,injection=injection)
    def failure_cleanup_test(self,out,preflight,deployment):
        """A separate live process/session, never part of formal result receipts."""
        errors=[]
        for action in list(reversed(self.cleanup.data['cleanup_pending'])):
            if action['kind'] in ['root','governor']:
                try:
                    self.transport.undo(action);self.cleanup.data['cleanup_pending'].remove(action);save(self.cleanup.path,self.cleanup.data)
                except Exception as e:errors.append(str(e))
        require(not errors,'cannot restore state before independent cleanup test')
        child=dict(self.job)
        child.update(experiment=self.job['experiment']+'-cleanup-test',output=str(out/'injected-job'),
                     injection=dict(preflight=preflight,deployment=deployment,
                                    input=next(x for x in self.inputs if x['role']=='test')))
        childfile=out/'injection-job.json';save(childfile,child)
        log=out/'injection-driver.log';env=os.environ.copy()
        with log.open('w') as f:
            p=subprocess.Popen([os.sys.executable,'-m','afdo_wf','run','--job',str(childfile)],stdout=f,stderr=subprocess.STDOUT,env=env)
            killed=False;start=time.monotonic()
            try:
                while p.poll() is None:
                    progress=Path(child['output'])/'injection-active.json'
                    if progress.exists():
                        # The child writes this only after observing perf stat in
                        # its exclusively owned remote process tree.
                        require(json_load(progress)['active'] is True,'invalid injection trigger')
                        p.send_signal(signal.SIGTERM);killed=True;break
                    require(time.monotonic()-start<180,'failure injection trigger timeout')
                    time.sleep(.25)
                rc=p.wait(timeout=120)
            finally:
                if p.poll() is None:p.terminate();p.wait(timeout=120)
        require(killed and rc!=0,'injection did not interrupt measurement')
        finals=sorted((out/'injected-job').glob('final-*.json'));require(finals,'injected cleanup evidence missing')
        final=json_load(finals[-1]);require(not final['cleanup_pending'] and not final['errors'],'injected cleanup incomplete')
        require(final['uid']==self.initial['uid'] and final['governors']==self.initial['governors'],'injected test did not restore original session state')
        if self.initial['uid']!='0':
            self.cleanup.register(dict(kind='root',previous=False));self.transport.root(True)
        for policy,value in self.initial['governors'].items():
            self.cleanup.register(dict(kind='governor',policy=policy,previous=value));self.transport.governor(policy,'performance')
        return dict(passed=True,exit_code=rc,final=final,job_sha256=sha256(childfile),separate_experiment=child['experiment'])
    def injected_run(self):
        data=self.job['injection'];out=self.d/'injection';out.mkdir(exist_ok=False)
        with self.session():
            self.ensure_work()
            self.host_artifact(self.scripts,{},True)
            self.transport.shell('mkdir -p '+q(self.scripts))
            for f in (self.w/'workflow/board').glob('*.sh'):self.push_owned(f,self.scripts+'/'+f.name)
            self.push_owned(Path(self.job['package']).parent/'workloads/timed.sh',self.scripts+'/timed.sh')
            cap=out/'capabilities.tsv';cap.write_text(''.join(k+'\t'+p+'\n' for k,v in data['preflight']['capabilities'].items() for p in v))
            self.push_owned(cap,self.scripts+'/capabilities.tsv')
            mf=out/'manifest.json';save(mf,data['deployment']['manifest'])
            self.push_owned(mf,self.scripts+'/'+data['deployment']['variant']+'-manifest.json')
            self.timed('injected-round',data['input'],data['deployment'],out,data['preflight'])
        require(False,'injection round completed without expected signal')
    def report(self,out,store):
        from . import report
        measured=self.details(store,'measure');rebuilt=self.details(store,'rebuild');converted=self.details(store,'convert')
        preflight=self.details(store,'preflight')
        primary=next(v for v in measured['comparisons'].values() if v['plan']['primary'])
        payload=dict(experiment_id=self.job['experiment'],build_lock=dict(passed=True,checks=rebuilt['buildlock']),
            board_identity=preflight['identity'],telemetry_manifest=preflight['capabilities'],tools=self.job['tools'],
            artifacts=rebuilt['candidate']['artifacts'],quality={str(i):dict(publishable=True,**r['verdict']) for i,r in enumerate(converted['quality'])},
            code_shares={'status':'diagnostic only'},consumption=rebuilt['consumption'],oracle=dict(passed=True,records=measured['oracles']),
            measurement_plan={k:v['plan'] for k,v in measured['comparisons'].items()},rounds=measured['rounds'],
            statistics=primary['statistics'],comparisons=measured['comparisons'],
            limitations=['One RPi4; single-threaded decode; ToS primary and Sintel secondary; no multiple-comparison correction; firmware throttle history unknown'],
            cleanup_pending=[])
        return report.write(out,payload)
    def run(self):
        if 'injection' in self.job:return self.injected_run()
        inputs=[self.job_path,self.job['package'],self.job['inputs'],self.job['patch']]
        inputs+=list((self.w/'workflow/afdo_wf').glob('*.py'))+list((self.w/'workflow/board').glob('*.sh'))
        inputs+=list((Path(self.job['package']).parent/'workloads').glob('*'))
        handlers=dict(preflight=self.preflight,build=self.build_base,deploy=self.deploy,collect=self.collect,
                      convert=self.convert,rebuild=self.rebuild,measure=self.measure,report=self.report)
        def progress(stage,status):
            save(self.d/'progress.json',dict(stage=stage,status=status,time=time.time(),pid=os.getpid()))
        result={'status':'failed','start':time.time()}
        try:
            with self.session():
                if (self.d/'receipts/preflight.json').exists():
                    from .receipts import Store
                    Store(self.d/'receipts').verify('preflight')
                    self.ensure_work();self.restore_host_artifacts()
                result['stages']=scheduler.execute([s for s in handlers if s!='report'],handlers,self.d/'stages',self.d/'receipts',inputs,progress)
            result['stages']+=scheduler.execute(['report'],handlers,self.d/'stages',self.d/'receipts',inputs,progress)
            result['status']='complete'
        except BaseException as e:
            result['error']=repr(e);raise
        finally:
            result.update(end=time.time(),cleanup_pending=self.cleanup.data['cleanup_pending'])
            save(self.d/('run-end-'+str(time.time_ns())+'.json'),result)

def remote_token(base,name):return base+'/'+name+'/'
