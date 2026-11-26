#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
scratch=$PWD
workspace=$(realpath ../../..)
kernel_root=$workspace/temp/kernel-afdo-k1
base=$kernel_root/kbase
tools=$kernel_root/profgen-k1b/review/tool-wrappers
probe="$scratch/abi"
mkdir "$probe"
exec 9<>"$workspace/temp/host-gbs.lock"
flock -w 28800 9
printf 'lock acquired %s\n' "$(date -Iseconds)" > "$probe/startup.log"
resource_deadline=$((SECONDS+10800))
while :; do
    available=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
    free=$(df -B1 --output=avail /home | tail -1)
    load=$(cut -d ' ' -f 1 /proc/loadavg)
    active=$(ps -eo stat=,comm= | awk '$1 !~ /^Z/ && $2 ~ /^(gbs|rpmbuild|depanneur)$/')
    printf '%s mem_available_kib=%s disk_available=%s load1=%s processes=%s\n' "$(date -Iseconds)" "$available" "$free" "$load" "$active" >> "$probe/startup.log"
    if [[ -z "$active" ]] && (( available >= 16*1024*1024 && free >= 50*1024*1024*1024 )) && awk -v load="$load" -v cpus="$(nproc)" 'BEGIN {exit !(load < 0.6*cpus)}'; then
        break
    fi
    if (( SECONDS >= resource_deadline )); then exit 1; fi
    for _ in {1..10}; do sleep 60; done
done
git clone --shared --quiet --no-checkout "$base/source" "$scratch/source"
git -C "$scratch/source" switch -c k2b-selective-gcov 7fffbec570692c925cbf1f58ea9b1cd1a5d78ac8
python3 - "$scratch" <<'PY'
import json
from pathlib import Path
import sys
root=Path(sys.argv[1])
selection=json.loads((root/'selection.json').read_text())
source=root/'source'
for directory in selection['selected']:
    makefile=source/directory/'Makefile'
    content=makefile.read_text()
    assert not any(line.startswith('GCOV_PROFILE ') for line in content.splitlines()), directory
    first, following=content.split('\n', 1)
    makefile.write_text(first+'\n\nGCOV_PROFILE := y\n'+following)
spec=source/'packaging/linux-rpi.spec'
text=spec.read_text()
key='EXTRA_FRAGMENTS="%{?lsm_fragment}"'
assert text.count(key)==1
spec.write_text(text.replace(key, 'EXTRA_FRAGMENTS="kernel/configs/k2b-gcov.config %{?lsm_fragment}"'))
(source/'kernel/configs/k2b-gcov.config').write_text('CONFIG_GCOV_KERNEL=y\n# CONFIG_GCOV_PROFILE_ALL is not set\n')
PY
git -C "$scratch/source" add --     kernel/sched/Makefile kernel/locking/Makefile fs/Makefile mm/Makefile lib/Makefile kernel/Makefile     packaging/linux-rpi.spec kernel/configs/k2b-gcov.config
git -C "$scratch/source" diff --cached --check
git -C "$scratch/source" commit -m 'Enable selective kernel GCOV for the arm-rpi4 laboratory build' \
    -m 'Instrument six built-in source directories selected from the sample profile. Apply the GCOV configuration fragment only to the ordinary Raspberry Pi 4 package variant.' \
    > "$probe/commit.log"
git -C "$scratch/source" format-patch -1 --stdout > "$scratch/0001-selective-kernel-gcov.patch"
git -C "$scratch/source" rev-parse HEAD > "$scratch/source.tip"
export PATH="$workspace/temp/kernel-afdo-k0/k2a/r2/bin:$tools:$PATH"
export M4="$workspace/temp/kernel-afdo-k0/k2a/r2/bin/m4"
export LOCALVERSION=-kbase
export KBUILD_BUILD_TIMESTAMP="Wed Nov 18 14:59:26 UTC 2026"
export KBUILD_BUILD_USER=abuild KBUILD_BUILD_HOST=linhao-linux KBUILD_BUILD_VERSION=1
export LC_ALL=C
printf '%s\n' '-arm-rpi4' > "$scratch/source/localversion-tizen"
clang --version > "$probe/clang-version.txt"
source="$scratch/source"
opts=(-C "$source" -j2 ARCH=arm LLVM=1 HOSTCC=gcc 'CC=clang -fintegrated-cc1' KBUILD_SYMTYPES=1)
for variant in base gcov; do
    object_dir="$probe/$variant"
    mkdir "$object_dir"
    cp "$base/artifacts/arm-rpi4/.config" "$object_dir/.config"
    if [[ "$variant" == gcov ]]; then
        "$source/scripts/kconfig/merge_config.sh" -m -O "$object_dir" "$object_dir/.config" "$source/kernel/configs/k2b-gcov.config" > "$probe/config-merge.log" 2>&1
    fi
    make "${opts[@]}" O="$object_dir" olddefconfig > "$probe/$variant-olddefconfig.log" 2>&1
    cp "$object_dir/.config" "$probe/$variant.config"
done
"$source/scripts/diffconfig" "$probe/base.config" "$probe/gcov.config" > "$probe/paired-config.diff"
"$source/scripts/diffconfig" "$base/artifacts/arm-rpi4/.config" "$probe/base.config" > "$probe/ambient-config.diff"
grep -x 'CONFIG_GCOV_KERNEL=y' "$probe/gcov.config"
grep -x '# CONFIG_GCOV_PROFILE_ALL is not set' "$probe/gcov.config"
grep -x 'CONFIG_MODVERSIONS=y' "$probe/gcov.config"
grep -x 'CONFIG_DEBUG_FS=y' "$probe/gcov.config"
# The host lacks libelf headers; disable BTF in both object-only replays. The
# baseline CRC is checked against the frozen GBS build before drawing conclusions.
for variant in base gcov; do
    object_dir="$probe/$variant"
    "$source/scripts/config" --file "$object_dir/.config" -d DEBUG_INFO_BTF
    make "${opts[@]}" O="$object_dir" olddefconfig > "$probe/$variant-object-config.log" 2>&1
    printf '%q ' make "${opts[@]}" O="$object_dir" V=1 kernel/module/version.o > "$probe/$variant-build.argv"
    printf '\n' >> "$probe/$variant-build.argv"
    make "${opts[@]}" O="$object_dir" V=1 kernel/module/version.o > "$probe/$variant-build.log" 2>&1
    grep -F '#SYMVER module_layout ' "$object_dir/kernel/module/.version.o.cmd" > "$probe/$variant-module-layout.crc"
    grep -E '^s#module ' "$object_dir/kernel/module/version.symtypes" > "$probe/$variant-struct-module.types"
    cp "$object_dir/include/generated/utsrelease.h" "$probe/$variant-utsrelease.h"
done
"$source/scripts/diffconfig" "$probe/base/.config" "$probe/gcov/.config" > "$probe/paired-object-config.diff"
cat "$probe/"*-module-layout.crc
