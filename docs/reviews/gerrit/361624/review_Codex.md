# Gerrit 361624 — Codex 协同确认评审

结论：**需要修改**。第 2 版的 workflow 架构定位及四项事实修正基本正确，但不能原样发出 §7 的建议补丁：

1. 无条件指定 `BOLT_TARGETS_TO_BUILD="X86;AArch64"` 会使保留的 aarch64 构建失败，须按构建架构分支。
2. 独立 tools spec 的 `%{release}` 不是 libllvm 提供包的 Release；建议的 exact Requires 可能锁错包，须单独锁定提供包 EVR。
3. `Recommends` 在所核对的 Tizen RPM 中支持，但不能承诺“构建根不拉 Python、安装系统一定拉 Python”；analyzer 拆包建议须同时处理解释器和配套文件。
4. 删除“任意 libllvm 变化都必须重建 perf”的无条件要求；收窄 build-id、armv7l 镜像影响等过度表述。

前两项属于建议补丁的严重问题。其余是发给 HQ 前应修正的事实或方案边界。不是要求阻塞现有 AutoFDO workflow，也没有重新评审 llvm-profgen 默认值。

## 1. 基线、实际核对与未核实部分

- 2026-11-16，main 执行 `git pull --ff-only origin main`，返回 `Already up to date.`；HEAD `fbe094fa5d0a482e7c89e08d03b8d5dbdaea60bd`。
- 已完整阅读本目录 `own.diff`、`llvm.spec`、`llvm-tools-subpkgs.spec`、`facts_check.md` 和第 2 版 `autofdo-bolt-agent-review.md`（下称 R）。R 当前 SHA-256：`bec98591b08534dc0521ef585ab1dac64fbfe2bcdd238ef372d09a583bc159b9`。`manifest.json` 中评审原稿的旧 SHA 不作为第 2 版身份。
- 两份完整 spec 逐字节等于独立 bare 仓库 `temp/gerrit-361624-ssh` 中提交 `da885208aeb52f55c448ff46873d242346727522` 的对应文件；父提交为 `61ef5d31ca91025c414c748477bef0c64ddfa67c`。下文 LLVM/BOLT/Clang/LLD 源码行号均指 **da885208**，不混用工作树的其他 LLVM 提交。
- 读取 workflow v0.3 的主机/板端职责、工具身份、打包和 BOLT 路径；复核 `evidence/package-summary.json`、包依赖与宏记录、buildconf 摘录、`bolt-cmake.txt`、RPM/GBS 调试包宏及已有 spec 解析记录。另只读现有构建根中的 LLVMConfig、RPM 宏和 Python/scan-view 文件。
- 直接读取目标提交的 BOLT CMake、driver、runtime、X86 standalone 改动，LLVMConfig 模板，scan-build/scan-view CMake 与 shebang，Clang build-id 驱动代码及 LLD 参数定义。
- 使用既有 x86_64 Tizen root 的加载器、库、`rpmspec` 和宏，对内存中的候选 spec 做 **查询/宏展开**；没有执行 `%prep/%build/%install/%check`。使用该 root 的 CMake 只运行 `set/message` 脚本核对变量行为，没有 configure、编译或安装。候选文本通过匿名内存文件传入，没有修改原 spec 或构建根。
- 未构建 361624，未查询板子或操作 Gerrit；未验证最终 RPM、链接符号、debuginfo/build-id 配对、真实 BOLT 重写或性能。本次没有重新做九个 profgen 补丁对“当前远端 tip”的适用性检查；此说法 **未核实**，应引用固定提交的既有 apply-check 记录或改为待验证。
- 本地 RPM/GBS 能力与远端 OBS 策略分开：RPM 标签解析和本机 build 工具已核对，HQ OBS 的包启用矩阵、发布计数策略、镜像弱依赖策略 **未核实**。

## 2. R 第 1–6 节逐条结论

### R §1：工具、运行架构与包归属

