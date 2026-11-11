# 登记前准备人工裁决

## 裁决 1：system_header_no_reference

- 背景：被采样 ELF 中有来自系统头的函数（例如 /usr/include/bits/string_fortified.h 的 memcpy），CU 的 producer 为评估所用的 clang 22.1.8，有代码与 DWARF，但 C 覆盖参考没有候选。原因是 clang 生成覆盖映射时默认跳过系统头，参考侧不存在这些行的计数；这与"未插桩"不同，属于评价域外，处理方式同宏展开区域。
- 新增对应表结论状态 system_header_no_reference，须同时满足以下正面证据，任一缺失仍保留为没有结论：
  ① 该函数的规范化 decl_file 位于该 CU 编译时的系统头目录之下。系统头目录取自 C 构建与 S 构建的实际编译命令（-isystem、--sysroot 与该 clang 的默认系统头目录，用同一 clang 的 -v 输出核对），两侧须一致。
  ② C 构建的编译命令没有打开系统头覆盖（没有 -mllvm -system-headers-coverage 或等价选项），并在 LLVM 22.1.8 源码中给出跳过系统头的代码位置（clang/lib/CodeGen/CoverageMappingGen.cpp 中 SystemHeadersCoverage 相关判断，写出文件与行号）。
  ③ 覆盖导出的文件表中没有位于这些系统头目录之下的文件（全局核对，一旦出现则本规则不适用，停止并报告）。
  ④ 该函数没有任何参考候选（有候选的一律走原来的对应规则）。
- 处理语义：键照常进入映射表，值记为 system_header_no_reference；条目计入"已对齐但不在 U 内"，单列原因"系统头"，不算未对齐，不进入 U，也不进入 ③ 的分母 C。顶层组的内联树中只含 system_header_no_reference、not_instrumented 与参考侧未执行函数时，归为 known_out_of_scope；内联树中含已执行参考函数的组仍在映射范围内。
- 局限：内联进用户函数的系统头代码不参与行级指标，登记文本写明。
- 本裁决在 N.5 全部完成后与其他发现一起合入设计文档的登记版；在此之前以本文件为准。

## 裁决 2：macro_generated_function（宏生成的函数）
- 背景：FFmpeg 中有整个函数由宏展开生成的情形（例如 pixels.h 中的宏在 hpeldsp_init_arm.c:38 生成 ff_put_pixels16_x2_arm）。两侧 DWARF 的声明位置在宏展开处，覆盖侧函数体的区域全部在宏定义所在文件，按 findMainViewFileID 得到的主文件因此与 decl_file 不同。这是同一函数，身份可以证明；但参考行在宏定义文件中，sample 侧的行号记在展开处，行级不能对齐，按 5.8 第 5 条对宏展开区域的处理，不进入 U。
- 建立对应须同时满足以下正面证据，任一缺失仍保留为没有结论：
  ① 名字精确一致：内部链接函数，覆盖记录的 PGO 名字形如 "<TU 文件>:<linkage name>"，其中 TU 文件（规范化后）等于该 DWARF 函数所在 CU 的源文件，且 linkage name 连同 .__uniq. 后缀与 DWARF 侧完全相同（这里不去后缀）；外部链接函数没有 TU 前缀与后缀时，要求 linkage name 完全相同，且在覆盖记录中、在被采样 ELF 的 DWARF 顶层定义中都唯一。
  ② 定义声明位置一致：C 构建 DWARF 中该函数的 decl_file 与 decl_line，与被采样侧 DWARF 的完全相同。
  ③ 宏生成的证据：该覆盖记录在 decl_file 中没有任何代码区域，全部代码区域都在另一个文件中；并且源码中 decl_file 的 decl_line 处是一个宏调用，其定义位于覆盖主文件中（给出宏名与两处源码行作为证据）。
  ④ 该函数不满足 v1.5 原规则下的普通对应（即确属"同名、文件不同"类）。
- 处理语义：身份对应成立，执行与否按该记录的 FNDA，进入组的映射范围判断时与普通对应相同（FNDA > 0 视为已执行参考函数，否则视为参考侧未执行）。该函数的参考行全部视为宏展开区域：不进入 U，不进入 ③ 的分母 C；其 DA 计入 ③′ 的说明（宏展开部分）。sample 侧落在这些函数上的条目计入"已对齐但不在 U 内"，单列原因"宏生成的函数"，不算未对齐。
- 登记前报告：闭合的函数清单、每个函数的宏名与两处源码行、FNDA，以及其中 FNDA > 0 的函数的 DA 之和（这部分是评价域外的执行量）。
- 本裁决在 N.5 全部完成后与其他发现一起合入设计文档的登记版；在此之前以本文件为准。

