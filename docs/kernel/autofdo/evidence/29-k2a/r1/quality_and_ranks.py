#!/usr/bin/env python3
from collections import Counter
from pathlib import Path
import csv
import json
import sys

out=Path(sys.argv[1])
stats=json.loads((out/'r1-statistics.json').read_text())
summary={}
fixed=['pipe','mmfault','tmpfs','syscall','tos']
json_files=[out/x['segment']/'quality.json' for x in stats['segments']]
quality=[json.loads(f.read_text()) for f in json_files]
k=Counter()
for segment,result,source in zip(stats['segments'],quality,json_files,strict=True):
    assert result['identity']['grade']=='verified' and result['semantics']['fs_discriminator']
    assert result['samples']['kernel_ip']['outside_image']['sample_count']<=.01*result['samples']['kernel_ip']['target']['sample_count']
    for field,value in result['samples']['kernel_ip'].items():
        k[field]+=value['sample_count']
with (out/'top30-before-after.tsv').open('w') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n')
    w.writerow(('workload','function','before_rank','after_rank','before_samples','after_samples','delta_samples','delta_period','before_kernel_pct','after_kernel_pct'))
    for name in fixed:
        load=stats['workloads'][name]
        a,b=Counter(),Counter()
        for source in sorted(out.glob(f'session-*/{name}/segment.json')):
            r=json.loads(source.read_text())
            a.update(r['before']); b.update(r['after'])
        before={f:i for i,(f,n) in enumerate(a.most_common(30),1)}
        after={f:i for i,(f,n) in enumerate(b.most_common(30),1)}
        total=load['kernel']
        ranked=[*before,*(f for f in after if f not in before)]
        for fn in ranked:
            w.writerow((name,fn,before.get(fn,''),after.get(fn,''),a[fn],b[fn],b[fn]-a[fn],(b[fn]-a[fn])*1000003,
                        round(100*a[fn]/total,5),round(100*b[fn]/total,5)))
        if name in fixed[:3]:
            assert load['usable_c_line_lower']>=50000
        reasons=load['reasons']
        structural=sum(reasons.get(key,0) for key in ('leaf_only','only_helper_frames','stack_boundary_without_caller','caller_outside_a32_text'))
        summary[name]=dict(total=total,irq_window=load['shadow'],assigned=reasons.get('reattributed',0),
                           structural_no_caller=structural,reason_counts=reasons,candidate_c_lower=load['usable_c_line_lower'],
                           k1e_c_lower=sum(x['baseline_c_line_lower'] for x in stats['segments'] if x['segment'].endswith('/'+name)))
assert len(quality)==15 and stats['ambiguous_upper']*100<=stats['usable']*2
data=dict(gates='passed',workloads=summary,memory_of_input_format='A32 K-BASE, fixed period 1000003',
          k1e_usable=stats['baseline_usable'],candidate_usable=stats['usable'],fs_discriminator=True,identity_verified=15,
          aggregate_kernel_ip=dict(k),ambiguous_upper=stats['ambiguous_upper'],ambiguous_upper_pct=100*stats['ambiguous_upper']/stats['usable'],
          volatile_perf_vdso_path_differences=sum(row.get('perf_vdso_path_differences',0) for row in stats['segments']),
          lost_reports=[q['lost'] for q in quality],profile_sha256=stats['profile_sha256'],baseline_profile_sha256=stats['baseline_profile_sha256'])
(out/'quality-summary.json').write_text(json.dumps(data,indent=2)+'\n')
