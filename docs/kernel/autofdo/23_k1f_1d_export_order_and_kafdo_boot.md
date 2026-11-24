# K1f-1d 导出符号表根因确认与 K-AFDO 首启

终态 **STOP**。K-BASE-S 在 LLD 22.1.8 的最终输入节排序中失去导出表名称顺序。两次重放均复现这一异常。

[证据索引](evidence/23-k1f-1d/index.json) · [所有输出节顺序](evidence/23-k1f-1d/output-order.tsv) · [地址序导出表与 CRC](evidence/23-k1f-1d/export-tables.tar.gz)

## PLAT 恢复与控制台证据

用户断电上电后核对 PLAT build-id `395733b9c917cb98309b39cc3ec379c03ac36b3f`、U-Boot、tryboot=0、原始 cmdline SHA `1a132093c6e7220e981bd54c1a6a7bf780a19927c9787d3c9dcb7149eff106b4`，boot ID `774bae67-67de-4e9b-a286-dae461aa1445`，rsts `0x1000`，root off 后 UID 5001。只读核对诊断前后的清单后，移除任务新增的 `cmdline-diag.txt` 并原子恢复正式 `tryboot.txt`。读回与诊断前 418 项 SHA 全同，原 413 个文件均通过。空闲 1,236,992 B。

用户描述诊断内核到达用户态，首次 modprobe 在 `check_modstruct_version` 触发 BUG，LR 在 bsearch。用户还报告五次 oops、后续 modprobe 自旋和约 63 秒间隔的 RCU stall。消息中的故障描述已逐字保存，SHA-256 `6ea5728907faee4220d6660a8d9dd77e252000d915f4853c1350e218949c64cd`。 [用户描述原文](evidence/23-k1f-1d/user-console-description.txt)

当前消息提供的是上述故障描述。尚未收到完整控制台流或附件。以下静态根因可由归档原件和重放独立核实。

## ELF 逐条核对

直接按 ARM32 ELF 中的地址解码 `struct kernel_symbol` 及 CRC 槽。名称来自字符串指针并以符号表标签复核，CRC 核对同索引标签和归档 `Module.symvers` 中该名称的值。三个归档只有普通与 GPL 两组，未发现 unused 组。表中逆序是相邻名称未严格递增的对数。索引从零计。

| 变体 | 普通组条目 / 逆序 | GPL 组条目 / 逆序 | CRC 槽名称不配对 / CRC 值差异 | module_layout 实际槽 / bsearch |
| --- | --- | --- | --- | --- |
| K-BASE | 6,547 / 0 | 7,166 / 0 | 0 / 0 | 3905 / 3905 |
| K-BASE-S | 6,547 / 3,185 | 7,166 / 3,440 | 0 / 0 | 531 / 未找到 |
| K-AFDO | 6,547 / 0 | 7,166 / 0 | 0 / 0 | 3905 / 3905 |
| 重放 A | 6,547 / 3,185 | 7,166 / 3,440 | 0 / 0 | 531 / 未找到 |
| 重放 B | 6,547 / 3,185 | 7,166 / 3,440 | 0 / 0 | 531 / 未找到 |

普通组 `module_layout` 的表项分别位于 K-BASE `0xc1af97dc`、K-BASE-S `0xc1aef9b4` 和 K-AFDO `0xc1af0df4`。CRC 均为 `0xc8c118b4`。K-BASE-S 的两个 CRC 数组与对应导出数组同序重排，槽位仍配对。按 Linux `__inline_bsearch` 重放，普通和 GPL 两组均返回空。于是 `find_symbol` 在版本比较前失败，`kernel/module/version.c:73` 的 BUG 路径可由产物复现。二分查找轨迹保存在摘要。 [导出表摘要](evidence/23-k1f-1d/export-summary.json)

## 所有链接输出节与两次重放

解析原始 LLD map 的 VMA、Out 和 In 列，使用对象、输入节名、同名出现序号匹配。对比共同输入的相对顺序，新增与消失单独记账。包括未分配的调试输出节，并给出非零输入统计。每个 map 解析出 50 个输出节。

- K-BASE-S 改变共同输入顺序的输出节为 `.rodata`、`.text`、`__kcrctab`、`__kcrctab_gpl`、`__ksymtab`、`__ksymtab_gpl`。
- K-AFDO 改变共同输入顺序的输出节为 `.ARM.unwind_tab`、`.text`。
- 重放 A 改变共同输入顺序的输出节为 `.rodata`、`.text`、`__kcrctab`、`__kcrctab_gpl`、`__ksymtab`、`__ksymtab_gpl`。
- 重放 B 改变共同输入顺序的输出节为 `.rodata`、`.text`、`__kcrctab`、`__kcrctab_gpl`、`__ksymtab`、`__ksymtab_gpl`。

两个归档候选的各级 initcall、console initcall、`.init.setup`、`__param`、`__ex_table` 输入、CPU/machine info 及 PCI fixup 组均无共同输入重排或增减。K-AFDO 仅有 `.text` 和 `.ARM.unwind_tab` 的顺序变化。后者由 EXIDX 中的 PREL31 指针寻址，归档的 EXIDX 严格单调，描述符落点全在 extab 内，最终异常表亦已排序。该版导出、CRC 和顺序敏感输入组通过首启前门禁。 [顺序敏感组](evidence/23-k1f-1d/required-order.tsv) · [K-AFDO 门禁](evidence/23-k1f-1d/kafdo-deploy-gate.json)

