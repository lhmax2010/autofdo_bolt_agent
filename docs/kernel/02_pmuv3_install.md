# RPi4 armv7l 普通版 PMUv3：安装、备份与回退

本文件所有板上命令 **由用户执行**。Agent 只离线核验产物并编写步骤，未连接、安装或重启开发板。构建通过用户批准的替代证据验收，GBS 真实退出码未取得，原 status 保持不变，详见 [03_pmuv3_build_result.md](03_pmuv3_build_result.md)。以下命令写入启动分区/模块目录的授权仅用于用户执行安装和回退，不沿用此前“只允许 /tmp”的探测范围。

## 1. 安装范围与启动链

**只安装这两个包，不安装任何 rt 包，也不卸载 rt 包来“切换普通版”。** 如果发现已装 RT，预检停止：RT 的卸载脚本本身会移动启动镜像。不要使用 `*.rpm` 通配安装。

- `arm-rpi4-linux-kernel-6.12.80-0.armv7l.rpm`
- `arm-rpi4-linux-kernel-modules-6.12.80-0.armv7l.rpm`

devel、headers、perf、bpftool、debug 包均无需安装。新旧普通包 NEVRA 相同，使用 `--replacepkgs`。完整产物 SHA-256 在 03 文档；安装命令再次核对这两个包。

源码依据为本地内核提交 `c27f160de761bb55f64672ceac642698a6e93684` 的 `temp/linux-rpi-pmuv3/packaging/linux-rpi.spec`：

| 条目 | 路径/行为 | spec 行号 |
|---|---|---|
| 普通镜像 | 启动分区的 `/boot/zImage` | 364–370 |
| 板型 DTB | `/boot/bcm*.dtb`，含 bcm2711-rpi-4-b.dtb | 371 |
| DT overlays | `/boot/overlays/*.dtb*` | 372 |
| 启动配置 | **payload 直接覆盖 `/boot/config.txt`，不是 %config(noreplace)** | 373 |
| 固件/许可证 | `/boot/start*.elf`、`fixup*.dat`、LICENCE.broadcom | 374–376 |
| 模块及索引 | 根分区 `/lib/modules/6.12.80-arm-rpi4-v7l/` | 341–346 |
| 普通包脚本 | 两个普通包 `rpm -qp --scripts` 均为空；没有自己的 %post/%preun/%posttrans | 327–339 只有 RT 脚本 |
| RT %post | `mv /boot/zImage_rt /boot/zImage` | 327–332 |
| RT %preun | `mv /boot/zImage /boot/zImage_rt` | 334–339 |

因此普通包 **没有通过 %post 修改 config.txt/cmdline.txt 的动作**；但 config.txt 仍会被文件安装覆盖。cmdline.txt、boot.scr.uimg、uboot.env、u-boot.bin 不属于这两个普通包，安装时应保持不变。备份覆盖整个启动分区（包括这些文件及所有固件/DT），并单独备份完整普通模块目录。普通 kernel/modules 的新旧 RPM 文件列表逐字节相同，离线核验保存在 `temp/pmuv3-verify/filelists_equal.json`。

包内 `rpi/boot/config.txt:52` 为 `kernel=u-boot.bin`：固件先启动 U-Boot。为弄清下一跳，本轮另只读下载同镜像的 `u-boot-rpi4-32b-2025.10-0.armv7l.rpm` 到 `temp/pmuv3-verify/uboot/`，按快照元数据核对 SHA-256：`1eb7fc7779091716cea32fa15360a878189993c78b37f9fc01ca632710d7f225`。不安装这个包。其 `uboot.env` 明确 `kernel=zImage`；`boot.scr.uimg` 的脚本按 active slot 选择 boot 分区，再加载分区根目录的 zImage，以 `bootz` 启动。解出的文本证据 `temp/pmuv3-verify/uboot/boot.scr.txt:34`、`:219`–226，`uboot.env.txt` 的 kernel 行。

历史实机只确认根是 `/dev/mmcblk0p2`；本轮未读取实时挂载表。以下命令只允许 RPi4 armv7l、rootfs p2、boot p1（vfat）、slot a 的布局；运行时校验镜像/板型/挂载/已安装包以及 **同镜像 U-Boot 三个文件的哈希**。不同就明确失败，不猜分区或改启动链。若 /boot 尚未挂载，命令只将已识别的 p1 挂载到 /boot，不 remount 根分区。启用其他 slot 或自定义 U-Boot 的设备不适用这套自动步骤。

