# RPi4 PMU、perf 与媒体补充探测

| 结论 | 状态与证据 |
|---|---|
| 当前 PMU 设备存在，但没有绑定驱动；硬件事件源未注册 | **已确认**。`evidence/09_pmu_runtime.txt:46`（事件源及缺失的 driver 链接）、`:79`（仅 armv7-pmu 驱动）。 |
| 内核配置：最可能原因是 ARM32 配置未启用 ARM_PMUV3 | **高可信推断，未完全闭合**。`drivers/perf/Kconfig:146` 默认值是 ARM64；两个 defconfig 均未显式设置。A72 compatible 由 arm_pmuv3.c 匹配，arm_v7_pmu.c 不匹配。原始摘录：`evidence/08_pmu_config.txt`。 |
| 设备树：不是“运行 DT 完全没有 PMU 节点”或“节点 status=disabled” | **这两种原因已排除**。运行 `/pmu` compatible 为 arm,cortex-a72-pmu，status 缺省；平台设备已创建。`evidence/09_pmu_runtime.txt:64`。IRQ/固件是否还有后续问题尚未验证。 |
| 其他原因/未知：两份实际生成的 .config | **未知**。两次 make 均 exit=2，主机缺 flex，未生成 .config；不能把静态默认值当作生成结果。`evidence/08_pmu_config.txt:2`、`:23`、`:68`。 |
| perf 安装与采样 | **阻塞**。同期 RPM 已下载并校验；板上依赖测试 exit=1，缺 perl/LLVM；同一仓库无提供者，未实际安装。`evidence/10_perf_package.txt:252`。 |
| 60 秒 H.264 视频和解码基线 | **支持**。720p / 1080p 都解码到 EOS，real 分别 14.323 / 27.359 秒；没有 perf 数据。`evidence/11_media_smoke.txt`。 |

日期：2026-10-27（Asia/Shanghai）。这是 [01_env_probe_report.md](01_env_probe_report.md) 的补充；本轮只测试 RPi4。源码固定在 `src/linux-rpi` commit `42aeefac58edeb081aff440f0b60be71cbe49755`。没有 GBS root，没有编译内核、修改 defconfig/DT、remount 或重启。make 仅尝试配置目标，其 host 配置辅助程序生成在 temp/。以下源码路径均相对 WORKDIR/src/linux-rpi；证据文件相对本报告目录。

## 1. 配置生成与源码判断

所有本机命令先设置 `TMPDIR=WORKDIR/temp/tmp`。依次执行：

```sh
nice -n 19 ionice -c3 make -C src/linux-rpi O=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kcfg-arm ARCH=arm tizen_bcm2711_defconfig
nice -n 19 ionice -c3 make -C src/linux-rpi O=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kcfg-arm64 ARCH=arm64 tizen_bcm2711_defconfig
```

两项退出码均为 **2**，stderr 为 `/bin/sh: 1: flex: not found`，随后 lexer.lex.c 的 make 规则报 Error 127。没有安装 flex/bison 或替换生成工具。两处 `.config` 都不存在。本机 gcc 为 13.3.0，`.conf.o.cmd` 显示 gcc 编译了 host Kconfig 辅助对象；目标内核编译器尚未运行。下述 PMU 核心选项依赖架构/CPU 与 PERF_EVENTS，没有直接的编译器能力测试；这种静态关系不受 GCC/Clang 选择影响，但配置生成失败仍不能提供实际值。没有 GBS 工具链配置结果，编译器相关的 DEBUG_INFO 等依赖不能替代验证。开始和结束的 `git -C src/linux-rpi status --porcelain` 均为空。证据：[08_pmu_config.txt](evidence/08_pmu_config.txt)。

下表的“生成值”严格指本次 make 的产物；静态解释用于定位，不是 .config 测量值。符号均带 `CONFIG_` 前缀。

