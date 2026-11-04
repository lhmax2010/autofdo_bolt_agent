# 第一批评估准备：裁决记录、主机工具与构建验证

> 最新续执行从第7节开始；第1–6节为此前停止记录，保留审计。本轮主机准备及24项生成侧构建已完成；板上尚未执行。

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

---

## 7. 裁决后恢复：最终任务范围与变体定义

以下为用户裁决后的续执行；第1–6节保留此前停止时的原始记录，其“未开始/未构建”仅描述当时状态。R生成改用IR插桩，FFmpeg不再拆到夜间任务；本轮只在主机执行，板上操作均为脚本/计划。

| 类型 | 生成侧选项（公共flags之外） | 后续消费/用途 |
|---|---|---|
| S | 无插桩；profiling debug、唯一内部名、SHA1 build-id | cycles采样；未来G0基线 |
| R | `-fprofile-generate -mllvm -disable-preinline` | `-fprofile-use=<R.profdata> -mllvm -disable-preinline -mllvm -print-after=pgo-instr-use`，只作IR局部分支参考 |
| C | `-fprofile-instr-generate -fcoverage-mapping` | llvm-cov export行覆盖参考 |
| G5 | `-fprofile-generate`，不加disable-preinline | `-fprofile-use=<G5.profdata>`，生产flags插桩PGO对照 |

公共项为平台`%{optflags}`、`-fdebug-info-for-profiling -funique-internal-linkage-names`，链接`-Wl,--build-id=sha1`，不加pseudo-probe；Thumb显式`-mthumb`，A32显式`-marm`，aarch64沿用目标平台flags。**本轮G5是生成侧，不是已经训练后的优化版本**；板上训练完成后才构建R-use、G1–G5-use。本轮不伪造训练数据。

| 对象 | RPi4 armv7l Thumb | RPi4 armv7l A32 | RPi5 aarch64 |
|---|---|---|---|
| spike | S / R / C / G5 | S / R / C / G5 | S / R / C / G5 |
| FFmpeg（libavcodec） | S / R / C / G5 | S / R / C / G5 | S / R / C / G5 |

ISA标签指本轮C源的编译选项，不承诺整个链接产物为纯ISA：例如spike A32 S的debug含24个$a与4个$t；A32 R含65个$a与159个$t。链接进来的既有代码也保留自己的映射状态，不能为“A32组”强行把所有地址当A32。完整映射计数随产物留证。

共24项生成侧构建。设计5.8第9条要求另一组A32覆盖；本轮选择完整A32 R/C/G5，以便A32统计质量和性能都有同ISA参考，不能以Thumb参考冒充A32。R/C的profile类型、计数插入点与用途不同，分开；R/G5按裁决保留两份，避免预内联差异污染生产对照。第2节源码与实测是R/C不能直接合并的依据。

### 7.1 工具链、LTO、源码路径和构建输入

[06_build_inputs.json](evidence/11/06_build_inputs.json)保存本地提交、完整spec、FFmpeg改动diff、全部GBS命令、配置SHA、工具包装器及代表性编译脚本。原`src/ffmpeg`不改，本地包仓库为`temp/eval-prep11/ffmpeg`与`temp/eval-prep11/spike`，不推远端。FFmpeg基于08相同源提交，公共唯一名/debug选项、ISA与插桩宏是评估改动；开启V=1仅让实际命令留证。spike源来自`spike/afdo-spike/spike.c`，同源SHA留证。

