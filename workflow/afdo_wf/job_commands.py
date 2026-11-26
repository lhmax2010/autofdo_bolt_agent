"""Host-only job initialization, DAG inspection and planning."""
from pathlib import Path
import re

from . import config, host_build, pgo, platforms
from .common import GateError, atomic_write, canonical, json_load, require, sha256
from .exits import EXIT_CODES
from .receipts import Store
from .stages import DAG, STAGES, RECEIPT_FIELDS


def paths(args, job):
    package = args.package or job.get('package')
    inputs = args.inputs or job.get('inputs')
    output = args.output or job.get('output')
    receipts = args.receipts or job.get('receipts') or (Path(output) / 'receipts' if output else None)
    if job.get('live'):
        require(not args.output or Path(args.output).resolve() == Path(job['output']).resolve(),
                'live output comes from the job')
        require(not args.receipts or Path(args.receipts).resolve() == (Path(job['output']) / 'receipts').resolve(),
                'live receipt directory comes from the job')
        require(not args.package or Path(args.package).resolve() == Path(job['package']).resolve(),
                'live package comes from the job')
        require(not args.inputs or Path(args.inputs).resolve() == Path(job['inputs']).resolve(),
                'live inputs come from the job')
        receipts = Path(job['output']) / 'receipts'
    return package, inputs, Path(output).resolve() if output else None, (
        Path(receipts).resolve() if receipts else None)


def optional_object(path):
    if not path.is_file():
        return None
    obj = json_load(path)
    require(isinstance(obj, dict), 'expected JSON object: ' + str(path))
    return obj


def cleanup_pending(output, receipts):
    for path in dict.fromkeys([output / 'cleanup.json', receipts.parent / 'cleanup.json']):
        journal = optional_object(path)
        if journal is not None and 'cleanup_pending' in journal:
            count = journal['cleanup_pending']
            require(isinstance(count, list), 'invalid cleanup journal: ' + str(path))
            return path, count
    return None, []


def reason_of(record):
    reason = record.get('reason', 'error')
    return 'user-abort' if reason == 'interrupted' else reason


def last_failure(store, stage, binding):
    for path in reversed(store.failure_paths(stage)):
        record = optional_object(path)
        if record is not None and (binding is None or record.get('redo') == binding):
            reason = reason_of(record)
            failure = dict(path=str(path), reason=reason, exit_code=EXIT_CODES.get(reason),
                           error=record.get('error'), recorded_reason=record.get('reason'))
            if 'gbs_waits' in record:
                failure['gbs_waits'] = record['gbs_waits']
            return failure
    return None