| 符号 | ARM 生成值 | ARM64 生成值 | 静态依赖/default 与预期；文件:行号 |
|---|---|---|---|
| PERF_EVENTS | 未知 | 未知 | `init/Kconfig:1899`，依赖 HAVE_PERF_EVENTS，PROFILING 时 default y；两个 defconfig 的 PROFILING=y 分别在 `arch/arm/configs/tizen_bcm2711_defconfig:33`、`arch/arm64/configs/tizen_bcm2711_defconfig:34`。 |
| HW_PERF_EVENTS | 未知 | 未知 | `arch/arm/Kconfig:1275` / `arch/arm64/Kconfig:1545`，依赖 ARM_PMU，def_bool y。 |
| ARM_PMU | 未知 | 未知 | `drivers/perf/Kconfig:58`，ARM 或 ARM64，default y；外层菜单还依赖 PERF_EVENTS（`:6`）。 |
| ARM_PMUV3 | 未知 | 未知 | `drivers/perf/Kconfig:146`，依赖 HW_PERF_EVENTS 且 ARM+CPU_V7 或 ARM64；default ARM64。两个 defconfig 没有显式项，因此预期 ARM=n、ARM64=y，待配置生成验证。 |
| CORESIGHT | 未知 | 未知 | `drivers/hwtracing/coresight/Kconfig:5`，ARM/ARM64 且 OF/ACPI，无 default y；未显式启用时预期 n。 |
| CORESIGHT_SOURCE_ETM3X | 未知 | 未知 | 同文件 `:87`，外层 CORESIGHT，且 !ARM64；无 default y。ARM 默认 n，ARM64 依赖不满足。 |
| CORESIGHT_SOURCE_ETM4X | 未知 | 未知 | 同文件 `:100`，外层 CORESIGHT 且 ARM64；无 default y。ARM 依赖不满足，ARM64 默认 n。 |
| ARM_SPE_PMU | 未知 | 未知 | `drivers/perf/Kconfig:218`，ARM64 专属 tristate，无 default y。ARM 不可选，ARM64 默认 n。 |
| ARM64_BRBE | 未知 | 未知 | `rg -n ARM64_BRBE src/linux-rpi/arch/arm64 src/linux-rpi/drivers/perf` exit=1；相关源码未定义该符号，不应把“符号不存在”伪写成生成的 n。 |
| KALLSYMS | 未知 | 未知 | `init/Kconfig:1831`，default y；运行板确实可读 kallsyms，未据此补填本地生成值。 |
| KALLSYMS_ALL | 未知 | 未知 | `init/Kconfig:1852`，依赖 DEBUG_KERNEL && KALLSYMS，无 default y，预期 n。 |
| DEBUG_INFO | 未知 | 未知 | `lib/Kconfig.debug:227` 隐藏 bool，由 DWARF4 等 select（`:271`）；两个 defconfig 的 DWARF4=y 在 `:530` / `:540`。相关编译器/汇编器依赖需要有效工具链再验证。 |
| THUMB2_KERNEL | 未知 | 未知 | `arch/arm/Kconfig:1137`，CPU_V7/CPU_V7M 且非 CPU_V6/CPU_V6K；只在 CPU_THUMBONLY 时 default y。此 ARM 平台预期 n；ARM64 不适用。 |
| PID_IN_CONTEXTIDR | 未知 | 未知 | `arch/arm/Kconfig.debug:1831` 依赖 CPU_COPY_V6，`arch/arm64/Kconfig.debug:3` 无该限制；均无 default y。ETM4X 会 select，但当前未显式启用，预期 n。 |

### PMU 驱动与设备树对应

- `arch/arm/boot/dts/broadcom/bcm2711.dtsi:435` 定义 PMU，compatible=`arm,cortex-a72-pmu`；IRQ 为 GIC_SPI 16–19，affinity 对应 cpu0–3，无 status 属性。
- ARM 板 DTS 在 `arch/arm/boot/dts/broadcom/bcm2711-rpi-4-b.dts:5` 包含该 dtsi；ARM64 DTS 在 `arch/arm64/boot/dts/broadcom/bcm2711-rpi-4-b.dts:2` 复用 ARM 的 RPi4 DTS。
- `drivers/of/base.c:452`、`:466` 明确 status 缺省意味着 available。因此运行 DT 的缺省 status 不是 disabled。
- `drivers/perf/arm_pmuv3.c:1383` 匹配 A72，`drivers/perf/Makefile:9` 由 ARM_PMUV3 控制编入；驱动名在 `include/linux/perf/arm_pmu.h:183` 为 armv8-pmu，注册在 `drivers/perf/arm_pmuv3.c:1420`。
- `drivers/perf/arm_v7_pmu.c:1947` 的匹配表含 A7/A8/A9/A12/A15/A17 等，没有 A72。运行板出现 armv7-pmu 并不意味着 A72 PMU 可用。
- 对 bcm2711.dtsi、bcm283x.dtsi、bcm270x.dtsi、bcm270x-rpi.dtsi 及两份 RPi4 DTS 执行 `rg -n 'etm|coresight' ...`，exit=1 无匹配。这个检查范围与运行 DT 深度 2 的检查均未发现 ETM/CoreSight 节点，不把它外推成芯片的完整硬件能力证明。

