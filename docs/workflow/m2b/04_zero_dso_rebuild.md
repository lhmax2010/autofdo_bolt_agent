# M2b 阶段 B · RPi5 碰撞裁决与停止点验收

## 裁决与恢复边界

2026-11-26 PST，按 [PM 裁决](01_design.md#阶段-b-续-2-pm-裁决2026-11-26) 复用上一轮 S0–S3。本次只连接 `192.168.108.13:26101`，核对 Raspberry Pi 5 Model B Rev 1.1、`aarch64`、内核 `6.12.80-arm64-rpi4-v8`、镜像 `tizen-unified-toolchain_20261118.083201`、初始 UID 5001。

新的 job 显式锁定碰撞裁决和原 S3 收据 SHA。runner 递归验证 S3 收据链、63 项输入、8283 项输出及原 job。旧 job 的临时 I/O 豁免已撤回，其他实验输入不变。为使历史收据继续按原路径逐字节复验，独立旧 worktree 中两份历史 Python 文件恢复为 S3 记录的精确字节，新 worktree 仍使用更正后的 `llvm-profdata --topn=20`。旧的训练和失败收据保留。S4 在主机完成；板上复用既有部署清单的原件后才进入 S5。

## S4 封存

三个训练进程正常退出，每个进程贡献 6 份 profraw，共 18 份。raw 版本为 `0x010000000000000a`，其中格式版本为 10，indexed 版本为 13。封存的 `pgo.profdata` SHA-256 为 `0da9065bb8cb664711f157a68250c51f2eee2ed609d61e8dfa72dd4c64f9603e`，与上一轮未封存候选的字节相同。

| 碰撞键 | Profile hash | 来源 DSO | 每份 raw 的计数向量 |
| --- | --- | --- | --- |
| `ff_scalarproduct_float_c` | `0x0209aa3e1d398548` | libavcodec、libavutil | 两个计数均为 0，各 DSO 3 份 |
| `ff_timecode_set_smpte` | `0x02dab88d7de0936e` | libavcodec、libavutil | 十二个计数均为 0，各 DSO 3 份 |
| `ff_toupper4` | `0x0d55ab714fffffff` | libavcodec、libavformat.so.62.3.100 | 五个计数均为 0，各 DSO 3 份 |

按裁决允许三个键合并，合并结果再次核对对应计数向量全为 0。libavcodec 有正计数的函数为 211/4530（4.66%），libavutil 为 83/1127（7.36%）。计数最高的 20 个函数均定位到具体编译对象，覆盖 libavcodec 的 6 个编译单元。[完整前 20 清单、逐 raw 计数和 build-id](evidence/rpi5-zero-dso-seal.json)。

## 主机资源

本次未使用 I/O 豁免。入口要求共享锁无占用、无其他 GBS/rpmbuild、MemAvailable ≥16 GiB、load1 <12、可用磁盘空间 ≥50 GiB、I/O PSI full avg60 <20%。入口两次检查 I/O 分别为 16.59%、17.45%。runner 复查先遇到 32.37% 和 21.45%，继续等待，03:49 PST 以 11.81%、可用内存 23.41 GiB 通过。GBS 仍要单独获取共享锁并复查该门禁。runner 为 1 GiB/50% CPU，GBS 为 4 GiB/100% CPU、MemoryHigh 3 GiB，均使用 nice 19、ionice idle。

| S5 构建 | GBS 退出码 | 构建墙钟 | 进入构建的等待 | 启动 I/O PSI full avg60 | cgroup 内存峰值 | 最低主机可用内存 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BASE-r | 0 | 240.55 s | 600.36 s | 3.32% | 2.29 GiB | 17.46 GiB |
| AFDO | 0 | 245.14 s | 0.53 s | 6.87% | 2.09 GiB | 21.66 GiB |
| PGO | 0 | 202.64 s | 0.18 s | 1.38% | 2.18 GiB | 21.06 GiB |

AFDO 的 `gbs --version` 取证调用另等待 1800.74 秒，等待期间记录了他人构建和共享锁。三次构建的 `MemoryHigh`、`MemoryMax`、OOM 事件均为 0。03:27:16–04:45:58 PST 的 runner 墙钟为 1 小时 18 分 42 秒，含入口复查与构建让行。各调用的锁均已释放，终止后非阻塞复验可取得共享锁。[主机、失败与恢复证据索引](evidence/rpi5-zero-dso-run.json)

## S5 审计与停止

| 项目 | 结果 |
| --- | --- |
| 冻结依赖与构建锁 | BASE-r、AFDO、PGO 均使用原冻结 109 包，PGOGEN 保留已登记的第 110 包 `compiler-rt`。四项构建锁全部通过，仅有各变体声明的差异。 |
| AFDO 消费 | 通过。`libavcodec`、`libavutil` 的 sample-profile 应用证据和 staged SHA 均通过。 |
| PGO 诊断 | 离线回放原构建日志通过。目标库 `profile-instr-out-of-date` 为 0，`profile-instr-unprofiled` 为 0，20 个高计数函数所属的 6 个对象均有编译证据。其它 profile 警告为 0。 |
| PGO 消费 | 离线复核通过。构建根内的 indexed profile SHA 与 S4 封存值一致，两个目标 DSO 的 `.text` 均变化。前 20 函数所属的 6 个热对象的可执行 `.text` / `.text.*` 节均有变化。 |
| BASE-r 复现 | 离线复核通过。两个目标库的运行文件 SHA、调试文件 SHA 和 build-id 与 BASE 逐项一致。 |
| BASE、AFDO、PGO 与 PLAT | 本次 S5 非计时正确性未执行。上一轮 S2 的 PLAT oracle 和非计时 BASE、PGOGEN 核对原件保留。 |
| S5 正式收据 | 未生成。原失败收据保留，退出码 7 `recovery-required`。未进入 measure。 |

原 runner 在 S5 报告 `PGO build log lacks compiler output synchronization proof`。原日志第 522–524 行显示 `export 'MAKEFLAGS=--output-sync=target  -k'` 后执行 `/bin/make -j2`。旧解析器要求 `MAKEFLAGS=` 前无引号，漏掉了 shell 跟踪的实际格式。本轮按 workflow 自身缺陷规则计 1 次，使用原文建立先失败后通过的回归用例。新解析器读取 shell 导出的变量值并检查完整选项，拒绝通过别的变量或相似选项取得同步证明。随后以同一份日志、原对象和已用的 profile 重放主机审计。正式实验的运行 worktree、S4 封存和 S5 失败收据保持原样，回放证据单独登记。

清理开始时，SDB 返回 `error: target not found` 和 `error: serial number '192.168.108.13:26101' wrong`。04:46:35 PST 仅对该 serial 执行 `disconnect`、`connect`，连接退出 1，设备未恢复。未重启共享 SDB 服务。清理日志保留 19 项待办，其中包括 root/UID、governor、1 个工作目录、10 项部署物和 6 个空目录。本次最终 UID、调速器、RPM 数和清理状态无法核验。恢复连接后需要先复核板子身份，再按原清理收据继续。

主机回归 269/269 通过，M1 封存运行只读回放 48/48 通过。原始 profile、构建日志、两次解析回归输出和收据均保存在 WORKDIR 的 `temp/`。本次使用宿主既有工具、认证和共享 SDB 服务，未主动在 WORKDIR 外创建产物。GBS 构建日志中的 `/var/tmp` 为构建根内路径。