**同意**工具分工：profgen/profdata/BOLT 在 x86_64 主机运行，板子运行负载与 perf；RPi4 不需要 BOLT，RPi5 的优化目标是 AArch64。主机 ISA 不等于所处理 ELF 的 ISA。

- **同意** profgen、profdata、readelf/objdump/dwarfdump/objcopy 仍属于主 `llvm` 包：完整 `llvm.spec:529–539,575` 等文件清单和 own.diff 均支持，没有本补丁将 profgen 移出主包的变化。
- **同意** x86_64 standalone BOLT 默认已有 AArch64：`llvm.spec:282–294` 与 `bolt/CMakeLists.txt:69–90` 确定默认是支持目标与安装 LLVM 目标的交集。这是源码结论，不是新二进制验收；显式目标和 smoke check 是防回归措施。
- **同意** compiler-rt profile archive 的目标架构要求；本补丁未变更其文件列表（`llvm.spec:681–685`）。本轮未核实新的 armv7l/aarch64 最终 archive，保持“请确认”正确。
- **同意** aarch64 instrumentation runtime 须与目标 ISA 匹配，不能拿 x86_64 archive 用于 AArch64；`bolt/runtime/CMakeLists.txt:15–24,44–68` 和 `bolt/CMakeLists.txt:149–184` 支持。表中“Present”应写为“spec 计划打包，最终产物待验收”；它是可选插桩路径，不是 M4 的 basic-sample 路径前提。
- **同意** kernel 不给当前 workflow 新增打包要求，不在本轮扩展。

### R §2：llvm-profgen 留在主包

**同意**保留主包和通过 `--help`/SHA 防止误用未增强版本的建议；不要求 HQ 为此次 BOLT 拆包同时迁移 profgen。当前补丁没有增强 profgen。

“独立构建可在几分钟内完成”“九个补丁适用于 current tip”不应作为已验证事实。本轮没有 standalone-profgen 构建或新的 apply-check；改为可行性/工时估计和待验证即可。已有约 80 分钟发布记录不能证明 361624 的实际构建时间。

### R §3：armv7l BOLT 与 armv7l 后端扩展

**同意**“本 workflow 无需 armv7l BOLT，可删除 armv7l BOLT 与对应后端扩展，若 HQ 有其他消费者则说明”的结论。

`bolt/CMakeLists.txt:71` 的支持目标为 AArch64/X86/RISCV，没有 ARM；因此不能重写 RPi4 的 Thumb/A32 ELF。与“32 位主机能否构建/运行一个处理其他 ISA 的 BOLT”是两件事，后者本轮 **未核实**，不宜把未测写成一定不能构建。

`llvm.spec:286–290` 确实将 armv7l LLVM 从 ARM/BPF 扩展到 ARM/AArch64/X86/BPF，会增加需构建和打包的后端代码；实际体积、时间增量未实测。将 “on every armv7l image” 改成 **“安装/更新该 libllvm 的 armv7l 镜像及工具运行树”**。workflow 私有目录中的已锁定 perf/libLLVM 不会因仓库提交自动改变；更新时按身份清单重新验收。

### R §4：包依赖（五项）

