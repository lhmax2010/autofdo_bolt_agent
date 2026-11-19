# K1c：ARM32 AutoFDO 回移植与 K-BASE 构建

K-BASE 用于后续在 RPi4 采样和与 K-AFDO 配对测量。本轮从 linux-rpi `0fac5de6a63091d141ad1cd3ed9d9e92b8dde708` 构建 ARM32 训练内核。普通与 RT 两个包变体均纳入构建，采样目标为普通版。

## 1. 回移植和配置

内核本地分支为 `k1c-kbase`，tip `7fffbec570692c925cbf1f58ea9b1cd1a5d78ac8`。五个指定上游补丁按顺序应用，零文本冲突。ARM32 特例和板型构建配置各有独立提交。七份补丁均在以原始基线初始化的临时 Git 索引中逐个检查并应用，所得 tree 与构建分支一致。

| 补丁 | 上游 | 本地 | 作用 |
| --- | --- | --- | --- |
| [0001](patches/kernel/0001-kbuild-Add-AutoFDO-support-for-Clang-build.patch) | `315ad8780a12` | `81f9c0f680d6` | Clang AutoFDO 配置、编译开关、训练和消费入口，保留 6.13 架构门禁和 Clang ≥17 条件 |
| [0002](patches/kernel/0002-vmlinux.lds.h-Adjust-symbol-ordering-in-text-output-.patch) | `0043ecea2399` | `538b438ff131` | 在通用文本输出中把特定冷热模式放在一般文本匹配之前 |
| [0003](patches/kernel/0003-vmlinux.lds.h-Add-markers-for-text_unlikely-and-text.patch) | `db0b2991ae1a` | `5afab829f803` | 增加热、冷文本区间标记 |
| [0004](patches/kernel/0004-AutoFDO-Enable-ffunction-sections-for-the-AutoFDO-bu.patch) | `0847420f5e49` | `085cb6e00998` | 引入上游 profile 消费路径的 function-sections 配套，ARM32 特例由 0006 实现 |
| [0005](patches/kernel/0005-AutoFDO-Enable-machine-function-split-optimization-f.patch) | `2fd65f7afd5a` | `56c8dc3c5071` | 引入上游 MFS 和 `.text.split` 区间，架构隔离由 0006 实现 |
| [0006](patches/kernel/0006-ARM-enable-Clang-AutoFDO-without-function-splitting.patch) | 本地适配 | `e23625e56c23` | ARM select `ARCH_SUPPORTS_AUTOFDO_CLANG`，仅 x86 profile 消费加 function-sections 与 MFS，ThinLTO 链接 MFS 同样只在 x86 且提供 profile 时生效 |
| [0007](patches/kernel/0007-ARM-configs-enable-Tizen-RPi4-AutoFDO-training.patch) | 本地构建配置 | `7fffbec57069` | BCM2711 defconfig 打开 AutoFDO，spec 接收可选 release 后缀并将同一后缀用于打包路径 |

Propeller 的 `d5dc95836147` 和 `d63b852430be` 以及 `de0bf1e138fc` 均未进入本轮分支。ARM 保留普通 `TEXT_MAIN` 匹配，专用 `.text.hot{,.*}`、`.text.unlikely{,.*}` 和 `.text.split*` 由 `TEXT_TEXT` 收入输出 `.text`。这样 ARM32 的 AutoFDO 开关不会单独把普通文本 wildcard 扩为 `.text.*`。MFS 仍受 Clang 驱动的目标限制。

将 `CONFIG_AUTOFDO_CLANG=y` 加入 spec 已为普通和 RT 变体合并的 BCM2711 defconfig，沿用 RT/LSM 片段流程。spec 在 build 和 install 两阶段接收 RPM 宏 `kernel_localversion=-kbase`，以 Kbuild 的 `LOCALVERSION=-kbase` 追加后缀。原有 `localversion-tizen` 和 `CONFIG_LOCALVERSION="-v7l"` 提供前缀。RPM 的模块路径原以 `-v7l/` 或 `-v8/` 结尾，同一个宏也用于模块 `%files`。宏可省略，省略时沿用原路径规则。

