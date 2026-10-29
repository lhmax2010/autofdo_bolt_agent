# RPi4 PMUv3 新镜像与 v0.2 冻结前事实核实

日期：2026-10-29（Asia/Shanghai）。本轮仅验证、一次性 IR 匹配原型及可选 armv7l spike；未修改 LLVM 源码、设计 v0.2 或启动增强实现。**证据完成不代表设计冻结。**

| 部分 | 结论 | 证据 |
|---|---|---|
| A 新镜像 PMU | 支持：A72 驱动绑定，cycles type=0/config=0、7,659 个样本，instructions/cycles 均有计数 | [E1](evidence/05/01_environment_hardware.txt) |
| B 输入事实 | dsoff 与 PT_LOAD 核验通过；双进程、period 和 build-id 已实测；无 LOST 样例、无主机 perf | [E2](evidence/05/02_perf_formats_mapping.txt) |
| C 主机原型 | 两架构默认 profi/显式关闭符合预期；IR 带权分支匹配 PGO 侧88.24%、sample侧65.22%，并非全量对齐 | [E3](evidence/05/03_clang_ir.txt) |
| D 可选 armv7l | 约7分30秒内完成：GBS两轮成功，MMAP2 build-id匹配，插桩PGO闭环且校验一致 | [E4](evidence/05/04_arm_spike.txt) |

证据中的每项以 `=== 名称 ===` 标识，包含完整命令、真实远端或主机退出码、stdout/stderr；SDB transport 不代替远端退出码。首次建立工作目录前的输出为 SDB 合并流，已标记。大文件/完整 JSON/日志全部保留在 `WORKDIR/temp/rpi4-prefreeze/`，下文简称 T；WORKDIR 为 `/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent`。新增证据四文件共 **146,877 B**，旧证据未改。

本轮板上环境：`LC_ALL=C`、`LD_LIBRARY_PATH=/opt/afdo_agent/lib`；HOME/TMPDIR/PERF_CONFIG/GST_REGISTRY/XDG_CACHE_HOME 均在 `/opt/afdo_agent/work/` 下。下文 P 是 `nice -n 19 ionice -c3 /opt/afdo_agent/tools/perf --buildid-dir /opt/afdo_agent/work/buildid`；F 是 `/opt/afdo_agent/work/`。所有数据命令都显式指定 `-i/-o`，不使用默认当前目录写入。

## A. 新镜像指纹与硬件 PMU

### A.1 身份、镜像和驱动

`sdb connect 192.168.108.26` 连接到 `192.168.108.26:26101`；先读取 uname -m/-r 并断言：`armv7l`、`6.12.80-arm-rpi4-v7l`，两次 uname 退出0，IDENTITY_OK，然后才继续板上查询。model 为 Raspberry Pi 4 Model B Rev 1.5。初始 uid=5001，`sdb root on` 成功，随后 id -u=0。

| 查询 | 实际值 | 与预期 |
|---|---|---|
| /etc/tizen-build.conf | TZ_BUILD_ID=tizen-unified-toolchain_20261028.105834 | 已换新镜像 |
| /etc/os-release | BUILD_ID=tizen-unified-toolchain_20261028.105834_tizen-headed-armv7l | armv7l |
| uname -a | Linux localhost 6.12.80-arm-rpi4-v7l #1 SMP Wed Oct 28 12:18:25 UTC 2026 armv7l GNU/Linux | 新编译时间；未重启操作 |
| /sys/bus/event_source/devices | armv8_cortex_a72、breakpoint、kprobe、software、tracepoint、uprobe | 硬件事件源已出现 |
| pmu/driver | ../../../bus/platform/drivers/armv8-pmu | 已绑定 |
| dmesg PMU 行 | hw perfevents: enabled with armv8_cortex_a72 PMU driver, 7 (8000003f) counters available | 驱动运行证据 |
| /proc/vmstat | 开始/结束均 pswpin=26、pswpout=613 | 本轮两次快照无增加 |

证据 E1 的 identity、fingerprint、pmu、dmesg、swap_before/after。perf header 中板端时间显示 Oct 30，主机记录为 Oct 29；本报告耗时以主机起止或 time 输出计算，不把两端墙上时间直接相减。

