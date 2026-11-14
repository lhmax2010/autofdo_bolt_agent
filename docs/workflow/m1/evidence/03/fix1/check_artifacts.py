from pathlib import Path
import subprocess,hashlib,json,re,shutil,sys
W=Path.cwd();D=W/"temp/m1-target-20261114/fix1";variant=sys.argv[1];out=D/("build-"+variant);result=json.loads((out/"result.json").read_text())
B=Path(result["buildroot"]);arch="armv7l";cache=B/"local/cache"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
log=(out/"build.log").read_text(errors="replace")
urls=re.findall(r"downloading (https://\S+?\.rpm)",log)
by_name={u.rsplit("/",1)[-1]:u for u in urls}
deps=[]
for p in sorted(cache.rglob("*.rpm")):
 cmd=["rpm","-qp","--qf","%{NAME}\\t%{VERSION}\\t%{RELEASE}\\t%{ARCH}\\n",str(p)]
 q=subprocess.run(cmd,capture_output=True,text=True)
 assert q.returncode==0,(p,q.stderr)
 fields=q.stdout.strip().split("\t");assert len(fields)==4
 deps.append({"path":str(p.relative_to(W)),"file":p.name,"name":fields[0],"version":fields[1],"release":fields[2],"arch":fields[3],"size_bytes":p.stat().st_size,"sha256":sha(p),"source_url":by_name.get(p.name,"unknown")})
(out/"dependencies.json").write_text(json.dumps(deps,indent=2)+"\n")
A=W/"temp/gbs-deps-archive/ffmpeg-armv7l-20261114";A.mkdir(exist_ok=True)
archived=[]
for dep in deps:
 src=W/dep["path"];dst=A/src.name
 if dst.exists():assert sha(dst)==dep["sha256"],"Archive filename collision"
 else:shutil.copy2(src,dst)
 assert sha(dst)==dep["sha256"]
 archived.append(dict(dep,archive_path=str(dst.relative_to(W))))
(out/"dependency-archive.json").write_text(json.dumps(archived,indent=2)+"\n")
(A/("manifest-fix1-"+variant+".json")).write_text(json.dumps(archived,indent=2)+"\n")
outputs=[{"path":str(p.relative_to(W)),"file":p.name,"size_bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted((B/"local/repos").rglob("*.rpm"))]
(out/"rpm-manifest.json").write_text(json.dumps(outputs,indent=2)+"\n")
if result["gbs_exit"]!=0:
 print(json.dumps({"variant":variant,"build":"failed","dependencies_archived":len(deps),"artifact_check":"not run"}));raise SystemExit(0)
X=out/"extracted";assert not X.exists();X.mkdir()
rpms=B/"local/repos/tizen_unified_standard/armv7l/RPMS"
for name in ["libavcodec","libavutil","ffmpeg-debuginfo"]:
 matches=list(rpms.glob(name+"-8.0.1-*.armv7l.rpm"));assert len(matches)==1,matches
 with (out/(name+"-extract.log")).open("wb") as f:
  p=subprocess.Popen(["rpm2cpio",str(matches[0])],stdout=subprocess.PIPE,stderr=f)
  q=subprocess.run(["cpio","-idm","--no-absolute-filenames"],cwd=X,stdin=p.stdout,stdout=f,stderr=f)
  p.stdout.close();rc=p.wait();assert rc==q.returncode==0
libs=[]
for name in ["libavcodec","libavutil"]:
 matches=[p for p in (X/"usr/lib").glob(name+".so.*") if not p.is_symlink()]
 assert len(matches)==1,matches
 runtime=matches[0];debug=X/"usr/lib/debug"/runtime.relative_to(X);debug=debug.with_name(debug.name+".debug")
 assert debug.exists(),str(debug)
 ids=[]
 for label,path in [("runtime",runtime),("debug",debug)]:
  q=subprocess.run(["readelf","-n",str(path)],capture_output=True,text=True)
  (out/(name+"-"+label+"-notes.txt")).write_text(q.stdout+q.stderr);assert q.returncode==0
  found=re.findall(r"Build ID: ([0-9a-f]+)",q.stdout);assert len(found)==1 and len(found[0])==40,found
  ids.append(found[0])
 assert ids[0]==ids[1],(name,ids)
 libs.append({"name":name,"runtime":str(runtime.relative_to(W)),"debug":str(debug.relative_to(W)),"runtime_sha256":sha(runtime),"debug_sha256":sha(debug),"build_id":ids[0],"debug_build_id":ids[1],"match":True})
commands=[]
for line in log.splitlines():
 if re.search(r"\bclang\s",line) and " -c " in line and "libav" in line:
  commands.append(line)
assert commands,"No actual clang compilation commands in log"
for flag in ["-fdebug-info-for-profiling","-funique-internal-linkage-names"]:
 assert any(flag in line for line in commands),flag
isa="-mthumb" if variant=="thumb" else "-marm"
checked=[line for line in commands if all(f in line for f in ["-fdebug-info-for-profiling","-funique-internal-linkage-names"])]
assert checked and all(re.findall(r"-m(?:thumb|arm)\b",line)[-1]==isa for line in checked),isa
(out/"compile-excerpts.txt").write_text("\n".join(checked[:10])+"\n")
report={"variant":variant,"libraries":libs,"rpm_count":len(outputs),"dependency_count":len(deps),"clang_dependencies":[x for x in deps if x["name"]=="clang"],"actual_compile_command_count":len(commands),"profiling_flag_command_count":len(checked),"effective_isa":isa,"all_checked_isa_match":True,"archive_bytes":sum(x["size_bytes"] for x in archived)}
(out/"artifact-check.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
