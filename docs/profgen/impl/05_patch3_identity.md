# 补丁3：IP采样身份校验

2026-11-02。基线为补丁2 `6e1b1b00c18b52de84351752767f0678113036f6`；冻结设计v0.7的SHA-256核对为 `eec6b208d8e1fedb840f0933eb20a37c188890b6c8c29e43986c5c9bbca9f6be`，正文未改。没有连接开发板，没有推送LLVM远端或Gerrit；仍不生成IP profile。

用户已澄清：目标无ID而输入有ID为mismatch；目标有ID而输入缺证据为unverified，可由allow-missing放行；目标与调试文件单边缺ID双向均为mismatch。与冻结设计5.3.2一致，无需修改设计。此前暂停后续实现等待澄清，继续完成本轮实现与验收；后续generation修正另作一次增量构建。

用户随后明确授权修正冻结设计5.3.3第5条的generation语义，见下文“规则修正登记”；不修改冻结设计文件正文。第二轮构建成功；最终验收结果见第4.1节。

LLVM本地补丁3提交 `30ceb73e9dcbe233f747d1ed8c97d9e3919564b0`，16文件、+1,185/-71行，新增5个lit文件；仅本地提交，不推LLVM远端。[补丁](../../../patches/profgen/0003-llvm-profgen-Add-build-id-identity-checks-for-IP-sample-mode.patch)。

## 1. 实现与共享代码

- 新增 `llvm/tools/llvm-profgen/IPIdentity.cpp`：直接用object读取两份ELF的build-id与节表，严格读取buildid-list，做保守汇总、冲突检查及未验证身份的跨pid歧义检查。不构造ProfiledBinary，不读DWARF，不用文件所在目录判断身份。
- `IPPerfReader` 将候选选择与地址计数拆开。输入全部解析完成后，选择候选路径，完成身份判断，再对已选样本计算地址及sample_count/period_sum。映射记录只作身份证据；样本不按pid重放映射，dsoff换算仍只使用目标可执行PT_LOAD。
- 新增 `--perf-buildid-list`、`--allow-missing-build-id`，按getNumOccurrences在非IP模式拒绝，包括显式false。已有 `--debug-binary` 仍是匹配调试文件；身份阶段先核对其note，后续符号化尚未实现。
- `llvm-profgen.cpp` 的共享解析错误缓冲在失败时总是原样打印；若是IP缺binary/负pid，随后走IP统一错误出口追加专门诊断。不再吞掉同次命令的未知选项错误。其他非IP路径与原测试不改。
- `CMakeLists.txt` 只登记新编译单元。`IPPerfReader.h/.cpp` 增加身份选项、候选集合及诊断；既有LBR reader/ProfiledBinary/生成器不改。
- 所有新IP错误返回Error/Expected，main统一打印。失败不打开output；身份通过或允许unverified后仍返回补丁2的固定过渡错误。质量报告、兜底回调与原子写出留补丁6。

代码位置（相对 `temp/llvm-profgen-enh/llvm/tools/llvm-profgen/`）：`IPIdentity.cpp:61`、`:85`、`:125` 的readObjectIdentity/readBuildIDList/validateIdentity分别负责对象、list与汇总，`:251–280`处理generation；`IPPerfReader.cpp:267`、`:329`、`:356` 的selectSamples/countAddresses/read负责分阶段调用；`llvm-profgen.cpp:114`注册选项，`:281`打印缓冲的CLI错误。提交审计附最终路径/行数，测试按下表的文件名定位。

### 1.1 等级与诊断

映射原始路径精确匹配候选路径，不合并deleted/未删除拼写。M只含可执行映射；非可执行映射缺证据不降级，已知冲突仍失败。M为空为unverified。每个可执行映射先选最强证据（mmap2、非deleted路径list、缺失），路径及全局取最低等级。已知冲突优先，包括目标无note而输入有ID、目标与显式debug一方有ID一方无ID。只有输入证据缺失而目标有ID属于unverified；这与冻结设计5.3.2的具体规则及deleted用例一致。