### A.2 工具恢复与目录验收

`findmnt -T /opt` 为 `/dev/mmcblk0p3 ext4 rw,relatime`，无 noexec。重刷后 tools/perf 和 lib/libLLVM.so.22.1 均不存在；从既有解包副本恢复，仅 SDB push，不安装 RPM。两端 SHA-256 一致；ldd 全部解析，LD_DEBUG 运行 perf --version 退出0，版本6.12.80。

| 保留路径 | 来源包/主机副本 | SHA-256 |
|---|---|---|
| /opt/afdo_agent/tools/perf | linux-kernel-perf 6.12.80-0.armv7l；temp/rpms/perf-extract/usr/bin/perf | `41b9b9a0d41da1b2a600c84ffa482ea05c52af54af094f5c6a2bf52d6aa13138` |
| /opt/afdo_agent/lib/libLLVM.so.22.1 | libllvm 22.1.8-1.6.armv7l；temp/rpms/llvm-extract/usr/lib/libLLVM.so.22.1 | `49fcc90da72ac2eabd7bbdb0a71566ea2284a532f98730ca46496782f30fb69e` |

使用的是 03 报告已核验的旧工具副本，并非声称工具来自新镜像仓库；新镜像实际依赖解析/运行通过。两个视频亦按本机/板上 SHA 校验，见 E1 push/sha。没有在 /tmp 执行工具、remount、安装/卸载、重启或写 /boot。

### A.3 cycles 采样与 stat

解码命令 L：

```sh
gst-launch-1.0 -q filesrc location=/opt/afdo_agent/work/bbb_720p_h264_60s.mp4 ! qtdemux ! h264parse ! avdec_h264 ! identity eos-after=300 ! fakesink sync=false
```

按30fps在解码端约300帧结束，即约10秒媒体内容，不是强制10秒墙上运行。`time -p P record -e cycles -c 1000003 -o F/fixed.data -- L` 退出0，real=3.31s，保存7,659样本。`P evlist -v -i F/fixed.data`：**type=0 (PERF_TYPE_HARDWARE)、config=0 (PERF_COUNT_HW_CPU_CYCLES)**，没有 cpu-clock 回退。

`P stat -e cycles,instructions -- L` 退出0：cycles=7,427,055,348，instructions=6,869,976,852，IPC=0.92，elapsed=2.364883554s。A 验证通过，B 使用 cycles。原始命令、输出在 E1 fixed_record/fixed_check/hw_stat；普通IP不意味着有分支栈，本轮没有重新验证 SPE/ETM/BRBE。

## B. 板上冻结前核实

### B.1 页大小

`getconf PAGESIZE` 返回 **4096**、退出0，符合设计对 RPi4 Tizen 页大小的预期。RPi5 此项未在本轮执行，不能用 RPi4 替代另一板的冻结前事实。

### B.2 dsoff 语法

按设计命令执行：`LC_ALL=C P script -i F/fixed.data --show-mmap-events --show-lost-events -F pid,tid,event,period,ip,dsoff`，退出0。前200行及20条 libavcodec 样本原文保存在 E2，完整流为 T/fixed_dsoff.txt。样例：

```text
  11948/11948   PERF_RECORD_MMAP2 11948/11948: [0xb612a000(0x55e000) @ 0 b3:02 1702 4080200201]: r-xp /usr/lib/libavcodec.so.62.11.100
  11948/11951      1000003 cycles:          b638637c (/usr/lib/libavcodec.so.62.11.100+0x25c37c)
  11948/11948      1000003 cycles:          c0518110 ([kernel.kallsyms])
```

实际字段顺序是 **pid/tid、period、event:、ip、(DSO+offset)**，不是 -F 参数顺序；pid/tid 十进制合并，ip 为无0x前缀的十六进制，dsoff 为路径后 `+0x` 十六进制偏移。内核 `[kernel.kallsyms]` 样本无偏移；multi 数据中 **`[vdso]+0x...` 确实带偏移**（原行在 E2），不能泛化为所有特殊/非文件 DSO 均不带偏移。本轮未见 `[unknown]` **DSO**；符号输出中的 `[unknown]` 仍有明确 libavcodec 路径，不能混为 unmapped DSO。

