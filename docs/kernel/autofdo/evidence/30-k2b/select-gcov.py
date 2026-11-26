#!/usr/bin/env python3
from bisect import bisect_right
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys

work, previous, source = map(Path, sys.argv[1:])
build_prefix = '/home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/'
by_key = defaultdict(set)
by_context = defaultdict(set)
by_root = defaultdict(set)
sections = []
map_input = previous / 'link-maps/kbase-input-sections.json'
for entry in json.loads(map_input.read_text()):
    match = re.fullmatch(r'vmlinux\.a\((.+)\.o\)', entry['object'])
    if not match or not entry['bytes'] or '.text' not in entry['output']:
        continue
    relative = Path(match[1])
    kinds = [ext for ext in ('.c', '.S', '.s') if (source / (str(relative) + ext)).is_file()]
    if len(kinds) == 1:
        sections.append((entry['address'], entry['address'] + entry['bytes'], (str(relative.parent), kinds[0])))
sections.sort()
assert all(a[1] <= b[0] for a, b in zip(sections, sections[1:]))
starts = [section[0] for section in sections]

def attribution(frame):
    for field in ('StartFileName', 'FileName'):
        filename = frame[field].removeprefix(build_prefix)
        path = Path(filename)
        if path.suffix in {'.c', '.S', '.s'} and (source / path).is_file():
            return (str(path.parent), path.suffix)
    return ('?', '?')

merge = json.loads((previous / 'merge.argv.json').read_text())
inputs = [previous / Path(argument).relative_to(previous).parent / 'symbolized-accepted.jsonl'
          for argument in merge[merge.index('-o') + 2:]]
assert len(inputs) == 15, len(inputs)
for path in inputs:
    for line in path.open():
        symbolized = json.loads(line)
        frames = symbolized['Symbol'][::-1]
        if not frames or not all(f['Line'] and f['FunctionName'] not in ('', '<invalid>') for f in frames):
            continue
        dwarf = attribution(frames[0])
        ip = int(symbolized['Address'], 16)
        index = bisect_right(starts, ip) - 1
        if index >= 0 and ip < sections[index][1]:
            unit = sections[index][2]
            if dwarf[1] != '?' and dwarf[1] != unit[1]:
                raise ValueError((symbolized['Address'], dwarf, unit))
        else:
            unit = dwarf
        frames = [(f['FunctionName'], (f['Line'] - f['StartLine']) & 0xffff, f['Discriminator']) for f in frames]
        name, offset, discriminator = frames[0]
        by_root[name].add(unit)
        context = (name,)
        for index, (name, offset, discriminator) in enumerate(frames[:-1]):
            context += ((offset, discriminator), frames[index + 1][0])
        by_context[context].add(unit)
        _, offset, discriminator = frames[-1]
        by_key[context + ((offset, discriminator),)].add(unit)

totals = Counter()
directories = Counter()
fallback = Counter()
unknown = Counter()
context = []
for line in (work / 'k1e.profile.txt').read_text().splitlines():
    root = re.fullmatch(r'(.+):(\d+):(\d+)', line) if not line.startswith(' ') else None
    if root:
        context = [(root[1],)]
        continue
    body = re.fullmatch(r'( +)(\d+)(?:\.(\d+))?: (.*)', line)
    if not body:
        continue
    level = len(body[1]) - 1
    position = (int(body[2]), int(body[3] or 0))
    context = context[:level + 1]
    hit = re.match(r'(\d+)(?:$| )', body[4])
    if not hit:
        inline = re.fullmatch(r'(.+):(\d+)', body[4])
        if not inline:
            raise ValueError(line)
        context.append(context[-1] + (position, inline[1]))
        continue
    weight = int(hit[1])
    key = context[-1] + (position,)
    for method, options in [('line', by_key.get(key)), ('context', by_context.get(context[-1])), ('root', by_root.get(context[-1][0]))]:
        if options:
            break
    else:
        method, options = 'unmapped', {('?', '?')}
    source_kinds = {kind for _, kind in options}
    if source_kinds == {'.c'}:
        totals['C'] += weight
        if len(options) == 1:
            directories[next(iter(options))[0]] += weight
            fallback[method] += weight
        else:
            totals['ambiguous_C_directory'] += weight
    elif source_kinds <= {'.S', '.s'}:
        totals['assembly'] += weight
    else:
        totals['unknown_or_mixed'] += weight
        unknown[(context[-1][0], tuple(sorted(options)))] += weight

mandatory = ['kernel/sched', 'kernel/locking', 'fs', 'mm']
selected = dict.fromkeys(mandatory)
ceiling_denominator = totals["C"] + totals["unknown_or_mixed"]
covered = sum(directories[directory] for directory in selected)
for directory, weight in directories.most_common():
    if covered * 10 >= ceiling_denominator * 9:
        break
    if directory not in selected:
        selected[directory] = None
        covered += weight
if covered * 10 < ceiling_denominator * 9:
    raise SystemExit('Cannot identify enough C sample weight')
assert all((source / d / 'Makefile').is_file() for d in selected)
report = {'weight_basis': 'sum of merged LLVM profile line-body counts, including inline contexts',
          'selection_unit': 'exact directory of outer C compilation unit',
          'total': dict(totals), 'attribution': dict(fallback),
          'directories': directories.most_common(), 'selected': {d: directories[d] for d in selected},
          'covered': covered, 'coverage_known_C': covered/totals['C'],
          'coverage_lower_bound': covered/ceiling_denominator, 'link_map_compilation_unit_intervals': len(sections),
          'symbolization_inputs': [str(path.relative_to(previous)) for path in inputs],
          'unattributed': [[name, attribution, weight] for (name, attribution), weight in unknown.most_common()]}
(work / 'selection.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k != 'directories'}, indent=2))
