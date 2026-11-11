"""Isolated C generator: only sealed C0 plus two debug ELFs."""
import json
import subprocess
import sys
from pathlib import Path
from run_scoped import WORK, ROOT, sha, platform
from ruling3_domain import reference
from apply_header_ruling import norm_file
from pack_static_evidence import tables
from v17_rules import domain, domain_sha

OUT = WORK / "docs/profgen/eval/prep/evidence/identity-gate/v17-recompute"
TEMP = WORK / "temp/prep-v17"
BASE = WORK / "docs/profgen/eval/prep/evidence"
SOURCE = r"""
#include "llvm/DebugInfo/DWARF/DWARFContext.h"
#include "llvm/DebugInfo/DWARF/DWARFDebugLine.h"
#include "llvm/DebugInfo/DWARF/DWARFUnit.h"
#include "llvm/Object/Binary.h"
#include "llvm/Object/ELFObjectFile.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/raw_ostream.h"
using namespace llvm;
void emit(json::Object O) { outs()<<json::Value(std::move(O))<<"\n"; }
int main(int argc,char **argv) {
 if(argc!=2)return 2;
 auto B=object::createBinary(argv[1]);
 if(!B){errs()<<toString(B.takeError());return 3;}
 auto *O=dyn_cast<object::ELFObjectFileBase>(B->getBinary());if(!O)return 4;
 json::Array Sections;
 for(auto S:O->sections()){
  auto N=S.getName();if(!N){errs()<<toString(N.takeError());return 5;}
  auto A=S.getAddress(),Z=S.getSize();if(A+Z<A)return 6;
  Sections.push_back(json::Object{{"name",N->str()},{"start",A},{"end",A+Z},
   {"executable",bool(object::ELFSectionRef(S).getFlags()&ELF::SHF_EXECINSTR)}});
 }
 emit(json::Object{{"kind","sections"},{"sections",std::move(Sections)}});
 auto C=DWARFContext::create(*O);
 for(auto &UP:C->compile_units()){
  auto *U=UP.get();auto D=U->getUnitDIE(false);
  if(!D.find(dwarf::DW_AT_stmt_list))continue;
  auto *L=C->getLineTableForUnit(U);
  if(!L){emit(json::Object{{"kind","error"},{"reason","line_table_unavailable"},{"cu",U->getOffset()}});continue;}
  unsigned SI=0;
  for(auto &S:L->Sequences){
   json::Array Rows;
   for(unsigned I=S.FirstRowIndex;I<S.LastRowIndex;++I){
    auto &R=L->Rows[I];std::string F;
    bool OK=L->getFileNameByIndex(R.File,U->getCompilationDir()?U->getCompilationDir():"",
     DILineInfoSpecifier::FileLineInfoKind::AbsoluteFilePath,F);
    Rows.push_back(json::Object{{"address",R.Address.Address},{"file",F},
      {"file_resolved",OK},{"line",R.Line},{"end_sequence",bool(R.EndSequence)}});
   }
   emit(json::Object{{"kind","sequence"},{"cu",U->getOffset()},{"id",SI++},{"rows",std::move(Rows)}});
  }
 }
 return 0;
}
"""


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+"\n")


def build():
    TEMP.mkdir(exist_ok=True)
    src=TEMP/"domain_lines.cpp";src.write_text(SOURCE)
    cmd=[str(WORK/"temp/eval-prep11/bin/host-clang"),"-x","c++","-std=c++17","-O1",str(src),"-o",str(TEMP/"domain_lines"),
         "-I",str(WORK/"src/llvm/llvm/include"),"-I",str(WORK/"temp/llvm-profgen-enh/build/include"),
         "-L",str(ROOT/"usr/lib64"),"-lLLVM","-lstdc++"]
    p=subprocess.run(cmd,capture_output=True,text=True)
    dump(OUT/"domain-tool-build.json",dict(command=cmd,exit_code=p.returncode,stderr=p.stderr,
        source=str(src),source_sha256=sha(src),binary_sha256=sha(TEMP/"domain_lines") if p.returncode==0 else None))
    print(p.stderr);return p.returncode


