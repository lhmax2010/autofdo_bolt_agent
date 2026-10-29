# RPi4 v0.2 冻结前补充核实

日期：2026-10-30（Asia/Shanghai）。本轮只验证、记录并修改获授权的 IR 匹配**原型**；不修改 LLVM 或设计，不开始增强实现。

| 项目 | 结论 | 证据 |
|---|---|---|
| 1. Thumb 来源与普遍程度 | GBS 项目 armv7l optflags 默认包含 `-mthumb`；目标多媒体库的已定义动态函数均为 Thumb，libc/加载器与裸 clang spike 存在 ARM 例外 | [E1](evidence/06/01_thumb.txt) |
| 2. IR 匹配 | 禁用 preinline 并计入零权边后，PGO/样本侧按边数为97.78%/95.65%；PGO IR权重覆盖100%，但键一致不保证后继语义一致 | [E2](evidence/06/02_ir_matching.txt) |
| 3. 主机 perf | 已查仓库均未提供 x86_64 linux-kernel-perf；没有可运行主机 perf，跨主机逐行比对未完成 | [E3](evidence/06/03_host_perf.txt) |
| 4. 丢样 | 实测942条 LOST、61,667个丢失样本；report提示8.06%，采样期间未新增换入/换出 | [E4](evidence/06/04_lost_cleanup.txt) |

下文 `W=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent`，`T=W/temp/rpi4-followup`，`F=/opt/afdo_agent/work`。E1–E4 保存命令、原始输出/明确标记的摘录和真实退出码；全量 JSON、ELF、IR、RPM、perf.data 只在 temp。板上通过命令结束标记获取真实退出码，SDB transport 退出码单列。

身份断言先于测试：`uname -m=armv7l`，`uname -r=6.12.80-arm-rpi4-v7l`，model=`Raspberry Pi 4 Model B Rev 1.5`，uid=0（E1）。连接192.168.108.26，未依赖SDB别名判板。仅写 `/opt/afdo_agent/`；未 remount、重启或装卸 RPM。

## 1. Thumb 的普遍程度与来源

### 1.1–1.2 实体文件与 ELF 统计

使用 `sdb pull` 读取已解析实体路径；板上 `sha256sum` 与本机文件哈希逐一相同。ELF 工具是 `W/temp/GBS-ROOT-RPI5-SPIKE/local/BUILD-ROOTS/scratch.aarch64.0/emul/usr/bin/readelf`，由同root的x86_64 loader及库启动，执行 `-sW`、`-SW`、`-A`（全为exit0），不是本机安装的readelf。跨架构读ELF不需要执行目标代码。

口径：仅统计已定义、类型为 **STT_FUNC** 的符号表条目；排除UND/IFUNC，版本别名按条目计数。bit0奇数为Thumb、偶数为ARM。无动态FUNC不能据此推断整个程序的模式；属性仅说明ISA使用，不能替代逐函数判断。

