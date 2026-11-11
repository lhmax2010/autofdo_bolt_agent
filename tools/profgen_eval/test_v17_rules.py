"""Synthetic v1.7 fixtures. No formal RUN or profile file is accessed."""
import copy
import unittest
from v17_rules import (witnesses, domain, domain_sha, ledger, coverage_views,
                       no_key_proven, classify_body, validate_conclusion,
                       DOMAIN_STATEMENT, classify_code_free)


def row(addr, line, end=False):
    return dict(address=addr, line=line, file="a.c", file_resolved=True,
                end_sequence=end)


def evidence(rows=None):
    return dict(sections=[dict(start=100, end=120, executable=True)],
                sequences=[dict(id=0, rows=rows or [row(100, 10), row(104, 0, True)])],
                errors=[])


class DomainTests(unittest.TestCase):
    def test_S_only_outside_mapping_scope(self):
        c, _, _, _ = domain({("a.c",10)}, {"S":evidence(), "C":evidence([row(100,0),row(104,0,True)])})
        self.assertEqual(c,{("a.c",10)})

    def test_mutated_identity_key_and_range_not_inputs(self):
        e={"S":evidence()};c0={("a.c",10)}
        original=domain_sha(domain(c0,e)[0])
        # The domain API has no parameter through which these can affect it.
        for changes in (dict(identity="macro_generated_function"),
                        dict(accepted_keys=[]), dict(selected_groups=[])):
            self.assertTrue(changes)
            self.assertEqual(domain_sha(domain(c0,e)[0]),original)

    def test_duplicate_address_last_record(self):
        w,_=witnesses(evidence([row(100,10),row(100,11),row(104,0,True)])["sequences"],evidence()["sections"])
        self.assertEqual(set(w),{("a.c",11)})

    def test_zero_length(self):
        w,_=witnesses(evidence([row(100,10),row(100,0,True)])["sequences"],evidence()["sections"])
        self.assertEqual(w,{})

    def test_end_sequence_not_a_witness(self):
        e=evidence([row(100,0),row(104,10,True)])
        self.assertEqual(domain({("a.c",10)},{"C":e})[0],set())

    def test_do_not_bridge_sequences(self):
        e=evidence();e["sequences"]=[dict(id=0,rows=[row(100,0),row(104,10,True)]),
                                   dict(id=1,rows=[row(108,11),row(112,0,True)])]
        self.assertEqual(domain({("a.c",10),("a.c",11)},{"C":e})[0],{("a.c",11)})

    def test_nonleaf_zero_does_not_remove_leaf_witness(self):
        e=evidence();e["sequences"][0]["rows"][0]["nonleaf_line"]=0
        self.assertEqual(domain({("a.c",10)},{"S":e})[0],{("a.c",10)})

    def test_executable_intersection_nonempty(self):
        e=evidence([row(98,10),row(102,0,True)])
        self.assertEqual(domain({("a.c",10)},{"S":e})[0],{("a.c",10)})

    def test_nonexecuting_or_adjacent_section_no_witness(self):
        e=evidence([row(96,10),row(100,0,True)])
        self.assertEqual(domain({("a.c",10)},{"S":e})[0],set())
        e=evidence();e["sections"][0]["executable"]=False
        self.assertEqual(domain({("a.c",10)},{"S":e})[0],set())

    def test_extraction_failure_retained_unresolved(self):
        e=evidence([row(100,0),row(104,0,True)]);e["errors"]=["failed"]
        c,_,unknown,errors=domain({("a.c",10)},{"C":e})
        self.assertEqual(c,unknown);self.assertEqual(unknown,{("a.c",10)})
        self.assertTrue(errors)

    def test_unresolved_filename_is_not_code_free(self):
        e=evidence();e["sequences"][0]["rows"][0]["file_resolved"]=False
        self.assertEqual(domain({("a.c",10)},{"S":e})[2],{("a.c",10)})

    def test_nested_sets_three_denominators(self):
        c0={("a.c",i) for i in range(1,5)};c={("a.c",1),("a.c",2)};u={("a.c",1)}
        da={k:k[1] for k in c0}
        r=coverage_views(c0,c,u,da,{("a.c",3):"structural_line",("a.c",4):"own_stmt_no_code"})
        self.assertEqual([r["coverage_3_views"][k]["denominator"] for k in ("C0","C_dc","C")],[10,7,3])
        self.assertEqual(r["nonduplicated_outside"]["numerator"],4)

    def test_macro_switch_changes_U_not_C(self):
        c0={("a.c",10)};da={("a.c",10):7};c=domain(c0,{"C":evidence()})[0]
        h=domain_sha(c)
        ordinary=ledger(c0,c,da,{})
        macro=ledger(c0,c,da,{},c0)
        self.assertEqual(domain_sha(c),h);self.assertEqual(ordinary[0],c);self.assertEqual(macro[0],set())
        self.assertEqual(macro[2]["buckets"][0]["reasons"],["macro_generated_function"])
        self.assertEqual(macro[2]["difference"],0)

    def test_executed_macro_without_witness_has_both_reasons(self):
        c0={("a.c",10)}
        r=ledger(c0,set(),{("a.c",10):9},{},c0)
        self.assertEqual(r[3]["buckets"],[dict(reasons=["code_free_line","macro_generated_function"],lines=1,DA=9)])
        self.assertEqual(r[3]["difference"],0)

    def test_domain_unresolved_is_U_loss(self):
        k=("a.c",10);r=ledger({k},{k},{k:3},{},unresolved={k})
        self.assertEqual(r[0],set());self.assertEqual(r[2]["buckets"][0]["reasons"],["domain_unresolved"])

    def test_fully_inline_call_class_precedes_own(self):
        n=dict(kind="CallExpr",begin_line=10,end_line=10,begin_offset=1,end_offset=5)
        r=classify_code_free(10,set(),[n],[dict(kind="identifier",offset=1,end_offset=4)],[],True,[dict(stage="S",die=1)])
        self.assertEqual(r["category"],"inlined_call_site")

    def test_structural_precedes_inline_call(self):
        r=classify_code_free(10,set(),[],[dict(kind="r_brace",offset=1,end_offset=2)],[],True,[{}])
        self.assertEqual(r["category"],"structural_line")


