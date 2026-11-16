# Gerrit 361624 patch set 1：事实核查

日期：2026-11-16。仅取回、读取既有构建根/日志/RPM与解析spec；**未构建361624、未接板、未在Gerrit评论或推送、未修改hq**。评审原文保持不变，本文件只提出事实修正。

## 1. 取回、身份与共享

独立bare仓库：`temp/gerrit-361624-ssh/`。命令：

```bash
git fetch ssh://lhmax2025@review.tizen.org:29418/platform/upstream/llvm refs/changes/24/361624/1
git rev-parse FETCH_HEAD
git show --stat FETCH_HEAD
git show FETCH_HEAD
git show FETCH_HEAD:packaging/llvm.spec
git show FETCH_HEAD:packaging/llvm-tools-subpkgs.spec
git rev-parse FETCH_HEAD^
```

- fetch退出0；FETCH_HEAD **da885208aeb52f55c448ff46873d242346727522**，与用户要求一致。
- 父提交 **61ef5d31ca91025c414c748477bef0c64ddfa67c**。
- [commit.txt](commit.txt)、[own.diff](own.diff)、[完整llvm.spec](llvm.spec)、[完整llvm-tools-subpkgs.spec](llvm-tools-subpkgs.spec)、[parent.txt](parent.txt)均为上述Git命令的原始输出，不修改。
- [评审原文](autofdo-bolt-agent-review.md)移动前后SHA均为 `1ab6f4311f60b6b26736286bd1707578f10eca799d804a234f9d4ab27e7fcf39`。使用mv移出指定Downloads路径，并复制到用户授权的 `/home/linhao/Toolchain/development/llvm-optimize/temp/review-361624/autofdo-bolt-agent-review.md`；复制后SHA再次一致。该外部项目仅写入这一个文件，未读取或修改其仓库配置/其他文件。
- 六份共享文件SHA见 [SHA256SUMS](SHA256SUMS)；全部证据和来源SHA见 [manifest.json](manifest.json)。
- 上一轮HTTPS错误原文保留在 [HTTPS日志](evidence/gerrit-361624-fetch.log)；本轮[SSH日志](evidence/gerrit-361624-ssh-fetch.log)与[结果](evidence/fetch-result.json)分开保存。未更改认证。

## 2. 事实一：标准包构建root中的llvm、clang、python3

**结论：所核查的两个root均含llvm与clang；FFmpeg armv7l的108包集合没有python3；LLVM x86_64的122包集合已经有python3。不能据此说“本次更新会让每一个包构建root首次增加python3”。**

| 已有root | 包总数 | llvm / clang | python3 |
|---|---:|---|---|
| FFmpeg armv7l（本次诊断root，包名版本逐行等于试跑BASE的108包） | 108 | 两者均22.1.8-4.1.armv7l | 未安装（完整包清单无python3系列） |
| LLVM发布x86_64 | 122 | 两者均22.1.8-4.1.x86_64 | python3、python3-base、python3-devel均3.14.2-1.10.x86_64 |

证据：[armv7l rpm -qa原文](evidence/armv7l-packages.json)、[x86_64原文](evidence/x86_64-packages.json)、[汇总与108包相等断言](evidence/package-summary.json)。每个JSON含实际root路径、命令、退出码。历史对照为 `docs/workflow/m1/evidence/08/build/BASE.rpm-lock.txt`，其中llvm/clang所在行80/11。

对应buildconf均为实际冻结/发布构建使用的 `tizen_unified_standard.conf`：

- [armv7l摘录](evidence/armv7l-buildconf.txt)、[x86_64摘录](evidence/x86_64-buildconf.txt)保存来源路径、SHA及原行号。两者第310行Required列binutils/glibc/rpm-build/libtool；第313行 **Support: clang llvm-devel**；第348行 **Keep: clang llvm libllvm llvm-devel**。
- Required/Preinstall/Support中均没有独立的 `llvm` 或 `python3` 包名；不能把Keep当作Support或Preinstall。第102–103行出现python3-mako等也不是这些指令。
- 但Support中的clang与llvm-devel会经依赖拉入llvm：现有armv7l RPM的Requires分别含 `llvm = 22.1.8-4.1`、`llvm = 22.1.8`。见 [clang依赖](evidence/armv7l-clang-requires.json)、[llvm-devel依赖](evidence/armv7l-llvm-devel-requires.json)。x86_64同类证据也已保存；其llvm-devel还有libpython3.14运行库依赖。
- 新完整 [llvm.spec](llvm.spec)第57–58行本就BuildRequires python3/python3-devel，第79行新加入运行时 **Requires: python3**。因此LLVM自己的x86_64构建root已有Python，并非此新运行依赖才带来。对沿用上述Support集合且原来没有Python的armv7l包构建root，升级到新llvm会引入额外的Python依赖，这是有证据的影响方向；未实测全平台全部包，不能声称所有root都同样变化。

