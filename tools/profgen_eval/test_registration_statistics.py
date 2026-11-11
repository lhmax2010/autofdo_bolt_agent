"""Synthetic only: Q.5 #7, #8 and numerical/statistical clauses of #10."""
import math
import random
import statistics
import unittest
from registration_statistics import *

MODEL=dict(id='synthetic-model',unverified_assumptions=['iid within phase','independent phases','approximate normality'],scenario_failures=[])

def table(K=80,neff=None):return dict(U_lines=100,T=1000,K=K,n_eff=neff)
def result(interval=(-.01,.01),flat=False):
    return dict(t=dict(degenerate=flat),envelope=list(interval))
def decide(t=None,results=None,**kw):
    args=dict(terminal_slots=15,complete_pairs=True,model=MODEL,quality_enabled=True)
    args.update(kw)
    return interpretation(table() if t is None else t,{'M1':result(),'M2':result()} if results is None else results,**args)

def metric(ref,sample=None,min_lines=5):
    return line_metrics(dict(enumerate(ref)),{} if sample is None else dict(enumerate(sample)),dict.fromkeys(range(len(ref)),'f'),min_lines)


class MFixtures(unittest.TestCase):
    def test_n15_k9_all_sample_zero(self):
        # 9*10 of total 96, threshold crossed at eighth and all 9 ties retained.
        self.assertEqual(metric([10]*9+[1]*6)['K'],9)
        self.assertEqual(metric([10]*9+[1]*6)['M2'],0)
    def test_single_positive_hot(self):
        self.assertEqual(metric([10]*9+[1]*6,[5]+[0]*14)['M2'],1/9)
    def test_positive_tie_cutoff(self):
        # All 15 sample positions tie; 9 slots -> share 3/5, hot intersection 9.
        self.assertEqual(metric([10]*9+[1]*6,[1]*15)['M2'],.6)
    def test_positive_shortfall_no_zero_padding(self):
        self.assertEqual(metric([10]*9+[1]*6,[1,1]+[0]*13)['M2'],2/9)
    def test_total_zero(self):
        x=metric([0]*5);self.assertIsNone(x['M2']);self.assertIsNone(x['M1'])
    def test_empty_u(self):
        self.assertIsNone(metric([])['K']);self.assertFalse(decide(dict(U_lines=0,T=0,K=None,n_eff=None))['equivalent'])
    def test_undefined_k(self):self.assertFalse(decide(table(K=None))['equivalent'])
    def test_null_neff_k5(self):self.assertEqual(decide(table(K=5))['result'],'descriptive_only')
    def test_null_neff_k49(self):self.assertEqual(decide(table(K=49))['result'],'descriptive_only')
    def test_null_neff_k50(self):self.assertIn('M2等价，M1未判读',decide(table(K=50))['result'])
    def test_null_neff_k80_every_gate(self):
        self.assertTrue(decide()['equivalent'])
        for kw in [dict(complete_pairs=False),dict(terminal_slots=14),dict(quality_enabled=False)]:self.assertFalse(decide(**kw)['equivalent'])
        self.assertFalse(decide(results={'M2':result(flat=True)})['equivalent'])
        self.assertFalse(decide(results={'M2':result((-.03,.01))})['equivalent'])
    def test_neff_exact_three_joint(self):
        self.assertIn('联合',decide(table(neff=3))['result'])
        self.assertFalse(decide(table(neff=3),{'M1':None,'M2':result()})['equivalent'])
    def test_ten_line_sensitivity_empty(self):self.assertIsNone(metric([1,2,3,4,5],min_lines=10)['M1'])
    def test_exact_eighty_percent(self):self.assertEqual(hot_reference({'a':8,'b':2})[0],{'a'})
    def test_just_cross_eighty_percent(self):self.assertEqual(hot_reference({'a':7,'b':2,'c':1})[0],{'a','b'})
    def test_sample_constant_scored_zero_not_dropped(self):self.assertEqual(metric([1,2,3,4,5],[0]*5)['M1'],0)
    def test_reference_constant_excluded(self):self.assertIsNone(metric([1]*5,[1,2,3,4,5])['M1'])
    def test_reverse_cost_order(self):self.assertAlmostEqual(metric([1,2,3,4,5],[100,80,60,40,5])['M1'],-1)
    def test_ranks_average_ties(self):self.assertEqual(ranks([2,1,2]),[2.5,1,2.5])
    def test_head_or_explicit_zero_does_not_change_body(self):
        ref={0:1,1:2,2:3,3:4,4:5};owners=dict.fromkeys(ref,'f')
        self.assertEqual(line_metrics(ref,{0:1},owners),line_metrics(ref,{0:1,1:0,2:0,3:0,4:0},owners))
    def test_fixed_function_weights_and_median(self):
        r={i:i%5+1 for i in range(10)};owners={i:'a' if i<5 else 'b' for i in r}
        m=line_metrics(r,{i:r[i] for i in range(5)},owners)
        self.assertEqual(m['M1'],.5);self.assertEqual(m['n_eff'],2);self.assertEqual(m['equal_function_median'],.5)
    def test_nan_rejected(self):
        with self.assertRaises(ValueError):metric([1,2,3,4,5],[math.nan]*5)


