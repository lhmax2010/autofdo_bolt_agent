# M1 手动试跑独立核查（2026-11-16）

## 1. 总体结论与范围

**一致：main `596d978` 的报告第8节所给本次 RPi4 Thumb / ToS60 pilot 判定 `faster`、点估计 −2.565%、bootstrap 95% CI [−2.859%, −2.256%]，由保存的证据支持。** 未发现改变该判定的数值、构建身份或profile重放差异。该结论不外推为通用FFmpeg性能收益、完整正确性或“未发生降频”。

核查对象：[原报告第8节](02_manual_pilot_rpi4_thumb.md#8-按-v02-专项指令执行的端到端试跑2026-11-16)，[证据索引](evidence/08/index.json)、[SHA清单](evidence/08/sha256.json)。本轮仅新增此报告并更新STATUS；不接板、不构建、不执行原统计脚本、不改原报告/evidence/08/设计/hq，不推Gerrit。已有未跟踪的v0.2评审文件与本地配置未处理。

独立Python标准库脚本及复核输出保留于 `temp/m1-independent-check-20261116/`，文末登记SHA。按用户授权读取三份本次训练导出、六份单DSO profile、两份DSO合并profile与锁定profile，用途仅为可复现性和交集核查；新生成结果写入该目录的`replay/`，没有覆盖原件、运行质量矩阵或登记修正案3。

## 2. 证据完整性

**一致。** 按路径逐项重算，不以Git对象存在或原来的`verified=true`代替：

| 清单 | 核对次数 | 不一致 | 缺失 |
|---|---:|---:|---:|
| evidence/08/sha256.json | 876 | 0 | 0 |
| index.json 的source原件 | 874 | 0 | 0 |
| index.json 的evidence副本（含gzip本体） | 874 | 0 | 0 |
| retained-raw-artifacts.json | 4 | 0 | 0 |
| 合计（含交叉清单重复核对） | 2628 | 0 | 0 |

去重后1754个路径。包含temp中的原始文本、三份perf.data及最终work归档；原始/压缩副本分别按各自声明的SHA核对。大文件索引中的最大原件为16,629,760字节work tar。另单独核验了工具/加载器/libLLVM、chroot profile及目标ELF（第4–5节）。这证明当前保存内容与声明一致，不把未签名清单解释为独立第三方时间戳或现场真实性证明。

## 3. 统计与顺序独立复算

### 3.1 原始轮次

**一致。** 从rounds.json及blocks.json选择15个完整正式block的attempt1；逐轮再从wall.txt和perf-stat.csv读取原值。包括4个预热在内，34轮的墙钟及三个perf事件值均与rounds一致；预热未进入统计。下表与原报告逐行一致：

| block | 顺序（A=BASE，B=AFDO） | BASE秒 | AFDO秒 | 标记 |
|---|---|---:|---:|---|
| 1 | BA | 30.839 | 30.332 | 无 |
| 2 | BA | 30.997 | 30.200 | 无 |
| 3 | BA | 30.884 | 30.021 | 无 |
| 4 | AB | 30.755 | 30.060 | 无 |
| 5 | AB | 31.057 | 29.978 | 无 |
| 6 | AB | 30.787 | 29.922 | 无 |
| 7 | AB | 30.728 | 29.944 | 无 |
| 8 | AB | 30.740 | 30.199 | 无 |
| 9 | BA | 30.950 | 30.002 | 无 |
| 10 | BA | 30.715 | 29.882 | 无 |
| 11 | AB | 30.753 | 30.005 | telemetry_unknown |
| 12 | AB | 31.009 | 29.934 | 无 |
| 13 | BA | 30.861 | 30.090 | 无 |
| 14 | BA | 30.947 | 30.001 | telemetry_unknown |
| 15 | AB | 30.894 | 30.475 | 无 |

### 3.2 区间与判定

**一致；实现差异已量化并解释。** 独立实现`r_i=ln(AFDO/BASE)`、配对block重采样、百分位插值；不调用或导入原statistics_pilot.py。t临界值以Student-t密度数值积分与二分求解（df14/12分别2.144786687918、2.178812829667），不沿用原脚本的临界值表。

| 项目 | 15个正式block | 13个干净block |
|---|---:|---:|
| exp(mean r)−1 | -2.565157872% | -2.537450726% |
| 中位数之比−1 | -2.773727358% | -2.721881987% |
| BASE CV | 0.365635424% | 0.373152549% |
| 独立randrange重采样95% CI | [-2.860164377%, -2.254251504%] | [-2.865494169%, -2.194043553%] |
| 匹配浮点随机数索引法95% CI | [-2.859136595%, -2.256299179%] | [-2.867768694%, -2.193959062%] |
| 独立t区间 | [-2.906041866%, -2.223077078%] | [-2.928897340%, -2.144425575%] |
| 判定 | faster | faster |

两套bootstrap都固定seed=2026111601、重复20,000次。本核查首次用`randrange`的整数随机抽样，与原脚本`Random.choices`所用浮点随机抽样消耗不同的随机序列；主CI端点差为−0.0010278 / +0.0020477个百分点，干净CI端点差为+0.0022745 / −0.0000845个百分点。随后独立用`int(random()*n)`选择索引、对log均值做百分位后expm1变换，复现原CI：主下界仅3.47e−18的浮点差，其余端点相同。不是更换数据、种子或阈值，未执行原统计脚本。

t区间与原值的最大绝对差约6.02e−13（比例单位，来自原临界值舍入）。点估计、中位数比、CV一致。2/15标记、0缺失，未超过设计20%限制；主分析保留两项标记，敏感性分析剔除11/14。两套区间上界均小于−1%，支持faster，而非inconclusive或equivalent。

### 3.3 顺序与计划时间

**一致。** 按已保存执行器声明的固定8个AB、7个BA和seed=20261116独立shuffle，结果为：

`BA BA BA AB AB AB AB AB BA BA AB AB BA BA AB`

它与plan、rounds顺序、measurement/operations.json.gz中30次正式调用顺序完全一致。计划记录时间01:22:37.694129−08:00，plan-receipt时间01:22:37.735955−08:00，首个正式调用01:25:39.871448−08:00；读取common.py确认该时间在subprocess启动前取得。receipt的计划SHA与实际文件相同：`12e2beb604f80a89279fbd79d3218800d387b6c3d7463dcee6389e2b07498aba`。保存代码的写入路径确实flush/fsync后才进入轮次。首轮perf原文标为板上18:25:57；不将板上时钟与主机时间无校准地相减。结论是现有同一主机时间线支持“先写计划再计时”，不是对历史时钟作外部认证。

### 3.4 有效频率

**一致。** 从每轮perf stat原文读取cycles和task-clock（msec），计算`cycles / task_clock_ms / 1000` MHz，先逐轮计算再分别取中位数：BASE **1499.803937521 MHz**，AFDO **1499.800640536 MHz**；相对差 **−0.000219827720%**。全部原始事件值匹配rounds.json，低于0.5%混杂风险阈值。该指标不能替代未取得的固件历史节流状态。

## 4. 构建锁与消费

**一致。** 独立从原BASE未排序rpm-qa清单与四个root的rpm-lock读取、排序并按行/重数比较：五份各108行，额外/缺失均0，包含SHA256HEADER。没有重新进入chroot执行rpm命令，也没有构建。

两份forensic build.log.gz去掉日志时间前缀，以实际以clang开头的命令为取证对象，用标准库shlex解析argv。每侧698条；只删除`-fprofile-sample-use=…` token后按Counter比较，双向差异0。独立保存完整解析argv；不引用原compile-link-commands作为比较输入。AFDO其中627条带profile-use，BASE-r为0；另见strip命令不属于编译/链接argv计数。

主AFDO与取证AFDO两个chroot中的Source profile均重新哈希为锁定值`61f03b59262e3ce7ce758219d65848a33b5a0549131c362a6769ad10386f2cf2`。实际打开保留的runtime/debug ELF，以readelf重读build-id，以Python解析ELF32 section table直接哈希.text；不调用原产物检查器。两目标runtime/debug ID成对一致：

| 目标 | BASE-r（等于原BASE） | AFDO |
|---|---|---|
| libavcodec | 805376f248504d2084e3e95470810873ffc3655a | 5aef89343bc6a870b6760c3d492206bbb8adc286 |
| libavutil | bb5b41f743b9b07bb38cc5007f7deb6516256579 | 1908c55105184d14beeb1e7076816dd1c994658c |

| 目标 | BASE-r .text SHA-256 | AFDO .text SHA-256 |
|---|---|---|
| libavcodec.so.62.11.100 | `b5ddb93cc6b951d228b1bcb694ec98be3ba805816484c087315e9555cd44c681` | `d92ab268f16662bedadc73d9a253126691ae8f2d0a7b9e209a22c1bd65c9293a` |
| libavutil.so.60.8.100 | `5201e0508548f6640e0785bf4e450028f7bca107e7ee297feb7a7a6a2c7f38d4` | `43e78cefa601b061091254ea85b1f3c7649d7f6bd10d97d2ef6473ce1c0fda6c` |

两目标.text都改变；全部六库/SONAME的SHA、两目标debug SHA均匹配记录，取证产物与对应主构建产物相同，BASE-r与原BASE清单相同。这些证据支持“确实消费profile且代码改变”，不能单独证明所有函数均充分匹配。

## 5. profile可复现性

**一致。** 启动前重新哈希发布工具：llvm-profgen为`67ad21faba787d276a80673c1f324f7c0591d28d76bd37a8bd57de0d86426be6`，llvm-profdata为`1700cc8924ba608c773a73b7550025189e5e2af3a994ef58ddc6009933d0977e`，加载器与libLLVM也与tool-identities匹配。

以conversion/operations.json保存的完整argv为依据，仅把输出目录换到本轮replay；所有binary、debug-binary、perfscript、buildid-list、完整regex及cycles/period/1000003/max/none/none/none/extbinary参数不变。依次运行六次转换（串行），均退出0、conversion=ok、identity=verified；stderr也与原记录逐字相同。

| 比较对象 | 结果 |
|---|---|
| 六份单RUN extbinary | 6/6逐字节相同 |
| 六份quality JSON | 仅各自tool.arguments[15]与[16]的output/quality-report路径改变；恢复原路径后6/6逐字节相同 |
| 两份DSO合并extbinary | 2/2逐字节相同 |
| 两份DSO text | 2/2逐字节相同 |
| 锁定package extbinary | 逐字节相同，SHA如下 |

`61f03b59262e3ce7ce758219d65848a33b5a0549131c362a6769ad10386f2cf2`

严格按原顺序：codec RUN1/2/3合并；util RUN1/2/3合并；codec、util两份合并为package。独立解析重新生成的text顶层函数键：codec119个、util44个，交集为空。没有把内联叶名扁平化为顶层键；本项验证的是用户要求的顶层冲突结论。

## 6. 正确性、运行身份、遥测及恢复

### 6.1 Oracle

**一致。** 从原始gst.log重新数framecounter的chain通知，同时核对独立frame-notifications.count、decoded.bytes、decoded.sha256和filesink caps。初始PLAT/BASE × 两片、计时前AFDO × 两片、计时后PLAT/BASE/AFDO × 两片共12次，全部通过：

| 项目 | BBB60 | ToS60 |
|---|---|---|
| 帧数 | 1800 | 1800 |
| 字节数 | 2488320000 | 2488320000 |
| 输出SHA-256 | 3a4c3820c576697edd4ca34f3532c8af8ffaf04687955c5d6b35215b9b06c814 | 4c2610c37b7790240c9158277981ed9c3ac81399e3e9df554ffebb2d2ff80c4e |

caps均为I420、1280×720、30/1、progressive、PAR1/1、chroma-site mpeg2。字节数等于1800×1280×720×3/2。此处验证保存的oracle输出记录一致；原始I420帧未保存，不能在本次只读主机核查中重新对帧字节流计算SHA或重新解码。

### 6.2 Maps与遥测

**一致。** 超过要求的至少5轮：全量核对30个正式计时轮。取gst.pid对应的maps/*.loaded原文，两目标路径都来自对应m1p-base/m1p-afdo/lib，未见误用系统库或另一变体；每轮runtime.sha256与该变体清单匹配。build-id通过“实际文件SHA一致＋保留ELF重读build-id”关联，maps本身不含build-id，不声称直接从maps读出ID。

所有完整频率读数为1500000 kHz、完整欠压值为0；开始温度57.452–59.887°C，最高63.296°C；含起止端点的最大间隔1.10秒。代表性10轮如下（全部maps/SHA匹配）：

| block/变体 | 最高温°C | 最大间隔秒 | 独立标记 |
|---|---:|---:|---|
| block-01-attempt-1-afdo | 63.296 | 1.06 | 无 |
| block-01-attempt-1-base | 62.322 | 1.09 | 无 |
| block-05-attempt-1-base | 62.809 | 1.09 | 无 |
| block-05-attempt-1-afdo | 62.809 | 1.07 | 无 |
| block-11-attempt-1-base | 61.835 | 1.08 | 无 |
| block-11-attempt-1-afdo | 62.322 | 1.06 | telemetry_unknown |
| block-14-attempt-1-afdo | 62.322 | 1.07 | telemetry_unknown |
| block-14-attempt-1-base | 62.322 | 1.06 | 无 |
| block-15-attempt-1-base | 62.809 | 1.06 | 无 |
| block-15-attempt-1-afdo | 63.296 | 1.10 | 无 |

第11 AFDO末行缺cpuinfo_cur_freq数值及后续字段；第14 AFDO末行缺in0_lcrit_alarm值。独立检测恰好得到这两个telemetry_unknown，与保存标记和汇总一致；不把完整读数正常解释成缺失部分也正常。其余28轮无新异常标记。固件历史欠压/节流不可观测仍为记录限制。

### 6.3 最终状态

**一致（历史证据，不是本轮现场查询）。** cleanup/result与cleanup/operations原始输出共同支持：uid5001、policy0=schedutil、RPM1233、cleanup_pending=[]，work_removed=true；末次保存操作时间约01:55:31−08:00。保留variants的SHA也可与清单对应。本轮没有连接板子，不能据此断言当前板上状态仍未变化。

## 7. 不一致、无法核查与解释边界

- **不一致：没有发现影响结论的项目。** 首次独立bootstrap数值略有差异，来自PRNG取样接口；改用相同的随机数到索引映射后精确复现，详见3.2，不是证据冲突。
- **无法核查：早期部分SDB逐条stdout。** 原报告已披露operations覆盖；现有材料不能恢复那些被覆盖的原文。本轮没有以脚本意图代替全部历史操作成功证明。
- **无法核查：完整固件历史降频/欠压状态。** 完整遥测正常、有效频率接近1.5GHz，不等于证明从未降频；两条截断遥测已正确保留标记。
- **无法核查：取证构建结束瞬间cgroup峰值及未保留的I420原帧。** 前者原报告已披露，后者只能核对保存的SHA/计数/caps输出，不能重哈希不存在的帧流。
- 计划与调用的先后有同一主机记录及代码顺序支撑，但未签名的本地记录没有外部可信时间戳；不能独立认证当时所有现场事实。
- 结论仅限本板、本构建、ToS60、CPU3单线程与保存的15block；不验证通用收益、采样充分性或全部FFmpeg正确性。本轮未扩展实验、阈值或资格。

## 8. 复核可追溯性与资源

所有主机执行均以nice19/ionice-c3、串行systemd用户scope 3G/200%运行；没有构建、安装或板上命令。哈希和转换入口检查MemAvailable≥4GiB，阶段结束保存meminfo。已实读scope峰值见资源文件（短辅助读取scope未逐个保存峰值，不声称全轮峰值完整）。

仅这份报告与STATUS提交；独立脚本、逐项核对JSON及重放输出留temp。复核入口命令为：

```bash
export TMPDIR="$PWD/temp/tmp"
nice -n 19 ionice -c3 systemd-run --user --scope \
  -p MemoryMax=3G -p CPUQuota=200% \
  python3 temp/m1-independent-check-20261116/check.py
# replay.py、build_check.py、board_evidence_check.py 同样串行包装；
# replay.py 拒绝覆盖已存在的输出目录，重用时须另设新输出目录。
```

本轮原始复核产物清单`temp/m1-independent-check-20261116/manifest.json`记录各脚本与结果SHA。关键文件如下：

| 主机保留文件（均在上述目录） | SHA-256 |
|---|---|
| check.py | `3f59df65ab3dd384bb616887d83fdf82e313795e4d06b9c00f1d68718fa33f7b` |
| replay.py | `791ca472f29101c81aa8dd905a0ab241a58b2f1da9b3c88617c4896edd3d54cd` |
| build_check.py | `670118b3228e9b8834b111c29f43c8e31352ac5fbbd95b69fcb752652a2634d0` |
| board_evidence_check.py | `a28126a7226aa2a744e79c0abfec4f57bdf696d35f999dc319328b7637d5c0c3` |
| hashes.json | `f9b955acd29225551b3e4e15fd64262e17c1b87a58b0cad1d7afc4650d9c03e6` |
| statistics-independent.json | `c0d98a14658d823bc2e3f18af9787fa35655fd412c6b5769b609b70d125bcb73` |
| bootstrap-compatible.json | `34a191466dfb6f821e2251b551f83601e67e55a55a85b29644c7c9cfdd659907` |
| build-check.json | `fbdf106a0c51e73bbe2be8643d833e056aa91d85ae8c9d03c107af7beb457504` |
| replay-check.json | `92748c36d81980473666e8e25ed539e0b09d0fc2070bfafd97a45e7de1ea9461` |
| maps-telemetry.json | `902ca14e2087e56ce709ee7127e0e8ed07b2337b97e6e132a992d19c3a54da5a` |
| oracles-independent.json | `4d0188b8101e68381d8382dc6d05b4cfd5e1e1cafc97b04cff006f99e8502c42` |
| plan-time-order.json | `28366fabf572185403fef1fb89be1294e202f390a974c4b6273827086e8bbaa4` |
| cleanup-independent.json | `4b016e6e133caf941826cf7e268f1d6921ff674ba9d4b0ffacb721a90d29433d` |

已保存采样的最低MemAvailable为 **16,202,887,168字节**；已记录scope最高memory.peak为 **86,847,488字节**。未触发资源暂停或终止。本轮profile接触时间见replay-operations.json及profile-disclosure.json，仅限上述复现用途，未来Q.5第17项汇总时须保留此项。
