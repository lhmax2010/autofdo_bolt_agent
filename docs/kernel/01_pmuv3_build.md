# RPi4 armv7l：准备启用 ARM PMUv3 的内核构建

第一段记录（2026-10-27）：本次只完成第一段：源码 worktree、唯一配置改动、本地内核提交、固定仓库配置与一键脚本。**没有执行 gbs/export/make 构建，没有连接开发板，没有产生内核 RPM，也没有编写或执行板上安装操作。** 第二段等用户通知构建结束后再做。

## 2026-10-28 执行状态

构建于 2026-10-28 11:56:53 启动，日志于 12:30:30 报告成功（33 分 37 秒），无重跑。ALL-END 缺失、真实 GBS 退出码未取得。用户随后明确批准以 depanneur success、HTML Succeeded、15 个二进制 RPM + 1 个 SRPM 的实存/时间/哈希一致性代替退出码验收，**三项全部通过**。普通版与镜像基线完整配置相比，仅 ARM_PMUV3 从 n 变 y；RT 实际仍为 n。见 [03_pmuv3_build_result.md](03_pmuv3_build_result.md) 与 [安装/回退步骤](02_pmuv3_install.md)。下文第一段的“未执行”为历史状态。

本轮另对包装脚本做了会话脱离修复：整个 worker 用 setsid --fork 启动，继承 fd 9 锁；GBS 用 setsid --wait 保留真实退出码。只通过 bash -n，**修复未经运行验证，下次构建时验证**；本轮没有执行修复后的脚本，也没有连接开发板。具体回收机制未确认，只能推断；不能保证抵抗 cgroup 清理/SIGKILL/断电。

## 用户执行入口

在本机终端直接运行，路径和参数已经固定：

```sh
/bin/bash /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/scripts/build_pmuv3_kernel.sh
```

第一段首次构建估算 **2–6 小时**（本次实际至成功日志为 **33 分 37 秒**；未来仍取决于负载），受下载、模拟/交叉构建、低优先级和共享主机负载影响，可能更久；不是实测承诺。当前 `nproc=20`，脚本运行时重新计算，make 使用 `max(1, floor(nproc/2))`，当前为 `-j10`；`--threads 1` 限制 GBS 同时只构建一个源包。普通内核和 RT 内核按 spec 顺序都编译。

按 depanneur 0.16.30 随包的 NOPASSWD 规则，**预计不会要求 sudo 密码，脚本跳过 sudo -v**。本轮未调用任何 sudo 命令，没有读取受保护的本机 sudoers 内容；若机器策略另有覆盖，后台构建将失败并记录，不能保证实际免密。详见 sudo 源码核查一节。

脚本前台完成预检后，只在最后打印以下查看命令；关闭 `tail` 不等于停止构建：

```sh
tail -f /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/logs/build_pmuv3.log
cat /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/logs/build_pmuv3.status
```

后续正常流程仍以 `ALL-END <时间> OK` 为入口；缺标记不得补写成功。本次例外按用户后续明确授权的替代证据验收通过，不更改原 status。

## 1. 精确基线与唯一改动

- 镜像：`tizen-unified-toolchain_20261022.054557`。
- 镜像包 VCS 基线：`21645b17c0d913e2ba7e10fbc9c993d286b3f57d`。
- `git -C src/linux-rpi cat-file -e 21645b17c0d913e2ba7e10fbc9c993d286b3f57d^{commit}` 返回 **0**，所以使用精确基线，没有 fetch、没有回退到当前 HEAD。
- 原工作树仍在 `42aeefac58edeb081aff440f0b60be71cbe49755` / tizen；开始和结束 `git status --porcelain` 都为空。Git worktree 必需的共享元数据和 local 提交署名会更新，检出的源码文件未改。
- 新工作树：`/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/linux-rpi-pmuv3`；分支 `afdo/pmuv3`。
- 内核本地提交：`c27f160de761bb55f64672ceac642698a6e93684`，署名 Hao Lin <hao.lin@samsung.com>。该提交只在 linux-rpi 本地仓库，**没有推送到结果仓库或内核远端**。
- 唯一改动：ARM 普通 `arch/arm/configs/tizen_bcm2711_defconfig` 的 CONFIG_PROFILING=y 后插入 CONFIG_ARM_PMUV3=y。没有 savedefconfig，没有改 spec、RT defconfig 或 ARM64 defconfig。

