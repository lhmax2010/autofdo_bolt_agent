# Codex：K1 与 ARM 内核 AutoFDO 能力方案评审

日期：2026-11-18。结论：**需修改后执行**。

RPi4 上先做 A32、非 LTO、非 MFS、仅 vmlinux 的 IP AutoFDO，技术方向成立。现有材料证明了原样 GBS 构建、PMU cycles 采集和内核 IP 转换组件的若干离线能力，尚未证明优化内核能启动、profile 在完整内核中的匹配质量或性能收益。必须先补齐版本命名与打包、模块消费隔离、真实启动分区与恢复流程，再冻结采集和跨重启测量协议。

总体方案需要调整优先顺序：**A72 的退休分支事件不是可靠的现成入口；先做 IP 基线、已有 Profi、局部 gcov 参考数据和尺寸收益核算，比先开发“分支目标采样”更有依据。**

## 1. 材料版本、核实范围与限制

本地 HEAD 为 `a321fa017cd461f39d68680fb7dac0d879aff513`，缺少 `06_k1_design_v0.1.md` 及部分 K1 报告，且已有用户改动。为遵守只读要求，没有 pull、checkout 或改动这些文件。通过 GitHub 只读接口取得远端 main，并固定在 **`6d8b116a77c422aa5ffc7af5aadec1916d553772`** 阅读两份设计和 03–05 报告；K1 主文档 Git blob 为 `c398c9f18cf4073f01be5b69af73750912a1ca43`。本文评审的是该版本，非假定本地缺失文件已经同步。

实际核对：

- 两份被评审设计；K0 与回移植清单中的构建、地址、模块、消费和内存章节；K1a 构建报告、基线/HDMI 报告、K1b 报告；workflow v0.3 的统计与遥测契约。
- 本地 `temp/kernel-afdo-k1/base-0fac5de6/source/`，HEAD 为内核 **`0fac5de6a63091d141ad1cd3ed9d9e92b8dde708`**。下文 `K:` 文件行号均指此树，包含该树的 perf 6.12.80。
- `src/llvm/`，HEAD **`f999bd406c0a70fe8107aa992164fe6945c5d46a`**，Tizen LLVM 22.1.8。下文 `L:` 行号均指此树。
- `temp/kernel-afdo-k1/profgen-k1b/llvm/`，HEAD **`5a541f22082b963a368f065d6150eee0afae4e30`** 的相关生成器、CommandGuide；这是针对设计契约的抽查，不是补丁十的全面代码评审。下文 `P:` 指此树。
- K0 保存的上游补丁，尤其 `315ad8780a12`、`0043ecea2399`；没有把累计应用了其他补丁的临时工作树误当成原始上游版本。
- 本地构建 `logs-04/result.json`、基线 `memory.c`、`workload.sh`、`runner.sh`、`source-identity.sh`、`identity-compare.json`、HDMI `summary.json`，以及原始 BASE 的 `System.map` 和配置摘要。没有重算正式性能效果。
- Arm A72/A76 TRM 的相关硬件描述、LLVM Profi 上游评审、内核 PGO/coverage 邮件和 OpenCSD 的公开材料，链接随相关结论列出。

未核实：本次没有接板、构建、执行部署/重启、运行编译器探针、读取正式 sample profile，亦未全面重验全部归档的哈希或所有原始遥测。A76 板上事件可用性、ETM 完整采集链、ARM32 插桩运行时可用性仍未核实。只新增本评审文件，不提交、不推送。

文中 **已证实** 指源码、手册或已有记录直接支持；**推断** 指基于这些事实的工程判断；**待验证/不确定** 不作为既成结果。

## 2. K1 设计 §11：逐条回答

### K1-Q1：首版不开 function sections 是否合理？

**同意这个取舍，但验证方法要改。**

已证实：L:`llvm/lib/CodeGen/CodeGenPrepare.cpp:180–182,579–603` 默认启用 profile 引导的 section prefix；L:`llvm/lib/CodeGen/TargetLoweringObjectFileImpl.cpp:657–688,938–954` 将前缀与“是否每函数独立节”分开处理。因此不必开 `-ffunction-sections` 才能产生 `.text.hot.` / `.text.unlikely.` 等输入节。显式指定 section 的内核函数另有处理，不能期待所有热函数都移动。

K:`include/asm-generic/vmlinux.lds.h:561–569` 已接收这些输入节；K:`arch/arm/kernel/vmlinux.lds.S:62–65` 最终把它们合入输出 `.text`。**只看最终 vmlinux 节表找不到独立 `.text.hot`，不能据此判定优化没有发生。** 应检查目标 `.o` 输入节、最终链接 map 和冷热边界符号。见 I6。

保留 ARM32 的 MFS 禁用：L:`clang/lib/Driver/ToolChains/Clang.cpp:6237–6245` 明确只允许 x86/AArch64 ELF。当前 K1 不应承担 MFS、ThinLTO、全局 function sections 三个额外变量。

### K1-Q2：并存、复制 zImage、重启是否可靠？

**有条件可行，按现稿尚不能自动执行。**

实际记录显示 `/boot` 未挂载；启动链是固件加载 U-Boot，再由脚本选择 zImage。往根文件系统的空 `/boot` 复制文件可能根本不改变下次启动内核。不同 LOCALVERSION 还与现有 RPM `%files` 后缀冲突。见 S1、S2。

第一版可保留文件切换，先验证真实分区、备份、模块索引、完整回退，再采用“同文件系统暂存、校验、同步、替换、复核、重启、运行身份复核”。这降低正常操作中的半写入风险，不应声称 FAT 掉电事务安全。

