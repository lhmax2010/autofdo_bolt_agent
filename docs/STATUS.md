【最高原则（必须遵守，违反即视为任务失败）】
工作目录：/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/（下文称 WORKDIR）
1. 开发测试过程中产生的所有文件只能创建在 WORKDIR 内，不得在其他任何地方生成文件。
   - 包括临时文件、缓存、下载内容、克隆的仓库、日志。
   - 临时文件和数据一律放 WORKDIR/temp/。
2. 不得使用 WORKDIR 以外的任何文件。
   - 不读取、不引用、不复制其他目录下的源码、配置、脚本或数据。
   - 系统自带的命令行工具（git、sdb、readelf、curl 等）本身可以执行。
   - 需要的源码与配置只从 WORKDIR/src、WORKDIR/config 取；网络上的公开仓库只能克隆到 WORKDIR/temp/ 内。
3. 落实方式：
   - 所有命令执行前 export TMPDIR=WORKDIR/temp/tmp（先创建该目录）。
   - git 只用仓库内配置（git config --local），不修改全局 git 配置。
   - 不做 pip / npm / apt 等任何安装；缺工具就停下，在报告里说明。
   - 任何工具若自行在 WORKDIR 外写了东西（例如 sdb 服务自身的状态文件），不要隐瞒，在报告的"边界例外"一节如实列出：路径、哪个工具写的、能否避免。
   - 检查上一次中断的执行有没有在 WORKDIR 外留下文件；有就列进"边界例外"，不要自行删除。
4. 开发板上无法写入 WORKDIR，所以板上只允许写 /tmp/afdo_probe/，结束时删除。

## 长期规则澄清（用户后续指令；优先于上述文字的歧义解释）

1. "不得使用 WORKDIR 以外的任何文件"约束的是项目的输入与产出：源码、配置、数据、脚本只能取自 WORKDIR，生成的文件只能落在 WORKDIR。它不禁止使用本机已有的 GitHub 推送认证。
2. 环境隔离（例如改 HOME、GIT_CONFIG_NOSYSTEM 等）只用于 gbs 相关命令（export、build 及其派生进程），本轮没有 gbs 命令，因此本轮不需要任何隔离。
3. 本项目结果仓库（autofdo_bolt_agent）的 git commit 与 git push 一律在正常环境下执行，使用本机已有的 GitHub 认证。提交署名仍用 git config --local 设置的 Hao Lin <hao.lin@samsung.com>，不修改全局 git 配置。

推送仍失败时：原样记录报错后停下，不索要令牌，不修改任何认证配置。

## 当前任务授权：PMUv3 内核构建准备（第一段）

- 仅准备源码分支/worktree、构建配置和一键脚本，Agent **不连接开发板，不执行任何构建，不运行构建脚本**；只用 bash -n 做语法检查。
- 不修改 config/ 下两份用户配置，不修改 src/linux-rpi 检出的文件；唯一源码改动放 temp/linux-rpi-pmuv3 的 afdo/pmuv3 分支。开始/结束原工作树状态必须为空。
- 优先使用本地镜像精确基线 21645b17c0d913e2ba7e10fbc9c993d286b3f57d，不 fetch；本地已存在。内核分支只本地提交，不推送。
- 用户自行运行固定快照的 GBS 构建；专用 HOME、buildroot、tmpdir/cache/log 均在 WORKDIR/temp，隔离只施加到 GBS 及子进程。结果仓库 commit/push 用正常环境。
- 第二段等用户通知构建结束后，Agent 再核对产物并写安装/备份/回退说明；安装、重启和板上验收由用户执行，Agent 不操作开发板。
- 只提交 scripts/build_pmuv3_kernel.sh、docs/kernel/01_pmuv3_build.md 与本次 STATUS 更新。temp/、src/ 不提交。

## 历史授权：补充探测（已结束，不能据此继续连接开发板）

用户最新指令覆盖前一版板上安装授权：允许使用镜像配套 Base-Toolchain 仓库（先查 builddata/manifest/build.xml；查不到才用 config/gbs_llvm.conf 的 Base reference 并注明近似），核对 perf 构建依赖与 libLLVM version-release；只在本机 temp/rpms 用 rpm2cpio/cpio 解包，在板上 /tmp/afdo_probe 部署 perf/所需动态库，以 LD_LIBRARY_PATH 指定临时库目录。**不安装 RPM，不推送/安装 perl，不 remount、不重启。** 推送前查 /tmp 空间，推送后必须用 ldd 或 LD_DEBUG 验证；未解析成功则记录并停止。记录每个推送文件、来源包/版本/仓库/SHA-256，结束清理并比较 RPM 数量。仍只授权本机内核配置目标（O=WORKDIR/temp/，不编译内核），禁止安装主机工具；媒体制作/解码/采样沿用原授权。

