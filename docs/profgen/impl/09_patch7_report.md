# 补丁7：文档、枚举选项与报告约定

2026-11-03。基于补丁6 `1dd4b9acd84045c230e77cc68d85eafca58eae88`。本轮只在同一会话执行；未连接开发板、不推LLVM/Gerrit，不改冻结v0.7正文及boundary-golden。已完成正式GBS、lit、C1、完整导出重放和本地LLVM提交；未向LLVM远端推送。

## 1. 枚举选项与解析错误

五项改成 `cl::opt<枚举, false, IPEnumParser<枚举>>` 与 `cl::values`：weight=period/sample，aggregation=sum/max/avg，head=none/entry-estimate，zero=none/sampled-functions，skid=none/prev-inst。有效文本、默认语义不变。aggregation内部的Unspecified不是公开取值；无`cl::init`默认聚合，仍以`getNumOccurrences()`拒绝未指定，错误原文保持 `IP sample mode requires --ip-aggregation during evaluation`。help明确“no default during evaluation; must be explicitly specified”，删除已过时的“profile generation pending”。

LLVM的通用枚举parser在非法值处调用`Option::error`，默认直接写errs，并不使用`ParseCommandLineOptions`的Errs参数（`llvm/include/llvm/Support/CommandLine.h`的`parser<DataType>::parse`；`llvm/lib/Support/CommandLine.cpp`的`Option::error`）。开发负对照捕获了这一行为：出现原解析器错误，但缓冲区为空，旧IP入口会继续运行。因此增加仅用于五项新IP枚举的小适配器：合法值仍走cl parser，非法值使用同一cl::values表与Option::error原文，定向写入现有解析缓冲区；不修改共享CommandLine库，不新增一套允许值字符串表。

普通缓冲解析错误由main原样打印一次，报告reason与stderr逐字节一致，不再额外套`llvm-profgen: error:`。缺binary/负pid的既定特殊诊断保持。非IP路径的C1另作两遍逐字节核对，不用“编译成功”推断未回归。

`ip-counting-options.test`仅改五处FileCheck非法值文本：

| 选项 | 旧匹配文本 | 新匹配文本 |
|---|---|---|
| ip-weight | `invalid --ip-weight` | `for the --ip-weight option: Cannot find option named 'bad'!` |
| ip-aggregation | `invalid --ip-aggregation` | `for the --ip-aggregation option: Cannot find option named 'bad'!` |
| ip-head-samples | `invalid --ip-head-samples` | `for the --ip-head-samples option: Cannot find option named 'bad'!` |
| ip-zero-fill | `invalid --ip-zero-fill` | `for the --ip-zero-fill option: Cannot find option named 'bad'!` |
| ip-skid | `invalid --ip-skid` | `for the --ip-skid option: Cannot find option named 'bad'!` |

质量测试新增五项非法枚举的parse失败报告、单次原文、旧profile保持和无临时文件断言；未知普通选项同样检查stderr=reason。五项枚举与未知普通选项均非零退出，parse失败报告reason与stderr逐字节一致；原始stderr及JSON见[13](evidence/09/13_parser_and_overflow.json)，正式lit逐条断言退出码。

## 2. 边界诊断与golden

IPBoundary的枚举失败改为条件描述，附`function`、十六进制`address`、半开`DWARF=[begin,end)`。Thumb前缀证明失败指出交集起点；截断指出被截断指令的起点；同址冲突指出冲突地址。加载映射失败没有可断言的损坏字节地址，附该函数受影响的样本地址及其DWARF区间，不能把它解释为元数据损坏位置。函数失败汇总直接打印带上下文的原因，不再以素材/函数名加冒号开头。

修改的现有期望：boundary-extra/check-boundaries.py中的bad-thumb-start/end、bad-arm-start匹配条件文本；bad-a64-start/end已有条件文本继续使用；新增每个负对照都包含函数/地址/区间且不含“素材名:”的断言。ip-boundary-metadata.test的两条ALL-DAG从`count_loop/main: no usable mapping symbols`改为`no usable mapping symbols (function=count_loop/main`，保留两个失败函数、退出码与输出不生成的检查。

**boundary-golden.json逐字节未改**，不仅数值未改；所有素材二进制和地址清单未改。完整测试diff见[01](evidence/09/01_test_changes.diff)，哈希与空golden diff见[07](evidence/09/07_unchanged_inputs.json)。

## 3. unknown、确认不存在与LOST溢出

统一约定选择JSON **null** 表示确认不存在；`"unknown"`表示未读、未取得或不可定义。ID已读取但没有、没有debug输入、证据项不携带ID、成功时没有failure_stage/reason均为null。已提供debug但尚未读取其ID仍为unknown。命令行中显式空token转为null，保留数组位置并在schema注明。选项的`none`仍是策略名字，不能把它改成null。schema_version继续为1，尚未发布。

逐字段字符串审计见[06](evidence/09/06_string_audit.json)：既包括实际可能为空的路径/ID/argv，也包括由解析器或内部枚举保证非空的事件、来源、等级、警告和函数名称。所有生成报告递归断言无空字符串值。字符串辅助函数返回拥有存储的json::Value；开发测试曾抓到对临时榜单字符串借用造成的无效UTF-8，已修为拥有字节后复测，不能把首次开发输出当正式结果。

