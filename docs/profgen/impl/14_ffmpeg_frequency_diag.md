# FFmpeg 有效频率诊断：资源启动门禁停止记录

本轮在连接开发板及启动诊断、编译、profile转换或统计分析前停止。连续三个检查点的MemAvailable低于8 GiB启动门槛，按用户“资源上限被触发两次以上”停止。这是**同一次持续低内存状态的三次观测**，不是三次独立压力事件；没有启动后被终止的计算任务。

## 资源限制与证据

所有主机命令由`nice -n 19 ionice -c3`包裹。长期任务原拟在可用时使用`systemd-run --user --scope -p MemoryMax=16G -p CPUQuota=600%`，编译/GBS上限`-j6`，分析单进程；启动门禁未通过，因此未探测scope或启动构建。监测之间等待60秒，实际观测间隔包括工具调用开销。

低优先级Python读取`/proc/meminfo`与`/proc/loadavg`；初始命令为`cat /proc/meminfo`。原文见[资源证据](evidence/14/01_resource_gate_stop.json)。第一次时间为初始输出落盘时间，不冒充精确读取时刻。

|检查|时间（+08:00）|MemAvailable KiB|GiB|动作|
|---|---|---:|---:|---|
|1|2026-11-06T16:44:21.083701+08:00|5,992,092|5.715|暂停新任务|
|2|2026-11-06T16:45:32.806181+08:00|6,087,040|5.805|暂停新任务|
|3|2026-11-06T16:46:52.222715+08:00|6,602,928|6.297|暂停新任务|

可用内存范围5.714–6.297 GiB，未低于4 GiB。轻量监测进程记录的最大RSS为11,780 KiB；未运行的诊断/编译/分析没有资源峰值，不能以监测RSS替代。初始进程列表观察到另一工作目录的GBS下载进程；没有访问其项目文件或结束他人进程。

## 板上诊断与资格判定

未执行sdb，未读取板子当前状态，不能判断镜像、内核、total_mem、回收程序或vm参数是否与第一轮相同。没有频率、utime/stime、缺页或回收增量新数据，不作“测量口径问题”或“疑似真实降频”判定。本轮未改变governor/root，无需恢复；旧报告的恢复状态不能当作当前新测结果。

未开始诊断采集，`preregistration_amendment2_rule.md`尚未创建/提交，修订2未生成。恢复时须先按用户要求原文登记并推送判定规则。原预注册与修订1不变；资格仍为31 clean、28 abnormal、11 unknown，FFmpeg clean为0，未重判。

## 非叶子line0与统计质量分析

未开始新的实现核实，不能判定是否需要补丁9；没有改LLVM或生成0009。已有2,736条非叶子line0统计不是对本轮调用点键问题的答案。工具仍为补丁8的`9f63c692a4239a222bfb86cd9dcab93b04a28fc32421306b597f4c799627fdc7`。

统计分析未执行：严格匹配率、概率误差、配置间CI、泛化、扰动负对照、候选配置均无新结果。不生成空白补丁9/质量报告冒充交付；恢复后按原要求继续，不放宽语义校验或资格阈值。

## 待设计 v0.8 登记

无新增设计裁决；用户授权的非叶子line0处理方案尚未核实/实现。登记资源约束及启动门禁停止事实，不修改冻结v0.7正文。

边界例外：无新增；未连接板子。下一步等待资源恢复及继续指示，三个部分均未宣称完成。


## 恢复轮：分级资源门禁与预注册（2026-11-06）

上一节为历史停止记录，保留。最新授权以轻任务≥4GiB/3G/200%、重任务≥10GiB且SwapFree≥1GiB/16G/600%替代统一门槛。user scope探测成功，所有执行由nice19/ionice3包裹；各轻任务串行、长诊断每60秒保存完整meminfo，未启多进程分析。实际scope及原始资源见[02](evidence/14/02_scope_and_baseline.json)、[06](evidence/14/06_resources_and_restoration.json)。没有满足重构建门槛，未启动GBS或lit。

