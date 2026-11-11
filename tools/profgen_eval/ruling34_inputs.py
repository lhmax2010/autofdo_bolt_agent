"""Rulings 3/4: isolated static input and actual-command evidence."""
import collections,json,sys
from pathlib import Path
from run_scoped import WORK,sha
from static_gate_data import BASE,OBJECTS,dump
from recheck_header_evidence import command_record
from pack_static_evidence import tables
OUT=BASE/"identity-gate/ruling3-4"
TEMP=WORK/"temp/prep-ruling3-4"

def main():
    result=[]
    for obj in OBJECTS:
        for stage in ("S","C"):
            p=BASE/"ruling1"/(obj+"-"+stage+"-commands.json")
            cmd=command_record(p)
            log=Path(cmd["log"])
            assert sha(log)==cmd["log_sha256"],log
            commands=[c for c in cmd["compile_commands"] if obj.startswith("spike") or
                      any(s.startswith("libavcodec/") for s in c["sources"])]
            assert commands
            rs=[];signatures=collections.Counter()
            for c in commands:
                args=c["args"]
                opts=[a for a in args if a.startswith("-O")]
                dbg=[a for a in args if a=="-g" or a.startswith(("-g0","-g1","-g2","-g3","-gdwarf","-gline"))]
                prof=[a for a in args if a.startswith("-") and any(x in a for x in ("profile","coverage","unique-internal","debug-info-for-profiling"))]
                isa=[a for a in args if a in ("-mthumb","-marm")]
                sig=(tuple(opts),tuple(dbg),tuple(prof),tuple(isa))
                signatures[sig]+=1
                rs.append([c["line"],c["sources"],c["text"],opts,opts[-1] if opts else "compiler_default",dbg,prof,isa])
            dest=OUT/(obj+"-"+stage+"-commands");dest.mkdir(exist_ok=False)
            parts=tables(dest,"commands",["log_line","sources","command","optimization_flags","effective_optimization","debug_flags","profiling_coverage_flags","ISA_flags"],rs)
            r=dict(object=obj,stage=stage,command_count=len(rs),source_log=str(log),source_log_sha256=sha(log),
                   compiler_sha256=cmd["compiler_sha256"],parts=parts,
                   signatures=[dict(optimization=list(k[0]),debug=list(k[1]),profiling=list(k[2]),isa=list(k[3]),commands=n) for k,n in signatures.items()])
            dump(dest/"index.json",r);result.append(r)
    dump(OUT/"compile-options.json",result)
    print(json.dumps([{k:v for k,v in r.items() if k!="parts"} for r in result],indent=2))
if __name__=="__main__":main()
