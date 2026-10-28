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

## 当前授权与完成状态（2026-10-28；PMUv3 补丁与软件采样）

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

更新：2026-10-28（Asia/Shanghai）。阶段：最新 tizen PMUv3 补丁完成、当前 RPi4 镜像软件采样完成；硬件 PMU 等用户 Quickbuild 新镜像后验证。**旧提交 e90492e 的探测结论全部作废；初轮从头重新采集，后续各轮增加独立证据。** RPi5 下一轮处理。每个新会话开场先读本文件，收尾时与报告在同一个 commit 更新。

## 计划

- 已交付 patches/0001-ARM-configs-tizen_bcm2711-enable-ARM_PMUV3.patch，用户合入 Gerrit 并发起 Quickbuild；Agent 不推 Gerrit。本轮最新补丁未构建/启动，旧镜像基线构建验证仍单独保留。
- 当前镜像的 perf /opt 部署、软件系统/媒体采样、DSO/符号统计及开销实测已完成；cycles 请求发生软件回退，不能当作硬件采样成功。
- 后续等用户的新镜像与授权，再验收 PMU 绑定及真正硬件事件。原手工安装方案取消，不执行 scripts/pmuv3_install/，不通知用户按旧方案重启。

以下为前序探测计划与持续纪律：

- 初轮读取 WORKDIR/src、WORKDIR/config 已提供材料；先两层盘点，不写 Agent 实现。本次补充轮的配置生成和板上 RPM 授权范围见上文。
- 按 model 确认 RPi4，检查 root、系统/内核、perf、媒体素材和实体库静态元数据。
- 下载两个配置共四个启用仓库的 primary/filelists，核对三架构工具包及源码构建声明。
- 重新克隆 CodingSystem、固定 commit 核查契约与实现边界。
- 只提交重要小文本，temp/、src/ 不提交；只 git push，不开 PR。署名 Hao Lin <hao.lin@samsung.com>，仅 local 配置。
- 所有耗时命令 nice -n 19 ionice -c3，不并行大任务。

## 进度

### PMUv3 补丁与当前镜像软件采样（当前，已完成）

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

- 用户合入 Gerrit 并发起 Quickbuild 的时间与新镜像交付；Agent 不向 Gerrit 推送，最新补丁本轮尚未构建/启动。

- **Agent 的板上部署不能依赖 /tmp（noexec），部署目录由能力探测模块按挂载参数自动选定。** 本轮手工授权 /opt/afdo_agent 已明确，后续按挂载参数验收，不再重复索要目录授权；通用自动选择规则仍待设计裁决。
- 历史直接 make 配置仍受主机 flex/bison 缺失限制；GBS 构建已完成并在构建根解决依赖，没有安装主机工具。
- 新镜像出来后的 PMU 驱动绑定及真实硬件 cycles 采样验收；不能以本轮 perf 软件回退或旧基线构建成功代替。
- 是否提供保留 .comment/build-id 的原始构建库及明确 debug 仓库配置。
- SDB 共享 daemon 已打开外部日志，若要求消除该例外，需由用户协调服务启动方式；本轮不重启服务、不删除遗留。

## 挂账

- 原 GBS 真实退出码无法追溯；会话/进程组被执行器回收属于推断，没有死亡信号或生命周期审计证据。原 status 永久保留原貌。
- 包装脚本修复未经运行验证，下次构建验证；setsid 不能抵抗 cgroup 清理、SIGKILL、断电、磁盘不可写。
- quiet 原构建日志没有完整 clang 命令行，已用本次 `.cmd` 命令和 ELF 代证；不伪造日志行号。
- 旧手工安装预检失败原因已查清且方案取消；/boot 未挂载时的 zImage 哈希仍未知，BUILDTIME=0 不用于匹配日期。新镜像 PMU 绑定/硬件采样仍待验收；软件采样已闭合。

- 1080p 本次丢样 6.29%，单次开销没有统计稳健性；strip 库内部符号仍缺失。分支栈负对照及 ETM/SPE/BRBE 未在本轮重测，不能由 PMUv3 补丁推断。
- 各包最终 CC/CXX、%{optflags}、外部 LTO/链接器参数与已运行镜像对应关系：无 GBS root/构建日志，不能静态补全。
- RPi5 实机：明确下一轮；本轮没有连接或探测。
- CodingSystem 业务指南、最终契约与实际实现的后续进展。
- 旧历史写入没有完整 syscall 审计，边界检查无法证明工作区外遗留全集。
