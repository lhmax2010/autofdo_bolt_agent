"""Package static token evidence and source citations; no sample inputs."""
import csv,json,subprocess
from pathlib import Path
from run_scoped import WORK,sha
BASE=WORK/"docs/profgen/eval/prep/evidence"
OUT=BASE/"ruling2/supplement2"


def main():
    excerpts=[]
    for file, spans in [
        ("src/llvm/clang/lib/Lex/TokenLexer.cpp",[(731,741),(786,836),(870,892)]),
        ("src/llvm/clang/lib/Lex/Preprocessor.cpp",[(236,261),(486,504)]),
        ("src/llvm/clang/include/clang/Lex/Preprocessor.h",[(1352,1363)]),
        ("src/llvm/clang/lib/AST/JSONNodeDumper.cpp",[(313,328)]),
        ("src/llvm/clang/lib/Frontend/FrontendAction.cpp",[(175,245)]),
    ]:
        lines=(WORK/file).read_text().splitlines()
        excerpts.append(f"{file} SHA-256 {sha(WORK/file)}")
        for start,end in spans:
            excerpts.extend(f"{i}: {lines[i-1]}" for i in range(start,end+1))
    (OUT/"compiler-source.txt").write_text("\n".join(excerpts)+"\n")
    for n in (1,7,18):
        path=OUT/f"ffmpeg-thumb-{n:02d}-tokens.json";r=json.loads(path.read_text())
        chain=r["identity_record"]["compiler_ast_chain"]
        with (OUT/f"example-{n:02d}-all-body-tokens.tsv").open("w") as f:
            writer=csv.writer(f,delimiter="\t",lineterminator="\n")
            writer.writerow(["index","raw_jsonl_line","kind","text","spelling","spelling_offset",
                             "expansion","isMacroArgExpansion","macro_trace","allowed_regions"])
            for i,t in enumerate(chain["tokens"],1):
                s,e=t["spelling"],t["expansion"]
                writer.writerow([i,t["_raw_line"],t["kind"],t["text"],
                                 f'{s["presumed_file"]}:{s["line"]}:{s["column"]}',s["offset"],
                                 f'{e["file"]}:{e["line"]}:{e["column"]}',t["isMacroArgExpansion"],
                                 " -> ".join(x["macro"] for x in t["trace"]),json.dumps(t["allowed_spelling_regions"])])
    versions=[]
    command=json.loads((BASE/"ruling2/thumb-token-api-commands.json").read_text())[0]["command"]
    cmd=command[:command.index("--no-default-config")]+["--version"]
    p=subprocess.run(cmd,capture_output=True,text=True)
    versions.append(dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
    (OUT/"compiler-version.json").write_text(json.dumps(versions,indent=2)+"\n")
    if p.returncode:raise RuntimeError("compiler version failed")
    # Verify raw AST/token inputs, including failed attempt preservation.
    for mode in ("thumb","a32"):
        for item in json.loads((BASE/f"ruling2/{mode}-token-api-commands.json").read_text()):
            for k in ("output","stderr"):
                if sha(Path(item[k]))!=item[k+"_sha256"]:raise ValueError(item[k])
    p=BASE/"ruling2/thumb-token-api-attempt1-commands.json";r=json.loads(p.read_text())
    for item in r:
        for k in ("output","stderr"):
            old=Path(item[k]);new=old.with_name("attempt1-"+old.name)
            item["preserved_"+k]=str(new)
            if sha(new)!=item[k+"_sha256"]:raise ValueError("preserved failed evidence mismatch")
    p.write_text(json.dumps(r,indent=2)+"\n")
    print("Raw token/compiler evidence SHA checks passed; examples include every body token.")


def manifest():
    inputs=[]
    for mode in ("thumb","a32"):
        for item in json.loads((BASE/f"ruling2/{mode}-token-api-commands.json").read_text()):
            for key in ("output","stderr"):
                inputs.append(dict(path=item[key],sha256=sha(Path(item[key])),size=Path(item[key]).stat().st_size))
    files=[]
    directories=[OUT]+[d for d in BASE.iterdir() if d.is_dir() and
                       (d.name.startswith("ruling2-token-") or d.name.startswith("ruling2-supp2-"))]
    paths=set()
    for directory in directories:
        paths.update(f for f in directory.rglob("*") if f.is_file() and f.name!="artifact-manifest.json")
    paths.update(BASE/"ruling2"/n for n in ["token-plugin-build.json","thumb-token-api-commands.json",
                                         "a32-token-api-commands.json","thumb-token-api-attempt1-commands.json"])
    for path in sorted(paths):
        if path.stat().st_size>=1_000_000:raise ValueError(("oversize",str(path)))
        files.append(dict(path=str(path.relative_to(WORK)),sha256=sha(path),size=path.stat().st_size))
    commands=["python3 tools/profgen_eval/compiler_token_evidence.py build",
              "python3 tools/profgen_eval/compiler_token_evidence.py thumb",
              "python3 tools/profgen_eval/compiler_token_evidence.py a32",
              "python3 tools/profgen_eval/audit_macro_tokens.py",
              "python3 -m unittest discover -s tools/profgen_eval -p test_macro_function_rule.py -v",
              "python3 tools/profgen_eval/package_token_evidence.py",
              "python3 tools/profgen_eval/package_token_evidence.py --manifest-only"]
    (OUT/"artifact-manifest.json").write_text(json.dumps(dict(
        files=files,raw_token_inputs=inputs,commands=commands,
        execution="nice -n 19 ionice -c3; systemd-run --user --scope MemoryMax=3G CPUQuota=200%; see per-task command.json",
        file_generation={"*-tokens.json / *-results.json / *-inventory / closure-summary.json":"audit_macro_tokens.py",
                         "example-*.tsv / compiler-source.txt / compiler-version.json":"package_token_evidence.py",
                         "raw token JSONL":"compiler_token_evidence.py",
                         "task evidence directories":"run_scoped.py"},no_sample_profile_inputs=True),indent=2)+"\n")
    print("Manifest",len(files),"files; each below 1 MB; raw token paths SHA-recorded.")


if __name__=="__main__":
    import sys
    manifest() if "--manifest-only" in sys.argv else main()

