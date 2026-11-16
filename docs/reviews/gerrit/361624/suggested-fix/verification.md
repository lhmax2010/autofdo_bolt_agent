# Gerrit 361624 建议补丁验证

日期：2026-11-16。本轮仅在独立工作树应用用户提供的补丁，不修改补丁；不接板、不操作 Gerrit、不改 hq。

## 1. 文件与应用

指定 Downloads 文件以 `mv` 入库，移动前后 SHA-256 均为 `8259a8d4504965b52167baeaf1667570bc6b46ff07682631b78ee8d12ca4b678`。原路径不留副本。

- 基线：`da885208aeb52f55c448ff46873d242346727522`。
- 独立工作树：`temp/verify-361624-fix-20261116/source`；来源 `temp/gerrit-361624-ssh`。
- `git am` 退出 0，无冲突，结果提交 **ae93ed9b5f98bc7991a1537feac4f5eff61e3e22**。
- 命令及输出：[apply.json](evidence/apply.json)、[worktree.log](evidence/worktree.log)。补丁作者与原提交信息保留；本仓库交付提交署名 Hao Lin。

## 2. 只读 spec 解析

使用 LLVM 发布 root `temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0` 的 loader、rpmspec、GBS/Tizen 宏，`_build_create_debug=1`。未执行 %prep/%build。每个组合分别运行展开、二进制包查询、BuildRequires 查询，最终 24 次命令均退出 0。

完整环境和逐次 argv/stdout/stderr 见 [parse-tizen](evidence/parse-tizen/summary.json)；[执行脚本](evidence/parse_specs.py)；[断言](evidence/parse-assertions.json)。

| tools spec 架构 | ExclusiveArch | bolt_targets | LLVM_LIBDIR_SUFFIX | 查询结果 |
|---|---|---|---|---|
| x86_64 | x86_64 aarch64 | X86;AArch64 | 64 | 成功 |
| aarch64 | x86_64 aarch64 | AArch64 | 64 | 成功 |
| armv7l | x86_64 aarch64 | AArch64（else 分支） | 空 | 查询退出 0，仍不属于 ExclusiveArch |
| i586 | x86_64 aarch64 | AArch64（else 分支） | 空 | 查询退出 0，仍不属于 ExclusiveArch |

`rpmspec -P/-q` 不因 ExclusiveArch 不包含目标而拒绝本次查询。这不是 armv7l/i586 获准构建的证据；本轮不实际构建这两种架构。

x86_64/aarch64 的 BuildRequires 都是：clang、cmake、compiler-rt、libllvm = 22.1.8、libomp = 22.1.8、libxml2-devel、llvm = 22.1.8、llvm-devel = 22.1.8、llvm-static-devel = 22.1.8、ninja、zlib-devel。bolt 的 spec 显式 Requires 为 `libllvm = 22.1.8`，无 compiler-rt；ELF 自动依赖须以实际 RPM 为准。

两架构包列表均为 `llvm-tools-subpkgs`、`llvm-tools-subpkgs-debuginfo`、`llvm-tools-subpkgs-debugsource`、`bolt`。这是解析出的包定义，实际文件是否产出仍须构建核验。

llvm.spec：x86_64 与 armv7l 的 llvm 运行 Requires 均只移除了 python3；BuildRequires 前后不变，因而 x86_64 的 Python 构建依赖仍保留。armv7l 的 LLVM_TARGETS_TO_BUILD 从 `ARM;AArch64;X86;BPF` 变为 `ARM;BPF`；x86_64 仍为 `X86;ARM;AArch64;BPF`。除上述变化及所删注释外，无其他展开差异。

前后原文与 diff：[x86_64](evidence/parse-tizen/llvm.spec-x86_64-expanded.diff)、[armv7l](evidence/parse-tizen/llvm.spec-armv7l-expanded.diff)、两侧 packages.diff/buildrequires.diff 均在同目录。

最初只指定 `--macros`、未指定 RPM_CONFIGDIR 的执行器试验加载了主机 RPM 环境，原 llvm.spec 与新 llvm.spec 都报 `Unknown tag: %[ (1)`，且工具包未显现调试子包。补充 `RPM_CONFIGDIR=<发布root>/usr/lib/rpm` 和 `HOME=<发布root>/home/abuild` 后全部通过；没有修改 spec。初次失败输出保留在任务 temp 的 `parse/`，不将执行器环境错误归为补丁缺陷。

## 3. 固定仓库与构建资源

固定仓库：Base `20261030.120529`、Unified `20261104.125239`。两个 packages/repodata/repomd.xml 及所指 primary 元数据均 HTTP 200，压缩元数据 SHA 与 repomd 相符。[请求记录](evidence/repository-check/requests.json)。

Base 元数据中的 clang、compiler-rt、libllvm、libomp、llvm、llvm-devel、llvm-static-devel 均为 x86_64 `22.1.8-4.1`（epoch 0），VCS 为 f999bd40；Unified 没有这些提供包。[提供包清单](evidence/repository-check/llvm-packages.json)。这是元数据前检，尚不代替 GBS 实际依赖解析。

