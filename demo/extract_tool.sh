#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 3 ]]; then
  echo "Usage: $0 RPM_DIRECTORY NEW_EXTRACTED_DIRECTORY GBS_SCRATCH_ROOT" >&2
  exit 2
fi
rpms=$(realpath "$1")
dest=$2
root=$(realpath "$3")
[[ ! -e "$dest" ]] || { echo "Destination already exists: $dest" >&2; exit 2; }
mkdir -p "$dest"
dest=$(realpath "$dest")
for package in llvm libllvm; do
  rpm="$rpms/$package-22.1.8-1.x86_64.rpm"
  [[ -f "$rpm" ]] || { echo "Missing RPM: $rpm" >&2; exit 2; }
  rpm2cpio "$rpm" | (cd "$dest" && cpio -idm --no-absolute-filenames) \
    >"$dest/$package-extract.log" 2>&1
done
tool="$dest/usr/bin/llvm-profgen"
loader="$root/lib64/ld-linux-x86-64.so.2"
libs="$dest/usr/lib64:$root/lib64:$root/usr/lib64"
sha256sum "$tool"
"$loader" --library-path "$libs" "$tool" --version
"$loader" --library-path "$libs" "$tool" --help > "$dest/llvm-profgen-help.txt"
for option in ip-samples ip-aggregation ip-skid ip-zero-fill ip-head-samples quality-report; do
  grep -q -- "--$option" "$dest/llvm-profgen-help.txt"
done
echo "Version and documented option checks passed."
