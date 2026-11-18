# K1a RPi4 现有内核基线

**60°C 重试完成。五项基准各取得 3 次预热、10 次计时和一次 system-wide 采样。50 个计时轮中 18 个带起跑温度标记，均保留。实机 boot 镜像和运行内核的身份相符，两者与历史 c27f160d 构建不同。详见下方重试章节。**

## 首次 58°C 门禁记录（保留）

本轮使用用户确认来自 `linux-rpi@0fac5de6a63091d141ad1cd3ed9d9e92b8dde708` 的现有运行内核。归档的另一次 BASE 构建为后续实验输入。[BASE 主机构建及部署方案](03_k1a_base_kernel_build.md)

## 运行身份与配置

| 项目 | 实测 |
|---|---|
| SDB serial / DT serial | `192.168.108.26:26101` / `100000004694d889` |
| DT model | Raspberry Pi 4 Model B Rev 1.5 |
| 镜像 | `tizen-unified-toolchain_20261104.160709` |
| `uname -a` | `Linux localhost 6.12.80-arm-rpi4-v7l #1 SMP Wed Nov  4 17:05:36 UTC 2026 armv7l GNU/Linux` |
| `/proc/version` | `Linux version 6.12.80-arm-rpi4-v7l (abuild@ip-192-168-56-171) (clang version 22.1.8, LLD 22.1.8) #1 SMP Wed Nov  4 17:05:36 UTC 2026` |
| 运行内核 GNU build-id | `395733b9c917cb98309b39cc3ec379c03ac36b3f`，拉回 `/sys/kernel/notes` 按 ELF32 小端 note 解析 |
| 普通 kernel/modules NEVRA | 按两个构建 RPM 名查询均未安装。已装 RPM 名单中无 kernel/linux-rpi 匹配，`/boot` 为空且未挂载，抽查 `kernel/lib/crc7.ko` 无 RPM 所有者。NEVRA 无法从 RPMDB 确认 |
| 内核配置 | `/proc/config.gz` 缺失，未取得运行配置，逐项差异未知。主机构建 `.config` 的 `CONFIG_IKCONFIG` 未启用，也无 `/proc/config.gz` 的预期 |
| 硬件 PMU | 运行内核的 `pmu/driver` 指向 `armv8-pmu`，事件源 `armv8_cortex_a72`。能力检查一次同时读到 cycles:u=366,129 和 cycles:k=2,362,872，两个事件 running 均 100% |

运行身份与 K0 曾记下的旧采样 build-id 相符。主机构建 ID 为 `25599043a52ba8e5edf2f7bf4e9bb51aaf9d65a3`。本轮符号化输入限定为板上 kallsyms，归档主机 `System.map` 与 vmlinux 只用于主机尺寸参照。确认 PMUv3 的实际可用性与主机配置一致。运行内核的 Thumb2、DWARF4、BTF 与其余配置值没有逐项证据。源码归属采用用户提供的提交，build-id 验证的是运行二进制身份。

## 基准参数与计数口径

| 基准 | 固定工作量 | 吞吐单位 |
|---|---|---|
| sched pipe | `perf bench sched pipe -l 500000`，进程模式 | loop/s |
| syscall basic | `perf bench syscall basic -l 20000000`，getppid(2)，实机 perf 6.12.80 支持 | syscall/s |
| tmpfs | 私有挂载命名空间内的 96 MiB tmpfs，每轮重复 8 次 64 MiB 顺序写、顺序读和删除，写入后检查长度 | MiB/s，读与写合计 1,024 MiB |
| 内存压力 | 4 个工作进程，各 128 MiB 匿名内存。按 16 MiB 一批逐 4 KiB 页写入固定种子派生字，批间 20 ms，保持 250 ms，回访并验校验和，再逐批释放，批间 10 ms。启动前要求 MemAvailable ≥1.5 GiB | MiB/s，触页工作集 512 MiB 除以整轮墙钟 |
| ToS 720p | M1 attempt-11 的 BASE.tar，校验六个 FFmpeg DSO 的 SHA。沿用 `timed.sh` 的 qtdemux → h264parse → avdec_h264（max-threads=1）→ I420 → fakesink（sync=false），输入为同一个 60 s/1,800 帧 ToS 片段 | 帧/s |

计划每项 3 个 warm-up、10 个计时轮和一次 system-wide record。负载固定 CPU3，遥测固定 CPU0，原始 Bash wall 计时包括 perf stat 的进程开销。计数使用同一轮任务及子进程的 cycles:u 和 cycles:k，内核周期占比为 sum(k)/sum(k+u)，不包含其他 CPU 的系统后台负载。system-wide 采样包含全板背景和采集开销，分母以记录的内核样本数为准。固定周期 1,000,003 cycles，带 `--buildid-mmap`，重复工作负载至少 36 秒，单次采集限 60 秒。root 读取 `/proc/kallsyms`，`kptr_restrict=0` 已得到可用地址。分析按内核模式 IP、前后快照及模块地址范围做函数/模块归属。

每轮先空闲 5 秒，复用 workflow `start_gate.sh`，每 30 秒检查所有已发现温度传感器，≤58°C 才起跑，最多等待 600 秒。遥测握手覆盖负载 `[start−1s,end+1s]`，读取固定频率、温度和已报告的电压告警。复用 workflow 分类的 60°C 起跑上限和 80°C 全窗口上限，窗口边界缺失或间隔 >2 s 标为 telemetry_missing。样本 CV＝样本标准差/均值。ε=1% 时按 workflow 的半宽规划，估算配对 block 数为 `min(40,max(10,ceil(2*(1.96*1.2533*CV/0.005)^2)))`，需 10 个有效计时轮。该预算按单变体 CV 估计，实际配对方差留待 K1 验证。