判定规则原文在任何诊断采集前单独提交并推送`5219d15`：[preregistration_amendment2_rule.md](../eval/preregistration_amendment2_rule.md)。这是条件规则登记，不是已采纳修订2；原预注册与修订1未改。

### 已完成：板子身份和状态核对

初始sdb devices为空；对已授权IP进行一次connect成功后只有一个设备。型号Raspberry Pi 4 Model B Rev1.5、armv7l、6.12.80-arm-rpi4-v7l；uname-v仍为`#1 SMP Wed Nov  4 17:05:36 UTC 2026`，/proc/version无PREEMPT字样，但不能由此确定全部抢占配置。镜像BUILD_ID为`tizen-unified-toolchain_20261104.160709`。镜像到QB1218764/1218766的对应关系没有板上证据，保持未知。

boot未挂载，使用root只读od读取/dev/mmcblk0p1的FAT16目录与config.txt簇，未挂载、未写分区；全文留证，存在`[all] total_mem=1600`。MemTotal=1,507,996KiB；resourced.service active/running(PID399)，reclaimd.service not-found且未见reclaimd进程。resourced配置ReclaimAtBoot=yes、SwapType=zram、ZramRatio=0.4；实际zram0为lzo-rle、disksize617,676,800B，swap容量603,196KiB，不符合“65%且关闭resourced swap”的类产品基线描述。

vm：swappiness60、page-cluster3、min_free_kbytes3388、watermark_scale_factor10、vfs_cache_pressure100、lru_gen/enabled=0x0001；KSM run节点不存在。/proc/config.gz及/boot配置不可得，HZ/具体抢占配置未知；getconf CLK_TCK=100是用户态计时单位，不能冒充内核CONFIG_HZ。

与第一轮可比项：镜像文件和/proc/version逐字节相同，内核构建串相同，MemTotal换算仍1472MiB，zram swap容量相同，resourced仍运行。第一轮未留config.txt全文、vm参数、zram算法及resourced配置，故这些项**无法证实是否相同**，没有将unknown写成相同，也没有发现已证实的配置差异。不得将本轮结果与第一轮无条件混用。非root ps遗漏root进程，后续root读取及systemctl确认了resourced，不把权限可见性当成进程消失。[状态原文与比较](evidence/14/03_board_state.json)

### 已完成：首个a类诊断；按规则停止后续运行

原管道为BBB720p→qtdemux→h264parse→avdec_h264 max-threads=1→I420→FIFO filesink，checksum读端同第一轮。先完成29项非root依赖、root部署SHA与perf版本验证，再固定performance；未修改sysctl/内存/回收设置。a类使用cycles -c1000003 record包裹stat(cycles:u,cycles:k,instructions:u,task-clock)。目标maps与buildid-list匹配。命令、真实退出码、全部遥测及SHA收据见[07](evidence/14/07_run_raw.json)，所有大文件保留temp/frequency-diag-resume/runs/ff-a-1。

|量|结果|
|---|---:|
|cycles:u / cycles:k|39,447,297,758 / 8,378,402,319|
|用户/内核CPU时间（目标进程time）|28.096s / 6.438s|
|task-clock|33.66242s|
|用户态有效频率|1.404018286GHz（固定频率93.6012%）|
|总体有效频率|1.420744560GHz|
|内核CPU时间占比|18.6425%|
|目标墙钟|60.847s|
|逐秒scaling_cur_freq|全为1,500,000kHz|
|温度范围|60.861–67.192°C|
|pgfault / pgmajfault增量|699,772 / 1|
|pgscan / pgsteal / refault / pswpin / pswpout|所采各项增量均0|
|kswapd0、resourced CPU ticks增量|均0|

