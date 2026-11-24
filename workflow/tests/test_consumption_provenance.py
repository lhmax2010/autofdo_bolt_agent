"""Source-command gate: synthetic negative tests and saved real failure replay."""
import json
import os
from pathlib import Path
import unittest
from afdo_wf import consumption
from afdo_wf.common import GateError
class Provenance(unittest.TestCase):
    def test_real_failure_and_partition(self):
        archive = os.environ.get('AFDO_WF_ATTEMPT07_RUN')
        if not archive:
            self.skipTest('original attempt-07 compiler diagnostics require AFDO_WF_ATTEMPT07_RUN')
        p = Path(archive)
        c=json.loads((p/'formal/stages/rebuild/001/AFDO/build-lock.json').read_text())['commands']
        self.assertFalse(all(any(x.startswith('-fprofile-sample-use=') for x in a) for a in c['libavcodec']))
        deps=[]
        from afdo_wf.buildlock import recorded_switches
        for f in (p/'consumption-diagnosis').glob('*.stdout'):deps.extend(recorded_switches(f.read_text()))
        source,excluded=consumption.target_source_commands(c,{k:k for k in c},deps)
        self.assertEqual({k:len(v) for k,v in source.items()},{'libavcodec':311,'libavutil':97})
        self.assertEqual({k:len(v) for k,v in excluded.items()},{'libavcodec':3,'libavutil':3})
        self.assertTrue(all(any(x.startswith('-fprofile-sample-use=') for x in a) for rows in source.values() for a in rows))
    def test_unproven_record_rejected(self):
        with self.assertRaises(GateError):consumption.target_source_commands({'lib':['GNU','bad']},{'lib':'lib'},[])
    def test_known_support_and_source_without_profile_retained(self):
        support=['GNU','C17','-fbuilding-libgcc'];source=['clang','-c','-o','lib/a.o','lib/a.c']
        a,b=consumption.target_source_commands({'lib':[support,source]},{'lib':'lib'},[support])
        self.assertEqual(a['lib'],[source]);self.assertEqual(b['lib'],[support])
        # Missing sample-use on a target source is never hidden by dependency proof.
        a,b=consumption.target_source_commands({'lib':[source]},{'lib':'lib'},[source])
        self.assertEqual(a['lib'],[source])
    def test_wrong_target_rejected(self):
        with self.assertRaises(GateError):consumption.target_source_commands({'a':[['clang','-c','-o','b/x.o']]},{'a':'a','b':'b'},[])
    def test_same_text_unproven_support_rejected(self):
        with self.assertRaises(GateError):consumption.target_source_commands({'lib':[['GNU','C17','-fbuilding-libgcc']]},{'lib':'lib'},[])
