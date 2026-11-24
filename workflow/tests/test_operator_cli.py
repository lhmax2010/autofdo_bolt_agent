"""Host-only CLI contracts. Transport and build work are synthetic."""
from contextlib import redirect_stderr, redirect_stdout
import fcntl
import io
import json
import os
from pathlib import Path
import signal
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from afdo_wf import cli, config, live, scheduler
from afdo_wf.common import GateError, StopRequested, json_load, save, sha256
from afdo_wf.exits import EXIT_CODES
from afdo_wf.receipts import Store
from afdo_wf.stages import DAG, RUN_STAGES
from afdo_wf.transport import SDB

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'packages/ffmpeg/package.toml'


class WorkflowCLI(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory(dir=os.environ['TMPDIR'])
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.output = self.root / 'out'
        self.receipts = self.output / 'receipts'
        self.job = self.root / 'job.json'
        save(self.job, dict(package=str(PACKAGE), output=str(self.output), receipts=str(self.receipts)))
        self.input = self.root / 'input'
        self.input.write_text('original')

    def invoke(self, *args):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = cli.main(args)
        return result, json.loads(stdout.getvalue()) if stdout.getvalue() else None, stderr.getvalue()

    def chain(self, stages=RUN_STAGES):
        store = Store(self.receipts)
        for stage in stages:
            store.complete(stage, [self.input], [], {})
        return store

    def snapshot(self):
        return {p.relative_to(self.root): (p.stat().st_mtime_ns, sha256(p))
                for p in self.root.rglob('*') if p.is_file()}

    def test_status_pending_without_creating_directories(self):
        before = self.snapshot()
        rc, view, _ = self.invoke('status', '--job', str(self.job))
        self.assertEqual(rc, 0)
        self.assertEqual(set(view['stages']), set(DAG))
        self.assertTrue(all(row['status']=='pending' for row in view['stages'].values()))
        self.assertFalse(self.output.exists())
        self.assertEqual(self.snapshot(), before)

    def test_status_inputs_dependency_failure_and_cleanup(self):
        store = self.chain(['preflight','build'])
        store.failed('deploy', GateError('DSO mismatch', 'identity'))
        save(self.output/'cleanup.json', {'cleanup_pending':[{'kind':'root'}]})
        before = self.snapshot()
        rc, view, _ = self.invoke('status', '--job', str(self.job))
        self.assertEqual(rc, 0)
        rows = view['stages']
        self.assertEqual(rows['build']['status'], 'completed')
        self.assertEqual(rows['build']['input_sha'], 'match')
        self.assertEqual(rows['deploy']['status'], 'failed')
        self.assertEqual(rows['deploy']['last_failure']['reason'], 'identity')
        self.assertTrue(Path(rows['deploy']['receipt']).is_file())
        self.assertEqual(rows['restore']['status'], 'cleanup_pending')
        self.assertEqual(rows['restore']['reason'], 'recovery-required')
        self.assertEqual(self.snapshot(), before)
        self.input.write_text('changed')
        _, view, _ = self.invoke('status', '--job', str(self.job))
        self.assertEqual(view['stages']['preflight']['status'], 'invalidated')
        self.assertEqual(view['stages']['build']['upstream_sha'], 'mismatch')
        self.assertEqual(view['stages']['preflight']['mismatched_inputs'], [str(self.input)])

    def test_status_does_not_parse_archived_stage_outputs(self):
        store=Store(self.receipts)
        output=self.root/'stage-output'
        output.write_text('bytes are verified only on resume')
        store.complete('preflight', [self.input], [output])
        output.unlink()
        _, info, _ = self.invoke('status', '--job', str(self.job))
        self.assertEqual(info['stages']['preflight']['input_sha'], 'match')
        with self.assertRaises(GateError):
            store.verify('preflight')

    def test_redo_archives_exact_bytes_and_replays_only_descendants(self):
        store = self.chain()
        store.failed('rebuild', GateError('old failure'))
        originals = {stage: store.path(stage).read_bytes() for stage in RUN_STAGES}
        rc, redo, _ = self.invoke('--redo', 'collect', '--reason', 'new sampling site', '--job', str(self.job))
        affected = ['collect','convert','rebuild','measure','report']
        self.assertEqual(rc, 0)
        self.assertEqual(redo['stages'], affected)
        archive = Path(redo['receipt'])
        record = json_load(archive)
        self.assertEqual(record['reason'], 'new sampling site')
        self.assertEqual(record['status'], 'invalidated')
        self.assertRegex(archive.parent.name, r'^\d{8}T\d{6}\.\d+Z-')
        for stage in affected:
            self.assertEqual((archive.parent/store.path(stage).name).read_bytes(), originals[stage])
            with self.assertRaises(GateError):
                store.verify(stage)
        fail = record['stages']['rebuild']['archived'][1]
        self.assertEqual(sha256(archive.parent/fail['archive']), fail['sha256'])
        _, status, _ = self.invoke('status', '--job', str(self.job))
        self.assertEqual([name for name in RUN_STAGES if status['stages'][name]['status']=='invalidated'], affected)
        rc, plan, _ = self.invoke('run', '--job', str(self.job), '--dry-run')
        self.assertEqual(rc, 0)
        self.assertEqual([row['stage'] for row in plan['stages'] if row['action']=='run'], affected + ['restore'])
        calls = []
        handlers = {stage: (lambda out, receipts, stage=stage: calls.append(stage) or {'rerun':stage})
                    for stage in RUN_STAGES}
        scheduler.execute(RUN_STAGES, handlers, self.output/'stages', self.receipts, [self.input])
        self.assertEqual(calls, affected)
        self.assertEqual(store.verify('report')['redo']['receipt'], str(archive))
        self.assertEqual(store.verify('report')['redo']['sha256'], sha256(archive))
        self.assertEqual(store.path('deploy').read_bytes(), originals['deploy'])
        self.assertEqual((archive.parent/'collect.json').read_bytes(), originals['collect'])

    def test_redo_fails_atomically_if_manifest_write_fails(self):
        store = self.chain()
        with patch('afdo_wf.receipts.save', side_effect=OSError('no space')):
            with self.assertRaises(OSError):
                store.redo('build')
        self.assertEqual(store.redo_bindings(), {})
        self.assertEqual(store.verify('report')['status'], 'complete')

    def test_redo_refuses_conflicting_dry_run_or_pending_cleanup(self):
        self.assertEqual(self.invoke('run','--job',str(self.job),'--dry-run','--redo','build')[0], 64)
        self.assertFalse(self.output.exists())
        save(self.output/'cleanup.json', {'cleanup_pending':[{'kind':'root'}]})
        self.assertEqual(self.invoke('--redo','build','--job',str(self.job))[0], 7)
        self.assertFalse((self.receipts/'redo').exists())

    def test_lock_timeout_without_changing_receipts(self):
        store = self.chain()
        lock_path = self.receipts / '.writer.lock'
        with lock_path.open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.invoke('--redo','build','--job',str(self.job))[0], 8)
        self.assertEqual(store.verify('report')['status'], 'complete')

    def test_live_dry_run_does_not_construct_runner(self):
        inputs = ROOT / 'packages/ffmpeg/inputs.toml'
        save(self.job, dict(live=True, package=str(PACKAGE), inputs=str(inputs), output=str(self.output)))
        before = self.snapshot()
        with patch('afdo_wf.live.Experiment', side_effect=AssertionError('would touch board')), \
             patch('afdo_wf.build.execute', side_effect=AssertionError('would build')):
            rc, plan, _ = self.invoke('run', '--job', str(self.job), '--dry-run', '--stop-after','afdo-audit')
        self.assertEqual(rc, 0)
        self.assertEqual(plan['stages'][-1]['stage'], 'rebuild')
        self.assertFalse(plan['board_contact'])
        collect = next(row for row in plan['stages'] if row['stage']=='collect')
        self.assertEqual([r['role'] for r in collect['declared_inputs']['media']], ['train'])
        self.assertTrue(collect['board_actions_this_stage'])
        self.assertFalse(self.output.exists())
        self.assertEqual(self.snapshot(), before)

    def test_explain_matches_planning_and_receipt_fields(self):
        rc, details, _ = self.invoke('explain', 'afdo-audit')
        self.assertEqual(rc, 0)
        self.assertEqual(details['stage'], 'rebuild')
        self.assertEqual(details['dependencies'], DAG['rebuild'])
        self.assertTrue(set(details['receipt_fields']) >= {'inputs','outputs','upstream'})
        rc, plan, _ = self.invoke('run', '--dry-run', '--job', str(self.job))
        self.assertEqual(rc, 0)
        self.assertEqual(next(row['gates'] for row in plan['stages'] if row['stage']=='rebuild'), details['gates'])

    def make_inputs(self, roles, starts=None):
        path = self.root / 'inputs.toml'
        starts = starts or [0]*len(roles)
        rows = []
        for idx, (role, start) in enumerate(zip(roles, starts)):
            name = f'clip-{idx}'
            (self.root/name).write_text('same clip')
            rows.append(f'''[[inputs]]
id = "{name}"
path = "/opt/afdo_agent/inputs/{name}"
sha256 = "{sha256(self.root/name)}"
start = {start}
duration = 10
role = "{role}"
oracle = {{caps = "I420", threads = 1, frames = 10, bytes = 100, digest = "{'0'*64}"}}''')
        path.write_text('\n'.join(rows))
        return path

    def init(self, inputs, platform='rpi4-armv7l'):
        return self.invoke('init','--job',str(self.root/'draft.json'),'--package',str(PACKAGE),
                           '--inputs',str(inputs),'--output',str(self.output),'--workdir',str(self.root),
                           '--platform',platform,'--media-dir',str(self.root))

    def test_init_creates_validated_draft_without_running_or_overwriting(self):
        inputs = self.make_inputs(['train','tuning','test'], [0,10,20])
        rc, doc, _ = self.init(inputs)
        self.assertEqual(rc, 0)
        draft = json_load(doc['job'])
        self.assertTrue(draft['draft'])
        self.assertEqual(set(draft['media']), {'clip-0','clip-1','clip-2'})
        self.assertEqual(draft['config_sha256']['inputs']['sha256'], sha256(inputs))
        self.assertFalse(self.output.exists())
        self.assertEqual(self.init(inputs)[0], 2)
        self.assertEqual(self.invoke('run','--job',doc['job'])[0], 2)
        self.assertEqual(self.invoke('run','--job',doc['job'],'--dry-run')[0], 0)

    def test_init_rejects_all_cross_role_overlaps(self):
        for roles in (['train','tuning','test'], ['train','test','test-secondary']):
            with self.subTest(roles=roles):
                inputs = self.make_inputs(roles)
                self.assertEqual(self.init(inputs)[0], 2)
                self.assertFalse((self.root/'draft.json').exists())
        inputs = self.make_inputs(['train','tuning','test'], [0,10,11])
        self.assertEqual(self.init(inputs)[0], 2)

    def test_init_checks_architecture_path_and_content(self):
        inputs = self.make_inputs(['train','test'], [0,10])
        self.assertEqual(self.init(inputs, 'rpi5-aarch64')[0], 2)
        (self.root/'clip-1').write_text('bad SHA')
        self.assertEqual(self.init(inputs)[0], 3)
        (self.root/'clip-1').unlink()
        self.assertEqual(self.init(inputs)[0], 2)
        self.assertFalse((self.root/'draft.json').exists())

    def test_exit_contract_written_to_failure_receipts(self):
        errors = {reason:GateError('failure', reason) for reason in ('gate','identity','environment',
                  'correctness','board-unreachable','recovery-required','lock-timeout')}
        errors.update(error=RuntimeError('unexpected'), **{'user-abort': StopRequested(signal.SIGTERM)})
        self.assertEqual(len(set(EXIT_CODES.values())), len(EXIT_CODES))
        for reason, exc in errors.items():
            with self.subTest(reason=reason), patch('afdo_wf.cli.host_stage', side_effect=exc):
                rc, _, stderr = self.invoke('preflight','--job',str(self.job))
                self.assertEqual(rc, EXIT_CODES[reason])
                self.assertIn(reason + ' [', stderr)
                status = self.invoke('status','--job',str(self.job))[1]
                self.assertEqual(status['stages']['preflight']['last_failure']['reason'], reason)
        self.assertEqual(self.invoke('status')[0], 64)

    def test_cleanup_pending_exit_preserves_original_cause(self):
        def abort(*args):
            save(self.output/'cleanup.json', {'cleanup_pending':[{'kind':'root'}]})
            raise GateError('offline', 'board-unreachable')
        with patch('afdo_wf.cli.host_stage', side_effect=abort):
            self.assertEqual(self.invoke('preflight','--job',str(self.job))[0], 7)
        view = self.invoke('status','--job',str(self.job))[1]
        self.assertEqual(view['last_run_failure']['reason'], 'recovery-required')
        self.assertEqual(view['last_run_failure']['cause']['reason'], 'board-unreachable')

    def test_transport_error_retains_typed_unreachable(self):
        from subprocess import CompletedProcess
        sender = lambda args, **kw: CompletedProcess(args, 1, b'', b'error: target not found')
        t = SDB('synthetic', self.root/'transport', runner=sender)
        with self.assertRaises(GateError) as caught:
            t.shell('true', readonly=True)
        self.assertEqual(caught.exception.reason, 'board-unreachable')

    def test_redo_prunes_only_artifacts_from_invalidated_attempts(self):
        store = Store(self.receipts)
        run = object.__new__(live.Experiment)
        run.d = self.output
        run.b = '/opt/afdo_agent'
        run.job = {'experiment':'synthetic'}
        run.remote = run.b + '/work/synthetic'
        def file(stage, name):
            path = self.output / 'stages' / stage / '001' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(name)
            return dict(kind='file', source=str(path), sha256=sha256(path))
        baseline = file('deploy','BASE.tar')
        candidate = file('rebuild','AFDO.tar')
        manifest = file('rebuild','AFDO-manifest.json')
        for stage in RUN_STAGES:
            extras = {'deploy':[baseline['source']], 'rebuild':[candidate['source'],manifest['source']]}
            store.complete(stage, [self.input], extras.get(stage, []))
        tar = lambda item: dict(members={'':item}, directory=False)
        variant = dict(members={'lib.so':candidate}, directory=True)
        registry = {
            run.remote+'/BASE.tar': tar(baseline),
            run.remote+'/AFDO.tar': tar(candidate),
            run.b+'/variants/synthetic-BASE': variant,
            run.b+'/variants/synthetic-AFDO': variant,
            run.b+'/tools/workflow-synthetic':dict(members={'AFDO-manifest.json':manifest},directory=True),
        }
        save(run.d/'host-artifacts.json',registry)
        store.redo('collect')
        run.prune_host_artifacts(store)
        self.assertEqual(set(json_load(run.d/'host-artifacts.json')),
                         {run.remote+'/BASE.tar', run.b+'/variants/synthetic-BASE'})
        old = next((run.d/'host-artifact-history').glob('*.json'))
        self.assertEqual(json_load(old),registry)
