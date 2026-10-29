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

4. 以后用户放在 Downloads 的材料一律移动到工作目录，不在 Downloads 保留副本；只处理用户指定的材料，不遍历或触碰其他文件。
5. llvm-profgen 增强设计须经多方评审并冻结后才开工；Agent 的设计与开发在 llvm-profgen 增强完成后才开始。

推送仍失败时：原样记录报错后停下，不索要令牌，不修改任何认证配置。

## 当前授权与执行状态（2026-10-30；v0.2 冻结前补充核实，已完成）

- 本轮完成 RPi4 与主机补证；只改获授权的 IR 匹配原型、报告与状态，不改 LLVM 或设计。v0.2 仍未冻结，待用户评审决定；Agent 开发仍在 llvm-profgen 增强完成后开始。
- Thumb：拉取13库＋5程序并核对SHA；GBS项目armv7l optflags含 `-mthumb`，FFmpeg/GLib/GStreamer/libstdc++已定义动态FUNC均为Thumb；libc/加载器偏ARM，裸clang spike自有C函数为ARM。这与v0.2“默认A32”前提不符。[证据](probe/evidence/06/01_thumb.txt)
- IR：生成/使用均禁用preinline，GBS真实退出0、带时间ALL-END OK，RPi4训练checksum与05相同；加入零权边后PGO/sample边数覆盖44/45与44/46，IR权重覆盖100%与97.16%。仍有switch/br相同键但后继语义不同，不能以100%覆盖宣称质量比较成立；原型保留重复键拒绝及自匹配，并报告形态差异。[证据](probe/evidence/06/02_ir_matching.txt)
- 主机perf：查同源20261022、相近20261027、reference、配套Base均无x86_64 linux-kernel-perf；新镜像20261028仓库404。无主机工具，05同数据跨主机逐行比对仍未完成，不安装或编译替代工具。[证据](probe/evidence/06/03_host_perf.txt)
- LOST已补实测：cycles -c10007 -m1、1080p约20秒媒体，942条LOST/61667丢失样本、8.06%；pswpin/pswpout保持26/613。LOST_SAMPLES未实测。[证据](probe/evidence/06/04_lost_cleanup.txt)
- 板上work为空，仅保留原perf/libLLVM；RPM前后1252；/opt清理后已用73412KiB、可用1232176KiB、6%，专用目录前后35796KiB。分区增加928KiB而专用目录大小不变，不删除其他目录追平占用。
- [06报告](probe/06_rpi4_prefreeze_followup.md)、四份证据、匹配原型和本状态同一commit提交。新证据总量低于150KB，旧证据保持不动；无新增已知边界例外，历史SDB服务内部写入审计限制继续保留。

## 前轮授权与执行状态（2026-10-29；RPi4 PMUv3 新镜像与 v0.2 冻结前核实，历史）

- 用户已授权并完成第 10 节步骤 1 的本轮板上/主机核实及可选 armv7l spike；不修改 LLVM 代码或设计文档，不开始增强实现。设计当前版本仍为 v0.2（未冻结、第二轮评审前），是否进行第二轮评审与冻结由用户决定。
- RPi4 身份断言通过；镜像 Unified 20261028.105834，armv8-pmu 已绑定 A72，cycles type=0/config=0，7,659样本；硬件PMU已在新镜像实测通过，页大小4096。
- dsoff 固定数据6,496条、双进程13,289条 libavcodec 样本公式/PT_LOAD均100%一致。固定period=1000003，频率模式逐样本变化；buildid-mmap与ELF非空ID实测匹配。
- 设计差异/未闭合项：buildid-mmap的buildid-list实际非空；vdso带偏移；Thumb符号区间需清除状态位；IR带权分支匹配15/17与15/23。没有产生LOST、无主机x86_64 perf、RPi5页大小本轮未测，不能宣称整个冻结门槛已闭合。
- armv7l插桩PGO在约7分30秒内闭环：两轮GBS退出0/ALL-END OK，base/instr/pgo校验同为ff818b861cb93a67；不推断性能收益。只在temp测试包中改架构宏与训练profile，原spike和LLVM源码不改。
- 板上work已清空，保留perf/libLLVM；/opt最终已用70628KiB、可用1234960KiB，RPM前后1252，pswpin/pswpout前后26/613。未remount、重启或装卸RPM。
- [05报告](probe/05_rpi4_pmu_image_and_prefreeze.md)、[本轮四份证据](probe/evidence/05/01_environment_hardware.txt)（146,877B）、[IR匹配原型](../tools/match_ir_branches_prototype.py)与本状态文件同一commit提交；旧证据、设计不动。执行偏差与历史SDB边界限制在报告末尾如实保留。

## 前轮授权与完成状态（历史；llvm-profgen 增强设计 v0.2 归档）

- 设计文档当前版本为 [v0.2](profgen/design/02_llvm_profgen_enhance_design_v0.2.md)（第二轮评审前）；v0.1 三方评审已处理完毕，处理表见 v0.2 附录 A。v0.1 文件保留不动。
- 待决事项：是否进行第二轮评审、是否先做第 10 节步骤 1 的冻结前板上核实，均由用户决定。本轮只移动归档和提交，不执行评审、板上核实、构建或代码修改；冻结前不开工，Agent 的设计与开发仍在 llvm-profgen 增强完成后才开始。
- 按用户授权的一次性例外，仅读取并用 `mv` 移入 `/home/linhao/Downloads/02_llvm_profgen_enhance_design_v0.2.md`；移动前 SHA-256 和标题校验通过，移动后哈希不变，已确认 Downloads 原文件不存在，未触碰其他 Downloads 文件。
- 仓库内文档 SHA-256：`b4b03533513b23aa06b26def0faa342445dca128f0602c013cd8545cc26f99cf`；内容未修改，仅与 STATUS.md 同一 commit 提交推送。

## 前轮授权与完成状态（历史；llvm-profgen 增强设计 v0.1 归档）

