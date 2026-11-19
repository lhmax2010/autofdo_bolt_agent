# K1 设计 v0.2：RPi4 armv7l 内核 AutoFDO（IP 采样）首次端到端验证

| 项目 | 内容 |
|---|---|
| 版本 | v0.2（按三份评审与 K1c 收尾结果修订；取代 v0.1） |
| 目标 | 在 RPi4（Cortex-A72，A32 内核）上完成一次内核 AutoFDO 端到端：K-BASE 采样 → llvm-profgen 内核 IP profile → K-AFDO → 跨重启配对测量，得到有置信区间的性能结论与按 2 MiB 档位核算的内存结论 |
| 依据 | 00–05、07（K1c 构建与收尾核对）、04 新增节（IRQ 恢复窗口与 C 份额）、reviews/review_claude_code_k1.md、review_Codex_k1.md、review_kimi_k1.md |
| 不在本阶段 | IRQ 影子的修正、分支信息补全（A2/A3/A4）、混合 profile、function sections、MFS/Propeller/ThinLTO、模块 profile、Thumb-2、尺寸调参、arm64 |
| 标注 | **[已证实]** 已有证据；**[需构建验证]** / **[需板上验证]** 本阶段必须证明；**[预登记]** 看结果前锁定，不得事后更改 |

---

## 0. 结论先行（相对 v0.1 的变化）

1. **IRQ 影子是 ARM32 内核 IP 采样的首要问题。** RPi4 的 PMU 溢出中断是普通 IRQ（GIC-400 无 NMI）。K1a 数据中，落在 IRQ 解除屏蔽候选指令及其后一条指令上的样本占全部内核样本：pipe 56.0%、syscall 60.0%、memory 47.3%、ToS 40.3%、tmpfs 35.0% **[已证实：位置统计；是否全部为延迟样本不可由记录判定]**。K1 不修正影子，主 profile 为原始 IP **[预登记]**；但每份 profile 报告影子份额，结论按"可作用份额"解释。修正方法列为 K2 第一研究项（§13）。
2. **构建锁已闭合。** 两个变体同用 `LOCALVERSION=-kbase`，固定 K-BASE 的 `KBUILD_BUILD_TIMESTAMP/USER/HOST/VERSION`（已逐字节复现），profile 经 `gbs --define` 传入同一 spec；运行时共用 K-BASE 模块树，K-AFDO 的模块不部署。
3. **切换改用 RPi 固件 tryboot，只新增文件。** 不改 `config.txt`、`cmdline.txt`、`u-boot.bin`、`boot.scr`、现有 `zImage`；每次切换只写一个几百字节的 `tryboot.txt`。任何普通重启或断电都回到 PLAT。启动失败进入 STOP，不自动重试。
4. **N 由跨重启 A/A 预试决定**，并增加一次布局噪声对照（LLD `--shuffle-sections`），因为 ARM32 无 KASLR、布局固定。
5. **基准调整。** pipe 仍为主比较 **[预登记]**；K1a 的内存测试含 490 ms 休眠，退役，换成无休眠的匿名缺页基准 `mmfault` 作次比较；syscall 不再称"留出"；新增一个不参与训练的留出基准 `forkexec`。
6. **consumption 证据不进被测构建。** 被测 K-AFDO 不加任何诊断参数；诊断通过重放所选目标文件的编译命令得到。
7. **内存按 2 MiB 档位核算。** K-BASE 文本距 2 MiB 边界余 922,468 B；K-AFDO 文本若再增长超过这一余量，会一次性多占 2 MiB，必须单独报告。

---

## 1. 已知事实

