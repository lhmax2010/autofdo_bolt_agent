#!/usr/bin/env python3
"""Convert LLVM 22 GCOV block counts to a one-TU, non-FS LLVM sample profile."""
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
import argparse
import json
import posixpath
import re
import struct

FUNCTION = re.compile(r"^===== (.+) \((\d+)\) @ (.+):(\d+)$")
BLOCK = re.compile(r"^Block : (\d+) Counter : (\d+)$")
LOCATION = re.compile(r"^\s*File: (\d+): ((?:\d+,)+)\s*$")
VERSION = b"*11B"        # LLVM Clang 22.1.8's B11* word-length format.


@dataclass
class Function:
    name: str
    file: int
    start: int
    blocks: dict = field(default_factory=dict)


def gcno_paths(path, *, allow_empty=False):
    """Reconstruct LLVM GCOV's first-seen, normalized filename index."""
    raw = path.read_bytes()
    if raw[:8] != b"oncg" + VERSION:
        raise ValueError("expected little-endian LLVM GCOV B11* notes")
    files, functions = {}, {}
    pos = 12
    def word():
        nonlocal pos
        if pos+4 > len(raw):
            raise ValueError("truncated GCNO")
        v = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        return v
    def string(end):
        nonlocal pos
        size = 4 * word()
        if pos+size > end:
            raise ValueError("GCNO string overruns record")
        data = raw[pos:pos+size]
        pos += size
        if not size:
            return ""
        if b"\0" not in data:
            raise ValueError("unterminated GCNO string")
        return data.partition(b"\0")[0].decode()
    def index(name):
        return files.setdefault(posixpath.normpath(name),len(files))
    string(len(raw))           # Compilation working directory.
    word()                     # hasUnexecutedBlocks
    while pos < len(raw):
        tag = word()
        if not tag:
            if any(raw[pos:]):
                raise ValueError("unexpected data after GCNO terminator")
            break
        size = word() * 4
        end = pos + size
        if end > len(raw):
            raise ValueError("GCNO record overruns input")
        if tag == 0x01000000:
            ident = word()
            word()            # Line number checksum
            word()            # CFG checksum
            name = string(end)
            word()            # Artificial-function flag
            source = string(end)
            start = word()
            word()            # Start column
            word()            # End line
            word()            # End column
            if ident in functions or not name or not source or not start:
                raise ValueError("invalid or duplicate GCNO function")
            functions[ident] = Function(name,index(source),start)
        elif tag == 0x01450000:
            word()            # Block index
            while pos < end:
                if word() == 0:
                    file = string(end)
                    if not file:
                        break
                    index(file)
        if pos > end:
            raise ValueError("GCNO detector consumed beyond record")
        pos = end
    if not functions and not allow_empty:
        raise ValueError("no GCNO functions")
    return functions, tuple(files)


def dump_blocks(path, notes, files):
    found = set()
    fn = block = None
    for lineno, raw in enumerate(path.read_text().splitlines(),1):
        func = FUNCTION.fullmatch(raw)
        basic = BLOCK.fullmatch(raw)
        loc = LOCATION.fullmatch(raw)
        if func:
            name, key, filename, start = func.groups()
            key = int(key)
            if key not in notes or key in found:
                raise ValueError(f"{path}:{lineno}: unknown or duplicate function {key}")
            fn = notes[key]
            if (fn.name,files[fn.file],fn.start) != (name,posixpath.normpath(filename),int(start)):
                raise ValueError(f"{path}:{lineno}: dump does not match notes")
            found.add(key)
            block = None
        elif basic and fn is not None:
            num, count = map(int,basic.groups())
            if num in fn.blocks or count > 2**64-1:
                raise ValueError(f"{path}:{lineno}: invalid block")
            block = (count,defaultdict(set))
            fn.blocks[num] = block
        elif loc and block is not None:
            file = int(loc[1])
            if file >= len(files):
                raise ValueError(f"{path}:{lineno}: unknown file index")
            block[1][file].update(int(x) for x in loc[2].rstrip(",").split(","))
        elif raw.strip() and not raw.strip().startswith(("Source Edges :", "Destination Edges :")):
            raise ValueError(f"{path}:{lineno}: unrecognized GCOV dump line")
    if found != set(notes) or any(0 not in fn.blocks for fn in notes.values()):
        raise ValueError("incomplete LLVM GCOV dump")


def convert(notes_path,dump_path,excluded=()):
    notes, files = gcno_paths(notes_path)
    dump_blocks(dump_path, notes, files)
    names = Counter(fn.name for fn in notes.values())
    output, audit = [], {}
    for fn in sorted(notes.values(),key=lambda f:(f.name,f.file,f.start)):
        source = files[fn.file]
        key = f"{fn.name}@{source}:{fn.start}"
        if names[fn.name]>1 or fn.name in excluded or re.search(r"[:\s]",fn.name):
            audit[key] = {"skipped":"ambiguous_or_unsupported_function_name"}
            continue
        hits = defaultdict(list)
        foreign = 0
        for _, (count, locations) in sorted(fn.blocks.items()):
            foreign += sum(len(lines) for file,lines in locations.items() if file!=fn.file)
            for line in locations.get(fn.file, ()):
                if line>=fn.start:
                    hits[line-fn.start].append(count)
        body = {line:max(values) for line,values in sorted(hits.items())}
        head = fn.blocks[0][0]
        row = {"head":head,"foreign_source_locations":foreign,"multiple_blocks_on_line":sum(len(v)>1 for v in hits.values()),
               "body":body}
        audit[key] = row
        if not body or not any(body.values()):
            row["skipped"]="no_executed_body_lines"
            continue
        total = max(head,sum(body.values()))
        if total>2**64-1:
            raise ValueError(f"{key}: sample-profile total overflow")
        output.append(f"{fn.name}:{total}:{head}\n")
        output.extend(f" {offset}: {count}\n" for offset,count in body.items())
    if not output:
        raise ValueError("no executed lines eligible for a sample profile")
    return "".join(output), audit


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("gcno",type=Path)
    p.add_argument("dump",type=Path)
    p.add_argument("output",type=Path)
    p.add_argument("--audit",type=Path,required=True)
    p.add_argument("--exclude-names",type=Path,help="One linkage name per line, e.g. collisions found across TUs")
    args = p.parse_args()
    excluded = args.exclude_names.read_text().splitlines() if args.exclude_names else ()
    output,audit = convert(args.gcno,args.dump,set(excluded))
    args.output.write_text(output)
    args.audit.write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")


if __name__ == "__main__":
    main()