## 计时与符号统计

2026-11-18 06:16:40 UTC 开始首轮空闲降温。21 个读数覆盖 601 秒墙钟（脚本等待预算 600 秒），范围为 **58.426–59.887°C**。首轮为 sched pipe 的第 1 次预热，门禁返回 3 后脚本结束。600 秒门禁、实际负载窗口与遥测分类是分别记录的，因此没有给未起跑的轮次套用遥测标签。

| 基准 | 已完成预热 / 计时 / record | 时间 / 吞吐 / CV / ε=1% block | 内核周期占比 / 内核前 30 函数 / 模块 |
|---|---:|---|---|
| sched pipe | 0 / 0 / 0 | 未测 | 未测 |
| syscall basic | 0 / 0 / 0 | 未测 | 未测 |
| tmpfs | 0 / 0 / 0 | 未测 | 未测 |
| 内存压力 | 0 / 0 / 0 | 未测 | 未测 |
| ToS 720p | 0 / 0 / 0 | 未测 | 未测 |

当前没有满足高内核占比、低 CV 的实测推荐。恢复测量时保留 K0 的候选顺序，先验证 pipe、syscall、tmpfs，再评估内存压力是否确实触发回收或 swap，最后用 ToS 检查媒体场景的相关性。采样可用性检查仅为一次 `perf stat ... /bin/true`，不计入基准。

私有 tmpfs 在初始化时挂载，退场时卸载。首次后台启动的进程在建立脚本状态前退出，随后通过持续的 SDB 会话运行，板上 `REMOTE_EXIT=3` 与结束收据一致。此尝试未检验实际负载、ToS 运行时的 DSO 映射、遥测窗口覆盖、采样解析和函数排名。

## 内存与尺寸参照

板上首读 `MemTotal=3,976,476 KiB`，`MemAvailable=3,370,836 KiB`，`Slab=56,472 KiB`，`VmallocUsed=21,076 KiB`，zram swap 已使用 4,352 KiB。`/proc/vmallocinfo` 有 7,362 行，第二列区域总长 446,574,592 B，其中 55 个带 ioremap 标记的区域合计 338,296,832 B，495 个带 vmalloc 标记的区域合计 24,530,944 B。区域长度包含映射和保留空间，驻留内存采用 meminfo 与实际分配数据另行判断。

超时清理后的空闲快照为 `MemAvailable=3,379,976 KiB`、`Slab=56,304 KiB`、`VmallocUsed=21,140 KiB`，swap 已用仍为 4,352 KiB。末次 vmallocinfo 有 2,575 行，第二列区域总长 387,792,896 B。带 ioremap 标记仍有 55 个、338,296,832 B，带 vmalloc 标记有 503 个、24,629,248 B。首末快照覆盖准备、空闲等待和清理，不能作为任一基准的前后变化。各基准的内存快照因未起跑而缺失。

主机 GNU `size -A` 对归档 BASE 的测量如下，`readelf -SW` 同时核对 AX 节（可分配、可执行）。主机 ELF 与板上运行内核的 build-id 不同，表中数值用于后续尺寸优化参照。

| 归档构建对象 | `.text` 字节 | AX 节总字节 |
|---|---:|---:|
| 普通 vmlinux | 19,870,632 | 20,237,876 |
| 普通 52 个未剥离模块合计 | 672,856 | 685,980 |

## 原始证据与范围

主机归档根为 `temp/kernel-afdo-k1/baseline-rpi4-01/`。M1 输入接触记录涉及 attempt-11 的 BASE.tar 与对应 DSO manifest、同一 ToS 输入和 `timed.sh`。用途为固定本轮用户态媒体负载，既有 M1 perf.data 和 profile 未读取。板上文件写入 `/opt/afdo_agent/k1a-baseline-01/` 及同级任务归档，governor 为本轮临时 sysfs 状态变更。归档拉回后 SHA-256 与板上相同，任务文件已移除。完整的温度读数、证据摘要与 SHA 均在索引中。[原始证据索引](04_k1a_baseline.index.json)

退出后核验 `schedutil → performance → schedutil`，SDB root off 且 `uid=5001(owner)`，`kptr_restrict` 前后均为 0。退出收据 `measurement=3 cleanup=0`，任务进程及挂载已退出，boot_id 前后一致。BASE 部署仍为未执行，本轮无 profile 产物。恢复测量需要空闲时达到 58°C，正式计时和采集结果仍待验证。

## 重试：60°C 起跑与轮间 powersave

PM 指定本轮用于估计噪声、周期占比和热点函数，因此采用设计 v0.3 的 T_start=60°C。首次 58°C 的门禁收据保留在上节。重试沿用 T_max=80°C 和 `[start−1s,end+1s]`，频率要求固定 1.5 GHz。温度或频率异常仍保留原轮，并同时报告全量和 clean 子集。设定为起跑前温度 >60°C 或整个遥测窗口达到 80°C 才构成温度异常，负载期间在 60–80°C 的读数仍保留于原始窗口。

