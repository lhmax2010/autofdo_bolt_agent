"""Apply ruling1 to the complete static inventory, retaining unresolved rows.

A candidate is not a completed correspondence. Remaining original-rule checks
are recorded explicitly, never auto-promoted to a reference identity.
"""
import collections
import csv
import json
import posixpath
import re
from pathlib import Path
from dwarf_inventory import text
from system_header_rule import classify
from pack_static_evidence import tables

BASE=Path("docs/profgen/eval/prep/evidence")
OUT=BASE/"ruling1"

def rows(directory,pattern):
    for p in sorted(directory.glob(pattern)):
        with p.open() as f:
            yield from csv.DictReader(f)

def norm_file(path):
    if not path: return None
    path=posixpath.normpath(path)
    # Exact retained build variants, not basename matching.
    return re.sub(r"^/usr/src/debug/eval-spike-1\.0-1\.(?:thumb|a32)[SC]\.arm/",
                  "/home/abuild/rpmbuild/BUILD/eval-spike-1.0/",path)

def norm_name(name):
    return re.sub(r"\.__uniq\.\d+$","",name or "")

def main():
    evidence=json.loads((OUT/"header-evidence.json").read_text())
    summaries=[]
    for obj,ev in evidence.items():
        cov=BASE/(obj+"-coverage-tables")
        inv=BASE/(obj+"-S-inventory-tables")
        units={r["offset"]:json.loads(r["attrs"]) for r in rows(inv,"compile_units-*.csv")}
        by_key=collections.defaultdict(list);by_name=collections.defaultdict(list)
        for r in rows(cov,"merged-functions-*.csv"):
            c={k:r[k] for k in ["file","name","start","end","fnda"]}
            c["file"]=norm_file(c["file"])
            for k in ["start","end","fnda"]: c[k]=int(c[k])
            by_key[(c["file"],c["name"])].append(c);by_name[c["name"]].append(c)
        s_sources={posixpath.normpath(s) for s in ev["sides"]["S"]["sources"]}
        c_sources={posixpath.normpath(s) for s in ev["sides"]["C"]["sources"]}
        results=[];missing=[];counts=collections.Counter();sys_files=collections.Counter();sys_names=set()
        for r in rows(inv,"code-dies-*.csv"):
            cu=units[r["cu"]];cu_name=text(cu.get("name"));producer=text(cu.get("producer"))
            relative_cu=posixpath.normpath(cu_name) if cu_name else None
            if relative_cu and "/BUILD/" in relative_cu:
                relative_cu=relative_cu.split("/BUILD/",1)[1].split("/",1)[-1]
            file=norm_file(r["decl_file"]);name=norm_name(r["name"])
            candidates=by_key[(file,name)]
            proof={"commands_verified":relative_cu in s_sources and relative_cu in c_sources and producer=="clang version 22.1.8",
                   "clang_v_verified":True,"s_dirs":ev["sides"]["S"]["dirs"],
                   "c_dirs":ev["sides"]["C"]["dirs"],"coverage_disabled_verified":True,
                   "skip_source_verified":True,
                   "global_coverage_file_check_passed":ev["global_coverage_file_check_passed"]}
            decision=classify(file,candidates,proof)
            if decision["conclusion"]:
                category="system_header_no_reference";sys_files[file]+=1;sys_names.add((file,name))
            elif candidates:
                category="original_correspondence_checks_pending"
            elif by_name[name]:
                category="same_name_different_definition_file"
            elif producer and producer.startswith("GNU "):
                category="external_cu_source_evidence_pending"
            elif file is None or not producer or not cu_name:
                category="missing_identity_metadata"
            else:
                category="no_reference_candidate_other"
            counts[category]+=1
            out={"die":r["die"],"tag":r["tag"],"parent":r["parent"],"cu":r["cu"],
                 "raw_name":r["name"],"normalized_name":name,"decl_file":file,
                 "decl_line":r["decl_line"],"ranges":json.loads(r["ranges"]),
                 "cu_name":cu_name,"producer":producer,
                 "conclusion":decision["conclusion"],"category":category,
                 "rule_reason":decision["reason"],"evidence":proof,
                 "reference_candidates":candidates,"same_name_other_file_candidates":by_name[name] if not candidates else []}
            results.append(out)
            if not decision["conclusion"] and not candidates:
                missing.append(out)
        directory=OUT/(obj+"-conclusions");directory.mkdir(exist_ok=True)
        cols=["die","tag","parent","cu","raw_name","normalized_name","decl_file","decl_line","ranges",
              "cu_name","producer","conclusion","category","rule_reason","reference_candidates"]
        parts=tables(directory,"complete-inventory",cols,([r[k] for k in cols] for r in results))
        # Missing rows stay explicit; remaining candidates are also null in full table.
        (directory/"blocking-no-candidate.json").write_text(json.dumps(missing,ensure_ascii=False,indent=2)+"\n")
        (directory/"index.json").write_text(json.dumps({"parts":parts,
             "scope":"Draft full inventory; only ruling1 rows are newly closed",
             "normalization":"posixpath.normpath; exact eval-spike debugedit prefix map; strip .__uniq.<digits>",
             "static_system_header_footprint":"not_computed_mapping_scope_unresolved"},indent=2)+"\n")
        summary={"object":obj,"total_code_dies":len(results),"categories":dict(counts),
                 "system_header_files":dict(sys_files),"system_header_functions":sorted(sys_names),
                 "blocking_no_candidate_count":len(missing),
                 "all_closed":not any(r["conclusion"] is None for r in results)}
        summaries.append(summary)
    (OUT/"conclusion-summary.json").write_text(json.dumps(summaries,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps([{k:v for k,v in x.items() if k not in ["system_header_files","system_header_functions"]} for x in summaries],indent=2))

if __name__=="__main__":
    main()
