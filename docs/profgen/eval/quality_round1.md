# 第一批统计质量分析：参考与工具验收已准备，最终矩阵未启动

以下前轮记录保留；最新状态见末节。本轮没有执行最终统计质量分析。用户要求使用最终工具；非叶子line0已证实会写入伪调用点，补丁9已实现但重构建门禁未满足，因此不能把补丁8矩阵当成最终结果。本报告逐项区分已完成准备与尚未执行指标，不用0或“等价”代替未知。

## 输入与资格

已保存70逻辑组/106个S原件、14份分stage profdata，setup已排除，输入与SHA沿用报告12。频率诊断首个a类用户态有效频率1.404GHz<1.455GHz，按预注册停止，不生成修订2。第一轮仍为31 clean/28 abnormal/11 unknown；FFmpeg clean为0。本轮的FFmpeg仅能保留全量、资格未定的描述，不能形成新干净子集。

## 已完成：独立于sample工具的参考准备

使用GBS平台Clang22.1.8、原spike源文件和原S编译flags，Thumb/A32分别加真实R profdata、`-mllvm -disable-preinline`，转储`pgo-instr-use`之后的IR。两次编译均exit0、无告警，每份一个完整module dump。候选`-print-before=inline -print-module-scope`也编译成功，但每ISA输出13次dump，尚未与sample侧配对比较，不宣称改善、不采用候选点。[命令、源/profile SHA、诊断](../impl/evidence/16/01_reference_ir_preparation.json)

对R参考自身运行既有保守语义匹配器，仅作为结构读取检查：

|ISA|条件终结指令数|自比严格配对|两侧比例|原因分类|
|---|---:|---:|---:|---|
|Thumb|22|3|13.6364%|unknown_weights1、unsupported_call1、load6、phi5、predicate5、type1|
|A32|22|3|13.6364%|同上|

这些不是IP配置的实际严格匹配率或概率误差结果，也没有证明候选点比原点更优。自比的低比例提示95%结构覆盖有明显风险；没有放宽操作数白名单、作用域/内联链/后继位置或重复键规则。[结构结果](../impl/evidence/16/02_reference_structure.json)

C参考方面：平台eu-unstrip合成运行文件与匹配debug，再用真实C profdata进行llvm-cov export。Thumb/A32 spike各11个函数、11个函数有执行计数，JSON有效；不是以单独debug替代含运行字节的对象。[覆盖参考](../impl/evidence/16/04_spike_coverage_reference.json)

libavcodec Thumb C对象合成后，`llvm-cov export`在3GiB/200%scope内被OOM终止：外层exit143，scope Result=oom-kill，输出0字节。未提高限额、未原样重试，未把空输出作覆盖结果。首次worker来不及保存汇总，两份已产生的spike JSON保留，随后仅对小spike重新导出确认并保存真实退出码。[scope原文](../impl/evidence/16/03_coverage_scope_oom.json)。A32/ToS的FFmpeg覆盖导出未启动。

## 描述性旧工具输入盘点（不是最终质量结论）

下表仅汇总报告12的补丁8质量JSON，用于明确已有输入的范围；补丁9重转未完成，不将它用于筛选配置。

|变体|target|outside_dwarf_func|比例|分类|ISA比例|
|---|---:|---:|---:|---|---|
|FFmpeg Thumb|4,054,701|1,219,819|30.0841%|in_cu_no_subprogram1,217,478；plt2,341；no_cu0|Thumb99.9423%，A32 0.0577%|
|FFmpeg A32|550,478|159,276|28.9341%|in_cu_no_subprogram158,860；plt416；no_cu0|A32 99.9947%，Thumb0.0053%|

所有这些正式输入身份verified，不能因汇编/行表覆盖不足放宽身份规则。[盘点](../impl/evidence/16/05_patch8_input_inventory.json)

## 未完成项目与原因

