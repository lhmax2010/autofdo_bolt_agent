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

## 2026-11-21 续跑：八小时窗口到期，磁盘门禁阻塞

本轮按 13:00–21:00 PST（21:00–次日 05:00 UTC）的新授权窗口执行。仍用原 `continuation/job.json`、原 `formal-attempt-01` 输出和 `--stop-after afdo-audit`。**2026-11-22 05:00:00 UTC 退出 2，原文为 `host startup gate timed out`。停在 S1 之前的主机启动门禁，未达到 afdo-audit。** 不是上一轮外部 GBS 互斥超时的重复结论。[本轮索引](evidence/m2a-resume-20261121/index.json) · [退出记录](evidence/m2a-resume-20261121/end-v2.txt) · [执行原文](evidence/m2a-resume-20261121/run-v2.log)

### 状态、原收据与固定快照

- 当前独立 worktree 开始时干净，从 `9a32faa41f66311127a4f4f47ba1a3ee4f92390a` fast-forward 到 GitHub main `e25f693fa8c111ff480e8d3e964de145ecbd2e6b`，确认原提交为祖先；提交前再 rebase 到 `2b506b1`，新增内容为内核轨道文档，未改 runner。只使用此 worktree 的索引。[开始状态](evidence/m2a-resume-20261121/git-start.json) · [锁检查](evidence/m2a-resume-20261121/git-lock-pre-final-rebase.json) · [收尾 rebase](evidence/m2a-resume-20261121/final-rebase.txt)
- 全部 runner **186 项测试通过**。首次调用遗漏 PYTHONPATH，随后完整测试暴露独立 worktree 缺少历史 M1 temp 夹具路径；在本 worktree 的 temp 内建立指向 WORKDIR 既有夹具的链接后，完整重跑通过。两份失败输出均保留；没有修改测试或 runner 判据。[最终测试](evidence/m2a-resume-20261121/workflow-tests-final.log)
- 只读核验 `.25:26101`：设备树 Raspberry Pi 5 Model B Rev 1.1、aarch64、内核 `6.12.80-arm64-rpi4-v8`、TZ_BUILD_ID `tizen-unified-toolchain_20261118.083201`、UID 5001。镜像 ID 取自 `/etc/tizen-build.conf`；未以 SDB 别名判板。[设备树](evidence/m2a-resume-20261121/board-identity-connected.txt) · [镜像与初态](evidence/m2a-resume-20261121/board-build-identity.txt)
- S0 收据链的 **44 项输入、12 项输出**逐项 SHA 通过，未重跑 S0。原 formal 的 **579 个文件、199,861 B**另存于 `WORKDIR/temp/m2a-resume-20261121/original-formal/`；最终复核 579/579 未改变，原成功和失败收据均未覆盖。四项同发布主机工具 SHA 也通过。[S0 核验](evidence/m2a-resume-20261121/s0-verification.json) · [原文件清单](evidence/m2a-resume-20261121/original-formal-manifest.json) · [最终复核](evidence/m2a-resume-20261121/original-formal-final-verification.json) · [主机工具](evidence/m2a-resume-20261121/host-tools-recheck.json)
- Base `20261030.120529`、Unified `20261104.125239` 的共享 repomd 和 primary 均返回 HTTP 200，primary SHA 与 repomd 声明一致；四份文件与上一轮准备材料逐字节一致。本轮未重新选择 snapshot。[可访问性](evidence/m2a-resume-20261121/snapshot-recheck.json) · [字节比较](evidence/m2a-resume-20261121/snapshot-byte-comparison.json)

### 等待、锁策略与受控适配

正式资源采样始于 13:06:37 PST，结束于 21:00:00 PST，跨度 **28,402.563 秒（473.376 分钟）**；八小时授权从 13:00 开始计算，准备和监督进程调整均未顺延截止。共 **49 次探测**，常规相邻间隔 600.011–600.106 秒，最后一次因绝对截止提前至 199.912 秒。界面心跳只读取已保存的结果，不增加门禁采样。49/49 磁盘失败，内存、负载失败均 0，外部 GBS/rpmbuild 非空记录 0。[逐项汇总及原始记录路径](evidence/m2a-resume-20261121/wait-summary.json)

