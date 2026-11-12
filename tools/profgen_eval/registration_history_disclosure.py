"""Q.5 #17: reconstruct historical disclosure from metadata; NEVER open profiles."""
import collections,json,re,subprocess
from pathlib import Path
from run_scoped import WORK,sha
from registration_address_check import BASE,dump
from pack_static_evidence import tables

OUT=BASE/"registration-checks/batch3"


def main():
    command=["git","-c","gc.auto=0","-c","maintenance.auto=false","ls-files","docs/profgen/impl","docs/profgen/eval","docs/probe"]
    tracked=subprocess.check_output(command,text=True).splitlines()
    metadata={WORK/p for p in tracked if p.endswith(".json") and
              ("/impl/evidence/" in p or "/probe/evidence/" in p)}
    # Retained command/verification logs, never their profile or perf outputs.
    prefixes=("profgen-patch4","profgen-patch5","profgen-patch6","profgen-patch7","profgen-patch8","profgen-patch8-amend","profgen-patch9",
              "board-round1","board-round1-resume","board-round1-resume2","board-round1-amend1","board-round1-patch8","board-round1-retry",
              "p9-formal-reconversion")
    for prefix in prefixes:
        for p in (WORK/"temp"/prefix).rglob("*.json"):
            if any(x in p.name for x in ("command","converted","comparison","summary","replay","full")) or p.name in ("run.json","runs.json","generation.json") or any(x.startswith(("full-","real","before-real","after-real")) for x in p.relative_to(WORK/"temp"/prefix).parts[:-1]):
                metadata.add(p)
    known=set()
    for row in json.loads((WORK/"docs/profgen/impl/evidence/08/25_patch6_real_exports.json").read_text()):
        known.add(str((WORK/row["input"]).resolve()))
    records=collections.defaultdict(lambda:dict(sources=[],inputs=set(),operations=set(),recorded_sha256=set(),exit_codes=set()))
    examined=[];failures=[];attempts=[]

    def real_input(value):
        if not isinstance(value,str):return False
        path=Path(value);path=path if path.is_absolute() else WORK/path
        return str(path.resolve()) in known or "/temp/board-round1" in str(path)

    def norm(value):
        path=Path(value);return str(path if path.is_absolute() else WORK/path)

    def add(path,source,loc,inp,record,operation):
        path=norm(path)
        if not path.startswith(str(WORK)+"/"):failures.append(dict(source=str(source),path=path,reason="outside_workdir_reference"));return
        r=records[path]
        r["sources"].append(dict(file=str(source.relative_to(WORK)),json_path=loc))
        if inp:r["inputs"].add(norm(inp))
        r["operations"].add(operation)
        for k in ("profile_sha256","output_sha256","profile_sha") + (("sha256",) if record.get("path") and norm(record["path"])==path else ()):
            value=record.get(k)
            if isinstance(value,str) and re.fullmatch("[0-9a-f]{64}",value):r["recorded_sha256"].add(value)
        for h in record.get("hashes",[]) if isinstance(record.get("hashes"),list) else []:
            if isinstance(h,dict) and isinstance(h.get("profile"),str) and re.fullmatch("[0-9a-f]{64}",h["profile"]):
                r["recorded_sha256"].add(h["profile"])
                r["operations"].add("two-pass SHA/determinism and previous-patch profile comparison")
        for run in record.get("runs",[]) if isinstance(record.get("runs"),list) else []:
            if isinstance(run,dict) and isinstance(run.get("exit"),int):r["exit_codes"].add(run["exit"])
        for k in ("exit_code","rc","exit"):
            if isinstance(record.get(k),int):r["exit_codes"].add(record[k])

    def walk(node,source,loc="root"):
        if isinstance(node,dict):
            for key in ("command","cmd","argv","arguments"):
                cmd=node.get(key)
                if not isinstance(cmd,list) or not all(isinstance(v,str) for v in cmd):continue
                perf=next((s.split("=",1)[1] for s in cmd if s.startswith("--perfscript=")),None)
                output=next((s.split("=",1)[1] for s in cmd if s.startswith("--output=")),None)
                if real_input(perf) and output:
                    # An output option alone can also designate a failed conversion.
                    attempts.append(dict(output=norm(output),input=norm(perf),source=str(source.relative_to(WORK)),json_path=loc,
                                         exit_code=next((node[k] for k in ("exit_code","rc","exit") if isinstance(node.get(k),int)),None)))
                    add(output,source,loc,perf,node,"real_input_conversion_output; SHA/content-read confirmation follows evidence")
            inp=node.get("source") or node.get("input")
            if real_input(inp):
                folder=node.get("output_directory")
                if isinstance(folder,str) and node.get("profile_sha256"):
                    add(str(Path(folder)/"profile.extbinary"),source,loc,inp,node,"profile_SHA_and_previous_profile_equality")
            for k,v in node.items():walk(v,source,loc+"."+str(k))
        elif isinstance(node,list):
            for i,v in enumerate(node):walk(v,source,loc+"["+str(i)+"]")

    for path in sorted(metadata):
        try:j=json.loads(path.read_text())
        except (ValueError,UnicodeError) as e:failures.append(dict(path=str(path),reason=str(e)));continue
        examined.append(dict(path=str(path.relative_to(WORK)),sha256=sha(path)))
        walk(j,path)

    # Explicit confirmed P8/P9 formal-profile pairs and exact period outputs.
    old=json.loads((WORK/"temp/board-round1-retry/final-reconverted.json").read_text())["runs"]
    comparisons=json.loads((WORK/"docs/profgen/impl/evidence/16/08_p9_reconversion_rows.json").read_text())
    bypair={(r["run"],r["weight"]):r for r in comparisons}
    for row in old:
        tag=Path(row["source"]).name;folder=WORK/"temp/p9-formal-reconversion/outputs"/tag
        for prefix,weight in (("","sample"),("period-","period")):
            cp=folder/(prefix+"command.json")
            if not cp.exists():continue
            j=json.loads(cp.read_text());cmd=j["command"]
            output=next(v.split("=",1)[1] for v in cmd if v.startswith("--output="))
            pair=bypair[(tag,weight)]
            add(output,cp,"command",str(Path(row["source"])/"perfscript.txt"),dict(profile_sha256=pair["after"]),"P9 profile tree/total/body/wrapped-callsite and byte-SHA comparison (no M1/M2)")
            previous=(Path(row["output_directory"])/("profile.extbinary" if weight=="sample" else "period.extbinary"))
            # Find old period output from retained command metadata instead of guessing.
            if weight=="period":
                candidates=[p for p in records if tag in p and "period" in Path(p).name and "p9-formal" not in p]
                for p in candidates:
                    records[p]["operations"].add("historical period comparison documented; path from original command")
            else:add(str(previous),WORK/"temp/board-round1-retry/final-reconverted.json",tag,row["source"],dict(profile_sha256=pair["before"]),"P8 old profile SHA/tree comparison with P9")
    # Prior batch2 disclosed new CALIBRATION profiles; metadata only this batch.
    for tag in ("cal-thumb","cal-a32","cal-ffmpeg-thumb","cal-ffmpeg-a32"):
        p=BASE/"registration-checks/batch2"/tag/"before-classification.json"
        j=json.loads(p.read_text())
        add(j["path"],p,"root",None,j,"batch2 CALIBRATION max/none/period entry-category counts and stage exit codes only")
    parts=[]
    ordered=[]
    for path,r in sorted(records.items()):
        ordered.append(dict(path=path,inputs=sorted(r["inputs"]),recorded_sha256=sorted(r["recorded_sha256"]),exit_codes=sorted(r["exit_codes"]),
          operations=sorted(r["operations"]),evidence=r["sources"],opened_this_batch=False,
          documented_quantities=(
            ["entry-category counts and stage exit codes only; no body ratios or quality metrics"] if "/registration-batch2/" in path else
            ["3 hot functions: independent instruction denominator n(k), avg/sum/max body values and per-key differences; see report13 / evidence12/31"] if "/independent-avg/" in path else
            ["SHA byte equality; parsed tree/body/callsite/total differences; written positions; exclusion of 2736 nonleaf-line0 samples; associated report layer counts, ratios and function coverage ranking; see quality_round1 section P9 reconversion"] if "/p9-formal-reconversion/" in path else
            ["conversion exit; profile SHA/equality/determinism when recorded; input/target/usable/layer counts and quality JSON; nonleaf-line0 address/function breakdown and period/sample conversion checks where reported; see reports12/13"] if "/board-round1" in path else
            ["historical whole-export conversion: existence/exit, SHA/equality/determinism, generation address/body/tree correctness and quality-report counters when recorded; reports06-09/13/15; not M1/M2"]),

          historical_read_confirmation="SHA/content comparison recorded" if r["recorded_sha256"] or any("comparison" in op or "CALIBRATION" in op for op in r["operations"])
          else "conversion output mentioned; may be failure/no output; see attempt rows (not asserted opened)"))
    parts+=tables(OUT,"historical-profile-disclosure",["record"],([r] for r in ordered))
    parts+=tables(OUT,"historical-conversion-attempts",["record"],([r] for r in attempts))
    parts+=tables(OUT,"historical-disclosure-sources",["path","sha256"],([r["path"],r["sha256"]] for r in examined))
    dump(OUT/"historical-disclosure-summary.json",dict(profile_paths=len(ordered),metadata_files=len(examined),attempts=len(attempts),
       confirmed_metadata_read=sum(r["historical_read_confirmation"].startswith("SHA") for r in ordered),parts=parts,
       scan_failures=failures,G0_pretrial="待第12项完成后补充",formal_profiles_opened_this_batch=0,
       policy="Output options with no confirmation are disclosed conservatively as attempts, not claimed opened. Hashes are quoted from retained metadata, never recomputed on profiles.",
       sources_command=command))
    print(json.dumps(dict(paths=len(ordered),metadata_files=len(examined),failures=len(failures))))


if __name__=="__main__":main()