### 补充 1

补充 1-①：覆盖 PGO 名字中的 TU 前缀只有 basename 时
- 先给出这一格式的来源：在 LLVM 22.1.8 源码中找出内部链接函数 PGO 名字前缀的生成位置（文件与行号），并用 C 构建的实际编译命令说明为什么得到的是 basename。若源码与命令不能解释 basename，停下报告，不要继续配对。
- 允许用 C 构建的实际编译命令建立"覆盖前缀 → 完整 CU 源文件路径"的显式映射：前缀须等于某条实际编译命令的源文件 basename，且该编译产物被链接进被采样的库。映射表随证据保存（前缀、完整路径、编译命令的日志路径与行号）。
- 唯一性：同一 basename 只对应一个 CU 时直接映射。对应多个 CU 时，只有恰好其中一个 CU 的 DWARF 中存在与覆盖记录完整 linkage name（含 .__uniq. 后缀）完全相同的定义，才算唯一；否则保留未决。
- 在任何情况下，完整 linkage name（含 .__uniq. 后缀）都必须两侧完全相同；不得只按 basename 或去后缀的名字配对。

补充 1-③：宏生成的证据可以是完整的宏展开链
- 直接调用的宏定义在 decl_file 中、再经一层或多层宏展开才到覆盖主文件（例如 DEF_PEL/PIXOP2 → CALL_2X_PIXELS → pixels.h）时，允许以完整的展开链作为③的证据。
- 证据必须由编译器生成：用 C 构建该 CU 的实际编译命令（GBS root 中的 clang，同一预处理定义），导出该函数声明的 AST（含源码位置），其中函数体各语句的拼写位置在覆盖主文件中、展开位置指向 decl_file 的 decl_line 处的宏调用；同时列出链上每一层宏的名字与定义位置（文件与行号）。只靠文本搜索得到的链不算证据。
- 仍须满足：该覆盖记录在 decl_file 中没有任何代码区域。
- 夹具：两层宏链（闭合）；链上某层定义位置与 AST 不符（未决）；只有文本搜索证据没有 AST（未决）；函数体部分语句的拼写位置在 decl_file 中（不适用，走原规则）。

### 补充 2：宏实参的拼写位置

替换补充 1-③ 中"函数体各语句的拼写位置在覆盖主文件中"这一要求，其余不变。

- 以 AST/token 证据逐个 token 判定（用 C 构建该 CU 的实际编译命令、GBS root 中的 clang）：
  ① 拼写位置不在覆盖主文件中的 token，必须全部由 clang 标为宏实参展开（SourceManager::isMacroArgExpansion 为真），并且其拼写位置只能落在以下两处之一：decl_file 的 decl_line 处那一次宏调用的实参范围内；或已记录的展开链上某一层宏的定义体内（中间宏把实参传给下一层宏的情形）。
  ② 非实参 token（语句结构、关键字、运算符、标点等由宏定义体提供的部分）的拼写位置必须全部在覆盖主文件中。
  ③ 覆盖记录在 decl_file 中没有任何代码区域（不变）。
- 三项都满足时，补充 1-③ 的宏生成证据成立；任一不满足时：非实参 token 拼写在 decl_file 中的，不适用本裁决，走原规则；实参 token 的拼写位置落在调用范围与展开链之外，或 isMacroArgExpansion 证据缺失的，保留未决。
- 证据保存：每个闭合函数的 token 清单（拼写位置、展开位置、isMacroArgExpansion、所属宏层级）、调用的实参范围、展开链各层的定义位置，以及原始 AST/token 输出与 SHA。
- 夹具：ff_put_pixels16_x2_arm 实例（实参 ff_put_pixels8_x2_arm 与 8 拼写在调用处，其余在 pixels.h → 闭合）；DEF_PEL/PIXOP2 两层链中由中间宏定义体传下的实参（闭合）；某个运算符或语句关键字拼写在 decl_file（不适用，走原规则）；实参 token 拼写在调用范围与展开链之外的第三个文件（未决）；缺少 isMacroArgExpansion 证据（未决）。

## 裁决2 补充3

适用对象：补充2判定中，拼写位置为 scratch buffer（presumed_file=`<scratch space>`）、因而判为 argument_spelling_outside_allowed_ranges 的 token。补充3只替代这类 token 的“拼写位置”条件；裁决2和补充1、补充2的其他所有条件不变（TU、linkage、声明、唯一性、组范围、AST、逐token标志、非实参token规则、coverage region规则）。FNDA 不得替代任何一步。

