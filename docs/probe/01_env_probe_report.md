# 设计前环境探测报告

日期：2026-10-27（Asia/Shanghai，会话日期）。范围：只读环境探测，不写产品实现、不编译、不安装软件。

**结果：已完成工作区盘点、设备发现、两个配置仓库的工具包查询和 CodingSystem 文档/实现状态检查。板卡未连接，源码尚未就绪，实机环境能力尚未闭合。** 未将“未探测”写成“不支持”。

## 1. 工作区与证据口径

工作目录：`/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/`。初始两层盘点为空；`ls -la` 只有 `.`、`..`。未发现任何已提供源码、配置、GBS root 或既有 `docs/STATUS.md`，也没有项目 `AGENTS.md`。初始化前远端 `git ls-remote https://github.com/lhmax2010/autofdo_bolt_agent.git` 成功且无 refs，因此初始化 `main` 并设置该 remote，无远端内容可拉取。提交署名配置为 `Hao Lin <hao.lin@samsung.com>`。

| 探测项 | 已执行命令 | 关键输出 | 结论 | 证据 |
|---|---|---|---|---|
| 初始目录两层 | `find . -maxdepth 2 -mindepth 1 -printf '%y %p\n' \| head -160`；`ls -la` | 无目录项；只有 `.`、`..` | 支持：已完成盘点；没有输入材料 | [01_workspace.txt](evidence/01_workspace.txt) |
| 远端内容 | `git ls-remote origin`（初始化后复核） | exit 0，stdout/stderr 空 | 支持：远端可读取，当时没有 refs | 同上 |
| GBS 配置 | `ls -ld config/gbs_llvm.conf` | exit 2，No such file or directory | 未提供 | 同上 |
| 源码 | `ls -ld linux-rpi src/llvm src/ffmpeg src/gstreamer src/chromium`（证据中逐项执行） | 各 exit 2；初始目录为空 | 未提供；不是对目录名的猜测性排除 | 同上 |
| 设备发现 | `sdb devices` | exit 0，仅 `List of devices attached`；stderr 空 | 支持：SDB 命令可运行；未发现任何板 | [02_sdb_devices.txt](evidence/02_sdb_devices.txt) |

**材料补入后的更新：** 初始盘点之后，用户侧补入根目录 `gbs_llvm.conf`、`gbs_gcc.conf`、空 `config/` 和正在克隆的 `src/llvm/`。上表记录初始状态；已按根目录实际配置完成 §6 元数据查询，不再将 GBS 配置记作完全未提供。`config/gbs_llvm.conf` 仍不存在，未擅自移动配置；`src/llvm` 尚无有效 HEAD/源码。证据 `01_workspace.txt` 末尾保留第二次盘点。

所有本轮临时下载位于被 `.gitignore` 排除的 `temp/`。未扫描工作目录外寻找源码或 GBS root；只对新配置明确指向的 GBS root 做只读 `ls -ld`，结果路径不存在。`temp/CodingSystem/` 是本轮下载的框架仓库，不是用户预置的包源码。耗时下载使用 `nice -n 19 ionice -c3`，未并行运行大任务。未修改或提交正在补入的源码、配置。

下文“未知”指缺少观测证据；“未执行”无退出码、无 stderr，不能记成 exit 0。能力的“支持/不支持”只用于有对应证据的结论。框架章节的“规范支持”不表示代码已经实现。

## 2. RPi4

**状态：未知，缺少连接信息。** `sdb devices` 未发现设备，按用户要求停止开发板部分并请求 RPi4 IP。未凭 IP、预期镜像架构或产品名称推定实际板型。

| 探测项 | 命令/续测规程 | 关键输出及执行状态 | 结论 | 证据 |
|---|---|---|---|---|
| model、架构、OS、内核版本 | §4 A | 未执行；无可选设备 | 未知；armv7l 只是需求中的预期镜像 | [02_sdb_devices.txt](evidence/02_sdb_devices.txt) |
| root | §4 B | `sdb root on` 未执行 | 未知 | 同上 |
| CPU、内存、空间 | §4 C | 未执行 | 未知 | 同上 |
| perf 版本、事件源、CoreSight、paranoid、dmesg、内核配置 | §4 D | 未执行 | 未知 | 同上 |
| cycles 普通采样、分支栈负对照、ETM、SPE、硬件事件列表 | §4 E | 全部未执行；无 data 文件、无样本证据 | 未知 | 同上 |
| FFmpeg/GStreamer 命令、avdec_h264、视频信息 | §4 F | 未执行 | 未知 | 同上 |
| libavcodec/libgstreamer 实体库、链接器、build-id、strip | §4 G | 未执行；未拉回任何二进制 | 未知 | 同上 |
| 临时目录清理 | §4 H | 从未创建 `/tmp/afdo_probe/`；未执行删除 | 无清理对象 | 同上 |

