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

def loc_in_definition(loc, macro):
    d=macro["definition"]
    return within(loc,dict(file=d["begin"]["file"],begin=d["begin"]["offset"],end=d["end"]["offset"]))

def extend_operand_chain(evidence, macros):
    """Include actual MacroArgs operand dependencies, using API raw ranges only.

    A paste erases its operands from the final token trace. The copied MacroArgs
    tokens retain their own chains; BIT_DEPTH must be recorded from those APIs.
    No same-name/file inference or arbitrary same-invocation callback inclusion.
    """
    seen=set();existing={(m["name"],m["invocation"]["begin"]["raw"]) for m in evidence["macro_callbacks"]}
    additions=[]
    def add_macro(m, via):
        key=(m["name"],m["invocation"]["begin"]["raw"])
        if key in existing:return
        existing.add(key)
        evidence["macro_callbacks"].append({k:m[k] for k in ("name","invocation","definition","expansion","_raw_line")})
        body=m["body"]
        if body and len({t["spelling"]["file"] for t in body})==1 and body[0]["spelling"]["file"]:
            region=dict(file=body[0]["spelling"]["file"],begin=body[0]["spelling"]["offset"],
                        end=body[-1]["spelling"]["offset"])
            evidence["chain"]["definition_body_ranges"].append(region)
        additions.append(dict(via_token=via,macro={k:m[k] for k in ("name","name_location","definition","invocation","_raw_line")}))
    def visit(t):
        raw=t["location"]["raw"]
        if raw in seen:return
        seen.add(raw)
        pairs={(q["immediate_expansion"]["begin"]["raw"],q["immediate_expansion"]["end"]["raw"]) for q in t["trace"]}
        for m in macros:
            if (m["invocation"]["begin"]["raw"],m["invocation"]["end"]["raw"]) in pairs:
                add_macro(m,raw)
        for l in t["trace"]:
            if not(l["immediate_spelling"]["is_scratch"] and not l["immediate_spelling"]["is_macro"]):continue
            o=l["begin_owner"]
            if "instance_range" not in o:continue
            hits=[m for m in macros if m["name"]==o["macro"] and m["name_location"]["raw"]==o["instance_range"]["begin"]["raw"]]
            if len(hits)!=1:continue
            x=hits[0];b,e=l["immediate_expansion"]["begin"],l["immediate_expansion"]["end"]
            add_macro(x,raw)
            for d in x["body"]:
                n=d["parameter_num"]
                if b["file"]==d["spelling"]["file"] and b["offset"]<=d["spelling"]["offset"]<=e["offset"] and n>=0 and n<len(x["arguments"]):
                    for a in x["arguments"][n]:visit(a)
    for t in evidence["chain"]["tokens"]:visit(t)
    evidence["operand_dependency_macros"]=additions