U-Boot 按独立文件名选择内核可以减少每轮重写大镜像，值得后续采用；但必须先核实当前 `boot.scr.uimg` 是否覆盖环境变量、环境存储布局以及 bootcount/回退支持。**未核实，不能直接推荐执行 `fw_setenv`。** kexec 也不是本轮默认替代品：它改变固件/设备初始化路径，不能直接与完整重启混用。

### K1-Q3：训练/测试和主次基准是否合理？

**pipe 适合作为首次机制验证的主比较；不足以代表 TV 产品整体。**

K1a 证实 pipe 的任务 cycles 以内核为主、波动相对较小，但它是固定 CPU 上两个进程的短消息往返，不是通用调度、跨核 IPC 或媒体性能。K:`tools/perf/bench/sched-pipe.c:180–190` 消息固定为 `sizeof(int)`；改变消息大小并不是现有命令提供的选项。可用不同 loop 数/独立训练脚本，不能把这称为独立内核路径。

“syscall 训练占比低”不是留出。若要称留出，就从训练中完全移除并预登记；否则称低权重训练内测试。ToS 解码是相关性/回归对照，既然运行在内核上，也不是严格的零效应负对照。

内存触页可保留为次比较，但需消除/分离人为休眠，写清 CPU/cgroup、工作集和计时边界。现有试验没有触发 reclaim/zram，不能据它宣称内存压力性能或节省 RAM。见 I3、I4。

### K1-Q4：按文件开启 consumption 优化记录是否可行？

**可行，但“按文件追加 KCFLAGS”应改为目标对象 CFLAGS；“有正数 AppliedSamples”只能证明最低限度消费。**

K:`scripts/Makefile.lib:125–140` 提供 `CFLAGS_<target-stem>.o`。`KCFLAGS` 是全局入口，不是天然的逐文件选择器。L:`clang/lib/Driver/ToolChains/Clang.cpp:1255–1267,1326–1333` 支持 YAML 及 pass 过滤；L:`llvm/include/llvm/Transforms/Utils/SampleProfileLoaderBaseImpl.h:428–443` 的 remark 名为 `AppliedSamples`，正整数位于 `Args.NumSamples`，不是一个叫 AppliedSamples 的数值字段。

按对象路径生成诊断清单，双变体保持相同诊断选项，保存独立 YAML；报告代表函数的匹配与未匹配原因，代码差异排除地址/版本字符串等非优化因素。正数 remark 与“确实更快”是两道独立门禁。见 I6。

### K1-Q5：时间估计和遗漏风险？

**4–6 人周作为从零开始的预算可理解，不能继续把已经完成离线交付的 K1b 当成尚需整段重做。** K1b 报告已记录提交、回归和合成 BASE 验证；剩余关键路径是同 boot 实采、真实 profile 匹配、ARM32 消费构建、启动恢复和跨重启测量。

已证实的一次原样 GBS 构建约 67 分钟，不意味着新补丁只需同样时间就能交付。遗漏/低估项包括：LOCALVERSION 打包、模块误消费、同名静态函数、启动分区未挂载、启动失败分类、IRQ 延迟归因、跨启动方差、performance 下重新升温、内存测试休眠，以及冻结 snapshot 的实体可恢复性。补完这些后再做一次排期，按“主机验证通过/首次可恢复启动/实采消费通过/测量协议锁定”分门槛；6–8 小时正式采集只能是无故障情况下的估计。

## 3. 必须修改与重要问题

### S1 — 严重：LOCALVERSION 与现有 GBS 打包契约不兼容

**位置：** K1 §0.2、§2、§4。

**已证实的依据：** K:`packaging/linux-rpi.spec:180–201` 写 `localversion-tizen` 并从 defconfig 重生成配置；defconfig 第 1 行为 `CONFIG_LOCALVERSION="-v7l"`。K:`scripts/setlocalversion:174–208` 将命令行 `LOCALVERSION` 接在现有版本尾部。spec 第 351–362 行的普通/RT 模块文件清单分别仅匹配 `*arm-rpi4-v7l/`、`*arm-rpi4-rt-v7l/`。直接追加 `-kbase/-kafdo` 不再匹配。把完整旧后缀替换为 `CONFIG_LOCALVERSION=-kbase` 同样不能保持匹配。

**影响：** 原 spec 原样完成 RPM 归档的承诺不成立；仅改构建命令不能自动解决。不同 release 也会改变生成头、vermagic 等，严格的“两个内核只差 profile”不成立。

**建议修改：**

```diff
- 同一 spec（仅 LOCALVERSION 与 profile 不同），两个内核只差 profile。
+ 使用同一份已评审的 K1 spec，参数化变体标识与 profile。
+ 显式登记普通/RT 的完整 kernelrelease；%files 精确匹配相应模块目录，
+ 不用覆盖全部模块的宽泛通配。所有 olddefconfig/build/install 阶段保持同一 release。
+ “只差 profile”改为“优化选项只差 profile；允许列举的身份元数据差异”。
+ 固定 KBUILD_BUILD_TIMESTAMP/USER/HOST/VERSION、源码路径及依赖；
+ 对身份元数据以外的配置、逐对象编译参数和模块代码差异作检查。
```

也可把实验标识放在 `localversion*` 的前缀位置，保留 spec 末尾匹配规则；两种方案选定一种后冻结，不能临时手工改名模块目录冒充新的 vermagic。

**验收：** spec 展开/文件清单夹具覆盖普通和 RT；预期 kernelrelease、模块 vermagic、模块路径、包清单一致；构建无缺失/未打包文件。该共同适配进入两个变体；它不是 AFDO 单边补丁。

