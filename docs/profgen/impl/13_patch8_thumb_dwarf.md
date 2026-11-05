# 补丁 8：GNU AS Thumb 子程序的 DWARF 地址与同指令别名查询

本轮依据 PM 2026-11-05 裁决实现，不修改冻结设计 v0.7 正文、不清样本 PC、不连接 LLVM/Gerrit 远端。LLVM 基线为补丁 7 `e4642a8ad9e0acb990b45ade3ef7aca755cd80f2`；原正式工具 SHA-256 `334a09290f53eb4c793ae91759f2b6344a36e63317820eb9151771b262dc3f30` 已核对并另存 `temp/profgen-patch8/baseline-llvm-profgen`。

## 1. 授权规则与实现范围

仅 IP、ELF32 小端 EM_ARM：DWARF 子程序区间下界为奇数，且清 bit0 后在可执行节的 `$t` 区间，才对两端清 bit0。函数加载处统一处理，因此归类与按需边界共享相同区间。偶数下界、A32/数据状态、不明确或冲突映射不凭空推断 Thumb；样本 PC 原样保留。非 IP 路径不加载这份映射元数据。

`IPBoundaryMap` 增加仅元数据模式（不读取指令字节、不枚举指令），供函数加载时查询映射状态；原 avg/补零/skid 仍按需读取运行文件字节与枚举。映射按节名与地址范围对应，局部 STT_NOTYPE 映射符号规则沿用补丁 5。

质量报告 schema_version 仍为 1，新增 `thumb_dwarf_normalization`：全部加载的规范化区间数与按函数名、原始起止地址排序的前 50 项；地址是 ELF VA 字节、半开区间。尚未加载/生成写 unknown；确认未发生为 0 与空数组。告警 `W_THUMB_DWARF_ADDRESS_NORMALIZED` 仅在实际发生规范化时出现。文档在原 llvm-profgen.rst schema 中同步登记。

## 2. GNU AS 原生素材与负对照

GBS armv7l root 的 GNU AS 2.43 `as -g`，GNU ld `--build-id=sha1 -Ttext=0x1000`：三条源指令为 movs（2 字节）、add.w（4 字节）、bx（2 字节），人工起点 0x1000/0x1002/0x1006。GNU readelf 实际 CU 范围 [0x1000,0x1008)，子程序 [0x1001,0x1009)；GNU objdump 与源指令边界一致。此原生差异无需手写 DWARF 伪造。

三份派生负对照明确标为合成元数据：映射 `$t` 分别重命名 `$a`/`$d`；另把子程序 low_pc 改为 0x1005，清位为 0x1004，位于 add.w 中间。生成过程、GBS 工具路径、readelf/dwarfdump/objdump 原文暂存 `temp/profgen-patch8/fixture-generation-final.json`。素材源码、二进制与生成说明位于 LLVM `Inputs/ip-mode/gnu-thumb/`。

## 3. 验收记录

仅完成开发编译及首组失败复现；未通过 GBS、正式 lit、C1、完整导出与新工具验收。已有 `packaging/llvm.spec` 本地测试改动不提交。边界 golden 与冻结设计正文不改。

## 待设计 v0.8 登记

本补丁的有证据约束的 Thumb DWARF 区间规范化，是 PM 对冻结 5.7.2 的明确修正，应列入下一轮外部评审。仅修改函数区间，不得推广成对任意奇数样本地址清位；归类和边界须统一，且报告规范化事实。

## 4. 停止记录：区间规范化没有同步进入共享符号化器

**补丁 8 未完成，未提交 LLVM commit、未导出 0008。** 新测试在第一组 sum 正例失败，保留预期而未把 golden 改为实测值。正式补丁 7 工具未替换，GBS、正式 lit、C1 两遍与 14 次导出重放均未启动；不能把开发编译成功当作验收通过。

三个真实指令起点各一条合成样本，period 为 10、20、30，P_ref=1，人工期望 total=60，各位置分别 10/20/30。结果：

| 工具 | sum/max | avg | 首地址归类 |
|---|---|---|---|
| 原正式补丁 7 | exit0，total50，仅后两位置 | exit1，奇数 DWARF 起点不能证明边界 | outside_dwarf_func |
| 补丁 8 草稿 | exit0，仍 total50 | exit0，仍 total50；枚举有0x1000/0x1002/0x1006 | in_func_no_line=1，period_sum=10 |

[完整命令、stdout/stderr、profile 与质量 JSON](evidence/13/03_stop_comparison.json)，[新测试失败原文](evidence/13/04_first_test_failure.json)。归类已经使用规范化后的 [0x1000,0x1008)，质量报告也正确记录原 [0x1001,0x1009) 与规范化区间；但首地址的源码位置没有写入 profile。

用 GBS LLVM 库做最小诊断，设置与 profgen 一样的 `UseSymbolTable=false`、LinkageName、非相对地址，直接打印 `symbolizeInlinedCode` 原始返回值：

