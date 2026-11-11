【最高原则（必须遵守，违反即视为任务失败）】
工作目录：/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/（下文称 WORKDIR）
1. 开发测试过程中产生的所有文件只能创建在 WORKDIR 内，不得在其他任何地方生成文件。
   - 包括临时文件、缓存、下载内容、克隆的仓库、日志。
   - 临时文件和数据一律放 WORKDIR/temp/。
2. 不得使用 WORKDIR 以外的任何文件。
   - 不读取、不引用、不复制其他目录下的源码、配置、脚本或数据。
   - 系统自带的命令行工具（git、sdb、readelf、curl 等）本身可以执行。
   - 需要的源码与配置只从 WORKDIR/src、WORKDIR/config 取；网络上的公开仓库只能克隆到 WORKDIR/temp/ 内。
3. 落实方式：
   - 所有命令执行前 export TMPDIR=WORKDIR/temp/tmp（先创建该目录）。
   - git 只用仓库内配置（git config --local），不修改全局 git 配置。
   - 不做 pip / npm / apt 等任何安装；缺工具就停下，在报告里说明。
   - 任何工具若自行在 WORKDIR 外写了东西（例如 sdb 服务自身的状态文件），不要隐瞒，在报告的"边界例外"一节如实列出：路径、哪个工具写的、能否避免。
   - 检查上一次中断的执行有没有在 WORKDIR 外留下文件；有就列进"边界例外"，不要自行删除。
4. 开发板上无法写入 WORKDIR，所以板上只允许写 /tmp/afdo_probe/，结束时删除。

## 长期规则澄清（用户后续指令；优先于上述文字的歧义解释）

1. "不得使用 WORKDIR 以外的任何文件"约束的是项目的输入与产出：源码、配置、数据、脚本只能取自 WORKDIR，生成的文件只能落在 WORKDIR。它不禁止使用本机已有的 GitHub 推送认证。
2. 环境隔离（例如改 HOME、GIT_CONFIG_NOSYSTEM 等）只用于 gbs 相关命令（export、build 及其派生进程），本轮没有 gbs 命令，因此本轮不需要任何隔离。
3. 本项目结果仓库（autofdo_bolt_agent）的 git commit 与 git push 一律在正常环境下执行，使用本机已有的 GitHub 认证。提交署名仍用 git config --local 设置的 Hao Lin <hao.lin@samsung.com>，不修改全局 git 配置。

4. 以后用户放在 Downloads 的材料一律移动到工作目录，不在 Downloads 保留副本；只处理用户指定的材料，不遍历或触碰其他文件。
5. llvm-profgen 增强设计须经多方评审并冻结后才开工；Agent 的设计与开发在 llvm-profgen 增强完成后才开始。

推送仍失败时：原样记录报错后停下，不索要令牌，不修改任何认证配置。

## 当前设计状态（v1.5定稿；登记前准备第一阶段）

- [设计v1.5](profgen/design/02_llvm_profgen_enhance_design_v1.5.md)定稿，按人工裁决不再评审设计；进入附录N.5登记前准备第一阶段。
- 修订3未登记；未计算任何正式 sample profile 的受控量。
- 本阶段只使用静态ELF/调试文件、C构建覆盖参考与源码；不连接板子，不打开或转换正式sample profile（含CALIBRATION）。
- v1.5文件SHA-256：be18d105d5711861b08517004d97eb40de5fb37b92213202cddd6b759fa9e636；从Downloads以mv移入，无同SHA重复副本，旧版本不动。


## 人工裁决（登记前准备）

- [裁决2补充3修订1](profgen/eval/prep/rulings.md)：直接未展开FileID实参以唯一MacroArgs槽位、该槽位的编译器区间、调用实例及同FileID证明来源，保留isMacroArgExpansion=false；不改变补充2物理函数体token规则。先登记，再实施与验收，身份门禁通过前不计算U/③。

- [裁决2补充3](profgen/eval/prep/rulings.md)：仅scratch token允许按编译器API的唯一拼接层、展开实例、定义片段、未展开实参、文本与递归来源证明替代拼写位置条件；其余规则不变。实际GBS bind工作树TokenLexer.cpp:895–914前提核验通过；真实未展开实参的FileID标志与规则7冲突，执行状态见下。

- [裁决2补充2](profgen/eval/prep/rulings.md)：宏拼写条件改为逐token校验；仅有clang isMacroArgExpansion正面证据、且位于指定调用实参或已记录宏定义体内的实参允许跨文件，其他条件不变。

- [裁决2补充1](profgen/eval/prep/rulings.md)：PGO basename须由编译命令、链接输入和完整linkage唯一消歧；宏链须同一C命令的编译器AST证明，文本搜索不能独立闭合。

- [裁决2：macro_generated_function](profgen/eval/prep/rulings.md)：宏生成函数须四项正面证据齐全才建立身份对应；参考行属于宏展开评价域外，FNDA决定组范围。先照录登记，后实现核对；不扩大原not_instrumented规则。

- [裁决1：system_header_no_reference](profgen/eval/prep/rulings.md)：系统头无覆盖参考是评价域外；仅四项正面证据全部满足时给出该封闭状态，不能扩大not_instrumented。本轮先核对编译命令、系统头目录与覆盖全局文件表；仍不打开正式sample profile。若有其他未决类别，停止并报告。

## 裁决2补充3修订1执行状态（2026-11-11）

- 修订1已照录推送b17c93f；正式classifier接入完成，旧物理token规则不变。每个MacroArgs槽位用回调token位置/长度证明半开区间，保留false标志。
- Thumb/A32各28条新闭合，未决0，FNDA均0，scope_role=reference_unexecuted；含既有6条后宏对应各34条。三例真实断言退出0。原27项及新增19项synthetic测试通过；初次夹具失误原文保留。[04§8.7](profgen/eval/prep/04_macro_function_ruling.md)
- 下一步普通候选：Thumb26841、A3226876、spike各15。未把候选当闭合；U、③、损失分解未计算。正式sample profile未打开，修正案3未登记。[05门禁](profgen/eval/prep/05_identity_gate_and_coverage.md)

## 裁决2补充3执行状态（2026-11-11；未展开实参标志停止）

- 裁决原文与TokenLexer前提已提交推送d79e285；GBS源码bind目录当前为空，核对实际bind工作树与f999源文件SHA一致，:895–914范围语义成立。[04报告§8](profgen/eval/prep/04_macro_function_ruling.md)
- 插件扩展公开API取证，Thumb/A32各5个CU退出0。共56个记录/112个scratch token全量核对，第1–6条与递归文本可证明；每侧28个记录在第7条失败：MacroArgs未展开直接实参put/avg为FileID、isMacroArgExpansion=false，虽然落在调用实参范围，却不在coverage主文件。具体原因paste_argument_nonmacro_outside_main；FNDA全部0，不替代证据。
- 原27项测试保留并重跑通过；两个必过真实例失败，第三个独立源码实例同样失败，真实断言退出1。新增11项合成夹具及正式classifier接入未完成；macro_function_rule.py未改，不扩大补充2物理token规则。
- 待裁决：是否允许“唯一X的MacroArgs槽位＋精确调用实参范围”证明这种未展开FileID操作数，保留真实false标志。未裁决前停止。普通候选（Thumb26841/A3226876/spike各15）、U、③、损失分解与静态规模均未继续；既有身份计数不变。[门禁报告](profgen/eval/prep/05_identity_gate_and_coverage.md)
- 全部文件在WORKDIR；未连接板子、未打开正式sample profile、修正案3未登记；未改LLVM本体/设计/认证/用户配置。资源3G/200%串行，资源原文见evidence/ruling2/supplement3/resources-summary.json。

## 裁决2补充2执行状态（2026-11-10；token-paste拼写范围停止）

