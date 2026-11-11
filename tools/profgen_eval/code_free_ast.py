"""Read-only Clang plugin extracts Stmt/Expr ranges under original C flags."""
import json,subprocess,sys,collections
from pathlib import Path
from run_scoped import WORK,ROOT,sha
from ruling3_union import OUT,TEMP,dump
from recheck_header_evidence import command_record
from apply_header_ruling import rows
SOURCE=r'''
#include "clang/AST/ASTConsumer.h"
#include "clang/AST/Decl.h"
#include "clang/AST/Stmt.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Frontend/FrontendPluginRegistry.h"
#include "clang/Lex/PPCallbacks.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/MemoryBuffer.h"
#include <map>
#include <set>
#include <functional>
using namespace clang;
namespace {
struct Rec {
 CompilerInstance &CI;SourceManager &SM;
 std::unique_ptr<llvm::raw_fd_ostream> Out;
 std::map<std::string,std::set<unsigned>> Targets;
 std::set<std::string> SeenFiles,SeenRanges;
 Rec(CompilerInstance &C,std::string Path,std::string Config):CI(C),SM(C.getSourceManager()){
  std::error_code EC;Out=std::make_unique<llvm::raw_fd_ostream>(Path,EC);if(EC)llvm::report_fatal_error("output");
  auto B=llvm::MemoryBuffer::getFile(Config);if(!B)llvm::report_fatal_error("targets");
  auto J=llvm::json::parse((*B)->getBuffer());if(!J)llvm::report_fatal_error("targets json");
  for(auto &X:*J->getAsArray()){auto *O=X.getAsObject();Targets[O->getString("file")->str()].insert(*O->getInteger("line"));}
 }
 std::string file(SourceLocation L){auto F=SM.getFilename(L).str();while(F.rfind("./",0)==0)F.erase(0,2);return F;}
 void emit(llvm::json::Object O){*Out<<llvm::json::Value(std::move(O))<<"\n";}
 void available(SourceLocation L){
  if(L.isInvalid())return;auto F=file(SM.getFileLoc(L));
  if(Targets.count(F)&&SeenFiles.insert(F).second)emit(llvm::json::Object{{"record","available_file"},{"file",F}});
 }
 void range(Stmt *S,bool Spelling){
  auto RawB=S->getBeginLoc(),RawE=S->getEndLoc();
  if(RawB.isInvalid()||RawE.isInvalid())return;
  auto B=Spelling?SM.getSpellingLoc(RawB):SM.getExpansionLoc(RawB);
  auto E=Spelling?SM.getSpellingLoc(RawE):SM.getExpansionLoc(RawE);
  available(B);available(E);
  auto F=file(B);if(!Targets.count(F)||SM.getFileID(B)!=SM.getFileID(E))return;
  unsigned L=SM.getSpellingLineNumber(B),H=SM.getSpellingLineNumber(E);
  if(H<L)return;auto I=Targets[F].lower_bound(L);if(I==Targets[F].end()||*I>H)return;
  std::string Key=F+":"+std::to_string(B.getRawEncoding())+":"+std::to_string(E.getRawEncoding())+":"+S->getStmtClassName();
  if(!SeenRanges.insert(Key).second)return;
  emit(llvm::json::Object{{"record","range"},{"file",F},{"kind",S->getStmtClassName()},{"begin_line",L},{"end_line",H},
    {"begin_offset",SM.getFileOffset(B)},{"end_offset",SM.getFileOffset(E)},
    {"begin_raw",RawB.getRawEncoding()},{"end_raw",RawE.getRawEncoding()},
    {"view",Spelling?"spelling":"expansion"},{"begin_macro",RawB.isMacroID()},{"end_macro",RawE.isMacroID()}});
 }
};
struct Callbacks:PPCallbacks{
 std::shared_ptr<Rec> R;Callbacks(std::shared_ptr<Rec> X):R(X){}
 void FileChanged(SourceLocation L,FileChangeReason,SrcMgr::CharacteristicKind,FileID)override{R->available(L);}
};
struct Consumer:ASTConsumer{
 std::shared_ptr<Rec> R;Consumer(std::shared_ptr<Rec>X):R(X){}
 void HandleTranslationUnit(ASTContext &C)override{
  std::function<void(Stmt*)> Walk=[&](Stmt*S){if(!S)return;R->range(S,true);R->range(S,false);for(auto *Ch:S->children())Walk(Ch);};
  for(auto *D:C.getTranslationUnitDecl()->decls())if(auto *F=dyn_cast<FunctionDecl>(D))
   if(F->doesThisDeclarationHaveABody())Walk(F->getBody());
  R->emit(llvm::json::Object{{"record","complete"},{"errors",C.getDiagnostics().hasErrorOccurred()}});
  R->Out->flush();
 }
};
struct Action:PluginASTAction{
 std::string Path,Config;
 bool ParseArgs(const CompilerInstance &,const std::vector<std::string>&A)override{if(A.size()!=2)return false;Path=A[0];Config=A[1];return true;}
 ActionType getActionType()override{return AddBeforeMainAction;}
 std::unique_ptr<ASTConsumer>CreateASTConsumer(CompilerInstance&CI,llvm::StringRef)override{
  auto R=std::make_shared<Rec>(CI,Path,Config);CI.getPreprocessor().addPPCallbacks(std::make_unique<Callbacks>(R));
  return std::make_unique<Consumer>(R);
 }
};
FrontendPluginRegistry::Add<Action>X("code-free-ranges","record compiler Stmt source ranges");
}
'''
def build():
    src=TEMP/"stmt_ranges.cpp";src.write_text(SOURCE);so=TEMP/"stmt_ranges.so"
    cmd=[str(WORK/"temp/eval-prep11/bin/host-clang"),"-x","c++","-std=c++17","-fPIC","-shared","-fno-rtti","-O0",str(src),"-o",str(so)]
    for inc in ("src/llvm/clang/include","src/llvm/llvm/include","temp/llvm-profgen-enh/build/tools/clang/include","temp/llvm-profgen-enh/build/include"):cmd+=["-I",str(WORK/inc)]
    cmd+=["-L",str(ROOT/"usr/lib64"),"-lclang-cpp","-lLLVM","-lstdc++"]
    p=subprocess.run(cmd,capture_output=True,text=True)
    dump(OUT/"AST-plugin-build.json",dict(command=cmd,exit_code=p.returncode,stderr=p.stderr,source_sha256=sha(src),plugin_sha256=sha(so) if p.returncode==0 else None))
    print(p.stderr);return p.returncode