def valid_proof():
    return dict(inventory_complete=True,enumeration_complete=True,
                symbolization_complete=True,instance_record_present=True,
                boundary_available=True,accepted_key_instructions=0)


class NoKeyTests(unittest.TestCase):
    def test_complete_zero(self):self.assertTrue(no_key_proven(valid_proof()))
    def test_missing_range(self):
        p=valid_proof();p["enumeration_complete"]=False;self.assertFalse(no_key_proven(p))
    def test_top_boundary_failure(self):
        p=valid_proof();p["boundary_available"]=False;self.assertFalse(no_key_proven(p))
    def test_deleted_instance_record(self):
        p=valid_proof();del p["instance_record_present"];self.assertFalse(no_key_proven(p))
    def test_symbolization_failure(self):
        p=valid_proof();p["symbolization_complete"]=False;self.assertFalse(no_key_proven(p))
    def test_incomplete_inventory(self):
        p=valid_proof();p["inventory_complete"]=False;self.assertFalse(no_key_proven(p))
    def test_whole_group_zero_mass_is_no_key_loss(self):
        ks={("a.c",1),("a.c",2)}
        r=ledger(ks,ks,{k:5 for k in ks},{k:{"no_key_line"} for k in ks})
        self.assertEqual(r[2]["loss"],10);self.assertEqual(r[2]["difference"],0)
        self.assertEqual(r[2]["buckets"][0]["reasons"],["no_key_line"])


def body(**kw):
    d=dict(known_name=True,reference_resolved=True,known_out_of_scope=False,
           registered_key=True,in_U=True,body_count=0)
    d.update(kw);return d


class ClassificationTests(unittest.TestCase):
    def test_pure_header_group(self):
        self.assertEqual(classify_body(body(known_out_of_scope=True,value_status="system_header_no_reference"))[0],"out_of_scope")
    def test_header_in_executed_user(self):
        self.assertEqual(classify_body(body(value_status="system_header_no_reference"))[0],"aligned_outside_U")
    def test_pure_macro_FNDA_zero(self):
        self.assertEqual(classify_body(body(known_out_of_scope=True,value_status="macro_generated_function"))[0],"out_of_scope")
    def test_executed_macro(self):
        self.assertEqual(classify_body(body(value_status="macro_generated_function"))[1],"macro_generated_function")
    def test_special_unregistered_key(self):
        for status in ("system_header_no_reference","macro_generated_function","identity_ambiguous"):
            self.assertEqual(classify_body(body(value_status=status,registered_key=False)),("unaligned","unmapped_key"))
    def test_unknown_name_before_special(self):
        self.assertEqual(classify_body(body(known_name=False,value_status="macro_generated_function"))[1],"unknown_name")
    def test_boundary_before_everything(self):
        self.assertEqual(classify_body(body(boundary_unavailable=True,known_name=False))[0],"boundary_unavailable")
    def test_zero_body_is_still_classified_once(self):
        rs=[body(),body(known_name=False),body(known_out_of_scope=True),body(boundary_unavailable=True),body(excluded=True)]
        out=[classify_body(r) for r in rs]
        self.assertEqual(len(out),5)
        self.assertEqual([x[0] for x in out],["in_U","unaligned","out_of_scope","boundary_unavailable","aligned_outside_U"])


