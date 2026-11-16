# M1第三阶段：RPi4端到端自动化验收

## 1. 本轮结果与停止点

执行日期：2026-11-16（America/Los_Angeles）。实验ID：m1-ffmpeg-rpi4-thumb-01。设计v0.3不改。本轮**S0主机资源门禁失败，停止；未完成M1自动化验收**。

主机MemAvailable为 **15,922,335,744字节（14.828831 GiB）**，低于§9.4的16 GiB。load1=0.958008，nproc=20（阈值12）；磁盘可用116,059,664,384字节（大于50 GiB），后二项通过。原文：[host-resource-gate.json](../runs/m1-ffmpeg-rpi4-thumb-01/host-resource-gate.json)。

用户本轮明确规定“任何门禁失败都原样记录并停止，不放宽门禁”。因此未设置等待/自动重试，未沿用上一任务361624 v3的临时资源豁免，也没有用旧试跑结果充当新实验数据。**尚未修改workflow代码/package.toml/inputs.toml、未下载Sintel、未构建、未采集、未生成profile、未测量。**

完整[运行索引](../runs/m1-ffmpeg-rpi4-thumb-01/index.json)、[SHA清单](../runs/m1-ffmpeg-rpi4-thumb-01/SHA256SUMS)；原件保留在temp/m1-ffmpeg-rpi4-thumb-01/。没有写入成功的S0–S7阶段收据。

## 2. PM决定登记（PM decision 2026-11-17）

以下保留用户指定的决定日期标签；本次执行日期见第1节。因S0停止，决定已在本报告登记，**尚未实施或验收**：

1. 同一比较两变体被遥测标记的round数之差 ≥ max(2, ceil(0.1·N)) 时，判定明显失衡，主判定封顶inconclusive，说明原因；20%规则不变。删除clear_flag_imbalance手工输入，改为自动计算。须补N=10/15/40、差值恰好等于阈值及差1的合成测试。
2. 第二测试片为Blender Foundation的Sintel，CC BY 3.0；仅从download.blender.org官方1080p片源取得。归档与原片留temp/media_src并记录URL、授权页、SHA。
3. 制作300–360秒片段，去音轨、1920×1080、保持原片帧率（预期24 fps，异则如实记录）、libx264、preset veryfast、profile main、cabac=0、yuv420p、8M/maxrate 8M/bufsize16M、threads2/filter_threads1、+faststart。须记录本机ffmpeg版本/二进制SHA，并用ffprobe和码流证据确认Main/CAVLC、帧数与时长。
4. inputs.toml新增sintel-1080p-60、role=test-secondary；ToS为预指定primary，Sintel为secondary，不做多重比较校正。视频不入Git，来源与命令按media/README.md登记。
5. 训练为BBB720p、R=3、cycles -c1000003、CPU3、显式max/none/none/none；拟复用试跑冻结108个RPM前，须完成逐包SHA和新旧BuildRequires核对。本轮未执行这些核对，不把仓库标为已复验。

## 3. 已执行的板上只读预检与恢复

最初sdb devices返回空列表；仅连接既有记录的192.168.108.26:26101，连接后设备列表为单个rpi4。没有因端点相同而跳过身份核对。每条shell命令保存独立退出码标记与原始stdout/stderr。

| 检查 | 实际值/结论 | 证据 |
|---|---|---|
| 型号 | Raspberry Pi 4 Model B Rev 1.5，与实验记录一致 | identity.json |
| 架构 | armv7l，一致 | identity.json |
| 内核 | 6.12.80-arm-rpi4-v7l，一致 | identity.json |
| TZ_BUILD_ID | tizen-unified-toolchain_20261104.160709，一致 | identity.json |
| 初始uid | 5001 | identity.json、tool-check-state.json |
| 系统PATH依赖 | 全部找到；未安装任何软件 | tool-check-operations.json的nonroot-dependencies |
| /opt/afdo_agent目录权限 | root下目录存在、可写且可遍历；尚未执行新脚本验证挂载exec能力 | tool-check-operations.json的agent-access |
| perf SHA | 41b9b9a0d41da1b2a600c84ffa482ea05c52af54af094f5c6a2bf52d6aa13138，匹配 | tool-check-result.json |
| libLLVM SHA | 49fcc90da72ac2eabd7bbdb0a71566ea2284a532f98730ca46496782f30fb69e，匹配 | tool-check-result.json |
| perf ldd/version | 无not found；perf version 6.12.80 | tool-check-operations.json |
| root恢复 | root on预检后finally执行root off，重新确认uid5001 | tool-check-operations.json的root-restore/final-uid |
| governor | 保存值与最终值逐字节相同，全程未设置performance | tool-check-state.json、tool-check-result.json |
| 清理 | cleanup_pending=[]；没有启动板上后台采样器/负载，没有创建本轮板上RUN目录或部署文件 | tool-check-result.json、end.json |

