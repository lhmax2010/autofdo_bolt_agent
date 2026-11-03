# 补丁5小修与补丁6质量报告、失败契约

2026-11-03。补丁5小修已独立验收并amend为`b843cf07f851985413c926a562f9135a272a3bea`；补丁6已完成正式GBS、lit、C1、真实导出与合成负载验收，本地提交`1dd4b9acd84045c230e77cc68d85eafca58eae88`。路径冲突、截断DWARF与旧报告覆盖三次裁决均已落实。下文保留停止历史；最终结果见第15–17节。冻结v0.7正文与golden未改。

第1–5节保留上一停止点的原始历史；第6节为该停止点的裁决，第7节以后为本次恢复后的事实。冻结设计和golden均未修改。

## 1. 需要裁决的契约冲突

本轮第二部分第3条同时要求：

1. profile与报告指向同一文件时报错；
2. 任一步失败，已有profile不被覆盖；
3. 只要给了`--quality-report`，失败时也写出失败报告。

当一个已有文件同时作为`--output`与`--quality-report`时，向该路径提交失败JSON就会覆盖旧profile；保留旧profile则无法在该路径写失败JSON。直接使用同一个路径已足以构成反例，无需硬链接、符号链接或崩溃。冻结设计5.6.3第2条同样要求拒绝别名、失败时旧输出不覆盖。

[原文、设计行号、最小反例及候选方案](evidence/08/01_contract_conflict.txt)。这是逻辑冲突分析，未执行任何会覆盖旧profile的实验。

**建议但未实施：** 将“profile/报告路径冲突”明确列为失败报告写入的例外：两种输出都不写，只在stderr报告路径冲突，保留已有文件；不得自行选另一个报告路径。已发起裁决请求，尚未把该例外写入代码或设计。

## 2. 补丁5小修草稿

LLVM HEAD仍为`d7bd4795c7fddfc239510b96fa6803b56b94dbb4`，没有amend，0005导出未变。工作树中保留以下**未验收、未提交**草稿：

- 指令保存所属映射交集索引，prev-inst要求同一DWARF区间、同一映射区间且首尾相接。
- 候选前驱无可用行信息时保留原地址，不把原有usable样本转为in_func_no_line。
- 未调整原因使用`first_instruction`、`range_gap`、`data_or_state_change`、`predecessor_no_line`。只在skid启用时初始化原因桶，默认关闭时诊断不变；测试检查分项之和等于总桶。
- 按函数分组可用样本地址，再逐函数检查起点，移除函数×全部地址的扫描。
- 增加0x1020跨A32→Thumb状态段的负对照；派生`skid-no-line.s/.perfbin`，0x1000行号0、0x1002仍为原来的行3。代码和函数区间沿用boundaries素材，golden未改。
- 顺便缩短IPBoundary.h文件头，使GBS clang-format保留LLVM单行头形式。

新增素材使用GBS armv7l root的clang/LLD 22.1.8生成，readelf行表输出与完整命令保存在[素材证据](evidence/08/02_skid_fixture_commands.json)。3个源码文件的改动行格式化及dry-run通过：[格式检查](evidence/08/03_format.json)。[未提交源码/测试diff](evidence/08/05_uncommitted_patch5_draft.diff)；新增二进制仅留LLVM工作树temp内，路径、大小、SHA在[停止状态](evidence/08/06_stop_state.json)。

开发编译启动后，在契约冲突裁决等待阶段向**本任务自己的**编译器和包装进程发TERM，终端退出143，随后ps确认相关PID均已退出。[进程记录](evidence/08/04_stopped_own_processes.json)。没有终止其他会话进程。该开发编译未生成新工具，不能作为验收；GBS增量尚未启动。

## 3. 验收与提交状态

| 项目 | 本轮结果 |
|---|---|
| 补丁5 GBS/%check lit | 未运行 |
| C1两遍636条 | 未运行，不复用上轮数字冒充本轮结果 |
| 14次完整导出重放 | 未运行 |
| 新LLVM补丁5提交 | 无，仍为旧HEAD |
| 补丁6实现/提交/0006导出 | 均未开始 |
| 当前工具SHA | `05ddac1c680fd34e21b4c2bfc424c792d2d1a1155fbed2e4d754e39242f4bfb6`，上轮工具，未重建 |
| spec | 原本地测试diff逐字节不变，未提交 |
| 设计/golden | SHA保持原值，未修改 |

开发日志与结束标记留在`temp/profgen-patch6/patch5-fix/devbuild.log`及`development.status`。恢复时先完成补丁5小修独立验收并amend，成功后才开始补丁6；不得跳过这道顺序要求。

## 4. 待设计v0.8登记

已由本轮用户裁决、尚待完成代码验收：

- prev-inst增加“同一映射区间”和“前驱有可用行信息”条件；分类按原始地址。
- skid_unadjusted原因细分，分项求和等于总量。
- coverage增加name_merged_functions计数及前50名单，不改按名合并逻辑。
- 比率门槛定点语法、精确整数比较，门槛失败阶段generate。
- 隐藏测试注入接口及最终点名列表，须随补丁6真实调用点实现和测试后登记；本轮尚未新增接口。

仍待用户裁决：输出路径别名冲突是否作为“失败时写报告”的显式例外。本报告没有替用户批准。

