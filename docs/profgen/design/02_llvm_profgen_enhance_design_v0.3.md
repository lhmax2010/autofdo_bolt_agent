# llvm-profgen 增强设计（第一批详细设计 + 第二、三批规划）

| 项目 | 内容 |
|---|---|
| 版本 | v0.3（草案，第二轮评审） |
| 状态 | 未冻结。分两阶段冻结（第 10 节）：第一阶段冻结 DWARF IP 核心（采集与输入、地址换算、身份、计数规则、输出与失败契约）；第二阶段在评估后冻结默认参数，并单独决定 probe 子方案是否准入。第一阶段冻结前不得开始正式实现；冻结前验证（第 10 节步骤 1）允许一次性原型与测试素材，不构成正式实现 |
| LLVM 基线 | Tizen llvm 包源码 `f999bd406c0a70fe8107aa992164fe6945c5d46a`（LLVM 22.1.8）；上游对照 tag `llvmorg-22.1.8` |
| 参考实现 | Google AutoFDO `f95d1a170dfe24ec5ce4117aa4b0f6d836841703`（create_llvm_prof） |
| 前置材料 | `docs/spike/01_afdo_pgo_feasibility.md`、`docs/profgen/00_incremental_build.md`、`docs/profgen/01_gap_analysis.md`、`docs/probe/03_rpi4_sampling.md`、`docs/probe/04_rpi5_probe.md`、`docs/probe/05_rpi4_pmu_image_and_prefreeze.md`、`docs/probe/06_rpi4_prefreeze_followup.md` |
| 适用范围 | 本文只覆盖 llvm-profgen 工具本身的增强，以及验证该增强所需的测试与评估。不包含任何 Agent 的设计与开发；Agent 在 llvm-profgen 增强完成后另行设计 |
| 评审记录 | v0.1 经 Kimi Code、Codex、Claude Code 三方评审，处理见附录 A。v0.2 未外部评审；依据冻结前板上核实（05、06 报告）修订为 v0.3，修订内容见附录 B |
| 引用约定 | `L/` = `llvm/tools/llvm-profgen/`。LLVM 行号以 `llvmorg-22.1.8` 为准（评审已核实 `L/` 下 13 个文件与 Tizen 树逐字节一致）。perf 行号以 Linux v6.12 `tools/perf` 为准，板上行为以 05、06 报告的实测为准。Google 行号以 `f95d1a17` 为准 |

---

## 1. 背景

1. 当前已验证的采样能力只有普通指令地址采样（下称 IP 采样）：
   - RPi5（aarch64，Cortex-A76）：硬件 cycles 已验证（PMU `armv8_cortex_a76`）；branch stack 采样失败；SPE、ETM 不可用。
   - RPi4（armv7l，Cortex-A72）：加入 ARM_PMUV3 的新镜像（`tizen-unified-toolchain_20261028.105834`）已验证硬件 cycles：PMU 驱动 `armv8-pmu` 绑定 `armv8_cortex_a72`，`perf evlist -v` 为 type=0、config=0，样本非空（05 报告 A 节）。旧镜像只有软件 cpu-clock，请求 cycles 时 perf 会静默回退且退出码为 0，所以每次采集都要用 `perf evlist -v` 确认事件类型。
2. LLVM 22.1.8 的 llvm-profgen 对纯 IP 输入直接报错 `Invalid perf script input!`（`L/PerfReader.cpp:1190–1218` 的 `checkPerfScriptType()`，报错在 :1216），没有降级路径。
3. Google create_llvm_prof 的 `--use_lbr=false` 路径支持 IP 采样，但它是 LLVM 之外的独立工具，依赖 perf_data_converter 等外部组件，且默认构建不含 32 位 ARM。
4. 差异分析（`01_gap_analysis.md`）确认：create_llvm_prof 真正领先的功能共 11 项；行级/内联计数、discriminator、入口计数、间接调用目标、输出格式、裁剪等 llvm-profgen 已具备。
5. 插桩 PGO 已在 RPi5（aarch64）与 RPi4（armv7l）上各完成一次小程序闭环，输出校验一致（spike 报告与 05 报告 D 节），可作为保底方案，也可作为评估 IP profile 质量的参考。
6. 已核实、且直接影响设计的平台与工具链事实：
   - **LLVM 镜像的 armv7l 包默认生成 Thumb-2 代码。** 项目 build.conf 中 armv7l 的 Optflags 含 `-mthumb`（06 报告 1.3 节，reference build.conf:363）。实测新镜像中 FFmpeg（libavcodec、libavutil、libavformat、libswscale）、GLib、GObject、GStreamer 各库与 libstdc++ 的已定义动态函数全部是 Thumb；libc 与 ld-linux 以 ARM 为主；不引用 `%{optflags}` 的包（例如直接调用 clang 的 spike）生成 ARM。因此镜像是 ARM 与 Thumb 混合的，主要多媒体库是 Thumb。只看通用 rpmrc 或裸 clang 的默认 triple 不能推断包级编译模式。
   - 板上现有库已 strip、没有 `.symtab` 与 DWARF；libavcodec、GStreamer 等库没有 build-id，但 libc、ld-linux、内核与 vdso 有 build-id（05 报告 B.6）。评估一律重新构建带调试信息的库。
   - RPi4 页大小为 4096（05 报告 B.1）。RPi5 尚未实测（第 10 节步骤 1）。本设计的地址换算与页大小无关（5.3.1）。
   - Tizen clang 对 armv7l 与 aarch64 两个目标，在任何 `-fprofile-sample-use` 下都默认追加 `-mllvm -sample-profile-use-profi`，加 `-fno-sample-profile-use-profi` 后消失（05 报告 C.1；驱动源码 `clang/lib/Driver/ToolChains/Clang.cpp:6277–6282`）。在 pass 内部，profi 只对 CS、preinlined、probe profile 自动开启（`llvm/lib/Transforms/IPO/SampleProfile.cpp:2015–2021`）。因此经 clang 驱动编译时，行级 IP profile 默认就开着 profi。
   - Tizen 的 Unified 与 Base 仓库都没有 x86_64 的 `linux-kernel-perf` 包（06 报告第 3 节），主机上目前没有可用的 perf。

## 2. 目标与非目标

### 2.1 目标

1. 把 llvm-profgen 增强为在无分支栈硬件上也能生成可用 AutoFDO profile 的工具。运行环境是 x86_64 主机，处理 aarch64 与 armv7l 的数据；armv7l 上的 Thumb-2 与 A32 两种代码都是第一批的完整支持对象（5.7）。
2. 按第 5–7 节分批吸收 create_llvm_prof 的有效优势，并加入本项目需要、但两个工具都没有的能力（第 8 节）。差异分析只是候选来源，不构成额外的交付承诺。
3. 工具输出"机器可判定"：除 profile 外，输出结构化质量报告，分别表达转换是否有效、身份是否可信、采样是否充分。运行时收益由独立评估确认，转换成功不等于证明有收益。
4. 生成的 IP profile 在 clang 中的消费语义正确：函数入口计数合理、分支权重不饱和、profile 记录覆盖率可查。给出推荐的 clang 端配置（5.9）。
5. 代码按 LLVM 上游规范编写，具备上游提交的条件。

### 2.2 非目标（第一批）

1. 不修改 clang/LLVM 的 profile 消费端（SampleProfileLoader 等）。只给出编译选项建议与评估方案。
2. 不实现 SPE、BRBE、Propeller、预取/LLC 提示，也不实现原生 perf.data 解析（均在第三批，见第 7 节）。
3. 不生成内核 profile（vmlinux 与内核模块均移到第二批，见 6.1）。第一批只识别并统计内核样本。
4. 不处理 GCC 的 AutoFDO 消费（gcov 格式输出已存在，不在本项目验证范围）。
5. 不包含 Agent：板上采集的自动化、Benchmark 场景管理、profile 提交到包仓库、多场景权重等均不在本文范围。本文的测试与评估所需的采集和构建，由人工按测试步骤执行。

## 3. 硬约束

| 编号 | 约束 | 验证方式 |
|---|---|---|
| C1 | 不使用任何新选项时，对既有命令行（固定输入、固定外部 perf 版本）：profile 内容、stderr 与退出码逐字节不变；`--help`、`--version` 的输出除外。22.1.8 的 reader 只识别 LBR 与 LBR+调用栈两类 perf 输入（`L/PerfReader.cpp:1190–1218`），本文不宣称存在独立的 ETM reader。对 ProfiledBinary、PerfReader 等共享代码的改动一律由 IP 模式门控。LBR 路径的既有问题（例如 4K 页的 FIXME，`L/ProfiledBinary.cpp:340`）不在本设计中修正，需要时另行提交 | lit 全部通过；每个已有测试输入在 text、binary、extbinary、gcc 四种格式下比对新旧工具的 profile 与 stderr；`--perfdata` 路径人工比对一次；不加 `--ip-samples` 时纯 IP 输入仍报原错误文本；主机 CPU 支持 LBR 时另采 x86 LBR 数据扩充比对语料 |
| C2 | 改动范围限于 `llvm/tools/llvm-profgen/`、其测试目录与命令文档。build-id 读取用现有 `object::getBuildID`（`llvm/include/llvm/Object/BuildID.h:33–37`），JSON 用 `llvm/Support/JSON.h`，SHA-256 用 LLVM Support；地址换算公式参考 BOLT（`BinaryContext.cpp:2227–2256`），Thumb 解码与映射符号切换参考 llvm-objdump（`llvm-objdump.cpp:2724–2735`、`:2320–2337`），均在工具内局部实现。如仍需修改 LLVM 库，必须在实现前单独申报理由与影响面 | 补丁 diffstat 检查 |
| C3 | 不影响其他 RPM 包的编译与运行：增强只在使用 llvm-profgen 时生效 | 检查工具目录以外的源码、公共 ABI 与链接依赖没有变化；只在可复现构建条件成立时要求其他产物逐字节一致，否则解释差异并抽查相关工具的行为 |
| C4 | 不拷贝 autofdo 源码。参考其算法自行实现；若沿用某处实现细节，在提交说明中列出位置与理由 | 代码评审 |
| C5 | 每项功能必须有可执行的验收用例。解析、地址换算、跨架构 ELF 处理这类格式或公式层面的逻辑，可用离线合成输入（lit）验证；涉及真实采样语义与性能的结论，必须有相应的板上运行证据。无法用任何方式验证的功能不进入 llvm 包 | 验收表分别标注"离线正确性""板上闭环""性能"，三者不能互相代替 |
| C6 | 开发验证用 GBS 增量构建；正式交付前必须做一次非增量的正常 GBS 构建 | 构建记录 |

## 4. 现有架构与扩展点

### 4.1 现状（经评审核实）

1. `ProfiledBinary` 在读取 perf 数据之前构造（`L/llvm-profgen.cpp:160–162`）。`load()` 无条件执行全量反汇编（`L/ProfiledBinary.cpp:272`）。FS discriminator 的检测放在反汇编流程末尾，且只查 `--binary` 自身的符号（`L/ProfiledBinary.cpp:808–824`）。
2. 地址换算：每个二进制只有一个全局 `BaseAddress`（`L/ProfiledBinary.h:422–430`）；`updateBinaryAddress` 按事件顺序覆盖它，不区分 pid（`L/PerfReader.cpp:534–585`）；没有 FORK/EXIT 处理；`--perfdata` 的 PID 预扫描只收集出现过 mmap 的 pid，fork 出的子进程会被排除（`L/PerfReader.cpp:472–500`）；段偏移按 4K 掩码（`L/ProfiledBinary.cpp:340–353`）。
3. 符号化已经是按地址惰性进行并缓存的（`L/ProfiledBinary.h:581–597`），这不是新能力。
4. 反汇编只创建一个由 triple 决定的 ARM 解码器，没有 Thumb 模式；`$a`、`$t`、`$d` 映射符号被当作普通分段点（`L/ProfiledBinary.cpp:684–740`）。因此 Thumb 代码会按 ARM 模式解码，A32 中的 literal pool 也会被当作指令解码。完全 strip 的 `--binary` 没有 `.symtab`，反汇编找不到符号，`addressIsCode()` 全部返回 false。由于 LLVM 镜像的主要 armv7l 库是 Thumb（第 1 节第 6 条），现有加载流程无法用于这些库。
5. probe 查找：`AddressProbesMap::find()` 要求地址精确相等（`llvm/include/llvm/MC/MCPseudoProbe.h:225–247`）。LBR 路径能命中，是因为它在执行区间内按反汇编结果逐指令步进（`L/ProfileGenerator.cpp:1213–1244`）。

