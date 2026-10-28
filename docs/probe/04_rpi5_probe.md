# RPi5（aarch64）环境与采样能力探测

| 开发板/当前镜像 | perf | 软件采样 | 硬件 cycles | 硬件计数 | 分支栈 | SPE | ETM | BRBE | /tmp 可执行 | 部署目录可用空间 | root | H.264 软解 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RPi4 / 20261022.054557 | 支持（专用部署） | 支持 | 不支持，回退 cpu-clock | 未知，未实测 | 未知，03 未实测 | 未知，03 未实测 | 未知，03 未实测 | 未知，未实测 | 不支持，exit 126 | /opt 1.2G（当轮开始） | 支持 | 支持 |
| RPi5 / 20261027.063617 | 支持（专用部署） | 支持 | **支持，type 0 / config 0** | **四项均支持** | **不支持，exit 255** | **当前镜像不支持** | **当前镜像不支持** | 当前镜像不可用，硬件独立能力未知 | 不支持，exit 126 | /opt 1.3G（本轮开始） | 支持，uid 0 | 支持，两档 EOS |

日期：2026-10-28（Asia/Shanghai）。RPi4 一行仅引用 [03_rpi4_sampling.md](03_rpi4_sampling.md)，未连接或重测 RPi4，也不把其未测项目补成“不支持”。RPi5 以 model、架构及实际数据确认，SDB 的设备别名 rpi4 不作为板型依据。能力表是当前镜像可用性，不能把缺事件源等同于硅片永久没有该能力。

本轮不 remount、不重启、不安装/卸载 RPM、不改 /boot，不运行内核构建。原手工安装 PMUv3 方案保持取消。

## 证据与退出码口径

- **E15**：[15_rpi5_environment.txt](evidence/15_rpi5_environment.txt)：身份、资源、挂载全文、执行对照、PMU、静态配置。
- **E16**：[16_rpi5_perf_deployment.txt](evidence/16_rpi5_perf_deployment.txt)：快照与 RPM 校验、NEEDED、推送、依赖解析。
- **E17**：[17_rpi5_sampling.txt](evidence/17_rpi5_sampling.txt)：每次 perf/GStreamer 命令、真实退出码、stderr、报告摘录及统计。
- **E18**：[18_rpi5_elf_cleanup.txt](evidence/18_rpi5_elf_cleanup.txt)：实体库路径/哈希、完整 ELF 元数据、清理与 RPM 数量。

下文以 `E编号 / === key ===` 指向具体证据段。完整 JSON 在 WORKDIR/temp/rpi5-probe/，其中含未截断 stdout/stderr、命令和 wrapper。远端 shell 紧接命令保存 `$?`；SDB 传输返回码另列。建立 work 前及清理后使用 SDB 合并流，证据标注 combined；其余命令在 work 内分离捕获 stdout/stderr。perf 输出先完整捕获，再在本机展示所需行数，不以 head 的退出码代替 perf 状态。没有拉回 perf.data。

## 1. 身份、资源与部署目录

连接 `sdb connect 192.168.108.26` 成功；`sdb devices` 得 serial `192.168.108.26:26101`，设备别名仍为 rpi4。随后所有调用显式使用 `sdb -s 192.168.108.26:26101`。model 和 uname -m 均符合要求后才继续，`sdb root on` 返回 0，id -u 确认 0。

