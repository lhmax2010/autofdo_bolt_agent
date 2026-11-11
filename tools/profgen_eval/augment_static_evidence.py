"""Supplement explicit inline-origin flags and reference identities."""
from static_gate_data import *
def main():
    for obj in OBJECTS:
        bi=bridge_inventory(obj);origins={r["abstract_origin"] for r in bi.values() if r["abstract_origin"]>=0}
        p=OUT/(obj+"-ambiguity")
        flags=[]
        for r in rows(p,"S-instances-*.csv"):
            d=int(r["die"],16)
            flags.append([r["group"],r["die"],d in origins,bi[d]["tag"]=="inlined_subroutine",bi[d]["abstract_origin"]])
        parts=tables(p,"S-inline-flags",["group","die","is_inline_abstract_source","is_inlined_instance","abstract_origin_offset"],flags)
        index=json.loads((p/"index.json").read_text());index["parts"]+=parts
        index["inline_flags_command"]=["python3","tools/profgen_eval/augment_static_evidence.py"]
        index["inline_flags_input_sha256"]=sha(TEMP/(obj+"-inventory.jsonl"));dump(p/"index.json",index)
        refs,da,rlines,inv,ch,lp=data(obj)
        dest=OUT/(obj+"-static");s=json.loads((dest/"summary.json").read_text())
        out=[]
        for rid in s["unmatched_reference_functions"]:
            r=refs[rid]
            out.append([rid,r["file"],r["name"],r["start"],r["end"],r["fnda"],r["copies"],
                        sorted(hex(d) for d,c in ch.items() if rid in c["candidate_ids"])])
        parts=tables(dest,"unmatched-reference",["reference_id","file","name","start","end","FNDA","coverage_copies","ambiguous_candidate_DIEs"],out)
        ix=json.loads((dest/"index.json").read_text());ix["parts"]+=parts;dump(dest/"index.json",ix)
    print("All S instance flags and unmatched reference identities written; no identity conclusion changed.")
if __name__=="__main__":main()