### 4.2 新增的数据流

```
perf script 文本（板上按 5.2.2 导出；第一批的主输入）────────┐
perf.data ──（有可用主机 perf 时：IP 模式自带的单次调用，5.2.4）──┤
                                                              ↓
  IPPerfReader（新）：严格解析样本行（pid/tid、period、event、ip、dsoff）、
                      MMAP2 行（只取逐映射 build-id）、LOST 行
                                                              ↓
  身份层（新）：逐映射 build-id、buildid-list、--binary 与 --debug-binary 身份链、歧义判定
                                                              ↓
  地址换算（新）：文件偏移 → 包含它的可执行 PT_LOAD → ELF 虚拟地址（与页大小无关）
                                                              ↓
  AddressCounter（新）：ELF 虚拟地址 → {sample_count, period_sum}
                                                              ↓
  ProfileGenerator::populateBodySamplesFromAddresses()（新，与 populateBodySamplesForAllFunctions() 并列）
     复用：内联链构建与 total 累计、MAX + duplication、postProcessProfiles()（裁剪、summary、密度）
     按需：对有样本的函数做指令边界枚举（A64/A32 定长；Thumb 用第二解码器，5.7）
                                                              ↓
  SampleProfileWriter（复用）  +  质量报告 JSON（新，llvm::json::OStream）
```

### 4.3 设计原则

1. IP 路径与 LBR 路径在数据结构上分开。不把 IP 样本伪装成长度为 0 的 LBR 区间，避免与 RangeCounter 的"执行次数"语义混淆，也避免影响已有代码。（测试中可以用 [ip, ip] 区间注入的结果，作为 `max` 方式的参考输出，见 5.10。）
2. 不新建 IPProfileGenerator 类。在 `ProfileGenerator` 内新增 `populateBodySamplesFromAddresses()`，复用叶子 profile 与内联链的构建、total 累计（`L/ProfileGenerator.cpp:637–670`）、MAX 与 duplication 补偿（:393–412）以及后处理（:530–537）。新建类会复制这些逻辑，上游也更难接受。
3. IP 专用加载策略，第一批即实施（只在 `--ip-samples` 时生效，原有模式继续使用原加载流程，满足 C1）：
   - 必需：目标架构、ELF 段与节、身份、调试文件、DWARF 函数区间（`findFuncRange`，`L/ProfiledBinary.h:522–533`）、FS discriminator 标记、符号化器。
   - 不做：全量反汇编；不使用 `addressIsCode`、`CodeAddressVec`；不做 prolog/epilog 推断。
   - 按需、只对有样本的函数做：指令边界枚举，供 `avg` 分母、补零枚举、skid 调整使用（5.7.2）。
   - `checkUseFSDiscriminator` 单独保留：先查 `--binary` 的符号表；`--binary` 已 strip 时查 `--debug-binary`。
   - 理由：IP 行级计数只依赖 DWARF；现有反汇编在 Thumb 和 `$d` 上必然出错；strip-all 的 `--binary` 下 `addressIsCode` 全部为假；跳过全量反汇编还会减少大二进制的耗时（是否降低峰值内存以测量为准）。
4. 依赖全量反汇编结果的诊断选项（`--show-disassembly-only` 等）在 IP 模式下报错，见 5.1.3。

## 5. 第一批：详细设计

第一批包含：IP 输入（板上导出的 perf script 文本；有可用主机 perf 时另含 `--perfdata`）、基于 perf `dsoff` 的地址换算、身份校验（含分离调试文件）、行级计数生成、质量报告与失败契约、aarch64 与 armv7l（Thumb-2 与 A32）支持、质量与性能评估方法、用现有 llvm-profdata 合并 profile 的验证。

不在第一阶段冻结范围内：pseudo-probe 子方案（5.5，实验性，单独准入）；默认参数（第二阶段冻结）。

### 5.1 命令行接口

#### 5.1.1 新增选项

| 选项 | 含义 | 默认值 |
|---|---|---|
| `--ip-samples` | 启用 IP 输入模式。输入为 `--perfscript`（按 5.2.2 导出的文本），或在满足 5.2.4 条件时为 `--perfdata` | 关闭 |
| `--ip-event=<name>` | 只统计指定事件，按 perf 打印的完整事件名匹配，包括修饰符（如 `cycles:u`、`cpu-clock:ppp`）。输入中出现多种事件且未指定时报错 | 未设置 |
| `--ip-weight=<period\|sample>` | 每个地址的权重：`period` 为 Σperiod / P_ref；`sample` 为样本数。见 5.4.1 | `period` |
| `--ip-period-unit=<N>` | 显式指定 P_ref。未设置时自动取值：全部样本 period 相同（`-c` 模式）时取该值；否则取该事件 period 的中位数。合并多份 profile 时必须显式统一 | 自动 |
| `--ip-aggregation=<sum\|max\|avg>` | 同一聚合键下多条指令的合并方式，见 5.4.4 | 评估前不设默认值，必须显式指定；这一过渡行为写入 `--help` 与文档；第二阶段冻结时确定默认值，提交上游前必须确定 |
| `--ip-head-samples=<none\|entry-estimate>` | 函数入口计数（head samples）的写法，见 5.4.6 | `none`（暂定，第二阶段冻结时定稿） |
| `--ip-zero-fill=<none\|sampled-functions>` | 未采到位置的补零策略，见 5.4.7 | `none`（暂定） |
| `--ip-skid=<none\|prev-inst>` | 采样位置漂移的处理，见 5.4.8 | `none`（暂定） |
| `--binary-match-regex=<re>` | 用正则限定目标 DSO 的候选路径（默认按 `--binary` 的文件名匹配） | 未设置 |
| `--perf-buildid-list=<file>` | 板上 `perf buildid-list` 的输出，供 `--perfscript` 输入做身份校验（5.3.2） | 未设置 |
| `--allow-missing-build-id` | 输入侧缺少 build-id 时继续，报告标记身份未验证。只放行"缺失"，不放行"不一致" | 关闭 |
| `--quality-report=<file>` | 输出质量报告 JSON，见 5.6 | 未设置 |
| `--ip-min-symbolized-ratio=<0..1>` | 符号化率（定义见 5.6.2）低于此值时失败 | `0.9`（暂定，用 libavcodec 实测定稿） |
| `--ip-min-target-samples=<n>` | 目标二进制内样本数（数量口径）低于此值时失败 | 暂定，由评估确定 |

命名规则：只对 IP 有意义的选项统一用 `--ip-` 前缀；将来对 LBR 也可能有用的选项（`--quality-report`、`--allow-missing-build-id`、`--binary-match-regex`、`--perf-buildid-list`）不加前缀，但第一批只在 IP 模式下有效。是否把 `--ip-samples` 改为可扩展的 `--perf-sample-type=auto|ip`，列入第 12 节，由上游 RFC 决定。

#### 5.1.2 启用规则

1. `--ip-samples` 只能显式开启，不做自动识别。理由：当前工具对无 LBR 的输入报错，改为自动降级会改变已有行为（违反 C1），也可能把"忘了加 `-b`"之类的采集错误静默降级成弱 profile。
2. 不加 `--ip-samples` 时，纯 IP 输入仍报原错误文本，不追加提示（追加提示会改变 stderr，违反 C1）。
3. 上表中的任一新选项在未开启 `--ip-samples` 时使用，一律报错。
4. 对 `--ip-samples` 给出 LBR 输入：报错（第一批的 IP 模式只接受无分支栈的样本行）。

#### 5.1.3 已有选项在 IP 模式下的行为

| IP 模式下 | 选项 |
|---|---|
| 报错 | `--unsymbolized-profile`、`--llvm-sample-profile`、`--skip-symbolization`、`--data-access-perftrace`、`--ignore-stack-samples`、`--csprof-*`、`--csspgo-*`、`--use-context-cost-for-preinliner`、`--max-search-depth`、`--gen-cs-nested-profile`、`--compress-recursion`、`--mark-all-context-preinlined`、`--use-offset`、`--use-first-loadable-segment-as-base`、`--update-total-samples`、`--fill-zero-for-all-funcs`（由 `--ip-zero-fill` 替代）、`--populate-profile-symbol-list`（推迟到第二批 6.3）、`--kernel`（第一批不生成内核 profile）、`--show-disassembly-only`、`--disassemble-functions`、`--show-source-locations`、`--show-canonical-fname`、`--show-pseudo-probe`、显式给出的 `--infer-missing-frames`（按 `getNumOccurrences()` 判断，因为它默认就是 true） |
| 保留原义 | `--binary`、`--debug-binary`、`--dwp`、`--output`/`-o`、`--format`、`--use-md5`、`--pid`（按样本的 pid 过滤；fork 出的子进程 pid 不同，不会被包含）、`--show-mmap-events`（打印 IP 模式解析到的 MMAP2 记录）、`--show-detailed-warning`、`--trim-cold-profile`、`--profile-density-*`、`--show-density`、`--load-function-from-symbol`、`--use-dwarf-correlation` |

表中每个"报错"项都要有一条 lit 负对照，用 FileCheck 检查报错文本。

#### 5.1.4 带 pseudo-probe 的二进制

1. 沿用现有约定：二进制同时含 `.pseudo_probe` 与 `.pseudo_probe_desc` 时走 probe 路径（`L/ProfiledBinary.cpp:429–450`），`--use-dwarf-correlation` 强制走 DWARF（`L/ProfiledBinary.cpp:58–62`）。
2. 在 probe 子方案（5.5）通过准入之前，IP 模式遇到带 probe 的二进制且未给 `--use-dwarf-correlation` 时报错，提示"IP 模式暂不支持 probe 关联，请加 `--use-dwarf-correlation`"。这样既不新增与现有约定方向相反的开关，也不会用未验证的 probe 映射静默生成 profile。
3. 子方案通过准入后，去掉这一报错，按现有约定自动走 probe 路径。

### 5.2 采集要求与输入格式

#### 5.2.1 采集要求

1. 录制方式：
   - 推荐 `perf record --buildid-mmap ...`：带 build-id 的映像，其 MMAP2 记录直接带上内核在映射时读取的 build-id（05 报告 B.6、D 节实测与 ELF note 一致）；没有 build-id 的映像仍打印设备号、inode 与 generation。
   - 也可用默认 `perf record`：MMAP2 不带 build-id，身份依赖 `perf buildid-list`（录制结束时从文件读取）。
   - 两种方式下 `perf buildid-list` 都可能有输出：缺少 build-id 表时它会处理事件（含 MMAP2）后打印各 DSO 的 build-id（`tools/perf/builtin-buildid-list.c:101–108`、`:122–135`；05 报告 B.6 实测非空）。因此不能用 buildid-list 是否为空来判断录制方式；身份来源按 5.3.2 逐映射确定。
2. 事件：RPi5 与 RPi4（新镜像）都用 `cycles`；只有旧镜像才用 `cpu-clock`。采集时保存 `perf evlist -v` 的输出作为证据（不是工具输入）。
3. `-c <N>`（固定周期）与 `-F <freq>`（频率模式）都支持。实测：`-c` 下样本没有 PERIOD 位，`period` 字段全部等于固定周期；`-F` 下有 PERIOD 位，period 逐样本变化（05 报告 B.5）。perf script 的 `period` 字段在样本没有 PERIOD 位时回退为 `attr.sample_period`（`tools/perf/util/evsel.c:2684`）。
4. 板上导出：第一批的主输入是在板上用 5.2.2 的命令导出的文本（板上 perf 与录制所用 perf 是同一个版本）。使用 `perf buildid-list` 时也在板上导出。

#### 5.2.2 导出命令与实测格式

```
LC_ALL=C perf script -i <perf.data> --show-mmap-events --show-lost-events -F pid,tid,event,period,ip,dsoff
```

