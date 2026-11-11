"""Q.5 2/3/4: re-run existing lit Python assertions with an argv recorder.

Unmodified formal llvm-profgen; only generated synthetic fixture profiles opened.
"""
import json
import runpy
import subprocess
import sys
from pathlib import Path
from run_scoped import WORK,platform,sha
from pack_static_evidence import tables

OUT=WORK/"docs/profgen/eval/prep/evidence/registration-checks/batch1"
TEMP=WORK/"temp/registration-batch1"
TREE=WORK/"temp/llvm-profgen-enh"
TOOL=TREE/"build/bin/llvm-profgen"
INPUT=TREE/"llvm/test/tools/llvm-profgen/Inputs/ip-mode"
EXPECTED="2e8895afce661b5fdc8cacab2b3323496fca51af7bd7b51c3753aa8328b7d0d5"
original_run=subprocess.run
RECORDS=[]
GROUP=sys.argv[1] if len(sys.argv)>1 else "unused"


def dump(p,data):
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+"\n")


def option(argv,name):
    result=None
    for i,arg in enumerate(argv):
        if arg.startswith(name+"="):result=arg.split("=",1)[1]
        elif arg==name and i+1<len(argv):result=argv[i+1]
    return result


def state(path):
    if path is None:return dict(exists=False)
    p=Path(path)
    return dict(path=str(p),exists=p.exists(),is_file=p.is_file(),
                sha256=sha(p) if p.is_file() else None)


def recorded_run(argv,**kwargs):
    if argv[0]!=str(TOOL):return original_run(argv,**kwargs)
    number=len(RECORDS)+1
    target,report=option(argv,"--output"),option(argv,"--quality-report")
    injection=option(argv,"--ip-test-inject-failure")
    before=dict(profile=state(target),report=state(report))
    actual=platform("llvm-profgen")[:-1]+list(argv)
    p=original_run(actual,**kwargs)
    after=dict(profile=state(target),report=state(report))
    q=None
    if report and Path(report).is_file():
        q=json.loads(Path(report).read_text())
    check="not_injection"
    if injection:
        if q and "tool" in q:
            assert q["tool"]["arguments"]==list(argv),(q["tool"]["arguments"],argv)
            check="committed_report_arguments_exact"
        else:
            assert p.returncode!=0
            assert before["report"]==after["report"]
            assert before["profile"]==after["profile"]
            assert p.stderr
            check="report_not_committed_executor_evidence"
    record=dict(number=number,argv=list(argv),executed_command=actual,
                returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,
                before=before,after=after,injection=injection,check=check,
                verdict=q.get("verdict") if q else None)
    RECORDS.append(record)
    # Persist each outcome before any later assertion can stop the harness.
    dump(TEMP/(GROUP+"-invocations.json"),RECORDS)
    return p


def main(group):
    assert sha(TOOL)==EXPECTED
    dest=TEMP/group;dest.mkdir(exist_ok=False)
    subprocess.run=recorded_run
    oldargv=sys.argv[:]
    try:
        if group=="thumb":
            script=INPUT/"gnu-thumb/check-normalization.py"
            sys.argv=[str(script),str(TOOL),str(dest)]
        else:
            script=INPUT/"quality/check-quality.py"
            sys.argv=[str(script),str(TOOL),group,str(dest)]
        # stable record name while runpy uses a different argv shape
        global RECORDS
        runpy.run_path(str(script),run_name="__main__")
    finally:
        subprocess.run=original_run
        sys.argv=oldargv
    if group=="missed":
        raise AssertionError("handled separately")
    if group=="thumb":
        negative=[r for r in RECORDS if Path(option(r["argv"],"--binary")).stem in ("odd-arm","odd-data","odd-middle")]
        assert len(negative)==3
        assert all(r["returncode"]!=0 and r["verdict"]["failure_stage"]=="boundary" for r in negative)
        dump(OUT/"q3-derived-negatives.json",negative)
    # Additional unexecuted injection points: no debug file / no report path.
    if group=="output":
        for point,report_enabled in (("debug-open-load",True),("debug-metadata",True),("report-write",False),("report-rename",False)):
            d=dest/("missed-"+point);d.mkdir()
            inp=d/"input.perfscript";inp.write_text("17/17 2 cycles: 1318 (/target+0x318)\n")
            args=[str(TOOL),"--ip-samples","--allow-missing-build-id","--binary-match-regex=^/target$",
                  "--ip-aggregation=sum","--ip-period-unit=1","--format=text",
                  "--binary="+str(INPUT/"a64-pie.perfbin"),"--perfscript="+str(inp),
                  "--output="+str(d/"out.prof"),"--ip-test-inject-failure="+point]
            if report_enabled:args+=["--quality-report="+str(d/"report.json")]
            # No report was requested in the last two cases, so success is valid.
            if report_enabled:
                p=recorded_run(args,capture_output=True,text=True)
                RECORDS[-1]["point_reached"]=False
            else:
                p=original_run(platform("llvm-profgen")[:-1]+args,capture_output=True,text=True)
                RECORDS.append(dict(number=len(RECORDS)+1,argv=args,
                  executed_command=platform("llvm-profgen")[:-1]+args,returncode=p.returncode,
                  stderr=p.stderr,stdout=p.stdout,injection=point,point_reached=False,
                  after=dict(profile=state(d/"out.prof"),report=state(None)),check="no_report_requested_point_not_reached"))
            assert p.returncode==0 and (d/"out.prof").exists(),p.stderr
    directory=OUT/("q234-"+group);directory.mkdir()
    parts=tables(directory,"invocations",["record"],([r] for r in RECORDS))
    raw=TEMP/(group+"-invocations-final.json");dump(raw,RECORDS)
    dump(directory/"index.json",dict(group=group,calls=len(RECORDS),passed=True,
      script=str(script),script_sha256=sha(script),tool=str(TOOL),tool_sha256=sha(TOOL),
      raw=str(raw),raw_sha256=sha(raw),parts=parts,
      injection_checks={x:sum(r.get("check")==x for r in RECORDS) for x in sorted({r["check"] for r in RECORDS})},
      unexecuted_injection_points=[r["injection"] for r in RECORDS if r.get("point_reached") is False]))
    print(group,len(RECORDS),"PASS")


if __name__=="__main__":
    main(sys.argv[1])
