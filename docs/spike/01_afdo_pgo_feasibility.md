# RPi5 AutoFDO / 插桩 PGO 工具可行性验证

| 路径 | 结论 | 关键证据与边界 |
|---|---|---|
| llvm-profgen 无分支栈输入 | **不可用** | LLVM 22.1.8 对 cycles、cpu-clock 的纯 IP 文本均退出 1：`Invalid perf script input!`；不是空 profile 成功。[E4](evidence/04_profiles.txt)，`src/llvm/llvm/tools/llvm-profgen/PerfReader.cpp:1186–1218` |
| create_llvm_prof 无 LBR 输入（源码结论） | **可用（源码路径）** | `--use_lbr=false` 使用 IP 计数并映射源码位置；本轮不构建，运行可用性/生成质量仍未知。[E1](evidence/01_source_analysis.txt)，`temp/autofdo/profile.cc:165–191` |
| BOLT 无分支栈模式（源码结论） | **可用（AArch64 源码路径）** | `-ba`/`--basic-events`，旧 `-nl` 已弃用；只接受 64 位小端 ELF，不能用于 RPi4 armv7l。本轮未构建/运行 BOLT。[E1](evidence/01_source_analysis.txt) |
| 插桩 PGO | **可用（RPi5 实测闭环）** | instr → profraw → profdata → PGO 重编 → 三次正确性通过；7 函数、31 个计数块，IR 中有匹配的函数计数/分支权重。[E2](evidence/02_build.txt)、[E3](evidence/03_runtime.txt)、[E4](evidence/04_profiles.txt) |

日期：2026-10-28，主机时间 Asia/Shanghai。仅编写测试程序与 spec，没有 Agent 实现；没有修改 LLVM、BOLT、内核、Google AutoFDO 源码，也没有安装板上 RPM。

## 1. 基线、证据与复现范围

- WORKDIR=`/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent`。本文相对路径均从此目录起算；证据中的 `$WORKDIR`/`$ROOT` 在各文件开头给出绝对值。
- LLVM 源码：`src/llvm`，commit `f999bd406c0a70fe8107aa992164fe6945c5d46a`，工作树干净。下文 LLVM/BOLT 行号均对应此提交。
- Google AutoFDO：`nice -n 19 ionice -c3 git clone https://github.com/google/autofdo temp/autofdo`，commit `f95d1a170dfe24ec5ce4117aa4b0f6d836841703`，工作树干净；下文其所有行号对应此提交，只读、未构建。
- `spike/afdo-spike/` 为独立本地 Git 仓库，元数据在 `temp/spike/source-git/`，不推送该独立仓库。提交顺序：`b6b45c28595347483685ce247b41e1506db644b7`（初始）、`f205e0b66b3294a0fcea3a90f7263bcfff079668`（关闭平台 debug 拆分）、`9925a104708449edabb82afe152d68a0a5b9c908`（profile 与 PGO）。结果仓库把 C、spec、文本 profile 作为普通文件提交，不是 submodule/gitlink。
- [E1](evidence/01_source_analysis.txt)：源文件带行号摘录；[E2](evidence/02_build.txt)：配置、完整构建 status、编译命令、工具/ELF；[E3](evidence/03_runtime.txt)：板上命令、原始输出、真实退出码、哈希、计时、清理；[E4](evidence/04_profiles.txt)：转换/检查命令及输出、PGO IR 计数。四个证据合计 90,836 B，低于 150KB；既有证据未修改。
- 完整构建日志/JSON/数据/提取产物在 `temp/spike/`；原始日志行号在截取时保留。板上退出码在执行命令后立即保存，再输出 stdout/stderr，另记 SDB 传输退出码。没有用 `head` 的退出码代替被测命令退出码。

## 2. 无分支栈的源码结论

### llvm-profgen

