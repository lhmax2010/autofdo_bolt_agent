"""Static coverage reference processing; never consumes sample profiles.

JSON region layout: LLVM22 CoverageExporterJson.cpp.
Line algorithm: LLVM22 CoverageMapping.cpp:1584-1644.
Production reference counts are lcov DA; JSON counts are verification only.
"""
import argparse
import collections
import hashlib
import json
import posixpath
import re
from pathlib import Path


def normalize_file(path):
    # Only lexical normalization. Variant-specific prefix maps must be explicit.
    return posixpath.normpath(path)


def source_name(name):
    return re.sub(r"\.__uniq\.\d+$", "", name.split(":", 1)[-1])


def main_file_id(function):
    expanded = {r[6] for r in function["regions"] if r[7] == 1}
    return next((i for i in range(len(function["filenames"]))
                 if i not in expanded), None)


def function_records(functions):
    merged = {}
    empty = []
    macros = []
    for index, f in enumerate(functions):
        main = main_file_id(f)
        code = [r for r in f["regions"] if r[7] == 0 and r[5] == main]
        for r in f["regions"]:
            if r[7] == 1:
                macros.append({"function_record": index, "expansion_file_id": r[6],
                               "spelling_file_id": r[5], "region": r,
                               "spelling_file": f["filenames"][r[5]],
                               "expanded_file": f["filenames"][r[6]]})
        if main is None or not code:
            empty.append({"record": index, "name": f["name"], "count": f["count"],
                          "reason": "no_main_view" if main is None else "no_main_code",
                          "status": "unresolved_requires_correspondence"})
            continue
        filename = normalize_file(f["filenames"][main])
        start, end = min(r[0] for r in code), max(r[2] for r in code)
        key = (filename, source_name(f["name"]), start)
        row = merged.setdefault(key, {"file": filename, "name": key[1],
                                     "start": start, "end": end, "fnda": 0,
                                     "copies": [], "code_regions": []})
        row["end"] = max(row["end"], end)
        row["fnda"] += f["count"]
        row["copies"].append({"record": index, "name": f["name"], "count": f["count"],
                              "main_file_id": main})
        row["code_regions"].extend(code)
    for row in merged.values():
        # Collapse duplicate region coordinates after summing CU contributions.
        totals = collections.Counter()
        for r in row["code_regions"]:
            totals[tuple(r[:4])] += r[4]
        row["code_regions"] = [list(k)+[v] for k,v in sorted(totals.items())]
    return [merged[k] for k in sorted(merged)], empty, macros


def lines_from_segments(segments):
    by_line = collections.defaultdict(list)
    for s in segments:
        by_line[s[0]].append(s)
    if not segments:
        return {}, []
    wrapped = None
    counts, multiple = {}, []
    for line in range(1, max(by_line) + 1):
        segs = by_line[line]
        starts = [s for s in segs if not s[5] and s[3] and s[4]]
        skipped = bool(segs and not segs[0][3] and segs[0][4])
        mapped = (not skipped and (bool(wrapped and wrapped[3]) or bool(starts)))
        mapped |= any(s[4] and s[3] for s in segs)
        if len(starts) > 1:
            multiple.append(line)
        if mapped:
            counts[line] = max([wrapped[2] if wrapped else 0] + [s[2] for s in starts])
        if segs:
            wrapped = segs[-1]
    return counts, multiple


def parse_lcov(path):
    files = {}
    current = None
    for line in Path(path).read_text().splitlines():
        if line.startswith("SF:"):
            current = normalize_file(line[3:])
            if current in files:
                raise ValueError("duplicate lcov SF record: " + current)
            files[current] = {"da": {}, "fn": [], "fnda": [], "summary": {}}
        elif line.startswith("DA:"):
            number, count, *_ = line[3:].split(",")
            if int(number) in files[current]["da"]:
                raise ValueError("duplicate DA")
            files[current]["da"][int(number)] = int(count)
        elif line.startswith(("FN:", "FNDA:")):
            kind, value = line.split(":", 1)
            number, name = value.split(",", 1)
            files[current][kind.lower()].append([int(number), name])
        elif line.startswith(("LF:", "LH:", "FNF:", "FNH:")):
            kind, value = line.split(":")
            files[current]["summary"][kind] = int(value)
    return files


def process(json_path, lcov_path):
    data = json.loads(Path(json_path).read_text())["data"][0]
    lcov = parse_lcov(lcov_path)
    fn, empty, macros = function_records(data["functions"])
    checks = []
    for f in data["files"]:
        path = normalize_file(f["filename"])
        lines, multiple = lines_from_segments(f["segments"])
        actual = lcov[path]["da"]
        diffs = [[n, lines.get(n), actual.get(n)] for n in sorted(lines.keys() | actual.keys())
                 if lines.get(n) != actual.get(n)]
        checks.append({"file": path, "da_differences": diffs,
                       "executable_lines": len(actual),
                       "covered_lines": sum(v > 0 for v in actual.values()),
                       "json_summary": f["summary"]["lines"],
                       "lcov_summary": lcov[path]["summary"],
                       "has_multiple_regions": multiple})
    missing = sorted(set(lcov) - {normalize_file(f["filename"]) for f in data["files"]})
    # lcov's FN uses CountedRegions.front, not an independently stored end line.
    fn_checks = []
    for f in data["functions"]:
        main = main_file_id(f)
        if main is None:
            continue
        file = normalize_file(f["filenames"][main])
        code = [r for r in f["regions"] if r[7] == 0 and r[5] == main]
        if code:
            fn_checks.append({"name": f["name"], "start": min(r[0] for r in code),
                              "lcov_fn_present": [min(r[0] for r in code), f["name"]] in lcov[file]["fn"],
                              "lcov_fnda_present": [f["count"], f["name"]] in lcov[file]["fnda"]})
    return {"json": str(json_path), "lcov": str(lcov_path), "files": checks,
            "extra_lcov_files": missing, "function_checks": fn_checks,
            "merged_functions": fn, "empty_main": empty, "macro_regions": macros}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--json", required=True)
    p.add_argument("--lcov", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    result = process(args.json, args.lcov)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
    assert not result["extra_lcov_files"]
    assert not any(f["da_differences"] for f in result["files"])
    assert all(f["lcov_fn_present"] and f["lcov_fnda_present"]
               for f in result["function_checks"])


if __name__ == "__main__":
    main()