def entry(ctx,d,n,line=10,**kw):
    e=dict(line=['file.c',line],context=[ctx],discriminator=d,count=n,
      reference_executed=True,source_owner='f',line_owner='f',regions=[dict(file='file.c',start=[10,2],end=[10,20])])
    e.update(kw);return e


class MergeFixtures(unittest.TestCase):
    def test_complementary_contexts(self):
        out=merge_lines([entry('a',0,100),entry('a',1,0),entry('b',0,0),entry('b',1,100)])
        self.assertEqual(out['lines'][('file.c',10)],dict(S=100,S_alt=200,S_sum=200))
    def test_inline_two_sites_different_branches(self):
        out=merge_lines([entry('call1',0,5,10),entry('call2',0,0,10),entry('call1',0,0,11),entry('call2',0,7,11)])
        self.assertEqual([out['lines'][('file.c',i)]['S'] for i in [10,11]],[5,7])
    def test_multiple_regions_and_discriminators(self):
        a=entry('a',0,10);b=entry('a',1,20,regions=[dict(start=[10,21],end=[11,2])])
        out=merge_lines([a,b]);self.assertEqual(out['lines'][('file.c',10)],dict(S=20,S_alt=20,S_sum=30))
        self.assertEqual(out['coverage_regions'],a['regions']+b['regions'])
    def test_unexecuted_template_same_line(self):
        out=merge_lines([entry('executed',0,5),entry('cold',1,999,reference_executed=False)])
        self.assertEqual(out['lines'][('file.c',10)]['S'],5);self.assertEqual(out['rejected'][0]['reason'],'unexecuted_reference_source')
    def test_source_owner_mismatch(self):
        out=merge_lines([entry('a',0,10,source_owner='other')]);self.assertFalse(out['lines'])
    def test_zero_entries_preserved(self):self.assertEqual(merge_lines([entry('a',0,0)])['lines'][('file.c',10)]['S'],0)


