# 补丁 2：IP 文本读取与 dsoff 地址换算

2026-11-02。本补丁只实现读取、筛选与 ELF 地址计数；**尚不能生成 IP profile**。成功读取后仍按本轮要求返回固定的过渡错误，退出 1，不创建或覆盖 output。

冻结设计 v0.7 SHA-256 为 `eec6b208d8e1fedb840f0933eb20a37c188890b6c8c29e43986c5c9bbca9f6be`，文档未改。LLVM 起点为补丁 1 `00fa352d531680f0bf4a55dec21b30bacfcd4092`；工作树 `temp/llvm-profgen-enh`、分支 `afdo/profgen-enhance`。没有连接开发板、没有向 LLVM 远端或 Gerrit 推送。

LLVM 本地提交：`8f4fa360ade28a7b044fd5ef392d4839311545aa`。共 **13 个文件，+816 / -3 行**；其中 7 个新增 lit 测试文件。导出的 [补丁 2](../../../patches/profgen/0002-llvm-profgen-Add-IP-sample-reader-and-dsoff-address-conversion.patch) 为 52,407 字节，反向应用检查退出 0。[提交路径、署名、残留 spec diff 审计](evidence/03/07_commit_audit.txt)

## 1. 实现与共享代码边界

以下 `L/` 为 LLVM 工作树的 `llvm/tools/llvm-profgen/`，`T/` 为 `llvm/test/tools/llvm-profgen/`。行号对应本补丁提交。

- 新增 `L/IPPerfReader.h`、`L/IPPerfReader.cpp`。`IPPerfReader::parseLine` 读取固定前缀与完整 DSO 字段，保存样本、原始路径/deleted 标记、映射及其身份原文；`loadBinary` 用 `llvm::object` 读取 ELF 程序头；`selectSamples` 做事件/PID/DSO 筛选及唯一 PT_LOAD 换算。`AddressCounter` 是按 uint64 ELF VA 排序的映射，每项分别存 uint64 `SampleCount`、`PeriodSum`。
- MMAP/MMAP2 保存外层原始行、记录内 PID/TID、起点、长度、pgoff、权限、原始路径、deleted 标记和 build-id 或设备号/inode/generation 字面值。记录内 PID/TID 作为映射所属进程；不依靠外层 `0/0` 推断进程。它们只是观察到的证据，不实现 fork/exec 地址空间重放，不用于重新计算 perf 已给出的 dsoff。
- `L/CMakeLists.txt:21` 只增加一个编译单元。`L/Options.h:19` 声明已有 `ShowMmapEvents`；`L/PerfReader.cpp:30` 只移除这个变量的 static 并格式化对应声明，原定义、默认值、描述和 LBR 使用点不变。
- `L/llvm-profgen.cpp:84` 增加三个公开选项与一个隐藏诊断选项。`:101` 的 `runIPMode` 集中检查选项和运行 IP 读取器；`:236` 的显式门控在原 `validateCommandLine` 前执行。未启用 IP 且未使用 IP 专属选项时，继续原 LBR 路径。没有重构原验证函数、ProfiledBinary、LBR reader 或 profile writer。
- IP 自有代码使用 `Error` / `Expected`，不调用 `exitWithError`；失败由 main 同一出口 `logAllUnhandledErrors` 打印并返回 `EXIT_FAILURE`。LLVM 通用命令行解析器对未知选项、缺少 required 参数的原生诊断仍由原基础设施负责。

### 1.1 统计口径与过渡接口

`--show-ip-address-counts` 是本轮用户明确授权、设计表之外的 **cl::Hidden 测试接口**，没有写入设计 5.1.1。它只在 IP 模式有效；即使显式给 `=false`，在非 IP 模式也报错。输出固定为：

```text
IP-ADDRESS 0x10000 sample_count=1 period_sum=1000003
IP-STATS input=4
IP-EVENT cycles samples=4
IP-STATS after_event=4
IP-STATS after_pid=4
IP-STATS pid_unknown=0
IP-STATS kernel=0
IP-STATS other_dso=0
IP-STATS unmapped=0
IP-STATS target=4
IP-STATS unmapped_in_target=0
IP-STATS lost_records=0
IP-STATS lost_L=0
IP-STATS mappings=2
```

