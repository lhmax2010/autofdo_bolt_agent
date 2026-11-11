"""Three C definitions, fixed ruling4-rev2 identity/key facts; no sample inputs."""
import collections,json,sqlite3,sys
from ruling3_union import OUT,OLD,TEMP,dump
from ruling3_domain import reference
from ruling34_static import measures,BODY_NOTE
from apply_header_ruling import rows
from pack_static_evidence import tables
from run_scoped import WORK,sha

def main(obj):
    refs,da,rlines,owners,lp=reference(obj)
    original=set(owners)
    previous=OLD/(obj+"-static")
    prior=json.loads((previous/"summary.json").read_text())
    why=collections.defaultdict(set)
    ledger=list(rows(previous,"old-C-exclusions-*.csv"))
    for r in ledger:
        why[(r["file"],int(r["line"]))]=set(json.loads(r["reasons"]))-{"code_free_line"}
    has_key={k for k in original if "no_key_line" not in why[k]}
    conly={(r["file"],int(r["line"])) for r in rows(OLD/(obj+"-C-domain"),"code-lines-*.csv")}
    union={(r["file"],int(r["line"])) for r in rows(OUT/(obj+"-domain"),"lines-*.csv")}
    dest=OUT/(obj+"-static");dest.mkdir()
    summaries={}
    for name,c in (("v15",original),("ruling3",conly),("ruling3-rev1",union)):
        sub=dest/name;sub.mkdir()
        u,weights,s=measures(da,{k:owners[k] for k in c},why,has_key)
        gates={}
        for reason in ("identity_ambiguous","unmatched_in_elf","boundary_unavailable"):
            ks={k for k in c if reason in why[k]};mass=sum(da[k] for k in ks)
            gates[reason]=dict(lines=len(ks),DA=mass,denominator=s["R_C"],ratio=mass/s["R_C"] if s["R_C"] else None,
                               exceeds_one_percent=100*mass>s["R_C"])
        blockers=[k for k,v in gates.items() if v["exceeds_one_percent"]]
        if not s["R_C"]:blockers.append("zero_reference_denominator")
        elif 2*s["R_U"]<s["R_C"]:blockers.append("coverage_3_below_50_percent")
        buckets=collections.defaultdict(lambda:dict(lines=0,DA=0))
        oldwhy={}
        for k in original-u:
            reasons=why[k]|({"code_free_line"} if k not in c else set())
            assert reasons
            oldwhy[k]=sorted(reasons);b=buckets[tuple(sorted(reasons))];b["lines"]+=1;b["DA"]+=da[k]
        lost=sum(v["DA"] for v in buckets.values());den0=sum(da[k] for k in original)
        assert den0-s["R_U"]-lost==0
        s.update(object=obj,rule=name,identity_rule="ruling4-rev2 (fixed for all three domains)",
            registration_status="不可登记" if blockers else "可登记",registration_reasons=blockers,gates=gates,
            coverage_3_tier="undefined" if not s["R_C"] else ("<50%" if 2*s["R_U"]<s["R_C"] else ("50–80%" if 5*s["R_U"]<4*s["R_C"] else "≥80%")),
            code_bearing_ratio=dict(numerator=s["R_C"],denominator=den0,ratio=s["R_C"]/den0),
            old_C_to_new_U_loss=dict(buckets=[dict(reasons=list(k),**v) for k,v in sorted(buckets.items())],
                original_R_C=den0,R_U=s["R_U"],sum_loss=lost,difference=0,assertion_passed=True),
            body_fraction_4=BODY_NOTE,static_special_code=prior["static_special_code"])
        parts=tables(sub,"U",["file","line","DA","reference_id"],
            ([*k,da[k],next(iter(owners[k]))] for k in sorted(u)))
        parts+=tables(sub,"exclusions",["file","line","DA","reference_ids","reasons"],
            ([*k,da[k],sorted(owners[k]),sorted(why[k])] for k in sorted(c-u)))
        parts+=tables(sub,"old-C-exclusions",["file","line","DA","reasons"],
            ([*k,da[k],oldwhy[k]] for k in sorted(original-u)))
        parts+=tables(sub,"weights",list(weights[0]) if weights else ["reference_id"],
            ([w[k] for k in weights[0]] for w in weights))
        if name=="ruling3":
            for key in ("C_lines","U_lines","R_C","R_U","n_eff","K","loss_buckets","gates"):
                assert s[key]==prior[key],(obj,key,s[key],prior[key])
            s["C_only_reproduction_exact"]=True
        dump(sub/"summary.json",s)
        dump(sub/"index.json",dict(parts=parts,summary_sha256=sha(sub/"summary.json")))
        summaries[name]=s
        if name=="ruling3-rev1":
            added=union-conly
            parts2=tables(dest,"added-by-S",["file","line","DA","in_U","loss_reasons"],
                ([*k,da[k],k in u,sorted(why[k])] for k in sorted(added)))
            s["added_by_S"]=dict(lines=len(added),DA=sum(da[k] for k in added),
                U_lines=len(added&u),U_DA=sum(da[k] for k in added&u),
                loss_lines=len(added-u),loss_DA=sum(da[k] for k in added-u),parts=parts2)
            # Static key database already certified under the same identity rules.
            dbpath=WORK/"temp/prep-ruling3-4"/(obj+"-static.sqlite")
            db=sqlite3.connect(dbpath.as_uri()+"?mode=ro",uri=True)
            keylines={(f,n) for f,n in db.execute("SELECT DISTINCT file,line FROM kv")}
            outside=keylines-union
            s["S_keys_outside_C"]=dict(lines=len(outside),known_DA=sum(da.get(k,0) for k in outside),
                originally_in_C_lines=len(outside&original),originally_in_C_DA=sum(da[k] for k in outside&original),
                unavailable_DA_lines=sum(k not in da for k in outside))
            assert sum(da[k] for k in outside&original)==0
            def outside_rows():
                for k in sorted(outside):
                    ids=[i for i,ks in rlines.items() if k in ks] if da.get(k,0) else []
                    facts=[dict(id=i,fnda=refs[i]["fnda"],name=refs[i]["name"],start=refs[i]["start"],end=refs[i]["end"]) for i in ids]
                    yield [*k,da.get(k),k in original,"no_executed_reference_owner" if k not in original else "code_free_line",facts]
            s["S_keys_outside_C"]["parts"]=tables(dest,"S-keys-outside-C",
                ["file","line","DA","in_original_C","reason","reference_owners"],outside_rows())
            s["key_database"]=dict(path=str(dbpath),sha256=sha(dbpath));db.close()
            dump(sub/"summary.json",s)
            index=json.loads((sub/"index.json").read_text());index["summary_sha256"]=sha(sub/"summary.json");dump(sub/"index.json",index)
    dump(dest/"comparison.json",summaries)
    inputs=[previous/"summary.json",*previous.glob("old-C-exclusions-*.csv"),OUT/(obj+"-domain")/"index.json"]
    dump(dest/"index.json",dict(command=["python3","tools/profgen_eval/ruling3_union_static.py",obj],
        inputs=[dict(path=str(p),sha256=sha(p)) for p in inputs],comparison_sha256=sha(dest/"comparison.json"),
        note="Reuse immutable ruling4-rev2 identity/keys only after independently sealing C from line tables. No RUN data."))
    print(json.dumps({k:{n:v[n] for n in ("C_lines","R_C","U_lines","R_U","coverage_3","n_eff","K","registration_status")} for k,v in summaries.items()}))
if __name__=="__main__":main(sys.argv[1])
