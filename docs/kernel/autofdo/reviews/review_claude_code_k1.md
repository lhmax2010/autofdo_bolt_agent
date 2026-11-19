# K1 设计 v0.1 与 ARM 内核 AutoFDO 能力方案 v0.1 评审（Claude Code）

- **评审对象**
  - 主要：`06_k1_design_v0.1.md`。
  - 总体方向：`01_arm_profile_capability_proposal_v0.1.md`。
  - 背景：00、02、03、04、05。
  - 版本均为 origin/main `6d8b116`。
- **方式：只读**
  - 主工作区有未提交的 `docs/STATUS.md` 修改，`git pull --ff-only` 被拒。本轮没有 stash，改用 `git show origin/main:<path>` 读取新文件。
  - 未构建、未接板、未改任何已有文件，只新建本文件。
  - 为保持独立，没有读取同目录的 `review_Codex_k1.md`、`review_kimi_k1.md`。
- **本轮读取的源码与产物**
  - K = linux-rpi `0fac5de6`，用 `git show` 读取。
  - L = LLVM 22.1.8，位于 `src/llvm`。
  - P = profgen sandbox，位于 `temp/llvm-profgen-sandbox-verify-20261114`。
  - U = 上游 v7.3.5 及已下载的回移植补丁。
  - K1a BASE 产物：`.config`、`System.map`、节表。
  - K1a 基线：`baseline-rpi4-02/summary.json`。
  - RPi4 既有探测：`docs/probe/evidence/05/01_environment_hardware.txt`。
- **标注**
  - **【已证实】**：本轮在源码、产物或既有数据中直接核对过。
  - **【推断】**：由已证实事实推出，没有实测。
  - **【不确定】**：没有足够依据。
  - **【外部】**：文献或硬件手册内容，凭记忆引用，本轮没有重新检索；作为依据使用前需要再核。

---

## 0. 结论：需修改后执行

方向和最小范围是对的：A32、非 LTO、非 MFS、只做 vmlinux、两个变体只差 profile。有几处与 ARM32、clang 22、板上实际情况不符或被低估。其中两处直接影响 K1 结论的可信度：

1. **ARM32 上 PMU 溢出中断是普通 IRQ，不是 NMI。** 在关中断区间里溢出的样本，PC 都落在重新开中断的位置。K1a 自己的数据里，仅 `_raw_spin_unlock_irqrestore` 和 `arch_local_irq_enable` 两个开中断点就占内核样本的 13–30%；主比较 pipe 最高，为 30.4%，另有 13.0% 在 `finish_task_switch`。调度器等关中断热路径会被 IP profile 系统性低估。设计没有提到这一点（§1 F1、F2）。
2. **N 的估计口径不对。** 测量的配对单位是"一次开机"，但 N 用的是同一次开机内 10 轮的 CV。开机之间的方差没有估计，ARM32 又没有 KASLR，每个构建的布局是固定的。N 可能偏小，布局偶然性也无法和 profile 效果区分（§5）。

其余问题：
- **切换方式**：设计假设无人值守重启后 sdb 会自动回来，但 03 §4.2 写的是"用户自行重启并配置网络"。另外每次切换都要写 FAT。
- **内存度量**：2 MiB 量化使 dmesg 的 "kernel code" 不随文本大小变化。
- **K-AFDO 布局**：可能还有链接器按调用图做的重排。
- **consumption 证据**：KCFLAGS 做不到按文件开启优化记录。

必须修改项和顺序见 §7。

---

## 1. 本轮核对的关键事实