| 事实 | 来源 |
|---|---|
| K = linux-rpi `0fac5de6`；clang 22.1.8、LLVM=1、A32、DWARF4；LPAE、STRICT_KERNEL_RWX；无 KASLR | K0、K1a **[已证实]** |
| K-BASE：5 个上游补丁零冲突 + 2 个本地补丁（ARM select、仅 x86 加 function-sections/MFS；spec 接收 release 后缀并用于 `%files`）；分支 `k1c-kbase` tip `7fffbec5` | 07 §1 **[已证实]** |
| K-BASE vmlinux build-id `96766cfc…`；与 K1a 的编译命令差异仅三项训练标志与 release 后缀 | 07 §3–4 **[已证实]** |
| 不开 function-sections 时 clang 产生 `.text.hot.`/`.text.unlikely.`；真实 `sched/core.c` 的热函数进入 `.text.hot.` | 07 §2 **[已证实]** |
| FS discriminator：K-BASE 行表含 discriminator；补丁 10 正确读出并写入独立行键，`fs_discriminator=true` | 07 §6 **[已证实]** |
| LLD 22.1.8 默认 `cdsort`；K-BASE 输入中无 `.llvm.call-graph-profile`，K-AFDO 将会有 | 07 §6 **[已证实]**；K-AFDO 侧 **[需构建验证]** |
| 462 个 local 函数名对应多个地址；与五项基准前 30 无重合 | 07 §6 **[已证实]** |
| `.text` 比 K1a BASE 增长 178,420 B（训练标志引起，99.48% 在链接前已出现）；距 2 MiB 边界余 922,468 B | 07 §6 **[已证实]** |
| PMU 中断为普通 IRQ；IRQ 恢复窗口样本占比见 §0.1；C 可映射份额：pipe 91.1%、memory 81.2%、ToS 85.4%、tmpfs 68.3%、syscall 36.4% | 04 新增节；Claude Code F1 **[已证实]** |
| A72 不实现 PC_WRITE_RETIRED(0x0C)，BR_RETIRED(0x21) 为保留；perf 通用 `branches` 在 RPi4 不可用 | Codex ARM-Q1（A72 TRM）；Claude Code F8 **[已证实]**；板上事件列表 **[需板上验证]** |
| K1a 内存测试每个 worker 含 490 ms 显式休眠 | Codex I3 **[已证实]** |
| 板上 `/boot` 未挂载；启动链：固件 → `u-boot.bin` → `boot.scr` → `bootz zImage` | 03 §4.1、04 **[已证实]** |
| K 的固件驱动支持 `reboot "0 tryboot"` | Claude Code F7 **[已证实（内核侧）]**；EEPROM 与 Tizen reboot 参数 **[需板上验证]** |

---

## 2. 评审意见处置

| 编号（来源） | 问题 | 处置 |
|---|---|---|
| D1 / I5 / Kimi-11.3 | IRQ 影子、可作用份额 | §0.1、§6.4、§9.2、§13 R1。K1 不修正，只度量与解释 |
| D2 / I2 / Kimi-4.1 | N 用开机内 CV 估计；无布局对照 | §8.2 跨重启 A/A 预试；§8.3 布局噪声对照 |
| D3 / S2 / Kimi-11.2 | 切换不可靠、写 FAT、无回退、写入范围 | §5 tryboot、只新增文件、失败状态机、授权范围 |
| D7 / S1 | LOCALVERSION 与打包、构建元数据 | 已由 0007 与固定 KBUILD 变量解决（§3） |
| S3 | 模块会消费 vmlinux profile | K-AFDO 模块不部署，共用 K-BASE 模块树（§3.3）；模块 profile 列 K2 |
| I1 / Kimi-风险2 | 同名 static 函数 | K1 不加 `-funique-internal-linkage-names`（需重建 K-BASE 并改变符号名）；报告歧义名份额，超阈值停止（§6.4） |
| D4 / I7 | 内存口径、2 MiB 量化、PGSO 默认开 | §10 |
| D5 / I6 / Kimi-11.1 | 节验收、链接重排 | §4 |
| D6 / I6 / Kimi-11.4 | consumption 证据做法 | §9 |
| D8 / I4 / Kimi-风险4 | 训练配方、背景负载、样本密度 | §6 |
| I3 / Kimi-11.3 | 内存基准含休眠；syscall 非留出 | §7.1 |
| D10 | 固定 60 秒等待 | §8.1 安静门禁 |
| D11 | 禁止 sample-accurate 与 symbol list | §6.3 |
| D12 | initramfs | §5.2 K1d-a 核查 |
| D9 | ARM32 训练标志 | 已证实（07 §3） |
| I8 / Kimi 方案 Q1–Q7 | 总体方案承诺过强 | 方案 v0.2 另行修订；要点见 §13 |
| G1 / G2 | 补丁计数、GBS 资源继承 | §3.1；沿用 K1a/K1c 已验证的 GBS 环境 |