- [llvm-profgen 增强设计 v0.1](profgen/design/02_llvm_profgen_enhance_design_v0.1.md) 已提交，待多方评审，**冻结前不开工**；Agent 的设计与开发在 llvm-profgen 增强完成后才开始。
- 文档内容未修改。SHA-256=`9a81267b33d1ea59ed84975baabb5802561ca6943219a2070ad2530707231053`；第一行以 `# llvm-profgen 增强设计` 开头；第10行“适用范围”含“不包含任何 Agent 的设计与开发”，三项核验通过。
- 本次从 `/home/linhao/Downloads/02_llvm_profgen_enhance_design_v0.1.md` 移入这一个文件，属于用户授权的例外；核验后已删除该原文件，并确认其不存在，未触碰 Downloads 下其他文件。以后用户放在 Downloads 的材料一律移动到工作目录，不在 Downloads 保留副本。
- 本次只提交设计文档和 STATUS.md，不执行评审、源码修改或构建。

## 前轮授权与完成状态（2026-10-28；llvm-profgen 增强准备，已完成）

- 本轮只读分析 GBS/depanneur/Google AutoFDO/llvm-profgen，完成一次未修改 llvm x86_64 全目标基线构建；不修改 LLVM 跟踪源码/spec，不连接开发板，不推 Gerrit。**停在设计确认阶段，不开始增强实现。**
- src/llvm 开始/结束 status 均为空，HEAD=f999bd406c0a70fe8107aa992164fe6945c5d46a；新分支 afdo/profgen-enhance、worktree=temp/llvm-profgen-enh 跟踪文件无改动，仅保留生成资产/对象/manifest。
- 增量结论：可以增量，但须固定 worktree/root/参数并保留对象、提前准备被跳过的 %prep 资产。当前 spec 不必改；修改源码后的增量耗时尚未实测。GBS 每次仍执行完整 %build/%install/产包。
- 构建 20:33:42–21:33:09+08:00，59分27秒，无重跑；GBS_EXIT=0、ALL-END OK。22 二进制 RPM + 1 SRPM 已记录 SHA-256，新编 llvm-profgen 22.1.8 运行退出0；short-circuit RPM 属开发产物，SRPM 不等同完整导出源码。
- 资源采样最低 available=16663 MiB，未观察到低于2GB；load 1/5/15分钟观测峰值15.11/10.58/9.17。全部临时产物仍在 temp/GBS-ROOT-LLVM-X86、temp/llvm-profgen-enh、temp/profgen-prep。
- 交付 [增量与基线报告](profgen/00_incremental_build.md)、[23项差异表](profgen/01_gap_analysis.md)、三份 profgen 证据与本状态文件，同一 commit 推送。无新增已知边界例外。

## 前轮授权与完成状态（历史；RPi5 AutoFDO / 插桩 PGO spike）

- 本轮允许 GBS 构建测试包、板上仅写 /opt/afdo_agent；不改 LLVM/BOLT/内核源码，不安装板上 RPM、不 remount/重启。Google AutoFDO 仅克隆只读、不构建。所有测试与清理已完成。
- llvm-profgen 22.1.8 对 cycles/cpu-clock 两份无分支栈 IP 输入均真实退出 1（Invalid perf script input!），没有生成 profile、没有 AFDO 重编。Google --use_lbr=false 和 BOLT -ba 是源码支持路径，未动态验证。
- 插桩 PGO 在 RPi5 已闭环：7 函数/31 计数块、profile 匹配写入 IR、pgo 三次 checksum 与 base 一致；base 均值 14.2733s、pgo 14.2567s，约 −0.12%，不认定稳定性能收益。RPi4 插桩仍需 armv7l 验证。
- 固定 Unified 20261027.063617 / Base 20261026.051209；首次因平台 debug 拆分导致未打包文件失败，只修正测试 spec 后重试成功，再 profile 重编成功；三次均取得真实 GBS 退出码与带时间 ALL-END。
- work 已清空，RPM 数前后 1249，保留原 perf/libLLVM；无新增边界例外，历史外部 /tmp/sdb.log 元数据未变。
- 交付 [spike 报告](spike/01_afdo_pgo_feasibility.md)、[源码/spec/profile](../spike/afdo-spike/)、四个 [spike 证据](spike/evidence/01_source_analysis.txt)（共 90,836 B）与本状态文件，同一 commit 推送。未编写 Agent 实现。

## 前轮授权与完成状态（历史；RPi5 环境与采样探测）

- 用户已把同 IP 192.168.108.26 的板换为 RPi5；本轮按 model=Raspberry Pi 5 Model B Rev 1.1、uname -m=aarch64 确认，未依赖 SDB 的旧 rpi4 别名。
- 本轮按挂载参数验收 /opt/afdo_agent/ 后部署 aarch64 perf/libLLVM；板上仅该目录可写，另有一次用户明确授权的 /tmp true 执行负对照（已删除）。不 remount、不重启、不安装/卸载 RPM、不改 /boot；无构建。
- **RPi5 真硬件 cycles 与四项硬件计数支持；分支栈不支持；SPE/ETM 当前镜像没有事件源。** 所有 record 后核对 evlist，成功 cycles 为 type 0/config 0，未回退软件。媒体三种采样全部无丢样，按规则不重跑。
- work 已清空，保留 tools/perf 与 lib/libLLVM.so.22.1；RPM 数开始/结束均 1,249。三个实体库只留本机 temp，现有文件缺完整符号表、代码重定位和调试信息，不具备直接 BOLT/源码行 profile 的前提。
- 交付 [04_rpi5_probe.md](probe/04_rpi5_probe.md)、新增证据 E15–E18 与本状态文件，同一 commit 推送。新增证据 128,645 B，不改任何历史证据；原手工安装内核方案仍取消。

## 前轮授权与完成状态（历史；PMUv3 补丁与 RPi4 软件采样）

