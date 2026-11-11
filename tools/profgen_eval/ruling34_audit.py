"""Audit new/old static identities, ambiguity and C/S line evidence."""
import collections,json,sys
from pathlib import Path
from ruling34_inputs import OUT,TEMP,dump
from static_gate_data import OUT as OLDOUT,TEMP as OLDTEMP,OBJECTS
from ruling4_apply import calculate
from ruling3_domain import records
from apply_header_ruling import rows,norm_file
from pack_static_evidence import tables
from run_scoped import sha
from static_coverage_gate import profile_key

def main(obj):
    refs,da,rlines,inv,old,funcs,ic,groups,new=calculate(obj)
    dest=OUT/(obj+"-audit");dest.mkdir(exist_ok=False);parts=[]
    newc={(r["file"],int(r["line"])) for r in rows(OUT/(obj+"-C-domain"),"code-lines-*.csv")}
    ambiguity=[g for g in groups if g["conclusion"]=="identity_ambiguous"]
    def mass(gs):
        ks=set().union(*(rlines[i]&newc for g in gs for i in g["candidate_ids"])) if gs else set()
        return dict(lines=len(ks),DA=sum(da[k] for k in ks))
    classes=collections.defaultdict(list)
    for g in ambiguity:
        g["reference_loss"]=mass([g])
        classes[(tuple(g["reasons"]),g["failure_extent"])].append(g)
    parts+=tables(dest,"ambiguity-groups",["file","name","reasons","extent","instances","failed_instances","candidate_ids","reference_lines","DA"],
       ([g["file"],g["name"],g["reasons"],g["failure_extent"],g["instances"],g["failed_instances"],g["candidate_ids"],g["reference_loss"]["lines"],g["reference_loss"]["DA"]] for g in ambiguity))
    ordered=sorted(ambiguity,key=lambda g:(-g["reference_loss"]["DA"],g["file"],g["name"]))
    top=[]
    for rank,g in enumerate(ordered[:20],1):
        row={k:v for k,v in g.items() if k!="dies"}
        row["rank"]=rank
        row["candidates"]=[{k:refs[i][k] for k in ("id","file","name","start","end","fnda","copies")} for i in g["candidate_ids"]]
        top.append(row)
    parts+=tables(dest,"ambiguity-top20",["record"],([r] for r in top))
    selected={d for g in ordered[:20] for d in g["dies"]}
    parts+=tables(dest,"ambiguity-top20-instances",["die","function","check"],
        ([hex(d),funcs[d],ic[d]] for d in sorted(selected)))
    # Distinguish all groups with at least one empty instance from the earlier
    # report's pure-empty reason groups.
    empty=[];oldreasonsets=collections.Counter()
    for g in groups:
        reasons=tuple(sorted({v for d in g["dies"] for v in old[d]["reasons"]}))
        if any("empty_leaf" in r for r in reasons):
            oldreasonsets[str(reasons)]+=1
            if all("empty_leaf" in r for r in reasons):empty.append(g)
    counts=collections.defaultdict(lambda:dict(instances=0,groups=set(),reference_ids=set()))
    examples=collections.defaultdict(list);emptyrows=[]
    for gi,g in enumerate(empty):
        for d in g["dies"]:
            x=ic[d];cat=x["instance_class"]
            c=counts[cat];c["instances"]+=1;c["groups"].add(gi);c["reference_ids"].update(g["candidate_ids"])
            emptyrows.append([g["file"],g["name"],hex(d),cat,x])
            if len(examples[cat])<3:examples[cat].append(dict(die=d,group=[g["file"],g["name"]],raw_function=funcs[d],check=x))
    parts+=tables(dest,"pure-empty-instances",["file","name","die","class","check"],emptyrows)
    for cat,c in counts.items():
        ks=set().union(*(rlines[i] for i in c["reference_ids"])) if c["reference_ids"] else set()
        c.update(groups=len(c["groups"]),reference_ids=sorted(c["reference_ids"]),DA=sum(da[k] for k in ks),
          new_C_DA=sum(da[k] for k in ks&newc))
    # Exact raw rows for each example (leaf and descendants), not just a
    # deduplicated leaf-line witness. Raw extractor + file hash retained.
    ex_by_die={e["die"]:e for es in examples.values() for e in es}
    for e in ex_by_die.values():e["raw_line_rows"]=[]
    for r in records(obj,"S","line_row"):
        for d in set(r["dies_leaf_to_root"]) & set(ex_by_die):
            ex_by_die[d]["raw_line_rows"].append(r)
    for cat,es in examples.items():
        parts+=tables(dest,"pure-empty-example-"+cat,["example"],([e] for e in es))
    # Full matrix arm/cabac.h:36..105. C rows are unfiltered raw evidence,
    # plus separate executed-C-qualified and new-C columns.
    cr=collections.defaultdict(list)
    for r in records(obj,"C","line_row"):
        if norm_file(r["file"]).endswith("/libavcodec/arm/cabac.h") and 36<=r["line"]<=105 and not r["end_sequence"]:
            cr[r["line"]].append(dict(cu=r["cu"],row=r["row"],address=r["address"],dies=r["dies_leaf_to_root"]))
    sk=collections.defaultdict(list)
    with (OLDTEMP/(obj+"-map.jsonl")).open() as f:
        for l in f:
            r=json.loads(l)
            if r["kind"]!="instruction":continue
            key=profile_key(r["frames_leaf_to_root"])
            if not key:continue
            leaf=r["frames_leaf_to_root"][len(r["frames_leaf_to_root"])-len(key)]
            if norm_file(leaf["file"]).endswith("/libavcodec/arm/cabac.h") and 36<=leaf["line"]<=105:
                sk[leaf["line"]].append(r["address"])
    if obj.startswith("ffmpeg"):
        path=next(f for f,n in da if f.endswith("/libavcodec/arm/cabac.h"))
        parts+=tables(dest,"cabac-36-105",["file","line","DA","C_line_record","C_rows","in_new_C","S_has_key","S_key_instruction_addresses"],
           ([path,n,da.get((path,n)),bool(cr[n]),cr[n],(path,n) in newc,bool(sk[n]),sorted(set(sk[n]))] for n in range(36,106)))
    # Requested four real functions: a compact group-level old/new display;
    # full individual raw evidence is in rev1-identity/example-*.
    real=[]
    for name in ("fill_rectangle","get_cabac","filter_mb_edge","get_bits"):
        for g in groups:
            if name not in g["name"]:continue
            real.append(dict(requested=name,file=g["file"],name=g["name"],instances=len(g["dies"]),
              old_conclusions=dict(collections.Counter(old[d]["conclusion"] for d in g["dies"])),
              old_reasons=sorted({r for d in g["dies"] for r in old[d]["reasons"]}),
              new=g["conclusion"],new_reasons=g["reasons"],new_statuses=dict(collections.Counter(ic[d]["line_status"] for d in g["dies"]))))
    parts+=tables(dest,"real-examples",["example"],([r] for r in real))
    summary=dict(object=obj,ambiguity_groups=len(ambiguity),ambiguity=mass(ambiguity),
        ambiguity_classes=[dict(reasons=list(k[0]),extent=k[1],groups=len(gs),**mass(gs)) for k,gs in sorted(classes.items())],
        old_empty_reason_groups=dict(oldreasonsets),pure_empty_groups=len(empty),pure_empty_categories=counts,
        pure_empty_examples={cat:len(es) for cat,es in examples.items()},
        categories_note="groups can span classes; DA is a per-class reference-line union and not additive; ordinary nonempty members reported separately",
        command=["python3","tools/profgen_eval/ruling34_audit.py",obj])
    dump(dest/"summary.json",summary);dump(dest/"index.json",dict(parts=parts,summary_sha256=sha(dest/"summary.json")))
    print(json.dumps(summary,ensure_ascii=False))
if __name__=="__main__":main(sys.argv[1])