创建命令（已执行，不要重复）：

```sh
nice -n 19 ionice -c3 git -C /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/src/linux-rpi worktree add -b afdo/pmuv3 /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/linux-rpi-pmuv3 21645b17c0d913e2ba7e10fbc9c993d286b3f57d
```

`git diff 21645b17c0d913e2ba7e10fbc9c993d286b3f57d..afdo/pmuv3 --stat`：

```text
 arch/arm/configs/tizen_bcm2711_defconfig | 1 +
 1 file changed, 1 insertion(+)
```

完整 diff：

```diff
diff --git a/arch/arm/configs/tizen_bcm2711_defconfig b/arch/arm/configs/tizen_bcm2711_defconfig
index bf97a71b2c3d..abdbb93e1765 100644
--- a/arch/arm/configs/tizen_bcm2711_defconfig
+++ b/arch/arm/configs/tizen_bcm2711_defconfig
@@ -31,6 +31,7 @@ CONFIG_SCHED_AUTOGROUP=y
 CONFIG_BLK_DEV_INITRD=y
 CONFIG_EXPERT=y
 CONFIG_PROFILING=y
+CONFIG_ARM_PMUV3=y
 CONFIG_ARCH_BCM=y
 CONFIG_ARCH_BCM2835=y
 CONFIG_ARM_LPAE=y
```

源码依据（以下路径相对该 worktree；行号在精确基线中核对）：

- `drivers/perf/Kconfig:146`：ARM_PMUV3 依赖 HW_PERF_EVENTS 和 ARM+CPU_V7 或 ARM64，`:149` 为 `default ARM64`，所以 32 位不会默认选中。
- `drivers/perf/Makefile:9`：CONFIG_ARM_PMUV3 控制 arm_pmuv3.o 编入。
- `drivers/perf/arm_pmuv3.c:1383`：匹配 `arm,cortex-a72-pmu`。
- `drivers/perf/arm_v7_pmu.c:1947`–1959：匹配表没有 A72。
- 原运行证据见 [PMU 补测报告](../probe/02_rpi4_pmu_probe.md)。该源码改动针对普通 ARM 内核；本轮没有生成最终 .config 或验证修复后的驱动绑定，不能预先宣布硬件采样已恢复。

## 2. 固定快照构建配置

新文件 `/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/gbs/gbs_rpi4_image.conf` 基于 `config/gbs_llvm.conf`，仅替换两个启用 URL、buildroot 和 tmpdir；profile、仓库顺序及其他字段/注释沿用。原 `config/gbs_llvm.conf`、`config/gbs_gcc.conf` 前后 SHA-256 均一致。

```ini
[general]
# GBS uses its own tmpdir setting; TMPDIR alone does not override /var/tmp.
tmpdir = /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/gbs-tmp-pmuv3
profile = profile.tizen_unified_standard
buildroot = /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-RPI4-PMUV3

[profile.tizen_unified_standard]
repos = repo.base-standard, repo.unified-standard

[repo.base-standard]
url=https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261020.074527/repos/standard/packages/
#url=http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20260722.045200/repos/standard/packages/
#url=http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20260804.124315/repos/standard/packages/

[repo.unified-standard]
url=https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261022.054557/repos/standard/packages/
#url=http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20260725.003315/repos/standard/packages/
#url=https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20260804.223836/repos/standard/packages/
```