- **已决定：PMUv3 通过补丁合入 Gerrit，由用户起 Quickbuild 出新镜像；原板上手工安装方案取消。** scripts/pmuv3_install/ 保留但不再使用；以下历史安装授权不再有效。不向 Gerrit 推送任何内容。
- 用户批准最新 tizen 基线只改普通 defconfig 一行；最新分支已删除独立 RT defconfig，RT 由普通配置叠加 rt.config。已检查全部 RT/LSM 片段无 PMU 依赖冲突，补丁提交与独立 git am 验证完成；本轮没有 make/构建。
- 本轮板上写入仅 /opt/afdo_agent/，另明确授权清理旧 /tmp/afdo_probe 和短暂 /tmp true noexec 负对照。工具/媒体校验、依赖解析、软件采样/硬件负对照已完成，work 清空，保留 tools/perf 与 lib/libLLVM.so.22.1。禁止 remount、重启、RPM 安装/卸载、/boot 改动；本轮均未执行。
- 提交补丁、06 补丁报告、03 软件采样报告、证据与本状态文件至本项目 main；不推内核分支。后续新镜像构建/刷写由用户推进；不自动恢复手工安装。

## 前轮只读诊断（历史，已完成）

- 判定 A：普通 kernel/modules 两包均不在 RPM 数据库，模块目录无 RPM 归属。/boot 未挂载；未获取 zImage 哈希；旧 RPM BUILDTIME=0，无法与运行内核编译日期直接对应。证据见 [05](kernel/05_preflight_diag.md)。

## 前轮安装授权与停止条件（历史；方案已取消，以下不得再执行）

- 用户已审核 02 安装方案，授权 Agent 将主机命令封装为 7 个独立脚本，执行 01–04 到重启前；四个原板上脚本内容必须保持不变。任一步 END FAILED 就立即停止，保留输出，不修复、不重试、不回退。
- **当前已触发停止：02_board_backup.sh 在已安装包预检返回远端 1，报 STOP: unexpected installed package。** 01 成功；02 尚未备份；03、04 未运行。不能通知用户“可以重启”，先等后续指示。
- 不 remount、不 reboot、不加 --nodeps/--force，不安装/卸载 RT。仅允许指定普通 kernel/modules RPM 安装；当前没有执行任何安装。板型确认是 RPi4 Model B Rev 1.5。
- 后续只有安装检查通过且用户通知“已重启并配好网络”后，才运行 05：新内核身份不符停止全任务；身份正确且未绑定 armv8-pmu 只做软件采样；绑定成功做软件+硬件采样。重启和网络配置始终由用户完成，Agent 不 reboot。
- 用户已为后续采样明确授权 /opt/afdo_agent/tools、lib、work，部署 perf/libLLVM 前先查挂载/空间并做执行负对照；遇 ro/noexec 或库未解析停止。按原任务完成媒体计时、软件/硬件采样、符号统计后清空 work，保留 tools/perf 与 lib/libLLVM.so.22.1，记录 RPM 数量前后相等。**当前尚未进入此阶段，不据此提前部署。**
- 本次交付 scripts/pmuv3_install/01–07、更新后的 02 与本 STATUS。执行输出在 temp/pmuv3-install/logs；临时目录保留供后续处置。最后阶段的 04_boot_verify / 03_sampling 报告须在实测后生成，不能预填结果。

## 上轮构建验收（已闭合）

- 缺少 ALL-END 的构建已按用户批准的三组替代证据验收通过：depanneur success/无 fail、HTML 成功行、15 个二进制 RPM + 1 个 SRPM 与日志/时间窗口/哈希逐项一致。真实 GBS 退出码未知，原 status 不改写。
- 构建包装脚本已静态修复 worker 会话/锁与 setsid --wait，未重新运行；根因机制仍属推断。原源码/config/spec 未改。

## 历史授权：PMUv3 内核构建准备（第一段）

- 仅准备源码分支/worktree、构建配置和一键脚本，Agent **不连接开发板，不执行任何构建，不运行构建脚本**；只用 bash -n 做语法检查。
- 不修改 config/ 下两份用户配置，不修改 src/linux-rpi 检出的文件；唯一源码改动放 temp/linux-rpi-pmuv3 的 afdo/pmuv3 分支。开始/结束原工作树状态必须为空。
- 优先使用本地镜像精确基线 21645b17c0d913e2ba7e10fbc9c993d286b3f57d，不 fetch；本地已存在。内核分支只本地提交，不推送。
- 用户自行运行固定快照的 GBS 构建；专用 HOME、buildroot、tmpdir/cache/log 均在 WORKDIR/temp，隔离只施加到 GBS 及子进程。结果仓库 commit/push 用正常环境。
- 第二段等用户通知构建结束后，Agent 再核对产物并写安装/备份/回退说明；安装、重启和板上验收由用户执行，Agent 不操作开发板。
- 只提交 scripts/build_pmuv3_kernel.sh、docs/kernel/01_pmuv3_build.md 与本次 STATUS 更新。temp/、src/ 不提交。

## 历史授权：补充探测（已结束，不能据此继续连接开发板）

用户最新指令覆盖前一版板上安装授权：允许使用镜像配套 Base-Toolchain 仓库（先查 builddata/manifest/build.xml；查不到才用 config/gbs_llvm.conf 的 Base reference 并注明近似），核对 perf 构建依赖与 libLLVM version-release；只在本机 temp/rpms 用 rpm2cpio/cpio 解包，在板上 /tmp/afdo_probe 部署 perf/所需动态库，以 LD_LIBRARY_PATH 指定临时库目录。**不安装 RPM，不推送/安装 perl，不 remount、不重启。** 推送前查 /tmp 空间，推送后必须用 ldd 或 LD_DEBUG 验证；未解析成功则记录并停止。记录每个推送文件、来源包/版本/仓库/SHA-256，结束清理并比较 RPM 数量。仍只授权本机内核配置目标（O=WORKDIR/temp/，不编译内核），禁止安装主机工具；媒体制作/解码/采样沿用原授权。

