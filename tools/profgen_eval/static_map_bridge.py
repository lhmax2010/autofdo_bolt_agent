"""Static-only bridge to existing GBS LLVM APIs and unchanged IP boundary code.

No sample input and no profile output. Official compiler/profgen files are not
modified; a separately named helper and source snapshots live in WORKDIR/temp.
"""
import json,subprocess,sys,shutil
from pathlib import Path
from run_scoped import WORK,ROOT,sha,platform
BASE=WORK/"docs/profgen/eval/prep/evidence"
OUT=BASE/"identity-gate"
TEMP=WORK/"temp/prep-static-gate"
PROFGEN=WORK/"temp/llvm-profgen-enh/llvm/tools/llvm-profgen"
SOURCE=r"""
#include "IPBoundary.h"
#include "llvm/DebugInfo/DWARF/DWARFContext.h"
#include "llvm/DebugInfo/DWARF/DWARFCompileUnit.h"
#include "llvm/DebugInfo/DWARF/DWARFDie.h"
#include "llvm/DebugInfo/Symbolize/Symbolize.h"
#include "llvm/IR/DebugInfoMetadata.h"
#include "llvm/Object/Binary.h"
#include "llvm/Object/ELFObjectFile.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/MemoryBuffer.h"
#include "llvm/Support/raw_ostream.h"
#include <algorithm>
#include <functional>
#include <map>
#include <set>
using namespace llvm;
using Kind=DILineInfoSpecifier::FileLineInfoKind;
using Range=std::pair<uint64_t,uint64_t>;
struct Info { DWARFDie D; uint64_t Top,CU; std::string Name;
  std::vector<Range> Original,Normalized; };
void emit(json::Object O){outs()<<json::Value(std::move(O))<<"\n";}
json::Array ranges(const std::vector<Range> &Rs) {
  json::Array A;for(auto [B,E]:Rs)A.push_back(json::Array{B,E});return A;
}
json::Array frames(const DIInliningInfo &II,bool FSD) {
  json::Array A;
  for(unsigned I=0;I<II.getNumberOfFrames();++I) {
    auto &F=II.getFrame(I);
    A.push_back(json::Object{{"name",F.FunctionName},{"file",F.FileName},
      {"line",F.Line},{"column",F.Column},{"start_line",F.StartLine},
      {"discriminator",F.Discriminator},{"base_discriminator",FSD?F.Discriminator:
       DILocation::getBaseDiscriminatorFromDiscriminator(F.Discriminator,false)}});
  }return A;
}
int main(int argc,char **argv) {
  if(argc<4)return 2;
  StringRef Mode=argv[1],Run=argv[2],Debug=argv[3];
  auto Binary=object::createBinary(Debug);
  if(!Binary){errs()<<toString(Binary.takeError());return 3;}
  auto *Obj=dyn_cast<object::ObjectFile>(Binary->getBinary());if(!Obj)return 4;
  auto Ctx=DWARFContext::create(*Obj);
  bool ARM32=isa<object::ELF32LEObjectFile>(Obj) && cast<object::ELFObjectFileBase>(Obj)->getEMachine()==ELF::EM_ARM;
  bool FSD=false;
  for(auto &S:Obj->symbols()) {auto N=S.getName();if(!N){errs()<<toString(N.takeError());return 4;}
    FSD|=*N=="__llvm_fs_discriminator__";}
  auto BM=sampleprof::IPBoundaryMap::load(Run,Debug,Mode=="map");
  std::string MappingError;if(!BM)MappingError=toString(BM.takeError());
  std::map<uint64_t,Info> Infos;std::map<std::string,std::vector<uint64_t>> Groups;
  std::map<uint64_t,uint64_t> Aliases;
  for(auto &UP:Ctx->compile_units()) {
    auto *U=UP.get();auto Root=U->getUnitDIE(false);
    std::function<bool(DWARFDie,uint64_t)> Visit=[&](DWARFDie D,uint64_t Top) {
      if(D.isSubroutineDIE()) {
        auto RR=D.getAddressRanges();if(!RR){errs()<<toString(RR.takeError());return false;}
        std::vector<Range> Rs;for(auto R:*RR)if(R.LowPC<R.HighPC)Rs.emplace_back(R.LowPC,R.HighPC);
        if(!Rs.empty()) {
          if(D.isSubprogramDIE())Top=D.getOffset();
          auto *N=D.getSubroutineName(DINameKind::LinkageName);
          Info I{D,Top,U->getOffset(),N?N:"",Rs,Rs};
          if(D.isSubprogramDIE()) {
            Groups[I.Name].push_back(D.getOffset());
            if(ARM32)for(auto &R:I.Normalized)if(R.first&1) {
              if(BM) {
                auto Thumb=BM->isThumbAddress(R.first&~uint64_t(1));
                if(!Thumb) {consumeError(Thumb.takeError());continue;}
                if(*Thumb) {Aliases.emplace(R.first&~uint64_t(1),R.first);R.first&=~uint64_t(1);R.second&=~uint64_t(1);}
              }
            }
          }
          Infos.emplace(D.getOffset(),std::move(I));
        }
      }
      for(auto Child:D)if(!Visit(Child,Top))return false;
      return true;
    };
    if(!Visit(Root,0))return 5;
  }
  if(Mode=="inventory") {
    emit(json::Object{{"kind","metadata"},{"fs_discriminator",FSD},{"mapping_error",MappingError}});
    for(auto &[Offset,I]:Infos) {
      auto Origin=I.D.getAttributeValueAsReferencedDie(dwarf::DW_AT_abstract_origin);
      emit(json::Object{{"kind","die"},{"die",Offset},{"cu",I.CU},{"top_die",I.Top},
        {"tag",I.D.isSubprogramDIE()?"subprogram":"inlined_subroutine"},
        {"name",I.Name},{"decl_file",I.D.getDeclFile(Kind::AbsoluteFilePath)},
        {"decl_line",I.D.getDeclLine()}, {"abstract_origin",Origin?int64_t(Origin.getOffset()):int64_t(-1)},
        {"ranges",ranges(I.Original)},{"normalized_ranges",ranges(I.Normalized)}});
    }
    return 0;
  }
  if(Mode!="map" || argc!=5)return 2;
  auto Buf=MemoryBuffer::getFile(argv[4]);if(!Buf){errs()<<"selection open failed";return 6;}
  auto Selection=json::parse((*Buf)->getBuffer());if(!Selection){errs()<<toString(Selection.takeError());return 6;}
  std::set<std::string> Wanted;auto *A=Selection->getAsArray();if(!A)return 6;
  for(auto &V:*A){auto N=V.getAsString();if(!N)return 6;Wanted.insert(N->str());}
  symbolize::LLVMSymbolizer::Options O;
  O.PrintFunctions=DILineInfoSpecifier::FunctionNameKind::LinkageName;
  O.Demangle=false;O.DefaultArch=ARM32?"arm":"aarch64";O.UseSymbolTable=false;O.RelativeAddresses=false;
  symbolize::LLVMSymbolizer Sym(O);
  for(auto &Name:Wanted) {
    auto It=Groups.find(Name);if(It==Groups.end()){errs()<<"unknown selected group "<<Name;return 7;}
    std::vector<Range> Rs;json::Array IDs;
    for(auto ID:It->second) {IDs.push_back(ID);auto &I=Infos.at(ID);Rs.insert(Rs.end(),I.Normalized.begin(),I.Normalized.end());}
    if(!BM) {emit(json::Object{{"kind","boundary_unavailable"},{"name",Name},{"reason",MappingError},{"dies",std::move(IDs)}});continue;}
    auto B=BM->enumerate(Name,Rs);
    if(!B) {emit(json::Object{{"kind","boundary_unavailable"},{"name",Name},{"reason",toString(B.takeError())},{"dies",std::move(IDs)}});continue;}
    emit(json::Object{{"kind","group"},{"name",Name},{"dies",std::move(IDs)},
      {"ranges",ranges(Rs)},{"instruction_count",int64_t(B->Instructions.size())}});
    for(auto &Inst:B->Instructions) {
      auto Q=[&](uint64_t Addr){return Sym.symbolizeInlinedCode(Debug.str(),{Addr,object::SectionedAddress::UndefSection});};
      uint64_t Address=Inst.Address,Query=Address;
      auto R=Q(Address);if(!R){errs()<<toString(R.takeError());return 8;}
      bool Alias=false;
      if(Aliases.count(Address)) {
        Alias=true;Query=Aliases.at(Address);auto T=Q(Query);if(!T){errs()<<toString(T.takeError());return 8;}
        bool OK=R->getNumberOfFrames() && T->getNumberOfFrames();
        if(OK){auto &X=R->getFrame(0);auto &Y=T->getFrame(0);OK=X.FileName==Y.FileName && X.Line==Y.Line && X.Discriminator==Y.Discriminator;}
        if(!OK){emit(json::Object{{"kind","alias_mismatch"},{"address",Address},
          {"original",frames(*R,FSD)},{"alias",frames(*T,FSD)}});return 9;}
        R=std::move(T);
      }
      json::Array Chain;
      if(auto *U=Ctx->getCompileUnitForCodeAddress(Query)) {
        for(auto D=U->getSubroutineForAddress(Query);D;D=D.getParent())
          if(D.isSubroutineDIE())Chain.push_back(D.getOffset());
      }
      emit(json::Object{{"kind","instruction"},{"group",Name},{"address",Address},
        {"size",Inst.Size},{"range_index",int64_t(Inst.RangeIndex)},
        {"query",Query},{"alias",Alias},{"dies_leaf_to_root",std::move(Chain)},
        {"frames_leaf_to_root",frames(*R,FSD)}});
    }
    outs().flush();
  }
  return 0;
}
"""
def paths(obj):
    meta=json.loads((BASE/(obj+"-S-inventory-tables/index.json")).read_text())
    debug=Path(meta["elf"])
    runtime=Path(str(debug).replace("/usr/lib/debug/usr/","/usr/").removesuffix(".debug"))
    assert debug.exists() and runtime.exists()
    return runtime,debug

