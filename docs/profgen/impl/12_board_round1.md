# RPi4 第一轮板上评估：采集进展与停止记录

**当前结果见第9节：7份正式采集已拉回，真实avg在GNU AS的Thumb DWARF边界处停止，governor/root已恢复；预注册未改。第1–8节为保留的历史记录。**

以下为首次停止记录：本轮**未完成正式评估**。16 项目标部署 SHA 通过，硬件 cycles 实际采到非零样本；第一次 Thumb spike 校准在收尾 RPM 数量比较处因板上没有 `cmp` 失败。依据 STATUS 最高原则第 3 条“缺工具就停下，在报告里说明”，停止后续采集、训练和主机 profile 生成，没有安装工具或现场绕过。此次不是 llvm-profgen 缺陷，正式工具未运行、未修改。

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

## 8. 恢复轮：root 前依赖预检因部署文件不可访问而停止

本节续写于2026-11-05，保留上面第一次停止和偏差记录。预注册 `7d3d9d9` 的文件逐字节不变（SHA `dfc5b429c5007ed701cb01c746349ed7544a0556b0591e530da690e52e4d7d70`）。本轮未连接其他板子、未执行任何 perf 命令、未推送或修改板上文件，也未执行 root/governor 状态变更。

### 8.1 本地主机改动及检查

`common.sh` 去掉 cmp 依赖：读取前后RPM数量，必须非空且全部为十进制数字；再用 Bash `10#` 整数比较，避免前导零被解释为八进制。额外拒绝超过18位的异常输入，避免算术溢出把异常值误判为相等。7项检查全部通过：相等、不同、空、负数、表达式字符串、前导零、超长溢出。三个板上脚本 `bash -n` 通过。[本地测试](evidence/12/15_resume_local_checks.json)

依赖清单写入 common.sh，扫描方法为逐一静态审阅 `common.sh`、`collect.sh`、`measure.sh`，覆盖命令替换、管道、数组中的程序与内嵌 Bash launcher；证据列出每个字面命令的文件和行号。字面检索只是人工审阅索引，不声称是完备的Bash语法分析器。Bash内建/关键字（time、kill、read、printf、test、wait、source等）不要求独立可执行文件；动态spike程序仍由load_variant检查可执行与SHA。节流改读明确指定的只读sysfs节点，没有节点即unknown，不再调用可选vcgencmd。[扫描清单](evidence/12/12_dependency_scan.json)

全部23项：

```text
/bin/bash awk cat cut date df find findmnt grep gst-inspect-1.0
 gst-launch-1.0 mkdir mkfifo ps readlink rm rpm sha256sum sleep tr uname wc
 /opt/afdo_agent/tools/perf
```

`new_run` 在创建RUN/启动perf前再次执行依赖预检与performance断言；本轮host先在root/governor变更之前执行同一完整清单的command-v门禁。**新版common.sh仅保存在主机，尚未部署到板上**；不能把本地修正称为板上验收通过。

### 8.2 实际身份、预检与权限证据

[预检原文](evidence/12/13_resume_preflight.json)、[停止只读诊断](evidence/12/14_resume_stop.json)。唯一设备仍是 `192.168.108.26:26101`，三项分别查询均退出0：model Raspberry Pi 4 Model B Rev 1.5、armv7l、6.12.80-arm-rpi4-v7l。最初合并查询缺少model后的换行，导致主机解析断言失败；改为分别查询确认实际身份正确，并未放宽身份规则。发送整个common.sh作内联查询超过SDB service-name长度限制；保留原报错后改为仅发送相同完整依赖数组的简短command-v循环，未执行或写入脚本文件。

最终依赖预检 **22项通过、1项未通过，远端退出1**：

```text
DEPENDENCY_MISSING /opt/afdo_agent/tools/perf
__REMOTE_RC=1
```

这里的MISSING是command-v门禁标签，**不是文件已不存在的事实断言**。停止前只读补证：

```text
id: uid=5001(owner) gid=100(users) ... context="User::Shell"
ls: cannot access /opt/afdo_agent/tools/perf: Permission denied
ls: cannot access /opt/afdo_agent/lib/libLLVM.so.22.1: Permission denied
__REMOTE_RC=2
sha256sum: /opt/afdo_agent/tools/perf: Permission denied
sha256sum: /opt/afdo_agent/lib/libLLVM.so.22.1: Permission denied
__REMOTE_RC=1
```

本次SDB原状态为非root，与第一次停止时原状态不同；不推测是谁或什么改变了状态。不调用root on来使检查通过，不chmod、不改安全标签、不重部署、不安装。错误只证明当前身份不能访问这两个路径，不能据此区分DAC/安全标签等具体根因。按本轮“root前依赖检查，任一缺失即停止”裁决停在此处。

候选需要用户决定的流程调整：系统命令保持root前完整预检；对部署文件仅因权限拒绝而不可检查的情况，是否允许记录该事实后暂开已授权root、在governor变更与任何perf运行前再检查部署工具/SHA，失败即恢复原root状态。或者由用户先使当前非root SDB shell可查询部署工具，再原样重跑门禁。**本轮均未执行。**

### 8.3 失败注入、空间与采集完成情况

拉回/全量SHA验证/确切RUN路径删除的单一失败即停止流程、故意哈希不符的主机演练，**尚未实现/运行**：本次在依赖门禁触发停止，不能声称演练通过，也没有正式数据使用未经演练的新清理流程。

只读sysfs查找 `find /sys/devices/platform /sys/firmware -iname '*throttl*' -print` 返回0、无输出；仅说明上述范围未找到节点，节流保持unknown，不能证明整个固件没有接口。没有逐秒采集，不更改异常阈值。

本轮板上查询从20:33:35.836到20:34:27.279+08，约 **51.44秒**，实际采集耗时0。状态始终未改：root保持off（uid5001）、policy0保持schedutil，无需恢复；RPM只读查询退出0、数量1232，与上轮记录相同。最后 `/opt` used **160,428 KiB**、available **1,145,188 KiB**、13%；本轮没有部署、清理或分批空间消耗。两次会话之间的磁盘变化不归因于本轮操作。

Tears of Steel片段仍只在主机；SHA复核和视频推送因门禁停止未执行。16变体本轮未能重新校验；不沿用旧SHA来宣称本轮恢复已通过。正式S仍 **0/70**，R/C/G5仍 **0/14**，五类集成0；旧失败校准226目标样本仅环境/流程证据。verified等级、nonleaf line0、profdata均未取得；LOST和真实avg挂账保持未关闭。

### 8.4 待设计 v0.8 登记：本轮执行流程裁决

1. 去掉cmp，非空十进制格式校验后Bash整数比较，失败门禁保留（本地实现和测试完成）。
2. 身份通过后、root/governor变更之前逐项command-v检查，列出全部失败项（本轮触发上述权限阻塞）。
3. performance之后才运行任何perf，包括权限探测（本地增加门禁，本轮无perf）。
4. 单一失败即停的拉回→实际路径检查→全量SHA→确切RUN删除流程，先哈希失败注入证明不会删除（待完成，不能使用上次有顺序缺陷的流程）。
5. 每次采集空间必须≥2×已观测产物估算+200MB；不够先拉回/核对/清理上一批，再不足即停止；不得删除部署库腾空间。LOST先小规模体积试采再独立估算（待执行）。
6. 只读查sysfs节流节点，未找到维持unknown；频率/温度阈值及原预注册不改。
7. 上次226条目标样本不计入正式矩阵。