class StatisticsFixtures(unittest.TestCase):
    def test_pairs_order_by_id(self):
        slots=[dict(run_id='a',phase='p'),dict(run_id='b',phase='p')]
        left={'b':dict(value=3,conversion='ok'),'a':dict(value=2,conversion='ok')}
        right={'a':dict(value=1,conversion='ok'),'b':dict(value=1,conversion='ok')}
        self.assertEqual(paired_differences(left,right,slots)['phases'],{'p':[1.,2.]})
    def test_one_sided_missing_and_failed(self):
        slots=[dict(run_id=k,phase='p') for k in ['a','b','c']]
        left={k:dict(value=1,conversion='ok') for k in ['a','b','c']}
        right={'b':dict(value=1,conversion='failed'),'c':dict(value=None,conversion='ok')}
        self.assertEqual(paired_differences(left,right,slots)['missing'],['a','b','c'])
    def test_multiple_segments_one_run(self):
        a={'a':dict(value=1,conversion='ok',segments=['s1','s2'])}
        out=paired_differences(a,a,[dict(run_id='a',phase='p')]);self.assertEqual(len(out['phases']['p']),1)
    def test_five_runs_no_interpretation(self):self.assertFalse(decide(terminal_slots=5)['equivalent'])
    def test_three_plus_twelve_flat_counterexample(self):
        self.assertTrue(stratified_t({'old':[0]*3,'new':list(range(12))})['degenerate'])
    def test_half_grid_positive_and_negative(self):
        a=[.0130000005000000555,.0130000004999999445]
        for vals in [a,[-x for x in a]]:self.assertTrue(phase_diagnostics({'p':vals})['p']['degenerate'])
    def test_translation(self):
        vals=[.001,.00100000000000001]
        self.assertEqual(phase_diagnostics({'p':vals})['p']['degenerate'],phase_diagnostics({'p':[x+.01 for x in vals]})['p']['degenerate'])
    def test_resolution_exact(self):self.assertTrue(phase_diagnostics({'p':[0,1e-9]})['p']['degenerate'])
    def test_resolution_nextafter(self):self.assertFalse(phase_diagnostics({'p':[0,math.nextafter(1e-9,1)]})['p']['degenerate'])
    def test_resolution_below(self):self.assertTrue(phase_diagnostics({'p':[0,math.nextafter(1e-9,0)]})['p']['degenerate'])
    def test_small_real_variation(self):self.assertFalse(phase_diagnostics({'p':[0,0,1e-6]})['p']['degenerate'])
    def test_fraction_sum_order(self):
        a=[1/3]+[1e-17]*5
        d=sum(a)-sum(reversed(a));self.assertTrue(phase_diagnostics({'p':[0,d]})['p']['degenerate'])
    def test_constant_nonzero_phase(self):self.assertTrue(stratified_t({'a':[.01]*5,'b':[i/1000 for i in range(10)]})['degenerate'])
    def test_single_phase_flat(self):self.assertTrue(stratified_t({'a':[.01]*15})['degenerate'])
    def test_stratified_mean_is_ordinary(self):
        a=[.01*i for i in range(5)];b=[-.01*i for i in range(10)]
        self.assertAlmostEqual(stratified_t({'a':a,'b':b})['mean'],statistics.mean(a+b))
    def test_single_phase_paired_t(self):
        a=[i*.001 for i in range(15)];r=stratified_t({'a':a})
        self.assertAlmostEqual(r['df'],14);self.assertAlmostEqual(r['SE'],statistics.stdev(a)/math.sqrt(15))
        self.assertAlmostEqual(r['interval'][1]-r['mean'],2.1447866879169273*statistics.stdev(a)/math.sqrt(15),places=12)
    def test_t_quantile_exact_df1_df2(self):
        self.assertAlmostEqual(t_quantile(1),math.tan(math.pi*(.975-.5)),places=9)
        # df2: CDF=1/2+t/(2*sqrt(t*t+2)), solve at .975.
        self.assertAlmostEqual(t_quantile(2),math.sqrt(2*.95**2/(1-.95**2)),places=10)
    def test_nonfinite_never_silently_dropped(self):
        for v in [math.nan,math.inf,-math.inf]:
            with self.assertRaises(ValueError):stratified_t({'a':[0,v]})
    def test_envelope_iff_double_pass(self):
        intervals=[[-.01,.01],[-.03,.01],[-.01,.03],[-.02,.02]]
        for a in intervals:
            for b in intervals:
                env=[min(a[0],b[0]),max(a[1],b[1])]
                self.assertEqual(-.02<=env[0] and env[1]<=.02,(-.02<=a[0] and a[1]<=.02) and (-.02<=b[0] and b[1]<=.02))
    def test_model_identifier_required(self):
        with self.assertRaises(ValueError):decide(model={})
        self.assertEqual(decide()['model'],MODEL)
    def test_global_false_all_objects_and_sensitivity(self):
        for k in [5,49,50,80]:
            for ne in [None,2,3,10]:
                for sens in [False,True]:self.assertFalse(decide(table(k,ne),quality_enabled=False,sensitivity=sens)['equivalent'])
    def test_outlier_normal_and_isolated(self):
        rng=random.Random(20261104);a=[rng.gauss(0,.02*.25*math.sqrt(15)) for _ in range(15)]
        self.assertLessEqual(len(outliers({'p':a})),2)
        self.assertEqual(len(outliers({'p':[i*1e-5 for i in range(14)]+[.3]})),1)
    def test_shared_bootstrap_and_determinism(self):
        a={'old':[i*.001 for i in range(5)],'new':[-i*.001 for i in range(10)]}
        first=intervals_joint({'M1':a,'M2':a});self.assertEqual(first['M1'],first['M2'])
        self.assertEqual(first,intervals_joint({'M1':a,'M2':a}))
    def test_phase_one_rejected(self):
        with self.assertRaises(ValueError):phase_diagnostics({'p':[1]})
    def test_missing_pair_not_reweighted_in_adapter(self):
        slots=[dict(run_id=str(i),phase='old' if i<5 else 'new') for i in range(15)]
        a={m:{str(i):dict(value=i*.001,conversion='ok') for i in range(15)} for m in ['M1','M2']}
        b={m:{str(i):dict(value=0,conversion='ok') for i in range(15)} for m in ['M1','M2']}
        b['M2'].pop('2')
        x=assess_paired_metrics(a,b,slots,table(neff=3),terminal_slots=15,model=MODEL,quality_enabled=True)
        self.assertEqual(x['planned_phase_counts'],{'old':5,'new':10})
        self.assertEqual(x['paired']['M2']['missing'],['2']);self.assertNotIn('M2',x['intervals'])
        self.assertFalse(x['decision']['equivalent'])
    def test_m2_only_allows_undefined_m1(self):
        slots=[dict(run_id=str(i),phase='all') for i in range(15)]
        a={m:{str(i):dict(value=(None if m=='M1' else i*.00001),conversion='ok') for i in range(15)} for m in ['M1','M2']}
        b={m:{str(i):dict(value=0,conversion='ok') for i in range(15)} for m in ['M1','M2']}
        x=assess_paired_metrics(a,b,slots,table(),terminal_slots=15,model=MODEL,quality_enabled=True)
        self.assertTrue(x['decision']['equivalent']);self.assertNotIn('M1',x['intervals'])
    def test_fixed_interval_no_weight_comparison(self):
        self.assertNotIn('sample_weight',comparisons(False));self.assertIn('sample_weight',comparisons(True))


if __name__=='__main__':unittest.main()
