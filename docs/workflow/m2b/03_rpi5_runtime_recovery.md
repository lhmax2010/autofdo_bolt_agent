# M2b 阶段 B · RPi5 依赖来源裁决与续跑

## compiler-rt 来源

实时读取 Tizen Base 的 7 个固定快照、Unified 的 2 个固定快照及两仓库的 `latest`、`reference`。13 份仓库查询的 primary 均与对应 repomd SHA-256 一致。Unified 的 4 个查询没有目标架构的 compiler-rt。Base 可用版本均为 22.1.8，release 为 1.6、1.7 或 3.1。两种架构均无与阶段 A 原 RPM 同 SHA 的包，按裁决第二级取最新固定快照 `tizen-base-toolchain_20261119.042539` 的 22.1.8-1.6。[仓库查询、版本与 SHA 证据](evidence/rpi5-runtime-recovery.json)

| 架构 | RPM SHA-256 | 包内静态 runtime | 本轮适用范围 |
| --- | --- | --- | --- |
| aarch64 | `bd8dd2dee4139910cede020736c9eff3b90619bd1e63a724de98b72f4aa875be` | `/usr/lib64/clang/22/lib/linux/libclang_rt.profile-aarch64.a` | PGOGEN 专用，已登记偏差 |
| armv7l | `f8228b43c73a2e0b94cff958525f0d0b4a14631bc1b933345388c01ed2a4e625` | `/usr/lib/clang/22/lib/linux/libclang_rt.profile-arm.a` | 仅核查供 RPi4 后续使用 |

两包的下载字节均匹配 primary SHA。分别从静态归档提取 `InstrProfilingVersionVar.c.o`，用 `readelf -Ws/-SW/-x 3` 对应 `__llvm_profile_raw_version` 的定义与数据，读到 8 字节小端整数 10。锁定编译器 Clang 22.1.8 在两个目标 triple 的 IR 插桩输出都写入 `0x010000000000000a`，其中低 56 位是格式版本 10，高位为 IR 标记。锁定的 llvm-profdata 成功读取一份同版字段的已验证合成 IR profile。此步骤核对格式，真实 ARM 训练输出仍要通过正式转换与身份门禁。

## 冻结集合

M2a 原 109 个 RPM 均重新核对文件 SHA 与 RPM 头 SHA，集合 ID 为 `0e5493096bdadc96b4ea1ed61bbbb8cef41283d679664823a4350a04ecc81cd0`。BASE、BASE-r、AFDO 与 PGO 固定使用该集合。PGOGEN 本地集合 ID 为 `f2e2b76f0a0dd803e448f383438c19168a454ebb864a5adc7f990ee53598181e`，唯一新增上述 aarch64 RPM，已验证其 Requires 可由原集合提供。job 和 PGOGEN manifest 均记录偏差。Runner 核对仓库及安装包头，比较构建锁时只接受这一个已声明依赖差异。实际 `rpmspec` 展开表明只有 PGOGEN 声明 `compiler-rt = 22.1.8-1.6`。正式 GBS 继续使用原有共享锁和启动门槛。

## 快照可用期

| 指定快照 | 最后一次观测到 HTTP 200（PST） | 首次发现 HTTP 404（PST） |
| --- | --- | --- |
| Base 20261030.120529 | 2026-11-25 05:36:25 | 2026-11-25 21:41:21 |
| Unified 20261104.125239 | 2026-11-25 05:36:26 | 2026-11-25 21:42:44 |

移除的准确时间未知。建议 workflow 在 preflight 尽早解析并冻结全部计划变体所需的依赖，归档对应 RPM、元数据 SHA 及构建配置。本轮只记录这项建议。

## 第一次运行与构建锁回放

只操作 `192.168.108.13:26101`。型号、架构、内核、镜像与 M2a 一致，初始 UID 5001、governor schedutil、1230 个 RPM。第一次运行的 preflight、BASE 与 PGOGEN 构建通过，分别按 109/110 个安装包头锁核对。PGOGEN 的两个目标 ELF 均有 profile runtime 定义，归档属主为登记的替代 RPM。审计收据在读取仓库锁字段时以 `KeyError('repo_id')` 停止。该次 GBS 的产物和失败收据保留，清理后 UID、governor 与 RPM 数复原，清理待办为空。

以原构建产物回放修正了仓库锁字段 `frozen_repo_id`。进一步定位到每个 PGOGEN 目标额外带入一条 GNU 编译命令字符串。PGOGEN 的 instrumentation runtime 引用 `atexit`，两个目标 ELF 都有链接后符号。该字符串与 `glibc-devel` 的 `libc_nonshared.a(atexit.oS)` 逐项相同；BASE 和 PGOGEN 两个 chroot 中该归档 SHA 相同，RPM 头属于原 109 包锁。比较只归属这一条已证实的链接来源，并保留完整原始构建锁。两目标各有 11 条已按档案核实的 compiler-rt 命令记录。复算 PGOGEN 相对 BASE，唯一安装包增量为已登记的 compiler-rt，归一化后的其余构建锁差异为 0。

以上两处 runner 修正使用失败原件复算并新增单元测试。最终主机测试 253/253 通过，M1 已封存回放 48/48 通过。代码改动会改变阶段输入 SHA，故另建 attempt 从 S0 复验，保留第一次运行原件，没有改写已发布的 M1 或 M2a 收据。