## 2. 主机节放置探针

整包启动前使用 K1a 冻结 buildroot 中 `clang-accel-x86_64-armv7l` 的 Clang 22.1.8 二进制和 LLVM 库。另以同一 buildroot 的 ARM 原生 Clang 经 QEMU 复核，节归属一致。

| 输入与手写 profile | 普通编译 | 额外加 `-ffunction-sections` |
| --- | --- | --- |
| 小 C 文件，`--target=armv7a-linux-gnueabihf -marm -O2`，`hot_leaf` 样本计数 100,000,000、`cold_leaf` 计数 1 | `.text.hot.` 与 `.text.unlikely.`，各 12 B | `.text.hot.hot_leaf` 与 `.text.unlikely.cold_leaf`，各 12 B |
| `kernel/sched/core.c`，重放 K1a Kbuild 的 ARM 参数和生成头，追加三项训练标志与手写 sample profile | `wake_up_process` 进入 `.text.hot.`（1,748 B），低计数 `sched_set_stop_task` 留在 `.text` | `.text.hot.wake_up_process`（1,748 B），低计数函数进入普通 `.text.sched_set_stop_task`（176 B） |

两组均只生成 `.o`。小样例确认 Clang 会在不开全局 function-sections 时产生带尾点的冷热节。真实调度文件确认热点归组可用，其低计数样本在该源文件和参数下未触发 Clang 的冷节判定。结果支持 K1 首版保留当前链接策略。真实 profile 的冷区和热区大小须待 K-AFDO 消费构建测量。

## 3. GBS 与编译命令核对

使用 K1a 的 Base `20261030.120529` 和 Unified `20261104.125239` 固定 snapshot。新 GBS armv7l buildroot 由原归档中的 130 个 RPM 按 SHA-256 校验后布置缓存，并核对新环境的 130 项已安装 RPM 头哈希和缓存 RPM SHA。两套 Clang 22.1.8 二进制及 LLVM 共享库均与 K1a 对应文件 SHA 一致。

启动时 MemAvailable 19,510,288,384 B，load1 2.22（20 CPU），可用磁盘 184,986,169,344 B。保留 16 GiB 启动门禁、-j2、MemoryMax 6 GiB、MemoryHigh 5 GiB、CPUQuota 200%、nice 19 和 ionice idle。预检的首个包装器进程因本地模块文件名不匹配退出，修正后从同一未使用的 buildroot 路径启动，预检失败时 GBS 尚未执行。

GBS 2.1.1 退出码 **0**，墙钟 **5,131.22 秒**（85 分 31 秒），cgroup 内存峰值 **5,371,985,920 B**（5.003 GiB）。`memory.events` high/max/OOM/OOM-kill 分别为 8245/0/0/0。产出 15 个二进制 RPM 和 1 个 SRPM。

```sh
gbs -c "$KBASE/gbs-01.conf" build -A armv7l --spec linux-rpi.spec \
  --buildroot "$KBASE/gbs-root-01" --threads 1 --define '_smp_mflags -j2' \
  --define 'kernel_localversion -kbase' \
  --define '__spec_build_cmd /usr/bin/env JOBS=2 %{___build_cmd}' \
  --define '__spec_install_cmd /usr/bin/env JOBS=2 %{___build_cmd}'
```

普通和 RT 的合并 `.config` 均只新增 `CONFIG_ARCH_SUPPORTS_AUTOFDO_CLANG=y` 和 `CONFIG_AUTOFDO_CLANG=y`。两者均为 Clang 22.1.8、PMUv3=y、THUMB2_KERNEL=n、DWARF4=y、LTO_NONE=y。release 后缀通过 Kbuild 环境传入。

逐项比较 K1a 与 K-BASE 保存的 Kbuild `.cmd` 编译命令。忽略约定的 release 后缀和这三项训练选项后，C、汇编和可识别的主机编译命令无未申报差异。调度文件实录包含 `-fdebug-info-for-profiling`、`-mllvm -enable-fs-discriminator=true`、`-mllvm -improved-fs-discriminator=true`。ARM32 编译记录中无 MFS、全局 function-sections 或 profile-use；命令中出现这些标志会使校验失败。

