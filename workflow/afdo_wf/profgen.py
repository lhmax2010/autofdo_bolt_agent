"""IP conversion, quality gates and collision-checked package-profile merge."""
from pathlib import Path
import re
import subprocess
from .common import require, json_load, sha256, save, finite_tree

POLICY=['--ip-aggregation=max','--ip-skid=none','--ip-zero-fill=none','--ip-head-samples=none']

def command(tool,artifact,perfscript,buildids,output,quality,period_unit,thresholds=None,allow_unverified=False):
    path=artifact['board_path'];require(path.startswith('/opt/afdo_agent/variants/') and '..' not in Path(path).parts,'untrusted board path')
    require(type(period_unit) is int and period_unit>0,'period unit')
    args=[*tool,'--ip-samples','--binary='+artifact['path'],'--debug-binary='+artifact['debug_path'],
          '--perfscript='+str(perfscript),'--perf-buildid-list='+str(buildids),'--binary-match-regex=^'+re.escape(path)+'$',
          '--ip-event=cycles','--ip-weight=period','--ip-period-unit='+str(period_unit),*POLICY,
          '--format=extbinary','--output='+str(output),'--quality-report='+str(quality)]
    for k,v in (thresholds or {}).items():
        require(k in ['min_usable_ratio','min_target_samples','max_lost_ratio'],'unknown threshold')
        args+=['--ip-'+k.replace('_','-')+'='+str(v)]
    if allow_unverified:args+=['--allow-missing-build-id']
    return args

def gate(exit_code,report,allow_unverified=False):
    finite_tree(report)
    require(exit_code==0,'profgen nonzero exit')
    v=report.get('verdict',{});require(v.get('conversion')=='ok','conversion failed')
    identity=v.get('identity');diagnostic=identity!='verified'
    require(identity=='verified' or (allow_unverified and identity in ['unverified','unverified_allowed']),'identity not verified','identity',3)
    for k,x in v.items():
        if k.endswith('_check'):require(x not in ['failed','fail'],'quality threshold failed: '+k)
    return dict(publishable=not diagnostic,identity=identity)

def convert(argv,output,quality,runner=subprocess.run,allow_unverified=False):
    p=runner(argv,capture_output=True,text=True)
    report=json_load(quality)
    result=gate(p.returncode,report,allow_unverified)
    require(Path(output).is_file(),'profile output absent')
    return dict(**result,argv=argv,exit_code=p.returncode,stderr=p.stderr,profile_sha256=sha256(output),quality=report)

def text_functions(text):
    """Parse llvm-profdata --sample --text output without flattening inline contexts.
    The entire top-level tree is compared, which also covers context bodies.
    """
    trees={};name=None;body=[]
    def commit():
        if name is not None:
            require(name not in trees,'duplicate top-level profile key');trees[name]='\n'.join(body)
    for line in text.splitlines():
        if not line.strip() or line.startswith('#'):continue
        if not line[0].isspace():
            commit();m=re.fullmatch(r'(.*):([0-9]+):([0-9]+)',line)
            require(m is not None,'unsupported sample text header: '+line)
            name=m[1];body=[line]
        else:
            require(name is not None,'orphan body');body.append(line)
    commit();require(trees,'empty profile');return trees

def collisions(by_dso):
    seen={};overlap=[]
    for dso,trees in by_dso.items():
        for key,body in trees.items():
            if key in seen:
                other,prev=seen[key];overlap.append(dict(key=key,dsos=[other,dso],identical=prev==body))
            else:seen[key]=(dso,body)
    require(all(x['identical'] for x in overlap),'cross-DSO bodies differ')
    return overlap

def merge(tool,runs,output,outdir,runner=subprocess.run):
    """Runs include an exact merge_key tuple (lock, ISA, DSO, event, weight, unit, policy)."""
    require(runs and all(len(r.get('merge_key',[]))==7 and r['merge_key'][2]==r['dso'] for r in runs),'complete seven-field merge key required')
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True);by_dso={};merged=[]
    for dso in sorted({r['dso'] for r in runs}):
        group=[r for r in runs if r['dso']==dso];key=group[0]['merge_key']
        require(all(r['merge_key']==key and r['publishable'] for r in group),'merge inputs incompatible/diagnostic')
        require(all(type(r.get('weight',1)) is int and r.get('weight',1)>0 for r in group),'merge weight')
        dest=outdir/(dso+'.extbinary');text=outdir/(dso+'.txt')
        for args in [
            [*tool,'merge','--sample','--extbinary',*[f"--weighted-input={r.get('weight',1)},{r['path']}" for r in group],'-o',str(dest)],
            [*tool,'merge','--sample','--text',str(dest),'-o',str(text)]]:
            p=runner(args,capture_output=True,text=True);require(p.returncode==0,'profdata merge failed: '+p.stderr)
        by_dso[dso]=text_functions(text.read_text());merged.append(str(dest))
    # Different DSOs may differ in identity, but all other collection policies must match.
    require(runs,'no merge inputs')
    policies=[tuple(r['merge_key'][:2])+tuple(r['merge_key'][3:]) for r in runs]
    require(all(p==policies[0] for p in policies),'cross-DSO collection policy mismatch')
    overlap=collisions(by_dso)
    p=runner([*tool,'merge','--sample','--extbinary',*merged,'-o',str(output)],capture_output=True,text=True)
    require(p.returncode==0,'package merge failed')
    lock=dict(sha256=sha256(output),order=merged,collisions=overlap,inputs=runs)
    save(outdir/'profile-lock.json',lock);return lock