## 3. RPi5

**状态：未知，缺少连接信息。** `sdb devices` 未发现设备，按用户要求停止开发板部分并请求 RPi5 IP。未按预期架构替代实际身份检查。

| 探测项 | 命令/续测规程 | 关键输出及执行状态 | 结论 | 证据 |
|---|---|---|---|---|
| model、架构、OS、内核版本 | §4 A | 未执行；无可选设备 | 未知；aarch64 只是需求中的预期镜像 | [02_sdb_devices.txt](evidence/02_sdb_devices.txt) |
| root | §4 B | `sdb root on` 未执行 | 未知 | 同上 |
| CPU、内存、空间 | §4 C | 未执行 | 未知 | 同上 |
| perf 版本、事件源、CoreSight、paranoid、dmesg、内核配置 | §4 D | 未执行 | 未知 | 同上 |
| cycles 普通采样、分支栈负对照、ETM、SPE、硬件事件列表 | §4 E | 全部未执行；无 data 文件、无样本证据 | 未知 | 同上 |
| FFmpeg/GStreamer 命令、avdec_h264、视频信息 | §4 F | 未执行 | 未知 | 同上 |
| libavcodec/libgstreamer 实体库、链接器、build-id、strip | §4 G | 未执行；未拉回任何二进制 | 未知 | 同上 |
| 临时目录清理 | §4 H | 从未创建 `/tmp/afdo_probe/`；未执行删除 | 无清理对象 | 同上 |

## 4. 板卡续测命令清单（全部未执行）

这里列出待执行项，避免遗漏，不是本轮实测记录。`SERIAL` 必须来自 SDB 设备发现；连接后先查 model，再归类 RPi4/RPi5。所有板上写入仅限 `/tmp/afdo_probe/`，不 remount、不装包、不重启；每项分别保存命令、原始退出码、stdout 和 stderr。耗时操作加 `nice -n 19 ionice -c3`；先检查板上调度工具是否可用。

| 编号 | 待执行命令及判定规则 |
|---|---|
| A 身份 | `sdb -s SERIAL shell 'cat /proc/device-tree/model; uname -m; cat /etc/os-release; uname -r'`。必须按 model 认板。 |
| B root | `sdb -s SERIAL root on`，记录返回结果；再 `sdb -s SERIAL shell id` 核验实际 uid。 |
| C 资源 | 板上分别执行 `cat /proc/cpuinfo`（保留 CPU part、Features）、`free -m`、`df -h /tmp`。 |
| D perf 与内核 | `which perf`、`perf --version`、`ls /sys/bus/event_source/devices/`、`ls /sys/bus/coresight/devices/`、`cat /proc/sys/kernel/perf_event_paranoid`；root 下 `dmesg \| grep -i -E 'spe\|brbe\|coresight\|etm\|pmu'`。优先读 `/proc/config.gz`（`zcat`），其次 `/boot/config-*`，筛选 `PERF_EVENTS\|HW_PERF_EVENTS\|ARM_PMU\|CORESIGHT\|ARM_SPE\|ARM64_BRBE\|KALLSYMS\|DEBUG_INFO\|AUTOFDO\|PROPELLER`，包括 `is not set`。BRBE 记录配置和事件证据，不仅凭 CPU 型号判断。 |
| E-a 普通采样 | `perf record -e cycles -a -o /tmp/afdo_probe/p1.data -- sleep 3`；随后 `perf report -i /tmp/afdo_probe/p1.data --stdio --sort dso` 取前 20 行，核验样本数。 |
| E-b 分支负对照 | `perf record -e cycles -b -o /tmp/afdo_probe/p2.data -- sleep 1`；随后 `perf script -i /tmp/afdo_probe/p2.data -F brstack \| head`。即使 record 成功，没有实际分支数据也按本次探测标准判不支持，同时保留采样量背景。 |
| E-c ETM | 有 cs_etm 才执行 `perf record -e cs_etm//u -o /tmp/afdo_probe/p3.data -- true`，再 `perf report -i /tmp/afdo_probe/p3.data --dump` 检查实际 ETM/AUX trace 数据块，不能只认事件名称或空记录头。 |
| E-d SPE | 若发现 arm_spe 事件源，使用其实际名称，例如 `perf record -e arm_spe_0//u -o /tmp/afdo_probe/p4.data -- true`，配合 `perf report -i /tmp/afdo_probe/p4.data --dump` 与 `perf script -i /tmp/afdo_probe/p4.data` 确认真实 SPE 记录；仅事件源存在不算成功。 |
| E-e 事件列表 | `perf list hw`。 |
| F Benchmark | `command -v ffmpeg ffprobe gst-launch-1.0 gst-inspect-1.0`；`gst-inspect-1.0 avdec_h264`；只读 `ls -la /root`，证据仅保留视频文件名和大小。若 ffprobe 存在，对每个视频执行 `ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate,avg_frame_rate:format=duration -of json VIDEO`。 |
| G 库文件 | 只读定位 `libavcodec.so*`、`libgstreamer-1.0.so*`，`readlink -f` 确认实体，再 `sdb -s SERIAL pull REMOTE_REAL_FILE temp/board_libs/BOARD/`。优先 GBS root 平台工具读取 `.comment`、build-id 和符号/调试节。没有 GBS root 时本机工具仅作获准的 `.comment` 等版本无关读取，本轮未使用本机 ELF 工具。`.comment` 中编译器字符串不能单独证明最终用了 GNU ld；无明确链接器标记时保留“未知”。build-id 与 strip 状态也不能凭 `.comment` 推断。 |
| H 清理 | 采集后仅删除本次创建的 `/tmp/afdo_probe/` 并验证不存在；不触碰其他板上路径。 |

