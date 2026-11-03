# 第一批主机侧验证：合并、消费与打包元数据

2026-11-03，Asia/Shanghai。**部分完成，按停止条件停止：平台 Clang 22.1.8 在 armv7l 的 pseudo-probe 构建中段错误。** 未改 llvm-profgen、LLVM/spec 源码或冻结设计，未连接板子、未推 LLVM/Gerrit。普通 DWARF 路径的合并与消费验证通过；不能把本轮标为全部验收完成。

正式工具 `temp/llvm-profgen-enh/build/bin/llvm-profgen`，SHA-256 前后均为 `334a09290f53eb4c793ae91759f2b6344a36e63317820eb9151771b262dc3f30`，LLVM HEAD `e4642a8ad9e0acb990b45ade3ef7aca755cd80f2`。设计 v0.7 SHA 保持 `eec6b208d8e1fedb840f0933eb20a37c188890b6c8c29e43986c5c9bbca9f6be`。[开场](evidence/10/00_start.json)、[结束范围](evidence/10/10_end_scope.json)。本轮只一个会话；所有原始材料和大文件在 `temp/profgen-host-verification/`，下文简称 D。

## 1. 合并验收（5.12）

新增 [check_merge_inputs.py](../../../tools/profgen/check_merge_inputs.py)，用法：

```text
python3 tools/profgen/check_merge_inputs.py --input A.prof A.json 1 --input B.prof B.json 2 --output merged.prof --llvm-profdata <平台llvm-profdata路径>
```

脚本只读文件、只打印建议，不调用工具或网络。每个输入包括 profile、schema1 质量报告、正整数权重；权重同时受 llvm-profdata 的 uint64 上限约束。检查完整事件名、weight、p_ref及其来源、aggregation、head、zero_fill、skid、binary build-id及等级、格式和MD5请求/实际生效设置；conversion非ok、必要字段缺失/unknown或任一不一致都拒绝，汇总所有差异。

schema1没有单独的format/MD5字段，因此从 `tool.arguments` 的原始直接参数（支持单双横线、`=值`及format的分离值）推导，默认extbinary/MD5=false；text/binary下MD5不生效，但请求设置也要求一致。该脚本是兼容性门禁，不是报告与profile之间的内容认证，不把一致的unverified身份升级成verified。当前验证覆盖直接参数调用；没有验证response-file调用方式。建议命令在本轮使用GBS loader和GBS library-path前缀执行，**没有调用本机工具链**。[脚本20项测试与完整命令](evidence/10/02_merge_checker.json)。

实际合并使用 `temp/GBS-ROOT-LLVM-X86/local/BUILD-ROOTS/scratch.x86_64.0/usr/bin/llvm-profdata`，LLVM22.1.8，经同root的loader/libs运行。两份输入权重均为1。素材为已有 `Inputs/ip-mode/a64-pie.perfbin`，`counting.c:12`相对count_loop声明行9为键`3.2`，两条指令VA为0x1318/0x131c、文件偏移0x318/0x31c，duplication factor均4。IP行由脚本构造，零贡献表示没有该地址的样本，**不是period=0行**。[生成方法、原始命令、结果](evidence/10/01_merge.json)。

| 用例 | 手算（按键body） | 分别生成后合并 | 先合并样本再生成 | 结论 |
|---|---|---:|---:|---|
| max | 每边u=10、d=4、P_ref=4，单边贡献10；MAX(10,0)+MAX(0,10)与MAX(10,10) | 20 | 10 | 不交换 |
| sum受限 | 两边u=12/20、P_ref=4；3+5=8，sum不乘d | 8 | 8 | 本例所有键及total/head逐字节相同 |
| 0.3+0.3 | u=3/3、P_ref=10；各自半入取整0后夹到1；合起来0.6取1 | 2 | 1 | “被采到至少1”导致差异 |
| 0.6+0.6 | u=6/6、P_ref=10；各自取1；合起来1.2取1 | 2 | 1 | 单纯取整也不交换 |
| cold裁剪 | A: count_loop=10,000,000、two_sites=1；B: two_sites=100 | two_sites=100 | two_sites=101 | 裁剪不交换 |