## 5. 挂账与边界

原有挂账不关闭：06完整LOST导出缺失；真实数据avg需用08产物重新采样；枚举选项/cl::values留补丁7；非叶子line0上板后决定。补丁6质量报告、失败回调、门槛和全部验收仍未完成。

本轮只读取用户指定的任务附件作为任务输入；所有产生的文件均在工作目录内。未连接板子，未推LLVM/Gerrit，未改认证、未索要密码；未修改冻结文档或golden。没有新增已观察到的工具越界写入。


## 6. 用户裁决后恢复（2026-11-03）

第1节冲突已裁决，保留上文为停止历史，不再作为阻塞。路径验证在IP流程最前完成，早于任何文件写入、临时文件、ELF加载、回调注册。冲突集合扩大为：output是`-`；profile与报告互相别名；任一输出与任一给定输入（perfscript、binary、debug-binary、perf-buildid-list、dwp）别名。已有文件用equivalent，不存在文件比较规范父目录与文件名。冲突时只stderr固定诊断，不写报告、不写profile、不创建临时文件，旧文件不变。这是“失败也写报告”的唯一例外，待v0.8登记。实现与验证结果在后续续写，不能把裁决当作已经实现。

恢复顺序：先补丁5小修独立GBS/lit/C1/完整导出验收并amend；再补丁6。原spec本地diff继续保持不变。

## 7. 补丁5小修独立验收与amend（已完成）

旧提交 `d7bd4795c7fddfc239510b96fa6803b56b94dbb4` amend为 `b843cf07f851985413c926a562f9135a272a3bea`。0005重新导出且反向应用检查通过；仅工具与测试目录，spec本地diff逐字节不变、未提交。[提交审计](evidence/08/11_patch5_amend_audit.json)

- GBS：2026-11-03 16:41:39–17:08:10 +08:00，1590.649秒、Ninja106步，GBS_EXIT=0，ALL-END OK。available最低5135MiB，无低于2GiB采样点；已用内存采样峰值26405MiB，1/5/15分钟负载峰值14.62/10.48/10.45。[构建与资源](evidence/08/07_patch5_build.txt)
- 正式%check lit 79项：77 PASS、0 FAIL、1 UNSUPPORTED（cs-preinline-cost，assertions=No）、1 XFAIL（invalid-perfscript）。原50及原补丁5全部结果不变；扩充既有skid测试，无新增lit文件。[日志](evidence/08/08_patch5_lit.log)、[xunit](evidence/08/08_patch5_lit.xml)
- C1每遍636，两遍一致，与原基线0差异，29个新增IP测试排除。[C1](evidence/08/09_patch5_c1_summary.json)
- 14次完整导出stdout/stderr及成功时profile与修前补丁5逐字节一致；默认关闭skid行为未变。[重放](evidence/08/10_patch5_full_comparison.json)
- 工具SHA-256：`095a7497ccda26f60ad075a4ce567b8cbd9159e1c9006749800f5d558279ead1`。存档 `temp/profgen-patch6/patch5-baseline-tool/llvm-profgen`。
- 小修完整diff：[源码与测试](evidence/08/07_patch5_fix.diff)。三个源码文件改动行GBS clang-format及dry-run通过，素材生成命令见第2节。黄金文件与冻结文档未改。

以上完成后才进入补丁6实现/测试可行性检查。第1–5节保留为历史停止记录。

## 8. 补丁6必测项的可行性核对与停止原因

### 8.1 任务要求与实际接口

本轮第二部分第4条指定：调试ELF头完整、`.debug_info`被截断；加载成功、首次符号化失败，检查generate阶段的退出兜底回调。仅使工具最终返回非0不足以验收这条要求，因为常规 `Error` 返回与 `exitWithError` 回调是不同路径。

当前LLVM 22.1.8对这里的DWARF损坏采用可恢复诊断：

- `llvm/lib/DebugInfo/DWARF/DWARFUnit.cpp:79–86` 把CU头解析错误交给WarningHandler；`:305–314`检测CU长度越过节边界。`DWARFContext.cpp:2452–2465`创建并返回context，不以Expected返回该诊断。
- `llvm/lib/DebugInfo/Symbolize/Symbolize.cpp:104–131`仅在getOrCreateModuleInfo返回Error时返回Error；实际DWARF行查询返回`DIInliningInfo`值。`:820–826`创建DWARFContext并构造module。`SymbolizableObjectFile.cpp:30–70`中的Error来源为对象符号等读取，并非.debug_info内容解析。
- `llvm/lib/DebugInfo/Symbolize/SymbolizableObjectFile.cpp:302–318`在DWARF查询无帧时补一个空帧，返回值，不生成Error。
- `llvm/tools/llvm-profgen/ProfiledBinary.cpp:1054–1061`在加载阶段已经遍历CU；`:1128–1137`只对Symbolizer的Error调用unwrapOrError，空帧/line0返回空调用栈。

上述源码摘录带逐行编号，见[接口证据](evidence/08/17_truncated_dwarf_source.txt)。结论限于**其他ELF元数据有效、仅截短.debug_info**的这一验收条件，不声称所有坏ELF或所有符号化错误都不能触发回调。

