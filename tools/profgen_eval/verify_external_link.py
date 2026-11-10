"""Link-driver inspection only: no relink, empty response used for -###."""
import json,re,shlex,subprocess,posixpath
from pathlib import Path
from run_scoped import WORK,sha
from apply_header_ruling import rows,norm_file
from dwarf_inventory import text as dwarf_text

OUT=WORK/"docs/profgen/eval/prep/evidence/ruling2"

def main():
    e=json.loads((OUT/"external-cu-members.json").read_text())
    command=e["driver_command"][:-1]
    original_archive=Path(e["archive"])
    selected=Path(e["driver_result"].strip())
    if not selected.samefile(original_archive):raise RuntimeError("archive differs")
    rsp=WORK/"temp/prep-ruling2/empty-link-inputs.rsp";rsp.write_text("")
    artifacts={r["id"]:r for r in json.loads((WORK/"docs/profgen/impl/evidence/11/08_artifacts.json").read_text())}
    records={}
    for obj in ("ffmpeg-thumb","ffmpeg-a32"):
        log=Path(artifacts[obj+"-S"]["log_path"])
        links=[]
        for no,line in enumerate(log.read_text().splitlines(),1):
            text=re.sub(r"^\[\s*\d+s\]\s*","",line)
            if "clang -shared" in text and "-o libavcodec/libavcodec.so.62 " in text:
                links.append((no,text))
        if len(links)!=1:raise RuntimeError(links)
        line,text=links[0];args=shlex.split(text)[1:]
        substitutions=[]
        for i,arg in enumerate(args):
            if arg.startswith("@"):
                substitutions.append({"original":arg,"inspection_only":"@"+str(rsp)})
                args[i]="@"+str(rsp)
        proc=subprocess.run(command+args+["-###"],cwd=WORK/"temp/eval-prep11/ffmpeg",capture_output=True,text=True)
        (OUT/(obj+"-link-driver.txt")).write_text(proc.stderr)
        if proc.returncode or '"-lgcc"' not in proc.stderr:raise RuntimeError(proc.stderr)
        covfiles={norm_file(r["file"]) for r in rows(OUT.parent/(obj+"-coverage-tables"),"files-*.csv")}
        units={r["offset"]:json.loads(r["attrs"]) for r in rows(OUT.parent/(obj+"-S-inventory-tables"),"compile_units-*.csv")}
        entries=[]
        old=json.loads((OUT.parent/"ruling1"/(obj+"-conclusions")/"blocking-no-candidate.json").read_text())
        old={r["die"]:r for r in old}
        for r in e["matches"][obj]:
            source=old[r["die"]]
            comp_dir=dwarf_text(units[source["cu"]].get("comp_dir"))
            absolute_source=posixpath.normpath(posixpath.join(comp_dir, source["cu_name"])) if comp_dir and source["cu_name"] else None
            proof=(bool(absolute_source) and r["member_match_unique"] and bool(source["cu_name"]) and bool(source["producer"])
                and source["producer"].startswith("GNU ") and absolute_source not in covfiles
                and not source["reference_candidates"] and not source["same_name_other_file_candidates"])
            entries.append(dict(**r,conclusion="not_instrumented" if proof else None,
                                source=source["cu_name"],normalized_source=absolute_source,comp_dir=comp_dir,producer=source["producer"]))
        records[obj]={"link_log":str(log),"log_sha256":sha(log),"line":line,"original_command":text,
                      "inspection_command":command+args+["-###"],"response_substitution":substitutions,
                      "limitation":"response object list unavailable; -### confirms compiler's default runtime search, not a historical linker map",
                      "archive":str(original_archive),"archive_sha256":sha(original_archive),
                      "selected_archive":str(selected),"same_file":selected.samefile(original_archive),"entries":entries}
    (OUT/"external-cu-register.json").write_text(json.dumps(records,indent=2)+"\n")
    print({o:sum(x["conclusion"]=="not_instrumented" for x in r["entries"]) for o,r in records.items()})

if __name__=="__main__":main()
