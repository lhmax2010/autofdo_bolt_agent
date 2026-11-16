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


## 6. 本轮继续：门禁澄清、准备完成与 S0 解析缺陷停止

本节对应收到 dbe00c2 停止记录后的用户新授权。第1–5节原文及其证据保留。
实验仍为 m1-ffmpeg-rpi4-thumb-01；**未完成第三阶段验收**。本轮用单条 workflow 命令启动，
真实退出码 **2**，停止于 S0。驱动器正常收尾退出0仅表示日志收集完成，不表示 workflow 成功。

### 6.1 本轮资源授权与实现状态

- 仅本实验本轮取消 GBS 启动 MemAvailable≥16GiB；仍要求 load1<0.6×nproc、可用磁盘≥50GiB，
  每60秒检查、最多3600秒。GBS运行时6G/5G/200%、-j2、threads1、nice19/ionice-c3不变；
  MemAvailable<6GiB连续两次或磁盘<20GiB仍只停止本任务构建scope。
- S0只保存主机资源，不以可用内存拒绝。构建收据新增启动资源、等待秒数和本轮授权字段。
  **本次构建0次，启动资源表为空、构建等待0秒**；未声称实际验证构建超时/恢复。
- 新增SDB transport、阶段调度、live入口、流式oracle及阶段接线。状态意图先于变更落盘；
  清理排序为自身进程→已校验拉回目录→governor→root；阶段尝试用新目录，成功收据复用前重新核对SHA。
  这些是待现场验收实现，**S1–S7均未到达，不能宣称已验证完整live调度或恢复**。
- PM decision 2026-11-17 的标记失衡改为自动计算：
  abs(两变体被标记round数差)≥max(2,ceil(0.1×N))，封顶inconclusive；
  删除手工 clear_flag_imbalance 参数，20%规则不变。package使用pilot决定N。
- 测试 **105项通过**（原94项及11项新增），包含N=10/15/40阈值、差1、
  临时内存豁免仍检查load/disk、运行中保护、只读重试与变更命令不重试、
  收据中断恢复、清理顺序、次要输入重叠拒绝。所有13个board/workload脚本通过bash --posix -n，
  新模块通过py_compile；未安装shellcheck。测试证据：
  [tests-monitored.log](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-02/tests-monitored.log)。
  本轮失败说明现有合成测试缺少本perf版本的冒号格式，应补正反例后再启动下一次现场运行。

### 6.2 Sintel、输入与冻结仓库

- Sintel来自官方download.blender.org；授权页 https://durian.blender.org/sharing/ 指明CC BY3.0。
  原片为独立MKV、没有另一个压缩归档。源SHA：
  97f1dbc66231df42ad49bd8c29aa174b8f48933058e47e7157d4ba63d93a8efa；
  1,180,090,590字节；1920×818、24fps。
- 按用户指定缩放至1920×1080，截取300–360秒、无音轨、Main/cabac=0、veryfast/yuv420p、
  8M/maxrate8M/bufsize16M、threads2/filter_threads1、faststart。编码退出0、27.788秒；
  ffmpeg版本与二进制SHA、完整命令见media/README.md及本轮证据。
- 输出60,471,233字节，SHA
  **b1c762e322350cecb04a38509050d320892ff8cbc8b2a7113418d5ecba4ad843**。
  ffprobe证实Main、24/1、1,440帧、60秒；全码流trace_headers的PPS中entropy_coding_mode_flag=0，
  证实CAVLC。host流式解码摘要只作为输入预期；**PLAT oracle尚未生成**，不把host摘要当作板上正确性验收。
- inputs.toml已登记test-secondary；ToS为primary，Sintel为secondary，不做多重比较校正。
  本轮S0已推送三个输入并逐个验证板上SHA。脚本/输入推送原始命令见
  [deployment-operations.json](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-02/deployment-operations.json)。
- 冻结108个RPM逐包SHA全部通过；旧试跑、新BASE、新AFDO的BuildRequires三份查询均退出0且完全相同。
  Base20261030.120529 / Unified20261104.125239不变，复用本地冻结仓库。
  [frozen-reuse.json](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-02/frozen-reuse.json)。
- 共享clone因alternates链过深失败，未改任何原树或补丁。保留失败目录，改从WORKDIR/src/ffmpeg做独立本地传输克隆，
  基线5fe76358后应用原profiling.patch；spec SHA仍为
  8e0e6a04528ad1fc8f4d5026ec1203e04f0bbf95b0658e66901f0b583942737a。
  尚未启动任何GBS。初次输入测试因新增第3片使旧测试选错片段而失败，修正测试选取后105项全过；
  失败日志保留，不覆盖。

### 6.3 单命令执行及失败原文

