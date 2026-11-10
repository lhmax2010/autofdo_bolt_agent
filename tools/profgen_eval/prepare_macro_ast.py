"""C-build AST evidence using recorded flags, build config and debugsource RPM."""
import hashlib,json,subprocess,sys,re
from pathlib import Path
from run_scoped import WORK,sha
from recheck_header_evidence import command_record

OUT=WORK/"docs/profgen/eval/prep/evidence/ruling2"
TEMP=WORK/"temp/prep-ruling2"

def main():
    mode=sys.argv[1]
    dest=TEMP/("headers4-"+mode);dest.mkdir(parents=True,exist_ok=False)
    pkg=next((WORK/"temp/eval-prep11/build"/("ffmpeg-"+mode+"-C")).glob("libavutil-devel-*.rpm"))
    a=subprocess.Popen(["rpm2cpio",str(pkg)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    b=subprocess.run(["cpio","-idm","--no-absolute-filenames"],stdin=a.stdout,cwd=dest,capture_output=True)
    a.stdout.close();err=a.stderr.read();rc=a.wait()
    if rc or b.returncode: raise RuntimeError((rc,err,b.stderr))
    src=WORK/"temp/eval-prep11/ffmpeg"
    root=WORK/"temp/GBS-ROOT-V04-FFMPEG/local/BUILD-ROOTS/scratch.armv7l.0"
    emul=root/"emul"
    driver=[str(emul/"lib64/ld-linux-x86-64.so.2"),"--library-path",str(emul/"lib64")+":"+str(emul/"usr/lib64"),str(emul/"usr/bin/clang"),"--no-default-config","--target=armv7l-tizen-linux-gnueabi","--sysroot="+str(root),"-resource-dir="+str(root/"usr/lib/clang/22")]
    cr=command_record(WORK/("docs/profgen/eval/prep/evidence/ruling1/ffmpeg-"+mode+"-C-commands.json"))
    configs=WORK/"temp/eval-prep11/build"/("ffmpeg-"+mode+"-C")
    print("source",src,"config",configs,"generated avconfig",dest/"usr/include/libavutil/avconfig.h")
    assert (dest/"usr/include/libavutil/avconfig.h").exists()
    generated=WORK/"temp/eval-prep11/configure"/mode
    components=(generated/"config_components.h").read_text()
    mak=(configs/"config.mak").read_text().splitlines()
    checks=[]
    for name,value in re.findall(r"^#define (CONFIG_\w+) ([01])$",components,re.M):
        expected=("" if value=="1" else "!")+name+"=yes"
        checks.append({"macro":name,"value":int(value),"config_mak_line":mak.index(expected)+1})
    (OUT/(mode+"-config-components.json")).write_text(json.dumps({"components_path":str(generated/"config_components.h"),"sha256":sha(generated/"config_components.h"),"actual_build_mak":str(configs/"config.mak"),"mak_sha256":sha(configs/"config.mak"),"checks":checks},indent=2)+"\n")
    results=[]
    for tu in ["libavcodec/arm/hpeldsp_init_arm.c","libavcodec/h264qpel.c","libavcodec/hpeldsp.c","libavcodec/qpeldsp.c","libavcodec/rv40dsp.c"]:
        cmd=next(c for c in cr["compile_commands"] if c["sources"]==[tu])
        args=["-I"+str(configs)];it=iter(cmd["args"][1:])
        for arg in it:
            if arg in ["-o","-MF","-MT"]: next(it);continue
            if arg in ["-MMD","-c"]: continue
            args.append(arg)
        args+= ["-I"+str(generated),"-I"+str(dest/"usr/include"),"-fsyntax-only","-Xclang","-ast-dump=json","-Xclang","-ast-dump-filter","-Xclang","pixels16"]
        out=TEMP/(mode+"-"+Path(tu).stem+".ast4.json")
        with out.open("w") as f:
            proc=subprocess.run(driver+args,cwd=src,stdout=f,stderr=subprocess.PIPE,text=True)
        stderr=OUT/(mode+"-"+Path(tu).stem+".stderr4.txt");stderr.write_text(proc.stderr)
        results.append(dict(tu=tu,original_log=cr["log"],original_log_sha256=cr["log_sha256"],original_line=cmd["line"],original_command=cmd["args"],command=driver+args,cwd=str(src),ast=str(out),ast_sha256=sha(out),stderr=str(stderr),exit_code=proc.returncode,source_sha256=sha(src/tu),config_sha256=sha(configs/"config.h"),generated_header_rpm=str(pkg),generated_header_rpm_sha256=sha(pkg),compiler_sha256=sha(emul/"usr/bin/clang-22")))
        (OUT/(mode+"-ast4-commands.json")).write_text(json.dumps(results,indent=2)+"\n")
        if proc.returncode: raise RuntimeError(proc.stderr)
    print("AST_DONE",mode)

if __name__=="__main__":main()
