"""Closed schema v1. No string commands or implicit TOML coercion."""
from pathlib import Path, PurePosixPath
import re
import tomllib
from .common import require, positive, finite_tree, json_load

FIELDS = {
    '': {'schema_version','package','build_units','targets','runtime','collect','identity','consumption','command_capture','measure'},
    'package': {'name','owner','source'},
    'source': {'gerrit','commit'},
    'build_units': {'id','spec','patch','arch','isa','macros','consume_macro','profile_staging'},
    'targets': {'id','build_unit','package_path','thresholds'},
    'thresholds': {'min_usable_ratio','min_target_samples','max_lost_ratio'},
    'runtime': {'deploy_set','must_load','env','plugin_dirs','cpu_affinity','timeout_s'},
    'collect': {'event','period','freq','runs','period_unit','min_target_share','rpi4','rpi5'},
    'identity': {'allow_unverified_identity'},
    'consumption': {'diag_macro','object_to_target','record_coverage_warn_percent','sample_coverage_warn_percent','fail_on_coverage_warning'},
    'command_capture': {'method','build_config_files'},
    'measure': {'metric','better','warmup','blocks','epsilon'},
}

def keys(obj, field, required=()):
    require(isinstance(obj, dict), field+' must be a table')
    require(not set(obj)-FIELDS[field], field+': unknown keys '+str(set(obj)-FIELDS[field]))
    require(set(required)<=set(obj), field+': missing keys '+str(set(required)-set(obj)))

def relative(path):
    require(isinstance(path,str) and path and not PurePosixPath(path).is_absolute() and '..' not in PurePosixPath(path).parts, 'unsafe package path')

def strings(values, label, nonempty=True):
    require(isinstance(values,list) and (bool(values) or not nonempty) and all(isinstance(x,str) and x for x in values), label+' must be string list')
    require(len(values)==len(set(values)), label+' duplicates')

def ratio(value, label):
    require(not isinstance(value,bool), label+' bool')
    try:
        n=float(value)
    except (ValueError,TypeError):
        require(False,label+' not numeric')
    require(0<=n<=1,label+' out of range')

def mapping(obj, label):
    require(isinstance(obj,dict) and all(isinstance(k,str) and isinstance(v,str) for k,v in obj.items()),label+' must map strings')

