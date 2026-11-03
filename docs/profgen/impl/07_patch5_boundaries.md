# 补丁 5：按需指令边界、avg、补零与 skid（含此前停止记录）

## 2026-11-03 恢复初期记录：按用户裁决修复素材（下方续写最终验收）

用户已授权修正素材缺陷，冻结规则与 golden 不变。补丁4 `aef395b32e27d5f63468c5d49f76f43508dbf270` 保持原提交，没有重做其验收；补丁5仍是未提交的工作树改动。

三份原始 `.s` 及 `boundary-extra/` 对应副本均改为 `.inst 0xd503201f`（小端字节 `1f 20 03 d5`）与 `.inst 0xd65f03c0`（`c0 03 5f d6`），删除手写 `$x`，由汇编器产生一个合法的局部 NOTYPE `$x`。编译/链接遵循补丁1命令与原有平台工具，完整命令、输出、退出码见 [生成与核对](evidence/07/15_fixture_repair_commands.json)。使用 RPi5 SPIKE GBS root 的 emul loader、clang/LLD/llvm-objcopy 22.1.8、GNU readelf 2.43：[版本与绝对路径](evidence/07/18_fixture_tool_versions.json)。未使用主机工具链。

| ELF（每行包含原始与 boundary-extra 副本） | 修正前/后 .text SHA-256（两次相同） | DWARF 区间 | 可执行节映射 |
|---|---|---|---|
| pure-a64.perfbin | `b3f6ed2e7b427c480736e26eaa0aa0f034d7bffcc009530a7a3a56ff851544e4` | [0x1000, 0x1008)，前后相同 | .text 0x1000 只有 $x，无 $d |
| bad-a64-start.perfbin | `b3f6ed2e7b427c480736e26eaa0aa0f034d7bffcc009530a7a3a56ff851544e4` | [0x1002, 0x1008)，前后相同 | .text 0x1000 只有 $x，无 $d |
| bad-a64-end.perfbin | `b3f6ed2e7b427c480736e26eaa0aa0f034d7bffcc009530a7a3a56ff851544e4` | [0x1000, 0x1006)，前后相同 | .text 0x1000 只有 $x，无 $d |

六份 ELF 均用 GBS `llvm-objcopy -O binary --only-section=.text` 提取旧/新代码再比 SHA；`readelf --debug-dump=Ranges` 输出逐字节相同。代码外的调试节 `$d` 不作为可执行映射处理。[逐项证明](evidence/07/14_fixture_repair_proof.json)。修正前原始文件、导出字节与全部命令留在 `temp/profgen-patch5/resume/`；`before/` 保存本轮前的六份源码和六份 ELF。

`boundary-golden.json` SHA 仍为 `3ea33f704b33d36ea0370e67a277cb25039870bd4440d72a10dd5c52f5790971`；原始及 boundary-extra 的 `bad-conflict.s/.perfbin` 四份文件均逐字节未变。补丁1提交未修改。

扫描覆盖 Inputs/ip-mode/ 下全部 **70** 份 ARM/AArch64 ELF（包含补丁1、补丁4 counting-extra、补丁5 boundary-extra）；另按 ELF magic 扫描确认无漏掉的其他后缀 ELF。按冻结规则只把可执行节内的局部 STT_NOTYPE 映射符号计入状态。同址冲突的修正前完整清单：

| 文件 | 可执行节/地址 | 符号 | 处理 |
|---|---|---|---|
| pure-a64.perfbin | .text / 0x1000 | $x, $d | 修复 |
| bad-a64-start.perfbin | .text / 0x1000 | $x, $d | 修复 |
| bad-a64-end.perfbin | .text / 0x1000 | $x, $d | 修复 |
| boundary-extra/pure-a64.perfbin | .text / 0x1000 | $x, $d | 修复 |
| boundary-extra/bad-a64-start.perfbin | .text / 0x1000 | $x, $d | 修复 |
| boundary-extra/bad-a64-end.perfbin | .text / 0x1000 | $x, $d | 修复 |
| bad-conflict.perfbin | .text / 0x1000 | $t, $a | 专门负对照，保留 |
| boundary-extra/bad-conflict.perfbin | .text / 0x1000 | $t, $a | 专门负对照，保留 |

