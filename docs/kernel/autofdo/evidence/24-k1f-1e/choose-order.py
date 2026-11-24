import bisect
import collections
import json
import pathlib
import random
import re
import struct
import sys

root,dest=map(pathlib.Path,sys.argv[1:])
maps=root/'temp/kernel-afdo-k1/k1e/link-maps'
base=root/'temp/kernel-afdo-k1/kbase/artifacts/arm-rpi4/vmlinux'
pattern=re.compile(r'^\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+([0-9a-fA-F]+)\s+[0-9]+( +)(.+)$')
inputs=[]
current=None
for line in (maps/'kbase.map').open():
    match=pattern.fullmatch(line.rstrip('\n'))
    if not match:
        continue
    addr,size,indent,value=match.groups()
    if len(indent)==1 and re.fullmatch(r'[^\s:]+',value):
        current=value
    elif current=='.text' and len(indent)==9 and int(size,16):
        part=re.fullmatch(r'(.*):\(([^)]+)\)',value)
        if part:
            inputs.append(dict(address=int(addr,16),size=int(size,16),object=part[1],section=part[2]))
inputs.sort(key=lambda row:row['address'])
starts=[i['address'] for i in inputs]
assert all(row['address']+row['size']<=following['address'] for row,following in zip(inputs,inputs[1:]))
raw=base.read_bytes()
h=struct.unpack_from('<16sHHIIIIIHHHHHH',raw)
assert h[0][:6]==b'\x7fELF\1\1' and h[2]==40
sections=[struct.unpack_from('<10I',raw,h[6]+40*i) for i in range(h[12])]
symbols=next(s for s in sections if s[1]==2)
symbol_strings=sections[symbols[6]]
strings=raw[symbol_strings[4]:symbol_strings[4]+symbol_strings[5]]
matching=collections.defaultdict(set)
candidate=collections.defaultdict(list)
for i in range(symbols[4],symbols[4]+symbols[5],16):
    n,v,size,info,other,index=struct.unpack_from('<IIIBBH',raw,i)
    if not n or index==0:
        continue
    name=strings[n:strings.index(b'\0',n)].decode(errors='replace')
    if info&15 != 2:
        matching[name].add(None)
        continue
    addr=v&~1
    loc=bisect.bisect_right(starts,addr)-1
    if loc<0 or addr>=starts[loc]+inputs[loc]['size']:
        matching[name].add(None)
        continue
    matching[name].add(loc)
    candidate[loc].append((int(info>>4==0),addr,name))
chosen=[]
shared_names=[]
excluded=[]
for loc,rows in sorted(candidate.items()):
    available=sorted(x for x in rows if matching[x[2]]=={loc})
    if not available:
        available=sorted(x for x in rows if None not in matching[x[2]])
        if available:
            name=available[0][2]
            shared_names.append(dict(**inputs[loc],representative=name,
                matches=[inputs[i] for i in sorted(matching[name])]))
        else:
            excluded.append(dict(**inputs[loc],names=sorted(set(x[2] for x in rows))))
            continue
    chosen.append(dict(**inputs[loc],symbol=available[0][2],function_address=available[0][1]))
assert not excluded, excluded
random.Random(20261120).shuffle(chosen)
(dest/'symbol-order.txt').write_text(''.join(name+'\n' for name in dict.fromkeys(x['symbol'] for x in chosen)))
summary=dict(seed=20261120,all_nonempty_inputs=len(inputs),inputs_with_function=len(candidate),
             representatives=len(chosen),distinct_symbol_names=len({item['symbol'] for item in chosen}),
             shared_names=shared_names,excluded=excluded,ordered_inputs=chosen)
(dest/'symbol-order.json').write_text(json.dumps(summary,indent=2)+'\n')
print({k:v for k,v in summary.items() if k!='ordered_inputs'})
