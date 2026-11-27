#!/bin/bash
set -euo pipefail
export LC_ALL=C
task=/opt/afdo_agent/k1f-1/k2c-r1
bootdev=/dev/mmcblk0p1
mountpoint_dir=/opt/afdo_agent/k1f-1/boot-ro
mode=$1
target=$2
label=$3
expected_boot_id=$4
[[ $mode == deploy || $mode == switch || $mode == verify ]]
[[ $target == kbase || $target == kafdo ]]
[[ $label =~ ^[a-z0-9-]+$ ]]
[[ $(id -u) == 0 ]]
[[ $(tr -d '\000' </proc/device-tree/serial-number) == 100000004694d889 ]]
[[ $(cat /proc/sys/kernel/random/boot_id) == "$expected_boot_id" ]]
[[ $(uname -m) == armv7l ]]
[[ $(blkid -s UUID -o value "$bootdev") == 404C-7537 ]]
[[ $(findmnt -nr -o SOURCE /) == /dev/mmcblk0p2 ]]
[[ $(findmnt -nr -o SOURCE,FSTYPE /usr/lib/modules) == '/dev/mmcblk0p6 ext4' ]]
findmnt -nr -o OPTIONS /usr/lib/modules | grep -Eq '(^|,)ro(,|$)'
! findmnt -rn -S "$bootdev"
cd "$task"
receipts="$task/$label"
mkdir "$receipts" "$receipts/exec"
mounted_exec=0
helper="$receipts/exec/boot-publish"
cleanup() {
    local rc=$?
    trap - EXIT HUP INT TERM
    cd /
    if mountpoint -q "$mountpoint_dir"; then umount "$mountpoint_dir" || rc=89; fi
    if ((mounted_exec)); then umount "$receipts/exec" || rc=90; fi
    printf '%s\n' "$rc" > "$receipts/exit"
    exit "$rc"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
m=$mountpoint_dir
hash() { sha256sum -- "$1" | cut -f1 -d' '; }
match() { [[ $(hash "$1") == "$(hash "$2")" ]]; }
inventory() { (cd "$m"; find . -type f -exec sha256sum {} + | sort -k2); }
mount_one() {
    mount -t vfat -o "$1,nosuid,nodev,noexec" "$bootdev" "$m"
    findmnt -nr -o OPTIONS "$m" | grep -Eq "(^|,)$1(,|$)"
}
fatsize() {
    read -r block available < <(stat -f -c '%S %a' "$m")
    [[ $block == 2048 ]]
}
floor_safety() { [[ $1 -ge 524288 ]]; }
publish_replace() {
    local src=$1 name=$2
    [[ -f "$src" && ! -e "$m/$name.tmp" ]]
    (set -o noclobber; cat -- "$src" > "$m/$name.tmp")
    "$helper" fsync "$m/$name.tmp"
    match "$src" "$m/$name.tmp"
    mv -T -- "$m/$name.tmp" "$m/$name"
    "$helper" syncfs "$m"
    match "$src" "$m/$name"
}
if [[ $mode != verify ]]; then
    mount -t tmpfs -o size=1048576,nosuid,nodev,mode=0700,exec tmpfs "$receipts/exec"
    mounted_exec=1
    cp /opt/afdo_agent/k1f-1/payload/boot-publish "$helper"
    chmod 0700 "$helper"
    [[ $(hash "$helper") == 98d6c65c1a2e2b4fea6d6c46af6dc63a337cd81c8ef0ebf126e1fc5102a80c21 ]]
fi
mount_one ro
inventory > "$receipts/before.sha256"
if [[ $mode == deploy ]]; then
    [[ $(hash /sys/kernel/notes) == 146a4e2d870f3f65fdc6c6f9ca738e3cabcb83bbf4dc6f96bbcdd18c6776ab35 ]]
    match "$task/expected-before-deploy.sha256" "$receipts/before.sha256"
    ! test -e "$m/zImage-kafdo-r1"
    ! test -e "$m/zImage-kafdo-r1.tmp"
    ! test -e "$m/tryboot.txt.tmp"
    [[ -f "$m/zImage-kafdo-r1-gcov" && -f "$m/zImage-kbase" ]]
    grep -qx 'kernel=zImage-kbase' "$m/tryboot.txt"
else
    sed '\@  ./tryboot.txt$@d' "$receipts/before.sha256" > "$receipts/preserved.sha256"
    match "$task/expected-after-deploy-preserved.sha256" "$receipts/preserved.sha256"
fi
grep -qx 'cmdline=cmdline-afdo.txt' "$m/tryboot.txt"
cp "$m/tryboot.txt" "$receipts/tryboot-before.txt"
existing=$(sed -n -E 's/^kernel=zImage-(kbase|kafdo-r1)$/\1/p' "$receipts/tryboot-before.txt")
[[ $existing == kbase || $existing == kafdo-r1 ]]
sed -E 's/^kernel=zImage-(kbase|kafdo-r1)$/kernel=zImage-kbase/' "$receipts/tryboot-before.txt" > "$receipts/formal.txt"
match "$task/formal-kbase.txt" "$receipts/formal.txt"
kernel_target=$target
[[ $target != kafdo ]] || kernel_target=kafdo-r1
sed "s/^kernel=zImage-kbase$/kernel=zImage-$kernel_target/" "$receipts/formal.txt" > "$receipts/tryboot.txt"
fatsize
if [[ $mode == deploy ]]; then
    before=$(stat -c '%s' "$m/zImage-kafdo-r1-gcov")
    after=$(stat -c '%s' "$task/zImage-kafdo-r1")
    atomic_cost=$(stat -c '%s' "$receipts/tryboot.txt")
    low=$(( (available+(before+block-1)/block-(after+block-1)/block-(atomic_cost+block-1)/block)*block ))
    floor_safety "$low"
    printf '%s\n' "$low" > "$receipts/projected-lowest-available"
fi
if [[ $mode == deploy || ( $mode == switch && $existing != "$kernel_target" ) ]]; then
    [[ ! -e "$m/tryboot.txt.tmp" ]]
    umount "$m"
    mount_one rw
    inventory > "$receipts/at-write.sha256"
    match "$receipts/at-write.sha256" "$receipts/before.sha256"
    if [[ $mode == deploy ]]; then
        rm -- "$m/zImage-kafdo-r1-gcov"
        "$helper" syncfs "$m"
        publish_replace "$task/zImage-kafdo-r1" zImage-kafdo-r1
    fi
    publish_replace "$receipts/tryboot.txt" tryboot.txt
    umount "$m"
    mount_one ro
fi
inventory > "$receipts/after.sha256"
sed '\@  ./tryboot.txt$@d' "$receipts/after.sha256" > "$receipts/after-preserved.sha256"
match "$task/expected-after-deploy-preserved.sha256" "$receipts/after-preserved.sha256"
match "$receipts/tryboot.txt" "$m/tryboot.txt"
fatsize
floor_safety "$((block*available))"
df -B1 "$m" > "$receipts/df.txt"
umount "$m"
echo BOOT_AFDO_OK
