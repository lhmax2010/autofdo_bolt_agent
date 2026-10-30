# llvm-profgen v0.4 冻结前核实（主机 + RPi4）

日期：2026-10-30（Asia/Shanghai）。只归档、验证与记录；LLVM、FFmpeg原源码/spec及设计正文均未修改，没有开始增强或Agent实现。一次性原型和测试包均留在temp，不进入tools。

| 项目 | 本轮结论 | 与v0.4预期 |
|---|---|---|
| 0 归档 | SHA/标题校验通过，用mv归档，Downloads原文件已不存在 | 一致 |
| 1 Tizen调试/运行文件 | debuginfo保留.symtab、映射符号与.ARM.attributes；代码节NOBITS。运行文件无上述符号/属性；两份均无build-id note | 分离文件形态符合；默认构建不能满足第9节的build-id要求 |
| 2 Thumb边界 | 20个最大Thumb函数（同时也是选取的20个含$d函数）全部逐地址一致；另补3个零大小CRT A32符号的有界范围 | 长度规则获本轮覆盖范围支持；不能推广为全部函数/DWARF范围验收 |
| 3 RPi4样例 | fork/exec偏移核对通过，取得(deleted)与.ko样本；未见([unknown]) | 符合路径/偏移规则；deleted映射身份仍缺失 |

`W=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent`，`T=W/temp/v04`，`F=/opt/afdo_agent/work`。四份证据为 [E1 构建](evidence/07/01_build.txt)、[E2 ELF](evidence/07/02_elf.txt)、[E3 边界](evidence/07/03_boundaries.txt)、[E4 板上](evidence/07/04_board.txt)。大文件、完整输出和一次性脚本只留T及GBS root。

## 0. v0.4 归档

先读STATUS；指定源文件SHA-256为 **abceb98ae958e20c4436e88c45da88c154ec4d29e0bc56939f0828530ddef4cf**，第一行为 `# llvm-profgen 增强设计（第一批详细设计 + 第二、三批规划）`，两项均满足。用 `mv -T` 从 `/home/linhao/Downloads/02_llvm_profgen_enhance_design_v0.4.md` 移至 [v0.4](../profgen/design/02_llvm_profgen_enhance_design_v0.4.md)，移动后哈希相同、源路径不存在；v0.1–v0.3不动。没有读取/触碰Downloads其他文件。

已阅读5.2.3、5.3、5.7.2、第9节与第10节步骤1，并按5.2.2固定字段导出所有正式板上样例。本轮按用户明确要求保持FFmpeg编译选项原样，**没有额外加第9节的profiling/build-id flags**；因此这是默认打包形态与边界验证，不是第9节评估构建或profile质量评估。

## 1. Tizen运行文件与调试文件

### 1.1 未改spec的GBS构建

`src/ffmpeg` HEAD=`5fe76358596f66e955f005094e6f34ca525ab23d`，在T/ffmpeg建立同提交的detached worktree。原树和worktree的 `packaging/ffmpeg.spec` SHA均为 `3bcacdb46864239418d177173bc629bc250f247e31de4e53bc8dfd247c307a49`，原树前后干净。

`temp/gbs/gbs_v04_ffmpeg.conf`复制自 `config/gbs_llvm.conf`，只把buildroot/tmpdir指向新的 `temp/GBS-ROOT-V04-FFMPEG` / `temp/gbs-tmp-v04-ffmpeg`；两份用户config未修改。仓库仍为：

- https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/reference/repos/standard/packages/
- https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/reference/repos/standard/packages/

运行 `gbs -c W/temp/gbs/gbs_v04_ffmpeg.conf build -A armv7l --threads 1 --define '_smp_mflags -j10'`；只调整make并发（nproc=20的一半），没有新增编译/链接flags。整段setsid worker，GBS使用setsid --wait、nice19/ionice3；HOME/GIT_CONFIG_NOSYSTEM仅给GBS及子进程。启动前未发现其他ninja/clang/gbs/make重任务；两个GBS构建串行。结束时status全文和带时间ALL-END打印到日志，启动输出最后单独给出tail/cat命令。

