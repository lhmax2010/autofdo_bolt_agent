# RPi4 PMU、perf 与媒体补充探测

| 结论 | 状态与证据 |
|---|---|
| 当前 PMU 设备存在，但没有绑定驱动；硬件事件源未注册 | **已确认**。`evidence/09_pmu_runtime.txt:46`（事件源及缺失的 driver 链接）、`:79`（仅 armv7-pmu 驱动）。 |
| 内核配置：最可能原因是 ARM32 配置未启用 ARM_PMUV3 | **高可信推断，未完全闭合**。`drivers/perf/Kconfig:146` 默认值是 ARM64；两个 defconfig 均未显式设置。A72 compatible 由 arm_pmuv3.c 匹配，arm_v7_pmu.c 不匹配。原始摘录：`evidence/08_pmu_config.txt`。 |
| 设备树：不是“运行 DT 完全没有 PMU 节点”或“节点 status=disabled” | **这两种原因已排除**。运行 `/pmu` compatible 为 arm,cortex-a72-pmu，status 缺省；平台设备已创建。`evidence/09_pmu_runtime.txt:64`。IRQ/固件是否还有后续问题尚未验证。 |
| 其他原因/未知：两份实际生成的 .config | **未知**。两次 make 均 exit=2，主机缺 flex，未生成 .config；不能把静态默认值当作生成结果。`evidence/08_pmu_config.txt:2`、`:23`、`:68`。 |
| perf 临时部署与采样 | **阻塞原因已更新为执行路径限制**。找到与构建时完全一致的 libllvm 并部署，但 `/tmp` 为 noexec；perf 启动 exit=126，加载器映射 exit=127。没有安装 RPM，没有进行采样。`evidence/13_perf_deployment.txt:75`、`:85`、`:96`。 |
| 60 秒 H.264 视频和解码基线 | **支持**。720p / 1080p 都解码到 EOS，real 分别 14.323 / 27.359 秒；没有 perf 数据。`evidence/11_media_smoke.txt`。 |

日期：2026-10-27（Asia/Shanghai）。这是 [01_env_probe_report.md](01_env_probe_report.md) 的补充；本轮只测试 RPi4。源码固定在 `src/linux-rpi` commit `42aeefac58edeb081aff440f0b60be71cbe49755`。没有 GBS root，没有编译内核、修改 defconfig/DT、remount 或重启。make 仅尝试配置目标，其 host 配置辅助程序生成在 temp/。以下源码路径均相对 WORKDIR/src/linux-rpi；证据文件相对本报告目录。后续用户允许配套 Base 仓库，改为仅解包部署、不安装 RPM；本报告已纳入该续测，证据 08–11 保留前一批真实记录，最新部署证据为 12–13。

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

## 3. 板上部署记录（仅解包，不安装 RPM）

### 来源与 LLVM 版本一致性

perf 来自镜像 BUILD_ID 对应快照，未使用 reference 回退：

`https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261022.054557/repos/standard/packages/`

`linux-kernel-perf-6.12.80-0.armv7l.rpm` SHA-256=`b6e48f1cd4f996b2101b9af167700f5a56ffa28acb02125098660ffa82b30323`，与 primary 一致；续测重新校验通过。RPM VCS=`platform/kernel/linux-rpi#21645b17c0d913e2ba7e10fbc9c993d286b3f57d`。

先检查 Unified 的 builddata/manifest 目录和 standard.xml，然后读取同快照根的 [build.xml](https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261022.054557/build.xml)：第 4 行 `base_id` 明确指定 **tizen-base-toolchain_20261020.074527**。因此选择实际配套 Base，而非近似 reference：

`https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261020.074527/repos/standard/packages/`

Base repomd/primary 下载成功，primary 压缩/解压 SHA-256 均通过。选中 `libllvm-22.1.8-1.6.armv7l.rpm`，SHA-256=`c22c4d7e2d18926f7aa918b14e24733ad92cba3db9f6b32ffd436650ede97407`，与 repodata 一致；`rpm -qp` 的 version-release 为 **22.1.8-1.6**。

