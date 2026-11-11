"""Synthetic fixtures; reference data only, no formal profiles."""
import collections,unittest
from static_coverage_gate import profile_key,measures
from ambiguity_package import mechanical

def frame(name="f",line=10,start=9,disc=0):
    return dict(name=name,line=line,start_line=start,base_discriminator=disc)
class Keys(unittest.TestCase):
    def test_full_inline_context(self):
        self.assertEqual(profile_key([frame("leaf",23,20,2),frame("top",15,10,4)]),
                         [["top",5,4],["leaf",3,2]])
    def test_leaf_zero(self):self.assertIsNone(profile_key([frame(line=0)]))
    def test_nonleaf_zero(self):self.assertIsNone(profile_key([frame(),frame("outer",0)]))
    def test_wrap(self):self.assertEqual(profile_key([frame(line=1,start=12)])[0][1],65525)
    def test_base_disc(self):self.assertEqual(profile_key([frame(disc=7)])[0][2],7)
    def test_unique_suffix_kept(self):self.assertEqual(profile_key([frame("f.__uniq.123")])[0][0],"f.__uniq.123")
    def test_empty(self):self.assertIsNone(profile_key([]))
    def test_invalid_name_truncates(self):
        self.assertEqual(profile_key([frame("<invalid>"),frame("outer")]),[["outer",1,0]])

class Classification(unittest.TestCase):
    def test_a(self):self.assertEqual(mechanical(["a.c","b.c"],False,[])[0],"a_different_TU")
    def test_b_positive_evidence(self):self.assertEqual(mechanical(["a.c"],True,[])[0],"b_same_TU_conditional_or_include")
    def test_c(self):self.assertEqual(mechanical(["a.c"],False,[("f",1),("f",2)])[0],"c_same_TU_multiple_definitions")
    def test_d_no_guess(self):self.assertEqual(mechanical(["a.c"],False,[("f",1)])[0],"d_other")
    def test_c_no_variant_evidence(self):self.assertEqual(mechanical(["a.c"],False,[("f",1),("f",2)],False)[0],"d_other")
    def test_a_precedence(self):self.assertEqual(mechanical(["a.c","b.c"],True,[])[0],"a_different_TU")

class Ledger(unittest.TestCase):
    def run_fixture(self,values,exclusions=None,owners=None):
        da={("f",n):v for n,v in enumerate(values)}
        owners=owners or {k:{0} for k in da}
        why=collections.defaultdict(set)
        for n,rs in (exclusions or {}).items():why[("f",n)].update(rs)
        return measures(da,owners,why,set(da))
    def test_overlap_loss_once(self):
        u,w,s=self.run_fixture([10,20,30],{1:["identity_ambiguous","unmatched_in_elf"]})
        self.assertEqual(s["loss_equation"]["sum_loss"],20)
        self.assertEqual(s["loss_equation"]["difference"],0)
    def test_zero_da_kept(self):
        u,w,s=self.run_fixture([0,1]);self.assertEqual(len(u),2)
    def test_null_neff(self):
        u,w,s=self.run_fixture([1,2]);self.assertIsNone(s["n_eff"])
    def test_constant_excluded_weight(self):
        u,w,s=self.run_fixture([2]*5);self.assertIsNone(s["n_eff"]);self.assertEqual(w[0]["reason"],"constant_reference")
    def test_neff(self):
        u,w,s=self.run_fixture([1,2,3,4,5]);self.assertEqual(s["n_eff"],1)
    def test_k_ties(self):
        u,w,s=self.run_fixture([4,4,4,1]);self.assertEqual(s["K"],3)
    def test_k_zero(self):
        u,w,s=self.run_fixture([0]*5);self.assertIsNone(s["K"])
    def test_k_descriptive(self):
        u,w,s=self.run_fixture([10,1]);self.assertEqual(s["K_interpretation"],"descriptive_only")
    def test_coverage_denominator_union(self):
        o={("f",0):{0,1},("f",1):{1}}
        u,w,s=self.run_fixture([10,20],{0:["reference_ambiguity"]},o)
        self.assertEqual(s["R_C"],30);self.assertEqual(s["R_U"],20)
    def test_missing_loss_reason_rejected(self):
        with self.assertRaises(AssertionError):
            measures({("f",1):1},{("f",1):{0}},collections.defaultdict(set),set())
    def test_half_boundary(self):
        u,w,s=self.run_fixture([10,10],{0:["no_key_line"]})
        self.assertEqual(s["coverage_3"],.5)
if __name__=="__main__":unittest.main()
