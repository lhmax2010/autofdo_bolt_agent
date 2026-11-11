"""Synthetic boundary exclusions and canonical-name option contract, unchanged tool."""
import json
import subprocess
import sys
from registration_address_check import OUT, TEMP, TOOL, TOOL_SHA, dump, profile_entries
from registration_mapping_checks import classify_entry
from run_scoped import WORK, platform, sha


def main():
    assert sha(TOOL) == TOOL_SHA
    tree = WORK/'temp/llvm-profgen-enh'
    inputs = tree/'llvm/test/tools/llvm-profgen/Inputs/ip-mode'
    root = TEMP/'contract-extras'; root.mkdir()
    records = []
    for name, aggregation, skid, canonical in [
        ('bad-conflict','max','none',False),
        ('bad-conflict','max','prev-inst',False),
        ('bad-conflict','avg','none',False),
        ('boundaries','max','none',True),
    ]:
        dest = root/f'{name}-{aggregation}-{skid}-{canonical}'; dest.mkdir()
        perf = dest/'synthetic.perfscript'; perf.write_text('17/17 1 cycles: 1000 (/target+0x1000)\n')
        out = dest/'synthetic.proftext'; report = dest/'report.json'
        command = platform('llvm-profgen')[:-1]+[str(TOOL),'--ip-samples','--allow-missing-build-id',
          '--binary-match-regex=^/target$', '--binary='+str(inputs/'boundary-extra'/(name+'.perfbin')),
          '--perfscript='+str(perf), '--output='+str(out),'--quality-report='+str(report),
          '--format=text','--ip-aggregation='+aggregation,'--ip-skid='+skid]
        if canonical:command += ['--show-canonical-fname']
        p = subprocess.run(command,capture_output=True,text=True)
        q = json.loads(report.read_text()) if report.exists() else None
        rec = dict(command=command,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,
                   verdict=q['verdict'] if q else None,output_created=out.exists(),
                   report=str(report),report_sha256=sha(report) if report.exists() else None)
        records.append(rec);dump(OUT/'contract-extras.json',records)
        if canonical:
            assert p.returncode != 0 and '--show-canonical-fname' in p.stderr and not out.exists()
        elif aggregation == 'max' and skid == 'none':
            assert p.returncode == 0
            entries = list(profile_entries(out)); assert entries
            classified = [classify_entry(k,{k[0][0]},{k[0][0]:'mapping_range'}, {}, unavailable={k[0][0]}) for k,c in entries]
            assert all(x[0]=='boundary_unavailable' for x in classified)
            rec['synthetic_entries'] = entries;rec['classifications'] = classified
        else:
            assert p.returncode != 0 and q['verdict']['failure_stage']=='boundary' and not out.exists()
            assert 'conflicting mapping states' in p.stderr
    dump(OUT/'contract-extras.json',records)
    source_evidence()
    print('PASS: boundary excluded group none/prev-inst/avg; canonical option rejection')


def source_evidence():
    tree = WORK/'temp/llvm-profgen-enh'
    specifications = {
      'llvm/tools/llvm-profgen/ProfiledBinary.h':[(613,622)],
      'llvm/tools/llvm-profgen/ProfiledBinary.cpp':[(1206,1218),(1275,1310)],
      'llvm/tools/llvm-profgen/llvm-profgen.cpp':[(237,253)],
      'llvm/tools/llvm-profgen/ProfileGenerator.cpp':[(580,622)],
      'llvm/tools/llvm-profgen/IPQualityReport.cpp':[(840,891)],
      'llvm/lib/ProfileData/Coverage/CoverageMapping.cpp':[(1468,1480),(1542,1567)],
      'llvm/tools/llvm-cov/CoverageSummaryInfo.cpp':[(80,140)],
      'llvm/tools/llvm-cov/CoverageReport.cpp':[(444,469)],
    }
    evidence=[]
    for relative, ranges in specifications.items():
        path=tree/relative;lines=path.read_text().splitlines()
        evidence.append(dict(path=str(path),sha256=sha(path),line_count=len(lines),excerpts=[dict(start=a,end=min(b,len(lines)),text='\n'.join(f'{n}: {lines[n-1]}' for n in range(a,min(b,len(lines))+1))) for a,b in ranges]))
    dump(OUT/'source-contracts.json',evidence)
    print('PASS: source excerpts saved with actual file bounds')


if __name__=='__main__':
    source_evidence() if '--source-only' in sys.argv else main()
