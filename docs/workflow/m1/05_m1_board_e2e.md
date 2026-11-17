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


## 7. 磁盘盘点、S0修正与SDB端点不可见停止（2026-11-17任务）

本轮以606ae8f为起点，先做磁盘盘点，再修正代码，之后尝试处理遗留探测目录。
**停止原因是当前SDB中没有192.168.108.26:26101；未启动第三部分的正式run。**
本轮未把该连接问题当作可忽略的实现缺陷，也没有改用其他端点、扫描地址或修改认证。

### 7.1 清理核查

[清理报告](../../maintenance/disk_cleanup_2026-11-17.md)及其SHA索引记录所有≥200MiB目录、
修改时间、任务归属、符号链接/真实路径、可见挂载和进程占用。
两次du用时358.437秒和273.825秒，均因部分root目录权限不足退出1，原文保留；
目录大小是可读部分下界，祖先/后代及硬链接的计数不可相加。

可用空间从 **113,591,267,328 B（105.790 GiB）**
到 **113,576,747,008 B（105.777 GiB）**。
删除 **0 B**：/proc有979项读取被拒，未能完整证明B候选不被进程使用；
按照“拿不准保留”跳过，未扩大sudo权限、未卸载、未触碰其他构建。
C项仅是可进一步划定可重建部分的候选，内含RPM/日志/冻结仓库等A项仍须保留。
空间已高于50GiB，**磁盘与内存不是本轮停止原因**。

### 7.2 解析与探测目录修正

- 新parse_cycles_event只接受一行/一个事件、事件名cycles；
  逗号分字段，精确type/config字段名，支持冒号或等号、int(value,0)与0x0，
  忽略括号说明；必须type=0且config=0，不能用config1/config2/bp_type/sample_type替代。
- attempt-02的cycles.evlist逐字节复制为
  workflow/tests/fixtures/rpi4-cycles.evlist；测试明确证明旧正则对该原文为False、新解析为True。
- 正例：本板真实原文、旧等号格式、十六进制；反例：cpu-clock软件事件、非零config、
  两事件、只有相似字段而缺type/config。没有更改事件门槛。
- cycles-check在创建前通过register_run登记remote/local/receipt；异常清理调用已有verified-pull，
  比对全量SHA并持久化收据后才删除确切路径。合成测试覆盖探测失败仍有日志、
  SHA失败不删除、校验成功才删除；旧拉回负对照继续通过。
- Sintel说明已补充：1920×818按PM要求缩放到1920×1080，纵向拉伸；
  仅用于解码性能/正确性，不影响其用途。没有重新编码，视频SHA不变。
- **112项测试全部通过，0失败/0错误；13个shell脚本bash --posix -n通过。**
  证据：[tests-monitored.log](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-03/tests-monitored.log)、
  [fixture-sha.json](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-03/fixture-sha.json)。

### 7.3 遗留cycles-check拉回尝试与停止

在任何root/governor变更之前先只读确认身份。指定端点的model查询首次及两次允许重试均为
真实主机退出码1，stderr原文：

    error: target not found
    error: serial number '192.168.108.26:26101' wrong

后续只读sdb devices诊断退出0，设备列表为空。它只能证明当前SDB没有该端点，
**不能据此断言板子断电、镜像变化或内核变化**。
[三次命令、时间、stdout/stderr](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-03/legacy-recovery/transport/)、
[结果](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-03/legacy-recovery/result.json)、
[sdb devices](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-03/sdb-devices.stdout)。

未读取旧perf.data、未获取远端SHA、未拉回或删除旧目录；
/opt/afdo_agent/work/m1-ffmpeg-rpi4-thumb-01/cycles-check仍记为**待核实拉回/清理**，
不能报告已清理。没有执行root on、修改governor、部署、采样或新探测。
因此本轮没有自身待恢复的板上状态；当前uid/governor均未知，不能用上一轮的恢复结果冒充本轮读取。

### 7.4 M1验收与自身缺陷处理记录

| 项目 | 本轮结果 |
|---|---|
| 磁盘盘点与分类 | 完成；未充分证明可删的B均跳过；删除0B |
| cycles解析/目录清理修正 | 合成测试通过，现场重测未进行 |
| 遗留目录拉回及删除 | 未完成：身份查询前即SDB端点不可见 |
| 新attempt单命令run | 未启动（先行恢复步骤失败） |
| S0新硬件事件/遥测能力/输入SHA | 未执行 |
| BASE、AFDO、BASE-r，build-lock及消费证据 | 未执行 |
| 三输入oracle、must-load/deploy-set、计时前后正确性 | 未执行 |
| ToS primary估计/CI/判定 | 未计算/未计算/未执行 |
| Sintel secondary估计/CI/判定 | 未计算/未计算/未执行 |
| S3后SIGTERM恢复测试 | 未到达 |
| 独立1block注入失败清理 | 未到达 |
| 本轮GBS启动资源与等待 | 构建0次，记录为空，等待0秒 |
| 运行中资源保护触发 | 无构建，无资源停止/OOM |

