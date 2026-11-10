# N.5 #16 完整身份清单：停止记录

**停止原因：静态清单中存在 C 覆盖参考没有候选的 clang 系统头内联函数，按 v1.5 现有规则不能给出封闭结论。未计算 U、①–③′、n_eff、K 或任何损失份额。**

## 已取得的静态清单

独立运行 GBS平台 llvm-dwarfdump --debug-info，不以采样地址或映射范围筛选；记录所有带非空代码区间的 subprogram/inlined_subroutine 及所引用的抽象定义。名称遍历顺序依源码 DWARFDie.cpp:327–368,530–552，每个DIE先MIPS再标准linkage，引用使用相同LIFO遍历，最后才name。当前实现是待完整夹具验收的初稿，不能视为已完成对应门禁。

| 对象 | S有代码DIE / CU | C有代码DIE / CU |
|---|---:|---:|
| spike Thumb | 17 / 6 | 264 / 24 |
| spike A32 | 17 / 6 | 264 / 24 |
| FFmpeg Thumb | 28149 / 377 | 26786 / 391 |
| FFmpeg A32 | 28190 / 377 | 26870 / 391 |

这里是DIE实例数，含内联实例，不是去重函数数。清单在 evidence/*-inventory-tables/，代码DIE、CU、引用定义分别分片；index记录生成命令、完整原始dwarfdump流SHA和各分片SHA。重复CU字段通过CU引用保留。原始C/S运行与调试文件均和既有产物清单SHA一致。

C构建实际带有DWARF，故本轮没有使用AST替代，更没有用仅行范围包含关系冒充定义身份证据。完整单候选声明位置/行集合核对尚未进行。

## 可直接复核的阻塞样例

FFmpeg Thumb S：
- CU libavcodec/aac/aacdec.c，producer=clang version 22.1.8。
- 有代码 DW_TAG_inlined_subroutine DIE 0x4652，区间 [0x2fe6c,0x2fe72)；外层 ff_aac_output_configure。
- abstract_origin=0x42ca，DW_AT_name="memcpy"，DW_AT_decl_file="/usr/include/bits/string_fortified.h"，DW_AT_decl_line=26。
- C调试文件也保留该内联函数；C覆盖JSON中没有memcpy源函数，覆盖文件表没有/usr/include/文件。
- 原始输出：evidence/ffmpeg-thumb-memcpy-die/stdout.txt、ffmpeg-thumb-memcpy-origin/stdout.txt、ffmpeg-thumb-C-memcpy/stdout.txt。

去掉 .__uniq.<digits>、两侧文件路径做 posixpath.normpath 后：
- Thumb：1308个有代码DIE找不到精确候选，其中1236个声明在/usr/include/；84种原始声明文件/名字/producer组合。
- A32：1314个，其中1242个声明在/usr/include/；84种组合。
- 清单：ffmpeg-{thumb,a32}-candidate-audit.json。这是候选缺失清单，**不是这些函数全部可排除的结论**，也不是基于样本的任何计数或占比。其余非系统头条目尚未裁决。

编译器源码支持这是正常覆盖排除路径：src/llvm/clang/lib/CodeGen/CoverageMappingGen.cpp:49–52的system-headers-coverage默认false；:1575–1579不传播计数到系统头函数体。摘录在 system-header-coverage-source.txt。本轮未改选项、未重建，不把一般源码规则直接当每条身份已闭合的证据。

## 为什么不能自行继续

v1.5 5.8第5条与N.5 #16要求所有有代码身份都有结论，clang CU中缺覆盖记录不能自动成为not_instrumented。not_instrumented的外部CU条件要求 producer 不是评估clang且命中带证据的清单；上述实例不满足。也不能删除它们或只枚举有覆盖候选的函数。

已向用户请求裁决：是否为有来源证据的系统头内联函数另定封闭状态及范围处理。候选方向是单独、明确的已知未覆盖系统头状态，并保留其与外层/内联体的关系；另一方向是修订C参考构建以覆盖系统头，需单独授权重建。两者本轮都没有执行。尚未判定其他缺候选条目，不将一次裁决扩大为所有clang缺候选函数的通行规则。

## 本轮未完成清单与门槛表

| 对象 | ① | ② | ③ | ③′ | n_eff | K | 损失分桶 |
|---|---|---|---|---|---|---|---|
| spike Thumb | 未计算 | 未计算 | 未计算 | 未计算 | 未计算 | 未计算 | 未生成 |
| spike A32 | 未计算 | 未计算 | 未计算 | 未计算 | 未计算 | 未计算 | 未生成 |
| FFmpeg Thumb | 未计算 | 未计算 | 未计算 | 未计算 | 未计算 | 未计算 | 未生成 |
| FFmpeg A32 | 未计算 | 未计算 | 未计算 | 未计算 | 未计算 | 未计算 | 未生成 |

停止点在完整身份闭合之前，**不是③已经低于50%**。不能将未决函数随意放进损失桶后给出一个门槛数字。

N.5 #16全部合成夹具（含Codex条件编译反例）、跨侧单候选定义核对、外部CU正面来源清单、静态地址映射、U/权重均未完成；不存在假定这些测试通过的清单。#13已通过的7项见01报告，summary交叉核对仍挂账。未执行新工具转换或CALIBRATION冒烟。

## P9转换可用性（只读既有报告）

只检索 docs/profgen/impl/15_patch9_nonleaf_line0.md 与 docs/profgen/eval/quality_round1.md 的报告文字，没有打开其链接的profile、质量JSON或诊断。
现有文字没有逐份明确给出第一轮正式S的prev-inst/avg成功表；仅有补丁测试和历史重放的总体记录，不能据此推定正式S两种配置成功。此项记“报告信息不足，未核实”，不新转换。允许后续在不读profile的前提下核对已存命令/报告以补证。

## 待人工裁决

1. 上述clang系统头内联体的封闭分类与范围规则，是否纳入设计后续修订。
2. 其余缺候选身份需逐条查来源；不以低权重或范围外免除完整清单门禁。

本轮设计不改、修订3未登记，未计算正式sample profile受控量。资源见01报告。本阶段未运行任何board/sdb命令，未触碰配置三项或任何LLVM远端。