| # | 事实 | 依据 | 级别 |
|---|---|---|---|
| F1 | RPi4 的 PMU 中断只能是普通 IRQ。arm_pmu 先调 `request_nmi`，失败才退回 `request_irq`。只有 GICv3 驱动声明 `IRQCHIP_SUPPORTS_NMI`，而 BCM2711 用的是 `arm,gic-400`（GICv2）。所以 PMU 溢出发生在关中断区间时，中断要等开中断后才被处理，样本 PC 落在开中断之后 | `K:drivers/perf/arm_pmu.c:639–646`；`K:kernel/irq/manage.c:1437`；`K:drivers/irqchip/irq-gic-v3.c:2051–2053`；`K:arch/arm/boot/dts/broadcom/bcm2711.dtsi:59` | 已证实 |
| F2 | K1a 各记录的样本构成见下表 | `baseline-rpi4-02/summary.json` 中的 `core_top30`、`kernel_tasks`；汇编函数逐个核对了源码，见表注 | 数据已证实；含义为推断 |
| F3 | 内核映像内存按 2 MiB 量化。<br>• 配置：`ARM_LPAE=y`，所以 `SECTION_SHIFT=21`；同时 `STRICT_KERNEL_RWX=y`、`DEBUG_ALIGN_RODATA=y`。<br>• BASE 布局：`.text` 为 `c0200000+0x12f33a8`，`_etext` 对齐到 `c1600000`，中间空 1,100,888 B（1.05 MiB，相当于 `.text` 的 5.54%）。<br>• dmesg 的 "kernel code" 按 `_etext-_stext` 计算，所以恒为 20,480K；保留区从 `_stext` 到 `_end`，包含这段空隙 | BASE `.config`；`K:arch/arm/include/asm/pgtable-3level.h:48`；`K:arch/arm/kernel/vmlinux.lds.S:55–70,86–90`；BASE `System.map` 与节表；`K:mm/mm_init.c:2588`；`K:arch/arm/include/asm/memory.h:137–139`；`K:arch/arm/mm/init.c:187` | 已证实 |
| F4 | 不开 `-ffunction-sections` 时，clang 也会按函数的 section prefix 输出 `.text.hot.` / `.text.unlikely.`，每个编译单元各一个非唯一节。prefix 由 CodeGenPrepare 根据 profile 热度或 hot/cold 属性设置，`-profile-guided-section-prefix` 默认开 | `L:llvm/lib/CodeGen/TargetLoweringObjectFileImpl.cpp:657–673,946–947`；`L:llvm/lib/CodeGen/CodeGenPrepare.cpp:180–182,588–604` | 源码已证实；实际产物需构建验证 |
| F5 | 核心补丁 `0847420f5e49` 已经在 `CONFIG_AUTOFDO_CLANG` 下把 TEXT_MAIN 扩成 `.text .text.[0-9a-zA-Z_]*`，K-BASE 同样生效。`db0b2991ae1a` 增加 `__hot_text_start/end` 和 `__unlikely_text_start/end` 标记 | `temp/kernel-afdo-k0/patches/0847420f….patch` 中 vmlinux.lds.h 的改动；`db0b2991….patch:34–39` | 已证实 |
| F6 | K-AFDO 可能发生链接时重排：<br>• 非 LTO 时，vmlinux 直接由 `vmlinux.a` 中的各目标文件链接；<br>• CGProfile pass 默认在流水线中；<br>• LLD 默认 `--call-graph-profile-sort=cdsort`，即使有 SECTIONS 脚本，也在每个输入节描述内按调用图排序；<br>• K 没有关闭这项排序 | `K:scripts/link-vmlinux.sh:62–69`；`L:llvm/lib/Passes/PassBuilderPipelines.cpp:1667–1668`；`L:lld/ELF/Driver.cpp:1190`；`L:lld/ELF/Writer.cpp:1104–1117,1258–1262`；K 中检索不到 call-graph-profile-sort | 源码已证实。只在有 profile 计数时才产生 `.llvm.call-graph-profile` 属推断；对 K-AFDO 的实际影响需构建验证 |
| F7 | K 的 RPi 固件驱动支持 `tryboot`：reboot 参数中出现 " tryboot" 时设置一次性标志，下次启动读 `tryboot.txt` 而不是 `config.txt` | `K:drivers/firmware/raspberrypi.c:204–220` | 内核侧已证实；EEPROM 版本和与 U-Boot 链的配合不确定 |
| F8 | RPi4 上 `perf list hw` 只有 `branch-misses`，没有 `branch-instructions`。驱动只有在 PMCEID 含 BR_RETIRED(0x21) 或 PC_WRITE_RETIRED(0x0C) 时才支持通用 branches | `docs/probe/evidence/05/01_environment_hardware.txt:262–267`；`K:drivers/perf/arm_pmuv3.c:1083–1097` | 证据已证实；由此推断两个事件都不在 PMCEID 中（perf list 会试开事件） |
| F9 | 只要有 `-fprofile-sample-use`，clang 驱动默认加 `-sample-profile-use-profi` | `L:clang/lib/Driver/ToolChains/Clang.cpp:6276–6281` | 已证实 |
| F10 | 没采到样本的函数默认不算 cold（entry count 初值 −1）。只有开 `-fprofile-sample-accurate`，或 profile 带 symbol list 时，才按 cold 处理；llvm-profgen 默认不生成 symbol list | `L:llvm/lib/Transforms/IPO/SampleProfile.cpp:163–165,2250–2259`；`P:llvm/tools/llvm-profgen/ProfileGenerator.cpp:49–51` | 已证实 |
| F11 | IP 路径与其他路径共用 FS discriminator 判定，依据是 vmlinux 中的 `__llvm_fs_discriminator__`（weak_odr 常量）。K1b 的实物验证用的是 K1a BASE，它没有 FS discriminator，所以内核上的 FS 路径没有被测到 | `P:…/ProfileGenerator.cpp:145–161`、`ProfiledBinary.cpp:883–895`；`L:llvm/lib/Transforms/Utils/SampleProfileLoaderBaseUtil.cpp:171–181`；05 §3 | 源码已证实；内核实测没有 |
| F12 | ARM32 可用的现成机制：<br>• GCOV_KERNEL：ARM select `ARCH_HAS_GCOV_PROFILE_ALL`，有 `kernel/gcov/clang.c`；<br>• `CORESIGHT_CPU_DEBUG` 依赖 `ARM \|\| ARM64`；<br>• HotColdSplitting 与目标无关；外提出的函数在原函数有显式节时沿用该节，并被标为 cold+minsize；不从 noinline/noreturn 函数外提 | `K:arch/arm/Kconfig:32`；`K:kernel/gcov/`；`K:drivers/hwtracing/coresight/Kconfig:136–144`；`L:llvm/lib/Transforms/IPO/HotColdSplitting.cpp:195–205,257–281,426–431`；`L:…/PassBuilderPipelines.cpp:237` | 已证实（源码） |
| F13 | BASE 配置：`UNWINDER_ARM=y`、`HIGHMEM=y`、`VMSPLIT_3G`、`FUNCTION_TRACER`/`DYNAMIC_FTRACE=y`、`IRQSOFF_TRACER=y`、`AUDITSYSCALL=y`、`MODVERSIONS=y`、`BLK_DEV_INITRD=y`、`HZ_100`；KEXEC、CORESIGHT、CPU_IDLE 均未开 | BASE `artifacts/arm-rpi4/.config` | 已证实 |
| F14 | KCFLAGS 加到全局 `KBUILD_CFLAGS`，不能只对单个文件生效 | `K:Makefile:1042` | 已证实 |

**F2 表：K1a system-wide 记录的内核样本构成（只统计前 30，是下限）**

| 基准 | 内核样本 | 开中断点 | `finish_task_switch` | 汇编函数 | enlightenment 的内核样本 |
|---|---:|---:|---:|---:|---:|
| sched pipe | 70,909 | **30.4%** | 13.0% | 11.3% | 14.6% |
| syscall basic | 68,207 | 3.3% | — | **63.3%** | 18.3% |
| tmpfs | 75,855 | 16.9% | — | 31.2% | 13.3% |
| 内存触页 | 63,323 | 23.6% | — | 17.3% | 16.0% |
| ToS 720p | 13,582 | 13.5% | 1.2% | 14.4% | **60.1%** |

表注：
- **开中断点**指 `_raw_spin_unlock_irqrestore` 与 `arch_local_irq_enable`，后者是 `cpsie i`，见 `K:arch/arm/include/asm/irqflags.h:37–45`。
- **汇编函数**指：
  - `vector_swi`、`ret_to_user`、`__sys_trace(_return)`，位于 `K:arch/arm/kernel/entry-common.S`；
  - `arm_copy_{from,to}_user`、`__copy_from_user_std`、`arm_clear_user`、`memset/mmioset`、`memcpy/mmiocpy`、`copy_page`，位于 `K:arch/arm/lib/*.S`。
- **数据来源**：PLAT 内核 `395733b9`，在接 HDMI 之前采集。

**为什么认为开中断点样本主要是"影子"**（推断，未直接证实）：
- `_raw_spin_unlock_irqrestore` 只有几条指令，却在 pipe 中占 26.6%。
- `__schedule` 不在 pipe 的前 30 中，而上下文切换后重新开中断的 `finish_task_switch` 占 13.0%。
- `vector_swi` 在入口处就执行 `enable_irq_notrace`（`K:arch/arm/kernel/entry-common.S:191–192`）。