地址按数值升序、事件按名称排序；每个地址一行，再打印统计。`input`、事件直方图、`pid_unknown`、LOST 条数/L、映射数是**整份输入级**；`after_event`、`after_pid` 是顺序筛选后的数量；kernel/other_dso/unmapped/target 是之后的分类；`unmapped_in_target` 是 target 的子集，不是额外类别。隐藏输出中的 LOST=0 只表示观察到的记录数为零，不声称真实丢样为零；质量报告的 unknown/source/completeness/比例留补丁 6。

无论是否打印诊断，成功解析/换算后仍返回：

```text
llvm-profgen: error: IP sample mode: profile generation is not implemented yet
```

错误本体就是用户指定的固定文本，前缀由 main 添加。此时不调用 writer、不打开 output；补丁 4 才移除这一过渡行为。`--show-mmap-events` 则逐行打印保存的 MMAP2 原文，不打印 MMAP。

## 2. 冻结规则、实现与测试对照

| 规则 | 实现位置 | lit 覆盖 |
|---|---|---|
| C1 / 5.1.2 显式启用、默认纯 IP 原错误不变 | `L/llvm-profgen.cpp:236` | 原 50 项 lit + 固定 C1 636 行；纯 IP 负对照仍退出 1 |
| 5.1.1 完整事件名、多个事件必须选择、筛选为空失败 | `L/IPPerfReader.cpp:265` | `ip-invalid.test` E0/EMPTY；`ip-selection.test` MOD/MIX/EXACT，cycles 与 cpu-clock 分开，cycles 不匹配 cycles:u |
| 5.1.2 IP 专属选项在非 IP 模式报错 | `L/llvm-profgen.cpp:105` | `ip-options.test` GATE；含隐藏开关显式 false |
| 5.1.3 全部报错选项，按 getNumOccurrences 而非默认值判定 | `L/llvm-profgen.cpp:107` | `ip-options.test` OPT0–OPT28，每个现存具体选项各一条；含 csprof/csspgo 全部注册项及 infer-missing-frames=false |
| 5.1.3 output 为 -；5.2.4 perfdata 未准入 | `L/llvm-profgen.cpp:136` | `ip-options.test` STDOUT/DATA/MISSING；perfdata 错误提示板上导出文本 |
| 5.2.2 / 5.2.3 固定字段，只有样本/MMAP/MMAP2/LOST | `L/IPPerfReader.cpp:97` | `ip-real-records.test`；`ip-invalid.test` TYPE/E5，LOST_SAMPLES 明确不支持 |
| 固定前缀后消费完整括号字段，拆末尾 +0x，保留内部空格/括号/+0x | `L/IPPerfReader.cpp:179` | `ip-selection.test` PATH 三个素材、DELETED；`ip-invalid.test` E4/E6/E7 |
| pid/tid=-1、禁止小于-1，--pid 不包含未知进程 | `L/IPPerfReader.cpp:49`、`:69`、`:284` | `ip-real-records.test` REAL/PID；`ip-invalid.test` E2/E3/MPID |
| period>0、损坏整数/截断/调用栈或 brstack 扩展拒绝 | `L/IPPerfReader.cpp:179` | `ip-invalid.test` E1/E4/E5/E6/E7/INTEGER；NUL 输入拒绝，不猜测路径 |
| 按名字识别内核、模块、特殊 DSO，不按地址范围 | `L/IPPerfReader.cpp:82`、`:89`、`:288` | `ip-real-records.test` 真实 kernel/module/vdso/-1/-1 与合成 unknown 的分类统计 |
| LOST 记录数、L 与整份输入样本数 S；映射身份只保存 | `L/IPPerfReader.cpp:105`、`:115`、`:217` | `ip-real-records.test` L=138、1 条 LOST、5 条映射；两种 MMAP2 原文、模块 MMAP；`ip-invalid.test` LOST 溢出 |
| 5.3.3.1 正则独占选择原始路径；默认 realpath basename、去 deleted 后缀 | `L/IPPerfReader.cpp:271`、`:304` | `ip-selection.test` REGEX/LINK/DELETED；同名但被正则排除的路径不计入候选 |
| 候选为空列最多 5 个高频文件 DSO 和正则提示 | `L/IPPerfReader.cpp:330` | `ip-invalid.test` TARGET/TOP；6 个 DSO，只输出最高的 5 个 |
| 5.3.1 唯一可执行 PT_LOAD、p_filesz 半开区间、offset→VA | `L/IPPerfReader.cpp:228`、`:314` | `ip-addresses.test` 五份配套地址与 paired-addresses.json 一致，multi-load 两段及 0x1800 空隙；`ip-segments.test` 重叠、区间末端 |
| 地址与各 uint64 计数加法溢出即失败 | `L/IPPerfReader.cpp:30`、`:243`、`:320` | `ip-invalid.test` period_sum、LOST、MMAP 地址/pgoff 溢出；`ip-segments.test` p_offset/p_vaddr 溢出 |
| 5.6.3.3 Error/Expected、单出口；过渡失败不碰 output | `L/llvm-profgen.cpp:101`、`:236` | 每个负对照检查错误文本；`ip-transition.test` 验证新文件不存在、旧文件 sentinel 不变 |
| C2 只改工具目录和工具测试目录 | 本地提交路径审计 | 证据中的提交 stat/路径清单；spec 不进入提交 |