max例的total也有独立归一化取整（两边各3，合并6；原始合并5），不把body反例扩大成total等价。cold例显式开启 `--trim-cold-profile`：A的极热函数使cold阈值高于1，two_sites被移除；B单独保留100；原始合并的two_sites=101超过可忽略尾部并保留。对应后处理实现 `llvm/tools/llvm-profgen/ProfileGenerator.cpp:957–972` 按total小于cold阈值删除。完整内联子树100/101随之不同，没有靠改变profile格式构造反例。

脚本20例通过：一致输入通过；p_ref、来源、带修饰符事件、aggregation、build-id、等级、weight、head、zero_fill、skid、失败报告、format、MD5分别拒绝；权重0/-1/1.5/abc/超过uint64拒绝；同时更改事件、p_ref和aggregation时一次列出三项差异。

## 2. 消费验证（5.10第三层）

aarch64使用`a64-pie.perfbin`，Thumb使用`thumb-count.perfbin`，均来自已有同一份`counting.c`。采用原有命令中的-O2、-ffreestanding、-fPIC、-g、-gdwarf-4、-fdebug-info-for-profiling、-funique-internal-linkage-names及相同源码工作目录/路径映射；Thumb另有-mthumb。原采样素材**已经含两个第9节选项**，无需另做“补加缺失flags”的对照组。消费时只增加任务指定的sample-use、pass转储、两项coverage=0与report-staleness；改为输出IR而非链接。原命令位置：`docs/profgen/impl/evidence/01/01_generation_commands.txt:5–7,17–19`。[全部命令、工具版本、IR原文与检查](evidence/10/03_consume.json)。

两架构均用sum、显式P_ref=1、head=none、zero_fill=none、skid=none，生成text/extbinary各一份；样本选自已知指令起点，GNU addr2line独立确认函数与内联链。count_loop body `3.2=120`；two_sites顶层total30，两个调用点偏移1/2分别有middle→leaf链，计数10/20。Thumb两条内联地址0x1308/0x130e，aarch64为0x13b4/0x13b0。

| 核对项 | 期望 | aarch64 / Thumb实际 |
|---|---|---|
| llvm-profdata show --sample --all-functions | 能读两种格式、树和行键保留 | 四次成功；single-input merge转回text均与profgen text逐字节一致，无字段差异 |
| 入口计数 | 有样本的count_loop、two_sites都有metadata | 两架构/两格式均存在；值分别1、20 |
| 条件分支 | count_loop循环条件携带非饱和权重 | 两架构均为`branch_weights i32 120, i32 1` |
| 内联关联 | two_sites声明行15，调用点16/17→偏移1/2 | IR中两条嵌套inlinedAt链分别终止于16/17，名称含相同唯一后缀 |
| 数值饱和 | 不出现4294967295 | 四份IR均无该饱和branch_weights |
| 两格式消费差异 | 格式不改变IR关联 | 除sample-profile路径属性外，pass转储逐字节一致 |

入口1/20是sample loader/profi推断结果，不是把profile的total120/30当入口；head=none的原profile入口仍0。IR里未采样函数可能带`function_entry_count=-1`哨兵，不把它误算为正入口或branch饱和。two_sites自身没有条件分支，只有带单值metadata的调用；没有把调用metadata计成条件分支。

四次消费均原样输出：

```text
(0/2) of callsites' profile are invalid and (0/150) of samples are discarded due to callsite location mismatch.
(0/0) of callsites and (0/0) of samples are recovered by stale profile matching.
```

coverage两个阈值设0时未额外输出coverage警告；这不等于独立证明所有机器指令都覆盖。原始诊断与完整IR留在证据及D，不能把“没有警告”写成性能改善或跨源码版本匹配已验证。