## 2. 本机准备部署目录和板上脚本（整块复制）

在本机 Bash 终端按顺序执行各代码块。全部主机产物留在 WORKDIR/temp，所有路径已固定。不要并行执行其他 RPM 更新或 FOTA；备份完成至本次验收期间保留这些文件。任一步失败就停止，不重启。

```bash
set -euo pipefail
export TMPDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/tmp
cd /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent
mkdir -p temp/pmuv3-install/new temp/pmuv3-install/old temp/pmuv3-install/scripts temp/pmuv3-install/backup
for name in arm-rpi4-linux-kernel arm-rpi4-linux-kernel-modules; do
    nice -n 19 ionice -c3 cp "temp/GBS-ROOT-RPI4-PMUV3/local/repos/tizen_unified_standard/armv7l/RPMS/$name-6.12.80-0.armv7l.rpm" temp/pmuv3-install/new/
    nice -n 19 ionice -c3 cp "temp/pmuv3-verify/baseline/$name-6.12.80-0.armv7l.rpm" temp/pmuv3-install/old/
done
cat > temp/pmuv3-install/new/SHA256SUMS <<'EOF'
832a0241990bab9162cfd9455efc687215af4222011eeb8cf64ed8671e3af18c  arm-rpi4-linux-kernel-6.12.80-0.armv7l.rpm
c08a11d4f624097a3619e31d4cb4dc6fa23965441ba66307e440cd01a76057f2  arm-rpi4-linux-kernel-modules-6.12.80-0.armv7l.rpm
EOF
cat > temp/pmuv3-install/old/SHA256SUMS <<'EOF'
c0282c7388fcaf020f6ec2bdee78191a22fbb2f4a1903378ca74bf8739f4da98  arm-rpi4-linux-kernel-6.12.80-0.armv7l.rpm
8234b9bea41af489d72777896ec7b6b8e0ec20312b178156242d8cc0fceae560  arm-rpi4-linux-kernel-modules-6.12.80-0.armv7l.rpm
EOF
(cd temp/pmuv3-install/new && nice -n 19 ionice -c3 sha256sum -c SHA256SUMS)
(cd temp/pmuv3-install/old && nice -n 19 ionice -c3 sha256sum -c SHA256SUMS)
# This helper verifies the remote exit marker because SDB transport success alone is insufficient.
cat > temp/pmuv3-install/run-board.sh <<'EOF'
#!/bin/bash
set -euo pipefail
export TMPDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/tmp
[[ $# == 1 && $1 =~ ^(prepare|install|check|rollback)$ ]] || exit 2
out=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/$1.out
sdb -s 192.168.108.26:26101 shell "sh /tmp/afdo_probe/$1.sh; rc=\$?; printf '\n__AFDO_RC__%s\n' \"\$rc\"; exit \"\$rc\"" > "$out" 2>&1 || { cat "$out"; exit 1; }
cat "$out"
tr -d '\r' < "$out" | grep -qx '__AFDO_RC__0'
EOF
cat > temp/pmuv3-install/scripts/prepare.sh <<'EOF'
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
cat > temp/pmuv3-install/scripts/check.sh <<'EOF'
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
cat > temp/pmuv3-install/scripts/install.sh <<'EOF'
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
cat > temp/pmuv3-install/scripts/rollback.sh <<'EOF'
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
for script in temp/pmuv3-install/scripts/*.sh; do /bin/sh -n "$script"; done
/bin/bash -n temp/pmuv3-install/run-board.sh
```

## 3. 用户连接、预检、备份并拉回主机

前一块未报错后执行。SDB serial 固定为历史确认的地址，prepare 仍按 model 验板。若连接地址已变，不猜其他设备。本段到备份校验完成为止没有安装 RPM。

