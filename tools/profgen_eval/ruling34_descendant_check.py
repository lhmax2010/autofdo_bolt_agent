import json,sys,collections
from pathlib import Path
sys.path.insert(0,"tools/profgen_eval")
from ruling4_apply import calculate
from ruling34_inputs import OUT,dump
from static_gate_data import TEMP
from static_coverage_gate import profile_key
result={}
for obj in ("ffmpeg-thumb","ffmpeg-a32"):
 refs,da,rlines,inv,old,funcs,ic,groups,new=calculate(obj)
 touched=set();keys=set()
 with (TEMP/(obj+"-map.jsonl")).open() as f:
  for l in f:
   r=json.loads(l)
   if r["kind"]!="instruction":continue
   touched.update(r["dies_leaf_to_root"])
   if profile_key(r["frames_leaf_to_root"]):keys.update(r["dies_leaf_to_root"])
 bad=[dict(die=hex(d),check=x,raw=funcs[d]) for d,x in ic.items() if d in touched and x["instance_class"].startswith(("b_","c_")) and d not in keys]
 result[obj]=dict(touched=len(touched),key_contexts=len(keys),descendant_claim_without_actual_key=bad)
dump(OUT/"descendant-key-crosscheck.json",result)
print({k:len(v["descendant_claim_without_actual_key"]) for k,v in result.items()})
