# llvm-profgen补丁3修正与补丁4：IP加载与计数生成

2026-11-02。补丁3已独立验收并amend，补丁4已完成本地提交、GBS增量构建、lit、C1、独立GNU核对和历史完整导出重放。未连接开发板、未推送LLVM远端或Gerrit、未开始Agent开发。

- 补丁3：旧 `30ceb73e9dcbe233f747d1ed8c97d9e3919564b0` → 新 `399a72494db096f27e5c06f7464a5815a659f5fa`。
- 补丁4：`de8171b77cec5e547c8ffc2f7a5039a8b39b8577`，33文件、+1,045/-198行，新增7个lit文件。工作树 `temp/llvm-profgen-enh`，分支 `afdo/profgen-enhance`。
- 最终工具SHA-256：`82af1d6a442bcb3771609c0fbdfe05570471321276042b3c8d22ec09c7953ac0`。
- [补丁3](../../../patches/profgen/0003-llvm-profgen-Add-build-id-identity-checks-for-IP-sample-mode.patch)、[补丁4](../../../patches/profgen/0004-llvm-profgen-Generate-line-level-profiles-from-IP-sa.patch)、[提交范围与反向应用审计](evidence/06/17_commit_audit.json)。两个LLVM提交只含工具/测试目录；spec未进入提交，其本地diff与02证据逐字节一致，**正式非增量构建前必须撤销**。

## 补丁3的小修与独立验收

`IPIdentity.cpp`中只有候选路径的list ID冲突才mismatch；无关路径冲突只输出 `unrelated buildid-list conflict`。新增两条RUN分别检查无关冲突保留verified-path、候选冲突仍失败。修正IPIdentity.cpp单行文件头，并检查补丁2/3新增C++文件头。

补丁3独立GBS成功后才开始补丁4：lit 61 PASS、0 FAIL、1 UNSUPPORTED、1 XFAIL，原50逐项不变；C1每遍636条，两遍一致、与既有基线0差异。[修改diff](evidence/06/02_patch3_fix.diff)、[文件头](evidence/06/01_headers.txt)、[独立lit](evidence/06/05_patch3_lit_summary.json)、[独立C1](evidence/06/06_patch3_c1_summary.json)。

## 实现概要与共享路径隔离

以下代码路径以 LLVM 本地补丁4提交为准，前缀 `llvm/tools/llvm-profgen/` 简写为 `T/`。没有修改 LLVM 库、spec、既有50项测试或冻结设计正文。

- `T/llvm-profgen.cpp:126` 定义六个选项，`:150` 的IP入口验证值和门控；`avg`、`sampled-functions`、`prev-inst` 固定拒绝，aggregation在评估期间必须显式选择。未开IP时使用新选项由main拒绝。
- `T/llvm-profgen.cpp:226` 先完成IP读取及身份链，再在`:256`构造 `ProfiledBinary(..., true)`。P_ref在构造前确定。
- `T/ProfiledBinary.cpp:185` 的构造器新增默认false的IPMode；只有IP跳过prolog/epilog推断。`:271`独立加载分支读架构、节、符号和DWARF后直接返回，跳过preferred base、全量反汇编、CodeAddressVec和probe解码。LBR仍走原分支。
- `T/ProfiledBinary.cpp:228` 在运行文件与显式调试文件符号表按名称检测FS标记，不检查符号所在节的类型，允许调试文件的NOBITS；`:985`仅IP收集CU区间用于细分；`:1027`仅IP取消原preferred-base下限；符号化转换在IP时将无帧/叶子原始行号0返回为空链。没有独立拷贝符号化转换器。
- `T/ProfileGenerator.cpp:247` 新增 `populateBodySamplesFromAddresses`，复用内联树构造，但传0避免旧接口提前计数；独立的整数分子表分别保存total和body，最后取整。共享树创建和 `postProcessProfiles` 本身没有修改。
- `T/ProfileGenerator.cpp:358` 新建IP专用安全writer；LBR原来的write不改。隐藏诊断追加确定性的 `IP-GENERATION` 行，旧地址计数及身份输出保留。

