"""Regenerate commands and stage-receipt fields from archived M1 attempt 11."""
import argparse
from pathlib import Path

from afdo_wf import build, live, profgen, scheduler
from afdo_wf.common import require, json_load, save, sha256


def replay(job_path, output):
    job = json_load(job_path)
    archive = Path(job['output'])
    experiment = live.Experiment({**job, 'output': str(output/'replay')}, job_path)
    stages = ['preflight', 'build', 'deploy', 'collect', 'convert', 'rebuild']
    original = {stage: json_load(archive/'receipts'/f'{stage}.json') for stage in stages}
    base = original['build']['details']
    deployment = original['deploy']['details']['deployment']
    training_item = next(item for item in experiment.inputs if item['role'] == 'train')
    checks = []

    def compare(kind, expected, observed, artifact):
        require(expected == observed, f'{kind} differs: {artifact}')
        checks.append(dict(check=kind, evidence=str(artifact), sha256=sha256(artifact)))

    launched = archive/'stages/collect/001'
    for index in range(1, experiment.package['collect']['runs'] + 1):
        name = f'train-{index}'
        for suffix, render in [('', experiment.training_command), ('-correctness', experiment.oracle_command)]:
            label = name + suffix
            argv, env = render(label, training_item, deployment)
            script = experiment.launch_script(experiment.remote+'/control-'+label, argv, env)
            artifact = launched/(label+'-launch.sh')
            compare('launch script', artifact.read_text(), script, artifact)

    for item in experiment.inputs:
        for label, deploy in [('PLAT', None), ('BASE', deployment)]:
            name = label+'-'+item['id']
            argv, env = experiment.oracle_command(name, item, deploy)
            script = experiment.launch_script(experiment.remote+'/control-'+name, argv, env)
            artifact = archive/'stages/deploy/001'/(name+'-launch.sh')
            compare('oracle launch', artifact.read_text(), script, artifact)

    variant_dirs = [archive/'stages/build/001', archive/'stages/rebuild/001/BASE-r',
                    archive/'stages/rebuild/001/AFDO']
    for directory in variant_dirs:
        artifact = directory/'execution/command.json'
        command = json_load(artifact)
        old = command['argv'][command['argv'].index('gbs'):]
        unit = experiment.package['build_units'][0]
        macros = dict(unit['macros'])
        if directory.name == 'AFDO':
            macros.update(unit['consume_macro'])
            macros.update(experiment.package['consumption']['diag_macro'])
        root_index = old.index('--buildroot')+1
        old[root_index] = str(output/'absent-build-root')
        argv = build.command(job['config'], job['source'], old[root_index], unit, macros, job['repo'], job['buildconf'])
        compare('GBS argv with new root normalized', old, argv, artifact)
        compare('GBS cwd', command['cwd'], job['source'], artifact)

    conversion = Path(original['convert']['details']['profile']).parent/'conversions.json'
    for item in json_load(conversion):
        profile = Path(item['path'])
        target = item['dso']
        artifact = {**base['artifacts'][target], 'board_path': next(
            row['board_path'] for row in deployment['manifest'].values() if row['id'] == target)}
        row = next(row for row in original['collect']['details']['runs'] if profile.name.startswith(row['id']+'-'))
        argv = profgen.command(job['profgen'], artifact, Path(row['local'])/'perf.script',
                               Path(row['local'])/'buildid-list.txt', profile,
                               profile.with_suffix('.quality.json'), experiment.package['collect']['period_unit'])
        compare('profgen argv', item['argv'], argv, conversion)
        expected_key = [job['repo_id'], artifact['isa'], target, experiment.package['collect']['event'],
                        'period', experiment.package['collect']['period_unit'], 'max/none/none/none']
        compare('profile partition key', item['merge_key'], expected_key, conversion)

    # Replay archived stage responses through the real receipt writer. It seals
    # copies of the response JSON without executing the old board/build stages.
    receipts = output/'replay-receipts'
    scheduler.execute(stages, {s: (lambda out, store, s=s: original[s]['details']) for s in stages},
                      output/'stage-replies', receipts, [job_path])
    for stage, record in original.items():
        artifact = archive/'receipts'/f'{stage}.json'
        new = json_load(receipts/f'{stage}.json')
        # Live GBS attempts now carry additional wait evidence. Archived
        # responses have no such evidence and keep their original schema.
        additive = {'gbs_waits'} - set(record) if stage in ('build', 'rebuild') else set()
        compare('receipt schema', set(record), set(new) - additive, artifact)
        compare('upstream stage names', set(record['upstream']), set(new['upstream']), artifact)
        compare('receipt detail replay', record['details'], new['details'], artifact)

    save(output/'m1-replay-summary.json', dict(
        result='pass', replay_checks=checks, stage_count=len(stages),
        additive_receipt_fields={'build': ['gbs_waits'], 'rebuild': ['gbs_waits']},
        normalization=['new build root', 'receipt timestamps and SHA bindings'],
        execution='command generation and receipt replay using archived responses; no GBS, SDB or profile execution',
    ))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archived_job', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    replay(args.archived_job.resolve(), args.output.resolve())
