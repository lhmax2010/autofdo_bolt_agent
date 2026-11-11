"""Read-only supplement3 proof inspection. Does not close identity records.
Stops the stage at real positive-example contradictions; never reads profiles.
"""
import json,collections
from pathlib import Path
from audit_macro_tokens import raw_records,function_evidence
from macro_function_rule import within
from run_scoped import WORK,sha

BASE=WORK/"docs/profgen/eval/prep/evidence/ruling2"
OUT=BASE/"supplement3"

from token_paste_rule import extend_operand_chain, prove as inspect

def write(p,v):
    p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+"\n")

def main():
    summary=[]
    for mode in ("thumb","a32"):
        commands={r["tu"]:r for r in json.loads((OUT/f"{mode}-token-api-commands.json").read_text())}
        audits=json.loads((BASE/f"ffmpeg-{mode}-macro-audit.json").read_text())
        prior=json.loads((BASE/f"supplement2/ffmpeg-{mode}-results.json").read_text())
        pending={r["die"] for r in prior if r["conclusion"] is None and
                 r["reasons"]==["argument_spelling_outside_allowed_ranges"]}
        if len(pending)!=28:raise ValueError("supplement2 input selection changed")
        cache={};resultrows=[]
        for i,a in enumerate(audits):
            if a["die"] not in pending:continue
            cmd=commands[a["cu"]]
            if a["cu"] not in cache:
                if cmd["exit_code"] or sha(Path(cmd["output"]))!=cmd["output_sha256"]:raise ValueError("raw evidence invalid")
                cache[a["cu"]]=raw_records(Path(cmd["output"]))
            raw=cache[a["cu"]]
            f=function_evidence(a,raw,cmd)
            f["coverage_main_file"]=a["coverage_main_file"].split("ffmpeg-8.0.1/")[-1]
            extend_operand_chain(f,[x for x in raw if x["record"]=="macro"])
            proofs=[inspect(t,f,[x for x in raw if x["record"]=="macro"]) for t in f["chain"]["tokens"] if t["spelling"]["is_scratch"]]
            path=OUT/f"ffmpeg-{mode}-{i+1:02d}-paste-proof.json"
            write(path,dict(die=a["die"],name=a["name"],cu=a["cu"],fnda=a["fnda"],proofs=proofs,
                            raw_token_file=cmd["output"],raw_token_sha256=cmd["output_sha256"],
                            original_ast_path=a["ast"],original_ast_sha256=sha(Path(a["ast"])),
                            function_ast=f["function"],compiler_command=cmd["command"],
                            invocation_argument_ranges=f["chain"]["invocation_argument_ranges"],
                            macro_definitions=f["macro_definitions"],operand_dependency_macros=f["operand_dependency_macros"],
                            definition_body_ranges=f["chain"]["definition_body_ranges"],
                            scope="read-only inspection; no identity closure"))
            if path.stat().st_size>=1_000_000:raise ValueError(("oversize",path))
            reasons=sorted({c for pr in proofs for c in pr["reason_codes"]})
            row=dict(die=a["die"],name=a["name"],fnda=a["fnda"],scratch_tokens=len(proofs),
                     proved_tokens=sum(p["status"]=="proved" for p in proofs),reason_codes=reasons,
                     path=str(path.relative_to(WORK)),sha256=sha(path))
            resultrows.append(row)
        write(OUT/f"ffmpeg-{mode}-paste-inspection.json",resultrows)
        summary.append(dict(object="ffmpeg-"+mode,records=len(resultrows),
                            all_paste_sources_proved=sum(not r["reason_codes"] for r in resultrows),
                            unresolved=sum(bool(r["reason_codes"]) for r in resultrows),
                            reasons=dict(collections.Counter(c for r in resultrows for c in r["reason_codes"])),
                            fnda_nonzero=[r for r in resultrows if r["fnda"]]))
    write(OUT/"paste-inspection-summary.json",summary);print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