## 设计、代码、测试对照

| 条文 | 实现位置 | 测试与判据 |
|---|---|---|
| 5.4.1 权重、较小中位数 | `T/IPPerfReader.cpp:329`，`T/llvm-profgen.cpp:250` | `ip-counting-arithmetic.test`：偶数中位数20、显式10、固定period/sample一致、sample忽略正periodunit；段外目标样本仍参与中位数 |
| 5.4.2 归类 | `T/ProfileGenerator.cpp:264`，`T/ProfiledBinary.cpp:247` | `ip-counting-classification.test`：三个outside子类各1、无行1、usable0失败；真实libavcodec全部outside，细分no_cu与plt |
| 5.4.3 完整内联键 | `T/ProfileGenerator.cpp:282`、`:850` | `ip-counting-inline.test`：不同调用点、多层嵌套；GNU独立核对完整链和base discriminator |
| 5.4.4 sum/max/精确整数/取整/告警 | `T/ProfileGenerator.cpp:199`、`:207`、`:295`、`:316` | `ip-counting.test`、`ip-counting-arithmetic.test`：三种ISA、2^53以上、乘法边界、半入、最小1、超UINT32告警 |
| 5.4.5 total每层一次 | `T/ProfileGenerator.cpp:290`、`:311` | 三层total分别30/10/20；sum/max总数相同32，不按指令长度计算 |
| 5.4.6 head | `T/ProfileGenerator.cpp:215`、`:330` | `ip-counting-inline.test`：none、最早inline、顶层无body、同一调用点两个inlinee；零估计兜底按用户授权延期 |
| 5.4.9 不产生间接调用目标 | `T/ProfileGenerator.cpp:247` | 新路径只写body、total、顶层head；独立文本解析拒绝多余target项，完整profile树一致 |
| 5.3.4 分离debug与FS | `T/ProfiledBinary.cpp:228`、`:271` | `ip-counting-split.test`：a64-pie、thumb-count、a64-fs，三种格式拆分前后逐字节一致，FS诊断相同 |
| 5.6.3 基本安全写出 | `T/ProfileGenerator.cpp:358` | `ip-counting-writer.test`：gcc/open/rename失败不覆盖旧文件、无临时残留；MD5；`ip-counting-classification.test`：usable0和裁剪后空失败 |
| 5.10 max参考对照 | 旧LBR路径未改 | `ip-counting.test`：A64/A32同地址[ip,ip]区间，正body24一致；LBR total128另用独立golden，不要求与IP total32相同 |
| 5.11 C1/C2 | main/IPMode门控 | 原50项lit逐项比对、636条C1每遍逐字节；提交只包含工具/测试目录 |

新增7个lit文件；旧13个IP测试的成功解析用例改为显式sum、gcc写出失败或no-usable失败，以保持原有地址/身份断言和失败不落盘断言。原LBR测试与基线清单没有改动。

## Golden值及素材

