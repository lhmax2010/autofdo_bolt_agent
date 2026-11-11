"""Descriptive code_free v2, operating only on sealed static-domain evidence."""
import collections,json,sys
from pathlib import Path
from code_free_v2_rules import classify,CATEGORIES
from code_free_v2_lex import OUT,TEMP,OLD
from ruling3_union import dump
from apply_header_ruling import rows
from pack_static_evidence import tables
from run_scoped import sha
def main(obj):
    meta=json.loads((OUT/"lexer-command.json").read_text())
    assert meta["exit_code"]==0 and sha(Path(meta["output"]))==meta["output_sha256"]
    tokens={(r["file"],r["line"]):r["tokens"] for r in map(json.loads,Path(meta["output"]).read_text().splitlines())}
    index=json.loads((OUT/(obj+"-AST/index.json")).read_text());assert index["all_equal"]
    nodes=collections.defaultdict(list);labels=collections.defaultdict(list);available=set();provenance=[]
    for it in index["commands"]:
        p=OUT/(obj+"-AST")/it["command"];m=json.loads(p.read_text())
        assert m["exit_code"]==m["previous_exit_code"]==0 and not any(m["differences"].values())
        raw=Path(m["output"]);assert sha(raw)==m["output_sha256"]
        provenance.append(dict(path=str(p),sha256=sha(p)))
        for n,line in enumerate(raw.open(),1):
            r=json.loads(line);kind=r["record"]
            if kind not in ("available_file","range","decl_range","label"):continue
            f=m["logical_root"]+r["file"]
            if kind=="available_file":available.add(f);continue
            r.update(file=f,tu=m["tu"],raw=str(raw),raw_line=n,raw_sha256=m["output_sha256"],command=str(p))
            if kind=="label":labels[f].append(r)
            else:nodes[f].append(r)
    domain=OLD/(obj+"-domain");d=json.loads((domain/"index.json").read_text())
    newc=collections.defaultdict(set)
    for r in rows(domain,"lines-*.csv"):newc[r["file"]].add(int(r["line"]))
    prior={(r["file"],int(r["line"])):r["category"] for r in rows(OLD/(obj+"-code-free-classification"),"lines-*.csv")}
    lines=list(rows(domain,"code-free-*.csv"));assert len(lines)==len(prior)
    result=[];counts={c:dict(lines=0,DA=0) for c in CATEGORIES}
    cross=collections.defaultdict(lambda:dict(lines=0,DA=0));sub=collections.defaultdict(lambda:dict(lines=0,DA=0))
    own=collections.defaultdict(lambda:dict(lines=0,DA=0));seen=set()
    for row in lines:
        f,n,v=row["file"],int(row["line"]),int(row["DA"]);assert (f,n) not in seen;seen.add((f,n))
        ts=tokens.get((f,n));ns=[r for r in nodes[f] if r["begin_line"]<=n<=r["end_line"]]
        ls=[r for r in labels[f] if r["begin_line"]<=n<=r["end_line"]]
        r=classify(n,newc[f],ns,ts,ls,f in available)
        if r["category"]=="structural_line":
            # Context is shown for review, not used to infer token membership.
            r["AST_context_only"]=min(ns,key=lambda x:(x["end_offset"]-x["begin_offset"],x["kind"])) if ns else None
            r["label_evidence"]=ls
            sub[r["reason"]]["lines"]+=1;sub[r["reason"]]["DA"]+=v
        if r["category"]=="own_stmt_no_code":
            own[r["statement_kind"]]["lines"]+=1;own[r["statement_kind"]]["DA"]+=v
        r.update(file=f,line=n,DA=v,tokens=ts,old_category=prior[(f,n)])
        result.append(r)
        counts[r["category"]]["lines"]+=1;counts[r["category"]]["DA"]+=v
        cross[(r["old_category"],r["category"])]["lines"]+=1;cross[(r["old_category"],r["category"])]["DA"]+=v
    assert sum(v["DA"] for v in counts.values())==d["original_R_C"]-d["union_R_C"]
    assert sum(v["lines"] for v in counts.values())==len(lines)==len(seen)
    for v in counts.values():
        v.update(original_denominator=d["original_R_C"],new_denominator=d["union_R_C"],
                 ratio_original=v["DA"]/d["original_R_C"],ratio_new=v["DA"]/d["union_R_C"])
    dest=OUT/(obj+"-classification");dest.mkdir()
    header=["file","line","DA","category","reason","old_category","tokens","witness","statement_kind","start_kinds","AST_context_only","label_evidence"]
    parts=tables(dest,"lines",header,([r.get(k) for k in header] for r in sorted(result,key=lambda r:(r["file"],r["line"]))))
    parts+=tables(dest,"other",header,([r.get(k) for k in header] for r in result if r["category"] in ("other","ast_unavailable")))
    top={c:sorted((r for r in result if r["category"]==c),key=lambda r:(-r["DA"],r["file"],r["line"]))[:20] for c in CATEGORIES}
    # Long asm tokens remain in <1MB CSV shards as well as the compact summaries.
    top_parts=tables(dest,"top20",header,([r.get(k) for k in header] for c in CATEGORIES for r in top[c]))
    summary=dict(object=obj,categories=counts,structural_subtypes=dict(sorted(sub.items())),own_statement_kinds=dict(sorted(own.items())),
        cross=[dict(old=k[0],new=k[1],**v) for k,v in sorted(cross.items())],
        assertion=dict(lines=len(seen),DA=sum(r["DA"] for r in result),expected=d["original_R_C"]-d["union_R_C"],difference=0,exactly_one=True),
        top20_parts=top_parts,expr_witness_kinds=dict(collections.Counter(r["witness"]["kind"] for r in result if r["category"]=="expr_continuation")))
    dump(dest/"summary.json",summary)
    dump(dest/"index.json",dict(command=["python3","tools/profgen_eval/classify_code_free_v2.py",obj],
        parts=parts+top_parts,summary_sha256=sha(dest/"summary.json"),AST_commands=provenance,
        old_domain_index=str(domain/"index.json"),old_domain_sha256=sha(domain/"index.json"),
        lexer_metadata_sha256=sha(OUT/"lexer-command.json")))
    print(json.dumps(summary,ensure_ascii=False))
if __name__=="__main__":main(sys.argv[1])
