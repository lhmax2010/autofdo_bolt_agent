"""Keep bulk synthetic-entry/range tables in temp; seal small repository indices."""
import json
import subprocess
from pathlib import Path
from run_scoped import WORK, sha

OUT=WORK/'docs/profgen/eval/prep/evidence/registration-checks/batch1'
TEMP=WORK/'temp/registration-batch1/detail-tables'


def dump(p,x):
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def archive():
    moved=[];replacements={}
    for obj in ['spike-thumb','spike-a32','ffmpeg-thumb','ffmpeg-a32']:
        for directory,patterns in [(OUT/(obj+'-addresses'),['*-entries-*.csv','*-fine-classification-*.csv']),
                                   (OUT/(obj+'-coverage-ranges-v2'),['functions-*.csv','groups-*.csv'])]:
            for pattern in patterns:
                for source in sorted(directory.glob(pattern)):
                    target=TEMP/source.relative_to(OUT)
                    target.parent.mkdir(parents=True,exist_ok=True)
                    assert not target.exists()
                    digest=sha(source);size=source.stat().st_size
                    source.rename(target)
                    assert sha(target)==digest
                    replacements[str(source)]=str(target)
                    moved.append(dict(path=str(target),sha256=digest,bytes=size))
    def replace(value):
        if isinstance(value,str):return replacements.get(value,value)
        if isinstance(value,list):return [replace(x) for x in value]
        if isinstance(value,dict):return {k:replace(v) for k,v in value.items()}
        return value
    for path in sorted(OUT.rglob('*.json')):
        data=json.loads(path.read_text());new=replace(data)
        if data!=new:dump(path,new)
    dump(OUT/'bulk-tables.json',dict(reason='Large full tables stay in WORKDIR/temp; small indices retain paths and SHA',files=moved))
    print('Archived',len(moved),'tables',sum(x['bytes'] for x in moved),'bytes')


def seal():
    resources=[]
    for path in sorted(OUT.rglob('resources.json')):
        r=json.loads(path.read_text());r['evidence_path']=str(path.relative_to(WORK));resources.append(r)
    available=[]
    for path in OUT.rglob('meminfo*.txt'):
        for line in path.read_text().splitlines():
            if line.startswith('MemAvailable:'):available.append(int(line.split()[1])*1024)
    dump(OUT/'resources-summary.json',dict(tasks=resources,peak_bytes=max(r['memory_peak_bytes'] for r in resources),
      min_memavailable_bytes=min(available),resource_terminations=sum(r['resource_terminated'] for r in resources),
      serialized=True,scope_memory_max='3G',scope_cpu_quota='200%',nice=19,ionice='-c3'))
    # Git object bytes provide a baseline without opening any formal profiles.
    existing_tests=subprocess.run(['git','ls-tree','-r','--name-only','7c96c1e','tools/profgen_eval'],capture_output=True,text=True,check=True).stdout.splitlines()
    tests=[]
    import hashlib
    for relative in existing_tests:
        if Path(relative).name.startswith('test_'):
            original=subprocess.run(['git','show','7c96c1e:'+relative],capture_output=True,check=True).stdout
            assert hashlib.sha256(original).hexdigest()==sha(WORK/relative)
            tests.append(dict(path=relative,sha256=sha(WORK/relative),unchanged=True))
    dump(OUT/'original-tests-unchanged.json',tests)
    # Verify every path/SHA pair recorded in the bulk index.
    for r in json.loads((OUT/'bulk-tables.json').read_text())['files']:
        assert sha(r['path'])==r['sha256']
    manifest=[]
    for path in sorted(OUT.rglob('*')):
        if path.is_file() and path.name!='manifest.json':
            assert path.stat().st_size<1000000,path
            manifest.append(dict(path=str(path.relative_to(WORK)),sha256=sha(path),bytes=path.stat().st_size))
    dump(OUT/'manifest.json',dict(files=manifest))
    assert (OUT/'manifest.json').stat().st_size<1000000
    print('Sealed',len(manifest),'files;',len(tests),'old test files unchanged')


if __name__=='__main__':
    import sys
    globals()[sys.argv[1]]()
