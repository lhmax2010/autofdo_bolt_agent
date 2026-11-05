#!/usr/bin/env python3
"""Independent per-key avg check: GBS GNU objdump/readelf/addr2line outputs.

No llvm-profgen boundary output is used to construct expected values. Unknown
GNU symbolization or ambiguous declaration lines are explicit verification gaps.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import subprocess


def decode(d):
    if d & 1:
        return 0
    d >>= 1
    return ((d >> 1) & 0xfe0) | (d & 0x1f) if d & 0x20 else d & 0x1f


def duplication(d):
    nxt = d >> 1 if d & 1 else d >> (14 if d & 0x40 else 7)
    return decode(nxt) or 1


def text_profile(text):
    bodies, contexts = {}, {}
    for line in text.splitlines():
        if not line or line.startswith('#'):
            continue
        depth = len(line) - len(line.lstrip(' '))
        row = line.strip()
        if depth == 0:
            name, total, head = row.rsplit(':', 2)
            contexts[0] = (name,)
            continue
        m = re.fullmatch(r'(\d+)(?:\.(\d+))?: (.+)', row)
        if not m:
            raise ValueError('Unexpected profile line: ' + line)
        loc = (int(m[1]), int(m[2] or 0))
        if re.fullmatch(r'\d+', m[3]):
            bodies[(contexts[depth-1], loc)] = int(m[3])
        else:
            name, count = m[3].rsplit(':', 1)
            contexts[depth] = contexts[depth-1] + ((loc, name),)
    return bodies


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--gnu-dir', type=Path, required=True)
    ap.add_argument('--output-dir', type=Path, required=True)
    a = ap.parse_args()
    W = Path('/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent')
    R = W/'temp/GBS-ROOT-RPI4-SPIKE/local/BUILD-ROOTS/scratch.armv7l.0/emul'
    for x in [a.run, a.gnu_dir, a.output_dir]:
        x.resolve().relative_to(W)
    a.output_dir.mkdir(parents=True, exist_ok=True)
    commands = []

    def gnu(label, tool, args, stdin=None):
        cmd = ['nice', '-n', '19', 'ionice', '-c3', str(R/'lib64/ld-linux-x86-64.so.2'), '--library-path', f'{R}/lib64:{R}/usr/lib64', str(R/'usr/bin'/tool), *args]
        p = subprocess.run(cmd, input=stdin, text=True, capture_output=True)
        (a.output_dir/(label+'.stdout')).write_text(p.stdout)
        (a.output_dir/(label+'.stderr')).write_text(p.stderr)
        commands.append(dict(command=cmd,rc=p.returncode))
        (a.output_dir/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        if p.returncode:
            raise RuntimeError(label+': '+p.stderr)
        return p.stdout

    report = json.loads((a.run/'quality.json').read_text())
    names = [x['name'] for x in report['coverage']['top50'][:3]]
    subprograms = json.loads((a.gnu_dir/'subprograms.json').read_text())
    decl = defaultdict(set)
    for d in subprograms:
        if 'decl_line' in d:
            decl[d['name']].add(int(d['decl_line'],0))
    # This ELF's executable PT_LOAD has offset==vaddr==0. Check, do not assume.
    segs=[]
    for line in (a.gnu_dir/'segments.stdout').read_text().splitlines():
        f=line.split()
        if f and f[0]=='LOAD' and 'E' in f:
            segs.append((int(f[1],16),int(f[2],16),int(f[4],16)))
    target=report['identity']['candidates'][0]['path']
    samples=Counter()
    for line in (a.run/'perfscript.txt').open():
        m=re.search(r'\('+re.escape(target)+r'\+0x([0-9a-f]+)\)\s*$',line)
        if m:
            off=int(m[1],16);matches=[v+(off-o) for o,v,size in segs if o<=off<o+size]
            if len(matches)!=1:raise ValueError('Nonunique segment')
            samples[matches[0]]+=1
    expected_by_function={}; problems=[]; address_maps={}
    for index,name in enumerate(names):
        ds=[d for d in subprograms if d['name']==name and ('low_pc' in d or 'ranges' in d)]
        if len(ds)!=1 or 'ranges' in ds[0]:
            problems.append(dict(function=name,reason='GNU DWARF range requires additional decoding',dies=ds));continue
        start=int(ds[0]['low_pc'],16);end=start+int(ds[0]['high_pc'],0)
        dis=gnu(f'function-{index}','objdump',['-d','-z','--disassemble='+name,str(a.gnu_dir/'libavcodec.combined')])
        addresses=[];data=[]
        for line in dis.splitlines():
            cols=line.split('\t');m=re.fullmatch(r'\s*([0-9a-f]+):',cols[0])
            if m and len(cols)>=3:
                addr=int(m[1],16)
                if not start<=addr<end:continue
                if cols[2].strip().startswith('.'):data.append(addr)
                else:addresses.append(addr)
        address_maps[name]=addresses
        if not addresses:raise ValueError('Empty GNU disassembly')
        text=gnu(f'lines-{index}','addr2line',['-a','-f','-i','-e',str(a.gnu_dir/'libavcodec.combined')],''.join(hex(x)+'\n' for x in addresses))
        groups={};current=None
        for line in text.splitlines():
            if re.fullmatch(r'0x[0-9a-f]+',line):current=int(line,16);groups[current]=[]
            elif current is not None:groups[current].append(line)
        counts=Counter();numerators=Counter();maxima=Counter();sumcounts=Counter();bad=[]
        for address in addresses:
            raw=groups[address]
            if len(raw)%2:raise ValueError('Odd addr2line output')
            frames=[];invalid=None
            for fn,loc in zip(raw[::2],raw[1::2]):
                m=re.search(r':(\d+|\?)(?: \(discriminator (\d+)\))?$',loc)
                if not m or fn=='??':invalid='unresolved GNU frame';break
                line=0 if m[1]=='?' else int(m[1]);disc=int(m[2] or 0)
                if len(decl[fn])!=1:invalid='ambiguous/missing GNU DW_AT_decl_line: '+fn;break
                frames.append((fn,(line-next(iter(decl[fn])))&0xffff,decode(disc),disc,line))
            if invalid:
                bad.append(dict(address=hex(address),reason=invalid));continue
            if not frames or frames[0][4]==0:continue
            frames.reverse()
            if frames[0][0]!=name:
                bad.append(dict(address=hex(address),reason='GNU root differs',frames=frames));continue
            context=(frames[0][0],)
            for parent,child in zip(frames,frames[1:]):context+=(((parent[1],parent[2]),child[0]),)
            leaf=frames[-1];key=(context,(leaf[1],leaf[2]));counts[key]+=1
            if samples[address]:
                contribution=samples[address]*duplication(leaf[3]);numerators[key]+=contribution;maxima[key]=max(maxima[key],contribution);sumcounts[key]+=samples[address]
        rows=[]
        for key,num in numerators.items():
            n=counts[key];avg=max(1,(2*num+n)//(2*n))
            rows.append(dict(context=key[0],location=key[1],numerator=num,n=n,avg=avg,sum=sumcounts[key],max=maxima[key]))
        expected_by_function[name]=dict(dwarf_range=[hex(start),hex(end)],instruction_starts=len(addresses),excluded_data=len(data),unresolved=bad,keys=rows)
    comparisons={}
    for aggregation in ['sum','max','avg']:
        file=a.output_dir/(aggregation+'.text')
        if not file.exists():continue
        actual=text_profile(file.read_text());diffs=[];matched=0
        for name,details in expected_by_function.items():
            for row in details['keys']:
                context=tuple(name if isinstance(name,str) else (tuple(name[0]),name[1]) for name in row['context']);key=(context,tuple(row['location']));value=actual.get(key)
                if value==row[aggregation]:matched+=1
                else:diffs.append(dict(key=row,actual=value,expected=row[aggregation]))
        comparisons[aggregation]=dict(matched_keys=matched,differences=diffs)
    result=dict(selected_names=names,selection='first three top-level usable hotspots in the first successful medium BBB Thumb fixed-period RUN; not substituted',functions=expected_by_function,problems=problems,comparisons=comparisons)
    (a.output_dir/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:{'matched_keys':v['matched_keys'],'difference_count':len(v['differences'])} for k,v in comparisons.items()}))


if __name__=='__main__':main()
