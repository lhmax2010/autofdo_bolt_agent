# 第一批评估准备：R 插桩类型与指定 IR 转储点冲突处停止

2026-11-04。**本轮未完成评估准备，按用户停止条件停止。** 已登记两项 probe 裁决，并以 GBS 平台 Clang 22.1.8 复现：任务给 R 指定的 `-fprofile-instr-generate` 生成前端插桩 profile，使用该 profile 时不会运行设计 5.8 第 2 条指定的 `pgo-instr-use` pass。没有该转储，不能把空文件当作参考 IR 交给匹配器。此处是任务 flags 与设计所选流程的冲突，**不是 llvm-profgen 缺陷，也不是编译失败**。

未修改 LLVM、llvm-profgen、冻结设计、现有 spec 或配置；未连接板子、未推 LLVM/Gerrit、未启动 GBS/FFmpeg 构建。报告中的对照只用于定位流程冲突，不替代任务授权的 R 构建定义。

## 1. 已生效的裁决

- “pseudo-probe 拆分后节的位置”按 aarch64 证据关闭。报告 10 的 [拆分证据](evidence/10/07_aarch64_split.json) 已覆盖运行文件带节、仅 debug 带节两种 IP 拒绝；节名检测与架构无关，不要求通过 ARM 崩溃重做才能闭合该项。
- armv7l 平台 Clang 22.1.8 的 `-fpseudo-probe-for-profiling` 崩溃只挂在设计第 10 节步骤 8 的 probe 子方案下，不阻塞第一批 DWARF 路径。本轮没有定位或绕过崩溃；原始材料仍见 [10 的停止证据](evidence/10/09_stop.json)。本轮停下的原因是下面独立的 R 流程冲突。

## 2. 停止证据：前端插桩不产生指定的 pass 转储

原始证据：[01_reference_instrumentation.json](evidence/11/01_reference_instrumentation.json)，含完整复现脚本、C 源、每次实际命令/cwd/退出码/完整 stdout/stderr、生成及消费 IR、手写 profile 输入和结果。源码摘录：[02_source_and_prior_config.txt](evidence/11/02_source_and_prior_config.txt)。临时原件位于 `temp/eval-prep11/`。

### 2.1 平台工具与方法

- clang：`temp/GBS-ROOT-RPI5-SPIKE/local/BUILD-ROOTS/scratch.aarch64.0/emul/usr/bin/clang`，版本 22.1.8；经同 emul 的 `lib64/ld-linux-x86-64.so.2 --library-path <emul>/lib64:<emul>/usr/lib64` 调用。
- llvm-profdata：`temp/GBS-ROOT-LLVM-X86/local/BUILD-ROOTS/scratch.x86_64.0/usr/bin/llvm-profdata`，经该 root 的加载器与库调用。没有调用主机安装的编译器。
- 小 C 函数 `reference(int x)` 根据 `x > 7` 返回 `x * 3` 或 `x + 11`。目标 aarch64，无系统头、无链接、无目标程序运行。公共参数为 `--target=aarch64-tizen-linux-gnu -ffreestanding -O2 -g -fdebug-info-for-profiling -funique-internal-linkage-names -mllvm -disable-preinline -S -emit-llvm`。
- 分别加 `-fprofile-instr-generate` 和 `-fprofile-generate` 生成 IR；从各自 `__profd_reference` 读取函数 hash 与计数器数目。前端 hash 为 11211998296，IR hash 为 382993475055910911，均有 2 个计数器。
- 为各自正确的 hash 写合成 instrumentation 文本，计数为 100、30；IR 文件带 `:ir` 标记，前端文件不带。用平台 `llvm-profdata merge` 生成索引文件，再以 `show --all-functions --counts` 确认类型。**这些是合成计数，不是实际采集，更不作为质量/性能结论。**
- 使用两份 profile 时均加 `-fprofile-use=<文件> -mllvm -print-after=pgo-instr-use`，其余上述 flags 相同。最终 IR 都带 `function_entry_count`，没有 profile 不匹配告警；因此“无转储”不是 profile 未被读入。

### 2.2 实测结果

| 生成选项 | cc1 实际参数 | profdata show 类型 | 生成 / merge / show / 使用退出码 | pgo-instr-use 转储次数 | 使用阶段 stderr |
|---|---|---|---|---:|---|
| 任务指定：`-fprofile-instr-generate` | `-fprofile-instrument=clang` | Front-end | 全部 0 | 0 | 0 字节 |
| 仅作诊断对照：`-fprofile-generate` | `-fprofile-instrument=llvm` | IR | 全部 0 | 1 | 3,933 字节，完整 IR 转储 |

IR 对照的 stderr 首行原文：

```text
; *** IR Dump After PGOInstrumentationUse on [module] ***
```

前端侧 stderr 为空，原样保留在 JSON；不能给它虚构错误消息或非零退出码。`-disable-preinline` 不会把前端插桩转换成 IR 插桩。只修改消费者 flag 也不能改变 profile 内记录的插桩种类。

### 2.3 源码依据