### B.3 公式与动态符号

T/analyze_perf.py 是本轮一次性核对脚本，不是拟实现的 LLVM reader：按导出顺序维护每个 pid 的 MMAP2 列表，选同pid、同路径且覆盖IP的最近记录，计算 `ip-start+pgoff`。fixed 的 **6,496/6,496（100%）** libavcodec 样本与 dsoff 一致，无不一致样本，超过1000条要求。例：`0xb638637c-0xb612a000+0=0x25c37c`。worker tid 不同但 pid 相同，按进程映射核对。

拉回新镜像实体 `libavcodec.so.62.11.100` 到 T，两端 SHA-256=`9c72c8cc96dbfd101a03414ff772fe1c6f2f41b4014234869de1be03d6ea5f56`。使用 `temp/GBS-ROOT-RPI5-SPIKE/local/BUILD-ROOTS/scratch.aarch64.0/emul/usr/bin/readelf` 配套加载器/库读取，未使用本机 readelf。可执行 PT_LOAD：p_offset=0、p_vaddr=0、p_filesz=0x2d5c04；全部6,496条唯一落入该段，`vaddr=p_vaddr+(off-p_offset)` 通过。此库两者均0，尚未覆盖不等的段偏移布局。该库没有 build-id。

对同数据 `-F pid,tid,event,period,ip,sym,symoff,dsoff` 独立导出，排除 unknown、PLT（无本DSO已定义 .dynsym 函数区间）后，fixed 仅1条可核对动态函数：

| 样本 | vaddr | .dynsym st_value / size | 原始区间 | ARM Thumb 地址规范化后 |
|---|---|---|---|---|
| fixed_symbols.txt:1429，av_packet_alloc+0x0 | 0x1ff000 | 0x1ff001 /112 | 不命中 | 命中 `(st_value & ~1)` 区间 |

所以严格原始数值命中率为0/1；清除 ARM Thumb 函数符号的状态位后为1/1。**不是 dsoff 公式失败，也不能把裸 st_value 的失败隐藏。** 扩展检查多进程7条、高率219条：原始值分别3/7、103/219，Thumb规范化后7/7、219/219；所有原始不一致样本逐条列于 E2（完整JSON在 T/perf_analysis.json），规范化后无不一致。小样本及动态符号稀疏限制仍存在，不能据此推断内部所有函数/DWARF正确。

### B.4 双进程

`P record -a -e cycles -c 1000003 ... -- sh -c 'L & p1=$!; L & p2=$!; ... wait "$p1" ... wait "$p2" ...'`，两个进程均退出0。pid=12121/12122 的 libavcodec 基址分别 **0xb61d5000 / 0xb6109000**；样本6,662/6,627，共13,289条，dsoff公式与同一可执行PT_LOAD均 **100%** 一致。系统级 mmap 流另有其他已有进程映射，不将其误认为本轮解码子进程。证据 E2 multi_record/ANALYSIS multi。

### B.5 period

| 录制 | 样本数 | sample_type | period 分布 |
|---|---:|---|---|
| cycles -c 1000003 | 7,659 | IP\|TID\|TIME，无PERIOD位 | 全部1000003 |
| cycles -F 1000 | 4,886 | IP\|TID\|TIME\|PERIOD，freq=1 | 4,638个不同值，最小1、最大20,001,473 |

频率模式按区间 `[1,10)、[10,100)、…、[10^7,10^8)` 的样本数依次为 **52、16、4、14、9、368、4,404、19**。与设计的固定周期回退attr值、频率模式逐样本变化一致。完整取值频数表 T/fixed_periods.tsv、T/freq_periods.tsv；E2保留分布摘要/top20及原evlist。没有把指定1000Hz当成每个样本period=1000。

### B.6 --buildid-mmap

record 退出0，stderr见E2；libavcodec 无build-id，其 MMAP2仍打印 `b3:02 inode generation`，未出现 `<id>`；libc有id，打印：

