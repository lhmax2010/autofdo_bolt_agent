"""Q.5 #13: Coverage API main-function ranges and summary decomposition."""
import collections,json,subprocess,sys
from pathlib import Path
from run_scoped import WORK,ROOT,platform,sha
from coverage_reference import main_file_id,parse_lcov
from pack_static_evidence import tables

BASE=WORK/"docs/profgen/eval/prep/evidence"
OUT=BASE/"registration-checks/batch1"
TEMP=WORK/"temp/registration-batch1"
SOURCE=r"""
#include "llvm/ProfileData/Coverage/CoverageMapping.h"
#include "llvm/Support/VirtualFileSystem.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/raw_ostream.h"
#include <map>
using namespace llvm;
using namespace llvm::coverage;
void emit(json::Object O){outs()<<json::Value(std::move(O))<<"\n";}
int main(int argc,char **argv){
 if(argc!=3)return 2;
 auto C=CoverageMapping::load({argv[1]},StringRef(argv[2]),*vfs::getRealFileSystem());
 if(!C){errs()<<toString(C.takeError());return 3;}
 auto &CM=**C;
 std::map<const FunctionRecord*,unsigned> IDs;
 std::map<const FunctionRecord*,std::pair<unsigned,unsigned>> Counts;
 unsigned I=0;
 for(auto &F:CM.getCoveredFunctions()){
  IDs[&F]=I;
  auto CD=CM.getCoverageForFunction(F);
  json::Array Lines;
  unsigned N=0,H=0;
  for(auto &L:getLineCoverageStats(CD))if(L.isMapped()){
   ++N;if(L.getExecutionCount())++H;
   Lines.push_back(json::Array{L.getLine(),L.getExecutionCount()});
  }
  Counts[&F]={N,H};
  std::vector<bool> Expanded(F.Filenames.size(),false);
  for(auto &R:F.CountedRegions)if(R.Kind==CounterMappingRegion::ExpansionRegion)Expanded[R.ExpandedFileID]=true;
  unsigned Main=0;while(Main<Expanded.size()&&Expanded[Main])++Main;
  if(Main==Expanded.size()){errs()<<"empty main view";return 4;}
  unsigned Lo=~0U,Hi=0;
  for(auto &R:F.CountedRegions)
   if(R.Kind==CounterMappingRegion::CodeRegion && R.FileID==Main){
    Lo=std::min(Lo,R.LineStart);Hi=std::max(Hi,R.LineEnd);
   }
  emit(json::Object{{"kind","function"},{"id",I++},{"name",F.Name},
    {"file",CD.getFilename()},{"count",F.ExecutionCount},{"start",Lo},{"end",Hi},
    {"main_id",Main},{"lines",std::move(Lines)}});
 }
 for(auto File:CM.getUniqueSourceFiles()){
  unsigned N=0,H=0,FN=0,FH=0;json::Array Groups;
  for(auto &G:CM.getInstantiationGroups(File)){
   unsigned GN=0,GH=0;json::Array Members;
   for(auto *F:G.getInstantiations()){
    GN=std::max(GN,Counts[F].first);GH=std::max(GH,Counts[F].second);
    Members.push_back(IDs[F]);
   }
   N+=GN;H+=GH;++FN;if(G.getTotalExecutionCount())++FH;
   Groups.push_back(json::Object{{"line",G.getLine()},{"column",G.getColumn()},
     {"members",std::move(Members)},{"LF",GN},{"LH",GH}});
  }
  emit(json::Object{{"kind","file"},{"file",File},{"LF",N},{"LH",H},
    {"FNF",FN},{"FNH",FH},{"groups",std::move(Groups)}});
 }
 return 0;
}
"""


def dump(p,x):
 p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+"\n")


def build():
 src=TEMP/"coverage_ranges_v2.cpp";src.write_text(SOURCE)
 cmd=[str(WORK/"temp/eval-prep11/bin/host-clang"),"-x","c++","-std=c++17","-O1",str(src),
      "-I",str(WORK/"src/llvm/llvm/include"),"-I",str(WORK/"temp/llvm-profgen-enh/build/include"),
      "-L",str(ROOT/"usr/lib64"),"-lLLVM","-lstdc++","-o",str(TEMP/"coverage_ranges_v2")]
 p=subprocess.run(cmd,capture_output=True,text=True)
 dump(OUT/"coverage-range-build-v2.json",dict(command=cmd,exit_code=p.returncode,stderr=p.stderr,
      source=str(src),source_sha256=sha(src)))
 print(p.stderr)
 return p.returncode