# 项目状态

更新：2026-10-27（Asia/Shanghai）。阶段：PMUv3 内核构建准备完成，等待用户执行脚本。**旧提交 e90492e 的探测结论全部作废；初轮从头重新采集，补充轮在其上增加独立证据。** 本轮只探测 RPi4，RPi5 下一轮处理。每个新会话开场先读本文件，收尾时与报告在同一个 commit 更新。

## 计划

- 当前第一段：已完成精确基线 worktree、单行 PMUv3 配置提交、固定工具链快照/专用 HOME、前台预检及后台结束标记脚本；不启动构建。
- 用户运行 `/bin/bash /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/scripts/build_pmuv3_kernel.sh` 后通知结果。
- 第二段：先确认 ALL-END OK，再核对 RPM 中配置和基线差异，编写 docs/kernel/02_pmuv3_install.md；此文件尚未生成。

以下为前序探测计划与持续纪律：

- 初轮读取 WORKDIR/src、WORKDIR/config 已提供材料；先两层盘点，不写 Agent 实现。本次补充轮的配置生成和板上 RPM 授权范围见上文。
- 按 model 确认 RPi4，检查 root、系统/内核、perf、媒体素材和实体库静态元数据。
- 下载两个配置共四个启用仓库的 primary/filelists，核对三架构工具包及源码构建声明。
- 重新克隆 CodingSystem、固定 commit 核查契约与实现边界。
- 只提交重要小文本，temp/、src/ 不提交；只 git push，不开 PR。署名 Hao Lin <hao.lin@samsung.com>，仅 local 配置。
- 所有耗时命令 nice -n 19 ionice -c3，不并行大任务。

## 进度

### 内核构建准备（当前；第一段完成）

- 精确镜像提交 21645b17c0d913e2ba7e10fbc9c993d286b3f57d 在本地存在，未 fetch。原 src/linux-rpi 仍为 42aeefac58edeb081aff440f0b60be71cbe49755，前后 status 为空。
- temp/linux-rpi-pmuv3 / afdo/pmuv3 的内核本地提交：c27f160de761bb55f64672ceac642698a6e93684。仅 ARM 普通 defconfig 增加 CONFIG_ARM_PMUV3=y，一文件一行；已提交且工作树干净。内核提交未推送。
- temp/gbs/gbs_rpi4_image.conf 已固定 Unified 20261022.054557 与 Base 20261020.074527；temp/gbs-home/.gbs.conf 最小配置已准备。config/ 原文件哈希不变。
- spec 无禁用 RT 的宏，脚本将构建普通+RT（只有普通配置加 PMUv3）。当前 nproc=20，运行时计算一半核数，GBS --threads 1。
- 已核查官方同版本 gbs 2.1.0 / depanneur 0.16.30 源码：随包 sudoers 为构建命令授予 NOPASSWD，脚本跳过 sudo -v；受保护的实际策略未读取/提权验证，异常时后台失败退出，不交互等待。
- 脚本只有 bash -n 静态语法检查（通过），没有执行。尚无本次构建日志、结束状态或 RPM。第二段未开始。
- 说明与完整内核 diff：[01_pmuv3_build.md](kernel/01_pmuv3_build.md)；脚本：[build_pmuv3_kernel.sh](../scripts/build_pmuv3_kernel.sh)。

### 补充轮（历史）

