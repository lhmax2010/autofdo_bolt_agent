"""Preliminary exact static candidate lookup, not final correspondence.

This deliberately stops short of assigning not_instrumented or any U membership.
Input paths must name this task's derived inventory and coverage JSON.
"""
import argparse
import collections
import json
import posixpath
import re
from pathlib import Path

def audit(coverage,inventory):
    ref={(x["file"],x["name"]) for x in coverage["merged_functions"]}
    missing=[x for x in inventory["code_dies"]
             if (posixpath.normpath(x["decl_file"]) if x["decl_file"] else None,
                 re.sub(r"\.__uniq\.\d+$","",x["name"] or "")) not in ref]
    groups=collections.Counter((x["decl_file"],x["name"],x["producer"]) for x in missing)
    return {"purpose":"Static candidate lookup only; no correspondence inferred",
            "normalization":"posixpath.normpath for both sides; remove only .__uniq.<digits> suffix",
            "code_die_count":len(inventory["code_dies"]),
            "no_candidate_die_count":len(missing),
            "system_header_no_candidate_dies":sum((x["decl_file"] or "").startswith("/usr/include/") for x in missing),
            "no_candidate_groups":[{"decl_file":k[0],"name":k[1],"producer":k[2],"count":v}
                                   for k,v in sorted(groups.items(),key=lambda kv:str(kv[0]))],
            "examples":missing[:5]}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--coverage",required=True)
    p.add_argument("--inventory",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    result=audit(json.loads(Path(a.coverage).read_text()),json.loads(Path(a.inventory).read_text()))
    Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
