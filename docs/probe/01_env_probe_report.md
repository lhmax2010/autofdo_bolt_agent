# 设计前环境探测报告（重新执行）

日期：2026-10-27，Asia/Shanghai。**本报告完整替代旧提交 e90492e 的探测结果；旧结论全部作废。** 本轮只探测 RPi4；RPi5 实机探测留待下一轮。只读检查，不编译、不安装包、不实现 Agent。

## 1. 盘点、范围和判定口径

WORKDIR=`/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/`。开场读取 `docs/STATUS.md` 后执行两层盘点；`src/` 各子目录只列一层。当前提供 `src/linux-rpi`、`src/llvm`、`src/ffmpeg`、`src/gstreamer`，以及 `config/gbs_llvm.conf`、`config/gbs_gcc.conf`。根目录另有同名配置，但本轮不使用。工作目录内两个配置指向的 GBS root 均不存在。没有 Chromium 源码，本轮新指令也不要求探测 Chromium。

命令：`find . -maxdepth 2 -mindepth 1 -not -path './.git/*' -not -path './temp/*' -printf '%y %p\n'`；`find src -mindepth 2 -maxdepth 2 -printf '%y %p\n'`；`nl -ba config/gbs_{llvm,gcc}.conf`；`ls -ld temp/GBS-ROOT-TIZEN-LLVM-CODES temp/GBS-ROOT-TOOLCHAIN-GCC-CODES`。关键输出：四个源码树和两份配置存在，两个 GBS root 均 ENOENT。**结论：源码/配置检查支持；构建根未提供。** 证据：[01_workspace.txt](evidence/01_workspace.txt)。

所有命令先 export `TMPDIR=WORKDIR/temp/tmp`；耗时操作使用 `nice -n 19 ionice -c3`，没有并行大任务。探测阶段曾关闭 login 初始化并禁用 Git system/global 配置读取；后续用户澄清该隔离仅用于 gbs，结果仓库 commit/push 已恢复正常环境并使用已有认证，Git 配置修改仍仅 local。下载、临时记录及分析辅助数据均在 `temp/`。只读公共仓库重新克隆到 `temp/CodingSystem`；旧克隆移到 `temp/CodingSystem_invalidated_run1`，没有用于本轮证据。边界例外详见 §7，不能把执行结论概括为“绝无边界例外”。

“支持”表示本次检查有肯定证据；“不支持（当前环境）”不外推为硬件永久不具备能力；“未知”表示缺工具、缺数据或无法判定。仓库“未找到”仅覆盖本次完整元数据快照。未展开的 RPM 宏不能冒充实际构建参数；本轮没有执行 configure/CMake/Meson 或编译。

源码指纹（`git rev-parse HEAD`，packaging 的 `git diff --name-only` 均为空；未声称全树无其他改动）：

| 源码 | HEAD |
|---|---|
| linux-rpi | `42aeefac58edeb081aff440f0b60be71cbe49755` |
| LLVM | `f999bd406c0a70fe8107aa992164fe6945c5d46a` |
| FFmpeg | `5fe76358596f66e955f005094e6f34ca525ab23d` |
| GStreamer | `68850298263d0bff872ca72aaffe8551fcdd33e2` |

证据：[05_sources.txt](evidence/05_sources.txt)。以下源码引用相对 WORKDIR；框架引用明确给出固定 commit。

## 2. RPi4 实机

### 2.1 连接、身份、权限与资源

本节完整命令、SDB 退出码、板上命令退出码及 stderr 均见 [02_rpi4.txt](evidence/02_rpi4.txt)。SDB shell 本身可能返回 0 而板上命令失败，判定使用 `REMOTE_EXIT`。

| 探测项 | 命令 | 关键输出 | 结论 |
|---|---|---|---|
| 连接 | `sdb connect 192.168.108.26`；`sdb devices` | exit 0，connected；serial=`192.168.108.26:26101` | 支持；首选 IP 成功，未尝试备用 IP |
| model | `cat /proc/device-tree/model` | Raspberry Pi 4 Model B Rev 1.5 | 支持：确认 RPi4，非按 IP 推断 |
| 架构、内核 | `uname -m`；`uname -r` | armv7l；6.12.80-arm-rpi4-v7l | 支持：32 位 ARM 镜像 |
| OS | `cat /etc/os-release` | Tizen 11.0.0；BUILD_ID=`tizen-unified-toolchain_20261022.054557_tizen-headed-armv7l` | 支持：取得镜像身份 |
| root | `sdb -s SERIAL root on`；`id` | Switched to 'root' account mode；uid=0 | 支持 |
| CPU | `cat /proc/cpuinfo` 后筛 CPU part/Features | 四核均 part `0xd08`；Features 含 neon、vfpv3、vfpv4、idiva、idivt、lpae、evtstrm、crc32 | 支持：取得 CPU 信息；不据此替代 PMU 实测 |
| 内存 | `free -m` | Mem total 3883 MiB，available 3351 MiB；Swap total 1553 MiB | 支持：取得当时资源快照 |
| 临时空间 | `df -h /tmp` | tmpfs 1.9G，可用 1.9G | 支持 |

### 2.2 perf、内核与数据实测

