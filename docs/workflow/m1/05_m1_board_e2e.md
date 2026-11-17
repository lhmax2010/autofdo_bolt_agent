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


## 11. PM观察器判据更正、SHA去重与attempt-07（2026-11-17任务）

### 11.1 本轮裁决与实现

PM明确：上一轮0.5秒上限并非设计v0.3门禁，本轮作废；旧记录保留。新S3/S6共同判据为：完整管线唯一识别解码进程；至少两份完整must-load快照；任何快照中的deploy-set DSO均须来自正确变体且SHA一致；采样时间有限、严格递增，相邻间隔>5秒为技术失败，按既有block技术重试规则处理。实际最小/中位/最大间隔仍记录。不修改设计v0.3文件。

采样循环保留stat/PPID完整后代树与逐进程原始快照，maps同时保存path/dev/inode。独立hash队列按唯一三元组去重，首次哈希前后核对文件dev/inode，且本round根进程须仍存在；SHA结果供所有相同身份的快照引用。采样循环不再逐快照SHA；观察器和hash子进程置于CPU0，负载仍CPU3。观察器退出时等待hash队列结束，保留失败日志。兼容旧attempt-06逐快照SHA原件仅用于历史复核，不改原件。

`self.transporself.push_owned`已修正为`self.push_owned`；新增不连板的合成路径测试，实际执行独立injected_run的脚本/能力/manifest部署调用与会话finally。运行前150项测试通过：原规则测试按PM新门槛更新，新增实际attempt-06全量身份复验（26份成功快照、最大1.16秒，通过新规则）、根进程/外部库/单份快照拒绝、>5秒技术失败、有限递增时间、SHA只计算一次及注入路径测试。

本轮PM授权修正不计自身缺陷次数；继承上轮停止信号修复1/3。新attempt-07使用相同实验ID、输入、冻结仓库、策略和种子；新source/output隔离目录，代码变更从S0开始。当前实验本轮继续豁免16GiB构建启动门槛，load/磁盘/运行中保护不变。完整收尾见11.3–11.7。


### 11.2 attempt-07：观察器通过、S4真实恢复通过，S5记录来源缺陷

三个训练RUN的完整解码器快照为56/56/57份，间隔最大0.70/0.69/0.69秒；每轮8个唯一(path,dev,inode)，实际SHA调用8次。无旧0.5秒断言。原始树/maps仍在temp，收据摘要与索引归档于本节证据。

S4实际运行时SIGTERM：第一次run退出143，`StopRequested`未被吞掉；finally恢复uid5001、schedutil、RPM1233、cleanup_pending=[]。同一命令第二次验证并复用S0–S3，collect收据SHA不变，从convert/002继续。6次转换成功，锁定profile SHA `ecd606489690ab92cf0b883ac2cd6978b845f031f28a11f733bc223f9245e35b`，跨DSO冲突为空。

BASE、BASE-r、AFDO三个GBS均退出0，墙钟129.919/122.747/119.783秒。两套build-lock均通过。S5在consumption停止：libavcodec/libavutil分别有1947/62条正数AppliedSamples，实际目标源码311/97条Clang命令都带准确sample-use，但程序把合并进ELF的3条GNU支持库producer记录也当成目标源码命令，误报missing sample-use。冻结root的libgcc.a与crtbeginS.o/crtendS.o原始readelf记录逐字证明其来源（`attempt-07/consumption-diagnosis/`）。两个目标.text已变化、chroot profile SHA正确；失败原件不改。

按用户自身缺陷规则本轮使用第2/3次（继承上轮1/3）：保持build-lock全部记录不变；消费检查将实际`-c/-o`目标源码命令与有冻结依赖原文证明的GNU/libgcc记录分开。未知记录仍拒绝，目标源码缺sample-use仍拒绝。真实失败先复现，新增来源缺失、错误目标、源码缺选项不可被排除等测试；总155项通过。修复后新attempt-08使用同一实验配置，从S0重做，未改设计/阈值/补丁/spec。attempt-07结束总墙钟2047.209秒，恢复无错误；没有计时结果，注入计时清理测试尚未到达。

### 11.3 attempt-08：S0–S5与恢复验收，S6拉回失败停止

**M1未完成；停止，不再启动负载或修改代码。** 本轮代码与attempt-07检查点已提交并推送 `5b4af659819776c9b4132325626486ee835dba31`。attempt-08使用同一job配置、不同输出目录，由单条 `python3 -m afdo_wf run --job <attempt-08/job.json>` 调度；S4中断后重复同一命令。原始命令、运行/恢复日志和文件SHA见 [attempt-08证据索引](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-08/run-index.json)，下文证据路径均相对该索引的 `run/`（大原件位于同结构temp目录，由raw-index定位）。运行代码的最终SHA复核全相同，见 `code-sha-final-check.json`。

| 验收项 | 本轮结果 | 证据 |
|---|---|---|
| S0身份、硬件cycles、输入SHA、能力清单 | 通过；RPi4 Model B Rev1.5，armv7l，6.12.80-arm-rpi4-v7l，TZ_BUILD_ID=tizen-unified-toolchain_20261104.160709；仅操作192.168.108.26:26101 | formal/stages/preflight/001/、host-artifacts/transport索引 |
| S1 BASE构建与S2部署/PLAT oracle | 通过；冻结108包，三个输入PLAT/BASE输出一致 | formal/stages/build/001/、formal/stages/deploy/001/ |
| S3训练与maps/build-id | 3/3通过；唯一解码器、重复完整快照、正确部署DSO，perf build-id交叉证据通过 | formal/stages/collect/001/train-{1,2,3}/ |
| S4真实SIGTERM、收据恢复 | 通过；第一次退出143，StopRequested未被subprocess吞掉；恢复复用S0–S3，convert/002重新转换 | recovery-interruption.json、recovery-verification.json、workflow-run-{1,2}.log |
| S5 build-lock与BASE-r | 两套三项门禁通过；BASE-r产物逐字节相同，选BASE作对照 | formal/stages/rebuild/001/buildlock.json、result.json |
| 两目标consumption | verified；libavcodec/libavutil正数AppliedSamples记录1966/54，目标源码命令311/97、chroot profile SHA、.text差异通过 | formal/stages/rebuild/001/consumption.json、consumption-provenance-summary.json |
| 计时前正确性 | BASE/AFDO × BBB/ToS/Sintel六项通过，和PLAT oracle一致 | formal/stages/measure/001/pre-*-oracle.json |
| 独立1 block计时中断清理 | 通过；在独立cleanup-test的watchdog/perf运行中SIGTERM，finally清理、root/governor恢复、pending/errors均空 | formal/stages/measure/001/injected-job/injection-active.json、final-1794918640181146896.json、injection-driver.log |
| ToS预登记/正式测量 | 10次BASE预试、4次预热完成；正式2/10 block完整，第3个block首轮拉回失败 | formal/stages/measure/001/tos-720p-60-plan*.json、rounds.json、tos-720p-60-blocks.json、failure.json |
| 全部计时进程maps门禁 | 已接收4个正式round全部通过；第3 block未完成拉回，未作为通过/有效数据计入 | 各formal-*/maps/decoder-check.json、stop-summary.json |
| Sintel测量、计时后正确性、敏感性/失衡终判 | 未到达；Sintel的计时前正确性通过不等于测量通过 | measure失败收据 |
| S7 report.json/report.md | 未生成；本节为停止报告，不是完整S7验收报告 | service-final.txt、driver-end.json |

