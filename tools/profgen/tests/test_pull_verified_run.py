"""Host-only failure injection: no board or real deletion is involved."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('transfer', ROOT / 'tools/profgen/pull_verified_run.py')
transfer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transfer)


class VerifiedTransfer(unittest.TestCase):
    def exercise(self, case):
        remote = '/opt/afdo_agent/work/eval-injection'
        good = b'original data\n'
        manifest = hashlib.sha256(good).hexdigest() + '  ' + remote + '/data.txt\n'
        deleted = []
        with tempfile.TemporaryDirectory(prefix='transfer-test-', dir=ROOT / 'temp/tmp') as directory:
            local = Path(directory) / 'pulled'

            def pull(_remote, destination):
                if case == 'transport':
                    raise OSError('injected transport failure')
                if case != 'missing':
                    (destination / 'data.txt').write_bytes(b'changed' if case == 'bad-hash' else good)
                if case == 'extra':
                    (destination / 'extra.txt').write_bytes(good)
                if case == 'symlink':
                    (destination / 'alias').symlink_to('data.txt')

            changed = manifest.replace(hashlib.sha256(good).hexdigest(), '0' * 64)
            invoke = lambda: transfer.pull_verify_delete(
                remote, local, manifest, pull,
                lambda: changed if case == 'remote-changed' else manifest,
                deleted.append)
            if case == 'success':
                result = invoke()
                self.assertTrue(result['all_verified_before_delete'])
                self.assertEqual(deleted, [remote])
            else:
                with self.assertRaises((ValueError, OSError)):
                    invoke()
                self.assertEqual(deleted, [])

    def test_hash_mismatch_prevents_deletion(self): self.exercise('bad-hash')
    def test_missing_file_prevents_deletion(self): self.exercise('missing')
    def test_extra_file_prevents_deletion(self): self.exercise('extra')
    def test_transport_failure_prevents_deletion(self): self.exercise('transport')
    def test_symlink_prevents_deletion(self): self.exercise('symlink')
    def test_remote_change_prevents_deletion(self): self.exercise('remote-changed')
    def test_success_deletes_exact_run(self): self.exercise('success')
    def test_manifest_path_escape_is_rejected(self):
        with self.assertRaises(ValueError):
            transfer.parse_manifest('0' * 64 + '  /opt/afdo_agent/work/eval-x/../outside\n', '/opt/afdo_agent/work/eval-x')

    def test_manifest_sha_failure_propagates(self):
        # Run the actual manifest shell command locally with one failing SHA
        # command. No board connection or deletion is performed.
        class LocalSDB(transfer.SDB):
            def shell(self, command, **kwargs):
                if command.startswith('readlink -f '):
                    return str(directory)
                if command.endswith('-type l -print'):
                    return ''
                setup = 'sha256sum() { return 17; }; export -f sha256sum; '
                p = subprocess.run(['/bin/bash', '-c', setup + command],
                                   text=True, capture_output=True)
                if p.returncode:
                    raise RuntimeError('SHA failed: ' + str(p.returncode))
                return p.stdout.strip()
        with tempfile.TemporaryDirectory(prefix='manifest-test-', dir=ROOT/'temp/tmp') as name:
            directory = Path(name)
            (directory/'data').write_text('test')
            with self.assertRaisesRegex(RuntimeError, 'SHA failed'):
                LocalSDB('host-only').manifest(str(directory))



class RemoteExitRetry(unittest.TestCase):
    def run_case(self, outputs, read_only):
        with tempfile.TemporaryDirectory(dir=ROOT/'temp/tmp') as directory:
            client = transfer.SDB('fake', Path(directory)/'audit.jsonl')
            replies = [subprocess.CompletedProcess([], rc, out, 'raw-stderr') for rc, out in outputs]
            with patch.object(transfer.subprocess, 'run', side_effect=replies) as run:
                try:
                    value = client.shell('read-or-mutate', read_only=read_only)
                    error = None
                except RuntimeError as e:
                    value, error = None, str(e)
                import json
                audit = [json.loads(s) for s in client.audit_path.read_text().splitlines()]
                self.assertTrue(all(x['stderr'] == 'raw-stderr' for x in audit if x['kind']=='command'))
                return value, error, run.call_count, client.retry_count

    def test_readonly_missing_marker_then_equal(self):
        self.assertEqual(self.run_case([(0,'same\n'),(0,'same\n__RC=0\n')],True),('same',None,2,1))
    def test_two_retries_maximum(self):
        x=self.run_case([(0,'same')]*3,True); self.assertEqual(x[2:],(3,2)); self.assertIn('Missing remote exit marker',x[1])
    def test_mutation_never_retries(self):
        x=self.run_case([(0,'same')],False); self.assertEqual(x[2:],(1,0)); self.assertIsNotNone(x[1])
    def test_changed_readonly_result_refused(self):
        x=self.run_case([(0,'old'),(0,'new\n__RC=0\n')],True); self.assertIn('output changed',x[1])
    def test_nonzero_remote_not_retried(self):
        x=self.run_case([(0,'same\n__RC=9\n')],True); self.assertEqual(x[2:],(1,0))
    def test_transport_failure_not_retried(self):
        x=self.run_case([(1,'same')],True); self.assertEqual(x[2:],(1,0))

if __name__ == '__main__':
    unittest.main(verbosity=2)