`/proc`每秒保存目标及其全部当时存活线程的stat；最后观察到的minflt/majflt/utime/stime逐线程留在[05](evidence/14/05_diagnostic.json)，进程退出后路径消失，不能把最后一次轮询冒充精确退出值。用户CPU时间采用目标命令自身的bash time，不包含外层perf的CPU时间。user+sys=34.534s与task-clock=33.66242s存在0.87158s口径差，不能归因于真实硬件降频；本轮没有回收活跃证据，不能把频率偏低解释成reclaimd或kswapd导致。

**校准计时局限**：初版脚本外层time包住taskset/perf，包含perf启动/收尾，cycles只统计工作负载，两者窗口不完全相同。下表保留原始比值，但不将其称为纯计算实际频率或独立降频证据。cycles/task-clock均约1.500GHz，说明需区分时间窗口；严格绑核纯循环墙钟校准仍未完成，不在触发停止后改口径重采。

|CPU|前：cycles/外层墙钟 GHz|后：cycles/外层墙钟 GHz|
|---|---:|---:|
|0|1.416230|1.400492|
|1|1.439936|1.447185|
|2|1.442666|1.446620|
|3|1.446916|1.444369|

即使不使用上述有局限的校准值，a类FFmpeg用户态频率1.404018286GHz已低于预注册1.455GHz，独立触发“疑似真实降频”分支。它是预注册操作性判定，**不是已证明物理降频**。不生成修订2、不重判第一轮资格；b类、spike对照和其余重复未运行，不能声称完成9次诊断。后续性能测量等待用户处理；候选后续核实为对齐校准cycles与纯循环墙钟窗口、核对用户态CPU计时与PMU事件口径，本轮不实施改变判据。

### 已完成：清理、恢复和资源记录

首个RUN采集/导出退出0；全部文件SHA核验及远端清单复查后删除确切RUN目录。诊断worker执行100.359s（RUN含拉回87.550s），因判定停止写ALL-END FAILED，未伪装全矩阵成功。root恢复off(uid5001)、policy0=schedutil、RPM1232不变；/opt收尾used295120KiB/available1010496KiB，后续只读状态另留证。无SDB缺码重试、无资源暂停/终止；worker监测RSS17,528KiB，完整样本见06，原始数据仍在temp。未改板上配置，保留诊断脚本供复核。

### 待设计 v0.8 登记（恢复轮）

按用户预注册规则记录疑似真实降频，不将固定scaling_cur_freq当作实际频率证据，也不把有开销的校准比值当作纯循环频率。记录缺失历史状态及计时窗口局限。分级资源规则已生效；板上停止后仅继续不依赖FFmpeg资格的主机核实。非叶子line0及统计分析进展在后续阶段记录，冻结正文不改。


## 本轮最终分项状态

|部分|状态|证据/限制|
|---|---|---|
|频率诊断|首个a类运行后按预注册停止|已恢复root/governor；用户态1.404GHz，校准外层计时局限已披露；不生成修订2|
|非叶子line0|已核实、补丁9已实现待构建|正式工具复现伪调用点65525；重任务门禁不满足，未构建/验收/导出0009；见[报告15](15_patch9_nonleaf_line0.md)|
|统计质量分析|参考准备完成，最终矩阵未完成|R参考IR及spike C导出通过；等待补丁9，FFmpeg C export被3GiB scope OOM终止；见[质量报告](../eval/quality_round1.md)|

资源总汇：最低已保存MemAvailable5.289GiB；成功测得峰值RSS500,516KiB；scope OOM一次，精确OOM峰值未知。全局低内存暂停/终止阈值均未触发，不原样重试FFmpeg export，不提高限额。重任务一次门禁不满足且未重试。[完整资源证据](evidence/16/06_resource_summary.json)

运行时例外说明：按用户明确要求使用systemd user scope，其临时unit/cgroup及系统日志由systemd管理，本轮只查询了本任务scope的状态和OOM日志；项目材料未写到WORKDIR之外。没有改认证，没有LLVM/Gerrit推送。
