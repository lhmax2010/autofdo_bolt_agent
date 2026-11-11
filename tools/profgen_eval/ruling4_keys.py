"""Static key presence: verbatim formal-tool context construction, no profiles."""
import json,subprocess,sys,hashlib
from pathlib import Path
from static_map_bridge import SOURCE as ORIGINAL,paths,PROFGEN
from ruling34_inputs import OUT,TEMP,dump
from run_scoped import WORK,ROOT,platform,sha
from static_gate_data import bridge_inventory
def build():
    source=(PROFGEN/"ProfiledBinary.cpp").read_text()
    begin=source.index("  SampleContextFrameVector CallStack;",source.index("ProfiledBinary::symbolize("))
    end=source.index("\n}",begin)
    body=source[begin:end]
    assert body.endswith("  return CallStack;")
    src=ORIGINAL.replace('#include "IPBoundary.h"','#include "IPBoundary.h"\n#include "llvm/ProfileData/SampleProf.h"\n#include "llvm/IR/PseudoProbe.h"')
    wrap="""
using namespace llvm::sampleprof;
SampleContextFrameVector officialKey(const DIInliningInfo &InlineStack,uint64_t Address){
 const bool IPMode=true,UseCanonicalFnName=false,UseProbeDiscriminator=false;
 struct {uint64_t Address;} IP{Address};
 std::set<uint64_t> IPNonLeafZeroLineAddresses;
 static std::set<std::string> NameStrings;
""" + body + "\n}\n"
    src=src.replace("int main(int argc",wrap+"\nint main(int argc")
    src=src.replace('  for(auto &Name:Wanted) {','''  std::map<uint64_t,uint64_t> Touched,Accepted;
  for(auto &Name:Wanted) {''')
    src=src.replace('      json::Array Chain;','''      auto K=officialKey(*R,Address);
      json::Array Chain;std::vector<uint64_t> Dies;''')
    src=src.replace('if(D.isSubroutineDIE())Chain.push_back(D.getOffset());','if(D.isSubroutineDIE()){Chain.push_back(D.getOffset());Dies.push_back(D.getOffset());}')
    a=src.index('      emit(json::Object{{"kind","instruction"}')
    b=src.index('\n    }',a)
    src=src[:a]+'''      for(auto D:Dies)Touched[D]++;
      // A truncated invalid inner name leaves only the accepted outer frames.
      if(!K.empty()){
        if(K.size()>Dies.size()){errs()<<"key/DIE depth mismatch";return 10;}
        for(size_t I=Dies.size()-K.size();I<Dies.size();++I)Accepted[Dies[I]]++;
      }
      emit(json::Object{{"kind","key_presence"},{"group",Name},{"address",Address},
        {"dies_leaf_to_root",std::move(Chain)},{"key_frames",int64_t(K.size())}});
''' +src[b:]
    src=src.replace('  return 0;\n}\n','''  for(auto &[D,I]:Infos)emit(json::Object{{"kind","die_keys"},{"die",D},{"top_die",I.Top},
     {"touched_instructions",Touched[D]},{"accepted_key_instructions",Accepted[D]}});
  return 0;
}
''')
    cpp=TEMP/"official_key_presence.cpp";cpp.write_text(src)
    cc=WORK/"temp/eval-prep11/bin/host-clang"
    boundary=WORK/"temp/prep-static-gate/IPBoundary.cpp"
    assert sha(boundary)==sha(PROFGEN/"IPBoundary.cpp")
    cmd=[str(cc),"-x","c++","-std=c++17","-O1",str(cpp),str(boundary),"-o",str(TEMP/"official_key_presence")]
    for inc in ("src/llvm/llvm/include","temp/llvm-profgen-enh/build/include","temp/prep-static-gate"):cmd+=["-I",str(WORK/inc)]
    cmd+=["-L",str(ROOT/"usr/lib64"),"-lLLVM","-lstdc++"]
    p=subprocess.run(cmd,capture_output=True,text=True)
    dump(OUT/"rev2-key-tool-build.json",dict(command=cmd,exit_code=p.returncode,stderr=p.stderr,
       source_sha256=sha(cpp),formal_source=str(PROFGEN/"ProfiledBinary.cpp"),formal_source_sha256=sha(PROFGEN/"ProfiledBinary.cpp"),
       copied_lines=[source[:begin].count("\n")+1,source[:end].count("\n")],
       copied_block_sha256=hashlib.sha256(body.encode()).hexdigest(),verbatim=True,
       tool_sha256=sha(TEMP/"official_key_presence") if not p.returncode else None))
    (OUT/"formal-key-block.txt").write_text(body+"\n")
    print(p.stderr);return p.returncode
def collect(obj):
    runtime,debug=paths(obj);inventory=bridge_inventory(obj)
    names=sorted({r["name"] for d,r in inventory.items() if r["tag"]=="subprogram"})
    selection=TEMP/(obj+"-all-top-groups.json");dump(selection,names)
    out=TEMP/(obj+"-official-key-presence.jsonl");assert not out.exists()
    cmd=platform("llvm-dwarfdump")[:-1]+[str(TEMP/"official_key_presence"),"map",str(runtime),str(debug),str(selection)]
    with out.open("w") as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.PIPE,text=True)
    dump(OUT/(obj+"-official-key-command.json"),dict(command=cmd,exit_code=p.returncode,stderr=p.stderr,
        runtime_sha256=sha(runtime),debug_sha256=sha(debug),output=str(out),output_sha256=sha(out),
        selection=str(selection),selection_sha256=sha(selection),tool_sha256=sha(TEMP/"official_key_presence")))
    print(obj,p.returncode);return p.returncode
if __name__=="__main__":raise SystemExit(build() if sys.argv[1]=="build" else collect(sys.argv[1]))