可以在主机上用 K1a 现有的 perf.data 做指令级直方图来证实：如果样本集中在 `cpsie i` 或 `msr cpsr_c` 之后的那一条指令上，即为影子。

---

## 2. K1 设计 §11 的 5 个问题

### Q1 首版不开 `-ffunction-sections`、只依赖 `.text.hot`/`.text.unlikely` 是否合理？ARM32 下 clang 的实际行为？

**取舍合理，但对行为的描述和步骤 2 的前提需要改。**

1. **clang 行为（F4，源码已证实）。** 不开 function sections 时，每个编译单元内被判为热的函数放进同一个 `.text.hot.`，判为冷的放进 `.text.unlikely.`，其余留在 `.text`。通用链接宏已经匹配 `.text.hot .text.hot.*`。所以步骤 1 已经能在函数粒度上跨编译单元聚集冷热代码；它缺的是热区内部的顺序。
   - BASE 也会产生 `.text.unlikely.`，来源是内核的 `__cold` 属性，与 profile 无关；两个变体都有。
   - 这件事需要在 K1c 用目标文件节表和 System.map 中 `__hot_text_start/end` 的间距确认（F5 的标记）。
2. **步骤 1 不只是"编译器内部优化"（F6）。** K-AFDO 的目标文件可能带 `.llvm.call-graph-profile`，LLD 默认会在 `.text.hot`、`.text`、`.text.unlikely` 各自的输入节描述内，按编译单元粒度重排。§3.2 中"若不产生，步骤 1 只评估编译器内部优化"的说法因此不准确。
   - 需要增加检查：目标文件是否有该节，K-BASE 与 K-AFDO 的 System.map 中目标文件顺序是否不同。
   - 是否保留这项重排要预先登记。建议保留（这是上游默认行为），但要记录它的存在。
3. **步骤 2 的前提已经满足（F5）。** "扩展 TEXT_MAIN"已由核心补丁 `0847420f5e49` 在 `CONFIG_AUTOFDO_CLANG` 下完成，步骤 2 实际上只是加一个编译参数。这个扩展对 K-BASE 也生效，所以 §3.3 第 2 项要再加一条检查：用链接 map 核对所有 `.text.<x>` 输入节的去向，确认没有 ARM 特殊节被 TEXT_MAIN 吞掉。上游 6.19 那组"排除 startup/exit"的修正正是为这类问题做的，而 K0 判定它们在 K 上冲突。
4. **步骤 2 在 ARM32 上价值有限。** ARM32 没有 MFS，也没有可用的 basic-block sections（K0 §5.2），function sections 剩下的用途是更细粒度的 LLD 排序或 `--symbol-ordering-file`，以及 `--gc-sections` 减小尺寸。建议移到 K2，并写明要验证的假设。
5. **对 ARM32 的预期要调低。**（推断）上游说热文本页对齐有利于 TLB。但这块板子开了 LPAE 和 STRICT_KERNEL_RWX，内核文本在 lowmem 中按 2 MiB 段映射，19.9 MB 文本只用约 10 个段，热区聚集对 iTLB 的帮助很小。收益主要来自 L1I（48 KB）与 L2 的局部性、内联和块布局。
6. **约束。** K1 必须禁止 `-fprofile-sample-accurate` 和 `--populate-profile-symbol-list`（F10）。在 F1 的影子影响下，关中断的热函数（如 `__schedule`）可能 0 样本；一旦把无样本视为 cold，它们会被放进 `.text.unlikely` 并按尺寸优化。设计 §5 的"保守策略同用户态（max/none/none/none）"应把这两项写成明确禁止。

### Q2 并存加复制 zImage 加重启的切换方式是否可靠？有没有更好的办法？

**现方案有四个未验证的前提，失败时也没有自动回退。**

1. **无人值守重启后 sdb 能否自动回来，未证实。** 03 §4.2 第 5 步写的是"用户自行重启并配置网络，再告知就绪"；K1a 用的是 TCP sdb（`192.168.108.26:26101`）。如果重启后网络不能自动恢复，30 个 block 共 60 次重启都需要人工处理。
   - **必须**在 K1d 之前，用 PLAT 连续做 ≥3 次无人值守重启，确认 sdb 在 5 分钟内自动重连。
   - 有条件时改用 USB 连接的 sdb，它不依赖网络配置。
2. **每次切换都要写 FAT。** 板上 `/boot` 没有挂载（04 §运行身份）。每次切换要把 mmcblk0p1 以读写方式挂载，再写入约 14.9 MB 的 zImage（BASE 的 zImage 为 14,906,840 B）。FAT 没有日志，写入时挂起或断电会损坏启动分区，只能取卡恢复。
3. **变体启动失败时不会自动回退。** 用复制方式时，板子会反复启动坏的 zImage，必须现场取卡。
4. **写入范围超出项目规则。** 启动分区与 `/lib/modules` 都在 `/opt/afdo_agent/` 之外。设计只说"首次部署需要用户确认"，应写明这次授权覆盖哪些路径，以及在实验期内持续有效。

**更好的办法：RPi 固件的 tryboot（F7）。**
- **做法**：`config.txt` 保持 PLAT 的启动路径不变。新建 `tryboot.txt` 指向某个变体，用 `reboot "0 tryboot"` 触发。标志只生效一次，之后任何普通重启或断电上电都回到 PLAT。变体挂起时，现场只需断电上电，不用取卡。
- **每次切换要写的文件**：只有 `tryboot.txt`，几百字节。即使写坏，`config.txt` 仍能正常启动 PLAT。
- **难点**：现有链路是 `config.txt` 的 `kernel=u-boot.bin` → `boot.scr` → `bootz zImage`，U-Boot 按固定文件名加载 zImage。`tryboot.txt` 可以让固件直接加载 `kernel=zImage-<variant>`，绕过 U-Boot。这样两个变体都走固件直启，路径一致，对 A/B 比较是公平的；但需要：
  - 用 `cmdline.txt` 复现 U-Boot 传入的 bootargs，并核对两个变体启动后的 `/proc/cmdline` 完全相同；
  - 确认 DTB 和 overlay 的处理一致。
