"""Q.5 #16: existing static identities and same-name out-of-scope inventory."""
import collections,json
from run_scoped import WORK,sha
from static_gate_data import BASE,OBJECTS,data,bridge_inventory,rows,norm_name
from registration_identity import complete_gate
from pack_static_evidence import tables
from registration_address_check import dump

OUT=BASE/"registration-checks/batch3"


def main():
    summary=[]
    extpath=BASE/"ruling2/external-cu-register.json";external=json.loads(extpath.read_text())
    for obj in OBJECTS:
        refs,da,rlines,inv,checks,lcov=data(obj);bi=bridge_inventory(obj)
        revised=BASE/"identity-gate/ruling3-4"/(obj+"-rev1-identity")
        conclusions={d:r["conclusion"] for d,r in inv.items()}
        for row in rows(revised,"instances-*.csv"):
            conclusions[int(row["die"],16)]=row["new_conclusion"]
        assert set(inv)==set(bi)
        complete_gate([dict(id=d) for d in bi],conclusions)
        groups={r["name"]:r for r in rows(BASE/"identity-gate"/(obj+"-groups"),"groups-*.csv")}
        executed={r["name"] for r in refs if r["fnda"]>0}
        selected=[];top_count=0
        for d,r in bi.items():
            if r["tag"]!="subprogram":continue
            top_count+=1
            g=groups[r["name"]]
            if g["role"]!="known_out_of_scope" or norm_name(r["name"]) not in executed:continue
            ids=json.loads(g["dies"]);candidates=json.loads(g["reference_ids"])
            assert not any(refs[i]["fnda"]>0 for i in candidates)
            assert all(conclusions[x] not in (None,"pending","") for x in ids)
            selected.append([hex(d),r["name"],norm_name(r["name"]),r["decl_file"],r["decl_line"],
                r["ranges"],conclusions[d],candidates,[dict(name=refs[i]["name"],file=refs[i]["file"],start=refs[i]["start"],fnda=refs[i]["fnda"]) for i in candidates],
                "Existing closed identities; whole raw-name group has no executed reference candidate. No new ruling."])
        parts=tables(OUT,obj+"-same-name-outside",["die","raw_name","normalized_name","decl_file","decl_line","ranges","conclusion","reference_ids","candidate_facts","scope_evidence"],selected)
        units={}
        for row in external.get(obj,{}).get("entries",[]):
            assert row["conclusion"]=="not_instrumented" and row["member_match_unique"]
            key=(row["cu"],row["source"],row["producer"])
            units.setdefault(key,[]).append(row["name"])
        extparts=tables(OUT,obj+"-external-CUs",["cu","source","producer","names","evidence"],([*k,v,str(extpath)] for k,v in sorted(units.items())))
        summary.append(dict(object=obj,inventory=len(inv),closed=collections.Counter(conclusions.values()),unresolved=0,top_count=top_count,
            same_name_outside=len(selected),parts=parts,external_cus=len(units),
            producer_distribution=dict(collections.Counter(k[2] for k in units)),external_parts=extparts,
            provenance=[dict(path=str(p.relative_to(WORK)),sha256=sha(p)) for p in (extpath,revised/"summary.json",BASE/"identity-gate"/(obj+"-groups")/"index.json")]))
    dump(OUT/"identity-audit-summary.json",summary);print(json.dumps(summary))


if __name__=="__main__":main()