### 8.2 可重现平台工具实验

未改任何LLVM源码、原素材或golden。使用GBS root的LLVM 22.1.8工具，在 `temp/profgen-patch6/debug-truncation/` 生成临时副本：从 `Inputs/ip-mode/a64-pie.debug` 用llvm-objcopy导出原501字节`.debug_info`，截为指定长度，以`--update-section`替换；其他节的源内容不改。每份用GBS readelf验证ELF头可读。runtime使用匹配的 `a64-pie.stripped.perfbin`。

为区别“空结果”与“Error”，临时C++观察程序依次调用createBinary、DWARFContext的compile_units/dies、首次symbolizeInlinedCode，打印真实Expected状态；链接本次未修改的libLLVM.so.22.1。源码及完整构建命令见[观察程序](evidence/08/15_api_probe_source.txt)、[GBS clang编译](evidence/08/14_api_probe_build.json)。这是一次性验证程序，既非测试注入，也未更改库的行为。由于通过加载器启动clang时驱动另起cc1的路径不能执行，使用同一平台clang `-###` 取得参数，再由平台加载器直接运行其cc1与LLD；未用主机工具链。

| .debug_info保留字节 | ELF读取 / DWARF加载返回 | 首次符号化Expected | 当前profgen |
|---|---|---|---|
| 0、1、4、8、11、12、16、250、493、500 | 均成功返回；CU=0 | 均为Value，1个空帧，line=0；观察程序退出0 | 退出1：`IP sample mode: no usable samples`；no_cu=1，usable=0，无profile |
| 501（完整正对照） | 成功，CU=1、49个DIE | Value，1帧，line=12 | 退出0，usable=1，写出profile |

500字节副本的原文节选：

```text
ELF_LOAD_OK
warning: DWARF unit from offset 0x00000000 incl. to offset  0x000001f5 excl. extends past section size 0x000001f4
DWARF_LOAD_RETURNED units=0 dies=0
FIRST_SYMBOLIZATION_BEGIN
...
FIRST_SYMBOLIZATION_VALUE frames=1 line=0
```

完整stdout/stderr、真实退出码及命令见[逐份结果](evidence/08/12_truncated_dwarf_results.json)、[原始命令输出](evidence/08/13_truncated_dwarf_commands.json)。额外用预置旧profile重跑500字节副本：退出1，前后SHA相同，见[旧输出保持](evidence/08/16_truncated_dwarf_old_output.json)。此处仍是补丁5工具，没有quality-report选项；不能声称已经取得generate阶段失败JSON或回调测试通过。

### 8.3 待裁决方案与当前停止范围

建议把验收拆成两条：

1. 真实截断DWARF文件：检查现有的no usable samples错误，在补丁6中产生generate失败报告、保留旧输出。明确它验证普通Error返回，不声称触发退出回调。
2. 按本轮已允许的隐藏注入方案，在**实际符号化调用点**令Expected返回Error，单独验证generate阶段兜底回调、无递归、旧输出及临时文件清理；加载后debug不可打开的测试仍按原要求执行，绝不删除输入文件。

另一候选是新增IP专用的DWARF损坏诊断升级策略，但这会改变“哪些可恢复诊断应致命、何时失败”的规则，不能仅为满足测试自行引入。单纯修改测试的预期退出码也不能替代回调验收。以上均**未实施**，已向用户请求裁决。

截至此停止点：补丁6源代码未改、无补丁6提交或0006导出、没有补丁6GBS构建/质量JSON/门槛/回调/真实数据报告验收。14次重放及77 PASS等是第7节的**补丁5独立验收**，不得冒充补丁6结果。新工具仍为 `095a7497ccda26f60ad075a4ce567b8cbd9159e1c9006749800f5d558279ead1`。

## 9. 待设计v0.8登记与挂账（当前）

- 已裁决、补丁5已实现验收：同映射段与前驱行信息条件，skid原因细分及原始地址分类；按函数分组起点检查。
- 已裁决、待补丁6实现：路径冲突覆盖所有输入/输出别名，检查先于ELF加载/写入/临时文件/回调；只stderr、不写报告是失败报告义务的唯一例外。
- 已授权、待补丁6实现：name_merged_functions；定点阈值精确比较及generate阶段失败；隐藏真实调用点错误注入（最终点名未定，尚无接口）。
- 待本次裁决：第8节的真实截断DWARF与回调验收是否拆分。未修改冻结文档。
- 原挂账不关闭：06完整LOST导出缺失；真实数据avg上板核对；选项枚举/cl::values留补丁7；非叶子line0实测后决定；正式非增量构建前撤销spec本地测试diff。

所有实验输出留在WORKDIR/temp。未连接开发板、未推LLVM/Gerrit、未改认证或索要密码，无新增已观察到的项目文件边界例外。

## 10. 截断DWARF裁决已收到；已有质量报告语义待明确

### 10.1 生效裁决（待设计v0.8登记）

用户同意拆分两条测试：真实截断、不注入，验证实际no usable samples、generate失败报告与分类；真实symbolizeInlinedCode调用点注入Error，经原有unwrapOrError→exitWithError验证generate回调。此前10种截断结果、平台生成命令、源码证据继续保留，第8节不再是阻塞。