| 命令 | 关键输出 | 真实退出码/证据 |
|---|---|---|
| cat /proc/device-tree/model | Raspberry Pi 5 Model B Rev 1.1 | 0；E15 model |
| uname -m | aarch64 | 0；E15 arch |
| uname -r | 6.12.80-arm64-rpi4-v8 | 0；E15 release |
| uname -v | #1 SMP PREEMPT Tue Oct 27 08:04:21 UTC 2026 | 0；E15 version |
| cat /etc/os-release | Tizen 11.0.0；BUILD_ID=tizen-unified-toolchain_20261027.063617_tizen-headed-aarch64 | 0；E15 os |
| id -u | 0 | 0；E15 uid |
| cat /proc/cpuinfo | 四核；implementer 0x41、part 0xd0b；PMU 日志明确 cortex_a76 | 0；E15 cpu |
| free -m | total 3981 MB，available 3297 MB；swap total 1592 MB | 0；E15 memory |
| cat /proc/mounts | 全文保存，含 /、/opt、/tmp 等 | 0；E15 mounts |
| findmnt -T /opt -n -o TARGET,SOURCE,FSTYPE,OPTIONS | /opt /dev/mmcblk0p3 ext4 rw,relatime | 0；E15 opt_mount |
| findmnt -T /tmp -n -o TARGET,SOURCE,FSTYPE,OPTIONS | /tmp tmpfs tmpfs rw,nosuid,nodev,noexec | 0；E15 tmp_mount |
| df -h /opt /tmp | /opt 1.3G、used 23M、available 1.3G；/tmp 2.0G | 0；E15 space |

CPU Features 全文：`fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics fphp asimdhp cpuid asimdrdm lrcpc dcpop asimddp`。不从 Features 字符串单独推断 PMU、SPE 或 BRBE 支持。

/opt 是独立 ext4 挂载，rw 且不含 noexec；建立 `/opt/afdo_agent/tools/`、`lib/`、`work/`。拷贝 /usr/bin/true 到 work 并执行返回 **0**；拷贝到 `/tmp/afdo_true_noexec_control` 执行返回 **126 / Permission denied**。两次拷贝执行后立即删除，true_cleanup 验证成功。未使用替代挂载点；本轮只有这个已授权 /tmp 执行负对照写入该路径。

## 2. PMU 与追踪硬件

| 命令 | 关键输出/结论 | 退出码/证据 |
|---|---|---|
| ls /sys/bus/event_source/devices/ | armv8_cortex_a76、breakpoint、kprobe、software、tracepoint、uprobe | 0；E15 events |
| ls /sys/bus/coresight/devices/ | No such file or directory；当前没有 CoreSight 总线设备目录 | 2；E15 coresight |
| find -H /proc/device-tree -maxdepth 2（筛 pmu/etm/coresight/spe） | 只有 /proc/device-tree/arm-pmu；compatible=arm,cortex-a76-pmu；status 属性不存在 | 0；E15 dt_nodes（含完整查找/读取命令） |
| ls -l /sys/bus/platform/devices/*pmu*/driver | arm-pmu/driver → ../../../bus/platform/drivers/armv8-pmu | 0；E15 pmu_driver |
| ls /sys/bus/platform/drivers/ \| grep -i pmu | armv8-pmu | 0；E15 pmu_drivers |
| dmesg \| grep -i -E 'pmu\|perf\|spe\|brbe\|etm\|coresight' | hw perfevents: enabled with armv8_cortex_a76 PMU driver, 7 (0,8000003f) counters available | 0；E15 dmesg |
| cat /proc/sys/kernel/perf_event_paranoid | 2；本轮 root 执行 | 0；E15 paranoid |

DT 查找只覆盖指定 maxdepth 2，不声称全树没有其他深层节点。status 缺省不当作 disabled，实际 driver symlink 和采样进一步证明 PMU 已工作。dmesg 中 Spectre-v4、Spectre-BHB、Speculative、speed、SuperSpeed 等也是筛选命中，**不属于 SPE 探测成功证据**。事件源无 arm_spe / cs_etm，按任务跳过对应 record，结论为当前镜像不支持。分支栈实际失败，不能声称当前可用 BRBE；本轮未读取特权特征寄存器单独验证其硬件能力。

### 内核配置：静态核对，不能替代运行配置

`/proc/config.gz` 不存在/不可读，检查命令打印 unavailable、退出 2。按指令改查本地 `src/linux-rpi`，HEAD **42aeefac58edeb081aff440f0b60be71cbe49755**；本轮没有 fetch、make 或生成 .config。镜像 perf RPM 的源码 VCS 为 **51a7da74537e1ea4c2eb35865d5d00f170bc57cf**，与本地 HEAD 不同，进一步限制了静态推断范围。以下源码路径相对 WORKDIR/src/linux-rpi，行号原始保留于 E15：

