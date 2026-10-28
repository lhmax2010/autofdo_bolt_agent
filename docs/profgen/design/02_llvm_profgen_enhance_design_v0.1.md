# llvm-profgen 增强设计（第一批详细设计 + 第二、三批规划）

| 项目 | 内容 |
|---|---|
| 版本 | v0.1（草案，待多方评审） |
| 状态 | 未冻结。冻结前不得据此开始实现 |
| LLVM 基线 | Tizen llvm 包源码 `f999bd406c0a70fe8107aa992164fe6945c5d46a`（LLVM 22.1.8）；上游对照 tag `llvmorg-22.1.8` |
| 参考实现 | Google AutoFDO `f95d1a170dfe24ec5ce4117aa4b0f6d836841703`（create_llvm_prof） |
| 前置材料 | `docs/spike/01_afdo_pgo_feasibility.md`、`docs/profgen/00_incremental_build.md`、`docs/profgen/01_gap_analysis.md`、`docs/probe/03_rpi4_sampling.md`、`docs/probe/04_rpi5_probe.md` |
| 适用范围 | 本文只覆盖 llvm-profgen 工具本身的增强，以及验证该增强所需的测试与评估。不包含任何 Agent 的设计与开发；Agent 在 llvm-profgen 增强完成后另行设计 |

---

## 1. 背景

1. 两块开发板（RPi4 armv7l、RPi5 aarch64）都没有分支栈、SPE、ETM，只能做普通指令地址采样（下称 IP 采样）。RPi5 可采硬件 cycles；RPi4 当前镜像只有软件 cpu-clock，加入 ARM_PMUV3 的新镜像出来后可采硬件 cycles。
2. 实测 LLVM 22.1.8 的 llvm-profgen 对纯 IP 输入直接报错 `Invalid perf script input!`（源码 `PerfReader.cpp:1186–1218`），没有降级路径。
3. Google create_llvm_prof 的 `--use_lbr=false` 路径支持 IP 采样，但它是 LLVM 之外的独立工具，依赖 perf_data_converter 等外部组件，且默认构建不含 32 位 ARM。
4. 差异分析（`01_gap_analysis.md`）确认：create_llvm_prof 真正领先的功能共 11 项；行级/内联计数、discriminator、入口计数、间接调用目标、输出格式、裁剪等 llvm-profgen 已具备。
5. 插桩 PGO 已在 RPi5 上完整跑通，可作为保底方案，也可作为评估 IP profile 质量的"真实执行计数"基准。

## 2. 目标与非目标

### 2.1 目标

1. 把 llvm-profgen 增强为在无分支栈硬件上也能生成可用 AutoFDO profile 的工具，覆盖 x86_64 主机处理 aarch64 与 armv7l（ARM/Thumb）数据。
2. 吸收 create_llvm_prof 的全部有效优势，并加入本项目需要、但两个工具都没有的能力（第 8 节汇总）。
3. 工具输出必须"机器可判定"：除 profile 外，同时输出结构化质量报告，调用方（人工或任何自动化流程）可以依据报告而不只是退出码判断 profile 是否可用。
4. 代码按 LLVM 上游规范编写，具备上游提交的条件。

### 2.2 非目标（本批）

1. 不修改 clang/LLVM 的 profile 消费端（SampleProfileLoader 等）。只给出编译选项建议与评估方案。
2. 不实现 SPE、Propeller、预取/LLC 提示（第三批）。
3. 不实现原生 perf.data 解析与内核模块（第二批）。
4. 不处理 GCC 的 AutoFDO 消费（gcov 格式输出已存在，不在本项目验证范围）。
5. 不包含 Agent：板上采集的自动化、Benchmark 场景管理、profile 提交到包仓库、多场景权重等均不在本文范围。本文的测试与评估所需的采集和构建，由人工按测试步骤执行。

## 3. 硬约束

