# llvm-profgen 增强设计（第一批详细设计 + 第二、三批规划）

| 项目 | 内容 |
|---|---|
| 版本 | v0.7（第一阶段冻结版） |
| 状态 | **第一阶段已冻结**：正确性规则与契约（采集与输入、地址换算、身份、计数规则、指令边界、输出与失败契约；第 10 节步骤 2 所列范围）以本版为准，实现按本版进行；对这些规则的任何修改都要单独提出并说明理由。第二阶段（默认参数与评估判据）在评估后冻结，probe 子方案单独准入，两者在本版中仍是待定内容 |
| LLVM 基线 | Tizen llvm 包源码 `f999bd406c0a70fe8107aa992164fe6945c5d46a`（LLVM 22.1.8）；上游对照 tag `llvmorg-22.1.8` |
| 参考实现 | Google AutoFDO `f95d1a170dfe24ec5ce4117aa4b0f6d836841703`（create_llvm_prof） |
| 前置材料 | `docs/spike/01_afdo_pgo_feasibility.md`、`docs/profgen/00_incremental_build.md`、`docs/profgen/01_gap_analysis.md`、`docs/probe/03_rpi4_sampling.md`、`docs/probe/04_rpi5_probe.md`、`docs/probe/05_rpi4_pmu_image_and_prefreeze.md`、`docs/probe/06_rpi4_prefreeze_followup.md`、`docs/probe/07_v04_prefreeze_checks.md`、`docs/probe/08_buildid_split_check.md`、`docs/probe/09_rpi5_prefreeze_checks.md` |
| 适用范围 | 本文只覆盖 llvm-profgen 工具本身的增强，以及验证该增强所需的测试与评估。不包含任何 Agent 的设计与开发；Agent 在 llvm-profgen 增强完成后另行设计 |
| 评审记录 | v0.1 经 Kimi Code、Codex、Claude Code 三方评审，处理见附录 A。v0.2 依据冻结前板上核实（05、06 报告）修订为 v0.3，见附录 B。v0.3 经三方第二轮评审（结论依次为"修改后可以冻结""需要重大修改""修改后可以冻结（第一阶段）"），处理见附录 C。v0.4 未外部评审；依据 07 报告与 LLVM 包的 build-id 方案小幅修订为 v0.5，见附录 D。v0.5 经 Codex、Claude Code 第三轮评审（Kimi Code 未参加），两家结论均为"修改后可以冻结"（Claude Code 注明第一阶段）；连同 08、09 报告的结果修订为 v0.6，见附录 E。v0.6 经 Codex、Claude Code 限定范围复核，两家结论均为"修改后可以冻结第一阶段"，没有严重问题；按复核意见修订为 v0.7 并冻结第一阶段，不再另起一轮，处理见附录 F |
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
4. 结构覆盖门槛：分别报告两侧条件终结指令中通过严格匹配的比例；暂定两侧都不低于 95%（第二阶段在 spike 与 libavcodec 上按第 3 条新规则重算后确认，br 与 switch 都按第 3 条的负对照重新计算；语义校验收紧后严格匹配率可能下降，必须据实重定门槛，不得为达到 95% 放宽语义校验）。该门槛只表示结构覆盖，不表示执行覆盖。跨终结指令的 `branch_weights` 之和只作描述性统计，不称为执行次数，也不作门槛。06 报告中的 97.78% / 95.65% / 100% 是旧规则下的结果，不能作为新规则的验收值。
5. 指标：
   - 主指标（第一批）：对严格匹配、且参考概率有定义的分支，计算分支概率误差，同时报告匹配范围与未匹配原因。
   - 执行加权的参考：用 `-fprofile-instr-generate -fcoverage-mapping` 加 `llvm-cov export` 得到行级真实执行计数，评估行级热点召回与按执行次数加权的行级误差；`.profdata` 的函数级计数作函数级参考（热点函数覆盖、函数级 Spearman，Spearman 只作辅助，因为 IP 总量反映时间、插桩总量是执行次数）。
   - 块计数重叠度、按执行次数加权的分支误差、热块召回：需要经验证的块/边绝对计数恢复方法。候选方法（第 10 节步骤 1 验证）：在插桩参考构建中读取 BFI 的块计数（例如 `-mllvm -print-bfi`），先证明其与 profdata 计数一致。未验证前这三项标为"未核实"，不用于默认值决策。
   - 已知局限：sample 侧加了 `-disable-sample-loader-inlining`，内联体的 profile 被合并或缩放到函数本体，测得的是函数本体的标注质量，不等于生产编译中带内联的效果。
