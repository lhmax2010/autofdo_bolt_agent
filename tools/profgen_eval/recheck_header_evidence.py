"""Derive per-side flags from retained raw command/probe/source evidence."""
import hashlib
import json
from pathlib import Path
from system_header_rule import normalized_dirs

BASE = Path("docs/profgen/eval/prep/evidence")
OUT = BASE / "ruling1"

def digest(data):
    return hashlib.sha256(data).hexdigest()

def command_record(path):
    path = Path(path)
    if path.exists():
        return json.loads(path.read_text())
    index = json.loads(Path(str(path)+".parts.json").read_text())
    chunks = []
    for part in index["parts"]:
        raw = Path(part["path"]).read_bytes()
        assert digest(raw) == part["sha256"]
        chunks.append(raw)
    raw = b"".join(chunks)
    assert digest(raw) == index["sha256"]
    return json.loads(raw)

def main():
    path = OUT / "header-evidence.json"
    evidence = json.loads(path.read_text())
    source = Path("src/llvm/clang/lib/CodeGen/CoverageMappingGen.cpp")
    lines = source.read_text().splitlines()
    skip = ("cl::init(false)" in "\n".join(lines[48:52]) and
            "if (!SystemHeadersCoverage && Body &&" in "\n".join(lines[1574:1579]) and
            "SM.isInSystemHeader" in "\n".join(lines[1574:1579]) and
            "return;" in "\n".join(lines[1574:1579]))
    for obj, record in evidence.items():
        for stage, side in record["sides"].items():
            cmd = command_record(side["command_evidence"])
            probe = BASE / ("ruling1-headers-"+obj+"-"+stage)
            result = json.loads((probe/"result.json").read_text())
            stderr = (probe/"stderr.txt").read_bytes()
            root = next(a.split("=",1)[1] for a in result["command"] if a.startswith("--sysroot="))
            search = stderr.decode().split("#include <...> search starts here:\n")[1].split("End of search list.")[0]
            dirs = [s.strip() for s in search.splitlines() if s.strip()]
            side["clang_v_verified"] = (result.get("exit_code") == 0 and
                digest(stderr) == result.get("stderr.txt_sha256") and
                "clang version 22.1.8" in stderr.decode() and
                all(s.startswith(root+"/") for s in dirs) and
                normalized_dirs([s[len(root):] for s in dirs]) == normalized_dirs(side["dirs"]) and
                cmd["compiler_sha256"] == side["compiler_sha256"])
            commands = cmd.get("compile_commands", [])
            side["coverage_disabled_verified"] = (bool(commands) and
                all(not any("system-headers-coverage" in a for a in c["args"]) for c in commands) and
                "system-headers-coverage" not in cmd["compiler_config"]["content"])
            side["skip_source_verified"] = skip
            side["verification_sources"] = {"probe_result":str(probe/"result.json"),
                "probe_stderr_sha256":digest(stderr), "compiler_commands":side["command_evidence"],
                "skip_source":str(source)+":49-52,1575-1579", "skip_source_sha256":digest(source.read_bytes())}
    path.write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps({o:{s:{k:v for k,v in e.items() if k.endswith("_verified")} for s,e in r["sides"].items()} for o,r in evidence.items()},indent=2))

if __name__ == "__main__":
    main()
