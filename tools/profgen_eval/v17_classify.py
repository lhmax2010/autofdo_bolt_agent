"""v1.7 code_free description. Reuse verified C AST/raw lex; add all-DIE calls."""
import collections,json,sys
from pathlib import Path
from v17_domain import OUT,TEMP,BASE,dump
from run_scoped import sha
from apply_header_ruling import rows,norm_file
from pack_static_evidence import tables
from v17_rules import classify_code_free
OLD=BASE/"identity-gate/code-free-v2"
CATEGORIES=("asm_interior","structural_line","expr_continuation","inlined_call_site",
            "own_stmt_no_code","other","ast_unavailable")

def main(obj):
 meta=json.loads((OLD/"lexer-command.json").read_text())
 assert meta["exit_code"]==0 and sha(Path(meta["output"]))==meta["output_sha256"]
 tokens={(r["file"],r["line"]):r["tokens"] for r in map(json.loads,Path(meta["output"]).read_text().splitlines())}
 index=json.loads((OLD/(obj+"-AST/index.json")).read_text());assert index["all_equal"]
 nodes=collections.defaultdict(list);labels=collections.defaultdict(list);available=set();provenance=[]
 for it in index["commands"]:
  p=OLD/(obj+"-AST")/it["command"];m=json.loads(p.read_text())
  assert m["exit_code"]==m["previous_exit_code"]==0 and not any(m["differences"].values())
  raw=Path(m["output"]);assert sha(raw)==m["output_sha256"]
  provenance.append(dict(path=str(p),sha256=sha(p)))
  for n,line in enumerate(raw.open(),1):
   r=json.loads(line);kind=r["record"]
   if kind not in ("available_file","range","decl_range","label"):continue
   f=m["logical_root"]+r["file"]
   if kind=="available_file":available.add(f);continue
   r.update(file=f,tu=m["tu"],raw=str(raw),raw_line=n,raw_sha256=m["output_sha256"],command=str(p))
   (labels if kind=="label" else nodes)[f].append(r)
 calls=collections.defaultdict(list)
 callmeta=json.loads((OUT/(obj+"-calls.json")).read_text())
 for m in callmeta:
  raw=Path(m["output"]);assert sha(raw)==m["sha256"]
  for i,line in enumerate(raw.open(),1):
   r=json.loads(line)
   if r["kind"]=="call" and r["file_resolved"] and r["line"]>0:
    calls[(norm_file(r["file"]),r["line"])].append(dict(stage=m["stage"],die=r["die"],cu=r["cu"],raw=str(raw),raw_line=i))
 domain=OUT/(obj+"-domain");d=json.loads((domain/"index.json").read_text())
 c=collections.defaultdict(set)
 for r in rows(domain,"lines-*.csv"):c[r["file"]].add(int(r["line"]))
 prior={(r["file"],int(r["line"])):r["category"] for r in rows(OLD/(obj+"-classification"),"lines-*.csv")}
 result=[];counts={k:dict(lines=0,DA=0) for k in CATEGORIES}
 own=collections.defaultdict(lambda:dict(lines=0,DA=0))
 cross=collections.defaultdict(lambda:dict(lines=0,DA=0))
 for row in rows(domain,"code-free-*.csv"):
  f,n,v=row["file"],int(row["line"]),int(row["DA"]);k=(f,n)
  assert k in prior,"new code_free target requires fresh AST/lex evidence"
  ts=tokens.get(k);ns=[r for r in nodes[f] if r["begin_line"]<=n<=r["end_line"]]
  ls=[r for r in labels[f] if r["begin_line"]<=n<=r["end_line"]]
  r=classify_code_free(n,c[f],ns,ts,ls,f in available,calls.get(k,[]))
  r.update(file=f,line=n,DA=v,tokens=ts,old_category=prior[k])
  result.append(r);cat=r["category"]
  counts[cat]["lines"]+=1;counts[cat]["DA"]+=v
  b=cross[(prior[k],cat)];b["lines"]+=1;b["DA"]+=v
  if cat=="own_stmt_no_code":
   b=own[r["statement_kind"]];b["lines"]+=1;b["DA"]+=v
 assert len(result)==len({(r["file"],r["line"]) for r in result})
 assert sum(x["DA"] for x in counts.values())==d["R_C0"]-d["R_C"]
 dest=OUT/(obj+"-classification");dest.mkdir()
 header=["file","line","DA","category","reason","description","old_category","tokens","witness","statement_kind"]
 parts=tables(dest,"lines",header,([r.get(k) for k in header] for r in result))
 parts+=tables(dest,"top20",header,([r.get(k) for k in header] for cat in CATEGORIES
       for r in sorted((x for x in result if x["category"]==cat),key=lambda x:(-x["DA"],x["file"],x["line"]))[:20]))
 for v in counts.values():
  v.update(denominator_C0=d["R_C0"],denominator_C=d["R_C"],
           ratio_C0=v["DA"]/d["R_C0"] if d["R_C0"] else None,
           ratio_C=v["DA"]/d["R_C"] if d["R_C"] else None)
 summary=dict(object=obj,categories=counts,own_statement_kinds=own,
   cross=[dict(old=k[0],new=k[1],**v) for k,v in sorted(cross.items())],
   difference=0,exactly_one_class=True,domain_index_sha256=sha(domain/"index.json"),
   AST_provenance=provenance,lexer_provenance_sha256=sha(OLD/"lexer-command.json"),
   call_provenance_sha256=sha(OUT/(obj+"-calls.json")),parts=parts)
 dump(dest/"summary.json",summary)
 print(json.dumps(counts,ensure_ascii=False))
if __name__=="__main__":main(sys.argv[1])
