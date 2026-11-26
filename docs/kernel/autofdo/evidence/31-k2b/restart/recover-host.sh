#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
work=$PWD
wk=$(realpath ../../..)
k1="$wk/temp/kernel-afdo-k1"
old="$k1/k1d-c-extra"
orig="$k1/kbase"
root="$work/kgcov/gbs-root/local/BUILD-ROOTS/scratch.armv7l.0"
rp="$root/home/abuild/rpmbuild"
src="$rp/BUILD/rpi4-linux-kernel-6.12.80"
build="$src/build/arm-rpi4"
release=6.12.80-arm-rpi4-v7l-kgcov
stage="$rp/BUILDROOT/rpi4-linux-kernel-6.12.80-0.arm/lib/modules/$release"
out="$work/artifacts"
staging="$work/staging"
mods="$staging/lib/modules/$release"
devel="$work/recovered-devel"
export LC_ALL=C PYTHONPYCACHEPREFIX="$work/pycache"
test "$(stat -c %s "$build/arch/arm/boot/zImage")" = 11408536
grep -Fqx '#define UTS_RELEASE "6.12.80-arm-rpi4-v7l-kgcov"' "$build/include/generated/utsrelease.h"
grep -E '^0x2f3f1497[[:blank:]]+module_layout[[:blank:]]' "$build/Module.symvers"
test "$(find "$stage" -name '*.ko' -type f | wc -l)" = 52
mkdir -p "$out" "$staging/lib/modules" "$devel" "$work/build-tools"
for f in vmlinux .config Module.symvers System.map modules.order modules.builtin modules.builtin.modinfo \
    include/generated/compile.h include/generated/utsrelease.h include/generated/utsversion.h \
    arch/arm/boot/Image arch/arm/boot/zImage arch/arm/boot/compressed/piggy_data; do
    mkdir -p "$out/$(dirname "$f")"
    if [[ ! -e "$out/$f" ]]; then ln -- "$build/$f" "$out/$f"; fi
    [[ "$build/$f" -ef "$out/$f" ]]
done
emul="$root/emul/usr"
for name in clang ld.lld llvm-ar llvm-nm llvm-objcopy llvm-objdump llvm-readelf llvm-strip; do
    executable="$emul/bin/$name"
    args=()
    if [[ $name == clang ]]; then executable="$emul/bin/clang-22"; args=(-no-canonical-prefixes); fi
    printf -v line '%q ' "$emul/lib64/ld-linux-x86-64.so.2" --library-path "$emul/lib64" --argv0 "$name" "$executable" "${args[@]}"
    printf '#!/usr/bin/env bash\nexec %s"$@"\n' "$line" > "build-tools/$name"
    chmod 0755 "build-tools/$name"
done
arm_wrapper() {
    local filename=$1 executable=$2 line
    mkdir -p "$(dirname "$filename")"
    printf -v line '%q ' /usr/bin/qemu-arm-static -L "$root" "$executable"
    printf '#!/usr/bin/env bash\nexec %s"$@"\n' "$line" > "$filename"
    chmod 0755 "$filename"
}
arm_wrapper "$work/build-tools/pahole" "$root/usr/bin/pahole"
export PATH="$work/build-tools:$PATH"
(cd "$build"; llvm-ar t vmlinux.a) > "$out/vmlinux-a-members.txt"
python3 - "$build" "$out" <<'PY'
import os
from pathlib import Path
import sys

build, out = map(Path,sys.argv[1:3])
for dirname in ('kernel/sched','kernel/locking','fs','mm','lib','kernel'):
    where = out/'gcno'/dirname
    where.mkdir(parents=True,exist_ok=True)
    for note in (build/dirname).glob('*.gcno'):
        dest=where/note.name
        if not dest.exists():
            os.link(note,dest)
        assert dest.samefile(note),dest
PY
python3 "$work/discover-notes.py" "$out"
"$work/source/scripts/diffconfig" "$orig/artifacts/arm-rpi4/.config" "$out/.config" > "$out/kbase-config.diff"
grep -Fx 'CONFIG_GCOV_KERNEL=y' "$out/.config"
grep -Fx 'CONFIG_CONSTRUCTORS=y' "$out/.config"
grep -Fx '# CONFIG_GCOV_PROFILE_ALL is not set' "$out/.config"
grep -Fx 'CONFIG_DEBUG_FS=y' "$out/.config"
grep -Fx 'CONFIG_DEBUG_INFO_DWARF4=y' "$out/.config"
grep -Fx 'CONFIG_CLANG_VERSION=220108' "$out/.config"
grep -Fx 'CONFIG_KERNEL_XZ=y' "$out/.config"
cmp "$orig/artifacts/arm-rpi4/include/generated/compile.h" "$out/include/generated/compile.h"
cmp "$orig/artifacts/arm-rpi4/include/generated/utsversion.h" "$out/include/generated/utsversion.h"
readelf -n "$out/vmlinux" > "$out/vmlinux-notes.txt"
python3 "$work/check-image.py" "$out/vmlinux" "$out/arch/arm/boot/Image" "$out/arch/arm/boot/compressed/piggy_data" \
    "$out/arch/arm/boot/zImage" "$out/image-identity.json" > "$out/image-identity.log"
