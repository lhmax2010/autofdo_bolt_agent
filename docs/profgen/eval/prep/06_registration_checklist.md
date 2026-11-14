# 登记前核对：Q.5 状态总表与分批验收

设计：v1.8；基线7c96c1e。本表先于本批执行建立。只根据仓库证据，不以设计中的“待核对”或历史局部通过推断整体通过。状态快照与分批结果分开记录。第一批未读取任何正式sample profile（含CALIBRATION）；第二批仅在专项授权及打开前披露后读取四份CALIBRATION基准转换，见§9。修正案3未登记。

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

## 9. 第二批：CALIBRATION、封存草稿与合成门禁（基线 ef57cd8）

### 9.1 范围、披露与流程结果（第5项④、第17项）

本批先读v1.8原文与既有状态，确认main与origin/main均为ef57cd80630fe17c987b57370af7fcb519b2d0a1；只有三个受保护的untracked配置项。未读这些配置，未接板、未编译Clang或llvm-profgen。

[打开前披露](17_profile_disclosure.md)与[输入路径/SHA](evidence/registration-checks/batch2/disclosure-before.json)先于perf文本读取写入。选择第一轮`calibration-runs.json`登记的四个成功校准RUN，每对象一份：cal-thumb、cal-a32、cal-ffmpeg-thumb、cal-ffmpeg-a32。它们没有混入正式矩阵；失败的226样本校准、频率试采、其他正式RUN均不打开。原收据SHA先登记，执行时全部复核一致。

正式工具仍为补丁9，SHA `2e8895afce661b5fdc8cacab2b3323496fca51af7bd7b51c3753aa8328b7d0d5`，每次启动都核对。复用原命令的runtime/debug ELF、GBS加载器/库与锚定路径正则，按v1.8唯一基准改为 **max / skid=none / weight=period / head=none / zero-fill=none**；输出text只为分类读取。旧`profile.extbinary`不打开、不比较、不覆盖。原始`perf.data`只通过既有收据列出路径/SHA，不打开；实际输入为完整`perfscript.txt`与`buildid-list.txt`。

每次生成后先做不解析内容的字节SHA，写入`cal-*/before-classification.json`，再解析新profile。解析器丢弃body数值，只保留原始名字、完整调用链键及文本行号；没有计算body权重之和、任何比例、M1/M2/M2b/M3或其他受控量。工具转换自身写出的quality报告保留在temp，未用于分析。新profile及输入的准确路径、SHA、命令、stdout/stderr、退出码都在各`cal-*`证据中。

|对象/RUN|转换/分类退出码|条目总数|进入U|系统头（已对齐、域外）|参考歧义（已对齐、不在U）|身份歧义（已对齐、不在U）|known_out_of_scope|未对齐|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|spike Thumb / cal-thumb|0 / 0|24|24|0|0|0|0|0|
|spike A32 / cal-a32|0 / 0|26|26|0|0|0|0|0|
|FFmpeg Thumb / cal-ffmpeg-thumb|0 / 0|1551|1477|4|67|1|2|0|
|FFmpeg A32 / cal-ffmpeg-a32|0 / 0|1604|1532|2|69|0|1|0|

这些都是**条目个数**，不是body权重、采样条数或质量比例。四份的boundary_unavailable、unknown_name、reference_unresolved、unmapped_key均为0；宏生成、参考侧未执行等其余分类也为0。各条目的精确键与分类见`cal-*/entries-*.csv`；排除原因用已封存的C₀排除清单细分，见`reason-detail-*.csv`。不存在因计数小而忽略未对齐条目的处理。汇总：[smoke-summary.json](evidence/registration-checks/batch2/smoke-summary.json)。第5项④通过，第5项现已完成。

### 9.2 第6项：历史可用性与对象封存草稿

只读历史命令与退出码元数据，不读取历史profile。检查补丁9重转的106次sample转换与额外20次period转换，共126次；命令均为sum / skid=none。因此不能从这批结果声称avg或prev-inst成功，亦不把未尝试算为转换失败。