对 `head` 等截断展示，后续必须单独保留原始 perf 命令的退出码和 stderr，不能把管道末端成功当作 perf 成功。

## 5. 源码探测

证据：[01_workspace.txt](evidence/01_workspace.txt)。初始工作目录为空；后补的 `src/llvm` 尚在克隆，只有 `.git`，无有效 HEAD。内核及三类业务源码仍**未提供，能力未知**。没有可以引用的源码 `文件:行号`，不使用上游通用版本代替本项目事实。

### 5.1 内核

| 要求 | 命令/检查方式（待提供源码后执行） | 当前结果 |
|---|---|---|
| 版本 | `rg -n '^(VERSION\|PATCHLEVEL\|SUBLEVEL)\s*=' KERNEL/Makefile` | 未执行；未提供 |
| AutoFDO/Propeller Kconfig | `rg -n 'AUTOFDO_CLANG\|PROPELLER_CLANG' KERNEL/arch/Kconfig` | 未执行；未知 |
| 架构 select | `rg -n 'select ARCH_SUPPORTS_(AUTOFDO\|PROPELLER)_CLANG' KERNEL/arch` | 未执行；未知 |
| spec 的 ARCH、defconfig、clang | 先找实际 spec，再以 `nl -ba SPEC` 保留条件分支、宏定义和构建命令 | 未执行；RPi4/RPi5 包和配置映射均未知 |

### 5.2 FFmpeg / GStreamer / Chromium

| 源码 | 包名、版本、spec 路径 | 编译器、优化级别、LTO、链接器/LDFLAGS | 手写汇编 |
|---|---|---|---|
| FFmpeg | 未提供 | 未知 | armv7l 与 aarch64 均未知；没有 configure 参数可统计 |
| GStreamer | 未提供 | 未知 | 本项不要求统计 |
| Chromium | 未提供 | 未知 | 本项不要求统计 |

待源码到位后，从真实 spec 的 `Name/Version`、架构条件、`CC/CXX`、`CFLAGS/CXXFLAGS/LDFLAGS`、configure/meson/GN 参数追溯到行号。不得把编译系统的默认值写成当前包的实测配置。

## 6. 工具链探测

### 6.1 仓库元数据与包提供关系

初始 `ls -ld config/gbs_llvm.conf` 返回 exit 2。随后实际补入的是根目录 `gbs_llvm.conf`，已执行 `nl -ba gbs_llvm.conf` 并按启用的两个 URL 下载；证据：[01_workspace.txt](evidence/01_workspace.txt)、[04_repodata.txt](evidence/04_repodata.txt)。

