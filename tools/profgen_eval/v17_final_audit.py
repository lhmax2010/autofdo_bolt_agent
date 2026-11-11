"""Final static-only integrity, size and schema audit; no formal profiles."""
import hashlib,json,subprocess,sys,unittest
from pathlib import Path
from v17_domain import OUT,BASE,TEMP,dump
from run_scoped import WORK,sha,platform
from v17_rules import validate_conclusion,write_conclusion,domain_sha,no_key_proven
from ruling4_apply import calculate
from apply_header_ruling import rows

OBJECTS=("spike-thumb","spike-a32","ffmpeg-thumb","ffmpeg-a32")
def main():
 doc=WORK/"docs/profgen/design/02_llvm_profgen_enhance_design_v1.7.md"
 assert sha(doc)=="9132af9a8242bdb7fa0a37aaf4f43b7eb2e06825fa6546309d5a3e46596ae092"
 assert not Path("/home/linhao/Downloads/02_llvm_profgen_enhance_design_v1.7.md").exists()
 oldpaths=[BASE/"identity-gate/ruling3-4",BASE/"identity-gate/ruling3-rev1",BASE/"identity-gate/code-free-v2"]
 changed=subprocess.check_output(["git","diff","fbf317a","--name-only","--",*[str(p) for p in oldpaths]],text=True)
 assert not changed,changed
 origtests=subprocess.check_output(["git","ls-tree","-r","--name-only","fbf317a","--","tools/profgen_eval"],text=True).splitlines()
 origtests=[p for p in origtests if Path(p).name.startswith("test_") and p.endswith(".py")]
 for path in origtests:
  content=subprocess.check_output(["git","show","fbf317a:"+path])
  assert hashlib.sha256(content).hexdigest()==sha(WORK/path),path
 suite=unittest.defaultTestLoader.discover(str(WORK/"tools/profgen_eval"),pattern="test_*.py")
 def ids(test):
  if isinstance(test,unittest.TestSuite):
   for x in test:yield from ids(x)
  else:yield test.id()
 testnames=list(ids(suite));assert len(testnames)==205
 dump(OUT/"test-inventory.json",dict(tests=testnames,count=len(testnames),original_tests=161,
                                  original_test_files_byte_identical=True))
 results={}
 for obj in OBJECTS:
  proof_flags={int(r["die"],16):json.loads(r["flags"]) for r in rows(OUT/(obj+"-key-audit"),"proofs-*.csv")}
  checked=calculate(obj,TEMP/(obj+"-keys.jsonl"),lambda d:no_key_proven(proof_flags[d]))
  old_groups={(r["file"],r["name"]):json.loads(r["result"]) for r in rows(BASE/"identity-gate/ruling3-4"/(obj+"-rev1-identity"),"groups-*.csv")}
  assert all(g==old_groups[(g["file"],g["name"])] for g in checked[7])
  p=OUT/(obj+"-static/summary.json");s=json.loads(p.read_text())
  validate_conclusion(s)
  dest=TEMP/(obj+"-schema-rewrite.json");write_conclusion(dest,s)
  assert sha(dest)==sha(p),"validated writer must be byte identical"
  d=OUT/(obj+"-domain")
  c={(r["file"],int(r["line"])) for r in rows(d,"lines-*.csv")}
  c0={(r["file"],r["line"]) for r in json.loads((TEMP/(obj+"-C0.json")).read_text())}
  classes={(r["file"],int(r["line"])):r["category"] for r in rows(OUT/(obj+"-classification"),"lines-*.csv")}
  dc=c0-{k for k,v in classes.items() if v in ("asm_interior","structural_line","expr_continuation")}
  u={(r["file"],int(r["line"])) for r in rows(OUT/(obj+"-static"),"U-*.csv")}
  assert u<=c<=dc<=c0
  assert domain_sha(c)==s["C_sha256"]
  assert s["ledger_C_to_U"]["difference"]==s["ledger_C0_to_U"]["difference"]==0
  results[obj]=dict(C_sha256=s["C_sha256"],summary_sha256=sha(p),
    C_dc_sha256=domain_sha(dc),nested_sets=True,two_ledger_differences_zero=True,
    validated_writer_byte_identical=True,final_identity_replay_unchanged=True)
  for m in json.loads((d/"index.json").read_text())["raw"]:
   assert sha(Path(m["elf"]))==m["elf_sha256"]
   assert sha(Path(m["output"]))==m["output_sha256"]
 # Record compiler/tool/library provenance; no build of clang itself.
 cmd=[str(WORK/"temp/eval-prep11/bin/host-clang"),"--version"]
 v=subprocess.run(cmd,capture_output=True,text=True);assert v.returncode==0 and "22.1.8" in v.stdout
 dump(OUT/"compiler-version.json",dict(command=cmd,stdout=v.stdout,stderr=v.stderr,exit_code=v.returncode))
 dump(OUT/"final-audit.json",dict(design_sha256=sha(doc),objects=results,
    unchanged_old_artifact_paths=[str(p) for p in oldpaths],old_artifact_diff=changed,
    tests=205,formal_profiles_read=False,amendment3_registered=False))
 for p in OUT.rglob("*"):
  if p.is_file():assert p.stat().st_size<1000000,(p,p.stat().st_size)
 print("final integrity audit passed; 205 tests; unchanged historical artifacts")
if __name__=="__main__":main()