- **不确定项**：EEPROM bootloader 是否支持 tryboot（`vcgencmd bootloader_version`）；Tizen 的 `reboot` 或 `systemctl reboot` 能否把参数传给 reboot(2)。
- **建议的验证顺序**：K1d 先用 `tryboot.txt` 启动一个 PLAT zImage 副本，零风险地验证整条链路。

**其他方式**
- **不建议采用**：
  - kexec：`CONFIG_KEXEC` 没开（F13），开启会改变被测内核；VC4/HDMI 在 kexec 后的重新初始化也不确定。
  - U-Boot 环境变量切换：需要板上有 `fw_setenv`（不确定）并修改 `boot.scr`。
- **如果仍用复制方式**：
  - 先写 `zImage.new`，fsync，在板上校验 SHA，再 rename 并 sync，然后复核 SHA；
  - 只在复制期间以读写方式挂载启动分区；
  - 当相邻两次启动用同一个变体时（例如 AB|BA 相接处）跳过复制。

**模块与 initrd**
- **模块**：建议两个变体使用同一个 LOCALVERSION，共用 K-BASE 构建的一套模块树，只有 zImage 不同（见 §5.4）。这样模块写入减半，模块字节也完全相同，排除了一个混杂因素。
- **initrd**：`BLK_DEV_INITRD=y`。启动链是否加载含 PLAT 模块的 initramfs 尚不确定，需要检查 `boot.scr`。如果加载，新的 `uname -r` 会使 initramfs 中的模块无法加载。

### Q3 训练负载与测试基准的关系、主次比较的选择是否合理？

1. **训练与测试同源。** 内核微基准的训练和测试只差参数，所以这些基准上的估计属于"同分布"结果，应如实标注。
   - syscall 不适合作留出项：它 63.3% 的内核样本在汇编（`vector_swi` 一项就占 60%），AutoFDO 改不了这部分代码。
   - 建议另选一个内核占比高、不参与训练的基准预先登记，例如 `perf bench sched messaging`、`perf bench futex`、`perf bench epoll`，或固定次数的 fork/exec 循环。这些 perf bench 子命令在板上 perf 6.12.80 中是否可用，需要确认。
2. **主比较 pipe 受影子影响最大**（30.4%，另有 13.0% 在 `finish_task_switch`）。它的关键 C 代码（`__schedule`、`try_to_wake_up`、入队路径）大多在关中断时执行，样本会被低估，profile 对这些代码可能起不到作用。
   - 这不是看结果前临时换主比较的理由。但报告应给出每个基准的"AutoFDO 可作用份额上限"，约等于 1 − 汇编 − 影子；按 F2 粗算，pipe 约 45–58%，内存触页约 59%。解释结果时要用到。
   - 如果 K1 前能做影子修正（§6 N1），主比较的设定就更站得住。
3. **训练记录混有背景负载。** system-wide 训练记录中，enlightenment 占内核样本的 13–18%（接 HDMI 前的数据）。
   - 建议按 CPU 拆分：负载固定在 CPU3，用 `perf script -C` 或分开记录，分别生成负载 CPU 和全板的 profile，并报告两者的样本占比。
   - 主 profile 用哪一份要预先登记。TV 日常负载段单独报告。
4. **次比较内存触页只覆盖缺页、清零页和 memcg charge**，04 已核实没有回收和 swap。它不是内存压力基准，报告措辞要与此一致。ToS 作为对照是合理的，但它的内核样本 60% 来自 enlightenment。

### Q4 consumption 证据按文件开启优化记录的做法是否可行？

**按 KCFLAGS 的写法不可行，而且做法本身会破坏 build lock。**

- KCFLAGS 加到全局 `KBUILD_CFLAGS`（F14），不能只对单个文件生效。按文件生效需要在目录 Makefile 中加 `CFLAGS_<obj>.o`，或者包装编译器。这两种做法都会改变被测 K-AFDO 构建的编译命令集合。
- **建议改为两层。**
  1. **被测 K-AFDO 构建不加任何诊断参数。** 证据来自：
     - K-BASE 与 K-AFDO 每个目标文件的 `.text` 哈希差异，热点所在的目标文件必须有变化；
     - `__hot_text_start/end` 区间非空，且前若干个热 C 函数位于其中；
     - llvm-profgen 质量报告中的覆盖率，以及 `fs_discriminator=true`（F11，同时补上内核 FS 路径的实测）。
  2. **诊断单独做，不进入测量。**
     - **首选**：保留构建树，从 `<obj>.o.cmd` 重放所选编译单元的原命令，追加 `-fsave-optimization-record -foptimization-record-passes=sample-profile`，或 `-S -emit-llvm` 检查 `!prof` 中的 `function_entry_count` 与 `branch_weights`。也可以加 `-mllvm -sample-profile-check-record-coverage=N` 输出每个函数的覆盖率（`L:…/SampleProfileLoaderBaseUtil.cpp:27–34`）。`AppliedSamples` 是按指令发出的分析类 remark（`L:…/SampleProfileLoaderBaseImpl.h:434,479`），记录量与有样本的行数成正比。
     - **否则**：做一次全量诊断构建，在 KCFLAGS 中只加 remark 参数，确认其 vmlinux 的装载节与 K-AFDO 逐字节相同后再使用。
     - 注意：K1a 的 GBS root 中已经没有 BUILD 树，必须事先安排保留构建树。
- **选文件的口径要改。** "profile 前 30 热函数"会选到汇编和影子点（`vector_swi`、`memset`、`_raw_spin_unlock_irqrestore`）。应改为排除这两类之后的前 N 个 C 函数。

### Q5 时间估计是否合理？遗漏了哪些风险？

- **时间。** K1b 已交付待评审，剩余 K1c–K1f 约 3–4 周；加上 §7 的必改项约需再加 1 周。
  - **K1c 的 1 周偏紧**：
    - 7 个核心补丁累计干净，但 9 个后续项需要适配，"必要的修正"具体指哪些还没定；
    - 每次 GBS 构建约 67 分钟（2 核），普通和 RT 两套都构建，预计需要 3–5 次构建。
  - **K1f 的 6–8 小时测量估计可信**（按每次开机约 5–6 分钟估算）。但开机间预试、布局对照和诊断构建没有计入。