| 探测项 | 命令 | 关键输出/退出码 | 结论 |
|---|---|---|---|
| perf 路径 | `which perf`；回退 `command -v perf` | which 自身不存在，127；command -v 返回 1、无输出 | 不支持（当前 PATH 无 perf）；未安装 |
| perf 版本 | `perf --version` | 127，perf: command not found | 未知：无版本可读 |
| 事件源 | `ls /sys/bus/event_source/devices/` | breakpoint、kprobe、software、tracepoint、uprobe；exit 0 | 没有暴露 CPU 硬件 PMU、cs_etm 或 arm_spe 事件源；硬件能力仍未知 |
| CoreSight | `ls /sys/bus/coresight/devices/` | exit 2，No such file or directory | 不支持（当前内核未暴露此总线目录） |
| paranoid | `cat /proc/sys/kernel/perf_event_paranoid` | 2；exit 0 | 支持读取；未修改 |
| dmesg | `dmesg \| grep -i -E 'spe\|brbe\|coresight\|etm\|pmu'` | exit 0；只匹配到 Spectre、speed/SuperSpeed 等无关词 | 未发现有效 PMU/ETM/SPE/BRBE 初始化证据；不能把 `spe` 子串误当 SPE |
| 内核配置 | 优先 `/proc/config.gz`，否则 `cat /boot/config-*`；筛用户指定配置项 | `/proc/config.gz` 不存在；`/boot/config-*` 不存在；筛选命令 exit 1，cat stderr 保留 | 未知：运行内核的配置无法取得 |

采样命令统一加 `nice -n 19 ionice -c3`，并为边界控制加入 perf 全局参数 `--buildid-dir /tmp/afdo_probe/buildid`；这是与要求示例的唯一 perf 参数差异。`PERF_CONFIG`、`TMPDIR` 及输出重定向均指向 `/tmp/afdo_probe/`。以下是实际失败调用，不是成功采样：

| 项目 | 实际 perf 子命令（公共前缀见上） | 退出码和 stderr | 结论 |
|---|---|---|---|
| cycles record | `record -e cycles -a -o /tmp/afdo_probe/p1.data -- sleep 3` | 127；`ionice: failed to execute perf: No such file or directory` | 未知：命令未启动，无样本 |
| cycles report | `report -i /tmp/afdo_probe/p1.data --stdio --sort dso` | 同上 | 没有报告前 20 行可供判断 |
| 分支负对照 | `record -e cycles -b -o /tmp/afdo_probe/p2.data -- sleep 1` | 同上 | 未知：不是“不支持分支”的实测证据 |
| 分支数据检查 | `script -i /tmp/afdo_probe/p2.data -F brstack` | 同上 | 无分支数据，但原因是 perf 未启动；没有发生“record 成功却无 brstack”的情况 |
| ETM | 条件命令 `record -e cs_etm//u -o /tmp/afdo_probe/p3.data -- true` | 未执行：perf 和 cs_etm 事件源均缺失 | 不支持当前环境的 ETM 采集；无 trace 块可检查 |
| SPE | 对实际 arm_spe 事件源的最小 record 与 dump | 未执行：perf 和 arm_spe 事件源均缺失 | 不支持当前环境的 SPE 采集；无记录可检查 |
| hw 列表 | `list hw` | 127；同上 | 未知：无法取得 perf list 输出 |

执行偏差说明：批次在发现 perf 缺失后仍调用了上表的 record/report/script/list，全部在 exec 阶段失败。没有采样进程或 perf.data 生成；没有安装或寻找外部替代工具。失败记录保留，不算成功测试，也不隐去这些额外调用。之后停止 perf 部分。

### 2.3 Benchmark 素材

| 项目 | 命令 | 关键输出 | 结论 |
|---|---|---|---|
| 可执行程序 | `command -v ffmpeg ffprobe gst-launch-1.0 gst-inspect-1.0`，再逐项复核缺失项 | 只有 `/usr/bin/gst-launch-1.0`、`/usr/bin/gst-inspect-1.0`；ffmpeg/ffprobe 单项 exit 1 | GStreamer 命令支持；ffmpeg/ffprobe 当前不可用 |
| H.264 软解插件 | `nice -n 19 ionice -c3 gst-inspect-1.0 avdec_h264` | exit 0；libav H.264 decoder；`/usr/lib/gstreamer-1.0/libgstlibav.so`；插件版本 1.24.11 | 支持插件发现；未运行视频解码 benchmark |
| /root 视频 | `ls -la /root` 按常见视频后缀筛选；另用 find 记录文件名与大小 | mp4/mkv/avi/mov/webm/h264/ts/yuv 均未匹配 | 没有发现这些后缀的视频；不排除无后缀或其他命名文件 |
| 视频参数 | ffprobe 的编码/分辨率/时长/帧率检查 | 未执行：ffprobe 缺失且没有发现素材 | 未知 |

GStreamer 检查显式设置 `GST_REGISTRY=/tmp/afdo_probe/gst-registry.bin`、`XDG_CACHE_HOME=/tmp/afdo_probe/cache`，避免默认 registry 写入用户目录。

### 2.4 实体库、链接器和清理

已 `readlink -f` 解引用，再分别执行 `nice -n 19 ionice -c3 sdb -s SERIAL pull REMOTE_REAL_FILE temp/board_libs/rpi4/FILE`，成功取回两份实体文件。没有拉回 perf 数据。

| 实体库 | 大小 | `.comment` | build-id | strip | 链接器结论 |
|---|---:|---|---|---|---|
| libavcodec.so.62.11.100 | 3,079,196 B | 不存在 | `readelf -n` 无 notes；未发现 | 已 strip | 未知，无法确定 lld/GNU ld |
| libgstreamer-1.0.so.0.2411.0 | 915,540 B | 不存在 | 同上 | 已 strip | 未知，无法确定 lld/GNU ld |

