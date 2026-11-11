"""Reference-only U and exclusion ledger, using a separately generated static map.

SQLite bounds memory; no RUN/sample profile path is accepted.
"""
import collections,json,sqlite3,sys
from static_gate_data import *

BODY_NOTE="未计算（需要 RUN 的 body 分母，修正案3登记后按 RUN 计算）"

def profile_key(frames):
    """Exact leaf-zero/nonleaf-zero rejection and 16-bit offset convention."""
    if not frames or any(f["line"]==0 for f in frames):return None
    accepted=[]
    for f in reversed(frames):
        if f["name"] in ("","<invalid>"):break
        accepted.append([f["name"],(f["line"]-f["start_line"])&65535,f["base_discriminator"]])
    if not accepted:return None
    return accepted

def measures(da,owners,reasons,has_key):
    c=set(owners);u={k for k in c if not reasons[k] and k in has_key}
    den=sum(da[k] for k in c);total=sum(da[k] for k in u)
    by_fn=collections.defaultdict(list)
    for k in u:
        assert len(owners[k])==1
        by_fn[next(iter(owners[k]))].append(k)
    weights=[]
    for f,ks in sorted(by_fn.items()):
        vals=[da[k] for k in ks]
        eligible=len(ks)>=5 and len(set(vals))>1
        weights.append(dict(reference_id=f,lines=len(ks),reference_mass=sum(vals),
                            eligible=eligible,weight=sum(vals) if eligible else 0,
                            reason="eligible" if eligible else ("fewer_than_5_lines" if len(ks)<5 else "constant_reference")))
    ws=[w["weight"] for w in weights if w["eligible"]]
    neff=sum(ws)**2/sum(w*w for w in ws) if ws and sum(w*w for w in ws) else None
    K=None
    if total:
        ordered=sorted((da[k] for k in u),reverse=True);cum=0
        for v in ordered:
            cum+=v
            if 5*cum>=4*total:
                K=sum(x>=v for x in ordered);break
    buckets=collections.defaultdict(lambda:dict(lines=0,DA=0))
    for k in c-u:
        assert reasons[k],("missing exclusion reason",k)
        b=buckets[tuple(sorted(reasons[k]))];b["lines"]+=1;b["DA"]+=da[k]
    loss=sum(b["DA"] for b in buckets.values())
    assert loss==den-total
    return u,weights,dict(C_lines=len(c),U_lines=len(u),R_C=den,R_U=total,
        coverage_1=len(u)/len(c) if c else None,
        coverage_2=sum(da[k]>0 for k in u)/sum(v>0 for v in da.values()) if any(v>0 for v in da.values()) else None,
        coverage_3=total/den if den else None,coverage_3_prime=total/sum(da.values()) if sum(da.values()) else None,
        all_covered_lines=sum(v>0 for v in da.values()),all_DA=sum(da.values()),
        n_eff=neff,n_eff_branch="undefined_no_eligible_reference_weight" if neff is None else ("below_3" if neff<3 else "at_least_3"),
        K=K,K_interpretation="undefined" if K is None else ("descriptive_only" if K<50 else "not_below_50"),
        loss_buckets=[dict(reasons=list(k),**v) for k,v in sorted(buckets.items())],
        loss_equation=dict(R_C=den,R_U=total,sum_loss=loss,difference=den-total-loss,assertion_passed=True))

