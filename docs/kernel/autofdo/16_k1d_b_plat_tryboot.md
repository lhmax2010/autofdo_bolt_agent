# K1d-b：PLAT 副本固件直启

## 2026-11-19 PST 写入前核对

本节保留批准前的只读核对。批准和实机执行结果见下文。

本轮目标为 `192.168.108.26:26101`，DT serial `100000004694d889`，运行 `6.12.80-arm-rpi4-v7l`、build-id `395733b9c917cb98309b39cc3ec379c03ac36b3f`。当前 boot ID 为 `e3c3050e-86dd-4d6a-b452-bd08ebafd9c9`，DT 的 `tryboot=0`、`u-boot,version=2025.10-g136798fd1-TIZEN.org`，HDMI-A-1 已连接且显示栈在运行。现场原始 cmdline、FDT、分区挂载、模块与 dmesg 作为对照。运行 FDT SHA-256 为 `b8628c49d4876750f6faf09b1e1f338d8904485657c6c7ceb06397c2290672a2`。[核对原件](evidence/k1d-b-index.json)

| 核对项 | 结果 |
| --- | --- |
| 归档镜像 | boot_a SHA-256 `ec89fb505f4e3a49e35b2044ab19bb4dd69388a53a3bdf5d6e8384a725ab5c9d` 通过。离线逐文件重算 413 项 SHA，均与 K1d-a 清单相同。 |
| 现场清单 | `/dev/mmcblk0p1`、FAT UUID `404C-7537`、PARTUUID `8cf5ae0c-2697-2540-9e74-bfb6482324c0`。只读挂载采集的 415 个条目及 413 个文件 SHA 均与归档一致。核对后卸载，SDB 复核 UID 5001。 |
| FAT 容量 | 实测空闲 39,010,304 B，每簇 2,048 B。四个拟新增文件合计实占 22,544,384 B，预计剩 **16,465,920 B（15.70 MiB）**，通过 512 KiB 下限。两份主机候选配置落在同一簇大小。 |

## 新文件与配置范围

| 拟新增文件 | 字节 | 主机侧来源和 SHA-256 |
| --- | ---: | --- |
| `zImage-plat-direct` | 14,905,760 | 精确从归档 boot_a 提取，SHA 与现场 `zImage` 相同，为 `d5345f13eada3a3aab8b2fca9f511c608469f708d83a6a2445882e68241cc9af`。 |
| `initramfs-afdo.gz` | 7,632,283 | 逐字节匹配归档 `ramdisk_a` 的 gzip 成员，解压后与 K1d-a CPIO 相同。SHA 为 `ea6c57b47cce3427abcb820c4da7682be52e50e8ac6e9c3dc40c1be4ce235eaf`。 |
| `cmdline-afdo.txt` | 360 | K1d-a §7 已入库草案，SHA 为 `7a6915f4e2bd45a318f7f891dc2a1c0a6c37b87c4c8f175a8c1e03dcabba3917`。 |
| `tryboot.txt` | 1,790 / 1,802 | 主机候选各自从归档 `config.txt` 生成。严格三处变更版与增加 ARM32 行版的 diff 和 SHA 均已留档。 |

