#!/bin/bash
# Run this file with /bin/bash; never source it into an interactive shell.
set -euo pipefail
export TMPDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/tmp
readonly SCRIPT_ID=01_host_prepare
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
mkdir -p /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/new /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/old /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/scripts /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/backup
for name in arm-rpi4-linux-kernel arm-rpi4-linux-kernel-modules; do
    nice -n 19 ionice -c3 cp "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-RPI4-PMUV3/local/repos/tizen_unified_standard/armv7l/RPMS/$name-6.12.80-0.armv7l.rpm" /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/new/
    nice -n 19 ionice -c3 cp "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-verify/baseline/$name-6.12.80-0.armv7l.rpm" /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/old/
done
cat > /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/new/SHA256SUMS <<'EOF'
832a0241990bab9162cfd9455efc687215af4222011eeb8cf64ed8671e3af18c  arm-rpi4-linux-kernel-6.12.80-0.armv7l.rpm
c08a11d4f624097a3619e31d4cb4dc6fa23965441ba66307e440cd01a76057f2  arm-rpi4-linux-kernel-modules-6.12.80-0.armv7l.rpm
EOF
cat > /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/old/SHA256SUMS <<'EOF'
c0282c7388fcaf020f6ec2bdee78191a22fbb2f4a1903378ca74bf8739f4da98  arm-rpi4-linux-kernel-6.12.80-0.armv7l.rpm
8234b9bea41af489d72777896ec7b6b8e0ec20312b178156242d8cc0fceae560  arm-rpi4-linux-kernel-modules-6.12.80-0.armv7l.rpm
EOF
(cd /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/new && nice -n 19 ionice -c3 sha256sum -c /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/new/SHA256SUMS)
(cd /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/old && nice -n 19 ionice -c3 sha256sum -c /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/old/SHA256SUMS)
# This helper verifies the remote exit marker because SDB transport success alone is insufficient.
cat > /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/run-board.sh <<'EOF'
#!/bin/bash
set -euo pipefail
export TMPDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/tmp
[[ $# == 1 && $1 =~ ^(prepare|install|check|rollback)$ ]] || exit 2
out=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/$1.out
sdb -s 192.168.108.26:26101 shell "sh /tmp/afdo_probe/$1.sh; rc=\$?; printf '\n__AFDO_RC__%s\n' \"\$rc\"; exit \"\$rc\"" > "$out" 2>&1 || { cat "$out"; exit 1; }
cat "$out"
tr -d '\r' < "$out" | grep -qx '__AFDO_RC__0'
EOF
cat > /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/scripts/prepare.sh <<'EOF'
#!/bin/sh
set -eu
export TMPDIR=/tmp/afdo_probe
fail() { echo "STOP: $*" >&2; exit 1; }
[ "$(id -u)" = 0 ] || fail 'root required'
case "$(tr -d '\000' < /proc/device-tree/model)" in 'Raspberry Pi 4 Model B'*) ;; *) fail 'not RPi4';; esac
[ "$(uname -m)" = armv7l ] || fail 'not armv7l'
[ "$(uname -r)" = 6.12.80-arm-rpi4-v7l ] || fail 'unexpected running kernel'
grep -q 'BUILD_ID=tizen-unified-toolchain_20261022.054557_' /etc/os-release || fail 'different image'
[ "$(awk '$2=="/" {print $1}' /proc/mounts)" = /dev/mmcblk0p2 ] || fail 'unexpected root partition'
case " $(cat /proc/cmdline) " in *' partition_ab=b '*) fail 'slot b is active';; esac
if rpm -qa --qf '%{NAME}\n' | grep -q '^arm-rpi4-rt-linux-kernel'; then fail 'RT packages installed; do not remove them automatically'; fi
for name in arm-rpi4-linux-kernel arm-rpi4-linux-kernel-modules; do
    [ "$(rpm -q --qf '%{VERSION}-%{RELEASE}.%{ARCH}' "$name")" = 6.12.80-0.armv7l ] || fail 'unexpected installed package'
done
for tool in tar sha256sum blkid mount umount awk grep tr dd nice ionice rpm; do command -v "$tool" >/dev/null || fail "missing $tool"; done
tar --help | grep -q -- --xattrs || fail 'tar cannot preserve module security xattrs'
[ "$(blkid -s TYPE -o value /dev/mmcblk0p1)" = vfat ] || fail 'p1 is not vfat'
label=$(blkid -s PARTLABEL -o value /dev/mmcblk0p1 || true)
case "$label" in ''|boot|boot_a) ;; *) fail 'unexpected boot partition label';; esac
bootdev=$(awk '$2=="/boot" {print $1}' /proc/mounts)
if [ -z "$bootdev" ]; then
    if awk '$1=="/dev/mmcblk0p1" {found=1} END {exit !found}' /proc/mounts; then fail 'p1 already mounted elsewhere'; fi
    mount -t vfat /dev/mmcblk0p1 /boot
