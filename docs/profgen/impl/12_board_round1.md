# RPi4 第一轮板上评估：校准收尾缺工具处停止

本轮**未完成正式评估**。16 项目标部署 SHA 通过，硬件 cycles 实际采到非零样本；第一次 Thumb spike 校准在收尾 RPM 数量比较处因板上没有 `cmp` 失败。依据 STATUS 最高原则第 3 条“缺工具就停下，在报告里说明”，停止后续采集、训练和主机 profile 生成，没有安装工具或现场绕过。此次不是 llvm-profgen 缺陷，正式工具未运行、未修改。

## 1. 预注册与时间

[预注册](../eval/preregistration.md) 提交 `7d3d9d9f9184bc2e0e2b94a479916a2d65f13463`，提交时间 **2026-11-05 20:04:33+08:00**，已推送 GitHub main，早于首条 `sdb devices`（20:07:34.970+08）。正式矩阵为 70 次 S 和 14 次 R/C/G5 训练；校准不计入矩阵。

从首条设备查询至最终恢复/空间核对（20:11:09.232+08）约 **214 秒（3 分 34 秒）**；其中校准 perf/workload 墙钟 **1.29 秒**，并非全部采集耗时。板上使用 +09 时区且观测时间比主机多约 14 秒；原始时间均保留，不将字符串时差解释为耗时。短步骤未达到 600 秒资源采样周期，没有启动整套长时间采集 worker。校准有逐秒环境文件和失败 ALL-END；主机停止标记见 `temp/board-round1/ALL-END.status`。

## 2. 身份、权限与部署

证据：[设备](evidence/12/01_devices.json)、[三项断言](evidence/12/02_identity.json)、[初始状态](evidence/12/04_before.json)、[完整操作记录](evidence/12/08_operations.json)。每条板上 shell 带 `__REMOTE_RC`，不以 SDB transport 退出 0 冒充远端成功。

- 唯一设备 `192.168.108.26:26101`；实际 model=`Raspberry Pi 4 Model B Rev 1.5`，arch=`armv7l`，release=`6.12.80-arm-rpi4-v7l`，不是凭 IP/别名认板。
- 当前内核 `#1 SMP Wed Nov 4 17:05:36 UTC 2026`，clang/LLD 22.1.8。保存了 `/proc/version`、镜像 tizen-build.conf、uname、zram/swaps。无可读 `/proc/config.gz` 或对应 `/boot/config-*`，配置哈希 **unknown**，未挂载 /boot。
- 初始 `id` 已为 uid=0；`sdb root on` 退出 0。policy0 初始 `schedutil`，保存主机及 `/opt/afdo_agent/state/round1-governors.tsv` 后改为 performance。`perf_event_paranoid=2`、`kptr_restrict=0`，始终未写。
- `/opt` 为 rw/ext4，无 noexec。初始可用 1,272,240 KiB，16 项 payload 实体约 90.4 MB（[空间清单](evidence/12/05_payload_space.json)）；本轮仅小规模校准，有足够空间，不声称已验证高档/LOST 的空间需求。
- perf/libLLVM 原已不存在，从已核验本地解包副本部署，主机/板上 SHA 一致：perf `41b9b9a0d41da1b2a600c84ffa482ea05c52af54af094f5c6a2bf52d6aa13138`，libLLVM `49fcc90da72ac2eabd7bbdb0a71566ea2284a532f98730ca46496782f30fb69e`。`perf --version` = 6.12.80，退出 0。
- payload-rpi4 全部 16 个清单目标逐项 SHA 通过。只验证了 spike-thumb-S 的运行时 maps/buildid-list；其余 15 项尚未执行，不能称运行时验收通过。

为本轮每 RUN 的内核记录要求，在 `tools/profgen/board/common.sh` 添加 `/proc/version`、只读配置哈希、swaps/zram 记录，`bash -n` 通过；没有改 LLVM、冻结设计或 `cmp` 行。

## 3. Tears of Steel 测试输入