`L+S>UINT64_MAX`现在是不可表示的诊断比率：`lost.exported_lost_ratio="unknown"`、新增`W_LOST_RATIO_OVERFLOW`；若显式设置最大丢样率则lost_ratio_check=unknown并加既有未知项告警，不因该项失败。未设置仍为not_evaluated。L本身的累计溢出仍是原有计数错误，不混同本次分母规则。测试用一条L=UINT64_MAX的LOST加一条正常样本，分别不设置/设置阈值0，两次均成功生成profile；保留L与S的原始uint64值。

## 4. 用户文档与schema

文档放在同一`llvm/docs/CommandGuide/llvm-profgen.rst`的IP子节及schema子节。理由：命令行、采集约束、计数语义和失败JSON需要一起阅读；单一文档避免版本漂移。未另加设计文件或修改冻结正文。

涵盖：采集/完整导出字段、严格语法与特殊DSO、全部公开IP选项和默认/过渡语义、已有保留/拒绝选项、保守身份与generation=0局限、PT_LOAD换算、P_ref和sum/max/avg、head/补零/skid、映射符号边界、输出原子替换与路径冲突例外、同名函数/LOST/line0等局限。没有板子私有路径。

schema逐字段写类型、意义、单位、unknown/null、排序和比率分母；有完整warning代码表与verdict优先级。采用点路径、数组元素`[]`，不能把空数组推断为缺少该字段。为让实际lit覆盖完整字段形状，质量fields组追加了有/无ID的MMAP2和同名函数临时副本：只把临时ELF内`count_loop\0`等长改为`two_sites\0\0`，不移动字节/节/地址、不修改源素材，也不把该人为副本当真实身份样例。

[字段核对脚本](evidence/09/check_schema.py)从**lit实际生成的**schema1报告递归取字段路径，对RST inventory做双向差集，并递归拒绝空字符串值；有意保留旧报告的路径/IO负对照不含schema1，单独排除。开发与正式检查均为110份报告、345路径，两差集为空；正式[字段清单与差集](evidence/09/12_schema.json)还记录空字符串值列表为空。

GBS root内Python3.14确认没有docutils和Sphinx，未安装/下载任何东西。采用同一root的CMake内置RST解析器：将其逐字节相同的可执行文件放在temp的私有可重定位目录，配置仅本任务的Help树，解析完整最终rst到文本，退出0。没有改GBS root或系统文件。这是**RST子集解析**，不等于完整Sphinx域、角色/指令检查或整站文档构建；额外检查新增option指令后的空行与隐藏测试接口未泄漏。[平台工具盘点](evidence/09/04_doc_tool_inventory.json)、[命令、哈希与限制](evidence/09/04_rst_check.json)。

隐藏接口只在本实现报告登记：`--show-ip-address-counts`、`--show-ip-boundaries`、`--ip-test-inject-failure`；未写入用户rst。schema中的callback计数作为已存在字段照实记录，不借此公开隐藏选项。

## 5. 便宜检查与正式验收

先开发定向编译，再受影响测试/全lit和C1，通过后才启动GBS。开发错误、修复和工具哈希保存在[03](evidence/09/03_development.json)。其中_FORTIFY_SOURCE告警来自开发编译-O0；正式构建仍用原spec优化参数。新增测试场景扩充已有组，lit文件总数仍85。

GBS参数与00报告一致：同worktree、同root、incremental，不clean、不改spec；整段worker由setsid脱离会话，gbs子进程setsid --wait取真实退出码，nice19/ionice3、jobs=nproc/2。只有GBS使用隔离HOME/GIT_CONFIG_NOSYSTEM。worker每600秒free -m/uptime，始末也采集；无论成败写带时间ALL-END。原始日志/结束标记在`temp/profgen-patch7/build/`。

正式GBS一次成功：2026-11-03 **21:24:56–21:44:56+08:00**，**1199.800秒、108 Ninja步**；另有一个1步CMake子构建，非第二次完整构建。GBS_EXIT=0，ALL-END OK。资源采样available最低12,986MiB、used最高18,554MiB；1/5/15分钟load采样峰值9.95/10.82/7.07；无available低于2GiB采样点。这些是周期采样的峰值，不是连续采样上界。[完整结束标记、资源与日志尾部](evidence/09/08_build.json)。

- **正式%check lit：85项，83 PASS、0 FAIL、1 UNSUPPORTED、1 XFAIL**；逐项与补丁6的85项结果一致，新增测试场景放入现有组，没有新增lit文件。UNSUPPORTED=`cs-preinline-cost.test`（assertions=No），XFAIL=`invalid-perfscript.test`；FAIL清单为空。[日志、测试名与XML哈希](evidence/09/09_lit.json)。
- **C1：两遍各636条、两遍字节一致、对已提交清单0差异**；原50测试127命令，另1纯IP负对照，508格式变体；35个新IP测试仍排除。[清单摘要与命令](evidence/09/10_c1.json)。完整大清单留`temp/profgen-patch7/formal-c1.json`，既有基线未覆盖。
- 新正式工具SHA-256：`334a09290f53eb4c793ae91759f2b6344a36e63317820eb9151771b262dc3f30`。与补丁6不同，符合此次代码重编；不用开发工具SHA替代正式工具。
- GBS clang-format对4个C++文件的改动行格式化并dry-run，全部退出0；Python/RST不适用clang-format。`git diff --check`通过。[命令与原始结果](evidence/09/02_format.json)。

