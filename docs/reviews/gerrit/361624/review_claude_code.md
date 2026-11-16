# Gerrit 361624 评审稿的协同评审（Claude Code）

- 被评审对象：`autofdo-bolt-agent-review.md`（第 2 版），针对 change 361624 patch set 1，commit `da885208aeb5`，父提交 `61ef5d31`。
- 读过的材料：`own.diff`、完整的 `llvm.spec` 与 `llvm-tools-subpkgs.spec`、`facts_check.md` 及 `evidence/`。另外只读查询了 `temp/gerrit-361624-ssh/` 中 `da885208` 和 `61ef5d31` 的源码，以及 `docs/profgen/delivery/01_release.md`。
- 只读：没有构建，没有在 Gerrit 评论，没有提交或推送。下文凡写"预计"的，都是由源码或 spec 推出、没有构建验证的结论。

## 结论：需要修改（3 项）

评审稿的方向是对的，第 1–6 节的大部分结论成立。但有 3 处必须先改，否则 HQ 照着做会出错，或者会指出评审稿的事实错误：

1. **第 7.1 节建议的版本固定写法在另一个 spec 里不成立（R1）。** `bolt` 写 `Requires: libllvm = %{version}-%{release}` 后，`%{release}` 取的是 `llvm-tools-subpkgs` 自己的 release，不是 `llvm` 的。结果是 `bolt` 装不上，或者只是碰巧装得上。
2. **第 7.1 节在所有架构上无条件设置 `-DBOLT_TARGETS_TO_BUILD="X86;AArch64"`，aarch64 会在 configure 阶段失败（R2）。** `%check` 中 `grep x86-64` 那一行在 aarch64 上也会失败。
3. **第 5 节第 4 项的事实前提有误，第 7.2 节的两个方案因此不是最好的修法（R3）。** scan-build 和 scan-view 在父提交里就已经在 `llvm` 包中，不是这次"移入"的。其中 scan-build 是 Perl 脚本，Python 工具因为 `libscanbuild` 被删除本来就跑不起来。更直接的改法是删掉新加的 `Requires: python3`。另外，影响范围应写成"所有架构上所有包的构建 root"，不只是 FFmpeg。

## 1. 第 1–6 节逐条核对