另需至少一条不经注入的损坏ELF真实库内退出，验证load阶段回调；06列出的7处调用点逐条说明自然用例或注入点。其他不能自然触发的冻结用例，可同样采用“真实输入验证实际行为＋真实调用点注入验证回调”，逐条登记，不再为这类情况单独请求裁决；需要改变冻结规则本身时才停止。

### 10.2 不经注入的load退出素材（已验证可达性）

临时副本 `temp/profgen-patch6/natural-load-exit/invalid-symbol-name.perfbin`，来自补丁1的a64-pie.perfbin。用GBS root readelf -SW取得.symtab偏移与ELF64项宽，只将第1号符号的st_name改为0xffffffff，其余字节不变。ELF头仍可读；build-id、PT_LOAD、输入样本保持原样。无需删除文件、竞态或错误注入。

用当前补丁5工具运行：先输出完整IP地址/身份诊断，最终unverified（已显式allow-missing），随后从 `ProfiledBinary.cpp:230–235` 的Sym.getName返回Error，经`:274`的unwrapOrError及ErrorHandling.h退出1。原文：

```text
llvm-profgen: error: .../invalid-symbol-name.perfbin: Invalid data was encountered while parsing the file
```

预置旧profile前后SHA相同。原始命令/真实退出码/输出/哈希：[自然退出证据](evidence/08/19_natural_load_exit.json)；素材生成脚本：[可重现步骤](evidence/08/20_natural_load_fixture.txt)。此轮只验证现有调用点可自然触发，补丁6的回调与failure_stage JSON还未实现，不声称该lit已通过。

### 10.3 当前唯一待明确的报告覆盖语义

本次裁决同时要求“失败报告conversion=failed”与“预置旧报告逐字节不变”。此前裁决又明确：路径冲突是不写失败报告的唯一例外。对非路径冲突、已有report.json含conversion=ok的运行，这两项无法同时成立。[原文与最小反例](evidence/08/21_existing_report_contract.txt)

建议明确：旧profile始终不变；非路径冲突失败时允许新的失败JSON原子替换旧质量报告；路径冲突或报告写入/提交本身失败时保持旧报告。这是询问新措辞是否指同一路径的旧质量报告，不重新询问已闭合的DWARF裁决。另选未授权报告路径、静默放弃失败报告或仅检查另一份无关旧报告均未实施。

截至本次记录，LLVM工作树相对补丁5无工具/测试代码改动，只有原spec本地diff；没有补丁6提交、构建或0006。上一轮补丁5的lit、C1、工具SHA不变。待此语义明确后继续补丁6，其余裁决已生效，不重复请求。

## 11. 已有报告覆盖语义（最终裁决，待v0.8登记）

第10节中“旧报告不变”的歧义已由用户确认是PM笔误，作废。旧profile在任何失败中逐字节不变；非路径冲突失败以新的完整失败JSON原子替换旧质量报告；成功以成功JSON原子替换；路径冲突、报告自身创建/写入/flush/close/rename失败，保留旧报告并清理临时文件。profile提交失败时已提交的成功报告尽力改写为失败报告，改写本身失败只追加stderr说明。不存在两个文件一起原子提交的保证，遵循指定提交顺序。

`ip-quality-exits.test`预置`conversion=ok`旧报告，真实截断、真实坏符号表、符号化/打开注入均要求报告变为可解析的failed JSON、阶段正确，旧profile不变。`ip-quality-output.test`覆盖报告自身失败，`ip-quality-paths.test`覆盖输出别名；这两类要求旧报告不变。每例检查临时文件残留、流析构fatal及递归诊断。

## 12. 补丁6实现与共享代码门控

新增`IPQualityReport.h/.cpp`：`validateIPOutputPaths`、`IPQualityReport`、精确门槛、诊断数据收集与同目录报告提交。该对象在IP路径校验无别名之后创建，维护阶段、警告、profile临时文件与单次退出回调。IP自身用Error返回main；已有共享库的直接退出通过注册回调补报告。没有给报告或门槛时，新增的逐事件/分层period计数不运行，保持既有IP计数错误顺序。

| 文件 | 改动及门控 |
|---|---|
| llvm-profgen.cpp | 新增隐藏IP报告、三门槛与失败注入选项；IP入口先路径校验，随后报告对象覆盖加载至最终rename；无IP选项仍走原LBR入口 |
| ErrorHandling.h | 空回调保持旧打印/退出流程；有回调时move并清空后调用，防重入；Error重载仅注册时用toString，避免inconvertible StringError被errorToErrorCode提前fatal |
| ProfiledBinary.cpp/.h | IP加载点与真实symbolizeInlinedCode调用点注入；IPMode下收集同名函数来源起点与DWARF警告；原符号化/内联转换不改，LBR没有注入或回调 |
| ProfileGenerator.cpp/.h | IP保留原始usable计数、函数覆盖与写出位置；新writer仅IP，显式flush/close/clear_error后提交；已有warning调用增加无ActiveReport时无效的记录钩子 |
| IPPerfReader.cpp/.h | 质量功能启用时按完整事件名与既有筛选层收集uint64计数；保存输入SHA、处理进度、typed身份结果；既有地址计数及诊断格式不变 |
| IPIdentity.cpp | 保存逐路径/映射证据及最终等级，不更改身份判定逻辑 |
| CMakeLists.txt | 将IPQualityReport.cpp加入同一工具目标 |