14次完整导出各运行两遍，profile、stdout、stderr、退出码均与补丁6一致，两遍profile/JSON/诊断也逐字节相同。对于原本generate失败的strip目标，“profile一致”指两边均未创建文件，不声称成功产出profile。JSON**仅确认不存在的字段变为null**；这些真实数据没有触发L+S溢出，溢出由独立lit负载覆盖。每个字段的路径、旧值、新值都在[逐份JSON差异清单](evidence/09/11_full_replay.json)，未删掉映射列表中的重复形状来隐藏差异。

| 完整导出/目标 | JSON变化字段数 | profile与补丁6 | 两遍JSON与诊断 |
|---|---:|---|---|
| 05-fixed | 7 | 相同 | 相同 |
| 05-multi | 11 | 相同 | 相同 |
| 05-freq | 7 | 相同 | 相同 |
| 05-buildid | 7 | 相同 | 相同 |
| 05-lost | 7 | 相同 | 相同 |
| 07-fork-cases | 8 | 相同 | 相同 |
| 07-exec-cases | 8 | 相同 | 相同 |
| 07-exec-after | 8 | 相同 | 相同 |
| 07-deleted-libdeleted_probe.so | 8 | 相同 | 相同 |
| 07-module | 1194 | 相同 | 相同 |
| 09-fixed | 7 | 相同 | 相同 |
| 09-multi | 13 | 相同 | 相同 |
| 09-freq | 7 | 相同 | 相同 |
| 09-buildid | 7 | 相同 | 相同 |

变化类别：缺失的binary/debug/mapping/evidence ID及debug路径由空串（或未给debug时的unknown）改null；成功报告的failure_stage/reason由unknown改null。07-module有大量映射/证据项，因此变化1194处，但都是上述同一约定。不存在数值、分类、身份等级、阈值判定或profile变化。06完整LOST文本仍缺失，不把05-lost冒充06。

独立边界诊断仅改文本，所有golden数值、素材和指令地址不变。代码位置索引见[14](evidence/09/14_source_locations.json)：`llvm-profgen.cpp:134`枚举适配、`:165`显式聚合、`:266`occurrences、`:336`IP入口、`:462`解析缓冲、`:489`一次原文输出；`IPBoundary.cpp:133`条件/函数/地址/DWARF上下文；`IPQualityReport.cpp:76`null、`:223`和`:645`LOST分母溢出、`:740`失败/成功字段。

### 本地提交与补丁导出

LLVM本地提交 `e4642a8ad9e0acb990b45ade3ef7aca755cd80f2`，作者与提交者均为Hao Lin <hao.lin@samsung.com>；9文件、+1633/-103行。仅4个工具文件、4个测试文件与CommandGuide；spec没有进入提交，原本地diff逐字节保持。源码src/llvm状态干净。

导出[0007补丁](../../../patches/profgen/0007-llvm-profgen-Document-IP-mode-and-finalize-options-and-reports.patch)（98,410字节），SHA-256 `78502de2024560efc8c1cd0536ebd16a049fc4f9313ef23fb514d265f50d3c60`；`git apply --reverse --check`退出0。[提交、范围、冻结文件及反向检查审计](evidence/09/15_commit_audit.json)。结果仓库只推GitHub当前分支；LLVM本地分支不推远端。


## 6. 待设计v0.8登记

- 五项IP选项为枚举/cl::values，aggregation显式必选无默认；枚举parser错误仍使用原Option::error文本、写parse失败报告。
- 边界错误去掉素材名硬编码，带函数/地址/区间；golden数值与文件未改。
- schema1确认不存在用null、未知用unknown、无空字符串值；成功的failure_stage/reason为null。完整argv中的空token用null且保持位置。
- LOST分母超过uint64不使整次失败，警告W_LOST_RATIO_OVERFLOW；配置门槛时状态unknown，不因该项失败。
- 普通缓冲解析失败只输出一次解析器原文，reason与其一致。

## 7. 挂账与边界

本轮闭合IP选项枚举/cl::values及文档收尾；不关闭06完整LOST导出缺失、08产物真实avg上板核对、非叶子line0上板裁决，以及正式非增量构建前撤销spec本地测试改动。7个补丁完成不等于第二阶段评估、正常非增量构建或Agent开发完成；下一步等待用户授权。

所有产出留WORKDIR，临时文件留temp；未读本任务之外的Downloads或附件，未连接板子、不推LLVM/Gerrit、不改认证或索要密码。原结果仓库未跟踪config/、gbs_*.conf保持不动。无新增已观察到的工具越界写入；不声称做过全系统写入审计。
