# LLVM 增量构建准备与 x86_64 未修改基线

## 结论

**可以增量，但需要满足条件。** 当前 spec 是单阶段 CMake/Ninja，`mkdir -p build` 后保留已有对象，没有每轮删除构建目录；修改 llvm-profgen 的单个实现文件原则上只需重编受依赖影响的对象并重链接。GBS 的 `--incremental` 本身不保证“只重编改动文件”：它每轮仍完整执行 `%build`、`%install` 及打包步骤。

必要条件：同一 worktree、相同 buildroot/编译器/宏/flags/CMake 配置，保留 build 目录；先准备 `%prep` 被跳过的 MLGO 资产；后续不加 `--clean`/`--clean-once`，不反复覆盖资产时间戳。`--noinit` 只能在依赖和配置已就绪后使用，不等于增量，也不替代 `--incremental`。**不需要修改当前 spec 才具备增量条件，本轮没有改 spec 或任何 LLVM 跟踪文件。**

一次仅 llvm-profgen `.cpp` 改动的估算：对象编译及该工具链接约 **1–5 分钟**；通过完整 GBS 流程含 CMake 检查、全包安装/strip/压缩，约 **10–40 分钟**，负载和磁盘可使其更长。这是源码结构推断的粗估，未做源码修改后的计时。公共头文件/LLVM 库变化会扩大重编/重链接范围；不能把单工具估算套用于 LLVM 全包。基线成功也不等于已经动态验证一次差量构建。

## 1. GBS/depanneur 的实际行为

证据：[01_incremental_source.txt](evidence/01_incremental_source.txt)。下列 `G/` 表示 `temp/pmuv3-prep/gbs-source/BUILD/`（GBS 2.1.0），`D` 表示 `temp/pmuv3-prep/BUILD/depanneur`（0.16.30），`B/` 表示 `temp/profgen-prep/build-source/build-20160629/`（发行版 build 20160629-tizen20260814）。

| 问题 | 结论 | 文件:行号 |
|---|---|---|
| 源码如何进入 root | 普通模式导出；增量跳过导出流程、bind mount `project_base_path` 到 BUILD/name-version，构建结果实际留在临时 Git worktree | `D:2943–2946,3010–3024,2162–2207`；`G/docs/GBS.rst:914–925` |
| 是否跳过 `%prep` | 是。初次 root 不存在会 `--no-build` 初始化，然后增量使用 short-circuit，从 `-bc` 开始；不会执行 `%prep` 里的解包/补丁动作 | `D:2178–2198`；`B/build-recipe-spec:150–172` |
| 是否执行完整 `%build` | 是，每次都从 `%build` 脚本开头执行；是否复用对象由 CMake/Ninja/spec 决定 | `G/docs/GBS.rst:934–944`；`B/build-recipe-spec:158–172` |
| 是否还生成 RPM | 是，build helper 依次 `--short-circuit -bc -bi -bb -bs`，包含安装、二进制 RPM、SRPM；depanneur 收集结果。帮助文字称“不产包”已落后于实现 | `D:319–327`（旧描述）、`:2198,2250–2265,2276–2305`（实现）；`B/build-recipe-spec:158–172` |
| SRPM 是否等同正常完整源码包 | 不能这样认为。增量模式创建临时占位 Source0，结束删除；即使有 SRPM，也不能把它当成正常导出源包的可复现基线 | `D:2206–2207,2236–2239`；源码基线须保留 Git commit/worktree |
| `--noinit` | 跳过远端仓库解析/初始化；要求 scratch.0、.guessed_dist 和保存的配置已存在。可与 incremental 叠加；第一次不能用。单独 noinit 并不自动保留 `%prep` | `G/gitbuildsys/cmd_build.py:625–629`；`D:528–547,2067,2246–2247` |
| 限制 | 仅 Git 风格单包；不能依赖 `%prep` 应用补丁/生成输入；noinit 也仅单包，不能与 clean/clean-once 并用；删除 root 前须确认源目录已卸载 | `D:494–497,3140–3145`；`G/gitbuildsys/cmd_build.py:819–822`；`G/docs/GBS.rst:918–944` |
| `--no-configure` | 只将 `%configure/%reconfigure/%autogen` 宏替换为 echo，**不能跳过本 spec 的裸 cmake 命令** | `D:2188–2193`；`G/tools/gbs:268–273` |

