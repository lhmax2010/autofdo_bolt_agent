# RPi4 armv7l 普通版 PMUv3：安装、备份与回退

用户最新授权：**Agent 执行脚本 01–04，停在重启前；用户手动重启并配置网络后，Agent 执行 05 验收和后续采样。任何失败立即停止，不做修复性操作。**构建通过用户批准的替代证据验收，GBS 真实退出码未取得，原 status 保持不变，详见 [03_pmuv3_build_result.md](03_pmuv3_build_result.md)。安装只允许指定普通内核及模块 RPM；备份写 /tmp/afdo_probe。禁止 remount、Agent 重启、--nodeps/--force 和 RT 安装/卸载。回退脚本仅准备，当前不授权自动执行回退。

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

## 脚本使用与结束标记

不要 source 脚本，也不要把 set -euo pipefail 粘贴到交互终端。下面每一条都启动独立 Bash；脚本内的失败不会退出父终端。每个脚本自带严格错误处理及 EXIT/信号 trap，结束时打印 `END <ISO 时间> OK` 或 `END <ISO 时间> FAILED <脚本/步骤>`，进程退出码保留失败状态。SIGKILL、断电、磁盘不可写不能由 trap 保证记录。

日志自动保存在 `/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/logs/`，按脚本名与时间命名；最近的结束标记另存 `<脚本名>.status`。板上真实退出码由 `__AFDO_RC__` 检查，不以 SDB 传输成功替代。每次联系板先按 device-tree model 认板。

原 prepare/install/check/rollback 四个板上脚本及 run-board.sh helper 按原文逐字保留，封装在 01 的 heredoc 中生成；主机路径改为绝对路径。四个板上脚本的适用条件、备份和安装逻辑没有调整。不要并行进行 RPM/FOTA/slot 更新；任一 END FAILED 就停止，不自动修复、重试或回退。

## 2. 本机准备：01_host_prepare.sh

复制新旧普通 kernel/modules 两个 RPM，核对四个 SHA-256，生成原板上脚本/helper 并做 bash -n/sh -n。正常看到四个包校验 OK 和最后 END OK；本步不连接板。

```sh
/bin/bash /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/scripts/pmuv3_install/01_host_prepare.sh
```

## 3. 连接、预检、备份：02_board_backup.sh

连接固定 SDB serial 192.168.108.26:26101、按 model 确认 RPi4，再推送原 prepare 等脚本。检查镜像、分区、slot、包、U-Boot 哈希和可写性；整个 boot、普通模块及元信息备份到板上 /tmp/afdo_probe/backup，再拉回主机 `temp/pmuv3-install/backup/`，逐项 sha256sum -c 并验证 tar 可读。只有全部成功才写 BACKUP_VERIFIED。**备份校验未全部通过不能执行 03。** 正常看到 __AFDO_RC__0、全部备份校验 OK 和 END OK。

```sh
/bin/bash /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/scripts/pmuv3_install/02_board_backup.sh
```

板上 /tmp 的 noexec 不妨碍显式 `sh 文件`；不在 /tmp 直接执行二进制。备份保留在主机，重启不丢失；在验收/回退完成前不要清理主机 temp。

## 4. 安装与重启前检查：03、04

03 首先重新核对主机备份 SHA-256 和 BACKUP_VERIFIED，再推送两个普通 RPM，依次执行 rpm --test 与 rpm --replacepkgs，最后调用原 check。正常看到包校验成功、RPM 事务成功、NORMAL-KERNEL-BOOT-CHECK OK、__AFDO_RC__0 和 END OK。失败不加 --force/--nodeps，不 remount。

```sh
/bin/bash /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/scripts/pmuv3_install/03_board_install.sh
```

04 是安装后、重启前独立检查：校验普通 zImage、新 config.txt、U-Boot/环境/启动脚本哈希，以及 `kernel=u-boot.bin` → `kernel=zImage` 和 cmdline 未变。此时 uname 仍是旧运行内核，不用它判断磁盘安装是否成功。

```sh
/bin/bash /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/scripts/pmuv3_install/04_board_check.sh
```

只有 04 输出 **NORMAL-KERNEL-BOOT-CHECK OK、__AFDO_RC__0、END OK**，才能通知用户“可以重启”。Agent 到此停止，绝不执行 reboot。用户自行重启并手动配置网络，然后通知“已重启并配好网络”。本文件不提供自动重启入口。

## 5. 用户通知后验收：05_board_verify_after_reboot.sh

未收到重启和网络就绪通知前不运行。打印 uname -r/-v、事件源、pmu/driver 链接与 dmesg PMU 摘录及各真实退出码。

```sh
/bin/bash /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/scripts/pmuv3_install/05_board_verify_after_reboot.sh
```

- 预期 release：6.12.80-arm-rpi4-v7l；version：**#1 SMP Wed Oct 28 04:12:26 UTC 2026**。不符输出 NEW_KERNEL_NOT_ACTIVE、END FAILED，整个任务停止，不回退、不采样。
- 身份正确且 driver 指向 armv8-pmu：输出 HARDWARE_PMU_REGISTERED、SAMPLING_SCOPE software+hardware、END OK；事件源通常出现 armv8_cortex_a72，随后执行软件与硬件采样。
- 身份正确但未绑定：输出 HARDWARE_PMU_NOT_RESTORED、SAMPLING_SCOPE software-only、END OK；此 OK 表示完成验收流程，**不表示硬件恢复**。只继续软件采样，不自动回退。