---

## 3. 变体与构建锁

### 3.1 变体

| 变体 | 内容 | 用途 |
|---|---|---|
| `PLAT` | 板上原内核（build-id `395733b9…`），经 U-Boot 启动 | 参照、恢复；不参与判定 |
| `K-BASE` | `k1c-kbase`，`CONFIG_AUTOFDO_CLANG=y`，无 profile（build-id `96766cfc…`） | 训练、对照 |
| `K-BASE-S` | K-BASE + 最终链接追加 `--shuffle-sections='.text*=<seed>'`（seed 预登记） | 布局噪声对照（§8.3） |
| `K-AFDO` | K-BASE + `CLANG_AUTOFDO_PROFILE=<profile>` | 候选 |

三个自建变体：同一源码 tip、同一 spec 文本、同一冻结 snapshot 与 130 个依赖 RPM、同一 GBS 资源设置；`LOCALVERSION=-kbase`；`KBUILD_BUILD_TIMESTAMP="Wed Nov 18 14:59:26 UTC 2026"`、`KBUILD_BUILD_USER=abuild`、`KBUILD_BUILD_HOST=linhao-linux`、`KBUILD_BUILD_VERSION=1`。变体只差 profile（或 shuffle 参数）。

### 3.2 构建门禁

1. 编译命令逐对象比较：K-AFDO 相对 K-BASE 只多 `-fprofile-sample-use=<profile>`（及上游 Makefile.autofdo 随之加入的参数，逐项列出）；K-BASE-S 编译命令完全相同，仅最终链接多一个参数。
2. 版本字符串、`uname -r`、`Module.symvers` CRC、模块 vermagic 与 K-BASE 一致。
3. K-AFDO 与 K-BASE-S 的构建树保留到 K1 报告完成（诊断重放需要）。
4. 每个变体归档原始 vmlinux、System.map、`.config`、RPM、最终 `ld.lld` argv、`vmlinux.a` 成员顺序。

### 3.3 模块

K-AFDO 与 K-BASE-S 不部署自己的模块；三者运行时共用 K-BASE 模块树 `/lib/modules/<K-BASE release>`。每次启动核对已加载模块列表与 K-BASE 首次启动时一致。K-AFDO 构建产出的模块只归档，用于记录"模块消费了 profile"这一事实，不进入测量。

---

## 4. 节布局与链接

1. 首版不开全局 `-ffunction-sections`（ARM32 下 0006 已只对 x86 开启）。
2. 热/冷归组的验收看**输入**而不是最终节表：
   - 目标文件中 `.text.hot.`/`.text.unlikely.` 的字节数与函数数；
   - System.map 中 `__hot_text_start/end`、`__unlikely_text_start/end` 的区间大小，以及 §9 选出的热 C 函数是否位于热区间；
   - 预期热区可能很小（IP 稀疏 profile 下 PSI 判热/判冷覆盖窄），如实报告，不作为失败条件。
3. LLD 调用图重排保留上游默认 `cdsort` **[预登记]**。K-AFDO 必须记录：含 `.llvm.call-graph-profile` 的目标文件数；用归档输入重放最终链接并追加 `-Map=`，与 K-BASE 同法生成的 map 比较输入节顺序。报告中把"编译期优化"与"链接期重排"分开描述，归因不再单称"profile 的编译器效果"。
4. 用链接 map 核对所有 `.text.<x>` 输入节的去向，确认 ARM 特殊节（head、idmap、entry、`.ARM.exidx/.ARM.extab`、init/exit）边界不变。