```text
  12425/12425   PERF_RECORD_MMAP2 12425/12425: [0xb6bbb000(0x162000) @ 0 <eaca6bd9055788fd8f7ea36cd4ae91041bbf1a9c>]: r-xp /usr/lib/libc.so.6
```

**buildid-list 不是空：** buildid模式列出libc、ld-linux、kernel的ID，以及多个无ID的DSO空ID列；默认录制列出ld-linux、libc、kernel、vdso的ID。全部原文见E2。新镜像的libavcodec/GStreamer缺ID，不代表所有库或内核都缺ID。

与v0.2“模式A下buildid-list为空”不一致。只读源码补证 `src/linux-rpi/tools/perf/builtin-buildid-list.c:101–108,122–135`：没有 HEADER_BUILD_ID 时设置with_hits并处理事件，包括MMAP2，再打印DSO ID。`--no-buildid` 不能推出 list 命令没有输出。D又验证自建spike的非空MMAP2 ID，与ELF完全一致。

### B.7 丢样格式

1080p完整60秒视频，`P record -e cycles -c 100003 -m 8 ...`，real=32.48s，1,044,541样本，数据31.915MB。采用较小环形缓冲区以提高丢样机会，但实际 **没有产生丢样**；script未见PERF_RECORD_LOST，report原文 `# Total Lost Samples: 0`。E2保留命令/原输出；不能提供未发生的LOST语法，更不能由此宣称冻结前LOST fixture已闭合。未继续无限加压。

### B.8 主机 perf

**无主机 perf**：工作目录现有候选仅内核构建的ARM perf、旧armv7l perf与aarch64 perf；GBS平台readelf核实Machine分别ARM/ARM/AArch64。未发现可执行x86_64 perf，因此跳过同份数据主机/板上逐行比对，未安装。名称搜索有受保护构建根/虚拟proc目录的权限拒绝，未提权；不对不可读取目录宣称完整性。候选与ELF证据见E2。

## C. 主机冻结前原型

### C.1 Tizen clang 默认 profi

使用 RPi5 spike GBS root 的 x86_64 accel clang 22.1.8及配套loader/libs。空profile=`T/empty.profile`，x.c只含`int x;`。两目标分别执行 `clang --target=... -fprofile-sample-use=... -### -c T/x.c`，再分别加 `-fno-sample-profile-use-profi`，四次均退出0：

| target | 默认 cc1 参数 | 显式关闭 |
|---|---|---|
| armv7l-tizen-linux-gnueabi | `-mllvm -sample-profile-use-profi` | 参数消失 |
| aarch64-tizen-linux-gnu | `-mllvm -sample-profile-use-profi` | 参数消失 |

符合预期。`-###` 仅验证driver注入，不编译空profile；没有用空profile成功编译的伪结论。四条完整命令/输出见E3。

### C.2 IR 分支匹配原型

复用前轮 `temp/spike/instr.profdata`（aarch64、2500000轮），源码为原 spike.c 字节副本；人工合成文本 sample profile 覆盖全部11个源码函数（包括internal函数的linkageName），各函数总量50000/head1000，偏移0..39赋值1000+7×offset。计数是任意测试值，**只检查结构匹配，不衡量采样质量/收益**。

两侧相同参数为 `--target=aarch64-tizen-linux-gnu --sysroot=<GBS root> -resource-dir=<同root>/usr/lib64/clang/22 -O2 -gline-tables-only -fdebug-info-for-profiling -funique-internal-linkage-names -S -emit-llvm`；分别追加：

```text
-fprofile-use=T/../spike/instr.profdata -mllvm -print-after=pgo-instr-use
-fprofile-sample-use=T/synthetic.sample -mllvm -print-after=sample-profile -mllvm -disable-sample-loader-inlining
```

实际展开路径见E3，两个clang退出0、无profile不匹配警告；读取的是pass刚完成时stderr中的模块dump，而非后续最终优化IR。首次漏显式resource-dir时stddef.h缺失，原失败保留E3；补同GBS root路径后成功，没有改源码或借用主机头文件。