其余文件无合法映射状态同址冲突，不需要修改仅用于地址换算/计数的素材。70份逐文件架构、大小、SHA、映射数量和冲突见 [修正前清单](evidence/07/16_fixture_inventory_before.json)、[修正后清单](evidence/07/17_fixture_inventory_after.json)。原始 readelf 全输出在 `temp/profgen-patch5/resume/inventory-{before,after}-commands.json`。

用停止时已有的开发工具（未重编、非正式GBS验收工具）重跑四条探针：pure-a64成功并枚举0x1000/0x1004；bad-a64-start/end分别到达起点/末端错误；bad-conflict仍报同址冲突。[原始输出/退出码](evidence/07/19_repaired_dev_probes.json)。这些探针不能替代完整lit、C1、GBS验收。

**当时状态（现已解决）：** 原补丁5完整prompt当时不在可用会话或工作目录中，已请求补发以核对完整测试矩阵、接口和验收要求；本轮明确授权的素材修复与核对已完成。完整测试矩阵、avg/补零/skid/head、objdump、08真实20函数、RSS/耗时、GBS、lit、C1、整份导出重放及提交/0005导出均未宣称完成。以下保留2026-11-02停止时的记录；其中“待裁决”指当时状态，已由本轮裁决解决。

---

2026-11-02。**补丁4小修已验收并amend；补丁5未完成、未提交、未导出正式补丁，也未执行补丁5的GBS验收构建。** 按本任务“发现某条规则无法按原文实现或测试，停下报告”的停止条件，发现既有A64素材与强制golden矛盾后停止。不是把草稿开发编译或少量探针当作完整验收。

## 1. 停止原因与待 PM 裁决

冻结设计SHA仍为 `eec6b208d8e1fedb840f0933eb20a37c188890b6c8c29e43986c5c9bbca9f6be`，正文及原始 `boundary-golden.json` 未改。[冻结预期与哈希](evidence/07/02_frozen_test_conflict.json)

三份**原始补丁1**素材 `pure-a64.perfbin`、`bad-a64-start.perfbin`、`bad-a64-end.perfbin`，均有：

```text
Value             Type    Bind   Ndx  Name
0000000000001000  NOTYPE  LOCAL    1   $x
0000000000001000  NOTYPE  LOCAL    1   $d
```

Ndx=1是可执行的 `.text`，两个符号都在节内，属性均符合5.7.2第2条。因此必须按第3/6条判为同址状态冲突。`pure-a64` 的golden却要求通过并输出 `0x1000,0x1004`；另外两项要求分别覆盖起点不对齐、末端截断，实际首先遇到同址冲突，不能提供所要求的独立负对照覆盖。[GBS GNU readelf原始命令/输出/退出码、源文件逐行文本](evidence/07/01_a64_mapping_conflict.txt)

源文件手写 `$x` 后用 `.byte` 写A64代码。`llvm/lib/Target/AArch64/MCTargetDesc/AArch64ELFStreamer.cpp:375–389` 的 `emitBytes` / `emitValueImpl` 均调用 `emitDataMappingSymbol()`；`:405–409` 发出 `$d`。[源码摘录](evidence/07/03_a64_streamer_source.txt) 这解释了素材生成阶段出现冲突的原因，不是新版工具添加了符号。

补丁1手写素材另缺行表，无法直接成为“有可用样本”的输入。为测试按需门控，草稿在 `Inputs/ip-mode/boundary-extra/` 添加了有行表的副本，只增加 `DW_AT_stmt_list`、`DW_AT_decl_line=1` 与字节粒度行表；保留原代码字节、映射符号和函数区间。该副本的 `bad-a64-start` 开发探针确实返回1，原文为：

```text
llvm-profgen: error: IP sample mode: failure_stage=boundary
  bad-a64-start: conflicting mapping states in section .text
```

[探针stdout](evidence/07/13_blocking_probe.stdout.txt)、[stderr](evidence/07/13_blocking_probe.stderr.txt)。不能通过忽略 `$d`、优先 `$x`、放宽属性识别，或偷偷改golden来获得PASS。未继续执行剩余测试或真实FFmpeg验收。

**待裁决的建议（未实施）：** 允许在补丁5中修正上述三份A64汇编素材，使用 `.inst` 表达同一代码字节并重新生成，使 `.text` 起点不再有冲突的 `$d`；保留既有函数区间和golden数值，保留单独 `bad-conflict` 负对照。随后从此处恢复完整验收。该建议修正测试输入，不要求改变冻结边界规则；本次没有自行选择或执行。

