# K1d-a：PLAT 启动链核查与基准准备

截至 2026-11-18 22:24 PST，主机到 `192.168.108.26:26101` 的初始连接失败，K1d-a 板上阶段待完成。已归档设计 v0.2，复核了 K1a 启动链历史证据，并交叉编译了两个基准和静态 RESTART2 辅助程序。基于 `0fac5de6` 的源码，若实际重启使用 BCM2835 watchdog 回调，`0 tryboot` 的尾部关键字会被忽略。EEPROM 版本和实际重启路径仍待板上核查。

第 6 节记录 RPi4 恢复连接后的现场证据，并修正第 3 节缺少固件 notifier 的推断。

## 1. 设计归档与连接门禁

- 实际输入文件为 `/home/linhao/Downloads/06_k1_design_v0.2.md`。原样复制到 [设计 v0.2](06_k1_design_v0.2.md)，Downloads 原件保留。SHA-256 为 `5c801324e3b863fb6a9d7de92ee56bfdf85d250ab35c1ac743d696fd32054ea3`，单文件提交 `a856ce07d370e6210f387a97f5a1b349cc23624a` 已推送 GitHub main。
- 22:17 PST 初检时，主机路由经 `192.168.107.1`，ICMP 2 次无响应，目标 TCP 26101 超时。22:18 起在五分钟窗口内重试 15 次。22:23:33 再做一次独立复核，TCP 仍超时（`timeout` 退出 124），SDB connect 打印 `failed to connect to remote target '192.168.108.26'`，其退出码为 0，但定向 shell 报 `target not found` / `serial number '192.168.108.26:26101' wrong` 并退出 1。见[证据索引](evidence/k1d-a-index.json)。
- 上次确认的板卡为 Raspberry Pi 4 Model B Rev 1.5，DT serial `100000004694d889`，PLAT `6.12.80-arm-rpi4-v7l`，GNU build-id `395733b9c917cb98309b39cc3ec379c03ac36b3f`。本轮未获得身份响应，尚不能确认板卡当前状态。SDB root、挂载、板上文件写入和重启命令均未执行。[K1a 基线及 HDMI 核对](04_k1a_baseline.md)

## 2. 启动分区、启动参数与 initramfs

本节基于 K1a 拉回的 `baseline-rpi4-02/board/source-identity/`，原始文件与本轮 SHA 对照见[证据索引](evidence/k1d-a-index.json)。

| 项目 | 历史证据 | K1d-a 待采证据 |
| --- | --- | --- |
| 启动分区 | `/dev/mmcblk0p1`，vfat，64 MiB，历史任务以 `ro,nosuid,nodev,noexec` 挂载；413 个普通文件有 SHA-256。归档 zImage SHA-256 为 `d5345f13eada3a3aab8b2fca9f511c608469f708d83a6a2445882e68241cc9af`，其内核 build-id 与历史运行内核一致。 | 现场块设备与 UUID、完整文件清单、全分区只读 `dd` 镜像及主板与主机 SHA。 |
| 模块分区 | `/dev/mmcblk0p6` 挂在 `/usr/lib/modules`，`crc7.ko` 的 vermagic 为 `6.12.80-arm-rpi4-v7l SMP mod_unload modversions ARMv7 p2v8`。有 52 个 `.ko` 的 SHA-256。 | PLAT 完整模块树清单，包含非 `.ko` 文件与符号链接。 |
| `config.txt` | 历史分区清单 SHA-256 为 `38a4959985ed44398e9656392c245b554155805808524fc04e556e31cc472925`，与 K1a BASE RPM 解包副本逐字节匹配。全文归档为 `config.k1a-matched.txt`。其中 `[pi4]` 指定 `kernel=u-boot.bin`、`vc4-kms-v3d-pi4,cma-320` 和 `dwc2,dr_mode=peripheral`，`[all]` 指定 `i2c1,pins_2_3`，另有 `auto_initramfs=1`。 | 现场 SHA 与全文。 |
| DTB / overlays | `bcm2711-rpi-4-b.dtb` 及上述三个 overlay 的文件 SHA 与 K1a BASE RPM 匹配。 | 运行中的 `/sys/firmware/fdt` SHA、实际应用的 overlay 和 U-Boot 设备树修改。 |
| U-Boot 配置 | 历史 `uboot.env` 与主机旧 Tizen U-Boot 包中的副本 SHA 相同，其中 `kernel=zImage`。历史 `u-boot.bin`、`boot.scr.uimg` 的 SHA 各自与该包的对应文件不同。 | 拉回现场 `boot.scr.uimg`，核对 mkimage 头、脚本内容和 bootargs 来源。 |
| `cmdline.txt` | 历史启动分区普通文件清单没有该文件。保存了历史 `/proc/cmdline`，见下。 | 现场是否存在及其全文，DT `/chosen/bootargs` 与 Linux `/proc/cmdline` 对照。 |
| initramfs | `auto_initramfs=1` 允许固件自动查找。旧 Tizen 包的 U-Boot 脚本也有从块区读 ramdisk、检查 gzip 再交给 `bootz` 的路径。由于脚本 SHA 不同，历史 PLAT 的 initramfs 加载状态未知。 | DT `linux,initrd-start/end`、启动日志及匹配的 initramfs 文件或块区内容，核对其 `lib/modules`。 |

