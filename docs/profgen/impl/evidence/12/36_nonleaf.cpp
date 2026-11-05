#include "llvm/DebugInfo/Symbolize/Symbolize.h"
#include "llvm/Support/Error.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/raw_ostream.h"
#include <iostream>
int main(int argc, char **argv) {
  llvm::symbolize::LLVMSymbolizer::Options O;
  O.PrintFunctions=llvm::DILineInfoSpecifier::FunctionNameKind::LinkageName;
  O.UseSymbolTable=false; O.Demangle=false; O.RelativeAddresses=false;
  llvm::symbolize::LLVMSymbolizer S(O);
  uint64_t A,Q;
  while(std::cin >> std::hex >> A >> Q) {
    auto R=S.symbolizeInlinedCode(argv[1], {Q,llvm::object::SectionedAddress::UndefSection});
    if(!R) {llvm::logAllUnhandledErrors(R.takeError(),llvm::errs());return 1;}
    bool Usable=R->getNumberOfFrames() && R->getFrame(0).Line>0;
    llvm::json::Array Zero;std::string Root;
    for(unsigned I=0;I<R->getNumberOfFrames();++I) {
      const auto &F=R->getFrame(I);
      if(F.FunctionName.empty() || F.FunctionName=="<invalid>")Usable=false;
      if(I && F.Line==0)Zero.push_back(F.FunctionName);
      Root=F.FunctionName;
    }
    llvm::outs()<<llvm::json::Value(llvm::json::Object{{"address",A},{"query",Q},{"usable",Usable},{"root",Root},{"nonleaf_line_zero",std::move(Zero)}})<<"\n";
  }
}