以上是执行流程裁决登记，没有修改v0.7正文或预注册。缺失的失败注入、空间门禁编排和全部采集/训练仍是恢复前待办；不把本次本地脚本改动当成整轮完成。边界例外：本恢复轮无板上写入或状态修改；没有读取WORKDIR外的项目输入，未扫描SDB自身可能使用的外部状态文件。

## 9. 两段预检后恢复：真实 avg 在 GNU AS 的 Thumb DWARF 区间处停止

### 9.1 当前结论与执行流程裁决（待设计 v0.8 登记）

本节是当前状态；第1–8节保留为历史。预注册 `7d3d9d9` 未改。完成 **7/70** 次正式 S 录制与完整拉回（均只有第1个独立重复），其中6次完成正式工具 sum 转换、身份均 **verified**；第7次在停止时收尾，原件完整保留，尚未转换。R/C/G5 **0/14**、LOST压力和5类集成均未开始。**本轮没有完成评估，不作配置优劣或等价结论。**

最新授权顺序登记如下：三项认板 → 非root系统PATH依赖 → 记录原root并root on → root下部署文件/权限/SHA及唯一例外`perf --version` → performance governor → 其他perf。root是会话权限；部署预检失败时尚未改governor，恢复root后停止。旧“所有perf必须在governor之后”由本次明确允许version预检的裁决细化；不把它扩展到record/list/stat。

[完整操作与真实远端RC](evidence/12/17_resume2_operations.json)、[静态依赖清单与源码行](evidence/12/22_dependency_inventory.json)。最终系统命令清单24项：

```text
/bin/bash awk cat cut date df find findmnt grep gst-inspect-1.0
gst-launch-1.0 ionice mkdir mkfifo nice ps readlink rm rpm sha256sum
sleep tr uname wc
```

静态审阅覆盖全部3个board脚本的管道、替换、数组与Bash launcher，字面出现位置作为审阅索引；不是声称正则能完整解析Bash。内建time/kill/read/printf/wait等不作外部依赖。部署的perf、spike及库另在root下检查。24项均存在，未安装或绕过缺失命令。

**预检时序偏差保留：**第一次非root检查22项；后来给launcher增加nice/ionice时，这两项在root下、第一次governor改变之前检查。20:54:57再次恢复执行时，完整24项已在非root下通过。不能把第一次22+2检查改写为“24项全在首次root前”。后续应始终按最终完整清单一次检查。

授权的cmp替代已部署：非空十进制、长度限制后Bash整数比较；不满足仍失败。采集脚本支持重复完整解码，保持同一FIFO写端直到所有重复结束，记录合并输出字节流的SHA，不把不同重复数的流SHA直接比较。三份脚本bash-n通过。

### 9.2 身份、root变化与部署复验

本次20:44:52+08重新查设备并三项断言，唯一RPi4：`Raspberry Pi 4 Model B Rev 1.5 / armv7l / 6.12.80-arm-rpi4-v7l`。`uname -v`仍为`#1 SMP Wed Nov  4 17:05:36 UTC 2026`，与第一次一致；各已回收RUN保存uname、/proc/version、os-release、tizen-build.conf及zram/swaps。配置文件不可读时明确记录unknown，没有挂载boot。

开始uid5001（root off），uptime **997.67秒**；第一次20:07开始时uid0。当前uptime反推约20:28启动，晚于第一次查询，故**支持中间重启过、内核仍相同的判断**；这是时间推断，未取得上次boot-id或uptime可作逐值比较，不能断言重启原因或单独归因于SDB重置。当前boot-id `4e5c71ff-0cf8-4e7e-9f61-16602d3c3b57`，没有执行重启。

root预检核对62个已部署普通文件（含16项目标及其依赖、旧脚本、manifest、perf/libLLVM）SHA全部一致；动态可执行目标另由load_variant/test-x验证，新版脚本部署后再次按主机SHA核对。旧脚本的62项预检SHA与新脚本部署SHA是两个时间点，不混为一份清单。[部署清单](evidence/12/18_resume2_deployment.json)。perf version 6.12.80、退出0；其余record均在performance后，硬件cycles type0/config0，未回退软件事件。

ToS先推送并核对`280fbd41f8772491ebe784aa19a3caed3bb1e8b2e64daef1d2a5a284d1f38ad1`，再推BBB720/1080并核对各自原SHA；均位于`/opt/afdo_agent/media/`。官方来源、许可与转码参数仍见第3节和09_media.json，没有重新选择测试片段。ToS只完成校准（40,652目标样本），没有把它计作正式中档重复。

### 9.3 失败即停的拉回/删除与空间

新增`tools/profgen/pull_verified_run.py`：只接受确切的`/opt/afdo_agent/work/eval-*`目录；校验规范路径/无符号链接，取得全量板上SHA；pull到不存在的空目标目录；按SDB实际平铺路径核对文件集合及每个SHA；再确认远端清单未变；全部成功才删除**该清单对应的唯一RUN路径**并确认不存在。路径、传输、文件或哈希错误均在删除回调之前抛错。

正式使用前的主机小RUN演练：故意改坏一个文件，报`SHA/file-set mismatch; deletion forbidden: ['data.txt']`，删除回调次数0；正确对照删除回调仅收到确切模拟路径。没有用真实板上目录做破坏演练。[初次演练](evidence/12/16_transfer_injection.json)。随后8项主机回归全通过（坏SHA、缺文件、多文件、传输失败、符号链接、远端清单改变、成功、清单路径越界），见[测试和恢复](evidence/12/21_resume2_restore_and_checks.json)。

每次RUN先检查`available_bytes >= 2*RUN_ESTIMATE_BYTES+200000000`。先以小规模校准量体积，再按目标样本比例或完整解码次数估算，加30%和1MB余量；所有RUN逐批拉回/校验/删除，不并存大批原件。已观测最大估算95,268,541字节（高档Thumb spike），所需390,537,082字节，当时可用约1GB，门禁通过。该估算只用于已执行负载，**LOST未试采，不能复用正常采样估算宣称LOST空间足够**。

本轮16个RUN（9校准/流程、7正式）共 **1,394个板上文件** 全量验证后删除；原始perf.data合计33,754,308字节，完整文本/逐秒文件另存。主机完整原件、SHA receipts及manifest留`temp/board-round1-resume2/{runs,receipts}/`，关键文件SHA与路径见[逐RUN清单](evidence/12/19_resume2_runs.json)。没有仅保留抽样或过滤版导出。最后一个高档RUN的主机编排暂停后，板上仍正常完成，使用同一安全流程收回后才恢复状态；它没有被丢弃或冒充失败校准。

### 9.4 已完成数据、身份与环境（剔除前/后均列出）

| 正式对象/预算（第1次） | 目标样本 | 总样本行 | usable | profile身份 | perf/workload real秒 |
|---|---:|---:|---:|---|---:|
| spike Thumb低 | 21,561 | 21,581 | 14,846 | verified | 15.35 |
| spike A32低 | 21,347 | 21,363 | 21,291 | verified | 15.36 |
| libavcodec Thumb低/BBB | 36,155 | 44,194 | 21,532 | verified | 61.56 |
| spike Thumb中 | 106,875 | 106,948 | 72,762 | verified | 72.64 |
| spike A32中 | 106,567 | 106,605 | 106,287 | verified | 72.64 |
| libavcodec Thumb中/BBB（三次完整解码） | 108,145 | 132,654 | 64,928 | verified | 182.23 |
| spike Thumb高 | 426,661 | 426,784 | 未转换 | 未取得 | 286.56 |