1. 一旦显式给出 `-F`（不带 `+`/`-` 前缀），perf 会清空默认字段（`tools/perf/builtin-script.c:3160–3166`），事件名不再自动出现，所以 `event` 是必须字段。字段列表不得精简。
2. `dsoff` 隐含 `dso`（`builtin-script.c:651–653`），偏移等于 `ip − 映射起点 + pgoff`（`tools/perf/util/map.c:472–486`、`util/evsel_fprintf.c:215–242`），由 perf 按线程维护的映射解析得到。05 报告中，单进程 6,496 条、双进程 13,289 条 libavcodec 样本与按 MMAP2 独立计算的偏移 100% 一致。
3. 板上 perf 6.12.80 的实际格式（05、06 报告原文）：
   - 样本行：`  <pid>/<tid>  <period> <event>:  <ip> (<路径>+0x<偏移>)`。实际顺序由 perf 决定，不按 `-F` 的排列；pid/tid 为十进制并以 `/` 连接；ip 为不带 `0x` 的十六进制。
   - MMAP2 行：`<pid>/<tid>  PERF_RECORD_MMAP2 <pid>/<tid>: [<起点>(<长度>) @ <pgoff> <设备与inode，或 <build-id>>]: <权限> <路径>`。
   - 丢样行：`<pid>/<tid>  PERF_RECORD_LOST lost <N>`。06 报告实测 942 条，N 之和 61,667，与 `perf report` 的 `Total Lost Samples` 一致。
   - 特殊 DSO：`[kernel.kallsyms]` 不带偏移；`[vdso]` 带偏移（形如 `([vdso]+0x4ec)`）。是否带偏移与是否为特殊 DSO 不是同一件事，分类一律按名称（5.2.3 第 4、5 条）。`[unknown]` DSO 尚未实测到。
4. 实测样例作为 lit 素材的来源；新格式（如 `PERF_RECORD_LOST_SAMPLES`、`[unknown]`）在取得实测样例前，按 perf 源码中的格式字符串编写素材，并注明来源。

#### 5.2.3 解析规则（严格）

1. 显式识别以下记录：样本行；`PERF_RECORD_MMAP`/`PERF_RECORD_MMAP2`（只用于读取逐映射的 build-id）；`PERF_RECORD_LOST`；`PERF_RECORD_LOST_SAMPLES`（按源码格式）；导出选项带出的其他 `PERF_RECORD_*` 行按清单计数后跳过。遇到不认识的行一律报错：perf script 的文本格式不是稳定 ABI。
2. 路径解析：DSO 路径取最后一个 ` (` 与行尾 `)` 之间的部分，偏移取最后一个 `+0x` 之后的部分，以容忍带空格的路径。
3. 必需字段缺失、整数损坏、行被截断时，整份输入报错，不逐行猜测。
4. 内核样本：DSO 为 `[kernel.kallsyms]` 或内核模块路径的样本归为内核，按 DSO 名分类，不按地址范围（armv7 的用户/内核分界取决于 VMSPLIT 配置）。第一批只计入 `samples.kernel`，不生成内核 profile。
5. 其他特殊 DSO（`[vdso]`、`[unknown]`、`//anon`、JIT 等）按名称识别：带偏移的计入 `other_dso`，不带偏移的计入 `samples.unmapped`。不得把特殊 DSO 当作文件 DSO 去匹配目标。
6. 丢样：
   - 每条 `PERF_RECORD_LOST lost N` 计为一条丢失记录、N 个丢失样本，分别统计并记录来源。
   - 节流（THROTTLE/UNTHROTTLE）不计入丢样，作为已知局限写入报告；能看到节流记录时计数。
   - "未知"不得写成 0：工具自己导出（`--perfdata`）时，没有 LOST 记录即为 0；`--perfscript` 输入时，出现 LOST 记录就记数值，否则记为 `unknown`（工具无法知道导出时是否带了该选项）。

#### 5.2.4 `--perfdata` 输入（有条件）

1. 前提：主机上有与板上录制所用 perf 版本一致、且能读取该 perf.data 的 perf。Tizen 仓库目前没有 x86_64 的 perf 包（06 报告第 3 节）。获得主机 perf 的方式（例如在工作目录内从同一内核源码为 x86_64 构建 tools/perf）由用户决定。
2. 准入：主机 perf 对同一份 perf.data 的导出与板上导出逐行一致（允许的差异逐类列明理由）之后，`--perfdata` 才进入第一批交付；否则第一批只交付 `--perfscript` 输入，`--perfdata` 在 IP 模式下报错并提示改用板上导出的文本（C5）。
3. 行为：IP 模式自带一次 perf 调用（命令同 5.2.2），不复用 LBR 路径的转换函数。现有转换函数分两次调用 perf，不检查退出码，字段固定为 `ip,brstack`，PID 预扫描会排除 fork 出的子进程（`L/PerfReader.cpp:451–519`）。LBR 路径的转换函数保持不变（C1）。
4. 检查 perf 的退出码并分别保存 stdout 与 stderr。非 0 退出、或输出部分内容后失败，都不得继续生成结果。需要 buildid-list 时另调用 `perf buildid-list`。主机 perf 的路径、版本与完整命令写入质量报告。

### 5.3 地址换算与身份校验

#### 5.3.1 地址换算

1. 对目标 DSO 的样本，取 dsoff 给出的文件偏移 `off`，在 `--binary` 的可执行 PT_LOAD 中查找满足 `p_offset ≤ off < p_offset + p_filesz` 的段，换算为 ELF 虚拟地址：

   `vaddr = p_vaddr + (off − p_offset)`

2. 必须唯一匹配。落在段外或段间空隙的偏移计入 `target.unmapped_in_target`，不得猜测。所有算术检查溢出。
3. 该公式与页大小无关，也不使用全局 `BaseAddress` 与 4K 掩码。AddressCounter 的键是 `--binary` 中的 ELF 虚拟地址。
4. 实测：新镜像 libavcodec 的可执行 PT_LOAD 为 `p_offset = p_vaddr = 0`，全部样本唯一落入该段（05 报告 B.3）。`p_offset ≠ p_vaddr`、多个可执行段、16K/64K 对齐等布局由离线 lit 覆盖（5.10）。
5. 不实现自建的 pid/fork/exec 映射表。perf 不支持 dsoff 时直接报错，不退回现有的全局基址逻辑。自建映射表（参照 BOLT `DataAggregator.cpp:1800–1885` 解析 COMM exec 与 FORK，:1963–2046 按 pid 建立映射）与原生 perf.data 解析一起放在第三批（第 7 节）。

#### 5.3.2 身份来源

1. 逐映射确定身份来源：
   - MMAP2 记录带 `<build-id>`：该映射判定为 `verified`（映射时由内核读取）。
   - MMAP2 记录不带 build-id，但 `--perf-buildid-list`（或 `--perfdata` 时工具调用的 buildid-list）中该路径有 build-id：判定为 `verified-post-hoc`（录制结束时从文件读取，弱于前者）。
   - 两者都没有：该映射缺少 build-id。buildid-list 中路径前为空白、没有 build-id 的行，按缺少处理。
2. 同一路径的两种来源同时存在且不一致时报错，不以优先级掩盖冲突。
3. 报告记录每个映射实际使用的来源，以及整份输入是否出现过带 build-id 的 MMAP2（即录制时是否用了 `--buildid-mmap`）。

#### 5.3.3 目标选择与判定

1. 候选：样本 DSO 路径匹配 `--binary-match-regex`，或文件名与 `--binary` 相同。特殊 DSO 不参与候选。
2. 目标 build-id 从 `--binary` 的 note 读取（`object::getBuildID`）。目标二进制本身没有 build-id 时报错，`--allow-missing-build-id` 可放行，报告标记 `unverified`。
3. 有 build-id 时：
   - 候选路径的映射全部与目标一致：通过。同一身份的多个进程、多次加载合并计数（不同加载基址已由 dsoff 处理）。
   - 同一路径出现不同 build-id 的映射：报错。样本行只带路径，无法把样本归到具体映射，不合并。
   - 改名但 build-id 相同的映像：用 `--binary-match-regex` 纳入候选后可以匹配。
   - 路径带 `(deleted)` 的映射：MMAP2 自带 build-id 时按它判定；只有 buildid-list 来源时判定为不一致（录制结束时读到的文件已不是被映射的那一份）。
4. 输入侧缺少 build-id：无 `--allow-missing-build-id` 时报错；有则继续，标记 `unverified`。此时只要在整份输入中（不只是同一 pid 内）出现文件名相同但路径不同的 DSO，就报歧义错误，要求用 `--binary-match-regex` 或 build-id 区分。
5. 身份未验证时，报告给出合理性指标：目标样本落在 DWARF 函数区间内的比例；在 AArch64 上再给出 4 字节对齐的比例（armv7l 上 Thumb 指令为 2 字节对齐，对齐比例没有区分度，不给出）。

#### 5.3.4 分离调试文件的身份链

1. Tizen 的包是"strip 后的运行文件 + debuginfo 包"的形态。`--binary` 提供采样映像的加载布局与身份，`--debug-binary`（已有选项，`L/llvm-profgen.cpp:70–74`、`L/ProfiledBinary.cpp:248–256`）提供匹配的 DWARF，以及 armv7l 上需要的映射符号（5.7.2）。
2. 样本映射的 build-id、`--binary` 的 note、`--debug-binary` 的 note 三者必须一致，否则报错。不要求 strip 前后的文件整体 SHA-256 相同。
3. DWO/DWP 沿用已有的 `--dwp` 等路径；缺失时在报告中列出，并体现在符号化率中。
4. strip-all 的 `--binary` 加 `--debug-binary` 生成的 profile，必须与未 strip 时逐字节一致（5.10 用例）。

#### 5.3.5 LBR 路径

身份校验在 LBR 路径中不启用，以满足 C1。后续如需让 LBR 路径也使用，另行设计。

### 5.4 计数生成：行级（DWARF）模式

#### 5.4.1 地址计数与权重

1. AddressCounter 对每个 ELF 虚拟地址 `a` 保存 `sample_count(a)` 与 `period_sum(a)`（uint64，检查溢出）。
2. 权重 `w(a)`：
   - `--ip-weight=period`：`w(a) = period_sum(a) / P_ref`，用 double 累加，写出时取整。P_ref 的取值见 5.1.1。
   - `--ip-weight=sample`：`w(a) = sample_count(a)`。
3. 归一化的原因：clang 会把超过 uint32 的分支权重截断为 UINT32_MAX（`SampleProfile.cpp:1720–1725`）。spike 的 cycles 数据有 68,745 个样本、period 为 500009，总量约 3.4e10，不归一化时单个热点行就会远超 4.29e9，两个热点后继会被压成 1:1。
4. 语义：`sample` 是命中次数，`period` 是事件量的估计（cycles 为周期数，cpu-clock 为纳秒），两者都不是执行次数。period 不补偿 PMU 复用、丢样与 skid。一次运行只统计一种事件，cycles 与 cpu-clock 不混算。`-c` 模式下两种权重只差一个常数倍；`-F` 模式下只有 period 加权是无偏的（05 报告实测频率模式的 period 从 1 到约 2e7）。作为对照：create_llvm_prof 的 IP 模式每个样本计 1，不按 period 加权（`sample_reader.cc:292–302`）。

#### 5.4.2 符号化与归类

1. 对每个唯一地址，经 ProfiledBinary 的符号化器（LLVMSymbolizer）得到内联帧链。
2. 地址不在任何 DWARF 函数区间内（汇编、PLT、链接器生成的桩代码）：计入 `target.outside_dwarf_func`，不写入 profile。
3. 在函数区间内但行号为 0：计入 `target.in_func_no_line`。
4. 其余计入 `target.usable`，参与计数。

#### 5.4.3 聚合键

聚合键为：顶层函数 + 完整内联调用点链 + 叶子位置（行偏移, base discriminator）。同一个内联函数出现在两个调用点时属于两个不同的键。普通 discriminator 与 FS discriminator 沿用现有的 `getBaseDiscriminator` 与 `UseFSDiscriminator` 处理。

#### 5.4.4 聚合方式（`--ip-aggregation`）

