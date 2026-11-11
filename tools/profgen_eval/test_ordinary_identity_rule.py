"""Synthetic identity fixtures; no formal sample profile is opened."""
import unittest
from ordinary_identity_rule import classify_ordinary
from apply_header_ruling import norm_name,norm_file
from dwarf_inventory import linkage_name
from system_header_rule import group_scope

class OrdinaryTests(unittest.TestCase):
    def run_case(self,decl=3,start=4,end=9,lines=(5,7,8),cdecl=3,extra=None):
        s=dict(decl_file="a.c",decl_line=decl)
        c=dict(file="a.c",start=start,end=end,fnda=1)
        return classify_ordinary(s,[c]+(extra or []),[dict(decl_file="a.c",decl_line=cdecl)],
                                 [dict(file="a.c",line=n) for n in lines])
    def test_brace_on_next_line(self):self.assertEqual(self.run_case()["conclusion"],"reference_executed")
    def test_three_line_signature(self):self.assertEqual(self.run_case(start=6,lines=(3,6,7))["conclusion"],"reference_executed")
    def test_codex_conditional_wrong_definition(self):
        r=self.run_case(decl=5,cdecl=3,start=3)
        self.assertIn("definition_declaration_conflict",r["reasons"]);self.assertEqual(r["conclusion"],"identity_ambiguous")
    def test_empty_lines_not_vacuous_proof(self):self.assertIn("empty_leaf_line_set",self.run_case(lines=())["reasons"])
    def test_signature_line(self):self.assertEqual(self.run_case(lines=(3,5))["conclusion"],"reference_executed")
    def test_line_in_other_definition(self):self.assertIn("leaf_line_outside_range",self.run_case(lines=(20,))["reasons"])
    def test_same_decl_different_body_ambiguous(self):self.assertEqual(self.run_case(extra=[dict(start=5,end=10,fnda=0)])["conclusion"],"identity_ambiguous")
    def test_no_nearest_candidate(self):self.assertEqual(self.run_case(extra=[dict(start=30,end=40,fnda=1)])["reasons"],["multiple_reference_candidates"])
    def test_variant_mismatch(self):self.assertIsNone(classify_ordinary({},[],[],[],False)["conclusion"])
    def test_missing_reference_not_out_of_scope(self):self.assertIsNone(classify_ordinary({},[],[],[])["conclusion"])
    def test_unexecuted_reference(self):
        r=classify_ordinary(dict(decl_file="a.c",decl_line=3),[dict(start=4,end=9,fnda=0)],
            [dict(decl_file="a.c",decl_line=3)],[dict(file="a.c",line=5)])
        self.assertEqual(r["conclusion"],"reference_unexecuted")
    def test_unique_suffix_only(self):
        self.assertEqual(norm_name("foo.__uniq.12"),"foo");self.assertNotEqual(norm_name("foo.cold.1"),"foo")
        self.assertNotEqual(norm_name("file.c:foo"),norm_name("_ZL3foov.__uniq.1"))
    def test_path_normalize_both_sides(self):self.assertEqual(norm_file("x/../a.c"),norm_file("./a.c"))
    def test_linkage_precedence(self):
        r={"a":{"attrs":{"MIPS_linkage_name":'"mips"',"linkage_name":'"standard"',"name":'"short"'}}}
        self.assertEqual(linkage_name(r,"a"),"mips")
        del r['a']['attrs']['MIPS_linkage_name'];r['a']['attrs']['abstract_origin']='0xb'
        r['0xb']={'attrs':{'MIPS_linkage_name':'"origin"'}}
        self.assertEqual(linkage_name(r,"a"),"standard")
        del r['a']['attrs']['linkage_name'];self.assertEqual(linkage_name(r,"a"),"origin")
        del r['a']['attrs']['abstract_origin'];self.assertEqual(linkage_name(r,"a"),"short")
    def test_specification_and_abstract_origin(self):
        r={'a':{'attrs':{'specification':'0xb'}},'0xb':{'attrs':{'linkage_name':'"linked"'}}}
        self.assertEqual(linkage_name(r,'a'),'linked')
        r['a']['attrs']={'abstract_origin':'0xb'};self.assertEqual(linkage_name(r,'a'),'linked')
    def test_external_group_does_not_hide_executed_inline(self):
        self.assertEqual(group_scope(['not_instrumented','reference_executed']),'in_mapping_scope')

if __name__=="__main__":unittest.main(verbosity=2)