配置内全部仓库 URL 如下。只查询生效仓库，注释中的历史 snapshot 不属于当前 profile，未下载。

| 配置行 | 状态 | URL |
|---|---|---|
| `gbs_llvm.conf:11` | 启用，base | https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/reference/repos/standard/packages/ |
| `gbs_llvm.conf:12` | 注释 | http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20260722.045200/repos/standard/packages/ |
| `gbs_llvm.conf:13` | 注释 | http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20260804.124315/repos/standard/packages/ |
| `gbs_llvm.conf:16` | 启用，unified | https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/reference/repos/standard/packages/ |
| `gbs_llvm.conf:17` | 注释 | http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20260725.003315/repos/standard/packages/ |
| `gbs_llvm.conf:18` | 注释 | https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20260804.223836/repos/standard/packages/ |

下载命令：分别对两个启用 URL 执行 `nice -n 19 ionice -c3 curl -fSL --max-time 60 URL/repodata/repomd.xml -o temp/repodata/REPO/repomd.xml`（exit 0）。随后 `nice -n 19 ionice -c3 python3` 用标准库解析 repomd，逐个下载 primary/filelists，校验压缩及解压内容 SHA-256，再以 filelists 的 pkgid 关联 primary checksum 全量查询。查询排除 `type=dir`，接受工具名的版本后缀；目录名 perf 不当作可执行文件。下载 URL、hash、包名、版本、RPM 路径与文件路径均在 `04_repodata.txt`。Python 下载与查询命令均 exit 0，无 stderr。

| repo | primary 压缩大小 | filelists 压缩大小 | 关联扫描包数 | 结论 |
|---|---|---|---|---|
| base | 356,567 B | 1,987,300 B | 1,748 | 支持：元数据可读取，双 checksum 校验通过 |
| unified | 1,598,149 B | 5,714,163 B | 9,503 | 支持：元数据可读取，双 checksum 校验通过 |

以下版本省略为 0 的 epoch。“未找到”表示这两个配置仓库的所取快照不提供对应匹配文件/包；不代表上游功能不支持，或其他 debug 仓库也没有。未安装或执行 RPM 内工具。

| 要查找的内容 | x86_64 包名/版本 | armv7l 包名/版本 | aarch64 包名/版本 |
|---|---|---|---|
| llvm-bolt | 未找到 | 未找到 | 未找到 |
| perf2bolt | 未找到 | 未找到 | 未找到 |
| merge-fdata | 未找到 | 未找到 | 未找到 |
| libbolt_rt_instr.a | 未找到 | 未找到 | 未找到 |
| llvm-profgen | llvm 22.1.8-3.1（base） | llvm 22.1.8-3.1（base） | llvm 22.1.8-3.1（base） |
| llvm-profdata | llvm 22.1.8-3.1（base） | llvm 22.1.8-3.1（base） | llvm 22.1.8-3.1（base） |
| libclang_rt.profile-*.a | compiler-rt 22.1.8-3.1；后缀 x86_64 | compiler-rt 22.1.8-3.1；后缀 arm | compiler-rt 22.1.8-3.1；后缀 aarch64 |
| perf | 未找到可执行文件 | linux-kernel-perf 6.12.80-0（unified） | linux-kernel-perf 6.12.80-0（unified） |
| create_llvm_prof | 未找到 | 未找到 | 未找到 |
| FFmpeg debuginfo | 未找到 | 未找到 | 未找到 |
| GStreamer debuginfo | 未找到 | 未找到 | 未找到 |

关键文件输出：llvm 包提供 `/usr/bin/llvm-profgen`、`/usr/bin/llvm-profdata`；compiler-rt 提供 `/usr/lib64/clang/22/lib/linux/libclang_rt.profile-{x86_64,aarch64}.a` 或 armv7l 下 `/usr/lib/clang/22/lib/linux/libclang_rt.profile-arm.a`；linux-kernel-perf 提供 `/usr/bin/perf`。两个仓库的全部包名均无 debuginfo 包，不能据此推断单独 debug 仓库的内容。

其他提供相同 profile 工具文件的包也已记录，不遗漏非标准路径：