### S2 — 严重：切换没有闭合真实 boot 分区、恢复与失败状态机

**位置：** K1 §3.3、§4、§6.3。

**已证实的依据：** `04_k1a_baseline.md`“运行身份与配置”“历史 PMUv3 构建来源核对”：`/boot` 空且未挂载；当前 kernel/modules 未登记于 RPMDB；历史 RPM 与运行镜像不匹配。本地 `baseline-rpi4-02/source-identity.sh:33–50` 也是通过任务目录只读挂载实际 FAT 分区后核验。`03_k1a_base_kernel_build.md §4.4` 是 RPM 安装路径的恢复规则，而 K1 §4 明确不安装 RPM，不能直接照搬“先恢复 RPM 包状态”。

此外，§4 说重启超时停止请用户处理，§6.3 又把重启超时列为整 block 重试一次，两个动作矛盾。候选内核启动失败不能被当作普通测量缺失、重试后忽略。

**建议修改：**

```diff
- cp zImage-<variant> zImage → sync → reboot；重启超时整 block 重试一次。
+ 先识别并登记 boot 分区 UUID/active slot/挂载点和完整启动链。
+ 未确认目标为实际启动分区时禁止写入；挂载权限与恢复办法在部署方案中明确。
+ 完整备份并验证当前真实 boot 文件、PLAT 模块树和索引，不假定旧 RPM 可恢复当前系统。
+ 在同一启动文件系统暂存候选、校验 SHA、同步后替换；替换后再读回校验。
+ 每次成功启动验证 boot_id 已变化、运行 build-id、完整 uname-r、cmdline、
+ DTB/显示状态、模块路径/索引及已加载模块身份。
+ boot 超时、身份错误、oops 或模块失败进入 STOP/RECOVERY_REQUIRED；不自动重试。
+ 只有已证明内核正常、且没有测量值的外部传输故障，才允许一次整 block 重试。
+ 文件部署按文件备份恢复；RPMDB 原先无包时不人为创建旧包安装状态。
```

**验收：** 部署脚本的离线夹具涵盖空 `/boot`、错误 slot/UUID、缺少模块索引、错误镜像、替换未完成、网络丢失但正常启动、真正启动失败。正式计时前实际走通一次 K-BASE→PLAT 恢复；其板上执行另行授权。保存状态日志，禁止失败 block 被静默替换为成功样本。

### S3 — 严重：仅生成 vmlinux profile，不等于仅让 vmlinux 消费它

**位置：** K1 §0.1、§2、§3.1、§5。

**已证实的依据：** 上游 `315ad8780a12` 补丁的 `scripts/Makefile.lib` hunk（本地补丁第 393–400 行）用 `is-kernel-object` 决定默认 AutoFDO flags；K:`scripts/Makefile.lib:223–227` 定义它为 `part-of-builtin OR part-of-module`。因此仅设置 `CONFIG_AUTOFDO_CLANG=y` 和全局 `CLANG_AUTOFDO_PROFILE`，默认也给模块传 profile。普通/RT 又由 spec 同时构建。

**影响：** 模块可消费主映像同名函数记录，或者因缺失记录受到 profile 推导影响；这超出“只覆盖 vmlinux”的实验范围。未证明一定发生错误匹配，但当前配置确实未隔离。

**建议修改：**

```diff
- profile 只覆盖 vmlinux；模块 profile 不在本阶段。
+ profile 的采集、生成和消费均限定于普通内核 vmlinux。
+ Kbuild 适配显式把 profile-use 限于 built-in 对象，并保留现有逐文件/目录排除；
+ 模块和 RT 不得使用该 profile。不要通过全局 KCFLAGS 绕过此限制。
+ 模块两侧使用相同无 profile 优化选项；release/vermagic 等身份差异单列。
```

**验收：** 逐对象 `.cmd` 核对 built-in、模块、host tools、RT、特殊入口/压缩启动对象的 flags；构造 built-in 与模块同名函数但相反热度的夹具，证明模块没有消费记录。模块 manifest 及实际加载身份纳入每次启动验收。

### I1 — 重要：缺少跨 CU 同名静态函数和路径稳定性门禁

**位置：** K1 §2、§5、§7；总体方案 A1/B1。

**依据：** L:`clang/docs/UsersManual.rst:2580–2599` 专门说明 `-funique-internal-linkage-names` 用于避免内部符号名冲突，且仅 best-effort；L:`clang/lib/CodeGen/CodeGenModule.cpp:509–518` 将主源文件路径用于哈希，并处理 macro prefix map。P:`ProfileGenerator.cpp:410–429,1064–1085` 构造以函数身份/行偏移为键的 profile，不把 CU 自动当作额外隔离维度。

本次只读 BASE `System.map`，发现本地 text 名 `init_once` 14 个、`type_show` 13 个、`local_bh_disable` 96 个。部分是相同头文件实例，不能一概判错；但证明“全内核名字天然唯一”不成立。实际哪些进入将来 profile，尚未核实。

**修改：** 在两侧共同启用并验证 unique internal names，固定 GBS 中主文件路径和相应 prefix-map；同时做 DWARF/linkage name/CU 对账。若该选项破坏内核按名字查找/汇编引用等约束，应选择经验证的排除/映射方案，而不是无声合并。只排除确定歧义的函数，不把所有头文件副本一律误判冲突。

**验收：** 两个源文件定义同名 static、不同分支行为；头文件重复实例；不同构建目录但相同规范化路径；名字后缀规范化不应重新制造冲突。列出被排除样本量和实际消费的匹配名字。训练完成后再改变命名规则必须重建训练内核并重采。