S4中断时间为epoch 1794917093.0250928；第一次finally文件 `formal/final-1794917168597233604.json` 记录uid5001、schedutil、RPM1233、cleanup_pending/errors为空。collect收据SHA `24edc588b87c3dc106fe85f476e125688cef333b4cefbc485f7448c9d1f2d0ea` 在恢复前后不变；preflight/build/deploy/collect各仅001，转换失败原件001保留、成功结果002。继承的StopRequested修正在本轮两次真实S4中断均按143退出并执行清理。

独立计时注入在epoch 1794918558.536644记录watchdog16494/perf16496，SIGTERM与最终恢复证据分别保存；不含正式结果，未替换正式block。它证明本轮拼写修正实际走到了该路径。此成功不掩盖下述正式拉回失败时的清理日志缺口。

### 11.4 实际观察器间隔、转换与profile披露

| 训练RUN | 完整must-load快照 | 起点样本数 | 最小/中位/最大间隔（秒） | 唯一SHA三元组/实际SHA调用 |
|---|---:|---:|---|---|
| train-1 | 57 | 64 | 0.29/0.50/0.74 | 8/8 |
| train-2 | 56 | 63 | 0.29/0.50/0.78 | 8/8 |
| train-3 | 57 | 64 | 0.29/0.50/0.69 | 8/8 |

已验收的训练、ToS预试、预热与4个正式round共21份decoder-check，采样间隔全局最小0.26秒、最大0.94秒；各轮中位数0.49–0.50秒（逐项原值见stop-summary），均无>5秒。每轮均8个唯一三元组、8次SHA调用。最后未接受的第3 block不在这个统计内，不以回收原件补判身份或计时有效。

六次转换退出0，conversion=ok、identity=verified；三个可选质量门槛未设置，sampling_adequacy=unknown，不称质量矩阵已通过。跨DSO顶层键冲突为空，合并锁定profile SHA：`a5b867326dcf0c6dc85a4899034812e3f986e3855d063d47ab4be6e2a0d0a4b2`。

| RUN/DSO | 目标样本 | usable | in_func_no_line | outside_dwarf_func | unmapped_in_target |
|---|---:|---:|---:|---:|---:|
| train-1-libavcodec | 40296 | 23939 | 4296 | 12061 | 0 |
| train-1-libavutil | 113 | 93 | 5 | 15 | 0 |
| train-2-libavcodec | 40376 | 23977 | 4204 | 12195 | 0 |
| train-2-libavutil | 116 | 90 | 10 | 16 | 0 |
| train-3-libavcodec | 40459 | 23824 | 4241 | 12394 | 0 |
| train-3-libavutil | 118 | 88 | 10 | 20 | 0 |

outside_dwarf_func的no_cu/in_cu_no_subprogram/plt子项详见stop-summary与原quality；它们不是额外互斥顶层桶，不能重复求和。本轮未计算5.8质量指标。

Q.5第17项披露：attempt-07/08的本次FFmpeg训练perf script各3份，用于各DSO显式max/none/none/none、period=1000003转换及消费构建；convert/001为中断尝试、convert/002各6份成功profile及一个锁定合并profile，文件路径、SHA、命令/时间与用途保存在各convert目录的披露/命令记录与raw-index。既有正式质量评估sample profile未打开；本次训练profile已生成、查看质量JSON并用于AFDO重建，将来登记须保留此披露。锁定profile不进Git，大原件只留temp。

### 11.5 ToS未完成数据与停止原因

ToS BASE十次预试墙钟：33.348、33.348、33.497、33.605、33.448、33.701、33.405、33.316、33.382、33.690秒；CV=0.4300324582%，锁定N=10。4轮clean、6轮telemetry_missing（missing window edge）；保持原标签，未补点、删轮或替换。计划于epoch1794920963.8707333写入，先于预热与正式计时，order_seed=2026111701，bootstrap_seed=2026111702，epsilon=1%，每变体预热2轮；主比较ToS，Sintel次要且不做多重比较校正。

| 已完成block | BASE秒 | AFDO秒 | BASE标签 | AFDO标签 |
|---|---:|---:|---|---|
| 1 | 33.352 | 32.775 | telemetry_missing | telemetry_missing |
| 2 | 33.480 | 32.780 | clean | telemetry_missing |

**ToS：inconclusive (incomplete)，估计与CI为null；Sintel：未开始，估计/CI/判定均无。** 只展示已完成原值，不以2个block计算完整N计划的结论。20%/标记失衡与敏感性终判未执行；不把不完整数据包装成faster/slower。计时后oracle未到达，旧手动试跑−2.565%不作为此次自动化结果。

第3 block首个BASE round的SDB拉回客户端退出 **-13（SIGPIPE）**：`formal/transport-1794917170396570931/000487.json`，epoch1794922882.077030至1794922936.5084164。stderr空，stdout只有部分文件复制进度。现有证据不能确定网络断连或SIGPIPE根因。负载产生物保留，不把本轮认定有效，也未启动第二次block或Sintel。