def validate(c):
    finite_tree(c)
    keys(c,'',FIELDS[''])
    require(type(c['schema_version']) is int and c['schema_version']==1,'unsupported schema')
    keys(c['package'],'package',FIELDS['package']); keys(c['package']['source'],'source',FIELDS['source'])
    require(re.fullmatch('[0-9a-f]{40}',c['package']['source']['commit']) is not None,'source commit must be pinned')
    require(c['package']['name'] and c['package']['owner'],'package name/owner missing')
    units={};targets={}
    require(isinstance(c['build_units'],list) and c['build_units'],'no build units')
    for b in c['build_units']:
        keys(b,'build_units',FIELDS['build_units'])
        require(b['id'] not in units,'duplicate build unit')
        require((b['arch'],b['isa']) in [('armv7l','thumb'),('armv7l','a32'),('aarch64','a64')],'mixed/unsupported ISA')
        for k in ['spec','patch','profile_staging']: relative(b[k])
        for k in ['macros','consume_macro']: mapping(b[k],k)
        require(b['macros'].get('profile_isa',b['isa'])==b['isa'],'macro ISA mismatch')
        require(not {'_smp_mflags','__make'} & b['macros'].keys(),'resource/capture macros reserved')
        units[b['id']]=b
    require(isinstance(c['targets'],list) and c['targets'],'no targets')
    for t in c['targets']:
        keys(t,'targets',{'id','build_unit','package_path'})
        require(t['id'] not in targets and t['build_unit'] in units,'target duplicate/unknown unit')
        relative(t['package_path']);keys(t.get('thresholds',{}),'thresholds')
        for k,v in t.get('thresholds',{}).items():
            if k=='min_target_samples':positive(v,k,integer=True,zero=True)
            else:ratio(v,k)
        targets[t['id']]=t
    r=c['runtime'];keys(r,'runtime',FIELDS['runtime'])
    for k in ['deploy_set','must_load','plugin_dirs']:strings(r[k],k,nonempty=k!='plugin_dirs')
    for p in r['deploy_set']:relative(p)
    require(set(r['must_load'])<=targets.keys(),'must_load unknown target')
    mapping(r['env'],'env');positive(r['cpu_affinity'],'cpu',True,True);positive(r['timeout_s'],'timeout')
    co=c['collect'];keys(co,'collect',{'event','runs','period_unit','min_target_share'})
    require(co['event']=='cycles','unsupported event');positive(co['runs'],'runs',True);positive(co['period_unit'],'unit',True);ratio(co['min_target_share'],'share')
    def sampling(d):
        require(('period' in d)^('freq' in d),'period xor freq required')
        positive(d.get('period',d.get('freq')),'sampling interval',True)
    sampling(co)
    for board in ['rpi4','rpi5']:
        if board in co:
            override=co[board];require(isinstance(override,dict) and not set(override)-{'period','freq'},'unknown board override')
            sampling(override)
    keys(c['identity'],'identity',FIELDS['identity']);require(type(c['identity']['allow_unverified_identity']) is bool,'identity bool')
    cs=c['consumption'];keys(cs,'consumption',FIELDS['consumption'])
    for k in ['diag_macro','object_to_target']:mapping(cs[k],k)
    require(set(cs['object_to_target'].values())==targets.keys(),'object mappings must cover targets')
    for path in cs['object_to_target']:relative(path)
    for k in ['record_coverage_warn_percent','sample_coverage_warn_percent']:
        positive(cs[k],k,True,True);require(cs[k]<=100,'coverage >100')
    require(type(cs['fail_on_coverage_warning']) is bool,'coverage boolean')
    cc=c['command_capture'];keys(cc,'command_capture',FIELDS['command_capture'])
    require(cc['method'] in ['recorded-switches','verbose-make'],'unknown capture method')
    strings(cc['build_config_files'],'build configs')
    for p in cc['build_config_files']:relative(p)
    m=c['measure'];keys(m,'measure',FIELDS['measure'])
    require(m['metric']=='seconds' and m['better']=='lower','only positive seconds/lower implemented')
    positive(m['warmup'],'warmup',True,True)
    if m['blocks']!='pilot':positive(m['blocks'],'blocks',True)
    ratio(m['epsilon'],'epsilon');require(0<float(m['epsilon'])<1,'epsilon bounds')
    return c

def load(path):
    with Path(path).open('rb') as f: return validate(tomllib.load(f))

def load_inputs(path):
    with Path(path).open('rb') as f:d=tomllib.load(f)
    require(set(d)=={'inputs'} and isinstance(d['inputs'],list),'inputs table')
    seen=set()
    for x in d['inputs']:
        require(set(x)=={'id','path','sha256','start','duration','role','oracle'},'input fields')
        require(x['id'] not in seen,'duplicate input');seen.add(x['id'])
        require(re.fullmatch('[0-9a-f]{64}',x['sha256']) is not None,'input SHA')
        require(x['role'] in ['train','pilot','test','test-secondary','tuning','conformance'],'input role')
        positive(x['start'],'start',zero=True);positive(x['duration'],'duration')
        o=x['oracle'];require(set(o)=={'caps','threads','frames','bytes','digest'},'oracle fields')
        for k in ['threads','frames','bytes']:positive(o[k],k,True)
        require(re.fullmatch('[0-9a-f]{64}',o['digest']) is not None,'oracle digest')
    roles = {'train': 'train', 'tuning': 'tuning', 'test': 'test', 'test-secondary': 'test'}
    for i, a in enumerate(d['inputs']):
        for b in d['inputs'][i+1:]:
            left, right = roles.get(a['role']), roles.get(b['role'])
            if left and right and left != right and a['sha256'] == b['sha256']:
                require(max(a['start'], b['start']) >= min(a['start']+a['duration'], b['start']+b['duration']),
                        left+'/'+right+' overlap: '+a['id']+' / '+b['id'])
    return d['inputs']

def hook_result(path):
    d=json_load(path)
    require(set(d)=={'status','eos','frames','bytes','digest','metric_value','metric_unit'},'hook fields')
    require(d['status']=='ok' and d['eos'] is True,'hook failed','correctness',3)
    for k in ['frames','bytes']:positive(d[k],k,True)
    require(re.fullmatch('[0-9a-f]{64}',d['digest']) is not None,'hook digest')
    positive(d['metric_value'],'hook metric');require(d['metric_unit']=='seconds','hook unit')
    return d