---

## 5. 板上部署与切换（K1d）

### 5.1 原则

- **只新增文件，不修改启动链现有文件。** 启动分区新增：`zImage-plat-direct`、`zImage-kbase`（以及后续的 `zImage-kbase-s`、`zImage-kafdo`）、`tryboot.txt`、`cmdline-afdo.txt`。根文件系统新增：`/lib/modules/<K-BASE release>/`。其余写入只在 `/opt/afdo_agent/`。
- **写入方式：** 启动分区只在写入期间以读写方式挂载；先写 `<name>.tmp`、`fsync`、板上校验 SHA-256、rename、`sync`，再读回校验；结束后卸载。
- **首次写入前**：把整个启动分区以只读方式 `dd` 到主机归档，记录 SHA-256；PLAT 模块树做文件清单与 SHA。
- **实验结束**：删除全部新增文件与模块目录，核对启动分区与备份前的文件清单一致，PLAT build-id 正确。

### 5.2 K1d 步骤

| 步骤 | 内容 | 板上写入 |
|---|---|---|
| K1d-a | **只读核查**：启动分区设备与 UUID；`config.txt`、`cmdline.txt`、`boot.scr` 内容（剥离 mkimage 头）；U-Boot 传入的 bootargs 与 `/proc/cmdline`；是否加载 initramfs 及其模块内容；DTB 与 overlay；EEPROM bootloader 版本与 tryboot 支持；板上 `reboot` 能否传参数；A72 PMU 事件列表（`events/` 目录与 PMCEID 反映的事件）；`perf bench` 子命令可用性。**无人值守重启**：用 PLAT 连续 3 次 `reboot`，每次主机等待 ≤5 分钟，sdb 自动重连，核对 `boot_id` 变化、build-id、HDMI 连接、显示栈运行，并记录开机后背景负载曲线（用于 §8.1 的安静门禁阈值）。另：编译并在 PLAT 上试运行新基准 `mmfault`、`forkexec`（只写 `/opt/afdo_agent`），开机内各 10 轮求 CV | 仅 `/opt/afdo_agent` |
| K1d-b | **tryboot 链路验证（PLAT 副本）**：新增 `zImage-plat-direct`（PLAT zImage 的副本）、`cmdline-afdo.txt`、`tryboot.txt`（= `config.txt` 副本，仅把 `kernel=` 改为 `zImage-plat-direct` 并加 `cmdline=cmdline-afdo.txt`，必要时加 `initramfs` 行；diff 归档）。`reboot "0 tryboot"`（板上 `reboot` 不能传参时，用部署在 `/opt/afdo_agent` 的小程序调用 `reboot(2)` 的 RESTART2）。核对：PLAT build-id、`/proc/cmdline`（记录与 U-Boot 路径的差异）、`/sys/firmware/fdt` SHA、HDMI、网络与 sdb、模块加载。再普通重启，确认回到 U-Boot 路径的 PLAT | 启动分区新增 3 个文件 |
| K1d-c | **K-BASE 首次启动**：新增 `zImage-kbase` 与 K-BASE 模块树；`tryboot.txt` 指向 `zImage-kbase`；tryboot 启动。核对：build-id `96766cfc…`、`uname -r`、`/proc/cmdline` 与 K1d-b 一致、dmesg 与 PLAT 对比无新增 oops/BUG/WARN、模块加载列表、PMU `cycles:k` 正计数、HDMI 与显示栈、温度。再普通重启回到 PLAT | 启动分区新增 1 个文件；根文件系统新增模块目录 |
| K1d-d | K-BASE 启动通过后，推送 K-BASE 补丁到 linux-rpi 的 Gerrit sandbox（分支名由用户确认） | 无 |

K1d-b 与 K1d-c 前各需用户确认。