build-id完整字节比较，十六进制大小写不影响结果；不截取20字节或8字节前缀。同一路径list包含两个不同ID时不选最后一条，按冲突失败。不同目标的list条目不与目标note比较；格式错误及list内部同路径冲突仍不能静默忽略。

隐藏输出追加 `IP-IDENTITY`：全输入是否出现MMAP2 ID、目标/realpath/debug路径和ID、regex/basename选择方式、原始候选路径及deleted状态、每个观察映射的来源与等级、逐路径汇总和最终等级。字符串用引号/转义、路径按字典序、映射按原输入序号，输出确定。失败时保留已形成的身份诊断；没有伪造无法取得的等级。

未验证歧义只检查已选候选，跨全部pid；设备/inode与generation用数值比较，避免十六进制大小写/前导零导致假冲突；generation=0按本轮授权修正视为未知。歧义错误提示正则或build-id，不允许allow-missing绕过。

## 2. 格式依据与测试

buildid-list实测依据为 `docs/probe/evidence/05/02_perf_formats_mapping.txt:101–115`：101–104、106–107等行的ID栏为空，路径前有空白；105/108为40位hex+分隔空白+完整路径；114是带ID的 `[kernel.kallsyms]`。默认录制输出见124–127。读取器不把无ID的路径解析为十六进制，不截断路径内部空格；未知、空行、NUL/CR、奇数长度或非hex的ID字段报错。[原文带行号摘录](evidence/05/01_preflight.txt)

新增五个lit文件：`ip-identity-matrix.test`、`ip-identity-chain.test`、`ip-identity-ambiguity.test`、`ip-identity-list.test`、`ip-identity-probe.test`。perfscript/list文本由split-file/echo准备，ID取补丁1素材的实际GBS readelf结果。测试不依赖主机perf、网络或开发板。

补丁2测试仍覆盖原规则：缺证据的正向读取用例显式加allow-missing；symlink用例的两个同名路径补一致MMAP2 ID，使其继续验证两路径计数合并，而不是绕过新歧义规则。原50个C1测试不改。

| 冻结条文 | 代码/职责 | lit覆盖或本补丁边界 |
|---|---|---|
| 5.1.1、5.1.2：新增IP专属选项 | main门控、IPReaderOptions | list：未启用IP时两选项拒绝（含false） |
| 5.1.4.2–3：两文件任一probe节拒绝，独立于强制DWARF | readObjectIdentity | probe：run/debug/desc-only各有无use-dwarf；普通DWARF不受影响 |
| 5.3.2.1：mmap2/list/inode来源；空ID行 | readBuildIDList、validateIdentity | matrix：空ID、MMAP与MMAP2；list：空白ID/空格路径/格式负对照 |
| 5.3.2.2：M、空M、非执行映射 | validateIdentity | matrix：无映射、仅非执行、加入无ID非执行不降级/冲突失败 |
| 5.3.2.3：最强证据→最低等级、冲突优先 | Grade与路径/全局汇总 | matrix：全部/部分/无mmap2 ID×list一致/缺失/冲突，缺失与冲突并存 |
| 5.3.2.3：一方有ID另一方无ID | readObjectIdentity/完整ID比较 | chain：目标无ID而mmap/list有ID、debug双向缺note、allow不放行 |
| 5.3.2.4：observed_mmap_build_id | 全Mappings观察 | 真实数据诊断与matrix |
| 5.3.3.1：候选regex或realpath basename，raw/deleted保留 | selectSamples保留补丁2语义 | 既有selection；ambiguity默认basename与regex排除 |
| 5.3.3.2：完整ID一致性、长度不同失败 | getBuildID与hexID | chain：8字节/20字节、other同名不同ID；matrix：hex大小写 |
| 5.3.3.3：保守多映射/多pid汇总 | 候选路径收集全部映射，不作样本绑定 | matrix多pid与真实fixed/multi |
| 5.3.3.4：deleted不能靠list补足 | Deleted门控 | ambiguity：默认拒绝、allow继续、自己的mmap2可验证、冲突拒绝 |
| 5.3.3.5：未验证歧义及本轮授权generation修正 | Basenames/Inodes/KnownGenerations/DeletedStates | ambiguity：同名异路径、同路径异inode、deleted/live、正则排除；0/非零及反序不冲突、不同非零冲突、0/0不冲突 |
| 5.3.3.6：目标无note | 完整ID比较及最终grade | chain/matrix：三方无ID与单方有ID |
| 5.3.3.7：DWARF覆盖/对齐合理性 | 本补丁不符号化、不输出正式质量报告 | 留生成/报告补丁，不把unverified解释为计数质量已验证 |
| 5.3.3.8：mapping为观察记录数 | Mappings及诊断原序号 | 既有real-records与整份导出统计不变 |
| 5.3.3.9：采样A→debug A，不按目录判定 | 身份只看note，不看BUILD目录 | chain：复制到BUILD通过、symlink指向不同ID失败、other代表不同ID产物 |
| 5.3.4.1–2：运行/调试分工、note身份链 | 布局从binary读；debug只取note/节名 | chain：未strip/stripped配同debug通过，不要求SHA相同 |
| 5.3.4.3：DWO/DWP | 此轮不加载DWARF | 后续生成/报告阶段沿用已有路径 |
| 5.3.4.4：拆分前后profile逐字节相同 | 此轮仍无profile生成 | 先检查相同VA及计数、身份；profile字节对照留补丁4 |
| 5.6.3.3：Error/Expected及无输出副作用 | main统一出口，不调用exitWithError | 身份/歧义/probe失败不创建文件，预置sentinel不变 |
| 补丁2遗留CLI诊断 | main解析缓冲打印 | list：未知选项+缺binary/负pid，两类错误均在 |