全部命令、退出码、源码行号摘录见 [08_pmu_config.txt](evidence/08_pmu_config.txt)。源码 commit 与 perf RPM 的 VCS commit 不同，当前没有可读的运行内核配置；因此“ARM_PMUV3 未启用”保持高可信推断，不能宣布运行镜像根因完全闭合。

## 2. RPi4 实机验证

通过 `sdb connect 192.168.108.26`，按 model 确认为 Raspberry Pi 4 Model B Rev 1.5；serial=`192.168.108.26:26101`。没有按 IP 推断板型。已在 root 会话运行，`id` 为 uid=0。

| 命令/探测项 | 关键输出、退出情况与结论 |
|---|---|
| `cat /proc/device-tree/model; uname -m; uname -r; cat /etc/os-release` | RPi4 / armv7l / 6.12.80-arm-rpi4-v7l，Tizen 11；BUILD_ID=`tizen-unified-toolchain_20261022.054557_tizen-headed-armv7l`。支持身份确认。 |
| `id; mount \| grep " / "` | root；`/dev/mmcblk0p2 on / type ext4 (rw,relatime,mb_optimize_scan=0)`。根原本可写，没有 remount。 |
| `dmesg \| grep -i -E 'perfevents\|hw perf\|pmu'` | grep exit=1，stdout/stderr 空；未获得 PMU 初始化成功日志，仅表示本次过滤未匹配。 |
| `find /proc/device-tree -maxdepth 2 ...` | 原命令未跟随入口符号链接而无输出；不能据此断言没有 PMU。 |
| `find -H /proc/device-tree -maxdepth 2 ...`；读取 compatible/status | 修正后发现 `/pmu`，A72 compatible，status 缺省；exit=0。 |
| `ls /sys/bus/event_source/devices/` | 只有 breakpoint/kprobe/software/tracepoint/uprobe；硬件 CPU PMU、ETM、SPE 事件源当前不支持。 |
| `ls -ld /sys/bus/platform/drivers/*pmu*`；读取 pmu modalias/uevent | 只有 armv7-pmu 驱动；设备 modalias=`of:NpmuT(null)Carm,cortex-a72-pmu`。 |
| `ls -l /sys/bus/platform/devices/pmu*/driver` | No such file or directory，exit=2；PMU 设备未绑定。 |
| `grep -E 'armv8pmu\|armv7pmu\|armpmu' /proc/kallsyms \| head -25` | 可看到 armpmu 通用框架符号；因截断，不用此输出证明所有 armv8 符号不存在。 |

原始分组命令、远端退出码及 stderr 在 [09_pmu_runtime.txt](evidence/09_pmu_runtime.txt)。分组命令的退出码是最后命令的状态，不能覆盖每个子命令；表中的独立失败也保留在 stderr 中。

## 3. 同期 perf RPM 与安装阻塞

选择镜像 BUILD_ID 对应的真实快照，未使用 reference 回退：

`https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261022.054557/repos/standard/packages/`

下载 repomd.xml 与其中 primary.xml.gz，压缩和解压后 checksum 都通过。primary 中找到 armv7l `linux-kernel-perf-6.12.80-0`；RPM 保存为 `temp/rpms/linux-kernel-perf-6.12.80-0.armv7l.rpm`。SHA-256=`b6e48f1cd4f996b2101b9af167700f5a56ffa28acb02125098660ffa82b30323`，与仓库一致。RPM 元数据 VCS=`platform/kernel/linux-rpi#21645b17c0d913e2ba7e10fbc9c993d286b3f57d`。

本机 `nice -n 19 ionice -c3 rpm -qpR temp/rpms/linux-kernel-perf-6.12.80-0.armv7l.rpm` exit=0，完整 Requires 见 [10_perf_package.txt](evidence/10_perf_package.txt)。随后推入板上临时目录，执行：

```sh
nice -n 19 ionice -c3 rpm -ivh --test /tmp/afdo_probe/linux-kernel-perf-6.12.80-0.armv7l.rpm
```

远端 exit=1，stderr 原文：

```text
error: Failed dependencies:
    /usr/bin/perl is needed by linux-kernel-perf-6.12.80-0.armv7l
    libLLVM.so.22.1 is needed by linux-kernel-perf-6.12.80-0.armv7l
    libLLVM.so.22.1(LLVM_22.1) is needed by linux-kernel-perf-6.12.80-0.armv7l
```

