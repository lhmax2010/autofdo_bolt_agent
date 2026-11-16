# M1 手动试跑：RPi4 Thumb（2026-11-16）

## 1. 当前结果：连接阶段停止

本轮目标是复用 FIX1-J2 Thumb RPM，完成三次训练采集、六份 profile 合并、AutoFDO 消费构建及正确性与性能检查。尚未进入上述步骤：已登记的 RPi4 端点无法连接，无法完成用户要求的身份比对，因此停止，不把 SDB 进程退出码 0 当作连接成功。

原始证据：[连接输出](evidence/05/connect.json)、[设备列表](evidence/05/devices.json)，[SHA 清单](evidence/05/sha256.json)。命令在 WORKDIR 中以 nice 19、ionice -c3、systemd 用户 scope（3G/200%）串行执行，TMPDIR 指向 WORKDIR/temp/tmp。

```text
sdb connect 192.168.108.26:26101
stdout: error: failed to connect to remote target '192.168.108.26'
stderr: （空）
进程退出码: 0

sdb devices
stdout: List of devices attached
       （没有设备）
stderr: （空）
进程退出码: 0
```

时间与完整 argv 见连接 JSON。仅尝试连接一次，未查询其他地址、未查询 RPi5。

## 2. 身份与恢复

周六对照原件为 [2026-11-14 查询](evidence/02/board-check-02/queries.json)：

| 字段 | 周六记录 | 本轮 |
|---|---|---|
| model | Raspberry Pi 4 Model B Rev 1.5 | 未能读取 |
| 架构 | armv7l | 未能读取 |
| 内核 | 6.12.80-arm-rpi4-v7l | 未能读取 |
| uname -v | #1 SMP Wed Nov 4 17:05:36 UTC 2026 | 未能读取 |
| 镜像 | tizen-unified-toolchain_20261104.160709_tizen-headed-armv7l | 未能读取 |

不把连接失败解释为身份不符；当前身份、root 与 governor 初始状态均未知。没有执行板上 shell、root、governor、push、perf 或删除命令，没有板上状态变更需要恢复。没有部署 variants 或创建本轮板上 work 目录。

## 3. 各阶段状态与 Q.5 第17项披露

| 阶段 | 状态 |
|---|---|
| FIX1-J2 RPM 运行树准备、部署及 SHA/build-id 核对 | 未开始 |
| perf/libLLVM/BBB/ToS SHA 与硬件 cycles 检查 | 未开始 |
| 3 RUN 训练采集 | 0/3 |
| 6 份 profile 转换与合并锁定 | 0/6；无锁定 profile SHA |
| AutoFDO 构建、编译器警告检查 | 未开始；未启动构建 |
| 两视频正确性 | 未开始 |
| 预热、15 对测量、bootstrap | 未开始；无统计结论 |

披露：本轮没有生成、打开或计算任何真实 profile；没有读取既有正式 RUN 或 CALIBRATION profile。对象拟为本轮新采集的 FFmpeg Thumb，实际访问文件集合为空。没有登记修正案3或运行质量矩阵。

## 4. 主机资源与边界

初次只读检查显示 MemAvailable 约15.28 GiB（free -m 的 available=15645 MiB）；它不是构建启动门禁的合格证据，本轮未启动构建。后续完整 meminfo 与轻任务 scope 实读峰值见 [资源记录](evidence/05/resources.json) 和 [meminfo](evidence/05/meminfo.txt)。没有影响其他构建，没有暂停、资源重试或终止构建。较早几个短探测 scope 未保存 memory.peak，不声称记录了全轮峰值。

所有项目产物均位于 WORKDIR。SDB 客户端可能访问自身默认状态目录；本轮未对 WORKDIR 外状态文件取证，不能证明其没有自行写入。未安装软件、未改认证、未推 Gerrit、未修改 hq。

## 5. 后续

等待 RPi4 连接恢复后重新从身份门禁开始，核对与周六记录一致，才能继续部署与采集。不得复用本次失败连接作为身份验收。

按用户要求登记下次 hq 更新待办（本轮不修改 hq）：examples/ffmpeg/README.md 构建命令简化为普通 gbs 命令与可选资源限制示例，去掉 GIT_CONFIG_*、SUDO_ASKPASS、XDG 等内部隔离设置，以及 “Do not interfere with other builds” 等内部口吻。

