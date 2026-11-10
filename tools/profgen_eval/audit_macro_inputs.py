"""Static-only PGO/TU, declaration, coverage-region and compiler AST audit."""
import collections,json,posixpath,re
from pathlib import Path
from apply_header_ruling import rows,norm_file
from dwarf_inventory import text
from recheck_header_evidence import command_record
from coverage_reference import main_file_id
from run_scoped import sha

BASE=Path("docs/profgen/eval/prep/evidence")
OUT=BASE/"ruling2"

def function_stream(path):
    # LLVM exporter uses a top-level functions array; summaries use objects.
    marker='"functions":[';buf="";decoder=json.JSONDecoder()
    with path.open() as f:
        while marker not in buf:
            block=f.read(1048576)
            if not block:raise ValueError("no functions array")
            buf=buf[-len(marker):]+block
        buf=buf.split(marker,1)[1]
        while True:
            buf=buf.lstrip()
            if buf.startswith("]"):return
            if buf.startswith(","):buf=buf[1:].lstrip()
            try:
                item,end=decoder.raw_decode(buf)
            except json.JSONDecodeError:
                more=f.read(1048576)
                if not more:raise
                buf+=more;continue
            yield item
            buf=buf[end:]

def ast_functions(path):
    buf=path.read_text();i=0;decoder=json.JSONDecoder();state={}
    def expand(node):
        if isinstance(node,dict):
            if "offset" in node and "col" in node:
                for key in ("file","line"):
                    if key in node:state[key]=node[key]
                    elif key in state:node[key]=state[key]
            for value in list(node.values()):expand(value)
        elif isinstance(node,list):
            for value in node:expand(value)
    while buf[i:].strip():
        i+=len(buf[i:])-len(buf[i:].lstrip());node,end=decoder.raw_decode(buf,i);i=end
        expand(node);yield node

def source_relative(path):
    p=posixpath.normpath(path)
    if "/ffmpeg-8.0.1/" in p:p=p.split("/ffmpeg-8.0.1/",1)[1]
    return p

def unmangle_static(name):
    m=re.match(r"_ZL(\d+)",name)
    return name[m.end():m.end()+int(m[1])] if m else name

