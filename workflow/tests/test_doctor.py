"""The startup version check and diagnostic command without live tools."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from afdo_wf import build, cli, doctor
from afdo_wf.common import save, sha256


class PythonStartup(unittest.TestCase):
    def test_unsupported_python_reports_environment_before_importing_cli(self):
        source = """
import importlib.abc
import runpy
import sys

class RefuseCLI(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname in ('afdo_wf.cli', 'tomllib'):
            raise AssertionError('imported before version check: ' + fullname)

sys.meta_path.insert(0, RefuseCLI())
sys.version_info = (3, 10, 9, 'final', 0)
runpy.run_module('afdo_wf', run_name='__main__')
"""
        result = subprocess.run([sys.executable, '-c', source], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 4)
        self.assertIn('environment [4] afdo_wf requires Python 3.11 or newer (found 3.10.9)', result.stderr)
        self.assertFalse(result.stdout)


class DoctorTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory(dir=os.environ['TMPDIR'])
        self.addCleanup(directory.cleanup)
        self.workdir = Path(directory.name)
        self.ready = dict(mem_available=16*build.GIB, load1=11.99, disk_free=50*build.GIB)

    def test_reports_installed_host_tools_and_exact_resources(self):
        with patch.object(doctor.shutil, 'which', side_effect=lambda tool: '/usr/bin/' + tool), \
                patch.object(doctor.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'version 1\n', '')) as run, \
                patch.object(build, 'resources', return_value=self.ready):
            result = doctor.inspect(self.workdir)
        self.assertEqual([c.args[0] for c in run.call_args_list], [
            ['/usr/bin/git', '--version'], ['/usr/bin/sdb', 'version'], ['/usr/bin/gbs', '--version']])
        self.assertEqual({row['check'] for row in result['ok']},
                         {'python', 'git', 'sdb', 'gbs', 'mem_available', 'load1', 'disk_free'})
        self.assertTrue(all(not result[key] for key in ('missing', 'mismatch', 'unknown')))
        self.assertFalse(list(self.workdir.iterdir()))

    def test_missing_executable_and_failed_or_timed_out_version_queries(self):
        with patch.object(doctor.shutil, 'which', side_effect=[None, '/usr/bin/sdb', '/usr/bin/gbs']), \
                patch.object(doctor.subprocess, 'run', side_effect=[
                    subprocess.TimeoutExpired(['sdb', 'version'], 10), subprocess.CompletedProcess([], 2, '', '')]), \
                patch.object(build, 'resources', return_value=self.ready):
            result = doctor.inspect(self.workdir)
        self.assertEqual([row['check'] for row in result['missing']], ['git'])
        self.assertEqual([row['check'] for row in result['unknown']], ['sdb', 'gbs'])

    def test_resource_gate_boundary_mismatches(self):
        low = dict(mem_available=16*build.GIB-1, load1=12, disk_free=50*build.GIB-1)
        with patch.object(doctor.shutil, 'which', return_value=None), patch.object(build, 'resources', return_value=low):
            result = doctor.inspect(self.workdir)
        self.assertFalse(build.can_start(low))
        self.assertEqual({row['check']: row['value'] for row in result['mismatch']}, low)

    def test_optional_job_locks_reports_missing_mismatch_and_malformed(self):
        local = self.workdir/'perf'
        local.write_bytes(b'contents')
        actual = sha256(local)
        expected = '0'*64
        job = dict(tools={
            'profgen': dict(path=str(local), sha256=actual),
            'profdata': dict(path=str(self.workdir/'absent'), sha256=expected),
            'loader': dict(path=str(local), sha256=expected),
            'libLLVM': dict(path=str(local), sha256='invalid'),
        }, board_tools=[dict(source=str(local), sha256=actual)])
        with patch.object(doctor.shutil, 'which', return_value=None), patch.object(build, 'resources', return_value=self.ready):
            result = doctor.inspect(self.workdir, job)
        self.assertTrue({'tools.profgen', 'board_tools[0]'} <= {row['check'] for row in result['ok']})
        self.assertIn('tools.profdata', {row['check'] for row in result['missing']})
        self.assertEqual(result['mismatch'][0]['check'], 'tools.loader')
        self.assertEqual(result['mismatch'][0]['sha256'], actual)
        self.assertEqual(result['unknown'][0]['check'], 'tools.libLLVM')

    def test_draft_locks_and_unavailable_host_resources_are_unknown(self):
        with patch.object(doctor.shutil, 'which', return_value=None), patch.object(build, 'resources', side_effect=OSError('fixture')):
            result = doctor.inspect(self.workdir, {'draft': True})
        self.assertEqual({row['check'] for row in result['unknown']}, {'host_resources', 'tools', 'board_tools'})

    def test_cli_doctor_reads_job_without_receipts_or_stage_execution(self):
        path = self.workdir/'job.json'
        save(path, dict(workdir=str(self.workdir), output=str(self.workdir/'run')))
        with redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()) as errors, \
                patch.object(cli, 'execute', side_effect=AssertionError('would run a stage')), \
                patch.object(doctor.shutil, 'which', return_value=None), patch.object(build, 'resources', return_value=self.ready) as sample:
            self.assertEqual(cli.main(['doctor', '--job', str(path)]), 0)
        sample.assert_called_once_with(self.workdir)
        self.assertEqual(set(json.loads(output.getvalue())), {'ok', 'missing', 'mismatch', 'unknown'})
        self.assertFalse(errors.getvalue())
        self.assertEqual(list(self.workdir.iterdir()), [path])
