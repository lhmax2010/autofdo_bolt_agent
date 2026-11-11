"""Extend the previous independent plugin; preserve its Stmt/Expr traversal."""
import json,subprocess,sys,collections
from pathlib import Path
from code_free_ast import SOURCE as BASE
from code_free_v2_lex import OUT,TEMP
from ruling3_union import OUT as OLD,dump
from run_scoped import WORK,ROOT,sha
SOURCE=BASE.replace('#include "clang/AST/Stmt.h"','#include "clang/AST/Stmt.h"\n#include "clang/AST/Expr.h"\n#include "clang/Lex/Lexer.h"')
SOURCE=SOURCE.replace('std::set<std::string> SeenFiles,SeenRanges;','std::set<std::string> SeenFiles,SeenRanges,SeenDecls;')
SOURCE=SOURCE.replace('emit(llvm::json::Object{{"record","range"}','llvm::json::Object O{{"record","range"}')
SOURCE=SOURCE.replace('{"end_macro",RawE.isMacroID()}});','''{"end_macro",RawE.isMacroID()}};
  std::string Semantic=S->getStmtClassName();
  if(auto *Op=dyn_cast<BinaryOperator>(S)){
   O["opcode"]=Op->getOpcodeStr().str();
   if(Op->isAssignmentOp())Semantic="assignment";
  }
  if(isa<CallExpr>(S))Semantic="function_call";
  if(isa<ReturnStmt>(S))Semantic="return";
  if(auto *DS=dyn_cast<DeclStmt>(S)){
   bool Init=false;for(auto *D:DS->decls())if(auto *V=dyn_cast<VarDecl>(D))Init|=V->hasInit();
   Semantic=Init?"declaration_with_initializer":"declaration_without_initializer";
  }
  O["semantic_kind"]=Semantic;emit(std::move(O));''')
INSERT=r'''
 void decl(Decl *D,bool Spelling){
  auto RawB=D->getBeginLoc(),RawE=D->getEndLoc();if(RawB.isInvalid()||RawE.isInvalid())return;
  auto B=Spelling?SM.getSpellingLoc(RawB):SM.getExpansionLoc(RawB);
  auto E=Spelling?SM.getSpellingLoc(RawE):SM.getExpansionLoc(RawE);
  auto F=file(B);if(!Targets.count(F)||SM.getFileID(B)!=SM.getFileID(E))return;
  unsigned L=SM.getSpellingLineNumber(B),H=SM.getSpellingLineNumber(E);
  if(H<L)return;auto I=Targets[F].lower_bound(L);if(I==Targets[F].end()||*I>H)return;
  std::string Kind=std::string(D->getDeclKindName())+"Decl";
  std::string Key=F+":"+std::to_string(B.getRawEncoding())+":"+std::to_string(E.getRawEncoding())+":"+Kind;
  if(!SeenDecls.insert(Key).second)return;
  llvm::json::Object O{{"record","decl_range"},{"file",F},{"kind",Kind},{"begin_line",L},{"end_line",H},
   {"begin_offset",SM.getFileOffset(B)},{"end_offset",SM.getFileOffset(E)},
   {"begin_raw",RawB.getRawEncoding()},{"end_raw",RawE.getRawEncoding()},
   {"view",Spelling?"spelling":"expansion"},{"begin_macro",RawB.isMacroID()},{"end_macro",RawE.isMacroID()}};
  std::string Semantic=Kind;
  if(auto *V=dyn_cast<VarDecl>(D)){O["has_initializer"]=V->hasInit();Semantic=V->hasInit()?"declaration_with_initializer":"declaration_without_initializer";}
  O["semantic_kind"]=Semantic;emit(std::move(O));
 }
 void label(Stmt *S){
  SourceLocation B,C;
  if(auto *SC=dyn_cast<SwitchCase>(S)){B=SC->getBeginLoc();C=SC->getColonLoc();}
  else if(auto *LS=dyn_cast<LabelStmt>(S)){
   B=LS->getIdentLoc();auto Next=Lexer::findNextToken(B,SM,CI.getLangOpts());
   if(Next&&Next->is(tok::colon))C=Next->getLocation();
  }else return;
  if(B.isInvalid()||C.isInvalid())return;
  for(bool Spelling:{true,false}){
   auto X=Spelling?SM.getSpellingLoc(B):SM.getExpansionLoc(B);
   auto Y=Spelling?SM.getSpellingLoc(C):SM.getExpansionLoc(C);
   if(SM.getFileID(X)!=SM.getFileID(Y))continue;
   auto F=file(X);if(!Targets.count(F))continue;
   unsigned L=SM.getSpellingLineNumber(X),H=SM.getSpellingLineNumber(Y);
   auto I=Targets[F].lower_bound(L);if(I==Targets[F].end()||*I>H)continue;
   emit(llvm::json::Object{{"record","label"},{"file",F},{"kind",S->getStmtClassName()},
    {"begin_line",L},{"end_line",H},{"begin_offset",SM.getFileOffset(X)},{"end_offset",SM.getFileOffset(Y)+1},
    {"begin_raw",B.getRawEncoding()},{"colon_raw",C.getRawEncoding()},{"view",Spelling?"spelling":"expansion"}});
  }
 }
'''
SOURCE=SOURCE.replace('\n};\nstruct Callbacks:',INSERT+'\n};\nstruct Callbacks:',1)
SOURCE=SOURCE.replace('std::function<void(Stmt*)> Walk=',r'''std::set<const Decl*> Seen;
  std::function<void(Decl*)> WalkDecl=[&](Decl*D){
   if(!D||!Seen.insert(D).second)return;
   R->decl(D,true);R->decl(D,false);
   if(auto *DC=dyn_cast<DeclContext>(D))for(auto *Ch:DC->decls())WalkDecl(Ch);
  };
  for(auto *D:C.getTranslationUnitDecl()->decls())WalkDecl(D);
  std::function<void(Stmt*)> Walk=''')