程序头处理覆盖 ELF32/ELF64 的 LE/BE 类型；本轮正向素材是 armv7l/AArch64 LE，不据此声称已验证其他架构。没有构造 ProfiledBinary、全局 BaseAddress、4K 掩码或指令解码器；计算使用 `vaddr = p_vaddr + (off - p_offset)`，不使用 p_memsz 扩大文件范围。

新测试都只依赖补丁 1 素材与 lit 工具。异常段通过 yaml2obj 合成小 ELF；没有新增外部 perf、网络或板上依赖。`ip-addresses.test` 要求 ARM 与 AArch64 targets，其余需要实际读取 A64 的测试标记 AArch64；纯选项拒绝测试不读取 ELF，无架构要求。

## 3. 构建、lit 与 C1

沿用 00 报告第 3 节的 `temp/gbs/gbs_llvm_x86_baseline.conf`、`temp/GBS-ROOT-LLVM-X86` 和同一开发 worktree；未加 clean/clean-once，未改任何配置或 spec。GBS 与子进程才设置隔离 HOME/GIT_CONFIG_NOSYSTEM。整个 worker 用 setsid 脱离，GBS 用 setsid --wait 获取真实返回码；每 600 秒记录 free/uptime，另取开始/结束点。启动前检查没有其他编译重任务，已有 NOPASSWD 支持 GBS 调用，无需输入 sudo 密码，未索要或改变凭据。

```text
setsid --wait nice -n 19 ionice -c3 gbs -c /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/gbs/gbs_llvm_x86_baseline.conf build -A x86_64 --spec llvm.spec --incremental --threads 1 --define '_smp_mflags -j10' --define 'mlgo_build_jobs 10'
```

### 3.1 构建记录

| 轮次 | 开始/结束（+08:00） | GBS 退出码 | 秒 | Ninja 总步数 | 结果 |
|---|---|---:|---:|---:|---|
| 首次编译 | 2026-11-02T14:23:14+08:00 / 2026-11-02T14:23:44+08:00 | 1 | 30.040 | 110 | FAILED |
| 修正后完整增量轮 | 2026-11-02T14:25:33+08:00 / 2026-11-02T14:41:35+08:00 | 0 | 962.800 | 104 | OK |
| 补强边界用例的最终轮 | 2026-11-02T14:42:43+08:00 / 2026-11-02T14:56:15+08:00 | 0 | 812.070 | 106 | OK |

首次失败是本轮新代码的两处 C++ 错误：对 DenseMap 条目调用了 getKey，以及新函数缺少闭括号。分别改为 Entry.first、补齐函数结构；同时改用 StringSwitch 的 initializer-list Cases 消除弃用警告。失败原文、退出码和收尾标记完整保留，没有绕过失败。第二轮 `%check` 为 54 PASS / 1 UNSUPPORTED / 1 XFAIL，6 个新测试均通过。之后增加 NUL 文本拒绝及异常 PT_LOAD 等补强用例，做第三轮最终验收；没有因失败改 spec、%files 或既有测试。

