# K2a 主机原型与 GCOV 可行性

R1 已用 15 份 K1e 带栈记录生成候选 profile，通过 K1e 身份和质量门禁。R2 已验证同源 C 程序的 GCOV 计数可被 Clang 22.1.8 消费，并能反转热分支布局。ARM 对象尺寸试验表明现有 boot_a 容量是 K2b 的部署门禁。 [证据索引](evidence/29-k2a/index.json)

## R1 IRQ 影子重归属

沿用 04 号报告的 A32 指令窗口，识别 cpsie i 和寄存器形式 msr CPSR_c,Rn，取该指令与同一符号内的下一条，窗口为 0/+4 B。按同次启动的 kallsyms、mmap 锚点和 vmlinux PT_LOAD 做地址换算。K-BASE vmlinux build-id 为 96766cfcbff8c33d83ca38152ad02f6a02dd44d4。 [K1a 指令窗口](04_k1a_baseline.md)

沿原始链逐帧向上找第一个非辅助内核调用者。辅助清单含 _raw_spin_unlock_irqrestore、IRQ 形式的 spin/read/write unlock、arch_local_irq_enable/restore、local_irq_enable/restore、raw_local_irq_enable/restore 以及开中断的 trace/lockdep 辅助。符号及 DWARF 内联名共同判别。finish_task_switch 按真实开中断窗口识别，函数其余调用点保留通常的调用者资格。候选调用点取 A32 返回 IP−4，要求为 BL 或寄存器形式 BLX 并有 DWARF C 行。直接 BL 还核对目标是否为下层帧所在符号。间接 BLX 的证据限于指令形态、调试行和记录的调用链。

1,010,453 个内核样本中有 489,185 个位于影子窗口。重归属 327,116 个，占 **66.87%**。结构性无可用调用者 51,054 个，占 **10.44%**，含叶帧、辅助链耗尽和用户态或未知 DSO 边界。102,425 个直接调用目标不符，8,590 个缺可用 C 行，均保留原 IP。目标不符可能来自尾调用、跳板或展开缺帧，本轮未区分。

| 负载 | 内核样本 | 影子窗口 | 重归属（占影子） | 结构性无调用者（占影子） | BL 目标不符 | 无 C 行 | 可用 C 行下界 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pipe | 282,906 | 169,561 | 99,958（58.95%） | 10,476（6.18%） | 50,756 | 8,371 | 213,048 → 217,603 |
| mmfault | 303,718 | 152,535 | 125,490（82.27%） | 122（0.08%） | 26,894 | 29 | 125,979 → 174,786 |
| tmpfs | 299,020 | 107,698 | 87,267（81.03%） | 451（0.42%） | 19,889 | 91 | 75,701 → 81,163 |
| syscall | 91,432 | 42,794 | 2,485（5.81%） | 39,699（92.77%） | 601 | 9 | 0 → 0 |
| tos | 33,377 | 16,597 | 11,916（71.80%） | 306（1.84%） | 4,285 | 90 | 21,877 → 24,669 |

pipe 的主要权重增量如下。K1e 每个样本原始 period 为 1,000,003，配方以 sample 计权。同址别名沿用 kallsyms。

| 函数 | 归属前 | 归属后 | 样本增量 |
| --- | ---: | ---: | ---: |
| __sched_text_start / __schedule | 890 | 42,688 | +41,798 |
| kmap_high_get | 295 | 40,282 | +39,987 |
| prepare_to_wait_event | 221 | 11,137 | +10,916 |
| vfs_write | 1,451 | 4,640 | +3,189 |
| pipe_read | 2,710 | 3,169 | +459 |
| vfs_read | 2,040 | 2,043 | +3 |

- mmfault 的主要增量是 kmap_high_get（+47,249）、__mem_cgroup_charge（+15,959）。
- tmpfs 的主要增量是 kmap_high_get（+32,649）、shmem_get_folio_gfp（+10,478）。
- syscall 的主要增量是 kmap_high_get（+678）、__sched_text_start / __schedule（+189）。
- tos 的主要增量是 kmap_high_get（+3,295）、__sched_text_start / __schedule（+1,269）。

各负载归属前后前 30 名、样本差、period 差与内核权重百分比均归档。 [前 30 名](evidence/29-k2a/r1/top30-before-after.tsv) · [逐段归属与调用点](evidence/29-k2a/r1/r1-statistics.json)