同一快照仓库 armv7l/noarch 的 primary Provides、/usr/bin/perl 文件记录、perl/libllvm 包名查询均无提供者。后两行依赖是同一个 LLVM 库的两个能力标识，不能当作两个独立包。需要配套 Base-Toolchain 等其他仓库才能继续解析；这超出本次“同一仓库”的明确约束，已请求用户澄清，尚未获准。不擅自跨库，也没有用 `--nodeps`、`--force` 绕过。

**安装记录：实际安装 0 包、下载依赖 0 包；仅运行 --test。** 前后完整 `rpm -qa` 集合差集 added=[]、removed=[]。`rpm -q linux-kernel-perf` exit=1：package ... is not installed。未执行安装后的 `rpm -ql`，因为没有已安装 perf 包。根本来可写，因此也没有触发只读根的临时解包运行分支。

**卸载记录：本轮无需执行卸载，无新增包。** 当前不要运行 `rpm -e linux-kernel-perf`；未来若获得跨库授权并成功安装，必须按实际新增包名和依赖顺序另行记录完整回滚命令，不能把未知依赖列表写成可执行卸载方案。

## 4. 视频素材与 GStreamer 基线

Blender 官方 BBB/Sunflower 1080p/30fps MP4 从官方 ZIP 获取，未采用合成备用画面。`ffmpeg` 的 libx264 已可用；没有安装主机工具。截取原片 300–360 秒，依次编码 1080p 8M 与 720p 4M；High、yuv420p、30fps、无音轨、60 秒。完整下载/编码/ffprobe 命令、源/产物 SHA-256、CC BY 3.0 署名见 [media/README.md](../../media/README.md)。MP4 仅保留在本机 media/，`.gitignore` 已加入 `media/*.mp4`。

| 视频 | ffprobe | 编码 exit/耗时 | 板上不带 perf 解码 real/user/sys | 带 perf 耗时 | 结果 |
|---|---|---|---|---|---|
| bbb_720p_h264_60s.mp4 | 1280×720，High，yuv420p，30/1，60.000000s，1800 帧，4,000,178 bit/s | 0 / 8.042s | 14.323 / 29.752 / 1.149s | 未执行 | 支持；EOS，exit=0 |
| bbb_1080p_h264_60s.mp4 | 1920×1080，High，yuv420p，30/1，60.000000s，1800 帧，8,047,973 bit/s | 0 / 13.570s | 27.359 / 64.107 / 1.199s | 未执行 | 支持；EOS，exit=0，低于 180 秒 |

1800 帧来自 MP4 的 nb_frames 元数据，未做独立逐帧计数。板上命令主体为：

```sh
time nice -n 19 ionice -c3 gst-launch-1.0 filesrc location=/tmp/afdo_probe/bbb_720p_h264_60s.mp4 ! qtdemux ! h264parse ! avdec_h264 ! fakesink sync=false
```

1080p 同样管线，外层 sh 写 PID 到临时目录以便超时控制，完整实际命令见 [11_media_smoke.txt](evidence/11_media_smoke.txt)。720p 首次 registry 扫描有不相关 cairo 插件缺 libGLESv2.so.2 的警告，但目标 avdec_h264 管线运行到 EOS；没有为此扩展安装范围。两次单次 smoke baseline 受不同分辨率、首次缓存建立、后台负载影响，不用作优化 A/B 性能收益证据。

板上进程使用 `HOME=/tmp/afdo_probe/home TMPDIR=/tmp/afdo_probe PERF_CONFIG=/tmp/afdo_probe/perfconfig GST_REGISTRY=/tmp/afdo_probe/gst-registry.bin XDG_CACHE_HOME=/tmp/afdo_probe/cache`。

## 5. 采样验收状态

**以下全部未执行，退出码/stderr/样本数均为“不适用：前置 perf 依赖阻塞”，不能填 0 或“不支持硬件”。** 最终 `command -v perf` 无输出，rpm 查询未安装。可见 software 事件源仅说明内核接口存在，尚不能证明 cpu-clock 实际采样成功。

