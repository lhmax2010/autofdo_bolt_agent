"""Allowlisted static inputs; never consumes RUN profiles."""
import collections,json,bisect
from pathlib import Path
from apply_header_ruling import rows,norm_file,norm_name
from coverage_reference import parse_lcov
from pack_static_evidence import tables
from run_scoped import WORK,sha
BASE=WORK/"docs/profgen/eval/prep/evidence"
OLD=BASE/"ruling2/supplement3/rev1/identity-gate/ordinary-v2"
OUT=BASE/"identity-gate"
TEMP=WORK/"temp/prep-static-gate"
OBJECTS=("spike-thumb","spike-a32","ffmpeg-thumb","ffmpeg-a32")

def dump(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")

def data(obj):
    cov=BASE/(obj+"-coverage-tables")
    meta=json.loads((cov/"index.json").read_text())
    lp=Path(meta["lcov"])
    if not lp.is_absolute(): lp=WORK/lp
    if not lp.exists():lp=WORK/"temp/prep-identity-gate"/(obj+"-reference.lcov")
    ref=list(rows(cov,"merged-functions-*.csv"))
    for i,r in enumerate(ref):
        r.update(id=i,file=norm_file(r["file"]),start=int(r["start"]),end=int(r["end"]),
                 fnda=int(r["fnda"]),copies=json.loads(r["copies"]),code_regions=json.loads(r["code_regions"]))
    da={(norm_file(f),int(n)):v for f,x in parse_lcov(lp).items() for n,v in x["da"].items()}
    perfile=collections.defaultdict(list)
    for f,n in da:perfile[f].append(n)
    for ns in perfile.values():ns.sort()
    rlines={}
    for i,r in enumerate(ref):
        ns=perfile[r["file"]]
        rlines[i]={(r["file"],n) for n in ns[bisect.bisect_left(ns,r["start"]):bisect.bisect_right(ns,r["end"])]}
    inventory={int(r["die"],16):r for r in rows(OLD/(obj+"-inventory"),"inventory-*.csv")}
    if not inventory:
        inventory={int(r["die"],16):r for r in rows(OLD/(obj+"-inventory"),"*.csv")}
    ordinary={}
    for r in rows(OLD/(obj+"-ordinary"),"checks-*.csv"):
        r["candidate_ids"]=json.loads(r["candidate_ids"])
        r["reasons"]=json.loads(r["reasons"])
        ordinary[int(r["die"],16)]=r
    macros={d for d,r in inventory.items() if r["category"]=="macro_generated_function"}
    if macros:
        proof_index=BASE/"ruling2/supplement3/rev1"/(obj+"-results.json")
        records=json.loads(proof_index.read_text())
        assert {int(r["die"],16) for r in records}==macros
        for r in records:
            assert r["conclusion"]=="macro_generated_function" and r["scope_role"]=="reference_unexecuted"
            assert r["fnda"]==0,("positive macro FNDA requires explicit group integration",r)
            assert sha(WORK/r["evidence"])==r["sha256"]
    return ref,da,rlines,inventory,ordinary,lp

def bridge_inventory(obj):
    out={}
    with (TEMP/(obj+"-inventory.jsonl")).open() as f:
        for line in f:
            r=json.loads(line)
            if r["kind"]=="die":out[r["die"]]=r
    return out

def select(obj):
    ref,da,rlines,inv,checks,lp=data(obj)
    b=bridge_inventory(obj)
    assert set(b)==set(inv),(len(b),len(inv),set(b)^set(inv))
    groups=collections.defaultdict(list)
    for die,r in b.items():
        i=inv[die]
        assert r["name"]==i["raw_name"] and norm_file(r["decl_file"])==norm_file(i["decl_file"])
        assert r["decl_line"]==int(i["decl_line"] or 0)
        assert r["top_die"] in b
        groups[b[r["top_die"]]["name"]].append(die)
    chosen=[]
    gr=[]
    for name,ds in sorted(groups.items()):
        rr=set()
        for d in ds:
            rr.update(checks.get(d,{}).get("candidate_ids",[]))
        # Existing macro rulings all have FNDA=0. Never infer a new positive mapping.
        macro=[d for d in ds if inv[d]["category"]=="macro_generated_function"]
        for d in macro:assert inv[d]["conclusion"]=="macro_generated_function"
        # Macro FNDA=0 is checked in the committed ruling2 closure evidence, not inferred from the enum.
        executed={r for r in rr if ref[r]["fnda"]>0}
        role="mapping_range" if executed else "known_out_of_scope"
        if executed:chosen.append(name)
        gr.append([name,role,ds,sorted(rr),sorted(executed)])
    dump(TEMP/(obj+"-selected-groups.json"),chosen)
    dest=OUT/(obj+"-groups");dest.mkdir(exist_ok=True)
    parts=tables(dest,"groups",["name","role","dies","reference_ids","executed_reference_ids"],gr)
    meta=dict(object=obj,parts=parts,complete_code_DIEs=len(b),unresolved=0,
        selected_groups=len(chosen),all_groups=len(groups),selection_sha256=sha(TEMP/(obj+"-selected-groups.json")),
        input_inventory_sha256=sha(TEMP/(obj+"-inventory.jsonl")),lcov_sha256=sha(lp))
    dump(dest/"index.json",meta);print(json.dumps(meta),flush=True)

if __name__=="__main__":
    import sys
    select(sys.argv[1])