| 结论 | 当前源码位置 |
|---|---|
| `-fprofile-instr-generate` 选择 Clang 前端插桩 | `src/llvm/clang/lib/Driver/ToolChains/Clang.cpp:414–432` |
| `-fprofile-generate` 选择 LLVM IR 插桩 | 同文件 `:477–484` |
| 消费时读取 profile 的类型，选择 `-fprofile-instrument-use=clang/llvm` | 同文件 `:504–531` |
| 只有 `hasProfileIRUse()` 建立 `PGOOptions::IRUse` | `src/llvm/clang/lib/CodeGen/BackendUtil.cpp:846–863` |
| IRInstr/IRUse 才进入预内联和 PGO instrumentation pass 路径 | `src/llvm/llvm/lib/Passes/PassBuilderPipelines.cpp:1218–1222,1240–1250` |
| 设计要求使用 `pgo-instr-use` 后的 IR，并说明生成/使用两侧关闭预内联 | `docs/profgen/design/02_llvm_profgen_enhance_design_v0.7.md:487–490` |
| coverage 参考另外指定前端插桩与 coverage-mapping | 同设计 `:503` |

### 2.4 候选方案（均未实施，需用户决定）

1. **推荐**：R 的生成改为 `-fprofile-generate -mllvm -disable-preinline`，使用侧仍 `-fprofile-use` 加 `-disable-preinline`，保持设计指定的 IR 参考路径；C 保持 `-fprofile-instr-generate -fcoverage-mapping`，R/C 分开。G5 是否仍采用用户本轮明确的前端插桩，或改成正常 flags 的 IR 插桩对照，需一并明确，不能由本轮擅自改动。
2. 保持 R 的前端插桩，但另选前端标注后的 IR 转储位置，并重新核对优化管线、权重语义、与 sample 侧的可比性；这需要明确调整本轮“pgo-instr-use 后”要求以及设计中的相应评估流程，不能直接以优化结束时的 IR 替代。

在方案 1 下 R/C 不能当作同一次插桩生成构建：两种 profile 类型和标注路径不同。若采用方案 2，R/C 合并仍需单独验证，本轮不作已可合并的结论。

## 3. 评估准备的实际完成范围

| 请求项 | 当前结果 |
|---|---|
| IR 新语义匹配器、负对照与 bootstrap | 未开始；没有测试通过数，不沿用旧原型结果 |
| 真实 count_loop/two_sites IR 冒烟 | 未运行新匹配器；前轮消费证据仍有效 |
| S/R/C/G5 × Thumb/A32/aarch64 最终变体表 | 未定案，先裁决 R 的生成方式；A32 的 R/C/G5 范围未定 |
| 两 root 的目标 profile runtime | 尚未完成有效性核对；初步路径搜索未得出结论，不宣称平台缺少运行库 |
| LTO 与第 9 节选项 | 只复核旧 08：`temp/v05/config_after.mak:51,75` 所列 CFLAGS/LDFLAGS 无 `-flto`，带 `-mthumb`/显式 sha1，缺两个 profiling/唯一命名选项；不能外推为新两架构变体全部已核对 |
| FFmpeg spec/宏变体与代表性源文件编译 | 未改、未运行；旧 spec `temp/v04/ffmpeg/packaging/ffmpeg.spec:232–248` 与配置保持原样 |
| spike RPM/debuginfo 构建及 build-id | 未开始，无本轮 RPM、无可报告的新 build-id |
| 板上脚本、计划、视频盘点 | 未开始，没有连接板子 |

08 的旧配置是 `temp/gbs/gbs_v05_ffmpeg.conf` 的 reference Base/Unified 仓库，不能写成固定快照；更完整的旧构建结论见 [报告 10 第 6 节](10_host_verification.md#6-评估构建需要注意的事项)。本轮不以旧对象冒充新 S/R/C/G5 构建。

## 4. 夜间构建启动方式

**尚未提供可执行的夜间构建入口，不能启动。** 变体定义在上述冲突处停止，`eval_build_night.sh` 未创建，也没有做 bash -n 或空跑。启动命令、FFmpeg 总时长及每板计划时长待裁决后实际完成准备再给出；本轮不提供未经验证的命令或估时。没有任何后台 GBS 构建，因此也没有本轮 GBS ALL-END 或需监测的进程。

## 5. 待设计 v0.8 登记

- 按用户本轮裁决，“pseudo-probe 拆分后节的位置”由 aarch64 实测闭合；节名检测与架构无关，两种位置拒绝已经验证。
- armv7l Clang22.1.8 probe 崩溃属于第 10 节步骤 8 的 probe 子方案阻塞，不阻塞第一批 DWARF 路径。
- 新发现待裁决：R 的前端插桩生成与 5.8 第 2 条指定 IR pass 转储不兼容。上节候选方案尚未实施，不把它写成已通过的设计变更。

## 6. 范围审计与后续

[03_scope.json](evidence/11/03_scope.json) 记录工具/设计 SHA、LLVM HEAD、工作树状态和保留的 spec diff SHA。正式 profgen SHA 仍为 `334a09290f53eb4c793ae91759f2b6344a36e63317820eb9151771b262dc3f30`；本轮未运行或重编它。v0.7 SHA 仍为 `eec6b208d8e1fedb840f0933eb20a37c188890b6c8c29e43986c5c9bbca9f6be`。

所有本轮主动创建文件在 WORKDIR 内，平台编译以 nice19/ionice3 顺序执行；不使用板子、不安装包、不读取外部项目材料、未索取密码。**无本轮新增已知边界例外**；没有做 WORKDIR 外文件扫描。原有用户未跟踪配置未纳入提交，LLVM 工作树现有 spec 测试改动保留不动。

本次只交付裁决登记、可复核的停止证据与候选方案。用户明确 R 流程后恢复剩余准备；尚未完成的测试/构建/夜间入口/板上计划不能视为已交付。