共827,311条目标样本。低档libavcodec因一次完整解码超出2万，原件完整保留，不截取到预算。spike Thumb完成3/20、A32完成2/20，FFmpeg Thumb BBB完成2/20、ToS0/5、A32 BBB0/5；**正式频率中档0**（仅有频率校准），训练0/14，集成0/5。不是完成了每档5次。spike无明确冷热分布运行模式，原源码未改，区分度负对照未做。

6份正式质量报告均conversion=ok、verified；`coverage.name_merged_functions=0`，没有名单可列。Thumb spike ISA全Thumb，A32 spike全A32；FFmpeg低档Thumb36,138/A3217，中档Thumb108,058/A3287（主要PLT），未知ISA0。各层分解如下，完整period/normalized weight及top50留19证据：

| 正式对象/预算 | outside_dwarf_func | 其中in_cu_no_subprogram / plt / no_cu | in_func_no_line | unmapped_in_target |
|---|---:|---|---:|---:|
| spike Thumb低 / 中 | 0 / 0 | 全0 | 6,715 / 34,113 | 0 |
| spike A32低 / 中 | 0 / 0 | 全0 | 56 / 280 | 0 |
| FFmpeg Thumb低 | 10,903 | 10,886 / 17 / 0 | 3,720 | 0 |
| FFmpeg Thumb中 | 32,143 | 32,056 / 87 / 0 | 11,074 | 0 |

所有已转换S（包括校准）的raw目标计数与工具报告一致；采集保存maps及buildid-list并核对目标路径/ID。没有把工具JSON中的event.type=unknown（文本本身无type）误当作硬件事件失败：type0/config0证据来自每份evlist。

逐秒原始观测：16个RUN最大温度63.296°C，全部pswpout增量0，观测频率均1,500,000kHz，未发现可读sysfs节流节点，throttling=unknown。**遗漏：脚本没有在每RUN开始前保存scaling_max_freq；停止时读得1,500,000不能补作采集前依据，因此频率合格性也记unknown。** 未改变预注册阈值。剔除前为上述7份；按预注册剔除异常及unknown后干净子集 **0份**，证据不足。保留全部数据，不作选择性丢弃。恢复前需补齐采集前policy边界记录。

本次设备操作20:44:52.452–21:17:16.417+08，**1,943.965秒（32分24秒）**，含预检/部署/主机分析/拉回/恢复；16次实际perf/workload real合计967.27秒，正式7次合计706.34秒。资源按600秒后台记录；最终停止/恢复也有记录，原始时点见21证据，不将这些耗时视为优化性能测量。host控制进程一次因读取JSON字段路径写错（sample_count实际在counts下）失败，已finally恢复；修正的是临时编排，不是LLVM；该轮仅校准，另起formal2，没有覆盖原失败日志。

### 9.5 阻塞证据：真实 avg 无法通过，不清位、不过滤

按预注册选第一份成功中档Thumb/BBB原始完整导出：

```text
temp/board-round1-resume2/runs/formal2-ffmpeg-thumb-S-sample-fixed-bbb-100000-r1-s1/perfscript.txt
SHA256 5732dce25be037de92dd08f00e1e6adfabd6c1577532a0db545e476554d52405
```

正式工具SHA仍`334a09290f53eb4c793ae91759f2b6344a36e63317820eb9151771b262dc3f30`，匹配runtime/debug的build-id `e7de4d8c9560442994341d9bfc5dfd06ae641a17`。使用原始输入分别生成text的sum/max/avg，仅aggregation及输出路径变化；完整命令、RC、stderr、失败JSON与GNU证据见[20_real_avg_boundary_stop.json](evidence/12/20_real_avg_boundary_stop.json)。sum=0、max=0、avg=1；avg.text未创建，失败报告conversion=failed、failure_stage=boundary，身份仍verified：

```text
llvm-profgen: error: IP sample mode: failure_stage=boundary
  range starts inside a Thumb instruction (function=__divsi3 address=0x3421a1 DWARF=[0x3421a1,0x342435))
  range starts inside a Thumb instruction (function=__udivsi3 address=0x341f29 DWARF=[0x341f29,0x342185))
```

不是部署错ID，也不是perf样本带bit0。GBS GNU readelf原文显示：

| 函数 | DWARF low_pc / high_pc长度 | GNU objdump首条指令 | 原导出落在该DWARF范围的样本 |
|---|---|---|---:|
| __udivsi3 | 0x341f29 / 604字节 | 0x341f28: `1e4a subs r2,r1,#1` | 1 |
| __divsi3 | 0x3421a1 / 660字节 | 0x3421a0: `2900 cmp r1,#0` | 5 |

两CU的low_pc本身分别为偶数0x341f28、0x3421a0；子程序low_pc却为奇数。来源`../../../libgcc/config/arm/lib1funcs.S`，producer **GNU AS 2.43**，comp_dir指向平台gcc-14.2.0/libgcc构建。该绝对comp_dir只是ELF内字符串，没有读取工作目录之外文件。GNU原文文件`temp/board-round1-resume2/gnu/debug-info.stdout:2228042–2228087`，符号表与反汇编同目录，证据20附原文和行号。

实现 `ProfiledBinary.cpp:1028–1061`原样接收DWARF ranges；`IPBoundary.cpp:169–192`从Thumb映射锚点按编码长度步进，不能恰好到达奇数起点，故按冻结5.7.2失败。冻结5.7.2第7条明确样本PC不清位、符号表Thumb地址规则，并说DWARF表示由lit核对；**此前素材未覆盖这类GNU AS子程序的带位地址**。[源码与设计原文](evidence/12/23_stop_scope_and_nonleaf.json)

这是本轮发现的**真实输入兼容性阻塞**：当前严格拒绝符合既定边界规则，但平台真实DWARF表示尚无获准的规范化规则。不能未经裁决就把所有奇数DWARF起点清零（会掩盖合法负对照），也不能忽略有样本的运行库函数、只输出容易通过的热点子集。按停止条件暂停后续采集与主机验收，未改LLVM、未改设计、未过滤原始输入。

候选后续处理，**均未实施**：

1. 明确设计/实现对GNU AS Thumb DWARF地址的处理：用目标架构、对应Thumb函数符号、映射状态及原始DWARF形式共同证明后规范化函数区间；低地址及high_pc长度/绝对地址须区分，增加实际样例和原bad-thumb-start负对照。先裁决规则，再授权修补和重验，不能直接无条件`&~1`。
2. 从平台libgcc的调试信息生产端修正，重建匹配运行/调试产物并重新采样；本轮不构建或替换平台库，不篡改同ID的debug来假装原件。
3. 若决定继续保留严格拒绝，则明确本构建avg/补零/prev-inst不可用，调整后续评估范围须由用户决定；不能宣称真实avg挂账已关闭。

前三个热点仍是decode_cabac_residual_nondc_internal、ff_h264_decode_mb_cabac、loop_filter的唯一内部链接名，没有换函数。但全输入avg失败，故**逐键GNU n(k)/avg验收未完成**。GNU addr2line读取合成runtime+debug时另有`DWARF error: mangled line number section (bad file number)`原警告，留证23，尚未判明影响；不能拿共享LLVM symbolizer冒充独立GNU证明。独立核对脚本草稿留temp、不作为已验收工具提交。