| 启动条件 | 本轮正式采样范围 | 结论 |
|---|---|---|
| MemAvailable ≥16 GiB | 23.401–23.606 GiB | 全部通过 |
| load1 <12 | 0–3.6211 | 全部通过 |
| 磁盘 ≥50 GiB | 13.416–13.441 GiB | 全部失败，确切阻塞 |
| 其他 gbs/rpmbuild | 每次均为空 | 无外部进程让行事件 |

新增规则通过本轮进程注入的 [launch.py](evidence/m2a-resume-20261121/launch.py) 实现，原 job 和 S0 绑定的实现文件保持原字节。GBS 包装器在调用原执行器前获取 `WORKDIR/temp/host-gbs.lock`，锁内写 workflow、阶段、PID、开始时间，整个执行器期间持锁；进程扫描保留 PID、用户、启动时间、cwd、脱敏 argv 和读取失败原因；无其他构建时再核资源，等待只到绝对截止。原执行器的 -j2、threads 1、6G/5G、200%、nice 19、ionice idle 和运行中保护不改。已有失败收据采用新文件名保存后续失败，避免覆盖历史。

**本轮在更早的主机启动门禁即阻塞，没有实际调用 GBS 包装器，没有获取真实 host-gbs.lock，也没有构建锁需要释放。** 锁持有/释放与阈值、脱敏、剩余期限传播仅通过隔离的合成检查；不称真实 GBS 验证通过。[适配检查](evidence/m2a-resume-20261121/adapter-checks.txt)

等待期间审查发现第一版适配器在绝对截止抛异常会跳过末次探测归档。保留 [第一版](evidence/m2a-resume-20261121/launch-v1.py) 和前九次记录后，仅停止本轮第一监督服务，改为返回“不准启动”，由原等待器先保存 `timed_out` 及末次探测再退出。旧版缺记录、新版完整记录的回归检查通过；第二监督服务沿用下一次原定采样时间，间隔与截止不变。原 runner 未修补，新增启动适配修正一次。[回归](evidence/m2a-resume-20261121/deadline-regression.txt) · [第一服务停止](evidence/m2a-resume-20261121/supervisor-v1-stop.txt) · [原件再核验](evidence/m2a-resume-20261121/original-formal-recheck-v2.json)

### 未到达项目与恢复状态

| 要求 | 本轮结果 |
|---|---|
| S1 依赖解析并集、冻结仓库、BASE 构建及身份审计 | 未启动；没有新增冻结仓库或 BASE 产物 |
| perf/库部署、板上 SHA/ldd、FFmpeg DT_NEEDED/SONAME 与版本差异 | 未到达；不把历史 S0 部署检查当作本轮重新部署结果 |
| BASE/PLAT 身份与非计时 oracle | 未执行 |
| BBB 720p CPU3 R=3、cycles -c1000003、evlist/LOST/样本 | 未采集 |
| 同发布 profgen max/none/none/none、profile 质量 | 工具 SHA 通过；未转换，无新 profile 或质量结果 |
| BASE-r/AFDO、构建锁、两目标 AppliedSamples、候选 oracle | 未执行；AppliedSamples 未知，不记作 0 |
| 配对测量 | 未开始 |

结束后只读复核身份未变、UID **5001**、governor **schedutil**、RPM **1230**、`/opt/afdo_agent` 不存在、cleanup_pending 为空。本轮没有进入板上写入会话，故无本轮部署或 governor/root 改动需要撤销；原 S0 可在未来恢复前重新校验。监督服务 MainPID=0、退出 2；最终 MemoryPeak 未保留，不能报告全程峰值。没有停止外部进程、重启板子、安装 RPM、操作其他板/Gerrit/hq 或修改认证。[板上终态](evidence/m2a-resume-20261121/board-poststop.txt) · [清理日志](evidence/m2a-resume-20261121/cleanup-poststop.json) · [监督服务终态](evidence/m2a-resume-20261121/supervisor-final.txt)

### 边界例外

