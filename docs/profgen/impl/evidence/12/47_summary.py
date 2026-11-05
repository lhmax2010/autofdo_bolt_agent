from pathlib import Path
import json,re,collections,hashlib
W=Path.cwd();D=W/'temp/board-round1-patch8';E=W/'docs/profgen/impl/evidence/12';rows=json.loads((D/'runs.json').read_text());converted=json.loads((D/'reconverted.json').read_text())['runs']
by_source={x['source']:x for x in converted};new_by_tag={x['tag']:x for x in rows};groups=[]
for x in json.loads((W/'docs/profgen/impl/evidence/12/19_resume2_runs.json').read_text()):
 if not x['formal']:continue
 source=str(W/x['run']);name=Path(source).name.removeprefix('formal2-');m=re.fullmatch(r'((?:spike|ffmpeg)-(?:thumb|a32)-S)-(sample-fixed|sample-freq)-(bbb|tos)-(\d+)-r(\d+)-s\d+',name);assert m
 variant,mode,video,budget,rep=m.groups();groups.append(dict(group=name.rsplit('-s',1)[0],variant=variant,mode=mode,video=video,budget=int(budget),rep=int(rep),target_samples=x['target_samples'],sources=[source],eligibility='unknown',reason='old formal data lack exact cycles/task-clock and starting policy bounds; retained, not fabricated'))
for root in [W/'temp/board-round1-amend1',D]:
 records={x['tag']:x for x in json.loads((root/'runs.json').read_text())}
 for x in json.loads((root/'formal-groups.json').read_text()):
  source=[records[s] for s in x['segments']];statuses=['abnormal' if s['eligibility']['abnormal_reasons'] else 'unknown' if s['eligibility']['unknown_reasons'] else 'clean' for s in source]
  category='abnormal' if 'abnormal' in statuses else 'unknown' if 'unknown' in statuses else 'clean'
  groups.append({**x,'sources':[s['local'] for s in source],'eligibility':category,'segment_eligibility':statuses})
# All conclusions retain excluded and clean views; no configuration quality comparison.
summary=collections.defaultdict(lambda:dict(groups=0,target_samples=0,usable_samples=0,clean_groups=0,clean_target_samples=0,abnormal_groups=0,unknown_groups=0))
for g in groups:
 key=f"{g['variant']}/{g['mode']}/{g['video']}/{g['budget']}";s=summary[key];s['groups']+=1;s['target_samples']+=g['target_samples'];s[g['eligibility']+'_groups']+=1
 if g['eligibility']=='clean':s['clean_target_samples']+=g['target_samples']
 g['conversion_complete']=all(p in by_source for p in g['sources']);g['usable_samples']=sum(by_source[p]['quality']['samples']['target']['usable']['sample_count'] for p in g['sources'] if p in by_source);s['usable_samples']+=g['usable_samples']
run_summaries=[];normalizations={};alias_total=0;pass_total=0
for x in converted:
 q=x['quality'];n=q['thumb_dwarf_normalization'];alias_total+=n['alias_query_count'];pass_total+=n['alias_check_passed'];normalizations[x['variant']]=n['top50'];src=Path(x['source']);out=D/'converted'/src.name
 row=dict(run=x['source'],variant=x['variant'],identity=q['identity']['grade'],conversion=q['verdict']['conversion'],input=q['samples']['input_total']['sample_count'],target=q['samples']['target'],isa={k:v['counts']['sample_count'] for k,v in q['isa'].items() if k in ['thumb','a32','a64','unknown']},name_merged_functions=q['coverage']['name_merged_functions'],name_merged_top50=q['coverage']['name_merged_top50'],normalized_ranges=n['range_count'],alias_queries=n['alias_query_count'],alias_check_passed=n['alias_check_passed'],alias_addresses=n['alias_addresses_top50'],profile_sha256=x['profile_sha256'],quality_path=str(out/'quality.json'),quality_sha256=hashlib.sha256((out/'quality.json').read_bytes()).hexdigest(),complete_text_path=str(src/'perfscript.txt'))
 # Hash original data via already verified receipt rather than rereading gigabytes.
 row['diagnostic_counts']=x['diagnostic_counts'];run_summaries.append(row)
res=dict(logical_groups=len(groups),expected_groups=70,physical_S_runs=len(converted),target_samples=sum(x['quality']['samples']['target']['counts']['sample_count'] for x in converted),usable_samples=sum(x['quality']['samples']['target']['usable']['sample_count'] for x in converted),groups=groups,by_configuration=dict(sorted(summary.items())),runs=run_summaries,normalizations_by_variant=normalizations,alias_queries=alias_total,alias_check_passed=pass_total,training_runs=[r for r in rows if r['mode'] in ['R','C','G5']],pending_groups=70-len(groups))
(D/'matrix-summary.json').write_text(json.dumps(res,indent=2)+'\n')
print({k:res[k] for k in ['logical_groups','physical_S_runs','target_samples','usable_samples','alias_queries','alias_check_passed','pending_groups']})
