# N.5 阶段1身份门禁与覆盖：历史停止与修订1验收

日期：2026-11-11。基于449c9e4；补充3原文及前提核验已提交d79e285。
本报告不含正式sample profile的任何受控量。修正案3未登记。

## 1. 门禁状态

补充3的TokenLexer前提成立；两个必过真实例在第7条的未展开实参FileID标志处失败。
Thumb/A32共56个记录全量检查，均未闭合。
具体API原文、逐层证明、候选裁决方向见[04报告第8节](04_macro_function_ruling.md#8-裁决2补充3拼接来源证明与规则7停止2026-11-11)。

| 对象 | 全清单DIE | 裁决1闭合 | 裁决2既有闭合 | 外部CU闭合 | 补充3未决 | 普通候选核对未完成 | 未决总数 |
|---|---:|---:|---:|---:|---:|---:|---:|
| spike Thumb | 17 | 2 | 0 | 0 | 0 | 15 | 15 |
| spike A32 | 17 | 2 | 0 | 0 | 0 | 15 | 15 |
| FFmpeg Thumb | 28149 | 1236 | 6 | 38 | 28 | 26841 | 26869 |
| FFmpeg A32 | 28190 | 1242 | 6 | 38 | 28 | 26876 | 26904 |

完整身份结论仍以补充2清单为准：
[evidence/ruling2/supplement2/closure-summary.json](evidence/ruling2/supplement2/closure-summary.json)。
本轮仅新增来源证明和具体未决原因，不改写原闭合表。
普通候选没有被当作已闭合；单候选的定义身份/行范围核对、多候选歧义验收均未执行。

## 2. 未决类别与3个完整实例

新发现的精确原因：paste_argument_nonmacro_outside_main。
每个FFmpeg对象28个记录都有这一原因；它们均FNDA=0，但仍须通过身份门禁。

1. hpeldsp.c:333 PIXOP2：未展开实参put是FileID，
   isMacroArgExpansion=false，spelling=hpeldsp.c:333:8。
   [完整实例](evidence/ruling2/supplement3/ffmpeg-thumb-18-paste-proof.json)。
2. pel_template.c:78 DEF_PEL：外层FUNC3与内层DEF_PEL的两次拼接均文本正确，
   内层未展开实参put是FileID，isMacroArgExpansion=false。
   [完整实例](evidence/ruling2/supplement3/ffmpeg-thumb-07-paste-proof.json)。
3. rv40dsp.c:265 PIXOP2：未展开实参put同样是FileID及false标志。
   [完整实例](evidence/ruling2/supplement3/ffmpeg-thumb-33-paste-proof.json)。

这些token虽然都在精确调用实参范围内，但补充3第7条继承的非实参位置规则不允许
它们拼写在coverage主文件之外。未自行增加例外，等待用户裁决。

## 3. 后续产物状态

| 产物 | 状态与原因 |
|---|---|
| 普通候选的单候选/多候选验收及全部夹具 | 未开始：补充3两例未通过，不满足用户规定的阶段顺序 |
| U、排除清单、权重 | 未计算：身份门禁未闭合 |
| 对象登记表①②③③′、n_eff、K | 未计算；不能把“尚未计算”冒充语义上的n_eff=null |
| ③损失分解与50%门槛 | 未计算，不能判断达标或不达标 |
| 映射范围系统头/宏代码静态地址数及字节数 | 未计算：组范围未建立 |
| 正式sample profile及受控量 | 没有打开或计算 |

门禁通过后才可继续，n_eff=null的显式分支与K<50仅描述规则不变。


## 4. 修订1恢复：补充3已通过，普通候选待核对

2026-11-11：裁决2补充3修订1解决上述规则缺陷。全56条闭合，
两个必过例及第三个实例均通过；前文为历史停止记录。
当前FFmpeg Thumb/A32宏对应各34条，未决分别只剩26841/26876普通候选；spike各15条。
裁决1、GNU外部CU计数不变。详细证据见04报告8.7及rev1/closure-summary.json。
尚未计算U、①②③③′、n_eff、K或损失分解。


## 5. 修订1后的普通候选核对（2026-11-11）

本节只用S调试ELF、C调试ELF、覆盖参考和源码；没有读取正式sample profile。
`compiler_dwarf_lines.py`使用GBS的LLVM 22.1.8 API，逐CU完整加载DIE，
调用`getSubroutineName(LinkageName)`与声明位置接口，并把行表地址区间按所有
subprogram/inlined_subroutine区间端点切分；每段用`getSubroutineForAddress`确定
自身为叶子帧的DIE。行号0及文件不等于decl_file的行不进入单候选行范围检查。
同一行表区间的证明地址、DIE、文件与行号均保留；并未把“有候选”当成闭合。
四个对象C侧均有调试信息，本轮无需AST替代声明位置。

| 对象 | 普通候选逐项检查 | 通过且参考已执行 | 通过且参考未执行 | identity_ambiguous | 多候选 | 未决 |
|---|---:|---:|---:|---:|---:|---:|
| spike Thumb | 15 | 15 | 0 | 0 | 0 | 0 |
| spike A32 | 15 | 15 | 0 | 0 | 0 | 0 |
| FFmpeg Thumb | 26841 | 9785 | 12159 | 4897 | 0 | 0 |
| FFmpeg A32 | 26876 | 9792 | 12158 | 4926 | 0 | 0 |

两侧定义声明位置全部一致；未通过的是行范围条件：Thumb为空1187、越界3710；
A32为空1209、越界3717。这些按v1.5 5.8第5条已有规则记为
`identity_ambiguous`，不是新增状态，也不是未决。全部候选相关参考行必须取并集排除。
相应唯一参考源函数数为1795/1802；其FNDA和为263224835/274724687，
**这些只是函数计数，不用于代替③分母或排除的DA。**

加上裁决1（spike各2，FFmpeg1236/1242）、裁决2（FFmpeg各34）、
GNU外部CU（FFmpeg各38），全清单17/17/28149/28190每条都有封闭结论。
这只闭合身份完整性，不表示对象已通过覆盖或登记门槛。

证据根目录：`evidence/ruling2/supplement3/rev1/identity-gate/`。
- `ordinary-v2/ordinary-summary.json`：全量计数与输入SHA。
- `ordinary-v2/*-ordinary/index.json`及checks分片：每DIE候选、定义位置、
  叶子行、原因与结论。覆盖原名及编译单元副本从对应coverage-table索引引用，
  不在每个DIE里重复保存。`compaction.json`证明去重前后结论数量完全一致。
- `ordinary-v2/*-empty_leaf_line_set-example*.json`、
  `*-leaf_line_outside_range-example*.json`：每对象每类三个完整实例。
- `*-command-v2.json`、`tool-build-v2.json`：平台工具、命令、原始输出路径与SHA。
  大的完整行表/DIE JSONL留在`temp/prep-identity-gate/`。
- `ordinary-tests/`：16个synthetic夹具通过，含定义身份反例、签名/花括号差异、
  空行集合、越界、多候选、不按距离消歧与变体证据冲突等；这些不替代真实核对。

### 5.1 保留的失败与资源约束

首版API辅助器仅加载CU根DIE，输出为空；完整性断言将其拒绝，
`initial-empty-diagnosis.json`保留诊断。改为`getUnitDIE(false)`加载完整DIE后，
全量数量、名字和声明位置与旧清单一致。LLVM本体未修改。

第一次普通候选汇总把C侧多份声明重复嵌入每条S记录，触发一次3GiB scope OOM；
`ordinary-oom.json`、journal、unit与原脚本原文保留。该次cgroup销毁前没有取得
精确memory.peak，不能把3GiB上限冒充实测峰值。改为共享声明索引后，在相同3G/200%
限制内串行完成；没有提高限额。scope监测随后增加逐秒落盘的峰值快照。

覆盖损失核算初版未处理既有lcov分片归档，路径检查失败；改为逐片SHA核对并
重建到temp。第二版全局逐行集合求交耗时较长，主动终止自己的子任务（退出143）后
改为按文件排序行号、bisect查范围；这是实现效率修正，不是放宽统计规则，旧输出保留。


## 6. 身份歧义DA核算与登记门槛

`check_identity_coverage_bound.py`仅读取C覆盖LCOV的DA、参考源函数范围、
已完成的普通候选对应表。以（规范化文件、行）去重，候选范围的排除取并集，
包括未执行候选与已执行函数重叠的行；不用FNDA替代DA。
LCOV归档分片逐片和整体校验SHA后只在temp重建。

| 对象 | C可执行行 | ΣR(C) | identity_ambiguous行 | 必须排除的DA | 占ΣR(C) | ③的上界（不是实算值） |
|---|---:|---:|---:|---:|---:|---:|
| spike Thumb | 122 | 21362787097 | 0 | 0 | 0% | 100% |
| spike A32 | 122 | 21362787097 | 0 | 0 | 0% | 100% |
| FFmpeg Thumb | 13040 | 28769855208 | 168 | 1605399811 | 5.580146% | 94.419854% |
| FFmpeg A32 | 13040 | 28769855208 | 163 | 1626239322 | 5.652581% | 94.347419% |

这里使用必要条件 `U ⊆ C \ identity_ambiguous`，
因此 `③ ≤ (ΣR(C) − 歧义行DA)/ΣR(C)`。
`coverage_3_actual=null`与`U_generated=false`明确表示未生成完整U，
不能把此表的上界写成实际③，也不能据此判定通过50%门槛。

**独立的已触发门槛**：v1.5 5.8第5条“跨侧的源函数对应”规定：
`identity_ambiguous`涉及参考计数超过③分母1%时，该对象评估不可用。
两个FFmpeg对象均触发。这个门槛与③至少50%不同；没有修改或放宽任何门槛。
已向用户请求决定：先交付不可登记的静态歧义证据，还是继续完成静态U/③但保留
对象不可登记的结论。当前停在登记准备门禁，不继续后续统计。

### 6.1 必然损失的互斥分桶

| 原因集合 | Thumb DA | A32 DA |
|---|---:|---:|
| 仅empty_leaf_line_set | 1605399755 | 1626239266 |
| empty_leaf_line_set与leaf_line_outside_range同时涉及 | 12 | 12 |
| 仅leaf_line_outside_range | 44 | 44 |
| 合计 | 1605399811 | 1626239322 |

每行只计一次，桶之和严格等于身份歧义的必然排除DA。
这**不是**完整的`ΣR(C)−ΣR(U)`分解，尚未加入边界、键歧义、无键行等原因。
逐行清单及SHA位于`identity-gate/coverage-bound-v3/*/index.json`；
总表在`coverage-bound-v3/summary.json`，原始命令与退出码在`coverage-bound-v3-run/`。
`test_identity_coverage_bound.py`的8项synthetic测试通过（整数大数、恰好50%、
零分母、排除并集不重复、未执行候选重叠等）。
独立CSV复算与全覆盖DA对照见`mass-audit.json`及`mass-audit-run/`，退出0。
覆盖导出全部DA之和为34067537001，两个对象的必然歧义DA占该更大分母仍为
4.712404%/4.773575%，没有用函数入口计数夸大损失。
最大的排除行包括cabac_functions.h:144–146（每行215694437）与rectangle.h:41；
前20行原文保存在mass-audit.json。

## 7. 本轮状态与剩余项

- 补充3修订1：全部56条真实记录通过；每侧新闭合28，未决0，FNDA>0为0。
  原27项测试、新19项synthetic（包含规定15项）、三个真实实例断言全部通过。
- 普通候选：53747项（26841+26876+15+15）；
  单候选全部核对，多候选真实数量0；新增16项synthetic通过。
- 身份完整性：四个清单全部行已有封闭结论，无新未决类别；
  但身份歧义的DA门槛导致FFmpeg对象不可登记。
- 未完成：完整U、全原因排除清单、函数权重、对象登记表①②③③′/n_eff/K、
  映射范围内系统头与宏生成函数的静态地址/字节规模。
  n_eff/K尚未计算，不能声称语义上的n_eff=null或K<50；将来实现仍须走其显式分支。
- 无正式sample profile被打开或计算；没有连接板子；修正案3未登记。
  设计、LLVM本体、用户配置与认证未改。

所有新增项目文件小于1MB。大原始DIE/行表与去重前普通候选证明留在
`temp/prep-identity-gate/`，索引记录路径/SHA和重定位规则。
本阶段资源与失败清单见`identity-gate/final-audit.json`；
一次3GiB scope OOM已如实列出，未提高资源上限。

### 7.1 最终审计

全套项目测试退出0：`; ----------------------------------------------------------------------; Ran 88 tests in 240.838s; ; OK`。
成功任务的最高实测cgroup memory.peak=784560128字节，最低MemAvailable=4370006016字节；资源监测阈值终止0次。另有上述1次scope OOM，精确峰值未知；另1次效率修正主动终止不记为资源终止。

提交前空白检查发现8份原始stdout的第一行有末尾空格；保留原文，不清洗证据。
`git-whitespace-check.txt/json`保存原始检查输出与退出2；源码与文档另行检查。


## 8. 新裁决恢复（静态计算继续，登记禁令保持）

普通候选完整结果已推送d981471（fd4b5b5的后续提交）。用户裁决明确：
1%不可登记门槛不阻止静态U的计算。现在继续四个对象的歧义证据包和完整静态表，
保持门槛、不新增身份裁决、不按DA挑选闭合，不读正式sample profile。
普通结果的集中入口为[evidence/identity-gate/ordinary-index.json](evidence/identity-gate/ordinary-index.json)，
引用已推送的全部清单、SHA、单候选结果、参考DA和88项测试；旧路径保留。
后续将把本报告第6、7节更新为完整歧义包与静态表，保留此前门槛发现记录。
