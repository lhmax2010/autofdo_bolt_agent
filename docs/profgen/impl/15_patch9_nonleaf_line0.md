# 补丁9：非叶子line0排除（已通过正式验收）

以下保留前轮草稿与资源门禁停止记录；最新完成状态见末节。补丁9已完成正式GBS/lit、C1及历史重放，LLVM本地提交 15a5ec3f46283ad2eccaecf97b2eac2a0e43d65c；本轮不重转正式S、不做最终质量矩阵。

## 已完成：正式工具行为核实

复用`Inputs/ip-mode/counting-extra/nonleaf-zero.perfbin`：只将head素材两处DW_AT_call_line从12置0，指令字节、正叶子行不变。两内联样本period3/7，加一个顶层样本100；原工具实际输出：

```text
both:110:0
 2: 100
 65525: _ZL4leftj.__uniq.326972730918826971593076268821660195379:3
  1: 3
 65525: _ZL5rightj.__uniq.326972730918826971593076268821660195379:7
  1: 7
```

正常head对照输出调用点1，total同为110。`ProfiledBinary.cpp`原1288只登记非叶子line0，原1295继续计算`(CallerFrame.Line - CallerFrame.StartLine) & 0xffff`；本例StartLine11，故0−11环绕为65525。`ProfileGenerator.cpp`原402–403只作usable_nonleaf_line_zero子统计，仍构造调用树。命令、工具SHA、两份profile和完整报告见[01](evidence/15/01_existing_behavior.json)。这满足用户授权补丁9的条件；不是因未知新缺陷擅自扩范围。

## 已完成：代码、测试与schema草稿

- 仅IP：正叶子行的原始内联栈中任一非叶子行0，在构造任何调用点之前登记地址并返回空栈；不截成半棵树，不改样本PC、LBR或共享符号化库。
- 初始归类同时记入in_func_no_line和nonleaf_line_zero；不进入OriginalUsable、sampled函数集合或profile。avg/补零符号化同用空栈，从而不为这些位置造调用点；prev-inst遇不可用前驱仍按原规则不调整。
- 报告新增`samples.target.in_func_no_line.nonleaf_line_zero`计数对象（sample_count、period_sum、normalized_weight）。保持schema_version1；未知仍unknown，未发生为0。旧隐藏usable_nonleaf_line_zero诊断保留为0，避免无关接口删除。
- 修改现有lit：sum/max混合输入应total100且只剩顶层body；正常调用点控制仍total110；全非叶子line0输入应generate/no usable samples，失败JSON分类正确、旧profile不变。Python断言语法检查通过；**测试尚未执行**。

草稿5文件+92/-21，完整diff见[02](evidence/15/02_pending_diff.json)，实际位置及范围见[05](evidence/15/05_draft_scope.json)。GBS平台clang-format处理改动行并dry-run通过，[03](evidence/15/03_format.json)。packaging/llvm.spec保留原本地改动，不纳入本草稿。

## 未完成：重构建与最终验收

唯一一次重任务门禁检查：MemAvailable=5.580803GiB、SwapFree=0.000290GiB，分别不足10GiB/1GiB。因此不启动、不重试GBS/lit；没有开发编译绕过门禁。证据[04](evidence/15/04_heavy_gate.json)。状态为“已实现待构建”，不能声称功能通过。

待资源允许后的独立授权：同配置GBS增量-j6、16G/600%scope，正式%check lit、C1两遍636、14份完整导出逐项解释差异、全量S重转及质量变化；通过后才提交LLVM补丁9、导出0009和给出新工具SHA。尚未重转的70组保留补丁8结果，不用算术预测替代实际转换。

## 待设计 v0.8 登记

按PM授权，把“正叶子行但非叶子line0”整样本排除到in_func_no_line，新增明确子项；不允许无效调用点偏移污染profile。此修改应与原非叶子line0挂账一起登记，当前仅实现草稿，挂账不能标为验收关闭。冻结v0.7正文未改。

## 新重构建窗口（2026-11-06；等待中）

用户替换重任务门禁：北京时间2026-11-06 22:00至11-07 08:00每10分钟检查MemAvailable≥14GiB，不查SwapFree；满足即一次启动GBS增量，scope MemoryMax=10G、CPUQuota=400%，_smp_mflags -j4及实际Ninja使用的mlgo_build_jobs 4。构建每60秒保存meminfo，连续两次<3GiB立即终止本任务scope，不碰其他进程。等待与构建均写“已结束”、时间、状态及ALL-END。当前仅等待，未构建。

worker与日志：temp/profgen-patch9/window/{wait_worker.py,build_child.py,wait.log,status.txt,resources.jsonl}；查看：tail -n 10 temp/profgen-patch9/window/wait.log、cat temp/profgen-patch9/window/status.txt。成功后还须正式%check lit、C1两遍636、14份历史重放逐项解释，全部通过才提交LLVM/导出0009；本轮明确不重转正式S、不做矩阵。

## 本轮完成：正式构建、验收与本地补丁9（2026-11-06）

22:00第一次窗口检查MemAvailable=22,933,276KiB（21.8709GiB），满足≥14GiB；不检查SwapFree。此前仅等待，没有提前编译。等待与构建日志都有“已结束”、时间与状态；原始记录见[06](evidence/15/06_window_build.json)。输入HEAD、五个草稿文件与本地spec SHA在启动前逐项核对，未变化。只给GBS及其子进程设置专用HOME与GIT_CONFIG_NOSYSTEM。

