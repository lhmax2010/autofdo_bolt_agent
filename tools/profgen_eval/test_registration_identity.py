"""Synthetic additions to existing identity fixtures (Q.5 #16)."""
import unittest
from registration_identity import *
from dwarf_inventory import linkage_name
from system_header_rule import group_scope

class Identity(unittest.TestCase):
    def test_only_MIPS(self):
        self.assertEqual(linkage_name({"x":{"attrs":{"MIPS_linkage_name":'"mips"'}}},"x"),"mips")
    def test_unresolved_outside_static(self):
        with self.assertRaises(ValueError):complete_gate([dict(id=1,scope="outside",name="static")],{1:None})
    def test_unresolved_clone(self):
        with self.assertRaises(ValueError):complete_gate([dict(id=1,name="f.cold.1")],{1:None})
        self.assertTrue(complete_gate([dict(id=1,name="f.cold.1")],{1:"reference_unexecuted"}))
    def test_tiny_unresolved_no_matched_outer(self):
        with self.assertRaises(ValueError):complete_gate([dict(id=1,mass=.00001)],{1:None})
    def test_partial_path_normalization_fails(self):
        row=dict(name="f",decl_file="other/a.h")
        self.assertEqual(candidates_for(row,[dict(name="f",file="a.h")]),[])
        with self.assertRaises(ValueError):complete_gate([dict(id=1)],{1:None})
    def test_omitted_suffix_normalization_missing(self):
        row=dict(name="f.__uniq.1",decl_file="a.c");refs=[dict(name="f",file="a.c")]
        self.assertEqual(len(candidates_for(row,refs)),1)
        self.assertNotEqual(row["name"],refs[0]["name"])
        with self.assertRaises(ValueError):complete_gate([dict(id=1)],{1:None})
    def test_mangling_mismatch(self):
        self.assertEqual(candidates_for(dict(name="_ZL3foov.__uniq.1",decl_file="a.c"),[dict(name="foo",file="a.c")]),[])
    def ext(self,**changes):
        row=dict(cu_name="libgcc2.c",producer="GNU C 14",path_normalized=True,producer_parsed=True)
        row.update(changes)
        return external_conclusion(row,[],set(),{("libgcc2.c","GNU C 14"):dict(link_source_verified=True,source_sha256="synthetic")})
    def test_GNU_C_positive(self):self.assertEqual(self.ext(),"not_instrumented")
    def test_GNU_AS_positive(self):
        row=dict(cu_name="lib1funcs.S",producer="GNU AS 2.43",path_normalized=True,producer_parsed=True)
        self.assertEqual(external_conclusion(row,[],set(),{("lib1funcs.S","GNU AS 2.43"):dict(link_source_verified=True,source_sha256="synthetic")}),"not_instrumented")
    def test_CU_filename_wrong(self):self.assertIsNone(self.ext(cu_name="wrong.c"))
    def test_producer_missing(self):self.assertIsNone(self.ext(producer=None))
    def test_producer_parse_failed(self):self.assertIsNone(self.ext(producer_parsed=False))
    def test_clang_missing_coverage_is_unresolved(self):self.assertIsNone(self.ext(producer="clang version 22.1.8"))
    def test_reference_candidate_before_external(self):
        row=dict(cu_name="libgcc2.c",producer="GNU C 14",path_normalized=True,producer_parsed=True)
        self.assertIsNone(external_conclusion(row,[dict(fnda=1)],set(),{}))
        self.assertEqual(group_scope(["not_instrumented","reference_executed"]),"in_mapping_scope")
    def test_full_inventory_not_selection(self):
        with self.assertRaises(ValueError):complete_gate([dict(id=1),dict(id=2)],{1:"reference_executed"})
    def test_variant_mismatch(self):
        with self.assertRaisesRegex(ValueError,"variant"):complete_gate([dict(id=1)],{1:"reference_executed"},False)

if __name__=="__main__":unittest.main()