def inspect(token,chain,macros,depth=0):
    result=dict(token=token,depth=depth,status="unresolved",reason_codes=[],steps_passed=[],operands=[])
    def fail(code):
        result["reason_codes"].append(code);return result
    if depth>8:return fail("paste_recursion_depth_exceeded")
    layers=[x for x in token.get("trace",[]) if x.get("immediate_spelling",{}).get("is_scratch") is True
            and x["immediate_spelling"].get("is_macro") is False]
    if len(layers)!=1:return fail("paste_layer_not_unique")
    layer=layers[0];result["L"]=layer;result["steps_passed"].append(1)
    b,e=layer["immediate_expansion"]["begin"],layer["immediate_expansion"]["end"]
    result["B"]=b;result["E"]=e
    if not b.get("is_macro") or not e.get("is_macro"):return fail("paste_endpoint_not_macro")
    bo,eo=layer["begin_owner"],layer["end_owner"]
    if bo!=eo or b["file_id"]!=e["file_id"]:return fail("paste_endpoint_instances_differ")
    hits=[m for m in macros if m["name"]==bo["macro"] and
          m["name_location"]["raw"]==bo["instance_range"]["begin"]["raw"]]
    if len(hits)!=1:return fail("paste_callback_instance_not_unique")
    x=hits[0];result["X"]={k:x[k] for k in ("name","name_location","invocation","definition","msvc_compat","_raw_line")}
    result["steps_passed"].append(2)
    if not loc_in_definition(b,x) or not loc_in_definition(e,x):return fail("paste_endpoint_outside_definition")
    identities={(m["name"],m["invocation"]["begin"]["raw"]) for m in chain["macro_callbacks"]}
    if (x["name"],x["invocation"]["begin"]["raw"]) not in identities:return fail("paste_instance_not_in_function_chain")
    result["steps_passed"].append(3)
    fragment=[t for t in x["body"] if t["location"]["file"]==b["file"] and
              b["offset"]<=t["location"]["offset"]<=e["offset"]]
    result["definition_tokens"]=fragment
    if x.get("msvc_compat") is not False:return fail("paste_msvc_compat_or_missing")
    if any(t["kind"]=="hash" for t in fragment):return fail("paste_stringification")
    if any(t["kind"]=="comma" for t in fragment):return fail("paste_comma_extension")
    if len(fragment)<3 or len(fragment)%2!=1:return fail("paste_definition_structure")
    if fragment[0]["location"]["offset"]!=b["offset"] or fragment[-1]["location"]["offset"]!=e["offset"]:
        return fail("paste_definition_endpoints_not_tokens")
    if any((t["kind"]=="hashhash")!=(i%2==1) for i,t in enumerate(fragment)):
        return fail("paste_definition_structure")
    result["steps_passed"].append(4)
    resolved=[]
    for t in fragment[::2]:
        if "parameter_num" not in t:return fail("paste_parameter_index_missing")
        n=t["parameter_num"]
        if n>=0:
            if n>=len(x["arguments"]):return fail("paste_macroargs_slot_missing")
            arg=x["arguments"][n]
            if not arg:return fail("paste_empty_argument")
            if len(arg)!=1:return fail("paste_multitoken_argument")
            resolved.append(dict(kind="argument",parameter_num=n,definition_token=t,token=arg[0]))
        else:resolved.append(dict(kind="definition",parameter_num=n,definition_token=t,token=t))
    result["steps_passed"].append(5);result["operands"]=resolved
    combined="".join(o["token"]["text"] for o in resolved)
    result["concatenation"]=dict(result=combined,expected=token["text"],equal_utf8=combined.encode()==token["text"].encode())
    if combined!=token["text"]:return fail("paste_text_mismatch")
    lex=[f for f in x["paste_fragments"] if f["begin"]["offset"]==b["offset"] and f["end"]["offset"]==e["offset"]]
    if len(lex)!=1:return fail("paste_intermediate_lex_evidence_missing")
    result["intermediate_lexing"]=lex[0]
    prefixes=lex[0]["prefix_lexing"]
    if len(prefixes)!=len(resolved) or token["kind"] not in ("identifier","numeric_constant"):
        return fail("paste_intermediate_kind")
    text=""
    for o,p in zip(resolved,prefixes):
        text+=o["token"]["text"]
        if p["text"]!=text or not p["whole_token"] or p["kind"] not in ("identifier","numeric_constant"):
            return fail("paste_intermediate_kind")
    result["steps_passed"].append(6)
    for o in resolved:
        t=o["token"]
        if o["kind"]=="definition":
            o["source_valid"]=loc_in_definition(t["spelling"],x)
            if not o["source_valid"]:result["reason_codes"].append("paste_literal_outside_definition")
            continue
        if t["spelling"]["is_scratch"]:
            sub=inspect(t,chain,macros,depth+1);o["subproof"]=sub
            o["source_valid"]=sub["status"]=="proved"
            result["reason_codes"]+=sub["reason_codes"]
            continue
        sp=t["spelling"];arg=t.get("isMacroArgExpansion")
        allowed=(chain["chain"]["invocation_argument_ranges"]+chain["chain"]["definition_body_ranges"])
        o["in_allowed_argument_or_definition_range"]=any(within(sp,r) for r in allowed)
        if type(arg) is not bool:
            o["source_valid"]=False;result["reason_codes"].append("paste_argument_flag_missing")
        elif sp["file"]==chain["coverage_main_file"]:
            o["source_valid"]=True
        elif not arg:
            o["source_valid"]=False;result["reason_codes"].append("paste_argument_nonmacro_outside_main")
        elif not o["in_allowed_argument_or_definition_range"]:
            o["source_valid"]=False;result["reason_codes"].append("paste_argument_source_outside_chain")
        else:o["source_valid"]=True
    if result["reason_codes"]:return result
    result["steps_passed"].append(7);result["status"]="proved";return result

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
