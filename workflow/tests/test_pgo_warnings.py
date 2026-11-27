from pathlib import Path
from tempfile import TemporaryDirectory
import zlib
import unittest

from afdo_wf import pgo_warnings as warnings
from afdo_wf.common import GateError


class PGOWarnings(unittest.TestCase):
    targets={'libavcodec/':'codec','libavutil/':'util'}
    objects={'libavcodec/hot.o':3,'libavutil/cold.o':12,'libavfilter/cold.o':15}
    top=[{'object':'libavcodec/hot.o'}]
    sync='[  12s] + export MAKEFLAGS=--output-sync=target -j2\n'

    def audit(self, *lines):
        return warnings.audit(self.sync+'\n'.join(lines), warnings.POLICY, self.targets, self.objects, self.top)

    def test_target_stale_warning_fails(self):
        result=self.audit('[  12s] CC\tlibavutil/cold.o',
                         '[  12s] warning: profile data may be out of date [-Wprofile-instr-out-of-date]')
        self.assertFalse(result['passed'])
        self.assertEqual(result['outdated_gate'][0]['target'],'util')

    def test_non_target_stale_and_cold_unprofiled_are_report_only(self):
        result=self.audit('CC libavfilter/cold.o',
                         'warning: profile data may be out of date [-Wprofile-instr-out-of-date]',
                         'CC libavutil/cold.o', 'warning: no profile data available for file "libavutil/cold.c" [-Wprofile-instr-unprofiled]',
                         'warning: profile data may be incomplete [-Wprofile-instr-missing]')
        self.assertTrue(result['passed'])
        self.assertEqual(result['counts'],dict.fromkeys((warnings.OUTDATED,warnings.UNPROFILED,'profile-instr-missing'),1))

    def test_hot_unprofiled_fails(self):
        result=self.audit('CC libavcodec/hot.o',
                         'warning: no profile data available for file "libavcodec/hot.c" [-Wprofile-instr-unprofiled]')
        self.assertFalse(result['passed'])
        self.assertEqual(len(result['unprofiled_gate']),1)

    def test_other_ir_backend_diagnostics_are_report_only(self):
        result=self.audit('CC libavcodec/hot.o',
                         'warning: libavcodec/hot.c: function control flow change detected (hash mismatch) hot Hash = 1 up to 4 count discarded [-Wbackend-plugin]')
        self.assertTrue(result['passed'])
        self.assertEqual(result['records'][0]['kind'],'backend-plugin')
        self.assertEqual(result['records'][0]['backend_detail'],'flow-mismatch')

    def test_unattributed_gate_warning_and_missing_sync_fail(self):
        result=self.audit('LD libavcodec/libavcodec.so',
                         'warning: profile data may be out of date [-Wprofile-instr-out-of-date]')
        self.assertFalse(result['passed'])
        self.assertIsNone(result['outdated_gate'][0]['object'])
        with self.assertRaisesRegex(GateError,'synchronization proof'):
            warnings.audit('',warnings.POLICY,self.targets,self.objects,self.top)

    def test_quoted_makeflags_export_from_gbs_build_trace(self):
        log = ("[   65s] + export 'MAKEFLAGS=--output-sync=target  -k'\n"
               "[   65s] + MAKEFLAGS='--output-sync=target  -k'\n"
               "[   65s] + /bin/make -j2\n")
        result = warnings.audit(log, warnings.POLICY, self.targets, self.objects, self.top)
        self.assertTrue(result['passed'])

    def test_sync_proof_requires_exact_option_in_export_value(self):
        for export in ("'MAKEFLAGS=--output-sync=target-other -k'",
                       'MAKEFLAGS=-k OTHER=--output-sync=target'):
            with self.subTest(export=export), self.assertRaisesRegex(GateError, 'synchronization proof'):
                warnings.audit('[   65s] + export '+export, warnings.POLICY,
                               self.targets, self.objects, self.top)

    def test_policy_and_ranking_are_locked(self):
        with self.assertRaisesRegex(GateError,'preregister'):
            warnings.validate({})
        text='\n'.join(f'  fun{i}, max count = {21-i}' for i in range(20))
        self.assertEqual(warnings.top_rows(text)[0],dict(function='fun0',max_count=21))
        with self.assertRaisesRegex(GateError,'20 uniquely'):
            warnings.top_rows(text.replace('fun19','fun18'))

    def test_decode_raw_and_compressed_names(self):
        plain=b'foo\x01x.c;bar'
        compressed=zlib.compress(b'quux')
        contents=bytes([len(plain),0])+plain+b'\0\0'+bytes([4,len(compressed)])+compressed
        self.assertEqual(warnings.profile_names(contents),{'foo','x.c;bar','quux'})
        with self.assertRaisesRegex(GateError,'invalid profile-name payload'):
            warnings.profile_names(b'\x1f\0foo')

    def test_compile_objects_requires_emitted_objects(self):
        with TemporaryDirectory() as directory:
            path=Path(directory)
            (path/'libavcodec').mkdir()
            (path/'libavcodec/hot.o').touch()
            self.assertEqual(warnings.compile_objects('CC libavcodec/hot.o\nCC missing.o\n',path),{'libavcodec/hot.o':1})
