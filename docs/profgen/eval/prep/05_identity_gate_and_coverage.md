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

## 10. 裁决3、裁决4修订1/2与新旧对照（2026-11-11）

基于a8aae984c31fa89cca5eefad46b60ace75539087。裁决及两次修订原文见[rulings.md](rulings.md)，待折入v1.6并经三家评审后才可登记。本轮已完成静态计算并停止；修正案3未登记，未打开正式sample profile，未计算RUN受控量，未连接板子。旧规则代码与旧结果不变。

### 10.1 实际编译参数、来源与实现

[compile-options.json](evidence/identity-gate/ruling3-4/compile-options.json)与各对象S/C的commands分片记录完整命令、实际构建日志路径/行号、日志SHA、编译器SHA。spike各1条，FFmpeg各311条libavcodec C源文件命令；不是依据spec推测。

|对象（S/C相同）|优化选项（末项生效）|调试选项|ISA选项（末项生效）|
|---|---|---|---|
|spike Thumb|-Os|-g2 -gdwarf-4 -g|-mthumb -mthumb|
|spike A32|-Os|-g2 -gdwarf-4 -g|-mthumb -marm|
|FFmpeg Thumb|-Os -O3|-g2 -gdwarf-4 -g -g|-mthumb -mthumb -mthumb|
|FFmpeg A32|-Os -O3|-g2 -gdwarf-4 -g -g|-mthumb -marm -marm|

所有S/C均有-fdebug-info-for-profiling、-funique-internal-linkage-names；C另有-fprofile-instr-generate、-fcoverage-mapping。首次摘要将dv_profile.c等文件名误识为选项，已修为只看以减号开头的参数；首轮输出保存在temp/prep-ruling3-4/compile-option-first-pass，最终为compile-options-v2-run。

新增Python入口为ruling34_inputs、ruling34_dwarf、ruling3_domain、ruling34_rules、ruling4_dwarf、ruling4_apply、ruling4_keys、ruling4_callsite、ruling4_rev2_evidence、ruling34_static、ruling34_audit；都在tools/profgen_eval。只编译取证helper并链接GBS LLVM公开API，没有修改或重编clang本体、LLVM/profgen源码或补丁。原有static_coverage_gate等入口不变。

### 10.2 裁决3：C构建自己决定C

C参考函数匹配来自C调试ELF的名字/声明与覆盖记录；候选须唯一且FNDA>0。C自身行表非零、非end_sequence记录的地址DIE链须落在已执行参考函数代码内。没有用S行表或S映射决定C。原macro-only排除保留。

|对象|旧C行|新C行|旧ΣR(C)|新ΣR(C)|code_free行|code_free DA|
|---|---|---|---|---|---|---|
|spike-thumb|122|75|21362787097|11674422883|47|9688364214|
|spike-a32|122|74|21362787097|11546422883|48|9816364214|
|ffmpeg-thumb|13040|7504|28769855208|6789285726|5536|21980569482|
|ffmpeg-a32|13040|7523|28769855208|6780632541|5517|21989222667|