```text
0x00001000 frames=1
  function=<invalid> line=9 start_line=0
0x00001001 frames=1
  function=gnu_thumb line=9 start_line=0
0x00001002 frames=1
  function=gnu_thumb line=10 start_line=0
0x00001006 frames=1
  function=gnu_thumb line=11 start_line=0
```

[原始 API 查询、平台编译/链接命令与真实退出码](evidence/13/02_raw_symbolizer.json)、[诊断程序](evidence/13/02_raw_symbolizer.cpp)。这份程序只在 temp 构建，不修改 LLVM 库。CLI llvm-symbolizer 默认使用符号表，会覆盖外层函数名，因此其显示 `gnu_thumb` 不能证明 profgen 使用的 DWARF-only 查询成功；最初 CLI 输出和无效 CLI 参数尝试仍在 `temp/profgen-patch8/`，没有把它们当成最终证明。

源码链条（[带行号摘录](evidence/13/05_source_locations.txt)）：

1. `llvm/lib/DebugInfo/DWARF/DWARFUnit.cpp:739` 的 `updateAddressDieMap` 直接把原始 `R.LowPC` 放入共享查询表；`:770` 的 `getSubroutineForAddress` 对0x1000找不到子程序。
2. `llvm/lib/DebugInfo/DWARF/DWARFContext.cpp:1847` 在内联链为空时仍从行表取出文件/行号，返回 function=`<invalid>`、line=9。
3. 草稿 `llvm/tools/llvm-profgen/ProfiledBinary.cpp:1215` 的现有帧转换会在函数名无效时中断，得到空调用链；`ProfileGenerator.cpp:295` 把空链记为 in_func_no_line。
4. 本轮获授权的区间规范化只修改 profgen 自己的函数范围表，没有改变共享 LLVMSymbolizer 内的原始 DWARF 地址查询表。因此它能修复边界起点，却不能补全该首地址的函数身份。

这不是第12报告中已证明的正常编译器 line0；这里原始行表和 API 明确给出正行号9。冻结 5.4.2 第3条将 in_func_no_line 定义为行号0，本例不满足该定义；更不能悄悄清/加样本PC或把首地址从正例中删掉。

### 需要裁决的候选方案（均未实施）

- 优先考虑：在 IP 专属符号化路径中，让 DWARF 子程序身份查询也使用已证明的规范化区间，并保持原始 PC 的行表结果与内联信息。需要明确此项超出当前“函数区间加载处”的修正，评审其对缺名字、StartLine、内联链的边界；不能只改全局 LLVM 库而影响 LBR。
- 更小但需明确限定的方案：仅对“实际规范化区间首地址、单帧正行号、函数名无效”使用同一 DWARF DIE 的名字/声明行补全帧；不使用符号表名，不猜最近行，不改 PC。须明确非 GNU AS/内联情形是否允许，新增测试和报告诊断。
- 若保留不可符号化首地址，则必须单独决定它的分类与质量影响，不能继续叫正常 line0，也不能声称首指令/avg完整验收通过。

尚未选择上述方案。开发草稿保留在 worktree；`temp/profgen-patch8/draft.diff` 与素材生成记录留存。正式工具 SHA、LLVM HEAD、设计/golden SHA、src/llvm 干净状态及原 spec diff见[范围审计](evidence/13/06_stop_scope.json)。开发工具 SHA 为 `813c91fa6b09bffa165dd7e74a47faccf4d8fa417466cfb5fe6ed29f89a74414`，仅用于复现，不用于正式数据转换。

新建 GNU AS 素材共4个 ELF；正例源码/负例生成命令、映射符号与 DWARF 原文见[生成证据](evidence/13/01_gnu_as_fixture.json)。新增 lit 入口1个，但其 helper 第一组失败；其余正负例没有完成验收。首次开发编译的基类访问错误已修正，随后开发链接成功；原始日志 `temp/profgen-patch8/devbuild{,2}.log` 保留。没有运行正式 GBS 或以放宽期望绕过停止条件。


## 5. 最新裁决后的恢复：同一指令别名查询

以上第4节为上一次停止记录，保留不改。PM已授权扩展冻结5.4.2/5.7.2的执行细节，采用同一指令别名查询；不改共享LLVM符号化库，也不从DIE另补函数名。

IP ELF32 little-endian EM_ARM函数加载时，仅遇到奇数low_pc才懒加载映射元数据。在已证明的Thumb区间中规范化两端，同时记N→N+1。符号化缓存仍按原A寻址，只有A恰等于规范化下界N才查询N+1；原查询的叶子文件、行号、discriminator逐项比较，任何一项不同以generate失败，经现有Error/unwrap出口生成失败JSON，旧profile不变。普通PC、计数键、非IP和共享库保持原逻辑。