6. 统计判据：
   - 每种配置至少独立采集 5 次，用 bootstrap 对配置间的差值（或相对收益）求 95% 置信区间；预先给定实际等价区间 ±ε（在第二阶段冻结前与评估计划一起确定）。
   - 差值区间完全落在 ±ε 内才判为等价；跨越边界时记为"证据不足"。证据不足时可以按复杂度或参考实现对齐选择保守配置（5.4.4 第 5 条），但不得称为统计等价。
   - 做低、中、高三档样本预算的敏感性分析。
7. 指标区分度的验证（负对照）：
   - 使用热点分布已知不同的受控工作负载，验证指标能识别差异；同时加入热点相同的不同输入，作为"不应强判退化"的对照。
   - 随机扰动（函数内计数打乱、行偏移整体平移）固定种子、重复多次，并确认扰动确实改变了参考分布。
   - 身份冲突只用于测试身份拒绝，不尝试绕过；需要评估"错误内容"时，使用显式缺失身份的测试 fixture，或在评估脚本中构造损坏的 profile，不为此增加生产接口。
   - "另一份真实输入"作为泛化测试，不要求其必然更差。
8. 可选对照：在 x86_64 主机上构建指定版本的 create_llvm_prof，用 `--use_lbr=false` 处理 RPi5 的 perf.data（它自带 perf.data 解析，是否需要主机 perf 在评估阶段确认），对齐 sample/period 语义后比较，不把它当作真值；如果 x86 主机支持 LBR，在主机上运行 spike，用同一份 perf.data 同时生成 LBR profile 与 IP profile 作为上界参考。
9. 输入与分阶段：训练输入与测试输入分开（不同视频）。先在 spike 上评估"聚合方式 × skid × 权重方式"，再在 libavcodec 上评估补零策略与 head 策略。armv7l 的评估构建按第 9 节要求（含 `-mthumb`），另做一组 `-marm` 构建覆盖 A32。06 报告中的人工 sample profile 只作为匹配器的结构测试，不作为统计质量证据。
10. 对象与板子：spike 测试程序；libavcodec（FFmpeg H.264 解码）。RPi5 与 RPi4（新镜像）都用 cycles。
11. 决定：默认值由测试输入上的性能（5.9）、统计判据（第 6 条）与实现复杂度共同决定，不只取训练输入上指标最好者。libavcodec 热点中 `outside_dwarf_func` 的占比与分类、Thumb/A32 的样本占比（`isa`）写入结论。

### 5.9 编译端选项与性能评估（不改 clang）

1. 显式控制：
   - 编译步骤统一用 `-fno-sample-profile-use-profi -mllvm -sample-profile-use-profi=<true|false>` 关闭驱动的自动注入并显式指定 profi；stale matching 显式用 `-mllvm -salvage-stale-profile=<true|false>`，单独评估它时固定 `-mllvm -salvage-unused-profile=false`。
   - LTO 构建时，链接步骤必须传入同一个 `-fprofile-sample-use=<profile>`（驱动据此给链接器传 `sample-profile=`，`CommonArgs.cpp:1253–1259`），并显式指定 profi、`salvage-stale-profile` 与 `salvage-unused-profile`：编译阶段的 `-mllvm` 参数只转发给 cc1 作业（`Clang.cpp:7680–7690`），链接参数的构造（`CommonArgs.cpp` 的 `addLTOOptions`、`Gnu.cpp`）不处理编译命令中的 `-mllvm`，所以链接步骤必须自己带上。lld 的写法为 `-Wl,-mllvm,<选项>`；其他链接器的写法未核实。
   - 用 `clang -###`、链接命令、profile 属性与 IR（LTO 时含 post-link IR）核对实际生效的配置；覆盖率与陈旧度诊断在实际运行 sample loader 的阶段核对（LTO 时为 post-link）。
   - LTO 组另加负对照："编译有 profile、链接漏传 profile"。
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

   若有目标包使用 LTO，另加 G1 的 LTO 变体，用 `-Wl,-mllvm,-print-after=sample-profile` 检查 post-link IR 中的 `function_entry_count`。

