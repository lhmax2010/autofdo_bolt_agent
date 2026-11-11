"""Synthetic fixtures required by rulings3/4 (no formal samples)."""
import unittest
from ruling34_rules import code_line_domain,instance_check,group_check

def inst(leaf=(),calls=(),code=True):
    return dict(decl_file="/f.c",decl_line=10,leaf_lines=[dict(file="/f.c",line=n) for n in leaf],
        direct_inline_calls=[dict(call_file=f,call_line=n,call_file_resolved=True,call_line_present=True) for f,n in calls],
        ranges=[[100,120]], descendant_nonzero_leaf=code,accepted_key_instructions=1 if code else 0)
C=[dict(file="/f.c",name="f",start=11,end=30,fnda=5)]
D=[dict(decl_file="/f.c",decl_line=10)]
def ck(x):return instance_check(x,C,D)
def row(n,end=False,die=1):
    return dict(file="/f.c",line=n,end_sequence=end,file_resolved=True,dies_leaf_to_root=[die],address=n*4)
class Rulings(unittest.TestCase):
    def test_01_multiline_inline_asm(self):
        c={( "/f.c",n) for n in range(10,21)}
        n,w=code_line_domain(c,[row(10),row(20)],{1})
        self.assertEqual(n,{("/f.c",10),("/f.c",20)})
    def test_02_call_argument_continuations(self):
        c={("/f.c",n) for n in range(11,16)}
        n,w=code_line_domain(c,[row(11),row(15)],{1})
        self.assertEqual(len(c-n),3)
    def test_03_macro_only_remains_excluded(self):
        n,w=code_line_domain({("/f.c",10)},[row(10),row(20)],{1})
        self.assertNotIn(("/f.c",20),n)
    def test_04_child_call_inside(self):self.assertEqual(ck(inst(calls=[("/f.c",15)]))["line_status"],"pass")
    def test_05_child_call_outside(self):self.assertEqual(ck(inst(calls=[("/f.c",31)]))["line_status"],"outside")
    def test_06_no_key(self):self.assertEqual(ck(inst(code=False))["line_status"],"no_key_instance")
    def test_07_group_all_no_key(self):
        r=group_check([ck(inst(code=False))],C)
        self.assertEqual(r["conclusion"],"reference_executed");self.assertTrue(r["all_no_key"])
    def test_08_group_partial_no_key(self):
        r=group_check([ck(inst(code=False)),ck(inst(leaf=[12]))],C)
        self.assertEqual(r["conclusion"],"reference_executed");self.assertFalse(r["all_no_key"])
    def test_09_descendant_code_other_file_call(self):
        r=ck(inst(calls=[("/other.c",20)],code=True))
        self.assertEqual(r["line_status"],"empty_with_keys")
        self.assertEqual(group_check([r],C)["conclusion"],"identity_ambiguous")
    def test_10_no_key_still_checks_definition(self):
        r=instance_check(inst(code=False),C,[])
        self.assertEqual(group_check([r],C)["conclusion"],"identity_ambiguous")
    def test_11_child_call_outside_not_hidden_by_leaf(self):
        self.assertEqual(ck(inst([15],[("/f.c",40)]))["line_status"],"outside")
    def test_12_zero_and_endsequence_not_code(self):
        n,w=code_line_domain({("/f.c",0),("/f.c",20)},[row(0),row(20,True)],{1})
        self.assertEqual(n,set())
    def test_13_unexecuted_C_function_not_code_witness(self):
        n,w=code_line_domain({("/f.c",10)},[row(10,die=9)],{1});self.assertEqual(n,set())
    def test_14_old_outside_not_rescued(self):
        r=ck(inst([40],[("/f.c",15)]));self.assertEqual(r["line_status"],"outside")
    def test_15_partial_failure_stays_ambiguous(self):
        r=group_check([ck(inst([15])),ck(inst(code=True))],C)
        self.assertEqual(r["failure_extent"],"partial_instances")
        self.assertEqual(r["conclusion"],"identity_ambiguous")
    def test_16_own_leaf_other_file_fails_even_with_call(self):
        x=inst(calls=[("/f.c",15)]);x["leaf_lines"]=[dict(file="/other.c",line=15)]
        self.assertEqual(ck(x)["line_status"],"leaf_other_file")
    def test_17_zero_leaf_and_descendants_has_address(self):
        x=inst(leaf=[0],code=False)
        self.assertTrue(x["ranges"])
        self.assertEqual(ck(x)["line_status"],"no_key_instance")
    def test_18_zero_call_is_not_proof(self):
        self.assertEqual(ck(inst(calls=[("/f.c",0)]))["line_status"],"empty_with_keys")
    def test_19_rev2_nonleaf_zero_empty_evidence_exempt(self):
        x=inst(code=True);x["accepted_key_instructions"]=0
        self.assertEqual(ck(x)["line_status"],"no_key_instance")
    def test_20_rev2_nonleaf_zero_outside_not_exempt(self):
        x=inst(leaf=[40],code=True);x["accepted_key_instructions"]=0
        self.assertEqual(ck(x)["line_status"],"outside")
    def test_21_rev2_nonleaf_zero_mixed_files_not_exempt(self):
        x=inst(leaf=[15]);x["accepted_key_instructions"]=0
        x["leaf_lines"].append(dict(file="/other.c",line=15))
        self.assertEqual(ck(x)["line_status"],"leaf_other_file")
if __name__=="__main__":unittest.main()