def build():
    OUT.mkdir(exist_ok=True);TEMP.mkdir(exist_ok=True)
    cpp=TEMP/"static_map.cpp";cpp.write_text(SOURCE)
    inputs=[]
    for name in ("IPBoundary.cpp","IPBoundary.h"):
        src=PROFGEN/name;dst=TEMP/name;shutil.copyfile(src,dst)
        assert sha(src)==sha(dst);inputs.append(dict(path=str(src),sha256=sha(src)))
    cc=WORK/"temp/eval-prep11/bin/host-clang"
    ver=subprocess.run([str(cc),"--version"],capture_output=True,text=True)
    assert ver.returncode==0 and "22.1.8" in ver.stdout
    cmd=[str(cc),"-x","c++","-std=c++17","-O1",str(cpp),str(TEMP/"IPBoundary.cpp"),"-o",str(TEMP/"static_map")]
    for inc in ("src/llvm/llvm/include","temp/llvm-profgen-enh/build/include"):cmd += ["-I",str(WORK/inc)]
    cmd += ["-I",str(TEMP),"-L",str(ROOT/"usr/lib64"),"-lLLVM","-lstdc++"]
    p=subprocess.run(cmd,capture_output=True,text=True)
    meta=dict(command=cmd,exit_code=p.returncode,source_sha256=sha(cpp),boundary_inputs=inputs,
              compiler_version=ver.stdout,compiler_wrapper_sha256=sha(cc),stderr=p.stderr)
    if not p.returncode:meta["tool_sha256"]=sha(TEMP/"static_map")
    (OUT/"static-tool-build.json").write_text(json.dumps(meta,indent=2)+"\n");print(p.stderr)
    return p.returncode

def collect(mode,obj):
    runtime,debug=paths(obj);selection=TEMP/(obj+"-selected-groups.json")
    cmd=platform("llvm-dwarfdump")[:-1]+[str(TEMP/"static_map"),mode,str(runtime),str(debug)]
    if mode=="map":cmd.append(str(selection))
    output=TEMP/(obj+"-"+mode+".jsonl")
    assert not output.exists(),output
    with output.open("w") as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.PIPE,text=True)
    meta=dict(command=cmd,exit_code=p.returncode,runtime=str(runtime),runtime_sha256=sha(runtime),
              debug=str(debug),debug_sha256=sha(debug),output=str(output),output_sha256=sha(output),
              bytes=output.stat().st_size,stderr=p.stderr,tool_sha256=sha(TEMP/"static_map"))
    if mode=="map":meta["selection_sha256"]=sha(selection)
    (OUT/(obj+"-"+mode+"-command.json")).write_text(json.dumps(meta,indent=2)+"\n")
    print(json.dumps(meta),flush=True);return p.returncode
if __name__=="__main__":raise SystemExit(build() if sys.argv[1]=="build" else collect(*sys.argv[1:]))