| 用例 | 手算 |
|---|---|
| 展开循环（三种ISA） | N=8、d=4，每份两条指令代价1/3；8个地址的u=(2,6)×4。sum=8×(1+3)=32；max=max(2,6)×4=24；total=Σu=32。叶子行偏移12−9=3，raw discriminator1028解码base2、duplication4 |
| LBR参考 | 同样的8个[ip,ip]范围、权重2/6；正body为24；旧total按4字节指令计数为Σu×4=128；零位置、total与head不当作IP golden |
| 分数聚合 | 两个地址各3，P_ref=10，先和6再半入得到1，不逐地址取整为2 |
| 半入与大整数 | 5/10→1；9007199254740993/2→4503599627370497，避免double丢精度 |
| 极小正值 | 1/18446744073709551615→最小1 |
| 中位数 | periods10/20/30/40，较小中位数20，总100→5；显式10→10 |
| 中位数筛选位置 | 一个有效目标地址period1、两个段外目标地址period100/200，P_ref=100；有效body仍最小1 |
| 固定period | 同一地址三个period7，自动P_ref7，period和sample均写3；sample显式指定正P_ref20仍按1 |
| multiplication边界 | DF4×4611686018427387903=18446744073709551612可表示，告警超UINT32；DF4×4611686018427387904溢出失败 |
| addition边界 | 同一函数不同地址的分子UINT64_MAX+1，报count generation overflow，不产生output |
| 多层内联 | two_sites调用行16/17、声明行15，两个调用点偏移1/2；样本10/20。顶层total30，两个middle及各自leaf为10/20，最早调用点head10 |
| 同一调用点多inlinee | both声明11、调用行12，两个inlinee body3和7，同键(1,0)，稍后顶层body100位于2；total110、head3+7=10。去掉顶层body则total10、head10；none写出的head字段为0 |
| 分类 | 手写DWARF：函数[0x1000,0x1004)无行表，CU[0x1000,0x1008)，0x1008无CU，.plt=0x1100。各1条period10，in_func_no_line=1、outside=3且三个子类各1，usable0 |

补充素材位于 `llvm/test/tools/llvm-profgen/Inputs/ip-mode/counting-extra/`：`classification.s/.lds/.perfbin`、`head.c/.perfbin`及README。使用aarch64 GBS root的clang22.1.8、LLD22.1.8，GNU readelf2.43。完整生成命令、工具路径、大小和SHA保存在README及证据；未使用本机工具链。head通过 `-mllvm -no-discriminators` 明确保证两个inlinee同属(行12,discriminator0)。二进制不依赖网络或板上运行。

## 独立GNU核对与测试修正记录

`tools/profgen/check_ip_counts_addr2line.py` 使用两个GBS root中的GNU addr2line/readelf。GNU addr2line输出完整内联帧和行号，readelf取DW_AT_decl_line、PT_LOAD、DW_AT_GNU_discriminator及DWARF4 ranges。脚本独立构造计数树、半入、total与head，与生成的text每个字段比较，不调用LLVM符号化器取得oracle。

首轮8组有1组差异：GNU addr2line没有打印内联调用点的DW_AT_GNU_discriminator，原head素材两个调用点的base分别1/2，工具正确得到head3，而初始脚本错误合并得到10。补读GNU readelf属性后原8组0差异。另重新构造关闭discriminator的head素材，覆盖同一调用点两inlinee。没有据工具输出反抄golden、没有修改设计规则。

预跑还发现LBR FileCheck前缀重复定义，及writer测试重复运行时mkdir目录已存在，分别删除重复检查定义、改mkdir -p。首轮完整lit两个FAIL（ip-identity-list、ip-options）是迁移旧IP RUN时误改报错预期，已恢复预期；实际工具报错未变化。初始日志完整留证。简单预跑脚本缺少%python/yaml2obj支持导致的两条非lit失败也已补齐runner，不能算工具缺陷。最终验收以下文GBS lit为准。

## head最小1兜底不可达的不变量证明

`llvm/include/llvm/ProfileData/SampleProf.h:1000–1021`中，进入最终兜底之前的原始Count只有三种可能为0：最早body位置为0；最早callsite下所有inlinee估计为0；body和calls均空。总数为正时，最终返回值仍为1。本轮不改此库函数。