命令：本机 `readelf -p .comment`、`readelf -n`、`readelf -SW`、`file`。两库为 ARM ELF32，均无 `.symtab`，保留 `.dynsym` 与 `.gnu_debuglink`；file 输出 stripped。**本轮无 GBS root，以上仅使用本机工具读取与工具版本无关的静态 ELF 元数据**，不做反汇编、优化或 profile 解析。不能根据 `.gnu.hash`、布局或仓库命名推断链接器；`.gnu_debuglink` 也不等于 build-id。证据：[03_libraries.txt](evidence/03_libraries.txt)。

结束执行 `rm -rf -- /tmp/afdo_probe`，随后 `test ! -e /tmp/afdo_probe` 返回 0；临时 registry、命令日志和 perfconfig 一并清除。无 remount、安装、重启。清理证据在 `02_rpi4.txt`。

## 3. 内核源码

证据：[05_sources.txt](evidence/05_sources.txt)。命令为 `nl -ba FILE` 的指定行摘录，以及 `rg -n` 搜索；没有运行 make。

| 项目 | 关键输出与结论 | 文件:行号 |
|---|---|---|
| 版本 | 支持读取：6.12.80，与 spec Version 一致 | `src/linux-rpi/Makefile:2–4`；`packaging/linux-rpi.spec:13–16`（后者相对该源码树） |
| AUTOFDO_CLANG / PROPELLER_CLANG | `rg -n 'AUTOFDO_CLANG\|PROPELLER_CLANG' src/linux-rpi/arch/Kconfig` exit 1，无匹配；当前源码不提供这些配置入口 | `src/linux-rpi/arch/Kconfig` 全文件搜索；否定结果无虚构行号 |
| 架构 select | `rg -n 'select ARCH_SUPPORTS_(AUTOFDO\|PROPELLER)_CLANG' src/linux-rpi/arch` exit 1；没有架构 select | `src/linux-rpi/arch/` 全目录搜索，证据含命令和退出码 |
| 源包 | `Name: rpi4-linux-kernel`，Version 6.12.80；同一 spec 按架构生成变体 | `src/linux-rpi/packaging/linux-rpi.spec:4–18,47–65` |
| 目标 ARCH 与配置 | aarch64 分支 buildarch=arm64，其余为 arm；config_name=tizen_bcm2711_defconfig；BASE_CONFIG 从对应 arch 目录取 | `src/linux-rpi/packaging/linux-rpi.spec:4–11,180–201` |
| 实际 make ARCH 的限制 | spec 没有显式传 `ARCH=`；Makefile 默认 `ARCH ?= $(SUBARCH)`，依赖 GBS 构建环境。arm/arm64 是 spec 选择的目标，不冒充本轮真实编译结果 | `src/linux-rpi/Makefile:361–381`；`packaging/linux-rpi.spec:201–219` |
| RPi4 armv7l | `arm-rpi4-linux-kernel` / `arm-rpi4-rt-linux-kernel`；`arch/arm/configs/tizen_bcm2711_defconfig` | `src/linux-rpi/packaging/linux-rpi.spec:4–11,47–65,187–201` |
| RPi5 aarch64 配置归属 | 同一源包的 `arm64-rpi4-linux-kernel`（及 rt 变体），配置 `arch/arm64/configs/tizen_bcm2711_defconfig`；名称仍 rpi4。arm64 启动配置显式含 pi5 段，DTS 列表含 bcm2712-rpi-5-b。支持源码层映射；RPi5 实际装包/启动路径未探测 | `src/linux-rpi/packaging/linux-rpi.spec:4–11,245–248`；`rpi/boot/config_64bit.txt:38–72`；`arch/arm64/boot/dts/broadcom/Makefile:26–32` |
| clang | `_toolchain` 已定义且 `toolchain_is clang` 时 `export LLVM=1`，不是无条件 clang。实际宏值/已运行内核编译器未知 | `src/linux-rpi/packaging/linux-rpi.spec:165–169,234–238` |
| perf 包构建声明 | spec 构建 tools/perf，NO_LIBTRACEEVENT=1、NO_JEVENTS=1；存在 linux-kernel-perf 包声明，但板上没有命令 | `src/linux-rpi/packaging/linux-rpi.spec:135–142,203–206` |

配置 fragments：普通变体带可选 LSM fragment，rt 变体增加 `kernel/configs/rt.config`。仅阅读 defconfig 不等于运行内核最终 .config，不能用它补齐实机配置缺失。

## 4. 工具链与仓库

### 4.1 配置差异与全部 URL

命令：`nl -ba config/gbs_llvm.conf`、`nl -ba config/gbs_gcc.conf`。证据：[01_workspace.txt](evidence/01_workspace.txt)。两者 profile 名和 repo section 名一致，tmpdir 都是 WORKDIR/temp；LLVM buildroot 后缀 `GBS-ROOT-TIZEN-LLVM-CODES`，GCC 为 `GBS-ROOT-TOOLCHAIN-GCC-CODES`，均在 WORKDIR 内。**配置 URL 的 Toolchain 后缀不同，不能仅凭配置文件名判定所有包都使用对应编译器。**

