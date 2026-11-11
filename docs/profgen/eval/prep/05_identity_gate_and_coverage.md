# N.5 阶段1：普通候选、歧义证据包与静态 U/③

日期：2026-11-11。基于449c9e4；补充3原文及前提核验已提交d79e285。
本报告不含正式sample profile的任何受控量。修正案3未登记。

## 1. 历史门禁状态（补充3修订1之前）

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



### 5.2 已推送的普通候选完整结果

普通结果提交 d9814714502baa2a0d446f98efb9b6c8fe75bf65；
继续静态计算裁决提交 838c88699d3c1faab2297ff4682956a35a990a2c。
集中索引：[ordinary-index.json](evidence/identity-gate/ordinary-index.json)。
四个完整清单的SHA在索引内；静态API再次枚举的DIE集合、名字、声明位置与清单逐项相等。
每个映射范围内函数都是完整清单的子集，未决0。真实多候选数量0，
多候选建立对应与多候选歧义均为0。单候选失败参考DA按③口径、C内候选行并集：
spike两侧0，FFmpeg Thumb1605399811、A321626239322，不按DIE重复累加。

## 6. identity_ambiguous 证据包（四个对象）

每组为规范化（decl_file、去后缀名字）及其全部S实例、参考候选。
本次歧义全部由单候选行范围检查失败触发；“来自不同TU”是覆盖副本的属性，
不是说出现了多个合并后的源函数候选。

机械分类在 ambiguity_package.py 的 mechanical 函数：a=不同PGO前缀；
b=有条件编译/重复include的编译器正面证据；
c=同TU同变体的不同C定义声明位置；否则d，保留失败原因。
没有b证据就不按模板文件名猜测。本数据b/c均为0。
每组恰好一类；类内DA按文件行去重，本数据不同类没有重叠行。
分类不是消歧裁决，identity_ambiguous全部保留。

| 对象 | 组数 | 涉及C行 | DA分子 | ΣR(C)分母 | 比例 |
|---|---|---|---|---|---|
| spike-thumb | 0 | 0 | 0 | 21362787097 | 0.000000% |
| spike-a32 | 0 | 0 | 0 | 21362787097 | 0.000000% |
| ffmpeg-thumb | 1795 | 168 | 1605399811 | 28769855208 | 5.580146% |
| ffmpeg-a32 | 1802 | 163 | 1626239322 | 28769855208 | 5.652581% |

| 对象 | 类别 | 组数 | DA | 占ΣR(C) |
|---|---|---|---|---|
| spike-thumb | a_different_TU | 0 | 0 | 0.000000% |
| spike-thumb | b_same_TU_conditional_or_include | 0 | 0 | 0.000000% |
| spike-thumb | c_same_TU_multiple_definitions | 0 | 0 | 0.000000% |
| spike-thumb | d_other | 0 | 0 | 0.000000% |
| spike-a32 | a_different_TU | 0 | 0 | 0.000000% |
| spike-a32 | b_same_TU_conditional_or_include | 0 | 0 | 0.000000% |
| spike-a32 | c_same_TU_multiple_definitions | 0 | 0 | 0.000000% |
| spike-a32 | d_other | 0 | 0 | 0.000000% |
| ffmpeg-thumb | a_different_TU | 316 | 1539177250 | 5.349965% |
| ffmpeg-thumb | b_same_TU_conditional_or_include | 0 | 0 | 0.000000% |
| ffmpeg-thumb | c_same_TU_multiple_definitions | 0 | 0 | 0.000000% |
| ffmpeg-thumb | d_other | 1479 | 66222561 | 0.230180% |
| ffmpeg-a32 | a_different_TU | 316 | 1539177250 | 5.349965% |
| ffmpeg-a32 | b_same_TU_conditional_or_include | 0 | 0 | 0.000000% |
| ffmpeg-a32 | c_same_TU_multiple_definitions | 0 | 0 | 0.000000% |
| ffmpeg-a32 | d_other | 1486 | 87062072 | 0.302616% |

### 6.1 明细与前90%清单

每对象 evidence/identity-gate/<object>-ambiguity/index.json 记录CSV分片SHA；
top.md按DA降序列至少20组并达到90%累计唯一DA。
Thumb/A32前20组分别覆盖1605399764/1605399811与1626239275/1626239322；
spike无歧义组，清单为空，不虚构20条。

- [Thumb前20](evidence/identity-gate/ffmpeg-thumb-ambiguity/top.md)；
  [A32前20](evidence/identity-gate/ffmpeg-a32-ambiguity/top.md)；
  [spike Thumb](evidence/identity-gate/spike-thumb-ambiguity/top.md)；
  [spike A32](evidence/identity-gate/spike-a32-ambiguity/top.md)。
