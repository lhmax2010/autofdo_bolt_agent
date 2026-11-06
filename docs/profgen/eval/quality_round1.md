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