## 2. 补丁4修正与提交

- 原提交：`de8171b77cec5e547c8ffc2f7a5039a8b39b8577`。
- 初次amend：`384f915f0c24c6f0de6490bd51637fbc09e5851b`；仅有测试输出清理遗漏，见下文。
- 最终amend：`aef395b32e27d5f63468c5d49f76f43508dbf270`；Hao Lin `<hao.lin@samsung.com>` 为作者与提交者。
- 相对原补丁4：8文件、**+54/-5行**，新增3704字节ELF素材；新增1个lit文件，并修改已有arithmetic测试。
- 整份补丁4：36文件、+1094/-198行。只含 `llvm/tools/llvm-profgen/` 与 `llvm/test/tools/llvm-profgen/`；spec原有本地diff逐字节不变、未提交。已重新导出 [0004补丁](../../../patches/profgen/0004-llvm-profgen-Generate-line-level-profiles-from-IP-sa.patch)。[提交审计](evidence/07/11_commit_audit.json)、[本轮修正diff](evidence/07/10_patch4_fix.diff)

明确拒绝 `--ip-weight=sample` 与显式 `--ip-period-unit` 同用，错误固定为：

```text
IP sample mode: --ip-period-unit has no effect with --ip-weight=sample
```

共享符号化中仅在 `IPMode`、有效帧链、`I>0 && CallerFrame.Line==0` 时登记地址；检测原始非叶子行号，不误用经过减法/截断的LineOffset。生成阶段仅追加诊断子集 `usable_nonleaf_line_zero`，不改变usable/body/total规则。两条内联样本period为3、7，top-only样本100：usable=3/110，子集=2/10；未修改对照素材子集=0/0，两者顶层total都110。[GNU addr2line核对](evidence/07/07_nonleaf_addr2line.txt)

## 3. 构建、lit、C1与失败原文

同00报告第3节的配置/root/宏，后台 `setsid`、nice19、ionice3、jobs10，spec编译池6/链接池2保持不变；每600秒free/uptime，起止也采集。真实结束记录：

```text
BUILD_START 2026-11-02T22:30:41+08:00
END 2026-11-02T22:48:17+08:00
GBS_EXIT 0
ELAPSED_SECONDS 1056.634
NINJA_TOTAL_OBSERVED 105
ALL-END 2026-11-02T22:48:17+08:00 OK
```

完整日志留 `temp/profgen-patch5/patch4-fix/build.log`，其SHA、行数、尾100行及资源采样在 [构建证据](evidence/07/08_patch4_build.txt)。最终GBS工具SHA-256：`d4274ef2c250f1a890153784f75f0049f5ff71f08d89c0709a83a9bacd322aee`。

| 验证 | PASS | FAIL | UNSUPPORTED | XFAIL | 说明 |
|---|---:|---:|---:|---:|---|
| GBS内首次lit | 68 | 1 | 1 | 1 | arithmetic末尾“文件不存在”断言碰到前轮旧输出 |
| 同一GBS工具、修正测试后全套lit | 69 | 0 | 1 | 1 | 71项；原50逐项与02相同 |

首次新错误文本的FileCheck已通过，但旧正向用例留下 `sample-explicit`，导致最后 `test ! -e` 失败。修正为在负对照前 `rm -f %t/sample-explicit`，只清理该测试自身输出，不改工具或放宽断言；随后amend。失败日志和XML完整保留：[首次log](evidence/07/04_patch4_initial_lit.log)、[首次XML](evidence/07/04_patch4_initial_lit.xml)。

复测在工作区独立lit执行目录进行，使用GBS loader、同一GBS二进制/libLLVM，重定位site路径与工具wrapper；未重编C++，不是第二次GBS构建。宿主Python执行源码树内lit；原50的assertions/target要求保持相同且逐项对照。lit启动探测wrapper文件格式时有一条readobj提示（wrapper不是ELF），未改变测试结果或新增跳过项，原文保留：[复测log](evidence/07/05_patch4_retest_lit.log)、[XML](evidence/07/05_patch4_retest_lit.xml)。

