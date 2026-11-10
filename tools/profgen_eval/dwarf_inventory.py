"""Independent DWARF inventory from platform llvm-dwarfdump, no sample input.

Only source-bearing DIE attributes are retained. Linkage name lookup duplicates
DWARFDie.cpp findRecursively traversal and MIPS-before-standard attribute order.
No correspondence decision is inferred from a spelling match.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from run_scoped import platform

TAGS = {"compile_unit", "partial_unit", "subprogram", "inlined_subroutine"}
ATTRS = {"name", "linkage_name", "MIPS_linkage_name", "decl_file", "decl_line",
         "producer", "comp_dir", "low_pc", "high_pc", "abstract_origin",
         "specification", "signature", "ranges", "call_file", "call_line"}
DIE = re.compile(r"^(0x[0-9a-f]+):( +)(DW_TAG_\w+|NULL)")
ATTR = re.compile(r"^\s+DW_AT_(\w+)\s+\((.*)")
RANGE = re.compile(r"\[(0x[0-9a-f]+), (0x[0-9a-f]+)\)")


def parse(lines):
    records, stack, current, cu = {}, [], None, None
    for number, line in enumerate(lines, 1):
        match = DIE.match(line)
        if match:
            offset, indent, tag = match.groups()
            depth = len(indent)
            while stack and stack[-1][0] >= depth:
                stack.pop()
            tag = tag.removeprefix("DW_TAG_")
            parent = next((x[1] for x in reversed(stack) if x[1] in records), None)
            current = None
            if tag != "NULL":
                stack.append((depth, offset))
            if tag in TAGS:
                if tag in {"compile_unit", "partial_unit"}:
                    cu = offset
                current = {"offset": offset, "tag": tag, "cu": cu, "parent": parent,
                           "dump_line": number, "attrs": {}, "ranges": []}
                records[offset] = current
        elif current:
            match = ATTR.match(line)
            if match and match[1] in ATTRS:
                current["attrs"][match[1]] = match[2].rstrip("\n")
            match = RANGE.search(line)
            if match:
                current["ranges"].append([int(match[1],16), int(match[2],16)])
    return records


def recursive(records, offset, attrs):
    work, seen = [offset], {offset}
    while work:
        node = records.get(work.pop())
        if not node:
            continue
        for name in attrs:
            if name in node["attrs"]:
                return node["attrs"][name]
        for name in ["abstract_origin", "specification", "signature"]:
            raw = node["attrs"].get(name, "")
            match = re.match(r"(0x[0-9a-f]+)", raw)
            if match and match[1] not in seen:
                seen.add(match[1])
                work.append(match[1])
    return None


def text(raw):
    if raw is None:
        return None
    match = re.search(r'"(.*)"', raw)
    return match[1] if match else None


def number(raw):
    if raw is None:
        return None
    match = re.match(r"(0x[0-9a-f]+|[0-9]+)",raw)
    return int(match[1], 16 if match[1].startswith("0x") else 10) if match else None


def linkage_name(records, offset):
    return text(recursive(records,offset,["MIPS_linkage_name","linkage_name"])) or text(
        recursive(records,offset,["name"]))


def inventory(records):
    rows, origins = [], set()
    for off,node in records.items():
        if node["tag"] not in {"subprogram","inlined_subroutine"}:
            continue
        ranges = node["ranges"][:]
        a, b = number(node["attrs"].get("low_pc")), number(node["attrs"].get("high_pc"))
        # llvm-dwarfdump has already resolved constant high_pc to an address.
        if a is not None and b is not None and a < b:
            ranges.append([a,b])
        ranges = sorted(set(tuple(r) for r in ranges if r[0]<r[1]))
        if not ranges:
            continue
        cu = records[node["cu"]]
        row = {"die":off, "tag":node["tag"], "parent":node["parent"],
               "name":linkage_name(records,off), "ranges":ranges,
               "decl_file":text(recursive(records,off,["decl_file"])),
               "decl_line":number(recursive(records,off,["decl_line"])),
               "cu": node["cu"], "cu_name":text(cu["attrs"].get("name")),
               "comp_dir":text(cu["attrs"].get("comp_dir")),
               "producer":text(cu["attrs"].get("producer")),
               "dump_line":node["dump_line"], "raw":node["attrs"]}
        rows.append(row)
        for attribute in ["abstract_origin","specification"]:
            ref=re.match(r"(0x[0-9a-f]+)",node["attrs"].get(attribute,""))
            if ref:
                origins.add(ref[1])
    return {"code_dies":rows, "referenced_definitions":[records[o] for o in sorted(origins) if o in records],
            "compile_units":[n for n in records.values() if n["tag"] in {"compile_unit","partial_unit"}]}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--elf",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    command=platform("llvm-dwarfdump")+["--debug-info",a.elf]
    rawhash=hashlib.sha256()
    with subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          text=True,encoding="utf-8") as proc:
        def lines():
            for line in proc.stdout:
                rawhash.update(line.encode())
                yield line
        records=parse(lines())
        err=proc.stderr.read()
        rc=proc.wait()
    if rc:
        raise RuntimeError(f"dwarfdump failed {rc}: {err}")
    result=inventory(records)
    result.update(elf=a.elf,command=command,dump_sha256=rawhash.hexdigest(),stderr=err)
    Path(a.out).write_text(json.dumps(result,ensure_ascii=False,separators=(",",":"))+"\n")
    print(json.dumps({"code_dies":len(result["code_dies"]),
                      "compile_units":len(result["compile_units"]),
                      "referenced_definitions":len(result["referenced_definitions"])}))

if __name__=="__main__":
    main()
