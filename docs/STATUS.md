# 项目状态

更新日期：2026-10-27（Asia/Shanghai）。阶段：设计前环境探测。**环境探测未全部完成；仓库元数据与框架检查完成，板卡缺失，源码未就绪。**

以后每个新会话开场先读本文件，并复核工作目录与设备现状。每个任务收尾须在同一 commit 更新本文件及相应产出。

## 计划

1. 只读探测 RPi4/armv7l 与 RPi5/aarch64；先按 model 确认身份，再做 perf、素材与库检查。
2. 读取已提供内核和业务源码、LLVM spec/CMake，以及 GBS 仓库元数据。
3. 固定 CodingSystem 契约版本并区分设计与实现。
4. 维护 [探测报告](probe/01_env_probe_report.md) 和 `probe/evidence/*.txt`；只提交小文本，使用 git push，不开 PR。

约束：所有产出留在当前工作目录，临时数据只放 `temp/`；板上只允许 `/tmp/afdo_probe/` 写入并在结束时清理；不 remount、不安装、不重启、不编译；耗时命令 `nice -n 19 ionice -c3`，不并行大任务；署名 Hao Lin <hao.lin@samsung.com>。

## 进度

- 已完成初始两层目录盘点：空目录；无历史状态可读。
- 已初始化 main 与用户指定 remote；初始远端无 refs，已忽略 temp/。
- 已执行 `sdb devices`，未发现任何设备；按要求暂停第 1 部分，已请求两块板 IP。
- 初始目录为空；任务期间补入根目录 gbs_llvm.conf、gbs_gcc.conf 和正在克隆的 src/llvm。config/gbs_llvm.conf 仍不存在，未移动或修改用户文件。
- 已读取实际根目录配置，下载两个启用仓库的 primary/filelists，校验压缩与解压 SHA-256 并全量关联查询；其他包源码未提供，LLVM 尚无有效 HEAD。
- 已克隆并只读检查 CodingSystem main，固定 commit `287d51c674e2b7d38605098338ff94fc8bb4e4fa`。
- 已产出部分探测报告及精简证据；本次提交同时保存本状态。推送结果由执行日志和最终回复确认。

## 已闭合结论（附证据路径）

- 初始工作目录没有用户预置材料；源码与配置缺失不是路径猜测。[probe/evidence/01_workspace.txt](probe/evidence/01_workspace.txt)
- 后补配置的两个仓库均可读取；三架构 llvm 22.1.8-3.1 提供 llvm-profgen/llvm-profdata，compiler-rt 22.1.8-3.1 提供 profile runtime，armv7l/aarch64 的 linux-kernel-perf 6.12.80-0 提供 /usr/bin/perf。两个仓库未找到 BOLT 工具/runtime、create_llvm_prof、FFmpeg/GStreamer debuginfo；仅限本次元数据快照，不代表功能不支持。[probe/evidence/04_repodata.txt](probe/evidence/04_repodata.txt)
- SDB 可执行但设备列表为空；两板身份、root、全部采样能力未知，未执行板上写入，无临时目录需要清理。[probe/evidence/02_sdb_devices.txt](probe/evidence/02_sdb_devices.txt)
- CodingSystem HLD 为 v1.0-draft-frozen，最新契约 v0.11 Draft 仍在复审，设计包版本为 1.0.0.dev1；不能称作正式 contract v1.0。[probe/evidence/03_codingsystem.txt](probe/evidence/03_codingsystem.txt)
- 该框架提交中业务指南 02–06、开发指南 08、计划 09 未入库，框架/业务代码目录仅 .gitkeep；P0 完成及 P1+ 实现均无依据。[probe/evidence/03_codingsystem.txt](probe/evidence/03_codingsystem.txt)
- 注册、TaskInput/HandoffResult、BuildReport/BenchReport 已有文档定义，详见 [报告 §7](probe/01_env_probe_report.md#7-multi-agent-框架契约)，尚无可运行实现证据。

## 待人工裁决

- 请提供 RPi4 和 RPi5 的 IP（及非默认 SDB 端口）；连接后仍须按 model 核验，不能按 IP 命名认板。
- 请提供内核、FFmpeg、GStreamer、Chromium 源码及 spec，或给出可只读检查的现有路径；LLVM 正在克隆，需完成后续测。已请求是否等待后续源码就绪再提交。
- 如已有 GBS root，请指明位置；当前 gbs_llvm.conf 指向的外部 buildroot 不存在，未建立或使用它。配置路径差异与可能独立的 debug 仓库待后续明确。
- 框架业务指南缺失、契约尚未冻结，后续设计需要明确采用的框架版本及缺失业务 schema；本轮没有擅自补写上游契约。

## 挂账

- 两板所有身份、系统资源、内核配置、perf cycles/brstack/ETM/SPE/BRBE、root、Benchmark 素材检查。
- 两板实体库 pull、链接器、build-id、strip 检查；无 GBS root 时不得把主机工具分析范围擅自扩大。
- 内核版本、Kconfig 支持、架构 select、各板包/defconfig/clang 映射。
- 三架构工具包元数据查询已闭合；RPM 内工具实际可执行性未测试，板上版本不等同仓库版本。独立 debug 仓库未提供，不扩展“不存在”结论到未查询仓库。
- LLVM spec/CMake 与 FFmpeg/GStreamer/Chromium 编译配置、FFmpeg 各架构汇编启用情况。
- 获取业务指南并复核框架契约后续复审与实现进度。

续测命令与判定规则在报告 §4–6；其中待执行命令不属于已完成实测，不得据此清账。