最终轮 **812.070 秒（约 13 分 32 秒）、106 步**，相对基线 7,633 步为 1.39%。三轮实际构建计时合计 **1804.910 秒**（约 30 分 5 秒，不含编辑与 C1 时间）。最终日志第 2123 行编译 IPPerfReader.cpp、第 2125 行编译 llvm-profgen.cpp、第 2126 行重新链接 bin/llvm-profgen；Ninja 最后一步在构建第 22 秒完成，其余主要是安装/拆分/打包。全部轮次有带时间的 ALL-END；最终状态全文：

```text
START 2026-11-02T14:42:43+08:00
BUILD_START 2026-11-02T14:42:43+08:00
END 2026-11-02T14:56:15+08:00
GBS_EXIT 0
ELAPSED_SECONDS 812.070
NINJA_TOTAL_OBSERVED 106
STOP_REASON 
ALL-END 2026-11-02T14:56:15+08:00 OK
```

[状态、资源、关键命令与末尾原文](evidence/03/03_build_records.txt)，[机器可读摘要](evidence/03/03_build_summary.json)。临时完整日志在 `temp/profgen-patch2/attempt1/`、`attempt2/` 和 `temp/profgen-patch2/build.log`；worker 同目录。前台分别打印过查看 status/tail 的命令。

### 3.2 资源采样

| 时间（+08:00） | 轮次 | used MiB | available MiB | load 1/5/15 min |
|---|---|---:|---:|---|
| 2026-11-02T14:23:14+08:00 | attempt1 | 15296 | 16244 | 0.7 / 0.78 / 0.84 |
| 2026-11-02T14:23:44+08:00 | attempt1 | 16314 | 15226 | 1.62 / 0.98 / 0.91 |
| 2026-11-02T14:25:33+08:00 | attempt2 | 15725 | 15815 | 0.68 / 0.81 / 0.85 |
| 2026-11-02T14:35:35+08:00 | attempt2 | 15255 | 16285 | 3.71 / 3.82 / 2.47 |
| 2026-11-02T14:41:35+08:00 | attempt2 | 15358 | 16182 | 11.54 / 7.1 / 4.11 |
| 2026-11-02T14:42:43+08:00 | final | 15247 | 16292 | 4.11 / 5.8 / 3.87 |
| 2026-11-02T14:52:45+08:00 | final | 15163 | 16377 | 2.82 / 3.55 / 3.64 |
| 2026-11-02T14:56:15+08:00 | final | 15115 | 16425 | 12.82 / 7.45 / 5.06 |

所有轮次的离散观测中，used 峰值 **16314 MiB**，available 最低 **15226 MiB**，load 峰值 **12.82 / 7.45 / 5.06**。没有 available 低于 2048 MiB 的采样点。这是整机离散采样，不是构建独占 RSS 或连续峰值。

### 3.3 lit

`%check` 实际运行固定的 `build/bin/llvm-lit -sv -j1` 与 xunit 输出，57 项、3.66 秒：

| 分类 | 数量 | 说明 |
|---|---:|---|
| PASS | 55 | 原有 48 + 新增 7 |
| FAIL | 0 | FAIL 清单为空 |
| UNSUPPORTED | 1 | 原 `cs-preinline-cost.test`，REQUIRES asserts；assertions=No 未改 |
| XFAIL | 1 | 原 `invalid-perfscript.test` 的 XFAIL:*，未改 |
| XPASS / UNRESOLVED / TIMEOUT | 0 / 0 / 0 | 无 |

新增：ip-addresses、ip-invalid、ip-options、ip-real-records、ip-segments、ip-selection、ip-transition（均 `.test`）。共 109 条 RUN（包含素材准备和检查命令，不是 109 个独立 lit 测试）。原 50 项与 02 的 xunit 逐项名称/失败/跳过状态及原因相同；XFAIL 名称结合原测试指令和 lit 文本确认，本版 xunit 不单独区分 XFAIL 与 PASS。

[lit 原始日志](evidence/03/04_lit.log)、[xunit](evidence/03/04_lit.xml)、[逐项分类](evidence/03/04_lit_classification.json)、[新测试 RUN 清单](evidence/03/02_test_inventory.json)。没有任何 FAIL 被隐藏或跳过。

### 3.4 新工具与 C1

