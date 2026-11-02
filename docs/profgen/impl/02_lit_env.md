# 补丁 2 前准备：C1 固定范围、基线存档与 lit 环境

日期：2026-11-02。设计仍为冻结版 v0.7；本轮没有修改 llvm-profgen 源码、既有测试、设计文档，没有连接开发板或向 Gerrit 推送。仅项目侧 C1 脚本进入提交；开发工作树的 spec 改动只本地保留，不进入 LLVM 补丁序列。

## 1. 构建前存档

在任何构建前验证原工具 SHA-256，并通过 GBS loader `--list` 查明实际加载的 libLLVM 来自本地 build/lib64；复制实体文件后逐一复核 SHA。工具路径和库路径、完整命令、真实退出码及输出见 [01_archive.json](evidence/02/01_archive.json)。

| 存档文件（相对 WORKDIR） | SHA-256 |
|---|---|
| `temp/profgen-baseline-tool/llvm-profgen` | `a31073338f9315a0fd6d2934e36431d9135086882ebfb07bd1bda7c36d7f9f1e` |
| `temp/profgen-baseline-tool/libLLVM.so.22.1` | `2c07f047841853eaeab97ab69a285e28941e8b8983706ec76183065791dd914a` |

存档后的 loader `--list` 进一步确认实际解析到存档目录的 libLLVM，退出 0，见 [01_archive_loader.txt](evidence/02/01_archive_loader.txt)。其余基础运行库仍使用原 GBS x86_64 root；本轮没有声称存档了整个系统环境。二进制不提交。

## 2. C1 脚本修正与自检

[脚本](../../../tools/profgen/c1_baseline.py) 的 compare 模式现在：

1. 从已提交基线清单取得原测试集合及每条 RUN 的行号、格式序列；只重放这些登记项。新增测试文件另列“新增、未纳入 C1 的测试文件”，不自动加入基线。
2. 在任何工具重放前，针对这 50 个原有测试文件执行 `git diff --exit-code f999bd406c0a70fe8107aa992164fe6945c5d46a -- <登记的路径>`。此检查覆盖提交、index 和工作树相对基线的改变；失败即停止。不是对所有 LLVM 文件做禁止变更检查，后续增强源码改动不受此门禁阻挡。
3. 先检查新旧清单总行数，再检查每行 test/line/format 顺序；任一不齐，停止内容比较并明确报矩阵错误。对齐后才比较退出码、profile SHA 和完整 stderr SHA。
4. 增加可重复的 `--library-dir`，这些目录优先于 GBS 基础运行库；未指定时仍使用 build/lib64。准备输入所需的辅助工具继续在既定 GBS 环境运行。
5. GBS loader 的 `--argv0` 固定为原基线的工具命令名。原因是初次存档重放有 10 行差异，全部是 `cs-preinline-cost.test` 两条 RUN × 五种格式的未知参数错误：提示中的 `Try: '<工具路径> --help'` 随工具存档路径改变。通过固定真实 argv[0] 保持同一命令名，而不是改写 stderr；初次失败记录保留在 temp。

基线清单 `tools/profgen/c1-baseline.json` 未覆盖，SHA-256 仍为 `5a6b9dddf4672fde6ff319b27ef31003f924202e7c0bcf3c8402c1816f61f275`。修正后的存档工具 compare 重放：50 个测试、127 条原命令＋508 条格式变体＋1 条纯 IP 负对照，636 行/遍，两遍一致，**与原清单 0 条差异**。实际新增测试列表为空。[摘要](evidence/02/04_archive_c1.json)、[运行日志与首次差异说明](evidence/02/04_archive_c1.log)

另外完成五项控制逻辑自检：新测试排除、原文件变更拒绝、矩阵数量/顺序错误先拒绝、已对齐内容差异定位、存档库优先与稳定 argv0。测试使用模拟发现路径/模拟 git diff，没有创建或修改 LLVM 测试文件。[自检证据](evidence/02/02_script_selfcheck.txt)

今后用存档工具复核或重录至临时清单（不覆盖提交的基线）：

```bash
cd /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent
export TMPDIR="$PWD/temp/tmp"
nice -n 19 ionice -c3 python3 tools/profgen/c1_baseline.py \
  --tool "$PWD/temp/profgen-baseline-tool/llvm-profgen" \
  --library-dir "$PWD/temp/profgen-baseline-tool" \
  --manifest "$PWD/temp/profgen-lit-prep/archive-c1.json" \
  --compare "$PWD/tools/profgen/c1-baseline.json"
```

