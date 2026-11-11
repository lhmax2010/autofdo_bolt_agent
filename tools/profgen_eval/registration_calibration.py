"""Q.5 #5(iv): disclosed CALIBRATION baseline conversion and entry counts only.

No historical profile reader, body-weight accumulator, ratios or metrics.
A before-open disclosure is mandatory. The output parser drops all counts.
"""
import collections
import datetime
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

from registration_address_check import BASE, TOOL, TOOL_SHA, rows, key_string, dump
from registration_admission import validate_generation_argv
from registration_mapping_checks import classify_entry
from run_scoped import WORK, sha
from pack_static_evidence import tables

OUT = BASE / 'registration-checks/batch2'
TEMP = WORK / 'temp/registration-batch2'


def entry_keys(lines):
    """Parse locations/names only; numeric body values are discarded, never summed."""
    stack = []
    for number, line in enumerate(lines, 1):
        depth = len(line) - len(line.lstrip(' '))
        text = line.strip()
        if not text:
            continue
        if depth == 0:
            name, total, head = text.rsplit(':', 2)
            if not total.isdecimal() or not head.isdecimal():
                raise ValueError(('invalid_header', number))
            stack = [(name, None)]
            continue
        location, rest = text.split(': ', 1)
        parts = location.split('.')
        loc = [int(parts[0]), int(parts[1]) if len(parts) == 2 else 0]
        stack = stack[:depth]
        if len(stack) != depth:
            raise ValueError(('invalid_depth', number))
        if re.fullmatch(r'[0-9]+', rest):
            yield number, [([name]+call) for name, call in stack[:-1]] + [[stack[-1][0]]+loc]
        else:
            name, count = rest.rsplit(':', 1)
            if not count.isdecimal():
                raise ValueError(('invalid_inline', number))
            stack[-1] = (stack[-1][0], loc)
            stack.append((name, None))


def run(tag):
    disclosure = OUT/'disclosure-before.json'
    manifest = json.loads(disclosure.read_text())
    matches = [r for r in manifest['runs'] if r['tag'] == tag]
    if len(matches) != 1 or manifest['baseline'] != dict(aggregation='max',skid='none',weight='period',head_samples='none',zero_fill='none',format='text'):
        raise ValueError('not_disclosed_CALIBRATION_baseline')
    record = matches[0]; obj = record['object']
    assert sha(TOOL) == TOOL_SHA
    dest = OUT/tag; dest.mkdir()
    output = WORK/record['planned_output']
    assert output.is_relative_to(TEMP) and output.name == 'baseline.proftext'
    output.parent.mkdir(parents=True, exist_ok=False)
    inputs = [r for r in record['inputs'] if r['operation'] == 'conversion input']
    dump(dest/'opened-inputs.json', dict(time=datetime.datetime.now().astimezone().isoformat(),
      disclosure=str(disclosure),disclosure_sha256=sha(disclosure),inputs=inputs,
      operations=['SHA verification','baseline conversion'],old_profile_opened=False,perf_data_opened=False))
    for r in inputs:
        assert sha(WORK/r['path']) == r['sha256'], r['path']
    old_command = WORK/'temp/board-round1-resume2/runs'/tag/'profgen-command.json'
    original = json.loads(old_command.read_text())['command']
    command = original[original.index(str(TOOL))-3:]
    # Preserve original loader/library, exact ELF and anchored path identity options.
    replacements = dict(ip_weight='period',ip_aggregation='max',ip_head_samples='none',
      ip_zero_fill='none',ip_skid='none',format='text',output=str(output),quality_report=str(output.with_suffix('.quality.json')))
    for k, value in replacements.items():
        opt = '--'+k.replace('_','-')+'='
        assert sum(x.startswith(opt) for x in command) == 1, opt
        command = [opt+value if x.startswith(opt) else x for x in command]
    validate_generation_argv(command)
    p = subprocess.run(command,text=True,capture_output=True)
    dump(dest/'conversion.json',dict(command=command,original_command_metadata=str(old_command),
      original_command_sha256=sha(old_command),exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,
      tool_sha256=sha(TOOL),output=str(output),output_exists=output.exists()))
    if p.returncode:
        return p.returncode
    # Persist the output SHA before any semantic parsing of its entries.
    dump(dest/'before-classification.json',dict(time=datetime.datetime.now().astimezone().isoformat(),
      path=str(output),sha256=sha(output),operations=['entry keys and classification counts only'],
      quality_report_opened=False))
    names = set()
    inventory = WORK/'temp/prep-static-gate'/(obj+'-inventory.jsonl')
    with inventory.open() as f:
        next(f)
        for line in f:
            names.add(json.loads(line)['name'])
    groups = {r['name']:r['role'] for r in rows(BASE/'identity-gate'/(obj+'-groups'),'groups-*.csv')}
    assert all(v in ('mapping_range','known_out_of_scope') for v in groups.values())
    u = {(r['file'],int(r['line'])) for r in rows(BASE/'identity-gate/v18-gates'/(obj+'-static'),'U-*.csv')}
    dbpath = WORK/'temp/prep-ruling3-4'/(obj+'-static.sqlite')
    db = sqlite3.connect('file:'+str(dbpath)+'?mode=ro',uri=True)
    mapping = {}; proof_values = {}
    # Only touched keys are queried; SQLite is read-only.
    counts = collections.Counter(); details = []; failures = []
    with output.open() as f:
        for number, key in entry_keys(f):
            encoded = key_string(key)
            values = list(db.execute('SELECT status,file,line,ref FROM kv WHERE k=?',(encoded,)))
            if values:
                statuses = {v[0] for v in values}
                special = next((s for s in ['identity_ambiguous','macro_generated_function','system_header_no_reference'] if s in statuses),None)
                mapping[encoded] = dict(status=special or values[0][0],
                  in_U=len(values)==1 and (values[0][1],values[0][2]) in u,
                  excluded=len(values)>1 or any((v[1],v[2]) not in u for v in values))
            category, reason = classify_entry(key,names,groups,mapping)
            counts[category+':'+reason] += 1
            row = [number,key,category,reason,values]
            details.append(row)
            if category == 'unaligned':
                failures.append(row)
    db.close()
    parts = tables(dest,'entries',['profile_line','raw_key','category','reason','map_values'],details)
    parts += tables(dest,'unaligned',['profile_line','raw_key','category','reason','map_values'],failures)
    dump(dest/'classification.json',dict(object=obj,entry_counts=counts,entries=sum(counts.values()),
      unaligned_entries=len(failures),classification_exit_code=1 if failures else 0,
      profile=str(output),profile_sha256=sha(output),parts=parts,
      static_map=dict(path=str(dbpath),sha256=sha(dbpath)),
      calculated=['number of body entries per classification; no body weight sums or ratios']))
    print(json.dumps(dict(tag=tag,counts=counts,unaligned=len(failures))))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(run(sys.argv[1]))
