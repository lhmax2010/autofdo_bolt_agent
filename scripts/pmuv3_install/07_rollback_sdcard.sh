#!/bin/bash
# Run this file with /bin/bash; never source it into an interactive shell.
set -euo pipefail
export TMPDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/tmp
readonly SCRIPT_ID=07_rollback_sdcard
readonly LOGDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/logs
step=$SCRIPT_ID
finish() {
    local rc=$? now
    trap - EXIT
    trap '' INT TERM HUP
    set +e
    now=$(date --iso-8601=seconds)
    if (( rc == 0 )); then
        printf 'END %s OK\n' "$now"
        [[ ! -d $LOGDIR ]] || printf 'END %s OK\n' "$now" > "$LOGDIR/$SCRIPT_ID.status"
    else
        printf 'END %s FAILED %s\n' "$now" "$step"
        [[ ! -d $LOGDIR ]] || printf 'END %s FAILED %s\n' "$now" "$step" > "$LOGDIR/$SCRIPT_ID.status"
    fi
    exit "$rc"
}
trap finish EXIT
trap 'step="$SCRIPT_ID:line=$LINENO"' ERR
trap 'step="$SCRIPT_ID:INT"; exit 130' INT
trap 'step="$SCRIPT_ID:TERM"; exit 143' TERM
trap 'step="$SCRIPT_ID:HUP"; exit 129' HUP
mkdir -p "$TMPDIR" "$LOGDIR"
readonly LOG="$LOGDIR/$SCRIPT_ID.$(date +%Y%m%dT%H%M%S%z).log"
exec > >(tee -a "$LOG") 2>&1
printf 'START %s %s\nLOG %s\n' "$(date --iso-8601=seconds)" "$SCRIPT_ID" "$LOG"

export TMPDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/tmp
cd /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent
(cd /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/backup && nice -n 19 ionice -c3 sha256sum -c /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/backup/SHA256SUMS)
boot_uuid=$(cat /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/backup/boot.uuid)
root_uuid=$(cat /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/backup/root.uuid)
boot_device=$(sudo blkid -U "$boot_uuid")
root_device=$(sudo blkid -U "$root_uuid")
[[ -b $boot_device && -b $root_device && $boot_device != "$root_device" ]]
[[ $(lsblk -ndo PKNAME "$boot_device") == "$(lsblk -ndo PKNAME "$root_device")" ]]
[[ $(cat "/sys/class/block/${boot_device##*/}/partition") == 1 && $(cat "/sys/class/block/${root_device##*/}/partition") == 2 ]]
if findmnt -rn -S "$boot_device" || findmnt -rn -S "$root_device"; then
    echo 'STOP: card partition already mounted; unmount it safely first' >&2
    exit 1
fi
mkdir -p /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/recovery/boot /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/recovery/root
sudo mount "$root_device" /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/recovery/root
sudo mount "$boot_device" /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/recovery/boot
sudo nice -n 19 ionice -c3 tar --no-same-owner --no-same-permissions -C /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/recovery/boot -xf /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/backup/boot.tar
sudo nice -n 19 ionice -c3 tar --xattrs --xattrs-include='*' --acls --numeric-owner -C /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/recovery/root -xpf /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/backup/modules.tar
expected_old=$(awk '{print $1}' /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/backup/old-zImage.sha256)
printf '%s  %s\n' "$expected_old" /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/recovery/boot/zImage | sha256sum -c -
sync
sudo umount /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/recovery/boot
sudo umount /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/recovery/root
