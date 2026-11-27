# M2b 阶段 B · RPi5 清理恢复与 S5 板上验收

## 身份与旧会话清理

2026-11-26（PST），原 job 的 `192.168.108.13:26101` 已可连接。只读核对为 Raspberry Pi 5 Model B Rev 1.1、`aarch64`、内核 `6.12.80-arm64-rpi4-v8`、`TZ_BUILD_ID=tizen-unified-toolchain_20261118.083201`。板子的 `/proc/stat` 记录启动时间为 18:30:43 PST，晚于上一轮 04:45:58 PST 的断连。当前 boot ID 为 `b6a68096-0092-4461-8437-756df8f31989`。

原 `cleanup.json` 的 19 项与 [上轮失败收据](04_zero_dso_rebuild.md) 逐项一致。10 项部署物先核对 host 原件 SHA，再按板上的 SHA、文件类型和链接目标验证所有权后删除。1 项工作目录在创建 verified-pull 收据后删除，收据记录 0 个剩余文件。6 项空目录使用 `rmdir` 核销，最后按原 journal 恢复 governor 和 root 状态。每项结果及所有权或 verified-pull 收据 SHA 见[证据索引](evidence/rpi5-s5-board-acceptance.json)。清理后复核 UID 5001、governor `schedutil`、RPM 数 1230、待办 0，boot ID 不变。

## S5 恢复方式

用独立的 `resume.py --stop-after rebuild` 调用标准 S5 handler 和收据调度器。复验原 S0–S4 SHA 链、三组成功的 GBS 命令、RPM 文件 SHA 与大小、解包后的 build-id 与库 SHA，重新导出 RPM header、编译选项和构建锁。S5 使用归档的 BASE-r、AFDO 和 PGO 构建输出，PGOGEN 保留在原训练证据中。恢复脚本不允许调用 GBS。封存的 v13 profdata 保持 `0da9065bb8cb664711f157a68250c51f2eee2ed609d61e8dfa72dd4c64f9603e`。

恢复采用 CPUQuota 50%、MemoryMax 1 GiB、nice 19、ionice idle。等待其他构建退出且启动门槛达标后继续，复查时 I/O PSI full avg60 为 18.36%，可用内存为 18.87 GiB。未使用 I/O 豁免。

## S5 板上正确性

三种变体均完成三个输入的单线程、非计时解码，EOS、帧数、字节数、输出 SHA-256 和约定 caps 均匹配封存的 PLAT oracle。每次均复验加载库路径与 SHA。恢复标准会话时临时恢复了历史部署清单，含归档的 PGOGEN 库；本次板上解码矩阵只运行 BASE、AFDO 和 PGO。

| 输入 | 帧数 | 输出字节数 | PLAT 与三变体共享的输出 SHA-256 |
| --- | ---: | ---: | --- |
| BBB 720p | 1800 | 2,488,320,000 | `3a4c3820c576697edd4ca34f3532c8af8ffaf04687955c5d6b35215b9b06c814` |
| ToS 720p | 1800 | 2,488,320,000 | `4c2610c37b7790240c9158277981ed9c3ac81399e3e9df554ffebb2d2ff80c4e` |
| Sintel 1080p | 1440 | 4,478,976,000 | `91d171c0cd99266d0efeee7b9023a77bf39c925ec372bcd1d1e7efaf08ecd193` |

本次 S5 重验 BASE-r、PGOGEN、AFDO、PGO 的构建锁。BASE-r 与 BASE 的库 SHA 及 build-id 一致，AFDO 消费检查通过。PGO 构建根中 profile SHA 与封存相同，目标库过期警告为 0，前 20 函数的编译单元全部通过，两目标库 `.text` 均变化。

## 停止点与最终状态

S5 收据状态为 `complete`，SHA-256 为 `405e6ce259bc4aafc0d76633b7886421c1f7264a4e8e32e4d40f04047382194a`。清理后用标准收据验证器重新核对了本阶段 35 项输入、332 项输出及上游 SHA 链。会话于 20:10:56 PST 正常停在 `rebuild`，未进入 `measure`。最终复核为 UID 5001、governor `schedutil`、RPM 数 1230，boot ID 与本次接回时一致，清理待办为 0。没有新 GBS 调用，退出后共享构建锁的非阻塞取得检查退出 0。

主机首次查询发现本地 SDB 服务未运行，SDB 自动启动了本地服务。后续连接和命令仅面向指定的 `.13`，未重启共享服务。原始日志、逐项清理记录、恢复脚本和完整 S5 收据均留在 WORKDIR `temp/`，证据索引记录路径与 SHA。
