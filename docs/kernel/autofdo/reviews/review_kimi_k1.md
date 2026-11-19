# K1 设计 v0.1 与方案 v0.1 评审（Kimi Code）

日期：2026-11-18。评审对象：`docs/kernel/autofdo/06_k1_design_v0.1.md`（主）、`01_arm_profile_capability_proposal_v0.1.md`。背景 00–05 全部读过；06/03/04/05 取自 `kernel-k0` 分支（本地 main 尚未包含 03–06）。只读评审：未构建、未接板、未修改仓库文件。标注沿用被审文档约定：**[已证实]**（源码或证据）、**[推断]**、**[需核实]**。

核实范围声明：

- 源码核实（本机只读）：LLVM 22.1.8 的 `.text.hot/.text.unlikely` 产生机制（`llvm/lib/CodeGen/CodeGenPrepare.cpp:181–201`、`:583–596`；`TargetLoweringObjectFileImpl.cpp:616–684,885–902`；`CommandFlags.cpp:418–421`）；PSI 判冷/热接口；内核 6.12.80 源码树（B）的 `kernel/trace/ftrace.c:1020`（function_profile_enabled）等。K（0fac5de6）相关结论以 00/02 报告的 K 检查为准，我未重新核对 K 树。
- 上游现状（6.13 AUTOFDO_CLANG、kernel/pgo v9、ETMv4 Kconfig 门禁等）：以 00/02 报告的核实为准，我未重新访问上游。
- 未核实：A2 所述"上游 IP RFC 讨论中有人提过采样已退休跳转"（[需核实]，未做检索）；任何板上行为的现行状态。

---

## 1. K1 设计第 11 节五问逐条回答

### 11.1 不开 `-ffunction-sections`、只依赖 `.text.hot/.text.unlikely` 前缀节

**结论：取舍合理，且机制在 ARM32 上不存在架构障碍；但"产生这些节"的覆盖面在 IP-only 稀疏 profile 下会很窄，预期应写低。**

依据（本轮源码核实，[已证实]）：

1. 节前缀的设置在 `CodeGenPrepare`（`CodeGenPrepare.cpp:583–596`）：`profile-guided-section-prefix` 默认 true；profile 判热 → `setSectionPrefix("hot")`，判冷 → `"unlikely"`。该 pass 与目标无关，ARM32 无特殊门控。
2. 节名生成在 `TargetLoweringObjectFileImpl.cpp:671–684`：有前缀即生成 `.text.hot.` / `.text.unlikely.`；**只有在 `TM.getUniqueSectionNames()`（即 `-ffunction-sections`，`CommandFlags.cpp:418–421`）时才在节名后追加函数名**（:682–684）。所以不开 function-sections 时，全部冷函数共享一个 `.text.unlikely.` 节、热函数共享 `.text.hot.` 节——**节会产生**，只是没有函数粒度。链接脚本通配 `.text.hot.*` 中的 `*` 匹配空串，可覆盖该节名；以链接 map 实证即可（设计已计划）。
3. 真正的限制在判定侧：PSI 判冷要求入口计数、调用计数、全部块都冷（`ProfileSummaryInfo.h` 的 `isFunctionColdInCallGraph`），IP-only 稀疏 profile 下大量函数 hotness unknown → 留在 `.text`；判热要求 entry hot 或块 hot。**因此首版能进热/冷节的函数占比可能很小**——这不使步骤 1 失效，但 §3.2 步骤 1 的"检查 vmlinux 节表"应预期"节存在但很小"，并把"两个节的字节数与函数数"作为 consumption 报告项。
4. 步骤 1 的主要收益来源本来就不是节放置：内联决策、函数内块布局（MachineBlockPlacement 用 BFI）、寄存器分配与 PGSO 都不依赖节。§3.2 的"步骤 1 不行再进步骤 2"顺序正确。

补充风险（[推断]）：cold 判定依赖 profile summary 的分位数阈值，IP 计数的语义是"时间"而非"执行次数"，cold cutoff 的含义与上游分支采样不同；解释结果时注意"耗时少"与"执行少"的差异。