- [02_rpi4_pmu_probe.md](probe/02_rpi4_pmu_probe.md) 与证据 08–13 已整理；本轮部分完成，主机 flex 缺失和板上 /tmp noexec 两个阻塞保持开放。
- 官方 BBB 片源、60 秒 720p/1080p H.264 视频、SHA-256/ffprobe/来源授权记录完成；[media/README.md](../media/README.md)。MP4 本地保留但忽略，不提交。
- 两份 defconfig 配置生成均因主机缺 flex exit=2，未生成 .config；仅 temp/ 下产生配置辅助对象，内核源码开始/结束均干净。
- RPi4 运行 DT 的 A72 PMU 节点及 platform 设备存在，未绑定驱动；只有 armv7-pmu，没有 armv8-pmu 注册。ARM_PMUV3 缺失是高可信候选原因，实际运行配置尚未闭合。
- 前一批同镜像 perf RPM 的 --test 缺 perl/LLVM；用户已批准配套 Base，并改为仅解包部署。
- Unified build.xml 指向 Base `tizen-base-toolchain_20261020.074527`。配套 `libllvm-22.1.8-1.6` 与 perf 构建日志完全一致，repodata/RPM SHA-256 验证通过；没有使用 reference。
- readelf 确认 libLLVM 是 perf 主程序的直接 NEEDED；perl 来自四个随包测试辅助脚本。只推送 perf 与 libLLVM 两个文件，板上 SHA-256 与本机一致。
- `/tmp` 实际挂载 rw,nosuid,nodev,noexec；ldd exit=1，直接 perf --version exit=126，动态加载器 --list exit=127（failed to map segment）。未完成库解析验收，按指令停止；未安装任何 RPM、未改挂载/标签/策略。
- 720p 和 1080p avdec_h264 管线均到 EOS，real=14.323s / 27.359s；perf 不可用，所有采样/报告/分支栈测试未执行。
- 最新临时部署已清理并验证 /tmp/afdo_probe 不存在；rpm -qa | wc -l 前后均 1252，完整集合新增/删除均为空。没有 perf.data 生成或拉回。
- 本次证据 12–13 为 14,646 字节，补充轮 08–13 合计 48,853 字节，所有 evidence 合计 185,033 字节，低于 200KB；只提交报告/证据/README/.gitignore/本状态文件。推送使用正常既有认证，不开 PR。

### 初轮（历史，补充轮结论优先）

- 已重新盘点，四个源码树和两份 config 文件就绪；配置指向的工作区内 GBS root 不存在。
- 已连接 192.168.108.26:26101，model=Raspberry Pi 4 Model B Rev 1.5，armv7l，root 成功。
- perf 缺失；批次中的 record/report/script/list 调用均 exec 失败，无采样数据生成。缺工具后未安装替代物，未把失败认作硬件不支持。
- 已检查插件、素材、拉取两份实体库；/tmp/afdo_probe 已删除并验证。
- 四个仓库元数据重新下载、压缩/解压 SHA-256 校验、全量文件提供关系查询完成。
- 内核/LLVM/FFmpeg/GStreamer spec 和相关源码检查完成；实际构建环境的宏展开保持未知。
- CodingSystem 重新克隆，当前 HEAD=287d51c674e2b7d38605098338ff94fc8bb4e4fa；只读，无修改/推送。
- 新报告与证据已重写；原始证据合计限于 300KB 内。报告：[probe/01_env_probe_report.md](probe/01_env_probe_report.md)。
- 推送规则已澄清：先前 exit 128 发生在主动禁用全局配置与 credential helper 的环境，不能据此判定本机认证失效。本次在正常环境提交长期规则与状态更新，并用原有 GitHub 认证推送全部未推送提交；不修改认证配置、不再请求仓库内凭据。推送结果以执行日志及远端 HEAD 校验为准。

## 已闭合结论（附证据路径）

- 镜像精确源码基线可用，afdo/pmuv3 只有一行配置新增；原源码和两份用户 GBS 配置未改。基线/提交/diff/核查命令见 [01_pmuv3_build.md](kernel/01_pmuv3_build.md)。
- spec 无只构建普通版宏；预期十个显式二进制包，RT 配置不变。GBS/depanneur 随包 sudo 调用与 NOPASSWD 策略源码位置同上；实际构建与实际 sudo 授权尚未运行验证。

- 配套 Base 快照已明确；libllvm 22.1.8-1.6 与 perf 实际构建日志一致，ABI/包校验通过；perl 为附带测试脚本解释器依赖。[12_perf_dependencies.txt](probe/evidence/12_perf_dependencies.txt)
- 临时路径 /tmp 的 noexec 阻止 perf 执行和加载器映射；ldd 无法完成全部 NEEDED 验证。推送文件已删除，RPM 前后同为 1252 且包集不变。[13_perf_deployment.txt](probe/evidence/13_perf_deployment.txt)

- 补充轮配置生成失败且源码未改；最终配置未知，不以默认值替代。[08_pmu_config.txt](probe/evidence/08_pmu_config.txt)
- 运行 DT 包含有效 A72 PMU 节点、平台设备未绑定，仅 armv7-pmu 注册；排除了“无节点/节点 disabled”，但未证明中断/固件无其他问题。[09_pmu_runtime.txt](probe/evidence/09_pmu_runtime.txt)
- 镜像同期 perf RPM SHA-256 校验通过，依赖测试失败，同库没有缺失依赖提供者；实际安装 0 包。[10_perf_package.txt](probe/evidence/10_perf_package.txt)
- 已建立 60 秒两档 BBB H.264 素材并完成 avdec_h264 解码基线；首轮“没有执行解码”的结论由本轮结果补齐。[11_media_smoke.txt](probe/evidence/11_media_smoke.txt)

