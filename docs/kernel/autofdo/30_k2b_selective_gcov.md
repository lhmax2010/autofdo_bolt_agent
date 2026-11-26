# K2b：选择性 GCOV 内核与共享模块 ABI

**K2b 按 PM 门禁停止在主机阶段。** 所选目录覆盖 K1e 合并 profile 的 91.44% C 行权重。选择性 GCOV 改变了 `module_layout` CRC，现有 58 个去除 BTF 的 K-BASE 模块均要求原 CRC。 [证据索引](evidence/30-k2b/index.json)

## 插桩范围

以 K1e 锁定的合并 profile 为输入（SHA-256 `d3e2f945ef17530a49d0bfe3bb754ae41cea1e4da7532342a05907d175a96208`）。用同版 `llvm-profdata merge --sample --text` 展开，累加函数体行记录的权重，包含内联上下文，函数总计与调用点总计不重复相加。使用 K1e 合并命令列出的 15 份符号化结果，把函数名、内联链、相对行与 FS discriminator 匹配到 profile 行，再用 K-BASE 链接 map 将 IP 归属到实际输入对象的目录。链接 map 对应的诊断重放映像与归档 K-BASE 的 GNU build-id 都是 `96766cfcbff8c33d83ca38152ad02f6a02dd44d4`。 [目录分布与输入](evidence/30-k2b/selection.json)

| Kbuild 目录 | C 行权重 | 纳入依据 |
| --- | ---: | --- |
| `kernel/sched` | 124,771 | 调度、唤醒，以及 `build_policy.c` 中实例化的 IRQ 辅助代码 |
| `kernel/locking` | 205,805 | 自旋锁与开中断路径 |
| `fs` | 19,767 | `pipe.c` 与顶层 VFS |
| `mm` | 211,834 | 缺页、高端内存映射和 shmem |
| `lib` | 37,661 | 补足热点库例程 |
| `kernel` | 33,424 | 补足进程、信号和软中断等通用路径 |
| **合计** | **633,262** | **已识别 C 行权重的 91.44%** |

分母为 692,526，包含 2 个无法唯一归属目录的权重。再把 12 个无法可靠判定来源的权重计入分母，保守覆盖率仍为 91.44%。`kernel/time`（19,054）、`arch/arm/kernel`（6,641）、`arch/arm/mm`（3,539）和 `kernel/rcu`（2,399）等目录在达到门槛后排除。Kbuild 的目录设置只作用于各目录直接编译的 C 对象，保留对象级排除和 `no_profile_instrument_function`。这里的百分比用于选目录，表示既有 profile 权重，实际生成的计数节点还取决于构建和启动。 [选取脚本](evidence/30-k2b/select-gcov.py)

本地补丁基于 K-BASE `7fffbec570692c925cbf1f58ea9b1cd1a5d78ac8`，为这 6 个目录分别设置 `GCOV_PROFILE := y`。打包片段仅用于普通 `arm-rpi4` 变体，启用 `GCOV_KERNEL` 并保持 `GCOV_PROFILE_ALL=n`。原配置已有 `DEBUG_FS=y`。 [本地补丁](evidence/30-k2b/0001-selective-kernel-gcov.patch)

## 主机 ABI 核对

在 `host-gbs.lock` 下使用 Clang 22.1.8、ARM32 Kbuild、`LLVM=1`、`-j2`，沿用 `-kbase` 和冻结的 KBUILD 身份（时间 `Wed Nov 18 14:59:26 UTC 2026`、用户 `abuild`、主机 `linhao-linux`、构建序号 `1`）。两侧 `olddefconfig` 的差异是启用 `GCOV_KERNEL` 及其自动选择的 `CONSTRUCTORS`，另外显式出现值为 `n` 的 GCOV 子项。两侧生成的 release 均为 `6.12.80-arm-rpi4-v7l-kbase`。 [配置差异](evidence/30-k2b/paired-config.diff) · [结果收据](evidence/30-k2b/result.json)

