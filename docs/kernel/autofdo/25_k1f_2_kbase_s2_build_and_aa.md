# K1f-2 修正版构建与跨重启 A/A 预试

**板上终态 STOP。** 第 1 个 A/A block 的首次 K-BASE 启动通过身份和安静门禁，起跑温度在冷却等待内未降到 60 °C。没有完成的 block，正式 N 未锁定。板已返回 PLAT。主机构建及门禁结果见下文。 [证据索引](evidence/25-k1f-2/index.json)

## 控制台附件与状态核对

本轮尚未收到 K-BASE-S 诊断启动的完整控制台日志附件。K1f-1d 已保存当时的用户描述原文。独立 GitHub worktree 已 rebase 到包含 `12a37f92` 的 main。板侧预检核对 PLAT 身份、p6 只读、K-BASE 共用去 BTF 模块树及 PLAT 模块树的归档 SHA，校验测量脚本、ToS 片源及 helper。只原子切换任务自有 `tryboot.txt` 的 kernel 行，boot_a 原 413 项 SHA 一致，`zImage-kafdo` 和 `zImage-kbase` 均保留。 [诊断描述](evidence/23-k1f-1d/user-console-description.txt) · [最初 PLAT 核查](evidence/25-k1f-2/initial-plat.json) · [boot_a 切换后清单](evidence/25-k1f-2/boot-a-after-aa-switch.sha256)

## A/A 预试及温度停止

保留 K1f-1 的 A/A 顺序（8 个 block），布局计划用 workflow v0.3 的 `stats.order` 与种子 `20261120` 重新生成，和既有计划中把 K-BASE-S 更名为 K-BASE-S2 的顺序一致。两个顺序及计时定义在首个 A/A 试启动前写入并锁定 SHA。最初本地校验尝试误用布局的种子重新生成 A/A 顺序。断言在预检写入及任何重启前阻止了该尝试，随后恢复上一轮已预登记顺序。 [顺序与统计方法](evidence/25-k1f-2/phase-plan.json) · [计划 SHA](evidence/25-k1f-2/phase-plan.sha256)

第 1 block 顺序 B → A，两腿均为 K-BASE。B 于 2026-11-23 23:58:08 PST 发令，首条新 boot ID 的 sdb 命令于 **60.333 s** 可用。build-id `96766cfcbff8c33d83ca38152ad02f6a02dd44d4`、`armv7l`、正式 cmdline、规范化 FDT、模块 10/10、显示、dlog 和 D-Bus 通过，`rsts=0x20`。安静门禁采到连续六个 5 秒窗口，耗时 30.37 s，忙时范围 0.650–2.272%，均低于 2.91%。门禁通过时以 KiB 记录 MemTotal / MemFree / MemAvailable / Slab / KernelStack / PageTables 为 3,976,472 / 3,382,012 / 3,453,676 / 50,892 / 3,504 / 5,232。 [启动验收](evidence/25-k1f-2/aa-first-direct.json) · [安静门禁原始值](evidence/25-k1f-2/aa-first-quiet.tsv) · [停止收据](evidence/25-k1f-2/aa-stop-receipt.json)

现有测量脚本在第一轮 pipe 预热前即检查温度。首次读数 70.114 °C，切到 `powersave` 后频率 600,000 kHz。共 61 条 10 秒间隔读数，最低 **67.679 °C**、中位 **68.653 °C**、最后 **68.166 °C**。名义上限 600 s，末次轮询与首次读数相隔 602.25 s。任务返回 `measurement=75 cleanup=0`，原 governor `schedutil` 已恢复。驱动的异常文本把非零测量退出与清理合并为一条消息，退出收据确认实际停止原因是温度超时。K-BASE 验收快照为 70.601 °C，回程 PLAT 的两个温度读数分别为 72.549 °C 和 72.062 °C。K1f-1e 的两次直启快照均为 58.426 °C。此次无预热完成、无计时窗口、无遥测标记、无配对值。没有替换该 block。 [降温逐点原始数据](evidence/25-k1f-2/aa-first-temperature.tsv) · [governor 切换](evidence/25-k1f-2/aa-first-governor-switches.tsv)

