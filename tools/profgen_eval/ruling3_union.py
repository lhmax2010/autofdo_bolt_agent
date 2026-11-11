"""C domain from line tables only; no key/identity maps are read here."""
import collections,json,sys
from pathlib import Path
from run_scoped import WORK,sha
from ruling3_domain import reference,records,functions
from apply_header_ruling import rows,norm_file
from pack_static_evidence import tables
OLD=WORK/"docs/profgen/eval/prep/evidence/identity-gate/ruling3-4"
OUT=WORK/"docs/profgen/eval/prep/evidence/identity-gate/ruling3-rev1"
TEMP=WORK/"temp/prep-ruling3-rev1"
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
def union_domain(original,c_records,s_records):
    a={k for k in c_records if k in original}
    b={k for k in s_records if k in original}
    return a|b,a,b
def classify_line(file,line,newc,ranges,available):
    if not available:return dict(category="ast_unavailable",witness=None)
    candidates=[r for r in ranges if r["file"]==file and r["begin_line"]<=line<=r["end_line"]]
    order=lambda r:(r["end_line"]-r["begin_line"],r.get("end_offset",0)-r.get("begin_offset",0),r["kind"],r.get("tu",""))
    asm=[r for r in candidates if r["kind"]=="GCCAsmStmt" and (file,line) not in newc]
    if asm:return dict(category="asm_interior",witness=min(asm,key=order))
    cont=[r for r in candidates if r["begin_line"]<r["end_line"] and
          any((file,n) in newc for n in range(r["begin_line"],r["end_line"]+1))]
    if cont:return dict(category="stmt_continuation",witness=min(cont,key=order))
    return dict(category="other",witness=min(candidates,key=order) if candidates else None)
def main(obj):
    refs,da,rlines,owners,lp=reference(obj);original=set(owners)
    # This is a function-range selection, not an address->key/identity mapping.
    selection=WORK/"temp/prep-static-gate"/(obj+"-selected-groups.json")
    names=set(json.loads(selection.read_text()))
    fs=functions(obj,"S")
    selected={d for d,f in fs.items() if f["tag"]=="subprogram" and f["ranges"] and f["name"] in names}
    assert {fs[d]["name"] for d in selected}==names
    cr={(r["file"],int(r["line"])):r for r in rows(OLD/(obj+"-C-domain"),"code-lines-*.csv")}
    sr={}
    for r in records(obj,"S","line_row"):
        if r["end_sequence"] or not r["file_resolved"] or r["line"]==0:continue
        chain=r["dies_leaf_to_root"]
        if not chain or not set(chain)&selected:continue
        key=(norm_file(r["file"]),r["line"])
        if key in original:sr.setdefault(key,r)
    domain,a,b=union_domain(original,cr,sr)
    dest=OUT/(obj+"-domain");dest.mkdir()
    parts=tables(dest,"lines",["file","line","DA","C_witness","S_leaf_row_witness","from_C","from_S"],
         ([*k,da[k],cr.get(k),sr.get(k),k in a,k in b] for k in sorted(domain)))
    parts+=tables(dest,"new-from-S",["file","line","DA","S_leaf_row_witness"],
         ([*k,da[k],sr[k]] for k in sorted(b-a)))
    parts+=tables(dest,"code-free",["file","line","DA"],([*k,da[k]] for k in sorted(original-domain)))
    selection_meta=dict(path=str(selection),sha256=sha(selection),selected_top_functions=len(selected),
       source="pre-existing mapping-range function names; no mapping table, key acceptance or identity conclusions consumed")
    s_meta=json.loads((OLD/(obj+"-S-dwarf-command.json")).read_text())
    assert sha(Path(s_meta["output"]))==s_meta["output_sha256"]
    summary=dict(object=obj,original_C_lines=len(original),original_R_C=sum(da[k] for k in original),
       C_only_lines=len(a),C_only_R_C=sum(da[k] for k in a),union_lines=len(domain),union_R_C=sum(da[k] for k in domain),
       S_only_added_lines=len(b-a),S_only_added_DA=sum(da[k] for k in b-a),
       code_free_lines=len(original-domain),code_free_DA=sum(da[k] for k in original-domain),
       code_bearing_ratio=sum(da[k] for k in domain)/sum(da[k] for k in original),selection=selection_meta,
       S_rows=s_meta,lcov_sha256=sha(lp),forbidden_inputs_used=False,
       command=["python3","tools/profgen_eval/ruling3_union.py",obj],parts=parts)
    assert summary["original_R_C"]==summary["union_R_C"]+summary["code_free_DA"]
    dump(dest/"index.json",summary);print(json.dumps({k:v for k,v in summary.items() if k not in ("parts","S_rows")},ensure_ascii=False))
if __name__=="__main__":main(sys.argv[1])
