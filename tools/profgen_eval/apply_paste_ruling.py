"""Run formal ruling2 classifier on all compiler-recorded macro functions.

Static inputs only: compiler tokens/AST, coverage FNDA and saved identity evidence.
Supplement2 output is retained unchanged. Rev1 outputs are separately checksummed.
"""
import collections
import json
from pathlib import Path
from audit_macro_tokens import raw_records, function_evidence
from macro_function_rule import classify_macro
from token_paste_rule import extend_operand_chain
from apply_header_ruling import rows
from pack_static_evidence import tables
from run_scoped import WORK,sha

BASE=WORK/"docs/profgen/eval/prep/evidence"
OLD=BASE/"ruling2/supplement2"
OUT=BASE/"ruling2/supplement3/rev1"

def write(path,value):
    text=json.dumps(value,indent=2,ensure_ascii=False)+"\n"
    if len(text.encode())>=1000000:raise ValueError(("evidence too large",path))
    path.write_text(text)

def paths(proof):
    counts=collections.Counter()
    for o in proof.get("operands",[]):
        if "proof_path" in o:counts[o["proof_path"]]+=1
        if "subproof" in o:counts.update(paths(o["subproof"]))
    return counts

def main():
    summaries=[];byobject={}
    for mode in ("thumb","a32"):
        obj="ffmpeg-"+mode
        cmds={x["tu"]:x for x in json.loads((OUT/(mode+"-token-api-commands.json")).read_text())}
        audits=json.loads((BASE/"ruling2"/(obj+"-macro-audit.json")).read_text())
        cache={};results=[]
        for i,a in enumerate(audits):
            cmd=cmds[a["cu"]]
            if a["cu"] not in cache:
                assert cmd["exit_code"]==0 and sha(Path(cmd["output"]))==cmd["output_sha256"]
                cache[a["cu"]]=raw_records(Path(cmd["output"]))
            raw=cache[a["cu"]];macros=[x for x in raw if x["record"]=="macro"]
            oldpath=OLD/f"{obj}-{i+1:02d}-tokens.json"
            record=json.loads(oldpath.read_text())["identity_record"]
            f=function_evidence(a,raw,cmd)
            f["coverage_main_file"]=record["coverage_main_file"]
            extend_operand_chain(f,macros)
            context={k:f[k] for k in ("macro_callbacks","invocations","coverage_main_file")}
            context["chain"]={k:f["chain"][k] for k in ("invocation_argument_ranges","definition_body_ranges")}
            context["macros"]=macros
            f["chain"]["paste_context"]=context
            record["compiler_ast_chain"]=f["chain"]
            verdict=classify_macro(record)
            proofs=f["chain"].get("paste_proofs",[])
            for proof in proofs:
                assert proof["status"] in ("proved","unresolved")
            # Contexts reference raw compiler records; do not duplicate a whole TU
            # in every saved proof. Actual classify invocation above used them all.
            del f["chain"]["paste_context"]
            f["chain"].pop("paste_proofs",None)
            path=OUT/f"{obj}-{i+1:02d}-proof.json"
            write(path,dict(die=a["die"],name=a["name"],fnda=a["fnda"],verdict=verdict,
                proofs=proofs,identity_record=record,raw_path=cmd["output"],raw_sha256=cmd["output_sha256"],
                base_identity_path=str(oldpath.relative_to(WORK)),base_identity_sha256=sha(oldpath),
                macro_callbacks=f["macro_callbacks"],invocations=f["invocations"],
                macro_definitions=f["macro_definitions"],operand_dependency_macros=f["operand_dependency_macros"]))
            pc=collections.Counter()
            for proof in proofs:pc.update(paths(proof))
            results.append(dict(die=a["die"],name=a["name"],fnda=a["fnda"],**verdict,
                proof_paths=dict(pc),scratch_tokens=len(proofs),evidence=str(path.relative_to(WORK)),sha256=sha(path)))
        byobject[obj]={r["die"]:r for r in results}
        write(OUT/(obj+"-results.json"),results)
        pending=[r for r in results if r["scratch_tokens"]]
        pc=collections.Counter()
        for r in pending:pc.update(r["proof_paths"])
        summaries.append(dict(object=obj,all_macro_records=len(results),supplement3_records=len(pending),
            closed=sum(r["conclusion"]=="macro_generated_function" for r in pending),
            unresolved=sum(r["conclusion"] is None for r in pending),
            reasons=dict(collections.Counter(c for r in pending for c in r["reasons"])),
            scope_roles=dict(collections.Counter(r.get("scope_role","unresolved") for r in pending)),
            proof_paths=dict(pc),fnda_nonzero=[r for r in pending if r["fnda"]>0]))
    write(OUT/"macro-summary.json",summaries)
    closure=[]
    for obj in ("spike-thumb","spike-a32","ffmpeg-thumb","ffmpeg-a32"):
        old=OLD/(obj+"-inventory");out=OUT/(obj+"-inventory");out.mkdir(exist_ok=True)
        data=[];counts=collections.Counter();unresolved=0
        for row in rows(old,"identities-*.csv"):
            r=byobject.get(obj,{}).get(row["die"])
            if r:
                row["conclusion"]=r["conclusion"] or ""
                row["category"]="macro_generated_function" if r["conclusion"] else ";".join(r["reasons"])
                row["evidence"]=r["evidence"]
            counts[row["category"]]+=1;unresolved+=not row["conclusion"]
            data.append([row[k] for k in ("die","cu","raw_name","decl_file","decl_line","conclusion","category","evidence")])
        parts=tables(out,"identities",["die","cu","raw_name","decl_file","decl_line","conclusion","category","evidence"],data)
        write(out/"index.json",dict(parts=parts,base=str(old.relative_to(WORK)/"index.json"),base_sha256=sha(old/"index.json")))
        closure.append(dict(object=obj,total=len(data),categories=dict(counts),unresolved=unresolved))
    write(OUT/"closure-summary.json",closure)
    print(json.dumps(dict(macros=summaries,closure=closure),indent=2))
    if any(r["unresolved"] for r in summaries):return 1
    assert all(r["supplement3_records"]==28 and r["closed"]==28 for r in summaries)
    return 0

if __name__=="__main__":raise SystemExit(main())
