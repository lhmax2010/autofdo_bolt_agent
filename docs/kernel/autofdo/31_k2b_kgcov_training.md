# K2b 续：独立 K-GCOV 与宿主机重启恢复

**K2b 完成。** 三次独立 K-GCOV 启动共导出 15 段计数，已生成 GCOV 与混合候选。RPi4 已恢复 PLAT。 [证据索引](evidence/31-k2b/index.json)

## 已完成的构建阶段

选择性 GCOV 沿用 `kernel/sched`、`kernel/locking`、`fs`、`mm`、`lib` 和 `kernel` 六个目录，覆盖 K1e 合并 profile 中 91.44% 的 C 行权重。`GCOV_PROFILE_ALL=n`，release 改为 `6.12.80-arm-rpi4-v7l-kgcov`。普通变体的实际 `module_layout` CRC 是 `0x2f3f1497`，与 30 号报告的配对预检一致。 [ABI 预检](30_k2b_selective_gcov.md)

Base `20261030.120529` 和 Unified `20261104.125239` 远端目录返回 404。用同一项目配置和原 130 个 SHA 锁定 RPM 建本地仓库。第一次本地尝试因 GBS 2.1.1 将 SQLite primary 当作 XML 解析而退出，改为仅生成 XML 元数据后进入构建。已核对新 buildroot 的 130 个 RPM 头 SHA 均与 K1a 冻结记录相同。

| 项目 | 结果 |
| --- | --- |
| gzip zImage | 17,378,248 B，超过历史容量上限 15,880,192 B |
| XZ zImage | 11,408,536 B，落盘文件重启后复核大小一致 |
| XZ 对应内核 | build-id `3d6e80182e504736cb06d14a62aed6845fef6c4d` |
| boot_a 预计最低空闲 | 4,995,072 B，基于历史 2,048 B 簇和原子替换开销，写前仍需板上复核 |
| 普通模块 | Kbuild `modules_install` 暂存区 52 个 .ko |
| 完整 RPM 打包 | 退出状态 −15，墙钟 4,941.54 秒，未完成 |

[镜像大小收据](evidence/31-k2b/restart/zimage-build-sizes.log) · [构建退出收据](evidence/31-k2b/restart/interrupted-build.json)

## 宿主机重启和恢复门禁

宿主机重启前，K2b 守卫连续两次采到可用内存低于 6 GiB，随后终止打包。该构建单元峰值约 5.0 GiB，cgroup 的 OOM 和 OOM kill 都是 0。最后一份资源收据的全局可用内存约 3.6 GiB，load1 约 140。旧启动日志另有阻塞任务记录，随后记录 systemd 关机，整机失去响应的根因仍未确定。 [终止前读数](evidence/31-k2b/restart/pre-shutdown-resource-samples.jsonl)

恢复使用保留的镜像、GCNO、`Module.symvers`、生成头文件和 Kbuild 暂存模块。待资源门禁通过后，独立输出目录只用 `-j1` 重建六个 extra 模块，随后核对全部 58 个模块的 ABI、去 BTF 和 p6 容量。当前恢复单元 CPUQuota 为 100%，MemoryHigh 1.5 GiB，MemoryMax 2.5 GiB，禁用 swap，nice 19，I/O 优先级 idle。用户 cgroup 无设备带宽控制器，镜像验证的批量读取在程序内限为 12 MB/s。开工要求可用内存至少 16 GiB、load1 小于 CPU 数的 0.6 倍、磁盘空间至少 50 GiB、全局 I/O full PSI 的 avg10 不超过 5%，并取得共享构建锁。资源门禁最多等待 3 小时。重启恢复初次归档时 I/O full PSI 的 avg10 为 56.14%，恢复尚未开工。 [恢复状态](evidence/31-k2b/restart/recovery-state.json) · [资源窗口](evidence/31-k2b/restart/resource-samples.jsonl)

## 两轨共用的主机重负载规则（首次归档）

自 2026-11-26 起，K0 的 GBS/rpmbuild、内核和模块构建、打包与压缩、大文件镜像校验、批量下载及大规模 perf 和 profile 分析，统一先对 `WORKDIR/temp/host-gbs.lock` 取独占 flock。锁贯穿资源等待与重型步骤，排队和持锁等待合计最多 8 小时。轻量 SDB 查询、小文件核对和文档无需取锁，tryboot 仍执行既有的主机构建互斥检查。

