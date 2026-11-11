"""Direct inline DIE caller attributes, including lexical-block children."""
import json,subprocess,sys
from pathlib import Path
from run_scoped import WORK,ROOT,platform,sha
from ruling34_inputs import OUT,TEMP,BASE,dump
SOURCE=r'''
#include "llvm/DebugInfo/DWARF/DWARFContext.h"
#include "llvm/DebugInfo/DWARF/DWARFDebugLine.h"
#include "llvm/DebugInfo/DWARF/DWARFDie.h"
#include "llvm/DebugInfo/DWARF/DWARFUnit.h"
#include "llvm/Object/Binary.h"
#include "llvm/Object/ObjectFile.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/raw_ostream.h"
#include <functional>
using namespace llvm;
int main(int argc,char **argv){
 if(argc!=2)return 2;
 auto B=object::createBinary(argv[1]);if(!B){errs()<<toString(B.takeError());return 3;}
 auto *O=dyn_cast<object::ObjectFile>(B->getBinary());if(!O)return 4;
 auto C=DWARFContext::create(*O);
 for(auto &UP:C->compile_units()){
  auto *U=UP.get();auto *LT=C->getLineTableForUnit(U);
  std::function<void(DWARFDie)> Visit=[&](DWARFDie D){
   if(D.getTag()==dwarf::DW_TAG_inlined_subroutine){
    auto F=dwarf::toUnsigned(D.find(dwarf::DW_AT_call_file));
    auto L=dwarf::toUnsigned(D.find(dwarf::DW_AT_call_line));
    std::string File;
    bool Resolved=F && LT && LT->getFileNameByIndex(*F,U->getCompilationDir()?U->getCompilationDir():"",
      DILineInfoSpecifier::FileLineInfoKind::AbsoluteFilePath,File);
    outs()<<json::Value(json::Object{{"die",D.getOffset()},{"cu",U->getOffset()},
       {"parent_die",D.getParent().getOffset()},{"call_file",File},{"call_file_index",F?int64_t(*F):-1},
       {"call_file_resolved",Resolved},{"call_line",L?*L:0},{"call_line_present",bool(L)}})<<"\n";
   }
   for(auto Ch:D)Visit(Ch);
  };
  Visit(U->getUnitDIE(false));outs().flush();
 }
 return 0;
}
'''
def build():
    src=TEMP/"direct_calls.cpp";src.write_text(SOURCE)
    cmd=[str(WORK/"temp/eval-prep11/bin/host-clang"),"-x","c++","-std=c++17","-O1",str(src),"-o",str(TEMP/"direct_calls")]
    for inc in ("src/llvm/llvm/include","temp/llvm-profgen-enh/build/include"):cmd+=["-I",str(WORK/inc)]
    cmd+=["-L",str(ROOT/"usr/lib64"),"-lLLVM","-lstdc++"]
    p=subprocess.run(cmd,capture_output=True,text=True)
    dump(OUT/"direct-calls-build.json",dict(command=cmd,exit_code=p.returncode,stderr=p.stderr,source_sha256=sha(src),
       tool_sha256=sha(TEMP/"direct_calls") if not p.returncode else None))
    print(p.stderr);return p.returncode
def collect(obj):
    elf=Path(json.loads((BASE/(obj+"-S-inventory-tables/index.json")).read_text())["elf"])
    out=TEMP/(obj+"-direct-calls.jsonl");assert not out.exists()
    cmd=platform("llvm-dwarfdump")[:-1]+[str(TEMP/"direct_calls"),str(elf)]
    with out.open("w") as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.PIPE,text=True)
    dump(OUT/(obj+"-direct-calls-command.json"),dict(command=cmd,exit_code=p.returncode,stderr=p.stderr,
        elf_sha256=sha(elf),output=str(out),output_sha256=sha(out)))
    return p.returncode
if __name__=="__main__":raise SystemExit(build() if sys.argv[1]=="build" else collect(sys.argv[1]))
