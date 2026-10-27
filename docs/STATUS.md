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

# 项目状态

更新：2026-10-27（Asia/Shanghai）。阶段：设计前环境探测。**旧提交 e90492e 的探测结论全部作废；本轮从头重新采集。** 本轮只探测 RPi4，RPi5 下一轮处理。每个新会话开场先读本文件，收尾时与报告在同一个 commit 更新。

## 计划

- 读取 WORKDIR/src、WORKDIR/config 已提供材料；先两层盘点，不编译、不安装、不写 Agent 实现。
- 按 model 确认 RPi4，检查 root、系统/内核、perf、媒体素材和实体库静态元数据。
- 下载两个配置共四个启用仓库的 primary/filelists，核对三架构工具包及源码构建声明。
- 重新克隆 CodingSystem、固定 commit 核查契约与实现边界。
- 只提交重要小文本，temp/、src/ 不提交；只 git push，不开 PR。署名 Hao Lin <hao.lin@samsung.com>，仅 local 配置。
- 所有耗时命令 nice -n 19 ionice -c3，不并行大任务。

## 进度

- 已重新盘点，四个源码树和两份 config 文件就绪；配置指向的工作区内 GBS root 不存在。
- 已连接 192.168.108.26:26101，model=Raspberry Pi 4 Model B Rev 1.5，armv7l，root 成功。
- perf 缺失；批次中的 record/report/script/list 调用均 exec 失败，无采样数据生成。缺工具后未安装替代物，未把失败认作硬件不支持。
- 已检查插件、素材、拉取两份实体库；/tmp/afdo_probe 已删除并验证。
- 四个仓库元数据重新下载、压缩/解压 SHA-256 校验、全量文件提供关系查询完成。
- 内核/LLVM/FFmpeg/GStreamer spec 和相关源码检查完成；实际构建环境的宏展开保持未知。
- CodingSystem 重新克隆，当前 HEAD=287d51c674e2b7d38605098338ff94fc8bb4e4fa；只读，无修改/推送。
- 新报告与证据已重写；原始证据合计限于 300KB 内。报告：[probe/01_env_probe_report.md](probe/01_env_probe_report.md)。
- 推送认证待解决：隔离全局配置并禁用外部 credential helper 后，git push --dry-run 和实际 git push origin main 均返回 exit 128（无法读取 GitHub 用户名）。本轮报告已在本地提交，尚未发布；远端 main 仍是作废的旧报告。已向用户请求仓库内认证，未读取工作区外凭据。

## 已闭合结论（附证据路径）

- 输入材料及配置已就绪，无 GBS root。[01_workspace.txt](probe/evidence/01_workspace.txt)
- RPi4：Tizen 11.0.0，内核 6.12.80-arm-rpi4-v7l；uid=0；perf 不在 PATH；无硬件 PMU/cs_etm/arm_spe 事件源，运行内核配置不可取得。[02_rpi4.txt](probe/evidence/02_rpi4.txt)
- avdec_h264 可发现；ffmpeg/ffprobe 命令及 /root 常见后缀视频未发现。只验证插件存在，没有执行解码 benchmark。[02_rpi4.txt](probe/evidence/02_rpi4.txt)
- 两份实体库已 strip、没有 .comment 和 build-id；链接器未知。本机工具只读静态 ELF 元数据。[03_libraries.txt](probe/evidence/03_libraries.txt)
- L 配置仓库提供 LLVM/compiler-rt 22.1.8-3.1，G 配置提供 22.1.8-6.5；三架构都有 profgen/profdata/profile runtime；armv7l/aarch64 有 linux-kernel-perf 6.12.80-0。四库均未找到 BOLT 工具/runtime、create_llvm_prof 或目标 debuginfo，结论不覆盖独立 debug 仓库。[04_repodata.txt](probe/evidence/04_repodata.txt)
- 内核源码 6.12.80 无 AUTOFDO_CLANG/PROPELLER_CLANG 配置和架构 select；同一源包包含 arm/arm64 的 tizen_bcm2711_defconfig 路径，arm64 配置及启动文件覆盖 pi5，但 RPi5 实机未验证。[05_sources.txt](probe/evidence/05_sources.txt)
- LLVM spec 未启用 bolt，lld 在 llvm 主包，profgen/profile runtime 有构建和打包声明；FFmpeg 正常非 ASan 路径保留 ARM 汇编/NEON；GStreamer 的 gst-libav 源码与包声明已提供。[05_sources.txt](probe/evidence/05_sources.txt)
- 框架 HLD draft frozen，契约 v0.11 复审中，业务指南缺失，代码目录只有占位；不能称框架已实现。[06_codingsystem.txt](probe/evidence/06_codingsystem.txt)
- 已确认外部遗留 /tmp/sdb.log，由现存 SDB 服务持有，当前 0 B、前后时间未变；没有删除。首次 shell/Git 隐式初始化读取未追踪，不能证明无外部配置读取；后续已隔离。[07_boundary.txt](probe/evidence/07_boundary.txt)

## 待人工裁决

- 在不读取 WORKDIR 外认证配置/数据的前提下，提供可用的仓库本地 GitHub 推送认证；不要在聊天中发送令牌。当前推送受认证阻塞。
- 后续是否提供已带 perf、可读内核配置和硬件 PMU 事件的镜像；本轮不安装、不重启、不变更内核。
- 提供 ffprobe/视频素材或其他可用媒体场景；当前不具备视频元信息检查条件。
- 是否提供保留 .comment/build-id 的原始构建库及明确 debug 仓库配置。
- SDB 共享 daemon 已打开外部日志，若要求消除该例外，需由用户协调服务启动方式；本轮不重启服务、不删除遗留。

## 挂账

- RPi4 cycles 实际样本、分支负对照、ETM/SPE trace 内容、BRBE 能力：当前工具/事件/配置不足。
- 各包最终 CC/CXX、%{optflags}、外部 LTO/链接器参数与已运行镜像对应关系：无 GBS root/构建日志，不能静态补全。
- RPi5 实机：明确下一轮；本轮没有连接或探测。
- CodingSystem 业务指南、最终契约与实际实现的后续进展。
- 旧历史写入没有完整 syscall 审计，边界检查无法证明工作区外遗留全集。
