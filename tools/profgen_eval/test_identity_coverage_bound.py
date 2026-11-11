"""Synthetic reference-only gate tests; no profile data."""
import unittest
from check_identity_coverage_bound import gate_bound
class BoundTest(unittest.TestCase):
    def test_below(self): self.assertTrue(gate_bound(100,51)["proves_coverage_3_below_half"])
    def test_exact_half_not_below(self): self.assertFalse(gate_bound(100,50)["proves_coverage_3_below_half"])
    def test_above(self): self.assertFalse(gate_bound(100,49)["proves_coverage_3_below_half"])
    def test_zero(self): self.assertIsNone(gate_bound(0,0)["coverage_3_upper_bound"])
    def test_integer_large(self): self.assertTrue(gate_bound(2**64+2,2**63+2)["proves_coverage_3_below_half"])
    def test_invalid(self):
        with self.assertRaises(ValueError): gate_bound(1,2)
    def test_union_no_double_count(self):
        da={1:10,2:20,3:30};amb_a={1,2};amb_b={2,3}
        self.assertEqual(gate_bound(sum(da.values()),sum(da[k] for k in amb_a|amb_b))["maximum_possible_R_U"],0)
    def test_unexecuted_candidate_overlap_still_excluded(self):
        C={1,2};unexecuted_ambiguous_range={2,3};da={1:10,2:20,3:0}
        self.assertEqual(gate_bound(sum(da[k] for k in C),sum(da[k] for k in C&unexecuted_ambiguous_range))["maximum_possible_R_U"],10)
if __name__=="__main__":unittest.main()
