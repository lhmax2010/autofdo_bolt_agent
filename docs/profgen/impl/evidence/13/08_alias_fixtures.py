from pathlib import Path
import struct,subprocess,json
w=Path.cwd();d=w/'temp/profgen-patch8';out=w/'temp/llvm-profgen-enh/llvm/test/tools/llvm-profgen/Inputs/ip-mode/gnu-thumb';g=w/'temp/GBS-ROOT-RPI4-SPIKE/local/BUILD-ROOTS/scratch.armv7l.0/emul';r=w/'temp/GBS-ROOT-LLVM-X86/local/BUILD-ROOTS/scratch.x86_64.0';rows=[]
def tool(name,args,root=g):
 cmd=[str(root/'lib64/ld-linux-x86-64.so.2'),'--library-path',f'{root}/lib64:{root}/usr/lib64',str(root/'usr/bin'/name)]+list(map(str,args));p=subprocess.run(['nice','-n','19','ionice','-c3']+cmd,cwd=out,capture_output=True,text=True);rows.append(dict(command=cmd,cwd=str(out),exit=p.returncode,stdout=p.stdout,stderr=p.stderr));assert not p.returncode,p.stderr;return p.stdout
(out/'adjacent.s').write_text('''.syntax unified
.arch armv7-a
.text
.thumb
.global first
.type first, %function
.thumb_func
first:
  movs r0, #1
  bx lr
.size first, .-first
.global second
.type second, %function
.thumb_func
second:
  movs r0, #2
  bx lr
.size second, .-second
''')
tool('as',['-g','-o',d/'adjacent.o','adjacent.s']);tool('ld',['--build-id=sha1','-e','first','-Ttext=0x1000','-o','adjacent.perfbin',d/'adjacent.o'])
# Synthetic DWARF2 line program: same 16-bit instruction has two line entries.
header=bytes([1,1,251,14,13])+bytes([0,1,1,1,1,0,0,0,1,0,0,1])+b'\0'+b'synthetic.s\0\0\0\0\0'
program=b'\0\5\2'+struct.pack('<I',0x1000)+b'\3\10\1'+b'\2\1\3\1\1'+b'\2\7\0\1\1'
body=struct.pack('<HI',2,len(header))+header+program
(d/'synthetic-line.bin').write_bytes(struct.pack('<I',len(body))+body)
tool('llvm-objcopy',['--update-section=.debug_line='+str(d/'synthetic-line.bin'),'gnu-thumb.perfbin','line-mismatch.perfbin'],r)
for name in ['adjacent','line-mismatch']:
 tool('readelf',['--debug-dump=info','--debug-dump=decodedline',name+'.perfbin'])
 tool('llvm-dwarfdump',['--debug-info','--debug-line',name+'.perfbin'],r)
 tool('objdump',['-d',name+'.perfbin'])
(d/'alias-fixtures.json').write_text(json.dumps(rows,indent=2)+'\n')
with (out/'README.txt').open('a') as f:f.write('''
Adjacent GNU AS case: as -g -o <temp>/adjacent.o adjacent.s;
ld --build-id=sha1 -e first -Ttext=0x1000 -o adjacent.perfbin <temp>/adjacent.o.
first [0x1001,0x1005), second [0x1005,0x1009); instruction starts 1000,1002,1004,1006.
The second normalized start 0x1004 is inside the first raw DWARF range.
line-mismatch.perfbin: SYNTHETIC DWARF2 line metadata; minimum_instruction_length=1,
set_address 0x1000, advance_line +8, copy (line9); advance_pc 1,
advance_line +1, copy (line10); advance_pc 7, end_sequence.
Replace only .debug_line using llvm-objcopy --update-section=.debug_line=<temp>/synthetic-line.bin.
This intentionally impossible instruction-level line split tests alias consistency failure;
it is not a compiler-produced line table. Complete generator lives in alias-fixtures.py
in the project evidence; lit only reads the resulting ELF.
''')
print('alias fixtures ready')