Unified 快照的 build.xml 指定 Base 为 `tizen-base-toolchain_20261020.074527`。对应构建日志中 clang/llvm/libllvm 为 **22.1.8-1.6**；此前已核对，见 [12_perf_dependencies.txt](../probe/evidence/12_perf_dependencies.txt)。同日志 `temp/perf_resume/linux-rpi.buildlog.txt:1632` 显示 `export LLVM=1`，`:13919` 在 install 阶段再次设置；基线 spec 的 `packaging/linux-rpi.spec:166`–170 按仓库 `_toolchain` 宏启用 LLVM。没有额外强制修改 CC/CXX/spec。

这固定了源码与仓库输入，尚未证明本地实际解析出的全部构建依赖/宏与服务器完全相同；第二段检查实际日志和产物配置，不能把“准备完毕”等同于完成可重复构建验证。

专用 HOME 文件 `/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/gbs-home/.gbs.conf`（权限 0600）仅为：

```ini
[general]
tmpdir = /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/gbs-tmp-pmuv3
```

配置 SHA-256：

| 文件 | SHA-256 |
|---|---|
| temp/gbs/gbs_rpi4_image.conf | `c4dfc2d24398e7f8afb1d6d10dc9161a2a9e40c88d59a9b21ccda2ad8b05a945` |
| temp/gbs-home/.gbs.conf | `6c48cae118a0de40bb1e3ad55ecdb6654a8129a131ade648e6ae686b3a02cfc6` |

脚本同时校验主配置 SHA-256 和最小 HOME 配置的逐字节内容；缺失或修改就前台停止。`temp/` 不提交，本机文件已备好；若清理了 temp，需重新准备，脚本不会自行恢复或覆盖用户配置。

GBS 2.1.0 源码 `temp/pmuv3-prep/gbs-source/BUILD/gitbuildsys/conf.py:287`–301、`:349`–382 表明 `-c` 不会阻止继续发现项目、HOME、`/etc/gbs.conf`，因此必须使用专用 HOME 并检查系统配置不存在。worktree 自带 `.gbs.conf:1`–4 仅包含 upstream_branch、upstream_tag、squash_patches_until，保持原样作为基线导出设置。脚本也拒绝额外 repo-tool 祖先配置，GBS 子进程设置独立 XDG 配置/缓存目录、GIT_CONFIG_NOSYSTEM=1，并清除可能覆盖隔离路径的 Git 配置环境变量与 VIRTUAL_ENV。结果仓库 commit/push 始终在正常环境执行。

## 3. depanneur 与 sudo 源码核查

`dpkg-query -W` 显示本机 gbs=2.1.0、depanneur=0.16.30。为遵守项目输入边界，没有复制 `/usr/bin` 中的工具源码或读取真实 HOME 配置；从 Tizen 官方工具仓库下载同版本源码到 temp：