当前SDB.pull非零退出沿普通GateError退出，未归入TechnicalFailure，因此没有执行设计§8.3的整block一次技术重试。**这是尚未闭合的错误分类/恢复实现缺口，不是重试已通过。** 本轮未以自身缺陷规则绕过板上操作失败，没有继续改代码重跑；需PM处理。自身缺陷累计2/3（上轮StopRequested 1次，本轮消费来源判据实现1次）；PM观察器与拼写授权修正不计次数。

### 11.6 失败原件保全与最终恢复

最终自动finally文件 `formal/final-1794923529579839541.json` 记录root off/uid5001、schedutil、RPM1233；只读重试0。**cleanup_pending仍为2，errors为2**：`unverified run has no cleanup metadata`、`pull destination already exists`。它们均对应第3 block部分拉回目录：一条重复登记缺元数据，另一条因本地部分拉回目录已存在而拒绝。原final、cleanup.json和失败收据未改写，不称自动清理日志闭合。

随后自动父目录兜底拉回成功：`formal/remaining-work-1794917175605086440.pull.json`，3152文件全部属于失败round，板上/本机SHA一致后才删除父work确切目录；收据SHA `99e10f3c7ca797371a5834906b1ff2424d06739067a8d68cfe14b45af0812208`。父目录拉回已保全完整原件，但子目录待办未随父目录删除核销。

停止后独立只读核对（`post-stop-readonly/`、`post-stop-reconciliation.json`）逐文件再验这3152份本地原件，全部一致；确认实验work、失败round子目录、BASE/AFDO variants、专用workflow tools、cleanup-test work/tools七个确切路径均不存在；身份未变、uid5001、schedutil、RPM1233。没有再次删除、重试负载或修改原journal。**板上物理目录清理得到独立证据，自动收据仍有2条过期待办；两者分别报告。** 通用perf/libLLVM/三个输入按原计划保留，不声称板上整个afdo目录为空。

服务已结束（ExecMainStatus=2、ActiveState/ SubState=failed），不是后台继续运行；结束记录为driver-end.json及ALL-END.log。本次失败未达到M1全验收。

### 11.7 资源、等待、边界与封存

各构建仍使用6G/5G/200%、nice19/ionice-c3、-j2、threads1串行，只有本实验本轮的启动MemAvailable≥16GiB条件豁免；load<12（20CPU）和磁盘≥50GiB检查均通过。全部启动资源为实读，不从豁免推断可无限用内存。

| attempt/构建 | 退出 | 墙钟秒 | 等待秒 | 启动MemAvailable B | load1 | 启动可用磁盘B | cgroup peak B |
|---|---:|---:|---:|---:|---:|---:|---:|
| attempt-07/BASE | 0 | 129.919 | 0.066 | 17449410560 | 1.659 | 241765801984 | 2140409856 |
| attempt-07/AFDO | 0 | 119.783 | 0.041 | 19764240384 | 2.627 | 232043118592 | 1854152704 |
| attempt-07/BASE-r | 0 | 122.747 | 0.054 | 19530309632 | 2.244 | 233560002560 | 1904500736 |
| attempt-08/BASE | 0 | 133.656 | 0.041 | 19124776960 | 2.896 | 229983764480 | 2054737920 |
| attempt-08/AFDO | 0 | 226.342 | 0.087 | 18964172800 | 3.566 | 219005349888 | 1661124608 |
| attempt-08/BASE-r | 0 | 338.967 | 0.056 | 18792701952 | 2.831 | 220951310336 | 1940631552 |

六次GBS合计1071.415秒，high/max/oom/oom_kill均0，没有资源停止/重试。attempt-07 driver墙钟2047.209秒，attempt-08为8345.505秒，合计10392.714秒（2小时53分12.7秒；不含阶段间代码修改、报告封存时间）。长期driver采样最低MemAvailable **15,040,495,616B（14.008GiB）**；构建峰值 **2,140,409,856B（1.993GiB）**；driver峰值 **778,166,272B**，最低可用磁盘210,372,747,264B。每60秒原始meminfo与cgroup采样、各构建启动/结束在driver-resources与execution资源记录；短诊断/测试/收尾scope没有完整峰值封存，不把长期采样峰值宣称整轮所有进程绝对峰值。

运行期间不改设计v0.3、hq、Gerrit、既有原件或补丁/spec；未安装软件、不kill sdb服务、不碰.13与其他构建。板上仅本实验/授权afdo目录的文件操作，加已授权root/governor临时切换；finally恢复原状态。主机产物都在WORKDIR；系统服务（SDB/systemd/GBS系统日志）的外部元数据写入未做全机审计，不能证明完全为零，未为审计而读取其他项目或修改系统状态。受保护config/及两GBS配置未读未动。本轮未增加磁盘清理操作。

证据封存：小文件及分片全部<1MB；raw-index对已有verified-pull的原始maps明确标注sha256_basis=verified_pull_receipt及收据SHA，其余与入库小文件重新计算SHA。仅终止并重启过本轮归档辅助脚本以避免重复磁盘读取（第一次退出143），未重启正式workflow；原件不改。原perf/profile/RPM/maps大集合留temp，由run-index→manifest-sha/copied-index/raw-index给出SHA。成功结果、失败原件、中断收据、父目录保全及后续只读核验并存。本轮停止，待PM决定SDB拉回技术失败分类与清理收据核销后再授权恢复；不自行补测或放宽条件。

封存核对通过：74,334项原件索引，其中69,127项引用23份verified-pull收据、5,207项归档时重算；归档含1,231份小文件副本及47份transport分片。导出文件1,409个、83,056,038字节（不含随后写入的核对记录），全部<1MB；所有入库文件SHA与清单一致。见 [export-validation.json](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-08/export-validation.json)。

## 12. PM授权单文件拉回、技术失败分类与遥测握手（2026-11-17任务）

### 12.1 授权、实现与运行前验收

PM授权的三项修正不计自身缺陷次数，继承2/3。本轮不改v0.3、门槛或判据；不合并attempt-08的两个block。全局收据输入包含所有workflow模块，本次live/transport/receipts及板上脚本SHA改变，不能证明S0–S5代码输入相同；逐模块比较保存在attempt-09/reuse-decision.json，因此新attempt-09从S0重做。