| 变体 | K1a/K-BASE 保存命令 | C（非模块/模块） | 带齐训练标志（非模块/模块） | 归一后编译差异 |
| --- | ---: | ---: | ---: | ---: |
| arm-rpi4 | 6,939 / 6,939 | 2,900 / 165 | 2,887 / 165 | 0 |
| arm-rpi4-rt | 6,516 / 6,516 | 2,899 / 165 | 2,886 / 165 | 0 |

每个变体各有 13 条非模块 C 辅助命令未使用训练标志，包括解压器、vDSO、版本和构建辅助对象，共同编译参数仍与 BASE 一致。

每个变体另有一条非编译命令变化。压缩引导解压器的 `ld.lld --defsym _kernel_bss_size=…` 使用输入映像算出的值，普通版由 589396 变为 592136，RT 版由 614832 变为 613584，其他链接参数一致。

## 4. 映像、模块及节表

主机产物位于 `temp/kernel-afdo-k1/kbase/artifacts/`，保留原始带 DWARF 的 vmlinux、System.map、zImage、DTB/overlays、未剥离模块及 RPM。vmlinux 的可装载节重建为原始 Image，解压 zImage 的 gzip 数据得到同一 Image，核对 GNU build-id note 和 DWARF4。两套构建后保留的原始 ELF 均与包处理前归档逐字节一致。

| 变体 | 预期 uname -r | 原始 vmlinux/zImage build-id | RPM devel/debug build-id | DWARF4 CU |
| --- | --- | --- | --- | ---: |
| arm-rpi4 | `6.12.80-arm-rpi4-v7l-kbase` | `96766cfcbff8c33d83ca38152ad02f6a02dd44d4` | `cacec875aa3b8e74ff108d220ccc0c308c029b91` / `cacec875aa3b8e74ff108d220ccc0c308c029b91` | 2,951 |
| arm-rpi4-rt | `6.12.80-arm-rpi4-rt-v7l-kbase` | `3a7f29050e83d65db4f959bff4c4f21bede2f0e8` | `c8a1f3a3d770fed8047711aa83a60f33c50644ee` / `c8a1f3a3d770fed8047711aa83a60f33c50644ee` | 2,950 |

普通版 K1a BASE 的原始 build-id 为 `25599043a52ba8e5edf2f7bf4e9bb51aaf9d65a3`。新 release 和训练构建生成新的二进制身份，后续采样使用 K-BASE 的原始 vmlinux `96766cfcbff8c33d83ca38152ad02f6a02dd44d4`。RPM 以标准 build-id seed 重算了 devel/debug ID。后续 profile 配对以运行映像的 ID 为准。

普通变体的节和地址如下。节单元格为 VMA 与字节数。

| 项 | K1a BASE | K-BASE |
| --- | --- | --- |
| `_text` | `0xc0008000` | `0xc0008000` |
| `_stext` | `0xc0200000` | `0xc0200000` |
| `_etext` | `0xc1600000` | `0xc1600000` |
| `__init_begin` | `0xc2400000` | `0xc2400000` |
| `__init_end` | `0xc2600000` | `0xc2600000` |
| `.text` | `0xc0200000` / 19,870,632 B | `0xc0200000` / 20,049,052 B |
| `.text.hot` | 无 | 无 |
| `.text.unlikely` | 无 | 无 |
| `.text.split` | 无 | 无 |
| `.ARM.exidx` | 无 | 无 |
| `.ARM.unwind_idx` | `0xc219b6c8` / 516,176 B | `0xc219b6e0` / 512,960 B |
| `.ARM.unwind_tab` | `0xc2219718` / 523,164 B | `0xc2218aa0` / 517,896 B |
| `.init.text` | `0xc24003c0` / 345,228 B | `0xc24003c0` / 345,272 B |
| `.exit.text` | `0xc245484c` / 20,368 B | `0xc2454878` / 20,384 B |
| `.init.data` | `0xc247d000` / 347,612 B | `0xc247d000` / 346,076 B |
| `.exit.data` | 无 | 无 |
| `.debug_info` | `0x00000000` / 215,081,476 B | `0x00000000` / 217,062,139 B |
| `.debug_line` | `0x00000000` / 28,686,663 B | `0x00000000` / 31,864,158 B |

