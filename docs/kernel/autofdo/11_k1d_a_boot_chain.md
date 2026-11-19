# K1d-a：PLAT 启动链核查与基准准备

截至 2026-11-18 22:24 PST，主机到 `192.168.108.26:26101` 的初始连接失败，K1d-a 板上阶段待完成。已归档设计 v0.2，复核了 K1a 启动链历史证据，并交叉编译了两个基准和静态 RESTART2 辅助程序。基于 `0fac5de6` 的源码，若实际重启使用 BCM2835 watchdog 回调，`0 tryboot` 的尾部关键字会被忽略。EEPROM 版本和实际重启路径仍待板上核查。

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