| 项目 | arm64 tizen_bcm2711_defconfig 与 Kconfig 依据 | 静态结论 |
|---|---|---|
| ARM_PMUV3 | defconfig 无显式项；drivers/perf/Kconfig:146–149，default ARM64 | arm64 默认开启；不是运行 .config 直接读值 |
| HW_PERF_EVENTS | arch/arm64/Kconfig:1545–1547，def_bool y、depends ARM_PMU；drivers/perf/Kconfig:58–61 ARM_PMU default y；defconfig:34 PROFILING=y，init/Kconfig:1899–1902 PERF_EVENTS default y if PROFILING，arch/arm64/Kconfig:232 select HAVE_PERF_EVENTS | 静态依赖链满足；运行 PMU 另有实测证据 |
| ARM_SPE_PMU | defconfig 无显式项；drivers/perf/Kconfig:218–224，无 default y | 没有显式启用证据，不将其写成运行值 n |
| CORESIGHT | defconfig 无显式项；drivers/hwtracing/coresight/Kconfig:5–11，无 default y | 没有显式启用证据 |
| CORESIGHT_SOURCE_ETM4X | defconfig 无显式项；上述 Kconfig:100–104，select PID_IN_CONTEXTIDR | 没有显式启用证据 |
| ARM64_BRBE | rg -n ARM64_BRBE arch/arm64 drivers/perf 返回 1，无匹配 | 本地所查源码未定义该符号；不是运行配置 n |
| PID_IN_CONTEXTIDR | defconfig 无显式项；arch/arm64/Kconfig.debug:3–9，无 default y，ETM4X 可 select | 无显式启用，不推断最终配置 |
| KALLSYMS | defconfig 无显式项；init/Kconfig:1831–1833，default y | 静态默认 y，未取得运行配置 |

## 3. 同期 perf 和 libLLVM 部署

从 BUILD_ID 精确定位 Unified 20261027.063617，读取该快照 `build.xml:4` 得配套 Base **20261026.051209**。未使用 reference，也没有沿用 RPi4 的旧快照。仓库根如下：

- Unified：https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261027.063617/
- Base：https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261026.051209/

两个包均来自各自根下 `repos/standard/packages/aarch64/`。repomd/primary 下载成功，primary 压缩与解压校验通过；RPM SHA-256 与 primary 完全一致。完整 URL、哈希、下载状态和本机路径见 E16 REPOSITORY DOWNLOAD。下载/解包均在 WORKDIR/temp/rpms-aarch64/，以 nice -n 19 ionice -c3 执行；仅 rpm -qp 查询及 rpm2cpio | cpio 解包，未安装。

| RPM | 版本 | SHA-256 |
|---|---|---|
| linux-kernel-perf-6.12.80-0.aarch64.rpm | 6.12.80-0 | 84836e8c02f06f7d677ace5c80d5ebed52e750a293640c51e9fdf6ddd4ac8d1b |
| libllvm-22.1.8-1.5.aarch64.rpm | 22.1.8-1.5 | 36d45482feef227a78b513dd402f7db4cb7b4139c69db6c1e2bbf2ccfd8b5851 |

同 Unified 快照 `builddata/buildlogs/standard/aarch64/succeeded/linux-rpi.buildlog.txt:131` 显示 `keeping libllvm-22.1.8-1.5`，`:160` 为 llvm-devel-22.1.8-1.5，与下载的 libllvm **version-release 完全一致**。不是仅比对 SONAME。

`readelf -d temp/rpms-aarch64/perf-extract/usr/bin/perf` 列出的 NEEDED 全部见 E16 perf_needed。逐库在板上 /lib64、/usr/lib64、/lib、/usr/lib 查实体路径：唯一未发现的是 libLLVM.so.22.1，其他主程序依赖已存在。部署同期 libLLVM 后，`LD_DEBUG=libs perf --version` 退出 0，显示真实 init/transfer；ldd 退出 0、所有依赖解析，无 not found。libLLVM 的 libxml2.so.16、libbz2.so.1、libgcc_s.so.1 等也由板上既有库满足。没有下载额外缺失依赖。