S6的push/pull/shell非零（包括-13）、超时、缺可信退出标记转换为TechnicalFailure，退出码与stdout/stderr仍保留；操作本身不盲目重试，正式block按既有paired_block整对最多两次。正确性/身份/maps内容门禁的GateError保持不变。部分本地拉回目录移动到该block的failed-attempt-n，成功收据不移动；下一try采用不同round/目录。失败清理使用新恢复目标，不覆盖部分原件。

拉回改为不压缩tar：打包前登记round与唯一transfer目录；板上保存members.sha256、round.tar、archive.sha256，主机只拉这三个文件，核tar/清单SHA、安全解包、逐成员SHA与板上未变化清单；均通过才删除确切round和transfer目录。拒绝链接、设备、路径越界、重复或缺失成员。包的原件留temp。父目录verified-pull并删除后，引用父收据SHA自动写子待办核销记录；不以目录消失替代证据。attempt-08两条过期待办仅新增独立核销收据，引用post-stop-reconciliation及3152文件父收据，原journal不改。

遥测保持设计[start−1,end+1]窗口。sampler写完整SAMPLE/END后原子发布ready；负载等首样本时间+1秒已到达才开始；负载结束请求end+1秒的完整尾样本并等done后停止。所有时间仍取/proc/uptime。固定sleep不再充当首尾覆盖证据。判定器stats.telemetry未改。

运行前171项测试、15份bash --posix -n通过；新增测试含SIGPIPE整block重试及二次失败停止、部分目录保留、tar SHA/缺成员/解包/路径失败、父收据核销、真实14轮遥测原件复验、合成反事实握手时序，以及直接执行同一measure.sh/telemetry.sh的主机合成握手测试。反事实数据只用于测试，不修改或重新标记旧轮次。

正式计划前必须运行独立实验m1-ffmpeg-rpi4-thumb-01-telemetry-check的三轮BASE，三轮全部clean才继续。预试、N、顺序与计划重新生成：ToS order_seed=2026111709、bootstrap_seed=2026111719；Sintel分别+1，种子在本次运行前job已固定。旧恢复/注入成功证据保留；因从S0重跑，原driver仍会自然执行S4中断恢复及独立计时注入路径。

### 12.2 attempt-08缺边逐项证据

旧脚本在启动sampler后sleep1，但sampler首条记录可能晚于sleep起点；首样本到负载开始不足1秒，缺左边10–30ms。结束sleep2也未与采样周期握手，个别尾样本距end+1还差20ms。这里缺的是设计窗口边界，并不代表首样本晚于负载本身。原始uptime仅到0.01秒，毫秒值按其分辨率报告，不外推更高精度。

| 轮次 | 缺左边ms | 缺右边ms |
|---|---:|---:|
| formal-tos-720p-60-1-try0-AFDO | 30 | 0 |
| formal-tos-720p-60-1-try0-BASE | 10 | 0 |
| formal-tos-720p-60-2-try0-AFDO | 10 | 20 |
| formal-tos-720p-60-2-try0-BASE | 0 | 0 |
| pilot-tos-720p-60-0 | 0 | 0 |
| pilot-tos-720p-60-1 | 0 | 0 |
| pilot-tos-720p-60-2 | 10 | 0 |
| pilot-tos-720p-60-3 | 0 | 0 |
| pilot-tos-720p-60-4 | 0 | 0 |
| pilot-tos-720p-60-5 | 10 | 0 |
| pilot-tos-720p-60-6 | 10 | 0 |
| pilot-tos-720p-60-7 | 10 | 0 |
| pilot-tos-720p-60-8 | 20 | 0 |
| pilot-tos-720p-60-9 | 10 | 0 |

合计预试6/10、正式3/4为missing window edge；来源路径、SHA及完整时间见telemetry-diagnosis.json，原标签原样保留。

### 12.3 本轮运行结果

**按非正式检查门禁停止，M1未完成。** attempt-09从S0重做，S0–S5成功；S4真实SIGTERM恢复、独立计时注入清理再次成功。两个正式比较均未开始，不计算估计、CI、敏感性或标记失衡终判，不把attempt-08的2个block合并进来。第三轮非正式检查未执行，S7未执行。

证据入口：[run-index.json](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-09/run-index.json)，其中run/stop-summary.json、formal/stages/measure/001/telemetry-check-job/check-rows.json与各check的原始telemetry.tsv可交叉核对。大原件仍在temp/m1-ffmpeg-rpi4-thumb-01/attempt-09/。

| 非正式BASE轮 | 负载start/end（uptime秒） | 首/尾样本 | 起跑门禁读数 | 窗口温度范围 | 结果 |
|---|---|---|---|---|---|
| check-0 | 115168.99 / 115203.08 | 115167.89 / 115204.81 | 59.400°C | 58.913–66.218°C | clean |
| check-1 | 115243.25 / 115277.65 | 115242.25 / 115278.94 | 59.887°C | 60.374–65.244°C | telemetry_anomaly：temperature |
| check-2 | 未执行 | — | — | — | 前轮非clean，停止 |

两轮均覆盖[start−1,end+1]，missing=[]。check-1首样本恰在start−1秒、温度60.374°C，高于起跑60°C条件；它与更早start-gate.log中的59.887°C是两次真实读数。此次是真实温度标记，不能通过删除边界样本、提高阈值或归入可重试transport失败来消除。窗口握手修复成立，但三轮全clean的进入条件不成立。轮内最高温度没有超过80°C，不能据此忽略起跑条件。

### 12.4 M1 §14逐项验收与恢复