两侧先编译 `kernel/module/version.o`，为绕过主机上 `resolve_btfids` 的 libelf 构建依赖，在这一步对称关闭了 BTF。这个对象探针的基线 CRC 与归档不一致。随后恢复两侧带 BTF 的配置，重新生成 `autoconf.h`，用记录的 ARM Clang 命令重放 `-E -D__GENKSYMS__`，再执行内核自带的 `genksyms`。这一步复现了归档的 K-BASE CRC。 [重放脚本](evidence/30-k2b/replay-exact-abi.sh) · [工具与资源日志](evidence/30-k2b/host-unit.log)

| 核对项 | `module_layout` CRC |
| --- | --- |
| K-BASE 归档 `Module.symvers` | `0xc8c118b4` |
| 58 个共享模块的 `__versions` | `0xc8c118b4`（58/58） |
| 保留 BTF 配置，K-BASE 预处理重放 | `0xc8c118b4` |
| 保留 BTF 配置，选择性 GCOV 预处理重放 | **`0x2f3f1497`** |

共享模块树主机副本的 72 个常规文件与 K1f-1e 的 p6 写后读回 SHA 清单一致。58 个模块的 vermagic 均为 `6.12.80-arm-rpi4-v7l-kbase SMP mod_unload modversions ARMv7 p2v8`。release 一致仍不足以通过启用 `CONFIG_MODVERSIONS` 的加载检查。 [逐模块 CRC、vermagic 与 SHA](evidence/30-k2b/shared-module-abi.json)

在 K-BASE 源码中，`kernel/gcov/Kconfig:4–9` 让 `GCOV_KERNEL` 选择 `CONSTRUCTORS`，`include/linux/module.h:590–594` 因此给 `struct module` 增加 `ctors` 和 `num_ctors`。两份带 BTF 的 genksyms 类型记录确认了这两项。导出的 `module_layout` 把 `struct module` 纳入 CRC（`kernel/module/version.c:94–101`），模块加载器在校验 vermagic 之前检查该 CRC，失败即返回 `-ENOEXEC`（`kernel/module/main.c:2845–2849`）。 [基线类型](evidence/30-k2b/exact/base-struct-module.types) · [GCOV 类型](evidence/30-k2b/exact/gcov-struct-module.types)

本地补丁提交为 `f50a1b01b6c64188c6e2311fdcfbff6526f17f7d`。对象核对后将本地提交作者设为 K-BASE 使用的项目身份，源码树 SHA 保持一致。预检首次负载超过 S0 门槛，等 10 分钟后复查通过。两次主机单元累计 CPU 时间 37.938 秒，首次预检记录峰值内存 2.6 GiB、swap 峰值 0 B，主机工作目录占用约 1.75 GB。 [本地补丁身份](evidence/30-k2b/result.json) · [S0 收据](evidence/30-k2b/startup.log)

## 容量、板上阶段与数据状态

K1f-3 最终归档的 boot_a 空闲为 1,374,208 B。按 2,048 B FAT 簇计算，移除实验用 `zImage-kafdo` 后，预留 512 KiB 安全余量和一簇原子配置替换空间，得到 K-GCOV 映像容量上限 **15,880,192 B**。这使用历史读回记录，实际 gzip 或 XZ 映像大小尚无数据。压缩设置不会消除已证实的模块 CRC 冲突。 [容量计算](evidence/30-k2b/capacity.json) · [K1f-3 最终记录](28_k1f_3_formal_compare.md)

| 环节 | 本轮状态 |
| --- | --- |
| 完整 GBS、链接和容量门禁 | 在模块 ABI 门禁处停止，未生成 `vmlinux` 或 `zImage` |
| tryboot、首启验收和恢复 PLAT | 未接触 RPi4，未改动 boot_a、p6 或系统状态 |
| 3 会话、15 段训练与 `.gcda` 导出 | 0 段 |
| GCOV profile 质量、对 IP 与 R1 的 Spearman 和前 30 重合度 | 无 GCOV 实测计数 |
| `K-AFDO-GCOV` 与 `K-AFDO-HYB` | 未生成 |

按当前共享模块约束停止。重新进入构建与启动阶段需要先解决 K-GCOV 与既有模块的 ABI 兼容问题，或由 PM 批准为训练内核使用独立的配套模块树。