def collect(obj):
    assert (TEMP/"stmt_ranges.so").exists(),"AST plugin build required"
    family,mode=obj.split("-")
    cr=command_record(WORK/"docs/profgen/eval/prep/evidence/ruling1"/(obj+"-C-commands.json"))
    assert sha(Path(cr["log"]))==cr["log_sha256"]
    previous=json.loads((WORK/"docs/profgen/eval/prep/evidence/ruling2"/(mode+"-ast4-commands.json")).read_text())[0]
    driver=previous["command"][:8]
    src=WORK/"temp/eval-prep11"/("ffmpeg" if family=="ffmpeg" else "spike")
    logical="/home/abuild/rpmbuild/BUILD/"+("ffmpeg-8.0.1" if family=="ffmpeg" else "eval-spike-1.0")+"/"
    lines=list(rows(OUT/(obj+"-domain"),"code-free-*.csv"))
    targets=[]
    for r in lines:
        assert r["file"].startswith(logical),r
        targets.append(dict(file=r["file"][len(logical):],line=int(r["line"])))
    cfg=TEMP/(obj+"-AST-targets.json");dump(cfg,targets)
    dest=TEMP/(obj+"-AST");dest.mkdir()
    evidence=OUT/(obj+"-AST");evidence.mkdir()
    results=[]
    commands=[c for c in cr["compile_commands"] if len(c["sources"])==1 and
        (family=="spike" or c["sources"][0].startswith("libavcodec/"))]
    for n,c in enumerate(commands):
        tu=c["sources"][0];args=[]
        if family=="ffmpeg":args+=["-I"+str(WORK/"temp/eval-prep11/build"/(obj+"-C"))]
        it=iter(c["args"][1:])
        for a in it:
            if a in ("-o","-MF","-MT"):next(it);continue
            if a in ("-MMD","-c") or a.startswith("-Wl,"):continue
            args.append(a)
        if family=="ffmpeg":
            args+=["-I"+str(WORK/"temp/eval-prep11/configure"/mode),
                   "-I"+str(WORK/"temp/prep-ruling2"/("headers4-"+mode)/"usr/include")]
        output=dest/(f"{n:04d}.jsonl");stderr=dest/(f"{n:04d}.stderr")
        args+=["-fsyntax-only","-Xclang","-load","-Xclang",str(TEMP/"stmt_ranges.so")]
        for a in (str(output),str(cfg)):args+=["-Xclang","-plugin-arg-code-free-ranges","-Xclang",a]
        cmd=driver+args
        with stderr.open("w") as err:p=subprocess.run(cmd,cwd=src,stdout=subprocess.PIPE,stderr=err,text=True)
        rec=dict(tu=tu,original_log=cr["log"],original_log_sha256=cr["log_sha256"],original_line=c["line"],
                 original_command=c["args"],command=cmd,cwd=str(src),source_sha256=sha(src/tu),exit_code=p.returncode,
                 output=str(output),output_sha256=sha(output) if output.exists() else None,
                 stderr=str(stderr),stderr_sha256=sha(stderr),targets_sha256=sha(cfg),logical_root=logical,
                 plugin_sha256=sha(TEMP/"stmt_ranges.so"))
        dump(evidence/(f"command-{n:04d}.json"),rec);results.append(dict(tu=tu,exit_code=p.returncode,command=f"command-{n:04d}.json"))
        if n%25==0 or p.returncode:print(obj,n,tu,p.returncode,flush=True)
    dump(evidence/"index.json",dict(object=obj,commands=results,targets=str(cfg),targets_sha256=sha(cfg),logical_root=logical,
        config_sha256=sha(WORK/"temp/eval-prep11/build"/(obj+"-C")/"config.h") if family=="ffmpeg" else None))
    print(obj,"complete",len(results),"failures",sum(r["exit_code"]!=0 for r in results),flush=True)
    return 0
if __name__=="__main__":raise SystemExit(build() if sys.argv[1]=="build" else collect(sys.argv[1]))