新工具 SHA-256：`b60ba7bb7dd07270da60bae8ff8b292209b506ef2c763f6e0ebe9722b596c69e`。本次确实重新编译/链接，不同于 02 的工具未重新链接情况。[GBS loader 解析与 --version](evidence/03/06_tool_runtime.txt) 确认使用 build/lib64 的 libLLVM 和 GBS root 的运行库，版本 22.1.8；没有改用本机工具链。

```bash
cd /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent
export TMPDIR="$PWD/temp/tmp"
nice -n 19 ionice -c3 python3 tools/profgen/c1_baseline.py \
  --expected-tool-sha b60ba7bb7dd07270da60bae8ff8b292209b506ef2c763f6e0ebe9722b596c69e \
  --manifest "$PWD/temp/profgen-patch2/c1.json" \
  --compare "$PWD/tools/profgen/c1-baseline.json"
```

C1 真实退出码 **0**：50 个登记测试、127 条原命令 + 508 个格式变体 + 1 条默认纯 IP 负对照，**636 行/遍，两遍一致，与已提交清单 0 条差异**。7 个新测试全部在“新增、未纳入 C1”的列表中。比较前原测试相对 f999bd4 的不变性门禁和矩阵对齐检查均通过；比较 profile SHA、完整 stderr SHA 和退出码，不归一化报错、不覆盖原清单。

默认纯 IP 仍退出 1、没有生成 profile，stderr 原文：

```text
llvm-profgen: error: Invalid perf script input!
```

[重放日志](evidence/03/05_c1.log)、[摘要与纯 IP 行](evidence/03/05_c1_summary.json)。基线清单 SHA 仍为 `5a6b9dddf4672fde6ff319b27ef31003f924202e7c0bcf3c8402c1816f61f275`。完整临时清单在 `temp/profgen-patch2/c1.json`，两遍 stdout/stderr/profile 在 `temp/profgen-c1-baseline/pass1/`、`pass2/`。


## 4. 格式、范围与后续补丁

使用 GBS root `temp/GBS-ROOT-LLVM-X86/local/BUILD-ROOTS/scratch.x86_64.0/usr/bin/clang-format`，经同 root loader/library-path 运行，版本 22.1.8。新文件整体格式化；共享文件仅用 `git diff -U0` 得到的改动行范围格式化，随后 `--dry-run --Werror` 检查退出 0。[完整命令](evidence/03/01_format.txt)

本轮完成的是用户给定的补丁 2 范围，不等同于第一阶段整体完成。留待后续：

- 补丁 3：build-id/分离调试文件身份链、MMAP2 与 buildid-list 的身份汇总、歧义/缺失/冲突判定。本补丁只保留证据，不据此宣称二进制匹配已验证。
- 后续身份/二进制加载路径还需落实 5.1.4 的 probe 节准入门禁；当前不构造 ProfiledBinary，也不做 DWARF/probe 关联，所有成功输入统一以过渡错误失败，不能生成 probe profile。
- 补丁 4：P_ref、权重、行级/内联上下文聚合和 profile 输出；其他 IP 选项按所属补丁加入。当前计数仅是原始 sample_count 与 period_sum。
- 补丁 5：ARM/Thumb 指令边界、映射符号、skid 等；当前按 dsoff 得到的字节 VA 计数，不隐式清 Thumb 位或做 4K 对齐。
- 补丁 6：质量报告、LOST 的 unknown/completeness/比例、门槛、原子输出/兜底回调与终态契约。隐藏诊断不是正式质量报告。

本轮没有发现需要修改冻结规则才能完成此补丁范围的情况。设计 5.2.3 中“其他记录按清单跳过”在本轮没有获准额外清单：按用户明确限定，只认四类记录，其他记录报错。

开发用 `packaging/llvm.spec` 两处本地改动原样保留，不提交到增强分支。**正式非增量构建前必须撤销**，详见 [02 报告](02_lit_env.md)。原 C1 清单没有覆盖，原 50 个测试没有修改，基线工具存档没有覆盖。Agent 开发未开始。

本轮没有新增已知项目文件边界例外。GBS 生成的未跟踪 manifest、debug 列表、mlgo_verify_assets 等仍留在临时工作树，没有暂存。完整日志、临时 profile/ELF、RPM、C1 清单和失败重试记录留在 `temp/profgen-patch2/`、`temp/profgen-c1-baseline/` 与原 GBS root；提交的证据只取必要原文，单个文件小于 1 MB。
