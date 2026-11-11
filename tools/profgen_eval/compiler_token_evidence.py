"""External, read-only Clang API bridge: actual per-token macro flags, no inference.

Generated C++ stays in temp. Uses only existing GBS libraries/source headers.
No LLVM sources, profiles, installed packages, or target binaries are changed.
"""
import argparse
import json
import subprocess
from pathlib import Path
from run_scoped import WORK, ROOT, sha

INPUT = WORK / "docs/profgen/eval/prep/evidence/ruling2"
BASE = INPUT / "supplement3/rev1"
OUT = WORK / "temp/prep-ruling2/token-api-supplement3-rev1"
SOURCE = r"""
#include "clang/AST/ASTConsumer.h"
#include "clang/AST/Decl.h"
#include "clang/AST/Stmt.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Frontend/FrontendPluginRegistry.h"
#include "clang/Lex/Lexer.h"
#include "clang/Lex/MacroArgs.h"
#include "clang/Lex/PPCallbacks.h"
#include "clang/Lex/Preprocessor.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/MemoryBuffer.h"
#include "llvm/Support/raw_ostream.h"
#include <set>
using namespace clang;
namespace {
struct Recorder {
  CompilerInstance &CI;
  SourceManager &SM;
  std::unique_ptr<llvm::raw_fd_ostream> Out;
  std::set<std::pair<std::string,unsigned>> Targets;
  Recorder(CompilerInstance &C, const std::string &Path,
           const std::string &Config): CI(C), SM(C.getSourceManager()) {
    std::error_code EC;
    Out = std::make_unique<llvm::raw_fd_ostream>(Path, EC);
    if (EC) llvm::report_fatal_error("cannot create token evidence");
    auto Buf = llvm::MemoryBuffer::getFile(Config);
    if (!Buf) llvm::report_fatal_error("cannot read target configuration");
    auto J = llvm::json::parse((*Buf)->getBuffer());
    if (!J || !J->getAsArray()) llvm::report_fatal_error("bad token configuration");
    for (auto &V : *J->getAsArray()) {
      auto *O = V.getAsObject();
      Targets.emplace(O->getString("file")->str(), unsigned(*O->getInteger("line")));
    }
  }
  std::string filename(SourceLocation L) {
    std::string F = SM.getFilename(L).str();
    while (F.compare(0,2,"./") == 0) F.erase(0,2);
    return F;
  }
  bool selected(SourceLocation L) {
    L = SM.getExpansionLoc(L);
    return L.isValid() && Targets.count({filename(L), SM.getSpellingLineNumber(L)});
  }
  llvm::json::Object loc(SourceLocation L) {
    if (L.isInvalid()) return llvm::json::Object{{"valid",false}};
    SourceLocation S = SM.getSpellingLoc(L);
    auto P = SM.getPresumedLoc(S);
    return llvm::json::Object{{"raw", int64_t(L.getRawEncoding())}, {"file",filename(S)},
            {"presumed_file",P.isValid()?P.getFilename():""},
            {"line",SM.getSpellingLineNumber(S)}, {"column",SM.getSpellingColumnNumber(S)},
            {"offset",SM.getFileOffset(S)}, {"file_id",SM.getFileID(L).getHashValue()}, {"is_macro",L.isMacroID()},
            {"is_scratch",SM.isWrittenInScratchSpace(S)}};
  }
  llvm::json::Object range(SourceRange R) {
    return llvm::json::Object{{"begin",loc(R.getBegin())},{"end",loc(R.getEnd())}};
  }
  void emit(llvm::json::Object O) { *Out << llvm::json::Value(std::move(O)) << "\n"; Out->flush(); }
  llvm::json::Object owner(SourceLocation L) {
    if (!L.isMacroID()) return llvm::json::Object{{"valid",false}};
    return llvm::json::Object{
      {"macro",Lexer::getImmediateMacroName(L, SM, CI.getLangOpts()).str()},
      {"instance_range",range(SM.getImmediateExpansionRange(L).getAsRange())},
      {"file_id",SM.getFileID(L).getHashValue()}};
  }
  llvm::json::Object lexText(const std::string &S) {
    auto Buffer = llvm::MemoryBuffer::getMemBufferCopy(S);
    Lexer Lex(SourceLocation(), CI.getLangOpts(), Buffer->getBufferStart(),
              Buffer->getBufferStart(), Buffer->getBufferEnd());
    Token T; Lex.LexFromRawLexer(T);
    auto RawKind = std::string(T.getName());
    if (T.is(tok::raw_identifier)) CI.getPreprocessor().LookUpIdentifierInfo(T);
    bool Whole = T.getLength()==S.size();
    return llvm::json::Object{{"text",S},{"raw_kind",RawKind},
                             {"kind",T.getName()},{"whole_token",Whole}};
  }
  llvm::json::Object token(const Token &T) {
    SourceLocation L = T.getLocation();
    llvm::json::Array Trace;
    SourceLocation C = L;
    for (unsigned I=0; C.isMacroID() && I<64; ++I) {
      Trace.push_back(llvm::json::Object{
        {"macro",Lexer::getImmediateMacroName(C, SM, CI.getLangOpts()).str()},
        {"location",loc(C)}, {"isMacroArgExpansion",SM.isMacroArgExpansion(C)},
        {"immediate_spelling",loc(SM.getImmediateSpellingLoc(C))},
        {"immediate_expansion",range(SM.getImmediateExpansionRange(C).getAsRange())},
        {"begin_owner",owner(SM.getImmediateExpansionRange(C).getBegin())},
        {"end_owner",owner(SM.getImmediateExpansionRange(C).getEnd())}});
      auto Next = SM.getImmediateMacroCallerLoc(C);
      if (Next == C) break;
      C = Next;
    }
    return llvm::json::Object{{"kind",T.getName()}, {"text",CI.getPreprocessor().getSpelling(T)},
            {"location",loc(L)}, {"length",T.getLength()}, {"spelling",loc(SM.getSpellingLoc(L))},
            {"expansion",loc(SM.getExpansionLoc(L))},
            {"isMacroArgExpansion",SM.isMacroArgExpansion(L)}, {"trace",std::move(Trace)}};
  }
};
struct Callbacks: PPCallbacks {
  std::shared_ptr<Recorder> Owner;
  Recorder &R;
  Callbacks(std::shared_ptr<Recorder> Rec): Owner(Rec), R(*Rec) {}
  void MacroExpands(const Token &Name, const MacroDefinition &MD, SourceRange Call,
                    const MacroArgs *Args) override {
    if (!R.selected(Name.getLocation())) return;
    const MacroInfo *MI = MD.getMacroInfo();
    llvm::json::Array Body, Arguments, ArgumentSlots, PasteFragments;
    for (const auto &T: MI->tokens()) {
      auto O=R.token(T);
      O["parameter_num"]=T.getIdentifierInfo()?MI->getParameterNum(T.getIdentifierInfo()):-1;
      Body.push_back(std::move(O));
    }
    auto DefTokens=MI->tokens();
    for (unsigned I=0; I+2<DefTokens.size(); ++I) {
      if (!DefTokens[I+1].is(tok::hashhash)) continue;
      unsigned J=I;
      std::string Spliced; llvm::json::Array Prefixes;
      bool Resolved=true;
      do {
        const Token *T=&DefTokens[J];
        int Param=T->getIdentifierInfo()?MI->getParameterNum(T->getIdentifierInfo()):-1;
        if (Param>=0) {
          if (!Args || unsigned(Param)>=Args->getNumMacroArguments()) {Resolved=false;break;}
          T=Args->getUnexpArgument(Param);
          if (T->is(tok::eof) || !(T+1)->is(tok::eof)) {Resolved=false;break;}
        }
        Spliced+=R.CI.getPreprocessor().getSpelling(*T);
        Prefixes.push_back(R.lexText(Spliced));
        if (J+2>=DefTokens.size() || !DefTokens[J+1].is(tok::hashhash)) break;
        J+=2;
      } while (true);
      PasteFragments.push_back(llvm::json::Object{
        {"begin",R.loc(DefTokens[I].getLocation())},{"end",R.loc(DefTokens[J].getLocation())},
        {"operands_resolved",Resolved},{"prefix_lexing",std::move(Prefixes)}});
      while (I+2<DefTokens.size() && DefTokens[I+1].is(tok::hashhash)) I+=2;
    }
    if (Args) for (unsigned I=0; I<Args->getNumMacroArguments(); ++I) {
      llvm::json::Array A;
      for (const Token *T=Args->getUnexpArgument(I); !T->is(tok::eof); ++T) A.push_back(R.token(*T));
      const Token *First = Args->getUnexpArgument(I), *Last = First;
      unsigned Count = 0;
      for (const Token *T=First; !T->is(tok::eof); ++T) {Last=T; ++Count;}
      llvm::json::Object Slot{{"slot",I},{"count",Count},
        {"copied_in_macroexpands",true},{"method","MacroArgs::getUnexpArgument"},
        {"invocation",R.range(Call)}, {"name_raw",Name.getLocation().getRawEncoding()}};
      if (Count) {
        auto B=R.SM.getSpellingLoc(First->getLocation());
        auto E=R.SM.getSpellingLoc(Last->getLocation()).getLocWithOffset(Last->getLength());
        Slot["begin"]=R.loc(B); Slot["end_exclusive"]=R.loc(E);
        llvm::json::Array Raw;
        for (const Token *T=First; !T->is(tok::eof); ++T) Raw.push_back(T->getLocation().getRawEncoding());
        Slot["token_raws"]=std::move(Raw);
      }
      ArgumentSlots.push_back(std::move(Slot));
      Arguments.push_back(std::move(A));
    }
    R.emit(llvm::json::Object{{"record","macro"},{"name",R.CI.getPreprocessor().getSpelling(Name)},
            {"invocation",R.range(Call)}, {"name_location",R.loc(Name.getLocation())},
            {"msvc_compat",bool(R.CI.getLangOpts().MSVCCompat)},
            {"expansion",R.loc(R.SM.getExpansionLoc(Name.getLocation()))},
            {"definition",R.range({MI->getDefinitionLoc(),MI->getDefinitionEndLoc()})},
            {"body",std::move(Body)}, {"arguments",std::move(Arguments)}, {"argument_slots",std::move(ArgumentSlots)}, {"paste_fragments",std::move(PasteFragments)}});
  }
};
struct Consumer: ASTConsumer {
  std::shared_ptr<Recorder> Owner;
  Recorder &R;
  Consumer(std::shared_ptr<Recorder> Rec): Owner(Rec), R(*Rec) {}
  void HandleTranslationUnit(ASTContext &C) override {
    for (auto *D: C.getTranslationUnitDecl()->decls()) {
      auto *F = dyn_cast<FunctionDecl>(D);
      if (!F || !F->doesThisDeclarationHaveABody() || !R.selected(F->getLocation())) continue;
      R.emit(llvm::json::Object{{"record","function"},{"name",F->getNameAsString()},
              {"location",R.loc(F->getLocation())},
              {"expansion",R.loc(R.SM.getExpansionLoc(F->getLocation()))},
              {"body",R.range(F->getBody()->getSourceRange())}});
    }
  }
};
struct Action: PluginASTAction {
  std::string Path, Config;
  std::shared_ptr<Recorder> R;
  bool ParseArgs(const CompilerInstance &, const std::vector<std::string> &Args) override {
    if (Args.size()!=2) return false;
    Path=Args[0];Config=Args[1];return true;
  }
  ActionType getActionType() override { return AddBeforeMainAction; }
  std::unique_ptr<ASTConsumer> CreateASTConsumer(CompilerInstance &CI, llvm::StringRef) override {
    R=std::make_shared<Recorder>(CI,Path,Config);
    CI.getPreprocessor().addPPCallbacks(std::make_unique<Callbacks>(R));
    CI.getPreprocessor().setTokenWatcher([R=R](const Token &T) {
      if (!T.isAnnotation() && R->selected(T.getLocation())) {
        auto O=R->token(T);O["record"]="token";R->emit(std::move(O));
      }
    });
    return std::make_unique<Consumer>(R);
  }
};
FrontendPluginRegistry::Add<Action> X("ruling-token-evidence", "record real macro argument locations");
}
"""

