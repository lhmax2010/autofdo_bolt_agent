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