- 输入材料及配置已就绪，无 GBS root。[01_workspace.txt](probe/evidence/01_workspace.txt)
- RPi4：Tizen 11.0.0，内核 6.12.80-arm-rpi4-v7l；uid=0；perf 不在 PATH；无硬件 PMU/cs_etm/arm_spe 事件源，运行内核配置不可取得。[02_rpi4.txt](probe/evidence/02_rpi4.txt)
- avdec_h264 可发现；ffmpeg/ffprobe 命令及 /root 常见后缀视频未发现。只验证插件存在，没有执行解码 benchmark。[02_rpi4.txt](probe/evidence/02_rpi4.txt)
- 两份实体库已 strip、没有 .comment 和 build-id；链接器未知。本机工具只读静态 ELF 元数据。[03_libraries.txt](probe/evidence/03_libraries.txt)
- L 配置仓库提供 LLVM/compiler-rt 22.1.8-3.1，G 配置提供 22.1.8-6.5；三架构都有 profgen/profdata/profile runtime；armv7l/aarch64 有 linux-kernel-perf 6.12.80-0。四库均未找到 BOLT 工具/runtime、create_llvm_prof 或目标 debuginfo，结论不覆盖独立 debug 仓库。[04_repodata.txt](probe/evidence/04_repodata.txt)
- 内核源码 6.12.80 无 AUTOFDO_CLANG/PROPELLER_CLANG 配置和架构 select；同一源包包含 arm/arm64 的 tizen_bcm2711_defconfig 路径，arm64 配置及启动文件覆盖 pi5，但 RPi5 实机未验证。[05_sources.txt](probe/evidence/05_sources.txt)
- LLVM spec 未启用 bolt，lld 在 llvm 主包，profgen/profile runtime 有构建和打包声明；FFmpeg 正常非 ASan 路径保留 ARM 汇编/NEON；GStreamer 的 gst-libav 源码与包声明已提供。[05_sources.txt](probe/evidence/05_sources.txt)
- 框架 HLD draft frozen，契约 v0.11 复审中，业务指南缺失，代码目录只有占位；不能称框架已实现。[06_codingsystem.txt](probe/evidence/06_codingsystem.txt)
- 已确认外部遗留 /tmp/sdb.log，由现存 SDB 服务持有，当前 0 B、前后时间未变；没有删除。首次 shell/Git 隐式初始化读取未追踪，作为历史审计限制保留；用户已澄清正常系统工具初始化及已有 GitHub 认证不属于项目输入边界限制，后续结果仓库 commit/push 不隔离。[07_boundary.txt](probe/evidence/07_boundary.txt)

## 待人工裁决

- 当前等待用户在终端运行第一段脚本并通知 status/log。Agent 不自行启动构建；构建成功也不自动安装或连接板。

- 用户需要提供符合写入边界且允许执行/映射的测试路径或预置 perf 的镜像。当前 /tmp 为 noexec；不能在“不 remount、不安装、不写其他路径”的范围内继续采样。Base 仓库授权已解决，无需再次确认。
- 历史直接 make 配置仍受主机 flex/bison 缺失限制；新 GBS 方案由 spec 的 BuildRequires 在隔离构建根解决依赖，尚未启动，未安装主机工具。
- 原运行镜像完整配置仍待核验；第一段已在独立 worktree 准备 ARM_PMUV3=y 改动，但没有构建、部署或重启。
- 是否提供保留 .comment/build-id 的原始构建库及明确 debug 仓库配置。
- SDB 共享 daemon 已打开外部日志，若要求消除该例外，需由用户协调服务启动方式；本轮不重启服务、不删除遗留。

## 挂账

- 用户执行构建、实际工具链/依赖解析与产物清单、普通版配置差异验证、安装/备份/回退说明；第二段等待用户通知。
- 脚本中断/退出处理目前只静态审查，未运行验证。SIGKILL/断电/不可写磁盘无法保证 ALL-END；缺标记按未完成处理。

- RPi4 perf 临时运行及完整动态库解析、cpu-clock/cycles 样本、分支负对照、媒体 perf 报告/计时、ETM/SPE trace 内容、BRBE 能力：/tmp noexec 阻塞，采样未执行；不再计划 RPM 安装。
- 各包最终 CC/CXX、%{optflags}、外部 LTO/链接器参数与已运行镜像对应关系：无 GBS root/构建日志，不能静态补全。
- RPi5 实机：明确下一轮；本轮没有连接或探测。
- CodingSystem 业务指南、最终契约与实际实现的后续进展。
- 旧历史写入没有完整 syscall 审计，边界检查无法证明工作区外遗留全集。