| 文件（均为板上绝对路径，末行为本机05产物） | .dynsym FUNC总数 | Thumb奇数 | ARM偶数 | .symtab $a/$t/$d | readelf -A |
|---|---:|---:|---:|---|---|
| /usr/lib/libavcodec.so.62.11.100 | 144 | 144 | 0 | 无.symtab | 空输出，exit0 |
| /usr/lib/libavutil.so.60.8.100 | 608 | 608 | 0 | 无.symtab | 空输出，exit0 |
| /usr/lib/libavformat.so.62.3.100 | 152 | 152 | 0 | 无.symtab | 空输出，exit0 |
| /usr/lib/libswscale.so.9.1.100 | 39 | 39 | 0 | 无.symtab | 空输出，exit0 |
| /usr/lib/libc.so.6 | 3003 | 3 | 3000 | 无.symtab | 空输出，exit0 |
| /usr/lib/ld-linux.so.3 | 22 | 0 | 22 | 无.symtab | 空输出，exit0 |
| /usr/lib/libglib-2.0.so.0.8000.5 | 1857 | 1857 | 0 | 无.symtab | 空输出，exit0 |
| /usr/lib/libgobject-2.0.so.0.8000.5 | 477 | 477 | 0 | 无.symtab | 空输出，exit0 |
| /usr/lib/libgstreamer-1.0.so.0.2411.0 | 1785 | 1785 | 0 | 无.symtab | 空输出，exit0 |
| /usr/lib/libgstbase-1.0.so.0.2411.0 | 389 | 389 | 0 | 无.symtab | 空输出，exit0 |
| /usr/lib/libgstvideo-1.0.so.0.2411.0 | 533 | 533 | 0 | 无.symtab | 空输出，exit0 |
| /usr/lib/gstreamer-1.0/libgstlibav.so | 2 | 2 | 0 | 无.symtab | 空输出，exit0 |
| /usr/lib/libstdc++.so.6.0.33 | 4610 | 4610 | 0 | 无.symtab | 空输出，exit0 |
| /usr/bin/gst-launch-1.0 | 0 | 0 | 0 | 无.symtab | 空输出，exit0 |
| /usr/bin/gst-inspect-1.0 | 0 | 0 | 0 | 无.symtab | 空输出，exit0 |
| /usr/bin/dbus-daemon | 0 | 0 | 0 | 无.symtab | 空输出，exit0 |
| /usr/bin/bash | 1 | 0 | 1 | 无.symtab | 空输出，exit0 |
| /usr/bin/ls | 0 | 0 | 0 | 无.symtab | 空输出，exit0 |
| 05 spike-base (local) | 0 | 0 | 0 | 19/4/26 | ARM Yes / Thumb-2（全文E1） |

18个板上文件均没有.symtab，不能把映射符号不可得写成确认不存在ARM/Thumb代码。`libc++` 未找到，按任务使用实际存在的 libstdc++。板上文件的 `readelf -A` 全为空；05 spike保留AEABI属性，含ARM ISA Yes、Thumb-2、v7、VFPv3、NEONv1（全文E1）。

05 spike的.symtab有14个已定义FUNC：10个ARM、4个Thumb。`main`、`hash_mix`、`sort_block`、`lookup_work`、`rare_path`、`run_workload` 为偶数ARM入口；4个Thumb入口是 `deregister_tm_clones`、`register_tm_clones`、`__do_global_dtors_aux`、`frame_dummy`。因此它是混合ELF，自己的测试负载C函数是ARM，不能用该测试包代替镜像常规包的默认flags。

完整SHA-256：

| 文件 | SHA-256 |
|---|---|
| /usr/lib/libavcodec.so.62.11.100 | `9c72c8cc96dbfd101a03414ff772fe1c6f2f41b4014234869de1be03d6ea5f56` |
| /usr/lib/libavutil.so.60.8.100 | `d9bbdf5e131799b082bed7845d2afa06780f2f9e1f7b8441a6756b83b53243af` |
| /usr/lib/libavformat.so.62.3.100 | `299b0d3485daa30c800fbf909642bf876cf85e34d4e7397285b3cc2ba328ed88` |
| /usr/lib/libswscale.so.9.1.100 | `8b2efc46173b01ce41afb5e013520fd49fa36adaa6f54f88bfbc8ceb2eb03eb9` |
| /usr/lib/libc.so.6 | `5265d103c649dee96819be42f444c31fe1045d49c0abf7c095459e13366a0d82` |
| /usr/lib/ld-linux.so.3 | `d5498e47b0a67a510cb1897aa885e3ccd4b4c3aa2bb0356edc51f8d5f1a11f42` |
| /usr/lib/libglib-2.0.so.0.8000.5 | `d4cc71caf0e97d91fe26ff6c2b1c0166d6f42df84585bdebc22c56e0f1faa4f2` |
| /usr/lib/libgobject-2.0.so.0.8000.5 | `659019d55cfc65f6239f13487426f3e582e8815895b24dd4befe90b548889636` |
| /usr/lib/libgstreamer-1.0.so.0.2411.0 | `03943dea8a6d019a599255f2c0a81fba9c34b26ad5147d5285bf11dc67f11819` |
| /usr/lib/libgstbase-1.0.so.0.2411.0 | `8075a31773ab0104fae4572f1bd185ccd00732e209492698fdddbc85ecba482f` |
| /usr/lib/libgstvideo-1.0.so.0.2411.0 | `d93eea57fbee808ac968d729008a1ff3d77df975f12aeca4c9aba05ed9a96301` |
| /usr/lib/gstreamer-1.0/libgstlibav.so | `123f426bd65f5d39ca14eefba28d17afca582272d2e54286e0d29138dfff89da` |
| /usr/lib/libstdc++.so.6.0.33 | `0c467b0a84f464363696e6ab20b7dffa5c12c9c3f56a34060242e35f1d5328cc` |
| /usr/bin/gst-launch-1.0 | `fbf80df4e729b12df8f1b4ccbf78d5f2c88b38cf8c5061e2994831c776ef7ab6` |
| /usr/bin/gst-inspect-1.0 | `7b7e1ad2d298d168ffc5eb4e19876b5bc55cf0f0a18051b9abbd61a72bdd7741` |
| /usr/bin/dbus-daemon | `1e410afe9a347987d93283ad380a60c3ea900f2884117b91c8310133818776a9` |
| /usr/bin/bash | `9d96ca4bee770b739e0a104d083f57690fd5c1842c35bf92e58a374028752c4d` |
| /usr/bin/ls | `b70f94a25f82cf89a2bb6c12eff543935e7266daea9190e8be3d3034d741d7fa` |
| 05 spike-base (local) | `4b9b4121b36f6c034410e8ff3d9aa46498d605bdd2d20f1401a280bf324fa26f` |