首次只读 SDB 命令返回目标未找到，并打印 `Server is not running` 与自动启动成功；不是显式执行服务重启。随后仅 `sdb connect 192.168.108.25:26101` 恢复成功。此副作用不能写作“未启动 SDB 服务”。daemon PID 158650 的 stdout/stderr 指向 **`/tmp/sdb.log`**，未读取其内容、删除或改动服务；本轮没有事前/事后完整主机文件审计，无法确认此前遗留全集。[首次原文](evidence/m2a-resume-20261121/board-identity-initial.txt) · [目标连接](evidence/m2a-resume-20261121/sdb-connect.txt) · [描述符核查](evidence/m2a-resume-20261121/sdb-boundary.json)

systemd-run 自动生成的运行时 unit 路径为 **`/run/user/1000/systemd/transient/m2a-resume-20261121-v2.service`**，并可能写系统 journal；这属于采用系统监督器的外部运行时产物，具体 journal 文件未跟踪。SDB 日志由客户端自动启动行为产生；预先确认 daemon 状态可以避免意外触发启动，但本轮首次调用前未做该检查。项目输入、临时材料与证据均留在 WORKDIR，未安装软件或清理其他任务数据。

## 2026-11-23 续跑：清理后核验并从 S1 恢复

### 开工核对

- 独立 worktree `temp/m2a-rpi5-wt` 已 rebase 到 `cc526ab`，含磁盘清理提交 `8ff3613d` 与 M2a runner 提交 `9a32faa4`。186 项 workflow 测试通过。原 job 与 S0 绑定的 runner 文件保持原字节。 [Git 核对](evidence/m2a-resume-20261123/git-start.txt) · [测试日志](evidence/m2a-resume-20261123/workflow-tests.log)
- 116 项 SHA 核对通过，含 S0 收据的 44 项输入、12 项输出、发布版 profgen/profdata 与加载器的依赖闭包、磁盘清理记录所列 13 个原件及其保全副本。Base `20261030.120529`、Unified `20261104.125239` 的 aarch64 repomd 与 primary 均重新取得 HTTP 200，内容与先前本地记录按 SHA 一致。 [SHA 核验](evidence/m2a-resume-20261123/post-cleanup-sha.json) · [请求及原件索引](evidence/m2a-resume-20261123/index.json)
- RPi5 `192.168.108.25:26101` 确认 Raspberry Pi 5 Model B Rev 1.1、aarch64、内核 `6.12.80-arm64-rpi4-v8`、`TZ_BUILD_ID=tizen-unified-toolchain_20261118.083201`、UID 5001。主机的 SDB 客户端符号链接目标已不存在。把仍在运行的共享守护进程映像按字节复制到 WORKDIR，核对 SHA 与客户端版本 4.2.25。首次客户端返回 target not found，按授权仅对 `.25:26101` 执行 disconnect/connect，重新读取成功。守护进程 PID 276783 保留。 [身份与客户端证据](evidence/m2a-resume-20261123/index.json)
- 正式流程验收了板上 perf 6.12.80 与 libLLVM 的逐项 SHA 和 `ldd`，复用原 S0 收据。开跑前另存原 formal 的 583 个文件及其 SHA，以保留后续会更新的状态文件。 [部署闭包](evidence/m2a-resume-20261123/board-runtime.json) · [运行原件索引](evidence/m2a-resume-20261123/index.json)

### 共享锁与资源

本轮在原 CLI 外用一次性启动适配器接入 `temp/host-gbs.lock`。每次 GBS（含依赖解析）在持锁后扫描全主机 gbs/rpmbuild，并再次取资源读数。每 10 分钟复查，等待累计上限 8 小时，构建执行时间不计入等待预算。启动门槛为 16 GiB、load1 <12、50 GiB，无临时豁免。原执行器使用 `-j2`、`--threads 1`、6G/5G/200%、nice 19 与 ionice idle，并保留运行中保护。失败收据沿用新文件名。 [启动适配器](evidence/m2a-resume-20261123/launch.py) · [合成检查](evidence/m2a-resume-20261123/adapter-checks.txt)