以上证据均位于[本轮运行目录](../runs/m1-ffmpeg-rpi4-thumb-01/index.json)。本轮未执行perf record或perf stat；**硬件cycles三项断言、完整遥测能力、输入部署SHA和完整S0仍未完成**。perf --version只是工具预检，不当作硬件事件可用性证明。

## 4. §14 M1逐项验收状态

| 验收项 | 本轮结果 | 原因/待完成部分 |
|---|---|---|
| S0前置 | **失败** | 主机16GiB门禁未过；已完成的身份/工具检查见第3节 |
| 单命令S0→S7 | 未执行 | live transport与阶段调度尚未接入并验收 |
| build-lock三门禁 | 未执行 | 未构建新BASE/AFDO，未生成新锁 |
| BASE-r离线复建及对照选择 | 未执行 | 无本轮构建 |
| 三输入PLAT oracle及前后正确性 | 未执行 | Sintel未准备；不复用旧正确性标签代替 |
| 每个计时进程must-load/deploy-set | 未执行 | 无计时进程 |
| 两目标AppliedSamples消费证据 | 未执行 | 无本轮AFDO产物 |
| ≥10 BASE预试、CV/N与锁定计划 | 未执行 | 未开始任何测量 |
| ToS、Sintel比较与变换后CI | 未执行 | 没有本轮数据 |
| S3后SIGTERM恢复测试 | 未执行 | S3未开始 |
| 独立1 block中途SIGTERM清理测试 | 未执行 | 未开始；没有混入正式数据 |
| S7 report.json/report.md与固定声明 | 未生成 | 未伪造完成态实验报告；本文件仅为停止报告 |

| 比较 | 估计 | 95% CI | 判定 |
|---|---|---|---|
| ToS（primary） | 未计算 | 未计算 | 未执行 |
| Sintel（secondary） | 未计算 | 未计算 | 未执行 |

未运行或补充代码测试，因为本轮在实施前门禁停止，代码没有变化；旧单元测试/手动试跑不算本轮自动化验收通过。

## 5. 资源、墙钟与边界

- 首次sdb devices至主机门禁检查：**158.311秒**。这是连接与预检墙钟，不是构建/采样/测量耗时；后者均未启动。
- 本轮保存的meminfo样本最低MemAvailable：**15,922,335,744 B**。实读并保存的轻量检查scope memory.peak最大：**7,905,280 B**，仅覆盖有采样的检查scope，不能外推为未记录的全部命令总峰值。两份cgroup事件均无high/max/OOM。
- 主机命令串行nice19/ionice-c3、3G/200% scope。没有启动GBS单元，无资源终止/重试；没有停止其他进程。
- 板上只有授权root状态临时切换，已恢复；未写/opt的新文件、/usr、未安装RPM、未重启/挂载、未改sysctl、未修改governor。SDB使用既有服务，本次输出未提示启动新daemon；未检查或清理SDB服务的外部内部状态文件，不能据此断言其内部零写入。
- 没有打开任何真实sample profile；没有Gerrit/hq操作；未改设计或旧证据。新文件只在WORKDIR内；受保护的config/、gbs_gcc.conf、gbs_llvm.conf未读取或改动。
- 已写带时间的[ALL-END](../runs/m1-ffmpeg-rpi4-thumb-01/end.log)。按停止条件结束，待用户决定后续。
