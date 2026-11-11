"""Synthetic v1.8 fixtures; never read any sampled profile."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import v18_rules as r

WORK = Path(__file__).resolve().parents[2]


def sequence(start=100, end=120, line=10, cu=0, section="1", sid="a"):
    return dict(cu=cu, section_index=section, id=sid, low=start, high=end,
                rows=[dict(address=start, file="f", line=line, file_resolved=True, end_sequence=False),
                      dict(address=end, file="f", line=0, file_resolved=True, end_sequence=True)])


def sections(start=100, end=200, executable=True, index="1"):
    return [dict(index=index, start=start, end=end, executable=executable)]


def evidence(seqs=None, secs=None, **kwargs):
    return {"C": dict(sequences=seqs if seqs is not None else [sequence()],
                      sections=secs if secs is not None else sections(), **kwargs)}


def conclusion(n=980):
    frac = lambda d: dict(numerator=n, denominator=d, ratio=n/d)
    return dict(object="A", status="eligible", domain_unresolved_lines=0,
                evaluation_domain=r.DOMAIN_EXPLANATION,
                coverage_3_views=dict(C0=frac(1210), C_dc=frac(1100), C=frac(1000)),
                coverage_3_prime=n/1500,
                code_bearing=dict(numerator=1000, denominator=1210, ratio=1000/1210),
                nonduplicated_outside=dict(numerator=100, denominator=1100, ratio=100/1100))


class DomainSynthetic(unittest.TestCase):
    def test_overlap_rejected(self):
        e=evidence([sequence(), sequence(end=110,line=20,sid="b")])
        c, seen, unknown, errors, checks=r.domain({("f",10),("f",20)},e)
        self.assertFalse(checks["C"]["passed"])
        self.assertFalse(seen)
        self.assertEqual(unknown,c)
        self.assertIn("C:overlapping_sequences",errors)

    def test_adjacent_sequences(self):
        result=r.domain({("f",10),("f",20)},evidence([sequence(),sequence(120,130,20,sid="b")]))
        self.assertEqual(len(result[0]),2)
        self.assertFalse(result[3])

    def test_different_sections_same_address(self):
        e=evidence([sequence(),sequence(section="2",line=20,sid="b")],
                   sections()+sections(index="2"))
        result=r.domain({("f",10),("f",20)},e)
        self.assertTrue(result[4]["C"]["passed"])
        self.assertEqual(len(result[0]),2)

    def test_different_CU(self):
        result=r.domain({("f",10),("f",20)},evidence([sequence(),sequence(cu=1,line=20)]))
        self.assertFalse(result[3])

    def test_overlap_outside_executable_section(self):
        result=r.domain({("f",10)},evidence([sequence(0,80),sequence(0,70,sid="b")]))
        self.assertTrue(result[4]["C"]["passed"])
        self.assertFalse(result[0])

    def test_executable_data_has_witness_but_no_key(self):
        k=("f",10)
        c,_,unknown,_,_=r.domain({k},evidence())
        u,_,ledger,_=r.ledger({k},c,{k:20},{k:{"no_key_line"}},unresolved=unknown)
        self.assertEqual(c,{k})
        self.assertFalse(u)
        self.assertEqual(ledger["loss"],20)

    def test_non_executable_section(self):
        self.assertFalse(r.domain({("f",10)},evidence(secs=sections(executable=False)))[0])

    def test_sequence_zero_below_text(self):
        result=r.domain({("f",10)},evidence([sequence(0,20)]))
        self.assertFalse(result[0])
        self.assertEqual(result[4]["C"]["low_sequences_count"],1)

    def test_partial_intersection(self):
        result=r.domain({("f",10)},evidence([sequence(90,110)]))
        self.assertEqual(result[0],{("f",10)})
        self.assertEqual(result[4]["C"]["partial_intervals_count"],1)
        self.assertEqual(result[4]["C"]["partial_intervals"][0]["interval"],[90,110])

    def test_duplicate_rows_last_wins(self):
        s=sequence()
        s["rows"].insert(1,dict(s["rows"][0],line=20))
        self.assertEqual(r.domain({("f",10),("f",20)},evidence([s]))[0],{("f",20)})

    def test_unresolved_with_key_excluded(self):
        k=("f",20); c,_,unknown,_,_=r.domain({k},evidence(exit_code=1))
        u,rs,cl,ol=r.ledger({k},c,{k:10},{},unresolved=unknown)
        self.assertFalse(u)
        self.assertEqual(rs[k],{"domain_unresolved"})
        self.assertEqual(cl["difference"],ol["difference"])

    def test_nonzero_exit_all_unseen_unknown(self):
        c0={("f",10),("f",20),("f",30)}
        result=r.domain(c0,evidence(exit_code=1))
        self.assertEqual(result[2],{("f",20),("f",30)})
        self.assertEqual(result[0],c0)

    def test_diagnostic_all_unseen_unknown(self):
        result=r.domain({("f",10),("f",20)},evidence(diagnostics="DWARF warning"))
        self.assertEqual(result[2],{("f",20)})

    def test_codex_denominator_dilution(self):
        k0,k1,k2,k3=[("f",n) for n in (10,20,30,40)]
        da={k0:980,k1:12,k2:8,k3:210}
        base={k1:{"identity_ambiguous"},k2:{"no_key_line"}}
        for failed in (False,True):
            c=set(da) if failed else set(da)-{k3}
            unknown={k3} if failed else set()
            u,_,cl,_=r.ledger(set(da),c,da,base,unresolved=unknown)
            den=cl["denominator"]
            gates={"identity_ambiguous":dict(exceeds_one_percent=1200>den)}
            status, reasons=r.registration(len(unknown),gates,980,den)
            self.assertNotEqual(status,"eligible")
            self.assertEqual(den,1210 if failed else 1000)
            self.assertEqual(cl["numerator"],980)
            if failed:
                self.assertEqual(status,"domain_evidence_incomplete")
                self.assertLess(12/den,.01)
            else:
                self.assertIn("identity_ambiguous",reasons)

    def test_zero_DA_unknown_blocks(self):
        k=("f",20);c,_,unknown,_,_=r.domain({k},evidence(exit_code=1))
        self.assertEqual(sum({k:0}[x] for x in unknown),0)
        self.assertEqual(r.registration(len(unknown),{},0,1)[0],"domain_evidence_incomplete")

    def test_nonzero_DA_unknown_blocks(self):
        self.assertEqual(r.registration(1,{},980,1210)[0],"domain_evidence_incomplete")

    def test_repair_to_witness(self):
        k=("f",10); c,_,unknown,_,_=r.domain({k},evidence())
        u,_,cl,_=r.ledger({k},c,{k:10},{},unresolved=unknown)
        self.assertEqual(u,{k})
        self.assertEqual(r.registration(len(unknown),{},cl["numerator"],cl["denominator"])[0],"eligible")

    def test_repair_to_proven_absence(self):
        c0={("f",10),("f",20)}
        c,_,unknown,_,_=r.domain(c0,evidence())
        u,rs,cl,ol=r.ledger(c0,c,{("f",10):10,("f",20):210},{},unresolved=unknown)
        self.assertFalse(unknown)
        self.assertEqual(rs[("f",20)],{"code_free_line"})
        self.assertEqual(ol["loss"],210)
        self.assertEqual(r.registration(0,{},cl["numerator"],cl["denominator"])[0],"eligible")

    def test_inlined_callsite_measurability_fixed(self):
        c0={("f",10),("f",20)}
        v=r.coverage_views(c0,{("f",10)},{("f",10)},
                           {("f",10):10,("f",20):20},{("f",20):"inlined_call_site"})
        self.assertEqual(v["coverage_3_views"]["C_dc"]["denominator"],30)


class ConclusionSynthetic(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=WORK/"temp")
        self.addCleanup(self.tmp.cleanup)
        self.dir=Path(self.tmp.name)
        self.good=conclusion()
        self.table=self.dir/"table.json"
        self.table.write_text(json.dumps({"objects":{"A":self.good,"B":dict(conclusion(970),object="B")}},allow_nan=False))
        self.digest=hashlib.sha256(self.table.read_bytes()).hexdigest()

    def rejected(self, payload, sha=None, object_id="A"):
        for existing in (False,True):
            out=self.dir/("existing.json" if existing else "absent.json")
            if existing:out.write_bytes(b"preserve old bytes")
            with self.assertRaises((ValueError,KeyError,TypeError)):
                r.write_conclusion(out,payload,self.table,sha or self.digest,object_id)
            self.assertEqual(out.read_bytes() if out.exists() else None,
                             b"preserve old bytes" if existing else None)

    def test_valid_zero_numerator(self):
        self.good=conclusion(0)
        self.table.write_text(json.dumps({"objects":{"A":self.good}},allow_nan=False))
        h=hashlib.sha256(self.table.read_bytes()).hexdigest()
        out=self.dir/"valid.json"
        r.write_conclusion(out,self.good,self.table,h,"A")
        self.assertEqual(json.loads(out.read_text()),self.good)

    def test_sha_mismatch(self):
        self.rejected(self.good,sha="0"*64)

    def test_cross_object(self):
        self.rejected(self.good,object_id="B")

    def test_table_off_by_one(self):
        p=copy.deepcopy(self.good)
        for f in p["coverage_3_views"].values():
            f["numerator"]+=1;f["ratio"]=f["numerator"]/f["denominator"]
        self.rejected(p)

    def test_undefined_diagnostic_only(self):
        p=copy.deepcopy(self.good);p["coverage_3_views"]["C"]["denominator"]=0
        self.rejected(p)
        out=self.dir/"diagnostic.json"
        r.write_diagnostic(out,["zero_denominator"],{"ratio":None})
        result=json.loads(out.read_text())
        self.assertFalse(result["quality_conclusion_defined"])
        self.assertEqual(result["registration_status"],"not_assessed")

    def test_nonfinite_diagnostic_not_written(self):
        out=self.dir/"diagnostic.json";out.write_bytes(b"old")
        with self.assertRaises(ValueError):r.write_diagnostic(out,["bad"],{"ratio":float("nan")})
        self.assertEqual(out.read_bytes(),b"old")


# Each mutation is an independently named synthetic test; writer checks both
# absent and pre-existing output paths for every rejection.
def add_bad(name, mutate):
    def test(self):
        p=copy.deepcopy(self.good);mutate(p);self.rejected(p)
    setattr(ConclusionSynthetic,"test_"+name,test)


add_bad("all_null",lambda p:p.update({k:None for k in r.FIELDS}))
add_bad("empty_objects",lambda p:p.update({k:{} for k in r.FIELDS}))
add_bad("nan",lambda p:p["coverage_3_views"]["C"].update(ratio=float("nan")))
add_bad("infinity",lambda p:p["coverage_3_views"]["C"].update(ratio=float("inf")))
add_bad("zero_denominator",lambda p:p["coverage_3_views"]["C"].update(denominator=0))
add_bad("unequal_numerators",lambda p:p["coverage_3_views"]["C"].update(numerator=979,ratio=.979))
add_bad("unordered_denominators",lambda p:p["coverage_3_views"]["C"].update(denominator=1200,ratio=980/1200))
add_bad("inconsistent_ratio",lambda p:p["coverage_3_views"]["C"].update(ratio=.9))
add_bad("negative_integer",lambda p:p["coverage_3_views"]["C"].update(numerator=-1,ratio=-.001))
add_bad("float_denominator",lambda p:p["coverage_3_views"]["C"].update(denominator=1000.0))
add_bad("bool_integer",lambda p:p["coverage_3_views"]["C"].update(numerator=True))
add_bad("missing_domain",lambda p:p.pop("evaluation_domain"))
add_bad("instruction_claim",lambda p:p.update(evaluation_domain=r.DOMAIN_EXPLANATION+" 已证明每行都有指令"))
add_bad("missing_view",lambda p:p["coverage_3_views"].pop("C0"))
add_bad("unknown_state",lambda p:p.update(status="domain_evidence_incomplete"))
add_bad("unknown_zero_DA_count",lambda p:p.update(domain_unresolved_lines=1))
add_bad("nested_nonfinite_extra_field",lambda p:p.update(extra={"value":float("inf")}))
add_bad("prime_differs_from_table",lambda p:p.update(coverage_3_prime=.2))
add_bad("bearing_differs_from_table",lambda p:p["code_bearing"].update(numerator=999,ratio=999/1210))
add_bad("outside_differs_from_table",lambda p:p["nonduplicated_outside"].update(numerator=99,ratio=99/1100))


if __name__=="__main__":
    unittest.main()