|对象|补丁9历史命令记录数|avg|prev-inst|
|---|---:|---|---|
|spike Thumb|33|未尝试，success=null|未尝试，success=null|
|spike A32|33|未尝试，success=null|未尝试，success=null|
|FFmpeg Thumb|55|未尝试，success=null|未尝试，success=null|
|FFmpeg A32|5|未尝试，success=null|未尝试，success=null|

另保存12报告`31_real_avg_independent.json`中的旧补丁8 FFmpeg Thumb avg退出0事实，明确不等于补丁9可用性。没有为填表重新运行avg/prev-inst。逐命令/退出报告路径与SHA见[availability.json](evidence/registration-checks/batch2/availability.json)及`historical-conversions-*.csv`。

[对象封存草稿](evidence/registration-checks/batch2/object-seal-draft.json)汇集四个既有训练参考对象的①②③③′、三口径③、代码承载比例、评价域外比例、n_eff、K、domain状态与上述可用性，来源均为v1.8静态summary；没有重算或改变C/U/权重。SHA：`c7095475d9c1e085ce39edd497a23d6eaa54c756cf56084e808c449f3db20caa`。它是`unregistered_seal_draft`，**不是修正案3**；第19项仍需把最终全部产物与协议一起登记。第6项剩余的核对与草稿已完成，参数实际可用性仍如上表，不推定。

### 9.3 第7、8、10项：原文逐条实施与synthetic验收

完整对应表：[clause-mapping.md](evidence/registration-checks/batch2/clause-mapping.md) / [JSON](evidence/registration-checks/batch2/clause-mapping.json)。表保留Q.5原文、设计行号、实现文件/函数/行号、测试名与PASS；按原文分号展开42条，复合条款列出全部子例。原文、实现与测试的SHA随索引保存。

|项目|实现|本批验收|
|---|---|---|
|7 M1/M2与分支|`registration_statistics.py`：`line_metrics`、`hot_reference`、`interpretation`|22项MFixtures通过；含N15/K9、全零/单正/正并列/正计数不足、T0/U空/K无定义、null n_eff四个K、n_eff=3、10行空集合、80%整数边界；另外保留v1.8评价域输出门禁|
|8 合并口径|同模块`merge_lines`|6项通过；互补上下文得到100/200/200，不同内联调用点、覆盖region原值保存、discriminator、未执行模板不借用执行实例行、源函数归属、显式0|
|10 统计|同模块`phase_diagnostics`、`stratified_t`、`intervals_joint`、`paired_differences`、`assess_paired_metrics`、`outliers`|27项通过；同ID配对、缺失不补零/不改阶段权重、逻辑RUN、退化与nextafter、NaN、单/双阶段、包络、全局回退及敏感性分支、模型标识、离群、固定间隔不比较权重|
|10 收据/状态/门禁|`registration_protocol.py`：`validate_slots`、`replay`、`validate_recovery`、`admit_computation`、`compute_guarded`、`GitEvidence`|18项协议＋19项恢复＋18项准入通过；全部Q.5停止/恢复负例，三段证据，未推送/缺初始化/重复原件/终态改写/14槽未终态/缺日志拒绝|

实现选择与边界：

- 统计模块纯Python标准库、单进程，无profile读取器，无第9项模拟驱动。未来模拟与正式分析共用此模块；本批只运行指定synthetic夹具。bootstrap固定seed=20261104、20000次，阶段内重采样，M1/M2共用索引；percentile采用固定的经验线性插值`(B−1)*p`，没有按结果选择方法。t分位数用正则不完全beta的连分式和二分反解，df=1/2解析值及df=14对照通过。退化严格用double字面量1e-9，先记录原始极值和极差，未量化后计算区间。
- 缺失保留计划槽位与阶段权重；没有给失败转换记零分、没有只删某配置的RUN。尚未收齐15个终态、required指标缺失、flat或全局开关false均不输出等价。判读只是内存结果；实际文件输出仍必须走既有`v18_rules.write_conclusion`的对象表SHA/评价域/数值检查。本批未输出任何真实质量结论。
- 收据/计算日志是追加式SHA链。`append_file`校验tip、加锁追加并fsync；`GitEvidence`校验blob SHA和已存在于origin/main的提交历史，并验证已推送事件历史只能扩展，重算整条链不能掩盖改写。只读后端不fetch、不改认证；正式执行前应由入口刷新远端引用。合成Git夹具位于WORKDIR/temp，无网络、无LLVM远端。
- 登记前或没有已推送计算意图时，`compute_guarded`在调用数据操作前拒绝。真实路径核对登记协议、槽位、全部锁定产物的blob及工作区字节、脚本SHA、原件归属与收据、计算日志链；合成路径单独标记。敏感性与新增质量量同受此门禁，不用白名单遗漏来放行。
- 证据schema以attempt_id/boot_id/单调时钟关联故障、恢复前环境、身份复核三段，并引用SHA核验的证据。空间/过热/人工停止均需关联停止动作；仅时间附近异常不够。恢复沿用原条件和尝试次数，后续尝试引用恢复事件；不可恢复错误优先，stopped_missing不可撤销。传输中断只允许同attempt、同原件重传，不是再跑负载。原因码白名单及阈值均由将来登记协议输入；测试中的数值与原因码明确是synthetic，不改变真实资格阈值或采集规则。
- 没有把真实输入交给指标模块。第9项模拟、第11/12/14项以及其他未授权项目均未启动；本批不提前确定`quality_equivalence_enabled`的真实值。

