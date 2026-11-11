# N.5 阶段1身份门禁与覆盖：补充3停止记录

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