| 构建 | 启动内存（GiB） | load1 | 可用磁盘（GiB） | 等待（秒） | 构建（秒） | cgroup 峰值（GiB） |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 在线依赖解析 | 17.70 | 5.03 | 385.59 | 0.159 | 414.04 | 2.168 |
| 离线 BASE | 19.51 | 3.67 | 382.77 | 0.480 | 286.74 | 1.929 |
| 离线 BASE-r（首次） | 19.74 | 1.29 | 380.36 | 0.159 | 146.15 | 2.187 |
| 离线 AFDO（首次） | 19.74 | 2.78 | 378.59 | 0.142 | 151.39 | 2.124 |
| 离线 BASE-r（恢复） | 19.74 | 1.54 | 376.65 | 0.100 | 147.14 | 1.938 |
| 离线 AFDO（恢复） | 19.51 | 3.24 | 374.41 | 0.125 | 152.36 | 2.125 |

六次 GBS 启动时均无其他 gbs/rpmbuild，全部退出 0，构建结束后均释放共享锁。累计就绪与锁等待 1.335 秒，最低主机 MemAvailable 17.60 GiB，最高 cgroup memory.peak 2.187 GiB。首次 CLI 22:29:36–22:56:50 PST。恢复 CLI 22:58:46–23:09:45 PST，从第一次启动到最终退出共 40 分 09 秒。 [锁与资源收据](evidence/m2a-resume-20261123/build-resource-summary.json) · [等待记录](evidence/m2a-resume-20261123/wait-budget.jsonl)

### S1–S4：冻结、构建、兼容性与训练

- BASE 和 AFDO 展开的 BuildRequires 均为 `clang`。依赖解析 GBS 成功，固定源解析出 109 个 RPM，冻结归档逐包复核 109/109，实际 Clang 22.1.8-4.1。仓库 ID 为 `0e5493096bdadc96b4ea1ed61bbbb8cef41283d679664823a4350a04ecc81cd0`。离线 BASE、BASE-r 与 AFDO 的安装包/头摘要同解析构建完全相等。 [冻结核验](evidence/m2a-resume-20261123/frozen-verification.json) · [RPM 清单](evidence/m2a-resume-20261123/frozen-manifest.json)
- BASE 产出 22 个二进制 RPM。两个目标库的运行文件与 debuginfo 的 SHA-1 build-id 均相等。部署 6 个 DSO 的 8 个不同 DT_NEEDED，在板上均有匹配 SONAME。runner 的 `rpm --root` 默认查到了错误的数据库位置，主机构建侧的版本字段为空。对 glibc 使用构建 chroot 的 `var/lib/rpm`，对 FFmpeg 使用实际产出 RPM 复查，8 项版本完全相同（glibc 2.40-2.5，FFmpeg 8.0.1-1，均 aarch64）。 [ELF/RPM 清单](evidence/m2a-resume-20261123/stage-summary.json) · [逐项查证](evidence/m2a-resume-20261123/soname-version-recheck.json)
- 三个输入的 PLAT 与 BASE oracle 一致。BBB 三次训练均使用 CPU3、硬件 cycles、周期 1,000,003；解码进程 maps、DSO SHA 与 perf build-id 核验通过，三次独立的训练后正确性也通过。导出有 0 条 `PERF_RECORD_LOST`，报告对丢失事件的完整性仍标记为 unknown。 [evlist、build-id 与原件 SHA](evidence/m2a-resume-20261123/profile-quality-summary.json)

| 训练 | 输入样本 | libavcodec 目标 / 可用 | libavutil 目标 / 可用 | 导出 LOST 记录 |
| --- | ---: | ---: | ---: | ---: |
| 1 | 33,948 | 26,850 / 14,530 | 153 / 104 | 0 |
| 2 | 33,552 | 26,654 / 14,421 | 139 / 85 | 0 |
| 3 | 33,959 | 26,921 / 14,582 | 167 / 100 | 0 |

六次转换均用 SHA-256 `67ad21faba787d276a80673c1f324f7c0591d28d76bd37a8bd57de0d86426be6` 的发布版工具与显式 `max/none/none/none`，退出 0，`conversion=ok`、`identity=verified`。可选质量阈值字段为 `not_evaluated`。按 DSO 合并并检查跨 DSO 顶层键，交集为空。最终锁定 profile SHA-256 为 `db4d4c196cde3afb20803580ed5317d83a7d4a95f0d8f830c5394f1536b99d5a`。六份训练转换按 Q.5 第 17 项格式记载。 [质量摘要](evidence/m2a-resume-20261123/profile-quality-summary.json) · [profile 披露](evidence/m2a-resume-20261123/Q5-17.json)