## 6. 重新开始后的检查（2026-11-16 00:42–00:45 PST）：部署前提缺失，停止

本节保留第1–5节连接失败记录。本轮 SDB 已列出原端点 192.168.108.26:26101；未尝试其他端点或 RPi5。

### 6.1 身份与权限

[六项身份原文及逐项比较](evidence/06/identity.json)：model、uname -m/-r/-v、tizen-release 与 tizen-build.conf 均与周六相同，6/6通过。型号 Raspberry Pi 4 Model B Rev 1.5，armv7l，6.12.80-arm-rpi4-v7l，镜像 tizen-unified-toolchain_20261104.160709_tizen-headed-armv7l。

[初始权限与系统命令预检](evidence/06/initial-preflight.json)：uid=5001(owner)，RPM计数1233；所列系统命令均能通过command -v。df /opt/afdo_agent 报 No such file or directory。该复合查询末尾退出标记为0，仅代表最后一项命令，不代表df成功；按原始诊断识别了失败。

为排除非root权限导致不可见，记录初始状态后按用户授权执行一次sdb root on，再只读检查部署目录和文件。没有设置performance，没有执行任何perf命令。

### 6.2 root 下部署检查与停止原因

[原始检查](evidence/06/root-preflight.json)显示uid=0，并逐项返回：

```text
MISSING /opt/afdo_agent
MISSING /opt/afdo_agent/inputs
MISSING /opt/afdo_agent/tools/perf
MISSING /opt/afdo_agent/lib/libLLVM.so.22.1
MISSING /opt/afdo_agent/inputs/bbb_720p_h264_60s.mp4
MISSING /opt/afdo_agent/inputs/tos_720p_h264_60s.mp4
```

整个父目录不存在，因此不是仅凭ToS文件名判断缺失。没有搜索其他路径作为替代，没有补传工具或视频，没有创建目录。本轮任务第一部分第2条规定视频“缺失或不一致则停止”，因此停止；无法取得工具/视频SHA或进行cycles验证。

hq记录的预期输入SHA：BBB `b5e116b9d01cec8e7f697041c53575d36bd96a5928e40faa69e731f9ae2d00a4`；ToS60秒段 `280fbd41f8772491ebe784aa19a3caed3bb1e8b2e64daef1d2a5a284d1f38ad1`。这些是既有记录，不是本轮板上校验结果。不推断目录缺失的原因；镜像标识相同不能证明部署数据仍然存在。

### 6.3 退出恢复及资源

- [root on](evidence/06/root-on.json)与[root off](evidence/06/root-off.json)均返回明确切换结果，未重试；finally路径执行恢复。
- [恢复后身份、RPM与df](evidence/06/restored-id.json)：uid=5001(owner)，与初始状态相同；RPM计数仍1233。
- governor前值为policy0=schedutil，未写入过；[最后复读](evidence/06/final-governor.json)仍为schedutil。
- /opt可用1,256,748 KiB，恢复前后相同。没有部署、创建或删除本轮板上work目录，无variants新增。
- 仅运行串行轻量scope（3G/200%、nice19、ionice-c3），没有启动构建，也没有影响其他构建。初次free显示MemAvailable15656 MiB；[结束资源原文](evidence/06/meminfo.txt)与[scope峰值](evidence/06/resources.json)单独保存。较早短scope峰值未保存，不声称为完整全轮峰值。没有资源暂停、终止或重试。
- 所有远端读取均收到真实退出码标记；只读重试0次，状态命令重试0次。没有安装、挂载、重启或修改sysctl。

### 6.4 产出与披露

训练0/3，profile转换0/6；无锁定profile SHA，无AutoFDO构建及警告统计，无正确性或测量结果。本轮未生成或打开任何真实profile（Q.5第17项访问集合为空），未做质量矩阵、未登记修正案3。baseline RPM提取及运行树准备尚未开始。

证据索引与SHA：[evidence/06/sha256.json](evidence/06/sha256.json)。原始工作目录：temp/m1-pilot-rpi4-20261116/restart-01/。仅更新main报告与STATUS；hq和Gerrit均不变。继续前需要恢复已验证工具与两个视频输入的部署前提；本轮不自行越过缺失停止条件。

