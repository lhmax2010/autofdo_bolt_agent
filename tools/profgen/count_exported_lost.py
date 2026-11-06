#!/usr/bin/env python3
"""Independent counts of a complete strict perf script text export.

No llvm-profgen code or parser is imported. S counts every sample, including
kernel/unknown/other DSOs. An absence of LOST records is not evidence of zero
actual loss. This script reports only observed records, not recording loss.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

SAMPLE = re.compile(r'^\s*(-?\d+)/(-?\d+)\s+(\d+)\s+(\S+):\s+([0-9a-fA-F]+)\s+\((.*)\)\s*$')
LOST = re.compile(r'^\s*(-?\d+)/(-?\d+)\s+PERF_RECORD_LOST lost (\d+)\s*$')


def count(path):
    samples = records = lost = mappings = lines = 0
    events = Counter()
    unknown = []
    examples = []
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for lines, raw in enumerate(stream, 1):
            digest.update(raw)
            line = raw.decode('utf-8').rstrip('\r\n')
            match = LOST.fullmatch(line)
            if match:
                records += 1
                lost += int(match[3])
                if len(examples) < 10:
                    examples.append({'line': lines, 'raw': line})
            elif match := SAMPLE.fullmatch(line):
                samples += 1
                events[match[4]] += 1
            elif 'PERF_RECORD_MMAP ' in line or 'PERF_RECORD_MMAP2 ' in line:
                mappings += 1
            elif line.strip():
                unknown.append({'line': lines, 'raw': line})
    return dict(source=str(path), sha256=digest.hexdigest(), lines=lines,
                LOST_records=records, observed_L=lost, S=samples,
                exported_lost_ratio=({'numerator': lost,
                                      'denominator': lost + samples}
                                     if records else 'unknown'),
                sample_events=dict(sorted(events.items())), mappings=mappings,
                unknown_lines=unknown, LOST_examples=examples)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export', type=Path)
    args = parser.parse_args()
    work = Path(__file__).resolve().parents[2]
    path = args.export.resolve()
    path.relative_to(work)
    result = count(path)
    print(json.dumps(result, indent=2))
    return 1 if result['unknown_lines'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