| 包架构 | base 中 `/emul/usr/bin/{llvm-profgen,llvm-profdata}` 提供包 | unified 中 `/bootstrap/{bin,usr/bin}/{llvm-profgen,llvm-profdata}` 提供包 |
|---|---|---|
| x86_64 | clang-accel 0.4-2.2 | mic-bootstrap-x86-arm 1.0-1 |
| armv7l | clang-accel-armv7l、clang-accel-x86_64-armv7l，均 0.4-2.2 | mic-bootstrap-x86-arm 1.0-1 |
| aarch64 | clang-accel-aarch64、clang-accel-x86_64-aarch64，均 0.4-2.2 | mic-bootstrap-x86-arm 1.0-1 |

这是 RPM 包架构，不是对嵌入工具 ELF 架构/可执行性的验证，尤其不能把 emul/bootstrap 路径工具认作板上原生工具。未下载 RPM、未建立 GBS root、未编译。配置 `gbs_llvm.conf:3,5` 指向工作目录外的临时和构建路径，本轮未运行 GBS，未向那里写入；对该 buildroot 的只读 `ls -ld` 返回不存在。

### 6.2 LLVM 源码与打包

初始 `ls -ld src/llvm` 返回 exit 2；补入后目录出现，但 `git -C src/llvm rev-parse HEAD` 返回 exit 128（没有有效 HEAD），仅 `.git`，尚无可读源码。证据：[01_workspace.txt](evidence/01_workspace.txt)。以下均**待克隆完成/未知**；元数据中的 LLVM 22.1.8 不能替代源码版本与打包参数证据。

| 要查项 | 待检查位置 | 本轮结果 |
|---|---|---|
| LLVM 版本 | spec、版本 CMake 定义 | 未执行 |
| LLVM_ENABLE_PROJECTS 是否含 bolt | spec 的 CMake 参数及被引用配置 | 未执行 |
| LLVM_TARGETS_TO_BUILD | 同上 | 未执行 |
| llvm-profgen 构建并打包 | CMake、spec 文件清单 | 未执行 |
| BOLT runtime 构建 | BOLT runtime CMake、spec | 未执行 |
| compiler-rt profile runtime 构建 | compiler-rt CMake、spec | 未执行 |
| lld 子包 | spec 的子包定义和文件清单 | 未执行 |

## 7. Multi-Agent 框架契约

### 7.1 固定版本与可复核性

执行：`nice -n 19 ionice -c3 git -c gc.auto=0 clone https://github.com/lhmax2010/CodingSystem.git temp/CodingSystem`，退出码 0。只读检查 `git rev-parse HEAD`、`git ls-tree -r --name-only HEAD`、`git log -5`、编号文档摘录；`git status --porcelain` 为空。未修改或推送该仓库。

本节所有来源固定于 **commit `287d51c674e2b7d38605098338ff94fc8bb4e4fa`**（下文简称 `287d51c`，分支 `main`）。所有相对源码路径均相对于 `temp/CodingSystem/`，证据统一为 [03_codingsystem.txt](evidence/03_codingsystem.txt)，包含版本、完整 tracked 文件列表和带原始行号的必要摘录。结论仅覆盖该提交的 main，不推断其他分支或未提交工作。

| 项目 | 关键输出、结论 | 文件:行号 @ commit |
|---|---|---|
| 最新已冻结 HLD | `v1.0-draft-frozen`，状态 DRAFT FREEZE，含 E-01 勘误。只是架构草案冻结，正式 contract v1.0 仍需真实 Compiler 消费、五类 fixture、兼容矩阵 | `docs/00_Framework_HLD_v1.0_draft_frozen.md:3–6,31,497` @ `287d51c` |
| 最新契约 | `v0.11 Draft`，复审中，待第十一轮复审；规范包版本标识 `1.0.0.dev1`、DSL 1。不能宣称已冻结或可安装 | `docs/01_Contract_Spec_v0.11.md:3–6,37–41` @ `287d51c` |
| 业务设计指南 | HLD 引用 02–06_Agent_Design_Guide，但 tracked 树没有这些文件，Compiler/UT/Benchmark/Review/CI 各业务指南均未提供；07 onboarding、08 开发指南、09 分期计划也未入库 | `docs/00_Framework_HLD_v1.0_draft_frozen.md:6,16–22` @ `287d51c`；证据中的 `git ls-tree`（目录缺失证据无源码行号） |
| 实现程度 | `.dev_memory/current_state.md` 写“尚未包含业务代码”；实际 `framework/*`、`agents/compiler`、`agents/skeletons`、ci、conformance、pipelines 均只有 `.gitkeep`。存在规范，不存在可运行 SDK/框架实现证据 | `.dev_memory/current_state.md:3–29` @ `287d51c`；同提交 tracked 树 |
| 阶段判定 | HLD P0 还要求 00/01 draft freeze 及 08/09 就绪；当前 Contract 仍复审、08/09 缺失，不能宣称 P0 已完成。P1–P5 是计划，无代码或测试产物证明完成 | `docs/00_Framework_HLD_v1.0_draft_frozen.md:436–445`、`docs/01_Contract_Spec_v0.11.md:3–4` @ `287d51c` |