`src/llvm/llvm/tools/llvm-profgen/PerfReader.h:69–74` 只有 Unknown、LBR、LBRStack 三种内容类型。`PerfReader.cpp:346–377` 据此建立 LBRPerfReader 或 HybridPerfReader。`PerfReader.cpp:1152–1165` 用分支地址的 `0x`/`/` 格式识别 LBR；`:1186–1218` 允许之前有十六进制调用栈行，但只有找到随后 LBR 才能返回已识别类型。读到末尾仍没有 LBR 就报 `Invalid perf script input!`。

因此纯 IP 和只有调用栈的 perf script 都没有被接纳的降级路径；不会自动产生“只有函数级计数”或普通行计数 profile。内部 unsymbolized profile 是另一种输入格式，不能把普通 perf IP 文本改名冒充。直接输入 perf.data 的转换在 `PerfReader.cpp:453–518` 调用 `perf script --show-mmap-events -F ip,brstack`，不会补造没有录入的分支数据。[E1](evidence/01_source_analysis.txt)

架构方面，`ProfiledBinary.cpp:82–93` 从对象构造 Triple 并在 TargetRegistry 查找后端，`:230–241` 接受 ELF/COFF，`:684–717` 依赖目标 MC 组件；`llvm-profgen.cpp:147–165` 初始化已编入的目标。没有“只接受 x86”或“只接受 64 位”的显式白名单。`CMakeLists.txt:1–16` 链接 AllTargets 组件；`src/llvm/packaging/llvm.spec:215–233` 的 x86_64 构建含 X86/ARM/AArch64/BPF，armv7l 构建含 ARM/BPF，aarch64 构建含 AArch64/BPF。

本轮 AArch64 ELF 已被实际读取，失败发生在 perf 输入识别。32 位 ARM 需要对应 MC 后端；不能从有 ARM 后端进一步推断 ARM/Thumb 混合代码完全正确，当前核查未闭合 Thumb 模式切换/地址映射的动态正确性。本轮未运行 ARM/Thumb 二进制，无分支栈拒绝条件对其同样适用。[E1](evidence/01_source_analysis.txt)、[E4](evidence/04_profiles.txt)

### Google AutoFDO create_llvm_prof

以下均为 commit `f95d1a170dfe24ec5ce4117aa4b0f6d836841703` 的源码结论：

- `temp/autofdo/profile.cc:31` 默认 `use_lbr=true`，必须显式关闭。`:165–179` 关闭后用 `maps.address_count_map`；开启且 LBR 范围为空则 warning 并返回。
- `sample_reader.cc:270–310` 读取 perf.data，`:297–301` 对匹配二进制的采样 IP 累加，独立于 branch_stack。`profile_creator.cc:167–216` 的 `profiler=perf` 选择该 reader，按 build-id/二进制名称匹配。没有要求 IP 事件必须为 cycles 的分支；能读入 cpu-clock 不等于其统计权重与 cycles 等价。
- `profile.cc:53–60` 将偏移换成静态地址；`:181–191` 将地址计数映射到 `source_stack` 并 `AddSourceCount`。`instruction_map.cc:18–39` 用 DWARF 的 inline stack 建立地址映射。因此源码支持行/位置及内联上下文计数，不仅函数总数；它没有 LBR 提供的路径/边信息，质量依赖符号、DWARF、采样密度与映射完整性。
- `create_llvm_prof.cc:260–290` 可写 extbinary。候选调用是 `create_llvm_prof --binary=<匹配ELF> --profile=<perf.data> --profiler=perf --use_lbr=false --format=extbinary --out=<输出>`；**本轮未执行此命令**。
- AArch64：`CMakeLists.txt:261–270` 默认 LLVM 目标包含 X86/AArch64。ARM/Thumb：`util/symbolize/elf_reader.cc:60–68,632–652` 有 EM_ARM/Thumb 符号低位清理，`:943–955` 有 ELF32/64 reader，`:288–318` 检查 ELF class/endian。普通 IP 路径不强制 LBR 反汇编检查（`profile_creator.h:35–41` 默认 `check_lbr_entry=false`；`profile.cc:73–85` 才在该开关开启时创建 MiniDisassembler）。这些说明存在 ARM 地址/ELF 支持代码，不能代替 RPi4 ARM/Thumb 实测；默认 LLVM 目标列表也不含 ARM，需要单独核查实际构建配置。