### 5.3 公平性

所有被测变体（K-BASE、K-BASE-S、K-AFDO）都走同一条固件直启路径（tryboot + 同一 `cmdline-afdo.txt` + 同一 DTB/overlay），每次启动核对 `/proc/cmdline` 与 `/sys/firmware/fdt` SHA 与 K1d-b 记录一致。PLAT 经 U-Boot 启动，只作参照。

### 5.4 失败状态机

| 情况 | 处理 |
|---|---|
| 启动超时（5 分钟内 sdb 未回来） | `RECOVERY_REQUIRED`：停止，请用户断电上电（tryboot 一次性，断电后回到 PLAT）；不重试 |
| 身份断言失败（build-id、cmdline、FDT、模块列表） | `STOP`：不测量，回到 PLAT，记录 |
| oops/BUG/WARN、正确性自检失败 | `STOP` |
| 内核正常、未产生测量值的传输故障（sdb 断开、拉取失败） | 整 block 重试一次；第二次仍失败则 `STOP` |

失败 block 不得被静默替换；所有状态写入收据。

---

## 6. 训练（K1e）

### 6.1 采集 [预登记]

- 在 K-BASE 上做 3 次训练会话，每次是一次独立启动（tryboot）。
- 每次会话：安静门禁 → 依次 5 段，每段独立一份 `perf record -a -e cycles -c 1000003 --buildid-mmap`：

| 段 | 参数（与测量不同） | 时长 |
|---|---|---|
| pipe | `perf bench sched pipe`，与测量不同的 loop 数，两端绑 CPU3 | 60 s |
| mmfault | 32 MiB（测量用 64 MiB），绑 CPU3 | 60 s |
| tmpfs | 与测量不同的文件大小，绑 CPU3 | 60 s |
| syscall | `perf bench syscall basic`，绑 CPU3 | 30 s |
| TV 日常 | ToS 720p 解码播放到显示 | 120 s |

- `forkexec` 不参与训练（留出）。
- 显示状态与测量相同（HDMI 接入、显示栈运行、静态画面）。
- 同时记录内核调用栈（`-g`）供 K2 使用，前提是 K1b 的 IP 输入提取能逐字节去掉调用栈；否则训练记录不加 `-g`，另做一次只用于 K2 的调用栈记录。
- 每份记录登记 `boot_id`、build-id、evlist、LOST 计数、各 CPU 样本数。

### 6.2 转换与合并 [预登记]

- 每份记录单独转换：`llvm-profgen --ip-samples --kernel`（补丁 10），输入为该记录与归档的 K-BASE 原始 vmlinux；保守策略 max/none/none/none；完整 CLI 参数写入收据。
- 15 份 profile 用 `llvm-profdata merge --sample` 等权求和（时长固定，因此即按时间加权）。
- 主 profile 使用全部 CPU 的样本（含产品真实存在的显示栈背景）；同时报告负载 CPU（CPU3）与其他 CPU 的样本占比。
- 最终 profile、工具版本与 SHA 锁定后才能构建 K-AFDO。

### 6.3 消费约束

- 不加 `-fprofile-sample-accurate`，不生成 profile symbol list（无样本的函数不得被当作冷函数）。
- 保留 clang 驱动默认的 `-sample-profile-use-profi`。
- K1 不调整 PGSO 等尺寸相关默认值。

### 6.4 质量门禁与报告

必须满足，否则停止：
1. 身份 `verified`；映像外样本 ≤1%；`fs_discriminator=true`。
2. 每段可用的内核 C 行样本 ≥ 50,000；不足时按预登记规则把该段时长加倍重采一次（只允许一次）。
3. 歧义名（§1 的 462 个名字）上的样本占可用样本 ≤ 2%；超过则停止，由 PM 决定是否引入 `-funique-internal-linkage-names`（需重建 K-BASE 并重采）。

