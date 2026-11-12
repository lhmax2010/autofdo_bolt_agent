"""Synthetic-only Q.5 #9 fixtures; not simulation repeats or results."""
import copy
import json
from pathlib import Path
import random
import unittest
from unittest.mock import patch
import interval_simulation as sim


class SimulationFixtures(unittest.TestCase):
    def setUp(self):
        self.manifest=json.loads(sim.MANIFEST.read_text())
        self.rows=self.manifest['scenarios']
    def row(self,family):return copy.deepcopy(next(r for r in self.rows if r['family']==family))
    def test_all_explicit_rows_and_moments(self):
        self.assertEqual(len(sim.validate_manifest(self.manifest)),150)
    def test_A2_does_not_generate_ratio16(self):
        for r in self.rows:
            if r['family']=='A2':self.assertIn(r['variance_ratio'],(1,'not_applicable'))
    def test_injected_A2_ratio16_rejected(self):
        r=self.row('A2');r['variance_ratio']=16
        with self.assertRaises(ValueError):sim.validate_row(r)
    def test_A5_lambda_mean(self):
        for r in self.rows:
            if r['family']=='A5':self.assertAlmostEqual((5/15)*r['phase_parameters'][0]['a']*.15,r['delta'])
    def test_false_then_true_stays_false(self):
        self.assertFalse(sim.combined_switch([dict(complete=True,quality_equivalence_enabled=False),dict(complete=True,quality_equivalence_enabled=True)]))
    def test_incomplete_not_in_complete_conjunction(self):
        self.assertTrue(sim.combined_switch([dict(complete=False,quality_equivalence_enabled=False),dict(complete=True,quality_equivalence_enabled=True)]))
    def test_missing_rows_false_incomplete(self):
        x=sim.summarize_run(self.rows,[])
        self.assertFalse(x['complete']);self.assertFalse(x['quality_equivalence_enabled']);self.assertFalse(x['included_in_complete_run_conjunction'])
    def test_all_zero_decision(self):
        r=sim.evaluate({'0':[0]*15},0)['t']
        self.assertTrue(r['degenerate']);self.assertTrue(r['covered']);self.assertFalse(r['equivalent'])
    def test_rare_flat_covers_true_mean(self):
        r=sim.evaluate({'0':[0]*5,'1':[.001]*10},.03)['t']
        self.assertTrue(r['covered']);self.assertFalse(r['equivalent'])
    def test_boundary_pass_is_inclusive(self):
        r=self.row('A1');r['delta']=.02
        self.assertTrue(sim.acceptance(r,dict(covered=930000,equivalent=30000,degenerate=0),1000000))
    def test_bad_coverage_fails(self):
        r=self.row('A1');self.assertFalse(sim.acceptance(r,dict(covered=929999,equivalent=0,degenerate=0),1000000))
    def test_bad_equivalence_fails(self):
        r=self.row('A3');self.assertFalse(sim.acceptance(r,dict(covered=1000000,equivalent=30001,degenerate=0),1000000))
    def test_A4_requires_all_degenerate(self):
        r=self.row('A4');self.assertFalse(sim.acceptance(r,dict(covered=1000000,equivalent=0,degenerate=999999),1000000))
    def test_A4_requires_zero_equivalent(self):
        r=self.row('A4');self.assertFalse(sim.acceptance(r,dict(covered=1000000,equivalent=1,degenerate=1000000),1000000))
    def test_actual_moments_mismatch_rejected(self):
        r=self.row('A1');r['phase_variances'][0]*=2
        with self.assertRaises(ValueError):sim.validate_row(r)
    def test_nan_rejected(self):
        r=self.row('A1');r['se_ratio']=float('nan')
        with self.assertRaises(ValueError):sim.validate_row(r)
    def test_changed_repeat_rejected(self):
        r=self.row('A3');r['t_repeats']=10000
        with self.assertRaises(ValueError):sim.validate_row(r)
    def test_seed_stream_mismatch_rejected(self):
        r=self.row('A1');r['seed']+=1
        with self.assertRaises(ValueError):sim.validate_row(r)
    def test_same_seed_same_samples(self):
        for fam in ['A1','A2','A3','A4','A5','B1','B2','B3']:
            r=self.row(fam);self.assertEqual(sim.sample(r,random.Random(r['seed'])),sim.sample(r,random.Random(r['seed'])))
    def test_shared_t_path(self):
        original=sim.shared.stratified_t
        with patch.object(sim.shared,'stratified_t',wraps=original) as f:
            sim.evaluate({'0':list(range(15))},0);self.assertEqual(f.call_count,1)
    def test_shared_envelope_path(self):
        original=sim.shared.intervals_joint
        with patch.object(sim.shared,'intervals_joint',wraps=original) as f:
            out=sim.evaluate({'0':[0,.001,.002,.003,.004]*3},0,True)
            self.assertEqual(f.call_count,1);self.assertIn('envelope',out)
    def test_mc_se(self):
        self.assertAlmostEqual(sim.summarize({'covered':5000},10000)['covered']['mc_se'],.005)
    def test_report_B_not_switch(self):
        r=self.row('B1');x=dict(id=r['id'],seed=r['seed'],t_repeats=0,envelope_repeats=10000,passed=None)
        self.assertTrue(sim.summarize_run([r],[x])['quality_equivalence_enabled'])
    def test_run_repeat_mismatch_incomplete(self):
        r=self.row('A1');x=dict(id=r['id'],seed=r['seed'],t_repeats=999999,envelope_repeats=10000,passed=True)
        self.assertFalse(sim.summarize_run([r],[x])['complete'])


if __name__=='__main__':unittest.main()
