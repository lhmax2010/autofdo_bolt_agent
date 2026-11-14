from pathlib import Path
import configparser,hashlib,json,subprocess,os
W=Path.cwd();D=W/"temp/hq-revision-20261114-work";H=W/"temp/hq-revised-20261114"
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
template=H/"examples/gbs/llvm-release.conf.in";actual=W/"temp/gbs/gbs_llvm_x86_release.conf"
configs=[]
for p in [actual,template]:
 c=configparser.ConfigParser(interpolation=None);c.read(p)
 configs.append({s:dict(c[s]) for s in c.sections()})
original_a=json.loads(json.dumps(configs[0]));original_b=json.loads(json.dumps(configs[1]))
path_differences=[]
for key in ["tmpdir","buildroot"]:
 path_differences.append({"section":"general","field":key,"actual":configs[0]["general"][key],"template":configs[1]["general"][key]})
 for c in configs:c["general"][key]="<filesystem path>"
assert configs[0]==configs[1], (configs[0],configs[1])
r={"actual":str(actual.relative_to(W)),"actual_sha256":sha(actual),"template_sha256":sha(template),"all_fields_equal_except_paths":True,"omitted_fields":[],"path_differences":path_differences}
(D/"configuration-equivalence.json").write_text(json.dumps(r,indent=2)+"\n")
tree=W/"temp/llvm-profgen-sandbox-verify-20261114"
git=["git","-c","gc.auto=0","-c","maintenance.auto=false","-C",str(tree)]
head=subprocess.check_output(git+["rev-parse","HEAD"],text=True).strip()
assert head=="c8942ae1b53099a78a97dca2b64427af6e58432b"
log=subprocess.check_output(git+["log","--reverse","--format=%H %s","f999bd406c0a70fe8107aa992164fe6945c5d46a..HEAD"],text=True)
assert len(log.splitlines())==9
rc=subprocess.run(git+["diff","--exit-code","f999bd406c0a70fe8107aa992164fe6945c5d46a","--","packaging/llvm.spec"],check=False).returncode
assert rc==0
(D/"source-verification.json").write_text(json.dumps({"head":head,"commits":log.splitlines(),"spec_diff_exit":rc,"network_clone_repeated":False},indent=2)+"\n")
expected="67ad21faba787d276a80673c1f324f7c0591d28d76bd37a8bd57de0d86426be6"
assert sha(D/"extracted/usr/bin/llvm-profgen")==expected
for name in ["a64-pie","thumb-count"]:
 r=json.loads((D/f"demo-output/{name}.quality.json").read_text())
 assert r["verdict"]["conversion"]=="ok" and r["verdict"]["identity"]=="unverified"
 assert r["verdict"]["sampling_adequacy"]=="unknown"
 assert r["samples"]["target"]["counts"]["sample_count"]==1
 assert r["samples"]["target"]["usable"]["sample_count"]==1
 assert r["samples"]["written_positions"]==1
 assert (D/f"demo-output/{name}.show.txt").read_text()=="Function: main: 1, 0, 1 sampled lines\nSamples collected in the function's body {\n  0: 1\n}\nNo inlined callsites in this function\n"
 results={"verdict":r["verdict"],"samples":r["samples"]}
 (D/f"{name}-expected-objects.json").write_text(json.dumps(results,indent=2)+"\n")
inventory=[{"path":p.relative_to(H).as_posix(),"size_bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted(H.rglob("*")) if p.is_file() and ".git" not in p.relative_to(H).parts]
(D/"hq-files.json").write_text(json.dumps({"files":inventory,"total_bytes":sum(p["size_bytes"] for p in inventory)},indent=2)+"\n")
print("Config fields equal except paths; no omissions. Source HEAD/spec pass. Tool SHA and demo expectations pass.")