匹配脚本：[tools/match_ir_branches_prototype.py](../../tools/match_ir_branches_prototype.py)。这是一次性正则解析原型，仅支持本次单module dump中的br/switch；键为函数linkage名＋解析后的DILocation（行/列/discriminator/作用域/内联链）＋后继序号。缺位置或重复键不猜测配对；没有用IR编号或基本块编号跨文件配对。输出JSON到T/ir_match.json：

```sh
python3 tools/match_ir_branches_prototype.py temp/rpi4-prefreeze/pgo_pass.txt temp/rpi4-prefreeze/sample_pass.txt > temp/rpi4-prefreeze/ir_match.json
```

| 指标 | 插桩 PGO pass后 | SampleProfile pass后 |
|---|---:|---:|
| 条件终结指令总数 | 22 | 23 |
| 带branch_weights的终结指令 | 17 | 23 |
| 对应带权后继边 | 34 | 46 |
| 匹配终结指令 / 边 | 15 / 30 | 15 / 30 |
| 匹配率（各侧带权为分母） | 88.24% | 65.22% |

所有未匹配后继原文和原因在E3，概括如下（行号为spike.c源码行，列随DILocation保留）：

| 侧 | 函数/位置 | 未匹配分支数 | 可观察原因 |
|---|---|---:|---|
| PGO | run_workload，内联checksum_block:110 | 1 | sample侧仍为独立checksum_block函数，函数/内联位置键不同 |
| PGO | main，内联initialize_table:55 | 1 | sample侧仍为独立initialize_table函数 |
| sample | checksum_block:110、initialize_table:55 | 2 | 上述反向差异 |
| sample | parse_number:141:24（dump:369） | 1 | 另一pass无同键；相同源码短路表达式经不同阶段处理后的结构不同 |
| sample | main:158:67、parse_number:141:24（dump:365）、146:20、146:35、146:51 | 5 | PGO侧同键存在但没有branch_weights，不作为带权匹配 |

逐侧自匹配均100%，重复键负对照拒绝匹配；已处理文本IR中i32权重的有符号打印。本原型不计算权重概率或质量指标；不能把sample侧65.22%称为设计已要求的“可接受”，v0.2没有给出接受阈值。两pass处于不同阶段/内联状态的事实需要评审；仅按当前键不能覆盖所有分支。

## D. 可选 armv7l spike 与插桩 PGO

限时从23:40:01到23:47:31，共约7分30秒，小于40分钟。临时独立Git源码在 T/spike-arm，仅测试spec的ExclusiveArch改为armv7l；原 spike 源码/spec不改，LLVM不改。GBS配置=`temp/gbs/gbs_rpi4_spike.conf`，沿用旧RPi4配置快照Unified20261022.054557/Base20261020.074527，独立buildroot=`temp/GBS-ROOT-RPI4-SPIKE`。**不是新镜像同期工具链的额外证明**；按本任务使用现有配置变体，实际运行ABI兼容通过。

整段setsid worker，GBS子进程setsid --wait，nice19/ionice3、单包threads1、_smp_mflags=-j2；HOME/GIT_CONFIG_NOSYSTEM隔离仅GBS及子进程。两轮日志与结束标记在E4、T/logs/：

| 构建 | 开始 → 结束（+08:00） | 退出码 | 结束标记 |
|---|---|---:|---|
| base/instr | 23:40:01 → 23:43:48 | 0 | ALL-END ... OK |
| 以本板profile重编pgo | 23:46:21 → 23:46:38 | 0 | ALL-END ... OK |

从RPM解出base/instr/pgo，用GBS平台readelf确认ELF32 ARM，build-id和.debug_line存在；没有只核对打包前文件。base的GNU build-id为 **c0b79348eade7bedbe988a295bd7d8a765128b10**，板上`--buildid-mmap`记录的MMAP2：

```text
  15336/15336   PERF_RECORD_MMAP2 15336/15336: [0x4d0000(0x1000) @ 0 <c0b79348eade7bedbe988a295bd7d8a765128b10>]: r-xp /opt/afdo_agent/work/spike-base
```

与ELF完全一致；该data的buildid-list也非空，包含spike、libc和kernel（E4）。正好补足无ID的libavcodec之外的非空情况。

