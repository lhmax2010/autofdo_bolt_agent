"""Audit only this ruling's explicit artifacts and immutable static inputs."""
import json,subprocess
from pathlib import Path
from ruling3_union import OUT,TEMP,dump
from run_scoped import WORK,sha
from pack_static_evidence import tables
def main():
    checked={}
    for p in OUT.rglob("index.json"):
        d=json.loads(p.read_text())
        for r in d.get("parts",[]):
            q=Path(r["path"]);q=q if q.is_absolute() else WORK/q
            assert q.is_relative_to(WORK),q
            if str(q) not in checked:checked[str(q)]=sha(q)
            assert checked[str(q)]==r["sha256"],q
        if "summary_sha256" in d:assert sha(p.parent/"summary.json")==d["summary_sha256"]
    oldtests=[
        p for p in (WORK/"tools/profgen_eval").glob("test_*.py") if p.name!="test_ruling3_union.py"]
    for p in oldtests:
        expected=subprocess.check_output(["git","show","HEAD:"+str(p.relative_to(WORK))])
        assert expected==p.read_bytes(),p
    failed=OUT/"AST-plugin-build-failed.json"
    d=json.loads(failed.read_text());q=TEMP/"failed-plugin-build/stmt_ranges.cpp"
    assert sha(q)==d["source_sha256"]
    dump(OUT/"failure-source.json",dict(path=str(q),sha256=sha(q),failed_command_metadata=str(failed),metadata_sha256=sha(failed)))
    allresources=[]
    for p in OUT.rglob("resources.json"):
        d=json.loads(p.read_text());d["path"]=str(p);allresources.append(d)
    dump(OUT/"resources-summary.json",dict(min_memavailable=min(r["min_memavailable"] for r in allresources),
        peak_memory=max(r["memory_peak_bytes"] for r in allresources),
        resource_terminated=any(r["resource_terminated"] for r in allresources),scopes=allresources))
    files=sorted(p for p in OUT.rglob("*") if p.is_file() and p.name!="artifact-sha256.csv")
    files += [WORK/"tools/profgen_eval"/s for s in (
        "ruling3_union.py","ruling3_union_static.py","code_free_ast.py","classify_code_free.py","test_ruling3_union.py","report_ruling3_union.py","audit_ruling3_union.py")]
    assert all(p.stat().st_size<1000000 for p in files)
    print(json.dumps(dict(verified_parts=len(checked),old_test_files_unchanged=len(oldtests),
        artifact_files=len(files),largest=max(p.stat().st_size for p in files),total_bytes=sum(p.stat().st_size for p in files))))
if __name__=="__main__":main()
