"""Q.5 #6: read command/exit metadata only; never open a historical profile."""
import collections
import json
from pathlib import Path
from run_scoped import WORK, sha
from registration_address_check import dump
from pack_static_evidence import tables

BASE = WORK/'docs/profgen/eval/prep/evidence'
OUT = BASE/'registration-checks/batch2'


def main():
    source = WORK/'temp/board-round1-retry/final-reconverted.json'
    runs = json.loads(source.read_text())['runs']
    assert len(runs)==106
    details=[]; counts=collections.defaultdict(collections.Counter)
    for row in runs:
        folder=WORK/'temp/p9-formal-reconversion/outputs'/Path(row['source']).name
        for prefix in ['', 'period-']:
            cp=folder/(prefix+'command.json');rp=folder/(prefix+'run.json')
            if not cp.exists():
                assert prefix=='period-'
                continue
            cmd=json.loads(cp.read_text())['command'];result=json.loads(rp.read_text())
            binary=next(x.split('=',1)[1] for x in cmd if x.startswith('--binary='))
            obj=next(o for o in ['spike-thumb','spike-a32','ffmpeg-thumb','ffmpeg-a32'] if o+'-S/' in binary)
            agg=next(x.split('=',1)[1] for x in cmd if x.startswith('--ip-aggregation='))
            skid=next(x.split('=',1)[1] for x in cmd if x.startswith('--ip-skid='))
            counts[obj][agg+'/'+skid]+=1
            details.append([obj,row['source'],str(cp.relative_to(WORK)),sha(cp),str(rp.relative_to(WORK)),sha(rp),agg,skid,result['rc']])
    assert len(details)==126
    parts=tables(OUT,'historical-conversions',['object','run','command_metadata','command_sha256','exit_metadata','exit_sha256','aggregation','skid','exit_code'],details)
    availability={obj:{opt:dict(status='not_attempted_in_patch9_reconversion',success=None,
        recorded_attempts=sum(n for key,n in c.items() if opt in key.split('/'))) for opt in ['avg','prev-inst']} for obj,c in counts.items()}
    assert all(v['recorded_attempts']==0 for a in availability.values() for v in a.values())
    older=WORK/'docs/profgen/impl/evidence/12/31_real_avg_independent.json'
    older_cmds=[dict(command=x['command'],exit_code=x['exit']) for x in json.loads(older.read_text())['generation'] if '--ip-aggregation=avg' in x['command']]
    dump(OUT/'availability.json',dict(source=str(source),source_sha256=sha(source),conversion_metadata_records=len(details),
      configurations=counts,availability=availability,parts=parts,
      historical_patch8_avg=dict(source=str(older),sha256=sha(older),commands=older_cmds,
      interpretation='Earlier patch8 FFmpeg Thumb avg success is not patch9 availability evidence'),
      profiles_opened=0,interpretation='not attempted is neither success nor failure; no conversion was rerun'))
    draft=dict(kind='unregistered_seal_draft',amendment3_registered=False,objects={},sources=[])
    for obj in sorted(counts):
        p=BASE/'identity-gate/v18-gates'/(obj+'-static')/'summary.json';s=json.loads(p.read_text())
        fields=['coverage_1','coverage_2','coverage_3','coverage_3_prime','coverage_3_views',
                'code_bearing','nonduplicated_outside','n_eff','K','status','registration_status','domain_unresolved_lines','evaluation_domain']
        draft['objects'][obj]={k:s[k] for k in fields}
        draft['objects'][obj]['availability']=availability[obj]
        draft['sources'].append(dict(path=str(p.relative_to(WORK)),sha256=sha(p)))
    p=OUT/'object-seal-draft.json';dump(p,draft)
    dump(OUT/'object-seal-draft-sha.json',dict(path=str(p.relative_to(WORK)),sha256=sha(p),not_amendment3=True))
    print(json.dumps(dict(records=len(details),configurations=counts,draft_sha256=sha(p))))


if __name__=='__main__':main()