首项前先在 `performance` 下作 10 分钟无基准负载观察，与 M1 attempt-10 的 `cooling-idle` 用相同 governor。诊断以板上 uptime 为时间轴，每 10 秒读取所有发现的温度传感器、各 CPU 的 governor、`scaling_cur_freq`、`cpuinfo_cur_freq` 和 loadavg。读取 `/proc/*/stat` 的 utime+stime，以 PID 和 starttime 对齐相邻采样，按增量取前五。首点使用 0.2 秒预采样，因此与后续 10 秒增量分别解释。

每轮切 `powersave` 后开始门禁，温度全数 ≤60°C 才切回 `performance`，稳定等待 3 秒后采集遥测。门禁每 10 秒一次，最长 600 秒。每次切换均保存时间、前后 governor 和各 CPU 频率，另记 3 秒稳定后的频率。3 轮预热、10 轮计时和独立 system-wide 采样采用同一门禁。采样按实际硬件 cycles 的固定周期执行，附带 mmap build-id。

启动前的板上能力检查发现旧 `dd` 拒绝 `status=none`，移除此显示选项，固定读写参数一致。首次空闲诊断在温度采样前由于旧 awk 的条件表达式解析错误退出，退出收据确认恢复 governor，修正括号并在实机检验后重新开始完整十分钟曲线。正式负载的重试数量和有效性见下节。
前三项完成后，内存 worker 文件与结果目录同名，第一次主流程退出 1，清理返回 0。将可执行文件改名为 `memory-worker` 后，从尚未起跑的内存项继续，前 42 个计时、预热和采样原件保持不变。ToS 预热约 31 秒，固定 36 秒重复循环会执行第二次完整解码并超过 60 秒，因此 ToS 独立采样只执行一次完整解码。最终续跑退出 0，合计 15 个预热、50 个计时及 5 个独立采样全部完成，每个基准 3+10+1。没有重跑或替换已取得的轮次。

### 降温诊断

| 10 分钟无基准负载 | 点数 / 覆盖时长 s | 首 / 尾 °C | 最低 / 最高 °C | 中位 °C | 首达 ≤58°C |
|---|---:|---:|---:|---:|---:|
| 本轮 RPi4 | 61 / 599.71 | 59.400 / 58.913 | 58.426 / 59.887 | 59.400 | 未达到 |
| M1 attempt-10 cooling-idle | 61 / 600.73 | 58.913 / 57.939 | 56.965 / 59.400 | 57.939 | 10.02 s |

两次均使用 `performance`。本轮四核读数全为 1.5 GHz，1 分钟 loadavg 为 1.00–1.16，`enlightenment` 每次均排名第一，总计 58,286 ticks（`CLK_TCK=100`，约占一个核的 97%）。本轮温度中位比 M1 高 1.461°C。M1 原曲线只采温度，无同步逐核频率、进程增量或室温，无法分解背景负载与环境各自影响。板上 hwmon 未暴露风扇转速，物理风扇状态未知。原 M1 曲线和本轮诊断字段、进程排名、切换日志及频率读数按 SHA 索引保留。

首次尝试在 `performance` 下以 59.400°C 开始等待，601 秒采样均高于 58°C，最低 58.426°C。重试的 70 次门禁都通过，`powersave` 读数均为 600 MHz，37 次首点已达门槛，33 次需等下一点，最长 9.59 秒（首点到达标点之间，不含首点准备及后续 3 秒频率稳定）。本轮门槛从 58 改为 60，后台负载及环境也可能不同，因此这组前后差异无法单独量化 governor 的因果效果。

| 基准 | 达标温度范围 °C | 有等待轮 / 14 | 等待中位 / 最大 s | 计时轮最后一个起跑前温度范围 °C |
|---|---:|---:|---:|---:|
| sched pipe | 57.452–59.887 | 9 | 9.58 / 9.59 | 58.913–60.861 |
| syscall basic | 56.965–59.887 | 7 | 4.79 / 9.59 | 58.426–61.348 |
| tmpfs | 57.452–59.887 | 2 | 0.00 / 9.59 | 58.913–61.348 |
| 内存触页 | 57.939–59.887 | 1 | 0.00 / 9.57 | 58.913–60.374 |
| ToS 720p | 57.939–58.913 | 14 | 9.58 / 9.59 | 58.913–59.887 |

### 计时、噪声与周期占比

墙钟为一次完整 `perf stat` 启动的 Bash `time`，含进程启动开销。吞吐用固定工作量除以计时中位数。ToS 依据固定输入的 1,800 帧和 EOS 计算名义吞吐。全部 50 轮的两项硬件计数运行率均为 100%。内核占比为计时批次的 `sum(cycles:k) / sum(cycles:k + cycles:u)`。块数采用历史节的 ε=1% 预算公式，括号内为截断前值，无 A/B 效果判定。

| 基准 | 均值 / 中位 s | 中位吞吐 | CV | block 预算（原值） | 内核周期 | 计时标记 / 10 |
|---|---:|---:|---:|---:|---:|---:|
| sched pipe | 13.4333 / 13.4175 | 37,264.77 loop/s | 0.787% | 30（30） | 97.671% | 5 |
| syscall basic | 11.3071 / 11.2720 | 1,774,308.02 syscall/s | 1.113% | 40（60） | 87.235% | 6 |
| tmpfs | 3.0091 / 2.9995 | 341.39 MiB/s | 1.339% | 40（87） | 99.394% | 3 |
| 内存触页 | 1.7992 / 1.7960 | 285.08 MiB/s | 0.765% | 29（29） | 97.912% | 3 |
| ToS 720p | 30.7211 / 30.7005 | 58.63 帧/s | 0.409% | 10（9） | 1.392% | 1 |

