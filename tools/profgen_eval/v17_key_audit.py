"""Re-run all-top static official key enumeration; no RUN/profile input."""
import collections,json,subprocess,sys
from pathlib import Path
from run_scoped import sha,platform
from v17_domain import OUT,TEMP,BASE,dump
from static_gate_data import bridge_inventory
from static_map_bridge import paths,PROFGEN
from ruling4_apply import calculate
from apply_header_ruling import rows
from v17_rules import no_key_proven
from pack_static_evidence import tables

OLD=BASE/"identity-gate/ruling3-4"
def main(obj):
 meta=json.loads((OLD/(obj+"-official-key-command.json")).read_text())
 tool=Path(meta["command"][3]);assert sha(tool)==meta["tool_sha256"]
 build=json.loads((OLD/"rev2-key-tool-build.json").read_text())
 source=(PROFGEN/"ProfiledBinary.cpp").read_text()
 a=source.index("  SampleContextFrameVector CallStack;",source.index("ProfiledBinary::symbolize("))
 b=source.index("\n}",a)
 import hashlib
 assert hashlib.sha256(source[a:b].encode()).hexdigest()==build["copied_block_sha256"]
 inv=bridge_inventory(obj)
 names=sorted({r["name"] for r in inv.values() if r["tag"]=="subprogram"})
 selection=TEMP/(obj+"-all-top.json");dump(selection,names)
 assert names==json.loads(Path(meta["selection"]).read_text())
 run,debug=paths(obj);assert sha(run)==meta["runtime_sha256"] and sha(debug)==meta["debug_sha256"]
 raw=TEMP/(obj+"-keys.jsonl");assert not raw.exists()
 cmd=platform("llvm-dwarfdump")[:-1]+[str(tool),"map",str(run),str(debug),str(selection)]
 with raw.open("w") as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.PIPE,text=True)
 command=dict(command=cmd,exit_code=p.returncode,stderr=p.stderr,output=str(raw),sha256=sha(raw),
   runtime_sha256=sha(run),debug_sha256=sha(debug),all_top_selection_sha256=sha(selection),
   all_top_selection=str(selection),tool_sha256=sha(tool))
 dump(OUT/(obj+"-keys-command.json"),command)
 assert p.returncode==0 and not p.stderr
 groups={};failed={};proofs={};counts=collections.Counter()
 for line in raw.open():
  r=json.loads(line)
  if r["kind"]=="group":groups[r["name"]]=r
  elif r["kind"]=="boundary_unavailable":failed[r["name"]]=r
  elif r["kind"]=="die_keys":proofs[r["die"]]=r
  elif r["kind"]=="key_presence":counts[r["group"]]+=1
  else:raise AssertionError(r["kind"])
 assert set(groups)|set(failed)==set(names)
 assert set(proofs)==set(inv)
 flags={}
 for d,i in inv.items():
  top=inv[i["top_die"]];name=top["name"]
  expected=[r for j in inv.values() if j["tag"]=="subprogram" and j["name"]==name for r in j["normalized_ranges"]]
  g=groups.get(name)
  flags[d]=dict(inventory_complete=True,instance_record_present=d in proofs,
    boundary_available=g is not None,
    enumeration_complete=bool(g and g["ranges"]==expected and counts[name]==g["instruction_count"]),
    symbolization_complete=p.returncode==0,
    accepted_key_instructions=proofs[d]["accepted_key_instructions"])
 fresh_sha=sha(raw);assert fresh_sha==meta["output_sha256"],"all-top key output changed"
 vals=calculate(obj,raw,lambda d:no_key_proven(flags[d]))
 instances,newgroups,new=vals[6:9]
 previous=list(rows(OLD/(obj+"-rev1-identity"),"groups-*.csv"))
 old={(r["file"],r["name"]):json.loads(r["result"]) for r in previous}
 assert all(g==old[(g["file"],g["name"])] for g in newgroups),"identity conclusions changed"
 dest=OUT/(obj+"-key-audit");dest.mkdir()
 parts=tables(dest,"proofs",["die","top_die","name","flags","no_key_proven"],
    ([hex(d),hex(inv[d]["top_die"]),inv[d]["name"],flags[d],no_key_proven(flags[d])] for d in sorted(inv)))
 summary=dict(object=obj,full_inventory=len(inv),all_top_groups=len(names),
    all_top_DIEs=sum(r["tag"]=="subprogram" for r in inv.values()),enumerated_groups=len(groups),
    failed_groups=len(failed),instruction_occurrences=sum(counts.values()),
    byte_identical_to_old=True,new_sha256=fresh_sha,old_sha256=meta["output_sha256"],
    no_key_proven_instances=sum(no_key_proven(v) for v in flags.values()),
    ordinary_no_key_exemptions=sum(x["line_status"]=="no_key_instance" for x in instances.values()),
    ordinary_groups=len(newgroups),ordinary_instances=len(new),identity_results_unchanged=True,
    formal_key_block_sha256=build["copied_block_sha256"],parts=parts,
    mapping_inputs_separate_from_C=[dict(path=str(selection),sha256=sha(selection)),
                                  dict(path=str(raw),sha256=fresh_sha)])
 dump(dest/"summary.json",summary)
 print(json.dumps({k:v for k,v in summary.items() if k!="parts"},ensure_ascii=False))
 return 0
if __name__=="__main__":raise SystemExit(main(sys.argv[1]))