```bash
set -euo pipefail
export TMPDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/tmp
cd /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent
sdb connect 192.168.108.26
sdb -s 192.168.108.26:26101 root on
sdb -s 192.168.108.26:26101 shell 'mkdir -p /tmp/afdo_probe/new /tmp/afdo_probe/old'
for script in prepare install check rollback; do sdb -s 192.168.108.26:26101 push "temp/pmuv3-install/scripts/$script.sh" "/tmp/afdo_probe/$script.sh"; done
/bin/bash /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/run-board.sh prepare
for file in boot.tar modules.tar boot.uuid root.uuid old-zImage.sha256 cmdline.sha256 packages.txt mounts.txt running-cmdline.txt uname.txt SHA256SUMS COMPLETE; do
    sdb -s 192.168.108.26:26101 pull "/tmp/afdo_probe/backup/$file" "temp/pmuv3-install/backup/$file"
done
(cd temp/pmuv3-install/backup && nice -n 19 ionice -c3 sha256sum -c SHA256SUMS)
nice -n 19 ionice -c3 tar -tf temp/pmuv3-install/backup/boot.tar > temp/pmuv3-install/backup/boot.list
nice -n 19 ionice -c3 tar -tf temp/pmuv3-install/backup/modules.tar > temp/pmuv3-install/backup/modules.list
printf 'host backup verified\n' > temp/pmuv3-install/BACKUP_VERIFIED
sdb -s 192.168.108.26:26101 push temp/pmuv3-install/BACKUP_VERIFIED /tmp/afdo_probe/BACKUP_VERIFIED
```

`prepare.out` 保存分区、包状态与备份结果；备份本体和校验和在主机 `temp/pmuv3-install/backup/`，重启后仍在。板上 /tmp 可能 noexec，所有脚本显式用 `sh 文件` 解释执行；不直接执行 /tmp 下的二进制。不要清理主机 temp，直至安装验收/回退完成。

## 4. 安装普通版，重启前确认

安装前需要 `/`、`/boot` 可写及足够空间；prepare 已打印空间，RPM 的 test 还会检查事务依赖与冲突。若权限/空间/冲突失败，不加 --nodeps/--force，不 remount 根来绕过，停止并保留输出。

```bash
set -euo pipefail
export TMPDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/tmp
cd /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent
for file in arm-rpi4-linux-kernel-6.12.80-0.armv7l.rpm arm-rpi4-linux-kernel-modules-6.12.80-0.armv7l.rpm SHA256SUMS; do
    sdb -s 192.168.108.26:26101 push "temp/pmuv3-install/new/$file" "/tmp/afdo_probe/new/$file"
done
/bin/bash /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/run-board.sh install
```

**安装后、重启前可单独复制的一条检查命令**（校验实际普通 zImage 哈希、完整新 config.txt、既有 U-Boot/环境/启动脚本哈希及 kernel=zImage；不能仅凭 uname -r，因为此时还运行旧内核）：

```bash
/bin/bash /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/run-board.sh check
```

只有输出 `NORMAL-KERNEL-BOOT-CHECK OK` 且 `__AFDO_RC__0` 才继续。prepare 至重启期间不能有人修改 slot/FOTA/U-Boot。本次不改 inform、ramdisk、root 启动参数，也不切换启动槽。

用户确认上述检查通过后自行执行重启（连接中断属于预期，重启命令的传输退出码不能作为内核验收）：

```bash
export TMPDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/tmp
sdb -s 192.168.108.26:26101 shell 'sync; rm -rf /tmp/afdo_probe; reboot'
```

## 5. 用户重启后的验收

等板启动后执行。不能仅凭 PMUv3=y 宣称真实硬件采样恢复；先验证新内核身份与 PMU 注册/绑定。

```bash
export TMPDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/tmp
sdb connect 192.168.108.26
sdb -s 192.168.108.26:26101 root on
sdb -s 192.168.108.26:26101 shell 'uname -r; uname -v; ls /sys/bus/event_source/devices/; ls -l /sys/bus/platform/devices/pmu/driver; dmesg | grep -i -E "pmu|perf.*event"'
```

应看到：

- `uname -r` 为 `6.12.80-arm-rpi4-v7l`，`uname -v` 为 **`#1 SMP Wed Oct 28 04:12:26 UTC 2026`**。
- 事件源包含 Cortex-A72 PMU（驱动的典型名称 `armv8_cortex_a72`）；sysfs pmu/driver 链接指向 `armv8-pmu`。
- 若新身份正确却未绑定，记录输出继续诊断 DT/中断/固件，不把这一构建验收当成板上功能已通过。perf 暂时不可用的问题保持独立。

## 6. 能启动且 SDB 可连接时的回退

同样只操作普通包。原始镜像 RPM 和启动/模块备份在主机，即使 /tmp 被重启清除也能恢复。旧 RPM 恢复包数据库内容，再恢复备份文件（包括用户原 config.txt/cmdline.txt/uboot.env 等定制），所以无须复制或回滚整套 RPM 数据库。