### I2 — 重要：把单次启动内 CV 直接搬到跨重启配对，预算与稳定性证据不足

**位置：** K1 §6.2–6.4。

**已证实：** K1a 的 10 轮是在同一运行内核/boot 内完成；正式实验每个变体每个 block 都重新启动。现有 CV 未包含服务启动、内存初态、设备状态等启动间变异。workflow 的公式本来也注明是预算、不是 power 保证；K1 应保留这个限制。单纯 N 低不会自动使 bootstrap 错误，但不能承诺因此能判出 1%。

**修改：** 正式前做若干独立重启的 K-BASE A/A block，而不是仅同一次启动内 10 次计时；每次至少两次内部重复，用于分离启动内/启动间噪声。锁定 N、AB/BA 平衡表、计时器、失败规则、分析代码，再开始正式比较。正式 N 达上限后精度仍不足就 inconclusive，不追加至显著。

以“启动对”为统计单位；若每 boot 多轮，先按预定规则在 boot 内汇总，再对 block 重采样，不把内部重复当成独立 N。分两天运行时每个会话内部平衡 AB/BA，报告会话效应；若预先分层，则固定各层权重并在层内 bootstrap。60 秒是最低等待，另记录预先定义的服务就绪和背景负载稳定条件，不能只因时间到了就认为稳态。

ε=1% 可以保留为工程上有意义的阈值，不能同时解释为误差精度或统计显著性。保留 workflow 的 log-ratio、expm1、边界严格比较，并报告 t 区间、原始配对数据及 A/A 结果。

**验收：** 合成输入覆盖重启间共同扰动、AB/BA 顺序效应、会话差异、重复观测、缺失/遥测标记、恰好 ±1% 的边界；boot 失败按 S2 处理。不同 kernelrelease 标签导致的元数据差异应明确披露，必要时增加无 profile 的标签对照。

### I3 — 重要：内存触页的墙钟混有大量固定休眠，不能作纯 fault/memcg 指标

**位置：** K1 §6.1、§6.5、§7；K1a 内存测试沿用部分。

**已证实：** `temp/kernel-afdo-k1/baseline-rpi4-02/memory.c:29–44` 每个 worker 有 `8×20 + 250 + 8×10 = 490 ms` 显式休眠；同时计时还含 fork、验证、munmap 和调度。K1a 整轮约 1.8 秒；不能从 CPU cycles 中 97.9% 属于内核推出墙钟也有同样占比。多个 worker 的休眠会重叠，不能直接把四倍 490 ms 从整轮相减。

**修改：** 若保留旧负载，命名为“分批匿名内存分配/保持/释放场景”，不把 MiB/s 称为页错误处理吞吐。另定义固定页数、无主动休眠的 fault 阶段，预定是否包含 fork/mmap/munmap、是否四进程都在 CPU3，校验在计时外或在两侧相同位置；报告 task-clock、minor faults、页数和阶段墙钟。旧/新结果不能合并，重新预试。

**验收：** 页数/校验和相同、计时窗口内无主动 sleep、各 worker affinity 和 cgroup 相同；无 swap/reclaim 时不声称验证了这些路径。采样器对不到两秒的小测试可能是实质扰动，可增加固定重复工作量，避免只依赖两三个遥测点。

### I4 — 重要：训练配方、用户态工具身份、留出与遥测起跑条件尚未锁定

**位置：** K1 §5、§6.1、§6.4、§7。

**依据：** “每段固定时长、R=3”与“输入三次采样”没有说清是五个负载各三次，还是三套混合 suite；`max` 聚合又不是线性运算。P:`ProfileGenerator.cpp:423–429` 按行取最大值，所以“先合并地址计数再 max”通常不同于“逐 RUN max 后合并 profile”。各段等时长也不等于等权，更不等于 TV 产品使用权重。

K1a 在 powersave 降温后等待 3 秒，仍有 18/50 计时轮起跑标记（报告重试章节）。这已证明“切回 performance 等 3 秒”本身不是温度门禁。另有两份内核各自产出的 perf，如果随内核切换用户态工具，会破坏 A/B 归因。

**修改：**

```diff
- 每段固定时长，R=3；三次采样生成 profile；syscall 部分留出。
+ 冻结训练清单：每种负载的输入 SHA、参数、CPU/cgroup、时长或操作数、重复数、权重。
+ 明确选择“逐录制转换后以登记权重合并”或“同 boot 地址计数聚合后转换”，不混用。
+ 每份原始采集登记 boot_id、vmlinux/build-id、mmap、evlist、LOST 与质量报告；
+ 显式指定 event、period 权重及共同 ip-period-unit=1000003，不准缺失身份豁免。
+ 不同 boot 的文本不直接拼接；最终 profile、llvm-profgen/llvm-profdata 版本与 SHA 锁定。
+ 两变体共用同一份 perf、worker、用户态 DSO 和测试输入，明确 affinity 与 cgroup。
+ syscall 若称留出则不进入训练；否则改称低权重训练内检查。
+ 每轮在 performance 下、遥测窗口真正开始前复核温度和频率；超时记缺失/停止，
+ 不把 powersave 下先前达标当作正式起跑合格。训练与测量均保持同一显示状态。
```

“max/none/none/none”可以继续作为已批准保守策略，本评审不重开工具默认值。应把全部实际 CLI 参数展开到收据，避免后续默认改变。