## 7. 环境恢复完成（2026-11-16；等待 v0.2 试跑指令）

用户新授权重新建立 `/opt/afdo_agent/{tools,lib,variants,inputs,work}`，仅使用 WORKDIR 内已有且SHA匹配的副本。本节不覆盖先前停止记录。

### 7.1 缺失原因核查

[完整命令、时间、退出码及原文](evidence/07/operations.json)中 `cause-readonly`：

- uptime约34分钟；板上时钟17:52:10（主机记录为00:51–00:52 PST，时区不同）。本轮未重启板子。
- `/`为 `/dev/mmcblk0p2`，ext4、ro；`/opt`为 `/dev/mmcblk0p3`，ext4、rw；恢复前 `/opt/afdo_agent`不存在，因此没有该子目录的独立挂载可核对。`mount`只列出现有挂载，没有执行挂载操作。
- model、uname、镜像文件内容六项与周六一致。`/etc/tizen-build.conf`记录Unified20261104.160709；mtime为2026-11-05 06:19:04 +0900，`/etc/tizen-release`mtime为2026-11-05 06:27:45 +0900。没有本轮烧录日志或镜像包可用于证明实际烧录时间。
- `/opt`目录mtime/ctime为1970-01-01 09:00:22 +0900，不能据此推断清理时间。与上次检查相比，仍为同一设备路径与挂载点；仅路径一致也不能排除重新格式化或换回同一镜像。
- **缺失原因：未知。** 现有证据不能在重新烧录、人工清理、此前挂载变化之间确定原因；uptime只证明当前启动持续时间，不证明重启造成文件丢失。按指令，此不确定性不阻塞已授权恢复。

### 7.2 来源与逐文件SHA核对

此前[部署操作](../../profgen/impl/evidence/12/08_operations.json)及[部署清单](../../profgen/impl/evidence/12/18_resume2_deployment.json)中，perf随附的 `/opt/afdo_agent/lib/` 文件只有libLLVM；没有额外库需要从其他来源替代。BBB来源见[媒体清单11](../../profgen/impl/evidence/11/09_media.json)，ToS来源见[媒体清单12](../../profgen/impl/evidence/12/09_media.json)。

| 板上路径 | 主机与板上相同的SHA-256 | 主机已有副本 |
|---|---|---|
| `/opt/afdo_agent/tools/perf` | `41b9b9a0d41da1b2a600c84ffa482ea05c52af54af094f5c6a2bf52d6aa13138` | `temp/rpms/perf-extract/usr/bin/perf` |
| `/opt/afdo_agent/lib/libLLVM.so.22.1` | `49fcc90da72ac2eabd7bbdb0a71566ea2284a532f98730ca46496782f30fb69e` | `temp/rpms/llvm-extract/usr/lib/libLLVM.so.22.1` |
| `/opt/afdo_agent/inputs/bbb_720p_h264_60s.mp4` | `b5e116b9d01cec8e7f697041c53575d36bd96a5928e40faa69e731f9ae2d00a4` | `media/bbb_720p_h264_60s.mp4` |
| `/opt/afdo_agent/inputs/tos_720p_h264_60s.mp4` | `280fbd41f8772491ebe784aa19a3caed3bb1e8b2e64daef1d2a5a284d1f38ad1` | `temp/board-round1/tos_720p_h264_60s.mp4` |

[主机核验清单](evidence/07/host-manifest.json)、[部署后清单](evidence/07/deployment.json)记录路径、字节数与来源证据。四文件共96,622,512字节；传输前重哈希，逐个push后板上sha256sum再核对，4/4一致。没有下载、重建或安装。

### 7.3 运行与恢复验证

