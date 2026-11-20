# M2a RPi5 上板准备与 S0 资源门禁记录

2026-11-19（America/Los_Angeles）。RPi5 身份通过，完成独立只读能力探测与十分钟空闲曲线。**正式流程未启动。** workflow v0.3 §5 S0 引用 §9.4 的主机门禁，准入要求 MemAvailable ≥16 GiB。本轮复查区间为 11.918–13.329 GiB，门禁未过。未沿用 M1 的临时豁免。 [证据索引](evidence/m2a-rpi5-prep-20261119/index.json)

## 身份与板上能力

唯一 SDB 操作目标为 `192.168.108.25:26101`。connect 成功，已从设备树断言 **Raspberry Pi 5 Model B Rev 1.1**，`uname -m=aarch64`。四核 CPU implementer `0x41`、part `0xd0b`、variant `0x4`、revision `1`，对应 Cortex-A76。内核为 `6.12.80-arm64-rpi4-v8 #1 SMP PREEMPT Wed Nov 18 09:57:28 UTC 2026`，其中 release 里的 `rpi4` 字符串保留原文，板型取设备树。TZ_BUILD_ID 为 `tizen-unified-toolchain_20261118.083201`，OS 为 Tizen11.0/Unified，镜像 BUILD_ID 后缀为 `_tizen-headed-aarch64`。身份及后续只读会话均以 UID 5001 执行。

| 观察项 | 结果 |
|---|---|
| 频率 | cpufreq policy0 的 scaling 与 cpuinfo 当前频率可读。首份清单分别为 1700、2400 MHz，cpuinfo 上限 2400 MHz。governor 为 schedutil。 |
| 温度 | thermal_zone0 为 cpu-thermal。hwmon0 为 cpu_thermal，有 temp1_input，hwmon1 为 pwmfan。 |
| 电压、欠压、降频 | `vcgencmd` 不在 PATH，预期 firmware get_throttled 节点不可读，无可读的 hwmon `in*_alarm` 或 `in*_input`。`/sys/class/misc/vcio/dev` 存在，未用其推断固件状态。三项记为 unknown。 |
| PMU | sysfs 列出 `armv8_cortex_a76`。正式 `perf record` + evlist 的 type/config=0 断言尚未执行。 |
| HDMI 和显示栈 | HDMI-A-2 connected，HDMI-A-1 disconnected。尾部复查 HDMI-A-2 为 enabled，存在 root:display 的 /run/wayland-0 socket。UID 5001 可见进程没有匹配到已知 compositor 名称，未确定具体进程。 |
| 板上工具 | 初始 UID 5001 未找到 PATH 内 perf，`/opt/afdo_agent/tools/perf` 与 `/opt/afdo_agent/lib/libLLVM.so.22.1` 均不可读或不存在。未部署，板上动态链接与版本门禁未验收。 |

ID/频率/温度、显示原文及最终状态见 [只读取证](evidence/m2a-rpi5-prep-20261119/transcripts.json)。

## 十分钟空闲曲线

UID 5001 和原 governor schedutil 下，采样器每 10 秒读 uptime、温度、scaling_cur_freq、loadavg，并记录 ps 前五名，未发起 CPU 负载。共有 **61 帧、601.55 秒**。CPU 温度首/末 **34.75 / 35.30°C**，最低/中位/最高 **33.10 / 34.20 / 35.85°C**。scaling_cur_freq 为 **1500–2400 MHz**，1 分钟负载为 **0.00–0.16**。空闲温度在 58°C 冷却目标以下，不能据此给出短负载结束后的冷却时间。短负载、60°C 起跑与 80°C 运行上限门禁未进入，阈值不变。

| 最后一帧 PID | 用户 | %CPU | 进程 |
|---:|---|---:|---|
| 79 | root | 0.1 | `sugov:0` |
| 4643 | owner | 0.0 | `sh` |
| 18 | root | 0.0 | `rcu_preempt` |
| 85 | root | 0.0 | `kworker/0:2-events` |
| 823 | root | 0.0 | `psimon` |

上表 ps %CPU 为进程生命周期平均值，监视命令也可能出现在列表。每帧前五名和测量原文在证据中。[曲线 CSV](evidence/m2a-rpi5-prep-20261119/idle-curve.csv) · [曲线摘要](evidence/m2a-rpi5-prep-20261119/idle-summary.json)

## 主机门禁、工具与上游仓库

首次主机采样时 MemAvailable 为 13.329 GiB。独立 worktree 使用 workflow 的 `build.resources` 和 `build.can_start` 复查，未传入 M1 实验豁免。资源与构建互斥检查如下。早期未观察到 gbs/rpmbuild/gbp，最后两次观察到另一个 gbs 进程。正式 S0 未通过，所以没有进入需要每五分钟复查的 GBS 启动等待阶段，不把本任务记成构建失败。未创建构建 scope 或 buildroot。