|验收项|结果|
|---|---|
|GBS|退出0；22:00:00.136248–22:17:59.720993 +08:00；1079.586秒|
|并发与scope|GBS _smp_mflags -j4；实际Ninja mlgo_build_jobs 4；10G/400% scope|
|Ninja|107步；不是全量7633步重编|
|正式%check lit|86项：84 PASS、1 UNSUPPORTED、1 XFAIL、0 FAIL；旧结果类别相同|
|C1|两遍各636条（127原命令＋508格式变体＋纯IP负对照）；两遍相同、基线差异0|
|历史重放|14份各两遍，全部确定；4份成功profile字节相同，10份既有失败仍不写profile|
|Schema/格式|140报告、396字段路径，双向差集空；GBS clang-format改动行dry-run成功|
|提交|15a5ec3f46283ad2eccaecf97b2eac2a0e43d65c，5文件+92/-21；author/committer均Hao Lin|
|补丁|patches/profgen/0009-llvm-profgen-Exclude-IP-samples-with-missing-non-lea.patch；二进制format-patch已导出，反向应用check退出0|
|新工具SHA-256|2e8895afce661b5fdc8cacab2b3323496fca51af7bd7b51c3753aa8328b7d0d5|

证据：[lit与测试名](evidence/15/07_lit.json)、[C1](evidence/15/08_c1.json)、[逐份重放](evidence/15/09_historical_replay.json)、[schema/format/提交审计](evidence/15/10_schema_format_commit.json)。packaging/llvm.spec未进入提交，原本地测试改动逐字节保留；未推送LLVM或Gerrit，冻结v0.7未改。

### 非叶子line0的正式结果

原先两个无效调用点65525的样本现在整体排除：in_func_no_line=2、nonleaf_line_zero=2、period_sum=10；sum/max只保留both total100、body2=100，无65525或部分内联树。正行号对照仍total110、正常调用点；全排除输入generate/no usable samples，旧profile不变，失败报告子计数为2。非IP/LBR行为由C1闭合。[实际profile、JSON与诊断](evidence/15/12_formal_nonleaf_behavior.json)

### 历史重放逐项差异

所有输入的目标/usable/LOST/身份/边界等既有字段不变。新增nonleaf_line_zero计数为0；另两处差异仅为tool.arguments中--output和--quality-report移到补丁9临时目录。没有归类变化。这14份不含本轮70组正式S，不能据此声称正式S已重转。

|输入|每遍退出码|与补丁8的profile比较|JSON差异原因|
|---|---:|---|---|
|05-fixed|1|两版均无profile|新增0子项；两处输出argv路径改变|
|05-multi|1|两版均无profile|新增0子项；两处输出argv路径改变|
|05-freq|1|两版均无profile|新增0子项；两处输出argv路径改变|
|05-buildid|1|两版均无profile|新增0子项；两处输出argv路径改变|
|05-lost|1|两版均无profile|新增0子项；两处输出argv路径改变|
|07-fork-cases|0|字节相同|新增0子项；两处输出argv路径改变|
|07-exec-cases|0|字节相同|新增0子项；两处输出argv路径改变|
|07-exec-after|0|字节相同|新增0子项；两处输出argv路径改变|
|07-deleted-libdeleted_probe.so|0|字节相同|新增0子项；两处输出argv路径改变|
|07-module|1|两版均无profile|新增0子项；两处输出argv路径改变|
|09-fixed|1|两版均无profile|新增0子项；两处输出argv路径改变|
|09-multi|1|两版均无profile|新增0子项；两处输出argv路径改变|
|09-freq|1|两版均无profile|新增0子项；两处输出argv路径改变|
|09-buildid|1|两版均无profile|新增0子项；两处输出argv路径改变|

10份非零退出是基线已有的generate/no usable samples，不是本补丁新增失败，不能表述成“14份都成功生成profile”。原件、两遍哈希和完整差异在09证据及temp/profgen-patch9/real/。

### 资源与待设计v0.8登记

本轮最低已保存MemAvailable=9,607,548KiB（9.162472GiB）；构建期间最低19.217651GiB，未触发连续两次<3GiB终止。构建scope观测峰值9.532642GiB（含缓存），GBS子进程最大RSS2,603,416KiB；C1最大RSS110,888KiB，重放320,240KiB。全任务观测RSS最大3,168,464KiB来自已按用户规则停止的FFmpeg覆盖scope OOM；轻任务全局内存暂停/终止均0。[完整meminfo与汇总](evidence/15/11_final_resources.json)

旧正式工具9f63c692及实际加载的libLLVM已复制到temp/profgen-patch9/prebuild-tool/并核对SHA，供可追溯复核。不是用新工具覆盖唯一存档。

待v0.8登记：PM授权的非叶子line0整上下文排除及报告子项已实现、验收；不是对非叶子行0自行生成偏移或截断内联树。正式S重转、最终质量矩阵与性能测量按本轮范围均未进行，留待下一任务；频率资格不变。

补丁邮件容器检查说明：根仓库对新加入的format-patch文件执行diff --check，会把空白上下文行的单空格前缀及标准邮件签名分隔符尾空格报出；原文记录在10证据。LLVM源码diff --check、格式检查和补丁反向应用检查均通过；未删改生成补丁字节，文档/证据另做diff --check。
