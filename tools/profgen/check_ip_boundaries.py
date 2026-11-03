#!/usr/bin/env python3
"""Offline IP boundary cross-check with GBS readelf/objdump, not a decoder oracle.

Requires an existing llvm-profgen launcher and a GBS emul root. All artifacts
are written below --output-dir. ELF metadata comes from the platform tools.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


def sections(text):
    result = {}
    for line in text.splitlines():
        m = re.match(r'\s*\[\s*(\d+)\]\s+(\S+)\s+(\S+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+\S+\s+(\S*)', line)
        if m:
            i, name, typ, addr, off, size, flags = m.groups()
            result[int(i)] = dict(name=name, type=typ, addr=int(addr, 16), off=int(off, 16), size=int(size, 16), flags=flags)
    return result


def symbols(text):
    result, table = [], ''
    for line in text.splitlines():
        m = re.match(r"Symbol table '([^']+)'", line)
        if m:
            table = m[1]
        fields = line.split()
        if table == '.symtab' and len(fields) >= 8 and fields[0].endswith(':') and fields[6].isdigit():
            result.append(dict(value=int(fields[1], 16), size=int(fields[2], 0), type=fields[3], bind=fields[4], section=int(fields[6]), name=fields[7]))
    return result


def parse_boundaries(text):
    result, current = {}, None
    for line in text.splitlines():
        if line.startswith('IP-BOUNDARY function='):
            current = line.split('=', 1)[1]
            result[current] = dict(ranges=[], instructions=[])
        elif line.startswith('IP-BOUNDARY range='):
            result[current]['ranges'].append([int(v, 16) for v in line.split('=', 1)[1].split(':')])
        elif line.startswith('IP-BOUNDARY instruction='):
            result[current]['instructions'].append(int(line.split('=', 1)[1].split()[0], 16))
    return result


class Runner:
    def __init__(self, output, root):
        self.output = output
        output.mkdir(parents=True, exist_ok=True)
        self.root = root
        self.commands = []

    def platform(self, name, *args):
        return [str(self.root / 'lib64/ld-linux-x86-64.so.2'), '--library-path', f'{self.root}/lib64:{self.root}/usr/lib64', str(self.root / 'usr/bin' / name), *map(str, args)]

    def run(self, label, args, check=True):
        args = ['nice', '-n', '19', 'ionice', '-c3', *map(str, args)]
        out, err = self.output / (label + '.stdout'), self.output / (label + '.stderr')
        # A lightweight launcher forks the measured child. Otherwise a large
        # parsed objdump/ELF table in this parent can inflate the child's initial
        # ru_maxrss. Only the tool child's wait4 usage is reported, not the
        # launcher's own inherited high-water mark.
        usage_path = self.output / (label + '.usage.json')
        launcher = """import json,os,sys,time