| 位置 | 结论 | 理由与证据 |
|---|---|---|
| §0 workflow 用法 | 同意 | 与设计 v0.3 一致：profile 处理和 BOLT 只在 x86_64 主机上做，板子只跑负载和 perf |
| §1 工具与包表 | 同意，补一处 | 补充：x86_64 的 `bolt` 用 `LLVM_LINK_LLVM_DYLIB=ON` 链接 libLLVM.so（standalone spec 第 82 行）。主机提取 BOLT 工具时，必须同时提取同一次构建的 x86_64 `libllvm` RPM，并检查 `ldd`。这是 workflow 侧的事（见第 3 节第 1 条），不是对 HQ 的要求 |
| §2 llvm-profgen 留在 `llvm` | 同意 | 父提交 `61ef5d31:packaging/llvm.spec` 第 506 行已有 `/usr/bin/llvm-profgen`，属于 `llvm` 包；361624 的 diff 没有动这一行。79 分 40 秒、9/9 干净应用到 `61ef5d31`、tip `c8942ae1` 都与 `01_release.md` 第 17、31、55、326 行一致。"several hours" 是估计，建议写成 "expected"。361624 不改 llvm-profgen 源码，补丁应该也能直接应用到 `da885208`（未验证） |
| §3 armv7l BOLT 与 armv7l 目标扩展 | 同意，补一条依据 | ① BOLT 不能改写 32 位 ARM 二进制。② **两项必须一起撤回**：standalone BOLT 的默认目标是 `{AArch64,X86,RISCV}` 与已安装 LLVM 目标的交集（`bolt/CMakeLists.txt` 第 71–88 行）。armv7l LLVM 若是 `ARM;BPF`，交集为空，configure 报 `FATAL_ERROR "BOLT_TARGETS_TO_BUILD is empty"`。所以这次扩展 armv7l 目标，就是为了让 armv7l BOLT 能构建。③ 补充：armv7l 包的构建 root 用的是 x86_64 的 `clang-accel`（buildconf 第 233 行），所以扩展目标不改变 armv7l 包的编译器行为。影响主要是 armv7l 的 libLLVM.so 变大（板上 perf 加载它，STATUS 记录板上部署了 perf 与 libLLVM）和 armv7l 的 LLVM 构建时间变长。库变大多少没有测量 |
| §4.1 libllvm 版本固定 | 目标同意，写法不同意 | 见 R1。另外，"partial repository update can pair BOLT with a different libLLVM" 的风险要说准：rpm 会自动生成 `libLLVM.so.22.1(LLVM_22.1)` 依赖（现有 x86_64 `llvm` 的 Requires 中就有），已经能阻止跨 22.1 的混用。精确固定防的是 22.1.x 内部 Tizen 本地补丁改动 ABI 的情况 |
| §4.2 板上 perf | 部分同意 | perf 必须保留、armv7l 库变大会传到板上，这两点同意。"any `libllvm` change must rebuild `perf` in the same release" 说得过重：只有 SONAME（`libLLVM.so.22.1`）变化时 perf 才必须重建，22.1.x 内部不需要 |
| §4.3 aarch64 的 bolt_rt | 同意 | `RuntimeLibrary.cpp` 第 30–79 行按"工具路径/../lib64"和安装的 libdir 查找运行时。所以 x86_64 主机默认找到的是 x86_64 的 archive，插桩 aarch64 二进制时必须显式传 `-runtime-instrumentation-lib` |
| §4.4 debuginfo 与 build-id | 同意 | 与 `facts_check.md` 第 4 节一致：调试包由 GBS 注入，后置的 `%{nil}` 清不掉它；`find-debuginfo.sh` 挂在 `__debug_install_post` 上，spec 注释写错了。实际产物仍未知 |
| §4.5 默认 build-id | 同意 | 影响全平台，应单独提交，评审稿已写明 |
| §5 第 1 项 | 同意 | 同 §3 |
| §5 第 2 项 | 同意定性为防回归建议；配套 diff 不同意 | 见 R2。x86_64 LLVM 目标为 `X86;ARM;AArch64;BPF`（`llvm.spec` 第 284 行），按交集规则默认已含 AArch64 |
| §5 第 3 项 | 目标同意，写法不同意 | 见 R1 |
| §5 第 4 项 | 结论方向同意，事实与范围要改 | 见 R3 |
| §5 第 5 项 | 同意 | armv7l 的 libdir 是 `/usr/lib`。补充：i586 构建的是 `i686-tizen-linux`（buildconf 第 192–193 行），同样是 32 位，`LLVM_LIBDIR_SUFFIX=64` 在那里也错。若采用 `ExclusiveArch`，这一项对 armv7l 和 i586 都不再出现 |
| §5 第 6 项 | 同意 | — |
| §5 小注 | 同意 | `llvm-static-devel` 的两处说法确实矛盾：spec 第 12–15 行写需要，第 67–69 行写 "not installed here" |
| §6 汇总 | 同意，随 R1–R3 同步修改 | — |

## 2. 第 7 节建议的补丁

### R1　版本固定：`%{release}` 在另一个 spec 里不是 `llvm` 的 release

- **证据。** 现有 armv7l `llvm-22.1.8-4.1` 的 Requires 是 `libllvm = 22.1.8-4.1`（`evidence/armv7l-llvm-requires.json`），但 `llvm.spec` 中写的是 `Release: 1`，最终的 `4.1` 由 OBS/GBS 按包分配。`llvm-tools-subpkgs` 是另一个源包，release 独立编号（spec 第 4 行 `Release: 1`）。所以 `bolt` 里的 `%{version}-%{release}` 会展开成 `22.1.8-<tools 的 release>`，与已发布的 `libllvm-22.1.8-4.1` 不匹配，`bolt` 装不上。§4.1 的 "as `llvm` already does" 只在同一个 spec 内成立。
- **建议写法**：在构建时取实际安装的 libllvm 的 EVR，并在 `%build` 中断言取到了：

```spec
# exact libllvm this BOLT was linked against (separate source package, own release)
%define libllvm_evr %(rpm -q --qf '%%{VERSION}-%%{RELEASE}' libllvm 2>/dev/null)
BuildRequires: libllvm = %{version}
BuildRequires: llvm = %{version}
BuildRequires: llvm-devel = %{version}
...
%package -n bolt
Requires: libllvm = %{libllvm_evr}
...
%build
case "%{libllvm_evr}" in %{version}-*) ;; *) echo "libllvm EVR not found: %{libllvm_evr}"; exit 1;; esac
```

- **副作用。** `llvm` 每次升 release，都必须重建 `llvm-tools-subpkgs`，否则 `bolt` 装不上。OBS 会因构建依赖变化自动重建；本地 GBS 需要手动按顺序构建。如果 HQ 不想要这种耦合，可退回只靠自动生成的 SONAME 依赖加 `Requires: libllvm = %{version}`（只固定版本）。评审稿应把这两种方案都列出来。

### R2　`BOLT_TARGETS_TO_BUILD` 与 `%check` 必须按架构分开

