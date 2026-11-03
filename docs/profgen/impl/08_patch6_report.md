# 补丁5小修完成；补丁6截断DWARF必测项待裁决

2026-11-03。最新状态：补丁5小修已独立验收并amend；路径冲突裁决和截断DWARF拆分裁决均已收到。第10节记录新的验收要求与真实库内退出素材。补丁6尚未改LLVM代码：本次新增“旧报告逐字节不变”与此前“非路径冲突失败写失败报告”在报告已存在时冲突，覆盖语义待明确；没有再次请求截断DWARF的裁决。

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