sys.excepthook=sys.__excepthook__
cmd=json.loads(sys.argv[1]); start=time.monotonic(); pid=os.fork()
if pid==0: os.execvp(cmd[0],cmd)
_,status,usage=os.wait4(pid,0)
row={'exit':os.waitstatus_to_exitcode(status),'seconds':time.monotonic()-start,'peak_rss_kib':usage.ru_maxrss}
with open(sys.argv[2],'w') as f: json.dump(row,f)
"""
        with out.open('wb') as stdout, err.open('wb') as stderr:
            proc = subprocess.run([sys.executable, '-c', launcher, json.dumps(args), str(usage_path)], stdout=stdout, stderr=stderr)
        if proc.returncode:
            raise RuntimeError(f'measurement launcher failed: {label}; {err.read_text()}')
        measured = json.loads(usage_path.read_text())
        row = dict(label=label, command=args, **measured, stdout=str(out), stderr=str(err), measurement='lightweight launcher, direct tool child wait4 rusage')
        self.commands.append(row)
        (self.output/'commands.json').write_text(json.dumps(self.commands, indent=2)+'\n')
        if check and row['exit']:
            raise RuntimeError(f"{label}: exit {row['exit']}; {err.read_text()}")
        return out.read_text()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool', type=Path, required=True)
    parser.add_argument('--platform-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--debug', type=Path, required=True)
    args = parser.parse_args()
    r = Runner(args.output_dir, args.platform_root)
    for label, path in [('runtime', args.runtime), ('debug', args.debug)]:
        notes = r.run(label+'-notes', r.platform('readelf', '-n', path))
        assert 'f960461f63c852474257f51267b7b543afffdc9c' in notes, (label, notes)
    secs = sections(r.run('sections', r.platform('readelf', '-SW', args.debug)))
    ss = symbols(r.run('symbols', r.platform('readelf', '-sW', args.debug)))
    fs, seen = [], set()
    for s in ss:
        key = (s['value'] & ~1, s['size'], s['section'])
        if s['type'] != 'FUNC' or not s['value'] & 1 or not s['size'] or 'X' not in secs.get(s['section'], {}).get('flags', '') or key in seen:
            continue
        seen.add(key)
        fs.append(dict(s, start=key[0], end=key[0]+s['size']))
    fs.sort(key=lambda f: (-f['size'], f['start'], f['name']))
    fs = fs[:20]
    assert len(fs) == 20
    ph = r.run('segments', r.platform('readelf', '-lW', args.runtime))
    loads = []
    for line in ph.splitlines():
        p = line.split()
        if p and p[0] == 'LOAD' and 'E' in p[6:-1]:
            loads.append(tuple(int(p[j], 16) for j in (1, 2, 4)))
    def offset(addr):
        matches = [off+addr-va for off,va,size in loads if va <= addr < va+size]
        assert len(matches) == 1, (addr, matches)
        return matches[0]
    merged = args.output_dir/'libavcodec.merged.so'
    r.run('merge', r.platform('eu-unstrip', '-o', merged, args.runtime, args.debug))
    # Choose each synthetic sample from objdump, independently of profgen.
    for index, f in enumerate(fs):
        dis = r.run('input-objdump-'+str(index), r.platform('llvm-objdump', '--triple=thumbv7a', '-d', '--start-address='+hex(f['start']), '--stop-address='+hex(f['end']), merged))
        choices = []
        for line in dis.splitlines():
            m = re.match(r'^\s*([0-9a-f]+):\s+([^\t]+)\t(.*)', line)
            if m and not m[3].lstrip().startswith('.') and f['start'] <= int(m[1],16) < f['end']:
                choices.append(int(m[1],16))
        assert choices and choices[0] == f['start'], f
        f['sample_address'] = choices[0]
    sample = args.output_dir/'largest20.perfscript'
    sample.write_text(''.join(f'17/17 1000003 cycles: {f["sample_address"]:x} (/target+0x{offset(f["sample_address"]):x})\n' for f in fs))
    text = r.run('largest20-profgen', [args.tool, '--ip-samples', '--allow-missing-build-id', '--binary-match-regex=^/target$', '--binary='+str(args.runtime), '--debug-binary='+str(args.debug), '--perfscript='+str(sample), '--ip-aggregation=avg', '--show-ip-boundaries', '--show-ip-address-counts', '--format=text', '--output='+str(args.output_dir/'largest20.prof')])
    bounds = parse_boundaries(text)
    results = []
    for index, f in enumerate(fs):
        b = bounds.get(f['name'])
        row = dict(function=f['name'], start=hex(f['start']), end=hex(f['end']), size=f['size'])
        dis = r.run('objdump-'+str(index), r.platform('llvm-objdump', '--triple=thumbv7a', '-d', '--start-address='+hex(f['start']), '--stop-address='+hex(f['end']), merged))
        starts = set()
        for line in dis.splitlines():
            m = re.match(r'^\s*([0-9a-f]+):\s+([^\t]+)\t(.*)', line)
            if m and not m[3].lstrip().startswith('.') and f['start'] <= int(m[1],16) < f['end']:
                starts.add(int(m[1],16))
        got = set(b['instructions']) if b else set()
        primary = {a for a in got if f['start'] <= a < f['end']}
        # ProfiledBinary groups same canonical names across CUs. Check every
        # returned DWARF range as well; never truncate the reported profile.
        all_starts = set()
        if b:
            for j, (lo, hi) in enumerate(b['ranges']):
                full = r.run(f'objdump-{index}-range-{j}', r.platform('llvm-objdump', '--triple=thumbv7a', '-d', '--start-address='+hex(lo), '--stop-address='+hex(hi), merged))
                for line in full.splitlines():
                    m = re.match(r'^\s*([0-9a-f]+):\s+([^\t]+)\t(.*)', line)
                    if m and not m[3].lstrip().startswith('.') and lo <= int(m[1],16) < hi:
                        all_starts.add(int(m[1],16))
        row.update(profiled=b is not None, ranges=b['ranges'] if b else [], profgen_count=len(got), objdump_count=len(all_starts), matches=len(all_starts & got), profgen_only=[hex(a) for a in sorted(got-all_starts)], objdump_only=[hex(a) for a in sorted(all_starts-got)], selected_symbol_count=len(primary), selected_objdump_count=len(starts), selected_matches=len(primary & starts), additional_dwarf_addresses=[hex(a) for a in sorted(got-primary)])
        results.append(row)
    summary = dict(functions=results, total_matches=sum(x['matches'] for x in results), total_profgen=sum(x['profgen_count'] for x in results), total_objdump=sum(x['objdump_count'] for x in results), reference_07_count=132859, selected_symbol_matches=sum(x['selected_matches'] for x in results), runtime_sha256=hashlib.sha256(args.runtime.read_bytes()).hexdigest(), debug_sha256=hashlib.sha256(args.debug.read_bytes()).hexdigest())
    (args.output_dir/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))
    if any(not x['profiled'] or x['selected_matches'] != x['selected_objdump_count'] or x['profgen_only'] or x['objdump_only'] for x in results):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