# 项目状态

更新：2026-10-30（Asia/Shanghai）。阶段：RPi4 PMUv3 新镜像与冻结前补充核实已完成，Thumb默认模式及IR匹配语义差异已补证；llvm-profgen 设计当前版本 v0.2（第二轮评审前），v0.1 三方评审已处理完毕；第二轮评审与冻结待用户决定，冻结前不开工；增强准备和 x86_64 未修改基线已完成；RPi5 AutoFDO/插桩 PGO 工具 spike 已完成；RPi5 环境/软硬件采样完成；RPi4 PMUv3 补丁与软件采样已完成，RPi4 新镜像硬件 PMU 已实测通过。**旧提交 e90492e 的探测结论全部作废；初轮从头重新采集，后续各轮增加独立证据。** RPi5 本轮已完成。每个新会话开场先读本文件，收尾时与报告在同一个 commit 更新。

## 计划

- 当前设计 v0.2（第二轮评审前）；v0.1 三方评审已处理完毕，见附录 A。本轮第 10 节步骤 1 核实已出报告；后续第二轮评审、未闭合证据和冻结由用户决定。冻结前不开工，Agent 的设计与开发在 llvm-profgen 增强完成后才开始。

- v0.2 已确定分批范围：原生 perf.data 解析和 SPE 放第三批；内核模块、Chromium 规模放第二批。保留增量 buildroot/worktree，未经冻结与新授权不开始 LLVM 增强。

- 本轮工具 spike 已完成，不重复采集/构建。建议 RPi5 默认插桩 PGO；RPi4 先验证 ARM runtime/全链路。Google 无 LBR 转换和 BOLT -ba 保留为需后续授权验证的候选。

- RPi5 环境探测完成；硬件 cycles/计数已验证，分支栈失败、无 SPE/ETM。后续 spike 已验证插桩 PGO，普通 IP 的 llvm-profgen 路径不可用；真实包仍须匹配未 strip/debug 二进制。

- 已交付 patches/0001-ARM-configs-tizen_bcm2711-enable-ARM_PMUV3.patch，用户合入 Gerrit 并发起 Quickbuild；Agent 不推 Gerrit。本轮最新补丁未构建/启动，旧镜像基线构建验证仍单独保留。
- 当前镜像的 perf /opt 部署、软件系统/媒体采样、DSO/符号统计及开销实测已完成；cycles 请求发生软件回退，不能当作硬件采样成功。
- RPi4 新镜像 PMU 绑定及真正硬件cycles已验收。原手工安装方案仍取消，不执行 scripts/pmuv3_install/；后续真实包训练与优化另行授权。

以下为前序探测计划与持续纪律：

- 初轮读取 WORKDIR/src、WORKDIR/config 已提供材料；先两层盘点，不写 Agent 实现。本次补充轮的配置生成和板上 RPM 授权范围见上文。
- 按 model 确认 RPi4，检查 root、系统/内核、perf、媒体素材和实体库静态元数据。
- 下载两个配置共四个启用仓库的 primary/filelists，核对三架构工具包及源码构建声明。
- 重新克隆 CodingSystem、固定 commit 核查契约与实现边界。
- 只提交重要小文本，temp/、src/ 不提交；只 git push，不开 PR。署名 Hao Lin <hao.lin@samsung.com>，仅 local 配置。
- 所有耗时命令 nice -n 19 ionice -c3，不并行大任务。

## 进度

### RPi4 PMUv3 新镜像与冻结前核实（当前，已完成）

- A/B/C/D 实测、未匹配IR分支、设计差异、板上清理与原始文件位置详见 [05](probe/05_rpi4_pmu_image_and_prefreeze.md)。只写一次性匹配原型，不修改设计或开始实现。
- 采样与部署证据：[E1](probe/evidence/05/01_environment_hardware.txt)、[E2](probe/evidence/05/02_perf_formats_mapping.txt)；编译器/IR与armv7l闭环：[E3](probe/evidence/05/03_clang_ir.txt)、[E4](probe/evidence/05/04_arm_spike.txt)。

### llvm-profgen 增强准备（历史，已完成）

- GBS/depanneur/build helper 源码核对：bind 源码、跳过 prep、完整执行 build/install 并生成 short-circuit RPM；单包限制和 noinit 条件已记录。[增量源码证据](profgen/evidence/01_incremental_source.txt)
- 未修改基线完成 7633 个 Ninja 步骤，真实 GBS 退出0、ALL-END OK；平台加载器/工具验收新 profgen 成功，23 个产物逐文件 SHA-256 已保存。[构建证据](profgen/evidence/03_baseline_build.txt)
- 差异表覆盖输入/匹配/计数/输出/规模/诊断，并区分 Google 独有、双方已有和未实测能力；建议先做纯 IP、身份/地址正确性与有效样本诊断，模块、raw reader、SPE 分期。[差异源码证据](profgen/evidence/02_gap_source.txt)

### RPi5 AutoFDO / 插桩 PGO spike（历史，已完成）

