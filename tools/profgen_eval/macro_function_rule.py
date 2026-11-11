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
        if chain_result == "nonargument_token_in_decl_file":
            return {"conclusion": None, "route": "original_correspondence_rules",
                    "reasons": [chain_result]}
        if chain_result is not None:
            reasons.append(chain_result)
    else:
        reasons.append("compiler_token_evidence_missing")
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


def within(location, region):
    """Inclusive token-start offsets; files must be real, identical source files."""
    return (bool(location.get("file")) and not location.get("is_scratch") and
            norm(location["file"]) == norm(region.get("file")) and
            isinstance(location.get("offset"), int) and
            isinstance(region.get("begin"), int) and isinstance(region.get("end"), int) and
            region["begin"] <= location["offset"] <= region["end"])


def validate_ast_chain(chain, decl_file, decl_line, main_file):
    """Supplement2: compiler truth, without reconstructing scratch spelling."""
    if not chain.get("ast_sha256") or not chain.get("compiler_command"):
        return "compiler_ast_evidence_missing"
    if not chain.get("token_sha256"):
        return "compiler_token_evidence_missing"
    definitions = chain.get("definitions", [])
    if not definitions or definitions != chain.get("compiler_definitions"):
        return "macro_chain_definition_disagrees"
    tokens = chain.get("tokens", [])
    if not tokens:
        return "body_tokens_missing"
    allowed = chain.get("invocation_argument_ranges", []) + chain.get("definition_body_ranges", [])
    for token in tokens:
        spelling, expansion = token.get("spelling", {}), token.get("expansion", {})
        if norm(expansion.get("file")) != decl_file or expansion.get("line") != decl_line:
            return "token_expansion_disagrees"
        if type(token.get("isMacroArgExpansion")) is not bool:
            return "macro_argument_flag_missing"
        if norm(spelling.get("file")) == main_file:
            continue
        if token["isMacroArgExpansion"] is not True:
            return ("nonargument_token_in_decl_file" if norm(spelling.get("file")) == decl_file
                    else "nonargument_token_outside_main_file")
        if not any(within(spelling, region) for region in allowed):
            context=chain.get("paste_context")
            if (spelling.get("is_scratch") is True and
                spelling.get("presumed_file")=="<scratch space>" and context is not None):
                from token_paste_rule import prove
                proof=prove(token,context,context.get("macros",[]))
                chain.setdefault("paste_proofs",[]).append(proof)
                if proof["status"]=="proved":
                    continue
                return ";".join(proof["reason_codes"])
            return "argument_spelling_outside_allowed_ranges"
    return None
