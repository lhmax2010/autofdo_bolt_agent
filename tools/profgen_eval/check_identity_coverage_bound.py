"""Reference-only necessary coverage bound; never claims to have generated U.

Every identity-ambiguous candidate line is excluded by v1.5. Thus
sum(R(U)) <= sum(R(C minus ambiguous)). A failing upper bound proves ③<50%.
"""
import collections,json,bisect
from pathlib import Path
from apply_header_ruling import rows,norm_file
from coverage_reference import parse_lcov
from pack_static_evidence import tables
from run_scoped import WORK,sha
BASE=WORK/"docs/profgen/eval/prep/evidence"
GATE=BASE/"ruling2/supplement3/rev1/identity-gate"
OUT=GATE/"coverage-bound-v3"

def gate_bound(den, loss):
    if den < 0 or not 0 <= loss <= den:
        raise ValueError("invalid reference mass")
    return dict(maximum_possible_R_U=den-loss,
                coverage_3_upper_bound=(den-loss)/den if den else None,
                proves_coverage_3_below_half=bool(den and 2*(den-loss)<den))

def main():
    OUT.mkdir(exist_ok=True);results=[]
    summaries=json.loads((GATE/"ordinary-v2/ordinary-summary.json").read_text())
    assert len(summaries)==4 and all(s["unresolved"]==0 for s in summaries)
    for obj in [s["object"] for s in summaries]:
        cov=BASE/(obj+"-coverage-tables");meta=json.loads((cov/"index.json").read_text())
        lpath=WORK/meta["lcov"]
        if not lpath.exists():
            partindex=lpath.with_name("stdout.parts.json")
            archived=json.loads(partindex.read_text())
            reconstructed=WORK/"temp/prep-identity-gate"/(obj+"-reference.lcov")
            with reconstructed.open("wb") as target:
                for part in archived["parts"]:
                    pp=WORK/part["path"];assert sha(pp)==part["sha256"]
                    target.write(pp.read_bytes())
            assert sha(reconstructed)==archived["sha256"]
            lpath=reconstructed
        lcov=parse_lcov(lpath)
        da={(norm_file(f),int(n)):v for f,r in lcov.items() for n,v in r["da"].items()}
        perfile=collections.defaultdict(list)
        for file,line in da:perfile[file].append(line)
        for lines in perfile.values():lines.sort()
        refs=list(rows(cov,"merged-functions-*.csv"))
        ambiguous=set();reason_by_ref=collections.defaultdict(set)
        for row in rows(GATE/"ordinary-v2"/(obj+"-ordinary"),"checks-*.csv"):
            if row["conclusion"]=="identity_ambiguous":
                for n in json.loads(row["candidate_ids"]):
                    ambiguous.add(n);reason_by_ref[n].update(json.loads(row["reasons"]))
        c=set();excluded=set();why=collections.defaultdict(set)
        for i,r in enumerate(refs):
            file=norm_file(r["file"]);lines=perfile[file]
            a=bisect.bisect_left(lines,int(r["start"]));b=bisect.bisect_right(lines,int(r["end"]))
            keys={(file,line) for line in lines[a:b]}
            if int(r["fnda"])>0:c.update(keys)
            if i in ambiguous:
                excluded.update(keys)
                for k in keys:why[k].update(reason_by_ref[i])
        excluded &= c
        den=sum(da[k] for k in c);loss=sum(da[k] for k in excluded);upper=den-loss
        bucket=collections.Counter()
        for k in excluded:bucket[tuple(sorted(why[k]))]+=da[k]
        dest=OUT/obj;dest.mkdir(exist_ok=True)
        parts=tables(dest,"reference-domain",["file","line","DA","identity_ambiguous","reasons"],
            ([*k,da[k],k in excluded,sorted(why[k])] for k in sorted(c)))
        (dest/"index.json").write_text(json.dumps(dict(parts=parts,lcov=str(lpath),lcov_sha256=sha(lpath)),indent=2)+"\n")
        r=dict(object=obj,C_lines=len(c),R_C=den,identity_ambiguous_lines=len(excluded),
            identity_ambiguous_DA=loss,identity_ambiguous_fraction=loss/den if den else None,
            mandatory_loss_buckets=[dict(reasons=list(k),DA=v) for k,v in sorted(bucket.items())],
            **gate_bound(den,loss),
            coverage_3_actual=None,U_generated=False,identity_ambiguity_over_one_percent=loss*100>den,
            equation="U subset of C minus identity_ambiguous; sum buckets = mandatory loss only, not final R(C)-R(U)")
        assert sum(bucket.values())==loss
        results.append(r);print(json.dumps(r),flush=True)
        (OUT/"summary.json").write_text(json.dumps(results,indent=2)+"\n")
        if r["proves_coverage_3_below_half"]:
            print("STOP: mathematically proven ③<50%, without constructing or claiming exact U",flush=True)
            return 2
    return 0

if __name__=="__main__":raise SystemExit(main())