1. `T/ProfileGenerator.cpp:264–281`只让usable地址进入profile；`:295–308`只累计正整数分子，`:207–212`半入后正分子至少1，`:316–325`写body。补丁4从不插入零body；补零属于补丁5。
2. `:285–293`仅为命中地址逐层建立prefix，`:850–883`复用的树构造器只在这些调用中创建inlinee；每层的正分子分别累计，`:311–315`为各层写入至少1的total。因此内联子节点total至少1，库函数给它的估计至少1；最早调用点求和非0。`:215–232`先检查递归加法，不能借溢出触发0。
3. 每个FunctionSamples均因某usable地址而存在。地址的叶子层在`:295`取得body位置，顶层由`:711–714`的ProfileMap.create创建，祖先层由`:866–875`创建callsite和子节点；不存在total正而既无body也无callsite的函数。head调用在`:330–336`，发生在裁剪之前，树完整。
4. 因此该分支在补丁4不可达，通过IP输入触发它的测试留到补丁5。用户已明确授权延期；本轮其余三项head测试完整覆盖。

STATUS挂账：补丁5实现补零后，构造有样本函数，其最早位置被补零为0，随后才有正body；开 `--ip-head-samples=entry-estimate --ip-zero-fill=sampled-functions`，应head=1，不能以函数total替代入口计数。

## 仍可能绕过Error出口的共享调用点

以下均在身份门禁通过后可达，按授权留补丁6的兜底回调处理：`T/ProfiledBinary.cpp:259` createBinary运行文件；`:264`不合法image；`:274`运行文件IP符号/节元数据Expected解包；`:279`createBinary显式debug；`:281`debug元数据解包；`:1056`DWARFContext创建失败；`:1128`LLVMSymbolizer::symbolizeInlinedCode的unwrapOrError。首次符号化可能再打开调试文件。内部DWARF库诊断与损坏输入失败也不宣称已经完整覆盖质量报告契约。

新计数、选项校验、writer均返回Error/Expected至main统一出口；不调用exitWithError。临时文件在序列化、flush、close检查全部成功后才rename，错误先clear_error防析构再次终止；gcc、创建失败、rename失败均有lit。兜底回调、报告同路径校验、JSON质量报告属于补丁6，不在本轮冒充完成。

## 三轮构建与最终验收

同00报告第3节的配置、buildroot与worktree，GBS incremental、不clean，外层threads1、make并发10（nproc的一半）；整段setsid worker及setsid --wait GBS，nice19/ionice3。只给GBS设置隔离HOME/GIT_CONFIG_NOSYSTEM。每10分钟记录free/uptime，保留真实退出码和ALL-END。

| 轮次 | 开始→结束（+08:00） | 秒 | Ninja | GBS/ALL-END | lit |
|---|---|---:|---:|---|---|
| 补丁3独立 | 2026-11-02T18:50:05+08:00 → 2026-11-02T19:06:09+08:00 | 964.136 | 103 | 0 / OK | PASS/FAIL/UNSUPPORTED/XFAIL：61/0/1/1 |
| 补丁4初次 | 2026-11-02T19:46:27+08:00 → 2026-11-02T20:18:50+08:00 | 1942.871 | 112 | 0 / OK | PASS/FAIL/UNSUPPORTED/XFAIL：66/2/1/1 |
| 补丁4最终 | 2026-11-02T20:18:51+08:00 → 2026-11-02T20:47:19+08:00 | 1707.474 | 102 | 0 / OK | PASS/FAIL/UNSUPPORTED/XFAIL：68/0/1/1 |

初次补丁4因测试预期修正、fixture完善和弃用API清理而追加最终构建；不是只报告成功轮。初次编译出现make_scope_exit弃用警告，改用scope_exit后最终轮不再出现。平台已有的无build-id打包警告仍保留，未修改spec或链接flags。

[补丁3构建](evidence/06/04_patch3_build.txt)、[初次补丁4构建](evidence/06/07_initial_build.txt)、[初次lit两项失败原文](evidence/06/07_initial_lit.log)、[最终构建](evidence/06/08_final_build.txt)、[最终xunit](evidence/06/08_final_lit.xml)、[最终逐项分类](evidence/06/08_final_lit_summary.json)。