- 源码固定 LLVM f999bd406c0a70fe8107aa992164fe6945c5d46a、Google AutoFDO f95d1a170dfe24ec5ce4117aa4b0f6d836841703；均保持干净。源码结论详见 [报告 §2](spike/01_afdo_pgo_feasibility.md)。
- 测试包独立本地提交 9925a104708449edabb82afe152d68a0a5b9c908；结果仓库跟踪三个普通文本文件，不跟踪嵌套 Git 元数据。174 行 C、固定 2500000 轮，所有正式运行 checksum=a31c311b953a2ac5。
- GBS 19:15:24–19:19:29 失败退出 1；修正测试 spec 后 19:20:58–19:21:12 成功；profile 重编 19:27:19–19:27:36 成功。整个 worker setsid、GBS setsid --wait，三次 ALL-END 完整；该 spike 临时 wrapper 的验证不等于重新运行了历史内核脚本。[构建证据](spike/evidence/02_build.txt)
- clang/profgen/profdata 22.1.8、readelf 2.43 均来自 GBS root；最终 RPM 三个 ELF 保留 symtab/build-id/debug_line/rela.text。cycles 真硬件 68745 样本，cpu-clock 14268 样本，均无丢样且无 BRANCH_STACK；数据/文本/profile 均核对传输哈希。[运行证据](spike/evidence/03_runtime.txt)
- 两份 llvm-profgen 均退出 1、输出文件不存在；没有 AFDO 优化变体。插桩 merge/show 成功，profile 文本 819 B 入库，spec 内重新 merge 后重编；IR 热点入口/冷热权重匹配。[profile 证据](spike/evidence/04_profiles.txt)
- base real=14.27/14.27/14.28；instr=15.02（+5.23%）；pgo=14.25/14.26/14.26（−0.12%，小差异不认定收益）；所有校验一致。采集器两种 real 均15.20（+6.49%）。
- 板上 work 空、RPM 前后1249，工具/库哈希不变；/tmp/sdb.log 前后495 B、mtime未变。新增四份证据90,836 B，无修改历史证据，无新增已知边界例外。

### RPi5 环境与采样（历史，已完成）

- 板型 RPi5 Model B Rev 1.1、aarch64、uid 0；BUILD_ID=tizen-unified-toolchain_20261027.063617_tizen-headed-aarch64；内核 6.12.80-arm64-rpi4-v8。CPU part 0xd0b，armv8_cortex_a76 事件源，arm-pmu 已绑定 armv8-pmu，日志 7 counters。
- /opt 为 /dev/mmcblk0p3 ext4 rw,relatime，可用 1.3G；true 执行 0。/tmp noexec，true 执行 126；两个拷贝立即删除。/proc/config.gz 不可读，仅核对本地 arm64 defconfig/Kconfig，明确不当作运行配置。
- Unified 同期 build.xml 指向 Base 20261026.051209；perf 6.12.80-0.aarch64、libllvm 22.1.8-1.5.aarch64 的 repodata/RPM 哈希通过，后者与 aarch64 linux-rpi 构建日志一致。两端部署哈希一致，LD_DEBUG/ldd 全部解析；仅解包，不安装。
- 软件系统 11,619 样本；硬件 cycles 系统 12,027 样本，evlist type 0/config 0；四项 stat 都有数值。分支栈 record=255，不支持；无 arm_spe/cs_etm，按条件跳过。BRBE 当前不可用，硬件独立能力未知。
- 720p 基线 real 8.39/8.35/8.52s，均值 8.42s；软件 9.18s、18,940 样本、+9.03%；cycles 9.17s、91,979 样本、+8.91%。1080p 基线 20.09s，软件 21.24s、48,968 样本、+5.72%。所有成功记录 Lost=0，没有触发 -m 1024；全部 EOS/退出 0。
- 三种采样有完整 DSO/符号计数；libgstlibav 有名称样本全部为 PLT。libavcodec/libgstlibav/libgstreamer 的 .comment、build-id、.symtab、.rela.text 和 DWARF 均缺失；ELF DYN/无 TEXTREL 与 PIC 相符，但原始 -fPIC 开关未知。本机 readelf 只读元数据，库只留 temp。
- 清空 work 并验证，保留 perf/libLLVM；RPM 前后 1,249。历史 /tmp/sdb.log 跨轮从 400 B 变为首次 connect 后的 495 B、mtime 17:48:51，收尾未变；未在 connect 前 stat，不推断精确写入归因。用户提供的工作区外附件仅作为任务指令读取。
- 报告与证据：[04](probe/04_rpi5_probe.md)、[E15](probe/evidence/15_rpi5_environment.txt)、[E16](probe/evidence/16_rpi5_perf_deployment.txt)、[E17](probe/evidence/17_rpi5_sampling.txt)、[E18](probe/evidence/18_rpi5_elf_cleanup.txt)。新增证据合计 128,645 B，历史证据未修改。

### PMUv3 补丁与 RPi4 镜像软件采样（历史，已完成）