### 9.4 测试、资源与失败记录

原有296项测试文件逐字节不变；新增114项，合计**410项全部通过**。新增数包含上述110项以及4项只读取合成字符串的CALIBRATION解析器测试。旧静态产物、设计文档无diff：[unchanged-baseline.json](evidence/registration-checks/batch2/unchanged-baseline.json)。正式验收原文：[tests-acceptance-final/stderr.txt](evidence/registration-checks/batch2/tests-acceptance-final/stderr.txt)。

开发失败保留：可用性脚本首次漏导入Path，退出1，补导入后成功；追加历史的合成Git测试发现单行JSONL被读作普通dict，改为识别单条链记录后通过。分别见`run-availability/stderr.txt`、`tests-final/stderr.txt`；没有真实工具失败、没有重试CALIBRATION转换或提高资源上限。索引生成曾报一个Python字符串转义SyntaxWarning，改为raw string后无警告；不影响执行结果。

实质任务全部串行，nice19/ionice-c3、systemd user scope **3G/200%**，启动前MemAvailable≥4GiB。持久采样最低MemAvailable **6543753216 B**，实读cgroup memory.peak最大 **473284608 B**（提交触发的Git自动打包；转换/测试scope最高107290624 B）；无OOM、暂停或资源终止。完整原文与各scope索引：[resource-summary.json](evidence/registration-checks/batch2/resource-summary.json)。短任务在scope内完成；长任务的通用runner每60秒保存meminfo，最终全量测试约90秒，已保存60秒时的meminfo，其余主要转换均不足60秒。所有新增证据文件<1MB，原始profile与临时Git夹具仅在`temp/registration-batch2/`。

边界例外：上下文恢复后曾执行一次未包装scope/nice的`pwd`来确认当前目录；它没有打开项目数据或创建文件。该探测不符合“所有命令包装”的字面要求，予以披露；之后的读取、修改、转换、测试及Git操作均使用指定包装。另在最后索引整理时，前一条写入脚本命令的完成状态尚未取回即发出了索引命令，随后分别确认两者均退出0；预提交检查发现manifest尚未生成，未暂存任何文件，确认写入完成后串行重跑索引并重新核验全部SHA；这不满足严格串行的确认流程，不能据此声称所有短命令均无重叠。转换、测试与统计任务没有并行，后续操作等待前一命令退出后执行。

提交时Git自动启动后台打包；暂停推送并监测到进程结束。它继承了3G/200% scope，记录峰值473284608B；原始资源记录见`git-autogc-monitor.json`。没有更改Git持久配置；后续本次提交修订与推送用命令级`-c gc.auto=0 -c maintenance.auto=false`避免再次启动自动整理。

### 9.5 更新后的Q.5状态与停止

|当前状态|编号|说明|
|---|---|---|
|已完成（13项）|1、2、3、4、5、6、7、8、10、13、15、20、21|本批完成5④、6剩余草稿/可用性、7/8/10；6的avg/prev-inst明确未尝试，不等于工具成功保证|
|部分完成（2项）|16、17|16仍待全部扩展身份条款核销；17本次披露已完成，历史总体披露/G0信息仍待齐全|
|未开始（6项）|9、11、12、14、18、19|未运行模拟、未接板，未登记修正案3|

