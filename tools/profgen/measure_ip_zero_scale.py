#!/usr/bin/env python3
"""Synthetic load scale measurement, NOT sampled-workload or avg correctness evidence.

Selects one independent objdump start per executable STT_FUNC extent. Functions
with st_size=0 extend to the next distinct function or section end (as probe07).
Aliases sharing an extent are counted once. Input coverage and exclusions are
recorded; missing DWARF is never manufactured or filled outside profgen rules.
"""
import argparse
import bisect
import hashlib
import json
from pathlib import Path
import re
from check_ip_boundaries import Runner, sections, symbols


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for arg in ['tool','platform-root','output-dir','runtime','debug','reference']:
        ap.add_argument('--'+arg,type=Path,required=True)
    args=ap.parse_args();r=Runner(args.output_dir,args.platform_root)
    ids=[]
    for label,path in [('runtime',args.runtime),('debug',args.debug)]:
        text=r.run(label+'-notes',r.platform('readelf','-n',path))
        ids.append(re.findall(r'Build ID: (\S+)',text))
    assert ids[0]==ids[1]==['f960461f63c852474257f51267b7b543afffdc9c']
    bid=ids[0][0]
    sec=sections(r.run('sections',r.platform('readelf','-SW',args.debug)))
    syms=symbols(r.run('symbols',r.platform('readelf','-sW',args.debug)))
    funcs=[s for s in syms if s['type']=='FUNC' and 'X' in sec.get(s['section'],{}).get('flags','')]
    bysection={}
    for f in funcs:bysection.setdefault(f['section'],set()).add(f['value']&~1)
    bysection={s:sorted(aa) for s,aa in bysection.items()}
    chosen=[];seen=set();aliases=[]
    for f in funcs:
        lo=f['value']&~1;ss=sec[f['section']];hi=lo+f['size']
        if not f['size']:
            starts=bysection[f['section']];j=bisect.bisect_right(starts,lo)
            hi=starts[j] if j<len(starts) else ss['addr']+ss['size']
        if not ss['addr']<=lo<hi<=ss['addr']+ss['size']:
            continue
        key=(f['section'],lo,hi)
        if key in seen:aliases.append(f);continue
        seen.add(key);chosen.append(dict(f,start=lo,end=hi,thumb=bool(f['value']&1)))
    chosen.sort(key=lambda f:(-f['size'],f['start'],f['name']))
    # One whole-file disassembly, streamed below. This is an independent source
    # of PCs, never a profgen-generated boundary list.
    r.run('objdump-all',r.platform('llvm-objdump','--triple=thumbv7a','--mattr=+neon,+vfp3','-d',args.reference))
    starts=[]
    for line in (args.output_dir/'objdump-all.stdout').open():
        m=re.match(r'^\s*([0-9a-f]+):\s+([^\t]+)\t(.*)',line)
        if m and not m[3].lstrip().startswith('.'):
            starts.append(int(m[1],16))
    starts=sorted(set(starts));no_instruction=[];eligible=[]
    for f in chosen:
        j=bisect.bisect_left(starts,f['start'])
        if j==len(starts) or starts[j]>=f['end']:
            no_instruction.append(f);continue
        eligible.append(dict(f,sample_address=starts[j]))
    ph=r.run('segments',r.platform('readelf','-lW',args.runtime));loads=[]
    for line in ph.splitlines():
        v=line.split()
        if v and v[0]=='LOAD' and 'E' in v[6:-1]:loads.append(tuple(int(v[j],16) for j in (1,2,4)))
    def offset(addr):
        found=[off+addr-va for off,va,size in loads if va<=addr<va+size]
        assert len(found)==1,(addr,found)
        return found[0]
    mappings=''.join(f'0/0 PERF_RECORD_MMAP2 17/17: [0x{va:x}(0x{size:x}) @ {off:x} <{bid}>]: r-xp /target\n' for off,va,size in loads)
    cohorts={'largest20':[f for f in eligible if f['thumb'] and f['size']][:20],'all-executable':eligible}
    rows=[]
    for label,fs in cohorts.items():
        perf=args.output_dir/(label+'.perfscript')
        perf.write_text(mappings+''.join(f'17/17 1000003 cycles: {f["sample_address"]:x} (/target+0x{offset(f["sample_address"]):x})\n' for f in fs))
        out=args.output_dir/(label+'.prof')
        if out.exists():out.unlink()
        r.run(label,[args.tool,'--ip-samples','--binary-match-regex=^/target$','--binary='+str(args.runtime),'--debug-binary='+str(args.debug),'--perfscript='+str(perf),'--ip-aggregation=avg','--ip-zero-fill=sampled-functions','--show-ip-address-counts','--show-ip-boundaries','--format=text','--output='+str(out)],check=False)
        cmd=r.commands[-1];stats={};instructions=0
        for line in (args.output_dir/(label+'.stdout')).open():
            if line.startswith('IP-BOUNDARY instruction='):instructions+=1
            m=re.match(r'IP-GENERATION (\w+)(?:=| )(.*)',line)
            if m:stats[m[1]]=m[2].strip()
        entries={'top_level_functions':0,'inline_nodes':0,'body_locations':0,'zero_body_locations':0,'lines':0}
        if out.exists():
            for line in out.open():
                entries['lines']+=1
                if not line.startswith(' '):entries['top_level_functions']+=1
                elif re.fullmatch(r'\s+\d+(?:\.\d+)?: \d+\n',line):
                    entries['body_locations']+=1
                    if line.rstrip().endswith(': 0'):entries['zero_body_locations']+=1
                else:entries['inline_nodes']+=1
        rows.append(dict(label='合成负载规模测量/'+label,input_functions=len(fs),functions=fs,exit=cmd['exit'],seconds=cmd['seconds'],peak_rss_kib=cmd['peak_rss_kib'],enumerated_instruction_starts=instructions,generation_stats=stats,profile_entries=entries,profile_exists=out.exists(),profile_sha256=hashlib.sha256(out.read_bytes()).hexdigest() if out.exists() else None,stderr=(args.output_dir/(label+'.stderr')).read_text()))
    result=dict(kind='合成负载规模测量：不是实测采样，不验证avg数值',build_id=bid,executable_function_symbols=len(funcs),deduplicated_extents=len(chosen),aliases=aliases,no_objdump_instruction=no_instruction,cohorts=rows,limitations='Only functions with usable DWARF samples participate in zero-fill; executable functions without usable DWARF are recorded outside/in_func_no_line, not invented. Counts include same-name CU ranges combined by existing loader.')
    (args.output_dir/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in x.items() if k!='functions'} for x in rows],indent=2))

if __name__=='__main__':main()