设 `d(a)` 为从 discriminator 解码出的 duplication factor。推导：一段代码展开为 d 份、每份 k 条指令、共执行 N 次时，每份执行 N/d 次。

| 方式 | 定义 | duplication |
|---|---|---|
| `sum` | `body(k) = Σ w(a)`，a 取键 k 的全部地址 | 不乘。sum 自然得到 N·Σc |
| `max` | `body(k) = max w(a)·d(a)` | 乘。max 得到 (N/d)·max c；复用现有 `updateBodySamplesforFunctionProfile` 的语义（`L/ProfileGenerator.cpp:393–412`） |
| `avg` | `body(k) = Σ w(a)·d(a) / n(k)` | 乘。avg 得到 N·c̄/d |

1. `avg` 的分母 `n(k)`：键 k 在函数各区间内的全部指令数，包括没有样本的指令，排除数据（`$d`）。指令边界由 5.7.2 的按需枚举得到；A64、A32 与 Thumb 都支持。
2. 指令边界无法确定时（ARM 二进制没有可用的映射符号、或 Thumb 解码失败），`avg` 对该函数明确失败并报错，不静默退化。
3. 取整：写出时四舍五入；被采到的键写出值至少为 1，避免把采到的位置写成 0。
4. 溢出：中间值用 uint64 或 double 并检查。写出前任一 body 或 total 超过 UINT32_MAX 时告警并写入报告（归一化后正常不应出现）。
5. 默认值不在设计阶段拍板，由 5.8、5.9 的评估决定。平局规则：各方式的差异落在置信区间内时选 `max`，与两个参考实现对齐。Google 对纯 IP 输入也是按位置取 MAX 并乘 duplication factor（`symbol_map.cc:622–624`、`:648–655`），LLVM 的 LBR 路径同样如此。

#### 5.4.5 函数 total

每个样本的 `w(a)` 对其内联链上每一层的 FunctionSamples（叶子及全部祖先）的 total 各计一次，不乘指令长度（LBR 路径按字节累计，`L/ProfileGenerator.cpp:715–720`），也不把已含 inlinee 的父 total 与 inlinee total 重复相加。复用 `getLeafProfileAndAddToTotal`（`L/ProfileGenerator.cpp:637–665`）。total 与聚合方式无关，只有 body 随聚合方式变化，这样比较聚合方式时只改变一个变量。

#### 5.4.6 入口计数（`--ip-head-samples`）

1. 消费端行为：
   - 不开 profi 时，入口块所在等价类的权重和函数入口计数都是 `HeadSamples + 1`（`llvm/include/llvm/Transforms/Utils/SampleProfileLoaderBaseImpl.h:624–627`、`:1060–1061`）。不写 head 时所有函数的入口计数都是 1，PSI 会把不含调用的热叶子函数判为冷（`ProfileSummaryInfo.h:128–162`）。
   - 开 profi 时，入口计数取 profi 推断出的入口块权重，推断结果为 0 时才回退到 `HeadSamples + 1`（`SampleProfileLoaderBaseImpl.h:1089–1095`）。
   - 非 CS profile 的内联决策本来就用"最小行偏移处的 body 计数"估计 head（`getHeadSamplesEstimate`，`llvm/include/llvm/ProfileData/SampleProf.h:1000–1021`）。
2. `none`：不写 head samples。Tizen clang 驱动默认开启 profi（第 1 节第 6 条，已实测），这是可用的配置。前提是推荐配置不得关闭 profi；报告给出这一提示。
3. `entry-estimate`：只对顶层函数 profile 写 head，值为该函数最小行偏移处的 body 计数，与消费端 `getHeadSamplesEstimate` 的口径一致。内联调用点下的 profile 不写。不得用函数 total 冒充入口计数。
4. 默认值暂定 `none`，由 5.9 中"profi 开/关 × head 策略"的分组确定。

#### 5.4.7 补零（`--ip-zero-fill`）

1. 背景：LBR 路径会给有样本函数的全部区间补 0（`L/ProfileGenerator.cpp:672–690`），编译器把 0 理解为"不执行"。对稀疏的 IP 采样，"没采到"不等于"没执行"，而 profi 会把 0 当作已知的冷块。
2. `none`：未采到的位置保持缺失（未知），不复用 LBR 的补零逻辑。
3. `sampled-functions`：对有样本的函数，把其 DWARF 区间内未采到的键写为 0。枚举方法与 `avg` 分母相同（5.7.2），失败条件也相同。
4. 无样本的函数在任何策略下都不写入。默认 `none`（暂定）。

#### 5.4.8 采样位置漂移（`--ip-skid`）

1. 背景：异步采样得到的 IP 往往是"下一条将要执行的指令"，cpu-clock 是中断返回地址，PMU 溢出也有漂移。计数会系统性地前移，还可能越过已跳转的分支落到目标块。
2. `none`：不调整。
3. `prev-inst`：把地址换成布局上的前一条指令的地址，前提是前一条指令仍在同一函数区间内且不在数据范围中；否则不调整，计入 `skid_unadjusted`。A64、A32 上前一条指令在 4 字节之前；Thumb 上指令长度为 2 或 4 字节，不能向后猜，前一条指令由 5.7.2 从函数起点向前顺序解码得到。
4. 已知局限：跳转之后，实际上一条执行的指令不是布局上的上一条。默认 `none`（暂定），与聚合方式一起在 5.8 评估。

#### 5.4.9 其他

1. 间接调用目标：IP 数据无法得到，不生成。
2. 落在汇编或 PLT 中的样本无法写入 profile，只在报告中按 `.symtab` 名称列出前 20 个（5.4.2 第 2 条）。

### 5.5 pseudo-probe 子方案（实验性，单独准入）

本子方案不属于第一阶段冻结范围，以独立的实验补丁推进，不阻塞 DWARF 路径。通过准入之前不进入 llvm 包；在此之前 IP 模式对带 probe 的二进制按 5.1.4 报错。

1. 动机：pseudo-probe 以块为单位标识位置，并带函数 CFG 校验和，有助于发现 profile 与代码失配。LLVM 的 stale matching 同时存在于行级与 probe 两条路径：对 probe profile 默认开启（`SampleProfile.cpp:2038–2047`）；对行级 profile 需显式开启，且锚点只有调用点（`SampleProfileMatcher.cpp:114–128`）。IP profile 没有调用目标，锚点有限，所以可复用范围靠测量，不预先承诺"大部分复用"。
2. 消费端的连带效应：probe profile 会自动开启 profi、迭代 BFI、ext-tsp 等（`SampleProfile.cpp:2015–2047`）；陈旧度过高时整份 profile 会被拒绝（`rejectHighStalenessProfile`，`SampleProfile.cpp:2100–2135`、`:2176–2178`）。
3. 映射问题：LLVM 中没有现成的"任意 IP → 块"组件。`AddressProbesMap::find()` 是精确匹配；BOLT 靠自己的 CFG 把 probe 归到块（`DataAggregator.cpp:2394–2410`），profgen 无法复用。
4. 两种候选映射，都要评估，正确性优先：
   - M1（最近 probe）：先由 DWARF/符号表确定 IP 所属的函数区间片段，再在该片段内取地址不大于 IP 的最大 probe 地址，把该地址上的全部 probe（含内联 probe）计入；IP 小于片段首个 probe 时单独统计其占比。
   - M2（精确块边界，先做 AArch64）：构建时加 `-fbasic-block-address-map`（clang 驱动只对 X86 与 AArch64 的 ELF 放行，`Clang.cpp:6179–6187`），用 `ELFObjectFileBase::readBBAddrMap`（`llvm/include/llvm/Object/ELFObjectFile.h:119–128`）得到机器块边界，把 IP 归到所在机器块，再把该块内的 probe 计入。它不能自动解决"一个机器块含多个逻辑 probe"的关联，需要另定规则。armv7l 不能使用 M2。
5. 必须处理的情形：一址多 probe、同一 probe 多份副本、被优化掉的 probe、call probe 与 block probe、冷热分区后的函数片段、内联边界。基本块本身是连续的，重排不分裂块；真实风险是冷块外迁导致函数地址范围不连续，以及部分块没有 probe。无法确定归属的样本单独报告，不向前猜测。
6. 计数：IP 计数约等于"执行次数 × 块代价"，与 LBR 下 probe 计数的"执行次数"不同。块计数按 `--ip-aggregation` 用块内指令数归一化（指令边界来自 5.7.2）；skid 处理与 5.4.8 相同；head 取 entry probe 的计数。
7. 架构：IR 层插入 probe 和 `.pseudo_probe` 节的发射是通用路径，但 MIR 层的 `PseudoProbeInserter` 在本树只挂在 X86 后端（`X86TargetMachine.cpp:616`）。先在 AArch64 上验证，用 `--show-pseudo-probe` 核对 `.pseudo_probe` 结构完整（函数记录、块 probe 都在）；armv7l（Thumb 为主）验证失败时，probe 只支持 aarch64。
8. 准入：
   - 正确性：每种情形都有已知预期归属的 golden fixture，全部通过；
   - 统计质量：5.8；
   - 性能：5.9（含"带 probe 但不用 profile"的开销组）。
   正确性不通过则不进入正式包，只作为实验补丁保留；正确性通过但性能不占优时，再讨论是否作为非默认功能保留。

### 5.6 质量报告与失败契约

#### 5.6.1 报告内容

`--quality-report` 输出 JSON，用 `llvm::json::OStream` 生成。字段至少包括：

| 字段 | 说明 |
|---|---|
| `schema_version` | 报告格式版本 |
| `tool` | 工具版本与完整参数 |
| `input` | 输入路径与 SHA-256；`--perfdata` 时还有 perf 路径、版本、完整命令与退出状态 |
| `semantics` | `weight`、`unit`（cycles / ns / samples）、`p_ref`、`aggregation`、`dup_policy`、`zero_fill`、`head_samples`、`skid`、`mode`（dwarf / probe）、`fs_discriminator` |
| `identity` | 是否出现带 build-id 的 MMAP2；目标路径与 build-id；`--debug-binary` 的 build-id；候选路径；逐映射的来源与判定（`verified` / `verified-post-hoc` / `unverified` / `mismatch`）；最终判定 |
| `mapping` | pid 数、匹配的映射数、verified 与 unverified 映射数 |
| `samples` | 逐层统计，每层同时给出样本数与权重：`input_total`、事件筛选后、pid 筛选后、`kernel`、`other_dso`（按 DSO 列前 20，含 `[vdso]`）、`unmapped`、`target`、`target.unmapped_in_target`、`target.outside_dwarf_func`（按 `.symtab` 列前 20）、`target.in_func_no_line`、`target.usable`、实际写出的位置数、`skid_unadjusted` |
| `isa` | armv7l 上按样本数与权重分别统计落在 Thumb、A32 与无法判定代码中的比例 |
| `lost` | 丢失记录数、丢失样本数、来源；无法获知时为 `unknown` |
| `throttle` | 节流记录数，或 `unknown` |
| `ratios` | 符号化率（按权重与按数量各一个，判定用哪一个写明） |
| `sanity` | 身份未验证时给出：落在 DWARF 函数区间内的比例；AArch64 上 4 字节对齐的比例 |
| `coverage` | 有样本的函数数、唯一地址数、权重最高的前 50 个函数及占比 |
| `consumer_hints` | 例如 `head_samples=none` 时提示"推荐配置不得关闭 profi" |
| `warnings` | 全部告警，带稳定的诊断代码 |
| `verdict` | `conversion`（`ok` / `failed`，失败阶段与原因）；`identity`（同上述判定）；`sampling_adequacy`（`ok` / `insufficient`）。不对运行时收益作任何判断 |

1. 未知值写 `unknown`，不写 0。整数用 uint64 表示，不经浮点，无精度损失。
2. 报告不含时间戳，数组顺序确定。同一输入运行两次，profile 与报告都必须逐字节相同。

#### 5.6.2 判定口径

1. 符号化率 = `usable / (usable + in_func_no_line)`，按权重计算。`outside_dwarf_func` 只报告，不参与判定：libavcodec 的热点有相当一部分在 NEON 汇编中，把它们计入分母会让主要评估对象因为与"符号缺失"无关的原因失败。
2. `--ip-min-symbolized-ratio` 的默认值用 libavcodec 的实测数据确定。

