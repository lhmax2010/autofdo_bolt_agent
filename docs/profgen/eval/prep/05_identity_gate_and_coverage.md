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

## 11. 裁决3修订1：两构建行表并集与 code_free 描述（2026-11-11）
本节基于 cb2da1b；裁决原文已登记到 rulings.md，仍待折入 v1.6 并经三家评审。未读取正式 sample profile（含 CALIBRATION），未登记修正案3，未接板、未进入仿真或其他 N.5。

### 11.1 数据流、实现与可复核范围

三套表固定裁决4修订2的身份与键事实，只改变C域。“旧规则”在本节指v1.5原C域＋裁决4修订2，并非§10历史旧身份表；因此FFmpeg旧C的U与§10历史行不同，这是有意控制身份变量。C-only表的C/U/质量比、n_eff、K、损失桶、三个门槛均与cb2da1b逐字段相等（断言）。
ruling3_union.py只读覆盖参考、独立C/S DWARF行表与既有映射范围的顶层函数名清单。S证据要求非end_sequence、已解析文件、非零行号、地址属于选定函数区间（原始DIE链）；使用行表叶子文件/行，不读地址→键映射表或身份结论，不要求完整上下文接受。每个C成员保存C/S见证；域先独立封存，ruling3_union_static.py随后才复用cb2已验收的裁决4修订2静态键数据库和逐行原因。数据库只读，路径/SHA入索引，未打开任何RUN数据。
每个对象的domain/index.json保留输入SHA、实际生成命令、选择范围SHA与行表原文位置；static/{v15,ruling3,ruling3-rev1}/index.json登记U、排除、权重及摘要SHA。证据根目录：[ruling3-rev1](evidence/identity-gate/ruling3-rev1/)。旧代码/旧结果均未覆盖。
code_free_ast.py仅构建独立插件，使用GBS Clang公开API；clang本体不改不重编。用实际C构建命令保留优化、覆盖、预处理参数，仅去掉对象/依赖输出并加-fsyntax-only、插件参数。按已验证方法重定位源目录、sysroot与生成头；AST-config-provenance.json记录实际config.h/config.mak、avconfig.h及2270项config_components对应证据与SHA。spike每侧1个CU、FFmpeg每侧311个CU全部退出0，complete.errors=false。原始大JSONL仅在temp/prep-ruling3-rev1/*-AST，每条命令单独记录源SHA、原日志行、完整命令、原始输出SHA。
分类只按编译器SourceManager的spelling/expansion源码范围：先GCCAsmStmt，再含其他新C行的跨行Stmt/Expr，再other；无成功AST为ast_unavailable。范围冲突取最短范围，再按类型/TU排序，确定性输出。依条文字面，CompoundStmt也是Stmt，没有自行排除；故stmt_continuation不能一概解释为“实参续行”，下面单列CompoundStmt规模。无法形成同文件范围的跨文件端点不拼接、不猜测；它们的原始AST仍留存。

### 11.2 三套对象表

表内“可登记”只表示本表门槛通过，不代表裁决已评审或其余登记条件已完成。④body比例仍未计算。①②③③′的分子分母定义保持原实现；n_eff=null有显式分支，本数据无null；spike K<50仍仅描述。

|对象|C规则|C行|ΣR(C)|U行|ΣR(U)|①|②|③|③′|n_eff|K|状态|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|spike-thumb|旧C（身份固定）|122|21362787097|73|11673422882|59.836066%|61.206897%|54.643726%|53.354972%|1.328515|19|可登记|
|spike-thumb|裁决3原文|75|11674422883|73|11673422882|97.333333%|61.206897%|99.991434%|53.354972%|1.328515|19|可登记|
|spike-thumb|裁决3修订1|75|11674422883|73|11673422882|97.333333%|61.206897%|99.991434%|53.354972%|1.328515|19|可登记|
|spike-a32|旧C（身份固定）|122|21362787097|72|11545422882|59.016393%|60.344828%|54.044553%|52.769930%|1.299623|10|可登记|
|spike-a32|裁决3原文|74|11546422883|72|11545422882|97.297297%|60.344828%|99.991339%|52.769930%|1.299623|10|可登记|
|spike-a32|裁决3修订1|74|11546422883|72|11545422882|97.297297%|60.344828%|99.991339%|52.769930%|1.299623|10|可登记|
|ffmpeg-thumb|旧C（身份固定）|13040|28769855208|6810|5870786315|52.223926%|53.614043%|20.406034%|17.232788%|22.607016|465|不可登记：coverage_3_below_50_percent|
|ffmpeg-thumb|裁决3原文|7504|6789285726|6679|5778242097|89.005864%|52.684718%|85.108247%|16.961138%|22.295678|457|可登记|
|ffmpeg-thumb|裁决3修订1|7637|6890196397|6810|5870786315|89.171141%|53.614043%|85.204920%|17.232788%|22.607016|465|可登记|
|ffmpeg-a32|旧C（身份固定）|13040|28769855208|6828|5856961473|52.361963%|53.671409%|20.357980%|17.192207%|22.643693|464|不可登记：coverage_3_below_50_percent|
|ffmpeg-a32|裁决3原文|7523|6780632541|6698|5756536364|89.033630%|52.810922%|84.896746%|16.897425%|22.113109|455|可登记|
|ffmpeg-a32|裁决3修订1|7656|6889424103|6828|5856961473|89.184953%|53.671409%|85.013804%|17.192207%|22.643693|464|可登记|

三个1%门槛，分子/分母原值（同对象分母随C规则变化）：

|对象|C规则|原因|分子DA|分母ΣR(C)|比例|超1%|
|---|---|---|---|---|---|---|
|spike-thumb|旧C（身份固定）|identity_ambiguous|0|21362787097|0.000000%|False|
|spike-thumb|旧C（身份固定）|unmatched_in_elf|0|21362787097|0.000000%|False|
|spike-thumb|旧C（身份固定）|boundary_unavailable|0|21362787097|0.000000%|False|
|spike-thumb|裁决3原文|identity_ambiguous|0|11674422883|0.000000%|False|
|spike-thumb|裁决3原文|unmatched_in_elf|0|11674422883|0.000000%|False|
|spike-thumb|裁决3原文|boundary_unavailable|0|11674422883|0.000000%|False|
|spike-thumb|裁决3修订1|identity_ambiguous|0|11674422883|0.000000%|False|
|spike-thumb|裁决3修订1|unmatched_in_elf|0|11674422883|0.000000%|False|
|spike-thumb|裁决3修订1|boundary_unavailable|0|11674422883|0.000000%|False|
|spike-a32|旧C（身份固定）|identity_ambiguous|0|21362787097|0.000000%|False|
|spike-a32|旧C（身份固定）|unmatched_in_elf|0|21362787097|0.000000%|False|
|spike-a32|旧C（身份固定）|boundary_unavailable|0|21362787097|0.000000%|False|
|spike-a32|裁决3原文|identity_ambiguous|0|11546422883|0.000000%|False|
|spike-a32|裁决3原文|unmatched_in_elf|0|11546422883|0.000000%|False|
|spike-a32|裁决3原文|boundary_unavailable|0|11546422883|0.000000%|False|
|spike-a32|裁决3修订1|identity_ambiguous|0|11546422883|0.000000%|False|
|spike-a32|裁决3修订1|unmatched_in_elf|0|11546422883|0.000000%|False|
|spike-a32|裁决3修订1|boundary_unavailable|0|11546422883|0.000000%|False|
|ffmpeg-thumb|旧C（身份固定）|identity_ambiguous|21849|28769855208|0.000076%|False|
|ffmpeg-thumb|旧C（身份固定）|unmatched_in_elf|10096086|28769855208|0.035093%|False|
|ffmpeg-thumb|旧C（身份固定）|boundary_unavailable|0|28769855208|0.000000%|False|
|ffmpeg-thumb|裁决3原文|identity_ambiguous|15555|6789285726|0.000229%|False|
|ffmpeg-thumb|裁决3原文|unmatched_in_elf|26367|6789285726|0.000388%|False|
|ffmpeg-thumb|裁决3原文|boundary_unavailable|0|6789285726|0.000000%|False|
|ffmpeg-thumb|裁决3修订1|identity_ambiguous|15555|6890196397|0.000226%|False|
|ffmpeg-thumb|裁决3修订1|unmatched_in_elf|26367|6890196397|0.000383%|False|
|ffmpeg-thumb|裁决3修订1|boundary_unavailable|0|6890196397|0.000000%|False|
|ffmpeg-a32|旧C（身份固定）|identity_ambiguous|21849|28769855208|0.000076%|False|
|ffmpeg-a32|旧C（身份固定）|unmatched_in_elf|10096086|28769855208|0.035093%|False|
|ffmpeg-a32|旧C（身份固定）|boundary_unavailable|0|28769855208|0.000000%|False|
|ffmpeg-a32|裁决3原文|identity_ambiguous|15555|6780632541|0.000229%|False|
|ffmpeg-a32|裁决3原文|unmatched_in_elf|26367|6780632541|0.000389%|False|
|ffmpeg-a32|裁决3原文|boundary_unavailable|0|6780632541|0.000000%|False|
|ffmpeg-a32|裁决3修订1|identity_ambiguous|15555|6889424103|0.000226%|False|
|ffmpeg-a32|裁决3修订1|unmatched_in_elf|26367|6889424103|0.000383%|False|
|ffmpeg-a32|裁决3修订1|boundary_unavailable|0|6889424103|0.000000%|False|


### 11.3 代码承载比例、S新增行与域外键


|对象|新ΣR(C)|原ΣR(C)|代码承载比例|因(b)新增行/DA|进入U行/DA|仍损失行/DA|
|---|---|---|---|---|---|---|
|spike-thumb|11674422883|21362787097|54.648407%|0/0|0/0|0/0|
|spike-a32|11546422883|21362787097|54.049234%|0/0|0/0|0/0|
|ffmpeg-thumb|6890196397|28769855208|23.949361%|133/100910671|131/92544218|2/8366453|
|ffmpeg-a32|6889424103|28769855208|23.946676%|133/108791562|130/100425109|3/8366453|

新增行逐行见*-static/added-by-S-*.csv，保留in_U与完整loss_reasons。Thumb两行、A32三行仍为损失，DA均8366453，不能因S行表存在便记入U：

|对象|文件|行|DA|原因|
|---|---|---|---|---|
|ffmpeg-thumb|libavcodec/h264_mb_template.c|94|6480000|["reference_ambiguity"]|
|ffmpeg-thumb|libavcodec/h264_mb_template.c|234|1886453|["reference_ambiguity"]|
|ffmpeg-a32|libavcodec/h264_mb_template.c|68|0|["reference_ambiguity"]|
|ffmpeg-a32|libavcodec/h264_mb_template.c|94|6480000|["reference_ambiguity"]|
|ffmpeg-a32|libavcodec/h264_mb_template.c|234|1886453|["reference_ambiguity"]|


|对象|所有S键域外行|已知DA|原C内域外行|原C内域外DA|无参考DA行|
|---|---|---|---|---|---|
|spike-thumb|0|0|0|0|0|
|spike-a32|0|0|0|0|0|
|ffmpeg-thumb|27502|10|0|0|26|
|ffmpeg-a32|27595|10|0|0|26|

修订针对的“满足原C条件但被行表筛走”子集四侧均DA=0，已断言。若字面统计全部S键，FFmpeg两侧仍各有10 DA在原C之外：bytestream.h:94=1、96=1、99=8。逐行参考owner查询均为空（无任何参考函数主文件行范围覆盖），不是因两边行表缺失被筛走；不符合v1.5原C条件，不能为使总量为0而扩大C。全量逐行明细及原因见S-keys-outside-C分片；无覆盖DA的行写空值，不伪造0。

### 11.4 code_free结构描述（不用于门槛）


|对象|类别|行数|DA|占原ΣR(C)|
|---|---|---|---|---|
|spike-thumb|stmt_continuation|47|9688364214|45.351593%|
|spike-thumb|asm_interior|0|0|0.000000%|
|spike-thumb|other|0|0|0.000000%|
|spike-thumb|ast_unavailable|0|0|0.000000%|
|spike-a32|stmt_continuation|48|9816364214|45.950766%|
|spike-a32|asm_interior|0|0|0.000000%|
|spike-a32|other|0|0|0.000000%|
|spike-a32|ast_unavailable|0|0|0.000000%|
|ffmpeg-thumb|stmt_continuation|5294|7828843778|27.211968%|
|ffmpeg-thumb|asm_interior|68|14050578484|48.837849%|
|ffmpeg-thumb|other|41|236549|0.000822%|
|ffmpeg-thumb|ast_unavailable|0|0|0.000000%|
|ffmpeg-a32|stmt_continuation|5275|7829616072|27.214652%|
|ffmpeg-a32|asm_interior|68|14050578484|48.837849%|
|ffmpeg-a32|other|41|236549|0.000822%|
|ffmpeg-a32|ast_unavailable|0|0|0.000000%|

所有code_free行逐行归入且只归入一个类别；分类行数/DA之和等于原C减并集C，断言通过。CompoundStmt见证的stmt_continuation规模：

|对象|行数|DA|
|---|---|---|
|spike-thumb|46|9688364213|
|spike-a32|47|9816364213|
|ffmpeg-thumb|4274|6959873067|
|ffmpeg-a32|4251|6960082326|

各类DA最高10行（不足10行全列；0行类别无条目）。完整raw AST行号/命令/SHA在*-code-free-classification/summary.json与lines分片中；下面为可读摘要。
**spike-thumb**


|类别|文件|行|DA|Stmt类型|范围|view|
|---|---|---|---|---|---|---|
|stmt_continuation|eval-spike-1.0/spike.c|69|4063610861|CompoundStmt|67–70|spelling|
|stmt_continuation|eval-spike-1.0/spike.c|70|4063610861|CompoundStmt|67–70|spelling|
|stmt_continuation|eval-spike-1.0/spike.c|38|137029154|CompoundStmt|38–40|spelling|
|stmt_continuation|eval-spike-1.0/spike.c|40|137029154|CompoundStmt|38–40|spelling|
|stmt_continuation|eval-spike-1.0/spike.c|28|128004096|CompoundStmt|28–35|spelling|
|stmt_continuation|eval-spike-1.0/spike.c|29|128004096|CompoundStmt|28–35|spelling|
|stmt_continuation|eval-spike-1.0/spike.c|33|128004096|CompoundStmt|28–35|spelling|
|stmt_continuation|eval-spike-1.0/spike.c|35|128004096|CompoundStmt|28–35|spelling|
|stmt_continuation|eval-spike-1.0/spike.c|90|128000000|CompoundStmt|79–90|spelling|
|stmt_continuation|eval-spike-1.0/spike.c|112|128000000|CompoundStmt|110–112|spelling|

**spike-a32**


|类别|文件|行|DA|Stmt类型|范围|view|
|---|---|---|---|---|---|---|
|stmt_continuation|eval-spike-1.0/spike.c|69|4063610861|CompoundStmt|67–70|spelling|
|stmt_continuation|eval-spike-1.0/spike.c|70|4063610861|CompoundStmt|67–70|spelling|
|stmt_continuation|eval-spike-1.0/spike.c|38|137029154|CompoundStmt|38–40|spelling|
|stmt_continuation|eval-spike-1.0/spike.c|40|137029154|CompoundStmt|38–40|spelling|
|stmt_continuation|eval-spike-1.0/spike.c|28|128004096|CompoundStmt|28–35|spelling|
|stmt_continuation|eval-spike-1.0/spike.c|29|128004096|CompoundStmt|28–35|spelling|
|stmt_continuation|eval-spike-1.0/spike.c|33|128004096|CompoundStmt|28–35|spelling|
|stmt_continuation|eval-spike-1.0/spike.c|35|128004096|CompoundStmt|28–35|spelling|
|stmt_continuation|eval-spike-1.0/spike.c|82|128000000|CompoundStmt|79–90|spelling|
|stmt_continuation|eval-spike-1.0/spike.c|90|128000000|CompoundStmt|79–90|spelling|

**ffmpeg-thumb**


|类别|文件|行|DA|Stmt类型|范围|view|
|---|---|---|---|---|---|---|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/arm/cabac.h|32|255523038|CompoundStmt|32–105|spelling|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/arm/cabac.h|33|255523038|CompoundStmt|32–105|spelling|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/arm/cabac.h|34|255523038|CompoundStmt|32–105|spelling|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/arm/cabac.h|105|255523038|CompoundStmt|32–105|spelling|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/cabac_functions.h|146|215694437|CompoundStmt|144–146|spelling|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1649|201269902|CompoundStmt|1596–1776|spelling|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1670|85349935|BinaryOperator|1670–1696|spelling|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1671|84904984|BinaryOperator|1671–1696|spelling|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1672|84904984|BinaryOperator|1671–1696|spelling|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1680|84904984|BinaryOperator|1673–1696|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|37|255523038|GCCAsmStmt|36–102|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|38|255523038|GCCAsmStmt|36–102|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|39|255523038|GCCAsmStmt|36–102|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|40|255523038|GCCAsmStmt|36–102|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|41|255523038|GCCAsmStmt|36–102|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|42|255523038|GCCAsmStmt|36–102|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|43|255523038|GCCAsmStmt|36–102|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|44|255523038|GCCAsmStmt|36–102|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|45|255523038|GCCAsmStmt|36–102|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|46|255523038|GCCAsmStmt|36–102|spelling|
|other|ffmpeg-8.0.1/libavcodec/codec_internal.h|285|19950|CompoundStmt|285–287|spelling|
|other|ffmpeg-8.0.1/libavcodec/codec_internal.h|286|19950|DeclRefExpr|286–286|spelling|
|other|ffmpeg-8.0.1/libavcodec/codec_internal.h|287|19950|CompoundStmt|285–287|spelling|
|other|ffmpeg-8.0.1/libavcodec/decode.c|103|19820|CompoundStmt|103–105|spelling|
|other|ffmpeg-8.0.1/libavcodec/decode.c|104|19820|DeclRefExpr|104–104|spelling|
|other|ffmpeg-8.0.1/libavcodec/decode.c|105|19820|CompoundStmt|103–105|spelling|
|other|ffmpeg-8.0.1/libavutil/rational.h|72|14423|CompoundStmt|72–75|spelling|
|other|ffmpeg-8.0.1/libavutil/rational.h|73|14423|DeclRefExpr|73–73|spelling|
|other|ffmpeg-8.0.1/libavutil/rational.h|74|14423|DeclRefExpr|74–74|spelling|
|other|ffmpeg-8.0.1/libavutil/rational.h|75|14423|CompoundStmt|72–75|spelling|

**ffmpeg-a32**


|类别|文件|行|DA|Stmt类型|范围|view|
|---|---|---|---|---|---|---|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/arm/cabac.h|32|255523038|CompoundStmt|32–105|spelling|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/arm/cabac.h|33|255523038|CompoundStmt|32–105|spelling|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/arm/cabac.h|34|255523038|CompoundStmt|32–105|spelling|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/arm/cabac.h|105|255523038|CompoundStmt|32–105|spelling|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/cabac_functions.h|146|215694437|CompoundStmt|144–146|spelling|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1649|201269902|CompoundStmt|1596–1776|spelling|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1670|85349935|BinaryOperator|1670–1696|spelling|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1671|84904984|BinaryOperator|1671–1696|spelling|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1672|84904984|BinaryOperator|1671–1696|spelling|
|stmt_continuation|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1680|84904984|BinaryOperator|1673–1696|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|37|255523038|GCCAsmStmt|36–102|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|38|255523038|GCCAsmStmt|36–102|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|39|255523038|GCCAsmStmt|36–102|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|40|255523038|GCCAsmStmt|36–102|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|41|255523038|GCCAsmStmt|36–102|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|42|255523038|GCCAsmStmt|36–102|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|43|255523038|GCCAsmStmt|36–102|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|44|255523038|GCCAsmStmt|36–102|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|45|255523038|GCCAsmStmt|36–102|spelling|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|46|255523038|GCCAsmStmt|36–102|spelling|
|other|ffmpeg-8.0.1/libavcodec/codec_internal.h|285|19950|CompoundStmt|285–287|spelling|
|other|ffmpeg-8.0.1/libavcodec/codec_internal.h|286|19950|DeclRefExpr|286–286|spelling|
|other|ffmpeg-8.0.1/libavcodec/codec_internal.h|287|19950|CompoundStmt|285–287|spelling|
|other|ffmpeg-8.0.1/libavcodec/decode.c|103|19820|CompoundStmt|103–105|spelling|
|other|ffmpeg-8.0.1/libavcodec/decode.c|104|19820|DeclRefExpr|104–104|spelling|
|other|ffmpeg-8.0.1/libavcodec/decode.c|105|19820|CompoundStmt|103–105|spelling|
|other|ffmpeg-8.0.1/libavutil/rational.h|72|14423|CompoundStmt|72–75|spelling|
|other|ffmpeg-8.0.1/libavutil/rational.h|73|14423|DeclRefExpr|73–73|spelling|
|other|ffmpeg-8.0.1/libavutil/rational.h|74|14423|DeclRefExpr|74–74|spelling|
|other|ffmpeg-8.0.1/libavutil/rational.h|75|14423|CompoundStmt|72–75|spelling|


### 11.5 完整互斥损失账本

下表为三套C→U完整原因集合。另一个原C→该套U账本在每套summary.old_C_to_new_U_loss及old-C-exclusions分片中：被移出域的行增加code_free_line并保留其余完整原因，不重复计数。共12个C→U与12个原C→U差值均断言为0。

|对象|C规则|完整原因集合|行数|DA|
|---|---|---|---|---|
|spike-thumb|旧C（身份固定）|no_key_line|49|9689364215|
|spike-thumb|裁决3原文|no_key_line|2|1000001|
|spike-thumb|裁决3修订1|no_key_line|2|1000001|
|spike-a32|旧C（身份固定）|no_key_line|50|9817364215|
|spike-a32|裁决3原文|no_key_line|2|1000001|
|spike-a32|裁决3修订1|no_key_line|2|1000001|
|ffmpeg-thumb|旧C（身份固定）|identity_ambiguous + no_key_line + reference_ambiguity + unmatched_in_elf|10|36|
|ffmpeg-thumb|旧C（身份固定）|identity_ambiguous + no_key_line + unmatched_in_elf|17|21813|
|ffmpeg-thumb|旧C（身份固定）|no_key_line|5873|22390280990|
|ffmpeg-thumb|旧C（身份固定）|no_key_line + reference_ambiguity|142|236199535|
|ffmpeg-thumb|旧C（身份固定）|no_key_line + unmatched_in_elf|37|10074237|
|ffmpeg-thumb|旧C（身份固定）|reference_ambiguity|151|262492282|
|ffmpeg-thumb|裁决3原文|identity_ambiguous + no_key_line + unmatched_in_elf|6|15555|
|ffmpeg-thumb|裁决3原文|no_key_line|650|724950846|
|ffmpeg-thumb|裁决3原文|no_key_line + reference_ambiguity|17|31940587|
|ffmpeg-thumb|裁决3原文|no_key_line + unmatched_in_elf|3|10812|
|ffmpeg-thumb|裁决3原文|reference_ambiguity|149|254125829|
|ffmpeg-thumb|裁决3修订1|identity_ambiguous + no_key_line + unmatched_in_elf|6|15555|
|ffmpeg-thumb|裁决3修订1|no_key_line|650|724950846|
|ffmpeg-thumb|裁决3修订1|no_key_line + reference_ambiguity|17|31940587|
|ffmpeg-thumb|裁决3修订1|no_key_line + unmatched_in_elf|3|10812|
|ffmpeg-thumb|裁决3修订1|reference_ambiguity|151|262492282|
|ffmpeg-a32|旧C（身份固定）|identity_ambiguous + no_key_line + reference_ambiguity + unmatched_in_elf|10|36|
|ffmpeg-a32|旧C（身份固定）|identity_ambiguous + no_key_line + unmatched_in_elf|17|21813|
|ffmpeg-a32|旧C（身份固定）|no_key_line|5855|22404105832|
|ffmpeg-a32|旧C（身份固定）|no_key_line + reference_ambiguity|146|235797038|
|ffmpeg-a32|旧C（身份固定）|no_key_line + unmatched_in_elf|37|10074237|
|ffmpeg-a32|旧C（身份固定）|reference_ambiguity|147|262894779|
|ffmpeg-a32|裁决3原文|identity_ambiguous + no_key_line + unmatched_in_elf|6|15555|
|ffmpeg-a32|裁决3原文|no_key_line|654|731523394|
|ffmpeg-a32|裁决3原文|no_key_line + reference_ambiguity|18|38018090|
|ffmpeg-a32|裁决3原文|no_key_line + unmatched_in_elf|3|10812|
|ffmpeg-a32|裁决3原文|reference_ambiguity|144|254528326|
|ffmpeg-a32|裁决3修订1|identity_ambiguous + no_key_line + unmatched_in_elf|6|15555|
|ffmpeg-a32|裁决3修订1|no_key_line|654|731523394|
|ffmpeg-a32|裁决3修订1|no_key_line + reference_ambiguity|18|38018090|
|ffmpeg-a32|裁决3修订1|no_key_line + unmatched_in_elf|3|10812|
|ffmpeg-a32|裁决3修订1|reference_ambiguity|147|262894779|

新并集C的原C→新U账本（包括code_free）：

|对象|完整原因集合|行数|DA|
|---|---|---|---|
|spike-thumb|code_free_line + no_key_line|47|9688364214|
|spike-thumb|no_key_line|2|1000001|
|spike-a32|code_free_line + no_key_line|48|9816364214|
|spike-a32|no_key_line|2|1000001|
|ffmpeg-thumb|code_free_line + identity_ambiguous + no_key_line + reference_ambiguity + unmatched_in_elf|10|36|
|ffmpeg-thumb|code_free_line + identity_ambiguous + no_key_line + unmatched_in_elf|11|6258|
|ffmpeg-thumb|code_free_line + no_key_line|5223|21665330144|
|ffmpeg-thumb|code_free_line + no_key_line + reference_ambiguity|125|204258948|
|ffmpeg-thumb|code_free_line + no_key_line + unmatched_in_elf|34|10063425|
|ffmpeg-thumb|identity_ambiguous + no_key_line + unmatched_in_elf|6|15555|
|ffmpeg-thumb|no_key_line|650|724950846|
|ffmpeg-thumb|no_key_line + reference_ambiguity|17|31940587|
|ffmpeg-thumb|no_key_line + unmatched_in_elf|3|10812|
|ffmpeg-thumb|reference_ambiguity|151|262492282|
|ffmpeg-a32|code_free_line + identity_ambiguous + no_key_line + reference_ambiguity + unmatched_in_elf|10|36|
|ffmpeg-a32|code_free_line + identity_ambiguous + no_key_line + unmatched_in_elf|11|6258|
|ffmpeg-a32|code_free_line + no_key_line|5201|21672582438|
|ffmpeg-a32|code_free_line + no_key_line + reference_ambiguity|128|197778948|
|ffmpeg-a32|code_free_line + no_key_line + unmatched_in_elf|34|10063425|
|ffmpeg-a32|identity_ambiguous + no_key_line + unmatched_in_elf|6|15555|
|ffmpeg-a32|no_key_line|654|731523394|
|ffmpeg-a32|no_key_line + reference_ambiguity|18|38018090|
|ffmpeg-a32|no_key_line + unmatched_in_elf|3|10812|
|ffmpeg-a32|reference_ambiguity|147|262894779|


### 11.6 测试、失败记录、资源与停止

原134项测试文件未修改、全部保留；新增10项synthetic，共144项通过。前7项逐项覆盖用户要求；另加AST不可得不归other、macro-only原域外不准入、范围内没有其他C行不归continuation。真实AST624条编译命令均成功；C-only重现及所有账本/域外DA断言通过。
保留3次开发失败：AST-plugin-build-run的显式JSON构造编译错误；spike-thumb-AST-run在插件未成功时缺少so；spike-thumb-AST-v2-run把collect当对象名的CLI错误。修正后独立插件构建成功、调用前检查so存在，真实取证均通过。它们不是OOM，未采纳失败输出。
串行nice19/ionice-c3、systemd scope MemoryMax=3G/CPUQuota=200%；每次分析启动前检查≥4GiB。最低实测MemAvailable=6861107200B；最高实读cgroup memory.peak=614322176B；资源终止=False。原始meminfo、scope、真实退出码、ALL-END和resources-summary.json保留。未提高限额、未并行运行分析。系统scope自身记账属系统服务行为；未观察到项目在WORKDIR外产生文件。
四对象新表③均≥80%，三个1%门槛均未超限；仅本表门槛可登记。裁决待折入v1.6并经三家评审。按要求完成后停止：不登记修正案3，不进入仿真/其他N.5，不计算④body比例或任何正式sample profile受控量。

## 12. code_free 描述性分类 v2（2026-11-11；完成后停止）

基于4459894，只重做描述分类；旧分类与C、U、权重、三个1%门槛及登记状态不变。1048个旧证据文件全部SHA逐项一致。未读取任何正式sample profile/CALIBRATION，未登记修正案3，未接板。证据根目录：[code-free-v2](evidence/identity-gate/code-free-v2/)。

### 12.1 补采授权、命令与一致性

旧插件只保存Stmt/Expr，缺少Decl、运算符、初始化和标号冒号事实，因此先停下确认。PM明确授权沿用原C命令补采独立插件字段，并要求旧节点集合完全一致；本轮按此执行，不改/不重编clang本体、不挂载。完整授权及缺失字段见authorization.md与pending.json（历史停止点，现已闭合）。

新插件保留旧Stmt/Expr遍历及去重顺序，额外记录Decl（含DeclStmt各Decl、DeclContext子节点）、VarDecl初始化、Binary/CompoundAssign运算符及语句类名。case/default冒号取Clang AST API，普通标号冒号由Clang Lexer::findNextToken取得并确认tok::colon。旧Stmt/Expr的完整字段投影按多重集合比较：类型、spelling/expansion视图、起止raw/offset/line、文件及macro标志全部逐条一致。

完整原C命令及实际取证命令逐条保存；原编译参数、cwd、源SHA、sysroot、生成头/config及目标行清单SHA不变。命令字面仅替换两个产物路径：旧插件.so→新插件.so、旧JSONL→temp/prep-code-free-v2的新JSONL，避免覆盖旧产物；不把这两项隐藏成整串字节相同。两侧FFmpeg各311 CU、spike各1 CU，真实退出码与上轮均为0，complete.errors=false。

|对象|命令数|旧/新Stmt-Expr记录数|新增Decl范围|差异数|
|---|---|---|---|---|
|spike-thumb|1|96|25|0|
|spike-a32|1|104|26|0|
|ffmpeg-thumb|311|63900|7776|0|
|ffmpeg-a32|311|63970|7779|0|

72个物理源文件由GBS Clang公开Lexer API从文件起点raw lex，保留跨行token状态，忽略注释/空白；标识符经Clang IdentifierTable取得关键字kind。原始tokens JSONL为temp/prep-code-free-v2/raw-tokens.jsonl（路径/SHA/源码SHA见lexer-command.json），AST大JSONL也只留该temp目录。Lex使用C17/GNU C；FFmpeg原命令为-std=c17，spike为该clang默认GNU C。仓库仅存小分片与索引。

### 12.2 分类算法与未决描述

优先级固定为asm→structural→expr_continuation→own_stmt_no_code→other；取不到AST或lex证据单列ast_unavailable。structural按该行全部raw token检查，只接受{、}、;、else、do以及编译器确认的标号范围；空白/注释-only单列结构子类。未从文件名或源文本推测语义。

expr_continuation要求本行没有任何非CompoundStmt节点起始，候选起始行在新C中，并排除CompoundStmt与if/for/while/switch/do整体范围；取最内层合格范围。own_stmt按本行起始的非CompoundStmt节点判定，汇总种类选择起点最早、覆盖最外层的节点，固定排序去除TU遍历顺序影响；同时保存全部起始节点类型。语句细类来自AST（赋值运算、调用、return、声明初始化等），不把词法等号当作AST赋值证据。

每侧有2行（cabac.c:167，DA=1800；h264idct_template.c:283，DA=38861）仅能找到整段FunctionDecl容器。无法证明该行属于普通声明部分而非函数体，因此不猜成expr_continuation，列other，原因only_FunctionDecl_range_declarator_vs_body_eligibility_unavailable。其他other逐行记录no_node_start_and_no_eligible_range_starting_in_C及可得AST上下文。AST不可得为0，但并不把other解释成全部已证实优化消除。

### 12.3 四对象分类汇总与两种分母

|对象|类别|行数|DA分子|原ΣR(C)|占原C|新ΣR(C)|占新C|
|---|---|---|---|---|---|---|---|
|spike-thumb|asm_interior|0|0|21362787097|0.000000%|11674422883|0.000000%|
|spike-thumb|structural_line|28|5238745153|21362787097|24.522761%|11674422883|44.873697%|
|spike-thumb|expr_continuation|0|0|21362787097|0.000000%|11674422883|0.000000%|
|spike-thumb|own_stmt_no_code|19|4449619061|21362787097|20.828832%|11674422883|38.114253%|
|spike-thumb|other|0|0|21362787097|0.000000%|11674422883|0.000000%|
|spike-thumb|ast_unavailable|0|0|21362787097|0.000000%|11674422883|0.000000%|
|spike-a32|asm_interior|0|0|21362787097|0.000000%|11546422883|0.000000%|
|spike-a32|structural_line|28|5238745153|21362787097|24.522761%|11546422883|45.371153%|
|spike-a32|expr_continuation|0|0|21362787097|0.000000%|11546422883|0.000000%|
|spike-a32|own_stmt_no_code|20|4577619061|21362787097|21.428005%|11546422883|39.645344%|
|spike-a32|other|0|0|21362787097|0.000000%|11546422883|0.000000%|
|spike-a32|ast_unavailable|0|0|21362787097|0.000000%|11546422883|0.000000%|
|ffmpeg-thumb|asm_interior|68|14050578484|28769855208|48.837849%|6890196397|203.921306%|
|ffmpeg-thumb|structural_line|2105|2967361906|28769855208|10.314136%|6890196397|43.066434%|
|ffmpeg-thumb|expr_continuation|25|1799|28769855208|0.000006%|6890196397|0.000026%|
|ffmpeg-thumb|own_stmt_no_code|3056|4668195093|28769855208|16.225994%|6890196397|67.751263%|
|ffmpeg-thumb|other|149|193521529|28769855208|0.672654%|6890196397|2.808650%|
|ffmpeg-thumb|ast_unavailable|0|0|28769855208|0.000000%|6890196397|0.000000%|
|ffmpeg-a32|asm_interior|68|14050578484|28769855208|48.837849%|6889424103|203.944165%|
|ffmpeg-a32|structural_line|2100|2977361898|28769855208|10.348894%|6889424103|43.216412%|
|ffmpeg-a32|expr_continuation|25|1799|28769855208|0.000006%|6889424103|0.000026%|
|ffmpeg-a32|own_stmt_no_code|3042|4658967395|28769855208|16.193920%|6889424103|67.624918%|
|ffmpeg-a32|other|149|193521529|28769855208|0.672654%|6889424103|2.808965%|
|ffmpeg-a32|ast_unavailable|0|0|28769855208|0.000000%|6889424103|0.000000%|

各类均为描述，不设门槛；分类总DA是被排除部分，因此占新C的比例允许超过100%，不是新C的组成比例。

### 12.4 structural_line token细类

|对象|结构token种类集合|行数|DA|
|---|---|---|---|
|spike-thumb|else+l_brace+r_brace|1|999023|
|spike-thumb|l_brace|4|266033251|
|spike-thumb|r_brace|23|4971712879|
|spike-a32|else+l_brace+r_brace|1|999023|
|spike-a32|l_brace|4|266033251|
|spike-a32|r_brace|23|4971712879|
|ffmpeg-thumb|blank_or_comment_only|13|90175272|
|ffmpeg-thumb|do+l_brace|3|33561179|
|ffmpeg-thumb|else|58|32549782|
|ffmpeg-thumb|else+l_brace|7|9256741|
|ffmpeg-thumb|else+l_brace+r_brace|197|355532176|
|ffmpeg-thumb|else+r_brace|35|12252810|
|ffmpeg-thumb|l_brace|154|577689901|
|ffmpeg-thumb|l_brace+label|6|1352|
|ffmpeg-thumb|label|242|1960229|
|ffmpeg-thumb|r_brace|1375|1771258151|
|ffmpeg-thumb|r_brace+semi|15|83124313|
|ffmpeg-a32|blank_or_comment_only|13|90175272|
|ffmpeg-a32|do+l_brace|3|33561179|
|ffmpeg-a32|else|58|32549782|
|ffmpeg-a32|else+l_brace|7|9256741|
|ffmpeg-a32|else+l_brace+r_brace|192|363149473|
|ffmpeg-a32|else+r_brace|35|12252810|
|ffmpeg-a32|l_brace|154|577689901|
|ffmpeg-a32|l_brace+label|6|1352|
|ffmpeg-a32|label|242|1960229|
|ffmpeg-a32|r_brace|1375|1773640846|
|ffmpeg-a32|r_brace+semi|15|83124313|

label的具体case/default/普通标号以及所有原始token在逐行CSV中；表中按结构token集合互斥汇总。blank_or_comment_only是忽略注释空白后的空集合。

### 12.5 own_stmt_no_code语句种类

|对象|AST语句种类|行数|DA|
|---|---|---|---|
|spike-thumb|DeclRefExpr|1|1|
|spike-thumb|UnaryOperator|1|4063610861|
|spike-thumb|assignment|1|128004096|
|spike-thumb|declaration_with_initializer|6|257004098|
|spike-thumb|declaration_without_initializer|3|3|
|spike-thumb|function_call|1|1|
|spike-thumb|return|6|1000001|
|spike-a32|DeclRefExpr|1|1|
|spike-a32|UnaryOperator|1|4063610861|
|spike-a32|assignment|1|128004096|
|spike-a32|declaration_with_initializer|7|385004098|
|spike-a32|declaration_without_initializer|3|3|
|spike-a32|function_call|1|1|
|spike-a32|return|6|1000001|
|ffmpeg-thumb|ArraySubscriptExpr|122|1114130|
|ffmpeg-thumb|BinaryOperator|70|58618768|
|ffmpeg-thumb|BreakStmt|98|12230745|
|ffmpeg-thumb|CStyleCastExpr|63|274996719|
|ffmpeg-thumb|ConditionalOperator|1|0|
|ffmpeg-thumb|ContinueStmt|34|11283590|
|ffmpeg-thumb|DeclRefExpr|97|102307406|
|ffmpeg-thumb|DoStmt|29|33388885|
|ffmpeg-thumb|ForStmt|80|199757035|
|ffmpeg-thumb|FunctionDecl|9|94987739|
|ffmpeg-thumb|GotoStmt|84|618778|
|ffmpeg-thumb|IfStmt|164|555002171|
|ffmpeg-thumb|ImplicitCastExpr|108|115138141|
|ffmpeg-thumb|InitListExpr|27|163213424|
|ffmpeg-thumb|IntegerLiteral|27|11347734|
|ffmpeg-thumb|MemberExpr|34|1063|
|ffmpeg-thumb|ParenExpr|11|20145619|
|ffmpeg-thumb|UnaryExprOrTypeTraitExpr|13|5|
|ffmpeg-thumb|UnaryOperator|36|239538229|
|ffmpeg-thumb|WhileStmt|7|17923586|
|ffmpeg-thumb|assignment|566|458930553|
|ffmpeg-thumb|declaration_with_initializer|354|1057123850|
|ffmpeg-thumb|declaration_without_initializer|375|1016200791|
|ffmpeg-thumb|function_call|226|146115141|
|ffmpeg-thumb|return|421|78210991|
|ffmpeg-a32|ArraySubscriptExpr|121|1044167|
|ffmpeg-a32|BinaryOperator|70|58881829|
|ffmpeg-a32|BreakStmt|95|12230745|
|ffmpeg-a32|CStyleCastExpr|63|274996719|
|ffmpeg-a32|ConditionalOperator|1|0|
|ffmpeg-a32|ContinueStmt|33|11283590|
|ffmpeg-a32|DeclRefExpr|97|102307406|
|ffmpeg-a32|DoStmt|29|33388885|
|ffmpeg-a32|ForStmt|83|201776305|
|ffmpeg-a32|FunctionDecl|9|94987739|
|ffmpeg-a32|GotoStmt|84|618778|
|ffmpeg-a32|IfStmt|162|554793292|
|ffmpeg-a32|ImplicitCastExpr|111|115138141|
|ffmpeg-a32|InitListExpr|27|163213424|
|ffmpeg-a32|IntegerLiteral|27|11347734|
|ffmpeg-a32|MemberExpr|34|1063|
|ffmpeg-a32|ParenExpr|11|20145619|
|ffmpeg-a32|UnaryExprOrTypeTraitExpr|13|5|
|ffmpeg-a32|UnaryOperator|36|239538229|
|ffmpeg-a32|WhileStmt|7|17923586|
|ffmpeg-a32|assignment|540|441445128|
|ffmpeg-a32|declaration_with_initializer|355|1056941438|
|ffmpeg-a32|declaration_without_initializer|375|1016200791|
|ffmpeg-a32|function_call|238|151329288|
|ffmpeg-a32|return|421|79433494|

### 12.6 新旧分类交叉表

**spike-thumb：行数**

|旧类→新类|asm_interior|structural_line|expr_continuation|own_stmt_no_code|other|ast_unavailable|
|---|---|---|---|---|---|---|
|asm_interior|0|0|0|0|0|0|
|stmt_continuation|0|28|0|19|0|0|
|other|0|0|0|0|0|0|
|ast_unavailable|0|0|0|0|0|0|

**spike-thumb：DA**

|旧类→新类|asm_interior|structural_line|expr_continuation|own_stmt_no_code|other|ast_unavailable|
|---|---|---|---|---|---|---|
|asm_interior|0|0|0|0|0|0|
|stmt_continuation|0|5238745153|0|4449619061|0|0|
|other|0|0|0|0|0|0|
|ast_unavailable|0|0|0|0|0|0|

**spike-a32：行数**

|旧类→新类|asm_interior|structural_line|expr_continuation|own_stmt_no_code|other|ast_unavailable|
|---|---|---|---|---|---|---|
|asm_interior|0|0|0|0|0|0|
|stmt_continuation|0|28|0|20|0|0|
|other|0|0|0|0|0|0|
|ast_unavailable|0|0|0|0|0|0|

**spike-a32：DA**

|旧类→新类|asm_interior|structural_line|expr_continuation|own_stmt_no_code|other|ast_unavailable|
|---|---|---|---|---|---|---|
|asm_interior|0|0|0|0|0|0|
|stmt_continuation|0|5238745153|0|4577619061|0|0|
|other|0|0|0|0|0|0|
|ast_unavailable|0|0|0|0|0|0|

**ffmpeg-thumb：行数**

|旧类→新类|asm_interior|structural_line|expr_continuation|own_stmt_no_code|other|ast_unavailable|
|---|---|---|---|---|---|---|
|asm_interior|68|0|0|0|0|0|
|stmt_continuation|0|2086|25|3034|149|0|
|other|0|19|0|22|0|0|
|ast_unavailable|0|0|0|0|0|0|

**ffmpeg-thumb：DA**

|旧类→新类|asm_interior|structural_line|expr_continuation|own_stmt_no_code|other|ast_unavailable|
|---|---|---|---|---|---|---|
|asm_interior|14050578484|0|0|0|0|0|
|stmt_continuation|0|2967213852|1799|4668106598|193521529|0|
|other|0|148054|0|88495|0|0|
|ast_unavailable|0|0|0|0|0|0|

**ffmpeg-a32：行数**

|旧类→新类|asm_interior|structural_line|expr_continuation|own_stmt_no_code|other|ast_unavailable|
|---|---|---|---|---|---|---|
|asm_interior|68|0|0|0|0|0|
|stmt_continuation|0|2081|25|3020|149|0|
|other|0|19|0|22|0|0|
|ast_unavailable|0|0|0|0|0|0|

**ffmpeg-a32：DA**

|旧类→新类|asm_interior|structural_line|expr_continuation|own_stmt_no_code|other|ast_unavailable|
|---|---|---|---|---|---|---|
|asm_interior|14050578484|0|0|0|0|0|
|stmt_continuation|0|2977213844|1799|4658878900|193521529|0|
|other|0|148054|0|88495|0|0|
|ast_unavailable|0|0|0|0|0|0|

### 12.7 每类DA最高20行

不足20行全列、空类别无条目。下表token为该行全部raw token文本序列（不含注释/空白），详细kind/offset/跨行跨度、AST原始JSONL行号与SHA见各对象top20分片。structural的AST列仅列上下文，不参与除标号范围之外的结构性判断。

**spike-thumb**

|类|文件|行|DA|全部token|AST节点|范围|
|---|---|---|---|---|---|---|
|structural_line|eval-spike-1.0/spike.c|70|4063610861|["}"]|CompoundStmt|67–70|
|structural_line|eval-spike-1.0/spike.c|38|137029154|["{"]|CompoundStmt|38–40|
|structural_line|eval-spike-1.0/spike.c|40|137029154|["}"]|CompoundStmt|38–40|
|structural_line|eval-spike-1.0/spike.c|28|128004096|["{"]|CompoundStmt|28–35|
|structural_line|eval-spike-1.0/spike.c|35|128004096|["}"]|CompoundStmt|28–35|
|structural_line|eval-spike-1.0/spike.c|90|128000000|["}"]|CompoundStmt|79–90|
|structural_line|eval-spike-1.0/spike.c|112|128000000|["}"]|CompoundStmt|110–112|
|structural_line|eval-spike-1.0/spike.c|124|128000000|["}"]|CompoundStmt|122–124|
|structural_line|eval-spike-1.0/spike.c|72|127000000|["}"]|CompoundStmt|64–72|
|structural_line|eval-spike-1.0/spike.c|50|120004252|["}"]|CompoundStmt|44–50|
|structural_line|eval-spike-1.0/spike.c|88|8003062|["}"]|CompoundStmt|86–88|
|structural_line|eval-spike-1.0/spike.c|92|1000000|["}"]|CompoundStmt|77–92|
|structural_line|eval-spike-1.0/spike.c|108|1000000|["{"]|CompoundStmt|108–114|
|structural_line|eval-spike-1.0/spike.c|114|1000000|["}"]|CompoundStmt|108–114|
|structural_line|eval-spike-1.0/spike.c|133|1000000|["}"]|CompoundStmt|121–133|
|structural_line|eval-spike-1.0/spike.c|130|999023|["}", "else", "{"]|CompoundStmt|128–130|
|structural_line|eval-spike-1.0/spike.c|132|999023|["}"]|CompoundStmt|130–132|
|structural_line|eval-spike-1.0/spike.c|103|30287|["}"]|CompoundStmt|97–103|
|structural_line|eval-spike-1.0/spike.c|102|27069|["}"]|CompoundStmt|100–102|
|structural_line|eval-spike-1.0/spike.c|58|4096|["}"]|CompoundStmt|55–58|
|own_stmt_no_code|eval-spike-1.0/spike.c|69|4063610861|["--", "j", ";"]|UnaryOperator|69–69|
|own_stmt_no_code|eval-spike-1.0/spike.c|29|128004096|["uint64_t", "x", "=", "*", "state", ";"]|DeclStmt|29–29|
|own_stmt_no_code|eval-spike-1.0/spike.c|33|128004096|["*", "state", "=", "x", ";"]|BinaryOperator|33–33|
|own_stmt_no_code|eval-spike-1.0/spike.c|66|127000000|["unsigned", "int", "j", "=", "i", ";"]|DeclStmt|66–66|
|own_stmt_no_code|eval-spike-1.0/spike.c|78|1000000|["uint64_t", "sum", "=", "0", ";"]|DeclStmt|78–78|
|own_stmt_no_code|eval-spike-1.0/spike.c|109|1000000|["uint64_t", "sum", "=", "0", ";"]|DeclStmt|109–109|
|own_stmt_no_code|eval-spike-1.0/spike.c|113|1000000|["return", "sum", ";"]|ReturnStmt|113–113|
|own_stmt_no_code|eval-spike-1.0/spike.c|54|1|["uint64_t", "state", "=", "initial_seed", ";"]|DeclStmt|54–54|
|own_stmt_no_code|eval-spike-1.0/spike.c|118|1|["uint32_t", "values", "[", "BLOCK_SIZE", "]", ";"]|DeclStmt|118–118|
|own_stmt_no_code|eval-spike-1.0/spike.c|120|1|["uint64_t", "checksum", "=", "UINT64_C", "(", "0x6a09e667f3bcc909", ")", ";"]|DeclStmt|120–120|
|own_stmt_no_code|eval-spike-1.0/spike.c|140|1|["unsigned", "long", "long", "parsed", ";"]|DeclStmt|140–140|
|own_stmt_no_code|eval-spike-1.0/spike.c|157|1|["uint64_t", "result", ";"]|DeclStmt|157–157|
|own_stmt_no_code|eval-spike-1.0/spike.c|169|1|["initialize_table", "(", ")", ";"]|CallExpr|169–169|
|own_stmt_no_code|eval-spike-1.0/spike.c|172|1|["rounds", ",", "seed", ",", "result", ")", ";"]|DeclRefExpr|172–172|
|own_stmt_no_code|eval-spike-1.0/spike.c|173|1|["return", "0", ";"]|ReturnStmt|173–173|
|own_stmt_no_code|eval-spike-1.0/spike.c|142|0|["return", "0", ";"]|ReturnStmt|142–142|
|own_stmt_no_code|eval-spike-1.0/spike.c|147|0|["return", "0", ";"]|ReturnStmt|147–147|
|own_stmt_no_code|eval-spike-1.0/spike.c|161|0|["return", "2", ";"]|ReturnStmt|161–161|
|own_stmt_no_code|eval-spike-1.0/spike.c|166|0|["return", "2", ";"]|ReturnStmt|166–166|

**spike-a32**

|类|文件|行|DA|全部token|AST节点|范围|
|---|---|---|---|---|---|---|
|structural_line|eval-spike-1.0/spike.c|70|4063610861|["}"]|CompoundStmt|67–70|
|structural_line|eval-spike-1.0/spike.c|38|137029154|["{"]|CompoundStmt|38–40|
|structural_line|eval-spike-1.0/spike.c|40|137029154|["}"]|CompoundStmt|38–40|
|structural_line|eval-spike-1.0/spike.c|28|128004096|["{"]|CompoundStmt|28–35|
|structural_line|eval-spike-1.0/spike.c|35|128004096|["}"]|CompoundStmt|28–35|
|structural_line|eval-spike-1.0/spike.c|90|128000000|["}"]|CompoundStmt|79–90|
|structural_line|eval-spike-1.0/spike.c|112|128000000|["}"]|CompoundStmt|110–112|
|structural_line|eval-spike-1.0/spike.c|124|128000000|["}"]|CompoundStmt|122–124|
|structural_line|eval-spike-1.0/spike.c|72|127000000|["}"]|CompoundStmt|64–72|
|structural_line|eval-spike-1.0/spike.c|50|120004252|["}"]|CompoundStmt|44–50|
|structural_line|eval-spike-1.0/spike.c|88|8003062|["}"]|CompoundStmt|86–88|
|structural_line|eval-spike-1.0/spike.c|92|1000000|["}"]|CompoundStmt|77–92|
|structural_line|eval-spike-1.0/spike.c|108|1000000|["{"]|CompoundStmt|108–114|
|structural_line|eval-spike-1.0/spike.c|114|1000000|["}"]|CompoundStmt|108–114|
|structural_line|eval-spike-1.0/spike.c|133|1000000|["}"]|CompoundStmt|121–133|
|structural_line|eval-spike-1.0/spike.c|130|999023|["}", "else", "{"]|CompoundStmt|128–130|
|structural_line|eval-spike-1.0/spike.c|132|999023|["}"]|CompoundStmt|130–132|
|structural_line|eval-spike-1.0/spike.c|103|30287|["}"]|CompoundStmt|97–103|
|structural_line|eval-spike-1.0/spike.c|102|27069|["}"]|CompoundStmt|100–102|
|structural_line|eval-spike-1.0/spike.c|58|4096|["}"]|CompoundStmt|55–58|
|own_stmt_no_code|eval-spike-1.0/spike.c|69|4063610861|["--", "j", ";"]|UnaryOperator|69–69|
|own_stmt_no_code|eval-spike-1.0/spike.c|29|128004096|["uint64_t", "x", "=", "*", "state", ";"]|DeclStmt|29–29|
|own_stmt_no_code|eval-spike-1.0/spike.c|33|128004096|["*", "state", "=", "x", ";"]|BinaryOperator|33–33|
|own_stmt_no_code|eval-spike-1.0/spike.c|82|128000000|["const", "struct", "entry", "*", "item", "=", "&", "table", "[", "index", "]", ";"]|DeclStmt|82–82|
|own_stmt_no_code|eval-spike-1.0/spike.c|66|127000000|["unsigned", "int", "j", "=", "i", ";"]|DeclStmt|66–66|
|own_stmt_no_code|eval-spike-1.0/spike.c|78|1000000|["uint64_t", "sum", "=", "0", ";"]|DeclStmt|78–78|
|own_stmt_no_code|eval-spike-1.0/spike.c|109|1000000|["uint64_t", "sum", "=", "0", ";"]|DeclStmt|109–109|
|own_stmt_no_code|eval-spike-1.0/spike.c|113|1000000|["return", "sum", ";"]|ReturnStmt|113–113|
|own_stmt_no_code|eval-spike-1.0/spike.c|54|1|["uint64_t", "state", "=", "initial_seed", ";"]|DeclStmt|54–54|
|own_stmt_no_code|eval-spike-1.0/spike.c|118|1|["uint32_t", "values", "[", "BLOCK_SIZE", "]", ";"]|DeclStmt|118–118|
|own_stmt_no_code|eval-spike-1.0/spike.c|120|1|["uint64_t", "checksum", "=", "UINT64_C", "(", "0x6a09e667f3bcc909", ")", ";"]|DeclStmt|120–120|
|own_stmt_no_code|eval-spike-1.0/spike.c|140|1|["unsigned", "long", "long", "parsed", ";"]|DeclStmt|140–140|
|own_stmt_no_code|eval-spike-1.0/spike.c|157|1|["uint64_t", "result", ";"]|DeclStmt|157–157|
|own_stmt_no_code|eval-spike-1.0/spike.c|169|1|["initialize_table", "(", ")", ";"]|CallExpr|169–169|
|own_stmt_no_code|eval-spike-1.0/spike.c|172|1|["rounds", ",", "seed", ",", "result", ")", ";"]|DeclRefExpr|172–172|
|own_stmt_no_code|eval-spike-1.0/spike.c|173|1|["return", "0", ";"]|ReturnStmt|173–173|
|own_stmt_no_code|eval-spike-1.0/spike.c|142|0|["return", "0", ";"]|ReturnStmt|142–142|
|own_stmt_no_code|eval-spike-1.0/spike.c|147|0|["return", "0", ";"]|ReturnStmt|147–147|
|own_stmt_no_code|eval-spike-1.0/spike.c|161|0|["return", "2", ";"]|ReturnStmt|161–161|
|own_stmt_no_code|eval-spike-1.0/spike.c|166|0|["return", "2", ";"]|ReturnStmt|166–166|

**ffmpeg-thumb**

|类|文件|行|DA|全部token|AST节点|范围|
|---|---|---|---|---|---|---|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|37|255523038|["\"ldrb       %[bit]        , [%[state]]                  \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|38|255523038|["\"add        %[r_b]        , %[tables]   , %[lps_off]    \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|39|255523038|["\"mov        %[tmp]        , %[range]                    \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|40|255523038|["\"and        %[range]      , %[range]    , #0xC0         \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|41|255523038|["\"add        %[r_b]        , %[r_b]      , %[bit]        \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|42|255523038|["\"ldrb       %[range]      , [%[r_b], %[range], lsl #1]  \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|43|255523038|["\"add        %[r_b]        , %[tables]   , %[norm_off]   \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|44|255523038|["\"sub        %[r_c]        , %[tmp]      , %[range]      \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|45|255523038|["\"lsl        %[tmp]        , %[r_c]      , #17           \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|46|255523038|["\"cmp        %[tmp]        , %[low]                      \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|47|255523038|["\"it         gt                                          \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|48|255523038|["\"movgt      %[range]      , %[r_c]                      \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|49|255523038|["\"itt        cc                                          \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|50|255523038|["\"mvncc      %[bit]        , %[bit]                      \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|51|255523038|["\"subcc      %[low]        , %[low]      , %[tmp]        \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|52|255523038|["\"add        %[r_c]        , %[tables]   , %[mlps_off]   \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|53|255523038|["\"ldrb       %[tmp]        , [%[r_b], %[range]]          \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|54|255523038|["\"ldrb       %[r_b]        , [%[r_c], %[bit]]            \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|55|255523038|["\"lsl        %[low]        , %[low]      , %[tmp]        \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|56|255523038|["\"lsl        %[range]      , %[range]    , %[tmp]        \\n\\t\""]|GCCAsmStmt|36–102|
|structural_line|ffmpeg-8.0.1/libavcodec/arm/cabac.h|32|255523038|["{"]|CompoundStmt|32–105|
|structural_line|ffmpeg-8.0.1/libavcodec/arm/cabac.h|105|255523038|["}"]|CompoundStmt|32–105|
|structural_line|ffmpeg-8.0.1/libavcodec/cabac_functions.h|146|215694437|["}"]|CompoundStmt|144–146|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1680|84904984|["}"]|CompoundStmt|1670–1680|
|structural_line|ffmpeg-8.0.1/libavcodec/cabac_functions.h|142|39828601|["}"]|CompoundStmt|140–142|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|585|39117292|["}"]|CompoundStmt|571–585|
|structural_line|ffmpeg-8.0.1/libavcodec/cabac_functions.h|180|36812720|["}"]|CompoundStmt|167–180|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1723|33561176|["do", "{"]|CompoundStmt|1723–1763|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1725|33561176|[]|CompoundStmt|1723–1763|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1727|33561176|[]|CompoundStmt|1723–1763|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1679|33116225|["}"]|CompoundStmt|1672–1679|
|structural_line|ffmpeg-8.0.1/libavcodec/rectangle.h|122|27667920|["}"]|CompoundStmt|41–122|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_parse.h|128|26374116|["{"]|CompoundStmt|128–134|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_parse.h|134|26374116|["}"]|CompoundStmt|128–134|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1735|25893332|["}", "else", "{"]|CompoundStmt|1728–1735|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1732|23970368|["}", "else", "{"]|CompoundStmt|1730–1732|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1734|23970368|["}"]|CompoundStmt|1732–1734|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|668|23755400|["}"]|CompoundStmt|654–668|
|structural_line|ffmpeg-8.0.1/libavcodec/h264dec.h|676|20947440|["{"]|CompoundStmt|676–678|
|structural_line|ffmpeg-8.0.1/libavcodec/h264dec.h|678|20947440|["}"]|CompoundStmt|676–678|
|expr_continuation|ffmpeg-8.0.1/libavcodec/h264_slice.c|1088|1799|[")", ")", ";"]|ParenExpr|1082–1088|
|expr_continuation|ffmpeg-8.0.1/libavcodec/avcodec.c|302|0|["\"add '-strict %d' if you want to use it.\\n\"", ","]|CallExpr|300–303|
|expr_continuation|ffmpeg-8.0.1/libavcodec/avcodec.c|390|0|["\"that doesn't support it\\n\"", ")", ";"]|ImplicitCastExpr|389–390|
|expr_continuation|ffmpeg-8.0.1/libavcodec/bsf.c|161|0|["\"bitstream filter '%s'. Supported codecs are: \"", ","]|ImplicitCastExpr|160–161|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|121|0|["\"changes, but PARAM_CHANGE side data was sent to it.\\n\"", ")", ";"]|ImplicitCastExpr|120–121|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|481|0|["\"Stop draining and force EOF.\\n\"", ")", ";"]|ImplicitCastExpr|480–481|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|743|0|["\"%\"", "SIZE_SPECIFIER", "\"/%\"", "SIZE_SPECIFIER", "\"/%\"", "SIZE_SPECIFIER", "\"/%\"", "SIZE_SPECIFIER", "\" \""]|CallExpr|741–746|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|744|0|["\"(frame size %dx%d). This is a bug, please report it\\n\"", ","]|CallExpr|741–746|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|784|0|["\"This is a bug, please report it.\\n\"", ")", ";"]|ImplicitCastExpr|783–784|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|1239|0|["\"get_format() callback.\\n\"", ")", ";"]|ImplicitCastExpr|1238–1239|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|1283|0|["\"does not match the format of the provided frames \""]|ImplicitCastExpr|1282–1284|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|1294|0|["\"does not match the type of the provided device \""]|ImplicitCastExpr|1293–1295|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|1903|0|["\"supported with subtitles codecs\\n\"", ")", ";"]|ImplicitCastExpr|1902–1903|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|1907|0|["\"subtitles character encoding will be ignored\\n\"", ","]|ImplicitCastExpr|1906–1907|
|expr_continuation|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|771|0|[":"]|ConditionalOperator|769–772|
|expr_continuation|ffmpeg-8.0.1/libavcodec/h264_ps.c|485|0|["\"values are l:%d r:%d t:%d b:%d\\n\"", ","]|ImplicitCastExpr|484–485|
|expr_continuation|ffmpeg-8.0.1/libavcodec/h264_ps.c|573|0|[")", ";"]|CallExpr|557–573|
|expr_continuation|ffmpeg-8.0.1/libavcodec/h264_ps.c|718|0|["\"(%\"", "SIZE_SPECIFIER", "\" > %\"", "SIZE_SPECIFIER", "\")\\n\"", ","]|ImplicitCastExpr|717–718|
|expr_continuation|ffmpeg-8.0.1/libavcodec/h264_refs.c|372|0|[")", ";"]|CallExpr|369–372|
|expr_continuation|ffmpeg-8.0.1/libavcodec/h264_refs.c|743|0|["\"assignment for second field \""]|ImplicitCastExpr|742–745|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/arm/cabac.h|33|255523038|["int", "bit", ";"]|DeclStmt|33–33|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/arm/cabac.h|34|255523038|["void", "*", "reg_b", ",", "*", "reg_c", ",", "*", "tmp", ";"]|DeclStmt|34–34|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1649|201269902|["#", "define", "CC", "&", "cc"]|UnaryOperator|1649–1649|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1670|85349935|["for", "(", "last", "=", "0", ";", "last", "<", "coefs", ";", "last", "++", ")", "{"]|ForStmt|1670–1680|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1671|84904984|["uint8_t", "*", "sig_ctx", "=", "significant_coeff_ctx_base", "+", "sig_off", ";"]|VarDecl|1671–1701|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1672|84904984|["if", "(", "get_cabac", "(", "CC", ",", "sig_ctx", ")", ")", "{"]|IfStmt|1672–1679|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|571|48896615|["for", "(", "i", "=", "0", ";", "i", "<", "4", ";", "i", "++", ")", "{"]|ForStmt|571–585|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/rectangle.h|41|42499258|["static", "av_always_inline", "void", "fill_rectangle", "(", "void", "*", "vp", ",", "int", "w", ",", "int", "h", ",", "int", "stride", ",", "uint32_t", "val", ",", "int", "size", ")", "{"]|FunctionDecl|41–122|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/rectangle.h|42|42499258|["uint8_t", "*", "p", "=", "(", "uint8_t", "*", ")", "vp", ";"]|DeclStmt|42–42|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/rectangle.h|43|42499258|["av_assert2", "(", "size", "==", "1", "\|\|", "size", "==", "2", "\|\|", "size", "==", "4", ")", ";"]|CStyleCastExpr|43–43|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/rectangle.h|44|42499258|["av_assert2", "(", "w", "<=", "4", ")", ";"]|CStyleCastExpr|44–44|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/rectangle.h|46|42499258|["w", "*=", "size", ";"]|CompoundAssignOperator|46–46|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/rectangle.h|47|42499258|["stride", "*=", "size", ";"]|CompoundAssignOperator|47–47|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/rectangle.h|49|42499258|["av_assert2", "(", "(", "(", "(", "long", ")", "vp", ")", "&", "(", "FFMIN", "(", "w", ",", "8", "<<", "(", "HAVE_NEON", "\|", "ARCH_PPC", "\|", "HAVE_MMX", ")", ")", "-", "1", ")", ")", "==", "0", ")", ";"]|CStyleCastExpr|49–49|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/rectangle.h|50|42499258|["av_assert2", "(", "(", "stride", "&", "(", "w", "-", "1", ")", ")", "==", "0", ")", ";"]|CStyleCastExpr|50–50|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/rectangle.h|51|42499258|["if", "(", "w", "==", "2", ")", "{"]|IfStmt|51–120|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|572|39117292|["int", "x", "=", "dir", "==", "0", "?", "0", ":", "i", ";"]|DeclStmt|572–572|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|573|39117292|["int", "y", "=", "dir", "==", "0", "?", "i", ":", "0", ";"]|DeclStmt|573–573|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|574|39117292|["int", "b_idx", "=", "8", "+", "4", "+", "x", "+", "8", "*", "y", ";"]|DeclStmt|574–574|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|575|39117292|["int", "bn_idx", "=", "b_idx", "-", "(", "dir", "?", "8", ":", "1", ")", ";"]|DeclStmt|575–575|
|other|ffmpeg-8.0.1/libavcodec/h264_parse.h|133|26374116|["#", "endif"]|CompoundStmt|128–134|
|other|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1645|12657144|["#", "if", "!", "ARCH_X86"]|CompoundStmt|1596–1776|
|other|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1646|12657144|["#", "define", "CABAC_ON_STACK"]|CompoundStmt|1596–1776|
|other|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1647|12657144|["#", "endif"]|CompoundStmt|1596–1776|
|other|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1648|12657144|["#", "ifdef", "CABAC_ON_STACK"]|CompoundStmt|1596–1776|
|other|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1722|12657144|["#", "define", "STORE_BLOCK", "(", "type", ")"]|CompoundStmt|1596–1776|
|other|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1770|12657144|["#", "ifdef", "CABAC_ON_STACK"]|CompoundStmt|1596–1776|
|other|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1774|12657144|["#", "endif"]|CompoundStmt|1596–1776|
|other|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1703|10681452|["#", "endif"]|CompoundStmt|1697–1704|
|other|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|496|10534474|[")", "{"]|CompoundStmt|496–543|
|other|ffmpeg-8.0.1/libavcodec/rectangle.h|118|8964616|["#", "endif"]|CompoundStmt|100–119|
|other|ffmpeg-8.0.1/libavcodec/h264_mb.c|554|6300442|["}", "else", "if", "(", "xchg", ")"]|CompoundStmt|547–554|
|other|ffmpeg-8.0.1/libavcodec/h264_mb.c|555|6300442|["AV_SWAP64", "(", "b", ",", "a", ")", ";"]|CompoundStmt|515–594|
|other|ffmpeg-8.0.1/libavcodec/h264_mb.c|557|6300442|["AV_COPY64", "(", "b", ",", "a", ")", ";"]|CompoundStmt|515–594|
|other|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|846|5354692|["#", "endif"]|CompoundStmt|720–847|
|other|ffmpeg-8.0.1/libavcodec/h264_cabac.c|2090|2896608|["sl", "->", "intra4x4_pred_mode_cache", "[", "scan8", "[", "i", "]", "]", ")", ";"]|CompoundStmt|2085–2091|
|other|ffmpeg-8.0.1/libavcodec/cabac_functions.h|65|2610383|["#", "if", "CABAC_BITS", "==", "16"]|CompoundStmt|64–75|
|other|ffmpeg-8.0.1/libavcodec/h264_mvpred.h|280|2610331|["\"pred_motion (%2d %2d %2d) (%2d %2d %2d) (%2d %2d %2d) -> (%2d %2d %2d) at %2d %2d %d list %d\\n\"", ","]|CompoundStmt|231–283|
|other|ffmpeg-8.0.1/libavcodec/h264_mvpred.h|281|2610331|["top_ref", ",", "B", "[", "0", "]", ",", "B", "[", "1", "]", ",", "diagonal_ref", ",", "C", "[", "0", "]", ",", "C", "[", "1", "]", ",", "left_ref", ","]|CompoundStmt|231–283|
|other|ffmpeg-8.0.1/libavcodec/h264_mvpred.h|282|2610331|["A", "[", "0", "]", ",", "A", "[", "1", "]", ",", "ref", ",", "*", "mx", ",", "*", "my", ",", "sl", "->", "mb_x", ",", "sl", "->", "mb_y", ",", "n", ",", "list", ")", ";"]|CompoundStmt|231–283|

**ffmpeg-a32**

|类|文件|行|DA|全部token|AST节点|范围|
|---|---|---|---|---|---|---|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|37|255523038|["\"ldrb       %[bit]        , [%[state]]                  \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|38|255523038|["\"add        %[r_b]        , %[tables]   , %[lps_off]    \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|39|255523038|["\"mov        %[tmp]        , %[range]                    \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|40|255523038|["\"and        %[range]      , %[range]    , #0xC0         \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|41|255523038|["\"add        %[r_b]        , %[r_b]      , %[bit]        \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|42|255523038|["\"ldrb       %[range]      , [%[r_b], %[range], lsl #1]  \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|43|255523038|["\"add        %[r_b]        , %[tables]   , %[norm_off]   \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|44|255523038|["\"sub        %[r_c]        , %[tmp]      , %[range]      \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|45|255523038|["\"lsl        %[tmp]        , %[r_c]      , #17           \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|46|255523038|["\"cmp        %[tmp]        , %[low]                      \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|47|255523038|["\"it         gt                                          \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|48|255523038|["\"movgt      %[range]      , %[r_c]                      \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|49|255523038|["\"itt        cc                                          \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|50|255523038|["\"mvncc      %[bit]        , %[bit]                      \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|51|255523038|["\"subcc      %[low]        , %[low]      , %[tmp]        \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|52|255523038|["\"add        %[r_c]        , %[tables]   , %[mlps_off]   \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|53|255523038|["\"ldrb       %[tmp]        , [%[r_b], %[range]]          \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|54|255523038|["\"ldrb       %[r_b]        , [%[r_c], %[bit]]            \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|55|255523038|["\"lsl        %[low]        , %[low]      , %[tmp]        \\n\\t\""]|GCCAsmStmt|36–102|
|asm_interior|ffmpeg-8.0.1/libavcodec/arm/cabac.h|56|255523038|["\"lsl        %[range]      , %[range]    , %[tmp]        \\n\\t\""]|GCCAsmStmt|36–102|
|structural_line|ffmpeg-8.0.1/libavcodec/arm/cabac.h|32|255523038|["{"]|CompoundStmt|32–105|
|structural_line|ffmpeg-8.0.1/libavcodec/arm/cabac.h|105|255523038|["}"]|CompoundStmt|32–105|
|structural_line|ffmpeg-8.0.1/libavcodec/cabac_functions.h|146|215694437|["}"]|CompoundStmt|144–146|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1680|84904984|["}"]|CompoundStmt|1670–1680|
|structural_line|ffmpeg-8.0.1/libavcodec/cabac_functions.h|142|39828601|["}"]|CompoundStmt|140–142|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|585|39117292|["}"]|CompoundStmt|571–585|
|structural_line|ffmpeg-8.0.1/libavcodec/cabac_functions.h|180|36812720|["}"]|CompoundStmt|167–180|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1723|33561176|["do", "{"]|CompoundStmt|1723–1763|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1725|33561176|[]|CompoundStmt|1723–1763|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1727|33561176|[]|CompoundStmt|1723–1763|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1679|33116225|["}"]|CompoundStmt|1672–1679|
|structural_line|ffmpeg-8.0.1/libavcodec/rectangle.h|122|27667920|["}"]|CompoundStmt|41–122|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_parse.h|128|26374116|["{"]|CompoundStmt|128–134|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_parse.h|134|26374116|["}"]|CompoundStmt|128–134|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1735|25893332|["}", "else", "{"]|CompoundStmt|1728–1735|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1732|23970368|["}", "else", "{"]|CompoundStmt|1730–1732|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1734|23970368|["}"]|CompoundStmt|1732–1734|
|structural_line|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|668|23755400|["}"]|CompoundStmt|654–668|
|structural_line|ffmpeg-8.0.1/libavcodec/h264dec.h|676|20947440|["{"]|CompoundStmt|676–678|
|structural_line|ffmpeg-8.0.1/libavcodec/h264dec.h|678|20947440|["}"]|CompoundStmt|676–678|
|expr_continuation|ffmpeg-8.0.1/libavcodec/h264_slice.c|1088|1799|[")", ")", ";"]|ParenExpr|1082–1088|
|expr_continuation|ffmpeg-8.0.1/libavcodec/avcodec.c|302|0|["\"add '-strict %d' if you want to use it.\\n\"", ","]|CallExpr|300–303|
|expr_continuation|ffmpeg-8.0.1/libavcodec/avcodec.c|390|0|["\"that doesn't support it\\n\"", ")", ";"]|ImplicitCastExpr|389–390|
|expr_continuation|ffmpeg-8.0.1/libavcodec/bsf.c|161|0|["\"bitstream filter '%s'. Supported codecs are: \"", ","]|ImplicitCastExpr|160–161|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|121|0|["\"changes, but PARAM_CHANGE side data was sent to it.\\n\"", ")", ";"]|ImplicitCastExpr|120–121|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|481|0|["\"Stop draining and force EOF.\\n\"", ")", ";"]|ImplicitCastExpr|480–481|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|743|0|["\"%\"", "SIZE_SPECIFIER", "\"/%\"", "SIZE_SPECIFIER", "\"/%\"", "SIZE_SPECIFIER", "\"/%\"", "SIZE_SPECIFIER", "\" \""]|CallExpr|741–746|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|744|0|["\"(frame size %dx%d). This is a bug, please report it\\n\"", ","]|CallExpr|741–746|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|784|0|["\"This is a bug, please report it.\\n\"", ")", ";"]|ImplicitCastExpr|783–784|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|1239|0|["\"get_format() callback.\\n\"", ")", ";"]|ImplicitCastExpr|1238–1239|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|1283|0|["\"does not match the format of the provided frames \""]|ImplicitCastExpr|1282–1284|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|1294|0|["\"does not match the type of the provided device \""]|ImplicitCastExpr|1293–1295|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|1903|0|["\"supported with subtitles codecs\\n\"", ")", ";"]|ImplicitCastExpr|1902–1903|
|expr_continuation|ffmpeg-8.0.1/libavcodec/decode.c|1907|0|["\"subtitles character encoding will be ignored\\n\"", ","]|ImplicitCastExpr|1906–1907|
|expr_continuation|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|771|0|[":"]|ConditionalOperator|769–772|
|expr_continuation|ffmpeg-8.0.1/libavcodec/h264_ps.c|485|0|["\"values are l:%d r:%d t:%d b:%d\\n\"", ","]|ImplicitCastExpr|484–485|
|expr_continuation|ffmpeg-8.0.1/libavcodec/h264_ps.c|573|0|[")", ";"]|CallExpr|557–573|
|expr_continuation|ffmpeg-8.0.1/libavcodec/h264_ps.c|718|0|["\"(%\"", "SIZE_SPECIFIER", "\" > %\"", "SIZE_SPECIFIER", "\")\\n\"", ","]|ImplicitCastExpr|717–718|
|expr_continuation|ffmpeg-8.0.1/libavcodec/h264_refs.c|372|0|[")", ";"]|CallExpr|369–372|
|expr_continuation|ffmpeg-8.0.1/libavcodec/h264_refs.c|743|0|["\"assignment for second field \""]|ImplicitCastExpr|742–745|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/arm/cabac.h|33|255523038|["int", "bit", ";"]|DeclStmt|33–33|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/arm/cabac.h|34|255523038|["void", "*", "reg_b", ",", "*", "reg_c", ",", "*", "tmp", ";"]|DeclStmt|34–34|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1649|201269902|["#", "define", "CC", "&", "cc"]|UnaryOperator|1649–1649|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1670|85349935|["for", "(", "last", "=", "0", ";", "last", "<", "coefs", ";", "last", "++", ")", "{"]|ForStmt|1670–1680|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1671|84904984|["uint8_t", "*", "sig_ctx", "=", "significant_coeff_ctx_base", "+", "sig_off", ";"]|VarDecl|1671–1701|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1672|84904984|["if", "(", "get_cabac", "(", "CC", ",", "sig_ctx", ")", ")", "{"]|IfStmt|1672–1679|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|571|48896615|["for", "(", "i", "=", "0", ";", "i", "<", "4", ";", "i", "++", ")", "{"]|ForStmt|571–585|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/rectangle.h|41|42499258|["static", "av_always_inline", "void", "fill_rectangle", "(", "void", "*", "vp", ",", "int", "w", ",", "int", "h", ",", "int", "stride", ",", "uint32_t", "val", ",", "int", "size", ")", "{"]|FunctionDecl|41–122|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/rectangle.h|42|42499258|["uint8_t", "*", "p", "=", "(", "uint8_t", "*", ")", "vp", ";"]|DeclStmt|42–42|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/rectangle.h|43|42499258|["av_assert2", "(", "size", "==", "1", "\|\|", "size", "==", "2", "\|\|", "size", "==", "4", ")", ";"]|CStyleCastExpr|43–43|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/rectangle.h|44|42499258|["av_assert2", "(", "w", "<=", "4", ")", ";"]|CStyleCastExpr|44–44|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/rectangle.h|46|42499258|["w", "*=", "size", ";"]|CompoundAssignOperator|46–46|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/rectangle.h|47|42499258|["stride", "*=", "size", ";"]|CompoundAssignOperator|47–47|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/rectangle.h|49|42499258|["av_assert2", "(", "(", "(", "(", "long", ")", "vp", ")", "&", "(", "FFMIN", "(", "w", ",", "8", "<<", "(", "HAVE_NEON", "\|", "ARCH_PPC", "\|", "HAVE_MMX", ")", ")", "-", "1", ")", ")", "==", "0", ")", ";"]|CStyleCastExpr|49–49|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/rectangle.h|50|42499258|["av_assert2", "(", "(", "stride", "&", "(", "w", "-", "1", ")", ")", "==", "0", ")", ";"]|CStyleCastExpr|50–50|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/rectangle.h|51|42499258|["if", "(", "w", "==", "2", ")", "{"]|IfStmt|51–120|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|572|39117292|["int", "x", "=", "dir", "==", "0", "?", "0", ":", "i", ";"]|DeclStmt|572–572|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|573|39117292|["int", "y", "=", "dir", "==", "0", "?", "i", ":", "0", ";"]|DeclStmt|573–573|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|574|39117292|["int", "b_idx", "=", "8", "+", "4", "+", "x", "+", "8", "*", "y", ";"]|DeclStmt|574–574|
|own_stmt_no_code|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|575|39117292|["int", "bn_idx", "=", "b_idx", "-", "(", "dir", "?", "8", ":", "1", ")", ";"]|DeclStmt|575–575|
|other|ffmpeg-8.0.1/libavcodec/h264_parse.h|133|26374116|["#", "endif"]|CompoundStmt|128–134|
|other|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1645|12657144|["#", "if", "!", "ARCH_X86"]|CompoundStmt|1596–1776|
|other|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1646|12657144|["#", "define", "CABAC_ON_STACK"]|CompoundStmt|1596–1776|
|other|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1647|12657144|["#", "endif"]|CompoundStmt|1596–1776|
|other|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1648|12657144|["#", "ifdef", "CABAC_ON_STACK"]|CompoundStmt|1596–1776|
|other|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1722|12657144|["#", "define", "STORE_BLOCK", "(", "type", ")"]|CompoundStmt|1596–1776|
|other|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1770|12657144|["#", "ifdef", "CABAC_ON_STACK"]|CompoundStmt|1596–1776|
|other|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1774|12657144|["#", "endif"]|CompoundStmt|1596–1776|
|other|ffmpeg-8.0.1/libavcodec/h264_cabac.c|1703|10681452|["#", "endif"]|CompoundStmt|1697–1704|
|other|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|496|10534474|[")", "{"]|CompoundStmt|496–543|
|other|ffmpeg-8.0.1/libavcodec/rectangle.h|118|8964616|["#", "endif"]|CompoundStmt|100–119|
|other|ffmpeg-8.0.1/libavcodec/h264_mb.c|554|6300442|["}", "else", "if", "(", "xchg", ")"]|CompoundStmt|547–554|
|other|ffmpeg-8.0.1/libavcodec/h264_mb.c|555|6300442|["AV_SWAP64", "(", "b", ",", "a", ")", ";"]|CompoundStmt|515–594|
|other|ffmpeg-8.0.1/libavcodec/h264_mb.c|557|6300442|["AV_COPY64", "(", "b", ",", "a", ")", ";"]|CompoundStmt|515–594|
|other|ffmpeg-8.0.1/libavcodec/h264_loopfilter.c|846|5354692|["#", "endif"]|CompoundStmt|720–847|
|other|ffmpeg-8.0.1/libavcodec/h264_cabac.c|2090|2896608|["sl", "->", "intra4x4_pred_mode_cache", "[", "scan8", "[", "i", "]", "]", ")", ";"]|CompoundStmt|2085–2091|
|other|ffmpeg-8.0.1/libavcodec/cabac_functions.h|65|2610383|["#", "if", "CABAC_BITS", "==", "16"]|CompoundStmt|64–75|
|other|ffmpeg-8.0.1/libavcodec/h264_mvpred.h|280|2610331|["\"pred_motion (%2d %2d %2d) (%2d %2d %2d) (%2d %2d %2d) -> (%2d %2d %2d) at %2d %2d %d list %d\\n\"", ","]|CompoundStmt|231–283|
|other|ffmpeg-8.0.1/libavcodec/h264_mvpred.h|281|2610331|["top_ref", ",", "B", "[", "0", "]", ",", "B", "[", "1", "]", ",", "diagonal_ref", ",", "C", "[", "0", "]", ",", "C", "[", "1", "]", ",", "left_ref", ","]|CompoundStmt|231–283|
|other|ffmpeg-8.0.1/libavcodec/h264_mvpred.h|282|2610331|["A", "[", "0", "]", ",", "A", "[", "1", "]", ",", "ref", ",", "*", "mx", ",", "*", "my", ",", "sl", "->", "mb_x", ",", "sl", "->", "mb_y", ",", "n", ",", "list", ")", ";"]|CompoundStmt|231–283|

### 12.8 不变量、测试、资源与停止

|对象|分类行数|分类DA|原C−新C|差值|
|---|---|---|---|---|
|spike-thumb|47|9688364214|9688364214|0|
|spike-a32|48|9816364214|9816364214|0|
|ffmpeg-thumb|5403|21879658811|21879658811|0|
|ffmpeg-a32|5384|21880431105|21880431105|0|

每个code_free行恰好出现一次、分类DA之和=原ΣR(C)−新ΣR(C)，四对象断言均通过；新旧交叉表边际和亦核对。原144项测试文件字节不变，新增17项synthetic，共161项通过。包含用户要求的7例及asm/other/ast_unavailable、排除控制语句整体、节点本行起始阻止续行、最内层节点、Decl续行、标号后跟调用及FunctionDecl无法确认时不猜测。

保留开发草稿：最初把Clang token kind else/do误写成kw_else/kw_do，检查真实token后修正；未发布的分类草稿移到temp/prep-code-free-v2/draft-keyword-spelling，SHA/原因见draft-classification-disposition.json。旧发布分类从未改写，最终证据以*-classify-final-run与*-classification/index.json为准。不是编译器缺陷或规则修改。

资源全程串行nice19/ionice-c3，scope MemoryMax=3G、CPUQuota=200%；分析前MemAvailable≥4GiB。最低MemAvailable=7198117888 B，最高实读cgroup memory.peak=544968704 B，资源终止=False；无OOM。原始meminfo/退出码/scope/ALL-END均保留。边界例外：无已知项目文件在WORKDIR外生成；systemd自身系统记账不属于项目输出。

完成后停止。本轮仅描述，不改变C、U、权重、任何门槛或资格；不登记修正案3，不做仿真、正式profile分析或板上工作。


## 13. v1.7 入库与静态重算（含修正稿前停止记录）

13.1–13.3 保留修正稿前的停止记录；该问题已由用户修正稿与13.4解决。最终结果见13.5–13.10。

### 13.1 入库及已完成项

设计 v1.7 从指定 Downloads 文件以 mv 移入；移动前后 SHA-256 均为
`4a72d97fd26174e3fd454b43adfb183b942a0ea6e90fbc4308ccf1cad78d842e`，源文件已不存在。
基线为 main 的 fbf317a41e254587e9ed7f8f7489b7f104ad60d3，fetch 后与 origin/main 一致。
旧设计、静态表和分类结果均保留；没有读取正式 sample profile，没有登记修正案3。

| 条款 | 修改前 | 本轮结果 |
|---|---|---|
| O.2.2#2 操作数按角色分流 | 已先按 MacroInfo 的 parameter_num 分出 definition/argument，定义体操作数直接来自唯一 X 的片段；缺 definition_body 证明路径标签 | 增加该标签，不改变判定条件；形参后续三分支不变 |
| P.5#20 定义体操作数夹具 | 未具名覆盖三种指定结构 | 新增 OPNAME ## _pixels8、a ## _ ## b ## c 正例与同文本异定义反例；全部通过 |
| O.2.3 LLVM 行表语义 | 旧 C 生成曾使用函数/selected-groups 过滤，不能直接沿用 | 核对源码 findRowInSeq：同一 sequence 中 upper_bound−1 取最后一条同地址记录；源码摘录及 SHA 已保存。新 C 生成器尚未实施 |

测试命令：`python3 -m unittest discover -s tools/profgen_eval -p 'test_*.py'`。
原161项保留并通过，新增3项synthetic，共164项通过。
证据：[tests-role](evidence/identity-gate/v17-recompute/tests-role/command.json)、
[测试原文](evidence/identity-gate/v17-recompute/tests-role/stderr.txt)、
[LLVM源码摘录及SHA](evidence/identity-gate/v17-recompute/compiler-source.txt)。

### 13.2 待裁决：C 输入独立性与宏生成行排除

原文证据：[domain-rule-conflict.txt](evidence/identity-gate/v17-recompute/domain-rule-conflict.txt)。

- O.2.3#2要求 C 只用两份调试ELF与C₀，不用任何身份结论；仅改变对应结论时C的SHA不变。
- O.2.3#3、5.8#5同时要求裁决2认定的宏生成函数行不进入C。P.5#20明确要求覆盖FNDA>0宏函数，不能以当前真实34项FNDA全为0代替此项验证。
- 最小合成逻辑反例：固定C₀中的一行（DA=1）与两份ELF，该行有有效可执行行表见证。若作为普通对应，应进入C；若仅改变对应结论为macro_generated_function，按排除条文则不进入C。不能同时保持SHA不变。
- 尚未采用的候选方向：将宏生成行的排除证明明确为独立于跨侧对应表、随C₀封存的参考/编译器事实，并定义允许输入、证明方法及优先级。这需要人工裁决，不能由实现暗中引入对应表。

[逻辑反例记录](evidence/identity-gate/v17-recompute/pending-domain-decision.json)是synthetic规则核对，不是真实profile分析。
本轮已提出澄清，等待裁决；不把“重算完成”写入STATUS。

### 13.3 未完成项与资源

| 工作 | 状态 |
|---|---|
| 新C、C_dc、U及三口径③、两个账本、domain_unresolved、四对象门槛/登记状态 | 未重算；依赖13.2裁决，旧结果不冒充v1.7结果 |
| inlined_call_site分类、完整无键重跑、特殊状态分类器、结论输出门禁、其余P.5#20夹具 | 未完成；保留到恢复执行 |
| 正式sample profile、修正案3、其他N.5/P.5任务 | 未打开、未登记、未开展 |

串行nice19/ionice-c3，systemd scope 3G/200%。两项记录作业启动时MemAvailable均≥4GiB；
记录范围为测试与源码/规则取证，轻量文件阅读没有单独峰值记录。
两项作业最低MemAvailable=5150109696字节，最高cgroup memory.peak=23052288字节；无资源终止。
资源与SHA索引：[summary.json](evidence/identity-gate/v17-recompute/summary.json)、[manifest.json](evidence/identity-gate/v17-recompute/manifest.json)。


### 13.4 修正稿与最终规则

用户裁决不另立宏事实输入。设计修正稿以mv替换，移动前后SHA均为
`9132af9a8242bdb7fa0a37aaf4f43b7eb2e06825fa6546309d5a3e46596ae092`；
Downloads源文件不存在，文档内容未改。替换提交为bc2dc60（“v1.7 修正稿，见附录 P.4 第7条”）；初次入库/停止记录提交为d632b45。

最终C生成不包含任何宏排除规则。宏生成身份仅从U排除该行，并在账本中加
macro_generated_function；无见证时与code_free_line组成完整原因集合。
实测宏函数68个（两侧各34），FNDA均0，身份结论全部不变；已执行宏函数的两个账本分支由synthetic夹具独立验证。
证据：[macro-recheck.json](evidence/identity-gate/v17-recompute/macro-recheck.json)。

| v1.7条款 | 修改前/复用部分 | 最终实现与验证 |
|---|---|---|
| O.2.2#2 | 已按定义体/形参角色分流；未标definition_body | token_paste_rule.py记录该证明路径；test_v17_paste.py三例通过；68个真实宏身份重新核对不变 |
| O.2.3#1–2 | 旧domain使用函数/selected-groups过滤，取原始行而非有效查询区间 | v17_domain.py的独立LLVM API工具只取ELF执行节及LineTable.Sequences；v17_rules.witnesses按序列相邻行构造半开区间，重复地址只保留末条，排除end_sequence与零长；不做函数、边界或键筛选 |
| O.2.3#2输入隔离 | 映射选择曾参与S见证 | C₀由C覆盖参考封存为file/line/DA；生成器仅使用该C₀与C/S两份调试ELF。现有inventory索引仅用于取得ELF路径，不读取其函数记录。各domain/index.json的admitted_domain_inputs列出三个输入SHA；static/index.json另列mapping_range_inputs_separate_from_C |
| O.2.3#3/P.4#7 | 旧稿宏排除与输入独立性冲突 | C不消费身份；v17_rules.ledger在U/账本阶段处理宏状态，保留完整原因集合。取证失败时domain_unresolved保守保留C并作为U损失，不能变成code_free；无法定位失败影响时保留所有尚未取得见证的C₀行 |
| O.2.3#5 | 旧描述无inlined_call_site | v17_calls.py直接遍历两份ELF的全部DIE，独立取得call_file/call_line；v17_classify.py复用已校验C命令AST/raw Lexer，在own_stmt之前加入内联调用点分类，不将分类结果反向用于C。own_stmt描述改为“未取得指令行归属见证” |
| O.2.4#3 | 已有全部顶层函数键枚举；旧apply以全量记录/无边界失败断言保证前置条件 | v17_key_audit.py重跑原独立helper，仍使用正式工具原样复制的键生成块；校验完整清单、全部范围、指令数量、符号化退出码和逐DIE记录。新增显式无键证明门禁；不完整证明按有键实例检查，不默认0豁免。旧入口默认行为保留 |
| 5.8#5特殊状态 | 无统一的受检条目分类接口 | v17_rules.classify_body按boundary→unknown_name→reference_unresolved→known_out_of_scope→unmapped_key→特殊已登记值→其他排除→U处理。仅synthetic输入验证，不读取真实body |
| 5.8#6结论域门禁 | 未有强制输出字段检查 | validate_conclusion/write_conclusion在打开文件前要求评价域原文、③三口径、③′、代码承载与非重复域外比例。static摘要实际通过门禁；缺字段既不创建文件也不覆盖旧文件 |
| P.5#20 | 原161项 | 原测试文件逐字节未改；新增44项（含3项拼接），共205项通过；完整名字见test-inventory.json |

LLVM22.1.8的DWARFDebugLine.cpp:1297–1316源码已核对：同sequence内通过upper_bound−1选择最后一条同地址记录。
SHA与原文见compiler-source.txt。新增C取证工具与callsite工具是独立程序，只链接GBS LLVM库，不修改或重编Clang。
C的定义理由分开：结构性重复计数修正对应asm/structural/expr三类；其余无见证行的排除是可测量性限定。行级结论**只覆盖固定构建中有指令行归属见证的行**，不推断其他构建也没有指令。

### 13.5 v1.6/v1.7对象登记表（只含静态参考量）

“可登记”仅为表内门槛状态；实际仍等待限定范围评审，未登记修正案3。
①=U行/C行，②=正DA的U行/全部已覆盖行，③′=ΣR(U)/覆盖全部DA。
④的RUN body比例仍未计算。

| 对象 | 规则 | C行 | ΣR(C) | U行 | ΣR(U) | ① | ② | ③′ | n_eff | K |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|spike Thumb|v1.6|75|11674422883|73|11673422882|97.333333%|61.206897%|53.354972%|1.328514991|19|
|spike Thumb|v1.7|75|11674422883|73|11673422882|97.333333%|61.206897%|53.354972%|1.328514991|19|
|spike A32|v1.6|74|11546422883|72|11545422882|97.297297%|60.344828%|52.769930%|1.299622728|10|
|spike A32|v1.7|74|11546422883|72|11545422882|97.297297%|60.344828%|52.769930%|1.299622728|10|
|FFmpeg Thumb|v1.6|7637|6890196397|6810|5870786315|89.171141%|53.614043%|17.232788%|22.607015895|465|
|FFmpeg Thumb|v1.7|7670|6908301525|6810|5870786315|88.787484%|53.614043%|17.232788%|22.607015895|465|
|FFmpeg A32|v1.6|7656|6889424103|6828|5856961473|89.184953%|53.671409%|17.192207%|22.643693057|464|
|FFmpeg A32|v1.7|7687|6912581744|6828|5856961473|88.825289%|53.671409%|17.192207%|22.643693057|464|

两侧spike的n_eff<3、K<50，按显式分支记录，K仅描述；不据本表输出任何RUN级统计结论。

| 对象 | 规则 | ③(C₀)：ΣR(U)/ΣR(C₀) | ③(C_dc)：ΣR(U)/ΣR(C_dc) | ③(C)：ΣR(U)/ΣR(C) |
|---|---|---|---|---|
|spike Thumb|v1.6|11673422882/21362787097 = 54.643726%|11673422882/16124041944 = 72.397622%|11673422882/11674422883 = 99.991434%|
|spike Thumb|v1.7|11673422882/21362787097 = 54.643726%|11673422882/16124041944 = 72.397622%|11673422882/11674422883 = 99.991434%|
|spike A32|v1.6|11545422882/21362787097 = 54.044553%|11545422882/16124041944 = 71.603776%|11545422882/11546422883 = 99.991339%|
|spike A32|v1.7|11545422882/21362787097 = 54.044553%|11545422882/16124041944 = 71.603776%|11545422882/11546422883 = 99.991339%|
|FFmpeg Thumb|v1.6|5870786315/28769855208 = 20.406034%|5870786315/11751913019 = 49.956006%|5870786315/6890196397 = 85.204920%|
|FFmpeg Thumb|v1.7|5870786315/28769855208 = 20.406034%|5870786315/11757799111 = 49.930997%|5870786315/6908301525 = 84.981617%|
|FFmpeg A32|v1.6|5856961473/28769855208 = 20.357980%|5856961473/11741913027 = 49.880811%|5856961473/6889424103 = 85.013804%|
|FFmpeg A32|v1.7|5856961473/28769855208 = 20.357980%|5856961473/11741913027 = 49.880811%|5856961473/6912581744 = 84.729001%|

FFmpeg的C_dc口径仍小于50%，C口径超过80%。门槛通过依赖可测量性限定；不称为对齐能力提升，也不把C_dc作为新的门槛。

| 对象（v1.7） | C_dc行 | 代码承载ΣR(C)/ΣR(C₀) | 非重复域外ΣR(C_dc\C)/ΣR(C_dc) | domain_unresolved行/DA |
|---|---:|---|---|---|
|spike Thumb|94|11674422883/21362787097 = 54.648407%|4449619061/16124041944 = 27.596176%|0/0|
|spike A32|94|11546422883/21362787097 = 54.049234%|4577619061/16124041944 = 28.390022%|0/0|
|FFmpeg Thumb|10843|6908301525/28769855208 = 24.012292%|4849497586/11757799111 = 41.244943%|0/0|
|FFmpeg A32|10847|6912581744/28769855208 = 24.027169%|4829331283/11741913027 = 41.128999%|0/0|

### 13.6 三个1%门槛与登记状态

| 对象 | 规则 | identity_ambiguous 分子/分母 | unmatched_in_elf 分子/分母 | boundary_unavailable 分子/分母 | ③门槛 | 表内状态 |
|---|---|---|---|---|---|---|
|spike Thumb|v1.6|0/11674422883 = 0.000000%|0/11674422883 = 0.000000%|0/11674422883 = 0.000000%|≥80%|可登记（未实际登记）|
|spike Thumb|v1.7|0/11674422883 = 0.000000%|0/11674422883 = 0.000000%|0/11674422883 = 0.000000%|≥80%|可登记（未实际登记）|
|spike A32|v1.6|0/11546422883 = 0.000000%|0/11546422883 = 0.000000%|0/11546422883 = 0.000000%|≥80%|可登记（未实际登记）|
|spike A32|v1.7|0/11546422883 = 0.000000%|0/11546422883 = 0.000000%|0/11546422883 = 0.000000%|≥80%|可登记（未实际登记）|
|FFmpeg Thumb|v1.6|15555/6890196397 = 0.000226%|26367/6890196397 = 0.000383%|0/6890196397 = 0.000000%|≥80%|可登记（未实际登记）|
|FFmpeg Thumb|v1.7|15555/6908301525 = 0.000225%|26367/6908301525 = 0.000382%|0/6908301525 = 0.000000%|≥80%|可登记（未实际登记）|
|FFmpeg A32|v1.6|15555/6889424103 = 0.000226%|26367/6889424103 = 0.000383%|0/6889424103 = 0.000000%|≥80%|可登记（未实际登记）|
|FFmpeg A32|v1.7|15555/6912581744 = 0.000225%|26367/6912581744 = 0.000381%|0/6912581744 = 0.000000%|≥80%|可登记（未实际登记）|

所有门槛均未超限。四对象C→U与C₀→U的完整原因集合账本如下；每行只计一次，各账本差值均断言为0。

| 对象 | 账本 | 原因集合 | 行数 | DA |
|---|---|---|---:|---:|
|spike Thumb|C→U|no_key_line|2|1000001|
|spike Thumb|C₀→U|code_free_line, no_key_line|47|9688364214|
|spike Thumb|C₀→U|no_key_line|2|1000001|
|spike A32|C→U|no_key_line|2|1000001|
|spike A32|C₀→U|code_free_line, no_key_line|48|9816364214|
|spike A32|C₀→U|no_key_line|2|1000001|
|FFmpeg Thumb|C→U|identity_ambiguous, no_key_line, unmatched_in_elf|6|15555|
|FFmpeg Thumb|C→U|no_key_line|683|743055974|
|FFmpeg Thumb|C→U|no_key_line, reference_ambiguity|17|31940587|
|FFmpeg Thumb|C→U|no_key_line, unmatched_in_elf|3|10812|
|FFmpeg Thumb|C→U|reference_ambiguity|151|262492282|
|FFmpeg Thumb|C₀→U|code_free_line, identity_ambiguous, no_key_line, reference_ambiguity, unmatched_in_elf|10|36|
|FFmpeg Thumb|C₀→U|code_free_line, identity_ambiguous, no_key_line, unmatched_in_elf|11|6258|
|FFmpeg Thumb|C₀→U|code_free_line, no_key_line|5190|21647225016|
|FFmpeg Thumb|C₀→U|code_free_line, no_key_line, reference_ambiguity|125|204258948|
|FFmpeg Thumb|C₀→U|code_free_line, no_key_line, unmatched_in_elf|34|10063425|
|FFmpeg Thumb|C₀→U|identity_ambiguous, no_key_line, unmatched_in_elf|6|15555|
|FFmpeg Thumb|C₀→U|no_key_line|683|743055974|
|FFmpeg Thumb|C₀→U|no_key_line, reference_ambiguity|17|31940587|
|FFmpeg Thumb|C₀→U|no_key_line, unmatched_in_elf|3|10812|
|FFmpeg Thumb|C₀→U|reference_ambiguity|151|262492282|
|FFmpeg A32|C→U|identity_ambiguous, no_key_line, unmatched_in_elf|6|15555|
|FFmpeg A32|C→U|no_key_line|685|754681035|
|FFmpeg A32|C→U|no_key_line, reference_ambiguity|18|38018090|
|FFmpeg A32|C→U|no_key_line, unmatched_in_elf|3|10812|
|FFmpeg A32|C→U|reference_ambiguity|147|262894779|
|FFmpeg A32|C₀→U|code_free_line, identity_ambiguous, no_key_line, reference_ambiguity, unmatched_in_elf|10|36|
|FFmpeg A32|C₀→U|code_free_line, identity_ambiguous, no_key_line, unmatched_in_elf|11|6258|
|FFmpeg A32|C₀→U|code_free_line, no_key_line|5170|21649424797|
|FFmpeg A32|C₀→U|code_free_line, no_key_line, reference_ambiguity|128|197778948|
|FFmpeg A32|C₀→U|code_free_line, no_key_line, unmatched_in_elf|34|10063425|
|FFmpeg A32|C₀→U|identity_ambiguous, no_key_line, unmatched_in_elf|6|15555|
|FFmpeg A32|C₀→U|no_key_line|685|754681035|
|FFmpeg A32|C₀→U|no_key_line, reference_ambiguity|18|38018090|
|FFmpeg A32|C₀→U|no_key_line, unmatched_in_elf|3|10812|
|FFmpeg A32|C₀→U|reference_ambiguity|147|262894779|

逐行账本、U及权重均在各对象static目录分片保存并登记SHA。当前真实宏FNDA全0，无宏执行量；有见证/无见证且FNDA>0的两个互斥账本分支均由synthetic验证，不伪造真实数据。

### 13.7 code_free描述分类

新C移出的目标是旧code_free的子集，因此复用624条原C命令的AST及raw Lexer原件；逐件核验SHA及旧Stmt/Expr一致性元数据，不需要再次编译源码。全部目标有AST与Lexer证据。

| 类别（行数 / DA） | spike Thumb | spike A32 | FFmpeg Thumb | FFmpeg A32 |
|---|---:|---:|---:|---:|
|asm_interior|0 / 0|0 / 0|68 / 14050578484|68 / 14050578484|
|structural_line|28 / 5238745153|28 / 5238745153|2104 / 2961475814|2100 / 2977361898|
|expr_continuation|0 / 0|0 / 0|25 / 1799|25 / 1799|
|inlined_call_site|1 / 1|1 / 1|327 / 173856712|335 / 175649375|
|own_stmt_no_code|18 / 4449619060|19 / 4577619060|2697 / 4482119345|2676 / 4460160379|
|other|0 / 0|0 / 0|149 / 193521529|149 / 193521529|
|ast_unavailable|0 / 0|0 / 0|0 / 0|0 / 0|

每类占C₀/C的分子分母、own_stmt语句种类、逐行token/AST/callsite证据和top20见classification/summary.json及CSV分片。own_stmt仅表示未取得指令行归属见证；other保留原因，未推断其优化机制。两份构建所有inlined_subroutine的call属性均独立收集，包含lexical block下的节点。

### 13.8 全量键证明、变化行与独立性

| 对象 | 完整有代码DIE | 全部顶层组 | 枚举指令出现数 | 已证明无键实例 | 普通候选豁免实例 | 失败顶层组 |
|---|---:|---:|---:|---:|---:|---:|
|spike Thumb|17|9|385|0|0|0|
|spike A32|17|9|386|0|0|0|
|FFmpeg Thumb|28149|4630|1046243|965|928|0|
|FFmpeg A32|28190|4633|1026941|963|925|0|

四份新键证明原始输出与旧输出SHA完全相同；普通候选所有组结论完全相同。边界失败/漏范围/缺记录/符号化失败在synthetic中不得获得豁免；整组无键时完整参考质量进入no_key_line。

| 对象 | 新增C行/DA | 新增行进入U：行/DA | 移出C行/DA | S有被接受键却不在C的C₀行/DA |
|---|---|---|---|---|
|spike Thumb|0/0|0/0|0/0|0/0|
|spike A32|0/0|0/0|0/0|0/0|
|FFmpeg Thumb|33/18105128|0/0|0/0|0/0|
|FFmpeg A32|31/23157641|0/0|0/0|0/0|

新增行逐项列于static/added-C分片，均以原有键/身份证据判损失，没有静默删除。每对象三次重放使用完全相同C₀与ELF派生行表，只改变合成的外部对应/键/映射范围状态，C SHA均不变；另对实际见证行作DA=1的明确synthetic宏状态切换，只有U/账本变化。证据为各对象invariance.json。C⊆C_dc⊆C₀及U⊆C均有运行时断言。

### 13.9 验收、资源与证据索引

205项测试通过（原161项逐文件未变，新增44项）。完整测试名、原文、源代码与输入SHA分别见test-inventory.json、tests-final-205/stderr.txt、final-manifest.json和各命令记录。旧ruling3-4、ruling3-rev1及code-free-v2产物git差异为空；旧路径输出未覆盖。

所有记录作业串行、nice19/ionice-c3、systemd scope MemoryMax=3G / CPUQuota=200%；启动检查MemAvailable≥4GiB。记录最低MemAvailable=5150109696字节（4.796GiB），峰值cgroup memory.peak=1302265856字节（1241.938MiB）；无资源终止，所有记录作业退出0。原始meminfo与scope记录在各*-run/和作业目录。轻量文件编辑/阅读没有逐条独立峰值记录，峰值统计范围为带run_scoped记录的作业。

- spike Thumb：[对象表/两个账本](evidence/identity-gate/v17-recompute/spike-thumb-static/comparison.json)；[C输入SHA](evidence/identity-gate/v17-recompute/spike-thumb-domain/index.json)；[描述分类](evidence/identity-gate/v17-recompute/spike-thumb-classification/summary.json)；[全部顶层键证明](evidence/identity-gate/v17-recompute/spike-thumb-key-audit/summary.json)。
- spike A32：[对象表/两个账本](evidence/identity-gate/v17-recompute/spike-a32-static/comparison.json)；[C输入SHA](evidence/identity-gate/v17-recompute/spike-a32-domain/index.json)；[描述分类](evidence/identity-gate/v17-recompute/spike-a32-classification/summary.json)；[全部顶层键证明](evidence/identity-gate/v17-recompute/spike-a32-key-audit/summary.json)。
- FFmpeg Thumb：[对象表/两个账本](evidence/identity-gate/v17-recompute/ffmpeg-thumb-static/comparison.json)；[C输入SHA](evidence/identity-gate/v17-recompute/ffmpeg-thumb-domain/index.json)；[描述分类](evidence/identity-gate/v17-recompute/ffmpeg-thumb-classification/summary.json)；[全部顶层键证明](evidence/identity-gate/v17-recompute/ffmpeg-thumb-key-audit/summary.json)。
- FFmpeg A32：[对象表/两个账本](evidence/identity-gate/v17-recompute/ffmpeg-a32-static/comparison.json)；[C输入SHA](evidence/identity-gate/v17-recompute/ffmpeg-a32-domain/index.json)；[描述分类](evidence/identity-gate/v17-recompute/ffmpeg-a32-classification/summary.json)；[全部顶层键证明](evidence/identity-gate/v17-recompute/ffmpeg-a32-key-audit/summary.json)。

大的新原始行表、callsite、键证明与独立工具产物只在temp/prep-v17/；各command/index记录路径与SHA。复用的大AST/Lexer仍在temp/prep-code-free-v2/，SHA来源登记于classification摘要。仓库新增证据每个小于1MB。

### 13.10 本阶段结束

按v1.7修正稿完成本任务指定的静态重算，等待限定范围评审后再决定后续；不登记修正案3，不进入其他N.5/P.5项目。未连接开发板，未打开任何正式sample profile，未计算任何RUN级受控量；宏/条目分类/结论门禁的动态形态用例全部是synthetic。
