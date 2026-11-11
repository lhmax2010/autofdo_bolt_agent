# 登记前核对：Q.5 状态总表与第一批

设计：v1.8；基线7c96c1e。本表先于本批执行建立。只根据仓库证据，不以设计中的“待核对”或历史局部通过推断整体通过。状态快照与本批结果分开记录。未读取任何正式sample profile（含CALIBRATION），未登记修正案3。

## 1. 执行前状态（Q.5第1–21项）

证据提交全哈希见 [initial-evidence-commits.json](evidence/registration-checks/batch1/initial-evidence-commits.json)。表内未开始指当前v1.8该项尚无完整实施证据，不否认旧版本局部原型。

|项|状态|已完成与证据（提交/文件）|剩余|需要板子|需要真实profile|
|---|---|---|---|---|---|
|1|已完成|08报告的前驱检查、四种skid原因与补丁9的无效前驱测试；15报告正式lit通过；3b6bcb0 / [08_patch6_report.md](../../impl/08_patch6_report.md)|本批不重做|否|否|
|2|部分完成|补丁6已有16个注入点与失败契约验收；G.1.7要求的argv及准入变体尚无完整专项证据；3b6bcb0 / [08_patch6_report.md](../../impl/08_patch6_report.md)|本批补argv追溯、未命中注入点、五类命令准入|否|否|
|3|部分完成|补丁8规则和派生素材已有；1c113f0 / [13_patch8_thumb_dwarf.md](../../impl/13_patch8_thumb_dwarf.md)|本批按avg重跑三项负对照|否|否|
|4|部分完成|补丁6提交顺序例外、同名统计已实现；旧正式lit通过；3b6bcb0 / [08_patch6_report.md](../../impl/08_patch6_report.md)|本批重跑与canonical化源码复核|否|否|
|5|部分完成|静态映射、全顶层边界/键枚举和身份域已形成；不能替代两条独立路径；7c96c1e / [05_identity_gate_and_coverage.md](05_identity_gate_and_coverage.md)|本批①②③及夹具；④CALIBRATION等待单独裁决|否|仅④需要（本批禁止）|
|6|部分完成|四对象①–③′、n_eff、K、三口径及v1.8门禁已完成；7c96c1e / [05_identity_gate_and_coverage.md](05_identity_gate_and_coverage.md)|列出avg/prev-inst可用性、登记时封存|否|不需profile；只读转换报告|
|7|未开始|未找到当前v1.8 M1/M2全部判读夹具的验收证据|按Q.5完整实现|否|否（合成）|
|8|未开始|覆盖副本合并有局部夹具，不能代替本项S/S_alt/S_sum；0bb587f / [01_coverage.md](01_coverage.md)|完整合并口径夹具|否|否（合成）|
|9|未开始|既有bootstrap原型不等于v1.8分层t/包络完整模拟|先登记清单/种子再模拟|否|否|
|10|未开始|v1.8结论数值门禁已验收，但未找到本项统计/槽位/恢复事件完整实现；7c96c1e / [05_identity_gate_and_coverage.md](05_identity_gate_and_coverage.md)|全部本项夹具|否|否（合成）|
|11|未开始|旧board_plan不是本项矩阵自动门禁验收|矩阵、N公式与不混用规则夹具|否|否|
|12|未开始|旧板上诊断存在，不满足加装散热后本项采样器/日志完整流程|本项全部板上验收与G0预试|是|否|
|13|部分完成|四对象lcov DA/JSON一致、主文件/宏区、副本夹具与HasMultipleRegions已有证据；0bb587f / [01_coverage.md](01_coverage.md)|本批补主文件函数范围与summary交叉核对|否|否（C参考不是sample profile）|
|14|未开始|第一轮旧资格标签不等于本项新规则验收|离线夹具及遥测原件重放|否|否（遥测即可）|
|15|已完成|v1.8四对象静态表、1%门槛、③与两个账本断言通过；7c96c1e / [05_identity_gate_and_coverage.md](05_identity_gate_and_coverage.md)|登记时封存；本批不改静态数值|否|否|
|16|部分完成|全部身份已闭合、无键规则、外部CU及裁决证据通过；全顶层复核不变；7c96c1e / [05_identity_gate_and_coverage.md](05_identity_gate_and_coverage.md)|逐条核销Q.5全部扩展夹具；本批5关联项先做|否|否|
|17|部分完成|历史报告披露曾转换正式S、质量统计尚未开展；未有完整登记披露表；d4137a2 / [quality_round1.md](../quality_round1.md)|汇总正式profile打开清单、量；加入后续G0条件/开销|G0依赖12|不需重新打开；依据日志|
|18|未开始|尚无本轮G0预试CV和登记N|第12项后计算或明确采用默认40|依赖12|否|
|19|未开始|静态候选产物已有，修订3尚未登记；7c96c1e / [05_identity_gate_and_coverage.md](05_identity_gate_and_coverage.md)|全部登记材料/槽位/收据封存与独立提交推送|间接依赖12|否|
|20|已完成|原205+v1.8新增45=250通过；八份行表前提和不变性通过；7c96c1e / [05_identity_gate_and_coverage.md](05_identity_gate_and_coverage.md)|登记时随最终产物重跑|否|否|
|21|已完成|v1.8已入库、设计评审完成，约定不再评审；第20项验收通过；7c96c1e / [05_identity_gate_and_coverage.md](05_identity_gate_and_coverage.md)|无本项剩余；整体登记仍受其他项阻断|否|否|