def status(output, receipts):
    store = Store(receipts, create=False)
    bindings = store.redo_bindings()
    cleanup_file, pending = cleanup_pending(output, receipts)
    hashes = {}

    def fingerprint(file):
        if file not in hashes:
            f = Path(file)
            try:
                hashes[file] = sha256(f) if f.is_file() else None
            except OSError:
                hashes[file] = None
        return hashes[file]

    result = {}
    for stage, dependencies in DAG.items():
        path = store.path(stage)
        binding = bindings.get(stage)
        row = dict(status='pending', receipt=str(path), input_sha='not_recorded',
                   upstream_sha='not_recorded', reason=None, dependencies=dependencies)
        try:
            record = optional_object(path)
            if record is not None:
                require(record.get('stage') == stage and record.get('status') in ('complete', 'invalidated')
                        and isinstance(record.get('inputs'), dict) and isinstance(record.get('upstream'), dict),
                        'malformed stage receipt: ' + str(path))
                row['recorded_status'] = record['status']
                if 'pgo_evidence' in record.get('details', {}):
                    row['pgo_evidence'] = record['details']['pgo_evidence']
                if 'gbs_waits' in record:
                    row['gbs_waits'] = record['gbs_waits']
                mismatches = [name for name, expected in record['inputs'].items() if fingerprint(name) != expected]
                if mismatches:
                    row['input_sha'] = 'mismatch'
                    row['mismatched_inputs'] = mismatches
                else:
                    row['input_sha'] = 'match'
                upstream_ok = (set(record['upstream']) == set(dependencies) and all(
                    result[name]['status'] == 'completed'
                    and fingerprint(str(store.path(name))) == record['upstream'][name]
                    for name in dependencies))
                row['upstream_sha'] = 'match' if upstream_ok else 'mismatch'
                if store.invalidated(record, binding) or mismatches or not upstream_ok:
                    row.update(status='invalidated', reason='gate')
                else:
                    row['status'] = 'completed'
            elif binding is not None:
                row.update(status='invalidated', reason='gate')
            failed = last_failure(store, stage, binding)
            if failed:
                row['last_failure'] = failed
                if row['status'] == 'pending' or row['status'] == 'invalidated' and binding:
                    row.update(status='failed', receipt=failed['path'], reason=failed['reason'])
            if binding:
                row['redo'] = binding
                row['rerun_authorized'] = store.invalidated(record, binding)
        except (GateError, OSError, ValueError, TypeError) as exc:
            row.update(status='failed', reason='error', error=str(exc))
        result[stage] = row
    if pending:
        result['restore'].update(status='cleanup_pending', reason='recovery-required',
                                 receipt=str(cleanup_file), pending_actions=len(pending))
    elif cleanup_file is not None and result['restore']['status'] == 'pending':
        result['restore']['receipt'] = str(cleanup_file)
        final = max(output.glob('final-*.json'), key=lambda p: p.stat().st_mtime_ns, default=None)
        if final is not None:
            state = optional_object(final)
            if state.get('cleanup_pending') == [] and state.get('errors') == []:
                result['restore'].update(status='completed', receipt=str(final))
    failures = [path for path in [*output.glob('failure-*.json'), receipts / 'run.failure.json'] if path.is_file()]
    last = max(failures, key=lambda p: p.stat().st_mtime_ns, default=None)
    history = None
    if last is not None:
        history = {**optional_object(last), 'path': str(last)}
    return dict(receipts=str(receipts), cleanup_pending=len(pending), stage_order=list(DAG), stages=result, last_run_failure=history)


def platform_package(package, platform):
    require(all(unit['arch'] == platform.arch and unit['isa'] in platform.isas
                for unit in package['build_units']), 'build unit does not match board platform')
    require(package['runtime']['cpu_affinity'] == platform.cpu, 'workload CPU differs from board platform')


def file_lock(path):
    value = Path(path).expanduser().resolve()
    require(value.is_file(), 'required local file missing: ' + str(value))
    return dict(path=str(value), sha256=sha256(value))


