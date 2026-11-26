# K2b 续：独立 K-GCOV 与宿主机重启恢复

**当前停在主机 I/O 门禁。** XZ 镜像与 52 个普通模块已在冻结 buildroot 中落盘。宿主机重启后，串行恢复单元正在等 I/O 压力下降。RPi4 仍运行原 PLAT，p6 和 boot_a 尚未写入。 [证据索引](evidence/31-k2b/index.json)

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

宿主机重启前，K2b 守卫连续两次采到可用内存低于 6 GiB，随后终止打包。该构建单元峰值约 5.0 GiB，cgroup 的 OOM 和 OOM kill 都是 0。最后一份资源收据的全局可用内存约 3.6 GiB，load1 约 140。旧启动日志另有阻塞任务记录，随后记录 systemd 关机，证据不足以确定整机失去响应的根因。 [终止前读数](evidence/31-k2b/restart/pre-shutdown-resource-samples.jsonl)

恢复使用保留的镜像、GCNO、`Module.symvers`、生成头文件和 Kbuild 暂存模块。待资源门禁通过后，独立输出目录只用 `-j1` 重建六个 extra 模块，随后核对全部 58 个模块的 ABI、去 BTF 和 p6 容量。当前恢复单元 CPUQuota 为 100%，MemoryHigh 1.5 GiB，MemoryMax 2.5 GiB，禁用 swap，nice 19，I/O 优先级 idle。用户 cgroup 无设备带宽控制器，镜像验证的批量读取在程序内限为 12 MB/s。开工要求可用内存至少 16 GiB、load1 小于 CPU 数的 0.6 倍、磁盘空间至少 50 GiB、全局 I/O full PSI 不超过 5%，并取得共享构建锁。资源门禁最多等待 3 小时。归档时 I/O full PSI 为 56.14%，恢复尚未开工。 [恢复状态](evidence/31-k2b/restart/recovery-state.json) · [资源窗口](evidence/31-k2b/restart/resource-samples.jsonl)

## 板上状态和未完成项

宿主机重启后，共享 SDB 一度无监听。端口恢复监听后仅重新连接 RPi4。只读核对确认 PLAT build-id 对应原内核，boot ID 未变，原 cmdline、U-Boot、tryboot=0、UID 5001 与 p6 只读状态均复核通过。重启后的额外 5 分钟只读温度中位数 59.400°C（范围 57.939–60.374°C，30 点），高于首启准备的 58°C 门槛。 [PLAT 身份](evidence/31-k2b/restart/plat-identity.txt) · [温度原件](evidence/31-k2b/restart/plat-thermal.tsv)

六个 extra 模块的重建、58 个模块的最终核验、写入、首启及 15 段训练仍待执行。`.gcda` 导出为 0 段，GCOV 质量、与 IP/R1 的对照及混合候选均无实测结果。恢复单元只处理主机阶段，首启仍需在用户可观察 HDMI 时进行。
