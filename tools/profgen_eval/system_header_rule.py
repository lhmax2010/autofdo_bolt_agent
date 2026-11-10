"""Ruling 1. Positive evidence only; this is not a replacement for N.5 #16."""
import posixpath

def under(path, directory):
    if not path or not directory:
        return False
    path, directory = posixpath.normpath(path), posixpath.normpath(directory)
    return path == directory or path.startswith(directory.rstrip("/") + "/")

def normalized_dirs(directories):
    return sorted(set(posixpath.normpath(d) for d in directories))

def validate_global_files(coverage_files, system_dirs):
    violations = sorted({f for f in coverage_files if any(under(f,d) for d in system_dirs)})
    if violations:
        raise ValueError("coverage_file_in_system_directory: " + ", ".join(violations))

def classify(decl_file, candidates, evidence):
    """None is unresolved, never an invented closed state."""
    if candidates:
        return {"conclusion": None, "route": "original_correspondence_rules",
                "reason": "reference_candidate_present"}
    if not evidence.get("commands_verified") or not evidence.get("clang_v_verified"):
        return {"conclusion": None, "reason": "compile_or_search_evidence_missing"}
    s = normalized_dirs(evidence.get("s_dirs", []))
    c = normalized_dirs(evidence.get("c_dirs", []))
    if not s or s != c:
        return {"conclusion": None, "reason": "system_directories_missing_or_differ"}
    if not any(under(decl_file,d) for d in s):
        return {"conclusion": None, "reason": "decl_file_outside_system_directories"}
    if not evidence.get("coverage_disabled_verified") or not evidence.get("skip_source_verified"):
        return {"conclusion": None, "reason": "coverage_option_or_source_evidence_missing"}
    if not evidence.get("global_coverage_file_check_passed"):
        return {"conclusion": None, "reason": "global_file_check_not_passed"}
    return {"conclusion": "system_header_no_reference", "reason": "ruling1_all_four_proven"}

def group_scope(conclusions):
    if "reference_executed" in conclusions:
        return "in_mapping_scope"
    if conclusions and all(c in {"system_header_no_reference", "not_instrumented",
                                 "reference_unexecuted"} for c in conclusions):
        return "known_out_of_scope"
    return None


def proof_from_record(record, commands_verified):
    """Missing evidence on either side fails closed; no truthy strings."""
    sides = record.get("sides", {})
    proof = {"commands_verified": commands_verified,
             "s_dirs": sides.get("S", {}).get("dirs", []),
             "c_dirs": sides.get("C", {}).get("dirs", []),
             "global_coverage_file_check_passed":
                 record.get("global_coverage_file_check_passed") is True}
    for field in ("clang_v_verified", "coverage_disabled_verified", "skip_source_verified"):
        proof[field] = all(sides.get(side, {}).get(field) is True for side in ("S", "C"))
    return proof
