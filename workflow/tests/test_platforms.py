from contextlib import nullcontext
from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch

from afdo_wf import build, config, live, platforms
from afdo_wf.common import GateError, json_load
from afdo_wf.receipts import Store


class PlatformTests(unittest.TestCase):
    def test_rpi5_layout_and_collection_override(self):
        board = platforms.load('rpi5-aarch64')
        self.assertEqual(board.arch, 'aarch64')
        self.assertEqual(board.isas, ['a64'])
        self.assertEqual(board.runtime_environment('/variant', '/tools'), '/variant/usr/lib64:/tools/lib')
        self.assertEqual(str(Path(board.debug_root) / 'usr/lib64/libavcodec.so.debug'),
                         'usr/lib/debug/usr/lib64/libavcodec.so.debug')
        self.assertEqual(board.cpu, 3)
        self.assertEqual(board.sampling_period({'collect': {'period': 33, 'rpi5': {'period': 1000003}}}),
                         1000003)
        package = config.load(Path(live.__file__).resolve().parents[1] / 'packages/ffmpeg/package-rpi5.toml')
        self.assertEqual(package['build_units'][0]['isa'], 'a64')
        self.assertTrue(all(target['package_path'].startswith(board.runtime_lib+'/')
                            for target in package['targets']))

    def test_gcc_support_paths_follow_each_platform_abi(self):
        for name, runtime_lib, gcc_support in [
            ('rpi4-armv7l', 'usr/lib', 'usr/lib/gcc'),
            ('rpi5-aarch64', 'usr/lib64', 'usr/lib64/gcc'),
        ]:
            with self.subTest(platform=name):
                board = platforms.load(name)
                self.assertEqual(board.runtime_lib, runtime_lib)
                self.assertEqual(board.gcc_support, gcc_support)

    def test_same_address_or_alias_does_not_validate_wrong_hardware(self):
        board = platforms.load('rpi5-aarch64')
        board.check_identity({'model': 'Raspberry Pi 5 Model B Rev 1.1', 'arch': 'aarch64'})
        for given in [{'model': 'Raspberry Pi 5 Model B', 'arch': 'armv7l'},
                      {'model': 'Novatek TV', 'arch': 'aarch64'},
                      {'model': 'Raspberry Pi 4 Model B', 'arch': 'aarch64'}]:
            with self.subTest(given=given), self.assertRaises(GateError):
                board.check_identity(given)

    def test_stop_at_audit_and_resume_verifies_receipts(self):
        with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as directory:
            output = Path(directory)
            files = {}
            for name in ('job', 'patch', 'package', 'inputs', 'config', 'snapshot_evidence', 'spec'):
                files[name] = output/name
                files[name].write_text(name)
            runner = object.__new__(live.Experiment)
            runner.d = output
            runner.w = output
            runner.code = output
            runner.platform = platforms.load('rpi5-aarch64')
            runner.platform_name = 'rpi5-aarch64'
            runner.job_path = files['job']
            runner.package = {'build_units': [{'spec': 'spec'}]}
            runner.job = {key: str(value) for key, value in files.items()}
            runner.job.update(platform='rpi5-aarch64', board_tools=[], source=str(output))
            runner.session = nullcontext
            runner.ensure_work = lambda: None
            runner.restore_host_artifacts = lambda: None
            runner.cleanup = type('CleanupStub', (), {'data': {'cleanup_pending': []}})()
            calls = []
            for name in ('preflight', 'build_base', 'deploy', 'collect', 'convert', 'rebuild', 'measure', 'report'):
                def handler(out, store, name=name):
                    calls.append(name)
                    return {'executed': name}
                setattr(runner, name, handler)
            with patch.object(build, 'wait_for_host'):
                runner.run('rebuild')
                self.assertEqual(calls, ['preflight', 'build_base', 'deploy', 'collect', 'convert', 'rebuild'])
                self.assertFalse((output/'receipts/measure.json').exists())
                self.assertEqual(json_load(output/'progress.json')['status'], 'stopped')
                self.assertEqual(Store(output/'receipts').verify('rebuild')['details'], {'executed': 'rebuild'})
                runner.run()
            self.assertEqual(calls[-2:], ['measure', 'report'])
            self.assertEqual(calls.count('rebuild'), 1)
            self.assertEqual(Store(output/'receipts').verify('report')['status'], 'complete')

    def test_host_gate_waits_on_external_gbs_then_memory(self):
        with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as directory:
            result = Path(directory)/'gate.json'
            ready = dict(mem_available=17*build.GIB, load1=1, nproc=10, disk_free=60*build.GIB)
            samples = [ready.copy(), {**ready, 'mem_available': 15*build.GIB}, ready.copy()]
            with patch.object(build, 'resources', side_effect=samples), \
                 patch.object(build.host_build, 'active_builds', side_effect=[[{'pid': 7, 'executable': 'gbs'}], [], []]), \
                 patch.object(build.time, 'sleep') as sleep:
                build.wait_for_host(directory, result, exclusive=True)
            self.assertEqual([args.args[0] for args in sleep.call_args_list], [600, 600])
            log = json_load(result)
            self.assertEqual(len(log['samples']), 3)
            self.assertEqual(log['status'], 'ready')
            self.assertEqual(log['samples'][0]['other_builds'][0]['pid'], 7)