## 3. 真实数据验收

用本轮新工具运行8次，结果均符合冻结规则；构建结束后已核对工具SHA与这些运行时一致。完整命令、真实退出码、每条IP-IDENTITY原文与输入/ELF哈希见[真实身份验收](evidence/05/02_real_identity.json)。

| 输入/目标 | 选项 | 最终等级与退出原因 |
|---|---|---|
| 09 buildid / libc | 无list、无allow | verified；过渡错误退出1 |
| 09 fixed / libc | 09固定录制的buildid-list | verified-path；过渡错误退出1 |
| 05 fixed / libavcodec | 默认 / allow各一次 | unverified；默认缺证据拒绝，allow后过渡错误 |
| 09 fixed / libavcodec | 默认 / allow各一次 | unverified；默认缺证据拒绝，allow后过渡错误 |
| 07 deleted / libdeleted_probe.so | 默认 / allow各一次 | unverified；无mmap2 ID，默认拒绝，allow后过渡错误 |

09 libc来自 `temp/rpi5-prefreeze/libc`，SHA `e28a87adc858f1f166ab7d781621f6afc79a2fef83323c19d66e64e003b6ee90` 与任务指定值一致；note及MMAP2为 `8b45bf5b6a314fc498c8c73f164d6259c895405b`。fixed list确实保留在 `temp/rpi5-prefreeze/fixed_buildids.json` 的stdout，本轮原样提取到 `temp/profgen-patch3/identity-real/09-fixed.buildids`。未调用主机perf或重采。

07的“无mmap2证据”指没有MMAP2 build-id，不是没有MMAP2记录；原记录仍有设备/inode/generation。所有8次output均未创建。

### 3.1 首轮整份导出与规则修正依据（历史结果）

14次目标运行均使用原完整文本，加allow-missing。**11次通过身份门禁并到达过渡错误；这11次的全部地址计数与统计和04一致，剔除新增IP-IDENTITY行后stdout逐字节相同。3次按冻结歧义规则拒绝，未进入地址计数。** 不是输入格式被拒绝，也没有过滤映射或忽略generation来使测试通过。[逐份命令/身份诊断/比对](evidence/05/06_full_exports.json)

