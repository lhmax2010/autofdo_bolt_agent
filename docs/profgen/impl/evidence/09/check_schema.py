#!/usr/bin/env python3
"""Compare RST field inventory with actual lit reports; no build/network needed."""
import argparse
import json
from pathlib import Path
import re


def paths(value, prefix='', found=None):
    if found is None:
        found = set()
    if prefix:
        found.add(prefix)
    assert value != '', ('empty string value', prefix)
    if isinstance(value, dict):
        for key, child in value.items():
            paths(child, prefix + '.' + key if prefix else key, found)
    elif isinstance(value, list):
        for child in value:
            paths(child, prefix + '[]', found)
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('guide', type=Path)
    ap.add_argument('lit_output', type=Path)
    ap.add_argument('result', type=Path)
    args = ap.parse_args()
    documented = set(re.findall(r'^``([^`]+)`` \(', args.guide.read_text(), re.M))
    observed, inputs = set(), []
    for file in sorted(args.lit_output.rglob('report.json')):
        value = json.loads(file.read_text())
        if value.get('schema_version') != 1:
            continue  # Deliberately preserved old reports in I/O/path negatives.
        observed.update(paths(value))
        inputs.append(str(file))
    result = {'documented_paths': sorted(documented),
              'observed_paths': sorted(observed),
              'undocumented_paths': sorted(observed - documented),
              'documented_but_unobserved_paths': sorted(documented - observed),
              'report_count': len(inputs), 'reports': inputs,
              'empty_string_values': 0}
    args.result.write_text(json.dumps(result, indent=2) + '\n')
    assert inputs and observed == documented, result
    print(f'{len(inputs)} reports, {len(observed)} paths; both differences empty')


if __name__ == '__main__':
    main()
