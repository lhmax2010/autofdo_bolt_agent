"""Clang raw Lexer evidence only; no AST or profile generation."""
import collections,json,subprocess,sys
from pathlib import Path
from run_scoped import WORK,ROOT,sha,platform
from ruling3_union import OUT as OLD,dump
from apply_header_ruling import rows
OUT=WORK/"docs/profgen/eval/prep/evidence/identity-gate/code-free-v2"
TEMP=WORK/"temp/prep-code-free-v2"
SOURCE=r'''
#include "clang/Basic/Diagnostic.h"
#include "clang/Basic/DiagnosticOptions.h"
#include "clang/Basic/FileManager.h"
#include "clang/Basic/IdentifierTable.h"
#include "clang/Basic/SourceManager.h"
#include "clang/Lex/Lexer.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/MemoryBuffer.h"
#include "llvm/Support/raw_ostream.h"
#include <map>
using namespace clang;
int main(int argc,char **argv) {
 if(argc!=3)return 2;
 auto B=llvm::MemoryBuffer::getFile(argv[1]);if(!B)return 3;
 auto J=llvm::json::parse((*B)->getBuffer());if(!J)return 4;
 std::error_code EC;llvm::raw_fd_ostream Out(argv[2],EC);if(EC)return 5;
 DiagnosticOptions Opts;
 DiagnosticsEngine Diags(new DiagnosticIDs,Opts,new IgnoringDiagConsumer);
 FileManager FM{FileSystemOptions()};SourceManager SM(Diags,FM);
 LangOptions LO;LO.C99=true;LO.C11=true;LO.C17=true;LO.GNUMode=true;LO.LineComment=true;
 IdentifierTable Idents(LO);
 for(auto &Entry:*J->getAsArray()){
  auto *O=Entry.getAsObject();std::string Path=O->getString("path")->str();
  auto Buf=llvm::MemoryBuffer::getFile(Path);if(!Buf)return 6;
  FileID F=SM.createFileID(std::move(*Buf));
  std::map<unsigned,llvm::json::Array> Lines;
  for(auto &N:*O->getArray("lines"))Lines[*N.getAsInteger()]={};
  Lexer L(F,SM.getBufferOrFake(F),SM,LO);L.SetCommentRetentionState(false);
  Token T;
  do {
   L.LexFromRawLexer(T);if(T.is(tok::eof))break;
   unsigned A=SM.getFileOffset(T.getLocation()),E=A+T.getLength();
   unsigned First=SM.getLineNumber(F,A),Last=SM.getLineNumber(F,E?E-1:E);
   std::string Text=Lexer::getSpelling(T,SM,LO);
   auto Kind=T.getKind();
   if(Kind==tok::raw_identifier)Kind=Idents.get(T.getRawIdentifier()).getTokenID();
   for(auto I=Lines.lower_bound(First);I!=Lines.end()&&I->first<=Last;++I)
    I->second.push_back(llvm::json::Object{{"kind",tok::getTokenName(Kind)},{"raw_kind",tok::getTokenName(T.getKind())},
       {"text",Text},{"offset",A},{"end_offset",E},{"begin_line",First},{"end_line",Last}});
  }while(!T.is(tok::eof));
  for(auto &KV:Lines)Out<<llvm::json::Value(llvm::json::Object{{"file",O->getString("file")->str()},
     {"line",KV.first},{"tokens",std::move(KV.second)}})<<"\n";
 }
 Out.flush();return Out.has_error()?7:0;
}
'''
def build():
    p=TEMP/"raw_lex.cpp";p.write_text(SOURCE);binary=TEMP/"raw_lex"
    cmd=[str(WORK/"temp/eval-prep11/bin/host-clang"),"-std=c++17","-fno-rtti","-O0",str(p),"-o",str(binary)]
    for inc in ("src/llvm/clang/include","src/llvm/llvm/include","temp/llvm-profgen-enh/build/tools/clang/include","temp/llvm-profgen-enh/build/include"):cmd+=["-I",str(WORK/inc)]
    cmd+=["-L",str(ROOT/"usr/lib64"),"-lclang-cpp","-lLLVM","-lstdc++"]
    r=subprocess.run(cmd,capture_output=True,text=True)
    dump(OUT/"lexer-build.json",dict(command=cmd,exit_code=r.returncode,stderr=r.stderr,source_sha256=sha(p),binary_sha256=sha(binary) if r.returncode==0 else None))
    print(r.stderr);return r.returncode
def collect():
    wanted=collections.defaultdict(set)
    for obj in ("spike-thumb","spike-a32","ffmpeg-thumb","ffmpeg-a32"):
        for r in rows(OLD/(obj+"-domain"),"code-free-*.csv"):wanted[r["file"]].add(int(r["line"]))
    cfg=[]
    for f,ls in sorted(wanted.items()):
        family,rel=f.split("/BUILD/")[1].split("/",1)
        src=WORK/"temp/eval-prep11"/("spike" if family=="eval-spike-1.0" else "ffmpeg")/rel
        cfg.append(dict(file=f,path=str(src),source_sha256=sha(src),lines=sorted(ls)))
    config=TEMP/"lexer-inputs.json";dump(config,cfg);output=TEMP/"raw-tokens.jsonl"
    cmd=platform("clang")[:-1]+[str(TEMP/"raw_lex"),str(config),str(output)]
    r=subprocess.run(cmd,capture_output=True,text=True)
    dump(OUT/"lexer-command.json",dict(command=cmd,exit_code=r.returncode,stderr=r.stderr,
        input=str(config),input_sha256=sha(config),output=str(output),output_sha256=sha(output) if output.exists() else None,
        source_inputs=cfg,binary_sha256=sha(TEMP/"raw_lex"),
        lexical_options="C17/GNU C raw lex; comments skipped, entire physical file lexed to retain multiline token/comment state"))
    print("lexer",r.returncode,"files",len(cfg));return r.returncode
if __name__=="__main__":raise SystemExit(build() if sys.argv[1]=="build" else collect())