SOURCE=SOURCE.replace('if(!S)return;R->range(S,true);R->range(S,false);for(auto *Ch:S->children())Walk(Ch);',
 'if(!S)return;R->range(S,true);R->range(S,false);R->label(S);if(auto *DS=dyn_cast<DeclStmt>(S))for(auto *D:DS->decls())WalkDecl(D);for(auto *Ch:S->children())Walk(Ch);')
def build():
    src=TEMP/"extended_ranges.cpp";src.write_text(SOURCE);so=TEMP/"extended_ranges.so"
    old=json.loads((OLD/"AST-plugin-build.json").read_text())
    cmd=[str(src) if x.endswith("/stmt_ranges.cpp") else str(so) if x.endswith("/stmt_ranges.so") else x for x in old["command"]]
    p=subprocess.run(cmd,capture_output=True,text=True)
    dump(OUT/"AST-build.json",dict(command=cmd,source_sha256=sha(src),exit_code=p.returncode,stderr=p.stderr,
      plugin_sha256=sha(so) if p.returncode==0 else None))
    print(p.stderr);return p.returncode
def collect(obj):
    idx=json.loads((OLD/(obj+"-AST/index.json")).read_text())
    dest=TEMP/(obj+"-AST");dest.mkdir()
    ev=OUT/(obj+"-AST");ev.mkdir()
    result=[]
    for i,item in enumerate(idx["commands"]):
        oldp=OLD/(obj+"-AST")/item["command"];m=json.loads(oldp.read_text())
        assert sha(Path(m["cwd"])/m["tu"])==m["source_sha256"]
        assert sha(Path(m["output"]))==m["output_sha256"]
        out=dest/(f"{i:04d}.jsonl");err=dest/(f"{i:04d}.stderr")
        substitutions={str(WORK/"temp/prep-ruling3-rev1/stmt_ranges.so"):str(TEMP/"extended_ranges.so"),m["output"]:str(out)}
        cmd=[substitutions.get(x,x) for x in m["command"]]
        assert len([1 for a,b in zip(cmd,m["command"]) if a!=b])==2
        with err.open("w") as f:p=subprocess.run(cmd,cwd=m["cwd"],stdout=subprocess.PIPE,stderr=f)
        oldrecords=[json.loads(l) for l in Path(m["output"]).read_text().splitlines()]
        records=[json.loads(l) for l in out.read_text().splitlines()] if out.exists() else []
        a=[r for r in oldrecords if r["record"]=="range"]
        b=[{k:v for k,v in r.items() if k not in ("opcode","semantic_kind")} for r in records if r["record"]=="range"]
        ca=collections.Counter(json.dumps(r,sort_keys=True) for r in a);cb=collections.Counter(json.dumps(r,sort_keys=True) for r in b)
        diff=dict(old_only=list((ca-cb).elements()),new_only=list((cb-ca).elements()))
        rec=dict(tu=m["tu"],previous=str(oldp),previous_sha256=sha(oldp),command=cmd,previous_command=m["command"],
           substitutions=substitutions,compile_parameters_identical=True,cwd=m["cwd"],source_sha256=m["source_sha256"],
           exit_code=p.returncode,previous_exit_code=m["exit_code"],output=str(out),output_sha256=sha(out) if out.exists() else None,
           stderr=str(err),stderr_sha256=sha(err),stmt_count=len(a),new_stmt_count=len(b),differences=diff,
           complete=records[-1] if records else None,decl_count=sum(r["record"]=="decl_range" for r in records),
           labels=sum(r["record"]=="label" for r in records),logical_root=m["logical_root"])
        dump(ev/item["command"],rec)
        assert p.returncode==m["exit_code"]==0 and records[-1]=={"record":"complete","errors":False},rec
        assert not diff["old_only"] and not diff["new_only"],diff
        result.append(dict(command=item["command"],tu=m["tu"],stmt_count=len(a),decl_count=rec["decl_count"],equal=True))
        if i%50==0:print(obj,i,"same",len(a),flush=True)
    dump(ev/"index.json",dict(commands=result,logical_root=idx["logical_root"],all_equal=True))
    return 0
if __name__=="__main__":raise SystemExit(build() if sys.argv[1]=="build" else collect(sys.argv[1]))
