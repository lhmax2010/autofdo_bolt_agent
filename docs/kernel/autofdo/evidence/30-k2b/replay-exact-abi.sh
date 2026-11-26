#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
workspace=$(realpath ../../..)
scratch=$PWD
base="$workspace/temp/kernel-afdo-k1/kbase"
tools="$workspace/temp/kernel-afdo-k1/profgen-k1b/review/tool-wrappers"
export PATH="$workspace/temp/kernel-afdo-k0/k2a/r2/bin:$tools:$PATH"
export M4="$workspace/temp/kernel-afdo-k0/k2a/r2/bin/m4"
export LOCALVERSION=-kbase LC_ALL=C
export KBUILD_BUILD_TIMESTAMP="Wed Nov 18 14:59:26 UTC 2026" KBUILD_BUILD_USER=abuild KBUILD_BUILD_HOST=linhao-linux KBUILD_BUILD_VERSION=1
exec 9<>"$workspace/temp/host-gbs.lock"
flock -w 28800 9
mkdir -p abi/exact
for variant in base gcov; do
    object_dir="$scratch/abi/$variant"
    cp "$scratch/abi/$variant.config" "$object_dir/.config"
    make -s -C "$scratch/source" O="$object_dir" -j2 ARCH=arm LLVM=1 HOSTCC=gcc 'CC=clang -fintegrated-cc1' syncconfig \
        > "$scratch/abi/exact/$variant-syncconfig.log" 2>&1
    grep -x '#define CONFIG_DEBUG_INFO_BTF 1' "$object_dir/include/generated/autoconf.h"
    python3 - "$scratch/source" "$scratch/abi" "$variant" <<'PY'
from pathlib import Path
import shlex
import subprocess
import sys

source, abi = map(Path, sys.argv[1:3])
variant = sys.argv[3]
object_dir = abi / variant
log = abi / 'exact'
cmdfile = object_dir / 'kernel/module/.version.o.cmd'
command = cmdfile.read_text().splitlines()[0].split(' := ', 1)[1].split(';', 1)[0]
args = shlex.split(command)
assert args[-4:] == ['-c', '-o', 'kernel/module/version.o', str(source / 'kernel/module/version.c')], args[-6:]
args = args[:-4] + ['-D__GENKSYMS__', '-E', args[-1]]
genksyms = ['scripts/genksyms/genksyms', '-T', str(log / (variant+'.symtypes')), '-r', '/dev/null']
(log / (variant + '-argv.json')).write_text(__import__('json').dumps([args, genksyms], indent=2)+'\n')
with (log / (variant + '.i')).open('wb') as preprocessed:
    subprocess.run(args, cwd=object_dir, stdout=preprocessed, check=True)
with (log / (variant + '.i')).open('rb') as preprocessed:
    output = subprocess.run(genksyms, cwd=object_dir, stdin=preprocessed, capture_output=True, check=True, text=True).stdout
assert len(output.splitlines()) == 1 and output.startswith('#SYMVER module_layout '), output
(log / (variant + '-module-layout.crc')).write_text(output)
print(variant, output.strip())
PY
done
