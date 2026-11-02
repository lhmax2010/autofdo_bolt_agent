# 补丁 2 收尾：完整真实导出验收与小修

2026-11-02。开始前读取 STATUS、03 实现报告。冻结设计 v0.7 不改；不连接开发板、不重采、不推送 Gerrit。第一步严格使用旧工具 SHA-256 `b60ba7bb7dd07270da60bae8ff8b292209b506ef2c763f6e0ebe9722b596c69e`，核对成功后才运行。旧工具另存 `temp/profgen-patch2-followup/prior-tool/llvm-profgen`，未覆盖最初的 C1 基线工具。

LLVM 补丁2旧提交：`8f4fa360ade28a7b044fd5ef392d4839311545aa`；amend后新提交：`6e1b1b00c18b52de84351752767f0678113036f6`。父提交仍为补丁1 `00fa352d531680f0bf4a55dec21b30bacfcd4092`。最终补丁 **14个文件，+877/-5行**，包含8个IP测试文件；本轮增加1个测试文件并扩展既有负对照。覆盖导出的[补丁2](../../../patches/profgen/0002-llvm-profgen-Add-IP-sample-reader-and-dsoff-address-conversion.patch)为57,474字节，反向应用检查通过。[提交范围与spec保留审计](evidence/04/06_amend_audit.txt)、[本轮源码diff](evidence/04/06_followup.diff)。

## 1. 完整真实导出的验收（修改前）

共找到并验收 **13 份不同的完整导出、14 次目标运行**（exec 对两个映像分别运行）。除要求的文件，还覆盖05的freq/buildid及约104万样本的大文件。每次传 `--ip-samples --show-ip-address-counts --show-mmap-events`，并以 `^完整板上路径$` 正则指定目标；正则转义文件名的点及deleted括号。所有样本事件都只有cycles，不需要额外 --ip-event；MMAP来源的dummy:u不是样本事件。

工具经GBS x86_64 root loader与build/lib64运行，nice19/ionice3，完整argv、输入/ELF SHA、真实退出码和stderr见 [修改前记录](evidence/04/01_before.json)、[摘要](evidence/04/01_before.log)。所有已找到完整文件的**每一行均被接受**。最终退出码均为1，stderr仅为要求的过渡错误：

```text
llvm-profgen: error: IP sample mode: profile generation is not implemented yet
```

这表示读取与换算成功，不表示生成了profile；所有output路径都未创建。没有删行、改写路径或先过滤记录来让完整文本通过。

| 导出/运行 | 完整文本（相对 WORKDIR） | 行数 / 接受行数 | 输入样本 | 目标样本 | 对照结论 |
|---|---|---:|---:|---:|---|
| 05-fixed | `temp/rpi4-prefreeze/fixed_dsoff.txt` | 7,703 / 7,703 | 7,659 | 6,496 | 原MMAP2独立重算逐VA计数/period和，0差异 |
| 05-multi | `temp/rpi4-prefreeze/multi_dsoff.txt` | 27,112 / 27,112 | 22,662 | 13,289 | 原MMAP2独立重算逐VA计数/period和，0差异 |
| 05-freq | `temp/rpi4-prefreeze/freq_dsoff.txt` | 4,930 / 4,930 | 4,886 | 4,096 | 原MMAP2独立重算逐VA计数/period和，0差异 |
| 05-buildid | `temp/rpi4-prefreeze/buildid_dsoff.txt` | 7,510 / 7,510 | 7,466 | 6,322 | 原MMAP2独立重算逐VA计数/period和，0差异 |
| 05-lost | `temp/rpi4-prefreeze/lost_dsoff.txt` | 1,044,585 / 1,044,585 | 1,044,541 | 943,893 | 原MMAP2独立重算逐VA计数/period和，0差异 |
| 07-fork-cases | `temp/v04/fork.txt` | 9,861 / 9,861 | 9,845 | 9,840 | 与07保存的计数一致 |
| 07-exec-cases | `temp/v04/exec.txt` | 5,946 / 5,946 | 5,925 | 4,833 | 与07保存的计数一致 |
| 07-exec-after | `temp/v04/exec.txt` | 5,946 / 5,946 | 5,925 | 1,081 | 与07保存的计数一致 |
| 07-deleted-libdeleted_probe.so | `temp/v04/deleted.txt` | 169 / 169 | 151 | 151 | 与07保存的计数一致 |
| 07-module | `temp/v04/module.txt` | 334,304 / 334,304 | 318,382 | 51,874 | 模块分类一致；另选libc验证用户ELF目标 |
| 09-fixed | `temp/rpi5-prefreeze/fixed_dsoff.txt` | 7,661 / 7,661 | 7,617 | 5,865 | 原MMAP2独立重算逐VA计数/period和，0差异 |
| 09-multi | `temp/rpi5-prefreeze/multi_dsoff.txt` | 31,066 / 31,066 | 26,778 | 14,331 | 原MMAP2独立重算逐VA计数/period和，0差异 |
| 09-freq | `temp/rpi5-prefreeze/freq_dsoff.txt` | 2,625 / 2,625 | 2,581 | 2,006 | 原MMAP2独立重算逐VA计数/period和，0差异 |
| 09-buildid | `temp/rpi5-prefreeze/buildid_dsoff.txt` | 7,270 / 7,270 | 7,226 | 5,611 | 原MMAP2独立重算逐VA计数/period和，0差异 |
| 06 loss1 | **完整文本未保留**；只有 `temp/rpi4-followup/loss1_lost_lines.json` 中过滤后的LOST行 | 未知 / 未验收 | 未知 | 未知 | 独立核对942条LOST、L=61,667；不能与703,821样本作等值验收 |


