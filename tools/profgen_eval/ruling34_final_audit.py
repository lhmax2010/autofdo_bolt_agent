"""Final audit for the static ruling3/4 batch."""
import json,hashlib,subprocess
from pathlib import Path
from ruling34_inputs import OUT
from run_scoped import WORK,sha
files=sorted(p for p in OUT.rglob("*") if p.is_file())
assert all(p.stat().st_size<1000000 for p in files)
checked=0
for p in OUT.rglob("index.json"):
    meta=json.loads(p.read_text())
    for part in meta.get("parts",[]):
        path=Path(part["path"])
        if not path.is_absolute():path=WORK/path
        assert path.is_relative_to(OUT),(p,path)
        assert sha(path)==part["sha256"],(p,path)
        checked+=1
original=["tools/profgen_eval/static_coverage_gate.py","tools/profgen_eval/static_gate_data.py",
 "tools/profgen_eval/static_map_bridge.py","docs/profgen/design/02_llvm_profgen_enhance_design_v1.5.md"]
p=subprocess.run(["git","diff","--exit-code","HEAD","--",*original],capture_output=True,text=True)
assert p.returncode==0,p.stdout
summaries=[]
for obj in ("spike-thumb","spike-a32","ffmpeg-thumb","ffmpeg-a32"):
    s=json.loads((OUT/(obj+"-static/summary.json")).read_text())
    assert s["loss_equation"]["difference"]==s["old_C_to_new_U_loss"]["difference"]==0
    a=json.loads((OUT/(obj+"-rev2-proof/summary.json")).read_text())
    assert a["key_acceptance_or_depth_differences"]==0
    assert s["registration_status"]=="可登记"
    summaries.append(dict(object=obj,C=s["C_lines"],U=s["U_lines"],coverage_3=s["coverage_3"],
        no_key_consistency=s["no_key_static_crosscheck"],key_acceptance_differences=0))
result=dict(checked_output_SHA_entries=checked,old_code_and_design_unchanged=True,
    files=len(files),new_files_under_1MB=True,objects=summaries,
    command=["python3","tools/profgen_eval/ruling34_final_audit.py"])
(OUT/"final-audit.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(result,ensure_ascii=False))