| 编号 | 约束 | 验证方式 |
|---|---|---|
| C1 | 不使用任何新选项时，已有全部输入路径（LBR、LBR+调用栈、unsymbolized、ETM 等）的行为与输出逐字节不变 | 已有 lit 测试全部通过；对已有测试输入，新旧工具生成的 profile 二进制比对一致 |
| C2 | 改动范围限于 `llvm/tools/llvm-profgen/`、其测试目录与命令文档。如需修改 LLVM 库（ProfileData、DebugInfo、MC 等），必须在实现前单独申报理由与影响面 | 补丁 diffstat 检查 |
| C3 | 不影响其他 RPM 包的编译与运行：增强只在使用 llvm-profgen 时生效 | 改动范围检查；llvm 包 GBS 构建产物中除 llvm-profgen 外其余二进制一致性抽查 |
| C4 | 不拷贝 autofdo 源码。参考其算法自行实现；若沿用某处实现细节，在提交说明中列出位置与理由 | 代码评审 |
| C5 | 无法在现有硬件上验证的功能不进入 llvm 包 | 每项功能必须有可执行的验收用例 |
| C6 | 开发验证用 GBS 增量构建；正式交付前必须做一次非增量的正常 GBS 构建 | 构建记录 |

## 4. 现有架构与扩展点

现有数据流：

```
perf.data ──(调用 perf script -F ip,brstack)──┐
perf script 文本 ─────────────────────────────┤→ PerfReader（LBR / LBRStack）
                                              │      ↓
                                              │  SampleCounter（RangeCounter + BranchCounter）
                                              │      ↓
ProfiledBinary（ELF 加载、全量反汇编、DWARF/pseudo-probe 解码、符号化）
                                              │      ↓
                                ProfileGenerator / CSProfileGenerator
                                              │      ↓
                                     SampleProfileWriter（text/binary/extbinary/gcc）
```

本设计新增的部分：

```
perf.data / perf script 文本（无分支栈）
        ↓
  IPPerfReader（新）：解析 mmap、pid、event、period、ip
        ↓
  身份校验层（新）：build-id / 名称筛选 / 同名歧义检查
        ↓
  AddressCounter（新）：每个目标二进制内偏移 → 权重
        ↓
  IPProfileGenerator（新）：只符号化被采到的地址 → 行级 / probe 级计数
        ↓
  SampleProfileWriter（复用）  +  质量报告 JSON（新）
```

设计原则：

1. IP 路径与 LBR 路径在数据结构上分开。不把 IP 样本伪装成长度为 0 的 LBR 区间，避免与 RangeCounter 的"执行次数"语义混淆，也避免影响已有代码。
2. 复用 ProfiledBinary 的 ELF 加载、DWARF 内联栈符号化、pseudo-probe 解码，以及 SampleProfileWriter。
3. IP 模式只对实际被采样到的唯一地址做符号化（惰性），不依赖全量反汇编完成计数。如果现有 ProfiledBinary 的加载流程强制全量反汇编，第一批先保持现状，同时记录 Chromium 规模下的内存与耗时（见 6.6）。

## 5. 第一批：详细设计

第一批包含：IP 输入、身份校验、行级与 probe 级计数生成、质量报告、ARM/Thumb 与内核镜像支持、质量评估方法。

### 5.1 命令行接口

新增选项（名称为提案，评审可改）：

| 选项 | 含义 | 默认值 |
|---|---|---|
| `--ip-samples` | 启用 IP 采样输入模式。输入可为 `--perfscript`（需按 5.2 的字段导出）或 `--perfdata`（工具按 5.2 调用 perf script） | 关闭 |
| `--ip-event=<name>` | 只统计指定事件（如 `cycles`、`cpu-clock`）。输入中出现多种事件且未指定时报错 | 未设置 |
| `--ip-weight=<sample\|period>` | 每个样本的权重取样本数还是 perf 记录的 period | `period`（输入无 period 字段时报错，除非显式指定 `sample`） |
| `--ip-aggregation=<sum\|max\|avg>` | 同一源码位置（行偏移 + discriminator）下多条指令的计数合并方式，见 5.4 | 由 5.8 的评估决定后写入；评估前不设默认值，必须显式指定 |
| `--perf-buildid-list=<file>` | `perf buildid-list` 的输出，供 `--perfscript` 输入做身份校验 | 未设置 |
| `--binary-match-regex=<re>` | 用正则匹配 mmap 中的目标 DSO 路径（默认按 `--binary` 的文件名匹配） | 未设置 |
| `--allow-missing-build-id` | 输入中找不到目标二进制的 build-id 时继续（报告中标记"身份未验证"） | 关闭 |
| `--quality-report=<file>` | 输出质量报告 JSON，格式见 5.6 | 未设置 |
| `--min-symbolized-ratio=<0..1>` | 目标二进制内样本的符号化成功率低于此值时以失败退出 | `0.9`（待评估） |