### 1.3 构建来源

- `config/gbs_llvm.conf:11,16` 指向Base/Unified reference。由Unified的repomd取得并核验build.conf压缩与解压SHA；文件为 `T/reference_build.conf`。该文件`:151–153`定义clang命令和优化宏，`:162`默认 `_toolchain=clang`，`:167–169`选择CC/CXX/optflags，**`:363` 的 armv7l Optflags明确有 `-mthumb`**。完整URL、哈希和带行号原文见E1。reference是可变别名，本次下载事实不是新镜像每个包的完整构建溯源；但它直接否定了只读通用rpmrc即可确定GBS项目默认flags的推论。
- `src/ffmpeg/packaging/ffmpeg.spec:232` 使用 `%{optflags}`；`:236`额外指定NEON，`:240–249`选择平台CC并调用configure。spec没有显式 `--enable-thumb`、`-mthumb` 或 `-marm`。`src/ffmpeg/configure:429`有thumb选项；`:6383–6386`检测 `__thumb__`，启用thumb后使用 `-mthumb`，否则 `-marm`。因此Thumb可由上层optflags传入，无需spec显式启用；与本次FFmpeg四库导出函数全Thumb一致。
- 实际命令：`temp/rpi4-prefreeze/logs/arm_base.log:495–496` 和 `T/logs/no_preinline.log:217–218` 均为直接 `clang -O2 ... spike.c`，没有 `-mthumb`，也没有 `-marm`。临时spec `T/spike-arm/packaging/afdo-spike.spec:29–32`没有引用 `%{optflags}`；它没有继承上述项目包级默认值。05 spike自身C函数的偶数入口与此吻合。
- libc与ld-linux的导出函数以ARM为主；本轮没有其实际构建日志/源码，不能补写它们的覆盖flags。glib、gobject、gstreamer、gst-base、gst-video、gst-libav、libstdc++的已定义动态FUNC全部Thumb，内部无符号函数/汇编的模式仍不能由导出表穷尽。

**一句话结论：本次LLVM项目配置的armv7l包默认optflags是Thumb，实测FFmpeg/GLib/GStreamer/libstdc++导出函数遵循Thumb；libc/加载器偏ARM，裸clang spike的自有C函数是ARM，镜像并非统一A32。** 与设计v0.2第1.6条的默认A32前提不一致。

## 2. 改进的 IR 分支匹配（armv7l / RPi4）

### 2.1 重新训练与生成IR