为核对 `--stage=-bs` 的含义，补充取得官方 build 源码及发行版 diff，仅在 temp 解包/应用该发行版补丁，不安装。来源 `https://download.tizen.org/tools/latest-release/Ubuntu_24.04/`，文件 `build_20160629.orig.tar.gz` SHA-256=`e4f31e9761630dc50b348fbaba86e370e0ee9e7249a6d8bb3fdd16bcb7a9a972`；`build_20160629-tizen20260814.diff.gz` SHA-256=`03e8c42d3e6ecda0b99beb54129bd6451deab5408a1ab51fb962718a8d7c516c`，均与下载的 .dsc 一致。不能只依据 GBS 老帮助文本判断“不出 RPM”。

## 2. 当前 llvm.spec 对增量的影响

固定 `src/llvm` 提交：`f999bd406c0a70fe8107aa992164fe6945c5d46a`。下表路径均为 `src/llvm/packaging/llvm.spec`，摘录在 E1。

| 检查 | 结论 | 行号 |
|---|---|---|
| `%prep` | `%setup -q`，x86_64 默认启用 MLGO，展开 Source1004 到 mlgo_verify_assets。增量模式不会执行这些步骤，必须先准备生成资产 | `:7–9,44–46,155–168` |
| `%build` 是否清理对象 | `mkdir -p build; cd build; cmake ... ../llvm`；没有 rm build、ninja clean 或强制新目录。configure-only 验证分支删除的是独立 mlgo_probe_root，默认宏为 0 | `:48–49,188–198,274–283,329–344` |
| 多阶段 bootstrap | 未见 stage1/stage2 自举流程。一次 CMake 配置、一次全目标 Ninja；LLVM_OPTIMIZED_TABLEGEN 不是整个编译器的两阶段 bootstrap | `:198–274,343–344` |
| 每次 cmake | 每轮重新配置，但参数/生成文件内容不变时 Ninja 可复用对象；编译器、flags、宏或生成输入变化会触发重编。不能保证 cmake 每次都全量，也不能保证它永远零影响 | `:198–274` |
| ThinLTO / PGO | 本 spec 未设置 LLVM_ENABLE_LTO、LLVM_BUILD_INSTRUMENTED、LLVM_PROFDATA_FILE/PGO 或 bootstrap；实际 CMakeCache 已确认 LLVM_ENABLE_LTO=OFF、LLVM_BUILD_INSTRUMENTED=OFF、LLVM_PROFDATA_FILE 为空，CFLAGS/CXXFLAGS 没有 -flto/-fprofile；使用的是平台 clang，不能按提交标题推断成 GCC | `:170–178,201–213,216–218,235–241`；定向搜索与实际记录见 E1/E3 |
| MLGO | 使用随包 AOT 模型/运行时对象，不在本机 TensorFlow 训练；修改这些输入会扩大重编。MLGO 不等于插桩 PGO 或 ThinLTO；模型复制走 configure_file(COPYONLY)，见 src/llvm/llvm/cmake/modules/TensorFlowCompile.cmake:74–88 | `:41–46,188–193,257–273` |
| 并发 | Ninja 使用 `mlgo_build_jobs`，仅设置 `_smp_mflags` 不足；CMake 固定编译池 6、链接池 2 | `:48,255–256,343–344` |
| 安装/打包成本 | 每轮执行全部 cmake install、LLDB/绑定复制和打包，未按 llvm-profgen 单工具裁剪；debug 后处理也可能耗时 | `:24–29,346–378`；profgen 被 `%files` 收录 `:443` |

若后续希望比完整 GBS 增量更快，可以设计仅构建 llvm-profgen 的开发模式，跳过无关安装/打包，并对 MLGO 预处理做显式条件。但这是建议，不修改本轮 spec，也不把单工具结果冒充完整包构建。

## 3. 基线准备及运行参数

新 worktree：`WORKDIR/temp/llvm-profgen-enh`；分支 `afdo/profgen-enhance`；起点为上述 commit，没有新增源码提交。`src/llvm` 开始 status 为空，原树不参与构建。第一次增量启动没有 build/对象缓存，因此是**全量编译目标**，而非从已有 LLVM 构建产物续编。