### 7.2 注册与接入（规范支持，运行时未实现）

| 项目 | 契约摘要 | 文件:行号 @ commit |
|---|---|---|
| 分发与注册 | 业务包依赖框架 wheel `codingsystem-framework`，通过 entry-point `codingsystem.agents` 注册；继承 `AgentBase`，实现 `setup(ctx)`、`execute(task) -> HandoffResult`、`teardown()` | `docs/00_Framework_HLD_v1.0_draft_frozen.md:259–278,414` @ `287d51c` |
| 注册字段 | `agent_type`、`task_prefix`、非空 `status_set`、`contract_requires`、`produces`、`hard_required_inputs`、`capabilities_required`；task_prefix 为 2–4 大写字母且全局唯一 | `docs/01_Contract_Spec_v0.11.md:35,176–182` @ `287d51c` |
| 准入 | 版本兼容与 conformance attestation 必须通过；attestation 绑定 Agent 制品 digest、contract 版本、套件版本；draft 期精确锁版本 `==1.0.0.devN` | `docs/01_Contract_Spec_v0.11.md:38,113` @ `287d51c` |
| 路由 | Agent 仅输出业务 status，编排层按 pipeline 路由；没有 target 字段。强依赖必须有唯一且支配消费者的同 series 生产者 | `docs/00_Framework_HLD_v1.0_draft_frozen.md:81`、`docs/01_Contract_Spec_v0.11.md:127,193–197` @ `287d51c` |
| 能力与副作用 | ctx 注入获准的 BuildExecutor/BoardPool 等句柄，不注入发布通道；构建/板上操作走 side_effect，框架承诺 at-least-once，效应侧承担幂等；effects 注册在 `codingsystem.effects`，build.* 必须可 probe，board.* 可 probe 或 replay_safe，publish.* 仅 broker | `docs/00_Framework_HLD_v1.0_draft_frozen.md:271,280–286`、`docs/01_Contract_Spec_v0.11.md:398–405,440–448` @ `287d51c` |
| 外部入口 | 框架外 Coding Agent 经 HTTP+JSON Skill 协议调用 create_run、submit_patch、get_status、get_result、cancel_run；不是业务插件注册面的替代物 | `docs/00_Framework_HLD_v1.0_draft_frozen.md:309–312` @ `287d51c` |

### 7.3 通用输入输出

以下均为 `docs/01_Contract_Spec_v0.11.md` @ `287d51c` 的规范定义，关键原文位于证据 `03_codingsystem.txt`。

| 消息 | 字段与语义 | 文件:行号 @ commit |
|---|---|---|
| TaskInput | run_id、task_id、dispatch_id、attempt；node、node_config、mode；series_id、snapshot_id；upstream 与 join_inputs。UpstreamItem 按生产节点/报告类型区分，ref=None 显式表示缺失 | `docs/01_Contract_Spec_v0.11.md:184–191` @ `287d51c` |
| HandoffResult | task_id、status、series_id、可选 series_candidate_id、artifact_refs、reason、metrics；不产 patch 时 candidate 为 None；metrics 是运行观测，不参与 digest | `docs/01_Contract_Spec_v0.11.md:193–197` @ `287d51c` |
| ArtifactRef / RunContext | 引用携带 digest/kind/media_type/data_class；上下文包含 snapshot manifest 引用、pipeline/contract 标识、实际授权能力 | `docs/01_Contract_Spec_v0.11.md:199–203` @ `287d51c` |
| ReportBase | report_type、task_id、run_id、series_id、created_at、data_class、inputs；产出报告在 artifact_refs 中以 report_type 为键；其他键不得冲突 | `docs/01_Contract_Spec_v0.11.md:208–213` @ `287d51c` |
| 类型扩展与门禁 | 模型默认 frozen/extra forbid；报告额外字段只能放 ext，键带组织前缀。比率使用定点字符串，threshold 读取报告顶层 gateable 字段并按 Decimal 比较；缺失/非法值 fail-closed | `docs/01_Contract_Spec_v0.11.md:14,41,134–135` @ `287d51c` |