- S-instances分片：每个S实例的CU、完整名字、decl_file/line、全部low/high区间、
  subprogram/inlined_subroutine标签、abstract_origin偏移、失败检查及叶子行集合。
  S-inline-flags分片另列is_inline_abstract_source与is_inlined_instance。
- candidates分片：合并参考身份、行范围、FNDA、候选行DA及C声明位置；
  candidate-copies分片：完整PGO名字、TU前缀、完整linkage、FNDA、
  命令编号及同linkage的C侧有代码DIE。此字段为空不证明C中没有抽象或优化掉的定义，
  不用于改变原身份判断。
- commands分片：完整实际命令、构建日志与行号、源文件完整相对路径。
  每个PGO副本都有命令索引；有多个命令时保留全部，不凭basename作新消歧。
- 按group/reference_id连接表，避免每行重复大对象；CU/TU/linkage事实供后续裁决，
  FNDA与DA不参与身份闭合。原有单候选C定义证明仍在共享definitions索引中。

### 6.2 三个独立1%门槛

unmatched_in_elf为已执行参考源函数没有已建立唯一对应的S实例；
仅在identity_ambiguous候选集合中不算建立对应。两种原因可重叠，
账本保留完整原因集合而不重复计数。边界按完整同名顶层组处理，本次无失败组。

| 对象 | 原因 | 行数 | DA分子 | 分母 | 比例 | >1% |
|---|---|---|---|---|---|---|
| spike-thumb | identity_ambiguous | 0 | 0 | 21362787097 | 0.000000% | False |
| spike-thumb | unmatched_in_elf | 0 | 0 | 21362787097 | 0.000000% | False |
| spike-thumb | boundary_unavailable | 0 | 0 | 21362787097 | 0.000000% | False |
| spike-a32 | identity_ambiguous | 0 | 0 | 21362787097 | 0.000000% | False |
| spike-a32 | unmatched_in_elf | 0 | 0 | 21362787097 | 0.000000% | False |
| spike-a32 | boundary_unavailable | 0 | 0 | 21362787097 | 0.000000% | False |
| ffmpeg-thumb | identity_ambiguous | 168 | 1605399811 | 28769855208 | 5.580146% | True |
| ffmpeg-thumb | unmatched_in_elf | 68 | 657157674 | 28769855208 | 2.284188% | True |
| ffmpeg-thumb | boundary_unavailable | 0 | 0 | 28769855208 | 0.000000% | False |
| ffmpeg-a32 | identity_ambiguous | 163 | 1626239322 | 28769855208 | 5.652581% | True |
| ffmpeg-a32 | unmatched_in_elf | 68 | 657157674 | 28769855208 | 2.284188% | True |
| ffmpeg-a32 | boundary_unavailable | 0 | 0 | 28769855208 | 0.000000% | False |

## 7. 静态 U、损失账本与登记状态

### 7.1 实现与输入边界

static_map_bridge.py在temp生成独立辅助程序，链接GBS LLVM 22.1.8公开DWARF/
symbolizer API；复制未修改的IPBoundary.cpp/.h并核对SHA，复用已有边界规则。
没有重编或修改GBS clang、官方llvm-profgen或LLVM源码，没有运行profile转换器。
边界实现与工具共享，本次不是独立objdump复测，也不替代此前边界验收。

先验证全部有代码DIE清单，再由父链导出顶层组并按原始名字取完整闭包。
范围由已执行参考对应或含已执行候选的identity_ambiguous导出；
只含系统头、not_instrumented、未执行参考及FNDA=0宏函数的组不纳入。
各对象groups索引保存完整角色与选择清单SHA；四对象均无“去后缀名字等于已执行参考、
却在映射范围外”的待逐个裁决组。

字节取运行ELF，映射符号取调试ELF；叶子/非叶子line0不产生键，
偏移为(Line−StartLine)&65535，discriminator按工具规则，名字不demangle并保留后缀。
GNU AS奇数下界与别名一致性校验沿用现有规则；本轮line_before_start为0。
值通过确切叶子DIE结论取得，未执行源函数的键不能替已执行源函数填行。
没有RUN、采集资格或样本量参与。

static_coverage_gate.py用SQLite控制内存，输出mapping、U、exclusions、weights分片；
audit_static_gate.py从CSV独立复算并集、权重与损失。
宏只按FileID/region类型识别；C与macro-only行交集为空的断言通过。
不按宏文件名整文件删除。n_eff=null及K无定义分支有夹具。
这不是N.5的合成profile全地址验收；本任务没有执行后者。