标记为窗口起跑区间出现 >60°C，共 18/50 个计时轮、8/15 个预热轮、3/5 个采样轮。零频率异常、零电压告警、零窗口缺失，计时最高 64.270°C，所有窗口均低于 80°C。为呈现全部超过 60°C 的情况，下表另列任何窗口读数 >60°C 的轮数。主表保留全部轮次，clean 子集仅供敏感性检查，样本均不足 10 个，未用它重新定 block 预算。

| 基准 | clean 计时数 | clean 中位 s / CV | clean 内核周期 | 预热标记 / 3 | 任意窗口 >60°C / 10 | 标记计时轮 |
|---|---:|---:|---:|---:|---:|---|
| sched pipe | 5 | 13.4020 / 0.742% | 97.693% | 1 | 10 | 03,04,05,08,09 |
| syscall basic | 4 | 11.2750 / 0.912% | 87.121% | 3 | 10 | 01,04,05,06,08,10 |
| tmpfs | 7 | 3.0010 / 1.451% | 99.395% | 2 | 10 | 02,05,09 |
| 内存触页 | 7 | 1.7950 / 0.359% | 97.936% | 2 | 9 | 01,02,06 |
| ToS 720p | 9 | 30.6440 / 0.432% | 1.394% | 0 | 10 | 09 |

### System-wide 采样与符号

每项执行 `perf record -a -e cycles -c 1000003 --buildid-mmap -N`。前四项重复各自固定负载至至少 36 秒，ToS 完整解码一遍。五份 record 的硬件事件与 1,000,003 周期已核验，perf 的 SAMPLE 计数与导出 IP 条数一致，event stats 无 LOST 条目。内核 build-id 均为 `395733b9c917cb98309b39cc3ec379c03ac36b3f`。root 在 `kptr_restrict=0` 下读取采集前后 kallsyms 和模块列表。依据样本 CPU mode、同次内核地址区间与稳定的模块区间归属，对内核文本 IP 使用最近前序 T/t/W/w 符号，同址别名合并。每份内核样本均归入核心文本或模块，没有未归属样本。该方法的函数边界来自符号起址，精度不包含内联层和调用栈；PMU skid 仍可能把个别 IP 落在邻近指令。

system-wide 的分母含其他核与后台程序，不能代替前表的任务周期占比。`enlightenment` 占全板样本的 44.99–49.42%，在 ToS 采样中占内核样本的 60.10%。ToS 样本中的 libavcodec、libavutil 路径位于本次专用 BASE 目录，记录的两个 build-id 均与 M1 BASE.tar 中的原始 ELF 一致。其余四个 DSO 的部署 SHA 通过核验。整套管线复用 M1 的计时脚本。

| 基准 | record s / 标签 | 全部 / 内核样本 | 内核样本占全板 | 模块样本（占内核样本） |
|---|---|---:|---:|---|
| sched pipe | 39.297 / telemetry_anomaly | 119,028 / 70,909 | 59.573% | proc_tsm 4 (0.0056%), kdbus 4 (0.0056%) |
| syscall basic | 47.307 / telemetry_anomaly | 139,619 / 68,207 | 48.852% | kdbus 5 (0.0073%), proc_tsm 3 (0.0044%), logger 1 (0.0015%) |
| tmpfs | 40.282 / clean | 122,436 / 75,855 | 61.955% | proc_tsm 6 (0.0079%), logger 2 (0.0026%), hci_uart 1 (0.0013%), kdbus 1 (0.0013%) |
| 内存触页 | 39.302 / telemetry_anomaly | 109,644 / 63,323 | 57.753% | proc_tsm 3 (0.0047%), kdbus 2 (0.0032%) |
| ToS 720p | 33.298 / clean | 97,189 / 13,582 | 13.975% | kdbus 5 (0.0368%), proc_tsm 4 (0.0295%) |

每份采样的前 30 项如下，分母均为该份采样的全部内核样本。

<details><summary>sched pipe 前 30 内核函数</summary>

| # | 函数或同址别名 | 样本 | 占比 |
|---:|---|---:|---:|
| 1 | `_raw_spin_unlock_irqrestore` | 18,877 | 26.621% |
| 2 | `finish_task_switch` | 9,228 | 13.014% |
| 3 | `vector_swi` | 4,175 | 5.888% |
| 4 | `__rseq_handle_notify_resume` | 3,873 | 5.462% |
| 5 | `arch_local_irq_enable` | 2,656 | 3.746% |
| 6 | `kunmap_local_indexed` | 2,573 | 3.629% |
| 7 | `__kmap_local_pfn_prot` | 2,556 | 3.605% |
| 8 | `do_work_pending` | 1,959 | 2.763% |
| 9 | `arm_copy_from_user` | 1,784 | 2.516% |
| 10 | `do_sys_poll` | 1,216 | 1.715% |
| 11 | `pipe_write` | 1,124 | 1.585% |
| 12 | `arm_copy_to_user` | 968 | 1.365% |
| 13 | `eventfd_write` | 925 | 1.304% |
| 14 | `ktime_get_coarse_real_ts64` | 910 | 1.283% |
| 15 | `__fget_files` | 682 | 0.962% |
| 16 | `_raw_spin_lock_irqsave` | 668 | 0.942% |
| 17 | `_copy_from_iter` | 643 | 0.907% |
| 18 | `arm_clear_user` | 616 | 0.869% |
| 19 | `pipe_read` | 591 | 0.833% |
| 20 | `fput` | 577 | 0.814% |
| 21 | `mutex_unlock` | 502 | 0.708% |
| 22 | `__copy_from_user_std` | 490 | 0.691% |
| 23 | `vfs_write` | 456 | 0.643% |
| 24 | `mutex_lock` | 452 | 0.637% |
| 25 | `eventfd_read` | 422 | 0.595% |
| 26 | `fdget_pos` | 412 | 0.581% |
| 27 | `vfs_read` | 407 | 0.574% |
| 28 | `__audit_syscall_entry` | 382 | 0.539% |
| 29 | `migrate_enable` | 371 | 0.523% |
| 30 | `__audit_syscall_exit` | 324 | 0.457% |