**对评审的修正：** §5表第4项、§6/§7相关“every package build root gains python3”改为上述分架构/既有包集合的限定表述；“确认llvm不在默认root”这一备选不能用于这两套buildconf。是否拆出analyzer仍是打包政策意见，不是事实核查自动裁决。

## 3. 事实二：LLVM目标集合与跨架构工具

完整 [llvm.spec](llvm.spec)第282–294行明确设置，并非留默认：

| 构建架构 | LLVM_TARGETS_TO_BUILD |
|---|---|
| x86_64（同时覆盖i686分支） | `X86;ARM;AArch64;BPF`（第284行） |
| aarch64 | `AArch64;BPF`（第293行） |
| armv7l（补充上下文） | `ARM;AArch64;X86;BPF`（第288行） |

若未设置，LLVM 22.1.8的默认是`all`，但这里不适用：已保存**目标提交本身**的 [llvm/CMakeLists.txt](evidence/llvm-cmake.txt)，第552行默认值，第649–650行展开LLVM_ALL_TARGETS（第518行起）。

目标提交的 [bolt/CMakeLists.txt](evidence/bolt-cmake.txt)第38行在standalone模式读取安装的LLVMConfig；第71–88行将默认BOLT目标设为 `{AArch64,X86,RISCV}` 与安装LLVM目标集合的交集。因此若使用这个spec产生的x86_64 LLVM、且没有其他覆盖，BOLT默认包含AArch64与X86；aarch64 LLVM对应AArch64。这是源码推导，**不是361624的BOLT二进制实测**。

本项目发布的x86_64 llvm-profgen SHA `67ad21faba787d276a80673c1f324f7c0591d28d76bd37a8bd57de0d86426be6` 已对ARM/Thumb/AArch64素材与历史输入通过回归，见[发布报告](../../../profgen/delivery/01_release.md)及其 `evidence/03/release-tool.json`、`replay-result.json`。这证明主机运行架构与所分析ELF架构可以不同，并证明该发布profgen含所需后端能力；**不证明新standalone BOLT已构建成功、具备目标运行时或已完成AArch64优化验收**。

**对评审的修正：** §5第2项“x86_64目标未说明”需补充完整spec的上述显式集合；显式BOLT_TARGETS_TO_BUILD与smoke test可保留为防回归建议，不应描述为当前确定缺少AArch64的修复。安装LLVM版本/目标集合仍须验证。

## 4. 事实三：debug_package nil与Tizen调试包

**结论：仅看`%define debug_package %{nil}`不能判定不产debuginfo。实际生效的条件、定义位置和GBS注入均重要。旧LLVM发布构建确实产出llvm-debuginfo；361624的llvm/bolt实际RPM及build-id配对，本轮未知（按要求没有构建）。**

### 4.1 既有root的机制

- 两root的只读 `rpm --eval` 完整输出见 [armv7l](evidence/armv7l-macros.json)、[x86_64](evidence/x86_64-macros.json)。脱离构建命令时 `_build_create_debug` 为空；不应据此断言GBS未启用它。
- [旧GBS日志摘录](evidence/old-build-debug-log.txt)原第476行：`rpmbuild ... --define '_build_create_debug 1' -ba .../llvm.spec`。
- GBS生成的 `/home/abuild/.rpmmacros` 原第131–136行（[摘录](evidence/gbs-injected-macros.txt)）：在 `%package`/`%prep` 时，若未设`__debug_package`且有`_build_create_debug`，执行 `_build_insert_debug_package`，设 `__debug_package=1` 并展开debug_package。
- RPM宏原第229–235行定义debug_package；第899行由 `%{?__debug_package:%{__debug_install_post}}` 触发调试后处理，第901行才调用 `__os_install_post`。`find-debuginfo.sh`属于`__debug_install_post`（原第183行），见 [RPM宏摘录](evidence/rpm-debug-hooks.txt)。standalone spec第57–58行把它归给`__os_install_post`的注释不准确。

### 4.2 两个spec应分别理解