### 11.2 并存 + 复制 zImage + 重启的切换方式

**结论：可行，但 `cp` 覆盖 zImage 在 FAT 启动分区上是非原子写，掉电即砖；建议改为 rename 原子替换，或更好的 U-Boot 文件选择方案。**

1. 现有方案的最小修正（低风险）：`cp zImage-<v> zImage.new && sync && mv -f zImage.new zImage && sync`。rename 在 FAT 上原子，掉电最多留下 `zImage.new` 残留。[已证实：FAT rename 语义]
2. 更好的方案（需用户确认改动 boot.scr）：板上启动链为 config.txt `kernel=u-boot.bin` → U-Boot `boot.scr` → `bootz zImage`（03 §4.1 [已证实]）。改 boot.scr 从一个小文件（如 `/kvariant`，一行 `kbase`/`kafdo`）读变量，`bootz zImage-${kvariant}`；切换 = 写一行小文件 + sync。不掉电覆盖内核镜像、切换痕迹最小；缺点是要动 boot.scr（不属于内核包，需用户确认），并要静态核验 U-Boot 脚本语法。
3. 备选：kexec 免完整重启。切换快、可脚本化，但固件不重新初始化、设备状态与冷启动不同，测量保真度下降，且 ARM32 kexec 未在 K 的配置中验证过 [需核实]。**不建议**为本测量引入；冷重启的环境一致性更值钱。
4. 不变项：重启后以 `/sys/kernel/notes` 的运行 build-id 断言身份的做法已在 K1a 离线验证 [已证实]，保留。

### 11.3 训练负载与测试基准的关系、主/次比较

**结论：主/次比较选择合理，但"内核周期占比 97.7%"系统性高估了 AutoFDO 的可优化份额；syscall 作为"部分留出"没有检验力。**

1. 依据（K1a 实测 [已证实]）：syscall 的 60.0% 样本在 `vector_swi`（汇编异常入口），pipe 的前 30 含 `arch_local_irq_enable`、`arm_copy_*`、`__memset/memcpy` 等汇编；K1b 会把这些归入 special_section/no_cu 丢弃（[已证实]，K1b §1）。**这些代码 AutoFDO 无法优化**。建议 K1e 增加领先指标：每个基准"可符号化到 C 行号的内核样本占比"，写进报告并与 §9 门槛 4 的解释挂钩——若 pipe 的该比例低，inconclusive 的直接解释就是"可优化份额不足"而非"profile 无效"。
2. pipe 作主比较成立：其热点 `finish_task_switch`、`pipe_write`、`do_sys_poll` 等是 C 函数。内存触页作次比较成立，但注意 K1a 实测它只覆盖 fault/memcg charge，**未触发 reclaim/swap**（pgfault 6.4M、回收与换出全 0 [已证实]）——不要称它为"内存压力"，回收路径仍需单独负载。
3. syscall 的"部分留出"角色没有检验力：它 60% 在汇编入口，对 AutoFDO 几乎不敏感，留出与否都测不出训练泄漏。建议要么去掉该角色表述，要么改用 tmpfs（99.4% 内核且热点 `shmem_*`/`filemap_*` 全是 C）承担留出检查；tmpfs 的 CV 1.34% 在 ε=1% 下需要 87 block（截断到 40 仍不足），这正是它只能做探索项的原因 [已证实，04 §计时表]。
4. 训练/测试共享内核路径已如实披露 ✓；ToS 作对照（内核占比 1.4%）成立 ✓。

### 11.4 consumption 证据按文件开启优化记录

**结论：可行但按文件实施成本高；建议改为 K-AFDO 全局开启、主机侧过滤，并增加 record-coverage 检查。**