- ARM FFmpeg沿用`temp/gbs/gbs_v05_ffmpeg.conf`与独立V04 root；ARM spike用`temp/gbs/gbs_host_check_arm.conf`与RPI4-SPIKE root。它们是此前08/10已使用的**reference仓库**，不称为镜像固定快照。
- AArch64用`temp/gbs/gbs_rpi5_image.conf`与RPI5-SPIKE root，Unified 20261027.063617、Base 20261026.051209。配置文件不改，用户config目录不改。
- 两平台Clang22.1.8。ARM `compiler-rt-22.1.8-1.6`、aarch64 `compiler-rt-22.1.8-1.5`都有对应profile静态运行库；分别由GBS平台readelf确认19个ARM/AArch64 ELF成员。开始时scratch未安装不能等同仓库不存在，先核对缓存RPM，再由BuildRequires交GBS处理。主机不安装RPM。
- 平台配置`temp/gbs-tmp-v04-ffmpeg/linhao-gbs/tizen_unified_standard.conf`及`temp/gbs-tmp-spike/linhao-gbs/tizen_unified_standard.conf`中armv7l optflags含mthumb/neon/softfp（366行），aarch64含cortex-a53（368行）；编译器宏在143/153行。spec、展开的config.mak以及实际命令未启用`-flto`。因此本轮没有post-link sample loader；后续若增加LTO，编译和链接都须给`-fprofile-sample-use`，lld链接另给`-Wl,-mllvm,-sample-profile-use-profi=<...>`、`-salvage-stale-profile=<...>`、`-salvage-unused-profile=false`，不能靠编译的-mllvm自动传播。
- FFmpeg configure按原配置追加O3；spike按平台optflags的Os。它们是各自对象内部一致的基线，不把不同对象的绝对时间直接比较。
- 各变体的Name/Version及`BUILD/ffmpeg-8.0.1/libavcodec/...`、`BUILD/eval-spike-1.0/spike.c`不变，只改变Release/宏；同一对象跨ISA的chroot内路径也保持一致。避免改变唯一内部名依赖的源码路径。保存每份RPM、安装后runtime/debug的ID；**不以BUILD目录的未打包ID替代部署ID**。

### 7.2 代表性源文件门禁

对全部12个ISA×类型，先按相同configure参数产生配置头，使用GBS root平台clang编译`libavcodec/h264_cabac.c`，同时保存`clang -###`、对象`.GCC.command.line`和映射符号。12/12通过后才启动完整构建。修正configure参数分隔空格后，再重跑12项全部通过。

[05_representative_checks.json](evidence/11/05_representative_checks.json)为逐项断言；[05b_representative_commands.json](evidence/11/05b_representative_commands.json)为完整命令、退出码、driver输出及对象记录。检查包括两项profiling flags、ISA、IR/前端插桩种类、coverage开关、仅R关闭preinline。编译对象只留`temp/eval-prep11/preflight/`。配置阶段几次本轮包装器设置错误保留在`temp/eval-prep11/configure/a64-setup-attempt*.json`，最终使用GBS加载器的`--argv0`和`-no-canonical-prefixes`让子cc1仍走同一平台工具；没有改源码或降低要求绕过。

## 8. 新IR语义匹配器与统计工具

脚本为[match_ir_semantics.py](../../../tools/profgen/match_ir_semantics.py)，不是旧原型结果续用。旧原型只提供metadata/br/switch文本抽取思路，配对及判定重新实现。

- 候选键是函数+完整DILocation语义（作用域、file、line/column、inline链、discriminator等），不使用两模块的metadata编号或SSA名字配对；重复键拒绝配对。
- 参数按同函数序号和类型；整数常量按类型/位模式；白名单整数运算、icmp、整数cast、select递归比较opcode、类型、arity、语义flags和操作数，默认深度16可配置。load/call/PHI/undef/poison及不支持表达式保守记unverified。浮点、向量等未实现的等价证明也不放行。
- 条件取反交换后继；只规范化无语义flags的xor true，不能丢掉disjoint等标志。switch按位宽case/default配对。每个后继首DILocation必须存在、彼此不同并对应。
- 缺权重、expected权重、形态差异分别分类；不能用entry count补零。诊断指定的未匹配/部分忽略函数整体排除；无法定位函数的相关诊断保守排除全模块。严格匹配主比例使用两侧全部条件终结指令作分母；另列函数排除后子集的eligible比例和两种分母，避免通过排除抬高主比例。
- 参考权重和为0不进概率误差分母；sample和为0也不给虚构概率。每条严格分支输出有符号和绝对概率误差。结构比例不是执行覆盖率，跨分支权重之和不作执行计数。

[04_semantics_and_bootstrap.json](evidence/11/04_semantics_and_bootstrap.json)含23组手写IR对的逐例预期/结果、46份IR的GBS llvm-as检查（均成功）、真实Clang输出冒烟和测试原文。14个unittest方法通过，其中IR fixture方法覆盖23对，7个bootstrap测试。覆盖任务全部负对照，另含参数改名、case重排/位宽、语义flags、零参考权重等。原始fixture在`tools/profgen/tests/ir/`。空IR、截断函数体及不支持的函数头显式拒绝，不能把未取得转储当成零分支成功。