隐藏选项`--ip-test-inject-failure`仅IP有效，16个点名：`runtime-open`、`invalid-image`、`runtime-metadata`、`debug-open-load`、`debug-metadata`、`context-create`、`symbolize`、`debug-open`、`profile-write`、`profile-flush`、`profile-close`、`profile-rename`、`report-write`、`report-flush`、`report-close`、`report-rename`。不删除/改动调试输入。报告新增`verdict.fallback_callback_count`便于核对单次回调；这些是测试接口，待v0.8登记。

## 13. schema、口径与确定性

`schema_version=1`，使用llvm::json::OStream；uint64不经过double。原始权重以`normalized_weight={numerator,denominator}`表达，分母为p_ref（sample模式为1）；未取得或分母0为字符串unknown。所有数组固定排序：事件/候选按完整名称字典序；映射和身份证据保持输入顺序；函数/DSO前N按原始所选权重降序、名字升序打破并列；边界来源/失败按既有稳定顺序；warning按稳定code字典序。没有时间戳。输入完整参数含输出路径，因此两遍确定性验收使用同一组路径。

| 5.6.1字段 | 实现口径与未知值 |
|---|---|
| tool/input | LLVM版本、完整argv、输入路径/SHA、ip-only；未读输入SHA未知 |
| event | 完整事件名含修饰符，筛选前分别sample_count/period_sum；type/config未知，不从名字猜 |
| semantics | weight、原始单位、输出单位、p_ref/来源、aggregation、dup、zero/head/skid、DWARF与FS状态 |
| identity/mapping | build-id读取状态、真实路径、原始候选/deleted、typed证据/等级、候选可执行/非执行映射数；不声称样本逐条绑定；completeness始终unknown |
| samples | input_total只有数量；后续每层数量/period/未取整权重；target分为段外、DWARF外三类、无行、usable；原始usable先于skid/聚合/裁剪；写出位置及skid原因 |
| isa | 映射符号优先、.symtab/.dynsym的函数SF_Thumb后备（排除SHN_ABS/未定义/非代码节）；未知/冲突只入unknown，不触发边界失败；数量与权重比例分别给出 |
| boundaries | 沿用补丁5按需函数数、来源、完整失败列表；不为报告触发枚举 |
| lost/throttle | records、L、S、L/(L+S)，scope=input/source=PERF_RECORD_LOST/count_unit=records/completeness=unknown；没有LOST时L与比例unknown，观察到的LOST记录条数为0；throttle未知 |
| ratios/sanity | usable/target两种原始口径及判定口径、usable/(usable+无行)；DWARF函数覆盖比例、A64对齐比例，不判断收益 |
| coverage | usable顶层函数数、唯一目标地址、原始权重top50；多个不同DIE起点按同名合并的有样本函数数与top50，不改合并逻辑 |
| consumer_hints/warnings/verdict | head=none时提示profi；稳定告警code；独立失败优先，门槛未设not_evaluated/未取得unknown/已知精确比较，充分性只有insufficient或unknown |

比率门槛只接受0、1或`0.`后1–9位数字；整数门槛为uint64十进制。比较用APInt交叉乘法，绝不浮点。所有检查在生成后、writer前，失败阶段generate；早期独立失败使尚未检查的已设门槛保持unknown。LOST比例分母超过uint64时明确溢出失败，不截断或输出浮点数。

## 14. 测试对照与库内退出审计

新增六组lit（Python逐字段/逐字节断言，无网络/板子/perf依赖）：

| lit | 覆盖 |
|---|---|
| ip-quality-fields | 全部schema根字段、混合单位隔离、原始usable口径与sum/max/avg/裁剪、ISA映射/.symtab与.dynsym的SF_Thumb/ABS排除/冲突unknown、LOST、双遍确定性 |
| ip-quality-thresholds | 定点语法和uint64边界；设置/不设置×已知/未知；passed/failed/exceeded/not_exceeded；无门槛但无目标失败；普通CLI错误写parse报告 |
| ip-quality-exits | 真实截断、真实坏runtime/debug符号表、7个共享退出位置与generate打开错误注入、identity/boundary失败 |
| ip-quality-output | profile写/flush/close/rename；报告写/flush/close/rename；自然gcc writer不支持；不可创建父目录；旧文件与临时清理 |
| ip-quality-paths | output=-、相同路径、符号/硬链接、规范化父路径、任一输出覆盖perfscript/binary；不注册回调、不创建临时文件；非IP选项门控 |
| ip-quality-writer | text use-md5告警、extbinary MD5生效；同一ProfileMap的IP/LBR extbinary逐字节一致 |

IP/LBR writer对照用pure-a64与单一`[0x1000,0x1000]:7`范围；IP补零建立相同body，LBR使用已有`--update-total-samples`把其字节范围total改为body合计，形成相同ProfileMap。没有改IP total规则或共享writer。旧reader/身份/计数/边界矩阵沿用ip-addresses、ip-invalid、ip-real-records、ip-identity-*、ip-counting-*、ip-boundary-*，本轮不重复改golden。

