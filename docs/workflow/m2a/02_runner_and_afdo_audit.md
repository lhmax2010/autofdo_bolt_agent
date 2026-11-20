# M2a RPi5 参数化与 AFDO 审计准备

## Runner 与 M1 回归

- `workflow/platforms/` 存放 RPi4 armv7l（Thumb-2、A32）与 RPi5 aarch64 的架构、库和调试文件布局、perf 部署位置、采样和观察器亲和性、遥测节点。RPi5 的 FFmpeg 配置采用设计 §6 的 `[collect.rpi5]`，BBB 720p、CPU3、三轮、`cycles -c 1000003` 沿用 M1。PLAT 读取系统库，其他变体使用各自目录。
- `run --stop-after afdo-audit` 对应 `rebuild`。RPi5 在写 S5 收据前完成 BASE-r/AFDO 构建锁、消费检查和候选、对照的非计时 oracle。退出时记录停止阶段、收据与清理结果。再次运行时逐个核验已封存的输入、产物、上游收据，再决定是否复用。合成测试覆盖停止点与继续至 S6/S7。M1 统计实现和 v0.3 设计未改动。
- 回放使用 M1 attempt-11 已归档配置和阶段返回值，重建 6 份训练/训练正确性脚本、6 份 PLAT/BASE oracle 脚本、3 个 GBS argv 和工作目录、6 份 profgen argv 和合并键。脚本逐字节一致，GBS argv 只对本次新 buildroot 占位同值处理。用现有调度器重写 S0–S5 收据，比较顶层字段、上游阶段和完整 details。共 48 项比较通过。重放收据的时间戳、验证过的输入和产物 SHA 绑定按回放本身生成；本次主机回放不执行 GBS、板上步骤或 profile 转换。[回放证据](evidence/m2a-runner-20261120/m1-command-replay.json)

## 快照

2026-11-20（America/Los_Angeles）实时获取 Tizen Base 和 Unified 顶层索引，分别发现 9 和 3 个固定 ID。对每个记录 aarch64 包目录与共享 RPM-MD 的 HTTP、长度和 SHA。Base 20261119.042539 晚于板子镜像日期。所选两份 primary 经 repomd 所列 SHA-256 核验，aarch64 包数按元数据的 arch 字段计数。

| 仓库 | 固定 ID | aarch64 包 | clang |
|---|---|---:|---|
| Base | `20261030.120529` | 542 | 22.1.8-4.1，LLVM f999bd40 |
| Unified | `20261104.125239` | 3,107 | 无 clang 包 |

两份均为 M1 使用的固定 ID，符合本轮优先选择规则。各快照的 aarch64 子目录内 `repomd.xml` 返回 404，仓库根下的共享 `repomd.xml` 返回 200。选择依据是共享元数据中确有 aarch64 包。[实时核对与 SHA](evidence/m2a-runner-20261120/snapshots.json) · [Base 固定仓库](https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261030.120529/repos/standard/packages/) · [Unified 固定仓库](https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261104.125239/repos/standard/packages/)

AArch64 补丁后的两个 RPM spec 模式（BASE 与 with_autofdo=1 + afdo_diag=1）各只声明 `clang` 为 BuildRequires，查询均退出 0。解析后的 buildconf 仍负责补齐发行版的构建依赖。源码引自本地 FFmpeg 的 5fe76358596f66e955f005094e6f34ca525ab23d，独立克隆后用与 M1 相同的 profiling.patch，通过了应用前检查。[BASE 查询](evidence/m2a-runner-20261120/buildrequires-base.txt) · [AFDO 查询](evidence/m2a-runner-20261120/buildrequires-afdo.txt)

## RPi5 S0