| 配置:行 | 状态 | URL |
|---|---|---|
| gbs_llvm.conf:11 | 启用，llvm_base | https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/reference/repos/standard/packages/ |
| gbs_llvm.conf:12 | 注释 | http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20260722.045200/repos/standard/packages/ |
| gbs_llvm.conf:13 | 注释 | http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20260804.124315/repos/standard/packages/ |
| gbs_llvm.conf:16 | 启用，llvm_unified | https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/reference/repos/standard/packages/ |
| gbs_llvm.conf:17 | 注释 | http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20260725.003315/repos/standard/packages/ |
| gbs_llvm.conf:18 | 注释 | https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20260804.223836/repos/standard/packages/ |
| gbs_gcc.conf:11 | 启用，gcc_base | https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base/reference/repos/standard/packages/ |
| gbs_gcc.conf:12 | 注释 | https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base/tizen-base_20260219.223706/repos/standard/packages/ |
| gbs_gcc.conf:13 | 注释 | http://download.tizen.org/SBS/TIZEN/Tizen/Tizen-Base-Dev/tizen-base-dev_20260325.020522/repos/standard/packages/ |
| gbs_gcc.conf:14 | 注释 | http://109.123.100.71/test_files/gcc/tizen-base-dev_20260325.020522/repos/standard/packages |
| gbs_gcc.conf:15 | 注释 | http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20260711.094822/repos/standard/packages |
| gbs_gcc.conf:18 | 启用，gcc_unified | https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified/reference/repos/standard/packages/ |
| gbs_gcc.conf:19 | 注释 | https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified/tizen-unified_20260309.210600/repos/standard/packages/ |
| gbs_gcc.conf:20 | 注释 | http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20260710.134244/repos/standard/packages/ |

### 4.2 primary/filelists 下载与包查询

重新下载四个启用仓库的 `repodata/repomd.xml`，按其中 href 下载 primary/filelists 到 `temp/repodata/run2/{llvm_base,llvm_unified,gcc_base,gcc_unified}/`。注释历史 URL 不属于当前启用仓库，未下载。执行 `nice -n 19 ionice -c3 python3`，标准库 urllib GET（timeout=60），gzip 解压后 ElementTree 流式全量扫描。压缩与解压 SHA-256 均匹配 repomd；以 filelists.pkgid 关联 primary.checksum。排除目录，精确匹配工具 basename（允许数字版本后缀）和 runtime 文件模式；debuginfo 包名包含 ffmpeg/libav/libsw/gstreamer/gst-。退出码 0，无 stderr。完整 URL、hash、包/文件匹配输出在 [04_repodata.txt](evidence/04_repodata.txt)。

| 仓库 | primary 包数 | filelists 扫描包数 | 结果 |
|---|---:|---:|---|
| llvm_base | 1748 | 1748 | 支持；下载、双校验、关联成功 |
| llvm_unified | 9503 | 9503 | 支持；同上 |
| gcc_base | 1731 | 1731 | 支持；同上 |
| gcc_unified | 9237 | 9237 | 支持；同上 |

下表 epoch 均为 0，省略不写。L=LLVM 配置的 base/unified；G=GCC 配置的 base/unified。存在表示元数据提供，不表示板上已经安装或工具运行通过。

| 文件/包类别 | x86_64 包名与版本 | armv7l 包名与版本 | aarch64 包名与版本 |
|---|---|---|---|
| llvm-bolt | L/G 均未找到 | 同左 | 同左 |
| perf2bolt | L/G 均未找到 | 同左 | 同左 |
| merge-fdata | L/G 均未找到 | 同左 | 同左 |
| libbolt_rt_instr.a | L/G 均未找到（查询包含 libbolt_rt_instr*.a） | 同左 | 同左 |
| llvm-profgen | llvm：L 22.1.8-3.1；G 22.1.8-6.5 | 同左 | 同左 |
| llvm-profdata | llvm：L 22.1.8-3.1；G 22.1.8-6.5 | 同左 | 同左 |
| libclang_rt.profile-*.a | compiler-rt：L 22.1.8-3.1；G 22.1.8-6.5；后缀 x86_64 | 同版本；后缀 arm | 同版本；后缀 aarch64 |
| perf | L/G 均未找到 | linux-kernel-perf 6.12.80-0，L/G 均有 | 同左 |
| create_llvm_prof | L/G 均未找到 | 同左 | 同左 |
| FFmpeg debuginfo | L/G 均未找到 | 同左 | 同左 |
| GStreamer debuginfo | L/G 均未找到 | 同左 | 同左 |

标准路径：`/usr/bin/llvm-profgen`、`/usr/bin/llvm-profdata`、`/usr/bin/perf`；profile 库位于 `/usr/lib{,64}/clang/22/lib/linux/`。四库中所有 debuginfo 包计数均为 0，本结论不覆盖可能独立的 debug 仓库。

其他文件提供包也记录如下，避免漏掉非标准路径：

