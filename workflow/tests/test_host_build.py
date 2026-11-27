"""Synthetic GBS calls with real flock files and a virtual wait clock."""
from contextlib import redirect_stderr, redirect_stdout
import fcntl
import io
import json
import os
from pathlib import Path
import signal
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from afdo_wf import build, cli, host_build, scheduler
from afdo_wf.common import GateError, StopRequested, json_load, require, save, sha256
from afdo_wf.receipts import Store

READY = dict(mem_available=16*build.GIB, load1=11.99, disk_free=50*build.GIB)
LOW = {**READY, 'mem_available': 16*build.GIB-1}
BUILDER = dict(pid=222, user='other-user', started_utc='2026-11-24T12:00:00+00:00',
               cwd='/build', argv=['rpmbuild', '-ba', 'other.spec'])


class SharedBuildLock(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory(dir=os.environ['TMPDIR'])
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.lock = host_build.lock_path(self.root)
        self.output = self.root / 'execution'
        self.lock.parent.mkdir()
        self.now = 0
        self.sleeps = []
        self.on_sleep = lambda: None
        self.builders = self.patch(host_build, 'active_builds', return_value=[])
        self.resources = self.patch(build, 'resources', return_value=READY)
        self.patch(host_build.time, 'monotonic', side_effect=lambda: self.now)
        self.patch(host_build.time, 'sleep', side_effect=self.sleep)
        self.launch = self.patch(build.subprocess, 'Popen', side_effect=self.synthetic_scope)
        self.systemctl = self.patch(build.subprocess, 'run')

    def patch(self, module, name, **kwargs):
        mock = patch.object(module, name, **kwargs)
        self.addCleanup(mock.stop)
        return mock.start()

    def sleep(self, delay):
        self.sleeps.append(delay)
        self.now += delay
        self.on_sleep()

    def run_build(self, **kwargs):
        return build.execute(['gbs', 'build'], self.root, self.root, self.output,
                             workflow='synthetic', **kwargs)

    def synthetic_scope(self, argv, **kwargs):
        self.assertEqual(argv[-2:], ['gbs', 'build'])
        with self.lock.open('a+') as observer:
            with self.assertRaises(BlockingIOError):
                fcntl.flock(observer, fcntl.LOCK_EX | fcntl.LOCK_NB)
        receipt = Path(argv[-3])
        save(receipt, dict(exit_code=0, memory_peak=0))
        return Mock(returncode=0, **{'poll.return_value': 0})

    def record(self):
        return json_load(self.output / host_build.WAIT_FILE)

    def assert_released(self):
        with self.lock.open('a+') as peer:
            fcntl.flock(peer, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def test_default_and_configured_path(self):
        self.assertEqual(self.lock, self.root/'temp/host-gbs.lock')
        self.lock = self.root/'temp/custom.lock'
        self.assertEqual(self.run_build(host={'gbs_lock': 'temp/custom.lock'}, stage='rebuild')['status'], 'success')
        record = self.record()
        self.assertEqual(record['path'], str(self.lock))
        self.assertEqual(record['owner']['stage'], 'rebuild')
        self.assertTrue(record['owner']['started_utc'].endswith('+00:00'))
        self.assert_released()

    def test_waits_for_existing_flock_without_replacing_file(self):
        with self.lock.open('w+') as owner:
            inode = self.lock.stat().st_ino
            owner.write('kernel build owner\n')
            owner.flush()
            fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.on_sleep = lambda: fcntl.flock(owner, fcntl.LOCK_UN)
            self.assertEqual(self.run_build()['status'], 'success')
        entry = self.record()['checks'][0]
        self.assertEqual(entry['observed_owner'], 'kernel build owner')
        self.assertEqual(self.sleeps, [600])
        self.assertEqual(inode, self.lock.stat().st_ino)
        self.assert_released()

    def timing(self):
        return host_build.BuildCoordination(self.lock, self.root / 'timing.json',
                                            'synthetic', 'measure', 'timing', shared=True)

    def test_two_timing_holders_share_without_rewriting_lock_metadata(self):
        self.lock.write_text('last exclusive owner\n')
        with self.lock.open() as other:
            fcntl.flock(other, fcntl.LOCK_SH)
            timing = self.timing()
            try:
                timing.acquire()
                self.assertEqual(timing.record['mode'], 'shared')
                self.assertEqual(self.lock.read_text(), 'last exclusive owner\n')
                with self.assertRaises(BlockingIOError):
                    self.assert_released()
            finally:
                timing.finish(None)
            self.assertEqual(self.sleeps, [])
        self.assert_released()

    def test_build_waits_for_timing_holder_to_release(self):
        with self.lock.open('a+') as other:
            fcntl.flock(other, fcntl.LOCK_SH)
            self.on_sleep = lambda: fcntl.flock(other, fcntl.LOCK_UN)
            self.assertEqual(self.run_build()['status'], 'success')
        self.assertEqual(self.sleeps, [600])
        self.assertEqual([row['ready'] for row in self.record()['checks'][:2]], [False, True])
        self.assertEqual(self.record()['mode'], 'exclusive')
        self.assert_released()

    def test_timing_waits_for_exclusive_holder_to_release(self):
        with self.lock.open('a+') as other:
            fcntl.flock(other, fcntl.LOCK_EX)
            self.on_sleep = lambda: fcntl.flock(other, fcntl.LOCK_UN)
            timing = self.timing()
            try:
                timing.acquire()
                self.assertEqual([row['ready'] for row in timing.record['checks']], [False, True])
            finally:
                timing.finish(None)
        self.assertEqual(self.sleeps, [600])
        self.assert_released()

    def test_lock_holder_timeout_does_not_change_peer(self):
        self.patch(host_build, 'COORDINATION_LIMIT', new=601)
        with self.lock.open('w+') as owner:
            owner.write('{"workflow":"kernel","pid":1234}\n')
            owner.flush()
            fcntl.flock(owner, fcntl.LOCK_EX)
            self.assertEqual(self.run_build()['reason'], 'lock-timeout')
            self.assertEqual(json_load(self.lock)['workflow'], 'kernel')
        self.assertEqual(self.sleeps, [600, 1])
        self.assertFalse(self.record()['released'])
        self.launch.assert_not_called()

    def test_external_build_waits_then_starts(self):
        self.builders.side_effect = [[BUILDER], []]
        self.assertEqual(self.run_build()['status'], 'success')
        self.assertEqual(self.sleeps, [600])
        self.assertEqual(self.record()['checks'][1]['processes'], [BUILDER])
        self.assert_released()

    def test_combined_lock_and_external_build_timeout(self):
        self.patch(host_build, 'COORDINATION_LIMIT', new=1000)
        with self.lock.open('a+') as owner:
            fcntl.flock(owner, fcntl.LOCK_EX)
            self.on_sleep = lambda: fcntl.flock(owner, fcntl.LOCK_UN)
            self.builders.return_value = [BUILDER]
            self.assertEqual(self.run_build()['reason'], 'lock-timeout')
        self.assertEqual(self.sleeps, [600, 400])
        self.assertEqual(self.record()['waited_seconds']['coordination'], 1000)
        self.launch.assert_not_called()
        self.assert_released()

    def test_waits_for_resources_and_rechecks_builders(self):
        self.resources.side_effect = [LOW, READY]
        self.builders.side_effect = [[], [BUILDER], []]
        result = self.run_build()
        self.assertEqual(result['start_resources'], READY)
        self.assertEqual(self.sleeps, [600, 600])
        self.assertEqual(self.record()['waited_seconds'], dict(coordination=600, resources=600))
        self.assert_released()

    def test_resource_timeout_reports_gate(self):
        self.patch(host_build, 'RESOURCE_LIMIT', new=1201)
        self.resources.return_value = LOW
        self.assertEqual(self.run_build()['reason'], 'gate')
        self.assertEqual(self.sleeps, [600, 600, 1])
        self.assertEqual(self.record()['checks'][-1]['readings'], LOW)
        self.launch.assert_not_called()
        self.assert_released()

    def test_cancellation_while_waiting_releases_lock(self):
        self.builders.return_value = [BUILDER]
        previous = signal.getsignal(signal.SIGTERM)
        self.on_sleep = lambda: signal.raise_signal(signal.SIGTERM)
        self.assertEqual(self.run_build()['reason'], 'user-abort')
        self.assertEqual(signal.getsignal(signal.SIGTERM), previous)
        self.launch.assert_not_called()
        self.assert_released()

    def test_cancellation_after_launch_stops_only_own_scope_then_releases(self):
        self.launch.side_effect = None
        child = Mock(**{'poll.return_value': None, 'wait.side_effect': [StopRequested(signal.SIGTERM), 143]})
        self.launch.return_value = child
        def systemctl(argv, **kwargs):
            with self.lock.open('a+') as peer:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(peer, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return subprocess.CompletedProcess(argv, 0, '', '')
        self.systemctl.side_effect = systemctl
        result = self.run_build()
        self.assertEqual(result['reason'], 'user-abort')
        self.assertEqual(result['exit_code'], 143)
        self.assertEqual(self.systemctl.call_args.args[0], ['systemctl', '--user', 'stop', result['unit']])
        self.assert_released()

    def test_child_failure_releases_lock(self):
        def fail(argv, **kwargs):
            save(Path(argv[-3]), dict(exit_code=55, memory_peak=42))
            return Mock(returncode=55, **{'poll.return_value': 55})
        self.launch.side_effect = fail
        result = self.run_build()
        self.assertEqual((result['reason'], result['exit_code']), ('environment', 55))
        self.assertEqual(self.record()['outcome'], 'environment')
        self.assert_released()

    def test_failed_receipt_status_and_cli_exit_8(self):
        self.patch(host_build, 'COORDINATION_LIMIT', new=0)
        self.builders.return_value = [BUILDER]
        job = self.root/'job.json'
        receipts = self.root/'receipts'
        save(job, dict(package='synthetic', workdir=str(self.root), output=str(self.root),
                       receipts=str(receipts)))
        store = Store(receipts)
        store.complete('preflight', [], [])
        def handler(out, store):
            self.output = out/'execution'
            result = self.run_build()
            require(result['status'] == 'success', result['error'], result['reason'])
        def host_run(*args):
            scheduler.execute(['build'], {'build': handler}, self.root/'stages', receipts, [])
        self.patch(cli, 'host_run', side_effect=host_run)
        with redirect_stderr(io.StringIO()) as err:
            self.assertEqual(cli.main(['build', '--job', str(job)]), 8)
        self.assertIn('lock-timeout [8]', err.getvalue())
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cli.main(['status', '--job', str(job)]), 0)
        failure = json.loads(out.getvalue())['stages']['build']['last_failure']
        self.assertEqual(failure['exit_code'], 8)
        wait = failure['gbs_waits'][0]
        self.assertEqual(wait['sha256'], sha256(wait['file']))
        self.assertEqual(wait['record']['checks'][-1]['processes'], [BUILDER])
        self.assert_released()

    def test_completed_receipt_and_explain_expose_waits(self):
        receipts = self.root/'receipts'
        store = Store(receipts)
        store.complete('preflight', [], [])
        def handler(out, _store):
            self.output = out/'execution'
            return self.run_build()
        scheduler.execute(['build'], {'build': handler}, self.root/'stages', receipts, [])
        receipt = store.verify('build')
        wait = receipt['gbs_waits'][0]
        self.assertEqual(receipt['outputs'][wait['file']], wait['sha256'])
        self.assertEqual(cli.job_commands.status(self.root, receipts)['stages']['build']['gbs_waits'], [wait])
        for stage in ('build', 'rebuild'):
            self.assertIn('resources', cli.job_commands.explain(stage)['gbs_waits']['checks'])


class OtherProcessEvidence(unittest.TestCase):
    def test_reads_processes_by_name_or_script_and_skips_unrelated_argv(self):
        with TemporaryDirectory(dir=os.environ['TMPDIR']) as d:
            proc = Path(d)
            (proc/'stat').write_text('btime 1700000000\n')
            for index, (name, argv, state) in enumerate([
                ('rpmbuild', b'/bin/rpmbuild\0-ba\0some.spec\0', 'S'),
                ('python3', b'python3\0/home/bin/gbs\0https://user:token@example.invalid\0', 'S'),
                ('bash', b'bash\0gbs\0', 'S'),
                ('rpmbuild', b'', 'Z'),
            ], 101):
                directory = proc/str(index)
                directory.mkdir()
                (directory/'comm').write_text(name + '\n')
                (directory/'cmdline').write_bytes(argv)
                (directory/'status').write_text(f'Uid: 0\t{os.getuid()}\t0\t0\n')
                (directory/'stat').write_text(f'{index} ({name}) {state} ' + '0 '*18 + '100 0\n')
                if index != 102:
                    (directory/'cwd').symlink_to(proc)
            rows = host_build.active_builds(proc)
            self.assertEqual([row['executable'] for row in rows], ['rpmbuild', 'gbs'])
            self.assertEqual(rows[0]['cwd'], str(proc))
            self.assertEqual(rows[0]['uid'], os.getuid())
            self.assertTrue(rows[0]['started_utc'].startswith('2023-11-14T22:13:'))
            self.assertEqual(rows[1]['argv'][-1], 'https://<redacted>@example.invalid')
            self.assertIn('cwd', rows[1]['unavailable'])
