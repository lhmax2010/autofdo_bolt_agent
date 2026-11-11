"""New helper for C-owned line rows and direct-child inline call evidence.

Old collectors and outputs are unchanged. The compiler and LLVM libraries are
only executed/linked; their sources and binaries are not modified.
"""
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
#include <map>
#include <set>
using namespace llvm;
using Kind=DILineInfoSpecifier::FileLineInfoKind;
struct Info {
 DWARFDie D; bool SubtreeCode=false;
 std::vector<std::pair<uint64_t,uint64_t>> Ranges;
 std::map<std::pair<std::string,uint32_t>,uint64_t> Lines;
};
void emit(json::Object O){outs()<<json::Value(std::move(O))<<"\n";}
int main(int argc,char **argv) {
 if(argc!=2)return 2;
 auto Bin=object::createBinary(argv[1]);
 if(!Bin){errs()<<toString(Bin.takeError());return 3;}
 auto *Obj=dyn_cast<object::ObjectFile>(Bin->getBinary());if(!Obj)return 4;
 auto Ctx=DWARFContext::create(*Obj);
 for(auto &UP:Ctx->compile_units()){
  auto *U=UP.get();auto Root=U->getUnitDIE(false);
  std::map<uint64_t,Info> Infos;std::set<uint64_t> Cuts;
  std::map<uint64_t,bool> Code;bool OK=true;
  std::function<void(DWARFDie)> Visit=[&](DWARFDie D){
   auto RR=D.getAddressRanges();
   if(!RR){errs()<<toString(RR.takeError());OK=false;return;}
   bool Has=false;
   for(auto R:*RR)if(R.LowPC<R.HighPC)Has=true;
   for(auto Child:D){Visit(Child);Has|=Code[Child.getOffset()];}
   Code[D.getOffset()]=Has;
   if(!D.isSubroutineDIE())return;
   Info I;I.D=D;I.SubtreeCode=Has;
   for(auto R:*RR)if(R.LowPC<R.HighPC){
    I.Ranges.emplace_back(R.LowPC,R.HighPC);Cuts.insert(R.LowPC);Cuts.insert(R.HighPC);
   }
   Infos.emplace(D.getOffset(),std::move(I));
  };
  Visit(Root);if(!OK)return 5;
  const auto *LT=Ctx->getLineTableForUnit(U);
  auto FileName=[&](uint64_t Idx,std::string &F) {
   return LT && LT->getFileNameByIndex(Idx,U->getCompilationDir()?U->getCompilationDir():"",Kind::AbsoluteFilePath,F);
  };
  if(LT)for(size_t N=0;N+1<LT->Rows.size();++N){
   auto &R=LT->Rows[N];auto &Next=LT->Rows[N+1];
   if(R.EndSequence || R.Address.SectionIndex!=Next.Address.SectionIndex || R.Address.Address>=Next.Address.Address)continue;
   std::string File;if(!FileName(R.File,File)){errs()<<"line file resolution failed\n";return 6;}
   auto Add=[&](uint64_t A){
    auto D=U->getSubroutineForAddress(A);
    if(D && Infos.count(D.getOffset()))Infos.at(D.getOffset()).Lines.emplace(std::make_pair(File,R.Line),A);
   };
   Add(R.Address.Address);
   for(auto C=Cuts.upper_bound(R.Address.Address);C!=Cuts.end()&&*C<Next.Address.Address;++C)Add(*C);
  }
  for(auto &[Offset,I]:Infos){
   auto D=I.D;auto *Name=D.getSubroutineName(DINameKind::LinkageName);
   json::Array Ranges,Lines,Calls;
   for(auto [A,B]:I.Ranges)Ranges.push_back(json::Array{A,B});
   for(auto &[FL,A]:I.Lines)Lines.push_back(json::Object{{"file",FL.first},{"line",FL.second},{"address",A}});
   for(auto Ch:D)if(Ch.getTag()==dwarf::DW_TAG_inlined_subroutine){
    auto FI=dwarf::toUnsigned(Ch.find(dwarf::DW_AT_call_file));
    auto LI=dwarf::toUnsigned(Ch.find(dwarf::DW_AT_call_line));
    std::string File;bool Resolved=FI && FileName(*FI,File);
    Calls.push_back(json::Object{{"die",Ch.getOffset()},{"call_file",File},
      {"call_file_index",FI?int64_t(*FI):int64_t(-1)},{"call_file_resolved",Resolved},
      {"call_line",LI?*LI:0},{"call_line_present",bool(LI)}});
   }
   auto Parent=D.getParent();auto Origin=D.getAttributeValueAsReferencedDie(dwarf::DW_AT_abstract_origin);
   emit(json::Object{{"kind","function"},{"die",Offset},{"cu",U->getOffset()},{"cu_die",Root.getOffset()},
      {"parent",Parent?int64_t(Parent.getOffset()):int64_t(-1)},
      {"tag",D.isSubprogramDIE()?"subprogram":"inlined_subroutine"},{"name",Name?Name:""},
      {"decl_file",D.getDeclFile(Kind::AbsoluteFilePath)},{"decl_line",D.getDeclLine()},
      {"declaration",bool(dwarf::toUnsigned(D.find(dwarf::DW_AT_declaration),0))},
      {"abstract_origin",Origin?int64_t(Origin.getOffset()):int64_t(-1)},
      {"ranges",std::move(Ranges)},{"self_or_descendant_has_ranges",I.SubtreeCode},
      {"leaf_lines",std::move(Lines)},{"direct_inline_calls",std::move(Calls)}});
  }
  if(LT)for(size_t N=0;N<LT->Rows.size();++N){
   auto &R=LT->Rows[N];std::string File;bool Resolved=FileName(R.File,File);json::Array Chain;
   if(!R.EndSequence)for(auto D=U->getSubroutineForAddress(R.Address.Address);D;D=D.getParent())
      if(D.isSubroutineDIE())Chain.push_back(D.getOffset());
   emit(json::Object{{"kind","line_row"},{"cu",U->getOffset()},{"row",int64_t(N)},
      {"address",R.Address.Address},{"file",File},{"file_resolved",Resolved},
      {"line",R.Line},{"end_sequence",bool(R.EndSequence)},{"is_stmt",bool(R.IsStmt)},
      {"dies_leaf_to_root",std::move(Chain)}});
  }
  outs().flush();
 }
 return 0;
}
'''
def build():
    src=TEMP/"ruling34_dwarf.cpp";src.write_text(SOURCE)
    cc=WORK/"temp/eval-prep11/bin/host-clang"
    cmd=[str(cc),"-x","c++","-std=c++17","-O1",str(src),"-o",str(TEMP/"ruling34_dwarf")]
    for inc in ("src/llvm/llvm/include","temp/llvm-profgen-enh/build/include"):cmd+=["-I",str(WORK/inc)]
    cmd+=["-L",str(ROOT/"usr/lib64"),"-lLLVM","-lstdc++"]
    p=subprocess.run(cmd,capture_output=True,text=True)
    m=dict(command=cmd,exit_code=p.returncode,source_sha256=sha(src),stderr=p.stderr)
    if not p.returncode:m["tool_sha256"]=sha(TEMP/"ruling34_dwarf")
    dump(OUT/"tool-build.json",m);print(p.stderr);return p.returncode
def collect(obj,stage):
    ix=BASE/(obj+"-"+stage+"-inventory-tables/index.json")
    elf=Path(json.loads(ix.read_text())["elf"])
    out=TEMP/(obj+"-"+stage+"-dwarf.jsonl");assert not out.exists()
    cmd=platform("llvm-dwarfdump")[:-1]+[str(TEMP/"ruling34_dwarf"),str(elf)]
    with out.open("w") as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.PIPE,text=True)
    m=dict(command=cmd,exit_code=p.returncode,elf=str(elf),elf_sha256=sha(elf),
           output=str(out),output_sha256=sha(out),bytes=out.stat().st_size,stderr=p.stderr,
           tool_sha256=sha(TEMP/"ruling34_dwarf"))
    dump(OUT/(obj+"-"+stage+"-dwarf-command.json"),m)
    print(json.dumps(m),flush=True);return p.returncode
if __name__=="__main__":raise SystemExit(build() if sys.argv[1]=="build" else collect(*sys.argv[1:]))
