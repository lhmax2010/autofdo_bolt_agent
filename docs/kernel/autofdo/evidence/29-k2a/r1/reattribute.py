#!/usr/bin/env python3
"""Offline A32 IRQ-shadow attribution for K1e's archived perf records."""
from bisect import bisect_right
from collections import Counter, defaultdict
from itertools import zip_longest
from pathlib import Path
import argparse
import hashlib
import json
import mmap
import re
import shutil
import struct
import subprocess

BUILD_ID = "96766cfcbff8c33d83ca38152ad02f6a02dd44d4"
HEADER = re.compile(rb"^\s*-?\d+/-?\d+\s+(\d+)\s+cycles:\s*\n$")
FRAME = re.compile(rb"^\t\s*([a-fA-F0-9]+)\s+\((.*)\)\n$")
KERNEL = re.compile(rb"^\[kernel\.kallsyms\]\+0x([a-fA-F0-9]+)$")
ANCHOR = re.compile(rb"\[0x([a-f0-9]+)\(0x[0-9a-f]+\) @ 0x[0-9a-f]+ <([a-f0-9]+)>\]: ---p \[kernel\.kallsyms\](_[a-z]+)")
VDSO_TEMP = re.compile(rb"/tmp/perf-vdso\.so-[A-Za-z0-9]{6}(?=\+0x)")
HELPERS = frozenset({
    "_raw_spin_unlock_irqrestore", "_raw_spin_unlock_irq",
    "_raw_read_unlock_irqrestore", "_raw_write_unlock_irqrestore",
    "_raw_read_unlock_irq", "_raw_write_unlock_irq",
    "arch_local_irq_enable", "arch_local_irq_restore",
    "local_irq_enable", "local_irq_restore", "raw_local_irq_enable", "raw_local_irq_restore",
    "trace_hardirqs_on", "trace_hardirqs_on_prepare", "lockdep_hardirqs_on",
})
WORKLOADS = ("pipe", "mmfault", "tmpfs", "syscall", "tos")


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def run(argv, stdout, stderr):
    with stdout.open("wb") as o, stderr.open("wb") as e:
        subprocess.run(argv, stdout=o, stderr=e, check=True)


