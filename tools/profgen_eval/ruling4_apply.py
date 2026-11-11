"""Apply ruling4 rev1 to the original, code-bearing inventory only."""
import collections,json,sys
from pathlib import Path
from static_gate_data import data,OBJECTS,bridge_inventory
from ruling34_inputs import OUT,TEMP,dump
from ruling34_rules import instance_check,group_check
from apply_header_ruling import norm_file,norm_name
from pack_static_evidence import tables
from run_scoped import sha

def load_functions(obj):
    result={}
    with (TEMP/(obj+"-S-rev1.jsonl")).open() as f:
        for line in f:
            r=json.loads(line)
            if r["kind"]=="function":result[r["die"]]=r
    return result

def calculate(obj, key_input=None, key_guard=None):
    refs,da,rlines,inv,old,lp=data(obj);funcs=load_functions(obj)
    key_proofs={};failed_top=set()
    key_input=key_input or TEMP/(obj+"-official-key-presence.jsonl")
    with key_input.open() as f:
        for line in f:
            x=json.loads(line)
            if x["kind"]=="die_keys":key_proofs[x["die"]]=x
            elif x["kind"]=="boundary_unavailable":failed_top.update(x["dies"])
    if key_guard is None:
        assert set(key_proofs)==set(inv),("key inventory changed",set(key_proofs)^set(inv))
    else:
        # A missing proof is not evidence of zero keys. The v1.7 guard
        # sends that instance through the active-instance checks below.
        assert set(key_proofs)<=set(inv),"foreign key-proof DIE"
    if key_guard is None:
        assert not any(key_proofs[d]["top_die"] in failed_top for d in old),"ordinary candidate has unavailable static key proof"
    assert all(funcs[d]["ranges"] for d in inv)
    # Propagate positive leaf witnesses through actual parent DIE links, not name matches.
    descendant_positive=set()
    for d,r in funcs.items():
        if any(x["line"]>0 for x in r["leaf_lines"]):descendant_positive.update(r["ancestors"])
    instances={};groups=collections.defaultdict(list)
    for d,ch in old.items():
        r=funcs[d];r["descendant_nonzero_leaf"]=d in descendant_positive;r["accepted_key_instructions"]=key_proofs.get(d,{}).get("accepted_key_instructions",0)
        if key_guard is not None:
            r["no_key_proof_unavailable"]=(d not in key_proofs or not key_guard(d))
        # Collection must agree with the original leaf evidence, not silently repair it.
        oldleaf={(norm_file(x["file"]),x["line"]) for x in json.loads(ch["leaf_rows"])}
        newleaf={(norm_file(x["file"]),x["line"]) for x in r["leaf_lines"]}
        assert oldleaf==newleaf,(obj,d,oldleaf^newleaf)
        cs=[refs[i] for i in ch["candidate_ids"]]
        instances[d]=instance_check(r,cs,json.loads(ch["c_declaration_positions"]))
        groups[(norm_file(r["decl_file"]),norm_name(r["name"]))].append(d)
    newgroups=[];new={}
    for key,ds in sorted(groups.items()):
        ids=old[ds[0]]["candidate_ids"]
        assert all(old[d]["candidate_ids"]==ids for d in ds)
        g=group_check([instances[d] for d in ds],[refs[i] for i in ids])
        g.update(file=key[0],name=key[1],dies=ds,candidate_ids=ids)
        newgroups.append(g)
        for d in ds:new[d]=dict(candidate_ids=ids,conclusion=g["conclusion"],all_no_key=g["all_no_key"])
    return refs,da,rlines,inv,old,funcs,instances,newgroups,new