- 新建tools、lib、variants、inputs、work五个目录。仅恢复上述四文件；variants目前没有部署FFmpeg变体。
- `chmod 755 /opt/afdo_agent/tools/perf`成功。
- `LD_LIBRARY_PATH=/opt/afdo_agent/lib ldd /opt/afdo_agent/tools/perf`退出0、没有`not found`；libLLVM来自部署目录，其余依赖（包括libxml2.so.16）来自现有系统库。没有替换系统库。
- 将HOME、TMPDIR、PERF_CONFIG与build-id目录指向 `/opt/afdo_agent/work`，执行`perf --version`输出`perf version 6.12.80`、远端退出0。这里只执行版本检查，没有record/stat/evlist或工作负载。
- 初始uid5001；仅部署需要时root on，finally恢复root off，结束复读uid5001。policy0 governor初始与结束均schedutil，期间没有写governor，因此无需切回。RPM前后均1233。
- `/opt`可用空间从1,256,308 KiB变为1,161,836 KiB；部署前通过`2×文件总量+200 MB`空间检查。没有删除任何旧目录。
- 执行段18.749秒；串行轻量scope3G/200%、nice19/ionice-c3。起止采样最低MemAvailable15,925,891,072字节，cgroup memory.peak20,234,240字节；不足60秒没有中途60秒采样。没有资源暂停/终止/重试。见[结果](evidence/07/result.json)。

### 7.4 后续边界与披露

环境恢复通过，原“部署目录缺失”阻塞已解除。当前消息尚未附带“M1手动试跑（按设计v0.2规则）”全文，已请求补发；不自行把旧版规则当作v0.2规则。等待期间root已恢复初始状态。

未采集、未生成或打开任何真实profile；Q.5第17项本轮profile访问集合为空。没有AutoFDO构建、正确性或性能测量。未改hq、未推Gerrit。证据SHA见[索引](evidence/07/sha256.json)。

## 8. 按 v0.2 专项指令执行的端到端试跑（2026-11-16）

本节取代第 7 节的“等待试跑指令”状态，保留全部历史失败记录。执行范围为 RPi4 Thumb、FFmpeg AutoFDO；未操作 RPi5、hq 或 Gerrit。以本轮用户指令为准：固定 15 个 block、不增加覆盖诊断选项，只使用 BBB60 训练与 ToS60 测量；不把 v0.2 中建议的第二测试片、覆盖阈值或由 pilot 推算 N 混入本轮。

### 8.1 身份、工具、BASE 与安全边界

六项身份与周六 `evidence/02/board-check-02/queries.json` 逐项相同：Raspberry Pi 4 Model B Rev 1.5、armv7l、6.12.80-arm-rpi4-v7l，TZ_BUILD_ID=tizen-unified-toolchain_20261104.160709。原始比对见 [identity](evidence/08/identity.json)。初始 uid=5001，policy0 governor=schedutil；每次板上阶段都保存/恢复状态。仅在授权的 root/governor 操作外写 `/opt/afdo_agent/`；没有 RPM 安装、系统库替换、重启、挂载或 sysctl 修改。

重新核对的既有部署身份：

| 对象 | SHA-256 |
|---|---|
| perf 6.12.80 | `41b9b9a0d41da1b2a600c84ffa482ea05c52af54af094f5c6a2bf52d6aa13138` |
| libLLVM.so.22.1（板上 perf 依赖） | `49fcc90da72ac2eabd7bbdb0a71566ea2284a532f98730ca46496782f30fb69e` |
| BBB60，训练 | `b5e116b9d01cec8e7f697041c53575d36bd96a5928e40faa69e731f9ae2d00a4` |
| ToS60，测试 | `280fbd41f8772491ebe784aa19a3caed3bb1e8b2e64daef1d2a5a284d1f38ad1` |

BASE 直接提取 FIX1-J2 的六个运行库 RPM（libavcodec、libavfilter、libavformat、libavutil、libswresample、libswscale）；没有重建原 BASE。运行树为 `/opt/afdo_agent/variants/m1p-base/lib/`，十二个真实文件/SONAME 链接逐项 SHA 核对。见 [RPM 来源](evidence/08/base-rpms.json)、[部署清单](evidence/08/base-manifest.json)。

短 `perf record` 的原始 evlist 确认 `cycles: type: 0 (PERF_TYPE_HARDWARE), config: 0 (PERF_COUNT_HW_CPU_CYCLES)`，period=1000003、build_id=1。初版检查正则漏写字段后的冒号，产生一次执行器误报；保留原始 evlist 与更正记录，没有把它解释成硬件不可用，也没有更换事件。