## 3. 08 FFmpeg构建选项与同名静态函数

08安装产物build-id仍为`f960461f63c852474257f51267b7b543afffdc9c`。依据保留的config.mak、spec、实际链接进程命令，以及本轮GBS readelf读取的`.GCC.command.line`，不重新构建FFmpeg。[带文件行号的证据](evidence/10/05_ffmpeg.json)。

| 选项 | 08实际情况 | 依据 |
|---|---|---|
| -fdebug-info-for-profiling | 未带 | `temp/v05/config_after.mak:51`无此项；ELF记录的314条编译命令中0次出现 |
| -funique-internal-linkage-names | 未带 | 同上；实际DWARF抽查没有唯一链接名后缀 |
| -mthumb | 已带 | config.mak:51，实际ELF编译记录625次出现（不是625个文件） |
| -Wl,--build-id=sha1 | 已带 | config.mak:75、`temp/v04/ffmpeg/packaging/ffmpeg.spec:247`、`temp/v05/link_observed.txt:2` |

ELF命令记录有311条clang记录、3条GNU记录；不凭config中的CC就断言每个链接输入均由clang编译。完整readelf输出501,338字节留D，仓库证据保存命令、SHA、计数与原文摘录。

08 debug `.symtab`中decode_frame至少两份独立实现，清Thumb位后VA为0x220b78/0x2667f0；DWARF分别指向mpegaudiodec_template.c:1553、tiff.c:1925；另有flacdec.c中的内联实例。iadst_iadst_16x16_add_c有三个独立地址0x2e1970、0x2f44f0、0x30bac0，来源vp9dsp_template.c:1509。都没有唯一后缀。因此补丁6的308个name_merged_functions有实际同名多DIE基础；该指标按采样命中的名字计数，不等同于文件数，也不能声称加选项必定恰好消除全部308项。

本轮最小armv7l双C文件独立验证：[源码、编译/链接/readelf/dwarfdump原文与profile](evidence/10/04_unique_names.json)。两文件都有静态noinline的decode_frame、iadst_iadst_16x16_add_c；只比较是否加唯一命名选项，profiling debug两边都开。未开时两个名字各合并2份，name_merged_functions=2；开启后DW_AT_linkage_name和profgen输出均含`.__uniq.200338890065916146067916621550098724088`或`.__uniq.326785185349622253265111230872268319535`，四函数各计10、name_merged_functions=0。样本偏移从GNU readelf程序头与清Thumb位的符号地址推导，不依赖profgen边界输出。

## 4. 交付前核实与停止原因

### 4.1 GBS执行范围

小包源/spec只在`D/package`的本地git库，不推任何远端；包含普通libhostcheck.so和probe版libhostprobe.so。使用镜像optflags，追加-g/-gdwarf-5和第9节两个选项、显式SHA1；probe版仅额外加pseudo-probe选项。未关闭真实Tizen find-debuginfo，未手工替代RPM拆分。原有spike源码/spec不改。

| 尝试 | 配置/root | 结果与时间 |
|---|---|---|
| aarch64 | 原gbs_rpi5_image.conf / GBS-ROOT-RPI5-SPIKE | 22:21:27–22:21:53，GBS_EXIT0、ALL-END OK；运行/debuginfo/debugsource RPM已生成 |
| armv7l首次 | 原gbs_rpi4_spike.conf / GBS-ROOT-RPI4-SPIKE | 22:21:53–22:21:59，GBS_EXIT1；旧Base/Unified快照不可用，未编译 |
| armv7l重试 | gbs_host_check_arm.conf / 同独立root | 22:22:42–22:26:32，GBS_EXIT1、ALL-END FAILED；普通版编译成功，probe版Clang段错误 |