真实冒烟读报告10的a64/Thumb text/extbinary消费IR（包含count_loop/two_sites），每组1条条件分支，因PHI选择值保守不匹配；两组输入是不同格式profile的sample消费者，**只证明可读取Clang22输出，不宣称R-vs-sample质量通过**。最终板上训练后的R与sample IR还要按本工具重算，不能沿用06原型的匹配率。

[bootstrap_equivalence.py](../../../tools/profgen/bootstrap_equivalence.py)默认固定种子20261104、20,000次bootstrap，至少5个独立观测；默认中位数/独立重采样，另支持均值与明确配对的数据。输出candidate−reference的95% percentile CI、`100*(reference−candidate)/reference`相对收益CI，完全落入用户给定±ε才等价，否则证据不足。参考值非正时相对收益未知，不丢掉该轮；差值仍可计算。本轮没有为实际数据决定ε，也没有统计收益结论。

## 9. 构建脚本、实际过程与产物

入口[eval_build.sh](../../../tools/profgen/eval_build.sh)，worker[eval_build.py](../../../tools/profgen/eval_build.py)。顺序执行24变体，不读终端；先检查代表性门禁、源码HEAD/干净状态与配置SHA，nproc非空后取一半并发。本机20CPU所以-j10，GBS --threads1，nice19/ionice3。GBS及子进程独有HOME隔离与GIT_CONFIG_NOSYSTEM；整个worker setsid脱离会话并继承锁，GBS另用setsid --wait取得真实退出码。每个变体保存开始/结束/真实RC/RPM SHA，资源每600秒free/uptime；成功、失败、可捕获中断都写带时间ALL-END。启动后另补了源/config哈希和预检异常收尾保护；实际队列使用启动时已载入的worker版本，这些新增失败路径仅做静态检查与正常空跑，没有人为触发后再构建。SIGKILL/断电无法由进程trap保证，明确属于运行环境限制。

启动方式（已执行；不要在已有worker运行时另起）：

```bash
/bin/bash /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/tools/profgen/eval_build.sh --dry-run
/bin/bash /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/tools/profgen/eval_build.sh
```

先bash -n与空跑通过；stdout末尾单独给出tail/cat进度命令。开始前及每变体前检查其他会话重任务，有则每600秒等待，不结束其他进程。实际重跑FFmpeg的命令带`--object ffmpeg`，避免重复已经完成的spike。

本轮自己的准备错误如实保留：attempt01漏`--overwrite`导致第二个同包变体被GBS跳过，虽然GBS返回0，产物非空门禁拒绝，ALL-END FAILED；补上后attempt02完整生成12个spike。随后首个FFmpeg在configure阶段因新增`--enable-thumb`后缺分隔空格失败（GBS1），修正本轮spec后重做12项门禁，再从FFmpeg队列开始。两个失败日志和状态均未覆盖，放`temp/eval-prep11/build/attempt01/`、`attempt02/`。

24项最终构建均GBS_EXIT=0，并生成RPM/debuginfo。ID表为实际RPM安装内容的runtime与debug共同ID；其余FFmpeg ELF完整ID见[08b](evidence/11/08b_all_ffmpeg_elf_ids.json)。全部RPM路径、大小、SHA与起止时间见[07](evidence/11/07_builds.json)，目标编译/链接命令及ELF节/映射符号计数见[08](evidence/11/08_artifacts.json)。

