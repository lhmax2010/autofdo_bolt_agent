from pathlib import Path
import re,json,subprocess,struct
w=Path.cwd();d=w/'temp/profgen-patch8/independent-avg';src=w/'temp/board-round1-resume2/gnu';g=w/'temp/GBS-ROOT-RPI4-SPIKE/local/BUILD-ROOTS/scratch.armv7l.0/emul';r=w/'temp/GBS-ROOT-LLVM-X86/local/BUILD-ROOTS/scratch.x86_64.0'
rows=[];cur=None;root=False
for n,line in enumerate((src/'debug-info.stdout').open(),1):
 m=re.search(r'Compilation Unit @ offset (0x[0-9a-f]+|0):',line)
 if m:cur={'offset':int(m[1],0),'source_line':n};rows.append(cur);root=False
 if cur is None:continue
 m=re.search(r'Version:\s+(\d+)',line)
 if m:cur['version']=int(m[1])
 if 'DW_TAG_compile_unit' in line:root=True;continue
 if root:
  if re.match(r'\s*<\d+><',line):root=False;continue
  m=re.search(r'DW_AT_(name|stmt_list|low_pc|high_pc)\s*:\s*(.*)',line)
  if m:cur[m[1]]=m[2].split(': ')[-1]
(d/'cu-index.json').write_text(json.dumps(rows,indent=2)+'\n')
commands=[]
def tool(root,name,args):
 cmd=['nice','-n','19','ionice','-c3',str(root/'lib64/ld-linux-x86-64.so.2'),'--library-path',f'{root}/lib64:{root}/usr/lib64',str(root/'usr/bin'/name),*map(str,args)];p=subprocess.run(cmd,capture_output=True,text=True);commands.append(dict(command=cmd,exit=p.returncode,stdout=p.stdout,stderr=p.stderr));assert not p.returncode,p.stderr;return p
# Only temporary diagnostic copies are altered. Original input and debug ELF stay unchanged.
tool(r,'llvm-objcopy',['--dump-section=.debug_info='+str(d/'all-info.bin'),src/'libavcodec.combined',d/'dump-copy.elf'])
data=(d/'all-info.bin').read_bytes();results=[]
for cu in rows:
 if cu['version']!=5 and cu.get('name') not in ['libavcodec/h264_cabac.c','libavcodec/h264_loopfilter.c']:continue
 off=cu['offset'];length=struct.unpack_from('<I',data,off)[0];assert length!=0xffffffff
 (d/'one-info.bin').write_bytes(data[off:off+4+length])
 tool(r,'llvm-objcopy',['--remove-section=.debug_aranges','--update-section=.debug_info='+str(d/'one-info.bin'),src/'libavcodec.combined',d/'one-cu.elf'])
 addr=cu.get('low_pc','0');addr={'libavcodec/h264_cabac.c':'0xcd684','libavcodec/h264_loopfilter.c':'0xfb180'}.get(cu.get('name'),addr)
 p=tool(g,'addr2line',['-a','-f','-i','-e',d/'one-cu.elf',addr]);results.append(dict(cu=cu,address=addr,warnings=p.stderr.count('bad file number'),stdout=p.stdout,stderr=p.stderr));print(cu.get('name'),results[-1]['warnings'],flush=True)
(d/'cu-isolation.json').write_text(json.dumps(dict(method='Diagnostic .debug_info contains exactly one original CU, .debug_aranges removed; original ELF not modified',results=results,commands=commands),indent=2)+'\n')
