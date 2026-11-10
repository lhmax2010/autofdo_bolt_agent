"""Inspect retained libgcc members and S-link driver's default archive search."""
import collections,json,re,subprocess
from pathlib import Path
from run_scoped import WORK,platform,sha
from dwarf_inventory import parse,inventory,text
from apply_header_ruling import rows

OUT=WORK/"docs/profgen/eval/prep/evidence/ruling2"
TEMP=WORK/"temp/prep-ruling2/libgcc"
ROOT=WORK/"temp/GBS-ROOT-V04-FFMPEG/local/BUILD-ROOTS/scratch.armv7l.0"

def checked(command):
    p=subprocess.run(command,capture_output=True,text=True)
    if p.returncode:raise RuntimeError((command,p.returncode,p.stderr))
    return p

def main():
    TEMP.mkdir(parents=True,exist_ok=False)
    archive=ROOT/"usr/lib/gcc/armv7l-tizen-linux-gnueabi/14.2.0/libgcc.a"
    members=checked(platform("llvm-ar")+["t",str(archive)])
    (OUT/"libgcc-members.txt").write_text(members.stdout)
    nm=checked(platform("llvm-nm")+["-A","--defined-only",str(archive)])
    (TEMP/"nm.txt").write_text(nm.stdout)
    member_names=members.stdout.splitlines()
    objects={}; matches={}
    needed=set()
    for obj in ("ffmpeg-thumb","ffmpeg-a32"):
        a=json.loads((OUT.parent/"ruling1"/(obj+"-conclusions")/"blocking-no-candidate.json").read_text())
        objects[obj]=[r for r in a if r["category"]=="external_cu_source_evidence_pending"]
        for r in objects[obj]:
            for line in nm.stdout.splitlines():
                if line.split()[-1:]==[r["raw_name"]]:
                    for member in member_names:
                        if ":"+member+":" in line:
                            needed.add(member)
                            matches.setdefault(r["raw_name"],set()).add(member)
    member_records={}
    for member in sorted(needed):
        raw=subprocess.run(platform("llvm-ar")+["p",str(archive),member],capture_output=True)
        if raw.returncode:raise RuntimeError(raw.stderr)
        path=TEMP/member;path.write_bytes(raw.stdout)
        dump=checked(platform("llvm-dwarfdump")+["--debug-info",str(path)])
        (TEMP/(member+".dwarf.txt")).write_text(dump.stdout)
        records=parse(dump.stdout.splitlines(True));inv=inventory(records)
        member_records[member]={"sha256":sha(path),"path":str(path),"dump_sha256":sha(TEMP/(member+".dwarf.txt")),
                                "compile_units":inv["compile_units"],"functions":inv["code_dies"]}
    result={}
    for obj,records in objects.items():
        result[obj]=[]
        for r in records:
            candidates=[]
            for member in sorted(matches.get(r["raw_name"],[])):
                inv=member_records[member]
                for f in inv["functions"]:
                    if f["name"]==r["raw_name"] and f["cu_name"]==r["cu_name"] and f["producer"]==r["producer"]:
                        candidates.append({"member":member,"member_sha256":inv["sha256"],"source":f["cu_name"],"producer":f["producer"],"member_die":f["die"],"member_dump":str(TEMP/(member+".dwarf.txt"))})
            result[obj].append({"die":r["die"],"cu":r["cu"],"name":r["raw_name"],"candidates":candidates,
                                "member_match_unique":len(candidates)==1})
    emul=ROOT/"emul"
    driver=[str(emul/"lib64/ld-linux-x86-64.so.2"),"--library-path",str(emul/"lib64")+":"+str(emul/"usr/lib64"),str(emul/"usr/bin/clang"),"--no-default-config","--target=armv7l-tizen-linux-gnueabi","--sysroot="+str(ROOT),"-resource-dir="+str(ROOT/"usr/lib/clang/22")]
    selected=checked(driver+["-print-libgcc-file-name"])
    (OUT/"libgcc-driver-path.txt").write_text(selected.stdout+selected.stderr)
    (OUT/"external-cu-members.json").write_text(json.dumps({"archive":str(archive),"archive_sha256":sha(archive),"ar_command":platform("llvm-ar")+["t",str(archive)],"nm_command":platform("llvm-nm")+["-A","--defined-only",str(archive)],"driver_command":driver+["-print-libgcc-file-name"],"driver_result":selected.stdout,"members":member_records,"matches":result},indent=2)+"\n")
    print({o:{"total":len(v),"unique_member":sum(r["member_match_unique"] for r in v)} for o,v in result.items()})

if __name__=="__main__":main()