C1每遍636项、两遍一致、相对既有基线**0差异**，71项中的新增IP测试正确排除：[C1摘要](evidence/07/09_patch4_c1_summary.json)、[C1日志](evidence/07/09_patch4_c1.log)。这些检查通过后才开始补丁5。补丁4改动C++行已用GBS clang-format处理及dry-run检查：[命令/退出码](evidence/07/06_patch4_format.txt)。

## 4. 补丁5草稿范围与未完成项

草稿留在 `temp/llvm-profgen-enh`，没有LLVM提交、没有 `0005-*.patch`。新增 `IPBoundary.h/.cpp`、CMake登记；ProfiledBinary只增加debug路径getter；ProfileGenerator/CLI增加按需调用、avg/补零/skid与诊断。共享LBR反汇编未改，但**未完成补丁5的C1验证，不声称LBR验收通过**。[工作树文件/哈希清单](evidence/07/12_patch5_wip_manifest.json)，跟踪文件diff另留 `temp/profgen-patch5/patch5-wip-tracked.diff`。

| 冻结条款 | 草稿状态 | 验收状态 |
|---|---|---|
| 5.7.2.1 按需范围 | 先收集有可用样本的函数；三项功能任一启用才加载边界 | 未全验收 |
| 5.7.2.2–3 映射属性、按节隔离、两文件对应、冲突 | 独立边界模块；按节名+范围对应；冲突失败 | A64既有素材矛盾，停止点 |
| 5.7.2.4 ISA区间/锚点/前缀/末端 | Thumb顺序步进；A32/A64定长；字节来自runtime | 少量开发探针，未完成golden矩阵 |
| 5.7.2.5 MC交叉核对、.8 全部逐地址验收 | 尚未进行 | 未验收 |
| 5.7.2.6 全函数失败汇总 | 草稿在计数前汇总失败；不降级 | 未全验收 |
| 5.7.2.7 样本/符号地址 | 不对样本清Thumb位 | 未全验收 |
| 5.4.4 avg | 草稿checked乘加、按指令符号化计n(k)、最后除法 | 手算矩阵、溢出、展开/多区间未完成 |
| 5.4.7 补零 | 草稿只遍历有样本的顶层函数 | head零兜底未验证，挂账不关闭 |
| 5.4.8 skid | 草稿按已枚举布局前驱、同区间且连续，否则unadjusted | 16/32位/数据/跨函数矩阵未完成 |

按本次PM澄清登记：启用按需功能时，可用样本若不在枚举指令起点，整次 `failure_stage=boundary`；不得用清位或就近取整掩盖不一致。新增隐藏测试接口草稿 `--show-ip-boundaries`（只在 `--ip-samples` 下准入）输出函数、DWARF区间、ISA交集、锚点和全部起点。`--show-ip-address-counts`草稿追加枚举函数数、来源文件、失败列表、`skid_unadjusted`。这两个新增部分尚未完成格式/确定性验收。

开发性定向编译使用GBS root内clang/loader/sysroot，输出仅在 `temp/profgen-patch5/dev/`，未替换GBS正式产物。首次缺CheckedArithmetic头文件的编译错误保留在 `devbuild-initial-failure.log`，补头文件后定向编译/链接通过；**这不等于完整GBS增量或补丁5验收**。未继续格式化、提交或导出草稿。

真实FFmpeg最大20函数、132859起点对照、热点函数avg+补零、objdump脚本、运行耗时/RSS均**未执行**，不存在可报告的测量数字。补丁5的完整导出地址重放、全lit、C1、GBS构建也未执行，不能沿用补丁4的结果冒充。

## 5. 后续事项与边界

先由PM决定如何修正上述A64测试素材，然后恢复补丁5全部验收。未完成前保留head兜底挂账；补丁6的报告/门槛与补丁7的完善仍待后续任务。新增挂账：“IP 新选项改为枚举类型与 cl::values，补丁 7 处理”、“非叶子帧行号为 0 的处理，上板后按实测数据决定”。

未连接任何开发板，未推送LLVM远端或Gerrit；spec未改动/提交，设计未改动。结果仓库原有未跟踪config及gbs配置保留。工具导入时曾在 `tools/profgen/__pycache__/` 生成一个Python缓存（仍在WORKDIR内），封存时已移至temp并移除空目录；后续设置PYTHONDONTWRITEBYTECODE=1。未观察到新增工作区外项目文件写入，本次未做全系统syscall审计。


