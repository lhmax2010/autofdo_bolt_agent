# K2c K-AFDO-GCOV 阶段报告

**阶段状态 complete。** pipe 为预登记主比较。 [证据索引](evidence/32-k2c-gcov/index.json)

## 构建与门禁

封存 profile SHA-256 为 23693afab064fa7ebac233346446db7a647627c3c24f3bfb7b84dc3a90c02fa9。源码为 K-BASE 加 0008，tip 3a2602c3e12c11c4bf32f2415b02fdf8fe1ee75a。armv7l GBS 使用 K1a 冻结的 130 个 RPM 的本地 RPM-MD、-j2、固定 KBUILD 身份与 -kbase。重型主机步骤持独占锁，启动要求可用内存 ≥16 GiB、I/O full avg60 <20%，构建单元内存上限 6 GiB、CPU 配额 200%、禁用 swap、nice 19 和 idle I/O。 [构建收据](evidence/32-k2c-gcov/logs/result.json)

GCOV 开工准备期间的两次 I/O 门禁等待曾释放独占锁，等待期间没有 GBS 编译。复查通过并重新取锁后才实际启动 GBS，构建期间持锁。 [开工读数](evidence/32-k2c-gcov/logs/admission.jsonl)

GBS 退出码 0，墙钟 4179.5 秒，cgroup 峰值内存 5.00 GiB。

逐对象编译命令只增加 profile 参数。release、版本串、14,130 个 Module.symvers 条目、52 个模块 vermagic 均一致。实际 build-id f620ed046dcec1b10f2733ce10db9f715379433c，zImage SHA-256 f0cbc05b553bb16df1d78e03716c3514a97c53c6bd154852280526923df6f464。 [构建核对](evidence/32-k2c-gcov/artifacts/variant-verification.json)

在前 20 个热 C 函数的诊断重放中，20 个出现正值 AppliedSamples，9/9 个对应对象的 .text 哈希变化。热区 334,492 B，冷区 184,528 B，159 个对象带 call-graph profile。共同文本输入节 2,894 项中 2,890 项位置改变，map 重放 build-id 与原件一致。 [消费证据](evidence/32-k2c-gcov/artifacts/arm-rpi4/consumption/results.json) · [节布局](evidence/32-k2c-gcov/artifacts/arm-rpi4/layout.json)

| 变体 | .text B | .rodata B | .data B | .bss B | 文本对齐余量 B | 2 MiB 档位 | zImage B |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| K-BASE | 20,049,052 | 5,158,333 | 1,874,160 | 592,080 | 922,468 | 20 | 14,965,104 |
| K-AFDO-GCOV | 20,143,444 | 5,106,909 | 1,874,160 | 592,272 | 828,076 | 20 | 14,973,432 |

2026-11-27T00:45:17.312808-08:00 在第 5 个已验收正式 block 和第 6 个 block 之间切换到共享锁。切换时已回到 PLAT，前后主机构建进程数为 0 和 0。原已验收配对和预登记均沿用。后续部署与测量持共享锁，GBS 和重型主机核验继续持独占锁。 [切换收据](evidence/32-k2c-gcov/lock-handover.jsonl)

第 9 组第二次尝试检测到了 VS Code Insiders 进程组内的 rpmbuild -bb。该进程在本实验持共享锁的期间出现。保留整组失败记录，重试继续沿用主机构建活动检查。 [进程收据](evidence/32-k2c-gcov/host-overlap-observer.jsonl)

## 首启验收

63.83 秒恢复首条 SDB 命令。身份、规范化 FDT、cmdline、模块 10/10、HDMI、日志、D-Bus、安静门禁、PMU 和三项冒烟均通过。首启安静门禁温度 55.991°C，部署后 boot_a 空闲 1,431,552 B。 [首启证据](evidence/32-k2c-gcov/board/afdo-first.json)

## 正式比较

有效 10/10 个 block。AB/BA 种子 20261126，配对 log 比和 20,000 次 block bootstrap，ε=1%。效应为耗时变化，负值表示更快。布局列是单一随机布局的量级参照。 [预登记](evidence/32-k2c-gcov/board/preregistration.json) · [统计](evidence/32-k2c-gcov/board/formal-analysis.json)

