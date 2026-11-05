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