一个 scratch token T 通过补充3，当且仅当以下全部由编译器 API 的实测数据给出（不得用文本搜索、正则或 trace 推断替代）：

1. 拼接层唯一：在 T 的位置链中，恰好有一层的 immediate spelling 是 scratch 的 FileID 位置（is_macro=false、is_scratch=true），称为拼接层 L。若有 0 层或多层，判未决。
2. 拼接范围：对 L 调用 SourceManager::getImmediateExpansionRange，得到 [B,E]。B 和 E 都必须是宏位置，且属于同一个宏展开实例 X。X 必须能与插件记录的 MacroExpands 回调一一对应：宏名相同，展开位置 raw 值相同。
3. 定义体内：B 和 E 的 spelling 必须都落在 X 的 MacroInfo 的定义范围 [DefinitionLoc, DefinitionEndLoc] 内，且 X 位于该函数已记录的展开链上。
4. 拼接结构：从 X 的 MacroInfo::tokens() 中按位置取出 [B, E] 所覆盖的定义 token（E 是最后一个操作数的起始位置）。这段 token 必须严格符合“操作数 (tok::hashhash 操作数)+”。以下情况判未决：
   - 出现字符串化 `#`；
   - GNU 逗号拼接 `, ## __VA_ARGS__`；
   - MSVCCompat。
5. 操作数解析：
   (a) 若操作数是 X 的形参（MacroInfo::getParameterNum），则取 X 的 MacroArgs 中对应的“未展开”实参 token，在回调时复制保存，含 SourceLocation。该实参必须恰好是 1 个 token；空实参（placemarker）或多 token，判未决。
   (b) 否则，操作数就是定义体 token 本身。
6. 文本一致：按顺序把各操作数的 Preprocessor::getSpelling 拼起来，结果必须与 T 的文本逐字节相等。T 和每个中间结果的 kind 只能是 identifier 或 numeric_constant。
7. 操作数来源（递归）：
   - 定义体操作数：满足第3条即可。
   - 实参操作数：用该 token 自己的位置链按补充2的规则判定，即 isMacroArgExpansion 标志、调用实参范围、已记录展开链定义体、非实参须在 coverage 主文件。
   - 若实参操作数本身也是 scratch token（嵌套拼接，例如 DEF_PEL→FUNCC→FUNC2→FUNC3），则对它递归应用补充3。递归深度上限为 8，超过判未决。
8. 证据：每个 scratch token 输出完整的证明记录：
   - L 与 [B,E] 的 raw/presumed 位置；
   - X 的身份；
   - 定义 token 片段；
   - 每个操作数的来源与位置链；
   - 拼接后的文本与 T 的比对；
   - 递归子证明。
   任何一项缺失，判未决，原因码写具体项，不要笼统写 argument_spelling_outside_allowed_ranges。

前提核验（先做；不成立就停止报告，不实施规则）：在 GBS 根目录的 clang 22.1.8 源码中，找到 TokenLexer::pasteTokens 末尾为拼接结果创建 expansion location 的代码，即把起止位置映射到当前展开（getExpansionLocForMacroDefLoc / createExpansionLoc）。确认第2条所依据的语义确实成立：拼接层的 immediate expansion range 覆盖从首操作数到末操作数起点的 `##` 表达式。把原文行号和 SHA 追加进 compiler-source.txt。若语义与上述不符，停止并报告。


## 裁决2 补充3 修订1

背景：补充3第5(a)条取的是 MacroArgs 中的未展开实参。如果这个实参直接写在宏调用处，它在 Clang 中是物理文件的 FileID 位置（SourceManager.cpp:984–986：非 MacroID 位置，isMacroArgExpansion 恒为 false）。原第7条要求“用 token 自身位置链按补充2规则判定”，与第5(a)条矛盾。这是规则缺陷，不是证据缺失。

