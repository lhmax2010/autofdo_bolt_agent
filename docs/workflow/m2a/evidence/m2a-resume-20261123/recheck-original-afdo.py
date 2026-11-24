"""Exercise the unchanged consumption check against the original AFDO objects."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

from afdo_wf import buildlock, consumption
from afdo_wf.common import GateError, sha256
from afdo_wf.live import consumed_profile_path

formal, out = map(Path, sys.argv[1:])
variant = formal/'stages/rebuild/001/AFDO'
base = json.loads((formal/'stages/build/002/result.json').read_text())
lock = json.loads((variant/'build-lock.json').read_text())
build_argv = json.loads((variant/'execution/command.json').read_text())['argv']
root = Path(build_argv[build_argv.index('--buildroot') + 1])/'local/BUILD-ROOTS/scratch.aarch64.0'
loc = root/lock['source_layout'].lstrip('/')
targets = list(base['artifacts'])
mapping = dict(zip(targets, targets))
names = {'libgcc.a','libgcc_eh.a','crtbeginS.o','crtendS.o'}

def support(path):
    return [record for obj in sorted((root/path).rglob('*')) if obj.name in names
            for record in buildlock.recorded_switches(subprocess.check_output(
                ['readelf','-p','.GCC.command.line',obj], text=True))]

try:
    consumption.target_source_commands(lock['commands'], mapping, support('usr/lib/gcc'))
except GateError as error:
    assert str(error) == 'unclassified recorded command'
else:
    raise AssertionError('wrong path did not fail closed')
source, excluded = consumption.target_source_commands(lock['commands'], mapping, support('usr/lib64/gcc'))
assert all(len(source[t])+len(excluded[t])==len(lock['commands'][t]) for t in targets)
option = consumed_profile_path(lock['commands'])
samples = formal/'stages/convert/001/autofdo.extbinary'
renamed = {t:variant/'extracted/usr/lib64'/base['artifacts'][t]['real_name'] for t in targets}
text_after={}
for t,path in renamed.items():
    sections = subprocess.check_output(['readelf','-SW',path],text=True)
    section = re.search(r'\] \.text\s+PROGBITS\s+[0-9a-fA-F]+\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)',sections)
    assert section
    with path.open('rb') as stream:
        stream.seek(int(section[1],16))
        text_after[t] = hashlib.sha256(stream.read(int(section[2],16))).hexdigest()
remarks = [(str(p.relative_to(loc)), p) for t in targets for p in sorted((loc/t).rglob('*.opt.yaml'))]
result=consumption.evaluate(targets,mapping,remarks,source,sha256(samples),root/option.lstrip('/'),
                            base['text'],text_after,option)
(out/'original-afdo-offline-consumption.json').write_text(json.dumps(dict(result=result,remark_files=len(remarks)),indent=2)+'\n')
assert result['passed'],result
print({t:item['positive_records'] for t,item in result['targets'].items()})