### 9.6 非叶子line0、未完成项与下一步输入

停止前只做过固定间隔FFmpeg Thumb**校准**的隐藏诊断：`usable_nonleaf_line_zero samples=29 period_sum=29000087`，usable21,736，比例0.133419%。不是正式矩阵汇总，不能据此决定处理规则；全部正式S总数/比例和涉及函数top20尚未统计，保持挂账。[原文与范围](evidence/12/23_stop_scope_and_nonleaf.json)

LOST压力/完整高丢样导出尚未采集，06挂账未关闭；真实avg未关闭。fork/exec/deleted/module/-1/-1集成未执行，不能沿用07/09旧结论冒充本轮验收。R/C/G5均未运行，无新profraw/profdata，不进行5.8质量分析、消费构建或收益比较。

下一步质量分析输入已具备：7份完整正式S原件、6份verified sum extbinary/JSON、每RUNmaps/ID/环境/输出SHA、9份明确排除的校准/流程原件；缺少余下63次正式采集、训练14次、LOST和5集成、全量nonleaf统计、avg独立核对。第7份高档原件未转换，正式repeat数远不足5，全部当前轮次的干净子集为空。恢复时不能覆盖这些原件或把校准并入正式重复。

### 9.7 停止与恢复

发现边界失败后，只暂停本任务host编排PID831123防止启动新RUN；正在录制的高档spike正常结束（板上record=0、ALL-END OK），未中断其负载。按全量SHA流程拉回并删除确切RUN后，向该host进程发送SIGINT/CONT，让其finally恢复；host标记：

```text
ALL-END 2026-11-05T21:17:16.417545+08:00 FAILED elapsed=1254.158
```

这里FAILED是整轮停止，不改写已成功录制的板上RUN状态。policy0逐值恢复`schedutil`并回读；root恢复off，uid5001；RPM **1232→1232**。全部16个本轮RUN有删除后不存在断言；停止前进程清单无本任务板上perf/负载，host编排随后已退出。[恢复/资源/测试](evidence/12/21_resume2_restore_and_checks.json)

`/opt`最初used161,020 / available1,144,596 KiB；结束used **282,072** / available **1,023,544 KiB**，22%。保留16变体、perf/libLLVM、脚本、三份视频及小型state文件供恢复；没有删除部署物腾空间，没有保留本轮RUN大数据。perf_event_paranoid/kptr_restrict未写。

待v0.8登记除9.1流程外：GNU AS Thumb子程序DWARF地址兼容性待裁决；未知节流/缺采集前policy边界仍按原预注册排除干净子集；nonleaf处理仍待完整数据。边界例外仍限用户授权root会话与governor sysfs设置/恢复，其他板上写入在opt；未读取其他主机项目输入、未扫描外部SDB状态，不声称不存在任何未观察的守护进程写入。未推LLVM/Gerrit，未改认证或索要密码，未开始Agent实现。

## 10. 恢复前主机核实：Thumb in_func_no_line 与预注册修订1

### 10.1 逐地址核对结论

本阶段未连接开发板。对前6份正式完整导出，用GNU readelf的可执行PT_LOAD独立换算全部目标地址，再查询平台LLVM symbolizer的原始内联栈，并对leaf line=0地址逐一检查 `llvm-dwarfdump --debug-line` 的原始相邻行区间（不跨end_sequence猜测最近行）。6份报告中的in_func_no_line **全部命中明确line=0**；没有“有正行号但符号化未查到”或“行表无覆盖行”的in_func_no_line样本。额外无覆盖的FFmpeg87/17条是PLT，属于原报告outside_dwarf_func，不混入本分类。各函数前20、占本分类/目标比例、热点地址、原始行表行号和命令见[24](evidence/12/24_line_zero_diagnosis.json)，GNU原文和汇编见[25](evidence/12/25_line_zero_raw_excerpts.json)。原始全量分析在`temp/round1-thumb-line0/`。

| 正式对象 | 低档line0/target | 中档line0/target | 判定 |
|---|---|---|---|
| spike Thumb | 6715/21561 | 34113/106875 | 全部明确line0 |
| spike A32 | 56/21347 | 280/106567 | 全部明确line0 |
| FFmpeg Thumb | 3720/36155 | 11074/108145 | 全部明确line0 |

spike Thumb中档的34,113条中，sort_block34,078（99.8974%）、run_workload31、hash_mix4。**单一地址0x1076a占33,856条**，GNU反汇编是`add.w r5,r0,r2,lsl #2`（内循环的地址计算）；原始行表在0x1076a–0x1076e写line0。GNU addr2line也返回该函数及`spike.c:?`，相邻指令行号67/68可解析。

A32同源sort_block的无行样本仅240条，中档总无行280；A32使用`ldr r5,[r4,r2,lsl #2]!`合并地址更新/加载，其0x10778起的行表为67，而Thumb独立add的编译器位置为0。不同机器指令与PC采样分布共同造成明显比例差异；不把它解释为Thumb源文件缺少32%的源码行。

为排除strip/debug拆分导致，使用原S构建完整flags（含-Os、profiling两项和对应ISA）与同一GBS Clang22.1.8，只额外改为输出汇编：Thumb在该add之前明确输出`.loc 1 0 0`，A32地址加载使用line67。未改源码/flags或重建替换评估RPM。构建命令与汇编行号留24/25。GNU探查7个Thumb地址、6个A32地址，leaf均无源码行，与原始line0一致，无GNU警告。

FFmpeg中档前5个受影响顶层函数及样本：ff_h264_filter_mb1650、decode_cabac_residual_nondc_internal1635、ff_h264_decode_mb_cabac1485、hl_decode_mb_simple_8 1254、fill_decode_caches869（完整唯一链接名与前20见24）。60个抽查地址GNU addr2line均返回leaf未知行，原始行表为0；有些祖先调用点仍有正行号，冻结规则仍按**叶子**line0排除，不提升成祖先可用样本。A32 FFmpeg没有正式数据，本轮只用既有排除的校准作诊断性同函数对照：3807/36553也全为明确line0，不能把它当正式配置质量比较。GNU在FFmpeg查询仍有bad-file-number警告；原文保留，未将GNU警告隐去，后续avg须定位其CU和影响。

**原因与质量影响：**本次高比例来自编译器当前优化/指令选择明确生成的line0，加上热点PC分布；不是缺行表或profgen漏查正行号，第一阶段停止条件未触发。规则保持：这些样本不进入body/total，不能补一个邻近行来提高usable。相同target预算不代表Thumb/A32有同量usable信息；后续须并列展示target、usable、各层剔除与函数集中程度，可能需要更多采集，但本轮不改预算、阈值或行0处理。这里只排查调试信息，不作统计质量/性能收益比较。

### 10.2 预注册修订与旧数据判定

新增[preregistration_amendment1.md](../eval/preregistration_amendment1.md)，原7d3d9d9文件逐字节不变。依据用户裁决：恢复采集前单独提交推送；用同负载树perf stat的cycles/task-clock计算有效频率，≥固定频率97%、逐秒频率等于固定值且温度低于原阈值，才写“未观察到节流”。开始/结束均保存每policy四项频率/调速字段。读不到固件节流节点单独保留unknown，不单凭此剔除满足新判据的轮次。无效/缺计数、multiplex或缺CPU时间保持unknown。