#### 5.6.3 失败契约

1. 以下情况返回非 0：身份不一致；目标样本数为 0 或低于 `--ip-min-target-samples`；符号化率低于门槛；输入格式错误；perf 调用失败；报告写入失败。
2. 失败时不生成、不覆盖 `--output`：profile 先写临时文件，成功后再改名。非 0 退出不得被解释为可使用新 profile。
3. 指定了 `--quality-report` 时，可处理的失败要写出报告，并注明失败阶段。IP 模式在加载二进制之前完成输入解析与身份前置检查；加载阶段的致命错误也要写出 `failure_stage=load` 的报告（具体做法在代码评审中确定）。崩溃或磁盘不可写时，不承诺一定有报告。

### 5.7 架构支持

#### 5.7.1 支持矩阵

| 目标 | 要求 | 验证 |
|---|---|---|
| aarch64 | ELF64 小端；PIE、共享库、多个可执行 PT_LOAD 且 `p_offset ≠ p_vaddr`；4K/16K/64K 对齐（离线 lit）；映射符号中的 `$d` 不计为指令；指令边界为定长 4 字节 | 格式核对：从 spike 保留的 perf.data 重新导出；评估数据用重新构建的库重新采集 |
| armv7l Thumb-2（LLVM 镜像默认） | ELF32；第一批完整支持：符号化计数、`avg`、`sampled-functions` 补零、`prev-inst` skid，指令边界由第二解码器按需得到（5.7.2） | RPi4 新镜像，cycles；评估用以 `%{optflags}` 构建的库（含 `-mthumb`，与镜像一致） |
| armv7l A32 | ELF32；`$a` 范围定长 4 字节；`$d` literal pool 不计为指令，也不作为 skid 回退目标 | lit：A32 构建（`-marm`）与 ARM/Thumb 混合构建 |
| vmlinux | 第一批只识别并统计内核样本，不生成 profile。原因：6.12 内核没有 `AUTOFDO_CLANG`，内核只在 `toolchain_is clang` 时才用 clang 构建（`linux-rpi.spec:166–167`），第一批没有可验证的消费端。生成移到第二批（6.1） | 合成输入中包含内核样本 |

#### 5.7.2 指令边界的按需枚举

1. 只对有样本的函数，在其 DWARF 区间内进行，只在 `avg`、`sampled-functions` 补零或 `prev-inst` skid 被启用时执行。
2. ISA 与数据范围的判定：
   - AArch64：`$x` 为代码、`$d` 为数据；没有映射符号时，函数区间整体按代码处理。
   - EM_ARM：按 `$a`（A32）、`$t`（Thumb）、`$d`（数据）映射符号切换。映射符号来自 `--binary` 或 `--debug-binary` 的 `.symtab`（板上运行文件已 strip，需由调试文件提供；Tizen debuginfo 是否保留映射符号在冻结前确认，见第 10 节步骤 1）。没有可用的映射符号时，以函数符号（STT_FUNC）`st_value` 的 bit0 判定函数入口的 ISA（bit0 为 1 是 Thumb）；函数内部无法确认是否有 literal pool 时，该函数的按需功能失败并计入报告，不静默退化。
3. 解码：
   - A64、A32：从范围起点按 4 字节步进。
   - Thumb：在 IP 模式下为 EM_ARM 二进制创建第二个带 `+thumb-mode` 的解码器（参照 `llvm-objdump.cpp:2724–2735`、`:2320–2337`），从 `$t` 范围起点或函数起点向前顺序解码，得到 2/4 字节的指令边界。解码失败的位置计入报告，该函数的按需功能失败。
   - 该解码器只在 IP 模式下创建，不改变原有加载流程（C1）。
4. 采样 IP 与符号地址：
   - 采样 IP 本身不带 bit0：内核的 `perf_instruction_pointer` 直接返回 `ARM_pc`，Thumb 状态在 CPSR 的 T 位。不得对样本地址做 Thumb 位处理。
   - 带 bit0 的是符号表中 Thumb STT_FUNC 的 `st_value`。LLVM 读取时已清除（`ELFObjectFile.h:615–618`），但直接读取原始 `st_value` 的核对脚本必须自行清除（05 报告 B.3：清除前 3/7、103/219 命中，清除后全部命中）。
   - DWARF 中 Thumb 函数低地址的表示方式由 lit 用例核对。
5. 验收：对 lit 中的 A32、Thumb、混合二进制，以及评估用的 libavcodec 热点函数，把枚举得到的指令边界与 `llvm-objdump -d`（带映射符号）的结果逐条比对。

### 5.8 质量评估方法（统计质量）

评估分三层：A. 转换正确性（golden fixture，见 5.10）；B. 统计质量（本节）；C. 优化收益（5.9）。三层不能互相代替。

1. 参考与对齐（主方法）：同一源码、同一组 flags，分别用 `-fprofile-use=<插桩 profdata>` 和 `-fprofile-sample-use=<IP profile>` 编译，加 `-mllvm -print-after=pgo-instr-use` 或 `-mllvm -print-after=sample-profile`（`PassRegistry.def:133`、`:161`），以及 `-mllvm -disable-sample-loader-inlining`（`SampleProfile.cpp:196–200`），导出刚完成标注的 IR。插桩计数由编译器自身的计数恢复流程给出，`.profdata` 本身不是逐块真值表，不直接读取。
2. 对齐规则（依据 05、06 报告的原型）：
   - 插桩参考构建的生成与使用两侧都加 `-mllvm -disable-preinline`。插桩 PGO 在打计数之前会先做一次预内联（`PassBuilderPipelines.cpp:1241–1242` 调用 `addPreInlinerPasses`），sample 侧没有这一步；不关闭时两侧的内联状态不同，分支无法对应。这个参考构建只用于本节的比较，5.9 中的插桩 PGO 对照组仍用正常 flags。
   - 插桩侧所在函数带 `function_entry_count`、但分支没有 `branch_weights` 的，按全部后继权重为 0 参与匹配（PGO 对计数全为 0 的分支不写权重）。
   - 匹配键为"函数 + 终结指令的完整 DILocation（含作用域、内联链与 discriminator）+ 后继序号"，重复键不配对。
   - 语义校验：键相同的两条终结指令，必须指令类型相同、后继数相同，且每个后继块中第一条带 DILocation 的指令位置相同；任一不符，整条终结指令判为形态不一致，不参与指标并单独计数。06 报告中出现过 PGO 侧 switch 与 sample 侧 br 键相同、但后继含义不同的情况，仅按键匹配会把不同路径配成同一条边。
   - 接受门槛：每个评估程序按插桩侧执行权重计算的有效匹配率（通过语义校验的已匹配边权重之和 / 全部边权重之和）不低于 95%（暂定，在 spike 与 libavcodec 上确认）。低于门槛的程序不使用本节的 IR 层指标，改用第 3 条的辅助参考，并在结论中注明。
   - 原型参考：06 报告在 armv7l spike 上，关闭预内联并计入零权重后，按边数为 97.78%（插桩侧）/ 95.65%（sample 侧），按插桩权重为 100%，另有 1 条形态不一致的终结指令（当时尚未加语义校验）。
3. 辅助参考：用 `-fprofile-instr-generate -fcoverage-mapping` 加 `llvm-cov export` 得到行级真实执行计数，评估行级热点召回；`.profdata` 的函数级计数作交叉核对。
4. 指标：
   - 主指标：归一化块计数的加权重叠度 Σmin(p̂, q̂)；按执行次数加权的分支概率误差；95% 与 99% 热块的召回率。
   - 辅助指标：函数级 Spearman 相关系数；插桩计数占比合计 95% 的热点函数在 IP profile 中的覆盖率；行级热点召回。
   - IP 的总量反映时间，插桩的总量是执行次数，秩相关不能消除这种差异，所以 Spearman 只作辅助。
5. 噪声：每种配置至少独立采集 5 次，用 bootstrap 求 95% 置信区间；做低、中、高三档样本预算。"差异小于波动"指置信区间重叠，判为平局，按 5.4.4 的平局规则处理。
6. 负对照（指标必须明显更差，用于证明指标有区分度）：另一份输入采集的 profile；函数内计数随机打乱；错误版本二进制的样本（用身份未验证模式故意生成）；行偏移整体平移。
7. 可选对照：在 AArch64 上运行指定版本的 `create_llvm_prof --use_lbr=false`，对齐 sample/period 语义后比较，不把它当作真值；如果 x86 主机支持 LBR，在主机上运行 spike，用同一份 perf.data 同时生成 LBR profile 与 IP profile 作为上界参考。
8. 输入与分阶段：训练输入与测试输入分开（不同视频）。先在 spike 上评估"聚合方式 × skid × 权重方式"，再在 libavcodec 上评估补零策略与 head 策略。armv7l 的 spike 评估构建必须使用 `%{optflags}`（含 `-mthumb`），与镜像中的真实包一致；另做一组 `-marm` 构建覆盖 A32。
9. 对象与板子：spike 测试程序；libavcodec（FFmpeg H.264 解码）。RPi5 与 RPi4（新镜像）都用 cycles。
10. 决定：默认值由测试输入上的性能（5.9）、统计稳定性与实现复杂度共同决定，不只取训练输入上相关性最高者。libavcodec 热点中 NEON 汇编的占比（`outside_dwarf_func`）以及 Thumb/A32 的样本占比（`isa`）写入结论。

### 5.9 编译端选项与性能评估（不改 clang）

1. 显式控制：所有组统一用 `-fno-sample-profile-use-profi -mllvm -sample-profile-use-profi=<true|false>` 关闭驱动的自动注入并显式指定 profi；stale matching 显式用 `-mllvm -salvage-stale-profile=<true|false>`，单独评估它时固定 `-mllvm -salvage-unused-profile=false`。用 `clang -###`、profile 属性与 IR 核对实际生效的配置。
2. 分组（聚合方式、skid、补零先由 5.8 筛出候选，只有入围组合进入本节）：

| 组 | 配置 |
|---|---|
| G0 | 基线，不用 profile |
| G1 | IP 行级，profi=true，head=none |
| G2 | IP 行级，profi=false，head=none（体现 5.4.6 所述的入口计数问题） |
| G3 | IP 行级，profi=false，head=entry-estimate |
| G4 | IP 行级，profi=true，head=entry-estimate |
| G5 | 插桩 PGO `-fprofile-use=<profdata>`（对照组，正常 flags，不关闭预内联） |
| G6 | 带 `-fpseudo-probe-for-profiling` 构建，不用 profile（衡量 probe 本身的开销；probe 子方案用） |
| G7 | IP probe，profi=true 与 profi=false 各一组（probe 子方案通过正确性准入后才做） |

3. 消费端检查（每组）：`-mllvm -sample-profile-check-record-coverage=<N>`、`-mllvm -sample-profile-check-sample-coverage=<N>`（`SampleProfileLoaderBaseUtil.cpp:26–34`）、`-mllvm -report-profile-staleness`；在 IR 中检查 `function_entry_count` 是否存在且合理，以及是否有等于 4294967295 的 branch_weights（饱和）。
4. `-fprofile-sample-accurate`：会把未采样的调用点和函数都按 0 处理（`SampleProfile.cpp:150–154`），并忽略 profile 符号列表（`:1987–1989`）。不作为稀疏 IP 的推荐默认，只在评估中观察。profile 符号列表会让列表中的符号被视为"计数准确"（`ProfileAccurateForSymsInList` 默认为 true，`:162–165`），所以第一批禁用 `--populate-profile-symbol-list`。
5. 性能测量（仅用于验证本增强）：
   - RPi5 与 RPi4 各自在 FFmpeg H.264 解码上测；固定编译、链接、LTO 参数、解码工作量与线程数。armv7l 的库按镜像的 `%{optflags}` 构建。
   - 每组至少 10 轮，各组交错执行，丢弃预热轮（注册表扫描）。RPi4 视方差加量：旧镜像 720p 基线的最大最小差为 2.04 s，均值 12.31 s，相对差约 16.6%（`03_rpi4_sampling.md` 第 4 节）。
   - 固定 cpufreq governor；记录 `scaling_cur_freq`、`/sys/class/thermal` 与节流、后台负载；记录镜像 BUILD_ID、内核 `uname -v`、实际加载的 libavcodec build-id、换出统计 pswpout（新镜像的 force_reclaim 修复会真正换出到 zram）。
   - 保存全部轮次；异常判据预先定义（例如换出明显增加、发生节流），同时报告剔除前与剔除后的结果；报告中位数与 95% 置信区间。
   - 每轮核对解码输出的校验和一致。训练用的视频与测量用的视频不同。另用 `perf stat` 的 cycles 与 instructions 作为噪声更低的辅助指标（两板都可用）。
   - "未证明改善"是允许的结论。