| 轮次 | 主机used采样峰值 MiB | available采样最低 MiB | load 1/5/15分钟各自峰值 |
|---|---:|---:|---|
| 补丁3独立 | 18553 | 12987 | [10.69, 7.44, 5.08] |
| 补丁4初次 | 23665 | 7874 | [11.4, 9.03, 8.65] |
| 补丁4最终 | 23958 | 7582 | [14.44, 10.92, 9.63] |

以上是整机离散采样，不是构建进程的独占内存，也不能当作连续峰值；没有available低于2GiB的采样点。未终止构建或他人的进程。打包期间自己启动的只读git diff --check持有索引锁，向该进程发TERM后自动释放，未手工删锁；最终暂存与diff检查重新通过。[记录](evidence/06/16_git_check_interruption.txt)

最终70项lit：PASS68、FAIL0、UNSUPPORTED1（cs-preinline-cost.test，REQUIRES asserts）、XFAIL1（invalid-perfscript.test），XPASS/UNRESOLVED/TIMEOUT均0。assertions=No与02相同；原50项逐项不变，旧13项IP与新增7项均通过，没有跳过FAIL。

C1：50个原测试、127条原命令、508个格式变体、1条纯IP负对照，636行/遍；两遍逐字节一致，与已提交基线0差异。新增/未纳入C1的测试文件共20个。未开IP时纯IP输入的原报错与退出码不变。[清单摘要](evidence/06/09_final_c1_summary.json)、[原始结果](evidence/06/09_final_c1.log)。

GNU独立核对最终9组（A64/A32/Thumb各sum与max、FS、嵌套调用、同调用点多inlinee）全部0差异，包括每个body/total/head字段。初始调用点discriminator差异及修正原文见[修正记录](evidence/06/14_test_corrections.txt)；[最终逐地址GNU输出及完整预期/实际树](evidence/06/10_independent_counts.json)、[独立脚本](../../../tools/profgen/check_ip_counts_addr2line.py)。它是这些DWARF4素材的核对脚本，不是通用DWARF读取器。

改动C++行均经GBS root的clang-format格式化及dry-run --Werror；[命令与退出码](evidence/06/12_format.txt)。新测试/素材源码使用单行文件头；[生成命令与版本](evidence/06/13_fixture_generation.txt)、[大小与SHA](evidence/06/13_fixture_manifest.json)。两个新增ELF为5,400及3,704字节。

## 完整真实导出重放

没有重新采样。使用05/07/09保留的13份完整文本做14次目标运行，每次reader地址计数及非身份/生成诊断输出都与 `temp/profgen-patch2-followup/after/<label>.stdout` 逐字节一致，依据是04已经做过MMAP2/PT_LOAD独立核对的结果；这里仅排除新增IP-IDENTITY/IP-GENERATION行。输入与ELF SHA、完整命令、stderr、各类样本数/period_sum、墙钟与RSS见[逐份证据](evidence/06/11_full_export_comparison.json)。