| 原06的7处共享退出 | 当前阶段/验证方式 | 自然触发限制 |
|---|---|---|
| createBinary运行文件 | load，runtime-open注入 | 输入ELF已被reader检查，稳定文件无法在第二次打开才突然失败；不制造竞态 |
| image类型检查 | load，invalid-image注入 | 非ELF已在IP reader拒绝；真实无效输入验证reader实际错误，不假称进入共享回调 |
| 运行文件IP元数据unwrap | load，invalid-symbol.perfbin自然触发及runtime-metadata注入 | .symtab[1].st_name越过字符串表；PT_LOAD/build-id仍可读 |
| createBinary debug文件 | load，debug-open-load注入 | 显式debug已通过身份检查，不在测试中删除输入 |
| debug元数据unwrap | load，invalid-symbol.debug自然触发及debug-metadata注入 | 与runtime同样的真实符号表损坏 |
| DWARFContext创建检查 | load，context-create注入 | LLVM create通常返回context对象，真实截断只警告并跳CU；不把截断当成null |
| symbolizeInlinedCode→unwrap | generate，symbolize/debug-open在真实调用点返回Error | 真截断查询返回成功line0，debug-open模拟该打开操作的Error，不改文件；经原unwrap→exitWithError |

真实截断单条样本独立预期：CU被丢弃，没有DWARF函数/行，no_cu=1、usable=0、generate/no usable samples、callback_count=0；原DWARF警告仍在stderr。自然坏符号表callback_count=1。注入也是1，不递归、不发生流析构fatal。全部均预置成功旧报告并检查被完整失败JSON替换，旧profile保持或不存在。10种截断长度、API行为及源码证据见第8–10节，不改历史事实。

### 14.1 warning代码清单

| 稳定代码 | 触发与测试/证据 |
|---|---|
| W_LOST_MAY_INCLUDE_SIDEBAND | 至少一条LOST；quality-fields与真实导出独立重算 |
| W_CONSTANT_PERIOD | 全部输入样本period相同；quality-thresholds/fields基本输入 |
| W_IDENTITY_UNVERIFIED | 身份门禁允许缺ID；quality-fields、真实旧库导出 |
| W_USABLE_RATIO_UNKNOWN / W_TARGET_COUNT_UNKNOWN / W_LOST_RATIO_UNKNOWN | 对应门槛已设但失败前未取得可判定指标；quality-thresholds的parse失败与无LOST成功输入 |
| W_LARGE_COUNT | 生成body/total超过UINT32_MAX；quality-thresholds的UINT64_MAX输入与既有ip-counting-arithmetic |
| W_MD5_IGNORED | 非extbinary使用use-md5；quality-writer |
| W_EMPTY_DENSITY / W_LOW_DENSITY | 既有密度建议；quality-fields裁剪失败/小输入及原profile-density；只记录、不改旧stderr |
| W_DWO_MISSING | 已有DWO加载不完整告警；quality-exits复用原split-dwarf-split.exe但不提供.dwo；foo VA0x400540、文件偏移0x540，实际缺DWO失败报告 |
| W_NO_DWARF_FUNCTIONS | DWARF加载后无函数；quality-exits真实截断和05/09 strip库 |
| W_DUPLICATE_FUNCTION_START | 已有同起点函数重叠告警；共享调用点审计，真实合成负载若出现按实记录（不人为制造不同于边界golden的符号表） |
| W_DWARF_RECOVERABLE / W_DWARF_WARNING | IP DWARFContext已有恢复/告警处理器转发原打印并记录代码；quality-exits真实截断；是否触发哪种由原LLVM诊断类型决定 |

警告按代码去重，完整原始stderr保留在验收日志；JSON不复制无界重复警告文本。代码和触发条件与已经触发的测试分开列出，未触发的警告分支不宣称已有独立运行覆盖。

完整导出清点（不是从新报告反推）：此前保存的14个目标运行输入都没有LOST文本行；名字含lost的05文件也没有该记录。06只有过滤后的942条LOST与L=61,667，缺完整样本导出，不能算独立的S或比例验收。此挂账继续保留，不能因合成quality-fields覆盖了LOST公式而关闭。

### 14.2 收尾静态检查发现并修正的问题

开发检查先发现ErrorHandling的Error重载会把inconvertible StringError交给errorToErrorCode，在IP回调之前fatal；已仅在回调注册时使用toString转到原字符串退出函数，原LBR路径不变。16个注入点和两个真实坏符号表均重新验证，没有fatal或递归退出。

首轮GBS编译发现C++17结构化绑定捕获扩展与旧make_scope_exit弃用告警；改为普通StringRef局部变量和scope_exit构造。ISA后备补读.dynsym函数，排除SHN_ABS、未定义、非代码节；增加strip与ABS负对照。边界枚举仍仅使用.symtab映射符号；outside_symtab_top20也严格只用.symtab，不将动态符号混入该字段。

对不存在输出的规范化，先解析现有父目录（保留符号链接后`..`的实际语义），再对剩余未存在尾部消除点路径。新增`parent-link/../missing2`与`real/missing2`冲突测试，检查递归目录清单不变。否则先做纯词法消点可能漏判，两份新输出互相覆盖；这是实现修正，不是冻结规则变更。选项语法校验阶段明确为parse。