- 补充2已照录并单独推送56c7cc7。实际C命令+GBS Clang外部只读取证插件直接记录逐token的isMacroArgExpansion、拼写/展开、调用实参和完整宏链；不修改LLVM。十个CU/ISA命令退出0。[报告§7](profgen/eval/prep/04_macro_function_ruling.md#7-裁决2补充2逐token实测与停止2026-11-10)
- FFmpeg Thumb/A32各闭合6个macro_generated_function；ff_put_pixels16_x2_arm的28个body token中4个跨文件实参全部满足条件。每侧另外28个DIE各有2个##生成的scratch token，isMacroArgExpansion=true但拼写不在补充2允许的两类源码位置，保留未决、不扩规则。[完整token与汇总](profgen/eval/prep/evidence/ruling2/supplement2/macro-summary.json)
- 27项规则/真实证据测试通过；真实DEF_PEL/PIXOP2“闭合”要求因scratch仍未满足，已保存两个完整示例而非改写拼写位置。待人工裁决：是否为token-paste另立严格的编译器来源证明规则。裁决1闭合spike各2、FFmpeg1236/1242不变；GNU外部CU每侧38不变。
- 未决总数spike各15、FFmpeg26869/26904（其中macro scratch各28、原规则候选未完成26841/26876）。单候选/多候选歧义验收、U、③、损失分桶及映射范围静态规模均未继续。[完整清单](profgen/eval/prep/evidence/ruling2/supplement2/closure-summary.json)
- 3G/200%串行scope，无OOM/资源暂停/终止；最低MemAvailable7.502766GiB、最高cgroup peak0.538528GiB，原始资源与辅助代码失败均留证。没有打开正式sample profile、未连接板子、修订3仍未登记。

## 裁决2执行状态（2026-11-10；宏实参AST条件停止）

- 裁决1修正已推送f8f141f，11项夹具通过、闭合数不变。裁决2与补充1已分别推送099a78c、0c603bd。
- C命令与LLVM源码证明PGO前缀为basename；显式TU映射与完整linkage、S/C声明位置、覆盖区域检查每个FFmpeg对象34/34通过。宏AST条件尚未闭合：CallExpr的宏实参拼写位置在decl_file或scratch space，均isMacroArgExpansion，需用户决定是否允许这一类；不自行忽略。[报告与原文](profgen/eval/prep/04_macro_function_ruling.md)
- GNU外部CU每侧38个DIE已对应10个libgcc归档成员，按原规则not_instrumented；归档SHA、平台ar/dwarfdump、S链接日志/driver检查与局限见报告。规则辅助函数18项合成夹具通过，不冒充真实宏链验收。
- 宏函数每侧34仍未决；普通候选的完整定义/叶子行集合验证未继续（spike各15、FFmpeg26841/26876）；尚未验收原规则单候选与多候选歧义数量。全部清单行保留，详见evidence/ruling2/closure-summary.json。
- U、③、对象表、分桶损失与映射范围内静态代码规模未计算；正式sample profile未打开；修订3未登记。不改LLVM/设计、不碰板子。等待宏实参拼写位置裁决后继续。

## 裁决1代码修正（2026-11-10）

- 已删除三个常量True；逐对象、S/C逐侧从header-evidence.json读取核验结果，任一缺失/假则未决。11项夹具通过，重跑闭合数spike各2、FFmpeg1236/1242完全不变。[报告](profgen/eval/prep/03_system_header_ruling.md#6-裁决1实现修正用户裁决2入口)
- 下一步按用户裁决2继续宏函数、外部CU与普通对应核对；仍不打开正式sample profile。

## 裁决1执行状态（2026-11-10；其他身份类别停止）

- 裁决原文已先提交推送42925cce108de42b6a8dfc69a6d0c17d0254e643。四项证据已核对：S/C系统目录同为/usr/lib/clang/22/include、/usr/local/include、/usr/include；C未开启系统头覆盖，源码跳过条件及覆盖全局文件表核对通过。
- 新规则10项合成夹具通过、0失败。静态清单新闭合system_header_no_reference：FFmpeg Thumb1236、A321242、spike Thumb/A32各2个DIE。[执行报告与证据](profgen/eval/prep/03_system_header_ruling.md)
- 按裁决停止条件：FFmpeg每侧另有34个同名异定义文件DIE（hpeldsp_init_arm.c/pel_template.c/hpeldsp.c/rv40dsp.c，参考主文件不同），需人工裁决；另38个GNU外部CU DIE待现有规则的来源证据。未按同名或FNDA=0强行对应。
- 完整清单全部行保留；有候选但定义/行集合尚未核对的记录仍为未决（spike各15、FFmpeg Thumb26841/A3226876），没有把候选当结论。未继续原规则核对和全套夹具。
- U、①②③③′、n_eff、K、损失分桶与映射范围内系统头地址/字节数均未计算，原因是映射范围尚未建立。未打开正式sample profile、未连接板子、修订3未登记。
- 待人工裁决：宏生成函数同名、两侧DWARF声明文件一致而覆盖主文件不同的处理；其他挂账保留。

## 登记前准备第一阶段（2026-11-10；身份门禁停止）

- v1.5已单独提交推送dba4de162eab5058f16dfed8445da93ea058e49a；计划提交34f0013。修订3未登记，本轮没有打开或计算任何正式sample profile（含CALIBRATION）。
- N.5 #13部分完成：四份C参考lcov与JSON segments逐行一致；7个合成覆盖夹具通过；spike17条HasMultipleRegions与Coverage API一致。summary与完整DA视图不同，范围交叉核对尚未闭合。[覆盖记录](profgen/eval/prep/01_coverage.md)
- N.5 #16已生成独立S/C DWARF静态清单，未完成闭合对应表与全套夹具。FFmpeg系统头内联memcpy等有代码，但覆盖参考无候选；CU为评估clang，不满足现有not_instrumented规则。Thumb/A32各1308/1314个候选缺失DIE（其中系统头1236/1242），不是采样计数。[停止证据与清单](profgen/eval/prep/02_identity_stop.md)
- 待人工裁决：系统头内联函数的封闭身份状态与范围处理；不自行扩展not_instrumented。其他无候选身份仍需逐条查明。
- N.5 #6/#15未计算：身份门禁未闭合，未生成U、①②③③′、n_eff、K或损失分桶，不能声称③达标或不达标。ToS参考尚未推进。
- 已有P9报告文字不足以逐份确认正式S的avg/prev-inst成功，挂账；本轮不为补证而转换profile。原统计/资格状态不改。
- 所有新代码/证据在tools/profgen_eval与docs/profgen/eval/prep；资源scope限制、启动门禁、原文与SHA保留。未连接板子，未改LLVM/补丁/设计正文/认证/三项用户配置。

## 当前完成状态（2026-11-09；P9正式S重转与FFmpeg整体覆盖）

- 固定工具2e8895afce661b5fdc8cacab2b3323496fca51af7bd7b51c3753aa8328b7d0d5完成70组/106原件及额外20份period重转。输出temp/p9-formal-reconversion/outputs/；P8存档与旧结果保留，SHA已复核。移出usable=2736，与报告12独立统计一致；target11131603不变，usable8235324→8232588；身份全verified。sample50份变化/56份不变，period10变化/10不变；逐字段与profile树核对无额外差异。[质量报告](profgen/eval/quality_round1.md)、[逐份证据](profgen/impl/evidence/16/08_p9_reconversion_rows.json)
- 每转换独立3G/200%scope串行，无工具OOM/失败/重试。比对器一次遗漏删除空祖先，保留原错误后修正并精确核对，没有重跑该转换；全部顶层total差值与原独立逐函数非叶子样本数一致，period派生文本由只读P8存档生成参考并与P9逐字节一致。
- 用户后续改为立即10GiB门禁、8G/200%scope；旧等待在export启动前终止，保留未开始收尾。Thumb/A32整体export各一次、串行成功，8.025/6.674秒；运行中cgroup峰值4.324688/4.272709GiB，export RSS4190164/4179876KiB。两份JSON各498文件、28236函数实例记录（去重函数3575）、112206可执行行/8298覆盖行；大文件temp/coverage-whole-8g-20261109/。[覆盖证据](profgen/impl/evidence/16/09_whole_coverage_8g.json)
- 已采样最低MemAvailable16528896KiB（15.763184GiB）；无资源暂停/终止、无OOM/重试。旧等待scope的主动取消是用户改指令后的执行流程调整，不是资源终止。[资源证据](profgen/impl/evidence/16/10_reconversion_coverage_resources.json)
- 原资格31 clean/28 abnormal/11 unknown不变；未连接板子，未开始最终质量矩阵、消费构建或性能测量，LLVM源码与旧profile未改。后续质量分析可引用新P9 profile与整体C覆盖JSON，仍待用户授权；Agent开发不开始。

## 当前完成状态（2026-11-06；频率区分、覆盖分片与补丁9）

- 判定规则原文预提交7546425；单核60区间约1.500GHz，四核38区间最低0.793GHz、仅连续2区间低于1.455GHz，80.341°C停止。欠压sticky全0，完整固件时钟/标志不可用；按规则unknown，不运行后续FFmpeg、不生成修订。两RUN已SHA核验后删除；root off/schedutil、RPM1232恢复。[报告14](profgen/impl/14_ffmpeg_frequency_diag.md)
- 覆盖：Thumb spike整体与逐源文件合并119行/11函数完全一致（1源文件）；libavcodec h264_cabac.c单文件仍3GiB scope OOM，停止且未重试、未提高限额。[质量报告](profgen/eval/quality_round1.md)
- 补丁9完成：LLVM本地15a5ec3f46283ad2eccaecf97b2eac2a0e43d65c，新工具SHA 2e8895afce661b5fdc8cacab2b3323496fca51af7bd7b51c3753aa8328b7d0d5；0009已导出并反向检查通过，spec本地diff不变/未提交，未推LLVM或Gerrit。非叶子line0整样本排除至in_func_no_line及nonleaf_line_zero子项，正式测试通过。[报告15](profgen/impl/15_patch9_nonleaf_line0.md)
- 22:00门禁21.8709GiB通过；GBS10G/400%、-j4，退出0/1079.586秒/107步。正式lit84 PASS/1 UNSUPPORTED/1 XFAIL/0 FAIL；C1两遍636、0差异；14历史输入各两遍一致（4成功profile不变，10既有失败不写profile）；schema140报告396字段差集空。
- 本轮资源最低MemAvailable9.162472GiB，构建最低19.217651GiB；无全局内存暂停/终止、无重构建阈值终止。覆盖scope OOM一次，观测RSS峰值3168464KiB；构建scope峰值9.532642GiB含缓存。
- 按本轮范围：没有重转正式S，没有最终质量矩阵/性能测量。原31 clean/28 abnormal/11 unknown不变；下一步等待用户决定散热/判据、覆盖导出办法与正式S重转。Agent开发不开始。

## 本轮阶段状态（2026-11-06；诊断与覆盖结束，补丁9等待窗口）

- 频率区分规则原文预提交7546425；单核60区间约1.500GHz，四核38区间中仅连续2次低于1.455GHz，最高80.341°C触发停止；rpi_volt欠压sticky全部0，其他固件频率/标志来源不可用。按原规则unknown，不运行FFmpeg、不生成修订、不改资格。两RUN完整SHA后删除，root off/schedutil、RPM1232恢复。[报告14](profgen/impl/14_ffmpeg_frequency_diag.md)
- 覆盖分片：Thumb spike整体/单文件合并119行、11函数完全一致（实际1源文件）；libavcodec首文件h264_cabac.c仍3GiB scope OOM，未重试/提高限额/继续其他文件。[质量报告](profgen/eval/quality_round1.md)
- 补丁9草稿未变、未构建。已启动22:00–08:00窗口等待程序，≥14GiB即10G/400%scope、GBS/Ninja-j4；连续两次<3GiB停自己的scope。当前无重构建运行，不开始最终质量矩阵/性能测量。[报告15](profgen/impl/15_patch9_nonleaf_line0.md)

## 本轮入口（2026-11-06；频率区分、覆盖分片、补丁9窗口）

- 按用户原文登记 [frequency_disambiguation_rule.md](profgen/eval/frequency_disambiguation_rule.md)，本提交推送后才采集诊断。原预注册/修订文件不变，不开始最终质量矩阵或性能测量。
- 轻任务≥4GiB，3G/200% scope串行；补丁9窗口为2026-11-06 22:00至11-07 08:00，每10分钟检查≥14GiB，不查SwapFree；构建10G/400%、-j4，连续两次<3GiB终止自己的构建。
- 尚未采集本轮数据。板上必须root off/schedutil收尾；覆盖分片先验证spike逐行/函数计数一致，再逐源文件独立scope。

## 当前收尾状态（2026-11-06；诊断停止、补丁9待构建、质量参考已准备）

- 判定规则预提交5219d15；首个FFmpeg a类用户态有效频率1.404GHz<1.455GHz，按规则停止，未生成修订2。校准外层墙钟包含perf开销，不能当作纯循环实际频率；物理降频未被证明。root off/schedutil恢复，RPM1232不变。[报告14](profgen/impl/14_ffmpeg_frequency_diag.md)
- 非叶子line0已正式复现写入65525伪调用点；补丁9草稿5文件+92/-21已完成、测试/schema已写、clang-format通过，但重任务门禁不足10GiB/1GiB，未构建、不重试；LLVM HEAD仍660a46f，正式工具仍9f63c692，未导出0009、未重转S。[报告15](profgen/impl/15_patch9_nonleaf_line0.md)
- 主机独立准备完成：Thumb/A32真实R参考IR，保守自比各3/22（13.64%，非sample质量结论）；spike C覆盖导出各11/11函数执行。FFmpeg C export触发3GiB scope OOM（一次），输出空，不提高限制、不原样重试。最终配置矩阵/CI/泛化/扰动/候选均待最终工具及覆盖资源条件，不伪造结论。[质量报告](profgen/eval/quality_round1.md)
- 资源：最低已记录MemAvailable5.289GiB，成功测得RSS峰值500516KiB；OOM精确峰值未知。全局暂停/终止阈值未触发。未运行本任务重构建，scope内OOM未影响他人进程。
- 下一步等待资源及用户指示：补丁9正式验收后完成全量转换/统计；频率测量等待处理，不调阈值；FFmpeg覆盖须验证限额内方案或用户另定资源。Agent开发不开始。

## 本轮补丁9阶段（历史，2026-11-06；已实现待构建）

- 正式补丁8最小复现确认非叶子line0会写入调用点65525（正常对照为1），total110含两个错误上下文。按授权完成IP专属排除草稿，归in_func_no_line并新增nonleaf_line_zero子项，测试与schema草稿已写；平台clang-format/dry-run通过。[报告15](profgen/impl/15_patch9_nonleaf_line0.md)
- 重任务门禁一次检查：MemAvailable5.580803GiB、SwapFree0.000290GiB，不满足10GiB/1GiB，不启动不重试GBS/lit。LLVM HEAD仍660a46f，未提交补丁9/导出0009；正式工具未改，C1/重放/正式S重转待验收。不要使用草稿作质量结论。
- 主机仍可做轻量准备：Thumb/A32 R参考IR已按原flags与真实profdata生成，无编译告警；最终配置矩阵依赖补丁9正式工具，尚未产出统计结论。后续进展见quality_round1。

## 本轮板上阶段（历史，2026-11-06；诊断首RUN按预注册停止）

- 判定规则原文已单独推送5219d15。首个FFmpeg a类用户态频率1.404018286GHz<1.455GHz，按规则“疑似真实降频”停止，不生成修订2，不重判原31/28/11资格；不能据此声称证明硬件降频。
- 校准外层墙钟含perf启动/收尾，原比值1.400–1.447GHz不作为纯循环频率证据，cycles/task-clock约1.500GHz；其余诊断重复未做。CPU user+sys与task-clock也有计时口径差。原始证据保留，[报告14](profgen/impl/14_ffmpeg_frequency_diag.md)。
- 镜像/内核/已知内存及swap容量与第一轮相符；total_mem=1600、resourced运行、zram配置0.4/lzo-rle；历史config/vm等缺证据，无法证明完全相同。无改配置。root off/schedutil恢复，RPM1232不变，确切RUN已全量SHA核验后删除。
- 轻任务3G/200%scope成功、无资源暂停/终止；重构建条件不满足，未启动。继续仅主机非叶子line0核实及不依赖FFmpeg资格的分析；补丁9尚未实现，不使用未验收工具。

## 本轮恢复入口（历史，2026-11-06；分级资源门禁）

- 新规则替代上一轮8GiB统一门禁：轻任务≥4GiB，3G/200% scope，串行；重任务须≥10GiB且SwapFree≥1GiB，16G/600%、-j6，不满足则留待构建而不整体停止。运行中每60秒保存meminfo，连续两次<2.5GiB暂停，任一次<1.5GiB终止本任务进程并停止。
- 主机初查MemAvailable约5.55GiB、SwapFree约38.6MiB，允许轻任务，不允许重构建。3G/200% user scope实际启动成功。资源基线在temp/frequency-diag-resume/baseline.txt。
- 已按用户原文登记[修订2判定规则](profgen/eval/preregistration_amendment2_rule.md)，本次单独提交推送后才做板上诊断；不是资格修订2本身，预注册及修订1不变。先比对身份/板子状态，任何差异即停，不调整板子。
- 尚未开始板上读取或诊断、line0核实、补丁9、统计质量分析。完成情况后续据实更新。

## 上轮停止记录（2026-11-06；频率诊断与质量分析启动前）

- 用户授权RPi4频率诊断、条件性补丁9及统计质量分析；资源上限nice19/ionice3、长任务可用时16GiB/600% scope、编译最多-j6、分析单进程。
- MemAvailable连续三次5.714、5.805、6.297GiB，均低于8GiB；按“资源上限被触发两次以上”停止。这是同一次低内存状态的三次观测，未触及4GiB强停线，未启动计算任务。[报告14](profgen/impl/14_ffmpeg_frequency_diag.md)、[证据](profgen/impl/evidence/14/01_resource_gate_stop.json)
- 未连接板子，未改root/governor、LLVM、设计或预注册。尚未提交诊断判定规则，未生成修订2/补丁9，未做质量分析；原31 clean/28 abnormal/11 unknown不变。
- 下一步资源恢复并获继续指示后，先提交诊断判定原文，再按原任务完成诊断、line0核实及质量分析；不提前给出候选配置或性能结论。

## 上轮完成状态（2026-11-06；补丁8小修与RPi4第一轮闭合）

- 保留RUN恢复完成：99项SHA与首次清单/本机完全一致，target106593计入矩阵，确切目录已删除。实际缺码重试0次；只读最多2次重试裁决已落实、15项主机门禁测试通过。预注册7d3d9d9与修订1不变。[恢复](profgen/impl/12_board_round1.md)、[审计](profgen/impl/evidence/12/51_retry_audit.json)
- 补丁8小修完成：LLVM `660a46f036a47ecc940e02b153d3e76e6eb39e79`，正式工具SHA `9f63c692a4239a222bfb86cd9dcab93b04a28fc32421306b597f4c799627fdc7`。GBS1157.977秒/111步，lit84 PASS/1 UNSUPPORTED/1 XFAIL/0 FAIL，C1两遍各636条0差异，14历史重放与153个Clang profile不变，0008反向检查通过；spec未提交。[报告13](profgen/impl/13_patch8_thumb_dwarf.md)
- 正式S完成70/70逻辑组（14配置各5组）、106物理RUN，target11,131,603/usable8,235,324；106份sample与20份频率period profile均与旧补丁8逐字节一致，身份全部verified、name_merged_functions=0。FFmpeg两ISA各33规范化区间，别名72次全部一致，映射不可用0。[完整性](profgen/impl/evidence/12/65_completeness.json)、[矩阵](profgen/impl/evidence/12/56_matrix_summary.json)
- 按修订1：31 clean/28 abnormal/11 unknown；clean target4,807,883/usable4,109,735，旧7份仍unknown。14/14 R/C/G5训练及测试参考已按stage合并profdata，setup排除。没有做配置质量分析、消费构建或性能结论。[报告12第15节](profgen/impl/12_board_round1.md)、[profdata](profgen/impl/evidence/12/58_profdata_summary.json)
- LOST完整导出闭合：主压力423条LOST、L58343、S1190755；系统压力626条、L71965、S1720866，独立L/(L+S)与工具一致。fork/exec/deleted/模块/系统级五项通过；取得16条真实-1/-1和335条([unknown])，PID筛选与分类正确，关闭unknown实测挂账。[报告12第16节](profgen/impl/12_board_round1.md)、[特殊样本](profgen/impl/evidence/12/69_special_samples.json)
- 流程修正如实保留：首次LOST试采因Bash3.2空数组nounset在perf启动前退出1，恢复后修正并新试采一次；不是缺码重试。主机JSON工具路径/继承映射核对器的两次误报已保留原文并修正，未改数据/LLVM规则。[Bash证据](profgen/impl/evidence/12/66_bash_compatibility_fix.json)、[继承核对](profgen/impl/evidence/12/67_independent_checker_correction.json)
- 最终已恢复root off(uid5001)、policy0=schedutil，RPM1232不变；/opt used294728KiB/available1010888KiB。所有本轮RUN已SHA核验后删除，工具/变体/视频保留；无活动采集任务。执行阶段累计8228.477秒（含传输/核验），首条恢复至末次恢复墙钟9133.291秒。[恢复](profgen/impl/evidence/12/70_completion_and_restoration.json)
- 真实avg保持已关闭。全量非叶子line0=2736，target占0.0245787%、usable占0.0332227%，涉及5个顶层函数；处理规则仍待PM。下一步等待质量分析/消费构建授权及v0.8登记评审，Agent开发不开始。

## 上轮阶段状态（历史）（2026-11-06；补丁8完成，板上在第二次清单退出码门禁停止）

- 补丁8已完成：LLVM本地`cd5168c48b5422a50829259fd43e84cc3edd6694`，正式工具SHA `41440292c7cf3a380a6779dfea6d06ff74a22e18537127561829bf989bb16413`；lit84 PASS/0 FAIL/1 UNSUPPORTED/1 XFAIL，C1两遍各636条0差异，14份历史整份profile与补丁7一致，GBS791秒/113步，0008反向应用检查通过。结果仓库阶段提交41e0be8、2de3086已推送；LLVM/Gerrit未推。[报告13](profgen/impl/13_patch8_thumb_dwarf.md)
- 本次矩阵23:48:02–01:34:01，6358.323秒，新增27逻辑组/46物理RUN。累计35/70组、54完整S导出，target5,911,900/usable4,390,651，全部verified、name_merged_functions=0；环境资格13 clean/12 abnormal/10 unknown，干净子集target1,991,272，原7份仍unknown，未做配置间比较。[逐组/分类](profgen/impl/evidence/12/40_matrix_summary.json)、[原件SHA/资源](profgen/impl/evidence/12/48_runs_receipts_resources.json)
- 真实规范化：FFmpeg Thumb/A32各33区间、spike各0；别名查询33次全部一致。54份P7/P8对照24份profile变化，仅__udivsi3/__divsi3/__aeabi_idivmod；15份分类变化，共28样本由outside/in_cu_no_subprogram移入usable。[全部函数差异](profgen/impl/evidence/12/43_profile_function_changes.json)
- **停止门禁**：A32 spike中档r3的`/opt/afdo_agent/work/eval-20261106T023250-25276`采集exit0，但拉回后第二次远端清单缺`__RC`。本机99文件与首次/第二次可见SHA均相同，不能代替真实退出码；未写完成收据、未删板上目录、未计入正式矩阵。没有重试/绕过，根因未知，stderr在现有包装器此分支未留存。下一步需决定如何记录/核验该层，不原样重跑当前worker。[原文与分析](profgen/impl/evidence/12/44_transfer_stop.json)、[失败状态](profgen/impl/evidence/12/45_matrix.status.txt)
- 安全恢复已回读：policy0=schedutil，root off(uid5001)，RPM1232不变；/opt used304988KiB/available1000628KiB，同内核，无本任务残留进程。主机后台均结束；后续串行器未启动LOST/集成。旧599文件中断RUN已在此前完整核验后删除，勿与这份新保留RUN混淆。[恢复](profgen/impl/evidence/12/45_final_board.txt)、[进程](profgen/impl/evidence/12/45_processes_after_stop.txt)
- 已闭合真实avg：原3热点11,525指令/715键GNU独立sum/max/avg零差异。当前全部54份nonleaf line0=1371，target占0.0231905%、usable占0.0312254%，涉及5顶层函数；规则仍待PM。[avg](profgen/impl/evidence/12/31_real_avg_independent.json)、[nonleaf](profgen/impl/evidence/12/41_nonleaf_final.json)
- 未完成：剩余35正式组、训练0/14、LOST压力0、集成0/5；06高LOST完整导出挂账未关闭。未执行的集成草稿仅存temp，未部署，项目board脚本不改。保留全部原件/排除记录，续跑须新目录并排除已完成槽位。等待指示，Agent开发不开始。[报告12第13节](profgen/impl/12_board_round1.md)

## 本轮中间状态（2026-11-05；补丁8验收后恢复矩阵，历史，已按上节停止）

- 最新PM裁决：IP规范化区间首地址N采用同指令别名N+1查询，原A缓存/计数键不变；两次叶子文件/行/discriminator不一致则generate失败并给出原文。此项修改冻结5.4.2/5.7.2执行细节，待设计v0.8登记及外部评审，v0.7正文不改。[报告13第5节](profgen/impl/13_patch8_thumb_dwarf.md)
- 补丁8 LLVM本地`cd5168c48b5422a50829259fd43e84cc3edd6694`；21文件+492/-23；0008已导出并反向应用检查通过。GBS退出0、791秒/113步；正式lit84 PASS、1 UNSUPPORTED、1 XFAIL、0 FAIL；C1两遍各636条0差异；14份导出各两遍profile与补丁7逐字节相同。正式工具SHA `41440292c7cf3a380a6779dfea6d06ff74a22e18537127561829bf989bb16413`。原spec本地测试改动未提交，src/llvm干净。[正式证据](profgen/impl/evidence/13/12_formal_build.json)、[审计](profgen/impl/evidence/13/17_commit_audit.json)
- 已闭合主机验收：全部8份正式S以新工具转换verified、name_merged_functions=0，target1,259,104/usable1,023,185；FFmpeg每份33规范化区间，sum别名共3次一致，中档usable+1。真实avg保持原3热点、11,525指令/715键，GNU独立sum/max/avg零差异，关闭真实avg挂账。52个GNU告警定位DWARF5汇编CU，不影响热点C CU。[报告12第12节](profgen/impl/12_board_round1.md)、[独立证据](profgen/impl/evidence/12/31_real_avg_independent.json)
- 已有正式数据nonleaf line0=88，target占0.0069891%、usable占0.0086006%，涉及3个顶层函数；只覆盖当前8份，处理规则仍待裁决。06完整LOST、剩余矩阵、训练与5集成尚未完成。
- 原中断RUN已root下成功核验599文件、拉回复核后删确切目录，排除正式矩阵。预检结束root off、schedutil、RPM1232、/opt used293332KiB/available1012284KiB。HUP伪成功及SHA子命令失败传播门禁已修，主机5项trap+9项传输回归通过。[收据](profgen/impl/evidence/12/35_partial_run_receipt.json)
- **当时板上矩阵正在后台运行（现已停止，见开头）**：temp/board-round1-patch8/worker.py；已重新开root并固定performance，结束/失败必须恢复原uid5001/schedutil，不能把上面的预检恢复当成最终恢复。原8组保留，其余按短RUN分段累计，不改预算/预注册；预计4–5小时。每600秒资源记录，真实内核必须不变。SDB再掉线当前RUN排除，最多一次重连后停下。
- 下一步：监测剩余矩阵、训练；完成LOST压力与5集成、全量nonleaf统计/profraw合并，逐阶段更新报告12与本状态。Agent开发不开始。

## 前轮授权与执行状态（2026-11-05；补丁8符号化契约停止，板上已恢复）

- 计划/授权：本轮先排查6份正式Thumb line0，再新增并推送预注册修订1，恢复RPi4，同时实现获PM授权的GNU AS Thumb DWARF区间规范化。补丁8未完成，不开始后续设计或Agent开发。
- 已闭合：6份报告的in_func_no_line均为原始行表显式line0，未见正行号漏查；spike Thumb sort_block集中在编译器.loc 0地址计算指令，A32对应地址加载保留line67。修订1已推送`6629b2e5a1bbc12073748fc01c12a5af04b34352`（完整值以修订提交审计为准），原7d3d9d9不变，旧7份正式缺cycles/task-clock仍unknown。见[报告12第10、11节](profgen/impl/12_board_round1.md)、[修订1](profgen/eval/preregistration_amendment1.md)。
- 进度：新增完成正式A32 spike高档431793目标样本，累计8/70正式、1259104目标样本；训练0/14、LOST0、集成0/5。新pilot2238仅流程验证。A32高档有效频率1.497442GHz、温度59.400°C、逐秒1.5GHz、换出0，按修订未观察到节流；完整SHA后删除。旧6份quality verified保持；旧高档Thumb与新增A32未转换。[新RUN/资格](profgen/impl/evidence/12/26_amendment1_resume_stop.json)
- 当前阻塞/待人工裁决：GNU AS原生最小素材子程序DWARF[0x1001,0x1009)，指令[0x1000,0x1008)。草稿规范化自身函数表后，LLVMSymbolizer的独立原始DWARF表仍在0x1000返回line9/function=<invalid>；空帧链被现有逻辑计为in_func_no_line，人工total60但sum/max/avg为50。需决定是否将有约束的规范化扩展到IP符号化函数身份查询，或明确另一分类/补全契约，未自行修改冻结5.4.2。[补丁8停止报告](profgen/impl/13_patch8_thumb_dwarf.md)、[API原文](profgen/impl/evidence/13/02_raw_symbolizer.json)、[前后对照](profgen/impl/evidence/13/03_stop_comparison.json)
- 补丁8状态：开发草稿/4个GNU AS ELF素材保留worktree与temp/profgen-patch8；新helper首组失败，未运行GBS/正式lit/C1/14重放，未建LLVM提交/0008。正式工具仍334a0929…、LLVM HEAD仍e4642a8…；设计/golden/src/llvm不改，spec原本地diff保持。[范围审计](profgen/impl/evidence/13/06_stop_scope.json)
- 板上安全收尾：要求当前RUN收尾期间，SDB掉线导致FFmpeg高档无真实RECORD_EXIT/完整导出；trap留下的ALL-END OK不可信，排除该RUN。重连后同一身份/内核、无残余采集进程；uid0下perf.data哈希Permission denied，清单失败、未拉取未删除。不完整目录`/opt/afdo_agent/work/eval-20261105T232305-7773`保留。已恢复schedutil/root off(uid5001)，RPM1232不变，最终/opt used307868KiB/available997748KiB。[操作原文](profgen/impl/evidence/12/27_amendment1_operations.json)
- 挂账：恢复前需修复HUP/中断trap伪成功与处理不完整RUN；不得据缺失的record返回码或失败SHA清单清理目录。真实avg、06完整LOST、全部正式nonleaf line0/top20、5集成与profraw合并均未关闭。新工具通过后才重做所有正式S；不以旧排除校准nonleaf29/21736冒充正式汇总。
- 下一步：等待GNU AS首指令符号化契约裁决后续补丁8；保持停止，不恢复剩余板上采集。结果仓库正常认证推送，无LLVM/Gerrit推送、无认证修改或密码请求。

## 前轮阶段记录（2026-11-05；恢复前line0核实通过，预注册修订1）

- 已完成本轮主机第一阶段：6份正式in_func_no_line逐地址全部为原始行表明确line0；spike Thumb中档34113条中33856条集中sort_block地址0x1076a，GBS GNU反汇编及addr2line一致，同flags Clang汇编在地址计算add前明确.loc 1 0 0。A32合并地址加载指令保留line67；无正行号漏查证据。FFmpeg60地址GNU抽查也为leaf未知行，原始行表为0；GNU bad-file-number警告仍保留待avg定位。[报告12第10节](profgen/impl/12_board_round1.md)、[统计](profgen/impl/evidence/12/24_line_zero_diagnosis.json)、[原文](profgen/impl/evidence/12/25_line_zero_raw_excerpts.json)
- 原预注册7d3d9d9逐字节不变；新增[修订1](profgen/eval/preregistration_amendment1.md)，须本次提交推送成功后才恢复板上采集。有效频率=stat cycles/task-clock，至少固定频率97%，逐秒频率等于固定值且温度低于75°C；每轮前后保存policy governor/min/max/cur。读不到固件节点不单独剔除；缺计数/CPU时间或不可靠计数仍unknown。原ε/预算/次数/bootstrap不变。
- 旧7份正式数据缺精确cycles/task-clock，按修订仍unknown，未补造记录、未做配置质量/性能比较；9份排除原件仍排除。line0是编译器明确位置，不改冻结排除规则；不同ISA须并报target/usable，不能按相同target预算假定相同可用信息。
- 已获补丁8裁决：IP的ELF32小端EM_ARM中奇数DWARF下界清bit0后处于$t时，范围两端清bit0，统一作用归类/边界，不清样本PC；增加报告/告警并完成GBS/lit/C1/重放。该授权替代下列历史“待裁决”，实现尚未开始。
- 下一步：推送修订后恢复剩余63份S、14训练及LOST/5集成，预计板上约4–5小时；并在本机实现/验收补丁8。当前阶段未连接板子、未变更root/governor，最近实证状态仍root off/schedutil。原avg/LOST/全量nonleaf等挂账待后续闭合。

## 前轮授权与执行状态（2026-11-05；RPi4恢复采集，真实avg在Thumb DWARF边界处停止，历史）

- 计划/裁决：预注册`7d3d9d9`与冻结v0.7逐字节不变。两段依赖预检按最新裁决登记：身份→非root系统命令→root→部署/SHA及perf版本→performance→采集。最终24项系统依赖通过，62文件/16目标SHA复验、新脚本/三视频SHA通过。首次nice/ionice补查发生在root后、governor前，随后24项完整非root检查通过；该时序偏差未隐去。[报告12第9节](profgen/impl/12_board_round1.md#9-两段预检后恢复真实-avg-在-gnu-as-的-thumb-dwarf-区间处停止)、[操作](profgen/impl/evidence/12/17_resume2_operations.json)、[依赖](profgen/impl/evidence/12/22_dependency_inventory.json)
- 进度：7/70正式S已完整采集/拉回，目标样本合计827311；前6份正式工具sum转换verified、name_merged_functions=0，第7份高档Thumb spike仅原件留存、未转换。9份校准/流程原件另存，不入矩阵；训练0/14、LOST压力0、集成0/5。[逐RUN与SHA](profgen/impl/evidence/12/19_resume2_runs.json)
- 已闭合流程：去cmp保留非空十进制整数失败门禁；安全拉回工具先全量文件集合/SHA、复查远端清单，再删确切RUN。坏哈希注入删除次数0、正确对照仅删确切模拟路径，8项主机回归通过。16RUN共1394板上文件验证后删除，完整原件和清单在temp/board-round1-resume2。[演练](profgen/impl/evidence/12/16_transfer_injection.json)、[测试/恢复](profgen/impl/evidence/12/21_resume2_restore_and_checks.json)
- 当前阻塞/待人工裁决：首份中档Thumb FFmpeg完整导出sum/max成功，avg退出1/failure_stage=boundary：GNU AS2.43的libgcc __udivsi3/__divsi3子程序DWARF low_pc为0x341f29/0x3421a1，而指令起点为0x341f28/0x3421a0。正式工具原样取DWARF范围，冻结规则要求无法证明边界即整次失败；未授权对这种DWARF表示清位。保留GNU原文、实际样本及失败JSON，未改LLVM、未过滤函数/样本。候选为有证据约束的地址规范化并补设计/lit，或修正平台DWARF生产端；均须裁决，未实施。[原始证据](profgen/impl/evidence/12/20_real_avg_boundary_stop.json)、[代码/设计位置](profgen/impl/evidence/12/23_stop_scope_and_nonleaf.json)
- 恢复：本次原uid5001/root off、policy0=schedutil，结束已恢复并回读；RPM1232→1232，/opt used282072KiB/available1023544KiB。uname-v与首次相同，uptime997.67秒支持中间同内核重启推断。板上总过程1943.965秒；host ALL-END FAILED表示按边界阻塞停止，不改写已成功RUN。[恢复证据](profgen/impl/evidence/12/21_resume2_restore_and_checks.json)
- 挂账：LOST完整高丢样/真实avg均未关闭；nonleaf line0只有校准29/21736=0.133419%，全矩阵与top20未做。采集脚本漏存每RUN开始前scaling_max_freq，频率资格unknown；节流也unknown，按原预注册干净子集0，不能用事后1.5GHz替代。恢复前需补齐policy边界记录并保持完整非root依赖顺序。工具正式SHA334a0929…未改，无新profile消费构建/质量结论；等待上述边界裁决后再恢复剩余63采集与14训练、集成和主机分析。

## 前轮授权与执行状态（2026-11-05；恢复轮在root前依赖预检处停止，历史）

- 预注册7d3d9d9逐字节不变；最新7项执行流程裁决登记在[报告12第8节](profgen/impl/12_board_round1.md)。本地common.sh移除cmp、增加完整依赖与performance门禁、sysfs节流读取；7项RPM比较测试和全部bash-n通过，尚未部署。
- 三项RPi4身份通过，23项依赖中22通过；/opt/afdo_agent/tools/perf的command-v失败，远端退出1。只读诊断显示当前uid5001(owner)，perf/libLLVM的ls与sha256sum均Permission denied，不能判为文件丢失。按“root前全部依赖通过，否则停止”未开root、未改governor、未执行perf。[预检](profgen/impl/evidence/12/13_resume_preflight.json)、[权限原文](profgen/impl/evidence/12/14_resume_stop.json)
- 需用户决定：是否允许只对“非root权限拒绝的部署文件”在记录原因后暂开root复核，仍在governor和perf之前；或由用户先使非root身份可查询。没有自行绕过、chmod或安装。root保持off、governor=schedutil，RPM1232，可用1145188KiB；本轮板上只读51.44秒，无需恢复。
- 待办：拉回/路径/全量SHA/确切RUN删除的单一失败即停流程及主机哈希失败注入尚未实施；2倍估算+200MB空间门禁尚未运行。ToS推送、部署复验、正式70次S/14次训练及集成全部待做。旧226目标样本仅失败校准证据。LOST/真实avg/nonleaf line0挂账不变。

## 前轮授权与执行状态（2026-11-05；RPi4第一轮校准收尾缺工具处停止）

- 已推送预注册 `7d3d9d9f9184bc2e0e2b94a479916a2d65f13463`（20:04:33+08），早于设备查询；阈值/预算/70次S与14次训练矩阵见[预注册](profgen/eval/preregistration.md)。仅RPi4授权、root/performance保存恢复、sysctl不改、官方ToS等裁决待v0.8登记。[报告12](profgen/impl/12_board_round1.md)
- 三项身份通过，新内核6.12.80-arm-rpi4-v7l（Nov4构建）；16项payload SHA全通过。Thumb spike校准cycles硬件type0/config0、235样本（目标226）、运行ID正确；收尾common.sh调用板上不存在的cmp，真实退出127/ALL-END FAILED。按最高原则“缺工具就停下”停止，没有安装或绕过。正式70次S、14次训练及集成尚未开始；profgen未运行，无verified质量等级、非叶子line0与profdata结果。
- 官方ToS下载与同参数60秒720p转码完成，SHA `280fbd41f8772491ebe784aa19a3caed3bb1e8b2e64daef1d2a5a284d1f38ad1`，留temp/board-round1，未推视频。[输入证据](profgen/impl/evidence/12/09_media.json)
- 已恢复governor=schedutil、root=原开启状态；RPM1232→1232，/opt最终used158064KiB、available1147552KiB，work为空，工具/变体/脚本保留。[操作原文](profgen/impl/evidence/12/08_operations.json)
- 执行偏差如实保留：初始3秒权限探测在原governor下（排除正式数据）；SDB平铺目录导致首次哈希检查路径错误，外层shell未fail-closed仍删除了板上RUN，随后33/33主机文件与事先板上SHA一致，但违反“先验哈希后删除”顺序。[哈希证据](profgen/impl/evidence/12/06_pull_hashes.json)。不可用事后一致掩盖流程错误。
- 待人工决定恢复执行：cmp依赖可改为带非空/数字校验的Bash计数比较（本轮未改），拉回/验证/删除必须合为显式fail-closed流程。节流工具缺失仍unknown，不事后放宽预注册。LOST完整导出、真实avg、非叶子line0等原挂账不关闭。LLVM/正式工具/冻结设计未改，Agent未开始。

## 前轮授权与执行状态（2026-11-04；评估准备与全部生成侧构建完成）

- 本轮单会话完成主机准备，不连接板子、不改LLVM/正式profgen/冻结v0.7、不推LLVM/Gerrit。用户裁决：R为IR插桩并关闭preinline，C为前端coverage，G5为正常IR插桩；R/C、R/G5分开。待设计v0.8登记。[报告11](profgen/impl/11_eval_prep.md)
- 新IR语义匹配器按完整位置+递归操作数等价/后继校验重写，23组手写IR对与14个测试方法（含7个bootstrap测试）通过；46份.ll由GBS llvm-as验证。真实clang消费IR只作读取冒烟，PHI保守unverified，不作为统计质量结论。[测试证据](profgen/impl/evidence/11/04_semantics_and_bootstrap.json)
- 12项FFmpeg代表性源文件选项核对全部通过后构建。spike/FFmpeg × Thumb/A32/aarch64 × S/R/C/G5共24项最终GBS成功，RPM/debuginfo已留存。spike合计240.03秒；FFmpeg合计2288.20秒，16:17:56–16:56:06，之前等待其他会话约80分钟。最低available10373MiB；未低于2GiB。[构建/失败尝试原文](profgen/impl/evidence/11/07_builds.json)
- 24个目标的选项、映射符号、成对20字节SHA1 ID通过；FFmpeg全部84对运行ELF/debug ID一致，debug保留对应ISA映射符号，R/C/G5全体运行ELF含插桩节及运行库符号。两个目标平台均有compiler-rt profile运行库，当前无LTO。各变体实际命令、build-id及RPM SHA见[目标清单](profgen/impl/evidence/11/08_artifacts.json)、[全部FFmpeg ELF](profgen/impl/evidence/11/08b_all_ffmpeg_elf_ids.json)。
- C覆盖文件须用匹配runtime+debug经GBS eu-unstrip合成后交llvm-cov；单独debug缺PROGBITS的profile名字节。三ISAreader已用合成profile核对，真实计数仍待板上训练；不把合成数据当覆盖真值。[证据](profgen/impl/evidence/11/10_coverage_split.json)
- 板上脚本与[计划](profgen/eval/board_plan.md)仅准备、bash-n检查；本机payload为temp/eval-prep11/payload-rpi4（16项）及payload-rpi5（8项），尚未部署。现有视频同源BBB，缺不同视频的测试输入；独立片源/ε/异常规则/板上权限待用户决定。当前G5为生成侧，优化收益组仍需训练后消费构建。
- 关闭R插桩类型阻塞、按aarch64证据关闭probe拆分位置；保留ARM probe崩溃为步骤8子方案阻塞，不阻塞DWARF路径。其他板上/默认build-id/非增量前撤销spec挂账不变。下一步等待板上评估授权，Agent设计开发仍在增强完成后。

## 前轮授权与执行状态（2026-11-04；R 插桩类型冲突处停止；历史，已获裁决）

- 已获第一批白天评估准备授权；只做便宜主机检查与小程序构建，不连接板子、不完整构建FFmpeg。按停止条件，在R生成方式与设计指定IR转储流程冲突处停止；未改LLVM/工具/冻结设计/spec或配置。[报告11](profgen/impl/11_eval_prep.md)
- 已复现：任务指定的`-fprofile-instr-generate`产生Front-end profile，使用时`-print-after=pgo-instr-use`无转储（exit0、stderr0字节）；`-fprofile-generate`诊断对照产生IR profile及1次转储（exit0）。两侧最终IR均有入口计数，不是profile未读入。完整命令、合成输入及原始输出见[证据](profgen/impl/evidence/11/01_reference_instrumentation.json)。没有自行更换R flags；等待裁决后继续匹配脚本、spike各变体、夜间脚本与板上计划。
- 用户裁决已登记（待设计v0.8）：pseudo-probe拆分后节的位置按aarch64证据关闭，节名检测与架构无关，两种位置拒绝已验证；armv7l Clang22.1.8 probe崩溃仅阻塞第10节步骤8的probe子方案，**不阻塞第一批DWARF路径**，本轮不定位、不绕过。[原拆分证据](profgen/impl/evidence/10/07_aarch64_split.json)
- 本轮无GBS构建、无新RPM/build-id、无夜间可运行入口；IR新匹配器/统计测试尚未开始。正式工具与设计SHA保持不变，原有spec测试改动保持不动。[范围审计](profgen/impl/evidence/11/03_scope.json)

## 前轮授权与执行状态（2026-11-03；第一批主机验证，Clang崩溃处停止；以下为历史）

- 本轮授权只做主机验证；正式补丁7工具SHA仍为`334a09290f53eb4c793ae91759f2b6344a36e63317820eb9151771b262dc3f30`，LLVM HEAD仍`e4642a8ad9e0acb990b45ade3ef7aca755cd80f2`。未改LLVM或设计、未连接板子、未推LLVM/Gerrit。[报告](profgen/impl/10_host_verification.md)
- 已完成合并验证：max 20/10、受限sum 8/8、0.3及0.6各2/1、cold裁剪100/101；新增tools/profgen/check_merge_inputs.py，20项正反测试通过，输出建议命令不执行。[合并](profgen/impl/evidence/10/01_merge.json)、[门禁](profgen/impl/evidence/10/02_merge_checker.json)
- 已完成aarch64/Thumb两格式消费：show与text回读一致，IR入口/分支/两处内联匹配；0/2调用点失配、0/150样本丢弃、无饱和权重。[消费](profgen/impl/evidence/10/03_consume.json)
- 08 FFmpeg未带profiling debug与唯一内部名，带-mthumb及显式SHA1；最小双文件对照的name_merged_functions由2降为0，证明唯一后缀被profgen读取。正式FFmpeg评估必须重新按第9节构建，本轮未重建FFmpeg。[08选项](profgen/impl/evidence/10/05_ffmpeg.json)、[命名对照](profgen/impl/evidence/10/04_unique_names.json)
- aarch64小包GBS成功：debug保留$x/$d；probe两节在debug、两位置拒绝成立；新构建DWARF5行表/20地址符号化/comp_dir前后一致，BUILD与RPM ID不同。旧08 BUILD产物缺失，不能声称复现原FFmpeg同一次构建。[拆分](profgen/impl/evidence/10/07_aarch64_split.json)、[DWARF](profgen/impl/evidence/10/08_DWARF5_split.json)
- **停止原因**：armv7l旧快照不可用，沿用08 reference配置副本重试；普通构建成功，probe构建在ARM Instruction Selection/ScoreboardHazardRecognizer::EmitInstruction中Clang22.1.8段错误，GBS_EXIT1/ALL-END FAILED。任务进程已退出，预处理源码及重现脚本已保留，未运行/修复/换flags绕过。下一步等待用户决定独立定位或其他处理。[原始崩溃与候选方案](profgen/impl/evidence/10/09_stop.json)
- 整体尚未完成：armv7l probe拆分、旧08同次构建复核未闭合；新LLVM默认build-id发布后复核与[unknown]真实样例继续挂账。已有spec本地测试diff保持原样；Agent设计开发未开始。

## 前轮授权与执行状态（2026-11-03；补丁7完成，历史）

- 补丁1–7已获授权并完成。补丁7 LLVM `e4642a8ad9e0acb990b45ade3ef7aca755cd80f2`，9文件+1633/-103行；完成五项IP枚举、显式aggregation、边界错误上下文、schema1的unknown/null约定、LOST分母溢出warning和用户/schema文档。[报告](profgen/impl/09_patch7_report.md)、[0007](../patches/profgen/0007-llvm-profgen-Document-IP-mode-and-finalize-options-and-reports.patch)、[提交审计](profgen/impl/evidence/09/15_commit_audit.json)
- 正式GBS 21:24:56–21:44:56+08，1199.800秒、108 Ninja步，GBS_EXIT0/ALL-END OK。%check仍85项：83 PASS/0 FAIL/1 UNSUPPORTED/1 XFAIL，与补丁6逐项一致。C1两遍各636条、两遍一致、对基线0差异。[构建](profgen/impl/evidence/09/08_build.json)、[lit](profgen/impl/evidence/09/09_lit.json)、[C1](profgen/impl/evidence/09/10_c1.json)
- 14次完整导出带quality-report各两遍；profile/诊断/退出码与补丁6一致，JSON只出现确认不存在值转null的授权差异，逐字段留证。110份lit报告345字段与schema文档双向差集0、空字符串值0。GBS无Sphinx/docutils，已做CMake RST子集解析，完整Sphinx检查未做。[重放](profgen/impl/evidence/09/11_full_replay.json)、[schema](profgen/impl/evidence/09/12_schema.json)、[文档检查](profgen/impl/evidence/09/04_rst_check.json)
- 新工具SHA `334a09290f53eb4c793ae91759f2b6344a36e63317820eb9151771b262dc3f30`。关闭“IP新选项改为枚举类型与cl::values”挂账；非叶子line0、06完整LOST缺失、08真实avg上板、非增量前撤销spec等继续保留。新约定已在报告“待设计v0.8登记”列明；冻结v0.7正文与golden逐字节未改。
- 本轮单会话，无板上操作、无LLVM/Gerrit推送、无认证修改或密码索取，无新增已观察到的工具越界写入。spec本地测试diff保持原样、不提交；下一步等待用户授权，Agent设计开发仍在增强完成后，补丁完成不等于第二阶段或产品收益验证完成。

## 前轮授权与执行状态（2026-11-03；补丁5小修、补丁6完成，历史）

- 补丁5小修已独立验收/amend：LLVM `b843cf07f851985413c926a562f9135a272a3bea`，0005已重新导出；未重做补丁4。[审计](profgen/impl/evidence/08/11_patch5_amend_audit.json)
- 补丁6 LLVM `1dd4b9acd84045c230e77cc68d85eafca58eae88`，26文件、+1559/-33行、新增6组lit；实现确定性质量JSON、精确可选门槛、ISA/覆盖诊断、原子输出和单次阶段回调。[报告](profgen/impl/08_patch6_report.md)、[0006](../patches/profgen/0006-llvm-profgen-Add-quality-reports-and-failure-contracts.patch)、[提交审计](profgen/impl/evidence/08/36_patch6_commit_audit.json)
- 已闭合：最终GBS 20:28:22–20:42:46+08，864.668秒、107 Ninja步、GBS_EXIT0/ALL-END OK；正式%check 85项：83 PASS/0 FAIL/1 UNSUPPORTED/1 XFAIL。原79逐项不变，原50保持48/0/1/1；C1两遍各636、对基线0差异，35个新IP测试排除。[构建](profgen/impl/evidence/08/22_patch6_builds.json)、[lit](profgen/impl/evidence/08/23_patch6_lit_summary.json)、[C1](profgen/impl/evidence/08/24_patch6_c1_summary.json)
- 已闭合：14次完整导出各两遍，JSON/profile/诊断确定，样本各层独立重算与旧证据一致；05/09 strip库按预期generate失败、不生成profile。两档08合成负载profile与补丁5相同，报告同名合并函数数2/308。[真实重放](profgen/impl/evidence/08/25_patch6_real_exports.json)、[合成负载](profgen/impl/evidence/08/27_patch6_synthetic_scale.json)
- 生效裁决（待设计v0.8登记）：路径冲突时两种输出都不写，含输入别名且先于任何副作用；其余失败原子替换完整失败JSON，任何失败均保留旧profile；报告自身写入/提交失败保留旧报告。此前“普通失败也保留旧报告”是PM笔误，作废。真实截断DWARF验证no_cu/usable0；真实符号化调用点注入验证generate回调，真实损坏符号表验证load回调。均已验收，不再挂为阻塞。
- 收尾修正：父目录符号链接后接`..`的不存在输出别名已拒绝；未计算指标写unknown；ISA可用.dynsym作SF_Thumb后备但排除SHN_ABS，outside_symtab榜单仍只用.symtab。[路径反例与修复](profgen/impl/evidence/08/34_path_alias_before_after.json)
- 新工具SHA `4f115a34cf558008bc138c7aaf3d3476717ea7d5fc2e44ea4142ac6fb06cb4f9`；冻结设计/golden/C1基线未改，src/llvm工作树干净；spec本地diff原样保留、不提交。未连接板子、未推LLVM/Gerrit、未改认证或索要密码；无新增已观察到的工具越界写入。
- 下一步等待补丁7授权；Agent设计与开发仍在llvm-profgen增强完成后。06完整LOST、真实avg上板、IP枚举/cl::values、非叶子line0与非增量前撤销spec等挂账继续保留。

## 前轮授权与执行状态（2026-11-03；输出别名契约停止，已获裁决，历史）

- 已获本轮实现授权；按停止条件，在“报告路径与旧profile为同一文件时，既写失败JSON又保持旧profile不变”的冲突处停止，等待用户裁决。建议仅stderr报路径冲突、两种输出都不写，**尚未实施该例外**。[报告](profgen/impl/08_patch6_report.md)、[原文与反例](profgen/impl/evidence/08/01_contract_conflict.txt)
- 补丁5小修草稿已写：同映射段/前驱有行信息、skid原因细分、按函数分组校验；新增无前驱行信息Thumb素材及测试。格式检查通过，但开发编译已TERM停止，未生成新工具；GBS/lit/C1/14份重放未运行，不能称小修完成。[状态](profgen/impl/evidence/08/06_stop_state.json)
- LLVM HEAD仍为 `d7bd4795c7fddfc239510b96fa6803b56b94dbb4`；无amend、无补丁6提交，0005未改。spec原diff保持原样、不提交；设计v0.7与golden不变。只停止本任务自己的开发编译进程，已核对退出，未影响其他会话。
- 下一步：用户裁决后先完成补丁5独立验收/amend，再开始补丁6。未连接板子、未推LLVM/Gerrit、未改认证或索要密码；原挂账继续保留，Agent设计开发仍在增强完成后。

## 前轮授权与执行状态（2026-11-03；补丁5完成，历史）

- 计划/授权：已按完整补丁5任务与两次素材/规模裁决完成；补丁4小修 `aef395b32e27d5f63468c5d49f76f43508dbf270` 未重做，冻结v0.7和golden未改。下一步等待补丁6授权；Agent设计开发仍在增强完成后。
- LLVM本地补丁5 `d7bd4795c7fddfc239510b96fa6803b56b94dbb4`：64文件、+3298/-40行，新增8个lit。实现按需映射符号边界、avg、sampled-functions补零、prev-inst及隐藏诊断。[报告](profgen/impl/07_patch5_boundaries.md)、[提交审计](profgen/impl/evidence/07/33_patch5_commit_audit.json)、[0005](../patches/profgen/0005-llvm-profgen-Enumerate-instruction-boundaries-on-dem.patch)。仅工具/测试目录，未推LLVM远端/Gerrit；spec原diff保持不动且未提交。
- 已闭合：三份A64原件与三个行表副本用同字节.inst修正，.text哈希与DWARF区间不变。最终70份ELF排查仅两份故意bad-conflict有同址异状态。[修复](profgen/impl/evidence/07/14_fixture_repair_proof.json)、[最终清单](profgen/impl/evidence/07/20_fixture_inventory_final.json)。
- 已闭合：head补零兜底测试total50、首body0、head1通过；未用total冒充入口。13素材182起点与objdump一致；08最大20Thumb符号范围132859起点一致，现有DWARF按名合并后的全部137117起点也一致。[objdump](profgen/impl/evidence/07/26_fixture_objdump.json)、[20函数](profgen/impl/evidence/07/27_real20_boundaries.json)。
- 构建：GBS 13:45:14–14:14:55+08成功，实际约1781秒、108 Ninja步；worker共2380.498秒含资源等待600秒，GBS_EXIT0/ALL-END OK。available最低9656MiB。[记录](profgen/impl/evidence/07/22_patch5_build.txt)
- 正式GBS %check：79项，77 PASS/0 FAIL/1 UNSUPPORTED/1 XFAIL，原50逐项不变、新8全PASS。C1每遍636、两遍一致、0差异，新增29测试排除；14次完整导出地址/reader与补丁2逐字节一致。[lit](profgen/impl/evidence/07/23_patch5_lit_summary.json)、[C1](profgen/impl/evidence/07/24_patch5_c1_summary.json)、[重放](profgen/impl/evidence/07/29_full_export_comparison.json)。
- 新工具SHA `05ddac1c680fd34e21b4c2bfc424c792d2d1a1155fbed2e4d754e39242f4bfb6`。合成负载规模测量：20函数137117起点，avg+补零0.399秒/96000KiB；全部5594可执行范围输入，4598 usable→4090函数/1041309起点，2.572秒/306612KiB。996样本缺DWARF函数被排除，不能声称所有.text均补零。只作规模观测，不作实际采样或avg正确性证据。[两档](profgen/impl/evidence/07/28_synthetic_zero_scale.json)
- 未连接板子，未改设计、认证或索要密码，无新增已知边界例外。正式非增量构建前必须撤销spec本地测试改动；原停止记录下列保留为历史。

## 前轮授权与执行状态（2026-11-02；补丁4小修完成，补丁5因素材冲突停止，历史）

- 计划：先补丁4小修及GBS/lit/C1，再完成补丁5按需边界、avg、补零、skid及全部交叉核对。冻结v0.7 SHA仍为 `eec6b208d8e1fedb840f0933eb20a37c188890b6c8c29e43986c5c9bbca9f6be`；未改设计、未连接板子、不推LLVM远端/Gerrit。[报告](profgen/impl/07_patch5_boundaries.md)
- 已闭合：补丁4从 `de8171b77cec5e547c8ffc2f7a5039a8b39b8577` amend为 `aef395b32e27d5f63468c5d49f76f43508dbf270`，修正sample+显式period-unit错误、非叶子原始line0诊断；相对原补丁4为8文件+54/-5行及3704B素材。重新导出0004；spec原有diff逐字节不变、未提交。[审计](profgen/impl/evidence/07/11_commit_audit.json)
- GBS增量22:30:41–22:48:17+08:00成功，1056.634秒、Ninja105步、GBS_EXIT0/ALL-END OK。GBS内首次lit因旧测试输出有1 FAIL；负对照增加清理自身旧输出后，用同一GBS工具重跑全lit为69 PASS/0 FAIL/1 UNSUPPORTED/1 XFAIL，原50逐项不变。C1每遍636项、两遍一致、0差异。通过后才开始补丁5。[构建/失败/复测](profgen/impl/07_patch5_boundaries.md#3-构建litc1与失败原文)
- 人工裁决前提：补丁1的pure-a64、bad-a64-start/end在.text 0x1000均有合法局部NOTYPE的$x和$d；冻结5.7.2要求冲突失败，而指定pure-a64 golden要求通过，另外两项不能独立覆盖起止边界错误。按“无法按原文测试则停下”停止，未自行放行、改golden或修正原素材。[原始证据](profgen/impl/evidence/07/01_a64_mapping_conflict.txt)、[预期冲突](profgen/impl/evidence/07/02_frozen_test_conflict.json)
- 补丁5仅有本地未提交草稿与有行表的派生素材；无LLVM补丁5 SHA、无正式0005导出、无第二轮GBS验收。真实20函数/objdump、完整测试矩阵、耗时/RSS、全导出重放均未做，不用补丁4结果替代。继续前需PM裁决是否允许修正三份A64素材的代码表达（如同字节.inst），保持冻结规则和golden。[草稿清单](profgen/impl/evidence/07/12_patch5_wip_manifest.json)
- 挂账：head补零兜底尚未验收，不能关闭；IP 新选项改为枚举类型与 cl::values，补丁 7 处理；非叶子帧行号为 0 的处理，上板后按实测数据决定。spec本地改动正式非增量构建前必须撤销；不修改结果仓库未跟踪config/、gbs_*.conf。

## 前轮授权与执行状态（2026-11-02；补丁3修正与补丁4已完成，历史）

- LLVM补丁3从 `30ceb73e9dcbe233f747d1ed8c97d9e3919564b0` amend为 `399a72494db096f27e5c06f7464a5815a659f5fa`；无关buildid-list冲突仅诊断，候选冲突仍mismatch。独立GBS/lit/C1通过后才开始补丁4。
- LLVM补丁4 `de8171b77cec5e547c8ffc2f7a5039a8b39b8577`，33文件、+1,045/-198行，新增7项lit；完成IP专用加载、period/sample、sum/max、精确取整、分层total、顶层head估计、分类与安全写profile。[报告](profgen/impl/06_patch4_counting.md)、[补丁4](../patches/profgen/0004-llvm-profgen-Generate-line-level-profiles-from-IP-sa.patch)、[提交审计](profgen/impl/evidence/06/17_commit_audit.json)。只提交工具/测试目录，未推LLVM远端或Gerrit。
- 三轮GBS均退出0：补丁3独立964.136秒/103步；补丁4初次1942.871秒/112步；补丁4最终1707.474秒/102步（20:18:51–20:47:19+08:00，ALL-END OK）。初次lit两项测试预期错误已修正并留证。主机available采样最低7,582MiB，无低于2GiB采样点。
- 最终lit70项：PASS68、FAIL0、UNSUPPORTED1、XFAIL1，原50逐项不变；C1每遍636条、两遍一致、对原基线0差异，20个新增IP测试排除。[lit](profgen/impl/evidence/06/08_final_lit_summary.json)、[C1](profgen/impl/evidence/06/09_final_c1_summary.json)。新工具SHA `82af1d6a442bcb3771609c0fbdfe05570471321276042b3c8d22ec09c7953ac0`。
- GNU addr2line/readelf独立核对9组完整profile树0差异；14次完整导出地址/reader输出与补丁2逐字节一致。[GNU核对](profgen/impl/evidence/06/10_independent_counts.json)、[真实重放](profgen/impl/evidence/06/11_full_export_comparison.json)。
- 实测偏离任务预测：05/09的strip libavcodec目标全部outside、usable0而失败不落盘，但少量样本属于plt，其余no_cu；9份plt计数/period和均与GNU节范围独立核对一致，遵守冻结5.4.2，没有改分类规则。[证据](profgen/impl/evidence/06/15_real_plt_verification.json)。
- 用户已授权head兜底用例延期：补丁4只创建正body与有样本的内联树，原始head估计为0分支不可达；报告附实际代码不变量证明，补丁5补零后补用例。设计与库函数不变。
- 下一步等待补丁5授权。avg/补零/skid枚举留5，质量报告与兜底回调留6；Agent设计开发仍在增强完成后。spec本地diff保持02原样、未提交，**正式非增量构建前必须撤销**。未连接板子、不改认证或索要密码；无新增已观察到的越界文件写入。

## 前轮授权与执行状态（2026-11-02；llvm-profgen补丁3，修正前已完成，历史）

- LLVM本地提交 `30ceb73e9dcbe233f747d1ed8c97d9e3919564b0`，16文件、+1,185/-71行，新增5个lit文件；只改工具/测试目录。[报告](profgen/impl/05_patch3_identity.md)、[补丁3](../patches/profgen/0003-llvm-profgen-Add-build-id-identity-checks-for-IP-sample-mode.patch)、[提交审计](profgen/impl/evidence/05/14_commit_audit.txt)。未向LLVM远端或Gerrit推送。
- 实现build-id证据分级、保守汇总、分离调试文件身份链、probe拒绝及身份失败无输出副作用。用户澄清：目标无ID/输入有ID为mismatch；目标有ID/输入缺证据为unverified；目标与debug单边缺ID双向均为mismatch。
- **生效的授权规则修正（5.3.3.5）：** generation=0视为未知；只有不同非零generation才冲突，设备/inode不同仍冲突。理由、源码、测试单独登记在[报告3.2节](profgen/impl/05_patch3_identity.md)；设计v0.7文件正文和SHA保持不变。已知局限：inode复用且一条generation未知时，替换可能无法被发现，等级仍为unverified。
- 最终GBS增量18:15:40–18:31:17+08:00成功，936.802秒、Ninja105步、GBS_EXIT=0、ALL-END OK；两次成功构建计时合计2,013.349秒，第二次为授权generation修正。available最低13,009MiB。最终工具SHA `745d9994dc94394a1125836c6196935fbcd8dc3e274b87d4609202f5da4fbcb6`。[构建](profgen/impl/evidence/05/10_final_build.txt)
- 最终lit 63项：PASS61、FAIL0、UNSUPPORTED1、XFAIL1；原50逐项不变，补丁2的8项与补丁3的5项全部PASS。C1每遍636条、两遍一致、与既有基线0差异；13个新IP测试按规则排除。[lit](profgen/impl/evidence/05/11_final_lit_summary.json)、[C1](profgen/impl/evidence/05/12_final_c1_summary.json)
- 8次真实身份验收符合预期；14次完整导出目标重放均通过身份门禁后到达固定过渡错误，地址计数与补丁2逐字节一致（仅排除新增IP-IDENTITY诊断）。仍不生成profile。[完整重放](profgen/impl/evidence/05/09_final_full_exports.json)、[身份重验](profgen/impl/evidence/05/09_final_real_identity.json)
- 05 multi/09 multi/07 module候选路径的generation=0/非0映射数分别1/2、2/2、60/535；零值行均在首个样本前，仅作佐证、不作判定规则。[逐条位置](profgen/impl/evidence/05/08_generation_positions.json)
- 下一步等待补丁4授权；不开始Agent设计开发。spec本地改动保持原样且未提交，**正式非增量构建前必须撤销**。未连接板子，未修改认证或索要密码，无新增已知项目文件边界例外。

## 前轮授权与执行状态（2026-11-02；补丁2收尾，已完成，历史）

- 完整真实导出先验收后修改：05/07/09共13份完整文本、14次目标运行，全部行被接受；修改后stdout/stderr逐字节一致。05单/双目标6,496/13,289与09单/双5,865/14,331，按保存MMAP2/PT_LOAD独立重算逐VA计数及period和均0差异。[报告](profgen/impl/04_patch2_followup.md)、[前后比对](profgen/impl/evidence/04/05_real_export_comparison.json)
- 06完整loss1文本未保留，仅有过滤LOST行及perf.data；独立核对942条、L=61,667，但无法证明完整样本行数等于record的703,821。未重导或重采，没有发现需用户裁决的新格式。07 deleted/模块分类正确；07无-1样本，09 multi的1条-1/-1计为pid_unknown与kernel。[材料限制](profgen/impl/evidence/04/02_loss06.json)
- 完成缺binary、负pid、regex help、非法hex尾缀和LLVM文件头小修；LLVM补丁2从 `8f4fa360ade28a7b044fd5ef392d4839311545aa` amend为 `6e1b1b00c18b52de84351752767f0678113036f6`，最终14文件+877/-5行，8个IP lit文件。导出补丁已覆盖，反向应用检查通过；spec未提交、内容未变。[审计](profgen/impl/evidence/04/06_amend_audit.txt)
- 同配置GBS增量一次成功：15:56:59–16:13:52+08:00，1,012.782秒、Ninja105步、GBS_EXIT=0、ALL-END OK；available最低15,812MiB。新工具SHA `0afa78538527548dfaf9f0f373475f52d621ceb8be1b37db20ce1dc5485926e4`。[构建](profgen/impl/evidence/04/04_build.txt)
- lit 58项：PASS56、FAIL0、UNSUPPORTED1、XFAIL1，原50结果不变、新8项全通过；C1每遍636条，两遍一致且与既有清单0差异。[lit](profgen/impl/evidence/04/04_lit_summary.json)、[C1](profgen/impl/evidence/04/05_c1_summary.json)
- 最大完整导出1,044,585行，旧/新工具墙钟1.405509/1.384008秒，子进程峰值RSS304,924/305,012KiB，单次热缓存观测。冻结设计与C1基线未改；未连接板子、未推Gerrit、未改认证。下一步等待补丁3授权，IP profile生成仍未实现；开发spec **正式非增量构建前必须撤销**。无新增已知项目文件边界例外。

## 前轮授权与执行状态（2026-11-02；llvm-profgen 补丁2，收尾前，历史）

- 已按本轮授权实现 IP 文本读取、显式选项门控、dsoff→ELF VA 换算和 AddressCounter。冻结版 v0.7 与 C1 基线清单未改；未连接开发板、未推 Gerrit、未开始 Agent 开发。[报告](profgen/impl/03_patch2_reader.md)
- LLVM 本地提交 `8f4fa360ade28a7b044fd5ef392d4839311545aa`，13 个文件、+816/-3 行，范围仅 llvm/tools/llvm-profgen 与 llvm/test/tools/llvm-profgen；导出[补丁2](../patches/profgen/0002-llvm-profgen-Add-IP-sample-reader-and-dsoff-address-conversion.patch)，52,407 字节，反向应用检查通过。spec 未提交；GBS 的未跟踪生成物保留在 temp。[审计](profgen/impl/evidence/03/07_commit_audit.txt)
- IP 模式仍为分阶段实现：成功读取/换算后固定退出1，报 `IP sample mode: profile generation is not implemented yet`，不创建或覆盖 output。隐藏诊断 `--show-ip-address-counts` 为本轮授权的测试接口，未加入冻结设计表；身份/权重/生成/边界/报告等留后续补丁。
- GBS增量共三轮：首次新代码编译错误已修正并保留失败证据；第二轮成功，6个新lit通过；补强边界后最终轮14:42:43–14:56:15+08:00成功，812.070秒、106步、GBS_EXIT=0、ALL-END OK。三轮构建计时合计1804.910秒；available最低15,226MiB，无低于2GiB采样点。[构建](profgen/impl/evidence/03/03_build_records.txt)
- 新工具已重新编译/链接，SHA `b60ba7bb7dd07270da60bae8ff8b292209b506ef2c763f6e0ebe9722b596c69e`。最终lit 57项：PASS55、FAIL0、UNSUPPORTED1、XFAIL1；原50项保持48/0/1/1，新增7项全部通过。[lit](profgen/impl/evidence/03/04_lit_classification.json)
- C1：127原命令＋508格式变体＋1纯IP负对照，636行/遍，两遍一致，与原清单0差异；7个新测试正确排除，原50测试相对f999不变。默认纯IP仍退出1及原 `Invalid perf script input!`。[复核](profgen/impl/evidence/03/05_c1_summary.json)
- 下一步等待补丁3授权；没有发现需改冻结规则才能完成本补丁范围的情况。开发spec两处改动继续仅本地保留，**正式非增量构建前必须撤销**。无新增已知项目文件边界例外，未改认证配置或索要密码。

## 前轮授权与执行状态（2026-11-02；补丁2前C1/lit准备，历史）

- 本轮只修正项目侧C1脚本、存档基线工具、补齐开发用lit环境；未修改llvm-profgen源码、既有测试或设计，未连接开发板、未推Gerrit，未开始补丁2。[报告](profgen/impl/02_lit_env.md)
- 构建前存档到 `temp/profgen-baseline-tool/`：llvm-profgen SHA `a31073338f9315a0fd6d2934e36431d9135086882ebfb07bd1bda7c36d7f9f1e`，实际加载的libLLVM.so.22.1 SHA `2c07f047841853eaeab97ab69a285e28941e8b8983706ec76183065791dd914a`；GBS loader --list确认来源及存档解析。[证据](profgen/impl/evidence/02/01_archive.json)
- C1 compare固定为基线登记的测试/行/格式；原测试相对f999bd4有改动即停止；先验矩阵对齐再比较内容。增加库目录参数，实际argv0固定以消除存档路径引起的帮助提示差异，不归一化stderr。存档与构建后工具各两遍636行，均与原基线0差异；原清单不变。[存档复核](profgen/impl/evidence/02/04_archive_c1.json)、[构建后复核](profgen/impl/evidence/02/10_rebuilt_c1.json)
- 同一root/config/worktree的GBS增量构建成功：11:05:43–11:20:13+08:00，870.697秒，GBS_EXIT=0、ALL-END OK，Ninja126步（原基线7633）。没有重跑、没有未打包文件错误。新工具SHA及mtime不变，没有重新链接。[构建](profgen/impl/evidence/02/07_build_record.txt)
- 原有lit基线：PASS48、FAIL0、UNSUPPORTED1（cs-preinline-cost.test，requires asserts）、XFAIL1（invalid-perfscript.test）；assertions=No保持不变，没有修复或额外跳过测试。LLVM site配置缺失已闭合。[lit日志](profgen/impl/evidence/02/09_lit.log)、[xunit](profgen/impl/evidence/02/09_lit.xml)
- 开发工作树 `packaging/llvm.spec` 仅开启LLVM_INCLUDE_TESTS并添加%check；未提交到LLVM分支，HEAD仍为补丁1。**正式非增量构建前必须撤销**；后续补丁只显式暂存工具、测试、文档，不能把该spec带入。
- 下一步等待补丁2授权。Agent设计与开发仍在llvm-profgen增强完成后；无新增已知项目文件边界例外，未改认证配置或索要密码。

## 前轮授权与执行状态（2026-11-02；llvm-profgen 补丁 1，历史）

- 已获本轮实现授权，范围为测试素材与 C1 原行为基线；冻结设计仍为 v0.7，SHA 不变。没有修改 llvm-profgen 源码、既有测试、spec 或设计，没有 GBS 构建、板上操作或 Gerrit 推送。
- LLVM 本地分支 afdo/profgen-enhance 提交 `00fa352d531680f0bf4a55dec21b30bacfcd4092`，只新增 Inputs/ip-mode 的104个文件、366795字节（46个ELF共255656字节）；二进制 format-patch 已在独立 index 对原基线应用检查通过。[报告](profgen/impl/01_patch1_test_inputs.md)、[补丁](../patches/profgen/0001-llvm-profgen-Add-test-inputs-for-IP-sample-mode.patch)
- C1：50个现有测试、127条原命令＋508条固定格式变体＋1条纯IP负对照，每遍636次，两遍全部一致；归档的636份stderr、636份stdout、585份profile另作直接字节比对。失败/提前退出行为均保留，不能把运行次数当作测试通过数。[清单](../tools/profgen/c1-baseline.json)、[摘要](profgen/impl/evidence/01/10_c1_summary.json)
- 基线工具SHA仍为 `a31073338f9315a0fd6d2934e36431d9135086882ebfb07bd1bda7c36d7f9f1e`；纯IP保持退出1与 `Invalid perf script input!` 原文。lit辅助工具齐全，但LLVM_INCLUDE_TESTS=OFF、LLVM site配置未生成，本轮按约束未运行或补建；assertions专用原测试只记录当前Release工具的参数错误。[lit盘点](profgen/impl/evidence/01/07_lit_inventory.txt)
- `[unknown]`按perf源码格式的合成素材已补；没有发现冻结规则无法构造素材的情形。同址多节素材仅供边界单元测试，objcopy probe组合不能替代真实Tizen拆分证据，详见报告限制。
- 下一步等待补丁2授权；完整lit验收需后续补齐配置，不能因C1重放一致宣称全部lit通过。Agent设计与开发仍在llvm-profgen增强完成后才开始。无新增已知项目文件边界例外。

## 前轮授权与执行状态（2026-10-30；设计v0.7归档与第一阶段冻结，历史）

- 当前设计版本为 [v0.7](profgen/design/02_llvm_profgen_enhance_design_v0.7.md)。第一阶段（正确性规则与契约，第10节步骤2的范围）已冻结；v0.6限定范围复核（Codex、Claude Code）已处理，记录见附录F。
- 冻结后对冻结范围内规则的修改，需单独提出并在设计文档中记录。
- 交付前的非★项：新LLVM发布后复核默认build-id；aarch64 Tizen debuginfo的`$x/$d`；probe构建拆分后`.pseudo_probe/.pseudo_probe_desc`的位置；补存DWARF5拆分核对与BUILD目录产物build-id的证据；`[unknown]`素材。
- 第二阶段待定事项见设计文档第12节。挂账不再包含LOST_SAMPLES实测：v0.6起已不支持从文本读取这类记录，不再是待办。
- 下一步：等待实现授权；本轮只移动文件与记录状态，不修改设计文档内容，不开始任何实现。Agent设计与开发仍在llvm-profgen增强完成后才开始。
- 按用户授权，仅用mv移入Downloads中指定的v0.7文件；移动前后SHA-256均为`eec6b208d8e1fedb840f0933eb20a37c188890b6c8c29e43986c5c9bbca9f6be`，行数均为1015，源文件已不存在。v0.5、v0.6原位保留且内容不变，未触碰Downloads其他文件；本次指定文件移动属于用户授权的边界例外。

## 前轮授权与执行状态（2026-10-30；设计v0.6归档，历史）

- 当前设计版本为 [v0.6](profgen/design/02_llvm_profgen_enhance_design_v0.6.md)。本轮仅移动文档与记录状态，不修改文档内容，不开始任何实现。
- v0.5第三轮评审已处理（Codex、Claude Code；Kimi Code未参加），处理记录见v0.6附录E。
- 第一阶段的★前置项已全部闭合：[08](probe/08_buildid_split_check.md)验证build-id拆分；[09](probe/09_rpi5_prefreeze_checks.md)验证RPi5的dsoff、buildid-mmap和页大小。
- 交付前的非★项：新LLVM发布后复核默认build-id；确认aarch64 Tizen debuginfo的`$x/$d`；补存DWARF5拆分核对与BUILD目录产物build-id的证据；`[unknown]`素材。
- 下一步：等待限定范围复核或第一阶段冻结的决定；前置项闭合不等于已授权实现，Agent设计与开发仍在llvm-profgen增强完成后开始。
- 按用户授权，仅处理Downloads中指定的v0.6文件，用mv移入仓库；移动前后SHA-256均为`f4342dad5ffaea1e102c20744c73dcb3dfcb402162daac4ed4b7b0d320cff231`，行数均为953，源文件已不存在。v0.5原位保留且内容不变，未触碰Downloads其他文件；本次指定文件移动属于用户授权的边界例外。

## 前轮授权与执行状态（2026-10-30；RPi5 v0.5冻结前板上核实，历史）

- 设计当前版本仍为v0.5，内容未修改；只验证与记录，不改LLVM、不开始增强或Agent实现。没有GBS构建，没有板上装卸RPM、remount、重启或/tmp执行。
- 初次连接失败，用户确认开机后重连；身份断言aarch64、6.12.80-arm64-rpi4-v8通过，model为RPi5。当前镜像20261028.105834，比04更新；页大小4096。原工具不存在，按04哈希恢复aarch64 perf/libLLVM、依赖解析通过。[E1](probe/evidence/09/01_environment_cleanup.txt)
- 真硬件cycles type=0/config=0；固定周期7,617样本。libavcodec单进程5,865条及双进程14,331条dsoff公式/唯一可执行PT_LOAD均100%通过；两个解码pid基址不同。可执行段仍offset=vaddr=0，未覆盖不等布局。[E2](probe/evidence/09/02_sampling_formats.txt)、[E3](probe/evidence/09/03_mapping_buildid_period.txt)
- --buildid-mmap exit0；libc的MMAP2与GBS readelf ID均为8b45bf5b6a314fc498c8c73f164d6259c895405b（20字节），1/1匹配。libavcodec仍无ID；buildid-list两种录制均非空。固定period均1000003；频率模式2,431种取值，行为与05/v0.5一致。
- 新观察：multi系统级内核样本有一条pid/tid=-1/-1；v0.5未明确此负值例子的语义，报告保留原文，不修改设计。未出现([unknown])；按源码格式编写素材仍挂账。
- work已删除全部内容并验空；仅保留perf/libLLVM，哈希不变，RPM前后1249。/opt清理后已用96,816KiB、可用1,208,800KiB、8%，专用目录70,400KiB。[E1](probe/evidence/09/01_environment_cleanup.txt)
- 冻结前剩余项：新LLVM发布后的原样构建复核；[unknown]样例按源码格式编写素材。RPi5的dsoff、--buildid-mmap、页大小本轮闭合；设计冻结仍待评审决定，主机perf准入和第二阶段IR/BFI实验保留。
- [09报告](probe/09_rpi5_prefreeze_checks.md)、三份证据（122,412字节）及本状态同一commit提交。无新增已知边界例外；历史SDB共享服务外部日志的隐式写入未审计。

## 前轮授权与执行状态（2026-10-30；v0.5归档与build-id调试拆分核实，历史）

- 设计当前版本为 [v0.5](profgen/design/02_llvm_profgen_enhance_design_v0.5.md)，正文未修改；SHA-256=`1e70bac98024bfa45dc5505bb315565fd7a1591c9cfcf5ba0e24747b3d45a8cf`。校验后用mv移入指定Downloads文件，源路径已不存在，其他Downloads文件及v0.1–v0.4不动。
- 本轮不连接开发板、不改LLVM、不开始实现。07的临时FFmpeg worktree分支afdo/v05-buildid仅在spec configure调用新增一行`--extra-ldflags="-Wl,--build-id=sha1"`；原src/ffmpeg干净。临时提交8a50cbfdc1383a34b781756c73c6252d86e6e1ad只本地保留；不推FFmpeg/Gerrit。
- GBS armv7l构建成功，64秒，真实GBS_EXIT=0、ALL-END 2026-10-30T21:20:41+08:00 OK；实际链接argv包含sha1选项，CFLAGS不变、LDFLAGS仅该新增项。[证据](probe/evidence/08/01_build.txt)
- 运行文件与.debug均有可读`.note.gnu.build-id`、SHT_NOTE（非NOBITS），build-id同为`f960461f63c852474257f51267b7b543afffdc9c`，20字节完全一致；debuginfo RPM的两个.build-id链接正确。补齐07缺有ID拆分正例的缺口。[证据](probe/evidence/08/02_elf_split.txt)
- 符号/属性保留方式与07一致；.debug的$a/$t/$d为27/5883/6489，其中$t比07多1；运行文件无.symtab及ARM属性。DWARF5 debugedit警告仍在，不据note成功认定完整行表/源码路径修写质量通过。未重做边界核对。
- 剩余冻结前项：RPi5的dsoff、`--buildid-mmap`、页大小；新LLVM发布后的原样构建复核（默认build-id及拆分结果）。第一阶段冻结仍待评审确认，不因本轮验证通过自动开工；IR/BFI等第二阶段前实验和主机perf决策保留。
- [08报告](probe/08_buildid_split_check.md)、v0.5、两份证据（39326字节）及本STATUS同一commit提交。本轮仅指定Downloads移动这一用户授权例外，无新增已知其他边界例外。

## 前轮授权与执行状态（2026-10-30；v0.4归档与主机/RPi4冻结前核实，历史）

- 设计当前版本为 [v0.4](profgen/design/02_llvm_profgen_enhance_design_v0.4.md)，正文未改；SHA-256=`abceb98ae958e20c4436e88c45da88c154ec4d29e0bc56939f0828530ddef4cf`。按用户授权校验后用mv从指定Downloads路径移入，源文件已不存在，其他Downloads文件及v0.1–v0.3不动。
- 本轮只做验证与记录，未改LLVM/原FFmpeg源码或spec；一次性边界脚本与测试包留在temp，不开始增强或Agent实现。v0.4第一阶段评审/冻结仍待确认，不以本轮验证结束自动开工。
- 原样FFmpeg在独立GBS root构建成功（GBS_EXIT=0、带时间ALL-END OK），产出运行与debuginfo RPM。调试文件保留.symtab、$a/$t/$d=27/5882/6489和.ARM.attributes，代码节NOBITS；运行文件无这些符号/属性。两份均没有build-id note，不能称已验证build-id身份一致性；默认链接无build-id，与06镜像现象一致。[构建/ELF证据](probe/evidence/07/01_build.txt)
- 20个最大Thumb函数（也覆盖所取含$d前20）指令边界全部一致；另对3个st_size=0的CRT A32符号作有界范围补充，总132871个起点无差异。零大小符号的推导上界不等同DWARF函数范围验收。thumb与thumbv7a差异已复现，前者警告但仍exit0。[证据](probe/evidence/07/03_boundaries.txt)
- RPi4 fork父/子目标样本4923/4917，偏移100%一致，子无自有MMAP2；exec后旧映像样本0；deleted最终正常录制151条，模块1729条，未出现([unknown])。deleted前两次返回143/130，保留失败证据，不当成功；最终record和子进程均0。[证据](probe/evidence/07/04_board.txt)
- 板上work已清空；只保留原perf/libLLVM；RPM前后1252；/opt清理后已用82788KiB、可用1222800KiB、7%，专用目录du前后35796KiB。未remount、重启或装卸RPM。
- 剩余RPi5项：dsoff及公式核对、`--buildid-mmap`、页大小。第二阶段前按v0.4新规则重跑IR/BFI核实；主机x86_64 perf构建仍待用户决定。当前FFmpeg没有有ID的note保留正例，debugedit的DWARF5警告与完整行表/源码路径质量未在本轮核验。
- [07报告](probe/07_v04_prefreeze_checks.md)、v0.4、四份新增证据（99680字节）及STATUS同一commit交付。只有本次指定Downloads移动这一授权例外，无新增已知其他边界例外；历史SDB服务内部写入审计限制保留。

## 前轮授权与执行状态（2026-10-30；llvm-profgen增强设计v0.3归档，历史）

- 设计当前版本为 [v0.3](profgen/design/02_llvm_profgen_enhance_design_v0.3.md)，依据 [05](probe/05_rpi4_pmu_image_and_prefreeze.md)、[06](probe/06_rpi4_prefreeze_followup.md) 冻结前核实修订，修订表见附录 B；进入第二轮三方评审。冻结前不开工，Agent 的设计与开发在 llvm-profgen 增强完成后才开始。
- 冻结前核实剩余项：RPi5 的 dsoff、`--buildid-mmap`、页大小；aarch64 IR 匹配按 v0.3 的 5.8 第 2 条重跑；Tizen debuginfo 是否保留 `$a/$t/$d` 映射符号。
- 待用户决定：是否在工作目录内为 x86_64 构建主机 perf，决定 `--perfdata` 能否进入第一批。本次仅归档，不执行评审、板上核实、构建或实现。
- 按用户授权的一次性例外，只处理 `/home/linhao/Downloads/02_llvm_profgen_enhance_design_v0.3.md`：SHA-256及标题前缀校验通过后，用 `mv` 移入仓库，移动后哈希一致、Downloads 原文件已不存在；未触碰该目录其他文件，v0.1、v0.2 保留不动。
- v0.3 文档内容未修改，SHA-256=`fd093bb7b0c5a19599b21b480ccc9bb06a542e9b3ea144628c54e659e74b50f3`；仅与本 STATUS 同一 commit 提交推送。

## 前轮授权与执行状态（2026-10-30；v0.2 冻结前补充核实，历史）

- 本轮完成 RPi4 与主机补证；只改获授权的 IR 匹配原型、报告与状态，不改 LLVM 或设计。v0.2 仍未冻结，待用户评审决定；Agent 开发仍在 llvm-profgen 增强完成后开始。
- Thumb：拉取13库＋5程序并核对SHA；GBS项目armv7l optflags含 `-mthumb`，FFmpeg/GLib/GStreamer/libstdc++已定义动态FUNC均为Thumb；libc/加载器偏ARM，裸clang spike自有C函数为ARM。这与v0.2“默认A32”前提不符。[证据](probe/evidence/06/01_thumb.txt)
- IR：生成/使用均禁用preinline，GBS真实退出0、带时间ALL-END OK，RPi4训练checksum与05相同；加入零权边后PGO/sample边数覆盖44/45与44/46，IR权重覆盖100%与97.16%。仍有switch/br相同键但后继语义不同，不能以100%覆盖宣称质量比较成立；原型保留重复键拒绝及自匹配，并报告形态差异。[证据](probe/evidence/06/02_ir_matching.txt)
- 主机perf：查同源20261022、相近20261027、reference、配套Base均无x86_64 linux-kernel-perf；新镜像20261028仓库404。无主机工具，05同数据跨主机逐行比对仍未完成，不安装或编译替代工具。[证据](probe/evidence/06/03_host_perf.txt)
- LOST已补实测：cycles -c10007 -m1、1080p约20秒媒体，942条LOST/61667丢失样本、8.06%；pswpin/pswpout保持26/613。LOST_SAMPLES未实测。[证据](probe/evidence/06/04_lost_cleanup.txt)
- 板上work为空，仅保留原perf/libLLVM；RPM前后1252；/opt清理后已用73412KiB、可用1232176KiB、6%，专用目录前后35796KiB。分区增加928KiB而专用目录大小不变，不删除其他目录追平占用。
- [06报告](probe/06_rpi4_prefreeze_followup.md)、四份证据、匹配原型和本状态同一commit提交。新证据总量低于150KB，旧证据保持不动；无新增已知边界例外，历史SDB服务内部写入审计限制继续保留。

## 前轮授权与执行状态（2026-10-29；RPi4 PMUv3 新镜像与 v0.2 冻结前核实，历史）

- 用户已授权并完成第 10 节步骤 1 的本轮板上/主机核实及可选 armv7l spike；不修改 LLVM 代码或设计文档，不开始增强实现。设计当前版本仍为 v0.2（未冻结、第二轮评审前），是否进行第二轮评审与冻结由用户决定。
- RPi4 身份断言通过；镜像 Unified 20261028.105834，armv8-pmu 已绑定 A72，cycles type=0/config=0，7,659样本；硬件PMU已在新镜像实测通过，页大小4096。
- dsoff 固定数据6,496条、双进程13,289条 libavcodec 样本公式/PT_LOAD均100%一致。固定period=1000003，频率模式逐样本变化；buildid-mmap与ELF非空ID实测匹配。
- 设计差异/未闭合项：buildid-mmap的buildid-list实际非空；vdso带偏移；Thumb符号区间需清除状态位；IR带权分支匹配15/17与15/23。没有产生LOST、无主机x86_64 perf、RPi5页大小本轮未测，不能宣称整个冻结门槛已闭合。
- armv7l插桩PGO在约7分30秒内闭环：两轮GBS退出0/ALL-END OK，base/instr/pgo校验同为ff818b861cb93a67；不推断性能收益。只在temp测试包中改架构宏与训练profile，原spike和LLVM源码不改。
- 板上work已清空，保留perf/libLLVM；/opt最终已用70628KiB、可用1234960KiB，RPM前后1252，pswpin/pswpout前后26/613。未remount、重启或装卸RPM。
- [05报告](probe/05_rpi4_pmu_image_and_prefreeze.md)、[本轮四份证据](probe/evidence/05/01_environment_hardware.txt)（146,877B）、[IR匹配原型](../tools/match_ir_branches_prototype.py)与本状态文件同一commit提交；旧证据、设计不动。执行偏差与历史SDB边界限制在报告末尾如实保留。

## 前轮授权与完成状态（历史；llvm-profgen 增强设计 v0.2 归档）

- 设计文档当前版本为 [v0.2](profgen/design/02_llvm_profgen_enhance_design_v0.2.md)（第二轮评审前）；v0.1 三方评审已处理完毕，处理表见 v0.2 附录 A。v0.1 文件保留不动。
- 待决事项：是否进行第二轮评审、是否先做第 10 节步骤 1 的冻结前板上核实，均由用户决定。本轮只移动归档和提交，不执行评审、板上核实、构建或代码修改；冻结前不开工，Agent 的设计与开发仍在 llvm-profgen 增强完成后才开始。
- 按用户授权的一次性例外，仅读取并用 `mv` 移入 `/home/linhao/Downloads/02_llvm_profgen_enhance_design_v0.2.md`；移动前 SHA-256 和标题校验通过，移动后哈希不变，已确认 Downloads 原文件不存在，未触碰其他 Downloads 文件。
- 仓库内文档 SHA-256：`b4b03533513b23aa06b26def0faa342445dca128f0602c013cd8545cc26f99cf`；内容未修改，仅与 STATUS.md 同一 commit 提交推送。

## 前轮授权与完成状态（历史；llvm-profgen 增强设计 v0.1 归档）

- [llvm-profgen 增强设计 v0.1](profgen/design/02_llvm_profgen_enhance_design_v0.1.md) 已提交，待多方评审，**冻结前不开工**；Agent 的设计与开发在 llvm-profgen 增强完成后才开始。
- 文档内容未修改。SHA-256=`9a81267b33d1ea59ed84975baabb5802561ca6943219a2070ad2530707231053`；第一行以 `# llvm-profgen 增强设计` 开头；第10行“适用范围”含“不包含任何 Agent 的设计与开发”，三项核验通过。
- 本次从 `/home/linhao/Downloads/02_llvm_profgen_enhance_design_v0.1.md` 移入这一个文件，属于用户授权的例外；核验后已删除该原文件，并确认其不存在，未触碰 Downloads 下其他文件。以后用户放在 Downloads 的材料一律移动到工作目录，不在 Downloads 保留副本。
- 本次只提交设计文档和 STATUS.md，不执行评审、源码修改或构建。

## 前轮授权与完成状态（2026-10-28；llvm-profgen 增强准备，已完成）

- 本轮只读分析 GBS/depanneur/Google AutoFDO/llvm-profgen，完成一次未修改 llvm x86_64 全目标基线构建；不修改 LLVM 跟踪源码/spec，不连接开发板，不推 Gerrit。**停在设计确认阶段，不开始增强实现。**
- src/llvm 开始/结束 status 均为空，HEAD=f999bd406c0a70fe8107aa992164fe6945c5d46a；新分支 afdo/profgen-enhance、worktree=temp/llvm-profgen-enh 跟踪文件无改动，仅保留生成资产/对象/manifest。
- 增量结论：可以增量，但须固定 worktree/root/参数并保留对象、提前准备被跳过的 %prep 资产。当前 spec 不必改；修改源码后的增量耗时尚未实测。GBS 每次仍执行完整 %build/%install/产包。
- 构建 20:33:42–21:33:09+08:00，59分27秒，无重跑；GBS_EXIT=0、ALL-END OK。22 二进制 RPM + 1 SRPM 已记录 SHA-256，新编 llvm-profgen 22.1.8 运行退出0；short-circuit RPM 属开发产物，SRPM 不等同完整导出源码。
- 资源采样最低 available=16663 MiB，未观察到低于2GB；load 1/5/15分钟观测峰值15.11/10.58/9.17。全部临时产物仍在 temp/GBS-ROOT-LLVM-X86、temp/llvm-profgen-enh、temp/profgen-prep。
- 交付 [增量与基线报告](profgen/00_incremental_build.md)、[23项差异表](profgen/01_gap_analysis.md)、三份 profgen 证据与本状态文件，同一 commit 推送。无新增已知边界例外。

## 前轮授权与完成状态（历史；RPi5 AutoFDO / 插桩 PGO spike）

- 本轮允许 GBS 构建测试包、板上仅写 /opt/afdo_agent；不改 LLVM/BOLT/内核源码，不安装板上 RPM、不 remount/重启。Google AutoFDO 仅克隆只读、不构建。所有测试与清理已完成。
- llvm-profgen 22.1.8 对 cycles/cpu-clock 两份无分支栈 IP 输入均真实退出 1（Invalid perf script input!），没有生成 profile、没有 AFDO 重编。Google --use_lbr=false 和 BOLT -ba 是源码支持路径，未动态验证。
- 插桩 PGO 在 RPi5 已闭环：7 函数/31 计数块、profile 匹配写入 IR、pgo 三次 checksum 与 base 一致；base 均值 14.2733s、pgo 14.2567s，约 −0.12%，不认定稳定性能收益。RPi4 插桩仍需 armv7l 验证。
- 固定 Unified 20261027.063617 / Base 20261026.051209；首次因平台 debug 拆分导致未打包文件失败，只修正测试 spec 后重试成功，再 profile 重编成功；三次均取得真实 GBS 退出码与带时间 ALL-END。
- work 已清空，RPM 数前后 1249，保留原 perf/libLLVM；无新增边界例外，历史外部 /tmp/sdb.log 元数据未变。
- 交付 [spike 报告](spike/01_afdo_pgo_feasibility.md)、[源码/spec/profile](../spike/afdo-spike/)、四个 [spike 证据](spike/evidence/01_source_analysis.txt)（共 90,836 B）与本状态文件，同一 commit 推送。未编写 Agent 实现。

## 前轮授权与完成状态（历史；RPi5 环境与采样探测）

- 用户已把同 IP 192.168.108.26 的板换为 RPi5；本轮按 model=Raspberry Pi 5 Model B Rev 1.1、uname -m=aarch64 确认，未依赖 SDB 的旧 rpi4 别名。
- 本轮按挂载参数验收 /opt/afdo_agent/ 后部署 aarch64 perf/libLLVM；板上仅该目录可写，另有一次用户明确授权的 /tmp true 执行负对照（已删除）。不 remount、不重启、不安装/卸载 RPM、不改 /boot；无构建。
- **RPi5 真硬件 cycles 与四项硬件计数支持；分支栈不支持；SPE/ETM 当前镜像没有事件源。** 所有 record 后核对 evlist，成功 cycles 为 type 0/config 0，未回退软件。媒体三种采样全部无丢样，按规则不重跑。
- work 已清空，保留 tools/perf 与 lib/libLLVM.so.22.1；RPM 数开始/结束均 1,249。三个实体库只留本机 temp，现有文件缺完整符号表、代码重定位和调试信息，不具备直接 BOLT/源码行 profile 的前提。
- 交付 [04_rpi5_probe.md](probe/04_rpi5_probe.md)、新增证据 E15–E18 与本状态文件，同一 commit 推送。新增证据 128,645 B，不改任何历史证据；原手工安装内核方案仍取消。

## 前轮授权与完成状态（历史；PMUv3 补丁与 RPi4 软件采样）

- **已决定：PMUv3 通过补丁合入 Gerrit，由用户起 Quickbuild 出新镜像；原板上手工安装方案取消。** scripts/pmuv3_install/ 保留但不再使用；以下历史安装授权不再有效。不向 Gerrit 推送任何内容。
- 用户批准最新 tizen 基线只改普通 defconfig 一行；最新分支已删除独立 RT defconfig，RT 由普通配置叠加 rt.config。已检查全部 RT/LSM 片段无 PMU 依赖冲突，补丁提交与独立 git am 验证完成；本轮没有 make/构建。
- 本轮板上写入仅 /opt/afdo_agent/，另明确授权清理旧 /tmp/afdo_probe 和短暂 /tmp true noexec 负对照。工具/媒体校验、依赖解析、软件采样/硬件负对照已完成，work 清空，保留 tools/perf 与 lib/libLLVM.so.22.1。禁止 remount、重启、RPM 安装/卸载、/boot 改动；本轮均未执行。
- 提交补丁、06 补丁报告、03 软件采样报告、证据与本状态文件至本项目 main；不推内核分支。后续新镜像构建/刷写由用户推进；不自动恢复手工安装。

## 前轮只读诊断（历史，已完成）

- 判定 A：普通 kernel/modules 两包均不在 RPM 数据库，模块目录无 RPM 归属。/boot 未挂载；未获取 zImage 哈希；旧 RPM BUILDTIME=0，无法与运行内核编译日期直接对应。证据见 [05](kernel/05_preflight_diag.md)。

## 前轮安装授权与停止条件（历史；方案已取消，以下不得再执行）

- 用户已审核 02 安装方案，授权 Agent 将主机命令封装为 7 个独立脚本，执行 01–04 到重启前；四个原板上脚本内容必须保持不变。任一步 END FAILED 就立即停止，保留输出，不修复、不重试、不回退。
- **当前已触发停止：02_board_backup.sh 在已安装包预检返回远端 1，报 STOP: unexpected installed package。** 01 成功；02 尚未备份；03、04 未运行。不能通知用户“可以重启”，先等后续指示。
- 不 remount、不 reboot、不加 --nodeps/--force，不安装/卸载 RT。仅允许指定普通 kernel/modules RPM 安装；当前没有执行任何安装。板型确认是 RPi4 Model B Rev 1.5。
- 后续只有安装检查通过且用户通知“已重启并配好网络”后，才运行 05：新内核身份不符停止全任务；身份正确且未绑定 armv8-pmu 只做软件采样；绑定成功做软件+硬件采样。重启和网络配置始终由用户完成，Agent 不 reboot。
- 用户已为后续采样明确授权 /opt/afdo_agent/tools、lib、work，部署 perf/libLLVM 前先查挂载/空间并做执行负对照；遇 ro/noexec 或库未解析停止。按原任务完成媒体计时、软件/硬件采样、符号统计后清空 work，保留 tools/perf 与 lib/libLLVM.so.22.1，记录 RPM 数量前后相等。**当前尚未进入此阶段，不据此提前部署。**
- 本次交付 scripts/pmuv3_install/01–07、更新后的 02 与本 STATUS。执行输出在 temp/pmuv3-install/logs；临时目录保留供后续处置。最后阶段的 04_boot_verify / 03_sampling 报告须在实测后生成，不能预填结果。

## 上轮构建验收（已闭合）

- 缺少 ALL-END 的构建已按用户批准的三组替代证据验收通过：depanneur success/无 fail、HTML 成功行、15 个二进制 RPM + 1 个 SRPM 与日志/时间窗口/哈希逐项一致。真实 GBS 退出码未知，原 status 不改写。
- 构建包装脚本已静态修复 worker 会话/锁与 setsid --wait，未重新运行；根因机制仍属推断。原源码/config/spec 未改。

## 历史授权：PMUv3 内核构建准备（第一段）

- 仅准备源码分支/worktree、构建配置和一键脚本，Agent **不连接开发板，不执行任何构建，不运行构建脚本**；只用 bash -n 做语法检查。
- 不修改 config/ 下两份用户配置，不修改 src/linux-rpi 检出的文件；唯一源码改动放 temp/linux-rpi-pmuv3 的 afdo/pmuv3 分支。开始/结束原工作树状态必须为空。
- 优先使用本地镜像精确基线 21645b17c0d913e2ba7e10fbc9c993d286b3f57d，不 fetch；本地已存在。内核分支只本地提交，不推送。
- 用户自行运行固定快照的 GBS 构建；专用 HOME、buildroot、tmpdir/cache/log 均在 WORKDIR/temp，隔离只施加到 GBS 及子进程。结果仓库 commit/push 用正常环境。
- 第二段等用户通知构建结束后，Agent 再核对产物并写安装/备份/回退说明；安装、重启和板上验收由用户执行，Agent 不操作开发板。
- 只提交 scripts/build_pmuv3_kernel.sh、docs/kernel/01_pmuv3_build.md 与本次 STATUS 更新。temp/、src/ 不提交。

## 历史授权：补充探测（已结束，不能据此继续连接开发板）

用户最新指令覆盖前一版板上安装授权：允许使用镜像配套 Base-Toolchain 仓库（先查 builddata/manifest/build.xml；查不到才用 config/gbs_llvm.conf 的 Base reference 并注明近似），核对 perf 构建依赖与 libLLVM version-release；只在本机 temp/rpms 用 rpm2cpio/cpio 解包，在板上 /tmp/afdo_probe 部署 perf/所需动态库，以 LD_LIBRARY_PATH 指定临时库目录。**不安装 RPM，不推送/安装 perl，不 remount、不重启。** 推送前查 /tmp 空间，推送后必须用 ldd 或 LD_DEBUG 验证；未解析成功则记录并停止。记录每个推送文件、来源包/版本/仓库/SHA-256，结束清理并比较 RPM 数量。仍只授权本机内核配置目标（O=WORKDIR/temp/，不编译内核），禁止安装主机工具；媒体制作/解码/采样沿用原授权。

# 项目状态

更新：2026-11-06（Asia/Shanghai）。当前设计v0.7第一阶段已冻结；llvm-profgen补丁1–8及RPi4第一轮采集/训练/集成已完成，正式验收与待设计v0.8登记见上方当前状态。下一步等待质量分析/消费构建授权；Agent设计开发尚未开始。各轮探测、spike、构建与历史停止记录保留。**旧提交 e90492e 的探测结论全部作废；后续各轮采用独立证据。** 每个新会话开场先读本文件，收尾时与报告在同一个commit更新。

## 计划

- 24项生成侧构建已完成；RPi4第一轮70组S、14次训练与5集成已闭合，补丁8小修、真实avg、高LOST完整导出已验收。下一步消费构建/配置质量分析等待授权；probe子方案独立挂账。

- 当前设计v0.7，第一阶段（正确性规则与契约，第10节步骤2范围）已冻结；v0.6限定范围复核（Codex、Claude Code）处理见附录F。冻结范围内规则的修改须单独提出并在设计文档中记录。交付前非★项见“挂账”，第二阶段待定事项见设计第12节；补丁1–8与RPi4第一轮已完成，下一步质量分析/消费构建等待指示；Agent设计与开发仍在llvm-profgen增强完成后才开始。

- v0.2 已确定分批范围：原生 perf.data 解析和 SPE 放第三批；内核模块、Chromium 规模放第二批。保留增量 buildroot/worktree；第一阶段已冻结、补丁1至补丁8已授权完成，后续评估与开发等待新授权。

- 本轮工具 spike 已完成，不重复采集/构建。建议 RPi5 默认插桩 PGO；RPi4 先验证 ARM runtime/全链路。Google 无 LBR 转换和 BOLT -ba 保留为需后续授权验证的候选。

- RPi5 环境探测完成；硬件 cycles/计数已验证，分支栈失败、无 SPE/ETM。后续 spike 已验证插桩 PGO，普通 IP 的 llvm-profgen 路径不可用；真实包仍须匹配未 strip/debug 二进制。

- 已交付 patches/0001-ARM-configs-tizen_bcm2711-enable-ARM_PMUV3.patch，用户合入 Gerrit 并发起 Quickbuild；Agent 不推 Gerrit。本轮最新补丁未构建/启动，旧镜像基线构建验证仍单独保留。
- 当前镜像的 perf /opt 部署、软件系统/媒体采样、DSO/符号统计及开销实测已完成；cycles 请求发生软件回退，不能当作硬件采样成功。
- RPi4 新镜像 PMU 绑定及真正硬件cycles已验收。原手工安装方案仍取消，不执行 scripts/pmuv3_install/；后续真实包训练与优化另行授权。

以下为前序探测计划与持续纪律：

- 初轮读取 WORKDIR/src、WORKDIR/config 已提供材料；先两层盘点，不写 Agent 实现。本次补充轮的配置生成和板上 RPM 授权范围见上文。
- 按 model 确认 RPi4，检查 root、系统/内核、perf、媒体素材和实体库静态元数据。
- 下载两个配置共四个启用仓库的 primary/filelists，核对三架构工具包及源码构建声明。
- 重新克隆 CodingSystem、固定 commit 核查契约与实现边界。
- 只提交重要小文本，temp/、src/ 不提交；只 git push，不开 PR。署名 Hao Lin <hao.lin@samsung.com>，仅 local 配置。
- 所有耗时命令 nice -n 19 ionice -c3，不并行大任务。

## 进度

- 2026-11-06：补丁8小修通过；70/70正式组、106份verified转换与14份profdata完成，LOST/五集成/unknown实测闭合，root/governor恢复。原停止记录保留报告12第13节，恢复与最终结果见14–16节。

- 2026-11-04（裁决后）：匹配/统计脚本与板上计划完成，24项spike/FFmpeg生成侧构建及产物核对通过；原R冲突停止记录保留于报告1–6节。[报告11](profgen/impl/11_eval_prep.md)

### llvm-profgen 补丁3（历史，已完成）

- 身份分级/链、probe拒绝及generation授权修正已实现；最终GBS936.802秒/105步，lit61/0/1/1，C1零差异，14次完整重放计数不变。[报告](profgen/impl/05_patch3_identity.md)
- LLVM本地补丁已提交并导出，等待补丁4授权；profile生成仍为过渡错误。

### llvm-profgen 补丁2收尾（历史，已完成）

- 13份完整导出、14次目标运行前后逐字节一致；独立MMAP2/PT_LOAD逐地址核对0差异。06缺完整文本的限制详见挂账。[报告](profgen/impl/04_patch2_followup.md)
- 小修后GBS增量1,012.782秒、105步成功；lit 56 PASS/0 FAIL/1 UNSUPPORTED/1 XFAIL，C1两遍636条且与原基线0差异。补丁2已amend，等待补丁3授权。

### llvm-profgen 补丁2（收尾前，历史）

- 显式IP读取器、dsoff程序头换算、checked uint64计数与隐藏诊断完成；输出仍固定过渡失败，不生成profile。[报告](profgen/impl/03_patch2_reader.md)
- 最终GBS增量812.070秒、106步成功；7个新lit全部通过，原50项不变；C1两遍636行及基线比对均0差异。已导出LLVM本地补丁，下一步等待补丁3。

### 补丁2前C1/lit准备（历史，已完成）

- 存档工具与libLLVM；固定C1登记范围与原测试完整性门禁，存档/构建后工具复核均0差异。
- GBS增量14分31秒、126步成功；lit PASS48/FAIL0/UNSUPPORTED1/XFAIL1，工具未重新链接。spec仅保留本地测试环境改动，正式非增量构建前必须撤销。[报告](profgen/impl/02_lit_env.md)

### llvm-profgen 补丁1（历史，已完成）

- 只提交输入素材的LLVM本地补丁；项目侧保存重放脚本、636行基线与逐命令stderr。没有修改增强实现。[报告](profgen/impl/01_patch1_test_inputs.md)
- 两遍字节一致；lit缺site配置未运行。下一步等待补丁2。

### RPi4 PMUv3 新镜像与冻结前核实（历史，已完成）

- A/B/C/D 实测、未匹配IR分支、设计差异、板上清理与原始文件位置详见 [05](probe/05_rpi4_pmu_image_and_prefreeze.md)。只写一次性匹配原型，不修改设计或开始实现。
- 采样与部署证据：[E1](probe/evidence/05/01_environment_hardware.txt)、[E2](probe/evidence/05/02_perf_formats_mapping.txt)；编译器/IR与armv7l闭环：[E3](probe/evidence/05/03_clang_ir.txt)、[E4](probe/evidence/05/04_arm_spike.txt)。

### llvm-profgen 增强准备（历史，已完成）

- GBS/depanneur/build helper 源码核对：bind 源码、跳过 prep、完整执行 build/install 并生成 short-circuit RPM；单包限制和 noinit 条件已记录。[增量源码证据](profgen/evidence/01_incremental_source.txt)
- 未修改基线完成 7633 个 Ninja 步骤，真实 GBS 退出0、ALL-END OK；平台加载器/工具验收新 profgen 成功，23 个产物逐文件 SHA-256 已保存。[构建证据](profgen/evidence/03_baseline_build.txt)
- 差异表覆盖输入/匹配/计数/输出/规模/诊断，并区分 Google 独有、双方已有和未实测能力；建议先做纯 IP、身份/地址正确性与有效样本诊断，模块、raw reader、SPE 分期。[差异源码证据](profgen/evidence/02_gap_source.txt)

### RPi5 AutoFDO / 插桩 PGO spike（历史，已完成）

- 源码固定 LLVM f999bd406c0a70fe8107aa992164fe6945c5d46a、Google AutoFDO f95d1a170dfe24ec5ce4117aa4b0f6d836841703；均保持干净。源码结论详见 [报告 §2](spike/01_afdo_pgo_feasibility.md)。
- 测试包独立本地提交 9925a104708449edabb82afe152d68a0a5b9c908；结果仓库跟踪三个普通文本文件，不跟踪嵌套 Git 元数据。174 行 C、固定 2500000 轮，所有正式运行 checksum=a31c311b953a2ac5。
- GBS 19:15:24–19:19:29 失败退出 1；修正测试 spec 后 19:20:58–19:21:12 成功；profile 重编 19:27:19–19:27:36 成功。整个 worker setsid、GBS setsid --wait，三次 ALL-END 完整；该 spike 临时 wrapper 的验证不等于重新运行了历史内核脚本。[构建证据](spike/evidence/02_build.txt)
- clang/profgen/profdata 22.1.8、readelf 2.43 均来自 GBS root；最终 RPM 三个 ELF 保留 symtab/build-id/debug_line/rela.text。cycles 真硬件 68745 样本，cpu-clock 14268 样本，均无丢样且无 BRANCH_STACK；数据/文本/profile 均核对传输哈希。[运行证据](spike/evidence/03_runtime.txt)
- 两份 llvm-profgen 均退出 1、输出文件不存在；没有 AFDO 优化变体。插桩 merge/show 成功，profile 文本 819 B 入库，spec 内重新 merge 后重编；IR 热点入口/冷热权重匹配。[profile 证据](spike/evidence/04_profiles.txt)
- base real=14.27/14.27/14.28；instr=15.02（+5.23%）；pgo=14.25/14.26/14.26（−0.12%，小差异不认定收益）；所有校验一致。采集器两种 real 均15.20（+6.49%）。
- 板上 work 空、RPM 前后1249，工具/库哈希不变；/tmp/sdb.log 前后495 B、mtime未变。新增四份证据90,836 B，无修改历史证据，无新增已知边界例外。

### RPi5 环境与采样（历史，已完成）

- 板型 RPi5 Model B Rev 1.1、aarch64、uid 0；BUILD_ID=tizen-unified-toolchain_20261027.063617_tizen-headed-aarch64；内核 6.12.80-arm64-rpi4-v8。CPU part 0xd0b，armv8_cortex_a76 事件源，arm-pmu 已绑定 armv8-pmu，日志 7 counters。
- /opt 为 /dev/mmcblk0p3 ext4 rw,relatime，可用 1.3G；true 执行 0。/tmp noexec，true 执行 126；两个拷贝立即删除。/proc/config.gz 不可读，仅核对本地 arm64 defconfig/Kconfig，明确不当作运行配置。
- Unified 同期 build.xml 指向 Base 20261026.051209；perf 6.12.80-0.aarch64、libllvm 22.1.8-1.5.aarch64 的 repodata/RPM 哈希通过，后者与 aarch64 linux-rpi 构建日志一致。两端部署哈希一致，LD_DEBUG/ldd 全部解析；仅解包，不安装。
- 软件系统 11,619 样本；硬件 cycles 系统 12,027 样本，evlist type 0/config 0；四项 stat 都有数值。分支栈 record=255，不支持；无 arm_spe/cs_etm，按条件跳过。BRBE 当前不可用，硬件独立能力未知。
- 720p 基线 real 8.39/8.35/8.52s，均值 8.42s；软件 9.18s、18,940 样本、+9.03%；cycles 9.17s、91,979 样本、+8.91%。1080p 基线 20.09s，软件 21.24s、48,968 样本、+5.72%。所有成功记录 Lost=0，没有触发 -m 1024；全部 EOS/退出 0。
- 三种采样有完整 DSO/符号计数；libgstlibav 有名称样本全部为 PLT。libavcodec/libgstlibav/libgstreamer 的 .comment、build-id、.symtab、.rela.text 和 DWARF 均缺失；ELF DYN/无 TEXTREL 与 PIC 相符，但原始 -fPIC 开关未知。本机 readelf 只读元数据，库只留 temp。
- 清空 work 并验证，保留 perf/libLLVM；RPM 前后 1,249。历史 /tmp/sdb.log 跨轮从 400 B 变为首次 connect 后的 495 B、mtime 17:48:51，收尾未变；未在 connect 前 stat，不推断精确写入归因。用户提供的工作区外附件仅作为任务指令读取。
- 报告与证据：[04](probe/04_rpi5_probe.md)、[E15](probe/evidence/15_rpi5_environment.txt)、[E16](probe/evidence/16_rpi5_perf_deployment.txt)、[E17](probe/evidence/17_rpi5_sampling.txt)、[E18](probe/evidence/18_rpi5_elf_cleanup.txt)。新增证据合计 128,645 B，历史证据未修改。

### PMUv3 补丁与 RPi4 镜像软件采样（历史，已完成）

- fetch origin 后最新 tizen 为 42aeefac58edeb081aff440f0b60be71cbe49755；原 src/linux-rpi 工作树保持干净。相对镜像 21645b17，arch/arm/configs/ 仅删除独立 RT defconfig；普通配置未变。
- 新 worktree 分支 afdo/pmuv3-gerrit 提交 2834afb2f85a6ef0905de18ed5b4a4ef7059635e；一文件一行新增，Kconfig 菜单顺序放在 GENERIC_PHY 与 ANDROID_BINDER_IPC 之间。rt/selinux/nosmack 片段均未覆盖五项 PMU 依赖；普通与 RT 共用并继承。独立干净 worktree git am 退出 0、结果树一致；无 make。详见 [06](kernel/06_pmuv3_patch.md)。
- RPi4 Model B Rev 1.5、uid=0；/opt 实为 /dev/mmcblk0p3 的 rw ext4 独立挂载，可执行；/tmp true 负对照返回 126，已立即删除。旧 /tmp/afdo_probe 清理通过。
- 已校验 perf 6.12.80/libLLVM 22.1.8 两端 SHA-256；LD_DEBUG/ldd 完全解析，perf 实际运行成功。全部数据、registry/cache 位于 work，结束已清空，只保留工具与库。RPM 数前后同为 1,252。
- 软件系统采样 12,012 样本。cycles record 返回 0 但 evlist/report 确认是 type=1 的 cpu-clock 回退；当前镜像硬件 cycles 不支持，不能只看退出码。
- 720p 三次基线 real 均值 12.3133s、差 2.04s；带采样 12.35s，观测开销 +0.30%，26,158 样本、无丢失。1080p 一次基线 23.29s，带采样 24.43s，+4.89%，保存 15,416、丢失 1,034（6.29%）。低次数/冷 registry/丢样限制详见 [03 软件采样](probe/03_rpi4_sampling.md)。
- libavcodec 样本占比 87.4035%/87.7465%；有名称比例仅 0.5467%/0.8575%，且绝大多数为 PLT。libgstlibav 有名称样本全部 PLT，内部函数仍不能解析。[14 原始证据](probe/evidence/14_rpi4_sampling.txt)。
- 全部 evidence/*.txt 合计 149,956 B，满足本轮 150KB；04/05/06/08 历史冗余输出已截断，文件头保留原不可变提交链接及 temp 完整副本路径，历史结论未变。
- 历史 /tmp/sdb.log 本轮末尾仍为 400 B、mtime 2026-10-28 12:01:10.724948977 +0800；没有新增已知未授权边界例外。


### 预检只读诊断（历史；已完成）

- 板型 Raspberry Pi 4 Model B Rev 1.5，id -u=0；本轮未再次切换 root 模式。
- 普通 kernel/modules 两包不带 --qf 和带指定 --qf 各查一次，均明确 is not installed，真实远端退出 1；不是已经发现版本/架构不一致或仅缺其中一个。
- RPM 全集关键词筛选只有 firmware-update-system-ui、firmware-update-system-ui-common、util-linux；rpm 与 grep 各退出 0，没有匹配另名/RT 内核、模块或 U-Boot 包。
- 模块目录与 modules.dep 的 rpm -qf 均为 is not owned by any package、退出 1；ls 可见 6.12.80-arm-rpi4-v7l 目录。
- /boot 的 /proc/mounts 精确匹配为空、awk 退出 0：未挂载。未查 boot 文件、未挂载、未解出旧 zImage，镜像哈希对应未知。
- uname -r=6.12.80-arm-rpi4-v7l；uname -v=#1 SMP Thu Oct 22 06:42:32 UTC 2026；命令行 bootmode=normal partition_ab=a。
- 本机两个旧 RPM 为 6.12.80-0.armv7l、VCS=platform/kernel/linux-rpi#21645b17c0d913e2ba7e10fbc9c993d286b3f57d；BUILDTIME 原始值均为 0，格式化为 1970-01-01 08:00:00 +08:00，不与运行内核的编译时间对应，不能据此验证或否定镜像字节匹配。
- 判定 **A**；原始命令/输出/真实退出码和限制见 [05_preflight_diag.md](kernel/05_preflight_diag.md)，未截断数据保存在 temp/pmuv3-diag/queries.json。
- 没有改脚本、重跑 02、安装/卸载、挂载/remount、重启、备份或采样；没有提出安装方案修改，停止等待指示。


### 安装执行（前轮；02 失败停止）

- 7 个主机脚本自带 set -euo pipefail、绝对路径、EXIT/信号 END 标记、日志；交互终端只需执行 /bin/bash 文件。四个板上脚本和原 helper 与批准文档逐字一致，bash -n / sh -n 全部通过。
- 01：`END 2026-10-28T15:39:52+08:00 OK`，主机退出 0，新旧普通 kernel/modules 四个 RPM SHA-256 全部 OK。
- 02：SDB root 成功、model 确认 RPi4；创建 /tmp/afdo_probe/new、old 并推送四个脚本后，原 prepare 报 `STOP: unexpected installed package`，`__AFDO_RC__1`；`END 2026-10-28T15:40:02+08:00 FAILED 02_board_backup:line=57`，主机退出 1。
- 原预检要求普通 kernel/modules 查询结果均为 6.12.80-0.armv7l；未打印实际包/返回值，具体不匹配尚未知。遵守立即停止规则，没有追加板上查询、修复、重试或回退。
- 未到 mount/备份/RPM 安装；本轮板上备份和主机备份校验都未执行，未创建 BACKUP_VERIFIED。03、04 没有执行，check 没有输出；没有重启或采样。
- 详细证据和边界记录见 [02 安装说明执行记录](kernel/02_pmuv3_install.md)。完整原输出在 temp/pmuv3-install/logs 与 prepare.out，板上四个临时脚本保留，没有安装任何 RPM。
- 既有 /tmp/sdb.log 前后 400 B、mtime 不变；无新增已知工作区外写入。未扩大外部文件扫描或删除遗留日志。


### 构建验收、静态修复与第二段（上轮）

- 构建 2026-10-28 11:56:53+08:00 启动，日志完成于 12:30:30+08:00；无重跑。worker=98602/GBS=98603 已退出，status 留在 BUILDING，真实退出码没有取得。
- 本轮按最新授权验收：success/rpi4-linux-kernel-6.12.80-0/log.txt 存在、fail 空；index.html 为 Succeeded；15 个二进制 RPM + 1 个 SRPM 全部实存、SHA-256 已记录、与 Wrote 行一一匹配，mtime 均在 11:56:53–12:31 内。完整 status、外层末尾 50 行、success 末尾 30 行及所有产物表见 [03](kernel/03_pmuv3_build_result.md)。
- 普通 devel `.config:5957` ARM_PMUV3=y，`:500` HW_PERF_EVENTS=y。从同镜像快照原 devel 提取基线配置，两边 5,649 项只有 ARM_PMUV3 从 n→y；没有其他依赖变化。配置核验不等于运行板上 PMU 已绑定。
- RT devel `.config:5996` ARM_PMUV3 未启用，`:505` HW_PERF_EVENTS=y。spec/实际日志使用独立 tizen_bcm2711_rt_defconfig；01 文档已更正为基于 RPM 的实际结论。
- 日志 LLVM=1、Kbuild `.main.o.cmd` 实际 clang 编译命令、GBS root 平台 readelf 读取 vmlinux .comment（通过 qemu-arm-static，无 sudo）一致确认 clang/LLD 22.1.8。quiet 构建日志没有完整 clang 命令，不能提供其日志行号；替代命令证据及限制已写 03。
- 构建脚本现将整个 worker 脱离调用会话，传递 fd 9 锁，setsid --wait 保留真实退出码；RPM 元数据扫描实读 16 个输出，无权限错误。仅 bash -n，通过；未实际运行修复。具体回收机制仍为推断。
- [02 安装/回退文档](kernel/02_pmuv3_install.md) 只安装普通 kernel+modules，备份整 boot 和模块并拉回主机验哈希；核对普通包无脚本、config.txt 直接覆盖、RT 脚本会切镜像；包含普通启动链哈希检查、在线与 SD 卡离线回退、重启后的身份与 PMU 绑定验收。文档 Shell 片段仅静态检查，不执行。
- 原源码/worktree 干净，未改 config/、固定 GBS 配置/spec，未运行构建、未连接板、未安装包/重启。主机临时 RPM、配置与证据在 temp/pmuv3-verify/；原日志/status 保留。

### 内核构建准备（历史；第一段完成）

- 精确镜像提交 21645b17c0d913e2ba7e10fbc9c993d286b3f57d 在本地存在，未 fetch。原 src/linux-rpi 仍为 42aeefac58edeb081aff440f0b60be71cbe49755，前后 status 为空。
- temp/linux-rpi-pmuv3 / afdo/pmuv3 的内核本地提交：c27f160de761bb55f64672ceac642698a6e93684。仅 ARM 普通 defconfig 增加 CONFIG_ARM_PMUV3=y，一文件一行；已提交且工作树干净。内核提交未推送。
- temp/gbs/gbs_rpi4_image.conf 已固定 Unified 20261022.054557 与 Base 20261020.074527；temp/gbs-home/.gbs.conf 最小配置已准备。config/ 原文件哈希不变。
- spec 无禁用 RT 的宏，脚本构建普通+RT（当前核验普通 PMUv3=y、RT 未启用，见上文）。准备时 nproc=20，运行时计算一半核数，GBS --threads 1。
- 已核查官方同版本 gbs 2.1.0 / depanneur 0.16.30 源码：随包 sudoers 为构建命令授予 NOPASSWD，脚本跳过 sudo -v；受保护的实际策略未读取/提权验证，异常时后台失败退出，不交互等待。
- 第一段当时仅完成 bash -n；后续已实际构建、核验产物并完成第二段文档，见当前进度。
- 说明与完整内核 diff：[01_pmuv3_build.md](kernel/01_pmuv3_build.md)；脚本：[build_pmuv3_kernel.sh](../scripts/build_pmuv3_kernel.sh)。

### 补充轮（历史）

- [02_rpi4_pmu_probe.md](probe/02_rpi4_pmu_probe.md) 与证据 08–13 已整理；本轮部分完成，主机 flex 缺失和板上 /tmp noexec 两个阻塞保持开放。
- 官方 BBB 片源、60 秒 720p/1080p H.264 视频、SHA-256/ffprobe/来源授权记录完成；[media/README.md](../media/README.md)。MP4 本地保留但忽略，不提交。
- 两份 defconfig 配置生成均因主机缺 flex exit=2，未生成 .config；仅 temp/ 下产生配置辅助对象，内核源码开始/结束均干净。
- RPi4 运行 DT 的 A72 PMU 节点及 platform 设备存在，未绑定驱动；只有 armv7-pmu，没有 armv8-pmu 注册。ARM_PMUV3 缺失是高可信候选原因，实际运行配置尚未闭合。
- 前一批同镜像 perf RPM 的 --test 缺 perl/LLVM；用户已批准配套 Base，并改为仅解包部署。
- Unified build.xml 指向 Base `tizen-base-toolchain_20261020.074527`。配套 `libllvm-22.1.8-1.6` 与 perf 构建日志完全一致，repodata/RPM SHA-256 验证通过；没有使用 reference。
- readelf 确认 libLLVM 是 perf 主程序的直接 NEEDED；perl 来自四个随包测试辅助脚本。只推送 perf 与 libLLVM 两个文件，板上 SHA-256 与本机一致。
- `/tmp` 实际挂载 rw,nosuid,nodev,noexec；ldd exit=1，直接 perf --version exit=126，动态加载器 --list exit=127（failed to map segment）。未完成库解析验收，按指令停止；未安装任何 RPM、未改挂载/标签/策略。
- 720p 和 1080p avdec_h264 管线均到 EOS，real=14.323s / 27.359s；perf 不可用，所有采样/报告/分支栈测试未执行。
- 最新临时部署已清理并验证 /tmp/afdo_probe 不存在；rpm -qa | wc -l 前后均 1252，完整集合新增/删除均为空。没有 perf.data 生成或拉回。
- 本次证据 12–13 为 14,646 字节，补充轮 08–13 合计 48,853 字节，所有 evidence 合计 185,033 字节，低于 200KB；只提交报告/证据/README/.gitignore/本状态文件。推送使用正常既有认证，不开 PR。

### 初轮（历史，补充轮结论优先）

- 已重新盘点，四个源码树和两份 config 文件就绪；配置指向的工作区内 GBS root 不存在。
- 已连接 192.168.108.26:26101，model=Raspberry Pi 4 Model B Rev 1.5，armv7l，root 成功。
- perf 缺失；批次中的 record/report/script/list 调用均 exec 失败，无采样数据生成。缺工具后未安装替代物，未把失败认作硬件不支持。
- 已检查插件、素材、拉取两份实体库；/tmp/afdo_probe 已删除并验证。
- 四个仓库元数据重新下载、压缩/解压 SHA-256 校验、全量文件提供关系查询完成。
- 内核/LLVM/FFmpeg/GStreamer spec 和相关源码检查完成；实际构建环境的宏展开保持未知。
- CodingSystem 重新克隆，当前 HEAD=287d51c674e2b7d38605098338ff94fc8bb4e4fa；只读，无修改/推送。
- 新报告与证据已重写；原始证据合计限于 300KB 内。报告：[probe/01_env_probe_report.md](probe/01_env_probe_report.md)。
- 推送规则已澄清：先前 exit 128 发生在主动禁用全局配置与 credential helper 的环境，不能据此判定本机认证失效。本次在正常环境提交长期规则与状态更新，并用原有 GitHub 认证推送全部未推送提交；不修改认证配置、不再请求仓库内凭据。推送结果以执行日志及远端 HEAD 校验为准。

## 已闭合结论（附证据路径）

- 补丁8同指令别名及映射不可用小修通过正式GBS/lit/C1；106份正式转换72次别名校验全通过，profile与旧补丁8一致。真实avg用匹配评估产物与BBB样本完成GNU独立715键零差异，挂账关闭。[报告13](profgen/impl/13_patch8_thumb_dwarf.md)、[avg证据](profgen/impl/evidence/12/31_real_avg_independent.json)

- pseudo-probe拆分后节位置按用户裁决由aarch64证据闭合：运行文件/调试文件两种位置拒绝均成立，不依赖架构。armv7l probe编译崩溃另归probe子方案。[拆分证据](profgen/impl/evidence/10/07_aarch64_split.json)、[裁决登记](profgen/impl/11_eval_prep.md#1-已生效的裁决)

- 补丁3身份验证已闭合：真实libc分别verified/verified-path，无证据库与deleted默认拒绝、allow后unverified；generation=0修正后14个真实目标地址计数不变，lit无FAIL、C1零差异。[实现与规则修正](profgen/impl/05_patch3_identity.md)、[最终验收](profgen/impl/evidence/05/09_final_real_identity.json)

- 补丁2收尾：完整真实文本全部接受、修改前后计数与输出不变；新CLI/dsoff尾缀负对照通过，原行为C1零差异。8个IP lit全通过，原50项不变。[收尾报告](profgen/impl/04_patch2_followup.md)、[逐地址](profgen/impl/evidence/04/02_independent.json)、[lit](profgen/impl/evidence/04/04_lit_summary.json)

- 补丁2的IP读取/地址换算与选项拒绝通过7个lit测试文件；默认LBR行为保持原50项lit结果和C1基线0差异。新工具确实重新链接；固定过渡失败不创建/覆盖output。[实现与规则表](profgen/impl/03_patch2_reader.md)、[lit](profgen/impl/evidence/03/04_lit_classification.json)、[C1](profgen/impl/evidence/03/05_c1_summary.json)

- LLVM site配置已生成，原有lit 50项基线取得（48 PASS、0 FAIL、1 UNSUPPORTED、1 XFAIL）；C1固定登记范围且存档/构建后复核均0差异。[lit](profgen/impl/evidence/02/09_lit.log)、[C1](profgen/impl/evidence/02/10_rebuilt_c1.json)

- 补丁1的104份素材与C1固定矩阵归档；两遍636次实际行为一致，纯IP旧错误保留。此结论不包含lit通过或新IP功能实现。[素材验证](profgen/impl/evidence/01/04_fixture_checks.txt)、[C1摘要](profgen/impl/evidence/01/10_c1_summary.json)

- RPi5页大小4096；libavcodec单进程5,865/双进程14,331条dsoff公式与唯一落段100%通过；libc MMAP2/ELF build-id一致，period行为符合v0.5；负pid/tid样例为新事实，不自动认定设计冻结。[09](probe/09_rpi5_prefreeze_checks.md)、[E3](probe/evidence/09/03_mapping_buildid_period.txt)

- RPi4 新镜像A72 PMU已绑定，cycles没有软件回退；armv7l插桩PGO小程序闭环通过。旧镜像软件回退结论仅适用于历史镜像。[E1](probe/evidence/05/01_environment_hardware.txt)、[E4](probe/evidence/05/04_arm_spike.txt)
- v0.2部分输入预期需评审：模式A buildid-list非空、vdso有偏移；当前IR匹配键只部分覆盖。period/页大小/地址换算/profi事实已取得。[E2](probe/evidence/05/02_perf_formats_mapping.txt)、[E3](probe/evidence/05/03_clang_ir.txt)

- 当前 LLVM spec 有条件支持对象复用；空目录完整基线已成功，差量耗时仍是估算。新 llvm-profgen 可运行，原 src/llvm 保持干净。[00](profgen/00_incremental_build.md)、[E3](profgen/evidence/03_baseline_build.txt)
- Google 的普通 IP、build-id 匹配等可作参考；行/内联计数、discriminator、符号列表和多种输出 LLVM 已有，不能重复列为缺失。[23项差异表](profgen/01_gap_analysis.md)、[E2](profgen/evidence/02_gap_source.txt)

- llvm-profgen 当前纯 IP 输入不可用；Google 无 LBR 和 BOLT -ba 仅源码支持，BOLT 排除 ARM32。[源码证据](spike/evidence/01_source_analysis.txt)、[实测 profile 证据](spike/evidence/04_profiles.txt)。不能据此把所有 AutoFDO 路径判不可用。
- RPi5 插桩 PGO 已实际构建/采集/合并/重编/正确性验证；未证明稳定性能收益。报告与限制：[01_afdo_pgo_feasibility.md](spike/01_afdo_pgo_feasibility.md)。

- RPi5 A76 PMU 已绑定，硬件 cycles 的实际 type/config=0/0，软件/计数支持；分支栈不支持，无 SPE/ETM 事件源；不能由 cycles 推断分支 profile 就绪。[04 报告](probe/04_rpi5_probe.md)、[E15](probe/evidence/15_rpi5_environment.txt)、[E17](probe/evidence/17_rpi5_sampling.txt)。
- RPi5 同期 aarch64 工具/依赖已校验并可执行，媒体全部无丢样；现有 strip 库不能直接提供完整 BOLT/AutoFDO 前提。work 清空，RPM 数不变；保留文件清单与删除命令见 [04](probe/04_rpi5_probe.md)、[E16](probe/evidence/16_rpi5_perf_deployment.txt)、[E18](probe/evidence/18_rpi5_elf_cleanup.txt)。

- **已决定：PMUv3 通过补丁合入 Gerrit、由用户起 Quickbuild 出新镜像；原手工安装方案取消，scripts/pmuv3_install/ 保留、不再使用。** 最新分支普通/RT 共用配置，片段无冲突；补丁与 git am 已验证：[06](kernel/06_pmuv3_patch.md)。
- /opt 部署可执行、所有 NEEDED 已解析；软件采样与 DSO 归属支持，硬件 cycles 请求实际回退，符号解析有限；work 已清空，RPM 数不变：[03 软件采样](probe/03_rpi4_sampling.md)、[14](probe/evidence/14_rpi4_sampling.txt)。

以下历史结论按当时镜像/基线阅读；当前授权和实测以上文为准。


- 预检诊断归类 A：两个普通内核/模块包都不在 RPM 数据库中，模块目录无 RPM 归属；/boot 未挂载。旧 RPM 的 BUILDTIME=0，无法验证 2026 年编译日期。证据：[05_preflight_diag.md](kernel/05_preflight_diag.md)。

- 历史普通版内核构建/完整配置对比已通过替代证据验收（[03](kernel/03_pmuv3_build_result.md)）；该旧产物手工安装方案已取消，后续使用用户 Quickbuild 的新镜像。
- 主机脚本封装完成；01 的 RPM 校验通过，02 在真实远端退出 1 后停止，未安装。证据与原输出路径：[02](kernel/02_pmuv3_install.md)。

- 构建经三组替代证据验收通过；真实 GBS 退出码未知且 ALL-END 缺失，不能补写。普通配置与精确镜像基线仅 ARM_PMUV3 从 n→y；RT 未启用。clang/LLD 22.1.8 已由配置、保存命令与 ELF 核对。证据：[03](kernel/03_pmuv3_build_result.md)。
- 普通 kernel/modules 无自己的 %post/%preun；config.txt 作为 payload 覆盖；RT %post/%preun 会移动 zImage。普通版安装、boot/模块备份、回退与启动检查：[02](kernel/02_pmuv3_install.md)。


- 镜像精确源码基线可用，afdo/pmuv3 只有一行配置新增；原源码和两份用户 GBS 配置未改。基线/提交/diff/核查命令见 [01_pmuv3_build.md](kernel/01_pmuv3_build.md)。
- spec 无只构建普通版宏；预期十个显式二进制包；RT 实际未启用 PMUv3，见 03 的 devel 配置。GBS/depanneur 随包 sudo 调用与 NOPASSWD 策略源码位置同上；实际构建已完成且未见 sudo 限制；当前脚本脱离会话修复仍未运行验证。

- 配套 Base 快照已明确；libllvm 22.1.8-1.6 与 perf 实际构建日志一致，ABI/包校验通过；perl 为附带测试脚本解释器依赖。[12_perf_dependencies.txt](probe/evidence/12_perf_dependencies.txt)
- 临时路径 /tmp 的 noexec 阻止 perf 执行和加载器映射；ldd 无法完成全部 NEEDED 验证。推送文件已删除，RPM 前后同为 1252 且包集不变。[13_perf_deployment.txt](probe/evidence/13_perf_deployment.txt)

- 补充轮配置生成失败且源码未改；最终配置未知，不以默认值替代。[08_pmu_config.txt](probe/evidence/08_pmu_config.txt)
- 运行 DT 包含有效 A72 PMU 节点、平台设备未绑定，仅 armv7-pmu 注册；排除了“无节点/节点 disabled”，但未证明中断/固件无其他问题。[09_pmu_runtime.txt](probe/evidence/09_pmu_runtime.txt)
- 镜像同期 perf RPM SHA-256 校验通过，依赖测试失败，同库没有缺失依赖提供者；实际安装 0 包。[10_perf_package.txt](probe/evidence/10_perf_package.txt)
- 已建立 60 秒两档 BBB H.264 素材并完成 avdec_h264 解码基线；首轮“没有执行解码”的结论由本轮结果补齐。[11_media_smoke.txt](probe/evidence/11_media_smoke.txt)

- 输入材料及配置已就绪，无 GBS root。[01_workspace.txt](probe/evidence/01_workspace.txt)
- RPi4：Tizen 11.0.0，内核 6.12.80-arm-rpi4-v7l；uid=0；perf 不在 PATH；无硬件 PMU/cs_etm/arm_spe 事件源，运行内核配置不可取得。[02_rpi4.txt](probe/evidence/02_rpi4.txt)
- avdec_h264 可发现；ffmpeg/ffprobe 命令及 /root 常见后缀视频未发现。只验证插件存在，没有执行解码 benchmark。[02_rpi4.txt](probe/evidence/02_rpi4.txt)
- 两份实体库已 strip、没有 .comment 和 build-id；链接器未知。本机工具只读静态 ELF 元数据。[03_libraries.txt](probe/evidence/03_libraries.txt)
- L 配置仓库提供 LLVM/compiler-rt 22.1.8-3.1，G 配置提供 22.1.8-6.5；三架构都有 profgen/profdata/profile runtime；armv7l/aarch64 有 linux-kernel-perf 6.12.80-0。四库均未找到 BOLT 工具/runtime、create_llvm_prof 或目标 debuginfo，结论不覆盖独立 debug 仓库。[04_repodata.txt](probe/evidence/04_repodata.txt)
- 内核源码 6.12.80 无 AUTOFDO_CLANG/PROPELLER_CLANG 配置和架构 select；同一源包包含 arm/arm64 的 tizen_bcm2711_defconfig 路径，arm64 配置及启动文件覆盖 pi5，但 RPi5 实机未验证。[05_sources.txt](probe/evidence/05_sources.txt)
- LLVM spec 未启用 bolt，lld 在 llvm 主包，profgen/profile runtime 有构建和打包声明；FFmpeg 正常非 ASan 路径保留 ARM 汇编/NEON；GStreamer 的 gst-libav 源码与包声明已提供。[05_sources.txt](probe/evidence/05_sources.txt)
- 框架 HLD draft frozen，契约 v0.11 复审中，业务指南缺失，代码目录只有占位；不能称框架已实现。[06_codingsystem.txt](probe/evidence/06_codingsystem.txt)
- 已确认外部遗留 /tmp/sdb.log，由现存 SDB 服务持有，当前 0 B、前后时间未变；没有删除。首次 shell/Git 隐式初始化读取未追踪，作为历史审计限制保留；用户已澄清正常系统工具初始化及已有 GitHub 认证不属于项目输入边界限制，后续结果仓库 commit/push 不隔离。[07_boundary.txt](probe/evidence/07_boundary.txt)

## 待人工裁决

- R/C/G5类型、ToS输入、ε、预注册/修订1、root/performance及只读缺码重试均已裁决执行；保留RUN恢复已闭合，不再重复索要。非叶子line0规则已裁决且补丁9通过；当前待PM的是下一步数据重转、覆盖与质量/消费构建授权；v0.8登记包含GNU AS规范化、别名一致性和映射不可用降级规则。

- [设计v0.7](profgen/design/02_llvm_profgen_enhance_design_v0.7.md)第一阶段已冻结，补丁1–8与RPi4第一轮已完成，下一步质量分析/消费构建等待指示；第二阶段待定事项见第12节。主机perf构建与`--perfdata`准入仍待决定，IP模式仍拒绝perfdata；文本输入已可生成profile。


- 本轮已完成spike及FFmpeg生成侧变体/训练输入采集；后续消费构建、质量与性能效果等待授权。Chromium/kernel/跨板集成及Agent仍未实现；Google无LBR和BOLT候选验证另行授权。

- 新镜像已由用户交付并通过05的PMUv3验收；Agent不向Gerrit推送，不恢复已取消的手工安装方案。后续镜像交付由用户决定。

- **Agent 的板上部署不能依赖 /tmp（noexec），部署目录由能力探测模块按挂载参数自动选定。** 本轮手工授权 /opt/afdo_agent 已明确，后续按挂载参数验收，不再重复索要目录授权；通用自动选择规则仍待设计裁决。
- 历史直接 make 配置仍受主机 flex/bison 缺失限制；GBS 构建已完成并在构建根解决依赖，没有安装主机工具。
- 新镜像PMU绑定及硬件cycles验收已完成；真实包优化效果与统计质量仍待后续授权评估。
- 是否提供保留 .comment/build-id 的原始构建库及明确 debug 仓库配置。
- SDB 共享 daemon 已打开外部日志，若要求消除该例外，需由用户协调服务启动方式；本轮不重启服务、不删除遗留。

## 挂账

- probe子方案（设计第10节步骤8）阻塞：平台Clang22.1.8在armv7l/Thumb的pseudo-probe小包构建中段错误；保留temp/profgen-host-verification/build重现材料，待单独授权定位，不绕过。按用户裁决，该项不阻塞第一批DWARF路径；probe拆分后节位置已按aarch64证据关闭。[报告10停止节](profgen/impl/10_host_verification.md#44-停止证据与候选方案)、[裁决登记](profgen/impl/11_eval_prep.md#1-已生效的裁决)
- 已关闭[unknown]真实样例：本轮系统级双解码压力取得335条([unknown])及16条-1/-1，原始文本/行号与工具分类核对已保留。[证据](profgen/impl/evidence/12/69_special_samples.json)

- 已关闭：IP新选项枚举与cl::values由补丁7完成，显式aggregation语义保持。[报告](profgen/impl/09_patch7_report.md)
- 非叶子line0处理已由补丁9闭合：整样本排除至in_func_no_line并列子计数，正式验收通过。原补丁8统计106份S共2736样本（target0.0245787%、usable0.0332227%、5顶层函数）保留；本轮未重转正式S，重转及影响统计留待下一任务。[报告15](profgen/impl/15_patch9_nonleaf_line0.md)、[旧统计](profgen/impl/evidence/12/57_nonleaf_summary.json)
- 已关闭真实avg：按最新裁决使用本轮同次评估构建和中档BBB真实采集，原3热点11,525指令/715键GNU独立sum/max/avg均一致；未套用旧镜像地址。head零估计挂账仍保持已关闭。[证据](profgen/impl/evidence/12/31_real_avg_independent.json)

- 本轮授权generation=0为未知；inode被复用且一条记录generation为0时，替换可能无法发现。不能将allow-missing后的unverified提升为verified；源码与限制见[补丁3规则修正登记](profgen/impl/05_patch3_identity.md)。

- 已关闭06高LOST完整导出验收挂账：新主压力423条LOST、L58343、S1190755，独立重算与工具一致；系统级补充626条/L71965/S1720866。旧06遗失文本和703821仍不可追溯，不宣称恢复旧材料。[新完整实测](profgen/impl/evidence/12/60_lost-bounded.json)

- 开发工作树 `temp/llvm-profgen-enh/packaging/llvm.spec` 的LLVM_INCLUDE_TESTS=ON和%check改动只本地保留，**正式非增量构建前必须撤销**，不得进入增强补丁。LLVM site配置与原有lit基线已闭合；assertions专用测试在当前No配置下仍为UNSUPPORTED。[报告](profgen/impl/02_lit_env.md)

- 交付前非★项（v0.7）：新LLVM发布后复核默认build-id；aarch64 Tizen debuginfo的`$x/$d`已由本轮小包闭合；probe拆分后节位置按2026-11-04裁决以aarch64证据关闭，armv7l Clang崩溃只挂probe子方案；新aarch64构建DWARF5拆分与BUILD/RPM ID差异已补证，原08 FFmpeg同次BUILD材料缺失，不外推为已复现。`[unknown]`合成素材已由补丁1闭合；构造的probe组合不替代真实拆分核实。第一阶段已冻结；第二阶段待定事项见设计第12节，IR匹配/BFI不沿用旧百分比。
- armv7l插桩已通过单程序/单输入闭环；跨训练输入、实际FFmpeg/GStreamer/kernel/Chromium与性能收益仍未验证。Thumb符号区间的状态位处理须保留在核对判据中。

- 本轮补丁2已实测少量源码增量：最终Ninja106步、完整GBS812.070秒（包含安装/拆分/打包），不再只依赖单文件估算；Chromium 两工具内存/耗时对比、Google 跨架构/SPE/模块运行仍未验证。当前 short-circuit RPM 非发布包，SRPM 源归档不完整；基线 profgen 无 GNU build-id，本轮未改 spec。

- Google create_llvm_prof --use_lbr=false 的端到端运行/行计数质量、ARM/Thumb 正确性和 BOLT -ba 优化仍未实测；RPi4 插桩 PGO 的 armv7l 小程序闭环已于本轮完成。当前 llvm-profgen 的纯 IP 拒绝已闭合，不待重试。
- 本轮性能测量次数少且未随机交错，PGO −0.12% 仅为观测差；真实场景收益、跨输入泛化需独立评估。

- 原 GBS 真实退出码无法追溯；会话/进程组被执行器回收属于推断，没有死亡信号或生命周期审计证据。原 status 永久保留原貌。
- 包装脚本修复未经运行验证，下次构建验证；setsid 不能抵抗 cgroup 清理、SIGKILL、断电、磁盘不可写。
- quiet 原构建日志没有完整 clang 命令行，已用本次 `.cmd` 命令和 ELF 代证；不伪造日志行号。
- 旧手工安装预检失败原因已查清且方案取消；/boot 未挂载时的 zImage 哈希仍未知，BUILDTIME=0 不用于匹配日期。新镜像 PMU 绑定/硬件采样已于05验收；软件采样已闭合。

- 1080p 本次丢样 6.29%，单次开销没有统计稳健性；strip 库内部符号仍缺失。分支栈负对照及 ETM/SPE/BRBE 未在本轮重测，不能由 PMUv3 补丁推断。
- 各包最终 CC/CXX、%{optflags}、外部 LTO/链接器参数与已运行镜像对应关系：无 GBS root/构建日志，不能静态补全。
- RPi5 实机探测已闭合；运行 .config、BRBE 独立硬件能力、原始编译器/链接器和 -fPIC 开关仍未知。没有生成 BOLT/AutoFDO profile 或验证优化收益。
- CodingSystem 业务指南、最终契约与实际实现的后续进展。
- 旧历史写入没有完整 syscall 审计，边界检查无法证明工作区外遗留全集。