本轮 A/A 点估计、95% CI、启动内及启动间方差和每个基准的 N 均不可估计。正式比较 N 沿用预登记公式，待 8 个有效 block 后以 `max(N_pipe, N_mmfault)` 锁定且上限为 40。K-BASE-S2 板上首启与 10 个布局 block 未进入。A/A 唯一启动的 rsts 为 `0x20`，回程也是 `0x20`，无跨启动分布估计。

普通重启回 PLAT 在 64.355 s 后取得首条新 boot ID 命令。PLAT build-id `395733b9c917cb98309b39cc3ec379c03ac36b3f`，boot ID `656d98ce-abdc-47e2-9f04-deffc0979c68`、U-Boot、tryboot=0、原 cmdline、root off、UID 5001 通过。boot_a 仍有 1,374,208 B 余量，试启动目标为 K-BASE。p6 未执行写入。共享 sdb 进程为 PID 276783，重启 0 次。 [回程](evidence/25-k1f-2/plat-final.json) · [SDB 监听收据](evidence/25-k1f-2/sdb-listener.txt)

## 0009、冻结输入与主机构建

0009 仅改变 `packaging/linux-rpi.spec`。源码提交 `be12d5d7d31438be5df6b7d95d7a5193876d3c39`，tree `64c0338faffbc2bc9d3f70295c9caa183bca0535`。新增可选 `kernel_vmlinux_symbol_order`，把排序文件和 SHA 清单分别作为 Source2002 与 Source2003，在 %build 内验 SHA 后只向顶层 vmlinux 链接传参。补丁 SHA-256 `f533fe0340e3622f9d18a3a6f8184f5d675824669b8d063a648ae9e5090d3a2a`。 [0009](patches/kernel/0009-packaging-optional-vmlinux-symbol-order.patch)

三个可选宏未定义时，`rpmspec -P` 的 0008 与 0009 输出经 `cmp` 逐字节一致。armv7l SHA-256 `ba7acbb2d8946dc322b24d13725cc47aebbcddcbc74850d7b3a198aeb6b61afd`，aarch64 `0822f92d8c505193e3da4c0c58c274a0ccbb3041cf5a11e40be2be17f1f16871`。排序文件 SHA-256 `6d8e0e7c632efed15d6169d6116eeeff8baa5b4ba57ab3d89e14f8f9de021b0c`，正向及修改副本反向探针均通过。 [无作用性证明](evidence/25-k1f-2/spec-noop.sha256) · [正确文件](evidence/25-k1f-2/spec-sha-probe-positive.txt) · [损坏文件](evidence/25-k1f-2/spec-sha-probe-negative.txt)

持有 `WORKDIR/temp/host-gbs.lock` 后以 S0 门禁启动，每次都使用新 buildroot。参数为 armv7l、`-j2`、`MemoryMax=6G`、`MemoryHigh=5G`、`CPUQuota=200%`、nice 19、ionice class 3。Base snapshot `20261030.120529`，Unified snapshot `20261104.125239`，复用 K1a 冻结的 130 个 RPM。LOCALVERSION 为 `-kbase`，KBUILD 构建时间为 `Wed Nov 18 14:59:26 UTC 2026`，用户 `abuild`、主机 `linhao-linux`、版本序号 1。

首次构建在 %build 的 SHA 校验以 GBS 退出码 1 停止，墙钟 362.035 s，内存峰值 5.000 GiB。冻结 Tizen 的 `sha256sum` 拒绝 `--strict`。改为比较实际摘要行与锁定的摘要和文件路径，用冻结的工具复核后重新取得主机锁。 [首次退出收据](evidence/25-k1f-2/attempt-01-result.json)

第二次 GBS **退出 0**，墙钟 **4688.114 s**，内存峰值 **5.002 GiB**。 [GBS 与资源收据](evidence/25-k1f-2/attempt-02-result.json)

从构建日志的实际输出行和 buildroot 中的 Sources 文件分别核对锁定摘要。 原包装驱动把 shell xtrace 内的摘要副本计入唯一行断言。GBS 自身退出码为 0，独立收据按完整的真实输出行重新核对通过。 [构建内 SHA 收据](evidence/25-k1f-2/attempt-02-build-checksum-verification.json)