```bash
set -euo pipefail
export TMPDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/tmp
cd /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent
(cd temp/pmuv3-install/backup && nice -n 19 ionice -c3 sha256sum -c SHA256SUMS)
(cd temp/pmuv3-install/old && nice -n 19 ionice -c3 sha256sum -c SHA256SUMS)
sdb connect 192.168.108.26
sdb -s 192.168.108.26:26101 root on
sdb -s 192.168.108.26:26101 shell 'mkdir -p /tmp/afdo_probe/backup /tmp/afdo_probe/old'
sdb -s 192.168.108.26:26101 push temp/pmuv3-install/scripts/rollback.sh /tmp/afdo_probe/rollback.sh
for file in boot.tar modules.tar boot.uuid root.uuid old-zImage.sha256 cmdline.sha256 packages.txt mounts.txt running-cmdline.txt uname.txt SHA256SUMS COMPLETE; do
    sdb -s 192.168.108.26:26101 push "temp/pmuv3-install/backup/$file" "/tmp/afdo_probe/backup/$file"
done
for file in arm-rpi4-linux-kernel-6.12.80-0.armv7l.rpm arm-rpi4-linux-kernel-modules-6.12.80-0.armv7l.rpm SHA256SUMS; do
    sdb -s 192.168.108.26:26101 push "temp/pmuv3-install/old/$file" "/tmp/afdo_probe/old/$file"
done
/bin/bash /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/run-board.sh rollback
```

看到 `ROLLBACK FILES RESTORED` 与 `__AFDO_RC__0` 后，用户执行上面的重启命令。旧身份对照主机 `temp/pmuv3-install/backup/uname.txt`，不要期待旧内核也有 PMUv3。

## 7. 新内核无法启动时：SD 卡离线回退

关闭板电源，取出该 SD 卡接到本机读卡器。下面代码用备份记录的 UUID 找设备，要求两个分区尚未挂载；若桌面自动挂载导致停止，先在桌面安全卸载该卡的挂载，再重试。不会猜 `/dev/sdX`。此处 sudo 由用户在本机终端执行；挂载点/日志仍全部在 WORKDIR/temp。

```bash
set -euo pipefail
export TMPDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/tmp
cd /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent
(cd temp/pmuv3-install/backup && nice -n 19 ionice -c3 sha256sum -c SHA256SUMS)
boot_uuid=$(cat temp/pmuv3-install/backup/boot.uuid)
root_uuid=$(cat temp/pmuv3-install/backup/root.uuid)
boot_device=$(sudo blkid -U "$boot_uuid")
root_device=$(sudo blkid -U "$root_uuid")
[[ -b $boot_device && -b $root_device && $boot_device != "$root_device" ]]
[[ $(lsblk -ndo PKNAME "$boot_device") == "$(lsblk -ndo PKNAME "$root_device")" ]]
[[ $(cat "/sys/class/block/${boot_device##*/}/partition") == 1 && $(cat "/sys/class/block/${root_device##*/}/partition") == 2 ]]
if findmnt -rn -S "$boot_device" || findmnt -rn -S "$root_device"; then
    echo 'STOP: card partition already mounted; unmount it safely first' >&2
    exit 1
fi
mkdir -p temp/pmuv3-install/recovery/boot temp/pmuv3-install/recovery/root
sudo mount "$root_device" /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/recovery/root
sudo mount "$boot_device" /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/recovery/boot
sudo nice -n 19 ionice -c3 tar --no-same-owner --no-same-permissions -C /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/recovery/boot -xf /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/backup/boot.tar
sudo nice -n 19 ionice -c3 tar --xattrs --xattrs-include='*' --acls --numeric-owner -C /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/recovery/root -xpf /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/backup/modules.tar
expected_old=$(awk '{print $1}' temp/pmuv3-install/backup/old-zImage.sha256)
printf '%s  %s\n' "$expected_old" /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/recovery/boot/zImage | sha256sum -c -
sync
sudo umount /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/recovery/boot
sudo umount /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/recovery/root
```

若中途失败，保留挂载用于排查，不能拔卡。上述正常结束后取回 SD 卡装回板并启动。**离线步骤恢复了旧启动文件与模块，尚未恢复 RPM 的文件摘要元数据**；SDB 恢复后继续执行第 6 节，用原始普通 RPM 恢复数据库，再恢复备份定制。不要把离线启动成功等同于事务回退已全部完成。

## 验证边界

文档中的 Bash/远端 sh 片段做了静态语法检查；所有安装、挂载、回退、重启和 sysfs 验收均未经本轮实机执行。命令包含不匹配即停止的保护，用户不需要改路径或猜设备。主机没有运行这些片段，板上安装成败和硬件 PMU 能力最终以用户运行结果为准。
