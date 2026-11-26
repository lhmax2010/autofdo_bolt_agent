#!/usr/bin/env python3
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

staging, prior_manifest, symvers = map(Path, sys.argv[1:])
manifest = {}
for line in prior_manifest.read_text().splitlines():
    digest, name = line.split('  ', 1)
    manifest[name.removeprefix('./')] = digest

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

installed = {str(path.relative_to(staging)): sha(path)
             for path in staging.rglob('*') if path.is_file() and not path.is_symlink()}
if installed != manifest:
    raise ValueError('Archived files differ from the K1f-1e p6 readback manifest')

def command_text(*argv):
    return subprocess.run(argv, text=True, capture_output=True, check=True).stdout.removesuffix('\n')

def crc_table(data):
    return {columns[1]: columns[0] for line in data.splitlines() if (columns := line.split())}

expected = crc_table(symvers.read_text())['module_layout']
rows = []
for name in sorted(path for path in manifest if path.endswith('.ko')):
    file = staging / name
    versions = crc_table(command_text('modprobe', '--dump-modversions', file))
    rows.append({'path': name, 'sha256': installed[name], 'module_layout': versions['module_layout'],
                 'vermagic': command_text('modinfo', '-F', 'vermagic', file)})
assert len(rows) == 58
assert all(row['module_layout'] == expected for row in rows)
print(json.dumps({'prior_p6_manifest_sha256': sha(prior_manifest), 'matching_p6_files': len(installed),
                  'kbase_symvers_sha256': sha(symvers), 'kbase_module_layout': expected,
                  'module_crc_values': dict(Counter(row['module_layout'] for row in rows)),
                  'vermagic_values': dict(Counter(row['vermagic'] for row in rows)), 'modules': rows},
                 indent=2))