- **证据。** BOLT 的 CMake 会逐个检查用户指定的目标，不在已安装 LLVM 目标中的就报错：`FATAL_ERROR "BOLT target '${tgt}' is not in LLVM_TARGETS_TO_BUILD"`（`bolt/CMakeLists.txt` 第 86–91 行）。aarch64 的 LLVM 只有 `AArch64;BPF`（`llvm.spec` 第 293 行），所以第 7.1 节的 diff 会让 aarch64 构建在 configure 阶段失败，`%check` 的 `grep -qi x86-64` 在 aarch64 上也会失败。
- **`%check` 本身的思路是对的。** `llvm-bolt` 只初始化 `TargetConfig.def` 中的 BOLT 目标（`llvm-bolt.cpp` 第 185–193 行），`--version` 再通过 `printRegisteredTargetsForVersion` 打印出来（第 165 行）。因此 `--version` 的输出反映的是 BOLT 的目标集合，而不是 libLLVM 的全部目标。
- **建议写法**：

```spec
%ifarch x86_64
    -DBOLT_TARGETS_TO_BUILD="X86;AArch64" \
%endif
%ifarch aarch64
    -DBOLT_TARGETS_TO_BUILD="AArch64" \
%endif
...
# at the end of %%build (does not depend on %%check being run)
./bin/llvm-bolt --version | grep -q 'aarch64'
%ifarch x86_64
./bin/llvm-bolt --version | grep -q 'x86-64'
%endif
```

  把断言放在 `%build` 末尾而不是 `%check`，是因为本轮没有核实 Tizen 的 GBS/OBS 是否带 `--nocheck`。rpm 用 `sh -e` 执行各节脚本，`grep -q` 失败会让构建失败。管道没有设 `pipefail`，所以 `llvm-bolt` 收到的 SIGPIPE 不影响结果。

### R3　python3：前提有误，建议删掉而不是改成 Recommends

- **证据。**
  - 父提交 `61ef5d31:packaging/llvm.spec` 第 452 和 527–529 行，`analyze-build`、`scan-build`、`scan-build-py`、`scan-view` 已经在 `llvm` 的 `%files` 中，且 `llvm` 没有 `Requires: python3`。361624 只在这组文件不变的情况下新增了 `Requires: python3`（diff 第 76–79 行）。评审稿 §5 第 4 项写的 "(scan-build/scan-view moved into it)" 不对。§7.2 方案 2 写的 "restore a `clang-analyzer` subpackage" 也不对：父提交中没有这个子包。
  - 解释器：`scan-build`、`ccc-analyzer`、`c++-analyzer` 的 shebang 是 `#!/usr/bin/env perl`。`scan-view` 是 `#!/usr/bin/env python`，不是 `python3`。只有 `scan-build-py`、`analyze-build`、`intercept-build` 及 `libexec` 中的 `analyze-cc`、`intercept-cc` 是 python3。
  - 那些 python3 工具依赖的 `libscanbuild` 包在 `%install` 中被删掉了：父提交第 427 行、新版第 455 行都是 `rm -rf %{buildroot}/usr/lib/libscanbuild/*`。`scan-view` 的 Python 模块装在 `share/scan-view`，归 `llvm-devel` 的 `%{_prefix}/share/*`。所以加了 `Requires: python3` 也不能让这些工具在只装 `llvm` 时运行。spec 注释 "scan-build and scan-view are Python scripts" 也与事实不符。
  - 范围：buildconf 第 313 行的 `Support: clang llvm-devel` 适用于所有包，`clang` 和 `llvm-devel` 都 Require `llvm`。所以新增的依赖会把 python3 及其运行时依赖带进所有架构上、本来没有 python3 的包构建 root，不只是 FFmpeg。在 OBS 上，这还会让 python3 及其依赖成为几乎所有包的构建依赖，python3 一变就会触发大范围重建；python3 自身的构建 root 也会出现它自己。这一点按 OBS 的一般行为推出，没有在 Tizen OBS 上核实。
- **建议写法**：首选删除 `Requires: python3`，回到父提交的状态，因为它没有带来功能上的好处。如果 HQ 希望 analyzer 工具真正可用，再单独提交一个 analyzer 子包：其中要包含 `share/scan-build`、`share/scan-view`（并从 `llvm-devel` 的 `share/*` 通配中排除）和不再删除的 `libscanbuild`，并在子包上声明 `Requires: perl, python3`。
- **关于 Recommends。** 构建 root 中的 rpm 是 4.14.1.1（`evidence/armv7l-packages.json`），支持 `Recommends`。OBS/GBS 展开构建依赖时预计不安装弱依赖，但没有用 GBS 实测。它可以作为备选写进评审稿，但不应是首选。

### 其他建议逐项