独立构建 HOME/TMPDIR/cache/buildroot 位于 `temp/verify-361624-fix-20261116/`。GBS 计划 -j2、threads 1，实际构建 scope MemoryMax=6G、MemoryHigh=5G、CPUQuota=200%，nice19/ionice-c3。启动门禁 MemAvailable≥16GiB、load1<0.6×nproc、磁盘可用≥50GiB。

补丁直接调用 ninja，不读取 `_smp_mflags`。为落实 -j2，在 RPM 命令行 build/install prelude 保留 `%{___build_pre}` 后增加 shell 函数 `ninja() { command /usr/bin/ninja -j2 "$@"; }`，并设置 CMAKE_BUILD_PARALLEL_LEVEL=2；不改补丁或 spec。这是资源限制，不是修补打包逻辑。[参数与理由](evidence/resource-guard-v2.json)、[宏展开检查](evidence/resource-guard-eval-v2.json)。最初多行宏试验被 rpmspec 截断，断言失败后改为单行参数，未启动构建；该试验原文仍在 temp。

原启动门禁等待1183.958秒，未启动GBS；两次检查均不足16GiB。用户答复“本次临时取消限制”后，只取消16GiB启动门槛，仍检查load/disk；停止仅等待中的本任务service，原结束记录为signal 15，exit_code=null，不是GBS构建失败。等待原件保留在 `build/`，实际构建另记 `build-authorized/`。未改共用workflow模块。

## 4. 实际构建与产物核对

第一次实际GBS运行退出1、墙钟391.114秒（子进程390.120秒），scope峰值4,782,354,432 B，无OOM；失败发生在执行器的资源宏展开，尚未进入补丁的build命令：