| 架构 | 文件提供包 |
|---|---|
| x86_64 | clang-accel（L 0.4-2.2，G 0.4-6.4）含 `/emul/usr/bin/llvm-prof{gen,data}`；L 的 mic-bootstrap-x86-arm 1.0-1 含 `/bootstrap/{bin,usr/bin}/llvm-prof{gen,data}` |
| armv7l | clang-accel-armv7l、clang-accel-x86_64-armv7l（L 0.4-2.2，G 0.4-6.4），路径同上；L 的 mic-bootstrap-x86-arm 1.0-1 同上；L/G 的 arm-rpi4-linux-kernel-devel 6.12.80-0 含 `/boot/kernel/devel/kernel-devel-arm-rpi4/perf` |
| aarch64 | clang-accel-aarch64、clang-accel-x86_64-aarch64（L 0.4-2.2，G 0.4-6.4），路径同上；L 的 mic-bootstrap-x86-arm 1.0-1 同上；L/G 的 arm64-rpi4-linux-kernel-devel 6.12.80-0 含 `/boot/kernel/devel/kernel-devel-arm64-rpi4/perf` |

这些是 RPM 架构与文件提供关系，未检查 emul/bootstrap 或 devel 包内文件的 ELF/执行属性。没有下载、安装 RPM。板上 libavcodec/gstreamer 来源无法凭这些包列表反推。

### 4.3 LLVM 源码与打包

命令：`rg -n` 搜索 spec/CMake，配合编号摘录；证据：[05_sources.txt](evidence/05_sources.txt)。

| 项目 | 关键输出与结论 | 文件:行号 |
|---|---|---|
| LLVM 版本 | 支持：22.1.8；spec Release=1，仓库 build release 另见上表 | `src/llvm/packaging/llvm.spec:32–35`；`src/llvm/cmake/Modules/LLVMVersion.cmake:3–10` |
| 启用 BOLT | 不支持当前 spec：LLVM_ENABLE_PROJECTS=`clang;lldb;clang-tools-extra;lld;compiler-rt;openmp`，没有 bolt | `src/llvm/packaging/llvm.spec:241` |
| TARGETS x86_64 | X86;ARM;AArch64;BPF，Release | `src/llvm/packaging/llvm.spec:216–219` |
| TARGETS armv7l | ARM;BPF，MinSizeRel | `src/llvm/packaging/llvm.spec:220–224` |
| TARGETS aarch64 | AArch64;BPF，Release | `src/llvm/packaging/llvm.spec:225–229` |
| llvm-profgen 构建/打包 | 支持声明：tools 默认 ON，自动纳入含 CMakeLists 的工具子目录，llvm-profgen 有 add_llvm_tool；spec 明确打包 llvm-profgen/profdata | `src/llvm/llvm/CMakeLists.txt:833–835`；`llvm/tools/CMakeLists.txt:54–56`；`llvm/tools/llvm-profgen/CMakeLists.txt:18`；`packaging/llvm.spec:442–443`（后三者相对 src/llvm） |
| BOLT runtime | 当前 spec 不构建 BOLT，故不构建其 runtime。源码能力另有 BOLT_ENABLE_RUNTIME：支持的系统/CPU 且非交叉编译时默认 ON，条件中没有 armv7l | `src/llvm/bolt/CMakeLists.txt:87–96,143–162`；`src/llvm/packaging/llvm.spec:241` |
| compiler-rt profile | 支持构建/打包声明：COMPILER_RT_BUILD_PROFILE 默认 ON，进入 profile runtime，compiler-rt 文件通配包含 clang/22 runtime | `src/llvm/compiler-rt/CMakeLists.txt:73–74`；`compiler-rt/lib/CMakeLists.txt:52–53`；`compiler-rt/lib/profile/CMakeLists.txt:177–192`；`packaging/llvm.spec:590–594`（后三者相对 src/llvm） |
| lld 独立子包 | 不支持“独立 lld 子包”这一判断：lld 已启用，但 lld/ld.lld/ld64.lld/lld-link/wasm-ld 位于 llvm 主包 `%files` | `src/llvm/packaging/llvm.spec:241,386–400`，子包声明全集见证据 |
| LLVM 自身链接器 | `_toolchain` 定义时显式 -fuse-ld=lld、LLVM_USE_LINKER=lld；其他分支不能在无宏环境时断言 | `src/llvm/packaging/llvm.spec:198–213` |

## 5. FFmpeg / GStreamer 源码

证据：[05_sources.txt](evidence/05_sources.txt)。命令：`rg -n '^Name:|^Version:|^%package'`、编译参数关键词搜索和对应 `nl -ba` 摘录。

### 5.1 FFmpeg

源包 `ffmpeg`，版本 `8.0.1-1`，spec=`src/ffmpeg/packaging/ffmpeg.spec:1–4`。该 spec 还声明 libavcodec/libavformat/libavutil/libavfilter/libswscale/libswresample 及各自 devel、doc、ffmpeg-tool；完整声明行号见证据。

| 项目 | 当前声明与结论 | 文件:行号 |
|---|---|---|
| 编译器 | CC=%{__cc}、CXX=%{__cxx}；由 GBS/RPM 宏决定，spec 未硬编码 gcc/clang。实际展开未知 | `src/ffmpeg/packaging/ffmpeg.spec:239–247` |
| 优化级别 | CFLAGS 继承 `%{optflags}` 并追加 fPIC、Tizen 宏；未提供宏展开环境。configure 对 GCC/Clang 的 speed 默认均为 -O3，默认开启 optimizations，未指定 optflags 时选 speed；这属于静态默认，不是本轮实际编译日志 | `src/ffmpeg/packaging/ffmpeg.spec:232–236`；`src/ffmpeg/configure:4228,5060–5079,5109–5114,7689–7704` |
| LTO | spec 没有显式 --enable-lto 或 -flto；不能排除外部 `%{optflags}`/环境注入 | spec 全文件关键词搜索，及 `src/ffmpeg/packaging/ffmpeg.spec:232–247` |
| 链接器/LDFLAGS | spec 未显式指定 LDFLAGS 或 -fuse-ld；启用 --toolchain=hardened。最终链接器未知，不能由 GCC/LLVM repo 名推断 | `src/ffmpeg/packaging/ffmpeg.spec:225,239–247`；全 spec 搜索 |
| armv7l 手写汇编 | 正常非 ASan 路径保留 asm 默认启用，显式 --enable-neon、-mfpu=neon；--disable-x86asm 只针对 x86。ASan 条件传 --disable-asm | `src/ffmpeg/packaging/ffmpeg.spec:140–148,227–237`；`src/ffmpeg/configure:4222` |
| aarch64 手写汇编 | 正常非 ASan 路径同样保留 asm、启用 NEON；不追加 armv7 的 -mfpu=neon。ASan 同样关闭 asm | 同上 |