必须报告：
- 每段及合并后：IRQ 恢复窗口份额（与 04 新增节同一方法）、汇编份额、未符号化份额、"C 且不在 IRQ 恢复窗口"份额；
- 前 30 函数，标注汇编、IRQ 恢复点、歧义名。

---

## 7. 基准

### 7.1 角色 [预登记]

| 基准 | 角色 | 指标 | 说明 |
|---|---|---|---|
| `perf bench sched pipe` | **主比较** | 墙钟（固定迭代） | 两端绑 CPU3；同分布结果（训练内） |
| `mmfault`（新） | 次比较 | 墙钟 | 单进程绑 CPU3；匿名 mmap 64 MiB、逐页写一次、munmap，重复固定次数；计时窗口内无休眠；校验在窗口外；同时报告 minor faults。只覆盖缺页与清零页，不称"内存压力"或回收 |
| tmpfs 读写 | 探索 | 墙钟 | |
| `perf bench syscall basic` | 探索 | 墙钟 | 汇编占 63.6%，AutoFDO 可作用份额低；参与训练，不称留出 |
| `forkexec`（新） | 探索，**留出** | 墙钟 | fork + exec 一个静态小程序固定次数，绑 CPU3；不参与训练 |
| ToS 720p 解码 | 对照 | 墙钟 | 用户态 BASE 构建；预期无变化，但不是严格的零效应对照 |

只有主比较给出判定标题；其余报告估计与 CI，不做多重比较校正，报告中说明。

### 7.2 可作用份额

每个基准报告 K-BASE 实采的"C 且不在 IRQ 恢复窗口"份额，作为 AutoFDO 能直接作用的样本份额的近似。主比较 inconclusive 或 equivalent 时，用它区分"可作用份额不足"与"profile 无效"。

---

## 8. 测量（K1f）

### 8.1 每次启动的流程

1. tryboot 启动指定变体，身份断言（§5.3）。
2. **安静门禁**：按 `/proc/stat` 计算全板忙时，连续 30 秒低于阈值才放行（阈值 = K1d-a 测得的开机后稳定忙时中位数 + 预登记余量），最长等 10 分钟；记录等待时长与期间前 5 进程。超时记为技术失败。
3. 每个基准：1 轮预热 + r=3 轮计时，启动值 = 3 轮的几何平均。基准顺序固定。
4. 每轮计时前温度门禁：在 performance governor 下、计时窗口开始前即时读取，≤60 °C 才开窗；否则切 powersave 冷却，切回 performance 后等 3 秒并**再次**读取，仍超过则继续冷却，超时记为缺失。T_max 80 °C。
5. 内存读数（§10）在安静门禁通过时读取。

### 8.2 跨重启 A/A 预试与 N [预登记]

- K-BASE 对 K-BASE（同一映像），8 个 AB/BA block（16 次启动），流程与正式测量相同。
- 由配对 log 比的方差估计 N（workflow 公式，ε=1%），上限 40；同时报告 A/A 的点估计与 CI（应包含 0）。
- 每个启动的 3 轮还给出启动内方差，与启动间方差分开报告。
- N 锁定后才开始 §8.3 与 §8.4；达到上限仍不够精确时判 inconclusive，不追加 block。

### 8.3 布局噪声对照

- K-BASE 对 K-BASE-S，10 个 AB/BA block，测 pipe 与 mmfault。
- 报告布局效应的点估计与 CI。若其绝对值 ≥0.5%，K-AFDO 的结果必须注明"效应与布局扰动同量级"，不能只归因于 profile。

### 8.4 正式比较

- K-BASE 对 K-AFDO，N 个 block，AB/BA 顺序按预登记的随机表。分两个会话运行时，每个会话内部 AB/BA 平衡，报告会话效应。
- 统计与判定同 workflow v0.3：以 block 为单位的配对 log 比、20,000 次 block bootstrap、expm1、ε=1%、四种判定；遥测标记、20% 规则、失衡判据不变。
- 判定只依据 block 内配对；失败按 §5.4 处理。

### 8.5 机制指标（不参与判定）

