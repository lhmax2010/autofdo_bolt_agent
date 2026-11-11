"""Revision1 provenance helper; original C row extraction remains unchanged."""
import json,subprocess,sys
from pathlib import Path
from ruling34_dwarf import SOURCE as ORIGINAL
from run_scoped import WORK,ROOT,platform,sha
from ruling34_inputs import OUT,TEMP,BASE,dump
TRACE=r'''
json::Object trace(DWARFDie Start,dwarf::Attribute Attr) {
 struct Step {DWARFDie D;std::vector<std::pair<uint64_t,std::string>> Path;};
 std::vector<Step> Todo{{Start,{{Start.getOffset(),"self"}}}};
 std::set<uint64_t> Seen{Start.getOffset()};
 json::Array Visited;
 while(!Todo.empty()){
  auto S=Todo.back();Todo.pop_back();auto D=S.D;Visited.push_back(D.getOffset());
  if(auto V=D.find(Attr)){
   json::Array Path;
   for(auto [O,E]:S.Path)Path.push_back(json::Object{{"die",O},{"edge",E}});
   auto Public=Start.findRecursively(Attr);
   if(!Public || Public->getAsUnsignedConstant()!=V->getAsUnsignedConstant()){
    errs()<<"attribute traversal differs from public API\n";std::exit(7);
   }
   return json::Object{{"found",true},{"path",std::move(Path)},{"visited",std::move(Visited)},
    {"source_die",D.getOffset()},{"value",dwarf::toUnsigned(V,0)}};
  }
  for(auto A:{dwarf::DW_AT_abstract_origin,dwarf::DW_AT_specification,dwarf::DW_AT_signature})
   if(auto R=D.getAttributeValueAsReferencedDie(A))
    if(Seen.insert(R.getOffset()).second){
     auto P=S.Path;P.emplace_back(R.getOffset(),dwarf::AttributeString(A).str());Todo.push_back({R,std::move(P)});
    }
 }
 return json::Object{{"found",false},{"visited",std::move(Visited)}};
}
'''
SOURCE=ORIGINAL.replace("int main(int argc",TRACE+"\nint main(int argc")
SOURCE=SOURCE.replace('auto Parent=D.getParent();auto Origin=', '''json::Array Ancestors;
   for(auto P=D.getParent();P;P=P.getParent())if(P.isSubroutineDIE())Ancestors.push_back(P.getOffset());
   auto Parent=D.getParent();auto Origin=''')
SOURCE=SOURCE.replace('{"parent",Parent?', '''{"ancestors",std::move(Ancestors)},
      {"decl_file_trace",trace(D,dwarf::DW_AT_decl_file)},
      {"decl_line_trace",trace(D,dwarf::DW_AT_decl_line)},
      {"parent",Parent?''')
def build():
    src=TEMP/"ruling4_dwarf.cpp";src.write_text(SOURCE)
    cmd=[str(WORK/"temp/eval-prep11/bin/host-clang"),"-x","c++","-std=c++17","-O1",str(src),"-o",str(TEMP/"ruling4_dwarf")]
    for inc in ("src/llvm/llvm/include","temp/llvm-profgen-enh/build/include"):cmd+=["-I",str(WORK/inc)]
    cmd+=["-L",str(ROOT/"usr/lib64"),"-lLLVM","-lstdc++"]
    p=subprocess.run(cmd,capture_output=True,text=True)
    m=dict(command=cmd,exit_code=p.returncode,source_sha256=sha(src),stderr=p.stderr)
    if not p.returncode:m["tool_sha256"]=sha(TEMP/"ruling4_dwarf")
    dump(OUT/"rev1-tool-build.json",m);print(p.stderr);return p.returncode
def collect(obj):
    elf=Path(json.loads((BASE/(obj+"-S-inventory-tables/index.json")).read_text())["elf"])
    out=TEMP/(obj+"-S-rev1.jsonl");assert not out.exists()
    cmd=platform("llvm-dwarfdump")[:-1]+[str(TEMP/"ruling4_dwarf"),str(elf)]
    with out.open("w") as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.PIPE,text=True)
    dump(OUT/(obj+"-S-rev1-command.json"),dict(command=cmd,exit_code=p.returncode,elf=str(elf),elf_sha256=sha(elf),
      output=str(out),output_sha256=sha(out),bytes=out.stat().st_size,stderr=p.stderr,tool_sha256=sha(TEMP/"ruling4_dwarf")))
    print(obj,p.returncode);return p.returncode
if __name__=="__main__":raise SystemExit(build() if sys.argv[1]=="build" else collect(sys.argv[1]))