| 构建 | 开始→结束（+08:00） | 真实GBS退出码 | 结束标记 |
|---|---|---:|---|
| FFmpeg | 20:35:55→20:42:49（6分54秒） | 0 | ALL-END 2026-10-30T20:42:49+08:00 OK |
| 板上临时样例包 | 20:43:08→20:43:32（24秒） | 0 | ALL-END 2026-10-30T20:43:32+08:00 OK |

FFmpeg产出22个二进制RPM（含7个debuginfo与1个debugsource）及1个SRPM；完整大小/SHA清单在E1、T/rpm_manifest.json。解包 `libavcodec-8.0.1-1.armv7l.rpm` 与 `libavcodec-debuginfo-8.0.1-1.armv7l.rpm` 至T/runtime-extract、T/debug-extract（rpm2cpio/cpio使用pipefail，exit0）。没有安装板上RPM。

实际配置 `temp/GBS-ROOT-V04-FFMPEG/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/ffbuild/config.mak:51` 包含平台 `-Os -g2 -gdwarf-4 ... -mthumb`，FFmpeg随后追加 `-O3 ... -mthumb`。这些是原spec/configure产生的flags，不能只以平台-Os称最终优化级别为Os。完整行在E1。

### 1.2 ELF内容

所有ELF读取/合并/反汇编均使用工作目录内 `temp/GBS-ROOT-RPI5-SPIKE/local/BUILD-ROOTS/scratch.aarch64.0/emul/usr/bin/` 的平台工具及配套x86_64 loader/libs，未用主机安装的readelf/objdump。readelf执行 `-SW/-sW/-A/-n/-lW` 全部exit0，命令及原输出见E2。

| 项目 | 运行文件 libavcodec.so.62.11.100 | 对应 .debug |
|---|---|---|
| .symtab | 无 | 有 |
| 映射符号$a / $t / $d（含数字后缀形式） | 不可得（无.symtab） | 27 / 5882 / 6489 |
| .ARM.attributes | 无，readelf -A空输出 | 有，SHT_ARM_ATTRIBUTES；原文见E2 |
| build-id note节/类型 | 不存在；不是NOBITS占位 | 不存在；不是NOBITS占位 |
| readelf -n可读build-id | 无 | 无 |
| 两份build-id一致性 | 缺失，不能判“已匹配” | 缺失，不能验证有ID时的note保留方式 |
| .init/.plt/.text/.fini | PROGBITS，含代码字节 | 全为NOBITS，不含指令字节 |

.debug的AEABI属性含CPU v7、ARM ISA Yes、Thumb-2、VFPv3、NEONv1等；运行文件去除了该节，符合从debug优先取属性的必要性。映射符号按 `^\$[atdx](?:\.\d+)?$` 匹配并统计，区分有无.symtab，不把不可得当成“整个二进制没有映射状态”。

运行文件SHA-256=`0c552ec77c568b0848e8ae61db6ff82d2a2afc6a73c724cccadf63522a128dec`；.debug SHA-256=`8a01c7b03326a05ad4e7043d61f102e2e66151cf9f9e07567d8c2741b637f4e9`。两者来自同次构建及对应RPM，不能用文件整体SHA不同否定配对，也不能冒称它们已通过build-id身份链。

### 1.3 默认链接与build-id

`T/logs/ffmpeg.log:1488`只打印 `LD libavcodec/libavcodec.so.62`，原spec的make是静默模式，**日志没有完整链接参数**。为不改原spec或编译选项，另用只读 `ps -ww -eo pid,args` 捕获了20:42:33实际运行的链接shell和clang argv（T/link_observed.txt:1–2，E1）。这是真实进程观察，非make -n推导，也没有补写成原构建日志：

```text
armv7l-tizen-linux-gnueabi-clang -shared -Wl,-soname,libavcodec.so.62
-Wl,-Bsymbolic -Wl,--version-script,libavcodec/libavcodec.ver
-Llibavcodec -Llibavdevice -Llibavfilter -Llibavformat -Llibavutil -Llibswscale -Llibswresample
-Wl,-z,relro -Wl,-z,now -Wl,--as-needed -Wl,-z,noexecstack
-Wl,-rpath-link=:libswresample:libswscale:libavfilter:libavdevice:libavformat:libavcodec:libavutil
-Qunused-arguments -o libavcodec/libavcodec.so.62 @libavcodec/libavcodec.so.62.objs
-lavutil -pthread -lm -latomic -lm -latomic -pthread
```

