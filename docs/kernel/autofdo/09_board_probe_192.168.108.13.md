# 第二块研究板只读探测（192.168.108.13）

2026-11-18，SDB 4.2.25。命令 `sdb connect 192.168.108.13:26101` 返回 `192.168.108.13:26101 is already connected`。`sdb devices` 确认 SDB 序列号 `192.168.108.13:26101`、状态 `device`，附加字段为 `0`。此后所有 shell 和 root 命令均显式指定该序列号。初次尝试把多项读取放入一条 shell 命令，SDB 返回 `error: service name too long`，将只读命令拆分后完成。原始输出和失败原文均保留。 [命令与原始字节记录](evidence/09-board-probe-192.168.108.13/commands-and-output.json) · [可读日志](evidence/09-board-probe-192.168.108.13/output.txt) · [SHA-256](evidence/09-board-probe-192.168.108.13/SHA256SUMS)

## 与 .25 对照

| 项目 | 192.168.108.13 | 192.168.108.25 |
|---|---|---|
| SoC、设备树根 | Novatek NT72671D，`novatek,nt72671d`、`nvt,ca53` | 同型号、同 compatible |
| CPU | Cortex-A53 r0p4，4 核，0–3 在线 | Cortex-A53，cpuinfo 枚举 4 核，原件的 variant/revision 同为 0/4 |
| 位宽 | 32 位 armv7l 内核，`/bin/sh` ELF32 | 32 位 armv7l 内核，Tizen 镜像标为 `arm`，报告 08 未检查 shell ELF |
| 内核与镜像 | 6.12.60，SMP PREEMPT，BUILD_ID `T-KSU2EJAKUC-0101-PERF-202611171009` | uname 构建串与 BUILD_ID 相同 |
| CoreSight / ETM | 无 CoreSight devices、无 `cs_etm`、无 ETM 或 sink 节点。硬件能力未知 | 同样未暴露，硬件能力未知 |
| PMU | `armv7_cortex_a7`，type 8，CPU 0–3，DT 指定四个 SPI | 同名，同 type。报告 08 未核对中断 |
| PMU 事件 | 30 个 sysfs 别名及编码 | 30 个别名的名称和编码逐项相同 |
| perf | PATH 和所查标准目录未发现 | PATH 与所查常见目录未发现 |
| 显示栈 | DRM LVDS 已连接且启用，未见常用合成器进程或 DRM HDMI 连接器 | 报告 08 未探测 |

两端点报告为同一 SoC 型号，运行相同镜像与内核构建。设备身份输出未提供可用于区分实物的唯一序列号，因而只能确认两次探测的型号与软件栈一致。ETM 硅片实现与 sink 连线均未知。当前镜像没有公开 CoreSight 采集链，板上 perf/OpenCSD 链也未验证。 [报告 08](08_board_etm_probe_192.168.108.25.md)

## 一、身份与内存

```text
Linux localhost 6.12.60 #1 SMP PREEMPT Mon Nov 16 20:15:36 UTC 2026 armv7l GNU/Linux
Tizen10/TV 10.0.0 (arm)
BUILD_ID=T-KSU2EJAKUC-0101-PERF-202611171009
online=0-3  present=0-3  possible=0-3
/bin/sh -> bash
7f 45 4c 46 01
MemTotal:        1601972 kB
```

ELF 第五字节 `01` 为 ELFCLASS32，与 `getconf LONG_BIT=32` 一致。CPU 实测如下，Arm implementer `0x41` 与 part `0xd03` 对应 Cortex-A53。内核源码中可用 `arch/arm64/include/asm/cputype.h` 的 `ARM_CPU_PART_CORTEX_A53` 和 `MIDR_CORTEX_A53` 交叉核对。

| CPU | implementer | part | variant | revision | 核心 |
|---|---|---|---|---|---|
| 0 | 0x41 | 0xd03 | 0x0 | 4 | Cortex-A53 r0p4 |
| 1 | 0x41 | 0xd03 | 0x0 | 4 | Cortex-A53 r0p4 |
| 2 | 0x41 | 0xd03 | 0x0 | 4 | Cortex-A53 r0p4 |
| 3 | 0x41 | 0xd03 | 0x0 | 4 | Cortex-A53 r0p4 |

普通权限下 Kernel code 和 Kernel data 的起止地址均显示为全零。经用户授权短时 root 读取后，以包含首尾字节的 `end − start + 1` 计算。

| /proc/iomem 项目 | 起止地址 | 大小 |
|---|---|---:|
| Kernel code | `040082c0-04833257` | 8,564,632 字节（8.168 MiB） |
| Kernel data | `04a34000-04ec8bc7` | 4,803,528 字节（4.581 MiB） |

## 二、CoreSight / ETM / PTM