1. kbuild 的按文件机制是 `CFLAGS_<file>.o +=`（需改各目录 Makefile，给 K-AFDO 引入源码差异）或按目录 `ccflags-y`；对"前 30 热函数所在文件"逐个改 Makefile 既繁琐又破坏"两变体只差一点"的纯净性。
2. 更简单且满足 build-lock 的做法：把 `-fsave-optimization-record=yaml -foptimization-record-passes=sample-profile` 声明为 K-AFDO 的候选差异选项、**全内核开启**；clang 默认对每个 .o 在旁生成 `<name>.opt.yaml`，主机事后过滤前 30 热函数。全内核 yaml 量约几千个小文件，主机可承受 [推断，体积未实测]；`AppliedSamples` remark 由 SampleProfileLoader 产生（[已证实]，LLVM SampleProfileLoader）。
3. 补充一项更直接的 consumption 证据（复用用户态 workflow 已用选项 [已证实]）：K-AFDO 构建加 `-mllvm -sample-profile-check-record-coverage=<N>` 与 `-mllvm -sample-profile-check-sample-coverage=<N>`（`SampleProfileLoaderBaseUtil.cpp:26–34`），直接报告 profile 记录的函数命中率；并比较两变体 System.map 中前 30 热函数的大小/地址及 `.text.hot.`/`.text.unlikely.` 节尺寸。

### 11.5 时间估计与遗漏风险

**结论：总量 4–6 周与 K0 一致、大致合理；K1c 偏紧，测量方法上有一处必须修正的遗漏（预试估不到配对方差）。**

- K1c 1 周偏乐观 [推断]：ARM32 节表/启动差异排查（veneer、exidx、向量节、unwind）一旦出问题是开放式工作；建议 1–2 周。
- K1f 1 周紧张但可行；遗漏预算：sdb/网络中断的恢复演练、空对照预试（见下）。
- 遗漏风险（按重要性）：
  1. **预试设计错误**（见第 3 节）：K-BASE 单变体预试只能估单变体 CV，估不到配对差值的方差；N 可能系统性偏小。
  2. **同名 static 函数的 profile 错配**：上游 Makefile.autofdo 默认不加 `-funique-internal-linkage-names`（[已证实]，00 §4.3）；内核各驱动同名 static 函数常见，会拉低匹配率。建议训练与消费构建都加该选项（用户态 workflow 已用），并在 consumption 报告中给出记录覆盖率。
  3. 内核 DWARF 在 `-gdwarf-4` + `-fdebug-info-for-profiling` + FS discriminator 组合下的行表/内联质量，未在 ARM32 内核规模（2,951 个 CU）验证过 [需构建验证]。
  4. vector_swi 等汇编热点占比（见 11.3）。

---

## 2. 方案 v0.1 第 7 节七问逐条回答

### Q1：A2（被采分支目标采样）在 A72/A76 上的可行性

**[推断] 可行性低到中；语义假设很可能不成立，但探针便宜，按 P0 做止损试验是对的。**

- 机制判断：BR_RETIRED/PC_WRITE_RETIRED 溢出触发的是普通 PMU 中断，记录的 IP 是**中断时刻的执行点**，不是被采分支的目标；事件名不产生 source/target 对（00 §5.1 已正确裁定 [已证实]）。假设要成立，需要"溢出时刻的执行点系统性落在刚退休的 taken 分支的目标附近"——A72 的中断延迟与 skid 为数十条指令量级 [推断，板上未测]，其间可能又经过多个分支，样本实际混合"目标之后"与"fall-through 之后"两类位置。
- 事件可用性：A72 的 BR_RETIRED（0x21）/PC_WRITE_RETIRED（0x0C）在 AArch32 下的采样行为未经板上验证（00 §5.1 [已证实：需板上确认]）；A76 的 BR_RETIRED 枚举已见，PC_WRITE_RETIRED 未见。
- 公开研究/实现：我未见把该思路做成 profile 来源并评估的公开结果（**不确定**，未做文献检索）。方案中"上游 RFC 有人提过"的说法同样未核实。
- 建议的探针顺序（与 P0 一致，补充一条退路）：先在用户态用已知 CFG 的小程序测"样本 PC 与块首的距离分布"和"块入口计数与插桩真值的秩相关"；若 BR_RETIRED 在 A72 不可用，可用 ftrace/断点式计数先验证"块入口频率分布能否改善布局"这一概念本身，再决定是否值得追硬件路径。