jq -e '.build_id=="3d6e80182e504736cb06d14a62aed6845fef6c4d" and .compression=="xz" and .zimage_bytes==11408536' "$out/image-identity.json"
python3 "$work/check-deps.py" "$k1/base-0fac5de6/dependencies/installed-matched-04.json" "$root" > "$out/installed-deps.json"
# Separate output with generated config and headers from the original GBS build.
# No writes into the original kernel build tree.
for p in .config include/config include/generated arch/arm/include/generated Module.symvers scripts/module.lds vmlinux; do
    mkdir -p "$devel/$(dirname "$p")"
    [[ -e "$devel/$p" ]] || ln -s -- "$build/$p" "$devel/$p"
done
for helper in scripts/basic/fixdep scripts/mod/modpost scripts/recordmcount scripts/genksyms/genksyms tools/bpf/resolve_btfids/resolve_btfids; do
    arm_wrapper "$devel/$helper" "$build/$helper"
done
src_rpm="$old/sources/linux-tizen-modules-source-11.0.0-0.armv7l.rpm"
sha256sum "$src_rpm" > "$out/extra-source.sha256"
grep -q '^ef770d5e8af0532fe4f80748a699e13710025fb0c1218f6504bc9eee1d80dbf5  ' "$out/extra-source.sha256"
if [[ ! -d "$work/recovered-module-source" ]]; then
    mkdir "$work/recovered-module-source"
    rpm2cpio "$src_rpm" | (cd "$work/recovered-module-source"; cpio -idm --quiet)
fi
external="$work/recovered-module-source/usr/src/linux-tizen-modules-source"
find "$external" -name Makefile -type f -exec sed -i 's/-Wno-error=missing-attributes//g' {} +
export KBUILD_BUILD_USER=abuild KBUILD_BUILD_HOST=linhao-linux
export KBUILD_BUILD_TIMESTAMP='Wed Nov 18 14:59:26 UTC 2026'
export KBUILD_BUILD_VERSION=1 LOCALVERSION=-kgcov
export BUILD_dm_bow=m BUILD_extcon_usb_fixed=m BUILD_inform_reboot=m
export BUILD_kdbus=m BUILD_logger=m BUILD_proc_tsm=m BUILD_zlogger=n THREAD_GROUP_CPUTIME_SUPPORT=1
{
    clang --version
    ld.lld --version
    pahole --version
    make -C "$src" O="$devel" M="$external" ARCH=arm LLVM=1 LD=ld.lld \
        "KERNELRELEASE=$release" "CFLAGS_MODULE=-I$external/include" V=1 -j1 modules
} > "$out/build-extra.log" 2>&1
cp "$external/Module.symvers" "$out/extra-Module.symvers"
# Kbuild modules_install completed before devel/RPM packaging was interrupted.
# Copy the 52 staged files; preserve the original GBS staging files untouched.
mkdir -p "$mods"
cp -a "$stage/." "$mods/"
find "$mods/kernel" -type f -name '*.ko' | wc -l | grep -Fx 52
mkdir -p "$mods/extra/kdbus"
for name in dm-bow extcon-usb-fixed inform-reboot kdbus/kdbus logger proc-tsm; do
    install -m 0644 "$external/$name.ko" "$mods/extra/$name.ko"
    llvm-strip --strip-debug "$mods/extra/$name.ko"
done
python3 "$work/check-modules.py" "$out" "$mods" "$wk/temp/kernel-afdo-k0/k1f-1e/stripped-staging/lib/modules/6.12.80-arm-rpi4-v7l-kbase" > "$out/module-abi.json"
depmod -b "$staging" -e -F "$out/System.map" "$release" > "$out/depmod.log" 2>&1
[[ ! -s "$out/depmod.log" ]]
(
    cd "$mods"
    find . -printf '%y\t%p\t%l\n' | sort > "$out/kgcov.files.tsv"
    find . -type f -exec sha256sum {} + | sort -k2 > "$out/kgcov.sha256"
    sha256sum -c "$out/kgcov.sha256" > "$out/kgcov-sha256-check.log"
)
python3 - "$mods" > "$out/p6-size.json" <<'PY'
import json
from pathlib import Path
import sys

tree=Path(sys.argv[1])
block=4096

def alloc(p):
    if p.is_symlink():
        return block if len(str(p.readlink()).encode())>=60 else 0
    if p.is_dir():
        entries=sum(12+len(child.name.encode()) for child in p.iterdir())
        return max(block,(entries+block-1)//block*block)
    assert p.is_file(),p
    return (p.stat().st_size+block-1)//block*block

size=sum(alloc(p) for p in [tree,*tree.rglob('*')])
print(json.dumps({'allocation_unit':block,'estimated_allocated_bytes':size,
                  'minimum_free_bytes':(size*6+4)//5},indent=2))
PY
tar -C "$staging/lib/modules" --owner=0 --group=0 --numeric-owner -cf "$out/kgcov-modules.tar" "$release"
sha256sum "$out/kgcov-modules.tar" "$out/arch/arm/boot/zImage"
touch "$work/HOST_READY"
