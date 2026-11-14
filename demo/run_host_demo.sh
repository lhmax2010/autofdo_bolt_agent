#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 4 ]]; then
  echo "Usage: $0 LLVM_SANDBOX_TREE EXTRACTED_RPM_ROOT GBS_SCRATCH_ROOT NEW_OUTPUT_DIR" >&2
  exit 2
fi
tree=$(realpath "$1")
rpmroot=$(realpath "$2")
root=$(realpath "$3")
out=$4
[[ ! -e "$out" ]] || { echo "Output directory already exists: $out" >&2; exit 2; }
[[ $(git -c gc.auto=0 -c maintenance.auto=false -C "$tree" rev-parse HEAD) == c8942ae1b53099a78a97dca2b64427af6e58432b ]]
loader="$root/lib64/ld-linux-x86-64.so.2"
libs="$rpmroot/usr/lib64:$root/lib64:$root/usr/lib64"
profgen="$rpmroot/usr/bin/llvm-profgen"
profdata="$rpmroot/usr/bin/llvm-profdata"
[[ -x "$loader" && -x "$profgen" && -x "$profdata" ]]
mkdir -p "$out"
out=$(realpath "$out")
inputs="$tree/llvm/test/tools/llvm-profgen/Inputs/ip-mode"
for name in a64-pie thumb-count; do
  "$loader" --library-path "$libs" "$profgen" \
    --ip-samples --binary="$inputs/$name.perfbin" \
    --perfscript="$inputs/$name.perfscript" \
    --binary-match-regex='.*' --allow-missing-build-id \
    --ip-weight=period --ip-aggregation=max \
    --ip-skid=none --ip-zero-fill=none --ip-head-samples=none \
    --format=extbinary --output="$out/$name.extbinary" \
    --quality-report="$out/$name.quality.json" \
    >"$out/$name.stdout" 2>"$out/$name.stderr"
  "$loader" --library-path "$libs" "$profdata" show --sample --all-functions \
    "$out/$name.extbinary" >"$out/$name.show.txt"
  echo "=== $name ==="
  cat "$out/$name.show.txt"
  python3 - "$out/$name.quality.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1], encoding="utf-8"))
assert r["verdict"]["conversion"] == "ok"
print(json.dumps({
    "conversion": r["verdict"]["conversion"],
    "identity": r["verdict"]["identity"],
    "target_samples": r["samples"]["target"]["counts"]["sample_count"],
    "usable_samples": r["samples"]["target"]["usable"]["sample_count"],
    "written_positions": r["samples"]["written_positions"],
    "sampling_adequacy": r["verdict"]["sampling_adequacy"]
}, sort_keys=True))
PY
done
