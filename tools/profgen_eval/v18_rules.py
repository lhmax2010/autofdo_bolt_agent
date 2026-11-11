"""v1.8 operational domain prerequisites and fail-closed conclusion gates.

No profile reader. v17 rules remain available solely for historical reproduction.
"""
import hashlib
import json
import math
from pathlib import Path
from v17_rules import (domain_sha, ledger, coverage_views, classify_code_free as old_classify)

DOMAIN_STATEMENT = ("只覆盖固定构建中满足登记的行表归属见证规则的行；"
                    "该规则不等同于逐行证明存在真实指令")
DOMAIN_EXPLANATION = (DOMAIN_STATEMENT + "。这是可执行节内有效行表区间的操作性定义，"
                      "可能保留数据；三口径比例是参考行计数质量比例，不是运行时间或独立执行事件比例。")
UNDEFINED_SECTION = str(2**64 - 1)


def executable_sections(seq, sections):
    index = str(seq["section_index"])
    return [s for s in sections if s["executable"] and
            (index == UNDEFINED_SECTION or str(s["index"]) == index)]


def intersections(start, end, sections):
    return [(str(s["index"]), max(start, s["start"]), min(end, s["end"]))
            for s in sections if start < s["end"] and s["start"] < end]


def sequence_check(sequences, sections):
    """Validate sectioned address spaces before combining any sequence rows."""
    spans = {}
    partial, low, failures = [], [], []
    minimum = min((s["start"] for s in sections if s["executable"]), default=None)
    count = 0
    for seq in sequences:
        count += 1
        identity = {k: seq[k] for k in ("cu", "id", "section_index", "low", "high")}
        if seq["low"] >= seq["high"]:
            failures.append(dict(reason="invalid_sequence_range", **identity))
        if minimum is not None and seq["low"] < minimum:
            low.append(identity)
        secs = executable_sections(seq, sections)
        for physical, a, b in intersections(seq["low"], seq["high"], secs):
            key = (seq["cu"], str(seq["section_index"]), physical)
            spans.setdefault(key, []).append((a, b, identity))
        rows = seq["rows"]
        if not rows or not rows[-1]["end_sequence"]:
            failures.append(dict(reason="unterminated_sequence", **identity))
        for i, row in enumerate(rows):
            if row["end_sequence"]:
                continue
            if i + 1 == len(rows):
                continue
            a, b = row["address"], rows[i+1]["address"]
            if a < seq["low"] or b > seq["high"] or b < a:
                failures.append(dict(reason="invalid_row_range", row=i, **identity))
                continue
            if a == b:
                continue
            clips = intersections(a, b, secs)
            # Union clip lengths, rather than adding potentially overlapping sections.
            merged = []
            for _, x, y in sorted(clips, key=lambda v: (v[1], v[2])):
                if merged and x <= merged[-1][1]:
                    merged[-1][1] = max(y, merged[-1][1])
                else:
                    merged.append([x, y])
            if clips and sum(y-x for x, y in merged) < b-a:
                partial.append(dict(**identity, row=i, line=row["line"], file=row["file"],
                                    interval=[a, b], intersections=clips))
    for key, intervals in sorted(spans.items()):
        previous = None
        for a, b, identity in sorted(intervals, key=lambda v: (v[0], v[1], str(v[2]))):
            if previous and a < previous[1]:
                failures.append(dict(reason="overlapping_sequences", address_space=key,
                                     first=previous[2], second=identity,
                                     intersection=[a, min(b, previous[1])]))
            if previous is None or b > previous[1]:
                previous = (a, b, identity)
    return dict(sequence_count=count, passed=not failures, failures=failures,
                partial_intervals=partial, low_sequences=low,
                partial_intervals_count=len(partial), low_sequences_count=len(low))


def stage_witnesses(sequences, sections):
    """Must only run after sequence_check; no instruction boundary assumption."""
    found, failures = {}, []
    for seq in sequences:
        secs = executable_sections(seq, sections)
        for i, row in enumerate(seq["rows"][:-1]):
            start, end = row["address"], seq["rows"][i+1]["address"]
            if row["end_sequence"] or end <= start or row["line"] == 0:
                continue
            clips = intersections(start, end, secs)
            if not clips:
                continue
            if not row["file_resolved"]:
                failures.append("line_file_unresolved")
                continue
            found.setdefault((row["file"], row["line"]),
                             dict(sequence=seq["id"], cu=seq["cu"],
                                  section_index=seq["section_index"], row=i,
                                  interval=[start, end], executable_intersections=clips))
    return found, failures