else
    [ "$bootdev" = /dev/mmcblk0p1 ] || fail '/boot is not p1'
fi
awk '$2=="/boot" && $4 ~ /(^|,)rw(,|$)/ {ok=1} END {exit !ok}' /proc/mounts || fail '/boot is not writable'
# Resolve the GPT inform label like the packaged script, with its legacy p9 fallback.
inform_device=$(blkid -t PARTLABEL=inform -o device | grep '^/dev/mmcblk0p[0-9]*$' || true)
[ -n "$inform_device" ] || inform_device=/dev/mmcblk0p9
if [ -b "$inform_device" ]; then
    mkdir -p /tmp/afdo_probe/inform
    mount -o ro "$inform_device" /tmp/afdo_probe/inform
    trap 'umount /tmp/afdo_probe/inform' EXIT
    if [ -f /tmp/afdo_probe/inform/partition-ab.info ]; then
        [ "$(dd if=/tmp/afdo_probe/inform/partition-ab.info bs=1 count=1 2>/dev/null)" != b ] || fail 'next boot slot b'
    fi
    umount /tmp/afdo_probe/inform
    trap - EXIT
fi
printf '%s\n' \
 '0813526aeef267c3d92bd4c93605358f4e5424b28161528edd81caaa4de35d85  /boot/u-boot.bin' \
 'a1fb3849c26f8d0aabe99e60c1bb986c27db3d36f2162e6ad68fe67856eecdc6  /boot/uboot.env' \
 '8ba55683d6f53c04334e2abc8ccc23fd3d7a9eb2d5059c2d80f4b93cbbe985e9  /boot/boot.scr.uimg' | sha256sum -c -
[ -d /lib/modules/6.12.80-arm-rpi4-v7l ] || fail 'missing old module directory'
[ ! -e /tmp/afdo_probe/backup/COMPLETE ] || fail 'backup already exists; do not overwrite'
mkdir -p /tmp/afdo_probe/backup
cd /tmp/afdo_probe/backup
df -h /tmp /boot /
nice -n 19 ionice -c3 tar -C /boot -cpf boot.tar .
nice -n 19 ionice -c3 tar --xattrs --xattrs-include='*' --acls --numeric-owner -C / -cpf modules.tar lib/modules/6.12.80-arm-rpi4-v7l
blkid -s UUID -o value /dev/mmcblk0p1 > boot.uuid
blkid -s UUID -o value /dev/mmcblk0p2 > root.uuid
[ -s boot.uuid ] && [ -s root.uuid ] || fail 'missing UUID'
sha256sum /boot/zImage > old-zImage.sha256
if [ -f /boot/cmdline.txt ]; then sha256sum /boot/cmdline.txt > cmdline.sha256; else : > cmdline.sha256; fi
rpm -qa --qf '%{NAME} %{VERSION}-%{RELEASE} %{ARCH}\n' > packages.txt
cat /proc/mounts > mounts.txt
cat /proc/cmdline > running-cmdline.txt
uname -a > uname.txt
nice -n 19 ionice -c3 sha256sum boot.tar modules.tar boot.uuid root.uuid old-zImage.sha256 cmdline.sha256 packages.txt mounts.txt running-cmdline.txt uname.txt > SHA256SUMS
printf 'backup complete\n' > COMPLETE
EOF
cat > /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/scripts/check.sh <<'EOF'
#!/bin/sh
set -eu
export TMPDIR=/tmp/afdo_probe
[ "$(awk '$2=="/boot" {print $1}' /proc/mounts)" = /dev/mmcblk0p1 ]
[ "$(awk '$2=="/" {print $1}' /proc/mounts)" = /dev/mmcblk0p2 ]
if rpm -qa --qf '%{NAME}\n' | grep -q '^arm-rpi4-rt-linux-kernel'; then echo 'STOP: RT package detected'; exit 1; fi
printf '%s\n' \
 'a1cf2077f2053f2d779b39a0d9d7482bc636ecb38d5c07caf305fc0889207cd6  /boot/zImage' \
 '38a4959985ed44398e9656392c245b554155805808524fc04e556e31cc472925  /boot/config.txt' \
 '0813526aeef267c3d92bd4c93605358f4e5424b28161528edd81caaa4de35d85  /boot/u-boot.bin' \
 'a1fb3849c26f8d0aabe99e60c1bb986c27db3d36f2162e6ad68fe67856eecdc6  /boot/uboot.env' \
 '8ba55683d6f53c04334e2abc8ccc23fd3d7a9eb2d5059c2d80f4b93cbbe985e9  /boot/boot.scr.uimg' | sha256sum -c -
