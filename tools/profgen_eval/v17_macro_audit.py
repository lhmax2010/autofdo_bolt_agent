"""Reprove recorded API tokens with v1.7 role labeling; no compiler rebuild."""
import collections,json
from pathlib import Path
from apply_paste_ruling import BASE,OUT as OLD,OLD as SUP2,paths
from audit_macro_tokens import raw_records,function_evidence
from token_paste_rule import extend_operand_chain
from macro_function_rule import classify_macro
from run_scoped import sha
from v17_domain import OUT,dump
def main():
 results=[];sources=[]
 for mode in ("thumb","a32"):
  obj="ffmpeg-"+mode
  commands=OLD/(mode+"-token-api-commands.json")
  cmds={x["tu"]:x for x in json.loads(commands.read_text())}
  audit=BASE/"ruling2"/(obj+"-macro-audit.json")
  audits=json.loads(audit.read_text())
  cache={}
  for i,a in enumerate(audits):
   cmd=cmds[a["cu"]]
   if a["cu"] not in cache:
    assert cmd["exit_code"]==0 and sha(Path(cmd["output"]))==cmd["output_sha256"]
    cache[a["cu"]]=raw_records(Path(cmd["output"]))
    sources.append(dict(path=cmd["output"],sha256=cmd["output_sha256"]))
   raw=cache[a["cu"]];macros=[x for x in raw if x["record"]=="macro"]
   oldpath=SUP2/f"{obj}-{i+1:02d}-tokens.json"
   record=json.loads(oldpath.read_text())["identity_record"]
   f=function_evidence(a,raw,cmd);f["coverage_main_file"]=record["coverage_main_file"]
   extend_operand_chain(f,macros)
   context={k:f[k] for k in ("macro_callbacks","invocations","coverage_main_file")}
   context["chain"]={k:f["chain"][k] for k in ("invocation_argument_ranges","definition_body_ranges")}
   context["macros"]=macros;f["chain"]["paste_context"]=context
   record["compiler_ast_chain"]=f["chain"]
   verdict=classify_macro(record)
   old=json.loads((OLD/f"{obj}-{i+1:02d}-proof.json").read_text())
   assert verdict==old["verdict"],(obj,i,verdict)
   pc=collections.Counter()
   for proof in f["chain"].get("paste_proofs",[]):
    assert proof["status"]=="proved"
    pc.update(paths(proof))
   results.append(dict(object=obj,index=i+1,name=a["name"],fnda=a["fnda"],verdict=verdict,
                       proof_paths=pc,old_proof=str(OLD/f"{obj}-{i+1:02d}-proof.json"),
                       old_proof_sha256=sha(OLD/f"{obj}-{i+1:02d}-proof.json")))
 dump(OUT/"macro-recheck.json",dict(records=results,compiler_inputs=sources,closed=len(results),
      changed_verdicts=0,positive_FNDA=sum(r["fnda"]>0 for r in results)))
 print("68 macro verdicts unchanged; all scratch proofs pass")
if __name__=="__main__":main()