执行器的正式子命令为 python3 -m afdo_wf run --job temp/m1-ffmpeg-rpi4-thumb-01/attempt-02/job.json
（完整绝对路径argv与SHA见workflow-launch-1.json）。外层3G/200% scope单进程串行，
驱动器负责60秒资源采样及预定SIGTERM试验；本次未到达注入点，没有触发第二次运行。

S0设备身份与试跑一致：Raspberry Pi 4 Model B Rev1.5、armv7l、6.12.80-arm-rpi4-v7l、
TZ_BUILD_ID=tizen-unified-toolchain_20261104.160709。系统PATH、perf/libLLVM SHA、ldd与perf6.12.80通过；
先保存初态，再开root、固定performance，之后运行cycles探测。

perf record退出0，perf evlist原文为：

    cycles: type: 0 (PERF_TYPE_HARDWARE), size: 136, config: 0 (PERF_COUNT_HW_CPU_CYCLES), ...

**这是解析器缺陷，不是硬件事件不可用结论。** 新代码使用type与config后仅允许空白的正则，
没有接受实际的冒号分隔；event断言为真，type/config正则断言为假。原文已经提供硬件type0/config0事实。
原始[cycles.evlist](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-02/formal/stages/preflight/001/cycles.evlist)、
[独立静态解析诊断](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-02/cycles-parser-audit.json)。

按用户“其他门禁失败即记录并停止”，**没有修改解析条件后重跑**，也没有跳过门禁继续构建。
建议下一轮修正字段分隔解析，并补实际冒号格式、软件事件、错误config、多事件歧义的合成测试；
不需要修改硬件门槛或设计。

### 6.4 本次验收、恢复与保留目录

| 项目 | 本次结果 |
|---|---|
| live S0身份/工具/三个输入SHA | 已通过 |
| cycles三项断言 | 解析器误拒绝，S0退出2 |
| 遥测能力清单 | 尚未执行到该步骤 |
| S1 BASE / BASE-r / AFDO、build-lock、consumption | 均未执行 |
| BBB训练R=3、profile转换/锁定 | 均未执行，未读取真实profile |
| 三输入PLAT/BASE/AFDO正确性 | 未执行 |
| ToS primary / Sintel secondary估计、CI、判定 | 未计算，无测量数据 |
| S3后SIGTERM恢复、独立计时中断清理测试 | 未到达；合成测试不替代现场测试 |
| S7成功态report.json/report.md | 未生成；只保留失败收据与本停止报告 |
| root/governor恢复 | uid5001、policy0=schedutil，与初态相同 |
| RPM包数 | 前后均1233 |
| SDB只读重试 | 0 |
| 构建启动资源/等待 | 无构建；无启动记录；等待0秒 |

状态恢复原文见final收据。**原始cleanup_pending=[]只覆盖已登记的状态恢复动作，不代表工作目录已完全清理。**
S0在拉回前失败，板上
/opt/afdo_agent/work/m1-ffmpeg-rpi4-thumb-01/cycles-check
中的perf.data尚未拉回核验，按规则保留，未删除。后续恢复须先处理该确切目录，不能覆盖。
脚本保留在/opt/afdo_agent/tools/workflow-m1-ffmpeg-rpi4-thumb-01；
三个视频保留inputs，未部署新的BASE/AFDO变体。没有启动遥测采样器或长期负载。
此处同时暴露S0探测目录未提前加入拉回清理日志的缺口，下一轮应补齐，不以空journal掩盖。

### 6.5 资源、边界与停止状态

- 正式命令与恢复墙钟 **73.492秒**；GBS/训练/测量墙钟均不适用。
- 运行期3份资源样本，最低MemAvailable **17,094,287,360 B**
  （15.920296GiB）；driver scope实读memory.peak **25,735,168 B**；
  单元测试scope实读峰值 **26,259,456 B**。这些不是所有准备命令的合并峰值：
  下载/编码等早期短scope未保存memory.peak，峰值未知；不补造。
- 无构建启动等待、资源停止、OOM或重试。收尾写明ALL-END及子命令真实退出码2。
- 边界例外：最初pwd未包scope；AGENTS文件名查找误以父目录为起点，只遍历名称/目录元数据，
  没有读取匹配文件内容，随后只终止该查找自身PID560992。未因此写入WORKDIR外文件。
  已有SDB daemon是否更新外部状态文件未知，未检查或更改其他项目数据。
- 未接RPi5、未改hq/Gerrit/设计/旧证据、未安装软件，未触碰受保护配置；
  本轮新证据与大文件SHA见
  [索引](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-02/index.json)和
  [本地主件清单](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-02/large-and-local-index.json)。
- **本轮停止，等待解析缺陷与S0目录清理缺口的后续处理指令；不宣称M1通过。**