| 项 | 判断 | 理由与需修正点 |
|---|---|---|
| 4.1 libllvm 固定 | **不同意当前写法；同意固定提供包的目标** | tools 与 LLVM 是两个独立源包，`%{version}-%{release}` 展开为 tools 自己的 EVR。`llvm-config --version` 也看不到 RPM Release。见严重 S2。 |
| 4.2 perf | **不同意“任何 libllvm 变化必须重建 perf”** | `DT_NEEDED` 同名库不推出“任何实现变化都 ABI 不兼容”。应检查实际运行依赖、SONAME/符号版本/所用 API 及兼容性；有 ABI 变化或验收失败才要求匹配重建/更新。见 I3。保持 PMU 与 perf 可用的要求本身同意。 |
| 4.3 bolt_rt | **同意，附产物未验证限定** | 主机工具支持 AArch64 不会自动生成 AArch64 runtime。显式路径可用，`bolt/lib/RuntimeLibs/RuntimeLibrary.cpp:68–72` 首先接受存在的给定路径。当前 basic-sample workflow 不需要因此新增板上安装步骤。 |
| 4.4 debuginfo/build-id | **同意** | GBS 注入时点、`__debug_install_post` 钩子和晚定义 nil 的区别已正确吸收 facts_check。解析有调试包名不等于最终有 debug 文件/正确 ID。`llvm.spec:271–279` 的 build-id flag 还受 `_toolchain` 分支限制，不能声称所有配置均无条件启用。 |
| 4.5 默认 build-id | **同意 follow-up 方向；不同意“every Tizen package”** | `clang/lib/Driver/ToolChains/Linux.cpp:326–328` 只给相应 Clang ELF 链接路径添加 `--build-id`；不改变 GCC、直接调用 linker 或显式覆盖该选项的构建。不能自动取消 workflow 的身份门禁。该 Tizen 提交 `lld/ELF/Options.td:58–60` 将裸 `--build-id` 别名设为 **sha1**，本轮不将“必然生成非 SHA-1”作为问题。 |

### R §5：六项请求与小项

| 项 | 判断 | 说明 |
|---|---|---|
| 5.1 删除 armv7l BOLT/扩展 | **同意** | 限定为本 workflow 无消费者；是否保留其他消费者由 HQ 决定。 |
| 5.2 显式 BOLT 目标 | **同意防回归目标；不同意 §7 的全架构实现** | x86_64 设 X86/AArch64，aarch64 只能要求现有 LLVM 提供的 AArch64。见 S1。 |
| 5.3 版本固定 | **不同意当前具体写法** | 改为单独的提供包 EVR/ABI 约束，见 S2。 |
| 5.4 Python 扩散 | **同意影响事实；不同意弱依赖的保证性结论** | 已查 108 包 armv7l root 无 Python；Support 的 clang/llvm-devel 经依赖引入 llvm。升级后新增强 Requires 会改变该 root。x86_64 LLVM 自身 root 已有 Python，不能推广为所有 root 首次增加。`Recommends` 能解析，但不是运行时完整性或安装策略保证，见 I1/I2。 |
| 5.5 libdir 后缀 | **同意** | armv7l `_lib=lib`、LLVMConfig 在 `/usr/lib/cmake/llvm`，硬编码 64 不合适。按宏派生后缀语法可解析；不把它直接等同于 find_package 搜索路径。见 §4.3。 |
| 5.6 拆分 change | **同意作为可维护性建议** | own.diff 包含 CMake/目标 helper、打包/升级、build-id、MLGO 增量处理与 DESTDIR 多类修改；不是当前 AutoFDO 的运行阻塞。拆分时须保持 standalone helper、dylib 链接修改与打包的依赖顺序。 |

小项：**同意**补充 basic-sample 描述和修正 `llvm-static-devel`“未安装”注释。**同意**没有依据让 BOLT driver 的运行包强依赖整个 compiler-rt；是否还存在自动生成的运行依赖以最终 RPM 为准，BuildRequires 与 runtime Requires 不要混删。

“AutoFDO/PGO 不以合入 361624 为前提”正确；不能把它解释为“更新到 361624 后 build root 和工具字节不变”。既有 workflow 的构建锁仍须生效。

### R §6：九项汇总请求

| 请求 | 判断 |
|---|---|
| 1 armv7l BOLT/目标 | **同意**，保留其他消费者说明选项。 |
| 2 x86_64 AArch64 防回归 | **同意**，按 S1 改写后发出。 |
| 3 exact Requires/BuildRequires | **不同意当前 `%{release}` 写法**，按 S2 替换。 |
| 4 Python | **不同意把 Recommends 当作确定解法**；可要求 analyzer 完整拆包或验证弱依赖政策，见 I1/I2。 |
| 5 libdir | **同意**。 |
| 6 拆分/build-id | **同意**作为组织修改的建议。 |
| 7 最终 debug/ID 证据 | **同意**，本轮未替代真实构建验收。 |
| 8 AArch64 runtime | **同意**作为可选插桩文档，不增加本 workflow basic-sample 的前提。 |
| 9 Clang 默认 ID/profgen 合入 | **同意 follow-up**，限定默认 ID 适用路径；合入范围/适用性绑定固定提交。 |

