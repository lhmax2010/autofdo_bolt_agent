"""v1.8 static diagnostic tables; no registered quality conclusion is emitted."""
import collections,json,sqlite3,sys
from pathlib import Path
from v18_domain import OUT,BASE,dump
from run_scoped import WORK,sha
from ruling3_domain import reference
from ruling34_static import measures,BODY_NOTE
from apply_header_ruling import rows,norm_file,norm_name
from pack_static_evidence import tables
from v18_rules import (ledger,coverage_views,DOMAIN_EXPLANATION,domain_sha,
                       registration,validate_conclusion)
PREVIOUS=BASE/"identity-gate/v17-recompute"

OLD=BASE/"identity-gate/ruling3-4"
V16=BASE/"identity-gate/ruling3-rev1"
def main(obj):
 audit=json.loads((PREVIOUS/(obj+"-key-audit/summary.json")).read_text())
 assert audit["identity_results_unchanged"] and audit["byte_identical_to_old"]
 refs,da,rlines,owners,lp=reference(obj);c0=set(owners)
 di=json.loads((OUT/(obj+"-domain/index.json")).read_text())
 c={(r["file"],int(r["line"])) for r in rows(OUT/(obj+"-domain"),"lines-*.csv")}
 unknown={(r["file"],int(r["line"])) for r in rows(OUT/(obj+"-domain"),"domain-unresolved-*.csv")}
 assert domain_sha(c)==di["C_sha256"]
 original=OLD/(obj+"-static")
 why=collections.defaultdict(set)
 for r in rows(original,"old-C-exclusions-*.csv"):
  why[(r["file"],int(r["line"]))]=set(json.loads(r["reasons"]))-{"code_free_line"}
 has_key={k for k in c0 if "no_key_line" not in why[k]}
 macros=[];macro_lines=set()
 if obj.startswith("ffmpeg"):
  source=BASE/"ruling2"/(obj+"-macro-audit.json")
  macros=json.loads(source.read_text())
  # Map reference records by their compiler PGO name, never by sampled keys.
  for a in macros:
   hits=[r for r in refs if any(x.get("name")==a["pgo_name"] for x in r["copies"] if isinstance(x,dict))]
   if a["fnda"]>0:
    assert hits,"missing macro reference record"
    for r in hits:macro_lines.update(rlines[r["id"]])
 # The present immutable inputs have FNDA=0 for all 34 macro functions;
 # positive FNDA and overlapping reasons are covered independently in fixtures.
 assert not any(a["fnda"]>0 for a in macros)
 u,rs,cl,ol=ledger(c0,c,da,why,macro_lines,unknown)
 mu,weights,s=measures(da,{k:owners[k] for k in c},rs,has_key)
 assert u==mu
 classes={(r["file"],int(r["line"])):r["category"] for r in rows(OUT/(obj+"-classification"),"lines-*.csv")}
 views=coverage_views(c0,c,u,da,classes)
 gates={}
 for reason in ("identity_ambiguous","unmatched_in_elf","boundary_unavailable"):
  ks={k for k in c if reason in rs[k]};mass=sum(da[k] for k in ks)
  gates[reason]=dict(lines=len(ks),DA=mass,denominator=s["R_C"],
     ratio=mass/s["R_C"] if s["R_C"] else None,exceeds_one_percent=100*mass>s["R_C"])
 blockers=[k for k,v in gates.items() if v["exceeds_one_percent"]]
 if not s["R_C"]:blockers.append("zero_reference_denominator")
 elif 2*s["R_U"]<s["R_C"]:blockers.append("coverage_3_below_50_percent")
 status,blockers=registration(len(unknown),gates,s["R_U"],s["R_C"])
 prior=json.loads((V16/(obj+"-static/ruling3-rev1/summary.json")).read_text())
 oldc={(r["file"],int(r["line"])) for r in rows(V16/(obj+"-domain"),"lines-*.csv")}
 base=json.loads((original/"summary.json").read_text())
 s.update(object=obj,rule="v1.8 O.2.3",status=status,domain_unresolved_lines=len(unknown),artifact_kind="static_diagnostic_not_registration",**views,
   evaluation_domain=DOMAIN_EXPLANATION,ledger_C_to_U=cl,ledger_C0_to_U=ol,
   domain_unresolved=dict(lines=len(unknown),DA=sum(da[k] for k in unknown)),
   registration_status=("domain_evidence_incomplete" if status=="domain_evidence_incomplete" else
      ("不可登记" if blockers else "可登记（仅表内；修订3未登记）")),
   registration_reasons=blockers,coverage_3_tier="<50%" if 2*s["R_U"]<s["R_C"] else ("50–80%" if 5*s["R_U"]<4*s["R_C"] else "≥80%"),
   gates=gates,body_fraction_4=BODY_NOTE,
   static_4=base["static_4"],static_special_code=base["static_special_code"],
   actual_executed_macro_functions=sum(a["fnda"]>0 for a in macros),
   C_sha256=di["C_sha256"],C0_lines=len(c0),R_C0=sum(da[k] for k in c0))
 dbpath=WORK/"temp/prep-ruling3-4"/(obj+"-static.sqlite")
 db=sqlite3.connect(dbpath.as_uri()+"?mode=ro",uri=True)
 keylines={(f,n) for f,n in db.execute("SELECT DISTINCT file,line FROM kv")};db.close()
 outside=(keylines&c0)-c
 s["S_key_C0_lines_outside_C"]=dict(lines=len(outside),DA=sum(da[k] for k in outside))
 assert not outside,"effective-query domain missed an accepted key line in C0"
 dest=OUT/(obj+"-static");dest.mkdir()
 parts=tables(dest,"U",["file","line","DA","reference_id"],([*k,da[k],next(iter(owners[k]))] for k in sorted(u)))
 parts+=tables(dest,"C-exclusions",["file","line","DA","reasons"],([*k,da[k],sorted(rs[k])] for k in sorted(c-u)))
 parts+=tables(dest,"C0-exclusions",["file","line","DA","reasons"],([*k,da[k],sorted(rs[k])] for k in sorted(c0-u)))
 parts+=tables(dest,"weights",list(weights[0]) if weights else ["reference_id"],([w[k] for k in weights[0]] for w in weights))
 parts+=tables(dest,"added-C",["file","line","DA","in_U","reasons"],([*k,da[k],k in u,sorted(rs[k])] for k in sorted(c-oldc)))
 parts+=tables(dest,"removed-C",["file","line","DA"],([*k,da[k]] for k in sorted(oldc-c)))
 s["C_changes"]=dict(added_lines=len(c-oldc),added_DA=sum(da[k] for k in c-oldc),
   removed_lines=len(oldc-c),removed_DA=sum(da[k] for k in oldc-c),
   added_U_lines=len((c-oldc)&u),added_U_DA=sum(da[k] for k in (c-oldc)&u))
 # v1.6 three-view figures are reconstructed from the preserved v2 description,
 # without adding v1.7 callsite classification or changing the old results.
 oldclasses={(r["file"],int(r["line"])):r["category"] for r in rows(BASE/"identity-gate/code-free-v2"/(obj+"-classification"),"lines-*.csv")}
 oldu={(r["file"],int(r["line"])) for r in rows(V16/(obj+"-static/ruling3-rev1"),"U-*.csv")}
 oldviews=coverage_views(c0,oldc,oldu,da,oldclasses)
 prior=dict(prior,**oldviews)
 previous=json.loads((PREVIOUS/(obj+"-static/summary.json")).read_text())
 # Exact equality of every pre-existing numerical/static result, including
 # both ledgers, all gates, ratios, weights, n_eff's explicit branch and K.
 exempt={"rule","evaluation_domain","registration_status"}
 differences={k:dict(v17=v,v18=s.get(k)) for k,v in previous.items()
              if k not in exempt and s.get(k)!=v}
 dump(dest/"comparison.json",dict(v17=previous,v18=s,differences=differences))
 assert not differences,"v1.8 static numbers differ: stop and report"
 dump(dest/"summary.json",s)
 for prefix in ("U","weights","C-exclusions","C0-exclusions"):
  old=list(rows(PREVIOUS/(obj+"-static"),prefix+"-*.csv"))
  new=list(rows(dest,prefix+"-*.csv"))
  assert old==new, "v1.8 line/weight/ledger changes: "+prefix
 # Seal a candidate table for gate acceptance only. It is NOT amendment 3,
 # and no quality conclusion about a real RUN is generated.
 payload={k:s[k] for k in ("object","status","domain_unresolved_lines","evaluation_domain",
      "coverage_3_views","coverage_3_prime","code_bearing","nonduplicated_outside")}
 candidate=dest/"candidate-table.json"
 dump(candidate,dict(kind="pre_registration_static_candidate",objects={obj:payload}))
 accepted=validate_conclusion(payload,candidate,sha(candidate),obj)
 dump(dest/"gate-acceptance.json",dict(accepted=accepted,registered=False,
    candidate=str(candidate),candidate_sha256=sha(candidate),
    actual_quality_conclusion_emitted=False,profile_read=False,
    inlined_call_site=json.loads((OUT/(obj+"-classification/summary.json")).read_text())["categories"]["inlined_call_site"]))
 dump(dest/"index.json",dict(parts=parts,
   reused_static_inputs=[dict(path=str(p),sha256=sha(p)) for p in
    [*original.glob("old-C-exclusions-*.csv"),original/"summary.json",dbpath,lp,
     PREVIOUS/(obj+"-key-audit/summary.json"),OUT/(obj+"-classification/summary.json")]],
   mapping_range_inputs_separate_from_C=dict(
       selection=str(WORK/"temp/prep-static-gate"/(obj+"-selected-groups.json")),
       selection_sha256=sha(WORK/"temp/prep-static-gate"/(obj+"-selected-groups.json")),
       static_mapping=json.loads((original/"index.json").read_text())["map_input"],
       static_mapping_sha256=json.loads((original/"index.json").read_text())["map_input_sha256"],
       static_mapping_provenance=str(original/"index.json"),
       static_mapping_provenance_sha256=sha(original/"index.json")),
   domain_input_manifest=str(OUT/(obj+"-domain/index.json")),
   mapping_input_manifest=str(PREVIOUS/(obj+"-key-audit/summary.json")),
   summary_sha256=sha(dest/"summary.json"),comparison_sha256=sha(dest/"comparison.json")))
 print(json.dumps({k:s[k] for k in ("object","C_lines","R_C","U_lines","R_U","coverage_3_views","n_eff","K","registration_status","C_changes")},ensure_ascii=False))
if __name__=="__main__":main(sys.argv[1])
