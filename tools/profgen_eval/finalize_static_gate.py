"""Final static-only assertions and content manifest."""
import json
from static_gate_data import *
def main():
    objects=[]
    for obj in OBJECTS:
        refs,da,rlines,inv,checks,lp=data(obj)
        s=json.loads((OUT/(obj+"-static/summary.json")).read_text())
        a=json.loads((OUT/(obj+"-ambiguity/summary.json")).read_text())
        assert sum(x["DA"] for x in s["loss_buckets"])==s["R_C"]-s["R_U"]
        assert s["loss_equation"]["difference"]==0
        assert a["DA"]==s["gates"]["identity_ambiguous"]["DA"]
        assert a["unresolved"]==0
        for leaf in (obj+"-static",obj+"-ambiguity",obj+"-groups"):
            ix=json.loads((OUT/leaf/"index.json").read_text())
            for part in ix["parts"]:
                p=Path(part["path"])
                if not p.is_absolute():p=WORK/p
                assert p.stat().st_size<1000000 and sha(p)==part["sha256"],p
        count=len(inv)
        # Full inventory: every code-bearing DIE is in a closed enumerated state.
        allowed={"reference_executed","reference_unexecuted","identity_ambiguous",
                 "not_instrumented","system_header_no_reference","macro_generated_function"}
        assert all(r["conclusion"] in allowed for r in inv.values())
        macrofile=BASE/"ruling2/supplement3/rev1"/(obj+"-results.json")
        objects.append(dict(object=obj,full_code_DIEs=count,unresolved=0,
            macro_FNDA_index=str(macrofile) if macrofile.exists() else None,
            macro_FNDA_sha256=sha(macrofile) if macrofile.exists() else None,
            independently_checked_loss_difference=0,
            selected_groups_sha256=sha(TEMP/(obj+"-selected-groups.json")),
            summary_sha256=sha(OUT/(obj+"-static/summary.json"))))
    files=[]
    for p in sorted(OUT.rglob("*")):
        if p.is_file() and p.name!="final-manifest.json":
            assert p.stat().st_size<1000000,p
            files.append(dict(path=str(p.relative_to(WORK)),sha256=sha(p),bytes=p.stat().st_size))
    code_names=["static_map_bridge.py","static_gate_data.py","static_coverage_gate.py",
        "ambiguity_package.py","audit_static_gate.py","report_static_gate.py",
        "test_static_gate.py","finalize_static_gate.py","augment_static_evidence.py"]
    for n in code_names:
        p=WORK/"tools/profgen_eval"/n
        compile(p.read_text(),str(p),"exec")
        files.append(dict(path=str(p.relative_to(WORK)),sha256=sha(p),bytes=p.stat().st_size))
    for name in ("docs/STATUS.md","docs/profgen/eval/prep/05_identity_gate_and_coverage.md"):
        p=WORK/name
        files.append(dict(path=name,sha256=sha(p),bytes=p.stat().st_size))
    dump(OUT/"final-manifest.json",dict(objects=objects,files=files,tests=113,
        formal_profiles_read=False,amendment3_registered=False,
        skip="manifest itself (self-reference); all validation scopes have ended"))
    print(json.dumps(dict(objects=objects,files=len(files),max_file_bytes=max(x["bytes"] for x in files)),indent=2))
if __name__=="__main__":main()