K1a 历史 `/proc/cmdline`（保留内部空格）：

```text
cgroup_enable=memory vc_mem.mem_base=0x3ec00000 vc_mem.mem_size=0x40000000 swiotlb=8192 8250.nr_uarts=1 dma.dmachans=0x7f35 bcm2709.serial=0xed6687d3 snd_bcm2835.enable_compat_alsa=0 snd_bcm2835.enable_hdmi=1 bcm2709.uart_clock=48000000 dwc_otg.lpm_enable=0  bootmode=normal partition_ab=a console=ttyS0,115200n8 earlycon=uart8250,mmio32,0xfe215040 loglevel=4
```

K-BASE 的 release 为 `6.12.80-arm-rpi4-v7l-kbase`。若实际加载的 initramfs 内置 PLAT 模块且在切换根分区前需要加载它们，K-BASE 的模块查找路径和 vermagic 会不匹配。是否影响启动取决于实际早期加载的驱动及其是否编入内核。历史运行模块树位于独立挂载的 p6，这也需要和早期加载顺序区分。[K-BASE 构建记录](07_k1c_kbase_build.md)

## 3. EEPROM、RESTART2 与 tryboot

Raspberry Pi 官方定义了单次 tryboot 标记和 `0 tryboot` 参数。板上 EEPROM 版本、构建时间、固件对标记的处理，以及 Tizen 上 `reboot` / `systemctl reboot` 是否传递参数，本轮均没有实机证据。[Raspberry Pi tryboot 文档](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#fail-safe-os-updates-tryboot)

另外，`0fac5de6` 存在独立于用户态传参的内核侧问题。该提交的 `kernel/reboot.c:775–783` 将 RESTART2 字符串交给 `kernel_restart`，ARM 的 `arch/arm/kernel/reboot.c:132–137` 传给重启回调。若选中已编入主机构建 BASE 和 K-BASE 的 BCM2835 watchdog 回调，`drivers/watchdog/bcm2835_wdt.c:125–138` 只用 `sscanf(data, "%lu", …)` 解析分区号，随后 `101–112` 只写分区位。这个回调收到 `0 tryboot` 时会按分区号 0 处理。单纯绕过用户态命令无法补齐该回调缺失的逻辑。需以 PLAT 的实际重启处理器和固件证据确认；K1d-a 普通重启与后续 tryboot 分开判定。[源码摘录与构建配置索引](evidence/k1d-a-index.json)

主机已交叉编译 `reboot-restart2`。它使用 ARM EABI 直接调用 `reboot(2)`、`LINUX_REBOOT_CMD_RESTART2` 及字符串 `0 tryboot`。静态 ARM ELF 无解释器，已通过只读反汇编确认 syscall、参数寄存器和字符串。SHA-256 为 `2ff584c842960e347e6f7f2513204f59103805c1bd98688325c813e44dbc7863`。仅在主机归档，未部署或执行。[构建和反汇编索引](evidence/k1d-a-index.json)

## 4. PMU、重启和安静门禁

- 历史 K1a 已在 PLAT 使用 perf 6.12.80 的 `sched pipe`、`syscall basic` 与硬件 cycles。K1d-a 所需 A72 `events/` 目录和 `sched messaging`、`futex`、`epoll` 菜单仍待列出。[K1a 基线](04_k1a_baseline.md)
- 待测 raw 事件为 `r01`（L1I refill）、`r02`（L1I TLB refill）、`r08`（INST_RETIRED）、`r10`（BR_MIS_PRED）、`r0c`（PC_WRITE_RETIRED）、`r21`（BR_RETIRED）、`r11`（CPU_CYCLES）。名称对应 `0fac5de6` 的 `include/linux/perf/arm_pmuv3.h:17–49`。本轮七项均无计数，尚无法分类为有计数、恒零或不支持。[证据索引](evidence/k1d-a-index.json)
- PLAT 重启 **0/3 已发起**，当前阻塞发生在初始连接。没有新 boot ID、自动重连时间、HDMI 或显示栈确认，也没有 10 分钟开机后忙时及温度曲线。
- 安静门禁沿用 v0.2 §8.1：用相邻 `/proc/stat` 差分计算每 5 秒全板忙时，连续 30 秒低于阈值放行，最长 10 分钟。建议以每次重启后 10 分钟的后 5 分钟为稳定窗口，用三次等长窗口的合并中位数加预登记余量。安静门禁数值待实测，旧 HDMI 空闲温度不能替代这三次的忙时曲线。[设计 v0.2](06_k1_design_v0.2.md)

## 5. 新基准准备与待测项

使用 K1a 冻结 sysroot 内的 Clang/LLD 22.1.8 和 Tizen ARMv7 用户态运行库。Clang 编译 C 对象，LLD 显式接收 sysroot CRT 和库；汇编小程序由同版本 Clang 集成汇编器生成。两个基准均为 ARM EABI5 动态 ELF，子程序 `empty` 为静态 ARM ELF。构建脚本、源文件、ELF 及 SHA 在主机 `temp/kernel-afdo-k1/k1d-a/`，见[证据索引](evidence/k1d-a-index.json)。

| 基准 | 试运行输入与主机验证 | 板上结果 |
| --- | --- | --- |
| `mmfault` | 绑 CPU3，`mmfault 64 <reps>`；训练可用 `32`。匿名映射，每 4 KiB 写一次，解映射，报告墙钟和 minor faults。最后一轮逐页读回校验在计时外，末次解映射的用时单独计入，无休眠。QEMU 下 32 / 64 MiB 各 2 次迭代均通过校验。 | 待 PLAT 标定固定次数至约 10 秒。CV、启动间方差均待测。 |
| `forkexec` | 绑 CPU3，`forkexec <reps> <empty 的绝对路径>`，逐次 fork、execve、waitpid 并检查退出码。静态 ARM `empty` 单独在 QEMU 退出 0。QEMU 父进程执行宿主子程序通过，执行 ARM 子程序这条主机路径返回 3，ARM 组合仍待板上验证。 | 待 PLAT 标定固定次数至约 10 秒。CV、启动间方差均待测。 |
| pipe | CPU3，沿用 K1a 的 `perf bench sched pipe -l 500000`。 | 本轮无计时；CV、启动间方差待测。 |

恢复连接后，先核对 PLAT 身份并完成只读归档。每次正常重启后核对 boot ID 变化、build-id、HDMI 和显示栈，记录 10 分钟的全板忙时、温度和前 5 进程。首启每个基准先 1 轮预热加 10 轮计时，再进入三个启动各自的 1 轮预热加 3 轮计时。计时开窗前在 performance 下即时读取 ≤60°C，最高 80°C；切回 performance 后等 3 秒再核对。启动内 CV 用样本标准差除以均值，启动间初估用每启动三轮的几何均值并报告三组之间的 log 方差。只计真实 PLAT 轮次。任一实际重启后五分钟仍不能连接，则停止后续重启并报告现场处理。

## 6. 板上补做（2026-11-18 PST）

### PLAT 与启动链

22:55:46 PST 首次重连成功。进入 root 前核对 DT serial `100000004694d889` 与内核 release。测前身份为 RPi4 Rev 1.5、`6.12.80-arm-rpi4-v7l`、GNU build-id `395733b9c917cb98309b39cc3ec379c03ac36b3f`、boot ID `dcc453b3-4681-45a6-a182-9a312fcdd56b`。HDMI-A-1 为 connected，enlightenment PID 546。[现场原件索引](evidence/k1d-a-index.json)

| 项目 | 实机结果 |
| --- | --- |
| 启动分区备份 | `/dev/mmcblk0p1`（`boot_a`），FAT UUID `404C-7537`，PARTUUID `8cf5ae0c-2697-2540-9e74-bfb6482324c0`。在本任务目录以 `ro,nosuid,nodev,noexec` 挂载，`dd` 只读块设备。主机收到 67,108,864 B，板端和主机 SHA-256 均为 `ec89fb505f4e3a49e35b2044ab19bb4dd69388a53a3bdf5d6e8384a725ab5c9d`。已卸载并在发起重启前再次检查。413 个普通文件的 SHA 清单与 K1a 相同。 |
| 模块树 | `module_a` 的 p6 以只读方式挂载在 `/usr/lib/modules`。PLAT 树共 123 个条目（含目录及符号链接），73 个普通文件有 SHA-256。 |
| 启动脚本和配置 | 完整 `config.txt` SHA-256 为 `38a4959985ed44398e9656392c245b554155805808524fc04e556e31cc472925`，指定 `kernel=u-boot.bin`。FAT 无 `cmdline.txt`、无文件名为 `boot.scr` 的文件。实际脚本是 `boot.scr.uimg`，SHA-256 为 `fe89a9cd064da48b1207eb110b710362640842ed1c2a3e9f8cb360b3d4013122`。验证 mkimage header 和 payload CRC 后，剥离 64 B 头和脚本长度表，全文为 `boot.scr.decoded.txt`。 |
| U-Boot 与 bootargs | 运行 DT 记录 `2025.10-g136798fd1-TIZEN.org`。脚本拼接 `tizen_bootarg`、`rootargs`、`bootmode`、`partition_ab`、`console`、`opts`、`ip_opt`，并通过 `bootz` 传入 DT 和 initrd。现场 DT `chosen/bootargs` 与 `/proc/cmdline` 仅结尾 NUL / 换行不同，内容与 §2 历史记录一致。 |
| DTB 与 overlays | FAT 归档含 `bcm2711-rpi-4-b.dtb`，配置引用 FAT 中的 `vc4-kms-v3d-pi4`、`dwc2` 和 `i2c1`；脚本使用固件预载的 FDT。现场 `/sys/firmware/fdt` SHA-256 为 `e591ad4a342b4631acd1b18364a0578bc8d3f6d163b9ebba18757b5cf7017ff3`。 |
| initramfs | dmesg 显示已解包 initramfs 并释放 14,336 KiB。DT 范围 `0x04700000–0x054ffe00`。普通模式下脚本选择 `ramdisk_a`（`/dev/mmcblk0p7`），实机只读拉回的 gzip 解包为 14,679,552 B，等于 DT 区间长度。CPIO 123 条记录，只有空的 `usr/lib/modules` 目录，没有 `.ko`。已核对这份 initramfs 不携带 PLAT 模块，K-BASE 的启动仍需核对挂载 p6 后使用的 `-kbase` 模块树。 |

### tryboot 路径复核

**支持该内核调用路径，端到端 tryboot 留待另轮验证。** `0fac5de6` 的 `drivers/firmware/raspberrypi.c:186–222` 对含 `" tryboot"` 的重启参数置位 `0x1`，先通过 mailbox 发送 `RPI_FIRMWARE_SET_REBOOT_FLAGS`（`0x00038064`），再发送 `RPI_FIRMWARE_NOTIFY_REBOOT`。驱动 probe 设置 `g_pdev` 和 drvdata（384–385 行），初始化时注册 blocking reboot notifier（496–516 行）。`kernel/reboot.c:775–783` 接收 RESTART2 参数，`kernel_restart_prepare(cmd)` 先运行该 notifier（91–96 行），到 `machine_restart(cmd)` 才进入 ARM 的 restart handler 链并由 watchdog 写分区号。因此，同一次 RESTART2 可先请求固件标志再重启。§3 关于 watchdog 仅解析分区号的观察仍成立。mailbox 返回值被忽略，syscall 路径本身无法保证标志实际写入。[K 源码与实机证据](evidence/k1d-a-index.json)

- `CONFIG_RASPBERRYPI_FIRMWARE=y` 见 K defconfig 207 行及 K-BASE 构建 `.config` 1651 行。板上没有 `/proc/config.gz`。PLAT 的 `modules.builtin` 有 `kernel/drivers/firmware/raspberrypi.ko`，`/proc/modules` 无该模块，sysfs 显示驱动已绑定 `soc:firmware`，dmesg 记录连接到 2025-05-14T12:23:36 的固件。这些运行证据与 PLAT 驱动内建一致。[现场证据](evidence/k1d-a-index.json)
- EEPROM 版本为 `8ba17717fbcedd4c3b6d4bce7e50c7af4155cba9`，构建时间 2023-01-11 17:40:52 UTC，capabilities `0x7f`，当前 DT `tryboot=0`。该版本晚于 Raspberry Pi 4 EEPROM 引入 tryboot 的 2020-10-28，发布说明也记载了对应的 2023-01-11 镜像。板上未执行 tryboot，未部署 §3 的程序。[EEPROM 发布说明](https://github.com/raspberrypi/rpi-eeprom/blob/master/firmware-2711/release-notes.md)
- 板上 `reboot` 最终指向 `systemctl`（systemd 244），帮助列出 `reboot [ARG]`。实机 ELF 中兼容 `reboot` 和 `systemctl reboot` 路径均调用 `update_reboot_parameter_and_warn`，与上游 v244 的两处参数处理吻合。Tizen 的 `systemd-shutdown` 实际指向 `deviced-shutdown`。其 ELF 静态核查显示先读 `/run/reboot`，否则读 `/run/systemd/reboot-param`，对非空参数调用 ARM `syscall(88, …, 0xa1b2c3d4, param)`，即 RESTART2。由此确认安装版本有传参路径。实机只发出无参数的普通重启。[systemd v244 参数处理](https://github.com/systemd/systemd/blob/v244/src/systemctl/systemctl.c#L3337-L3340)、[兼容命令参数处理](https://github.com/systemd/systemd/blob/v244/src/systemctl/systemctl.c#L8053-L8059)、[实机 ELF 证据](evidence/k1d-a-index.json)

### A72 计数与 perf bench

使用 K1a 同一路径的 perf 6.12.80，SHA-256 `41b9b9a0d41da1b2a600c84ffa482ea05c52af54af094f5c6a2bf52d6aa13138`。CPU3 上执行 100,000 次 Bash 空循环，每组约 1 秒。七项同测与逐项单测均完成，记录的运行占比均为 100%。A72 PMU sysfs 为 `armv8_cortex_a72`，type 10，覆盖 CPU 0–3。事件可见性以 `drivers/perf/arm_pmuv3.c:268–297` 中的 PMCEID 位图为依据。[原始清单和计数](evidence/k1d-a-index.json)

| 事件 | 同测计数 | 单测计数 | sysfs 别名 |
| --- | ---: | ---: | --- |
| r01 | 5,879,746 | 7,567,223 | l1i_cache_refill |
| r02 | 349,754 | 891,665 | l1i_tlb_refill |
| r08 | 1,918,623,882 | 1,918,965,503 | inst_retired |
| r10 | 5,618,354 | 5,972,967 | br_mis_pred |
| r0c | 0 | 0 | 未列出 |
| r21 | 0 | 0 | 未列出 |
| r11 | 1,478,794,916 | 1,514,618,726 | cpu_cycles |

`r0c` 与 `r21` 的 raw 打开成功，但同测及单测均为 0，且相应别名未公开。后续机制计数可使用本轮有非零实测的五项。`perf bench` 菜单列出 sched 的 `messaging`、`pipe`、`seccomp-notify`，futex 的 `hash`、`wake`、`wake-parallel`、`requeue`、`lock-pi`，以及 epoll 的 `wait`、`ctl`。syscall 集合还列出 `basic`、`getpgid`、`fork`、`execve`。此步只枚举菜单。[perf 原始输出](evidence/k1d-a-index.json)

### 普通重启验收与基准状态

| 重启 | 发起时间（PST） | 验收 |
| --- | --- | --- |
| 1 | 23:01:08 | SDB shell 的主机等待在 8 秒时超时。随后 TCP 26101 在 23:02:52 一度可达，SDB 曾短暂列为 `unknown` / `offline`，未获得 shell 或新 boot ID。23:06:08 到达 300 秒上限，停止。 |
| 2、3 | 未发起 | 等待现场恢复。 |

普通重启 **1 次已发出，0/3 通过验收**。重启后 build-id、HDMI 与显示栈均未验证。第一次未到达空闲采集入口，三次 10 分钟曲线均未生成，**暂无可量化的安静门禁阈值**。后续仍以每次 10 分钟的后 5 分钟计算稳定窗口中位数，再加预登记余量。两项新基准及静态空子程序已部署到本任务目录并核对 SHA，未开始板上标定或计时。pipe、mmfault、forkexec 的有效轮数均为 0，开机内 CV 和启动间方差均无估计。[重连日志与任务程序](evidence/k1d-a-index.json)

第一次重启前已经卸载启动分区。未执行 tryboot，未写启动分区，未部署内核或模块，也未改变 governor（初始为 `schedutil`）或 `kptr_restrict`（初始为 0）。初始 SDB 为 owner，22:56 切换为 root 取证。300 秒时仍无可用 SDB 会话，`root off` 和板上任务目录清理待恢复连接后执行，当前 root 状态未知。请现场核对显示输出与 SDB 服务后再继续。

## 7. 续 2：PLAT 恢复、开机联网与直启容量（2026-11-18 PST）

### 恢复状态与时间线

现场确认后首次连接仍报 `failed to connect` / `target not found`。随后按用户指示，在主机重启 SDB server 并重试一次，立即得到 owner shell。主机 server 启动记录的端口为 26099，板端仍是 `192.168.108.26:26101`。序列号为 `100000004694d889`，新 boot ID 为 `6a5f0a9b-7d27-41cc-b3b7-1a17589408c7`，首次读取 uptime 为 2,204.02 s。运行 notes SHA 与 K1a 相同，对应 PLAT build-id `395733b9c917cb98309b39cc3ec379c03ac36b3f`。初次读取和末次复核均为 UID 5001（owner），root mode 已关，无需切换。[连接与时钟记录](evidence/k1d-a-index.json)

| 事件 | 实测时间 | 证据 |
| --- | --- | --- |
| 首次普通重启请求 | 主机 23:01:08 PST | §6 主机日志 |
| PLAT 内核启动 | 板钟 07:02:02 UTC | `/proc/stat` 的 `btime`，此后 boot ID 未变 |
| rootfs p2 挂载 | 开机 +3.163 s | dmesg |
| TCP SDB socket 开始监听 | 开机 +15.191 s | `sdbd_tcp.socket ActiveEnterTimestampMonotonic` |
| 恢复 Ethernet MAC 单元完成 | 开机 +16.713 s | `ethernet-mac-setup.service` |
| ConnMan ready、graphical.target active | 开机 +17.282 s、+18.001 s | systemd 单元时间戳 |
| eth0 载波 up | 开机 +19.845 s | dmesg |
| sdbd 进程开始、ready | 开机 +27.081 s、+27.130 s | systemd 单元时间戳 |
| 主机首次证实 TCP 连接成功 | 主机 23:02:52 PST，距重启请求 104 s | §6 主机 TCP 探测 |
| 主机首次证实可用 SDB shell | 主机 23:38:18 PST 发起 server 重启后，板钟读取 07:38:46 UTC | 主机启停与定向 shell 记录 |

末次比较时板钟快约 22.7 s。若启动后时差基本稳定，内核约在主机 23:01:39 PST 启动，graphical.target 约在 23:01:57 PST 已到达。跨钟估计不能替代主机的 104 s TCP 实测。没有获取到精确的 IPv4 配置时刻或第一个可用 SDB 协议会话时刻。owner 可读当前 dmesg 和 systemd 状态，但 journalctl 对当前及 `-b -1` 均报权限不足，上一 boot 的持久 journal 可用性未判定。[单元状态和时钟回执](evidence/k1d-a-index.json)

**失败最符合主机 SDB 传输状态异常。** 上轮在 104 s 已证明 TCP 可建立，SDB 仍一度显示 `unknown/offline`，到 300 s 也没有 shell。本轮不改板端状态，仅重启主机 server 就取得同一 boot 的正常会话。板端恢复机制有实际就绪证据，具体握手故障点缺少日志，不能把约 37 分钟的会话证据空档视为板端恢复时间。建议保留 **300 s** 的硬上限，加入 **180 s 传输诊断点**（本次观测的 104 s TCP 时刻加 76 s）。当 TCP 已通但 SDB 仍离线，记录状态并在拥有该主机 SDB 服务的前提下重建 server，再使用剩余时间完成身份验收。正式修改验收超时前，按三次正常重启实测的 SDB shell 最大值加 60 s 余量复核。三次测量尚未补做。

### 现有机制与主机准备工具

该板是 `Tizen11.0/Unified`，构建 `tizen-unified-toolchain_20261104.160709`，ConnMan 1.42、systemd 244、sdbd 3.0.50。读取的 unit 全文、命令输出、文件元数据与 SHA 原件已归档。[只读取证索引](evidence/k1d-a-index.json)

| 路径 | 已核实的作用 | 属主与修改时间（板本地 +0900） | SHA-256 |
| --- | --- | --- | --- |
| `/etc/systemd/system/ethernet-mac-setup.service` | 已启用的本机定制 oneshot。等待 eth0 设备，依次 down、设置 MAC `2c:cf:67:a0:72:b5`、up，并排在 ConnMan 之前。 | root:root，2026-11-10 17:52:18 | `f319a1842879a317e33006ed1ce8ae4d109c54bf09fecadb96e28c72be80b14c` |
| `/usr/lib/systemd/system/connman.service` | 由厂商 `multi-user.target.wants` 链接以及 Ethernet 单元拉起，运行 `connmand`。eth0 现场为 `192.168.108.26/24`，IPv4 lifetime 为 forever，默认网关 `192.168.108.1`。 | root:root，2026-11-05 02:11:08 | `cacfea2326511879e300770b6afb6b48ae01ef81124aecc156c647c3e39bd14a` |
| `/etc/connman/main.conf` | ConnMan 通用配置。找到持久有线条目 `/var/lib/connman/ethernet_2ccf67a072b5_cable`，owner 无权读内容和 SHA，ConnMan D-Bus 查询也超时。确切 IPv4 配置方式待确认。 | network_fw:network_fw，2026-11-05 02:11:09 | `82ca303bf7bd6bd97d2fbdbebe2dce566458897a47629025286bc8c090f7c03f` |
| `/usr/lib/systemd/system/sockets.target.wants/sdbd_tcp.socket` | 厂商链接指向 `../sdbd_tcp.socket`。`is-enabled` 的 disabled 状态无法反映此厂商链接，`sockets.target Wants=` 包含该项。 | root:root，2026-11-05 02:48:58 | 链接文本哈希见原件 |
| `/usr/lib/systemd/system/sdbd_tcp.socket` | `ListenStream=26101`，实机监听 `[::]:26101` 并接受 IPv4。服务为 `sdbd.service`，现有开发模式路径条件和 SMACK 设置保留。 | root:root，2026-11-05 02:48:58 | `90cb4b09782d55b12dc6e11fefd017273103a9349b034d4802c3d09a03b9b20a` |
| `/usr/lib/systemd/system/sdbd.service` | 以 sdk 用户和组运行 `/usr/sbin/sdbd $SDBD_CMDLINE`。无 socket/service drop-in，`/run/sdbd-env` 不存在。 | root:root，2026-11-05 02:48:58 | `5426f8a156a10f7900af1dd1d16f5e733d3378e98055b53e4b28ad59a497473d` |

当前无已列出的 timer。未取得可读的 vconf 值，现有 socket-activation 路径已经由 systemd 依赖和实测监听证实。

新增 [sdb-tcp-autostart](../../../tools/board/sdb-tcp-autostart/README.md)。`verify` 只读检查。离线 `install` / `uninstall` 默认预览，显式 `--apply` 才写入指定离线树。工具发现现有机制即保留，以新增的 ConnMan provisioning、绑定 IP/接口的厂商 socket drop-in 和 wants 链接完成 staging。安装在首个文件写入前记录每项原状态和新 SHA，原有路径保留，原先不存在的路径按清单回退和核验。主机 `sh -n`、Python 语法和 9 项单元测试通过。首次向板端内联整份脚本超出 SDB 命令长度，改为压缩后通过管道直接运行同一只读脚本，板上没有落盘。实机返回 `EXISTS: 192.168.108.26:26101 via eth0, boot-linked ConnMan and sdbd_tcp.socket`，退出 0。任何板上的 install/uninstall 均未运行。[测试与验收回执](evidence/k1d-a-index.json)

### boot_a 容量、initramfs 与 A/B 槽位

只读解析 §6 的 FAT16 镜像并与 `fsck.fat -n` 对照。总容量 67,108,864 B（64 MiB），簇大小 2,048 B，已有文件和目录使用簇 27,949,056 B，FAT 等固定区 149,504 B，空闲 **39,010,304 B（37.20 MiB）**。现有 413 个普通文件的完整大小收录于 `fat-space.json`。其中 `zImage` 14,905,760 B、`u-boot.bin` 808,272 B、`start4.elf` 2,264,064 B、DTB 56,450 B、`config.txt` 1,716 B、`boot.scr.uimg` 7,520 B、`uboot.env` 16,384 B。K-BASE 实测 zImage 为 **14,965,104 B**。估算 K-BASE-S、K-AFDO 暂以 K-BASE 大小，每个配置文本按一簇。[容量与文件大小原件](evidence/k1d-a-index.json)

| 新增组合（现有文件均保留） | FAT 实占 | 剩余 / 缺口 |
| --- | ---: | ---: |
| 四份直启 zImage、压缩 initramfs、两份配置 | 67,444,736 B | 缺 28,434,432 B |
| PLAT-direct、K-BASE、压缩 initramfs、两份配置 | 37,511,168 B | 余 1,499,136 B |
| 任意两份 K 变体，按 K-BASE 体量、共用压缩 initramfs 和两份配置 | 37,570,560 B | 估计余 1,439,744 B |
| 一份直启镜像，例如 K-BASE、压缩 initramfs、两份配置 | 22,603,776 B | 余 16,406,528 B |

最少同时新增一份本阶段所需的直启 zImage、共用压缩 initramfs、`tryboot.txt` 和 `cmdline-afdo.txt`。先验证 PLAT-direct，再切到 K-BASE。若正式 A/B 同时保留两份镜像，取得 K-BASE-S 与 K-AFDO 的实际大小后重新按簇计算，并计入写入期间可能同时存在的临时文件。两份 K-BASE 大小镜像再加一份解压态 CPIO 超出空闲容量。

`ramdisk_a` 是 p7，32 MiB。原件为开头 gzip、其后分区填充，gzip 成员为 **7,632,283 B**，解压为 **14,679,552 B** 的 newc CPIO。提取的主机归档 `initramfs-plat.cpio.gz` SHA-256 为 `ea6c57b47cce3427abcb820c4da7682be52e50e8ac6e9c3dc40c1be4ce235eaf`。CPIO 中 `/init` 指向 `sbin/init`，对应 `/usr/sbin/init` 脚本：[原件和完整 /init](evidence/k1d-a-index.json)

- 44–70、180–295 行读取 `bootmode` 与 `partition_ab`，用分区标签选 rootfs、module、hal 等。正常 slot A 将 p2 用作根分区。
- 403–529、1000–1040 行按条件执行 verity、fsck 和挂载。提前挂载模块分区，挂载 rootfs、system-data、hal，并准备模块、overlay 等。
- 962–983 行在 initramfs 路径下执行 `switch_root /sysroot /sbin/init`。沿用实机 bootargs 时没有 `root=`。K-BASE 启用 `CONFIG_CMDLINE_FROM_BOOTLOADER=y`，存在非空固件 cmdline 时不能依靠编译期默认 root 补齐。单加 `root=PARTUUID=4cef3024-c6de-5246-8603-d44bde2e6aae rootfstype=ext4 rootwait ro` 可给出内核根设备，但仍缺少这套 Tizen 早期挂载与检查，当前证据不足以放行无 initramfs 直启。
- 在主机草案中，以 `initramfs initramfs-plat.cpio.gz followkernel` 指向去掉填充的同一 gzip 成员。U-Boot 解 gzip 后传 CPIO，固件直启可传 gzip，K-BASE 的 `CONFIG_BLK_DEV_INITRD=y`、`CONFIG_RD_GZIP=y` 可解该格式。内核得到同一 CPIO 在内容上等价。仍需在后续授权启动核对 FDT 的 initrd 地址与大小、模块树、DTB/overlay 和显示网络。此轮未生成或写入板上配置。[Raspberry Pi initramfs 文档](https://www.raspberrypi.com/documentation/computers/config_txt.html#initramfs)

A/B 元数据确认 `boot_b=p11`（64 MiB）、`rootfs_b=p12`（3 GiB）、`module_b=p13`（32 MiB）、`ramdisk_b=p14`（32 MiB）、`ramdisk-recovery_b=p15`（32 MiB）及 `hal_b=p16`（256 MiB）。B 槽均未挂载，udev 没有给出文件系统标识。块设备权限为 0660、root:disk，owner 无法读取原始内容，B 槽是否空白及其 SHA 尚未确认。归档 `boot_a` 根目录没有 `autoboot.txt`，`boot_b` 是否有该文件未知。设计按同一 `boot_a` 内的 `tryboot.txt` 验证，不依赖 B 槽。[分区与镜像取证](evidence/k1d-a-index.json)

### cmdline-afdo.txt 草案

下面是一行，沿用现场 U-Boot 路径的 `/proc/cmdline`（去除行尾空格）。草案保留 `bootmode=normal partition_ab=a`，与上述 initramfs 配对。

```text
cgroup_enable=memory vc_mem.mem_base=0x3ec00000 vc_mem.mem_size=0x40000000 swiotlb=8192 8250.nr_uarts=1 dma.dmachans=0x7f35 bcm2709.serial=0xed6687d3 snd_bcm2835.enable_compat_alsa=0 snd_bcm2835.enable_hdmi=1 bcm2709.uart_clock=48000000 dwc_otg.lpm_enable=0  bootmode=normal partition_ab=a console=ttyS0,115200n8 earlycon=uart8250,mmio32,0xfe215040 loglevel=4
```

直启不经过 U-Boot 的变量拼接和 `bootz`。`tryboot.txt` 草案将指定 `cmdline=cmdline-afdo.txt`、ARM32 模式（`arm_64bit=0`）和显式 initramfs。固件可能自动添加部分参数，首次启动应逐项比对 `/proc/cmdline`，特别是重复的参数与串口。预期 FDT 不再有 U-Boot 写入的 `u-boot,version`，`linux,initrd-*` 可变化。保留原 DTB/overlay 和实测 FDT 的 SHA，核对到 ARM32 K-BASE 及后续变体共用的有效硬件配置。[Raspberry Pi config.txt](https://www.raspberrypi.com/documentation/computers/config_txt.html)

本轮板上操作仅为读取，未重启板卡。K1d-a 的剩余重启、安静门禁测量和基准轮次仍待进行，本轮不更改 v0.2 设计。