3. 消费端检查（每组）：`-mllvm -sample-profile-check-record-coverage=<N>`、`-mllvm -sample-profile-check-sample-coverage=<N>`（`SampleProfileLoaderBaseUtil.cpp:26–34`）、`-mllvm -report-profile-staleness`；在 IR 中检查 `function_entry_count` 是否存在且合理（G2 组另观察目标函数的入口计数值与冷标记），以及是否有等于 4294967295 的 branch_weights（饱和）。
4. `-fprofile-sample-accurate`：会把未采样的调用点和函数都按 0 处理（`SampleProfile.cpp:151–155`），并忽略 profile 符号列表（`:1987–1989`）。不作为稀疏 IP 的推荐默认，只在评估中观察。profile 符号列表会让列表中的符号被视为"计数准确"（`ProfileAccurateForSymsInList` 默认为 true，`:162–165`），所以第一批禁用 `--populate-profile-symbol-list`。
5. 性能测量（仅用于验证本增强）：
   - RPi5 与 RPi4 各自在 FFmpeg H.264 解码上测；固定编译、链接、LTO 参数、解码工作量与线程数。库按第 9 节的构建要求构建。
   - 每组至少 10 轮，各组交错执行，丢弃预热轮（注册表扫描）。RPi4 视方差加量：旧镜像 720p 基线的最大最小差为 2.04 s，均值 12.31 s，相对差约 16.6%（`03_rpi4_sampling.md` 第 4 节）。
   - 固定 cpufreq governor；记录 `scaling_cur_freq`、`/sys/class/thermal` 与节流、后台负载；记录镜像 BUILD_ID、内核 `uname -v`、实际加载的 libavcodec build-id、换出统计 pswpout（新镜像的 force_reclaim 修复会真正换出到 zram）。
   - 保存全部轮次；异常判据预先定义（例如换出明显增加、发生节流），同时报告剔除前与剔除后的结果；报告中位数与组间差值的 95% 置信区间，按 5.8 第 6 条的等价区间判读。
   - 每轮核对解码输出的校验和一致。训练用的视频与测量用的视频不同。另用 `perf stat` 的 cycles 与 instructions 作为噪声更低的辅助指标（两板都可用）。
   - "未证明改善"是允许的结论。
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
| 1 | 冻结前验证（一次性原型与素材，不构成正式实现）。已完成项见附录 B、D、E。★ 为第一阶段冻结的前置条件，**全部 ★ 项已闭合**：<br>已由 07 报告完成：调试文件保留映射符号与 `.ARM.attributes`、代码节为 NOBITS；Thumb 边界在 libavcodec 最大的 20 个 Thumb 函数上与 `llvm-objdump --triple=thumbv7a -d` 逐条一致（132,859 个起点，A32 只覆盖到 3 个启动代码片段，由 lit 的 A32 fixture 补足）；不 exec 的 fork、exec 替换、`(deleted)`、内核模块的真实样例；平台默认链接不生成 build-id 的原因。<br>★ 已由 08 报告闭合：当前工具链显式 `-Wl,--build-id=sha1` 构建，拆分后运行文件与调试文件的 build-id 都是可读的 SHT_NOTE、20 字节一致，`.build-id` 链接正确。08 未验证 DWARF5 行表质量，未重跑指令边界。<br>★ 已由 09 报告闭合：RPi5 的 dsoff 输出与公式核对（单进程、双进程均 100%）、`--buildid-mmap`（libc 的 MMAP2 build-id 与 ELF 一致）；RPi5 页大小 4096。<br>非 ★，交付前（步骤 9 之前）完成：LLVM 打开 `ENABLE_LINKER_BUILD_ID` 发布后，用新工具链原样构建复核默认 build-id 与拆分结果；aarch64 的 Tizen debuginfo 是否保留 `$x`/`$d`（5.7.2 第 2 条）；用 GBS 打包一个 `-fpseudo-probe-for-profiling` 构建，记录 `.pseudo_probe`/`.pseudo_probe_desc` 拆分后位于哪个文件（5.1.4 第 3 条）；把第三轮评审实测的 DWARF5 拆分核对（行表逐行、抽样符号化、`comp_dir`）与 BUILD 目录产物 build-id 不同的结果补存为仓库证据；`[unknown]` 的真实样例（未出现时按源码格式编写素材）。<br>第二阶段前完成：aarch64 与 armv7l（按第 9 节构建的 Thumb 构建，A32 构建作附加覆盖）按 5.8 第 3 条新规则重跑 IR 匹配，并试验共同转储点；验证 BFI 块计数恢复方法；<br>是否获取主机 perf（用户决定，5.2.4） | 证据评审 |
| 2 | 第一阶段冻结：正确性规则与契约（5.1–5.4、5.6、5.7、5.10–5.12） | **已冻结（v0.7）**，可以开工 |
| 3 | （可选）在 discourse.llvm.org 发 RFC，征求选项命名与整体方案意见。是否发、何时发由用户决定 | 用户决定 |
| 4 | 实现补丁 1–7；回归与新增测试；独立核对；板上集成用例 | 代码评审 |
| 5 | 5.8 质量评估（RPi5 与 RPi4） | 评估结论评审 |
| 6 | 5.9 性能与过期复用测试 | 结果评审 |
| 7 | 第二阶段冻结：默认参数（聚合方式、head、补零、skid、各门槛）与评估判据（等价区间、结构覆盖门槛） | 评审 |
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
| IR 层对齐只覆盖部分分支，或候选键相同而语义不同 | 评估指标失真 | 严格候选验证、操作数等价定义、条件规范化、switch 先校验选择值再按 case 值配对、`unknown` 处理、结构覆盖门槛（5.8 第 3、4 条）；不把跨分支的 IR 权重之和解释为执行覆盖 |
| probe 到地址的映射不正确 | probe 计数偏差 | 独立准入；正确性不过则不进正式包（5.5） |
| `-fpseudo-probe-for-profiling` 本身影响优化 | 收益被抵消 | G6 单独测量 |
| 多次采样结果不稳定 | 默认值决策不可靠 | 重复采样、差值置信区间与等价区间、样本预算敏感性分析，不只重复计时 |
| 测量噪声与热降频 | 性能结论不可靠 | 10 轮以上、固定 governor、记录频率与温度、置信区间（5.9） |
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

1. `--ip-aggregation` 的默认值（`sum` / `max` / `avg`），以及证据不足时是否按 5.4.4 第 5 条保守选择 `max`。
2. `--ip-head-samples`、`--ip-zero-fill`、`--ip-skid` 的默认值（5.4.6–5.4.8，由 5.8、5.9 的分组评估确定）。
3. 三个门槛（`--ip-min-usable-ratio`、`--ip-min-target-samples`、`--ip-max-lost-ratio`）是否设默认值及取值，按真实库的汇编占比确定（5.6.2）。
4. 5.8 的评估判据：结构覆盖门槛（暂定 95%，按新的语义校验规则重算后确定）、实际等价区间 ±ε、BFI 块计数恢复方法是否可用。
5. 是否在 discourse.llvm.org 发 RFC，以及 `--ip-samples` 的最终命名（第 10 节步骤 3）。
6. probe 子方案的准入（5.5），以及是否为 x86_64 主机构建 perf、让 `--perfdata` 进入交付（5.2.4，用户决定）。

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