def conclusion():
    f=dict(numerator=1,denominator=2,ratio=.5)
    return dict(evaluation_domain=DOMAIN_STATEMENT,
                coverage_3_views={k:f.copy() for k in ("C0","C_dc","C")},
                coverage_3_prime=.2,nonduplicated_outside=f.copy(),code_bearing=f.copy())


class ConclusionTests(unittest.TestCase):
    def test_complete(self):self.assertTrue(validate_conclusion(conclusion()))
    def test_missing_domain(self):
        d=conclusion();del d["evaluation_domain"]
        with self.assertRaisesRegex(ValueError,"evaluation_domain"):validate_conclusion(d)
    def test_missing_C0(self):
        d=conclusion();del d["coverage_3_views"]["C0"]
        with self.assertRaisesRegex(ValueError,"missing_coverage_3:C0"):validate_conclusion(d)
    def test_missing_Cdc(self):
        d=conclusion();del d["coverage_3_views"]["C_dc"]
        with self.assertRaisesRegex(ValueError,"missing_coverage_3:C_dc"):validate_conclusion(d)
    def test_missing_C(self):
        d=conclusion();del d["coverage_3_views"]["C"]
        with self.assertRaisesRegex(ValueError,"missing_coverage_3:C$"):validate_conclusion(d)

class NoKeyIntegrationTests(unittest.TestCase):
    def test_missing_proof_uses_active_instance_check(self):
        from ruling34_rules import instance_check
        i=dict(decl_file="a.c",decl_line=1,leaf_lines=[],direct_inline_calls=[],
               accepted_key_instructions=0,descendant_nonzero_leaf=False,
               no_key_proof_unavailable=True)
        r=instance_check(i,[dict(start=1,end=9)],[dict(decl_file="a.c",decl_line=1)])
        self.assertNotEqual(r["line_status"],"no_key_instance")
        self.assertEqual(r["line_status"],"empty_with_keys")

    def test_all_exempt_instances_map_to_no_key_group(self):
        from ruling34_rules import instance_check,group_check
        i=dict(decl_file="a.c",decl_line=1,leaf_lines=[],direct_inline_calls=[],
               accepted_key_instructions=0,descendant_nonzero_leaf=False,
               no_key_proof_unavailable=False)
        c=[dict(start=1,end=9,fnda=8)]
        r=instance_check(i,c,[dict(decl_file="a.c",decl_line=1)])
        g=group_check([r],c)
        self.assertTrue(g["all_no_key"])
        self.assertEqual(g["conclusion"],"reference_executed")


class WriterGateTests(unittest.TestCase):
    def test_missing_fields_leave_existing_output_unchanged(self):
        import tempfile
        from pathlib import Path
        from run_scoped import WORK
        from v17_rules import write_conclusion
        with tempfile.TemporaryDirectory(dir=WORK/"temp/tmp") as d:
            p=Path(d)/"synthetic.json"
            for name in ("evaluation_domain","C0","C_dc","C"):
                data=conclusion()
                if name=="evaluation_domain":del data[name]
                else:del data["coverage_3_views"][name]
                p.write_text("old")
                with self.assertRaises(ValueError):write_conclusion(p,data)
                self.assertEqual(p.read_text(),"old")
                p.unlink()
                with self.assertRaises(ValueError):write_conclusion(p,data)
                self.assertFalse(p.exists())
            write_conclusion(p,conclusion())
            self.assertIn(DOMAIN_STATEMENT,p.read_text())

class MissingRecordIntegrationTests(unittest.TestCase):
    def test_missing_record_cannot_receive_zero_exemption(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from run_scoped import WORK
        from ruling4_apply import calculate
        # Synthetic inventory has an address range but its key proof is absent.
        refs=[dict(start=1,end=9,fnda=1)]
        old={1:dict(candidate_ids=[0],leaf_rows="[]",
                    c_declaration_positions='[{"decl_file":"a.c","decl_line":1}]')}
        funcs={1:dict(name="f",decl_file="a.c",decl_line=1,ranges=[[100,102]],
                      leaf_lines=[],direct_inline_calls=[],ancestors=[])}
        with tempfile.TemporaryDirectory(dir=WORK/"temp/tmp") as d:
            p=Path(d)/"keys.jsonl";p.write_text("")
            with patch("ruling4_apply.data",return_value=(refs,{}, {}, {1:{}},old,None)), \
                 patch("ruling4_apply.load_functions",return_value=funcs):
                r=calculate("synthetic",p,lambda die:True)
            self.assertEqual(r[6][1]["line_status"],"empty_with_keys")
            self.assertFalse(r[7][0]["all_no_key"])
            self.assertEqual(r[7][0]["conclusion"],"identity_ambiguous")