def publish(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def symbol_table(path):
    core = defaultdict(set)
    markers = {}
    for line in path.read_text().splitlines():
        fields = line.split()
        if len(fields) < 3:
            continue
        address, kind, name, *module = fields
        if module:
            continue
        address = int(address, 16)
        if name in ("_text", "_stext", "_etext", "_sinittext", "_einittext"):
            markers[name] = address
        if kind in "TtWw":
            core[address].add(name)
    assert len(markers) == 5
    return dict(core), markers


class Image:
    def __init__(self, image):
        self.core, self.markers = symbol_table(image.parent / "System.map")
        self.starts = sorted(self.core)
        with image.open("rb") as handle:
            self.data = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        assert self.data[:6] == b"\x7fELF\x01\x01"
        assert struct.unpack_from("<H", self.data, 18)[0] == 40
        offset = struct.unpack_from("<I", self.data, 28)[0]
        length, count = struct.unpack_from("<HH", self.data, 42)
        self.loads = []
        for i in range(count):
            typ, pos, addr, _, filesz, _, flags, _ = struct.unpack_from("<8I", self.data, offset + i * length)
            if typ == 1 and flags & 1:
                self.loads.append((addr, addr + filesz, pos))

    def start(self, ip):
        if not any(self.markers[a] <= ip < self.markers[b]
                   for a, b in (("_stext", "_etext"), ("_sinittext", "_einittext"))):
            return None
        i = bisect_right(self.starts, ip) - 1
        return self.starts[i] if i >= 0 else None

    def names(self, ip):
        return self.core.get(self.start(ip), set())

    def word(self, ip):
        if ip % 4:
            return 0
        for first, last, offset in self.loads:
            if first <= ip <= last - 4:
                return struct.unpack_from("<I", self.data, offset + ip - first)[0]
        return 0

    def irq_window(self, ip):
        start = self.start(ip)
        return start is not None and any(opener(self.word(ip - step)) for step in (0, 4) if ip-step >= start)


def opener(word):
    return (word & 0xfffffe3f == 0xf1080000 and word & 0x80) or (
        word >> 28 != 15 and word & 0x0ffffff0 == 0x0121f000)


def a32_call(word, pc):
    if word >> 28 == 15:
        return None
    if word & 0x0f000000 == 0x0b000000:
        relative = (word & 0x00ffffff) << 2
        if relative & (1 << 25):
            relative -= 1 << 26
        return ("bl", pc + 8 + relative)
    if word & 0x0ffffff0 == 0x012fff30:
        return ("blx-register", None)
    return None


def parse_frames(stream):
    line = stream.readline()
    while line:
        header = HEADER.fullmatch(line)
        if not header:
            yield line, (), None
            line = stream.readline()
            continue
        frames = []
        previous = None
        line = stream.readline()
        while line.startswith(b"\t"):
            row = FRAME.fullmatch(line)
            if not row:
                raise ValueError(f"unrecognized callchain frame {line!r}")
            ip, dso = int(row[1], 16), row[2]
            if dso == b"inlined":
                previous = ip
            else:
                if previous is not None:
                    assert previous == ip
                previous = None
                frames.append((ip, dso, line))
            line = stream.readline()
        assert previous is None and frames
        yield header[0][:-1] + b" " + frames[0][2][1:], frames, int(header[1])
        if line == b"\n":
            line = stream.readline()


def read_dwarf(tool, image, addresses):
    if not addresses:
        return {}
    text = "".join(f"{ip:#x}\n" for ip in sorted(addresses))
    result = subprocess.run([tool, f"--obj={image}", "--output-style=JSON", "--functions=linkage", "--inlines"],
                            input=text, capture_output=True, text=True, check=True)
    entries = [json.loads(line) for line in result.stdout.splitlines()]
    mapped = {int(row["Address"], 16): row.get("Symbol", []) for row in entries}
    assert set(mapped) == set(addresses)
    return mapped


def outcome(image, slide, ips, dwarf):
    previous = ips[0][0] - slide
    last = "leaf_only"
    for ip, dso, _ in ips[1:]:
        if not KERNEL.fullmatch(dso):
            return "stack_boundary_without_caller", None
        link = ip - slide
        if link == previous:
            last = "leaf_only"
            continue
        pc = link - 4
        item = image.start(pc)
        if item is None or pc % 4:
            return "caller_outside_a32_text", None
        frames = dwarf.get(pc, [])
        function = image.names(pc)
        if image.irq_window(pc) or function & HELPERS or (frames and frames[0]["FunctionName"] in HELPERS):
            previous = pc
            last = "only_helper_frames"
            continue
        decoded = a32_call(image.word(pc), pc)
        if not decoded:
            return "return_ip_without_link_instruction", None
        kind, target = decoded
        if target is not None and image.start(target) != image.start(previous):
            return "direct_call_target_disagrees", None
        if not frames or not frames[0]["Line"] or not frames[0]["FileName"].endswith((".c", ".h")) or not frames[-1]["StartLine"]:
            return "no_c_dwarf_callsite", None
        return "reattributed", (pc, kind, frames)
    return last, None


def apply_segment(args, image, source, out):
    out.mkdir(parents=True, exist_ok=False)
    label = f"{source.parent.name}/{source.name}"
    original = source / "perf.data"
    expected_sha = (source / "perf.sha256").read_text().split()[0]
    assert digest(original) == expected_sha
    recorded = (source/"perf.argv").read_text().split()
    assert "-g" in recorded
    before, runtime = symbol_table(source / "kallsyms.before")
    after, runtime_after = symbol_table(source / "kallsyms.after")
    assert (before, runtime) == (after, runtime_after)
    slides = {runtime[key] - v for key, v in image.markers.items()}
    assert len(slides) == 1
    slide = slides.pop()
    old = json.loads((source / "segment-summary.json").read_text())
    weights = Counter({name: counts["samples"] for name, counts in old["functions"].items()})
    update = weights.copy()
    baseline_q = json.loads((source / "quality.json").read_text())
    stack = out / "stack.perfscript"
    run([args.perf, "script", "-i", original, "--show-mmap-events", "--show-lost-events",
         "-F", "pid,tid,event,period,ip,dsoff"], stack, out / "perf.stderr")
    candidates = {}
    aliases = sorted(before)
    seen = Counter()
    def name(ip):
        i = bisect_right(aliases, ip) - 1
        return " / ".join(sorted(before[aliases[i]])) if i >= 0 else "[unknown]"
    with stack.open("rb") as full, (source/"ip.perfscript").open("rb") as flat:
        for i, pair in enumerate(zip_longest(parse_frames(full), flat)):
            item, reference = pair
            assert item is not None and reference is not None, (label,i)
            if item[0] != reference:
                assert VDSO_TEMP.sub(b"/tmp/perf-vdso.so-RANDOM",item[0]) == VDSO_TEMP.sub(b"/tmp/perf-vdso.so-RANDOM",reference), (label,i,item,reference)
                seen["perf_vdso_path_differences"] += 1
            row, frames, period = item
            if not frames:
                anchor = ANCHOR.search(row)
                if anchor:
                    assert anchor[2].decode() == BUILD_ID and runtime[anchor[3].decode()] == int(anchor[1],16)
                    seen["anchors"] += 1
                continue
            assert period == 1000003
            seen["samples"] += 1
            ip, dso, _ = frames[0]
            if KERNEL.fullmatch(dso) and image.irq_window(ip-slide):
                candidates[i] = frames
    assert seen["anchors"] and seen["samples"] == baseline_q["samples"]["input_total"]["sample_count"]
    assert len(candidates) == old["counts"]["irq_window"], (label, len(candidates), old["counts"]["irq_window"])
    callsites = {ip-slide-4 for frames in candidates.values() for ip,dso,_ in frames[1:]
                 if KERNEL.fullmatch(dso) and image.start(ip-slide-4) is not None}
    dwarf = read_dwarf(args.tools/"llvm-symbolizer", args.vmlinux, callsites)
    decisions = Counter()
    moves = Counter()
    rewrites = {}
    for i, frames in candidates.items():
        reason, target = outcome(image, slide, frames, dwarf)
        decisions[reason] += 1
        if target is None:
            continue
        pc, kind, line = target
        previous, new = name(frames[0][0]), name(pc+slide)
        assert update[previous] > 0, (label, previous, frames[0])
        update[previous] -= 1
        update[new] += 1
        leaf = line[0]
        moves[(previous,new,hex(pc),leaf["FileName"],leaf["Line"],kind)] += 1
        rewrites[i] = pc + slide
    flat_path = out / "corrected.perfscript"
    with (source/"ip.perfscript").open("rb") as original_flat, flat_path.open("wb") as corrected:
        for i, row in enumerate(original_flat):
            pc = rewrites.get(i)
            if pc is not None:
                rpc = f"{pc:x}".encode()
                row, count = re.subn(rb"[a-fA-F0-9]+ \(\[kernel\.kallsyms\]\+0x[a-fA-F0-9]+\)\n$",
                                     rpc+b" ([kernel.kallsyms]+0x"+rpc+b")\n", row)
                assert count == 1
            corrected.write(row)
    assert sum(weights.values()) == sum(update.values()) == old["kernel"]
    stack.unlink()
    shutil.copyfile(source/"buildids.txt", out/"buildids.txt")
    cli = [args.tools/"llvm-profgen","--ip-samples","--kernel",f"--binary={args.vmlinux}",
           f"--perfscript={flat_path}",f"--perf-buildid-list={out/'buildids.txt'}","--ip-weight=sample",
           "--ip-aggregation=max","--ip-head-samples=none","--ip-zero-fill=none","--ip-skid=none",
           "--show-ip-address-counts","--format=extbinary",f"--output={out/'segment.prof'}",
           f"--quality-report={out/'quality.json'}"]
    publish(out/"profgen.argv.json", list(map(str,cli)))
    run(cli, out/"profgen-addresses.txt", out/"profgen.stderr")
    q = json.loads((out/"quality.json").read_text())
    assert q["identity"]["grade"] == "verified" and q["identity"]["binary_build_id"] == BUILD_ID
    assert q["semantics"]["fs_discriminator"]
    for key in ("target","outside_image","modules_skipped","user","unknown_address","unknown_pid"):
        if key in baseline_q["samples"]["kernel_ip"]:
            assert baseline_q["samples"]["kernel_ip"][key] == q["samples"]["kernel_ip"][key], (label,key)
    accepted = {}
    pattern = re.compile(r"IP-ADDRESS (0x[\da-f]+) sample_count=(\d+) period_sum=(\d+)")
    for record in (out/"profgen-addresses.txt").read_text().splitlines():
        match = pattern.fullmatch(record)
        if match:
            ip, count, period = match.groups()
            assert int(period) == int(count)*1000003
            accepted[int(ip,16)] = int(count)
    assert accepted
    symbols = read_dwarf(args.tools/"llvm-symbolizer", args.vmlinux, accepted)
    duplicates = set(json.loads(args.duplicates.read_text()))
    available = sum(n for ip,n in accepted.items() if symbols[ip] and symbols[ip][0]["Line"] and
                    symbols[ip][0]["FileName"].endswith((".c",".h")) and
                    symbols[ip][-1]["StartLine"] and symbols[ip][-1]["StartFileName"].endswith((".c",".h")))
    usable = q["samples"]["target"]["usable"]["sample_count"]
    lower = max(0, usable - (sum(accepted.values()) - available))
    ambiguous = sum(n for ip,n in accepted.items() if any(fun["FunctionName"] in duplicates for fun in symbols[ip]))
    result = dict(segment=label,input_sha256=expected_sha,flat_replay_byte_identical=not seen["perf_vdso_path_differences"],
                  perf_vdso_path_differences=seen["perf_vdso_path_differences"],boot_id=old["boot_id"],
                  input_samples=seen["samples"],kernel=old["kernel"],shadow=len(candidates),decisions=dict(decisions),
                  usable=usable,baseline_usable=old["profgen_usable"],usable_c_line_lower=lower,
                  ambiguity_upper=ambiguous,baseline_c_line_lower=old["usable_c_line_lower"],lost=q["lost"],
                  moves=[dict(zip(("from","to","link_ip","file","line","instruction","samples"),(*key,n)))
                         for key,n in moves.most_common()],
                  before=dict(weights),after=dict(update),sha256=digest(out/"segment.prof"))
    publish(out/"segment.json",result)
    print(label, result["shadow"], dict(decisions), "usable", usable, flush=True)
    return result


def main():
    p = argparse.ArgumentParser()
    for name in ("training","out","tools","perf","vmlinux","duplicates"):
        p.add_argument("--"+name, type=Path, required=True)
    p.add_argument("--one", help="Only run one session/workload for validation")
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    image = Image(args.vmlinux)
    all_results = []
    dirs = []
    for session in ("session-01","session-02","session-03"):
        for workload in WORKLOADS:
            part = f"{session}/{workload}"
            if args.one and args.one != part:
                continue
            dest = args.out / part
            cached = dest / "segment.json"
            if cached.is_file():
                row = json.loads(cached.read_text())
                assert digest(dest/"segment.prof") == row["sha256"]
                assert digest(args.training/part/"perf.data") == row["input_sha256"]
            else:
                row = apply_segment(args,image,args.training/part,dest)
            all_results.append(row)
            dirs.append(dest)
    if args.one:
        return
    assert len(all_results) == 15
    merge = [args.tools/"llvm-profdata","merge","--sample","--extbinary","-o",args.out/"K-AFDO-R1.prof",
             *[d/"segment.prof" for d in dirs]]
    publish(args.out/"merge.argv.json",list(map(str,merge)))
    run(merge,args.out/"merge.stdout",args.out/"merge.stderr")
    output = args.out/"K-AFDO-R1.prof"
    run([args.tools/"llvm-profdata","show","--sample",output],args.out/"merged-profile.txt",args.out/"merged-profile.stderr")
    by_load = {}
    for workload in WORKLOADS:
        entries = [r for r in all_results if r["segment"].endswith("/"+workload)]
        before, after, reasons = Counter(), Counter(), Counter()
        for row in entries:
            before.update(row["before"])
            after.update(row["after"])
            reasons.update(row["decisions"])
        changes = sorted(((name,after[name]-before[name]) for name in set(before)|set(after)),key=lambda x:(-x[1],x[0]))
        by_load[workload] = dict(kernel=sum(r["kernel"] for r in entries),shadow=sum(r["shadow"] for r in entries),
              reasons=dict(reasons),before_top30=before.most_common(30),after_top30=after.most_common(30),
              highest_gains=changes[:30],largest_losses=changes[-30:][::-1],
              usable_c_line_lower=sum(r["usable_c_line_lower"] for r in entries))
    compact = [{k:v for k,v in r.items() if k not in ("before","after")} for r in all_results]
    publish(args.out/"r1-statistics.json",dict(segments=compact,workloads=by_load,
        profile_sha256=digest(output),baseline_profile_sha256=digest(args.training/"linux-rpi-k1e.prof"),
        ambiguous_upper=sum(r["ambiguity_upper"] for r in all_results),usable=sum(r["usable"] for r in all_results),
        baseline_usable=sum(r["baseline_usable"] for r in all_results)))


if __name__ == "__main__":
    main()