为满足增量跳过 `%prep` 的条件，仅将该提交的 `packaging/mlgo_x86_model.tar.gz` 按 spec 原命令解到临时 worktree 的 `mlgo_verify_assets/`。这属于 temp 下生成的构建输入，不修改任何跟踪源码/spec；GBS 后续还会产生 build/、manifest 等临时文件。以后复用时不重复解包以免改变时间戳。没有改 `config/` 原配置。

`temp/gbs/gbs_llvm_x86_baseline.conf` 复制 `temp/gbs/gbs_rpi5_image.conf`，仓库仍为：

- Unified：`https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261027.063617/repos/standard/packages/`
- Base：`https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261026.051209/repos/standard/packages/`
- buildroot=`WORKDIR/temp/GBS-ROOT-LLVM-X86`；tmpdir=`WORKDIR/temp/gbs-tmp-llvm-x86`。

构建前 ps 未发现其他 ninja/clang/gbs/depanneur/make/链接重任务（不把编辑器 clangd 当编译任务）；worker 也实现有任务就每 600 秒再查。起始 nproc=20，并发参数取 10；spec 内编译池 6、链接池 2 保持原样。

完整 worker 用 `setsid --fork nice -n 19 ionice -c3 python3 WORKDIR/temp/profgen-prep/worker.py` 启动、全部标准流重定向/脱离调用会话；只有 GBS 及子进程使用专用 HOME/GIT_CONFIG_NOSYSTEM。实际子命令：

```text
setsid --wait nice -n 19 ionice -c3 gbs -c WORKDIR/temp/gbs/gbs_llvm_x86_baseline.conf build -A x86_64 --spec llvm.spec --incremental --threads 1 --define '_smp_mflags -j10' --define 'mlgo_build_jobs 10'
```

GBS 环境：`HOME=WORKDIR/temp/gbs-home GIT_CONFIG_NOSYSTEM=1 TMPDIR=WORKDIR/temp/gbs-tmp-llvm-x86`。显式选 llvm.spec 是因为 packaging 下还有 libcxx-runtimes.spec，增量只允许单包。首次不使用 --noinit；后续同配置可考虑添加 --noinit。日志 `temp/profgen-prep/logs/baseline.log`、状态 `baseline.status`；worker 每 600 秒保存 free -m/uptime 到 resources.txt，并在开始/结束各采一条。峰值只指这些离散采样观测值，不能替代连续监测或单进程峰值 RSS。低内存阈值按 free -m 的 available 列 <2048 MiB 判断，不使用 free 列。

## 4. 构建结果（已完成）

**基线构建通过，没有重跑。** 证据：[03_baseline_build.txt](evidence/03_baseline_build.txt)。从空 build 目录完成 7,633 个 Ninja 构建步骤，完整执行安装与打包；本次启用 incremental 是为保留后续复用环境，不代表已实测修改文件后的差量构建。

```text
START 2026-10-28T20:33:42+08:00
BUILD_START 2026-10-28T20:33:42+08:00
END 2026-10-28T21:33:09+08:00
GBS_EXIT 0
ALL-END 2026-10-28T21:33:09+08:00 OK
```

总用时 **59 分 27 秒**，GBS 成功包计数 1 是源包 llvm；其下实际输出 **22 个二进制 RPM + 1 个 SRPM**。没有借用别轮退出码，也没有补写结束标记。外层日志第 10811 行为 `[7633/7633]`，成功汇总和末尾打包原文在 E3。

### 4.1 资源记录

时间均为 2026-10-28 Asia/Shanghai；总内存 31,540 MiB。每 10 分钟采样，另包含开始/结束点：

| 时间 | used MiB | available MiB | load 1/5/15 min |
|---|---:|---:|---|
| 20:33:42 | 12096 | 19444 | 2.35 / 3.13 / 2.63 |
| 20:43:42 | 13027 | 18513 | 7.99 / 6.19 / 4.12 |
| 20:53:42 | 14876 | 16663 | 10.43 / 10.58 / 7.16 |
| 21:03:42 | 13408 | 18132 | 7.85 / 8.05 / 7.35 |
| 21:13:42 | 13231 | 18309 | 11.10 / 8.47 / 7.71 |
| 21:23:42 | 12050 | 19490 | 15.11 / 10.56 / 9.17 |
| 21:33:09 | 12783 | 18757 | 10.83 / 8.20 / 8.15 |