完成后按要求停止，不开始其他Q.5项目；没有对正式矩阵profile进行读取、转换或计算，没有跨配置比较，没有改变资格判定。全部新增代码与证据由本报告所在提交封存，清单见[batch2 manifest](evidence/registration-checks/batch2/manifest.json)。

## 10. 第三批：合成avg、性能协议、离线资格与身份/披露核销（基线 c5ad459）

### 10.1 范围与第6项合成可用性

本批不接板，不重编Clang/llvm-profgen，不打开任何真实profile（包括CALIBRATION），不登记修正案3，不执行第9、12、18、19项。设计、C/U及旧资格标签均不修改。正式工具启动时核对SHA：2e8895afce661b5fdc8cacab2b3323496fca51af7bd7b51c3753aa8328b7d0d5。

[avg-plan.json](evidence/registration-checks/batch3/avg-plan.json)先列组合及设计依据：5.8第6条的avg与max/none基准，及最终推荐组合、5.9第2条对入选aggregation/skid组合的要求，因此同时核对avg/none和avg/prev-inst。复用第一批814859个指令起点的四份合成全地址文本，逐份SHA与batch1一致；只换aggregation与新输出路径，其余沿用第一批命令（sample、head=none、zero-fill=none、text）。没有对两个组合做质量比较或选择。

|对象|none / prev-inst 退出码|none写出条目|prev-inst写出条目|分类|
|---|---|---:|---:|---|
|spike-thumb|0 / 0|93|92|全部映射命中；未对齐0|
|spike-a32|0 / 0|92|91|全部映射命中；未对齐0|
|ffmpeg-thumb|0 / 0|83031|81017|全部映射命中；未对齐0|
|ffmpeg-a32|0 / 0|82287|80083|全部映射命中；未对齐0|

8次转换全部成功，无失败阶段；boundary_unavailable与known_out_of_scope均0。各目录conversion.json、classification.json及entries分片保存完整命令、真实退出码、输入/输出SHA与逐键分类。只解析键与条目数，不汇总body权重或计算质量比例。大输出保留temp/registration-batch3/，不会覆盖第一批、第二批或真实数据。

新[对象封存草稿](evidence/registration-checks/batch3/object-seal-draft.json)SHA为8cb026abe12fde4bcfae5225db41152090bc58ff44d9bfc5e4f2b0dd1ec991c0；新增synthetic_input_availability，旧历史可用性字段原样保留。它不是修正案3，也不能据此声称真实avg/prev-inst可用。第二批草稿不覆盖。

### 10.2 第11项：性能协议与不混用

实现registration_performance.py，23项synthetic测试通过。N由预试CV（四位有效数字）计算：min(40,max(10,ceil(2*(1.96*1.2533*CV/0.005)^2)))；无定义/非有限CV取40，非法负数拒绝。预试离群保留、正式N锁定、预热/预试不并入正式轮次。G0–G5参数、driver禁内联、stale/salvage、LTO一致性、小矩阵缺失交互说明、probe准入都有正负例。性能使用中位数相对差、独立percentile bootstrap 95% CI与±1%，不得替换质量配对统计、±0.01、区间类型或停止规则。这里只验证合成数据，没有产生真实N、性能组或性能结果。

### 10.3 第14项：离线资格及历史遥测重放

实现registration_telemetry.py与重放入口，新增61项synthetic测试；逐条包括完整单调窗口、端点/采样间隙、逐policy状态、校准有效区间与25点、忙碌率、MAD、kmsg序号/boot/时间边界/错误粘性、EAGAIN及非阻塞读取器。实际非阻塞管道用于验证drain，不打开板子或本机/dev/kmsg；保存失败不推进最后成功序号。板上降温后的正常对照属于第12项，仍未执行。

先写[遥测披露](evidence/registration-checks/batch3/telemetry-disclosure.json)、telemetry-before分片与telemetry-extra-before.json，随后按SHA核对并读取12480个遥测文件。路径、SHA、逐RUN原文依据均留存；未读取perf样本或任何真实profile。完整结论见[重放汇总](evidence/registration-checks/batch3/telemetry-replay-summary.json)及telemetry-group-differences-000.csv。