所有中间GBS记录保留。最终验收以最后一次对应源码的GBS `%check`、C1与真实重放为准，不用较早工具的通过结果代替收尾版本。

早期选项/输入失败时，尚未取得的语义、事件列表、候选、映射列表和coverage榜单写unknown，而非以默认值或空榜单冒充已计算结果；新增相应断言。原始观察到的证据与最终身份等级分开保留。

榜单占比的分母：other_dso_top20用other_dso总原始权重；outside_symtab_top20用target总原始权重；coverage的top50与name_merged_top50均用usable总原始权重。ISA只统计已换算成功的目标VA，比例的分母仍为target；段外样本单列unmapped_in_target，所以ISA各项比例不一定合计1。A64对齐比例也是“已证明对齐的目标样本/target”，其余可能是未换算而非已证明不对齐。

写入注入在真实write/flush/close/rename调用点模拟错误返回，用于检查失败路径；不宣称制造了真实磁盘故障。实际坏ELF/截断DWARF/不可创建目录仍使用真实输入和真实错误。所有临时测试文件只在工作目录内。

### 14.3 规则—代码—测试位置

T=`temp/llvm-profgen-enh/llvm/tools/llvm-profgen/`；位置对应补丁6最终工作树，完整调用点审计另存evidence/08/29_patch6_exit_audit.json。

| 规则 | 代码（T下） | 验证 |
|---|---|---|
| 5.6.3路径最前校验 | `IPQualityReport.cpp:78` | ip-quality-paths |
| 5.6.1 schema/未知值/整数 | `IPQualityReport.cpp:427` | ip-quality-fields、thresholds |
| 5.6.1层级与多事件隔离 | `IPPerfReader.cpp:276` | ip-quality-fields |
| 5.6.2原始usable不受聚合影响 | `ProfileGenerator.cpp:298` | ip-quality-fields |
| ISA诊断/映射与函数符号 | `IPQualityReport.cpp:259` | ip-quality-fields |
| LOST输入级记录/未知 | `IPQualityReport.cpp:640` | ip-quality-fields、thresholds |
| 精确定点门槛语法 | `IPQualityReport.cpp:161` | ip-quality-thresholds |
| 生成后门槛检查 | `IPQualityReport.cpp:217` | ip-quality-thresholds |
| profile序列化、关闭与最后提交 | `ProfileGenerator.cpp:528` | ip-quality-output、writer |
| 报告原子替换与失败清理 | `IPQualityReport.cpp:743` | ip-quality-output、exits |
| 整个IP流程失败报告 | `llvm-profgen.cpp:307` | ip-quality-exits、paths |
| 兜底一次性注册/注销 | `IPQualityReport.cpp:133` | ip-quality-exits |
| 共享库原退出处回调 | `ErrorHandling.h:39` | ip-quality-exits；C1 |
| 真实符号化调用点注入 | `ProfiledBinary.cpp:1182` | ip-quality-exits |
| 同名多DIE来源计数 | `ProfiledBinary.cpp:1049` | 两档08合成负载 |

## 15. 正式构建、lit与C1

| GBS轮次 | 开始 / 结束 | 秒 | Ninja步数 | 真实退出 |
|---|---|---:|---:|---|
| build | 2026-11-03T19:39:59+08:00 / 2026-11-03T19:58:58+08:00 | 1139.703 | 108 | 0 / ALL-END OK |
| build-final | 2026-11-03T20:02:38+08:00 / 2026-11-03T20:23:02+08:00 | 1224.219 | 106 | 0 / ALL-END OK |
| build-verified | 2026-11-03T20:28:22+08:00 / 2026-11-03T20:42:46+08:00 | 864.668 | 107 | 0 / ALL-END OK |

三轮均完成，没有将较早结果冒充最后版本。收尾修改原因见14.2；源码编译告警已消除，平台原有build-id/项目配置提示保留。资源采样每10分钟；最低available 11745 MiB，最大used 19794 MiB；1/5/15分钟load采样峰值[68.16, 38.89, 18.96]。这些是采样峰值，不是连续监测极值；无available低于2GiB采样点。[构建/资源原文](evidence/08/22_patch6_builds.json)

最终GBS `%check`：85项，83 PASS、0 FAIL、1 UNSUPPORTED（cs-preinline-cost需要asserts，当前No）、1 XFAIL（invalid-perfscript）。原79项逐项保持，原50仍48/0/1/1，新增6组全PASS。[日志](evidence/08/23_patch6_lit.log)、[xunit](evidence/08/23_patch6_lit.xml)、[逐项核对](evidence/08/23_patch6_lit_summary.json)

C1最终两遍各636条（127原RUN＋1纯IP负对照＋508格式变体），两遍逐字节一致、相对已提交基线0差异；35个新增IP测试单列排除。开发阶段曾错误使用另一scratch目录，产生stderr路径差异；正式各轮均使用基线原路径，未归一化字节、未覆盖基线清单。[C1](evidence/08/24_patch6_c1_summary.json)