修订：第7条中的“实参操作数”分三种情况，按 token 自身的 SourceLocation 判定：
(i) 宏位置（MacroID）：按原第7条处理，即用自身位置链套补充2规则。若其拼写位置是 scratch，按原规则递归应用补充3。
(ii) 物理文件位置（FileID，且不是 scratch）：改用“直接调用实参”证明，必须同时满足：
   a. 该 token 是从唯一实例 X 的 MacroArgs 槽位 n 取得的（n = MacroInfo::getParameterNum(该形参)，在 MacroExpands 回调时复制），且该槽位恰好只有这 1 个 token；
   b. X 是本函数已记录展开链上的调用实例，且 X 的调用位置本身满足补充2对调用位置的要求，即它就是已记录的 invocation；
   c. token 的拼写区间 [offset, offset+len) 完整落在 X 这次调用中第 n 个实参的区间内。这个区间按槽位切：只包含第 n 个实参自己的 token，不含括号和分隔逗号。用整个调用的实参总范围代替判定无效；
   d. token 与 X 调用的名字位置（name_location）在同一个 FileID 中；
   e. 证据如实记录 isMacroArgExpansion=false，不得改写成 true。证明路径写成 `direct_unexpanded_argument_slot`，并写明槽位 n 及该槽位区间的 raw/offset。
(iii) scratch 的 FileID 位置：按原规则递归应用补充3。
其他情况一律判未决：取不到槽位、槽位多 token 或为空、区间不在第 n 个槽位内、跨 FileID、X 不在链上，等等。
本修订不改变补充2对函数体内“非实参 token 必须在 coverage 主文件”的规则；它只适用于从 MacroArgs 槽位取得的拼接操作数。


## 裁决3、裁决4（2026-11-11；待折入 v1.6 并经三家评审）

这是 v1.5 5.8 第5条“③<50% 时先修订本条”的修订，后续折入 v1.6 并经三家评审后才可登记。

裁决3：③ 的行域 C 限定为“承载代码的行”
- 背景：覆盖导出给区域跨越的每一行都记计数。多行语句的续行（例如 arm/cabac.h 中内联汇编字符串的第37–102行）在任何构建的行表里都不可能有指令，它们的计数与语句首行是同一次执行，计入 C 会重复计数。这和 v1.5 排除宏定义行的理由相同。
- 规则：某个（文件、行）进入 C，除满足 v1.5 原条件外，还必须在 C 构建自己的调试 ELF 行表中，至少有一行行号非 0 的行表记录，且该记录的地址落在某个已执行参考源函数的代码区间内（作为叶子帧即可）。只用 C 构建的数据，不得使用被采样 ELF（S）的行表或映射来决定 C。
- U ⊆ C 的关系不变：S 有键、但不在新 C 中的行不进入 U，必须计数并列明细。
- ③′、①、② 的分母按各自原定义执行；凡原定义引用 C 的，改用新 C。
- 被移出 C 的行全部归入新的损失类别 code_free_line（只用于报告，不参与 1% 门槛），按文件给出行数和 DA 明细。

裁决4：单候选检查第②项中，空叶子行集合的处理

> 以下 no_code_instance 及相关组判定为原裁决历史记录；已由下方“裁决4 修订1”替换。
- 第②项检查的行集合改为：该 DWARF 实例以自身为叶子帧、文件等于 decl_file 的行表行号，并上其直接子 inlined_subroutine 的 DW_AT_call_line（仅限 DW_AT_call_file 等于 decl_file 的）。范围判定仍为 [min(decl_line, 候选起始行), 候选结束行]。
- 合并后行集合非空：按原规则判定通过或越界。
- 合并后行集合为空，且该实例连同所有后代都没有任何地址区间：记为 no_code_instance。这种实例不产生任何键，也不出现在任何键的上下文中，因此不参与本组的身份判定。
- 合并后行集合为空，但实例或其后代有地址区间：仍按原规则记为失败，不放宽。
- 组判定：第①项（定义身份）对全部实例照旧检查。不计 no_code_instance 时，只要至少一个实例的第②项通过、且没有任何实例出现越界或上一条那种失败，本组就建立对应。如果组内全部是 no_code_instance，本组不产生键：它的参考行记为 no_key_line，不记 identity_ambiguous；对应的已执行参考源函数记为“已对应但无键”，不算 unmatched_in_elf。
- 越界（leaf_line_outside_range）的规则不变。


### 裁决4 修订1（2026-11-11；替换原裁决4中 no_code_instance 的相关部分）

一、范围：不扩大清单
身份核对的实例范围仍是原完整清单，即有地址区间的 DIE。不把无代码的定义 DIE（包括 DW_AT_inline 抽象源）纳入组判定。
理由：inlined_subroutine 实例的名字和声明位置本来就经 abstract_origin 链取自抽象源，第①项对实例的检查已经覆盖了抽象源的声明位置；没有具体实例的抽象源不产生任何键，与样本归属无关。
需要在证据中确认：每个 inlined_subroutine 实例的 decl_file/decl_line 确实经 abstract_origin 链取得，列出取值路径。