K2b 恢复单元先取锁，再记录开工读数。要求 `MemAvailable ≥ 16 GiB` 且 `/proc/pressure/io` 的 `full avg60 < 20%`，未通过时持锁每 10 分钟复查。原有 avg10、负载、磁盘和 3 小时资源等待门槛同时生效。保留单核、2.5 GiB 内存上限、禁用 swap 和 idle I/O。运行时守卫记录连续低于 6 GiB 的采样并中止步骤，原有更严的运行中止条件继续生效。中止后按收据报告。 [恢复守卫](evidence/31-k2b/shared-heavy-rule/guard-recovery.py) · [门禁核验](evidence/31-k2b/shared-heavy-rule/gate-check.txt)

当前单元 `kernel-k2b-recovery-shared-gate.service` 已启用新规则。归档时共享锁由另一进程持有，K2b 尚未进行恢复构建或镜像校验。 [新单元状态](evidence/31-k2b/shared-heavy-rule/unit-state.json) · [锁观察](evidence/31-k2b/shared-heavy-rule/lock-observation.txt)

## K2b 恢复门禁对齐

2026-11-26 03:30:24 PST 启用新单元 `kernel-k2b-recovery-aligned.service`。开工前取独占共享锁，锁内只判定 `MemAvailable ≥ 16 GiB`、I/O `full avg60 < 20%` 和磁盘余量 `≥ 50 GiB`。该阶段取消旧 avg10 和 load1 条件。若未通过，先释放锁，再等待 10 分钟复查，资源等待上限 3 小时。符合门禁即开工，完成后释放锁。单核、2.5 GiB 上限、禁用 swap、idle I/O、12 MB/s 校验限速及运行中资源保护保持原值。 [新守卫](evidence/31-k2b/aligned-gate/guard-recovery.py) · [锁内读数](evidence/31-k2b/aligned-gate/admission-checks.jsonl)

前三次锁内检查的 I/O avg60 分别为 35.56%、42.71%、49.16%。同期可用内存分别为 19.57、20.28、23.24 GiB，磁盘余量分别为 145.82、145.77、143.23 GiB。三次均因 I/O 未达到开工条件，检查后均已释放锁。 [单元状态](evidence/31-k2b/aligned-gate/unit-state.json)

上一单元在 01:53 曾获得开工资格，随后在对比 GCNO 目录时因 `Path` 与字符串比较出错而停止。保留原错误，并修正比较类型。轻量清单复核确认六个目录分别有 4、7、63、66、121 和 66 个 GCNO 对应已链接对象，共 327 个。 [旧错误](evidence/31-k2b/aligned-gate/previous-gcno-error.log) · [修正脚本](evidence/31-k2b/aligned-gate/discover-notes.py)

主机恢复完成后的顺序为 p6 容量核对与写入、PLAT 5 分钟空闲温度门禁（中位 ≤58°C，每 10 分钟复查，最多 2 小时）、用户在 RPi4 旁时首启。温度等待期间 boot_a 保持原样。此处的部署和训练状态将在取得板上收据后更新。

## 对齐后的恢复结果

04:12:24 PST 拿到共享锁并实际开工。可用内存 21.76 GiB、I/O full avg60 15.33%、磁盘余量 177.08 GiB。04:13:45 PST 完成并释放锁，退出码 0，墙钟 81.3 秒，cgroup 峰值内存 1.30 GiB，无 OOM。XZ zImage 的 SHA-256 为 `f74fc430e35e463cd06aeee87ffebd8bda5c54194e8bc84a319bbb4933c0c698`，与保留的原始 vmlinux 和 raw Image 配对通过。 [恢复收据](evidence/31-k2b/host-recovered/recovery-result.json) · [镜像核对](evidence/31-k2b/host-recovered/image-identity.json)

从原 `linux-tizen-modules-source-11.0.0-0.armv7l.rpm` 串行重建 6 个 extra。源包 SHA-256 为 `ef770d5e8af0532fe4f80748a699e13710025fb0c1218f6504bc9eee1d80dbf5`。58 个模块全部去除 `.BTF`，其中 6 个 extra 同时去除 `.BTF.base`。其余节内容、vermagic `6.12.80-arm-rpi4-v7l-kgcov SMP mod_unload modversions ARMv7 p2v8` 和 `module_layout=0x2f3f1497` 均核对通过。depmod 无输出。327 个已链接 GCNO 已锁定供首启逐节点核对。 [逐模块核对](evidence/31-k2b/host-recovered/module-abi.json) · [预期 GCDA 节点](evidence/31-k2b/host-recovered/expected-gcda.txt)

