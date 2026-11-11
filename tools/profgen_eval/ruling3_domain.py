"""C-only ruling3 evidence. No sampled ELF or S mapping participates."""
import collections,json,bisect,sys
from pathlib import Path
from ruling34_inputs import OUT,TEMP,BASE,dump
from static_gate_data import OBJECTS
from run_scoped import WORK,sha
from coverage_reference import parse_lcov
from apply_header_ruling import rows,norm_file,norm_name
from pack_static_evidence import tables
from ruling34_rules import code_line_domain

def reference(obj):
    cov=BASE/(obj+"-coverage-tables");meta=json.loads((cov/"index.json").read_text())
    path=Path(meta["lcov"])
    if not path.is_absolute():path=WORK/path
    if not path.exists():path=WORK/"temp/prep-identity-gate"/(obj+"-reference.lcov")
    da={(norm_file(f),int(l)):v for f,x in parse_lcov(path).items() for l,v in x["da"].items()}
    funcs=list(rows(cov,"merged-functions-*.csv"))
    perfile=collections.defaultdict(list)
    for f,n in da:perfile[f].append(n)
    for ns in perfile.values():ns.sort()
    rr={};owners=collections.defaultdict(set)
    for i,r in enumerate(funcs):
        r.update(id=i,file=norm_file(r["file"]),start=int(r["start"]),end=int(r["end"]),fnda=int(r["fnda"]),
                 copies=json.loads(r["copies"]))
        ns=perfile[r["file"]]
        rr[i]={(r["file"],n) for n in ns[bisect.bisect_left(ns,r["start"]):bisect.bisect_right(ns,r["end"])]}
        if r["fnda"]>0:
            for k in rr[i]:owners[k].add(i)
    return funcs,da,rr,owners,path

def records(obj,stage,kind=None):
    p=TEMP/(obj+"-"+stage+"-dwarf.jsonl")
    with p.open() as f:
        for l in f:
            r=json.loads(l)
            if kind is None or r["kind"]==kind:yield r

def functions(obj,stage):return {r["die"]:r for r in records(obj,stage,"function")}

def main(obj):
    ref,da,rr,owners,lp=reference(obj);oldc=set(owners)
    meta=json.loads((OUT/(obj+"-C-dwarf-command.json")).read_text())
    assert meta["exit_code"]==0 and sha(Path(meta["output"]))==meta["output_sha256"]
    cfunc=functions(obj,"C")
    bykey=collections.defaultdict(list)
    for r in ref:bykey[(r["file"],r["name"])].append(r["id"])
    executable={};ambiguous=[]
    for d,r in cfunc.items():
        if r["declaration"] or not r["self_or_descendant_has_ranges"]:continue
        cs=bykey[(norm_file(r["decl_file"]),norm_name(r["name"]))]
        pos=[x for x in cs if ref[x]["fnda"]>0]
        if len(cs)==1 and pos:executable[d]=pos
        elif len(cs)>1 and pos:ambiguous.append(dict(die=d,candidates=cs))
    assert not ambiguous,("C-only executed reference association is not unique",ambiguous[:3])
    newc,witness=code_line_domain(oldc,records(obj,"C","line_row"),executable)
    removed=oldc-newc
    dest=OUT/(obj+"-C-domain");dest.mkdir(exist_ok=False)
    parts=tables(dest,"code-lines",["file","line","DA","C_row","executed_C_DIEs","executed_reference_ids"],
        ([*k,da[k],witness[k]["row"],witness[k]["executed_C_DIEs"],
          sorted({rid for d in witness[k]["executed_C_DIEs"] for rid in executable[d]})] for k in sorted(newc)))
    parts+=tables(dest,"code-free-lines",["file","line","DA","reason"],([*k,da[k],"code_free_line"] for k in sorted(removed)))
    perfile=collections.defaultdict(lambda:[0,0])
    for f,n in removed:perfile[f][0]+=1;perfile[f][1]+=da[(f,n)]
    parts+=tables(dest,"code-free-files",["file","lines","DA"],([f,*v] for f,v in sorted(perfile.items())))
    parts+=tables(dest,"C-executed-DIEs",["die","name","decl_file","decl_line","ranges","reference_ids"],
                  ([d,cfunc[d]["name"],cfunc[d]["decl_file"],cfunc[d]["decl_line"],cfunc[d]["ranges"],ids] for d,ids in sorted(executable.items())))
    summary=dict(object=obj,old_C_lines=len(oldc),new_C_lines=len(newc),old_R_C=sum(da[k] for k in oldc),
                 new_R_C=sum(da[k] for k in newc),code_free_lines=len(removed),code_free_DA=sum(da[k] for k in removed),
                 executed_C_DIEs=len(executable),C_only=True,S_inputs_used=False,parts=parts,
                 C_elf_sha256=meta["elf_sha256"],C_rows_sha256=meta["output_sha256"],lcov_sha256=sha(lp),
                 command=["python3","tools/profgen_eval/ruling3_domain.py",obj])
    assert summary["old_R_C"]-summary["new_R_C"]==summary["code_free_DA"]
    dump(dest/"index.json",summary);print(json.dumps({k:v for k,v in summary.items() if k!="parts"}))
if __name__=="__main__":main(sys.argv[1])
