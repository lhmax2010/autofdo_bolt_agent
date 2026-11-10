"""Preserve every code DIE and update only positively closed external CUs."""
import collections,json
from pathlib import Path
from apply_header_ruling import rows
from pack_static_evidence import tables
from run_scoped import sha

BASE=Path("docs/profgen/eval/prep/evidence")
OUT=BASE/"ruling2"

def main():
    ext=json.loads((OUT/"external-cu-register.json").read_text())
    summaries=[]
    for obj in ("spike-thumb","spike-a32","ffmpeg-thumb","ffmpeg-a32"):
        old=BASE/"ruling1"/(obj+"-conclusions")
        bydie={r["die"]:r for r in ext.get(obj,{}).get("entries",[])}
        out=OUT/(obj+"-inventory");out.mkdir(exist_ok=True)
        current=[];counts=collections.Counter()
        for r in rows(old,"complete-inventory-*.csv"):
            entry=bydie.get(r["die"])
            if entry and entry["conclusion"]=="not_instrumented":
                r["conclusion"]="not_instrumented";r["category"]="external_cu_proven"
                evidence=str(OUT/"external-cu-register.json")+"#"+obj+":"+r["die"]
            elif r["category"]=="same_name_different_definition_file":
                r["category"]="macro_argument_spelling_scope_requires_ruling"
                evidence=str(OUT/(obj+"-macro-audit.json"))+"#"+r["die"]
            else:evidence=str(old/"index.json")+"#"+r["die"]
            counts[r["category"]]+=1
            current.append([r[k] for k in ["die","cu","raw_name","decl_file","decl_line","conclusion","category"]]+[evidence])
        parts=tables(out,"identities",["die","cu","raw_name","decl_file","decl_line","conclusion","category","evidence"],current)
        (out/"index.json").write_text(json.dumps({"parts":parts,"base_inventory":str(old/"index.json"),"base_index_sha256":sha(old/"index.json"),"note":"All original attributes/candidates remain in base inventory; row IDs are unchanged. No implicit closure."},indent=2)+"\n")
        summaries.append({"object":obj,"total":len(current),"categories":dict(counts),
                          "unresolved":sum(not r[5] for r in current)})
    (OUT/"closure-summary.json").write_text(json.dumps(summaries,indent=2)+"\n")
    print(json.dumps(summaries,indent=2))

if __name__=="__main__":main()
