from pathlib import Path
import json,hashlib,statistics,csv,sys,time
w=Path.cwd();b=Path(__file__).resolve().parent;f=b/'formal';m=f/'stages/measure/001'
sys.path.insert(0,str(w/'workflow'))
from afdo_wf.stats import parse_telemetry_tsv
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
end=read(b/'driver-end.json');assert end['results'][-1]['exit_code']==0
receipts={p.stem:read(p) for p in (f/'receipts').glob('*.json') if not p.name.endswith('.failure.json')}
assert all(v['status']=='complete' for v in receipts.values())
builds=[]
for p in sorted((f/'stages').glob('**/execution/result.json')):
 v=read(p);r=v['start_resources'];builds.append(dict(path=str(p.relative_to(w)),sha256=sha(p),exit_code=v['exit_code'],seconds=v['build_seconds'],peak=v['memory_peak'],minimum_mem_available=v['min_mem_available'],wait=v['wait_seconds'],start={k:r[k] for k in ['mem_available','load1','disk_free','nproc','time']},events=v['child']['memory_events'],unit=v['unit'],startup_memory_waiver=v.get('startup_memory_waiver')))
resources=read(b/'driver-resources.json');finals={str(p.relative_to(w)):read(p) for p in f.glob('final-*.json')}
for child in ['injected-job','telemetry-check-job']:
 for p in (m/child).glob('final-*.json'):finals[str(p.relative_to(w))]=read(p)
assert all(not v['errors'] and not v['cleanup_pending'] for v in finals.values())
rows=read(m/'rounds.json');assert len(rows)==62
compact=[]
for r in rows:
 local=Path(r['local']);samples=parse_telemetry_tsv((local/'telemetry.tsv').read_text());before=[s for s in samples if s['time']<=r['start']-1];after=[s for s in samples if s['time']>=r['end']+1];window=[before[-1]]+[s for s in samples if r['start']-1<s['time']<r['end']+1]+[after[0]]
 temp=[v for s in window for v in s['temperature'].values()];freq=[v for s in window for v in s['frequency'].values()];starttemp=[v for s in window if s['time']<=r['start'] for v in s['temperature'].values()]
 maps=read(local/'maps/decoder-check.json')
 compact.append(dict(input=r['input'],block=r['block'],variant=r['variant'],attempt=r['attempt'],wall_seconds=r['wall_seconds'],classification=r['telemetry']['classification'],task_clock_ms=r['perf']['task-clock'],cycles=r['perf']['cycles'],instructions=r['perf']['instructions'],start=r['start'],end=r['end'],window_start_max_c=max(starttemp),max_c=max(temp),min_c=min(temp),frequency_min_khz=min(freq),frequency_max_khz=max(freq),cadence_max=maps['cadence']['max_gap_seconds'],maps_snapshots=r['maps_checked'],raw=str(local.relative_to(w)),telemetry_sha256=sha(local/'telemetry.tsv')))
with (b/'accepted-rounds.csv').open('w') as out:
 cw=csv.DictWriter(out,fieldnames=compact[0].keys());cw.writeheader();cw.writerows(compact)
comparisons=read(m/'comparisons.json');planchecks={}
for k,v in comparisons.items():
 p=m/(k+'-plan.json');lock=read(m/(k+'-plan-lock.json'));rr=[r for r in rows if r['input']==k];pilots=v['pilots'];actual=[[r['variant'] for r in rr if r['block']==i] for i in range(1,v['plan']['N']+1)]
 assert sha(p)==lock['sha256'] and actual==v['plan']['order']
 planchecks[k]=dict(plan_sha256=sha(p),actual_order_matches=True,pilot_cv=statistics.stdev(r['wall_seconds'] for r in pilots)/statistics.mean(r['wall_seconds'] for r in pilots),N=v['plan']['N'],order_seed=v['plan']['order_seed'],bootstrap_seed=v['plan']['bootstrap_seed'],statistics=v['statistics'],effective_frequency=v['effective_frequency'])
r=receipts['rebuild']['details'];c=receipts['convert']['details']
summary=dict(time=time.time(),driver=end,receipts={k:dict(status=v['status'],path=str((f/'receipts'/(k+'.json')).relative_to(w)),sha256=sha(f/'receipts'/(k+'.json'))) for k,v in receipts.items()},builds=builds,resources=dict(minimum_mem_available=min([x['mem_available'] for x in resources]+[x['minimum_mem_available'] for x in builds]),driver_peak=max(int(x['memory.peak']) for x in resources),driver_events=resources[-1]['memory.events'],driver_samples=len(resources),driver_sample_max_gap=max(y['time']-x['time'] for x,y in zip(resources,resources[1:])),build_peak=max(x['peak'] for x in builds),minimum_disk_free=min(x['disk_free'] for x in resources)),finals=finals,buildlock=r['buildlock'],offline_reproducible=r['offline_reproducible'],control=r['control'],consumption={k:{x:y for x,y in v.items() if x!='examples'} for k,v in r['consumption']['targets'].items()},profile_sha256=c['lock']['sha256'],collisions=c['lock']['collisions'],nonformal_check=[dict(name=x['name'],telemetry=x['telemetry']) for x in read(m/'telemetry-check-job/check-rows.json')],comparisons=planchecks,formal_rounds=len(rows),oracle_count=len(list(m.glob('*oracle.json'))),maps_checks=len(list(m.glob('*/maps/decoder-check.json'))),technical_failures={p.name:read(p) for p in m.glob('*-failed-*.json')},formal_temperature_max=max(r['max_c'] for r in compact),formal_start_window_max=max(r['window_start_max_c'] for r in compact),cadence_max=max(r['cadence_max'] for r in compact))
summary['recovery_S3_receipt_unchanged']=sha(f/'receipts/collect.json')==read(b/'recovery-interruption.json')['collect_receipt_sha256']
assert summary['recovery_S3_receipt_unchanged']
code=read(b/'code-sha.json');summary['runtime_sha_differences']=[k for k,v in code.items() if sha(w/k)!=v];assert not summary['runtime_sha_differences']
summary['quality_counts']=[]
for i,q in enumerate(c['quality']):
 t=q['samples']['target'];summary['quality_counts'].append(dict(index=i,verdict=q['verdict'],counts={k:v['sample_count'] for k,v in t.items() if isinstance(v,dict) and 'sample_count' in v},nonleaf_line_zero=t['in_func_no_line']['nonleaf_line_zero']['sample_count'],target_paths=sorted(set(r['path'] for r in q['mapping']['records']))))
summary['recovery_receipts_predate_signal']={k:receipts[k]['time']<read(b/'recovery-interruption.json')['time'] for k in ['preflight','build','deploy','collect']}
(b/'acceptance-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['technical_failures','finals','receipts']},ensure_ascii=False,indent=2))
