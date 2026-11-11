import json,sys,collections
from pathlib import Path
sys.path.insert(0,"tools/profgen_eval")
from ruling34_inputs import OUT,dump
from static_gate_data import TEMP
from static_coverage_gate import profile_key
data=json.loads((OUT/"descendant-key-crosscheck.json").read_text())
for obj,r in data.items():
 targets={int(e["die"],16):e for e in r["descendant_claim_without_actual_key"]}
 counts={d:collections.Counter() for d in targets};examples={d:[] for d in targets}
 with (TEMP/(obj+"-map.jsonl")).open() as f:
  for l in f:
   x=json.loads(l)
   if x["kind"]!="instruction":continue
   ds=x["dies_leaf_to_root"];fs=x["frames_leaf_to_root"]
   for d in set(ds)&set(targets):
    reason="leaf_zero" if not fs or fs[0]["line"]==0 else ("nonleaf_zero" if any(y["line"]==0 for y in fs[1:]) else "other")
    counts[d][reason]+=1
    if len(examples[d])<2 and fs and fs[0]["line"]>0:examples[d].append(x)
 result=[]
 for d,e in targets.items():result.append(dict(**e,actual_key_rejection=counts[d],instruction_examples=examples[d]))
 dump(OUT/(obj+"-nonleaf-zero-key-cases.json"),result)
 print(obj,collections.Counter(e["check"]["line_status"] for e in result),collections.Counter(k for c in counts.values() for k in c))
 for e in result[:3]:
  print(e["die"],e["actual_key_rejection"])
  for x in e["instruction_examples"][:1]:print(hex(x["address"]),[(f["name"],f["line"]) for f in x["frames_leaf_to_root"]])