| 对象 | U/C行 | ① | ② | ③ | ③′ | n_eff | K | ③档 | 登记状态（本表门槛） |
|---|---|---|---|---|---|---|---|---|---|
| spike-thumb | 73/122 | 59.836066% | 61.206897% | 54.643726% | 53.354972% | 1.3285149908059033 | 19 | 50–80% | 可登记 |
| spike-a32 | 72/122 | 59.016393% | 60.344828% | 54.044553% | 52.769930% | 1.2996227284761774 | 10 | 50–80% | 可登记 |
| ffmpeg-thumb | 6741/13040 | 51.694785% | 52.822396% | 19.269762% | 16.273212% | 21.290194729173507 | 441 | <50% | 不可登记 |
| ffmpeg-a32 | 6764/13040 | 51.871166% | 52.937127% | 19.172781% | 16.191312% | 21.884972576707312 | 441 | <50% | 不可登记 |

②分母为整个覆盖导出的已覆盖行；①、③分母分别为C行数、C行DA。
spike两侧K<50，仅描述。“可登记”只表示本表门槛不禁止，不表示其余N.5已完成，
不授权现在登记修正案3。FFmpeg两侧身份歧义、unmatched均>1%，且③<50%，不可登记。
按裁决完成全部静态表后停止。

④的条目分类比例统一为：**未计算（需要 RUN 的 body 分母，修正案3登记后按 RUN 计算）**。
下列仅为静态部分，不充当body比例：

| 对象 | 歧义键 | 受影响行 | 涉及C行 | identity歧义组/行 | 系统头地址/字节 | 宏函数地址/字节 |
|---|---|---|---|---|---|---|
| spike-thumb | 0 | 0 | 0 | 0/0 | 0/0 | 0/0 |
| spike-a32 | 0 | 0 | 0 | 0/0 | 0/0 | 0/0 |
| ffmpeg-thumb | 0 | 0 | 0 | 1795/168 | 3067/10036 | 0/0 |
| ffmpeg-a32 | 0 | 0 | 0 | 1802/163 | 3375/13500 | 0/0 |

系统头统计为映射范围内叶子DIE属于裁决1的唯一已证明指令起点及其指令长度和，包含line0地址。逐文件/函数见special-code分片。宏函数全部FNDA0且不在映射范围内，规模0。

| 对象 | 宏region行DA | macro-only DA | 覆盖总DA | macro-only占比 | 宏展开文件全部DA（描述） |
|---|---|---|---|---|---|
| spike-thumb | 516004099 | 516004099 | 21878791196 | 2.358467% | 21878791196 |
| spike-a32 | 516004099 | 516004099 | 21878791196 | 2.358467% | 21878791196 |
| ffmpeg-thumb | 6563256990 | 5285313702 | 34067537001 | 15.514223% | 31754091334 |
| ffmpeg-a32 | 6563256990 | 5285313702 | 34067537001 | 15.514223% | 31754091334 |

### 7.2 完整互斥损失分桶

保留完整原因集合，不用一个原因覆盖其他原因；四对象独立复算差值均为0。

**spike-thumb**

| 完整原因集合 | 行数 | DA |
|---|---|---|
| no_key_line | 49 | 9689364215 |

21362787097 − 11673422882 − 9689364215 = **0**（assertion通过）。

**spike-a32**

| 完整原因集合 | 行数 | DA |
|---|---|---|
| no_key_line | 50 | 9817364215 |

21362787097 − 11545422882 − 9817364215 = **0**（assertion通过）。

**ffmpeg-thumb**

| 完整原因集合 | 行数 | DA |
|---|---|---|
| identity_ambiguous | 73 | 326913076 |
| identity_ambiguous, no_key_line | 64 | 631403298 |
| identity_ambiguous, no_key_line, reference_ambiguity, unmatched_in_elf | 10 | 36 |
| identity_ambiguous, no_key_line, unmatched_in_elf | 21 | 647083401 |
| no_key_line | 5801 | 21111806771 |
| no_key_line, reference_ambiguity | 142 | 236199535 |
| no_key_line, unmatched_in_elf | 37 | 10074237 |
| reference_ambiguity | 151 | 262492282 |

28769855208 − 5543882572 − 23225972636 = **0**（assertion通过）。

**ffmpeg-a32**

| 完整原因集合 | 行数 | DA |
|---|---|---|
| identity_ambiguous | 68 | 340989569 |
| identity_ambiguous, no_key_line | 64 | 638166316 |
| identity_ambiguous, no_key_line, reference_ambiguity, unmatched_in_elf | 10 | 36 |
| identity_ambiguous, no_key_line, unmatched_in_elf | 21 | 647083401 |
| no_key_line | 5783 | 21118868595 |
| no_key_line, reference_ambiguity | 146 | 235797038 |
| no_key_line, unmatched_in_elf | 37 | 10074237 |
| reference_ambiguity | 147 | 262894779 |

28769855208 − 5515981237 − 23253873971 = **0**（assertion通过）。