| 数据/目标 | 输入行数 | 目标样本 | usable | in_func_no_line | outside | no_cu | plt | 退出码/创建profile | 地址计数对04 |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 05-fixed | 7,703 | 6,496 | 0 | 0 | 6,496 | 6,473 | 23 | 1 / 否 | 一致 |
| 05-multi | 27,112 | 13,289 | 0 | 0 | 13,289 | 13,232 | 57 | 1 / 否 | 一致 |
| 05-freq | 4,930 | 4,096 | 0 | 0 | 4,096 | 4,079 | 17 | 1 / 否 | 一致 |
| 05-buildid | 7,510 | 6,322 | 0 | 0 | 6,322 | 6,298 | 24 | 1 / 否 | 一致 |
| 05-lost | 1,044,585 | 943,893 | 0 | 0 | 943,893 | 940,961 | 2,932 | 1 / 否 | 一致 |
| 07-fork-cases | 9,861 | 9,840 | 9,802 | 38 | 0 | 0 | 0 | 0 / 是 | 一致 |
| 07-exec-cases | 5,946 | 4,833 | 4,829 | 4 | 0 | 0 | 0 | 0 / 是 | 一致 |
| 07-exec-after | 5,946 | 1,081 | 1,081 | 0 | 0 | 0 | 0 | 0 / 是 | 一致 |
| 07-deleted-libdeleted_probe.so | 169 | 151 | 151 | 0 | 0 | 0 | 0 | 0 / 是 | 一致 |
| 07-module | 334,304 | 51,874 | 0 | 0 | 51,874 | 51,839 | 35 | 1 / 否 | 一致 |
| 09-fixed | 7,661 | 5,865 | 0 | 0 | 5,865 | 5,862 | 3 | 1 / 否 | 一致 |
| 09-multi | 31,066 | 14,331 | 0 | 0 | 14,331 | 14,317 | 14 | 1 / 否 | 一致 |
| 09-freq | 2,625 | 2,006 | 0 | 0 | 2,006 | 2,005 | 1 | 1 / 否 | 一致 |
| 09-buildid | 7,270 | 5,611 | 0 | 0 | 5,611 | 5,605 | 6 | 1 / 否 | 一致 |

**任务预期的一处事实差异：不是全部no_cu。** 运行文件没有DWARF，但仍有可识别的.plt节；按冻结5.4.2的优先细分，落在该节的样本属于outside_dwarf_func.plt，其余属于no_cu。RPi4 .plt区间为[0x14004,0x14d7c)，RPi5为[0x345f0,0x35710)。GNU readelf -SW独立读取后逐VA重新累计，9份数据的plt样本数、period和均与工具一致；outside=plt+no_cu、usable=0、退出1、不创建output都符合预期。[RPi4节表](evidence/06/15_rpi4_sections.txt)、[RPi5节表](evidence/06/15_rpi5_sections.txt)、[独立计数](evidence/06/15_real_plt_verification.json)。没有为了满足“全部no_cu”的预测改动分类规则。

共享DWARF加载器还输出原有warning `Loading of DWARF info completed, but no binary functions have been retrieved.`，之后是 `IP sample mode: no usable samples`。初始验收脚本要求stderr仅有最后一行而触发断言；已在保留原始stderr的前提下核对上述warning和最终错误，不删除或归一化原始证据。[验收脚本初次失败及系统hook栈](evidence/06/16_post_validator.txt)

07的四个带DWARF历史目标离线生成profile；这只证明旧材料在本机的处理，不代表已完成板上采样→优化编译→运行验收。本轮没有连接板子。

## 留给补丁5/6及边界

- 补丁5：按需指令边界、avg、sampled-functions补零、prev-inst；补本轮已授权延期的head最小1兜底输入测试。聚合默认值仍未决定，必须显式指定sum/max。
- 补丁6：质量JSON报告、分级与失败报告、全IP流程兜底回调、profile/report同路径校验、LOST语义与诊断报告等。当前只提供隐藏诊断与基本安全profile写出。
- 带DWARF的板上端到端与性能评估留到后续集成，不把合成计数素材或历史数据离线profile当作优化收益证明。
- 冻结设计与C1清单哈希保持不变（见提交审计）；无新规则修改，唯一不可达用例按用户授权延期。未向LLVM远端/Gerrit推送、不修改认证、不索要密码。
- 所有显式生成文件位于WORKDIR；原始日志、RPM、工具、profile、完整输出保留在 `temp/profgen-patch4/{patch3-fix,counting-build,counting-final,independent-final,full-final}/`。新增提交证据每文件小于1MB。
- 无新增已观察到的越界文件写入。系统Python异常hook曾在导入阶段失败，栈已保存；没有手工读取或改动外部项目输入/认证。GBS chroot内路径均对应WORKDIR内buildroot。
