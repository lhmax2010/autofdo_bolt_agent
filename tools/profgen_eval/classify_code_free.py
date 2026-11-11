"""Describe excluded lines using compiler ranges; never changes any domain."""
import collections,json,sys
from pathlib import Path
from ruling3_union import OUT,dump,classify_line
from apply_header_ruling import rows
from run_scoped import sha
from pack_static_evidence import tables

def main(obj):
    ast=OUT/(obj+"-AST");idx=json.loads((ast/"index.json").read_text())
    domain=json.loads((OUT/(obj+"-domain")/"index.json").read_text())
    newc={(r["file"],int(r["line"])) for r in rows(OUT/(obj+"-domain"),"lines-*.csv")}
    lines=list(rows(OUT/(obj+"-domain"),"code-free-*.csv"))
    byfile=collections.defaultdict(list);available=set();commands=[]
    for item in idx["commands"]:
        p=ast/item["command"];m=json.loads(p.read_text());commands.append(dict(path=str(p),sha256=sha(p)))
        if m["exit_code"]!=0:continue
        raw=Path(m["output"]);assert sha(raw)==m["output_sha256"]
        records=[json.loads(s) for s in raw.read_text().splitlines()]
        assert records[-1]=={"record":"complete","errors":False},(raw,records[-1])
        for n,r in enumerate(records,1):
            if r["record"] not in ("available_file","range"):continue
            file=m["logical_root"]+r["file"]
            if r["record"]=="available_file":available.add(file);continue
            r.update(file=file,tu=m["tu"],evidence=str(raw),evidence_line=n,evidence_sha256=m["output_sha256"],
                     command=str(p),command_sha256=sha(p))
            byfile[file].append(r)
    result=[];counts=collections.defaultdict(lambda:dict(lines=0,DA=0))
    kinds=collections.defaultdict(lambda:dict(lines=0,DA=0))
    for r in lines:
        f,n,v=r["file"],int(r["line"]),int(r["DA"])
        c=classify_line(f,n,newc,byfile[f],f in available)
        result.append(dict(file=f,line=n,DA=v,**c))
        counts[c["category"]]["lines"]+=1;counts[c["category"]]["DA"]+=v
        w=c["witness"];key=(c["category"],w["kind"] if w else "none")
        kinds[key]["lines"]+=1;kinds[key]["DA"]+=v
    assert sum(v["lines"] for v in counts.values())==domain["code_free_lines"]
    assert sum(v["DA"] for v in counts.values())==domain["code_free_DA"]
    dest=OUT/(obj+"-code-free-classification");dest.mkdir()
    parts=tables(dest,"lines",["file","line","DA","category","witness"],
        ([r[k] for k in ("file","line","DA","category","witness")] for r in sorted(result,key=lambda r:(r["file"],r["line"]))))
    for name in ("asm_interior","stmt_continuation","other","ast_unavailable"):
        counts[name]["fraction_of_original_R_C"]=counts[name]["DA"]/domain["original_R_C"]
    summary=dict(object=obj,original_R_C=domain["original_R_C"],categories=dict(counts),
        by_kind=[dict(category=k[0],kind=k[1],**v) for k,v in sorted(kinds.items())],
        top10={c:sorted([r for r in result if r["category"]==c],key=lambda r:(-r["DA"],r["file"],r["line"]))[:10] for c in counts},
        AST_commands=len(idx["commands"]),failed_commands=sum(c["exit_code"]!=0 for c in idx["commands"]),
        semantics="GCCAsmStmt first; then all multiline Stmt/Expr including CompoundStmt; shortest containing range is deterministic witness; spelling and expansion ranges retained; descriptive only.")
    dump(dest/"summary.json",summary)
    dump(dest/"index.json",dict(parts=parts,summary_sha256=sha(dest/"summary.json"),commands=commands,
        domain_sha256=sha(OUT/(obj+"-domain")/"index.json"),
        command=["python3","tools/profgen_eval/classify_code_free.py",obj]))
    print(json.dumps(dict(object=obj,categories=counts,by_kind=summary["by_kind"]),ensure_ascii=False))
if __name__=="__main__":main(sys.argv[1])
