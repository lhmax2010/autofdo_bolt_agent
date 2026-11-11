"""v1.5 single/multiple candidate identity rule; no sample input or heuristics."""
from apply_header_ruling import norm_file,norm_name


def classify_ordinary(s,candidates,c_definitions,leaf_rows,variant_verified=True):
    if not variant_verified:return dict(conclusion=None,reasons=["variant_evidence_mismatch"])
    if not candidates:return dict(conclusion=None,reasons=["reference_candidate_missing"])
    reasons=[]
    lines=sorted({r["line"] for r in leaf_rows if r["line"]>0 and norm_file(r["file"])==norm_file(s["decl_file"])})
    if len(candidates)>1:
        reasons=["multiple_reference_candidates"]
    else:
        c=candidates[0]
        positions={(norm_file(d["decl_file"]),int(d["decl_line"])) for d in c_definitions if d.get("decl_file") and d.get("decl_line")}
        expected=(norm_file(s["decl_file"]),int(s["decl_line"]))
        if positions!={expected}:reasons.append("definition_identity_unproven" if not positions else "definition_declaration_conflict")
        lower=min(int(s["decl_line"]),int(c["start"]))
        if not lines:reasons.append("empty_leaf_line_set")
        elif any(n<lower or n>int(c["end"]) for n in lines):reasons.append("leaf_line_outside_range")
    # v1.5 explicitly allows identity_ambiguous for failed single checks.
    return dict(conclusion="identity_ambiguous" if reasons else
                ("reference_executed" if int(candidates[0]["fnda"])>0 else "reference_unexecuted"),
                reasons=reasons,leaf_lines=lines,
                candidate_executed=any(int(c["fnda"])>0 for c in candidates))