- `192.168.108.25:26101` 的 SDB 别名仍为 `rpi4`。实际设备树报告 Raspberry Pi 5 Model B Rev 1.1，AArch64，四个 Cortex-A76 核（part `0xd0b`），内核 `6.12.80-arm64-rpi4-v8`，TZ_BUILD_ID `tizen-unified-toolchain_20261118.083201`。[本轮身份](evidence/m2a-runner-20261120/board-identity.json)
- 在清理日志登记后建立部署目录，推送并验证历史 aarch64 perf 与 libLLVM.so.22.1 的锁定 SHA。板上 `ldd` 无缺失，`perf --version` 为 6.12.80。实际计数器试采的 evlist 恰为一个 `cycles` 事件，type=0、config=0。[工具检查](evidence/m2a-runner-20261120/board-runtime.json) · [evlist](evidence/m2a-runner-20261120/cycles.evlist)
- 前轮 10 分钟空闲温度为 33.10–35.85°C，HDMI-A-2 连接。正式 S0 的频率取 policy0 的 scaling/cpuinfo 两项，设置 performance 后均为 2400 MHz。thermal_zone0 可读，电压、欠压和固件降频历史为 unknown。[空闲记录](01_rpi5_preparation.md#十分钟空闲曲线) · [S0 收据内容](evidence/m2a-runner-20261120/s0.json)
- CPU3 短负载约 20 秒。负载前 39.15°C，负载返回后的首个读数 40.80°C，首个复查约 0.24 秒，已满足 ≤58°C，未进入额外冷却等待。从这些离散读数不能确定负载期间峰值。[冷却记录](evidence/m2a-runner-20261120/cooldown.json)

## 主机资源与本轮停止点

正式 S0 的主机门禁通过。启动依赖解析构建前，从 00:11:22 PST 开始执行互斥与资源检查，等待约 **180.00 分钟**，共记录 **19 次**。门槛为 MemAvailable ≥16 GiB、load1 <12（20 核 × 0.6）、磁盘 ≥50 GiB，且无其他 GBS/rpmbuild。M2a 未使用 M1 的临时豁免。等待期间可用内存 **16.40–21.06 GiB**，负载 **1.88–18.75**，磁盘 **272.69–347.41 GiB**。到期仍有 gbs PID 157878, gbs PID 157898。因此触发 `build start gate timeout`，GBS 进程、构建 scope 与 buildroot 均未启动。CLI 退出码 **2**。[逐次复查](evidence/m2a-runner-20261120/build-001-dependency-resolution-resources.json) · [构建门禁收据](evidence/m2a-runner-20261120/build-001-dependency-resolution-result.json) · [命令退出](evidence/m2a-runner-20261120/cli-end.txt)

| 项目 | 本轮结论 |
|---|---|
| S0 板上前置 | 通过，收据已封存 |
| S1 依赖并集、冻结、BASE 构建与审计 | aarch64 两模式的 BuildRequires 一致；实际依赖下载、冻结、BASE RPM 和 build-id 核对因启动门禁未执行 |
| S2 BASE 运行依赖、部署、PLAT/BASE oracle | 未到达；没有板上 FFmpeg soname 兼容性结论 |
| S3 训练与 S4 profile | 未到达；无三轮训练、转换或质量结果 |
| S5 BASE-r、AFDO、构建锁、AppliedSamples 和正确性 | 未到达；S5 停止点已通过合成测试 |
| S6/S7 配对测量与报告 | 未启动 |

## 收尾与证据

CLI 执行失败路径清理。板上 UID 恢复至 5001，governor 恢复为 schedutil，RPM 数为 1230，与开始一致，清理待办为空。结束时复核 `/opt/afdo_agent` 不存在。[退出后板上核对](evidence/m2a-runner-20261120/board-poststop.txt) 只操作 RPi5，未重启，也未重启主机 SDB 服务。主机侧测试 186 项通过，板上脚本通过 `bash --posix -n`。SDB 或 systemd 自身的系统日志写入未做主机级审计。[证据索引与 SHA](evidence/m2a-runner-20261120/index.json) · [测试输出](evidence/m2a-runner-20261120/workflow-tests.log)