- **遗漏的风险**（按影响排序）：
  1. **IRQ 影子**（F1/F2）：profile 偏向开中断点，关中断热路径被低估。
  2. **开机间方差与固定布局**（无 KASLR）：N 偏小；布局偶然性被当成 profile 效果【外部：Mytkowicz et al., ASPLOS 2009；Curtsinger & Berger, STABILIZER, ASPLOS 2013】。
  3. **2 MiB 量化**（F3）：PGSO 一类尺寸优化在跨过边界之前，节省的内存为 0；反过来，文本增长超过 5.54% 会**一次性多占 2 MiB**。AutoFDO 的内联会使热路径变大，这在 §10 中没有列出。
  4. **链接时调用图重排**（F6）：会让"只差 profile"的归因多一个来源。
  5. **内核上的 FS discriminator 路径没测过**（F11）：如果判定或映射有误，样本会挂到错误的行键上而不报错。
  6. **重启后网络不能自动恢复、FAT 写入、写入范围超出 `/opt/afdo_agent`**（Q2）。
  7. **开机后的系统活动**：固定等 60 秒不能保证安静。Tizen 开机后会有服务初始化、索引一类后台活动（推断）。应改为安静门禁（§5.3）。
  8. **模块问题**：带 profile 的编译参数也会作用于模块，两个变体的模块字节因此不同。另外，vmlinux 的 profile 可能套到模块中的同名函数上（K0 §3.3）。
  9. **训练参数对代码的影响**：`-fdebug-info-for-profiling` 与 FS discriminator 预期只影响调试信息（推断）。没有验证时，不能声称 K-BASE 等同于产品内核。

---

## 3. 方案 v0.1 §7 的 7 个问题

### Q1 A2（被采分支目标采样）在 A72/A76 上是否可行？skid、可用事件、公开研究？

- **RPi4（A72，AArch32 内核）上很可能不可行。** 原因是事件可用性（F8）：
  - perf 的通用 `branches` 在 RPi4 上不可用，说明 PMCEID 中既没有 BR_RETIRED(0x21)，也没有 PC_WRITE_RETIRED(0x0C)（推断）。
  - 【外部，凭记忆】Cortex-A57/A72 主要实现的是推测类分支事件（BR_PRED 0x12、BR_MIS_PRED 0x10、BR_*_SPEC 0x76–0x7A），而不是架构上已退休的分支事件。推测事件包含错误路径上的分支，采到的 PC 与已执行的跳转目标没有对应关系。
  - 在投入任何 A2 工作之前，先花 10 分钟在板上确认：列出 `/sys/bus/event_source/devices/armv8_cortex_a72/events/`，并用 `perf stat -e r0c,r21,r12,r10` 看计数。如果两个"已退休"事件都没有，A2 在 RPi4 上就按设计不可行，只剩 RPi5（A76，K0 已证实枚举中有 `br_retired`）。
- **skid。** ARMv8.0/8.1 的 PMU 采样基于溢出中断，没有精确归属（这正是 ARM 后来引入 SPE 的原因【外部】）。A72 是乱序核，skid 量级不确定，只能用已知 CFG 的合成微基准实测。
  - 在 ARM32 内核里还叠加 F1 的影子，所以内核上的 A2 只会比用户态更差。
  - 建议探针先在用户态做，因为用户态 IRQ 总是打开的；也不要直接拿 FFmpeg，先用"已知块长、已知跳转次数"的合成程序，真值可以解析得出。
- **公开研究**【外部】：
  - Chen, Vachharajani, Hundt 等，"Taming Hardware Event Samples for FDO Compilation"（CGO 2010），讨论普通事件采样对 FDO 的偏差与修正；
  - Levin, Newman, Haber，HiPEAC 2008，用最小费用流补全不准确的计数；
  - He, Ottoni, Panchenko 等，"Profile Inference Revisited"（POPL 2022），即 Profi。
  - 我不知道有针对 ARM 上"已退休分支目标采样"的公开评估【不确定】，没有做穷尽检索。

### Q2 B1 混合 profile 的融合规则是否合理？有没有更好的方式？

方向成立。问题在于两份数据来自**不同的二进制**：插桩会改变代码，所以不能按地址融合，只能按源码键（函数、行偏移、discriminator）融合，落到 K-BASE 这次构建的行表上。建议：

1. **方向取自实验室，量级取自现场。** 对每个函数，用实验室数据（插桩或 GCOV）给出块和边之间的比例，再按现场样本的函数总量缩放，最后交给 Profi 做流守恒调和。Profi 目前只接收块权重，不接收边先验，需要扩展。这属于研究性质。
2. **按函数决定是否采纳实验室数据。** 比较实验室与现场的块热度秩相关，低于阈值就退回只用现场数据。阈值要预先登记，并在留出负载上评价（E1）。
3. **在 ARM32 上最具体的价值是修复影子。** 现场 IP 在关中断区间几乎没有样本；实验室的计数真值（如 GCOV，见下题）覆盖这些区间，可以用来补上。这比"热度与方向的一般性融合"更容易验证收益。
4. **调用上下文**可以来自现场的内核调用栈（§6 N7），在函数内联决策这一层加权。

### Q3 A4：内核 PGO 运行时与 LLVM 采样插桩的现状、可复用补丁、ARM32 适配难点？

- **现状**（K0 §5.3 已核实）：kernel/pgo 的 v9（2021）没有进入主线。LLVM 22 的采样插桩开关是 `-mllvm -sampled-instrumentation`，依赖 TLS 变量 `__llvm_profile_sampling`，而内核没有 TLS。
- **ARM32 适配难点**：
  - 32 位上的 64 位计数器：原子更新需要 ldrexd/strexd，代价高；不用原子则有竞争；
  - noinstr、中断与递归路径；
  - profraw 格式与版本；
  - 导出一致的快照。
  - K0 估计需要 4–6 周以上，我认同。
- **更快的替代：主线的 GCOV 内核（F12）。**
  - ARM 支持 `GCOV_PROFILE_ALL`，`kernel/gcov/clang.c` 支持 LLVM 的 gcov 格式。可以按目录设 `GCOV_PROFILE := y`，从 debugfs 导出 `.gcda`。
  - 用 `llvm-cov gcov` 就能得到**行级执行次数**。AutoFDO profile 本身就是行级的，所以用来评价 A1/A2 的行样本已经足够，作为 E1 的真值也足够。
  - 缺点：计数器不是原子的（有少量误差）；实验室开销大；插桩构建与 K-BASE 是不同的二进制，只能在源码行这一层比较。
  - 估计 1–2 周即可建立真值流程，不需要移植运行时。

### Q4 A3：ETMv4 移植到 ARM32 的可行性与工作量；perf 对 A32/T32 的解码是否完整？