```text
cd "/home/abuild/rpmbuild/BUILD" ninja() { command /usr/bin/ninja -j2 ; }; ...
syntax error near unexpected token `('
```

原因：prelude末尾无分隔符，且GBS传参提前展开了 `$@`。不归为补丁缺陷。已保留失败root、日志和生成脚本；不修改补丁/spec。执行器修正为用分号分隔prelude，并由RPM宏在GBS传参结束后生成引号与 `$@`。已通过root RPM展开、bash语法与build/install实参转发断言；在全新 `root-x86_64-retry-executor` 重跑。该次重跑仅修复执行器，不调整依赖、代码或打包规则。

执行器修正后 **GBS退出0，墙钟564.821秒**（子进程564.670秒），成功完成唯一授权的x86_64 tools包构建。结果：[收据](evidence/build-executor-retry/result.json)、[完整日志](evidence/build-executor-retry/build.log)、[逐分钟资源](evidence/build-executor-retry/resources.json)、[实际启动命令](evidence/build-executor-retry/command.json)。

原始命令（路径用TASK代表 `temp/verify-361624-fix-20261116`；完整绝对argv见证据）：

```bash
gbs -c "$TASK/gbs-retry.conf" build -A x86_64 \
  --spec llvm-tools-subpkgs.spec --include-all \
  --buildroot "$TASK/root-x86_64-retry-executor" --threads 1 \
  --define '_smp_mflags -j2' \
  --define '__spec_build_pre %{___build_pre}; ninja() { command /usr/bin/ninja -j2 %{lua:print(string.char(34,36,64,34))}; }; export CMAKE_BUILD_PARALLEL_LEVEL=2' \
  --define '__spec_install_pre %{___build_pre}; ninja() { command /usr/bin/ninja -j2 %{lua:print(string.char(34,36,64,34))}; }; export CMAKE_BUILD_PARALLEL_LEVEL=2'
```

这两个命令级宏只限制Ninja并行度。日志确认实际执行 `/usr/bin/ninja -j2 bolt bolt_rt` 与 `/usr/bin/ninja -j2 install`，不省略原spec目标。GBS成功日志计时432秒只涵盖其内部阶段；上述564.821秒含源码导出等主机侧步骤，不能混用。

实际root有120包，LLVM提供包均为22.1.8-4.1；日志出现 `BOLT is built against LLVM provider 22.1.8-4.1`。[rpm -qa](evidence/verification-smoke/installed-packages.stdout)。

资源：本次成功构建最低MemAvailable **12,628,295,680 B**（11.761GiB）；cgroup memory.peak **5,369,208,832 B**（5.000465GiB）；MemoryHigh事件940，max/oom/oom_kill均0，无运行中资源停止。成功scope及监督service均已结束；此前等待和执行器失败单元均已停止，无本任务构建继续运行。

### 4.1 RPM、依赖与身份

| RPM | 大小/B | SHA-256 |
|---|---:|---|
| bolt-22.1.8-1.x86_64.rpm | 1686510 | `da718adb2d4cc79484861ab61e2c41ce239ae1bd6600b5ad2b7edaa63d939cfe` |
| bolt-debuginfo-22.1.8-1.x86_64.rpm | 310938 | `2addc9486c7cceb6de4b6b38ae50b7ce449b35cd7cba177834f3204747b61816` |
| llvm-tools-subpkgs-debugsource-22.1.8-1.x86_64.rpm | 6730 | `7ebe135848b07cbf1eead97228167a40eac615de05e6e36979a82d51c7573fc5` |

完整文件清单：[bolt](evidence/verification/rpm-list-0.stdout)、[bolt-debuginfo](evidence/verification/rpm-list-1.stdout)、[debugsource](evidence/verification/rpm-list-2.stdout)。bolt含 `/usr/lib64/libbolt_rt_instr.a`、`/usr/lib64/libbolt_rt_hugify.a`；perf2bolt、llvm-boltdiff为llvm-bolt别名。

[rpm -qpR](evidence/verification/bolt-requires.stdout)含 `libllvm = 22.1.8` 与 `libLLVM.so.22.1(LLVM_22.1)(64bit)`，不含compiler-rt。5个实体工具的运行/debug SHA-1 build-id逐一相同，全部SHA详见[核对结果](evidence/verification-smoke/result.json)。

| 运行工具（对应.debug同名） | runtime/debug共同build-id |
|---|---|
| llvm-bolt | `a8aed4dac276af53a68d041f2efe2dbd849f5bbe` |
| llvm-bolt-binary-analysis | `40ea0ec2207b16c62d3082f653cc02123bc22655` |
| merge-fdata | `298fc9b73a949a13ef7fdb0d7fcee547c9501fb8` |
| llvm-bolt-heatmap | `6e7f1d95d985058076341ca50e4d68772141c0d5` |
| llvm-bat-dump | `234c30c7730fd734a8ebb57fcd05e4f906220804` |

llvm-bolt SHA-256：`2e011c6610fea8b24591037721048ed0b371e1dffdf70cb5024c2c897b778fd3`。

解包工具置于本次构建root的独立测试目录，在该root原libllvm下 [ldd](evidence/verification-smoke/ldd.stdout) 无not found；[--version](evidence/verification-smoke/version.stdout)退出0，LLVM22.1.8，含aarch64与x86-64。[构建时bolt-version.txt](evidence/verification-smoke/bolt-version.txt)也通过同样检查。

检查执行器最初尝试 `sudo -n mkdir` 被现有策略拒绝（a password is required），未请求密码或修改认证；随后用已有可用的 `sudo -n chroot <本次root> /bin/mkdir` 与chown创建同一测试目录，成功。原失败输出与命令、后续成功收据都保留在verification证据中；不是工具失败，没有重跑构建。

### 4.2 功能冒烟

root已有clang、ld.lld，使用自写 `_start`/answer 两函数汇编，不链接libc，不安装软件。完整命令与退出码：[commands.json](evidence/verification-smoke/commands.json)；源码：[AArch64](evidence/verification-smoke/aarch64.S)、[x86_64](evidence/verification-smoke/x86_64.S)。clang目标分别为aarch64-linux-gnu、x86_64-linux-gnu，ld.lld参数为 `-static --emit-relocs --build-id=sha1 -e _start`；llvm-bolt不带profile，使用 `-reorder-blocks=none -reorder-functions=none`。

| 输入 | BOLT退出 | relocation模式 | 输出反汇编 | 原程序/输出程序运行 |
|---|---:|---|---|---|
| AArch64静态ELF | 0 | 日志明确enabling relocation mode | llvm-objdump退出0 | 不执行跨架构程序 |
| x86_64静态ELF | 0 | 日志明确enabling relocation mode | llvm-objdump退出0 | 主机退出码7/7，完全相同 |

原始日志：[AArch64](evidence/verification-smoke/aarch64-bolt.stdout)、[x86_64](evidence/verification-smoke/x86_64-bolt.stdout)；重定位、反汇编、输入输出SHA均在同目录。AArch64日志“0 estimated cost”警告来自无profile的小例子，退出0，未将其计为性能验证。

### 4.3 发现的调试信息问题及建议（未修补）

1. **源码级调试信息不完整。** 虽然bolt-debuginfo含5份.debug且build-id全匹配，llvm-bolt.debug的DWARF只有glibc启动对象CU（start.S、abi-note.c、init.c、crti.S、crtn.S），没有BOLT源码CU。debugsource RPM `(contains no files)`。生成的[编译规则](evidence/verification/compile-flags-excerpt.txt)为 `-O3 -DNDEBUG`，无 `-g`；[完整DWARF原文](evidence/verification/llvm-bolt-dwarf-info.txt)与[节表](evidence/verification/llvm-bolt-debug-sections.txt)留证。不能以.debug文件存在、build-id相同宣称BOLT源码行级调试已具备。这来自原spec的Release构建方式，建议补丁未解决，不是此次修改新引入的编译回归。建议由补丁作者决定保留优化级别并显式加入调试选项，或采用适当的RelWithDebInfo配置，再验证BOLT源码CU与debugsource；本轮不自行修改。
2. spec注释称产生llvm-tools-subpkgs-debuginfo；实际Tizen打包重分配后为 **bolt-debuginfo**，不是只读rpmspec查询所列名称。建议按实产修改注释。主llvm-tools-subpkgs及其-debuginfo空壳没有产出RPM；debugsource RPM存在但空。解析结果与实产结果均保留，不覆盖前者。

**结论：补丁有问题（BOLT源码级调试信息缺失、调试包注释不准确）；本轮指定的x86_64编译、运行依赖、文件身份及AArch64/x86_64改写冒烟均通过。** 不把调试文件“存在”误报为完整可调试性，不把未执行的AArch64实际构建或完整llvm.spec构建记为通过。


aarch64 实际构建与 llvm.spec 完整构建按任务范围未执行。

## 5. 证据与边界

证据逐文件SHA：[SHA256SUMS](SHA256SUMS)。保留在temp的元数据、执行器、日志与源码RPM索引：[raw-index.json](raw-index.json)。

本轮原件目录：`temp/verify-361624-fix-20261116/`；保护的本地配置未读取或改动。没有板上、Gerrit、hq 操作，没有安装主机软件（GBS只在本任务的新root内安装构建依赖），没有修改已有证据或设计。

## 6. v2（仅注释）复核

日期：2026-11-16。按用户本轮指定的构建等价性验收口径执行；v1补丁和以上验证记录保留不变。本轮不重新GBS构建、不重新冒烟、不操作Gerrit、不改hq、不接板、不安装软件。

### 6.1 入库与应用

指定文件 `361624-suggested-fix-v2.patch` 由Downloads以mv移入本目录；移动前后SHA-256均为 **b0b1a05f67fb50a37c1351e776ff0a92c2dfd1f6e08be65068d1d5be0790f2e9**，Downloads不留副本。[移动收据](evidence/v2/move.json)。

从 `temp/gerrit-361624-ssh` 在基线 `da885208aeb52f55c448ff46873d242346727522` 创建独立工作树 `temp/verify-361624-fix-v2-20261116/source`，git am退出0、干净应用，结果提交 **d509bc12ee2f824025b3e54331257936a8dfc33a**。[工作树记录](evidence/v2/worktree.json)、[应用记录](evidence/v2/apply.json)。v1工作树未修改。

以下为 `git diff ae93ed9b5f98bc7991a1537feac4f5eff61e3e22 d509bc12ee2f824025b3e54331257936a8dfc33a` 完整输出，未过滤文件或上下文；唯一变化是 `%define debug_package` 上方注释，4行删除、7行增加。源文件差异断言见 [source-diff-assertions.json](evidence/v2/source-diff-assertions.json)，原文见 [v1-v2.diff](evidence/v2/v1-v2.diff)。

```diff
diff --git a/packaging/llvm-tools-subpkgs.spec b/packaging/llvm-tools-subpkgs.spec
index ee34485360dc..05f346e77c97 100644
--- a/packaging/llvm-tools-subpkgs.spec
+++ b/packaging/llvm-tools-subpkgs.spec
@@ -67,10 +67,13 @@ to improve instruction cache and TLB utilization.
 # itself; the standard debug_package macro would add them a second time
 # and fail with "package already exists". NOTE: keep percent signs out of
 # this comment -- rpmbuild expands macros even in comment lines.
-# Debuginfo IS still generated (find-debuginfo.sh runs from
-# __debug_install_post): the llvm-tools-subpkgs debuginfo and debugsource
-# packages are produced. The -Wl,--build-id=sha1 linker flags above make the bolt
-# binaries debug-correlatable.
+# find-debuginfo.sh still runs from __debug_install_post and moves the
+# separated debug files into bolt-debuginfo, named after the bolt
+# subpackage. BOLT is compiled with the CMake Release flags only, without
+# -g, as llvm.spec does for its release build, so these files hold symbol
+# tables but no source-level DWARF, and llvm-tools-subpkgs-debugsource is
+# empty. The build-id linker flags in the build section tie each debug
+# file to its binary.
 %define debug_package %{nil}
 
 %build
```

### 6.2 解析等价性

复用第2节同一发布root的rpmspec、加载器、全部宏路径；RPM_CONFIGDIR与HOME分别指向该root的 `usr/lib/rpm` 和 `home/abuild`，显式 `_build_create_debug=1`。v1/v2 × x86_64/aarch64 × 四种查询，共 **16次最终命令，全部退出0**。bolt Requires查询保存所有包的原始查询输出，再按精确包名bolt选取唯一记录，不以全包依赖代替bolt依赖。

完整执行器：[check_equivalence.py](evidence/v2/check_equivalence.py)；每条argv、环境、退出码和输入SHA：[commands.json](evidence/v2/parse-final/commands.json)；断言及各相同段的SHA：[equivalence.json](evidence/v2/equivalence.json)。

| 核对项 | x86_64 | aarch64 |
|---|---|---|
| 包列表 | 逐字节相同 | 逐字节相同 |
| BuildRequires | 逐字节相同 | 逐字节相同 |
| bolt Requires | 逐字节相同：libllvm = 22.1.8 | 逐字节相同：libllvm = 22.1.8 |
| rpmspec -P | 仅指定注释块不同 | 仅指定注释块不同 |
| %build | 逐字节相同 | 逐字节相同 |
| %install | 逐字节相同 | 逐字节相同 |
| 全部3个%files段（含自动调试段） | 逐字节相同 | 逐字节相同 |

解析差异原文：[x86_64](evidence/v2/parse-final/x86_64-expanded.diff)、[aarch64](evidence/v2/parse-final/aarch64-expanded.diff)。断言不仅忽略一般注释，而是确认用源文件中唯一改变的原注释块替换一次后，整个-P输出逐字节等于v2。`llvm.spec` 两树字节相同，按要求未重新解析。

执行器初次比较误把第一个自动生成的%files段至文件末尾当作一个段，包含了%prep下的注释，导致一次`files`比较断言失败；这8次初始查询本身均退出0。修正段边界后重新执行全部16次查询并通过。初次执行器、原始输出保留在本节证据的 `check_equivalence_initial.py`、`parse/`，原因见 [comparison-initial.json](evidence/v2/comparison-initial.json)；未修改补丁/spec。

### 6.3 结论与沿用范围

**v2 与已验证的 v1 构建等价，补丁通过验证。**

x86_64构建与冒烟沿用第4节：GBS退出0、564.821秒，RPM依赖/runtime静态库/运行调试build-id通过；AArch64与x86_64最小ELF改写均退出0、relocation模式，x86原/输出程序均退出7。本轮不重复执行这些步骤。

v2修正的是调试包名称与Release构建局限的注释，不增加BOLT源码级调试信息；第4.3节记载的实际内容（BOLT源码DWARF未生成、debugsource为空）保持真实有效。本轮用户指定的验收是注释改动不改变已验证构建行为，不将其表述为源码级调试能力恢复。aarch64实际构建、完整llvm.spec构建仍未验证。

全程nice19/ionice-c3、串行3G/200% scope；所记录三次MemAvailable最低 **13,087,903,744 B**，最终解析/比较scope的实读memory.peak **11,747,328 B**。资源记录见 [resources.json](evidence/v2/resources.json)；本轮未启动构建。

## 7. 构建环境缺陷（评审发现）

日期：2026-11-16。本节更正第3–4节及第6节对正常Tizen构建的外推；旧报告和原始证据保留，不改补丁。本轮仅归档评审、展开宏、生成脚本并做断言，**没有启动GBS，也没有执行生成的%build/%install脚本**。

### 7.1 两份评审原样归档

| 评审方 | 文件 | SHA-256 |
|---|---|---|
| Codex | [review_Codex.md](review_Codex.md) | `230bc239118b3600bde71cd1e56ff01c8b87c0217eb58f7ff623c73bcc1141da` |
| Claude Code | [review_claude_code.md](review_claude_code.md) | `ed61d2de826c63ff9dbbc143680f790a4c8306c7f323bf86b551e26d29623a07` |

内容未修改，提交前后核对相同SHA。关于链接参数、支持范围等其他建议只作为评审原文归档，本轮不改spec或补丁。

### 7.2 缺陷与原始证据

**错误来自本次验证执行器，而不是从这次结果可推导出的正常GBS编译行为。** 第3–4节使用的 `--define '__spec_build_pre %{___build_pre}; ninja()…'` 替换了Tizen原有的 `__spec_build_pre`，遗漏 `%{set_build_flags}`，丢失发行版CFLAGS/CXXFLAGS/LDFLAGS导出。安装前置段也被替换，遗漏原有可选STRIP_DEFAULT_PACKAGE分支与buildroot准备动作。

| 证据 | 原文件与行号 | 实测内容 |
|---|---|---|
| 旧验证构建 | `evidence/build-executor-retry/build.log` **483–769**（%build段） | 没有 `+ export CFLAGS`、CXXFLAGS、LDFLAGS；只保留了更基础的构建环境 |
| 旧构建CMake缓存 | `temp/verify-361624-fix-20261116/root-x86_64-retry-executor/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/rpmbuild/BUILD/llvm-22.1.8/bolt-build/CMakeCache.txt` **66、96、114** | `CMAKE_CXX_FLAGS:STRING=`、`CMAKE_C_FLAGS:STRING=` 均为空；EXE_LINKER_FLAGS仅 `-Wl,--build-id=sha1` |
| 正常LLVM发布构建 | `temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/repos/tizen_unified_standard/x86_64/logs/success/llvm-22.1.8-1/log.txt` **467–472** | 467赋CFLAGS（含-g2/-gdwarf-4/-g），**468导出CFLAGS、470导出CXXFLAGS、472导出LDFLAGS** |
| Tizen原始前置段 | 发布root `usr/lib/rpm/tizen/macros`（实际文件 `usr/lib/rpm/tizen_macros`）**229–232、234–239** | build包含set_build_flags；install保留可选strip设置以及删除/创建RPM_BUILD_ROOT |
| set_build_flags原定义 | 同root `usr/lib/rpm/macros` **1057–1060** | 分别设置并导出CFLAGS、CXXFLAGS、LDFLAGS |

上述文件的SHA与原行号摘录见 [source-evidence.json](evidence/executor-v4/source-evidence.json)、[旧日志](evidence/executor-v4/old-build-prelude.txt)、[发布日志](evidence/executor-v4/release-build-prelude.txt)、[CMakeCache](evidence/executor-v4/cmake-cache-flags.txt)、[Tizen宏](evidence/executor-v4/tizen-preludes.txt)、[set_build_flags](evidence/executor-v4/set-build-flags.txt)。发布root和旧验证root的Tizen宏SHA相同：`f0f991bd97f44b7bf906ac4a7a45cd34b7444c1acce2358261e4a95b3e68ebc8`。

**更正的范围：**

- 第4.1节的RPM/llvm-bolt SHA及5个build-id仅描述那个非标准环境的产物，不代表正常GBS构建。
- 第4.3节第1条“来自原spec的Release构建方式”及第6节关于正常构建缺少BOLT源码调试信息的外推撤回。原产物确实没有BOLT源码CU且debugsource为空，但不能据此认定正常Tizen构建也是如此。也不能因此要求补丁增加-g：原Tizen前置段本已提供调试选项。
- 第6节的“通过验证”仅保留v1/v2注释改动的构建等价性结论；正常Tizen环境的产物验收尚未完成，须等待另行授权的修正执行器重建。
- 包名、依赖、provider检查、--version检查与两项冒烟改写的已记录结论不受影响；冒烟证明的是旧二进制的功能，不能替代将来正常环境产物的验收。

### 7.3 executor-v4：完整保留原前置段

执行器从发布root原始Tizen宏逐条读取**完整宏体**，保留可选安装分支，不再以 `%{___build_pre}` 代替发行版前置段；只在末尾追加：

```bash
ninja() { command /usr/bin/ninja -j2 "$@"; }; export CMAKE_BUILD_PARALLEL_LEVEL=2
```

为避免GBS的shell传参提前处理换行、双引号或美元符号，参数将这些字符编码成RPM Lua `string.char`，在RPM展开阶段还原；没有改原宏文件。以下是准备好的**两个完整参数原文**（并非本轮执行的GBS命令）：

```bash
--define '__spec_build_pre %{lua:print(string.char(10))}%{___build_pre}%{lua:print(string.char(10))}%{set_build_flags};%{lua:print(string.char(10))}%{nil}%{lua:print(string.char(10))}ninja() { command /usr/bin/ninja -j2 %{lua:print(string.char(34))}%{lua:print(string.char(36))}@%{lua:print(string.char(34))}; }; export CMAKE_BUILD_PARALLEL_LEVEL=2%{lua:print(string.char(10))}' \
  --define '__spec_install_pre %{lua:print(string.char(10))}%{___build_pre}%{lua:print(string.char(10))}%{?_enable_binutils_strip:export STRIP_DEFAULT_PACKAGE=%{lua:print(string.char(34))}binutils%{lua:print(string.char(34))}}%{lua:print(string.char(10))}%__rm -rf %{lua:print(string.char(34))}%{lua:print(string.char(36))}RPM_BUILD_ROOT%{lua:print(string.char(34))}%{lua:print(string.char(10))}%__mkdir_p %{lua:print(string.char(34))}%{lua:print(string.char(36))}RPM_BUILD_ROOT%{lua:print(string.char(34))}%{lua:print(string.char(10))}%{nil}%{lua:print(string.char(10))}ninja() { command /usr/bin/ninja -j2 %{lua:print(string.char(34))}%{lua:print(string.char(36))}@%{lua:print(string.char(34))}; }; export CMAKE_BUILD_PARALLEL_LEVEL=2%{lua:print(string.char(10))}'
```

机器可读参数和未编码原宏体：[parameters.json](evidence/executor-v4/parameters.json)。执行器与全部命令收据：[check_executor.py](evidence/executor-v4/check_executor.py)、[commands.json](evidence/executor-v4/checks-accepted/commands.json)。未来使用前须再次核对实际root宏；本轮的shell参数往返检查不宣称已经跑过GBS传参。

### 7.4 展开与断言结果

使用发布root的RPM/加载器、相同RPM_CONFIGDIR/HOME、GBS宏和 `_build_create_debug=1`，只作宏展开与rpmspec -P。

| 断言 | 结果 | 证据 |
|---|---|---|
| 新build/install前置段 = 未加define的原展开 + 唯一追加内容 | 通过，逐字节比较 | checks-accepted/default-*-original.stdout 与 *-v4.stdout |
| 可选 `_enable_binutils_strip=1` 时仍完整保留原前置段 | 通过，逐字节比较 | checks-accepted/strip-enabled-*.stdout |
| CFLAGS/CXXFLAGS/LDFLAGS导出存在，CFLAGS含-g | 通过（含-g2和-g） | default-build-v4.stdout |
| 完整%build、%install脚本 `bash -n` | 均退出0 | build-full.sh、install-full.sh及syntax收据 |
| ninja的 `$@` 转发 | 通过：bolt/bolt_rt、install、含空格参数和空参数 | forwarding.sh、forwarding.stdout |
| 参数经shell往返后逐字节相同 | 通过 | shell-argument-roundtrip.stdout |

完整结果：[result.json](evidence/executor-v4/result.json)。完整脚本由原生RPM template、spec展开后的主体及原生postlude重建，补齐正常spec的name/version/release/buildroot/buildsubdir/docdir上下文；**仅bash -n，不执行**，其中的清理、编译和安装命令均没有运行。转发夹具用合成 `command` 函数打印实参，也没有调用ninja。

准备过程中的三次辅助断言失败已保留：首次误将rpm查询格式中的VERSION/RELEASE视作未展开宏，随后补齐独立模板展开所需docdir与小写name上下文；原输出在checks、checks-final、checks-complete，最终全部通过的是checks-accepted。前置段等价性从首轮起即通过；这些准备过程没有执行构建。RPM不支持macrobody查询的探测及过宽文件名搜索的中止也记入 [setup-notes.json](evidence/executor-v4/setup-notes.json)。

本轮归档和验证在串行nice19/ionice-c3、3G/200% scope中进行；最终断言scope memory.peak **11,018,240 B**。未修改补丁、原评审、旧证据、发行版宏文件或认证；不接板、不操作Gerrit、不改hq、不安装软件。**结论：执行器v4的展开与静态断言通过，正常环境重建尚未执行。**

## 8. v3 正常前置段构建验收

日期：2026-11-16。v1、v2补丁及旧证据保留，本轮只对指定v3验证。没有Gerrit评论/推送、hq改动、板上操作或主机软件安装。

### 8.1 入库、应用与解析

- 指定Downloads文件mv入库，前后SHA均为 **81f41716aa2fe1761d1a3f228c83ab86e6559e0f09c7c5defeac762afec5116b**；[移动收据](evidence/v3/move.json)。
- 基于 da885208aeb52f55c448ff46873d242346727522，独立工作树 temp/verify-361624-fix-v3-20261116/source git am退出0，结果 **bd6dd0d009b4c70e89d1a5730dbc30d3e6c7dce8**；[应用收据](evidence/v3/apply.json)。
- [完整v2→v3 diff](evidence/v3/v2-v3.diff)：tools spec保留发行版LDFLAGS、更新provider日志和说明、删除重复rm；llvm.spec只增加3行注释。
- 最终 **38 次** 只读解析/展开命令均0。tools x86_64/aarch64的包列表、BuildRequires、bolt Requires与v2逐字节相同；armv7l/i586仍不在ExclusiveArch。llvm.spec x86_64/armv7l的包列表及Requires/BuildRequires相同，源文件仅3行注释增加，RPM展开为3个空行。
- 同第2节的发布root、加载器、RPM_CONFIGDIR、HOME与GBS宏，_build_create_debug=1。命令、环境、退出码及原文见 [parse-final/commands.json](evidence/v3/parse-final/commands.json)，断言见 [preflight-result.json](evidence/v3/preflight-result.json)。辅助执行器准备过程见 [preparation-notes.json](evidence/v3/preparation-notes.json)。

### 8.2 执行器与资源门禁

本轮严格使用 [executor-v4已验收参数](evidence/v3/executor-parameters.json)，并再次用发布root的rpmspec --eval验证：原Tizen前置段逐字节保留，只在末尾追加ninja函数与CMAKE_BUILD_PARALLEL_LEVEL；CFLAGS/CXXFLAGS/LDFLAGS导出齐全且含-g2、-gdwarf-4。没有用基础___build_pre替换发行版前置段。

固定Base20261030.120529 / Unified20261104.125239；全新buildroot temp/verify-361624-fix-v3-20261116/root-x86_64；[GBS配置](evidence/v3/gbs.conf)、[完整计划argv](evidence/v3/planned-command.json)、[监督器](evidence/v3/run_build.py)。独立HOME/TMPDIR/cache，-j2、threads1、MemoryMax6G/MemoryHigh5G/CPUQuota200%、nice19/ionice-c3。

最初按本轮指令恢复MemAvailable≥16GiB、load1<0.6×nproc、磁盘≥50GiB、最多1800秒的门禁，未沿用旧授权。等待944.208秒后，用户在本会话新授权“本轮不用考虑限制”。据此停止**尚未启动GBS的等待监督器**，取消本次16GiB等待，保留负载/磁盘检查、-j2、6G/5G/200%与运行中停止保护。不是构建失败重试；该root在真正启动前不存在。两次监督器收据分别保留在build/（signal 15、GBS退出码null）与build-authorized/（实际构建）。

最新实际[完整argv](evidence/v3/planned-command-authorized.json)、[授权及停止等待收据](evidence/v3/gate-waiver-stop.json)、[执行器](evidence/v3/run_build_authorized.py)。每60秒采样；连续两次MemAvailable<6GiB、磁盘<20GiB或max/oom事件停止本任务，未提高6G上限或并行度。实际新root的两份RPM宏与前置解析root逐字节相同，见[actual-root-macros.json](evidence/v3/actual-root-macros.json)。

### 8.3 构建与四.1–四.9验收结果

**GBS退出0，v3补丁通过验证。** 仅构建x86_64的llvm-tools-subpkgs.spec，不是完整llvm.spec或AArch64主机构建。

| 用户项 | 结果 | 原始证据与行号 |
|---|---|---|
| 四.1 Tizen导出flags | 通过：CFLAGS/CXXFLAGS含-g2 -gdwarf-4，三者均export | build-authorized/build.log 486–491；flags/result.json |
| 四.2 CMakeCache | 通过：C/CXX与各自导出值逐字节相同；EXE/SHARED链接flags等于LDFLAGS加-Wl,--build-id=sha1 | flags/bolt-CMakeCache.txt 66、96、114、240；flags/result.json |
| 四.3 编译规则 | 通过：BOLT保留完整发行版flags及-g2，之后-O3 -DNDEBUG；bolt_rt的C/CXX缓存为空 | flags/bolt-rule.txt（原build.ninja 418起）；flags/bolt-rt-rule.txt（原52起）；flags/bolt-rt-CMakeCache.txt 43、70 |
| 四.4 provider/targets | 通过：Version-Release一致22.1.8-4.1；aarch64与x86-64均在版本表，两个grep通过 | build-authorized/build.log 550–551、773–774；verification/bolt-version.txt；flags/result.json |
| 四.5 RPM/依赖 | 通过：3个二进制包+1个源码包；bolt含两份lib64 runtime归档，依赖libllvm=22.1.8和LLVM_22.1(64bit)，无compiler-rt运行依赖 | verification/all-rpms.json；rpm-list-0/1/2.stdout、source-rpm-0.stdout；bolt-requires.stdout 2、11 |
| 四.6 调试信息 | 通过：5份.debug与对应运行文件build-id一致；有BinaryFunction.cpp编译单元；debugsource非空且含BOLT源码 | verification/result.json；llvm-bolt-dwarf.stdout 1265；rpm-list-2.stdout 138 |
| 四.7 链接与运行 | 通过：5个ELF均GNU_RELRO，逐个ldd无缺失、--version退出0 | verification/relro-*.stdout（llvm-bolt第21行）；ldd-*.stdout、version-*.stdout；commands.json |
| 四.8 两项冒烟 | 通过：两架构均relocation模式、改写退出0、objdump退出0；x86输入/输出均退出7 | verification/aarch64-bolt.stdout、x86_64-bolt.stdout第5行；commands.json、result.json；smoke-equivalence.json |
| 四.9 资源 | 构建成功；high回收事件2342，max/oom/oom_kill均0，未触发停止或重试 | build-authorized/resources.json、child-result.json、result.json、end.log |

以上相对证据路径均位于[evidence/v3](evidence/v3/summary.json)。实际执行的[flags断言](evidence/v3/verify_flags.py)与[产物/冒烟检查器](evidence/v3/verify_artifacts.py)已归档；不把检查器存在当作结果，结果由各命令真实退出码与[验收JSON](evidence/v3/verification/result.json)支持。两项冒烟源码与旧素材逐字节相同；除新root与测试目录外，编译、链接、BOLT与objdump参数相同（smoke-equivalence.json）。

实际GBS墙钟 **657.953秒**（子进程收据657.767秒）；开始约2026-11-16T17:48:39.469043+00:00，结束2026-11-16T17:59:37.421727+00:00。此前等待 **944.208秒** 单列，不计入构建墙钟。构建cgroup实读memory.peak **5,369,176,064 B（5.0004 GiB）**，每60秒采样的最低MemAvailable **12,783,538,176 B（11.9056 GiB）**；MemoryHigh=2342、max=0、oom=0、oom_kill=0、oom_group_kill=0。产物轻量检查scope峰值705,003,520 B，无max/OOM；本任务全部监督单元已结束。

### 8.4 产物清单与身份

| RPM | 字节数 | SHA-256 |
|---|---:|---|
| bolt-22.1.8-1.x86_64.rpm | 1699990 | 15f4302b1fe63c00e785ab9a706b3dfe0dd49d31c88fc08c11e3fac4bb210926 |
| bolt-debuginfo-22.1.8-1.x86_64.rpm | 43475370 | 0d40557304c512ea31f57966e0dc0ecacfcca65902e35daa7d50695f3ca62664 |
| llvm-tools-subpkgs-debugsource-22.1.8-1.x86_64.rpm | 1934530 | 24f002e9d60ab1e08f91d7aa6271248dbdc776d9db65b23306843d5666948a04 |
| llvm-tools-subpkgs-22.1.8-1.src.rpm | 340890079 | 7a61b4caec79c2dcce5c0393fa584129224832583f47c5d752299780c273bfd9 |

完整文件清单见verification/rpm-list-0.stdout（bolt）、rpm-list-1.stdout（bolt-debuginfo）、rpm-list-2.stdout（debugsource）、source-rpm-0.stdout（源码RPM）。源码RPM和二进制只留temp，不进Git。

| 运行文件 | runtime/.debug一致的build-id |
|---|---|
| llvm-bolt | d41669d23f1fae816f89f69d1b35b29dd2e3959f |
| llvm-bolt-binary-analysis | 5e7cbfbaa7b7fe21202d6ea460f800bae4215824 |
| merge-fdata | 2a3da2ef3af0caed498769e33c7410a32cbedc00 |
| llvm-bolt-heatmap | 224740f0542fb2b077b34d1e384844f75c3bb867 |
| llvm-bat-dump | 37a77096799348a071e32b003092495b43d333b8 |

llvm-bolt SHA-256：bfcf86f1a76f4b3645655a5417816eeb42866e50254b3c92014b5dc0a9abc5f8。每个运行文件与.debug的SHA均见verification/result.json。两个runtime归档为/usr/lib64/libbolt_rt_instr.a、/usr/lib64/libbolt_rt_hugify.a。

### 8.5 结论与边界

**v3 补丁通过验证。** 这次在完整Tizen前置段下实际构建并验证了BOLT源码DWARF和debugsource，闭合第7节指出的正常环境验收缺口。旧错误环境的产物与结论保留为历史，不覆盖或复用其调试身份。

AArch64只完成spec解析和x86_64工具改写AArch64 ELF冒烟，没有实际构建AArch64主机包；完整llvm.spec构建未执行。两项无profile最小程序冒烟不代表真实工作负载优化收益。

原件和大产物保存在temp/verify-361624-fix-v3-20261116/；[raw-index.json](evidence/v3/raw-index.json)记录路径、SHA、大小。原补丁/v1/v2证据未改，未删除任何既有temp目录；未操作开发板、Gerrit或hq，未安装主机软件。GBS只在本任务独立root安装依赖，自动生成的HOME/.gbs.conf位于本任务temp内；没有新增WORKDIR外项目产物。完成后停止。