|旧标签→本批重放|组数|
|---|---:|
|clean→unknown|31|
|abnormal→unknown|20|
|abnormal→abnormal|8|
|unknown→unknown|11|

70组（106个物理RUN）为8 abnormal、62 unknown、0 clean；51组变化。逐组原因完整列在CSV，旧标签逐字节保持不变。8组有温度达到75°C的正面异常证据；unknown来自缺少四个单调端点、开机连续kmsg、cpuinfo频率和规定的前后四核30秒校准等，不能用其他RUN或墙钟猜测补齐。原异常标签只因旧总体有效频率而成立的，不自动继承为v1.8异常。

另重放既有单核/四核诊断：单核unknown；四核abnormal，最高80.341°C，scaling_cur_freq出现600MHz（也记录1.5GHz）。原始逐秒数据同时保留缺证据原因；不把“已观察到异常”误写成所有资格数据齐全。没有重新采集、修改资格阈值或据此进行配置比较。

### 10.4 第16项：扩展身份核销与同名范围外清单

原有身份、宏、完整清单与边界夹具保留，新加16项synthetic测试。完整清单覆盖核对不能以“有候选”代替结论，编译变体、外部CU来源及覆盖缺席是正面证据条件。23条扩展身份条文逐项指向新旧实现与具体测试，不重复放宽已有规则。

|对象|清单DIE|未决|顶层定义|同名范围外顶层|外部CU|
|---|---:|---:|---:|---:|---:|
|spike Thumb|17|0|9|0|0|
|spike A32|17|0|9|0|0|
|FFmpeg Thumb|28149|0|4630|0|10|
|FFmpeg A32|28190|0|4633|0|10|

[identity-audit-summary.json](evidence/registration-checks/batch3/identity-audit-summary.json)记录完整清单与来源SHA、封闭枚举分布和显式空清单。FFmpeg每侧10个外部CU包括5个GNU AS、5个GNU C，涉及38个DIE；沿用归档成员来源登记，不新增状态。identity_ambiguous是已有封闭结论，不等于未决。本批不重算静态身份或U。

### 10.5 第17项：历史总体披露

[完整披露表](17_profile_disclosure.md)新增历史汇总；批3CSV逐路径合并批2CALIBRATION，并给出元数据来源、SHA引用与历史计算量。扫描1759个仓库/保留日志元数据文件，汇总1139次转换尝试、616个profile路径；410个路径有保留的读取/哈希核对证据，其余只作保守的输出尝试披露，不声称文件实际生成或打开。扫描错误0。

历史包括补丁验证的字节/树/计数、真实avg三个热点的独立核对、第一轮转换层级报告、补丁9剔除无效调用点的重转比对，以及第二批CALIBRATION仅条目分类与退出码。这些历史量不在本批重算；来源日志中的SHA为引用值，未重新打开真实profile计算SHA。披露不能恢复未保留的操作记录，因此未知打开/生成状态显式保留。G0预试标为待第12项完成后补充，第17项仍部分完成。

### 10.6 逐条对应与当前Q.5状态

[72条对应表](evidence/registration-checks/batch3/clause-mapping.md)保留原文、设计行号、实现位置、具体夹具与结果；[校验索引](evidence/registration-checks/batch3/validation-summary.json)记录设计/工具/草稿SHA。原有§1/§9为历史快照，以本表为最新状态。

|项|状态|本批结果或剩余|
|---|---|---|
|1|已完成|沿用§1证据|
|2|已完成|第一批注入/准入契约|
|3|已完成|第一批派生负对照|
|4|已完成|第一批提交/canonical契约|
|5|已完成|第一批①②③、第二批④；本批不再打开CALIBRATION|
|6|已完成|静态封存草稿及历史报告；本批补8次合成avg可用性|
|7|已完成|第二批M1/M2 synthetic|
|8|已完成|第二批覆盖合并synthetic|
|9|未开始|模拟不在本批范围|
|10|已完成|第二批统计/协议/恢复门禁synthetic|
|11|已完成|本批23项性能协议synthetic|
|12|未开始|需板上验证、G0预试；本批不执行|
|13|已完成|第一批主FileID/lcov/JSON范围核对|
|14|已完成|本批离线实现、61项夹具及已有遥测重放；不替代第12项|
|15|已完成|沿用静态表/门槛证据|
|16|已完成|本批扩展条款核销与全清单审计|
|17|部分完成|历史与CALIBRATION已汇总；G0待12；无证据的历史打开状态保留未知|
|18|未开始|不进入本批之外项目|
|19|未开始|未登记修正案3|
|20|已完成|沿用v1.8全部新增夹具证据|
|21|已完成|沿用已有条文与证据|