新报告字段为alias_query_count（实际查询次数，不是样本数）、alias_check_passed、alias_addresses_top50（按原地址排序，含别名地址、比较结果与两次完整帧查询原文）。最多50项，计数不截断；尚未查询为0/空数组。schema_version仍1，文档列出字段和单位。该裁决与区间规范化一并列入下一轮外部评审，冻结v0.7正文不改。

### 素材与开发验收

新增GNU AS相邻函数：原first=[0x1001,0x1005)、second=[0x1005,0x1009)，second首指令0x1004原查询误归first，别名0x1005返回second，叶子line16一致。正例sum/max/avg计数分别为first10、second20，没有伪造内联关系。另造明确标为合成的DWARF2行表，在同一16位指令内0x1000/0x1001分别标line9/10，验证整次generate失败、回调一次、完整失败JSON原子替换、旧profile不变且无临时文件。GNU三指令原例sum/max/avg=60，10/20/30；补零、prev-inst及三个原负例保持要求。[生成命令与原文](evidence/13/08_alias_fixtures.json)、[生成脚本](evidence/13/08_alias_fixtures.py)。

开发全套lit为86项：84 PASS、1 UNSUPPORTED、1 XFAIL、0 FAIL；新增入口1个。已有clang素材生成的153份profile逐字节相同。开发C1两遍各636条，0差异。[开发原文](evidence/13/10_development_lit.txt)、[摘要](evidence/13/10_development_checks.json)。首次开发全套因临时增量驱动未跟踪头文件导致陈旧对象ABI不一致，重编全部profgen翻译单元后消除；随后将映射读取限制为遇到奇数low_pc才触发，保留原错误阶段。首次C1换了scratch目录产生141条stderr路径差异，profile/退出码未变；恢复基线目录后两遍0差异，未覆盖已提交基线。

真实BBB中档libavcodec开发冒烟：33个规范化区间，sum两次别名查询、avg三次，一致性均通过；包括__udivsi3首地址及原误归__divsi3的下一函数__aeabi_idivmod首地址。这是开发检查，不替代正式GBS验收。[原始命令/查询](evidence/13/11_development_real_smoke.json)。

### 待设计 v0.8 登记补充

同指令别名查询仅用于已规范化区间的首地址；叶子位置不一致为generate失败，不得按任一查询继续。缓存/计数键始终为原地址。报告登记范围与查询证据。实现保留先前加载/边界失败阶段，不为偶数DWARF区间提前读取边界元数据。


## 6. 正式验收与提交

- LLVM本地补丁8：`cd5168c48b5422a50829259fd43e84cc3edd6694`；21文件，+492/-23行，6个小型ELF素材，新lit入口1个。只含profgen工具/测试与schema文档；spec本地测试diff与原来完全一致，未进入提交。冻结设计、boundary golden、src/llvm不改。[审计](evidence/13/17_commit_audit.json)
- GBS正式增量：2026-11-05T23:26:34+08:00至2026-11-05T23:39:45+08:00，791秒；113 Ninja步，GBS_EXIT=0、ALL-END OK。此前按资源约束等待其他会话600秒，包装进程总1390.995秒。资源600秒采样原文、日志尾与完整temp位置见[构建证据](evidence/13/12_formal_build.json)。
- 正式%check：86项，84 PASS/0 FAIL/1 UNSUPPORTED/1 XFAIL，原85项逐项与补丁7相同；新测试通过。[日志](evidence/13/13_formal_lit.txt)、[xunit](evidence/13/13_formal_lit.xml)
- C1两遍各636条，0差异、两遍逐字节一致；新测试列为未纳入C1。[清单摘要](evidence/13/14_formal_c1.json)
- 14份完整导出各两遍，profile与补丁7逐字节一致，退出码/诊断两遍确定。每份JSON仅新增thumb_dwarf_normalization，以及本轮独立输出目录造成的两项tool.arguments路径变化；没有现有质量统计变化。[逐份差异与SHA](evidence/13/15_full_replay.json)
- 123份报告共383字段路径，与schema文档双向差集0、空字符串值0。扩大采集到新测试的非report.json文件后，发现旧schema未列出四类skid原因计数对象的20个子字段，本补丁只补文档类型/字段，不改变这些字段的输出。[字段检查](evidence/13/16_schema.json)
- GBS clang-format改动行处理和dry-run通过。[原文](evidence/13/09_format.json)
- 正式新工具SHA-256：`41440292c7cf3a380a6779dfea6d06ff74a22e18537127561829bf989bb16413`。导出[0008补丁](../../../patches/profgen/0008-llvm-profgen-Normalize-GNU-AS-Thumb-DWARF-addresses-in-IP-mode.patch)，`git apply --reverse --check`通过；未推LLVM/Gerrit。

补丁8主机实现阶段闭合。全部正式S重转换、真实avg独立核对和板上恢复另记报告12，不以本节开发冒烟代替其结果。边界例外：无新增。
