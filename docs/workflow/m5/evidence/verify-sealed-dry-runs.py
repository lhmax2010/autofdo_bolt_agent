"""Exercise M5's read-only commands on the original, sealed M1 and M2a jobs."""
from pathlib import Path
import json
import os
import subprocess
import sys
from afdo_wf.common import sha256
from afdo_wf.stages import DAG, RUN_STAGES

work, output = map(Path, sys.argv[1:])
jobs = {
    'm1': work / 'temp/m1-ffmpeg-rpi4-thumb-01/attempt-11/job.json',
    'm2a': work / 'temp/m2a-rpi5-prep-20261119/continuation/job.json',
}


def invoke(label, *args):
    result = subprocess.run([sys.executable, '-B', '-m', 'afdo_wf', *args],
                            capture_output=True, text=True, check=True)
    (output / (label + '.json')).write_text(result.stdout)
    return json.loads(result.stdout)


report = {}
for label, job in jobs.items():
    conf = json.loads(job.read_text())
    run = Path(conf['output'])
    receipts = run / 'receipts'
    files = [job, Path(conf['package']), Path(conf['inputs']), run/'cleanup.json']
    files += sorted(receipts.glob('*.json'))
    before = {str(path): (sha256(path), path.stat().st_size, path.stat().st_mtime_ns) for path in files}
    root_entries = sorted((p.name, p.stat().st_mtime_ns) for p in run.iterdir())
    stat = invoke(label + '-status', 'status', '--job', str(job))
    dry = invoke(label + '-dry-run', 'run', '--dry-run', '--job', str(job))
    archive_report = json.loads((receipts/'report.json').read_text())
    for name in RUN_STAGES:
        row = stat['stages'][name]
        assert row['status'] == 'completed' and row['input_sha'] == row['upstream_sha'] == 'match'
        actual = Path(row['receipt'])
        assert actual == receipts/(name+'.json') and before[str(actual)][0] == sha256(actual)
        explained = invoke('explain-'+name, 'explain', name)
        planned = next(p for p in dry['stages'] if p['stage'] == name)
        assert explained['dependencies'] == planned['dependencies'] == DAG[name]
        assert explained['gates'] == planned['gates']
    explained = invoke('explain-restore', 'explain', 'restore')
    assert not explained['dependencies']
    assert stat['stages']['restore']['status'] == 'completed' and stat['cleanup_pending'] == 0
    assert stat['stage_order'] == list(DAG)
    assert not dry['board_contact']
    assert all(row['action']=='reuse' and not row['board_actions_this_stage'] for row in dry['stages'])
    measures = next(p for p in dry['stages'] if p['stage']=='measure')
    expected_seeds = {key:{field:value['plan'][field] for field in ('order_seed','bootstrap_seed')}
                      for key,value in archive_report['details']['comparisons'].items()}
    assert measures['declared_inputs']['recorded_plan_seeds'] == expected_seeds
    assert root_entries == sorted((p.name, p.stat().st_mtime_ns) for p in run.iterdir())
    assert all((sha256(path), os.stat(path).st_size, os.stat(path).st_mtime_ns) == value
               for path,value in before.items())
    report[label] = dict(stage_statuses={k:v['status'] for k,v in stat['stages'].items()},
                         input_and_upstream_match=len(RUN_STAGES), dry_run_reuse=len(dry['stages']),
                         explanation_metadata_matches=len(DAG), cleanup_pending=stat['cleanup_pending'],
                         archived_verdict=archive_report['details']['statistics']['primary']['verdict'],
                         archived_plan_seeds=expected_seeds,
                         unchanged={path:value[0] for path,value in before.items()})
(output/'sealed-acceptance.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
for label,row in report.items():
    print(label, row['input_and_upstream_match'], 'sealed completed stages,', row['dry_run_reuse'],
          'read-only plan entries,',len(row['unchanged']), 'files unchanged')