ARM 链接脚本将 `.ARM.exidx*` 与 `.ARM.extab*` 分别汇入 `.ARM.unwind_idx` 与 `.ARM.unwind_tab`，因此最终 ELF 中没有同名 `.ARM.exidx`。已核对 unwind 范围与起止符号、init/exit 节与 init 区间。冷热输入并入输出 `.text`，普通 K-BASE 的 `System.map` 标记区间为 hot 0 B、unlikely 104,564 B、split 0 B。训练构建没有使用 sample profile，这些区间反映本次无 profile 链接的实际布局。

GNU `size` 结果，单位为字节。

| 变体 | K1a text/data/bss | K-BASE text/data/bss | 差值 text/data/bss |
| --- | --- | --- | --- |
| arm-rpi4 | 28,426,344 / 7,468,073 / 589,392 | 28,601,158 / 7,465,029 / 592,080 | 174,814 / -3,044 / 2,688 |
| arm-rpi4-rt | 28,528,090 / 7,427,697 / 614,800 | 28,702,686 / 7,423,569 / 613,584 | 174,596 / -4,128 / -1,216 |

arm-rpi4 的 52 个模块，其原始与 RPM 模块 build-id 均匹配，vermagic 与 `6.12.80-arm-rpi4-v7l-kbase` 一致。RPM 的模块文件均位于 `/lib/modules/6.12.80-arm-rpi4-v7l-kbase`，与原模块路径分离。399 个 DTB/overlay 与 K1a 对应产物的 SHA-256 全部一致。

arm-rpi4-rt 的 52 个模块，其原始与 RPM 模块 build-id 均匹配，vermagic 与 `6.12.80-arm-rpi4-rt-v7l-kbase` 一致。RPM 的模块文件均位于 `/lib/modules/6.12.80-arm-rpi4-rt-v7l-kbase`，与原模块路径分离。399 个 DTB/overlay 与 K1a 对应产物的 SHA-256 全部一致。

普通版变动以 `.text` 和调试节为主。与 K1a 相比，`.text` 增加 178,420 B，`.debug_line`、`.debug_loc`、`.debug_info` 分别增加 3,177,495、2,503,856 和 1,980,663 B。调试节变化与加入 profiling debug/discriminator 标志一致；部分对象在链接前尺寸已发生变化，例如 `kernel/sched/core.o` 的 GNU size text 从 74,533 B 变为 74,794 B。链接阶段还改变了冷热节排序和对齐，现有两份构建无法单独量化每项对最终 `.text` 的贡献。`_text`、`_stext`、`_etext` 和 init 区起止地址保持一致。unwind 两节尺寸有变化，区间与边界符号相符；它们仍由相同 ARM unwind 规则收集。BASE 与 K-BASE 的 `kernel/panic.o`、`init/main.o` 均已有 `.text.unlikely.` 输入，K-BASE 的非空冷区无需 profile 才能产生。

[证据索引](evidence/k1c-kbase-index.json)记录补丁、日志和各产物清单的路径及 SHA-256。

## 5. 待验证

- K1d 在获得用户刷写授权后核对启动、运行内核 notes、模块加载、PMU cycles、HDMI 和回滚。当前仅有主机产物证据。
- K1e 用同一次 K-BASE boot 的真实 perf 数据配对原始 vmlinux，核对采样覆盖和 K-AFDO 的 `AppliedSamples` 及节布局。

## 6. K1c 评审收尾核对

### 版本身份与共用模块

PM 决定 K-BASE 和未来的 K-AFDO 均使用 `LOCALVERSION=-kbase`，运行时共用已归档的 K-BASE 模块树。普通版 K-BASE 原始 vmlinux 的 banner 和生成头给出预期 `uname -v` 为 `#1 SMP Wed Nov 18 14:59:26 UTC 2026`，编译身份为 `abuild@linhao-linux`。GBS 构建包装器清除了外部覆盖，这些值来自该次实际构建的 Kbuild 自动值。RT 版独立记录为 `#1 SMP PREEMPT_RT Wed Nov 18 15:19:44 UTC 2026`，采样变体使用普通版。