无键损失示例：spike.c:69、70各DA=4063610861；
FFmpeg的libavcodec/arm/cabac.h多行各DA=255523038。
这是参考行有计数、静态映射没有对应唯一键的事实；没有把“同函数其他行有键”
扩大成这些行也可评价。完整参考身份与并存原因都在exclusions分片。
改变行域需要裁决，不能挑选DA大的条目修补。

### 7.3 产物、复现与执行失败

各对象static/index.json列出所有分片及SHA；summary.json为对象表，
audit.json为独立CSV复算；unmatched-reference分片列出没有唯一对应的已执行参考身份及全部歧义候选DIE。上层inventory-command/map-command记录运行/调试ELF SHA、
辅助程序SHA、完整原始输出路径与SHA。大JSONL、SQLite、辅助程序只留
temp/prep-static-gate/。各命令逐个经run_scoped.py执行：

    python3 tools/profgen_eval/static_map_bridge.py build
    python3 tools/profgen_eval/static_map_bridge.py inventory <object>
    python3 tools/profgen_eval/static_gate_data.py <object>
    python3 tools/profgen_eval/static_map_bridge.py map <object>
    python3 tools/profgen_eval/static_coverage_gate.py <object>
    python3 tools/profgen_eval/ambiguity_package.py <object>
    python3 tools/profgen_eval/audit_static_gate.py <object>

保留的实现失败：GNU外部CU无decl_line文本，首次完整性比较空串转整数失败，
改为与API的0核对，身份不变；歧义包首次误把CU header偏移当CU DIE偏移查表，
改用完整清单的CU DIE键。原始失败scope保留，均非身份规则未决。
首次调用在项目工具目录生成的Python缓存已移入temp/prep-static-gate/python-cache-first-invocation，未提交缓存；后续禁止写pycache。
C定义明细补充内联有代码DIE；首版仅取out-of-line的派生产物保留temp。
spike Thumb初版n_eff分支标签阈值误写5，审计改为冻结阈值3，数值与U未变。

原88项保留、新增25项synthetic，共**113通过、0失败**，见static-tests/。包含完整内联键、零行、偏移取模、后缀、四类机械分类、重叠损失、空/常量权重、n_eff null、K并列/零值/仅描述。

本轮memory.peak最高528437248B，最低MemAvailable 11063332864B，资源阈值终止0次、无OOM。resource-summary.json保留各scope原文索引。前一阶段普通候选OOM仍见5.1，不混为本轮峰值。


### 7.4 停止与边界

身份未决仍为0，未扩大任何裁决。③<50%及1%门槛均保留。
现在停止等待歧义类别和低保留率裁决；不登记修正案3、不做仿真或其他N.5。
没有读取正式sample profile、RUN body比例或受控量；不碰板子，
不改LLVM、设计、认证及三个用户配置。项目输入产出均在WORKDIR；
GBS clang包装器固定TMPDIR到WORKDIR/temp/tmp，clang本体未重编。未发现项目文件越界写入。

## 8. 本轮人工裁决

不可登记不等于停止静态计算，全部对象静态表照常完成；不放宽门槛。
④body比例依v1.5第538/540行属登记后RUN级量，登记前不计算。
完成证据后停止，不进入其他准备阶段。

## 9. 保留的此前上界计算与停止记录（历史）

### 历史6. 身份歧义DA核算与登记门槛

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

#### 历史6.1 必然损失的互斥分桶

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

### 历史7. 本轮状态与剩余项

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

#### 历史7.1 最终审计

全套项目测试退出0：`; ----------------------------------------------------------------------; Ran 88 tests in 240.838s; ; OK`。
成功任务的最高实测cgroup memory.peak=784560128字节，最低MemAvailable=4370006016字节；资源监测阈值终止0次。另有上述1次scope OOM，精确峰值未知；另1次效率修正主动终止不记为资源终止。

提交前空白检查发现8份原始stdout的第一行有末尾空格；保留原文，不清洗证据。
`git-whitespace-check.txt/json`保存原始检查输出与退出2；源码与文档另行检查。


### 历史8. 新裁决恢复（静态计算继续，登记禁令保持）

普通候选完整结果已推送d981471（fd4b5b5的后续提交）。用户裁决明确：
1%不可登记门槛不阻止静态U的计算。现在继续四个对象的歧义证据包和完整静态表，
保持门槛、不新增身份裁决、不按DA挑选闭合，不读正式sample profile。
普通结果的集中入口为[evidence/identity-gate/ordinary-index.json](evidence/identity-gate/ordinary-index.json)，
引用已推送的全部清单、SHA、单候选结果、参考DA和88项测试；旧路径保留。
后续将把本报告第6、7节更新为完整歧义包与静态表，保留此前门槛发现记录。