| 官方源码 | 本地路径 | SHA-256（与官方 .dsc 一致） |
|---|---|---|
| [depanneur_0.16.30.tar.gz](https://download.tizen.org/tools/latest-release/Ubuntu_24.04/depanneur_0.16.30.tar.gz) | temp/pmuv3-prep/BUILD/ | `4fc2b0536a9aaa4f9dedeb567f9b7c701416da3590eac08805da8f14ce7d9fb3` |
| [gbs_2.1.0.tar.gz](https://download.tizen.org/tools/latest-release/Ubuntu_24.04/gbs_2.1.0.tar.gz) | temp/pmuv3-prep/gbs-source/BUILD/ | `08e1d24df60a3a15910bf645c5d1bc5467c629b9835108df3865986aad813acf` |

官方 Git HTTP 入口认证失败/Gitweb 403，旧 GitHub mirror 不存在，故使用上述官方版本源码归档；没有修改认证、安装软件或 fetch linux-rpi。

源码结论：

| 来源文件:行号 | 行为 |
|---|---|
| `temp/pmuv3-prep/BUILD/depanneur:2048` | 构建命令前缀为 `sudo /usr/bin/build`。 |
| 同文件 `:2158`–2159 | 透传 --define；GBS 侧 `gitbuildsys/cmd_build.py:674`–675 也透传，因此脚本的 _smp_mflags 会到达底层构建命令。 |
| 同文件 `:83`–84、`:3164`–3174 | 启动即触发、每 180 秒执行 `sudo /bin/echo -n`；失败报 sudo: failed to request passwd。注释称 sudo -v，但实际代码调用 echo。 |
| 同文件 `:2202`–2220、`:2247`、`:2258`–2259 | 用 sudo 创建/绑定 scratch、复制构建 conf、查询 chroot 中的 RPM 路径。 |
| 同文件 `:2284`、`:2298` | 用 sudo ln 把构建产物链接到专用 local/repos。 |
| `temp/pmuv3-prep/BUILD/data/gbs:1`–13 | 对对应 mount/umount/mkdir/build/cp/mv/echo/chroot/ln 命令授予 NOPASSWD；`:21` 为 Defaults !use_pty。 |

随包 sudoers `data/gbs` MD5=`7e574df7712f0fbf202fda5957d9b62e`，与 `dpkg-query -s depanneur` 记录的发行版 conffile MD5 相同。**这证明发行版预期策略，不证明受保护的本机文件未修改或不存在其他覆盖规则。** 本机 `/etc/sudoers.d/gbs` 对当前用户不可读；没有提权读取，没有执行 sudo -l/-n/-v 或实际构建来验证授权。

据随包规则，本任务不需要交互密码预热，脚本没有执行 sudo 命令；GBS 内部仍会调用 sudo。为避免策略异常时后台挂住，GBS 在独立 session 中、stdin=/dev/null 启动，不能在原终端请求密码。若被拒绝，以日志和 GBS 非零退出码报 FAILED；不要仅凭发行版策略判成功。脚本预检锁定工具版本，版本变化须重新核查。

## 4. armv7l 的预期产物

基线 `packaging/linux-rpi.spec:6`–12 在非 aarch64 下设置 buildarch=arm、variant=arm-rpi4；`:16`–17 为 Version 6.12.80、Release 0。实际 RPM release/架构/完整列表待构建后确认。

| 预期二进制包名 | spec 声明 / %files 行号 | 用途 |
|---|---|---|
| arm-rpi4-linux-kernel | 48 / 364 | 普通 zImage、DTB/overlay、启动配置及固件 |
| arm-rpi4-linux-kernel-modules | 70 / 341 | 普通内核 modules |
| arm-rpi4-linux-kernel-devel | 91 / 355 | 普通内核配置/映射/构建信息，第二段从中核对配置 |
| arm-rpi4-linux-kernel-btf-devel | 111 / 361 | vmlinux.h |
| arm-rpi4-linux-kernel-headers | 125 / 392 | UAPI headers |
| arm-rpi4-rt-linux-kernel | 58 / 378 | RT zImage_rt 等 |
| arm-rpi4-rt-linux-kernel-modules | 79 / 348 | RT modules |
| arm-rpi4-rt-linux-kernel-devel | 101 / 358 | RT 配置/构建信息 |
| linux-kernel-perf | 136 / 395 | perf 等 |
| linux-kernel-bpftool | 145 / 401 | bpftool |

另可能产生 SRPM 或构建系统自动 debug 子包，以真实产物为准。`Name: rpi4-linux-kernel` 没有对应主包 `%files`，不能凭 Name 行再假设多一个同名二进制包。

`:178` 与 `:252` 都是无条件 `for target in %{variant} %{variant}-rt`；没有只编普通版的宏开关，所以脚本没有虚构 --define 来禁用 RT，也没有改 spec。`:172` 的 dev_wos 只改变安全配置，不是禁用 RT 的开关，未设置它。RT 实际结果现已核对：devel 包 `.config:5996` 为 `# CONFIG_ARM_PMUV3 is not set`，`:505` 为 `CONFIG_HW_PERF_EVENTS=y`。本次 spec `:5` / `:198` 使用独立 tizen_bcm2711_rt_defconfig，成功日志 `:9376` 同样如此，并非本次从已改普通 defconfig 叠加 rt.config。此结论来自实际产物，撤回此前“未直接修改即可推断 RT”及“本次 RT 必定继承”的表述。`:327`–339 的 RT %post/%preun 会切换启动镜像，安装文档明确不安装或自动卸载任何 RT 包。

## 5. 脚本预检、后台状态与限制

[build_pmuv3_kernel.sh](../../scripts/build_pmuv3_kernel.sh) 的前台预检包括：工作树/分支/干净状态/精确 HEAD、原源码树干净、最小 HOME 配置、固定构建配置 SHA-256、`/etc/gbs.conf` 不存在、工具版本与所需命令。磁盘空间和现存 gbs 进程只打印，不设阈值、不终止其他会话。当前准备时磁盘可用约 460G，运行时重新读取。

后台核心命令（N 在运行时计算；实际包外层另有 setsid/env 隔离）：

```sh
HOME=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/gbs-home GIT_CONFIG_NOSYSTEM=1 nice -n 19 ionice -c3 /usr/bin/gbs -c /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/gbs/gbs_rpi4_image.conf build -A armv7l --threads 1 --define '_smp_mflags -jN'
```

- 在固定 worktree 中执行；所有项目输出、日志、专用 HOME、下载/临时目录均指向 WORKDIR/temp。
- `flock` 防止此脚本重复启动覆盖正在运行的日志；只拒绝同一脚本的重复运行，不阻止用户的其他 GBS 会话。拒绝重复启动时保留当前任务的状态，不能为第二个进程改写其 ALL-END。
- 整个收尾 worker 现在由 `setsid --fork /bin/bash ... --worker` 脱离调用会话，继承 fd 9 锁并确认启动；其内部用 `setsid --wait` 等待 GBS。Worker PID 存入 `temp/logs/build_pmuv3.pid`，前台同时打印 `kill -TERM <PID>`。worker 忽略终端关闭的 HUP；TERM/INT 处理及 EXIT trap 会写出 FAILED/真实 wait 退出码，给本任务进程组发送终止请求，不触碰其他构建。权限隔离下的 root 子进程可能无法由普通用户直接终止；中断后如仍有后台进程，应据日志处理，不据 ALL-END 宣称所有特权进程都已消失。
- 状态文件原子替换，含 START/END、HEAD、GBS_EXIT、WRAPPER_EXIT、RPM 列表，最后一行是 `ALL-END <时间> OK|FAILED`。预检失败为 GBS_EXIT NOT_STARTED；信号终止保留中断原因。GBS 正常退出且码为 0、RPM 列表读取成功时才写 OK。
- RPM 列表扫描专用 `BUILDROOT/local/repos`，不把下载依赖缓存作为产物；重复运行时这是专用输出仓库的现有清单，不等于证明每个文件本次重新编译。真实产物归属、配置、build-id 等留待第二段核验。
- trap 覆盖可捕获的终止和普通错误；**SIGKILL、断电、磁盘不可写时无法保证写出 ALL-END**。出现缺标记必须按未完成处理，不能补写 OK。旧脚本已运行且发生缺标记；本次修复仅静态检查，修复未经运行验证，下次构建时验证。

## 6. 第一段检查与交接

已执行 `bash -n scripts/build_pmuv3_kernel.sh`，退出码 0；没有执行脚本，包括前台预检模式。已独立只读核对路径、分支、提交、工具存在、系统 gbs.conf 不存在、磁盘/核数、配置内容/哈希。

- 原源码树开始/结束状态为空；新 worktree 提交后状态为空。
- 基线到分支 diff 仅一个文件一行新增。
- config/ 两份原配置哈希前后相同。
- 临时核查输出保存在 `temp/pmuv3-prep/`，不提交源码树、工具源码归档、临时配置或二进制。
- 本次只提交脚本、本说明、STATUS；结果仓库正常环境 commit/push，内核分支不推送。

下一步由用户运行脚本并通知结果。第二段将读取 status/log，核对实际 RPM 中 CONFIG_ARM_PMUV3=y、CONFIG_HW_PERF_EVENTS=y，与基线比较其他配置，随后才依据 %files/%post 写安装、备份、回退与重启验收步骤。Agent 不安装、不重启、不自行连接开发板。