perf 与 libLLVM 推送前计算本机 SHA-256，SDB push 后板上再次 sha256sum，均一致，结束保留文件再次校验。全过程没有使用 RPi4 的 armv7l 二进制。

所有 perf 调用均应用下列环境和完整命令前缀；下文 `P` 是该前缀的简写，E17 保存每次完整命令。这是已执行记录，work 现已清空。

```sh
export LD_LIBRARY_PATH=/opt/afdo_agent/lib
export HOME=/opt/afdo_agent/work/home
export TMPDIR=/opt/afdo_agent/work/tmp
export PERF_CONFIG=/opt/afdo_agent/work/perfconfig
export GST_REGISTRY=/opt/afdo_agent/work/registry.bin
export XDG_CACHE_HOME=/opt/afdo_agent/work/cache
# P：
nice -n 19 ionice -c3 /opt/afdo_agent/tools/perf --buildid-dir /opt/afdo_agent/work/buildid
```

PERF_CONFIG 是 work 下新建空文件；其他所需目录均已创建。LD_DEBUG 中先后出现 nice/ionice 的初始化也保留了，但依赖验收依据是最终 perf 初始化与 ldd 全部解析。

## 4. 采样能力实测

| 命令（P 如上；所有数据路径在 /opt/afdo_agent/work/） | 真实退出码、输出与实际事件 | 结论/证据 |
|---|---|---|
| P --version；P list sw；P list hw；P list pmu | 均 0；perf 6.12.80；cpu-clock 等软件事件、cycles/instructions 等硬件事件、armv8_cortex_a76 事件 | 支持枚举；E17 perf_version/list_* |
| P record -e cpu-clock -F 999 -a -o .../s1.data -- sleep 3 | 0；11,619 样本；evlist 0，type 1/config 0；report 0，Lost 0 | 软件采样支持；system_sw_* |
| P record -e cycles -a -o .../h1.data -- sleep 3 | 0；12,027 样本；evlist 0，**type 0 (PERF_TYPE_HARDWARE), config 0 (PERF_COUNT_HW_CPU_CYCLES)**；report 0，Lost 0 | 真硬件 cycles 支持；system_hw_* |
| P stat -e cycles,instructions,branches,branch-misses -- sleep 2 | 0；四项都有数字，无 not supported | 支持；stat |
| P record -e cycles -b -o .../b1.data -- sleep 1 | **255**；PMU Hardware or event type doesn't support branch stack sampling | 不支持；branch_record |
| P evlist -v -i .../b1.data | 255；zero-sized data, nothing to do | 失败后仍核对，未伪造事件属性；branch_evlist |
| SPE / ETM 条件实测 | 无 arm_spe/cs_etm 事件源，按指令跳过 record | 当前镜像不支持；E15 events/coresight |

每次实际 record 后都执行 evlist，包括失败的分支栈。成功的系统级记录均同时用 report 确认有样本，必要摘录为前 40 行。硬件 cycles 的 dummy 软件辅助事件不改变主事件确实为硬件 cycles 的结论。分支栈 record 失败且文件为零字节，因此没有执行 brstack 展示或媒体分支栈采样；不能声称存在 BRANCH_STACK 样本。SPE/ETM 没有触发最小实测，不将缺数据写成已测试的成功或失败退出码。

硬件 stat 原始计数：cycles **1,467,831**；instructions **1,645,084**；branches **392,144**；branch-misses **7,763**（1.98%）。elapsed=2.001473518s。这是 sleep 进程及启动退出开销的进程级计数，不是全系统两秒总数。

## 5. 真实 H.264 解码与开销