### 1.1 目标 ELF 与来源

- 05 使用 `temp/rpi4-prefreeze/libavcodec.so.62.11.100`，板上实体路径 `/usr/lib/libavcodec.so.62.11.100`，SHA `9c72c8cc96dbfd101a03414ff772fe1c6f2f41b4014234869de1be03d6ea5f56`。
- 09 使用 `temp/rpi5-prefreeze/libavcodec`，板上实体路径 `/usr/lib64/libavcodec.so.62.11.100`，SHA `0aaecd3a290fdedb6fa0ba6088fd49cea8635bf7d89c1cbe94efe5506cc63166`；本机文件被改名，所以必须使用锚定正则。
- 07 cases/after/libdeleted_probe.so 使用 `temp/v04/samples-extract/usr/bin/` 中原部署文件。它们不是再次从板上拉回的副本，但本轮逐一核对了07的 `deploy_cases.json`、`deploy_after.json`、`deploy_libdeleted_probe_so.json` 中板上SHA，与本机字节完全相同。没有重新构建或假设同名即可匹配。
- 07 module 是系统级多DSO流；选择06拉回的 `temp/rpi4-followup/libs/usr_lib_libc.so.6` 作为用户ELF目标，并精确锚定 `/usr/lib/libc.so.6`。模块本身仍按kernel分类，不把ET_REL模块当用户PT_LOAD目标。本轮没有拉取/构造新的模块ELF。

每个文件的完整SHA和每条实际命令均在修改前JSON；大文件没有提交。

### 1.2 逐地址独立核对的依据与限度

原保存结果是 `temp/rpi4-prefreeze/perf_analysis.json` 和 `temp/rpi5-prefreeze/analysis.json`；它们保存全部目标/公式/唯一落段的总数、错误清单及若干逐条例子，**没有保存所有样本的逐VA计数表**。因此没有把一个不存在的旧逐地址表当作依据。

本轮从两报告保存的**原始完整文本、MMAP2 和 `libavcodec_segments.txt`（GBS readelf原输出）**重做原算法：对每条目标样本，取同pid/同路径最近的覆盖映射，独立算 `ip-start+pgoff`，再用原PT_LOAD算VA；逐条验证等于dsoff、唯一落段，并按独立VA累加 sample_count/period_sum。随后与工具每个 `IP-ADDRESS` 项精确比较键和值，包含缺键/多键检查。不是仅比较总数，也不是仅把文本dsoff抄给参考计数器。

05 fixed/multi分别 **6,496/13,289** 条；09 fixed/multi分别 **5,865/14,331** 条，独立公式/落段错误均0、逐地址键及两种计数差异均0。对应地址键数量为2,290/3,286/1,712/2,889。额外05 freq/buildid/lost与09 freq/buildid也全部通过。

[逐份独立摘要](evidence/04/02_independent.json)、[原算法带行号快照](evidence/04/02_reference_algorithms.txt)、[本轮检查器快照](evidence/04/02_independent.py.txt)。逐样本含行号、ip、映射起点、pgoff、reported/calculated dsoff、VA与period的表保存为 `temp/profgen-patch2-followup/<05或09>-<类型>-independent.tsv`，不提交。原保存JSON及旧脚本均未改写、未导入执行；没有触发其板上辅助代码。

