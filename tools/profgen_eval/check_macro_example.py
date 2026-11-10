"""Keep compiler evidence for the first ruling2 macro; do not infer identity."""
import json, subprocess
from pathlib import Path
from run_scoped import sha

BASE=Path("docs/profgen/eval/prep/evidence/ruling2")

def main():
    r=json.loads((BASE/"thumb-ast4-commands.json").read_text())[0]
    original=r["command"]
    start=original.index("-Xclang")
    base=original[:start]
    commands=[]
    for label,args in [("ast-text",["-Xclang","-ast-dump","-Xclang","-ast-dump-filter","-Xclang","ff_put_pixels16_x2_arm"]),
                       ("tokens",["-Xclang","-dump-tokens"])]:
        p=subprocess.run(base+args,cwd=r["cwd"],capture_output=True,text=True)
        for stream in ("stdout","stderr"):
            out=Path("temp/prep-ruling2")/(label+"."+stream)
            out.write_text(getattr(p,stream))
        commands.append(dict(command=base+args,cwd=r["cwd"],exit_code=p.returncode,
                             stdout_sha256=sha(Path("temp/prep-ruling2")/(label+".stdout")),
                             stderr_sha256=sha(Path("temp/prep-ruling2")/(label+".stderr"))))
        if p.returncode: raise RuntimeError(p.stderr)
    (BASE/"macro-example-commands.json").write_text(json.dumps(commands,indent=2)+"\n")
    raw=Path("temp/prep-ruling2/ast-text.stdout").read_text()
    (BASE/"macro-example-ast.txt").write_text(raw)
    raw=Path("temp/prep-ruling2/tokens.stderr").read_text().splitlines()
    (BASE/"macro-example-tokens.txt").write_text("\n".join(f"{i}: {s}" for i,s in enumerate(raw,1) if "hpeldsp_init_arm.c:38:" in s)+"\n")
    print((BASE/"macro-example-ast.txt").read_text())

if __name__=="__main__":main()