结论：支持源码层 asm/NEON 启用意图，具体汇编对象能否通过工具链检查未知。本轮没有把“spec 未禁用”写成“已验证所有汇编都被编译”。ffprobe 不由当前基本配置启用：`--disable-programs --enable-ffmpeg`，来源 spec:144；与板上 ffprobe 缺失相容，但不能证明板上装包原因。

### 5.2 GStreamer 包清单

仅发现一份 `src/gstreamer/packaging/gstreamer.spec`。默认 `plugin=all`，主包名 gstreamer；可用 plugin 宏单独选择 core/base/good/bad/ugly/libav/rs/es。8 个对应源码子项目都已提供，版本均为 1.24.11（各 `subprojects/NAME/meson.build:1–5`）。统一 spec 版本 **1.24.11-42**（spec:62–64）。以下逐个列出默认 all 模式的主包及 17 个子包；表中行号均属于该 spec。

| 包名 | 版本 | spec 行 |
|---|---|---:|
| gstreamer | 1.24.11-42 | 47,62–64 |
| gstreamer-utils | 1.24.11-42 | 96 |
| gstreamer-devel | 1.24.11-42 | 111 |
| gst-plugins-base | 1.24.11-42 | 137 |
| gst-plugins-base-extension-adder | 1.24.11-42 | 192 |
| gst-plugins-base-devel | 1.24.11-42 | 202 |
| gst-plugins-good | 1.24.11-42 | 217 |
| gst-plugins-good-extra | 1.24.11-42 | 262 |
| gst-plugins-good-cairo | 1.24.11-42 | 273 |
| gst-plugins-good-v4l2 | 1.24.11-42 | 285 |
| gst-plugins-bad | 1.24.11-42 | 303 |
| gst-plugins-bad-devel | 1.24.11-42 | 346 |
| gst-plugins-ugly | 1.24.11-42 | 365 |
| gst-libav | 1.24.11-42 | 392 |
| gst-rtsp-server | 1.24.11-42 | 425 |
| gst-rtsp-server-devel | 1.24.11-42 | 441 |
| gst-editing-services | 1.24.11-42 | 457 |
| gst-editing-services-devel | 1.24.11-42 | 474 |

编译器：spec 未设置 CC/CXX，由构建环境/Meson 选取，实际 gcc/clang 未知。CFLAGS=`%{optflags}` 加 `-fno-strict-aliasing -fstack-protector-strong -Wl,-z,relro -D_FORTIFY_SOURCE=2`，CXXFLAGS 追加 `-Wno-error`，LDFLAGS 追加 `-pthread`。没有显式 LTO 或 linker selection。来源：`src/gstreamer/packaging/gstreamer.spec:515–526` 及全文件关键词搜索。

顶层与上述各子项目都声明 `buildtype=debugoptimized`；spec 没有覆盖 buildtype/optimization，也没有 `b_lto`。但 `%{optflags}` 的最终展开、Meson 版本及最终编译命令未知，不据此把实际优化级别写死为 -O2。来源：`src/gstreamer/meson.build:1–8`、各 `subprojects/NAME/meson.build:1–5`、spec:526 起的 meson 调用。

**H.264 软解插件已提供：** `avdec_h264` 属于 `gst-libav`，源码在 `src/gstreamer/subprojects/gst-libav`；spec:392 声明包，403–406 依赖 libavcodec/libavfilter/libavformat/libavutil，1212–1216 打包 `libgstlibav.so`。插件注册以解码器名组成 `avdec_%s`（`subprojects/gst-libav/ext/libav/gstavviddec.c:2797–2804`）。板上 gst-inspect 实测进一步确认 avdec_h264 来自该库。结论：支持插件发现及源码归属，未做吞吐量验证。

## 6. Multi-Agent 框架契约

执行新的 `nice -n 19 ionice -c3 git -c credential.helper= -c gc.auto=0 clone https://github.com/lhmax2010/CodingSystem.git temp/CodingSystem`，退出 0。随后 `git rev-parse HEAD`、`git ls-tree -r --name-only HEAD`、编号文档摘录、`git status --porcelain`（为空）。未修改或推送框架仓库。证据：[06_codingsystem.txt](evidence/06_codingsystem.txt)。

本节每条结论固定在 **commit `287d51c674e2b7d38605098338ff94fc8bb4e4fa`**，以下 `@287d51c` 均指此完整 hash；路径相对于 `temp/CodingSystem/`。这是重新克隆后的证据，不沿用旧探测结果。