|要求|状态|原因/后续依赖|
|---|---|---|
|spike aggregation×skid×weight、三档预算、全量/clean|未执行最终矩阵|等待补丁9正式工具；不使用旧结果冒充最终转换|
|两侧严格匹配率、概率误差中位数与分布|未取得|当前只有R侧及自比，不能用自比冒充两侧质量|
|bootstrap95%CI、质量ε±0.01判读|未执行|缺最终配置独立观测误差，不能称等价或显著差异|
|候选print-before=inline改善试验|仅取得R侧13次dump|需明确sample对应点并保留同样语义校验，未采用|
|libavcodec补零×head、行级召回/加权误差|未执行|补丁9待验收；C export受3GiB限制|
|函数热点覆盖/Spearman|未执行|依赖最终sample profile对齐，不能把C函数总数当相关系数|
|ToS泛化、BBB/ToS不应强判退化对照|未执行|同上；不推断ToS必然更差|
|固定种子扰动≥20次|未执行|缺最终指标基线，不以改计数后文件不同代替区分度验证|
|95%结构门槛|sample侧未核实|R自比13.64%仅提示风险，不放宽规则|
|BFI块计数指标|未核实|未试验，不用于结论|
|G1–G4候选配置清单|尚无可推荐项|缺统计判据，不预选默认聚合或head|

这些未完成项属于工具验收与资源依赖，不是宣布设计规则无法实现。补丁9通过后才能重转全部正式S并完成矩阵；FFmpeg覆盖需要在现有限额内找到经验证的较小导出办法，或由用户另行决定资源，不自行提高限额。没有新消费组构建或性能测量。

## 资源与待设计 v0.8 登记

本轮轻任务使用user scope 3GiB/200%，nice19/ionice3，串行。最低已保存MemAvailable=5,546,088KiB（5.289GiB）；没有触发全局连续<2.5GiB暂停或<1.5GiB终止。记录成功取得的最大RSS为500,516KiB；OOM任务精确峰值无法取得（scope回收后MemoryPeak=[not set]），不能用成功任务峰值代表OOM任务。发生一次scope内OOM，未触碰他人进程。重任务门禁只检查一次，不满足，未重试。[资源摘要与原文](../impl/evidence/16/06_resource_summary.json)

待v0.8登记：非叶子line0排除规则仍是待验收实现；记录频率判据的操作性停止与计时窗口局限，记录严格匹配器对本工作负载的结构覆盖风险，以及FFmpeg C覆盖导出的3GiB资源障碍。v0.7正文不改，不调整ε或语义校验。

## 本轮补充：按源文件导出（2026-11-06；已结束）

按用户新方案先验证Thumb spike：重新执行整体export，再按整体JSON列出的全部源文件逐一export，合并以filename及(function name, filenames)为键去重且要求重复对象相同。完整file对象（segments/regions/branches等）逐项相同，函数对象和计数相同，因此逐行执行计数及函数计数零差异。该spike实际只有一个源文件，11函数，119可执行行、109已覆盖行；不能将这个单文件结果冒充多源header去重的普遍证明。[命令、比对、资源及OOM原文](../impl/evidence/16/07_source_filtered_coverage.json)

随后对Thumb libavcodec C指定首个源文件/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/h264_cabac.c进行独立3G/200%scope export。仍发生OOM：scope Result=oom-kill，外层返回-15，输出为空。运行中观察到cgroup memory.peak=3221225472B、进程RSS=3168464KiB；结束后systemd显示的小MemoryPeak与运行中实读不符，二者原样留证，以运行中达到3GiB及oom-kill事实为准。不提高限额，不原样重试，不继续其他文件；没有生成可用的FFmpeg合并覆盖JSON。

spike两次成功任务子进程峰值RSS分别38928/38968KiB。候选解释为源文件过滤并未限制前置覆盖映射/计数加载内存，但本轮未定位实现，不把该解释当成已证实原因。大文件与执行脚本在temp/coverage-split-check/，对象仍在temp/quality-round1/。

本轮不开始最终质量矩阵、正式S重转或性能测量。待设计v0.8登记：源文件过滤方案在3GiB限额下不能导出这份libavcodec，后续需用户决定其他方案。

## 本轮最终状态：工具验收完成，不启动矩阵

补丁9已正式验收，新工具SHA-256为2e8895afce661b5fdc8cacab2b3323496fca51af7bd7b51c3753aa8328b7d0d5，LLVM本地提交15a5ec3f46283ad2eccaecf97b2eac2a0e43d65c，详见[报告15](../impl/15_patch9_nonleaf_line0.md)。本轮用户明确不重转正式S，因此原106份S及其质量报告仍是补丁8结果，没有将它们改标为补丁9。

