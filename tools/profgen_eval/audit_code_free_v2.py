"""Read-only final proof checks for the code_free descriptive update."""
import collections,json
from pathlib import Path
from code_free_v2_lex import OUT,OLD
from code_free_v2_rules import CATEGORIES
from ruling3_union import dump
from run_scoped import WORK,sha
from apply_header_ruling import rows
def main():
    frozen=json.loads((OUT/"immutable-inputs.json").read_text())
    for r in frozen:assert sha(WORK/r["path"])==r["sha256"],r["path"]
    checked=[]
    for obj in ("spike-thumb","spike-a32","ffmpeg-thumb","ffmpeg-a32"):
        dest=OUT/(obj+"-classification")
        summary=json.loads((dest/"summary.json").read_text());old=json.loads((OLD/(obj+"-code-free-classification/summary.json")).read_text())
        for kind,values in old["categories"].items():
            xs=[r for r in summary["cross"] if r["old"]==kind]
            assert sum(r["lines"] for r in xs)==values["lines"]
            assert sum(r["DA"] for r in xs)==values["DA"]
        for kind,values in summary["categories"].items():
            xs=[r for r in summary["cross"] if r["new"]==kind]
            assert sum(r["lines"] for r in xs)==values["lines"]
            assert sum(r["DA"] for r in xs)==values["DA"]
        assert old["categories"]["asm_interior"]["DA"]==summary["categories"]["asm_interior"]["DA"]
        assert old["categories"]["asm_interior"]["lines"]==summary["categories"]["asm_interior"]["lines"]
        records=list(rows(dest,"lines-*.csv"))
        assert len({(r["file"],r["line"]) for r in records})==len(records)
        for kind in CATEGORIES:
            r=[r for r in records if r["category"]==kind]
            assert len(r)==summary["categories"][kind]["lines"]
            assert sum(int(x["DA"]) for x in r)==summary["categories"][kind]["DA"]
        assert sum(v["DA"] for v in summary["own_statement_kinds"].values())==summary["categories"]["own_stmt_no_code"]["DA"]
        assert sum(v["lines"] for v in summary["own_statement_kinds"].values())==summary["categories"]["own_stmt_no_code"]["lines"]
        index=json.loads((dest/"index.json").read_text())
        for r in index["parts"]:assert sha(Path(r["path"]))==r["sha256"]
        assert sha(dest/"summary.json")==index["summary_sha256"]
        checked.append(dict(object=obj,cross_marginals_equal=True,each_line_once=True,asm_unchanged=True,own_subtypes_conserved=True))
    files=[p for p in OUT.rglob("*") if p.is_file()]
    assert all(p.stat().st_size<1000000 for p in files)
    dump(OUT/"audit.json",dict(objects=checked,unchanged_old_files=len(frozen),max_new_file=max(p.stat().st_size for p in files),
        command=["python3","tools/profgen_eval/audit_code_free_v2.py"]))
    print(json.dumps(checked))
if __name__=="__main__":main()