独立临时源码 `T/spike-arm`，沿用 `temp/gbs/gbs_rpi4_spike.conf` 和独立 `temp/GBS-ROOT-RPI4-SPIKE`。仓库仍为05使用的Unified20261022.054557/Base20261020.074527，不冒充新镜像同期快照。原 `spike/afdo-spike` 与 LLVM 未改。仅临时spec的插桩生成和使用命令增加 `-mllvm -disable-preinline`；本轮GBS实际编译base/instr，profile使用侧按任务2.2在主机直接编译IR。

整段setsid worker、GBS `setsid --wait`，nice19/ionice3；HOME与GIT_CONFIG_NOSYSTEM仅施加GBS。构建开始00:21:54、结束00:22:11（+08:00），真实 `GBS_EXIT=0`，`ALL-END 2026-10-30T00:22:11+08:00 OK` 同时写入日志与status。实际命令行见 `T/logs/no_preinline.log:217–218`；完整status、worker、conf在E2。

板上 `LLVM_PROFILE_FILE=F/nopre-%p.profraw F/no-preinline-instr 200000`，exit0；校验值 **ff818b861cb93a67**，与05相同轮数一致。两端SHA核对后拉回profraw，用GBS平台 `llvm-profdata merge` 得 `T/nopre.profdata`（exit0），show为11函数/35计数块，较原训练7函数/31块保留更多未preinline函数。运行、merge、show原文见E2。

主机用上述GBS的Tizen clang（22.1.8），sysroot为armv7l构建根，resource-dir为该根 `/usr/lib/clang/22`，输入均从 `T/spike-arm` 以相对 `spike.c` 传入；两侧共同参数：

```text
--target=armv7l-tizen-linux-gnueabi --sysroot=<armv7l GBS root>
-resource-dir=<armv7l GBS root>/usr/lib/clang/22
-O2 -gline-tables-only -fdebug-info-for-profiling -funique-internal-linkage-names
-Werror=profile-instr-out-of-date -Werror=profile-instr-unprofiled -S -emit-llvm
```

PGO追加 `-fprofile-use=T/nopre.profdata -mllvm -disable-preinline -mllvm -print-after=pgo-instr-use`；sample追加 `-fprofile-sample-use=T/synthetic_arm.sample -mllvm -print-after=sample-profile -mllvm -disable-sample-loader-inlining`。两侧exit0，没有profile缺失/过期警告；原始pass dump为T/pgo_pass.txt和T/sample_pass.txt，不以最终优化后的IR代替pass边界。

合成sample沿用05的计数规则（11函数、每函数50000:1000、行偏移0..39计数1000+7×offset），只调整为本轮ARM linkageName。**计数任意，仅检验结构。** `-funique-internal-linkage-names` 的hash取决于输入路径（`src/llvm/clang/lib/CodeGen/CodeGenModule.cpp:509–518`），故保持与GBS相同的相对源码名；ARM parse_number的类型后缀为Py，05 aarch64为Pm。初次误用arm64式resource-dir `/usr/lib64/clang/22` 导致stddef.h找不到、exit1，已保留E2；改用同GBS的实际32位路径后成功，没有使用主机头文件或修改LLVM。

### 2.2 原型算法与三组结果

[匹配脚本](../../tools/match_ir_branches_prototype.py)仍按函数＋完整DILocation（作用域/内联链/discriminator）＋后继序号匹配，重复键拒绝。新增：有function_entry_count但无branch_weights的分支，按所有后继权重0参与，单独统计；`--no-zero-profiled`可复现原口径；输出按IR权重的覆盖率。i32负数打印按无符号还原。额外输出 `matched_shape_mismatches`，提醒相同键的opcode/后继数不同，但不偷偷改变用户要求的匹配规则。

按条数的主指标是**后继边数**，同时列出整个终结指令匹配数。权重比=该侧已匹配边的IR权重总和/该侧全部IR带权边的权重总和；PGO列是要求的插桩权重口径，sample列按请求补列，但其权重来自人工profile，不能解释为实际执行覆盖。branch_weights可能经缩放，跨分支求和也不等同从原始profdata恢复的绝对执行次数。