已有选项在 IP 模式下的行为：

1. `--binary`、`--output`、`--format`、`--kernel`、`--pid` 等保持原义。
2. 与 LBR 专属语义冲突的选项（上下文敏感、`--use-dwarf-correlation` 等）在 IP 模式下一律报错，不静默忽略。完整冲突清单在实现前列出并进入评审。
3. `--ip-samples` 只能显式开启，不做自动识别。原因：当前无 LBR 输入会报错，若改为自动降级，就改变了已有行为（违反 C1），也可能掩盖采集配置错误。

### 5.2 输入格式

perf script 导出命令（板上或主机执行均可）：

```
perf script -i <perf.data> --show-mmap-events -F pid,tid,event,ip,period,dso
```

解析规则：

1. 记录类型：MMAP/MMAP2 事件维护每个 pid 的地址映射；其余行为样本行。复用现有 mmap 事件解析逻辑，扩展 MMAP2 的 build-id 字段（若存在）。
2. 样本行字段缺失（无 period 且 `--ip-weight=period`、无 event）时整份输入报错，不逐行猜测。
3. 内核地址：仅在 `--kernel` 模式下计入；否则计入"非目标样本"统计。
4. `--perfdata` 输入时，工具内部调用主机 perf，参数同上；主机 perf 的路径与版本写入质量报告。主机 perf 无法读取该数据时报错，并提示改用板上导出的文本。
5. 丢样：解析 perf script 输出中的丢样提示，或要求调用方通过 `--perf-lost-samples=<n>` 传入（二选一，实现前确定），写入质量报告。

### 5.3 身份校验

1. 目标二进制 build-id 从 `--binary` 的 `.note.gnu.build-id` 读取。
2. 输入侧 build-id 的来源，按优先级：MMAP2 事件中的 build-id → `--perf-buildid-list` 文件 → `--perfdata` 输入时由工具调用 `perf buildid-list`。
3. 判定：
   - 两侧都有且不一致：报错退出，报告中写明两侧的值。
   - 输入侧没有：无 `--allow-missing-build-id` 时报错；有则继续，报告标记 `identity: unverified`。
   - 目标二进制本身没有 build-id：报错（`--allow-missing-build-id` 同样可放行）。
4. 名称匹配：默认按 `--binary` 的文件名匹配 mmap 路径。同一 pid 内出现多个同名但不同路径或不同 build-id 的 DSO 时，报"歧义"错误，要求用 `--binary-match-regex` 或 build-id 区分，不合并计数。
5. 地址换算：复用现有的 mmap 偏移与段映射逻辑。新增测试覆盖：PIE 可执行文件、共享库、多个可执行 PT_LOAD 段、AArch64 16K/64K 页大小的二进制（现有代码 `ProfiledBinary.cpp:336–365` 假设 4K 页，需要核实并在必要时修正）。
6. 身份校验在 LBR 路径中默认不启用，以满足 C1；后续可另加选项让 LBR 路径也使用。

### 5.4 计数生成：行级（DWARF）模式

1. AddressCounter：每个目标二进制一个 `map<偏移, 权重>`，权重按 `--ip-weight` 累加。
2. 符号化：对每个唯一偏移调用 ProfiledBinary 的内联栈符号化，得到"函数 → 内联调用点链 → 行偏移 + discriminator"。
3. 写入 FunctionSamples：
   - 最内层帧的 (行偏移, discriminator) 计入 body samples；
   - 外层帧通过 callsite FunctionSamples 构建内联上下文，与 LBR 路径的非 CS profile 结构保持一致；
   - 函数 total samples = 其下全部计数之和。
