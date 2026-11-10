"""Ruling 2: explicit positive evidence; never strip TU paths or unique suffixes."""
import posixpath

def norm(path):
    return posixpath.normpath(path) if path else None

def classify_macro(record):
    reasons = []
    code_files = {norm(f) for f in record.get("code_files", [])}
    decl = norm(record.get("s_decl_file"))
    if decl in code_files:
        return {"conclusion": None, "route": "original_correspondence_rules",
                "reasons": ["code_region_in_decl_file"]}
    pgo, linkage = record.get("pgo_name", ""), record.get("s_linkage", "")
    if not pgo or not linkage:
        reasons.append("name_evidence_missing")
    elif record.get("internal") is True:
        if ":" not in pgo:
            reasons.append("internal_tu_prefix_missing")
        else:
            tu, name = pgo.split(":", 1)
            if (norm(tu) != norm(record.get("s_cu_source")) and
                resolve_tu_prefix(tu, linkage, record.get("tu_compile_evidence", [])) != norm(record.get("s_cu_source"))):
                reasons.append("tu_prefix_not_equal_to_cu_source")
            if name != linkage:
                reasons.append("full_linkage_name_mismatch")
    elif record.get("internal") is False:
        if ":" in pgo or ".__uniq." in pgo or ".__uniq." in linkage or pgo != linkage:
            reasons.append("external_name_mismatch")
        if record.get("coverage_name_count") != 1 or record.get("s_top_definition_count") != 1:
            reasons.append("external_name_not_unique")
    else:
        reasons.append("linkage_kind_unproven")
    if (not decl or not record.get("s_decl_line") or
        decl != norm(record.get("c_decl_file")) or
        record.get("s_decl_line") != record.get("c_decl_line") or
        record.get("c_definition_verified") is not True):
        reasons.append("declaration_identity_unproven")
    main = norm(record.get("coverage_main_file"))
    if not main or code_files != {main} or main == decl:
        reasons.append("code_regions_not_all_in_other_main_file")
    if record.get("macro_invocation_verified") is not True:
        reasons.append("decl_line_not_proven_macro_invocation")
    chain = record.get("compiler_ast_chain")
    if chain is not None:
        chain_result = validate_ast_chain(chain, decl, record.get("s_decl_line"), main)
        if chain_result == "statements_in_decl_file":
            return {"conclusion": None, "route": "original_correspondence_rules",
                    "reasons": [chain_result]}
        if chain_result is not None:
            reasons.append(chain_result)
    elif record.get("macro_definition_verified") is not True or norm(record.get("macro_definition_file")) != main:
        reasons.append("macro_definition_not_in_main_file")
    if record.get("ordinary_same_name_other_file") is not True:
        reasons.append("ordinary_rule_exclusion_unproven")
    if not isinstance(record.get("fnda"), int) or record["fnda"] < 0:
        reasons.append("fnda_missing_or_invalid")
    if reasons:
        return {"conclusion": None, "reasons": reasons}
    return {"conclusion": "macro_generated_function", "reasons": [],
            "scope_role": "reference_executed" if record["fnda"] > 0 else "reference_unexecuted",
            "in_u": False, "in_c_denominator": False, "exclusion_reason": "macro_generated_function"}


def resolve_tu_prefix(prefix, full_linkage, commands):
    """Commands must carry final C ELF code-definition provenance."""
    eligible = [c for c in commands if c.get("source") and
                posixpath.basename(c["source"]) == prefix and
                c.get("compile_log") and isinstance(c.get("compile_line"), int) and
                c["compile_line"] > 0 and c.get("linked_elf_code_dies")]
    cus = {norm(c["source"]) for c in eligible}
    if len(cus) == 1:
        return next(iter(cus))
    matched = {norm(c["source"]) for c in eligible if full_linkage in c.get("definition_linkages", [])}
    return next(iter(matched)) if len(matched) == 1 else None


def validate_ast_chain(chain, decl_file, decl_line, main_file):
    if not chain.get("ast_sha256") or not chain.get("compiler_command"):
        return "compiler_ast_evidence_missing"
    definitions = chain.get("definitions", [])
    if not definitions or definitions != chain.get("compiler_definitions"):
        return "macro_chain_definition_disagrees"
    locations = chain.get("statement_locations", [])
    if not locations:
        return "ast_statement_locations_missing"
    for loc in locations:
        if norm(loc.get("spelling_file")) == decl_file:
            return "statements_in_decl_file"
        if norm(loc.get("spelling_file")) != main_file:
            return "statement_spelling_not_in_main_file"
        if norm(loc.get("expansion_file")) != decl_file or loc.get("expansion_line") != decl_line:
            return "statement_expansion_disagrees"
    return None
