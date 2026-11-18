# K1b llvm-profgen 内核 IP 支持

第 10 个补丁已在 LLVM 本地分支 `k1b-kernel-ip` 提交，等待 PM 评审。前九项的 sandbox 提交 `c8942ae1b53099a78a97dca2b64427af6e58432b` 是补丁的直接父提交，系列基线为 `f999bd406c0a70fe8107aa992164fe6945c5d46a`。

| 交付项 | 值 |
| --- | --- |
| LLVM commit | `5a541f22082b963a368f065d6150eee0afae4e30` |
| 补丁 | [0010-llvm-profgen-Support-Linux-kernel-IP-sample-profiles.patch](patches/0010-llvm-profgen-Support-Linux-kernel-IP-sample-profiles.patch) |
| 补丁 SHA-256 | `7b8ff2bb1e5226ed375ddce065752dc040cc6a56c2d49e41f26e17c595197ec8` |
| 补丁验证 | 在以 `c8942ae1` 初始化的临时 Git 索引中，`git apply --cached --check` 与实际应用均成功，结果 tree 与 LLVM commit 一致 |
| 原始日志、命令与产物 | [证据索引](evidence/k1b-profgen-kernel-index.json)，路径相对主机 WORKDIR |

## 1. 实现与设计约束

- **选择与地址。** `--ip-samples --kernel` 选择主映像的 kallsyms DSO。合成内核 mmap 必须为 host PID −1，并以 `_text` 或 `_stext` 结尾。读取 `pgoff` 作为运行锚点，读取 `vmlinux` 符号表中的同名链接锚点，再以 `link_ip = runtime_ip − runtime_anchor + elf_anchor` 换算。对两个 ELF 地址宽度以无符号差值检查上下溢出。映射范围、锚点、文件有内容的可执行 `PT_LOAD` 和节归属都参加校验。`---p` 是 perf 合成映射允许的权限。多条 mmap 可以用不同参考符号描述同一重定位，但必须有一致范围和位移。
- **身份。** 运行映像须为小端 ELF32/EM_ARM 或 ELF64/EM_AARCH64 的 ET_EXEC/ET_DYN。内核 mmap、buildid-list 和可选 split-debug 的 GNU build-id 都使用既有身份门禁。已知冲突失败，缺失证据沿用显式的 `--allow-missing-build-id` 并标为 `unverified`。split-debug 另查 ELF class 和 machine。只有 mmap 需要参考后缀，样本与 buildid-list 也接受裸 `[kernel.kallsyms]`。
- **采样与符号。** 无 PID filter 时保留 −1 样本，显式 `--pid` 仍按样本所记 PID 筛选，可能漏掉 kworker、IRQ 等内核时间。链接 PC 直接交给既有 IP DWARF 行表、内联及 discriminator 路径，无返回地址减一。边界层先剔除 `$d`、启动/退出代码、PLT 和异常向量等特殊节。BASE 中同 VMA 的替代向量可以计为特殊节，重叠的可采样代码仍拒绝。无 CU、无可用行号沿用符号化丢弃口径。
- **报告。** 内核模式新增 `kernel_mmap` 与 `samples.kernel_ip`。后者报告 target、modules_skipped、user_samples、special_skipped、unknown_address、unknown_pid、special_section、mapping_data、no_cu 和 in_func_no_line。unknown PID 在事件选择后、PID filter 前计数，DSO 分桶在 PID filter 后。标识为 vmlinux 却落在映射或可执行段外的地址会计入 unknown_address 后失败。模块路径包括常见压缩 `.ko` 后缀，缺乏模块路径证据的特殊 DSO 名称计入 special_skipped。
- **边界与偏差。** 与 [K0 §4.2](00_feasibility.md#42-最小设计仅提案没有实现) 的主流程相符。实现沿用现有边界组件的小端限制，内核目标选择固定为 kallsyms 并拒绝 `--binary-match-regex`。只接收同次 boot 的录制，导出文本可以发现相互矛盾的 mmap，但无法区分同一映像、同一地址布局的两次开机。模块符号化、JIT/BPF、livepatch 与 guest 内核归属均在本补丁范围外。采集、导出、身份与质量字段的用法已写入 LLVM CommandGuide。

## 2. 构建与资源

从 `temp/llvm-profgen-enh/build` 的编译数据库、现有 Ninja 链接命令、生成头文件和 `libLLVM.so.22.1` 复用开发构建。Tizen sysroot 的 Clang 22.1.8 编译独立 worktree 的工具源文件，LLVM 库、编译产物与缓存的原有目录继续提供依赖。重定位后的局部 Ninja 图在任务目录生成对象和二进制。单元测试的局部链接复用现有 GTest 和 LLVM 库，去掉两个测试源均未引用且开发目录中没有归档的 LLVMTestingSupport。补丁中的 CMake 仍使用现有链接配置。

局部图的完整验证重编译 10 个工具和 2 个测试编译单元，链接两个目标，退出码 0，耗时 **19.208 秒**。cgroup 内存峰值 **928,333,824 B（885.3 MiB）**，合计 CPU 时间 37.059 秒，`memory.events` 的 high/max/oom/oom_kill 均为 0。Ninja `-j2`，scope 为 MemoryMax=6G、MemoryHigh=5G、CPUQuota=200%，进程以 nice 19、ionice idle 运行。启动前检查 gbs/rpmbuild/depanneur，检查时没有构建进程。

局部构建命令在证据目录用 `python3 setup-build.py` 生成 Ninja 图，从同目录执行以下启动方式。包装器保留命令、退出码及 cgroup 读数。

```sh
systemd-run --user --scope --unit=k1b-profgen-build-final \
  -p MemoryMax=6G -p MemoryHigh=5G -p CPUQuota=200% \
  nice -n 19 ionice -c3 python3 -u build-wrapper.py
```

初次试编暴露了 ELF/字符串 API 与局部测试链接的适配问题，已修正。最后整理单测文件头后，仅重链单测时曾遇到一次 LLD 段错误。复试原命令退出 0，七个单测重跑通过。工具二进制 SHA-256 为 `0d045a2375797ae8342c5c367792ed3c87e59d1f02cb42d64c7ff6539b13b415`。

## 3. 新增测试和用户态回归

| 验证 | 结果 |
| --- | --- |
| LLVM `tools/llvm-profgen` lit | 87 项，85 PASS，1 XFAIL（`invalid-perfscript.test`），1 UNSUPPORTED（`cs-preinline-cost.test`），0 FAIL |
| 新增 `ip-kernel.test` | 合成 ELF 上 30 组转换及失败检查，包含零/非零 slide、`_text != _stext`、多可执行 LOAD、PID −1 与显式 PID、`---p`、缺失与冲突 build-id、正确与错误 split-debug、ET_REL 模块、ARM32 高地址、Thumb/`$d`、特殊节、无 CU/行号和坏输入 |
| `LLVMProfgenTests` | 7/7，含新增 4 项地址换算测试和既有 3 项压缩测试。覆盖负位移、AArch64 高地址、ARM32 顶端及不可表示的输入或结果 |
| 第九补丁交付重放 | 32/32，旧工具和新工具共用输入、argv[0] 与输出路径。返回码、profile、quality JSON、stdout、stderr 逐字节一致，历史期望退出码全部吻合 |
| 冻结 C1 回放 | 50 个测试文件、每版每轮 636 条，两版各跑两轮。同路径下 exit/profile/stdout/stderr 无差异。直接与旧目录归档比较时，新旧工具都报告同一组 141 条诊断哈希差异，以同路径重放作为逐字节比较依据 |

### BASE 实物离线验证

使用 K1a 的未剥离 ARM32 `vmlinux`，SHA-256 `02bbef6771300aae8dfcb49ee1955a0ad8e1ebd80d47cc431d606a3163285411`，build-id `25599043a52ba8e5edf2f7bf4e9bb51aaf9d65a3`。使用该构建的 System.map 选择地址，在主机合成同身份文本，共 5 个 IP。报告身份为 `verified`，3 个普通 IP 分别落在 `handle_mm_fault`、`pipe_write`、`schedule` 的 DWARF 行，另两条启动/异常向量样本均计入 special_section。生成的 extbinary 用 `llvm-profdata show --sample` 读回。对旧 build-id `395733b9…` 仅用同形状的合成 parser 夹具测试拒绝，实际旧导出与 BASE 从未配对。BASE 的原始 ELF 与打包后 debug 文件身份记录见 [K1a](03_k1a_base_kernel_build.md#3-配置产物和二进制身份)。

## 4. 待验证

- RPi4 运行 K1a BASE 后的真实同 boot 采集、build-id 对账、样本可用率及 Clang 反馈编译。此次 BASE 验证使用合成采样，现场 profile 与优化收益尚无数据。
- RPi5 的真实 AArch64 KASLR 映射与 DWARF 端到端。目前的非零位移和多 LOAD 证据来自合成 ELF。
- 使用完整真实系统负载核对 perf 的 DSO 命名、模块排除比例和无行号占比。现场 E2E 须等 PM 评审及后续 BASE 上板授权。