4. 同一源码位置有多条指令时的合并（`--ip-aggregation`）：
   - IP 样本与 LBR 的语义不同：LBR 区间内每条指令执行次数相同，因此 LBR 路径取 MAX 合理；IP 样本数近似"执行次数 × 该指令的停顿周期"，长语句的指令多、停顿不均。
   - 三种候选：`sum`（该位置耗时之和）、`max`（最热指令）、`avg`（总和除以该位置在二进制中的指令条数，近似执行次数 × 平均 CPI）。
   - 不在设计阶段拍板：按 5.8 用插桩 PGO 的真实执行计数作为基准，三种方式都测，选与基准相关性最高者作为默认值，评估数据写入实现报告并重新评审。
   - `avg` 需要每个位置的指令条数，需要对相关函数做反汇编；只对有样本的函数做。
5. duplication factor：与现有路径一致，按 `-fdebug-info-for-profiling` 编码的 discriminator 解码。是否与 `avg` 叠加要在评估中一并确认，避免重复补偿。
6. 入口计数（head samples）：IP 数据无法得到真实调用次数，默认不写。不得用函数总样本数冒充入口计数。若评估证明某种估计方式对内联决策有明显帮助，作为独立选项另行评审。
7. 间接调用目标：IP 数据无法得到，不写。

### 5.5 计数生成：pseudo-probe 模式

动机：pseudo-probe 以基本块为单位标识位置，不受行号漂移影响，函数还带 CFG 校验和。clang 的过期 profile 匹配（stale profile matching）依赖它，这直接服务于"代码改动后不必频繁重新采集"的目标。Google 工具没有这个模式。

1. 二进制含 `.pseudo_probe` 段时，可以用新选项 `--ip-use-probes`（提案）启用；否则报错。
2. 地址到 probe 的映射：复用 MCPseudoProbeDecoder 已解码的 probe 地址。一个 IP 落在哪个块，按"同一函数内、地址不大于 IP 的最近一个块 probe"确定。块重排后同一块可能不连续，这一规则在跨块指令处可能出错：映射规则本身也纳入 5.8 的评估，并与按反汇编块边界精确映射的方案对比。
3. 输出 probe-based 非 CS profile，与现有 probe 路径的输出格式一致（函数 CFG 校验和保留）。
4. 本模式依赖构建时加 `-fpseudo-probe-for-profiling`。它是否影响代码生成与性能（probe 对优化的干扰）要在 5.8 中单独测量。

### 5.6 质量报告

`--quality-report` 输出 JSON，字段至少包括：

| 字段 | 说明 |
|---|---|
| `tool_version`、`options` | 工具版本与完整参数 |
| `input` | 输入文件路径、SHA-256、事件名、权重方式、perf 版本（若调用了 perf） |
| `identity` | 目标二进制路径、build-id、输入侧 build-id、判定结果（`verified` / `unverified` / `mismatch`） |
| `samples.total` | 输入中的样本总数 |
| `samples.lost` | 丢样数（来源见 5.2 第 5 条） |
| `samples.target` | 落入目标二进制的样本数与权重 |
| `samples.symbolized` | 成功符号化到有行号（或 probe）的样本数与权重 |
| `samples.no_debug_info` | 落入目标二进制但无调试信息的样本数（按函数列出前 20） |
| `samples.other_dso` | 落入其他 DSO 的样本数（按 DSO 列出前 20） |
| `samples.kernel` | 内核样本数 |
| `coverage` | 有样本的函数数、唯一地址数、权重最高的前 50 个函数及其占比 |
| `warnings` | 全部告警 |
| `verdict` | `ok` / `failed`，以及失败原因 |

退出码：身份不一致、`samples.target == 0`、符号化率低于 `--min-symbolized-ratio` 时返回非 0，并仍写出报告。各比例的分母在报告中写明，不把"没采到"和"符号缺失"混在同一分母里。

### 5.7 架构支持