| 基准 | 本轮 | bootstrap 95% CI | t 95% CI | 判定 | K1f-3 K-AFDO | K1f-2 布局 | 标记轮 BASE/候选 |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: |
| pipe | -7.027% | -7.223% 至 -6.854% | -7.252% 至 -6.802% | 更快 | -0.077% | +1.453% | 0/0 |
| mmfault | -1.288% | -1.737% 至 -0.804% | -1.857% 至 -0.717% | 不确定 | -1.984% | +0.270% | 0/0 |
| tmpfs | -1.688% | -2.496% 至 -0.904% | -2.654% 至 -0.712% | 不确定 | -1.434% | +0.498% | 0/0 |
| syscall | -1.619% | -1.812% 至 -1.416% | -1.861% 至 -1.377% | 更快 | -1.562% | -0.740% | 0/0 |
| forkexec | -3.168% | -3.564% 至 -2.768% | -3.662% 至 -2.673% | 更快 | +0.114% | +0.499% | 0/0 |
| tos | -0.040% | -0.288% 至 +0.191% | -0.337% 至 +0.258% | 等价 | -0.274% | +0.086% | 0/1 |

forkexec 的 A/A 偏差为 +0.462%，bootstrap 95% CI +0.158% 至 +0.807%。

| 内存项 | K-BASE 中位 KiB | 候选中位 KiB | 配对差中位 KiB | 最小至最大 KiB |
| --- | ---: | ---: | ---: | ---: |
| MemTotal | 3976472.0 | 3976472.0 | +0.0 | +0 至 +0 |
| MemFree | 3402474.0 | 3378206.0 | -20856.0 | -151184 至 +115368 |
| MemAvailable | 3473490.0 | 3452216.0 | -18072.0 | -54880 至 +24672 |
| Slab | 50850.0 | 50974.0 | +202.0 | -1096 至 +1888 |
| KernelStack | 3540.0 | 3556.0 | +24.0 | -104 至 +72 |
| PageTables | 5396.0 | 5410.0 | +88.0 | -244 至 +212 |

## 机制计数

有效 3 个只计数 block，仅计 CPU3。 [逐 block 计数](evidence/32-k2c-gcov/board/mechanism-analysis.json)

| 负载 | 事件 | 配对几何变化 | 配对计数差中位 | 最低运行比 |
| --- | --- | ---: | ---: | ---: |
| pipe | cycles:k | -5.316% | -927905162 | 100.0% |
| pipe | instructions:k | -5.817% | -511875996 | 100.0% |
| pipe | r01 | -23.594% | -53017453 | 100.0% |
| pipe | r02 | -28.318% | -10766150 | 100.0% |
| pipe | r10 | -27.689% | -7576369 | 100.0% |
| mmfault | cycles:k | -1.472% | -177470322 | 100.0% |
| mmfault | instructions:k | -5.736% | -333712542 | 100.0% |
| mmfault | r01 | -74.374% | -24778406 | 100.0% |
| mmfault | r02 | -34.198% | -11701203 | 100.0% |
| mmfault | r10 | +32.392% | +1926204 | 100.0% |

## 运行条件

已接受启动 26 次。PLAT 发令温度最小／中位／最大为 55.99、58.43、59.40 °C，安静等待 30.29、75.95、91.13 秒。窗口起跑温度 54.04、57.94、59.89 °C，窗口最高温度 57.45、60.37、63.30 °C，冷却等待 4.09、4.10、18.25 秒。计划固定频率 [1500000] kHz，计时遥测频率最小／中位／最大 1500000.00、1500000.00、1500000.00 kHz，rsts 分布 {'0x20': 26}。tryboot 到首条 SDB 命令 57.68、58.87、68.89 秒，共享 SDB 重启次数 0。

技术失败及重试 {'host_build_overlap': 4}。已接受 block 的构建活动见共享锁收据。 [终态](evidence/32-k2c-gcov/board/terminal.json)

阶段结束回到原 PLAT，UID 5001，tryboot 指向 K-BASE。 [PLAT 身份](evidence/32-k2c-gcov/board/final-owner/plat.json)