观测到 used 峰值 **14,876 MiB**、available 最低 **16,663 MiB**，均在 20:53:42；没有采样点低于 2GB。1/5/15 分钟 load 的观测峰值分别为 **15.11 / 10.58 / 9.17**（21:23:42 / 20:53:42 / 21:23:42）。这是整机离散观测，包含其他会话活动，不是构建独占内存或连续峰值。

### 4.2 产物清单与 SHA-256

目录：`temp/GBS-ROOT-LLVM-X86/local/repos/tizen_unified_standard/x86_64/RPMS/`；最后一项在同级 `SRPMS/`。文件及构建目录只保留 temp，不提交。逐文件 sha256sum 退出码均为 0，原命令见 E3。

| 文件 | 字节 | SHA-256 |
|---|---:|---|
| clang-22.1.8-1.x86_64.rpm | 29045992 | `46725a77f733fcc152e7f30b9062f7a2aa1f82179f8ed6242ec783e26e4384cc` |
| clang-debuginfo-22.1.8-1.x86_64.rpm | 321657648 | `5bde462c558616f378026ec0677ec7ce43842535c325b73e9b171d8357ae2a11` |
| clang-devel-22.1.8-1.x86_64.rpm | 4062832 | `0f25b1ad76fe57ca5685ff87499ded56037f97532591ec04147fb20d4f0851f0` |
| clang-devel-debuginfo-22.1.8-1.x86_64.rpm | 6348380 | `6f3b91d9475f08fff36d88e294fb2b1dc1373affc64049c20108480daae56848` |
| compiler-rt-22.1.8-1.x86_64.rpm | 3720376 | `860077cbdef4ee83d955b3f4f9baeeb5c852c47c4ccd2e7ee45a62172c80731d` |
| compiler-rt-debuginfo-22.1.8-1.x86_64.rpm | 1289320 | `2d7d257edb146f1bac44db23817b53d4d7d23de1e716554ebaef60172a128ca4` |
| libllvm-22.1.8-1.x86_64.rpm | 21244892 | `d23f5f15d6a89c694ac7e6b674dbf35de842470b82a5de7f5a46888170265eeb` |
| libllvm-debuginfo-22.1.8-1.x86_64.rpm | 187419108 | `27f2db63c5fea45c907ebd9ab9b0449dc7f72c9aa3b072caf62ef6eb0a5c0fbe` |
| libomp-22.1.8-1.x86_64.rpm | 341364 | `61dab037f38d0b32e435e852742d34ba07943556366c319c2e033e18b7ec2ffb` |
| libomp-debuginfo-22.1.8-1.x86_64.rpm | 1033676 | `b6e1bd21a12f97d633ece0fabef8c8aee8a454097fc4942acbfd150bc0082afb` |
| libomp-devel-22.1.8-1.x86_64.rpm | 25544 | `1fa596f65d909ebced98a91beb9cfb5622c3a3d2f17c21981d05b8dd0cf5e046` |
| lldb-22.1.8-1.x86_64.rpm | 4860100 | `f84d85d703b4f61f3e1959a39c91757ea90d5458c90d1c76f35a9db04ad0c3f9` |
| lldb-debuginfo-22.1.8-1.x86_64.rpm | 73501428 | `abbac0d23a2eeb559c239822b8bcc246131513cf7389c30af823ad17885893fa` |
| lldb-devel-22.1.8-1.x86_64.rpm | 5040420 | `036ce604ba7b7d9597a1c7192b767cc433250d109fd88cd63370b1477e8b7256` |
| lldb-devel-debuginfo-22.1.8-1.x86_64.rpm | 51174760 | `91318bb1dcf2b6cd83b8f04a41f54daa241a1e7d0ed8c631772d30c95c3ee885` |
| llvm-22.1.8-1.x86_64.rpm | 16778172 | `da0d9eda7864af5dfd0892d5200bfe6b726b0ce3172956eb750462c48ac9422b` |
| llvm-debuginfo-22.1.8-1.x86_64.rpm | 169654472 | `3bfd6853cc7367071941d940599658d5606697d984b1b850ea67af8da65b5d0d` |
| llvm-debugsource-22.1.8-1.x86_64.rpm | 43687380 | `a34ca717563bece2b2aaf21eb2eb7eca1eda0d45b91213aee1b57b99e637e85c` |
| llvm-devel-22.1.8-1.x86_64.rpm | 5327436 | `72154b4c2c10a82900892e57c33c2e261e56e7148f376abba6a210880c0a4ad5` |
| llvm-devel-debuginfo-22.1.8-1.x86_64.rpm | 433984 | `6f782039e67d067fc693d44d1f08ecaa5f5b4f4d624140423312b8b04301f5ea` |
| llvm-static-devel-22.1.8-1.x86_64.rpm | 60867264 | `9a531b47ce3c53fcb4e30f14b6a0beceecb7ecb86bda8d8dd71ff6b287ef6c69` |
| python-clang-22.1.8-1.x86_64.rpm | 36256 | `194cec207aa500237e486a1ec60822875384cfcc2080521b607b3c83bea53bf3` |
| llvm-22.1.8-1.src.rpm | 86962605 | `f9b43d8da92c0134ad98cecae9334949a49ca665c2ec717ec67c470fe2bd654f` |