最终工具SHA-256：`4f115a34cf558008bc138c7aaf3d3476717ea7d5fc2e44ea4142ac6fb06cb4f9`。平台clang-format新文件/改动行及dry-run通过；IP自身的指定作用域无exitWithError/unwrapOrError/report_fatal_error，7处共享退出留在原库路径并覆盖回调。[格式](evidence/08/28_patch6_format.json)、[审计](evidence/08/29_patch6_exit_audit.json)、[行号索引](evidence/08/30_patch6_source_index.json)

## 16. 完整导出、合成负载与开销

14次运行每次各两遍；profile（包括不存在状态）、完整JSON、stdout与stderr两遍相同。地址诊断及旧生成分类与补丁5/此前已验收结果逐字节/逐桶一致；原始文本另行重算筛选层和事件period，未用新报告反抄预期。05/09的strip库解析成功但无usable，按原设计generate失败，不创建profile。

| 输入/目标 | 行数 | 样本总数 | 目标 / usable | 退出 | 身份 |
|---|---:|---:|---:|---:|---|
| 05-fixed | 7703 | 7659 | 6496 / 0 | 1 | unverified |
| 05-multi | 27112 | 22662 | 13289 / 0 | 1 | unverified |
| 05-freq | 4930 | 4886 | 4096 / 0 | 1 | unverified |
| 05-buildid | 7510 | 7466 | 6322 / 0 | 1 | unverified |
| 05-lost | 1044585 | 1044541 | 943893 / 0 | 1 | unverified |
| 07-fork-cases | 9861 | 9845 | 9840 / 9802 | 0 | unverified |
| 07-exec-cases | 5946 | 5925 | 4833 / 4829 | 0 | unverified |
| 07-exec-after | 5946 | 5925 | 1081 / 1081 | 0 | unverified |
| 07-deleted-libdeleted_probe.so | 169 | 151 | 151 / 151 | 0 | unverified |
| 07-module | 334304 | 318382 | 51874 / 0 | 1 | unverified |
| 09-fixed | 7661 | 7617 | 5865 / 0 | 1 | unverified |
| 09-multi | 31066 | 26778 | 14331 / 0 | 1 | unverified |
| 09-freq | 2625 | 2581 | 2006 / 0 | 1 | unverified |
| 09-buildid | 7270 | 7226 | 5611 / 0 | 1 | unverified |

[逐份独立计数、旧输出与确定性比对](evidence/08/25_patch6_real_exports.json)。完整原始输入路径、ELF路径、命令在该证据中；报告及大stdout/profile位于`temp/profgen-patch6/implementation/real/`。最大输入为05-lost，1044585行。

单次热缓存观测（直接子进程wait4 rusage）：补丁5工具不带报告 1.395613秒 / 320084 KiB；补丁6带报告 1.714590秒 / 320260 KiB。不据单次数据推断稳定开销或性能收益。[命令与测量](evidence/08/26_patch6_timing.json)

两档均为**合成负载规模测量**，不是真实采样，不验证avg数值。

| 输入 | usable函数数 | 同名合并函数数 | 墙钟秒 | RSS KiB | profile与补丁5 |
|---|---:|---:|---:|---:|---|
| largest20 | 20 | 2 | 0.727723 | 96180 | 相同 |
| all-executable | 4090 | 308 | 2.519621 | 319396 | 相同 |

20函数档的两项同名合并为decode_frame、iadst_iadst_16x16_add_c，与补丁5证据吻合；全部可执行函数档308项，top50按权重排序，20函数档两名并不必然进入该top50。未改变同名合并逻辑。[覆盖与规模](evidence/08/27_patch6_synthetic_scale.json)。大文件留`temp/profgen-patch6/implementation/scale/`。

## 17. 提交、待v0.8登记与挂账

LLVM补丁6：`1dd4b9acd84045c230e77cc68d85eafca58eae88`；只含工具/测试目录，spec本地diff逐字节不变且未提交。0006为binary format-patch，反向应用检查通过；0005仍为第7节独立验收的amend版本。[提交/范围审计](evidence/08/36_patch6_commit_audit.json)

待设计v0.8登记（不改冻结v0.7）：

1. 补丁5同映射状态段、前驱有行信息的skid约束及原因桶；分组边界校验。
2. 路径冲突为失败报告唯一例外：包含输入别名，且在任何写入/临时文件/ELF加载/回调前拒绝。此前旧报告笔误作废：非冲突失败原子替换失败JSON，报告自身写入失败保留旧报告；成功原子替换成功报告。旧profile在任何失败中保留。
3. 截断.debug_info不自然产生Expected Error：真实截断验证no_cu/usable0/no usable samples；真实symbolize调用点注入验证generate回调，另用真实坏符号表验证load回调。其余7处自然/注入边界见14节。
4. 16个隐藏注入点、fallback_callback_count测试字段；coverage.name_merged_functions与top50披露现有合并行为。
5. 门槛定点文本语法与APInt比较；阈值失败阶段generate；新增字段和unknown/排序/分母约定见13节。

继续挂账：06缺完整LOST导出；avg真实数据须重新采集08产物；IP枚举选项/cl::values留补丁7；非叶子line0由上板实测决定；正式非增量构建前撤销spec本地测试改动。未开始补丁7或Agent设计开发。未连接开发板、未推LLVM/Gerrit、未改认证或索要密码。除读取用户指定任务附件作为已授权输入外，无新增已观察到的项目文件边界例外。
