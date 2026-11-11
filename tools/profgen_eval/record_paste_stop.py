"""Preserve supplement3 stopping assertions and source excerpts (static only)."""
from pathlib import Path
import json,hashlib,subprocess
from run_scoped import WORK,sha
OUT=WORK/"docs/profgen/eval/prep/evidence/ruling2/supplement3"


def main():
    p=OUT/"compiler-source.txt";text=p.read_text()
    for name,a,b in [("clang/lib/Basic/SourceManager.cpp",984,997),
                     ("clang/include/clang/Lex/MacroArgs.h",76,86),
                     ("clang/lib/Lex/TokenLexer.cpp",1050,1058),
                     ("clang/lib/Lex/TokenLexer.cpp",1080,1097)]:
        path=WORK/"temp/llvm-profgen-enh"/name;lines=path.read_text().splitlines()
        text+=f"\n{name} SHA-256 {sha(path)}\n"
        text+="\n".join(f"{i}: {lines[i-1]}" for i in range(a,b+1))+"\n"
    p.write_text(text)
    examples=[]
    for n in (18,7,33):
        p=OUT/f"ffmpeg-thumb-{n:02d}-paste-proof.json";r=json.loads(p.read_text())
        lines=[f"# {r['name']}",f"Source JSON: {p.relative_to(WORK)}; SHA-256 {sha(p)}",
               "API evidence only. This record remains unresolved under supplement3 rule7.",""]
        def render(pr):
            x=pr.get("X",{})
            lines.append(f"depth={pr['depth']} text={pr['token']['text']} X={x.get('name')} invocation_raw={x.get('name_location',{}).get('raw')}")
            lines.append(f"passed={pr['steps_passed']}; reasons={pr['reason_codes']}")
            lines.append("definition fragment: "+" ".join(t["text"] for t in pr.get("definition_tokens",[])))
            lines.append("text comparison: "+json.dumps(pr.get("concatenation",{})))
            for op in pr["operands"]:
                t=op["token"];sp=t["spelling"]
                lines.append(f"  {op['kind']} param={op['parameter_num']} text={t['text']} "
                             f"spelling={sp['presumed_file']}:{sp['line']}:{sp['column']} raw={t['location']['raw']} "
                             f"is_macro={t['location']['is_macro']} isMacroArgExpansion={t['isMacroArgExpansion']} "
                             f"source_valid={op.get('source_valid')} in_allowed_range={op.get('in_allowed_argument_or_definition_range')}")
                if "subproof" in op:render(op["subproof"])
        render(r["proofs"][0])
        dest=OUT/f"example-{n:02d}-proof.txt";dest.write_text("\n".join(lines)+"\n")
        examples.append(dict(path=str(p.relative_to(WORK)),sha256=sha(p),fn=r["name"],expected="all proofs pass",
                             actual=[pr["status"] for pr in r["proofs"]],
                             result="FAIL" if any(pr["status"]!="proved" for pr in r["proofs"]) else "PASS"))
    (OUT/"real-example-assertions.json").write_text(json.dumps(examples,indent=2)+"\n")
    print(json.dumps(examples,indent=2))
    # Explicitly nonzero: do not relabel the required passing cases as successful tests.
    return 1 if any(r["result"]=="FAIL" for r in examples[:2]) else 0


if __name__=="__main__":raise SystemExit(main())