---

## 补丁5实现与独立判据（本轮续写）

前缀 `T/` 表示 `llvm/tools/llvm-profgen/`。`IPBoundary.h/.cpp` 是IP专用边界元数据与长度规则实现，CMake只增加该源文件；不调用LBR反汇编器，不修改共享解码器或LLVM库。

共享代码改动穷举：`ProfileGenerator.h`加入IP选项/诊断结构及边界声明，`.cpp`只扩展IP专用 `populateBodySamplesFromAddresses` 和诊断打印；`ProfiledBinary.h:428`增加只读debug路径getter，不改变加载流程；`llvm-profgen.cpp`定义隐藏IP诊断选项、去掉三个枚举值的过渡拒绝，在IP入口填选项并打印结果，非IP使用该选项仍拒绝。所有新增错误沿Error/Expected返回main，LBR生成、反汇编和writer逻辑不改。

| 规则 | 实现（本地 LLVM 树文件:行号） | 测试/独立判据 |
|---|---|---|
| 5.7.2.1 按需、有可用样本函数 | `T/ProfileGenerator.cpp:274,292`，`T/ProfileGenerator.h:163` | negative：无映射时sum/max成功且枚举0，任一按需功能失败；avg-counting只写count_loop |
| 5.7.2.2 映射名字、属性与两个来源 | `T/IPBoundary.cpp:25,34,68` | positive含$t.1/$t.hot/$d.literal；metadata的全局$x不作为映射；split从debug读取映射 |
| 5.7.2.3 按节、最近状态、对应失败 | `T/IPBoundary.cpp:86,120` | before_state/at_state/section-adjacent；metadata改debug节名、缺初始状态；独立C++ section-same-address单元 |
| 5.7.2.4 交集、ISA长度、锚点、数据和末端 | `T/IPBoundary.cpp:120` | positive按原golden精确比较整个起点向量；negative起止切入；literal的数据虽然可解码也排除 |
| 5.7.2.5 MC只作交叉核对 | 核心代码不依赖MC；项目`tools/profgen/check_ip_fixture_objdump.py` | 平台objdump使用thumbv7a/armv7a/aarch64，记录属性，Thumb无attributes固定v7a+neon+vfp3 |
| 5.7.2.6 整次失败及全部原因 | `T/ProfileGenerator.cpp:300–325` | metadata同时报告count_loop/main失败；输出新文件不创建、旧文件不变；无降级 |
| 5.7.2.7 不处理样本bit0 | `T/IPBoundary.cpp:199`；`T/ProfileGenerator.cpp:310` | negative的0x1001样本必须失败，0x1004切入MOV.W同样失败；符号元数据不用于推断指令长度 |
| 5.7.2.8 两种独立参照 | golden来自原JSON；objdump由项目脚本调用 | 手写bytes/.inst是人工参照，objdump仅交叉验证；08真实构建单列范围差异 |
| 5.4.4 avg | `T/ProfileGenerator.cpp:366,383,433` | avg-counting三ISA完整base discriminator键；avg-manual不连续区间/未采样指令/分母溢出 |
| 5.4.7 sampled-functions | `T/ProfileGenerator.cpp:383,416` | zero十个手算键，不加入$d；avg-counting无样本顶层函数不出现；total不变 |
| 5.4.6 head零估计 | 既有库函数不变，IP在body补零后调用 | zero：首键0、后键50，total50/head1；不使用total代替入口 |
| 5.4.8 prev-inst | `T/IPBoundary.cpp:206`，`T/ProfileGenerator.cpp:334` | skid：16/32/IT前驱、首指令、数据屏障、跨区间/跨函数、原始period |

**单独登记的澄清：** 启用avg/补零/skid时，可用样本不是枚举指令起点，整次 `failure_stage=boundary`。不清Thumb位、不就近取整；负对照覆盖奇数PC、32位指令中间与可解码数据。

**隐藏测试接口：** `--show-ip-boundaries` 只在IP模式有效，打印固定前缀`IP-BOUNDARY`的函数、区间、交集/ISA/锚点、全部起点及大小/区间索引。它不单独开启枚举；sum/max且三项按需功能均关闭时不枚举。`--show-ip-address-counts`追加`IP-GENERATION`的枚举数、来源、失败函数与skid_unadjusted。均非冻结用户选项表的新增条目，仅登记测试接口。