</details>

<details><summary>syscall basic 前 30 内核函数</summary>

| # | 函数或同址别名 | 样本 | 占比 |
|---:|---|---:|---:|
| 1 | `vector_swi` | 40,953 | 60.042% |
| 2 | `ktime_get_coarse_real_ts64` | 3,757 | 5.508% |
| 3 | `__audit_syscall_entry` | 2,117 | 3.104% |
| 4 | `do_sys_poll` | 2,059 | 3.019% |
| 5 | `_raw_spin_unlock_irqrestore` | 2,039 | 2.989% |
| 6 | `__audit_syscall_exit` | 1,831 | 2.684% |
| 7 | `eventfd_write` | 1,079 | 1.582% |
| 8 | `syscall_trace_enter` | 998 | 1.463% |
| 9 | `ret_slow_syscall / ret_to_user` | 907 | 1.330% |
| 10 | `__fget_files` | 740 | 1.085% |
| 11 | `fput` | 588 | 0.862% |
| 12 | `__task_pid_nr_ns` | 543 | 0.796% |
| 13 | `eventfd_read` | 538 | 0.789% |
| 14 | `syscall_trace_exit` | 430 | 0.630% |
| 15 | `handle_mm_fault` | 315 | 0.462% |
| 16 | `arm_copy_from_user` | 312 | 0.457% |
| 17 | `__sys_trace` | 291 | 0.427% |
| 18 | `__memset / memset / mmioset` | 290 | 0.425% |
| 19 | `__ep_eventpoll_poll` | 289 | 0.424% |
| 20 | `ep_done_scan` | 266 | 0.390% |
| 21 | `do_page_fault` | 243 | 0.356% |
| 22 | `arch_local_irq_enable` | 242 | 0.355% |
| 23 | `__kmap_local_pfn_prot` | 235 | 0.345% |
| 24 | `kunmap_local_indexed` | 234 | 0.343% |
| 25 | `fdget` | 216 | 0.317% |
| 26 | `__copy_from_user_std` | 216 | 0.317% |
| 27 | `vfs_write` | 215 | 0.315% |
| 28 | `percpu_counter_add_batch` | 214 | 0.314% |
| 29 | `signalfd_poll` | 212 | 0.311% |
| 30 | `__sys_trace_return` | 206 | 0.302% |

</details>

<details><summary>tmpfs 前 30 内核函数</summary>

| # | 函数或同址别名 | 样本 | 占比 |
|---:|---|---:|---:|
| 1 | `_raw_spin_unlock_irqrestore` | 9,673 | 12.752% |
| 2 | `__memcpy / memcpy / mmiocpy` | 8,827 | 11.637% |
| 3 | `__copy_from_user_std` | 8,152 | 10.747% |
| 4 | `__memset / memset / mmioset` | 4,377 | 5.770% |
| 5 | `arch_local_irq_enable` | 3,136 | 4.134% |
| 6 | `kunmap_local_indexed` | 3,102 | 4.089% |
| 7 | `__kmap_local_pfn_prot` | 2,265 | 2.986% |
| 8 | `shmem_add_to_page_cache` | 2,004 | 2.642% |
| 9 | `filemap_remove_folio` | 1,905 | 2.511% |
| 10 | `vector_swi` | 1,542 | 2.033% |
| 11 | `do_sys_poll` | 1,465 | 1.931% |
| 12 | `percpu_counter_add_batch` | 1,439 | 1.897% |
| 13 | `__percpu_counter_limited_add` | 1,143 | 1.507% |
| 14 | `__clear_user_memset` | 1,038 | 1.368% |
| 15 | `try_charge_memcg` | 1,026 | 1.353% |
| 16 | `memcg1_commit_charge` | 1,021 | 1.346% |
| 17 | `eventfd_write` | 850 | 1.121% |
| 18 | `__copy_to_user_memcpy` | 816 | 1.076% |
| 19 | `arm_copy_from_user` | 795 | 1.048% |
| 20 | `get_page_from_freelist` | 759 | 1.001% |
| 21 | `__fget_files` | 649 | 0.856% |
| 22 | `_raw_spin_lock` | 573 | 0.755% |
| 23 | `xas_load` | 521 | 0.687% |
| 24 | `fput` | 476 | 0.628% |
| 25 | `get_mem_cgroup_from_mm` | 457 | 0.602% |
| 26 | `handle_mm_fault` | 448 | 0.591% |
| 27 | `eventfd_read` | 444 | 0.585% |
| 28 | `shmem_get_folio_gfp` | 405 | 0.534% |
| 29 | `filemap_get_entry` | 402 | 0.530% |
| 30 | `migrate_enable` | 379 | 0.500% |

