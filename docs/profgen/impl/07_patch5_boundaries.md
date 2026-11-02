# 补丁 4 小修验收与补丁 5 边界枚举：因素材冲突停止

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