遥测能力：policy0 的 scaling_cur_freq、cpuinfo_cur_freq 可读，设定频率 1500000 kHz；唯一 thermal_zone0 为 cpu-thermal，hwmon0 为 rpi_volt，in0_lcrit_alarm 可读。固件历史节流状态未取得；结论只能称“现有遥测未观察到异常”，不能称“未降频”。

### 8.2 正确性 oracle 与三次训练

PLAT 与 BASE 在训练/测试片上均为 1,800 帧、2,488,320,000 字节，协商 caps 为 I420、1280×720、30/1 fps、progressive、pixel-aspect-ratio 1/1、chroma-site mpeg2。逐帧通知数与 `1800 × 1280 × 720 × 3/2` 的字节数相符。使用 FIFO→tee→SHA/wc，未在板上保存大体积原始帧。

| 输入 | 解码输出 SHA-256 |
|---|---|
| BBB60 | `3a4c3820c576697edd4ca34f3532c8af8ffaf04687955c5d6b35215b9b06c814` |
| ToS60 | `4c2610c37b7790240c9158277981ed9c3ac81399e3e9df554ffebb2d2ff80c4e` |

[PLAT/BASE oracle](evidence/08/stage2/oracles.json) 保存帧数、字节数、SHA、caps 与实际库路径。AFDO 的计时前校验及计时后的各变体复核另见本节后面的最终验收。

训练执行 3 次 BBB60：CPU3 解码、CPU0 的 1 秒遥测和 maps 观察器，`perf record --buildid-mmap -e cycles -c 1000003`。保存目标进程及后代的 maps；libavcodec/libavutil 均来自 m1p-base，build-id 和 SHA 一致。采样器记录的频率全部为 1500000 kHz、欠压告警全部为 0；三轮最高温均 62.809°C，最大采样间隔分别 1.07/1.08/1.09 秒。启动温度门禁在脚本内每 30 秒复查、最多 10 分钟；训练脚本未单独落盘每次门禁读值，因此不补造三轮的精确起始温度。

每个训练 RUN 都先拉回、逐文件校验、fsync 保存 receipt，再复核远端清单并删除该 RUN。三份 receipt 与删除记录位于 `evidence/08/stage3/`；perf script、buildid-list、evlist、LOST 导出诊断、maps、原始遥测均保留。原始 perf.data 留在 WORKDIR，路径/字节数/SHA 见 [大文件索引](evidence/08/retained-raw-artifacts.json)。

### 8.3 profile、样本与代码范围

发布 llvm-profgen SHA 为 `67ad21faba787d276a80673c1f324f7c0591d28d76bd37a8bd57de0d86426be6`。六次转换均显式使用 max/none/none/none、cycles、period、period-unit=1000003、extbinary，退出 0，conversion=ok、identity=verified；regex 从真实部署清单路径生成。

先按 DSO 求和合并三轮，再核查跨 DSO 键。顶层函数/上下文键交集为空；内联叶名共有 memcpy、memset，但完整调用链上下文不同，清单另列，未将它们扁平合并。锁定 profile：

`61f03b59262e3ce7ce758219d65848a33b5a0549131c362a6769ad10386f2cf2`

[锁定记录](evidence/08/conversion/locked-profile.json)；[profile 文件](evidence/08/conversion/autofdo.extbinary)；[逐轮质量摘要](evidence/08/conversion/compact-summary.json)。本轮不设额外 CLI 质量阈值，sampling_adequacy=unknown，各 threshold check=not_evaluated，不能据转换成功宣称采样充分。

| 目标 | RUN | 目标样本 | 可用 | DWARF 函数内无可写行 | DWARF 函数外（含汇编/PLT） |
|---|---:|---:|---:|---:|---:|
| libavcodec | 1 | 38299 | 22654 | 3957 | 11688 |
| libavcodec | 2 | 38056 | 22655 | 3971 | 11430 |
| libavcodec | 3 | 38093 | 22579 | 3921 | 11593 |
| libavutil | 1 | 103 | 79 | 13 | 11 |
| libavutil | 2 | 95 | 72 | 13 | 10 |
| libavutil | 3 | 127 | 88 | 20 | 19 |

上述后三列构成目标样本的互斥分解；PLT、no_cu、in_cu_no_subprogram 是函数外项的细分，不能重复相加。全部质量报告随证据保留；未映射目标样本为 0。

