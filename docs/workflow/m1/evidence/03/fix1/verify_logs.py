from pathlib import Path
import json,re,hashlib
F=Path(__file__).resolve().parent
for v in ("thumb","a32"):
 out=F/("build-"+v);log=out/"build.log"
 result=json.loads((out/"result.json").read_text())
 lines=log.read_text(errors="replace").splitlines()
 commands=[(i+1,l) for i,l in enumerate(lines) if re.search(r"\bclang\s",l) and " -c " in l and "libav" in l]
 wanted="-mthumb" if v=="thumb" else "-marm"
 checks=[]
 for n,l in commands:
  flags=all(f in l for f in ("-fdebug-info-for-profiling","-funique-internal-linkage-names"))
  isa=re.findall(r"-m(?:thumb|arm)\b",l)
  checks.append(dict(log_line=n,profiling_flags=flags,effective_isa=isa[-1] if isa else None))
 assert commands and all(x["profiling_flags"] and x["effective_isa"]==wanted for x in checks)
 selected=[]
 for lib in ("libavcodec","libavutil"):
  examples=[(n,l) for n,l in commands if lib+"/" in l]
  assert examples
  selected.extend(examples[:2])
 (out/"compile-excerpts.txt").write_text("\n".join(str(n)+": "+l for n,l in selected)+"\n")
 errors=[(i+1,l) for i,l in enumerate(lines) if any(x in l for x in ("error:", "find-debuginfo.sh", "debugedit:", "V=1/debug", "ALL-END", "已结束"))]
 (out/"failure-excerpts.txt").write_text("\n".join(str(n)+": "+l for n,l in errors)+"\n")
 r=dict(variant=v,actual_clang_libav_compilations=len(commands),all_profiling_flags_present=True,all_effective_isa_match=True,effective_isa=wanted,
 gbs_exit=result["gbs_exit"],log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),packaged_library_buildid_validation="not performed: packaging failed")
 (out/"compile-validation.json").write_text(json.dumps(r,indent=2)+"\n")
 print(json.dumps(r))