结论是“存在无 LBR 的候选工具路径”，不是“本轮已生成可用 AutoFDO profile”。后续须取得兼容工具后验证 perf 解码、DWARF 映射、热点计数、clang profile 匹配和正确性。[E1](evidence/01_source_analysis.txt)

### BOLT perf2bolt

`src/llvm/bolt/lib/Profile/DataAggregator.cpp:46–64` 定义 `--basic-events`/`-ba`；`-nl` 是打印弃用提示的别名。`:213–225` 在此模式调用 `perf script -F pid,event,ip`；`:1678–1720` 累积 PC 命中，`:722–752` 记录函数内位置计数；`:2215–2230` 输出 `no_lbr` 及事件名/命中数。因此这是非分支栈基本采样模式，不等同精确边频率；`:1634–1649` 明确提示收益可能有限。

AArch64 后端在 `src/llvm/bolt/lib/Rewrite/RewriteInstance.cpp:348–360`；`:398–404` 只接受 64 位小端 ELF，排除 RPi4 armv7l；`:2251–2262` 默认拒绝 stripped 二进制，`:2279–2283` 提示 AArch64 非重定位模式未完整支持，`:2304–2309` 还有 CDSplit/LongJmp 组合限制。后续 AArch64 试验应保留符号及 `--emit-relocs`，不能直接拿已 strip 的板上库套用。本轮没有构建/执行 BOLT，未验证转换产物或收益。[E1](evidence/01_source_analysis.txt)

## 3. 测试包与固定工具链构建

[C 源码](../../spike/afdo-spike/spike.c) 174 行：128 元素插入排序、4096 项查表、哈希混合、约 15/16 的热分支及每 1024 轮的冷路径；没有显式 hot/cold 提示。固定轮数、种子、无符号运算保证各变体工作量一致，结束打印 checksum。先以 100000 轮试跑约 0.57s，再固定 `2500000` 轮，默认种子 `0123456789abcdef`，正式运行约 14–15s；可用参数改变轮数/种子，不用时间截止循环。

[spec](../../spike/afdo-spike/packaging/afdo-spike.spec) 在同一包生成 base、instr，第二次逻辑构建启用 `with_pgo=1` 生成 pgo。最初请求中的“第三个变体”由第二次构建得到；AFDO 仅在 profile 成功时才启用，本轮没有生成 afdo 可执行文件。

配置 `temp/gbs/gbs_rpi5_image.conf` 固定为：

- Unified：`https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261027.063617/repos/standard/packages/`
- Base：`https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261026.051209/repos/standard/packages/`
- buildroot：`WORKDIR/temp/GBS-ROOT-RPI5-SPIKE`；GBS tmpdir：`WORKDIR/temp/gbs-tmp-spike`。沿用 rpi4 配置写法，未修改 `config/` 原文件。

临时 worker `temp/spike/build.sh` 用整段 `setsid --fork` 脱离会话，持有 fd 9 锁；子命令 `setsid --wait env HOME=WORKDIR/temp/gbs-home GIT_CONFIG_NOSYSTEM=1 TMPDIR=WORKDIR/temp/gbs-tmp-spike nice -n 19 ionice -c3 gbs -c WORKDIR/temp/gbs/gbs_rpi5_image.conf build -A aarch64 --threads 1 --define '_smp_mflags -j2'`，PGO 轮另加 `--define 'with_pgo 1'`。无并行大任务，隔离只施加到 GBS；三个退出状态都由 trap 写出时间与 ALL-END，没有代证退出码。[E2](evidence/02_build.txt)

