# 第一批 RPi4 板上评估：预注册

本文件的 Git commit 时间为预注册时间；必须成功推送后才查询/采集本轮板上数据。对象仅 RPi4。冻结设计 v0.7 正文不改，本轮裁决另在报告12登记供v0.8采用。所有既有探测数字仅用于操作规划，不与改动后的内核作性能比较。

## 1. 输入、构建与权限

- 训练：BBB 720p，SHA256 `b5e116b9d01cec8e7f697041c53575d36bd96a5928e40faa69e731f9ae2d00a4`。BBB1080p仅压力/LOST。
- 测试：只从download.blender.org或mango.blender.org下载Tears of Steel官方影片；独立于BBB，固定取300–360秒，不依据测量结果选片段。按media/README.md的720p原命令：libx264/veryfast/High/yuv420p，1280×720/30fps/60秒，4M目标与maxrate、8M bufsize，2编码线程/1滤镜线程、无音频、faststart。原命令level自动选择，用ffprobe核对原BBB及新片段实际level一致。证据11/09只有码率等元数据，编码命令以同一仓库media/README.md和旧原始日志补足。不同内容的实际平均码率不要求逐bit相等。
- 报告11的16项RPi4清单：spike/FFmpeg × Thumb/A32 × S/R/C/G5。逐项SHA与运行时目标路径、build-id核对。
- 允许sdb root on及performance governor；先记录原状态，成功、失败、可捕获中断都恢复并核对。sysfs governor写入是本轮明确授权的/opt写入边界例外；除此仅/opt/afdo_agent。perf_event_paranoid、kptr_restrict保持不变；不安装RPM、不重启、不remount。
- 三项认板断言与用户任务一致；无匹配或多个候选停止。所有RUN记录完整内核指纹，内核改变则停止跨组比较。未知配置哈希显式记unknown，不挂载/boot。

## 2. 固定采集矩阵

| 对象/输入 | 固定间隔低/中/高 | 频率中档 | 训练 |
|---|---|---|---|
| spike Thumb | 各5次 | 5次 | R/C/G5各1次 |
| spike A32 | 各5次 | 5次 | R/C/G5各1次 |
| libavcodec Thumb / BBB720 | 各5次 | 5次 | R/C/G5各1次 |
| libavcodec Thumb / Tears of Steel | 中档5次 | 无 | R/C各1次 |
| libavcodec A32 / BBB720 | 中档5次 | 无 | R/C/G5各1次 |

合计至少70份独立S采集、14次训练，另有校准、LOST及5类集成用例。低/中/高按目标DSO内样本数达到20,000 / 100,000 / 400,000；预算不是全系统样本数。独立采集重启负载/perf，不能将一次录制切块冒充5次。按重复编号轮转低/中/高预算，避免只把一个预算放在最后。

固定间隔起点cycles -c 1000003；频率cycles -F 1000。通过spike rounds或多次完整解码分段达到预算，不凭profile质量调参；每份记录段数、时长、事件、实际target数量及超额。分段保留全部原始数据/完整导出，逻辑RUN内按同一语义合并计数，不能删掉低样本段。校准轮标记CALIBRATION，不进入5次独立采集。频率模式也以实际目标样本数达标。

spike现有接口为rounds/seed，没有明确可选的冷热分布模式；随机换seed不自动视为“已知热点分布不同”。若源码确认无该能力，记录条件负对照不支持，不改源码。

LOST先用BBB1080p、cycles -c 10007 -m 1，必要时同shell双解码进程加系统级录制。完整保存，不以仅LOST摘录代替；“LOST较多”操作定义为至少100条LOST且L>=1000。未达到则如实报告，不改原始文本。LOST压力是故意异常，单独分层，不参与正常质量/性能组的剔除判定。

## 3. 异常判据（采集前写定）

对每个逻辑RUN及其全部段，保存每秒telemetry、开始/结束vmstat、zram、policy边界与内核指纹。异常标志取并集，不在看到效果后调阈值：

1. 换出：RUN内`delta(pswpout) × getconf PAGESIZE >= 4 MiB`为明显换出；计数回退或无法读取为unknown。
2. 节流/电源：vcgencmd get_throttled当前低4位任一非零，或本RUN新出现对应高16–19位历史标志，即异常。预先已经置位的历史位不单独判本RUN异常。无该工具/不能读取时记unknown，不声称没有节流。
3. 温度：任一CPU/SoC thermal sensor达到或超过75,000毫摄氏度，或报告小于0/高于110,000的异常值，标记异常/传感器无效。传感器缺失为unknown。
4. 频率：performance governor期间，以RUN前只读取得的各policy scaling_max_freq为基准；负载存活期间连续3个1秒观测低于其95%，或任一次高于其105%，标记异常。governor不是performance、边界缺失或观测缺失为unknown/状态异常，不选择性忽略。
5. 身份/SHA/build-id/硬件事件错误、空间不足等为任务停止条件，不是可丢弃后继续的普通异常。输出校验和不一致同样停止，不作为噪声剔除。

主结果保留全部轮次；附录另报告去除上述异常和unknown后的干净子集，逐条列原因及数量。不得只公布剔除后的结果。正常组干净独立重复不足5次时只标证据不足；需要补采必须保留先前所有轮次及预注册规则，不放宽阈值。本轮只采集和记录，不进行质量/收益统计决策。

## 4. 后续统计规则

- 性能：每组至少10个交错正式轮次，预热不入统计但保留原始记录；解码耗时中位数相对差的等价区间±1%。RPi4证据不足时后续加轮数，不放宽区间。本轮不做消费构建后的性能比较。
- 质量：严格匹配分支的概率绝对误差，配置间差值等价区间±0.01。后续共同严格匹配集合中先对各分支后继概率绝对误差取均值，再对分支等权平均成每次采集的指标；同时保留逐分支误差、两侧严格匹配率和排除原因，不能用覆盖缩小掩盖失配。
- bootstrap默认独立重采样，种子20261104、20,000次、percentile 95% CI；不因交错自动当作配对。只有CI完整落在等价区间内才称等价，其他为证据不足。不得把分支权重跨终结指令求和解释为执行次数。
- 全部S的规范转换：正式工具SHA `334a09290f53eb4c793ae91759f2b6344a36e63317820eb9151771b262dc3f30`，sample/sum、head=none、zero-fill=none、skid=none、extbinary，显式verified身份；频率数据另输出period权重，显式period-unit=1000003，和sample分开保留。不合并不同语义的profile。
- 中档Thumb真实avg独立核对预定选首份成功完成的libavcodec/BBB720固定间隔RUN，在该RUN按目标采样数排序选前3个可核对热点函数，GNU objdump/addr2line复算；无法复算的原因逐一列出，不换成“容易通过”的函数。sum/max作为并列对照，不据其结果选择默认值。

## 5. 保存与恢复

每次保存perf.data、未经行过滤的5.2.2导出、evlist、buildid-list、stderr和真实退出码；主机收到并SHA核对后才删除对应板上RUN。校准与失败数据也保留。训练只合并各stage负载的profraw，排除setup；训练/测试视频、ISA和stage分开。主机与板上长步骤每600秒资源记录，并写带时间ALL-END。

root原状态和governor原值在改变前独立保存到主机及/opt（能写时）；恢复governor后再恢复root，逐项回读。连接丢失等不能确认恢复的情况明确报告“未确认”，不能声称已恢复；不通过改sysctl或重启绕过。脚本、perf、库保留供下一轮；结束记录df与RPM包数。只推结果仓库GitHub，不推LLVM/Gerrit。