| K-AFDO 构建输入 | 普通 K-BASE 固定值 |
| --- | --- |
| `KBUILD_BUILD_TIMESTAMP` | `Wed Nov 18 14:59:26 UTC 2026` |
| `KBUILD_BUILD_USER` | `abuild` |
| `KBUILD_BUILD_HOST` | `linhao-linux` |
| `KBUILD_BUILD_VERSION` | `1`，本次探针固定以重现 `#1` |
| `LOCALVERSION` | `-kbase` |

K-AFDO 的 spec 在 %build 中用 RPM 宏展开并 export 前三项，%install 中使用同一 release 后缀。可由 GBS 传入 `--define 'kernel_build_timestamp Wed Nov 18 14:59:26 UTC 2026'`、`--define 'kernel_build_user abuild'`、`--define 'kernel_build_host linhao-linux'`，分别在 spec 中以 `export KBUILD_BUILD_TIMESTAMP="%{kernel_build_timestamp}"` 等引用，时间戳必须保留双引号。本次用 `rpm --eval` 展开后通过原始 `init/Makefile` 生成 UTS_VERSION，复用 `scripts/setlocalversion` 和 `scripts/mkcompile_h` 生成 release 和编译身份。三份结果与 K-BASE 生成头逐字节一致。探针只执行 make 的头文件规则和版本脚本。共用模块的实际可加载性仍需在 K-AFDO 产生后核对 vermagic、Module.symvers 的 CRC 和启动加载结果。

### FS discriminator

K-BASE 原始 vmlinux 的 DWARF4 行表由 `llvm-dwarfdump --debug-line` 读取。地址 `0xc021b13c`、`0xc021b150`、`0xc021b160`、`0xc021b16c` 均属于 `include/trace/events/initcall.h:10` 的 `__traceiter_initcall_level`，discriminator 分别为 3、8、9、11。以相同 GNU build-id `96766cfcbff8c33d83ca38152ad02f6a02dd44d4` 构造一条零 slide 的内核 mmap 和四条合成 IP 样本，用补丁 10 的 `llvm-profgen --ip-samples --kernel` 转换。质量报告为 `verified`、`semantics.fs_discriminator=true`。`llvm-profdata show --sample` 读回四个相对行键 `0.3`、`0.8`、`0.9`、`0.11`，各一条样本。此项验证 ARM32 原始 ELF 的 FS 读取与 profile 写入。

### LLD 排序与链接 map

归档 `.vmlinux.cmd` 使用 LLD 22.1.8，未显式传 `--call-graph-profile-sort`、关闭选项或外部 ordering profile。LLVM 同版本 `lld/ELF/Driver.cpp:getCGProfileSortKind` 默认 `cdsort`，而 `Writer.cpp` 仅在 call-graph profile 非空时按该图排序。检查 `vmlinux.a` 的 2,958 个输入成员，以及归档的 `vmlinux.o`、导出符号和版本对象，均无 `.llvm.call-graph-profile`。K-BASE 的默认排序选项因此没有样本边可用。

K-BASE 的 `CONFIG_VMLINUX_MAP=n`，现有归档以 `System.map` 和节头为布局基准。K-AFDO 记录最终 `ld.lld` argv、归档成员顺序及对象 call-graph section 清单。需要逐输入区分布局时，在诊断用的最终链接命令中追加 `-Map=<绝对路径>`。K-BASE 可用已归档的同一批对象、归档、链接脚本和最终链接输入在临时路径重放这条命令。先核对重放的最终布局，再按输入对象与节名比较 map 中的输出 VMA、大小和排序；保持链接参数一致，用 `System.map` 核对冷热标记和函数地址。此次只核对已归档输入，未执行重链接。

### 同名 local 函数