| 组 | 侧 | 条件终结总数 | 完全匹配终结/参与终结 | 匹配边/参与边（匹配率） | 匹配IR权重/总IR权重（匹配率） |
|---|---|---:|---|---|---|
| 05原始输入/原口径 | pgo | 22 | 15/17 | 30/34（88.24%） | 8271035908/8593540005（96.25%） |
| 05原始输入/原口径 | sample | 23 | 15/23 | 30/46（65.22%） | 27574/37417（73.69%） |
| 本轮禁用preinline/显式权重 | pgo | 22 | 20/21 | 42/43（97.67%） | 1804524407/1804524407（100.00%） |
| 本轮禁用preinline/显式权重 | sample | 23 | 21/23 | 42/46（91.30%） | 35945/37417（96.07%） |
| 本轮禁用preinline＋零权重 | pgo | 22 | 21/22 | 44/45（97.78%） | 1804524407/1804524407（100.00%） |
| 本轮禁用preinline＋零权重 | sample | 23 | 22/23 | 44/46（95.65%） | 36354/37417（97.16%） |

新PGO侧显式带权21条终结指令，零策略增加main:158:67一条终结/两条边；sample显式23条，无新增零分支。零边不改变PGO权重分母。本轮源码和05相同，但05组为aarch64、250万轮，本轮为armv7l、20万轮，并对齐了训练源码路径；因此跨组改进不能全归因于disable-preinline这一项。后两组使用相同新IR，只切换零处理策略，才是单因素对照。

三组全部未匹配边逐条列在E2的 `unmatched`（含完整函数名、dump行号、DILocation、后继序号、权重和指令）。下面按终结指令合并显示；`0,1`表示两条边均未匹配，不省略任何未匹配分支：

| 组/侧 | 函数、源码行:列 / dump行 | 未匹配后继 | 权重 | 原因 |
|---|---|---|---|---|
| 05原始输入/原口径/pgo | run_workload 110:5 / 206 | 0,1 | 320000000,2500000 | 内联后函数/内联链不同 |
| 05原始输入/原口径/pgo | main 55:5 / 319 | 0,1 | 4096,1 | 内联后函数/内联链不同 |
| 05原始输入/原口径/sample | checksum_block 110:5 / 273 | 0,1 | 1028,1042 | 内联后函数/内联链不同 |
| 05原始输入/原口径/sample | main 158:67 / 321 | 0,1 | 409,0 | 另一侧同键无branch_weights |
| 05原始输入/原口径/sample | parse_number 141:24 / 365 | 0,1 | 0,1063 | 另一侧同键无branch_weights |
| 05原始输入/原口径/sample | parse_number 141:24 / 369 | 0,1 | 0,1063 | 不同CFG/位置作用域或后继序号，另一侧无同键 |
| 05原始输入/原口径/sample | parse_number 146:20 / 380 | 0,1 | 0,1063 | 另一侧同键无branch_weights |
| 05原始输入/原口径/sample | parse_number 146:35 / 385 | 0,1 | 0,1063 | 另一侧同键无branch_weights |
| 05原始输入/原口径/sample | parse_number 146:51 / 393 | 0,1 | 0,1063 | 另一侧同键无branch_weights |
| 05原始输入/原口径/sample | initialize_table 55:5 / 422 | 0,1 | 1035,1014 | 内联后函数/内联链不同 |
| 本轮禁用preinline/显式权重/pgo | parse_number 141:24 / 356 | 2 | 0 | 不同CFG/位置作用域或后继序号，另一侧无同键 |
| 本轮禁用preinline/显式权重/sample | main 158:67 / 314 | 0,1 | 409,0 | 另一侧同键无branch_weights |
| 本轮禁用preinline/显式权重/sample | parse_number 141:24 / 362 | 0,1 | 0,1063 | 不同CFG/位置作用域或后继序号，另一侧无同键 |
| 本轮禁用preinline＋零权重/pgo | parse_number 141:24 / 356 | 2 | 0 | 不同CFG/位置作用域或后继序号，另一侧无同键 |
| 本轮禁用preinline＋零权重/sample | parse_number 141:24 / 362 | 0,1 | 0,1063 | 不同CFG/位置作用域或后继序号，另一侧无同键 |

