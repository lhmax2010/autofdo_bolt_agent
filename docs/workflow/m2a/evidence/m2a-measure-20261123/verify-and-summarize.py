"""Verify immutable receipts and reconstruct S6 plans, estimates and frequency series."""
from datetime import datetime
import json
from pathlib import Path
import re
import statistics
import sys
from zoneinfo import ZoneInfo

from afdo_wf import stats
from afdo_wf.common import save, sha256
from afdo_wf.receipts import Store

out = Path(sys.argv[1])
prerequisites = json.loads((out/'prerequisites.json').read_text())
formal = Path(prerequisites['formal'])
store = Store(formal/'receipts')
assert sha256(prerequisites['sealed_job'])==prerequisites['sealed_job_sha256']
assert sha256(prerequisites['sealed_platform'])==prerequisites['sealed_platform_sha256']
for stage, meta in prerequisites['receipts'].items():
    assert sha256(store.path(stage))==meta['sha256']
stored = store.verify('report')
measured = json.loads(store.path('measure').read_text())  # Already checked through report upstream.
output = Path(stored['details']['rounds'][0]['local']).parent
report_file = next(Path(p) for p in stored['outputs'] if p.endswith('/report.json'))
report_md = next(Path(p) for p in stored['outputs'] if p.endswith('/report.md'))
report = json.loads(report_file.read_text())
assert report==stored['details']
expected = {'tos-720p-60': (2026112340,2026112350), 'sintel-1080p-60': (2026112341,2026112351)}
windows = {}
checks = {}
for test, seeds in expected.items():
    planpath=output/(test+'-plan.json')
    plan=json.loads(planpath.read_text())
    locked=json.loads((output/(test+'-plan-lock.json')).read_text())
    row=report['comparison_summary'][test]
    comparison=measured['details']['comparisons'][test]
    assert (row['order_seed'],row['bootstrap_seed'])==seeds
    assert row['plan_sha256']==locked['sha256']==sha256(planpath)
    assert row['plan_lock_host_epoch']<row['first_formal_launch_host_epoch']
    assert row['first_formal_launch_host_epoch']<datetime.fromisoformat(measured['time']).timestamp()
    pilots=[r['wall_seconds'] for r in comparison['pilots']]
    assert plan['N']==stats.budget(pilots) and plan['warmup']==2 and len(pilots)==10 and plan['epsilon']==.01
    assert plan['order']==stats.order(plan['N'], seeds[0])
    assert row['pilot_base_cv']==statistics.stdev(pilots)/statistics.mean(pilots)
    blocks=json.loads((output/(test+'-blocks.json')).read_text())
    assert stats.analyze(blocks,plan['N'],seeds[1],plan['epsilon'])==row['statistics']
    rounds=[r for r in measured['details']['rounds'] if r['input']==test]
    labels=['BASE','AFDO']
    assert len(blocks)==plan['N'] and len(rounds)==2*plan['N']
    frequencies=[]
    pair_attempts=[]
    for i,wanted in enumerate(plan['order'], 1):
        block=[r for r in rounds if r['block']==i]
        assert [r['variant'] for r in block]==[plan['control'] if x=='BASE' else x for x in wanted]
        assert all(r['maps_checked'] and r['perf']['task-clock']>0 and r['perf']['cycles']>0 for r in block)
        assert len({r['attempt'] for r in block})==1
        pair_attempts.append(dict(block=i,attempt=block[0]['attempt'],order=wanted))
        freq={}
        for r in block:
            label='control' if r['variant']==plan['control'] else 'candidate'
            freq[label]=dict(cycles=r['perf']['cycles'],task_clock_ms=r['perf']['task-clock'])
        frequencies.append(freq)
    assert stats.effective_frequency(frequencies)==row['effective_frequency']
    for path in sorted(output.glob('*-'+test+'-*-row.json')):
        item=json.loads(path.read_text())
        if not item.get('perf'):
            continue
        value=item['perf']['cycles']/item['perf']['task-clock']/1000
        windows[path.name]=dict(stage=path.name.split('-')[0],test=test,
                                variant=item['variant'],MHz=value,flag=item['telemetry']['classification'],
                                monotonic_start=item['start'],monotonic_end=item['end'],
                                row_sha256=sha256(path))
    checks[test]=dict(plan_sha256=sha256(planpath), plan_order=plan['order'],pairs=pair_attempts,
                      formal_count=len(rounds), deterministic_statistics_match=True)
nonformal=measured['details']['telemetry_check']['rounds']
for item in nonformal:
    p=Path(item['local']).parent/(item['name']+'-row.json')
    windows['nonformal-'+item['name']]=dict(stage='nonformal',test='tos-720p-60',variant=item['variant'],
        MHz=item['perf']['cycles']/item['perf']['task-clock']/1000,flag=item['telemetry']['classification'],
        monotonic_start=item['start'],monotonic_end=item['end'],row_sha256=sha256(p))
assert len(windows)==sum(2*report['comparison_summary'][test]['N']+14 for test in expected)+3
deploy=store.verify('deploy')['details']['oracles']
checks['oracle_comparisons']=len(report['oracle']['records'])
for name, r in report['oracle']['records'].items():
    key=re.sub(r'^(?:pre|post)-(?:control|candidate)-','',name)
    assert all(r[k]==deploy[key][k] for k in ('frames','digest','bytes','caps','eos'))
assert checks['oracle_comparisons']==12
end=out/'end.txt'
assert end.read_text().splitlines()[0]=='exit_code=0'
la=ZoneInfo('America/Los_Angeles')
start_time=datetime.fromisoformat((out/'start.utc').read_text().strip())
end_time=datetime.fromisoformat(end.read_text().splitlines()[1])
save(out/'paired-analysis-verification.json', dict(
    checks=checks, report_json=dict(path=str(report_file),sha256=sha256(report_file)),
    report_md=dict(path=str(report_md),sha256=sha256(report_md)),
    unchanged_s0_s5=prerequisites['receipts'], measure_receipt_sha256=sha256(store.path('measure')),
    report_receipt_sha256=sha256(store.path('report')),
    start_pacific=start_time.astimezone(la).isoformat(),end_pacific=end_time.astimezone(la).isoformat(),
    elapsed_seconds=(end_time-start_time).total_seconds()))
save(out/'effective-frequency-windows.json',windows)
print('Verified all sealed receipts,', len(windows), 'timing windows, and',checks['oracle_comparisons'],'oracle comparisons')
print('Report JSON:',report_file)