覆盖分片方案在spike上逐行/函数计数一致，但libavcodec首文件仍3GiB scope OOM；频率诊断为unknown、资格未修订。最终质量矩阵、配置间CI、候选配置、消费构建及性能测量均未开始。后续需另行授权正式S重转及覆盖办法；不把工具验收通过当成统计质量结论。

## 补丁9正式S重转与整体覆盖导出（2026-11-09）

### 正式S：已完成，资格与配置不变

固定工具SHA-256为2e8895afce661b5fdc8cacab2b3323496fca51af7bd7b51c3753aa8328b7d0d5，启动前与收尾各核对一次。补丁8存档工具9f63c692及libLLVM只读、SHA未变；106份旧profile逐个与已登记SHA核对，全部保留。重转输出写入temp/p9-formal-reconversion/outputs/，不覆盖旧结果。

70逻辑组、106物理S原件全部按temp/board-round1-retry/final-reconverted.json登记的原命令执行，仅更换output和quality-report路径。原有20份频率模式period profile也保留其显式ip-period-unit=1000003参数重转，不计入106原件样本汇总第二次。每次转换使用独立user scope：MemoryMax=3G、CPUQuota=200%，串行、nice19/ionice3；没有OOM或转换重试。

|对象|物理原件数|移出usable的样本|profile有变化|
|---|---:|---:|---:|
|spike Thumb|28|0|0|
|spike A32|28|0|0|
|FFmpeg Thumb（含ToS）|45|2366|45|
|FFmpeg A32|5|370|5|
|合计|106|2736|50|

总target仍为11,131,603；usable从8,235,324降到8,232,588，差值正好2,736，与报告12独立统计一致。全部身份仍为verified；56份sample profile字节不变。额外20份period profile中10份不变，10份仅有相同排除带来的变化。[逐份清单](../impl/evidence/16/08_p9_reconversion_rows.json)、[汇总与存档SHA](../impl/evidence/16/08_p9_reconversion_summary.json)。

核对没有按字段前缀笼统放行：复用报告12逐地址、逐函数非叶子line0清单，从旧IP-ADDRESS诊断独立求移出sample_count与period_sum，逐项重算新计数、比例、函数coverage排序和份额。所有其他JSON字段必须相同；top50数组中的name位置变化仅来自扣除后重新排序。profile解析为函数/调用点树，删除仅发生在已登记zero-line父函数下的wrapped调用点（例如63616、65068、65117）；删除其空祖先后，保留body和全部其余节点精确相同，所有顶层total差值又与独立逐函数样本数一致。written_positions的减少由剩余树重算，不放宽为任意减少。

period涉及每键一次取整，未采用±1容差：按平台readelf可执行PT_LOAD与旧清单地址，从派生文本中仅删除已知异常样本；原始全文不变，MMAP与其他记录保留。只读补丁8存档工具对该派生文本使用同样的显式period单位生成参考，参考与新工具原始全文输出逐字节一致。这个辅助参考不是新增采集或最终配置矩阵。

完整JSON差异分片：[01](../impl/evidence/16/08_p9_differences_01.json)、[02](../impl/evidence/16/08_p9_differences_02.json)、[03](../impl/evidence/16/08_p9_differences_03.json)、[04](../impl/evidence/16/08_p9_differences_04.json)、[05](../impl/evidence/16/08_p9_differences_05.json)、[06](../impl/evidence/16/08_p9_differences_06.json)、[07](../impl/evidence/16/08_p9_differences_07.json)。每份均为unexpected空；变化只包括nonleaf子计数、相应归类/比例/coverage、移除无效调用点及其派生total/空上下文/位置数、输出路径。

比对器首次在第10份停止：错误地保留了被删除调用点上方的空内联上下文。保留原stderr及失败状态，依据实际diff修正只清除total=0且无body/calls的空祖先后，精确比较通过。工具未失败、未重新转换该原件；这不属于允许差异范围的扩张。[核对脚本全文、修正记录与每份原件SHA](../impl/evidence/16/08_p9_reconversion_method.json)。

原31 clean / 28 abnormal / 11 unknown保持不变；没有重判资格、合并分段profile、最终质量矩阵、消费构建或性能测量，也没有连接开发板。

### 整体覆盖：按后续裁决立即执行，已完成