验收和采样最终分别记录于 docs/kernel/04_pmuv3_boot_verify.md 和 docs/probe/03_rpi4_sampling.md；尚未发生的结果不预填。

## 6. SDB 可连接时回退：06_rollback_online.sh（当前不执行）

仅在用户决定回退后执行。核对主机备份和旧普通 RPM，推回板；恢复原 RPM 元数据，再从备份恢复 boot 和模块（包含用户原配置）。不复制整套 RPM 数据库，不操作 RT。正常看到旧 zImage 哈希 OK、ROLLBACK FILES RESTORED、__AFDO_RC__0、END OK。旧内核身份对照主机 backup/uname.txt。

```sh
/bin/bash /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/scripts/pmuv3_install/06_rollback_online.sh
```

回退后重启也由用户执行，不包含于脚本。

## 7. SD 卡离线回退：07_rollback_sdcard.sh（当前不执行）

仅在用户决定离线回退后：断板电，SD 卡插入本机读卡器。按备份 UUID 确认同一张卡的 p1/p2；分区若已挂载则停止，用户先安全卸载。sudo 由用户在终端输入密码；挂载点仍在 WORKDIR/temp/pmuv3-install/recovery。恢复 boot 与模块，核对旧 zImage 哈希，正常完成后卸载并输出 END OK。失败保留挂载供排查，不能直接拔卡。

```sh
/bin/bash /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/scripts/pmuv3_install/07_rollback_sdcard.sh
```

此步只恢复启动文件和模块，尚未恢复 RPM 文件摘要元数据。SD 卡装回并恢复 SDB 后，继续 06 完成包数据库及备份定制恢复；所有重启均由用户执行。

## 验证边界与执行记录

7 个主机脚本通过 bash -n；四个原板上脚本通过 sh -n，helper 通过 bash -n，内容与重构前文档逐字相同。具体执行结果在本节和 STATUS 收尾时记录；安装成功不等于新内核已运行或采样已恢复。

### 2026-10-28 执行结果：02 预检失败，停止

| 脚本 | 实际结果 |
|---|---|
| 01_host_prepare.sh | 主机退出码 0；四个新旧普通 RPM SHA-256 全部 OK；`END 2026-10-28T15:39:52+08:00 OK` |
| 02_board_backup.sh | 主机退出码 1，远端退出码 1；`END 2026-10-28T15:40:02+08:00 FAILED 02_board_backup:line=57` |
| 03_board_install.sh | 未运行；没有结束标记 |
| 04_board_check.sh | 未运行；没有 check 输出或结束标记 |
| 05/06/07 | 未运行；没有验收、回退或重启 |

02 关键原始输出（仅规范 CRLF）：

```text
connecting to 192.168.108.26:26101 ...
connected to 192.168.108.26:26101
Switched to 'root' account mode
MODEL Raspberry Pi 4 Model B Rev 1.5
__AFDO_RC__0
[已推送原 prepare.sh、install.sh、check.sh、rollback.sh]
STOP: unexpected installed package
__AFDO_RC__1
END 2026-10-28T15:40:02+08:00 FAILED 02_board_backup:line=57
```

失败位置是原 prepare.sh 的已安装包预检：依次查询普通 kernel/modules 的 `%{VERSION}-%{RELEASE}.%{ARCH}`，要求严格等于 `6.12.80-0.armv7l`。原脚本不打印失败的包名或查询返回值，因此 **当前不能确定是哪个包、实际版本是什么、还是查询本身失败**。没有把这一报错推断为“架构错误”或“包缺失”，没有失败后追加板上查询。

失败发生在挂载/备份/安装之前：没有执行 mount、remount、备份 tar、RPM 安装或回退；仅切换 SDB root 模式、确认板型、创建 /tmp/afdo_probe/new 与 old 并推送四个脚本。按“失败立即停止并保留输出”，保留这些临时目录/脚本，未额外清理或重试。主机侧 **没有本轮板上备份，未进行备份 SHA-256 校验，没有 BACKUP_VERIFIED**；01 的 RPM 校验不能替代备份校验。不得运行 03/04，**当前不能通知用户‘可以重启’**。

完整主机日志：

- `temp/pmuv3-install/logs/01_host_prepare.20261028T153952+0800.log`
- `temp/pmuv3-install/logs/02_board_backup.20261028T153958+0800.log`
- 原远端输出：`temp/pmuv3-install/prepare.out`
- 结束标记：同日志目录下 `01_host_prepare.status`、`02_board_backup.status`。

语法检查再次通过；实际生成的四个板上脚本与重构前文档逐字相同。没有失败后修改脚本、配置或板上状态来绕过预检。需用户给出下一步指令后才继续。

边界例外：已有 SDB 服务的 `/tmp/sdb.log` 在本轮前后均为 400 bytes、mtime `2026-10-28 12:01:10.724948977 +0800`，没有删除或改动；无新增已知工作区外写入。比对记录在 `temp/pmuv3-install-refactor/boundary_before.txt` 与 `boundary_after.txt`，不是完整系统调用审计。用户显式提供的本轮附件仅用于读取指令，没有改动附件。