| UTC | MemAvailable GiB | load1 | Disk free GiB | 其他构建进程 | S0 |
|---|---:|---:|---:|---|---|
| 2026-11-20T05:27:29+00:00 | 13.173 | 0.723 | 365.82 | 未观察到 | 未通过 |
| 2026-11-20T05:28:29+00:00 | 13.120 | 0.681 | 365.82 | 未观察到 | 未通过 |
| 2026-11-20T05:29:29+00:00 | 12.913 | 0.473 | 365.82 | 未观察到 | 未通过 |
| 2026-11-20T05:30:29+00:00 | 12.007 | 3.600 | 365.82 | 未观察到 | 未通过 |
| 2026-11-20T05:31:29+00:00 | 11.918 | 7.039 | 365.62 | 未观察到 | 未通过 |
| 2026-11-20T05:32:29+00:00 | 11.982 | 7.302 | 365.48 | 未观察到 | 未通过 |
| 2026-11-20T05:33:29+00:00 | 12.303 | 6.590 | 365.34 | 未观察到 | 未通过 |
| 2026-11-20T05:34:29+00:00 | 12.261 | 5.738 | 365.66 | gbs PID 2387461 | 未通过 |
| 2026-11-20T05:35:29+00:00 | 12.045 | 5.832 | 365.50 | gbs PID 2387461 | 未通过 |

GBS 2.1.1，Python 3.12.3。主机发布版 llvm-profgen 的 SHA-256 `67ad21faba787d276a80673c1f324f7c0591d28d76bd37a8bd57de0d86426be6`，与 M1 使用的 f999bd40＋9 补丁交付版相同。llvm-profdata、动态加载器与主机 libLLVM 也均与 M1 锁匹配。用同一加载命令执行 `--version`，profgen 首次 15 秒超时，在第二次只读核对后退出 0，两工具均报告 LLVM 22.1.8。历史 RPi5 perf 及其依赖的主机副本均已重算 SHA，分别为：

- aarch64 perf `d23f11a13d5b0b21fc1957a883eb0025c80f9a26bcde360b7031b4d3b1348949`。
- aarch64 libLLVM.so.22.1 `06b9971c974f113b16ea49c988b6481f20272e70ba36040358735fa6c91af007`。

只检查了与板上镜像同号的 Unified 候选。Tizen Toolchain 的 `packages/aarch64/repodata/repomd.xml` 与 `packages/repodata/repomd.xml` 两个请求均 **HTTP 404**。这只是所查 URL 的结果，未选择替代 snapshot、未配对 Base、未解析/下载依赖或创建冻结仓库。BBB 训练片、ToS 主测片和 Sintel 副测片存在，SHA 与 M1 输入记录一致。 [工具锁](evidence/m2a-rpi5-prep-20261119/host-tool-locks.json) · [媒体 SHA](evidence/m2a-rpi5-prep-20261119/host-media-sha.json)

## 阶段状态与 M1 差异

| 项目 | 本轮状态 |
|---|---|
| S0 | 身份通过，保存只读遥测。16 GiB 主机资源门禁未通过。短负载冷却、板上 perf 依赖与 hardware cycles 未到达。 |
| S1 BASE 和离线冻结 | 未开始。没有依赖并集、RPM、配对 build-id 或编译命令审计结果。 |
| S2 部署及 PLAT/BASE oracle | 未开始。M1 的媒体和阈值沿用，M2a 的 PLAT 输出没有从 M1 推定。 |
| S3 训练 | 未开始。待沿用 BBB 720p、CPU3、R=3、cycles -c1000003，evlist、LOST、样本数据均未生成。 |
| S4 profile 和质量 JSON | 未开始。交付工具已核验，计划继续使用 max/none/none/none，没有生成或打开本次 profile。 |
| S5 BASE-r/AFDO 和候选正确性 | 未开始。没有 build-lock、AppliedSamples 或正确性结果。 |
| S6/S7 | 未启动配对测量或产生性能结论。准备轮指定的停止点仍为 AFDO 审计及正确性完成。 |

通过资源门禁也不能直接把当前 M1 job 指向 RPi5。现有 FFmpeg package 只登记 armv7l Thumb 单元。live runner 仍固定使用 `scratch.armv7l.0`、`usr/lib` 路径和 `thumb` 合并标识，oracle 脚本也硬编码运行时库目录。现有 live `run` 固定继续到 measure，未暴露这次要求的 S5 停止点，且候选 oracle 在 measure 入口才运行。恢复前须按实际 aarch64 RPM 布局接入这些路径，并让收据链在候选正确性后停止。GBS 互斥需检查整个主机而非只依赖 workflow 内部 flock。本轮未改代码、配置或设计。参考 [v0.3](../01_afdo_bolt_workflow_design_v0.3.md) 和 [M1 验收](../m1/05_m1_board_e2e.md)。

## 收尾

只读取证完成。结束身份仍为 Raspberry Pi 5/aarch64、UID 5001、governor schedutil，读取 RPM 计数 1230，SDB 仍为 device。明确验证 /opt/afdo_agent、perf 和板上 libLLVM 路径均不存在。 未切 root、未变更 governor、未写板上目录、未安装 RPM、未重启或触碰其他目标。未启动 GBS、未改 Gerrit/hq。SDB 和系统工具内部日志写入未做全机审计。结果归档在独立 worktree。