`rpm -qp --requires` 对 LLVM 的要求是 `libLLVM.so.22.1` 和 `libLLVM.so.22.1(LLVM_22.1)`，并没有写包级 version-release 等式。候选包的 Provides 满足这两个 ABI 条件。为核实实际构建版本，还下载了同 Unified 快照的 [linux-rpi.buildlog.txt](https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261022.054557/builddata/buildlogs/standard/armv7l/succeeded/linux-rpi.buildlog.txt)：**第 114 行 libllvm-22.1.8-1.6，第 154 行 llvm-22.1.8-1.6，第 158 行 llvm-devel-22.1.8-1.6**。候选 version-release 与构建日志完全一致，不仅是 SONAME 相同。证据：[12_perf_dependencies.txt](evidence/12_perf_dependencies.txt)。

### 每项依赖由谁引入

本机按本次明确授权使用 `rpm2cpio | cpio` 解包，只读 `readelf -d` 的动态段；没有用本机工具解析板上 perf.data。两条命令都 exit=0，输出分别为 6725 / 65708 blocks：

```sh
nice -n 19 ionice -c3 bash -o pipefail -c 'rpm2cpio temp/rpms/linux-kernel-perf-6.12.80-0.armv7l.rpm | (cd temp/rpms/perf-extract && cpio -idm --no-absolute-filenames)'
nice -n 19 ionice -c3 bash -o pipefail -c 'rpm2cpio temp/rpms/libllvm-22.1.8-1.6.armv7l.rpm | (cd temp/rpms/llvm-extract && cpio -idm --no-absolute-filenames)'
```

扫描包内所有普通文件的 ELF magic，共五个 ELF 路径：`usr/bin/perf`、`usr/bin/trace`（硬链接）、三个 `usr/libexec/perf-core/dlfilters/dlfilter-{show-cycles,test-api-v0,test-api-v2}.so`。逐个 `readelf -d` 的全部 NEEDED 已列入证据 12。

- **libLLVM 是 perf 本身的直接依赖**：perf/trace 的 NEEDED 包含 `libLLVM.so.22.1`；另有 libunwind、libunwind-arm、pthread、rt、m、dl、z、elf、dw、crypto、stdc++、lzma、gcc_s、c 及 ld-linux。三个 dlfilter ELF 各自只直接 NEEDED libc.so.6。
- **perl 来自随包测试脚本**：`usr/libexec/perf-core/tests/shell/common/` 下 `check_all_lines_matched.pl`、`check_all_patterns_found.pl`、`check_errors_whitelisted.pl`、`check_no_patterns_found.pl` 第一行均为 `#!/usr/bin/perl`。`rpm -qp --scripts` 无输出；未发现 RPM 安装脚本引入 perl。ELF 的 NEEDED 没有 libperl。这解释包级 `/usr/bin/perl` 依赖，不代表已证明所有 perf 子命令都可无 perl 运行。
- libLLVM 的 NEEDED 为 rt、dl、m、z、xml2、stdc++、gcc_s、c、ld-linux；板上原有 `libxml2.so.16 -> libxml2.so.16.1.1`。尚未完成动态加载器的全部解析验证，不能据此声称所有间接库均可用。
- 前一批 `rpm -ivh --test` 失败仍保留在证据 10。本次没有运行安装/卸载/测试事务，没有推送或安装 perl；仅推送下表两个 ELF 文件。

### 推送清单与完整性

推送前 `df -h /tmp`：tmpfs 1.9G，已用 24K，可用 1.9G。两个文件共 36,634,172 字节。每项 `sdb push` exit=0；板上 `sha256sum` 与本机提取文件一致。仓库 URL 为上文两个完整 packages/ URL（下表简写 Unified / Base），文件均在结束时随 `/tmp/afdo_probe/` 删除。

| 板上路径 | 来源包 / version-release / 仓库 | 大小 | 文件 SHA-256 |
|---|---|---|---|
| /tmp/afdo_probe/perf | linux-kernel-perf / 6.12.80-0 / Unified | 2,992,296 B | `41b9b9a0d41da1b2a600c84ffa482ea05c52af54af094f5c6a2bf52d6aa13138` |
| /tmp/afdo_probe/lib/libLLVM.so.22.1 | libllvm / 22.1.8-1.6 / Base | 33,641,876 B | `49fcc90da72ac2eabd7bbdb0a71566ea2284a532f98730ca46496782f30fb69e` |

