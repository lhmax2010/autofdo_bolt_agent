#!/usr/bin/env python3
"""Cross-check profgen boundary diagnostics against platform objdump, per range.

Human golden assertions remain in lit; objdump is a secondary cross-check.
Inputs and all generated artifacts must be in the project workspace.
"""
import argparse
import json
from pathlib import Path
import re
from check_ip_boundaries import Runner, parse_boundaries


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--tool', type=Path, required=True)
    ap.add_argument('--platform-root', type=Path, required=True)
    ap.add_argument('--inputs', type=Path, required=True)
    ap.add_argument('--output-dir', type=Path, required=True)
    args = ap.parse_args()
    r = Runner(args.output_dir, args.platform_root)
    cases = [('boundaries',0x1000,'thumbv7a'),('boundary-before_state',0x1002,'thumbv7a'),('boundary-at_state',0x1012,'thumbv7a'),('boundary-discontinuous',0x1002,'thumbv7a'),('boundary-after_data_a32',0x1018,'armv7a'),('pure-arm',0x1000,'armv7a'),('pure-a64',0x1000,'aarch64'),('arm-literal',0x1000,'armv7a'),('section-adjacent',0x1004,'thumbv7a'),('thumb-count',0x12be,'thumbv7a'),('thumb-no-attributes',0x12be,'thumbv7a'),('arm-count',0x12c8,'armv7a'),('a64-pie',0x1318,'aarch64')]
    results = []
    for name, addr, triple in cases:
        original = name in ('thumb-count','thumb-no-attributes','arm-count','a64-pie')
        binary = args.inputs / ('' if original else 'boundary-extra') / (name+'.perfbin')
        off = addr - (0x1000 if original else -0x1000 if name == 'section-adjacent' else 0)
        perf = args.output_dir/(name+'.perfscript')
        perf.write_text(f'17/17 1000003 cycles: {addr:x} (/target+0x{off:x})\n')
        r.run(name+'-attributes', r.platform('readelf','-A',binary))
        out = r.run(name+'-profgen',[args.tool,'--ip-samples','--allow-missing-build-id','--binary-match-regex=^/target$','--binary='+str(binary),'--perfscript='+str(perf),'--format=text','--output='+str(args.output_dir/(name+'.prof')),'--ip-aggregation=avg','--show-ip-boundaries'])
        for function, data in parse_boundaries(out).items():
            actual = set()
            for j,(lo,hi) in enumerate(data['ranges']):
                dis = r.run(name+'-objdump-'+str(j),r.platform('llvm-objdump','--triple='+triple,'--mattr=+neon,+vfp3' if triple!='aarch64' else '--mattr=+neon','-d','--start-address='+hex(lo),'--stop-address='+hex(hi),binary))
                for line in dis.splitlines():
                    m = re.match(r'^\s*([0-9a-f]+):\s+([^\t]+)\t(.*)',line)
                    if m and not m[3].lstrip().startswith('.') and lo <= int(m[1],16) < hi:
                        actual.add(int(m[1],16))
            expected = set(data['instructions'])
            results.append(dict(fixture=name,function=function,triple=triple,profgen_count=len(expected),objdump_count=len(actual),matches=len(expected&actual),profgen_only=list(map(hex,sorted(expected-actual))),objdump_only=list(map(hex,sorted(actual-expected))),ranges=data['ranges']))
    (args.output_dir/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))
    if any(x['profgen_only'] or x['objdump_only'] for x in results):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
