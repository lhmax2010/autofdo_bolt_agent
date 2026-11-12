"""Synthetic Q.5 #11 fixtures. No profiles or board inputs."""
import copy
import math
import unittest
from registration_performance import *


def matrix():
    return dict(shortlist=[["avg","none"]],rows=[dict(id=g+z,group=g,profi=p,head=h,aggregation="avg",skid="none",
        zero_fill=z,weight="period",profile="synthetic",driver_profi_disabled=True,stale=False,salvage_unused=False)
        for g,(p,h) in GROUPS.items() for z in ("none","sampled-functions")])


class Performance(unittest.TestCase):
    def test_cv_half_percent(self): self.assertEqual(budget(.005)["N"],13)
    def test_cv_one_percent(self): self.assertEqual(budget(.01)["N"],40)
    def test_cv_zero(self): self.assertEqual(budget(0)["N"],10)
    def test_cv_missing(self): self.assertEqual(budget()["N"],40)
    def test_cv_nan(self): self.assertEqual(budget(float("nan"))["N"],40)
    def test_cv_infinity(self): self.assertEqual(budget(float("inf"))["N"],40)
    def test_cv_four_significant_digits(self): self.assertEqual(budget(.005123456)["cv"],.005123)
    def test_outlier_is_retained(self):
        rows=[dict(seconds=1.,outlier=False) for _ in range(9)]+[dict(seconds=1.2,outlier=True)]
        conditions=dict(new_image=True,cooling_installed=True,sampler_enabled=True,conditions_recorded=True)
        self.assertEqual(pretrial_budget(rows,conditions)["N"],40)
        self.assertEqual(pretrial_budget(rows,conditions)["cv"],float(format(statistics.stdev([1.]*9+[1.2])/1.02,".4g")))
    def test_warmup_removed(self):
        rows=[dict(seconds=1.) for _ in range(10)]+[dict(seconds=9.,warmup=True)]
        self.assertEqual(pretrial_budget(rows,dict.fromkeys(["new_image","cooling_installed","sampler_enabled","conditions_recorded"],True))["N"],10)
    def test_old_image_not_cv(self): self.assertEqual(pretrial_budget([dict(seconds=1.)]*10,{})["N"],40)
    def test_matrix_complete(self): self.assertTrue(claim_zero_fill_default(matrix()))
    def test_each_group_parameters(self):
        for i in range(8):
            m=matrix();m["rows"][i]["profi"]=not m["rows"][i]["profi"]
            with self.assertRaisesRegex(ValueError,"group_parameters"):validate_matrix(m)
    def test_small_matrix_no_default_claim(self):
        m=matrix();m["rows"]=m["rows"][:1]
        m["unassessed_interactions"]=[["avg","none",g,z] for g in GROUPS for z in ("none","sampled-functions") if (g,z)!=("G1","none")]
        m["fixed_parameters"]={"zero_fill":"none"}
        self.assertFalse(validate_matrix(m)["zero_fill_default_verified"])
        with self.assertRaisesRegex(ValueError,"control_missing"):claim_zero_fill_default(m)
    def test_omission_must_be_disclosed(self):
        m=matrix();m["rows"].pop()
        with self.assertRaisesRegex(ValueError,"unexplained"):validate_matrix(m)
    def test_lto_requires_same_parameters(self):
        m=matrix();r=m["rows"][0];r["lto"]=True
        with self.assertRaisesRegex(ValueError,"LTO"):validate_matrix(m)
        r["link"]={k:r[k] for k in ("profile","profi","stale","salvage_unused")}
        self.assertTrue(validate_matrix(m)["zero_fill_default_verified"])
    def test_G0_G5(self):
        m=matrix();m["rows"] += [dict(id="base",group="G0",profile=None),dict(id="instr",group="G5",profile="synthetic",instrumentation="IR",disable_preinline=False)]
        validate_matrix(m)
        m["rows"][-1]["disable_preinline"]=True
        with self.assertRaisesRegex(ValueError,"G5"):validate_matrix(m)
    def test_disable_quality_leaves_performance(self): self.assertEqual(performance_policy(False),performance_policy(True))
    def test_quality_rules_rejected(self):
        base=dict(performance_policy(True),N=13,completed=13,interval_bounds=[-.005,.005])
        for key,val in dict(statistic="RUN_mean",epsilon=.02,interval="stratified_t",stop="15_RUNs").items():
            with self.assertRaisesRegex(ValueError,"mixing"):validate_performance_result(dict(base,**{key:val}),13)
    def test_insufficient_no_extension(self):
        r=dict(performance_policy(False),N=13,completed=13,interval_bounds=[-.02,.02]);self.assertEqual(validate_performance_result(r,13),"insufficient_evidence")
        with self.assertRaisesRegex(ValueError,"changed"):validate_performance_result(dict(r,extend_for_precision=True),13)
    def test_N_exhausted(self):
        rows=[dict(id=str(i),group="G1",stage="formal") for i in range(13)]
        with self.assertRaisesRegex(ValueError,"exhausted"):accept_formal_round(rows,dict(id="new",group="G1",stage="formal"),13)
    def test_pretrial_excluded(self):
        with self.assertRaisesRegex(ValueError,"pretrial"):accept_formal_round([],dict(id="pre",group="G0",stage="pretrial"),13)
    def test_warmup_excluded(self):
        with self.assertRaisesRegex(ValueError,"warmup"):accept_formal_round([],dict(id="pre",group="G0",stage="formal",warmup=True),13)
    def test_normal_round(self):self.assertEqual(len(accept_formal_round([],dict(id="x",stage="formal",group="G1"),13)),1)

if __name__=="__main__":unittest.main()
