"""Q.5 #11 synthetic-validated performance registration checks; no execution."""
import math
import statistics

GROUPS = {"G1":(True,"none"),"G2":(False,"none"),
          "G3":(False,"entry-estimate"),"G4":(True,"entry-estimate")}


def budget(cv=None):
    """v1.8 5.9.5: four significant figures BEFORE substitution."""
    if cv is None or not isinstance(cv,(int,float)) or not math.isfinite(cv):
        return dict(N=40,source="pretrial_unavailable_budget_cap",cv=None)
    if cv<0: raise ValueError("negative_CV")
    cv=float(format(cv,".4g"))
    n=min(40,max(10,math.ceil(2*(1.96*1.2533*cv/0.005)**2)))
    return dict(N=n,source="G0_untrimmed_sample_CV",cv=cv)


def pretrial_budget(rows, conditions):
    required=("new_image","cooling_installed","sampler_enabled","conditions_recorded")
    if not all(conditions.get(k) is True for k in required): return budget()
    values=[r["seconds"] for r in rows if not r.get("warmup",False)]
    if len(values)<10 or any(not isinstance(x,(int,float)) or not math.isfinite(x) or x<=0 for x in values): return budget()
    # Deliberately do not filter outlier or eligibility flags.
    return budget(statistics.stdev(values)/statistics.mean(values))


def validate_matrix(matrix):
    """Validate every explicit registered group; small matrices list omissions."""
    seen=set(); coverage=set()
    for r in matrix["rows"]:
        identity=r["id"]
        if identity in seen: raise ValueError("duplicate_matrix_id")
        seen.add(identity)
        g=r["group"]
        if g in ("G6","G7"):
            if not matrix.get("probe_admitted"): raise ValueError("probe_not_admitted")
            continue
        if g=="G0":
            if r.get("profile") is not None: raise ValueError("G0_profile")
            continue
        if g=="G5":
            if r.get("instrumentation")!="IR" or not r.get("profile") or r.get("disable_preinline"):
                raise ValueError("G5_requires_normal_IR_PGO")
            continue
        if g not in GROUPS: raise ValueError("unknown_group")
        profi,head=GROUPS[g]
        if r["profi"] is not profi or r["head"]!=head: raise ValueError("group_parameters")
        if r["zero_fill"] not in ("none","sampled-functions"): raise ValueError("zero_fill")
        if r["aggregation"] not in ("sum","max","avg") or r["skid"] not in ("none","prev-inst"): raise ValueError("generation_parameters")
        if r["weight"] not in ("sample","period") or not r.get("profile"): raise ValueError("profile_parameters")
        if not r.get("driver_profi_disabled") or not isinstance(r.get("stale"),bool) or not isinstance(r.get("salvage_unused"),bool): raise ValueError("explicit_consumer_parameters")
        if r.get("stale_only_comparison") and r["salvage_unused"]: raise ValueError("stale_not_isolated")
        if r.get("symbol_list"): raise ValueError("symbol_list_forbidden")
        if r.get("lto"):
            expected={k:r[k] for k in ("profile","profi","stale","salvage_unused")}
            if r.get("link")!=expected: raise ValueError("LTO_link_mismatch")
        coverage.add((r["aggregation"],r["skid"],g,r["zero_fill"]))
    required={(a,s,g,z) for a,s in matrix["shortlist"] for g in GROUPS for z in ("none","sampled-functions")}
    missing=required-coverage
    if coverage-required: raise ValueError("unregistered_combination")
    omitted={tuple(x) for x in matrix.get("unassessed_interactions",[])}
    if missing and (missing!=omitted or not matrix.get("fixed_parameters")): raise ValueError("unexplained_small_matrix")
    return dict(missing=sorted(missing),zero_fill_default_verified=not missing)


def claim_zero_fill_default(matrix):
    if not validate_matrix(matrix)["zero_fill_default_verified"]: raise ValueError("zero_fill_control_missing")
    return True


def performance_policy(quality_equivalence_enabled):
    # Parameter intentionally has no effect on performance rules.
    return dict(statistic="relative_difference_of_medians",epsilon=0.01,
                interval="independent_percentile_bootstrap_95",stop="registered_N_no_extension")


def accept_formal_round(existing, row, registered_n):
    if isinstance(registered_n,bool) or not isinstance(registered_n,int) or not 10<=registered_n<=40: raise ValueError("invalid_registered_N")
    if row.get("stage")!="formal" or row.get("warmup"): raise ValueError("pretrial_or_warmup_not_formal")
    if row["id"] in {r["id"] for r in existing}: raise ValueError("duplicate_round")
    if any(r.get("stage")!="formal" or r.get("warmup") for r in existing): raise ValueError("polluted_formal_rounds")
    if sum(r["group"]==row["group"] for r in existing)>=registered_n: raise ValueError("registered_N_exhausted")
    return existing+[row]


def validate_performance_result(result,registered_n):
    policy=performance_policy(False)
    if any(result.get(k)!=v for k,v in policy.items()): raise ValueError("quality_performance_rule_mixing")
    if result.get("N")!=registered_n or result.get("extend_for_precision"): raise ValueError("registered_N_changed")
    if result.get("completed")!=registered_n: return "incomplete"
    interval=result["interval_bounds"]
    if len(interval)!=2 or any(not math.isfinite(x) for x in interval) or interval[0]>interval[1]: raise ValueError("invalid_interval")
    return "equivalent" if -0.01<=interval[0]<=interval[1]<=0.01 else "insufficient_evidence"
