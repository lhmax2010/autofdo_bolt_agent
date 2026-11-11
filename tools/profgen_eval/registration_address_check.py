"""Q.5 synthetic-only all-address checks. Never accepts a RUN profile path.

The second key calculation below does not import the static mapper's key code.
Inputs are allowlisted static instruction records and their matching ELF files.
"""
import collections
import csv
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys

from run_scoped import WORK, platform, sha
from static_map_bridge import paths
from pack_static_evidence import tables
from apply_header_ruling import norm_file
from registration_admission import validate_generation_argv

BASE = WORK / 'docs/profgen/eval/prep/evidence'
OUT = BASE / 'registration-checks/batch1'
TEMP = WORK / 'temp/registration-batch1'
TOOL = WORK / 'temp/llvm-profgen-enh/build/bin/llvm-profgen'
TOOL_SHA = '2e8895afce661b5fdc8cacab2b3323496fca51af7bd7b51c3753aa8328b7d0d5'


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def rows(directory, glob):
    for path in sorted(directory.glob(glob)):
        with path.open() as f:
            yield from csv.DictReader(f)


def independent_key(frames, fs=False):
    """Public symbolizer JSON -> profile key; independent of mapper implementation.

Discriminator component decoding is the documented prefix encoding: low one bit
is an empty component, bit 6 selects the 12-bit rather than 5-bit payload.
"""
    if not frames or any(f['Line'] == 0 for f in frames):
        return None
    result = []
    for frame in frames[::-1]:
        if frame['FunctionName'] in ('', '<invalid>', '??'):
            break
        d = frame['Discriminator']
        base = d if fs else (0 if d & 1 else ((d >> 1) & 31 if not d & 64 else ((d >> 1) & 31) | ((d >> 7) & 127) << 5))
        result.append([frame['FunctionName'], (frame['Line']-frame['StartLine']) % 65536, base])
    return result or None


def mapped_key(frames):
    # Compare the stored address-level proof as well as the committed SQL map.
    if not frames or any(f['line'] == 0 for f in frames):
        return None
    out = []
    for f in frames[::-1]:
        if f['name'] in ('', '<invalid>'):
            break
        out.append([f['name'], (f['line']-f['start_line']) & 65535, f['base_discriminator']])
    return out or None


def key_string(key):
    return json.dumps(key, separators=(',', ':'))


def profile_entries(path):
    """Read ONLY the explicitly generated synthetic text profile in TEMP."""
    assert path.is_relative_to(TEMP) and 'synthetic' in path.name
    stack = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        depth = len(line)-len(line.lstrip(' '))
        text = line.strip()
        if not text:
            continue
        if depth == 0:
            name, total, head = text.rsplit(':', 2)
            assert total.isdecimal() and head.isdecimal(), (number, text)
            stack = [(name, None)]
            continue
        location, rest = text.split(': ', 1)
        parts = location.split('.')
        loc = [int(parts[0]), int(parts[1]) if len(parts) == 2 else 0]
        stack = stack[:depth]
        assert len(stack) == depth, (number, text, stack)
        if re.fullmatch(r'[0-9]+', rest):
            yield [([name]+call) for name, call in stack[:-1]] + [[stack[-1][0]]+loc], int(rest)
        else:
            name, count = rest.rsplit(':', 1)
            assert count.isdecimal(), (number, text)
            stack[-1] = (stack[-1][0], loc)
            stack.append((name, None))


def prepare(obj):
    assert sha(TOOL) == TOOL_SHA
    dest = OUT / (obj+'-addresses'); dest.mkdir()
    temp = TEMP / obj; temp.mkdir()
    runtime, debug = paths(obj)
    raw = WORK / 'temp/prep-static-gate' / (obj+'-map.jsonl')
    cmd = platform('readelf')+['-lW', str(runtime)]
    p = subprocess.run(cmd, text=True, capture_output=True)
    dump(dest/'program-headers.json', dict(command=cmd, exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr))
    assert p.returncode == 0
    loads = []
    for line in p.stdout.splitlines():
        fields = line.split()
        if fields and fields[0] == 'LOAD' and 'E' in fields[6:-1]:
            loads.append(tuple(int(fields[x], 16) for x in (1, 2, 4)))
    assert loads
    count = collections.Counter(); seen = set()
    query = temp/'symbolizer-addresses.txt'; perf = temp/'synthetic-all.perfscript'
    with query.open('w') as q, perf.open('w') as out, raw.open() as source:
        for line in source:
            r = json.loads(line)
            if r['kind'] == 'boundary_unavailable':
                raise ValueError(r)
            if r['kind'] != 'instruction':
                continue
            count['instruction_records'] += 1
            count['alias_queries'] += r['alias']
            q.write(hex(r['query'])+'\n')
            if r['address'] in seen:
                continue
            seen.add(r['address'])
            matches = [(o, v, n) for o, v, n in loads if v <= r['address'] < v+n]
            assert len(matches) == 1, r
            o, v, n = matches[0]
            offset = o+r['address']-v
            out.write(f"17/17 1 cycles: {r['address']:x} (/target+0x{offset:x})\n")
    count['unique_instruction_addresses'] = len(seen)
    dump(dest/'inputs.json', dict(object=obj, counts=count,
      provenance='synthetic one sample per proven instruction start; not collected data',
      inputs=[dict(path=str(x), sha256=sha(x)) for x in (raw, runtime, debug, query, perf)],
      tool_sha256=sha(TOOL)))
    print(json.dumps(count))