## 3. 必须修改的技术问题与遗漏

### S1（严重）— 建议补丁会使 aarch64 的 configure 必然拒绝 X86

**位置：**R §7.1:151,165–166；§5.2、§6.2。

`llvm.spec:291–294` 的 aarch64 构建只提供 `AArch64;BPF`；`bolt/CMakeLists.txt:86–88` 对显式要求但 LLVM 不提供的目标执行 FATAL_ERROR。`ExclusiveArch: x86_64 aarch64` 又保留了 aarch64 构建，因此该组合并非可直接采用的修复。即便放过 configure，无条件 grep x86-64 也会错误拒绝正常 AArch64-only 包。

**改法：**x86_64 指定 `X86;AArch64`，aarch64 指定 `AArch64`；`%check` 同步分支，具体片段见 §4.1。不为满足错误检查而再扩展 aarch64 LLVM 的 X86 后端。

**验收：**两架构分别解析 spec、configure 并核对版本输出；缺失所需 AArch64 的 x86_64 LLVM 必须失败；正常 AArch64-only 包必须通过。此次仅完成宏解析和源码分支核对，未 configure/build。

### S2（严重）— 独立包 Release 被误用为 libLLVM 的 Release

**位置：**R §4.1:68、§6.3:108、§7.1:132–146,176。

两份源 spec 都写 `Release: 1` 不意味着独立 OBS/GBS 构建的最终 Release 相等。现存证据明确有 `libllvm/llvm 22.1.8-4.1`，而直接解析建议的 standalone spec 得到 **`Requires: libllvm = 22.1.8-1`**。该 spec 的 `BuildRequires: libllvm = 22.1.8` 仍允许拿 4.1 编译，却生成依赖 1 的运行包。

依据：`evidence/package-summary.json`、`x86_64-packages.json`；本机 `/usr/lib/build/build-recipe-spec:42–54` 可将外部 Release 传给 spec 替换步骤。不能把主 spec 内同源子包间的 exact pin 模式照搬到独立源包。`llvm-config --version` 只检查 22.1.8，无法查出上述错误，更不能证明头文件、生成表和动态库来自同一构建。

**改法：**另设 HQ 维护、对调度器和 rpmbuild 都可见的 `llvm_provider_evr`，同时约束 BuildRequires 和 Requires；将提供包 source revision/目标集合写入构建记录。可检查 `llvm-devel`、`llvm-static-devel`、libllvm、LLVM 工具来自同一提供者构建，相关 libomp 导出目标也须匹配。具体写法见 §4.2。

**验收：**故意让 tools Release 与 provider Release 不同；输出 RPM 必须仍依赖实际 provider。负例包括同 Version 不同 Release、混合 headers/static archives/dylib、错误 llvm-tblgen。精确 EVR 不能替代包内容 SHA 和来源记录，也不能保证未来被覆盖的同 EVR 字节仍相同。

### I1（重要）— Recommends 支持已确认，但“两边安装行为”不是标签保证

**位置：**R §5.4、§6.4、§7.2:193–200。

