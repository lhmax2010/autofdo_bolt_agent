"""Independent all-DIE callsite evidence, used only for description, never C."""
import json,subprocess,sys
from pathlib import Path
from v17_domain import OUT,TEMP,BASE,dump,SOURCE
from run_scoped import WORK,ROOT,sha,platform
CPP=SOURCE.replace('#include "llvm/Support/JSON.h"', '#include "llvm/Support/JSON.h"\n#include <functional>')
a=CPP.index('  unsigned SI=0;')
b=CPP.index('\n }\n return 0;',a)
CPP=CPP[:a]+r"""
  std::function<void(DWARFDie)> Visit=[&](DWARFDie D){
   if(D.getTag()==dwarf::DW_TAG_inlined_subroutine){
    auto F=dwarf::toUnsigned(D.find(dwarf::DW_AT_call_file));
    auto N=dwarf::toUnsigned(D.find(dwarf::DW_AT_call_line));
    std::string Name;
    bool OK=F && L->getFileNameByIndex(*F,U->getCompilationDir()?U->getCompilationDir():"",
      DILineInfoSpecifier::FileLineInfoKind::AbsoluteFilePath,Name);
    emit(json::Object{{"kind","call"},{"die",D.getOffset()},{"cu",U->getOffset()},
      {"file",Name},{"file_resolved",OK},{"line",N?*N:0}});
   }
   for(auto Ch:D)Visit(Ch);
  };
  Visit(D);
""" +CPP[b:]
def build():
 src=TEMP/"all_calls.cpp";src.write_text(CPP)
 cmd=[str(WORK/"temp/eval-prep11/bin/host-clang"),"-x","c++","-std=c++17","-O1",str(src),"-o",str(TEMP/"all_calls"),
      "-I",str(WORK/"src/llvm/llvm/include"),"-I",str(WORK/"temp/llvm-profgen-enh/build/include"),"-L",str(ROOT/"usr/lib64"),"-lLLVM","-lstdc++"]
 p=subprocess.run(cmd,capture_output=True,text=True)
 dump(OUT/"calls-build.json",dict(command=cmd,exit_code=p.returncode,stderr=p.stderr,source_sha256=sha(src),tool_sha256=sha(TEMP/"all_calls") if p.returncode==0 else None))
 print(p.stderr);return p.returncode
def collect(obj):
 result=[]
 for stage in ("C","S"):
  d=json.loads((OUT/(obj+"-domain/index.json")).read_text())
  elf=Path(next(x["elf"] for x in d["raw"] if x["stage"]==stage))
  raw=TEMP/(obj+"-"+stage+"-calls.jsonl");assert not raw.exists()
  cmd=platform("llvm-dwarfdump")[:-1]+[str(TEMP/"all_calls"),str(elf)]
  with raw.open("w") as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.PIPE,text=True)
  result.append(dict(stage=stage,command=cmd,exit_code=p.returncode,stderr=p.stderr,elf_sha256=sha(elf),output=str(raw),sha256=sha(raw)))
  assert p.returncode==0 and not p.stderr
 dump(OUT/(obj+"-calls.json"),result)
 print(obj,"all call attributes collected")
if __name__=="__main__":raise SystemExit(build() if sys.argv[1]=="build" else collect(sys.argv[1]))