正式比较后，再做 5 个只计数不计时的 block：`cycles:k`、`instructions:k`，以及 A72 实际提供的 L1I refill、L1I TLB refill、分支误预测事件（以 K1d-a 的事件列表为准）。只用于解释机制。

---

## 9. consumption 证据

### 9.1 原则

被测 K-AFDO 构建不加任何诊断参数。诊断从保留的构建树重放所选目标文件的 `.cmd` 编译命令，追加 `-fsave-optimization-record=yaml -foptimization-record-passes=sample-profile` 与 `-mllvm -sample-profile-check-record-coverage=<N>`；重放的产物不进入测量。

### 9.2 选择对象

按合并 profile 选前 20 个热 **C** 函数，排除汇编例程与 IRQ 恢复点所在的小函数（`_raw_spin_unlock_irqrestore`、`arch_local_irq_enable` 等）；按 DWARF 的 CU 映射到目标文件。

### 9.3 证据与门禁

1. 这 20 个函数所在目标文件中，K-BASE 与 K-AFDO 的 `.text` 哈希至少有 1 个不同，否则停止（profile 未进入编译）。
2. 重放得到的 YAML 中有 `Pass: sample-profile`、`Name: AppliedSamples` 且 `NumSamples > 0`；报告每个函数的记录覆盖率与未匹配原因。
3. §4.2 的热/冷区间与热函数位置；§4.3 的链接重排记录。
4. 不要求每个热函数都有机器码变化（正确消费但无优化机会是合法结果）。"工具链打通"与"性能收益"是两个独立结论。

---

## 10. 内存

### 10.1 主机侧（静态）

- `.text`、`.rodata`、`.data`、`.bss` 原始字节；`__hot_text`、`__unlikely_text` 区间大小；
- `_etext` 到 2 MiB 边界的余量（K-BASE 922,468 B）；`_end − _stext` 所在的 2 MiB 档位；
- 压缩 zImage 大小；K-BASE 模块 text 合计（K1 中三个变体共用）。

### 10.2 板上

每次启动安静门禁通过时读 `MemTotal`、`MemFree`、`MemAvailable`、`Slab`、`KernelStack`、`PageTables`；dmesg 的 `Memory:` 行只用于核对档位（"kernel code" 在档位不变时恒定）。整板读数按 block 配对报告，不归因为 AutoFDO 单独的效果。

### 10.3 口径

- 文本字节减少不保证释放等量 RAM；跨过 2 MiB 档位才有可见变化。
- K-AFDO 的文本增长超过 922,468 B 时会多占 2 MiB：作为独立结论单独报告，不中止性能测量。
- PGSO 在带 profile 的编译中默认生效；K1 只记录尺寸变化，不调参。

---

## 11. 步骤、依赖与时间

| 步骤 | 内容 | 依赖 | 估计 |
|---|---|---|---|
| K1d-a | 只读核查、3 次无人值守重启、新基准试运行 | — | 1 天 |
| K1d-b/c | tryboot 链路（PLAT 副本）、K-BASE 首次启动（各需用户确认） | K1d-a | 1–2 天 |
| K1d-d | K-BASE 推送 linux-rpi Gerrit sandbox | K1d-c | 0.5 天 |
| K1e | 训练 3 会话、转换与质量门禁、构建 K-AFDO 与 K-BASE-S（各约 85 分钟）、consumption 证据 | K1d-c | 4–5 天 |
| K1f | A/A 预试（16 次启动）、布局对照（20 次）、正式比较（≤80 次）、机制指标、报告 | K1e | 1.5–2 周 |

剩余合计约 3.5–4 周。K1b 已离线交付；真实同次启动的端到端验证在 K1e 完成。

---

## 12. 门槛与止损