自身缺陷政策已写入STATUS长期规则。本轮预先指定的cycles解析缺陷修正计1次，
原文/原因/改动/先失败后通过见7.2；正式运行中的自动修复/恢复次数为0。
SDB失败不属于该政策，不消耗/绕过实现缺陷次数，也没有修改判据。
探测目录日志补齐是同一已知S0修复的配套工作。后续仍需先处理遗留目录，
再用新attempt单命令运行；本次不伪造成功收据或统计结果。

### 7.5 资源与边界

测试scope实读memory.peak **28,700,672 B**，
测试前后采样最低MemAvailable **12,163,461,120 B**。
没有GBS，因此没有任何构建启动内存、load、磁盘或等待时间记录。
保留本实验本轮的16GiB启动门槛豁免，其余load/disk及运行中保护未改动。

主机命令nice19/ionice-c3、3G/200% scope；仅检查本项目及/proc、findmnt等系统元数据。
WORKDIR外仅观察到llvm-optimize的cwd路径，没有遍历其文件或测量大小，更未删除/修改。
SDB使用已有服务；其是否更新WORKDIR外的内部状态未知。
未改设计/hq/Gerrit、未安装软件、未读或修改受保护配置、未打开真实sample profile。
[本轮索引](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-03/index.json)保存失败原文与SHA，ALL-END已记录。
本轮停止，待指定端点恢复可见后继续。

## 8. PM清理判据第二轮、M1 attempt-04与S2启动无完成证据停止

基于28cdd4f；执行顺序为清理→显式sdb connect→遗留目录校验清理→同一job单命令M1。
本轮**未完成M1验收**：S0与BASE构建/产物核对通过，S2首次PLAT/BBB oracle的远端启动进程消失且没有退出文件，停止。
不能把此前手动试跑的结果填作本轮ToS/Sintel结果。

### 8.1 磁盘清理

