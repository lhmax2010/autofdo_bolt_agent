"""Re-run the RPi5 S5 audit on archived build artifacts without GBS or SDB."""
import argparse
from pathlib import Path

from afdo_wf import config, live, platforms
from afdo_wf.common import json_load, require, save, sha256


def replay(archive, output):
    def details(stage):
        return json_load(archive / 'receipts' / f'{stage}.json')['details']

    audited = details('rebuild')
    runner = object.__new__(live.Experiment)
    runner.platform = platforms.load('rpi5-aarch64')
    runner.package = config.load(live.Experiment.code / 'packages/ffmpeg/package-rpi5.toml')
    runner.ops = 0
    runner.details = lambda _, stage: details(stage)

    def archived_variant(name, *_args, **_kwargs):
        return audited[{'BASE-r': 'base_repeat', 'AFDO': 'candidate'}[name]]

    runner.build_variant = archived_variant
    runner.deploy_variant = lambda _variant, _out: audited['deployments']['candidate']

    def archived_oracle(name, item, _deployment, _out):
        label = name.removeprefix('audit-').removesuffix('-' + item['id'])
        return audited['oracles'][label][item['id']]

    runner.oracle = archived_oracle
    runner.inputs = [{'id': item} for item in audited['oracles']['control']]
    output.mkdir(parents=True, exist_ok=False)
    observed = runner.rebuild(output, None)

    require(observed['buildlock'] == audited['buildlock'], 'archived command comparison changed')
    require(observed['consumption'] == audited['consumption'], 'archived consumption evidence changed')
    provenance = json_load(output / 'consumption-command-provenance.json')
    old = json_load(archive / 'stages/rebuild/002/consumption-command-provenance.json')
    require(provenance == old and provenance['build_lock_unmodified'], 'archived GCC provenance changed')
    archived_deps = {Path(row['path']).name: row['sha256'] for row in provenance['dependencies']}
    require(set(archived_deps) == {'crtbeginS.o', 'crtendS.o', 'libgcc.a', 'libgcc_eh.a'},
            'archived GCC support-object set changed')
    require(all(Path(row['path']).is_relative_to(Path(audited['candidate']['scratch']) / runner.platform.gcc_support)
                for row in provenance['dependencies']), 'support provenance escapes platform GCC path')
    art = audited['candidate']['artifacts']
    for entry in art.values():
        runtime = Path(entry['path']).relative_to(audited['candidate']['extracted'])
        debug = Path(entry['debug_path']).relative_to(audited['candidate']['extracted'])
        require(runtime.parent == Path(runner.platform.runtime_lib), 'runtime path differs from archive')
        require(debug == Path(runner.platform.debug_root) / (str(runtime) + '.debug'),
                'debug path differs from archive')
        require(sha256(entry['path']) == entry['sha256']
                and sha256(entry['debug_path']) == entry['debug_sha256'], 'archived ELF changed')
    require(platforms.load('rpi4-armv7l').gcc_support == 'usr/lib/gcc', 'ARM32 GCC path changed')
    save(output / 'rpi5-replay-summary.json', dict(
        passed=True, archive=str(archive), original_rebuild_receipt=sha256(archive / 'receipts/rebuild.json'),
        aarch64_gcc_path=runner.platform.gcc_support, armv7l_gcc_path='usr/lib/gcc',
        aarch64_runtime_path=runner.platform.runtime_lib, aarch64_debug_path=runner.platform.debug_root,
        gcc_objects=archived_deps, paired_elf_sha_verified=list(art),
        source_counts=provenance['source_command_counts'],
        excluded_counts={key: len(rows) for key, rows in provenance['excluded_support_records'].items()},
        applied_samples={name: row['positive_records'] for name, row in observed['consumption']['targets'].items()},
    ))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    arguments = parser.parse_args()
    replay(arguments.archive.resolve(), arguments.output.resolve())