1. **llvm.spec：** 第11–16行，当GBS已有`_toolchain`时，`llvm_release_build=0`。第24–30行的nil定义与删debug目录只在release_build=1时生效。两套buildconf明确设`_toolchain`（原第163行）；旧发布root的实际路径属于0分支。旧spec条件原文见 [旧spec摘录](evidence/old-spec-debug-condition.txt)。旧日志第16448行运行find-debuginfo，第17283行Processing llvm-debuginfo，第17494行写出llvm-debuginfo RPM。**这些旧产物不能当作启用了nil分支后仍产包的实测证据。**
2. **llvm-tools-subpkgs.spec：** 第38行已有`%package -n bolt`，第49行为`%prep`，nil定义直到第61行才出现。因此前面的GBS宏注入已经可以建立调试包状态，后置nil不会自动清除`__debug_package`。
3. 额外只读解析（不是构建）：使用发布root的RPM二进制/动态加载器/库，显式读取同root RPM宏与GBS生成宏，并设`_build_create_debug=1`，`rpmspec -q` 两份spec均退出0。完整命令及输出见 [llvm解析](evidence/llvm.spec-parse-native.json)、[standalone解析](evidence/llvm-tools-subpkgs.spec-parse-native.json)。前者列出llvm-debuginfo/llvm-debugsource；后者列出llvm-tools-subpkgs-debuginfo/llvm-tools-subpkgs-debugsource及bolt。**解析输出没有直接证明最终bolt-debuginfo RPM存在；子包拆分与最终文件/身份仍需真实产物核验。**

初次只读解析尝试的错误也保留：root中rpmspec不支持`--load`；随后chroot内没有`/dev/stdin`，未挂载或写入root绕过。最终使用root加载器在宿主读取归档spec，显式加载其宏，成功解析。所有失败输出见同目录`*-parse.json`、`*-parse-macros.json`；未执行%prep/%build/%install。

**对评审的修正：** §4.4/§7.4的“请提供最终debuginfo及build-id配对证据”仍合理；但不能将nil本身作为缺包结论。应注明GBS宏注入、llvm条件分支和standalone的后置定义，并纠正find-debuginfo调用钩子。361624实际产物继续标为未知。

## 5. 事实四：armv7l库目录与LLVMConfig

**结论已证实：armv7l `%{_lib}=lib`，`%{_libdir}=/usr/lib`；已有armv7l llvm-devel的配置安装在 `/usr/lib/cmake/llvm/LLVMConfig.cmake`。**

- 运行已有armv7l root内 `/usr/bin/rpm --eval`，退出0，见 [原文](evidence/armv7l-macros.json)。x86_64对照为lib64、/usr/lib64。
- 对已有 `temp/m1-pilot-v02-20261116/build/repo/llvm-devel-22.1.8-4.1.armv7l.rpm` 执行 `rpm -qpl`，退出0。见 [完整命令/清单](evidence/armv7l-llvm-devel-files.json)、[LLVMConfig相关行](evidence/armv7l-llvmconfig-paths.txt)。
- 新standalone spec第80行硬编码LLVM_LIBDIR_SUFFIX=64，66行注释固定`/usr/lib64/cmake/llvm`，这与armv7l安装路径不同。第104/106行已经同时清理两种路径，不能漏看第二条清理。

**对评审的修正：** §5第5项的armv7l路径事实可以从“待确认”改为已确认；跨架构libdir审查建议有依据。但`LLVM_LIBDIR_SUFFIX`影响输出目录，不等同于强制`find_package(LLVM)`只搜索lib64；不能仅凭此断言find_package必然失败。构建是否失败、具体文件遗漏仍未知，本轮不构建。§7.4该路径问题已闭合。

## 6. 执行边界与交付

- 只更新main。受保护config/、gbs_gcc.conf、gbs_llvm.conf未读取、修改或暂存。设计、旧证据、hq及所有LLVM开发检出未修改。
- Downloads读取/mv与另一个项目的单文件复制均为本任务明确授权的WORKDIR外例外；不涉及其他文件。源文件不再留在Downloads。
- 所有命令nice19/ionice-c3，systemd scope 3G/200%；未安装软件、未挂载。首次完整Git取回经历较长磁盘等待，保留独立目录；取回中资源读数见 `evidence/fetch-resource.jsonl`（离散采样，非完整峰值监控；记录OOM=0，不能据此声称逐秒完整监控）。
- 除Git取回、本地证据文件和明确授权的复制，均为读取/查询操作。未生成或打开任何sample profile。
- 评审文件只存原文；本报告的建议不等于在Gerrit发送评论，也未替评审方改写其文件。