def main():
    summary={}
    for mode in ("thumb","a32"):
        obj="ffmpeg-"+mode
        pending=json.loads((BASE/"ruling1"/(obj+"-conclusions")/"blocking-no-candidate.json").read_text())
        pending=[r for r in pending if r["category"]=="same_name_different_definition_file"]
        names={r["raw_name"] for r in pending}
        covpath=Path(json.loads((BASE/(obj+"-coverage-tables")/"index.json").read_text())["json"])
        cov=[]
        for i,f in enumerate(function_stream(covpath)):
            if f["name"].split(":",1)[-1] in names:cov.append((i,f))
        command=command_record(BASE/"ruling1"/(obj+"-C-commands.json"))
        cc=list(rows(BASE/(obj+"-C-inventory-tables"),"code-dies-*.csv"))
        cu={r["offset"]:text(json.loads(r["attrs"]).get("name")) for r in rows(BASE/(obj+"-C-inventory-tables"),"compile_units-*.csv")}
        astcommands=json.loads((OUT/(mode+"-ast4-commands.json")).read_text())
        asts={r["tu"]:list(ast_functions(Path(r["ast"]))) for r in astcommands}
        result=[];prefixmap=[]
        for r in pending:
            references=[(i,f) for i,f in cov if f["name"].split(":",1)[-1]==r["raw_name"]]
            if len(references)!=1:raise ValueError((r["raw_name"],len(references)))
            i,ref=references[0];prefix=ref["name"].split(":",1)[0]
            commands=[c for c in command["compile_commands"] if any(Path(s).name==prefix for s in c["sources"])]
            cus=sorted({s for c in commands for s in c["sources"]})
            definitions=[c for c in cc if c["name"]==r["raw_name"]]
            matched_cus=sorted({source_relative(cu[c["cu"]]) for c in definitions}&set(cus))
            chosen=cus[0] if len(cus)==1 else matched_cus[0] if len(matched_cus)==1 else None
            selected=[c for c in definitions if source_relative(cu[c["cu"]])==chosen]
            same_decl=bool(selected) and all(norm_file(c["decl_file"])==r["decl_file"] and c["decl_line"]==r["decl_line"] for c in selected)
            maprow={"prefix":prefix,"candidate_cus":cus,"matched_full_linkage_cus":matched_cus,"resolved_cu":chosen,
                    "full_linkage_name":r["raw_name"],"s_cu":r["cu_name"],"matches_s_cu":chosen==source_relative(r["cu_name"]),
                    "compile_log":command["log"],"commands":[{"line":c["line"],"command":c["text"]} for c in commands],
                    "linked_code_proof":{"S_ELF_DIE":r["die"],"C_ELF_DIEs":[{"die":c["die"],"tag":c["tag"]} for c in selected],"C_CUs":[cu[c["cu"]] for c in selected]},
                    "declaration_identity_equal":same_decl}
            prefixmap.append(maprow)
            main=norm_file(ref["filenames"][main_file_id(ref)])
            codefiles=sorted({norm_file(ref["filenames"][rg[5]]) for rg in ref["regions"] if rg[7]==0})
            ast=[a for a in asts[chosen] if a.get("name")==unmangle_static(r["raw_name"]) and any(n.get("kind")=="CompoundStmt" for n in a.get("inner",[]))]
            if len(ast)!=1:raise ValueError((r["raw_name"],len(ast)))
            body=next(n for n in ast[0]["inner"] if n["kind"]=="CompoundStmt")
            statements=[]
            for n in body.get("inner",[]):
                locations=[]
                for end,loc in n.get("range",{}).items():
                    spell=loc.get("spellingLoc",loc);exp=loc.get("expansionLoc",loc)
                    locations.append(dict(end=end,spelling=spell,expansion=exp))
                statements.append({"kind":n["kind"],"locations":locations})
            bad=[p for n in statements for p in n["locations"] if source_relative(p["spelling"].get("file",""))!=source_relative(main)]
            row=dict(die=r["die"],name=r["raw_name"],cu=r["cu_name"],decl_file=r["decl_file"],decl_line=r["decl_line"],
                     coverage_record=i,pgo_name=ref["name"],fnda=ref["count"],code_files=codefiles,coverage_main_file=main,
                     tu_prefix_proven=maprow["matches_s_cu"],declaration_identity_equal=same_decl,
                     no_code_in_decl_file=r["decl_file"] not in codefiles,code_only_in_main=codefiles==[main],
                     ast=next(a["ast"] for a in astcommands if a["tu"]==chosen),ast_body_statements=statements,
                     non_main_statement_endpoints=bad,conclusion=None,
                     reason="macro_argument_spelling_scope_requires_ruling" if bad else "complete_chain_not_yet_verified")
            result.append(row)
            if len(result)==1:
                (OUT/(mode+"-example-ast-expanded.json")).write_text(json.dumps(ast[0],indent=2)+"\n")
                (OUT/(mode+"-example-coverage.json")).write_text(json.dumps(ref,indent=2)+"\n")
        (OUT/(obj+"-prefix-map.json")).write_text(json.dumps(prefixmap,indent=2)+"\n")
        (OUT/(obj+"-macro-audit.json")).write_text(json.dumps(result,indent=2)+"\n")
        summary[obj]={"total":len(result),"tu_prefix_proven":sum(r["tu_prefix_proven"] for r in result),
                      "decl_equal":sum(r["declaration_identity_equal"] for r in result),"no_code_in_decl":sum(r["no_code_in_decl_file"] for r in result),
                      "body_endpoints_outside_main":sum(bool(r["non_main_statement_endpoints"]) for r in result),
                      "closed":0,"fnda_sum":sum(r["fnda"] for r in result),"coverage_sha256":sha(covpath)}
    (OUT/"macro-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
