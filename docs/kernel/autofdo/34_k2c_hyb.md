# K2c K-AFDO-HYB 阶段报告

**阶段状态 complete。** pipe 为预登记主比较。 [证据索引](evidence/34-k2c-hyb/index.json)

## 构建与门禁

封存 profile SHA-256 为 f66c39f3772765d5c5f618c5d1c29f334873fbfba31b9b4efe0e12e759e745f3。源码为 K-BASE 加 0008，tip 3a2602c3e12c11c4bf32f2415b02fdf8fe1ee75a。armv7l GBS 使用 K1a 冻结的 130 个 RPM 的本地 RPM-MD、-j2、固定 KBUILD 身份与 -kbase。重型主机步骤持独占锁，启动要求可用内存 ≥16 GiB、I/O full avg60 <20%，构建单元内存上限 6 GiB、CPU 配额 200%、禁用 swap、nice 19 和 idle I/O。 [构建收据](evidence/34-k2c-hyb/logs/result.json)

GBS 退出码 0，墙钟 4114.8 秒，cgroup 峰值内存 5.00 GiB。

逐对象编译命令只增加 profile 参数。release、版本串、14,130 个 Module.symvers 条目、52 个模块 vermagic 均一致。实际 build-id e0709cc1dc6cdc5d101c8d0d52eea8a98ed402fb，zImage SHA-256 26c5227e624a68e63e1262fd3180bff940c76421ca60d9a13bcb0e586bad80de。 [构建核对](evidence/34-k2c-hyb/artifacts/variant-verification.json)

在前 20 个热 C 函数的诊断重放中，20 个出现正值 AppliedSamples，11/11 个对应对象的 .text 哈希变化。热区 619,944 B，冷区 453,496 B，391 个对象带 call-graph profile。共同文本输入节 2,887 项中 2,873 项位置改变，map 重放 build-id 与原件一致。 [消费证据](evidence/34-k2c-hyb/artifacts/arm-rpi4/consumption/results.json) · [节布局](evidence/34-k2c-hyb/artifacts/arm-rpi4/layout.json)

| 变体 | .text B | .rodata B | .data B | .bss B | 文本对齐余量 B | 2 MiB 档位 | zImage B |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| K-BASE | 20,049,052 | 5,158,333 | 1,874,160 | 592,080 | 922,468 | 20 | 14,965,104 |
| K-AFDO-HYB | 20,119,880 | 5,130,373 | 1,874,192 | 590,544 | 851,640 | 20 | 15,038,232 |

## 首启验收

57.67 秒恢复首条 SDB 命令。身份、规范化 FDT、cmdline、模块 10/10、HDMI、日志、D-Bus、安静门禁、PMU 和三项冒烟均通过。首启安静门禁温度 53.556°C，部署后 boot_a 空闲 1,368,064 B。 [首启证据](evidence/34-k2c-hyb/board/afdo-first.json)

## 正式比较

有效 10/10 个 block。AB/BA 种子 20261128，配对 log 比和 20,000 次 block bootstrap，ε=1%。效应为耗时变化，负值表示更快。布局列是单一随机布局的量级参照。 [预登记](evidence/34-k2c-hyb/board/preregistration.json) · [统计](evidence/34-k2c-hyb/board/formal-analysis.json)

| 基准 | 本轮 | bootstrap 95% CI | t 95% CI | 判定 | K1f-3 K-AFDO | K1f-2 布局 | 标记轮 BASE/候选 |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: |
| pipe | +0.176% | +0.012% 至 +0.346% | -0.027% 至 +0.379% | 等价 | -0.077% | +1.453% | 0/0 |
| mmfault | +0.048% | -0.476% 至 +0.642% | -0.630% 至 +0.730% | 等价 | -1.984% | +0.270% | 0/0 |
| tmpfs | -0.946% | -1.938% 至 -0.146% | -2.054% 至 +0.174% | 不确定 | -1.434% | +0.498% | 0/0 |
| syscall | +0.863% | +0.723% 至 +1.015% | +0.683% 至 +1.044% | 不确定 | -1.562% | -0.740% | 0/0 |
| forkexec | +1.154% | +0.712% 至 +1.610% | +0.611% 至 +1.700% | 不确定 | +0.114% | +0.499% | 0/0 |
| tos | +0.069% | -0.146% 至 +0.262% | -0.181% 至 +0.320% | 等价 | -0.274% | +0.086% | 0/0 |

forkexec 的 A/A 偏差为 +0.462%，bootstrap 95% CI +0.158% 至 +0.807%。

| 内存项 | K-BASE 中位 KiB | 候选中位 KiB | 配对差中位 KiB | 最小至最大 KiB |
| --- | ---: | ---: | ---: | ---: |
| MemTotal | 3976472.0 | 3976476.0 | +4.0 | +4 至 +4 |
| MemFree | 3309442.0 | 3282868.0 | +1880.0 | -138664 至 +100064 |
| MemAvailable | 3468104.0 | 3445050.0 | -11842.0 | -44148 至 +10360 |
| Slab | 52300.0 | 52186.0 | -270.0 | -1848 至 +1844 |
| KernelStack | 3564.0 | 3572.0 | -16.0 | -104 至 +104 |
| PageTables | 5466.0 | 5562.0 | +56.0 | -288 至 +364 |

## 机制计数

有效 3 个只计数 block，仅计 CPU3。 [逐 block 计数](evidence/34-k2c-hyb/board/mechanism-analysis.json)

| 负载 | 事件 | 配对几何变化 | 配对计数差中位 | 最低运行比 |
| --- | --- | ---: | ---: | ---: |
| pipe | cycles:k | +0.255% | +363875 | 100.0% |
| pipe | instructions:k | -5.271% | -455400117 | 100.0% |
| pipe | r01 | +6.490% | +11958455 | 100.0% |
| pipe | r02 | -27.244% | -10789342 | 100.0% |
| pipe | r10 | -19.030% | -6071809 | 100.0% |
| mmfault | cycles:k | -0.763% | -66960139 | 100.0% |
| mmfault | instructions:k | -5.487% | -320753661 | 100.0% |
| mmfault | r01 | -55.812% | -17792641 | 100.0% |
| mmfault | r02 | -18.044% | -6320582 | 100.0% |
| mmfault | r10 | +76.549% | +4639623 | 100.0% |

## 运行条件

已接受启动 26 次。PLAT 发令温度最小／中位／最大为 54.53、55.50、56.48 °C，安静等待 30.31、45.52、111.46 秒。窗口起跑温度 52.58、54.53、56.48 °C，窗口最高温度 55.02、56.97、59.89 °C，冷却等待 4.09、4.10、4.18 秒。计划固定频率 [1500000] kHz，计时遥测频率最小／中位／最大 1500000.00、1500000.00、1500000.00 kHz，rsts 分布 {'0x20': 26}。tryboot 到首条 SDB 命令 55.62、62.68、63.69 秒，共享 SDB 重启次数 0。

技术失败及重试 {}。已接受 block 的构建活动见共享锁收据。 [终态](evidence/34-k2c-hyb/board/terminal.json)

阶段结束回到原 PLAT，UID 5001，tryboot 指向 K-BASE。 [PLAT 身份](evidence/34-k2c-hyb/board/final-owner/plat.json)