6. 过期复用测试：
   - 改动类型：纯行号移动；热点函数内的 CFG 改动；调用点插入与删除。
   - 每种改动比较四组：不用 profile；旧 profile 且关闭 salvage；旧 profile 且开启 salvage；重新采集的 profile。行级组显式开启 salvage；probe 组验证默认开启的行为。
   - 记录是否触发 checksum mismatch、是否实际发生匹配、是否被 `rejectHighStalenessProfile` 整体拒绝。
   - 旧 profile 原本就没有显著收益时，"收益保留比例"标为不适用。

### 5.10 测试

1. 回归：按 C1 的验证方式执行。
2. 三层验证：
   - 第一层，golden fixture：可人工推导地址、内联栈与计数的小程序。每个二进制 fixture 附源文件、生成命令、工具版本与预期值。测试不依赖本机 perf、板子或网络。
   - 第二层，独立核对：主核对用 GNU `addr2line -i -f`（GBS root 中的 binutils 2.43），行偏移的起始行从 `readelf --debug-dump=info` 的 `DW_AT_decl_line` 取得；`llvm-symbolizer` 作为第二核对方（它与 profgen 共用 DWARF 与 Symbolize 库，独立性不足）。重算行级计数并与工具输出逐行比对。地址扰动负对照分两类：落到无效地址；仍落到另一个有效函数或源码位置（用来发现"符号化率高但内容错误"）。核对脚本读取原始 `st_value` 时清除 Thumb 位（5.7.2 第 4 条）。
   - 第三层，消费验证：`llvm-profdata show` 能读取；clang 消费后在 IR 中检查函数名、内联位置的匹配情况与覆盖率诊断。
3. lit 基础设施：该测试目录整体要求 X86 后端（`test/tools/llvm-profgen/lit.local.cfg:6–7`），新用例另加 `REQUIRES: aarch64-registered-target` 或 `arm-registered-target`。Tizen x86_64 的 llvm 包含 X86、ARM、AArch64 后端，满足条件。预生成的测试二进制单独成一个补丁，便于评审。perf script 文本素材取自 05、06 报告中板上 perf 6.12.80 的实际输出（样本行、MMAP2 两种形式、`[vdso]`、`[kernel.kallsyms]`、LOST、buildid-list 的空 build-id 行）。
4. 新增正向用例：
   - aarch64 PIE；aarch64 共享库，非零加载基址，多个 PT_LOAD 且 `p_offset ≠ p_vaddr`；16K、64K 对齐的合成偏移；
   - 两个 pid 以不同基址加载同一个库；fork 出的子进程没有自己的 MMAP 事件；
   - Thumb 构建（`-mthumb`，与镜像默认一致）；A32 构建（`-marm`）且含 `$d` literal pool；ARM/Thumb 混合；Thumb 上的 `avg`、`sampled-functions` 补零与 `prev-inst` skid（含 16 位与 32 位指令相邻的情形）；指令边界与 `llvm-objdump -d` 逐条一致；只有 `.dynsym`、没有映射符号时按函数符号 bit0 判定 ISA；
   - `#pragma unroll 4` 循环，检查 sum、max、avg 三种方式加 duplication 后的值；同一函数内联到两个调用点；多层内联；使用 FS discriminator 的二进制；
   - strip-all 的 `--binary` 加 `--debug-binary`（映射符号来自调试文件）与未 strip 时输出逐字节一致；
   - `-c` 与 `-F` 两种 period 输入（输出等于 Σperiod / P_ref）；LOST 记录；MMAP2 带 build-id 与只有 buildid-list 两种身份来源；buildid-list 中的空 build-id 行；
   - 未加 `--kernel` 时出现内核样本；`[vdso]` 带偏移的样本计入 `other_dso`；汇编函数中的样本归入 `outside_dwarf_func`；
   - `entry-estimate` 的输出；带修饰符的事件名；
   - `max` 方式与 [ip, ip] 区间注入后的输出逐行一致；
   - 确定性：同一输入运行两次，profile 与报告逐字节相同；
   - 5.12 的合并用例。
5. 负对照（每条都检查报错文本或具体计数）：
   - 缺少 dsoff 字段；dsoff 偏移落在两个段之间；
   - 逐映射 build-id 不一致；同一路径出现不同 build-id；MMAP2 与 buildid-list 对同一路径给出不同 build-id；只有 buildid-list 来源时的 `(deleted)` 路径；
   - strip 后的 `--binary` 与 `--debug-binary` 的 build-id 不一致；无 build-id 时文件名相同而路径不同；
   - 多事件未指定 `--ip-event`；事件筛选后为空；目标样本为 0；符号化率低于门槛；
   - 不认识的行、截断的行、损坏的整数；超大 period 导致的溢出；
   - `--perfdata` 时 PATH 中放一个非 0 退出的假 perf，工具必须失败；不满足 5.2.4 准入时 `--perfdata` 报错；
   - 给 `--ip-samples` 一份 LBR 输入；不加 `--ip-samples` 时纯 IP 输入仍报原错误；
   - 5.1.3 中每个"报错"选项；未开启 `--ip-samples` 时使用 IP 专属选项；未指定 `--ip-aggregation`；
   - 没有映射符号且函数内含 literal pool 时启用 `avg`；Thumb 解码失败的函数；
   - 带 probe 的二进制在 IP 模式下未加 `--use-dwarf-correlation`；
   - 报告路径不可写：返回非 0，且 `--output` 未生成、已有文件未被覆盖。
6. 规模：用 libavcodec 记录工具的峰值内存与耗时，作为第二批 Chromium 规模（6.2）的外推基础。

### 5.11 第一批交付物

1. 补丁序列（基于 `f999bd40`），每个补丁可独立编译、测试通过，按以下顺序拆分：
   1. 测试输入（预生成二进制与 perf 文本素材）；
   2. IP 读取器与 dsoff 地址换算；
   3. 身份校验（逐映射来源、分离调试文件身份链）；
   4. IP 加载策略与 `ProfileGenerator` 中的 IP 填充（聚合、head、补零、skid）；
   5. 按需指令边界枚举（映射符号切换与 Thumb 第二解码器）；
   6. 质量报告与失败契约；
   7. 文档（`docs/CommandGuide/llvm-profgen.rst` 与报告 schema）。
   probe 子方案是独立的实验补丁，通过准入前不并入序列。`--perfdata` 在满足 5.2.4 准入后才并入。
2. 独立核对脚本与质量评估脚本（放本项目仓库 `tools/`；IR 匹配脚本在原型基础上按 5.8 第 2 条补上语义校验）。
3. 实现报告：回归结果、新增测试、独立核对结果、5.8 评估数据与默认值决定、5.9 性能数据、消费端匹配证据、probe 准入结论、`--perfdata` 准入结论、已知局限。
4. llvm 包的一次正常（非增量）GBS 构建记录。
5. 冻结前验证的证据（05、06 报告及第 10 节步骤 1 的剩余项）。

### 5.12 多份 profile 合并（第一批验证现有能力）

1. 不在 llvm-profgen 增加多输入选项。每份采样单独生成 profile，再用已有的 `llvm-profdata merge --sample --weighted-input=<权重>,<文件>` 合并（`llvm-profdata.cpp:108–112`、`:171–173`）。权重必须是正整数（`:1707–1718`），调用方规划权重时按需取整。
2. 这是 profile 层的加权融合，不保证与"原始样本合并后再生成"等价。`max` 不满足这种等价性：同一位置两条指令，输入 A 为 (10, 0)、输入 B 为 (0, 10)，分别取 MAX 后相加得 20，先合并再取 MAX 得 10。`sum` 在 P_ref 相同时等价。
3. 合并前由调用方依据报告核对：事件、权重方式、P_ref、聚合方式、head、补零、skid、构建身份、MD5 与格式一致。工具不会自动替调用方检查报告。
4. 同一次采集的分片若要求合并结果与整体生成一致，需要地址级的原始计数合并，不在第一批，需要时另行决策（6.5）。
5. 验收用例：上述 MAX 反例；`sum` 的等价情形；P_ref 不同的两份 profile 由核对脚本拒绝。

## 6. 第二批：规划（第一批完成后再出详细设计）

| 项目 | 目标 | 第一批需要预留或提供的 |
|---|---|---|
| 6.1 内核 profile（vmlinux 与模块） | vmlinux：用内核 mmap 记录中 `_text`/`_stext` 等重定位参考符号的运行地址（内核合成 mmap 的 pgoff 存放该地址，`tools/perf/util/synthetic-events.c:1154`）与 vmlinux 中同名符号的链接地址求 `slide = runtime_anchor − linked_anchor`，`elf_va = ip − slide`；校验锚点、可执行范围与内核身份，缺锚点或地址被隐藏时明确失败；`--pid` 不得因此丢弃 pid=-1 的全局内核映射。模块（ET_REL）：按"模块名 + build-id"识别，按节换算；核实 dsoff 对模块的语义；模块地址不归入 vmlinux。设计中必须说明消费路径（clang 构建的内核与 AutoFDO 支持） | 第一批的内核样本分类；地址键保留"对象身份 + 节"的扩展能力 |
| 6.2 大规模二进制（Chromium） | 峰值内存与耗时目标；分阶段释放缓存 | 第一批的 libavcodec 内存与耗时数据 |
| 6.3 冷函数符号列表 | 在现有 `--populate-profile-symbol-list` 上增加按函数大小覆盖率的选取策略。冷函数列表必须由明确的工作负载覆盖声明或独立的覆盖证据支持：身份校验与样本量是必要条件，不是充分条件。默认不根据"未采到"推断冷函数；尺寸覆盖率只用于压缩已确定的候选集合。与 `-fprofile-sample-accurate` 互斥（消费端开启后者时忽略符号列表），评估时二选一 | 第一批禁用；报告提供样本量指标 |
| 6.4 IP 模式阈值与裁剪 | 优先复用已有的 `--trim-cold-profile` 与 summary 阈值（`L/ProfileGenerator.cpp:530–553`）。只有已有机制无法表达的需求（例如样本可靠性过滤）才新增策略，而且可靠性不能只看 period 加权后的数值大小 | 第一批记录已有裁剪在 IP 模式下的效果 |
| 6.5 地址级原始计数合并（可选） | 只在同一采集的分片需要与整体生成结果一致时立项 | 5.12 的结论 |

（v0.2 中的"6.6 Thumb 解码"已并入第一批，见 5.7.2。）

## 7. 第三批：登记（条件具备后立项）

| 项目 | 立项条件 | 备注 |
|---|---|---|
| ARM SPE 输入 | 有带 SPE 的板子 | SPE 是统计采样，不是连续 trace；不能套用 LBR 区间假设 |
| BRBE | 有带 BRBE 的板子 | 先验证 perf 输出的分支记录能否直接走现有 LBR 解析，不预先承诺新 reader |
| Propeller 布局 profile | 有分支栈（LBR/BRBE）数据，且目标支持 `-fbasic-block-address-map` | 准确表述：clang 驱动只对 X86 与 AArch64 的 ELF 放行该选项（`Clang.cpp:6179–6187`），后端实现本身与指令集无关。涉及 CFG、布局算法与链接器消费，属于独立子系统 |
| 预取 / LLC miss 提示 | clang 出现可用的消费端 | 当前 clang 不使用这类信息，暂不实现 |
| 原生 perf.data 解析（由第二批降级） | 板上导出文本无法满足需求（例如 perf 不支持 dsoff，或导出吞吐不够），或主机长期没有可用 perf 而又需要在主机直接读 perf.data | 直接读 header、attr、MMAP2、COMM、FORK、EXIT、SAMPLE、build-id 表、丢样记录；同时实现自建的进程地址空间代际与映射（参照 BOLT `DataAggregator.cpp:1800–1885`、`:1963–2046`）。LLVM 内没有先例，BOLT 也调用 perf script（`DataAggregator.cpp:213–236`）；工作量大，上游接受度低。接口约束：读取层对上游只暴露"样本流（pid, event, period, dso, 文件偏移）+ 身份信息" |