修订前7份正式数据均没有匹配的精确cycles总计数/task-clock，不能把采样period和当作counter；按同一修订仍全为unknown，原件不改，干净子集0。修订写明发生于任何配置间结果比较前，列出全部7份名称与样本数。ε、预算、次数、bootstrap等其余条款不变。恢复前将补录policy边界并加入同负载stat。

### 10.3 待设计v0.8登记与阶段状态

- 本轮裁决授权补丁8：仅IP、ELF32小端EM_ARM，奇数DWARF下界在清bit0后映射状态为$t时，两端清bit0；统一影响归类及边界枚举，样本PC不清位。此前9.5的待裁决已获得此明确规则；本阶段尚未修改LLVM。
- 补丁8须新统计/告警/schema/lit及正式GBS/C1/14导出验收，不以本次line0排查替代。
- 当前第一项核实通过，原始证据及预注册修订先提交；板上剩余采集、补丁8与后续avg/LOST等还未在本阶段开始。板上恢复前预计另需约4–5小时（依据已有每档耗时及拉回开销估算，样本不足会增加分段）；将继续单板串行，不重采覆盖旧7份。


## 11. 修订1后恢复、补丁8符号化阻塞及掉线收尾（2026-11-05）

### 11.1 开始顺序与修订记录

第10节的六份正式 in_func_no_line 排查通过后，先提交并推送预注册修订 **`6629b2e5a1bbc12073748fc01c12a5af04b34352`**，再启动新采集。原 `7d3d9d9` 和文件逐字节不变。没有做配置间质量/性能比较；此前7份原件按修订仍全为 unknown：缺精确cycles及对应CPU时间，不能用采样period总和反推或补造频率边界。

本次身份Pi4/armv7l/rpi4-v7l通过，25项系统依赖（新增getconf）在非root下全部通过；原uid5001。root开启后复验既有部署文件SHA、部署新版3脚本并核SHA、复验三视频SHA、perf --version成功，再把policy0从schedutil设为performance。每RUN前后增加governor/min/max/cur，S采样的同一负载树由内层 `perf stat -x ';' -e cycles,instructions,task-clock` 记录精确周期与CPU时间。外层record参数与目标预算不变。

[依赖、脚本SHA/bash-n和8项拉回回归](evidence/12/29_amendment1_checks.json)、[全部操作原文](evidence/12/27_amendment1_operations.json)。原坏哈希注入证明不删除的证据16保留，本次8项主机回归仍通过。未安装工具、未改sysctl、未重启/remount/装卸RPM。

### 11.2 新增完成数据与空间

| 新RUN | 目标样本/全部样本 | 用途与修订资格 | 拉回/清理 |
|---|---:|---|---|
| pilot-effective-frequency | 2238/2329 | 排除校准；有效频率1.497362GHz，最高56.478°C，swapout0，逐秒1.5GHz、边界不变 | 全量SHA后删除 |
| spike A32 fixed高档 r1 | 431793/432014 | 正式；有效频率1.497442GHz（门槛1.455GHz），最高59.400°C，swapout0；计数100%运行，逐秒1.5GHz且前后边界不变，未观察到节流 | 全量SHA后删除；323.161秒，64,346,455字节 |
| FFmpeg Thumb BBB fixed高档 r1 | 未取得完整导出，不能报样本数 | 12次解码期间SDB断开；排除、不补入矩阵 | 留板，不删除，见11.3 |

实际空间门禁：pilot可用1,043,836,928字节、要求204,000,000；A32高档可用1,043,767,296、估算93,159,253、要求386,318,506；FFmpeg高档可用1,043,283,968、估算119,445,465、要求438,890,930。均满足2×估算+200MB；不是空间不足停止。未删除变体或工具腾空间。[逐RUN统计/资格](evidence/12/26_amendment1_resume_stop.json)、[已完成RUN全量文件SHA与删除收据](evidence/12/28_amendment1_transfer_receipts.json)。

累计正式完成 **8/70**，目标样本 **1,259,104**：spike Thumb低/中/高各1，spike A32低/中/高各1，FFmpeg Thumb BBB低/中各1。频率、ToS、FFmpeg A32均0；训练0/14，LOST0，集成0/5。旧9份排除原件不变；本轮pilot与不完整FFmpeg另列排除，不覆盖旧文件。旧6份质量报告verified/name_merged_functions=0；旧高档Thumb与新高档A32仅原始数据，补丁8未通过，未新生成质量报告，不冒称新增转换verified。

### 11.3 两项独立停止事实与恢复

1. 主机补丁8最小GNU AS测试发现：规范化函数区间后，首指令0x1000仍在共享符号化器中返回正行号9、无效函数名，被现有空链分类写为in_func_no_line。人工total60，草稿sum/max/avg为50。已触发停止条件，写STOP_REQUESTED，要求当前RUN完成拉回后恢复；没有开始下一RUN。证据与候选方案见[补丁8报告](13_patch8_thumb_dwarf.md)。
2. 22:33:34主机侧SDB出现 `target offline`。当时FFmpeg没有返回真实RECORD_EXIT；拉回尚在规范路径读取阶段就失败，未执行删除，自动governor/root恢复也失败。约后续重连成功，三项身份与同一uname-v再次断言通过，uptime继续增长，未发现重启证据；未发现残余perf/gst-launch/本轮采集进程。

掉线RUN中 `record.stderr` 原文有 GStreamer `Broken pipe`，`perf-stat.csv` 与decoded.sha256为空，严格导出/evlist/buildid-list均未完成。EXIT trap却记录 `EXIT 0 / ALL-END ... OK`，这一标记不能代替缺失的真实record返回码与必需产物：本轮明确判失败。可能涉及断连信号收尾，未做影响其他进程的实验；**再次恢复前须修正HUP/中断的失败标记门禁**，不得按该伪成功标记纳入矩阵。

仅尝试只读归档不完整目录：uid0下 `sha256sum .../perf.data` 返回 `Permission denied`，清单校验拒绝，因此不拉取、不删除、不改权限绕过。失败原文与ROOT恢复操作在证据27，摘要在证据26。不完整文件留在：

```text
/opt/afdo_agent/work/eval-20261105T232305-7773
```

再次恢复governor并回读schedutil，然后root off并回读uid5001；RPM1232不变；最终 `/opt` used **307868KiB**、available **997748KiB**（24%）。没有以清理不完整RUN来掩盖失败。后台worker状态 `ALL-END FAILED elapsed=1033.162`；恢复归档状态也为FAILED（SHA归档失败），但root/governor恢复经最终回读确认成功。本次从首次身份查询到最终恢复操作约 **1695.053秒**（28.25分钟，含预检/部署/安全收尾），不把它全算负载运行时间。主机与板子时钟约差1小时且板子+0900，保留原始时间/uptime，不按墙钟差猜重启。

### 11.4 本阶段结果与下一步输入

大文件仍在 `temp/board-round1-amend1/`（完成的pilot、A32高档和SHA收据）、`temp/board-round1-resume2/`（旧7正式及9排除原件）。原始完整清单和脚本命令均留存。主机stage1排查数据在 `temp/round1-thumb-line0/`。不完整FFmpeg只有板上原件与主机命令/失败清单，**没有主机完整perf.data副本**。

真实avg与LOST挂账均未关闭；GNU bad-file-number的CU定位待真实avg续做。全体正式nonleaf line0/top20未完成，不能把旧排除校准的29/21736（0.133419%）当成正式汇总。5个集成用例未执行，无新结论；R/C/G5训练及profdata合并未做。