p6 写前可用 11,354,112 B，模块树估算 3,670,016 B，1.2 倍门槛 4,404,020 B。板上 `du` 读回为 4,165,632 B，写前空间也高于实测的 1.2 倍。只新增 `/lib/modules/6.12.80-arm-rpi4-v7l-kgcov/`，逐文件 SHA 读回通过，PLAT 和 K-BASE 模块树的 SHA 均一致。p6 已恢复只读，剩余 7,684,096 B，UID 5001。 [p6 容量](evidence/31-k2b/host-recovered/p6-preflight.txt) · [写后空间](evidence/31-k2b/host-recovered/p6-after.df) · [模块 SHA](evidence/31-k2b/host-recovered/kgcov-ro.sha256)

按顺序写完 p6 后，在 PLAT 保持原 governor，首个 5 分钟窗口采 30 点，中位 **56.965°C**，范围 55.991–58.426°C。04:19:10 PST 已通过 ≤58°C 门禁，未触发 10 分钟复查。boot_a 尚未写入，未发出 tryboot。 [温度门禁](evidence/31-k2b/host-recovered/temperature-gate.json) · [原始窗口](evidence/31-k2b/host-recovered/temperature-window.tsv)

## 首启前的板上状态（历史）

宿主机重启后，共享 SDB 一度无监听。端口恢复监听后仅重新连接 RPi4。只读核对确认 PLAT build-id 对应原内核，boot ID 未变，原 cmdline、U-Boot、tryboot=0、UID 5001 与 p6 只读状态均复核通过。重启后的额外 5 分钟只读温度中位数 59.400°C（范围 57.939–60.374°C，30 点），高于首启准备的 58°C 门槛。 [PLAT 身份](evidence/31-k2b/restart/plat-identity.txt) · [温度原件](evidence/31-k2b/restart/plat-thermal.tsv)

p6 与温度门禁已通过。boot_a 镜像部署、首启和 15 段训练仍待执行。`.gcda` 导出为 0 段，GCOV 质量、与 IP/R1 的对照及混合候选均无实测结果。首启仍需确认用户可在 RPi4 旁观察 HDMI。

## K-GCOV 首启、脚本恢复和训练

首启前 PLAT 5 分钟温度中位 56.965°C，实际发令前温度 57.939°C。发令前通知用户观察 HDMI。2026-11-26T04:58:08.559-08:00 发出 tryboot，74.12 秒后首条 SDB 命令成功。首启及各会话验收通过 ARMv7l、tryboot=1、cmdline、规范化 FDT、HDMI、网络、dlog、D-Bus、10/10 模块路径与运行 build-id、挂载和 dmesg 差异。首个安静门禁通过后于 2026-11-26T05:02:01.716-08:00 确认全部 327 个预期 GCDA 节点可读，含 pipe 和 highmem。 [首启身份](evidence/31-k2b/session-01/boot/direct-summary.json) · [FDT](evidence/31-k2b/session-01/boot/fdt-comparison.json) · [节点收据](evidence/31-k2b/first-boot-accepted.json)

首启后的 pipe 导出因板上缺少 `cmp` 失败，未纳入训练。清理后普通重启 74.14 秒恢复 PLAT，复核 UID 5001，tryboot 配置恢复 K-BASE。将脚本内三处文件比较改成板上已有的 SHA-256 核对，从 PLAT 只重新指向已有的 K-GCOV 镜像，在新的 boot ID 重新采集完整第一会话。用户确认 PC 只有本任务后，本轮后续主机控制与转换取消临时资源限制。板上的重启身份、安静与温度门槛、tryboot 前构建互斥继续按原规则执行。 [旧导出错误](evidence/31-k2b/session-01/training/pipe.stdout) · [修复脚本](evidence/31-k2b/reproduction/train-board.sh) · [rearm 核对](evidence/31-k2b/rearm/boot-after.sha256)

| 会话 | boot ID | tryboot 到首条 SDB 命令 | 安静门禁耗时 | 回 PLAT 到首条命令 | 模块 |
| --- | --- | ---: | ---: | ---: | ---: |
| 1 | `7db2e57e-1d7b-4f7b-bc85-28895f1ed7f3` | 74.13 s | 138.1 s | 73.99 s | 10/10 |
| 2 | `83804af7-b698-4692-97c1-404c6f2b3680` | 74.01 s | 214.7 s | 61.03 s | 10/10 |
| 3 | `2c62a755-0e36-4077-90ba-7c32b05b443a` | 86.28 s | 311.6 s | 74.02 s | 10/10 |