def main(obj):
 index=json.loads((BASE/(obj+"-coverage-tables/index.json")).read_text())
 exp=BASE/(obj+"-lcov/command.json")
 if not exp.exists():exp=BASE/(obj+"-lcov-admitted/command.json")
 old=json.loads(exp.read_text())["command"]
 elf=WORK/old[old.index("export")+1]
 prof=WORK/next(x.split("=",1)[1] for x in old if x.startswith("-instr-profile="))
 output=TEMP/(obj+"-coverage-api-v2.jsonl")
 cmd=platform("llvm-cov")[:-1]+[str(TEMP/"coverage_ranges_v2"),str(elf),str(prof)]
 with output.open("w") as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.PIPE,text=True)
 command=dict(command=cmd,exit_code=p.returncode,stderr=p.stderr,elf=str(elf),elf_sha256=sha(elf),
    C_profdata=str(prof),C_profdata_sha256=sha(prof),output=str(output),sha256=sha(output),
    helper_sha256=sha(TEMP/"coverage_ranges_v2"))
 dump(OUT/(obj+"-coverage-api-command-v2.json"),command)
 assert p.returncode==0,p.stderr
 jp=WORK/index["json"]
 data=json.loads(jp.read_text())["data"][0]
 lp=WORK/index["lcov"]
 if not lp.exists():lp=WORK/"temp/prep-identity-gate"/(obj+"-reference.lcov")
 lcov=parse_lcov(lp)
 functions=data["functions"];files={f["filename"]:f for f in data["files"]}
 ranges=[];summaries=[];details=[];differences=[]
 for text in output.open():
  r=json.loads(text)
  if r["kind"]=="function":
   f=functions[r["id"]]
   main=main_file_id(f)
   code=[v for v in f["regions"] if v[7]==0 and v[5]==main]
   assert code,"empty main view must be separately reported"
   start,end=min(v[0] for v in code),max(v[2] for v in code)
   expected=dict(main_id=main,name=f["name"],file=f["filenames"][main],count=f["count"],start=start,end=end)
   for k,v in expected.items():
    if r[k]!=v:differences.append(dict(kind="function_range",id=r["id"],field=k,api=r[k],expected=v))
   assert [start,f["name"]] in lcov[expected["file"]]["fn"]
   assert [f["count"],f["name"]] in lcov[expected["file"]]["fnda"]
   outside=[x for x in r["lines"] if not start<=x[0]<=end]
   if outside:differences.append(dict(kind="API_lines_outside_main_range",id=r["id"],lines=outside))
   ranges.append(dict(id=r["id"],**expected,API_mapped_lines=len(r["lines"]),
                     API_covered_lines=sum(v>0 for n,v in r["lines"]),lcov_FN_agrees=True))
  else:
   f=files[r["file"]];sf=lcov[r["file"]]
   js=f["summary"]
   expect=dict(LF=js["lines"]["count"],LH=js["lines"]["covered"],
               FNF=js["functions"]["count"],FNH=js["functions"]["covered"])
   for k,v in expect.items():
    if r[k]!=v or sf["summary"][k]!=v:
     differences.append(dict(kind="file_summary",file=r["file"],field=k,api=r[k],json=v,lcov=sf["summary"][k]))
   # Explain summary vs DA by API's per-instantiation-group maxima, not a
   # guessed interval filter. Per-function member line sets remain in raw.
   summaries.append(dict(file=r["file"],**expect,DA_lines=len(sf["da"]),
        DA_covered=sum(v>0 for v in sf["da"].values()),
        DA_minus_LF=len(sf["da"])-r["LF"],covered_minus_LH=sum(v>0 for v in sf["da"].values())-r["LH"],
        groups=len(r["groups"])))
   details.append(r)
 dest=OUT/(obj+"-coverage-ranges-v2");dest.mkdir()
 parts=tables(dest,"functions",list(ranges[0]),([v[k] for k in ranges[0]] for v in ranges))
 parts+=tables(dest,"files",list(summaries[0]),([v[k] for k in summaries[0]] for v in summaries))
 parts+=tables(dest,"groups",["record"],([v] for v in details))
 result=dict(object=obj,function_records=len(ranges),files=len(summaries),
   differences=differences,empty_main=0,
   DA_lines=sum(v["DA_lines"] for v in summaries),summary_LF=sum(v["LF"] for v in summaries),
   DA_covered=sum(v["DA_covered"] for v in summaries),summary_LH=sum(v["LH"] for v in summaries),
   range_checks="all main-code ranges equal API; lcov FN starts and FNDA match; API lines contained",
   summary_checks="per-file instantiation-group max(line_count,covered_count) sums match lcov AND JSON",
   raw=str(output),raw_sha256=sha(output),json=str(jp),json_sha256=sha(jp),
   lcov=str(lp),lcov_sha256=sha(lp),parts=parts)
 dump(dest/"index.json",result)
 assert not differences,differences[:3]
 print(json.dumps({k:v for k,v in result.items() if k!="parts"},ensure_ascii=False))
 return 0

if __name__=="__main__":raise SystemExit(build() if sys.argv[1]=="build" else main(sys.argv[1]))