def build():
    OUT.mkdir(parents=True, exist_ok=True)
    src=OUT/"token_evidence.cpp"; src.write_text(SOURCE)
    so=OUT/"token_evidence.so"
    cmd=[str(WORK/"temp/eval-prep11/bin/host-clang"), "-x", "c++", "-std=c++17",
         "-fPIC", "-shared", "-fno-rtti", "-O0", str(src), "-o", str(so)]
    for inc in ["src/llvm/clang/include", "src/llvm/llvm/include", "temp/llvm-profgen-enh/build/tools/clang/include", "temp/llvm-profgen-enh/build/include"]:
        cmd += ["-I",str(WORK/inc)]
    cmd += ["-L",str(ROOT/"usr/lib64"),"-lclang-cpp", "-lLLVM", "-lstdc++"]
    p=subprocess.run(cmd,capture_output=True,text=True)
    for stream in ["stdout","stderr"]: (OUT/("build."+stream)).write_text(getattr(p,stream))
    meta=dict(command=cmd,exit_code=p.returncode,source_sha256=sha(src),stderr_sha256=sha(OUT/"build.stderr"))
    if p.returncode==0: meta["plugin_sha256"]=sha(so)
    (BASE/"token-plugin-build.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(p.stderr);print(json.dumps(meta))
    return p.returncode

def collect(mode):
    audit=json.loads((INPUT/f"ffmpeg-{mode}-macro-audit.json").read_text())
    targets=sorted({(r["decl_file"].split("ffmpeg-8.0.1/")[-1],int(r["decl_line"])) for r in audit})
    cfg=OUT/(mode+"-targets.json");cfg.write_text(json.dumps([dict(file=f,line=l) for f,l in targets],indent=2)+"\n")
    records=[]
    for r in json.loads((INPUT/f"{mode}-ast4-commands.json").read_text()):
        stem=mode+"-"+Path(r["tu"]).stem
        output=OUT/(stem+".jsonl")
        cmd=r["command"][:r["command"].index("-Xclang")]
        cmd += ["-Xclang","-load","-Xclang",str(OUT/"token_evidence.so")]
        for arg in [str(output),str(cfg)]:
            cmd += ["-Xclang","-plugin-arg-ruling-token-evidence","-Xclang",arg]
        p=subprocess.run(cmd,cwd=r["cwd"],capture_output=True,text=True)
        for stream in ["stdout","stderr"]: (OUT/(stem+"."+stream)).write_text(getattr(p,stream))
        rec=dict(tu=r["tu"],command=cmd,cwd=r["cwd"],exit_code=p.returncode,
                 output=str(output),stderr=str(OUT/(stem+".stderr")),
                 stderr_sha256=sha(OUT/(stem+".stderr")),targets_sha256=sha(cfg))
        if output.exists(): rec.update(output_sha256=sha(output),output_size=output.stat().st_size)
        records.append(rec)
        (BASE/f"{mode}-token-api-commands.json").write_text(json.dumps(records,indent=2)+"\n")
        print(json.dumps(rec))
        if p.returncode: print(p.stderr);return p.returncode
    return 0

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("action",choices=["build","thumb","a32"]);a=p.parse_args()
    raise SystemExit(build() if a.action=="build" else collect(a.action))
