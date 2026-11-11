"""Static-only v1.8 acceptance, including SHA-backed candidate-table gates."""
import hashlib
import json
import subprocess
import unittest
from pathlib import Path
from v18_domain import OUT, TEMP, BASE, dump
from v18_rules import domain_sha, validate_conclusion, write_conclusion
from run_scoped import WORK, sha
from apply_header_ruling import rows

OBJECTS=("spike-thumb","spike-a32","ffmpeg-thumb","ffmpeg-a32")
PREVIOUS=BASE/"identity-gate/v17-recompute"
BASE_COMMIT="aa77cd75402b013d2ec877830acff9ecb1e495e6"


def test_ids(test):
    if isinstance(test,unittest.TestSuite):
        for item in test:
            yield from test_ids(item)
    else:
        yield test.id()


def main():
    doc=WORK/"docs/profgen/design/02_llvm_profgen_enhance_design_v1.8.md"
    assert sha(doc)=="ae667bd61470118179f6876c912285b7c57ab22518640c2af9f42103ad428e59"
    assert not Path("/home/linhao/Downloads/02_llvm_profgen_enhance_design_v1.8.md").exists()
    paths=subprocess.check_output(["git","ls-tree","-r","--name-only",BASE_COMMIT,
                                   "--","tools/profgen_eval"],text=True).splitlines()
    tests=[]
    for path in paths:
        if Path(path).name.startswith("test_") and path.endswith(".py"):
            original=subprocess.check_output(["git","show",BASE_COMMIT+":"+path])
            assert hashlib.sha256(original).hexdigest()==sha(WORK/path)
            tests.append(dict(path=path,sha256=sha(WORK/path)))
    suite=unittest.defaultTestLoader.discover(str(WORK/"tools/profgen_eval"),pattern="test_*.py")
    names=list(test_ids(suite))
    assert len(names)==250
    dump(OUT/"test-inventory.json",dict(count=len(names),tests=names,original_count=205,
         new_count=45,original_files=tests,original_files_unchanged=True))
    changed=subprocess.check_output(["git","diff",BASE_COMMIT,"--name-only","--",
        "docs/profgen/eval/prep/evidence/identity-gate/v17-recompute",
        "tools/profgen_eval/v17*"],text=True)
    assert not changed,changed
    objects={};inputs=[]
    for obj in OBJECTS:
        new=OUT/(obj+"-static");old=PREVIOUS/(obj+"-static")
        comparison=json.loads((new/"comparison.json").read_text())
        assert not comparison["differences"]
        summary=json.loads((new/"summary.json").read_text())
        for prefix in ("U","C-exclusions","C0-exclusions","weights"):
            assert list(rows(new,prefix+"-*.csv"))==list(rows(old,prefix+"-*.csv"))
        classes=json.loads((OUT/(obj+"-classification/summary.json")).read_text())
        prior_classes=json.loads((PREVIOUS/(obj+"-classification/summary.json")).read_text())
        for field in ("categories","own_statement_kinds","cross","difference","exactly_one_class"):
            assert classes[field]==prior_classes[field],(obj,field)
        old_details=list(rows(PREVIOUS/(obj+"-classification"),"lines-*.csv"))
        new_details=list(rows(OUT/(obj+"-classification"),"lines-*.csv"))
        assert len(old_details)==len(new_details)
        for a,b in zip(old_details,new_details):
            assert {k:v for k,v in a.items() if k!="description"}=={k:v for k,v in b.items() if k!="description"}
            if a["category"]=="own_stmt_no_code":
                assert b["description"]=="未取得行表归属见证"
            else:assert a["description"]==b["description"]
        d=OUT/(obj+"-domain")
        di=json.loads((d/"index.json").read_text())
        previous=json.loads((PREVIOUS/(obj+"-domain/index.json")).read_text())
        for key in ("C_sha256","C_lines","R_C","domain_unresolved_lines","domain_unresolved_DA"):
            assert di[key]==previous[key]
        c={(r["file"],int(r["line"])) for r in rows(d,"lines-*.csv")}
        c0={(r["file"],r["line"]) for r in json.loads((TEMP/(obj+"-C0.json")).read_text())}
        cc={(r["file"],int(r["line"])):r["category"] for r in rows(OUT/(obj+"-classification"),"lines-*.csv")}
        dc=c0-{k for k,v in cc.items() if v in ("asm_interior","structural_line","expr_continuation")}
        u={(r["file"],int(r["line"])) for r in rows(new,"U-*.csv")}
        assert u<=c<=dc<=c0
        assert domain_sha(c)==summary["C_sha256"]
        assert summary["ledger_C_to_U"]["difference"]==summary["ledger_C0_to_U"]["difference"]==0
        for m in di["raw"]:
            assert sha(Path(m["elf"]))==m["elf_sha256"]
            assert sha(Path(m["output"]))==m["output_sha256"]
            pre=di["sequence_checks"][m["stage"]]
            assert pre["passed"]
            assert sha(Path(pre["raw"]))==pre["raw_sha256"]
            inputs.append(dict(object=obj,**m,preconditions=pre))
        table=new/"candidate-table.json"
        payload=json.loads(table.read_text())["objects"][obj]
        assert validate_conclusion(payload,table,sha(table),obj)
        # Writer tests use only a static candidate fixture, clearly not a RUN
        # or actual registered quality conclusion.
        fixture=TEMP/(obj+"-candidate-gate-fixture.json")
        write_conclusion(fixture,payload,table,sha(table),obj)
        assert json.loads(fixture.read_text())==payload
        objects[obj]=dict(summary_sha256=sha(new/"summary.json"),
            C_sha256=domain_sha(c),U_sha256=domain_sha(u),C_dc_sha256=domain_sha(dc),
            numeric_differences={},ledgers_difference=[0,0],classification_unchanged=True,
            candidate_gate_passed=True,actual_registration=False,
            inlined_call_site=classes["categories"]["inlined_call_site"])
    dump(OUT/"eight-inputs-index.json",inputs)
    source=WORK/"src/llvm/llvm/lib/DebugInfo/DWARF/DWARFDebugLine.cpp"
    lines=source.read_text().splitlines()
    excerpt="Source: "+str(source)+"\nSHA-256: "+sha(source)+"\n"
    excerpt+="\n".join(str(i)+":"+(" "+lines[i-1] if lines[i-1] else "") for i in range(1271,1353))+"\n"
    (OUT/"compiler-source.txt").write_text(excerpt)
    dump(OUT/"final-audit.json",dict(objects=objects,tests=250,new_tests=45,
        design_sha256=sha(doc),input_count=len(inputs),source_sha256=sha(source),
        formal_profiles_read=False,amendment3_registered=False,
        unchanged_historical_artifacts=True,numeric_differences={}))
    for path in OUT.rglob("*"):
        if path.is_file():
            assert path.stat().st_size<1000000,(str(path),path.stat().st_size)
    print(json.dumps(dict(passed=True,objects=objects,tests=250),ensure_ascii=False))

if __name__=="__main__":
    main()