### 1.3 总数、LOST 与07分类

- 05各份输入总数与原perf_analysis一致：fixed 7,659、multi 22,662、freq 4,886、buildid 7,466、lost 1,044,541。05名称为lost的数据实测LOST=0，不能与06的loss1混淆。
- 09总数与原analysis/report一致：fixed **7,617**、multi **26,778**、freq **2,581**、buildid **7,226**。
- 06当时的导出管道使用awk只保存LOST相关行；留存 `loss1.data`、`loss1_lost_lines.json`，**没有完整样本文本**。对JSON的stdout重新计数得到 **942 条、L=61,667**；record原文写出703,821样本，但本轮无法证明导出样本行数与之相等，写作未知。没有用perf.data重导或重新采集冒充原保存完整文本。[06缺失说明与过滤命令](evidence/04/02_loss06.json)，原过滤脚本行号见算法快照。
- 07 fork：input 9,845、cases target 9,840、kernel 5；父子目标总数与原4,923+4,917一致。exec：input 5,925，cases 4,833、after 1,081，kernel 10，另1条非目标用户样本。
- 07 deleted：151条输入全部是带 ` (deleted)` 的目标样本，target=151，不被误归other_dso。module：input 318,382，kernel=136,336，其中kallsyms 134,607、kdbus 1,663、logger 56、proc-tsm 10（模块共1,729）；libc target=51,874、other_dso=130,172。另有274条deleted路径样本，属于非目标用户DSO，原路径保留。
- 07四份文本中的pid=-1样本实际为 **0**，没有捏造该覆盖；09 multi有 **1** 条 `-1/-1` 内核样本，pid_unknown=1、kernel含该条，与09记录一致。

### 1.4 被拒绝行与性能

完整导出没有被拒绝的行；记录类型只有样本、MMAP、MMAP2，没有未知类型需要用户裁决。没有发现需从真实文本提取新缺陷素材的实现错误。06未留完整文本属于材料缺失，不是发现了设计未列出的语法，按用户允许的缺文件分支记录后继续小修。

最大文件是 `temp/rpi4-prefreeze/lost_dsoff.txt`，98,865,909字节，**1,044,585行**（1,044,541样本+44映射）。旧工具墙钟 **1.405509 秒**，峰值RSS **304,924 KiB（297.78 MiB）**。采用独立子进程exec工具、父进程 `os.wait4` 返回的该子进程 `rusage.ru_maxrss`，不是把多次运行累计的RUSAGE_CHILDREN峰值混用。墙钟包括nice/ionice/loader启动；父进程先检查文本，文件页缓存已热。这是单次本机观测，不是冷缓存或产品性能承诺。[运行器快照](evidence/04/02_run_full.py.txt)

## 2. 小修与测试

| 修改 | 实现 | 测试 |
|---|---|---|
| IP缺binary的专属错误 | 仍保留原cl::Required；缓冲解析错误，IP缺binary经原IP单一错误出口输出 `IP sample mode requires --binary` | 新 `ip-cli-followup.test` 两种参数顺序；非IP缺binary保留旧文本 |
| IP负pid拒绝并解释-1不匹配 | PIDParser继承原uint32解析器，仅记负号拼写；非IP继续原解析器原文，IP最终统一返回 `samples with pid -1 never match --pid` | 同文件 -1/-2、等号/分隔写法、--ip-samples在前/后；非IP负pid旧报错 |
| 正则help准确说明 | 原始DSO路径含deleted标记、子串搜索、需^/$整串锚定 | 同文件 HELP 检查原文 |
| 非法十六进制尾缀作为路径 | 只有非空全hex尾缀才拆offset；普通文件因此报缺dsoff。全hex但超过uint64仍是整数错误 | `ip-invalid.test` garbage/空hex尾缀缺dsoff；超uint64保留offset错误 |
| 两个文件的单行LLVM文件头 | 缩短描述、保留标准单行头，不改语义 | GBS clang-format后检查首行，dry-run/Werror退出0 |

未添加IP新选项、未修改设计或spec。共享命令行改动只为这两种IP诊断延迟公共解析错误输出：其他解析失败原样打印缓冲字节，非IP的诊断不追加提示。两条旧CLI额外原文已在修改前保存，[原输出](evidence/04/03_old_cli.json)；构建后逐字节对照均一致。全部原有50项仍由lit/C1验证，不修改原测试。