`command -v gst-launch-1.0` 和 `gst-inspect-1.0 avdec_h264` 均退出 0；avdec_h264 来自 /usr/lib64/gstreamer-1.0/libgstlibav.so。首次插件扫描有不影响此管线的警告，原样保留 E17 gst_inspect stderr；没有据此安装包。两个媒体从 WORKDIR/media 推到 work，本机与板上 SHA-256 一致：

| 文件 | SHA-256 |
|---|---|
| bbb_720p_h264_60s.mp4 | b5e116b9d01cec8e7f697041c53575d36bd96a5928e40faa69e731f9ae2d00a4 |
| bbb_1080p_h264_60s.mp4 | 31f72f11eb0566e0265358a14294e5dbddf13fce4ce1507d8872b04c2596a6da |

720p 基线连跑三次，1080p 跑一次，完整管线（1080p 替换对应文件名）为：

```sh
time -p nice -n 19 ionice -c3 gst-launch-1.0 filesrc location=/opt/afdo_agent/work/bbb_720p_h264_60s.mp4 ! qtdemux ! h264parse ! avdec_h264 ! fakesink sync=false
```

软件采样用 `time -p P record -e cpu-clock -F 999 -o /opt/afdo_agent/work/720p_sw.data -- 同一管线`；1080p 对应 1080p_sw.data。720p 硬件采样为 `time -p P record -e cycles -c 500009 -o /opt/afdo_agent/work/720p_hw.data -- 同一管线`。全部真实退出码为 0、管线到 EOS，完整命令/stderr 见 E17。

| 场景 | real 秒 | user 秒 | sys 秒 |
|---|---:|---:|---:|
| 720p 无 perf #1 | 8.39 | 18.59 | 0.38 |
| 720p 无 perf #2 | 8.35 | 18.76 | 0.36 |
| 720p 无 perf #3 | 8.52 | 19.15 | 0.33 |
| 1080p 无 perf #1 | 20.09 | 48.70 | 0.64 |
| 720p_sw | 9.18 | 18.73 | 0.44 |
| 720p_hw | 9.17 | 19.20 | 0.45 |
| 1080p_sw | 21.24 | 48.52 | 0.71 |

| 采样 | 基线 real 均值 | 基线最大−最小 | 采样 real | 观测开销 | 保存样本 | 丢失样本/比例 | 实际 type/config | -m 1024 重跑 |
|---|---:|---:|---:|---:|---:|---|---|---|
| 720p_sw | 8.42s | 0.17s | 9.18s | +9.03% | 18,940 | 0 / 0.00% | 1/0 cpu-clock | 未触发 |
| 720p_hw | 8.42s | 0.17s | 9.17s | +8.91% | 91,979 | 0 / 0.00% | 0/0 cycles | 未触发 |
| 1080p_sw | 20.09s | 0.00s | 21.24s | +5.72% | 48,968 | 0 / 0.00% | 1/0 cpu-clock | 未触发 |

开销公式为 `(带 perf real / 同分辨率无 perf real 均值 − 1) × 100%`。1080p 只有一个基线，其范围 0 不代表没有随机波动。所有系统和媒体成功记录的 report Lost Samples 都是 0；分支记录失败没有有效样本，丢样比例不适用。没有一项超过 1%，所以按规则没有使用 -m 1024 重跑，也没有继续调参。测量未锁定频率或关闭桌面后台负载，以上是本轮观察值，不能直接视为稳定常数；两块板镜像不同，不把与 RPi4 的耗时差当作严格硬件 A/B。

### DSO 与符号统计方法

每个媒体采样执行 `P report --stdio --sort dso -i 数据文件`（展示前 30 行）和 `--sort dso,sym`（前 40 行）；再执行 `--sort dso,sym --show-nr-samples --percent-limit 0 --field-separator ';'`。三种 report 均退出 0。汇总完整输出的样本计数，合计分别为 18,940、91,979、48,968；下表百分比是 **DSO 样本数/保存总样本数**，不是默认按 period 加权的 Overhead，避免只按前若干行估算。

### 720p_sw：前 10 DSO

