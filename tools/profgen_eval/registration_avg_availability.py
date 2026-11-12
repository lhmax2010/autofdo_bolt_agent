"""Q.5 #6: exact batch1 synthetic input, avg availability; no RUN reader."""
import collections
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from run_scoped import WORK, sha
from registration_address_check import BASE, TOOL, TOOL_SHA, dump, rows, key_string
from registration_calibration import entry_keys
from registration_admission import validate_generation_argv
from pack_static_evidence import tables

OUT = BASE / "registration-checks/batch3"
TEMP = WORK / "temp/registration-batch3"
OBJECTS = ("spike-thumb", "spike-a32", "ffmpeg-thumb", "ffmpeg-a32")


def plan():
    OUT.mkdir(exist_ok=True)
    assert sha(TOOL) == TOOL_SHA
    records = []
    for obj in OBJECTS:
        source = BASE / "registration-checks/batch1" / (obj+"-addresses")
        manifest = json.loads((source/"inputs.json").read_text())
        perf = next(r for r in manifest["inputs"] if r["path"].endswith("synthetic-all.perfscript"))
        assert sha(perf["path"]) == perf["sha256"]
        records.append(dict(object=obj, input=perf, manifest=str(source/"inputs.json"), manifest_sha256=sha(source/"inputs.json")))
    dump(OUT/"avg-plan.json", dict(kind="synthetic_input_availability", tool_sha256=sha(TOOL),
        combinations=[dict(aggregation="avg",skid=s) for s in ("none","prev-inst")],
        basis={"avg/none":"v1.8 5.8.6 line 568: avg versus max/none baseline",
               "avg/prev-inst":"v1.8 5.8.6 line 568 final recommended combination; 5.9.2 lines 619,632 each shortlisted aggregation/skid combination. Availability only; no selection or comparison."},
        inputs=records, formal_profiles_opened=False))


def run(obj, skid):
    assert obj in OBJECTS and skid in ("none","prev-inst")
    assert sha(TOOL) == TOOL_SHA
    plan_data=json.loads((OUT/"avg-plan.json").read_text())
    item=next(r for r in plan_data["inputs"] if r["object"]==obj)
    assert sha(item["input"]["path"]) == item["input"]["sha256"]
    source=BASE/"registration-checks/batch1"/(obj+"-addresses")
    old=json.loads((source/(skid+"-command.json")).read_text())
    dest=OUT/(obj+"-avg-"+skid); dest.mkdir()
    output=TEMP/(obj+"-avg-"+skid)/"synthetic.proftext"
    output.parent.mkdir(exist_ok=False)
    report=output.with_suffix(".quality.json")
    replacements={"--ip-aggregation=":"avg","--output=":str(output),"--quality-report=":str(report)}
    command=[next((k+v for k,v in replacements.items() if x.startswith(k)),x) for x in old["command"]]
    assert "--perfscript="+item["input"]["path"] in command
    validate_generation_argv(command)
    result=subprocess.run(command,text=True,capture_output=True)
    q=json.loads(report.read_text()) if report.exists() else {}
    dump(dest/"conversion.json",dict(command=command,exit_code=result.returncode,stderr=result.stderr,stdout=result.stdout,
        input=item["input"],output=str(output),output_sha256=sha(output) if output.exists() else None,
        report=str(report),report_sha256=sha(report) if report.exists() else None,
        failure_stage=q.get("failure_stage"),tool_sha256=sha(TOOL)))
    if result.returncode: return result.returncode
    assert output.is_relative_to(TEMP) and output.name=="synthetic.proftext"
    dbpath=WORK/"temp/prep-ruling3-4"/(obj+"-static.sqlite")
    db=sqlite3.connect("file:"+str(dbpath)+"?mode=ro",uri=True)
    groups={r["name"]:r["role"] for r in rows(BASE/"identity-gate"/(obj+"-groups"),"groups-*.csv")}
    counts=collections.Counter(); details=[]; failures=[]
    with output.open() as stream:
        for number,key in entry_keys(stream):
            hit=db.execute("SELECT 1 FROM kv WHERE k=? LIMIT 1",(key_string(key),)).fetchone()
            category=("mapping_table_hit" if hit else "known_out_of_scope" if groups.get(key[0][0])=="known_out_of_scope"
                      else "unknown_name" if key[0][0] not in groups else "unmapped_key")
            counts[category]+=1; details.append([number,key,category])
            if category not in ("mapping_table_hit","boundary_unavailable","known_out_of_scope"): failures.append([number,key,category])
    parts=tables(dest,"entries",["line","key","classification"],details)
    dump(dest/"classification.json",dict(kind="synthetic_input_availability",counts=counts,entries=sum(counts.values()),
        unaligned=len(failures),failures=failures,parts=parts,map_sha256=sha(dbpath)))
    db.close()
    print(json.dumps(dict(object=obj,skid=skid,counts=counts,unaligned=len(failures))))
    return 1 if failures else 0


if __name__=="__main__":
    if sys.argv[1]=="plan": plan()
    else: sys.exit(run(*sys.argv[1:]))
