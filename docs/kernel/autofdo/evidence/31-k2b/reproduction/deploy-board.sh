#!/bin/bash
set -euo pipefail
export LC_ALL=C
task=/opt/afdo_agent/k2b-kgcov
mode=$1
boot_id=$2
need=$3
case $mode in modules|deploy|finish|rearm) ;; *) exit 64 ;; esac
[[ $need =~ ^[0-9]+$ ]]
receipt_name=${4:-$mode}
[[ $receipt_name =~ ^(modules|deploy|finish|rearm)(-resume)?$ ]]
dev=/dev/mmcblk0p1
mods=/usr/lib/modules
release=6.12.80-arm-rpi4-v7l-kgcov
new=$mods/$release
receipts=$task/$receipt_name-receipts
m=$receipts/boot-ro
x=$receipts/exec
helper=$x/boot-publish
cd "$task"
[[ $(id -u) == 0 ]]
[[ $(tr -d '\000' </proc/device-tree/serial-number) == 100000004694d889 ]]
[[ $(cat /proc/sys/kernel/random/boot_id) == "$boot_id" ]]
[[ $(uname -r) == 6.12.80-arm-rpi4-v7l && $(uname -m) == armv7l ]]
[[ $(sha256sum /sys/kernel/notes | cut -d' ' -f1) == 146a4e2d870f3f65fdc6c6f9ca738e3cabcb83bbf4dc6f96bbcdd18c6776ab35 ]]
[[ $(blkid -s UUID -o value "$dev") == 404C-7537 ]]
[[ $(findmnt -nr -o SOURCE /) == /dev/mmcblk0p2 ]]
[[ $(findmnt -nr -o SOURCE,FSTYPE "$mods") == '/dev/mmcblk0p6 ext4' ]]
[[ $(readlink -f /lib/modules) == "$mods" ]]
! findmnt -rn -S "$dev"
mkdir "$receipts" "$m" "$x"
p6_rw=0
cleanup() {
    local rc=$?
    trap - EXIT HUP INT TERM
    cd /
    if ((p6_rw)); then
        sync
        mount -o remount,ro "$mods" || rc=72
    fi
    findmnt -n -o SOURCE,FSTYPE,OPTIONS "$mods" > "$receipts/p6-final.mount" || rc=72
    if mountpoint -q "$m"; then umount "$m" || rc=73; fi
    if mountpoint -q "$x"; then umount "$x" || rc=74; fi
    printf '%s\n' "$rc" > "$receipts/exit"
    exit "$rc"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
mount -t tmpfs -o size=1M,nosuid,nodev,mode=0700,exec tmpfs "$x"
cp /opt/afdo_agent/k1f-1/payload/boot-publish "$helper"
chmod 0700 "$helper"
printf '%s  %s\n' 98d6c65c1a2e2b4fea6d6c46af6dc63a337cd81c8ef0ebf126e1fc5102a80c21 "$helper" | sha256sum -c -
hash() { sha256sum -- "$1" | cut -d' ' -f1; }
same() { [[ $(hash "$1") == "$(hash "$2")" ]]; }
ro_modules() { findmnt -n -o OPTIONS "$mods" | grep -Eq '(^|,)ro(,|$)'; }
mount_boot() {
    mount -t vfat -o "$1,nosuid,nodev,noexec" "$dev" "$m"
    findmnt -n -o OPTIONS "$m" | grep -Eq "(^|,)$1(,|$)"
}
hash_tree() {
    (cd "$1"; find . -type f -exec sha256sum {} + | sort -k2) > "$2"
}
compare_tree() {
    local filesystem=$1 snapshot=$2 expected=$3
    hash_tree "$filesystem" "$snapshot"
    same "$snapshot" "$expected"
}
compare_file_types() {
    (cd "$1"; find . -printf '%y\t%p\t%l\n' | sort) > "$2"
    same "$2" "$3"
}
verify_shared_modules() {
    compare_tree "$mods/6.12.80-arm-rpi4-v7l" "$receipts/plat-$1.sha256" "$task/expected-plat.sha256"
    compare_tree "$mods/6.12.80-arm-rpi4-v7l-kbase" "$receipts/kbase-$1.sha256" "$task/expected-kbase.sha256"
    compare_file_types "$mods/6.12.80-arm-rpi4-v7l" "$receipts/plat-$1.files.tsv" "$task/expected-plat.files.tsv"
    compare_file_types "$mods/6.12.80-arm-rpi4-v7l-kbase" "$receipts/kbase-$1.files.tsv" "$task/expected-kbase.files.tsv"
}
fatsize() {
    read -r block available < <(stat -f -c '%S %a' "$m")
    [[ $block == 2048 ]]
}
publish() {
    local input=$1 name=$2
    [[ ! -e "$m/$name.tmp" ]]
    (set -o noclobber; cat "$input" > "$m/$name.tmp")
    "$helper" fsync "$m/$name.tmp"
    same "$input" "$m/$name.tmp"
    if [[ $name == tryboot.txt ]]; then
        mv -T -- "$m/$name.tmp" "$m/$name"
    else
        "$helper" publish "$m/$name.tmp" "$m/$name"
    fi
    "$helper" syncfs "$m"
    same "$input" "$m/$name"
}
ro_modules
verify_shared_modules before
mount_boot ro
hash_tree "$m" "$receipts/boot-before.sha256"
if [[ $mode == modules || $mode == deploy ]]; then
    if [[ $mode == modules ]]; then
        [[ ! -e "$new" && ! -L "$new" ]]
    else
        [[ -d "$new" && ! -L "$new" ]]
    fi
    same "$receipts/boot-before.sha256" "$task/expected-boot-before.sha256"
    [[ -f "$m/zImage-kafdo" && ! -e "$m/zImage-kgcov" && ! -e "$m/zImage-kgcov.tmp" && ! -e "$m/tryboot.txt.tmp" ]]
    same "$task/tryboot-kbase.txt" "$m/tryboot.txt"
    read -r p6_block p6_avail < <(stat -f -c '%S %a' "$mods")
    [[ $p6_block == 4096 ]]
    if [[ $mode == modules ]]; then
        [[ $((p6_block*p6_avail)) -ge "$need" ]]
    fi
    printf 'available_before=%s required=%s\n' "$((p6_block*p6_avail))" "$need" > "$receipts/p6-preflight.txt"
    fatsize
    old=$(stat -c %s "$m/zImage-kafdo")
    image=$(stat -c %s "$task/zImage-kgcov")
    config=$(stat -c %s "$task/tryboot-kgcov.txt")
    low=$(((available+(old+block-1)/block-(image+block-1)/block-(config+block-1)/block)*block))
    printf '%s\n' "$low" > "$receipts/boot-projected-minimum"
    ((low>=524288))
elif [[ $mode == rearm ]]; then
    same "$receipts/boot-before.sha256" "$task/expected-boot-final.sha256"
    same "$task/tryboot-kbase.txt" "$m/tryboot.txt"
    [[ ! -e "$m/tryboot.txt.tmp" ]]
    fatsize
    config=$(stat -c %s "$task/tryboot-kgcov.txt")
    (( (available-(config+block-1)/block)*block>=524288 ))
else
    same "$receipts/boot-before.sha256" "$task/expected-boot-kgcov.sha256"
    same "$task/tryboot-kgcov.txt" "$m/tryboot.txt"
fi
umount "$m"
if [[ $mode == modules ]]; then
    p6_rw=1
    mount -o remount,rw "$mods"
    findmnt -n -o OPTIONS "$mods" | grep -Eq '(^|,)rw(,|$)'
    mkdir "$new"
    tar --numeric-owner --same-owner --same-permissions -xf kgcov-modules.tar -C "$mods"
    compare_tree "$new" "$receipts/kgcov-rw.sha256" "$task/kgcov.sha256"
    "$helper" syncfs "$mods"
    mount -o remount,ro "$mods"
    ro_modules
    p6_rw=0
    du -B1 -s "$new" > "$receipts/installed.du"
    df -B1 -P "$mods" > "$receipts/p6-after.df"
fi
compare_tree "$new" "$receipts/kgcov-ro.sha256" "$task/kgcov.sha256"
compare_file_types "$new" "$receipts/kgcov-ro.files.tsv" "$task/kgcov.files.tsv"
verify_shared_modules after
if [[ $mode == modules ]]; then
    echo BOARD_WRITE_OK
    exit 0
fi
mount_boot rw
compare_tree "$m" "$receipts/boot-at-write.sha256" "$receipts/boot-before.sha256"
if [[ $mode == deploy ]]; then
    fatsize
    (( (available+(old+block-1)/block-(image+block-1)/block-(config+block-1)/block)*block>=524288 ))
    rm -- "$m/zImage-kafdo"
    "$helper" syncfs "$m"
    publish "$task/zImage-kgcov" zImage-kgcov
    publish "$task/tryboot-kgcov.txt" tryboot.txt
    final=expected-boot-kgcov.sha256
elif [[ $mode == rearm ]]; then
    publish "$task/tryboot-kgcov.txt" tryboot.txt
    final=expected-boot-kgcov.sha256
else
    publish "$task/tryboot-kbase.txt" tryboot.txt
    final=expected-boot-final.sha256
fi
umount "$m"
mount_boot ro
compare_tree "$m" "$receipts/boot-after.sha256" "$task/$final"
fatsize
((available*block>=524288))
df -B1 -P "$m" > "$receipts/boot-after.df"
umount "$m"
echo BOARD_WRITE_OK