| 产物 | Build ID | 编译 argv | CRC 行数 / 模块 vermagic | zImage | 核对问题 |
| --- | --- | ---: | ---: | ---: | --- |
| arm-rpi4 | `04ef511ea1e0684d3afda273599755028c86c9e2` | 3,237 | 14,130 / 52 | 15,174,960 B | 无 |
| arm-rpi4-rt | `0cfe5cf907c6541fa650b8a857bc23b17656832c` | 3,214 | 14,119 / 52 | 15,229,224 B | 无 |

逐条核对编译 argv 的基准为 K1e 已验证与 K-BASE 一致的构建日志。静默构建的主机工具命令使用 K1a 保存的 .cmd 补齐，K1c 已逐条核对这些工具命令一致。现场 buildroot 的归档成员顺序、.config、Module.symvers、模块 vermagic、固定构建身份也已核对。版本字符串按 ELF 的 linux_banner 符号读取，排除了初次字符串扫描误取的临时构建串。LLD 两次中间链接和最终链接只增加排序文件参数，System.map 与最后一轮 kallsyms 输入逐字节一致。RT 模板沿用 K1e 的同一固定时间戳。 [全部结果](evidence/25-k1f-2/variant-verification.json) · [普通版 argv](evidence/25-k1f-2/arm-rpi4-compile-argv.json) · [RT 版 argv](evidence/25-k1f-2/arm-rpi4-rt-compile-argv.json)

130 个已安装 RPM 的 header SHA、缓存 RPM SHA 及冻结 clang/LLVM 关键二进制与 K-BASE 一致。 [依赖核对](evidence/25-k1f-2/dependencies.json)

arm-rpi4 的实际末次链接经加 map 重放后 build-id 一致。重放 LLD 共 0 条告警，其中未找到排序符号 0 条。 [逐遍 argv](evidence/25-k1f-2/arm-rpi4-lto-or-kallsyms-argv.json)

arm-rpi4-rt 的实际末次链接经加 map 重放后 build-id 一致。重放 LLD 共 4 条告警，其中未找到排序符号 4 条。 [逐遍 argv](evidence/25-k1f-2/arm-rpi4-rt-lto-or-kallsyms-argv.json)

普通版静态布局核对 **通过**。共同非空 .text 输入节 2,949 个，2,936 个相对序号改变，比例 **99.56%**。普通及 GPL 导出表分别为 6,547 和 7,166 项，逆序及 CRC 槽不配对均为 0。module_layout 二分命中索引 3905。保序输入组无变化，220 条异常表记录及 64,243 条 EXIDX 通过。idmap 两项仍在同一 4 KiB 页，保留页内交换，冷热区大小和成员不变。SMP alternatives、PV 表和 mcount 也通过。 [布局与排序表](evidence/25-k1f-2/arm-rpi4-symbol-order-audit.json)

RT 版的静态排序表核对亦通过。两次中间链接和最终链接各报告 4 个只在普通版清单中的符号。最终重放记录为 jump_label_lock、arch_jump_label_transform、ledtrig_cpu、do_softirq_own_stack。 [RT 排序表](evidence/25-k1f-2/arm-rpi4-rt-symbol-order-audit.json) · [RT LLD 告警](evidence/25-k1f-2/arm-rpi4-rt-link-warnings.txt)

归档 zImage 解压后与本次 vmlinux 的入口、text、build-id note 及关键表节匹配。 [zImage 核对](evidence/25-k1f-2/arm-rpi4-zimage-check.json)

已归档 16 个 RPM（含源包）及两版原始 vmlinux、System.map、zImage、链接 map。产物 SHA 和路径见证据索引。

## Gerrit sandbox

已向 `sandbox/lhmax2025/afdo_kernel_arm32` 追加 0009。读回 tip `be12d5d7d31438be5df6b7d95d7a5193876d3c39`、tree `64c0338faffbc2bc9d3f70295c9caa183bca0535`，父提交 `3a2602c3e12c11c4bf32f2415b02fdf8fe1ee75a`，均与本地一致。 [Gerrit 复核](evidence/25-k1f-2/gerrit-0009-verified.txt)

```text
packaging: support an optional vmlinux symbol ordering file

Expose the symbol ordering file and its checksum as optional RPM
sources. Verify the checksum before invoking Kbuild and apply the
ordering file only to the vmlinux link and its kallsyms passes.
Keep the expanded spec unchanged when the option is unset.

Signed-off-by: Hao Lin <hao.lin@samsung.com>
```