代码来源以独立 llvm-symbolizer 22.1.8 查询实际目标地址，按 PT_LOAD 换算并处理 Thumb 位。用函数定义源路径识别 C/头文件函数，用 `.S/.s/.asm` 行表见证识别汇编，其余保守列为其他函数外；不凭函数名猜测汇编。汇总为：

| 目标 | 总目标样本 | DWARF C/头文件函数 | 汇编源行见证 | 其他函数外 |
|---|---:|---:|---:|---:|
| libavcodec | 114448 | 79737 (69.671%) | 34637 (30.264%) | 74 (0.065%) |
| libavutil | 325 | 285 (87.692%) | 0 (0.000%) | 40 (12.308%) |

汇编见证主要在 DWARF 函数外，所以上表的汇编列与上一表“函数外”有包含关系；不是把行表存在当作可写 profile。DWARF 函数内也有无可写行的损失。libavutil 三轮合计仅 325 个目标样本，这一稀疏性如实保留。详细地址分类、查询参数与工具 SHA 见 `evidence/08/code-shares/`。

### 8.4 离线构建、构建锁与消费证据

把 BASE 实际下载的 108 个 RPM 逐份 SHA 校验后复制为本次冻结仓库，用 createrepo_c 建索引。初次 file:// 入口及随后仅增加 buildconf 的入口均在 GBS 仓库解析阶段失败（寻找 builddata/build.xml），没有编译；保留两次失败记录。最终使用 `--skip-conf-repos -R <本地目录> -D <原归档buildconf>`，没有切换 snapshot 或依赖版本。GBS 配置的路径/入口 SHA 与原在线配置不同，源代码、spec、宏、解析后 buildconf 与包集合按门禁核对；不把两个不同配置文件说成字节相同。

四次完整构建（主构建 BASE-r/AFDO，独立取证 BASE-r/AFDO）均使用新 root、串行 `--threads 1 --define '_smp_mflags -j2'`，MemoryMax=6G、MemoryHigh=5G、CPUQuota=200%、nice19、ionice-c3。启动门禁为 MemAvailable≥16 GiB、load1<0.6×nproc、磁盘≥50 GiB；等待上限本轮取 600 秒。运行中每60秒检查低内存与磁盘，仅允许停止本任务单元。资源采样、全部命令和退出码在 build 证据中；没有修改其他构建。主构建另有 cgroup 采样；取证构建未单独保存结束瞬间的 memory.peak，不将主构建峰值冒充全轮峰值。

四次完整构建各有8条既有debugedit DWARF5诊断，均非致命；原文单列保存，不宣称debugsource路径改写完整。

补丁 SHA `0c94e54d252ad1ecbc625f629af090b257edba4cd3753d76352fd031486243b6`、spec SHA `0e611e7eb95ada2c024dbea379821c5b109383f1545bcb0c86ef85f238740c27` 均保持不变。profile 仅作为 Source2000 放入 packaging/autofdo.extbinary；没有加入覆盖诊断选项。

| 构建 | 秒数 | GBS 退出码 |
|---|---:|---:|
| base-r | 120.017 | 0 |
| afdo | 124.341 | 0 |
| forensic/base-r | 125.234 | 0 |
| forensic/afdo | 123.792 | 0 |

构建锁全部通过：

- 原 BASE、BASE-r、AFDO，以及两次取证 root 的 108 条 `rpm -qa`（含 SHA256HEADER）排序后逐行相同。
- 独立取证只通过 `--define '__make /usr/bin/make V=1'` 打开命令打印，未放入 `_smp_mflags`。两侧各 698 条实际编译/链接命令，去掉 profile-use 参数后按命令多重集合比较，差异 0（并行打印顺序不是语义）。完整 argv、原始 build.log 与差异清单保存。
- 每侧取证产物与主构建的六个运行库、目标库调试文件 SHA/build-id 相同。因此用取证命令补足主构建简略 CC/AS 日志的证据，并没有把取证产物换入 A/B。
- BASE-r 的全部六个运行库 SHA 与原 BASE 相同；两个目标的 build-id 也相同，最终对照仍为 BASE。4,866 份 C/头文件/汇编源文件（含生成文件）在 BASE-r/AFDO 中逐字节相同。
- AFDO 取证日志有 627 条命令带 profile-use；chroot 内 profile SHA 等于锁定值。两个目标库 `.text` SHA 均改变，runtime/debug build-id 成对一致且不同于 BASE。默认输出中 profile 相关编译警告为 0；这不是消费证据，消费证据是前述 flag、profile SHA 和代码变化。