每对象*-C-domain/index.json登记输入及输出SHA、生成命令；code-lines分片逐行保存C的CU/row/地址/DIE/参考ID。移出行的逐行与文件汇总分别在code-free-lines、code-free-files分片。四对象断言旧ΣR(C)−新ΣR(C)=code_free DA全部通过。
原始大行表在temp/prep-ruling3-4/*-C-dwarf.jsonl，精确路径和SHA见*-C-dwarf-command.json。

### 10.3 实例清单、声明路径与完整上下文键

实例范围严格为原有有地址区间DIE：spike各17，FFmpeg Thumb28149、A3228190；普通候选分别15/15/26841/26876。无代码定义仅作为abstract_origin来源，没有加入组判定。

逐属性的声明查找路径在*-rev1-identity/declaration-paths分片（目录名保留，内容为最终修订2）。每个inline实例的decl_file、decl_line均经abstract_origin：spike各8、FFmpeg23519/23557；查找与公开API结果断言一致。源码及SHA见declaration-source.txt：DWARFDie.cpp:340–370、557–568。

修订1初算将“后代有非零叶子行”等同“产生键”；额外交叉核对发现Thumb47/A3252个实例全部因非叶子line0无键，已暂停并取得修订2，未自行放宽。暂停证据保留在descendant-key-crosscheck.json及*-nonleaf-zero-key-cases.json；初算表保留temp/prep-ruling3-4/revision1-provisional，comparison-PROVISIONAL.json明确不是最终表。

最终无键判定直接使用正式ProfiledBinary.cpp构造调用栈键的原文代码块，包含叶子/非叶子line0拒绝与非法名字截断；没有另写近似规则。独立helper仅设置IPMode=true、UseCanonicalFnName=false、UseProbeDiscriminator=false，与这批DWARF IP构建一致。逐字节摘取区间、SHA、完整块与编译命令见rev2-key-tool-build.json、formal-key-block.txt。枚举全部原清单顶层函数，不把未选择的函数当作“没找到键”；all-key-proofs保存每个DIE的指令覆盖数和被接受键数。原映射内358/359/413090/401052条指令的接受状态和栈深与正式代码结果逐条一致，差异0。

无键豁免仍同时要求：定义身份通过；自身声明文件非零叶子行与直接子调用行均不越界；不存在其他文件非零叶子行。任一不满足仍失败。

#### a–e分类与判定

下表按原完整普通候选清单统计，DA是每类别涉及参考行的并集，组可跨类，类别DA不可直接相加。不存在的类别/结果显式0见各对象*-rev2-proof/a-e-verdicts；自身正常非零叶子行的普通实例另列，未强塞进a–e。

|对象|类别|结果|实例|组|参考DA|
|---|---|---|---|---|---|
|ffmpeg-thumb|a_self_and_descendants_zero|exempt|20|15|958247895|
|ffmpeg-thumb|b_descendant_key_call_in_decl_file|failed|167|30|28|
|ffmpeg-thumb|b_descendant_key_call_in_decl_file|passed|916|40|647151844|
|ffmpeg-thumb|c_descendant_key_call_not_in_decl_file|failed|32|2|21777|
|ffmpeg-thumb|e_nonleaf_zero_rejected|exempt|52|14|647164269|
|ffmpeg-a32|a_self_and_descendants_zero|exempt|25|17|892003561|
|ffmpeg-a32|b_descendant_key_call_in_decl_file|failed|170|30|28|
|ffmpeg-a32|b_descendant_key_call_in_decl_file|passed|925|41|647151844|
|ffmpeg-a32|c_descendant_key_call_not_in_decl_file|failed|32|2|21777|
|ffmpeg-a32|e_nonleaf_zero_rejected|exempt|57|17|734226337|

用户指出的e子集独立核对如下（不是用FNDA或DA筛选豁免）：

|对象|e实例|组|参考DA|判定|
|---|---|---|---|---|
|spike-thumb|0|0|0|{}|
|spike-a32|0|0|0|{}|
|ffmpeg-thumb|47|9|647164269|{'exempt': 47}|
|ffmpeg-a32|52|12|734226337|{'exempt': 52}|

每个e实例所有静态地址的完整上下文、被拒绝frame、其来源子DIE及原始DW_AT_call_line（含属性是否存在）、豁免证据与结果在*-rev2-proof/e-addresses、e-instances分片。至少三例可直接按DIE定位：
Thumb 0x39b3e/0x3aea1（put_bits），0x193419（get_bits_long）；A32 0x3ca92/0x3d720（put_bits），0x16c808（decode_cabac_residual_nondc）。其中0xf0582的get_bits叶子行340、get_bits_long调用行0，最终按修订2豁免。
一次取证脚本断言发现lexical block下的inline DIE未被父函数“直接子列表”收录；新增直接读取每个inline DIE原始call属性的helper补齐来源，未改变身份/键规则。失败原文在ffmpeg-thumb-rev2-proof-run，修复后两侧proof-v2-run退出0。

纯空叶子原因组仍是Thumb69、A3277；另有同时含空集合与越界的19/18组，分列。每类原始行、DIE区间、直接子调用及至多三个完整实例见*-audit/pure-empty-example分片；真实d类若为0如实记0，失败语义由synthetic夹具覆盖。

### 10.4 指定真实例与cabac逐行对照

逐DIE完整检查见*-rev1-identity/example-*；以下保留指定函数的精确链接名，包含同源多个.__uniq.实例时逐组列出：

|对象|链接名|实例|旧原因|新结论|新原因|新实例状态|
|---|---|---|---|---|---|---|
|ffmpeg-thumb|_ZL14fill_rectanglePviiiji|121|['empty_leaf_line_set']|reference_executed|[]|{'pass': 111, 'no_key_instance': 10}|
|ffmpeg-thumb|_ZL9get_cabacP12CABACContextPh|104|['empty_leaf_line_set']|reference_executed|[]|{'pass': 102, 'no_key_instance': 2}|
|ffmpeg-thumb|_ZL8get_bitsP13GetBitContexti|2133|['empty_leaf_line_set']|reference_executed|[]|{'pass': 1821, 'no_key_instance': 312}|
|ffmpeg-a32|_ZL14fill_rectanglePviiiji|121|['empty_leaf_line_set']|reference_executed|[]|{'pass': 111, 'no_key_instance': 10}|
|ffmpeg-a32|_ZL9get_cabacP12CABACContextPh|103|['empty_leaf_line_set']|reference_executed|[]|{'pass': 102, 'no_key_instance': 1}|
|ffmpeg-a32|_ZL8get_bitsP13GetBitContexti|2138|['empty_leaf_line_set']|reference_executed|[]|{'pass': 1821, 'no_key_instance': 317}|

|ffmpeg-thumb|_ZL15filter_mb_edgehPhiPKsjiiPK11H264Contexti|71|['empty_leaf_line_set']|reference_executed|[]|{'pass': 39, 'no_key_instance': 32}|
|ffmpeg-thumb|_ZL15filter_mb_edgevPhiPKsjiiPK11H264Contexti|71|[]|reference_executed|[]|{'pass': 66, 'no_key_instance': 5}|
|ffmpeg-thumb|_ZL16filter_mb_edgechPhiPKsjiiPK11H264Contexti|32|[]|reference_executed|[]|{'pass': 8, 'no_key_instance': 24}|
|ffmpeg-thumb|_ZL16filter_mb_edgecvPhiPKsjiiPK11H264Contexti|35|[]|reference_executed|[]|{'pass': 32, 'no_key_instance': 3}|
|ffmpeg-a32|_ZL15filter_mb_edgehPhiPKsjiiPK11H264Contexti|68|[]|reference_executed|[]|{'pass': 38, 'no_key_instance': 30}|
|ffmpeg-a32|_ZL15filter_mb_edgevPhiPKsjiiPK11H264Contexti|71|[]|reference_executed|[]|{'pass': 66, 'no_key_instance': 5}|
|ffmpeg-a32|_ZL16filter_mb_edgechPhiPKsjiiPK11H264Contexti|39|[]|reference_executed|[]|{'pass': 20, 'no_key_instance': 19}|
|ffmpeg-a32|_ZL16filter_mb_edgecvPhiPKsjiiPK11H264Contexti|32|[]|reference_executed|[]|{'pass': 32}|

arm/cabac.h第36–105行共70行的C原始行表、C域成员、S键和地址见*-audit/cabac-36-105分片。两侧在此区间有C行表记录/有S键的行均为36、104；其余行逐行列出否，不用S结果替代C证据。


### 10.5 四对象旧/新登记表

“可登记”仅指本表门槛；裁决3/4仍须折入v1.6并经三家评审，本轮不实际登记。①②③③′按各自原定义；引用C的使用新C。④body比例不计算。

|对象|规则|U行|ΣR(U)|①|②|③|③′|n_eff|K|表内状态|
|---|---|---|---|---|---|---|---|---|---|---|
|spike-thumb|旧|73|11673422882|59.836066%|61.206897%|54.643726%|53.354972%|1.328515|19|可登记|
|spike-thumb|裁决3+4修订2|73|11673422882|97.333333%|61.206897%|99.991434%|53.354972%|1.328515|19|可登记|
|spike-a32|旧|72|11545422882|59.016393%|60.344828%|54.044553%|52.769930%|1.299623|10|可登记|
|spike-a32|裁决3+4修订2|72|11545422882|97.297297%|60.344828%|99.991339%|52.769930%|1.299623|10|可登记|
|ffmpeg-thumb|旧|6741|5543882572|51.694785%|52.822396%|19.269762%|16.273212%|21.290195|441|不可登记|
|ffmpeg-thumb|裁决3+4修订2|6679|5778242097|89.005864%|52.684718%|85.108247%|16.961138%|22.295678|457|可登记|
|ffmpeg-a32|旧|6764|5515981237|51.871166%|52.937127%|19.172781%|16.191312%|21.884973|441|不可登记|
|ffmpeg-a32|裁决3+4修订2|6698|5756536364|89.033630%|52.810922%|84.896746%|16.897425%|22.113109|455|可登记|

n_eff为null有显式分支，未作数值比较；本数据均非null。spike K=19/10<50，仍为仅描述。FFmpeg K=457/455。权重/U/排除分片及SHA见各*-static/index.json。③均≥80%；没有对象触发<50%停止门槛。完整旧/新字段在comparison-final.json；③′宏展开DA占比沿用本报告§7的“宏region行DA / macro-only DA / 覆盖总DA”原值表（C筛选不改变该分母），各对象macro行证据亦保持原SHA。

三个1%门槛：

|对象|原因|分子DA|分母ΣR(C)|比例|超过1%|
|---|---|---|---|---|---|
|spike-thumb|identity_ambiguous|0|11674422883|0.000000%|False|
|spike-thumb|unmatched_in_elf|0|11674422883|0.000000%|False|
|spike-thumb|boundary_unavailable|0|11674422883|0.000000%|False|
|spike-a32|identity_ambiguous|0|11546422883|0.000000%|False|
|spike-a32|unmatched_in_elf|0|11546422883|0.000000%|False|
|spike-a32|boundary_unavailable|0|11546422883|0.000000%|False|
|ffmpeg-thumb|identity_ambiguous|15555|6789285726|0.000229%|False|
|ffmpeg-thumb|unmatched_in_elf|26367|6789285726|0.000388%|False|
|ffmpeg-thumb|boundary_unavailable|0|6789285726|0.000000%|False|
|ffmpeg-a32|identity_ambiguous|15555|6780632541|0.000229%|False|
|ffmpeg-a32|unmatched_in_elf|26367|6780632541|0.000389%|False|
|ffmpeg-a32|boundary_unavailable|0|6780632541|0.000000%|False|

新歧义包见*-audit/ambiguity-groups、ambiguity-top20、ambiguity-top20-instances。按失败原因与partial/all统计，不按DA修复身份；每对象即使没有歧义也输出空表及0汇总。

### 10.6 互斥损失账本与S键在C外

新C到U的完整原因集合：

|对象|完整原因集合|行数|DA|
|---|---|---|---|
|spike-thumb|no_key_line|2|1000001|
|spike-a32|no_key_line|2|1000001|
|ffmpeg-thumb|identity_ambiguous + no_key_line + unmatched_in_elf|6|15555|
|ffmpeg-thumb|no_key_line|650|724950846|
|ffmpeg-thumb|no_key_line + reference_ambiguity|17|31940587|
|ffmpeg-thumb|no_key_line + unmatched_in_elf|3|10812|
|ffmpeg-thumb|reference_ambiguity|149|254125829|
|ffmpeg-a32|identity_ambiguous + no_key_line + unmatched_in_elf|6|15555|
|ffmpeg-a32|no_key_line|654|731523394|
|ffmpeg-a32|no_key_line + reference_ambiguity|18|38018090|
|ffmpeg-a32|no_key_line + unmatched_in_elf|3|10812|
|ffmpeg-a32|reference_ambiguity|144|254528326|

每对象均断言ΣR(C)−ΣR(U)−Σ桶DA=0；同时另有“旧C到新U”账本，增加code_free_line并保留每行其他原因，差值也为0。移出C的code_free_line不进入新C分母或1%门槛。账本在summary.json、old-C-exclusions、exclusions；不是将互相重叠的单原因DA相加。

S有键却不在新C的行全部排除，逐行保存在S-key-outside-C分片：

|对象|C外S键行|有参考的DA合计|无覆盖DA行|原在旧C行|原在旧C的DA|
|---|---|---|---|---|---|
|spike-thumb|0|0|0|0|0|
|spike-a32|0|0|0|0|0|
|ffmpeg-thumb|27635|100910681|26|133|100910671|
|ffmpeg-a32|27728|108791572|26|133|108791562|

没有覆盖参考的行DA写空值，不用0伪造；其中“原在旧C”子集直接证明U⊆新C筛选没有偷用S键反向扩张C。静态系统头/宏代码规模沿用全指令枚举统计，按新身份重核，见summary的static_special_code。

### 10.7 验收、资源、SHA与停止

原113项全部保留；本轮21项synthetic夹具，共134项通过（tests-rev2，真实退出0）。包括用户要求的9项、修订1其他文件叶子行、修订2非叶子0豁免/越界失败，以及混合文件叶子行不豁免等补充负例。

全部scope串行nice19/ionice-c3，MemoryMax=3G、CPUQuota=200%，启动门槛MemAvailable≥4GiB。最低MemAvailable=10107416576B，最高实读cgroup memory.peak=1675350016B；资源终止=False。一次取证来源断言失败原文保留并已修复，不是OOM。资源原文与每次带时间结束状态、生成命令见各*-run及resources-summary.json。

所有新增文件<1MB；manifest登记SHA及路径，大原始取证数据在temp并由命令记录登记SHA。旧v1.5正文、旧代码/证据、用户配置未改，无板上操作、无挂载、无认证变更、无正式sample profile读取，边界例外：无。

本任务到此停止。不登记修正案3，不进入仿真或其他N.5项目。待折入v1.6并经评审后再由用户决定后续。