| 运行 | 04目标数 | 本轮结果 |
|---|---:|---|
| 05 fixed | 6,496 | 相同 |
| 05 multi | 13,289 | generation歧义，身份失败，无地址计数 |
| 05 freq | 4,096 | 相同 |
| 05 buildid | 6,322 | 相同 |
| 05 lost | 943,893 | 相同 |
| 07 fork | 9,840 | 相同 |
| 07 exec/cases | 4,833 | 相同 |
| 07 exec/after | 1,081 | 相同 |
| 07 deleted | 151 | 相同 |
| 07 module/libc | 51,874 | generation歧义，身份失败，无地址计数 |
| 09 fixed | 5,865 | 相同 |
| 09 multi | 14,331 | generation歧义，身份失败，无地址计数 |
| 09 freq | 2,006 | 相同 |
| 09 buildid | 5,611 | 相同 |

三个目标路径本身相同，设备/inode一致，但generation不同：

| 原始完整文本行号 | 目标 | 设备/inode | generation |
|---|---|---|---|
| `temp/rpi4-prefreeze/multi_dsoff.txt:3115`、`:4463` | libavcodec | b3:02 / 1702 | 0 / 4080200201 |
| `temp/v04/module.txt:20`、`:4277` | libc | b3:02 / 1073 | 0 / 583608144 |
| `temp/rpi5-prefreeze/multi_dsoff.txt:3595`、`:4318` | libavcodec | b3:02 / 1290 | 0 / 3403977211 |

[原文与源码证据](evidence/05/07_generation_ambiguity.txt)。`src/linux-rpi/tools/perf/util/synthetic-events.c:486` 明确把合成映射generation设为0；`kernel/events/core.c:9019`取inode的generation，`:9057`写入事件；`tools/perf/util/event.c:344–349`把这些字段打印出来。这与当前观测一致，但不凭此认定每条generation=0记录的来源，更不把0自行当通配值。

冻结5.3.3.5要求比较完整设备/inode/generation元组，不允许allow-missing放行该歧义。按原规则，三个输入必须失败；与本任务“所有完整导出地址计数仍与04一致”不能同时满足。当时暂停提交并请求裁决；用户随后授权下述修正。06完整LOST样本文本未保留的旧限制仍在，本轮未重采/重导。


### 3.2 规则修正登记：generation=0为未知

**授权来源：** 本轮用户在发现上述真实材料后，明确修正冻结设计5.3.3第5条，要求在实现报告单独登记；本报告承担本次变更记录，v0.7设计文件本身保持原SHA不变。

- 同一路径（歧义检查时去掉deleted标记）的设备号或inode不同，仍报歧义。
- generation=0视为未知。只有两条记录generation均非0且不相等才报歧义；0/非0、非0/0和0/0均不构成generation冲突。
- 同路径deleted/live混合、同basename不同路径等其他歧义规则不变；已知build-id冲突仍优先失败，不受allow-missing或本修正放行。
- 理由与源码：perf为预先存在的映射合成MMAP2时显式写0（`src/linux-rpi/tools/perf/util/synthetic-events.c:486`）；内核记录取真实inode generation（本地源码 `kernel/events/core.c:9019`、`:9057`，对应用户所引版本中的8918/8956）。原文及源码commit见证据07。
- **已知局限：inode被复用、且其中一条记录generation为0时，替换可能无法被发现。** 本修正不会把这种缺证据情况提升为verified；它仍为unverified，需要显式allow-missing。

实现用每个路径的设备/inode集合与非零generation集合分别检查。补充lit覆盖要求的四种情况，并额外检查0/非0的反向顺序，避免顺序相关行为。

### 3.3 映射数量与输入位置（仅佐证）

| 完整输入/候选路径 | generation=0条数 | 非0条数 | 首个样本行 | 0值记录是否全在首样本之前 |
|---|---:|---:|---:|---|
| 05 multi / `/usr/lib/libavcodec.so.62.11.100` | 1 | 2 | 4,194 | 是 |
| 09 multi / `/usr/lib64/libavcodec.so.62.11.100` | 2 | 2 | 4,158 | 是 |
| 07 module / `/usr/lib/libc.so.6` | 60 | 535 | 4,194 | 是 |