每次独立启动先通过全板忙时 <2.91% 连续 30 秒的门禁。负载按 K1e 参数依次绑 CPU3，沿用 60/60/60/30/120 秒及 performance 下的 60°C 开窗门槛。每段开始前写 debugfs reset，结束后逐个复制 GCDA，拉回 tar 并核对归档和内部每文件 SHA。训练期间只采集覆盖计数。导出期间其他 CPU 和后台任务仍在运行，读数为逐文件快照。GCOV 插桩和导出本身也会改变记录到的路径频度，影响对照。

| 会话 | 负载 | 负载秒数 | 起跑 / 窗口最高 °C | CPU3 所在 policy 频率 MHz | GCDA 数 | tar SHA-256 |
| --- | --- | ---: | --- | --- | ---: | --- |
| 1 | pipe | 60.46 | 58.426 / 63.296 | 1500 | 327 | `54e8e9215b3e423973c4924c3dfbcfa813beb7f8067976c5527428c7f9e30dd3` |
| 1 | mmfault | 60.53 | 59.887 / 63.783 | 1500 | 327 | `e798ab18e7502db342f07391264f65953315d04f74693010307469f76648c163` |
| 1 | tmpfs | 60.53 | 59.400 / 64.270 | 1500 | 327 | `ea101e3adcb11e0f1b28cbaaec7f48ff71c007a0cfe176f7844605ef4294182d` |
| 1 | syscall | 30.21 | 59.400 / 62.809 | 1500 | 327 | `6940aff1a9173111def889e532ae29d1478b9e8eec2ab5edfd8d5f39cb3cc306` |
| 1 | tos | 121.05 | 58.913 / 64.757 | 1500 | 327 | `580c666eb8e5b5fb0c33ee4209be550a44723fecfb4a802570045b8fd001bfd6` |
| 2 | pipe | 60.48 | 57.939 / 63.296 | 1500 | 327 | `e2e2ed536221a81469c5c53676547165a78ca58f5902509a1a015bfda866dd0a` |
| 2 | mmfault | 60.50 | 59.887 / 63.783 | 1500 | 327 | `071f4d997cf28bfbd3da74deca15cbfc6ba94e2b6cdff76c6a1366f52703ccb4` |
| 2 | tmpfs | 60.53 | 59.400 / 64.270 | 1500 | 327 | `a4a498f74701754d4c2ff8511b468afe4ec7d916f27a60aa5328f1cbe29ce7c1` |
| 2 | syscall | 30.21 | 59.887 / 62.809 | 1500 | 327 | `efdf3ac75c9f7ef818763260777a3a2bd3bac10055ea964c354d971c21301e98` |
| 2 | tos | 121.04 | 58.913 / 65.244 | 1500 | 327 | `8d3b98ce0cc5e71db8fc04bfa8b517860cb6111b3a1b7a73a0aa1f69f2c8b09b` |
| 3 | pipe | 60.46 | 57.939 / 62.809 | 1500 | 327 | `71ccc1cc7764990723d3674fa3b41fe3e6ab2a15cd6b704b6593a7a623ef6dfe` |
| 3 | mmfault | 60.49 | 59.400 / 63.296 | 1500 | 327 | `a77c56d614b887cece55ea40a6d467f8a8f25fe013d73a260a32d898b50bbed8` |
| 3 | tmpfs | 60.51 | 59.887 / 63.296 | 1500 | 327 | `2099bbe5231fa8900048997d5ed4c736a116453f95d862e2669b4a175a9daf33` |
| 3 | syscall | 30.21 | 59.400 / 62.322 | 1500 | 327 | `35d010696d7a34f3d891549016f2a67248c4cd560d88b23d5c9900e92e62e8e2` |
| 3 | tos | 120.98 | 59.887 / 64.757 | 1500 | 327 | `fa76ef9a073e121ae87b28782fa6c9d9390c4df15fdc2a88de8f8c6d59a345ce` |

三会话共 4,905 份 GCDA（按段计），每段 327 份。每份原始 tar 在主机保留，索引记录路径、大小、SHA。SDB 恢复仅对 RPi4 执行 disconnect/connect，共享服务重启次数为 0。 [训练证据与 tar 索引](evidence/31-k2b/index.json)

## GCOV profile 与函数级对照