1. K1d：无人值守重启后 sdb 不能自动恢复 → 停止自动化设计，与用户商定连接方式（如 USB sdb）。tryboot 不可用 → 退回"新增文件 + 原子 rename 替换 `zImage`"方案，并重新评审。
2. K1d-c：K-BASE 启动或正确性检查失败且一次修正不能解决 → 回到 PLAT，停止。
3. K1e：§6.4 质量门禁或 §9.3 第 1 项不满足 → 停止。
4. K1f：A/A 的 CI 不包含 0 → 测量系统有偏，停止排查。主比较 inconclusive/equivalent → 结合 §7.2 如实报告；是否进入 K2 由 R1（影子）与 R2（计数 profile）的离线评估决定。

---

## 13. K2 研究项（按优先级；本阶段不实施）

| # | 方向 | 要点 |
|---|---|---|
| R1 | **IRQ 影子的度量与修正** | ARM32 产品内核（包括 TV SoC）都没有 NMI，这是上游 x86/arm64 路线没有遇到的问题。(a) 利用训练记录的内核调用栈，把恢复点上的样本归到调用者的调用点，修正函数级热度；(b) 硬件路线：跨核读取外部调试 PC 采样寄存器（EDPCSR，不受 IRQ 屏蔽影响；需要调试 APB 地址与授权）、PMU 中断改走 FIQ（需要安全态配置权限）；先做可行性探测，再定 |
| R2 | **基于 GCOV 的计数 profile** | 主线 GCOV 内核支持 ARM。实验室插桩构建跑同一训练负载，`llvm-cov gcov` 得到行与块计数，转换为 sample profile（按源码键，不用 FS discriminator）。它不受影子影响，语义上是执行次数，与上游 x86 LBR profile 更接近。既是 R1 的真值，也是一条独立的 profile 来源（K-AFDO-GCOV） |
| R3 | ftrace 函数入口计数 | 零移植的函数级计数，用于校准 R1/R2 |
| R4 | `-funique-internal-linkage-names` | 视 §6.4 的歧义份额决定 |
| R5 | function sections、符号排序、hot-cold-split、链接期死代码回收 | 在 ARM32 上价值需逐项证明 |
| R6 | 尺寸：Thumb-2 内核基线、冷文件 `-Os`，以跨 2 MiB 档位为目标 | |
| R7 | A2（已退休分支事件采样） | RPi4 的 A72 不实现所需事件；TV SoC（A53，32 位内核）列出 `pc_write_retired`，是 A2 的实际探测对象 |
| R8 | RPi5 | A76 只在 EL0 支持 AArch32，不能运行 ARM32 内核；RPi5 只用于 arm64 内核路线 |
| R9 | 模块 profile | 需 Kbuild 侧把 profile-use 与对象类型对应 |

方案 v0.1（01）将据此修订为 v0.2：A2 改到 TV SoC、A4 改为 R2、D 组加入 2 MiB 量化与反向风险、新增 R1。

---

## 14. 风险

| 风险 | 影响 | 缓解 |
|---|---|---|
| IRQ 影子使关中断热路径被低估 | profile 失真，收益偏小 | §6.4 报告、§7.2 解释；R1/R2 |
| 布局偶然性大于 profile 效果 | 归因错误 | §8.3 布局对照 |
| 重启后网络或 sdb 不能自动恢复 | 无法自动测量 | K1d-a 先验证；USB sdb 备选 |
| tryboot 或 Tizen reboot 参数不可用 | 切换方案失效 | K1d-a 核查；小程序调用 `reboot(2)`；退回原子 rename |
| 固件直启与 U-Boot 路径的 cmdline/FDT 不同 | 与 PLAT 不可比 | 只比较同一路径的自建变体 |
| K-AFDO 文本跨过 2 MiB 档位 | 多占 2 MiB | §10.3 单独报告 |
| 共用模块树与 K-AFDO vmlinux 不兼容 | 启动失败 | §3.2 第 2 项核对 CRC 与 vermagic |
| IP 样本稀疏 | 热/冷判定覆盖窄 | §6.4 第 2 项；如实报告 |
| 开机后后台活动 | 噪声 | §8.1 安静门禁 |
