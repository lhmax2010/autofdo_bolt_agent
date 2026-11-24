import json
from pathlib import Path
import subprocess
import sys

formal, out = map(Path, sys.argv[1:])
base = json.loads((formal/'stages/build/002/result.json').read_text())
record = json.loads((formal/'stages/deploy/001/soname-compatibility.json').read_text())
assert not record['missing'] and set(record['versions']) == set(record['board'])
products = {item['name']: item['path'] for item in base['rpms']}
values = {}
for name, item in sorted(record['versions'].items()):
    package = item['package']
    if package not in values:
        fmt = r'%{VERSION}-%{RELEASE} %{ARCH}\n'
        if package in products:
            argv = ['rpm', '-qp', '--qf', fmt, products[package]]
            source = 'BASE-output-RPM'
        else:
            argv = ['rpm', '--dbpath', str(Path(base['scratch'])/'var/lib/rpm'), '-q', '--qf', fmt, package]
            source = 'BASE-construction-RPM-db'
        q = subprocess.run(argv, text=True, capture_output=True)
        assert q.returncode == 0 and len(q.stdout.splitlines()) == 1, q.stderr
        values[package] = dict(version=q.stdout.strip(), argv=argv, source=source, exit_code=q.returncode)
result = {name: {**item,'build':values[item['package']]['version'],
                 'matches':item['board']==values[item['package']]['version']}
          for name, item in sorted(record['versions'].items())}
(out/'soname-version-recheck.json').write_text(json.dumps(dict(board_and_build_versions=result, source_queries=values), indent=2)+'\n')
print('SONAME matches:',sum(row['matches'] for row in result.values()),'/',len(result))