**验收：** 合成两 RUN 在同一行不同地址上分别取高值，证明所选合并顺序稳定；跨 boot/缺 build-id/错误事件拒绝；perf 与 worker SHA 不随内核改变；performance 切换后温度反弹、遥测缺边界、低于上限但超过起跑阈值均有确定分类。定义质量“样本不足”的预登记量化条件，至少报告 usable/target、汇编/无 CU/无行号/特殊节/模块损失，不能只看转换退出 0。

### I5 — 重要：ARM 内核 IRQ 延迟造成的采样偏差被低估

**位置：** K1 §5、§9–10；总体方案 A1/A2/B2/E1。

**已证实：** K:`drivers/perf/arm_pmuv3.c:831–886` 在溢出 IRQ 中取 `get_irq_regs()`，传给 `perf_event_overflow`；没有在这里提供被溢出事件指令的精确 PC。基线 pipe 样本 26.621% 落在 `_raw_spin_unlock_irqrestore`，另有 `arch_local_irq_enable`（`04_k1a_baseline.md` pipe 前 30）。

**推断：** 关中断区间的事件可能延迟到重新开中断附近才被采到；这些尖峰可能有延迟投影，不能全部解释成解锁函数自身执行成本。实际偏差大小未核实，也不能反向断言这些热点全是假象。这一问题比“固定回退一条 A32 指令”更大。

**修改：** 保留 IP E2E，但把 profile 定义为“PMU IRQ 可观测位置的热度估计”，明确不是无偏的边计数。训练阶段增加固定周期敏感性/独立短诊断，报告 IRQ-enable/restore 周边聚集、汇编与未符号化份额；不要根据效果挑选周期后继续称原计划验证。需要校正时另立 K2 假设，不在 K1 中事后改写热点。

**验收：** 后续合成受控负载区分普通循环、访存停顿、已知长短临界区，比较采样 PC 分布与独立事件/参考计数；保持调试改动不进入正式 A/B。正面消费和真实性能结果都要报告，不能把高 usable 比例等同于高 profile 准确率。

### I6 — 重要：section 与 consumption 的验收会产生假阴性或过弱的通过

**位置：** K1 §3.2、§7、§9.3。

依据见 K1-Q1/Q4。只看最终节表可能漏判冷热输入节；任意一条正数 remark 又不足以说明前 30 个重要函数有效匹配。顶层同名函数、内联头文件实例、显式特殊节和汇编代码也不能简单对应成“30 个源文件”。

**修改：** 热冷布局查看输入对象节和最终链接 map；使用 DWARF/CU/对象路径选择诊断对象，逐对象 `CFLAGS_<stem>.o` 添加 YAML/pass 过滤，两侧相同。YAML 检查 `Pass: sample-profile`、`Name: AppliedSamples`、`NumSamples > 0`，列明样本匹配覆盖及失败原因；保留 chroot 内 profile SHA 和实际编译命令。代码差异用按函数/重定位规范化的反汇编或结构差异，不能只因 build-id/地址不同就认定消费有效。

不要要求每个热函数必有机器码变化：正确消费后没有优化机会是合法结果；也不能把某个不相关函数变化当作全部消费证明。修改后明确“工具链打通”和“性能获益”两个结论。

**验收：** 正/零/缺少 AppliedSamples、错误 pass 名、同名对象、仅重定位变化、内联函数、显式 section 和没有独立输出热节的夹具；观察诊断选项是否改变产物，若会改变，应采用两侧一致设置或验证专门取证构建与正式产物等价。

### I7 — 重要：内存收益口径与“PGSO 放 K2”的说法不准确

**位置：** K1 §0.5、§6.5；总体方案 D1/D2。

**已证实：** L:`llvm/lib/Transforms/Utils/SizeOpts.cpp:18–25` 中 PGSO 默认启用且带工作集等条件。K1 可以不调参，但不能声称带 profile 的编译完全不涉及 PGSO。K:`arch/arm/kernel/vmlinux.lds.S:55–89` 有 section/page 级对齐，init 又有单独生命周期。K0 §6.3 已正确说明 `.text` 缩小不等于等量 RAM 节省，总体方案反而退回了错误说法。

**修改：**

```diff
- 尺寸优化（PGSO 等）放到 K2；text 体积下降直接等于内存下降。
+ K1 不进行额外尺寸调参；记录 Clang 22 默认 PGSO 与 profile 引起的尺寸变化。
+ 分列压缩 zImage、ELF 可装载代码/数据、调试信息、对齐空洞、启动后保留页、
+ init 回收与已加载模块的内存。text 字节减少不保证释放同等 RAM。
+ /proc/meminfo 在固定就绪状态和负载阶段取样；MemFree/MemAvailable 差异只是整板观察，
+ 不单独归因为 AutoFDO。库同时报告 RSS/PSS 和文件页触及范围。
```

**验收：** 构造“text 少一些但仍占相同页”“跨页边界释放页”“init-only 变化”三个核算夹具；报出高端/低端内存相关口径，不把 vmalloc 虚拟区间和常驻内存混用。静态尺寸不需要统计 CI，动态整板内存若比较则按相同 boot/block 状态配对。

### I8 — 重要：总体方案对硬件、数据格式和插桩“真值”的承诺过强

**位置：** 总体方案 §0、A2–A5、B1/B3、§4–5。

此项不阻塞修正后的 K1 IP 路线，但必须修正再作为 K2 研发依据。详细证据与替代路径见下一节七个问题：