## 8. 超出 create_llvm_prof 的增强（汇总）

以下是设计目标；每项效果以实现报告中的实测结果为准，未通过的能力标为实验或未交付。

| 增强 | 作用 |
|---|---|
| 结构化质量报告，分别判定转换有效性、身份与采样充分性 | 调用方可依据报告判断 profile 能否使用，不只靠退出码；不对收益作判断 |
| 显式事件与 period 加权，计数单位归一化 | create_llvm_prof 的 IP 模式每个样本计 1，不按 period 加权（`sample_reader.cc:292–302`）；归一化避免 clang 中分支权重饱和 |
| 由 perf 按线程解析映射（dsoff），换算与页大小无关 | 多进程、fork、exec 下地址换算正确（已在 RPi4 实测） |
| build-id 不匹配时失败报错；逐映射身份来源；分离调试文件身份链 | Google 也做 build-id 匹配（`sample_reader.cc:276–286`），但不匹配时返回空结果而不报错 |
| head 估计选项与消费端语义检查（入口计数、权重饱和、覆盖率） | 让 profile 在 clang 中的实际效果可查 |
| 默认策略在可对齐子集上参考插桩计数，并以独立输入上的性能与稳定性决定 | 用数据而不是假设决定 IP 计数规则 |
| ARM Thumb-2 与 A32 的完整支持（含按需指令边界） | create_llvm_prof 默认构建不含 32 位 ARM；Tizen LLVM 镜像的 armv7l 包默认是 Thumb |
| 编译端组合评估（profi、head、stale matching） | 无需改 clang，给出推荐配置 |
| pseudo-probe IP 模式（实验，准入后才交付） | 评估不同代码变化下的复用范围，不保证保留比例 |

## 9. 工具的输入与输出约定

本节只描述 llvm-profgen 自身的输入输出，不涉及调用方如何使用。

1. 输入：
   - 板上按 5.2.2 导出的 perf script 文本（第一批的主输入）；满足 5.2.4 准入时也可以是 perf.data；
   - 采集要求：推荐 `perf record --buildid-mmap`；也可默认录制并在板上导出 `perf buildid-list`；`-c` 或 `-F` 均可；
   - 采样映像对应的 ELF（程序头完整，可以是 strip 后的），以及内嵌的、或通过 `--debug-binary`/DWO/DWP 提供的匹配调试信息；armv7l 上启用按需功能时，调试文件需含映射符号。采样映像身份、ELF 加载布局与调试信息的对应关系必须可验证，不要求 strip 前后的文件整体字节相同；
   - 可选：`perf buildid-list` 输出；事件名。
2. 输出：profile 文件（extbinary 等已有格式）；可选的质量报告 JSON（5.6）。
3. 退出码：5.6.3 规定的失败条件返回非 0，此时不生成、不覆盖 profile；返回 0 时，详细质量信息以报告为准。

## 10. 实施步骤与评审节点

| 步骤 | 内容 | 节点 |
|---|---|---|
| 0 | 本版（v0.3）第二轮评审 | 评审结论 |
| 1 | 冻结前验证（一次性原型与素材，不构成正式实现）。已完成（RPi4，05、06 报告）：硬件 cycles、页大小、dsoff 格式与公式、双进程、period、`--buildid-mmap` 与 buildid-list、LOST 格式、Tizen clang 的 profi 默认注入、IR 匹配原型、armv7l 插桩 PGO、armv7l 默认 Thumb。剩余：RPi5 的 dsoff、`--buildid-mmap`、页大小，以及 aarch64 上按 5.8 第 2 条规则（含语义校验）重跑 IR 匹配；Tizen debuginfo 调试文件是否保留 `$a`/`$t`/`$d` 映射符号；是否获取主机 perf（用户决定，5.2.4） | 证据评审 |
| 2 | 第一阶段冻结：DWARF IP 核心（5.1–5.4、5.6、5.7、5.10–5.12 的规则与契约） | 冻结后才能开工 |
| 3 | （可选）在 discourse.llvm.org 发 RFC，征求选项命名与整体方案意见。是否发、何时发由用户决定 | 用户决定 |
| 4 | 实现补丁 1–7；回归与新增测试；独立核对 | 代码评审 |
| 5 | 5.8 质量评估（RPi5 与 RPi4） | 评估结论评审 |
| 6 | 5.9 性能与过期复用测试 | 结果评审 |
| 7 | 第二阶段冻结：默认参数（聚合方式、head、补零、skid、各门槛） | 评审 |
| 8 | probe 子方案：细化设计、实验补丁、准入评估（5.5） | 准入评审 |
| 9 | 正常 GBS 构建；整理补丁序列 | 交付评审；由用户决定 Gerrit 合入方式与时间 |
| 10 | 第二批详细设计 | 另行评审 |

1. 每个冻结节点列出已决事项、验收证据与剩余的实验项。"后续评估"不能代替必须成立的正确性规则。
2. 步骤 1 的剩余项可与步骤 0 的评审并行；其结果若与设计不符，在冻结前修订。
3. 默认值未确定期间的实验选项，不自动成为稳定的命令行接口。
4. probe 未通过准入，不阻塞已通过验收的 DWARF 路径。
5. Agent 的设计与开发在 llvm-profgen 增强完成（至少第一批交付）之后开始，不与本表的步骤并行。

## 11. 风险

| 风险 | 影响 | 对策 |
|---|---|---|
| 无分支信息的 AutoFDO 收益明显低于 LBR 情形，可能低于插桩 PGO | 增强的实际价值受限 | 5.8、5.9 如实给出收益，"未证明改善"是允许的结论 |
| profile 结构合法、符号化率高，但关联到错误位置 | 静默的错误优化 | golden fixture、两类地址扰动负对照、消费端匹配验证（5.10） |
| 多进程或 fork 导致地址换算错误 | 计数错位 | 由 perf 按线程解析（dsoff），不使用全局基址（5.3.1）；已实测 |
| perf script 文本格式变化，或板上 perf 不支持 dsoff | 输入不可用 | 严格解析、遇到未知格式即报错；以实测输出为素材；第三批的原生解析作为后备 |
| 主机没有可用 perf | `--perfdata` 无法交付 | 第一批以板上导出文本为主输入；`--perfdata` 有条件准入（5.2.4） |
| 计数单位导致分支权重饱和 | 分支概率被压平 | period 归一化（5.4.1）；IR 饱和检查（5.9） |
| 不写 head 且关闭 profi 时入口计数为 1 | 热叶子函数被判为冷 | 推荐配置保持 profi；`entry-estimate` 选项；G1–G4 分组验证 |
| 稀疏 IP 被解释为明确的冷代码 | 错误的冷代码优化 | 默认不补零、禁用符号列表、不推荐 `-fprofile-sample-accurate` |
| 热点在 NEON 汇编中 | 可用率与收益被压低 | `outside_dwarf_func` 单独统计并写入结论 |
| skid 使计数前移 | 块计数偏差 | `--ip-skid` 维度评估；局限写入文档 |
| 现有库无 build-id 或已 strip | 身份无法验证、无法符号化 | 评估使用重新构建的库；分离调试文件身份链 |
| armv7l 主要库为 Thumb，指令边界判定出错 | `avg`、补零、skid 结果错误 | 第二解码器与映射符号切换（5.7.2）；与 `llvm-objdump -d` 逐条比对；判定不了时明确失败 |
| 调试文件不含映射符号 | 函数内 literal pool 无法排除 | 冻结前确认 Tizen debuginfo；退回按函数符号 bit0 判定并对含数据的函数失败 |
| IR 层对齐只覆盖部分分支，或键相同而语义不同 | 评估指标失真 | 关闭预内联、零权重处理、语义校验与 95% 门槛（5.8 第 2 条）；低于门槛改用辅助参考 |
| probe 到地址的映射不正确 | probe 计数偏差 | 独立准入；正确性不过则不进正式包（5.5） |
| `-fpseudo-probe-for-profiling` 本身影响优化 | 收益被抵消 | G6 单独测量 |
| 多次采样结果不稳定 | 默认值决策不可靠 | 重复采样、bootstrap、样本预算敏感性分析，不只重复计时 |
| 测量噪声与热降频 | 性能结论不可靠 | 10 轮以上、固定 governor、记录频率与温度、置信区间（5.9） |
| 与 BOLT/PGO 线同时修改 llvm 包 | 补丁冲突 | 独立分支开发；合入前由用户协调顺序 |

## 12. 待第二轮评审确认的问题

1. 第一批只用 perf 的 dsoff 做地址换算、不实现自建映射表（perf 不支持时直接报错），是否可接受。
2. 带 probe 的二进制：沿用现有约定（自动 probe，`--use-dwarf-correlation` 强制 DWARF），准入前在 IP 模式下报错——这一处理是否合适。
3. `--ip-samples` 与 `--perf-sample-type=auto|ip` 的命名取舍（建议在 RFC 中征求上游意见）。
4. 鉴于 Tizen clang 驱动默认开启 profi，`--ip-head-samples` 默认暂定 `none` 是否合适。
5. Thumb 第二解码器与映射符号切换进入第一批（5.7.2）：方案、失败条件与验收方式是否充分；没有映射符号时按函数符号 bit0 判定的退路是否可靠。
6. 以板上导出文本为第一批主输入、`--perfdata` 有条件准入（5.2.4），是否合适。
7. 5.8 的 IR 对齐规则（关闭预内联、零权重、语义校验、95% 门槛）与主指标，是否足以支撑默认值决策。
8. 两阶段冻结的划分，以及步骤 1 剩余项与评审并行的安排是否合理。
9. 失败契约（失败时不生成、不覆盖 profile；加载阶段失败也写报告）是否合理、可实现。

---

## 附录 A：v0.1 评审意见处理

来源缩写：K = Kimi Code，C = Codex，CC = Claude Code。v0.3 中因板上实测而改变的处理，在表中以"（v0.3 更新）"注明，详见附录 B。

### A.1 严重

| 问题 | 来源 | 处理 | 位置 |
|---|---|---|---|
| 地址换算：全局基址、无 pid/fork/exec、4K 掩码，多进程或 fork 时静默出错 | C 5.2-1、5.3-1；CC S1；K 5.3 | 采纳 CC 方案 A（perf dsoff + PT_LOAD 公式，与页大小无关），公式与 C 一致；C 的地址空间代际与 CC 的方案 B 作为第三批后备；K 的"修正共享代码中的页大小"不采纳（改为新路径不使用该逻辑，LBR 路径不动，满足 C1）。（v0.3 更新：已在 RPi4 实测 100% 一致） | 5.2.2、5.3.1、第 7 节 |
| 全量反汇编：Thumb 必然解错、strip-all 下 addressIsCode 全假、FS 检测在反汇编内 | K 第 4 节；C 4-1；CC 4-3 | 采纳：IP 专用加载策略第一批即实施，跳过全量反汇编，单独保留 FS 检测（并补充查 `--debug-binary`）；K 提出的"按 .debug_line 行数计 avg 分母"不采纳（行表行数不等于指令数） | 4.3、5.4.4 |
| Thumb bit0 的对象说错 | K 5.7；C 5.7-1；CC 5.7-1 | 采纳：样本 IP 不带 bit0，符号 st_value 由 LLVM 清除。（v0.3 更新：CC 的"Tizen 默认 A32"经实测不成立，LLVM 镜像 armv7l 默认 Thumb；CC 提出的第二解码器由第二批移回第一批） | 1.6、5.7 |
| period 加权导致分支权重饱和 | CC S2 | 采纳 CC 的 P_ref 归一化 | 5.1.1、5.4.1 |
| 不写 head 时非 profi 路径入口计数为 1 | CC S3；K 5.4（兜底机制） | 部分采纳：clang 驱动默认注入 profi（C 的说法成立，v0.3 已在 Tizen clang 实测），影响限于关闭 profi 的配置；采纳 `--ip-head-samples`，默认暂定 `none`，由 G1–G4 决定 | 1.6、5.4.6、5.9 |
| IP 权重语义与 duplication 未定义 | C 5.4-1；CC 5.4-2 | 采纳 CC 的推导（sum 不乘，max、avg 乘）与 C 的语义说明 | 5.4.1、5.4.4 |
| 最近前置 probe 不是可靠映射 | C 5.5-1；K 5.5；CC 5.5-1 | 采纳 C：probe 改为独立实验子方案与准入；采纳 CC 的 M1 细化与 C 的 BB address map 作为 M2；采纳 K 的"函数归属前置"与"块不分裂"表述修正 | 5.5 |
| 内核 KASLR 不能套用用户态模型 | C 5.7-2；CC 5.7-3 | 采纳 CC：内核 profile 生成移到第二批（第一批无消费端）；C 的 slide 公式写入 6.1 | 5.7、6.1 |
| `.profdata` 不是逐块真值表 | C 5.8-1；K 5.8；CC 5.8-1 | 采纳 CC 的 IR 层比较为主方法；K 的 llvm-cov 作为辅助参考；C 的"正确性与统计质量分层"作为评估结构。（v0.3 更新：按原型结果补充对齐规则与门槛） | 5.8、5.10 |
| 编译端分组存在等价组与混杂因素 | C 5.9-1；K 5.9；CC 5.9-1 | 采纳 C 的显式 profi/salvage 控制与 CC 的分组及消费端检查 | 5.9 |