- ETM4X 依赖 ARM64，这一点 K0 已证实。ETMv4 也可以通过内存映射接口访问，驱动中有 MMIO 访问路径，所以只走 MMIO 的移植在原理上可行（推断）。但还需要 sink（ETF/ETR）、AUX 缓冲在 ARM32 上可用，以及 SoC 拓扑与调试授权。
- RPi4 的设备树里没有 CoreSight 节点。BCM2711 的调试与跟踪拓扑我没有找到公开资料【不确定】，所以**无法在 RPi4 上验证**，工作量也无法在拿到目标 SoC 之前估计。
- 【外部】OpenCSD 支持解码 ETMv3、PTM、ETMv4 下的 A32/T32；perf cs-etm 在 32 位环境下对 T32 指令长度的处理是否完整【不确定】，必须用已知轨迹的测试样例验证。
- 建议维持"等 HQ 提供 SoC 信息"的结论，不放进 P1/P2 的关键路径。

### Q5 D 组：ARM32 上尺寸优化与冷热拆分能否在不损失性能的前提下减少内存？有没有遗漏的手段？

- **先纠正一个前提。** 方案 D1 中"text 体积下降直接等于内存下降"在这块板子上不成立（F3）。
  - 内核映像按 2 MiB 量化，当前只剩 1.05 MiB 余量。尺寸优化节省不到 1.05 MiB 时，RAM 节省为 0。
  - 反过来，AutoFDO 让文本增长超过 5.54% 时，会多占 2 MiB。
  - 模块文本合计只有 0.67 MB；整机内存的主要部分在 slab、页表、vmalloc 和用户态。内核文本优化的上限很小，必须按 2 MiB 量化如实报告。
- **方案中遗漏的手段**（都需要实测尺寸与性能）：
  1. **Thumb-2 内核作为尺寸基线。** 在 ARM32 上这是最大的文本尺寸杠杆，通常能小约 25–30%【外部/推断】。先只构建、只量尺寸，成本很低；性能需要配对测量。
  2. **按 profile 对冷文件用 `-Os`。** 对所有负载中都没有样本的编译单元整体用 `-Os`，比 PGSO 更稳健、更容易审计。前提是 F1 的影子不会把关中断热代码误判为"无样本"。所以必须以多负载并集，加上 GCOV 覆盖作为判定依据。
  3. **用 hot-cold-split 代替 MFS**（F12，源码已证实可用于任意目标）。它在 IR 层把冷区外提为 cold+minsize 函数，进入 `.text.unlikely`；有显式节的函数（如 `__init`）外提出的部分留在原节内。风险：调用开销、栈回溯、kprobe 黑名单，需要构建与启动验证。属于 K2 研究项。
  4. **`LD_DEAD_CODE_DATA_ELIMINATION`**：K 中 `HAVE_=y`。配合 function sections 可以回收未引用代码；需要核对 initcall、exidx、导出符号的 KEEP 规则。
  5. **按 profile 混用 ISA**：热代码保持 A32，冷编译单元用 Thumb。这是研究性想法，可行性【不确定】：`ARM()`/`THUMB()` 宏是按 `CONFIG_THUMB2_KERNEL` 全局决定的，内联汇编、展开表和 ftrace 都可能出问题。
- **用户态 RSS（D2）** 是更有希望看到"内存减少"的方向，按 `smaps` 的 Rss 测量即可。

### Q6 有没有方案中没有、但更好的做法？

见 §6。最值得先做的三项：
- **N1**：识别影子样本，并按调用者归属。仅 ARM32 需要，主机侧即可完成。
- **N2**：用 GCOV 作真值，代替 A4。
- **N3**：用 LLD `--shuffle-sections` 做布局噪声对照。

### Q7 推荐路线的顺序与门槛是否合理？哪些估计明显偏低？

- **调整 P0**，增加三项低成本工作：
  - 在主机上用 K1a 的 perf.data 量化影子；
  - A2 事件可用性的 10 分钟板上检查；
  - 用 GCOV 真值流程替换 A4 移植。
- **P1 门槛要量化**："IP-only 有可测收益或尺寸收益"应写成预先登记的 ε 和置信区间判定。尺寸收益按字节和 2 MiB 量化分别给出。
- **估计明显偏低的项**：

| 项 | 方案估计 | 评审意见 |
|---|---|---|
| A4 | 3–4 周 | 4–6 周以上；改走 GCOV 约 1–2 周 |
| A3 | 2–4 周 | 没有硬件就无法估计 |
| C1 | 1–2 周 | 偏低：9 项后续补丁需要适配，还要加启动验证 |
| B1 | 3–4 周 | 依赖跨二进制的源码键映射与真值，是研究性工作 |
| P2/P3 | 各 4–6 周 | 偏乐观 |
| A1 | 1–2 周 | K0 改为 2–3 周，现已交付 |

- **建议顺序**：
  1. K1，即 C1+A1，同时完成影子量化与必改项；
  2. GCOV 真值，作为 E1 对 A1 的评价；
  3. 影子修复或轻量 B1；
  4. A2 只在事件可用的平台上做，先 RPi5；
  5. D 组，按 2 MiB 量化如实报告；
  6. A3 视硬件而定；A5 维持低优先级。

---

## 4. 与 ARM32、clang 22、Tizen GBS 实际行为不符或风险被低估之处