### 手算golden

- `boundaries`：相对0x1000的起点为0,2,6,8,10,18,24,28,32,34；[14,18)、[22,24)是数据。Thumb顺序长度2,4,2,2,4；状态切换后4；A32两条4；末尾Thumb两条2。TBB/TBH表可解码也不计入。
- before_state的DWARF区间[2,10)从锚点0证明后仅输出2,6,8；at_state=[18,22)只18；discontinuous=[2,6)∪[34,36)只2,34；after_data_a32=[24,32)只24,28。证明前缀不加n(k)或补零键。
- pure-arm/pure-a64只有0x1000、0x1004；arm-literal同样两个起点，0x1008的数据不算；section-adjacent只有0x1004、0x1006，不继承前一节$d。该素材的可执行PT_LOAD是offset0x2000/vaddr0x1000，因此样本off=VA+0x1000。
- section-same-address仅在独立C++单元中调用边界API：同为[0x1000,0x1004)，指定.text得到0x1000、0x1002；指定.plt得到$d且没有指令；不指定节拒绝歧义。未将它作为唯一PT_LOAD端到端正例。
- 三ISA count_loop：8条样本u=(2,6)×4，Σu=32、DF4；max24，sum32。GNU objdump+addr2line核对完整键(行12−decl9=3, base2)有15条指令：12条raw discriminator1028和3条raw4，共同base2。7条未采样位置也加入分母。avg分子32×4=128、分母15，半入为9；total仍32。等效N=8、c̄=(4×(1+3)+7×0)/15=16/15，N·c̄=128/15。不是只数8个采样地址，也不是只数12个raw1028地址。早期开发检查误漏raw4，已由独立核对纠正，未更改冻结算法。
- arm-uniform：2条同键指令只采首条u10，n=2，avg5、total10。discontinuous-uniform：两个不连续区间各1条指令，同键n=2，结果同上。P_ref=UINT64_MAX时n×P_ref溢出，必须报错。
- zero：whole_mixed的10个键对应上述10个起点偏移；只在偏移6采u50、P_ref1。补零前body只有6:50；补零后其他9键0，total仍50；最早body=0使entry-estimate走库函数至少1兜底，head=1而非50。
- skid：0x1002→0x1000、0x1006→0x1002、0x1008→0x1006；0x1000、数据后的0x1012/0x1018、before_state首条0x1002、discontinuous第二区间0x1022、section-adjacent首条0x1004均不调整。a64-pie main入口前方属于two_sites，也不调整。单样本period7的P_ref仍7，归一化body1，未调整桶samples1/period_sum7。
- split：同一混合素材strip-all运行文件+NOBITS调试文件与拆分前profile字节一致；每次按需枚举都从runtime读代码。text/binary/extbinary各两遍profile及全部诊断逐字节一致。

## 最终验收（2026-11-03）

本轮补丁4保持 `aef395b32e27d5f63468c5d49f76f43508dbf270`，只提交补丁5。用户补发完整任务后恢复测试与正式构建。冻结设计、原始golden和C1基线均未修改。此前“未完成/待裁决”段落为保留的停止记录，不代表本节最终状态。

### 素材、格式与节分组

最终扫描仍为70份ARM/A64 ELF，同址异状态冲突仅两份刻意保留的bad-conflict。[最终逐文件清单](evidence/07/20_fixture_inventory_final.json)。新增草稿a64-no-map也改用`.inst`后将唯一$x全局化，确保没有合法局部映射符号；它不是补丁1的历史文件。生成命令在`temp/profgen-patch5/resume/no-map-commands.json`，可复现步骤写入新增`boundary-extra/README.txt`。三份原始素材与对应副本的六份修复证明仍见14证据；非代码调试节映射不影响结论。

GBS clang-format 22.1.8对新增文件及现有文件改动行执行，dry-run均退出0；文件头为LLVM单行格式。[命令](evidence/07/21_clang_format.json)。仅文档README在正式构建后补足生成路径说明，工具源码与测试命令未变。

同址不同节的单元核对链接正式GBS产生的`build/tools/llvm-profgen/CMakeFiles/llvm-profgen.dir/IPBoundary.cpp.o`，`.text`得两个Thumb起点，`.plt`纯数据为空，未指定节返回歧义错误；退出0。该独立C++单元不是端到端lit，不将两个重叠PT_LOAD解释成唯一地址映射。[源码、完整命令和输出](evidence/07/25_section_unit.txt)

