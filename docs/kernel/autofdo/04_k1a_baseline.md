# K1a RPi4 现有内核基线

**本轮停在首项的 58°C 起跑门禁。600 秒内最低采样 58.426°C，五项基准均未启动。板上身份、PMU 能力、空闲内存快照和主机尺寸参照已取得。**

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