### A.2 重要

| 问题 | 来源 | 处理 | 位置 |
|---|---|---|---|
| C1 措辞与验证范围；不存在独立 ETM reader；共享代码改动 | C 3-1；CC 3-1；K 第 3 节 | 采纳 C 与 CC 的合并表述（含 stderr、`--help` 除外、IP 门控、四种格式比对）；K 的"允许行为等价的共享修改"不再需要 | 第 3 节 |
| C3、C5 的验证方式 | C 3-2；CC 3-2 | 采纳 | 第 3 节 |
| 选项冲突矩阵；`--use-dwarf-correlation` 不是 LBR 专属；probe 开关方向 | C 5.1-1；CC 5.1-1、5.1-2 | 采纳 CC 的矩阵（补充 `--kernel`、显示类选项与 CS 推断类选项），沿用现有 probe 约定；C 的"显式 `--ip-use-probes`"不采纳（与现有约定方向相反），但采纳其"probe 未验证前不得静默生效" | 5.1.3、5.1.4 |
| 丢样改用 `--show-lost-events`；未知不得写 0 | K 5.2；C 5.2-2；CC 5.2-5 | 采纳；"无记录记 0"按输入来源区分。（v0.3 更新：LOST 格式已实测） | 5.2.2、5.2.3 |
| MMAP2 build-id 需 `--buildid-mmap`，与 buildid-list 互斥 | K 5.3；CC 5.2-2 | 采纳 CC 的判定等级。（v0.3 更新：实测 buildid-list 在 `--buildid-mmap` 下也有输出，"互斥"不成立，改为逐映射确定来源） | 5.2.1、5.3.2 |
| build-id 一致性、改名、跨 pid 歧义、`(deleted)` | C 5.3-2；K 5.3；CC 5.3-2 | 采纳三方合并规则；`(deleted)` 按来源区分（在 CC 基础上细化） | 5.3.3 |
| 分离调试文件身份链 | C 5.3-3；CC 5.3-1 | 采纳 | 5.3.4、第 9 节 |
| 文本语法、严格解析、perf 退出码 | C 5.2-2；CC 5.2-3、5.2-6；K 5.2 | 采纳。（v0.3 更新：语法按实测输出写定） | 5.2.2–5.2.4 |
| 不新建 IPProfileGenerator | CC 4-2 | 采纳 | 4.3 |
| 聚合键、avg 分母、total 口径 | C 5.4-2；CC 5.4-4 | 采纳 | 5.4.3–5.4.5 |
| 补零策略 | C 5.4-3；CC 5.4-1 | 采纳 CC 的选项与 C 的默认原则 | 5.4.7 |
| skid | CC 5.4-3 | 采纳 | 5.4.8 |
| stale matching 的行级与 probe 不对称；`-salvage-stale-profile` 对 probe 冗余 | K 5.5、5.9；C 5.5-2 | 采纳 | 5.5、5.9 |
| 报告 schema、分母、PLT/汇编桶、语义字段、确定性 | C 5.6-1；CC 5.6-1~3；K 5.6 | 采纳 CC 的分类（含 K 的 PLT 桶）与 C 的失败契约 | 5.6 |
| ARM 映射符号、`$d`、AArch64 数据映射 | C 5.7-1；CC 5.7-1 | 采纳 | 5.7 |
| 评估指标、噪声、负对照、训练与测试分离、可选对照 | C 5.8-2；K 5.8；CC 5.8-2~4 | 采纳 | 5.8 |
| 性能实验控制与轮数 | C 5.9-2；CC 5.9-2 | 采纳 | 5.9 |
| `-fprofile-sample-accurate` 与符号列表 | K 5.9、6.4；C 5.9-1；CC 5.9-3 | 采纳 | 5.9、6.3 |
| lit 基础设施与 REQUIRES；独立核对改用 GNU addr2line | CC 5.10-1、5.10-3；C 5.10-1；K 5.10 | 采纳 | 5.10 |
| 原生 perf.data 降级 | CC 6-1 | 采纳，移到第三批并给出立项条件 | 第 7 节 |
| 冷函数列表的证据要求 | C 6.4-1 | 采纳 | 6.3 |
| 合并不等价、权重为正整数、第一批即验证 | C 6.6-1；K 第 6 节；CC 6-2 | 采纳 | 5.12 |
| 冻结与评估的循环；两阶段冻结 | C 10-1 | 采纳 | 状态、第 10 节 |
| probe 准入条件；风险补充 | C 11-1；CC 11-1 | 采纳 | 5.5、第 11 节 |
| 第 9 节不应要求"未 strip" | C 9-1；CC 9-1 | 采纳 | 第 9 节 |
| 2.1 目标的边界与消费语义目标 | C 2-1；CC 2-1 | 采纳 | 2.1 |

### A.3 一般

| 问题 | 来源 | 处理 |
|---|---|---|
| 行号 1186 应为 1190（报错在 :1216） | K 第 1 节 | 采纳 |
| 背景区分"当前镜像"与"硬件能力" | C 1-1 | 采纳 |
| 补充平台事实（A32、strip、页大小） | CC 1-1 | 采纳 strip 与页大小。（v0.3 更新：A32 一条经实测改为"默认 Thumb"；RPi4 页大小已实测为 4K，RPi5 待测） |
| C2 预先说明不需要库改动 | CC 3-3 | 采纳 |
| `--min-symbolized-ratio` 改名与暂定；`--ip-aggregation` 过渡期写入 `--help` | K 5.1；CC 5.1-3 | 采纳 |
| 事件名含修饰符 | CC 5.1-3 | 采纳 |
| `-F` 清空默认字段、`event` 必需 | K 5.2 | 采纳 |
| `--perfdata` 单次调用 | K 5.2 | 采纳。（v0.3 更新：`--perfdata` 改为有条件准入） |
| 内核样本按 DSO 名分类 | CC 5.2-4 | 采纳 |
| 身份未验证时的合理性指标 | CC 5.3-3 | 采纳。（v0.3 更新：对齐比例只在 AArch64 给出） |
| Google 也取 MAX，作为平局规则依据 | K 5.4；CC 12.4 | 采纳 |
| 汇编函数样本单独计数 | CC 5.4-5 | 采纳 |
| probe 在 ARM/AArch64 的发射完整性需实测 | K 5.5；CC 5.5-2 | 采纳 |
| `-fbasic-block-address-map` 的准确表述 | K 第 7 节 | 采纳 |
| 第 8 节删除"惰性符号化"、修正 build-id 对比、措辞收窄 | C 8-1；CC 8-1；K 第 8 节 | 采纳 |
| 补丁拆分顺序；测试输入单独成补丁 | CC 5.11-1；K 5.10 | 采纳 |
| 已采数据需重新导出或重新采集 | CC 5.7-2 | 采纳 |
| 6.5 复用已有裁剪 | C 6.5-1 | 采纳 |
| 增加 RFC 步骤、armv7l 插桩 PGO 验证步骤 | CC 10-1 | 采纳；RFC 为可选步骤，由用户决定。（v0.3 更新：armv7l 插桩 PGO 已在 05 报告中完成） |
| 第 4 节与 5.10 中 Chromium 交叉引用错误 | C 6.3 | 已修正（现为 6.2） |
| 无 LBR 报错时加提示文本 | K 12.2 | 不采纳：会改变 stderr，违反 C1（K 本身也建议放弃） |
| `--ip-samples` 改为 `--perf-sample-type` | CC 12.1 | 暂不采纳，列入第 12 节由 RFC 决定（K、C 均主张保留现名） |

## 附录 B：v0.2 → v0.3 修订（依据 05、06 冻结前核实报告）

| 实测事实 | 来源 | 设计修订 | 位置 |
|---|---|---|---|
| LLVM 镜像 armv7l 的 Optflags 含 `-mthumb`；FFmpeg、GLib、GStreamer、libstdc++ 导出函数全部 Thumb，libc/ld-linux 以 ARM 为主 | 06 第 1 节 | 删除"默认 A32"前提；Thumb-2 与 A32 都是第一批完整支持对象；Thumb 第二解码器与映射符号切换从第二批移入第一批；按需功能在 Thumb 上可用；评估构建使用 `%{optflags}`；报告增加 `isa` 统计 | 1.6、2.1、4.1、4.3、5.4.4、5.4.7、5.4.8、5.7、5.8、5.11、第 6 节、第 11 节 |
| `--buildid-mmap` 下 buildid-list 仍有输出；没有 build-id 的映像在 MMAP2 中打印设备号与 inode；buildid-list 有空 build-id 行 | 05 B.6 | 删除"两种互斥模式、buildid-list 为空"的表述；身份来源逐映射确定；报告记录是否出现带 build-id 的 MMAP2 | 5.2.1、5.3.2、5.3.3、5.6.1 |
| `[vdso]` 样本带偏移，`[kernel.kallsyms]` 不带 | 05 B.2 | 特殊 DSO 一律按名称分类，与是否带偏移无关 | 5.2.2、5.2.3 |
| 实际导出格式、LOST 行格式与计数（942 条、61,667 个样本，与 report 一致） | 05 B.2、06 第 4 节 | 按实测写定语法；lit 素材取自实测输出 | 5.2.2、5.2.3、5.10 |
| dsoff 与 PT_LOAD 公式单进程、双进程 100% 一致；`-c`/`-F` 的 period 行为 | 05 B.3–B.5 | 地址换算与 period 规则确认，补充实测说明；`p_offset ≠ p_vaddr` 仍由离线用例覆盖 | 5.2.1、5.3.1、5.4.1 |
| 原始 `st_value` 区间核对在清除 Thumb 位后才全部命中 | 05 B.3 | 核对脚本必须清除 Thumb 位；对齐合理性指标只在 AArch64 给出 | 5.3.3、5.7.2、5.10 |
| Tizen 仓库没有 x86_64 perf 包 | 06 第 3 节 | 板上导出文本作为第一批主输入；`--perfdata` 有条件准入；获取主机 perf 由用户决定 | 4.2、5.2.4、5.11、第 9 节、第 11 节 |
| IR 匹配：插桩预内联导致内联状态不同；零计数分支无权重；键相同但后继含义不同 | 05 C.2、06 第 2 节 | 参考构建关闭预内联；零权重参与匹配；增加语义校验；设定按权重 95% 的暂定门槛 | 5.8 |
| Tizen clang 默认注入 profi；RPi4 页大小 4K；RPi4 新镜像硬件 cycles；armv7l 插桩 PGO 闭环 | 05 A、B.1、C.1、D | 由"待确认"改为已核实事实 | 1.1、1.5、1.6、5.4.6、第 10 节 |