| 尝试 | 开始 → 结束（+08:00） | GBS / wrapper 退出码 | ALL-END | 结果 |
|---|---|---|---|---|
| 首次 base/instr | 19:15:24 → 19:19:29 | 1 / 1 | FAILED | 编译完成，但平台仍做 debug 拆分，出现未打包 debug 文件 |
| 修正 spec 后重试 | 19:20:58 → 19:21:12 | 0 / 0 | OK | 首轮可用 base/instr RPM |
| profile 重编 | 19:27:19 → 19:27:36 | 0 / 0 | OK | base/instr/pgo RPM |

首次只关闭 `debug_package` 不足以屏蔽平台 `__debug_install_post`。日志还有旧 debugedit 的 DWARF5 告警，最终因 unpackaged `.debug` 文件失败。只在测试包 spec 增加 `%global __debug_install_post %{nil}`，并保留关闭 `__os_install_post`/strip 的设置；没有更改系统宏或用户配置。重试成功后从**最终 RPM** 再核对 ELF，避免只检查打包前产物。完整失败/成功 status 与原报错在 E2。

GBS 内 clang 版本为 **22.1.8，Target aarch64-tizen-linux-gnu**，见 `temp/spike/logs/build1_retry.log:205–209`。完整命令摘自该日志 `:215–216`：

```text
clang -O2 -gline-tables-only -fdebug-info-for-profiling -funique-internal-linkage-names -Wl,--build-id=sha1 -Wl,--emit-relocs spike.c -o afdo-spike-base
clang -O2 -gline-tables-only -fdebug-info-for-profiling -funique-internal-linkage-names -Wl,--build-id=sha1 -Wl,--emit-relocs -fprofile-generate spike.c -o afdo-spike-instr
```

第二轮 `temp/spike/logs/build2.log:221–223`：

```text
llvm-profdata merge instr.proftext -o instr.profdata
clang -O2 -gline-tables-only -fdebug-info-for-profiling -funique-internal-linkage-names -Wl,--build-id=sha1 -Wl,--emit-relocs -fprofile-use=instr.profdata -Werror=profile-instr-out-of-date -Werror=profile-instr-unprofiled -Rpass=pgo-instrumentation -Rpass-missed=pgo -fsave-optimization-record -fdiagnostics-show-hotness spike.c -o afdo-spike-pgo
clang -O2 -gline-tables-only -fdebug-info-for-profiling -funique-internal-linkage-names -fprofile-use=instr.profdata -Werror=profile-instr-out-of-date -Werror=profile-instr-unprofiled -S -emit-llvm spike.c -o afdo-spike-pgo.ll
```

分析全部使用 `ROOT=WORKDIR/temp/GBS-ROOT-RPI5-SPIKE/local/BUILD-ROOTS/scratch.aarch64.0` 内 `/emul/usr/bin/` 的平台 x86_64 clang/llvm-profgen/llvm-profdata/readelf（LLVM 22.1.8、GNU readelf 2.43），通过同 root 的 loader 与库运行。该分析工具 clang 报 x86_64 target，与 GBS 内 aarch64 编译目标不矛盾。没有本机工具替代。E2/E4 记录每条完整工具路径和退出码。

最终 RPM 的三个 ELF 都有 `.symtab`、`.debug_line`、`.rela.text`、SHA1 build-id，未 strip。`readelf -SW/-n/-p .comment` 均退出 0；.comment 同时含 clang 22.1.8 与启动对象的 GCC 标记，不据此声称本测试 C 由 GCC 编译。base/instr 两次成功构建字节一致。

| 文件 | 大小 B | build-id | SHA-256 |
|---|---:|---|---|
| afdo-spike-base | 23600 | `10cf3fa4b2a24395310f402e23cbbc7703a831bc` | `28c1ac135271ec050588691bc654ca59e486a4258ed0e4027c9e156dd14675df` |
| afdo-spike-instr | 172824 | `6e001e0362ee072afd58e7334714dd632b564d83` | `b09905ebe115c1c6b81b2cb813a086cb31905b43fb88f28c6944af4012f5f682` |
| afdo-spike-pgo | 23872 | `b279c893b9786f05a45ad81ea08af983893ae1e5` | `9ecb901764f4ccca9c3538d7bd2cdd7103c01f797f9a0752cf7f309f4e5ec029` |