### 构建、lit、C1与完整导出

同00第3节的worktree/config/buildroot执行GBS incremental；没有改spec编译参数，`packaging/llvm.spec`测试用本地diff逐字节保留、未提交。worker整段setsid，nice19/ionice3、threads1、make/mlgo jobs10；检测到其他GBS导出后先等待600秒。真实记录：

```text
START 2026-11-03T13:35:14+08:00
BUILD_START 2026-11-03T13:45:14+08:00
END 2026-11-03T14:14:55+08:00
GBS_EXIT 0
ELAPSED_SECONDS 2380.498
NINJA_TOTAL_OBSERVED 108
ALL-END 2026-11-03T14:14:55+08:00 OK
```

总worker耗时2380.498秒含等待；实际GBS约1781秒（29分41秒，按秒级时间戳），Ninja108步，一轮成功。每10分钟free/uptime：available最低9656MiB，used最高21884MiB；load平均值采样峰值1/5/15分钟分别14.45/8.20/5.91，无低于2GiB的采样点。这是离散采样峰值，非全程峰值。[构建结束/日志尾部/资源](evidence/07/22_patch5_build.txt)。完整日志`temp/profgen-patch5/build/build.log`。

新工具SHA-256：`05ddac1c680fd34e21b4c2bfc424c792d2d1a1155fbed2e4d754e39242f4bfb6`。

| 验收 | 结果 | 证据 |
|---|---|---|
| 正式GBS %check lit | 79项：77 PASS、0 FAIL、1 UNSUPPORTED、1 XFAIL；原有50逐项不变；新增8项全部PASS | [原始日志](evidence/07/23_patch5_lit.log)、[xunit](evidence/07/23_patch5_lit.xml)、[逐项结果](evidence/07/23_patch5_lit_summary.json) |
| 不支持/预期失败 | cs-preinline-cost requires asserts，当前assertions=No；invalid-perfscript原有XFAIL；没有新增跳过 | 同上 |
| C1 | 原127命令＋508格式变体＋1纯IP负对照，每遍636，两遍一致、原清单0差异；29个新增IP测试单独排除 | [摘要](evidence/07/24_patch5_c1_summary.json) |
| 完整真实导出重放 | 14次目标运行，地址与reader计数输出逐字节等于补丁2，仅剔除后增的IP-IDENTITY/IP-GENERATION诊断 | [逐份结果](evidence/07/29_full_export_comparison.json) |

完整重放中05/09的strip libavcodec依旧因usable=0不生成profile；这与补丁4一致，不代表读取器拒绝导出。05单/双目标6496/13289、09单/双5865/14331均保持原数。06完整loss1未保留的历史限制继续挂账，不声称重放了该缺失文件。首次post辅助脚本错误地按“stderr只有一行”判FAIL，实际上还有原有DWARF警告前缀；保留原始失败状态，修正验收判据后对已有输出逐字节复核，工具与输出未修改。[诊断记录](evidence/07/31_measurement_and_harness_notes.txt)

### 素材与08真实构建的边界交叉核对

`tools/profgen/check_ip_fixture_objdump.py`覆盖13份Thumb/A32/A64素材，共182个起点，与平台objdump逐条一致。[逐素材结果](evidence/07/26_fixture_objdump.json)。avg手算使用GNU objdump/addr2line给出的完整base discriminator键；独立结果在[手算辅助证据](evidence/07/30_avg_independent_oracle.json)。手写golden并未从补丁5输出反抄。

08运行/调试文件均为build-id `f960461f63c852474257f51267b7b543afffdc9c`，由GBS eu-unstrip合成代码与符号供objdump使用。最大的20个Thumb符号范围内，**132859/132859**个起点匹配，与07报告的计数相同。按profgen现有DWARF函数名归组后，实际枚举**137117/137117**个起点，仍全部匹配。多出的4258不属于边界不一致：`decode_frame`多143，`iadst_iadst_16x16_add_c`多4115，来自现有`ProfiledBinary.cpp:1017–1032`按名字合并的其他DWARF范围；逐函数、逐范围、额外地址均留证。不能把两个统计范围混写成一个数字。[完整20函数结果及命令](evidence/07/27_real20_boundaries.json)