用 Clang 22.1.8 对应的 `llvm-cov gcov` 配对 GCDA/GCNO，读取函数入口和基本块计数。每段的 327 份 GCDA 均通过版本和编译单元校验，其中 4 份对应不含函数记录的编译单元。按唯一 ELF 链接名、DWARF 声明源路径和起始行映射 K-BASE。16,777 个插桩名称中 8,051 个匹配（47.99%），最终等权合并的 GCOV profile 有 2,151 个正行权重函数。同行多块取最大计数，排除外源文件位置，无内联上下文和 FS discriminator。 [质量与排除原因](evidence/31-k2b/profiles/gcov-quality.json) · [K-AFDO-GCOV](evidence/31-k2b/profiles/K-AFDO-GCOV.prof)

GCOV profile SHA-256 为 `23693afab064fa7ebac233346446db7a647627c3c24f3bfb7b84dc3a90c02fa9`。Spearman 用入口执行次数与 IP/R1 各叶函数的行权重比较。匹配全集保留零值，同权重用平均秩。前 30 取正权重，同权重按函数名排序。GCOV 反映执行频度，IP 反映周期权重。 [完整排名和可见子集对照](evidence/31-k2b/profiles/rank-comparison.json)

| 负载 | 匹配集合 n | IP ρ | R1 ρ | IP top 30 重合 | R1 top 30 重合 |
| --- | ---: | ---: | ---: | ---: | ---: |
| pipe | 8,051 | +0.483 | +0.483 | 13/30 | 13/30 |
| mmfault | 8,051 | +0.512 | +0.515 | 11/30 | 12/30 |
| tmpfs | 8,051 | +0.632 | +0.635 | 10/30 | 10/30 |
| syscall | 8,051 | +0.412 | +0.413 | 14/30 | 13/30 |
| tos | 8,051 | +0.584 | +0.584 | 9/30 | 8/30 |
| all | 8,051 | +0.673 | +0.675 | 10/30 | 10/30 |

pipe 的前 30 重合仍为 13/30。匹配全集的 ρ 变化 -0.0003，只保留两侧任一权重非零时为 -0.0084。这次计数对照未显示 R1 改善 pipe 排名。

pipe 的 GCOV 前十入口依次为 `arch_local_irq_restore`、`arch_local_irq_save`、`_raw_spin_unlock_irqrestore`、`_raw_spin_lock_irqsave`、`entity_eligible`、`update_curr`、`__cond_resched`、`page_address`、`__update_load_avg_cfs_rq`、`update_cfs_rq_load_avg`。

## 混合候选与收尾

混合候选按外层函数分区，对具有已核对 GCOV 映射和可用行计数的外层函数用 GCOV 替换，按覆盖集合的 R1 行权重总和与原始 GCOV 行计数总和之比 `632013/62571612853` 缩放，取最近整数。若一个有正计数的函数所有行均被取整为零，则在最高原始计数的行保留 1 个样本，并列时取最小行偏移。采用 2,151 个 GCOV 外层函数，零计数覆盖了 10 个原 R1 外层函数。保留其余 846 个 R1 外层函数及其内联上下文，1,384 个 GCOV 外层函数通过单样本下限保留。缩放后 GCOV 行权重合计 631,991，原覆盖集合的 R1 权重为 632,013。保留 FS discriminator 标记供 R1 上下文消费，GCOV 行的 discriminator 为 0。SHA-256 为 `f66c39f3772765d5c5f618c5d1c29f334873fbfba31b9b4efe0e12e759e745f3`。 [混合质量](evidence/31-k2b/profiles/hybrid-quality.json) · [K-AFDO-HYB](evidence/31-k2b/profiles/K-AFDO-HYB.prof)

最终已核对 PLAT build-id `395733b9c917cb98309b39cc3ec379c03ac36b3f`、原始 cmdline、U-Boot、tryboot=0 和 UID 5001。boot_a 的原有 413 个文件 SHA 未变，tryboot.txt 已恢复指向 K-BASE。保留 `cmdline-afdo.txt`, `initramfs-afdo.gz`, `tryboot.txt`, `zImage-kbase`, `zImage-kgcov`。boot_a 最终剩余 4,997,120 B。p6 保持只读，三套模块树文件类型与 SHA 均通过核对。 [最终身份](evidence/31-k2b/final-plat/plat.json) · [最终 boot_a 清单](evidence/31-k2b/finish/boot-after.sha256)

两份候选只做了格式、匹配、合并与读回核对。真实内核消费、吞吐、机制计数及尺寸影响待 PM 决定是否进入 K2c。主机转换的墙钟、CPU 时间和峰值 RSS 随收据归档。 [转换资源](evidence/31-k2b/host-conversion.time)