包为 `afdo-spike-1.0-1.aarch64.rpm` 与同版本 SRPM，位于该 buildroot 的 `local/repos/tizen_unified_standard/aarch64/{RPMS,SRPMS}/`。两次成功输出的二进制 RPM 另存 `temp/spike/build1.rpm`、`build2.rpm`，展开目录为同名前缀 `*-extract/`。板上只推送其中可执行文件，没有安装 RPM。

## 4. RPi5 采集和实际事件

连接 `192.168.108.26:26101` 后读取 model=**Raspberry Pi 5 Model B Rev 1.1**、arch=aarch64、uid=0；/opt 为 rw 可执行 ext4，可用约 1.2G。沿用 [04 探测](../probe/04_rpi5_probe.md) 已验证的 perf/libLLVM，哈希复核不变。所有写入限定 `/opt/afdo_agent/`。[E3](evidence/03_runtime.txt)

运行环境是 `HOME=/opt/afdo_agent/work/home TMPDIR=/opt/afdo_agent/work/tmp PERF_CONFIG=/opt/afdo_agent/work/perfconfig LD_LIBRARY_PATH=/opt/afdo_agent/lib`；附带 GST_REGISTRY/XDG_CACHE_HOME 也限定 work。所有 perf 调用均带 `--buildid-dir /opt/afdo_agent/work/buildid`，长命令带 `nice -n 19 ionice -c3`。下面为去掉公共前缀后的命令；完整环境/路径/真实退出码在 E3。

```sh
perf record -e cycles -c 500009 -o /opt/afdo_agent/work/afdo_cycles.data -- /opt/afdo_agent/work/afdo-spike-base 2500000
perf record -e cpu-clock -F 999 -o /opt/afdo_agent/work/afdo_clk.data -- /opt/afdo_agent/work/afdo-spike-base 2500000
perf evlist -v -i /opt/afdo_agent/work/afdo_cycles.data
perf evlist -v -i /opt/afdo_agent/work/afdo_clk.data
```

| 输入 | 实际 evlist | 样本数 / 丢失 | base DSO 占比 | record/evlist/report 退出码 |
|---|---|---:|---:|---|
| cycles | type=0 hardware，config=0，period=500009 | 68,745 / 0 | 99.98% | 均 0 |
| cpu-clock | type=1 software，config=0，freq=999 | 14,268 / 0 | 99.99% | 均 0 |

两者 sample_type 都没有 BRANCH_STACK；cycles 没有回退 cpu-clock。分别导出 `perf script -F ip,sym,dso` 供人工定位，以及 `perf script --show-mmap-events -F ip` 供 llvm-profgen 类型检测；后者保留 mmap 信息且没有额外符号列。四次导出退出 0。两份 perf.data、两类文本全部拉回 `temp/spike/`，核对两端 SHA-256；不是只留文本。

插桩运行设置 `LLVM_PROFILE_FILE=/opt/afdo_agent/work/instr-%p.profraw`，instr 退出 0、checksum 正确。得到 `instr-36489.profraw` 并拉回、核对 SHA-256。所有推送 base/instr/pgo 也分别核对板上 SHA-256 与本机一致。完整 stderr（含 perf 写入量、计时）保存在 E3。

## 5. profile 生成、匹配及复编验证

使用上述 GBS root 平台工具分别执行：

```text
llvm-profgen --binary=WORKDIR/temp/spike/build1-extract/usr/bin/afdo-spike-base --perfscript=WORKDIR/temp/spike/afdo_cycles_ip.txt --format=extbinary --output=WORKDIR/temp/spike/afdo_cycles.extbinary
llvm-profgen --binary=WORKDIR/temp/spike/build1-extract/usr/bin/afdo-spike-base --perfscript=WORKDIR/temp/spike/afdo_clk_ip.txt --format=extbinary --output=WORKDIR/temp/spike/afdo_clk.extbinary
```