| 变体 | GBS秒 | runtime = debug SHA1 build-id |
|---|---:|---|
| spike-thumb-S | 20.00 | `322b4f1082e030032b3a85eb599e2bdfbe37797d` |
| spike-thumb-R | 20.00 | `2d4962a0a428f77b1c52988c17e8573c16c7755e` |
| spike-thumb-C | 20.00 | `32d5cebeddcff17b6e42d5cc21e6adb6eaf4943c` |
| spike-thumb-G5 | 20.00 | `1215990e265f8b37652b176ecccf501680c345cc` |
| spike-a32-S | 20.00 | `9993b1fe8d154d2deda012358f47a87078214a98` |
| spike-a32-R | 20.00 | `e9586fadc34328dda341e6066379226807edbc84` |
| spike-a32-C | 20.00 | `413a325ca1ccf531c835001bbd1f8624b06819a1` |
| spike-a32-G5 | 20.00 | `7d0612002d39c330e660b3ccd6cbae1ea88ee1b2` |
| spike-a64-S | 26.00 | `597a6af4e628152cddd3fb3edc18f4153982a9da` |
| spike-a64-R | 18.00 | `f07577603cdf73ff122bde97c43333881c74cee0` |
| spike-a64-C | 18.00 | `5484556d0ef9ff7213df11117727fc20dadff498` |
| spike-a64-G5 | 18.00 | `8f884245b83cd97446bc6ba8edd62742ef1bf3ef` |
| ffmpeg-thumb-S | 92.01 | `e7de4d8c9560442994341d9bfc5dfd06ae641a17` |
| ffmpeg-thumb-R | 90.01 | `0012f15c9617a508f7bfcfca0273a33e2be8d6db` |
| ffmpeg-thumb-C | 98.01 | `07d083e754ba0c5162c08fc054644807bc140a8f` |
| ffmpeg-thumb-G5 | 98.01 | `181f5a159c3927432588e57a3897bdee4106b352` |
| ffmpeg-a32-S | 94.01 | `b3b8b19e8277641331bab478a94c2d5636075c14` |
| ffmpeg-a32-R | 122.01 | `236a95df1407cfce0e5960c4601c2e14150ad375` |
| ffmpeg-a32-C | 198.03 | `b262c36697a0957d48c691b1bcad8b0517465741` |
| ffmpeg-a32-G5 | 262.02 | `d426c555f71c96c01c9719ac0627e64f86248151` |
| ffmpeg-a64-S | 434.03 | `9b59f8982a668ca39e0c87cdfe455eec19810654` |
| ffmpeg-a64-R | 482.03 | `b917556c617f8526a57049a87b7dfcce87450171` |
| ffmpeg-a64-C | 124.03 | `0c664fa35745a5a7f84026aa340c855219b73e75` |
| ffmpeg-a64-G5 | 194.02 | `6346b0f91f1999e33c18435641c61e05f098337b` |

spike最终12项合计240.03秒；FFmpeg最终12项合计2288.20秒。FFmpeg队列2026-11-04T14:57:53+08:00–2026-11-04T16:56:06+08:00，包含等待其他会话的时间；不能把等待计入纯编译耗时。资源采样最低available 10373MiB、最大used 21166MiB，1/5/15分钟load峰值[16.7, 17.57, 11.34]，是离散600秒观测值，不是连续峰值。

spike和FFmpeg的S均有两项profiling flags及显式ISA（aarch64不使用ARM ISA开关），全部成对ID为20字节SHA1；所有debug目标保留对应映射符号。R/C/G5目标有`__llvm_prf_cnts`等节，并在debug符号表找到链接进来的`__llvm_profile_write_file`，不是仅命令行写了选项。runtime strip后映射符号可能不保留，板上采样必须同时保留同ID debug。全部FFmpeg 84对ELF/debug的ID和映射符号也已核对；其中R/C/G5的全部运行ELF均有插桩节和运行库符号。资源采样没有available低于2GiB的点。大型原始日志、对象、RPM、debug只留`temp/eval-prep11/`。

### 9.1 C覆盖对象的拆分注意事项

三ISA的C包实测：runtime有`__llvm_prf_names`但没有covmap；debug有`__llvm_covmap/__llvm_covfun`，而`__llvm_prf_names`为NOBITS。只给llvm-cov debug会报`function name is empty`。用GBS的`eu-unstrip -o combined runtime debug`合成后，三ISA均可被llvm-cov export读取。[10_coverage_split.json](evidence/11/10_coverage_split.json)保存原始命令/失败及成功输出。

该检查使用无关合成前端profile，只验证对象读取链路，不验证真实计数或profile匹配；板上C训练后必须用对应profraw合并再查。此为打包处理步骤，不改插桩类型，不绕过身份校验；runtime/debug必须同ID。

## 10. 板上执行准备与输入盘点（未连接板子）

本机payload也已生成并核对：`temp/eval-prep11/payload-rpi4`共16条、`payload-rpi5`共8条清单，均未部署到板。生成器是`tools/profgen/prepare_board_bundle.py`；[11_script_static_checks.json](evidence/11/11_script_static_checks.json)保存语法/空跑与payload结果。