按补丁 10 与 K1e 同一配方逐段生成 extbinary，采用 sample/max/none/none/none，再等权合并 15 份。带栈投影逐行与原 IP 输入核对，56 行仅差 perf 随机生成的 VDSO 临时文件名。候选流沿用归档原行，只替换可归属内核 IP 和对应 DSO offset。15/15 身份 verified，FS discriminator 启用，1,010,271 个内核目标样本中映像外为 0。可用样本 **712,547 → 743,652**，歧义上界 **1.153%**，低于 2%。pipe、mmfault、tmpfs 的可用 C 行下界均 ≥50,000。导出未见 LOST 记录，profgen 的完整性仍为 unknown。候选 SHA-256 为 **91ea9b27da0fa9ed5bb1c3ff1ecf463d9d8fe7c7ec1f9b026cc4e8a047646418**。 [候选 profile](evidence/29-k2a/r1/K-AFDO-R1.prof) · [质量汇总](evidence/29-k2a/r1/quality-summary.json)

这是函数与调用点层面的归属修正。关中断区内的真实指令、基本块和路径仍未知。后续用同负载 GCOV 入口计数比较 R1 前后的秩相关与热点重合，再用同源配对测量评价性能和尺寸。K1f-3 的 pipe 等价及 L1I refill +15.6%，mmfault 耗时 −1.98% 且机制计数改善，是后续参照。 [K1f-3 正式比较](28_k1f_3_formal_compare.md)

## R2 配置、插桩范围与规模

源为 K-BASE 提交 7fffbec570692c925cbf1f58ea9b1cd1a5d78ac8。ARM 在 arch/arm/Kconfig:32 选择 ARCH_HAS_GCOV_PROFILE_ALL。同一探测环境分别对基线和 GCOV 跑 olddefconfig，得到 GCOV_KERNEL=y、GCOV_PROFILE_ALL=y、CONSTRUCTORS=y，逐目录选择项默认 n。K-BASE 已启用 DEBUG_FS=y 与 DEBUG_FS_ALLOW_ALL=y。冻结 buildroot 的 pahole 1.29 使两份配置保持 BTF。本地探测相对冻结 K-BASE 关闭两项 AS 能力，两边相同。对象试编译缺 libelf 开发头，试验两侧均关闭 BTF，另存配置差异。 [GCOV 差异](evidence/29-k2a/r2/gcov-config.diff) · [本地探测差异](evidence/29-k2a/r2/ambient-config.diff) · [对象配置差异](evidence/29-k2a/r2/objects-config.diff)

全树 17 条显式 GCOV_PROFILE[_对象] := n。其中可适用于 ARM 的通用条目是 lib/test_bitmap.o，其余位于 x86、s390、parisc、powerpc、xtensa 或 sh。对象、目录、全局配置的优先级见 scripts/Makefile.lib:153–159。ftrace、RDS、io_uring 的新增 n 是局部启用开关，PROFILE_ALL 仍按实际对象规则生效。汇编及主机工具没有 C GCOV 计数。noinstr 与 __cpuidle 使用含 __no_profile 的 __noinstr_section，分别对应 .noinstr.text 和 .cpuidle.text。A32 验证对象的 notes 只有 ordinary，带 no_profile_instrument_function 的 early 未生成计数记录。 [排除清单](evidence/29-k2a/r2/gcov-exclusions-relative.txt) · [源码与入口收据](evidence/29-k2a/r2/source-receipt.txt) · [A32 标注验证](evidence/29-k2a/r2/fixture/arm-noinstr-proof.json)

七个试验对象覆盖 ARM traps、pipe、scheduler、softirq、mm、network core 和 driver core。每侧只编这些对象与必要的 prepare 工具。样本可执行节 **257,044 → 774,584 B**，初始化节 324,654 → 910,201 B，零填充 588 → 83,824 B。逐对象 gzip 代理总量 124,349 → 324,691 B。

按上述对象比值外推，原 zImage 14,965,104 B → **约 39.08 MB**，静态驻留分配 **约增加 75.38 MB**。七个对象偏热，实际未插桩比例、重定位、链接对齐和跨对象压缩都会改变投影。注册开销另按 ARM32 两类 28 B 结构取 32 B slab 槽估算，2,958 个链接成员与 64,805 个正文地址约对应 **2.17 MB**。这只是注册代理，debugfs 节点、卸载副本和临时快照另计。 [逐对象与空间模型](evidence/29-k2a/r2/size-estimate.json)

boot_a 当前空闲 1,374,208 B。按 FAT 2,048 B 簇、原子配置替换预留一簇及至少 512 KiB 安全余量，仅移除实验 K-AFDO 可容纳 **15,880,192 B**。另经 PM 批准移除两个自有实验映像，上限 **30,846,976 B**。两者均低于代表性投影。K2b 以真实产物重算空间。超过现有上限时申请独立可回滚的较大启动介质，或经批准先做减小插桩范围的实验。

## R2 转换器与验证

Clang 22.1.8 --coverage 在 x86_64 fixture 与 A32 对象上均生成 little-endian B11* GCOV。原型用 GCNO 恢复 LLVM 文件索引和函数起始行，用 llvm-cov gcov -a -b -c -f -dump 的 block 0 计数作函数头。行偏移为源码行减函数起始行。同行多块取最大，函数总量取行计数之和与头计数的较大者。输出 plain sample 文本，行记录无 discriminator。按函数归属源文件过滤跨文件行，拒绝未知版本、结构错误、dump/notes 不匹配，支持按链接名排除跨 TU 冲突。