| # | 设计位置 | 问题 | 依据 | 严重度 |
|---|---|---|---|---|
| D1 | §1、§5、§10 | 没有考虑 IRQ 影子。主比较 pipe 30.4%+13.0%，内存触页 23.6% | F1、F2 | 高 |
| D2 | §6.2 | 用开机内的 CV 推出 N，但配对单位是一次开机；没有布局噪声对照 | §5.1–5.2 | 高 |
| D3 | §4 | 重启后网络与 sdb 是否自动恢复未证实（03 §4.2 第 5 步要求用户配置网络）；每次切换都写 FAT；没有自动回退；写入范围超出 `/opt/afdo_agent` | 03 §4.2、04、F7 | 高 |
| D4 | §6.5 | 用 dmesg 的 "kernel code" 和尺寸作为内存证据，但它恒为 20,480K；没有列出文本增长超过 5.54% 会多占 2 MiB 的风险 | F3 | 中高 |
| D5 | §3.2 | 步骤 2 的前提已由核心补丁满足；"步骤 1 只评估编译器内部优化"忽略了 LLD 调用图重排 | F5、F6 | 中 |
| D6 | §7 | 按文件追加 KCFLAGS 做不到；诊断参数进入被测构建会破坏 build lock；"前 30 热函数"会选到汇编和影子点 | F14、F2 | 中 |
| D7 | §2 | LOCALVERSION 不同、模块各一套，不符合"只差 profile"；构建时间戳、用户名、主机名没有固定；profile 如何进入 GBS 构建（spec Source 或 `--define`）没有写明 | 03 §3（uname-v 含构建时间）、本文 §5.4 | 中 |
| D8 | §5 | 训练记录混入 13–18% 的背景负载；没有留出基准；syscall 的汇编占比为 63% | F2 | 中 |
| D9 | §2、§3.3 | 内核上的 FS discriminator 路径没测过；ARM32 是否接受训练参数也还要构建确认（设计已标注） | F11 | 中 |
| D10 | §6.2 | 开机后固定等 60 秒，没有安静门禁 | 推断 | 中低 |
| D11 | §5 | 没有写明禁止 `-fprofile-sample-accurate` 与 symbol list | F10 | 中低（现在是默认值，但必须写进约束） |
| D12 | §4 | 没有检查 initramfs 是否含 PLAT 模块 | F13 `BLK_DEV_INITRD=y` | 低（需核实） |

---

## 5. 测量方法的改进与替代方案

### 5.1 block 结构与 N

- **正式测量前在开机之间做预试。** K-BASE 开机 6–8 次，每次开机每个基准计时 r=3 轮，得到开机间方差 σ_b² 与开机内方差 σ_w²。配对差的方差约为 2σ_b² + 2σ_w²/r，用它求 N，上限仍为 40。现在的"K-BASE 上 10 轮预试"如果在同一次开机内完成，就测不到 σ_b。
- **每次开机计时 3 轮，取平均作为这次开机的值。** pipe 每轮约 13 秒，与 2–3 分钟的重启开销相比可以忽略。配对单位仍是 block。

### 5.2 布局噪声对照（ARM32 没有 KASLR）

- **做法**：构建 1–2 个 K-BASE-S 变体，在 vmlinux 的最终链接中加入 LLD 的 `--shuffle-sections='.text*=<seed>'`（`L:lld/ELF/Options.td:703–706`）。它只在每个输入节描述内打乱，冷热分组保持不变。用 10 个 block 比较 K-BASE 与 K-BASE-S。
- **解读**：如果 |Δ| 与 K-AFDO 的预期效果同一量级，报告中必须说明 K-AFDO 的差异不能只归因于 profile。
- **成本**：每个变体多一次构建（约 67 分钟）和约 2 小时测量。
- **待验证**：`LDFLAGS_vmlinux` 在顶层 Makefile 中先被清空再赋值（`K:Makefile:530,930,1046–1059`），这个参数怎样传入最终链接需要构建验证。

### 5.3 切换与开机后的门禁

- 切换方式见 Q2：优先 tryboot，复制方式作为退路，并加上原子写入与 SHA 校验。
- **把固定等 60 秒改为安静门禁。** 按 `/proc/stat` 计算全板忙时，连续 30 秒低于预先设定的阈值才放行，最长等 N 秒；记录等待时长和期间排名前五的进程。之后再接温度门禁。

### 5.4 build lock

- **两个变体的构建参数**：
  - 使用相同的 LOCALVERSION，`-kbase` 和 `-kafdo` 不再需要，靠运行 build-id 区分；
  - 固定 `KBUILD_BUILD_TIMESTAMP`、`KBUILD_BUILD_USER`、`KBUILD_BUILD_HOST`；
  - 使用同一份 spec 文本，profile 通过 `%{?autofdo_profile}` 条件和 `gbs build --define` 传入。
- **模块**：只部署 K-BASE 构建的一套模块。先核对两次构建的 `Module.symvers` 与 vermagic 相同。profile 本来只覆盖 vmlinux，这样也避免了 vmlinux profile 套到模块上。
- **可复现性（建议）**：K-BASE 重建一次，比较 vmlinux 装载节的字节。不能逐字节复现时，记录差异来源；否则 K-BASE 与 K-AFDO 的差异无法完全归因。

### 5.5 ε=1% 与机制指标

- ε=1% 对 pipe 和内存触页合适（开机内 CV 约 0.8%）。按 §5.1 的预试结果预先登记最小可检出效应。
- **另加只计数、不计时的轮次**，在两个变体上采集：
  - `cycles:k`、`instructions:k`；
  - L1I_CACHE_REFILL(0x01)、L1I_TLB_REFILL(0x02)、BR_MIS_PRED(0x10)。A72 是否实现这几个事件【外部】，需要在板上确认。
  - 这些指标只用来解释效果的机制，不参与判定。

### 5.6 主比较、次比较与留出

- 保持 pipe 为主比较、内存触页为次比较，并预先登记。
- 另加一个留出基准（见 §2 Q3）。所有训练过的基准都标为"同分布"。
- 报告每个基准的可作用份额上限（1 − 汇编 − 影子）。

### 5.7 内存度量（替换 §6.5 的口径）

- **主机侧**：
  - `.text`、`.rodata` 的原始字节数；
  - `__hot_text`、`__unlikely_text` 区间大小；
  - `_end − _stext` 的保留量及其所在的 2 MiB 档位；
  - `_etext` 余量（BASE 为 1,100,888 B）。
- **板上**：MemTotal、MemFree、Slab，在安静门禁通过后的同一时点读取。dmesg 的 "kernel code" 只作为档位核对。
- **止损与报告**：K-AFDO 的文本跨过 2 MiB 档位时必须单独报告。

---

## 6. 方案中没有、我认为更好或更有新意的做法