完整[board_plan.md](../eval/board_plan.md)以及`tools/profgen/board/`三份脚本已做bash -n，**未在开发板执行，不能声称实测成功**。先断言model/arch/kernel，所有生成文件在/opt/afdo_agent，findmnt拒绝ro/noexec；不安装、重启、remount。清单绑定runtimeSHA与GBS读取的ID，运行时核对/proc/PID/maps，采样再核对buildid-list。插件探测本身可能加载插桩库，故在gst-inspect之前已设置本轮目录下的LLVM_PROFILE_FILE，避免默认.profraw外写。setup扫描产生的profraw单独命名并排除在训练合并之外，存在性门禁只检查实际负载的stage前缀。

采集保存完整perf.data、严格5.2.2字段的完整导出、buildid-list、真实RC和环境，另安排高频小ring的LOST采样；若未丢样不能宣称闭合06。性能脚本每组1轮预热丢弃、至少10轮轮转交错，逐秒频率/thermal/节流/负载、每轮pswpout和checksum/perfstat全保存；不自行改sysfs。只接受S或训练后的USE，不允许拿生成侧R/C/G5冒充生产收益。预热和所有异常轮次保留原件。

需要用户开板时决定的操作为：是否root录制、是否设performance governor、是否改变perf_event_paranoid，以及内核符号核对是否需要临时改kptr_restrict；计划逐项列出命令、影响、原值备份和恢复方式，本轮均未执行。身份/硬件事件失败时停止，不回退掩盖。fork/exec/deleted/模块/-1用例单独采集与验收，不能由lit替代。

估算初轮RPi4约85–170分钟（Thumb+A32），RPi5约70–120分钟；训练后性能轮另约30–70/20–45分钟，均不含主机消费构建等待。初始每板规划4GB空间，实际按首份数据量校准；完整主机留存可能1–4GB。

[09_media.json](evidence/11/09_media.json)含ffprobe原始元数据与SHA：720p60秒约4.00Mbps、30,023,879B；1080p60秒约8.05Mbps、60,382,636B；均30fps、同一BBB原片300–360秒内容。原634.6秒BBB也不算另一视频。**现有材料不足以区分不同视频训练/测试**；720p暂作训练、1080p作压力，测试需用户提供独立内容，或另授权固定种子动态场景（只能称合成泛化）。本轮未下载/生成视频。其余搜到的FFmpeg tests/ref/*.mp4是文本参考文件，不是额外片源。

## 11. 待设计 v0.8 登记（裁决后）

1. 5.8第2条R与5.9的G5均为IR插桩；R生成/使用两侧disable-preinline，G5保持正常flags；5.8第5条C是前端插桩coverage。R/C不合并，R/G5分别构建。此前PM前端R措辞已被裁决取代。
2. pseudo-probe拆分节位置按aarch64实测闭合，检测与架构无关；ARM22.1.8 probe崩溃只阻塞步骤8子方案，不阻塞第一批DWARF路径。
3. C参考需保存匹配runtime+debug并eu-unstrip后交llvm-cov，不能把debug单文件含covmap误判为单独可用；真实计数尚待板上。
4. ε、样本预算与结构门槛仍属第二阶段待定；本轮合成脚本测试/产物核对不等于统计质量或优化收益验收。冻结v0.7不改。

## 12. 范围审计与后续挂账

[12_scope_after.json](evidence/11/12_scope_after.json)确认正式工具SHA仍为`334a09290f53eb4c793ae91759f2b6344a36e63317820eb9151771b262dc3f30`、LLVM HEAD仍为`e4642a8ad9e0acb990b45ade3ef7aca755cd80f2`、设计v0.7 SHA不变。`src/llvm`和`src/ffmpeg`干净；LLVM原spec diff SHA仍为`7bbc1828a5a05cde73b6b15225f18aa3280bdbbf4f6620704e6ecc215c97f8fc`，原有打包未跟踪文件保持不动。本轮未重编或改动LLVM。

边界例外：无本轮新增已知例外。GBS在工作目录内的root中处理BuildRequires；未在主机或板上安装RPM。系统命令与既有Git认证按长期澄清使用，无认证修改或密码索取。没有连接开发板、推LLVM/Gerrit或开始Agent开发。

保持挂账：ARM probe子方案崩溃；新LLVM发布后的默认build-id复核；真实[unknown]素材、06完整LOST导出、08真实avg上板核对与非叶子line0；正式非增量LLVM构建前撤销本地spec测试改动。第一批统计/收益尚需独立测试视频、ε及采样预算裁决与板上训练/测量，脚本和生成侧构建完成不能替代这些验收。