保持默认 scratch 路径不变，以免既有诊断里的输入路径改变。profile 和完整逐命令输出保留在 `temp/profgen-c1-baseline/`；本次清单与启动日志在 `temp/profgen-lit-prep/`，不提交大文件。

## 3. 只保留本地的 spec 改动

工作树 `temp/llvm-profgen-enh`，分支 `afdo/profgen-enhance`，HEAD 仍为补丁 1 `00fa352d531680f0bf4a55dec21b30bacfcd4092`。修改前 spec 跟踪文件 diff 为空；只改两处，完整 [diff](evidence/02/03_spec_local.diff)：

```diff
-    -DLLVM_INCLUDE_TESTS=OFF \
+    -DLLVM_INCLUDE_TESTS=ON \
```

在 `%install` 后、包脚本段前新增：

```spec
%check
build/bin/llvm-lit -sv -j1 --xunit-xml-output=build/profgen-lit.xml build/test/tools/llvm-profgen > build/profgen-lit.log 2>&1 || true
cat build/profgen-lit.log
```

`-j1` 限制 lit 并行，测试范围只有 llvm-profgen。日志和 xunit 都固定写到 build；`|| true` 只避免测试失败中断打包，不意味着 lit 测试成功。没有改 `%files`、其他选项或 assertions=No。

**正式非增量构建前必须撤销。** 当前 spec 不提交到 LLVM 分支；以后每个补丁只能显式 git add 工具目录、测试目录及文档，不能 git add -A 把本地 spec 带入。确认没有后续其他 spec 改动后，可在开发工作树内执行 `git restore --source=HEAD -- packaging/llvm.spec`；本轮按用户要求保留这两处，未执行撤销。

## 4. 构建条件与记录

沿用 00 报告第 3 节：同一 `temp/gbs/gbs_llvm_x86_baseline.conf`、`temp/GBS-ROOT-LLVM-X86`、`temp/llvm-profgen-enh`；固定 20261027 Unified / 20261026 Base 快照。没有 `--clean`、`--clean-once` 或额外 `--noinit`。

预检没有其他 ninja/clang/gbs/make 编译重任务，磁盘可用 246 GiB。`sudo -n -l` 退出 0，已有 NOPASSWD 规则覆盖 build、scratch bind/unmount、日志搬运和 chroot 等 GBS 所需命令。未请求密码、未更改 sudo 或 Git 认证配置。[预检证据](evidence/02/05_preflight.json)

后台 worker 整段用 setsid 脱离，GBS 子进程用 setsid --wait 获取真实返回码；只有 GBS 及其子进程设置隔离 HOME/GIT_CONFIG_NOSYSTEM。nproc=20，jobs=10；原 spec 编译池 6、链接池 2 不变。完整命令：

```text
setsid --wait nice -n 19 ionice -c3 gbs -c /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/gbs/gbs_llvm_x86_baseline.conf build -A x86_64 --spec llvm.spec --incremental --threads 1 --define '_smp_mflags -j10' --define 'mlgo_build_jobs 10'
```

状态/日志：`temp/profgen-lit-prep/build.status`、`build.log`；资源每 600 秒记录 free -m/uptime，另采开始和结束点。worker 位于同目录 `worker.py`。预先声明 Ninja 总步数超过 1,000 则停止并报告明显扩大重编（原基线 7,633）；本轮实际是否触发见下文。不通过改 %files 绕过打包问题。

### 4.1 构建结果

**构建成功，无重跑。** GBS 真实退出码 0；开始 11:05:43、结束 11:20:13（+08:00），worker 计时 **870.697 秒，约 14 分 31 秒**。Ninja 总计 **126 步**，相对原基线 7,633 步为 **1.65%**；未触发异常重编停止条件，没有多余安装文件导致的打包失败。日志完成安装、检查、RPM/SRPM 写出及成功收尾；没有修改 `%files` 绕过任何失败。[构建记录与末尾 200 行](evidence/02/07_build_record.txt)

```text
START 2026-11-02T11:05:43+08:00
BUILD_START 2026-11-02T11:05:43+08:00
END 2026-11-02T11:20:13+08:00
GBS_EXIT 0
ELAPSED_SECONDS 870.697
NINJA_TOTAL_OBSERVED 126
STOP_REASON 
ALL-END 2026-11-02T11:20:13+08:00 OK
```