| 验收项 | 本轮状态与证据（run/内相对路径） |
|---|---|
| S0身份、硬件cycles、输入SHA、遥测能力 | 通过；formal/stages/preflight/001/result.json及探测原件 |
| S1/BASE-r/AFDO构建与build-lock三项 | 通过；formal/stages/rebuild/001/buildlock.json；AFDO与BASE-r均differences=[] |
| BASE-r离线重建与对照选择 | 字节一致；offline_reproducible=true，control=BASE；rebuild/001/result.json |
| PLAT oracle与BASE、候选正确性 | BBB/ToS/Sintel三片通过；deploy/001及measure/001的pre-control/pre-candidate六份oracle；正式计时后复核未到达 |
| S3进程树/maps、deploy-set、交叉build-id | 三RUN通过；train-1/2/3分别57/57/56份完整DSO快照，最大间隔0.66/0.67/0.68秒；collect/001各decoder-check.json |
| S4六次转换、合并 | 通过，identity=verified、conversion=ok；锁定SHA e1a6960cb91d04dd386b67fffae8a56e9c72613db8240c047b2e57345457a0a4 |
| S5 consumption | 两库verified；libavcodec 1959条、libavutil 56条正NumSamples AppliedSamples；profile SHA、.text变化共同门禁通过 |
| S4 SIGTERM与同命令恢复 | 第一进程退出143；S0–S3复用，collect收据SHA前后相同f38a89f77f114f5dec34ca28a26fce3669ed88a7ab9182c4221082d6e885a15f；convert/001原件保留、convert/002成功；StopRequested真实清理完成 |
| 独立1 block计时中断清理 | 通过；measure/001/injected-job的injection-active、signal15日志与final，uid5001、pending=[]、errors=[] |
| 三轮非正式clean检查 | 失败，第二轮温度异常；不再执行第三轮 |
| 新预试/CV/N/计划、ToS主比较、Sintel次比较 | 均未开始；无估计、CI或性能判定；20%/失衡/敏感性尚无正式数据可判 |
| S7 report.json/report.md及固定声明 | 未到达；本节为停止报告，不能充当M1成功报告 |

本轮真实S6没有使用整block技术重试（0次）；非零/信号退出与第二次失败停止已由合成测试覆盖。正式运行前代码30文件SHA锁定并在结束复核不变；未修改运行中代码。此次三项PM授权修正不占次数，自身缺陷使用仍为2/3。

Q.5第17项披露：本轮新采集3份BBB训练perf script，按两个DSO生成6份成功profile并合并用于本轮AFDO消费；convert/001为恢复测试中断原件、convert/002成功。路径、时间、参数与SHA列在转换收据及raw-index。未读既有正式质量评估profile，未计算质量矩阵受控量。

### 12.5 清理、限制与资源

退出时独立非正式检查已恢复root off；父流程随后尝试清理root拥有的部署物，出现Permission denied、链接路径错误与list index out of range，留下5条待办。原final-1794932352108701782.json与journal均保留，不能将自动finally标为全部通过。这是停止路径的清理缺口，本轮未修代码或据此重跑。

随后仅做授权清理：重新确认同一RPi4身份，保存root/governor，临时root on；对主机来源物核对原件/板上SHA及链接，对板上产生物新目录打包拉回并逐成员验证；只删除本实验确切目录，独立收据引用原final SHA。post-stop-cleanup/result.json：errors=[]、pending=[]、uid=5001、schedutil、RPM=1233。原5条待办通过独立journal核销，不改原失败证据；attempt-08旧2条也仅以独立核销收据闭合。

| 构建 | 退出 | 墙钟秒 | 等待秒 | 启动MemAvailable B | load1 | 启动可用磁盘B | cgroup peak B |
|---|---:|---:|---:|---:|---:|---:|---:|
| BASE | 0 | 153.342 | 0.066 | 15575924736 | 1.761 | 203843014656 | 1538895872 |
| AFDO | 0 | 127.453 | 0.064 | 17964785664 | 2.520 | 202999140352 | 1837764608 |
| BASE-r | 0 | 134.658 | 0.169 | 17946271744 | 2.525 | 204519030784 | 2133442560 |

三次构建均保持6G/5G/200%、-j2/threads1、nice19/ionice-c3；本实验取消16GiB启动门槛的授权仅用于此次，load/磁盘与运行中保护不变。high/max/oom/oom_kill均0，没有资源停止或重试。driver总墙钟2487.070秒（含S4中断恢复及检查；不含准备与停止后清理/归档）。采样最低MemAvailable **14664486912B（13.657GiB）**，构建最大memory.peak **2133442560B（1.987GiB）**，driver峰值576937984B，最低可用磁盘201037434880B。60秒资源原文在driver-resources及各execution目录；短测试/收尾scope未完整封存峰值，不宣称上述为全会话所有进程的绝对峰值。

边界：只操作.26，不操作.13或其他构建；不改v0.3/hq/Gerrit，不安装软件。板上文件仅/opt/afdo_agent，root/governor为明确授权状态操作，结束已恢复。系统服务元数据写入未做全机审计，不能证明WORKDIR外系统日志为零。另一工作线未提交STATUS与kernel文件原样保留，不纳入本任务提交。本轮按非正式检查停止条件结束，等待PM后续指令。


封存核对：19542项原件索引、916份小文件副本、5份transport分片；956个清单文件共27907313字节，全部<1MB，副本与来源SHA复核通过（export-validation.json）。提交前发现遗留空index.lock，复查无本仓库Git进程与可见持有者后移入attempt-09/stale-index.lock保留，见独立记录；没有删除其他工作线文件。

### 12.6 共享Git索引与同步补记（用户后续指令）

用户确认K0会话也在本仓库工作，并指定新的锁流程：按ps及/proc/PID/cwd检查WORKDIR内Git；有进程先等待；无进程且空锁mtime经间隔5分钟复查仍未变化才删除，随后git status；提交前先git pull --rebase。

如实区分时序：本轮此前空锁已在epoch1794932762移到temp/m1-ffmpeg-rpi4-thumb-01/attempt-09/stale-index.lock留证，当时没有执行后来指定的“5分钟间隔复查”，不声称符合该新增流程。此次复查epoch1794935212已无锁、无WORKDIR内Git进程，所以未再删除任何锁。此前dc59c88推送因远端前进被拒，原输出保留。

按授权pull --rebase取得K0提交1b096d2后，21个同名未跟踪文件阻挡checkout；逐字节比较全部等于远端，先移到本轮git-reconcile/kernel-autofdo-preserved留存，Git随后从远端恢复的21文件SHA全部相同。STATUS暂存于有名stash和本轮快照，仅解决相邻新增段冲突，保留K0远端记录与M1段。M1提交rebase为92ecc97b2d9b6d57ca7d3170a977e9ccd4a4b999，原代码/测试/证据内容不变。未提交的K0设计状态段恢复在工作区、不纳入本次提交；对应未跟踪设计文件及config/、gbs_gcc.conf、gbs_llvm.conf未读未改。保留stash与temp副本供并行会话核对。

本次只做Git同步与文档登记。真实温度停止条件仍有效，没有恢复M1负载或追加测量。检查、SHA对照、rebase与推送输出位于temp/m1-ffmpeg-rpi4-thumb-01/attempt-09/git-reconcile/。