合计16项完成、1项部分、4项未开始，不表示整体可登记。

### 10.7 测试、资源与边界

正式验收510项全部通过，原410项测试文件逐字节不变，新增100项（性能23、遥测61、身份16）。原文tests-acceptance/stderr.txt。没有变更设计、LLVM代码、正式工具、静态C/U/权重或三个用户配置文件。仅新合成profile被解析，未计算M1/M2、质量比例、正式RUN受控量。

记录的最低MemAvailable为17274179584 B，实读cgroup memory.peak最大616714240 B。没有OOM、资源暂停或终止。完整资源索引见[resource-summary.json](evidence/registration-checks/batch3/resource-summary.json)。

所有shell命令使用nice19/ionice-c3与3G/200% scope，实质转换/审计/测试任务经启动门禁并保存资源；短编辑/读取scope未逐一持久保存启动检查与峰值，因此不能声称该最低值覆盖每个简单命令及所有采样间隔。这是本批资源取证不完整之处，未提高限额。

失败保留：最初avg计划输出目录尚未创建（工具未运行，setup-failure.txt）；初版遥测读取器误把after.txt当数字命名快照，退出1（telemetry-replay/stderr.txt），修正输入选择后重放成功；两次编排层JavaScript字符串解析错误发生在shell启动前，无任务执行或文件变更。未隐藏真实转换失败或原样重试OOM。

新增证据均小于1MB；大输出在temp/registration-batch3/并由conversion.json登记路径/SHA。完成后停止，不进入第9、12、18、19项，不登记修正案3。

## 11. 第9项模拟运行前封存

场景、种子、代码及共用统计模块SHA见[07报告](07_interval_simulation.md)。150行逐项矩核对通过；新增24项夹具，共534项通过。第9项由未开始改为部分完成（先推送清单，再试跑估时）；其余项目状态保持§10不变。未登记修正案3、未读取任何真实profile。

### 11.1 试跑完成，正式模拟因12小时门槛未启动

清单提交6946344b0fae4c8e851fb71d1abd46abcca71029已先推送。150行各10000次t估时与一次完整包络计时完成，耗时698.759秒；正式预测35.500648小时（t 13.158279、包络 22.342369），超过12小时，因此未开始正式重复。quality_equivalence_enabled=false是未完成准入状态，不是某场景统计不通过，也不计入完整运行结果合取。逐场景耗时、SHA及正式未运行状态见07报告§5–7。测试534项通过；未读真实profile或登记修正案3。

|最新状态|编号|
|---|---|
|已完成16项|1、2、3、4、5、6、7、8、10、11、13、14、15、16、20、21|
|部分完成2项|9（正式模拟未运行）、17（G0待12）|
|未开始3项|12、18、19|

按时间门槛停止，不进入其他项目。

### 11.2 新裁决与两阶段执行准备

解除12小时门槛，单进程3G/100%。原6946344锁与统计代码不变；新增调度入口先验证并推送。第一阶段122个验收场景完成后先推送结果与开关，再执行第二阶段150行包络。第9项仍部分完成，正式结果待填；不进入其他Q.5项目。新增24项synthetic调度夹具，合计558项通过，证据simulation/phased/preflight-tests/。

### 第9项 acceptance阶段完成

122个验收场景完成，结果先推送再开始包络；第9项仍部分完成。 开关=true。详见07报告第6节。未登记修正案3。

### 第9项 envelope阶段完成

150行包络与报告完成，第9项已完成。Q.5为17项完成、17部分、12/18/19未开始。 开关=true。详见07报告第6节。未登记修正案3。