### Q2：B1（混合 profile）的融合规则

**[推断] 方向合理；建议把"实验室数据只给方向、生产数据只给量"写成硬规则，而不是可选项。**

- 具体规则：实验室数据（A4/A3）在函数内归一化为分支概率（方向），绝对计数一律丢弃；函数与块的热度全部来自生产样本。两来源计数尺度不同（次数 vs 时间），任何跨来源的绝对值相加都是错误的。
- 置信度：按函数给"实验室覆盖率"（该函数在实验室数据中的边覆盖比例），覆盖低的函数整体回退到 Profi 推断（B2）。
- "按调用上下文加权"在 IP 输入下不可用（IP 没有上下文）；按上下文融合是 CSSPGO（A5）的领域，不要混进 B1 首版。
- 负载不匹配的风险已识别 ✓；补充一条验收规则：融合 profile 必须先在"实验室负载"上证明不劣于纯实验室 profile，再谈生产泛化。

### Q3：A4 内核 PGO 运行时与 LLVM 采样插桩

- 上游现状以 00 §5.3 为准 [已证实]：v9（2021-04-07）、进入维护者 -next、主线 pull 前撤出、最新稳定版未包含；`kernel/pgo` 与 CONFIG_PGO_CLANG 不在现树。采样插桩选项为 `-mllvm -sampled-instrumentation`（默认 false，period 65536，burst 200；`InstrProfiling.cpp:171–194`），`-fprofile-generate-sampling` 是 ignored 组（`Options.td:7146`）[均已证实]。
- ARM32 适配难点（[推断]，按风险排序）：内核无 TLS 运行时的惯用法（`__llvm_profile_sampling` 是 thread-local，内核需改 per-CPU 计数）；64 位计数器在 32 位并发下的原子性；noinstr/NMI/中断路径；profraw 导出（debugfs）与内核写文件限制；模块加载/卸载的计数器生命周期。
- 工作量：K0 已把原方案 3–4 周修正为 4–6 周或更多，我同意修正后的估计。
- **重要替代（方案未提）**：若目标只是"真值参考"，内核自带的 **ftrace function profile**（`function_profile_enabled`，`kernel/trace/ftrace.c:1020` [已证实存在]）零移植给出真实函数入口计数，可与插桩计数互验，也可直接补 IP 采样缺的 head samples 维度。边计数真值仍需 A4，但函数级真值不必等它。

### Q4：A3（ETMv4 移植到 ARM32 内核）

- ETM4X 限 ARM64、ETM3X/PTM 支持 32 位，均已在 K 的 Kconfig 直接核实（00 §5.4 [已证实]）。bcm2711 的 DT 闭包无 CoreSight 节点 [已证实]，但芯片物理上是否有未接出的 ETM 属 HQ 问题 [需核实]。
- 移植可行性：ETMv4 有内存映射寄存器路径，理论可行；难点在系统寄存器访问路径与 ETE/TRBE 代码的隔离 [需核实]。2–4 周估计偏乐观（[推断]，驱动移植 + 验证链通常更长）。
- perf 对 A32/T32 的 ETM 解码完整性：OpenCSD 支持 A32/T32 是解码库能力 [外部]，perf inject 合成链在 32 位内核 trace 上的完整性未验证 [需核实]——需要已知答案的 trace 夹具。
- 结论：列在最后、等产品 SoC 信息是正确的。

### Q5：D 组（尺寸优化与冷热拆分）在 ARM32 上的可行性