grep -qx 'kernel=u-boot.bin' /boot/config.txt
tr '\000' '\n' < /boot/uboot.env | grep -qx 'kernel=zImage'
if [ -s /tmp/afdo_probe/backup/cmdline.sha256 ]; then sha256sum -c /tmp/afdo_probe/backup/cmdline.sha256; else [ ! -e /boot/cmdline.txt ]; fi
[ -d /lib/modules/6.12.80-arm-rpi4-v7l ]
echo 'NORMAL-KERNEL-BOOT-CHECK OK (config -> U-Boot -> ordinary zImage; known slot-a layout)'
EOF
cat > /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/scripts/install.sh <<'EOF'
#!/bin/sh
set -eu
export TMPDIR=/tmp/afdo_probe
[ -f /tmp/afdo_probe/BACKUP_VERIFIED ]
[ -f /tmp/afdo_probe/backup/COMPLETE ]
cd /tmp/afdo_probe/new
sha256sum -c SHA256SUMS
nice -n 19 ionice -c3 rpm -Uvh --replacepkgs --test ./arm-rpi4-linux-kernel-6.12.80-0.armv7l.rpm ./arm-rpi4-linux-kernel-modules-6.12.80-0.armv7l.rpm
nice -n 19 ionice -c3 rpm -Uvh --replacepkgs ./arm-rpi4-linux-kernel-6.12.80-0.armv7l.rpm ./arm-rpi4-linux-kernel-modules-6.12.80-0.armv7l.rpm
sync
sh /tmp/afdo_probe/check.sh
EOF
cat > /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/scripts/rollback.sh <<'EOF'
#!/bin/sh
set -eu
export TMPDIR=/tmp/afdo_probe
[ "$(id -u)" = 0 ]
case "$(tr -d '\000' < /proc/device-tree/model)" in 'Raspberry Pi 4 Model B'*) ;; *) exit 1;; esac
[ "$(awk '$2=="/" {print $1}' /proc/mounts)" = /dev/mmcblk0p2 ]
bootdev=$(awk '$2=="/boot" {print $1}' /proc/mounts)
if [ -z "$bootdev" ]; then mount -t vfat /dev/mmcblk0p1 /boot; else [ "$bootdev" = /dev/mmcblk0p1 ]; fi
if rpm -qa --qf '%{NAME}\n' | grep -q '^arm-rpi4-rt-linux-kernel'; then echo 'STOP: RT package detected'; exit 1; fi
cd /tmp/afdo_probe/backup
nice -n 19 ionice -c3 sha256sum -c SHA256SUMS
[ "$(blkid -s UUID -o value /dev/mmcblk0p1)" = "$(cat boot.uuid)" ]
[ "$(blkid -s UUID -o value /dev/mmcblk0p2)" = "$(cat root.uuid)" ]
cd /tmp/afdo_probe/old
sha256sum -c SHA256SUMS
nice -n 19 ionice -c3 rpm -Uvh --oldpackage --replacepkgs --test ./arm-rpi4-linux-kernel-6.12.80-0.armv7l.rpm ./arm-rpi4-linux-kernel-modules-6.12.80-0.armv7l.rpm
nice -n 19 ionice -c3 rpm -Uvh --oldpackage --replacepkgs ./arm-rpi4-linux-kernel-6.12.80-0.armv7l.rpm ./arm-rpi4-linux-kernel-modules-6.12.80-0.armv7l.rpm
# Restore original custom configuration after restoring original package metadata.
nice -n 19 ionice -c3 tar --no-same-owner --no-same-permissions -C /boot -xf /tmp/afdo_probe/backup/boot.tar
nice -n 19 ionice -c3 tar --xattrs --xattrs-include='*' --acls --numeric-owner -C / -xpf /tmp/afdo_probe/backup/modules.tar
sha256sum -c /tmp/afdo_probe/backup/old-zImage.sha256
sync
echo 'ROLLBACK FILES RESTORED; reboot remains a separate user action'
EOF
# Syntax checks only; creating these files does not contact the board.
for script in /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/scripts/*.sh; do /bin/sh -n "$script"; done
/bin/bash -n /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/run-board.sh