两次真实退出码都是 **1**，stdout 为空，stderr 原文都是：

```text
llvm-profgen: error: Invalid perf script input!
```

两个 extbinary 文件均未生成，因而没有可执行的 `llvm-profdata show --sample` 检查对象、没有 AFDO 热点/行计数结果，也没有 AFDO 重编/板上耗时。本次失败与 `PerfReader.cpp:1186–1218` 的无 LBR 拒绝吻合，不能解释成“采样没采到热点”、符号被 strip 或 AArch64 后端缺失。没有修改 LLVM 或伪造分支字段。[E4](evidence/04_profiles.txt)

插桩链路执行 `llvm-profdata merge temp/spike/instr-36489.profraw -o temp/spike/instr.profdata`，再 `llvm-profdata show --all-functions --counts temp/spike/instr.profdata`，均退出 0。profile 为 IR instrumentation，**7 函数、31 个计数块、总计数 22,210,232,043**。总计数是计数器总和，不是 perf 样本数，也不是程序调用总次数。

| 热点/冷点 | profile 核对 | 复编 IR 核对（temp/spike/afdo-spike-pgo.ll） |
|---|---|---|
| hash_mix | 单计数器 300,003,624 | `:16` 引用 !59，`:482` entry_count=300003624 |
| sort_block | 末计数器 2,500,000；内部比较计数达 10,465,782,328 | `:29` 引用 !70，`:493` entry_count=2500000 |
| lookup_work | 分支计数 299,991,523 / 20,008,477，入口 2,500,000 | `:79` 入口 !70；`:551` 对应 branch_weights |
| rare_path | 入口 2,442 | `:133` 引用 !151，`:574` entry_count=2442 |
| run_workload 冷热分支 | 2,497,558 / 2,442 | `:217` 引用 !213，`:636` branch_weights=2442,2497558 |

为只提交小体积文本，用 `llvm-profdata merge --text` 把同一 profile 导出为 [instr.proftext](../../spike/afdo-spike/instr.proftext)（819 B），提交到包源码。第二轮 spec 在构建根把它 merge 回 `instr.profdata` 后用 `-fprofile-use`；二进制 profile 只留 temp。文件 `instr.proftext:3–9,11–19,36–44,46–67` 包含上表计数。

匹配证据不只依赖命令行出现 `-fprofile-use`：本次启用 profile 过期/缺失警告为错误，构建退出 0且无相关警告；同时用同一 profile 和编译参数导出 IR，实际看到上述 entry_count/branch_weights。`-Rpass` 本次没有输出额外的 profile 专用 remark，未把空诊断宣称为命中证明。E4 保存 IR 原行号，E2 保存第二轮实际命令。三个 pgo 运行退出 0，与 base 的校验值完全一致。

## 6. 耗时与正确性

正式参数始终 `2500000`，种子 `0123456789abcdef`。使用 `time -p`，real 是包含启动/退出的观测时间；perf 测量还包含采样器收尾。相对变化=`(real均值/base均值-1)*100%`。

| 变体/运行方式 | real 秒（逐次） | 均值 s | 最大最小差 s | 相对 base | checksum |
|---|---|---:|---:|---:|---|
| base，无 perf | 14.27 / 14.27 / 14.28 | 14.2733 | 0.01 | 0 | `a31c311b953a2ac5`，三次一致 |
| base，cycles | 15.20 | 15.2000 | 不适用（1 次） | +6.49% | 同上 |
| base，cpu-clock | 15.20 | 15.2000 | 不适用（1 次） | +6.49% | 同上 |
| instr | 15.02 | 15.0200 | 不适用（1 次） | +5.23% | 同上 |
| pgo | 14.25 / 14.26 / 14.26 | 14.2567 | 0.01 | −0.12% | 同上，三次一致 |
| afdo | 未构建：无有效 profile | — | — | — | — |