待设计v0.8登记：修订1有效频率资格规则；Thumb普通line0证据及不同ISA的target/usable差异；补丁8区间规范化裁决；新发现的“正行号但缺函数名”符号化契约需决定，尚未自行扩充冻结规则。执行流程还需修复SDB中断的trap伪成功；失败清单不得触发删除。本轮无需任何新权限、凭据或安装；正式工具/设计未改，未推LLVM/Gerrit。


## 12. 补丁8完成后的主机验收与中断RUN恢复

补丁8已正式验收并由结果仓库提交41e0be8归档；LLVM提交、新工具SHA、正式GBS/lit/C1与14份旧导出重放见[报告13第6节](13_patch8_thumb_dwarf.md)。本节不覆盖旧7份/9份排除原件；第8份A32高档也保留原件，新产物另存temp/board-round1-patch8/converted。

### 12.1 八份已完成正式S的重转换

正式新工具SHA `41440292c7cf3a380a6779dfea6d06ff74a22e18537127561829bf989bb16413`。8份全部conversion=ok、identity=verified、name_merged_functions=0；目标样本仍合计1,259,104，usable合计1,023,185。[逐RUN命令、身份、各层计数、ISA、区间/别名与SHA](evidence/12/30_patch8_reconversion.json)。

| RUN | target | usable | in_func_no_line | outside_dwarf_func | 规范化区间/别名查询 |
|---|---:|---:|---:|---:|---:|
| formal2-ffmpeg-thumb-S-sample-fixed-bbb-100000-r1-s1 | 108145 | 64929 | 11074 | 32142 | 33 / 2 |
| formal2-ffmpeg-thumb-S-sample-fixed-bbb-20000-r1-s1 | 36155 | 21532 | 3720 | 10903 | 33 / 1 |
| formal2-spike-a32-S-sample-fixed-bbb-100000-r1-s1 | 106567 | 106287 | 280 | 0 | 0 / 0 |
| formal2-spike-a32-S-sample-fixed-bbb-20000-r1-s1 | 21347 | 21291 | 56 | 0 | 0 / 0 |
| formal2-spike-thumb-S-sample-fixed-bbb-100000-r1-s1 | 106875 | 72762 | 34113 | 0 | 0 / 0 |
| formal2-spike-thumb-S-sample-fixed-bbb-20000-r1-s1 | 21561 | 14846 | 6715 | 0 | 0 / 0 |
| formal2-spike-thumb-S-sample-fixed-bbb-400000-r1-s1 | 426661 | 290816 | 135845 | 0 | 0 / 0 |
| spike-a32-S-sample-fixed-bbb-400000-r1-s1 | 431793 | 430722 | 1071 | 0 | 0 / 0 |

FFmpeg两份各有33个GNU AS规范化区间（含别名DIE，不是33个互不相交的函数）；spike六份均为0。中档别名地址0x341f28→0x341f29（__udivsi3）与0x342434→0x342435（原查询误归__divsi3，正确为__aeabi_idivmod），低档只触发后者；三次叶子文件/行/discriminator全部一致。中档usable较补丁7增加1、outside减少1；低档分类总数不变，但相邻函数首地址归属纠正。范围名单含__divsi3，即使该份sum未采到其首地址也记录规范化事实。旧高档Thumb与新高档A32此前未转换，没有伪造旧值对比。

### 12.2 真实avg独立核对闭合

保持原选中的中档BBB Thumb RUN和前三热点：decode_cabac_residual_nondc_internal、ff_h264_decode_mb_cabac、loop_filter（完整唯一链接名见证据）。GNU objdump提取1892、8457、1176个起点，合计11,525；715个有样本聚合键（51/495/169）。GNU addr2line负责叶子行表，GNU readelf负责DIE范围、声明行与内联调用点的call_line/GNU_discriminator，独立计算n(k)、duplication和分子，再按设计取整。sum/max/avg每种715键，键集合双向相等、数值差异0。**关闭真实avg上板核对挂账**，不把本次输入外的函数或无样本键纳入这项结论。[逐键手算数据、原始工具命令位置、耗时/RSS](evidence/12/31_real_avg_independent.json)，[独立计算脚本](evidence/12/36_inline_keys_formal.py)。

GNU bad-file-number警告并非三个热点CU损坏：原ELF377个CU中52个为DWARF5汇编CU；临时诊断副本逐一只保留一个原始CU（清除过期debug_aranges），52个各复现一次告警，均为文件表从0编号的汇编CU。热点所属h264_cabac.c/h264_slice.c（DWARF4）单独查询无警告，原文件不修改。GNU rawline及LLVM原始行表均可列出这些汇编条目；本次715键计算没有借用LLVM symbolizer或dwarfdump补值。逐CU原文留temp/profgen-patch8/independent-avg/cu-isolation.json，CU清单和原文摘录见证据。诊断中还发现GNU addr2line把叶子discriminator重复打印到祖先帧，不能直接当调用点discriminator；以GNU readelf的原始DIE调用点属性独立构造键后才进行验收，未按profgen输出反抄。

### 12.3 非叶子line0（当前八份，不代替未完成矩阵）

usable_nonleaf_line_zero合计88：中档FFmpeg67、低档FFmpeg21，其余6份spike为0；占target 0.0069891%，占usable 0.0086006%。按顶层函数汇总：ff_h264_decode_mb_cabac 82、ff_h264_filter_mb 5、ff_h264_queue_decode_slice 1（不足20项则全部列出）。另存实际line0帧函数与地址，使用同配置DWARF-only查询对照正式工具诊断，计数一致。这里只报告观测，处理规则仍待PM决定。[分解](evidence/12/32_formal_nonleaf.json)、[诊断源码](evidence/12/36_nonleaf.cpp)。

### 12.4 中断目录安全收尾与继续采集

新一轮身份/内核断言通过，非root依赖全部通过后开root。重新读取原不完整目录`/opt/afdo_agent/work/eval-20261105T232305-7773`：本次SHA可读，599文件拉回、主机全量SHA与文件集合一致、再读板上清单一致后，才删除该确切目录。标为“中断，不计入正式矩阵”；旧ALL-END OK仍不作为成功证据。[收尾结果](evidence/12/33_partial_run_recovery.json)、[原始操作](evidence/12/34_partial_run_operations.jsonl)、[599文件SHA收据](evidence/12/35_partial_run_receipt.json)。此预检阶段40.406秒，未改governor；root恢复uid5001，schedutil、RPM1232；/opt used293332KiB、available1012284KiB。

HUP/TERM/早退收尾修复：只有finish_run完成且run_complete=1才能写OK，提前exit0也变为退出1/FAILED；5项信号/退出模拟全部通过。SHA清单改为find批量-exec，使子进程sha256sum失败传播为非0，避免分号形式的find掩盖读失败；9项主机拉回门禁回归通过（含坏哈希不删除与清单SHA命令失败）。[门禁证据](evidence/12/37_recovery_gates.json)。

恢复剩余矩阵前再次核对已部署文件/脚本/三视频SHA，性能采集仍在performance设置后执行；长高档预算按每段最多约15万目标样本、FFmpeg最多3次解码分段累计，逻辑预算和5次独立采集不变。预计剩余板上4–5小时；运行于temp/board-round1-patch8/worker.py，600秒资源记录，原8份逻辑组不重采。当前正在恢复，最终结果/恢复状态在下一节续记；不把当前运行状态写成最终完成。

