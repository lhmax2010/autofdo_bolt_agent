"""Reclassify immutable AST/Lexer evidence; no new compiler or profile input."""
import json
import sys
from v18_domain import OUT, TEMP, dump
from v18_rules import classify_code_free
from run_scoped import sha
import v17_classify as historical


def main(obj):
    source = historical.OUT / (obj + "-calls.json")
    dump(OUT / (obj + "-calls.json"), json.loads(source.read_text()))
    dump(OUT / (obj + "-calls-provenance.json"),
         dict(path=str(source), sha256=sha(source), kind="reused immutable ELF call attributes"))
    historical.OUT, historical.TEMP = OUT, TEMP
    historical.classify_code_free = classify_code_free
    historical.dump = dump
    historical.main(obj)

if __name__ == "__main__":
    main(sys.argv[1])