[第二轮清理报告](../../maintenance/disk_cleanup_2026-11-17.md#第二轮按pm逐项判据清理2026-11-17任务)记录五项判据和逐次删除证据。
不再以他人fd不可读作为前提；仍保留不能完整核实全树修改时间、含未保留原件、被指定文件引用或提交可达性未证实的目录。

可用空间108,855,418,880→109,025,251,328 B（101.380→101.538 GiB）。删除23个确切路径，删除前分配块合计6,470,066,176 B（6.026 GiB），不能等同净释放：缓存保留副本、硬链接与文件系统并发变化均影响df。保留693份去重缓存文件、2,294,814,761字节，逐个SHA通过；local/repos等处321条RPM/日志SHA记录保留。没有sudo、卸载、软件安装或其他项目清理。

待PM决定项及大小详见清理表：旧chroot内部权限阻止完整mtime检查；发布root/工具树及若干源码被引用；am-check和361624源码副本的提交未证明由保留refs覆盖。原始perf/profile/quality/收据、三个输入、冻结repo、当前实验全部保留。

### 8.2 连接与遗留cycles-check

显式sdb connect 192.168.108.26:26101退出0，提示already connected；sdb devices列出目标RPi4与另一端点192.168.108.13:26101。本轮仅访问指定RPi4；连接重试0，远端只读重试0，没有kill-server或重启服务。
身份仍为Raspberry Pi 4 Model B Rev 1.5 / armv7l / 6.12.80-arm-rpi4-v7l / tizen-unified-toolchain_20261104.160709。

遗留目录唯一文件perf.data的SHA为8ed24e55c8c53d8afc80039c0b9132a9d566e98e082c3297a9499e52d300d047。
两次远端SHA清单与本地落盘一致、verified-pull收据保存后删除该确切目录。
原件在temp/m1-ffmpeg-rpi4-thumb-01/attempt-04/legacy-recovery/pulled/；未打开分析该perf数据。
root按必要性临时开启并恢复，governor未改变；RPM1233不变。
证据：[legacy-recovery](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-04/legacy-recovery/result.json)。

### 8.3 正式命令与自身缺陷修复（本轮1/3）

命令（两次一致）：

    PYTHONPATH=WORKDIR/workflow python3 -m afdo_wf run --job WORKDIR/temp/m1-ffmpeg-rpi4-thumb-01/attempt-04/job.json

主机监督为独立user service（nice19/ionice-c3，driver 3G/200%），GBS使用独立6G/5G/200% scope、-j2、threads1。
新源码检出5fe76358并应用原workflow profiling.patch；spec SHA与attempt-02一致；发布工具SHA重验通过；冻结108RPM逐包SHA重验通过，新旧BuildRequires引用已封存且相同spec的attempt-02证据。

首次GBS退出0，但后处理错误ambiguous build source。原始日志335/336等行表明实际BUILD是/home/abuild/rpmbuild/BUILD，旧硬编码/usr/src/packages/BUILD为空。
这是实际构建成功且源码位置可证的实现错误，没有修改spec、补丁、依赖或门槛。
修正：从成功RPM跟踪日志提取唯一BUILD路径，再要求唯一含ffbuild/config.mak的FFmpeg目录；构建锁记录实际chroot布局；消费profile路径从唯一实际编译选项取得，不再硬编码旧SOURCES路径。

夹具保留实际cd原文，证明旧glob为空、新路径解析通过，并覆盖歧义拒绝和唯一消费路径；**114项测试通过**。
原失败收据、原live.py、原文与SHA见[defects/01-build-layout](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-04/defects/01-build-layout/evidence.json)。
代码是阶段收据的输入，因此显式redo将旧preflight收据归档再失效；不伪造代码SHA、不宣称跨代码变更复用收据，用同一job从S0重验并重新构建。
这是本轮唯一自身缺陷修复；S2启动消失的原因未证实，未占用剩余次数去猜测修补或重试负载。

### 8.4 两次BASE构建与启动资源

本实验本次仅取消MemAvailable≥16GiB启动门槛；load1<0.6×20=12及磁盘≥50GiB保留，最多60分钟等待；运行中低内存/磁盘停止保护保持。

| 执行 | GBS退出 | GBS墙钟秒 | 启动MemAvailable GiB | load1 | 启动可用盘 GiB | 等待秒 | cgroup峰值字节 | 后处理 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| BASE-1 | 0 | 138.258 | 10.548 | 2.430 | 100.720 | 0.066 | 2108694528 | 旧路径错误 |
| BASE-2 | 0 | 129.604 | 10.249 | 3.271 | 99.173 | 0.074 | 1924259840 | 通过，S1收据完成 |

第二次22个二进制RPM清单/SHA已保存；已安装108包及header SHA与冻结清单相同。
两个目标runtime/debug SHA-1 build-id成对一致：

| 目标 | build-id |
|---|---|
| libavcodec | 805376f248504d2084e3e95470810873ffc3655a |
| libavutil | bb5b41f743b9b07bb38cc5007f7deb6516256579 |

RPM、源树与完整build.log保留temp；[build/002/result.json](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-04/formal/stages/build/002/result.json)记录真实路径、SHA、命令集合和构建锁。这里只通过单个BASE证据，不能宣称BASE/BASE-r/AFDO三方build-lock或consumption已经通过。

### 8.5 S2远端启动消失：停止事实与未知原因

BASE部署逐文件SHA通过后，首次PLAT BBB oracle启动命令为setsid bash .../control-PLAT-bbb-720p-60/launch.sh。
启动命令的主机/远端标记为0并写PID9973，但后续只读查询证明/proc/9973不存在；无oracle/gst进程、无exit文件，stdout/stderr均空，输出oracle目录未形成。
当时uid仍0，SDB连接未中断。这些事实不能证明oracle成功，也不能确定是SDB会话寿命、信号还是其他启动问题；**不把猜测作为实现修复依据**。
证据：[launch-raw](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-04/launch-raw/)、[逐次只读诊断](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-04/oracle-progress-readonly/)。

在缺少远端完成证据时，不重试负载、不替换原件；核对本任务run PID及完整argv后只发SIGTERM给该run，触发finally。
[停止收据](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-04/operation-failure-stop.json)明确这不是要求的S3恢复测试，也不是独立1block计时注入测试。
本次第二个workflow进程退出1来自signal15；远端负载真实退出码**未知**，不能写成远端退出1。

### 8.6 恢复、残留及验收表

finally完成：uid5001、policy0=schedutil、RPM1233、cleanup_pending=[]、errors=[]。
控制目录全部SHA校验拉回后删除。
额外核查发现BASE.tar不在自动清理日志内：非root读取Permission denied原文保留；随后记录状态、临时开root，全量SHA拉回到final-work-cleanup-root/pulled并写收据后，只删除本实验work目录，再恢复root off与schedutil。
BASE.tar SHA=37a94a03be8f4cade489b9205cd547c105ab7a8ac0c4a786989abe177e5db852。
**自动清理没有覆盖该tar是已知缺口**；此次最终清理依靠额外的verified-pull收尾，不能以cleanup_pending=[]声称自动清理验收通过。
variants/m1-ffmpeg-rpi4-thumb-01-BASE与tools/workflow-m1-ffmpeg-rpi4-thumb-01保留；没有AFDO变体。

| M1验收项 | 本轮结果 |
|---|---|
| S0身份、perf/libLLVM、硬件cycles、三输入SHA | 通过；唯一cycles/type0/config0；1.5GHz；温度/频率/电压告警来源已登记，固件历史unknown |
| 冻结108依赖、BASE构建与产物身份 | 通过（第二次BASE） |
| BASE/BASE-r/AFDO三项build-lock与离线重建 | 未到达，只有BASE锁 |
| PLAT三个输入oracle、BASE对照正确性 | 未完成；首次PLAT启动无完成证据 |
| must-load与全部deploy-set计时进程核验 | 未到达；仅BASE部署SHA已核对 |
| R=3训练、六次profile转换、锁定profile | 均0；未产生/读取真实sample profile |
| 两个目标AppliedSamples消费判定 | 未到达 |
| ToS估计/CI/判定 | 未计算 / 未计算 / 未执行 |
| Sintel估计/CI/判定 | 未计算 / 未计算 / 未执行 |
| S3后SIGTERM恢复复用 | 未到达 |
| 独立1block中断清理验收 | 未到达；本轮故障停止不冒充验收 |
| S7 report.json/report.md | 未到达；本停止报告不等同S7成功报告 |
| 最终root/governor/RPM与work残留 | root off、schedutil、1233；work全部verified-pull后删除，variants保留 |

### 8.7 资源、边界与后续

两次driver墙钟合计779.031秒（186.669+592.362，不含前期磁盘核查）；两次GBS合计267.862秒。构建峰值2,108,694,528 B，driver峰值257,687,552 B；M1已记录样本的最低MemAvailable 9,389,166,592 B（8.744 GiB）。无运行中资源停止/OOM。清理阶段只有实际抽样记录，缺少完整连续峰值，不补造。

没有改设计v0.3、hq、Gerrit、认证或其他项目；未安装软件；只停止本任务run；板上项目文件只写/opt/afdo_agent，root/governor变更按任务授权并恢复。
SDB已有服务可能自行更新WORKDIR外内部状态，未取得可列出的实际写入路径，不能声称已证实无此行为。其余未发现主动WORKDIR外项目文件读写。
Q.5#17：本轮没有进入训练转换阶段，没有生成/查看真实sample profile；仅SHA保存遗留与S0探测perf数据，没有分析其内容。

本轮停止。后续需先查明远端启动没有完成收据的原因，并补齐部署tar的清理登记，再继续M1；不修改判据或以旧手动结果替代。
[本轮证据索引](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-04/index.json)含原命令、失败原文、收据、资源和temp大文件SHA；ALL-END已写。


## 9. PM 授权前台启动、部署物清理与 attempt-05（2026-11-17任务）

### 9.1 边界与探测

仅操作192.168.108.26:26101；devices列表中的192.168.108.13未操作。身份仍为RPi4 Model B Rev1.5 / armv7l / 6.12.80-arm-rpi4-v7l / tizen-unified-toolchain_20261104.160709。初始uid5001、schedutil、RPM1233。探测前持久登记launch-probe目录，root变更也先登记；未改governor。

最小脚本写start、sleep20、end及exit=0。每种3次；后台方式同一命令保存PID、/proc/PID/cgroup和ps的PID/PGID/SID，返回后2秒、25秒检查。实际命令原文保存在transport索引，PID存入launched-pid文件。

| 方式 | 次数 | sdb墙钟秒 | 2秒状态 | 25秒／前台返回状态 |
|---|---:|---:|---|---|
| setsid | 1 | 0.183 | PID存活、start存在 | end存在、exit=0；PID已退出 |
| setsid | 2 | 0.250 | PID存活、start存在 | end存在、exit=0；PID已退出 |
| setsid | 3 | 0.200 | PID存活、start存在 | end存在、exit=0；PID已退出 |
| nohup | 1 | 0.208 | PID存活、start存在 | end存在、exit=0；PID已退出 |
| nohup | 2 | 0.242 | PID存活、start存在 | end存在、exit=0；PID已退出 |
| nohup | 3 | 0.225 | PID存活、start存在 | end存在、exit=0；PID已退出 |
| foreground | 1 | 20.203 | 前台阻塞 | end存在、exit=0；脚本完成后返回 |
| foreground | 2 | 20.287 | 前台阻塞 | end存在、exit=0；脚本完成后返回 |
| foreground | 3 | 20.279 | 前台阻塞 | end存在、exit=0；脚本完成后返回 |

setsid与nohup setsid均3/3正常完成；PID=PGID=SID，memory/devices/systemd cgroup仍为/system.slice/sdbd.service。**这些结果不支持“sdb退出必然杀死其子进程”的结论；上一轮负载消失的具体原因仍未证实。** 按PM决定，正式路径仍统一改为前台阻塞，不选用后台方式。全部探测文件SHA拉回核对后删除确切launch-probe目录；root恢复off、schedutil不变，pending=[]。

### 9.2 实现与测试

- launch现在使用前台`bash launch.sh`，sdb连接一直阻塞到完整round退出；脚本内部管理负载、遥测采样器和退出文件。Oracle/采集使用600秒负载预算，计时脚本含最长600秒温度门禁和600秒负载预算，整体1200秒；transport分别为预算+120秒。成功、异常退出、超时和SIGTERM均有清理路径。watchdog计时器使用自己新建的进程组，退出只停止该组及其负载组。
- S6预先列明的技术失败由整个block最多重试一次，保留失败尝试及部分round原件；正确性、身份门禁不按技术失败重试。
- host_artifact与run分开登记：主机来源tar、variants、workflow tools及新创建输入先登记后创建，核对主机原件SHA、远端SHA/符号链接与树成员后删除；未完成push的不同SHA不会被删除，保持pending。已存在的三份相同输入只读核验并复用，不取得其清理所有权。板上生成目录先verified-pull后删除；空目录也需远端前后清单一致。实验work父目录同样登记。
- S4中断后的恢复先复验收据，再从封存的主机来源重新部署，不重新执行已完成S0–S3的负载。独立注入测试只暂时恢复主会话root/governor，借用已验证主变体，不取得其所有权；子实验的脚本/work独立登记。
- 旧BASE变体与workflow工具目录已按attempt-04部署来源核对全部regular文件和符号链接后删除。旧脚本原文从e3b8409取证，未拿本轮修改后的脚本冒充旧原件；清理成功、root恢复off。
- PM实现修正不计自身缺陷次数。新增14个合成测试，原114个保留，128项通过；14份脚本（含生成示例）bash --posix -n通过。测试包含前台阻塞成功、负载非零、超时、transport中断、采样器异常清理、整block重试一次、正确性不可重试、创建前登记、部分push失败、SHA/额外成员拒删、拒绝已有非本任务路径。

### 9.3 自身缺陷修复记录（本轮上限3次）

首个正式命令通过S0、BASE GBS退出0（177.342秒），首次PLAT/BBB前台脚本退出0，但S2因`oracle caps mismatch format`停止，完整失败收据与原文保留。

1. 已登记BBB/ToS的caps是`I420,1280x720,30/1,progressive,1/1`简写，原解析器却对登记值要求GStreamer typed语法；实际原文为I420/1280/720/30/1/progressive/1/1，1800帧、2,488,320,000字节、SHA 3a4c3820c576697edd4ca34f3532c8af8ffaf04687955c5d6b35215b9b06c814均吻合。修正仅解析两种表示，比较全部登记字段，保留raw_caps；格式/帧率/扫描方式/像素比例反例仍拒绝。
2. capability文件生成时在已有末尾换行上再加换行，空行被严格的board sampler拒绝，原始遥测只有一个未闭合SAMPLE。修正生成器为恰好一个末尾换行，保留相同四个能力条目；不放宽采样器、频率/温度/电压或窗口判据。

真实原文夹具分别证明旧代码失败、新代码通过。累计130测试通过。使用2/3次；未将这两项混入PM豁免。初次失败finally已恢复root off、schedutil、RPM1233，variants/tools/work全部核验清理，pending=[]。S0及后代收据按DAG归档失效，旧host-artifacts登记封存SHA后移除活动指针；同一job/同一命令启动修复后的第二次执行，BASE重建正常。


### 9.4 最终停止点与验收表

修复后第二次执行S0、S1、S2通过：三个输入PLAT/BASE共六份oracle均与登记的帧数、字节数、SHA和caps一致，BASE的加载库核对通过。S2前台启动缺口已跨真实负载验证。

**停在S3身份门禁，workflow退出3：`no decoder loaded-library evidence`。** train-1的perf record与三份导出退出0，EOS完整，perf.data约1.328MB；拉回清单SHA逐项一致。保存的30份maps快照全部属于PID20061的`bash …/watchdog.sh 600 …perf record…`，没有任何一份包含libavcodec/libavutil。原件与逐份SHA、cmdline见`maps-gate-failure.json`。观察器当时没有保存子进程枚举读取结果，无法仅凭现有证据确定为何只遍历根进程。

不能拿之前的oracle maps、预设LD_LIBRARY_PATH或采集成功替代本次解码进程身份核查。此处属于证据缺失，原文不能证明门禁条件已成立，因此不作为第三次自动修复放行，也未重采或替换原件。未执行profgen转换或查看sample profile。一个训练原件完整保留，但正式接受训练RUN为0/3。

| 验收项 | 本轮结论 |
|---|---|
| 启动探测、前台负载 | 9次探测通过；真实oracle及首次训练负载前台退出0 |
| S0身份、工具、cycles、三输入SHA | 通过，两次执行均有收据 |
| S1 BASE构建与冻结108包、成对build-id | 两次构建退出0，构建后核对通过 |
| S2三个输入PLAT/BASE oracle | 修复后六项全部通过 |
| S3训练及加载库身份 | train-1采集/导出成功，但缺decoder maps证据；停止，不接受 |
| S4转换、锁定profile | 未到达；未产生新sample profile |
| S3后S4 SIGTERM恢复 | 未到达，不计前述正常失败finally为此测试通过 |
| BASE-r、AFDO、build-lock三项、consumption | 未到达 |
| 独立1block中断清理测试 | 未到达 |
| 预试、预登记、正式计时、S7报告 | 未到达 |

| 比较 | 估计 | 95% CI | 判定 |
|---|---|---|---|
| ToS（primary） | 未计算 | 未计算 | 未测量 |
| Sintel（secondary） | 未计算 | 未计算 | 未测量 |

普通失败finally清理现场核验通过，但不代替两项指定的中断验收。最终uid5001/root off、policy0=schedutil、RPM1233，cleanup_pending=[]、errors=[]。本实验work、BASE variant及workflow tools目录均确认不存在；三个既有输入与通用perf/libLLVM不属于本轮新增物，保留。两个driver service均MainPID=0、failed终态（退出2、3），没有本任务负载残留。

只读重试1次：PLAT/BBB control SHA清单首读没有退出码标记；重试的正文完全一致且真实退出码0后继续，原始stdout/stderr/时间全部保留。状态改动命令未重试，未kill-server或操作另一设备。

### 9.5 构建资源、清理与边界

每次构建均记录本实验本轮16GiB启动内存门槛豁免；load<12（20核）、磁盘≥50GiB保留，运行中6G/5G/200%、-j2/threads1、nice19/ionice-c3与60秒记录不变。

| BASE执行 | 启动MemAvailable B | load1 | 启动磁盘可用 B | 等待秒 | GBS秒 | 退出 | memory.peak B |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 10175823872 | 3.015625 | 111838666752 | 0.108 | 177.342 | 0 | 1531699200 |
| 2 | 10178826240 | 4.32666015625 | 110067023872 | 0.134 | 271.503 | 0 | 1152229376 |

两个driver墙钟分别322.942、1022.465秒，合计1345.407秒；GBS合计448.844秒。driver实读峰值230,383,616B，M1最低采样MemAvailable 9,229,725,696B；所有构建memory.events的high/max/oom/oom_kill均0，无资源停止或重试。普通scope测试130项通过；清理核查只保存了运行中观测峰值，最终峰值缺口在磁盘报告中明示，不以M1峰值冒充全任务峰值。

[磁盘第三轮](../../maintenance/disk_cleanup_2026-11-17.md)已在构建前结束：删除三个干净361624源码工作树，分配块合计7,792,844,800B；可用空间104,390,893,568→111,846,215,680B。18个chroot因sudo -n不可用尚未删除；RPM与日志保留证据、待用户执行的确切路径脚本及SHA见该报告。后续M1构建自身占用不计为清理收益。

本轮自身缺陷计数2/3；PM授权启动/清理修正不计数。没有改变设计v0.3、补丁、门槛、hq、Gerrit或既有证据；不安装软件、不触碰其他构建/其他项目。项目文件均写WORKDIR；板上文件只写/opt/afdo_agent，root/governor按授权操作并恢复。系统命令读取/proc、/sys、systemd/dbus运行元数据属于资源及状态核查；systemd/sdb自身的系统服务元数据或日志由系统维护，未对系统外部文件逐一作写入审计，不能声称完全无系统侧写入。首个cwd只读探测未套资源scope，其余主机任务按nice/ionice与scope/service限制执行。

证据：[本轮运行索引](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-05/run-index.json)、[启动探测及遗留清理](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-05/launch-probe/index.json)。大原件保留`temp/m1-ffmpeg-rpi4-thumb-01/attempt-05/`；未删除旧attempt。ALL-END，停止等待对解码进程枚举/身份取证缺口的处理决定，不进入后续测量。


## 10. 完整进程树观察与 attempt-06：间隔超限停止（2026-11-17任务）

### 10.1 范围、实现与测试

本轮 PM 授权修正 S3/S6 观察器，不占自身缺陷计数；设计 v0.3、hq、Gerrit 与旧证据不改。仅操作 RPi4 `192.168.108.26:26101`，身份仍为 Raspberry Pi 4 Model B Rev 1.5 / armv7l / `6.12.80-arm-rpi4-v7l` / `tizen-unified-toolchain_20261104.160709`。未操作 `.13`。

旧 `observe_maps.sh` 依赖 `/proc/<pid>/task/<pid>/children`，sleep 为1秒；新 `proc_tree.sh` 从 `/proc/*/stat` 提取 PPID，并计算根PID的完整后代闭包，不依赖 pgrep 或 children 文件。stat 的 comm 按最后一个右括号切分，保留 PID、PPID、PGID、SID、starttime；每次保存完整枚举表、选中表与采样时间。每个后代保存 stat/comm/cmdline/maps、结束时 stat 与 complete 标志；读取失败原文保留，PID复用或未完成快照不作为成功证据。

解码进程规则由 `workflow/packages/ffmpeg/workloads/decoder.json` 声明：可执行名与完整 argv（本 round 输入路径替换）精确匹配，不在通用判定逻辑中硬编码 gst-launch。S3/S6 共用 `board.decoder_maps`：唯一 PID/starttime、完整快照、全部 must-load、deploy-set 路径与 SHA。动态加载初期尚未包含完整 must-load 的快照不计成功；任一已出现的部署 DSO 路径/SHA 不符即失败。PLAT oracle 仍按其自身系统库定义，其他 oracle 直接记录自身 gst 子进程。

S3 增加 `check_perf_buildids`，两目标 build-id 必须与 S1 一致，但绝不代替 maps。workload JSON 纳入收据输入 SHA 链。

运行前140项测试通过（原130项保留），12个board shell语法检查通过。新增10项覆盖三层树、短暂存在的解码进程单次快照、只见根进程、/usr误加载、多个候选、读取失败原文、错误管线、attempt-05全部30份真实maps、build-id交叉证据。attempt-05 cmdline从保留原件提取到 `workflow/tests/fixtures/attempt05-root-cmdlines.json`，逐条记录来源与SHA；旧结果仍被拒绝。第一次测试因cmdline原件不在Git导出目录而失败，原日志保留；修正夹具来源后通过，未改旧证据。

**实际结果不满足本轮观察间隔要求。** 新循环虽设 `sleep .1`，但枚举、快照、逐路径 SHA 均串行发生在循环内，不能把 sleep 当作实际采样周期。停止后补上 `observer_cadence` 主机硬断言：时间必须有限且递增，每段间隔≤0.5秒，缺证据也拒绝。没有提高上限，没有重新采集。运行时版本与停止后版本分别由 `code-sha.json`、`final-code-sha.json`封存。

### 10.2 单命令运行与真实观察结果

新目录 `temp/m1-ffmpeg-rpi4-thumb-01/attempt-06/`，同一实验ID/job设置；仅隔离 source/output、更新本轮授权文字。源码独立clone、同一基线与patch；运行入口：

```sh
PYTHONPATH="$WORKDIR/workflow" python3 -m afdo_wf run --job "$WORKDIR/temp/m1-ffmpeg-rpi4-thumb-01/attempt-06/job.json"
```

实际独立systemd service与完整argv见 `launch-service.json`；所有主机命令 nice19/ionice-c3，控制任务3G/200%，GBS独立6G/MemoryHigh5G/200%、-j2、threads1。driver原计划在S3收据完成后、S4运行中SIGTERM再以同命令恢复；本轮未到达该触发点。

S0、BASE构建、S2全部通过。108包冻结清单校验通过；完整候选/对照build-lock与BASE-r仍未执行。

| 输入 | PLAT/BASE帧数 | 两侧输出SHA-256（相同） |
|---|---:|---|
| BBB | 1800 | `3a4c3820c576697edd4ca34f3532c8af8ffaf04687955c5d6b35215b9b06c814` |
| ToS | 1800 | `4c2610c37b7790240c9158277981ed9c3ac81399e3e9df554ffebb2d2ff80c4e` |
| Sintel | 1440 | `91d171c0cd99266d0efeee7b9023a77bf39c925ec372bcd1d1e7efaf08ecd193` |

S3 train-1的采集/导出退出0，完整SHA拉回。真实树包含 watchdog Bash PID16762 → perf PID16764 → gst-launch PID16801，另有timer/sleep及短暂子进程，总计7个PID。唯一解码候选16801，26份完整快照通过完整管线与两目标库SHA/maps核对；5份其他进程读取失败快照保留原文，不计成功。build-id交叉证据：

| 目标 | S1与perf buildid-list共同值 |
|---|---|
| libavcodec | `805376f248504d2084e3e95470810873ffc3655a` |
| libavutil | `bb5b41f743b9b07bb38cc5007f7deb6516256579` |

但32个采样起点的31个间隔中，**28段>0.5秒**；最小0.26秒、中位1.08秒、最大1.16秒。完整树捕获修复成立，观察器实时性验收失败；train-1不能接受。证据：`process-observation-summary.json`、原 `maps/samples.tsv` 与 `cadence-stop.json`。串行取证耗时是实现上可见的风险，但没有逐操作计时，不能把超时精确归因于某一个命令。后续须降低采样关键路径耗时并重新验收，不能仅进一步缩短sleep。

### 10.3 停止缺陷、原件保全与恢复

发现间隔超限后，对核实属于本job的run PID732068发送SIGTERM。原信号处理器抛 `InterruptedError`，在 subprocess communicate/select 等待中被当作可重试的中断，未退出；原文显示拉回后还执行了train-1正确性检查并短暂启动train-2。**这是停止处理失效的边界例外，不是授权追加训练，也不计成功。**

随后再次核实PID命令行，只对本任务run发SIGKILL、对其自身SDB客户端发SIGTERM；未kill SDB服务、未停止其他进程/单元。driver记录子进程-9，服务ExecMainStatus247；本轮不是S4恢复测试通过。使用现有清理日志和身份核对执行手动restore。

首次train-2拉回期间，`collect.log` 与 `perf.data` 的SHA发生变化，按原门禁不接受该单独拉回、不直接删除该目录，原错误和前后清单保留。随后父work目录完整拉回并核对，收据包含206个文件，其中204个属于train-2；主机再次逐个SHA核对通过，父目录才按收据删除。原train-2失败副本也保留。最后只读确认远端目录已不存在，以父目录verified收据为依据核销冗余子目录cleanup条目；没有盲目重试删除。见 `manual-restore-final.json`、`cleanup-pull-change.json`、`cleanup-pending-before-reconcile.json`、`cleanup-reconcile.json`。

最终uid5001/root off、schedutil、RPM1233；work、BASE variant、workflow tools全部不存在，未发现遗留负载（ps匹配仅查询自身；随后按starttime核查两次训练捕获的13个PID，全部不存在，见final-pid-check.json）；通用工具与既有inputs保留；cleanup_pending=[]、最终reconcile errors=[]。首次restore错误仍保留，不能将其描述为自动finally清理一次通过。

自身缺陷修复 **1/3**：停止后以合成子进程证明旧 `InterruptedError` 在communicate期间被吞后继续，而新的非OSError控制流异常 `StopRequested` 立即退出并执行finally。应用到live与board session，不改变门禁。另补0.5秒边界/超限测试；最终**143项测试通过**。未恢复正式实验。准备heredoc最初有缺括号的SyntaxError，未执行任何语句，修正后才启动；记录在 preparation-diagnostic.txt。

### 10.4 M1验收与资源

| 验收项 | 本轮结论 |
|---|---|
| S0身份/cycles/工具/输入SHA | 通过 |
| S1 BASE及108包冻结核对 | 通过 |
| 完整build-lock三项、BASE-r | 未到达 |
| PLAT/BASE三个输入oracle | 六项通过；AFDO/计时后检查未到达 |
| S3解码进程maps与build-id | train-1身份取证通过，但间隔超限，采集整体不接受 |
| 有效训练 | 0/3；完整原件1份，中断原件1份 |
| S4转换、锁定profile、S5 consumption | 未到达；新profile生成/打开0 |
| S4 SIGTERM恢复、独立1block注入清理 | 未到达，不以本轮手动恢复替代 |
| S6/S7 | 未到达 |
| ToS估计/CI/判定 | 未测量 |
| Sintel估计/CI/判定 | 未测量 |

BASE构建墙钟140.946741秒、退出0，启动等待0.074606秒；启动MemAvailable9,929,777,152B、load1=1.7412109375（nproc20）、可用磁盘248,596,525,056B。仅本次实验豁免16GiB启动内存门槛，load<12与磁盘≥50GiB、运行中保护均保留。构建memory.peak=2,034,958,336B，最低MemAvailable9,855,733,760B；driver峰值229,380,096B。high/max/oom事件0，无资源性停止。driver墙钟1016.952434秒；手动restore另计46.829秒。运行前测试scope峰值33,546,240B；短命令及停止后测试的最终cgroup峰值未逐条封存，不宣称全会话全覆盖峰值。

磁盘：只读核查原18路径全部已不存在，可用248,767,696,896B；本轮删除0，未执行sudo脚本，无额外清理。见清理报告第三轮后续小节。

静态阅读另发现未到达的注入路径仍有 `self.transporself.push_owned` 拼写错误；本轮未执行或修改该路径，不宣称注入验收通过，后续需修复并测试。资源与平台状态仅按证据报告；系统工具自身的系统级元数据写入未作完整审计。未触碰受保护的三个untracked配置，未操作WORKDIR外项目、hq、Gerrit或设计。

**本轮已结束：完整进程树可取证，0.5秒采样要求未通过。停止等待后续处理，不继续质量/性能推断。** 证据索引：[attempt-06](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-06/run-index.json)；实际相对位置为 `docs/workflow/runs/m1-ffmpeg-rpi4-thumb-01/attempt-06/`，大原件留同名temp目录并记录SHA。