[逐条行号、pid、字段与统计](evidence/05/08_generation_positions.json)。完整0值行号清单在JSON的`zero_line_numbers`，非0行号也全部保留。首个样本按完整文本中第一个样本行计，不是首个目标样本；映射按观察记录计数，不去重。本结果支持源码解释，但**不作为判定规则**：实现不因记录位于样本前/后改变generation语义，也不据此给每条记录标定合成/内核来源。

### 3.4 修正后的最终完整重放

修正后14/14次均通过身份门禁并到达固定过渡错误，output均未创建。全部地址sample_count/period_sum、统计与04一致；仅剔除新增IP-IDENTITY诊断后，stdout逐字节相同。05 multi目标恢复为13,289、09 multi为14,331、07 module/libc为51,874，未过滤原文本或映射。

[最终14次完整重放](evidence/05/09_final_full_exports.json)、[最终8次真实身份重验](evidence/05/09_final_real_identity.json)。09 libc仍分别为verified与verified-path；其他缺证据用例默认拒绝/allow后unverified，与前述表一致。构建结束后已核对工具SHA与重放时一致。

最大05 lost文本1,044,585行、目标943,893，本轮墙钟约1.419秒、峰值RSS319,920KiB；单次热缓存观测，且当时GBS正打包，不能直接据此作性能回归判断。大文件和全输出只留 `temp/profgen-patch3/gen-final/` 与 `generation-fix/identity-real/`。

## 4. 构建、lit与C1

配置、buildroot及worktree沿用00第3节；只给GBS及其子进程设置隔离HOME/GIT_CONFIG_NOSYSTEM。整段worker以setsid后台启动，GBS用setsid --wait，nice19/ionice3、线程1、make/MLGO并发10。未加clean或clean-once、未改配置/spec；启动前未发现其他重构建，不需要sudo密码。

```text
START 2026-11-02T17:39:22+08:00
BUILD_START 2026-11-02T17:39:22+08:00
END 2026-11-02T17:57:18+08:00
GBS_EXIT 0
ELAPSED_SECONDS 1076.547
NINJA_TOTAL_OBSERVED 100
ALL-END 2026-11-02T17:57:18+08:00 OK
```

首轮成功（尚未采用generation修正）：**1,076.547秒（17分56.547秒）、Ninja100步**。日志2116/2117/2119行编译三个实现文件，2120行链接llvm-profgen。开始/10分钟/结束资源采样：used峰值17,077MiB、available最低14,463MiB，load峰值11.85/6.93/4.78；无available低于2GiB采样点。整机离散观测不代表任务独占或瞬时峰值。[构建原文](evidence/05/03_build.txt)、[摘要](evidence/05/03_build_summary.json)。

新工具SHA-256 `a0358528585f264faa65c4b52de8b1476ecdec79c65f4b1652506bb9146624d9`，已重新链接，且与真实身份预检所用工具SHA相同。GBS root clang-format对新文件整体、其余文件的改动行格式化，dry-run/Werror均0。[命令与返回码](evidence/05/03_format.txt)

%check实际执行lit，**63项：PASS61、FAIL0、UNSUPPORTED1、XFAIL1**（5.63秒）；原50项逐项名称/状态/原因与02相同。UNSUPPORTED仍是`cs-preinline-cost.test`（assertions=No不满足requires asserts），XFAIL仍是`invalid-perfscript.test`；没有FAIL、XPASS、UNRESOLVED或TIMEOUT。补丁2的8个测试与本补丁5个测试全部PASS；首轮5个新文件含70次profgen正/负调用（不把调用数当测试文件数）。[原始日志](evidence/05/04_lit.log)、[xunit](evidence/05/04_lit.xml)、[逐项分类](evidence/05/04_lit_summary.json)。