- `ls /sys/bus/coresight/devices/` 返回 `No such file or directory`。event_source 只有 `armv7_cortex_a7`、`breakpoint`、`software`、`tracepoint`，没有 `cs_etm`。
- 设备树的 658 个目录名和 98 个节点的 compatible 均未出现 CoreSight、ETM、PTM、funnel、replicator、ETB、ETF、ETR、TMC、TPIU、STM 或 CTI 匹配。无对应节点的 reg 可报告。PMU 与 GIC 属性的原始字节在 `device-tree` 段。
- 普通权限和 root 的 `/proc/iomem` 摘录均没有标签匹配的 debug/trace 区域。普通权限下 `dmesg` 与过滤器均退出 0，当前 ring buffer 无 CoreSight/ETM/PTM 或 `hw perfevents` 匹配行。开机时的驱动探测日志和计数器数量未知。
- `/proc/config.gz` 不存在，`/boot/config-*` 无可见匹配。所请求的 CORESIGHT、PERF_EVENTS/HW_PERF_EVENTS、ARM_PMU、KALLSYMS、DEBUG_INFO、ARM_LPAE、STRICT_KERNEL_RWX、THUMB2_KERNEL 配置均未知。ARM64_PSEUDO_NMI 对本次 32 位内核不适用。debugfs 没有用于本轮取证。

## 三、PMU

`/proc/device-tree/pmu/compatible` 为 `arm,cortex-a7-pmu`。四个 CPU DT 节点均写作 `arm,cortex-a7`，而 cpuinfo 的硬件 ID 为 Cortex-A53。这一差异和 .25 相同。sysfs 的 CPU PMU 名为 `armv7_cortex_a7`，`type=8`、`cpus=0-3`、`format/event=config:0-7`。另三个 event_source 的 type 分别为 breakpoint 5、software 1、tracepoint 2。

根节点 `interrupt-parent` 的 phandle 1 指向 `/proc/device-tree/interrupt-controller@ffd00000`，compatible 为 `arm,cortex-a7-gic`，`#interrupt-cells=3`。PMU 的 interrupts 解码为 `<0 105 4> <0 106 4> <0 107 4> <0 108 4>`，四条电平触发 SPI。interrupt-affinity 为 `<0xc 0xd 0xe 0xf>`，分别对应 CPU0–3。GIC SPI 编号加 32 后得到硬件 IRQ 137–140，与 `/proc/interrupts` 的四行 `arm-pmu` 匹配。没有取得 NMI 声明或实测证据。

```text
41: 37095     0     0     0 GIC-0 137 Level arm-pmu
42:     0 36359     0     0 GIC-0 138 Level arm-pmu
43:     0     0 59130     0 GIC-0 139 Level arm-pmu
44:     0     0     0 47286 GIC-0 140 Level arm-pmu
```

| 事件别名 | sysfs 编码 |
|---|---|
| `br_retired` | 无同名项 |
| `pc_write_retired` | 0x0C |
| `inst_retired` | 0x08 |
| `cpu_cycles` | 0x11 |
| `br_mis_pred` | 0x10 |
| `br_immed_retired`、`br_return_retired`、`br_pred` | 0x0D、0x0E、0x12 |

`perf_event_paranoid=2`，`kptr_restrict=1`。以 UID 5001 读 `/proc/kallsyms` 返回 `No such file or directory`，无可报告的行数或零地址比例。没有导出符号内容。`which perf` 和 `command -v perf` 均退出 1，搜索标准 bin/sbin 目录也没有发现。版本与解码支持未知，未运行计数或采样。中断快照与 sysfs 别名只说明当前内核暴露的接口，A2 事件语义与实际计数待验证。

## 四、负载、显示与会话

`/sys/class/drm/card0-LVDS-1/status=connected`，`enabled=enabled`。可见的 DRM 连接器只有 LVDS，未找到 HDMI status。进程匹配未见 Enlightenment、Weston、Xorg/Xwayland 等，厂商合成器状态未知。没有可读的 `thermal_zone*/type` 与 `temp`，当前温度未知。cpufreq policy0 覆盖四核，`performance`，软硬件范围均 500–1350 MHz，读数 1350 MHz。

```text
 PID USER     %CPU %MEM COMMAND
  83 root      2.3  0.0 zram_bgrecompd
 513 root      1.7  0.0 PQ_MPFW_TASK
  31 root      0.9  0.0 ksoftirqd/2
  49 root      0.4  0.0 printk
 450 root      0.4  0.0 tzdev-tee-threads
 539 root      0.3  0.0 SCLR_DP0
3981 root      0.2  0.0 kworker/u32:2-vd_time_occupy_workqueue
1368 root      0.2  0.0 RTW_CMD_THREAD
 305 root      0.2  0.0 DRV_DBG_UART
 461 root      0.1  0.0 DRV_VD
```

上表为 `ps` 的进程生存期间平均 CPU 占用快照。`who` 退出 0、无输出。恢复 root 后读取板上 TCP 表，26101 端口只有 IPv6 表中的 1 条监听和 1 条已建立连接。这个快照能够确认当时的 SDB TCP 连接数，不能判定是否有其他客户端复用同一主机的 SDB 服务，也不能据此确认板子独占。

## 清理验证

`id -u` 初始为 5001。普通权限屏蔽 iomem 地址后，执行已授权的 `sdb root on`，验证 UID 0，只读一次 `/proc/iomem`。随即 `sdb root off` 返回 `Switched to 'sdk user' account mode`，即时及末次检查均为 UID 5001，governor 仍为 performance。所有命令通过 stdout 回收，板上临时目录的创建数及清理待办均为 0，原有 SDB 连接保留。SDB 或系统的内部日志写入未审计。 [清理记录](evidence/09-board-probe-192.168.108.13/cleanup.json)
