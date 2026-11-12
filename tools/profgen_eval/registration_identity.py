"""Q.5 #16 complete inventory gate and external-CU positive evidence."""
from apply_header_ruling import norm_file,norm_name
from ordinary_identity_rule import classify_ordinary
from registration_mapping_checks import validate_correspondence


def candidates_for(row,refs):
    return [r for r in refs if norm_file(r["file"])==norm_file(row["decl_file"]) and
            r["name"]==norm_name(row["name"])]


def external_conclusion(row,candidates,coverage_files,registered):
    if candidates:return None
    cu=row.get("cu_name");prod=row.get("producer")
    if not cu or not prod or not row.get("path_normalized") or not row.get("producer_parsed"):return None
    if cu in coverage_files or prod=="clang version 22.1.8":return None
    proof=registered.get((cu,prod))
    if not proof or not proof.get("link_source_verified") or not proof.get("source_sha256"):return None
    return "not_instrumented"


def complete_gate(inventory,conclusions,variant_verified=True):
    if not variant_verified:raise ValueError("variant_evidence_mismatch")
    ids={r["id"] for r in inventory}
    if len(ids)!=len(inventory) or set(conclusions)!=ids:raise ValueError("inventory_not_complete")
    validate_correspondence(conclusions.values())
    return True
