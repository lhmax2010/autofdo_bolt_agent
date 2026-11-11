"""Independent CSV accounting and macro-region facts. No sampled inputs."""
import collections,json,bisect
from static_gate_data import *
from audit_macro_inputs import function_stream
from coverage_reference import main_file_id

def main(obj):
    refs,da,rlines,inv,checks,lp=data(obj)
    dest=OUT/(obj+"-static")
    summary=json.loads((dest/"summary.json").read_text())
    u=list(rows(dest,"U-*.csv"));ex=list(rows(dest,"exclusions-*.csv"))
    keys=lambda xs:{(x["file"],int(x["line"])) for x in xs}
    assert len(keys(u))==len(u) and len(keys(ex))==len(ex) and not (keys(u)&keys(ex))
    c=set().union(*(rlines[i] for i,r in enumerate(refs) if r["fnda"]>0))
    assert keys(u)|keys(ex)==c
    RU=sum(int(r["DA"]) for r in u);RC=sum(da[k] for k in c)
    buckets=collections.Counter()
    for r in ex:
        rs=tuple(json.loads(r["reasons"]));assert rs and rs==tuple(sorted(set(rs)))
        buckets[rs]+=int(r["DA"])
    assert RC-RU==sum(buckets.values())==sum(int(x["DA"]) for x in ex)
    assert (RC,RU)==(summary["R_C"],summary["R_U"])
    ws=[int(r["weight"]) for r in rows(dest,"weights-*.csv") if r["eligible"]=="True"]
    neff=sum(ws)**2/sum(x*x for x in ws) if ws and sum(x*x for x in ws) else None
    assert neff==summary["n_eff"]
    # Macro membership from actual expanded FileIDs/code regions, not file-name heuristics.
    cov=BASE/(obj+"-coverage-tables")
    source=Path(json.loads((cov/"index.json").read_text())["json"])
    byfile=collections.defaultdict(list)
    for f,n in da:byfile[f].append(n)
    for a in byfile.values():a.sort()
    mainlines=set();macrolines=set()
    for f in function_stream(source):
        m=main_file_id(f);expanded={r[6] for r in f["regions"] if r[7]==1}
        for rg in f["regions"]:
            if rg[7]!=0:continue
            file=norm_file(f["filenames"][rg[5]]);ls=byfile[file]
            ks={(file,n) for n in ls[bisect.bisect_left(ls,rg[0]):bisect.bisect_right(ls,rg[2])]}
            if rg[5]==m:mainlines.update(ks)
            if rg[5] in expanded:macrolines.update(ks)
    only=macrolines-mainlines
    # No changed C definition is silently accepted.
    assert not c&only,("C includes macro-only lines",obj,sorted(c&only)[:10])
    macrofiles={f for f,n in macrolines}
    perfile=[]
    for f in sorted(macrofiles):
        ks={k for k in macrolines if k[0]==f}
        os={k for k in only if k[0]==f}
        perfile.append([f,len(ks),sum(da[k] for k in ks),len(os),sum(da[k] for k in os),
                        sum(v for (ff,n),v in da.items() if ff==f)])
    parts=tables(dest,"macro-DA",["file","macro_region_lines","macro_region_DA","macro_only_lines","macro_only_DA","all_file_DA"],perfile)
    execnames={r["name"] for r in refs if r["fnda"]>0}
    outscope=[]
    for g in rows(OUT/(obj+"-groups"),"groups-*.csv"):
        if g["role"]=="known_out_of_scope" and norm_name(g["name"]) in execnames:
            outscope.append(g)
    parts+=tables(dest,"same-name-outside",["name","role","dies","reference_ids","executed_reference_ids"],
                  ([g[k] for k in ["name","role","dies","reference_ids","executed_reference_ids"]] for g in outscope))
    macro=dict(macro_region_DA=sum(da[k] for k in macrolines),macro_only_DA=sum(da[k] for k in only),
        all_DA=sum(da.values()),macro_region_fraction=sum(da[k] for k in macrolines)/sum(da.values()),
        macro_only_fraction=sum(da[k] for k in only)/sum(da.values()),
        macro_expansion_files_all_DA=sum(v for (f,n),v in da.items() if f in macrofiles),
        source_json=str(source),source_json_sha256=sha(source),
        C_contains_macro_only_lines=0,
        note="region-specific macro union and macro-only DA; all-file DA is descriptive, never a blanket exclusion")
    audit=dict(object=obj,U_rows=len(u),exclusion_rows=len(ex),R_C=RC,R_U=RU,loss=sum(buckets.values()),
        loss_difference=RC-RU-sum(buckets.values()),assertions_passed=True,n_eff=neff,
        same_normalized_name_outside_mapping=len(outscope),macro=macro,parts=parts)
    dump(dest/"audit.json",audit)
    # These annotations contain no new sample-derived quantity.
    summary["macro_reference"]=macro
    summary["same_normalized_name_outside_mapping"]=len(outscope)
    if outscope:
        summary["registration_status"]="不可登记"
        summary["registration_reasons"].append("same_name_outside_mapping_requires_explicit_ruling")
    # Correct branch label to frozen n_eff=3; the number itself is unchanged.
    summary["n_eff_branch"]="undefined_no_eligible_reference_weight" if neff is None else ("below_3" if neff<3 else "at_least_3")
    dump(dest/"summary.json",summary)
    index=json.loads((dest/"index.json").read_text());index["parts"]+=parts
    index["summary_sha256"]=sha(dest/"summary.json");index["audit_sha256"]=sha(dest/"audit.json")
    dump(dest/"index.json",index)
    print(json.dumps(audit),flush=True)
if __name__=="__main__":
    import sys
    main(sys.argv[1])
