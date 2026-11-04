#!/usr/bin/env python3
"""Conservative v0.7 §5.8 semantic comparison of two single-module IR dumps.

No LLVM bindings or external commands. The old prototype inspired metadata and
br/switch text extraction only; none of its matching/zero-fill logic is reused.
Unsupported IR expressions fail closed. Weights are local relative probabilities,
never absolute execution counts. Diagnostics without an identifiable function
exclude all functions, rather than silently claiming profile coverage.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re


class Unverified(ValueError):
    pass


def split(text):
    """Split commas outside nested LLVM constructs and quoted identifiers."""
    result, start, stack, quoted, escaped = [], 0, [], False, False
    for i, ch in enumerate(text):
        if quoted:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                quoted = False
        elif ch == '"':
            quoted = True
        elif ch in '([{<':
            stack.append(ch)
        elif ch in ')]}>':
            if stack:
                stack.pop()
        elif ch == ',' and not stack:
            result.append(text[start:i].strip())
            start = i + 1
    result.append(text[start:].strip())
    return result


def field(text, name):
    m = re.search(r'\b' + name + r':\s*(!\d+|"(?:\\.|[^"\\])*"|[^,)]+)', text)
    return m[1].strip() if m else None


def ident(text):
    return text.lstrip('%@').strip('"')


class Module:
    def __init__(self, text):
        if text.count('; *** IR Dump After') > 1:
            raise ValueError('Expected a single module dump, not concatenated passes')
        self.md = dict(re.findall(r'^!(\d+) = (.*)$', text, re.M))
        self.diagnostics = "\n".join(line for line in text.splitlines()
                                     if re.search(r"(?:^|: )(?:warning|remark|error):|^\(\d+/\d+\) of callsites", line))
        self.functions = {}
        self.branches = []
        fn = None
        block = 'entry'
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            m = re.match(r'define\b.*?@("[^"]+"|[^ (]+)\((.*?)\)\s', line)
            if m:
                name = ident(m[1])
                if name in self.functions:
                    raise ValueError('Duplicate function definition: ' + name)
                fn = {'name': name, 'args': {}, 'defs': {}, 'first': {}}
                self.functions[name] = fn
                for n, arg in enumerate(split(m[2])):
                    a = re.search(r'(%(?:"[^"]+"|[\w.$-]+))$', arg)
                    t = re.match(r'(i\d+|ptr|float|double)\b', arg)
                    if a and t:
                        fn['args'][a[1]] = (n, t[1])
                block = 'entry'
            elif line.startswith('define '):
                raise ValueError('Unsupported function header: ' + line)
            elif line == '}':
                fn = None
            elif fn:
                m = re.match(r'("[^"]+"|[\w.$-]+):', line)
                if m:
                    block = ident(m[1])
                    continue
                while line.startswith('switch ') and ']' not in line and i < len(lines):
                    line += ' ' + lines[i].strip()
                    i += 1
                dbg = re.search(r'!dbg !(\d+)', line)
                loc = self.location(dbg[1]) if dbg else None
                if loc is not None and block not in fn['first']:
                    fn['first'][block] = loc
                d = re.match(r'(%(?:"[^"]+"|[\w.$-]+)) = (.*)', line)
                if d:
                    fn['defs'][d[1]] = re.split(r',\s*![\w.]+\s*!', d[2])[0]
                if line.startswith(('br i1 ', 'switch ')):
                    self.branches.append(self.branch(fn, block, line, loc, i))

        if fn is not None:
            raise ValueError('Unterminated function in IR dump')
        if not self.functions:
            raise ValueError('No function definitions in IR dump')

    def scope(self, ref, seen=()):
        if not ref:
            return None
        idx = ref.lstrip('!')
        if idx in seen:
            raise ValueError('Cyclic scope metadata')
        text = self.md.get(idx, '')
        m = re.search(r'!(DI\w+)\(', text)
        if not m:
            raise ValueError('Missing/unsupported scope metadata: ' + ref)
        keys = ('name', 'linkageName', 'filename', 'directory', 'line', 'column',
                'discriminator', 'scopeLine')
        scalars = tuple((key, field(text, key)) for key in keys if field(text, key) is not None)
        return (m[1], scalars, self.scope(field(text, 'file'), seen + (idx,)),
                self.scope(field(text, 'scope'), seen + (idx,)))

    def location(self, idx, seen=()):
        if idx in seen:
            raise ValueError('Cyclic inlinedAt metadata')
        text = self.md.get(idx, '')
        if '!DILocation(' not in text:
            raise ValueError('Missing DILocation: ' + idx)
        inline = field(text, 'inlinedAt')
        return (tuple((k, field(text, k)) for k in
                      ('line', 'column', 'discriminator', 'isImplicitCode', 'atomGroup', 'atomRank')),
                self.scope(field(text, 'scope')),
                self.location(inline[1:], seen + (idx,)) if inline else None)

    def branch(self, fn, block, line, loc, lineno):
        labels = [ident(x) for x in re.findall(r'label\s+(%(?:"[^"]+"|[\w.$-]+))', line)]
        p = re.search(r'!prof !(\d+)', line)
        meta = self.md.get(p[1], '') if p else ''
        weights = [int(v) % (1 << int(bits)) for bits, v in re.findall(r'i(32|64)\s+(-?\d+)', meta)]
        b = dict(function=fn['name'], block=block, line=lineno, location=loc,
                 successors=labels, weights=weights if '"branch_weights"' in meta else None,
                 expected='"expected"' in meta, raw=line)
        if line.startswith('br '):
            b.update(shape='br', type='i1', selector=line[6:].split(',')[0].strip(), cases=None)
        else:
            m = re.match(r'switch\s+(i\d+)\s+([^,]+),', line)
            if not m:
                raise ValueError('Unsupported switch syntax: ' + line)
            cases = re.findall(r'(i\d+)\s+(-?\d+)\s*,\s*label', line.split('[', 1)[1].split(']', 1)[0])
            b.update(shape='switch', type=m[1], selector=m[2].strip(),
                     cases=[('default',)] + [(t, int(v) % (1 << int(t[1:]))) for t, v in cases])
        return b

    def expression(self, fn, typ, value, depth):
        if depth < 0:
            raise Unverified('depth_limit')
        if value in ('undef', 'poison'):
            raise Unverified('undef_or_poison')
        if value in fn['args']:
            n, argtype = fn['args'][value]
            if argtype != typ:
                raise Unverified('operand_type')
            return ('arg', typ, n)
        if re.fullmatch(r'-?\d+|true|false', value) and re.fullmatch(r'i\d+', typ):
            n = {'true': 1, 'false': 0}.get(value)
            n = int(value) if n is None else n
            return ('constant', typ, n % (1 << int(typ[1:])))
        if value == 'null' and typ == 'ptr':
            return ('constant', typ, 'null')
        if value not in fn['defs']:
            raise Unverified('unsupported_leaf')
        text = fn['defs'][value]
        op = text.split()[0]
        if op in ('load', 'call', 'invoke', 'phi') or op in ('tail', 'musttail', 'notail'):
            raise Unverified('unsupported_' + op)
        binary = {'add', 'sub', 'mul', 'udiv', 'sdiv', 'urem', 'srem', 'shl', 'lshr', 'ashr', 'and', 'or', 'xor'}
        casts = {'trunc', 'zext', 'sext', 'bitcast'}
        expr = lambda t, v: self.expression(fn, t, v, depth - 1)
        if op in binary or op == 'icmp':
            parts = text.split(None, 1)[1]
            tokens = parts.split()
            typeidx = next((n for n, token in enumerate(tokens) if re.fullmatch(r'i\d+', token)), None)
            if typeidx is None:
                raise Unverified('unsupported_type')
            flags, itype = tuple(tokens[:typeidx]), tokens[typeidx]
            if op == 'icmp':
                if len(flags) != 1 or flags[0] not in INVERSE:
                    raise Unverified('unsupported_predicate')
            elif any(f not in ('nsw', 'nuw', 'exact', 'disjoint') for f in flags):
                raise Unverified('unsupported_flags')
            args = split(' '.join(tokens[typeidx + 1:]))
            if len(args) != 2 or typ != ('i1' if op == 'icmp' else itype):
                raise Unverified('operand_type_or_arity')
            return (op, typ, tuple(sorted(flags)), itype, *(expr(itype, a) for a in args))
        if op in casts:
            m = re.fullmatch(r'\w+ (i\d+) (.+) to (i\d+)', text)
            if not m or typ != m[3]:
                raise Unverified('unsupported_cast')
            return (op, typ, expr(m[1], m[2]))
        if op == 'select':
            parts = split(text[7:])
            if len(parts) != 3:
                raise Unverified('operand_arity')
            vals = []
            for part in parts:
                m = re.fullmatch(r'(i\d+) (.+)', part)
                if not m:
                    raise Unverified('unsupported_select')
                vals.append(expr(m[1], m[2]))
            if vals[0][1] != 'i1' or any(v[1] != typ for v in vals[1:]):
                raise Unverified('operand_type')
            return ('select', typ, *vals)
        raise Unverified('unsupported_' + op)


INVERSE = dict(eq='ne', ne='eq', ugt='ule', uge='ult', ult='uge', ule='ugt',
               sgt='sle', sge='slt', slt='sge', sle='sgt')


def normalized_condition(expr):
    invert = False
    while expr[0] == 'xor' and expr[1] == 'i1' and not expr[2]:
        a, b = expr[-2:]
        if b == ('constant', 'i1', 1):
            expr, invert = a, not invert
        elif a == ('constant', 'i1', 1):
            expr, invert = b, not invert
        else:
            break
    if invert and expr[0] == 'icmp':
        return (*expr[:2], (INVERSE[expr[2][0]],), *expr[3:])
    return ('not', expr) if invert else expr


def diagnostics_exclusions(module, texts):
    excluded = defaultdict(list)
    for text in texts:
        for line in text.splitlines():
            # LLVM's staleness summary also prints when both losses are zero.
            summary = re.search(r"\((\d+)/\d+\) of callsites' profile are invalid and \((\d+)/\d+\) of samples are discarded due to callsite location mismatch\.", line)
            if summary and int(summary[1]) == int(summary[2]) == 0:
                continue
            if not re.search(r'(?i)(profile|profiling|sample).*(mismatch|unmatch|out.of.date|discard|ignor|missing|not found|not available|invalid|unknown function)|unprofiled|no profile data', line):
                continue
            names = [n for n in module.functions if
                     re.search(r"[\"'@]" + re.escape(n) + r"[\"'( ]", line) or
                     re.search(r"(?:Profile in |function |Func )" + re.escape(n) + r"(?:\s|$)", line) or
                     re.search(r"\s" + re.escape(n) + r" Hash =", line)]
            for name in names or list(module.functions):
                excluded[name].append(line)
    return dict(excluded)


def compare(reference, sample, depth=16, diagnostics=()):
    diagnostics = [*diagnostics, reference.diagnostics, sample.diagnostics]
    excluded = diagnostics_exclusions(reference, diagnostics)
    for name, reasons in diagnostics_exclusions(sample, diagnostics).items():
        excluded.setdefault(name, []).extend(reasons)
    def group(module):
        groups = defaultdict(list)
        for b in module.branches:
            groups[(b['function'], b['location'])].append(b)
        return groups
    a, b = group(reference), group(sample)
    candidates, matches, failures = [], [], []
    for key in sorted(set(a) | set(b), key=repr):
        aa, bb = a.get(key, []), b.get(key, [])
        item = {'function': key[0], 'location': key[1], 'reference_lines': [x['line'] for x in aa], 'sample_lines': [x['line'] for x in bb]}
        reason = None
        if key[0] in excluded:
            reason = 'function_excluded'
        elif key[1] is None:
            reason = 'missing_location'
        elif len(aa) > 1 or len(bb) > 1:
            reason = 'duplicate_key'
        elif not aa or not bb:
            reason = 'no_candidate'
        else:
            candidates.append(dict(item))
            x, y = aa[0], bb[0]
            try:
                if x['shape'] != y['shape']:
                    raise Unverified('different_shape')
                if x['weights'] is None or y['weights'] is None:
                    raise Unverified('unknown_weights')
                if x['expected'] or y['expected']:
                    raise Unverified('expected_weights')
                if any(len(z['weights']) != len(z['successors']) for z in (x, y)):
                    raise Unverified('weight_arity')
                if x['type'] != y['type']:
                    raise Unverified('selector_width')
                ex = reference.expression(reference.functions[key[0]], x['type'], x['selector'], depth)
                ey = sample.expression(sample.functions[key[0]], y['type'], y['selector'], depth)
                if x['shape'] == 'br':
                    ex, ey = normalized_condition(ex), normalized_condition(ey)
                    if ex == ey:
                        pairing = [0, 1]
                    elif (ex[0] == ey[0] == 'icmp' and ex[:2] == ey[:2] and ex[3:] == ey[3:]
                          and INVERSE[ex[2][0]] == ey[2][0]):
                        pairing = [1, 0]
                    else:
                        raise Unverified('condition_not_equivalent')
                else:
                    if ex != ey:
                        raise Unverified('selector_not_equivalent')
                    if any(c != ('default',) and c[0] != z['type'] for z in (x, y) for c in z['cases']):
                        raise Unverified('case_width')
                    if any(len(set(z['cases'])) != len(z['cases']) for z in (x, y)) or set(x['cases']) != set(y['cases']):
                        raise Unverified('case_set')
                    pairing = [y['cases'].index(case) for case in x['cases']]
                fx = reference.functions[key[0]]['first']; fy = sample.functions[key[0]]['first']
                lx = [fx.get(s) for s in x['successors']]; ly = [fy.get(s) for s in y['successors']]
                if None in lx or None in ly:
                    raise Unverified('successor_location_missing')
                if len(set(lx)) != len(lx) or len(set(ly)) != len(ly):
                    raise Unverified('successor_location_duplicate')
                if any(lx[i] != ly[j] for i, j in enumerate(pairing)):
                    raise Unverified('successor_location_mismatch')
                rx, ry = sum(x['weights']), sum(y['weights'])
                errors = None if not rx or not ry else [y['weights'][j] / ry - x['weights'][i] / rx for i, j in enumerate(pairing)]
                matches.append(dict(item, successor_pairing=pairing, reference_weights=x['weights'], sample_weights=y['weights'],
                                    probability_errors=errors, absolute_probability_errors=None if errors is None else list(map(abs, errors)),
                                    probability_exclusion='reference_zero_total' if not rx else 'sample_zero_total' if not ry else None))
            except Unverified as e:
                reason = str(e)
        if reason:
            failures.append(dict(item, reason=reason))
    raw_r, raw_s = len(reference.branches), len(sample.branches)
    nr = sum(x['function'] not in excluded for x in reference.branches)
    ns = sum(x['function'] not in excluded for x in sample.branches)
    return dict(schema_version=1, candidate_pairs=candidates, strict_pairs=matches, semantic_unverified=failures,
                reason_counts=dict(sorted(Counter(x['reason'] for x in failures).items())),
                unverified_terminators_by_reason={side: {reason: sum(len(x[side+'_lines']) for x in failures if x['reason']==reason) for reason in sorted({x['reason'] for x in failures})} for side in ['reference','sample']},
                conditional_terminators={'reference': raw_r, 'sample': raw_s},
                eligible_terminators={'reference': nr, 'sample': ns},
                strict_ratios={'reference': len(matches)/raw_r if raw_r else None, 'sample': len(matches)/raw_s if raw_s else None},
                eligible_strict_ratios={'reference': len(matches)/nr if nr else None, 'sample': len(matches)/ns if ns else None},
                probability_denominator=sum(x['probability_errors'] is not None for x in matches),
                excluded_functions=excluded, depth_limit=depth,
                note='Structural coverage only; branch weight sums are not execution counts.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('reference', type=Path); p.add_argument('sample', type=Path)
    p.add_argument('--depth-limit', type=int, default=16)
    p.add_argument('--diagnostics', type=Path, action='append', default=[])
    a = p.parse_args()
    if a.depth_limit < 0:
        p.error('depth-limit must be nonnegative')
    try:
        result = compare(Module(a.reference.read_text()), Module(a.sample.read_text()), a.depth_limit,
                         [f.read_text() for f in a.diagnostics])
    except ValueError as e:
        p.error(str(e))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
