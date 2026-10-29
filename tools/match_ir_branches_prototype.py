#!/usr/bin/env python3
"""Pre-freeze prototype, not a general LLVM IR parser or a quality metric.

Match weighted br/switch successors by function + resolved DILocation + index.
Keep inlinedAt, scope, file, discriminator and column; reject ambiguous keys.
Inputs must be a single module dump after the requested pass. No fuzzy matching.
All outputs are JSON on stdout; caller chooses an in-workspace destination.
"""
import argparse
import collections
import json
import re
from pathlib import Path


def parse(path):
    text = Path(path).read_text()
    if text.count('; *** IR Dump After') != 1:
        raise ValueError('Expected exactly one pass/module dump')
    md = dict(re.findall(r'^!(\d+) = (.*)$', text, re.M))

    def field(value, name):
        m = re.search(r'\b' + name + r': (?:!(\d+)|"([^"]*)"|(\d+))', value)
        return next((g for g in m.groups() if g is not None), None) if m else None

    def scope(idx, seen=()):
        if idx is None or idx in seen:
            return None
        value = md.get(idx, '')
        if '!DIFile(' in value:
            return ('file', field(value, 'directory'), field(value, 'filename'))
        if '!DISubprogram(' in value:
            return ('function', field(value, 'linkageName') or field(value, 'name'),
                    field(value, 'line'), scope(field(value, 'file'), seen + (idx,)))
        return ('scope', field(value, 'line'), field(value, 'column'),
                field(value, 'discriminator'), scope(field(value, 'scope'), seen + (idx,)))

    def loc(idx, seen=()):
        if idx is None or idx in seen:
            return None
        value = md.get(idx, '')
        if '!DILocation(' not in value:
            return None
        return (field(value, 'line'), field(value, 'column'),
                field(value, 'discriminator'), scope(field(value, 'scope')),
                loc(field(value, 'inlinedAt'), seen + (idx,)))

    branches = []
    function = None
    block = 'entry'
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^define .*?@("[^"]+"|[^ (]+)\(', line)
        if m:
            function, block = m[1].strip('"'), 'entry'
        if line == '}':
            function = None
        label = re.match(r'^([\w.$-]+):', line)
        if label and function:
            block = label[1]
        if function and re.match(r'\s*(br|switch)\b', line):
            start = i + 1
            while line.lstrip().startswith('switch') and ']' not in line:
                i += 1
                line += '\n' + lines[i]
            successors = re.findall(r'\blabel %([\w.$-]+)', line)
            if len(successors) > 1:
                prof = re.search(r'!prof !(\d+)', line)
                dbg = re.search(r'!dbg !(\d+)', line)
                metadata = md.get(prof[1], '') if prof else ''
                weighted = '"branch_weights"' in metadata
                weights = re.findall(r'i(?:32|64) (-?\d+)', metadata) if weighted else []
                if weighted and len(weights) != len(successors):
                    raise ValueError(f'Weights/successors mismatch at {path}:{start}')
                branches.append({'function': function, 'block': block, 'line': start,
                                 'location': loc(dbg[1]) if dbg else None,
                                 'successors': successors, 'weights': weights,
                                 'weighted': weighted, 'instruction': line.strip()})
        i += 1
    return branches


def key(branch, index):
    return json.dumps([branch['function'], branch['location'], index], sort_keys=True)


def match(left, right):
    def edges(branches, only_weighted):
        out = collections.defaultdict(list)
        for b in branches:
            if only_weighted and not b['weighted']:
                continue
            for index in range(len(b['successors'])):
                out[key(b, index)].append((b, index))
        return out
    a, b = edges(left, True), edges(right, True)
    all_a, all_b = edges(left, False), edges(right, False)
    matched = {k for k in a.keys() & b.keys()
               if len(a[k]) == len(b[k]) == 1 and a[k][0][0]['location'] is not None}
    result = {'matched_successors': len(matched), 'sides': {}}
    for name, own, other, other_all, branches in [('pgo', a, b, all_b, left),
                                                 ('sample', b, a, all_a, right)]:
        unmatched = []
        fully_matched = 0
        for branch in branches:
            if not branch['weighted']:
                continue
            keys = [key(branch, j) for j in range(len(branch['successors']))]
            if all(k in matched for k in keys):
                fully_matched += 1
            for j, k in enumerate(keys):
                if k in matched:
                    continue
                if branch['location'] is None:
                    why = 'missing DILocation'
                elif len(own[k]) > 1 or len(other.get(k, [])) > 1:
                    why = 'ambiguous repeated key; not paired arbitrarily'
                elif k in other_all:
                    why = 'same key exists but opposite branch has no branch_weights'
                else:
                    why = 'no same function/location/successor key at opposite pass boundary'
                unmatched.append({'function': branch['function'], 'block': branch['block'],
                                  'line': branch['line'], 'location': branch['location'],
                                  'successor_index': j, 'reason': why,
                                  'instruction': branch['instruction']})
        total = sum(len(v) for v in own.values())
        result['sides'][name] = {'conditional_terminators': len(branches),
            'weighted_terminators': sum(x['weighted'] for x in branches),
            'fully_matched_terminators': fully_matched,
            'weighted_successors': total,
            'matched_successors': len(matched),
            'matched_ratio': len(matched) / total if total else None,
            'unmatched': unmatched}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pgo_ir')
    parser.add_argument('sample_ir')
    args = parser.parse_args()
    print(json.dumps(match(parse(args.pgo_ir), parse(args.sample_ir)), indent=2))


if __name__ == '__main__':
    main()