user/sys 原值全部在 E3：base user=14.27/14.25/14.25，sys 均 0；pgo user=14.24/14.24/14.25，sys 均 0；instr user=15.01、sys=0；cycles user/sys=14.50/0.08；cpu-clock=14.37/0.12。

PGO 的观测差只有约 0.017s；三次顺序运行、计时分辨率 0.01s，没有随机交错或频率/温度控制，不据此认定稳定加速。训练/验证用同一输入，验证的是工具与正确性闭环，不代表跨输入泛化或真实媒体负载优化收益。

## 7. 对 Agent 设计的含义

| 板型 | 建议默认路径 | 前提与本轮边界 |
|---|---|---|
| RPi5 aarch64 | **插桩 PGO**，现已实测完整闭环 | 匹配的 clang/compiler-rt/profdata、可重新编译的包、代表性训练负载、可写 profraw 路径；保留基线并校验 checksum/场景输出。不能把本测试的微小时间差当成性能目标已达成 |
| RPi4 armv7l | **优先验证插桩 PGO，再作为默认** | 需要 ARM 目标 profile runtime 和同版本工具，并完成 armv7l 实测；本轮仅验证 aarch64，不能自动标记 RPi4 已可用。PMUv3 新镜像不是插桩前提 |

普通 IP AutoFDO 的后续候选是 Google `create_llvm_prof --use_lbr=false`，RPi5 可用已证实的 cycles，RPi4 现镜像可用 cpu-clock；必须先补工具构建和端到端转换/匹配测试，特别是 ARM/Thumb 地址及 DWARF 映射。当前 llvm-profgen 不能作为这两块板的纯 IP 转换器；RPi4 将来启用 PMUv3 只增加普通硬件事件，并不因此获得 LBR/BRBE。

BOLT `-ba` 是 RPi5 后续候选，需具备 BOLT 工具、64 位小端/未 strip/保留重定位的匹配 ELF，并实际验证优化正确性及收益；不能作为已走通路径。RPi4 armv7l 被该 BOLT 的 ELF64 限制排除。上述建议来自本轮源码与实测，不是额外安装或构建授权。

## 8. 清理、保留与边界例外

板上 `find /opt/afdo_agent/work -mindepth 1 -delete` 后检查为空并 `ls -la`，退出 0，仅 `.`/`..`；包括可执行文件、perf.data、profraw、文本、缓存、buildid 都已清理。`rpm -qa | wc -l` 开始/结束均 **1249**。没有 remount、重启、安装/卸载 RPM 或改动 /boot。本机二进制、perf.data、profraw、二进制 profdata/RPM 仅在 temp。[E3](evidence/03_runtime.txt)

保留上一轮工具，没有新增常驻板上文件：

| 板上路径 | 来源包（同镜像快照，见 04 探测） | SHA-256 |
|---|---|---|
| `/opt/afdo_agent/tools/perf` | linux-kernel-perf 6.12.80-0.aarch64 | `d23f11a13d5b0b21fc1957a883eb0025c80f9a26bcde360b7031b4d3b1348949` |
| `/opt/afdo_agent/lib/libLLVM.so.22.1` | libllvm 22.1.8-1.5.aarch64 | `06b9971c974f113b16ea49c988b6481f20272e70ba36040358735fa6c91af007` |

完整移除命令为 `rm -rf /opt/afdo_agent`；本轮按要求保留工具，未执行该命令。

**边界例外：无新增。** 历史共享 SDB daemon 的 `/tmp/sdb.log` 仍在工作区外；本轮前后只读 stat 均为 495 B，mtime=`2026-10-28 17:48:51.361776578 +0800`，没有删除或重启服务。此历史遗留继续登记，不声称不存在；没有做全系统 syscall 审计。GBS buildroot/tmp/cache/log 均在 WORKDIR/temp；本轮没有读取工作区外项目输入或附件。正常 Git 认证沿用用户已批准的系统环境。