- PGSO 机制与默认值已核实（`SizeOpts.cpp:18–59` [已证实]）；它是多处优化的尺寸倾向，不保证 ARM32 每个 pass 都有收益 [需实测]。**"无样本即 minsize"不是现有行为**，D1 的措辞要保持这一点。
- 方案遗漏的手段（按价值排序）：
  1. **冷文件按 -Os 编译**：kbuild 原生支持 `CFLAGS_<file>.o`，把"从未采到样本的文件"整体 -Os，比逐函数 PGSO 更直接、更可控；需 D3 的覆盖证据支撑，风险同样标出。
  2. **THUMB2_KERNEL=y**：A32→Thumb-2 的 text 缩减约 20–30% [推断，量级依经验，未实测]，比任何 profile 引导的尺寸手段都大一个量级。上游支持存在；K 的 defconfig 现为 n、K1 明确排除 Thumb——建议把它列为 K2 的独立候选并如实写明风险（需完整启动与基准验证；正是本项目已建立的 ARM/Thumb 工具链能力可直接复用）。
  3. 冷代码降低对齐要求（对齐填充在嵌入式 ARM 上是可见的尺寸来源 [推断]）；属编译器选项级，评估成本低于 PGSO 调参。
- 冷热拆分（D2）在内核主要是速度项，作者已正确注明对内存帮助小 ✓；用户态库的页聚簇（热页集中）对 TV 产品的常驻页有实际意义 ✓。

### Q6：方案之外更好的做法

1. **ftrace 函数入口计数**（最大遗漏，见 Q3）：生产内核自带、零移植；补 IP 采样缺的"调用次数"维度；可直接作为 llvm-profgen `entry-estimate` 的校准源或 B1 的轻量输入。验证：开 `function_profile_enabled` 跑基准，读 tracing 目录计数，与 A4/插桩互验。
2. **kprobe 级热分支计数**（实验室）：对已识别的热点函数，用 kprobe 在少数热分支指令上精确计数，得到局部真实边频率——比 A4 全内核插桩便宜得多，可作为 B1 的方向来源的最小可行版。[推断，未验证 overhead]
3. 不建议的方向：BOLT（不支持 32 位 ARM，正确排除）；Propeller（ARM32 basic-block sections 被驱动拒绝，`Clang.cpp:6190–6220` [已证实]）。

### Q7：路线顺序与工作量

- 顺序合理：P0（探针/回移植检查）→ P1（C1+A1）→ P2（A2/A4）→ P3（融合）。
- 明显偏低的估计：A4（3–4 周 → 应 4–6 周+，00 §5.3）；C1 的"1–2 周 + 板上启动验证"中启动验证可能占大头；A1 的 1–2 周已由 K0 修正为 10–15 人日（一致）。
- 门槛补充：P1 的"IP-only 有可测收益"门槛建议加一个前置的可解释指标——主比较基准的"可符号化到 C 行号的内核样本占比"，避免 inconclusive 时无法区分"profile 无效"与"可优化份额不足"。

---

## 3. 与 ARM32 内核 / clang 22 / Tizen GBS 实际行为不符或风险低估之处

| # | 位置 | 问题 | 依据 |
|---|---|---|---|
| 1 | 06 §3.2 步骤 1 | "依赖编译器产生热/冷前缀节"的机制本身无架构障碍（见 11.1），但 IP-only 稀疏 profile 下判冷/判热覆盖面会很窄；文档已标"需构建验证"，建议把预期明确写低，并把节字节数列为 consumption 报告项 | `CodeGenPrepare.cpp:583–596`；PSI 判冷需三条件全冷 [已证实] |
| 2 | 06 §6.2 | N 由 K1a 单变体 CV 预估，**配对差值方差从未被测量**；预试只在 K-BASE 上做，同样测不到配对方差 | 统计方法问题，见第 4 节第 1 条 |
| 3 | 06 §2 | 训练/消费构建未提 `-funique-internal-linkage-names`；上游 Makefile.autofdo 默认没有它，内核同名 static 函数常见，匹配率会受损 | 00 §4.3 [已证实] |
| 4 | 06 §5 | R=3 次训练采样、每段固定时长：以 K1a 数据外推 pipe 段约 12 万内核样本×3，对 20 MB text 属稀疏 [推断]；建议先以首次转换的质量报告（unique 地址数、usable 率）决定是否增加 R 或段长，再冻结参数 | K1a 采样统计 [已证实]；稀疏度判断 [推断] |
| 5 | 06 §6.1 | syscall 列为"部分留出"没有检验力（60% 在汇编入口 vector_swi） | 04 syscall 前 30 表 [已证实] |
| 6 | 06 §6.1/§0.4 | 内存触页基准只覆盖 fault/memcg charge，未触发回收/swap；不要以它声称覆盖"内存压力"路径 | 04 §内存基线：回收/换出增量全 0 [已证实] |
| 7 | 01 §3 A2 | "样本 PC 近似落在跳转目标上"是未验证假设，00 已正确降级；本评审进一步判断其先验概率不高（见 Q1） | 00 §5.1 [已证实部分]；语义分析 [推断] |
| 8 | 01 §5 P1 门槛 | "IP-only 有可测收益"门槛缺少可解释性指标，inconclusive 时无法归因 | 建议见 Q7 |
| 9 | 01 §3 A4 | 3–4 周估计偏低；K0 已修正为 4–6 周或更多，方案 v0.1 未跟进 | 00 §5.3 [已证实] |
| 10 | 06 §0.3/§4 | `cp` 覆盖 zImage 非原子（FAT），掉电可砖；另见 11.2 的更好方案 | FAT 语义 [已证实] |

