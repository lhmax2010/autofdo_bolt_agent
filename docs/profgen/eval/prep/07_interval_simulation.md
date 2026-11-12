# 第9项：区间模拟与运行前封存

## 1. 范围与运行前登记

基线3ace1cb；设计v1.8 Q.5第9项（2150行）、5.8第6条（558–575行）。只用synthetic差值，不读任何真实profile，不接板，不登记修正案3。

场景逐行清单：[scenarios.md](evidence/registration-checks/simulation/scenarios.md)，机器清单：[scenarios.json](evidence/registration-checks/simulation/scenarios.json)。固定150行：A1 80、A2 20、A3 16、A4 2、A5 4、B1 24、B2 2、B3 2。场景不在运行时扩展；各族按各自适用矩阵列出，A2无方差比16。B1两种结构均报告，各阶段同参数；A1两阶段r=16与1/16分别表示小阶段/大阶段方差更大。固定的5+10仅为本次模拟结构，不声称真实RUN槽位已经登记。

ε=.02，单阶段15/两阶段5+10，λ=n/15。清单逐行含分布参数、Δ、阶段真实均值/方差、方差比、实际SE/ε、t与包络重复数、固定种子。每个场景的一个整数种子供t抽样；包络独立流为该种子的十进制文本追加“:envelope”，规则与实际字符串均封存。内层bootstrap仍用共用模块固定seed=20261104和20000重采样，不改参数。A1按设计闭式方差解；B1按lognormal解析矩定尺度与平移；A5校验λ₁×a×.15=Δ。启动时逐行重算解析矩、检查清单、SHA和已推送blob；不可行参数先报错。

判定规则（用户原文）：

> t 单独的覆盖率 ≥ 93%；Δ 为 ±0.02 与 ±0.03 时，t 单独的判等价比例 ≤ 3.0%；A4 必须 100% 退化、0% 判等价；退化重复按“不判等价、覆盖为真”计。quality_equivalence_enabled 取全部验收场景都通过且全部运行完整时的逻辑与；任一场景不通过或未完成，即为 false。

正式A场景每行1000000次t验收；全部150行各10000次包络，报告t、percentile和包络，B仅报告。退化始终覆盖为真、等价为否，比例分母不删除退化。标准误为sqrt(p*(1-p)/R)。不完整时有效开关为false，但按设计不把执行失败计入完整运行结果的统计合取；任何一次完整运行false永久保留。不得把统计验收未达标说成执行失败。

## 2. 实现、共用路径与SHA

新增tools/profgen_eval/interval_simulation.py。所有区间与退化直接调用第二批registration_statistics.stratified_t / intervals_joint；未改共用模块，也未另写统计区间、退化或bootstrap实现。模拟器只负责生成分布数据、计数事件、MC标准误、门禁与记录。

[prerun-lock.json](evidence/registration-checks/simulation/prerun-lock.json)封存以下文件。正式/试跑前必须在origin/main中逐字节找到同SHA的锁与各文件，否则拒绝。后续只更新报告和结果，不修改锁定文件。

|文件|SHA-256|
|---|---|
|tools/profgen_eval/interval_simulation.py|eaf7055d4d9d18e4a137df9726481ba0def399e0fd6e158d2826a80895f24a98|
|tools/profgen_eval/test_interval_simulation.py|8f9dcab017b75e179c94cb060817f4d08bde2f786f5e6d9178c769bf59468f08|
|tools/profgen_eval/registration_statistics.py|2815e458c1a2cc791d902572fb87072003a968faed4a086131083ebe3b2feb12|
|docs/profgen/eval/prep/evidence/registration-checks/simulation/scenarios.json|9490e762d4d1b8ac36f2f4980ed7740bf2a548d1889a031fd0343ffcd1b329ad|
|docs/profgen/eval/prep/evidence/registration-checks/simulation/scenarios.md|4757b669ec025854ca07870f69a258edeeb118ce5bc7f42b3059c28fb95f7437|
|docs/profgen/design/02_llvm_profgen_enhance_design_v1.8.md|ae667bd61470118179f6876c912285b7c57ab22518640c2af9f42103ad428e59|

新增24项synthetic夹具，原510项保留，合计534项通过。包括缺行、false后true仍false、A2方差比16拒绝、A5真实均值、A4严格退化、验收边界、矩/种子/重复错误、共享调用路径。证据prerun-tests/；全部150行解析矩校验通过，证据prerun-moments/。这些是小夹具与解析校验，不是正式模拟重复。

## 3. 试跑估时与正式执行方式（先推送再启动）

试跑每场景10000次t调用，只保留耗时，不保留其覆盖/判等价统计为结果。另对每行用独立包络流计时一次完整的共用模块包络调用（内部20000次重采样），用于估算额外的10000次包络成本；不减少正式重复、不改变统计实现。总估时为所有行t计时×正式次数/10000，加包络计时×10000。超过43200秒停止，正式入口也验证估时文件与清单SHA并拒绝启动。

资源：单进程、串行、nice19/ionice-c3、systemd user scope 3G/200%；启动MemAvailable≥4GiB。实时进度每秒更新，每60秒保存meminfo；从cgroup读取memory.peak。每完成一个场景，追加JSONL、fsync并记录SHA链；中断后只跳过完整且参数/种子/SHA核验通过的场景，未完成场景从同一固定种子重跑。最终ALL-END保存时间、完成/失败/中断、已完成数和资源。运行中不改代码或清单。正式结果及完整运行合取账本位于temp/interval-simulation/。

启动命令（先确认本节清单提交已推送）：

    TMPDIR="$PWD/temp/tmp" PYTHONDONTWRITEBYTECODE=1 nice -n 19 ionice -c3 systemd-run --user --scope -q -p MemoryMax=3G -p CPUQuota=200% python3 tools/profgen_eval/interval_simulation.py pilot --out temp/interval-simulation/pilot

满足12小时门槛后，formal命令仅把pilot改为formal，并使用新的temp/interval-simulation/formal-001输出目录。两阶段不得同时运行。进度为相应目录progress.json；每次恢复的end.jsonl追加保留。

## 4. 当前状态

运行前封存已准备；尚未试跑或执行正式重复。当前没有统计验收结果，quality_equivalence_enabled不启用。清单提交与估时/结果将在下一阶段追加。
