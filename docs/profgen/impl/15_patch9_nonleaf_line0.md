# 补丁9：非叶子line0核实与排除草稿（已实现待构建）

本轮按PM裁决实现草稿，**未构建、未验收、未提交LLVM commit、未导出0009**。正式工具仍为补丁8 `9f63c692a4239a222bfb86cd9dcab93b04a28fc32421306b597f4c799627fdc7`；未用草稿重转正式S。

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