def domain(c0, evidence):
    """Only C0 + ELF facts; sequence suppliers can be reopened for streaming."""
    seen, errors, checks = {}, [], {}
    for stage, e in sorted(evidence.items()):
        seq = e["sequences"]
        factory = seq if callable(seq) else lambda seq=seq: iter(seq)
        check = sequence_check(factory(), e["sections"])
        checks[stage] = check
        failures = list(e.get("errors", []))
        if e.get("exit_code", 0) != 0:
            failures.append("extractor_nonzero_exit")
        if e.get("diagnostics"):
            failures.append("extractor_diagnostic")
        if not check["passed"]:
            failures.extend(sorted({r["reason"] for r in check["failures"]}))
            # No direct union from an input whose sequence semantics failed.
            w = {}
        else:
            w, row_failures = stage_witnesses(factory(), e["sections"])
            failures.extend(row_failures)
        for k, value in w.items():
            if k in c0:
                seen.setdefault(k, dict(stage=stage, **value))
        errors.extend(stage + ":" + f for f in failures)
    unresolved = set(c0) - seen.keys() if errors else set()
    return set(seen) | unresolved, seen, unresolved, errors, checks


def registration(unresolved_lines, gates, numerator, denominator):
    reasons = [name for name, g in gates.items() if g["exceeds_one_percent"]]
    if denominator == 0:
        reasons.append("zero_reference_denominator")
    elif 2*numerator < denominator:
        reasons.append("coverage_3_below_50_percent")
    if unresolved_lines:
        reasons.append("domain_evidence_incomplete")
        return "domain_evidence_incomplete", reasons
    return ("ineligible" if reasons else "eligible"), reasons


def classify_code_free(*args):
    result = old_classify(*args)
    if result["category"] == "own_stmt_no_code":
        result["description"] = "未取得行表归属见证"
    return result


def _finite_tree(value, path="$"):
    if value is None or value == {}:
        raise ValueError("undefined_value:" + path)
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite_value:" + path)
    if isinstance(value, dict):
        for key, item in value.items():
            _finite_tree(item, path + "." + key)
    elif isinstance(value, list):
        for n, item in enumerate(value):
            _finite_tree(item, path + "[" + str(n) + "]")


def _fraction(f, name):
    if not isinstance(f, dict) or set(f) != {"numerator", "denominator", "ratio"}:
        raise ValueError("invalid_fraction:" + name)
    n, d, r = f["numerator"], f["denominator"], f["ratio"]
    if type(n) is not int or type(d) is not int or n < 0 or d <= 0:
        raise ValueError("invalid_integer_or_denominator:" + name)
    if type(r) not in (int, float) or not math.isfinite(r) or r != n / d:
        raise ValueError("inconsistent_ratio:" + name)


FIELDS = ("coverage_3_views", "coverage_3_prime", "code_bearing", "nonduplicated_outside")


def _validate_values(data):
    _finite_tree(data)
    text = data.get("evaluation_domain", "")
    if DOMAIN_STATEMENT not in text or "已证明每行都有指令" in text:
        raise ValueError("incorrect_evaluation_domain")
    if data.get("status") == "domain_evidence_incomplete":
        raise ValueError("domain_evidence_incomplete")
    if type(data.get("domain_unresolved_lines")) is not int or data["domain_unresolved_lines"] < 0:
        raise ValueError("missing_unresolved_count")
    if data["domain_unresolved_lines"]:
        raise ValueError("domain_evidence_incomplete")
    views = data.get("coverage_3_views", {})
    if set(views) != {"C0", "C_dc", "C"}:
        raise ValueError("missing_coverage_view")
    for name, f in views.items():
        _fraction(f, name)
    if len({f["numerator"] for f in views.values()}) != 1:
        raise ValueError("unequal_numerators")
    if not views["C"]["denominator"] <= views["C_dc"]["denominator"] <= views["C0"]["denominator"]:
        raise ValueError("unordered_denominators")
    for name in FIELDS[1:]:
        if name not in data:
            raise ValueError("missing_descriptor:" + name)
        if name == "coverage_3_prime":
            if type(data[name]) not in (int, float) or not math.isfinite(data[name]) or data[name] < 0:
                raise ValueError("invalid_coverage_3_prime")
        else:
            _fraction(data[name], name)
    json.dumps(data, allow_nan=False)


def validate_conclusion(data, table_path, registered_sha, object_id):
    """Trusted SHA and object ID come from registration, never from the payload."""
    _validate_values(data)
    raw = Path(table_path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != registered_sha:
        raise ValueError("registration_table_sha_mismatch")
    table = json.loads(raw, parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite_table:"+x)))
    expected = table["objects"][object_id]
    _validate_values(expected)
    if data.get("object") != object_id or expected.get("object") != object_id:
        raise ValueError("object_mismatch")
    for name in (*FIELDS, "status", "domain_unresolved_lines"):
        if data[name] != expected[name]:
            raise ValueError("registration_table_value_mismatch:" + name)
    return True


def write_conclusion(path, data, table_path, registered_sha, object_id):
    validate_conclusion(data, table_path, registered_sha, object_id)
    serialized = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    Path(path).write_text(serialized)


def write_diagnostic(path, reasons, evidence):
    """Undefined values may only appear under an explicitly non-conclusive kind."""
    data = dict(kind="diagnostic", quality_conclusion_defined=False,
                registration_status="not_assessed", reasons=reasons, evidence=evidence)
    serialized = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    Path(path).write_text(serialized)
