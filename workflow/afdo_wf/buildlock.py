"""Build-lock comparison; capture provenance cannot be inferred from warnings."""
from collections import Counter
import re
import shlex
from .common import require, sha256

DIAGNOSTICS=['-fsave-optimization-record=yaml','-foptimization-record-passes=sample-profile']

def normalize(argv, exact=DIAGNOSTICS, value_options=('-fprofile-sample-use',)):
    out=[];i=0
    while i<len(argv):
        arg=argv[i]
        if arg in exact:i+=1;continue
        if arg in value_options:
            require(i+1<len(argv),'missing candidate option value');i+=2;continue
        if any(arg.startswith(k+'=') for k in value_options):i+=1;continue
        out.append(arg);i+=1
    return tuple(out)

def recorded_switches(readelf_output):
    commands=[]
    for line in readelf_output.splitlines():
        m=re.match(r'\s*\[\s*[0-9a-fA-F]+\]\s+(.*)',line)
        if m:commands.append(shlex.split(m[1]))
    require(commands,'incomplete: no recorded commands')
    return commands

def make_settings(text):
    wanted={'CC','CFLAGS','ASFLAGS','LDFLAGS','SHFLAGS'};out={}
    text=text.replace('\\\n',' ')
    for line in text.splitlines():
        m=re.match(r'^(CC|CFLAGS|ASFLAGS|LDFLAGS|SHFLAGS)\s*(\+?[:?]?=)\s*(.*)$',line)
        if m:
            name,op,value=m.groups()
            if op=='+=':out.setdefault(name,[]).extend(shlex.split(value))
            else:out[name]=shlex.split(value)
    require(set(out)==wanted,'incomplete build settings')
    return out

def verbose_commands(text):
    """Only actual recipe lines; no shell reconstruction or guesses from CC foo.o."""
    commands=[]
    for line in text.splitlines():
        try:argv=shlex.split(line)
        except ValueError:continue
        if argv and re.fullmatch(r'(?:\S*/)?(?:clang(?:\+\+)?|gcc|g\+\+|cc|c\+\+|ld|ld.lld|ar)',argv[0]):
            require(not any(x in argv for x in ['&&',';','|']),'compound recipe needs explicit capture')
            commands.append(argv)
    require(commands,'incomplete: no verbose commands');return commands

def compare(control,candidate,exact=DIAGNOSTICS,value_options=('-fprofile-sample-use',),candidate_macros=('with_autofdo','afdo_diag')):
    diffs=[]
    required=['source_commit','patch_sha','spec_sha','source_layout','frozen_repo_id','resolved_buildconf_sha','gbs_version','packages','capture_method','commands','settings','macros','gbs_config_sha']
    for name in required:require(name in control and name in candidate,'incomplete lock: '+name)
    for name in required[:7]:
        if control[name]!=candidate[name]:diffs.append(name)
    if control['gbs_config_sha']!=candidate['gbs_config_sha']:diffs.append('gbs_config_sha')
    strip=lambda m:{k:v for k,v in m.items() if k not in candidate_macros}
    if strip(control['macros'])!=strip(candidate['macros']):diffs.append('macros')
    if sorted(control['packages'])!=sorted(candidate['packages']):diffs.append('packages')
    method=control['capture_method'];require(method==candidate['capture_method'],'capture method mismatch')
    require(method in ['recorded-switches','verbose-make'],'incomplete capture')
    if method=='verbose-make':
        for lock in [control,candidate]:
            require(lock.get('forensic_artifacts') and lock['forensic_artifacts']==lock.get('formal_artifacts'),'forensic artifact inequality')
    require(control['commands'] and set(control['commands'])==set(candidate['commands']),'incomplete per-target commands')
    for target in control['commands']:
        a=control['commands'][target];b=candidate['commands'][target];require(a and b,'empty target command evidence')
        collect=set if method=='recorded-switches' else Counter
        if collect(normalize(x,exact,value_options) for x in a)!=collect(normalize(x,exact,value_options) for x in b):diffs.append('commands:'+target)
    if method=='recorded-switches':
        for lock in [control,candidate]:require(set(lock['settings'])=={'CC','CFLAGS','ASFLAGS','LDFLAGS','SHFLAGS'},'incomplete settings')
    if {k:normalize(v,exact,value_options) for k,v in control['settings'].items()}!={k:normalize(v,exact,value_options) for k,v in candidate['settings'].items()}:diffs.append('settings')
    return dict(passed=not diffs,differences=diffs)

def reproducible_control(base,repeat):
    require(base.keys()==repeat.keys() and base,'artifact keys missing')
    return 'BASE' if base==repeat else 'BASE-r'
