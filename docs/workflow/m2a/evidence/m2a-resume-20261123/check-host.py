from hashlib import file_digest
import json, shutil, subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone
from afdo_wf.receipts import Store

work=Path.cwd()
out=work/'temp/m2a-resume-20261123'
old=work/'temp/m2a-rpi5-prep-20261119/continuation'
prior=work/'temp/m2a-resume-20261121'
w=work/'temp/m2a-rpi5-wt'
job=json.loads((old/'job.json').read_text())
root=Path(job['output'])

def digest(p):
    with Path(p).open('rb') as f:
        return file_digest(f,'sha256').hexdigest()

records={}
def check(key,path,expected):
    p=Path(path)
    resolved=p.resolve(strict=True)
    if not resolved.is_relative_to(work) or not p.is_file():
        raise RuntimeError(f'path not a regular input in WORKDIR: {p}')
    found=digest(p)
    records[key]=dict(path=str(p.relative_to(work)),sha256=found,expected=expected,matched=(found==expected))
    if found!=expected:
        raise RuntimeError(f'SHA changed for {key}: {p}')

try:
    receipt=Store(root/'receipts').verify('preflight')
    for group in ('inputs','outputs'):
        for p, expected in receipt[group].items():
            check(group+':'+p,p,expected)
    for name,m in job['tools'].items():
        check('tool:'+name,m['path'],m['sha256'])
    saved=json.loads((w/'docs/maintenance/evidence/2026-11-23/preserved-tools.json').read_text())
    for m in saved:
        check('cleanup-original:'+m['source'],work/m['source'],m['sha256'])
        check('cleanup-copy:'+m['preserved'],work/m['preserved'],m['sha256'])
    for name in ('profgen','profdata'):
        argv=job[name]
        result=subprocess.run([*argv[:-1], '--list', argv[-1]],capture_output=True,text=True,check=True,timeout=20)
        (out/(name+'-loader-list.txt')).write_text(result.stdout)
        for line in result.stdout.splitlines():
            if '=>' not in line:
                continue
            path=Path(line.partition('=>')[2].strip().split()[0])
            if path.is_absolute():
                prior_row=next((m for m in saved if work/m['source']==path or (work/m['source']).resolve()==path.resolve()),None)
                if prior_row is None:
                    raise ValueError(f'loader dependency lacks pre-cleanup checksum: {path}')
                check(f'{name}:runtime:{path}',path,prior_row['sha256'])
    snapshot=json.loads(Path(job['snapshot_evidence']).read_text())['selected']
    for name,expected in snapshot.items():
        identity=expected['id']
        local_meta=old/(identity+'.repodata_repomd.xml')
        local_primary=old/(identity+'-primary.xml.gz')
        check('snapshot:'+name+':repomd',local_meta,digest(prior/(name+'-repomd.xml')))
        check('snapshot:'+name+':primary',local_primary,expected['primary_sha256'])
        node=ET.parse(local_meta).find('{*}data[@type="primary"]')
        check('snapshot:'+name+':primary-declaration',local_primary,node.find('{*}checksum').text)
        host_root=expected['url']
        for suffix, url, reference in [('repomd.xml',host_root+'repodata/repomd.xml',local_meta),
                                        ('primary.xml.gz',host_root+node.find('{*}location').get('href'),local_primary)]:
            path=out/(name+'-'+suffix)
            cmd=['curl','--location','--fail','--silent','--show-error','--max-time','60','--output',str(path),'--write-out','%{http_code} %{url_effective}',url]
            reply=subprocess.run(cmd,check=False,capture_output=True,text=True)
            (out/(name+'-'+suffix+'.curl.txt')).write_text(reply.stdout+'\n'+reply.stderr)
            if reply.returncode or not reply.stdout.startswith('200 '):
                raise RuntimeError(f'{name} {suffix} unavailable: {reply.stdout} {reply.stderr}')
            check('snapshot-online:'+name+':'+suffix,path,digest(reference))
finally:
    (out/'post-cleanup-sha.json').write_text(json.dumps(records,indent=2)+'\n')
assert all(row['matched'] for row in records.values())
print(f"{len(receipt['inputs'])} S0 inputs, {len(receipt['outputs'])} outputs, {len(records)} SHA checks passed")
backup=out/'previous-formal'
shutil.copytree(root,backup,symlinks=True)
files={str(f.relative_to(root)):digest(f) for f in sorted(root.rglob('*')) if f.is_file() and not f.is_symlink()}
assert all(digest(backup/name)==val for name,val in files.items())
(out/'previous-formal-sha.json').write_text(json.dumps(files,indent=2)+'\n')
print('archived previous formal files',len(files))
