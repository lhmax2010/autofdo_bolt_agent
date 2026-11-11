# llvm-profgen 增强设计（第一批详细设计 + 第二、三批规划）

| 项目 | 内容 |
|---|---|
| 版本 | v1.8（第一阶段冻结版 + 实现期增补 + 第二阶段评估判据，折入登记前准备中的裁决 1–4，经 v1.6、v1.7 评审修订） |
| 状态 | **第一阶段已冻结（v0.7）**，实现期间对冻结范围的增补与澄清已全部登记在附录 G.1，并已随补丁 1–9 实现与验收；附录 G.1 的优先级只限于其中明确列出的修订点，正文中受影响的条款末尾都注明了对应的附录条目；未列出的正文限制继续有效。第二阶段冻结版将把 G.1 并入正文，附录只留历史。**第二阶段（默认参数与评估判据）尚未冻结**：本版按第一轮实测修订了 5.8 的质量判据与 5.9 的采集合格判据（附录 G.3、G.4），并按 v0.8 至 v1.4 各轮评审意见修订（附录 H–N）。v1.5 按约定未再评审，直接进入附录 N.5 的登记前准备；准备中以裁决 1–4 修订 5.8 第 5 条（系统头函数与宏生成函数的结论状态、③ 的行集合、单候选检查中的无键实例），并澄清 ④ 的计算时点。v1.6 折入这些裁决（附录 O），经 Codex、Claude Code 限定范围评审（严重问题 0 项），按附录 P 修订为 v1.7，并按 v1.7 规则重算了静态产物（`docs/profgen/eval/prep/05_identity_gate_and_coverage.md` 第 13 节）。v1.7 连同重算结果经 Codex、Claude Code 限定范围评审（严重问题 0 项），按附录 Q 修订为本版；本版只加强门禁、前提检查与措辞，不改变 C、U 与三个门槛的数值，按项目约定不再评审设计文档，以实现与夹具验收为准。预注册修订 3 在附录 Q.5 的核对完成后单独登记，登记前不得对任何正式 sample profile 计算质量指标。probe 子方案仍单独准入 |
| LLVM 基线 | Tizen llvm 包源码 `f999bd406c0a70fe8107aa992164fe6945c5d46a`（LLVM 22.1.8）；上游对照 tag `llvmorg-22.1.8` |
| 参考实现 | Google AutoFDO `f95d1a170dfe24ec5ce4117aa4b0f6d836841703`（create_llvm_prof） |
| 前置材料 | `docs/spike/01_afdo_pgo_feasibility.md`、`docs/profgen/00_incremental_build.md`、`docs/profgen/01_gap_analysis.md`、`docs/probe/03_rpi4_sampling.md`、`docs/probe/04_rpi5_probe.md`、`docs/probe/05_rpi4_pmu_image_and_prefreeze.md`、`docs/probe/06_rpi4_prefreeze_followup.md`、`docs/probe/07_v04_prefreeze_checks.md`、`docs/probe/08_buildid_split_check.md`、`docs/probe/09_rpi5_prefreeze_checks.md` |
| 适用范围 | 本文只覆盖 llvm-profgen 工具本身的增强，以及验证该增强所需的测试与评估。不包含任何 Agent 的设计与开发；Agent 在 llvm-profgen 增强完成后另行设计 |
| 评审记录 | v0.1 经 Kimi Code、Codex、Claude Code 三方评审，处理见附录 A。v0.2 依据冻结前板上核实（05、06 报告）修订为 v0.3，见附录 B。v0.3 经三方第二轮评审（结论依次为"修改后可以冻结""需要重大修改""修改后可以冻结（第一阶段）"），处理见附录 C。v0.4 未外部评审；依据 07 报告与 LLVM 包的 build-id 方案小幅修订为 v0.5，见附录 D。v0.5 经 Codex、Claude Code 第三轮评审（Kimi Code 未参加），两家结论均为"修改后可以冻结"（Claude Code 注明第一阶段）；连同 08、09 报告的结果修订为 v0.6，见附录 E。v0.6 经 Codex、Claude Code 限定范围复核，两家结论均为"修改后可以冻结第一阶段"，没有严重问题；按复核意见修订为 v0.7 并冻结第一阶段，不再另起一轮，处理见附录 F。v0.7 冻结后完成补丁 1–9 的实现与第一轮板上采集，实现期裁决、评估判据修订与实测事实整理为 v0.8，见附录 G。v0.8 经 Claude Code、Codex、Kimi Code 限定范围评审（结论均为"修改后可以进入第二阶段评估"；严重问题合计 1 项），处理见附录 H，修订为 v0.9。v0.9 经同三家限定范围评审（Claude Code、Codex 结论为"修改后可以"，Kimi Code 为"可以登记"；严重问题 0 项），处理见附录 I，修订为 v1.0。v1.0 经同三家限定范围确认评审（三家结论均为"修改后可以登记"；严重问题 0 项），处理见附录 J，修订为 v1.1。v1.1 经同三家限定范围评审（Codex、Claude Code 结论为"修改后可以进入登记准备"，Kimi Code 为"可以进入登记准备"；严重问题 1 项），处理见附录 K，修订为 v1.2。v1.2 经同三家限定范围评审（Codex、Claude Code 结论为"修改后可以进入登记准备"，Kimi Code 为"可以进入登记准备"；严重问题 2 项），处理见附录 L，修订为 v1.3。v1.3 经同三家限定范围评审（Codex、Claude Code 结论为"修改后可以进入登记准备"，Kimi Code 为"可以进入登记准备"；严重问题 1 项），处理见附录 M，修订为 v1.4。v1.4 经同三家限定范围评审（Codex、Claude Code 结论为"修改后可以进入登记准备"，Kimi Code 为"可以进入登记准备"；严重问题 0 项），处理见附录 N，修订为 v1.5；按约定不再评审，直接进入登记前准备。准备中的裁决 1–4 与 ④ 的澄清折入 v1.6，见附录 O。v1.6 经 Codex、Claude Code 限定范围评审（两家结论均为"修改后可以登记"；严重问题 0 项；Kimi Code 本轮未参加），处理见附录 P，修订为 v1.7。v1.7 连同按其规则重算的静态结果经 Claude Code、Codex 限定范围评审（Claude Code 结论为"可以登记"，Codex 为"修改后可以登记"；严重问题 0 项；Kimi Code 未参加），处理见附录 Q，修订为 v1.8；按约定不再评审 |
| 引用约定 | `L/` = `llvm/tools/llvm-profgen/`。LLVM 行号以 `llvmorg-22.1.8` 为准；评审已核实 `L/` 下 13 个文件以及本文引用的 `Clang.cpp`、`PassBuilderPipelines.cpp`、`SampleProfileMatcher.cpp`、`ELFObjectFile.h/.cpp`、`BuildID.h`、`llvm-objdump.cpp`、`llvm-profdata.cpp`，以及第三轮评审核实的 `lld/ELF/Options.td`、`lld/ELF/Driver.cpp`、`clang/lib/Driver/ToolChains/Gnu.cpp`、`ProfileSummaryInfo.cpp`、`SampleProfWriter.cpp`、`PGOInstrumentation.cpp`、`BlockFrequencyInfo.cpp` 与 Tizen 树逐字节一致（Tizen 的 `Linux.cpp` 与上游只差一处 libstdc++ 头文件路径，与 build-id 无关）。perf 行号以 Linux v6.12 `tools/perf` 为准，内核生产端（`kernel/events/`）同样以 v6.12 为准（板上 perf 为 6.12.80，个别文件行号不同时两者都注明），板上行为以 05–09 报告的实测为准。Google 行号以 `f95d1a17` 为准 |

---

## 1. 背景

1. 当前已验证的采样能力只有普通指令地址采样（下称 IP 采样）：
   - RPi5（aarch64，Cortex-A76）：硬件 cycles 已验证（PMU `armv8_cortex_a76`）；branch stack 采样失败；SPE、ETM 不可用。
   - RPi4（armv7l，Cortex-A72）：加入 ARM_PMUV3 的新镜像（`tizen-unified-toolchain_20261028.105834`）已验证硬件 cycles：PMU 驱动 `armv8-pmu` 绑定 `armv8_cortex_a72`，`perf evlist -v` 为 type=0、config=0，样本非空（05 报告 A 节）。旧镜像只有软件 cpu-clock，请求 cycles 时 perf 会静默回退且退出码为 0，所以每次采集都要用 `perf evlist -v` 确认事件类型。
2. LLVM 22.1.8 的 llvm-profgen 对纯 IP 输入直接报错 `Invalid perf script input!`（`L/PerfReader.cpp:1190–1218` 的 `checkPerfScriptType()`，报错在 :1216），没有降级路径。
3. Google create_llvm_prof 的 `--use_lbr=false` 路径支持 IP 采样，但它是 LLVM 之外的独立工具，依赖 perf_data_converter 等外部组件，且默认构建不含 32 位 ARM。
4. 差异分析（`01_gap_analysis.md`）确认：create_llvm_prof 真正领先的功能共 11 项；行级/内联计数、discriminator、入口计数、间接调用目标、输出格式、裁剪等 llvm-profgen 已具备。
5. 插桩 PGO 已在 RPi5（aarch64）与 RPi4（armv7l）上各完成一次小程序闭环，输出校验一致（spike 报告与 05 报告 D 节；RPi4 一次使用旧快照工具链 Unified 20261022 / Base 20261020，不是新镜像同期的工具链）。可作为保底方案，也可作为评估 IP profile 质量的参考。
6. 已核实、且直接影响设计的平台与工具链事实（结论范围以证据为限）：
   - **LLVM 镜像的 armv7l 包默认生成 Thumb-2 代码。** 项目 reference build.conf 中 armv7l 的 Optflags 含 `-mthumb`（06 报告 1.3 节，build.conf:363；reference 是可变配置，不等于镜像中每个包的实际构建记录）。实测新镜像中 FFmpeg（libavcodec、libavutil、libavformat、libswscale）、GLib、GObject、GStreamer 各库与 libstdc++ 的已定义动态导出函数全部是 Thumb；libc 与 ld-linux 以 ARM 为主。统计口径只覆盖 `.dynsym` 导出函数，内部函数与汇编的模式未逐一核实。本次未引用 `%{optflags}`、直接调用 clang 的 spike，其自有 C 函数生成 A32，不能据此泛化到所有未引用 `%{optflags}` 的包。结论：镜像是 ARM 与 Thumb 混合的，主要多媒体库是 Thumb。
   - 板上现有库已 strip、没有 `.symtab` 与 DWARF，`readelf -A` 也没有 `.ARM.attributes` 输出（06 报告 1.1 节）。libavcodec、GStreamer 等库没有 build-id，但 libc、ld-linux、内核与 vdso 有 build-id（05 报告 B.6）。评估一律重新构建带调试信息的库。
   - 按 LLVM 镜像配置原样构建的 FFmpeg（07 报告第 1 节）：debuginfo 调试文件保留 `.symtab`、映射符号（`$a` 27、`$t` 5882、`$d` 6489）与 `.ARM.attributes`，其代码节为 NOBITS；strip 后的运行文件没有 `.symtab` 与 `.ARM.attributes`。运行文件与调试文件都没有 build-id：clang 构建时未打开 `ENABLE_LINKER_BUILD_ID`，链接时不传 `--build-id`（GCC 配置了 `--enable-linker-build-id`，所以 GCC 链接的 libc 等有 build-id）。打包时 debugedit 对 DWARF5 内容报"unhandled"警告。第三轮评审（Claude Code）对 08 的构建实测：拆分后的调试文件与 GBS BUILD 目录中未拆分的产物相比，行表 637,259 行逐行一致，2,549 个抽样地址的 `llvm-symbolizer --inlines` 结果一致，`DW_AT_comp_dir` 未被改写。范围只限 libavcodec 的一次构建，且尚未作为证据存入仓库（第 10 节步骤 1 补存）。
   - 带 build-id 的构建（08 报告，当前工具链加 `-Wl,--build-id=sha1`）：拆分后运行文件与调试文件的 build-id 都是可读的 SHT_NOTE，20 字节完全相同，`.build-id` 链接正确；调试文件代码节仍为 NOBITS。打包时 `find-debuginfo` 带 `--build-id-seed` 调用（08 报告 2.3 节），会重算 build-id：评审实测 BUILD 目录中链接产物的 build-id 与 RPM 中两份文件的不同。因此采样已安装的 RPM 时，看到的身份来自打包后的文件：应保留该安装产物及其匹配的 debuginfo，不得未经核对就用打包前的 BUILD 产物替代。工具只按 build-id 判定身份，不按文件所在目录判定（5.3.3 第 9 条）。该"ID 不同"的结果是评审实测，尚未存入仓库（第 10 节步骤 1）。
   - build-id 方案：LLVM 包将打开 `-DENABLE_LINKER_BUILD_ID=ON`（LLVM owner 已计划），此后 clang 每次为 Linux 目标链接都追加不带参数的 `--build-id`（`clang/lib/Driver/ToolChains/Linux.cpp:326–327`），不依赖各包的链接参数；之后显式给出的链接选项仍可能覆盖它，是否生成以产物为准。LLVM 22.1.8 的 lld 把不带参数的 `--build-id` 解释为 `--build-id=sha1`（`lld/ELF/Options.td:60`），GNU ld 也生成 20 字节；只有显式 `--build-id=fast` 等写法才得到其他长度（`lld/ELF/Driver.cpp:972–978`）。工具不根据链接器推断长度，始终按 ELF 中实际取得的完整字节串比较。新 LLVM 包的实际默认行为在发布后复核（第 10 节步骤 9）。
   - 镜像的 Optflags 只有 `-g2 -gdwarf-4` 一类调试选项（reference build.conf:360–363），没有 `-fdebug-info-for-profiling` 与 `-funique-internal-linkage-names`。AutoFDO 所需的构建要求见第 9 节。
   - RPi4 与 RPi5 的页大小都是 4096（05 报告 B.1；09 报告 1.1 节，RPi5 镜像 `tizen-unified-toolchain_20261028.105834`，内核 6.12.80-arm64-rpi4-v8）。本设计的地址换算与页大小无关（5.3.1）。RPi5 上 dsoff 与可执行 PT_LOAD 公式的核对结果与 RPi4 相同（单进程 5,865 条、双进程 14,331 条，均 100% 一致），`--buildid-mmap` 下 libc 的 MMAP2 build-id 与 ELF 一致，libavcodec 没有 build-id（09 报告第 3、4 节）。
   - clang 22 驱动（上游行为，提交 `d4331344ac45`、`2fc4a4a9d3a8`，Tizen 未修改）在编译（cc1）作业中，只要有 `-fprofile-sample-use` 就默认追加 `-mllvm -sample-profile-use-profi`；加 `-fno-sample-profile-use-profi` 后消失（`clang/lib/Driver/ToolChains/Clang.cpp:6277–6282`；Tizen clang 对 armv7l 与 aarch64 已实测，05 报告 C.1）。链接步骤不追加（`CommonArgs.cpp:1259` 只传 `sample-profile=`），而 (Thin)LTO 的 post-link 会再次运行 sample loader（`PassBuilderPipelines.cpp:1104–1105`、`:1149–1152`、`:1984–1988`），此时 profi 默认关闭。在 pass 内部，profi 只对 CS、preinlined、probe profile 自动开启（`llvm/lib/Transforms/IPO/SampleProfile.cpp:2015–2021`）。
   - 06 报告列出的 Unified/Base 快照及 reference 仓库中没有找到 x86_64 的 `linux-kernel-perf` 包（06 报告第 3 节）；其他仓库未核实。主机上目前没有可用的 perf，跨主机导出对照尚未验证。

## 2. 目标与非目标

### 2.1 目标

1. 把 llvm-profgen 增强为在无分支栈硬件上也能生成可用 AutoFDO profile 的工具。运行环境是 x86_64 主机，处理 aarch64 与 armv7l 的数据；armv7l 上的 Thumb-2 与 A32 两种代码都是第一批的支持对象，按需功能（`avg`、补零、skid 调整）的可用条件见 5.7.2。
2. 按第 5–7 节分批吸收 create_llvm_prof 的有效优势，并加入本项目需要、但两个工具都没有的能力（第 8 节）。差异分析只是候选来源，不构成额外的交付承诺。
3. 工具输出"机器可判定"：除 profile 外，输出结构化质量报告，分别表达转换是否有效、身份是否可信、采样是否满足门槛。工具不宣称采样已经"充分"，也不判断运行时收益；收益由独立评估确认。
4. 生成的 IP profile 在 clang 中的消费语义正确：函数入口计数合理、分支权重不饱和、profile 记录覆盖率可查。给出推荐的 clang 端配置（编译与链接两步，5.9）。
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
| C1 | 不使用任何新选项时，对既有命令行（固定输入、固定外部 perf 版本）：profile 内容、stderr 与退出码逐字节不变；`--help`、`--version` 的输出除外。22.1.8 的 reader 只识别 LBR 与 LBR+调用栈两类 perf 输入（`L/PerfReader.cpp:1190–1218`），本文不宣称存在独立的 ETM reader。对 ProfiledBinary、PerfReader、ErrorHandling 等共享代码的改动一律由 IP 模式门控。LBR 路径的既有问题（例如 4K 页的 FIXME，`L/ProfiledBinary.cpp:340`）不在本设计中修正，需要时另行提交 | lit 全部通过；每个已有测试输入在 text 与 extbinary 格式下比对新旧工具的 profile 与 stderr，非 CS、非 probe 输入另加 binary 格式（CS/probe profile 不支持 binary 写出，`SampleProfWriter.cpp:966–968`；gcc 格式写出在 22.1.8 不被支持，`:976–977`，只核对新旧工具报错行为一致，不作为输出比对项）；比较的是新旧工具实际的成功或失败行为；`--perfdata` 路径人工比对一次；不加 `--ip-samples` 时纯 IP 输入仍报原错误文本；主机 CPU 支持 LBR 时另采 x86 LBR 数据扩充比对语料 |
| C2 | 改动范围限于 `llvm/tools/llvm-profgen/`、其测试目录与命令文档。build-id 读取用现有 `object::getBuildID`（`llvm/include/llvm/Object/BuildID.h:33–37`），JSON 用 `llvm/Support/JSON.h`，SHA-256、宽整数与溢出检查用 LLVM Support；地址换算公式参考 BOLT（`bolt/lib/Core/BinaryContext.cpp:2226–2256`），映射符号切换参考 llvm-objdump（`llvm-objdump.cpp:2320–2337`），均在工具内局部实现。如仍需修改 LLVM 库，必须在实现前单独申报理由与影响面 | 补丁 diffstat 检查 |
| C3 | 不影响其他 RPM 包的编译与运行：增强只在使用 llvm-profgen 时生效 | 检查工具目录以外的源码、公共 ABI 与链接依赖没有变化；只在可复现构建条件成立时要求其他产物逐字节一致，否则解释差异并抽查相关工具的行为 |
| C4 | 不拷贝 autofdo 源码。参考其算法自行实现；若沿用某处实现细节，在提交说明中列出位置与理由 | 代码评审 |
| C5 | 每项功能必须有可执行的验收用例。解析、地址换算、跨架构 ELF 处理这类格式或公式层面的逻辑，可用离线合成输入（lit）验证；涉及真实采样语义、perf 行为与性能的结论，必须有相应的板上运行证据。无法用任何方式验证的功能不进入 llvm 包 | 验收表分别标注"离线正确性""板上闭环""性能"，三者不能互相代替 |
| C6 | 开发验证用 GBS 增量构建；正式交付前必须做一次非增量的正常 GBS 构建 | 构建记录 |

## 4. 现有架构与扩展点

### 4.1 现状（经评审核实）

1. `ProfiledBinary` 在读取 perf 数据之前构造（`L/llvm-profgen.cpp:160–162`）。`load()` 无条件执行全量反汇编（`L/ProfiledBinary.cpp:272`）。FS discriminator 的检测放在反汇编流程末尾，只查 `--binary` 自身、且只遍历数据节（`Section.isData()`）中的符号（`L/ProfiledBinary.cpp:812–829`）；只含调试信息的文件中 `.rodata` 为 NOBITS，`isSectionData` 会把它排除（`ELFObjectFile.h:956–961`）。
2. 地址换算：每个二进制只有一个全局 `BaseAddress`（`L/ProfiledBinary.h:422–430`）；`updateBinaryAddress` 按事件顺序覆盖它，不区分 pid（`L/PerfReader.cpp:534–585`）；没有 FORK/EXIT 处理；`--perfdata` 的 PID 预扫描只收集出现过 mmap 的 pid，fork 出的子进程会被排除（`L/PerfReader.cpp:472–500`）；段偏移按 4K 掩码（`L/ProfiledBinary.cpp:340–353`）。
3. 符号化已经是按地址惰性进行并缓存的（`L/ProfiledBinary.h:581–597`），这不是新能力。
4. 反汇编只创建一个由 `Obj->makeTriple()` 与 `getFeatures()` 决定的解码器（`L/ProfiledBinary.cpp:684–740`），没有 Thumb 模式；`$a`、`$t`、`$d` 映射符号被当作普通分段点。ELF 没有 `.ARM.attributes` 时，triple 退化为不带版本的 `arm`，feature 为空（`ELFObjectFile.cpp:160–166`、`:723–733`、`:774`）；评审用 Tizen GBS root 的 llvm-mc 实测，`thumb` triple 下 32 位 Thumb-2 指令解码失败，`thumbv7a` 下正常。llvm-profgen 只读 `.symtab`、从不读 `.dynsym`，没有 `.symtab` 的 `--binary` 下反汇编找不到符号，`addressIsCode()` 全部返回 false。由于 LLVM 镜像的主要 armv7l 库是 Thumb（第 1 节第 6 条），现有加载流程无法用于这些库。
5. probe 查找：`AddressProbesMap::find()` 要求地址精确相等（`llvm/include/llvm/MC/MCPseudoProbe.h:225–247`）。LBR 路径能命中，是因为它在执行区间内按反汇编结果逐指令步进（`L/ProfileGenerator.cpp:1213–1244`）。
6. 错误处理：加载阶段的错误经 `exitWithError`（`L/ErrorHandling.h`）直接退出进程。

### 4.2 新增的数据流

```
perf script 文本（板上按 5.2.2 导出；第一批的主输入）────────┐
perf.data ──（满足 5.2.4 准入时：IP 模式自带的单次调用）─────┤
                                                              ↓
  IPPerfReader（新）：严格解析样本行（pid/tid、period、event、ip、DSO 字段）、
                      MMAP2 行（逐映射的 build-id 或设备号/inode）、LOST 行
                                                              ↓
  身份层（新）：逐映射身份证据、buildid-list、--binary 与 --debug-binary 身份链、保守汇总
                                                              ↓
  地址换算（新）：文件偏移 → 包含它的可执行 PT_LOAD → ELF 虚拟地址（与页大小无关）
                                                              ↓
  AddressCounter（新）：ELF 虚拟地址 → {sample_count, period_sum}（整数）
                                                              ↓
  ProfileGenerator::populateBodySamplesFromAddresses()（新，与 populateBodySamplesForAllFunctions() 并列）
     复用：内联 profile 树的构造；整数分子按键聚合，最后一次除以 P_ref 并取整（5.4）
     按需：对有样本的函数枚举指令边界（A64/A32 定长；Thumb 按编码长度规则，5.7.2）
     复用：postProcessProfiles()（裁剪、summary、密度）
                                                              ↓
  SampleProfileWriter（复用）  +  质量报告 JSON（新，llvm::json::OStream）
```

### 4.3 设计原则

1. IP 路径与 LBR 路径在数据结构上分开。不把 IP 样本伪装成长度为 0 的 LBR 区间，避免与 RangeCounter 的"执行次数"语义混淆，也避免影响已有代码。
2. 不新建 IPProfileGenerator 类。在 `ProfileGenerator` 内新增 `populateBodySamplesFromAddresses()`，复用内联 profile 树的构造（`getLeafProfileAndAddTotalSamples` 等，`L/ProfileGenerator.cpp:637–670`）与后处理（:530–537）。现有的 `updateBodySamplesforFunctionProfile`（:393–412）与 total 累计接口接收 `uint64_t`，且前者会立即乘 duplication factor；IP 路径不直接调用这两个整数接口，避免提前取整或重复乘 duplication。IP 路径在独立的整数结构中完成聚合，最后一次性写入 FunctionSamples。LBR 路径的整数接口与行为保持不变。
3. IP 专用加载策略，第一批即实施（只在 `--ip-samples` 时生效，原有模式继续使用原加载流程，满足 C1）：
   - 必需：目标架构、ELF 段与节、身份、调试文件、DWARF 函数区间（`findFuncRange`，`L/ProfiledBinary.h:521–532`）、FS discriminator 标记、符号化器。
   - 不做：全量反汇编；不使用 `addressIsCode`、`CodeAddressVec`；不做 prolog/epilog 推断。
   - 按需、只对有样本的函数做：指令边界枚举，供 `avg` 分母、补零枚举、skid 调整使用（5.7.2）。
   - FS discriminator 检测：IP 模式下按符号名 `__llvm_fs_discriminator__` 在 `--binary` 与 `--debug-binary` 的 `.symtab` 中查找，不按节类型过滤（调试文件中的数据节为 NOBITS）。LBR 路径的 `checkUseFSDiscriminator` 不变。
   - 理由：IP 行级计数只依赖 DWARF；现有反汇编在 Thumb 和 `$d` 上必然出错；没有 `.symtab` 的 `--binary` 下 `addressIsCode` 全部为假；跳过全量反汇编还会减少大二进制的耗时（是否降低峰值内存以测量为准）。
4. 依赖全量反汇编结果的诊断选项（`--show-disassembly-only` 等）在 IP 模式下报错，见 5.1.3。
5. `main` 的顺序在 IP 模式下调整为：先解析输入与身份前置检查，再构造 `ProfiledBinary`（`L/llvm-profgen.cpp:160–187`）。

## 5. 第一批：详细设计

第一批包含：IP 输入（板上导出的 perf script 文本；满足准入时另含 `--perfdata`）、基于 perf `dsoff` 的地址换算、身份校验（含分离调试文件）、行级计数生成、质量报告与失败契约、aarch64 与 armv7l（Thumb-2 与 A32）支持、质量与性能评估方法、用现有 llvm-profdata 合并 profile 的验证。

不在第一阶段冻结范围内：pseudo-probe 子方案（5.5，实验性，单独准入）；默认参数与评估判据（第二阶段冻结）。

### 5.1 命令行接口

#### 5.1.1 新增选项

| 选项 | 含义 | 默认值 |
|---|---|---|
| `--ip-samples` | 启用 IP 输入模式。输入为 `--perfscript`（按 5.2.2 导出的文本），或在满足 5.2.4 准入时为 `--perfdata` | 关闭 |
| `--ip-event=<name>` | 只统计指定事件，按 perf 打印的完整事件名匹配，包括修饰符（如 `cycles:u`、`cpu-clock:ppp`）。输入中出现多种事件且未指定时报错 | 未设置 |
| `--ip-weight=<period\|sample>` | 每个地址的权重来源：`period` 用 period 之和、按 P_ref 归一化；`sample` 用样本数。见 5.4.1 | `period` |
| `--ip-period-unit=<N>` | 显式指定 P_ref（正整数）。未设置时自动取值，规则见 5.4.1。合并多份 profile 时必须显式统一 | 自动 |
| `--ip-aggregation=<sum\|max\|avg>` | 同一聚合键下多条指令的合并方式，见 5.4.4 | 评估前不设默认值，必须显式指定；这一过渡行为写入 `--help` 与文档；第二阶段冻结时确定默认值，提交上游前必须确定 |
| `--ip-head-samples=<none\|entry-estimate>` | 函数入口计数（head samples）的写法，见 5.4.6 | `none`（暂定，第二阶段冻结时定稿） |
| `--ip-zero-fill=<none\|sampled-functions>` | 未采到位置的补零策略，见 5.4.7 | `none`（暂定） |
| `--ip-skid=<none\|prev-inst>` | 采样位置漂移的处理，见 5.4.8 | `none`（暂定） |
| `--binary-match-regex=<re>` | 给出时，只用该正则匹配样本的原始 DSO 路径来选择候选，取代默认的文件名匹配；未给出时按 `--binary` 的文件名匹配（5.3.3 第 1 条） | 未设置 |
| `--perf-buildid-list=<file>` | 板上 `perf buildid-list` 的输出，供 `--perfscript` 输入做身份校验（5.3.2） | 未设置 |
| `--allow-missing-build-id` | 任一必要身份证据缺失时继续，最终身份等级为 `unverified`。只放行"缺失"，不放行任何已知的不一致 | 关闭 |
| `--quality-report=<file>` | 输出质量报告 JSON，见 5.6 | 未设置 |
| `--ip-min-usable-ratio=<0..1>` | 目标可用率（定义见 5.6.2）低于此值时失败 | 第二阶段冻结前不设默认值：未给出时不做该项判定，报告中对应结果写 `not_evaluated`。默认值用真实库（含其汇编占比）的实测数据在第二阶段确定 |
| `--ip-min-target-samples=<n>` | 目标二进制内样本数（数量口径）低于此值时失败 | 同上（第二阶段由评估确定）。目标样本数为 0 时无论是否设置都失败（5.6.3） |
| `--ip-max-lost-ratio=<0..1>` | 可见丢样比例（`exported_lost_ratio`，定义见 5.2.3 第 7 条）高于此值时，`sampling_adequacy` 判为 `insufficient` 并失败 | 同上（第二阶段由评估确定） |

命名规则：只对 IP 有意义的选项统一用 `--ip-` 前缀；将来对 LBR 也可能有用的选项（`--quality-report`、`--allow-missing-build-id`、`--binary-match-regex`、`--perf-buildid-list`）不加前缀，但第一批只在 IP 模式下有效。第一批保留 `--ip-samples`；是否改为 `--perf-sample-type=<...>` 交上游 RFC 决定，届时默认值仍须保持现有的识别与报错语义，不得暗含对 IP 输入的自动降级。

#### 5.1.2 启用规则

1. `--ip-samples` 只能显式开启，不做自动识别。理由：当前工具对无 LBR 的输入报错，改为自动降级会改变已有行为（违反 C1），也可能把"忘了加 `-b`"之类的采集错误静默降级成弱 profile。
2. 不加 `--ip-samples` 时，纯 IP 输入仍报原错误文本，不追加提示（追加提示会改变 stderr，违反 C1）。
3. 上表中的任一新选项在未开启 `--ip-samples` 时使用，一律报错。
4. 输入范围：IP 模式只接受 5.2.2 规定的 IP 文本语法，文本中出现分支栈（brstack）或调用栈扩展行时报错。原始 perf.data 本身可以含分支栈；IP 模式只消费按 5.2.2 投影出的 IP 字段，报告记录 `projection=ip-only`，不使用其中的分支信息。

#### 5.1.3 已有选项在 IP 模式下的行为

| IP 模式下 | 选项 |
|---|---|
| 报错 | `--unsymbolized-profile`、`--llvm-sample-profile`、`--skip-symbolization`、`--data-access-perftrace`、`--ignore-stack-samples`、`--csprof-*`、`--csspgo-*`、`--use-context-cost-for-preinliner`、`--max-search-depth`、`--gen-cs-nested-profile`、`--compress-recursion`、`--mark-all-context-preinlined`、`--use-offset`、`--use-first-loadable-segment-as-base`、`--update-total-samples`、`--fill-zero-for-all-funcs`（由 `--ip-zero-fill` 替代）、`--populate-profile-symbol-list`（推迟到第二批 6.3）、`--kernel`（第一批不生成内核 profile）、`--show-disassembly-only`、`--disassemble-functions`、`--show-source-locations`、`--show-canonical-fname`、`--show-pseudo-probe`、显式给出的 `--infer-missing-frames`（按 `getNumOccurrences()` 判断，因为它默认就是 true）；`--output` 为 `-`（标准输出）时也报错（无法回滚，见 5.6.3） |
| 保留原义 | `--binary`、`--debug-binary`、`--dwp`、`--output`/`-o`、`--format`、`--use-md5`、`--pid`（按样本的 pid 过滤；fork 出的子进程 pid 不同，不会被包含；pid 为 -1 的样本永不匹配，5.2.3 第 8 条）、`--show-mmap-events`（打印 IP 模式解析到的 MMAP2 记录）、`--show-detailed-warning`、`--trim-cold-profile`、`--profile-density-*`、`--show-density`、`--load-function-from-symbol`、`--use-dwarf-correlation` |

表中每个"报错"项都要有一条 lit 负对照，用 FileCheck 检查报错文本。

#### 5.1.4 带 pseudo-probe 的二进制

1. 沿用现有约定：二进制同时含 `.pseudo_probe` 与 `.pseudo_probe_desc` 时走 probe 路径（`L/ProfiledBinary.cpp:429–450`），`--use-dwarf-correlation` 强制走 DWARF（`L/ProfiledBinary.cpp:58–62`）。
2. 在 probe 子方案（5.5）通过准入之前，IP 模式拒绝带 probe 的二进制，包括显式给出 `--use-dwarf-correlation` 的情况。报错文本为"该构建的 IP 关联模式尚未准入，请使用不含 `-fpseudo-probe-for-profiling`、且带匹配 DWARF 的采样构建"。理由：在 probe 构建上用 DWARF 关联时 discriminator 的解读未核实，不能作为第一批的支持形态；现有的 `checkPseudoProbe()` 遇到强制 DWARF 会直接返回（`L/ProfiledBinary.cpp:429–449`），只说明可以选路径，不说明计数语义成立。
3. IP 模式对 `.pseudo_probe` 与 `.pseudo_probe_desc` 的检测独立执行，不受 `--use-dwarf-correlation` 的路径选择影响；在 `--binary` 与 `--debug-binary` 中都检测，任一文件含其中任一节即拒绝（不要求两节同时存在，比 LBR 路径的检测更严，有意为之）。理由：现有检测只遍历 `--binary` 的节（`L/ProfiledBinary.cpp:429–450`），而这两节是非分配节，经 Tizen 调试拆分后位于哪个文件未核实（列入第 10 节步骤 1 的非 ★ 项）。LBR 路径的行为不变（C1）。
4. probe 关联、或 probe 构建上的 DWARF 关联，各自通过准入后才放开对应的形态；probe 关联放开后按现有约定自动走 probe 路径。
5. 第一批 DWARF 路径的评估构建不加 `-fpseudo-probe-for-profiling`（第 9 节）。

### 5.2 采集要求与输入格式

#### 5.2.1 采集要求

1. 录制方式：
   - 推荐 `perf record --buildid-mmap ...`：带 build-id 的映像，其 MMAP2 记录直接带上 build-id（05 报告 B.6、D 节，09 报告第 4 节，实测与 ELF note 一致）；没有 build-id 的映像仍打印设备号、inode 与 generation。录制期间新建的映射，build-id 由内核在映射时读取；录制开始前已经存在的映射（`-a`、`-p`），perf 在用户态合成 MMAP2，build-id 由 perf 在录制开始时按路径读取文件得到（`tools/perf/util/synthetic-events.c:366–397`）。两者都按逐映射证据处理；文本中能否区分二者未核实，报告不作区分。已知局限：映射建立后、录制开始前原地改写同一文件时，合成记录中的 build-id 可能与实际映射的内容不符。
   - 也可用默认 `perf record`：MMAP2 不带 build-id，身份可借助板上导出的 `perf buildid-list`。
   - `perf buildid-list` 的结果可能来自 perf.data 的 build-id 表，也可能是它处理 MMAP2、build-id 等事件后恢复的（`tools/perf/builtin-buildid-list.c:101–108`、`:122–135`；`util/machine.c:1709–1738`）。它是路径/DSO 级的身份，不说明采集时机。不能用它是否为空来判断录制方式；身份等级按 5.3.2 判定。
2. 事件：RPi5 与 RPi4（新镜像）都用 `cycles`；只有旧镜像才用 `cpu-clock`。采集时保存 `perf evlist -v` 的输出作为证据（不是工具输入）。
3. `-c <N>`（固定周期）与 `-F <freq>`（频率模式）都支持。实测：`-c` 下样本没有 PERIOD 位，`period` 字段全部等于固定周期；`-F` 下有 PERIOD 位，period 逐样本变化（05 报告 B.5）。perf script 的 `period` 字段在样本没有 PERIOD 位时回退为 `attr.sample_period`（v6.12 `tools/perf/util/evsel.c:2673`，6.12.80 树为 :2684）。已知局限：频率模式下 `attr.sample_period` 存的是频率值，若遇到不带 PERIOD 位的频率模式数据，period 列会显示频率而非周期；工具无法从文本识别此情形，当全部样本 period 相同时在报告中给出提示，请调用方确认是 `-c` 模式。
4. 板上导出：第一批的主输入是在板上用 5.2.2 的命令导出的文本（板上 perf 与录制所用 perf 是同一个版本）。使用 `perf buildid-list` 时也在板上导出。

#### 5.2.2 导出命令与实测格式

```
LC_ALL=C perf script -i <perf.data> --show-mmap-events --show-lost-events -F pid,tid,event,period,ip,dsoff
```

1. 一旦显式给出 `-F`（不带 `+`/`-` 前缀），perf 会清空默认字段（`tools/perf/builtin-script.c:3160–3166`），事件名不再自动出现，所以 `event` 是必须字段。字段列表不得精简。
2. `dsoff` 隐含 `dso`（`builtin-script.c:651–653`）。偏移等于 `ip − 映射起点 + pgoff`（计算在 `tools/perf/util/map.h:108–125`，打印在 `util/map.c:472–486`），由 perf 按线程维护的映射解析得到。05 报告中，单进程 6,496 条、双进程 13,289 条 libavcodec 样本与按 MMAP2 独立计算的偏移 100% 一致。
3. 板上 perf 6.12.80 的实际格式（05、06 报告原文）；字段的打印顺序由 perf 源码决定，与 `-F` 的排列无关（`builtin-script.c:832–837`、`:2270–2280`、`:2324–2340`）：
   - 样本行：`  <pid>/<tid>  <period> <event>:  <ip> (<DSO 字段>)`。pid/tid 为带符号的十进制整数（`%7d/%-7d`，`builtin-script.c:833`），以 `/` 连接；系统级录制中实测有 `-1/-1` 的内核样本（09 报告"对设计的影响"第 1 条，形如 `  -1/-1  1000003  cycles:  ffff80008008ed38 ([kernel.kallsyms])`）。ip 为不带 `0x` 的十六进制。文件 DSO 的 DSO 字段为 `<路径>+0x<偏移>`。
   - MMAP2 行：`<pid>/<tid>  PERF_RECORD_MMAP2 <pid>/<tid>: [<起点>(<长度>) @ <pgoff> <设备号 inode generation，或 <build-id>>]: <权限> <路径>`。
   - MMAP 行（内核模块、内核等的合成映射）：`<pid>/<tid>  PERF_RECORD_MMAP <pid>/<tid>: [<起点>(<长度>) @ <pgoff>]: <x|r> <路径>`（`util/event.c:315–322`）；内核映射的 pid 可以是 -1。
   - 丢样行：`<pid>/<tid>  PERF_RECORD_LOST lost <N>`（格式在 `util/event.c:487–490`）。06 报告实测 942 条，N 之和 61,667，与 `perf report` 的 `Total Lost Samples` 一致。该行不带事件名或事件 ID，无法归属到某个事件、DSO 或 pid。N 是丢失的**输出记录**数，不只是样本：内核对样本与 MMAP、MMAP2、COMM 等边带记录走同一个输出入口，写不进环形缓冲区时一并累加同一个丢失计数，之后以 `PERF_RECORD_LOST` 输出（`kernel/events/ring_buffer.c:178–182`、`:250–265`；MMAP 输出在 `kernel/events/core.c:8800–8828`，COMM 在 `:8456–8473`）。文本无法区分 N 中样本与边带记录各占多少。
   - v6.12 的 `--show-lost-events` 只为 `PERF_RECORD_LOST` 安装打印回调（`builtin-script.c:2930–2931`），不打印 `PERF_RECORD_LOST_SAMPLES`；而 perf record 会根据内核的计数器合成 `PERF_RECORD_LOST_SAMPLES`（`builtin-record.c:1936–1980`）。两者的关系未核实，不能把后者视为另一桶独立的 IP 丢样。
   - 特殊 DSO：`[kernel.kallsyms]` 不带偏移；`[vdso]` 带偏移（形如 `([vdso]+0x4ec)`）。名字以 `[` 开头的 DSO 在 dsoff 下打印长名（`map.c:439–444`）；没有映射时打印 ` ([unknown])` 且不带偏移（`map.c:446–486`，尚未实测）。内核模块属于 object file（`util/dso.c:77–106`），会带偏移，形式与普通文件 DSO 相同。被删除文件的 DSO 名带 ` (deleted)` 后缀，位于最后的 `+0x偏移` 之前（07 报告 3.3 实测，形如 `(/opt/.../libdeleted_probe.so (deleted)+0x410)`；BOLT 解析同类输出时也单独处理该后缀，`DataAggregator.cpp:1977`）；即使录制时用了 `--buildid-mmap`，被删除文件的合成 MMAP2 也可能不带 build-id，按缺失身份处理。内核模块实测为完整的模块路径加偏移（形如 `(/lib/modules/6.12.80-arm-rpi4-v7l/extra/kdbus/kdbus.ko+0x945c)`），其合成映射记录为 `PERF_RECORD_MMAP` 而不是 MMAP2（07 报告 3.4）。合成映射记录的外层 pid/tid 前缀可以是 `0/0`，映射所属的 pid 以记录类型之后的字段为准。
4. 实测样例作为 lit 素材的来源：样本行、MMAP2 两种形式、`[vdso]`、`[kernel.kallsyms]`、LOST、`-1/-1` 样本（05、06、09 报告），`(deleted)`、内核模块与 `PERF_RECORD_MMAP`（07 报告）。`[unknown]` 在 05–09 的数据中都没有出现，按 perf 源码中的格式编写素材并注明来源。`PERF_RECORD_LOST_SAMPLES` 不作为该导出命令的已支持文本记录；将来有实际导出格式与准入证据后再增加。

#### 5.2.3 解析规则（严格）

1. 显式识别以下记录：样本行；`PERF_RECORD_MMAP`/`PERF_RECORD_MMAP2`；`PERF_RECORD_LOST`；导出选项带出的其他 `PERF_RECORD_*` 行按清单计数后跳过。遇到不认识的行一律报错：perf script 的文本格式不是稳定 ABI。
2. 样本行按固定字段顺序解析：先完整读出 pid/tid（带符号整数，见第 8 条）、period、`<event>:`、ip 这些前缀字段；ip 之后的剩余部分必须以 ` (` 开头、以行尾的 `)` 结尾，两者之间的全部内容为 DSO 字段。若 DSO 字段以 `+0x<十六进制>` 结尾，则拆出偏移，其余部分为路径；路径内部的空格、括号（包括 ` (deleted)`）和 `+0x` 原样保留。不能用"最后一个 ` (`"切分路径。无法由该行式格式无歧义表示的路径（例如含换行）明确报错。
3. MMAP2 行同样按固定前缀解析，路径取 `]: <权限> ` 之后到行尾的全部内容；MMAP 行的路径取 `]: <x|r> ` 之后到行尾的全部内容。记录内的 pid/tid 同样按带符号整数解析。
4. 必需字段缺失、整数损坏、行被截断时，整份输入报错，不逐行猜测。`period=0` 的样本报错。
5. 内核样本：DSO 为 `[kernel.kallsyms]`，或路径位于 `/lib/modules/` 之下、以 `.ko`、`.ko.xz`、`.ko.zst`、`.ko.gz` 结尾（按实测样例确认）的样本归为内核，按 DSO 名分类，不按地址范围（armv7 的用户/内核分界取决于 VMSPLIT 配置）。第一批只计入 `samples.kernel`，不生成内核 profile。
6. 其他特殊 DSO（`[vdso]`、`[unknown]`、`//anon`、JIT 等）按名称识别：带偏移的计入 `other_dso`，不带偏移的计入 `samples.unmapped`。不得把特殊 DSO 当作文件 DSO 去匹配目标。
7. 丢样：
   - 每条 `PERF_RECORD_LOST lost N` 计为一条 LOST 记录与 N 个丢失的输出记录（可能包含边带记录，见 5.2.2 第 3 条），分别统计并记录来源；报告记 `count_unit=records`。为与 perf 的用语一致，报告字段仍称 lost，但注明含边带记录。
   - L > 0 时报告给出告警 `W_LOST_MAY_INCLUDE_SIDEBAND`，并记 `mapping.completeness=unknown`：边带记录丢失时，perf 的 dsoff 归属可能不完整，多数情况下样本落到 `[unknown]`，极端情况下 exec 之后旧映射仍留着，样本可能被归到旧映像。身份判定照常按 5.3.2 进行（丢失的映射记录按缺失处理）。
   - 节流（THROTTLE/UNTHROTTLE）不计入丢样，作为已知局限写入报告；能看到节流记录时计数。
   - "未知"不得写成 0：工具自己导出（`--perfdata`）时，没有 LOST 记录只表示可见的 `PERF_RECORD_LOST` 计数为 0；`--perfscript` 输入时，出现 LOST 记录就记数值，否则记为 `unknown`（工具无法知道导出时是否带了该选项）。两种情况下报告都记 `lost.completeness=unknown`：可见计数既不能拆分出 IP 样本，也不覆盖 `PERF_RECORD_LOST_SAMPLES`，所以不宣称它是真实 IP 丢样数的下界，也不宣称是上界。
   - 丢样比例是输入级的诊断代理量，不是目标的真实丢样率：`exported_lost_ratio = L / (L + S)`，L 为全部可见 LOST 记录中 N 的总和，S 为整份输入中筛选前的样本行数。按数量计算，不按 period 加权，不用目标 DSO 的样本数作分母（LOST 行无法归属到事件、DSO 或 pid）。报告同时记 `scope=input`、`source=PERF_RECORD_LOST`、`count_unit=records`。以 06 报告的数据为例（record 写出 703,821 个样本）：61,667 / (61,667 + 703,821) ≈ 8.06%，与 `perf report` 提示的比例一致；导出文本中的样本行数是否等于 record 写出的样本数，lit 素材按实际导出核对。
   - 门槛判定（5.6.2 第 4 条）：`exported_lost_ratio` 超过 `--ip-max-lost-ratio` 时判为 `exceeded` 并按契约失败，含义是"可见诊断量超过了配置的输入质量门槛"，不据此推断真实 IP 丢样率；未超过时判为 `not_exceeded`，同样只针对这个诊断量。06 报告约 8.06% 的一致性不能证明那次的丢失全部是样本。
8. pid/tid：按带符号十进制整数解析，接受 -1，小于 -1 的值按格式错误处理。pid 为 -1 表示样本或映射的进程未知（09 报告中为系统级录制的内核样本；内核的合成映射也可能是 -1），不推断其产生原因。pid 为 -1 的样本照常按 DSO 字段分类（第 5、6 条），计入报告的 `samples.pid_unknown`；`--pid` 永不匹配 pid 为 -1 的样本。

#### 5.2.4 `--perfdata` 输入（有条件）

1. 前提：主机上有与板上录制所用 perf 版本一致、且能读取该 perf.data 的 perf。06 报告查询的仓库没有 x86_64 perf 包。获得主机 perf 的方式（例如在工作目录内从同一内核源码为 x86_64 构建 tools/perf）由用户决定。
2. 准入：主机 perf 对同一份 perf.data 的导出与板上导出逐行一致（允许的差异逐类列明理由）之后，`--perfdata` 才进入第一批交付；否则第一批只交付 `--perfscript` 输入，`--perfdata` 在 IP 模式下报错并提示改用板上导出的文本（C5）。准入证据绑定"主机 perf 版本、板上 perf 版本"这一对，任一方变化后重新比对；版本号一致不能代替逐行比对。
3. 行为：IP 模式自带一次 perf 调用（命令同 5.2.2），不复用 LBR 路径的转换函数。现有转换函数分两次调用 perf，不检查退出码，字段固定为 `ip,brstack`，PID 预扫描会排除 fork 出的子进程（`L/PerfReader.cpp:451–519`）。LBR 路径的转换函数保持不变（C1）。
4. 检查 perf 的退出码并分别保存 stdout 与 stderr。非 0 退出、或输出部分内容后失败，都不得继续生成结果。需要 buildid-list 时另调用 `perf buildid-list`。主机 perf 的路径、版本与完整命令写入质量报告。

### 5.3 地址换算与身份校验

#### 5.3.1 地址换算

1. 对目标 DSO 的样本，取 DSO 字段中的文件偏移 `off`，在 `--binary` 的可执行 PT_LOAD 中查找满足 `p_offset ≤ off < p_offset + p_filesz` 的段，换算为 ELF 虚拟地址：

   `vaddr = p_vaddr + (off − p_offset)`

2. 必须唯一匹配。落在段外或段间空隙的偏移计入 `target.unmapped_in_target`，不得猜测。所有算术检查溢出。
3. 该公式与页大小无关，也不使用全局 `BaseAddress` 与 4K 掩码。AddressCounter 的键是 `--binary` 中的 ELF 虚拟地址。
4. 已验证范围：新镜像 libavcodec 的可执行 PT_LOAD 为 `p_offset = p_vaddr = 0`，全部样本唯一落入该段；两个由 shell 启动（fork + exec）的进程以不同基址加载同一库时 dsoff 换算 100% 一致（05 报告 B.3、B.4）。RPi5 的 aarch64 libavcodec 同样只有一个可执行 PT_LOAD（`p_offset = p_vaddr = 0`），单进程与双进程的样本全部唯一落段、100% 一致（09 报告 3.2、3.3 节）。不 exec 的 fork 子进程没有自己的 MMAP2 记录，但其样本的 dsoff 偏移与父进程映射计算的结果 100% 一致；同一进程 exec 到不同映像后，前后样本都归属正确，没有样本被归到旧映像（07 报告 3.1、3.2）。这两种情形依赖 perf 的映射处理，正式实现的验收中仍保留板上集成用例（5.10）。`p_offset ≠ p_vaddr`、多个可执行段、16K/64K 对齐等布局由离线 lit 覆盖：两块板上都没有观察到可执行段 `p_offset ≠ p_vaddr` 的实例（09 报告中 RW 段的 `p_offset ≠ p_vaddr` 不是代码段，不算覆盖），这类布局不再列为板上待核实项。
5. 不实现自建的 pid/fork/exec 映射表。perf 不支持 dsoff 时直接报错，不退回现有的全局基址逻辑。自建映射表（参照 BOLT `DataAggregator.cpp:1800–1885` 解析 COMM exec 与 FORK，:1963–2046 按 pid 建立映射）与原生 perf.data 解析一起放在第三批（第 7 节）。

#### 5.3.2 身份证据与等级

1. 证据来源（逐映射或逐路径记录 `source`）：
   - `mmap2`：MMAP2 记录带 `<build-id>`，按逐映射证据处理（读取时机见 5.2.1 第 1 条）。
   - `buildid-list`：`--perf-buildid-list`（或 `--perfdata` 时工具调用的 buildid-list）中该路径的 build-id。这是路径/DSO 级的证据，其原始采集来源记为 `unknown`，不能冒充逐映射证明。buildid-list 中路径前为空白、没有 build-id 的行，按缺失处理。
   - `inode`：MMAP2 不带 build-id 时的设备号、inode 与 generation。只用于未验证模式下的歧义检查（5.3.3 第 5 条），不作为身份证明。
2. 必要身份：目标 ELF（`--binary`）的 build-id；给出 `--debug-binary` 时调试文件的 build-id；每个候选路径的可执行映射集合 M（权限含 `x`）中每个映射的身份证据。
   - M 为空时（包括候选路径在输入中没有任何映射记录，以及只有非可执行映射的情形），该路径的映射身份按缺失处理，最终不高于 `unverified`；即使存在非可执行映射或匹配的 `buildid-list`，也不得以空集合判定通过。
   - 非可执行映射（例如 `perf record -d` 带来的数据映射）不进入 M，不会因为缺少证据而使等级下降；但它们带有的已知 build-id 仍参与冲突检查。
3. 等级的汇总公式（与目标 ELF 的 build-id 比较之后才确定）：
   - 任一已知证据与目标不一致（包括同一路径出现不同 build-id、`mmap2` 与 `buildid-list` 给出不同 ID、调试文件 ID 与目标不同，以及候选路径的非可执行映射带有不同 ID）：最终为 `mismatch`。冲突优先于缺失：两者同时存在时按 `mismatch` 失败。
   - 一方有 build-id、另一方没有，也是已知的不一致，判为 `mismatch`：build-id 是 ELF 内容的一部分，没有 note 的文件不可能是含 note 的那个文件。具体为：目标 ELF 没有 build-id，而任一候选映射或路径有 build-id 证据（`mmap2` 或 `buildid-list`）；目标 ELF 有 build-id 而给出的调试文件没有，或反过来（Tizen 的调试拆分保留 note，08 报告 2.1 节；将来需要支持会丢弃 note 的拆分工具时另行准入）。
   - 目标 ELF 没有 build-id、给出的调试文件也没有、且输入侧完全没有 ID 证据：最终不高于 `unverified`。
   - 否则对每个候选可执行映射取其最强的可用证据：有与目标一致的 `mmap2` 证据为 `verified`；没有 `mmap2` 证据、但该路径有与目标一致的 `buildid-list` 证据为 `verified-path`；两者都没有为缺失（`unverified`）。路径带 ` (deleted)` 的映射不得用 `buildid-list` 补足（被删除的文件与路径当前对应的文件可能不同），没有 `mmap2` 证据即为缺失。
   - 最终等级取全部候选映射等级中的最小值，顺序为 `verified` > `verified-path` > `unverified`。
   - 最终为 `unverified` 时，只在给了 `--allow-missing-build-id` 时继续，否则失败。
   - 示例：同一路径的两个映射一个有一致的 `mmap2` 证据、一个没有，而该路径有一致的 `buildid-list` 证据，最终为 `verified-path`；没有 `buildid-list` 证据时为 `unverified`。
4. 记录 `observed_mmap_build_id`（输入中是否出现过带 build-id 的 MMAP2），不据此反推录制命令。

#### 5.3.3 目标选择与判定

1. 候选：
   - 给出 `--binary-match-regex` 时，只以该正则匹配样本的原始 DSO 路径（含 ` (deleted)` 标记）选择候选；未匹配的路径即使文件名与 `--binary` 相同也不进入候选。
   - 未给出时，按文件名（basename）与 `--binary` 经 realpath 解析后的文件名匹配（MMAP 中的路径是内核解析后的真实文件名，例如 09 报告中的 `/usr/lib64/libavcodec.so.62.11.100`；`--binary` 给的可能是 `libavcodec.so.62` 这样的符号链接）；比较前识别并去掉样本路径末尾的 ` (deleted)` 标记。报告同时记录给出的路径与解析后的路径。原始路径与 deleted 状态完整保留，用于身份判定与报告，不与未删除路径的身份证据自动合并。
   - 候选为空时按"目标样本为 0"失败，报错中列出样本数最多的至多 5 个文件 DSO，并提示用 `--binary-match-regex` 指定（例如从板上拉回的文件被改了名）。
   - 特殊 DSO 不参与候选。
2. 一致性：样本映射、`--binary` 的 note、`--debug-binary` 的 note，所有已知的 build-id 必须一致。build-id 按完整字节串比较，不假设长度，也不根据链接器推断长度（第 1 节第 6 条）；长度不同即为不一致。任一已知冲突始终失败，`--allow-missing-build-id` 不能覆盖冲突。
3. 保守汇总：样本行只带路径，无法把单个样本绑定到具体映射，因此按 5.3.2 第 3 条的公式对全部候选映射汇总。同一身份的多个进程、多次加载合并计数（不同加载基址已由 dsoff 处理）。改名但 build-id 相同的映像，用 `--binary-match-regex` 纳入候选后可以匹配。
4. 路径带 ` (deleted)` 的映射：有 `mmap2` 证据时按它判定；没有时为缺失（默认失败；给了 `--allow-missing-build-id` 时为 `unverified`），不用 `buildid-list` 补足；已知 ID 冲突始终失败。被删除的目标样本在默认文件名匹配下进入候选，不得悄悄归入 `other_dso`。
5. 未验证模式（`unverified`）下的歧义检查，在已选出的候选集合上跨 pid 执行（显式正则已排除的路径不重新加入）：
   - 候选集合中出现文件名相同但路径不同的 DSO，报歧义错误，要求用 `--binary-match-regex` 或 build-id 区分；
   - 同一路径（去掉 ` (deleted)` 标记后比较）出现不同的（设备号, inode, generation），或同一路径既有 deleted 又有未删除的映射，报歧义错误（文件在录制期间被替换）。
6. 目标二进制本身没有 build-id：输入侧与调试文件也都没有 ID 证据时按缺失处理（无 `--allow-missing-build-id` 时失败）；任一方有 ID 证据时为 `mismatch`，`--allow-missing-build-id` 不能放行（5.3.2 第 3 条）。
7. 身份未验证时，报告给出合理性指标：目标样本落在 DWARF 函数区间内的比例；在 AArch64 上再给出 4 字节对齐的比例（armv7l 上 Thumb 指令为 2 字节对齐，对齐比例没有区分度，不给出）。
8. 报告中的 `mapping` 计数指输入中观察到的映射记录，不表示样本已逐条绑定到这些映射。
9. 校验范围：身份校验的链是"采样记录 → 实际被采样的 ELF A → A 的调试文件"。`--binary` 必须对应实际被采样的映像 A，调试文件必须对应 A；工具只按 build-id 判定，不按文件所在目录或来源判定（`--binary` 在现有工具中的定义就是被采样的二进制，`L/llvm-profgen.cpp:60–74`；`getBuildID` 只返回 note 中的字节，`BuildID.cpp:26–55`）。采样对象来自已安装的 RPM 时，应保留该安装产物及其匹配的 debuginfo，不得未经核对就用打包前的 BUILD 产物替代，因为打包可能改变 build-id（第 1 节第 6 条）；直接采样未打包的产物同样允许。用该 profile 构建出的新 ELF B 不参与比较，不要求与 A 同 build-id；B 的代码与 build-id 改变是正常情况。

#### 5.3.4 分离调试文件的身份链

1. Tizen 的包是"strip 后的运行文件 + debuginfo 包"的形态。`--binary` 提供采样映像的加载布局、身份与指令字节；`--debug-binary`（已有选项，`L/llvm-profgen.cpp:70–74`、`L/ProfiledBinary.cpp:248–257`）提供匹配的 DWARF、`.symtab`，以及 armv7l 上需要的映射符号（5.7.2）。调试文件中的代码节为 NOBITS，指令字节一律从 `--binary` 读取。
2. build-id 一致性按 5.3.3 第 2 条处理。不要求 strip 前后的文件整体 SHA-256 相同。`getBuildID` 先找 SHT_NOTE 节再找 PT_NOTE 段（`BuildID.cpp:37–55`）。调试文件中的 build-id note 可读且与运行文件一致（08 报告 2.1 节，当前工具链显式 sha1 构建）；新工具链默认路径在发布后复核（第 10 节步骤 9）。
3. DWO/DWP 沿用已有的 `--dwp` 等路径；缺失时在报告中列出，并体现在目标可用率中。
4. strip-all 的 `--binary` 加 `--debug-binary` 生成的 profile，必须与未 strip 时逐字节一致（5.10 用例）。对照对象是同一个 ELF 用 `llvm-objcopy` 拆分前后的文件（build-id 相同），或用 `eu-unstrip` 合并后的文件；不是 GBS BUILD 目录中的链接产物（其 build-id 可能与打包后的文件不同）。lit fixture 的生成命令中写明拆分方式。

#### 5.3.5 LBR 路径

身份校验在 LBR 路径中不启用，以满足 C1。后续如需让 LBR 路径也使用，另行设计。

### 5.4 计数生成：行级（DWARF）模式

#### 5.4.1 地址计数、权重与 P_ref

1. AddressCounter 对每个 ELF 虚拟地址 `a` 保存整数 `sample_count(a)` 与 `period_sum(a)`（uint64，检查溢出）。
2. 每个地址的整数分子 `u(a)`：`--ip-weight=period` 时为 `period_sum(a)`；`--ip-weight=sample` 时为 `sample_count(a)`，此时 P_ref 视为 1。
3. P_ref（`--ip-weight=period` 时）：
   - 必须为正整数。`--ip-period-unit` 显式给出时用该值。
   - 自动取值：对经事件、pid 与目标 DSO 筛选后、符号化之前的样本 period 取中位数；样本数为偶数时取较小的中位数。全部样本 period 相同（`-c` 模式）时即为该值，此时 period 与 sample 两种权重写出的结果相同。
4. 归一化的原因：clang 会把超过 uint32 的分支权重截断为 UINT32_MAX（`SampleProfile.cpp:1720–1725`）。spike 的 cycles 数据有 68,745 个样本、period 为 500009，总量约 3.4e10，不归一化时单个热点行就会远超 4.29e9，两个热点后继会被压成 1:1。
5. 语义：`sample` 是命中次数，`period` 是事件量的估计（cycles 为周期数，cpu-clock 为纳秒），两者都不是执行次数。period 加权用于补偿逐样本采样周期的变化（05 报告实测频率模式的 period 从 1 到约 2e7），不保证消除 PMU 复用、丢样、节流与 skid 引入的偏差。一次运行只统计一种事件，cycles 与 cpu-clock 不混算。作为对照：create_llvm_prof 的 IP 模式每个样本计 1，不按 period 加权（`sample_reader.cc:292–302`）。

#### 5.4.2 符号化与归类

1. 对每个唯一地址，经 ProfiledBinary 的符号化器（LLVMSymbolizer）得到内联帧链。
2. 地址不在任何 DWARF 函数区间内：计入 `target.outside_dwarf_func`，不写入 profile。它表示缺少 DWARF 函数归属，不自动等同于汇编。尽可能细分原因：
   - `plt`：地址位于 `.plt`、`.plt.got` 等链接器生成的节；
   - `in_cu_no_subprogram`：地址落在某个 CU 的地址范围内，但没有对应的 subprogram。带 `-g` 的汇编文件会落入这一类，但调试信息不完整、subprogram 缺名字或范围读取失败（现有加载会跳过这类 subprogram，`L/ProfiledBinary.cpp:938–956`）也会落入，所以它只提示、不证明汇编来源；有独立的语言属性（如 CU 的 `DW_AT_language`）或构建证据时，报告另附 `assembly` 来源说明；
   - `no_cu`：没有任何 CU 覆盖该地址（缺失调试信息、缺失 DWO、或调试文件不匹配）。
3. 在函数区间内但行号为 0：计入 `target.in_func_no_line`。
4. 其余计入 `target.usable`，参与计数。

> 增补：5.4.2 的归类另见附录 G.1.9（非叶子内联帧行号为 0 时整体排除，单列 `nonleaf_line_zero`）；Thumb 函数在 GNU 汇编生成的调试信息中起始地址为奇数时的符号化另见附录 G.1.8。

#### 5.4.3 聚合键

聚合键为：顶层函数 + 完整内联调用点链 + 叶子位置（行偏移, base discriminator）。同一个内联函数出现在两个调用点时属于两个不同的键。普通 discriminator 与 FS discriminator 沿用现有的 `getBaseDiscriminator` 与 `UseFSDiscriminator` 处理。

#### 5.4.4 聚合方式（`--ip-aggregation`）与取整

设 `d(a)` 为从 discriminator 解码出的 duplication factor，`n(k)` 为聚合键为 k 的指令总数：包括未采到的指令，包括各展开副本，跨该函数的全部 DWARF 区间，排除数据（`$d`）。

| 方式 | 整数分子 | 写出值 |
|---|---|---|
| `sum` | `Σ u(a)`，a 取键 k 的全部地址 | 分子 / P_ref |
| `max` | `max (u(a) × d(a))` | 分子 / P_ref |
| `avg` | `Σ (u(a) × d(a))` | 分子 / (P_ref × n(k)) |

推导（理想化）：一段代码展开为 d 份、每份执行 N/d 次，设指令 i 的代价为 c_i，则 `u(a) ∝ (N/d)·c_i`。`sum` 不乘 d，自然得到 `N·Σc_i`；`max` 的原始最大值为 `(N/d)·max c_i`，乘 d 后为 `N·max c_i`；`avg` 乘 d 并除以含全部副本的 `n(k)` 后为 `N·c̄`。`max` 的语义与现有 LBR 路径（`L/ProfileGenerator.cpp:393–412`）及 Google 的实现（`symbol_map.cc:622–624`、`:648–655`）一致。

1. 整数累计：所有分子用整数保存，乘法与加法用 LLVM Support 的宽整数或溢出检查完成；任何中间值或最终值超出 uint64 时报错。不在逐地址、逐内联帧插入时提前取整。
2. 取整：聚合完成后，每个键只做一次除法与取整（四舍五入，0.5 向上）。写出值为 0 而分子为正（即被采到的键）时写 1，避免把采到的位置写成 0。
3. 写出前任一 body 或 total 超过 UINT32_MAX 时告警并写入报告（归一化后正常不应出现）。
4. `avg` 的 `n(k)` 由 5.7.2 的按需枚举得到。指令边界无法确定时按 5.7.2 第 6 条处理（整次运行失败）。
5. 默认值不在设计阶段拍板，由 5.8、5.9 的评估决定，判据见 5.8 第 6 条。证据不足以区分各方式时选 `max`，因为它与两个参考实现对齐；这是保守选择，不称为统计等价。

#### 5.4.5 函数 total

1. 每个样本的整数分子 `u(a)` 对其内联链上每一层的 FunctionSamples（叶子及全部祖先）各计一次，不乘指令长度（LBR 路径按字节累计，`L/ProfileGenerator.cpp:715–720`），也不把已含 inlinee 的父 total 与 inlinee total 重复相加。
2. total 在独立的整数结构中累计，最后与 body 一样只做一次除以 P_ref 的取整；正分子对应的 profile，其 total 写出后至少为 1。
3. total 与聚合方式无关，只有 body 随聚合方式变化，这样比较聚合方式时只改变一个变量。

#### 5.4.6 入口计数（`--ip-head-samples`）

1. 消费端行为：
   - 不开 profi 时，入口块所在等价类的权重和函数入口计数都是 `HeadSamples + 1`（`llvm/include/llvm/Transforms/Utils/SampleProfileLoaderBaseImpl.h:624–627`、`:1060–1061`）。不写 head 时所有函数的入口计数都是 1，基于入口计数的判定（`isFunctionEntryCold`，`ProfileSummaryInfo.cpp:105–116`）会把这类函数当作冷入口；是否落在冷阈值内取决于该 profile 的 summary（`isColdCount`，`:186–188`）。`isFunctionColdInCallGraph` 需要入口、调用与全部块都冷才判冷，不受此单独影响。
   - 开 profi 时，入口计数取 profi 推断出的入口块权重，推断结果为 0 时才回退到 `HeadSamples + 1`（`SampleProfileLoaderBaseImpl.h:1089–1095`）。
   - 非 CS profile 的内联决策用 `getHeadSamplesEstimate` 估计 head（`llvm/include/llvm/ProfileData/SampleProf.h:1000–1021`）。
2. `none`：不写 head samples。前提是编译与链接两步都开启 profi：
   - 非 LTO 构建：clang 驱动在编译作业中默认注入 profi（第 1 节第 6 条）。
   - (Thin)LTO 构建：链接步骤不会自动注入，post-link 的 sample loader 默认关闭 profi，必须在链接步骤另外传入（lld 写法为 `-Wl,-mllvm,-sample-profile-use-profi`；其他链接器的写法未核实），链接步骤还须传入同一 profile（5.9 第 1 条）。目前的 optflags 与 `ffmpeg.spec` 都不含 `-flto`。
   - 报告的 `consumer_hints` 给出这两条提示。
3. `entry-estimate`：在 body、callsite 与 total 都构建完成后，对顶层 FunctionSamples 调用 `getHeadSamplesEstimate()`，把结果写入 head；内联调用点下的 profile 不额外写 head。该估计在最早的内联调用点行号更小时会递归使用调用点的估计，并在 total 为正时至少返回 1。它不等于真实的入口执行次数；不得用函数 total 冒充入口计数。
4. 默认值暂定 `none`，不能只因驱动默认开启 profi 就冻结；由 5.9 中"profi 开/关 × head 策略"的分组确定。

#### 5.4.7 补零（`--ip-zero-fill`）

1. 背景：LBR 路径会给有样本函数的全部区间补 0（`L/ProfileGenerator.cpp:672–690`），编译器把 0 理解为"不执行"。对稀疏的 IP 采样，"没采到"不等于"没执行"，而 profi 会把 0 当作已知的冷块。
2. `none`：未采到的位置保持缺失（未知），不复用 LBR 的补零逻辑。
3. `sampled-functions`：对有样本的函数，把其 DWARF 区间内未采到的键写为 0。枚举方法、可用条件与失败处理同 5.7.2。
4. 无样本的函数在任何策略下都不写入。默认 `none`（暂定）。

#### 5.4.8 采样位置漂移（`--ip-skid`）

1. 背景：异步采样得到的 IP 往往是"下一条将要执行的指令"，cpu-clock 是中断返回地址，PMU 溢出也有漂移。计数会系统性地前移，还可能越过已跳转的分支落到目标块。
2. `none`：不调整。
3. `prev-inst`：把地址换成布局上的前一条指令的地址，前提是前一条指令仍在同一函数区间内且不在数据范围中；否则不调整，计入 `skid_unadjusted`。前一条指令由 5.7.2 的边界枚举得到（Thumb 指令长度为 2 或 4 字节，不能向后猜）。可用条件与失败处理同 5.7.2。
4. 已知局限：跳转之后，实际上一条执行的指令不是布局上的上一条。默认 `none`（暂定），与聚合方式一起在 5.8 评估。

> 增补：5.4.8 的前驱条件与未调整原因另见附录 G.1.1（在本节条件上追加，不替代本节的函数范围限制）。

#### 5.4.9 其他

1. 间接调用目标：IP 数据无法得到，不生成。
2. 落在 `outside_dwarf_func` 中的样本无法写入 profile，只在报告中按原因分类，并按 `.symtab` 名称列出前 20 个（5.4.2 第 2 条）。

### 5.5 pseudo-probe 子方案（实验性，单独准入）

本子方案不属于第一阶段冻结范围，以独立的实验补丁推进，不阻塞 DWARF 路径。通过准入之前不进入 llvm 包；在此之前 IP 模式对带 probe 的二进制按 5.1.4 报错。本节只确定边界与准入条件，映射与计数规则在子方案的准入设计中冻结。

1. 动机：pseudo-probe 以块为单位标识位置，并带函数 CFG 校验和，有助于发现 profile 与代码失配。LLVM 的 stale matching 同时存在于行级与 probe 两条路径：对 probe profile 默认开启（`SampleProfile.cpp:2038–2047`）；对行级 profile 需显式开启，且锚点只有调用点（`llvm/lib/Transforms/IPO/SampleProfileMatcher.cpp:114–128`）。IP profile 没有调用目标，锚点有限，所以可复用范围靠测量，不预先承诺。
2. 消费端的连带效应：probe profile 会自动开启 profi、迭代 BFI、ext-tsp 等（`SampleProfile.cpp:2015–2047`）；陈旧度过高时整份 profile 会被拒绝（`rejectHighStalenessProfile`，`SampleProfile.cpp:2100–2137`、`:2176–2178`）。陈旧度只统计热度在 80 万分位以上的函数（:2113–2115），热函数少于 50 个时跳过检查（:247–250），小 benchmark 不会触发整体拒绝。
3. 映射问题：LLVM 中没有现成的"任意 IP → 块"组件。`AddressProbesMap::find()` 是精确匹配；BOLT 靠自己的 CFG 把 probe 归到块（`DataAggregator.cpp:2394–2410`），profgen 无法复用。
4. 两种候选映射，都要评估，正确性优先：
   - M1（最近 probe）：先由 DWARF/符号表确定 IP 所属的函数区间片段，再在该片段内取地址不大于 IP 的最大 probe 地址，把该地址上的全部 probe（含内联 probe）计入；IP 小于片段首个 probe 时单独统计其占比。
   - M2（精确块边界，先做 AArch64）：构建时加 `-fbasic-block-address-map`（clang 驱动只对 X86 与 AArch64 的 ELF 放行，`Clang.cpp:6179–6187`），用 `ELFObjectFileBase::readBBAddrMap`（`llvm/include/llvm/Object/ELFObjectFile.h:119–128`）得到机器块边界，把 IP 归到所在机器块，再把该块内的 probe 计入。它不能自动解决"一个机器块含多个逻辑 probe"的关联，需要另定规则。armv7l 不能使用 M2。
5. 必须处理的情形：一址多 probe、同一 probe 多份副本、被优化掉的 probe、call probe 与 block probe、冷热分区后的函数片段、内联边界。基本块本身是连续的，重排不分裂块；真实风险是冷块外迁导致函数地址范围不连续，以及部分块没有 probe。无法确定归属的样本单独报告，不向前猜测。
6. 计数：IP 计数约等于"执行次数 × 块代价"，与 LBR 下 probe 计数的"执行次数"不同。块计数按 `--ip-aggregation` 用块内指令数归一化（指令边界来自 5.7.2）；skid 处理与 5.4.8 相同；head 取 entry probe 的计数。
7. 架构：IR 层插入 probe 和块 probe 的发射是通用路径；MIR 层的 `PseudoProbeInserter` 在本树只挂在 X86 后端（`X86TargetMachine.cpp:615–616`），它负责给调用指令加带 probe 编码的 discriminator，所以在 AArch64 上要重点核对 call probe 是否完整。先在 AArch64 上用 `--show-pseudo-probe` 核对 `.pseudo_probe` 结构（函数记录、块 probe、call probe 数量）；armv7l 验证失败时，probe 只支持 aarch64。
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
| `input` | 输入路径与 SHA-256；`projection`（固定为 `ip-only`）；`--perfdata` 时还有 perf 路径、版本、完整命令与退出状态 |
| `event` | 实际选中的完整事件名（含修饰符）；事件的 type/config 等未作为输入提供的属性写 `unknown`，不从名字猜测；多事件时按完整事件名分别给出筛选前的样本数与 `period_sum`（不同事件的权重单位不同，不合算为一个总量） |
| `semantics` | `weight`、`raw_event_unit`（cycles / ns / samples）、`output_count_unit`（period 模式为 `normalized-event-count`，sample 模式为 `samples`）、`p_ref` 及其来源（显式 / 自动）、`aggregation`、`dup_policy`、`zero_fill`、`head_samples`、`skid`、`mode`（dwarf / probe）、`fs_discriminator` |
| `identity` | `observed_mmap_build_id`；目标路径（给出的路径与 `binary_realpath`）与 build-id；`--debug-binary` 的 build-id；候选的选择方式（正则 / 文件名）与候选路径（原始路径与 deleted 状态）；逐映射或逐路径的证据 `source` 与判定；最终等级（`verified` / `verified-path` / `unverified` / `mismatch`） |
| `mapping` | pid 数、输入中观察到的候选映射记录数（可执行与非可执行分开）及其证据分类（不表示样本已逐条绑定到这些映射）；`completeness`（有可见 LOST 记录时为 `unknown`，5.2.3 第 7 条） |
| `samples` | 逐层统计。`input_total` 只给出跨事件的样本数（事件筛选前的 `period_sum` 按事件分别放在 `event` 中）；选定单一事件之后的各层同时给出样本数、`period_sum` 与归一化权重（保留原始整数分子与 `p_ref`，避免整数展示提前丢失小数）：事件筛选后、pid 筛选后、`pid_unknown`（pid 为 -1）、`kernel`、`other_dso`（按 DSO 列前 20，含 `[vdso]`）、`unmapped`、`target`、`target.unmapped_in_target`、`target.outside_dwarf_func`（按 `plt` / `in_cu_no_subprogram` / `no_cu` 分类，并按 `.symtab` 列前 20）、`target.in_func_no_line`、`target.usable`、实际写出的位置数、`skid_unadjusted` |
| `isa` | armv7l 上按样本数与权重分别统计落在 Thumb、A32 与无法判定代码中的比例；判定依据（映射符号或函数符号的 `SF_Thumb` 标志）一并写明 |
| `boundaries` | 按需枚举时：枚举的函数数、边界来源（映射符号）、失败的函数列表与原因 |
| `lost` | LOST 记录条数、N 之和 L（丢失的输出记录数，可能含边带记录）、`exported_lost_ratio`、`scope=input`、`source=PERF_RECORD_LOST`、`count_unit=records`、`completeness=unknown`（5.2.3 第 7 条）；无法获知时为 `unknown` |
| `throttle` | 节流记录数，或 `unknown` |
| `ratios` | `target_usable_ratio = usable / target`（判定用；口径见 5.6.2 第 1 条，另一口径也给出）；`line_resolution_ratio = usable / (usable + in_func_no_line)`（只报告）。分母为 0 时写 `unknown` |
| `sanity` | 身份未验证时给出：落在 DWARF 函数区间内的比例；AArch64 上 4 字节对齐的比例 |
| `coverage` | 有样本的函数数、唯一地址数、权重最高的前 50 个函数及占比 |
| `consumer_hints` | 例如 `head_samples=none` 时提示"编译与链接两步都不得关闭 profi；LTO 时链接步骤需显式开启" |
| `warnings` | 全部告警，带稳定的诊断代码（例如全部 period 相同时的 5.2.1 第 3 条提示） |
| `verdict` | `conversion`（`ok` / `failed`，失败阶段 `failure_stage` 与原因；阶段取值为 `load` / `parse` / `identity` / `generate` / `boundary` / `write` / `commit`）；`identity`（最终等级）；`usable_ratio_check`（`passed` / `failed` / `unknown` / `not_evaluated`）；`sampling_adequacy`（`insufficient` / `unknown`，不给出 `ok`）以及 `sample_threshold_check`（`passed` / `failed` / `unknown` / `not_evaluated`）、`lost_ratio_check`（`exceeded` / `not_exceeded` / `unknown` / `not_evaluated`）两项分别的结果。各项状态的优先级见 5.6.2 第 5 条。不对运行时收益作任何判断 |

1. 未知值写 `unknown`，不写 0。整数用 uint64 表示，不经浮点，无精度损失。
2. 报告不含时间戳，数组顺序确定。同一输入运行两次，profile 与报告都必须逐字节相同。

> 增补：5.6.1 的比率与门槛写法、取值约定、合并函数名字段另见附录 G.1.4、G.1.5、G.1.10；LOST 比率分母溢出另见附录 G.1.6。

#### 5.6.2 判定口径

1. 目标可用率 `target_usable_ratio = usable / target` 用于 `--ip-min-usable-ratio` 判定，口径跟随 `--ip-weight`：period 模式用 `usable.period_sum / target.period_sum`，sample 模式用 `usable.sample_count / target.sample_count`。比率只用原始整数计数，不使用 body 聚合值、duplication、取整、"至少为 1"的修正或裁剪后的结果。它能发现大面积缺失调试信息：例如 99% 的目标样本没有 DWARF 函数归属、只有 1% 可用时，这一比率为 1%，而仅看 `line_resolution_ratio` 会得到接近 100%。
2. 门槛按真实库的汇编占比确定：libavcodec 的热点有相当一部分在 NEON 汇编中，它们属于 `outside_dwarf_func`，门槛不沿用未经验证的 0.9。第二阶段冻结之前三个门槛都没有默认值；未给出的门槛不判定，报告中对应项为 `not_evaluated`，不影响退出码。
3. `line_resolution_ratio` 只报告，用于区分"有函数归属但缺行号"的情形。
4. 采样充分性：单份输入只通过数量门槛，不能证明工作负载有代表性。`sampling_adequacy` 只在不满足 `--ip-min-target-samples`，或 `lost_ratio_check` 为 `exceeded`（5.2.3 第 7 条）时判为 `insufficient`（并失败），此时的含义是"未满足配置的输入质量门槛"；其余情况为 `unknown`。
5. 三项门槛检查的状态统一按以下优先级确定：
   - 门槛未设置：`not_evaluated`；
   - 门槛已设置，但指标没有取得（例如外部文本中没有 LOST 行）、分母无定义、或输入处理在计算该指标之前已经失败：`unknown`；
   - 门槛已设置且指标已知：执行比较，得到 `passed` / `failed`（丢样为 `exceeded` / `not_exceeded`）。
   - 门槛未设置不豁免独立的失败条件（目标样本为 0、`usable=0`、格式错误等，5.6.3 第 1 条）。门槛已设置而状态为 `unknown` 时不因该项失败，并在 `warnings` 中说明。

#### 5.6.3 失败契约

1. 以下情况返回非 0：身份为 `mismatch`，或必要身份缺失且未给 `--allow-missing-build-id`；目标样本数为 0；已设置的门槛未满足（目标样本数低于 `--ip-min-target-samples`、可见丢样比例超过 `--ip-max-lost-ratio`、目标可用率低于 `--ip-min-usable-ratio`）；`usable=0`、最终没有正计数位置、或裁剪后没有可写的 profile；按需指令边界失败（5.7.2 第 6 条）；输入格式错误；perf 调用失败；报告写入或关闭失败；profile 写入或提交失败。
2. 输出的提交顺序：
   - IP 模式先验证输出路径，拒绝 profile 与报告指向同一文件（含路径别名），`--output` 为标准输出时报错；
   - profile 写入目标目录内的临时文件。IP 模式自己打开该文件的 `raw_fd_ostream`，交给现有的 `SampleProfileWriter::create(std::unique_ptr<raw_ostream> &, Format)` 创建 writer，流由 writer 持有，经 `getOutputStream()` 访问（`SampleProfWriter.h:115–126`），不改公共库接口。自建 writer 时复现现有写出路径中仍然适用的行为：按格式使用与 `create(StringRef)` 相同的打开标志（binary/extbinary 用 `OF_None`，text 用 `OF_TextWithCRLF`，`SampleProfWriter.cpp:942–945`）；临时文件必须是可定位的普通文件（extbinary 写节头表时把流转为 `raw_pwrite_stream`，`:825–826`）；复现 `--use-md5` 的设置与"非 extbinary 时忽略"的告警（`L/ProfileGenerator.cpp:181–187`）；`--format=gcc` 时 writer 创建返回错误，记 `failure_stage=write`（`SampleProfWriter.cpp:976–977`）。该 `create` 重载在头文件中注明"For testing"，在生产路径使用的理由在 RFC 或代码评审时说明；
   - `SampleProfileWriter::write()` 返回成功不表示数据已落盘：它不做 flush/close 检查（`SampleProfWriter.cpp:156–163`），而 `raw_fd_ostream` 在析构时才发现错误并直接调用 `reportFatalUsageError`（`raw_ostream.cpp:655–678`），会绕过本契约。因此序列化完成后，显式 flush 并 close 临时文件、检查 `has_error()`，记录错误后调用 `clear_error()`，再销毁流与 writer；
   - 完成解析、加载、生成、profile 序列化及流关闭检查、报告写入与关闭检查之后，最后把临时文件改名为 `--output`；提交后不再执行会使退出码变为非 0 的可失败操作；
   - 任一步失败都删除临时文件，`--output` 不生成、已有文件不被覆盖；profile 提交失败时，尽力把报告改为失败；报告无法更新时在 stderr 说明。
   - 不承诺两个文件在进程崩溃时的原子提交。非 0 退出不得被解释为可使用新 profile。
3. 库内退出的兜底报告：
   - 问题：`ProfiledBinary` 内部大量使用 `unwrapOrError`，出错时经 `exitWithError` 直接 `::exit`（`L/ErrorHandling.h:21–46`）。这不只发生在加载阶段：例如 `ProfiledBinary::symbolize()` 用 `unwrapOrError` 取 `symbolizeInlinedCode()` 的结果（`L/ProfiledBinary.cpp:1065–1073`），而符号化器在第一次查询时才打开 `--debug-binary`，调试文件打不开或 DWARF 解析出错会在生成阶段才暴露。
   - 做法：IP 模式在进入 IP 流程时注册一个回调，直到最终提交（改名）完成才注销；IP 路径维护一个"当前阶段"变量（`load`、`parse`、`identity`、`generate`、`boundary`、`write`、`commit`），每进入一个阶段即更新。`exitWithError` 调用回调，回调按当前阶段写出 `failure_stage` 与错误信息的失败报告，删除临时文件，然后照常退出。
   - 回调只触发一次、不可重入；回调自身写报告失败时只向 stderr 追加说明，不再次进入同一回调。
   - IP 路径自己的代码一律显式返回错误并记录阶段，不调用 `exitWithError`；IP 路径也不调用现有 writer 的创建与写出函数（它们同样经 `exitWithError` 退出，`L/ProfileGenerator.cpp:162–179`）。回调只是 `ProfiledBinary` 等共享代码内部退出时的兜底。
   - 不采用"为 IP 路径另写一个不经 `unwrapOrError` 的符号化包装函数"的做法：它只能覆盖符号化这一处，`ProfiledBinary` 中其他经 `unwrapOrError` 的路径仍会绕过契约，而把帧转换逻辑抽出共用又要改共享代码。回调方式覆盖全部库内退出，且不改共享代码。
   - 回调只在 IP 模式下注册，LBR 路径的错误行为与 writer 路径不变（C1）。不承诺覆盖 LLVM 库内部的 `report_fatal_error`。IP 模式下 `main` 先解析输入与身份前置检查，再构造 `ProfiledBinary`（4.3 第 5 条）。崩溃或磁盘不可写时，不承诺一定有报告。

> 增补：5.6.3 的输出路径冲突、失败时旧文件的处理、测试注入选项与失败阶段测试另见附录 G.1.2、G.1.3、G.1.7。

### 5.7 架构支持

#### 5.7.1 支持矩阵

| 目标 | 要求 | 验证 |
|---|---|---|
| aarch64 | ELF64 小端；PIE、共享库、多个可执行 PT_LOAD 且 `p_offset ≠ p_vaddr`；4K/16K/64K 对齐（离线 lit）；指令定长 4 字节；按需功能要求可用的映射符号（5.7.2；Tizen debuginfo 是否保留待确认） | 格式与地址换算已在 RPi5 核对（09 报告）；评估数据用按第 9 节要求重新构建的库重新采集 |
| armv7l Thumb-2（LLVM 镜像默认） | ELF32；符号化计数（`sum`、`max`）无额外条件；`avg`、`sampled-functions` 补零、`prev-inst` skid 要求可用的映射符号（5.7.2） | RPi4 新镜像，cycles；评估用按第 9 节要求构建的库（含 `-mthumb`，与镜像一致） |
| armv7l A32 | ELF32；`$a` 范围定长 4 字节；`$d` literal pool 不计为指令，也不作为 skid 回退目标；按需功能要求可用的映射符号 | lit：A32 构建（`-marm`）与 ARM/Thumb 混合构建 |
| vmlinux | 第一批只识别并统计内核样本，不生成 profile。原因：6.12 内核没有 `AUTOFDO_CLANG`，内核只在 `toolchain_is clang` 时才用 clang 构建（`linux-rpi.spec:165–169`），第一批没有可验证的消费端。生成移到第二批（6.1） | 合成输入中包含内核样本 |

#### 5.7.2 指令边界的按需枚举

1. 范围：只对有样本的函数，在其 DWARF 区间内进行；只在 `avg`、`sampled-functions` 补零或 `prev-inst` skid 被启用时执行。`sum`、`max` 的符号化计数不需要边界，不受本节条件限制。
2. 前提：可用的映射符号。
   - 映射符号来自 `--binary` 或 `--debug-binary` 的 `.symtab`。名字为短名，或短名后接 `.` 与任意合法符号后缀的长形式（后缀不限于数字，如 `$t.1`、`$t.hot`、`$d.literal`；Arm ELF ABI 的 mapping symbols 一节）。EM_ARM 识别 `$a`、`$t`、`$d`；AArch64 识别 `$x`、`$d`。结合 ELF 符号类型（STT_NOTYPE）、绑定（局部）与所属节识别，名字相符但属性不符的符号不当作映射符号。
   - 板上运行文件已 strip，映射符号需由调试文件提供。armv7l 的 Tizen debuginfo 已确认保留映射符号（07 报告第 1 节；08 报告中调试文件的 `$t` 为 5883 个，比 07 多 1 个，只说明映射符号保留，不说明边界已重新验证）。aarch64 的 Tizen debuginfo 是否保留 `$x`/`$d` 尚未在 Tizen 构建上确认（评审在 clang 直接构建的 aarch64 产物上实测有 `$x`/`$d`），列入第 10 节步骤 1 的非 ★ 项；它只影响 aarch64 上按需功能是否可用，不影响本节规则。
   - 没有可用映射符号的二进制（EM_ARM 与 AArch64 都一样），不支持按需功能：启用即整次运行失败（第 6 条）。理由：只凭"能解码成功"无法证明区间内没有数据——literal pool、内联的 TBB/TBH 跳转表可能恰好解码为合法指令；AArch64 也不能仅因指令定长就把未知范围全部视为代码。
3. 映射状态：
   - 映射符号按所属节分组。所属节按节名与地址范围在 `--binary` 与 `--debug-binary` 之间对应，不依赖两份文件的节索引相同；对应不上时按第 6 条失败。
   - 每个枚举区间的起始状态取同一节内、地址不大于区间起点的最近映射符号（包括恰好位于起点的符号；映射状态可能在函数起点之前就已建立）。映射状态不跨节延续：同一节内找不到时按第 6 条失败（clang 在每个代码节的开头都放置映射符号，评审在 aarch64 `.o` 中实测 `$x` 位于节偏移 0）。
   - 区间内按映射符号切换 A32（`$a`）、Thumb（`$t`）、A64（`$x`）与数据（`$d`）。同一地址出现状态不同的映射符号时，按第 6 条失败。
   - 查询方式与 llvm-objdump 一致：按节保存映射，按 `<= 地址` 查找（`llvm-objdump.cpp:1453–1464`、`:1816–1835`）；07 报告的原型也按节隔离。
4. 边界规则（不依赖子目标）：
   - 映射区间：先按映射符号把每个节划分为半开区间 `[m_i, m_{i+1})`，每个区间只有一种状态（`$a`、`$t`、`$x` 或 `$d`），区间的起点 m 是该映射符号的地址。再把每个 DWARF 函数区间与这些映射区间求交，按交集逐段处理。
   - `$d` 交集：作为数据排除，不枚举、不计入 `n(k)`，也不作为 skid 回退目标。
   - `$a`、`$x` 交集（A32、A64）：交集起点必须 4 字节对齐，且与锚点 m 的距离为 4 的倍数；之后按 4 字节步进。否则按第 6 条失败。
   - `$t` 交集（Thumb）：以覆盖该交集的当前 `$t` 映射区间起点 m 为锚点，从 m 按长度规则顺序步进，恰好到达交集起点才成立；步进越过交集起点（起点落在 32 位指令中间）按第 6 条失败。不得从更早的映射区间跨过 `$d` 或另一种 ISA 连续步进。指令长度按架构编码规则确定：第一个半字的 bits[15:11] 为 `0b11101`、`0b11110` 或 `0b11111` 时为 32 位（即第一个半字不小于 `0xE800`），否则为 16 位（Arm 架构参考手册的 Thumb 编码规则；LLVM 的 `ARMDisassembler::suggestBytesToSkip()` 用同样的判断，`ARMDisassembler.cpp:6138–6163`）。IT 块不改变指令长度。第一批 armv7l 限定 ELF32 小端，半字按目标的指令字节序读取。
   - 交集末端不得截断一条指令：最后一条指令必须恰好结束在交集末端，否则按第 6 条失败。
   - 为证明起点而从锚点 m 读取的、DWARF 区间之外的前缀，只用于证明，不计入 `n(k)`、补零位置或 profile。为避免长距离步进，实现可以缓存每个 `$t` 映射区间内已验证的边界。
   - DWARF 区间的起点（包括函数的第二段及以后的不连续区间）因此不能直接当作已知指令起点，任意偶地址也不能代替证明。
   - 指令字节一律从 `--binary` 读取（调试文件中代码节为 NOBITS）。
5. MCDisassembler 只作交叉核对（可选，测试与诊断用）：子目标按"`--debug-binary` 的 `.ARM.attributes` → `--binary` 的 `.ARM.attributes` → 固定的 `thumbv7a` + `neon` + `vfp3`"的顺序取得，所用来源写入报告；不得使用不带版本的 `arm`/`thumb`（4.1 第 4 条）。
6. 失败处理：任一被枚举函数的边界无法确定（缺映射符号、同一节内没有起始状态、同址映射状态冲突、节在两份文件间对应不上、DWARF 区间起点不是已知指令起点、A32/A64 起点不对齐、长度规则步进越过交集末端等），整次运行失败（`failure_stage=boundary`），报告列出全部失败函数及原因；不跳过该函数，也不改用其他聚合方式写出。调用方可以显式改用不需要边界的 `sum`/`max` 并关闭补零与 skid 重新运行。
7. 采样 IP 与符号地址：
   - 采样 IP 本身不带 bit0：内核的 `perf_instruction_pointer` 直接返回 `ARM_pc`，Thumb 状态在 CPSR 的 T 位。不得对样本地址做 Thumb 位处理。
   - 带 bit0 的是符号表中 Thumb STT_FUNC 的 `st_value`。经 LLVM API 读到的地址已清除 bit0（`ELFObjectFile.h:615–618`），不得用读取到的地址反推 ISA；函数入口的 ISA 用 `getSymbolFlags()` 给出的 `SF_Thumb` 标志判定（`ELFObjectFile.h:803–815`；`SHN_ABS` 符号不清位，:611–612，排除在判定之外）。该标志只用于报告中的 `isa` 统计，不能用来确定函数内部的指令边界；没有符号条目的函数（例如 `.dynsym` 之外的内部函数）计入"无法判定"。
   - 直接读取原始 `st_value` 的核对脚本必须自行清除 Thumb 位（05 报告 B.3：清除前 3/7、103/219 命中，清除后全部命中）。
   - DWARF 中 Thumb 函数低地址的表示方式由 lit 用例核对。
8. 验收：对 lit 中的 A32、Thumb、混合二进制，以及评估用的 libavcodec 热点函数，把枚举得到的指令边界与 `llvm-objdump --triple=thumbv7a -d`（A32 用 `armv7a`，带映射符号）的结果逐条比对；另有人工已知边界的 golden fixture，不只与共享同一解码器的 objdump 相互印证。07 报告在 20 个最大 Thumb 函数上的 132,859 个起点支持长度规则与 `$d` 排除；它用的是符号表的函数区间，不能代替任意 DWARF 子区间的测试，这部分由 5.10 的用例覆盖。

> 增补：5.7.2 中 DWARF 区间起点为奇数的 Thumb 函数另见附录 G.1.8；同址映射冲突的报告地址另见附录 G.1.10。

### 5.8 质量评估方法（统计质量）

评估分三层：A. 转换正确性（golden fixture，见 5.10）；B. 统计质量（本节）；C. 优化收益（5.9）。三层不能互相代替。本节的判据属于第二阶段冻结内容。

1. 插桩参考的性质：`.profdata` 本身不是逐块真值表。IR 中的 `branch_weights` 按每条终结指令单独决定缩放因子后写入（`PGOInstrumentation.cpp:2408–2419`）：该终结指令的最大边计数小于 UINT32_MAX 时因子为 1，即写入原始边计数，否则按 `MaxCount / UINT32_MAX + 1` 缩放（`llvm/include/llvm/IR/ProfDataUtils.h:172–176`、`ProfDataUtils.cpp:329–339`）。同一条终结指令内的相对概率总可以比较；被缩放的终结指令无法从 IR 识别出缩放因子，所以跨终结指令的权重之和只作描述性统计，不作执行覆盖率，也不能直接得到全程序归一化的块计数。第二阶段如需执行加权的分支指标，先证明所选分支都未被缩放（例如与 BFI 或 profdata 计数对照）再使用。
2. IR 层比较（局部分支概率）：
   - 同一源码、同一组 flags（第 9 节），分别用 `-fprofile-use=<插桩 profdata>` 和 `-fprofile-sample-use=<IP profile>` 编译，加 `-mllvm -print-after=pgo-instr-use` 或 `-mllvm -print-after=sample-profile`（`PassRegistry.def:133`、`:161`），以及 `-mllvm -disable-sample-loader-inlining`（`SampleProfile.cpp:195–200`），导出刚完成标注的 IR。
   - 插桩参考构建的生成与使用两侧都加 `-mllvm -disable-preinline`：插桩 PGO 在打计数前会做一次预内联（`PassBuilderPipelines.cpp:1240–1242`，生成与使用两侧都跑），sample 侧没有这一步。关闭预内联只减少差异，不表示两个 pass 边界处的 IR 已经相同（两者之间还有 IPSCCP、GlobalOpt、InstCombine、SimplifyCFG 等，`PassBuilderPipelines.cpp:1149–1153`、`:1188–1209`、`:1240–1249`）。这个参考构建只用于本节；5.9 中的插桩 PGO 对照组仍用正常 flags。
   - 候选改进（第 10 节步骤 1 验证，效果未核实）：两侧都在两个 pass 之后的同一位置转储（例如 `-mllvm -print-before=inline`），使两侧经过相同的清理 pass；若能消除 switch/br 的形态差异，即改用这一转储点。
3. 匹配与语义校验：
   - 候选：按"函数 + 终结指令的完整 DILocation（含作用域、内联链与 discriminator）"产生候选对；重复键不配对。DILocation 只用于产生候选，不证明语义相同。
   - 操作数等价（两侧是不同的模块，SSA 名字不可比）：叶子只接受同一函数中同序号的参数，以及类型与值都相同的普通常量。定义指令只在已支持的无副作用运算白名单中比较：递归比较 opcode、类型、操作数个数、相关语义标志（如 `nsw`/`nuw`/`exact`、比较谓词）与各个操作数，递归深度设上限。只比较"一层 opcode、类型与 DILocation"不够：`and i32 %x, 1` 与 `and i32 %x, 2` 的这三项都可以相同，后接 `icmp eq ..., 0` 时含义却相反（LLVM 自身判断指令相同时也比较操作数与语义状态，`Instruction.cpp:962–985`）。DILocation 只用于产生候选，不作为值等价的证明。`undef`/`poison`、内存读取、调用、未支持的 PHI、超过递归上限等情形，没有额外证明时一律判为 `semantic_unverified`。
   - 条件 br：两侧的条件必须可以规范化对比，即谓词相同、操作数类型相同且操作数按上一条等价。条件相同则按 true/false 配对；谓词互为取反（如 `icmp eq` 与 `icmp ne`）且操作数等价，则交换 true/false 配对。另外校验每个后继块中第一条带 DILocation 的指令位置与配对一致；同一终结指令的两个后继首位置相同、或某个后继块中没有带位置的指令时，判为 `semantic_unverified`。
   - switch：先校验选择值的整数类型与位宽相同、且选择值按上一条等价（相同的 case 集合不代表相同的条件，`switch(x)` 与 `switch(y)` 可以有相同的位置与 case 集合；选择值是 switch 语义的独立组成部分，`Instructions.h:3391–3405`）；再按带位宽的 case 常量与 default 配对，不按文本中的后继序号配对，并校验后继的对应关系（同上，用后继首位置）。选择值、case 集合或后继关系无法确认时判为 `semantic_unverified`。同为 default 只表示语法角色相同，不单独证明语义一致。
   - 形态不同（如一侧 switch、一侧 br 链）或无法建立明确一一对应的，一律判为 `semantic_unverified`，排除在指标之外并单独计数。第一版只接受能建立明确一一对应的子集。
   - 缺少 `branch_weights`：默认视为 `unknown` 并排除，仅有 `function_entry_count` 不足以补零。只有取得该块恢复计数为 0 的独立证据时，才记为零计数分支。区分 PGO 计数权重与 `llvm.expect` 等产生的预期权重（带 `expected` 标记的不参与）。存在 profile 部分忽略、未匹配或相关诊断的函数整体排除。参考总权重为 0 的分支没有可比较的条件概率，不进入概率误差的分母。
4. 结构覆盖（v0.8 修订，原 95% 门槛取消）：分别报告两侧条件终结指令中通过严格匹配的比例与未匹配原因，作为每轮评估报告的固定栏目，不再作为门槛。依据：在本次 spike、`pgo-instr-use` 转储点与当前匹配器实现下，插桩参考与它自身比较，Thumb、A32 各 22 条条件终结指令中只有 3 条可进入严格比较（13.64%），未通过的原因为内存读取 6、PHI 5、谓词 5、调用 1、类型 1、无权重 1（`docs/profgen/eval/quality_round1.md`、`docs/profgen/impl/evidence/16/02_reference_structure.json`）。这 3 条可以报告局部概率误差，但不足以代表整体代码质量，不能作为主指标；该比例也不外推为其他负载或其他匹配器实现的普遍上限。第 3 条的语义校验规则不放宽；跨终结指令的 `branch_weights` 之和仍只作描述，不称为执行次数。参考自比的结果在结果文件中标记为 `reference_self_check`，不进入配置间误差矩阵。
5. 指标（v1.1）：
   - 参考：插桩覆盖构建（C 构建，定义见附录 G.2.1）在同一训练输入上的逐行执行计数。行计数直接取 `llvm-cov export -format=lcov` 的 `DA` 记录（导出代码在 `llvm/tools/llvm-cov/CoverageExporterLcov.cpp:88–93`），它按 llvm-cov 的行统计逻辑得出：起止位置与类型都相同的区域实例先求和，再取在该行起始的区域计数的最大值（`llvm/lib/ProfileData/Coverage/CoverageMapping.cpp:1342–1373`、`:1584–1626`）。不从 JSON 的 segment 自行推算行计数；函数执行计数取 `FNDA`。
   - 参考侧的源函数：覆盖 JSON 的函数记录（字段见 `llvm/tools/llvm-cov/CoverageExporterJson.cpp:327–338`，没有现成的函数行范围字段）按"规范化定义文件、去掉 `<文件>:` 前缀与 `.__uniq.<数字>` 后缀后的名字、起始行"合并为一个源函数：同一个 static 或 inline 定义在多个编译单元中的副本是同一个源函数（覆盖侧名字的构成见 `llvm/lib/ProfileData/InstrProf.cpp:303`）。这与两侧的合并方式一致：lcov 的 `DA` 已对各副本中起止位置与类型相同的区域求和，sample 侧跨内联上下文求和也合并各副本。
     - 主文件、起始行与行范围：主文件按 LLVM `findMainViewFileID` 的规则确定（本构建中均为 FileID 0，脚本仍按规则核对）。起始行 = 主文件中代码区域的最小起始行；行范围 = 这些区域的 [最小起始行, 最大结束行]（闭区间）。这里的起始行只用于覆盖记录之间的分组，不等于 DWARF 的声明行。`findMainViewFileID` 返回空的覆盖记录不进入任何源函数，单独报告其 FNDA。宏展开区域（按覆盖映射的区域类型与 FileID 识别，不按物理文件名整体排除）不计入任何函数的行范围，只属于宏展开区域的行不进入 U（DWARF 把宏展开的代码记在调用处的行上，这些行在 sample 侧无法对齐）。
     - 歧义：合并之后，同一行仍落在多个已执行（`FNDA` > 0）源函数的行范围内时，该行标为歧义；未执行的源函数对 `DA` 的贡献为 0，不参与歧义判定。
     - 已知代价：各副本的计数无法区分（`DA` 本来也不区分）；同一模板文件的多个实例中，未执行实例的行归到已执行的实例。
   - 跨侧的源函数对应（对应表，登记前只用 ELF、调试文件与参考数据生成）：
     - DWARF 函数（subprogram 以及 inlined_subroutine 的抽象源）按"规范化 decl_file + 去掉 `.__uniq.<数字>` 后缀的名字"对应参考侧源函数；名字取 LLVM 22.1.8 `DWARFDie::getSubroutineName(DINameKind::LinkageName)` 的结果：按 `findRecursively` 的实际遍历，在每个访问到的 DIE 上先查 `DW_AT_MIPS_linkage_name`、再查 `DW_AT_linkage_name`，沿 abstract origin、specification 与 signature 递归，最后按接口规则回退到短名 `DW_AT_name`（`llvm/lib/DebugInfo/DWARF/DWARFDie.cpp:327`、`:341`、`:530`、`:548–552`）；实现复用该接口或完整复现其规则。本构建的外部 C 函数如 `ff_h264_decode_mb_cabac` 没有 linkage name，按此回退。不要求起始行相等：DWARF 的 decl_line（工具的 StartLine，基线 `L/ProfiledBinary.cpp:1087`）是声明行，参考侧起始行是函数体第一个代码区域，FFmpeg 的左花括号另起一行，二者通常不同（评审在正式 S 的调试信息上核对，4 个热点函数中 3 个不相等）。
     - 同一（文件、名字）只有一个参考源函数候选时，须同时满足两项才建立对应：① 定义身份——候选在 C 构建中的定义声明位置（规范化 decl_file 与 decl_line，取自 C 构建的调试信息；C 构建没有调试信息时，用同一源码、同一预处理定义的 clang AST 导出）与被采样侧 DWARF 的声明位置相同；这里比较的是两侧的定义声明位置，不是声明行与覆盖区域起始行；② 行范围一致——该 DWARF 函数以自身为叶子帧、文件等于其 decl_file 的全部行表行号（行号 0 除外）都落在 [min(decl_line, 候选起始行), 候选结束行] 内（容许签名所在的行）。筛选后的行号集合为空时 ② 不算通过。行范围包含只是一致性证据，不单独证明身份：条件编译下，错误定义的行号也可能全部落在候选范围内（附录 N.2）。任一项不满足或证据不足时不自动建立对应，按多候选的规则处理（显式裁决，或记 `identity_ambiguous`）；裁决证据与所选编译变体不一致时拒绝登记。登记前报告未通过检查的单候选函数个数及其参考计数。② 的行集合还包括直接子 inlined_subroutine（含位于 lexical block 之下者）在 decl_file 中行号非 0 的调用行。无键实例：对完整身份清单的全部顶层函数（不限于映射范围），在全部已证明的指令起点上运行与正式工具相同的键生成代码，枚举与符号化全部成功、且没有任何被接受的键以该实例为叶子帧或上下文帧；所在顶层函数边界无法证明、枚举不完整、符号化失败或缺少键证明记录时，不得认定为无键实例。无键实例满足豁免条件时不参与组判定，组判定以其余实例为准；组内全部为豁免的无键实例时，参考行记为 `no_key_line`（计入损失），不计入 `unmatched_in_elf`（裁决 4，附录 O.2.4）。有多个候选时默认记 `identity_ambiguous`：声明行距离只用于展示候选，不作为消歧证据（条件编译下两个同名定义可以声明行相同、函数体起点不同）；只有登记前的静态裁决能以源码、编译变体、DWARF 位置与覆盖区域证据唯一证明定义身份时，才建立对应，证据随裁决表保存。`identity_ambiguous` 是已登记的结论：它的键在映射表中，值保存候选集合与排除标志，不伪造唯一的源函数身份；全部候选的相关参考行取并集，进入排除清单；涉及的参考计数（按 U 第 ③ 项的口径）超过 ③ 分母的 1% 时，该对象评估不可用。
     - 未插桩：按编译单元判定，且须有正面证据。先查参考候选：已有参考候选的函数（包括外部 CU 中能对应已执行参考函数的内联体）不得按 CU 归为 `not_instrumented`。没有候选的函数，只有当其 CU 的源文件与 `DW_AT_producer` 字段完整、源文件不在覆盖导出的文件表中、producer 不是评估所用的 clang，并且该 CU 命中登记的外部 CU 清单（带构建或链接来源证据）时，才记为 `not_instrumented`（本构建预期为 libgcc 的 5 个 GNU AS CU 与 5 个 GNU C CU，例如 `__divsi3`、`__aeabi_*`；只看语言不够，`libgcc2.c` 是 C）。字段缺失、解析失败或路径规范化失败都保留为没有结论。源文件在覆盖导出中、却找不到同名参考源函数的 DWARF 函数不属于此类，按下项记为没有结论。登记前报告 `not_instrumented` 的 CU 清单与 producer 分布。内联树只含 `not_instrumented` 与参考侧未执行函数的顶层组属于 `known_out_of_scope`；名字相同而文件不同的情形不属于此类，由裁决表决定。
     - 登记前裁决给出的结论状态：`system_header_no_reference`（系统头中的函数，参考侧因 clang 默认不为系统头生成覆盖映射而没有候选；裁决 1，附录 O.2.1）；`macro_generated_function`（整个函数由宏展开生成，以编译器 AST 与 token 证据证明身份，执行与否按其 FNDA；裁决 2，附录 O.2.2）。两者的参考行都不进入 U；是否属于 C 只按第 ③ 项的见证规则判定，不随这两种结论变化，属于 C 时计为损失并单列原因。条目先按下文的顶层组分类顺序处理：已证明属于 `known_out_of_scope` 的组记为范围外；位于映射范围内、命中已登记键且值为上述状态的条目，才计入"已对齐但不在 U 内"，分别单列原因；特殊状态不使未知名字或未登记键绕过未对齐检查。
     - 对应表覆盖完整性（登记前静态检查）：先独立于映射范围，枚举被采样 ELF 中全部有代码、可产生 profile 的 DWARF 函数（全部 subprogram 与 inlined_subroutine 的抽象源，含优化克隆），建立完整身份清单；在生成映射范围之前，清单中的每一项都必须在对应表中有一个封闭枚举内的结论——对应到已执行的参考源函数、对应到参考侧未执行的源函数、`identity_ambiguous`、`not_instrumented`、`system_header_no_reference`、`macro_generated_function`（附录 O.2），或裁决表中的其他结论；`pending`、主文件缺失等状态不是结论。任一函数没有结论时登记准备失败，不在 RUN 级降级处理；未决项不因未进入映射范围而免于检查。映射范围由这些结论导出，`known_out_of_scope` 只能由组内全部函数的结论推出。裁决表的结果同样必须落入预先定义、具有明确处理语义的状态枚举。
     - 对应完整性：每个已执行的参考源函数，要么对应到被采样 ELF 中至少一个 DWARF 实例，要么以 `unmatched_in_elf` 列出并报告其参考计数；`unmatched_in_elf` 涉及的参考计数（按 U 第 ③ 项的口径）超过 ③ 分母的 1% 时，该对象评估不可用。另列出"名字去后缀后与某个已执行参考源函数相同、却不在映射范围内"的全部 ELF 顶层函数，逐个裁决后随修订 3 登记（裁决表）。
     - 对应表保存覆盖原名、合并后的源函数身份、DWARF 函数身份与声明位置，与映射表一起登记 SHA。原始 profile 函数名与用于参考匹配的去后缀名字分别保存；条目分类与名字闭包只用原始名字。
   - 映射表（sample 侧对齐）：映射表只由固定的被采样 ELF、匹配的调试文件与覆盖参考决定，不读取任何 RUN 的样本。
     - 函数名：按工具实际写出的形式，即符号化器给出的 linkage name，不 demangle，不做 canonical 化，保留 `.__uniq.` 等后缀（补丁树 `15a5ec3f` 的 `L/ProfiledBinary.cpp:1206`）。写 profile 的符号化路径 `L/ProfiledBinary.h:620` 把 `SymbolizerOpts.UseSymbolTable` 作为 UseCanonicalFnName 传入，该值在 `getSymbolizerOpts` 中固定为 false（`L/ProfiledBinary.cpp:1212`），`:1297–1298` 的 canonical 化不执行；`--show-canonical-fname` 只影响反汇编显示（`:632`、`:670`），并在 IP 模式下被拒绝（`llvm-profgen.cpp:249`）。与参考侧的对应按上一项的对应表进行。
     - 范围：被采样 ELF 中，内联树（DWARF 的 subprogram 与 inlined_subroutine）中有任一函数按对应表对应到参考侧执行过的源函数，或为候选集合中含已执行参考源函数的 `identity_ambiguous` 的全部顶层函数；再按工具的函数身份取闭包：与其中任一顶层函数同名的全部 ELF 顶层函数（工具按名字合并 DWARF 函数，`L/ProfiledBinary.cpp:1080–1084`，补丁树），即使其源函数在参考侧没有执行，也纳入映射与歧义分析。下称"映射范围"。闭包只用 ELF、调试信息与固定的名字规则建立。
     - 地址：只取按 5.7.2 规则证明的指令起点，不把任意字节地址当作样本位置。映射范围内某个函数的边界无法证明时，按工具顶层 profile 身份的完整合并组（同名的全部顶层函数）处理：该组登记为 `boundary_unavailable`，静态确定它可能贡献的全部参考行 B 并整行排除；无法保守确定 B，或不能把该组与可评价的组区分时，该对象评估不可用。边界排除比例 = Σ_{l∈B∩C} R(l) ÷ Σ_{l∈C} R(l)（C、R 见 U 的第 ③ 项），超过 1% 时该对象评估不可用；不用函数入口计数 FNDA 代替逐行计数。边界排除组在登记前静态锁定，不依据任何 RUN 的样本。需要边界的配置（`prev-inst`、`avg`）在该组有样本时按冻结契约整次转换失败，按第 6 条记为转换失败的缺失；不需要边界的配置把该组条目归为 `boundary_unavailable`。
     - 键：对每个地址逐个符号化，按工具写出 profile 的方式计算"（顶层函数名、完整内联上下文、行偏移、discriminator）"，复现以下规则：调用点与行偏移取 `(Line − StartLine) & 0xffff`（基线 `L/ProfiledBinary.cpp:1087`）；discriminator 取 `getBaseDiscriminator()` 的结果（定义在 `L/ProfileGenerator.h:59–62`，使用点如 `L/ProfileGenerator.cpp:653`），FS discriminator 按工具实际写出的形式；叶子帧行号为 0 的地址不产生键，任一非叶子帧行号为 0 的地址整体不产生键（G.1.9；补丁树 `15a5ec3f` 的 `L/ProfiledBinary.cpp:1278–1288`，基线中没有这段代码）；奇数 DWARF 起点按 G.1.8 规范化并做别名查询。
     - 值：键映射到"（源函数、规范化源文件路径、绝对行号、discriminator）"，源函数按上面的合并规则标识；路径规范化规则在修订 3 中固定，不只按文件 basename 匹配。
     - 不用"起始行 + 偏移"的算术还原：偏移已对 2¹⁶ 取模，profile 也不记录源文件，函数体内 `#include` 的代码、同名函数合并、偏移碰撞都无法由算术还原。
     - 这是评估脚本的预处理要求，不改变工具"只按需枚举有样本函数"的冻结规则；预处理无法完成时报告评估不可用，不扩大工具的失败条件。
   - 歧义：同一个键对应多个源位置时为歧义键。歧义键可能贡献的全部源位置所在的行都标为"受影响"，整行移出 U，不只删除该键而保留该行的完整参考计数。歧义键、受影响行、参考侧的歧义行、`identity_ambiguous` 涉及的行与 `boundary_unavailable` 组的行合成一份排除清单。
   - 条目分类（每个 RUN、每个配置，逐条 body 记录，只用原始 profile 函数名，按以下顺序归类）：
     - `boundary_unavailable`：顶层函数属于登记的边界排除组 → 单独报告，不进入指标，不算未对齐；
     - `unknown_name`：顶层函数名不等于被采样 ELF 中任何 DWARF 顶层函数按上述规则得到的名字 → 未对齐；
     - `reference_unresolved`：名字属于 ELF，但该组没有有效的登记结论（全量的覆盖完整性检查通过后不应出现；出现即说明登记产物有误）→ 未对齐；`identity_ambiguous` 不属于此类：它的已登记键命中时，条目计入"已对齐但不在 U 内"，同一组中不在映射表里的键仍为 `unmapped_key`；
     - `known_out_of_scope`：名字属于 ELF，且对应表已证明该组不包含参考侧执行过的函数（含只由 `not_instrumented`、`system_header_no_reference` 与参考侧未执行函数（包括 FNDA = 0 的宏生成函数）组成的组；不能证明时不归入此类）→ 范围外，只报告；
     - `unmapped_key`：在映射范围内、但键不在映射表中 → 未对齐。
     - 出现任一未对齐条目（不论计数大小，包括显式 0 条目），该 RUN、该配置的 M1、M2、M2b 无定义，不通过删除这些条目继续判读。未对齐表明输入与映射契约不一致，须调查原因。登记前以合成全地址核对与"地址 → 键 → 源位置"关系核对（附录 Q.5 第 5 项）作为这一规则的前提；一份真实 profile 上的键全部命中，不能证明所有可能的键都已验证。补零配置写出的显式 0 键不在合成全地址核对的覆盖范围内；补零配置不进入质量指标（第 9 条），将来如要对补零配置计算质量指标，须先扩展该核对并作为协议变更登记。
     - 另报告未对齐、范围外、`boundary_unavailable`、"已对齐但不在 U 内"四类各自的 body 计数之和占同一份 profile 全部 body 计数之和的比例。每条 body 记录只计一次，不计 head、函数 total 或父节点的累计；分母为 0 时记为 not_applicable。"已对齐但不在 U 内"按原因分列：值中的源函数为未执行源函数、却落在已执行源函数行上的键（见下项）；`identity_ambiguous`；系统头（裁决 1）；宏生成的函数（裁决 2）；排除清单中的其他行。未对齐比例超过 1% 另标"高占比对齐失败"。这些比例只作描述，不称为 usable 样本的丢失比例，也不用于跨聚合方式比较。
   - 行计数的合并：sample 侧每行的计数 S(line) 在主分析中固定为 max_d Σ_context count(context, line, d)，即先对同一源位置跨内联上下文求和，再在同一行的不同 discriminator 之间取最大。这是预先选定的行热度代理口径，不宣称与 llvm-cov 的区域汇总语义等价：llvm-cov 合并的是起止位置与类型相同的区域，不按 discriminator 合并；discriminator 由函数内的文件、行与基本块分配（`llvm/lib/Transforms/Utils/AddDiscriminators.cpp:140–188`），它与覆盖区域是否一一对应没有证明。另登记两个敏感性口径，使用同一个 U：S_alt = Σ_context max_d count(context, line, d)；S_sum = Σ_context Σ_d count(context, line, d)。任一敏感性口径改变了某个比较的等价结论，或使差值的点估计改变符号时，该比较报告为"合并口径敏感"，不选择较有利的口径作为最终结果。三个口径都只汇总"值中的源函数 = 该行所属源函数"的键；值中的源函数为未执行源函数、却落在已执行源函数行上的键（例如同一模板文件的未执行实例），计入"已对齐但不在 U 内"。
   - 比较总体 U：插桩侧在训练输入上执行过（`FNDA` > 0）的源函数（按上面的合并规则）中，具有可执行覆盖映射、属于第 ③ 项的行集合 C、在映射表中至少有一个键与之唯一对应、并且不在排除清单中的源码行，包含参考计数为 0 的行。U 只由被采样 ELF、调试文件与参考数据决定：sample 侧完全没有条目的函数，其行是否属于 U 同样按映射表判定，与样本有无无关。U 按构建、ISA、输入分别生成，与映射表、排除清单、各函数权重一起在登记修订 3 之前生成，并登记各自的 SHA-256（附录 G.3）。在 U 内，sample 侧缺少条目的行按"零次观测"计入（只用于评估，不改变生产 profile 中"缺失不等于明确冷代码"的约定）。分别报告：① U 的行数占 C 的行数的比例；② U 中参考计数大于 0 的行占全部已覆盖行的比例；③ U 内参考计数之和 ÷ Σ_{l∈C} R(l)：C₀ 为已执行源函数行范围（主文件代码区域推导）内的全部可执行行，在歧义、边界与对齐排除之前建立，按"文件、行"去重，R(l) 取该行的 `DA`；C₀ 限定于本方案可评价的主文件代码行，不含只属于宏展开区域的行，这是评价域的限定，不表示宏内部各行的计数可以由调用行的计数代替；C 为 C₀ 中有行表归属见证的行：在 C 构建或 S 构建的调试 ELF 中，按附录 O.2.3 第 1 项的逐 sequence 区间算法（同一地址取最后一条记录，去掉 `end_sequence` 与零长度区间；前提是同一 CU、同一节的 sequence 互不重叠，生成前自动验证）存在行号非 0、文件与行号即为该行、与带执行属性的节相交且非空的行表区间；这是操作性定义，不逐行证明存在真实指令；不限定该区间属于哪个函数，不使用对应表、映射范围、映射表、边界排除结果、键是否被接受或任何身份结论（裁决 3，附录 O.2.3）；行表取证失败的行记为 `domain_unresolved`，留在 C 中、排除出 U、在两份账本中单列，失败不能定位到具体行时全部未取得见证的 C₀ 行都记为 `domain_unresolved`；任一对象存在 `domain_unresolved` 行时，状态为 `domain_evidence_incomplete`，不得判为可登记，也不得输出质量结论；C₀ 中其余的行记为 `code_free_line`，不进入 ③ 与三个 1% 门槛的分母；分母为 0 时该对象不可评价；③′ U 内参考计数之和 ÷ 覆盖导出全部行的 `DA` 之和（描述性，另报告宏展开文件中行的 `DA` 占比，这部分按设计不进入 U）；④ 上一项"条目分类"中的各类比例（分母是每个 RUN 的 profile body 计数，登记后按 RUN 计算，登记前不计算），以及歧义键数、受影响行数、`identity_ambiguous` 的组数与涉及行数、映射范围内系统头代码与宏生成代码的静态地址数与字节数（这些只用静态产物计算，登记前写入修订 3）。①–③′ 只用参考数据计算，登记前按对象写入修订 3；同时登记 C_dc（C₀ 去掉 `asm_interior`、`structural_line`、`expr_continuation` 三类结构性重复计数的行，C ⊆ C_dc ⊆ C₀）、按 C₀、C_dc、C 三个口径的 ③、代码承载比例 ΣR(C) ÷ ΣR(C₀)、评价域外的不重复参考执行量比例 ΣR(C_dc \ C) ÷ ΣR(C_dc)，以及 `code_free_line` 的结构分类（附录 O.2.3 第 5 项），这些只作描述。任一对象的 ③ 低于 50% 时不登记，先修订本条；50% ≤ ③ < 80% 时，修订 3 须按原因（参考歧义、键歧义、无键行、`boundary_unavailable`、`unmatched_in_elf`、`identity_ambiguous`）分解损失后才能登记；每行保留完整的原因集合，按互斥的原因集合分桶，各桶的 `DA` 之和须等于 ΣR(C) − ΣR(U)，同一行不重复计。不论 ③ 落在哪个区间，修订 3 都登记两份账本：C → U，以及 C₀ → U（多出原因 `code_free_line`；宏生成函数被执行时，其行在两份账本中都带原因 `macro_generated_function`，每行保留完整原因集合、不重复计数）。50% 是预先选定的最低保留率，不证明代表性或对齐正确。③ 是评价域修订后的条件保留率，只衡量固定构建中有行表归属见证的行上的保留率，不表示对齐能力提升；C 相对 C_dc 的收窄是可测量性的限定（叶子帧采样对没有见证的行在构造上恒为 0），不是重复计数的修正，门槛的通过是否依赖这一限定须按登记产物写明（v1.6 规则下 FFmpeg 只做重复计数修正时 ③ 约为 49.9%，附录 P.2）。C 的定义随修订 3 冻结：之后不因 RUN、配置、门槛或结果修改，改变构建须重新生成并登记评价域，任何规则修改都作为新的修订送评审并对全部对象统一适用。
   - M1（主指标，按 n_eff 条件判读）：行级排序一致性。U_f 为源函数 f 在 U 中的行，Spearman 相关系数的并列值取平均秩。函数集合与权重只由参考数据与 U 决定：|U_f| ≥ 5 且参考侧秩方差不为 0 的函数进入 M1，权重 w_f = Σ_{l∈U_f} 参考计数(l)；参考计数恒定的函数不进入，单独报告其行数与参考计数质量。sample 侧秩方差为 0（例如全部为 0）的函数记 0 分，不排除、不重新分配权重；这是评分约定，不是数学上有定义的 Spearman，也不保证任何稀疏化都会使 M1 下降。M1 = Σ w_f·ρ_f ÷ Σ w_f；没有入选函数或 Σ w_f = 0 时 M1 无定义。
     - 有效函数数 n_eff = (Σw)² / Σw² 只由参考数据与 U 计算。没有入选函数或 Σw² = 0 时 n_eff 记为 null（JSON 写 `null`，不写 NaN）；判读时按第 6 条的显式分支处理，不做数值比较。
     - 同时报告按函数等权的中位数，以及参与行门槛取 10 时的 M1（敏感性分析）。
   - M2（主指标）：热点集合重叠。
     - H_ref：T 为 U 内参考计数之和。U 中各行按参考计数降序排列，取最小的 k 使前 k 行的累计计数 c_k 满足 5·c_k ≥ 4·T（整数比较，与 G.1.4 一致）；v 为第 k 行的参考计数，H_ref = U 中参考计数 ≥ v 的全部行，K = |H_ref|。T > 0 时 v > 0，H_ref 不含参考计数为 0 的行。
     - H_s：只从 U 中 sample 计数大于 0 的行里，按 sample 计数降序选取，最多 K 个名额。截断位置上 sample 计数相同的一组正计数行，每行按"剩余名额 ÷ 组内行数"计入部分份额，这等于随机打破 sample 侧并列时重叠数的期望。正计数行不足 K 时，不用零计数行补足。
     - M2 = Σ(H_s 中各行的份额，限 H_ref 内的行) ÷ K，分母始终为 K。U 内 sample 全部为 0 且 K > 0 时 M2 = 0。U 为空或 T = 0 时 M2 与 M2b 都无定义，不记为 0 或 1。
     - 粒度：没有截断并列时，单个 RUN 的 M2 是 1/K 的整数倍；并列份额与跨 RUN 的均值会产生更细的变化。
   - 对象登记表：登记修订 3 之前，只用参考数据与 U，按构建、ISA、输入写成一张表：①–③′、n_eff、K。第 6 条按这张表决定每个对象的判读方式。spike 的 n_eff 按参考数据估算约为 1.3、K 约为 5（评审估算，确切值由脚本给出）。
   - M2b（描述性）：H_ref 中 sample 计数大于 0 的行数 ÷ K。同一批样本在 sum、max、avg 三种聚合方式下正计数集合相同，M2b 不能区分聚合方式，只反映采样覆盖。
   - M3（辅助）：函数级 Spearman（函数总计数）、热点函数覆盖。
   - 敏感性（区域）：只在参考侧"在本行起始的非 gap 区域入口不超过一个"（`LineCoverageStats` 的 `HasMultipleRegions=false`，`CoverageMapping.cpp:1589–1625`）的行上另算一次 M1。这个条件不证明该行只有一个活动区域或一个基本块：从上一行延续下来的区域不计入该字段。标志由覆盖 JSON 的 segments 按同版本 LLVM 的谓词提取，或经 Coverage API 导出；lcov 只提供行计数。
   - 指标的含义与盲区：M1 衡量 sample 行热度与插桩执行热度的排序一致性。行间执行代价不同时排序可以相反（例如执行次数 1、2、3、4、5 而每次代价 100、40、20、10、1，准确的周期计数排序与执行次数完全相反，Spearman 为 −1），所以 M1 不证明周期计数正确，也不证明执行次数恢复准确，不给 M1 设绝对门槛。M2 衡量参考热点是否在 sample 侧同样处在高位，不衡量计数是否准确。head 不进入任何行的 body 计数，U 内缺失按 0 计时补零也不改变各行计数，所以 M1、M2 对 head 与补零策略没有区分力（见第 9 条、5.9 第 2 条）。行级指标也不能证明内联上下文或 discriminator 归属正确：两者被打乱但汇总行计数不变时，行级指标不变。
   - 分支概率误差（原主指标）：在严格匹配的分支上照常计算并报告，作为描述性指标，不参与等价判读。已知局限（只适用于该描述性指标）：sample 侧加了 `-disable-sample-loader-inlining`，内联体的 profile 被合并或缩放到函数本体，测得的是函数本体的标注质量，不等于生产编译中带内联的效果。
   - 插桩覆盖参考的取得：FFmpeg 的整体 `llvm-cov export`（JSON）峰值约 4.3 GiB，按源文件过滤不降低内存（附录 G.2.5）；lcov 导出的内存未核实，按附录 G.2.4 的覆盖导出级别执行，并在 spike 上核对 lcov 与 JSON 的逐行计数一致。参考文件生成一次后复用，记录 SHA。
   - 评估侧另统计"行号非 0 但小于函数起始行"的帧数（`line_before_start`），只观测，不改变工具的计数规则；评估中非 0 时另行裁决。
6. 统计判读（v1.1）：
   - 判读方式与结果名称（按第 5 条的对象登记表）。先处理无定义情形：U 为空、T = 0 或 K 无定义时，该对象 M1、M2 都无定义，判读记为"证据不足"；之后才进入下列分支，不对 0 或 null 计算 1/K：
     - K < 50：该对象 M1、M2 都只作描述，不进入任何判读分支（spike 预计属于此类）。K ≥ 50 是预先选定的对象准入条件，不是统计分辨率定理，也不表示 K < 50 时等价必然要求全部 RUN 相同。
     - K ≥ 50 且 n_eff ≥ 3：联合判读模式。M1、M2 都有定义且各自差值区间都完全落在 [−ε, ε] 内时，结果为"M1、M2 联合等价"。
     - K ≥ 50 且（n_eff 为 null，或 n_eff 有定义且 n_eff < 3）：M2-only 判读模式（显式分支，不对 null 做数值比较）。M1 只作描述；只有 M2 的区间、退化与准入检查全部通过时，结果为"M2 等价，M1 未判读"。
     - 判读所需的任一指标无定义或证据不足，都不得给出等价。联合判读是交集检验，不另做多重校正。
     - 聚合方式与 skid 的正式结论只取"联合等价"类对象的结果；"M2 等价，M1 未判读"类对象作为辅助证据（第 9 条）。
   - 等价区间：M1、M2 的 ε 为指标值的绝对差 ±0.02（不是相对变化 2%）。±0.02 是预先选定的判读界限，不是已验证的指标精度，其区分力由第 7 条的负对照检验。
   - 工作模型与等价结论的限定：本方案采用模型条件推断。登记的工作模型为：同一阶段内各逻辑 RUN 的配对差值独立同分布，阶段之间相互独立；t 区间按近似正态（分层时用 Satterthwaite 自由度），percentile 区间按 bootstrap 近似。这些假设在正式对象上没有被验证，模拟场景也不是它们成立的证明。输出的结果名称前加"登记工作模型条件下的"，区间注明为名义 95% 区间；每条结论附模型标识、未验证的假设与报告场景的失效结果，以及评价域说明（只覆盖固定构建中满足登记的行表归属见证规则的行，该规则不等同于逐行证明存在真实指令；同时给出该对象按 C、C_dc、C₀ 的 ③、③′、代码承载比例与评价域外的不重复参考执行量比例，这些是参考行计数质量的比例，不是运行时间或独立执行事件的比例；写出前按附录 O.2.3 第 7 项校验，不通过时拒绝写出），不把报告场景的误判率解释为正式对象的实际误判率。有限样本可能漏掉稀有事件：每个 RUN 发生概率低于约 21%（1 − 0.03^{1/15}）的偏离，有超过 3% 的概率一次也观测不到。更保守的方法可以用更宽的区间或拒判控制这一风险，但在本预算下多半无法给出等价；本方案选择保留标注工作模型条件的推断，并以下面的回退兜底（附录 M.4 第 1 条）。每条结论同时报告每个 RUN 的差值、超过 ε 的 RUN 个数与最大绝对差值；某个 RUN 的差值偏离本层中位数超过 max(ε, 5 × MAD) 时，另标"存在离群的单次差值"（只是描述，不改变判读结果）。
   - 预先登记的回退：附录 Q.5 第 9 项的验收场景有任一不达标时，修订 3 登记 `quality_equivalence_enabled=false`（全局开关，由模拟脚本按验收结果写出，不人工设定，不按对象或比较分别选择）：M1、M2 的差值与两种区间照常报告，不输出任何等价结论；聚合方式与 skid 的默认值按 5.4.4 第 5 条的保守规则与 5.9 的性能结果决定。这一取值在模拟完成后、任何正式受控量计算之前确定，不因此修订本文。模拟执行异常、缺行，或参数、种子与登记清单不符，属于执行失败，由脚本在运行前后自动判定，不触发回退：修正实现、提交并记录新的代码 SHA 后，按同一清单与种子重跑。统计验收不达标不能改称执行失败。完整运行（全部场景行齐全、清单与种子核对通过）的结果一经写出即保存并推送；之后发现统计实现错误时，修正后的实现同时用于正式分析，按同一清单与种子重跑，开关取所有完整运行结果的合取——任一次完整运行为 false 即为 false。全部运行的代码 SHA 与结果随修订 3 披露。模拟与正式分析调用同一个分层 t 区间与退化判定实现（同一模块，SHA 登记在 ① 中）。
   - 比较清单：每个因素单独与基准配置（`max`、skid=`none`、权重=`period`）比较：聚合方式 `sum`、`avg`；skid `prev-inst`；权重 `sample` 只在频率模式（period 不恒定）的采集层上比较，固定间隔采集的层上两种权重只差常数倍，不比较。另报告最终推荐组合与基准的比较：该组合由单因素结果按第 11 条与 5.4.4 第 5 条选出，依赖同一批数据，所以只作描述。清单在修订 3 中逐项列出，不做两两比较。清单中全部为配对比较；出现独立比较须作为协议变更登记。
   - 样本量与采集阶段：每个比较层的最终逻辑 RUN 数固定为 15，在修订 3 的 RUN 槽位表中按阶段登记计划数 n_h（Σn_h = 15）：第一轮已有的 RUN 为一个阶段，加装散热后补采的 RUN 为另一个阶段。某层第一轮的有效 RUN 少于 5 个时，该层不使用第一轮，15 个全部补采（3 + 12 结构在阶段方差比为 16 时判等价率约 3.4%，超过验收线）；这一选择只按 RUN 个数决定，不看任何指标。阶段权重固定为 λ_h = n_h / 15。第 5、10 个 RUN 时的结果只作描述，等价判读只在全部槽位采集完成后执行一次。原预注册"每配置至少 5 次"仍是下限；原预注册"干净重复不足……需要补采"对质量由固定槽位取代。
   - 估计量：主分析估计预定阶段混合总体的平均配置差值 Δ = Σ_h λ_h·mean(D_h)，D_h 为第 h 阶段各 RUN 的配对差值。结论只适用于这个预定混合总体，不外推为新散热条件下的单独结论。λ_h = n_h / 15 时 Δ 等于全部配对差值的普通均值，分层只改变标准误与区间。
   - 区间（都取 95%）：
     - (a) 分层 percentile bootstrap：种子 20261104、20,000 次（与原预注册相同），在每个阶段内部独立抽取 n_h 个逻辑 RUN；同一 RUN 的两个配置以及 M1、M2 使用相同的抽样索引。
     - (b) 分层 t 区间：a_h = λ_h²·s_h² / n_h，SE² = Σ_h a_h，自由度 = (Σ_h a_h)² / Σ_h [a_h² / (n_h − 1)]，s_h² 为阶段内以 n_h − 1 为分母的样本方差；只有一个阶段时就是普通配对 t 区间。
     - 判为等价要求 (a) 与 (b) 都完全落在 ±ε 内，等价于两者的包络 [min(L_a, L_b), max(U_a, U_b)] 落在 ±ε 内。这是因 RUN 数少、percentile 区间偏窄而登记的保守补充；区间方法在修订 3 中固定，不得因区间宽度改用其他方法。20,000 次重采样不能代替独立 RUN 数。
     - 退化样本：任一具有正权重的阶段，其配对差值的极差 max(D_h) − min(D_h) ≤ 10⁻⁹ 时，标记 `degenerate_sample`（原因 `numerically_flat`），结论为"证据不足"：不把该阶段的不确定性视为已经证明为 0（例如旧阶段 3 个 RUN 的差值全为 0，而真实差值来自稀有事件）。极差用未量化的差值计算，与阈值的比较一律用 IEEE-754 double：阈值为字面量 1e-9 对应的 double，M2 若以精确有理数计算差值，先转为 double 再求极差与比较；规则对平移不变，不受舍入分格的影响，能挡住浮点误差（数学上相等的两个 M2 可因求和顺序相差约 10⁻¹⁷）。它表示"在登记的数值分辨率内不可区分"，不宣称数学上完全相等，也会保守地拒绝小于 10⁻⁹ 的真实阶段波动；大于这一分辨率的真实微小扰动不受它影响，属于上面所述工作模型的局限。保存每个阶段的原始最小值、最大值与极差；区间与描述性差值用未量化的值。某阶段的差值都在分辨率内相同时，描述中写明"该阶段所有 RUN 的差值在数值分辨率内相同"，不称为等价。任一非空阶段 n_h < 2 时，登记准备校验失败。NaN、无穷值或无法形成区间都不得通过。
   - 配对：由同一逻辑 RUN 的原始数据转换出的不同配置按 RUN ID 配对，两侧使用同一个 RUN ID 集合。来自不同原始采集的配置之间独立重采样，不因交错执行而当作配对。这是对原预注册"默认独立重采样"的明确补充，在修订 3 中登记。
   - 有效 RUN、重采与停止：
     - 有效 RUN 指采集完成、原始数据通过拉回校验的逻辑 RUN。
     - 每次尝试结束后，由脚本先按原预注册的任务停止条件（`preregistration.md` 第 3 节第 5 条：身份、build-id、原件 SHA 不一致、硬件事件错误等）分类，再决定是否重采。非停止类故障必须命中修订 3 登记的原因码白名单，并满足该原因码规定的正面证据条件；仅有 perf 非零退出、缺少 stderr 或"没有发现停止证据"，都归为原因不明，按停止处理，不推定为可重采。
     - 拉回中断而板上原件完整保留时，重传同一原件，不重新运行负载，也不计为新的尝试；完整传输后 SHA 仍不一致，按停止条件处理。
     - 重采在同一槽位进行：本批内下一个交错位置立即重采；批次结束后才发现的失败，在下一批开头重采。首次尝试之外最多 3 次（总尝试不超过 4 次，第五次尝试被拒绝），每次尝试都写入收据。
     - 每个槽位至多一次成功，首次成功即为终态，此后不得再采。成功、失败或停止由脚本按退出码、原因码、停止条件分类与拉回 SHA 自动判定并写入收据，不人工改判。转换失败、遥测资格与任何指标结果都不是重采理由。
     - 4 次尝试都失败的槽位保留为缺失，不用额外 RUN 替换。
     - 停止后的状态：停止首先进入 `paused_stop`，原收据保留自动判定的结果，不覆盖。之后只能通过追加的事件迁移状态：
        - 证据记录：每次尝试结束（不论成败）以及采集器检测到失败时，脚本立即记录 `/opt/afdo_agent/` 所在分区的 `df` 与全部温度传感器读数，连同 attempt_id、boot_id 与 CLOCK_MONOTONIC 时间，作为证据文件随该尝试的收据保存；采集脚本自身的停止动作（过热停止、空间检查不通过、收到人工停止命令）也写入带 attempt_id 的记录。
        - 恢复：事件引用原停止收据，给出登记的原因码与证据文件的 SHA，由脚本核验三部分：① 故障证据——与该 attempt_id、boot_id 关联的停止动作记录（空间不足：空间检查不通过的记录，且证据文件中的可用空间低于登记阈值；过热：过热停止记录，且温度读数达到登记阈值；人工停止：带本次 attempt_id 的停止命令记录）；时间窗内的环境异常只能作为佐证，不能单独把原因不明的退出定为可恢复的故障；② 恢复前新采集的状态证据，证明空间、温度等满足登记的启动条件；③ 重新通过原预注册的身份断言（型号、架构、内核、build-id）。只有说明文字不行。恢复不得改变登记的采集条件，人工停止须有明确的恢复指令。之后的尝试收据引用已推送的恢复事件，并继续累计原尝试次数，达到 4 次后不得恢复为第 5 次。
        - 结束：原因为身份、build-id、原件 SHA 不一致或硬件事件错误（同时存在可恢复原因时，不可恢复原因优先），没有关联停止动作的原因不明退出，证据不能核验，或决定结束采集时，追加 `stopped_missing` 事件，所有尚无终态的槽位进入终态"停止缺失"，按缺失处理，相关比较为"证据不足"。终态在本修订下不得撤销，恢复须作为新的预注册修订。
        - 转换失败与遥测异常不进入这一状态机，也不是重采理由。
   - 缺失：某个 RUN 的派生配置转换失败，或该 RUN 该配置按第 5 条为无定义（出现未对齐条目），都不记为零分，也不只在失败的配置中删去该 RUN；该 RUN 对涉及这个配置的比较记为缺失。任一阶段的有效配对少于计划数时，该比较记为"证据不足"，不重新分配阶段权重，并报告缺失原因与次数；转换失败本身写入该配置的可用性结论。
   - 干净子集：按新判据的"遥测合格"子集只作描述，不作等价判读（第一轮在新判据下全部为 unknown，干净子集达不到 15 个）。
   - 证据不足时，可以按复杂度或参考实现对齐选择保守配置（5.4.4 第 5 条），但不得称为统计等价。
   - 做低、中、高三档样本预算的敏感性分析。
   - 登记内容的划分与门禁：
     - 修订 3 登记并锁定：① 分析协议、评估脚本及其依赖与配置、对象登记表与全部静态产物（跨侧对应表与裁决表、映射表、排除清单、边界排除组、U、函数权重）；② 登记时已存在的输入的完整清单与 SHA-256；③ 完整的 RUN 槽位表：每层 15 个槽位，含纳入的既有 RUN（原 RUN ID、原件 SHA 与既有的采集、接收凭据）与未来 RUN（预定的层、阶段、负载与采集参数，原件字段暂空）。
     - 既有 RUN 的凭据作为初始化收据导入，注明导入时间与原始采集时间，不表述为登记后的新采集。补采原件按槽位写入单独的、只追加的数据收据（槽位、尝试序号、原件 SHA-256、采集与接收时间、实际命令、自动判定的结果与原因），在该原件首次参与指标计算之前提交并推送。新增或替换槽位、改变采集规则属于协议变更。
     - 受控量：M1、M2、M2b、M3、分支概率误差、区域敏感性与合并口径敏感性，以及其他任何在配置之间比较质量的量。清单随修订 3 登记。
     - 计算日志：每次对正式原件计算任一受控量，都向只追加的计算日志写入时间、原件集合、配置与脚本 SHA，并与上一条记录做 SHA 链接；后续任何修订都须据此披露登记后看过的中间结果。
     - 门禁：评估脚本在计算任何正式 sample profile 的受控量之前核对：修订 3 已提交并推送；①、②、③ 的 SHA-256（或锁定提交中的 blob 身份）与登记一致；参与计算的原件都属于登记的槽位、有已推送的收据，同一原件不占两个槽位，每个槽位至多一次成功；计算日志的 SHA 链完整；尝试、停止、恢复事件与终态的状态迁移完整合法（恢复事件先于后续尝试、证据核验通过、没有绕过停止条件）。等价判读之前，另核对该层全部槽位都有终态收据（成功、4 次尝试都失败，或"停止缺失"）。任一项不满足时拒绝计算。
     - 登记后对 ①–③ 的任何修改，都必须作为新的预注册修订重新登记并写明原因，不得在修订 3 名下修改后重算。
     - 脚本开发的数据规则：合成 profile（把计数写到映射表的键上、按工具的文本格式生成）可以计算任意指标；与正式 S 同一 ELF 的任何真实 profile（包括第一轮的 CALIBRATION 运行与基准配置）在登记前一律不计算任何受控量，只转换基准配置，只用于键覆盖、条目分类与流程冒烟；修订 3 披露登记前打开过哪些真实 profile、计算过哪些量。
7. 指标区分度的验证（负对照）：
   - 使用热点分布已知不同的受控工作负载，验证指标能识别差异；同时加入热点相同的不同输入，作为"不应强判退化"的对照。
   - 随机扰动（函数内计数打乱、行偏移整体平移）固定种子、重复多次，并确认扰动确实改变了参考分布。
   - 身份冲突只用于测试身份拒绝，不尝试绕过；需要评估"错误内容"时，使用显式缺失身份的测试 fixture，或在评估脚本中构造损坏的 profile，不为此增加生产接口。
   - "另一份真实输入"作为泛化测试，不要求其必然更差。
   - 行级指标的夹具（v0.9）：参考恒定、sample 恒定、全部为 0、大量并列；热点截断恰好达到、跨过 80% 与截断处大量并列；M1 等价而 M2 不等价、任一指标无定义；同一 RUN 派生配置的配对重采样与多个采集段归属同一 RUN；固定种子重跑逐项一致、不静默丢弃 NaN；"执行次数与周期热度反序"的受控例子；所有参与行都写 1 时 M2b 可以为 1 但不能判为质量良好；只改 head、只补显式 0 时 M1、M2 不变；用同一份地址级计数生成 sum、max、avg 三份 profile，M2b 相同而 M2 可以不同。对齐夹具：函数体内 `#include` 一段代码、同一内联函数出现在两个调用点、一行含多个区域的循环头、两个源文件中的同名函数、同一物理行上的两个函数、行偏移回绕、同一 profile 键对应多个源位置、多行区域与 gap 及 skipped region；缺失条目与显式 0 条目产生相同的 U；删除一个热点函数的全部 sample 条目不能使它从 U 中消失；所有覆盖比例的分子都属于分母。v1.0 增加的夹具（映射表与 U 的独立性、未对齐键、M2 零计数与无定义情形、合并口径、n_eff、固定样本量与配对、转换失败、区域敏感性）见附录 Q.5 第 5–10、13、14、16 项。
8. 可选对照：在 x86_64 主机上构建指定版本的 create_llvm_prof，用 `--use_lbr=false` 处理 RPi5 的 perf.data（它自带 perf.data 解析，是否需要主机 perf 在评估阶段确认），对齐 sample/period 语义后比较，不把它当作真值；如果 x86 主机支持 LBR，在主机上运行 spike，用同一份 perf.data 同时生成 LBR profile 与 IP profile 作为上界参考。
9. 输入与分阶段：训练输入与测试输入分开（不同视频）。登记修订 3 之前，只用参考数据与 U 写出对象登记表（第 5 条：①–③、n_eff、K），不涉及任何 sample profile。spike 的 n_eff 约为 1.3、K 约为 5（评审按参考数据估算，确切值由脚本给出），预计 K < 50，M1、M2 都只作描述，spike 的结果是方向性的描述证据。聚合方式与 skid 的正式结论取联合判读模式的对象（K ≥ 50 且 n_eff ≥ 3，预期为 libavcodec，未核实）的结果，M2-only 判读模式的对象作辅助证据；`quality_equivalence_enabled=false` 时只报告差值与区间，默认值按 5.4.4 第 5 条与 5.9 的性能结果决定（第 6 条）。若没有任何对象属于联合判读类，聚合方式与 skid 由 M2 的辅助证据与 5.9 的性能结果共同决定，并在结论中写明。补零与 head 策略不改变各行的 body 计数，M1、M2 对它们没有区分力，只由 5.9 的性能分组与消费端检查（入口计数、覆盖率诊断）评估。M1 最高的配置不自动解释为最正确或最优的配置，聚合方式与 skid 的指标差异和 5.9 的性能结果一起报告。armv7l 的评估构建按第 9 节要求（含 `-mthumb`），另做一组 `-marm` 构建覆盖 A32。06 报告中的人工 sample profile 只作为匹配器的结构测试，不作为统计质量证据。
10. 对象与板子：spike 测试程序；libavcodec（FFmpeg H.264 解码）。RPi5 与 RPi4（新镜像）都用 cycles。
11. 决定：默认值由测试输入上的性能（5.9）、统计判据（第 6 条）与实现复杂度共同决定，不只取训练输入上指标最好者。libavcodec 热点中 `outside_dwarf_func` 的占比与分类、Thumb/A32 的样本占比（`isa`）写入结论。

### 5.9 编译端选项与性能评估（不改 clang）

1. 显式控制：
   - 编译步骤统一用 `-fno-sample-profile-use-profi -mllvm -sample-profile-use-profi=<true|false>` 关闭驱动的自动注入并显式指定 profi；stale matching 显式用 `-mllvm -salvage-stale-profile=<true|false>`，单独评估它时固定 `-mllvm -salvage-unused-profile=false`。
   - LTO 构建时，链接步骤必须传入同一个 `-fprofile-sample-use=<profile>`（驱动据此给链接器传 `sample-profile=`，`CommonArgs.cpp:1253–1259`），并显式指定 profi、`salvage-stale-profile` 与 `salvage-unused-profile`：编译阶段的 `-mllvm` 参数只转发给 cc1 作业（`Clang.cpp:7680–7690`），链接参数的构造（`CommonArgs.cpp` 的 `addLTOOptions`、`Gnu.cpp`）不处理编译命令中的 `-mllvm`，所以链接步骤必须自己带上。lld 的写法为 `-Wl,-mllvm,<选项>`；其他链接器的写法未核实。
   - 用 `clang -###`、链接命令、profile 属性与 IR（LTO 时含 post-link IR）核对实际生效的配置；覆盖率与陈旧度诊断在实际运行 sample loader 的阶段核对（LTO 时为 post-link）。
   - LTO 组另加负对照："编译有 profile、链接漏传 profile"。
2. 分组（聚合方式、skid 先由 5.8 的指标与本节结果共同筛选；head 与补零不由 5.8 筛选，在本节的消费端检查与性能测量中评估）：

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

   补零维度：每个入围的聚合方式与 skid 组合，G1–G4 都按 `--ip-zero-fill=none` 与 `--ip-zero-fill=sampled-functions` 展开，完整的生成与消费参数写入登记矩阵。采用较小矩阵时，须在修订 3 中逐项列明固定项与未评估的交互，不得对未覆盖的组合宣布默认行为已验证。

   若有目标包使用 LTO，另加 G1 的 LTO 变体，用 `-Wl,-mllvm,-print-after=sample-profile` 检查 post-link IR 中的 `function_entry_count`。

3. 消费端检查（每组）：`-mllvm -sample-profile-check-record-coverage=<N>`、`-mllvm -sample-profile-check-sample-coverage=<N>`（`SampleProfileLoaderBaseUtil.cpp:26–34`）、`-mllvm -report-profile-staleness`；在 IR 中检查 `function_entry_count` 是否存在且合理（G2 组另观察目标函数的入口计数值与冷标记），以及是否有等于 4294967295 的 branch_weights（饱和）。
4. `-fprofile-sample-accurate`：会把未采样的调用点和函数都按 0 处理（`SampleProfile.cpp:151–155`），并忽略 profile 符号列表（`:1987–1989`）。不作为稀疏 IP 的推荐默认，只在评估中观察。profile 符号列表会让列表中的符号被视为"计数准确"（`ProfileAccurateForSymsInList` 默认为 true，`:162–165`），所以第一批禁用 `--populate-profile-symbol-list`。
5. 性能测量（仅用于验证本增强）：
   - RPi5 与 RPi4 各自在 FFmpeg H.264 解码上测；固定编译、链接、LTO 参数、解码工作量与线程数。库按第 9 节的构建要求构建。
   - 每组的正式轮数 N 在修订 3 中按板子写定，各组交错执行，丢弃预热轮（注册表扫描）。N = max(10, ⌈2 ×（1.96 × 1.2533 × CV ÷ 0.005）²⌉)，上限 40：CV 为加装散热后新镜像上 G0 预试（至少 10 轮，带采样器）去掉预热轮后耗时的样本标准差（分母 n − 1）÷ 均值，保留 4 位有效数字后代入，预试中的离群轮次不剔除（偏向更大的 N）。目标是两组中位数相对差的 95% 区间半宽约为 0.5%（近似正态时中位数的标准误约为 1.2533·σ/√n）；这是在两组独立、近似正态、波动相近条件下的预算近似，不保证实际半宽达到 0.5%。无法完成规定的预试时直接取 N = 40，标注为预算上限选择；旧镜像基线（`03_rpi4_sampling.md` 第 4 节）只作背景，不用来反推 CV。到上限时仍取 40，结论可能为"证据不足"。N 不依据任何组间比较或区间宽度增加；G0 预试的条件、轮数、原始耗时、采样器开销与 N 的计算随修订 3 披露，预试数据不并入正式的 N 轮。原预注册"RPi4 证据不足时后续加轮数"与"干净重复不足……需要补采"对性能由本条取代。
   - 固定 cpufreq governor；记录 `scaling_cur_freq`、`/sys/class/thermal` 与节流、后台负载；记录镜像 BUILD_ID、内核 `uname -v`、实际加载的 libavcodec build-id、换出统计 pswpout（新镜像的 force_reclaim 修复会真正换出到 zram）。
   - 保存全部轮次；异常判据预先定义（例如换出明显增加、发生节流），同时报告剔除前与剔除后的结果。性能按耗时中位数的组间相对差判读，等价区间 ±1%，区间方法沿用原预注册。达到登记的轮数 N 后区间仍未落入 ±1% 的，报告"证据不足"，不再加轮。n 约为 10 时 percentile 区间可能偏窄，这一点作为已知局限写入结论。5.8 第 6 条的 RUN 均值、±0.02、固定 15 个 RUN 与分层估计只用于质量指标，不用于耗时。
   - 采集与测量的合格判据（v1.1，预注册修订 3，附录 G.3）。全部满足时标为"现有遥测未观察到异常"。本板读不到固件的完整降频状态位，固件降频状态单列为 unknown，这个标签不表示已排除全部降频。
     - 监测窗口：每个 RUN 记录 monitor_start、workload_start、workload_end、monitor_end 四个 CLOCK_MONOTONIC 时间；monitor_start 不晚于 workload_start 前 2 秒，monitor_end 不早于 workload_end 后 4 秒。"负载窗口"指 [workload_start, workload_end]，"监测窗口"指 [monitor_start, monitor_end]。
     1. 负载窗口内每秒读取的 `scaling_cur_freq` 都等于固定频率（`cpufreq.c:752` 的 `show_scaling_cur_freq`）。它反映内核记录的频率，能看到内核的温控降频，看不到固件层面的调频；同时读取第 2 项时，它也会受第 2 项的影响（见下条）。
     2. 负载窗口内每秒以 root 读取的 `cpuinfo_cur_freq` 都等于固定频率（`show_cpuinfo_cur_freq`，`cpufreq.c:791`，权限 0400 见 `:963`）。读取经 `__cpufreq_get`（`:1881`）由 cpufreq-dt 经 `clk_get_rate` 调用 clk-raspberrypi 的 `raspberrypi_fw_get_rate` 向固件发 GET_CLOCK_RATE（评审核实每次读取都向固件查询，不使用缓存）。GET_CLOCK_RATE 是否反映全部固件限频未核实，这一项只能发现固件改设的时钟。偏离只由判定脚本比较读数与固定频率得出。读数与内核记录相差 ≥ 1 MHz 时，`cpufreq_verify_current_freq`（`:1774`）经 `cpufreq_out_of_sync`（`:1759`，只有 `pr_debug` 输出；它发出的频率转换通知在转换结束时把内核记录改为该读数）更新内核记录，并调度 policy 更新（`handle_update`，`:1191`），performance governor 随后会重新请求最大频率（`cpufreq_performance.c:14–17`）。所以读取第 2 项会使第 1 项随之偏离，并可能"修复"固件的改动；相差不足 1 MHz 时读数直接返回内核记录（`:1797`），因此读数不是未经修饰的硬件测量值。规则：以首次偏离为准，任一秒偏离即判异常，之后的读数不能撤销这一判定。行号均以板上内核 6.12.80 源码为准。
     3. 监测窗口内（含批次校准期间）所有温度读数低于 75°C。
     4. 欠压：监测窗口内每秒读取 `rpi_volt` 的 `in0_lcrit_alarm` 全部为 0，且监测窗口内的内核日志（见"日志检查"）没有 `Undervoltage detected`。驱动以延迟工作名义上每 2 秒向固件查询一次并清除固件的 sticky 位，sysfs 返回最近一次查询的结果（`raspberrypi-hwmon.c:28–80`）；2 秒不是保证的刷新时限，窗口延到负载结束后 4 秒只是名义余量。查询失败时驱动只用 `dev_err_once` 记录第一次失败并保留旧值（`:37–40`），之后的失败不可观测，读到 0 不证明刚刚成功刷新。规则：每个板上会话开始时（开启 root 后、第一批之前）启动记录器，以 `O_RDONLY | O_NONBLOCK` 打开 `/dev/kmsg` 并 `lseek(fd, 0, SEEK_SET)`，从缓冲中最旧的记录读起（`printk.c:900`），首条记录序号须为 0（证明开机以来的日志尚未被覆盖）；之后在整个会话中连续保存到 `/opt/afdo_agent/` 并核对序号连续，会话结束时停止，随数据"拉回 → 校验 → 删除"；不安装开机服务，不写其他位置（附录 G.2.3）。每个 RUN 前核对 boot_id，改变时重新启动记录器并重新核对首条序号。会话开始时首条序号不为 0（缓冲已回卷）时不开始采集，告知用户：可由用户在会话前重启板子后开始新会话（用户操作，评估脚本不重启），或由用户决定接受该次开机全部 RUN 的本项为 unknown，决定写入事件记录；接受须在该次开机的第一次采集之前写入，采集后补写不能追认，之后的正常观测也不能清除该次开机欠压项的 unknown。记录器按 boot_id 维护"查询失败"的粘滞标记。记录中出现过 "Failed to get throttled"（`raspberrypi-hwmon.c:38–39`）时，该次开机全部 RUN 的本项判 unknown；记录器首条序号不为 0、有断号、保存失败或状态丢失、无法证明开机以来的日志完整时，同样判 unknown，不把"当前日志里没找到"当作"没有发生"。失败标记在本次评估的日志截止点统一传播，截止点随结果保存，使重放结果确定。没有失败记录时，标签说明中写明"后续查询失败只记录一次，缓存的新鲜度未核实"。
     5. 校准夹测：批次是预先排定的一轮完整交错配置块。每批前后，CPU0–3 依次各绑核运行同一个纯计算 spike 30 秒，`perf stat -I 1000` 在同一计数对象、同一窗口上记录 cycles 与 task-clock；校准期间采样进程绑到当前未被校准的 CPU。
        - 频率检查：除第一个与最后一个区间外，所有计数有效（计数器全程运行、未复用、时间有效、task-clock 大于 0）的中间区间都检查 cycles/task-clock 不低于本批固定频率的 97%（RPi4 为 1.455 GHz，沿用修订 1 有效频率判据的 97% 口径）；任一区间低于下限即判异常，不因该区间的时长或忙碌率不合格而删去这一证据。
        - 有效性：任一中间区间计数无效时记 unknown 原因，不能由其余合格区间抵消；每个 CPU 计数有效的中间区间少于 25 个、或校准提前结束时判 unknown。
        - 时序：相邻两次输出的时间差超出 1.000 ± 0.020 秒，或 task-clock 低于该时间差的 99% 时，只记告警。cycles/task-clock 的比值不依赖区间长短；板上已有记录中区间通常约 1.005 秒，每个 CPU 每次运行都有一个约 1.015 秒的区间。
        - 校准本身同样适用监测窗口、温度与缺口规则。
     6. policy：监测窗口内每秒读取 `scaling_governor`、`scaling_min_freq`、`scaling_max_freq`，任一与运行前的记录不同即判异常；无法读取判 unknown。
     - 遥测执行：采样进程以 root、nice 0 运行，绑到负载不使用的 CPU；负载占满全部 CPU 时绑到 CPU0，并在报告中记录。每条读数带 CLOCK_MONOTONIC 时间戳。
     - 缺口：每个观测流分别计算，第 1、2 项按负载窗口，第 3、4、6 项按监测窗口。相邻读数间隔大于 1.5 秒记为一个缺口；窗口内缺口超过 2 个，或任一间隔大于 3 秒，为超限缺口。允许范围内的缺口只记告警，不单独导致 unknown。第一条读数晚于窗口起点 1.5 秒以上，或最后一条早于窗口终点 1.5 秒以上，为"窗口不完整"。
     - 日志检查：不写 `/dev/kmsg`。记录器是该描述符唯一的读取者，按 boot_id 持有"最后已保存序号"：每条记录成功保存后更新，读到 EAGAIN 时不重置，只有本次开机从未读到任何记录时才为 −1。测量脚本在 monitor_start 之前与 monitor_end 之后各向记录器请求一次端点：记录器把描述符排空到 EAGAIN，返回最后已保存序号（s0、s1）与排空前后的 CLOCK_MONOTONIC 时间。窗口为序号区间 (s0, s1] 的全部已保存记录；期间没有新记录时 s1 = s0，窗口为空，不等待新日志（描述符为非阻塞，读空时内核返回 EAGAIN，`printk.c:836`）。一个 RUN 的两个端点必须属于同一 boot_id，否则判 unknown。两次读取须在时间上保守包围监测窗口：第一次读取完成早于 monitor_start，第二次读取开始晚于 monitor_end。相邻序号不连续、读取返回 `-EPIPE`（同一描述符读到已被覆盖的记录，`printk.c:859–863`）、读取超时或无法证明包围时判 unknown。`SEEK_END` 只把游标放到下一条待写记录（`printk.c:912–914`），不用来取最后序号。日志时间戳取自 `local_clock()`（`printk.c:2249`），与 CLOCK_MONOTONIC 不同，只作交叉核对，不用来界定窗口。先核对序列完整，再按窗口与关键字筛选。
     - 判定优先级：有效读数证明任一项不满足（含已确认的 policy 变化）→ 异常；否则任一必需观测缺失、无效（解析失败、`<unknown>`、读取超时）、超限缺口或窗口不完整 → unknown；否则 → 现有遥测未观察到异常。无效读数不当作明确异常。异常与 unknown 的各项原因都保留，不互相覆盖。例如已知过热的旧记录即使缺少新字段，也判异常；第一轮没有已知异常、只缺新字段的记录判 unknown。
     - 校准结果的传播：一批的前、后校准的异常、缺失或无效原因传播到该批每个 RUN，再与该 RUN 自身的原因按"异常 > unknown > 合格"合并。同批一个 RUN 自身异常，不影响其他 RUN 因校准缺失而判 unknown。
     - 全部轮次与"遥测合格"子集分别报告。
   - 有效频率（协变量）：逐轮记录 cycles/task-clock。组间有效频率差定义为 |m_A − m_B| ÷ ((m_A + m_B) / 2)，m 为各组有效频率的中位数；超过 0.5% 时，该比较的性能结论标为"有混杂风险"，不作等价或收益判读。频率离群标记：在"遥测合格"的轮次中，有效频率低于本组中位数减 3 × max(MAD, 0.001 × 中位数)（MAD 为未缩放的中位数绝对偏差）的轮次标为"频率离群"，只在附录中列出，并对主结果做一次剔除这些轮次的敏感性分析；离群标记不改变资格，也不改变主结果。逐秒采样可能漏掉亚秒级的频率跌落，这一标记是对它的兜底。
   - 散热前置条件：第一轮诊断中四核满载约 25 秒升到 79°C，80.3°C 时 `scaling_cur_freq` 降到 600 MHz（附录 G.5.4）。性能测量前板子须加装散热片与风扇，并复测四核满载 60 秒的最高温度低于 75°C；不满足时不开始性能测量。这只是启动条件，不替代逐轮的合格判定。
   - 判定脚本的夹具：用模拟的 sysfs 目录与 `/dev/kmsg` 记录覆盖以下情形：告警在运行中途短暂为 1；告警在负载结束附近出现、随后才被驱动更新；欠压日志在负载结束后 2 秒到达（仍须命中本 RUN）；窗口外的欠压行，包括时间戳因时钟偏差看似落在窗口内的（不计）；序号跳号、`-EPIPE`；开机后出现过 "Failed to get throttled"（本项 unknown）；`cpuinfo_cur_freq` 有一秒偏离、之后恢复（仍判异常）；`scaling_max_freq` 在运行中下降（异常）；校准有一秒为 1.44 GHz；校准中一个时长 1.05 秒、1.44 GHz 的区间（仍判异常）；计数有效、频率合格、忙碌率 ≥ 99% 时，校准区间时间差为 1.015 秒（不告警）与 1.025 秒（时序告警），以及 0.980 与 1.020 秒的边界；忙碌率 98% 的区间（忙碌率告警；频率低于 97% 仍判异常，计数无效仍判 unknown）；某 CPU 计数有效的中间区间 24 个（unknown）；一个中间区间计数无效、其余全部合格（unknown）；校准全部区间被截断、校准提前退出、PMU 未计数；记录器首条序号不为 0（例如 37）、记录有断号、保存失败（欠压项 unknown）；会话中 boot_id 改变而记录器没有重启（该 RUN unknown）；记录器输出路径不在 `/opt/afdo_agent/` 下（准入失败）；两次端点请求之间缓冲回卷（unknown）；两次端点都没有新记录（空窗口，通过）；一个 RUN 的两个端点跨 boot（unknown）；会话开始时首条序号不为 0（不开始采集）；后台已保存窗口内的欠压消息而端点请求时没有新记录（仍须命中）；负载结束后 3 秒内 policy 没有读数（窗口不完整）；后校准失败（整批异常）；一个 RUN 过热、其余正常但全批缺后校准（该 RUN 异常、其余 unknown）；温度达到 75.0°C；已知过热同时缺一个传感器（异常）；间隔恰为 1.5、1.6、3.0、3.01 秒；3 个缺口；不同传感器各自缺口；负载结束后 4 秒内没有读数（窗口不完整）；`<unknown>`、读取超时、无效温度与明确过热分别处理；15 轮有效频率完全相同（MAD 下限生效、无离群）；离群轮次（只标记）；组间有效频率差超过 0.5%（标混杂风险，不再筛选）；所有项正常。另用已有的四核 600 MHz、80.3°C 诊断原件重放判定，应判异常；第一轮缺欠压字段的轮次不得用其他 RUN 的 0 值补齐；新判定规则对旧记录的重放标签不覆盖历史资格。加装散热后用四核满载做一次正对照，应判合格。
6. 过期复用测试：
   - 改动类型：纯行号移动；热点函数内的 CFG 改动；调用点插入与删除。
   - 每种改动比较四组：不用 profile；旧 profile 且关闭 salvage；旧 profile 且开启 salvage；重新采集的 profile。行级组显式开启 salvage；probe 组验证默认开启的行为。
   - 记录是否触发 checksum mismatch、是否实际发生匹配、是否被 `rejectHighStalenessProfile` 整体拒绝。
   - 旧 profile 原本就没有显著收益时，"收益保留比例"标为不适用。
7. 可选组（工具链升级）：用新版本工具链消费旧工具链构建上采集的 profile，记录覆盖率与陈旧度诊断。它对应"从已发布的 N 版本采样、用于 N+1 版本构建"的常规用法；身份校验不涉及消费构建（5.3.3 第 9 条），失配由消费端诊断体现。

### 5.10 测试

1. 回归：按 C1 的验证方式执行。
2. 三层验证：
   - 第一层，golden fixture：可人工推导地址、内联栈与计数的小程序。每个二进制 fixture 附源文件、生成命令、工具版本与预期值。测试不依赖本机 perf、板子或网络。
   - 第二层，独立核对：主核对用 GNU `addr2line -i -f`（GBS root 中的 binutils 2.43），行偏移的起始行从 `readelf --debug-dump=info` 的 `DW_AT_decl_line` 取得；`llvm-symbolizer` 作为第二核对方（它与 profgen 共用 DWARF 与 Symbolize 库，独立性不足）。重算行级计数并与工具输出逐行比对。地址扰动负对照分两类：落到无效地址；仍落到另一个有效函数或源码位置（用来发现"可用率高但内容错误"）。核对脚本读取原始 `st_value` 时清除 Thumb 位（5.7.2 第 7 条）。
   - 第三层，消费验证：`llvm-profdata show` 能读取；clang 消费后在 IR 中检查函数名、内联位置的匹配情况与覆盖率诊断。
3. lit 基础设施：该测试目录整体要求 X86 后端（`test/tools/llvm-profgen/lit.local.cfg:6–7`），新用例另加 `REQUIRES: aarch64-registered-target` 或 `arm-registered-target`。Tizen x86_64 的 llvm 包含 X86、ARM、AArch64 后端，满足条件。预生成的测试二进制单独成一个补丁，便于评审。perf script 文本素材取自 05–09 报告中板上 perf 6.12.80 的实际输出（样本行、MMAP2 两种形式、`PERF_RECORD_MMAP`、`[vdso]`、`[kernel.kallsyms]`、LOST、`-1/-1` 样本、buildid-list 的空 build-id 行、`(deleted)`、内核模块）；`[unknown]` 按 perf 源码格式编写并注明来源。不把自造的 `PERF_RECORD_LOST_SAMPLES` 行当作"符合 v6.12 导出格式"的正向素材。
4. 新增正向用例：
   - aarch64 PIE；aarch64 共享库，非零加载基址，多个 PT_LOAD 且 `p_offset ≠ p_vaddr`；16K、64K 对齐的合成偏移；
   - DSO 字段解析：路径含空格、嵌套括号、` (deleted)`、路径内部的 `+0x`、合法的十六进制偏移后缀、`([unknown])`；
   - Thumb 构建（`-mthumb`）；A32 构建（`-marm`）且含 `$d` literal pool；ARM/Thumb 混合；去掉 `.ARM.attributes` 的 Thumb fixture；16 位与 32 位 Thumb 指令相邻、IT 块、内联 TBB/TBH 跳转表（`$d`）；映射状态在函数起点之前建立；映射符号恰好位于函数起点；多个不连续的函数区间（第二段起点须由覆盖它的 `$t` 映射区间步进得到）；纯 A32（只有 `$a`）与纯 AArch64（只有 `$x`）的合法起点在没有任何 `$t` 时通过；`$d` 区间之后的 A32 函数起点；`$t → $d → $a/$t` 的混合区间（不得跨状态连续解码）；为证明起点而读取的较长前缀不增加 `n(k)` 或补零位置；`$t.1`、`$t.hot`、`$d.literal` 一类长形式映射符号名；`.plt` 末尾为 `$d`、紧接的 `.text` 以 `$t` 开头（不得把 `.text` 开头判为数据）；同地址、不同节的映射符号；`only-keep-debug` 调试文件不含代码字节、指令取自运行 ELF；Thumb 上的 `avg`、`sampled-functions` 补零与 `prev-inst` skid；边界与 `llvm-objdump --triple=thumbv7a -d` 及人工 golden 值逐条一致；
   - 只有 `.dynsym`、没有映射符号：`isa` 统计按 `SF_Thumb` 正确（另见负对照）；
   - `#pragma unroll 4` 循环：按 5.4.4 修正后的推导设定 golden 值（`sum = N·Σc_i`、`max = N·max c_i`、`avg = N·c̄`），检查三种方式加 duplication 后的值；同一函数内联到两个调用点；多层内联；
   - 使用 FS discriminator（`-mllvm -enable-fs-discriminator`）的二进制，经 strip-all 再配 `--debug-binary`，`fs_discriminator` 字段与未 strip 时一致；
   - strip-all 的 `--binary` 加 `--debug-binary`（映射符号来自调试文件）与未 strip 时输出逐字节一致（对照对象见 5.3.4 第 4 条）；
   - 计数与取整：分数权重在聚合后才取整、0.5 边界、超过 2^53 的整数、duplication 乘法接近溢出、极小正 total 写为 1、偶数个样本的中位数、固定 period 下两种权重结果相同；`-c` 与 `-F` 两种 period 输入；
   - 身份（按 5.3.2 第 3 条的公式）："全部映射有 ID / 部分有 ID / 全部无 ID"分别与"buildid-list 一致 / 缺失 / 冲突"组合；buildid-list 中的空 build-id 行；样本路径没有映射记录；目标路径只有非可执行映射，分别与 buildid-list 一致、缺失、冲突组合（默认失败，允许缺失时最多为 `unverified`，冲突为 `mismatch`）；已有一致的可执行映射时，加入无 ID 的非可执行映射等级不变，加入 ID 冲突的非可执行映射为 `mismatch`；三方都没有 ID 且给了 `--allow-missing-build-id` 时为 `unverified` 并继续；deleted 路径不用 buildid-list 补足；
   - 候选选择：`--binary` 为指向真实文件的符号链接时候选正确，指向另一个文件时按 build-id 判为 `mismatch`；候选为空时报错列出样本最多的文件 DSO 并提示正则；两个无 ID、文件名相同而路径不同的 DSO，默认匹配时报歧义，用正则只选其中一个时可按 `unverified` 继续；正则排除的同名路径不重新进入候选；默认匹配下 `libx.so (deleted)` 命中 `--binary=libx.so` 进入候选，没有 `mmap2` 证据时因身份缺失而拒绝，不进入 `other_dso`；
   - build-id 长度：由 `--build-id=fast` 构造的 8 字节 ID 与 20 字节 ID 判为不一致；
   - pid/tid：`-1/-1` 的内核样本被正确解析与分类、计入 `pid_unknown`；`--pid` 不匹配 -1；pid 为 -1 的 `PERF_RECORD_MMAP` 内核映射；
   - LOST 记录与丢失比例：用 06 的计数核对 `exported_lost_ratio`；改变事件、pid、DSO 筛选条件时该比例不变；无 LOST、只有 LOST、多事件、多进程；检查 LOST 行条数、N 之和与样本行数分别记录，`count_unit=records`、`completeness=unknown`；有 LOST 行时出现 `W_LOST_MAY_INCLUDE_SIDEBAND` 与 `mapping.completeness=unknown`，没有时不出现；不用合成文本声称已在板上复现"只丢边带记录"；
   - 报告：cycles 与 cpu-clock 混合输入时不产生跨单位的 `period_sum` 总量；少量可用样本与大量不可用样本混合时，目标可用率不受聚合方式、取整与裁剪影响；小于一个归一化单位的桶；门槛"设置 / 未设置"与指标"已知 / 未知"的状态矩阵（5.6.2 第 5 条），其中未设置丢样门槛且文本没有 LOST 时为 `not_evaluated`；输入有效且没有独立失败条件时，未设置门槛的退出码为 0；所有门槛都未设置但目标样本为 0 时仍非 0 退出；
   - writer：IP 模式加 `--use-md5` 时，text 格式出现告警、extbinary 生效；同一 ProfileMap 经 IP 与 LBR 两条路径写出的 extbinary 字节相同（用 [ip, ip] 对照用例的 ProfileMap）；
   - 未加 `--kernel` 时出现内核样本；`[vdso]` 带偏移的样本计入 `other_dso`；`outside_dwarf_func` 的三类原因；
   - `entry-estimate`：最早位置是内联调用点、顶层没有 body、同一调用点多个 inlinee、正 total 但估计为零；带修饰符的事件名；
   - `max` 对照：在 aarch64 与 A32 的 fixture 上，整数权重、关闭 skid、相同符号化与 duplication 的条件下，IP 模式已命中位置的正 body 计数与 [ip, ip] 区间注入后 LBR 路径的对应计数一致；total、head、缺失位置与零位置各用独立的 golden 预期，不要求完整 profile 一致；Thumb 不做这项对照（LBR 路径依赖全量反汇编）；
   - 确定性：同一输入运行两次，profile 与报告逐字节相同；
   - 5.12 的合并用例。
5. 负对照（每条都检查报错文本或具体计数）：
   - 缺少 dsoff 字段；dsoff 偏移落在两个段之间；含 brstack 或调用栈扩展行的文本；`period=0`；
   - 逐映射 build-id 不一致；同一路径出现不同 build-id；MMAP2 与 buildid-list 对同一路径给出不同 build-id；只有路径级证据时的 `(deleted)` 路径；未验证模式下同一路径的 inode 不同；缺失与冲突同时存在（必须按冲突失败）；mmap2 证据为 X 而 `--binary` 没有 note（用 `llvm-objcopy --remove-section=.note.gnu.build-id` 去掉同一文件的 note），加不加 `--allow-missing-build-id` 都判为 `mismatch`；buildid-list 证据为 X 而 `--binary` 没有 note，判为 `mismatch`；`--binary` 有 X 而 `--debug-binary` 没有 note（及反过来），判为 `mismatch`；
   - strip 后的 `--binary` 与 `--debug-binary` 的 build-id 不一致；无 build-id 时文件名相同而路径不同；样本来自 RPM 安装的 A、`--binary` 给的是 ID 不同的打包前产物 A0，必须判为 `mismatch`；用消费 profile 后重建的、ID 不同的 ELF B 冒充被采样的 A，必须判为 `mismatch`（两条都要先构造或核实 ID 确实不同；反过来，A 生成的 profile 用于构建 B 不受身份校验约束）；同一个 A 复制到名为 BUILD 的目录后作为 `--binary`，结果不变；直接采样未打包 A 的合法 fixture 通过；
   - 多事件未指定 `--ip-event`；事件筛选后为空；目标样本为 0；目标可用率低于门槛（含"全部无 DWARF"、"只有一个 CU 有 DWARF"、"缺失 DWO"、"错误的调试文件但少量地址偶然命中"）；`usable=0`；裁剪后没有可写 profile；丢失比例超过门槛；
   - 不认识的行、截断的行、损坏的整数；pid/tid 小于 -1；超大 period 导致的溢出；
   - `--perfdata` 时 PATH 中放一个非 0 退出的假 perf，工具必须失败；不满足 5.2.4 准入时 `--perfdata` 报错；
   - 不加 `--ip-samples` 时纯 IP 输入仍报原错误；
   - 5.1.3 中每个"报错"选项；未开启 `--ip-samples` 时使用 IP 专属选项；未指定 `--ip-aggregation`；
   - 没有映射符号时启用 `avg`、补零或 `prev-inst`（整次失败，`--output` 未生成）；数据恰好能解码为合法指令的 literal pool；长度规则步进越过区间末尾；DWARF 区间起点切入 32 位 Thumb 指令中间；A32/A64 起点落在 4 字节指令中间（不对齐，或与锚点的距离不是 4 的倍数）；交集末端截断一条指令；同址冲突的映射状态；节内没有起始映射符号；
   - 带 probe 的二进制在 IP 模式下被拒绝，加与不加 `--use-dwarf-correlation` 各一条；`-fpseudo-probe-for-profiling` 构建拆分后的三种形态（两节只在运行文件中、只在调试文件中、只剩 `.pseudo_probe_desc`）都被拒绝；普通 DWARF 输入加 `--use-dwarf-correlation` 仍按约定工作；
   - 生成阶段的库内退出：`--debug-binary` 指向 ELF 头完整、但 `.debug_info` 被截断的文件，使加载成功、第一次符号化失败；加载完成后删除调试文件（模拟打开失败）。两条都检查非 0 退出、报告中 `failure_stage=generate`、`--output` 未生成、旧 profile 不变；
   - `--format=gcc` 在 IP 模式下失败，`failure_stage=write`；
   - 输出：报告路径不可写、报告写入或关闭失败、writer 创建失败、profile 序列化失败、延迟到 flush 才出现的写入失败、close 失败、最终改名失败、profile 与报告指向同一文件（含别名）、`--output -`、加载失败（损坏的 ELF，报告中 `failure_stage=load`）；每项都核对 `failure_stage` 正确、诊断不递归、没有因流析构触发的 fatal、临时文件已清理，并预置旧 profile 检查其内容不变。不能只测试 `Writer::write()` 立即返回错误的情形。
6. 板上集成用例（不能用 lit 代替，因为 fork 与 exec 的映射由 perf 解析）：spike 的变体在不 exec 的情况下 fork 出子进程继续计算；同一进程 exec 到不同映像；运行期间替换库文件得到真实的 `(deleted)` 输出；采一次触发内核模块代码的样本；一次系统级录制（含 `-1/-1` 样本）。07、09 报告已用一次性原型得到这些情形的真实样例，正式实现的验收仍用实现本身重跑。按 05 报告 B.3 的方法核对 dsoff，并保存原始事件与导出结果作为素材。
7. 规模：用 libavcodec 记录工具的峰值内存与耗时，作为第二批 Chromium 规模（6.2）的外推基础。

### 5.11 第一批交付物

1. 补丁序列（基于 `f999bd40`），每个补丁可独立编译、测试通过，按以下顺序拆分：
   1. 测试输入（预生成二进制与 perf 文本素材）；
   2. IP 读取器与 dsoff 地址换算；
   3. 身份校验（证据等级、保守汇总、分离调试文件身份链）；
   4. IP 加载策略与 `ProfileGenerator` 中的 IP 填充（整数聚合、取整、head、补零、skid）；
   5. 按需指令边界枚举（映射符号切换与 Thumb 长度规则）；
   6. 质量报告与失败契约（含输出提交顺序、自建 writer 及 profile 流的显式关闭检查、覆盖整个 IP 流程的库内退出兜底回调与各阶段的失败记录）；
   7. 文档（`docs/CommandGuide/llvm-profgen.rst` 与报告 schema）。
   probe 子方案是独立的实验补丁，通过准入前不并入序列。`--perfdata` 在满足 5.2.4 准入后才并入。
2. 独立核对脚本与质量评估脚本（放本项目仓库 `tools/`；IR 匹配脚本在原型基础上按 5.8 第 3 条的语义校验重写）。
3. 实现报告：回归结果、新增测试、独立核对结果、5.8 评估数据与默认值决定、5.9 性能数据、消费端匹配证据、probe 准入结论、`--perfdata` 准入结论、已知局限。
4. llvm 包的一次正常（非增量）GBS 构建记录。
5. 冻结前验证的证据（05–09 报告及第 10 节步骤 1 的剩余项）。

### 5.12 多份 profile 合并（第一批验证现有能力）

1. 不在 llvm-profgen 增加多输入选项。每份采样单独生成 profile，再用已有的 `llvm-profdata merge --sample --weighted-input=<权重>,<文件>` 合并（`llvm-profdata.cpp:108–112`、`:171–173`）。权重必须是正整数（`:1707–1718`），调用方规划权重时按需取整。
2. 这是 profile 层的加权融合，不保证与"原始样本合并后再生成"等价：
   - `max` 不满足等价性：同一位置两条指令，输入 A 为 (10, 0)、输入 B 为 (0, 10)，分别取 MAX 后相加得 20，先合并再取 MAX 得 10。
   - `sum` 只在未取整的整数分子层具有可加性。写出的 profile 经过取整与"被采到至少为 1"的规则，合并结果与先合并再生成可能不同（例如 0.3 + 0.3：分别生成再合并为 1 + 1 = 2，先合并再生成为 1；每份 profile 每个键最多差 1）。head 估计与裁剪也不一定与合并交换次序。
   - 只有贡献为整数、相关非线性处理关闭或已证明可交换时，才对明确限定的字段声明等价。
3. 合并前由调用方依据报告核对：事件名、权重方式、P_ref、聚合方式、head、补零、skid、构建身份、MD5 与格式一致。工具不会自动替调用方检查报告。
4. 同一次采集的分片若要求合并结果与整体生成一致，需要地址级的原始计数合并，不在第一批，需要时另行决策（6.5）。
5. 验收用例：上述 MAX 反例；`sum` 的受限等价情形；分数取整（0.3 + 0.3、0.6 + 0.6）、最小值与裁剪的不等价反例；P_ref 或事件不同的两份 profile 由核对脚本拒绝。

## 6. 第二批：规划（第一批完成后再出详细设计）

| 项目 | 目标 | 第一批需要预留或提供的 |
|---|---|---|
| 6.1 内核 profile（vmlinux 与模块） | vmlinux：用内核 mmap 记录中 `_text`/`_stext` 等重定位参考符号的运行地址（内核合成 mmap 的 pgoff 存放该地址，`tools/perf/util/synthetic-events.c:1154–1177`，MMAP2 在 :1161、MMAP 在 :1174）与 vmlinux 中同名符号的链接地址求 `slide = runtime_anchor − linked_anchor`，`elf_va = ip − slide`；校验锚点、可执行范围与内核身份，缺锚点或地址被隐藏时明确失败；`--pid` 不得因此丢弃 pid=-1 的全局内核映射。模块（ET_REL）：按"模块名 + build-id"识别，按节换算；核实 dsoff 对模块的语义；模块地址不归入 vmlinux。设计中必须说明消费路径（clang 构建的内核与 AutoFDO 支持） | 第一批的内核样本分类；地址键保留"对象身份 + 节"的扩展能力 |
| 6.2 大规模二进制（Chromium） | 峰值内存与耗时目标；分阶段释放缓存 | 第一批的 libavcodec 内存与耗时数据 |
| 6.3 冷函数符号列表 | 在现有 `--populate-profile-symbol-list` 上增加按函数大小覆盖率的选取策略。冷函数列表必须由明确的工作负载覆盖声明或独立的覆盖证据支持：身份校验与样本量是必要条件，不是充分条件。默认不根据"未采到"推断冷函数；尺寸覆盖率只用于压缩已确定的候选集合。与 `-fprofile-sample-accurate` 互斥（消费端开启后者时忽略符号列表），评估时二选一 | 第一批禁用；报告提供样本量指标 |
| 6.4 IP 模式阈值与裁剪 | 优先复用已有的 `--trim-cold-profile` 与 summary 阈值（`trimColdProfiles`，`L/ProfileGenerator.cpp:539–554`；阈值计算在 :1186–1194）。只有已有机制无法表达的需求（例如样本可靠性过滤）才新增策略，而且可靠性不能只看 period 加权后的数值大小 | 第一批记录已有裁剪在 IP 模式下的效果 |
| 6.5 地址级原始计数合并（可选） | 只在同一采集的分片需要与整体生成结果一致时立项 | 5.12 的结论 |

## 7. 第三批：登记（条件具备后立项）

| 项目 | 立项条件 | 备注 |
|---|---|---|
| ARM SPE 输入 | 有带 SPE 的板子 | SPE 是统计采样，不是连续 trace；不能套用 LBR 区间假设 |
| BRBE | 有带 BRBE 的板子 | 先验证 perf 输出的分支记录能否直接走现有 LBR 解析，不预先承诺新 reader |
| Propeller 布局 profile | 有分支栈（LBR/BRBE）数据，且目标支持 `-fbasic-block-address-map` | 准确表述：clang 驱动只对 X86 与 AArch64 的 ELF 放行该选项（`Clang.cpp:6179–6187`），后端实现本身与指令集无关。涉及 CFG、布局算法与链接器消费，属于独立子系统 |
| 预取 / LLC miss 提示 | clang 出现可用的消费端 | 当前 clang 不使用这类信息，暂不实现 |
| 原生 perf.data 解析（由第二批降级） | 板上导出文本无法满足需求（例如 perf 不支持 dsoff，或导出吞吐不够），或主机长期没有可用 perf 而又需要在主机直接读 perf.data | 直接读 header、attr、MMAP2、COMM、FORK、EXIT、SAMPLE、build-id 表、丢样记录；同时实现自建的进程地址空间代际与映射（参照 BOLT `DataAggregator.cpp:1800–1885`、`:1963–2046`）。LLVM 内没有先例，BOLT 也调用 perf script（`DataAggregator.cpp:213–235`）；工作量与维护成本大，上游的实际接受度未核实，以 RFC 反馈为准。接口约束：读取层对上游只暴露"样本流（pid, event, period, dso, 文件偏移）+ 身份信息" |

## 8. 超出 create_llvm_prof 的增强（汇总）

以下是设计目标；每项效果以实现报告中的实测结果为准，未通过的能力标为实验或未交付。

| 增强 | 作用 |
|---|---|
| 结构化质量报告，分别判定转换有效性、身份等级与采样门槛 | 调用方可依据报告判断 profile 能否使用，不只靠退出码；不宣称采样充分，不对收益作判断 |
| 显式事件与 period 加权，整数精确累计与统一归一化 | create_llvm_prof 的 IP 模式每个样本计 1，不按 period 加权（`sample_reader.cc:292–302`）；归一化避免 clang 中分支权重饱和 |
| 由 perf 按线程解析映射（dsoff），换算与页大小无关 | 多进程（fork + exec 启动）已在 RPi4 与 RPi5 实测（05、09 报告）；不 exec 的 fork 与 exec 替换已由一次性原型在 RPi4 实测（07 报告），正式验收由板上集成用例确认 |
| build-id 不匹配时失败报错；身份证据分级与保守汇总；分离调试文件身份链 | Google 也做 build-id 匹配（`sample_reader.cc:276–287`），但不匹配时返回空结果而不报错 |
| head 估计选项与消费端语义检查（入口计数、权重饱和、覆盖率、LTO 链接步骤） | 让 profile 在 clang 中的实际效果可查 |
| 默认策略以局部分支概率、执行加权的行级参考、独立输入上的性能与统计判据共同决定 | 用数据而不是假设决定 IP 计数规则 |
| ARM Thumb-2 与 A32 支持（按需指令边界不依赖子目标） | create_llvm_prof 默认构建不含 32 位 ARM；Tizen LLVM 镜像的 armv7l 包默认是 Thumb |
| 编译端组合评估（profi、head、stale matching） | 无需改 clang，给出推荐配置 |
| pseudo-probe IP 模式（实验，准入后才交付） | 评估不同代码变化下的复用范围，不保证保留比例 |

## 9. 工具的输入与输出约定

本节只描述 llvm-profgen 自身的输入输出，不涉及调用方如何使用。

1. 输入：
   - 板上按 5.2.2 导出的 perf script 文本（第一批的主输入）；满足 5.2.4 准入时也可以是 perf.data；
   - 采集要求：推荐 `perf record --buildid-mmap`；也可默认录制并在板上导出 `perf buildid-list`；`-c` 或 `-F` 均可；
   - 实际被采样的 ELF（程序头与代码字节完整，可以是 strip 后的），以及内嵌的、或通过 `--debug-binary`/DWO/DWP 提供的匹配调试信息；启用按需功能时，调试文件需含映射符号。采样映像身份、ELF 加载布局与调试信息的对应关系必须可验证，不要求 strip 前后的文件整体字节相同。采样对象来自已安装的 RPM 时，用该安装产物及同一次打包的 debuginfo：打包时 `find-debuginfo` 可能重算 build-id（第 1 节第 6 条），不得未经核对就用打包前的 BUILD 产物替代。工具只按 build-id 判定，不按目录判定（5.3.3 第 9 条）；
   - 身份校验只涉及被采样的映像及其调试文件（5.3.3 第 9 条），与使用 profile 的构建无关。使用 profile 的构建可以采用不同版本的工具链（例如从已发布的 N 版本采样，用于 N+1 版本的构建），由此带来的函数命名、调试关联与代码失配由消费端的覆盖率检查与 stale matching 体现（5.9）；受控评估（5.8、5.9）内部固定工具链版本、源码路径与公共编译选项，目的是控制匹配率与实验变量，不是为了让两次构建的 build-id 相同；
   - 构建要求：被采样的构建与使用 profile 的构建，都在 `%{optflags}` 之外追加 `-fdebug-info-for-profiling -funique-internal-linkage-names`（前者提供 discriminator，5.4.4 的 duplication 处理依赖它；后者生成的名字后缀取决于源文件路径，`CodeGenModule.cpp:509–518`），两次构建的源码相对路径相同；第一批 DWARF 路径的构建不加 `-fpseudo-probe-for-profiling`；
   - 被采样的构建链接时生成 build-id：LLVM 包打开 `ENABLE_LINKER_BUILD_ID` 并发布后（第 1 节第 6 条），由 clang 默认生成，无需另加（以产物为准，发布后复核）；发布前的评估构建显式加 `-Wl,--build-id=sha1`（08 报告已验证）。clang 默认的 `--build-id` 在链接命令中排在 `-Wl,` 参数之前（`Gnu.cpp:331` 加入默认选项，`:452` 才加入链接输入与 `-Wl,` 参数）；lld 取最后一个 `--build-id`（`lld/ELF/Driver.cpp:972`）；GNU ld 的行为未在源码中核实。最终 build-id 以打包后的文件为准；
   - 可选：`perf buildid-list` 输出；事件名。
2. 输出：profile 文件（extbinary 等已有格式，不支持写到标准输出）；可选的质量报告 JSON（5.6）。
3. 退出码：5.6.3 规定的失败条件返回非 0，此时不生成、不覆盖 profile；返回 0 时，详细质量信息以报告为准。

## 10. 实施步骤与评审节点

| 步骤 | 内容 | 节点 |
|---|---|---|
| 0 | v0.5 第三轮评审（已完成，附录 E）；v0.6 限定范围复核（已完成，附录 F），修订为 v0.7 | 已完成 |
| 1 | 冻结前验证（一次性原型与素材，不构成正式实现）。已完成项见附录 B、D、E。★ 为第一阶段冻结的前置条件，**全部 ★ 项已闭合**：<br>已由 07 报告完成：调试文件保留映射符号与 `.ARM.attributes`、代码节为 NOBITS；Thumb 边界在 libavcodec 最大的 20 个 Thumb 函数上与 `llvm-objdump --triple=thumbv7a -d` 逐条一致（132,859 个起点，A32 只覆盖到 3 个启动代码片段，由 lit 的 A32 fixture 补足）；不 exec 的 fork、exec 替换、`(deleted)`、内核模块的真实样例；平台默认链接不生成 build-id 的原因。<br>★ 已由 08 报告闭合：当前工具链显式 `-Wl,--build-id=sha1` 构建，拆分后运行文件与调试文件的 build-id 都是可读的 SHT_NOTE、20 字节一致，`.build-id` 链接正确。08 未验证 DWARF5 行表质量，未重跑指令边界。<br>★ 已由 09 报告闭合：RPi5 的 dsoff 输出与公式核对（单进程、双进程均 100%）、`--buildid-mmap`（libc 的 MMAP2 build-id 与 ELF 一致）；RPi5 页大小 4096。<br>非 ★，交付前（步骤 9 之前）完成：LLVM 打开 `ENABLE_LINKER_BUILD_ID` 发布后，用新工具链原样构建复核默认 build-id 与拆分结果；aarch64 的 Tizen debuginfo 是否保留 `$x`/`$d`（5.7.2 第 2 条）；用 GBS 打包一个 `-fpseudo-probe-for-profiling` 构建，记录 `.pseudo_probe`/`.pseudo_probe_desc` 拆分后位于哪个文件（5.1.4 第 3 条）；把第三轮评审实测的 DWARF5 拆分核对（行表逐行、抽样符号化、`comp_dir`）与 BUILD 目录产物 build-id 不同的结果补存为仓库证据；`[unknown]` 的真实样例（未出现时按源码格式编写素材）。<br>第二阶段前（可选，只用于描述性的分支概率指标）：按 5.8 第 3 条重跑 IR 匹配，试验共同转储点；验证 BFI 块计数恢复方法；<br>是否获取主机 perf（用户决定，5.2.4） | 证据评审 |
| 2 | 第一阶段冻结：正确性规则与契约（5.1–5.4、5.6、5.7、5.10–5.12） | **已冻结（v0.7）**，可以开工 |
| 3 | （可选）在 discourse.llvm.org 发 RFC，征求选项命名与整体方案意见。是否发、何时发由用户决定 | 用户决定 |
| 4 | 实现补丁 1–7；回归与新增测试；独立核对；板上集成用例。实现与第一轮采集中另增补丁 8（GNU 汇编 Thumb 调试信息规范化）与补丁 9（非叶子行号 0 整体排除），见附录 G.1.8、G.1.9 | **已完成**：补丁 1–9 验收，正式工具 SHA-256 `2e8895af…d0d5`（附录 G.5） |
| 5 | 5.8 质量评估（RPi5 与 RPi4） | 进行中：RPi4 第一轮 70 组采集完成并用补丁 9 重转；插桩与覆盖参考已取得；登记前的静态产物（完整身份清单、对应表、映射表、U、对象登记表）已按裁决 1–4 生成（附录 O.3，v1.6 规则；本版规则下须重算）。本版评审通过后：按 5.8 第 6 条的数据规则实现评估脚本与夹具；只用 ELF、调试文件与参考数据预先生成映射表、排除清单、U、权重与对象登记表；完成附录 Q.5 的核对（第 12 项需要板子，加装散热后）；登记并推送预注册修订 3；之后按 RUN 槽位表补采（每层 15 个 RUN，写入数据收据）并计算质量矩阵。RPi5 待板子就绪 |
| 6 | 5.9 性能与过期复用测试 | 结果评审 |
| 7 | 第二阶段冻结：默认参数（聚合方式、head、补零、skid、各门槛）。评估判据（映射表与比较总体 U、M1/M2 定义、合并口径、等价区间、固定样本量与区间、合格判据、负对照要求）在计算任何正式 sample profile 指标之前由预注册修订 3 登记，不在本步骤再改；结构覆盖只报告 | 评审 |
| 8 | probe 子方案：细化设计、实验补丁、准入评估（5.5） | 准入评审 |
| 9 | 正常 GBS 构建；整理补丁序列；确认步骤 1 的非 ★ 交付前项已完成 | 交付评审；由用户决定 Gerrit 合入方式与时间 |
| 10 | 第二批详细设计 | 另行评审 |

1. 每个冻结节点列出已决事项、验收证据与剩余的实验项。"后续评估"不能代替必须成立的正确性规则。
2. 步骤 1 中 ★ 以外的剩余项可与步骤 0 的评审及后续实现并行；★ 项的结果必须在第一阶段冻结之前取得，若与设计不符，在冻结前修订（09 报告发现的 `-1/-1` 已按此修订进 5.2.3 第 8 条）。尚未发布的工具链默认行为不作为第一阶段冻结的前提，已验证的显式 sha1 路径可以先行使用。
3. 每项证据记录架构、实际编译命令、优化级别、ISA 与 profile 来源；旧原型的百分比不沿用为新规则的结果。
4. 默认值未确定期间的实验选项，不自动成为稳定的命令行接口。
5. probe 未通过准入，不阻塞已通过验收的 DWARF 路径。
6. Agent 的设计与开发在 llvm-profgen 增强完成（至少第一批交付）之后开始，不与本表的步骤并行。

## 11. 风险

| 风险 | 影响 | 对策 |
|---|---|---|
| 无分支信息的 AutoFDO 收益明显低于 LBR 情形，可能低于插桩 PGO | 增强的实际价值受限 | 5.8、5.9 如实给出收益，"未证明改善"是允许的结论 |
| profile 结构合法、可用率高，但关联到错误位置 | 静默的错误优化 | golden fixture、两类地址扰动负对照、消费端匹配验证（5.10） |
| 大面积缺失调试信息被比率掩盖 | 错误地判定输入有效 | 以目标可用率判定；`outside_dwarf_func` 分类报告；`usable=0` 失败（5.6.2、5.6.3） |
| 多进程、fork 或 exec 导致地址换算错误 | 计数错位 | 由 perf 按线程解析（dsoff），不使用全局基址（5.3.1）；双进程已实测，fork 与 exec 由板上集成用例确认 |
| perf script 文本格式变化，或板上 perf 不支持 dsoff | 输入不可用 | 严格解析、遇到未知格式即报错；以实测输出为素材；第三批的原生解析作为后备 |
| `(deleted)` 等路径解析出错 | 目标样本被误归为其他 DSO | 按固定字段顺序解析 DSO 字段（5.2.3 第 2 条） |
| 主机没有可用 perf | `--perfdata` 无法交付 | 第一批以板上导出文本为主输入；`--perfdata` 有条件准入（5.2.4） |
| 计数单位导致分支权重饱和，或提前取整带来误差 | 分支概率被压平或失真 | 整数分子聚合后统一归一化（5.4.1、5.4.4）；IR 饱和检查（5.9） |
| 不写 head 且关闭 profi（含 LTO 链接步骤）时入口计数为 1 | 函数入口被判为冷 | 推荐配置编译与链接两步都保持 profi；`entry-estimate` 选项；G1–G4 分组验证 |
| 稀疏 IP 被解释为明确的冷代码 | 错误的冷代码优化 | 默认不补零、禁用符号列表、不推荐 `-fprofile-sample-accurate` |
| 热点在 NEON 汇编中 | 可用率与收益被压低 | `outside_dwarf_func` 分类统计并写入结论（`in_cu_no_subprogram` 只提示、不证明汇编来源，5.4.2）；门槛按真实库确定 |
| skid 使计数前移 | 块计数偏差 | `--ip-skid` 维度评估；局限写入文档 |
| 现有库无 build-id 或已 strip | 身份无法验证、无法符号化 | 评估使用按第 9 节重新构建的库；分离调试文件身份链 |
| ELF 没有 `.ARM.attributes`，解码器退化为不带版本的 `arm` | Thumb-2 32 位指令解码失败 | 边界枚举改用编码长度规则，不依赖子目标；MCDisassembler 只作交叉核对且子目标来源固定（5.7.2） |
| 调试文件不含映射符号 | 按需功能不可用 | armv7l 的 Tizen debuginfo 已确认保留（07）；aarch64 在交付前确认；不可用时按需功能整体失败，函数符号的 `SF_Thumb` 只用于 `isa` 统计 |
| 映射状态跨节继承，或 DWARF 区间起点落在指令中间 | 指令边界错误，`avg` 分母、补零与 skid 出错 | 映射状态按节查找、不大于起点、同址冲突即失败；DWARF 区间与映射区间求交后，按各自的 ISA 从当前映射区间的锚点证明起点，不跨状态步进（5.7.2 第 3、4 条） |
| IR 层对齐只覆盖部分分支，或候选键相同而语义不同 | 评估指标失真 | 严格候选验证、操作数等价定义、条件规范化、switch 先校验选择值再按 case 值配对、`unknown` 处理（5.8 第 3 条）；本次参考自比只有 3/22 可严格比较，主指标改为行级 M1、M2，分支概率误差只作描述（5.8 第 4、5 条） |
| 行级指标的盲区（行间代价、一行多块、内联上下文、head 与补零） | 指标好不代表计数正确或配置最优 | 明确盲区；一行单区域的敏感性分析；head 与补零只由 5.9 评估；M1 最高者不自动视为最优（5.8 第 5、9 条） |
| probe 到地址的映射不正确 | probe 计数偏差 | 独立准入；正确性不过则不进正式包（5.5） |
| `-fpseudo-probe-for-profiling` 本身影响优化 | 收益被抵消 | G6 单独测量 |
| 多次采样结果不稳定 | 默认值决策不可靠 | 重复采样、固定样本量、差值置信区间与等价区间、样本预算敏感性分析，不只重复计时 |
| 评估侧的键计算或函数名与工具不一致，跨侧对应出错，或 U 随样本变化 | 指标的分母漂移，计数被静默丢弃或误归为范围外 | 映射表、对应表与 U 只由 ELF、调试文件与参考数据生成并登记 SHA；函数名按工具写法、按名字取闭包；跨侧按文件与名字对应，单候选须有定义身份证据，多候选默认歧义，未插桩须有编译单元级的正面证据，对应表须覆盖整个 ELF 的每个函数；条目分类中对应未决与未对齐都使指标无定义；登记前做合成全地址核对与地址关系核对（5.8 第 5 条、附录 Q.5） |
| 参考侧把同一定义的各编译单元副本当成不同源函数 | 最热的代码被判歧义移出 U | 按定义文件、去后缀的名字与起始行合并副本；③ 按固定分母计算，低于 50% 时不登记（5.8 第 5 条、附录 Q.5） |
| RUN 数少、按区间宽度补采或加轮、某个阶段的差值全部为 0、稀有的大幅偏离没有被观测到 | 区间覆盖不足，等价结论偏乐观 | 质量每层固定 15 个 RUN、按阶段分层，percentile 与 t 区间同时满足，任一阶段差值极差在 10⁻⁹ 以内即判证据不足；登记工作模型，稀有偏离作为局限随每个等价结论披露；验收场景（显式清单，t 区间 10⁶ 次重复）不达标时按预先登记的规则关闭等价判读；性能按公式固定轮数 N（5.8 第 6 条、5.9 第 5 条、附录 Q.5） |
| 参考计数权重集中在少数函数，或热点行很少 | M1 实际只反映一两个函数；M2 太粗 | 按参考数据预先登记 n_eff 与 K；K < 50 的对象先判为只作描述；其余对象 n_eff < 3 或为 null 时只用 M2 判读（5.8 第 5、6、9 条） |
| 遥测采样进程被负载推迟 | 读数缺口使大量轮次判 unknown | root、nice 0、绑核；缺口按观测流与窗口定义，允许的缺口只记告警；板上试运行与判定标准（5.9 第 5 条、附录 Q.5） |
| 登记前用真实 profile 调试脚本 | 提前看到正式比较的结果 | 同一 ELF 的真实 profile 登记前只转换基准配置、只做键覆盖与冒烟，不计算任何受控量，并披露（5.8 第 6 条） |
| 测量噪声与热降频 | 性能结论不可靠 | 10 轮以上、固定 governor、记录频率与温度、置信区间（5.9） |
| RPi4 散热不足，多核负载很快达到约 80°C | 多线程场景与性能测量出现降频，结论不可靠 | 加装散热片与风扇，测量前复测四核满载温度；按 5.9 的合格判据逐轮判定（附录 G.5.4） |
| PMU 周期数与 task-clock 之比在部分负载上低于固定频率，原因未确定 | 按有效频率判据，现有遥测未见异常的轮次也会被判为异常；若原因是固件限频，现有遥测又可能看不到 | 合格判据改为逐秒的内核频率、固件时钟、温度、欠压告警与批次前后校准；有效频率作为组间平衡的协变量（5.9 第 5 条、附录 G.3） |
| 欠压告警由驱动每 2 秒清除一次 | 只读端点会漏掉运行中途的欠压 | 逐秒读取并检查 dmesg 欠压事件（5.9 第 5 条） |
| 开发主机由多条工作线共用，可用内存长期偏低 | 主机任务被 OOM 终止或挤崩其他进程 | 主机任务分级限额与运行中监测（附录 G.2.4） |
| 构建 flags 与路径不一致 | profile 匹配率下降 | 第 9 节构建要求；消费端覆盖率检查与路径不一致的负对照 |
| 把与被采样映像 ID 不同的文件（打包前的 BUILD 产物、用 profile 重建的 ELF）误作被采样的 ELF 输入 | 身份校验失败 | 保留实际被采样的产物及其匹配的 debuginfo；身份只按 build-id 校验被采样映像，不按目录（5.3.3 第 9 条、第 9 节） |
| 目标 ELF 或调试文件被去掉了 build-id note | 若当作"缺失"，`--allow-missing-build-id` 会放行可以证明不是同一文件的输入 | 一方有 ID、另一方没有判为 `mismatch`（5.3.2 第 3 条） |
| 共享代码内部经 `exitWithError` 直接退出（例如生成阶段第一次符号化时调试文件打不开） | 不写报告、临时文件残留，绕过失败契约 | 覆盖整个 IP 流程的兜底回调按当前阶段写失败报告（5.6.3 第 3 条） |
| probe 节在调试拆分后只留在调试文件中 | probe 构建被当作普通 DWARF 构建处理，且没有提示 | 在 `--binary` 与 `--debug-binary` 中都检测（5.1.4 第 3 条）；拆分后的位置在交付前核实 |
| 使用 profile 的构建更换了工具链 | 函数命名、调试关联与代码变化使 profile 失配，优化效果下降 | 不影响身份判定；由消费端覆盖率与 stale matching 体现（5.9 第 3、6、7 条）；评估内固定工具链 |
| 调试文件中 DWARF5 内容未被 debugedit 处理 | 源码路径或行表可能不完整，影响符号化 | 第三轮评审对 08 构建的 libavcodec 核实行表与抽样符号化一致（第 1 节第 6 条，待补存证据）；其他库在评估中以目标可用率实测 |
| 文本中只能看到 `PERF_RECORD_LOST`，且其计数混有边带记录 | 丢样比例既不是 IP 丢样的上界也不是下界；边带记录丢失可能使映射不完整 | 比例只作输入级诊断代理，超过门槛时按"未满足输入质量门槛"失败；报告标明 `count_unit=records`、`completeness=unknown`，有 LOST 时告警并标 `mapping.completeness=unknown`（5.2.3 第 7 条） |
| 系统级录制中的负 pid（`-1/-1`） | 严格解析把真实输入判为格式错误 | 按带符号整数解析，-1 记为进程未知（5.2.3 第 8 条） |
| 与 BOLT/PGO 线同时修改 llvm 包 | 补丁冲突 | 独立分支开发；合入前由用户协调顺序 |

## 12. 第二阶段冻结前待定的问题

第一阶段已在 v0.7 冻结；v0.6 第 12 节十个确认问题的意见与处理见附录 F。以下是第二阶段（评估之后）需要确定的事项，第一阶段的实现不依赖它们的结论：

1. `--ip-aggregation` 的默认值（`sum` / `max` / `avg`），以及证据不足时是否按 5.4.4 第 5 条保守选择 `max`。聚合方式与 skid 的正式结论只取 K ≥ 50 且 n_eff ≥ 3 的对象，spike 只作方向性描述；质量等价判读按预先登记的规则关闭时，由保守规则与性能结果决定（5.8 第 6、9 条）。
2. `--ip-head-samples`、`--ip-zero-fill`、`--ip-skid` 的默认值（5.4.6–5.4.8）：skid 由 5.8 与 5.9 共同确定；head 与补零不由 5.8 的行级指标区分，由 5.9 的消费端检查与性能测量确定（G1–G4 按补零展开，5.9 第 2 条）。
3. 三个门槛（`--ip-min-usable-ratio`、`--ip-min-target-samples`、`--ip-max-lost-ratio`）是否设默认值及取值，按真实库的汇编占比确定（5.6.2）。
4. 5.8 的评估判据：v1.5 已定义参考侧源函数的合并、跨侧对应表、映射表与比较总体 U（含 ③ 的分母）、条目分类、M1、M2、M2b、对象登记表、合并口径与敏感性、ε=±0.02、判读方式与结果名称、固定样本量与阶段分层、区间与退化规则、工作模型与等价结论的限定、预先登记的回退、有效 RUN 与重采、停止与恢复的状态机、受控量、登记内容的划分与门禁（5.8 第 5、6 条），在计算任何正式 sample profile 指标之前由预注册修订 3 登记；BFI 块计数恢复方法是否可用仍未验证，只影响描述性指标。
5. 5.9 的合格判据、散热前置条件与性能的固定轮数 N（5.9 第 5 条），随预注册修订 3 登记。
6. 预注册修订 3 的登记（附录 G.3）：在本版确认、附录 Q.5 的核对完成（含模拟与 `quality_equivalence_enabled` 的取值）、对应表、映射表、U 与对象登记表等产物生成之后，对任何正式 sample profile 计算质量指标之前单独提交并推送。
7. 是否在 discourse.llvm.org 发 RFC，以及 `--ip-samples` 的最终命名（第 10 节步骤 3）。
8. probe 子方案的准入（5.5），以及是否为 x86_64 主机构建 perf、让 `--perfdata` 进入交付（5.2.4，用户决定）。

---

## 附录 A：v0.1 评审意见处理

来源缩写：K = Kimi Code，C = Codex，CC = Claude Code。v0.3、v0.4 中因板上实测或后续评审而改变的处理，在表中注明，详见附录 B、附录 C。

### A.1 严重

| 问题 | 来源 | 处理 | 位置 |
|---|---|---|---|
| 地址换算：全局基址、无 pid/fork/exec、4K 掩码，多进程或 fork 时静默出错 | C 5.2-1、5.3-1；CC S1；K 5.3 | 采纳 CC 方案 A（perf dsoff + PT_LOAD 公式，与页大小无关），公式与 C 一致；C 的地址空间代际与 CC 的方案 B 作为第三批后备；K 的"修正共享代码中的页大小"不采纳（改为新路径不使用该逻辑，LBR 路径不动，满足 C1）。双进程已实测 100% 一致；fork 不 exec 与 exec 替换待板上集成用例（v0.4，附录 C） | 5.2.2、5.3.1、第 7 节 |
| 全量反汇编：Thumb 必然解错、strip-all 下 addressIsCode 全假、FS 检测在反汇编内 | K 第 4 节；C 4-1；CC 4-3 | 采纳：IP 专用加载策略第一批即实施，跳过全量反汇编；FS 检测改为按符号名在两份 `.symtab` 中查找（v0.4）；K 提出的"按 .debug_line 行数计 avg 分母"不采纳（行表行数不等于指令数） | 4.3、5.4.4 |
| Thumb bit0 的对象说错 | K 5.7；C 5.7-1；CC 5.7-1 | 采纳：样本 IP 不带 bit0，符号地址由 LLVM 清除。CC 的"Tizen 默认 A32"经实测不成立（v0.3）；Thumb 边界改用编码长度规则、ISA 用 `SF_Thumb` 标志（v0.4） | 1.6、5.7 |
| period 加权导致分支权重饱和 | CC S2 | 采纳 P_ref 归一化；v0.4 补充整数精确累计、统一取整与 P_ref 自动取值规则 | 5.1.1、5.4.1、5.4.4 |
| 不写 head 时非 profi 路径入口计数为 1 | CC S3；K 5.4 | 部分采纳：clang 驱动在编译作业中默认注入 profi；v0.4 补充 LTO 链接步骤不注入、`entry-estimate` 直接调用 `getHeadSamplesEstimate()` | 1.6、5.4.6、5.9 |
| IP 权重语义与 duplication 未定义 | C 5.4-1；CC 5.4-2 | 采纳 CC 的推导（sum 不乘，max、avg 乘）与 C 的语义说明；v0.4 修正推导列的表述与 `n(k)` 定义 | 5.4.1、5.4.4 |
| 最近前置 probe 不是可靠映射 | C 5.5-1；K 5.5；CC 5.5-1 | 采纳 C：probe 改为独立实验子方案与准入；CC 的 M1 与 C 的 BB address map（M2）为候选；K 的"函数归属前置"与"块不分裂"表述修正 | 5.5 |
| 内核 KASLR 不能套用用户态模型 | C 5.7-2；CC 5.7-3 | 采纳 CC：内核 profile 生成移到第二批；C 的 slide 公式写入 6.1 | 5.7、6.1 |
| `.profdata` 不是逐块真值表 | C 5.8-1；K 5.8；CC 5.8-1 | 采纳 IR 层比较；v0.4 起 IR 层只用于局部分支概率，执行加权的评价改用 llvm-cov 行级参考，块级指标待恢复方法验证 | 5.8、5.10 |
| 编译端分组存在等价组与混杂因素 | C 5.9-1；K 5.9；CC 5.9-1 | 采纳 C 的显式 profi/salvage 控制与 CC 的分组及消费端检查；v0.4 补 LTO 链接步骤 | 5.9 |

### A.2 重要

| 问题 | 来源 | 处理 | 位置 |
|---|---|---|---|
| C1 措辞与验证范围；不存在独立 ETM reader；共享代码改动 | C 3-1；CC 3-1；K 第 3 节 | 采纳 C 与 CC 的合并表述；v0.4 调整比对矩阵（gcc 写出不支持、CS/probe 不支持 binary） | 第 3 节 |
| C3、C5 的验证方式 | C 3-2；CC 3-2 | 采纳 | 第 3 节 |
| 选项冲突矩阵；`--use-dwarf-correlation` 不是 LBR 专属；probe 开关方向 | C 5.1-1；CC 5.1-1、5.1-2 | 采纳 CC 的矩阵，沿用现有 probe 约定；不采纳 C 的显式 `--ip-use-probes`，但采纳其"probe 未验证前不得静默生效" | 5.1.3、5.1.4 |
| 丢样改用 `--show-lost-events`；未知不得写 0 | K 5.2；C 5.2-2；CC 5.2-5 | 采纳；LOST 格式已实测（v0.3）；v0.4 增加丢失比例门槛 | 5.2.2、5.2.3、5.6 |
| MMAP2 build-id 需 `--buildid-mmap`，与 buildid-list 互斥 | K 5.3；CC 5.2-2 | "互斥"经实测不成立（v0.3）；v0.4 改为证据来源与身份等级分开，buildid-list 为路径级证据 | 5.2.1、5.3.2 |
| build-id 一致性、改名、跨 pid 歧义、`(deleted)` | C 5.3-2；K 5.3；CC 5.3-2 | 采纳三方合并规则；v0.4 补充保守汇总与 inode 歧义检查 | 5.3.3 |
| 分离调试文件身份链 | C 5.3-3；CC 5.3-1 | 采纳；v0.4 明确指令字节取自 `--binary` | 5.3.4、第 9 节 |
| 文本语法、严格解析、perf 退出码 | C 5.2-2；CC 5.2-3、5.2-6；K 5.2 | 采纳；v0.4 改为按固定字段顺序解析 DSO 字段 | 5.2.2–5.2.4 |
| 不新建 IPProfileGenerator | CC 4-2 | 采纳；v0.4 明确不直接调用现有整数接口 | 4.3 |
| 聚合键、avg 分母、total 口径 | C 5.4-2；CC 5.4-4 | 采纳；v0.4 补充整数累计与取整时机 | 5.4.3–5.4.5 |
| 补零策略 | C 5.4-3；CC 5.4-1 | 采纳 | 5.4.7 |
| skid | CC 5.4-3 | 采纳 | 5.4.8 |
| stale matching 的行级与 probe 不对称 | K 5.5、5.9；C 5.5-2 | 采纳 | 5.5、5.9 |
| 报告 schema、分母、PLT/汇编桶、语义字段、确定性 | C 5.6-1；CC 5.6-1~3；K 5.6 | 采纳；v0.4 改为以目标可用率判定，补事件身份与单位、充分性不给出 `ok` | 5.6 |
| ARM 映射符号、`$d`、AArch64 数据映射 | C 5.7-1；CC 5.7-1 | 采纳；v0.4 收紧为没有映射符号即不支持按需功能 | 5.7 |
| 评估指标、噪声、负对照、训练与测试分离、可选对照 | C 5.8-2；K 5.8；CC 5.8-2~4 | 采纳；v0.4 改为差值置信区间与等价区间判据，并修订负对照 | 5.8 |
| 性能实验控制与轮数 | C 5.9-2；CC 5.9-2 | 采纳 | 5.9 |
| `-fprofile-sample-accurate` 与符号列表 | K 5.9、6.4；C 5.9-1；CC 5.9-3 | 采纳 | 5.9、6.3 |
| lit 基础设施与 REQUIRES；独立核对改用 GNU addr2line | CC 5.10-1、5.10-3；C 5.10-1；K 5.10 | 采纳 | 5.10 |
| 原生 perf.data 降级 | CC 6-1 | 采纳，移到第三批并给出立项条件 | 第 7 节 |
| 冷函数列表的证据要求 | C 6.4-1 | 采纳 | 6.3 |
| 合并不等价、权重为正整数、第一批即验证 | C 6.6-1；K 第 6 节；CC 6-2 | 采纳；v0.4 补充 sum 在取整后的不等价 | 5.12 |
| 冻结与评估的循环；两阶段冻结 | C 10-1 | 采纳 | 状态、第 10 节 |
| probe 准入条件；风险补充 | C 11-1；CC 11-1 | 采纳 | 5.5、第 11 节 |
| 第 9 节不应要求"未 strip" | C 9-1；CC 9-1 | 采纳；v0.4 补回构建 flags 要求 | 第 9 节 |
| 2.1 目标的边界与消费语义目标 | C 2-1；CC 2-1 | 采纳 | 2.1 |

### A.3 一般

| 问题 | 来源 | 处理 |
|---|---|---|
| 行号 1186 应为 1190（报错在 :1216） | K 第 1 节 | 采纳 |
| 背景区分"当前镜像"与"硬件能力" | C 1-1 | 采纳 |
| 补充平台事实（A32、strip、页大小） | CC 1-1 | 采纳 strip 与页大小；A32 一条经实测改为"默认 Thumb"（v0.3） |
| C2 预先说明不需要库改动 | CC 3-3 | 采纳 |
| `--min-symbolized-ratio` 改名与暂定；`--ip-aggregation` 过渡期写入 `--help` | K 5.1；CC 5.1-3 | 采纳；v0.4 改为 `--ip-min-usable-ratio` |
| 事件名含修饰符 | CC 5.1-3 | 采纳 |
| `-F` 清空默认字段、`event` 必需 | K 5.2 | 采纳 |
| `--perfdata` 单次调用 | K 5.2 | 采纳；`--perfdata` 改为有条件准入（v0.3） |
| 内核样本按 DSO 名分类 | CC 5.2-4 | 采纳 |
| 身份未验证时的合理性指标 | CC 5.3-3 | 采纳；对齐比例只在 AArch64 给出（v0.3） |
| Google 也取 MAX，作为平局规则依据 | K 5.4；CC 12.4 | 采纳；v0.4 改为"证据不足时的保守选择" |
| 汇编函数样本单独计数 | CC 5.4-5 | 采纳；v0.4 细分为三类原因 |
| probe 在 ARM/AArch64 的发射完整性需实测 | K 5.5；CC 5.5-2 | 采纳 |
| `-fbasic-block-address-map` 的准确表述 | K 第 7 节 | 采纳 |
| 第 8 节删除"惰性符号化"、修正 build-id 对比、措辞收窄 | C 8-1；CC 8-1；K 第 8 节 | 采纳 |
| 补丁拆分顺序；测试输入单独成补丁 | CC 5.11-1；K 5.10 | 采纳 |
| 已采数据需重新导出或重新采集 | CC 5.7-2 | 采纳 |
| 6.5 复用已有裁剪 | C 6.5-1 | 采纳 |
| 增加 RFC 步骤、armv7l 插桩 PGO 验证步骤 | CC 10-1 | 采纳；RFC 为可选步骤；armv7l 插桩 PGO 已完成（05 报告） |
| Chromium 交叉引用错误 | C 6.3 | 已修正 |
| 无 LBR 报错时加提示文本 | K 12.2 | 不采纳：会改变 stderr，违反 C1 |
| `--ip-samples` 改为 `--perf-sample-type` | CC 12.1 | 不采纳，第一批保留现名，交 RFC 决定 |

## 附录 B：v0.2 → v0.3 修订（依据 05、06 冻结前核实报告）

v0.4 对本表的更正以"（v0.4 更正）"标注。

| 实测事实 | 来源 | 设计修订 | 位置 |
|---|---|---|---|
| LLVM 镜像 armv7l 的 Optflags 含 `-mthumb`；FFmpeg、GLib、GStreamer、libstdc++ 导出函数全部 Thumb，libc/ld-linux 以 ARM 为主 | 06 第 1 节 | 删除"默认 A32"前提；Thumb-2 与 A32 都是第一批支持对象；Thumb 边界枚举从第二批移入第一批；评估构建使用镜像的编译选项；报告增加 `isa` 统计。（v0.4 更正：Thumb 上按需功能的可用性取决于调试文件是否含映射符号，待步骤 1 的 ★ 项确认；统计口径只限导出函数） | 1.6、2.1、4.1、4.3、5.4、5.7、5.8、5.11、第 6 节、第 11 节 |
| `--buildid-mmap` 下 buildid-list 仍有输出；没有 build-id 的映像在 MMAP2 中打印设备号与 inode；buildid-list 有空 build-id 行 | 05 B.6 | 删除"两种互斥模式、buildid-list 为空"的表述。（v0.4 更正：buildid-list 是路径级证据，不说明采集时机；身份等级按证据分级） | 5.2.1、5.3.2、5.3.3、5.6.1 |
| `[vdso]` 样本带偏移，`[kernel.kallsyms]` 不带 | 05 B.2 | 特殊 DSO 一律按名称分类，与是否带偏移无关 | 5.2.2、5.2.3 |
| 实际导出格式、LOST 行格式与计数（942 条、61,667 个样本，与 report 一致） | 05 B.2、06 第 4 节 | 按实测写定语法；lit 素材取自实测输出 | 5.2.2、5.2.3、5.10 |
| dsoff 与 PT_LOAD 公式单进程、双进程 100% 一致；`-c`/`-F` 的 period 行为 | 05 B.3–B.5 | 地址换算与 period 规则确认。（v0.4 更正：双进程由 shell 以 fork + exec 启动，不 exec 的 fork 与 exec 替换未专项验证） | 5.2.1、5.3.1、5.4.1 |
| 原始 `st_value` 区间核对在清除 Thumb 位后才全部命中 | 05 B.3 | 核对脚本必须清除 Thumb 位；对齐合理性指标只在 AArch64 给出 | 5.3.3、5.7.2、5.10 |
| 所查 Tizen 仓库没有 x86_64 perf 包 | 06 第 3 节 | 板上导出文本作为第一批主输入；`--perfdata` 有条件准入。（v0.4 更正：结论只限 06 报告查询的仓库） | 4.2、5.2.4、5.11、第 9 节、第 11 节 |
| IR 匹配：插桩预内联导致内联状态不同；零计数分支无权重；键相同但后继含义不同 | 05 C.2、06 第 2 节 | 参考构建关闭预内联；增加语义校验。（v0.4 更正：关闭预内联后的提升不能全部归因于这一选项；缺少权重不能仅凭函数入口计数推定为零；跨分支的 IR 权重之和不等于执行次数；06 的百分比是旧规则结果，新规则需重算） | 5.8 |
| Tizen clang 默认注入 profi；RPi4 页大小 4K；RPi4 新镜像硬件 cycles；armv7l 插桩 PGO 闭环 | 05 A、B.1、C.1、D | 由"待确认"改为已核实事实。（v0.4 更正：profi 注入是上游 clang 22 的行为，只在编译作业中生效；armv7l 插桩 PGO 使用旧快照工具链） | 1.1、1.5、1.6、5.4.6、第 10 节 |

## 附录 C：v0.3 评审意见处理（第二轮）

来源缩写同附录 A。各家对同一问题提出不同方案时，写明采用哪一家及理由。v0.6 对本表的补充或更正以"（v0.6 …）"标注，详见附录 E；原"采纳"的状态不变。

### C.1 严重

| 问题 | 来源 | 处理 | 位置 |
|---|---|---|---|
| Thumb 解码器的子目标没有规定；板上文件没有 `.ARM.attributes`，退化为不带版本的 `arm`，32 位 Thumb-2 指令无法解码 | CC 5.7-1 | 采纳 CC：边界枚举改用 Thumb 编码长度规则，不依赖子目标；MCDisassembler 只作交叉核对，子目标来源固定且写入报告；C2 的参考来源相应缩小为映射符号切换 | 4.1、5.7.2、C2 |
| 符号化率排除全部 `outside_dwarf_func`，会掩盖大面积缺失调试信息 | C 5.6-1 | 采纳 C：以目标可用率 `usable / target` 判定，`line_resolution_ratio` 只报告；`usable=0` 等失败；分母为 0 写 `unknown`。另在 C 的基础上把 `outside_dwarf_func` 细分为 `plt`、`in_cu_no_subprogram`、`no_cu` 三类，以区分可确认的汇编与未知原因的缺失（v0.6 更正：三类只区分地址所在区域与缺少函数归属的形态，`in_cu_no_subprogram` 不单独证明汇编来源） | 5.4.2、5.6 |
| 跨终结指令的 `branch_weights` 之和被当作执行次数，95% 门槛与块级指标失真 | C 5.8-1 | 采纳 C：IR 层只用于局部分支概率；门槛改为结构覆盖；执行加权评价改用 llvm-cov 行级参考；块级指标在恢复方法验证前标为未核实。另补一个候选恢复方法（BFI 块计数）放入步骤 1 验证。CC 5.8-1 的"按权重 ≥ 95% 且按边数 ≥ 80%"双门槛不采纳，因为权重门槛本身不成立 | 5.8 |
| 首条 DILocation 一致仍不能证明边语义相同（条件取反、同行后继、switch case 顺序） | C 5.8-2；CC 5.8-1 | 合并采纳：DILocation 只产生候选（C）；条件 br 规范化比较谓词与操作数，相同按 true/false 配对，谓词互为取反且操作数相同则交换配对（在 C 的基础上明确了能可靠识别的取反情形）；后继首位置一致性作为附加校验，首位置不两两相异时判为不可判定（CC）；switch 按 case 值与 default 配对（C）；其余判为 `semantic_unverified`；共同转储点作为步骤 1 的候选改进（CC）（v0.6 补充：操作数等价的可执行定义；switch 先校验选择值） | 5.8 |

### C.2 重要

| 问题 | 来源 | 处理 | 位置 |
|---|---|---|---|
| 5.4.4 推导列差一个因子 d，`n(k)` 定义有歧义 | K 5.4；C 5.4-1 | 采纳：推导列改为先写原始值再写乘 d 后的结果（`max` 为 `N·max c_i`，`avg` 为 `N·c̄`），`n(k)` 明确为含全部副本、跨全部区间的指令总数 | 5.4.4 |
| 单个函数的按需功能失败，整体如何处理不一致 | K 5.4；CC 5.4-2 | 采纳 CC：整次运行失败，报告列出全部失败函数。K 的"函数级失败 + 占比阈值"不采纳：它引入一个没有数据支撑的新门槛，而在映射符号可用时函数级失败应很少；调用方可以显式改用 `sum`/`max` | 5.4.4、5.7.2、5.6.3 |
| 延迟取整与拟复用的整数接口不兼容；P_ref 规则未定义；"无偏"表述过强 | C 5.4-1；CC 5.4-4 | 采纳 C：整数分子聚合后统一除以 P_ref 并取整，不直接调用现有整数接口；P_ref 取筛选后、符号化前样本 period 的较小中位数，`period=0` 报错。CC 的"double 累加后统一取整"不采纳，因为 double 不能精确表示全部 uint64 计数 | 4.3、5.4.1、5.4.4、5.4.5 |
| `entry-estimate` 没有复现 LLVM 的 head 估计 | C 5.4-2；CC 5.4-3 | 采纳：构建完成后直接调用 `getHeadSamplesEstimate()` | 5.4.6 |
| LTO 下 `head=none` 的前提（profi 已开启）不成立 | CC 5.4-1 | 采纳：链接步骤需显式开启 profi；5.9 补 LTO 变体与链接步骤控制 | 1.6、5.4.6、5.9 |
| DSO 路径按"最后一个 ` (`"切分，在 `(deleted)` 与带括号的路径下误判 | C 5.2-1；CC 5.2-1 | 采纳（两家方案一致）：按固定字段顺序解析，DSO 字段取 ip 之后的 ` (` 到行尾的 `)`，只把末尾的 `+0x<十六进制>` 解释为偏移 | 5.2.3 |
| 身份来源混淆了容器来源与采集时机；最终等级如何汇总未定义 | C 5.3-1 | 采纳 C：证据来源与身份等级分开，buildid-list 为路径级证据（`verified-path`），保守汇总，空集合不得判通过，缺失与冲突的统一规则（v0.6 补充：混合来源时的汇总公式） | 5.2.1、5.3.2、5.3.3、5.6.1 |
| 没有映射符号时按 bit0 判定 ISA 的退路被高估；AArch64 无映射符号时整体按代码处理过宽 | C 5.7-1；CC 5.7-2；K 5.7 | 采纳：没有映射符号即不支持按需功能（EM_ARM 与 AArch64 一致，C）；函数符号只用于 `isa` 统计（CC）；ISA 用 `SF_Thumb` 标志而不是读取后的地址（K）；指令字节取自 `--binary`、不从指令中间起步、映射状态取区间起点之前的最近映射符号（C）（v0.6 补充：按节查找、包括恰在起点的符号、同址冲突、长形式名、DWARF 区间起点的证明） | 5.7.2 |
| 报告缺少完整事件身份，单位与"充分性"有误导 | C 5.6-2；CC 5.6-2 | 采纳：增加 `event` 字段与 `raw_event_unit`/`output_count_unit`；`sampling_adequacy` 不给出 `ok`（C）；增加丢失比例门槛 `--ip-max-lost-ratio`，丢样未知时该项为 `unknown`（CC） | 5.1.1、5.6 |
| 失败契约需要明确双输出的提交顺序、路径冲突与加载失败 | C 5.6-3；CC 5.6-1 | 合并采纳：提交顺序、路径别名与标准输出的处理采用 C；加载失败采用 CC 的"IP 模式下在 `exitWithError` 中调用已注册回调"并调整 `main` 顺序。C 的"统一错误出口、不复用 `exitWithError`"不采纳：它需要重构共享加载代码中的大量错误路径，回调方式由 IP 模式门控、对 LBR 路径零改动（v0.6 补充：回调限定在加载作用域；profile 流显式 flush/close 检查） | 4.3、5.6.3 |
| 缺少权重的分支不能一律补零 | C 5.8-3 | 采纳：默认视为 `unknown`；需要独立证据才记为零；区分 `llvm.expect` 产生的预期权重；部分忽略 profile 的函数整体排除 | 5.8 |
| 置信区间重叠不是等价判据；负对照不能要求所有不同输入都更差 | C 5.8-4 | 采纳：差值置信区间与预先给定的等价区间 ±ε；证据不足时可保守选择但不称等价；负对照改为受控工作负载与固定种子扰动，不为评估增加身份绕过 | 5.4.4、5.8 |
| `max` 与 [ip,ip] 注入输出"逐行一致"的用例必然失败 | C 5.10-1；CC 5.10-1 | 采纳 C 的口径：只比较已命中位置的正 body 计数，total、head、缺失与零位置各用独立 golden；采纳 CC 的限制：只在 aarch64 与 A32 上做，Thumb 不做。CC 方案中"带补零后含 0 值行逐行一致"不采纳，因为两条路径的补零范围定义不同 | 5.10 |
| `sum` 在取整后不等价 | C 5.12-1；CC 5.12-1 | 采纳：只在整数分子层可加；写出后每份每键最多差 1；head 与裁剪不一定可交换 | 5.12 |
| "fork、exec 已实测"超出证据 | C 8-1；CC 8-1、5.10-2 | 采纳：改为"双进程（fork + exec 启动）已实测"；lit 中的 fork 用例检验不到 perf 的行为，改为板上集成用例 | 5.3.1、5.10、第 8 节 |
| 构建 flags 要求在 v0.3 中丢失 | CC 9-1 | 采纳：第 9 节补回 `-fdebug-info-for-profiling -funique-internal-linkage-names`、相同源码相对路径、DWARF 路径不加 probe | 第 9 节、5.8、5.9 |
| 步骤 1 剩余项不完整，部分必须在第一阶段冻结前闭合；IR 重跑应覆盖真实的 Thumb 构建 | C 10-1；CC 10-1、5.8-2 | 合并采纳：★ 项（调试文件内容、Thumb 边界验证、RPi5 的 dsoff）为第一阶段前置条件；IR 匹配按新规则在 aarch64 与真实 Thumb 构建上重跑，归入第二阶段前（C 的分阶段划分） | 第 10 节 |
| 输入范围"拒绝 LBR 输入"与评估中的同一 perf.data 冲突 | C 5.1-1 | 采纳：拒绝含 brstack 的文本，原始 perf.data 可以含分支栈，报告记录 `projection=ip-only` | 5.1.2 |
| 附录 A、B 的若干处理状态不准确 | C A-1、B-1；CC 附录 A、B | 采纳：附录 A 在受影响的条目中注明 v0.4 的补充；附录 B 增加"v0.4 更正" | 附录 A、B |

### C.3 一般

| 问题 | 来源 | 处理 |
|---|---|---|
| profi 默认注入是上游 clang 22 行为，只在编译作业中生效 | K 第 1 节；C 1-1；CC 1-1 | 采纳 |
| 平台结论的范围（Thumb 统计只限导出函数；spike 不能泛化；仓库查询范围；armv7l 插桩 PGO 用的是旧快照工具链） | C 1-1；CC 1-1 | 采纳 |
| C1 比对矩阵：gcc 写出不支持、CS/probe 不支持 binary；比较实际的成功或失败行为 | K 第 3 节；C 第 3 节 | 采纳 |
| 4.1 中"完全 strip"应放宽为"无 `.symtab`" | K 第 4 节 | 采纳 |
| 调试文件中查 FS discriminator 不能直接复用现有函数 | CC 4-1 | 采纳 |
| 频率模式下 period 回退为频率值的边界情形 | K 5.1 | 采纳，作为已知局限并在全部 period 相同时提示 |
| 内核模块与 `[unknown]` 的格式可由源码确定 | CC 5.2-2 | 采纳，并列入步骤 1 的实测素材 |
| `--perfdata` 准入证据与版本对绑定 | CC 5.2-3 | 采纳 |
| 未验证模式下用设备号与 inode 检查歧义 | CC 5.3-1 | 采纳 |
| 调试文件中 build-id note 的可用性需确认 | CC 5.3-2 | 采纳，列入步骤 1 的 ★ 项（v0.6：已由 08 报告闭合） |
| PSI 论断应指向 `isFunctionEntryCold` | K 5.4 | 采纳 |
| 取整时机 | CC 5.4-4 | 采纳（按 C 5.4-1 的整数方案落实） |
| `PseudoProbeInserter` 的作用描述；陈旧度检查的统计范围 | CC 5.5-1；K 5.5 | 采纳 |
| 映射符号名的匹配规则（`$t.1` 等） | CC 5.7-3 | 采纳（v0.6 更正：后缀不限于数字） |
| create_llvm_prof 对照的运行位置有歧义 | K 5.8 | 采纳，改为在 x86_64 主机上构建并读取板上 perf.data，可行性在评估阶段确认 |
| sample 侧关闭内联带来的测量局限 | CC 5.8-1 | 采纳 |
| 原生 perf.data 的"上游接受度低"只是预期判断 | C 第 7 节 | 采纳 |
| 行号与函数名勘误（`getLeafProfileAndAddTotalSamples`、`evsel.c`、`synthetic-events.c`、`SampleProfile.cpp`、`ProfiledBinary.cpp`、`linux-rpi.spec`、`findFuncRange`、`map.h`、`SampleProfileMatcher.cpp` 路径、`rejectHighStalenessProfile`、BOLT 路径） | K 各节；CC H-1 | 采纳，按评审核实的行号逐处修正 |
| 引用约定中补充行号的核实范围 | K 总体结论 | 采纳 |
| `--ip-samples` 与 `--perf-sample-type` 的命名 | K、C、CC 第 12 节 | 三家都主张第一批保留 `--ip-samples`，采纳；改名交 RFC，届时默认值不得暗含自动降级（K、C） |

## 附录 D：v0.4 → v0.5 修订（依据 07 报告与 build-id 方案）

| 事实或决定 | 来源 | 设计修订 | 位置 |
|---|---|---|---|
| 调试文件保留映射符号与 `.ARM.attributes`，代码节为 NOBITS；运行文件没有这两者 | 07 第 1 节 | 写入背景；5.7.2 的前提（映射符号来自调试文件、指令字节来自运行文件）得到支持 | 1.6、第 10 节 |
| 原样构建的 FFmpeg 运行文件与调试文件都没有 build-id；原因是 clang 未打开 `ENABLE_LINKER_BUILD_ID` | 07 第 1.3 节 | 写入背景；拆分后 build-id note 是否可读改为新的 ★ 项（v0.6：已由 08 报告闭合） | 1.6、第 10 节 |
| LLVM 包将打开 `-DENABLE_LINKER_BUILD_ID=ON`，预计下周发布 | 用户决定（LLVM owner） | 第 9 节的 build-id 要求改为"发布后由 clang 默认生成，发布前评估构建显式加 `-Wl,--build-id=sha1`"；要求采样构建与使用构建用同一版本工具链；build-id 按完整字节串比较，不假设长度（GNU ld 20 字节、lld 8 字节）。（v0.6 更正：22.1.8 的 lld 不带参数时也是 sha1、20 字节；"同一版本工具链"的要求删除，身份只校验被采样映像，见附录 E） | 1.6、5.3.3、第 9 节、第 11 节、第 12 节 |
| Thumb 边界在 20 个最大 Thumb 函数上与 objdump 逐条一致；A32 只覆盖到启动代码片段 | 07 第 2 节 | 原 ★ 项闭合；A32 由 lit fixture 补足 | 第 10 节 |
| 不 exec 的 fork 与 exec 替换的偏移与归属全部正确 | 07 第 3.1、3.2 节 | 由"待验证"改为已实测；正式验收仍保留板上集成用例 | 5.3.1 |
| `(deleted)` 的实际格式；`--buildid-mmap` 下被删除文件的映射也可能不带 build-id；内核模块为完整 `.ko` 路径、映射记录为 `PERF_RECORD_MMAP`；合成记录的外层前缀可为 `0/0` | 07 第 3.3、3.4 节 | 按实测写定格式；被删除文件的映射按缺失身份处理 | 5.2.2 |
| debugedit 对 DWARF5 报"unhandled"警告 | 07 第 1.3 节 | 写入背景与风险，评估中以目标可用率实测 | 1.6、第 11 节 |

## 附录 E：v0.5 评审意见处理（第三轮）与 08、09 报告修订

来源缩写：C = Codex，CC = Claude Code（Kimi Code 本轮未参加）。条目编号沿用各家评审中的编号。两家结论均为"修改后可以冻结"，都没有提出严重问题。两家都把 RPi5 的 ★ 项列为未完成，这是因为评审基于 v0.5 所在的提交；09 报告随后已闭合该项（E.1）。

### E.1 08、09 报告与评审实测带来的事实

| 事实 | 来源 | 设计修订 | 位置 |
|---|---|---|---|
| 显式 sha1 构建经 RPM 调试拆分后，运行文件与调试文件都是可读的 SHT_NOTE，20 字节 build-id 一致，`.build-id` 链接正确；调试文件的 `$t` 为 5883 个（07 为 5882 个） | 08 报告 2.1–2.2 节 | ★ 项闭合；5.3.4 第 2 条改为已确认；不写成"映射符号数量完全一致"，也不视为边界已重新验证 | 1.6、5.3.4、5.7.2、第 10 节 |
| `find-debuginfo` 带 `--build-id-seed` 调用；BUILD 目录中链接产物的 build-id 与 RPM 中两份文件的不同 | 08 报告 2.3 节（命令行）；CC 1-2（实测 ID 不同） | 身份以打包后的文件为准；BUILD 目录产物不能作为 `--binary`/`--debug-binary`；增加对应负对照；实测结果补存为仓库证据（非 ★）。（v0.7 更正：改为只按 build-id 判定、不按目录判定，见附录 F） | 1.6、5.3.3、5.10、第 9、10 节 |
| 拆分后行表逐行一致、抽样符号化一致、`comp_dir` 未改写（libavcodec 单次构建） | CC 1-2（评审实测） | DWARF5 风险降级，但只限该库与该次构建；补存证据（非 ★） | 1.6、第 10、11 节 |
| RPi5：页大小 4096；dsoff 公式单进程 5,865、双进程 14,331 条 100% 一致；`--buildid-mmap` 下 libc 的 MMAP2 build-id 与 ELF 一致；buildid-list 非空；period 行为与 RPi4 一致 | 09 报告 1–5 节 | RPi5 的 ★ 项闭合；页大小写入背景 | 1.6、5.3.1、5.7.1、第 10 节 |
| 系统级录制中 pid/tid 可以是 `-1/-1` | 09 报告"对设计的影响"第 1 条 | pid/tid 按带符号整数解析，-1 为进程未知，`--pid` 不匹配；增加 lit 用例 | 5.1.3、5.2.2、5.2.3、5.6.1、5.10、第 11 节 |
| 两块板上都没有可执行段 `p_offset ≠ p_vaddr` 的实例 | 05、09 报告 | 该布局只由离线 lit 覆盖，不再列为板上待核实项 | 5.3.1 |
| clang 直接构建的 aarch64 产物带 `$x`/`$d`，且 `$x` 位于节偏移 0 | CC 5.7-1、5.7-2（评审实测） | 支持按节查找映射状态；Tizen aarch64 debuginfo 的保留情况列为非 ★ 项 | 5.7.2、第 10 节 |

### E.2 重要

| 问题 | 来源 | 处理 | 位置 |
|---|---|---|---|
| `SampleProfileWriter::write()` 成功不表示流已落盘；`raw_fd_ostream` 析构时发现错误会直接 fatal，绕过失败契约；加载回调固定写 `failure_stage=load`，但 `exitWithError` 也用于 writer 失败 | C R7 | 采纳 C：IP 模式自建 `raw_fd_ostream` 交给现有 `create(std::unique_ptr<raw_ostream> &, Format)`，序列化后显式 flush/close、检查并清除错误；回调只在加载作用域内注册、一次性、不可重入；其他阶段显式记录 `failure_stage`。已核对 `SampleProfWriter.cpp:156–163`、`raw_ostream.cpp:655–678`、`SampleProfWriter.h:115–126` | 5.6.1、5.6.3、5.10、5.11 |
| 混合身份证据（同一路径部分映射有 `mmap2`、部分只有 `buildid-list`）的最终等级没有明确规则 | C R5；CC 5.3-2 | 合并采纳：汇总公式采用 CC 的"逐映射取最强证据、再取最小值、只计可执行映射"；必要身份的范围、冲突优先于缺失、deleted 路径不用 `buildid-list` 补足采用 C | 5.3.2、5.3.3、5.10 |
| 候选选择写成"匹配正则或文件名相同"，正则无法消歧；`(deleted)` 后缀使默认文件名匹配失效 | C R4 | 采纳 C：给出正则时只按正则，取代文件名匹配；默认匹配时去掉 ` (deleted)` 标记，原始路径与 deleted 状态保留；歧义检查在已选候选集合上执行。另补充：同一路径既有 deleted 又有未删除的映射时，未验证模式下按"文件被替换"报歧义 | 5.1.1、5.3.3、5.6.1、5.10 |
| `PERF_RECORD_LOST_SAMPLES` 不会出现在 perf script 文本中；LOST 行无法归属到事件、DSO 或 pid，以目标样本数作分母会失真 | C R3；CC 5.2-1 | 合并采纳：删除 `LOST_SAMPLES` 的文本支持与素材（两家一致）；比例采用 C 的输入级定义 `L / (L + S)` 与 `scope`、`source` 字段；下界语义采用 CC。在此基础上明确判定：下界超过门槛即可确定真实丢样也超过，判为 `exceeded`；未超过时为 `not_exceeded_visible`，不写成通过。（v0.7 更正：LOST 的计数混有边带记录，不是 IP 丢样的下界，改为输入级诊断代理与 `completeness=unknown`，见附录 F）已核对 `builtin-script.c:2930–2931`、`builtin-record.c:1936–1980`；用 06 的数据核对比例约为 8.06% | 5.1.1、5.2.2、5.2.3、5.6、5.10、第 11 节 |
| "采样构建与使用构建必须用同一版本工具链"混淆了转换输入的身份与消费构建的身份 | C R11；CC 9-1 | 合并采纳：身份链为"采样记录 → 被采样的 A → A 的调试文件"，消费构建 B 不参与比较（C）；工具链升级是常规用法，失配由消费端诊断体现，评估内固定工具链是为了控制变量；身份以打包后的文件为准（CC）。5.9 增加"新工具链消费旧 profile"的可选组（CC）；增加"用 B 冒充 A"与"BUILD 目录产物"两条负对照。（v0.7 更正：负对照改为明确构造 ID 不同的输入，见附录 F） | 5.3.3、5.9、5.10、第 9、11 节、附录 D |
| 错误提示引导用户使用文档明确不支持的"probe 构建 + DWARF 关联" | C R2 | 采纳 C：准入前 IP 模式拒绝带 probe 的构建，包括加 `--use-dwarf-correlation` 的情况；probe 检测独立于路径选择。已核对 `checkPseudoProbe()` 在强制 DWARF 时直接返回（`L/ProfiledBinary.cpp:429–449`）。该组合是否确实产生错误计数仍未核实，拒绝的理由是支持契约而不是已知错误 | 5.1.4、5.10 |
| 映射符号规则不完整：后缀不限于数字；"之前最近"应包括恰在起点的符号；必须按节查找；同址冲突；DWARF 区间起点不能直接当作指令起点 | C R8；CC 5.7-1 | 合并采纳：长形式名、符号属性、`<=` 查找、同址冲突、DWARF 起点的证明、ELF32 小端采用 C；按节查找两家一致，`.plt`/`.text` 相邻的 fixture 采用 CC。在此基础上补充：两份文件之间按节名与地址范围对应节，不依赖节索引相同；DWARF 起点的证明方式定为"从同一节内不大于起点的最近 `$t` 按长度规则步进恰好落在起点"。（v0.7 更正：改为与映射区间求交、按各自 ISA 从当前映射区间的锚点证明，不跨 `$d` 或另一种 ISA 步进，见附录 F）已核对 `ARMDisassembler.cpp:6138–6163` 的长度判断与 `llvm-objdump.cpp` 的按节查询 | 5.7.2、5.10、第 11 节 |
| 报告要求 `input_total` 等每层都给出 `period_sum`，与"不同事件不合算"冲突；可用率未限定用原始计数 | C R6 | 采纳 C：`input_total` 只给样本数，筛选前的 `period_sum` 按事件分别给出；目标可用率按 `--ip-weight` 选口径，只用原始整数计数 | 5.6.1、5.6.2、5.10 |
| 严格解析没有考虑负的 pid/tid | 09 报告（本设计自查） | 见 E.1 | 5.2.3 第 8 条 |
| 〔第二阶段〕switch 匹配缺少选择值语义校验 | C R9 | 采纳 C：先校验选择值的类型、位宽与等价，再按带位宽的 case 常量配对并校验后继；语义校验收紧后据实重定结构覆盖门槛，不为达到 95% 放宽 | 5.8 |
| 〔第二阶段〕LTO 链接步骤只显式控制 profi，还不足以控制实验变量 | C R10 | 采纳 C：链接步骤传入同一 `-fprofile-sample-use`，并显式指定 profi 与两项 salvage 选项；诊断在 post-link 阶段核对；增加"链接漏传 profile"负对照。只影响 LTO 实验，当前非 LTO 的 FFmpeg 评估不增加工作 | 5.9 |

### E.3 一般

| 问题 | 来源 | 处理 |
|---|---|---|
| lld 22.1.8 不带参数的 `--build-id` 是 sha1（20 字节），"lld 默认 8 字节"的说法错误 | C R1；CC 1-1 | 采纳（两家一致，已核对 `lld/ELF/Options.td:60`、`Driver.cpp:972–978`）。"按完整字节串比较"的规则不受影响；lit 中保留由 `--build-id=fast` 构造的 8 字节与 20 字节判为不一致的用例（CC）。C 提出的"对 lld 的裸参数、sha1、fast、none 分别核对 note"属于链接器行为，不作为 profgen 的测试，并入新工具链发布后的复核 |
| 默认 `--build-id` 与 `-Wl,--build-id=sha1` 的先后与覆盖关系 | CC 9-1 | 采纳：写明 clang 默认选项排在 `-Wl,` 之前、lld 取最后一个、GNU ld 未核实；最终以打包后的文件为准 |
| 三个门槛在第二阶段前的行为没有写明 | CC 5.1-1 | 采纳：未给出时不判定，报告为 `not_evaluated`，退出码不受影响；目标样本数为 0 无论如何都失败（保留 v0.5 的规则） |
| 合成 MMAP2 中的 build-id 并不都是映射时由内核读取的 | CC 5.3-1 | 采纳，并把"录制开始前原地改写文件"写为已知局限 |
| 调试文件 build-id note 可读性已由 08 确认 | CC 5.3-3 | 采纳 |
| aarch64 的 Tizen debuginfo 是否保留 `$x`/`$d` 未确认 | CC 5.7-2 | 采纳，列为交付前的非 ★ 项：它只决定 aarch64 上按需功能是否可用，不影响第一阶段冻结的规则 |
| `branch_weights` 的缩放描述过严 | CC 5.8-1 | 采纳（已核对 `ProfDataUtils.h:172–176`）：缩放因子通常为 1；跨终结指令的和仍只作描述性统计，执行加权使用前须证明未被缩放 |
| "操作数来源一致"没有可执行的定义 | CC 5.8-2 | 采纳，并同时用于条件 br 与 switch 的选择值（与 C R9 合并） |
| `in_cu_no_subprogram` 不能证明是汇编 | C R13 | 采纳（已核对 `L/ProfiledBinary.cpp:938–956` 会跳过缺名字或范围读取失败的 subprogram）；有独立证据时另附 `assembly` 来源说明 |
| 版本信息、前置材料与 ★ 项状态未随 08 更新；未发布的默认行为不应绑在冻结前提上 | C R12；CC H-1、10-1 | 采纳：前置材料加入 08、09；★ 项按 08、09 闭合；新工具链复核改为交付前的非 ★ 项（两家一致） |
| 风险表随身份范围、丢样可见性与 DWARF5 结果更新 | C 第 11 节；CC 11-1 | 采纳，并补"负 pid"与"映射状态跨节"两行 |
| 附录 C 中 R5、R7、R8、R9 相关条目应补限定，不必改回"未采纳" | C 附录 C | 采纳，在相应条目后加"（v0.6 补充）" |
| 07 的真实样例应直接替换"待补"的 deleted、模块素材 | C 5.10 | 采纳 |

### E.4 未采纳或部分采纳

| 意见 | 来源 | 理由 |
|---|---|---|
| RPi5 的 dsoff 与 `--buildid-mmap` 仍是冻结前提 | C R12、总体结论；CC 10-1、总体结论 | 评审时成立；09 报告已闭合，不再是前提 |
| 由评审方直接生成 v0.6 草稿或保存评审文件 | CC 总体结论 | 不需要；评审原文由用户保存 |
| 对 lld 各种 `--build-id` 写法逐一核对 note 作为本设计的测试 | C R1 | 部分采纳，理由见 E.3 第 1 条 |

## 附录 F：v0.6 限定范围复核意见处理与第一阶段冻结

来源缩写：C = Codex（编号 P1–P5、S1），CC = Claude Code（编号 R6-1 至 R6-10）。两家结论均为"修改后可以冻结第一阶段"，都没有严重问题；两家都确认附录 E 的处理已落地、★ 项已全部闭合。下列修改都是局部的规则补充，不改架构，因此修订后直接冻结第一阶段，不再另起一轮。附录 E 中被本附录更正的条目已标注"（v0.7 更正）"。

### F.1 重要（第一阶段）

| 问题 | 来源 | 处理 | 位置 |
|---|---|---|---|
| 一方有 build-id、另一方没有时被当作"缺失"，`--allow-missing-build-id` 能放行可以证明不是同一文件的输入 | CC R6-1 | 采纳 CC：目标 ELF 没有 note 而输入侧有 ID 证据、目标与调试文件一方有 note 一方没有，都判为 `mismatch`；三方都没有 ID 时才按缺失处理。在 CC 的基础上补上"调试文件有、目标没有"这一反方向 | 5.3.2 第 3 条、5.3.3 第 6 条、5.10、第 11 节 |
| 可执行映射筛选后为空的情形没有定义；"非可执行映射不影响等级"与"任一已知冲突失败"没有统一 | C P1 | 采纳 C：M 为空按缺失处理，不得以空集合判通过；非可执行映射不因缺证据而降级，但其已知 ID 仍参与冲突检查 | 5.3.2 第 2、3 条、5.6.1、5.10 |
| `ProfiledBinary` 内部经 `unwrapOrError` → `exitWithError` 直接退出（例如生成阶段第一次符号化时才打开调试文件），绕过失败契约 | CC R6-2 | 采纳问题，方案采用 CC 列出的备选 B，不采用其推荐的 A：兜底回调覆盖整个 IP 流程，由 IP 路径维护的"当前阶段"决定 `failure_stage`。理由：A（另写不经 `unwrapOrError` 的符号化包装）只覆盖符号化一处，`ProfiledBinary` 中其他经 `unwrapOrError` 的路径仍会绕过契约，且抽出共用的帧转换逻辑要改共享代码；B 覆盖全部库内退出，且不改共享代码。已核对 `L/ProfiledBinary.cpp:1065–1073`、`L/ErrorHandling.h:21–46` | 5.6.3 第 3 条、5.10、5.11、第 11 节 |
| probe 检测只看 `--binary`，拆分后这两节可能只在调试文件中 | CC R6-3 | 采纳 CC：两份文件都检测，任一文件含任一节即拒绝；拆分后的位置列为交付前的非 ★ 项 | 5.1.4 第 3 条、5.10、第 10、11 节 |
| `PERF_RECORD_LOST` 的 N 是丢失的输出记录数，也包含 MMAP、COMM 等边带记录；v0.6 把它说成真实 IP 丢样的下界、并据此推断"超过门槛即真实丢样超过"，不成立 | C P2；CC R6-5 | 两家一致，合并采纳：语义与判定采用 C（`count_unit=records`、`completeness=unknown`，`exceeded` 只表示可见诊断量超过配置的门槛，不推断真实 IP 丢样率）；`W_LOST_MAY_INCLUDE_SIDEBAND` 告警与 `mapping.completeness=unknown` 采用 CC。公式与失败机制不变。已核对 `kernel/events/ring_buffer.c:178–182`、`:250–265` | 5.2.2 第 3 条、5.2.3 第 7 条、5.6、5.10、第 11 节 |
| 起点证明统一要求从最近 `$t` 步进，纯 A32、纯 AArch64 会失败；即使是 Thumb，也可能从更早的 `$t` 跨过 `$d` 或另一种 ISA 连续步进；A32/A64 的起点没有对齐要求 | C P3；CC R6-8 | 合并采纳：DWARF 区间与映射区间求交、按各自 ISA 从当前映射区间的锚点证明、`$d` 交集排除、末端不得截断、证明用的前缀不计入 `n(k)` 采用 C；A32/A64 起点与锚点距离为 4 的倍数两家一致 | 5.7.2 第 4、6 条、5.10、第 11 节 |
| "BUILD 目录产物不能作为输入"过度泛化：身份应由 build-id 决定，不由目录决定 | C P5 | 采纳 C：改为"必须对应被采样的映像 A"；采样已安装 RPM 时不得未经核对就用打包前产物替代；直接采样未打包产物同样允许；负对照改为明确构造 ID 不同的输入，并增加"复制到 BUILD 目录后结果不变"的正对照 | 1.6、5.3.3 第 9 条、第 9 节、5.10、第 11 节 |

### F.2 重要（第二阶段，不阻塞第一阶段冻结）

| 问题 | 来源 | 处理 | 位置 |
|---|---|---|---|
| "一层 opcode、类型与 DILocation 相同"不能证明操作数等价（`and %x, 1` 与 `and %x, 2` 的反例） | C S1 | 采纳 C：叶子只接受对应参数与相同常量；白名单内的无副作用运算递归比较操作数与语义标志并设深度上限；其余判为 `semantic_unverified`；结构覆盖率按新规则重算。已核对 `Instruction.cpp:962–985` | 5.8 第 3、4 条 |

### F.3 一般

| 问题 | 来源 | 处理 |
|---|---|---|
| `--binary` 为符号链接时默认文件名匹配不到 | CC R6-4 | 采纳：按 realpath 解析后的文件名匹配，报告记录两者。CC 提出的报错提示条件（"存在与给出名同名的 DSO"）改为更通用的"候选为空时列出样本最多的文件 DSO 并提示正则"，因为从板上拉回的文件常被改名，realpath 也解决不了 |
| 门槛"未设置"与指标"未知"的状态优先级冲突 | C P4 | 采纳：统一为"未设置 → `not_evaluated`；已设置但指标未知 → `unknown`；已知 → 比较"；未设置不豁免独立失败条件。另外明确：门槛已设置而状态为 `unknown` 时不因该项失败，并给出告警 |
| IP 路径自建 writer 时要复现现有写出路径中仍适用的行为（打开标志、可定位文件、`--use-md5`、gcc 格式报错），以及"For testing"重载的说明 | CC R6-7 | 采纳。已核对 `SampleProfWriter.cpp:825–826`、`:942–945`，`L/ProfileGenerator.cpp:181–187` |
| "strip 前后逐字节一致"的对照对象需要说明 | CC R6-9 | 采纳：对照对象是同一 ELF 用 `llvm-objcopy` 拆分前后的文件或 `eu-unstrip` 合并后的文件，不是 BUILD 目录产物 |
| 两处引用不够直接（`suggestBytesToSkip()`；`-mllvm` 不传到链接端的依据） | CC R6-10 | 采纳。已核对 `CommonArgs.cpp`、`Gnu.cpp` 的链接参数构造中没有 `OPT_mllvm` |
| 候选选择的其余情形完整 | CC R6-6 | 无需修改 |

### F.4 冻结说明

1. 冻结范围：第 10 节步骤 2 所列的正确性规则与契约（5.1–5.4、5.6、5.7、5.10–5.12）。
2. 冻结的依据：两家复核都没有严重问题，全部意见已按本附录处理；★ 前置项已由 07、08、09 闭合；本版的修改都是局部规则，复核方已给出候选方案，本版采用的方案及理由见 F.1–F.3。
3. 尚未入库的评审实测（DWARF5 拆分核对、BUILD 产物与 RPM 的 build-id 不同）仍标为未核实，按第 10 节步骤 1 的非 ★ 项补存，不作为冻结依据。
4. 冻结之后，对冻结范围内规则的修改需要单独提出，写明理由与影响，并在本文档中记录。

## 附录 G：v0.7 → v0.8 → v0.9 → v1.0 → v1.1 → v1.2 → v1.3 → v1.4 → v1.5 修订（实现期增补、评估判据修订与第一轮实测）

本附录登记 v0.7 冻结以后的全部裁决与实测事实，v0.9 按 v0.8 评审意见修订（处理见附录 H），v1.0 按 v0.9 评审意见修订（处理见附录 I），v1.1 按 v1.0 确认评审意见修订（处理见附录 J），v1.2 按 v1.1 评审意见修订（处理见附录 K），v1.3 按 v1.2 评审意见修订（处理见附录 L），v1.4 按 v1.3 评审意见修订（处理见附录 M），v1.5 按 v1.4 评审意见修订（处理见附录 N）。G.1 是对第一阶段冻结范围的增补与澄清，已随补丁实现并验收；它的优先级只限于各条明确列出的修订点，正文中未被列出的限制继续有效。G.1 的写法以已验收的实现与证据为准，不改变既有 golden 值。G.2 是评估执行的定义与规则。G.3、G.4 是第二阶段判据的修订，预注册修订 3 登记前不对任何正式 sample profile 计算质量指标。G.5 是实测事实。证据路径均相对仓库根目录。

### G.1 第一阶段冻结范围的增补（已实现、已验收）

#### G.1.1 `prev-inst` 的前驱条件（5.4.8）

1. 在 5.4.8 原有条件之上追加，不替代原有的函数范围限制：前驱指令与原地址处在同一个枚举区间（该函数的 DWARF 区间与映射区间之交，同一 ISA），前驱指令的末端与原地址相接，并且前驱可以符号化到有效行时，才把样本移到前驱。
2. 不调整的样本按原因计数，按实现的检查顺序归类（`IPBoundary.cpp` 的 `IPFunctionBoundaries::predecessor`）：`first_instruction`（该函数已枚举指令序列的第一条指令；两个独立函数共用同一个 `$t` 范围时，第二个函数的第一条指令也属于此类）；`range_gap`（前驱属于同一函数的另一个 DWARF 区间，或前驱末端与原地址不相接；同一函数后续 DWARF 区间的首指令归入此类）；`data_or_state_change`（前驱属于另一个映射区间）；`predecessor_no_line`（前驱没有有效行，包括 G.1.9 判为整体排除的前驱）。样本地址不是指令起点时，整次运行在 boundary 阶段失败（5.7.2），不走到这里。
3. 归类（`target`、`usable`、`outside_dwarf_func` 等）始终按原地址进行，skid 只改变计数落到哪一行，不改变归类。
4. 理由：跨函数、跨 ISA 或跨数据区移动会把样本记到不可能执行的位置；按原地址归类保证各配置的分母一致。证据：`docs/profgen/impl/08_patch6_report.md`。

#### G.1.2 输出路径冲突（5.6.3）

`--output -`（标准输出）、质量报告路径与 profile 路径相同、或任一输出路径与任一输入相同，都判为路径冲突：不写任何文件，只在 stderr 报告冲突。理由：此时无法在不损坏输入或另一输出的前提下写出失败报告。

#### G.1.3 失败时旧文件的处理（5.6.3）

1. 旧 profile 在任何失败下都保持不变。
2. 除路径冲突外的失败：质量报告原子替换为带失败原因的报告。
3. 报告尚未成功提交时，路径冲突或报告本身写入、提交失败：旧报告保持不变。
4. 提交顺序的例外：本次成功报告已经提交、随后 profile 提交失败时，尽力把报告改写为失败报告；改写也失败时，可能留下本次的成功报告，此时必须在 stderr 明示，且进程非 0 退出始终优先于报告中的转换结论（`docs/profgen/impl/08_patch6_report.md` 第 11 节）。
5. 理由：失败报告是失败契约的一部分，必须能覆盖上一次成功的报告，否则下游会读到过期的成功结论；只有在报告本身写不出来时才保留旧文件。

#### G.1.4 比率与门槛的写法（5.6.1、5.6.2）

1. 报告中的比率一律写成 `{numerator, denominator}` 两个整数，不写浮点数。
2. 门槛参数接受十进制定点文本，小数位不超过 9 位；比较时换算成整数比较，不经过浮点。
3. 门槛未满足的失败记为 `failure_stage=generate`。

#### G.1.5 报告取值约定（5.6.1）

不适用或不存在的字段写 `null`（枚举类字段写 `none`）；无法确定的值写 `"unknown"`。二者不可混用，也不用 0 代替未知。

#### G.1.6 LOST 比率溢出（5.2.3 第 7 条）

LOST 计数 L 与样本数 S 都能表示、但比率的分母 L + S 超出 uint64 范围时，比率记为 `"unknown"` 并告警 `W_LOST_RATIO_OVERFLOW`，不截断、不饱和。L 或 S 自身累计溢出仍按计数错误失败。证据：`docs/profgen/impl/09_patch7_report.md` 第 3 节。

#### G.1.7 测试注入选项与失败阶段的测试（5.10）

1. 新增隐藏选项 `--ip-test-inject-failure=<阶段>`，只在 IP 模式有效、不写入用户文档，在 5.1.1 的选项表之外登记为隐藏的测试选项，用于在指定调用点注入失败以测试失败契约。只有实际执行到该调用点时才触发：例如没有提供分离调试文件时调试文件类注入点不会经过，没有报告路径时报告写入类注入点不会经过，此时转换不保证失败。失败消息也不保证带 "injected"：只有 `runtime-open`、`runtime-metadata`、`debug-open-load`、`debug-metadata`、`symbolize`、`debug-open` 注入点带这一字样（这些消息都由补丁 6 引入）；`invalid-image` 给出 "not a valid ELF/COFF image"，profile 与报告的写入类注入给出普通 IO 错误，`context-create` 给出调试上下文错误。成功写出的报告在 `tool.arguments` 中记录原始 argv（`llvm-profgen.cpp:355`）；响应文件 `@x.rsp` 在选项解析时才展开，记录中看不到其中的选项。正式评估的输入准入拒绝任何以 `@` 开头的参数，以及注入选项的单横线、双横线、`=值`、分离值四种写法，不依赖退出码或错误消息判断。测试：报告提交成功的用例断言 `tool.arguments` 记录了该选项；报告自身写入或提交失败的用例，用测试执行器保存的 argv、stderr、退出码与文件状态核对调用点与契约，不要求旧报告或不存在的新报告包含本次参数；未执行到注入点的用例单列，验证"不保证失败"。上游提交前重新评估：可改为只在打开断言的构建或测试构建中编译该选项。
2. 各失败阶段的测试来源：真实截断的调试文件验证实际的可恢复加载行为，以及随后 generate 阶段因没有可用样本而失败的结果与归类（`docs/profgen/impl/evidence/08/12_truncated_dwarf_results.json`）；真实损坏的 ELF 验证 load 阶段的兜底回调；对真实符号化调用点的注入验证 generate 阶段的兜底回调。理由：真实截断文件在不同位置截断时失败阶段不确定，单靠它无法稳定覆盖符号化阶段。

#### G.1.8 GNU 汇编 Thumb 函数的调试信息规范化（补丁 8，5.7.2）

1. 背景：板上采集发现 `__divsi3`、`__udivsi3` 等 GNU 汇编生成的 Thumb 函数，在 DWARF 中的起始地址带奇数位（Thumb 位），而符号化器按偶数地址查询，导致这些样本符号化出错（`docs/profgen/impl/13_patch8_thumb_dwarf.md`）。
2. 规则：只对 `EM_ARM` 且 IP 模式生效。DWARF 区间起点为奇数时，取 `low & ~1`：它必须落在唯一的可执行节内，且按同节中地址不大于它的最近映射符号确定的有效状态为 `$t`（不要求函数起点同址存在映射符号）。满足时区间两端都清除最低位。映射元数据缺失、节对应失败，或所在可执行节内存在任何同址映射冲突（此时整节不做规范化）时，不规范化该区间；sum/max 可以按原区间继续，按需边界功能仍按 5.7.2 的冻结规则失败。样本的 PC 与缓存键保持原值。补丁 8 原有的三项派生负对照（`$t` 改为 `$a` 或 `$d`、low_pc 落在 `add.w` 中间）按既有的 `--ip-aggregation=avg` 测试命令重跑，仍须在 boundary 阶段失败；其他配置按原有测试契约核对，不要求普通 sum/max 新增边界失败（附录 Q.5）。
3. 同一指令的别名查询：查询地址等于规范化后的区间起点 N 时，改用原奇数地址 N + 1 向符号化器查询，并核对两次结果的叶子帧文件、行与 discriminator 一致；不一致时整次转换在 generate 阶段失败，不猜测。报告记录 `thumb_dwarf_normalization.alias_query_count`、`alias_check_passed` 与前 50 个别名查询的原始结果。
4. 映射符号元数据加载失败时不做规范化，告警 `W_THUMB_DWARF_NORMALIZATION_UNAVAILABLE`，sum/max 聚合照常进行；做了规范化时告警 `W_THUMB_DWARF_ADDRESS_NORMALIZED` 并计数。

#### G.1.9 非叶子内联帧行号为 0（补丁 9，5.4.2）

1. 背景：原实现用"行号 − 函数起始行"计算调用点偏移。非叶子帧行号为 0 时无符号回绕，生成 65525 一类不存在的调用点（`docs/profgen/impl/15_patch9_nonleaf_line0.md`）。
2. 规则：IP 模式下，原始内联栈中任一非叶子帧的行号为 0，整个样本上下文排除，不构造部分内联树，也不自行推算偏移。排除的样本计入 `in_func_no_line`，并在其下单列子计数 `nonleaf_line_zero`；叶子帧行号为 0 仍按原规则只计 `in_func_no_line`。作为 `prev-inst` 前驱时视为没有有效行（G.1.1 的 `predecessor_no_line`）。
3. 影响：第一轮全部正式数据中共 2,736 条样本（0.0246%）被排除，全部来自 FFmpeg；spike 不受影响（G.5.2）。
4. 验收：lit 84 通过、1 不支持、1 预期失败、0 失败；C1 两遍各 636 条零差异；14 份历史输入重放中，成功的 4 份 profile 字节相同，其余 10 份保持原有失败。

#### G.1.10 其他

1. 同一地址的映射状态冲突，报告中给出的是该节第一个冲突地址（补丁 7 遗留说明，行为本身符合 5.7.2 第 3 条"同址冲突即失败"）。
2. 质量报告的 coverage 部分新增按名字合并的函数计数 `name_merged_functions` 与前 50 名单 `name_merged_top50`，不改变按名合并的逻辑（`docs/profgen/impl/08_patch6_report.md`）。

### G.2 评估执行的定义与规则

#### G.2.1 参考构建的定义（5.8、5.9）

| 名称 | 定义 | 用途 |
|---|---|---|
| R | IR 插桩（`-fprofile-generate` / `-fprofile-use`），生成与使用两侧都加 `-mllvm -disable-preinline` | 5.8 的 IR 层分支概率参考 |
| C | 前端插桩加覆盖映射（`-fprofile-instr-generate -fcoverage-mapping`） | 5.8 的行级执行计数参考（`llvm-cov export`） |
| G5 | IR 插桩，正常 flags | 5.9 的插桩 PGO 对照组 |

R 不能用前端插桩：前端插桩没有 `pgo-instr-use` 这个转储点（`docs/profgen/impl/11_eval_prep.md`）。

#### G.2.2 pseudo-probe

armv7l 上带 `-fpseudo-probe-for-profiling` 编译 Clang 崩溃（`docs/profgen/impl/10_host_verification.md`）。这是 probe 子方案（5.5）的阻塞项，不影响第一批 DWARF 路径。

#### G.2.3 板上执行规则

1. 依赖预检分两段：先以非 root 检查 PATH 中的命令，再开 root 检查只能由 root 读取的项；之后才设 governor 与运行 perf。
2. 数据拉回采用"拉回 → 校验 → 删除"，校验未通过不删除板上文件。
3. 只读命令失败最多重试 2 次；改变状态的命令一律不重试。
4. 按批次执行，并在每批前检查板上空间。
5. 以型号、架构、内核版本确认板子身份，不以 IP 地址确认。
6. 只写 `/opt/afdo_agent/`；不重启、不重新挂载、不安装或卸载 RPM；结束时恢复 root off 与 schedutil。

#### G.2.4 主机资源分级

开发主机由多条工作线共用，可用内存长期偏低，交换区常处于用满状态。主机任务按以下分级执行，运行中每 60 秒记录一次内存，连续两次可用内存低于阈值即终止本任务启动的进程，不触碰其他进程。

| 级别 | 适用 | 启动条件 | 限额 |
|---|---|---|---|
| 轻 | 转换、统计、板上诊断与拉取 | 可用内存 ≥ 4 GiB | 每任务 3 GiB / 200% CPU，串行 |
| 覆盖导出 | `llvm-cov export` | 可用内存 ≥ 10 GiB | 8 GiB / 200% CPU |
| 重 | LLVM 包增量构建 | 可用内存 ≥ 14 GiB（不检查交换区） | 10 GiB / 400% CPU，`-j4` |

#### G.2.5 覆盖导出

按源文件过滤不降低 `llvm-cov export` 的内存：只导出 `h264_cabac.c` 一个文件也在 3 GiB 处被终止，因为过滤前已经载入全部覆盖映射。改为整体导出：FFmpeg Thumb、A32 各一次，峰值约 4.3 GiB、耗时约 8 秒；两份都是 498 个文件、112,206 可执行行、8,298 已覆盖行（`docs/profgen/impl/evidence/16/09_whole_coverage_8g.json`）。

### G.3 预注册与修订链（第二阶段判据）

| 文件 | 提交 | 内容 | 结果 |
|---|---|---|---|
| `docs/profgen/eval/preregistration.md` | `7d3d9d9` | 性能 ε ±1%，质量 ε ±0.01（分支概率误差），预算 20k/100k/400k，每配置至少 5 次，bootstrap 默认独立重采样 | 有效；质量指标、重采样配对、固定样本量与区间方法由修订 3 补充 |
| `docs/profgen/eval/preregistration_amendment1.md` | `6629b2e` | 合格判据：有效频率 ≥ 97%、逐秒 `scaling_cur_freq` 等于固定值、温度 < 75°C | 第一轮 31 合格 / 28 异常（全部 FFmpeg，有效频率约 1.43–1.46 GHz）/ 11 待定。修订 3 提交后，对之后的采集与全部性能测量被修订 3 取代；已采集轮次按两套判据并列报告 |
| `docs/profgen/eval/preregistration_amendment2_rule.md` | `5219d15` | FFmpeg 频率诊断判定规则 | 首次运行用户态有效频率 1.404 GHz，判"疑似真实降频"，未生成修订 2 |
| `docs/profgen/eval/frequency_disambiguation_rule.md` | `7546425` | 固件降频与计数口径的区分规则 | 判 unknown（G.5.4） |
| 预注册修订 3（待登记） | — | 见下 | 附录 Q.5 的登记前核对完成后单独提交并推送。推送之前，不得对任何正式 sample profile 计算任何受控量（5.8 第 6 条），不论是否跨配置 |

预注册修订 3 的性质与内容：

1. 性质：采集之后的分析计划修订，不表述为采集前的原始预注册。提交文本写明登记时点：当时尚未计算任何正式 sample profile 的受控量，也未做待评配置之间的任何性能比较。同时披露登记前已经查看过的数据：第一轮资格结果、频率诊断、参考自比、覆盖导出的行数统计、补丁 9 重转的差异核对、正式 S 的工具质量报告（每次采集的 coverage 前 50 函数及占比、usable、`outside_dwarf_func` 与 `isa` 比例，`quality_round1.md` 中的变体盘点），登记前打开过的真实 profile 清单与在其上计算过的量（5.8 第 6 条的脚本开发数据规则），以及 G0 采样器预试的条件、轮数、原始耗时与开销（5.9 第 5 条）。修订的触发依据是资格数据与参考方法的性质，不是配置间比较的结果。
2. 合格判据：5.9 第 5 条的全部判据（含第 6 项 policy）、监测窗口、遥测执行、缺口与窗口完整性、日志检查、判定优先级、校准结果的传播；有效频率作为协变量（差值定义与 0.5% 界限）；频率离群的标记规则（含 MAD 下限）及其后果；散热前置条件。
3. 第一轮的处理：第一轮没有记录欠压告警、`cpuinfo_cur_freq` 与 policy，也没有批次前后校准，在新判据下资格为 unknown（已知异常的轮次仍判异常），不视为通过，也不用其他 RUN 的值补齐；新判据下第一轮的"遥测合格"子集为空。质量的主分析按 5.8 第 6 条的阶段规则使用第一轮；性能的主结果按原预注册使用全部轮次，干净子集分别按旧判据与新判据两栏给出。修订 3 不追认第一轮已经证明未降频。
4. 质量指标：5.8 第 5 条参考侧源函数的合并规则、跨侧对应表与裁决表（名字规则、完整身份清单、单候选的定义身份与行范围检查、多候选默认歧义、有正面证据的 `not_instrumented` 与外部 CU 清单、对应表覆盖完整性）、映射表规则（函数名、范围与名字闭包、边界排除组、键）、地址关系表、排除清单、条目分类（五类）与未对齐的处理、③ 的分母（评价域）、50% 与 80% 两档及互斥分桶的损失分解、行计数的主合并口径与两个敏感性口径、比较总体 U、M1（含权重与 n_eff）、M2、M2b 与区域敏感性分析的完整算法。
5. 负对照：5.8 第 7 条的对照集合、扰动方式、种子与重复次数。
6. 统计判读：5.8 第 6 条的判读方式与结果名称、ε、比较清单（逐项列出，全部为配对比较）、完整的 RUN 槽位表（每层 15 个，含既有与未来 RUN、按阶段的计划数与权重）、分层估计量、两种区间与退化样本规则（任一阶段差值极差 ≤ 10⁻⁹ 即退化）、工作模型与等价结论的限定、显式场景清单与模拟代码及种子的 SHA、`quality_equivalence_enabled` 的取值及其依据（附录 Q.5 第 9 项的模拟结果；全部完整运行取合取，模拟与正式分析共用同一实现模块）、配对、有效 RUN、原因码白名单与重采、停止与恢复的状态机、自动证据记录、恢复的三部分证据与"停止缺失"、缺失、干净子集的地位、受控量清单、计算日志。
7. 性能：5.9 第 2 条的完整分组矩阵（G1–G4 按补零展开；如采用较小矩阵，逐项列明固定项与未评估的交互）；每组固定轮数 N 的公式、G0 预试与计算结果（5.9 第 5 条）；耗时按中位数相对差、等价区间 ±1%；质量与性能的统计量、ε 与停止规则分开。原预注册"RPi4 证据不足时后续加轮数"由本条取代。
8. 登记并锁定的内容与 SHA-256（5.8 第 6 条"登记内容的划分与门禁"）：① 分析协议、评估脚本及其依赖与配置、对象登记表（各对象的 ①–③′、n_eff、K），以及只由 ELF、调试文件与参考数据预先生成的跨侧对应表与裁决表、映射表、排除清单、边界排除组、U 与函数权重；② 登记时已存在的输入清单（正式 S 原件、补丁 9 工具 SHA、插桩与覆盖参考文件 SHA）；③ 完整的 RUN 槽位表与既有 RUN 的初始化收据。补采原件按槽位写入只追加的数据收据，不修改 ①–③。
9. 门禁与变更：脚本在计算前按 5.8 第 6 条核对修订 3 已提交并推送、①②③ 的 SHA 一致、原件与槽位和收据的对应、每个槽位至多一次成功、计算日志 SHA 链完整；等价判读前核对全部槽位都有终态收据。登记后对 ①–③ 的任何修改都必须作为新的预注册修订（修订 4 及以后）重新登记并写明原因，不得在修订 3 名下修改后重算。修订 3 的提交与推送成功的记录在正式指标计算之前保存。
10. 其余（性能 ε ±1%、预算、重复次数下限、种子与次数、训练与测试输入、换出阈值、原始数据保留）不变。原预注册第 3 节第 5 条的任务停止条件不变，并用于重采前的失败分类；原预注册"干净重复不足……需要补采"对质量由固定槽位取代，对性能由固定 N 取代。
11. 理由：诊断表明，内核温控降频会同时体现在 `scaling_cur_freq`（降到 600 MHz）与实测周期频率上。FFmpeg 诊断运行中温度为 61–67°C，逐秒 `scaling_cur_freq` 均为 1.5 GHz，未显示异常，但该次没有记录欠压告警，周期频率偏低约 5% 的原因仍未确定；后续纯计算诊断中欠压告警为 0，这不能作为 FFmpeg 的同期观测。按原判据，现有遥测未见异常的轮次也会全部判为异常；新判据改为可逐秒观测的内核频率、固件时钟、policy、温度、欠压与批次前后的硬件周期校准，这是新的操作性资格规则，不是对旧轮次的追认。质量统计改为固定样本量、按阶段分层并加 t 区间，性能改为固定轮数，都是因为 RUN 数少时 percentile 区间偏窄，而按区间宽度决定补采或加轮属于数据依赖的停止。

### G.4 5.8 判据修订的理由

1. 在本次 spike、指定转储点与当前匹配器实现下，严格匹配在参考自比上只有 3/22（G.5.3），这 3 条不足以代表整体代码质量；放宽语义校验会违反 5.8 第 3 条的原则，所以不放宽，分支概率误差改为描述性。
2. sample profile 本身按源码行记录计数；经过按地址符号化建立的位置映射，可以与插桩覆盖的逐行执行计数形成可比较的子集，对齐不依赖 IR 形态，也不受 pass 边界差异影响。
3. IP 计数反映"执行次数 × 代价"，插桩计数是执行次数。二者绝对值不可比，主指标用排序一致性（M1）与热点重叠（M2）；但行间代价不同时排序也会改变，M1 不证明计数正确（5.8 第 5 条"指标的含义与盲区"）。
4. 已知局限：插桩构建与被采样构建的优化不同，两侧可对齐的行不完全相同，由比较总体 U 的三个比例报告；FFmpeg 训练输入的已覆盖行比例约为 7.4%，这个数字不是 U 的比例。M1 在 U 上计算，M2 的热点集合取自 U 中参考计数大于 0 的行。
5. 行级指标对 head、补零、内联上下文与 discriminator 归属没有区分力，这些由 5.9 的消费端检查与性能测量评估。

### G.5 实测事实

#### G.5.1 第一轮采集（RPi4，armv7l）

70 组、106 次正式采集，target 样本 11,131,603，usable 8,235,324，身份全部 verified。集成用例 5/5 成功，真实 `[unknown]` 样本 335 条，生成 profdata 14 份。LOST 与样本权重核对已闭合。证据：`docs/profgen/impl/12_board_round1.md`。

#### G.5.2 补丁 9 重转

固定工具 SHA-256 `2e8895afce661b5fdc8cacab2b3323496fca51af7bd7b51c3753aa8328b7d0d5`。106 份原件全部重转，另含 20 份按周期加权的 profile：usable 由 8,235,324 降为 8,232,588，差值 2,736 与独立统计一致；FFmpeg Thumb 移出 2,366 条、A32 移出 370 条，spike 为 0；56 份 profile 字节不变；非预期差异 0。补丁 8 的结果原样保留。证据：`docs/profgen/impl/evidence/16/08_p9_reconversion_summary.json`。

#### G.5.3 IR 参考自比

R 参考在 spike 上与自身比较，Thumb、A32 均为 22 条条件终结指令、3 条严格匹配（13.64%）。候选转储点 `-print-before=inline` 能编译，但每个 ISA 输出 13 次转储，尚未与 sample 侧配对比较，不采用。证据：`docs/profgen/impl/evidence/16/01_reference_ir_preparation.json`、`02_reference_structure.json`。

#### G.5.4 频率与散热诊断

1. 单核纯计算 60 秒：逐秒周期频率 1.4999–1.5000 GHz，最高 64.8°C。
2. 四核纯计算：约 25 秒升到 79°C，80.3°C 时 `scaling_cur_freq` 降到 600 MHz，周期频率降到 0.79 GHz，降温后恢复 1.5 GHz；温度门禁结束对照，低于阈值只连续 2 秒，按规则判 unknown。
3. 固件来源：`vcgencmd` 与固件 `get_throttled` 节点都不存在；只有 `rpi_volt` 的欠压告警可读，单核与四核对照全程为 0。FFmpeg 没有在这次诊断中运行。
4. 结论：约 80°C 时出现的降频与内核调频记录（`scaling_cur_freq`）同步出现，说明内核温控降频可以由它观察到；这次遥测不能证明其他降频机制也都能由它观察到。散热不足以支撑多核满载。FFmpeg 周期频率偏低约 5% 的原因仍未确定。
5. 更正：14 报告把 `in0_lcrit_alarm` 称为欠压 sticky 位，这不准确。驱动名义上每 2 秒（延迟工作，不是保证的时限）向固件查询一次并清除固件的 sticky 位，sysfs 返回的是最近一次查询结果（`raspberrypi-hwmon.c:31–36`、`:72`、`:80`）。证据：`docs/profgen/impl/14_ffmpeg_frequency_diag.md`。

### G.6 v0.8 请评审方确认的问题

v0.8 列出的五个问题与三家的回答见附录 H.4；v0.9 六项重点检查的处理见附录 I；v1.0 确认评审的处理见附录 J；v1.1 评审的处理见附录 K；v1.2 评审的处理见附录 L；v1.3 评审的处理见附录 M；v1.4 评审的处理见附录 N。

## 附录 H：v0.8 评审意见处理（Claude Code、Codex、Kimi Code）

三家的结论都是"修改后可以进入第二阶段评估"。严重问题合计 1 项（Claude Code：合格判据看不到运行中途的欠压与固件调频），Codex 与 Kimi Code 没有严重问题。三家都确认附录 G.1 与冻结正文没有实质冲突，第一阶段不需要重开，补丁 1–9 的验收不受影响。下表按严重程度列出处理结果；"来源"一栏写明提出该问题的评审方，"采用"一栏写明最终采用了谁的方案以及原因。

### H.1 严重

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| 合格判据不足以排除降频：`scaling_cur_freq` 只是内核请求的频率；欠压告警由驱动每 2 秒清除一次，只读运行前后会漏掉中途欠压；撤掉有效频率后实际只剩温度一项 | Claude Code S1；Codex 重要 5；Kimi Code 一般 5（Kimi 认为原判据充分） | 采纳 | 采用 Claude Code 的五项判据（逐秒 `scaling_cur_freq`、逐秒 `cpuinfo_cur_freq`、温度、逐秒欠压告警加 dmesg、批次前后校准夹测）与"有效频率作组间平衡协变量"；采用 Codex 的标签措辞"现有遥测未观察到异常"、固件降频状态单列 unknown、读数缺口判 unknown，以及证据更正（FFmpeg 那次运行没有欠压记录）；采用 Kimi Code 的亚秒级离群扫描作兜底。另把欠压的读取窗口延到负载结束后至少 4 秒，覆盖驱动的 2 秒轮询。Kimi Code 的"充分"结论不采纳：Claude Code 与 Codex 都以驱动源码证明告警会被清除，只读端点确实会漏 | 5.9 第 5 条；G.3；G.5.4 |

### H.2 重要

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| M1 缺少并列、常数序列、权重集中与小样本的规则 | Claude Code I1；Codex 重要 3；Kimi Code 重要 1 | 采纳 | 并列取平均秩、参考侧恒定的函数排除：三家一致。sample 侧恒定记 ρ=0、不排除：采用 Claude Code（与 Kimi Code"权重留在分母"等效）；Codex 的"出现无定义即整次 M1 不判读"不采纳，因为低预算下几乎每次采集都有全 0 的函数，M1 将无法使用，而记 0 能保持函数集合与权重不随配置变化，并如实惩罚稀疏。参与行下限取 5 且参考秩方差不为 0（Codex、Kimi Code），10 行作敏感性分析（Claude Code 的主张反过来用）。合并用参考计数加权平均，不用 Claude Code 的 Fisher z：小函数加并列时 ρ=±1 很常见，z 变换需要额外的截断参数，而推断已由 bootstrap 承担。报告 n_eff 与等权中位数（Claude Code），n_eff 门槛取 3 而非 5：spike 只有 11 个函数，取 5 会使聚合方式的主评估只能作描述（v1.0 更正：此理由不成立，见附录 I.4 第 1 条） | 5.8 第 5 条 |
| 统计判读规则不完整 | Claude Code I1；Codex 重要 3 | 采纳 | ε 是绝对差、M1 与 M2 必须都有定义且都落入区间才称等价：采用 Codex。以逻辑 RUN 为重采样单位、同一 RUN 转换出的不同配置按 RUN 配对：采用 Codex，这些配置来自同一份原始数据，按独立样本处理会高估方差。置信区间保留原预注册的 percentile，不改 BCa（Claude Code）：5 个簇时加速常数估计不稳定。区间过宽时补采到 10 次、最多 15 次，只按半宽决定：采用 Claude Code（v1.0 改为固定样本量，见附录 I.4 第 2 条） | 5.8 第 6 条 |
| M1/M2 对部分评估维度没有区分力 | Claude Code I2；Codex 重要 4 | 采纳 | M2 改为热点集合重叠：采用 Claude Code 的思路；H_ref 截断处并列全部纳入：采用 Codex；H_s 改为按 sample 计数取前 \|H_ref\| 行、截断处并列按份额计入（自拟），不采用 Claude Code 的"按 sample 计数质量取 80%、并列按参考次序"，因为 sample 计数反映时间、质量截断含义不同，按参考次序破并列会把参考信息带入 sample 侧。原"计数大于 0 的比例"改为描述性的 M2b。一行单区域的敏感性分析：Claude Code。M1 的含义与盲区（排序不能消除代价差异的反例、不证明计数正确）：采用 Codex。head 与补零不由行级指标筛选、移到 5.9：两家一致 | 5.8 第 5、9 条；5.9 第 2 条；第 12 节第 2 条 |
| 登记时机与内容不足以保证"先登记、后比较" | Claude Code I3；Codex（登记时机一节）；Kimi Code（登记时点声明） | 采纳 | 登记点提前到"对任何正式 sample profile 计算指标之前"：采用 Claude Code，比 Codex 的"配置间比较之前"更严，避免先看单个配置的分布再定参数。登记内容含完整算法、脚本与 SHA、输入清单、补采规则、合格判据：Claude Code 与 Codex 合并。标明是采集后的分析计划修订并披露已看过的数据：Codex。写入登记时点声明：Kimi Code。修订 1 被取代的范围、第一轮欠压未记录判 unknown：Claude Code 与 Codex 一致。脚本门禁：Claude Code | G.3；5.8 第 6 条；第 10、12 节 |
| 行级对齐会丢信息：起始行加偏移不能还原文件与回绕后的行号；先汇总再分组会丢函数归属；插桩侧不能直接用 segment；discriminator 合并与 llvm-cov 语义是否一致 | Codex 重要 1；Claude Code G1；Kimi Code 重要 2 | 采纳 | 按地址符号化建立"profile 键 → 源位置"的映射表、歧义键排除并计数：Claude Code 与 Codex 一致。汇总键保留源函数身份：Codex。合并顺序"先跨上下文求和、再在 discriminator 间取最大"并直接用 lcov 的 `DA` 行计数：采用 Claude Code，它引用了 llvm-cov 的源码（跨实例求和后取该行起始区域的最大值），这也回答了 Kimi Code 未核实的问题，Kimi Code 提出的"可能应求和"因此不采纳（v1.0 更正：源码不能证明合并顺序，见附录 I.4 第 3 条）。行所属函数取自覆盖 JSON 的函数区域：Codex。lcov 导出的内存未核实，列入执行前核对 | 5.8 第 5 条 |
| 比较总体前后矛盾，覆盖比例分子分母不一致 | Codex 重要 2 | 采纳 | 采用 Codex 的比较总体 U 定义：读取配置指标前固定、包含参考计数为 0 的行、缺失按零次观测，以及三个比例；更正"指标只在 7.4% 的行上计算"的说法 | 5.8 第 5 条；G.4 |
| G.1 的部分概括与已验收行为不一致（Thumb 条件、截断 DWARF 的阶段、报告提交顺序的例外、LOST 溢出的范围、遗漏的合并函数字段）；G.1.1 中"区间"有歧义 | Codex 重要 6；Claude Code G2 | 采纳 | 按 Codex 给出的、以补丁与证据为准的写法改写 G.1.1、G.1.3、G.1.6–G.1.8、G.1.10；G.1.1 的"枚举区间"与"第二个函数的第一条指令计入 `first_instruction`"采用 Claude Code。G.1 的优先级限定为明确列出的修订点：Codex | G.1；状态栏 |

### H.3 一般

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| 行号非 0 但小于函数起始行的情况没有统计 | Claude Code G3 | 部分采纳 | 改为在评估侧统计 `line_before_start`，不给工具加报告字段：只为观测而改动已验收的工具不划算，评估侧的符号化映射表能得到同样的数 | 5.8 第 5 条 |
| 测试注入选项的可追溯性与上游可接受性 | Claude Code G4；Kimi Code 一般 6 | 部分采纳 | 不新增 `test_injection` 字段：现有实现中注入必定失败、非 0 退出、profile 不提交，报告的 `tool.arguments` 已记录该选项、失败消息带 "injected"，误用已可识别（v1.0 更正：注入不必定失败，消息也不都带 injected，见附录 I.4 第 4 条）。采用 Kimi Code 的建议：上游提交前重新评估只在测试构建中编译 | G.1.7 |
| 别名查询不一致时的失败粒度未写明 | Kimi Code 一般 4 | 采纳 | 按补丁 8 已验收的行为写明：整次转换在 generate 阶段失败，并列出报告字段 | G.1.8 |
| 文字一致性：正文缺少指向附录的标注；"第 9 节的 C 构建"引用错误；内联局限的适用范围；第 10 节步骤 1、7 的旧判据残留；第 12 节编号乱序且缺修订 3；13.64% 外推过强 | Claude Code G5；Codex 一般 1；Kimi Code 一般 1–3 | 采纳 | 受影响条款末尾加附录指引；引用改为附录 G.2.1；局限限定为描述性分支指标；步骤 1 的 IR 重跑改为可选，步骤 7 改写；第 12 节重排并增加修订 3；13.64% 的结论限定在本次 spike、转储点与匹配器实现，自比结果标记 `reference_self_check`（Codex） | 状态栏；5.4.2、5.4.8、5.6.1、5.6.3、5.7.2；5.8 第 4、5 条；第 10、12 节 |
| 附录 G.1 的长期治理 | Kimi Code 一般 7 | 采纳 | 第二阶段冻结版把 G.1 并入正文，附录只留历史 | 状态栏 |
| 逐秒采样可能漏掉亚秒级降频 | Kimi Code 一般 5 | 采纳 | 对合格轮次的有效频率做离群扫描 | 5.9 第 5 条 |
| 14 报告把欠压告警称为 sticky 位 | Claude Code S1 第 2 点 | 采纳 | 在 G.5.4 更正；14 报告的原文由执行方在下一次提交中修正 | G.5.4 |

### H.4 v0.8 附录 G.6 五个问题的回答汇总

1. 行级对齐：三家都认为方向正确。需要改为按地址符号化的映射表、保留函数归属、按 llvm-cov 语义合并；已按 H.2 处理。
2. M1、M2 参数与 ε：±0.02 可以作为预先选定的判读界限，但须同时登记联合等价、补采与配对规则，并说明它不是已验证的精度；已按 H.2 处理。
3. 取消结构覆盖门槛：三家同意。补充的风险（一行多块、head 与补零失去指标、旧判据残留）已按 H.2、H.3 处理。
4. 合格判据：Claude Code 与 Codex 认为不充分，Kimi Code 认为充分；采纳前两家的意见，按 H.1 处理。
5. G.1 与冻结正文：三家都认为没有实质冲突；概括不准确之处按 H.2 最后一行处理。

### H.5 执行前须核对的事项

v1.0 起本节由附录 I.5 取代，以下保留 v0.9 原文。以下几点在 v0.9 中按评审方引用的源码与补丁写入，但还没有在本仓库的实现或板子上逐一核对，登记修订 3 之前由执行方核对，结果不符时先修订本文：

1. G.1.1 的"枚举区间"与"前驱末端相接"条件，与补丁中 `prev-inst` 的实现及测试一致。
2. G.1.7 中注入时报告 `tool.arguments` 记录该选项、失败消息带 "injected"。
3. G.1.8 的映射状态查找方式与补丁 8 一致。
4. RPi4 上以 root 读取 `cpuinfo_cur_freq` 可用；逐秒读取对负载的影响可以忽略；dmesg 欠压事件的检查方法可行。
5. spike 上 lcov 的 `DA` 行计数与 JSON 推得的行计数一致；FFmpeg 的 lcov 导出在覆盖导出级别限额内完成。

## 附录 I：v0.9 评审意见处理（Claude Code、Codex、Kimi Code）

三家的结论：Claude Code "修改后可以登记预注册修订 3 并进入第二阶段评估"（严重 0、重要 4、一般 5）；Codex "修改后可以"（严重 0、重要 7、一般 2）；Kimi Code "可以登记"（严重 0、重要 0、一般 6）。三家都没有严重问题，都认为第一阶段不需要重开；本版不改补丁 1–9，不改已有 golden 值，G.1 只更正文字。下表按严重程度列出处理结果；"来源"一栏写明提出该问题的评审方，"采用"一栏写明最终采用了谁的方案以及原因。标"自拟"的内容是本版为闭合问题新写的规则，三家都还没有看过，列在 I.6。

### I.1 严重

无。

### I.2 重要

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| 映射表只对"有样本的函数"建立，U 与歧义集合因此随采集轮次变化，与"U 不随样本改变"矛盾；未对齐键没有规则；键计算须复现的工具规则没有写明 | Claude Code I1；Codex 重要 1；Kimi Code 一般 3（同一问题的较轻表述） | 采纳 | 合并 Claude Code 与 Codex：映射表只由 ELF、调试文件与参考决定；地址只取已证明的指令起点、歧义键涉及的全部行整行移出 U、映射表与排除清单与 U 与权重分别登记 SHA（Codex）；逐条列出须复现的工具规则（行号 0、`& 0xffff`、基础 discriminator、G.1.8）、未对齐比例超过 1% 时指标无定义、登记前预先生成（Claude Code）。Kimi Code 的"无样本函数按行表判定"由新定义直接覆盖。自拟："映射范围"按内联树包含参考执行函数的顶层函数界定，范围外的样本单独报告、不计入未对齐比例；否则参考侧未执行的函数中的正常样本也会触发 1% 规则 | 5.8 第 5 条 |
| discriminator 的合并顺序不能由 llvm-cov 的区域合并规则推出 | Codex 重要 2；Kimi Code（认为已由源码核实一致） | 采纳 Codex | 主口径保留 max_d Σ_context，明确为预先选定的代理口径，不宣称与 llvm-cov 语义等价；登记 S_alt = Σ_context max_d 敏感性，结论改变时报告"合并口径敏感"、不选有利者（Codex）。Kimi Code 核实的是参考侧的语义（同范围区域求和、行内取最大），这一点成立；但它不能证明 discriminator 与覆盖区域一一对应，Codex 的互补上下文反例（100 对 200）说明顺序确实影响结果，所以不采纳"已闭合"。自拟：另加 S_sum = Σ_context Σ_d，覆盖 Kimi Code 上一轮"可能应求和"的疑问。H.2 中"已由源码证明"的理由作废（I.4） | 5.8 第 5 条 |
| M2 用零计数行补足热点名额，全部未观测也可得到 K/N；空参考、空函数集合未定义 | Codex 重要 3；Claude Code G2（截断写法与整数比较）；Kimi Code 一般 4（T 的口径） | 采纳 | H_s 只从正计数行选取、分母固定为 K、全零时 M2 = M2b = 0、U 为空或 T = 0 时无定义、M1 无函数时无定义、权重 w_f 显式写出、"恒定记 0"改称评分约定：Codex。截断写成 5·c_k ≥ 4·T 的整数比较、份额规则等于随机打破并列的期望：Claude Code。T 取 U 内参考计数之和：Claude Code 与 Kimi Code 一致。H_ref 改写为"参考计数 ≥ v 的全部行"，与原意相同、更易实现 | 5.8 第 5 条 |
| spike 的参考权重高度集中（n_eff 约 1.3），M1 在 spike 上必然只作描述，按联合规则 spike 得不到任何等价结论 | Claude Code I2；Codex 重要 3 的附带意见 | 采纳 Claude Code 方案 A | n_eff 只由参考数据计算、登记前写成表；n_eff < 3 的对象只用 M2 判读并写明"M1 未判读"；聚合方式与 skid 的判读以 n_eff ≥ 3 的对象为准。不采用方案 B（按行数加权）：它改变指标定义，并让几乎没执行过的函数获得与热点函数相当的权重。门槛 3 作为预先选定的规则保留，不再用"函数个数"作理由（Codex 指出函数个数推不出 n_eff）。H.2 的理由更正（I.4） | 5.8 第 5、6、9 条；第 12 节第 1 条 |
| 5 个 RUN 时 percentile 区间偏窄（覆盖约 85%）；按区间半宽决定补采属于数据依赖停止，普通区间在随机停止点不保持名义覆盖率 | Claude Code I3；Codex 重要 4；Kimi Code 一般 5 | 采纳，三家合并 | 固定终点：每个比较层最终 15 个 RUN，第 5、10 个只作描述，判读只做一次（Codex 推荐的较简单方案）；不采用 Claude Code 的"按较大半宽补采"，因为在 Codex 指出的问题下它仍是数据依赖停止。在固定的 15 个 RUN 上同时要求 percentile 与 t（配对 n−1、独立 Welch）都落入 ±ε（Claude Code）：n=15 时 percentile 单独约 92%，仍偏窄。区间方法固定、不得因宽度改换方法（Kimi Code）。同一 RUN ID 集合、两指标共用重采样索引、转换失败不记零也不单侧删除、按采集阶段分层（Codex）。代价：板上采集量增加，见 I.6 | 5.8 第 6 条；G.3 |
| 五项遥测判据不能直接实现：缺口没有定义、采样器可能被饿死、dmesg 标记要写 `/dev/kmsg`、状态优先级与窗口未定义、校准批次与失效传播未定义、离群扫描无规则、`cpufreq_out_of_sync` 的描述不准 | Claude Code I4；Codex 重要 5；Kimi Code 一般 1 | 采纳，三家合并 | 采样器 root、nice 0、绑核，缺口按 1.5 秒与 3 秒定义，dmesg 按 CLOCK_MONOTONIC 窗口检查、不写 kmsg，校准逐 CPU 串行、首尾不完整区间不判、校准期间温度同样适用，离群按"中位数减 3×MAD"只标记加敏感性分析：Claude Code。判定优先级（异常 > unknown > 合格、原因并存）、四个时间点的统一窗口、dmesg 有序游标、驱动查询失败不把缓存 0 当成新鲜结果、批次定义、校准失效按整批传播、有效频率差的分母：Codex。`pr_debug` 与读取会调度 policy 更新：Kimi Code 与 Claude Code。离群规则用 Claude Code 的具体阈值而不是 Codex 的"只列分布"：阈值预先写定后不再留事后选择的空间，后果同样限于标记与敏感性分析。三家引用的内核行号不一致（Codex 按上游 v6.12，Claude Code 与 Kimi Code 按板上 6.12.80 树），正文改为引用函数名，行号在 I.5 按板上内核源码核对。自拟：读取引起 policy 更新的影响未核实，所以以首次偏离为准，之后的读数不用于证明已恢复 | 5.9 第 5 条；G.3 |
| G.1.7 写"注入必定失败、消息带 injected"，与已验收代码不符 | Codex 重要 6；Claude Code G1 | 采纳 | 采用 Codex 的写法：只有实际执行到注入点才触发，消息不保证带 injected；正式评估的输入准入直接拒绝含非空注入选项的生成命令，不依赖退出码或消息。事实部分采用 Claude Code 的核对。本轮在补丁文件中复核：带 "injected" 的消息只出现在补丁 6、补丁 8 的运行文件与调试文件加载、符号化注入点（v1.1 更正：全部由补丁 6 引入，`invalid-image` 不带该字样，见附录 J.4）。仍不新增 `test_injection` 字段，理由改为"命令清单可审计、评估准入按命令拒绝"（I.4） | G.1.7；H.3 |
| 补零移到 5.9 后分组表没有补零维度；5.9 引用的等价区间与原预注册的性能口径冲突 | Codex 重要 7 | 采纳 | G1–G4 对每个入围的聚合方式与 skid 组合按补零展开；较小矩阵须在修订 3 中列明固定项与未评估交互，不得对未覆盖组合宣布默认行为已验证。性能按耗时中位数相对差、±1% 判读，5.8 的均值与 ±0.02 只用于质量 | 5.9 第 2、5 条；G.3 |

### I.3 一般

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| G.1.1 把每个枚举区间的首指令都写成 `first_instruction`，与实现不同 | Codex 一般 1；Claude Code G1（核对结果一致） | 采纳 | 改为"函数已枚举指令序列的第一条指令"；同一函数后续 DWARF 区间的首指令为 `range_gap`，映射区间变化为 `data_or_state_change`，按实现的检查顺序归类。本轮在补丁 5 的 `IPFunctionBoundaries::predecessor` 中复核一致 | G.1.1 |
| `HasMultipleRegions=false` 不等于"一行只有一个区域"；lcov 不导出该字段 | Codex 一般 2 | 采纳 | 改称"在本行起始的非 gap 区域入口不超过一个"，写明不证明单区域或单基本块；标志由 JSON segments 按同版本谓词提取或经 Coverage API 导出 | 5.8 第 5 条 |
| G.1.8 写"不规范化受影响的区间"，实现是同节存在任何同址冲突即整节不规范化；补丁 8 的负对照在新表述下是否仍失败 | Claude Code G1；Kimi Code 一般 4 | 采纳 | 按实现改写（Claude Code）；补丁 8 的派生负对照在本规则下仍须失败，列入 I.5 重跑（Kimi Code） | G.1.8；I.5 |
| 比较范围没有预先规定；派生配置缺失时的处理没有规定 | Claude Code G3 | 采纳，阈值调整 | 每个候选只与基准（`max`、skid=`none`、权重=`period`）比较、清单在修订 3 中逐项列出：Claude Code。缺失的门槛由"少于 5 对"改为"少于固定的 15 对"，与固定样本量一致（Codex 重要 4） | 5.8 第 6 条 |
| 修订 3 的披露清单遗漏工具质量报告；U、映射表、n_eff 可以在登记前生成；脚本开发能用什么数据未写明 | Claude Code G4 | 采纳 | 披露清单加入正式 S 的工具质量报告与变体盘点；预先生成的产物与脚本一起登记 SHA；脚本开发只用合成夹具与非正式校准 profile | G.3 第 1、7 条 |
| 登记后发现脚本缺陷时如何处理未写明，SHA 门禁可能诱使静默绕过 | Kimi Code 一般 6 | 采纳 | 登记后任何修改都作为新的预注册修订重新登记并写明原因，不在修订 3 名下修改后重算 | 5.8 第 6 条；G.3 第 8 条 |
| 1.455 GHz 没有出处；`CoverageExporterLcov.cpp` 的目录未写明；JSON 没有函数行范围字段 | Kimi Code 一般 2 | 采纳 | 写明 1.455 GHz = 固定频率的 97%，沿用修订 1 的口径；路径写全；行所属函数由 regions 数组推导 | 5.8 第 5 条；5.9 第 5 条 |
| 驱动的轮询是延迟工作，2 秒不是保证的刷新时限 | Codex 重要 5 第 3 点 | 采纳 | 正文与 G.5.4 改为"名义上每 2 秒" | 5.9 第 5 条；G.5.4 |
| H.5 不完整 | Claude Code G5；Codex（建议 6–12）；Kimi Code 一般 2 | 采纳 | 三家的补充项合并为 I.5，取代 H.5 | I.5 |

### I.4 对前一版附录的更正

1. H.2 第 1 行"n_eff 门槛取 3 而非 5：spike 只有 11 个函数"的理由不成立：起作用的是权重的集中程度，spike 的 n_eff 约为 1.3。门槛 3 仅作为预先选定的规则保留，判读方式按 5.8 第 5、9 条。
2. H.2 第 2 行"区间过宽时补采到 10 次、最多 15 次"已由固定样本量取代。
3. H.2 第 5 行"合并顺序由 llvm-cov 源码证明、Kimi Code 的'可能应求和'不采纳"不成立：源码只说明参考侧的语义，主口径改为预先选定的代理口径，并登记 S_alt、S_sum 两个敏感性口径。
4. H.3 第 2 行"注入必定失败、失败消息带 injected"不符合实现；不新增字段的结论不变，理由改为 I.2 中所述。
5. H.5 由 I.5 取代。

### I.5 执行前须核对的事项（取代 H.5）

v1.1 起本节由附录 J.5 取代，以下保留 v1.0 原文。

登记修订 3 之前由执行方完成。结果与本文不符时先修订本文，再登记。除第 12 项外都不需要板子；全部事项都不计算正式 sample profile 的 M1、M2、M2b。

| 编号 | 事项 | 状态 |
|---|---|---|
| 1 | G.1.1 的前驱条件与原因分类与补丁 5 一致 | 已核对（Claude Code、Codex；本轮复核 `predecessor`），文字已按 I.3 更正 |
| 2 | G.1.7：对每个注入点断言 `tool.arguments` 记录了该选项、该注入点确实被执行、失败阶段与输出契约；未提供调试文件或报告路径时请求对应注入不保证失败；评估准入拒绝含注入选项的命令 | 部分核对（消息标记只覆盖部分注入点）；测试待补 |
| 3 | G.1.8 的映射状态查找与同节冲突粒度与补丁 8 一致；补丁 8 的派生负对照（`$t` 改为 `$a`/`$d`、low_pc 落在 `add.w` 中间）在本规则下仍然失败 | 查找方式已核对（Claude Code、Codex）；负对照待重跑 |
| 4 | G.1.3 第 4 条的提交顺序例外、G.1.10 第 2 条的 `name_merged_functions`/`name_merged_top50`，与补丁 6 的实现与测试一致 | 待核对 |
| 5 | 映射表：在一份非正式的校准 profile 上，映射范围内工具写出的键 100% 能在映射表中找到；两个命中函数集合不同的 RUN、删除热点函数全部条目、加显式零条目、改变预算，映射表、排除清单、U 与权重的 SHA 都不变；原始 discriminator 不同而写出键相同、Thumb 别名、非叶子行号 0、偏移碰撞、不同构建路径、歧义键与正常键同时贡献同一行 | 待实现与核对 |
| 6 | 只用参考数据与 U 计算各构建、ISA、输入的 n_eff，写成表；确认 5.8 第 9 条的判读方式 | 待计算 |
| 7 | M1、M2 合成夹具：N=15、K=9、sample 全零时 M2 = 0；只有一个正计数热点；正计数并列；正计数行不足 K；T = 0；U 为空；M1 无入选函数；10 行敏感性下的空函数集合；累计恰好等于与刚好跨过 80% | 待实现 |
| 8 | 合并口径：互补上下文（d0/d1 = 100/0 与 0/100）三个口径的值；同一内联函数在不同调用点走不同分支；同一行多个覆盖区域与不同 discriminator；同时保存覆盖区域边界，不以聚合结果相等作为语义证明 | 待实现 |
| 9 | 区间模拟：在正态、偏斜、离散与稀有事件的合成分布上，真实差值为 0 与 ±ε 时各 1,000 次重复，组合规则在 n=15 时的覆盖率不低于 93%，保存模拟种子；配对与独立两种实现分别核对 | 待执行 |
| 10 | 统计规则夹具：配对 RUN 顺序不同而 ID 相同；单边缺失与转换失败；多个采集段只贡献一个 RUN；第 5 个 RUN 已显示等价时脚本仍不输出判读；分阶段报告 | 待实现 |
| 11 | 性能矩阵：从登记矩阵自动校验每组的聚合方式、skid、head、补零、profi 参数；缺少补零对照时拒绝输出"补零默认值已验证"；同一数据分别走质量与性能判读，确认均值与中位数、绝对差与相对差、两个 ε 没有混用 | 待实现 |
| 12 | 板上（需要板子，加装散热后）：root 读取 `cpuinfo_cur_freq` 可用；"解码满载 + 采样器"试运行，统计读数间隔分布与采样器对解码耗时的影响；dmesg 时间戳与 CLOCK_MONOTONIC 的对应、有序游标可行且不写 `/dev/kmsg`；hwmon 查询失败能否观测；逐秒读取不依赖动态调试输出；5.9 引用函数在板上内核 6.12.80 源码中的行号 | 待板上执行 |
| 13 | 覆盖参考：spike 上 lcov 的 `DA` 与 JSON 推得的行计数一致；由 regions 推导的函数行范围与 lcov/JSON summary 交叉一致；`HasMultipleRegions` 从 segments 提取的结果与 Coverage API 一致（wrapped region 加本行入口、两个本行入口、只有 gap、skipped region）；FFmpeg 的 lcov 导出在覆盖导出级别限额内完成 | 待核对 |
| 14 | 登记：脚本及其依赖与配置、输入清单、映射表、排除清单、U、权重、n_eff 表的 SHA-256 写入修订 3；修订 3 提交与推送成功的记录在正式指标计算之前保存 | 登记时执行 |

### I.6 本版新写、尚未经评审的内容

以下五条已经 v1.0 确认评审，处理见附录 J.2、J.4。

1. 映射范围的界定（内联树包含参考执行函数的顶层函数），以及范围外样本不计入未对齐比例（5.8 第 5 条）。
2. 第二个合并敏感性口径 S_sum（5.8 第 5 条）。
3. 固定 RUN 数取 15，以及第一轮 RUN 计入 15 个、主分析合并各阶段并分阶段报告的规则（5.8 第 6 条）。板上影响：每个采集制度（负载、ISA、预算）都要补到 15 个逻辑 RUN。
4. `cpuinfo_cur_freq` 以首次偏离为准、之后的读数不用于证明已恢复（5.9 第 5 条）。
5. monitor_start 不晚于负载开始前 2 秒（取自 Claude Code 的 dmesg 窗口 [开始 − 2 秒, 结束 + 4 秒]，扩展到 sysfs 读数）（5.9 第 5 条）。

## 附录 J：v1.0 确认评审意见处理（Claude Code、Codex、Kimi Code）

三家的结论都是"修改后可以登记"，没有严重问题。重要问题：Codex 7 项、Claude Code 5 项、Kimi Code 0 项；一般问题：Codex 1 项、Claude Code 6 项、Kimi Code 4 项。三家都认为不需要重开第一阶段或修改补丁 1–9。本版不改补丁，不改已有 golden 值，G.1 只更正文字。下表按严重程度列出处理结果；"来源"一栏写明提出该问题的评审方，"采用"一栏写明最终采用了谁的方案以及原因。标"自拟"的内容是本版为闭合问题新写的规则，列在 J.6。

### J.1 严重

无。

### J.2 重要

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| 参考侧按函数记录判歧义：同一 static inline 定义在各编译单元的副本被当成不同源函数，宏展开区域也被计入，FFmpeg 约一半的参考计数（含最热的 CABAC 函数）会移出 U | Claude Code I1 | 采纳 | 采用 Claude Code 的方案：按"规范化定义文件 + 去前缀和 `.__uniq.` 后缀的名字 + 起始行"合并副本；行范围只取主文件的代码区域，宏定义行不进入 U；只在已执行的源函数之间判歧义；sample 帧名去后缀后与参考侧对应。两侧口径一致（`DA` 对副本求和、sample 侧跨上下文求和）。另采纳"任一对象的 ③ 低于 50% 时不登记"：在登记前、只用参考数据就能发现 U 失真 | 5.8 第 5 条；G.3 第 4 条；J.5 |
| 映射范围没有闭合到工具实际合并的函数身份；名字规则不一致时，样本会被归为"范围外"而绕过未对齐检查 | Codex 重要 1；Claude Code I2（a 与同名合并两点） | 采纳，两家合并 | 函数名按工具实际写法（linkage name、不 demangle、不 canonical 化、保留后缀）、三分类（无法识别的名字、范围外、范围内未命中）：Claude Code。按工具函数身份取闭包、无法识别的身份不得当作正常范围外：Codex 与 Claude Code 一致。补丁树行号单独标明基线（Claude Code、Kimi Code 一般 2） | 5.8 第 5 条 |
| 未对齐比例的分子是聚合后的 body 计数，分母是 usable 原始计数，单位不同，`max`、`avg` 下比例被压低 | Codex 重要 2；Claude Code I2b | 采纳 Codex 的严格规则，比例采用两家共同的同单位口径 | 任一未对齐条目即使该 RUN、该配置的指标无定义：采用 Codex。登记前的核对要求映射范围内的键 100% 能找到，此后再出现未对齐只能是评估侧的实现错误，按比例容忍只会掩盖错误。不采用 Claude Code 的"同单位比例超过 1% 才无定义"，但它的同单位口径（同一份 profile 的 body 计数之和）保留为描述性比例。无定义的 RUN 按缺失处理（Claude Code 一般 2） | 5.8 第 5、6 条；第 11 节 |
| 边界无法证明的函数会使整个对象不可用；"已对齐但不在 U 内"的计数没有报告 | Claude Code I2c、I2d | 采纳 | 以 `boundary_unavailable` 排除该函数并单独报告，其参考计数超过 T 的 1% 时对象不可用；第 ④ 项增加"已对齐但不在 U 内"的比例 | 5.8 第 5 条 |
| 双区间规则缺少退化样本的处理；稀有事件反例（15 个差值全为 0 的概率 63%，真实差值却超出 ε）；I.5 的覆盖率验收没有定义 | Codex 重要 3；Claude Code 一般 5（第 9 项）；Kimi Code 一般 1 | 采纳，三家合并 | 95% 水平、方差为 0 标 `degenerate_sample` 判证据不足、NaN 不得通过、包络定义：Codex。模拟验收：覆盖率按两种区间的包络定义（Claude Code）；分别报告覆盖率与判定的工作特性（Kimi Code）；真实差值为 ±ε 时判等价的比例不超过 2.5%：采用 Claude Code 的 2.5%，不用 Kimi Code 的 5%，因为"95% 双侧区间落入 ±ε"对应每侧 2.5% 的检验；加 ±0.03 界外场景、预先固定分布参数、不得通过换种子规避（Codex）；重复 10,000 次（Claude Code：1,000 次时标准误约 0.8%，不足以判定 93%） | 5.8 第 6 条；J.5 |
| 采集阶段只分开报告，没有真正分层；旧阶段与加装散热后的新阶段不能仅凭同一二进制认定同分布 | Codex 重要 4 | 采纳 | 采用 Codex 的分层方案：按阶段登记计划数与固定权重，估计预定混合总体的差值，bootstrap 在阶段内重采样，t 区间用分层标准误与 Satterthwaite 自由度，结论只适用于该混合总体。自拟：某层第一轮少于 3 个 RUN 时不使用第一轮，只按个数决定，避免出现无法估计方差的阶段 | 5.8 第 6 条 |
| 登记的输入 SHA 与登记后的补采冲突：未来原件的 SHA 无法预先登记 | Codex 重要 5 | 采纳 | 采用 Codex 的划分：锁定协议与静态产物、已存在输入、RUN 槽位表三部分；补采原件写入只追加的数据收据。重采规则合并 Claude Code 一般 2（采集失败可以重采）与 Codex（失败槽位不得静默替换）：同一槽位按原顺序最多重采 3 次，每次写入收据，转换失败、遥测与指标都不是重采理由；3 次仍失败则保留为缺失。次数 3 为自拟 | 5.8 第 6 条；G.3 第 8、9 条 |
| "非正式校准 profile"没有定义：第一轮的 CALIBRATION 运行与正式 S 同一 ELF、同一负载与参数，开发脚本时会提前预览正式比较 | Claude Code I3 | 采纳 | 采用 Claude Code 的数据规则：合成 profile 可以算任意指标；同一 ELF 的真实 profile 登记前只用于键覆盖与流程冒烟，只转换基准配置，不对两个及以上配置计算指标；披露打开过的真实 profile | 5.8 第 6 条；G.3 第 1 条；J.5 |
| 性能侧保留了"视方差加轮"，与质量侧改为固定样本量的理由矛盾 | Claude Code I4 | 采纳 | 每组固定轮数 N 在修订 3 中按板子写定（不少于 10），只用 G0 单组预试或旧镜像基线确定；达到 N 仍未落入 ±1% 报告证据不足，不再加轮；取代原预注册的"RPi4 后续加轮数"。G0 预试与板上采样器试运行合并做（J.5） | 5.9 第 5 条；G.3 第 7 条 |
| 遥测状态机自相矛盾（允许的缺口与"有缺口即 unknown"）；校准"完整 1 秒区间"、批次传播、hwmon 失败的可观测性、dmesg 时间戳、policy 读取项、窗口完整性、读取第 2 项对第 1 项的影响、MAD 为 0 时的退化都没有闭合 | Codex 重要 6；Claude Code I5；Kimi Code 一般 4 | 采纳，三家合并 | 缺口按观测流与各自窗口分别计算、允许的缺口只记告警、无效读数不当作异常、校准原因逐 RUN 传播再合并：Codex。`/dev/kmsg` 序号界定日志窗口、`-EPIPE` 判 unknown（日志时间戳是 `local_clock`，不是 CLOCK_MONOTONIC）、开机以来出现过查询失败则欠压项 unknown、新增 policy 读取项、窗口完整性定义、读取第 2 项会改写内核记录、MAD 下限、可评价区间的数值定义（1.000 ± 0.010 秒，task-clock ≥ 99%）、内核行号：Claude Code。Kimi Code 的 hwmon 源码说明与 Claude Code 一致，以及 Codex 指出的 perf 区间实际约 1.005 秒，用于确认 ±0.010 秒的容差合适（v1.2 更正：板上记录中每次运行都有约 1.015 秒的区间，校准规则已改，见附录 K.4）。自拟：每个 CPU 至少 15 个可评价区间 | 5.9 第 5 条；J.5 |
| I.5 的两项断言超出冻结实现：报告写入失败时不可能在报告里看到本次参数；"全部派生负对照仍须失败"没有限定命令 | Codex 重要 7 | 采纳 | 采用 Codex 的写法：报告提交成功的用例才断言 `tool.arguments`，其余用测试执行器保存的 argv、stderr、退出码与文件状态核对；三项 Thumb 负对照按既有的 `avg` 命令重跑、仍须在 boundary 阶段失败，不扩展到普通 sum/max | G.1.7；G.1.8；J.5 |

### J.3 一般

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| n_eff < 3 的对象"只用 M2 判读"与"spike 只作描述"前后不一致；spike 的 K 约为 5，M2 步长约为 ε 的 10 倍 | Claude Code 一般 1 | 采纳 | 按对象登记 K；1/K > ε 的对象 M1、M2 都只作描述；聚合方式与 skid 的正式结论只取 n_eff ≥ 3 且 1/K ≤ ε 的对象 | 5.8 第 5、6、9 条；第 12 节第 1 条 |
| 没有入选函数时 n_eff 为 0/0；只用 M2 时不宜沿用"两个指标等价"的名称 | Codex 一般 1 | 采纳 | n_eff 记 null、不进入 < 3 分支、判读记证据不足；结果名称分为"M1、M2 联合等价"与"M2 等价，M1 未判读" | 5.8 第 5、6 条 |
| 统计规则缺四处定义：RUN 级无定义、有效 RUN 与重采、干净子集的地位、"排序"的含义与比较清单的组成 | Claude Code 一般 2 | 采纳 | 无定义 RUN 按缺失；有效 RUN 定义与重采规则（与 Codex 重要 5 合并）；干净子集只作描述；"排序改变"改为"点估计改变符号"；比较清单改为单因素对基准，权重比较只在频率模式的层上进行，最终组合只作描述 | 5.8 第 5、6 条 |
| G.3 的登记清单与正文对不上（负对照、散热前置条件、K、①–③、性能 N、打开过的真实 profile） | Claude Code 一般 3 | 采纳 | G.3 补全并重新编号 | G.3 |
| G.1.7 仍有不准：`invalid-image` 不带 "injected"；带该字样的消息全部由补丁 6 引入；响应文件与单横线写法可以绕过评估准入 | Claude Code 一般 4 | 采纳 | 列出带该字样的 6 个注入点；准入拒绝以 `@` 开头的参数与四种写法的注入选项。本轮在补丁文件中复核：5 处带 "injected" 的字符串都由补丁 6 新增，补丁 8 中出现的是上下文行；`invalid-image` 走 "not a valid ELF/COFF image" | G.1.7；I.2 第 7 行更正 |
| I.5 有几项不可判定，另有几项可以由源码直接回答 | Claude Code 一般 5；Kimi Code 一般 1、4 | 采纳 | 合并成 J.5：第 8 项写明期望值，第 9 项定义模拟验收，第 12 项删去已由源码回答的两项、加入试运行判定标准，另加 ③ 门槛、打开过的真实 profile、离线资格夹具、性能 N 四项 | J.5 |
| 引用：`CoverageExporterJson.cpp:257–262` 是文件 segments 的导出；`L/` 下的非叶子行号 0 规则是补丁树行号；`getBaseDiscriminator` 的定义位置 | Claude Code 一般 6；Kimi Code 一般 2 | 采纳 | 函数记录字段改引 `:327–338`；补丁树行号标明 `15a5ec3f`；偏移计算引基线 `:1087`；`getBaseDiscriminator` 定义引 `ProfileGenerator.h:59–62` | 5.8 第 5 条 |
| spike 的 n_eff 同时写了 1.3 与 1.34 | Kimi Code 一般 3 | 采纳 | 统一为"约 1.3"，确切值由脚本给出 | 5.8 第 5、9 条；I.2 第 4 行 |

### J.4 对前一版附录的更正

1. I.2 第 7 行"带 injected 的消息出现在补丁 6、补丁 8"应为"全部由补丁 6 引入"；`invalid-image` 不带该字样。
2. I.2 第 4 行的"n_eff 约 1.34"统一为"约 1.3"。
3. I.5 由 J.5 取代；I.6 的五条新写内容已经本轮评审，处理见 J.2（映射范围、固定 15 个 RUN 与阶段合并已修改，其余三条被确认）。

### J.5 执行前须核对的事项（取代 I.5）

v1.2 起本节由附录 K.5 取代，以下保留 v1.1 原文。

登记修订 3 之前由执行方完成。结果与本文不符时先修订本文，再登记。只有第 12 项需要板子；全部事项都不对正式 sample profile 计算 M1、M2、M2b。

| 编号 | 事项 | 状态 |
|---|---|---|
| 1 | G.1.1 的前驱条件与原因分类与补丁 5 一致 | 已核对（三家与本文复核） |
| 2 | G.1.7：报告提交成功的用例断言 `tool.arguments` 记录了注入选项；报告自身写入或提交失败的用例，用测试执行器保存的 argv、stderr、退出码与文件状态核对调用点与契约；未执行到注入点的用例单列，验证"不保证失败"；评估准入对 `@rsp`、单横线、双横线、`=值`、分离值写法都拒绝 | 部分核对；测试待补 |
| 3 | G.1.8 的映射状态查找与同节冲突粒度与补丁 8 一致；三项派生负对照（`$t` 改为 `$a`/`$d`、low_pc 落在 `add.w` 中间）按既有 `avg` 命令重跑，仍在 boundary 阶段失败，逐项保存命令与原因 | 查找方式已核对；负对照待重跑 |
| 4 | G.1.3 第 4 条的提交顺序例外、G.1.10 第 2 条的 `name_merged_functions`/`name_merged_top50`，与补丁 6 的实现与测试一致 | 源码已核对（Codex）；测试待重跑 |
| 5 | 映射表：在第一轮 CALIBRATION 运行的基准配置（`max`、skid=`none`、`period`）转换结果上，映射范围内工具写出的键 100% 能在映射表中找到；两个命中函数集合不同的 RUN、删除热点函数全部条目、加显式零条目、改变预算，映射表、排除清单、U 与权重的 SHA 都不变；夹具：原始 discriminator 不同而写出键相同、Thumb 别名、非叶子行号 0、偏移碰撞、不同构建路径、歧义键与正常键同时贡献同一行、两个编译单元中同名的局部函数只有一个在参考侧执行、名字闭包、评估侧错误地去掉 `.__uniq.` 后缀（期望无定义而不是归为范围外）、无法识别的函数名、一个未对齐键且计数占比很小（仍判无定义）、同一地址计数生成 sum 与 max 时描述性比例按各自的 body 总量计算、映射范围内一个函数缺映射符号（`boundary_unavailable`） | 待实现与核对 |
| 6 | 对象登记表：只用参考数据与 U 计算各构建、ISA、输入的 ①–③、n_eff、K；确认第 6 条的判读方式 | 待计算 |
| 7 | M1、M2 合成夹具：N=15、K=9、sample 全零时 M2 = 0；只有一个正计数热点；正计数并列；正计数行不足 K；T = 0；U 为空；M1 无入选函数时 n_eff 为 null（不是 NaN、不是 0）；n_eff 恰为 3；10 行敏感性下的空函数集合；累计恰好等于与刚好跨过 80% | 待实现 |
| 8 | 合并口径：互补上下文（d0/d1 = 100/0 与 0/100）期望 S = 100、S_alt = 200、S_sum = 200；同一内联函数在不同调用点走不同分支；同一行多个覆盖区域与不同 discriminator；同时保存覆盖区域边界，不以聚合结果相等作为语义证明 | 待实现 |
| 9 | 区间模拟：按登记的阶段结构，先固定各合成分布（正态、偏斜、离散步长 1/K、Bernoulli 稀有事件、全零差值）的参数、种子与预期结果；真实差值取 0、±0.02、±0.03，各重复 10,000 次；分别报告两种区间及其包络的覆盖率、判为等价的比例、退化与无定义的比例及 Monte Carlo 标准误。验收：包络覆盖率 ≥ 93%（只适用于列出的场景，不表述为一般保证）；真实差值为 ±0.02 时判为等价的比例 ≤ 2.5%；退化重复不得删去后再算通过率，退化结果不得判等价。不达标时先修订本文，不通过更换种子或分布规避 | 待执行 |
| 10 | 统计规则夹具：配对 RUN 顺序不同而 ID 相同；单边缺失与转换失败；RUN 级无定义按缺失；多个采集段只贡献一个 RUN；第 5 个 RUN 已显示等价时脚本不输出判读；5 + 10 的两阶段且均值明显不同、阶段顺序打乱、某阶段单边缺失、阶段差值方向相反；只有一个阶段时与普通配对实现一致；15 个全零差值、15 个相同的非零差值、独立比较一方恒定、NaN 传播；包络与"双通过"的逻辑等价；采集失败后重采仍计入同一槽位；第 16 个 RUN、重复槽位、替换旧原件、未推送的收据都被门禁拒绝；固定间隔的层不产生权重比较；修订 3 推送之前，对同一 ELF 的真实 profile 拒绝计算第二个配置的 M1/M2 | 待实现 |
| 11 | 性能矩阵：从登记矩阵自动校验每组的聚合方式、skid、head、补零、profi 参数；缺少补零对照时拒绝输出"补零默认值已验证"；同一数据分别走质量与性能判读，确认均值与中位数、绝对差与相对差、两个 ε、两套停止规则没有混用；超过登记的 N 之后脚本拒绝计入新轮次，达到 N 且区间未落入时输出"证据不足" | 待实现 |
| 12 | 板上（需要板子，加装散热后）：root 读取 `cpuinfo_cur_freq` 可用；`/dev/kmsg` 序号括号法可行且不写入；"解码满载 + 采样器"试运行，判定标准为负载期间 ≥ 99% 的读数间隔不超过 1.5 秒、没有超过 3 秒的间隔、采样器使解码耗时中位数的变化小于 0.5%；同一次试运行的 G0 耗时用于确定性能轮数 N | 待板上执行 |
| 13 | 覆盖参考：spike 上 lcov 的 `DA` 与 JSON 推得的行计数一致；按主文件代码区域推导的函数行范围与 lcov/JSON summary 交叉一致；副本合并规则在合成覆盖 JSON 上的夹具（3 个编译单元的同一 static inline 函数只执行 1 个、宏展开区域、同一模板文件被不同名字包含两次、两个不同的已执行函数在同一物理行）；`HasMultipleRegions` 从 segments 提取的结果与 Coverage API 一致（wrapped region 加本行入口、两个本行入口、只有 gap、skipped region）；FFmpeg 的 lcov 导出在覆盖导出级别限额内完成 | 待核对 |
| 14 | 离线资格分类：执行 5.9 第 5 条列出的全部判定脚本夹具，并用第一轮与四核诊断的原件重放，重放标签不覆盖历史资格 | 待实现 |
| 15 | ③ 门槛：按新的源函数合并规则，在 FFmpeg（Thumb、A32）与 spike 的参考上计算合并前后的 ③，任一对象低于 50% 时不登记 | 待计算 |
| 16 | 登记前打开过的真实 profile 清单与在其上计算过的量，写入修订 3 的披露 | 登记时执行 |
| 17 | 性能轮数 N：按第 12 项的 G0 试运行或 03 报告第 4 节的旧镜像基线确定每块板的 N（不少于 10），写明来源 | 待确定 |
| 18 | 登记：①（协议、脚本、依赖、配置、对象登记表、映射表、排除清单、U、权重）与 ②（已存在输入清单）的 SHA-256、③ RUN 槽位表写入修订 3；修订 3 提交与推送成功的记录在正式指标计算之前保存 | 登记时执行 |

### J.6 本版新写、尚未经评审的内容

以下四条已经 v1.1 评审，处理见附录 K.4 第 2 条。

1. 某层第一轮的有效 RUN 少于 3 个时，该层不使用第一轮，15 个全部补采（5.8 第 6 条）。
2. 采集失败的槽位最多重采 3 次（5.8 第 6 条）。
3. 校准每个 CPU 至少 15 个可评价区间（5.9 第 5 条）。
4. 最终推荐组合与基准的比较只作描述（5.8 第 6 条；Claude Code 提议加入这一比较，本版把它限定为描述，因为组合是用同一批数据选出的）。

## 附录 K：v1.1 评审意见处理（Claude Code、Codex、Kimi Code）

三家的结论：Codex "修改后可以进入登记准备"（严重 1、重要 6、一般 2）；Claude Code "修改后可以进入登记准备"（严重 0、重要 5、一般 5）；Kimi Code "可以进入登记准备"（严重 0、重要 0、一般 2）。三家都认为不需要重开第一阶段或修改补丁 1–9。本版不改补丁，不改已有 golden 值。下表按严重程度列出处理结果；"来源"一栏写明提出该问题的评审方，"采用"一栏写明最终采用了谁的方案以及原因。标"自拟"的内容列在 K.6。

### K.1 严重

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| 只有"所有阶段方差都为 0"才判退化：一个阶段全为 0、另一阶段有微小扰动时仍可通过。反例：旧阶段 3 个 RUN、权重 0.2、差值以 15% 的概率为 1，全为 0 的概率 61%；新阶段 12 个 ±0.001 的扰动，两种区间都落在 ±0.001 内，真实差值却是 0.03 | Codex 严重 1 | 采纳 | 任一具有正权重的阶段方差为 0 即判 `degenerate_sample`、证据不足；s_h² 明确为分母 n_h − 1 的样本方差；任一非空阶段 n_h < 2 时登记准备失败；模拟验收按"决策置信集合"计算（没有区间时取整个参数空间），全零场景须 100% 退化、0% 判等价，±0.03 场景同样验收。Codex 给出的独立比较自由度公式不再需要：采用 Claude Code 一般 3，比较清单全部是配对比较，出现独立比较属于协议变更 | 5.8 第 6 条；K.5 |

### K.2 重要

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| 跨侧的源函数对应依赖"起始行"，两侧的起始行不是同一个量：DWARF 的 decl_line 是声明行，覆盖侧是函数体第一个代码区域；正式 S 的调试信息上 4 个热点函数中 3 个不相等。对不上的函数会静默归为"范围外"，它的行也从 U 中消失 | Codex 重要 1；Claude Code 重要 1 | 采纳，两家合并 | 覆盖侧起始行与行范围的定义、跨侧按"文件 + 去后缀的名字"对应、同名多候选时按"decl_line ≤ 起始行且差值最小"消歧、对应完整性检查（`unmatched_in_elf` 超过 1% 时对象不可用）、同名但不在范围内的 ELF 函数逐个裁决、S(line) 只汇总所属源函数的键：Claude Code，它给出了确定的消歧规则与实测。对应表单独登记、原始名字与匹配用名字分开保存、对应失败归为 `reference_unresolved` 而不是范围外、主文件按 `findMainViewFileID` 的规则确定：Codex | 5.8 第 5 条 |
| ③ 的分母没有定义，50% 门槛无法判定；不同读法的结果分别约为 62% 与 97% | Claude Code 重要 2；Codex 重要 2 | 采纳，以 Claude Code 为主 | 分母取已执行源函数行范围内的可执行行，不含宏定义行：采用 Claude Code，宏定义行的执行已体现在调用处的行上，计入分母会重复。Codex 建议在宏行排除之前建立分母，不采用这一点；采用它的"按文件与行去重、R 取 DA、在歧义与对齐排除之前固定、分母为 0 不可评价、50% 不证明代表性"。另加描述性的 ③′（分母为全部 DA）与 50%–80% 之间须分解损失（Claude Code） | 5.8 第 5 条；G.3 |
| `boundary_unavailable` 与"任一未对齐即无定义"冲突；"这类函数的参考计数"没有定义 | Codex 重要 2；Claude Code 重要 3 | 采纳，两家合并 | 条目分类单列 `boundary_unavailable`、不算未对齐：Claude Code 与 Codex 一致。按工具顶层身份的完整合并组处理、静态确定受影响的参考行并整行排除、比例按逐行 DA 计算而不是 FNDA、无法确定时对象不可用：Codex | 5.8 第 5 条 |
| "未对齐只可能是实现错误"的前提只在一份真实 profile 的已采样地址上核对过，没有覆盖 `prev-inst` | Claude Code 重要 3；Codex 重要 1（措辞） | 采纳 | 采用 Claude Code 的合成全地址核对：为映射范围内每个已证明的指令起点构造一条合成样本，用正式工具分别以 skid=`none` 与 `prev-inst` 转换，写出的键必须全部在映射表中或属于 `boundary_unavailable`；真实 profile 的键覆盖保留为流程冒烟。正文措辞改为"表明输入与映射契约不一致，须调查原因"：Codex | 5.8 第 5 条；K.5 |
| 既有 RUN 没有纳入槽位与收据；槽位表本身没有 SHA 门禁；同一槽位成功后可以再采，结果可以人工改判，槽位未齐就可以判读 | Codex 重要 3；Claude Code 一般 2 | 采纳，两家合并 | 槽位表覆盖全部 15 个 RUN、既有 RUN 的凭据作为初始化收据导入、③ 也核对 SHA：Codex。每个槽位至多一次成功、结果由脚本自动判定、判读前全部槽位须有终态、只追加并带 SHA 链的计算日志、"按原顺序重采"的定义：Claude Code | 5.8 第 6 条；G.3 |
| 重采规则与原预注册的任务停止条件冲突：身份、build-id、SHA 不一致、硬件事件错误、过热停止都可能表现为 perf 非零退出 | Codex 重要 4；Claude Code 一般 4（原预注册第 41 行） | 采纳 | 先按原停止条件分类再决定是否重采、原因不明时停止、拉回中断时优先重传同一原件、"最多 3 次"明确为首次之外最多 3 次：Codex。原预注册的"干净重复不足……需要补采"对质量由固定槽位取代、对性能由固定 N 取代，G.3 写明"停止条件不变"指的是任务停止条件：Claude Code | 5.8 第 6 条；G.3 |
| 校准按时长筛区间，可能把已观察到的低频区间筛掉后判合格；按板上已有记录，20 秒、±0.010 秒、至少 15 个区间只有 1–2 个余量 | Codex 重要 5；Claude Code 一般 1 | 采纳，两家合并，时序处理为自拟 | 计数有效的中间区间全部检查频率下限、观察到低频即异常、无效区间的 unknown 不能被其余区间抵消、板上实际跑完整校准流程：Codex。改为 30 秒、至少 25 个区间、采样器绑到未被校准的 CPU：Claude Code。自拟：区间时长超出 1.000 ± 0.020 秒或忙碌率低于 99% 只记告警，不判 unknown，理由是 cycles/task-clock 的比值不依赖区间长短（Claude Code 的论证），而 Codex 担心的"删去不利证据"已由"所有有效区间都检查"解决 | 5.9 第 5 条；K.5 |
| `/dev/kmsg` 没有"读取当前最后一条序号"的接口（`SEEK_END` 指向下一条待写记录）；两次分别打开时 `-EPIPE` 判据失效；"开机以来"需要从序号 0 起的完整日志；policy 的读取窗口与缺口窗口不一致 | Codex 重要 6；Claude Code 重要 5、一般 5 | 采纳，两家合并 | 同一描述符读到 EAGAIN、记最后序号、窗口为两次序号之间：两家一致。两次读取须在时间上保守包围监测窗口：Codex。每次开机由常驻记录器从序号 0 起连续保存，不从 0 开始或断号时欠压项 unknown，记录板上 `CONFIG_LOG_BUF_SHIFT`：Claude Code。按 boot_id 维护失败标记、在日志截止点统一传播并保存截止点：Codex。policy 改按监测窗口计算缺口：两家一致 | 5.9 第 5 条；K.5 |
| J.5 第 9 项"±ε 处判等价 ≤ 2.5%"会随种子翻转：正态且标准误远小于 ε 时，真实比例正好约 2.5%，三个种子得到 2.39%–2.89% | Claude Code 重要 4 | 采纳 | 预先固定标准误与 ε 之比、阶段结构与方差比的场景网格；验收线改为估计值 ≤ 3.0%（名义 2.5% 加约 3 倍 Monte Carlo 标准误），同时报告单侧 99% Clopper–Pearson 上界；不达标时先修订本文（例如把自由度改为 min_h(n_h) − 1），不换种子、不删场景。2.5% 作为名义水平三家都同意 | K.5 |

### K.3 一般

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| "1/K > ε 时等价等于要求全部 RUN 的热点集合相同"的推论不对：并列份额与跨 RUN 均值会产生更细的变化，K=20 时可以判等价 | Codex 一般 1 | 采纳 | K ≥ 50 保留为预先选定的对象准入条件，删去错误的推论；先处理 U 为空、T = 0、K 无定义，再进入分支 | 5.8 第 5、6 条；第 11 节 |
| n_eff 为 null 时判"证据不足"，与 n_eff = 1.3 时可以判读 M2 不一致 | Claude Code 一般 3 | 采纳，与上一轮 Codex 的规则调和 | n_eff 为 null 只表示 M1 没有入选函数，M2 仍有定义，所以与 n_eff < 3 同样处理：采用 Claude Code。上一轮 Codex 要求 null 不得当作 0 进入数值比较，这一要求保留：按显式分支处理，不做数值比较 | 5.8 第 5、6 条 |
| 写明 λ_h = n_h/15 时分层点估计等于普通均值；独立比较用不到 | Claude Code 一般 3 | 采纳 | 写明；比较清单全部为配对比较，出现独立比较属于协议变更 | 5.8 第 6 条 |
| 性能轮数 N 没有确定公式 | Claude Code 一般 4 | 采纳 | N = max(10, ⌈2 ×（1.96 × 1.2533 × CV ÷ 0.005）²⌉)，上限 40，CV 取自加装散热后带采样器的 G0 预试；旧镜像基线只在无法预试时使用。CV 为 0.5% 时 N = 13，为 1% 时到上限 40 | 5.9 第 5 条；G.3 |
| 登记声明"未做任何性能比较"与 G0 采样器开关预试冲突；开发门禁只拒绝"第二个配置"，没拦住第一个真实配置 | Codex 一般 2 | 采纳 | 声明改为"未做待评配置之间的性能比较"并披露预试；登记前对同一 ELF 的任何真实 profile，包括基准配置，都不计算 M1、M2、M2b | 5.8 第 6 条；G.3；K.5 |
| `UseCanonicalFnName` 的引用位置 | Kimi Code 一般 2 | 采纳 | 理由改为"canonical 化只由 `--show-canonical-fname` 打开，该选项在 IP 模式下报错（5.1.3）"，调用点并列 `L/ProfiledBinary.cpp:670` 与 `.h:620`，在 K.5 核对 | 5.8 第 5 条 |
| 判据 2 写"把内核记录改为该读数"不准确，应为只调度一次纠正性的重发 | Kimi Code 一般 1 | 不采纳 | `cpufreq_out_of_sync` 发出一次频率转换通知，转换结束（POSTCHANGE）时内核记录被改为该读数，随后才是 `handle_update` 与 governor 的重发；Codex 与 Claude Code 在板上内核源码中的核对结论与此一致。正文补上这一机制，具体行号在 K.5 第 12 项按板上源码核对 | 5.9 第 5 条 |

### K.4 对前一版附录的更正

1. J.2 遥测一行"perf 区间实际约 1.005 秒，用于确认 ±0.010 秒的容差合适"不准：板上记录中每个 CPU 每次运行都有一个约 1.015 秒的区间。校准规则已改（K.2）。
2. J.6 四条：第 1 条（第一轮少于 3 个 RUN 时不用）经两家确认，另受 K.1 的阶段退化规则约束；第 2 条（重采次数）改写为"首次之外最多 3 次"，并受停止条件分类约束；第 3 条（每 CPU 至少 15 个可评价区间）改为 30 秒、至少 25 个计数有效的区间；第 4 条（最终组合只作描述）经三家确认。
3. J.5 由 K.5 取代。

### K.5 执行前须核对的事项（取代 J.5）

v1.3 起本节由附录 L.5 取代，以下保留 v1.2 原文。

登记修订 3 之前由执行方完成。结果与本文不符时先修订本文，再登记。只有第 12 项需要板子；全部事项都不对正式 sample profile 计算 M1、M2、M2b。

| 编号 | 事项 | 状态 |
|---|---|---|
| 1 | G.1.1 的前驱条件与原因分类与补丁 5 一致 | 已核对 |
| 2 | G.1.7：报告提交成功的用例断言 `tool.arguments` 记录了注入选项；报告自身写入或提交失败的用例，用测试执行器保存的 argv、stderr、退出码与文件状态核对；未执行到注入点的用例单列；评估准入对 `@rsp`、单横线、双横线、`=值`、分离值写法都拒绝 | 部分核对；测试待补 |
| 3 | G.1.8：三项派生负对照按既有 `avg` 命令重跑，仍在 boundary 阶段失败，逐项保存命令与原因 | 查找方式已核对；负对照待重跑 |
| 4 | G.1.3 第 4 条与 G.1.10 第 2 条与补丁 6 的实现与测试一致；`UseCanonicalFnName` 的调用点（`L/ProfiledBinary.cpp:670`、`.h:620`）与 `--show-canonical-fname` 在 IP 模式下报错 | 源码已核对；测试待重跑 |
| 5 | 映射表与条目分类：合成全地址核对——为映射范围内每个已证明的指令起点构造一条合成样本，按工具的 perf 输入格式写入，用正式工具以 skid=`none` 与 `prev-inst`、聚合方式 `max` 分别转换，写出的键必须全部在映射表中或属于 `boundary_unavailable`。另在第一轮 CALIBRATION 运行的基准配置上做流程冒烟。夹具：映射表故意漏一个冷地址、`prev-inst` 键算法错一位（核对失败）；两个命中函数集合不同的 RUN、删除热点函数全部条目、加显式零条目、改变预算（映射表、对应表、排除清单、U、权重的 SHA 都不变）；原始 discriminator 不同而写出键相同、Thumb 别名、非叶子行号 0、偏移碰撞、不同构建路径、歧义键与正常键同时贡献同一行、两个编译单元中同名的局部函数只有一个执行、名字闭包、评估侧错误地去掉 `.__uniq.` 后缀且 ELF 恰好有同名的范围外函数（期望无定义而不是范围外）、无法识别的函数名、一个计数很小的未对齐键（仍判无定义）、一个 `boundary_unavailable` 函数有样本（单列，RUN 仍有定义）、同名组同时含可证明与不可证明的范围、被排除函数含热点内联体、FNDA 很小而循环行计数很大 | 待实现与核对 |
| 6 | 对象登记表：只用参考数据与 U 计算各构建、ISA、输入的 ①–③′、n_eff、K | 待计算 |
| 7 | M1、M2 合成夹具：N=15、K=9、sample 全零时 M2 = 0；只有一个正计数热点；正计数并列；正计数行不足 K；T = 0；U 为空；K 无定义；n_eff 为 null 且 K = 80（期望"M2 等价，M1 未判读"）；n_eff 恰为 3；K = 49 与 50；10 行敏感性下的空函数集合；累计恰好等于与刚好跨过 80% | 待实现 |
| 8 | 合并口径：互补上下文（d0/d1 = 100/0 与 0/100）期望 S = 100、S_alt = 200、S_sum = 200；同一内联函数在不同调用点走不同分支；同一行多个覆盖区域与不同 discriminator；未执行模板实例的键落在已执行实例的行上（计入"已对齐但不在 U 内"）；同时保存覆盖区域边界 | 待实现 |
| 9 | 区间模拟：场景网格预先固定——标准误与 ε 之比 ∈ {0.05, 0.1, 0.25, 0.5}；登记的阶段结构；阶段方差比 ∈ {1, 16}；分布为正态、偏斜、离散步长 1/K、Bernoulli 稀有事件、全零差值，以及"一个阶段为稀有事件、另一阶段为非退化小扰动"；真实差值取 0、±0.02、±0.03；每个场景 10,000 次，参数、种子与预期结果先固定。报告两种区间及其包络的覆盖率、判为等价的比例、退化与无区间的比例、有效区间率及 Monte Carlo 标准误。验收：按决策置信集合（有区间时取包络，没有区间时取整个参数空间）计算的覆盖率 ≥ 93%；真实差值为 ±0.02 时判等价比例的估计值 ≤ 3.0%，并报告单侧 99% Clopper–Pearson 上界；±0.03 时判等价比例同样 ≤ 3.0%；全零场景 100% 退化、0% 判等价；退化或无区间的重复判等价必须为否，不得删去后再计算。任一场景不达标时先修订本文（例如自由度改为 min_h(n_h) − 1），不换种子、不删场景。上一轮评审的三个场景各固定一个种子作为回归用例 | 待执行 |
| 10 | 统计与登记门禁夹具：配对 RUN 顺序不同而 ID 相同；单边缺失与转换失败；RUN 级无定义按缺失；多个采集段只贡献一个 RUN；第 5 个 RUN 已显示等价时脚本不输出判读；3 + 12 的阶段退化反例、某阶段全零而另一阶段非零、某阶段恒定非零、单阶段退化（都判证据不足）；两阶段时分层点估计等于普通均值；只有一个阶段时与普通配对实现一致；NaN 传播；包络与"双通过"的逻辑等价；旧 5 + 新 10 全部合法通过、旧 RUN 没有初始化收据、篡改槽位表、旧 RUN 冒充新 RUN、同一原件占两个槽位、第 16 个 RUN、槽位成功后再追加成功、人工改判、第 14 个槽位还没有终态时请求判读、计算日志 SHA 链断开、未推送的收据（都被门禁拒绝）；普通采集故障后成功、第四次重采仍失败、完整原件 SHA 不一致、只有传输中断、过热引起 perf 非零退出、首次成功但遥测异常、成功后转换失败（按停止条件与重采规则分别处理）；固定间隔的层不产生权重比较；登记前对同一 ELF 的真实 profile（含基准配置）请求 M1/M2 即拒绝，合成 profile 允许 | 待实现 |
| 11 | 性能矩阵：从登记矩阵自动校验每组参数；缺少补零对照时拒绝输出"补零默认值已验证"；质量与性能的统计量、ε、停止规则没有混用；超过登记的 N 后拒绝计入新轮次；N 的公式夹具（CV 0.5% 得 13，1% 得 40）；G0 预试数据不进入正式轮次 | 待实现 |
| 12 | 板上（需要板子，加装散热后）：root 读取 `cpuinfo_cur_freq` 可用；常驻记录器在开机后取得序号 0、批次结束时序号连续，记录板上 `CONFIG_LOG_BUF_SHIFT`；同一描述符的序号括号法可行且不写入；完整执行一次前后校准流程（30 秒、每个 CPU 计数有效的中间区间 ≥ 25、采样器并行时的行为）；"解码满载 + 采样器"试运行，负载期间 ≥ 99% 的读数间隔不超过 1.5 秒、没有超过 3 秒的间隔、采样器使解码耗时中位数的变化小于 0.5%；同一次试运行带采样器的 G0 耗时（至少 10 轮）用于计算 N；核对 5.9 第 5 条引用的内核函数与行号，包括 `cpufreq_out_of_sync` 的频率转换通知在 POSTCHANGE 时改写内核记录 | 待板上执行 |
| 13 | 覆盖参考：spike 上 lcov 的 `DA` 与 JSON 推得的行计数一致；按主文件代码区域推导的函数行范围与 lcov/JSON summary 交叉一致；主文件按 `findMainViewFileID` 的规则核对；副本合并夹具（3 个编译单元的同一 static inline 函数只执行 1 个、宏展开区域、同一模板文件被不同名字包含两次、两个不同的已执行函数在同一物理行）；`HasMultipleRegions` 从 segments 提取的结果与 Coverage API 一致 | 待核对 |
| 14 | 离线资格分类：执行 5.9 第 5 条列出的全部判定脚本夹具，并用第一轮与四核诊断的原件重放，重放标签不覆盖历史资格 | 待实现 |
| 15 | ③ 门槛：按新的源函数合并规则与 ③ 的分母，在 FFmpeg（Thumb、A32）与 spike 的参考上计算 ③、③′ 与按原因的损失分解；任一对象 ③ 低于 50% 时不登记，50%–80% 时登记文本须含损失分解 | 待计算 |
| 16 | 跨侧对应表：只用 ELF、调试文件与参考数据生成；夹具为左花括号另起一行（decl_line = 起始行 − 1）、签名跨 3 行、同一文件中两个同名 static 函数（按最近 decl_line 对应）、评估侧错误地用 decl_line 精确匹配（期望 `unmatched_in_elf` 超过 1%，而不是静默归为范围外）、对应失败不得落入 `known_out_of_scope`；列出名字去后缀后与已执行参考源函数相同、却不在映射范围内的全部 ELF 顶层函数并逐个裁决 | 待生成 |
| 17 | 登记前打开过的真实 profile 清单与在其上计算过的量；G0 预试的条件、轮数、原始耗时与开销，写入修订 3 的披露 | 登记时执行 |
| 18 | 性能轮数 N：按第 12 项的 G0 预试与 5.9 第 5 条的公式确定每块板的 N，写明来源 | 待确定 |
| 19 | 登记：①（协议、脚本、依赖、配置、对象登记表、对应表与裁决表、映射表、排除清单、边界排除组、U、权重）、②（已存在输入清单）、③（完整 RUN 槽位表与既有 RUN 的初始化收据）的 SHA-256 写入修订 3；修订 3 提交与推送成功的记录在正式指标计算之前保存 | 登记时执行 |

### K.6 本版新写、尚未经评审的内容

以下三条已经 v1.2 评审，处理见附录 L.4 第 3 条。

1. 校准区间时长超出 1.000 ± 0.020 秒或忙碌率低于 99% 只记告警，不判 unknown（5.9 第 5 条）。
2. 常驻日志记录器的输出写入 `/opt/afdo_agent/`（5.9 第 5 条；遵守附录 G.2.3 的写入范围）。
3. 条目分类中，名字属于 ELF 但对应未决的条目（`reference_unresolved`）与未对齐同样处理（5.8 第 5 条；合并 Codex 的 `reference_unresolved` 与 Claude Code 的 `unmatched_in_elf` 时的分工：前者用于 RUN 级条目，后者用于登记前的对象级检查）。

## 附录 L：v1.2 评审意见处理（Claude Code、Codex、Kimi Code）

三家的结论：Codex "修改后可以进入登记准备"（严重 1、重要 5、一般 3）；Claude Code "修改后可以进入登记准备"（严重 1、重要 4、一般 2）；Kimi Code "可以进入登记准备"（严重 0、重要 0、一般 1）。三家都认为不需要重开第一阶段或修改补丁 1–9。本版不改补丁，不改已有 golden 值。下表按严重程度列出处理结果；"来源"一栏写明提出该问题的评审方，"采用"一栏写明最终采用了谁的方案以及原因。标"自拟"的内容列在 L.6。

### L.1 严重

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| 稀有事件叠加微小扰动时，两个阶段方差都不为 0，退化规则不触发，两种区间都判等价：例如差值 = 0.99 × Bernoulli(1/33) + 0.001 × (±1)，真实差值 0.03，3 + 12 结构下判等价的概率至少约 47%，单阶段 15 个至少约 63%。现有模拟网格不覆盖这类场景 | Codex 严重 1；Claude Code 重要 1（同一现象，认为是 15 个样本的固有盲区） | 采纳，按两家的共同结论处理为"已登记的方法局限 + 预先登记的回退" | 两家都确认任何区间方法都消除不了这一盲区（每个 RUN 发生概率低于约 21% 的偏离，有超过 3% 的概率一次也观测不到）。处理：① 模拟分为验收场景与报告场景，稀有事件叠加扰动、偏斜分布列为报告场景，完整参数预先固定，只报告不验收（Claude Code）；② 每个等价结论都附带这一限定，并报告每个 RUN 的差值与最大绝对差值（Claude Code 的披露要求，具体输出为自拟）；③ 验收场景有任一不达标时，按预先登记的规则关闭质量等价判读（`quality_equivalence_enabled=false`），只报告差值与区间，默认值按保守规则与性能结果决定，不再修订本文（Codex 的方案，作为预先登记的回退采用）。（v1.4 更正：此行对两家意见的归纳不准确，见附录 M.4 第 1 条。）不直接关闭等价判读：在登记的分布假设下，配对等价区间是常规方法，关闭会丢掉可用的证据；但它不再依赖"模拟一定通过"，所以不会再引出新一轮修订 | 5.8 第 6 条；L.5 第 9 项 |
| 退化规则按字面"方差为 0"实现，会被浮点误差绕过：数学上相等的两个 M2 因求和顺序不同相差 ±5.6×10⁻¹⁷，上一轮反例的判等价率从 0% 升到 46% | Claude Code 严重 1 | 采纳 | 采用 Claude Code 的方案：退化判定前把每个差值按 10⁻⁹ 的固定网格舍入，再用精确有理数运算计算阶段方差；舍入只用于退化判定，区间用未舍入的值。某阶段全部差值相同时写明"该阶段所有 RUN 的差值相同"，不称为等价 | 5.8 第 6 条；L.5 第 10 项 |

### L.2 重要

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| 3 + 12 结构在方差比 16、小阶段噪声大时判等价率约 3.4%，超过验收线；偏斜场景的超线不能靠改自由度修正 | Claude Code 重要 1 | 采纳 | 第一轮少于 5 个有效 RUN 时该层不用第一轮（原为 3 个）；偏斜场景改为报告场景。采集面上的影响：第一轮每个采集制度有 5 个 RUN，只有出现无效 RUN 的层要全部补采 | 5.8 第 6 条；L.5 第 9 项 |
| "最近声明行"不是可靠的身份证据：条件编译下同一头文件的两个同名 static 函数可以声明行相同、函数体起点不同，两个 DWARF 实例都会选到同一个候选 | Codex 重要 1 | 采纳 | 采用 Codex 的方案：同一（文件、名字）只有一个候选时直接对应；有多个候选时默认 `identity_ambiguous`，只有登记前的静态裁决能以源码、编译变体、DWARF 位置与覆盖区域证据唯一证明时才建立对应，不凭行号距离裁决。Claude Code 认为原规则不会错配，这一点被 Codex 的条件编译反例推翻 | 5.8 第 5 条；L.5 第 16 项 |
| `identity_ambiguous` 被算作未对齐，一个样本就使全部 RUN 无定义；汇编实现、未插桩的 libgcc 函数（`__divsi3`、`__aeabi_*`）没有确定归属；外部 C 函数没有 linkage name；`findMainViewFileID` 可能返回空；全地址核对的通过条件没有包含 `prev-inst` 前驱落在范围外的正常情形 | Claude Code 重要 2 | 采纳 | 全部采用 Claude Code 的方案：`identity_ambiguous` 是已登记的结论，条目计入"已对齐但不在 U 内"，其参考计数超过 ③ 分母的 1% 时对象不可用；`not_instrumented` 组属于范围外；名字缺 linkage name 时取 `DW_AT_name`；没有主文件的覆盖记录单独报告；全地址核对允许 `known_out_of_scope` | 5.8 第 5 条；L.5 第 5、16 项 |
| 全地址核对只证明"键都存在"：`max` 会合并同键的多个地址，删去一个碰撞地址后键集合可以不变；`prev-inst` 遇到边界不可证明的组会整次转换失败，不能统一预期"RUN 仍有定义" | Codex 重要 2 | 采纳 | 另外保存并核对"地址 → 键 → 源位置"的完整关系与排除结果，碰撞夹具包含"删去一个地址后键集合不变"；`prev-inst`、`avg` 等需要边界的配置在边界排除组有样本时按冻结契约整次失败、记为转换失败的缺失，全地址成功核对只包含边界可证明的组 | 5.8 第 5 条；L.5 第 5 项 |
| "1/K ≤ ε 且 n_eff < 3，或 n_eff 为 null"的优先级不明确，K = 5、n_eff = null 时会绕过 K ≥ 50 | Codex 重要 3 | 采纳 | 先判断 K < 50（只作描述），再按 n_eff 分支；"M2-only 判读模式"与"M2 等价"的结果分开 | 5.8 第 6 条 |
| 记录器读到 EAGAIN 时把末序号记为 −1，会得到错误的窗口；开机启动的常驻记录器需要安装开机服务，与 G.2.3 只写 `/opt/afdo_agent/`、不安装软件的规定冲突 | Codex 重要 4；Claude Code 重要 3 | 采纳，两家合并 | 记录器按 boot_id 持有"最后已保存序号"，EAGAIN 不重置，只有本次开机从未读到记录时才为 −1，窗口端点由唯一读取者排空后返回（Codex）。记录器在每个板上会话开始时启动、以 `SEEK_SET` 从缓冲起点读、首条序号须为 0，不装开机服务；每个 RUN 前核对 boot_id，改变时重启记录器并重新核对（Claude Code） | 5.9 第 5 条；L.5 第 12、14 项 |
| 重采示例"没有停止类证据的 perf 非零退出"与"原因不明即停止"冲突；夹具"第四次重采"与总次数矛盾；停止类失败之后没有终态，判读永远无法执行；门禁只管 M1、M2、M2b，M3、分支误差、各类敏感性同样会提前透露比较结果 | Codex 重要 5；Claude Code 重要 4 | 采纳，两家合并 | 非停止类故障必须命中登记的原因码白名单并有正面证据，否则按原因不明停止；夹具改为"第四次尝试（第三次重采）仍失败，第五次被拒绝"（Codex）。空间不足、过热、人工停止在消除措施以事件记录推送后可在同一槽位继续；身份、build-id、原件 SHA、硬件事件错误使未完成槽位写入终态"停止缺失"；门禁、计算日志与开发数据规则改为管全部"受控量"（Claude Code）。自拟：原因不明的停止在事件记录给出可消除的原因后才能继续，否则同样写入"停止缺失" | 5.8 第 6 条；G.3；L.5 第 10 项 |

### L.3 一般

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| ③ 不含宏定义行的理由"计入会重复"过强：区域行计数不是守恒的量，宏内部循环的计数不必等于调用行；损失分解没有处理一行多个原因 | Codex 一般 1 | 采纳 | 理由改为"评价域的限定"，不宣称可以由调用行代替；宏区域按区域类型与 FileID 识别，不按文件名整体排除；损失按互斥的原因集合分桶，各桶之和等于 ΣR(C) − ΣR(U)。Claude Code 认为原理由成立，但评价域的写法不改变分母，又避免了一个无法证明的断言，所以采用 Codex 的写法 | 5.8 第 5 条；L.5 第 15 项 |
| N 的 CV 怎么算没有写死；无法预试时用旧基线反推 CV 没有依据 | Codex 一般 2；Claude Code 一般 2 | 采纳，两家合并 | CV = 去掉预热轮后耗时的样本标准差（分母 n − 1）÷ 均值，保留 4 位有效数字，离群轮次不剔除（Claude Code）；写明公式是近似正态、两组波动相近条件下的预算近似；无法完成预试时直接取 N = 40，旧基线只作背景（Codex） | 5.9 第 5 条 |
| 校准时序夹具与正文不一致：1.015 秒在 ±0.020 秒之内，不应告警；忙碌率没有给出 | Codex 一般 3 | 采纳 | 夹具改为：1.015 秒不告警、1.025 秒告警、忙碌率 98% 的区间告警，频率低于 97% 仍判异常 | 5.9 第 5 条 |
| canonical 化的理由与引用不准：写 profile 的路径是 `L/ProfiledBinary.h:620`，传入的 `UseSymbolTable` 在 `getSymbolizerOpts` 中固定为 false；`--show-canonical-fname` 只影响反汇编显示 | Claude Code 一般 1 | 采纳 | 按 Claude Code 的核对改写；上一轮按 Kimi Code 改的理由作废 | 5.8 第 5 条；L.5 第 4 项 |
| 补零配置写出的显式 0 键不在全地址核对的覆盖范围内 | Kimi Code 一般 1 | 采纳 | 正文写明：补零配置不进入质量指标；将来如要计算，须先扩展核对并作为协议变更登记 | 5.8 第 5 条 |

### L.4 对前一版附录的更正

1. K.3 中"canonical 化只由 `--show-canonical-fname` 打开"的理由不准，见 L.3。
2. K.2 第 1 行"同名多候选时按 decl_line 最近者消歧"已撤销，见 L.2。
3. K.6 第 3 条（`reference_unresolved` 与 `unmatched_in_elf` 的分工）保留，但 `identity_ambiguous` 不再归入 `reference_unresolved`。K.6 第 2 条（记录器写入 `/opt/afdo_agent/`）保留，"开机启动"改为"会话开始时启动"。K.6 第 1 条（时序偏差只告警）经三家确认。
4. K.5 由 L.5 取代。K.5 第 9 项"不达标时先修订本文"改为按预先登记的规则回退，不修订本文。

### L.5 执行前须核对的事项（取代 K.5）

v1.4 起本节由附录 M.5 取代，以下保留 v1.3 原文。

登记修订 3 之前由执行方完成。除第 9 项按预先登记的规则回退外，结果与本文不符时先修订本文，再登记。只有第 12 项需要板子；全部事项都不对正式 sample profile 计算任何受控量。

| 编号 | 事项 | 状态 |
|---|---|---|
| 1 | G.1.1 的前驱条件与原因分类与补丁 5 一致 | 已核对 |
| 2 | G.1.7：报告提交成功的用例断言 `tool.arguments` 记录了注入选项；报告自身写入或提交失败的用例，用测试执行器保存的 argv、stderr、退出码与文件状态核对；未执行到注入点的用例单列；评估准入对 `@rsp`、单横线、双横线、`=值`、分离值写法都拒绝 | 部分核对；测试待补 |
| 3 | G.1.8：三项派生负对照按既有 `avg` 命令重跑，仍在 boundary 阶段失败，逐项保存命令与原因 | 查找方式已核对；负对照待重跑 |
| 4 | G.1.3 第 4 条与 G.1.10 第 2 条与补丁 6 的实现与测试一致；写 profile 的符号化路径不做 canonical 化（`L/ProfiledBinary.h:620` 传入的 `UseSymbolTable` 在 `L/ProfiledBinary.cpp:1212` 固定为 false，`:1297–1298` 不执行），`--show-canonical-fname` 只影响反汇编显示并在 IP 模式下被拒绝（`llvm-profgen.cpp:249`） | 源码已核对；测试待重跑 |
| 5 | 映射表与条目分类：① 合成全地址核对——为映射范围内边界可证明的每个指令起点构造一条合成样本，按工具的 perf 输入格式写入，用正式工具以 skid=`none` 与 `prev-inst`、聚合方式 `max` 分别转换，写出的每个条目按 5.8 第 5 条分类，只允许映射表命中、`boundary_unavailable` 或 `known_out_of_scope`（例如 `prev-inst` 的前驱落在范围外函数），出现 `unknown_name`、`reference_unresolved`、`unmapped_key` 即失败；② 独立保存并核对"地址 → 键 → 源位置"的完整关系与排除结果（这一步证明映射关系，①只证明键覆盖）；③ 边界排除组单独测试：`none` 转换把其条目归为 `boundary_unavailable`，`prev-inst`/`avg` 转换按冻结契约在 boundary 阶段失败；④ 在第一轮 CALIBRATION 运行的基准配置上做流程冒烟。夹具：映射表漏一个冷地址、删去一个碰撞地址后键集合不变、交换两个键的值、`prev-inst` 键算法错一位（都须被①或②发现）；同键不同源位置、同键同位置；两个命中函数集合不同的 RUN、删除热点函数全部条目、加显式零条目、改变预算（静态产物的 SHA 都不变）；原始 discriminator 不同而写出键相同、Thumb 别名、非叶子行号 0、偏移碰撞、不同构建路径、歧义键与正常键同时贡献同一行、名字闭包、评估侧错误地去掉 `.__uniq.` 后缀且 ELF 恰好有同名的范围外函数（期望无定义）、无法识别的函数名、一个计数很小的未对齐键（仍判无定义）、一个 `boundary_unavailable` 函数在 `none` 配置下有样本（单列，RUN 仍有定义）、同名组同时含可证明与不可证明的范围、被排除函数含热点内联体、FNDA 很小而循环行计数很大；补零 profile 不参与质量指标（只断言，补零键是否全部在映射表内只记录） | 待实现与核对 |
| 6 | 对象登记表：只用参考数据与 U 计算各构建、ISA、输入的 ①–③′、n_eff、K | 待计算 |
| 7 | M1、M2 与判读分支夹具：N=15、K=9、sample 全零时 M2 = 0；只有一个正计数热点；正计数并列；正计数行不足 K；T = 0；U 为空；K 无定义；n_eff 为 null 且 K ∈ {5, 49, 50, 80}（K < 50 只作描述；K = 80 进入 M2-only 判读模式，只有区间、退化与准入检查全部通过才输出"M2 等价，M1 未判读"）；n_eff 恰为 3；10 行敏感性下的空函数集合；累计恰好等于与刚好跨过 80% | 待实现 |
| 8 | 合并口径：互补上下文（d0/d1 = 100/0 与 0/100）期望 S = 100、S_alt = 200、S_sum = 200；同一内联函数在不同调用点走不同分支；同一行多个覆盖区域与不同 discriminator；未执行模板实例的键落在已执行实例的行上（计入"已对齐但不在 U 内"）；同时保存覆盖区域边界 | 待实现 |
| 9 | 区间模拟。验收场景（参数、种子与预期结果先固定）：标准误与 ε 之比 ∈ {0.05, 0.1, 0.25, 0.5} × 登记的阶段结构 × 阶段方差比 ∈ {1, 16}，分布为正态、离散步长 1/K、纯 Bernoulli 稀有事件（其余为精确 0）、全零差值、"一个阶段为纯稀有事件、另一阶段为非退化小扰动"；真实差值取 0、±0.02、±0.03；每个场景 10,000 次。报告场景（完整参数预先固定，只报告、不验收）：平移 lognormal 偏斜（偏度 0.5、1.0、3.3，长尾分别朝 +ε 与 −ε）；稀有事件叠加非退化小扰动（0.99 × Bernoulli(1/33) + 0.001 × Rademacher，以及 0.2 × Bernoulli(0.15) + N(0, 0.001)），分别用单阶段 15、5 + 10 与登记的阶段结构。每个场景输出参数、真实均值与方差、实际标准误与 ε 之比，两种区间及其包络的覆盖率、判为等价的比例、退化与无区间的比例、有效区间率与 Monte Carlo 标准误。验收：按决策置信集合计算的覆盖率 ≥ 93%；真实差值为 ±0.02 与 ±0.03 时判等价比例的估计值 ≤ 3.0%，并报告单侧 99% Clopper–Pearson 上界；全零场景 100% 退化、0% 判等价；退化或无区间的重复判等价必须为否，不得删去后再计算。任一验收场景不达标时，修订 3 登记 `quality_equivalence_enabled=false`（5.8 第 6 条），不换种子、不删场景、不修订本文。报告场景的结果写入修订 3 的局限说明 | 待执行 |
| 10 | 统计与登记门禁夹具：配对 RUN 顺序不同而 ID 相同；单边缺失与转换失败；RUN 级无定义按缺失；多个采集段只贡献一个 RUN；第 5 个 RUN 已显示等价时脚本不输出判读；3 + 12 的阶段退化反例；旧阶段差值为 [5.55e-17, −5.55e-17, 5.55e-17] 而新阶段非退化、[0.013] × 5、同一组份额按两种顺序求和得到的 M2 差（都判退化）；[0, 0, 1e-6]（不退化）；某阶段恒定非零、单阶段退化；两阶段时分层点估计等于普通均值；只有一个阶段时与普通配对实现一致；NaN 传播；包络与"双通过"的逻辑等价；任一 RUN 差值绝对值超过 ε 时输出标记；旧 5 + 新 10 全部合法通过、旧 RUN 没有初始化收据、篡改槽位表、旧 RUN 冒充新 RUN、同一原件占两个槽位、第 16 个 RUN、槽位成功后再追加成功、人工改判、第 14 个槽位没有终态时请求判读、计算日志 SHA 链断开、未推送的收据（都被门禁拒绝）；未知原因的 perf 非零退出（停止）、白名单故障且有正面证据（重采）、过热引起非零退出、stderr 丢失（停止）、只有传输中断（重传，不计尝试）、完整传输后 SHA 不一致（停止）、第四次尝试（第三次重采）仍失败而第五次被拒绝；空间不足停止后按事件记录在同一槽位继续（通过）、硬件事件错误停止后试图继续（拒绝，未完成槽位写入"停止缺失"）、"停止缺失"被门禁视为终态；登记前对真实 profile 请求 M3 或分支误差（拒绝）、登记后计算 M3 没有写日志（拒绝）；固定间隔的层不产生权重比较；合成 profile 允许计算 | 待实现 |
| 11 | 性能矩阵：从登记矩阵自动校验每组参数；缺少补零对照时拒绝输出"补零默认值已验证"；质量与性能的统计量、ε、停止规则没有混用；超过登记的 N 后拒绝计入新轮次；N 的公式夹具（CV 0.5% 得 13，1% 得 40，CV 为 0、缺失或非有限值、预试含一个离群轮次、无法预试时取 40）；G0 预试数据不进入正式轮次 | 待实现 |
| 12 | 板上（需要板子，加装散热后）：root 读取 `cpuinfo_cur_freq` 可用；会话开始时记录器以 `SEEK_SET` 读到首条序号 0，记录开机到会话开始的时长与 `CONFIG_LOG_BUF_SHIFT`，会话期间序号连续；模拟一次 boot_id 改变后的重启与重新核对；端点读取接口在"两次都没有新记录"与"后台已保存窗口内记录"两种情况下给出正确窗口；完整执行一次前后校准流程（30 秒、每个 CPU 计数有效的中间区间 ≥ 25、采样器并行时的行为）；"解码满载 + 采样器"试运行，负载期间 ≥ 99% 的读数间隔不超过 1.5 秒、没有超过 3 秒的间隔、采样器使解码耗时中位数的变化小于 0.5%；同一次试运行带采样器的 G0 耗时（至少 10 轮）用于计算 N；核对 5.9 第 5 条引用的内核函数与行号 | 待板上执行 |
| 13 | 覆盖参考：spike 上 lcov 的 `DA` 与 JSON 推得的行计数一致；按主文件代码区域推导的函数行范围与 lcov/JSON summary 交叉一致；主文件按 `findMainViewFileID` 的规则核对，返回空的记录单独报告；宏区域按区域类型与 FileID 识别；副本合并夹具（3 个编译单元的同一 static inline 函数只执行 1 个、宏内部循环、同文件同时含普通函数与宏定义、同一模板文件被不同名字包含两次、两个不同的已执行函数在同一物理行）；`HasMultipleRegions` 从 segments 提取的结果与 Coverage API 一致 | 待核对 |
| 14 | 离线资格分类：执行 5.9 第 5 条列出的全部判定脚本夹具（含记录器状态：首条序号不为 0、会话中 boot_id 改变而记录器没有重启、保存失败、输出路径不在 `/opt/afdo_agent/` 下），并用第一轮与四核诊断的原件重放，重放标签不覆盖历史资格 | 待实现 |
| 15 | ③ 门槛：按新的源函数合并规则与 ③ 的分母，在 FFmpeg（Thumb、A32）与 spike 的参考上计算 ③、③′ 与按互斥原因集合分桶的损失分解（各桶之和等于 ΣR(C) − ΣR(U)，同一行有两个排除原因时只计一次）；任一对象 ③ 低于 50% 时不登记，50%–80% 时登记文本须含损失分解 | 待计算 |
| 16 | 跨侧对应表：只用 ELF、调试文件与参考数据生成。夹具：左花括号另起一行与签名跨 3 行的单候选函数（正常对应）；没有 linkage name 的外部 C 函数（按 `DW_AT_name` 正常对应）；同一文件多个同名定义，包括条件编译导致声明行相同而函数体起点不同（不能唯一证明时判 `identity_ambiguous`）；候选较近但错误、正确候选缺失（不得选另一个候选）；`identity_ambiguous` 被内联进热点函数且有样本（RUN 有定义、相关行被排除）；libgcc 汇编函数有样本（`not_instrumented`，归为范围外）；评估侧错误地用 decl_line 精确匹配（期望 `unmatched_in_elf` 超过 1%，而不是静默归为范围外）；列出名字去后缀后与已执行参考源函数相同、却不在映射范围内的全部 ELF 顶层函数并逐个裁决，裁决证据随表保存 | 待生成 |
| 17 | 登记前打开过的真实 profile 清单与在其上计算过的量；G0 预试的条件、轮数、原始耗时与开销，写入修订 3 的披露 | 登记时执行 |
| 18 | 性能轮数 N：按第 12 项的 G0 预试与 5.9 第 5 条的公式确定每块板的 N；无法完成预试时取 40，写明来源 | 待确定 |
| 19 | 登记：①（协议、脚本、依赖、配置、对象登记表、对应表与裁决表、映射表、地址关系表、排除清单、边界排除组、U、权重、受控量清单、重采原因码白名单）、②（已存在输入清单）、③（完整 RUN 槽位表与既有 RUN 的初始化收据）的 SHA-256 写入修订 3，连同第 9 项的模拟结果与 `quality_equivalence_enabled` 的取值；修订 3 提交与推送成功的记录在正式受控量计算之前保存 | 登记时执行 |

### L.6 本版新写、尚未经评审的内容

以下三条已经 v1.3 评审，处理见附录 M.4 第 4 条。

1. 每个等价结论另报告每个 RUN 的差值与最大绝对差值，任一 RUN 的差值绝对值超过 ε 时输出标记（5.8 第 6 条）。这是描述，不改变判读结果。
2. 原因不明的停止，只有在事件记录给出可消除的原因（空间不足、过热、人工停止）后才能在同一槽位继续，否则未完成槽位写入"停止缺失"（5.8 第 6 条）。
3. `quality_equivalence_enabled=false` 时，聚合方式与 skid 的默认值按 5.4.4 第 5 条的保守规则与 5.9 的性能结果决定，M1、M2 的差值与区间只作描述（5.8 第 6、9 条）。

## 附录 M：v1.3 评审意见处理（Claude Code、Codex、Kimi Code）

三家的结论：Codex "修改后可以进入登记准备"（严重 1、重要 4、一般 2）；Claude Code "修改后可以进入登记准备"（严重 0、重要 4、一般 3）；Kimi Code "可以进入登记准备"（严重 0、重要 0、一般 1）。三家都认为上一轮两项严重问题的处理方向正确，第一阶段与补丁 1–9 不需要重开。本版不改补丁，不改已有 golden 值。下表按严重程度列出处理结果；"来源"一栏写明提出该问题的评审方，"采用"一栏写明最终采用了谁的方案以及原因。标"自拟"的内容列在 M.6。

### M.1 严重

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| 按 10⁻⁹ 固定网格舍入后再算方差，仍会被浮点噪声绕过：真实值恰在半格附近（例如 0.0130000005）时，±10⁻¹⁷ 的误差会落到两个格里，舍入后方差为 3×10⁻¹⁹，不为 0 | Codex 严重 1 | 采纳 | 采用 Codex 的方案：改为阶段极差规则，max(D_h) − min(D_h) ≤ 10⁻⁹ 即判退化（原因 `numerically_flat`）。极差对平移不变，不受分格影响；写明它表示"在登记的数值分辨率内不可区分"，不宣称数学上相等，并会保守地拒绝小于 10⁻⁹ 的真实波动。Claude Code 与 Kimi Code 认为舍入规则已经足够，Codex 的半格反例推翻了这一点 | 5.8 第 6 条；M.5 第 10 项 |

### M.2 重要

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| 回退开关会被 Monte Carlo 噪声触发：5 + 10、方差比 16 的场景真实判等价率约 2.77%，10,000 次重复时估计值超过 3.0% 的概率约 8%，整个网格有约 16%–40% 的概率仅因噪声关闭判读 | Claude Code 重要 1 | 采纳 | 采用 Claude Code 的方案：验收统计量改用只算分层 t 区间的 10⁶ 次重复。同一次重复中"包络判等价"必然蕴含"t 判等价"，包络必然包含 t 区间，所以 t 单独的判等价比例是包络的严格上界、t 单独的覆盖率是包络的严格下界；包络的 10,000 次结果照常报告。Monte Carlo 标准误降到约 0.016%，验收结论由方法性质决定，不再由种子决定 | M.5 第 9 项 |
| 场景网格含不可能的参数组合（全零场景不能有正标准误、纯 Bernoulli 的均值与方差不能独立指定、单阶段没有方差比、离散分布与 `N(0, 0.001)` 的参数不明确），执行方要自行删改，回退结果依赖实现选择；场景参数在了解回退后果后选定也有引导空间 | Codex 重要 2；Claude Code 重要 1 | 采纳，两家合并 | 显式场景清单写入 M.5 第 9 项，每行给出完整的生成分布与参数，清单、代码与种子在运行前提交并推送（Codex、Claude Code）；离散场景取 {−1/K, 0, 1/K} 的平移、K ∈ {50, 200}，纯 Bernoulli 取 p ∈ {0.05, 0.15}、跳变幅度 = Δ/p（Claude Code）；开关是全局开关，由脚本按验收结果写出，不人工设定，不按对象分别选择；执行异常、缺行或参数不符是执行失败，不触发回退（Codex）。自拟：执行失败时修正实现，按同一清单与种子重跑 | 5.8 第 6 条；M.5 第 9 项 |
| 没有登记明确的工作模型，局限说明不能替代这一前提；L.1 把上一轮写成"两家都确认任何区间方法都消除不了"不准确，保守方法可以用宽区间或拒判控制风险 | Codex 重要 1 | 采纳 | 采用 Codex 的方案：登记工作模型（阶段内配对差值独立同分布、阶段间独立、t 与 bootstrap 的近似），结果名称加"登记工作模型条件下"，区间注明为名义 95%，每条结论附模型标识与未验证的假设；L.1 的归纳更正为"部分采纳 Codex 的方案：采纳回退机制，未采纳把压力场景作为准入条件" | 5.8 第 6 条；M.4 |
| `not_instrumented` 只凭"名字在覆盖导出中不存在"判定，两侧命名规则一旦不一致，所有 static 函数都会被静默归为范围外 | Claude Code 重要 2 | 采纳 | 采用 Claude Code 的方案：按编译单元判定——CU 的源文件不在覆盖导出的文件表中，且 producer 不是评估所用的 clang（本构建为 libgcc 的 5 个 GNU AS CU 与 5 个 GNU C CU）；源文件在覆盖导出中却找不到同名参考函数的，记为没有结论，从而在登记前暴露 | 5.8 第 5 条；M.5 第 16 项 |
| 内联帧的抽象源在对应表中没有结论时，样本会静默落入"已对齐但不在 U 内"，S(line) 被系统性低估而所有检查都通过；"表中有记录"不等于"有有效结论"；单候选在正确候选缺失时会直接对应到错误候选；只含歧义候选的顶层函数可能不被枚举 | Claude Code 重要 3；Codex 重要 3 | 采纳，两家合并 | 对应表覆盖完整性的静态检查（映射范围内每个 DWARF 函数，含内联抽象源，都须有封闭枚举内的结论，否则登记准备失败）、"已对齐但不在 U 内"按原因分列：Claude Code。结论状态用封闭枚举、`pending` 与主文件缺失不算结论、映射范围的种子包含含已执行候选的 `identity_ambiguous`、歧义键保存候选集合与排除标志、同组中不在映射表里的键仍判未对齐：Codex。单候选的静态一致性检查采用 Codex 的要求，具体判据为自拟：该 DWARF 函数以自身为叶子帧、文件等于其 decl_file 的全部行号都落在候选的行范围内 | 5.8 第 5 条；M.5 第 5、16 项 |
| 停止后的恢复缺少状态机与正面证据：原因不明的停止只凭事件记录"宣称"可消除原因就能继续，门禁只看收据，无法核验恢复是否合法 | Codex 重要 4；Claude Code 重要 4 | 采纳，两家合并 | 状态机（`paused_stop` → 追加的恢复事件或 `stopped_missing` 终态、恢复事件引用原收据与证据 SHA、后续尝试引用恢复事件、终态不可撤销、门禁核验完整的状态迁移）：Codex。证据的具体条件（空间、温度的时间窗与阈值、人工停止须有事先的命令记录）、恢复前重新做身份断言：Claude Code | 5.8 第 6 条；M.5 第 10 项 |

### M.3 一般

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| "存在超过 ε 的单次差值"几乎总会出现（标准误与 ε 之比为 0.25 时概率约 99.5%），不提供信息 | Claude Code 一般 1 | 采纳 | 改为报告超过 ε 的 RUN 个数；只有差值偏离本层中位数超过 max(ε, 5 × MAD) 时才标"存在离群的单次差值"。Codex 同意这一标记只作描述 | 5.8 第 6 条 |
| "地址 → 键 → 源位置"关系核对如果复用映射表的生成代码，就是自己核对自己 | Claude Code 一般 2 | 采纳 | 用不共享实现的第二条路径（`llvm-symbolizer` 逐地址符号化，加上独立的键计算）重算并逐项比较 | M.5 第 5 项 |
| DWARF 名字的回退没有完整复现 LLVM 的算法（还有 `DW_AT_MIPS_linkage_name`，并沿 abstract origin、specification、signature 递归） | Codex 一般 1 | 采纳 | 名字取 `getSubroutineName(LinkageName)` 的结果，实现复用该接口或完整复现其规则 | 5.8 第 5 条；M.5 第 16 项 |
| 改写时丢了"非阻塞打开"，端点算法依赖读到 EAGAIN；一个 RUN 的两个端点可能跨 boot | Codex 一般 2 | 采纳 | 写明 `O_RDONLY \| O_NONBLOCK` 打开并 `lseek(fd, 0, SEEK_SET)`；两个端点须属于同一 boot_id，否则判 unknown | 5.9 第 5 条 |
| 长时间开机后日志缓冲已回卷时没有出路；N 的边界夹具没有写期望值 | Claude Code 一般 3；Kimi Code 一般 1 | 采纳，两家合并 | 会话开始时首条序号不为 0 时不开始采集，告知用户：由用户在会话前重启板子（用户操作，Agent 不重启），或由用户决定接受该次开机的欠压项为 unknown，决定写入事件记录（Claude Code 的两种出路）。不采用 Kimi Code 的"修订本文"：这是可以预先写定的操作选择，不需要修订规则。N 的夹具：CV 为 0 时 N = 10，CV 缺失或非有限值时 N = 40 | 5.9 第 5 条；M.5 第 11、12 项 |

### M.4 对前一版附录的更正

1. L.1 第 1 行"两家都确认任何区间方法都消除不了这一盲区"不准确：有限样本可能漏掉稀有事件，但更保守的方法可以用宽区间或拒判控制风险，代价是判别力下降。处理应写为"部分采纳 Codex 的方案：采纳回退机制，未采纳把压力场景作为准入条件，选择保留标注工作模型条件的推断"。
2. L.1 第 2 行的 10⁻⁹ 舍入规则已由极差规则取代（M.1）。
3. L.5 第 12 项"模拟一次 boot_id 改变后的重启"不得在板上通过重启实现，改为离线夹具（M.5 第 14 项）。
4. L.6 三条：第 1 条（逐 RUN 差值与超 ε 标记）改为离群标记（M.3）；第 2 条（原因不明的停止）改为须有可核验的正面证据（M.2）；第 3 条（关闭判读时默认值由保守规则与性能结果决定）经三家确认。
5. L.5 由 M.5 取代。

### M.5 执行前须核对的事项（取代 L.5）

v1.5 起本节由附录 N.5 取代，以下保留 v1.4 原文。

登记修订 3 之前由执行方完成。除第 9 项按预先登记的规则回退外，结果与本文不符时先修订本文，再登记。只有第 12 项需要板子；全部事项都不对正式 sample profile 计算任何受控量。

| 编号 | 事项 | 状态 |
|---|---|---|
| 1 | G.1.1 的前驱条件与原因分类与补丁 5 一致 | 已核对 |
| 2 | G.1.7：报告提交成功的用例断言 `tool.arguments` 记录了注入选项；报告自身写入或提交失败的用例，用测试执行器保存的 argv、stderr、退出码与文件状态核对；未执行到注入点的用例单列；评估准入对 `@rsp`、单横线、双横线、`=值`、分离值写法都拒绝 | 部分核对；测试待补 |
| 3 | G.1.8：三项派生负对照按既有 `avg` 命令重跑，仍在 boundary 阶段失败，逐项保存命令与原因 | 查找方式已核对；负对照待重跑 |
| 4 | G.1.3 第 4 条与 G.1.10 第 2 条与补丁 6 的实现与测试一致；写 profile 的符号化路径不做 canonical 化（`L/ProfiledBinary.h:620`、`L/ProfiledBinary.cpp:1212`、`:1297–1298`），`--show-canonical-fname` 只影响反汇编显示并在 IP 模式下被拒绝（`llvm-profgen.cpp:249`） | 源码已核对；测试待重跑 |
| 5 | 映射表与条目分类：① 合成全地址核对——为映射范围内边界可证明的每个指令起点构造一条合成样本，用正式工具以 skid=`none` 与 `prev-inst`、聚合方式 `max` 分别转换，写出的每个条目按 5.8 第 5 条分类，只允许映射表命中、`boundary_unavailable` 或 `known_out_of_scope`，出现 `unknown_name`、`reference_unresolved`、`unmapped_key` 即失败；② 用不共享映射表生成实现的第二条路径（`llvm-symbolizer` 逐地址符号化，加上独立的键计算）重算"地址 → 键 → 源位置"关系与排除结果，逐项比较；③ 边界排除组单独测试：`none` 转换把其条目归为 `boundary_unavailable`，`prev-inst`/`avg` 转换按冻结契约在 boundary 阶段失败；④ 在第一轮 CALIBRATION 运行的基准配置上做流程冒烟。夹具：映射表漏一个冷地址、删去一个碰撞地址后键集合不变、交换两个键的值、`prev-inst` 键算法错一位（都须被①或②发现）；同键不同源位置、同键同位置；两个命中函数集合不同的 RUN、删除热点函数全部条目、加显式零条目、改变预算（静态产物的 SHA 都不变）；原始 discriminator 不同而写出键相同、Thumb 别名、非叶子行号 0、偏移碰撞、不同构建路径、歧义键与正常键同时贡献同一行、名字闭包、评估侧错误地去掉 `.__uniq.` 后缀且 ELF 恰好有同名的范围外函数（期望无定义）、无法识别的函数名、一个计数很小的未对齐键（仍判无定义）、一个 `boundary_unavailable` 函数在 `none` 配置下有样本（单列，RUN 仍有定义）、同名组同时含可证明与不可证明的范围、被排除函数含热点内联体、FNDA 很小而循环行计数很大；顶层函数只含歧义候选（被枚举，命中的键计入"已对齐但不在 U 内"）、热点顶层函数同时含正常与歧义的内联体、在歧义组中注入不存在的键（仍判未对齐）、对应表中存在 `pending` 记录（登记准备失败）；补零 profile 不参与质量指标 | 待实现与核对 |
| 6 | 对象登记表：只用参考数据与 U 计算各构建、ISA、输入的 ①–③′、n_eff、K；另列出第一轮补丁 9 重转中 `prev-inst`、`avg` 转换是否成功（可用性信息，不是受控量） | 待计算 |
| 7 | M1、M2 与判读分支夹具：N=15、K=9、sample 全零时 M2 = 0；只有一个正计数热点；正计数并列；正计数行不足 K；T = 0；U 为空；K 无定义；n_eff 为 null 且 K ∈ {5, 49, 50, 80}（K < 50 只作描述；K = 80 进入 M2-only 判读模式，只有区间、退化与准入检查全部通过才输出等价）；n_eff 恰为 3；10 行敏感性下的空函数集合；累计恰好等于与刚好跨过 80% | 待实现 |
| 8 | 合并口径：互补上下文（d0/d1 = 100/0 与 0/100）期望 S = 100、S_alt = 200、S_sum = 200；同一内联函数在不同调用点走不同分支；同一行多个覆盖区域与不同 discriminator；未执行模板实例的键落在已执行实例的行上（计入"已对齐但不在 U 内（未执行）"）；同时保存覆盖区域边界 | 待实现 |
| 9 | 区间模拟。场景清单、模拟代码与种子在运行前提交并推送（记录 SHA）；脚本先核对实际矩与清单一致，不可行的参数组合在运行前报错。记号：Δ 为真实均值差；"结构"取单阶段 15 与登记的阶段结构（预期为 5 + 10）；两阶段的方差比取 1 与 16，16 时分别让小阶段与大阶段的方差较大。验收场景：A1 正态，D_h ~ Normal(mean=Δ, sd=σ_h)，σ_h 使分层标准误与 ε 之比 ∈ {0.05, 0.1, 0.25, 0.5}，Δ ∈ {0, ±0.02, ±0.03}；A2 离散，D = Δ + U/K，U 在 {−1, 0, +1} 上等概率，K ∈ {50, 200}，Δ 同上；A3 纯 Bernoulli，D = a × Bernoulli(p)，其余为精确 0，p ∈ {0.05, 0.15}，a = Δ/p，Δ ∈ {±0.02, ±0.03}，各阶段同参数；A4 全零，D ≡ 0（Δ = 0，标准误为 0）；A5 两阶段，第一阶段 D = a × Bernoulli(0.15) 且 a = Δ/(λ₁ × 0.15)，第二阶段 D ~ Normal(mean=0, sd=0.001)，Δ ∈ {±0.02, ±0.03}。单阶段场景的方差比记 not_applicable。验收统计量：每个验收场景以 10⁶ 次重复只计算分层 t 区间（退化重复按"不判等价、覆盖为真"计），t 单独的覆盖率 ≥ 93%，Δ 为 ±0.02 与 ±0.03 时 t 单独的判等价比例 ≤ 3.0%；A4 须 100% 退化、0% 判等价。包络（两种区间）另以 10,000 次重复照常报告，不作为验收统计量。报告场景（只报告、不验收）：B1 平移 lognormal，σ_log ∈ {0.17, 0.32, 0.75}（偏度约 0.5、1.0、3.3），长尾分别朝 +ε 与 −ε，平移使均值为 Δ ∈ {±0.02}，尺度使标准误与 ε 之比为 0.1；B2 D = 0.99 × Bernoulli(1/33) + 0.001 × Rademacher；B3 D = 0.2 × Bernoulli(0.15) + Normal(mean=0, sd=0.001)；B2、B3 用单阶段 15 与登记的阶段结构。每个场景输出参数、真实均值与方差、实际标准误与 ε 之比、覆盖率、判等价比例、退化比例与 Monte Carlo 标准误。全部验收场景完整执行并通过时开关为 true，任一统计验收不达标时为 false，由脚本写出；执行异常、缺行、参数或种子与登记清单不符属于执行失败，修正实现后按同一清单与种子重跑，不触发回退。报告场景的结果写入修订 3 的局限说明 | 待执行 |
| 10 | 统计与登记门禁夹具：配对 RUN 顺序不同而 ID 相同；单边缺失与转换失败；RUN 级无定义按缺失；多个采集段只贡献一个 RUN；第 5 个 RUN 已显示等价时脚本不输出判读；3 + 12 的阶段退化反例；半格反例（0.0130000005000000555 与 0.0130000004999999445 交替）及其负数版本（都判退化）；给同一组差值加共同常数后退化结果不变；极差恰为 10⁻⁹、略小、略大；[0, 0, 1e-6]（不退化）；同一组份额按两种顺序求和得到的 M2 差（退化）；某阶段恒定非零、单阶段退化；两阶段时分层点估计等于普通均值；只有一个阶段时与普通配对实现一致；NaN 传播；包络与"双通过"的逻辑等价；每条等价结论带模型标识；`quality_equivalence_enabled=false` 时任何对象、任何敏感性分支都不输出等价；离群标记（标准误与 ε 之比为 0.25 的正态差值大多不标，14 个约为 0、1 个为 0.3 时标记）；旧 5 + 新 10 全部合法通过、旧 RUN 没有初始化收据、篡改槽位表、旧 RUN 冒充新 RUN、同一原件占两个槽位、第 16 个 RUN、槽位成功后再追加成功、人工改判、第 14 个槽位没有终态时请求判读、计算日志 SHA 链断开、未推送的收据（都被门禁拒绝）；未知原因的 perf 非零退出（`paused_stop`）、白名单故障且有正面证据（重采）、过热引起非零退出、stderr 丢失、只有传输中断（重传，不计尝试）、完整传输后 SHA 不一致；原因不明的暂停后有合法证据恢复（通过）、事件只有说明文字（拒绝）、空间证据的 `df` 记录正常（拒绝）、温度证据的时间戳不在失败前后 10 秒内（拒绝）、没有恢复事件直接追加成功收据（拒绝）、恢复事件改变采集条件（拒绝，属于协议变更）、第四次尝试停止后申请恢复（拒绝）、`stopped_missing` 后再次采集（拒绝）、硬件事件错误停止（未完成槽位进入"停止缺失"）、遥测异常或转换失败进入恢复路径（拒绝）；登记前对真实 profile 请求 M3 或分支误差（拒绝）、登记后计算 M3 没有写日志（拒绝）；固定间隔的层不产生权重比较；合成 profile 允许计算 | 待实现 |
| 11 | 性能矩阵：从登记矩阵自动校验每组参数；缺少补零对照时拒绝输出"补零默认值已验证"；质量与性能的统计量、ε、停止规则没有混用，关闭质量判读不改变性能规则；超过登记的 N 后拒绝计入新轮次；N 的公式夹具：CV 0.5% 得 13，1% 得 40，CV 为 0 得 10，CV 缺失或为 NaN、无穷时视为无法预试得 40，预试含一个离群轮次时按未剔除的 CV 计算；G0 预试数据不进入正式轮次 | 待实现 |
| 12 | 板上（需要板子，加装散热后）：root 读取 `cpuinfo_cur_freq` 可用；记录器以 `O_RDONLY \| O_NONBLOCK` 打开并 `lseek(fd, 0, SEEK_SET)` 后读到首条序号 0，无新记录时立即返回；记录开机到会话开始的时长、`CONFIG_LOG_BUF_SHIFT` 与按当时的日志速率估计的回卷时间，会话期间序号连续；端点读取接口在"两次都没有新记录"与"后台已保存窗口内记录"两种情况下给出正确窗口；完整执行一次前后校准流程（30 秒、每个 CPU 计数有效的中间区间 ≥ 25、采样器并行时的行为）；"解码满载 + 采样器"试运行，负载期间 ≥ 99% 的读数间隔不超过 1.5 秒、没有超过 3 秒的间隔、采样器使解码耗时中位数的变化小于 0.5%；同一次试运行带采样器的 G0 耗时（至少 10 轮）用于计算 N；核对 5.9 第 5 条引用的内核函数与行号。板上不为测试而重启 | 待板上执行 |
| 13 | 覆盖参考：spike 上 lcov 的 `DA` 与 JSON 推得的行计数一致；按主文件代码区域推导的函数行范围与 lcov/JSON summary 交叉一致；主文件按 `findMainViewFileID` 的规则核对，返回空的记录单独报告，并在对应表中有明确的状态；宏区域按区域类型与 FileID 识别；副本合并夹具（3 个编译单元的同一 static inline 函数只执行 1 个、宏内部循环、同文件同时含普通函数与宏定义、同一模板文件被不同名字包含两次、两个不同的已执行函数在同一物理行）；`HasMultipleRegions` 从 segments 提取的结果与 Coverage API 一致 | 待核对 |
| 14 | 离线资格分类：执行 5.9 第 5 条列出的全部判定脚本夹具，含记录器状态（首条序号不为 0 时不开始采集、会话中 boot_id 改变而记录器没有重启、一个 RUN 的两个端点跨 boot、保存失败、输出路径不在 `/opt/afdo_agent/` 下、非阻塞描述符无新记录时及时返回）；boot_id 改变用离线模拟，不在板上重启；用第一轮与四核诊断的原件重放，重放标签不覆盖历史资格 | 待实现 |
| 15 | ③ 门槛：按新的源函数合并规则与 ③ 的分母，在 FFmpeg（Thumb、A32）与 spike 的参考上计算 ③、③′ 与按互斥原因集合分桶的损失分解（各桶之和等于 ΣR(C) − ΣR(U)）；任一对象 ③ 低于 50% 时不登记，50%–80% 时登记文本须含损失分解 | 待计算 |
| 16 | 跨侧对应表：只用 ELF、调试文件与参考数据生成，结论状态为封闭枚举，覆盖映射范围内每个 DWARF 函数（含内联抽象源），任一没有结论时登记准备失败。夹具：左花括号另起一行与签名跨 3 行的单候选函数（通过一致性检查，正常对应）；正确候选缺失、只剩一个同名错误候选（一致性检查失败，不建立对应）；名字规则：只有 `DW_AT_name`、只有 `DW_AT_MIPS_linkage_name`、名字只在 specification 或 abstract origin 上、多种属性并存（与 `getSubroutineName(LinkageName)` 一致）；同一文件多个同名定义，包括条件编译导致声明行相同而函数体起点不同（判 `identity_ambiguous`）；`identity_ambiguous` 被内联进热点函数且有样本（RUN 有定义、相关行被排除）；GNU C 编译的 `libgcc2.c` 函数与 GNU AS 函数有样本（`not_instrumented`，归为范围外）；`not_instrumented` 外层含已执行参考函数的内联体（不得整组归为范围外）；覆盖侧不带 unique 名字而 DWARF 侧带（没有结论，登记准备失败）；clang C 编译单元中一个函数在覆盖导出中缺失（没有结论）；同一头文件在两个 CU 中的 decl_file 写法不同且只规范化了其中一种（登记准备失败）；内联帧对应到参考侧未执行的函数（计入"已对齐但不在 U 内（未执行）"）；列出名字去后缀后与已执行参考源函数相同、却不在映射范围内的全部 ELF 顶层函数并逐个裁决，裁决证据随表保存；报告 `not_instrumented` 的 CU 清单与 producer 分布 | 待生成 |
| 17 | 登记前打开过的真实 profile 清单与在其上计算过的量；G0 预试的条件、轮数、原始耗时与开销，写入修订 3 的披露 | 登记时执行 |
| 18 | 性能轮数 N：按第 12 项的 G0 预试与 5.9 第 5 条的公式确定每块板的 N；无法完成预试时取 40，写明来源 | 待确定 |
| 19 | 登记：①（协议与工作模型、脚本、依赖、配置、对象登记表、对应表与裁决表、映射表、地址关系表、排除清单、边界排除组、U、权重、受控量清单、重采原因码白名单与证据条件、停止与恢复事件的格式）、②（已存在输入清单）、③（完整 RUN 槽位表与既有 RUN 的初始化收据）的 SHA-256 写入修订 3，连同第 9 项的场景清单、模拟代码与种子的 SHA、模拟结果与 `quality_equivalence_enabled` 的取值；修订 3 提交与推送成功的记录在正式受控量计算之前保存 | 登记时执行 |

### M.6 本版新写、尚未经评审的内容

以下三条已经 v1.4 评审，处理见附录 N.4 第 2 条。

1. 单候选的静态一致性检查判据：该 DWARF 函数以自身为叶子帧、文件等于其 decl_file 的全部行号（行号 0 除外）都落在候选的行范围内（5.8 第 5 条）。
2. 模拟执行失败时，修正实现后按同一清单与种子重跑（5.8 第 6 条；M.5 第 9 项）。
3. A5 场景的参数取法：第一阶段的跳变幅度 a = Δ/(λ₁ × 0.15)，使混合均值等于 Δ（M.5 第 9 项）。

## 附录 N：v1.4 评审意见处理（Claude Code、Codex、Kimi Code）

三家的结论：Codex "修改后可以进入登记准备"（严重 0、重要 3、一般 4）；Claude Code "修改后可以进入登记准备"（严重 0、重要 2、一般 4）；Kimi Code "可以进入登记准备"（严重 0、重要 0、一般 1）。三家都确认上一轮的严重问题（半格舍入）已由阶段极差规则修复，没有新的严重问题，第一阶段与补丁 1–9 不需要重开。按项目约定（STATUS 中记录的人工裁决），本轮没有严重问题，修订后不再评审设计文档，直接开始 N.5 的登记前准备。本版不改补丁，不改已有 golden 值。下表按严重程度列出处理结果。

### N.1 严重

无。

### N.2 重要

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| 单候选的行范围包含检查不能证明身份：Codex 用 LLVM 22.1.8 编译了一个条件编译的合成例，参考侧（`MODE_A=1`）覆盖区域为第 3–9 行、声明行 3，被采样侧（`MODE_A=0`）声明行 5、行号 5、7、8，全部落在 [3, 9] 内，现行规则会对应到错误的定义；行号集合为空时"全部落在范围内"空集成立 | Codex 重要 1 | 采纳 | 采用 Codex 的方案：单候选须有定义身份证据——两侧的定义声明位置（C 构建的调试信息，或同源码同预处理定义的 clang AST）相同；行范围包含只作一致性证据；行号集合为空不算通过；证据不足或冲突时显式裁决或判歧义 | 5.8 第 5 条；N.5 第 16 项 |
| 对应表覆盖完整性只查映射范围，而映射范围又由对应结论播种：一个对应失败的顶层函数正因失败而不在范围内，检查看不到它，错误要到登记后的 RUN 级才暴露；`not_instrumented` 是负面筛选，字段缺失或解析失败也会被当成未插桩 | Codex 重要 2；Claude Code 重要 1 | 采纳，两家合并 | 先独立于映射范围枚举被采样 ELF 的全部有代码 DWARF 函数（含内联抽象源与优化克隆），为每一项建立结论，再由结论导出映射范围（两家一致）。`not_instrumented` 须先查参考候选，字段完整，并命中带构建或链接来源证据的登记外部 CU 清单，字段缺失或解析失败保留为没有结论；夹具改为"只有约定后缀的有无不同时正常对应、修饰方式不同或漏做规范化时失败"（Codex） | 5.8 第 5 条；N.5 第 16 项 |
| 恢复条件只证明"失败附近发生过异常"，没有证明故障归属与故障已消除；证据记录由谁、何时产生没有规定，失败发生在批次中途或拉回阶段时没有证据可用 | Codex 重要 3；Claude Code 一般 4 | 采纳，两家合并 | 恢复证据分三部分：与该 attempt_id、boot_id 关联的停止动作记录；恢复前新采集的状态证据；重新通过身份断言；时间窗内的环境异常只作佐证，不可恢复原因优先（Codex）。每次尝试结束与检测到失败时由脚本自动记录 `df` 与全部温度读数（Claude Code）。代价：没有关联停止动作的未知退出不能恢复，未完成槽位进入"停止缺失"，继续采集须作为新的预注册修订 | 5.8 第 6 条；N.5 第 10 项 |
| 完整运行之后再发现统计实现错误时没有规定，可以借"修正后重跑"一直重跑到开关为 true | Claude Code 重要 2 | 采纳 | 完整运行的结果保存推送；之后因实现错误重跑时，开关取全部完整运行结果的合取；模拟与正式分析调用同一实现模块，SHA 登记；统计验收不达标不能改称执行失败（Codex 一般 2 的补充） | 5.8 第 6 条；N.5 第 9 项 |

### N.3 一般

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| 名字查找的文字顺序与源码相反：`getLinkageName()` 按 `{DW_AT_MIPS_linkage_name, DW_AT_linkage_name}` 的顺序查找 | Codex 一般 1 | 采纳 | 改为"在每个访问到的 DIE 上先查 MIPS、再查标准 linkage name"，并加两种属性并存的夹具。Claude Code 与 Kimi Code 核对的是接口与递归属性，未指出顺序 | 5.8 第 5 条 |
| "t 单独是包络的严格界、验收不再由种子决定"说得过满：总体概率上是允许相等的保守界，两批次数不同的模拟估计值不保证逐次有序，10⁶ 次只是降低种子波动 | Codex 一般 2 | 采纳 | 改为"保守界（允许相等）"，有限次估计报告 Monte Carlo 标准误；不因独立的万次包络估计略高于百万次 t 估计而判代码错误 | N.5 第 9 项；N.4 |
| 场景清单顶部的"方差比 1、16"看起来适用于全部场景，但 A2、A3 只能为 1，A4 为 0/0，A5 由参数决定（5 + 10 时约为 20400 与 45900）；按全组合生成会在运行前报错 | Codex 一般 3；Claude Code 一般 1 | 采纳，两家合并 | 写明适用矩阵，清单逐行列出、不按全组合生成；A1 的阶段方差用 Codex 给出的闭式解确定。Claude Code 用合成数据跑过可行组合，A2、A3、A5 都能通过 | N.5 第 9 项 |
| 阶段极差规则的边界比较没有约定精度：`[0, 1e-9]` 用 double 与用有理数比较结论不同 | Claude Code 一般 2 | 采纳 | 一律以 IEEE-754 double 比较，阈值为字面量 1e-9 的 double；有理数算出的 M2 差值先转为 double | 5.8 第 6 条；N.5 第 10 项 |
| 单候选的行范围检查对签名所在的行过严 | Claude Code 一般 3；Kimi Code 一般 1 | 采纳 | 下界放宽为 min(decl_line, 候选起始行)；登记前报告未通过检查的单候选函数个数与参考计数。与 N.2 第 1 行合并：放宽的只是一致性检查，身份由定义声明位置证明 | 5.8 第 5 条 |
| 日志回卷后"接受 unknown"的分支没有进入登记前验收，可能被挡住或被误当成完整日志路径；"Agent 不重启"宜写成"评估脚本不重启" | Codex 一般 4 | 采纳 | 两条路径分别验收：首条序号 0 时验证完整日志路径；首条不为 0 时默认阻止，只有采集前已有接受事件才继续，且不记为完整路径通过；采集后补授权不能追认 | 5.9 第 5 条；N.5 第 12、14 项 |

### N.4 对前一版附录的更正

1. M.2 第 1 行"t 单独的判等价比例是包络的严格上界、覆盖率是严格下界……验收结论由方法性质决定，不再由种子决定"说得过满：这是总体概率上允许相等的保守界，有限次模拟估计仍有 Monte Carlo 误差。
2. M.6 三条：第 1 条（单候选检查判据）改为定义身份证据加放宽的一致性检查；第 2 条（执行失败后重跑）补充"完整运行取合取"；第 3 条（A5 参数）经三家确认。
3. M.5 由 N.5 取代。

### N.5 执行前须核对的事项（取代 M.5）

v1.6 起本节由附录 O.5 取代，以下保留 v1.5 原文。

登记修订 3 之前由执行方完成。除第 9 项按预先登记的规则回退外，结果与本文不符时先修订本文，再登记。只有第 12 项需要板子；全部事项都不对正式 sample profile 计算任何受控量。

| 编号 | 事项 | 状态 |
|---|---|---|
| 1 | G.1.1 的前驱条件与原因分类与补丁 5 一致 | 已核对 |
| 2 | G.1.7：报告提交成功的用例断言 `tool.arguments` 记录了注入选项；报告自身写入或提交失败的用例，用测试执行器保存的 argv、stderr、退出码与文件状态核对；未执行到注入点的用例单列；评估准入对 `@rsp`、单横线、双横线、`=值`、分离值写法都拒绝 | 部分核对；测试待补 |
| 3 | G.1.8：三项派生负对照按既有 `avg` 命令重跑，仍在 boundary 阶段失败，逐项保存命令与原因 | 查找方式已核对；负对照待重跑 |
| 4 | G.1.3 第 4 条与 G.1.10 第 2 条与补丁 6 的实现与测试一致；写 profile 的符号化路径不做 canonical 化（`L/ProfiledBinary.h:620`、`L/ProfiledBinary.cpp:1212`、`:1297–1298`），`--show-canonical-fname` 只影响反汇编显示并在 IP 模式下被拒绝（`llvm-profgen.cpp:249`） | 源码已核对；测试待重跑 |
| 5 | 映射表与条目分类：① 合成全地址核对——为映射范围内边界可证明的每个指令起点构造一条合成样本，用正式工具以 skid=`none` 与 `prev-inst`、聚合方式 `max` 分别转换，写出的每个条目按 5.8 第 5 条分类，只允许映射表命中、`boundary_unavailable` 或 `known_out_of_scope`，出现 `unknown_name`、`reference_unresolved`、`unmapped_key` 即失败；② 用不共享映射表生成实现的第二条路径（`llvm-symbolizer` 逐地址符号化，加上独立的键计算）重算"地址 → 键 → 源位置"关系与排除结果，逐项比较；③ 边界排除组单独测试：`none` 转换把其条目归为 `boundary_unavailable`，`prev-inst`/`avg` 转换按冻结契约在 boundary 阶段失败；④ 在第一轮 CALIBRATION 运行的基准配置上做流程冒烟。夹具：映射表漏一个冷地址、删去一个碰撞地址后键集合不变、交换两个键的值、`prev-inst` 键算法错一位（都须被①或②发现）；同键不同源位置、同键同位置；两个命中函数集合不同的 RUN、删除热点函数全部条目、加显式零条目、改变预算（静态产物的 SHA 都不变）；原始 discriminator 不同而写出键相同、Thumb 别名、非叶子行号 0、偏移碰撞、不同构建路径、歧义键与正常键同时贡献同一行、名字闭包、评估侧错误地去掉 `.__uniq.` 后缀且 ELF 恰好有同名的范围外函数（期望无定义）、无法识别的函数名、一个计数很小的未对齐键（仍判无定义）、一个 `boundary_unavailable` 函数在 `none` 配置下有样本（单列，RUN 仍有定义）、同名组同时含可证明与不可证明的范围、被排除函数含热点内联体、FNDA 很小而循环行计数很大；顶层函数只含歧义候选（被枚举，命中的键计入"已对齐但不在 U 内"）、热点顶层函数同时含正常与歧义的内联体、在歧义组中注入不存在的键（仍判未对齐）、对应表中存在 `pending` 记录（登记准备失败）；补零 profile 不参与质量指标 | 待实现与核对 |
| 6 | 对象登记表：只用参考数据与 U 计算各构建、ISA、输入的 ①–③′、n_eff、K；另列出第一轮补丁 9 重转中 `prev-inst`、`avg` 转换是否成功（可用性信息，不是受控量） | 待计算 |
| 7 | M1、M2 与判读分支夹具：N=15、K=9、sample 全零时 M2 = 0；只有一个正计数热点；正计数并列；正计数行不足 K；T = 0；U 为空；K 无定义；n_eff 为 null 且 K ∈ {5, 49, 50, 80}（K < 50 只作描述；K = 80 进入 M2-only 判读模式，只有区间、退化与准入检查全部通过才输出等价）；n_eff 恰为 3；10 行敏感性下的空函数集合；累计恰好等于与刚好跨过 80% | 待实现 |
| 8 | 合并口径：互补上下文（d0/d1 = 100/0 与 0/100）期望 S = 100、S_alt = 200、S_sum = 200；同一内联函数在不同调用点走不同分支；同一行多个覆盖区域与不同 discriminator；未执行模板实例的键落在已执行实例的行上（计入"已对齐但不在 U 内（未执行）"）；同时保存覆盖区域边界 | 待实现 |
| 9 | 区间模拟。场景清单、模拟代码与种子在运行前提交并推送（记录 SHA）；脚本先核对实际矩与清单一致，不可行的参数组合在运行前报错。记号：Δ 为真实均值差；"结构"取单阶段 15 与登记的阶段结构（预期为 5 + 10）。适用矩阵（清单逐行列出，不按全组合生成）：A1 用全部结构、全部标准误比；两阶段时方差比取 1 与 16，16 时分别让小阶段与大阶段的方差较大，阶段方差由闭式解确定：σ₂² = s² ÷ (λ₁²·r/n₁ + λ₂²/n₂)、σ₁² = r·σ₂²（s 为目标分层标准误，r 为方差比）；单阶段方差比记 not_applicable。A2 用全部结构，方差比只取 1，标准误比由 K 决定、照实报告。A3 用全部结构，各阶段同参数，方差比与标准误比照实报告。A4 用全部结构，标准误比为 0，方差比记 not_applicable。A5 只用两阶段的登记结构，方差比由参数推导并报告。验收场景：A1 正态，D_h ~ Normal(mean=Δ, sd=σ_h)，σ_h 使分层标准误与 ε 之比 ∈ {0.05, 0.1, 0.25, 0.5}，Δ ∈ {0, ±0.02, ±0.03}；A2 离散，D = Δ + U/K，U 在 {−1, 0, +1} 上等概率，K ∈ {50, 200}，Δ 同上；A3 纯 Bernoulli，D = a × Bernoulli(p)，其余为精确 0，p ∈ {0.05, 0.15}，a = Δ/p，Δ ∈ {±0.02, ±0.03}，各阶段同参数；A4 全零，D ≡ 0（Δ = 0，标准误为 0）；A5 两阶段，第一阶段 D = a × Bernoulli(0.15) 且 a = Δ/(λ₁ × 0.15)，第二阶段 D ~ Normal(mean=0, sd=0.001)，Δ ∈ {±0.02, ±0.03}。验收统计量：每个验收场景以 10⁶ 次重复只计算分层 t 区间（退化重复按"不判等价、覆盖为真"计；同一次重复中包络判等价蕴含 t 判等价、包络包含 t 区间，所以 t 单独的判等价概率与覆盖率是包络的保守界，允许相等；有限次估计仍有 Monte Carlo 误差，报告其标准误，不因独立的 10,000 次包络估计略高于 t 估计而判代码错误），t 单独的覆盖率 ≥ 93%，Δ 为 ±0.02 与 ±0.03 时 t 单独的判等价比例 ≤ 3.0%；A4 须 100% 退化、0% 判等价。包络（两种区间）另以 10,000 次重复照常报告，不作为验收统计量。报告场景（只报告、不验收）：B1 平移 lognormal，σ_log ∈ {0.17, 0.32, 0.75}（偏度约 0.5、1.0、3.3），长尾分别朝 +ε 与 −ε，平移使均值为 Δ ∈ {±0.02}，尺度使标准误与 ε 之比为 0.1；B2 D = 0.99 × Bernoulli(1/33) + 0.001 × Rademacher；B3 D = 0.2 × Bernoulli(0.15) + Normal(mean=0, sd=0.001)；B2、B3 用单阶段 15 与登记的阶段结构。每个场景输出参数、真实均值与方差、实际标准误与 ε 之比、覆盖率、判等价比例、退化比例与 Monte Carlo 标准误。全部验收场景完整执行并通过时开关为 true，任一统计验收不达标时为 false，由脚本写出；执行异常、缺行、参数或种子与登记清单不符属于执行失败，由脚本自动判定，修正实现并提交新的代码 SHA 后按同一清单与种子重跑，不触发回退；完整运行的结果保存并推送，之后因统计实现错误重跑时，开关取全部完整运行结果的合取；模拟与正式分析共用同一实现模块，SHA 不一致时拒绝写出开关值。夹具：第一次完整运行为 false、修正后为 true（开关为 false，两次都披露）；运行缺行（执行失败，可重跑，不计入合取）；清单生成器在 A2 × 方差比 16 上不产生行，人为加入时运行前报错；A5 核对 λ₁ × a × 0.15 = Δ。报告场景的结果写入修订 3 的局限说明 | 待执行 |
| 10 | 统计与登记门禁夹具：配对 RUN 顺序不同而 ID 相同；单边缺失与转换失败；RUN 级无定义按缺失；多个采集段只贡献一个 RUN；第 5 个 RUN 已显示等价时脚本不输出判读；3 + 12 的阶段退化反例；半格反例（0.0130000005000000555 与 0.0130000004999999445 交替）及其负数版本（都判退化）；给同一组差值加共同常数后退化结果不变；[0, 1e-9]（以 double 比较，退化）、[0, nextafter(1e-9, 1)]（不退化）、略小于 1e-9（退化）；[0, 0, 1e-6]（不退化）；同一组份额按两种顺序求和得到的 M2 差（退化）；某阶段恒定非零、单阶段退化；两阶段时分层点估计等于普通均值；只有一个阶段时与普通配对实现一致；NaN 传播；包络与"双通过"的逻辑等价；每条等价结论带模型标识；`quality_equivalence_enabled=false` 时任何对象、任何敏感性分支都不输出等价；离群标记（标准误与 ε 之比为 0.25 的正态差值大多不标，14 个约为 0、1 个为 0.3 时标记）；旧 5 + 新 10 全部合法通过、旧 RUN 没有初始化收据、篡改槽位表、旧 RUN 冒充新 RUN、同一原件占两个槽位、第 16 个 RUN、槽位成功后再追加成功、人工改判、第 14 个槽位没有终态时请求判读、计算日志 SHA 链断开、未推送的收据（都被门禁拒绝）；未知原因的 perf 非零退出（`paused_stop`）、白名单故障且有正面证据（重采）、过热引起非零退出、stderr 丢失、只有传输中断（重传，不计尝试）、完整传输后 SHA 不一致；原因不明的暂停后有合法证据恢复（通过）、事件只有说明文字（拒绝）、空间证据的 `df` 记录正常（拒绝）、温度证据的时间戳不在失败前后 10 秒内（拒绝）、曾经空间不足但恢复时仍不足（拒绝）、曾经过热但恢复时仍不满足启动条件（拒绝）、未知退出附近有高温却没有关联的停止动作（不可恢复，进入"停止缺失"）、硬件事件错误与过热同时出现（进入"停止缺失"）、旧的人工停止命令被用于另一次尝试（拒绝）、失败处理器没有写出证据文件（拒绝恢复）、故障已消除且证据关联正确（恢复）、没有恢复事件直接追加成功收据（拒绝）、恢复事件改变采集条件（拒绝，属于协议变更）、第四次尝试停止后申请恢复（拒绝）、`stopped_missing` 后再次采集（拒绝）、硬件事件错误停止（未完成槽位进入"停止缺失"）、遥测异常或转换失败进入恢复路径（拒绝）；登记前对真实 profile 请求 M3 或分支误差（拒绝）、登记后计算 M3 没有写日志（拒绝）；固定间隔的层不产生权重比较；合成 profile 允许计算 | 待实现 |
| 11 | 性能矩阵：从登记矩阵自动校验每组参数；缺少补零对照时拒绝输出"补零默认值已验证"；质量与性能的统计量、ε、停止规则没有混用，关闭质量判读不改变性能规则；超过登记的 N 后拒绝计入新轮次；N 的公式夹具：CV 0.5% 得 13，1% 得 40，CV 为 0 得 10，CV 缺失或为 NaN、无穷时视为无法预试得 40，预试含一个离群轮次时按未剔除的 CV 计算；G0 预试数据不进入正式轮次 | 待实现 |
| 12 | 板上（需要板子，加装散热后）：root 读取 `cpuinfo_cur_freq` 可用；记录器以 `O_RDONLY \| O_NONBLOCK` 打开并 `lseek(fd, 0, SEEK_SET)` 后读到首条序号 0，无新记录时立即返回；记录开机到会话开始的时长、`CONFIG_LOG_BUF_SHIFT` 与按当时的日志速率估计的回卷时间，会话期间序号连续；端点读取接口在"两次都没有新记录"与"后台已保存窗口内记录"两种情况下给出正确窗口；日志回卷的两条路径分别验收——首条序号 0 且连续时验证完整日志路径，首条不为 0 时默认阻止采集，只有采集前已有接受 unknown 的事件才继续，该路径不记为完整日志路径通过；加装散热后的正对照只有在全部必需观测完整时才预期合格，经批准的日志不完整路径预期为 unknown；完整执行一次前后校准流程（30 秒、每个 CPU 计数有效的中间区间 ≥ 25、采样器并行时的行为）；"解码满载 + 采样器"试运行，负载期间 ≥ 99% 的读数间隔不超过 1.5 秒、没有超过 3 秒的间隔、采样器使解码耗时中位数的变化小于 0.5%；同一次试运行带采样器的 G0 耗时（至少 10 轮）用于计算 N；核对 5.9 第 5 条引用的内核函数与行号。板上不为测试而重启 | 待板上执行 |
| 13 | 覆盖参考：spike 上 lcov 的 `DA` 与 JSON 推得的行计数一致；按主文件代码区域推导的函数行范围与 lcov/JSON summary 交叉一致；主文件按 `findMainViewFileID` 的规则核对，返回空的记录单独报告，并在对应表中有明确的状态；宏区域按区域类型与 FileID 识别；副本合并夹具（3 个编译单元的同一 static inline 函数只执行 1 个、宏内部循环、同文件同时含普通函数与宏定义、同一模板文件被不同名字包含两次、两个不同的已执行函数在同一物理行）；`HasMultipleRegions` 从 segments 提取的结果与 Coverage API 一致 | 待核对 |
| 14 | 离线资格分类：执行 5.9 第 5 条列出的全部判定脚本夹具，含记录器状态（首条序号不为 0 时不开始采集、会话中 boot_id 改变而记录器没有重启、一个 RUN 的两个端点跨 boot、保存失败、输出路径不在 `/opt/afdo_agent/` 下、非阻塞描述符无新记录时及时返回；日志回卷后未授权时拒绝采集，采集前授权后允许但保持 unknown，采集后补授权不能追认，之后观测正常也不能清除 unknown）；boot_id 改变用离线模拟，不在板上重启；用第一轮与四核诊断的原件重放，重放标签不覆盖历史资格 | 待实现 |
| 15 | ③ 门槛：按新的源函数合并规则与 ③ 的分母，在 FFmpeg（Thumb、A32）与 spike 的参考上计算 ③、③′ 与按互斥原因集合分桶的损失分解（各桶之和等于 ΣR(C) − ΣR(U)）；任一对象 ③ 低于 50% 时不登记，50%–80% 时登记文本须含损失分解 | 待计算 |
| 16 | 跨侧对应表：只用 ELF、调试文件与参考数据生成，结论状态为封闭枚举，覆盖映射范围内每个 DWARF 函数（含内联抽象源），任一没有结论时登记准备失败。夹具：左花括号另起一行与签名跨 3 行的单候选函数（通过一致性检查，正常对应）；正确候选缺失、只剩一个同名错误候选，包括 Codex 编译验证过的条件编译反例（错误定义的行号全部落在候选范围内，但两侧定义声明位置不同，不建立对应）；行号集合为空（不通过）；函数自身在签名行上有一个行表行（通过）；行号落在另一个同名定义的函数体内（不通过）；裁决证据与所选编译变体不一致（拒绝登记）；名字规则：只有 `DW_AT_name`、只有 `DW_AT_MIPS_linkage_name`、名字只在 specification 或 abstract origin 上、同一 DIE 同时有两种 linkage name 属性且值不同（先取 MIPS）、当前 DIE 的标准 linkage name 与引用 DIE 的 MIPS linkage name 同时存在（与 `getSubroutineName(LinkageName)` 一致）；同一文件多个同名定义，包括条件编译导致声明行相同而函数体起点不同（判 `identity_ambiguous`）；`identity_ambiguous` 被内联进热点函数且有样本（RUN 有定义、相关行被排除）；GNU C 编译的 `libgcc2.c` 函数与 GNU AS 函数有样本（`not_instrumented`，归为范围外）；`not_instrumented` 外层含已执行参考函数的内联体（不得整组归为范围外）；只有约定的 `.__uniq.` 后缀有无不同、规范化后身份相同（正常对应）；修饰方式不同（`file.c:foo` 与 `_ZL3foov.__uniq.N`）或故意漏做后缀规范化（没有结论，登记准备失败）；完整身份清单独立于映射范围生成：范围外的顶层 static 函数名字去后缀后与覆盖侧不同、且没有被内联进任何范围内函数（登记准备失败），带 `.cold.1` 等后缀的克隆函数（登记准备失败或由裁决表给出结论），没有任何已匹配外层的未决函数、参考质量低于 1%（仍失败）；CU 文件名错误、producer 缺失或解析失败（没有结论）；外部 CU 中能对应已执行参考函数的内联体（不得归为未插桩）；clang C 编译单元中一个函数在覆盖导出中缺失（没有结论）；同一头文件在两个 CU 中的 decl_file 写法不同且只规范化了其中一种（登记准备失败）；内联帧对应到参考侧未执行的函数（计入"已对齐但不在 U 内（未执行）"）；列出名字去后缀后与已执行参考源函数相同、却不在映射范围内的全部 ELF 顶层函数并逐个裁决，裁决证据随表保存；报告 `not_instrumented` 的 CU 清单与 producer 分布 | 待生成 |
| 17 | 登记前打开过的真实 profile 清单与在其上计算过的量；G0 预试的条件、轮数、原始耗时与开销，写入修订 3 的披露 | 登记时执行 |
| 18 | 性能轮数 N：按第 12 项的 G0 预试与 5.9 第 5 条的公式确定每块板的 N；无法完成预试时取 40，写明来源 | 待确定 |
| 19 | 登记：①（协议与工作模型、脚本与共用的统计实现模块、依赖、配置、对象登记表、完整身份清单、外部 CU 清单、对应表与裁决表（含单候选的定义身份证据）、映射表、地址关系表、排除清单、边界排除组、U、权重、受控量清单、重采原因码白名单与证据条件、停止与恢复事件及证据记录的格式）、②（已存在输入清单）、③（完整 RUN 槽位表与既有 RUN 的初始化收据）的 SHA-256 写入修订 3，连同第 9 项的场景清单、种子、全部完整运行的代码 SHA 与结果，以及 `quality_equivalence_enabled` 的取值；修订 3 提交与推送成功的记录在正式受控量计算之前保存 | 登记时执行 |

### N.6 本版新写、尚未经评审的内容

无。本版的全部修改都采用了评审方给出的方案或其合并；合并时的取舍写在 N.2、N.3 的"采用与理由"一栏。

## 附录 O：登记前准备中的裁决（v1.5 → v1.6）

v1.5 按约定不再评审，直接进入附录 N.5 的登记前准备。准备中，执行方（Codex）在静态产物上发现 5.8 第 5 条有几处无法按原文闭合，或者闭合后对象不可用：被采样 ELF 中有一类函数没有可用的结论状态；宏生成的函数需要编译器级的身份证据；按原定义 FFmpeg 的 ③ 只有约 20%，低于 50% 的门槛；`identity_ambiguous` 与 `unmatched_in_elf` 超过 1%。按 5.8 第 5 条"③ 低于 50% 时先修订本条"的约定，以及"任一函数没有结论时登记准备失败、不得自行扩大规则"的约定，每一处都先停下，由用户裁决后再继续。裁决共四项（O.2），本版把它们折入 5.8 第 5 条，同时澄清 ④ 的计算时点，并记录静态结果（O.3）。

本版不改补丁，不改第一阶段，不改已有 golden 值，也不改 5.8 第 6 条以后的统计与判读规则。全部裁决只使用 ELF、调试文件、编译命令、编译器 API 与参考数据，没有读取任何正式 sample profile，也没有计算任何受控量。裁决是在看到参考侧静态结果后作出的修订，所以本版送三家限定范围评审；评审通过后才登记修订 3。O.6 列出全部未经评审的内容。

### O.1 发现与处理顺序

| 顺序 | 发现 | 处理 | 证据 |
|---|---|---|---|
| 1 | 被采样 ELF 中有来自系统头的函数（如 `string_fortified.h` 的 `memcpy`），有代码与 DWARF，但参考侧没有候选：clang 生成覆盖映射时默认跳过系统头（`clang/lib/CodeGen/CoverageMappingGen.cpp:49–52`、`:1575–1579`）。v1.5 的结论枚举里没有对应状态 | 裁决 1 | `docs/profgen/eval/prep/03_system_header_ruling.md` |
| 2 | FFmpeg 中整个函数由宏展开生成（如 `pixels.h` 的宏在 `hpeldsp_init_arm.c:38` 生成 `ff_put_pixels16_x2_arm`）：两侧声明位置在宏调用处，覆盖区域全部在宏定义文件。身份可以证明，但需要编译器级证据；其中 28 个函数的被调函数名由 `##` 拼接产生，拼写位置在 scratch buffer | 裁决 2 及补充 1–3、补充 3 修订 1 | `04_macro_function_ruling.md` 第 7–8 节 |
| 3 | 按 v1.5 原定义，FFmpeg 的 ③ 约 20%。无键行损失中，`libavcodec/arm/cabac.h` 一个文件就占 ③ 分母的 51.5%：`get_cabac_inline` 的内联汇编跨 70 行，覆盖导出给其中 58 行同一个计数 255523038，而指令只记在第 36、104 行（这两行在 U 内） | 裁决 3 及修订 1 | `05_identity_gate_and_coverage.md` 第 7、10–12 节 |
| 4 | `identity_ambiguous` 约 5.6%、`unmatched_in_elf` 约 2.3%，几乎全部来自"叶子行集合为空"：例如 `fill_rectangle` 有 121 个内联实例，120 个通过，1 个没有自身叶子行，整组被判歧义；`get_cabac` 的代码全在下一层内联函数里，104 个实例都没有自身叶子行 | 裁决 4 及修订 1、2 | 同上，第 6、10 节 |
| 5 | v1.5 把 ④ 的条目分类比例与 ①–③′ 写在同一项里，但它的分母是每个 RUN 的 profile body 计数，登记前不能计算 | 澄清（5.8 第 5 条） | 同上，第 8 节 |

### O.2 裁决全文（规范性）

v1.7 按附录 P 修订了 O.2.1 第 2、3 项、O.2.2 第 2、3 项、O.2.3 全文与 O.2.4 第 3 项；v1.8 按附录 Q 修订了 O.2.3。本节是四项裁决的最终合并文本，取代 `docs/profgen/eval/prep/rulings.md` 中的逐次修订记录（后者保留历史）。5.8 第 5 条引用本节；两者不一致时以 5.8 第 5 条为准，并视为本文的缺陷。每项裁决的任一正面证据缺失时，该函数保留为没有结论，按 5.8 第 5 条"任一函数没有结论时登记准备失败"处理；FNDA 不得替代任何一项身份证据。

#### O.2.1 裁决 1：`system_header_no_reference`

1. 适用条件（同时满足）：
   - ① 该函数规范化后的 decl_file 位于该 CU 编译时的系统头目录之下。系统头目录取自 C 构建与 S 构建的实际编译命令（`-isystem`、`--sysroot` 与该 clang 的默认系统头目录，用同一 clang 的 `-v` 输出核对），两侧须一致。
   - ② C 构建的编译命令没有打开系统头覆盖（没有 `-mllvm -system-headers-coverage` 或等价选项），并给出 LLVM 22.1.8 中跳过系统头的代码位置。
   - ③ 覆盖导出的文件表中没有任何位于这些系统头目录之下的文件（全局核对；一旦出现，本规则不适用，停止并报告）。
   - ④ 该函数没有任何参考候选；有候选的一律走原来的对应规则。
2. 处理：键照常进入映射表，值记为 `system_header_no_reference`。条目先按 5.8 第 5 条的顶层组分类顺序处理（范围外的组见本项末句）；位于映射范围内、命中已登记键且值为本状态的条目计入"已对齐但不在 U 内"，单列原因"系统头"，不算未对齐。本状态的参考行不进入 U，也不进入 ③ 的分母 C。内联树中只含 `system_header_no_reference`、`not_instrumented` 与参考侧未执行函数的顶层组，归为 `known_out_of_scope`；含已执行参考函数的组仍在映射范围内。
3. 局限：内联进用户函数的系统头代码不参与行级指标。修订 3 登记映射范围内系统头代码的静态地址数与字节数。系统头代码没有参考计数，其动态份额不能由参考侧账本量化，只能由登记后 RUN 级的条目分类给出。

#### O.2.2 裁决 2：`macro_generated_function`（宏生成的函数）

1. 建立对应须同时满足：
   - ① 名字精确一致。内部链接函数的覆盖 PGO 名字形如 `<TU 前缀>:<linkage name>`。linkage name 连同 `.__uniq.` 后缀必须与 DWARF 侧完全相同，这里不去后缀。TU 前缀须对应该 DWARF 函数所在 CU 的源文件，规则如下：
     - 前缀只有 basename 时，先在 LLVM 22.1.8 源码中给出 PGO 名字前缀的生成位置，并用 C 构建的实际编译命令说明为什么是 basename；源码与命令解释不了时停止。
     - 解释成立后，用实际编译命令建立"前缀 → 完整 CU 源文件路径"映射：前缀须等于某条编译命令的源文件 basename，且该产物被链接进被采样的库。
     - 同一 basename 对应多个 CU 时，只有恰好一个 CU 的 DWARF 中存在完整 linkage name 相同的定义才算唯一，否则保留未决。
     - 外部链接函数（没有 TU 前缀与后缀）要求 linkage name 完全相同，且在覆盖记录与被采样 ELF 的 DWARF 顶层定义中都唯一。
   - ② 定义声明位置一致：C 构建 DWARF 中的 decl_file 与 decl_line 与被采样侧完全相同。
   - ③ 宏生成的证据：该覆盖记录在 decl_file 中没有任何代码区域，全部代码区域在另一个文件（覆盖主文件）中；并由编译器证据证明函数体来自 decl_file 的 decl_line 处那一次宏调用（见第 2 项）。
   - ④ 该函数不满足 5.8 第 5 条原规则下的普通对应。
2. 宏生成的证据（用 C 构建该 CU 的实际编译命令与 GBS root 中的 clang 取得；只靠文本搜索、正则或宏名推断的证据不算）：
   - 展开链：导出函数声明的 AST 与 token 位置。链上每一层宏的名字与定义位置（文件与行号）由 `MacroExpands` 回调与 `MacroInfo` 给出，展开链可以有多层（例如 `DEF_PEL`/`PIXOP2` → `CALL_2X_PIXELS` → `pixels.h`）。
   - 逐 token 判定（函数体全部 token）：
     - 非实参 token（语句结构、关键字、运算符、标点等由宏定义体提供的部分）的拼写位置必须全部在覆盖主文件中。有非实参 token 拼写在 decl_file 中时，本裁决不适用，走原规则。
     - 拼写位置不在覆盖主文件中的 token，必须被 clang 标为宏实参展开（`SourceManager::isMacroArgExpansion` 为真）；其拼写位置只能落在 decl_file 的 decl_line 处那次宏调用的实参范围内，或者落在已记录展开链上某一层宏的定义体内（中间宏把实参传给下一层宏的情形）。落在别处或标志缺失时保留未决。
   - `##` 拼接产生的 token：拼写位置在 scratch buffer 中的 token，单独按下面的规则证明其来源。规则的前提是 clang 22.1.8 `TokenLexer::pasteTokens` 为拼接结果创建的 expansion range 覆盖从首操作数到末操作数起点的 `##` 表达式（`clang/lib/Lex/TokenLexer.cpp:749`、`:895`、`:903–914`，执行方已核对）。逐 token 满足以下各条，任一不满足判未决，原因码写到具体条目：
     - 唯一拼接层：在该 token 的位置链中，恰好有一层的直接拼写位置是 scratch 的 FileID 位置。
     - 拼接范围：对这一层取 `getImmediateExpansionRange` 得 [B, E]。B 与 E 都是宏位置，属于同一个宏展开实例 X；X 与插件记录的 `MacroExpands` 回调一一对应（宏名与展开位置的 raw 值都相同），并位于该函数已记录的展开链上。B、E 的拼写位置都在 X 的 `MacroInfo` 定义范围内。
     - 拼接结构：从 X 的 `MacroInfo::tokens()` 中按位置取出 [B, E] 覆盖的定义 token，必须严格是"操作数 (`##` 操作数)+"。出现字符串化 `#`、GNU 逗号拼接 `, ## __VA_ARGS__` 或 MSVCCompat 时判未决。
     - 操作数解析：形参操作数（`MacroInfo::getParameterNum`）取 X 的 `MacroArgs` 对应槽位的未展开实参。实参在回调时复制，含 SourceLocation，须恰好 1 个 token；空实参或多 token 判未决。非形参操作数就是定义体 token。
     - 文本一致：各操作数的 `Preprocessor::getSpelling` 依次拼接后，与该 token 的文本逐字节相同；该 token 与各中间结果的 kind 只能是 identifier 或 numeric_constant。
     - 操作数来源，先按操作数在拼接片段中的角色区分：
       - 非形参操作数：必须是唯一实例 X 的 `MacroInfo` 定义片段中的原始 token，拼写位置在该定义范围内；证明路径记为 `definition_body`，不要求 `MacroArgs` 槽位，也不要求 `isMacroArgExpansion` 为真。同文本、但来自另一宏定义的 token 不满足本条。
       - 形参操作数：取出未展开实参后，再按该 token 自身的 SourceLocation 分三种情况：
         - 宏位置：用该 token 自己的位置链按上面的逐 token 规则判定。
         - 非 scratch 的物理文件位置，即直接写在调用处的实参。它在 clang 中不是宏位置，`isMacroArgExpansion` 恒为 false（`clang/lib/Basic/SourceManager.cpp:984–986`）。改用"直接调用实参"证明，同时满足：取自唯一实例 X 的 `MacroArgs` 槽位 n，该槽位恰好这 1 个 token；X 是已记录的调用实例；token 的拼写区间完整落在 X 这次调用第 n 个实参自己的区间内（按槽位切分，不含括号与分隔逗号）；与 X 调用的名字位置在同一个 FileID 中。证据如实记录 `isMacroArgExpansion=false`，证明路径记为 `direct_unexpanded_argument_slot`。
         - scratch 位置：递归应用本规则，深度上限 8。
3. 处理：身份对应成立。执行与否按该覆盖记录的 FNDA；进入映射范围判断时与普通对应相同（FNDA > 0 视为已执行参考函数）。该函数的参考行不进入 U；是否属于 C 只按 O.2.3 第 1 项的见证规则判定，不使用本裁决的结论（宏展开的代码在行表中记在调用处，宏定义文件中的行通常没有见证），属于 C 时在 C → U 账本中计为损失；其 `DA` 计入 ③′ 的宏展开部分。条目先按 5.8 第 5 条的顶层组分类顺序处理：只含 FNDA = 0 的宏生成函数及其他范围外结论的组记为范围外；位于映射范围内、命中已登记键且值为本状态的条目计入"已对齐但不在 U 内"，单列原因"宏生成的函数"，不算未对齐。宏生成函数被执行时，其行在两份账本中都带原因 `macro_generated_function`；没有见证的行同时带 `code_free_line`，按完整原因集合分桶、不重复计数。
4. 登记前报告：闭合的函数清单、每个函数的宏名与两处源码行、FNDA、其中 FNDA > 0 的函数的 `DA` 之和（评价域外的执行量）；每个闭合函数保存逐 token 清单、调用实参范围、展开链各层定义位置、拼接证明（含递归子证明）以及原始 AST/token 输出与 SHA。

#### O.2.3 裁决 3：③ 的行集合 C 限定为有行表归属见证的行

（v1.7 按附录 P.2 第 2–4 行修订：取消函数过滤，按 LLVM 行表查询语义取见证，理由分为两部分，增加 C_dc 口径并冻结 C 的定义。v1.8 按附录 Q 修订：见证改称操作性定义并加 sequence 不重叠的前提与登记前报告，`domain_unresolved` 阻止登记，`inlined_call_site` 的归属写死，增加第 7 项结论输出门禁。）

1. 记 v1.5 原定义的行集合为 C₀。C₀ 中的某一行进入 C，当且仅当在 C 构建调试 ELF 或 S 构建调试 ELF 中，存在该行的行表归属见证：
   - 逐 sequence 取有效行表区间：同一 sequence 内，一条记录的区间为 [本记录地址, 下一条记录地址)；同一地址有多条记录时只取最后一条（与 LLVM 22.1.8 `findRowInSeq` 一致，`llvm/lib/DebugInfo/DWARF/DWARFDebugLine.cpp:1297`、`:1311`）；去掉 `end_sequence`、零长度区间与被同地址后续记录覆盖的记录。
   - 该区间的行号非 0，文件与行号即为该行（行表给出的就是叶子位置），区间与 ELF 中带执行属性的节相交且非空。
   - 不限定该区间属于哪个函数，也不要求它是已证明的指令起点或能生成被接受的键。非叶子帧行号为 0 只影响键，不删除这里的叶子见证。
   - 前提：逐 sequence 取区间再合并，只有在同一 CU、同一节的 sequence 在可执行节交集内互不重叠时，才与 LLVM 先选 sequence 再查行的语义一致（LLVM 说明共享库、可执行文件与 ICF 下可能出现重叠 sequence，`DWARFDebugLine.cpp:1274`，选择逻辑见 `:1335–1351`）。提取时保存每条 sequence 的 CU、SectionIndex 与地址范围；生成 C 前自动验证这一前提，不满足时判为静态取证失败（第 3 项），不得直接合并重叠 sequence 的行。今后若要支持重叠输入，须复现 LLVM 22.1.8 的 sequence 选择与 `findRowInSeq` 语义，并作为规则变更送评审。
   - 登记前报告：与可执行节只部分相交的区间个数；起始地址低于最低可执行节起点的 sequence 个数。两者不为 0 时逐项列出。
   - 这是操作性定义："可执行节内的有效行表区间"不等于逐行证明存在真实指令起点，可执行节中的 literal pool、填充等数据也可能被保留。C 因此是候选评价域；U 仍须满足独立的有效键与身份条件，进入 C 而不在 U 内的行照常计损失，不因推测为数据而删除。本方案不声称已排除可执行节中的全部非代码数据。
2. C 的生成只使用两份调试 ELF 与 C₀。不得使用对应表、映射范围、映射表、边界排除结果、键是否被接受或任何身份结论；`selected-groups` 等由跨侧身份结论派生的选择清单不得作为输入。映射范围与 C 的取证输入分别登记 SHA。保持 C₀ 与两份 ELF 不变、只改变对应表结论、键接受状态或映射范围时，C 的 SHA 必须不变。
3. 归类：
   - C 不因裁决 2 的结论增减：宏生成函数的行与其他行一样只按第 1 项判定；它们不进入 U（裁决 2），在两份账本中带原因 `macro_generated_function`（附录 P.4 第 7 条）；
   - 行表无法解析、取证失败的行记为 `domain_unresolved`：留在 C 中，明确排除出 U，在两份账本中单列，并报告行数与 `DA`，不得解释为 `code_free_line`。失败不能定位到具体行时（包括取证程序退出码非 0、有诊断输出，或第 1 项的 sequence 前提不成立），全部未取得见证的 C₀ 行都记为 `domain_unresolved`。这样处理只是为了把未解决的部分保存在账本里，并不保证准入判定保守：这些行同时加大 ③ 与三个 1% 门槛的分母，可能让本不合格的对象显得合格。因此，任一对象存在 `domain_unresolved` 行（不论其 `DA` 是否为 0）时，该对象状态为 `domain_evidence_incomplete`，不得判为可登记，也不得输出质量结论；只能修复静态取证、重新生成并核验相关产物后，再做准入判定；
   - C₀ 中其余没有见证的行记为 `code_free_line`，不进入 ③ 的分母，也不进入三个 1% 门槛的分母，逐行与按文件报告。
   - U ⊆ C 不变；有见证、但 S 中没有被接受的键的行，照常计为 `no_key_line` 等损失。①、③ 与三个 1% 门槛的分母使用 C；②、③′ 的分母不变。
4. 理由分两部分，登记文本分别写明：
   - (i) 结构性重复计数的修正。覆盖导出给区域跨越的每一行都记计数，内联汇编字符串的各行、只有花括号或 `else` 的结构行、多行表达式的续行，与有见证的那一行是同一次执行，计入分母会重复计算。这与 v1.5 把宏定义行排除在 C 之外的理由相同。对应下文第 5 项的 `asm_interior`、`structural_line`、`expr_continuation` 三类。
   - (ii) 可测量性的限定。有自己的语句或声明、但在两个固定构建中都没有行表归属见证的行，叶子帧采样在构造上不可能计到它们，任何配置在这些行上都恒为 0；它们不是重复计数。对应第 5 项的 `inlined_call_site`、`own_stmt_no_code` 与 `other`。这是评价范围的实质收窄：行级结论只覆盖在固定构建中满足本条见证规则的行。
   - 取两个构建的并集，比只用一个构建更保守：S 有见证而没对上的行算损失，C 有见证而 S 没有的行也算损失。
5. 必须报告的描述量（不设门槛）：
   - C_dc = C₀ 去掉 `asm_interior`、`structural_line`、`expr_continuation` 三类的行集合（只做第 4 项 (i) 的修正）；C ⊆ C_dc ⊆ C₀。
   - 按 C₀、C_dc、C 三个口径的 ③（分子都是 ΣR(U)）；代码承载比例 ΣR(C) ÷ ΣR(C₀)；评价域外的不重复参考执行量比例 ΣR(C_dc \ C) ÷ ΣR(C_dc)。报告分子分母原值，写入对象登记表与修订 3 的局限说明。这些都是参考行计数质量的比例，不是运行时间或独立执行事件的比例。
   - `code_free_line` 的结构分类：用 C 构建的实际编译命令取得 AST 与 Clang Lexer 的 raw token，每行只归一类，按以下顺序判定：
     - `asm_interior`：位于 `GCCAsmStmt` 范围内、且不是该语句中有见证的行；
     - `structural_line`：该行全部 token 只有 `{ } ;`、`else`、`do`、case/default 标号与普通标号；
     - `expr_continuation`：该行没有任何非 `CompoundStmt` 的 Stmt/Expr/Decl 开始，位于某个跨多行、非 `CompoundStmt` 节点的范围内（if/for/while/switch/do 的整体范围不算），而该节点的起始行属于 C；
     - `inlined_call_site`：该行出现在任一构建的 `DW_AT_call_file`/`DW_AT_call_line` 中（代码归属到被调函数的行上）；
     - `own_stmt_no_code`：该行有自己的语句或声明开始，但未取得行表归属见证。原因可能是优化合并或消除、归属到邻行或行号 0，本分类不据此断言具体原因；按语句种类汇总；
     - `other`：逐行写明原因；
     - `ast_unavailable`：取不到证据的行，不得并入其他类。
   - `inlined_call_site` 固定归入第 4 项 (ii) 可测量性一侧，不计入 C_dc 的修正（保守取法），不随评审或结果改变；它的行数与 `DA` 另行报告。调用行的计数带有被调函数计数的成分，若把它移到 (i) 一侧，FFmpeg 的 C_dc 口径 ③ 会从约 49.9% 变成约 50.7%，恰好跨过 50%；写死归属是为了避免以后因"纠正"分类而误读。
   - 以上只说明本次固定构建中这些行没有见证，不推断其他构建也没有指令。
6. 冻结：C 的定义随修订 3 冻结，不因 RUN、配置、门槛或结果修改。改变构建须重新生成并登记评价域；任何规则修改都作为新的修订送评审，并对全部对象统一适用。
7. 结论输出门禁（5.8 第 6 条的评价域说明）：写出任何有定义的质量结论之前，在打开输出文件之前完成以下校验，任一不通过即拒绝写出，不创建文件，也不覆盖已有文件：
   - 评价域说明原文存在，并含"只覆盖固定构建中满足登记的行表归属见证规则的行；该规则不等同于逐行证明存在真实指令"的限定；
   - 三个口径的 ③ 各自给出分子、分母与比值：分子、分母为非负整数，分母大于 0，比值有限，且等于分子 ÷ 分母；三个分子相同；ΣR(C) ≤ ΣR(C_dc) ≤ ΣR(C₀)；
   - 三口径 ③、③′、代码承载比例、评价域外的不重复执行量比例，与修订 3 登记的对象登记表逐项相等。登记表按登记的 SHA 读取，SHA 不符即拒绝；不得混用其他对象的数值；
   - 对象状态不是 `domain_evidence_incomplete`；
   - null、空对象、NaN、Infinity 一律拒绝；JSON 序列化禁止非有限数。
   分母为 0 等无定义情况只允许写出明确标记为诊断的报告，不得写出有定义的质量结论或"可登记"状态。

#### O.2.4 裁决 4：单候选检查第 ② 项的行集合与无键实例

1. 实例范围：仍为完整身份清单，即有地址区间的 DIE。无代码的定义 DIE（含 `DW_AT_inline` 抽象源）不加入组判定：inlined_subroutine 实例的名字与声明位置本来经 abstract_origin 链取自抽象源，第 ① 项对实例的检查已覆盖抽象源的声明位置；没有具体实例的抽象源不产生任何键。证据列出每个实例声明位置的取值路径。
2. 第 ② 项的行集合 = 该实例以自身为叶子帧、文件等于 decl_file、行号非 0 的行表行号，并上其直接子 inlined_subroutine（含位于 lexical block 之下者）中，`DW_AT_call_file` 等于 decl_file、行号非 0 的 `DW_AT_call_line`。范围仍为 [min(decl_line, 候选起始行), 候选结束行]。
3. 无键实例：对完整身份清单的全部顶层函数（不限于映射范围），在全部已证明的指令起点上运行与正式工具相同的键生成代码（叶子帧或任一非叶子帧行号为 0 时拒绝该键）；枚举与符号化全部成功、且没有任何一个被接受的键以该实例为叶子帧或上下文帧时，该实例为无键实例。所在顶层函数边界无法证明、枚举不完整、符号化失败或缺少该实例的键证明记录时，都不是无键证明，不得以默认计数 0 获得豁免，按有键实例检查。无键实例同时满足以下三条时豁免，即不参与组判定、单独计数报告；任一不满足判失败：
   - 第 ① 项通过；
   - 第 2 项的行集合中没有越界的行（集合为空时视为满足）；
   - 自身没有落在其他文件、行号非 0 的叶子行。
4. 有键实例：第 2 项的行集合非空且全部在范围内时通过。以下情形判失败：行集合为空（例如调用行只在其他文件）；有越界的行；自身的非 0 叶子行全部落在其他文件。部分叶子行在其他文件时，与 v1.5 相同，只检查 decl_file 中的行。
5. 组判定：第 ① 项对全部实例检查。排除豁免的无键实例后，至少一个实例第 ② 项通过、且没有实例失败时，本组建立对应；否则按多候选的规则处理（显式裁决，或记 `identity_ambiguous`）。组内全部是豁免的无键实例时，本组不产生键：其参考行记为 `no_key_line`，已执行参考源函数记为"已对应但无键"，不计入 `unmatched_in_elf`。
6. 理由：没有键的实例不可能让样本归属出错，它造成的身份风险只能来自现有行号证据，所以豁免以"现有行号证据不指向错误定义"为条件。v1.5 的"行号集合为空时 ② 不算通过"对普通有键实例保留；无键实例改按本裁决处理。

### O.3 登记前静态结果（参考数据与 ELF，未读取任何 sample profile）

v1.7 注：以下是 v1.6 规则下的数值。本版改变了 C 的定义（附录 P.2），第 3、4 项须按本版规则重算，第 1、2 项不受影响。

以下数值取自执行方的报告与证据（`docs/profgen/eval/prep/05_identity_gate_and_coverage.md` 第 5–12 节，提交 `a8aae98`、`cb2da1b`、`4459894`、`08bf2ed`）。修订 3 登记时以重新生成并登记 SHA 的产物为准。

1. 编译参数（S 与 C 相同，最后一个优化选项生效）：spike 为 `-Os`；FFmpeg 为 `-Os -O3`，即 -O3；两者都有 `-g2 -gdwarf-4`、`-fdebug-info-for-profiling`、`-funique-internal-linkage-names`；C 构建另有 `-fprofile-instr-generate -fcoverage-mapping`。
2. 身份闭合：完整身份清单 spike 每侧 17 项，FFmpeg Thumb 28149 项、A32 28190 项，全部有封闭结论，未决为 0。

| 对象 | 裁决 1 | 裁决 2 | `not_instrumented`（libgcc） | 普通候选 |
|---|---:|---:|---:|---:|
| spike Thumb / A32 | 2 / 2 | 0 / 0 | 0 / 0 | 15 / 15 |
| FFmpeg Thumb / A32 | 1236 / 1242 | 34 / 34 | 38 / 38 | 26841 / 26876 |

   裁决 2 的 34 个函数全部 FNDA = 0，结论为参考侧未执行，映射范围内的宏生成代码规模为 0。

3. 对象登记表（裁决 3 修订 1 与裁决 4 修订 2 之后；v1.5 原定义一并列出，身份规则相同）：

| 对象 | C 规则 | C 行 | ΣR(C) | U 行 | ③ | ③′ | n_eff | K |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| spike Thumb | v1.5 原定义 | 122 | 21362787097 | 73 | 54.643726% | 53.354972% | 1.328515 | 19 |
| spike Thumb | 本版 | 75 | 11674422883 | 73 | 99.991434% | 53.354972% | 1.328515 | 19 |
| spike A32 | v1.5 原定义 | 122 | 21362787097 | 72 | 54.044553% | 52.769930% | 1.299623 | 10 |
| spike A32 | 本版 | 74 | 11546422883 | 72 | 99.991339% | 52.769930% | 1.299623 | 10 |
| FFmpeg Thumb | v1.5 原定义 | 13040 | 28769855208 | 6810 | 20.406034% | 17.232788% | 22.607016 | 465 |
| FFmpeg Thumb | 本版 | 7637 | 6890196397 | 6810 | 85.204920% | 17.232788% | 22.607016 | 465 |
| FFmpeg A32 | v1.5 原定义 | 13040 | 28769855208 | 6828 | 20.357980% | 17.192207% | 22.643693 | 464 |
| FFmpeg A32 | 本版 | 7656 | 6889424103 | 6828 | 85.013804% | 17.192207% | 22.643693 | 464 |

   - 本版规则下三个 1% 门槛：spike 全部为 0；FFmpeg 两侧 `identity_ambiguous` 为 15555（0.000226%），`unmatched_in_elf` 为 26367（0.000383%），`boundary_unavailable` 为 0。四个对象的 ③ 都 ≥ 80%。
   - spike 两侧 K < 50，只作描述。
   - 裁决 4 之前，FFmpeg Thumb 的 `identity_ambiguous` 为 5.580146%，`unmatched_in_elf` 为 2.284188%（v1.5 原定义 C 下）。
   - 损失账本（C → U 与 C₀ → U 两份）在四个对象上差值都为 0。

4. 代码承载比例与 `code_free_line` 结构分类（单元格为"行数 / DA"）：

| 项目 | spike Thumb | spike A32 | FFmpeg Thumb | FFmpeg A32 |
|---|---:|---:|---:|---:|
| 代码承载比例 | 54.648407% | 54.049234% | 23.949361% | 23.946676% |
| `asm_interior` | 0 / 0 | 0 / 0 | 68 / 14050578484 | 68 / 14050578484 |
| `structural_line` | 28 / 5238745153 | 28 / 5238745153 | 2105 / 2967361906 | 2100 / 2977361898 |
| `expr_continuation` | 0 / 0 | 0 / 0 | 25 / 1799 | 25 / 1799 |
| `own_stmt_no_code` | 19 / 4449619061 | 20 / 4577619061 | 3056 / 4668195093 | 3042 / 4658967395 |
| `other` | 0 / 0 | 0 / 0 | 149 / 193521529 | 149 / 193521529 |
| `ast_unavailable` | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

   按 C₀ 的参考计数，FFmpeg 约 16% 落在"有自己的语句、但在 -O3 构建中没有指令"的行上，spike 约 21%。代码承载比例偏低，主要来自内联汇编各行的重复计数（FFmpeg 约 49%）与结构行。这些数值说明：本方案的行级结论只覆盖在优化构建中带指令的行，被优化合并或消除的语句不在评价范围内。

### O.4 对前一版的更正

1. 5.8 第 5 条第 ③ 项把 C 定义为"已执行源函数行范围内的全部可执行行"，但覆盖导出的"可执行行"包含不可能带指令的行（续行、内联汇编各行、结构行），会重复计数并压低 ③。由裁决 3 更正。
2. 5.8 第 5 条"筛选后的行号集合为空时 ② 不算通过"对没有自身叶子行、代码全在下一层内联函数中的实例过严，一个这样的实例就会让整组判为歧义。由裁决 4 更正，普通有键实例的规则保留。
3. 5.8 第 5 条第 ④ 项与 ①–③′ 写在一起，容易被理解为登记前要计算。条目分类比例的分母是每个 RUN 的 profile body 计数，登记前不计算；登记前只计算其中的静态部分。
4. v1.5 的结论状态枚举缺少系统头函数与宏生成函数的状态，由裁决 1、2 补充。
5. 文首"v1.4 评审没有严重问题，本版不再评审"的约定只适用于 v1.5；本版含有看到静态结果后作出的规则修订，送评审。
6. N.5 由 O.5 取代。

### O.5 执行前须核对的事项（取代 N.5）

v1.7 起本节由附录 P.5 取代，以下保留 v1.6 原文。

登记修订 3 之前由执行方完成。除第 9 项按预先登记的规则回退外，结果与本文不符时先修订本文，再登记。只有第 12 项需要板子；第 21 项是登记的前提；全部事项都不对正式 sample profile 计算任何受控量。

| 编号 | 事项 | 状态 |
|---|---|---|
| 1 | G.1.1 的前驱条件与原因分类与补丁 5 一致 | 已核对 |
| 2 | G.1.7：报告提交成功的用例断言 `tool.arguments` 记录了注入选项；报告自身写入或提交失败的用例，用测试执行器保存的 argv、stderr、退出码与文件状态核对；未执行到注入点的用例单列；评估准入对 `@rsp`、单横线、双横线、`=值`、分离值写法都拒绝 | 部分核对；测试待补 |
| 3 | G.1.8：三项派生负对照按既有 `avg` 命令重跑，仍在 boundary 阶段失败，逐项保存命令与原因 | 查找方式已核对；负对照待重跑 |
| 4 | G.1.3 第 4 条与 G.1.10 第 2 条与补丁 6 的实现与测试一致；写 profile 的符号化路径不做 canonical 化（`L/ProfiledBinary.h:620`、`L/ProfiledBinary.cpp:1212`、`:1297–1298`），`--show-canonical-fname` 只影响反汇编显示并在 IP 模式下被拒绝（`llvm-profgen.cpp:249`） | 源码已核对；测试待重跑 |
| 5 | 映射表与条目分类：① 合成全地址核对——为映射范围内边界可证明的每个指令起点构造一条合成样本，用正式工具以 skid=`none` 与 `prev-inst`、聚合方式 `max` 分别转换，写出的每个条目按 5.8 第 5 条分类，只允许映射表命中、`boundary_unavailable` 或 `known_out_of_scope`，出现 `unknown_name`、`reference_unresolved`、`unmapped_key` 即失败；② 用不共享映射表生成实现的第二条路径（`llvm-symbolizer` 逐地址符号化，加上独立的键计算）重算"地址 → 键 → 源位置"关系与排除结果，逐项比较；③ 边界排除组单独测试：`none` 转换把其条目归为 `boundary_unavailable`，`prev-inst`/`avg` 转换按冻结契约在 boundary 阶段失败；④ 在第一轮 CALIBRATION 运行的基准配置上做流程冒烟。夹具：映射表漏一个冷地址、删去一个碰撞地址后键集合不变、交换两个键的值、`prev-inst` 键算法错一位（都须被①或②发现）；同键不同源位置、同键同位置；两个命中函数集合不同的 RUN、删除热点函数全部条目、加显式零条目、改变预算（静态产物的 SHA 都不变）；原始 discriminator 不同而写出键相同、Thumb 别名、非叶子行号 0、偏移碰撞、不同构建路径、歧义键与正常键同时贡献同一行、名字闭包、评估侧错误地去掉 `.__uniq.` 后缀且 ELF 恰好有同名的范围外函数（期望无定义）、无法识别的函数名、一个计数很小的未对齐键（仍判无定义）、一个 `boundary_unavailable` 函数在 `none` 配置下有样本（单列，RUN 仍有定义）、同名组同时含可证明与不可证明的范围、被排除函数含热点内联体、FNDA 很小而循环行计数很大；顶层函数只含歧义候选（被枚举，命中的键计入"已对齐但不在 U 内"）、热点顶层函数同时含正常与歧义的内联体、在歧义组中注入不存在的键（仍判未对齐）、对应表中存在 `pending` 记录（登记准备失败）；补零 profile 不参与质量指标 | 待实现与核对 |
| 6 | 对象登记表：只用参考数据与 U 计算各构建、ISA、输入的 ①–③′、n_eff、K；另列出第一轮补丁 9 重转中 `prev-inst`、`avg` 转换是否成功（可用性信息，不是受控量） | ①–③′、n_eff、K 已按本版规则计算（附录 O.3）；`prev-inst`、`avg` 转换可用性待列出 |
| 7 | M1、M2 与判读分支夹具：N=15、K=9、sample 全零时 M2 = 0；只有一个正计数热点；正计数并列；正计数行不足 K；T = 0；U 为空；K 无定义；n_eff 为 null 且 K ∈ {5, 49, 50, 80}（K < 50 只作描述；K = 80 进入 M2-only 判读模式，只有区间、退化与准入检查全部通过才输出等价）；n_eff 恰为 3；10 行敏感性下的空函数集合；累计恰好等于与刚好跨过 80% | 待实现 |
| 8 | 合并口径：互补上下文（d0/d1 = 100/0 与 0/100）期望 S = 100、S_alt = 200、S_sum = 200；同一内联函数在不同调用点走不同分支；同一行多个覆盖区域与不同 discriminator；未执行模板实例的键落在已执行实例的行上（计入"已对齐但不在 U 内（未执行）"）；同时保存覆盖区域边界 | 待实现 |
| 9 | 区间模拟。场景清单、模拟代码与种子在运行前提交并推送（记录 SHA）；脚本先核对实际矩与清单一致，不可行的参数组合在运行前报错。记号：Δ 为真实均值差；"结构"取单阶段 15 与登记的阶段结构（预期为 5 + 10）。适用矩阵（清单逐行列出，不按全组合生成）：A1 用全部结构、全部标准误比；两阶段时方差比取 1 与 16，16 时分别让小阶段与大阶段的方差较大，阶段方差由闭式解确定：σ₂² = s² ÷ (λ₁²·r/n₁ + λ₂²/n₂)、σ₁² = r·σ₂²（s 为目标分层标准误，r 为方差比）；单阶段方差比记 not_applicable。A2 用全部结构，方差比只取 1，标准误比由 K 决定、照实报告。A3 用全部结构，各阶段同参数，方差比与标准误比照实报告。A4 用全部结构，标准误比为 0，方差比记 not_applicable。A5 只用两阶段的登记结构，方差比由参数推导并报告。验收场景：A1 正态，D_h ~ Normal(mean=Δ, sd=σ_h)，σ_h 使分层标准误与 ε 之比 ∈ {0.05, 0.1, 0.25, 0.5}，Δ ∈ {0, ±0.02, ±0.03}；A2 离散，D = Δ + U/K，U 在 {−1, 0, +1} 上等概率，K ∈ {50, 200}，Δ 同上；A3 纯 Bernoulli，D = a × Bernoulli(p)，其余为精确 0，p ∈ {0.05, 0.15}，a = Δ/p，Δ ∈ {±0.02, ±0.03}，各阶段同参数；A4 全零，D ≡ 0（Δ = 0，标准误为 0）；A5 两阶段，第一阶段 D = a × Bernoulli(0.15) 且 a = Δ/(λ₁ × 0.15)，第二阶段 D ~ Normal(mean=0, sd=0.001)，Δ ∈ {±0.02, ±0.03}。验收统计量：每个验收场景以 10⁶ 次重复只计算分层 t 区间（退化重复按"不判等价、覆盖为真"计；同一次重复中包络判等价蕴含 t 判等价、包络包含 t 区间，所以 t 单独的判等价概率与覆盖率是包络的保守界，允许相等；有限次估计仍有 Monte Carlo 误差，报告其标准误，不因独立的 10,000 次包络估计略高于 t 估计而判代码错误），t 单独的覆盖率 ≥ 93%，Δ 为 ±0.02 与 ±0.03 时 t 单独的判等价比例 ≤ 3.0%；A4 须 100% 退化、0% 判等价。包络（两种区间）另以 10,000 次重复照常报告，不作为验收统计量。报告场景（只报告、不验收）：B1 平移 lognormal，σ_log ∈ {0.17, 0.32, 0.75}（偏度约 0.5、1.0、3.3），长尾分别朝 +ε 与 −ε，平移使均值为 Δ ∈ {±0.02}，尺度使标准误与 ε 之比为 0.1；B2 D = 0.99 × Bernoulli(1/33) + 0.001 × Rademacher；B3 D = 0.2 × Bernoulli(0.15) + Normal(mean=0, sd=0.001)；B2、B3 用单阶段 15 与登记的阶段结构。每个场景输出参数、真实均值与方差、实际标准误与 ε 之比、覆盖率、判等价比例、退化比例与 Monte Carlo 标准误。全部验收场景完整执行并通过时开关为 true，任一统计验收不达标时为 false，由脚本写出；执行异常、缺行、参数或种子与登记清单不符属于执行失败，由脚本自动判定，修正实现并提交新的代码 SHA 后按同一清单与种子重跑，不触发回退；完整运行的结果保存并推送，之后因统计实现错误重跑时，开关取全部完整运行结果的合取；模拟与正式分析共用同一实现模块，SHA 不一致时拒绝写出开关值。夹具：第一次完整运行为 false、修正后为 true（开关为 false，两次都披露）；运行缺行（执行失败，可重跑，不计入合取）；清单生成器在 A2 × 方差比 16 上不产生行，人为加入时运行前报错；A5 核对 λ₁ × a × 0.15 = Δ。报告场景的结果写入修订 3 的局限说明 | 待执行 |
| 10 | 统计与登记门禁夹具：配对 RUN 顺序不同而 ID 相同；单边缺失与转换失败；RUN 级无定义按缺失；多个采集段只贡献一个 RUN；第 5 个 RUN 已显示等价时脚本不输出判读；3 + 12 的阶段退化反例；半格反例（0.0130000005000000555 与 0.0130000004999999445 交替）及其负数版本（都判退化）；给同一组差值加共同常数后退化结果不变；[0, 1e-9]（以 double 比较，退化）、[0, nextafter(1e-9, 1)]（不退化）、略小于 1e-9（退化）；[0, 0, 1e-6]（不退化）；同一组份额按两种顺序求和得到的 M2 差（退化）；某阶段恒定非零、单阶段退化；两阶段时分层点估计等于普通均值；只有一个阶段时与普通配对实现一致；NaN 传播；包络与"双通过"的逻辑等价；每条等价结论带模型标识；`quality_equivalence_enabled=false` 时任何对象、任何敏感性分支都不输出等价；离群标记（标准误与 ε 之比为 0.25 的正态差值大多不标，14 个约为 0、1 个为 0.3 时标记）；旧 5 + 新 10 全部合法通过、旧 RUN 没有初始化收据、篡改槽位表、旧 RUN 冒充新 RUN、同一原件占两个槽位、第 16 个 RUN、槽位成功后再追加成功、人工改判、第 14 个槽位没有终态时请求判读、计算日志 SHA 链断开、未推送的收据（都被门禁拒绝）；未知原因的 perf 非零退出（`paused_stop`）、白名单故障且有正面证据（重采）、过热引起非零退出、stderr 丢失、只有传输中断（重传，不计尝试）、完整传输后 SHA 不一致；原因不明的暂停后有合法证据恢复（通过）、事件只有说明文字（拒绝）、空间证据的 `df` 记录正常（拒绝）、温度证据的时间戳不在失败前后 10 秒内（拒绝）、曾经空间不足但恢复时仍不足（拒绝）、曾经过热但恢复时仍不满足启动条件（拒绝）、未知退出附近有高温却没有关联的停止动作（不可恢复，进入"停止缺失"）、硬件事件错误与过热同时出现（进入"停止缺失"）、旧的人工停止命令被用于另一次尝试（拒绝）、失败处理器没有写出证据文件（拒绝恢复）、故障已消除且证据关联正确（恢复）、没有恢复事件直接追加成功收据（拒绝）、恢复事件改变采集条件（拒绝，属于协议变更）、第四次尝试停止后申请恢复（拒绝）、`stopped_missing` 后再次采集（拒绝）、硬件事件错误停止（未完成槽位进入"停止缺失"）、遥测异常或转换失败进入恢复路径（拒绝）；登记前对真实 profile 请求 M3 或分支误差（拒绝）、登记后计算 M3 没有写日志（拒绝）；固定间隔的层不产生权重比较；合成 profile 允许计算 | 待实现 |
| 11 | 性能矩阵：从登记矩阵自动校验每组参数；缺少补零对照时拒绝输出"补零默认值已验证"；质量与性能的统计量、ε、停止规则没有混用，关闭质量判读不改变性能规则；超过登记的 N 后拒绝计入新轮次；N 的公式夹具：CV 0.5% 得 13，1% 得 40，CV 为 0 得 10，CV 缺失或为 NaN、无穷时视为无法预试得 40，预试含一个离群轮次时按未剔除的 CV 计算；G0 预试数据不进入正式轮次 | 待实现 |
| 12 | 板上（需要板子，加装散热后）：root 读取 `cpuinfo_cur_freq` 可用；记录器以 `O_RDONLY \| O_NONBLOCK` 打开并 `lseek(fd, 0, SEEK_SET)` 后读到首条序号 0，无新记录时立即返回；记录开机到会话开始的时长、`CONFIG_LOG_BUF_SHIFT` 与按当时的日志速率估计的回卷时间，会话期间序号连续；端点读取接口在"两次都没有新记录"与"后台已保存窗口内记录"两种情况下给出正确窗口；日志回卷的两条路径分别验收——首条序号 0 且连续时验证完整日志路径，首条不为 0 时默认阻止采集，只有采集前已有接受 unknown 的事件才继续，该路径不记为完整日志路径通过；加装散热后的正对照只有在全部必需观测完整时才预期合格，经批准的日志不完整路径预期为 unknown；完整执行一次前后校准流程（30 秒、每个 CPU 计数有效的中间区间 ≥ 25、采样器并行时的行为）；"解码满载 + 采样器"试运行，负载期间 ≥ 99% 的读数间隔不超过 1.5 秒、没有超过 3 秒的间隔、采样器使解码耗时中位数的变化小于 0.5%；同一次试运行带采样器的 G0 耗时（至少 10 轮）用于计算 N；核对 5.9 第 5 条引用的内核函数与行号。板上不为测试而重启 | 待板上执行 |
| 13 | 覆盖参考：spike 上 lcov 的 `DA` 与 JSON 推得的行计数一致；按主文件代码区域推导的函数行范围与 lcov/JSON summary 交叉一致；主文件按 `findMainViewFileID` 的规则核对，返回空的记录单独报告，并在对应表中有明确的状态；宏区域按区域类型与 FileID 识别；副本合并夹具（3 个编译单元的同一 static inline 函数只执行 1 个、宏内部循环、同文件同时含普通函数与宏定义、同一模板文件被不同名字包含两次、两个不同的已执行函数在同一物理行）；`HasMultipleRegions` 从 segments 提取的结果与 Coverage API 一致 | 待核对 |
| 14 | 离线资格分类：执行 5.9 第 5 条列出的全部判定脚本夹具，含记录器状态（首条序号不为 0 时不开始采集、会话中 boot_id 改变而记录器没有重启、一个 RUN 的两个端点跨 boot、保存失败、输出路径不在 `/opt/afdo_agent/` 下、非阻塞描述符无新记录时及时返回；日志回卷后未授权时拒绝采集，采集前授权后允许但保持 unknown，采集后补授权不能追认，之后观测正常也不能清除 unknown）；boot_id 改变用离线模拟，不在板上重启；用第一轮与四核诊断的原件重放，重放标签不覆盖历史资格 | 待实现 |
| 15 | ③ 门槛：按新的源函数合并规则与 ③ 的分母，在 FFmpeg（Thumb、A32）与 spike 的参考上计算 ③、③′ 与按互斥原因集合分桶的损失分解（各桶之和等于 ΣR(C) − ΣR(U)）；任一对象 ③ 低于 50% 时不登记，50%–80% 时登记文本须含损失分解 | 已计算（附录 O.3）：本版规则下四个对象 ③ ≥ 80%，三个 1% 门槛均未超限；同时登记 C₀ → U 账本、按 C₀ 的 ③、代码承载比例与 `code_free_line` 结构分类 |
| 16 | 跨侧对应表：只用 ELF、调试文件与参考数据生成，结论状态为封闭枚举，覆盖映射范围内每个 DWARF 函数（含内联抽象源），任一没有结论时登记准备失败。夹具：左花括号另起一行与签名跨 3 行的单候选函数（通过一致性检查，正常对应）；正确候选缺失、只剩一个同名错误候选，包括 Codex 编译验证过的条件编译反例（错误定义的行号全部落在候选范围内，但两侧定义声明位置不同，不建立对应）；行号集合为空（不通过）；函数自身在签名行上有一个行表行（通过）；行号落在另一个同名定义的函数体内（不通过）；裁决证据与所选编译变体不一致（拒绝登记）；名字规则：只有 `DW_AT_name`、只有 `DW_AT_MIPS_linkage_name`、名字只在 specification 或 abstract origin 上、同一 DIE 同时有两种 linkage name 属性且值不同（先取 MIPS）、当前 DIE 的标准 linkage name 与引用 DIE 的 MIPS linkage name 同时存在（与 `getSubroutineName(LinkageName)` 一致）；同一文件多个同名定义，包括条件编译导致声明行相同而函数体起点不同（判 `identity_ambiguous`）；`identity_ambiguous` 被内联进热点函数且有样本（RUN 有定义、相关行被排除）；GNU C 编译的 `libgcc2.c` 函数与 GNU AS 函数有样本（`not_instrumented`，归为范围外）；`not_instrumented` 外层含已执行参考函数的内联体（不得整组归为范围外）；只有约定的 `.__uniq.` 后缀有无不同、规范化后身份相同（正常对应）；修饰方式不同（`file.c:foo` 与 `_ZL3foov.__uniq.N`）或故意漏做后缀规范化（没有结论，登记准备失败）；完整身份清单独立于映射范围生成：范围外的顶层 static 函数名字去后缀后与覆盖侧不同、且没有被内联进任何范围内函数（登记准备失败），带 `.cold.1` 等后缀的克隆函数（登记准备失败或由裁决表给出结论），没有任何已匹配外层的未决函数、参考质量低于 1%（仍失败）；CU 文件名错误、producer 缺失或解析失败（没有结论）；外部 CU 中能对应已执行参考函数的内联体（不得归为未插桩）；clang C 编译单元中一个函数在覆盖导出中缺失（没有结论）；同一头文件在两个 CU 中的 decl_file 写法不同且只规范化了其中一种（登记准备失败）；内联帧对应到参考侧未执行的函数（计入"已对齐但不在 U 内（未执行）"）；列出名字去后缀后与已执行参考源函数相同、却不在映射范围内的全部 ELF 顶层函数并逐个裁决，裁决证据随表保存；报告 `not_instrumented` 的 CU 清单与 producer 分布 | 已生成：完整身份清单全部闭合，未决为 0（附录 O.3）；结论状态含裁决 1、2 新增的两种；夹具状态以 STATUS.md 为准 |
| 17 | 登记前打开过的真实 profile 清单与在其上计算过的量；G0 预试的条件、轮数、原始耗时与开销，写入修订 3 的披露 | 登记时执行 |
| 18 | 性能轮数 N：按第 12 项的 G0 预试与 5.9 第 5 条的公式确定每块板的 N；无法完成预试时取 40，写明来源 | 待确定 |
| 19 | 登记：①（协议与工作模型、脚本与共用的统计实现模块、依赖、配置、对象登记表、完整身份清单、外部 CU 清单、对应表与裁决表（含单候选的定义身份证据）、映射表、地址关系表、裁决 1–4 的证据清单（系统头目录与编译命令证据、宏生成函数的逐 token 与拼接证明、C 与 S 的行表证据、`code_free_line` 清单与结构分类、无键实例证明）、C₀ 与 C、排除清单、边界排除组、U、权重、受控量清单、重采原因码白名单与证据条件、停止与恢复事件及证据记录的格式）、②（已存在输入清单）、③（完整 RUN 槽位表与既有 RUN 的初始化收据）的 SHA-256 写入修订 3，连同第 9 项的场景清单、种子、全部完整运行的代码 SHA 与结果，以及 `quality_equivalence_enabled` 的取值；修订 3 提交与推送成功的记录在正式受控量计算之前保存 | 登记时执行 |
| 20 | 裁决夹具与证据：裁决 1–4 的 synthetic 夹具（各自的正例与反例）与真实例证明随登记；规则或实现变化时重跑全部夹具，并重新生成受影响的静态产物（完整身份清单、对应表、映射表、C、U、排除清单、权重、对象登记表）及其 SHA | 已实现（执行方报告 161 项通过）；登记时随产物重跑 |
| 21 | 本版（v1.6）经三家限定范围评审，评审意见处理后的版本才用于登记修订 3 | 待评审 |

### O.6 本版新写、尚未经评审的内容

本版全部修改都未经评审，请评审方重点核对：

1. 裁决 1（O.2.1）：`system_header_no_reference` 的四项正面证据是否充分；系统头代码内联进用户函数后不参与行级指标，这一局限是否可以接受。
2. 裁决 2（O.2.2）：宏生成函数的身份证据链，包括 TU basename 前缀映射、逐 token 拼写位置规则、`##` 拼接来源证明，以及"直接调用实参"的槽位证明。重点核对：保留真实的 `isMacroArgExpansion=false` 而改用 `MacroArgs` 槽位与实参区间作证明，是否会放过错误的身份。
3. 裁决 3（O.2.3）：③ 的行集合改为两个构建行表的并集。重点核对三点：
   - 用 S 的行表参与决定 C，是否会让被评估的一方影响分母（本版只用"有没有指令"这一事实，不用映射与身份结论）；
   - 去掉"有语句但在 -O3 下没有指令"的行，是否构成需要在结论中更醒目地披露的范围收窄；
   - ③ 从约 20% 升到约 85%，主要来自分母定义的修正。这是否应视为"修订本条"的正当结果，还是在看到结果后调整门槛，需要额外约束（例如同时登记 C₀ 口径的 ③ 并在结论中并列）。
4. 裁决 4（O.2.4）：无键实例的豁免条件与组判定。重点核对："键被拒绝"以正式工具的键生成代码为准，是否足以证明该实例不影响样本归属；部分实例豁免后，以其余实例的通过建立整组对应是否充分。
5. 5.8 第 5 条第 ④ 项的澄清：条目分类比例登记后按 RUN 计算，登记前只计算静态部分。
6. O.3 的数值来自执行方的报告，本文作者核对过报告与部分证据分片，没有独立重算；登记时以重新生成并登记 SHA 的产物为准。

## 附录 P：v1.6 评审意见处理（Codex、Claude Code）

两家的结论：Codex "修改后可以登记"（严重 0、重要 3、一般 3）；Claude Code "修改后可以登记"（严重 0、重要 2、一般 3）。Kimi Code 本轮未参加。两家都认为四项裁决的方向可以保留，不会放过错误的身份；需要修改的是：宏拼接规则在合并时漏掉一个分支；C 经由映射范围间接依赖身份结论；"有一条行表记录"不足以证明有指令；③ 越过门槛所依赖的理由与披露不准确；以及几处规范澄清。本版不改补丁，不改第一阶段，不改 golden 值，也不改 5.8 第 6 条的统计判读规则。C 的定义改变后，C、U、对象登记表、三个 1% 门槛与两份账本都须按本版规则重算；O.3 的数值是 v1.6 规则下的结果。

### P.1 严重

无。

### P.2 重要

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| O.2.2 的合并文本把所有非 scratch 的物理位置操作数都当作"直接调用实参"，漏掉了 `rulings.md` 补充 3 原有的"定义体操作数"分支。按字面，`_pixels8_x2_8_c`、`_pixels8`、`_` 这类定义体字面操作数会被拒绝，已经闭合的真实实例无法复现；实现（`token_paste_rule.py:157`）保留了这一分支 | Codex 重要 1 | 采纳 | 采用 Codex 的方案：操作数先按在拼接片段中的角色区分；非形参操作数须是唯一实例 X 定义片段中的原始 token、拼写位置在定义范围内，证明路径记为 `definition_body`，不要求槽位或宏实参标志；形参操作数取出未展开实参后，再按 SourceLocation 分三种情况。夹具采用 Codex 的正例与"同文本、异来源"反例 | O.2.2 第 2 项 |
| C 声称不依赖身份结论，但 O.2.3 的 S 侧要求地址落在"映射范围内函数"，映射范围由对应表的身份结论导出；实现读取 `selected-groups.json` 过滤 S 行表。5.8 正文没有函数限制，与 O.2.3 不一致，按 5.8 字面 O.3 不能复现 | Codex 重要 2；Claude Code 重要 R2 a | 采纳，两家合并 | 取消函数过滤，C 只由两份调试 ELF 与 C₀ 决定（Claude Code 的主方案；Codex 的"S ELF 独立完整代码清单"在不按执行状态与身份筛选时与之等价，本文进一步只要求区间落在可执行节内）。C 的生成禁止消费 `selected-groups` 等由跨侧结论派生的清单，映射范围与 C 的取证输入分别登记；只改变对应表、键接受状态或映射范围时 C 的 SHA 不变（Codex）。去掉过滤后 C 只会变大，③ 持平或下降，方向保守（Claude Code） | 5.8 第 5 条第 ③ 项；O.2.3 第 1–2 项 |
| "行表中有一条行号非 0 的记录"不足以证明该行有指令：同一地址可以有多条记录，LLVM 查询只取最后一条（`DWARFDebugLine.cpp:1297`、`:1311`）；现有实现没有排除被覆盖的记录。Codex 用合成记录验证了误纳入 | Codex 重要 3 | 采纳 | 采用 Codex 的方案：按 LLVM 22.1.8 行表查询语义取有效区间，排除 `end_sequence`、零长度区间与被同地址后续记录覆盖的记录；不要求能生成被接受的键；非叶子帧行号 0 不删除叶子见证；取证失败记为 `domain_unresolved`，不得解释为 `code_free_line`。Codex 没有规定 `domain_unresolved` 的去向，本文规定它保守地留在 C 中并单独报告（只会降低 ③）。Codex 建议的"可验证的指令起点"与函数区间求交没有采用：取消函数过滤后，指令起点证明依赖边界证明，会让 C 间接依赖映射范围；改为与带执行属性的节求交 | 5.8 第 5 条第 ③ 项；O.2.3 第 1、3 项 |
| ③ 从约 20% 升到约 85% 不能整体说成重复计数的修正。按 v1.6 规则，只排除内联汇编内部行、结构行与续行时，FFmpeg 的 ③ 为 49.96%（A32 49.88%），仍低于 50%；越过 50% 依赖排除 `other`，到 85% 依赖排除 `own_stmt_no_code`。按去除重复计数后的参考执行量，FFmpeg 约 40%、spike 约 28% 不在评价范围内，O.3 的"约 16%"以被内联汇编放大的 C₀ 为分母，低估了量级。"不可能有指令""被优化消除"属于过度解释 | Claude Code 重要 R1；Codex 一般 1 | 采纳，两家合并，按重要处理 | 理由拆为结构性重复计数的修正与可测量性的限定两部分；增加 C_dc 口径，三口径 ③ 与评价域外的不重复执行量比例写入对象登记表；每条结论附评价域说明；修订 3 后冻结 C 的定义（Claude Code）。措辞改为"固定构建中未取得指令行归属见证"，不推断其他构建；缺少任一 ③ 口径或范围说明时报告验收失败（Codex）。两家都认为改用可测量性定义评价域后可以作为"③ 低于 50% 时先修订本条"的正当修订：叶子帧采样对没有见证的行在构造上恒为 0，规则只用静态事实、不读样本、对全部对象统一适用；门槛仍按 C 判定 | 5.8 第 5 条第 ③ 项、第 6 条；O.2.3 第 4–6 项 |
| 无键实例的判定域没有写明。按字面，"静态映射中没有被接受的键"只覆盖映射范围，而映射范围又取决于组判定，形成循环；范围外顶层函数中的内联实例会被当作无键；枚举、边界或符号化失败也可能被当作"证明没有键" | Claude Code 重要 R2 b；Codex 一般 2 | 采纳，两家合并 | 对完整身份清单的全部顶层函数枚举，不限于映射范围；所在顶层函数边界无法证明时不得认定为无键（Claude Code）。枚举不完整、符号化失败、缺少键证明记录都不是无键证明，不得以默认计数 0 获得豁免；O.5 第 16 项的空集合夹具按新规则改写（Codex）。两家都核对到现有实现已经枚举全清单并拒绝边界不可证明的候选，本修改把实现前提写入规范，不改变现有结果 | 5.8 第 5 条（单候选一项）；O.2.4 第 3 项；P.5 第 16 项 |
| 5.8 漏写"位于 lexical block 之下"的子内联实例，O.2.4 有；以 5.8 为准时按字面会再次漏掉（执行方实现时遇到过） | Claude Code 重要 R2 c | 采纳 | 5.8 补上 | 5.8 第 5 条（单候选一项） |

### P.3 一般

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| 新增特殊状态的条目分类没有服从顶层组的分类顺序：纯系统头组、只含 FNDA = 0 宏生成函数的组应是范围外，不是"已对齐但不在 U 内" | Codex 一般 3 | 采纳 | 采用 Codex 的方案：先执行顶层组分类，已证明属于 `known_out_of_scope` 的组记为范围外；只有映射范围内、命中已登记键且值为特殊状态的条目才计入"已对齐但不在 U 内"；特殊状态不使未知名字或未登记键绕过未对齐检查 | 5.8 第 5 条；O.2.1 第 2 项；O.2.2 第 3 项 |
| `own_stmt_no_code` 中有内联调用点：Claude Code 比对 S 的 8977 个内联调用点，Thumb 的 3056 行中有 286 行（`DA` 约 1.63 亿）是调用点，代码归属在被调函数的行上 | Claude Code 一般 G1 | 采纳 | 新增子类 `inlined_call_site`，排在 `own_stmt_no_code` 之前，归入可测量性一侧 | O.2.3 第 5 项 |
| 宏生成函数一旦执行，其行按 v1.5 定义进入 C₀，但 5.8 的损失原因里没有对应项，C₀ → U 账本无法闭合（本构建 34 个函数 FNDA 全为 0，没有实际影响） | Claude Code 一般 G2 | 采纳 | 增加原因 `macro_generated_function`，用于两份账本；C 本身不随该结论变化（P.4 第 7 条） | 5.8 第 5 条；O.2.2 第 3 项；O.2.3 第 3 项 |
| O.6 第 6 项只写了本文作者的核对，可以补上评审方已经做过的核对 | Claude Code 一般 G3 | 采纳 | 写入 P.6 | P.6 |
| 系统头没有参考计数，不能声称其动态损失已被参考侧账本量化 | Codex 对裁决 1 的说明 | 采纳 | O.2.1 第 3 项补充 | O.2.1 |

### P.4 对前一版附录的更正

1. O.2 引言写"两者不一致时以 5.8 第 5 条为准"。v1.6 中两者确有三处不一致（C 的函数限制、无键判定域、lexical block 之下的子实例），按 5.8 字面 O.3 不能复现。本版已统一。
2. O.2.2 在合并补充 3 时漏掉了定义体操作数分支（`rulings.md` 补充 3 第 7 条原有）。
3. O.2.3 原第 4 项"这些行在任何构建的行表中都不可能有指令"不成立；行号归属随编译选项与调试位置变化。原第 5 项把 `own_stmt_no_code` 称为"被优化合并或消除的真实语句"属于过度解释。
4. O.3 末段"约 16%"以 C₀ 为分母，C₀ 含约 141 亿的内联汇编重复计数。按 C_dc，v1.6 规则下 FFmpeg 约 40%、spike 约 28%（A32 约 28.4%）不在评价范围内（Claude Code 计算）；本版规则下的数值由重算给出。
5. O.3 的数值是 v1.6 规则下的结果。本版改变了 C 的定义，O.3 第 3、4 项须按本版规则重算；第 1、2 项不受影响。
6. O.5 由 P.5 取代。
7. 本版初稿的 O.2.3 第 3 项要求把宏生成函数的行排除出 C，与第 2 项"C 不使用任何身份结论、只改对应表时 C 的 SHA 不变"矛盾：同一 C₀ 与 ELF 下，对应结论变成 `macro_generated_function` 会改变 C（执行方在实现前指出）。改为：C 只按见证规则判定，不含任何针对宏生成函数的规则；裁决 2 只决定这些行不进入 U，以及账本中的原因。宏展开的代码在行表中记在调用处，宏定义文件中的行通常没有见证，会自然落入 `code_free_line`；个别有见证的行留在 C 中计为损失，方向保守。本构建 34 个宏生成函数 FNDA 全为 0，不在 C₀ 中，数值不受影响。

### P.5 执行前须核对的事项（取代 O.5）

v1.8 起本节由附录 Q.5 取代，以下保留 v1.7 原文。

登记修订 3 之前由执行方完成。除第 9 项按预先登记的规则回退外，结果与本文不符时先修订本文，再登记。只有第 12 项需要板子；第 21 项是登记的前提；全部事项都不对正式 sample profile 计算任何受控量。

| 编号 | 事项 | 状态 |
|---|---|---|
| 1 | G.1.1 的前驱条件与原因分类与补丁 5 一致 | 已核对 |
| 2 | G.1.7：报告提交成功的用例断言 `tool.arguments` 记录了注入选项；报告自身写入或提交失败的用例，用测试执行器保存的 argv、stderr、退出码与文件状态核对；未执行到注入点的用例单列；评估准入对 `@rsp`、单横线、双横线、`=值`、分离值写法都拒绝 | 部分核对；测试待补 |
| 3 | G.1.8：三项派生负对照按既有 `avg` 命令重跑，仍在 boundary 阶段失败，逐项保存命令与原因 | 查找方式已核对；负对照待重跑 |
| 4 | G.1.3 第 4 条与 G.1.10 第 2 条与补丁 6 的实现与测试一致；写 profile 的符号化路径不做 canonical 化（`L/ProfiledBinary.h:620`、`L/ProfiledBinary.cpp:1212`、`:1297–1298`），`--show-canonical-fname` 只影响反汇编显示并在 IP 模式下被拒绝（`llvm-profgen.cpp:249`） | 源码已核对；测试待重跑 |
| 5 | 映射表与条目分类：① 合成全地址核对——为映射范围内边界可证明的每个指令起点构造一条合成样本，用正式工具以 skid=`none` 与 `prev-inst`、聚合方式 `max` 分别转换，写出的每个条目按 5.8 第 5 条分类，只允许映射表命中、`boundary_unavailable` 或 `known_out_of_scope`，出现 `unknown_name`、`reference_unresolved`、`unmapped_key` 即失败；② 用不共享映射表生成实现的第二条路径（`llvm-symbolizer` 逐地址符号化，加上独立的键计算）重算"地址 → 键 → 源位置"关系与排除结果，逐项比较；③ 边界排除组单独测试：`none` 转换把其条目归为 `boundary_unavailable`，`prev-inst`/`avg` 转换按冻结契约在 boundary 阶段失败；④ 在第一轮 CALIBRATION 运行的基准配置上做流程冒烟。夹具：映射表漏一个冷地址、删去一个碰撞地址后键集合不变、交换两个键的值、`prev-inst` 键算法错一位（都须被①或②发现）；同键不同源位置、同键同位置；两个命中函数集合不同的 RUN、删除热点函数全部条目、加显式零条目、改变预算（静态产物的 SHA 都不变）；原始 discriminator 不同而写出键相同、Thumb 别名、非叶子行号 0、偏移碰撞、不同构建路径、歧义键与正常键同时贡献同一行、名字闭包、评估侧错误地去掉 `.__uniq.` 后缀且 ELF 恰好有同名的范围外函数（期望无定义）、无法识别的函数名、一个计数很小的未对齐键（仍判无定义）、一个 `boundary_unavailable` 函数在 `none` 配置下有样本（单列，RUN 仍有定义）、同名组同时含可证明与不可证明的范围、被排除函数含热点内联体、FNDA 很小而循环行计数很大；顶层函数只含歧义候选（被枚举，命中的键计入"已对齐但不在 U 内"）、热点顶层函数同时含正常与歧义的内联体、在歧义组中注入不存在的键（仍判未对齐）、对应表中存在 `pending` 记录（登记准备失败）；补零 profile 不参与质量指标 | 待实现与核对 |
| 6 | 对象登记表：只用参考数据与 U 计算各构建、ISA、输入的 ①–③′、n_eff、K；另列出第一轮补丁 9 重转中 `prev-inst`、`avg` 转换是否成功（可用性信息，不是受控量） | 待按本版规则重算（C 的定义改变）；`prev-inst`、`avg` 转换可用性待列出 |
| 7 | M1、M2 与判读分支夹具：N=15、K=9、sample 全零时 M2 = 0；只有一个正计数热点；正计数并列；正计数行不足 K；T = 0；U 为空；K 无定义；n_eff 为 null 且 K ∈ {5, 49, 50, 80}（K < 50 只作描述；K = 80 进入 M2-only 判读模式，只有区间、退化与准入检查全部通过才输出等价）；n_eff 恰为 3；10 行敏感性下的空函数集合；累计恰好等于与刚好跨过 80% | 待实现 |
| 8 | 合并口径：互补上下文（d0/d1 = 100/0 与 0/100）期望 S = 100、S_alt = 200、S_sum = 200；同一内联函数在不同调用点走不同分支；同一行多个覆盖区域与不同 discriminator；未执行模板实例的键落在已执行实例的行上（计入"已对齐但不在 U 内（未执行）"）；同时保存覆盖区域边界 | 待实现 |
| 9 | 区间模拟。场景清单、模拟代码与种子在运行前提交并推送（记录 SHA）；脚本先核对实际矩与清单一致，不可行的参数组合在运行前报错。记号：Δ 为真实均值差；"结构"取单阶段 15 与登记的阶段结构（预期为 5 + 10）。适用矩阵（清单逐行列出，不按全组合生成）：A1 用全部结构、全部标准误比；两阶段时方差比取 1 与 16，16 时分别让小阶段与大阶段的方差较大，阶段方差由闭式解确定：σ₂² = s² ÷ (λ₁²·r/n₁ + λ₂²/n₂)、σ₁² = r·σ₂²（s 为目标分层标准误，r 为方差比）；单阶段方差比记 not_applicable。A2 用全部结构，方差比只取 1，标准误比由 K 决定、照实报告。A3 用全部结构，各阶段同参数，方差比与标准误比照实报告。A4 用全部结构，标准误比为 0，方差比记 not_applicable。A5 只用两阶段的登记结构，方差比由参数推导并报告。验收场景：A1 正态，D_h ~ Normal(mean=Δ, sd=σ_h)，σ_h 使分层标准误与 ε 之比 ∈ {0.05, 0.1, 0.25, 0.5}，Δ ∈ {0, ±0.02, ±0.03}；A2 离散，D = Δ + U/K，U 在 {−1, 0, +1} 上等概率，K ∈ {50, 200}，Δ 同上；A3 纯 Bernoulli，D = a × Bernoulli(p)，其余为精确 0，p ∈ {0.05, 0.15}，a = Δ/p，Δ ∈ {±0.02, ±0.03}，各阶段同参数；A4 全零，D ≡ 0（Δ = 0，标准误为 0）；A5 两阶段，第一阶段 D = a × Bernoulli(0.15) 且 a = Δ/(λ₁ × 0.15)，第二阶段 D ~ Normal(mean=0, sd=0.001)，Δ ∈ {±0.02, ±0.03}。验收统计量：每个验收场景以 10⁶ 次重复只计算分层 t 区间（退化重复按"不判等价、覆盖为真"计；同一次重复中包络判等价蕴含 t 判等价、包络包含 t 区间，所以 t 单独的判等价概率与覆盖率是包络的保守界，允许相等；有限次估计仍有 Monte Carlo 误差，报告其标准误，不因独立的 10,000 次包络估计略高于 t 估计而判代码错误），t 单独的覆盖率 ≥ 93%，Δ 为 ±0.02 与 ±0.03 时 t 单独的判等价比例 ≤ 3.0%；A4 须 100% 退化、0% 判等价。包络（两种区间）另以 10,000 次重复照常报告，不作为验收统计量。报告场景（只报告、不验收）：B1 平移 lognormal，σ_log ∈ {0.17, 0.32, 0.75}（偏度约 0.5、1.0、3.3），长尾分别朝 +ε 与 −ε，平移使均值为 Δ ∈ {±0.02}，尺度使标准误与 ε 之比为 0.1；B2 D = 0.99 × Bernoulli(1/33) + 0.001 × Rademacher；B3 D = 0.2 × Bernoulli(0.15) + Normal(mean=0, sd=0.001)；B2、B3 用单阶段 15 与登记的阶段结构。每个场景输出参数、真实均值与方差、实际标准误与 ε 之比、覆盖率、判等价比例、退化比例与 Monte Carlo 标准误。全部验收场景完整执行并通过时开关为 true，任一统计验收不达标时为 false，由脚本写出；执行异常、缺行、参数或种子与登记清单不符属于执行失败，由脚本自动判定，修正实现并提交新的代码 SHA 后按同一清单与种子重跑，不触发回退；完整运行的结果保存并推送，之后因统计实现错误重跑时，开关取全部完整运行结果的合取；模拟与正式分析共用同一实现模块，SHA 不一致时拒绝写出开关值。夹具：第一次完整运行为 false、修正后为 true（开关为 false，两次都披露）；运行缺行（执行失败，可重跑，不计入合取）；清单生成器在 A2 × 方差比 16 上不产生行，人为加入时运行前报错；A5 核对 λ₁ × a × 0.15 = Δ。报告场景的结果写入修订 3 的局限说明 | 待执行 |
| 10 | 统计与登记门禁夹具：配对 RUN 顺序不同而 ID 相同；单边缺失与转换失败；RUN 级无定义按缺失；多个采集段只贡献一个 RUN；第 5 个 RUN 已显示等价时脚本不输出判读；3 + 12 的阶段退化反例；半格反例（0.0130000005000000555 与 0.0130000004999999445 交替）及其负数版本（都判退化）；给同一组差值加共同常数后退化结果不变；[0, 1e-9]（以 double 比较，退化）、[0, nextafter(1e-9, 1)]（不退化）、略小于 1e-9（退化）；[0, 0, 1e-6]（不退化）；同一组份额按两种顺序求和得到的 M2 差（退化）；某阶段恒定非零、单阶段退化；两阶段时分层点估计等于普通均值；只有一个阶段时与普通配对实现一致；NaN 传播；包络与"双通过"的逻辑等价；每条等价结论带模型标识；`quality_equivalence_enabled=false` 时任何对象、任何敏感性分支都不输出等价；离群标记（标准误与 ε 之比为 0.25 的正态差值大多不标，14 个约为 0、1 个为 0.3 时标记）；旧 5 + 新 10 全部合法通过、旧 RUN 没有初始化收据、篡改槽位表、旧 RUN 冒充新 RUN、同一原件占两个槽位、第 16 个 RUN、槽位成功后再追加成功、人工改判、第 14 个槽位没有终态时请求判读、计算日志 SHA 链断开、未推送的收据（都被门禁拒绝）；未知原因的 perf 非零退出（`paused_stop`）、白名单故障且有正面证据（重采）、过热引起非零退出、stderr 丢失、只有传输中断（重传，不计尝试）、完整传输后 SHA 不一致；原因不明的暂停后有合法证据恢复（通过）、事件只有说明文字（拒绝）、空间证据的 `df` 记录正常（拒绝）、温度证据的时间戳不在失败前后 10 秒内（拒绝）、曾经空间不足但恢复时仍不足（拒绝）、曾经过热但恢复时仍不满足启动条件（拒绝）、未知退出附近有高温却没有关联的停止动作（不可恢复，进入"停止缺失"）、硬件事件错误与过热同时出现（进入"停止缺失"）、旧的人工停止命令被用于另一次尝试（拒绝）、失败处理器没有写出证据文件（拒绝恢复）、故障已消除且证据关联正确（恢复）、没有恢复事件直接追加成功收据（拒绝）、恢复事件改变采集条件（拒绝，属于协议变更）、第四次尝试停止后申请恢复（拒绝）、`stopped_missing` 后再次采集（拒绝）、硬件事件错误停止（未完成槽位进入"停止缺失"）、遥测异常或转换失败进入恢复路径（拒绝）；登记前对真实 profile 请求 M3 或分支误差（拒绝）、登记后计算 M3 没有写日志（拒绝）；固定间隔的层不产生权重比较；合成 profile 允许计算 | 待实现 |
| 11 | 性能矩阵：从登记矩阵自动校验每组参数；缺少补零对照时拒绝输出"补零默认值已验证"；质量与性能的统计量、ε、停止规则没有混用，关闭质量判读不改变性能规则；超过登记的 N 后拒绝计入新轮次；N 的公式夹具：CV 0.5% 得 13，1% 得 40，CV 为 0 得 10，CV 缺失或为 NaN、无穷时视为无法预试得 40，预试含一个离群轮次时按未剔除的 CV 计算；G0 预试数据不进入正式轮次 | 待实现 |
| 12 | 板上（需要板子，加装散热后）：root 读取 `cpuinfo_cur_freq` 可用；记录器以 `O_RDONLY \| O_NONBLOCK` 打开并 `lseek(fd, 0, SEEK_SET)` 后读到首条序号 0，无新记录时立即返回；记录开机到会话开始的时长、`CONFIG_LOG_BUF_SHIFT` 与按当时的日志速率估计的回卷时间，会话期间序号连续；端点读取接口在"两次都没有新记录"与"后台已保存窗口内记录"两种情况下给出正确窗口；日志回卷的两条路径分别验收——首条序号 0 且连续时验证完整日志路径，首条不为 0 时默认阻止采集，只有采集前已有接受 unknown 的事件才继续，该路径不记为完整日志路径通过；加装散热后的正对照只有在全部必需观测完整时才预期合格，经批准的日志不完整路径预期为 unknown；完整执行一次前后校准流程（30 秒、每个 CPU 计数有效的中间区间 ≥ 25、采样器并行时的行为）；"解码满载 + 采样器"试运行，负载期间 ≥ 99% 的读数间隔不超过 1.5 秒、没有超过 3 秒的间隔、采样器使解码耗时中位数的变化小于 0.5%；同一次试运行带采样器的 G0 耗时（至少 10 轮）用于计算 N；核对 5.9 第 5 条引用的内核函数与行号。板上不为测试而重启 | 待板上执行 |
| 13 | 覆盖参考：spike 上 lcov 的 `DA` 与 JSON 推得的行计数一致；按主文件代码区域推导的函数行范围与 lcov/JSON summary 交叉一致；主文件按 `findMainViewFileID` 的规则核对，返回空的记录单独报告，并在对应表中有明确的状态；宏区域按区域类型与 FileID 识别；副本合并夹具（3 个编译单元的同一 static inline 函数只执行 1 个、宏内部循环、同文件同时含普通函数与宏定义、同一模板文件被不同名字包含两次、两个不同的已执行函数在同一物理行）；`HasMultipleRegions` 从 segments 提取的结果与 Coverage API 一致 | 待核对 |
| 14 | 离线资格分类：执行 5.9 第 5 条列出的全部判定脚本夹具，含记录器状态（首条序号不为 0 时不开始采集、会话中 boot_id 改变而记录器没有重启、一个 RUN 的两个端点跨 boot、保存失败、输出路径不在 `/opt/afdo_agent/` 下、非阻塞描述符无新记录时及时返回；日志回卷后未授权时拒绝采集，采集前授权后允许但保持 unknown，采集后补授权不能追认，之后观测正常也不能清除 unknown）；boot_id 改变用离线模拟，不在板上重启；用第一轮与四核诊断的原件重放，重放标签不覆盖历史资格 | 待实现 |
| 15 | ③ 门槛：按新的源函数合并规则与 ③ 的分母，在 FFmpeg（Thumb、A32）与 spike 的参考上计算 ③、③′ 与按互斥原因集合分桶的损失分解（各桶之和等于 ΣR(C) − ΣR(U)）；任一对象 ③ 低于 50% 时不登记，50%–80% 时登记文本须含损失分解 | 待按本版规则重算：C 取消函数过滤并按 LLVM 行表查询语义取见证；登记 C₀、C_dc、C 三个口径的 ③、评价域外的不重复执行量比例、两份账本、`domain_unresolved` 与 `code_free_line` 结构分类（含 `inlined_call_site`） |
| 16 | 跨侧对应表：只用 ELF、调试文件与参考数据生成，结论状态为封闭枚举，覆盖映射范围内每个 DWARF 函数（含内联抽象源），任一没有结论时登记准备失败。夹具：左花括号另起一行与签名跨 3 行的单候选函数（通过一致性检查，正常对应）；正确候选缺失、只剩一个同名错误候选，包括 Codex 编译验证过的条件编译反例（错误定义的行号全部落在候选范围内，但两侧定义声明位置不同，不建立对应）；有键实例行号集合为空（不通过）；已完整证明无键、且三项豁免条件全部满足的空集合实例（豁免）；无键证明不完整（不得豁免）；函数自身在签名行上有一个行表行（通过）；行号落在另一个同名定义的函数体内（不通过）；裁决证据与所选编译变体不一致（拒绝登记）；名字规则：只有 `DW_AT_name`、只有 `DW_AT_MIPS_linkage_name`、名字只在 specification 或 abstract origin 上、同一 DIE 同时有两种 linkage name 属性且值不同（先取 MIPS）、当前 DIE 的标准 linkage name 与引用 DIE 的 MIPS linkage name 同时存在（与 `getSubroutineName(LinkageName)` 一致）；同一文件多个同名定义，包括条件编译导致声明行相同而函数体起点不同（判 `identity_ambiguous`）；`identity_ambiguous` 被内联进热点函数且有样本（RUN 有定义、相关行被排除）；GNU C 编译的 `libgcc2.c` 函数与 GNU AS 函数有样本（`not_instrumented`，归为范围外）；`not_instrumented` 外层含已执行参考函数的内联体（不得整组归为范围外）；只有约定的 `.__uniq.` 后缀有无不同、规范化后身份相同（正常对应）；修饰方式不同（`file.c:foo` 与 `_ZL3foov.__uniq.N`）或故意漏做后缀规范化（没有结论，登记准备失败）；完整身份清单独立于映射范围生成：范围外的顶层 static 函数名字去后缀后与覆盖侧不同、且没有被内联进任何范围内函数（登记准备失败），带 `.cold.1` 等后缀的克隆函数（登记准备失败或由裁决表给出结论），没有任何已匹配外层的未决函数、参考质量低于 1%（仍失败）；CU 文件名错误、producer 缺失或解析失败（没有结论）；外部 CU 中能对应已执行参考函数的内联体（不得归为未插桩）；clang C 编译单元中一个函数在覆盖导出中缺失（没有结论）；同一头文件在两个 CU 中的 decl_file 写法不同且只规范化了其中一种（登记准备失败）；内联帧对应到参考侧未执行的函数（计入"已对齐但不在 U 内（未执行）"）；列出名字去后缀后与已执行参考源函数相同、却不在映射范围内的全部 ELF 顶层函数并逐个裁决，裁决证据随表保存；报告 `not_instrumented` 的 CU 清单与 producer 分布 | 已生成（v1.6 规则），完整身份清单全部闭合；无键判定域按本版写明，现有实现已枚举全清单，待重跑确认结果不变；夹具状态以 STATUS.md 为准 |
| 17 | 登记前打开过的真实 profile 清单与在其上计算过的量；G0 预试的条件、轮数、原始耗时与开销，写入修订 3 的披露 | 登记时执行 |
| 18 | 性能轮数 N：按第 12 项的 G0 预试与 5.9 第 5 条的公式确定每块板的 N；无法完成预试时取 40，写明来源 | 待确定 |
| 19 | 登记：①（协议与工作模型、脚本与共用的统计实现模块、依赖、配置、对象登记表、完整身份清单、外部 CU 清单、对应表与裁决表（含单候选的定义身份证据）、映射表、地址关系表、裁决 1–4 的证据清单（系统头目录与编译命令证据、宏生成函数的逐 token 与拼接证明、C 与 S 的行表证据、`code_free_line` 清单与结构分类、无键实例证明）、C₀ 与 C、排除清单、边界排除组、U、权重、受控量清单、重采原因码白名单与证据条件、停止与恢复事件及证据记录的格式）、②（已存在输入清单）、③（完整 RUN 槽位表与既有 RUN 的初始化收据）的 SHA-256 写入修订 3，连同第 9 项的场景清单、种子、全部完整运行的代码 SHA 与结果，以及 `quality_equivalence_enabled` 的取值；修订 3 提交与推送成功的记录在正式受控量计算之前保存 | 登记时执行 |
| 20 | 裁决夹具与证据：裁决 1–4 的 synthetic 夹具（各自的正例与反例）与真实例证明随登记；规则或实现变化时重跑全部夹具，并重新生成受影响的静态产物（完整身份清单、对应表、映射表、C、U、排除清单、权重、对象登记表）及其 SHA。本版新增：O.2.2 定义体操作数正例（`OPNAME ## _pixels8`、`a ## _ ## b ## c`）与"同文本、来自另一宏定义"的反例；C 的取证——只有 S 行表见证且所在组不在映射范围的行进入 C，只改变对应表、键接受状态或映射范围时 C 的 SHA 不变，同地址两条记录、零长度区间、`end_sequence`、跨 sequence、非叶子行号 0 而叶子见证有效、取证失败记为 `domain_unresolved`；C ⊆ C_dc ⊆ C₀ 与三个口径的 ③；一行只调用一个被完全内联的函数归入 `inlined_call_site`；FNDA > 0 的宏生成函数：无见证的行在 C₀ → U 账本中带 {`code_free_line`, `macro_generated_function`}，有见证的行在 C 内、在 C → U 账本中带 `macro_generated_function`，两份账本差值为 0；同一 C₀ 与 ELF 下，某函数的对应结论在普通对应与 `macro_generated_function` 之间切换时，C 的 SHA 不变、只有 U 与账本原因改变；无键判定——漏枚举一个范围、顶层函数边界失败、删除一条键证明记录、符号化失败都不得豁免，全组无键时参考计数完整进入 `no_key_line`；特殊状态条目——纯系统头组为范围外、系统头内联进已执行函数、只含 FNDA = 0 宏生成函数的组为范围外、FNDA > 0 的宏生成函数、特殊状态组中的未登记键仍为未对齐，每条 body 记录只进入一个类别；结论输出缺少评价域说明或任一 ③ 口径时拒绝写出 | v1.6 规则的夹具已实现（执行方报告 161 项通过）；本版新增夹具待实现；登记时随产物重跑 |
| 21 | 本版（v1.7）连同按本版规则重算的静态结果经限定范围评审，评审意见处理后的版本才用于登记修订 3 | 待重算后评审 |

### P.6 本版新写、尚未经评审的内容

1. `domain_unresolved` 的去向：Codex 只规定它不得解释为 `code_free_line`；本文规定它保守地留在 C 中、不在 U 内即计为损失，并单独报告。
2. 见证区间的限定：本文没有采用"可验证的指令起点"与函数区间求交，改为只要求有效行表区间与带执行属性的节相交且非空，以免 C 经边界证明间接依赖映射范围。请评审方确认这一取舍不会把非代码数据误纳入 C。
3. C_dc 的定义采用 Claude Code 的三类；新增的 `inlined_call_site` 排在 `own_stmt_no_code` 之前，归入可测量性一侧，不计入 C_dc 的修正。
4. 5.8 第 6 条新增的评价域说明是结论输出的必备字段，缺少时拒绝写出。
5. 宏生成函数的行与 C 的关系（P.4 第 7 条）：C 不含针对宏生成函数的规则，有见证的宏生成行留在 C 中计为损失。
6. 已做的核对：两家各自核对了 O.3 中分类 `DA` 之和等于 ΣR(C₀) − ΣR(C)（Thumb 与 A32 逐字节相等），两份账本的 CSV 求和等式成立（Codex 核对 18 个分片的 SHA），O.3 的 ③ 与 05 报告第 11.2 节一致；Codex 重跑了 105 项相关测试，全部通过。两家都没有独立重算 U 与 ③。本版规则下的数值尚未计算，登记以重新生成并登记 SHA 的产物为准。

## 附录 Q：v1.7 评审意见处理（Claude Code、Codex）

评审对象是 v1.7 与按其规则重算的静态结果（05 报告第 13 节，提交 `aa77cd7`）。两家的结论：Claude Code "可以登记"（严重 0、重要 0、一般 5）；Codex "修改后可以登记"（严重 0、重要 2、一般 2）。Kimi Code 本轮未参加。两家都确认 v1.6 评审提出的问题已经正确解决，实现与 v1.7 的文字一致，重算数值与证据相符：Codex 从保存的八份行表提取文件独立重建 C，四组集合与登记产物一致，并独立重算了两份账本、三口径 ③、n_eff 与 K；Claude Code 逐项核对了 FFmpeg 两侧的分类和与账本。两家都接受以可测量性限定作为本次评价域修订的依据，条件是只支持限定后的结论。

本轮的修改只加强门禁、前提检查与措辞，不改变 C、U、③ 与三个门槛的数值。按项目约定（严重问题为 0 时修订后不再评审），本版不再评审设计文档，修改内容以实现与夹具验收为准。本版不改补丁，不改第一阶段，不改 golden 值，也不改 5.8 第 6 条的统计判读规则。

### Q.1 严重

无。

### Q.2 重要

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| `domain_unresolved` 留在 C 中只会压低 ③，却同时加大三个 1% 门槛的分母，可能让本不合格的对象显得合格。Codex 的合成反例：额外一行若已证明无见证，③ 为 98%、歧义比例 1.2%，不能登记；同一行若取证失败、以 `DA` = 210 留在 C 中，③ 为 80.99%、歧义比例 0.99%，两个门槛都通过。实现的登记阻断条件也没有检查 unresolved。另外，文字写的是逐行处理，实现是"无法定位就全体回退" | Codex 重要 1；Claude Code 一般 G2 | 采纳，两家合并 | 任一对象存在 `domain_unresolved` 行时，状态为 `domain_evidence_incomplete`，不得判为可登记，也不得输出质量结论；修复取证、重新生成后才做准入判定（Codex）。失败不能定位到具体行时（包括取证程序退出码非 0 或有诊断输出），全部未取得见证的 C₀ 行都记为 `domain_unresolved`，与现有实现一致（Claude Code）。"保守"一词改为如实说明：留在 C 中只是为了在账本里保存未解决的部分 | 5.8 第 5 条第 ③ 项；O.2.3 第 3 项 |
| 结论门禁只检查字段是否存在：三口径全为 null、空对象、过期或手写的数值都能通过（Codex 用合成调用验证） | Codex 重要 2；Claude Code 一般 G1 | 采纳，两家合并 | 写出前校验数值本身：分子分母为非负整数、分母大于 0、比值有限且等于分子 ÷ 分母、三个分子相同、ΣR(C) ≤ ΣR(C_dc) ≤ ΣR(C₀)，拒绝 null、NaN、Infinity 与跨对象数值，JSON 禁止非有限数，校验在打开输出文件之前完成，无定义情况只允许诊断报告（Codex）。各数值须与修订 3 登记、按 SHA 读取的对象登记表逐项相等（Claude Code） | 5.8 第 6 条；O.2.3 第 7 项（新增） |

### Q.3 一般

| 问题 | 来源 | 处理 | 采用与理由 | 位置 |
|---|---|---|---|---|
| 实现把每条 sequence 的有效区间直接取并集，LLVM 则先选 sequence 再查行（`DWARFDebugLine.cpp:1274`、`:1335–1351`）；两者只有在 sequence 不重叠时才一致，实现没有记录和验收这一前提，提取器还丢弃了 SectionIndex。Codex 检查了本次八份提取文件，没有发现同一 CU 内的 sequence 重叠 | Codex 一般 1 | 采纳 | 采用 Codex 的方案：保存 CU、SectionIndex 与 sequence 范围；生成 C 前自动验证"同一 CU、同一节的 sequence 在可执行节交集内不重叠"，不满足时判取证失败（随之进入 `domain_evidence_incomplete`）；今后支持重叠输入须作为规则变更。文字由"按 LLVM 查询语义"改为"逐 sequence 区间算法 + 前提" | 5.8 第 5 条第 ③ 项；O.2.3 第 1 项 |
| "与可执行节相交"不能保证排除非代码数据：可执行节中可以有 literal pool 等数据（`ARMELFStreamer.cpp:465`、`:571–600` 的 `$d` 映射符号）。另一个风险是其他链接器把被丢弃函数的行表地址重定位到 0，这样的序列只要与可执行节部分相交就会成为见证 | Codex 一般 2；Claude Code 一般 G4 | 采纳，两家合并 | 见证改称操作性定义，C 是候选评价域，不声称已排除全部非代码数据，"指令行归属见证"改为"行表归属见证"，评价域说明同步修改（Codex）。登记前报告与可执行节只部分相交的区间个数，以及起始地址低于最低可执行节起点的 sequence 个数，不为 0 时逐项列出（Claude Code）。Claude Code 核对了本构建行表的最低地址是 `.init` 起点 0x14f94，没有地址 0 附近的残留序列 | 5.8 第 5 条第 ③ 项、第 6 条；O.2.3 第 1、4 项 |
| `inlined_call_site` 归入可测量性一侧是对的，但调用行的计数带有被调函数计数的成分；若被移到结构性重复计数一侧，FFmpeg 的 C_dc 口径 ③ 会从 49.93% 变成 50.68%（A32 为 50.64%），恰好跨过 50%，以后容易被误读 | Claude Code 一般 G3 | 采纳 | 写明 `inlined_call_site` 固定归入可测量性一侧，不随评审或结果改变，`DA` 另行报告 | O.2.3 第 5 项 |
| 附录 P.4 第 4 条引用的"约 40%"偏低：Claude Code 上一轮只算了 `own_stmt_no_code`，漏了 `other` | Claude Code 一般 G5 | 采纳 | 更正见 Q.4 第 1 条 | Q.4 |
| 三口径 ③ 与域外比例是参考行计数质量的比例，不能解释为运行时间或独立执行事件的比例 | Codex（对可测量性限定的回答） | 采纳 | 写入 O.2.3 第 5 项与 5.8 第 6 条的评价域说明 | O.2.3 第 5 项；5.8 第 6 条 |

### Q.4 对前一版附录的更正

1. P.4 第 4 条："按 C_dc，v1.6 规则下 FFmpeg 约 40%……不在评价范围内"应为约 41.4%（(4668195093 + 193521529) ÷ 11751913019，与 05 报告第 13 节 `comparison.json` 中 v1.6 的值一致）；spike 约 27.6%（A32 约 28.4%）不变。本版规则下 FFmpeg 为 41.24%（Thumb）与 41.13%（A32）。
2. P.2 第 3 行与 P.6 第 1 条称 `domain_unresolved` 留在 C 中"只会降低 ③""方向保守"。这只对 ③ 成立，对三个 1% 门槛不成立（Q.2 第 1 行）。
3. P.6 第 2 条请评审方确认"不会把非代码数据误纳入 C"，这一点不能保证。现已改为操作性定义（Q.3 第 2 行）。
4. P.5 由 Q.5 取代。

### Q.5 执行前须核对的事项（取代 P.5）

登记修订 3 之前由执行方完成。除第 9 项按预先登记的规则回退外，结果与本文不符时先修订本文，再登记。只有第 12 项需要板子；第 21 项是登记的前提；全部事项都不对正式 sample profile 计算任何受控量。

| 编号 | 事项 | 状态 |
|---|---|---|
| 1 | G.1.1 的前驱条件与原因分类与补丁 5 一致 | 已核对 |
| 2 | G.1.7：报告提交成功的用例断言 `tool.arguments` 记录了注入选项；报告自身写入或提交失败的用例，用测试执行器保存的 argv、stderr、退出码与文件状态核对；未执行到注入点的用例单列；评估准入对 `@rsp`、单横线、双横线、`=值`、分离值写法都拒绝 | 部分核对；测试待补 |
| 3 | G.1.8：三项派生负对照按既有 `avg` 命令重跑，仍在 boundary 阶段失败，逐项保存命令与原因 | 查找方式已核对；负对照待重跑 |
| 4 | G.1.3 第 4 条与 G.1.10 第 2 条与补丁 6 的实现与测试一致；写 profile 的符号化路径不做 canonical 化（`L/ProfiledBinary.h:620`、`L/ProfiledBinary.cpp:1212`、`:1297–1298`），`--show-canonical-fname` 只影响反汇编显示并在 IP 模式下被拒绝（`llvm-profgen.cpp:249`） | 源码已核对；测试待重跑 |
| 5 | 映射表与条目分类：① 合成全地址核对——为映射范围内边界可证明的每个指令起点构造一条合成样本，用正式工具以 skid=`none` 与 `prev-inst`、聚合方式 `max` 分别转换，写出的每个条目按 5.8 第 5 条分类，只允许映射表命中、`boundary_unavailable` 或 `known_out_of_scope`，出现 `unknown_name`、`reference_unresolved`、`unmapped_key` 即失败；② 用不共享映射表生成实现的第二条路径（`llvm-symbolizer` 逐地址符号化，加上独立的键计算）重算"地址 → 键 → 源位置"关系与排除结果，逐项比较；③ 边界排除组单独测试：`none` 转换把其条目归为 `boundary_unavailable`，`prev-inst`/`avg` 转换按冻结契约在 boundary 阶段失败；④ 在第一轮 CALIBRATION 运行的基准配置上做流程冒烟。夹具：映射表漏一个冷地址、删去一个碰撞地址后键集合不变、交换两个键的值、`prev-inst` 键算法错一位（都须被①或②发现）；同键不同源位置、同键同位置；两个命中函数集合不同的 RUN、删除热点函数全部条目、加显式零条目、改变预算（静态产物的 SHA 都不变）；原始 discriminator 不同而写出键相同、Thumb 别名、非叶子行号 0、偏移碰撞、不同构建路径、歧义键与正常键同时贡献同一行、名字闭包、评估侧错误地去掉 `.__uniq.` 后缀且 ELF 恰好有同名的范围外函数（期望无定义）、无法识别的函数名、一个计数很小的未对齐键（仍判无定义）、一个 `boundary_unavailable` 函数在 `none` 配置下有样本（单列，RUN 仍有定义）、同名组同时含可证明与不可证明的范围、被排除函数含热点内联体、FNDA 很小而循环行计数很大；顶层函数只含歧义候选（被枚举，命中的键计入"已对齐但不在 U 内"）、热点顶层函数同时含正常与歧义的内联体、在歧义组中注入不存在的键（仍判未对齐）、对应表中存在 `pending` 记录（登记准备失败）；补零 profile 不参与质量指标 | 待实现与核对 |
| 6 | 对象登记表：只用参考数据与 U 计算各构建、ISA、输入的 ①–③′、n_eff、K；另列出第一轮补丁 9 重转中 `prev-inst`、`avg` 转换是否成功（可用性信息，不是受控量） | ①–③′、n_eff、K 已按 v1.7 规则计算（05 报告第 13 节）；本版不改变其数值，登记时随产物重跑；`prev-inst`、`avg` 转换可用性待列出 |
| 7 | M1、M2 与判读分支夹具：N=15、K=9、sample 全零时 M2 = 0；只有一个正计数热点；正计数并列；正计数行不足 K；T = 0；U 为空；K 无定义；n_eff 为 null 且 K ∈ {5, 49, 50, 80}（K < 50 只作描述；K = 80 进入 M2-only 判读模式，只有区间、退化与准入检查全部通过才输出等价）；n_eff 恰为 3；10 行敏感性下的空函数集合；累计恰好等于与刚好跨过 80% | 待实现 |
| 8 | 合并口径：互补上下文（d0/d1 = 100/0 与 0/100）期望 S = 100、S_alt = 200、S_sum = 200；同一内联函数在不同调用点走不同分支；同一行多个覆盖区域与不同 discriminator；未执行模板实例的键落在已执行实例的行上（计入"已对齐但不在 U 内（未执行）"）；同时保存覆盖区域边界 | 待实现 |
| 9 | 区间模拟。场景清单、模拟代码与种子在运行前提交并推送（记录 SHA）；脚本先核对实际矩与清单一致，不可行的参数组合在运行前报错。记号：Δ 为真实均值差；"结构"取单阶段 15 与登记的阶段结构（预期为 5 + 10）。适用矩阵（清单逐行列出，不按全组合生成）：A1 用全部结构、全部标准误比；两阶段时方差比取 1 与 16，16 时分别让小阶段与大阶段的方差较大，阶段方差由闭式解确定：σ₂² = s² ÷ (λ₁²·r/n₁ + λ₂²/n₂)、σ₁² = r·σ₂²（s 为目标分层标准误，r 为方差比）；单阶段方差比记 not_applicable。A2 用全部结构，方差比只取 1，标准误比由 K 决定、照实报告。A3 用全部结构，各阶段同参数，方差比与标准误比照实报告。A4 用全部结构，标准误比为 0，方差比记 not_applicable。A5 只用两阶段的登记结构，方差比由参数推导并报告。验收场景：A1 正态，D_h ~ Normal(mean=Δ, sd=σ_h)，σ_h 使分层标准误与 ε 之比 ∈ {0.05, 0.1, 0.25, 0.5}，Δ ∈ {0, ±0.02, ±0.03}；A2 离散，D = Δ + U/K，U 在 {−1, 0, +1} 上等概率，K ∈ {50, 200}，Δ 同上；A3 纯 Bernoulli，D = a × Bernoulli(p)，其余为精确 0，p ∈ {0.05, 0.15}，a = Δ/p，Δ ∈ {±0.02, ±0.03}，各阶段同参数；A4 全零，D ≡ 0（Δ = 0，标准误为 0）；A5 两阶段，第一阶段 D = a × Bernoulli(0.15) 且 a = Δ/(λ₁ × 0.15)，第二阶段 D ~ Normal(mean=0, sd=0.001)，Δ ∈ {±0.02, ±0.03}。验收统计量：每个验收场景以 10⁶ 次重复只计算分层 t 区间（退化重复按"不判等价、覆盖为真"计；同一次重复中包络判等价蕴含 t 判等价、包络包含 t 区间，所以 t 单独的判等价概率与覆盖率是包络的保守界，允许相等；有限次估计仍有 Monte Carlo 误差，报告其标准误，不因独立的 10,000 次包络估计略高于 t 估计而判代码错误），t 单独的覆盖率 ≥ 93%，Δ 为 ±0.02 与 ±0.03 时 t 单独的判等价比例 ≤ 3.0%；A4 须 100% 退化、0% 判等价。包络（两种区间）另以 10,000 次重复照常报告，不作为验收统计量。报告场景（只报告、不验收）：B1 平移 lognormal，σ_log ∈ {0.17, 0.32, 0.75}（偏度约 0.5、1.0、3.3），长尾分别朝 +ε 与 −ε，平移使均值为 Δ ∈ {±0.02}，尺度使标准误与 ε 之比为 0.1；B2 D = 0.99 × Bernoulli(1/33) + 0.001 × Rademacher；B3 D = 0.2 × Bernoulli(0.15) + Normal(mean=0, sd=0.001)；B2、B3 用单阶段 15 与登记的阶段结构。每个场景输出参数、真实均值与方差、实际标准误与 ε 之比、覆盖率、判等价比例、退化比例与 Monte Carlo 标准误。全部验收场景完整执行并通过时开关为 true，任一统计验收不达标时为 false，由脚本写出；执行异常、缺行、参数或种子与登记清单不符属于执行失败，由脚本自动判定，修正实现并提交新的代码 SHA 后按同一清单与种子重跑，不触发回退；完整运行的结果保存并推送，之后因统计实现错误重跑时，开关取全部完整运行结果的合取；模拟与正式分析共用同一实现模块，SHA 不一致时拒绝写出开关值。夹具：第一次完整运行为 false、修正后为 true（开关为 false，两次都披露）；运行缺行（执行失败，可重跑，不计入合取）；清单生成器在 A2 × 方差比 16 上不产生行，人为加入时运行前报错；A5 核对 λ₁ × a × 0.15 = Δ。报告场景的结果写入修订 3 的局限说明 | 待执行 |
| 10 | 统计与登记门禁夹具：配对 RUN 顺序不同而 ID 相同；单边缺失与转换失败；RUN 级无定义按缺失；多个采集段只贡献一个 RUN；第 5 个 RUN 已显示等价时脚本不输出判读；3 + 12 的阶段退化反例；半格反例（0.0130000005000000555 与 0.0130000004999999445 交替）及其负数版本（都判退化）；给同一组差值加共同常数后退化结果不变；[0, 1e-9]（以 double 比较，退化）、[0, nextafter(1e-9, 1)]（不退化）、略小于 1e-9（退化）；[0, 0, 1e-6]（不退化）；同一组份额按两种顺序求和得到的 M2 差（退化）；某阶段恒定非零、单阶段退化；两阶段时分层点估计等于普通均值；只有一个阶段时与普通配对实现一致；NaN 传播；包络与"双通过"的逻辑等价；每条等价结论带模型标识；`quality_equivalence_enabled=false` 时任何对象、任何敏感性分支都不输出等价；离群标记（标准误与 ε 之比为 0.25 的正态差值大多不标，14 个约为 0、1 个为 0.3 时标记）；旧 5 + 新 10 全部合法通过、旧 RUN 没有初始化收据、篡改槽位表、旧 RUN 冒充新 RUN、同一原件占两个槽位、第 16 个 RUN、槽位成功后再追加成功、人工改判、第 14 个槽位没有终态时请求判读、计算日志 SHA 链断开、未推送的收据（都被门禁拒绝）；未知原因的 perf 非零退出（`paused_stop`）、白名单故障且有正面证据（重采）、过热引起非零退出、stderr 丢失、只有传输中断（重传，不计尝试）、完整传输后 SHA 不一致；原因不明的暂停后有合法证据恢复（通过）、事件只有说明文字（拒绝）、空间证据的 `df` 记录正常（拒绝）、温度证据的时间戳不在失败前后 10 秒内（拒绝）、曾经空间不足但恢复时仍不足（拒绝）、曾经过热但恢复时仍不满足启动条件（拒绝）、未知退出附近有高温却没有关联的停止动作（不可恢复，进入"停止缺失"）、硬件事件错误与过热同时出现（进入"停止缺失"）、旧的人工停止命令被用于另一次尝试（拒绝）、失败处理器没有写出证据文件（拒绝恢复）、故障已消除且证据关联正确（恢复）、没有恢复事件直接追加成功收据（拒绝）、恢复事件改变采集条件（拒绝，属于协议变更）、第四次尝试停止后申请恢复（拒绝）、`stopped_missing` 后再次采集（拒绝）、硬件事件错误停止（未完成槽位进入"停止缺失"）、遥测异常或转换失败进入恢复路径（拒绝）；登记前对真实 profile 请求 M3 或分支误差（拒绝）、登记后计算 M3 没有写日志（拒绝）；固定间隔的层不产生权重比较；合成 profile 允许计算 | 待实现 |
| 11 | 性能矩阵：从登记矩阵自动校验每组参数；缺少补零对照时拒绝输出"补零默认值已验证"；质量与性能的统计量、ε、停止规则没有混用，关闭质量判读不改变性能规则；超过登记的 N 后拒绝计入新轮次；N 的公式夹具：CV 0.5% 得 13，1% 得 40，CV 为 0 得 10，CV 缺失或为 NaN、无穷时视为无法预试得 40，预试含一个离群轮次时按未剔除的 CV 计算；G0 预试数据不进入正式轮次 | 待实现 |
| 12 | 板上（需要板子，加装散热后）：root 读取 `cpuinfo_cur_freq` 可用；记录器以 `O_RDONLY \| O_NONBLOCK` 打开并 `lseek(fd, 0, SEEK_SET)` 后读到首条序号 0，无新记录时立即返回；记录开机到会话开始的时长、`CONFIG_LOG_BUF_SHIFT` 与按当时的日志速率估计的回卷时间，会话期间序号连续；端点读取接口在"两次都没有新记录"与"后台已保存窗口内记录"两种情况下给出正确窗口；日志回卷的两条路径分别验收——首条序号 0 且连续时验证完整日志路径，首条不为 0 时默认阻止采集，只有采集前已有接受 unknown 的事件才继续，该路径不记为完整日志路径通过；加装散热后的正对照只有在全部必需观测完整时才预期合格，经批准的日志不完整路径预期为 unknown；完整执行一次前后校准流程（30 秒、每个 CPU 计数有效的中间区间 ≥ 25、采样器并行时的行为）；"解码满载 + 采样器"试运行，负载期间 ≥ 99% 的读数间隔不超过 1.5 秒、没有超过 3 秒的间隔、采样器使解码耗时中位数的变化小于 0.5%；同一次试运行带采样器的 G0 耗时（至少 10 轮）用于计算 N；核对 5.9 第 5 条引用的内核函数与行号。板上不为测试而重启 | 待板上执行 |
| 13 | 覆盖参考：spike 上 lcov 的 `DA` 与 JSON 推得的行计数一致；按主文件代码区域推导的函数行范围与 lcov/JSON summary 交叉一致；主文件按 `findMainViewFileID` 的规则核对，返回空的记录单独报告，并在对应表中有明确的状态；宏区域按区域类型与 FileID 识别；副本合并夹具（3 个编译单元的同一 static inline 函数只执行 1 个、宏内部循环、同文件同时含普通函数与宏定义、同一模板文件被不同名字包含两次、两个不同的已执行函数在同一物理行）；`HasMultipleRegions` 从 segments 提取的结果与 Coverage API 一致 | 待核对 |
| 14 | 离线资格分类：执行 5.9 第 5 条列出的全部判定脚本夹具，含记录器状态（首条序号不为 0 时不开始采集、会话中 boot_id 改变而记录器没有重启、一个 RUN 的两个端点跨 boot、保存失败、输出路径不在 `/opt/afdo_agent/` 下、非阻塞描述符无新记录时及时返回；日志回卷后未授权时拒绝采集，采集前授权后允许但保持 unknown，采集后补授权不能追认，之后观测正常也不能清除 unknown）；boot_id 改变用离线模拟，不在板上重启；用第一轮与四核诊断的原件重放，重放标签不覆盖历史资格 | 待实现 |
| 15 | ③ 门槛：按新的源函数合并规则与 ③ 的分母，在 FFmpeg（Thumb、A32）与 spike 的参考上计算 ③、③′ 与按互斥原因集合分桶的损失分解（各桶之和等于 ΣR(C) − ΣR(U)）；任一对象 ③ 低于 50% 时不登记，50%–80% 时登记文本须含损失分解 | 已按 v1.7 规则计算（05 报告第 13 节）：四个对象 ③(C) ≥ 80%，三个 1% 门槛均未超限，`domain_unresolved` 为 0；FFmpeg 的 ③(C_dc) 为 49.93% / 49.88%，通过门槛依赖可测量性限定。本版新增 sequence 不重叠前提的验证与部分相交区间的报告，待随产物重跑 |
| 16 | 跨侧对应表：只用 ELF、调试文件与参考数据生成，结论状态为封闭枚举，覆盖映射范围内每个 DWARF 函数（含内联抽象源），任一没有结论时登记准备失败。夹具：左花括号另起一行与签名跨 3 行的单候选函数（通过一致性检查，正常对应）；正确候选缺失、只剩一个同名错误候选，包括 Codex 编译验证过的条件编译反例（错误定义的行号全部落在候选范围内，但两侧定义声明位置不同，不建立对应）；有键实例行号集合为空（不通过）；已完整证明无键、且三项豁免条件全部满足的空集合实例（豁免）；无键证明不完整（不得豁免）；函数自身在签名行上有一个行表行（通过）；行号落在另一个同名定义的函数体内（不通过）；裁决证据与所选编译变体不一致（拒绝登记）；名字规则：只有 `DW_AT_name`、只有 `DW_AT_MIPS_linkage_name`、名字只在 specification 或 abstract origin 上、同一 DIE 同时有两种 linkage name 属性且值不同（先取 MIPS）、当前 DIE 的标准 linkage name 与引用 DIE 的 MIPS linkage name 同时存在（与 `getSubroutineName(LinkageName)` 一致）；同一文件多个同名定义，包括条件编译导致声明行相同而函数体起点不同（判 `identity_ambiguous`）；`identity_ambiguous` 被内联进热点函数且有样本（RUN 有定义、相关行被排除）；GNU C 编译的 `libgcc2.c` 函数与 GNU AS 函数有样本（`not_instrumented`，归为范围外）；`not_instrumented` 外层含已执行参考函数的内联体（不得整组归为范围外）；只有约定的 `.__uniq.` 后缀有无不同、规范化后身份相同（正常对应）；修饰方式不同（`file.c:foo` 与 `_ZL3foov.__uniq.N`）或故意漏做后缀规范化（没有结论，登记准备失败）；完整身份清单独立于映射范围生成：范围外的顶层 static 函数名字去后缀后与覆盖侧不同、且没有被内联进任何范围内函数（登记准备失败），带 `.cold.1` 等后缀的克隆函数（登记准备失败或由裁决表给出结论），没有任何已匹配外层的未决函数、参考质量低于 1%（仍失败）；CU 文件名错误、producer 缺失或解析失败（没有结论）；外部 CU 中能对应已执行参考函数的内联体（不得归为未插桩）；clang C 编译单元中一个函数在覆盖导出中缺失（没有结论）；同一头文件在两个 CU 中的 decl_file 写法不同且只规范化了其中一种（登记准备失败）；内联帧对应到参考侧未执行的函数（计入"已对齐但不在 U 内（未执行）"）；列出名字去后缀后与已执行参考源函数相同、却不在映射范围内的全部 ELF 顶层函数并逐个裁决，裁决证据随表保存；报告 `not_instrumented` 的 CU 清单与 producer 分布 | 已生成（v1.6 规则），完整身份清单全部闭合；无键判定域按本版写明，现有实现已枚举全清单，待重跑确认结果不变；夹具状态以 STATUS.md 为准 |
| 17 | 登记前打开过的真实 profile 清单与在其上计算过的量；G0 预试的条件、轮数、原始耗时与开销，写入修订 3 的披露 | 登记时执行 |
| 18 | 性能轮数 N：按第 12 项的 G0 预试与 5.9 第 5 条的公式确定每块板的 N；无法完成预试时取 40，写明来源 | 待确定 |
| 19 | 登记：①（协议与工作模型、脚本与共用的统计实现模块、依赖、配置、对象登记表、完整身份清单、外部 CU 清单、对应表与裁决表（含单候选的定义身份证据）、映射表、地址关系表、裁决 1–4 的证据清单（系统头目录与编译命令证据、宏生成函数的逐 token 与拼接证明、C 与 S 的行表证据、`code_free_line` 清单与结构分类、无键实例证明）、C₀ 与 C、排除清单、边界排除组、U、权重、受控量清单、重采原因码白名单与证据条件、停止与恢复事件及证据记录的格式）、②（已存在输入清单）、③（完整 RUN 槽位表与既有 RUN 的初始化收据）的 SHA-256 写入修订 3，连同第 9 项的场景清单、种子、全部完整运行的代码 SHA 与结果，以及 `quality_equivalence_enabled` 的取值；修订 3 提交与推送成功的记录在正式受控量计算之前保存 | 登记时执行 |
| 20 | 裁决夹具与证据：裁决 1–4 的 synthetic 夹具（各自的正例与反例）与真实例证明随登记；规则或实现变化时重跑全部夹具，并重新生成受影响的静态产物（完整身份清单、对应表、映射表、C、U、排除清单、权重、对象登记表）及其 SHA。本版新增：O.2.2 定义体操作数正例（`OPNAME ## _pixels8`、`a ## _ ## b ## c`）与"同文本、来自另一宏定义"的反例；C 的取证——只有 S 行表见证且所在组不在映射范围的行进入 C，只改变对应表、键接受状态或映射范围时 C 的 SHA 不变，同地址两条记录、零长度区间、`end_sequence`、跨 sequence、非叶子行号 0 而叶子见证有效、取证失败记为 `domain_unresolved`；C ⊆ C_dc ⊆ C₀ 与三个口径的 ③；一行只调用一个被完全内联的函数归入 `inlined_call_site`；FNDA > 0 的宏生成函数：无见证的行在 C₀ → U 账本中带 {`code_free_line`, `macro_generated_function`}，有见证的行在 C 内、在 C → U 账本中带 `macro_generated_function`，两份账本差值为 0；同一 C₀ 与 ELF 下，某函数的对应结论在普通对应与 `macro_generated_function` 之间切换时，C 的 SHA 不变、只有 U 与账本原因改变；无键判定——漏枚举一个范围、顶层函数边界失败、删除一条键证明记录、符号化失败都不得豁免，全组无键时参考计数完整进入 `no_key_line`；特殊状态条目——纯系统头组为范围外、系统头内联进已执行函数、只含 FNDA = 0 宏生成函数的组为范围外、FNDA > 0 的宏生成函数、特殊状态组中的未登记键仍为未对齐，每条 body 记录只进入一个类别；结论输出缺少评价域说明或任一 ③ 口径时拒绝写出。v1.8 新增：`domain_unresolved` 阻止登记——Codex 的反例（额外一行已证明无见证时不可登记，同一行取证失败并以 `DA` = 210 留在 C 中时也不得变为可登记）、unresolved 的 `DA` 为 0 与非 0 都阻止、修复取证后分别取得见证或证明无见证时状态解除并重算账本、unresolved 行不因已有普通键重新进入 U、取证程序退出码非 0 或有诊断输出时全部未见证行进入 `domain_unresolved`；结论门禁——全 null、空对象、NaN、Infinity、分母为 0、三个分子不一致、ΣR(C) ≤ ΣR(C_dc) ≤ ΣR(C₀) 不成立、比值与分子分母不一致、对象 A 的数值配对象 B 的摘要、与登记表差 1、登记表 SHA 不符都拒绝，分子为 0 而分母为正的合法结果通过，失败时不创建也不覆盖文件，有效的四对象摘要继续通过；sequence 前提——同一 CU 内重叠的两条 sequence（A 为 [100,120)→行 10，B 为 [100,110)→行 20）拒绝取证，相邻不重叠的 sequence 通过，数值相同而节不同的地址不误判为同一地址空间，本次八份输入的前提检查结果写入证据索引；操作性定义——可执行节中同时有代码区与数据区、数据区有有效行表区间时允许进入 C、没有有效键时不进入 U 并完整记损失，同样的区间只与非执行节相交时不取得见证，起点为 0、长度到不了 `.text` 的 sequence 不产生见证，跨过可执行节边界的区间计入部分相交报告，结论文本不得输出"已证明每行都有指令" | v1.7 规则的夹具已实现（205 项通过）；v1.8 新增夹具待实现；登记时随产物重跑 |
| 21 | 设计文档：v1.7 连同重算结果经限定范围评审（严重问题 0 项），按附录 Q 修订为本版；按项目约定不再评审，本版新增内容以第 20 项的实现与夹具验收为准 | 设计评审已完成；待第 20 项验收 |

### Q.6 本版新写、尚未经评审的内容

本版全部修改都采用了评审方给出的方案或其合并，合并时的取舍写在 Q.2、Q.3 的"采用与理由"一栏。以下两点是本文作者在合并时作出的选择：

1. `domain_unresolved` 的 `DA` 为 0 时也阻止登记（Codex 的夹具建议中已包含这一点，本文写入正文）。
2. 结论门禁的对象登记表按修订 3 登记的 SHA 读取（Claude Code 的方案），与 Codex 的逐项一致性校验同时执行。

按项目约定，本版不再评审设计文档；上述两点与全部新增门禁以 Q.5 第 20 项的实现与夹具验收为准。
