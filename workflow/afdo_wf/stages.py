"""Stage order, dependencies and operator-visible workflow metadata."""

def stage(dependencies, purpose, inputs, gates, outputs, board):
    return dict(dependencies=dependencies, purpose=purpose, inputs=inputs, gates=gates,
                outputs=outputs, board_operations=board)


STAGES = {
    'preflight': stage(
        [], 'Establish host and board readiness.',
        ['job, package and platform', 'tool and media SHA locks', 'board identity'],
        ['host resources and tool availability', 'board identity and hardware cycles',
         'thermal and telemetry readiness', 'media SHA'],
        ['capabilities and resource records', 'hardware event and input evidence'],
        ['verify identity', 'journal the session', 'check or deploy tools, scripts and media',
         'probe hardware cycles and telemetry']),
    'build': stage(
        ['preflight'], 'Freeze dependencies and build the baseline.',
        ['pinned source, patch and spec', 'GBS config, snapshots or frozen repository',
         'package build unit'],
        ['host build locks and resource limits', 'frozen dependency identity',
         'matching runtime and debug build IDs'],
        ['BASE RPMs and ELF manifests', 'dependency and build-lock evidence'], []),
    'deploy': stage(
        ['build'], 'Prepare the baseline and establish independent correctness.',
        ['BASE runtime manifest', 'declared oracles and inputs', 'board runtime'],
        ['runtime compatibility', 'deployment and loaded-library identity', 'PLAT/BASE correctness'],
        ['deployment manifest', 'PLAT and BASE oracle records'],
        ['verify runtime compatibility when enabled', 'deploy BASE',
         'run untimed PLAT and BASE decoding']),
    'collect': stage(
        ['deploy'], 'Collect training samples from BASE.',
        ['BASE deployment', 'training input', 'sampling configuration'],
        ['cool-down and workload completion', 'loaded-library and perf build IDs', 'verified pull'],
        ['perf exports, evlists and build IDs', 'training correctness evidence'],
        ['run the training workload and perf', 'verify loaded libraries',
         'pull and verify collection artifacts']),
    'convert': stage(
        ['collect'], 'Convert, check and merge samples into the locked profile.',
        ['perf exports', 'paired ELF and debug files', 'pinned profgen and profdata'],
        ['profile conversion and identity checks', 'quality policy', 'merge compatibility'],
        ['quality reports', 'locked profile and disclosure'], []),
    'rebuild': stage(
        ['convert', 'build'], 'Rebuild and audit the AFDO candidate and control.',
        ['locked profile', 'frozen repository and BASE build lock', 'optimization records'],
        ['build-lock comparison', 'profile and AppliedSamples consumption', 'correctness when enabled'],
        ['BASE-r and AFDO artifacts', 'build-lock and consumption evidence'],
        ['for preparation-platform audits, deploy candidates and verify untimed correctness']),
    'measure': stage(
        ['rebuild', 'deploy'], 'Collect and analyze paired measurements.',
        ['audited variants and PLAT oracles', 'test inputs', 'telemetry capability record and seeds'],
        ['pre/post correctness', 'locked paired plan', 'temperature, telemetry and library identity'],
        ['paired rounds, plans and intervals', 'sensitivity analysis'],
        ['deploy or rehydrate variants', 'verify oracles', 'run pilots, warmups and timed pairs']),
    'report': stage(
        ['measure', 'convert'], 'Write the checked experiment report.',
        ['measurement and conversion receipts', 'build lock, consumption and cleanup evidence'],
        ['publishability checks', 'complete report fields'],
        ['report.json and report.md'], []),
    'restore': stage(
        [], 'Reconcile the experiment cleanup journal.',
        ['saved board identity', 'cleanup journal and verified-pull records'],
        ['identity before action', 'ownership and verified-pull checks'],
        ['restored session state or cleanup_pending'],
        ['restore root and governor', 'stop owned processes and clear verified artifacts']),
}

DAG = {name: data['dependencies'] for name, data in STAGES.items()}
RUN_STAGES = tuple(name for name in DAG if name != 'restore')
STOP_ALIASES = {'afdo-audit': 'rebuild'}
RECEIPT_FIELDS = ['stage', 'status', 'time', 'inputs', 'outputs', 'upstream', 'details']
