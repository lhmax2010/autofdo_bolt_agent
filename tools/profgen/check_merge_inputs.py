#!/usr/bin/env python3
"""Check schema-1 IP reports before suggesting a sample-profile merge.

No subprocess/network calls. Reports are supplied by the caller; this does not
prove a report belongs to the supplied profile or certify unverified identities.
Example: --input a.prof a.json 1 --input b.prof b.json 2 --output merged.prof
"""
import argparse
import json
from pathlib import Path
import re
import shlex
import sys

FIELDS = (
    'event.selected', 'semantics.weight', 'semantics.p_ref',
    'semantics.p_ref_source', 'semantics.aggregation', 'semantics.head_samples',
    'semantics.zero_fill', 'semantics.skid', 'identity.binary_build_id',
    'identity.grade',
)


def get(report, path):
    value = report
    for key in path.split('.'):
        value = value[key]
    return value


def output_options(args):
    """Read LLVM option spelling; defaults match profgen 22.1.8 patch 7."""
    if not isinstance(args, list) or any(a is not None and not isinstance(a, str) for a in args):
        raise ValueError('tool.arguments must be an argv array')
    fmt, md5 = 'extbinary', False
    i = 1
    while i < len(args):
        arg = args[i] or ''
        key, sep, value = arg.lstrip('-').partition('=')
        if arg.startswith('-') and key == 'format':
            if not sep:
                i += 1
                value = args[i] if i < len(args) else None
            if value not in ('text', 'binary', 'extbinary'):
                raise ValueError('unknown profile format: ' + repr(value))
            fmt = value
        elif arg.startswith('-') and key == 'use-md5':
            if not sep:
                md5 = True
            elif value in ('true', '1', 'false', '0'):
                md5 = value in ('true', '1')
            else:
                raise ValueError('invalid use-md5 value: ' + repr(value))
        i += 1
    return {'format': fmt, 'use_md5_requested': md5,
            'use_md5_effective': md5 and fmt == 'extbinary'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', nargs=3, action='append', required=True,
                   metavar=('PROFILE', 'REPORT', 'WEIGHT'))
    p.add_argument('--output', required=True)
    p.add_argument('--llvm-profdata', default='llvm-profdata')
    ns = p.parse_args()
    errors, rows = [], []
    for index, (profile, report, weight) in enumerate(ns.input, 1):
        tag = f'input[{index}]'
        if not re.fullmatch(r'[0-9]+', weight) or int(weight) == 0:
            errors.append(f'{tag}.weight: expected positive integer, got {weight!r}')
        elif int(weight) > 18446744073709551615:
            errors.append(f'{tag}.weight: exceeds llvm-profdata uint64 limit')
        if not Path(profile).is_file():
            errors.append(f'{tag}.profile: not a file: {profile}')
        try:
            j = json.loads(Path(report).read_text())
            if j.get('schema_version') != 1:
                errors.append(f'{tag}.schema_version: expected 1')
            if get(j, 'verdict.conversion') != 'ok':
                errors.append(f'{tag}.verdict.conversion: {get(j, "verdict.conversion")!r}, expected ok')
            row = {}
            for field in FIELDS:
                try:
                    value = get(j, field)
                    if value in ('unknown', '') or (value is None and field != 'identity.binary_build_id'):
                        errors.append(f'{tag}.{field}: unavailable value {value!r}')
                    row[field] = value
                except (KeyError, TypeError):
                    errors.append(f'{tag}.{field}: missing field')
            row.update(output_options(get(j, 'tool.arguments')))
            rows.append((index, row))
        except (OSError, ValueError, KeyError, TypeError) as e:
            errors.append(f'{tag}.report: {e}')
    if rows:
        ref_index, ref = rows[0]
        for index, row in rows[1:]:
            for key in sorted(ref.keys() | row.keys()):
                if key not in row or key not in ref or row[key] != ref[key]:
                    errors.append(f'input[{index}].{key}: {row.get(key)!r} != input[{ref_index}] {ref.get(key)!r}')
    if errors:
        for error in errors:
            print('REJECT: ' + error, file=sys.stderr)
        return 1
    cmd = [ns.llvm_profdata, 'merge', '--sample', '--' + rows[0][1]['format']]
    if rows[0][1]['use_md5_effective']:
        cmd.append('--use-md5')
    cmd += [f'--weighted-input={int(weight)},{profile}' for profile, _, weight in ns.input]
    cmd += ['-o', ns.output]
    print(shlex.join(cmd))
    return 0


if __name__ == '__main__':
    sys.exit(main())
