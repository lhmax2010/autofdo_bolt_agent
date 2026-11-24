import difflib
import hashlib
import json
from pathlib import Path
import re
import sys

reference, observed, directory=map(Path,sys.argv[1:4])
mode=sys.argv[4]

def parse(path):
    chosen=False
    bootloader=False
    found=0
    seeds=[]
    rsts=None
    cmdline=None
    out=[]
    for line in path.read_text().splitlines(keepends=True):
        if line=='\tchosen {\n':
            assert not chosen
            chosen=True
            found+=1
        if chosen and line=='\t\tbootloader {\n':
            assert not bootloader
            bootloader=True
        if chosen and bootloader:
            match=re.fullmatch(r'\t\t\trsts = <(0x[0-9a-fA-F]+)>;\n',line)
            if match:
                assert rsts is None
                rsts=int(match[1],16)
                continue
        if chosen and re.fullmatch(r'\t\t(?:kaslr-seed|rng-seed)(?:\s*=.*)?;\n',line):
            seeds.append(line.split('=',1)[0].strip())
            continue
        if chosen and mode=='diag' and line.startswith('\t\tbootargs = '):
            assert cmdline is None
            cmdline=line.strip()
            # The diagnostic invocation has a separate, explicitly exempted cmdline.
            # Preserve the property shape and audit its original text in the receipt.
            out.append('\t\tbootargs = "<diagnostic command line>";\n')
            continue
        out.append(line)
        if chosen and bootloader and line=='\t\t};\n':
            bootloader=False
        if chosen and line=='\t};\n':
            assert not bootloader
            chosen=False
    assert not chosen and not bootloader and found==1 and rsts is not None,path
    assert mode!='diag' or cmdline is not None,path
    return out,dict(rsts=f'0x{rsts:x}',seeds=seeds,bootargs=cmdline)

a,expected=parse(reference)
b,actual=parse(observed)
directory.mkdir(parents=True,exist_ok=True)
(directory/'expected.normalized.dts').write_text(''.join(a))
(directory/'observed.normalized.dts').write_text(''.join(b))
(directory/'normalized-fdt.diff').write_text(''.join(difflib.unified_diff(a,b,fromfile='reference',tofile='observed')))
receipt=dict(mode=mode,expected=expected,actual=actual,equal=a==b,
             expected_sha256=hashlib.sha256(''.join(a).encode()).hexdigest(),
             actual_sha256=hashlib.sha256(''.join(b).encode()).hexdigest(),
             excluded=['/chosen/kaslr-seed','/chosen/rng-seed','/chosen/bootloader/rsts'])
(directory/'fdt-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n')
sys.exit(a!=b)