完整 `temp/GBS-ROOT-V04-FFMPEG/local/BUILD-ROOTS/scratch.armv7l.0/tizen_unified_standard.conf:1–559` 中搜索build-id/build_id为0项；`:151–169`是clang选择宏，`:363`是armv7l optflags。实际 `ffbuild/config.mak:75` 的LDFLAGS也没有build-id。打包日志`:1756`调用find-debuginfo带 `--build-id-seed`，但`:1791`已警告No build ID note found，`:1851,2018`分别警告运行文件/.debug缺ID；seed没有凭空生成缺失note。

**一句话结论：本次LLVM reference配置下原样构建的FFmpeg链接没有生成build-id，split-debug后两份仍缺失，与06板上libavcodec无ID一致；第9节所需身份链必须另由授权的评估构建提供。** 此结论不泛化到所有包或GNU链接器。

打包另有 `T/logs/ffmpeg.log:1784,1789` 的debugedit警告：Unknown .debug_line_str、DWARF version 5 unhandled。RPM最终成功且映射符号可读；本轮没有验证完整DWARF源码路径修写或行表质量，不能据边界核对通过推断这些也已通过。

## 2. Thumb指令边界

### 2.1 原型与参照

一次性脚本 `T/elf_boundary.py`（只在temp），以平台readelf输出取得.debug的.symtab/映射符号/函数区间；按所属节取区间起点之前最近映射状态，内部遇映射符号切换。原始Thumb st_value先清bit0，样本IP不做该处理。

指令字节只读运行文件：$t从已知指令起点顺序步进，首半字bits[15:11]为29/30/31时4字节，否则2字节；$a每次4字节；$d整段跳过。遇缺映射或跨区间末尾记录失败，不偷偷计为代码。映射查询按节隔离，避免其他节的同地址符号干扰。

平台 `eu-unstrip -o T/libavcodec.merged.so <runtime> <debug>` 成功（exit0）；使用该合并文件作objdump参照，**没有使用strip前文件替代**。对每个选定函数运行 `llvm-objdump --triple=thumbv7a -d --start-address=... --stop-address=...`，映射符号使其中A32区间按ARM解码；忽略objdump的.word/.short等数据指令行，逐条比较真实指令起点。所有参照命令exit0，无unknown编码；完整输出T/disasm_*.txt，命令/摘要E3。

### 2.2 选取范围和逐函数结果

有非零STT_FUNC大小的Thumb函数共5584个，含$d范围的有4872个；各按大小降序（同大小按地址/名称）取前20，**这两组恰好是同一批20个函数**，不是40个不同函数。非零大小的A32函数为0；发现3个A32 CRT符号的st_size均为0，另做补充：call_weak_fn取到同节下一FUNC，_init/_fini取节末尾。下面明确标记其推导上界；它们不等同于已验证DWARF函数区间，也不隐藏本轮缺少有声明大小的A32函数这一限制。PLT的$a范围没有FUNC条目，不冒充函数纳入。