运行环境设置 `LD_LIBRARY_PATH=/tmp/afdo_probe/lib`，HOME/TMPDIR/PERF_CONFIG、GStreamer registry/cache 均指向临时目录。未推送其他缺失库或媒体；前者因动态解析在主程序映射阶段就受阻，后者因无法进行 perf 采样，无需重复上一批已完成的解码基线。

### 动态解析与执行失败（停止条件）

```text
$ chmod 755 /tmp/afdo_probe/perf; ldd /tmp/afdo_probe/perf
REMOTE_EXIT=1
ldd: warning: you do not have execution permission for `/tmp/afdo_probe/perf'
    not a dynamic executable

$ mount | grep -E ' /tmp | / '
/dev/mmcblk0p2 on / type ext4 (rw,relatime,mb_optimize_scan=0)
tmpfs on /tmp type tmpfs (rw,nosuid,nodev,noexec)

$ LD_DEBUG=libs /tmp/afdo_probe/perf --buildid-dir /tmp/afdo_probe/buildid --version
REMOTE_EXIT=126
/bin/sh: /tmp/afdo_probe/perf: Permission denied

$ LD_DEBUG=libs /lib/ld-linux.so.3 --list /tmp/afdo_probe/perf
REMOTE_EXIT=127
/tmp/afdo_probe/perf: error while loading shared libraries: /tmp/afdo_probe/perf: failed to map segment from shared object
```

`ls -l` 确认 perf 为 `-rwxr-xr-x`；`ls -lZ` 记录其标签 System、shell 标签 User::Shell。没有改变 Smack 标签或策略。**已确认 /tmp 的 noexec 足以阻止该路径运行**；尚未排除其他访问控制问题。ldd 的 “not a dynamic executable” 发生在执行权限检查失败后，不能解读成文件实际为静态 ELF；readelf 已证明它有动态段。加载器在 perf 本身映射阶段失败，未输出完整 NEEDED 解析结果，因此库解析验收为**未知/未通过**，也没有“缺失库为零”的结论。

按用户要求在此停止，未 remount、未迁移到其他可执行目录、未安装 RPM。RPM 包数开始/结束均 **1252**；额外比较两次完整 `rpm -qa` 集合，新增=[]、删除=[]。清理 `rm -rf -- /tmp/afdo_probe` 的 REMOVE_EXIT=0，随后不存在检查 ABSENT_TEST_EXIT=0。无需 rpm -e。证据：[13_perf_deployment.txt](evidence/13_perf_deployment.txt)。

## 4. 视频素材与 GStreamer 基线（前一批，未重复运行）

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

**版本命令已尝试但启动失败：exit=126，stderr 为 Permission denied；其余采样、报告和 list 均未执行。** 未执行项退出码/stderr/样本数为“不适用：临时执行路径 noexec 阻塞”，不能填 0 或“不支持硬件”。最终临时 perf 已删除，系统 perf 未安装。可见 software 事件源仅说明内核接口存在，尚不能证明 cpu-clock 实际采样成功。

| 计划项（perf 均应带 --buildid-dir /tmp/afdo_probe/buildid） | 本轮结果 |
|---|---|
| `perf --version` | 启动失败 exit=126，未取得版本输出；RPM 版本已核实 |
| `perf list sw`、`perf list hw` | 未执行，未知 |
| `perf record -e cpu-clock -F 999 -a -o /tmp/afdo_probe/s1.data -- sleep 3`，随后 report --stdio --sort dso 取前 40 行确认非零样本 | 未执行，未知 |
| `perf record -e cycles -a -o /tmp/afdo_probe/h1.data -- sleep 2`，随后 report | 未执行，未知；当前无硬件事件源 |
| `perf record -e cycles -b -o /tmp/afdo_probe/b1.data -- sleep 1`，成功后 script -F brstack | 未执行，未知；没有用退出码代替分支数据验证 |
| 720p cpu-clock -F 999 record、report --sort dso 与 --sort dso,sym（各取前 30 行） | 未执行，无样本、符号解析率或 perf 开销数据 |
| 1080p cpu-clock record 与计时 | baseline 满足时长门槛，但临时路径 noexec 阻塞，未执行 |

未产生或拉回任何 perf.data。板上 `/tmp/afdo_probe/` 已删除，REMOVE_EXIT=0、ABSENT_TEST_EXIT=0；临时视频、RPM、registry/cache 均随目录清理。本次清理证据：[13_perf_deployment.txt](evidence/13_perf_deployment.txt)；前一批见 [09_pmu_runtime.txt](evidence/09_pmu_runtime.txt)。

## 6. 后续最小候选修复（未实施）

1. 由用户提供 flex 等配置生成所需工具，或提供在可信工具链下生成的两份 `.config`；继续坚持不在本机擅自安装。确认 ARM_PMUV3 和其依赖的最终值，并核对实际镜像内核配置/源码版本。
2. 若最终 ARM 配置确实未启用 PMUv3，候选最小改动是 ARM 的 `tizen_bcm2711_defconfig` 加 `CONFIG_ARM_PMUV3=y`。当前 DT 已具备正确 A72 PMU 节点，暂不建议修改 compatible 或添加重复节点。
3. 经后续独立授权构建/部署后，验证 armv8-pmu 驱动注册、PMU 设备绑定、事件源以及 cycles 非零样本，再判断有无 IRQ/固件障碍；本轮不做构建、部署和重启。
4. 配套 Base 来源和构建时 LLVM version-release 已核实一致。当前需用户提供符合写入边界且允许执行/映射的测试路径或预置 perf 的镜像，再完成 ldd/LD_DEBUG 验收和采样。本次明确禁止 remount 和 RPM 安装，不能在现有范围内消除 /tmp 的 noexec 阻塞。
5. 即使 PMUv3 cycles 修复成功，也不能据此宣称分支栈、ETM、SPE、BRBE 可用；这些需要独立硬件、驱动和实际 trace 验证。

## 7. 边界例外与证据体积

- 沿用历史例外 `/tmp/sdb.log`：SDB 共享服务既有日志，0 B，mtime 为 2026-10-26 22:36:47，本轮观察未变；未删除、未重启服务。避免该路径需协调 daemon 的启动方式，本轮不调整共享服务。历史证据 [07_boundary.txt](evidence/07_boundary.txt)。
- 用户显式提供的附件只作为本次指令读取；项目源码、配置、数据来自 WORKDIR，下载和临时脚本均放 temp/。正常 GitHub 认证按 STATUS 的规则澄清使用。
- 本轮未观察到新增的工作区外产出；没有全进程 syscall 审计，不能声称完整证明不存在任何隐式系统写入。板上只保留既有软件，安装 0 包，测试文件均已清理。
- 本次新增证据 12–13 共 14,646 字节；补充轮 08–13 共 48,853 字节；包括原有证据在内共 185,033 字节，低于本轮 200KB 限额。二进制、完整下载和日志留在忽略目录，不提交。

## 8. RPi4 当前能力表

| 验收项 | 结论 | 依据 |
|---|---|---|
| perf 可用性 | 不支持（当前环境） | 临时 perf 已部署但 noexec 阻止执行；未安装 RPM |
| 软件采样 | 未知 | software 事件源可见，未运行 cpu-clock record |
| 硬件 cycles | 未知 | 未实测，当前没有 CPU PMU 事件源 |
| 分支栈 | 未知 | 未执行 record/script，未取得分支数据 |
| 程序级 DSO 归属 | 未知 | 未产生 perf 样本，不能判断 libgstlibav/libavcodec 的归属 |
| 符号解析 | 未知 | 未产生 perf report，未验证导出函数或其他符号的解析 |


“当前不支持”指本次镜像暴露的接口；“未知”指缺少实际采样证明，不代表芯片没有该能力。

| 板 | perf 工具可用 | cpu-clock 采样 | cycles 采样 | 分支栈 | ETM | SPE | BRBE | root | H.264 软解 |
|---|---|---|---|---|---|---|---|---|---|
| RPi4 / armv7l | 不支持：临时路径 noexec，未安装 | 未知：软件源存在，未实测 | 未知：未实测，当前无 PMU 事件源 | 未知：未实测 | 当前不支持：无事件源 | 当前不支持：无事件源 | 未知：未实测；源码未发现配置项 | 支持 | 支持：720p/1080p 到 EOS |