</details>

<details><summary>内存触页 前 30 内核函数</summary>

| # | 函数或同址别名 | 样本 | 占比 |
|---:|---|---:|---:|
| 1 | `_raw_spin_unlock_irqrestore` | 11,693 | 18.466% |
| 2 | `__memset / memset / mmioset` | 9,210 | 14.544% |
| 3 | `handle_mm_fault` | 3,862 | 6.099% |
| 4 | `kunmap_local_indexed` | 3,469 | 5.478% |
| 5 | `arch_local_irq_enable` | 3,271 | 5.166% |
| 6 | `do_page_fault` | 2,752 | 4.346% |
| 7 | `__kmap_local_pfn_prot` | 2,412 | 3.809% |
| 8 | `percpu_counter_add_batch` | 2,107 | 3.327% |
| 9 | `memcg1_commit_charge` | 1,661 | 2.623% |
| 10 | `try_charge_memcg` | 1,644 | 2.596% |
| 11 | `vector_swi` | 1,464 | 2.312% |
| 12 | `do_sys_poll` | 1,323 | 2.089% |
| 13 | `get_page_from_freelist` | 827 | 1.306% |
| 14 | `eventfd_write` | 814 | 1.285% |
| 15 | `__fget_files` | 747 | 1.180% |
| 16 | `get_mem_cgroup_from_mm` | 616 | 0.973% |
| 17 | `uncharge_folio` | 559 | 0.883% |
| 18 | `fput` | 542 | 0.856% |
| 19 | `charge_memcg` | 518 | 0.818% |
| 20 | `eventfd_read` | 451 | 0.712% |
| 21 | `__mem_cgroup_charge` | 447 | 0.706% |
| 22 | `_raw_spin_lock_irqsave` | 406 | 0.641% |
| 23 | `migrate_enable` | 333 | 0.526% |
| 24 | `mas_state_walk` | 326 | 0.515% |
| 25 | `__mod_memcg_lruvec_state` | 301 | 0.475% |
| 26 | `arm_copy_from_user` | 280 | 0.442% |
| 27 | `unmap_page_range` | 268 | 0.423% |
| 28 | `_raw_spin_lock` | 257 | 0.406% |
| 29 | `folio_remove_rmap_ptes` | 241 | 0.381% |
| 30 | `__kmap_local_page_prot` | 241 | 0.381% |

</details>

<details><summary>ToS 720p 前 30 内核函数</summary>

| # | 函数或同址别名 | 样本 | 占比 |
|---:|---|---:|---:|
| 1 | `_raw_spin_unlock_irqrestore` | 1,513 | 11.140% |
| 2 | `vector_swi` | 1,142 | 8.408% |
| 3 | `do_sys_poll` | 1,109 | 8.165% |
| 4 | `eventfd_write` | 697 | 5.132% |
| 5 | `__fget_files` | 498 | 3.667% |
| 6 | `fput` | 417 | 3.070% |
| 7 | `eventfd_read` | 339 | 2.496% |
| 8 | `arch_local_irq_enable` | 316 | 2.327% |
| 9 | `kunmap_local_indexed` | 251 | 1.848% |
| 10 | `__memset / memset / mmioset` | 234 | 1.723% |
| 11 | `__kmap_local_pfn_prot` | 226 | 1.664% |
| 12 | `do_page_fault` | 211 | 1.554% |
| 13 | `arm_copy_from_user` | 211 | 1.554% |
| 14 | `ktime_get_coarse_real_ts64` | 208 | 1.531% |
| 15 | `handle_mm_fault` | 193 | 1.421% |
| 16 | `__ep_eventpoll_poll` | 187 | 1.377% |
| 17 | `signalfd_poll` | 185 | 1.362% |
| 18 | `ep_done_scan` | 172 | 1.266% |
| 19 | `fdget` | 172 | 1.266% |
| 20 | `percpu_counter_add_batch` | 167 | 1.230% |
| 21 | `finish_task_switch` | 159 | 1.171% |
| 22 | `__copy_from_user_std` | 158 | 1.163% |
| 23 | `__audit_syscall_entry` | 143 | 1.053% |
| 24 | `vfs_write` | 130 | 0.957% |
| 25 | `arm_copy_to_user` | 121 | 0.891% |
| 26 | `vfs_read` | 121 | 0.891% |
| 27 | `mod_objcg_state` | 110 | 0.810% |
| 28 | `pipe_poll` | 102 | 0.751% |
| 29 | `_raw_spin_lock_irqsave` | 88 | 0.648% |
| 30 | `copy_page` | 86 | 0.633% |

</details>

### 内存基线与 K1 选择

以下为每个基准组开始前和采样后快照，组内每轮的 meminfo、vmstat、PSI、swap、zram 摘要均已归档。单位 KiB，整板读数包含背景进程。