### 待设计v0.8登记（本次执行流程补充）

同指令别名与一致性失败契约见报告13；真实avg独立验收已通过。断线RUN收尾必须以真实退出码和全量核验为准；SHA子命令失败须透传，任何提前退出不得写OK。分段只用于空间/连接稳定性，不改变预注册预算、ε、轮数或异常判据。


## 13. 补丁8正式工具恢复采集；第二次远端清单退出码缺失后停止（2026-11-06）

本节覆盖补丁8通过后的实际恢复阶段，保留上述历史停止记录。LLVM工具仍为补丁8 `cd5168c48b5422a50829259fd43e84cc3edd6694`，SHA-256 `41440292c7cf3a380a6779dfea6d06ff74a22e18537127561829bf989bb16413`。本节不改LLVM源码、设计v0.7、预注册7d3d9d9或修订1；未推LLVM/Gerrit。本轮板上工作**已停止并恢复权限/频率**，不是仍在后台运行。

### 13.1 实际执行与完整性门禁

开始2026-11-05T23:48:02.716357+08:00，结束2026-11-06T01:34:01.039490+08:00，6358.323秒（105.97分钟），`ALL-END FAILED`。此前处理旧中断RUN的40.406秒另见第12节，不混入矩阵时间。旧8组、9份排除原件及pilot2238原样保留；本次新增27个完整逻辑组、46个物理RUN、4,652,796个目标样本。合计35/70组、54份完整S导出；三档预算是目标样本门槛，逐组实际数量见证据，未宣称精确等于20k/100k/400k。高档采用短RUN分段累计，同一逻辑组的所有分段一起作为一个独立重复，不把分段充当独立次数。

恢复前确认唯一RPi4、armv7l、6.12.80-arm-rpi4-v7l，uname-v仍为`#1 SMP Wed Nov  4 17:05:36 UTC 2026`。非root下25项系统命令预检通过，root下重核已部署目标/工具/视频SHA；perf版本成功后才设置performance并采集。Tears of Steel沿用先前已推送片段，恢复时重新SHA核验，并未换素材。每RUN包含内核指纹、CPU策略边界前后值、每秒环境、真实退出码、完整perf.data/script/buildid-list/evlist/stderr；完整导出不截断。spike只支持rounds/seed，未提供独立热点分布模式，因此不改源码、不构造区分度负对照。[命令及root顺序](evidence/12/46_board_operations.jsonl)、[逐RUN收据、环境与资源](evidence/12/48_runs_receipts_resources.json)、[执行脚本](evidence/12/47_matrix_worker.py)。

每次要求可用空间≥2×依据已观测体积估计的产物+200MB；单次FFmpeg至多3次完整解码、spike分段以约150k样本上限估算，最后以实际目标计数累加。本次46份完整RUN共819,178,797字节，均完成拉回、全量本地SHA、第二次远端SHA复查后删除确切目录。第一次失败注入与14项流程回归仍见第12节，未取消门禁。主机每600秒free/uptime，板上同步free/uptime/df：主机available最低19293MiB、load1最高1.22；板上available最低1292MiB、load1最高1.48；本次完整RUN最高61.348°C、最大换出增量0。[资源原文](evidence/12/45_resources.jsonl)

### 13.2 停止原因及未删除RUN

停止位置：`spike-a32-S-sample-fixed-bbb-100000-r3-s1`，板上目录`/opt/afdo_agent/work/eval-20261106T023250-25276`。该采集本身RECORD_EXIT=0、ALL-END OK；SDB workload传输退出0。但**拉回后的第二次远端清单复查没有返回`__RC=<真实退出码>`**，`SDB.shell`据此抛错，完整流程未通过。不是已证明的哈希不一致，也没有证据确认发生了SDB断连；不得把缺失退出码当成0。

主机只读复核：首次清单99文件，本机99文件全部SHA相同；第二次stdout也含相同99个SHA条目（共100行含末尾空行），但缺少退出码标记。主机副本共15,931,283字节，位于`temp/board-round1-patch8/runs/spike-a32-S-sample-fixed-bbb-100000-r3-s1/`；没有完成收据，板上目录**未删除**，该槽位**未计入正式矩阵**。没有重读远端清单、没有重试采集、没有旁路清理。即时进度曾误称“尚未拉回”，随后根据本机落盘证据更正为此处的第二次复查失败。[原始stdout](evidence/12/44_failed_manifest_stdout.json)、[原始采集命令/退出码](evidence/12/44_pending_command.json)、[只读分析](evidence/12/44_transfer_stop.json)、[真实失败状态](evidence/12/45_matrix.status.txt)。

根因目前未知：现有SDB包装器在该分支只把stdout纳入异常，未保存这次调用的stderr，不能据此断言是权限、设备掉线或SDB输出截断。候选后续处理：完整保存该层command/transport_rc/stdout/stderr与退出码包络，再经重新身份断言和两段预检读取保留RUN清单，严格完成全流程才决定删除/重采。不得省略退出码校验或仅凭这99条哈希删除。当前停下等待指示，未自行修复包装器或恢复板上操作。

旧的`eval-20261105T232305-7773`不同于本次保留目录：它已在第12节按root下599文件全量核验完成恢复和删除，并被标为中断排除；对应的Thumb FFmpeg第一轮高档已重新采到436,016目标样本。

### 13.3 采集矩阵与资格（剔除前/后并列）

以下均为已完成逻辑组，要求每行最终5组，目前仍不足；“干净”仅依修订1的环境判据，不代表配置效果。原7份缺精确cycles/task-clock，仍unknown；第8份A32高档按修订为clean。当前35组：13 clean、12 abnormal、10 unknown；完整集目标5,911,900，干净子集目标1,991,272。没有做配置间质量或性能比较，未放宽任何阈值。

|配置 / 事件模式 / 输入 / 预算|完成组/5|目标样本（完整集）|usable|clean / abnormal / unknown|干净子集目标样本|
|---|---:|---:|---:|---:|---:|
|ffmpeg-a32-S/sample-fixed/bbb/100000|2/5|220,591|134,009|0 / 2 / 0|0|
|ffmpeg-thumb-S/sample-fixed/bbb/100000|2/5|216,903|130,687|0 / 1 / 1|0|
|ffmpeg-thumb-S/sample-fixed/bbb/20000|3/5|108,994|64,957|0 / 2 / 1|0|
|ffmpeg-thumb-S/sample-fixed/bbb/400000|3/5|1,306,838|783,523|0 / 3 / 0|0|
|ffmpeg-thumb-S/sample-fixed/tos/100000|2/5|243,729|140,645|0 / 2 / 0|0|
|ffmpeg-thumb-S/sample-freq/bbb/100000|2/5|216,808|129,854|0 / 2 / 0|0|
|spike-a32-S/sample-fixed/bbb/100000|2/5|214,160|213,601|1 / 0 / 1|107,593|
|spike-a32-S/sample-fixed/bbb/20000|3/5|64,211|64,043|2 / 0 / 1|42,864|
|spike-a32-S/sample-fixed/bbb/400000|3/5|1,244,259|1,241,072|2 / 0 / 1|838,921|
|spike-a32-S/sample-freq/bbb/100000|2/5|225,280|224,770|2 / 0 / 0|225,280|
|spike-thumb-S/sample-fixed/bbb/100000|3/5|320,869|218,658|2 / 0 / 1|213,994|
|spike-thumb-S/sample-fixed/bbb/20000|3/5|64,503|44,257|2 / 0 / 1|42,942|
|spike-thumb-S/sample-fixed/bbb/400000|3/5|1,238,707|846,447|1 / 0 / 2|406,003|
|spike-thumb-S/sample-freq/bbb/100000|2/5|226,048|154,128|1 / 0 / 1|113,675|

