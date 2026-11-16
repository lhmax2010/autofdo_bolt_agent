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