| 目标 | 要求 | 风险与验证 |
|---|---|---|
| aarch64 | ELF64 小端；PIE 与共享库 | 用 RPi5 已采的数据验证 |
| armv7l ARM/Thumb | ELF32；Thumb 地址最低位、映射符号（`$a`/`$t`/`$d`）、ARM 与 Thumb 混合代码 | llvm-profgen 现有代码对 Thumb 未有实测；如全量反汇编在 Thumb 上出错，IP 模式需绕开全量反汇编（见第 4 节第 3 条）。用 RPi4 数据验证，是第一批的验收必需项 |
| vmlinux（`--kernel`） | 复用现有内核匹配与 KASLR 处理 | 用 RPi5 内核采样验证 aarch64；armv7l 内核待新镜像 |

### 5.8 质量评估方法（第一批核心验收）

目的：决定 `--ip-aggregation` 的默认值、行级与 probe 模式的取舍，并量化 IP profile 相对插桩 PGO 的质量。

1. 基准（真实执行计数）：同一源码、同一输入，用插桩 PGO 得到每个基本块的执行次数。插桩构建用 `-fprofile-generate`，读取 `.profdata` 中的块计数。
2. 被评估对象：同一源码以 `-gline-tables-only -fdebug-info-for-profiling -funique-internal-linkage-names`（probe 模式另加 `-fpseudo-probe-for-profiling`）构建，在板上采 IP 样本生成 profile。
3. 对齐方式：以"函数 + 行偏移 + discriminator"（或 probe id）为键，把插桩块计数投影到同一键空间。投影规则写进评估脚本，并对小程序人工核对一遍。
4. 指标：
   - 热点函数覆盖：插桩计数占比合计 95% 的函数集合中，有多少在 IP profile 中有样本；
   - 函数级排序一致性：函数总计数的 Spearman 相关系数；
   - 函数内块级排序一致性：每个热点函数内各位置计数的 Spearman 相关系数，按权重平均；
   - 重编后的性能：见第 3 条以外的 5.9。
5. 样本：spike 测试程序；libavcodec（FFmpeg H.264 解码）；RPi5 用 cycles，RPi4 用 cpu-clock 与新镜像的 cycles 分别评估。
6. 判定：选择指标最好的聚合方式作为默认值；若三种方式差异小于不同采样之间的波动，选实现最简单者。评估数据与决定一起提交评审。

### 5.9 编译端选项评估（不改 clang）

| 组合 | 说明 |
|---|---|
| 基线 | 不用 profile |
| IP 行级 | `-fprofile-sample-use=<prof>` |
| IP 行级 + profi | 另加 `-mllvm -sample-profile-use-profi`（让编译器根据块计数推断一致的边计数，对缺少边信息的 IP profile 可能更重要） |
| IP probe | `-fpseudo-probe-for-profiling -fprofile-sample-use=<prof>` |
| IP probe + 过期匹配 | 另加 `-mllvm -salvage-stale-profile`，用于代码改动后的复用测试 |
| 插桩 PGO | `-fprofile-use=<profdata>`（对照组） |

`-fprofile-sample-accurate` 会把无样本的函数当作冷函数；IP 采样稀疏时风险较高，第一批只在评估中观察，不作为推荐默认。上述 `-mllvm` 选项在 LLVM 22.1.8 中是否存在、语义是否如上，由实现阶段先用源码确认。

性能测量（仅用于验证本增强，不是 Agent 功能）：RPi5 与 RPi4 各自在 FFmpeg H.264 解码上做；每组至少 5 轮、各组交错执行；记录测试环境（镜像 BUILD_ID、内核 uname -v、库 build-id、换出统计 pswpout）；运行期间换出明显增加的轮次标记为干扰并剔除。

过期复用测试：对 libavcodec 做一处小的源码改动（例如改动一个热点外的函数和一个热点函数内的一行），用旧 profile 编译，比较收益保留比例与诊断告警，分别测行级与 probe + 过期匹配。

### 5.10 测试