- fetch origin 后最新 tizen 为 42aeefac58edeb081aff440f0b60be71cbe49755；原 src/linux-rpi 工作树保持干净。相对镜像 21645b17，arch/arm/configs/ 仅删除独立 RT defconfig；普通配置未变。
- 新 worktree 分支 afdo/pmuv3-gerrit 提交 2834afb2f85a6ef0905de18ed5b4a4ef7059635e；一文件一行新增，Kconfig 菜单顺序放在 GENERIC_PHY 与 ANDROID_BINDER_IPC 之间。rt/selinux/nosmack 片段均未覆盖五项 PMU 依赖；普通与 RT 共用并继承。独立干净 worktree git am 退出 0、结果树一致；无 make。详见 [06](kernel/06_pmuv3_patch.md)。
- RPi4 Model B Rev 1.5、uid=0；/opt 实为 /dev/mmcblk0p3 的 rw ext4 独立挂载，可执行；/tmp true 负对照返回 126，已立即删除。旧 /tmp/afdo_probe 清理通过。
- 已校验 perf 6.12.80/libLLVM 22.1.8 两端 SHA-256；LD_DEBUG/ldd 完全解析，perf 实际运行成功。全部数据、registry/cache 位于 work，结束已清空，只保留工具与库。RPM 数前后同为 1,252。
- 软件系统采样 12,012 样本。cycles record 返回 0 但 evlist/report 确认是 type=1 的 cpu-clock 回退；当前镜像硬件 cycles 不支持，不能只看退出码。
- 720p 三次基线 real 均值 12.3133s、差 2.04s；带采样 12.35s，观测开销 +0.30%，26,158 样本、无丢失。1080p 一次基线 23.29s，带采样 24.43s，+4.89%，保存 15,416、丢失 1,034（6.29%）。低次数/冷 registry/丢样限制详见 [03 软件采样](probe/03_rpi4_sampling.md)。
- libavcodec 样本占比 87.4035%/87.7465%；有名称比例仅 0.5467%/0.8575%，且绝大多数为 PLT。libgstlibav 有名称样本全部 PLT，内部函数仍不能解析。[14 原始证据](probe/evidence/14_rpi4_sampling.txt)。
- 全部 evidence/*.txt 合计 149,956 B，满足本轮 150KB；04/05/06/08 历史冗余输出已截断，文件头保留原不可变提交链接及 temp 完整副本路径，历史结论未变。
- 历史 /tmp/sdb.log 本轮末尾仍为 400 B、mtime 2026-10-28 12:01:10.724948977 +0800；没有新增已知未授权边界例外。


### 预检只读诊断（历史；已完成）

- 板型 Raspberry Pi 4 Model B Rev 1.5，id -u=0；本轮未再次切换 root 模式。
- 普通 kernel/modules 两包不带 --qf 和带指定 --qf 各查一次，均明确 is not installed，真实远端退出 1；不是已经发现版本/架构不一致或仅缺其中一个。
- RPM 全集关键词筛选只有 firmware-update-system-ui、firmware-update-system-ui-common、util-linux；rpm 与 grep 各退出 0，没有匹配另名/RT 内核、模块或 U-Boot 包。
- 模块目录与 modules.dep 的 rpm -qf 均为 is not owned by any package、退出 1；ls 可见 6.12.80-arm-rpi4-v7l 目录。
- /boot 的 /proc/mounts 精确匹配为空、awk 退出 0：未挂载。未查 boot 文件、未挂载、未解出旧 zImage，镜像哈希对应未知。
- uname -r=6.12.80-arm-rpi4-v7l；uname -v=#1 SMP Thu Oct 22 06:42:32 UTC 2026；命令行 bootmode=normal partition_ab=a。
- 本机两个旧 RPM 为 6.12.80-0.armv7l、VCS=platform/kernel/linux-rpi#21645b17c0d913e2ba7e10fbc9c993d286b3f57d；BUILDTIME 原始值均为 0，格式化为 1970-01-01 08:00:00 +08:00，不与运行内核的编译时间对应，不能据此验证或否定镜像字节匹配。
- 判定 **A**；原始命令/输出/真实退出码和限制见 [05_preflight_diag.md](kernel/05_preflight_diag.md)，未截断数据保存在 temp/pmuv3-diag/queries.json。
- 没有改脚本、重跑 02、安装/卸载、挂载/remount、重启、备份或采样；没有提出安装方案修改，停止等待指示。


### 安装执行（前轮；02 失败停止）

- 7 个主机脚本自带 set -euo pipefail、绝对路径、EXIT/信号 END 标记、日志；交互终端只需执行 /bin/bash 文件。四个板上脚本和原 helper 与批准文档逐字一致，bash -n / sh -n 全部通过。
- 01：`END 2026-10-28T15:39:52+08:00 OK`，主机退出 0，新旧普通 kernel/modules 四个 RPM SHA-256 全部 OK。
- 02：SDB root 成功、model 确认 RPi4；创建 /tmp/afdo_probe/new、old 并推送四个脚本后，原 prepare 报 `STOP: unexpected installed package`，`__AFDO_RC__1`；`END 2026-10-28T15:40:02+08:00 FAILED 02_board_backup:line=57`，主机退出 1。
- 原预检要求普通 kernel/modules 查询结果均为 6.12.80-0.armv7l；未打印实际包/返回值，具体不匹配尚未知。遵守立即停止规则，没有追加板上查询、修复、重试或回退。
- 未到 mount/备份/RPM 安装；本轮板上备份和主机备份校验都未执行，未创建 BACKUP_VERIFIED。03、04 没有执行，check 没有输出；没有重启或采样。
- 详细证据和边界记录见 [02 安装说明执行记录](kernel/02_pmuv3_install.md)。完整原输出在 temp/pmuv3-install/logs 与 prepare.out，板上四个临时脚本保留，没有安装任何 RPM。
- 既有 /tmp/sdb.log 前后 400 B、mtime 不变；无新增已知工作区外写入。未扩大外部文件扫描或删除遗留日志。


### 构建验收、静态修复与第二段（上轮）

- 构建 2026-10-28 11:56:53+08:00 启动，日志完成于 12:30:30+08:00；无重跑。worker=98602/GBS=98603 已退出，status 留在 BUILDING，真实退出码没有取得。
- 本轮按最新授权验收：success/rpi4-linux-kernel-6.12.80-0/log.txt 存在、fail 空；index.html 为 Succeeded；15 个二进制 RPM + 1 个 SRPM 全部实存、SHA-256 已记录、与 Wrote 行一一匹配，mtime 均在 11:56:53–12:31 内。完整 status、外层末尾 50 行、success 末尾 30 行及所有产物表见 [03](kernel/03_pmuv3_build_result.md)。
- 普通 devel `.config:5957` ARM_PMUV3=y，`:500` HW_PERF_EVENTS=y。从同镜像快照原 devel 提取基线配置，两边 5,649 项只有 ARM_PMUV3 从 n→y；没有其他依赖变化。配置核验不等于运行板上 PMU 已绑定。
- RT devel `.config:5996` ARM_PMUV3 未启用，`:505` HW_PERF_EVENTS=y。spec/实际日志使用独立 tizen_bcm2711_rt_defconfig；01 文档已更正为基于 RPM 的实际结论。
- 日志 LLVM=1、Kbuild `.main.o.cmd` 实际 clang 编译命令、GBS root 平台 readelf 读取 vmlinux .comment（通过 qemu-arm-static，无 sudo）一致确认 clang/LLD 22.1.8。quiet 构建日志没有完整 clang 命令，不能提供其日志行号；替代命令证据及限制已写 03。
- 构建脚本现将整个 worker 脱离调用会话，传递 fd 9 锁，setsid --wait 保留真实退出码；RPM 元数据扫描实读 16 个输出，无权限错误。仅 bash -n，通过；未实际运行修复。具体回收机制仍为推断。
- [02 安装/回退文档](kernel/02_pmuv3_install.md) 只安装普通 kernel+modules，备份整 boot 和模块并拉回主机验哈希；核对普通包无脚本、config.txt 直接覆盖、RT 脚本会切镜像；包含普通启动链哈希检查、在线与 SD 卡离线回退、重启后的身份与 PMU 绑定验收。文档 Shell 片段仅静态检查，不执行。
- 原源码/worktree 干净，未改 config/、固定 GBS 配置/spec，未运行构建、未连接板、未安装包/重启。主机临时 RPM、配置与证据在 temp/pmuv3-verify/；原日志/status 保留。

### 内核构建准备（历史；第一段完成）

- 精确镜像提交 21645b17c0d913e2ba7e10fbc9c993d286b3f57d 在本地存在，未 fetch。原 src/linux-rpi 仍为 42aeefac58edeb081aff440f0b60be71cbe49755，前后 status 为空。
- temp/linux-rpi-pmuv3 / afdo/pmuv3 的内核本地提交：c27f160de761bb55f64672ceac642698a6e93684。仅 ARM 普通 defconfig 增加 CONFIG_ARM_PMUV3=y，一文件一行；已提交且工作树干净。内核提交未推送。
- temp/gbs/gbs_rpi4_image.conf 已固定 Unified 20261022.054557 与 Base 20261020.074527；temp/gbs-home/.gbs.conf 最小配置已准备。config/ 原文件哈希不变。
- spec 无禁用 RT 的宏，脚本构建普通+RT（当前核验普通 PMUv3=y、RT 未启用，见上文）。准备时 nproc=20，运行时计算一半核数，GBS --threads 1。
- 已核查官方同版本 gbs 2.1.0 / depanneur 0.16.30 源码：随包 sudoers 为构建命令授予 NOPASSWD，脚本跳过 sudo -v；受保护的实际策略未读取/提权验证，异常时后台失败退出，不交互等待。
- 第一段当时仅完成 bash -n；后续已实际构建、核验产物并完成第二段文档，见当前进度。
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

- RPi4 新镜像A72 PMU已绑定，cycles没有软件回退；armv7l插桩PGO小程序闭环通过。旧镜像软件回退结论仅适用于历史镜像。[E1](probe/evidence/05/01_environment_hardware.txt)、[E4](probe/evidence/05/04_arm_spike.txt)
- v0.2部分输入预期需评审：模式A buildid-list非空、vdso有偏移；当前IR匹配键只部分覆盖。period/页大小/地址换算/profi事实已取得。[E2](probe/evidence/05/02_perf_formats_mapping.txt)、[E3](probe/evidence/05/03_clang_ir.txt)

- 当前 LLVM spec 有条件支持对象复用；空目录完整基线已成功，差量耗时仍是估算。新 llvm-profgen 可运行，原 src/llvm 保持干净。[00](profgen/00_incremental_build.md)、[E3](profgen/evidence/03_baseline_build.txt)
- Google 的普通 IP、build-id 匹配等可作参考；行/内联计数、discriminator、符号列表和多种输出 LLVM 已有，不能重复列为缺失。[23项差异表](profgen/01_gap_analysis.md)、[E2](profgen/evidence/02_gap_source.txt)

- llvm-profgen 当前纯 IP 输入不可用；Google 无 LBR 和 BOLT -ba 仅源码支持，BOLT 排除 ARM32。[源码证据](spike/evidence/01_source_analysis.txt)、[实测 profile 证据](spike/evidence/04_profiles.txt)。不能据此把所有 AutoFDO 路径判不可用。
- RPi5 插桩 PGO 已实际构建/采集/合并/重编/正确性验证；未证明稳定性能收益。报告与限制：[01_afdo_pgo_feasibility.md](spike/01_afdo_pgo_feasibility.md)。

- RPi5 A76 PMU 已绑定，硬件 cycles 的实际 type/config=0/0，软件/计数支持；分支栈不支持，无 SPE/ETM 事件源；不能由 cycles 推断分支 profile 就绪。[04 报告](probe/04_rpi5_probe.md)、[E15](probe/evidence/15_rpi5_environment.txt)、[E17](probe/evidence/17_rpi5_sampling.txt)。
- RPi5 同期 aarch64 工具/依赖已校验并可执行，媒体全部无丢样；现有 strip 库不能直接提供完整 BOLT/AutoFDO 前提。work 清空，RPM 数不变；保留文件清单与删除命令见 [04](probe/04_rpi5_probe.md)、[E16](probe/evidence/16_rpi5_perf_deployment.txt)、[E18](probe/evidence/18_rpi5_elf_cleanup.txt)。

- **已决定：PMUv3 通过补丁合入 Gerrit、由用户起 Quickbuild 出新镜像；原手工安装方案取消，scripts/pmuv3_install/ 保留、不再使用。** 最新分支普通/RT 共用配置，片段无冲突；补丁与 git am 已验证：[06](kernel/06_pmuv3_patch.md)。
- /opt 部署可执行、所有 NEEDED 已解析；软件采样与 DSO 归属支持，硬件 cycles 请求实际回退，符号解析有限；work 已清空，RPM 数不变：[03 软件采样](probe/03_rpi4_sampling.md)、[14](probe/evidence/14_rpi4_sampling.txt)。

以下历史结论按当时镜像/基线阅读；当前授权和实测以上文为准。


- 预检诊断归类 A：两个普通内核/模块包都不在 RPM 数据库中，模块目录无 RPM 归属；/boot 未挂载。旧 RPM 的 BUILDTIME=0，无法验证 2026 年编译日期。证据：[05_preflight_diag.md](kernel/05_preflight_diag.md)。

- 历史普通版内核构建/完整配置对比已通过替代证据验收（[03](kernel/03_pmuv3_build_result.md)）；该旧产物手工安装方案已取消，后续使用用户 Quickbuild 的新镜像。
- 主机脚本封装完成；01 的 RPM 校验通过，02 在真实远端退出 1 后停止，未安装。证据与原输出路径：[02](kernel/02_pmuv3_install.md)。

- 构建经三组替代证据验收通过；真实 GBS 退出码未知且 ALL-END 缺失，不能补写。普通配置与精确镜像基线仅 ARM_PMUV3 从 n→y；RT 未启用。clang/LLD 22.1.8 已由配置、保存命令与 ELF 核对。证据：[03](kernel/03_pmuv3_build_result.md)。
- 普通 kernel/modules 无自己的 %post/%preun；config.txt 作为 payload 覆盖；RT %post/%preun 会移动 zImage。普通版安装、boot/模块备份、回退与启动检查：[02](kernel/02_pmuv3_install.md)。


- 镜像精确源码基线可用，afdo/pmuv3 只有一行配置新增；原源码和两份用户 GBS 配置未改。基线/提交/diff/核查命令见 [01_pmuv3_build.md](kernel/01_pmuv3_build.md)。
- spec 无只构建普通版宏；预期十个显式二进制包；RT 实际未启用 PMUv3，见 03 的 devel 配置。GBS/depanneur 随包 sudo 调用与 NOPASSWD 策略源码位置同上；实际构建已完成且未见 sudo 限制；当前脚本脱离会话修复仍未运行验证。

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

- [设计 v0.2](profgen/design/02_llvm_profgen_enhance_design_v0.2.md)：本轮冻结前事实已核实并列出设计差异；是否进行第二轮评审、补哪些未闭合证据及是否冻结，由用户决定，不据验证完成自动开工。


- 实际 FFmpeg/GStreamer/Chromium/kernel 包如何接入插桩训练、选择代表性输入及保留匹配二进制；本轮只验证小 C 程序，未实现 Agent。是否授权后续构建/验证 Google 无 LBR 工具、真实包插桩与 RPi5 BOLT -ba；RPi4小程序插桩已由05/06验证。

- 新镜像已由用户交付并通过05的PMUv3验收；Agent不向Gerrit推送，不恢复已取消的手工安装方案。后续镜像交付由用户决定。

- **Agent 的板上部署不能依赖 /tmp（noexec），部署目录由能力探测模块按挂载参数自动选定。** 本轮手工授权 /opt/afdo_agent 已明确，后续按挂载参数验收，不再重复索要目录授权；通用自动选择规则仍待设计裁决。
- 历史直接 make 配置仍受主机 flex/bison 缺失限制；GBS 构建已完成并在构建根解决依赖，没有安装主机工具。
- 新镜像PMU绑定及硬件cycles验收已完成；真实包优化效果与统计质量仍待后续授权评估。
- 是否提供保留 .comment/build-id 的原始构建库及明确 debug 仓库配置。
- SDB 共享 daemon 已打开外部日志，若要求消除该例外，需由用户协调服务启动方式；本轮不重启服务、不删除遗留。

## 挂账

- 冻结前未闭合：06已取得实际LOST语法与计数，LOST_SAMPLES仍未实测；所查仓库无主机x86_64 perf，跨主机文本比对仍跳过；RPi5页大小本轮未核实。IR匹配接受阈值、switch/br及后继语义差异需评审；合成profile与100%键权重覆盖不证明统计质量。Thumb在主要目标库中普遍存在，与v0.2默认A32前提不符。证据见[06](probe/06_rpi4_prefreeze_followup.md)。
- armv7l插桩已通过单程序/单输入闭环；跨训练输入、实际FFmpeg/GStreamer/kernel/Chromium与性能收益仍未验证。Thumb符号区间的状态位处理须保留在核对判据中。

- 本轮未改 LLVM，故单文件增量时间仅估算；Chromium 两工具内存/耗时对比、Google 跨架构/SPE/模块运行仍未验证。当前 short-circuit RPM 非发布包，SRPM 源归档不完整；新 profgen 无 GNU build-id，未改 spec。

- Google create_llvm_prof --use_lbr=false 的端到端运行/行计数质量、ARM/Thumb 正确性和 BOLT -ba 优化仍未实测；RPi4 插桩 PGO 的 armv7l 小程序闭环已于本轮完成。当前 llvm-profgen 的纯 IP 拒绝已闭合，不待重试。
- 本轮性能测量次数少且未随机交错，PGO −0.12% 仅为观测差；真实场景收益、跨输入泛化需独立评估。

- 原 GBS 真实退出码无法追溯；会话/进程组被执行器回收属于推断，没有死亡信号或生命周期审计证据。原 status 永久保留原貌。
- 包装脚本修复未经运行验证，下次构建验证；setsid 不能抵抗 cgroup 清理、SIGKILL、断电、磁盘不可写。
- quiet 原构建日志没有完整 clang 命令行，已用本次 `.cmd` 命令和 ELF 代证；不伪造日志行号。
- 旧手工安装预检失败原因已查清且方案取消；/boot 未挂载时的 zImage 哈希仍未知，BUILDTIME=0 不用于匹配日期。新镜像 PMU 绑定/硬件采样已于05验收；软件采样已闭合。

- 1080p 本次丢样 6.29%，单次开销没有统计稳健性；strip 库内部符号仍缺失。分支栈负对照及 ETM/SPE/BRBE 未在本轮重测，不能由 PMUv3 补丁推断。
- 各包最终 CC/CXX、%{optflags}、外部 LTO/链接器参数与已运行镜像对应关系：无 GBS root/构建日志，不能静态补全。
- RPi5 实机探测已闭合；运行 .config、BRBE 独立硬件能力、原始编译器/链接器和 -fPIC 开关仍未知。没有生成 BOLT/AutoFDO profile 或验证优化收益。
- CodingSystem 业务指南、最终契约与实际实现的后续进展。
- 旧历史写入没有完整 syscall 审计，边界检查无法证明工作区外遗留全集。