def seal(obj):
    # Coverage/reference-only preprocessing. No S inventory contents are read.
    refs,da,rlines,owners,lcov=reference(obj)
    dst=TEMP/(obj+"-C0.json")
    dump(dst,[dict(file=k[0],line=k[1],DA=da[k]) for k in sorted(owners)])
    shards=OUT/(obj+"-C0");shards.mkdir()
    parts=tables(shards,"lines",["file","line","DA"],([*k,da[k]] for k in sorted(owners)))
    inputs=[lcov,*sorted((BASE/(obj+"-coverage-tables")).glob("merged-functions-*.csv"))]
    dump(OUT/(obj+"-C0-provenance.json"),dict(inputs=[dict(path=str(p),sha256=sha(p)) for p in inputs],
         output=str(dst),sha256=sha(dst),parts=parts))
    return dst


def collect(obj):
    dst=OUT/(obj+"-domain");dst.mkdir()
    c0path=seal(obj)
    c0={(r["file"],r["line"]):r["DA"] for r in json.loads(c0path.read_text())}
    evidence={};meta=[]
    for stage in ("C","S"):
        # This catalog is used ONLY to resolve an ELF filename. No inventory
        # record, identity, selected-group or boundary data is read.
        catalog=BASE/(obj+"-"+stage+"-inventory-tables/index.json")
        elf=Path(json.loads(catalog.read_text())["elf"])
        raw=TEMP/(obj+"-"+stage+"-lines.jsonl")
        assert not raw.exists()
        cmd=platform("llvm-dwarfdump")[:-1]+[str(TEMP/"domain_lines"),str(elf)]
        with raw.open("w") as f:
            p=subprocess.run(cmd,stdout=f,stderr=subprocess.PIPE,text=True)
        sections=[];errors=[]
        with raw.open() as f:
            for line in f:
                r=json.loads(line)
                if r["kind"]=="sections":sections=r["sections"]
                elif r["kind"]=="error":errors.append(r["reason"])
        if p.returncode:errors.append("extractor_exit_"+str(p.returncode))
        if p.stderr:errors.append("extractor_diagnostic")
        if not sections:errors.append("missing_section_table")
        def seqs(path):
            with path.open() as f:
                for line in f:
                    r=json.loads(line)
                    if r["kind"]=="sequence":
                        for row in r["rows"]:row["file"]=norm_file(row["file"])
                        r["id"]=str(r["cu"])+":"+str(r["id"])
                        yield r
        evidence[stage]=dict(sections=sections,sequences=seqs(raw),errors=errors)
        meta.append(dict(stage=stage,command=cmd,elf=str(elf),elf_sha256=sha(elf),
            output=str(raw),output_sha256=sha(raw),exit_code=p.returncode,stderr=p.stderr,
            helper_sha256=sha(TEMP/"domain_lines")))
    c,seen,unresolved,errors=domain(c0,evidence)
    parts=tables(dst,"lines",["file","line","DA","status","witness"],
        ([*k,c0[k],"domain_unresolved" if k in unresolved else "witnessed",seen.get(k)] for k in sorted(c)))
    parts+=tables(dst,"code-free",["file","line","DA"],([*k,c0[k]] for k in sorted(set(c0)-c)))
    parts+=tables(dst,"domain-unresolved",["file","line","DA"],([*k,c0[k]] for k in sorted(unresolved)))
    data=dict(object=obj,C_lines=len(c),R_C=sum(c0[k] for k in c),C_sha256=domain_sha(c),
        C0_lines=len(c0),R_C0=sum(c0.values()),C0_path=str(c0path),C0_sha256=sha(c0path),
        errors=errors,domain_unresolved_lines=len(unresolved),domain_unresolved_DA=sum(c0[k] for k in unresolved),
        raw=meta,parts=parts,
        admitted_domain_inputs=[dict(path=str(c0path),sha256=sha(c0path))]+[
            dict(path=m["elf"],sha256=m["elf_sha256"]) for m in meta],
        no_identity_mapping_or_boundary_inputs=True)
    dump(dst/"index.json",data)
    print(json.dumps({k:v for k,v in data.items() if k not in ("parts","raw")},ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(build() if sys.argv[1]=="build" else collect(sys.argv[1]))