## 13. 起跑冷却余量与独立清理权限（2026-11-17任务）

### 13.1 PM授权、实现及测试

PM授权修改不占自身缺陷次数，仍2/3。等待冷却目标由60°C改为58°C（T_start−2°C），仅更改board/start_gate.sh；等待上限600秒、30秒复查不变。stats.telemetry及设计v0.3原文未改：窗口起跑样本≤60°C、运行温度80°C判据保持原样。不得把58°C误写为新的统计判据。

SDB.restore_cleanup在删除前独立核对设备身份、记录当前root状态与所需权限；必要时先持久化恢复动作再临时root on，按journal清理后恢复。子流程已恢复root off不再使父流程依赖陈旧的root假设。每次清理保存cleanup-sessions记录。链接按readlink目标核验，不跟随链接计算SHA；普通文件核对主机原件与板上SHA，空或格式错误的sha256sum输出给出明确identity错误，消除split()[0]的IndexError。清理失败仍保留待办，不重复失败的状态修改。

180项测试通过（原171项保留，新增9项），15份板上/工作负载脚本bash --posix -n通过。新增夹具覆盖：58°C边界；59°C等待600秒超时；59/60°C仍为clean、60.374/80°C异常；attempt-09真实停止原文对应的root-off旧清理失败/新清理成功；链接不跟随；链接改变拒绝；空SHA显式拒绝；初始root on保持；root off失败不自动重试。旧证据不改。详见attempt-10/tests.log、validation.json、shell-validation.json和workflow/tests/test_cooling_cleanup.py。

逐模块SHA显示live.py、transport.py、start_gate.sh变化；现有收据DAG包含全部workflow模块，不能证明S0–S5输入未变，所以attempt-10从S0重做，不强行复用。复用决定和新旧30模块SHA在reuse-decision.json。新job固定ToS order_seed=2026111720、bootstrap_seed=2026111730，Sintel各+1；正式计划仍须新预试/CV/N/顺序表落盘。旧不完整block不合并。

### 13.2 降温能力实测

先核对RPi4：192.168.108.26:26101，Raspberry Pi 4 Model B Rev1.5、armv7l、6.12.80-arm-rpi4-v7l、tizen-unified-toolchain_20261104.160709，与既有身份相同。performance governor、既有风扇状态；未发现风扇转速或控制接口，物理风扇状态未知且未修改。每10秒记录一次所有thermal zone，两个探测分别建清理日志，在写入前登记，拉回tar及成员SHA验证后删除。初始与结束root off、schedutil、RPM1233，待办与错误为空。

| 曲线 | 样本/时长秒 | 初温 | 末温 | 最低/最高 | 首次≤58°C | ≤56°C |
|---|---|---:|---:|---|---:|---|
| 空闲 | 61 / 600.73 | 58.913°C | 57.939°C | 56.965 / 59.400°C | 10.02秒 | 10分钟未达到 |
| 一轮BASE负载后 | 61 / 600.77 | 61.348°C | 56.965°C | 56.478 / 61.348°C | 50.07秒 | 10分钟未达到 |

58°C冷却目标可达，未触发“空闲10分钟降不到58°C”的停止条件。负载使用attempt-09已验证的BASE运行文件、ToS输入、CPU3与正常perf/观察脚本；退出0，63份maps身份核验通过。这是独立降温诊断，既不作为正式block，也不计算性能比较。负载后曲线到600秒上限结束，不把未达到56°C写成通过。完整逐点曲线、源码脚本、时间/SHA与final在cooling-idle/、cooling-load/和curve-summary.json。

### 13.3 attempt-10阶段与测量结果

attempt-10的S0–S5均通过：BASE/BASE-r/AFDO退出0，BASE-r字节一致、选BASE，两套build-lock differences=[]；两目标AppliedSamples正数记录1985/56。锁定profile SHA `a7439a2f982099050d0f95f00b7d72517ab67836a260cf40680f412a02fa586c`。S4真实SIGTERM退出143，恢复后S3收据SHA不变；三训练后oracle与六次计时前oracle通过。独立计时中断清理通过。

进入非正式检查后发现临时实验ID仍用固定后缀，与attempt-09相同（虽然job路径、SHA、输出目录均为本次新建）。这不符合本轮要求的新临时ID。保留child job与原文后，只向本次非正式检查子进程发SIGTERM；父流程依原门禁退出2，未产生正式block。自动finally成功：父/子root off、schedutil，pending/errors均空，RPM1233。此次真实子流程先root off，父清理仍成功，覆盖了attempt-09的实际失败路径。

自身实现缺陷第3/3次：标识拼接遗漏attempt命名空间。修正为父实验名+用途+输出绝对路径SHA前16位，随新attempt/stage生成新ID，同一恢复路径保持确定性；加入旧固定后缀碰撞/新ID不同、用途与stage隔离夹具。旧live.py重建副本与运行锁SHA完全一致，保存于attempt-10/live-before-id-fix.py，不改原结果。此次不调整判据，也不把被中止的非正式数据计入验收。

由于live模块再次变化，attempt-11必须从S0开始，旧收据不强行复用。后续实际结果在本节补齐；M1尚未完成。

### 13.4 资源、清理、披露与边界

attempt-10已结束，driver墙钟2613.588秒；BASE/BASE-r/AFDO构建墙钟分别122.127/115.690/119.850秒（原值以execution/result.json为准），均退出0。driver及构建采样最低MemAvailable 21070471168B；构建峰值2151804928B；driver峰值694833152B。各构建保留启动内存/load/磁盘与等待记录，6G/5G/200%、-j2/threads1、nice/ionice不变，未触发资源终止。空闲与负载降温scope的memory.peak、原始meminfo独立保存在各resources.json。

收据与原件索引：attempt-10/run-index.json。attempt-10三份训练perf script、convert/001中断和convert/002六份成功profile仅用于本次转换/消费；按Q.5第17项保留路径、SHA与用途，未读既有正式质量评估profile，未做质量矩阵。板上仅本实验/授权afdo目录；root/governor为明确授权状态操作，已恢复。未操作.13、hq、Gerrit、设计或其他构建。系统服务的外部元数据写入未做全机审计；不声称其为零。短scope未完整封存峰值的限制仍保留。