## 2026-11-26 主机重启与恢复

第二次 attempt 的 S0 收据完整，进入 S1 后等共享锁。最后一条锁检查仍未取得锁，本 attempt 没有 GBS 启动命令、构建日志或退出收据。主机重启使该 attempt 中断。此次崩溃的原因无法由 workflow 收据确定。

以只读身份断言复核同一 RPi5 后，按仍在盘上的清理日志恢复。复核结果为 UID 5001、governor schedutil、RPM 1230、清理待办为空。本次保留旧清理日志的原始副本和恢复收据，未重启共享 SDB 服务。

恢复 attempt 保留 16 GiB、load1 <12、50 GiB 的启动门槛及原 GBS 互斥。新增本次启用的主机保护：运行前先在主机侧等待其他 GBS/rpmbuild 退出，且连续两次相隔 60 秒的主机 I/O PSI full avg60 ≤20%；接板后的每次 GBS 启动也复查该门槛。GBS scope 的 CPUQuota=100%、MemoryHigh=3G、MemoryMax=4G，runner scope 的 CPUQuota=50%、MemoryMax=1G，均以 nice 19 和 ionice idle 运行。连续两次构建监测读到 MemAvailable <8 GiB 或 I/O PSI full avg60 ≥70% 时只停止本任务 scope。用户 cgroup 没有委派 I/O controller，因此 I/O 防护来自空闲优先级与压力门禁，而没有硬带宽限制。默认 workflow 及其他任务的限制不变。

随后按用户临时授权，仅对本次恢复 attempt 解除 I/O PSI 启动和运行中停止判定，保留 PSI 采样、ionice idle、CPU/内存限制、共享锁和内存/磁盘门槛。使用新 job `job-3-io-waiver.json`，未改写原 job。入口两次达标样本的可用内存为 16.54、16.73 GiB，未发现其他 GBS/rpmbuild。I/O PSI full avg60 同时实录 24.58%、22.92%。该授权不继承到其他 job。

## 恢复运行结果

恢复 attempt 于 2026-11-26 01:02:46 PST 进入 workflow，02:16:22 PST 完成清理，用时 1 小时 13 分 36 秒。中间 `BASE-version` 取证等待 K2b 释放共享锁约 40 分钟。各次本任务调用的释放收据均已核对。[阶段与资源收据索引](evidence/rpi5-runtime-run-summary.json)

| 变体 | 实际安装包数 | GBS 退出码 | 构建墙钟 | cgroup 峰值 | 最低主机可用内存 |
| --- | ---: | ---: | ---: | ---: | ---: |
| BASE | 109 | 0 | 415.99 s | 2.25 GiB | 18.58 GiB |
| PGOGEN | 110 | 0 | 289.36 s | 2.34 GiB | 19.36 GiB |
| BASE-r、AFDO、PGO | 未执行 | — | — | — | — |

S0、S1、S2、S3 完成。两目标库的 profile runtime 定义和 PGOGEN 构建锁通过。BBB、ToS、Sintel 三段输入的 PLAT、BASE、PGOGEN 非计时正确性均通过，共 9 份 oracle。

三次 BBB 训练 decoder PID 为 71118、80869、90192，均退出 0，各有 6 份 profraw。18 份清单逐一保留 PID、build-id、文件大小与 SHA。raw 版本字段均为 `0x010000000000000a`，合并候选 indexed 版本为 13，候选 SHA-256 为 `0da9065bb8cb664711f157a68250c51f2eee2ed609d61e8dfa72dd4c64f9603e`。[训练、候选 profile 与前 20 函数取证](evidence/rpi5-runtime-s4-collisions.json)

S4 **退出 2**，原因为 `target DSO function attribution is ambiguous`。逐项使用留存的 llvm-profdata 输出复核，发现三个精确的重叠键。三条在所有所属 DSO 的 raw 中均无正计数，合并后最大内部块计数均为 0，也不在前 20 中。

| 函数 | Profile hash | DSO |
| --- | --- | --- |
| `ff_scalarproduct_float_c` | `0x0209aa3e1d398548` | libavcodec、libavutil |
| `ff_timecode_set_smpte` | `0x02dab88d7de0936e` | libavcodec、libavutil |
| `ff_toupper4` | `0x0d55ab714fffffff` | libavcodec、libavformat |

分 DSO 的原始计数诊断为 libavcodec 211/4530、libavutil 83/1127 个插桩函数有正计数。当前门禁仍拒绝这三个重叠键，候选 profdata 未封存。这些诊断不构成正式的合并 profile 覆盖率或消费判定。诊断还核实所用 llvm-profdata 的前 20 参数正确拼写为 `--topn=20`，已更正该调用和对应说明。没有改变 S4 判据，也未重跑板上阶段。

S5 的 BASE-r 重现、AFDO/PGO 构建、PGO 警告门禁、目标 `.text` 比较和后续正确性均未执行。未开始测量。板上会话最终恢复为 UID 5001、governor schedutil，RPM 数 1230，清理待办为空。等待对这 3 个零计数重叠键的裁决。

最终主机回归 257/257 通过，M1 封存运行回放 48/48 通过。
