"""Synthetic scheduling fixtures; no formal repeats or real profile IO."""
import copy
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch
import interval_simulation_phased as s


class PhasedSimulationFixtures(unittest.TestCase):
    def setUp(self):
        self.manifest=json.loads(s.base.MANIFEST.read_text())
        self.temp=tempfile.TemporaryDirectory(dir=s.WORK/'temp',prefix='phased-fixture-')
        self.addCleanup(self.temp.cleanup);self.out=Path(self.temp.name)
    def row(self):return copy.deepcopy(self.manifest['scenarios'][0])
    def result(self,row=None,phase='acceptance'):
        row=row or self.row();n=s.repeats(row,phase)
        counts=s.new_counts(phase)
        for c in counts.values():c.update(covered=n,equivalent=0,degenerate=0,no_interval=0)
        r=dict(id=row['id'],phase=phase,seed=row['seed'],parameters=row,repeats=n,counts=counts,
               statistics={k:s.base.summarize(v,n) for k,v in counts.items()},elapsed_seconds=1)
        if phase=='acceptance':r['passed']=s.base.acceptance(row,counts['t'],n)
        return r
    def test_122_acceptance_rows(self):self.assertEqual(len(s.selected_rows(self.manifest,'acceptance')),122)
    def test_150_envelope_rows(self):self.assertEqual(len(s.selected_rows(self.manifest,'envelope')),150)
    def test_formal_repeats_unchanged(self):
        for r in s.selected_rows(self.manifest,'acceptance'):self.assertEqual(s.repeats(r,'acceptance'),1000000)
        for r in s.selected_rows(self.manifest,'envelope'):self.assertEqual(s.repeats(r,'envelope'),10000)
    def test_acceptance_no_bootstrap_kind(self):self.assertEqual(set(s.new_counts('acceptance')),{'t'})
    def test_envelope_all_three(self):self.assertEqual(set(s.new_counts('envelope')),{'t','percentile','envelope'})
    def test_valid_complete_result(self):self.assertTrue(s.validate_result(self.row(),'acceptance',self.result()))
    def test_seed_change_rejected(self):
        r=self.result();r['seed']+=1
        with self.assertRaises(ValueError):s.validate_result(self.row(),'acceptance',r)
    def test_repeat_change_rejected(self):
        r=self.result();r['repeats']-=1
        with self.assertRaises(ValueError):s.validate_result(self.row(),'acceptance',r)
    def test_phase_mismatch_rejected(self):
        with self.assertRaises(ValueError):s.validate_result(self.row(),'envelope',self.result())
    def test_counts_and_summary_must_agree(self):
        r=self.result();r['counts']['t']['covered']-=1
        with self.assertRaises(ValueError):s.validate_result(self.row(),'acceptance',r)
    def test_count_above_repeats_rejected(self):
        r=self.result();r['counts']['t']['covered']+=1
        with self.assertRaises(ValueError):s.validate_result(self.row(),'acceptance',r)
    def test_pass_must_recompute(self):
        r=self.result();r['passed']=False
        with self.assertRaises(ValueError):s.validate_result(self.row(),'acceptance',r)
    def test_missing_acceptance_false(self):
        r=s.acceptance_summary([self.row()],[])
        self.assertFalse(r['complete']);self.assertFalse(r['quality_equivalence_enabled'])
    def test_complete_pass_enables(self):self.assertTrue(s.acceptance_summary([self.row()],[self.result()])['quality_equivalence_enabled'])
    def test_prior_false_stays_false(self):
        r=s.acceptance_summary([self.row()],[self.result()],[dict(complete=True,quality_equivalence_enabled=False)])
        self.assertFalse(r['quality_equivalence_enabled'])
    def test_incomplete_prior_not_statistical_failure(self):
        r=s.acceptance_summary([self.row()],[self.result()],[dict(complete=False,quality_equivalence_enabled=False)])
        self.assertTrue(r['quality_equivalence_enabled'])
    def test_complete_append_resumes_without_change(self):
        r=self.result();written=s.base.append(self.out,r)
        self.assertEqual(s.load_complete(self.out,[self.row()],'acceptance'),[written])
    def test_torn_tail_preserved_and_restarted(self):
        written=s.base.append(self.out,self.result())
        with (self.out/'results.jsonl').open('ab') as f:f.write(b'{"id":"interrupted')
        self.assertEqual(s.load_complete(self.out,[self.row()],'acceptance'),[written])
        self.assertEqual(next(self.out.glob('interrupted-tail-*.bin')).read_bytes(),b'{"id":"interrupted')
    def test_corrupted_complete_record_rejected(self):
        s.base.append(self.out,self.result());p=self.out/'results.jsonl';p.write_text(p.read_text().replace('"covered": 1000000','"covered": 999999',1))
        with self.assertRaises(ValueError):s.load_complete(self.out,[self.row()],'acceptance')
    def test_unknown_id_rejected(self):
        r=self.result();r['id']='not-registered';s.base.append(self.out,r)
        with self.assertRaises(ValueError):s.load_complete(self.out,[self.row()],'acceptance')
    def test_stage2_requires_pushed_summary(self):
        (self.out/'acceptance').mkdir();s.save(self.out/'acceptance/summary.json',dict(complete=True,quality_equivalence_enabled=False))
        with patch.object(s,'ROOT',self.out),patch.object(s,'command',return_value=b'{}'):
            with self.assertRaises(ValueError):s.stage2_admission()
    def test_stage2_allows_false_switch_after_push(self):
        (self.out/'acceptance').mkdir();p=self.out/'acceptance/summary.json';s.save(p,dict(complete=True,quality_equivalence_enabled=False));(self.out/'acceptance/results.jsonl').write_text('synthetic')
        with patch.object(s,'ROOT',self.out),patch.object(s,'command',side_effect=[p.read_bytes(),b'synthetic']):
            self.assertFalse(s.stage2_admission()['quality_equivalence_enabled'])
    def test_stage2_rejects_unpushed_results(self):
        (self.out/'acceptance').mkdir();p=self.out/'acceptance/summary.json';s.save(p,dict(complete=True));(self.out/'acceptance/results.jsonl').write_text('synthetic')
        with patch.object(s,'ROOT',self.out),patch.object(s,'command',side_effect=[p.read_bytes(),b'other']):
            with self.assertRaises(ValueError):s.stage2_admission()
    def test_no_replacement_statistics(self):
        row=self.row();row['id']='synthetic-small';row['seed']=123;row['t_repeats']=7
        class Monitor:
            def tick(self,**kw):pass
        with patch.object(s.base,'evaluate',wraps=s.base.evaluate) as called:
            result=s.perform(row,'acceptance',Monitor());self.assertEqual(called.call_count,7)
            self.assertTrue(all(c.kwargs['envelope'] is False for c in called.call_args_list))
        rng=random.Random(123);counts=s.new_counts('acceptance')
        for _ in range(7):s.accumulate(counts,s.base.evaluate(s.base.sample(row,rng),row['delta']))
        self.assertEqual(result['counts'],counts)


if __name__=='__main__':unittest.main()