同源程序独立训练两次，choose 入口均为 100,000，分支分别是 **99,900/100** 和 **100/99,900**。Clang 用 -fprofile-sample-use 和禁用 FS discriminator 的设置重编。choose 的 AppliedSamples 记录有 100,000 和 99,900 等正值。IR 权重恰为对应计数，x86_64 汇编 fall-through 从 callq left 反转为 callq right。五项测试涵盖计数、版本/配对错误、同名排除、消费与布局、A32 noinstr。 [转换器](evidence/29-k2a/r2/gcov_to_sample.py) · [测试](evidence/29-k2a/r2/test_gcov_to_sample.py) · [测试输出](evidence/29-k2a/r2/fixture/tests.log)

主机 fixture 由 Clang 22.1.8 以 -O2 -g --coverage 编译，再用主机 GCC 链接同版本 libclang_rt.profile-x86_64.a。重新训练前移除上一次 .gcda，使用 llvm-cov gcov -a -b -c -f -dump 生成逐块记录。消费重编使用 -O2 -gline-tables-only -fdebug-info-for-profiling 与 -mllvm -enable-fs-discriminator=false。另把本机 GCDA 过滤成 kernel/gcov/clang.c:368–392 的头、函数和计数记录形态，llvm-cov 读回的块输出和转换 profile 均与原 fixture 一致。该项验证的是文件封装。 [GCDA 封装验证](evidence/29-k2a/r2/verification.txt)

内联上下文缺失，宏展开与同行多块可产生多对一位置，跨 TU 的 static 函数可能重名。GCOV 运行次数可作为 R1 参考，采样周期权重与运行次数的单位不同。K2b 还需核对内核导出与主机 notes 兼容，以及并发和后台活动的影响。

## K2b 计划，待 PM 批准

1. **主机构建。** 用冻结 K-BASE 源码、同一 Clang 和 snapshot 构建实验 GCOV 内核，锁定 .config、原始 vmlinux、System.map、全部匹配 .gcno、模块、日志和 SHA。核对 LLVM GCDA hooks、ARM 早期路径和构造器。比较 Module.symvers，准备独立 release 和匹配模块目录，模块复用以 ABI 核对为准。
2. **尺寸和部署门禁。** 用实际 zImage 逐簇重算，要求至少 512 KiB 空闲。确认独立可回滚介质或另批的范围调整，先做备份与 PLAT 恢复演练。板端写入、启动、模块目录均待批准。
3. **启动和空闲对照。** 查 build-id、cmdline、规范化 FDT、模块、dmesg、网络和 SDB。确认 /sys/kernel/debug/gcov 可读，B11* .gcda 能与同构建 notes 配对。记录空闲 meminfo、Slab、节点数量和同长度空闲计数。用固定次数测试多核计数一致性与重复性。若考虑 -fprofile-update=atomic，先在 ARM32 检查代码生成、ABI 和额外开销。
4. **分段训练与清零。** 沿用 K1e 五种训练参数、CPU3 绑定和门禁。每段预热后向 /sys/kernel/debug/gcov/reset 写入任意内容，验证代表性计数，再运行固定负载。保存会话、负载、开始结束、空闲对照和导出收据，避免模块在段内卸载。
5. **打包拉回。** 从批准的调试挂载中枚举 gcov 普通 .gcda 文件，逐文件用 cat 复制到 /opt/afdo_agent/k2b/<boot_id>/<load>/ 的等路径普通文件。debugfs 虚拟文件可报零长，先实体化，校验 magic、非零大小、清单和 SHA，再 tar 拉回并复核。调试目录的 .gcno 是指向构建路径的链接，使用主机同构建归档配对。拉回成功后再 reset 下一段。
6. **评估及停止。** 按 TU 核对 gcda/gcno 版本和校验，保存 llvm-cov 输出。跨 TU 同名无法消解时排除并量化覆盖。纯 GCOV 消费采用明确的非 FS 路径并匹配对照设定。比较 R1 前后与 GCOV 的 Spearman 秩相关和 top-30 重合率。实际收益在后续配对测量中验证。任一启动、尺寸、计数或身份门禁失败，保存证据并回到 PLAT。

## 资源账本

唯一单元 k2a-host.service 的 MemoryMax 为 6,442,450,944 B，swap 上限 0 B，CPUQuota 400%，Nice 10，试编译 -j4。归档完成、提交前的 cgroup 内存峰值 **2541.86 MB**（含文件缓存），累计 CPU **110.31 秒**。任务临时目录与交付文件净占用 **188.26 MB**，当时 /home 可用 **263850.77 MB**。两套对象试编译树已清理。 [资源收据](evidence/29-k2a/resources.json)
