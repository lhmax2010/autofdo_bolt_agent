"""Revision2 evidence, actual-key parity, and a-e verdicts."""
import collections,json,sys
from pathlib import Path
from ruling34_inputs import OUT,TEMP,dump
from static_gate_data import TEMP as OLD_TEMP,OBJECTS
from ruling4_apply import calculate
from static_coverage_gate import profile_key
from pack_static_evidence import tables
from run_scoped import sha
def verdict(x):
    return "failed" if not x["definition_ok"] or x["line_status"] not in ("pass","no_key_instance") else ("exempt" if x["line_status"]=="no_key_instance" else "passed")
def main(obj):
    refs,da,rlines,inv,old,funcs,ic,groups,new=calculate(obj)
    dest=OUT/(obj+"-rev2-proof");dest.mkdir(exist_ok=True)
    group_of={d:g for g in groups for d in g["dies"]}
    # Same key-generation block as the formal tool is the decision source.
    sizes={};keyinfo={};fail=[]
    with (TEMP/(obj+"-official-key-presence.jsonl")).open() as f:
        for line in f:
            r=json.loads(line)
            if r["kind"]=="key_presence":sizes[(r["group"],r["address"])]=r["key_frames"]
            elif r["kind"]=="die_keys":keyinfo[r["die"]]=r
            elif r["kind"]=="boundary_unavailable":fail.append(r)
    oldcases=json.loads((OUT/"descendant-key-crosscheck.json").read_text()).get(obj,{}).get("descendant_claim_without_actual_key",[])
    target={int(e["die"],16) for e in oldcases};evidence=[];compared=0;rejected=collections.Counter()
    calls={c["die"]:dict(parent_die=p,**c) for p,r in funcs.items() for c in r["direct_inline_calls"]}
    callpath=TEMP/(obj+"-direct-calls.jsonl")
    if callpath.exists():
        with callpath.open() as f:
            for line in f:
                c=json.loads(line);calls[c["die"]]=c
    with (OLD_TEMP/(obj+"-map.jsonl")).open() as f:
        for line in f:
            r=json.loads(line)
            if r["kind"]!="instruction":continue
            n=len(profile_key(r["frames_leaf_to_root"]) or [])
            assert sizes[(r["group"],r["address"])]==n,(obj,r["address"],n)
            compared+=1
            hits=set(r["dies_leaf_to_root"])&target
            if not hits:continue
            assert n==0
            sources=[]
            for i,frame in enumerate(r["frames_leaf_to_root"]):
                if frame["line"]!=0:continue
                if i==0:sources.append(dict(frame=i,source="line_table",value=0));continue
                child=r["dies_leaf_to_root"][i-1]
                assert child in calls,("missing direct DW_AT_call_line provenance",obj,child)
                assert calls[child]["call_line"]==0
                sources.append(dict(frame=i,source="DW_AT_call_line",source_child_die=hex(child),raw=calls[child]))
            for d in sorted(hits):
                rejected[d]+=1
                evidence.append([hex(d),r["address"],r["group"],r["frames_leaf_to_root"],sources,ic[d],verdict(ic[d])])
    assert target<=set(rejected)
    parts=tables(dest,"e-addresses",["die","address","top_group","complete_context","zero_line_provenance","exemption_checks","verdict"],evidence)
    parts+=tables(dest,"e-instances",["die","group","ranges","checks","verdict","rejected_addresses","key_proof"],
      ([hex(d),[group_of[d]["file"],group_of[d]["name"]],funcs[d]["ranges"],ic[d],verdict(ic[d]),rejected[d],keyinfo[d]] for d in sorted(target)))
    def summarize(ds):
        gs={(group_of[d]["file"],group_of[d]["name"]) for d in ds}
        rs={i for d in ds for i in new[d]["candidate_ids"]}
        lines=set().union(*(rlines[i] for i in rs)) if rs else set()
        return dict(instances=len(ds),groups=len(gs),reference_DA=sum(da[k] for k in lines))
    classified=collections.defaultdict(list)
    for d,x in ic.items():classified[(x["instance_class"],verdict(x))].append(d)
    classes=[dict(instance_class=k[0],verdict=k[1],**summarize(ds)) for k,ds in sorted(classified.items())]
    # Explicit zero rows for requested categories absent in real data.
    for cat in ("a_self_and_descendants_zero","b_descendant_key_call_in_decl_file","c_descendant_key_call_not_in_decl_file","d_self_leaf_other_file","e_nonleaf_zero_rejected"):
        for v in ("exempt","passed","failed"):
            if (cat,v) not in classified:classes.append(dict(instance_class=cat,verdict=v,instances=0,groups=0,reference_DA=0))
    parts+=tables(dest,"a-e-verdicts",["instance_class","verdict","instances","groups","reference_DA"],
                 ([c[k] for k in ("instance_class","verdict","instances","groups","reference_DA")] for c in classes))
    parts+=tables(dest,"all-key-proofs",["die","top_die","touched_instructions","accepted_key_instructions"],
      ([hex(d),hex(r["top_die"]),r["touched_instructions"],r["accepted_key_instructions"]] for d,r in sorted(keyinfo.items())))
    summary=dict(object=obj,all_code_DIEs=len(keyinfo),all_top_groups=len({k[0] for k in sizes}),
       existing_mapping_instructions_compared=compared,key_acceptance_or_depth_differences=0,
       original_e_subset=summarize(target),original_e_verdicts=dict(collections.Counter(verdict(ic[d]) for d in target)),
       a_e_classes=classes,interpretation="per-class union DA; groups can straddle classes, not additive",
       boundary_failures=fail,command=["python3","tools/profgen_eval/ruling4_rev2_evidence.py",obj])
    dump(dest/"summary.json",summary);dump(dest/"index.json",dict(parts=parts,summary_sha256=sha(dest/"summary.json")))
    print(json.dumps(summary,ensure_ascii=False))
if __name__=="__main__":main(sys.argv[1])
