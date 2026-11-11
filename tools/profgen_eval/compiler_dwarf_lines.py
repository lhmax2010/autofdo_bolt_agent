"""Static DWARF API evidence. No profile input; no source/compiler mutation."""
import json,subprocess,sys
from pathlib import Path
from run_scoped import WORK,ROOT,sha,platform
BASE=WORK/"docs/profgen/eval/prep/evidence"
OUT=BASE/"ruling2/supplement3/rev1/identity-gate"
TEMP=WORK/"temp/prep-identity-gate"
SOURCE=r'''
#include "llvm/DebugInfo/DWARF/DWARFContext.h"
#include "llvm/DebugInfo/DWARF/DWARFDebugLine.h"
#include "llvm/DebugInfo/DWARF/DWARFDie.h"
#include "llvm/DebugInfo/DWARF/DWARFUnit.h"
#include "llvm/Object/Binary.h"
#include "llvm/Object/ObjectFile.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/raw_ostream.h"
#include <algorithm>
#include <map>
#include <set>
using namespace llvm;
using Kind=DILineInfoSpecifier::FileLineInfoKind;
struct Info { DWARFDie Die; std::set<std::pair<std::string,uint32_t>> Lines;
  std::map<std::pair<std::string,uint32_t>,uint64_t> Witness;
  std::vector<std::pair<uint64_t,uint64_t>> Ranges; };
int main(int argc,char **argv) {
  if(argc!=2)return 2;
  auto Bin=object::createBinary(argv[1]);
  if(!Bin){errs()<<toString(Bin.takeError());return 1;}
  auto *Obj=dyn_cast<object::ObjectFile>(Bin->getBinary());
  if(!Obj)return 3;
  auto Ctx=DWARFContext::create(*Obj);
  for(auto &UP:Ctx->compile_units()) {
    auto *U=UP.get();std::map<uint64_t,Info> Infos;std::set<uint64_t> Cuts;
    std::function<bool(DWARFDie)> Visit=[&](DWARFDie D) {
      if(D.isSubroutineDIE()) {
        auto Rs=D.getAddressRanges();
        if(!Rs){errs()<<toString(Rs.takeError());return false;}
        for(auto R:*Rs)if(R.LowPC<R.HighPC) {
          auto &I=Infos[D.getOffset()];I.Die=D;I.Ranges.emplace_back(R.LowPC,R.HighPC);
          Cuts.insert(R.LowPC);Cuts.insert(R.HighPC);
        }
      }
      for(auto Child:D)if(!Visit(Child))return false;
      return true;
    };
    if(!Visit(U->getUnitDIE(false)))return 4;
    const auto *LT=Ctx->getLineTableForUnit(U);
    if(LT)for(size_t I=0;I+1<LT->Rows.size();++I) {
      auto &R=LT->Rows[I];auto &N=LT->Rows[I+1];
      if(R.EndSequence || R.Address.SectionIndex!=N.Address.SectionIndex ||
         R.Address.Address>=N.Address.Address)continue;
      std::string File;
      if(!LT->getFileNameByIndex(R.File,U->getCompilationDir()?U->getCompilationDir():"",Kind::AbsoluteFilePath,File)) {
        errs()<<"line file resolution failed CU="<<U->getOffset()<<" file="<<R.File<<"\n";return 5;
      }
      auto Add=[&](uint64_t A) {
        auto D=U->getSubroutineForAddress(A);
        if(D && Infos.count(D.getOffset())) {
          auto &V=Infos[D.getOffset()];auto K=std::make_pair(File,R.Line);
          V.Lines.insert(K);V.Witness.emplace(K,A);
        }
      };
      Add(R.Address.Address);
      for(auto C=Cuts.upper_bound(R.Address.Address);C!=Cuts.end()&&*C<N.Address.Address;++C)Add(*C);
    }
    for(auto &[Offset,I]:Infos) {
      auto D=I.Die;json::Array Lines,Ranges;
      for(auto &[F,L]:I.Lines)Lines.push_back(json::Object{{"file",F},{"line",L},{"address",I.Witness[{F,L}]}});
      for(auto [B,E]:I.Ranges)Ranges.push_back(json::Array{B,E});
      auto *Name=D.getSubroutineName(DINameKind::LinkageName);
      outs()<<json::Value(json::Object{{"die",Offset},{"cu",U->getOffset()},
        {"name",Name?Name:""},{"decl_file",D.getDeclFile(Kind::AbsoluteFilePath)},
        {"decl_line",D.getDeclLine()},{"ranges",std::move(Ranges)},
        {"leaf_lines",std::move(Lines)},{"line_table_present",bool(LT)}})<<"\n";
    }
  }
  return 0;
}
'''

def build():
    OUT.mkdir(parents=True,exist_ok=True);TEMP.mkdir(exist_ok=True)
    src=TEMP/"dwarf_lines_v2.cpp";src.write_text(SOURCE)
    cmd=[str(WORK/"temp/eval-prep11/bin/host-clang"),"-x","c++","-std=c++17","-O0",str(src),"-o",str(TEMP/"dwarf_lines_v2")]
    for inc in ("src/llvm/llvm/include","temp/llvm-profgen-enh/build/include"):cmd += ["-I",str(WORK/inc)]
    cmd += ["-L",str(ROOT/"usr/lib64"),"-lLLVM","-lstdc++"]
    p=subprocess.run(cmd,capture_output=True,text=True)
    (TEMP/"build.stderr").write_text(p.stderr)
    meta=dict(command=cmd,exit_code=p.returncode,source_sha256=sha(src),stderr=p.stderr)
    if not p.returncode:meta["tool_sha256"]=sha(TEMP/"dwarf_lines_v2")
    (OUT/"tool-build-v2.json").write_text(json.dumps(meta,indent=2)+"\n");print(p.stderr)
    return p.returncode

def collect(obj):
    meta=json.loads((BASE/(obj+"-S-inventory-tables/index.json")).read_text());elf=Path(meta["elf"])
    cmd=platform("llvm-dwarfdump")[:-1]+[str(TEMP/"dwarf_lines_v2"),str(elf)]
    out=TEMP/(obj+"-leaf-lines-v2.jsonl")
    with out.open("w") as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.PIPE,text=True)
    (OUT/(obj+"-command-v2.json")).write_text(json.dumps(dict(command=cmd,exit_code=p.returncode,
        elf=str(elf),elf_sha256=sha(elf),output=str(out),output_sha256=sha(out),bytes=out.stat().st_size,stderr=p.stderr),indent=2)+"\n")
    print(obj,p.returncode,out.stat().st_size,p.stderr)
    return p.returncode

if __name__=="__main__":raise SystemExit(build() if sys.argv[1]=="build" else collect(sys.argv[1]))