该20函数avg边界运行（不补零）工具墙钟0.360767秒、峰值RSS90508KiB，含诊断输出；PC由objdump先选定，样本由08自身ELF推导，不复用旧镜像地址。全量objdump与诊断留`temp/profgen-patch5/real-rusage/`，测量脚本为`tools/profgen/check_ip_boundaries.py`。

### 合成负载规模测量

**本节不是实际采样证据，也不验证avg数值正确性。** avg数值正确性由lit手算期望保证。按用户补充裁决做两档，每个可执行函数范围只给一条样本；PC来自独立objdump指令起点，MMAP2使用08自身的build-id。没有使用补丁5的边界输出反选样本，也没有使用旧镜像采样地址。

| 输入档 | 输入/usable样本 | 参与补零函数 | 枚举起点 | profile body条目（其中0） | 顶层/inline节点 | 工具墙钟 | 峰值RSS |
|---|---|---|---|---|---|---|---|
| 最大20个Thumb函数 | 20/20 | 20 | 137117 | 18497（18477） | 20/2285 | 0.398628秒 | 96000KiB |
| 所有可执行函数范围 | 5594/4598 | 4090 | 1041309 | 126599（122509） | 4090/20487 | 2.571665秒 | 306612KiB |

两份文本profile总行数20802/151176；body条目按每层FunctionSamples的行/判别符键统计，不能与指令数相加。原始可执行STT_FUNC有5614项，去重同范围别名20项，5594范围均找到objdump指令起点。零size符号按同节下一不同函数起点或节尾界定，与07取法一致。所有可执行函数档中，965样本in_cu_no_subprogram、31样本no_cu被冻结usable规则排除；其余4598个样本按现有函数名归组为4090个函数。因此这一档覆盖了全部可执行符号输入，**不能声称输出对每个.text字节都补零**；没有为996个缺DWARF函数强造行信息。

使用新鲜轻量启动进程的直接子进程wait4取rusage，避免主Python预解析大objdump产生的继承RSS影响；最初scale-final的20函数RSS出现该测量底值，保留原记录，改测量包装后重测，profile字节完全相同。不是改变工具算法后的性能对比。单次热缓存测量、不随机交错，只作规模观测。[两档计数、时间、RSS、警告及完整命令](evidence/07/28_synthetic_zero_scale.json)

复现脚本：`tools/profgen/measure_ip_zero_scale.py`；大文件/逐输入函数清单/合成perf文本/合并ELF/profile在`temp/profgen-patch5/scale-rusage/`。少量样本导致的既有“增加采样”警告原样记录，不能用合成每函数一次来推断真实优化收益。

### 留给后续与边界说明

- head零估计挂账已关闭：`ip-boundary-zero.test`验证total50、最早body0、head1。
- 补丁6：质量/完整报告、诊断与兜底回调等设计剩余内容；本补丁只提供既定诊断接口与严格失败。
- 补丁7：IP新选项改为枚举类型与cl::values、最终整理验收；非叶子帧line0处理仍在上板后按实测决定。
- **avg在真实数据上的核对留到上板联调**：须用08产物重新采集，不套用旧镜像地址或本节合成结果。
- A64素材缺陷已按授权修复，冻结规则与golden未变；未发现仍需改变冻结规则才能完成的本补丁事项。没有连接板子、没有推LLVM远端/Gerrit、没有改认证或请求密码；无新增已知边界例外。

## 提交与交付

LLVM本地补丁5：`d7bd4795c7fddfc239510b96fa6803b56b94dbb4`，父提交为补丁4 `aef395b32e27d5f63468c5d49f76f43508dbf270`。共64文件、+3298/-40行，8个新增lit文件；作者与提交者Hao Lin `<hao.lin@samsung.com>`。二进制素材保持普通文件0644，不引入可执行位变更。只提交工具/测试目录；spec未提交且diff不变；未推LLVM任何远端。

[0005二进制补丁](../../../patches/profgen/0005-llvm-profgen-Enumerate-instruction-boundaries-on-dem.patch) 149290字节；独立临时index反向应用检查通过。[提交范围、完整stat和哈希审计](evidence/07/33_patch5_commit_audit.json)。结果仓库同时提交三份交叉核对/规模脚本、报告、证据及STATUS，单文件均小于1MB。