## 2. 本批执行顺序与门禁

依次执行2、3、4、13、5①②③；5④不做。使用补丁9正式工具，启动核对SHA。所有工具与证据只取WORKDIR；每项若需要GBS/llvm-profgen重建、板子或正式profile，执行前停止。本批只添加项目验收脚本，不修改LLVM补丁。资源3G/200%、nice19/ionice-c3，串行。

## 3. 本批结果与当前状态

第2、3、4、13项通过；第5项①②③及本项夹具通过，④未执行，故第5项整体仍为部分完成。没有连接板子，没有读取正式sample profile或CALIBRATION，没有登记修正案3。所有新增profile均由本批构造的合成perf文本或既有lit素材生成；C参考的插桩profdata不属于sample profile。

|当前状态|Q.5编号|剩余说明|
|---|---|---|
|已完成（8项）|1、2、3、4、13、15、20、21|第1节历史证据加本报告§4–7；不是整体登记许可|
|部分完成（4项）|5、6、16、17|5仅剩本项④；6须列出历史avg/prev-inst可用性并封存；16须将扩展身份夹具/同名范围外清单逐条核销；17须汇总历史披露及G0信息|
|未开始（9项）|7、8、9、10、11、12、14、18、19|见第1节逐项剩余与依赖；不在本批启动|

本批证据以本报告所在提交封存，完整路径/SHA见[manifest.json](evidence/registration-checks/batch1/manifest.json)。脚本位于`tools/profgen_eval/registration_*.py`。不以新增synthetic分类测试宣称第7、8、9、10项的指标或统计门禁已完成。

## 4. 第2项：注入追溯与评估准入

使用未修改的补丁9正式工具，SHA-256为`2e8895afce661b5fdc8cacab2b3323496fca51af7bd7b51c3753aa8328b7d0d5`。通过GBS root加载器/库执行，未构建llvm-profgen。`registration_tool_checks.py`重跑已有lit Python断言，并在每次子进程返回后先保存实际argv、stdout/stderr、真实退出码与前后文件状态；随后才运行测试断言。