| 目标 | BASE = BASE-r build-id | AFDO build-id |
|---|---|---|
| libavcodec | `805376f248504d2084e3e95470810873ffc3655a` | `5aef89343bc6a870b6760c3d492206bbb8adc286` |
| libavutil | `bb5b41f743b9b07bb38cc5007f7deb6516256579` | `1908c55105184d14beeb1e7076816dd1c994658c` |

[门禁结果](evidence/08/build/gates.json)、[生成源比较](evidence/08/build/generated-source-comparison.json)、[主构建消费记录](evidence/08/build/afdo/consumption.json)。

### 8.5 测量计划、原始轮次与最终正确性

计划在 **2026-11-16T01:22:37.694129-08:00** 写入并 fsync，测量计划 SHA 为 `12e2beb604f80a89279fbd79d3218800d387b6c3d7463dcee6389e2b07498aba`。2 个预热 block（每个 BASE/AFDO 各一次），正式 N=15；顺序种子 20261116，bootstrap 种子 2026111601，20,000 次、ε=1%。A=BASE，B=AFDO：

`BA BA BA AB AB AB AB AB BA BA AB AB BA BA AB`

每轮固定 CPU3、相同 I420 caps、ToS60、fakesink sync=false；perf stat 记录 task-clock/cycles/instructions，墙钟为 Bash time 包裹 perf stat 的秒数（三位小数）。CPU0 采样器记录单调时间、两种频率、温度与欠压。固定冷却5秒，再按≤60°C启动门禁等待；轮内温度<80°C、所有频率读数=1500000 kHz、欠压0、含起止端点的间隔≤2秒。计时轮没有输出 hash；库文件 SHA 在计时结束后核验。所有解码进程 maps 均验证目标库来自本变体。

板上无 timeout 命令，使用现有 Bash 的独立进程组 watchdog，仅终止本任务子进程组，先通过1秒超时负例。第一次 AFDO oracle 启动又遇到旧 Bash 不支持 `${variant,,}`，在解码开始前失败；改为显式分支后重做。两项设置失败均保留，且各次退出都恢复 root/governor，不算正式 block 重采。

| block | 顺序 | BASE 秒 | AFDO 秒 | 标记 | 使用 attempt |
|---|---|---:|---:|---|---:|
| 1 | BA | 30.839 | 30.332 | 无 | 1 |
| 2 | BA | 30.997 | 30.200 | 无 | 1 |
| 3 | BA | 30.884 | 30.021 | 无 | 1 |
| 4 | AB | 30.755 | 30.060 | 无 | 1 |
| 5 | AB | 31.057 | 29.978 | 无 | 1 |
| 6 | AB | 30.787 | 29.922 | 无 | 1 |
| 7 | AB | 30.728 | 29.944 | 无 | 1 |
| 8 | AB | 30.740 | 30.199 | 无 | 1 |
| 9 | BA | 30.950 | 30.002 | 无 | 1 |
| 10 | BA | 30.715 | 29.882 | 无 | 1 |
| 11 | AB | 30.753 | 30.005 | telemetry_unknown | 1 |
| 12 | AB | 31.009 | 29.934 | 无 | 1 |
| 13 | BA | 30.861 | 30.090 | 无 | 1 |
| 14 | BA | 30.947 | 30.001 | telemetry_unknown | 1 |
| 15 | AB | 30.894 | 30.475 | 无 | 1 |

正式 block 完整 15/15；标记 2，缺失 0，技术故障记录 0。计时前 AFDO 两片与 PLAT oracle 一致；计时后 PLAT/BASE/AFDO × BBB/ToS 六次复核全部一致，仍是每片1,800帧、2,488,320,000字节及8.2的SHA。caps 审计及 maps 原文随证据保存。