### S5：故障、恢复与审计

第一次 BASE-r、AFDO 构建及 build-lock 核对通过，消费取证以 `unclassified recorded command` 退出 2。原版 AArch64 配置查找 `usr/lib/gcc`，冻结 RPM 实际安装在 `usr/lib64/gcc`。用首轮 AFDO 原件复现失败，随后对后者的 `crtbeginS.o`、`crtendS.o`、`libgcc.a`、`libgcc_eh.a` 核对 RPM 属主、SHA 及 `.GCC.command.line`，5 条非源码记录全部精确匹配。仅在 S5 执行期覆盖该路径，以保留已封存配置的字节和原收据。build-lock 保留全部记录，消费分类及门槛维持原实现。保留第一次失败原件与退出状态。 [失败原文](evidence/m2a-resume-20261123/audit-initial-failure.json) · [真实回归](evidence/m2a-resume-20261123/gcc-support-path-regression.json) · [原构建离线验收](evidence/m2a-resume-20261123/original-afdo-offline-consumption.json) · [S5 恢复适配器](evidence/m2a-resume-20261123/recover-s5.py)

恢复时逐项复验 S0–S4 及其 SHA，原训练、转换及锁定 profile 均复用，重跑 S5。BASE-r 的两套运行与 debuginfo 字节均与 BASE 相同，选 BASE 作对照。BASE-r、AFDO 的构建锁比较均为零差异。捕获并保留 libavcodec 297 条、libavutil 99 条记录，消费门禁逐源码命令核对 295/96 条。构建根内 profile SHA 与锁定值一致，两目标的 `.text` 均改变。 [构建锁](evidence/m2a-resume-20261123/buildlock.json) · [消费来源](evidence/m2a-resume-20261123/consumption-command-provenance.json)

| 目标 | BASE / BASE-r build-id | AFDO build-id | 正值 AppliedSamples |
| --- | --- | --- | ---: |
| libavcodec | `bcffda65a8d40cb94d9be2742cedd00adc5e0c8f` | `d3a522590c585393b0eb34674c14f43880d3b422` | 1,804 |
| libavutil | `873ad239a13b3eb4a6db24e82cc7fe37df81dd24` | `249aea67f6fa9f0689bc85a9c98c46049637d39d` | 63 |

表内 build-id 均为运行文件与 debuginfo 成对验证后的值。对照及 AFDO 在三份视频上的非计时 oracle 全部与 PLAT 一致，变体加载库路径和 SHA 检查通过。S5 收据封存后，`--stop-after afdo-audit` 退出 0，未创建测量或计时报告收据，配对测量等待 PM 审核。 [审计与 oracle](evidence/m2a-resume-20261123/stage-summary.json) · [消费收据](evidence/m2a-resume-20261123/consumption.json) · [全链复验](evidence/m2a-resume-20261123/run-verification.json)

### 清理与留档

结束时板上 UID 5001、`schedutil`、RPM 数 1230，与开始一致。部署目录已清理，cleanup_pending 为空，监督单元已结束。原 formal 的 583 个文件保留，577 个字节不变，6 个更新的状态及诊断文件均保留旧版副本。收尾同步到 `93be07b`，用独立 worktree 提交报告。 [板上终态](evidence/m2a-resume-20261123/board-poststop.txt) · [证据索引及原件 SHA](evidence/m2a-resume-20261123/index.json)

本轮只操作 RPi5 `.25:26101`，未重启板子或主机 SDB 服务。边界例外为共享 SDB 进程原有的 `/tmp/sdb.log` 日志句柄，未读取日志内容。通过 procfs 取用该进程的客户端映像作为缺失主机工具的字节副本，存于 WORKDIR。GBS 日志显示跨架构的 QEMU binfmt 注册步骤，宿主机级系统写入未做全量审计。SONAME 的 RPM 查询路径和 GCC 支持对象路径分别以本轮补查及 S5 适配器处理，封存 runner 配置未改。 [SDB 边界记录](evidence/m2a-resume-20261123/sdb-boundary.json) · [原始构建日志](evidence/m2a-resume-20261123/resolution-build.log)