- A72 TRM 不支持把 `0x21/0x0c` 当作现成退休分支来源；普通 PMU 溢出也不是 branch target record。
- A76 只支持 EL0 的 AArch32，不能运行方案描述的 ARM32 内核。
- 单个 sample profile 无直接任意 CFG edge 表，B1 需要明确降维或编译器消费者，而非承诺不丢信息融合。
- LLVM 采样插桩使用 TLS；它既非直接可用的 ARM32 内核功能，也非无误差真值。
- pseudo-probe 改善位置身份不等于自动获得动态 calling context；A4 不必经过 LBR 生成链，B3 不是所有路线的共同前置。

**修改：** 将这些“可实现/中高可行性”改成有独立硬件/语义/运行时门禁的研究项；删除 A2 是必须收益来源、A4 是精确真值及 B3 普遍必需的表述。优先次序采用 §5 的阶段建议。

**验收：** 每条研究路线先有最小夹具：事件不可用必须停止；间接跳转/未取分支不能伪造 target；CFG 不可辨识必须报不确定；采样插桩与未采样参考分开；ARM32 链接不得遗留用户态 TLS/runtime 依赖。

### G1 — 一般：补丁数量与完成状态需要更新

**位置：** K1 §0.1、§3.1、§8；总体方案 C2。

“7 个核心补丁”原清单含两项 Propeller，K1 又明确排除它们，目前实际只列出五个 SHA 加“必要修正”。MFS 补丁引入后 ARM 又禁用，也需要说明保留理由。K1b 已有报告，不能还只有“进行中”的笼统状态；C2 的 ARM32 MFS/ThinLTO 待核实也已被 K0 部分回答。

建议改为逐 SHA 的纳入/排除/适配表，不以数字代替构建输入。对 K1b 分列“离线交付已完成”和“真实同 boot E2E 未完成”；列清必须运行的现有回归及新增 ARM 验收。无需因此扩张首版范围。

### G2 — 一般：GBS 资源与 snapshot 恢复方案应显式继承已验证做法

**位置：** K1 §2、§8。

K1a 已证实单传 `-j2` 不限制 perf 的内层 JOBS，K:`tools/perf/Makefile:19–31,65` 会重置并行度；把 `JOBS=2` 塞入 `_smp_mflags` 又会污染 find-debuginfo 参数。直接引用 K1a 最终 attempt-04 的 build/install 环境覆盖、资源门禁和结束收据，不重复试错。

“冻结仓库”必须包含能重建 root 的实体、元数据、buildconf 和所有依赖 RPM SHA，不仅是会被删除的 snapshot URL。K1a 已归档 130 个依赖，复用前核对实体与 root 清单，禁止失败后自动切新 snapshot。验收用离线/缺包清单检查即可，不要求本轮再构建。

## 4. 总体方案 §7：逐条回答

### ARM-Q1：A2 在 A72/A76 可行吗？skid、事件、公开先例？

**A72：以文中两个事件为前提，不成立；整个“弱分支信息”方向不因此被证明不可研究。**