def main(obj):
    refs,da,rlines,inv,old,funcs,instances,groups,new=calculate(obj)
    dest=OUT/(obj+"-rev1-identity");dest.mkdir(exist_ok=False)
    parts=tables(dest,"instances",["die","old_conclusion","old_reasons","new_conclusion","check","ranges"],
        ([hex(d),old[d]["conclusion"],old[d]["reasons"],new[d]["conclusion"],instances[d],funcs[d]["ranges"]] for d in sorted(old)))
    parts+=tables(dest,"groups",["file","name","result"],([g["file"],g["name"],g] for g in groups))
    traces=[];tracecount=collections.Counter()
    for d in sorted(inv):
        r=funcs[d]
        if r["tag"]!="inlined_subroutine":continue
        for attr in ("decl_file","decl_line"):
            t=r[attr+"_trace"];path=t.get("path",[])
            tracecount[attr+":"+("abstract_origin" if any(x["edge"]=="DW_AT_abstract_origin" for x in path) else "other")]+=1
            assert t["found"],(obj,d,attr)
            traces.append([hex(d),attr,r[attr],t])
    parts+=tables(dest,"declaration-paths",["die","attribute","resolved_value","lookup"],traces)
    emptygroups=[g for g in groups if any("empty_leaf" in ",".join(old[d]["reasons"]) for d in g["dies"])]
    # A group can contain ordinary passing instances too. Report those separately,
    # and the four requested categories for its originally empty leaf instances.
    categories=collections.defaultdict(lambda:dict(instances=0,groups=set(),reference_ids=set(),examples=[]))
    records=[]
    for gi,g in enumerate(emptygroups):
        for d in g["dies"]:
            was_empty="empty_leaf" in ",".join(old[d]["reasons"])
            cat=instances[d]["instance_class"]
            c=categories[cat];c["instances"]+=1;c["groups"].add((g["file"],g["name"]));c["reference_ids"].update(g["candidate_ids"])
            records.append([g["file"],g["name"],hex(d),was_empty,cat,instances[d],funcs[d]["ranges"]])
            if len(c["examples"])<3:c["examples"].append(dict(die=hex(d),group=[g["file"],g["name"]],check=instances[d],raw_function=funcs[d]))
    parts+=tables(dest,"empty-group-instances",["file","name","die","originally_empty","class","check","ranges"],records)
    for cat,c in categories.items():
        ks=set().union(*(rlines[i] for i in c["reference_ids"])) if c["reference_ids"] else set()
        c.update(groups=len(c["groups"]),reference_ids=sorted(c["reference_ids"]),DA=sum(da[k] for k in ks),DA_note="union of reference lines per class; groups may span classes, not additive")
    examples=[]
    for needle in ("fill_rectangle","get_cabac","filter_mb_edge","get_bits"):
        matched=[g for g in groups if needle in g["name"]]
        parts+=tables(dest,"example-"+needle,["group","instance","old","new"],
          ([{k:v for k,v in g.items() if k!="dies"},funcs[d],{k:old[d][k] for k in ("conclusion","reasons","candidate_ids")},instances[d]] for g in matched for d in g["dies"]))
        examples.append(dict(name=needle,groups=len(matched),instances=sum(len(g["dies"]) for g in matched)))
    closed=collections.Counter(r["conclusion"] for r in new.values())
    summary=dict(object=obj,original_inventory=len(inv),ordinary_instances=len(old),new_closed=closed,
      unresolved=0,all_no_key_groups=sum(g["all_no_key"] for g in groups),
      no_key_instances=sum(r["line_status"]=="no_key_instance" for r in instances.values()),
      original_empty_groups=len(emptygroups),empty_group_categories=categories,declaration_paths=tracecount,
      real_examples=examples,source=str(TEMP/(obj+"-S-rev1.jsonl")),source_sha256=sha(TEMP/(obj+"-S-rev1.jsonl")),
      official_key_input=str(TEMP/(obj+"-official-key-presence.jsonl")),official_key_sha256=sha(TEMP/(obj+"-official-key-presence.jsonl")),command=["python3","tools/profgen_eval/ruling4_apply.py",obj])
    # Large examples stored as per-class files, not embedded in the summary.
    for cat,c in categories.items():
        ex=c.pop("examples");dump(dest/("empty-example-"+cat+".json"),ex)
    dump(dest/"summary.json",summary);dump(dest/"index.json",dict(parts=parts,summary_sha256=sha(dest/"summary.json")))
    print(json.dumps(summary,ensure_ascii=False))
if __name__=="__main__":main(sys.argv[1])
