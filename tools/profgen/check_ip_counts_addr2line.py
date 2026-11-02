#!/usr/bin/env python3
"""Independent IP count oracle: GBS GNU addr2line + GNU readelf, not profgen frames.

Run with --prepare-only before the new profgen exists; without it, compare every
body/total/head field to newly generated text profiles. All scratch stays in temp.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

W = Path(__file__).resolve().parents[2]
L = W / 'temp/llvm-profgen-enh'
I = L / 'llvm/test/tools/llvm-profgen/Inputs/ip-mode'
A = W / 'temp/GBS-ROOT-RPI5-SPIKE/local/BUILD-ROOTS/scratch.aarch64.0/emul'
B = W / 'temp/GBS-ROOT-V04-FFMPEG/local/BUILD-ROOTS/scratch.armv7l.0/emul'
R = W / 'temp/GBS-ROOT-LLVM-X86/local/BUILD-ROOTS/scratch.x86_64.0'


def platform(root, tool):
    return ['nice', '-n', '19', 'ionice', '-c3',
            str(root / 'lib64/ld-linux-x86-64.so.2'), '--library-path',
            f'{root}/lib64:{root}/usr/lib64', str(root / 'usr/bin' / tool)]


def run(argv):
    p = subprocess.run(argv, cwd=W, text=True, capture_output=True)
    if p.returncode:
        raise RuntimeError(f'{argv!r}\nexit={p.returncode}\n{p.stderr}')
    return p.stdout


def declarations(info):
    result = {}
    for block in re.split(r'(?m)^\s*<\d+><[0-9a-f]+>:', info):
        if '(DW_TAG_subprogram)' not in block:
            continue
        attrs = {}
        for line in block.splitlines():
            m = re.search(r'DW_AT_(linkage_name|name|decl_line)\s*:\s*(.*)', line)
            if m:
                attrs[m[1]] = m[2].split('): ', 1)[-1].strip()
        if 'decl_line' in attrs:
            result[attrs.get('linkage_name', attrs.get('name'))] = int(attrs['decl_line'])
    return result


def decode_discriminator(d, fs=False):
    # LLVM prefix encoding, independently evaluated from raw GNU line info.
    # A low 1 bit encodes zero; otherwise a 7/14-bit component follows.
    def component(v):
        if v & 1:
            return 0, v >> 1
        if v & 0x40:
            u = v >> 1
            return ((u >> 1) & 0xfe0) | (u & 0x1f), v >> 14
        return (v >> 1) & 0x1f, v >> 7
    if fs:
        return d, 1
    base, rest = component(d)
    duplication, _ = component(rest)
    return base, duplication or 1


def frames(text, decl):
    result = {}
    chunks = re.split(r'(?m)^(0x[0-9a-f]+)\s*$', text)
    for j in range(1, len(chunks), 2):
        address = int(chunks[j], 16)
        lines = chunks[j + 1].strip().splitlines()
        chain = []
        for k in range(0, len(lines), 2):
            name, where = lines[k:k + 2]
            m = re.search(r':(\d+)(?: \(discriminator (\d+)\))?$', where)
            if not m or name not in decl or int(m[1]) == 0:
                raise ValueError((name, where, decl))
            chain.append((name, (int(m[1]) - decl[name]) & 0xffff, int(m[2] or 0)))
        result[address] = list(reversed(chain))
    return result



def apply_call_discriminators(stacks, info, ranges_text, decl):
    """GNU addr2line omits DW_AT_GNU_discriminator on inline caller frames.

    Recover it from GNU readelf, independently of LLVM's symbolizer. These
    fixtures use DWARF4 relative high_pc or .debug_ranges; reject unknown forms.
    """
    ranges = {}
    for line in ranges_text.splitlines():
        m = re.fullmatch(r'\s*([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s*', line)
        if m:
            ranges.setdefault(int(m[1], 16), []).append((int(m[2], 16), int(m[3], 16)))
    dies = {}
    for m in re.finditer(r'(?ms)^\s*<\d+><([0-9a-f]+)>:([^\n]*)(.*?)(?=^\s*<\d+><|\Z)', info):
        attrs = {}
        for a in re.finditer(r'DW_AT_(\w+)\s*:\s*([^\n]+)', m[3]):
            attrs[a[1]] = a[2].split('): ', 1)[-1].strip()
        dies[int(m[1], 16)] = (m[2], attrs)
    for tag, attrs in dies.values():
        if 'DW_TAG_inlined_subroutine' not in tag:
            continue
        origin = int(attrs['abstract_origin'].strip('<>'), 16)
        original = dies[origin][1]
        name = original.get('linkage_name', original.get('name'))
        disc = int(attrs.get('GNU_discriminator', '0'), 0)
        if 'ranges' in attrs:
            intervals = ranges[int(attrs['ranges'], 0)]
        else:
            low = int(attrs['low_pc'], 0)
            intervals = [(low, low + int(attrs['high_pc'], 0))]
        for address, chain in stacks.items():
            if not any(a <= address < b for a, b in intervals):
                continue
            matches = [i for i in range(1, len(chain))
                       if chain[i][0] == name and chain[i - 1][1] ==
                       ((int(attrs['call_line']) - decl[chain[i - 1][0]]) & 0xffff)]
            if len(matches) != 1:
                raise ValueError(('ambiguous inline DIE', address, attrs, chain))
            i = matches[0] - 1
            chain[i] = (chain[i][0], chain[i][1], disc)


def node():
    return {'total': 0, 'head': 0, 'body': {}, 'calls': {}}


def oracle(samples, stacks, mode, unit, head, fs=False):
    tree = {}
    for address, period in samples:
        chain = stacks[address]
        current = tree.setdefault(chain[0][0], node())
        current['total'] += period
        for i in range(1, len(chain)):
            parent = chain[i - 1]
            loc = (parent[1], decode_discriminator(parent[2], fs)[0])
            current = current['calls'].setdefault(loc, {}).setdefault(chain[i][0], node())
            current['total'] += period
        _, line, raw = chain[-1]
        base, duplication = decode_discriminator(raw, fs)
        loc = (line, base)
        old = current['body'].get(loc, 0)
        current['body'][loc] = max(old, period * duplication) if mode == 'max' else old + period
    def rounding(n):
        q, r = divmod(n, unit)
        return max(1, q + (2 * r >= unit)) if n else 0
    def materialize(n):
        n['total'] = rounding(n['total'])
        n['body'] = {k: rounding(v) for k, v in n['body'].items()}
        for children in n['calls'].values():
            for c in children.values():
                materialize(c)
    def estimate(n):
        b, c = min(n['body'], default=None), min(n['calls'], default=None)
        v = n['body'][b] if b is not None and (c is None or b < c) else (
            sum(estimate(ch) for ch in n['calls'][c].values()) if c is not None else 0)
        return v or int(n['total'] > 0)
    for n in tree.values():
        materialize(n)
        if head:
            n['head'] = estimate(n)
    return tree


def parse_profile(text):
    result, stack = {}, []
    for line in text.splitlines():
        depth = len(line) - len(line.lstrip())
        if depth == 0:
            name, total, head = line.rsplit(':', 2)
            current = node(); current.update(total=int(total), head=int(head))
            result[name] = current; stack = [current]
            continue
        m = re.fullmatch(r'\s*(\d+)(?:\.(\d+))?: (.+)', line)
        if not m:
            raise ValueError(line)
        loc = (int(m[1]), int(m[2] or 0)); value = m[3]
        parent = stack[depth - 1]
        if ':' in value:
            name, total = value.rsplit(':', 1)
            current = node(); current['total'] = int(total)
            parent['calls'].setdefault(loc, {})[name] = current
            stack = stack[:depth] + [current]
        else:
            parent['body'][loc] = int(value)
    return result


def serial(tree):
    if isinstance(tree, dict):
        return {str(k): serial(v) for k, v in sorted(tree.items(), key=lambda x: str(x[0]))}
    return tree


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument('--prepare-only', action='store_true')
    ap.add_argument('--output-dir', default=str(W / 'temp/profgen-patch4/independent'))
    args = ap.parse_args(); out = Path(args.output_dir).resolve()
    out.relative_to(W / 'temp'); out.mkdir(parents=True, exist_ok=True)
    loops = {
        'a64-pie': [0x1318, 0x131c, 0x1324, 0x1328, 0x1330, 0x1334, 0x133c, 0x1340],
        'arm-count': [0x12c8, 0x12d0, 0x12d8, 0x12dc, 0x12e0, 0x12e4, 0x12e8, 0x12ec],
        'thumb-count': [0x12be, 0x12c4, 0x12ca, 0x12ce, 0x12d2, 0x12d4, 0x12d8, 0x12da]}
    cases = [(b, list(zip(aa, [2, 6] * 4)), mode, False) for b, aa in loops.items() for mode in ['sum', 'max']]
    cases += [('a64-fs', [(0x14e8, 2)], 'sum', False),
              ('a64-pie', [(0x13b4, 10), (0x13b0, 20)], 'sum', True),
              ('counting-extra/head', [(0x12f0, 3), (0x12d8, 7), (0x1300, 100)], 'sum', True)]
    results = []
    for number, (binary, samples, mode, head) in enumerate(cases):
        root = B if binary in ('arm-count', 'thumb-count') else A
        elf = I / (binary + '.perfbin')
        info_cmd = platform(root, 'readelf') + ['--debug-dump=info', str(elf)]
        line_cmd = platform(root, 'addr2line') + ['-a', '-i', '-f', '-e', str(elf)] + [hex(a) for a, _ in samples]
        info, line = run(info_cmd), run(line_cmd)
        decl = declarations(info); stacks = frames(line, decl)
        ranges_cmd = platform(root, 'readelf') + ['--debug-dump=Ranges', str(elf)]
        ranges_text = run(ranges_cmd)
        apply_call_discriminators(stacks, info, ranges_text, decl)
        expected = oracle(samples, stacks, mode, 1, head, fs=(binary == 'a64-fs'))
        trace = out / f'{number}.perfscript'
        # All these fixtures' executable PT_LOAD has vaddr-offset=0x1000.
        phdr_cmd = platform(root, 'readelf') + ['-lW', str(elf)]
        phdr = run(phdr_cmd); offsets = []
        for address, period in samples:
            found = []
            for row in phdr.splitlines():
                cols = row.split()
                if cols and cols[0] == 'LOAD' and 'E' in cols[6:-1]:
                    offset, va, size = int(cols[1],16), int(cols[2],16), int(cols[4],16)
                    if va <= address < va + size:
                        found.append(offset + address - va)
            assert len(found) == 1
            offsets.append(found[0])
        trace.write_text(''.join(f'17/17 {p} cycles: {a:x} (/target+0x{o:x})\n' for (a,p),o in zip(samples, offsets)))
        profile = out / f'{number}.prof'
        cmd = ['nice','-n','19','ionice','-c3',str(R/'lib64/ld-linux-x86-64.so.2'),
               '--library-path', f'{L}/build/lib64:{R}/lib64:{R}/usr/lib64',str(L/'build/bin/llvm-profgen'),
               '--ip-samples','--allow-missing-build-id','--binary-match-regex=^/target$',
               '--ip-period-unit=1',f'--ip-aggregation={mode}','--format=text',
               f'--ip-head-samples={"entry-estimate" if head else "none"}',f'--binary={elf}',
               f'--perfscript={trace}',f'--output={profile}']
        record = dict(binary=binary, sha256=hashlib.sha256(elf.read_bytes()).hexdigest(),
                      mode=mode, samples=samples, declarations=decl, frames=stacks,
                      expected=serial(expected), addr2line_command=line_cmd,
                      addr2line_output=line, readelf_command=info_cmd, ranges_command=ranges_cmd,
                      ranges_output=ranges_text, phdr_command=phdr_cmd,
                      phdr_output=phdr, profgen_command=cmd)
        (out / f'{number}.readelf.txt').write_text(info)
        if not args.prepare_only:
            p = subprocess.run(cmd, cwd=W, capture_output=True, text=True)
            record.update(exit=p.returncode, stdout=p.stdout, stderr=p.stderr)
            actual = parse_profile(profile.read_text()) if p.returncode == 0 else None
            record.update(actual=serial(actual), equal=(actual == expected))
        results.append(record)
    path = out / ('prepared.json' if args.prepare_only else 'comparison.json')
    path.write_text(json.dumps(results, indent=2) + '\n')
    print(path)
    if not args.prepare_only:
        failures = [r['binary'] + '/' + r['mode'] for r in results if not r['equal']]
        print('cases', len(results), 'differences', len(failures), failures)
        return bool(failures)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