已证实：Arm A72 r0p3 TRM §11.4.2 Table 11-5（页 11-404/405）把 `PC_WRITE_RETIRED=0x0c` 的实现位列为 0，`PMCEID1_EL0[31:0]` 为保留，不能把 `BR_RETIRED=0x21` 当作已支持。该寄存器说明同时覆盖 AArch32 映射。[Arm 原始 TRM 的公开镜像](https://www.scs.stanford.edu/~zyedidia/docs/arm/cortex_a72.pdf)

本地 K PMU 驱动对通用 branches 先查 BR_RETIRED，再查 PC_WRITE_RETIRED，没有则返回不支持（`drivers/perf/arm_pmuv3.c:1083–1097`）。用 raw `r21/r0c` 不等于证明硬件实现；应检查事件源/PMCEID 证据及已知循环计数，不把命令接受当作能力通过。本轮没有板测，不能替板上作实际计数断言。

A76 实际事件可用性本轮未核实，应独立探测；即便可用，两种事件也不是同义量，退休分支可能含未取条件分支，PC 写事件不等于完整 block entry。Linux 对通用 branches 的变更明确区分了二者。[上游 PMUv3 事件映射说明](https://lists.openwall.net/linux-kernel/2024/09/06/1427)

skid 没有在本材料中得到可移植的固定指令数上界；中断屏蔽还会放大内核偏差。普通 IRQ PC 不能恢复唯一 branch source/target；把当前位置就近吸到块首，不能补回多前驱边的流量。先做已知分支比例、可调后续指令/访存延迟、周期变化的合成循环，比较偏差和跨负载稳定性，之后才考虑 FFmpeg。

已核实的相关工作是 **Profi / Profile Inference Revisited**，不是 A72 退休事件 branch-target sampler。它解决 CFG 上缺失/不准计数的推断；不能据此声称新方案没有公开先例，也不能假称已有可用实现。[论文介绍](https://popl22.sigplan.org/details/POPL-2022-popl-research-papers/52/Profile-Inference-Revisited)、[LLVM D109860](https://reviews.llvm.org/D109860)

### ARM-Q2：B1 混合 profile 合理吗？更好的融合方式？

**作为带不确定性的推断合理；按现稿直接“一份 profile 保留生产总量和实验室边概率”不完整。**

L:`llvm/include/llvm/ProfileData/SampleProf.h:363–472,763–777` 的主要结构是函数、行/discriminator 样本、调用目标及内联调用点，不是任意 CFG 边表。两个不同流网络可能映射成相同的行样本；cycles 权重也不是生产函数调用次数。把实验室概率乘上生产 cycles 再写行计数，可能违反流守恒或丢失待保留的信息。

建议先做两级方案：

1. 以源函数身份和 CFG/hash 对齐，保留生产热度与实验室条件概率的不同单位、工作负载来源、覆盖范围。对不同输入/场景分层，而不盲目混为单一概率。无调用栈时只承诺已有内联上下文，不虚构动态调用链。
2. 在编译器 IR/Profi 层把实验室边比例作为软先验，生产样本作为带误差的约束，满足 CFG 流守恒；不一致/低置信度时回退 IP 或静态启发式。若仍导出标准 sample profile，必须验证 Clang 读回后的局部分支概率能否保留意图，并报告信息损失。

合成夹具至少含菱形 CFG、多前驱、循环、多条边共用源行、不同阶段输入使分支翻转、未覆盖错误路径。对不唯一解输出区间/歧义，不输出伪精确“真值”。候选与原始 IP、纯实验室 profile 比较，另留独立测试场景。没有证据支持现在就宣称融合优于任何单一来源。

### ARM-Q3：A4 的运行时、采样插桩和 ARM32 难点？

**有可复用材料；不是加编译选项就能用。建议先用现有局部 gcov 建参考。**

已核实 2021 PGO v6 补丁提供 debugfs profraw 导出，初始限制 x86；未核实其完整撤回历史，不能把“进过 next 又撤回”的细节当成当前可直接应用的支持承诺。[2021 原始补丁邮件](https://lists.openwall.net/linux-kernel/2021/01/21/530)

截至本次评审还存在 2026-11-03 的 coverage v2 系列，含 Clang source coverage、profraw v10（Clang 19–22）/v11 支持和原子计数，复用旧 PGO 导出代码；但发布的是待评审补丁，新增 source coverage 的启用目标是 x86_64，不是已证明 ARM32 可用的 IR PGO runtime。它值得参考，不能直接替换 A4。[系列说明](https://lists.openwall.net/linux-kernel/2026/11/03/191)、[14/20](https://lists.openwall.net/linux-kernel/2026/11/03/214)

LLVM 22 中选项已可从源码确认：L:`llvm/lib/Passes/PassBuilderPipelines.cpp:297,880–899` 有 `enable-sampled-instrumentation`，L:`llvm/lib/Transforms/Instrumentation/InstrProfiling.cpp:171–193` 有 sampled period/burst 选项；但 `:2141–2161` 创建 **thread-local** sampling variable。Linux ARM32 内核不能把普通用户态 TLS 当作 per-CPU 状态直接使用。还需处理 early boot/noinstr/IRQ、重入、迁移、32 位上的 64 位计数更新、导出一致性、profile 版本/节布局及潜在 libatomic/compiler-rt 依赖。

因此把 A4 拆成“少量安全 TU 的非采样参考计数”和“降低开销的采样版本”。采样版是估计量，不是精确真值；并发非原子增量、插桩造成路径/调度变化，即便非采样也要量化误差。

更快的起点已经在 K 中：`arch/arm/Kconfig:32`、`kernel/gcov/Kconfig:4–35`、`kernel/gcov/Makefile:4–8`、`kernel/gcov/clang.c` 支持 ARM/Clang gcov 与按文件选择。用 `llvm-cov gcov` 看安全 TU 的分支参考，先不设计全内核运行时；其 Clang22/本配置的实际构建及运行仍待验证。gcov 数据不能直接当 sample profile 或原生 IR PGO profile 使用。

### ARM-Q4：ETMv4 ARM32 移植及 A32/T32 解码完整性？

**条件性可行，现有板和证据不足以估算固定 2–4 周。**

K:`drivers/hwtracing/coresight/Kconfig:87–112` 确认 ETM3/PTM 与 ETM4 的架构门禁。ETM4 不是只改 Kconfig：还涉及 SoC source/sink/DT、寄存器访问、CPU 上下电/context、跟踪授权、地址空间和丢 trace 后重同步。内核能运行 A32 必须先成立。

方案 A3 将 A76 放进“运行 32 位内核”的列表是明确错误：A76 TRM §A1.4 仅支持 EL0 的 AArch32，EL1 内核使用 AArch64。[Arm A76 TRM](https://documentation-service.arm.com/static/5f562083235b3560a01e03bc)。应把 A76/RPi5 的 arm64 内核 + 32 位用户态追踪与 ARM32 内核移植分开。

OpenCSD 定义了 A32/T32 ISA，且有相应 decoder 和 Thumb 修复历史，说明有实现基础；不能推出当前 Tizen perf 的完整链都正确。[OpenCSD 项目](https://github.com/Linaro/OpenCSD)、[接口定义](https://android.googlesource.com/platform/external/OpenCSD/+/6fb9ed6a93ed3c6798210527ba58305943742e68/decoder/include/opencsd/ocsd_if_types.h)

拿到确有 source/sink、授权和已知可用 trace 的产品板后，先验证 A32 条件执行、Thumb IT/16–32 位混合、异常/IRQ、间接调用/返回、上下文切换、trace 丢失和内核 ASLR/地址锚点，再验证 `perf inject` 合成分支数据的语义。现阶段完整性与工期均不确定；不放在 RPi4 K1/K2 的必经路径。

### ARM-Q5：ARM32 尺寸优化/冷热拆分能保证不损失性能并省内存吗？

**可以研究并测到收益，不能先保证。** ARM32 MFS 目前被驱动拒绝；函数级冷热节、PGSO 和部分 TU 的尺寸策略仍有实现基础，不需要先支持 MFS。默认 PGSO 已存在，应先测它，再决定是否改变阈值/内联策略。无样本函数不能直接整体 `minsize`，尤其是尚未覆盖的错误、恢复和实时路径。

按 I7 区分磁盘、可加载段、保留页、动态内存；同样 `.text` 下降可能被 alignment、branch veneer、rodata/异常展开表增量抵消。库布局的 RAM 收益由实际触及/共享页决定，应看 PSS/共享文件页，不只单进程 RSS。

可增加“现有 `-O2` + AFDO”“选择性 `-Os`”“选择性 `-Os` + AFDO”的小型比较，但先固定候选清单和回归负载。owner 批准的 Kconfig/模块裁剪可能比编译优化释放更多页，必须与 AutoFDO 收益分账。全局 ICF、直接按未采样删除代码或大范围冷代码外提不宜作为第一步。

### ARM-Q6：没有写入方案但更好的做法？

按成本和对本平台的适用性排序：

| 做法 | ARM32 可行性与新增价值 | 验证方法 |
|---|---|---|
| **先比较 IP + 现成 Profi** | 无需分支硬件；L:`SampleProfileLoaderBaseUtil.cpp:41–43` 已有入口。line-based 非 CS profile 不应假定已默认开启；`SampleProfile.cpp:2015–2021` 是 CS/probe 情况下的自动启用。 | 独立 K2 候选，固定同一 profile，仅改变消费者选项；先用局部 gcov/合成 CFG 检查推断，再看性能和尺寸，不重写一个同功能推断器。 |
| **局部 gcov + 有歧义区域才加计数** | 现有 kernel/Clang gcov 可复用。先选择安全且业务相关的少量 TU，避免全内核运行时。后续研究只给 CFG 中无法由流守恒辨识的边加计数，减少测量扰动。 | 无插桩/局部插桩开销、并发丢计数、流守恒、独立负载上的分支误差；noinstr/入口/IRQ 等区域先排除。选择性边插桩需要额外编译器工作，未验证。 |
| **cycles 与 instructions 的分离诊断** | A72 TRM 列有退休指令事件，较退休分支事件有更直接硬件依据；实际计数仍须板测。cycles 用于成本热度，instructions/静态指令密度可作另一种弱先验。 | 分开采样并控制开销/周期；合成算术、访存停顿、A32 条件执行、临界区。不得简单相加不同事件，也不能把 block 长度相除后的数称精确执行次数。 |
| **不确定性驱动的保守优化** | 在多个可行 CFG 流解上评估分支方向；仅当高置信度方向一致时采用激进布局，其他保留基线。比把所有缺失边填成单个“真值”更稳健。 | 合成不可辨识 CFG、实验室/产品输入分布翻转；报告覆盖与不确定范围，用独立 benchmark 比较。属于研究建议，非已证实创新首创。 |
| **以保留页为目标的尺寸预算** | 结合 ARM32 严格 RWX 对齐、unwind/veneer 和热代码页，把每 TU 的尺寸优化收益换成可能释放的页，而不只追求最小 ELF。 | 对选定少量 TU 做 -O2/-Os 与内联策略对照，统计各段/空洞/保留页和长尾延迟；与用户态共享库 PSS 分开。 |

不建议 K1 为追求创新同时加入这些候选；先保留单一 AFDO 候选得到可解释的基线。

### ARM-Q7：路线、门槛、工期怎么调整？

建议顺序：

1. **执行准备：** 解决 S1–S3、I1，冻结真实构建/部署/恢复及采集契约。只做能够启动和恢复的 K-BASE。
2. **K1：** 同 boot 身份严格的 IP profile、真实消费证据、一次正确性/恢复闭环，再做跨重启 A/A 预试及锁定 A/B。结果可以没有加速，仍能交付能力与限制；不要把“必须测到收益”当作继续取数的条件。
3. **K2 低成本：** Profi 开关对照、默认 PGSO 的效果分解、函数级布局和局部尺寸策略、局部 gcov 参考。这些不依赖 A2 或 B3。
4. **研究扩展：** 在有参考数据后做融合和选择性插桩。A2 先过事件存在和语义门槛；A3 等真实可追踪产品板；A5 单独定位崩溃后再谈 profile 稳定性，不能把 pseudo-probe 等同于 CSSPGO 的完整动态上下文。

A2 在事件不可用时应立即结束该平台探针，不投入 2–3 周实现。A4 的 3–4 周、A3 的 2–4 周、B3 的 1–2 周最多是特定边界的原型预算，不能含全部 ARM32 运行时、异常追踪和产品验收承诺。B3 只为真实分支/trace 路线做，不作为 gcov/原生 PGO/IR 推断的前置。完整工期在最小夹具与板能力核对后重估。

## 5. 建议的执行前收敛顺序

本报告列出 **严重 3 项（S1–S3）、重要 8 项（I1–I8）、一般 2 项（G1–G2）**。优先级如下：

1. **部署/构建前必须完成：** S1 版本与打包，S2 真实分区与非 RPM 恢复，S3 模块/RT 隔离；I1 函数身份与稳定路径。没有这些，不应生成正式训练数据或启动自动切换。
2. **正式采集/计时前必须完成：** I2 跨 boot 预试与统计单位，I3 内存指标，I4 固定训练配方/工具/遥测，I6 可执行的消费与节验收。将 boot/正确性故障与可重试传输故障严格分开。
3. **报告与总体路线必须修正：** I5 采样偏差限制、I7 内存/PGSO 口径、I8 硬件和插桩前提。G1/G2 可以同步完成；已有证据无需重复获取。

最终结论：**需修改后执行**。修正后可以开展 RPi4 ARM32 内核 AutoFDO 首次端到端验证；现有证据不足以承诺 1% 以上加速、可迁移的退休分支目标采样，或 text 缩小等量转化为 RAM 节省。