- `output`19次、`exits`27次、`fields`18次、`thumb`27次，共91次工具调用通过原断言。注入用例中26次新提交报告的`tool.arguments`与实际工具argv逐元素相等（包括注入选项）。4次报告write/flush/close/rename失败没有新报告，改以执行器证据断言非0退出、旧报告/旧profile逐字节不变。
- 未执行到注入点单列4次：未给debug文件时的`debug-open-load`、`debug-metadata`；未请求报告时的`report-write`、`report-rename`。均退出0、profile存在，不伪称触发了故障。前两次成功报告仍保留注入argv，后两次由执行器保存argv。
- `registration_admission.py`不展开响应文件；拒绝`@rsp`，以及`-ip-test-inject-failure=X`、`--ip-test-inject-failure=X`、单横线分离值、双横线分离值，空注入值也拒绝。8项synthetic准入测试通过。此准入用于评估生成入口；lit故障测试不经过评估准入。

证据：[output索引](evidence/registration-checks/batch1/q234-output/index.json)、[exits索引](evidence/registration-checks/batch1/q234-exits/index.json)、[fields索引](evidence/registration-checks/batch1/q234-fields/index.json)、[thumb索引](evidence/registration-checks/batch1/q234-thumb/index.json)、[8条合成全地址命令的准入核对](evidence/registration-checks/batch1/synthetic-generation-admission.json)。各索引中的CSV保留命令和原文；大/完整运行目录位于`temp/registration-batch1/`。

## 5. 第3、4项：派生负对照、提交失败与名字

第3项按既有GNU Thumb测试的avg命令重跑，三份均退出1、`failure_stage=boundary`，没有profile产出：

|派生素材|失败原因原文关键部分|
|---|---|
|odd-arm|`unaligned A32 range start`|
|odd-data|`no runtime code section for DWARF range`|
|odd-middle|`range starts inside a Thumb instruction`|

完整命令、stderr及失败报告字段见[q3-derived-negatives.json](evidence/registration-checks/batch1/q3-derived-negatives.json)，没有重建或调整素材。

第4项重跑`profile-rename`等输出提交测试和`name_merged_functions`测试通过。源码确认先提交质量报告，再提交profile；后者失败会尝试重写失败报告，重写失败时stderr给出错误。原测试覆盖profile提交失败后成功写出失败报告；本批没有新增“双重提交故障”的自然触发测试，失败报告自身写入/提交失败由第2项独立用例验证，不把这两条独立测试冒充同时发生的故障。

写profile的`ProfiledBinary.h:620`传入`SymbolizerOpts.UseSymbolTable`，`ProfiledBinary.cpp:1212`固定为false，`:1297–1298`的canonical分支不执行。正式工具拒绝`--show-canonical-fname`，退出1、parse失败，stderr原文为：

```text
llvm-profgen: error: option --show-canonical-fname is not supported with --ip-samples
```

源码位置、带行号摘录与文件SHA见[source-contracts.json](evidence/registration-checks/batch1/source-contracts.json)，实际调用见[contract-extras.json](evidence/registration-checks/batch1/contract-extras.json)。未修改LLVM代码或既有测试。

## 6. 第13项：主文件范围与lcov/JSON summary

已有DA逐行一致、宏区域识别、覆盖副本合并、HasMultipleRegions与相关7项夹具的证据仍用[01_coverage.md](01_coverage.md)，本批不重新导出FFmpeg覆盖文件。

新增小型独立读取程序`temp/registration-batch1/coverage_ranges_v2`，用工作目录GBS Clang/LLVM库编译，直接读取C对象和C插桩profdata。没有GBS构建、没有重编Clang或llvm-profgen。它逐函数调用`getCoverageForFunction`取得映射行，再按每文件instantiation group的最大行数/覆盖行数求和，与两种导出的summary交叉核对。主文件按FileID而非物理文件名识别；范围只取该主FileID的CodeRegion。源码依据见`CoverageMapping.cpp:1468–1480,1542–1567`、`CoverageSummaryInfo.cpp:80–140`和`CoverageReport.cpp:444–469`（上述源码证据文件）。