二、“无键实例”取代 no_code_instance
按工具的键规则（行号为 0 不产生键）定义如下：
1. 无键实例：实例自身作为叶子帧的全部行表行号都是 0（或没有自身叶子行），并且它的全部后代 inlined_subroutine 也是如此（也就是说，以它为值或以它为上下文帧的键一个都没有）。
   无键实例不参与本组判定，单独计数报告；第①项照常检查，失败时照常记录。
2. 自身没有非 0 叶子行，但后代产生键：按原裁决4，用直接子 inlined_subroutine 的 DW_AT_call_line（限 DW_AT_call_file 等于 decl_file）作为第②项的行集合。
   在范围内判为通过。越界、调用行在其他文件、或没有符合条件的调用行，判为失败（不放宽）。
3. 自身有非 0 叶子行：按原规则判定，行集合并上第2条的调用行。
4. 自身叶子行全部落在其他文件（非 decl_file，且行号非 0）：判为失败，不放宽。

三、组判定
第①项对全部实例检查。排除无键实例后，至少一个实例第②项通过，且没有实例按第2–4条失败，则本组建立对应。
组内全部是无键实例：本组不产生键，参考行记为 no_key_line，已执行参考源函数记为“已对应但无键”，不算 unmatched_in_elf。

四、证据要求（加在原任务第二、三部分之上）
1. 对现有 69 个空叶子行集合组（Thumb，A32 同样处理），把每个实例分到以下四类之一，报告每类的实例数、组数和 DA：
   a. 自身与后代全为行号 0（无键）；
   b. 自身无叶子行、后代有键，且调用行在 decl_file；
   c. 自身无叶子行、后代有键，但调用行在其他文件；
   d. 自身叶子行在其他文件。
   每类给 3 个完整实例：DIE、地址区间、行表原始行、子 inlined_subroutine 的 call_file/call_line。
2. 夹具中的“完全无代码实例”一项改为“有地址、但自身与后代全为行号 0”；另加一项“自身叶子行在其他文件，判为失败”。

### 裁决4 修订2（补充修订1第二部分的“无键实例”定义）

一、“产生键”的口径
以工具的键规则为准：一个地址的完整内联上下文中，叶子帧或任一非叶子帧的行号为 0，该键被拒绝。必须使用静态映射中与正式工具相同的键生成代码判定，不另写近似规则。

二、无键实例（替换修订1第二部分第1条）
在静态映射中，没有任何一个被接受的键把该实例作为叶子帧或上下文帧，该实例即为无键实例。
因此，后代叶子行非零、但所有完整上下文都因非叶子帧行号为 0 而被拒绝的实例（如 get_bits_long：子 get_bits 叶子行 340，调用行 0），属于无键实例。

三、无键实例的豁免条件（三条都要满足，否则判失败）
1. 第①项（定义身份）通过。
2. 现有行号证据不得指向错误定义：
   - 自身在 decl_file 中行号非 0 的叶子行（不论键是否被接受）；
   - 直接子 inlined_subroutine 在 decl_file 中行号非 0 的 DW_AT_call_line。
   上述任一行落在 [min(decl_line, 候选起始行), 候选结束行] 之外，即判失败。证据集合为空时，本项视为满足。
3. 自身不存在落在其他文件、行号非 0 的叶子行。存在则判失败，与修订1第4条一致，不因无键而放宽。

满足以上三条的无键实例不参与本组判定，单独计数报告。
修订1第2–4条（有键实例的检查）以及组判定规则不变。

四、证据要求（在修订1第四部分之上增加）
1. 新增第 e 类：后代有非零叶子行，但全部上下文因非叶子帧行号为 0 被拒绝。报告 Thumb 47 个、A32 52 个实例所在的组数及其 DA，给 3 个完整实例：
   - 逐地址的完整上下文；
   - 被拒绝的帧及其行号来源（DW_AT_call_line 原值）；
   - 第三部分第2、3条的证据集合和判定结果。
2. a–e 五类各给出：最终判定（豁免 / 通过 / 失败）的实例数、组数、DA。
3. 夹具增加两项：
   - “后代叶子行非零但上下文行号为 0，证据集合为空”判为豁免；
   - “同上，但自身在 decl_file 中有一条越界的非零叶子行”判为失败。

确认后继续：先实施裁决4，再按新旧规则并列重算 U/③ 及全部门槛，完成后按原停止条件停下。