def symbolize(obj):
    dest = OUT/(obj+'-addresses'); temp = TEMP/obj
    _, debug = paths(obj)
    command = platform('llvm-symbolizer')+['--obj='+str(debug), '--functions=linkage', '--no-demangle', '--inlines', '--output-style=JSON', '--verbose', '--no-debuginfod']
    output = temp/'symbolizer.jsonl'
    with (temp/'symbolizer-addresses.txt').open() as inp, output.open('w') as out:
        p = subprocess.run(command, stdin=inp, stdout=out, stderr=subprocess.PIPE, text=True)
    dump(dest/'symbolizer-command.json', dict(command=command, exit_code=p.returncode,
      stderr=p.stderr, output=str(output), sha256=sha(output)))
    assert p.returncode == 0 and not p.stderr, p.stderr
    dbpath = WORK/'temp/prep-ruling3-4'/(obj+'-static.sqlite')
    db = sqlite3.connect('file:'+str(dbpath)+'?mode=ro', uri=True)
    db.execute('PRAGMA cache_size=-16384')
    cache = {}; counts = collections.Counter(); differences = []
    raw = WORK/'temp/prep-static-gate'/(obj+'-map.jsonl')
    with raw.open() as original, output.open() as independent:
        for line in original:
            r = json.loads(line)
            if r['kind'] != 'instruction':
                continue
            second = json.loads(next(independent))
            assert int(second['Address'], 16) == r['query']
            frames = second['Symbol']; a = mapped_key(r['frames_leaf_to_root']); b = independent_key(frames)
            counts['addresses_compared'] += 1
            reason = []
            if a != b:
                reason.append('key_or_exclusion_mismatch')
            if b:
                # No sharing of normalized filename code with key calculation;
                # source normalization is separately compared to stored map values.
                f = frames[len(frames)-len(b)]
                orig = r['frames_leaf_to_root'][len(r['frames_leaf_to_root'])-len(a)] if a else None
                if orig and (f['FileName'], f['Line'], f['Discriminator']) != (orig['file'], orig['line'], orig['discriminator']):
                    reason.append('leaf_source_mismatch')
                k = key_string(b)
                if k not in cache:
                    cache[k] = [(x, n, disc) for x, n, disc in db.execute('SELECT file,line,disc FROM kv WHERE k=?', (k,))]
                if (norm_file(f['FileName']), f['Line'], b[-1][2]) not in cache[k]:
                    reason.append('key_value_not_in_registered_map')
                counts['accepted_key_addresses'] += 1
            else:
                counts['excluded_addresses'] += 1
            if reason:
                differences.append(dict(reasons=reason, original=r, independent=second, old_key=a, independent_key=b))
        assert not independent.read().strip()
    parts = tables(dest, 'symbolizer-differences', ['record'], ([r] for r in differences))
    dump(dest/'symbolizer-comparison.json', dict(counts=counts, differences=len(differences), parts=parts,
      map_database=str(dbpath), map_sha256=sha(dbpath), all_addresses_checked=True,
      independence='llvm-symbolizer executable; independent offset/discriminator/context key calculation; static mapper not invoked'))
    db.close()
    assert not differences, (obj, len(differences), 'see symbolizer-differences')
    print(json.dumps(counts))


def convert(obj, skid):
    assert skid in ('none', 'prev-inst') and sha(TOOL) == TOOL_SHA
    dest = OUT/(obj+'-addresses'); temp = TEMP/obj
    runtime, debug = paths(obj)
    out = temp/('synthetic-'+skid+'.proftext'); report = temp/('synthetic-'+skid+'.json')
    command = platform('llvm-profgen')[:-1]+[str(TOOL), '--ip-samples', '--allow-missing-build-id',
      '--binary='+str(runtime), '--debug-binary='+str(debug), '--binary-match-regex=^/target$',
      '--perfscript='+str(temp/'synthetic-all.perfscript'), '--format=text', '--ip-weight=sample',
      '--ip-aggregation=max', '--ip-skid='+skid, '--output='+str(out), '--quality-report='+str(report)]
    validate_generation_argv(command)
    p = subprocess.run(command, text=True, capture_output=True)
    dump(dest/(skid+'-command.json'), dict(command=command, exit_code=p.returncode, stderr=p.stderr, stdout=p.stdout,
      output=str(out), output_sha256=sha(out) if out.exists() else None,
      report=str(report), report_sha256=sha(report) if report.exists() else None))
    assert p.returncode == 0, p.stderr
    dbpath = WORK/'temp/prep-ruling3-4'/(obj+'-static.sqlite')
    db = sqlite3.connect('file:'+str(dbpath)+'?mode=ro', uri=True)
    groups = {r['name']:r for r in rows(BASE/'identity-gate'/(obj+'-groups'), 'groups-*.csv')}
    counts = collections.Counter(); differences = []; entries = []
    for key, count in profile_entries(out):
        k = key_string(key)
        vals = list(db.execute('SELECT v,status FROM kv WHERE k=?', (k,)))
        if vals:
            classification = 'mapping_table_hit'
        elif key[0][0] in groups and groups[key[0][0]]['role'] == 'known_out_of_scope':
            classification = 'known_out_of_scope'
        else:
            classification = 'unknown_name' if key[0][0] not in groups else 'unmapped_key'
            differences.append(dict(key=key, count=count, classification=classification))
        counts[classification] += 1
        entries.append([key, count, classification, [json.loads(v) for v, status in vals]])
    parts = tables(dest, skid+'-entries', ['key', 'synthetic_count', 'classification', 'map_values'], entries)
    parts += tables(dest, skid+'-differences', ['record'], ([r] for r in differences))
    dump(dest/(skid+'-classification.json'), dict(entries=sum(counts.values()), counts=counts, differences=len(differences), parts=parts))
    assert not differences, (obj, skid, differences[:3])
    print(json.dumps(counts))


if __name__ == '__main__':
    globals()[sys.argv[1]](*sys.argv[2:])