126 步包含 LLDB 头文件 staging、compiler-rt 的 dummy 对象及辅助步骤；llvm-profgen 没有编译/链接步骤。大部分墙钟时间花在完整安装、调试信息拆分、静态归档 strip 与打包，这与 00 报告“GBS 增量仍执行完整安装/打包”的结论一致。

### 4.2 资源观测

以下为开始、每 10 分钟和结束的整机离散采样，不是构建独占 RSS 或连续峰值。完整 free/uptime 原文见构建证据。

| 时间（+08:00） | used MiB | available MiB | load 1 / 5 / 15 min |
|---|---:|---:|---|
| 2026-11-02T11:05:43+08:00 | 14968 | 16571 | 1.25 / 1.37 / 1.06 |
| 2026-11-02T11:15:46+08:00 | 14715 | 16825 | 2.46 / 2.83 / 2.15 |
| 2026-11-02T11:20:13+08:00 | 14988 | 16552 | 11.22 / 6.71 / 3.8 |

观测 used 峰值 **14988 MiB**、available 最低 **16552 MiB**；load 峰值 **11.22 / 6.71 / 3.8**。没有采样点 available 低于 2048 MiB。峰值均在最后一次采样；构建不足 20 分钟，故没有第二个 10 分钟周期点。[机器可读记录](evidence/02/08_artifact_resources.json)

## 5. 构建后工具与 C1 复核

`build/bin/llvm-profgen` SHA-256 仍为 `a31073338f9315a0fd6d2934e36431d9135086882ebfb07bd1bda7c36d7f9f1e`。工具内容与复制存档时保留的 mtime_ns 均相同，Ninja 日志中没有 llvm-profgen 编译/链接步骤：**本次没有重新链接 llvm-profgen**。不能将此结果描述成“已验证重新链接后的字节稳定性”，本轮实际证明的是仅开启测试配置的增量构建未改变工具及 C1 行为。

构建后的同一路径工具再次执行 compare 模式，命令：

```bash
cd /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent
export TMPDIR="$PWD/temp/tmp"
nice -n 19 ionice -c3 python3 tools/profgen/c1_baseline.py   --manifest "$PWD/temp/profgen-lit-prep/rebuilt-c1.json"   --compare "$PWD/tools/profgen/c1-baseline.json"
```

结果：50 个原测试、636 行/遍，两遍一致，**与原基线清单 0 条差异**，新增未纳入 C1 的测试列表为空。源码未改；原清单没有覆盖。新的命令名处理不更改输出字节，而是保证不同工具存放位置下实际 argv[0] 一致。[摘要](evidence/02/10_rebuilt_c1.json)、[日志](evidence/02/10_rebuilt_c1.log)

后续真正修改源码后，需用候选工具的预期哈希传 `--expected-tool-sha <新哈希>`，或者显式关闭旧哈希守卫；本轮工具哈希未变，默认守卫通过。不要以存档工具代替候选工具做补丁验收。

## 6. 原有 lit 基线

GBS `%check` 在原 x86_64 root 中实际运行了 `build/bin/llvm-lit -sv -j1`，仅覆盖 `test/tools/llvm-profgen`，完整生成固定 xunit 文件。配置证据见 [06_lit_config.txt](evidence/02/06_lit_config.txt)；原始 [lit 日志](evidence/02/09_lit.log)、[xunit XML](evidence/02/09_lit.xml)。

| 分类 | 数量 | 测试名/原因 |
|---|---:|---|
| PASS | 48 | 完整名称表见下文 |
| FAIL | 0 | 清单为空，无需要解释或修复的 FAIL |
| UNSUPPORTED | 1 | `cs-preinline-cost.test`：`REQUIRES: asserts`，XML 明示 Missing required feature(s): asserts |
| XFAIL | 1 | `invalid-perfscript.test`：原文件第 9 行 `XFAIL: *`，无效 perf script 的已知预期失败 |
| XPASS | 0 | 无 |
| UNRESOLVED / TIMEOUT | 0 / 0 | 无 |
| 其他未执行/排除项 | 0 | 本轮显式 scope 下发现 50 项；没有自行跳过或修复测试 |

lit 总时间 2.73 秒。`LLVM_ENABLE_ASSERTIONS=No` 保持不变，因此该 UNSUPPORTED 符合配置；没有改测试 REQUIRES，也没有用强制执行掩盖不支持项。其他 x86 target/Linux 条件在当前 root 满足。