插桩链路：`LLVM_PROFILE_FILE=F/arm-instr-%p.profraw F/spike-instr 200000` → 拉回 `T/arm-instr-15397.profraw`并校验 → GBS平台`llvm-profdata merge`生成T/arm.profdata → show确认7函数/31计数块 → 转文本到临时测试源码、提交 → GBS以`-fprofile-use`重编且启用profile缺失/过期为error → 拉取RPM中的pgo运行。各步退出0，完整命令/原输出见E4。

| 运行 | 输出 checksum | 结果 |
|---|---|---|
| base 200000轮 | ff818b861cb93a67 | exit0，real3.25s |
| instr 同轮数 | ff818b861cb93a67 | exit0，profraw成功 |
| pgo 同轮数 | ff818b861cb93a67 | exit0，real3.21s |

三者 seed=0123456789abcdef；一致性通过。仅单次、小输入工具闭环，不据0.04s差异认定性能收益或真实包泛化。所有二进制、RPM、perf.data、profraw/profdata只留temp。

## 对设计的影响（只陈述事实，不修改设计）

1. **5.2.1/5.3.2：模式A的buildid-list为空预期不成立。** 缺HEADER_BUILD_ID时该命令还会处理MMAP2，实际非空；无ID库也可能打印空ID列。不能用list是否为空来推断采集模式或身份来源。
2. **5.2.2：特殊DSO并不一律无偏移。** 本次 `[vdso]+0x...` 有偏移，kernel.kallsyms无偏移；未知DSO语法未取得。特殊DSO分类与“有无偏移”不是等价条件。
3. **ARM动态符号验证需区分Thumb状态位与地址。** dsoff/PT_LOAD公式100%一致；裸st_value区间产生失败，清除函数符号低位后全部命中。不以此修改设计现有ARM/Thumb约定，但测试判据不能忽略该位。
4. **5.8/第10节步骤1：当前IR键只能部分对齐。** 15/17与15/23，存在内联位置差异及无权重分支；任意计数profile没有统计质量意义，是否可接受由评审决定。
5. **尚未取得的证据：** LOST实际语法、主机perf逐行一致性、RPi5板上页大小本轮未闭合。不能用“本次未丢样/未找到工具”替代对应冻结条件。
6. 符合预期：RPi4 4096页、真硬件cycles、dsoff多进程归一化、固定/频率period、Tizen默认profi及显式关闭；armv7l插桩PGO前置条件已完成小程序闭环。

## 清理、文件位置与执行限制

| /opt（df -k，KiB） | 已用 | 可用 | 使用率 |
|---|---:|---:|---:|
| 开始 | 33,752 | 1,271,836 | 3% |
| 采样结束快照 | 434,496 | 871,092 | 34% |
| 最终清理后 | 70,628 | 1,234,960 | 6% |

已 `find /opt/afdo_agent/work -mindepth 1 -delete` 并验证空目录，删除视频、data、文本、spike/profraw、registry/cache和查询文件。work目录本身4KiB，/opt/afdo_agent合计35,796KiB，保留A.2两个工具供后续使用；RPM数量前后均1252。没有重启、改挂载、装卸RPM。证据E1 cleanup/disk_after/retained。

主机原始数据位于 T/{fixed,multi,freq,buildid,lost,arm_spike}.data；完整导出、period TSV、公式/符号核对JSON及IR均在T。IR匹配原型在tools/；临时B分析脚本仅在T。样本/权重分布摘要截取不改变完整数据。用户设计v0.2 SHA-256保持不变。

执行中保留的失败/限制：初次time调用127；首次IR缺resource-dir；一次并发查询复用了capture文件导致lost导出元输出混入libavcodec哈希，已改为独立capture文件并重导出，同一data的导出SHA一致。初次RPM解包误落到WORKDIR/usr，随即将这两个新生成文件和目录移至T/arm-base-extract，WORKDIR/usr已不在；未写到WORKDIR外，但属于临时数据应直接放temp的执行偏差，已记录。上述均未修改LLVM或设计。

本轮未新增已知工作区外项目文件；既有SDB共享服务外部日志的历史例外继续保留，受本轮禁止读取外部文件约束未再stat外部日志，不能确认daemon隐式更新情况。没有对Downloads或其他外部项目输入进行读取。