剩余parse_number:141:24：PGO是3后继switch，sample是两个短路br，第二个br的scope含discriminator=2。PGO后继2无另一侧同键，sample第二个br的两边也无PGO同键。**已匹配中仍有语义风险**：PGO switch默认后继0通向strtoull，而同键sample br后继0是字符`'-'`的拒绝路径；原型按序号将它们匹配（E2包含两侧指令/基本块）。另有条件取反也可能保持相同键，所以100%权重覆盖只说明此规则下的键覆盖，不能据此直接评估profile质量。新diagnostic列出此switch/br的两条形态不一致匹配边；没有修改设计或实现CFG语义匹配。

验证：旧/新输入两侧、两种策略共8次自匹配均100%；重复键负对照拒绝；无profile无权分支不补零；补零不修改输入记录；无符号权重及分母不变检查通过（E2）。原型不是通用IR解析器，没有开始正式实现。

复现三组：

```sh
python3 tools/match_ir_branches_prototype.py temp/rpi4-prefreeze/pgo_pass.txt temp/rpi4-prefreeze/sample_pass.txt --no-zero-profiled
python3 tools/match_ir_branches_prototype.py temp/rpi4-followup/pgo_pass.txt temp/rpi4-followup/sample_pass.txt --no-zero-profiled
python3 tools/match_ir_branches_prototype.py temp/rpi4-followup/pgo_pass.txt temp/rpi4-followup/sample_pass.txt
```

## 3. x86_64 主机 perf

查询repomd并按其位置下载primary，核验SHA-256后按架构和包名扫描；URL/HTTP结果/候选原文见E3。没有将名称相似的gperf当成perf。

| 查询仓库URL | 结果 |
|---|---|
| https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261022.054557/repos/standard/packages/ | 元数据200；x86_64含perf字样候选仅gperf 3.0.4-1；无linux-kernel-perf |
| https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/reference/repos/standard/packages/ | 元数据200；x86_64含perf字样候选仅gperf 3.0.4-1；无linux-kernel-perf |
| https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261020.074527/repos/standard/packages/ | 元数据200；x86_64含perf字样候选无；无linux-kernel-perf |
| https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261027.063617/repos/standard/packages/ | 元数据200；x86_64含perf字样候选仅gperf 3.0.4-1；无linux-kernel-perf |
| https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261028.105834/repos/standard/packages/ | repodata/repomd.xml HTTP404 |

20261022是板上保留perf原包的快照；20261027是已知相近快照，20261028对应当前镜像，另查reference及配套Base。**所查仓库未找到x86_64 perf包，不能证明所有Tizen仓库都没有。** 因而没有下载/安装依赖、没有主机perf --version成功记录。按任务允许的缺包分支跳过主机fixed.data/multi.data导出及buildid.data的buildid-list比较，一致/不一致行数均为**未知**，不是0。05原始data与板上完整导出文本仍留 `temp/rpi4-prefreeze/`。设计要求的跨主机对照仍未闭合。

## 4. 实际丢样记录

板上环境同05，HOME/TMPDIR/PERF_CONFIG/GST_REGISTRY/XDG_CACHE_HOME均在F内，LD_LIBRARY_PATH=/opt/afdo_agent/lib；所有perf调用用 `--buildid-dir F/buildid`，nice19/ionice3。推送1080p60秒视频后核对SHA，使用 `identity eos-after=600` 截取约20秒媒体（30fps），sync=false实际解码采样跨度11.266秒，并非强制墙钟睡眠20秒：

```text
perf --buildid-dir F/buildid record -e cycles -c 10007 -m 1 -o F/loss1.data --
  gst-launch-1.0 -q filesrc location=F/video.mp4 ! qtdemux ! h264parse !
  avdec_h264 ! identity eos-after=600 ! fakesink sync=false
```