| 函数 | 起点 | 大小/范围（字节） | 组 | 一致起点数 | 不一致数 |
|---|---|---:|---|---:|---:|
| inter_pred_scaled_8bpp | 0x31e0e4 | 36236 | Thumb前20＋含$d前20 | 13190 | 0 |
| inter_pred_scaled_16bpp | 0x326e70 | 36224 | Thumb前20＋含$d前20 | 13091 | 0 |
| inter_pred_8bpp | 0x32fbf0 | 27104 | Thumb前20＋含$d前20 | 10025 | 0 |
| inter_pred_16bpp | 0x3365d0 | 26964 | Thumb前20＋含$d前20 | 9873 | 0 |
| ff_h264_decode_mb_cabac | 0xc406c | 24156 | Thumb前20＋含$d前20 | 8190 | 0 |
| vp8_decode_mb_row_no_filter | 0x2a7308 | 21256 | Thumb前20＋含$d前20 | 7797 | 0 |
| ff_vp9_decode_block | 0x2bf90c | 19752 | Thumb前20＋含$d前20 | 7123 | 0 |
| vc1_decode_b_blocks | 0x27b6c0 | 19080 | Thumb前20＋含$d前20 | 6431 | 0 |
| decode_frame_header | 0x2b9390 | 18656 | Thumb前20＋含$d前20 | 6126 | 0 |
| decode_frame | 0x2667b0 | 17568 | Thumb前20＋含$d前20 | 5694 | 0 |
| ff_h264_decode_mb_cavlc | 0xd0070 | 16936 | Thumb前20＋含$d前20 | 5921 | 0 |
| vc1_decode_p_blocks | 0x277770 | 16208 | Thumb前20＋含$d前20 | 5415 | 0 |
| mp_decode_frame | 0x220d28 | 16056 | Thumb前20＋含$d前20 | 5375 | 0 |
| encode_mb | 0x231acc | 13988 | Thumb前20＋含$d前20 | 5120 | 0 |
| ff_h264_filter_mb_fast | 0xd7b48 | 13680 | Thumb前20＋含$d前20 | 4786 | 0 |
| ac3_decode_frame | 0x53df0 | 12164 | Thumb前20＋含$d前20 | 4277 | 0 |
| mpeg4_encode_mb | 0x21c380 | 11284 | Thumb前20＋含$d前20 | 3806 | 0 |
| hl_decode_mb_444_complex | 0xdd660 | 10972 | Thumb前20＋含$d前20 | 3898 | 0 |
| hl_decode_mb_complex | 0xe1250 | 10880 | Thumb前20＋含$d前20 | 3762 | 0 |
| iadst_iadst_16x16_add_c | 0x2e1930 | 10780 | Thumb前20＋含$d前20 | 2959 | 0 |
| call_weak_fn | 0x2fd28 | 36 | A32补充（st_size=0，推导上界） | 7 | 0 |
| _init | 0x14f50 | 12 | A32补充（st_size=0，推导上界） | 3 | 0 |
| _fini | 0x341060 | 8 | A32补充（st_size=0，推导上界） | 2 | 0 |

共 **132,871** 个起点逐地址一致，不一致0、步进越界0；无不一致地址/字节可列，完整逐函数JSON为T/boundary_results.json。20个Thumb函数的计数为132,859，3个A32补充范围合计12。另对人工已知 `00bf / 40f20100 / 00f000f8`（16位NOP/32位MOVW/32位BL）检查起点[0,2,6]，长度规则通过。未使用MC解码来产生原型的参考长度。

这些结果支持v0.4 5.7.2的长度规则及$d排除；范围按用户要求的大小/映射类型选取，**不是按本轮perf热度选取**，也不是任意DWARF子区间、所有手写汇编或所有架构的完整验收。

### 2.3 thumb与thumbv7a差异

平台llvm-mc对相同两行字节执行 `--disassemble --triple=thumb` 与 `--triple=thumbv7a`（命令、stdout、stderr全在E3）：

```text
输入：0x40 0xf2 0x01 0x00
      0x00 0xf0 0x00 0xf8
thumbv7a：movw r0, #1 ; bl #0
thumb：invalid instruction encoding警告，并错误拆成lsls/movs/lsls
```

**两次退出码都为0**，thumb输出含警告且边界错误，不能把exit0当解码正确。该差异与v0.4禁止无版本arm/thumb作为交叉核对triple一致。

## 3. RPi4真实样例

### 3.0 环境与采集口径

连192.168.108.26后先断言armv7l、内核6.12.80-arm-rpi4-v7l，退出0；model为Raspberry Pi 4 Model B Rev 1.5。/opt是rw、无noexec。复用保留的perf6.12.80/libLLVM，不安装或卸载RPM、不remount、不重启。所有新文件在F；HOME/TMPDIR/PERF_CONFIG/GST_REGISTRY/XDG_CACHE_HOME指向F下，LD_LIBRARY_PATH使用专用目录；perf全部加 `--buildid-dir F/buildid`。