---

## 4. 测量方法的改进建议

1. **（必须改）N 的方差来源**：正式测量前，用 K-BASE/K-BASE 做若干 AB/BA **空对照 block**（同一内核两次启动互为 A/B），测配对 log 比的方差；N 由该方差决定。当前设计用单变体 CV 规划 N，配对设计可能更紧也可能更松（重启引入的共同波动被配对消除，但变体间残余差异未知），空对照是唯一正确的估计途径，顺带还给出"零效果时的假阳性率"实测。
2. **（必须改）zImage 切换原子性**：`cp` 覆盖改为 `cp` 到新文件 + `sync` + `mv -f`；或采纳 11.2 的 U-Boot 文件选择方案（需用户确认改 boot.scr）。
3. **（建议）block 内结构**：现设计"每 block 两次启动、每次启动跑完全部基准"正确；补充在每个 block 记录两次启动的 build-id、起跑温度与基准顺序号，供事后审计（部分已含）。
4. **（建议）ε=1% 与多重性**：主比较 pipe 单一判定 ✓；次比较/探索项不校正并如实说明 ✓——保持。空对照结果应一并报告。
5. **（建议）K1e 领先指标**：每基准的"可符号化到 C 行号的内核样本占比"与 profile 记录覆盖率，先于性能测量报告。

---

## 5. 结论

**需修改后执行。** K1 的总体架构（最小回移植、两变体只差 profile、配对测量、门槛止损）是扎实的，K0/K1a 的证据链质量高；但上一节列出的方法问题需要在 K1c/K1f 开始前修正。

必须修改（按优先级）：

1. **N 的估计改为 K-BASE/K-BASE 空对照的配对方差**（第 4 节第 1 条）；没有这一步，ε=1% 的判定没有依据。
2. **zImage 切换改原子 rename**（或 U-Boot 文件选择方案）（第 4 节第 2 条）。
3. **训练与消费构建加 `-funique-internal-linkage-names`**，并在 consumption 证据中加入 record-coverage 检查（§11.4）；全局开启优化记录、主机侧过滤。
4. **K1e 增加"可符号化到 C 行号的内核样本占比"指标**，并与 §9 门槛 4 的解释规则挂钩（§11.3）。
5. **内存触页基准改名/限定口径**（不覆盖 reclaim/swap）；syscall 去掉"留出"角色。

建议（不阻塞 K1）：ftrace 函数入口计数评估（方案 v0.1 补入，作为 A4-lite 与 head samples 校准）；THUMB2_KERNEL 列为 K2 尺寸候选；A4 估时按 4–6 周；A2 维持 P0 探针 + 止损门槛。

**声明**：本评审未构建、未接板、未读取或计算任何正式 sample profile 的指标；反例均为推理或合成情形。