官方影片 URL：`https://download.blender.org/demo/movies/ToS/tears_of_steel_720p.mov`。实际 curl 下载成功，372,178,639 字节，SHA `efa9062d9cdb7a338e40ad530dfdf234806743f29ae6a1a136b97ece4e588e8f`。

授权依据：[Blender Mango 官方 sharing 页面](https://mango.blender.org/sharing/) 为 Creative Commons Attribution 3.0；署名 Blender Foundation / Mango Open Movie Project。目录下 copyright.txt 明确仅适用于 Original Soundtrack（BY-ND），**未把该文件当作影片许可**。Web 阅读工具返回 402，但本机 curl 官方页面及影片均成功；没有使用镜像/第三方内容。

取固定 300–360 秒，沿用 BBB 的 libx264/veryfast/High/yuv420p、1280×720、30fps、60秒、4M/maxrate4M/bufsize8M、2编码线程、1filter线程、无音频、faststart；未额外改 level。两份 ffprobe 的实际 level 都为 31。测试片段 29,964,461 字节，平均容器码率 3,995,261 bit/s（相同目标码率不保证不同内容的实际均值完全一样），SHA `280fbd41f8772491ebe784aa19a3caed3bb1e8b2e64daef1d2a5a284d1f38ad1`。尚未推送视频到板上。

[完整命令、ffprobe、哈希及授权摘录](evidence/12/09_media.json)；下载/转码原日志与官方页面留 `temp/board-round1/`，影片和生成片段也只留该目录。

## 4. 校准结果与停止原因

先做 3 秒 `cycles -c 1000003 -a -- sleep 3` 权限探测，record=0，evlist type=0/config=0（dummy 软件边带事件不是 cycles 回退）；该探测在原 governor 下执行，属于流程偏差，不计入预注册数据。之后固定 performance 执行：

```sh
/bin/bash /opt/afdo_agent/scripts/collect.sh rpi4 sample-fixed spike-thumb-S /opt/afdo_agent/eval-manifest.tsv 10000
```

校准实际 `record --buildid-mmap -e cycles -c 1000003`，strict 5.2.2 字段全量导出，record=0；独立统计 **235 条样本：目标 226、kernel 8、其他 1**，LOST=0。实际格式为 `pid/tid period event: ip (dso+off)`，统计正则留证。样本预算尚未校准到 2 万档。输出校验 `cb93552eab3a7dfe`。运行映像 ID `322b4f1082e030032b3a85eb599e2bdfbe37797d` 与清单一致；maps 命中正确部署路径，SHA 一致。[校准原文](evidence/12/07_calibration.json)

收尾失败原文：

```text
/opt/afdo_agent/scripts/common.sh: line 143: cmp: command not found
__REMOTE_RC=127
RECORD_EXIT 0
EXIT 127
ALL-END 2026-11-05T21:10:30,994303712+0900 FAILED
```

`command -v cmp` 另查退出 1。RPM 前后文件内容都是 1232，但脚本未能完成约定的比较，因此这次 RUN 标为失败，不将其补标成功。没有工具链/库缺陷证据。候选后续方案：经确认后将单值 RPM 计数比较改为 Bash 非空、数字格式校验及字符串/整数比较，保留失败门禁；或用户提供镜像内已有 cmp 的明确路径。**两者本轮均未实施，不建议安装 RPM 绕过纪律。**

环境片段见 [11_environment_excerpt.txt](evidence/12/11_environment_excerpt.txt)：频率 1.5GHz、观测温度约56.965°C、pswpout 2878不变；vcgencmd 不存在，节流状态 unknown，不能宣称符合全部清洁轮次规则。

| 正式采集/训练 | 完成数 | 目标样本数 |
|---|---:|---|
| spike Thumb S / A32 S | 0/20；0/20 | 未采集正式档；仅上述失败校准226 |
| FFmpeg Thumb BBB S / ToS S | 0/20；0/5 | 未采集 |
| FFmpeg A32 BBB S | 0/5 | 未采集 |
| R/C/G5 训练 | 0/14 | 无 profraw/profdata |
| LOST压力、五项集成 | 0 | 未执行 |

身份等级：部署/运行时 ID 核对通过一项；**正式 profgen 的 verified/unverified 等级未取得**。不把手工 ID 核对写成工具质量报告。没有生成 IP profile、质量报告或统计 nonleaf line 0；后者为未知，不是 0%。LOST 完整高丢样与真实 avg 挂账均未关闭。

## 5. 拉回、恢复与流程偏差

原始数据主机位置：`temp/board-round1/pulled/`（SDB 将目录内容直接平铺到目标路径，telemetry保留子目录），包含权限探测 cycles.data、校准 perf.data、完整 perfscript.txt、buildid-list、evlist、stderr、状态、maps、逐秒环境等。板上先保存了33个文件的 SHA 清单。

**清理顺序发生违规，明确记录：**首次主机哈希验证按错误的“多一层RUN子目录”查找，FileNotFoundError；外层 shell 未设置 errexit，仍继续删除了板上两个 RUN。这不满足用户“全部拉回并核对 SHA 后才删除”的要求。之后按实际落盘路径重新核对，33/33 SHA 与删除前保存的板上清单一致，数据完整，无已知丢失。[逐文件校验与时间说明](evidence/12/06_pull_hashes.json)。不能用后验一致消除这个顺序错误。后续需把拉回、路径检查、全量哈希验证、删除置于同一个显式 fail-closed 控制流程，失败时禁止触发删除。

恢复与最后状态（操作原文在08_operations）：

- policy0 恢复 schedutil，并读回与原值相等，退出0；root恢复/保持原始开启状态，`id`仍uid0。
- 两个本轮RUN已删除，`/opt/afdo_agent/work`为空；没有残留本任务 collect/perf/workload/telemetry进程。
- RPM开始/结束 **1232→1232**；结束单独检查 rpm 查询退出0。sysctl仍2/0。
- `/opt`结束 used **158,064 KiB**、available **1,147,552 KiB**（13%），增加主要为保留的16变体、perf/libLLVM、脚本及小型state文件。保留供后续轮次；没有改系统库或boot。
- 主机 `ALL-END 2026-11-05T20:11:09.253381+08:00 STOPPED missing-board-cmp; collect exit=127`。

板上明确授权边界例外：root模式、policy0 governor sysfs写入及恢复；其余板上文件写入均在opt专用目录。本轮未观察到新增主机越界文件写入，但未扫描工作目录外，不能据此保证SDB守护进程没有内部状态写入。上述预探测governor与清理时序是执行偏差，不归为获准例外。

## 6. 待设计 v0.8 登记

- 本轮授权 root/performance 保存恢复、不改两项sysctl；训练BBB720/测试官方ToS/BBB1080压力；性能±1%、质量±0.01、三档目标预算、独立采集次数、异常数字阈值与固定seed，均已预注册。
- no-cmp 是板上执行脚本的依赖缺口，不要求改变冻结IP设计规则；应将板上依赖预检提前至采集前。未知节流指标按预注册保留未知，不事后放宽判据。
- 没有质量数据，不能作默认aggregation/weight/skid/head/补零决策。没有新LLVM实现或Agent开发。

## 7. 下一步质量分析需要的输入清单

目前只有失败校准原件及已归档测试视频；**不足以开始质量分析**。后续仍需全部70份S预算采集（或其完整分段）、14次stage分离训练、LOST压力与五项集成、每RUN完整环境/maps/ID/退出码，以及正式工具逐份质量报告。R/C/G5的profdata尚不存在。恢复执行前需解决cmp依赖、收尾删除门禁、确认逐秒节流可观测性；预注册版本保留，不覆盖历史记录。

正式工具 SHA `334a09290f53eb4c793ae91759f2b6344a36e63317820eb9151771b262dc3f30`、v0.7 SHA `eec6b208d8e1fedb840f0933eb20a37c188890b6c8c29e43986c5c9bbca9f6be` 未变化。[范围证据](evidence/12/10_scope.json)