| 项目 | 结论与关键输出 | 文件:行号 @ commit |
|---|---|---|
| 最新冻结 HLD | v1.0-draft-frozen，DRAFT FREEZE。正式 contract v1.0 还需 Compiler 真实消费、五类 fixture、兼容矩阵；不能称正式定稿 | `docs/00_Framework_HLD_v1.0_draft_frozen.md:3–6,31` @287d51c |
| 最新契约 | v0.11 Draft，复审中；规范 contract_version=1.0.0.dev1，dsl_version=1 | `docs/01_Contract_Spec_v0.11.md:3–6,37–41` @287d51c |
| 业务指南 | HLD 引用 02–06_Agent_Design_Guide，但 tracked 树没有这些文件，五类指南均未提供；07/08/09 也未入库 | `docs/00_Framework_HLD_v1.0_draft_frozen.md:6,16–22` @287d51c；同 commit 的 ls-tree 全集（缺文件没有虚构行号） |
| 注册接入 | 业务包依赖 codingsystem-framework wheel，entry-point namespace codingsystem.agents；继承 AgentBase，实现 setup(ctx)、execute(TaskInput)->HandoffResult、teardown | `docs/00_Framework_HLD_v1.0_draft_frozen.md:259–278,414` @287d51c |
| 注册字段/准入 | agent_type、task_prefix、status_set、contract_requires、produces、hard_required_inputs、capabilities_required；前缀 2–4 大写且唯一；conformance 绑定制品 digest、contract/套件版本；draft 精确锁版本 | `docs/01_Contract_Spec_v0.11.md:35–38,113,176–182` @287d51c |
| 路由及上游 | Agent 只产 status，由框架路由；默认上游可选且显式标缺失；hard-required 必须有可解析、支配消费者的同 series 生产者 | `docs/00_Framework_HLD_v1.0_draft_frozen.md:81,303–304`；`docs/01_Contract_Spec_v0.11.md:127` @287d51c |
| 能力与效应 | ctx 注入 BuildExecutor/BoardPool 等授权能力；side_effect 提供 at-least-once+效应侧幂等。build.* 需 probe，board.* 需 probe 或 replay_safe；发布只允许 broker，业务 worker 无发布凭据 | `docs/00_Framework_HLD_v1.0_draft_frozen.md:271,280–286`；`docs/01_Contract_Spec_v0.11.md:398–405,440–448` @287d51c |
| 外部入口 | 框架外 Coding Agent 使用 HTTP+JSON 的 create_run/submit_patch/get_status/get_result/cancel_run，区别于业务插件注册面 | `docs/00_Framework_HLD_v1.0_draft_frozen.md:309–312` @287d51c |

通用 I/O（均为规范，未实现）：

| 类型 | 字段摘要 | 文件:行号 @ commit |
|---|---|---|
| TaskInput | run_id/task_id/dispatch_id/attempt；node/node_config/mode；series_id/snapshot_id；upstream/join_inputs。UpstreamItem.ref=None 表示缺失 | `docs/01_Contract_Spec_v0.11.md:184–191` @287d51c |
| HandoffResult | task_id/status/series_id；可选 series_candidate_id；artifact_refs/reason/metrics。没有路由 target；metrics 不参与 digest | `docs/01_Contract_Spec_v0.11.md:193–197` @287d51c |
| ArtifactRef/RunContext | 内容 digest、kind、media_type、data_class；ctx 包含 snapshot manifest、pipeline/contract 标识与授权能力 | `docs/01_Contract_Spec_v0.11.md:199–203` @287d51c |
| ReportBase | report_type/task_id/run_id/series_id/created_at/data_class/inputs；artifact_refs 以 report_type 为键。扩展限 ext 容器带组织前缀 | `docs/01_Contract_Spec_v0.11.md:41,208–213` @287d51c |
| 门禁指标 | 读取报告顶层 gateable 定点字符串，以 Decimal 比较；缺失/非法 fail-closed，不能用 HandoffResult.metrics 代替 | `docs/01_Contract_Spec_v0.11.md:134–135,197,222` @287d51c |

Compiler：输入通用 TaskInput/RunContext，fixture 不消费上游报告（仍需 snapshot/series 等）；BuildExecutor 设计入口 `build(snapshot,series,targets)`。输出 BuildReport：succeeded、targets_built、revdep_scope、failed_target、error_excerpt_ref、fix_patches、rounds_used、output_refs；HandoffResult 状态 fixture 为 build_passed/build_failed_exhausted，前缀 CMP。来源 `docs/01_Contract_Spec_v0.11.md:185–203,214,755–756`，`docs/00_Framework_HLD_v1.0_draft_frozen.md:340` @287d51c。

Benchmark：输入通用 TaskInput，fixture 消费 BuildReport；构建产物 hard-require 需要注册声明。输出 BenchReport：regression_pct（全指标最大回归，顶层 gateable）、metrics（每项 value/baseline/regression_pct 定点字符串）、baseline_ref、patch_relatedness_ref；fixture 状态 bench_done/bench_failed，前缀 BEN。来源 `docs/01_Contract_Spec_v0.11.md:181,218,222,755,758`，`docs/00_Framework_HLD_v1.0_draft_frozen.md:303–304` @287d51c。

规范 compiler_bench_only 示例为 Compiler→Benchmark→threshold→review summary，阈值 5.0 只是框架示例，不是本项目已决定的回归阈值。来源 `docs/01_Contract_Spec_v0.11.md:768–786` @287d51c。

