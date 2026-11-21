# K1f-1：sdb 恢复验证、K-BASE-S 部署与首启停止

状态为 **RECOVERY_REQUIRED**。六次 PLAT 普通重启全部通过；K-BASE-S 部署完成，但首次 tryboot 在 300 秒内未恢复 TCP 或 SDB。依设计 v0.2 §5.4 停止，不重试启动，不进入 A/A 或布局测量。需人工断电上电，随后重新核对 PLAT。当前不能确认运行内核、U-Boot、tryboot 状态或 UID，不能宣称已完成 PLAT 回程。

[证据索引](evidence/20-k1f-1/index.json)记录每次启动、命令、原始输出、主机路径、tar 成员、大小和 SHA。[原始收据包](evidence/20-k1f-1/raw-receipts.tar.gz)保留未规范化的命令输出，包括 CRLF。没有计时轮次，索引的 `rounds` 为空。

## 开工与状态核对

授权开工为 2026-11-21 13:00 America/Los_Angeles（21:00 UTC），首次读时为 13:00:11。专用 worktree 为 `/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent-k1f-1`，分支 `k1f-1-20261121`。从 `12a3fc24` 建立，fetch 后 rebase 到 GitHub main `e25f693fa8c111ff480e8d3e964de145ecbd2e6b`，确认 K1e 报告与索引存在。主工作区的其他未提交内容未纳入本任务；没有复用其他会话索引或删除其锁。主机执行脚本沿用 nice 19、ionice idle。

- 设备仅为 `192.168.108.26:26101`，model 为 Raspberry Pi 4 Model B Rev 1.5，序列号 `100000004694d889`，机器 `armv7l`，UID 5001。初始 boot ID `6be260d9-4276-4261-8df8-e66a91ee96b6` 与 K1e 最终回程相同。
- PLAT notes SHA `146a4e2d…` 与已归档 build-id `395733b9c917cb98309b39cc3ec379c03ac36b3f` 的 notes 完全一致。U-Boot 版本属性存在，tryboot 字节为 `00 00 00 00`。六次回程均核对原始 cmdline SHA `1a132093…`。
- boot_a 只读核对 **418/418** 文件 SHA：413 个原文件以及 zImage-plat-direct、zImage-kbase、initramfs-afdo.gz、cmdline-afdo.txt、tryboot.txt。对照 K1d-c 最终清单；K1e 未更改这些文件。p6 K-BASE 模块目录 **72/72** 普通文件 SHA 一致，p6 保持只读。
- K1e 索引所列 K-AFDO 与 K-BASE-S artifacts 共 **92/92** 项 SHA 一致，包括原始 vmlinux、镜像、配置、System.map、模块相关清单及 RPM。[逐项核对](evidence/20-k1f-1/host-artifact-verification.json)
- 另在部署前核对已有 mmfault、forkexec、empty 和 ToS 输入 SHA；BASE.tar SHA 为 `bc351378313b0fb71587892cfa0f1befa591e9038abfac2ef3d81bb2ea32561f`。没有 GBS 构建。

预检的首次卸载失败：取证 shell 工作目录仍在只读挂载内，返回 `target is busy`。shell 退出后显式切到 `/` 卸载成功，复核无 boot_a 挂载且 UID 5001。该失败和修复收据均保留，未进行读写挂载或修改待比对文件。

## sdb 诊断与选定方案

