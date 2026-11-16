"""Versioned machine report and human rendering of the same checked payload."""
from pathlib import Path
from .common import require, finite_tree, save, atomic_write

DISCLAIMER='profgen explicit conservative strategy; defaults not statistically validated'
REQUIRED={'experiment_id','build_lock','board_identity','telemetry_manifest','tools','artifacts','quality','code_shares','consumption','oracle','measurement_plan','rounds','statistics','limitations','cleanup_pending'}

def write(directory,data):
    require(REQUIRED<=data.keys(),'incomplete report: '+str(REQUIRED-data.keys()))
    finite_tree(data)
    data=dict(data);data['schema_version']=1
    data['limitations']=list(dict.fromkeys([*data['limitations'],DISCLAIMER]))
    primary=data['statistics'].get('primary',{})
    require(primary.get('verdict') in ['faster','slower','equivalent','inconclusive'],'invalid verdict')
    publishable=(bool(data['quality']) and data['build_lock'].get('passed') is True and data['consumption'].get('passed') is True and data['oracle'].get('passed') is True
                 and not data['cleanup_pending'] and all(q.get('publishable') is True for q in data['quality'].values()))
    if not publishable:
        data['statistics']={**data['statistics'],'primary':{**primary,'verdict':'inconclusive','publication_blocked':True}}
    data['publishable']=publishable
    directory=Path(directory)
    save(directory/'report.json',data)
    lines=['# Experiment '+data['experiment_id'],'',DISCLAIMER,'',
           'Verdict: **'+data['statistics']['primary']['verdict']+'**','',
           '| Section | Recorded value |','|---|---|']
    import json
    for k in sorted(REQUIRED):
        value=json.dumps(data[k],ensure_ascii=False,allow_nan=False).replace('|','\\|').replace('\n',' ')
        lines.append('| '+k+' | '+value+' |')
    atomic_write(directory/'report.md','\n'.join(lines)+'\n');return data