重试配置来自08已用的gbs_v05_ffmpeg.conf副本，仅改buildroot/tmpdir为本项目RPi4 spike目录；Base/Unified均reference。原config/与temp/gbs两份原配置均未改。该来源不同于RPi4旧镜像快照，不能声称同一期RPM可复现；实际Clang仍22.1.8。完整日志、实际命令、spec、资源与worker在[构建证据](evidence/10/06_builds.json)。worker整段setsid，nice19/ionice3，单包线程1/make10；每600秒采样，任务均小于600秒，有各次启动资源记录，没有伪造中间采样。已确认任务进程退出，无后台构建遗留。

### 4.2 aarch64映射符号、probe位置

[readelf原文与退出码](evidence/10/07_aarch64_split.json)：普通运行文件无.symtab，映射符号$x/$d均0；调试文件有.symtab，$x=9/$d=19，.text为NOBITS；打包前同样$x=9/$d=19，.text为PROGBITS。本小包证实Tizen aarch64 debuginfo保留映射符号，不能据此保证任意第三方包。

probe版运行文件**两节都没有**；调试文件含`.pseudo_probe`和`.pseudo_probe_desc`，$x=9/$d=23。本次probe调试文件的.text仍为PROGBITS，与普通版不同，不能把“所有debug代码节都是NOBITS”作为通用假设。

两种位置拒绝已在aarch64验证：打包前ELF自身含probe两节时拒绝；打包后runtime+debug（probe只在debug）也拒绝，原文均为：

```text
llvm-profgen: error: IP sample mode is not admitted for pseudo-probe builds yet; use a sampling build without -fpseudo-probe-for-profiling and with matching DWARF
```

另一个仅给strip运行文件、不提供debug的观察为DWARF缺失/no usable samples，不能声称它识别到了已被移走的probe；该原始输出保留在证据。正式的两位置断言使用上面确实含probe的输入。armv7l在编译期崩溃，**未生成可核对的probe RPM，不能闭合双架构核实项**。

### 4.3 DWARF5、comp_dir与BUILD身份

原第三轮评审的完整实测材料未在本轮WORKDIR中找到；08对应BUILD路径的libavcodec已不存在，只有RPM/extract与部分日志。遵照要求，用本轮新aarch64普通/probe小包重做，不把新小包证据冒充旧FFmpeg实测。[逐行表、GNU addr2line、comp_dir与build-id](evidence/10/08_DWARF5_split.json)。

两个库的BUILD文件与debuginfo：除工具输出首行输入文件名外，`llvm-dwarfdump --debug-line`全文逐字节相同；各取前20个非end_sequence行表地址，GNU addr2line -i -f输出逐字节相同；各CU comp_dir完全相同。20地址包含启动对象和本小包host_check；两库各有2处两边均显示`check.c:?`，因此结论是前后一致，不是20处都恢复了有效行号。两库均同时含启动对象DWARF4 CU及本小包DWARF5 CU；debugedit仍打印DWARF version 5 unhandled及未知.debug_*节告警。验证仅证明这些输入的行表/符号化/comp_dir保持，不证明debugedit已支持DWARF5路径改写。

| 库 | BUILD链接产物ID | RPM runtime与debug共同ID |
|---|---|---|
| 普通 | b282fa324b1b50fa50372bc3f29cf72b2d199e79 | f486432ebd9d8dac8baf164788b976e427d9b4b4 |
| probe | bb16aabaa51f9505d4e048ae6645e24d22f6bf3c | 14cb08a85d1adcbaadeb2c02e87467675714162b |

这两次拆分确实改变build-id，不能直接用BUILD产物替代RPM映像。本轮已补存新构建证据，但旧08 FFmpeg同一次构建的原结论仍未独立复现；停止后未再做armv7l拆分核对。

### 4.4 停止证据与候选方案

**工具缺陷现象是平台Clang崩溃，不是本轮发现llvm-profgen输出错误。** armv7l普通库的同一公共命令已退出成功；随后加`-fpseudo-probe-for-profiling`在`@host_check`上进入ARM Instruction Selection后段错误。GBS `%build`失败，无成功RPM。[完整原始栈、实际cc1命令、预处理源码及重现脚本](evidence/10/09_stop.json)。

