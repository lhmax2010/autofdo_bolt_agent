"""Recheck ruling1 using actual compile logs and the installed GBS compiler.

Only preprocess an empty source. Build paths are relocated into the retained
root; normalized search directories are reported in their original root view.
"""
import csv
import hashlib
import json
import re
import shlex
import subprocess
from pathlib import Path
from run_scoped import WORK, run, sha
from system_header_rule import validate_global_files

OUT=WORK/"docs/profgen/eval/prep/evidence/ruling1"
EVIDENCE=OUT.parent
MANIFEST=WORK/"docs/profgen/impl/evidence/11/08_artifacts.json"

def compile_commands(log):
    rows=[]
    for number,line in enumerate(log.read_text().splitlines(),1):
        text=re.sub(r"^\[\s*\d+s\]\s*","",line).removeprefix("+ ")
        if not re.match(r"(?:\S*/)?(?:armv7l-tizen-linux-gnueabi-)?clang(?:\+\+)?\s",text):
            continue
        args=shlex.split(text)
        sources=[a for a in args[1:] if a.endswith((".c",".cc",".cpp")) and not a.startswith("-")]
        if not sources:
            continue
        if any(a.startswith("@") for a in args):
            raise ValueError("compile response file must be inspected: "+text)
        rows.append(dict(line=number,text=text,args=args,sources=sources))
    if not rows:
        raise ValueError("no actual compile commands: "+str(log))
    return rows

def search_options(args):
    keys=["-isystem","-idirafter","-isysroot","--sysroot","-resource-dir",
          "--target","-target","-nostdinc","-nostdlibinc","-nobuiltininc"]
    result=[]
    i=1
    while i<len(args):
        a=args[i]
        if a in keys:
            result.append(a)
            if a not in ["-nostdinc","-nostdlibinc","-nobuiltininc"]:
                i+=1;result.append(args[i])
        elif any(a.startswith(k+"=") for k in keys) or a.startswith("-isystem"):
            result.append(a)
        i+=1
    return result

def read_files(obj):
    table=EVIDENCE/(obj+"-coverage-tables")
    files=[]
    for p in sorted(table.glob("files-*.csv")):
        with p.open() as f: files.extend(r["file"] for r in csv.DictReader(f))
    return files

def main():
    artifacts={x["id"]:x for x in json.loads(MANIFEST.read_text())}
    result={}
    for obj in ["spike-thumb","spike-a32","ffmpeg-thumb","ffmpeg-a32"]:
        side={}
        root=WORK/"temp"/("GBS-ROOT-V04-FFMPEG" if obj.startswith("ffmpeg") else "GBS-ROOT-RPI4-SPIKE")/"local/BUILD-ROOTS/scratch.armv7l.0"
        emul=root/"emul"
        cfg=root/"usr/bin/clang.cfg"
        config=cfg.read_text()
        if shlex.split(config)!=["-target","armv7l-tizen-linux-gnueabi","-resource-dir","/usr/lib/clang/22"]:
            raise ValueError("unhandled compiler config; do not infer defaults")
        for stage in ["S","C"]:
            row=artifacts[obj+"-"+stage];log=Path(row["log_path"])
            commands=compile_commands(log)
            signatures={tuple(search_options(r["args"])) for r in commands}
            # Actual logs currently have no system-search overrides. Refuse to
            # drop a newly discovered option while probing default directories.
            if signatures!={()}:
                raise ValueError("nonempty include-search overrides: "+repr(signatures))
            coverage_tokens=[r for r in commands if any("system-headers-coverage" in a for a in r["args"])]
            if coverage_tokens:
                raise ValueError("explicit system coverage option needs interpretation")
            label="ruling1-headers-"+obj+"-"+stage
            command=[str(emul/"lib64/ld-linux-x86-64.so.2"),"--library-path",
                     str(emul/"lib64")+":"+str(emul/"usr/lib64"),
                     str(emul/"usr/bin/clang"),"--no-default-config",
                     "--target=armv7l-tizen-linux-gnueabi",
                     "--sysroot="+str(root),"-resource-dir="+str(root/"usr/lib/clang/22"),
                     "-mthumb" if "thumb" in obj else "-marm","-E","-v","-x","c",str(OUT/"empty.c")]
            if run(label,command):
                raise RuntimeError("clang -v failed")
            stderr=(EVIDENCE/label/"stderr.txt").read_text()
            lines=stderr.split("#include <...> search starts here:\n")[1].split("End of search list.")[0].splitlines()
            physical=[s.strip() for s in lines if s.strip()]
            if any(not s.startswith(str(root)+"/") for s in physical):
                raise ValueError("search directory escaped retained buildroot")
            logical=[s[len(str(root)):] for s in physical]
            if "clang version 22.1.8" not in stderr:
                raise ValueError("compiler version changed")
            cfg_data=dict(path=str(cfg),sha256=sha(cfg),content=config)
            out=OUT/(obj+"-"+stage+"-commands.json")
            out.write_text(json.dumps({"log":str(log),"log_sha256":sha(log),
                "compiler_config":cfg_data,"compiler_sha256":sha(emul/"usr/bin/clang-22"),
                "compile_commands":commands,"search_option_signatures":[list(s) for s in signatures],
                "relocation":"explicit sysroot/root-resource-dir reproduce buildroot / view; no host include paths",
                "clang_v":str(EVIDENCE/label/"stderr.txt"),
                "logical_system_dirs":logical,"physical_system_dirs":physical},indent=2)+"\n")
            side[stage]=dict(dirs=logical,command_evidence=str(out),sources=sorted({s for c in commands for s in c["sources"]}),
                             compiler_sha256=sha(emul/"usr/bin/clang-22"))
        same=side["S"]["dirs"]==side["C"]["dirs"]
        files=read_files(obj)
        validate_global_files(files,side["S"]["dirs"])
        result[obj]={"sides":side,"equal_dirs":same,"coverage_file_count":len(files),
                     "global_system_file_violations":[],"global_coverage_file_check_passed":True,
                     "skip_source":"src/llvm/clang/lib/CodeGen/CoverageMappingGen.cpp:49-52,1575-1579"}
    (OUT/"header-evidence.json").write_text(json.dumps(result,indent=2)+"\n")

if __name__=="__main__":
    main()