record真实exit0；evlist为type=0/config=0、sample_period=10007、sample_type=IP|TID|TIME。record、report均提示：

```text
Processed 857333 events and lost 942 chunks!
Check IO/CPU overload!
Processed 765488 samples and lost 8.06%!
```

record写出703,821个样本；report `# Total Lost Samples: 61667`。`perf script --show-lost-events -F pid,tid,event,period,ip,dsoff` 通过awk只保留LOST行，保存各PIPESTATUS，perf和过滤器都exit0。共有**942条 `PERF_RECORD_LOST lost N`，N之和61,667**，与report一致；这是板上实测而非源码推导。例如：

```text
  30043/30043   PERF_RECORD_LOST lost 138
  30041/30041   PERF_RECORD_LOST lost 61
  30041/30070   PERF_RECORD_LOST lost 40
```

全部942条原文及stderr保存在E4，可作为文本解析素材；没有观察到PERF_RECORD_LOST_SAMPLES，不能把LOST语法等同于它。本次已产生丢样，不再启动第二个负载，也不需要走“未产生时源码推导”的替代分支。后台每秒读取vmstat共14次（epoch1793291146–1793291159）：pswpin始终26，pswpout始终613；无新增换页。仅终止本轮自己的监测循环，无其他进程操作。

GStreamer插件扫描另有 `libgstcairo.so: libGLESv2.so.2 ... No such file` 警告，原文E4；H.264解码命令仍exit0，不据此宣称所有插件可用。丢样统计与设计“丢失记录数/样本数分开计数”预期一致，补足05没有LOST的实测缺口。

## 对设计的影响（事实，不修改设计）

1. v0.2:26、370、566等处“Tizen armv7l默认A32、Thumb只在个别库”的前提与项目build.conf及本轮多媒体库不符。只看通用rpmrc或裸clang target不能推断GBS包级编译模式。第一批对Thumb的avg/补零/skid限制会涉及主要目标库，影响范围并非少数例外。
2. 禁用preinline和零边处理提高覆盖，但函数＋位置＋后继序号仍可能把switch默认路径与br拒绝路径配为同一边；即使插桩IR权重覆盖100%，也不证明后继语义或质量比较成立。人工sample计数、跨架构/轮数及源码路径差异也限制组间归因。
3. 实际LOST语法、计数与设计预期一致；LOST_SAMPLES未实测。主机perf跨架构导出对照仍缺可运行工具，不宣称冻结门槛全部满足。05已记录的buildid-list非空、vdso带偏移等结论不因本轮而撤回。

## 清理、保存与边界

采样data及训练profraw拉回T后，板上work全部清空并通过 `test -z "$(find /opt/afdo_agent/work -mindepth 1 -print -quit)"`（exit0，WORK_EMPTY）。仅保留原perf与libLLVM，两文件SHA在E4。RPM包数量前后均1252。

| /opt占用（KiB） | 开始 | 清理后 |
|---|---:|---:|
| 分区总量 | 1335696 | 1335696 |
| 已用 | 72484 | 73412 |
| 可用 | 1233104 | 1232176 |
| /opt/afdo_agent du | 35796 | 35796 |

分区整体已用增加928KiB，而专用目录大小不变、work为空；不能将系统其他写入或文件系统变化武断归因于遗留测试数据，也没有删除授权目录以外的文件。

大文件/完整证据：`T/libs/`、`T/elf_*_symbols.txt`、`T/loss1.data`（约23MiB）、`T/nopre-29568.profraw`、`T/nopre.profdata`、`T/{pgo,sample}_pass.txt`、`T/match_*.json`、`T/*primary.xml.gz`；GBS产物留在 `temp/GBS-ROOT-RPI4-SPIKE`，05数据留原temp目录。新增提交证据限E1–E4，合计147,851字节（小于150KB），旧证据不动。

边界例外：无新增已知例外。未读取工作目录外项目输入，未修改认证。历史SDB共享服务外部日志问题继续按STATUS既有记录保留；本轮未检查或删除外部文件，不能宣称审计了其内部所有隐式写入。