**增量模式产包限制：** 平台 RPM 查询确认 llvm 包包含 `rpmlib(ShortCircuited)` 依赖；这些是开发验证产物，不能当作正常发布包直接部署。增量 SRPM 的 Source0 使用占位文件，也不等同完整 LLVM 导出源包；基线由固定 Git commit、worktree、配置和日志共同标识。这里的“完整构建”指所有目标的编译、安装、产包均完成，不声称等价于常规非 short-circuit 发布流程。

### 4.3 本次 llvm-profgen 可执行验收

下列别名均指 WORKDIR 内绝对路径，实际展开后的命令和真实输出保存在 E3：

```text
R=WORKDIR/temp/GBS-ROOT-LLVM-X86/local/BUILD-ROOTS/scratch.x86_64.0
B=WORKDIR/temp/llvm-profgen-enh/build
nice -n 19 ionice -c3 R/lib64/ld-linux-x86-64.so.2 --library-path B/lib64:R/lib64:R/usr/lib64 B/bin/llvm-profgen --version
EXIT 0
LLVM (http://llvm.org/):
  LLVM version 22.1.8
  Optimized build.
```

使用 GBS root 的加载器、readelf 2.43 和基础库；`--list` 确认 libLLVM.so.22.1 来自**本次新编的 B/lib64**，其余依赖来自 R。没有以旧平台 profgen 冒充新产物，也没有使用本机 readelf 分析。新可执行文件 SHA-256：`a31073338f9315a0fd6d2934e36431d9135086882ebfb07bd1bda7c36d7f9f1e`。平台 readelf 确认为 ELF64/x86-64 PIE，动态依赖解析成功。

现有打包日志有缺 build-id 警告；新 profgen 的 `readelf -n` 只有 GNU ABI tag，没有 GNU build-id。本轮不改 spec 补参数，工具可执行性与目标二进制身份校验是两个不同验收项。

额外 RPM 依赖查询最初使用 `--requires` 返回 1：`rpm: --requires: unknown option`，使临时验证助手断言停止；此前 GBS 和新 profgen 运行已分别返回 0。随后仅改用只读查询格式 `--qf '[%{REQUIRENAME} %{REQUIREFLAGS} %{REQUIREVERSION}\n]'`，返回 0 并确认 ShortCircuited。失败原文与成功替代查询均保留，不隐藏为零退出；未重跑构建、未修改配置/源码。

### 4.4 源码收尾与范围

`src/llvm` 开始/结束 `git status --porcelain` 都为空，HEAD 保持 f999bd406c0a70fe8107aa992164fe6945c5d46a；新 worktree 的跟踪文件 diff 为空，只留 MLGO 展开资产、build 与打包 manifest 等生成文件。Google temp/autofdo 状态也为空。没有 LLVM 源码提交，没有向 Gerrit 推送，没有连接开发板。保留 worktree/对象/root 供设计确认后的增量开发，本轮不再构建。

## 5. 边界例外

本轮无新增已知边界例外。所有项目下载、构建、日志和产物均在 WORKDIR/temp；GBS chroot 中显示的 /home/abuild 路径对应此处 buildroot 或 bind 的临时 worktree。未执行全系统 syscall 审计，不把“未发现”表述为对所有系统服务隐式写入的完整证明；历史 SDB 日志例外仍保留在 STATUS，本轮未使用 SDB。