|对象|函数记录|文件|空主文件|范围/FN/FNDA差异|DA行数/正计数行数|JSON及lcov LF/LH|summary差异|
|---|---:|---:|---:|---:|---|---|---:|
|spike Thumb|11|1|0|0|126 / 116|119 / 109|0|
|spike A32|11|1|0|0|126 / 116|119 / 109|0|
|FFmpeg Thumb|28,236|498|0|0|114,750 / 8,716|112,206 / 8,298|0|
|FFmpeg A32|28,236|498|0|0|114,750 / 8,716|112,206 / 8,298|0|

lcov FN的起始行、FNDA、JSON函数主区域范围与API全部一致；每函数API行都位于所算范围内。JSON本身没有现成的函数终止行字段，不能声称直接与不存在的字段比较。文件summary使用实例组归并，DA则为文件行视图，故DA行数不要求等于LF；上述差额按LLVM实例组规则重现，未用猜测的范围过滤抹平，也未改变参考DA、C或U。

逐函数/逐文件结果索引：

- [spike Thumb](evidence/registration-checks/batch1/spike-thumb-coverage-ranges-v2/index.json)
- [spike A32](evidence/registration-checks/batch1/spike-a32-coverage-ranges-v2/index.json)
- [FFmpeg Thumb](evidence/registration-checks/batch1/ffmpeg-thumb-coverage-ranges-v2/index.json)
- [FFmpeg A32](evidence/registration-checks/batch1/ffmpeg-a32-coverage-ranges-v2/index.json)

完整函数表及API JSONL位于`temp/registration-batch1/`，索引登记SHA和生成命令。没有触发需要扩大资源档位或重新GBS构建的停止条件。

## 7. 第5项①②③：合成全地址、独立关系与排除组

只从已经封存的静态边界证明中取映射范围内每个指令起点，每地址恰好一条周期为1的**合成样本**。用GBS readelf读取可执行PT_LOAD，按`off = p_offset + address - p_vaddr`生成dsoff，要求唯一落段。正式工具固定`weight=sample, aggregation=max`，分别用skid=`none`与`prev-inst`。合成输入没有录制侧身份记录，显式使用`--allow-missing-build-id`；目标runtime/debug自身的SHA和身份链不变。本验证不是采样证据，也不用于质量或资格判断。

|对象|合成指令地址数|独立路径可接受键的地址数|排除地址数|none写出条目|prev-inst写出条目|关系/分类差异|
|---|---:|---:|---:|---:|---:|---:|
|spike Thumb|358|326|32|93|92|0|
|spike A32|359|332|27|92|91|0|
|FFmpeg Thumb|413,090|352,424|60,666|83,031|81,017|0|
|FFmpeg A32|401,052|339,894|61,158|82,287|80,083|0|

合计814,859个指令地址、8次转换。所有写出条目均命中静态映射表；`unknown_name`、`reference_unresolved`、`unmapped_key`、实际`boundary_unavailable`和`known_out_of_scope`均0。命中映射不等于进入U：FFmpeg还包含未执行参考源、系统头、身份歧义和被排除行，逐条按原始函数名与完整键分类，未去掉`.__uniq.`后缀。细分类清单及汇总在各对象`fine-classification.json`。

第二条路径使用GBS `llvm-symbolizer --functions=linkage --no-demangle --inlines --output-style=JSON --verbose`，按地址逐条查询（一次进程读取地址流），独立计算16位行偏移、base discriminator、完整内联链及行0排除；未调用映射生成器的键函数。另独立实现已登记的spike调试路径前缀规范化，同时保留raw FileName。与原静态地址证明及已封存的静态SQLite候选映射比较：每条地址、键、源文件/行/discriminator、排除原因、每组地址数和每个键/源位置的地址重数全部一致。删除碰撞地址而保持键集合不变也不能通过。独立关系JSONL逐地址保存于temp，路径与SHA在`independent-relation.json`。