唯一性修正后182项测试与15脚本语法通过。attempt-11新种子ToS order=2026111740、bootstrap=2026111750，Sintel各+1；准备证据在attempt-11/preparation/index.json。当前为运行前检查点，attempt-11尚未完成，后续追加实际验收结果。

### 13.5 attempt-11最终验收（单命令与恢复）

**M1自动化验收通过。** 运行前代码/测试检查点为 `c5d607ae6e8578d3fcb4525560713f784104a21d`。调用仍为 `PYTHONPATH=workflow python3 -m afdo_wf run --job temp/m1-ffmpeg-rpi4-thumb-01/attempt-11/job.json`，监督器只负责记录资源、S4预定SIGTERM与同命令恢复，不手动跳过阶段。最终八个成功收据均complete，恢复运行退出0；[S7 report.json](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-11/run/formal/stages/report/001/report.json)与[report.md](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-11/run/formal/stages/report/001/report.md)已生成，publishable=true，固定声明句存在：`profgen explicit conservative strategy; defaults not statistically validated`。报告SHA `49fca5d9c9993102400309b601806e9873ebda60f1a702aad30d22a3826300c9`。

[完整验收汇总](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-11/run/acceptance-summary.json)、[最终核验](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-11/run/final-verification.json)、[原件与分片SHA索引](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-11/run-index.json)。S4第一次退出143是预定测试，convert.failure.json保留；恢复后S0–S3收据时间早于中断，S3收据SHA未变，阶段目录没有重做，S4从新转换目录继续。30个运行模块的启动锁、中途与最终SHA均相同。未将attempt-10中止数据混入本次。

