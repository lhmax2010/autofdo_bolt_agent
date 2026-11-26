# K2b 续：独立 K-GCOV 与宿主机重启恢复

**主机恢复、p6 写入与 PLAT 温度门禁均已通过，等待用户在板旁。** RPi4 仍运行原 PLAT，boot_a 保持原样。 [证据索引](evidence/31-k2b/index.json)

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

## 板上状态和未完成项

宿主机重启后，共享 SDB 一度无监听。端口恢复监听后仅重新连接 RPi4。只读核对确认 PLAT build-id 对应原内核，boot ID 未变，原 cmdline、U-Boot、tryboot=0、UID 5001 与 p6 只读状态均复核通过。重启后的额外 5 分钟只读温度中位数 59.400°C（范围 57.939–60.374°C，30 点），高于首启准备的 58°C 门槛。 [PLAT 身份](evidence/31-k2b/restart/plat-identity.txt) · [温度原件](evidence/31-k2b/restart/plat-thermal.tsv)

p6 与温度门禁已通过。boot_a 镜像部署、首启和 15 段训练仍待执行。`.gcda` 导出为 0 段，GCOV 质量、与 IP/R1 的对照及混合候选均无实测结果。首启仍需确认用户可在 RPi4 旁观察 HDMI。