官方说明 RPi4 在默认模式下选择 64 位，已知标准内核名可影响自动选择。此 PLAT zImage 为 ARM32，自定义名 `zImage-plat-direct` 不属于标准命名。现有 `config.txt` 无显式 `arm_64bit`；现场普通路径成功运行 ARM32 U-Boot，不能由此确定固件将对该自定义 zImage 采用同一模式。K1d-a §7 的直启草案已提出 `arm_64bit=0`。本轮允许的 `tryboot.txt` 三项文本改动未列这行，已请求用户确认后再开始写入。[Raspberry Pi 启动配置](https://www.raspberrypi.com/documentation/computers/config_txt.html#arm_64bit)

目标板的 coreutils 6.9 的 `sync` 无文件参数，`mv` 也无 `-n`。已在主机用 Clang 22.1.8 准备仅用于写入步骤的辅助程序，分别调用 `fsync`、`renameat2(RENAME_NOREPLACE)` 和 `syncfs`。主机 QEMU 验证了文件同步、拒绝覆盖、成功发布和文件系统同步。板上计划在专用 tmpfs 自检，FAT 写入期间才临时 RW 挂载。尚未在板上执行辅助程序。[候选文件、工具和收据](evidence/k1d-b-index.json)

上述预检结束时，现场仍经 U-Boot 运行，启动分区尚未写入。

## 2026-11-19 PST 批准后执行

### 配置与写入

PM 批准仅在新 `tryboot.txt` 的 `[pi4]` 段加入 `arm_64bit=0`。写入前完整检查仍与归档匹配的 `config.txt`。检索 `arm_64bit`、`kernel`、`arm_control`，命中第 20 行的默认段注释 `# Use the kernel's default instead.`，以及第 52 行 `[pi4]` 的唯一有效相关设置 `kernel=u-boot.bin`。没有有效的 `arm_64bit` 或 `arm_control`。以下为完整配置差异，与拟写入文件逐字节比对通过。[检索和 diff 收据](evidence/k1d-b-index.json)

```diff
--- config.txt
+++ tryboot.txt
@@ -52 +52,4 @@
-kernel=u-boot.bin
+kernel=zImage-plat-direct
+cmdline=cmdline-afdo.txt
+initramfs initramfs-afdo.gz followkernel
+arm_64bit=0
```

首次执行发现板上缺少 `cmp`，在只读复核处退出，RW 挂载尚未发生。改用 `sha256sum` 比对同一组清单，从头重新完成只读门禁。空闲 39,010,304 B，按簇分配 22,544,384 B 后实测剩余 **16,465,920 B**。运行辅助程序前在 RAM tmpfs 验证了 fsync、拒绝覆盖、rename 和 syncfs。写入阶段对每项执行独占创建 `.tmp`、fsync、验证暂存 SHA、`RENAME_NOREPLACE`、syncfs、读回 SHA。RW 卸载后重新只读挂载并核对 417 个普通文件以及完整目录清单，413 个原文件全数匹配，只有以下四个新增。复核后卸载。任务暂存和来回取证使用 RAM tmpfs。[写入前后清单及挂载收据](evidence/k1d-b-index.json)

| 新增文件 | 字节 | RO 重挂验证 SHA-256 |
| --- | ---: | --- |
| `zImage-plat-direct` | 14,905,760 | `d5345f13eada3a3aab8b2fca9f511c608469f708d83a6a2445882e68241cc9af` |
| `initramfs-afdo.gz` | 7,632,283 | `ea6c57b47cce3427abcb820c4da7682be52e50e8ac6e9c3dc40c1be4ce235eaf` |
| `cmdline-afdo.txt` | 360 | `7a6915f4e2bd45a318f7f891dc2a1c0a6c37b87c4c8f175a8c1e03dcabba3917` |
| `tryboot.txt` | 1,802 | `31740c59d7cbf23ea3d3c6a3b8eebeb0660ad7646f05dea94091647f2cfa2c54` |

### PLAT 固件直启核对

21:10:56.806 PST 发出 `systemctl --no-block reboot '0 tryboot'`。收到退出 0 的提交回执后立即定向断开 SDB，随后每 10 秒定位目标并试读。**52.161 秒**得到首次新启动会话，恢复级别为自动，仅用了发出重启后的定向断开和常规轮询。未触发 120 秒补充断开或 180 秒主机恢复。新 boot ID 为 `dfb5031f-4797-4800-9e80-f3d85933d9b4`。内核 notes SHA 对应同一 PLAT build-id `395733b9c917cb98309b39cc3ec379c03ac36b3f`，DT bootloader `tryboot=1`，`u-boot,version` 属性消失。直启与原路径均为 `armv7l`，四个 CPU 的 `CPU architecture: 7` 原样匹配。[直接启动身份、架构及 SDB 回执](evidence/k1d-b-index.json)

- **cmdline**。草案中的 `bootmode=normal partition_ab=a`、串口、earlycon 和其余主要参数保留。固件在草案前加入 `coherent_pool=1M`、`cgroup_disable=memory`、`numa_policy=interleave`、`nvme.max_host_mem_size_mb=0`、`smsc95xx.macaddr`，以及若干重复的 UART、vc_mem 和音频参数。草案中的 `bcm2709.serial` 在现场 DT/内核 cmdline 中变成 `bcm2709.xxxxxx`，数值相同。DT `bootargs` 与 `/proc/cmdline` 仅结尾 NUL / 换行不同。dmesg 依次记录 memory cgroup 禁用和重新启用，`/sys/fs/cgroup/memory` 两条路径均已挂载。[cmdline 逐项差异与 dmesg](evidence/k1d-b-index.json)
- **FDT / initramfs**。U-Boot 对照 FDT SHA-256 为 `b8628c49d4876750f6faf09b1e1f338d8904485657c6c7ceb06397c2290672a2`，直启为 `b8564e4258c6c1a7fc59c825770f06cfddbd8999ea39b99f946f9667d37ee8e0`。U-Boot 的 initrd 范围为 `0x04700000–0x054ffe00`，直启为 `0x2e8b8000–0x2efff59b`，现场直启 initrd 长度 **7,632,283 B**，与所写 gzip 成员一致。dmesg 显示解包成功。[两份 FDT 和 initrd 证据](evidence/k1d-b-index.json)
- **启动稳定性**。rootfs 为槽 A 的 p2，两种路径的块设备分区挂载和选项一致，10 个模块的加载集合相同。对照完整启动日志，未检出新增 Oops、BUG、WARNING 或 panic 记录。采样时直启没有原路径已出现的两项 USB FunctionFS 挂载，`devtmpfs` 的容量和 inode 上限也不同。HDMI-A-1 已连接，display-manager 与 enlightenment 正常，eth0 保持 `192.168.108.26/24`，TCP SDB 正常。[模块、挂载及显示网络证据](evidence/k1d-b-index.json)

五分钟安静基线在原 governor `schedutil` 下完成。61 点覆盖 300.00 秒（启动 uptime 29.01–329.01 s），有 60 组前 5 进程收据。四核合计忙时中位数 **1.433%**、p90 **2.306%**、峰值 **3.668%**。首次观察到连续 30 秒低于 2.91% 的窗口在开机 uptime **109.02 s** 结束。两个温度传感器均为 54.530–58.426°C，中位数 55.504°C。按入榜累计 CPU ticks，前五为 `runner`、`bash`、`enlightenment`、`sugov:0` 和 `dlog_logger`。[五分钟原始采样和统计](evidence/k1d-b-index.json)

### 回到 U-Boot 路径与保留核对

21:16:52.833 PST 发出无参数的 `systemctl --no-block reboot`。收到退出 0 后定向断开，每 10 秒重连试读。**52.266 秒**首次取得新会话，恢复级别为自动。新 boot ID 为 `ae70026a-42df-4628-b9ae-9178012556b0`。内核 build-id 与原 PLAT 一致，`tryboot=0`，`u-boot,version=2025.10-g136798fd1-TIZEN.org` 恢复，原始 `/proc/cmdline` 逐字节一致。返回时 FDT SHA 为 `c848a3e266ed2470854dff23b212823dbb12dfb1964921bc23b9942e1991958e`，initrd 范围恢复到 `0x04700000–0x054ffe00`。HDMI、显示栈、eth0 和 ARM32 架构复核通过。[回程原件](evidence/k1d-b-index.json)

回程验收通过后，额外检查文件保留时遇到一次主机 SDB 会话丢失，ICMP 与 TCP 仍可达。常规重连取得同一 boot ID，无需再次重启板卡或主机 SDB 服务。随后再次只读挂载 boot_a，目录清单和 417 个文件 SHA 逐项匹配本轮写后清单，四个新增文件均保留，剩余空间仍为 **16,465,920 B（15.70 MiB）**。最终卸载，确认 UID 5001，governor 保持 `schedutil`，`kptr_restrict=0`。[保留核对和卸载回执](evidence/k1d-b-index.json)

**结论：K1d-b 通过。** 采用获准的 ARM32 `tryboot.txt` 结构完成同一 PLAT 的固件直启和 U-Boot 回程。两次重启均在 120 秒前取得新会话，未触发第二级或主机重启。未部署 K-BASE 或模块。