按 K-BASE ELF 的 `.symtab`，筛选可执行节中的 `STB_LOCAL + STT_FUNC`。同名同地址只算一个实例。34,380 条 local 函数符号中有 462 个名字对应多个地址，合计 1,511 个不同地址实例，比每名只取一项多出 1,049 个。逐项拆开 K1a 原统计中同地址别名，五项基准的核心函数和含模块全量 top 30 与这 462 个名字的精确匹配均为 0。此项使用名字比较，跨构建的同源身份和优化后覆盖不能由名字单独确认。本次未增加 `-funique-internal-linkage-names`。

### 文本增长与 2 MiB 余量

在双方归档中按相同 `vmlinux.a` 成员路径配对，直接读取 ELF 节头。每个对象累加 ARM 链接脚本收入主 `.text` 的输入节，包含热、冷、入口、调度、锁和 fixup 等节，排除 init/exit、unwind 和 debug。汇总为 19,870,960 → 20,048,460 B，净增 177,500 B，能解释最终 178,420 B 中的 99.48%。294 个对象增加、75 个减少，前 20 个合计增加 84,780 B。最终 ELF 与对象净增相差 920 B，包含链接阶段的对齐、填充及其他链接投入物的净影响，此处未进一步拆分。

对象级差异证明增长主要在最终链接前已经出现。K1c 校验的编译命令只新增三项训练标志，另固定变体的 release，因此现有制品支持训练配置影响了代码生成与节大小。未用单旗标编译拆分每项贡献。

| 主文本输入增长排名 | 对象 | K1a BASE B | K-BASE B | 增量 B |
| ---: | --- | ---: | ---: | ---: |
| 1 | `drivers/net/usb/r8152.o` | 118,416 | 135,824 | +17,408 |
| 2 | `sound/soc/soc-dapm.o` | 30,944 | 39,228 | +8,284 |
| 3 | `fs/nfs/nfs4xdr.o` | 54,308 | 61,684 | +7,376 |
| 4 | `kernel/events/core.o` | 99,396 | 105,336 | +5,940 |
| 5 | `net/xfrm/xfrm_state.o` | 33,224 | 38,304 | +5,080 |
| 6 | `fs/btrfs/send.o` | 71,376 | 75,176 | +3,800 |
| 7 | `lib/maple_tree.o` | 67,208 | 70,516 | +3,308 |
| 8 | `fs/f2fs/data.o` | 45,944 | 49,028 | +3,084 |
| 9 | `net/xfrm/xfrm_policy.o` | 37,748 | 40,724 | +2,976 |
| 10 | `fs/btrfs/free-space-cache.o` | 34,676 | 37,648 | +2,972 |
| 11 | `fs/locks.o` | 32,900 | 35,604 | +2,704 |
| 12 | `drivers/regulator/core.o` | 48,904 | 51,548 | +2,644 |
| 13 | `kernel/sched/build_policy.o` | 73,780 | 76,336 | +2,556 |
| 14 | `drivers/net/wireguard/noise.o` | 10,364 | 12,896 | +2,532 |
| 15 | `drivers/nvmem/core.o` | 12,856 | 15,384 | +2,528 |
| 16 | `net/ipv6/route.o` | 52,852 | 55,340 | +2,488 |
| 17 | `block/blk-mq.o` | 43,624 | 45,952 | +2,328 |
| 18 | `drivers/net/usb/ax88179_178a.o` | 19,064 | 21,376 | +2,312 |
| 19 | `drivers/android/binder.o` | 79,648 | 81,904 | +2,256 |
| 20 | `kernel/resource.o` | 12,160 | 14,364 | +2,204 |

`ARM_LPAE=y`、`STRICT_KERNEL_RWX=y`、`DEBUG_ALIGN_RODATA=y` 时，`SECTION_SHIFT=21`，脚本将主文本尾对齐到下一 2 MiB 边界。普通版 K1a BASE 的 `.text` 实尾为 `0xc14f33a8`，到 `_etext=0xc1600000` 余 1,100,888 B。K-BASE 实尾为 `0xc151ec9c`，同一边界余 **922,468 B**。两者对齐后的文本边界相同。该余量描述链接地址，运行时内存仍待启动后测量。

原始记录、脚本和 SHA-256 见[收尾证据索引](evidence/k1c-review-followup-index.json)。