| 建议 | 判断 |
|---|---|
| `ExclusiveArch: x86_64 aarch64` | 语法正确。不匹配的架构在 OBS/GBS 中标为 excluded，而不是失败（Tizen 上未实测）。评审稿要写明它的另外两个后果：① 去掉 i586。当前补丁在 i686 上预计会失败：BOLT 运行时默认只在 x86_64/aarch64/riscv64 开启（`bolt/CMakeLists.txt` 第 93–102 行），i686 上没有 `bolt_rt` 目标，`ninja bolt bolt_rt` 会报未知目标，而且后缀 64 也错。② 去掉 riscv64，而 BOLT 支持 RISCV。是否保留 riscv64 由 HQ 决定；如果保留，要加 `%ifarch riscv64` 并设 `BOLT_TARGETS_TO_BUILD="RISCV"` |
| `BuildRequires: … = %{version}` | 正确 |
| `llvm-config --version` 断言 | 正确，`llvm-config` 在 `llvm` 包中（第 501 行）。有了 `BuildRequires: llvm = %{version}` 它就是冗余的，但无害 |
| `LLVM_LIBDIR_SUFFIX=%(…)` | `%()` 写法可以，但建议与 `llvm.spec` 第 323 行用同一种写法：`` `echo %{_lib} \| sed s/lib//g` ``。采用 `ExclusiveArch` 后，两种写法结果都是 64 |
| 删除 armv7l 分支，统一 `ninja bolt bolt_rt` | 有 `ExclusiveArch` 时正确；没有时不能删 |
| 撤回 `llvm.spec` 的 armv7l 目标扩展 | 正确，但必须和去掉 armv7l BOLT 同时做（见 §1 表中 §3 行的第 ② 点） |
| 去掉 `bolt` 的 `Requires: compiler-rt` | 同意 |
| §7.3 `rpm2cpio … ./usr/lib64/libbolt_rt_instr.a` | 路径正确：aarch64 的 `%{_libdir}` 是 `/usr/lib64`，运行时装到 `lib${LLVM_LIBDIR_SUFFIX}` |

## 3. 评审稿遗漏的问题

1. **（workflow）BOLT 工具在主机上依赖 x86_64 libLLVM.so。** 我们现在从 x86_64 RPM 提取的 llvm 工具，因为 x86_64 用 `LLVM_LINK_LLVM_DYLIB=OFF`（`llvm.spec` 第 303–305 行），大多不链接 libLLVM。`bolt` 则必须链接（standalone spec 第 82 行）。M4 预检要同时提取 `bolt` 和同一次构建的 `libllvm`，通过 `LD_LIBRARY_PATH` 指向私有目录，并把两者的 SHA 都记入清单。
2. **（HQ）python3 的影响范围与 OBS 重建耦合。** 见 R3。评审稿只举了 FFmpeg root 的例子。
3. **（HQ）当前补丁在 i586 和 riscv64 上的状态没有说明。** 见第 2 节表中 `ExclusiveArch` 一行。i686 预计构建失败（未构建验证）。
4. **（HQ，次要）三条 `Obsoletes` 指向父提交中不存在的子包。** `clang-analyzer`、`llvm-xray`、`llvm-prof-tools` 在 `61ef5d31` 中都没有，`llvm-tools-subpkgs.spec` 也是这次新增的。除非这些名字曾经在某个仓库中发布过，否则这些 `Obsoletes` 是多余的，应请提交者说明来源。
5. **（workflow）合入后工具链会变。** `clang`/`llvm` 的 release、工具链二进制的 build-id，以及（如不撤回）armv7l 的 libLLVM 都会变。按设计 v0.3，已冻结的实验不受影响，新实验必须重新冻结依赖仓库。armv7l 包实际由 x86_64 的 `clang-accel` 编译，所以 armv7l 目标扩展本身预计不改变我们 FFmpeg 的编译结果，但 `rpm -qa` 锁会变。这一条不需要 HQ 做什么，只是提醒我们自己。

## 4. 修改清单（发出前）

- §4.1、§5 第 3 项、§7.1：按 R1 改写版本固定，并写明两种方案的取舍。
- §5 第 2 项、§7.1：按 R2 改为按架构设置目标，断言移到 `%build` 末尾或加架构条件。
- §5 第 4 项、§6 第 4 条、§7.2：按 R3 改正事实（文件早已在 `llvm` 中，scan-build 是 Perl，`libscanbuild` 被删除），把首选改为删除 `Requires: python3`，范围写成所有包的构建 root。
- 可选：§7.1 补充 `ExclusiveArch` 对 i586 和 riscv64 的影响；§4.2 改为"SONAME 变化时重建 perf"。
