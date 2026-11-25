#!/bin/bash
set -euo pipefail
: "${WK:?}" "${K2:?}"
while [[ $(df -B1 --output=avail /home | tail -1) -lt 40000000000 ]]; do
    date -Iseconds
    sleep 60
done
K="$WK/temp/kernel-afdo-k1/kbase"
SRC="$K/source"
A="$K/gbs-root-01/local/BUILD-ROOTS/scratch.armv7l.0"
B="$WK/temp/kernel-afdo-k1/profgen-k1b/review/tool-wrappers"
out="$K2/r2"
export PATH="$out/bin:$B:$PATH" M4="$out/bin/m4"
for t in pahole bc; do
    printf '#!/bin/bash\nexec /usr/bin/qemu-arm-static -L %q %q "$@"\n' "$A" "$A/usr/bin/$t" > "$out/bin/$t"
    chmod +x "$out/bin/$t"
done
pahole --version > "$out/pahole-version.txt"
base="$out/sample-base"
gcov="$out/sample-gcov"
mkdir "$base" "$gcov"
cleanup() { rm -rf -- "$base" "$gcov"; }
trap cleanup EXIT
cfg="$K/artifacts/arm-rpi4/.config"
cp "$cfg" "$base/.config"
cp "$cfg" "$gcov/.config"
bash "$SRC/scripts/config" --file "$gcov/.config" -e GCOV_KERNEL -e GCOV_PROFILE_ALL -e DEBUG_FS
opts=(-C "$SRC" -j4 ARCH=arm LLVM=1 HOSTCC=gcc 'CC=clang -fintegrated-cc1')
for variant in base gcov; do
    if [[ $variant == base ]]; then object_dir=$base; else object_dir=$gcov; fi
    make "${opts[@]}" O="$object_dir" olddefconfig > "$out/olddefconfig-$variant.log" 2>&1
    cp "$object_dir/.config" "$out/$variant.config"
done
"$SRC/scripts/diffconfig" "$cfg" "$base/.config" > "$out/ambient-config.diff"
"$SRC/scripts/diffconfig" "$base/.config" "$gcov/.config" > "$out/gcov-config.diff"
"$SRC/scripts/diffconfig" "$cfg" "$gcov/.config" > "$out/kbase-to-local-gcov.diff"
grep -qx 'CONFIG_GCOV_KERNEL=y' "$gcov/.config"
grep -qx 'CONFIG_GCOV_PROFILE_ALL=y' "$gcov/.config"
grep -qx 'CONFIG_ARCH_HAS_GCOV_PROFILE_ALL=y' "$gcov/.config"
grep -qx 'CONFIG_DEBUG_FS=y' "$gcov/.config"
# Object-only host lacks libelf development headers for the link-time BTF resolver.
# Keep the paired olddefconfig above intact, and turn off BTF in both object probes.
for variant in base gcov; do
    if [[ $variant == base ]]; then object_dir=$base; else object_dir=$gcov; fi
    bash "$SRC/scripts/config" --file "$object_dir/.config" -d DEBUG_INFO_BTF
    make "${opts[@]}" O="$object_dir" olddefconfig > "$out/objects-olddefconfig-$variant.log" 2>&1
    cp "$object_dir/.config" "$out/objects-$variant.config"
done
"$SRC/scripts/diffconfig" "$base/.config" "$gcov/.config" > "$out/objects-config.diff"
objects=(arch/arm/kernel/traps.o fs/pipe.o kernel/sched/core.o kernel/softirq.o mm/memory.o net/core/dev.o drivers/base/core.o)
for variant in base gcov; do
    if [[ $variant == base ]]; then object_dir=$base; else object_dir=$gcov; fi
    printf '%q ' make "${opts[@]}" O="$object_dir" "${objects[@]}" > "$out/objects-$variant.argv"
    printf '\n' >> "$out/objects-$variant.argv"
    make "${opts[@]}" O="$object_dir" "${objects[@]}" > "$out/objects-$variant.log" 2>&1
done
python3 "$out/estimate_size.py" --baseline "$base" --gcov "$gcov" --vmlinux "$K/artifacts/arm-rpi4/vmlinux" \
    --zimage "$K/artifacts/arm-rpi4/arch/arm/boot/zImage" --output "$out/size-estimate.json" "${objects[@]}"
for entry in "${objects[@]}"; do
    dir=${entry%/*}
    name=${entry##*/}
    target="$out/receipts/$dir"
    mkdir -p "$target"
    for variant in base gcov; do
        if [[ $variant == base ]]; then object_dir=$base; else object_dir=$gcov; fi
        cp "$object_dir/$dir/.$name.cmd" "$target/$name.$variant.cmd"
        "$B/llvm-readelf" -S --wide "$object_dir/$entry" > "$target/$name.$variant.sections"
    done
done
od -A n -t x1 -N 12 "$gcov/fs/pipe.gcno" > "$out/arm-gcno-header.txt"