| # | 做法 | ARM32 可行性 | 验证方法 | 级别 |
|---|---|---|---|---|
| N1 | **识别影子样本，并按调用者归属。** 质量报告统计落在 IRQ 解除屏蔽指令之后的样本：`cpsie i`、`msr cpsr_c` 一类的 restore，以及异常返回。可选两种处理：丢弃；或者结合内核调用栈（`perf record -g`，`UNWINDER_ARM=y` 可用），把样本记到调用者的调用点上（例如 `try_to_wake_up` 中调用 `raw_spin_unlock_irqrestore` 的那一行）。函数级热度因此得到修正；块级仍然无法恢复 | 高。主机侧只需改 llvm-profgen；采集多一个 `-g` | 先在 K1a 的 perf.data 上做指令级直方图，确认影子存在；再用 GCOV 真值（N2）比较修正前后函数热度的秩相关 | 机制已证实，效果待验证 |
| N2 | **用 GCOV 内核作真值**，代替 A4 移植运行时 | 高（F12） | 实验室构建一次，跑训练负载，导出 `.gcda`，用 `llvm-cov gcov` 得到行计数，与 IP profile 的行样本比较秩相关和覆盖率 | 源码已证实 |
| N3 | **布局噪声对照**：用 LLD `--shuffle-sections` 生成随机布局的 BASE（§5.2） | 高 | 用 10 个 block 估计布局效应的量级 | 选项已证实，传参方式需构建验证 |
| N4 | **用 hot-cold-split 代替 MFS** | 中（F12；内核兼容性未知） | K2：构建、启动、链接 map，再看尺寸与配对性能 | 源码已证实，内核未验证 |
| N5 | **尺寸工作按 2 MiB 量化计算**：先测 Thumb-2 内核的尺寸基线；对冷文件做文件级 `-Os`；目标是能跨过档位的节省 | 高（只需构建） | 只看主机侧尺寸，跨过档位的组合再做配对测量 | 量化已证实 |
| N6 | **外部调试 PC 采样（EDPCSR）**：用另一个核或调试端口读取目标核的 PC 采样寄存器，不受 IRQ 屏蔽影响，可以从根本上消除影子。`CORESIGHT_CPU_DEBUG` 支持 ARM32，只是目前仅在 panic 时读取 | 不确定：需要 BCM2711 调试 APB 的地址和 DBGEN/NIDEN 授权，没有公开资料 | 先向 HQ 或 SoC 资料确认调试 APB 能否访问；如果能，再做实验室原型 | 不确定 |
| N7 | **用内核调用栈得到调用点计数**，用于内联决策和函数排序（`perf -g`） | 中高：采集可行；llvm-profgen 需要新增"IP+调用栈"的输入路径（研究项） | 与 GCOV 调用计数比较 | 推断 |
| N8 | **用 IRQSOFF tracer 量化每个函数的关中断时间**，作为影子归属的独立核对（`IRQSOFF_TRACER=y` 已开） | 高（只在实验室用，有开销） | 与 N1 修正后的函数热度对比 | 配置已证实 |

---

## 7. 结论与必须修改项

**结论：需修改后执行。** 下列必改项完成后，K1 可以按现有框架执行。

### 必须修改（按优先顺序）

1. **IRQ 影子（D1）**
   - §1 与 §10 加入 F1 和 F2。
   - K1e 之前，在主机上用 K1a 的 perf.data 做指令级直方图，证实或否定影子。
   - 质量报告增加"开中断点样本占比"。
   - 约束中写明禁止 `-fprofile-sample-accurate` 与 profile symbol list。
   - pipe 的结果要结合可作用份额上限来解释。
2. **开机间预试与布局（D2）**
   - 用跨开机的预试求 N，每次开机计时 r=3 轮。
   - 布局噪声对照（N3）列为强烈建议；如果不做，报告必须写明这一局限。
3. **切换方式的前提与安全（D3）**
   - K1d 之前，用 PLAT 证实连续 ≥3 次无人值守重启后 sdb 能自动重连。
   - 优先评估 tryboot（先用 PLAT 副本零风险验证），复制方式作为带原子写入和 SHA 校验的退路。
   - 写明启动分区与模块树的写入授权范围。
   - 增加安静门禁（D10）。
4. **build lock（D7）**
   - 相同 LOCALVERSION；固定构建时间戳、用户名、主机名；同一 spec 文本，profile 通过 `--define` 传入。
   - 两个变体共用 K-BASE 构建的模块树（先核对 `Module.symvers` 与 vermagic）。
5. **内存度量（D4）**：改为 §5.7 的口径，§10 加入"文本增长超过 5.54% 会多占 2 MiB"的风险。
6. **consumption 证据（D6、D9）**
   - 被测构建不加诊断参数；诊断改为重放编译命令或单独的诊断构建，并保留构建树。
   - 按 C 函数选文件。
   - K1c/K1e 的门禁中加入：质量报告 `fs_discriminator=true`；K-BASE 与 K-AFDO 的 System.map 目标文件顺序比较（判断是否发生调用图重排）。
7. **§3.2 的事实更正（D5）**：步骤 2 的 TEXT_MAIN 前提已由 `0847420f5e49` 满足；步骤 1 可能有链接时重排；§3.3 第 2 项加入链接 map 中 `.text.<x>` 输入节去向的核对。

### 强烈建议

- 增加留出基准，并把训练过的基准标为"同分布"（D8）。
- 训练记录按 CPU 拆分，并报告背景占比。
- 增加只计数的机制指标轮次（§5.5）。
- K-BASE 可复现性检查（§5.4）。
- 检查 initramfs（D12）。
- 时间估计增加约 1 周。

### 对方案 v0.1 的建议修改

- **A2**：先做事件可用性检查。RPi4 上很可能不可行，改为 RPi5 优先，探针用合成程序。
- **A4**：改为用 GCOV 作真值（N2），运行时移植作为远期选项。
- **D 组**：加入 2 MiB 量化与"文本增长会多占内存"的反向风险，补上 N4、N5。
- **新增 N1 影子修正**，作为 ARM32 内核 IP profile 的必要组成部分。
- **路线与估计**：按 §3 Q7 调整。

---

## 附：本轮未做或不确定的事项

- 没有在 perf.data 上做指令级直方图；"开中断点样本主要是影子"仍是推断。
- 没有在板上确认以下各项：
  - A72 的 PMCEID 和可用的原始事件；
  - tryboot 与 EEPROM 版本；
  - 重启后网络是否自动恢复；
  - 是否加载 initramfs；
  - perf bench 子命令是否可用。
- 没有构建任何内核，下列各项都只有源码层面的依据：
  - `.text.hot.` / `.text.unlikely.` 是否实际产生；
  - `.llvm.call-graph-profile` 是否存在，链接时是否重排；
  - FS discriminator 符号是否保留在 vmlinux 中；
  - hot-cold-split 与内核是否兼容。
- 【外部】标注的文献和 A72 事件实现情况凭记忆引用，本轮没有重新检索。
- 主工作区没有 pull（本地有 `docs/STATUS.md` 修改），新文件按 origin/main `6d8b116` 读取。本轮只新建了本文件，没有提交，也没有推送。