本次使用既有 Tizen **RPM 4.14.1.1** 的 rpmspec 与 GBS 宏，添加 `Recommends: python3` 后查询退出 0，`RECOMMENDNAME` 含 python3：语法支持没有问题。弱依赖只是给上层包管理器的提示，不能据此断言所有构建求解器都忽略它、所有安装系统都采用它；[RPM 官方依赖文档](https://rpm-software-management.github.io/rpm/manual/dependencies.html)也明确其不由 RPM 强制满足。实际最终 Requires 还可能受自动依赖、其他包或项目配置影响。

本机 `/usr/lib/build/Build.pm:975–985,993–1000` 读取推荐关系并用于依赖选择；这也不足以代表 HQ 远端配置。本轮未运行新仓库的依赖求解事务。把 R 中的保证改为：

```diff
- make the dependency weak, so build roots do not pull python3 while installed systems still get it
+ Recommends is supported by the checked Tizen RPM. Use it only if HQ
+ intentionally allows analyzer tools to be unavailable without Python,
+ and verifies the build-root and image solver policies and final RPM
+ dependencies. It does not guarantee either installation outcome.
```

优先完整拆 analyzer 子包；如果暂不拆、却要保证这些随包工具可用，保留真实的强运行依赖比“弱化后承诺功能完整”更准确。Python 导致 root 改变是需纳入构建锁的成本，不是已经证明 AutoFDO 会失效。

### I2（重要，遗漏）— analyzer 方案还缺解释器和资源归属闭环

**位置：**R §4/§5 的 Python 原因、§7.2 的 analyzer 替代方案；完整 `llvm.spec:454–455,555–557,592,631–636`。

1. 目标提交 `clang/tools/scan-build/bin/scan-build:1` 是 **Perl** shebang，不是 Python；`scan-view:1` 是 `/usr/bin/env python`，不是 python3。既有 x86_64 root 安装了 python3/python3-base，但 `/usr/bin` 只见 python3/python3.14，没有 python。新增 `Requires: python3` 本身不能保证该入口可执行。现存 root 的 scan-view 同样是该 shebang。这是既有打包缺口，本轮不要称成新提交首次引入。
2. scan-view 的 Python 模块、scan-build 的共享资源目前落入 `llvm-devel` 的 `%{_prefix}/share/*`，与入口/clang libexec 分属不同子包。`llvm.spec` 还删除 `/usr/lib/libscanbuild/*`，而拥有 analyze-build/scan-build-py 等入口；`clang/tools/scan-build-py/CMakeLists.txt:82–95` 确实把模块安装到 `lib/libscanbuild`。恢复一个 analyzer 子包不能漏掉它们的模块。
3. “因 CMake exports，脚本必须留在 clang”未获源码支持。`clang/tools/scan-build/CMakeLists.txt:39–65,77–96`、`scan-view/CMakeLists.txt:12–47` 是 PROGRAMS/FILES 安装和 custom target，不是这些脚本的 LLVM imported executable 导出。profgen 等真正导出的可执行目标不能与此混为一谈。

**改法：**将 §7.2 的 cleaner 方案写成同一 LLVM 源构建下的 analyzer 子包，拥有其全部入口、libexec、Python modules、share/man；从原包的宽泛文件列表中排除同一文件；保持 `Requires: clang = %{version}-%{release}`（此处同源子包 exact pin 合理）、正确的 Python/Perl 依赖，并明确 Python 入口改成 python3。不要为解决循环依赖随意删除需要的资源：analyzer→clang→llvm 可成立，不需要 llvm→analyzer。

验收应在仅安装 analyzer 及其依赖、没有 llvm-devel 的最小环境检查入口和模块；核对 LLVMConfig 中没有指向缺失脚本的 import。新最终 RPM、自动 shebang 改写是否已由其他钩子完成 **未核实**；不能把读取旧 root 等同于新 RPM 实测。

### I3（重要）— perf 兼容性检查不能写成任意库变化必重建

**位置：**R §4.2:72。

`perf` 动态加载 libLLVM 说明必须检查运行依赖和兼容性，不说明增加后端、改注释、改 build-id 或保持 ABI 的修复都必然要求重新编译 perf。另一方面，相同 SONAME 也不能单独保证兼容。

```diff
- any libllvm change must rebuild perf in the same release
+ For a libllvm update, verify perf's actual package dependencies,
+ required symbols/versions and runtime compatibility. Rebuild/update
+ perf together when the used ABI or dependency constraints require it;
+ otherwise retain the verified compatible pair. Record both artifact
+ SHAs and repeat the workflow's perf/cycles preflight after an update.
```

这保留 HQ 发布一致性的责任，也符合 workflow 私有目录锁定工具、不自动更新板上系统库的做法。本轮未实测新 perf/libLLVM 组合，不能宣布兼容或不兼容。

## 4. §7 建议补丁的更好写法及可构建边界

### 4.1 架构与 smoke check

以下可用于 standalone spec；保留 x86_64/aarch64 两架构的前提是 HQ 同意这个包的支持矩阵：

```spec
ExclusiveArch: x86_64 aarch64

%ifarch x86_64
%global bolt_targets X86;AArch64
%else
%global bolt_targets AArch64
%endif

# Inside the existing cmake command:
    -DLLVM_LIBDIR_SUFFIX=%(echo %{_lib} | sed 's/^lib//') \
    -DBOLT_TARGETS_TO_BUILD="%{bolt_targets}" \
```

在 `%install` 结束后、`%files` 前放独立 `%check`：

```spec
%check
set -eu
LC_ALL=C ./bolt-build/bin/llvm-bolt --version > bolt-build/version.txt 2>&1 || {
    cat bolt-build/version.txt
    exit 1
}
cat bolt-build/version.txt
grep -Eq '^[[:space:]]*aarch64[[:space:]]+-' bolt-build/version.txt
%ifarch x86_64
grep -Eq '^[[:space:]]*x86-64[[:space:]]+-' bolt-build/version.txt
%endif
```

`bolt/tools/driver/llvm-bolt.cpp:161–168,185–194` 先初始化编译进来的 BOLT 目标，并为 `--version` 注册目标打印器；无需输入 ELF，检查方式成立。先检查进程退出码再 grep，避免管道只反映 grep 成功。这只验收工具可启动与目标注册，不证明 AArch64 重写正确。普通 GBS 的目标架构 root 中工具可经其既有执行机制运行；纯交叉构建、没有目标执行机制的环境仍需另安排 smoke check，不能用构建主机 ISA 推断。

**已做的只读核对：**候选 spec 在 x86_64/aarch64 两个宏分支解析退出 0，分别展开为 `X86;AArch64` / `AArch64`，后者不含 x86-64 grep。没有运行这些 `%check` 命令。

**ExclusiveArch 的边界：**标签语法正确，本机 `/usr/lib/build/Build/Rpm.pm:483–488,606–607` 会收集其限制；OBS 的作用是限制该源包的构建架构，不是限制 x86_64 BOLT 能处理的目标 ELF。它还会排除 riscv64/i686 等，并非只删除 armv7l。若 HQ 仍需其他架构，改为相应矩阵/ExcludeArch 并逐架构维护目标和 runtime 规则。不能以 `rpmspec -q --target armv7l` 仍可查询就认为调度器会构建；本次查询模式确实未拒绝这个目标。远端包启用、旧 armv7l bolt 包清理和消费者迁移尚需 HQ 确认。此限制只写 standalone spec，不写入主 llvm.spec。

### 4.2 LLVM 提供包的版本约束

不要将 tools 自身 Release 用于另一个独立源包。下面是可解析的示例，**4.1 仅取自已有归档，用来展示 Release 不同的正确语义，不是给 361624 指定未经验证的 ABI 基线**。合入时必须填 HQ 选定、实际支持该 standalone 源码的 provider EVR，并让 OBS 依赖解析与构建同时看到同一值：

```spec
%global llvm_provider_evr 22.1.8-4.1

BuildRequires: llvm = %{llvm_provider_evr}
BuildRequires: llvm-devel = %{llvm_provider_evr}
BuildRequires: llvm-static-devel = %{llvm_provider_evr}
BuildRequires: libllvm = %{llvm_provider_evr}
BuildRequires: libomp = %{llvm_provider_evr}

%package -n bolt
Summary: BOLT post-link binary optimizer
License: NCSA
Requires: libllvm = %{llvm_provider_evr}
```

BuildRequires 中原有编译器、compiler-rt、zlib/libxml2 等不要因这个片段遗漏而误删。可将 provider EVR/源码版本绑定由项目配置维护；如引入 Epoch，同步纳入 EVR。不能在宿主预解析 spec 时执行 `rpm -q libllvm` 并把宿主库当目标 provider。

`%build` 中保留版本检查，并检查已安装提供包的实际 EVR；spec 内 RPM queryformat 的百分号需转义：

```spec
test "$(llvm-config --version)" = "%{version}" || exit 1
for p in llvm llvm-devel llvm-static-devel libllvm libomp; do
    actual_evr=$(rpm -q --qf '%%{VERSION}-%%{RELEASE}' "$p") || exit 1
    test "$actual_evr" = "%{llvm_provider_evr}" || exit 1
done
```

候选 exact dependencies 和两架构条件经 Tizen rpmspec 展开成功。最终可链接性仍须 HQ 实际构建；仅 `llvm-config --version` 匹配不能承诺“enough to stop a mismatched build”。若 HQ 不愿维护 exact EVR，应设计明确的 provider ABI capability/兼容发布政策，而不是声称两个源包 Release 自动同步。

### 4.3 libdir 与弱依赖的语法确认

- 原建议的 `%(echo %{_lib} | sed 's/^lib//')` 语法可用。以已知宏值解析，lib64→64、lib→空串，分别得到 `-DLLVM_LIBDIR_SUFFIX=64` / `-DLLVM_LIBDIR_SUFFIX=`。不使用 Tizen armv7l 不成立的固定 `/usr/lib64` 注释。
- 不能指望 `find_package(LLVM)` 总会覆盖错误的 cache：目标提交 `llvm/cmake/modules/LLVMConfig.cmake.in:117` 的空后缀展开为 `set(LLVM_LIBDIR_SUFFIX )`，已有 armv7l LLVMConfig:239 也是此形式。CMake 只读变量脚本验证，在 cache 为 64 时该语句后仍取 64。`bolt/CMakeLists.txt:53` 等继续使用后缀，路径问题确有依据；是否在某安装/清理分支形成未打包文件仍未实际构建验证。
- `Recommends: python3` 解析正确，但应采用 I1 的限定表述；analyzer 完整拆包优于以弱依赖掩盖入口不可用。
- 删除 `Requires: compiler-rt` 只针对 bolt **运行包**；不等于删除编译所需 BuildRequires。最终 NEEDED/自动依赖和 runtime archive 的符号依赖要在构建产物检查中确认。

## 5. 发出前还应补充的 HQ 验收边界

1. **不是仅打包重排。** own.diff 改了多个 BOLT 库/工具的 `DISABLE_LLVM_LINK_LLVM_DYLIB`，还新增 X86 mnemonic/register/address-size helper 副本。`bolt/lib/Target/X86/CMakeLists.txt:8–17,24–44` 同时从源树 TD 生成表并调用安装的 llvm-tblgen，强化了同源 provider 约束。应让 HQ 提供 standalone+dylib 与原集成构建的 smoke/regression 证据；X86 helper 的同步和 AArch64 ELF/pre-aggregated `S` 路径都应覆盖。这里只标验证缺口，不在未构建情况下断言 helper 错误。
2. **移包/Obsoletes 的迁移须核对。** 本提交相对父提交并没有实际移走 profgen 等文件，主要是 standalone 新包和 Obsoletes 补充。若那些中间版本子包从未发布，说明即可；若已发布，则测试旧 EVR 升级、文件归属及旧包名的反向依赖。`Obsoletes` 不自动等于 `Provides`，也不保证独立包的旧 Release 一定低于新主包 Release；不要在缺少迁移事实时机械加入不真实的 Provides。
3. **耗时、32 位 host、最终调试包仍是未验证。** “几分钟”“armv7l 一定可/不可构建”“最终 debug 文件存在”不能由 spec 解析推导。保留 R 的实构建证据请求，但不要扩大成需要板上部署 BOLT或改现有私有工具运行树。

最终结论：**需要修改**。修正 S1、S2 的候选补丁，以及 I1–I3 和上述事实限定后，评审可以作为 workflow 消费者意见发给 HQ；本轮没有完成 361624 的构建认证。只新增本文件，未构建、未评论 Gerrit、未提交、未推送。
