# RPi4 第一批评估预注册修订 1：有效频率与节流可观测性

原预注册 commit `7d3d9d9f9184bc2e0e2b94a479916a2d65f13463` 及其文件保持不变。本文件单独提交并推送后，才恢复板上采集；Git commit 时间是修订时间。依据用户本轮明确裁决。本修订发生在任何配置间质量/性能结果比较之前；已开展的 Thumb/A32 line 0 排查属于调试信息诊断，不作配置收益或质量等价结论。

## 1. 理由与已有数据

该板未发现可读的固件节流状态节点，原判据将节流未知的所有轮次排除，干净子集恒为0。改用同一负载树的硬件cycles及CPU时间测得的有效频率，联合固定频率读数和温度，判断“未观察到节流”；这不是证明电源/固件历史节流位为0。

修订时已有7份正式采集，原件不覆盖，不与9份校准/流程原件混合，均位于 `temp/board-round1-resume2/runs/`：

| RUN后缀（前缀formal2-） | target样本 |
|---|---:|
| spike-thumb-S-sample-fixed-bbb-20000-r1-s1 | 21561 |
| spike-a32-S-sample-fixed-bbb-20000-r1-s1 | 21347 |
| ffmpeg-thumb-S-sample-fixed-bbb-20000-r1-s1 | 36155 |
| spike-thumb-S-sample-fixed-bbb-100000-r1-s1 | 106875 |
| spike-a32-S-sample-fixed-bbb-100000-r1-s1 | 106567 |
| ffmpeg-thumb-S-sample-fixed-bbb-100000-r1-s1 | 108145 |
| spike-thumb-S-sample-fixed-bbb-400000-r1-s1 | 426661 |

6份有补丁7的sum profile/质量报告，第7份尚未转换。没有完成多重复配置比较，没有选择默认策略，没有消费构建/性能收益比较。

## 2. 固定判据与具体计算

1. 每轮开始及结束，逐policy记录 governor、scaling_min_freq、scaling_max_freq、scaling_cur_freq；每秒继续记录各CPU当前频率和thermal。开始前performance已设置。RPi4当前所有CPU属policy0；固定频率 `f_fixed` 取该轮开始前policy的scaling_max_freq ×1000（单位Hz）。要求结束时边界与起始一致。若未来出现不同频率policy，本流程停止并报告，不把不同CPU的频率盲目平均。
2. 每轮用 `perf stat -e cycles,instructions,task-clock -x ';' -o <RUN>/perf-stat.csv -- <同一负载命令>` 记录精确计数。S录制在外层 `perf record --buildid-mmap ... -- perf stat ... -- <负载>`；stat计数对象为负载启动进程及其继承的子进程，不含外层record进程。多次完整解码用同一负载launcher循环，cycles和task-clock均覆盖同一进程树与同一时段。R/C/G5同样由stat包住负载，LLVM_PROFILE_FILE仍按stage分离。
3. `C` 为stat的硬件cycles计数，`T_ms` 为同一stat的task-clock毫秒数；`f_eff_Hz = C × 1000 / T_ms`。用十进制定点/有理数计算，不从屏幕截短的小数反推。task-clock按线程/子进程累计CPU时间，不能用墙钟real、整台板uptime或进程组外的CPU时间替代。计数/时间缺失、非正值、`<not counted>`、`<not supported>`、counter运行比例不是100%或无法确认无multiplex时，结果unknown；不以频率采样period和或“样本数×period”冒充精确cycles总量。
4. 同时满足以下三项时标为**未观察到节流**：`f_eff >= 0.97 × f_fixed`；负载轮次的所有逐秒 `scaling_cur_freq` 读数等于固定值；所有CPU/SoC温度低于原阈值75,000毫摄氏度，且传感器有效。当前固定值若仍为1,500,000kHz，则下限为1,455,000,000Hz。温度/频率样本缺失、policy记录矛盾或stat数据无效时为unknown。低于97%、频率偏离固定值或温度达到原阈值则标异常；不放宽阈值。
5. 读不到固件节流节点仍保留原始`throttling_node=unknown`，但不再仅因这一项将满足第4项的轮次剔除。其它异常判据（换出≥4MiB、无效温度、身份、内核、SHA及退出码等）继续适用。换出页大小在采集前只读取一次并留证。不得将“未观察到节流”缩写为“确认从未节流”。
6. 全部轮次和去除异常/unknown的子集均保存。重复不足仍为证据不足，不为了填满子集丢弃原始轮次。

## 3. 已有7份的同规则判定

这7份缺采集前policy边界；依用户裁决，允许依据已有逐秒读数和有效频率判定，但不补造起始记录。逐秒当前频率均为1,500,000kHz、温度低于75°C、pswpout未增加；**没有同期perf stat硬件cycles总计数及与其配对的task-clock**。evlist有采样period与read_format，不能据此声称已经保存精确总计数；没有sample_type READ值可代替。

因此7份节流资格都保持 **unknown**，干净子集仍为0。原始数据仍可用于功能、地址、行表和profile生成验收；不能将它们当作已通过本修订的干净统计重复。该结论在修订时写定，不因随后profile结果调整。

## 4. 保持不变

性能ε=±1%、质量ε=±0.01、三档target预算20k/100k/400k、每配置每档至少5次独立采集、频率中档5次、bootstrap独立重采样/seed20261104/20000次、训练与测试输入、异常换出/温度阈值、原始数据保留、身份与空间停止条件均不变。修订不改变冻结IP解析/计数规则，不授权修改内核/驱动或系统sysctl。