### 7.4 Compiler 与 Benchmark

| Agent | 输入 | 输出 | 文件:行号 @ commit |
|---|---|---|---|
| Compiler | 通用 TaskInput/RunContext；fixture 声明不消费上游报告，这不等于无需 snapshot/series/config。BuildExecutor 设计接口是 `build(snapshot, series, targets)` | `BuildReport` + HandoffResult；fixture 状态 `build_passed` / `build_failed_exhausted`，前缀 CMP | `docs/01_Contract_Spec_v0.11.md:185–203,214,755–756`；`docs/00_Framework_HLD_v1.0_draft_frozen.md:340` @ `287d51c` |
| Benchmark | 通用 TaskInput，fixture 消费 BuildReport；HLD 以构建产物引用作为 hard-required 示例，需通过注册显式声明 | `BenchReport` + HandoffResult；fixture 状态 `bench_done` / `bench_failed`，前缀 BEN | `docs/01_Contract_Spec_v0.11.md:181,185–197,222,755,758`；`docs/00_Framework_HLD_v1.0_draft_frozen.md:303–304` @ `287d51c` |

BuildReport 类型体：`succeeded`、`targets_built`、`revdep_scope`、`failed_target`、`error_excerpt_ref`、`fix_patches`、`rounds_used`、`output_refs`（RPM 等产物引用）。来源：`docs/01_Contract_Spec_v0.11.md:214` @ `287d51c`。

BenchReport 类型体：`regression_pct`（所有指标最大回归，顶层 gateable 定点字符串）、`metrics: dict[str, MetricEntry]`、`baseline_ref`、`patch_relatedness_ref`；MetricEntry 有定点字符串 `value`、`baseline`、`regression_pct`。门禁应读取报告而非 HandoffResult.metrics。来源：`docs/01_Contract_Spec_v0.11.md:135,197,218,222` @ `287d51c`。

规范给出 `compiler_bench_only` 示例：Compiler 成功 → Benchmark → threshold（`benchmark.regression_pct <= 5.0`）→ review summary，default_route 为 fail_safe。这里 5.0 是框架示例，不是本项目已决定的 A/B 阈值。来源：`docs/01_Contract_Spec_v0.11.md:768–786` @ `287d51c`。

**未闭合的业务定义：** 这些通用契约未给出本项目 profile 类型、训练/验证场景、profile 与二进制身份绑定、跨架构产物及包仓提交的完整业务 schema。业务指南缺失，不能自行把它们写成上游既定接口。框架发布权限属于 broker，未来 profile 入包仓流程需要结合该边界设计；本轮不写实现。依据：上述报告定义，以及 `docs/00_Framework_HLD_v1.0_draft_frozen.md:6,87,271` @ `287d51c`。

## 8. 未完成项与续测条件

1. RPi4、RPi5 IP/端口：两板都未连接，需先按 model 确认身份，再完成 §4 全部实测。
2. GBS 元数据查询已完成；根目录配置与约定路径的差异已记录。若需要独立 debug 仓库，请后续提供实际配置，不推测 URL。
3. 提供内核、FFmpeg、GStreamer、Chromium 源码及 spec，并等待 LLVM 克隆完成：才能完成版本、编译参数、配置映射和源码行号结论。
4. 提供或指明 GBS root：用于平台工具分析拉回的实体库；本轮无库、无 build-id/strip/链接器结论。
5. CodingSystem 的 02–06 指南和后续契约复审/实现状态：当前 main 没有指南及代码，不把规划当作完成。

本轮没有任何板上写入、采样文件、库文件或编译产物。原始证据只含必要文本，合计低于 300KB。接续会话应先读取 [../STATUS.md](../STATUS.md)，补齐材料后在同一后续 commit 同步报告与状态。

## 9. 能力总表

依据：[02_sdb_devices.txt](evidence/02_sdb_devices.txt)。所有“未知”均因设备缺失而未探测，不能等同“不支持”。

| 板卡 | perf | 普通采样 | 分支栈 | ETM | SPE | BRBE | root |
|---|---|---|---|---|---|---|---|
| RPi4（尚未按 model 确认） | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 |
| RPi5（尚未按 model 确认） | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 | 未知 |