| 计划项（perf 均应带 --buildid-dir /tmp/afdo_probe/buildid） | 本轮结果 |
|---|---|
| `perf list sw`、`perf list hw`、`perf --version` | 未执行，未知 |
| `perf record -e cpu-clock -F 999 -a -o /tmp/afdo_probe/s1.data -- sleep 3`，随后 report --stdio --sort dso 取前 40 行确认非零样本 | 未执行，未知 |
| `perf record -e cycles -a -o /tmp/afdo_probe/h1.data -- sleep 2`，随后 report | 未执行，未知；当前无硬件事件源 |
| `perf record -e cycles -b -o /tmp/afdo_probe/b1.data -- sleep 1`，成功后 script -F brstack | 未执行，未知；没有用退出码代替分支数据验证 |
| 720p cpu-clock -F 999 record、report --sort dso 与 --sort dso,sym（各取前 30 行） | 未执行，无样本、符号解析率或 perf 开销数据 |
| 1080p cpu-clock record 与计时 | baseline 满足时长门槛，但 perf 阻塞，未执行 |

未产生或拉回任何 perf.data。板上 `/tmp/afdo_probe/` 已删除，REMOVE_EXIT=0、ABSENT_TEST_EXIT=0；临时视频、RPM、registry/cache 均随目录清理。证据：[09_pmu_runtime.txt:120](evidence/09_pmu_runtime.txt)。

## 6. 后续最小候选修复（未实施）

1. 由用户提供 flex 等配置生成所需工具，或提供在可信工具链下生成的两份 `.config`；继续坚持不在本机擅自安装。确认 ARM_PMUV3 和其依赖的最终值，并核对实际镜像内核配置/源码版本。
2. 若最终 ARM 配置确实未启用 PMUv3，候选最小改动是 ARM 的 `tizen_bcm2711_defconfig` 加 `CONFIG_ARM_PMUV3=y`。当前 DT 已具备正确 A72 PMU 节点，暂不建议修改 compatible 或添加重复节点。
3. 经后续独立授权构建/部署后，验证 armv8-pmu 驱动注册、PMU 设备绑定、事件源以及 cycles 非零样本，再判断有无 IRQ/固件障碍；本轮不做构建、部署和重启。
4. perf 需先解决仓库范围：允许使用配套 Base-Toolchain 时，再校验版本/SHA-256、递归依赖和 `rpm --test`，依赖包总数超过 5 个即停止。尚未批准时停在现状。
5. 即使 PMUv3 cycles 修复成功，也不能据此宣称分支栈、ETM、SPE、BRBE 可用；这些需要独立硬件、驱动和实际 trace 验证。

## 7. 边界例外与证据体积

- 沿用历史例外 `/tmp/sdb.log`：SDB 共享服务既有日志，0 B，mtime 为 2026-10-26 22:36:47，本轮观察未变；未删除、未重启服务。避免该路径需协调 daemon 的启动方式，本轮不调整共享服务。历史证据 [07_boundary.txt](evidence/07_boundary.txt)。
- 用户显式提供的附件只作为本次指令读取；项目源码、配置、数据来自 WORKDIR，下载和临时脚本均放 temp/。正常 GitHub 认证按 STATUS 的规则澄清使用。
- 本轮未观察到新增的工作区外产出；没有全进程 syscall 审计，不能声称完整证明不存在任何隐式系统写入。板上只保留既有软件，安装 0 包，测试文件均已清理。
- 新证据 08–11 共 34,207 字节；包括原有证据在内共 170,387 字节，低于本轮 200KB 限额。二进制、完整下载和日志留在忽略目录，不提交。

## 8. RPi4 当前能力表

| 验收项 | 结论 | 依据 |
|---|---|---|
| perf 可用性 | 不支持（当前环境） | 命令缺失；RPM 依赖测试失败，未安装 |
| 软件采样 | 未知 | software 事件源可见，未运行 cpu-clock record |
| 硬件 cycles | 未知 | 未实测，当前没有 CPU PMU 事件源 |
| 分支栈 | 未知 | 未执行 record/script，未取得分支数据 |
| 程序级 DSO 归属 | 未知 | 未产生 perf 样本，不能判断 libgstlibav/libavcodec 的归属 |
| 符号解析 | 未知 | 未产生 perf report，未验证导出函数或其他符号的解析 |


“当前不支持”指本次镜像暴露的接口；“未知”指缺少实际采样证明，不代表芯片没有该能力。

| 板 | perf 工具可用 | cpu-clock 采样 | cycles 采样 | 分支栈 | ETM | SPE | BRBE | root | H.264 软解 |
|---|---|---|---|---|---|---|---|---|---|
| RPi4 / armv7l | 不支持：未安装、依赖阻塞 | 未知：软件源存在，未实测 | 未知：未实测，当前无 PMU 事件源 | 未知：未实测 | 当前不支持：无事件源 | 当前不支持：无事件源 | 未知：未实测；源码未发现配置项 | 支持 | 支持：720p/1080p 到 EOS |