| 基准 | MemAvailable 前→后 | Slab 前→后 | SUnreclaim 前→后 | VmallocUsed 前→后 | SwapFree 前→后 |
|---|---:|---:|---:|---:|---:|---:|
| sched pipe | 3,374,760→3,366,680 | 56,256→56,740 | 41,672→41,716 | 21,124→21,076 | 1,586,236→1,586,236 |
| syscall basic | 3,366,872→3,359,452 | 56,740→57,440 | 41,716→41,792 | 21,132→21,108 | 1,586,236→1,586,236 |
| tmpfs | 3,358,860→3,305,292 | 57,440→58,200 | 41,792→41,864 | 21,156→21,092 | 1,586,236→1,586,236 |
| 内存触页 | 3,383,528→3,340,668 | 58,188→58,856 | 41,888→41,888 | 21,116→21,116 | 1,586,236→1,586,236 |
| ToS 720p | 3,340,372→3,358,280 | 58,856→59,808 | 41,888→42,076 | 21,172→21,092 | 1,586,236→1,586,236 |

内存 worker 通过触页校验。该组全板 `pgfault` 增量为 6,387,444，`pgmajfault`、reclaim 扫描/回收、swap in/out、OOM kill 增量均为 0。实际覆盖了匿名页 fault、页清零和 memcg charge，未实测出 reclaim/zram 压力，不能当作其性能或节省内存的证据。清理后 `/proc/vmallocinfo` 共 5,615 行，第二列区域长合计 433,569,792 B，其中 55 个 ioremap 区域合计 338,296,832 B、502 个 vmalloc 区域合计 24,616,960 B。该量与驻留内存口径不同。主机 BASE 的 `size -A` 参照仍为 vmlinux .text 19,870,632 B、52 个模块 .text 合计 672,856 B，与板上运行镜像的 build-id 不同。

建议优先选 **pipe + 内存触页** 做下一轮验证。两项内核周期占比约 98%，全部轮 CV 小于 0.8%，分别覆盖调度/IPC 和 fault/memcg。将 tmpfs 作为第三候选，覆盖 shmem、copy 和页分配，当前 CV 1.34% 且未截断预算需 87 个 block。syscall 更集中于 AArch32 的 `vector_swi`，6/10 标记且 CV 1.11%，适合补充诊断。ToS 的 CV 最低但内核周期只有 1.39%，保留为媒体相关性对照。pipe 和内存触页分别有 5、3 个计时轮标记，正式 A/B 前需确认可取得合格且均衡的遥测；上述预算和样本分布只用于基准选择。

### 历史 PMUv3 构建来源核对

**现运行内核不是历史 c27f160d 的 PMUv3 测试内核。** 当前来源提交仍按用户确认的 `0fac5de6` 记录。二进制身份的证据如下。历史安装文档记载当时预检在包查询失败后停止，不能据该流程认定历史镜像实际安装。依据 [历史安装记录](../02_pmuv3_install.md) 和 [历史构建记录](../03_pmuv3_build_result.md)。

| 项目 | 当前启动镜像 / 运行内核 | 历史 c27f160d 构建 |
|---|---|---|
| uname -v | `#1 SMP Wed Nov  4 17:05:36 UTC 2026` | `#1 SMP Wed Oct 28 04:12:26 UTC 2026` |
| 主机 | `abuild@ip-192-168-56-171` | `abuild@linhao-linux` |
| 普通 zImage SHA-256 | `d5345f13eada3a3aab8b2fca9f511c608469f708d83a6a2445882e68241cc9af` | `a1cf2077f2053f2d779b39a0d9d7482bc636ecb38d5c07caf305fc0889207cd6` |
| 启动内核 GNU build-id | `395733b9c917cb98309b39cc3ec379c03ac36b3f` | `0d411ab9ae3244ee307d50d85e12db55d3e94c69` |
| crc7.ko vermagic | `6.12.80-arm-rpi4-v7l SMP mod_unload modversions ARMv7 p2v8` | 相同 |
| crc7.ko SHA-256 | `1825939b82c1a3d8b9867bcf1fc62d67fd7314f0ce099cc79f5890a42588abc9` | `6bf44318d6cecc61d2343e85e004e39aee8a5dcf98a5a75f6822d48bf649fa64` |

实机 `/boot` 挂载点为空，依据 `partition_ab=a`、实际根分区 mmcblk0p2 与历史启动布局，测量结束后在私有挂载命名空间内将 FAT 的 mmcblk0p1 以 ro、nosuid、nodev、noexec 挂到任务目录，校验后卸载。当前 zImage 解出的内核包含唯一一份与运行 `/sys/kernel/notes` 完全相同的 note 流，Linux banner 也一致。历史 build-id 从归档 zImage 解包后的主内核 .notes 解析，位置由历史 devel ELF 的装载节几何确认。历史 devel 副本的 RPM 后处理 ID 为 `64cd47eb…`，不参与启动身份比较。

历史普通 RPM 的 410 个 boot 文件中 409 个同 SHA（包括 config.txt、DTB、overlays 和固件），唯一差异是 zImage，现有启动分区另有 u-boot.bin、uboot.env、boot.scr.uimg。52 个普通模块路径都能对应历史 modules RPM，文件 SHA 全部不同。抽查 crc7.ko 的 vermagic 与 GNU build-id 相同，依然不能据此认定内核或模块文件字节相同。板上 `/proc/config.gz` 仍缺失，RPMDB 仍无这两个内核包，完整配置差异和 NEVRA 未知。

### 收据与恢复