所有新FFmpeg完整RUN的有效频率低于固定1.5GHz的97%门槛（1.455GHz），即使瞬时频率1.5GHz、温度低于75°C、换出0，也按既定判据列abnormal，不改判干净。3个新物理RUN的逐秒传感记录存在不完整观测，按unknown保留。组内任一异常则组异常，否则任一unknown则组unknown。物理RUN分类为20 clean/23 abnormal/3 unknown，与逻辑组数量不同。原始SHA、环境、判定理由及分段映射见[完整矩阵](evidence/12/40_matrix_summary.json)、[逐RUN收据](evidence/12/48_runs_receipts_resources.json)。

### 13.4 补丁8真实转换、别名及归类变化

54/54正式物理S导出转换成功，全部verified、`coverage.name_merged_functions=0`；target=5,911,900、usable=4,390,651。各层排除、outside_dwarf_func子类、ISA计数、每RUN质量报告位置与SHA均在[矩阵证据](evidence/12/40_matrix_summary.json)。频率模式额外生成period权重profile，显式P_ref=1000003，与sample权重各自保留，未进行配置间评估。

spike Thumb/A32均0规范化区间；FFmpeg Thumb与A32运行文件均有33个规范化DWARF区间（包括libgcc的Thumb子程序，即A32业务构建也不意味着所有依赖都是A32）。完整33项原始/规范化范围按variant登记于证据。实际sum转换共33次别名查询，33次叶子文件/行/discriminator一致，无一致性失败；这些是不同转换中的查询次数，不是33个唯一地址。

|目标|A → A+1|查询次数|修正身份|
|---|---|---:|---|
|FFmpeg Thumb|0x341f28 → 0x341f29|14|原无函数身份 → __udivsi3|
|FFmpeg Thumb|0x342434 → 0x342435|16|原__divsi3 → __aeabi_idivmod|
|FFmpeg A32|0x4509f0 → 0x4509f1|1|原无函数身份 → __udivsi3|
|FFmpeg A32|0x450efc → 0x450efd|2|原__divsi3 → __aeabi_idivmod|

全部54份另用存档补丁7工具作同输入对照：24份profile变化；15份分类变化，合计28样本从in_cu_no_subprogram/outside_dwarf_func移入usable；其余为函数归属改变而分类总量不变。将两边extbinary经GBS llvm-profdata规范化为text后逐函数比较，变化**仅**涉及__udivsi3（15份）、__divsi3与__aeabi_idivmod（各18份），与首指令/相邻函数修正一致，未发现其他函数变化。[逐份分类与命令](evidence/12/42_patch7_formal_comparison.json)、[全部函数差异](evidence/12/43_profile_function_changes.json)。这与正式验收的14份历史整份导出profile逐字节不变是不同数据集，不混为一谈。

### 13.5 avg、LOST、非叶子line0与未执行项

真实avg挂账已按第12节关闭：同一中档BBB Thumb采集、原3热点、GNU独立11,525指令/715键，sum/max/avg逐键零差异；GNU的52个bad-file-number告警定位于DWARF5汇编CU，不影响3热点所在DWARF4 C CU。没有为本次停止重做或修改规则。

当前54份S导出未出现LOST记录。不能把无LOST文本中的L当成已证明0；工具报告保持unknown。压力采集未启动，06完整高LOST挂账**未关闭**。

非叶子line0统计已覆盖当前全部54份S（不是完整计划70组）：1,371样本，占target的0.0231905%、占usable的0.0312254%。独立逐地址帧明细与工具诊断计数逐RUN一致；此处辅助符号化只用于定位统计，不冒充avg的GNU独立核对。

|顶层函数|涉及样本数|
|---|---:|
|ff_h264_decode_mb_cabac|1282|
|ff_h264_filter_mb|82|
|ff_h264_queue_decode_slice|4|
|ff_h264_decode_ref_pic_list_reordering|2|
|ff_h264_decode_ref_pic_marking|1|

仅5项，未凑足20。涉及的具体零行帧及原地址在[全量明细](evidence/12/41_nonleaf_final.json)，处理方式仍交PM裁决。本轮未改非叶子line0规则。

R/C/G5训练0/14，暂无本轮stage profdata可合并；未把setup原件算作训练。fork、exec、deleted、模块、系统级-1/-1集成0/5，未把07/09旧内核样例当作本轮验收。热点分布负对照因spike没有独立运行模式未执行。集成/LOST脚本、期望、按实测体积选择压力规模的控制器草稿保留`temp/board-round1-patch8/{extras.sh,extras_worker.py,extras_convert.py,integration-expectations.json}`，未部署/执行；附加依赖草稿为`common-extras-draft.sh`，不能当作已通过的预检。项目已跟踪board脚本保持本轮开始版本；未提交这些未执行草稿。

### 13.6 恢复、待设计v0.8登记与下一步输入清单

finally回读policy0=schedutil，sdb root off后uid5001；RPM1232→1232。结束/opt used304988KiB、available1000628KiB（含未删除失败RUN）；开始used293588KiB、available1012028KiB。后续仅一次非root只读身份/进程核对，同一型号/架构/内核、无/opt/afdo_agent任务进程。三个主机后台worker已退出，后续串行器因matrix FAILED未启动extras。[恢复](evidence/12/45_governor_restore.json)、[最终df/RPM](evidence/12/45_final_board.txt)、[进程原文](evidence/12/45_processes_after_stop.txt)。无本轮新增已知工作目录边界例外；root/governor为已授权状态改动且已恢复。

**待设计v0.8登记（执行流程）**：沿用两段预检与性能状态顺序；任何传输步骤缺真实退出码即停，即使当前可见SHA全匹配也不能跳过完整门禁。没有把此门禁失败解释为llvm-profgen缺陷或放宽身份/地址规则。同指令别名规则及本轮真实修正事实见报告13，需下一轮外部评审。

**下一步质量分析输入清单**：

- 完整逻辑组/分段/资格映射：证据40；新46物理RUN与原8份分开存放，receipt与关键原件SHA见证据48；新原件在`temp/board-round1-patch8/runs/`，原8份位置沿第12节。
- 正式补丁8profile/quality/完整诊断及频率period变体：`temp/board-round1-patch8/converted/<RUN>/`；每份身份、target/usable、ISA与quality SHA见证据40。P7对照与逐函数变化见证据42/43，不作为配置间性能比较。
- 每秒原环境、频率前后界、cycles/task-clock、校验和、核验后的完整perf.data/script/buildid-list保留在各RUN。旧7份修订资格仍unknown；不得补造频率记录。
- 尚缺35个正式逻辑组、14训练、LOST压力、5集成；保留的新失败RUN先按明确授权完成退出码/完整性核验再处置。续跑必须使用新阶段目录并显式排除这35组，**不能原样重跑当前worker覆盖清单或重复槽位**。
- 独立avg结果与GNU CU诊断见第12节；非叶子line0规则待PM。本轮不进行5.8质量比较或消费构建。因停止条件生效，等待后续指示。