本构建四份映射范围内的别名查询数均0；GNU AS Thumb别名另由原27次GNU测试和synthetic夹具验证，不冒称实际四对象覆盖了别名。四对象未启用FS discriminator，取证metadata已断言。CLI与正式工具都使用LLVM库，这不是第二套DWARF解析器；独立性限于用户指定的命令路径、键计算和关系核对。CLI默认允许符号表回退，实际查询的全部名字和源位置仍与正式路径一致。

地址排除细分：spike Thumb/A32叶子行0分别32/27；FFmpeg Thumb叶子行0为55,682、非叶子行0为4,984；FFmpeg A32分别56,866/4,292。这些是静态合成地址数，不是正式采样计数。

本构建无边界失败组，因此另用`bad-conflict.perfbin`：max/none成功，条目单列为`boundary_unavailable`且synthetic RUN分类有定义；max/prev-inst与avg/none均退出1、boundary失败。命令与原文见[contract-extras.json](evidence/registration-checks/batch1/contract-extras.json)。

本批第5项38个新synthetic单元测试覆盖全部列出的夹具：冷地址缺失、碰撞地址删除、键值交换、错位前驱；同键异源/同源；不同命中集合、删热点、显式零、预算改变而静态SHA不变；discriminator、Thumb别名、行0、偏移碰撞、路径差异；歧义与正常键同一行；名字闭包/去后缀陷阱；微小未对齐键；整组边界排除/热点内联体/小FNDA大循环DA；歧义顶层和内联体、pending阻断；补零profile不准入指标。v1.7/v1.8原有特殊状态顺序与domain/结论门禁测试一并保持通过。每项测试名与源码行见[fixture-index.json](evidence/registration-checks/batch1/fixture-index.json)。

对象索引分别在`evidence/registration-checks/batch1/{spike-thumb,spike-a32,ffmpeg-thumb,ffmpeg-a32}-addresses/`。完整合成profile、关系表、分类表保存在`temp/registration-batch1/`及`detail-tables/`；[bulk-tables.json](evidence/registration-checks/batch1/bulk-tables.json)记录全部路径与SHA。④CALIBRATION未执行，第5项不能标为整体完成。

## 8. 验收、资源、开发失败与停止边界

原250项测试文件逐字节不变；新增46项（准入8、映射/分类38），共296项通过，见[最终测试原文](evidence/registration-checks/batch1/unit-tests-selection-integration/stderr.txt)与[original-tests-unchanged.json](evidence/registration-checks/batch1/original-tests-unchanged.json)。另有95次契约/素材工具调用（91+4）、8次全地址转换；这不是重新运行GBS %check或声称增加了103个lit测试。

全部任务串行，nice19、ionice-c3、3G/200% scope。已保存采样文件中的最低MemAvailable为9,075,150,848字节（约8.45GiB），cgroup memory.peak最高2,051,166,208字节（约1.91GiB）；没有OOM、资源暂停或终止。[resources-summary.json](evidence/registration-checks/batch1/resources-summary.json)列出各任务、峰值和原始meminfo路径。这些是采样观察值，不是两次采样之间的系统最低值证明。

两处新增辅助程序的开发失败均保留：

1. 最初范围读取器按物理文件名过滤主文件，把相同物理文件不同FileID的宏区域混入。spike的范围断言失败；已改为按主FileID匹配，v2四对象通过。失败材料`coverage-range-spike-thumb/`、`spike-thumb-coverage-ranges/`保留，v2没有覆盖它们。这不是正式工具缺陷，也没有修改定义或既有静态产物。
2. 契约额外4次调用已通过后，辅助脚本摘录源码请求到第891行，但文件仅886行，发生IndexError。4次原文已写出；修正摘录边界后单独重跑取证通过（`source-contracts-fixed/`），未重复或篡改工具运行结果。

没有重编GBS Clang/llvm-profgen，没有修改设计、LLVM补丁、认证或三个用户配置项。未登记修正案3；不进入第5项④、模拟、统计质量或其他Q.5项目。完成本批后停止。