用户16:31的新指令将等待窗口替换为立即门禁10GiB、scope 8G/200%。原等待程序尚未启动任何export；仅终止本任务旧等待scope，确认inactive，保留“已结束 / 未开始 / 用户裁决替代”记录。INT因后台继承忽略未使其结束，随后TERM使该等待scope退出；这不是资源门禁终止，也没有终止他人的进程。原10G导出方案从未执行。

16:32:28首门禁MemAvailable17,174,056KiB，立即通过；16:32:42第二门禁16,752,632KiB通过，不检查SwapFree。两份整体export各执行一次，串行，独立MemoryMax=8G/CPUQuota=200%scope，nice19/ionice3，无源文件过滤。runtime/debug都经报告11登记SHA验证，GBS eu-unstrip合成对象build-id分别为Thumb 07d083e754ba0c5162c08fc054644807bc140a8f、A32 b262c36697a0957d48c691b1bcad8b0517465741。引用对应train-ffmpeg-thumb-C/a32-C.profdata，未混入setup、G5或ToS数据。

|对象|exit|export耗时|scope总耗时|运行中cgroup memory.peak|export子进程峰值RSS|文件数|函数实例记录数|可执行行|已覆盖行|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|FFmpeg Thumb C|0|8.025秒|13.668秒|4,643,598,336B（4.324688GiB）|4,190,164KiB|498|28,236|112,206|8,298|
|FFmpeg A32 C|0|6.674秒|12.059秒|4,587,786,240B（4.272709GiB）|4,179,876KiB|498|28,236|112,206|8,298|

cgroup memory.peak为运行时实读，包含scope内存及计费缓存，不等同于单进程RSS；RSS另由wait/rusage取得。结束后systemd的MemoryPeak显示not set，因此不能用它替代运行中已保存的峰值。memory.events的oom、oom_kill、max均为0。两份JSON均完整解析成功（llvm.coverage.json.export 3.1.0），各306,634,391B；校验进程峰值RSS分别1,844,916/1,844,656KiB，也在同一8G scope内。

函数实例记录数是data[].functions的条数，对应totals.instantiations.count=28,236；llvm-cov去重后的totals.functions.count另为3,575、covered=385，两者不得混称。行数为各文件summary.lines之和，并与totals.lines一致；不作跨ISA准确率或最终质量比较。

- Thumb SHA-256：e96a2d43ec475556cde0508a3eac7ba9edfab5fc911edaceb088fd8c8f01b402。
- A32 SHA-256：4a4c9970acba0c0c064fb923836be41781774053bd6ade27f900571a0529730a。
- 原始JSON：temp/coverage-whole-8g-20261109/thumb.coverage.json、a32.coverage.json；命令、stderr、版本、对象/profdata SHA与日志均在同目录或准备目录temp/coverage-whole-20261109/。仓库只留[完整执行摘要与峰值证据](../impl/evidence/16/09_whole_coverage_8g.json)。

等待与导出日志均有“已结束”、时间、状态；最终16:32:54成功。单份运行不足60秒，所以各有开始/结束完整meminfo记录，未到下一次60秒采样周期；监测代码仍按每60秒和连续两次<3GiB终止自己的scope实现。全流程已保存资源采样最低MemAvailable16,528,896KiB（15.763184GiB），这是采样最低值，不声称是每个瞬间的系统最小值。没有资源触发的暂停或终止、没有OOM/重试。[资源摘要](../impl/evidence/16/10_reconversion_coverage_resources.json)，其中保留全部观测时间/数值及初始、最低和覆盖任务的原文；每次完整meminfo原文留在摘要列出的temp JSONL中，并记录SHA。

执行顺序说明：前一条任务授权下，正式S重转在15:20已全部完成；后续16:31指令到达时只剩等待。新指令生效后先结束旧等待，再完成两份覆盖导出，最后复核106+20份新结果/旧profile与固定工具SHA，没有重复转换、没有两部分并行。无需把已完成的授权工作撤销或重做，原执行时间如实保留。

### 待设计v0.8登记

补丁9在正式S上精确排除2,736条非叶子line0样本，原质量资格不变；相关比例与profile内容须使用这套新结果，不能将补丁8旧结果改标为补丁9。覆盖的立即门禁与8G/200%限额是后续执行授权，不改变质量判据或冻结设计正文。