C1固定比对：127原命令+508格式变体+1纯IP负对照，**636条/遍，两遍一致，与既有清单0差异**；原50个测试相对f999未改，13个IP测试均列为未纳入C1。清单未覆盖。[日志](evidence/05/05_c1.log)、[摘要](evidence/05/05_c1_summary.json)。

### 4.1 generation修正后的最终验收

generation修正后的第二轮仍使用同一配置、root、worktree及资源参数，未改spec、未清理build目录。因用户批准语义修正而重新构建，不是失败重试。

```text
START 2026-11-02T18:15:40+08:00
BUILD_START 2026-11-02T18:15:40+08:00
END 2026-11-02T18:31:17+08:00
GBS_EXIT 0
ELAPSED_SECONDS 936.802
NINJA_TOTAL_OBSERVED 105
ALL-END 2026-11-02T18:31:17+08:00 OK
```

**最终936.802秒（15分36.802秒）、Ninja105步**；两轮构建计时合计 **2,013.349秒（33分33.349秒）**，均成功，未发生FAIL重试。[最终构建原文](evidence/05/10_final_build.txt)、[资源汇总](evidence/05/10_final_build_summary.json)。完整worker/status/log保留 `temp/profgen-patch3/generation-fix/`。

最终工具SHA：`745d9994dc94394a1125836c6196935fbcd8dc3e274b87d4609202f5da4fbcb6`。与14次完整重放及8次身份重验使用的字节一致；源码/测试哈希快照也一致。重新运行GBS clang-format改动行检查退出0。[格式化](evidence/05/10_final_format.txt)、[源码哈希](evidence/05/13_source_hashes.json)。

最终lit **63项：61 PASS、0 FAIL、1 UNSUPPORTED、1 XFAIL**，6.09秒；原50逐项不变，补丁2的8项与补丁3的5项全PASS。新增5个文件现在含75次profgen调用；generation四种要求与反向顺序均通过。FAIL清单为空，不支持及预期失败名称与首轮相同。[lit日志](evidence/05/11_final_lit.log)、[xunit](evidence/05/11_final_lit.xml)、[分类](evidence/05/11_final_lit_summary.json)。

最终C1仍为 **636条/遍、两遍逐字节一致、与既有基线0差异**（127原命令＋508格式变体＋1纯IP负对照）。50个原测试相对f999不变，13个新增IP测试独立列出并排除；基线清单SHA不变，没有覆盖或归一化观测字节。[日志](evidence/05/12_final_c1.log)、[摘要](evidence/05/12_final_c1_summary.json)。

最终轮整机资源采样：used峰值18,531MiB、available最低13,009MiB、1/5/15分钟load峰值12.29/7.43/4.70；开始、约10分钟和结束各采一次。两轮均无available低于2GiB的采样点；这些是整机离散采样值，不声称捕捉全部瞬时峰值。

## 5. 提交边界与后续

提交仅含 `llvm/tools/llvm-profgen/` 与 `llvm/test/tools/llvm-profgen/`。packaging/llvm.spec与02保存的本地diff逐字节相同，未进入提交；**正式非增量构建前必须撤销**。原50测试与C1清单、冻结设计内容均未修改。format-patch --binary为98,108字节，反向应用检查通过；SHA-256为 `23a215600259c5fda345595bf09523aa2ead49f97c4bceea1feac5c63296e53f`。[提交审计](evidence/05/14_commit_audit.txt)。

暂存区空白检查唯一提示为 `ip-identity-list.test:92` 的 `ff `：这是故意保留的“ID后有分隔空白但缺路径”负对照原文；对应C6测试通过，未删掉该语义字节。其他改动无空白错误。所有本轮交付文件小于1MB；构建产物与完整重放输出只保留在temp。

未实现后续计数权重/P_ref/聚合、DWARF行及内联上下文生成、指令边界、质量报告和原子profile输出。身份验证通过不等于profile生成或统计质量通过，过渡错误保留。无开发板操作、无Gerrit推送；无新增已知项目文件边界例外。