**当前实现程度：不支持运行框架这一结论有仓库证据。** framework、agents、ci、conformance、pipelines 目录仅 .gitkeep；`.dev_memory/current_state.md:3–29` @287d51c 写明尚无业务代码。HLD:436–445 的 P0–P5 是计划，且 P0 还要求契约 draft freeze、08/09 就绪；当前契约复审中、指南缺失，不能宣称 P0 完成，更不能宣称 SDK/Compiler/Benchmark 已实现。完整文件树在证据中。

本项目 profile schema、训练与验证场景、二进制身份关联和包仓 profile 提交流程仍需后续设计，现有通用 BuildReport/BenchReport 不能替代完整业务指南。此为据上述字段及缺失指南作出的范围判断，不是已实现接口。

## 7. 边界例外

后续规则澄清：工作目录边界约束项目输入/产出，不禁止已有 GitHub 认证；隔离仅用于 gbs，本轮没有 gbs。结果仓库 commit/push 在正常环境执行。下表保留探测时的事实与审计限制，首次系统初始化读取不再作为已证实的项目输入越界；外部 SDB 日志仍列为边界例外。长期规则见 `docs/STATUS.md` 开头。

证据：[07_boundary.txt](evidence/07_boundary.txt)。用户同时要求“不读取工作目录外文件”及“检查上一轮外部遗留”；本次对已知 SDB 路径仅做 stat 和进程 fd 符号链接的元数据检查，不读取外部日志/配置内容，不扫描其他项目目录、不删除外部文件。

| 路径/范围 | 工具、事实与来源 | 能否避免/本轮处理 |
|---|---|---|
| `/tmp/sdb.log` | 已存在，0 B；mtime/ctime=2026-10-26 22:36:47 +0800；现存 SDB PID 14243 的 fd 1/2 指向它。属于工作目录外 SDB 服务日志，启动时间与日志时间相同；上一轮具体创建 syscall 未记录，不能严格证明由哪次调用创建 | 未删除、未重启共享 SDB 服务。前后 stat 大小/mtime/ctime 未变，本轮未观察到内容写入。设 TMPDIR 对已运行 daemon 的已打开 fd 无效；能否在不重启服务下改路径未验证 |
| 首次 shell/Git 初始化读取（审计缺口） | 首次工具调用沿用默认 login shell，且首次 git status 尚未设置禁用全局配置读取；没有追踪该调用，无法证明未隐式加载工作目录外初始化/配置文件，具体路径未知 | 后续全部 login=false；GIT_CONFIG_NOSYSTEM=1，GIT_CONFIG_GLOBAL 指向 WORKDIR/temp/empty-git-config；不修改全局配置。此项不能写成“已证实无外部读取” |
| 系统工具运行依赖 | connect 的 strace 显示 sdb 动态加载系统库并读 `/etc/ld.so.cache`、名称解析配置等；这不是项目源码或分析输入。file/HTTPS/Git 同样需要工具自身运行环境 | 按“系统命令可执行”例外使用；未复制这些外部文件到项目 |

`strace -f -e trace=%file` 跟踪连接客户端没有外部 O_WRONLY/O_RDWR/O_CREAT、mkdir、rename、unlink，但它复用已运行的 SDB daemon，不能代表 daemon 的全部行为。已知候选 `/tmp/sdb-server.log`、`/home/linhao/.sdb`、`/home/linhao/.sdb/sdbkey` 均不存在。上一轮没有完整文件写入审计，不能追溯证明外部遗留全集；本报告不声称“边界例外无”。

板上唯一主动生成目录为 `/tmp/afdo_probe/`，含 gst registry 与文本诊断，已验证删除；没有 perf 数据生成/拉回。板上系统服务自身可能产生的日志不在 SDB 客户端文件跟踪范围内，未声称已逐 syscall 审计整个系统。

## 8. 未完成项与接续条件

- perf 缺失：普通采样、分支负对照及 hw 列表未能完成；不安装替代包。本轮全部失败调用已保留。后续需用户提供具备 perf 的镜像/环境并允许另轮实测。
- 当前镜像无硬件 PMU/cs_etm/arm_spe 事件源，且运行内核配置不可读；不能判断其根因或据此否定硬件能力。BRBE 没有可用配置/记录证据，保留未知。
- FFmpeg/ffprobe 命令和常见视频素材缺失；无法读取视频元信息或跑媒体场景。
- 两库无 .comment/build-id：链接器未知，build-id 未发现；需要保留这些元数据的原始构建产物才能进一步确认。
- 没有 GBS root / 宏展开和编译日志：各包最终编译器、外部优化/LTO/链接参数未知；本轮未编译。
- CodingSystem 五类业务指南和实现缺失，契约尚未正式冻结；只完成现有文档契约核对。
- RPi5 实机与 Chromium 不在本轮范围，不作为已验证项目。

## 9. RPi4 能力总表

| 板卡 | perf | 普通采样 | 分支栈 | ETM | SPE | BRBE | root |
|---|---|---|---|---|---|---|---|
| Raspberry Pi 4 Model B Rev 1.5 / armv7l | 不支持当前环境：命令缺失 | 未知：perf 未启动、无样本 | 未知：perf 未启动 | 不支持当前采集环境：无事件源/工具 | 不支持当前采集环境：无事件源/工具 | 未知：无配置/记录证据 | 支持：uid=0 |
