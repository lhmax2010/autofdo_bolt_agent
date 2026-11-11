"""Rulings3 and 4 revision1; old collectors and rule paths stay unchanged."""
from apply_header_ruling import norm_file

def code_line_domain(old_C,rows,executed_C_DIEs):
    witnesses={};executed=set(executed_C_DIEs)
    for r in rows:
        if r["end_sequence"] or not r["file_resolved"] or r["line"]==0:continue
        matches=set(r["dies_leaf_to_root"]) & executed
        if matches:
            k=(norm_file(r["file"]),r["line"])
            if k in old_C:witnesses.setdefault(k,dict(row=r,executed_C_DIEs=sorted(matches)))
    return set(witnesses),witnesses

def instance_check(instance,candidates,c_definitions):
    if len(candidates)!=1:
        return dict(definition_ok=False,line_status="not_checked",reasons=["multiple_reference_candidates" if candidates else "reference_candidate_missing"],lines=[])
    file=norm_file(instance["decl_file"]);decl=int(instance["decl_line"])
    positions={(norm_file(d["decl_file"]),int(d["decl_line"])) for d in c_definitions if d.get("decl_file") and d.get("decl_line")}
    definition_ok=positions=={(file,decl)}
    reasons=[] if definition_ok else ["definition_identity_unproven" if not positions else "definition_declaration_conflict"]
    positive=[r for r in instance["leaf_lines"] if r["line"]>0]
    leaf={r["line"] for r in positive if norm_file(r["file"])==file}
    call={r["call_line"] for r in instance["direct_inline_calls"] if r["call_file_resolved"] and r["call_line_present"] and r["call_line"]>0 and norm_file(r["call_file"])==file}
    combined=leaf|call;c=candidates[0];lower=min(decl,int(c["start"]));upper=int(c["end"])
    has_key=instance["accepted_key_instructions"]>0
    if not has_key:
        category=("a_self_and_descendants_zero" if not positive and not instance["descendant_nonzero_leaf"]
                  else ("e_nonleaf_zero_rejected" if not positive and instance["descendant_nonzero_leaf"]
                        else "own_positive_leaf_but_full_context_rejected"))
        if any(n<lower or n>upper for n in combined):
            status="outside";reasons.append("leaf_line_outside_range")
        elif any(norm_file(r["file"])!=file for r in positive):
            status="leaf_other_file";reasons.append("leaf_lines_in_other_files_no_key_exemption_denied")
        else:status="no_key_instance"
    elif positive and not leaf:
        status="leaf_other_file";category="d_self_leaf_other_file"
        reasons.append("leaf_lines_only_in_other_files")
    elif combined:
        status="pass" if all(lower<=n<=upper for n in combined) else "outside"
        category="own_leaf_in_decl_file" if positive else "b_descendant_key_call_in_decl_file"
        if status=="outside":reasons.append("leaf_line_outside_range")
    else:
        status="empty_with_keys";category="c_descendant_key_call_not_in_decl_file"
        reasons.append("no_eligible_child_call_line")
    return dict(definition_ok=definition_ok,accepted_key_instructions=instance["accepted_key_instructions"],line_status=status,instance_class=category,reasons=reasons,
        leaf_lines=sorted(leaf),child_call_lines=sorted(call),lines=sorted(combined),lower=lower,upper=upper)

def group_check(results,candidates):
    if len(candidates)!=1:
        return dict(conclusion="identity_ambiguous",reasons=["multiple_reference_candidates" if candidates else "reference_candidate_missing"],all_no_key=False,failed_instances=len(results),instances=len(results),failure_extent="all_instances")
    bad=[r for r in results if not r["definition_ok"] or r["line_status"] not in ("pass","no_key_instance")]
    active=[r for r in results if r["line_status"]!="no_key_instance"]
    assert results
    ok=not bad and (not active or any(r["line_status"]=="pass" for r in active))
    return dict(conclusion=("reference_executed" if int(candidates[0]["fnda"])>0 else "reference_unexecuted") if ok else "identity_ambiguous",
        reasons=sorted({reason for r in bad for reason in r["reasons"]}),all_no_key=not active,
        failed_instances=len(bad),instances=len(results),
        failure_extent="none" if not bad else ("all_instances" if len(bad)==len(results) else "partial_instances"))
