#include "llvm/DebugInfo/Symbolize/Symbolize.h"
#include "llvm/Support/Error.h"
#include "llvm/Support/raw_ostream.h"
int main(int argc, char **argv) {
  llvm::symbolize::LLVMSymbolizer::Options O;
  O.PrintFunctions=llvm::DILineInfoSpecifier::FunctionNameKind::LinkageName;
  O.UseSymbolTable=false; O.Demangle=false; O.RelativeAddresses=false;
  llvm::symbolize::LLVMSymbolizer S(O);
  for (uint64_t A: {0x1000,0x1001,0x1002,0x1006}) {
    auto R=S.symbolizeInlinedCode(argv[1], {A,llvm::object::SectionedAddress::UndefSection});
    if(!R) {llvm::logAllUnhandledErrors(R.takeError(),llvm::errs());return 1;}
    llvm::outs()<<llvm::format_hex(A,10)<<" frames="<<R->getNumberOfFrames()<<"\n";
    for(unsigned I=0;I<R->getNumberOfFrames();++I) {
      auto F=R->getFrame(I);llvm::outs()<<"  function="<<F.FunctionName<<" line="<<F.Line<<" start_line="<<F.StartLine<<" file="<<F.FileName<<"\n";
    }
  }
}
