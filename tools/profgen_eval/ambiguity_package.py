"""Observable-fact classification; never resolves an identity by DA or heuristics."""
import posixpath
from static_gate_data import *
from recheck_header_evidence import command_record
from dwarf_inventory import text

def mechanical(tus,conditional_include_evidence,definition_positions,same_variant=True):
    if len(set(tus))>1:return "a_different_TU","distinct recorded PGO TU prefixes"
    if conditional_include_evidence:return "b_same_TU_conditional_or_include","positive compiler conditional/include evidence"
    if len(set(definition_positions))>1 and len(set(tus))==1 and same_variant:
        return "c_same_TU_multiple_definitions","multiple C DWARF definition positions in one fixed variant"
    return "d_other","single candidate failed leaf-line constraint; no positive b/c evidence"

def cu_table(obj,stage):
    out={}
    for r in rows(BASE/(obj+"-"+stage+"-inventory-tables"),"compile_units-*.csv"):
        a=json.loads(r["attrs"]);n=text(a.get("name",""));d=text(a.get("comp_dir",""))
        out[int(r["offset"],16)]=dict(name=n,comp_dir=d,source=norm_file(posixpath.join(d,n)),
                                     producer=text(a.get("producer","")),dump_line=int(r["dump_line"]))
    return out

def main(obj):
    refs,da,rlines,inv,checks,lp=data(obj);bis=bridge_inventory(obj)
    scus=cu_table(obj,"S");ccus=cu_table(obj,"C")
    cdefs=collections.defaultdict(list)
    for d in rows(BASE/(obj+"-C-inventory-tables"),"code-dies-*.csv"):
        cdefs[d["name"]].append(d)
    commands=command_record(BASE/"ruling1"/(obj+"-C-commands.json"))
    cm=commands["compile_commands"]
    bybase=collections.defaultdict(set)
    for ci,cmd in enumerate(cm):
        for src in cmd["sources"]:bybase[posixpath.basename(src)].add(ci)
    dest=OUT/(obj+"-ambiguity");dest.mkdir(exist_ok=False)
    grouped=collections.defaultdict(list);badkeys=set()
    for die,ch in checks.items():
        k=(norm_file(ch["decl_file"]),norm_name(ch["name"]));grouped[k].append(die)
        if ch["conclusion"]=="identity_ambiguous":badkeys.add(k)
    c=set().union(*(rlines[i] for i,r in enumerate(refs) if r["fnda"]>0))
    details=[];candidates=[];instances=[];copyrows=[];usedcmd=set();classlines=collections.defaultdict(set)
    for cat in ("a_different_TU","b_same_TU_conditional_or_include","c_same_TU_multiple_definitions","d_other"):classlines[cat]
    for gid,k in enumerate(sorted(badkeys)):
        ds=grouped[k];ids=sorted({i for d in ds for i in checks[d]["candidate_ids"]})
        lines=set().union(*(rlines[i] for i in ids))&c
        mass=sum(da[l] for l in lines)
        tus=[];positions=[];reasons=set()
        for d in ds:
            s=bis[d];reasons.update(checks[d]["reasons"])
            instances.append([gid,hex(d),s["name"],scus[int(inv[d]["cu"],16)],s["decl_file"],s["decl_line"],
                              s["ranges"],s["tag"],s["abstract_origin"],checks[d]["conclusion"],checks[d]["reasons"],
                              json.loads(checks[d]["leaf_lines"])])
        for rid in ids:
            r=refs[rid];pos=set()
            for copy in r["copies"]:
                pgo=copy["name"]
                prefix,linkage=pgo.split(":",1) if ":" in pgo else ("",pgo)
                matching=cdefs.get(linkage,[])
                defs=[dict(die=d["die"],cu=ccus[int(d["cu"],16)]["source"],
                           decl_file=norm_file(d["decl_file"]),decl_line=int(d["decl_line"] or 0),tag=d["tag"]) for d in matching]
                for d in defs:pos.add((d["decl_file"],d["decl_line"]))
                cmdids=[]
                for ci in sorted(bybase.get(prefix,set()) if prefix else set().union(*(bybase.get(posixpath.basename(x["cu"]),set()) for x in defs))):
                    cmd=cm[ci]
                    if any((prefix and posixpath.basename(src)==prefix) or
                           (not prefix and any(x["cu"].endswith("/"+src.lstrip("./")) for x in defs))
                           for src in cmd["sources"]):
                        cmdids.append(ci);usedcmd.add(ci)
                tus.append(prefix if prefix else "<external>")
                copyrows.append([gid,rid,pgo,prefix,linkage,copy["count"],copy["record"],defs,cmdids,
                                 "exact PGO linkage and CU/compile-command facts; no new identity ruling"])
            positions.extend(pos)
            candidates.append([gid,rid,r["file"],r["name"],r["start"],r["end"],r["fnda"],
                               sum(da[l] for l in rlines[rid]),len(rlines[rid]),sorted(pos)])
        category,why=mechanical(tus,False,positions)
        classlines[category].update(lines)
        details.append(dict(group=gid,file=k[0],name=k[1],category=category,classification_reason=why,
                            S_instances=len(ds),ambiguous_S_instances=sum(checks[d]["conclusion"]=="identity_ambiguous" for d in ds),
                            candidate_ids=ids,reference_lines=len(lines),DA=mass,failed_checks=sorted(reasons),_lines=lines))
    global_lines=set().union(*(x["_lines"] for x in details)) if details else set()
    den=sum(da[k] for k in c);mass=sum(da[k] for k in global_lines)
    top=[];covered=set()
    for x in sorted(details,key=lambda x:(-x["DA"],x["group"])):
        if len(top)>=20 and (not mass or sum(da[k] for k in covered)*10>=9*mass):break
        top.append(x["group"]);covered.update(x["_lines"])
    summary=dict(object=obj,groups=len(details),involved_reference_lines=len(global_lines),DA=mass,denominator=den,
        fraction=mass/den if den else None,top_groups=top,top_group_count=len(top),
        top_unique_DA=sum(da[k] for k in covered),top_fraction=sum(da[k] for k in covered)/mass if mass else None,
        top_note="all available groups when fewer than 20; zero ambiguous groups => empty list",
        categories=[dict(category=cat,groups=sum(x["category"]==cat for x in details),lines=len(ls),DA=sum(da[k] for k in ls),
                         denominator=den,fraction=sum(da[k] for k in ls)/den if den else None)
                    for cat,ls in sorted(classlines.items())],
        class_DA_note="each group has one class; class DA is union of its lines. Cross-class line overlap is recorded separately, never double-counted in total",
        closed_inventory_sha256=sha(OLD/(obj+"-inventory/index.json")),
        unresolved=0,ordinary_checks_sha256=sha(OLD/(obj+"-ordinary/index.json")))
    overlap=collections.Counter()
    for k in global_lines:overlap[tuple(sorted(cat for cat,ls in classlines.items() if k in ls))]+=da[k]
    summary["class_overlap_DA"]=[dict(classes=list(k),DA=v) for k,v in sorted(overlap.items())]
    parts=[]
    cols=["group","file","name","category","classification_reason","S_instances","ambiguous_S_instances","candidate_ids","reference_lines","DA","failed_checks"]
    parts+=tables(dest,"groups",cols,([x[n] for n in cols] for x in details))
    parts+=tables(dest,"S-instances",["group","die","raw_name","CU","decl_file","decl_line","ranges","tag","abstract_origin","conclusion","failed_checks","leaf_lines"],instances)
    parts+=tables(dest,"candidates",["group","reference_id","file","name","start","end","FNDA","all_candidate_line_DA","candidate_lines","C_definition_positions"],candidates)
    # Compiler copies may be numerous: one record/copy per row, no duplicated aggregate.
    parts+=tables(dest,"candidate-copies",["group","reference_id","PGO_name","TU_prefix","linkage","FNDA","record","C_definitions","compile_command_ids","fact_note"],copyrows)
    parts+=tables(dest,"commands",["id","build_log","line","sources","command"],
                  ([i,commands["log"],cm[i]["line"],cm[i]["sources"],cm[i]["text"]] for i in sorted(usedcmd)))
    parts+=tables(dest,"ambiguous-lines",["file","line","DA","classes"],
                  ([*k,da[k],sorted(cat for cat,ls in classlines.items() if k in ls)] for k in sorted(global_lines)))
    dump(dest/"summary.json",summary)
    dump(dest/"index.json",dict(parts=parts,summary_sha256=sha(dest/"summary.json"),lcov_sha256=sha(lp),
             command=["python3","tools/profgen_eval/ambiguity_package.py",obj],
             source_C_commands=commands["log"],source_C_log_sha256=commands["log_sha256"]))
    print(json.dumps(summary),flush=True)
if __name__=="__main__":
    import sys
    main(sys.argv[1])