临时包在T/spike-samples，复用06的spike.c作为计算函数，新增cases、after、deleted和libdeleted_probe.so；只在temp变体中改spec，沿用 `temp/gbs/gbs_rpi4_spike.conf`、独立 `temp/GBS-ROOT-RPI4-SPIKE`，未改原spike。样例为-O2、含行表及显式build-id的ARM构建，不用于代表本轮FFmpeg的默认Thumb。对应ELF build-id和完整实际编译命令见E4。

所有正式样例均用同一命令导出，不增加/删减字段：

```text
LC_ALL=C perf --buildid-dir F/buildid script -i F/<case>.data
  --show-mmap-events --show-lost-events -F pid,tid,event,period,ip,dsoff
```

录制后用evlist核对cycles type=0/config=0，文本与data均拉回T并核对两端SHA；四次正式导出exit0。大文本保留T/*.txt，不把全量几十万行放进Git；E4留MMAP/样本原文摘录作为后续lit素材。

### 3.1 不exec的fork

`perf record -e cycles -c 1000003 ... -- F/cases fork`，exit0。父进程fork后两者直接运行同一spike负载，各200000轮；源码无exec，校验均为ff818b861cb93a67，父进程等待子进程正常退出。分析原型T/analyze_samples.py按已知父子关系将父进程已有映射用于子进程独立核对，不改perf/LLVM读入器。

| 进程 | 全部样本 | 目标cases样本 | ip−start+pgoff与dsoff一致 | 自有MMAP2 |
|---|---:|---:|---|---:|
| 父6736 | 4927 | 4923 | 4923/4923，100% | 5（含cases） |
| 子6738 | 4918 | 4917 | 4917/4917，100% | 0 |

目标映射起点0x420000、pgoff0。子进程没有自己的MMAP2，目标映射由fork继承；不能要求每个样本pid都在文本中出现自有MMAP2。这里独立核对仅针对cases映像，少量libc/内核样本不混入目标分母。与v0.4依赖perf处理fork映射的设计一致。

### 3.2 exec替换

`perf record -e cycles -c 1000003 ... -- F/cases exec`，exit0。PID **6835** 先运行相同计算，再execl到不同的F/after继续计算；stdout的BEFORE/EXEC/AFTER使用同pid。文本中cases映射起点0x420000，after为0x480000，均有独立MMAP2。

总样本5925；exec前cases **4833** 条、exec后after **1081** 条，目标合计5914条偏移公式100%一致。以新映像MMAP2在perf时间排序导出流中的位置为切换边界，exec后归旧cases的样本 **0**，切换前归after的样本 **0**。余11条非目标样本不宣称已做映像内偏移核对。符合v0.4的exec替换预期。

### 3.3 (deleted)

临时程序动态加载F/libdeleted_probe.so，进入main后unlink该路径，再创建F/deleted.ready等待采样触发，计算继续调用已映射的库。用LD_LIBRARY_PATH=F:/opt/afdo_agent/lib启动；只删除本轮专用测试库。为让合成MMAP2观察删除状态，perf使用-p附加到ready中的pid，再通过go文件放行。

第一次在目标结束后还保留5秒采集workload，perf返回143（stderr有Terminated）；第二次主动SIGINT结束采集返回130，子进程均0。这两次不判成功，原命令/错误保留E4，partial data留T/deleted_failed.data、T/deleted_interrupted.data。最终把采集workload限制为100ms，在目标仍活着时自然结束：**PERF_EXIT=0、CHILD_EXIT=0**，151条样本全部在删除后的库中，偏移核对151/151。

```text
      0/0       PERF_RECORD_MMAP2 7933/7933: [0xb6f50000(0x1000) @ 0 b3:03 966 0]: r-xp /opt/afdo_agent/work/libdeleted_probe.so (deleted)
   7933/7933       1000003 cycles:          b6f50410 (/opt/afdo_agent/work/libdeleted_probe.so (deleted)+0x410)
```

路径内部` (deleted)`在最终`+0x偏移`之前，符合5.2.3按完整DSO字段解析的规则。合成事件的外层前缀可以是0/0，映射实际pid在PERF_RECORD_MMAP2之后，不能拿外层前缀当映射pid。

该库ELF有build-id `390adaa690f0167d6f59403cc8d7deb4a04a7d86`，但本次虽用 `--buildid-mmap`，删除后的映射仍是设备号/inode格式、没有ID。不能凭本机相同路径/已知库ID宣称该映射身份verified；v0.4缺证据处理规则适用。这是后续lit需要覆盖的真实缺失身份案例。

### 3.4 已加载模块

lsmod列出kdbus、logger、proc_tsm等；以**只读DBus ListNames查询500次**触发已有kdbus代码，`perf record -a -e cycles -c 100003 ...`，record/查询/导出均exit0。没有加载/卸载模块，也不改网络、存储或启动配置。

系统级共318382样本，其中模块1729条：kdbus **1663**、logger **56**、proc-tsm **10**。系统级采样包含背景活动，后两者不归因于ListNames操作。实际DSO形式是完整模块路径加偏移，例：

```text
   8017/8017        100003  cycles:          bf03c3c8 (/lib/modules/6.12.80-arm-rpi4-v7l/extra/kdbus/kdbus.ko+0x945c)
```

模块合成映射在这份数据中打印为PERF_RECORD_MMAP（不是MMAP2），原文在E4，v0.4两种记录都识别的规则适用。本轮只核对分类/格式，不生成模块profile，不把模块偏移套用用户DSO公式。系统级还自然观察到274条其他删除DSO样本，未修改这些已有文件。

### 3.5 [unknown]与素材范围

四份正式文本合计9845+5925+151+318382条样本，`([unknown])` **0条**；如实记未观察到，不专门构造。所有原文均来自5.2.2导出，E4保留目标MMAP2、deleted样本、模块样本；完整txt和data在T。没有把“符号unknown”与DSO `([unknown])`混为一谈。

## 对设计的影响（只陈述事实）

- 调试文件确实提供映射符号/ARM属性，代码字节必须从运行文件读取；本轮支持5.3.4与5.7.2。原样FFmpeg缺build-id，所以“默认运行RPM＋debuginfo”本身不能满足第9节身份链；有ID时note在拆分后是否可读仍没有这次FFmpeg的正例，不以“两个都没有”称一致性验证通过。
- 20个Thumb函数边界和$d跳过全部一致；未验证所有DWARF函数子区间。A32只有3个st_size=0 CRT符号的补充范围，不能把推导上界视为可直接接受的DWARF边界策略。原型不进入正式实现。
- 不exec的子进程可以有样本而没有自有MMAP2；exec前后映像归属正确。deleted的括号位置、模块完整.ko路径与v0.4预期一致；deleted合成MMAP2即使启用buildid-mmap也可能无ID。`([unknown])`仍无实测素材。
- 构建日志中的debugedit DWARF5警告是额外观察，本轮没有证明源码路径修写或行信息完整性。未改设计文档；剩余RPi5的dsoff、--buildid-mmap、页大小待后续核实。第10节第二阶段前的IR/BFI重跑及是否构建主机perf不在本轮执行范围。

## 清理、原始数据与边界

板上F所有内容已删除，`find ...`空目录断言exit0，WORK_EMPTY；保留原tools/perf和lib/libLLVM.so.22.1，哈希未变，RPM数量前后1252。/opt分区：开始已用81880KiB/可用1223708KiB，清理后已用 **82788KiB**、可用 **1222800KiB**、**7%**；专用目录du前后均35796KiB。分区整体增加908KiB不等于专用目录有残留，不删除其他目录以追平系统占用。

原始数据：T/{fork,exec,deleted,module}.data及同名.txt；ELF与调试文件在T/runtime-extract、T/debug-extract，合并参照T/libavcodec.merged.so；全量符号/反汇编T/*symbols.txt、T/disasm_*.txt；一次性原型T/elf_boundary.py、T/analyze_samples.py；构建日志T/logs，所有RPM留对应GBS root。旧05/06证据不动。

边界例外：本次仅读取并移动指定Downloads v0.4文件，属于用户明确授权；未触碰其他Downloads文件。无新增已知的其他边界例外；历史SDB共享服务外部日志审计限制继续保留，本轮未读取或删除外部遗留文件。

本轮新增四份证据合计 **99,680字节**（小于150KB）。