def main(obj):
    refs,da,rlines,inv,checks,lp=data(obj);bi=bridge_inventory(obj)
    dest=OUT/(obj+"-static");dest.mkdir(exist_ok=False)
    dbpath=TEMP/(obj+"-static.sqlite");assert not dbpath.exists()
    db=sqlite3.connect(dbpath)
    db.executescript("PRAGMA cache_size=-65536; PRAGMA temp_store=FILE; CREATE TABLE kv(k TEXT,v TEXT,ref INTEGER,file TEXT,line INTEGER,disc INTEGER,status TEXT,n INTEGER,first INTEGER,PRIMARY KEY(k,v)); CREATE TABLE special(kind TEXT,addr INTEGER,size INTEGER,file TEXT,name TEXT,PRIMARY KEY(kind,addr));")
    owners=collections.defaultdict(set)
    for i,r in enumerate(refs):
        if r["fnda"]>0:
            for k in rlines[i]:owners[k].add(i)
    c=set(owners);why=collections.defaultdict(set)
    for k,ids in owners.items():
        if len(ids)>1:why[k].add("reference_ambiguity")
    amb=set();corresponded=set()
    for d,ch in checks.items():
        if ch["conclusion"]=="identity_ambiguous":amb.update(ch["candidate_ids"])
        elif ch["conclusion"] in ("reference_executed","reference_unexecuted"):corresponded.update(ch["candidate_ids"])
    # Ruling2 functions are all unexecuted and therefore cannot fill executed-reference gaps.
    unmatched={i for i,r in enumerate(refs) if r["fnda"]>0 and i not in corresponded}
    def exclude(ids,reason):
        for i in ids:
            for k in rlines[i]&c:why[k].add(reason)
    exclude(amb,"identity_ambiguous");exclude(unmatched,"unmatched_in_elf")
    groups={r["name"]:r for r in rows(OUT/(obj+"-groups"),"groups-*.csv")}
    stats=collections.Counter();failed=[];mapped=collections.Counter()
    with (TEMP/(obj+"-map.jsonl")).open() as raw:
        for line in raw:
            rec=json.loads(line)
            if rec["kind"]=="boundary_unavailable":
                ids=json.loads(groups[rec["name"]]["reference_ids"])
                exclude(ids,"boundary_unavailable");failed.append(rec);continue
            if rec["kind"]=="group":stats["enumerated_groups"]+=1;continue
            assert rec["kind"]=="instruction",rec
            stats["instruction_occurrences"]+=1
            ds=rec["dies_leaf_to_root"];fs=rec["frames_leaf_to_root"]
            if not ds:stats["no_DWARF_leaf"]+=1;continue
            # Resolve the exact leaf DIE; a missing closed conclusion is never downgraded.
            assert ds[0] in inv,(obj,rec)
            leaf=inv[ds[0]];category=leaf["category"]
            if category in ("system_header_no_reference","macro_generated_function"):
                db.execute("INSERT OR IGNORE INTO special VALUES(?,?,?,?,?)",
                    (category,rec["address"],rec["size"],norm_file(leaf["decl_file"]),leaf["raw_name"]))
            stats["line_before_start_frames"]+=sum(0<f["line"]<f["start_line"] for f in fs)
            key=profile_key(fs)
            if key is None:
                stats["leaf_line_zero" if not fs or fs[0]["line"]==0 else "nonleaf_line_zero_or_invalid"]+=1
                continue
            # If an invalid inner name truncated the stack, the surviving frame is the leaf.
            index=len(fs)-len(key)
            assert index<len(ds),(rec,"frame/DIE depth mismatch")
            d=ds[index];identity=inv[d]
            f=fs[index]
            assert bi[d]["name"]==f["name"],(obj,rec,bi[d])
            ch=checks.get(d,{})
            ids=ch.get("candidate_ids",[])
            status=identity["conclusion"]
            if status in ("reference_executed","reference_unexecuted") and identity["category"]!="macro_generated_function":
                assert len(ids)==1,(identity,ch)
                ref=ids[0];source=["reference",ref]
            elif status=="identity_ambiguous":
                assert ids;ref=-1;source=["identity_ambiguous",ids]
            else:
                ref=-1;source=[identity["category"],norm_file(identity["decl_file"]),norm_name(identity["raw_name"]),int(identity["decl_line"] or 0)]
            file=norm_file(f["file"]);n=f["line"];disc=f["base_discriminator"]
            k=json.dumps(key,separators=(",",":"))
            v=json.dumps([source,file,n,disc],separators=(",",":"))
            db.execute("INSERT INTO kv VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(k,v) DO UPDATE SET n=n+1,first=min(first,excluded.first)",
                       (k,v,ref,file,n,disc,identity["category"],1,rec["address"]))
            stats["key_instruction_occurrences"]+=1;mapped[identity["category"]]+=1
            if stats["instruction_occurrences"]%10000==0:db.commit()
    db.commit()
    db.execute("CREATE INDEX key_index ON kv(k)");db.commit()
    ambiguous_keys={r[0] for r in db.execute("SELECT k FROM kv GROUP BY k HAVING count(*)>1")}
    affected=set()
    for k in ambiguous_keys:
        for f,n in db.execute("SELECT file,line FROM kv WHERE k=?",(k,)):
            affected.add((f,n))
            if (f,n) in c:why[(f,n)].add("key_ambiguity")
    has_key=set()
    for k,ref,f,n in db.execute("SELECT k,ref,file,line FROM kv WHERE ref>=0"):
        if k not in ambiguous_keys and ref in owners.get((f,n),set()):has_key.add((f,n))
    for k in c-has_key:why[k].add("no_key_line")
    u,weights,summary=measures(da,owners,why,has_key)
    gates={}
    for reason in ("identity_ambiguous","unmatched_in_elf","boundary_unavailable"):
        ks={k for k in c if reason in why[k]};mass=sum(da[k] for k in ks)
        gates[reason]=dict(lines=len(ks),DA=mass,denominator=summary["R_C"],
                           ratio=mass/summary["R_C"] if summary["R_C"] else None,
                           exceeds_one_percent=100*mass>summary["R_C"])
    blockers=[k for k,v in gates.items() if v["exceeds_one_percent"]]
    if not summary["R_C"]:blockers.append("zero_reference_denominator")
    elif 2*summary["R_U"]<summary["R_C"]:blockers.append("coverage_3_below_50_percent")
    summary.update(object=obj,registration_status="不可登记" if blockers else "可登记",
        registration_reasons=blockers,coverage_3_tier="undefined" if not summary["R_C"] else
        ("<50%" if 2*summary["R_U"]<summary["R_C"] else ("50–80%" if 5*summary["R_U"]<4*summary["R_C"] else "≥80%")),
        gates=gates,body_fraction_4=BODY_NOTE,
        static_4=dict(ambiguous_keys=len(ambiguous_keys),affected_lines=len(affected),
                      affected_C_lines=len(affected&c),identity_ambiguous_reference_functions=len(amb)),
        mapping=dict(stats=stats,categories=mapped,failed_groups=len(failed)),
        unmatched_reference_functions=sorted(unmatched),boundary_failures=failed)
    special=[]
    for kind,f,name,n,bytes_ in db.execute("SELECT kind,file,name,count(*),sum(size) FROM special GROUP BY kind,file,name ORDER BY kind,file,name"):
        special.append(dict(kind=kind,file=f,name=name,addresses=n,code_bytes=bytes_))
    summary["static_special_code"]=dict(
        by_kind={kind:dict(addresses=sum(x["addresses"] for x in special if x["kind"]==kind),
                           code_bytes=sum(x["code_bytes"] for x in special if x["kind"]==kind))
                 for kind in ("system_header_no_reference","macro_generated_function")},
        interpretation="unique proven instruction starts within mapping range, leaf DWARF identity; byte sum of instruction lengths")
    parts=[]
    parts+=tables(dest,"U",["file","line","DA","reference_id"],([*k,da[k],next(iter(owners[k]))] for k in sorted(u)))
    parts+=tables(dest,"exclusions",["file","line","DA","reference_ids","reasons"],([*k,da[k],sorted(owners[k]),sorted(why[k])] for k in sorted(c-u)))
    parts+=tables(dest,"weights",list(weights[0]) if weights else ["reference_id"],([w[k] for k in weights[0]] for w in weights))
    parts+=tables(dest,"special-code",["kind","file","name","addresses","code_bytes"],([s[k] for k in ["kind","file","name","addresses","code_bytes"]] for s in special))
    parts+=tables(dest,"mapping",["key","value","reference_id","file","line","discriminator","category","instruction_occurrences","first_address"],
                  db.execute("SELECT * FROM kv ORDER BY k,v"))
    dump(dest/"summary.json",summary)
    dump(dest/"index.json",dict(parts=parts,summary_sha256=sha(dest/"summary.json"),
        map_input=str(TEMP/(obj+"-map.jsonl")),map_input_sha256=sha(TEMP/(obj+"-map.jsonl")),
        lcov=str(lp),lcov_sha256=sha(lp),command=["python3","tools/profgen_eval/static_coverage_gate.py",obj]))
    db.close();print(json.dumps(summary,ensure_ascii=False),flush=True)
    return 0

if __name__=="__main__":raise SystemExit(main(sys.argv[1]))