注意：本版 lit 的 xunit writer 将 XFAIL 记录为普通非失败 testcase，单看 XML 会得到 49 个“非失败且未跳过”项；**不能将其误报为 49 PASS**。结合 lit 文本的 48 PASS / 1 XFAIL 汇总和此目录唯一 `XFAIL:*` 指令，确定 XFAIL 名称。XML 的 UNSUPPORTED 名称和原因有直接记录。[对应测试指令与 xunit writer 源码](evidence/02/09_lit_classification.txt)

PASS 48 项：

| 测试名 | 结果 |
|---|---|
| `afdo-with-vtable-pie.test` | PASS |
| `afdo-with-vtable.test` | PASS |
| `callback-external-addr.test` | PASS |
| `coff-profile.test` | PASS |
| `cold-profile-trimming-symbolized.test` | PASS |
| `cold-profile-trimming.test` | PASS |
| `context-depth.test` | PASS |
| `coroutine.test` | PASS |
| `cs-extbinary.test` | PASS |
| `cs-external-address.test` | PASS |
| `cs-interrupt.test` | PASS |
| `cs-invalid-ret-addr.test` | PASS |
| `cs-preinline-sample-profile.test` | PASS |
| `cs-preinline.test` | PASS |
| `cs-tailcall.test` | PASS |
| `disassemble.test` | PASS |
| `filter-ambiguous-profile.test` | PASS |
| `fname-canonicalization.test` | PASS |
| `fs-discriminator-probe.test` | PASS |
| `fs-discriminator.test` | PASS |
| `func-split.test` | PASS |
| `help.test` | PASS |
| `inline-cs-noprobe.test` | PASS |
| `inline-cs-pseudoprobe.test` | PASS |
| `inline-force-dwarf.test` | PASS |
| `inline-noprobe.test` | PASS |
| `inline-noprobe2.test` | PASS |
| `inline-probe-afdo.test` | PASS |
| `inline-pseudoprobe.test` | PASS |
| `invalid-range.test` | PASS |
| `merge-cold-profile.test` | PASS |
| `missing-dwarf.test` | PASS |
| `mmapEvent.test` | PASS |
| `multi-load-segs.test` | PASS |
| `noinline-cs-noprobe.test` | PASS |
| `noinline-cs-pseudoprobe.test` | PASS |
| `noinline-noprobe.test` | PASS |
| `noinline-pseudoprobe.test` | PASS |
| `profile-density.test` | PASS |
| `pseudoprobe-decoding-discriminator.test` | PASS |
| `pseudoprobe-decoding.test` | PASS |
| `recursion-compression-noprobe.test` | PASS |
| `recursion-compression-pseudoprobe.test` | PASS |
| `separate-debuginfo-binary.test` | PASS |
| `split-dwarf.test` | PASS |
| `symbolize.test` | PASS |
| `truncated-pseudoprobe.test` | PASS |
| `update-samples.test` | PASS |

## 7. 收尾、挂账与证据边界

- 基线存档在 temp 下保留，已提交基线清单内容不变；新 C1 脚本、报告、证据与 STATUS 同一项目提交。
- LLVM 本地分支 HEAD 仍为补丁 1；唯一跟踪文件差异是开发专用 `packaging/llvm.spec` 两处改动，未暂存或提交。**正式非增量构建前必须撤销**，本轮保留供后续增量开发；不把此 spec 放进增强补丁。
- 新测试在 C1 中排除，但应进入正式 lit 验收；现有原测试如需修订，应另行说明并更新基线策略，不能绕过当前完整性门禁。
- 本轮 lit 没有 FAIL；UNSUPPORTED 和 XFAIL 原样保留。没有新增 llvm-profgen 功能实现，也没有开始补丁 2；下一步等待授权。
- 资源观测包含其他会话的整机使用，不能声称捕获连续峰值。后台结束标记覆盖本次正常完成；SIGKILL、断电不可能靠普通 finally 保证落盘。
- 新增提交文件均小于 1 MB；全构建日志、完整临时 C1 清单、profile、RPM、基线工具和库只留 temp。原 C1 stderr 证据未改写。
- 无新增已知项目文件边界例外。系统工具/已有 sudo 与 Git 认证按长期规则使用，未修改其配置，未索要凭据。
