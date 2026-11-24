import ast
import json
from pathlib import Path
import sys
from afdo_wf.common import sha256, save
from afdo_wf.receipts import Store

work, out = map(Path, sys.argv[1:])
w = work/'temp/m2a-rpi5-wt'
sealed = work/'temp/m2a-rpi5-prep-20261119/continuation/job.json'
job = json.loads(sealed.read_text())
formal = Path(job['output'])
store = Store(formal/'receipts')
verified = {}
for stage in ('preflight','build','deploy','collect','convert','rebuild'):
    result = store.verify(stage)
    verified[stage] = dict(sha256=sha256(store.path(stage)), inputs=len(result['inputs']), outputs=len(result['outputs']))
assert all(not store.path(stage).exists() for stage in ('measure','report'))
config = w/'workflow/platforms/rpi5-aarch64.toml'
assert result['inputs'][str(config)] == sha256(config)
assert result['inputs'][str(sealed)] == sha256(sealed)
reference = {}
def visit(p):
    tree = ast.parse(p.read_text())
    for node in ast.walk(tree):
        if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            continue
        matches = [n.lineno for n in ast.walk(node) if (
            isinstance(n, ast.Attribute) and n.attr=='gcc_support' or
            isinstance(n,ast.Constant) and isinstance(n.value,str) and any(
                pat in n.value for pat in ('usr/lib/gcc','usr/lib64/gcc','gcc_support')))]
        if matches:
            reference[p.name+':'+node.name] = matches
for p in sorted((w/'workflow/afdo_wf').glob('*.py')):
    visit(p)
assert list(reference) == ['live.py:rebuild'], reference
other = list((w/'workflow/board').glob('*.sh'))
other += list((Path(job['package']).parent/'workloads').glob('*'))
assert all(not any(pattern in p.read_text() for pattern in ('gcc_support','usr/lib/gcc','usr/lib64/gcc')) for p in other)
record = dict(receipts=verified, formal=str(formal), sealed_job=str(sealed), sealed_job_sha256=sha256(sealed),
    sealed_platform=str(config), sealed_platform_sha256=sha256(config), gcc_path_code_references=reference,
    note="S6/S7 reuse verified receipt data; the sealed TOML is checked for integrity only. S6/S7 do not query GCC support objects or invoke the S5 rebuild handler.",
    rebuild_receipt_sha256=verified['rebuild']['sha256'], original_control=result['details']['control'])
save(out/'prerequisites.json',record)
print(verified)