| v0.3 §14 M1验收项 | 结论 | 本轮证据（run/formal/下） |
|---|---|---|
| S0身份、cycles、输入与遥测能力 | 通过，唯一目标192.168.108.26:26101 | receipts/preflight.json；stages/preflight/001 |
| 单命令S0–S7、S3后恢复 | 通过，首次143、同命令恢复0 | run-end-*.json；../recovery-interruption.json；../driver-end.json |
| build-lock三项 | BASE-r与AFDO均passed，differences=[] | receipts/rebuild.json，details.buildlock |
| 冻结依赖与BASE-r离线复现 | 108RPM按锁核验，BASE-r逐字节相同，选BASE | receipts/build.json、receipts/rebuild.json |
| 三输入PLAT/BASE oracle | S2六项、训练后三项均通过 | stages/deploy/001/*oracle.json；stages/collect/001/*oracle.json |
| 每个计时进程must-load/deploy-set | 90轮检查通过（20预试+8预热+62接受正式round）；训练3轮另计 | stages/measure/001/*/maps/decoder-check.json |
| 两目标消费证据 | libavcodec 1959、libavutil 70条正数AppliedSamples；profile SHA及代码差异门禁通过 | receipts/rebuild.json，details.consumption |
| 预登记与统计 | ToS N=21、Sintel N=10，计划SHA与实际顺序一致，均先锁定后启动正式命令 | *-plan.json、*-plan-lock.json、*-blocks.json；../final-verification.json |
| 独立计时中断清理 | 通过；独立ID…cleanup-test-0617acf9747deff5 | injected-job/injection-active.json、final-*.json、injection-job.json |
| 非正式三轮clean门禁 | 3/3 clean，新ID…telemetry-check-7ed19f5d104f8f0f | telemetry-check-job/check-rows.json、check-result.json、final-*.json |
| 计时前后正确性 | 前6项、后6项均通过，BBB/ToS/Sintel的BASE/AFDO与PLAT一致 | stages/measure/001/*oracle.json；S7 oracle.records |
| 最终清理与S7 | root off、schedutil、RPM1233，pending/errors=[]；服务inactive/dead、MainPID0 | final-1794954789955930539.json；../final-verification.json |

本轮没有新的workflow缺陷修正，仍累计3/3（第3次是13.3所述临时ID修正）。封存汇总脚本的两次元数据读取错误（把预定failure收据纳入成功断言、把ISO时间当数值）仅修正汇总读取，原诊断日志保留；没有重跑实验、改运行模块、判据或数据。

### 13.6 三轮非正式检查与两个比较

新的非正式实验三轮check-0/1/2全部clean，anomalies=[]、missing=[]；两侧遥测窗口均覆盖，固件历史标志仍unknown。子流程结束先恢复root off后，父流程继续并最终正常清理，验证了独立清理权限修复的实际路径。

| 比较 | 预试CV / N | 估计相对墙钟变化 | block bootstrap 95% CI | 判定 | 标记BASE/AFDO | 失衡门槛/差值 | 技术重试 |
|---|---|---|---|---|---|---|---|
| ToS（主） | 0.6466% / 21 | -1.917156% | [-2.348800%, -1.449261%] | faster | 0/0 | 3/0 | 0 |
| Sintel（次） | 0.3692% / 10 | -1.489203% | [-1.862452%, -1.189055%] | faster | 0/0 | 2/0 | 1（第5 block成功） |

统计为配对log比的均值经expm1变换；20,000次block bootstrap，ε=1%，没有多重比较校正。ToS顺序/统计种子2026111740/2026111750，Sintel2026111741/2026111751；两者各10轮新预试、每变体2轮预热。全部接受block为clean，敏感性结果与主结果完全相同；无缺失，未触发20%或失衡封顶。ToS的t区间[-2.406465%, -1.425394%]，Sintel[-1.906856%, -1.069771%]；中位数之比分别-2.250565%、-1.257685%。正式BASE CV分别0.538660%、0.670397%。

有效频率中位数：ToS BASE/AFDO 1499.820075/1499.823882 MHz（相对差0.000254%）；Sintel 1499.842870/1499.846037 MHz（0.000211%），均未触发0.5%混杂提示。所有接受正式round的窗口起跑最高59.400°C、全窗口最高65.244°C；观察器最大间隔0.90秒。逐轮墙钟、perf、温度与身份索引见[accepted-rounds.csv](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-11/run/accepted-rounds.csv)，完整遥测、冷却等待、maps及SHA见分片索引。

Sintel第5 block第一次尝试在删除已拉回的临时传输目录时，SDB主机退出0，但stdout仅换行、无可信退出标记，故按既定TechnicalFailure处理。原命令transport-1794941651997488288/002011.json和stdout/stderr、失败收据与原始try0目录保留；已verified-pull的目录不挪动，failure.archived={}、partial={}，不等于没有原件。整block唯一重试（try1）两侧完成并接受；没有挑选旧侧数据或因温度替换轮次。[定位证据](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-11/run/technical-retry-evidence.json)。这是设计允许的技术重试，不是新增实现修补。

### 13.7 转换、消费与披露

锁定profile SHA `bab0130ccf4b72952092cfbdcd0c19b820bb2e85cb7843d9ecff667225be8485`。六次成功转换全部conversion=ok、identity=verified，跨DSO顶层键冲突为空。质量报告门槛仍按显式配置（未设置的检查not_evaluated，sampling_adequacy=unknown）；不能把转换成功当作统计质量等价验证。

| RUN / DSO | 目标样本 | usable | outside_dwarf_func | in_func_no_line | 其中nonleaf_line_zero |
|---|---:|---:|---:|---:|---:|
| 1 / libavcodec | 40970 | 24519 | 12204 | 4247 | 18 |
| 1 / libavutil | 142 | 110 | 21 | 11 | 0 |
| 2 / libavcodec | 40628 | 24243 | 12108 | 4277 | 23 |
| 2 / libavutil | 127 | 97 | 16 | 14 | 0 |
| 3 / libavcodec | 40724 | 24186 | 12411 | 4127 | 40 |
| 3 / libavutil | 111 | 87 | 10 | 14 | 0 |

按Q.5第17项登记：对象为本实验FFmpeg Thumb BASE的libavcodec/libavutil；时间为driver及convert收据中的UTC时间；打开本轮三份训练perf script/buildid-list、convert/001预定中断产物、convert/002六份profile及按DSO合并/锁定profile，用途仅为转换诊断、冲突检查和AFDO消费构建。路径、SHA、命令见run索引及receipts/convert.json。没有打开既有正式质量评估profile，没有计算质量矩阵或登记修正案3。本轮性能数据用于workflow端到端A/B，不能外推profgen默认值的统计有效性。

### 13.8 资源、结束状态与限制

attempt-11包含真实中断/恢复的driver墙钟 **14821.311秒**，三次GBS合计 **351.595秒**。构建均-j2/threads1、6G/5G/200%、nice19/IO idle；启动内存豁免仅本实验，load<12与磁盘≥50GiB仍检查，运行中保护不变。

| 构建 | 启动MemAvailable B | load1 | 磁盘可用 B | 等待秒 | 构建秒 / 退出码 | cgroup peak B |
|---|---:|---:|---:|---:|---|---:|
| BASE | 21726224384 | 0.542969 | 187353600000 | 0.066135 | 115.583 / 0 | 1814970368 |
| BASE-r | 21630504960 | 0.907715 | 185690320896 | 0.103940 | 117.486 / 0 | 1816170496 |
| AFDO | 21614669824 | 1.836426 | 184173445120 | 0.065763 | 118.526 / 0 | 1833254912 |

正式attempt采样最低MemAvailable **21333422080B（19.868GiB）**，最低磁盘179936792576B；包括前置空闲降温诊断的本轮已记录最低MemAvailable为 **16,296,251,392B（15.177GiB）**。构建峰值1833254912B，所有构建high/max/oom/oom_kill均0，无资源性停止或重试。

监督服务3G/200%实际memory.peak **3232858112B（3.010834GiB）**，原配置MemoryMax=3221225472B未提高；内核实读峰值略高于配置值，原值如实保留。memory.events最终max=9868、high=0、oom=0、oom_kill=0。近结束memory.stat快照为anon62,758,912B、file2,106,232,832B、kernel617,361,408B；这是cgroup总记账，不能称为进程峰值RSS。没有OOM或因此终止。[资源快照](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-11/run/cgroup-near-final.json)、driver-resources.json及三套execution/resource记录保存原始meminfo。driver共248次采样，按60秒轮询，实测最大间隔61.404秒（存在调度延迟），不伪称严格每60.000秒。短探测scope未逐一保存峰值的历史限制仍保留。

最终root off（uid5001）、policy0=schedutil、RPM1233；主/两个独立临时实验final均pending/errors为空；本实验部署物及work按主机来源SHA或verified-pull清理，通用工具与已授权输入保留。服务inactive/dead、MainPID0，ALL-END明确已结束。提交前锁检查无Git进程、无index.lock，没有删锁；Git同步与推送记录见本节收尾。

限制与边界：仅RPi4 Thumb、单线程、两个特定视频；ToS曾用于工具开发，不是全新holdout；Sintel按指定从1920×818拉伸到1920×1080，只用于解码正确性/性能；固件历史降频不可读；物理风扇状态未知且未改变。未操作.13、hq、Gerrit、设计或其他构建；板上文件仅/opt/afdo_agent。root/governor操作是明确授权的状态例外；系统服务元数据等WORKDIR外写入未做全机审计，不声称为零。工具、RPM、视频、perf/profile及大型原件留temp并登记SHA，小文件分片入库。完成后停止，不进入下一里程碑。


封存执行偏差：主流程结束后，曾在前一个导出scope仍返回running时启动第二个本任务导出scope，违反串行约束一次。没有板上测量或GBS并发，没有调整其他进程；交叠精确时长与合计峰值未采样，未知，不声称本轮全程串行。之后确认两者结束，串行完成SHA验证：377,628个原件索引、4,196个小文件副本、68个transport分片，4,901个manifest文件校验与复制源SHA均0差异，新增文件均<1MB。该偏差与S7前已完成的实验数据分开登记，不能隐去。[偏差及Git收尾证据](../runs/m1-ffmpeg-rpi4-thumb-01/attempt-11/finalization/index.json)。

提交前按共享仓库规则检查ps/cwd与index.lock：无活动Git进程、锁不存在，未删除任何锁。只暂存两个tracked文档到具名stash以执行git pull --rebase，结果Already up to date，随后原样恢复，保留stash作为备份。其他会话的K0 STATUS节与未跟踪设计文件保持未提交；config/、gbs_gcc.conf、gbs_llvm.conf不读不动。只提交本轮报告、STATUS的M1增量与本轮证据，不改hq/Gerrit。推送输出与最终commit在本次回复给出。