本机 sdb 为 **4.2.25**。`devices -l` 返回参数错误，保留原件并使用支持的 `devices`。本地帮助和 [Samsung 官方 SDB 文档](https://github.com/Samsung/tizen-docs/blob/master/docs/sdk-tools/baseline-sdk/common-tools/smart-development-bridge.md)没有给出独立主机服务端监听端口的公开设置。`-P 26199 help` 和 `--port 26199 help` 均返回不支持；设置 `SDB_SERVER_PORT` 与 `ANDROID_ADB_SERVER_PORT` 后，strace 仍观察到客户端连接 `127.0.0.1:26099`。因此未建立或验证独立实例，也不将未列出的隔离方式断言为不可能。

尝试 `SDB_DEBUG=1 SDB_TRACE_PACKET=1`，客户端没有产生额外 debug 输出；保留 stdout/stderr 与端口探测 trace。没有附加调试器或修改共享服务。共享服务器 PID 在核对时均为 `158650`，其余设备的测试前后列表一致；没有向其他板发送命令。

选定的恢复方法：发出普通 reboot 后定向 disconnect；轮询目标 TCP，端口可达后尝试 connect 和带 boot ID 的只读命令；仍未恢复时每约 30 秒仅对该设备再次 disconnect。每次都要求新 boot ID 和完整 PLAT 身份通过，再 root off 并复核 UID 5001。

| 次数 | 断开后 TCP 可达 s | 断开后 connect 成功 s | 新启动首条命令 s | disconnect / connect 次数 | 新 boot ID |
| --- | ---: | ---: | ---: | ---: | --- |
| 1 | 53.552 | 63.609 | 63.753 | 2 / 2 | `918cfad5-40e2-4be5-9c57-0dc17be1e08d` |
| 2 | 65.961 | 76.654 | 76.796 | 2 / 3 | `c1e519a7-23d1-4161-bea9-18999e2d7cf0` |
| 3 | 65.328 | 75.747 | 75.891 | 2 / 3 | `ed8a321b-63e0-4bb3-9d21-551260772469` |
| 4 | 65.596 | 75.727 | 75.871 | 2 / 3 | `01f49b37-5bc3-49e0-ae63-9c9ffac559e6` |
| 5 | 66.873 | 81.827 | 81.974 | 2 / 3 | `6eeb409f-5860-44e7-a055-19d0a712072c` |
| 6 | 61.021 | 67.677 | 67.821 | 2 / 3 | `ff512cc4-09a5-4aa8-9bef-6ec686f9d3cb` |

六次均通过 300 秒门禁；合计 **12 次定向 disconnect（6 次立即断开、6 次恢复断开）、17 次 connect**。共享服务重启 **0**，独立服务启动/重启/停止 **0**。本批未复现 K1e 的长时间 sdb 停滞；观察到的是 TCP 已可达后短暂 connect 失败，随后恢复，不能据此认定 K1e 的服务端根因已经解决。

原始驱动摘要中的 `tcp_seconds`/`connect_seconds` 可捕获 reboot 后仍存活的旧系统连接。上表使用独立 TCP 观察器及原始命令时间重新定位端口断开后的成功连接，首条命令另以新 boot ID 证明。第 1 次 TCP 值来自原驱动，后五次来自观察器；均为轮询观测时延，不是连续测量的精确就绪瞬间。[修正后的摘要](evidence/20-k1f-1/sdb-diagnostic-corrected.json)与原摘要同时保留。

## K-BASE-S 部署

先核算再写入：FAT 簇 2,048 B，原空闲 1,499,136 B；获准删除的 zImage-plat-direct 为 14,905,760 B，K-BASE-S 为 15,168,416 B。按簇计算剩余 **1,236,992 B**，实际只读复查值相同，大于 524,288 B。

仅删除任务新增 zImage-plat-direct，新增 zImage-kbase-s。沿用 K1d 的 boot-publish helper，依次独占创建 `.tmp`、fsync、SHA、rename、syncfs、读回比对，卸载后只读复查。镜像 SHA `3e12951859725a432377d98d45d515dd85df0d56a1d1fb5d2e6781d7962442cf`。其余 417 个文件逐项一致，原有 413 个文件均未变化。

首次启动前原子替换 tryboot.txt 的 `kernel=` 为 `zImage-kbase-s`，其余内容与 K1d-c 版本一致，新配置 SHA `0a20abdbc0cc89c6b72333f2fbc442cbd8421a4f860bec0b0a96ad5e0d914ce7`。读回一致，boot_a 卸载成功；p6 未写入，K-BASE 产物及共用模块树保留。板端脚本、载荷与收据均在 `/opt/afdo_agent/k1f-1/`。

## 首启、停止状态与恢复

在 **2026-11-21T13:14:51-08:00** 发出 `systemctl --no-block reboot "0 tryboot"`。先前 PLAT boot ID 为 `ff512cc4-09a5-4aa8-9bef-6ec686f9d3cb`；预期 K-BASE-S build-id 为 `a78e6ca8956db526ba91d5856369fc1a7f15b5fd`。

发令后 0.203 秒的首次 TCP 探测仍命中旧连接；此后 49 次探测全部不可达，最后一次在 295.815 秒。180 秒诊断 ping 2/2 丢失、TCP 不可达、设备列表无目标；到 **300.000 秒** 仍无首条命令，进入 `RECOVERY_REQUIRED`。该状态发生在 sdb connect 和内核身份验收之前，不能将其归为已证实的主机 sdb 服务停滞，也不能仅凭网络不可达断言内核 panic。没有串口、运行态 dmesg 或新 boot ID 证据。[首启收据](evidence/20-k1f-1/kbase-s-first-reboot.json)

本次首启执行定向 disconnect 1 次，端口始终未恢复，connect 尝试 0 次，服务重启 0 次。没有自动重试首启，也未发第二次 reboot。规范化 FDT、cmdline、模块、dmesg、HDMI、dlog、D-Bus 和 PMU 首启验收均未获得运行态证据。

**需要人工断电上电。** tryboot 按已验证的一次性机制应在下一次启动回到原 U-Boot PLAT，但本轮未验证回程。恢复后必须核对 PLAT build-id、U-Boot、tryboot=0、原始 cmdline，再 root off 并复核 UID 5001。最后一次已证实的 UID 5001 在首启前配置写入完成时；为发出首启随后切为 root，超时后 UID 未知，未伪报 root off 成功。

最后一次持久文件读回证明 boot_a 保留 zImage-kbase、zImage-kbase-s、initramfs-afdo.gz、tryboot.txt、cmdline-afdo.txt；tryboot.txt 指向 K-BASE-S。原 config.txt、PLAT 文件及 p6 已有内容未修改。没有独立 sdb 实例需要停止。

## 预登记与未执行项

[协议锁](evidence/20-k1f-1/protocol.lock.json)在采集前保存 8 个 A/A block 顺序、种子 20261120 的平衡布局 AB/BA 表、六项基准顺序、预热 1 轮/计时 3 轮、bootstrap 20,000 次、ε=1% 和 workflow stats.py SHA。[计时口径补充锁](evidence/20-k1f-1/timing-definition.lock.json)在任何测量前明确 mmfault/forkexec 使用程序自身 elapsed_ns，其中 mmfault 校验排除在计时窗外；其余沿用 K1a 外部墙钟。两份锁及 SHA 均保留。

预算预登记用配对 log 比样本方差替代 workflow 公式的 `2×CV²`，保留 1.2533 和 ε/2 精度目标；N 截断到 10–40，正式 N 取 pipe/mmfault 的最大值。**未取得 A/A 数据，因此 N 为 null，未生成已估计 N 的锁。** 没有 A/A 点估计、CI、方差分解、布局效应、温度/频率或安静门禁统计；全部为未执行，不能填写为零效应或门禁通过。

A/A 完成 0/8 block、0/16 次测量启动；布局完成 0/10 block；预热与计时轮次均为 0。准备但未运行的测量/分析脚本在原始包中标识，不视为经过板端验证的可直接续跑流程。没有 K-AFDO 部署、正式比较、GBS 构建、Gerrit 推送或 hq 修改。

本报告交付已完成部分与停止收据，等待恢复和 PM 审核。提交仅包含本任务的报告、证据索引、原始收据及预登记文件；发布前在独立 worktree 再次 fetch/rebase，普通推送 GitHub main，不强推。