[格式化命令](evidence/04/03_format.txt)：GBS root clang-format 22.1.8，经同root loader运行，只格式化相对旧补丁2的改动行。没有改本机工具链、认证配置或向Gerrit推送。

## 3. 构建与修改后验收

### 3.1 GBS增量构建

沿用00第3节同一config、buildroot与worktree，整段worker通过setsid后台运行，GBS用setsid --wait取得真实退出码；nice19/ionice3，10个并发任务。未加clean/clean-once，未改spec，未重跑，未索要sudo密码。完整命令和worker保存于 `temp/profgen-patch2-followup/worker.py`，日志为同目录 `build.log`。

```text
START 2026-11-02T15:56:59+08:00
BUILD_START 2026-11-02T15:56:59+08:00
END 2026-11-02T16:13:52+08:00
GBS_EXIT 0
ELAPSED_SECONDS 1012.782
NINJA_TOTAL_OBSERVED 105
STOP_REASON 
ALL-END 2026-11-02T16:13:52+08:00 OK
```

耗时 **1,012.782秒（约16分53秒）**，Ninja **105步**。按开始、10分钟、结束采样free/uptime：整机used峰值15,728MiB，available最低15,812MiB；1/5/15分钟load观测峰值10.63/6.57/4.09，没有available低于2GiB的采样点。离散采样不代表瞬时峰值或本任务独占内存。[构建原文](evidence/04/04_build.txt)、[汇总](evidence/04/04_build_summary.json)。

新工具经重新编译、链接，SHA-256：

```text
0afa78538527548dfaf9f0f373475f52d621ceb8be1b37db20ce1dc5485926e4
```

### 3.2 lit与C1

%check产生的原始日志和xunit：[lit日志](evidence/04/04_lit.log)、[xunit](evidence/04/04_lit.xml)、[按名称分类](evidence/04/04_lit_summary.json)。共 **58项：PASS56、FAIL0、UNSUPPORTED1、XFAIL1**，XPASS/UNRESOLVED/TIMEOUT均0，3.50秒。原50项与02逐项一致（48 PASS、1 UNSUPPORTED、1 XFAIL）；8个IP测试全PASS。`cs-preinline-cost.test` 的requires asserts与当前assertions=No一致，`invalid-perfscript.test`仍为原XFAIL，没有跳过或修复原测试。FAIL清单为空。

C1比对模式使用新工具SHA并读取既有基线清单：50原测试、127原命令+508格式变体+1纯IP负对照，**636条/遍，两遍一致，与原基线0条差异**。原文件相对f999的门禁通过，8个新增IP测试列为未纳入C1；基线清单未覆盖，SHA仍为 `5a6b9dddf4672fde6ff319b27ef31003f924202e7c0bcf3c8402c1816f61f275`。[C1日志](evidence/04/05_c1.log)、[汇总](evidence/04/05_c1_summary.json)。

### 3.3 完整导出重跑

以新工具重跑第1节相同14次调用，全部接受。逐项确认输入/ELF SHA、行数、退出码、所有统计相同；**14/14 stdout与stderr逐字节完全一致**，output仍未创建。第1节表中的计数即修改前后共同结果；06缺失材料状态不变。额外两条非IP CLI缺binary/负pid的旧报错文本与退出码也逐字节一致。[前后比对](evidence/04/05_real_export_comparison.json)、[重跑摘要](evidence/04/05_after.log)。

最大文件修改后墙钟 **1.384008秒**、子进程峰值RSS **305,012KiB（297.86MiB）**；修改前1.405509秒/304,924KiB。单次热缓存测量，不能据此声称性能改善。完整重跑输出保留 `temp/profgen-patch2-followup/after/`，未提交大文件。

## 4. 提交边界与后续

本轮按用户要求amend LLVM补丁2，保持首行提交说明不变，正文补收尾说明；仅工具目录和测试目录进入LLVM提交。开发 `packaging/llvm.spec` 的两处本地改动原样保留，**正式非增量构建前必须撤销**。未覆盖原C1基线清单，未改冻结设计。

下一步等待补丁3授权。06完整导出缺失的验收限制保留；本轮没有需要裁决的新记录格式。所有大文件、完整工具stdout、逐样本TSV、旧工具及构建日志只留 `temp/profgen-patch2-followup/` 和既有temp目录；新增提交文件均小于1MB。无新增已知项目文件边界例外。