1. 回归：改动前后各跑一次 `llvm/test/tools/llvm-profgen/` 全部 lit 测试，结果一致；对已有测试输入逐个比对新旧工具生成的 profile（C1）。
2. 新增 lit 测试（小体积输入，二进制随测试提交）：
   - aarch64 PIE 可执行文件，行级，三种聚合方式各一；
   - aarch64 共享库，带非零加载基址；
   - ARM Thumb 可执行文件；
   - vmlinux（`--kernel`）最小样例；
   - probe 模式；
   - 负对照：build-id 不一致、同名 DSO 歧义、多事件未指定 `--ip-event`、缺 period 字段、符号化率低于门槛。每个负对照必须实际失败并检查报错文本。
3. 独立核对：用与 llvm-profgen 无关的脚本（平台 llvm-symbolizer + `--inlines`）重算行级计数，与工具输出逐行比对；并做地址整体偏移的负对照，确认核对脚本能发现错误。
4. 规模：用 libavcodec 记录工具峰值内存与耗时；Chromium 规模测试放在第二批（6.6）。

### 5.11 第一批交付物

1. 补丁序列（基于 `f999bd40`），每个补丁可独立编译、测试通过。建议拆分：IP 读取与计数；身份校验；行级生成；probe 生成；质量报告；测试与文档。
2. 独立核对脚本与质量评估脚本（放本项目仓库 `tools/`）。
3. 实现报告：回归结果、新增测试、独立核对结果、5.8 评估数据与默认值决定、5.9 性能数据、已知局限。
4. llvm 包的一次正常（非增量）GBS 构建记录。

## 6. 第二批：规划（第一批完成后再出详细设计）

| 项目 | 目标 | 接口约束（第一批需预留） |
|---|---|---|
| 6.1 内核模块（.ko，ET_REL） | 支持模块的 IP profile：按模块加载地址与 `.text` 等节换算偏移 | 身份层按"模块名 + build-id"识别；AddressCounter 以"二进制 + 节"为键，不假设单一可执行段 |
| 6.2 原生 perf.data 解析 | 不依赖主机 perf：直接读 perf.data 的 header、attr、MMAP2、COMM、FORK、SAMPLE、build-id 表、丢样记录；按文件中的 ABI 与字节序解析 | IP 读取层对上游只暴露"样本流 + 映射事件"接口，文本与原生两种来源可替换 |
| 6.3 大规模二进制（Chromium） | 峰值内存与耗时目标；惰性符号化；分阶段释放缓存 | 第一批报告中记录 libavcodec 的内存与耗时作为外推基础 |
| 6.4 冷函数符号列表 | 在现有 `--populate-profile-symbol-list` 上增加按函数大小覆盖率的选取策略；对 IP 稀疏采样的误判做保护（仅在身份已验证、样本量达标时启用） | 质量报告提供样本量指标 |
| 6.5 IP 模式阈值与裁剪 | 稀疏样本的噪声过滤：最小样本阈值、按总量比例裁剪 | 与现有 CS 冷上下文裁剪互不干扰 |
| 6.6 多份采样合并 | 不在 llvm-profgen 内实现多输入合并：每份采样单独生成 profile，再用已有的 `llvm-profdata merge --sample --weighted-input=<权重>,<文件>` 合并 | 质量报告包含合并所需的身份与事件信息，供调用方在合并前核对一致性 |

## 7. 第三批：登记（条件具备后立项）

| 项目 | 立项条件 | 备注 |
|---|---|---|
| ARM SPE 输入 | 有带 SPE 的板子 | SPE 是统计采样，不是连续 trace；不能套用 LBR 区间假设 |
| BRBE | 有带 BRBE 的板子 | 先验证 perf 输出的分支记录能否直接走现有 LBR 解析 |
| Propeller 布局 profile | 有分支栈（LBR/BRBE）数据，且目标架构支持 `-fbasic-block-address-map`（32 位 ARM 目前不支持） | 涉及 CFG、布局算法与链接器消费，属于独立子系统 |
| 预取 / LLC miss 提示 | clang 出现可用的消费端 | 当前 clang 不使用这类信息，暂不实现 |

## 8. 超出 create_llvm_prof 的增强（汇总）