[计划](evidence/08/measurement/plan.json)、[全部轮次](evidence/08/measurement/rounds.json)、[block选择记录](evidence/08/measurement/blocks.json)。每轮目录包含 perf stat、墙钟、caps/EOS、maps、遥测和启动温度检查原文；本轮未独立测量遥测采样器开销，两变体使用同一观察方式。

### 8.6 统计与判定

Python 标准库，按 block 配对 `r_i=ln(T_AFDO/T_BASE)`，主估计 `exp(mean(r))-1`。标记轮次仍在主分析；干净 block 单独做敏感性分析。

- **主判定：faster**。主估计 **-2.565%**。
- block bootstrap 95% CI：**[-2.859%, -2.256%]**。
- t 区间（次要）：[-2.906%, -2.223%]；中位数之比−1：-2.774%。
- BASE CV：0.3656%，供以后估计 N，本轮没有据此增减轮数。
- cycles/task-clock 中位有效频率：BASE 1499.804 MHz，AFDO 1499.801 MHz；相对差 -0.000220%；未超过0.5%混杂风险阈值。
- 干净 block：n=13，判定 faster，估计 -2.537%，bootstrap CI [-2.868%, -2.194%]。

[统计原文](evidence/08/measurement/statistics.json)。第11、14个block均为AFDO轮的采样器终止半行，原脚本记telemetry_unknown；完整读数未观察到频率/温度/欠压异常，不将截断读数当作正常。两组保留在主分析，敏感性分析不替代主判定。统计脚本 SHA 在计时前锁定；等价、快、慢、超额标记、缺失的合成夹具均通过。没有观察中途效果来补采、改顺序或改 N。

### 8.7 恢复、证据与限制

最终 uid=5001，governor 为 `/sys/devices/system/cpu/cpufreq/policy0/scaling_governor=schedutil`，RPM计数 1233；cleanup_pending=[]。本轮 work 目录先打包拉回、校验 SHA、持久化收据，再复核远端清单并删除。保留 `/opt/afdo_agent/variants/m1p-base/` 与 `/opt/afdo_agent/variants/m1p-afdo/`，其真实文件 SHA 清单位于[清理结果](evidence/08/cleanup/result.json)。没有清理任何其他任务目录。

完整阶段脚本、实际 argv、构建日志、样本与质量报告、原始测量/遥测、oracle、收据和文件 SHA 见 [证据索引](evidence/08/index.json) 与 [校验清单](evidence/08/sha256.json)。大文本使用 .gz 保存原字节。主机工作目录为 `temp/m1-pilot-v02-20261116/`；RPM、buildroot、原始 perf.data 与最终板上 work 归档保留在其中，没有提交 LLVM 源码或二进制构建树。

记录限制：早期公共日志复用了 operations.json，导致第一阶段部分逐条 SDB stdout 被覆盖；保留原阶段脚本、独立 identity/evlist/状态/部署清单，并在采集前重新逐项验证工具、视频与所有 BASE 文件 SHA。此处不声称早期每条 stdout 都保留。取证构建的结束瞬间 cgroup peak 未记录。SDB 使用已有服务，未观察到本轮启动新服务；没有为核查其内部状态而访问项目外的源码/配置或清理外部文件。

本结果只覆盖这两个输入与这块板上的 FFmpeg Thumb pilot，不能外推为完整解码器正确性或普遍性能收益。训练和测试是不同视频/SHA；ToS 在之前 profgen 工作中使用过，不称为全新未接触 holdout。profgen explicit conservative strategy; defaults not statistically validated。本轮没有质量矩阵或 M1/M2 等质量指标计算，也没有登记预注册修订3。

### 8.8 Q.5 第17项与提交范围

所有本轮生成/读取的六份单 RUN profile、两份 DSO 合并 profile、锁定 package profile，以及文本检查、编译器消费的对象/时间/用途，见[接触登记](evidence/08/conversion/Q5-17-profile-access.json)。编译器消费时间范围用 command/result 文件时间及资源日志界定；目的为本次 workflow 消费、冲突与构建锁验证，未来质量评估必须披露此接触。

本轮只提交 main 的本报告、STATUS 与 evidence/08；不修改设计、hq、Gerrit或他人评审文件。最终 commit 与推送核验在执行汇报中给出。