归档最终 argv、relink-kit 最终 argv 与重放 A 三者传入的原始单个参数字节一致，为 `--shuffle-sections=.text*=20261120`。参数无引号或转义字节。重放 B 每个 glob 均作为一个独立 argv 元素，分别为 `--shuffle-sections=.text=20261120` 和 `--shuffle-sections=.text.*=20261120`。两次均用已归档的 LLD 22.1.8、同一对象、脚本和 kallsyms/BTF 输入，仅改变参数组合及诊断输出路径。 [LLD 22.1.8 参数定义](https://github.com/llvm/llvm-project/blob/llvmorg-22.1.8/lld/ELF/Options.td)

| 重放 | Build ID | 结果 |
| --- | --- | --- |
| A 原参数 | `a78e6ca8956db526ba91d5856369fc1a7f15b5fd` | 复现归档 K-BASE-S 导出顺序和查找失败 |
| B 两个收窄 glob | `dbe40714a21a95095e5905a5cb52918ce3e557b9` | 文本布局改变。两组导出及 CRC 顺序与 A 相同，查找仍失败 |

重放 A 的 build-id 与归档一致。原始重放 ELF 尚未经构建的 link 后处理，文件 SHA 以重放收据为准。两次重放都未用于部署。

### 根因与可行修正

LLD 对 glob 匹配到的输入做随机排列，随后 `maybeShuffle` 对**所有**输入赋予优先级，包括未匹配的 ksymtab 和 kcrctab。最终 `sortInputSections` 按这些优先级重排每个输入描述组，覆盖链接脚本已做的 `SORT(___ksymtab+*)` 等名称排序。收窄 glob 仍会触发全输入赋优先级。 [LLD 22.1.8 Writer.cpp](https://github.com/llvm/llvm-project/blob/llvmorg-22.1.8/lld/ELF/Writer.cpp#L979-L1014)

可行修正是让 LLD 仅在选中的文本输入组内部重排匹配项，并保留不匹配组与显式 SORT 组的脚本顺序。另一条可评估方案是禁用该 shuffle 参数，用固定种子生成只引用可重排文本的 `--symbol-ordering-file`，筛除歧义名和保序区间。修正版候选仍须以新产物验证导出表严格有序、CRC 槽配对、`module_layout` 搜索可达、其他保序组不变，再验证文本确已重排。本轮只重放 A/B，未构建修正版。

## K-AFDO 正式首启

发令时间 `2026-11-23T22:50:26.777-08:00`。定向 disconnect 2 次、connect 2 次。
新 boot ID 的首条命令在 **58.154 s** 成功。
build-id `43ba5d455daec5da17e7521048767cdace012c91`，tryboot=1，rsts `0x1020`。正式 cmdline=True，规范化 FDT=True，模块组=False，HDMI/网络=True，dlog=True，D-Bus=True，新增严重 dmesg 签名 2。
验收问题 module_set_equal, new Oops/BUG/WARNING/module failure, loaded module paths, vermagic or build ID。

### 共用模块的 BTF 拒绝

首启仅有 6/10 个预期模块。dmesg 对 `brcmutil` 和 `btbcm` 记录同一个 `Invalid name_offset:2733556` 并拒绝加载，返回 -22。归档的这两个 K-BASE .ko 包含 split BTF 且无 `.BTF.base`，因此模块名称偏移用运行内核的 BTF 基座解释。归档配置启用了模块 BTF 验证，并禁用了 `CONFIG_MODULE_ALLOW_BTF_MISMATCH`。K-BASE 的字符串池为 2,733,556 B，两个偏移分别解码为 `pktq` 和 `bcm_subver_table`。K-AFDO 的池为 2,698,027 B。加各模块字符串后，两个合法最大偏移分别为 2,698,973 和 2,698,314，日志偏移在两者中均越界。离线用 K-AFDO 基座编号得到的类型 ID 144626、144628 也与日志一致。这项运行态失败发生在静态检查通过之后。模块门禁触发后，PMU 和三个单轮冒烟均未运行。 [BTF 基座及模块收据](evidence/23-k1f-1d/btf-compatibility.json) · [运行日志摘录](evidence/23-k1f-1d/kafdo-btf-dmesg.txt)

验收停止原因 `Stop('boot acceptance failed: kafdo')`。
发令前已通知现场观察 HDMI 和已有串口。尚未收到这次用户画面描述。

## PLAT 回程与 boot_a

普通重启回到 PLAT。build-id `395733b9c917cb98309b39cc3ec379c03ac36b3f`，boot ID `ef7f0cd4-d211-416a-a298-41bc90817b6a`，原始 cmdline、U-Boot、tryboot=0 通过，rsts `0x20`，root off 后 UID 5001。
普通回程的首条新 boot ID 命令耗时 72.673 s。
最终只读验收 418 项，原有 413 个文件 SHA 不变，空闲 **1,374,208 B**。任务文件为 `cmdline-afdo.txt`、`initramfs-afdo.gz`、`tryboot.txt`、`zImage-kafdo`、`zImage-kbase`。试启动配置使用 `zImage-kafdo` 及正式 `cmdline-afdo.txt`。

共享 sdb 服务重启 0 次。K-BASE-S 未重建。A/A 与布局测量未运行。