归档根 `temp/kernel-afdo-k1/baseline-rpi4-02/`。原始板上 tar、五份 perf.data、kallsyms、温度进程记录、计时输入、分析脚本和 SHA 均已保留。raw kallsyms 和记录地址留在本机归档。M1 接触范围为 attempt-11 BASE.tar/manifest、同一 ToS 输入、计时脚本，以及 attempt-10 空闲降温证据。未读取 M1 的 perf.data 或 profile，本轮没有生成 profile。[重试证据索引](04_k1a_baseline.retry.index.json)

收尾核验退出 `measurement=0 cleanup=0`、governor 恢复为 schedutil、`kptr_restrict=0`、SDB root off/uid5001，boot_id 一致，任务挂载与临时路径均不存在。BASE 部署仍未执行，后续仍需独立授权。

## HDMI 接入后的空闲检查（2026-11-18）

2026-11-18 01:02:53（美国太平洋时间）开始在 `192.168.108.26:26101` 只读检查。DT serial `100000004694d889`，板型 Raspberry Pi 4 Model B Rev 1.5，运行 `6.12.80-arm-rpi4-v7l`。GNU build-id `395733b9c917cb98309b39cc3ec379c03ac36b3f` 和 boot_id `33a42791-2527-4041-a54b-9fe3f88d598b` 均与 K1a 一致。

| DRM 连接器 | status | enabled | DPMS |
|---|---|---|---|
| card0-HDMI-A-1 | connected | enabled | On |
| card0-HDMI-A-2 | disconnected | disabled | On |
| card0-Writeback-1 | unknown | disabled | On |

首末连接器读数一致。systemd 首末均报告 `display-manager.service` 为 active/running，主 PID 为 543（`/usr/bin/enlightenment`），启动时间戳不变。

### 2 分钟 CPU 观察

每 5 秒读取一次 `/proc/stat`、loadavg、四个 CPU 的 governor 与频率，25 点覆盖 120.00 秒。按每个 5 秒区间的 CPU 忙时差除以墙钟，100% 对应一个逻辑核连续运行。全板合计包括 user、nice、system、irq、softirq、steal，扣除 idle 和 iowait。全板合计平均 **11.33%**，单区间最高 **19.40%**。单个核的最高区间为 7.40%。1 分钟 loadavg 为 0.05–0.26，逐核频率读数范围 1000–1500 MHz，governor 为 `schedutil`。

K1a 接入前的空闲观察中，`enlightenment` 直接测得约 **97.2% 单核**。接入后 SDB 保持 uid 5001，`/proc/543/stat` 和 `schedstat` 返回 Permission denied，systemd 的 CPUAccounting=no，无服务 CPU 使用计数。因此本次没有该进程的直接占用值。**它的进程占用上界为全板合计：120 秒平均不超过 11.33%，各 5 秒区间均不超过 19.40%。** 这排除了在本次观察中持续跑满一个核。

当前 UID 可读的进程计数按 PID 和 starttime 对齐，再按 utime+stime 的区间差排列。每个采样点可见 149–151 个条目，`sugov:0` 在 22/24 个区间排名第一。原始 24 份可见前五名及 CPU 占用在本机 summary 中。由于权限限制，这一排行无法覆盖全板所有进程。占满单核的触发条件未出现，本轮无 perf 线程或内核栈采样。

### 10 分钟空闲温度

2 分钟 CPU 观察结束后单独开始温度序列，每 10 秒取一点。两个可读温度入口是 `thermal_zone0/temp` 和 `hwmon1/temp1_input`，分别由 cpu-thermal 与 cpu_thermal 驱动报告，两个入口顺序读取。hwmon 的温度范围为 53.556–55.504°C，中位 54.530°C。下表统一使用与历史记录一致的 thermal_zone0。温度阶段的全板忙时最高为单核等效 7.90%，各核 governor 保持 `schedutil`，频率读数 600–1500 MHz。

| 空闲曲线 | governor | 点数 / 覆盖 s | 首 / 尾 °C | 最低–最高 °C | 中位 °C |
|---|---|---:|---:|---:|---:|
| 本轮 HDMI 接入 | schedutil | 61 / 600.02 | 54.043 / 54.530 | 53.556–55.504 | **54.530** |
| K1a 60°C 重试基线 | performance | 61 / 599.71 | 59.400 / 58.913 | 58.426–59.887 | 59.400 |
| M1 attempt-10 cooling-idle | performance | 61 / 600.73 | 58.913 / 57.939 | 56.965–59.400 | 57.939 |

本轮中位温度比 K1a 低 **4.870°C**，比 M1 低 **3.409°C**。三条曲线的 governor、频率和背景活动有差异，室温和物理风扇状态也缺少同步记录。温差表明当前状态有更大的空闲温度余量，无法单独归因于 HDMI。

建议后续测量**保持 HDMI 接入和 TV 显示栈运行**，各变体固定相同的连接器状态、显示内容和 governor。正式计时前用其规定的 `performance` governor 复核空闲段和起跑遥测，确认低背景负载与温度余量在测量条件下仍成立。

原始证据留在 `temp/kernel-afdo-k1/hdmi-idle-rpi4-01/`，`index.json` SHA-256 `8a24458618d82420ff49e0d110fd8b4f0ae672e35818ac96c0c30d12b462c65a`。首次内联采集脚本超过 SDB 服务名称长度，之后用主机调度短只读查询完成全部采样。本轮无板上持久写入，governor、SDB UID、boot ID 和显示服务均保持原状态。
