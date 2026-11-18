# K1 设计 v0.1：RPi4 armv7l 内核 AutoFDO（IP 采样）首次端到端验证

| 项目 | 内容 |
|---|---|
| 版本 | v0.1（评审稿） |
| 目标 | 在 RPi4（armv7l，A32 内核）上完成一次内核 AutoFDO 端到端：训练内核 → 采样 → llvm-profgen 内核 IP profile → AFDO 内核 → 与 BASE 内核配对测量性能与内存，得到有置信区间的结论 |
| 依据 | 00_feasibility.md（K0）、02_upstream_backport_inventory.md、03_k1a_base_kernel_build.md、04_k1a_baseline.md（基线与 HDMI 检查）、方案 v0.1（01_arm_profile_capability_proposal） |
| 不在本阶段 | 分支信息补全（A2/A3/A4）、混合 profile（B1）、MFS/Propeller/ThinLTO、模块 profile、Thumb-2 内核、arm64（RPi5） |
| 标注 | **[已证实]** K0/K1a 已有证据；**[需构建验证]**/**[需板上验证]** 本阶段必须证明 |

---

## 0. 结论先行

1. 首版只做最小改动：回移植上游 AutoFDO 构建支持的 7 个核心补丁并适配 ARM32；**关闭 MFS，不用 LTO，第一步不开全局 -ffunction-sections**；profile 只覆盖 vmlinux。
2. 两个内核变体都由我们构建，只差 profile：`K-BASE`（开启 AutoFDO 构建支持、不带 profile，即训练内核）与 `K-AFDO`（同配置 + profile）。板上原内核（PLAT）只做参照，不参与判定。
3. 测量需要在两个内核之间切换，每个 block 重启两次。切换方式：板上并存两套内核与模块（不同 LOCALVERSION），重启前复制对应 zImage，重启后用运行 build-id 断言身份。
4. 基准：主比较 **pipe**（调度/IPC），次比较 **内存触页**（缺页/memcg）；tmpfs、syscall 为探索性；ToS 解码只作为用户态对照（内核占比 1.4%，预期无变化）。
5. 内存目标在 K1 只做度量：vmlinux 各段尺寸、启动后内核内存占用；尺寸优化（PGSO 等）放到 K2。
6. 环境标准：**RPi4 接 HDMI、TV 显示栈保持运行**（K1a 证实：接入后 enlightenment 不再占满单核，空闲温度中位 54.5°C）。

---

## 1. 已知事实（K0/K1a）

| 事实 | 来源 |
|---|---|
| 板用源码 linux-rpi `0fac5de6`（含 PMUv3 与 force_reclaim 修正 `f240c280`），clang 22.1.8、LLVM=1、A32（THUMB2_KERNEL=n）、DWARF4 | K0 §2 **[已证实]** |
| 7 个核心上游补丁在 K 上累计 apply 干净；后续 11 项中 9 项需适配 | K0 §3 **[已证实]** |
| ARM32：clang 驱动拒绝 MFS 与有效 basic-block sections；ARM32 无 ThinLTO select | K0 §3、§5.2 **[已证实]** |
| 非 LTO/非 GC 下 TEXT_MAIN 只匹配 `.text`；全局 -ffunction-sections 必须同步扩展 | K0 §3.1 **[已证实（源码）]** |
| RPM 打包会重写 debug 文件 build-id；profile 必须用归档的原始 vmlinux | K1a §3.1 **[已证实]** |
| 基准内核周期占比：pipe 97.7%、内存触页 97.9%、tmpfs 99.4%、syscall 87.2%、ToS 1.4%；CV 0.4–1.3% | K1a **[已证实]** |
| 接入 HDMI 后 enlightenment 不再持续占满单核；空闲温度中位 54.5°C（schedutil） | K1a HDMI 检查 **[已证实]**；performance governor 下需复核 |
| llvm-profgen 内核 IP 支持：设计见 K0 §4.2，实现为 K1b | 进行中 |

---

## 2. 内核变体

| 变体 | 内容 | 用途 |
|---|---|---|
| `PLAT` | 板上原内核（build-id 395733b9…） | 参照；恢复用 |
| `K-BASE` | K + AutoFDO 构建支持补丁 + `CONFIG_AUTOFDO_CLANG=y`，无 profile；LOCALVERSION `-kbase` | 训练（采样）与对照 |
| `K-AFDO` | 与 K-BASE 完全相同的源码/配置/工具链/冻结仓库，仅多 `CLANG_AUTOFDO_PROFILE=<profile>`；LOCALVERSION `-kafdo` | 候选 |

- 训练构建按上游 Makefile.autofdo：`-fdebug-info-for-profiling`、`-mllvm -enable-fs-discriminator=true`、`-mllvm -improved-fs-discriminator=true`（DEBUG_INFO 已开）。**[需构建验证：ARM32 接受这些选项]**
- 消费构建：`-fprofile-sample-use=<profile>`；**不加** `-fsplit-machine-functions`（ARM32 不支持）；第一步**不加** `-ffunction-sections`（见 §3）。
- 同一冻结仓库、同一 GBS 环境、同一 spec（仅 LOCALVERSION 与 profile 不同）；build-lock 规则同 workflow：除声明的候选选项外，编译命令集合相同。
- 两个变体各自的 vmlinux（原始、带 DWARF）、System.map、模块、RPM 全部归档。

---

## 3. 回移植与 ARM32 适配

### 3.1 补丁范围（首版）

- 7 个核心补丁（K0 表中 `315ad8780a12`、`0043ecea2399`、`db0b2991ae1a`、`0847420f5e49`、`2fd65f7afd5a` 及必要的修正），按依赖顺序应用；Propeller 两项不引入。
- 门禁模型：采用 6.13 风格（arch/Kconfig 的 `ARCH_SUPPORTS_AUTOFDO_CLANG`），为 ARM 新增 select；不混用 7.2 的移除门禁模型。
- Makefile.autofdo：MFS 相关标志按架构隔离（ARM 不加），不通过 `-mllvm` 绕过驱动限制。
- `de0bf1e138fc`（删除 clang>=17 限制）不引入。

### 3.2 节放置策略（分两步）

1. **步骤 1（首版）**：不开全局 `-ffunction-sections`。依赖编译器按 profile 把热/冷函数放入 `.text.hot` / `.text.unlikely` 前缀节，K 的通用链接宏已匹配这些节。**[需构建验证：在 ARM32、非 function-sections 下，clang 是否实际产生这些节；检查 vmlinux 节表与 System.map 中热函数的位置]**。若不产生，步骤 1 只评估"编译器内部优化"（内联、分支布局、寄存器分配等）的收益，并如实记录。
2. **步骤 2（K1 后半或 K2）**：开启 `-ffunction-sections`，同时扩展 TEXT_MAIN 匹配 `.text.[0-9a-zA-Z_]*` 并保证冷热节先匹配、特殊节（head/idmap/entry/noinstr/init/exit/exception/unwind、`.ARM.exidx/.ARM.extab`）边界不变；以链接 map 核对。

### 3.3 构建与启动验证门禁（每个变体）

1. 构建成功；`.config` 中 AUTOFDO_CLANG=y，其余与 K 的 defconfig 合并结果一致（差异清单只允许 AutoFDO 相关项与 LOCALVERSION）。
2. vmlinux 节表、`_text`/`_stext`、`.ARM.exidx` 范围、init/exit 节与 K1a BASE 对比，差异全部可解释。
3. 板上启动：运行 build-id 等于该变体 vmlinux；dmesg 与 PLAT 启动日志比较，没有新增 oops/BUG/WARN；模块全部按预期加载（与 PLAT 的已加载模块列表比较）；PMU cycles:u/k 正计数；HDMI 显示正常。
4. 任一失败：停止，按 03_k1a §4.4 恢复原内核。

---

## 4. 板上并存与切换

- `/boot`：保留 PLAT 的 zImage 备份；安装 `zImage-kbase`、`zImage-kafdo`；DTB/overlays 用 PLAT 的（不随变体切换，三者相同则只保留一份，不同则停止重新设计）。
- 模块：`/lib/modules/<uname-r>-kbase`、`...-kafdo` 各自一套，互不覆盖；不改 PLAT 的模块树。
- 不用 RPM 安装变体（避免覆盖 config.txt 与 PLAT 包状态）：从构建产物直接放置文件，SHA 清单记录；首次放置前完整备份 boot 分区与 PLAT 模块树（03_k1a §4.2 的备份规则）。
- 切换：`cp zImage-<variant> zImage` → `sync` → 通过 sdb 发起 `reboot` → 主机等待 sdb 重新上线（超时 5 分钟）→ 断言运行 build-id 与该变体一致 → 记录启动时间、dmesg 摘要。超时或断言失败：停止，请用户现场处理。
- 首次部署与首次切换需要用户确认；之后由 workflow 自动切换。所有板上改动在实验结束时恢复为 PLAT（并核对 PLAT build-id）。

---

## 5. 训练（采样）

- 在 K-BASE 上，按固定脚本运行训练负载：pipe、内存触页、tmpfs、syscall 各一段（参数与测量用的不同，例如不同消息大小/内存大小/文件大小），外加一段 HDMI 下的 TV 类日常负载（ToS 解码播放到显示）。
- `perf record -a -e cycles -c 1000003 --buildid-mmap`，每段固定时长，R=3 次；遥测与温度门禁同测量。
- 转换：llvm-profgen `--ip-samples --kernel`（K1b），输入为三次采样与归档的 K-BASE 原始 vmlinux；显式保守策略同用户态（max/none/none/none）；质量报告保存。
- 训练/测试关系如实披露：内核微基准的训练与测试共享内核路径（这是预期的），参数不同；syscall 作为部分留出（训练中占比低）的检查项。

---

## 6. 测量

### 6.1 基准与比较

| 基准 | 角色 | 指标 |
|---|---|---|
| perf bench sched pipe | 主比较 | 墙钟（固定迭代数） |
| 内存触页（固定进程组） | 次比较 | 墙钟 |
| tmpfs 读写 | 探索 | 墙钟 |
| perf bench syscall basic | 探索（部分留出） | 墙钟 |
| ToS 720p 解码（用户态 BASE 构建） | 对照（预期无变化） | 墙钟 |

只有主比较给出判定标题；次比较与探索项报告估计与 CI，不做多重比较校正，报告中说明。

### 6.2 block 结构

- 一个 block = 依次启动两个内核（顺序按预登记的 AB/BA 表随机），每次启动后：等待 60 秒稳定 → 冷却门禁 → 每个基准 1 轮预热 + 1 轮计时（基准顺序固定）。
- N：由 K1a 的 CV 预估（pipe 约 30，内存触页约 29）；正式前在 K-BASE 上做 10 轮预试重新求 CV 并锁定 N（上限 40）。
- 每个 block 两次重启，约 2–3 分钟开销；30 个 block 约需 6–8 小时（含冷却），可分两段运行（按 block 恢复）。

### 6.3 统计与判定

与 workflow 相同：block 内配对 log 比、20,000 次 block bootstrap、expm1 变换、ε=1%，四种判定；遥测标记、20% 规则与失衡判据不变；技术失败（重启超时、sdb 中断）整 block 重试一次。

### 6.4 环境

- HDMI 接入、TV 显示栈运行；正式前在 performance governor 下复核空闲负载与起跑温度。
- 计时窗口内 governor = performance、频率固定；轮间冷却允许切到 powersave，门禁满足后切回 performance 并等待 3 秒再开窗口（内核轨道的 PM 决定；workflow 是否采用另由用户决定）。
- T_start 60°C（冷却目标 58°C，若可达）、T_max 80°C。

### 6.5 内存度量（K1 只度量，不优化）

- 主机：两个变体 vmlinux 的 `size`（text/data/bss）、各节大小、热/冷节大小、模块 text 总和。
- 板上每次启动后：`/proc/meminfo`（MemTotal、MemFree、Slab、KernelStack 等）、dmesg 中 "Memory:" 行（kernel code/rwdata/rodata/init/bss）。
- 报告两个变体的差异；不做判定。

---

## 7. 正确性与 consumption 证据

- 正确性：每次启动的 §3.3 第 3 项检查；每个基准的自检（pipe 计数、内存程序校验和、tmpfs 文件 SHA）；ToS 解码输出与 PLAT oracle 一致。
- consumption：K-AFDO 构建时对含 profile 前 30 热函数的源文件开启 `-fsave-optimization-record=yaml -foptimization-record-passes=sample-profile`（只对这些文件，避免全内核记录量过大），要求存在正数 AppliedSamples；并对这些函数比较 K-BASE/K-AFDO 的目标代码差异。**[需构建验证：按文件追加 KCFLAGS 的方式]**

---

## 8. 依赖与顺序

| 步骤 | 内容 | 依赖 | 估计 |
|---|---|---|---|
| K1b | llvm-profgen 内核 IP 支持（第 10 个补丁） | K0 §4.2 | 2–3 周 |
| K1c | 回移植 + ARM32 适配补丁；构建 K-BASE；主机侧节表/配置核对 | — | 1 周 |
| K1d | 首次部署 K-BASE（用户确认）、启动验证、HDMI/温度复核 | K1c | 1–2 天 |
| K1e | 训练采样、转换（真实端到端验证 K1b）、构建 K-AFDO、consumption 证据 | K1b、K1d | 3–4 天 |
| K1f | 并存切换自动化、预试、正式测量、报告 | K1e | 1 周 |

K1b 与 K1c 可以并行。总计约 4–6 周（与 K0 估计一致）。

---

## 9. 门槛与止损

1. K1c：ARM32 训练选项或节放置无法通过构建验证 → 停止，回报适配问题。
2. K1d：K-BASE 启动或正确性检查失败且无法在一次修正内解决 → 恢复 PLAT，停止。
3. K1e：profile 质量报告显示内核目标样本不足或身份不能验证 → 停止；consumption 无正数 AppliedSamples → 停止。
4. K1f：主比较 inconclusive 或 equivalent → 如实报告；只有在 K2 的改进（function sections、尺寸优化、分支信息）有合理理由时再继续。

---

## 10. 风险

| 风险 | 影响 | 缓解 |
|---|---|---|
| IP-only profile 对内核收益小于 1% | 无法检出 | 如实报告；进入方案 v0.1 的 A2/A4 路线 |
| 训练选项在 ARM32 内核编译失败 | 阻塞 | 逐项隔离，保留可用的子集 |
| 重启切换不稳定（网络、sdb） | 测量中断 | 按 block 恢复；超时请用户现场处理 |
| 热/冷节在非 function-sections 下不产生 | 布局收益缺失 | 步骤 2 再开 function sections |
| 板上原有配置未知（无 /proc/config.gz） | PLAT 只能作参照 | 判定只用 K-BASE/K-AFDO |
| 显示栈负载随画面变化 | 噪声 | 测量期间显示静态画面；记录 DRM 状态 |

---

## 11. 请评审重点

1. 首版不开 `-ffunction-sections`、只依赖 `.text.hot/.text.unlikely` 前缀节的取舍是否合理？ARM32 下 clang 的实际行为？
2. 并存 + 复制 zImage + 重启的切换方式是否可靠？有没有更好的办法（例如 U-Boot 变量选择内核）？
3. 训练负载与测试基准的关系、主/次比较的选择是否合理？
4. consumption 证据按文件开启优化记录的做法是否可行？
5. 时间估计是否合理？遗漏了哪些风险？