| DSO | 样本数 | 占比 |
|---|---:|---:|
| libavcodec.so.62.11.100 | 15,077 | 79.6040% |
| libc.so.6 | 2,920 | 15.4171% |
| [kernel.kallsyms] | 413 | 2.1806% |
| libgstreamer-1.0.so.0.2411.0 | 140 | 0.7392% |
| libavutil.so.60.8.100 | 121 | 0.6389% |
| libgstbase-1.0.so.0.2411.0 | 47 | 0.2482% |
| libgstlibav.so | 42 | 0.2218% |
| libgstvideo-1.0.so.0.2411.0 | 34 | 0.1795% |
| libglib-2.0.so.0.8000.5 | 31 | 0.1637% |
| libgobject-2.0.so.0.8000.5 | 29 | 0.1531% |

### 720p_hw：前 10 DSO

| DSO | 样本数 | 占比 |
|---|---:|---:|
| libavcodec.so.62.11.100 | 73,520 | 79.9313% |
| libc.so.6 | 14,277 | 15.5220% |
| [kernel.kallsyms] | 1,795 | 1.9515% |
| libavutil.so.60.8.100 | 598 | 0.6501% |
| libgstreamer-1.0.so.0.2411.0 | 522 | 0.5675% |
| libgstbase-1.0.so.0.2411.0 | 235 | 0.2555% |
| libgstvideo-1.0.so.0.2411.0 | 201 | 0.2185% |
| libgstlibav.so | 185 | 0.2011% |
| libgobject-2.0.so.0.8000.5 | 160 | 0.1740% |
| libglib-2.0.so.0.8000.5 | 128 | 0.1392% |

### 1080p_sw：前 10 DSO

| DSO | 样本数 | 占比 |
|---|---:|---:|
| libavcodec.so.62.11.100 | 40,639 | 82.9909% |
| libc.so.6 | 6,821 | 13.9295% |
| [kernel.kallsyms] | 776 | 1.5847% |
| libavutil.so.60.8.100 | 193 | 0.3941% |
| libgstreamer-1.0.so.0.2411.0 | 175 | 0.3574% |
| libgstbase-1.0.so.0.2411.0 | 62 | 0.1266% |
| libgstvideo-1.0.so.0.2411.0 | 54 | 0.1103% |
| libgstlibav.so | 48 | 0.0980% |
| libgobject-2.0.so.0.8000.5 | 42 | 0.0858% |
| libgstisomp4.so | 39 | 0.0796% |

### 目标库符号解析

“有名称”排除纯十六进制地址和 unknown，包括 PLT；PLT 与非 PLT 再分开计数，不把 PLT 入口当作解码器内部函数。统计以完整 counted 输出的每行样本数加权，单位是样本，不是符号个数。

| 采样/库 | 库内总样本 | 有名称 | 其中 PLT | 非 PLT | 未解析 | 有名称比例 |
|---|---:|---:|---:|---:|---:|---:|
| 720p_sw / libavcodec.so.62.11.100 | 15,077 | 29 | 13 | 16 | 15,048 | 0.1923% |
| 720p_sw / libgstlibav.so | 42 | 19 | 19 | 0 | 23 | 45.2381% |
| 720p_hw / libavcodec.so.62.11.100 | 73,520 | 123 | 80 | 43 | 73,397 | 0.1673% |
| 720p_hw / libgstlibav.so | 185 | 74 | 74 | 0 | 111 | 40.0000% |
| 1080p_sw / libavcodec.so.62.11.100 | 40,639 | 44 | 28 | 16 | 40,595 | 0.1083% |
| 1080p_sw / libgstlibav.so | 48 | 17 | 17 | 0 | 31 | 35.4167% |