```text
Running pass 'ARM Instruction Selection' on function '@host_check'
llvm::ScoreboardHazardRecognizer::EmitInstruction(llvm::SUnit*)
clang: error: unable to execute command: Segmentation fault (core dumped)
clang: error: clang frontend command failed due to signal (use -v to see invocation)
```

静态源码定位 `src/llvm/llvm/lib/CodeGen/ScoreboardHazardRecognizer.cpp:171–191` 涉及SUnit指令描述与调度itinerary；栈只能定位子系统，**未证明具体故障行、空指针或根因**。候选后续工作（未执行）：

1. 编译器维护者在相同GBS root使用保留的`.c/.sh`单独复现并符号化崩溃，核对probe伪指令进入ARM hazard recognizer时的SUnit/MCInstrDesc及调度类别；若证实过滤/调度缺陷，再单独提交修复。
2. 经用户授权后，把普通DWARF与probe拆为独立小包，避免probe失败阻塞普通armv7l打包证据；这不会解决或闭合probe项。
3. A32、不同优化/调度配置或更新LLVM的对照只能作为后续定位变量，本轮没有改flags绕过，也没有据此修改设计或实现。

### 4.5 明确延期

新LLVM开启ENABLE_LINKER_BUILD_ID发布后的默认build-id复核依赖未发布包，本轮未做；`[unknown]`真实样例需板子，本轮未做，已有合成素材不替代真实样例。两项继续挂账。

## 5. 待设计v0.8登记

- 确认合并只在明确限定的线性字段和条件下等价；max、夹到至少1、取整、cold裁剪的具体反例已经实测。合并门禁从schema1的tool.arguments取得格式/MD5，不能替代profile/报告完整性绑定。
- aarch64真实Tizen拆分保留$x/$d；probe两节移到debug，且probe debug的.text可能仍是PROGBITS。IP模式继续拒绝含probe的任一文件，未改变规则。
- 新aarch64构建DWARF5行表/抽样符号化/comp_dir保持，BUILD与RPM build-id不同；证据适用范围与未复现旧FFmpeg的限制须保留。
- armv7l平台probe编译崩溃为新阻塞项；本轮没有发现必须修改冻结正确性规则的证据，也未修改v0.7正文。

## 6. 评估构建需要注意的事项

- 08 FFmpeg不能直接作为满足第9节的正式评估构建：缺两个profiling/唯一命名选项。下一任务应在采样、消费两侧显式追加，固定源码相对路径和公共flags；不要沿用本轮/08已编译对象来冒充重新编译。
- 需保留实际编译/链接命令、工具版本、RPM运行与debug的完整ID及对应关系。若工具链升级影响名称或调试关联，用消费覆盖/陈旧度诊断评估，不能用不同BUILD产物冒充已采样RPM。
- 第一批仍走无probe的DWARF路径；armv7l probe崩溃应独立定位，不能把该实验选项混入第一批性能对照公共flags。
- 本轮是合成计数/结构消费验证，不是执行次数真值、BFI/IR概率评估或性能收益。profi产生的入口与branch权重须结合下一阶段设计指标解释。
- 原RPi4快照当前不可用，后续选择仓库须保留URL和实际RPM版本，不能把本轮reference重试称为镜像同一期构建。

## 7. 文件边界与完成范围

所有主动生成材料在WORKDIR内；工具/loader均来自GBS root，未安装主机包。Clang报出的`/tmp/check-32dc12.c/.sh`是chroot路径，已确认实际文件位于WORKDIR的RPi4 buildroot/tmp内，并复制到D/build保留；未执行重现脚本。`core dumped`是否导致系统另存core未核实，未读取WORKDIR外目录，不能声称已做系统级写入审计。无已证实的新增越界项目文件。

合并脚本与已完成验证可交付；**armv7l probe打包与其拆分未完成，本轮整体停止待指示**。LLVM源码/冻结文档不改，未开始Agent代码或后续评估任务。
