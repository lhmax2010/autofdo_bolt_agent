"""Streaming reader for Clang YAML optimization records, not a general YAML loader.

Supported LLVM scalar/flow-map fields are validated. Unsupported relevant syntax
fails closed; arbitrary YAML tags, constructors and aliases are never evaluated.
"""
import re
from pathlib import PurePosixPath
from .common import require, sha256

def scalar(raw):
    raw=raw.strip()
    if len(raw)>=2 and raw[0]==raw[-1]=="'":return raw[1:-1].replace("''", "'")
    if raw.startswith('"'):
        import json
        return json.loads(raw)
    require(raw and raw[0] not in '&*!|>{[', 'unsupported remark scalar: '+raw)
    return raw

def records(path):
    """Yield the fields required for AppliedSamples; retain document index."""
    def parse(lines,index):
        fields={};args=[]
        for line in lines:
            m=re.match(r'^(Pass|Name|Function):\s*(.*?)\s*$',line)
            if m:
                require(m[1] not in fields,'duplicate remark field');fields[m[1]]=scalar(m[2])
            m=re.match(r'^DebugLoc:\s*\{\s*File:\s*(.+),\s*Line:\s*(\d+),\s*Column:\s*(\d+)\s*\}\s*$',line)
            if m:fields['DebugLoc']=dict(File=scalar(m[1]),Line=int(m[2]),Column=int(m[3]))
            m=re.match(r'^\s*-\s*NumSamples:\s*(.*?)\s*$',line)
            if m:args.append(scalar(m[1]))
        # LLVM's flow DebugLoc can wrap Column onto the next physical line.
        loc=re.search(r'^DebugLoc:\s*\{\s*File:\s*(.+),\s*Line:\s*(\d+),\s*Column:\s*(\d+)\s*\}', '\n'.join(lines), re.M)
        if loc:fields['DebugLoc']=dict(File=scalar(loc[1]),Line=int(loc[2]),Column=int(loc[3]))
        if fields.get('Name')=='AppliedSamples':
            require(fields.get('Pass') in ['sample-profile','sample-profile-impl'],'unexpected AppliedSamples pass')
            require(fields.get('Function') and fields.get('DebugLoc'),'incomplete application location')
            require(len(args)==1 and re.fullmatch(r'\d+',args[0]) is not None,'invalid NumSamples')
            fields['NumSamples']=int(args[0]);fields['document']=index
            return fields
        return None
    current=[];index=0;active=False
    with open(path) as f:
        for line in f:
            if line.startswith('---'):
                require(not active,'unterminated YAML document');active=True;current=[];index+=1
            elif line.strip()=='...':
                require(active,'orphan YAML end');r=parse(current,index)
                if r:yield r
                active=False;current=[]
            elif active:current.append(line.rstrip('\n'))
            else:require(not line.strip(),'text outside YAML document')
    require(not active,'truncated optimization record')

def target_for_object(path,mapping):
    p=PurePosixPath(path)
    require(not p.is_absolute() and '..' not in p.parts,'object path must be build-relative')
    matches=[target for prefix,target in mapping.items() if str(p).startswith(prefix.rstrip('/')+'/')]
    require(len(matches)==1,'ambiguous or absent object-to-target mapping: '+path)
    return matches[0]

def evaluate(targets,mapping,remark_files,commands,locked_sha,staged_profile,text_before,text_after,profile_option_path=None):
    require(sha256(staged_profile)==locked_sha,'chroot profile SHA mismatch')
    require(isinstance(profile_option_path,str) and profile_option_path.startswith('/'),'exact chroot option path required')
    found={t:[] for t in targets};counts={t:0 for t in targets}
    for object_path,path in remark_files:
        target=target_for_object(object_path,mapping)
        require(target in found,'unexpected target')
        for r in records(path):
            if r['NumSamples']>0:
                counts[target]+=1
                if len(found[target])<10:found[target].append(dict(object=object_path,remark_file=str(path),**r))
    output={}
    for t in targets:
        reasons=[];argvs=commands.get(t,[])
        def has_profile(argv):
            values=[a.split('=',1)[1] for a in argv if a.startswith('-fprofile-sample-use=')]
            values += [argv[i+1] for i,a in enumerate(argv[:-1]) if a=='-fprofile-sample-use']
            return values==[profile_option_path]
        if not argvs or not all(has_profile(a) for a in argvs):reasons.append('missing sample-use command')
        if counts[t]==0:reasons.append('no positive AppliedSamples')
        if not text_before.get(t) or not text_after.get(t) or text_before[t]==text_after[t]:reasons.append('no target text change')
        output[t]=dict(status='unverified' if reasons else 'verified',reasons=reasons,positive_records=counts[t],examples=found[t])
    return dict(passed=all(x['status']=='verified' for x in output.values()),targets=output,staged_sha256=locked_sha)
