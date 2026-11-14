from pathlib import Path
import subprocess,json,hashlib,re,collections,sys
R=Path(__file__).resolve().parent;W=R.parents[2];v=sys.argv[1]
attempts=[r for r in json.loads((R/"results.json").read_text()) if r["variant"]==v and not r.get("resource_stop")]
assert len(attempts)==1;record=attempts[0];assert record["gbs_exit"]==0
out=R/(v+"-attempt-"+str(record["attempt"]));root=Path(record["buildroot"])
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
rpms=[]
for p in sorted((root/"local/repos").rglob("*.rpm")):
 q=subprocess.run(["rpm","-qp","--qf","%{NAME}\\t%{VERSION}\\t%{RELEASE}\\t%{ARCH}",str(p)],capture_output=True,text=True)
 assert q.returncode==0,q.stderr
 n,ver,rel,arch=q.stdout.split("\t")
 rpms.append(dict(path=str(p.relative_to(W)),name=n,version=ver,release=rel,arch=arch,bytes=p.stat().st_size,sha256=sha(p)))
(out/"rpms.json").write_text(json.dumps(rpms,indent=2)+"\n")
X=out/"extracted";X.mkdir()
needed=[]
for n in ["libavcodec","libavutil","libavcodec-debuginfo","libavutil-debuginfo"]:
 matches=[r for r in rpms if r["name"]==n and r["arch"]=="armv7l"];assert len(matches)==1,(n,matches)
 needed.append(matches[0])
for r in needed:
 with (out/(r["name"]+"-extract.log")).open("wb") as log:
  p=subprocess.Popen(["rpm2cpio",str(W/r["path"])],stdout=subprocess.PIPE,stderr=log)
  q=subprocess.run(["cpio","-idm","--no-absolute-filenames"],cwd=X,stdin=p.stdout,stdout=log,stderr=log)
  p.stdout.close();rc=p.wait();assert q.returncode==rc==0
libs=[]
for n in ["libavcodec","libavutil"]:
 matches=[p for p in (X/"usr/lib").glob(n+".so.*") if p.is_file() and not p.is_symlink()]
 assert len(matches)==1,matches
 runtime=matches[0];debug=X/"usr/lib/debug"/runtime.relative_to(X);debug=debug.with_name(debug.name+".debug")
 assert debug.exists(),debug
 ids=[]
 for label,p in [("runtime",runtime),("debug",debug)]:
  q=subprocess.run(["readelf","-n",str(p)],capture_output=True,text=True)
  (out/(n+"-"+label+"-notes.txt")).write_text(q.stdout+q.stderr)
  assert q.returncode==0
  bid=re.findall(r"Build ID: ([0-9a-f]+)",q.stdout);assert len(bid)==1 and len(bid[0])==40
  ids.append(bid[0])
 assert ids[0]==ids[1]
 q=subprocess.run(["readelf","-SW",str(debug)],capture_output=True,text=True)
 (out/(n+"-sections.txt")).write_text(q.stdout+q.stderr)
 assert q.returncode==0 and ".debug_info" in q.stdout and ".debug_line " in q.stdout
 streams={}
 for kind in ["info","rawline"]:
  cmd=["readelf","--debug-dump="+kind,str(debug)];h=hashlib.sha256();total=0;counts=collections.Counter();excerpt=[]
  with (out/(n+"-"+kind+".stderr")).open("wb") as err:
   p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=err)
   for line in p.stdout:
    h.update(line);total+=len(line);s=line.decode(errors="replace")
    if len(excerpt)<40:excerpt.append(s)
    m=re.match(r"\s*Version:\s+(\d+)",s)
    if m:counts[m[1]]+=1
   rc=p.wait()
  (out/(n+"-"+kind+"-excerpt.txt")).write_text("".join(excerpt))
  assert rc==0 and total>0
  if kind=="info":assert counts
  streams[kind]=dict(command=cmd,exit=rc,output_bytes=total,output_sha256=h.hexdigest(),CU_versions=dict(counts))
 libs.append(dict(name=n,runtime=str(runtime.relative_to(W)),debug=str(debug.relative_to(W)),
  runtime_sha256=sha(runtime),debug_sha256=sha(debug),build_id=ids[0],debug_build_id=ids[1],build_id_match=True,dwarf=streams))
lines=(out/"build.log").read_text(errors="replace").splitlines()
diagnostics=[dict(line=i+1,text=l) for i,l in enumerate(lines) if "DWARF version 5 unhandled" in l or "Unknown debugging section .debug_line_str" in l]
files=sorted(set(re.findall(r"(/home/abuild/\S+?): (?:DWARF|Unknown debugging)", "\n".join(x["text"] for x in diagnostics))))
res=dict(variant=v,rpms=len(rpms),libraries=libs,diagnostic_count=len(diagnostics),diagnostic_files=files,diagnostics=diagnostics,
 profgen_load_only="skipped: CLI has no verified standalone read-only ELF+DWARF load command; no synthetic sample conversion was added")
(out/"artifact-validation.json").write_text(json.dumps(res,indent=2)+"\n")
print(json.dumps(res,indent=2))