| 增强 | 作用 |
|---|---|
| 结构化质量报告与失败判定 | 调用方可依据报告判断 profile 是否可用，不只靠退出码 |
| 显式事件与权重语义（event / period） | 避免频率模式下样本数与时间不对应；避免不同事件混算 |
| 聚合方式以插桩 PGO 真实计数为基准选定 | 用数据而不是假设决定 IP 计数的合并方式 |
| pseudo-probe IP 模式 + 过期 profile 匹配 | 代码改动后 profile 仍可大部分复用，减少重新采集 |
| build-id 默认强制校验、同名 DSO 歧义报错 | 防止错误 profile 进入包仓库 |
| 惰性符号化 | 降低大二进制的内存与耗时 |
| ARM/Thumb 实测支持 | create_llvm_prof 默认不含 32 位 ARM |
| 编译端组合评估（profi、过期匹配） | 让 IP profile 的收益最大化，无需改 clang |

## 9. 工具的输入与输出约定

本节只描述 llvm-profgen 自身的输入输出，不涉及调用方如何使用。

1. 输入：perf.data，或按 5.2 导出的 perf script 文本；目标二进制（未 strip、带 build-id 与调试信息，与采样时运行的完全一致）；可选的 `perf buildid-list` 输出；事件名。
2. 输出：profile 文件（extbinary 等已有格式）；可选的质量报告 JSON。
3. 退出码：工具异常或 5.6 规定的失败条件返回非 0；其余情况返回 0，详细质量信息以报告为准。

## 10. 实施步骤与评审节点

| 步骤 | 内容 | 节点 |
|---|---|---|
| 1 | 本设计多方评审，冻结 | 冻结后才能开工 |
| 2 | 实现 IP 读取、身份校验、行级生成、质量报告；回归与新增测试；独立核对 | 代码评审 |
| 3 | 5.8 质量评估（RPi5，随后 RPi4）；确定聚合默认值 | 评估结论评审 |
| 4 | probe 模式实现与评估 | 代码与评估评审 |
| 5 | 5.9 性能与过期复用测试 | 结果评审 |
| 6 | 正常 GBS 构建；整理补丁序列 | 交付评审；由用户决定 Gerrit 合入方式与时间 |
| 7 | 第二批详细设计 | 另行评审 |

Agent 的设计与开发在 llvm-profgen 增强完成（至少第一批交付）之后开始，不与本表的步骤并行。

## 11. 风险

| 风险 | 影响 | 对策 |
|---|---|---|
| 无分支信息的 AutoFDO 收益明显低于 LBR 情形，可能低于插桩 PGO | 增强的实际价值受限 | 5.8/5.9 用数据如实给出收益，结论供后续决策 |
| Thumb 代码在现有反汇编/符号化流程中出错 | RPi4 不可用 | 第一批即用 RPi4 数据验证；必要时 IP 模式绕开全量反汇编 |
| probe 到地址的映射在块重排后不精确 | probe 模式计数偏差 | 与精确块边界映射对比评估；评估不过则 probe 模式不进入默认 |
| `-fpseudo-probe-for-profiling` 本身影响优化 | 收益被抵消 | 5.9 单独测量 |
| 主机 perf 无法读取板上 perf.data | `--perfdata` 不可用 | 第一批支持板上导出文本；第二批原生解析 |
| 与 BOLT/PGO 线同时修改 llvm 包 | 补丁冲突 | 独立分支开发；合入前由用户协调顺序 |

## 12. 待评审确认的问题

1. 5.1 中的选项命名与默认值是否合理，是否与 LLVM 现有命名风格一致。
2. 不做自动识别、必须显式 `--ip-samples` 的取舍。
3. `--ip-weight` 默认用 period 是否合适（频率模式下 period 变化；cpu-clock 的 period 是时间）。
4. 5.4 的三种聚合方式是否完整，评估方法（5.8）的投影规则与指标是否足以支撑决策。
5. probe 模式的地址映射规则（5.5 第 2 条）是否有更准确的现成实现可复用。
6. 多场景合并放在 llvm-profdata 而不是 llvm-profgen 的决定（6.6）。
7. 第一批是否遗漏了现在就能验证、且对 AutoFDO 实际使用必需的功能。
8. 5.9 中各编译选项在 LLVM 22.1.8 的实际存在性与语义。