libgstlibav 的有名称样本全部为 PLT，三次采样都没有可辨的非 PLT 内部函数样本。libavcodec 绝大多数仍为地址。DSO 归属可用，但当前 strip 文件不足以做完整内部函数热点/源码行归属。所有有名称符号及计数保留在 E17 的 DERIVED STATISTICS；原始全量 counted 输出在 temp/rpi5-probe/*_counted.json。

## 6. BOLT / AutoFDO 二进制前提

按任务只读 ELF 元数据；本轮未建立/使用 aarch64 GBS root，使用**本机 readelf**，没有反汇编或执行这些库。先在板上 readlink -f 确认实体路径，再 sdb pull 到 WORKDIR/temp/board_libs/rpi5/，板上/本机 SHA-256 相等。命令为各文件的 `readelf -h`、`-SW`、`-n`、`-p .comment`、`-d`；均返回 0，但 .comment 不存在时 readelf 会在 stderr 警告，不能只看退出码说段存在（E18）。

| 实体文件 | 大小 B | ELF 类型/架构 | .comment / 编译器、链接器 | build-id | .symtab / strip | 代码重定位 | PIC 判断 |
|---|---:|---|---|---|---|---|---|
| /usr/lib64/gstreamer-1.0/libgstlibav.so | 269,008 | ELF64、DYN 共享对象、AArch64 | 不存在 / 未知 | 无 | 无 / 已 strip，仅 .dynsym | 无 .rela.text 等代码重定位；有 .rela.dyn/.rela.plt | 与 PIC 共享对象相符；无 TEXTREL，不能反推编译开关 |
| /usr/lib64/libavcodec.so.62.11.100 | 5,085,584 | ELF64、DYN 共享对象、AArch64 | 不存在 / 未知 | 无 | 无 / 已 strip，仅 .dynsym | 无 .rela.text 等代码重定位；有 .rela.dyn/.rela.plt | 与 PIC 共享对象相符；无 TEXTREL，不能反推编译开关 |
| /usr/lib64/libgstreamer-1.0.so.0.2411.0 | 1,321,664 | ELF64、DYN 共享对象、AArch64 | 不存在 / 未知 | 无 | 无 / 已 strip，仅 .dynsym | 无 .rela.text 等代码重定位；有 .rela.dyn/.rela.plt | 与 PIC 共享对象相符；无 TEXTREL，不能反推编译开关 |

这三个文件的 readelf -n 均无 build-id，段表也无相应 note；没有 .debug_line 等 DWARF 调试段。`.rela.dyn`/`.rela.plt` 是动态重定位，不能代替链接器为 BOLT 保留的代码重定位。DYN+SONAME 和没有 DT_TEXTREL 支持其作为位置无关共享库加载，但仅凭元数据无法证明每个输入对象都使用了 -fPIC。

**现有文件不能直接作为本项目可验证的 BOLT 优化输入**：缺完整符号表，函数重排所需的代码重定位也未保留；本轮没有运行 llvm-bolt 来虚构动态验收。Agent 自己构建时需要：

- 保留完整未 strip 的匹配二进制和符号表（不得 strip-all）；最终链接增加 `-Wl,--emit-relocs`，检查 `.rela.text` 等代码重定位实际存在。必要时单独保留未剥离产物，再制作分发包。
- 为构建与 profile 匹配显式保留 build-id（例如 `-Wl,--build-id=sha1`），记录二进制 SHA-256；build-id 是关联与验证措施，不把它单独称为 BOLT 唯一硬性条件。
- 共享库保持位置无关代码构建，例如 `-fPIC`；保留调试信息/源码行映射供分析，不能从当前 .comment 缺失猜测链接器。
- 普通 cycles 采样成功不等于分支 profile 可用。本轮没有 brstack/SPE/ETM，不能承诺分支驱动的 BOLT/AutoFDO 流程已就绪。本地 BOLT 文档描述无 brstack 的 perf2bolt `-ba` 路径，但本轮未验证工具可用性、aarch64 转换效果或优化收益。

依据为 WORKDIR/src/llvm/bolt/README.md:13–14、:119–124、:190–205（E18 保存摘录）：符号表、--emit-relocs 与非 brstack 处理要求。

**AutoFDO/LLVM SamplePGO**：当前板上库没有足够源码行信息，单靠这些 strip 文件与本轮 IP 样本不能完成可靠的源码行 profile 映射。Agent 构建时保留精确匹配的 DWARF，例如 `-gline-tables-only -fdebug-info-for-profiling -funique-internal-linkage-names`；若选 pseudo-probe 路径，需统一使用 `-fpseudo-probe-for-profiling` 并核验匹配的转换工具。依据 WORKDIR/src/llvm/clang/docs/UsersManual.rst:2815–2851（E18）。是否生成可消费 profile、是否需要某种事件/调用栈或分支轨迹，要按选定生成器验证；本轮没有生成 AutoFDO/BOLT profile 或优化编译。

实体文件哈希：

| 文件 | SHA-256 |
|---|---|
| libgstlibav.so | a3a87fcad461b83f9d75c5556da2caa172626aad17d92ae10406011aedaab671 |
| libavcodec.so.62.11.100 | 58bbcd7f1e14fd55590cbee15f58d10ebe02c66139c75c0c9ae8b871b7635455 |
| libgstreamer-1.0.so.0.2411.0 | bee5bb0d6e5cb0bf79d4b2596d7bf896783fe577c795b2f24205ed66124cd273 |

## 7. 清理、保留与边界

实际执行 `nice -n 19 ionice -c3 find /opt/afdo_agent/work -mindepth 1 -delete`，随后 test 验证无条目，ls 仅有 . / ..，退出 0。视频、perf.data、registry、cache、临时 stdout/stderr、perfconfig 等全部删除；/tmp 执行负对照文件最终也确认不存在。没有拉回采样数据；拉回的三个库只留在本机 temp/，不提交。

RPM 列表读取先检查 rpm 自身返回 0，再计行；开始与结束均 **1,249**。本轮没有运行任何 RPM 安装/卸载命令。板上保留：

| 路径 | 大小 B | 来源包 / 仓库 | SHA-256 |
|---|---:|---|---|
| /opt/afdo_agent/tools/perf | 3,261,448 | linux-kernel-perf-6.12.80-0.aarch64 / Unified 20261027.063617 | d23f11a13d5b0b21fc1957a883eb0025c80f9a26bcde360b7031b4d3b1348949 |
| /opt/afdo_agent/lib/libLLVM.so.22.1 | 68,804,864 | libllvm-22.1.8-1.5.aarch64 / Base 20261026.051209 | 06b9971c974f113b16ea49c988b6481f20272e70ba36040358735fa6c91af007 |

仓库完整 URL 见第 3 节与 E16。未来完整删除命令如下，**本轮按要求保留工具，没有执行此删除**：

```sh
rm -rf /opt/afdo_agent
```

### 边界例外

- 主机既有共享 SDB daemon 使用 `/tmp/sdb.log`。上轮末尾已知值是 400 B、mtime 2026-10-28 12:01:10；本轮首次 connect 后与收尾 stat 均为 **495 B、2026-10-28 17:48:51.361776578 +0800**。未在本轮 connect 前 stat，因此只能确认跨轮增长 95 B，不能精确归因每次写入；如实保留这一工作区外日志例外。没有删除日志或重启共享服务，消除该例外需要协调 SDB 服务日志位置。
- 用户指定的附件位于 WORKDIR 外；仅作为本次明确提供的任务指令读取，没有作为源码/配置/脚本输入，也未在附件目录写文件。其路径为 `/home/linhao/.codex/attachments/f6b1f79b-0a7a-4767-a00e-931a20bc967c/Pasted text.txt`。
- 板上 /tmp 唯一写入是用户明确要求的 true 执行负对照，已删除；其余任务写入位于 /opt/afdo_agent/。系统自身服务活动不在本轮 syscall 审计范围内，不宣称已证明不存在所有隐式写入。

本轮新增 E15–E18 共 **128,645 B**，低于 150,000 B。没有删除或修改任何历史证据文件。本轮未测/未知项已限定：运行 .config、BRBE 硬件独立能力、编译器/链接器、原始 -fPIC 开关、实际 BOLT/AutoFDO 转换；SPE/ETM 与媒体分支栈按条件跳过。