def initialize(args):
    require(args.job and args.package and args.inputs and args.platform and args.output,
            'init requires --job, --package, --inputs, --platform and --output', 'usage')
    path = Path(args.job).resolve()
    workdir = Path(args.workdir or Path.cwd()).resolve()
    output = Path(args.output).resolve()
    require(workdir.is_dir() and path.is_relative_to(workdir) and output.is_relative_to(workdir),
            'job and output must be inside the workdir')
    require(not path.is_relative_to(output), 'draft job must be outside the run output')
    require(not path.exists(), 'job already exists: ' + str(path))
    require(not output.exists(), 'init needs an unused run output path: ' + str(output))
    locks = {k: file_lock(v) for k, v in [('package', args.package), ('inputs', args.inputs),
                                         ('platform', platforms.profile_path(args.platform))]}
    package = config.load(locks['package']['path'])
    platform = platforms.load(args.platform)
    platform_package(package, platform)
    method = pgo.method(dict(method=getattr(args, 'method', None) or 'autofdo'), package)
    inputs = config.load_inputs(locks['inputs']['path'])
    require(inputs and any(r['role']=='train' for r in inputs) and any(r['role']=='test' for r in inputs),
            'at least a training input and a primary test input are required')
    provided = {}
    for item in args.media:
        key, sep, local = item.partition('=')
        require(sep and local and key not in provided, 'expected unique --media ID=FILE', 'usage')
        provided[key] = local
    require(set(provided) <= {row['id'] for row in inputs}, 'unknown media ID')
    media = {}
    for row in inputs:
        key = row['id']
        board = Path(row['path'])
        require(board.is_absolute() and board.is_relative_to('/opt/afdo_agent/inputs')
                and '..' not in board.parts and board.name != 'inputs',
                'input needs a file path under /opt/afdo_agent/inputs')
        local = provided.get(key) or (Path(args.media_dir) / board.name if args.media_dir else None)
        require(local, 'supply --media or --media-dir for ' + key)
        locked = file_lock(local)
        require(locked['sha256'] == row['sha256'], 'media SHA does not match manifest: ' + key, 'identity')
        media[key] = locked['path']
    experiment = args.experiment or path.stem
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', experiment) is not None,
            'experiment must be a single path component')
    required = ['serial', 'identity (exact model, arch, kernel, build_id)', 'tools', 'board_tools',
                'source', 'patch', 'config', 'build_environment', 'rpm_packages', 'profgen',
                'profdata', 'order_seed', 'bootstrap_seed']
    if platform.prepare_only or method == 'pgo':
        required += ['rpmspec', 'snapshots', 'snapshot_evidence']
    else:
        required += ['repo', 'repo_id', 'buildconf', 'frozen_packages']
    job = dict(draft=True, live=True, experiment=experiment, workdir=str(workdir), output=str(output),
               package=locks['package']['path'], inputs=locks['inputs']['path'], platform=args.platform,
               build_unit=package['build_units'][0]['id'], media=media, config_sha256=locks,
               missing_for_run=required)
    if method == 'pgo':
        job['method'] = method
        required += ['afdo_profile', 'pgo_warning_policy']
    atomic_write(path, canonical(job), exclusive=True)
    return dict(job=str(path), sha256=sha256(path), draft=True, missing_for_run=required)


def validate_locks(job):
    for name, lock in job.get('config_sha256', {}).items():
        actual = file_lock(lock['path'])
        configured = platforms.profile_path(job['platform']) if name == 'platform' else Path(job[name])
        same_path = Path(actual['path']) == configured.resolve()
        if not same_path and name=='platform' and job.get('pgo_resume_after_collect'):
            same_path = sha256(configured) == lock['sha256']
        require(actual['sha256'] == lock['sha256'] and same_path,
                'initialized configuration changed: ' + name)


