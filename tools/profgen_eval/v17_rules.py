"""v1.7 corrected domain and gates. Pure rules, no profile/file readers."""
import hashlib
import json
from code_free_v2_rules import classify as classify_v2


def domain_sha(lines):
    return hashlib.sha256(json.dumps(sorted(lines), ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def witnesses(sequences, sections):
    """Rows stay in sequence order; equal addresses are superseded naturally."""
    result = {}
    failures = []
    for seq in sequences:
        rows = seq["rows"]
        for i, row in enumerate(rows):
            if row["end_sequence"]:
                continue
            if i + 1 == len(rows):
                failures.append("unterminated_sequence")
                continue
            end = rows[i + 1]["address"]
            start = row["address"]
            if end < start:
                failures.append("nonmonotonic_sequence")
                continue
            if end == start or row["line"] == 0:
                continue
            intersections = [[max(start, s["start"]), min(end, s["end"])]
                             for s in sections if s["executable"]
                             and start < s["end"] and s["start"] < end]
            if not intersections:
                continue
            if not row["file_resolved"]:
                failures.append("line_file_unresolved")
                continue
            key = (row["file"], row["line"])
            result.setdefault(key, dict(sequence=seq.get("id"), row=i,
                                        interval=[start, end],
                                        executable_intersections=intersections))
    return result, failures


def domain(c0, evidence):
    """Only C0 and ELF-derived evidence. No correspondence/mapping argument."""
    seen = {}
    errors = []
    for stage, e in sorted(evidence.items()):
        w, failures = witnesses(e["sequences"], e["sections"])
        for k, v in w.items():
            if k in c0:
                seen.setdefault(k, dict(stage=stage, **v))
        errors.extend([stage + ":" + f for f in e.get("errors", []) + failures])
    # An unlocalized extraction failure cannot prove absence for any unseen line.
    unresolved = set(c0) - set(seen) if errors else set()
    c = set(seen) | unresolved
    return c, seen, unresolved, errors


def classify_code_free(line, c_lines, nodes, tokens, labels, available, calls):
    r = classify_v2(line, c_lines, nodes, tokens, labels, available)
    if r["category"] in ("own_stmt_no_code", "other") and calls:
        return dict(category="inlined_call_site",
                    reason="DW_AT_call_file_line_in_either_build",
                    witness=calls, tokens=tokens)
    if r["category"] == "own_stmt_no_code":
        r["description"] = "未取得指令行归属见证"
    return r


def ledger(c0, c, da, base_reasons, macro_lines=(), unresolved=()):
    """Macro state affects U and reasons, never C."""
    macro, missing = set(macro_lines), set(unresolved)
    reasons = {}
    for k in c0:
        rs = set(base_reasons.get(k, ()))
        if k not in c:
            rs.add("code_free_line")
        if k in macro:
            rs.add("macro_generated_function")
        if k in missing:
            rs.add("domain_unresolved")
        reasons[k] = rs
    u = {k for k in c if not reasons[k]}
    def account(universe):
        buckets = {}
        for k in sorted(set(universe) - u):
            key = tuple(sorted(reasons[k]))
            assert key
            b = buckets.setdefault(key, dict(lines=0, DA=0))
            b["lines"] += 1
            b["DA"] += da[k]
        den = sum(da[k] for k in universe)
        num = sum(da[k] for k in u)
        loss = sum(b["DA"] for b in buckets.values())
        assert den - num - loss == 0
        return dict(denominator=den, numerator=num, loss=loss, difference=0,
                    assertion_passed=True,
                    buckets=[dict(reasons=list(k), **v)
                             for k, v in sorted(buckets.items())])
    return u, reasons, account(c), account(c0)


def coverage_views(c0, c, u, da, classes):
    dc = set(c0) - {k for k, v in classes.items()
                   if v in ("asm_interior", "structural_line", "expr_continuation")}
    assert u <= c <= dc <= set(c0)
    num = sum(da[k] for k in u)
    den = {n: sum(da[k] for k in ks)
           for n, ks in (("C0", c0), ("C_dc", dc), ("C", c))}
    fractions = {n: dict(numerator=num, denominator=v,
                         ratio=num / v if v else None) for n, v in den.items()}
    outside = sum(da[k] for k in dc - c)
    return dict(C_dc_lines=len(dc), coverage_3_views=fractions,
                code_bearing=dict(numerator=den["C"], denominator=den["C0"],
                                  ratio=den["C"]/den["C0"] if den["C0"] else None),
                nonduplicated_outside=dict(numerator=outside, denominator=den["C_dc"],
                                          ratio=outside/den["C_dc"] if den["C_dc"] else None),
                nested_sets_assertion=True)


def no_key_proven(proof):
    return (proof.get("inventory_complete") is True
            and proof.get("enumeration_complete") is True
            and proof.get("symbolization_complete") is True
            and proof.get("instance_record_present") is True
            and proof.get("boundary_available") is True
            and proof.get("accepted_key_instructions") == 0)


def classify_body(record):
    """Synthetic-only entry point until registration; includes explicit zeros."""
    if record.get("boundary_unavailable"):
        return "boundary_unavailable", "boundary_unavailable"
    if not record["known_name"]:
        return "unaligned", "unknown_name"
    if not record["reference_resolved"]:
        return "unaligned", "reference_unresolved"
    if record["known_out_of_scope"]:
        return "out_of_scope", "known_out_of_scope"
    if not record["registered_key"]:
        return "unaligned", "unmapped_key"
    special = record.get("value_status")
    if special in ("system_header_no_reference", "macro_generated_function",
                   "identity_ambiguous"):
        return "aligned_outside_U", special
    if record.get("unexecuted_source"):
        return "aligned_outside_U", "unexecuted_reference_source"
    if record.get("excluded"):
        return "aligned_outside_U", "excluded_line"
    if record.get("in_U"):
        return "in_U", "in_U"
    return "aligned_outside_U", "outside_U"


DOMAIN_STATEMENT = "只覆盖固定构建中有指令行归属见证的行"


def validate_conclusion(data):
    """Check before any writer opens an output. No evaluation run is performed."""
    if data.get("evaluation_domain") != DOMAIN_STATEMENT:
        raise ValueError("missing_or_incorrect_evaluation_domain")
    for key in ("C0", "C_dc", "C"):
        if key not in data.get("coverage_3_views", {}):
            raise ValueError("missing_coverage_3:" + key)
        for field in ("numerator", "denominator", "ratio"):
            if field not in data["coverage_3_views"][key]:
                raise ValueError("missing_coverage_field:" + key + ":" + field)
    for key in ("coverage_3_prime", "nonduplicated_outside", "code_bearing"):
        if key not in data:
            raise ValueError("missing_domain_descriptor:" + key)
    return True

def write_conclusion(path, data):
    """Validation precedes file opening; callers cannot emit an unlabeled result."""
    validate_conclusion(data)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
