"""Apply supplement2 to compiler tokens, retaining every code-DIE identity.
No sample profiles are opened. Scratch spelling is never reassigned to source.
"""
import collections
import json
import re
from pathlib import Path
from audit_macro_inputs import source_relative, unmangle_static
from apply_header_ruling import rows
from macro_function_rule import classify_macro, within
from pack_static_evidence import tables
from run_scoped import WORK, sha

BASE=WORK/"docs/profgen/eval/prep/evidence"
OUT=BASE/"ruling2/supplement2"
SOURCE=WORK/"temp/eval-prep11/ffmpeg"


def write(path, value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n")


def raw_records(path):
    result=[]
    with path.open() as f:
        for line, text in enumerate(f,1):
            r=json.loads(text);r["_raw_line"]=line;result.append(r)
    return result


def region(tokens):
    if not tokens:
        return None
    starts=[t["spelling"] for t in tokens]
    files={x["file"] for x in starts}
    if len(files)!=1 or not next(iter(files)) or any(x["is_scratch"] for x in starts):
        return None
    return dict(file=starts[0]["file"],begin=min(x["offset"] for x in starts),
                end=max(x["offset"] for x in starts))


def function_evidence(audit, records, command):
    decl=source_relative(audit["decl_file"]);line=int(audit["decl_line"])
    fs=[r for r in records if r["record"]=="function" and r["name"]==unmangle_static(audit["name"])
        and r["expansion"]["file"]==decl and r["expansion"]["line"]==line]
    if len(fs)!=1: raise ValueError(("AST definition count",audit["name"],len(fs)))
    f=fs[0];tokens=[r for r in records if r["record"]=="token"]
    begin=[i for i,t in enumerate(tokens) if t["location"]["raw"]==f["body"]["begin"]["raw"]]
    end=[i for i,t in enumerate(tokens) if t["location"]["raw"]==f["body"]["end"]["raw"]]
    if len(begin)!=1 or len(end)!=1 or begin[0]>end[0]:raise ValueError("body token interval ambiguous")
    body=tokens[begin[0]:end[0]+1]
    # Match SourceLocation IDs within this invocation, not macro names or merely
    # file:line (the same template can be included repeatedly at different depths).
    expansion_pairs={(x["immediate_expansion"]["begin"]["raw"], x["immediate_expansion"]["end"]["raw"])
                     for t in body for x in t["trace"]}
    macros=[m for m in records if m["record"]=="macro"
            and m["expansion"]["raw"]==f["expansion"]["raw"]
            and (m["invocation"]["begin"]["raw"],m["invocation"]["end"]["raw"]) in expansion_pairs]
    definitions=[];defranges=[];args=[];invocations=[];raw_definitions=[]
    for m in macros:
        d=m["definition"];file=d["begin"]["file"]
        if file!=d["end"]["file"] or not file:raise ValueError("macro definition without file")
        key=dict(name=m["name"],file=file,line=d["begin"]["line"],end_line=d["end"]["line"])
        if key not in definitions:
            lines=(SOURCE/file).read_text().splitlines()
            first=lines[key["line"]-1]
            if not re.match(r"\s*#\s*define\s+"+re.escape(key["name"])+r"\b",first):
                raise ValueError(("compiler macro definition disagrees with source",key,first))
            definitions.append(key)
            raw_definitions.append(dict(**key,source_sha256=sha(SOURCE/file),
                source_lines=[dict(line=i,text=lines[i-1]) for i in range(key["line"],key["end_line"]+1)]))
        r=region(m["body"])
        if r and r not in defranges:defranges.append(r)
        # Only the outer, source-written invocation can authorize its argument tokens.
        inv=m["invocation"]["begin"]
        if not inv["is_macro"] and inv["file"]==decl and inv["line"]==line:
            invocations.append(dict(name=m["name"],range=m["invocation"],raw_line=m["_raw_line"]))
            for a in m["arguments"]:
                r=region(a)
                if r and r not in args:args.append(r)
    # Empty exact invocation ranges cannot be replaced with a whole source line.
    if not invocations:raise ValueError(("outer invocation not traced",audit["name"]))
    main=source_relative(audit["coverage_main_file"])
    for t in body:
        t["allowed_spelling_regions"] = ([dict(kind="coverage_main",file=main)]
            if t["spelling"]["file"]==main else
            [dict(kind="invocation_argument",**r) for r in args if within(t["spelling"],r)]
            +[dict(kind="macro_definition_body",**r) for r in defranges if within(t["spelling"],r)])
    chain=dict(ast_sha256=sha(Path(audit["ast"])),token_sha256=command["output_sha256"],
               compiler_command=command["command"],definitions=definitions,
               compiler_definitions=definitions.copy(),tokens=body,
               invocation_argument_ranges=args,definition_body_ranges=defranges)
    return dict(function=f,raw_token_file=command["output"],raw_token_sha256=command["output_sha256"],
                raw_ast_file=audit["ast"],raw_ast_sha256=chain["ast_sha256"],
                chain=chain,invocations=invocations,macro_definitions=raw_definitions,
                macro_callbacks=[{k:m[k] for k in ("_raw_line","name","invocation","definition","expansion")}
                                 for m in macros])


def main():
    OUT.mkdir(exist_ok=True)
    summaries=[];by_object={}
    for mode in ("thumb","a32"):
        obj="ffmpeg-"+mode
        audits=json.loads((BASE/"ruling2"/(obj+"-macro-audit.json")).read_text())
        prefix=json.loads((BASE/"ruling2"/(obj+"-prefix-map.json")).read_text())
        cmds=json.loads((BASE/"ruling2"/(mode+"-token-api-commands.json")).read_text())
        commands={r["tu"]:r for r in cmds}
        records={}
        cdefs=list(rows(BASE/(obj+"-C-inventory-tables"),"code-dies-*.csv"))
        results=[]
        for i,a in enumerate(audits):
            cmd=commands[a["cu"]]
            if cmd["exit_code"]!=0 or sha(Path(cmd["output"]))!=cmd["output_sha256"]:raise ValueError("raw compiler evidence invalid")
            if a["cu"] not in records:records[a["cu"]]=raw_records(Path(cmd["output"]))
            evidence=function_evidence(a,records[a["cu"]],cmd)
            pm=prefix[i]
            if pm["full_linkage_name"]!=a["name"]:raise ValueError("prefix row mismatch")
            cs=[c for c in cdefs if c["name"]==a["name"]]
            decl_matches=cs and all(source_relative(c["decl_file"])==source_relative(a["decl_file"]) and
                                   int(c["decl_line"])==int(a["decl_line"]) for c in cs)
            tu_evidence=[]
            for cu in pm["candidate_cus"]:
                for c in pm["commands"]:
                    # All current prefixes are unique. Still retain complete candidate list;
                    # a future multi-CU record must have full-linkage C-ELF provenance.
                    tu_evidence.append(dict(source=cu,compile_log=pm["compile_log"],compile_line=c["line"],
                        linked_elf_code_dies=pm["linked_code_proof"]["C_ELF_DIEs"]
                        if cu in pm["matched_full_linkage_cus"] else [],
                        definition_linkages=[a["name"]] if cu in pm["matched_full_linkage_cus"] else []))
            record=dict(internal=True,pgo_name=a["pgo_name"],s_linkage=a["name"],s_cu_source=a["cu"],
                        tu_compile_evidence=tu_evidence,s_decl_file=source_relative(a["decl_file"]),
                        s_decl_line=int(a["decl_line"]),c_decl_file=source_relative(cs[0]["decl_file"]) if cs else None,
                        c_decl_line=int(cs[0]["decl_line"]) if cs else None,c_definition_verified=bool(decl_matches),
                        code_files=[source_relative(f) for f in a["code_files"]],
                        coverage_main_file=source_relative(a["coverage_main_file"]),
                        macro_invocation_verified=bool(evidence["invocations"]),
                        ordinary_same_name_other_file=a["no_code_in_decl_file"] and a["code_only_in_main"],
                        fnda=a["fnda"],compiler_ast_chain=evidence["chain"])
            verdict=classify_macro(record)
            path=OUT/f"{obj}-{i+1:02d}-tokens.json"
            # Avoid duplicating token arrays; complete raw callback JSONL stays at its SHA-recorded temp path.
            saved_evidence={k:v for k,v in evidence.items() if k!="chain"}
            write(path,dict(identity_record=record,compiler_evidence=saved_evidence,verdict=verdict))
            if path.stat().st_size>=1_000_000:raise ValueError("evidence file exceeds 1 MB")
            body=evidence["chain"]["tokens"];outside=[t for t in body if t["spelling"]["file"]!=record["coverage_main_file"]]
            bad=[dict(raw_line=t["_raw_line"],text=t["text"],spelling=t["spelling"],
                      expansion=t["expansion"],isMacroArgExpansion=t["isMacroArgExpansion"])
                 for t in outside if not t["allowed_spelling_regions"]]
            row=dict(die=a["die"],name=a["name"],cu=a["cu"],decl_file=a["decl_file"],decl_line=a["decl_line"],
                     fnda=a["fnda"],body_tokens=len(body),outside_main_tokens=len(outside),
                     scratch_tokens=sum(t["spelling"]["is_scratch"] for t in body),
                     nonargument_outside_main=sum(not t["isMacroArgExpansion"] for t in outside),
                     invalid_spelling_tokens=bad,**verdict,evidence=str(path.relative_to(WORK)),sha256=sha(path))
            results.append(row)
        write(OUT/(obj+"-results.json"),results);by_object[obj]={r["die"]:r for r in results}
        summaries.append(dict(object=obj,macro_dies=len(results),closed=sum(r["conclusion"]=="macro_generated_function" for r in results),
                             unresolved=sum(r["conclusion"] is None for r in results),
                             reason_counts=dict(collections.Counter(reason for r in results for reason in r["reasons"])),
                             fnda_sum=sum(r["fnda"] for r in results),
                             scratch_tokens=sum(r["scratch_tokens"] for r in results)))
    write(OUT/"macro-summary.json",summaries)
    totals=[]
    for obj in ("spike-thumb","spike-a32","ffmpeg-thumb","ffmpeg-a32"):
        old=BASE/"ruling2"/(obj+"-inventory");new=OUT/(obj+"-inventory");new.mkdir(exist_ok=True)
        data=[];counts=collections.Counter();unresolved=0
        for r in rows(old,"identities-*.csv"):
            result=by_object.get(obj,{}).get(r["die"])
            if result:
                r["conclusion"]=result["conclusion"] or ""
                r["category"]="macro_generated_function" if result["conclusion"] else "macro_token_spelling_outside_allowed_ranges"
                r["evidence"]=result["evidence"]
            unresolved+=not r["conclusion"];counts[r["category"]]+=1
            data.append([r[k] for k in ("die","cu","raw_name","decl_file","decl_line","conclusion","category","evidence")])
        parts=tables(new,"identities",["die","cu","raw_name","decl_file","decl_line","conclusion","category","evidence"],data)
        write(new/"index.json",dict(parts=parts,base_inventory=str(old.relative_to(WORK)/"index.json"),
                                    base_index_sha256=sha(old/"index.json"),note="All prior attributes and candidates retained. No implicit closure."))
        totals.append(dict(object=obj,total=len(data),categories=dict(counts),unresolved=unresolved))
    write(OUT/"closure-summary.json",totals)
    print(json.dumps(dict(macros=summaries,closure=totals),indent=2))


if __name__=="__main__":main()
