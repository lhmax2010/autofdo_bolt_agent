"""Replay independently extracted line rows under synthetic external mutations."""
import json,sys
from pathlib import Path
from v17_domain import OUT,dump
from run_scoped import sha
from apply_header_ruling import norm_file
from v17_rules import domain,domain_sha,ledger

def main(obj):
 index=json.loads((OUT/(obj+"-domain/index.json")).read_text())
 c0path=Path(index["C0_path"]);assert sha(c0path)==index["C0_sha256"]
 c0={(r["file"],r["line"]):r["DA"] for r in json.loads(c0path.read_text())}
 def replay():
  evidence={}
  for m in index["raw"]:
   path=Path(m["output"]);assert sha(path)==m["output_sha256"]
   sections=[];errors=[]
   for line in path.open():
    r=json.loads(line)
    if r["kind"]=="sections":sections=r["sections"]
    elif r["kind"]=="error":errors.append(r["reason"])
   if m["exit_code"]:errors.append("extractor_exit_"+str(m["exit_code"]))
   if m["stderr"]:errors.append("extractor_diagnostic")
   def seqs(path):
    for line in path.open():
     r=json.loads(line)
     if r["kind"]=="sequence":
      for row in r["rows"]:row["file"]=norm_file(row["file"])
      yield r
   evidence[m["stage"]]=dict(sections=sections,sequences=seqs(path),errors=errors)
  return domain(c0,evidence)[0]
 trials=[]
 for state in (dict(correspondence="ordinary",keys="all",mapping_range="all"),
               dict(correspondence="macro_generated_function",keys="none",mapping_range="empty"),
               dict(correspondence="identity_ambiguous",keys="rejected_nonleaf_zero",mapping_range="changed")):
  c=replay();h=domain_sha(c);assert h==index["C_sha256"]
  trials.append(dict(synthetic_external_state=state,C_sha256=h,external_state_not_an_input=True))
 # Exercise the corrected macro transition on an actual witnessed row, with a
 # synthetic DA=1, never alter the real object's correspondence or weight.
 k=min(c);x=ledger({k},{k},{k:1},{})
 y=ledger({k},{k},{k:1},{},{k})
 assert x[0]=={k} and not y[0]
 assert y[2]["buckets"][0]["reasons"]==["macro_generated_function"]
 dump(OUT/(obj+"-invariance.json"),dict(object=obj,trials=trials,
   admitted_inputs=index["admitted_domain_inputs"],C_sha_unchanged=True,
   synthetic_macro_switch=dict(line=k,DA=1,ordinary_U_lines=len(x[0]),macro_U_lines=len(y[0]),
                              macro_ledger=y[2])))
 print(obj,"three C hashes identical")
if __name__=="__main__":main(sys.argv[1])