def plan(args, job, selected):
    package_path, inputs_path, output, receipts = paths(args, job)
    package = config.load(package_path) if package_path else None
    method = pgo.method(job, package)
    inputs = config.load_inputs(inputs_path) if inputs_path else []
    validate_locks(job)
    platform = platforms.load(job.get('platform', 'rpi4-armv7l'))
    if package:
        platform_package(package, platform)
    current = status(output, receipts) if output and receipts else None
    report = []
    common = dict(job=str(Path(args.job).resolve()), package=package_path, inputs=inputs_path)
    collection = [row for row in inputs if row['role']=='train']
    measurement = [row for row in inputs if row['role'] in ('test', 'test-secondary')]
    for name in selected:
        stage = pgo.stage_metadata(name, STAGES[name]) if method == 'pgo' else STAGES[name]
        state = current['stages'][name] if current else {}
        found = state.get('status', 'pending')
        action = ('restore-pending' if found=='cleanup_pending' else
                  'reuse' if found=='completed' else
                  'redo-required' if found=='invalidated' and not state.get('rerun_authorized') else 'run')
        if action == 'run' and found == 'failed' and state.get('reason') == 'error' and 'error' in state:
            action = 'inspect-receipt'
        specific = {}
        if name in ('preflight', 'deploy', 'collect', 'measure'):
            rows = collection if name=='collect' else measurement if name=='measure' else inputs
            specific['media'] = [{k:r[k] for k in ('id', 'role', 'path', 'sha256', 'start', 'duration')}
                                 | {'host_path':job.get('media', {}).get(r['id'])} for r in rows]
        if name in host_build.BUILD_STAGES:
            build_settings = {**job, **job.get(name, {})}
            specific.update({key:build_settings.get(key) for key in ('source', 'patch', 'config', 'repo', 'snapshot_evidence')})
            if build_settings.get('workdir'):
                specific['gbs_lock'] = str(host_build.lock_path(build_settings['workdir'], build_settings.get('host')))
            specific['build_units'] = [{k:u[k] for k in ('id', 'arch', 'isa', 'spec')} for u in
                                       package['build_units']] if package else []
            if method == 'pgo' and package:
                specific['declared_pgo_patch'] = str(Path(package_path).parent / package['pgo']['patch'])
                specific['pgo_warning_policy'] = job.get('pgo_warning_policy')
                specific['afdo_profile'] = job.get('afdo_profile')
        if name=='preflight':
            specific['tool_locks'] = job.get('tools', {})
        if name=='measure':
            specific.update({k:job.get(k) for k in ('order_seed','bootstrap_seed')})
            paths_by_input = {}
            if found=='completed':
                # The authoritative seeds are in the recorded plans, including run-local overrides.
                measured = json_load(receipts / 'measure.json')['details']
                paths_by_input = {key:{field:value['plan'][field] for field in ('order_seed','bootstrap_seed')}
                                  for key,value in measured.get('comparisons',{}).items()}
            if paths_by_input:
                specific['recorded_plan_seeds'] = paths_by_input
        if receipts:
            specific['upstream_receipts'] = {s:str(receipts / (s + '.json')) for s in DAG[name]}
        if name == 'restore' and action == 'run' and job.get('live'):
            action = 'cleanup-on-exit'
        board_actions = stage['board_operations'] if job.get('live') and action in (
            'run', 'restore-pending', 'cleanup-on-exit') else []
        if name == 'rebuild' and not platform.prepare_only and method != 'pgo':
            board_actions = []
        report.append(dict(stage=name, action=action, recorded_state=found, declared_inputs=common|specific,
                           board_actions_this_stage=board_actions,
                           **stage))
    session = []
    if args.stage == 'run' and job.get('live'):
        session = ['check host readiness and exact board identity',
                   'reconcile pending cleanup before stages',
                   'journal root and governor and validate tools',
                   'rehydrate reusable deployments when present',
                   'restore owned state before reporting or exit']
    pgo_summary = dict(method=method, variants=list(pgo.VARIANTS), comparisons=pgo.comparison_metadata(),
                       missing_for_run=job.get('missing_for_run', [])) if method == 'pgo' else {}
    return dict(mode='dry-run', board_contact=False, draft=job.get('draft', False), live=job.get('live', False),
                platform=job.get('platform','rpi4-armv7l'), model=platform.model, arch=platform.arch,
                serial=job.get('serial'), output=str(output) if output else None,
                planned_live_session=session,
                cleanup_pending=current['cleanup_pending'] if current else 0, stages=report, **pgo_summary)


def explain(name, method='autofdo'):
    description = pgo.stage_metadata(name, STAGES[name]) if method == 'pgo' else STAGES[name]
    result = dict(stage=name, **description, receipt_fields=RECEIPT_FIELDS,
                  redo_field='redo is present for a replacement receipt and binds the invalidation receipt by SHA')
    if method == 'pgo':
        result['method'] = method
        result['receipt_details'] = description['outputs']
        if name in ('measure','report'):
            result['comparisons'] = pgo.comparison_metadata()
    if name in host_build.BUILD_STAGES:
        result['receipt_fields'] = [*RECEIPT_FIELDS, 'gbs_waits (when GBS was attempted)']
        result['gbs_waits'] = dict(
            binding=['file', 'sha256', 'record'], invocation=['path', 'workflow', 'stage', 'invocation',
                'owner', 'started_utc', 'ended_utc', 'released', 'limits_seconds', 'waited_seconds', 'outcome'],
            owner=['workflow', 'stage', 'pid', 'started_utc'], checks={
                'shared-lock': ['time_utc', 'ready', 'observed_owner (when held by a peer)'],
                'other-builds': ['time_utc', 'ready', 'processes: PID, user, start time, cwd, argv, unavailable fields'],
                'resources': ['time_utc', 'ready', 'readings: MemAvailable, load1, disk_free']})
    return result
