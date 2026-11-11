"""Reference-only mass audit and largest mandatory exclusions (no sample inputs)."""
import csv,json,collections
from pathlib import Path
from apply_header_ruling import rows,norm_file
from coverage_reference import parse_lcov
from run_scoped import WORK,sha
BASE=WORK/"docs/profgen/eval/prep/evidence"
GATE=BASE/"ruling2/supplement3/rev1/identity-gate"
OUT=GATE/"mass-audit.json"
def main():
    results=[]
    for obj in ("ffmpeg-thumb","ffmpeg-a32"):
        src=GATE/"coverage-bound-v3"/obj
        data=list(rows(src,"reference-domain-*.csv"))
        C=sum(int(r["DA"]) for r in data)
        lost=[r for r in data if r["identity_ambiguous"] in ("True","true")]
        loss=sum(int(r["DA"]) for r in lost)
        top=sorted(lost,key=lambda r:(-int(r["DA"]),r["file"],int(r["line"])))[:20]
        lcov=WORK/"temp/prep-identity-gate"/(obj+"-reference.lcov")
        all_da=sum(v for r in parse_lcov(lcov).values() for v in r["da"].values())
        bucket=collections.Counter()
        for r in lost:bucket[tuple(json.loads(r["reasons"]))]+=int(r["DA"])
        summary=next(r for r in json.loads((GATE/"coverage-bound-v3/summary.json").read_text()) if r["object"]==obj)
        assert C==summary["R_C"] and loss==summary["identity_ambiguous_DA"]
        assert sum(bucket.values())==loss
        result=dict(object=obj,R_C=C,mandatory_DA=loss,all_exported_DA=all_da,
                    ratio_over_all_exported_DA=loss/all_da,
                    top_excluded_lines=top,lcov_sha256=sha(lcov),
                    note="Independent CSV resummation; all-exported DA is a conservative upper bound for the denominator C, not actual C.")
        results.append(result)
        print(json.dumps({k:v for k,v in result.items() if k!="top_excluded_lines"}),flush=True)
    OUT.write_text(json.dumps(results,indent=2)+"\n")
if __name__=="__main__":main()
