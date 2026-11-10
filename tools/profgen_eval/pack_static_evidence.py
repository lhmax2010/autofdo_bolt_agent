"""Pack derived static tables into small text shards; retain original hashes.

Only explicit *-coverage.json / *-inventory.json paths from this round are read.
The input ELF/coverage originals are never changed. Raw dumps are reproducible
with the retained platform command and SHA. No sample profile is accepted.
"""
import csv
import hashlib
import io
import json
from pathlib import Path

BASE=Path("docs/profgen/eval/prep/evidence")

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()

def tables(out,name,header,rows):
    parts=[]; lines=[]; size=0
    def line(row):
        s=io.StringIO()
        csv.writer(s,lineterminator="\n").writerow(
            [json.dumps(v,ensure_ascii=False,separators=(",",":")) if isinstance(v,(list,dict)) else v for v in row])
        return s.getvalue()
    heading=line(header)
    def flush():
        nonlocal lines,size
        p=out/f"{name}-{len(parts):03d}.csv"
        p.write_text(heading+"".join(lines))
        parts.append({"path":str(p),"sha256":sha(p),"rows":len(lines)})
        lines=[];size=0
    for row in rows:
        text=line(row)
        if size+len(text.encode())>600000 and lines:
            flush()
        lines.append(text);size+=len(text.encode())
    if lines:flush()
    return parts

def pack(p):
    d=json.loads(p.read_text()); out=BASE/(p.stem+"-tables");out.mkdir(exist_ok=True)
    meta={"source_derived_path":str(p),"source_derived_sha256":sha(p),"parts":[]}
    if p.name.endswith("-inventory.json"):
        meta.update({k:d[k] for k in ["elf","command","dump_sha256","stderr"]})
        # Every code-bearing DIE remains, including all inlined instances.
        cols=["die","tag","parent","cu","name","decl_file","decl_line","ranges","dump_line"]
        meta["parts"]+=tables(out,"code-dies",cols,([r.get(k) for k in cols] for r in d["code_dies"]))
        cols=["offset","tag","cu","parent","dump_line","attrs","ranges"]
        for key in ["compile_units","referenced_definitions"]:
            meta["parts"]+=tables(out,key,cols,([r.get(k) for k in cols] for r in d[key]))
        meta["omitted_redundant_fields"]="code DIE raw attributes and duplicated CU producer/name/comp_dir; resolved identity and ranges retained, raw dump SHA + regeneration command retained"
    else:
        meta.update({"json":d["json"],"lcov":d["lcov"],
                     "extra_lcov_files":d["extra_lcov_files"],"empty_main":d["empty_main"]})
        cols=["file","executable_lines","covered_lines","json_summary","lcov_summary","has_multiple_regions","da_differences"]
        meta["parts"]+=tables(out,"files",cols,([r[k] for k in cols] for r in d["files"]))
        cols=["name","start","lcov_fn_present","lcov_fnda_present"]
        meta["parts"]+=tables(out,"function-checks",["record"]+cols,([i]+[r[k] for k in cols] for i,r in enumerate(d["function_checks"])))
        cols=["file","name","start","end","fnda","copies","code_regions"]
        meta["parts"]+=tables(out,"merged-functions",cols,([r[k] for k in cols] for r in d["merged_functions"]))
        cols=["function_record","spelling_file_id","expansion_file_id","region","spelling_file","expanded_file"]
        meta["parts"]+=tables(out,"macro-regions",cols,([r.get(k) for k in cols] for r in d["macro_regions"]))
    m=out/"index.json";m.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
    # This derived intermediate is fully reproducible, not an original input.
    p.unlink()
    return {"index":str(m),"sha256":sha(m),"original_sha256":meta["source_derived_sha256"]}

if __name__=="__main__":
    names=[f"{o}-{isa}-{stage}-inventory.json" for o in ["spike","ffmpeg"]
           for isa in ["thumb","a32"] for stage in ["S","C"]]
    names += [f"{o}-{isa}-coverage.json" for o in ["spike","ffmpeg"] for isa in ["thumb","a32"]]
    result=[pack(BASE/name) for name in names]
    (BASE/"packed-products.json").write_text(json.dumps(result,indent=2)+"\n")
