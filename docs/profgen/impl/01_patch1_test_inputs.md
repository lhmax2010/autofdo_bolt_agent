# llvm-profgen 补丁 1：测试素材与 C1 基线

日期：2026-11-02。冻结设计 v0.7；本轮只新增测试素材及项目侧重放脚本，不修改 llvm-profgen 源码、既有测试、spec 或设计，不做 GBS 构建，不连接开发板，不推 Gerrit。

## 1. 基线、提交与范围

- 设计 SHA-256：`eec6b208d8e1fedb840f0933eb20a37c188890b6c8c29e43986c5c9bbca9f6be`。
- LLVM 基线：`f999bd406c0a70fe8107aa992164fe6945c5d46a`；工作树 `temp/llvm-profgen-enh`，分支 `afdo/profgen-enhance`。
- LLVM 本地补丁提交：`00fa352d531680f0bf4a55dec21b30bacfcd4092`，作者 Hao Lin <hao.lin@samsung.com>；标题 `[llvm-profgen] Add test inputs for IP sample mode`。
- [二进制 format-patch](../../../patches/profgen/0001-llvm-profgen-Add-test-inputs-for-IP-sample-mode.patch) 只新增 `llvm/test/tools/llvm-profgen/Inputs/ip-mode/` 内的 104 个文件，共 366,795 字节；其中 46 个 ELF 共 255,656 字节，最大 13,824 字节。没有新增 RUN 测试。
- 在独立临时 index 中 `git read-tree <基线>` 后 `git apply --cached --check <补丁>` 退出 0；未改动当前工作树的 index。记录见 [提交/应用检查](evidence/01/09_repository_checks.txt)。
- 原有基线工具 `temp/llvm-profgen-enh/build/bin/llvm-profgen` 使用前/后 SHA 均为 `a31073338f9315a0fd6d2934e36431d9135086882ebfb07bd1bda7c36d7f9f1e`。

## 2. 工具与生成方法

所有 ELF 的编译、链接、拆分与检查均使用工作目录内 GBS 平台工具，经其 x86_64 loader 和库运行；没有使用主机安装的工具链。只直接编译很小的 freestanding C/汇编，不启动 GBS，不运行新 ARM 二进制。

| 标识 | 工具根目录（相对 WORKDIR） | 实际版本 |
|---|---|---|
| T-ARM | `temp/GBS-ROOT-V04-FFMPEG/local/BUILD-ROOTS/scratch.armv7l.0/emul` | clang、ld.lld、llvm-objcopy、llvm-dwarfdump 22.1.8；GNU readelf 2.43 |
| T-A64 | `temp/GBS-ROOT-RPI5-SPIKE/local/BUILD-ROOTS/scratch.aarch64.0/emul` | clang、ld.lld、llvm-objcopy、llvm-dwarfdump 22.1.8；GNU readelf 2.43 |

[完整工具路径、版本命令与原始输出](evidence/01/02_tool_versions.txt)；[逐素材完整生成命令](evidence/01/01_generation_commands.txt)。两份文件也随 LLVM Inputs 提交为 `tools.txt`、`commands.txt`。命令按 `[文件名]` 分组，包含 loader、库目录、target、所有编译/链接/objcopy 参数、cwd 和临时对象位置；派生文件先执行其源文件的命令。所有耗时工具均 nice 19、ionice idle，串行执行。

C 素材显式使用 `-O2 -g -gdwarf-4 -fdebug-info-for-profiling -funique-internal-linkage-names`；Thumb/A32 分别显式 `-mthumb`/`-marm`。使用 DWARF4 是离线小素材的构造选择，不代表已经关闭 Tizen DWARF5 拆分挂账。汇编边界来自手写编码和标签，不依赖 objdump。

## 3. 素材总表

下表列出全部文件；“命令”指向第 2 节的完整命令证据内同名组。文本原文直接写入文件，来源及行号见 [素材说明](evidence/01/03_input_provenance.txt)。机器可读的完整清单见 [08_input_manifest.json](evidence/01/08_input_manifest.json)。文件均为 0644。

| 名称 | 架构/指令集 | 用途/设计节 | 来源 | 生成命令/工具 | 字节 | SHA-256 |
|---|---|---|---|---|---:|---|
| `README.txt` | 说明/golden | 5.3/5.7.2/5.10；复现与人工预期 | 本轮记录 | 手写/摘录；见素材说明 | 18183 | `ef2a1155df1123ae8a81ece20c89452d595c72dcfd05312eb58e6de673a37963` |
| `a64-16k.perfbin` | AArch64 | 5.3.1 PIE / segment offsets / alignment; 5.4 counting | 合成；源 counting.c | 同名命令组 / T-A64 | 6296 | `d8f18deac14fa8ed6a2a5c7cc6661d0489e024ca871af5ed08442d9af4e76c67` |
| `a64-16k.perfscript` | perf 文本 | 5.3.1 / 5.7 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output; p_offset=0x0003a0, p_vaddr=0x00000000000043a0, off=0x4a4 => VA=0x44a4 | 手写/摘录；见素材说明 | 65 | `3bd96f6f534d66d1efda08123b972ce5ebde4b44c87139134ed11226fae19c94` |
| `a64-64k.perfbin` | AArch64 | 5.3.1 PIE / segment offsets / alignment; 5.4 counting | 合成；源 counting.c | 同名命令组 / T-A64 | 6296 | `e654a4cb6a45bd1ae0610374b7da04cb3b8e01997ac983988a475555fbcaac80` |
| `a64-64k.perfscript` | perf 文本 | 5.3.1 / 5.7 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output; p_offset=0x0003a0, p_vaddr=0x00000000000103a0, off=0x4a4 => VA=0x104a4 | 手写/摘录；见素材说明 | 65 | `00245f27154fc202e7769db685dcebf5f752dd9e3b5993ddf249b2da67fa264b` |
| `a64-fast.perfbin` | AArch64 | 5.3.2/5.3.3 identity mismatch / missing ID | 合成；源 counting.c | 同名命令组 / T-A64 | 6280 | `349535714d3b904f4accba9a87310673f93a2c471a96d61d439a488e5d4d4564` |
| `a64-fs.debug` | AArch64 | 5.3.4/5.7.2 split-debug equivalence | 合成；源 a64-fs.perfbin | 同名命令组 / T-A64 | 6376 | `d37405fe4f7564532f91676b63723cdac0df02d1ac29535b901f42791f08427b` |
| `a64-fs.perfbin` | AArch64 | 5.4/5.10 FS discriminator + split-debug | 合成；源 counting.c | 同名命令组 / T-A64 | 6456 | `06ab09eca3175bc13df5b0f738122720f053c4eb919536c8946f0fdb188cc927` |
| `a64-fs.stripped.perfbin` | AArch64 | 5.3.4/5.7.2 split-debug equivalence | 合成；源 a64-fs.perfbin | 同名命令组 / T-A64 | 2704 | `258cb776b4f803f248602d6a18bbbe13c5397fab9b6c678203a70263dd286cf9` |
| `a64-multi-gap.perfscript` | perf 文本 | 5.3.1 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output; off=0x1800 lies in neither exec PT_LOAD; reject unmapped_in_target | 手写/摘录；见素材说明 | 75 | `03c3306f9fd00c818668d47c64d25296ec2fe91c255bb21c8e4740018b7752ff` |
| `a64-multi-load.perfbin` | AArch64 | 5.3.1 PIE / segment offsets / alignment; 5.4 counting | 合成；源 multi-load.s | 同名命令组 / T-A64 | 13824 | `4db0649ae2a1142278702157e495dade5fd715c881875394d9fb28db90d8d497` |
| `a64-multi-load.perfscript` | perf 文本 | 5.3.1 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output; paired with multi-load.lds; expected VA 0x10000,0x10004,0x30000,0x30004 | 手写/摘录；见素材说明 | 500 | `5d7cd0a0ddc260dd10c47969467e450d7ffe03f658e62820fdffc1163dd5362f` |
| `a64-no-id.debug` | AArch64 | 5.3.2/5.3.3 identity mismatch / missing ID | 合成；源 a64-pie.debug | 同名命令组 / T-A64 | 5648 | `10451a5178784f8da08f03c2ab5759720a82ae18f6732d0b4bdd173a3c7ac094` |
| `a64-no-id.perfbin` | AArch64 | 5.3.2/5.3.3 identity mismatch / missing ID | 合成；源 a64-pie.perfbin | 同名命令组 / T-A64 | 5648 | `8027b33b9980de956df6f0612378646aed25adb3f0728e26454244cf1234970c` |
| `a64-pie.debug` | AArch64 | 5.3.4/5.7.2 split-debug equivalence | 合成；源 a64-pie.perfbin | 同名命令组 / T-A64 | 5728 | `a13dcb56165f3fbb6c3cd57815fee948e181871a549062b8235c1e9bb59b1660` |
| `a64-pie.perfbin` | AArch64 | 5.3.1 PIE / segment offsets / alignment; 5.4 counting | 合成；源 counting.c | 同名命令组 / T-A64 | 5768 | `54ffd743a9f414167602f3f9234c44e435baeeec926986f7cb6dba6a2995bac7` |
| `a64-pie.perfscript` | perf 文本 | 5.3.1 / 5.7 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output; p_offset=0x0002f0, p_vaddr=0x00000000000012f0, off=0x3f4 => VA=0x13f4 | 手写/摘录；见素材说明 | 65 | `dc1872272087b7490376435f1d52788032dbb709532e2d3262a089e2cdeee029` |
| `a64-pie.stripped.perfbin` | AArch64 | 5.3.4/5.7.2 split-debug equivalence | 合成；源 a64-pie.perfbin | 同名命令组 / T-A64 | 2120 | `74502a146b832b08bd29f8b606ecbeed43ee3ec797de7ea80fa4935526963b25` |
| `a64-probe.debug` | AArch64 | 5.1.4/5.10 probe section rejection | 合成；源 a64-probe.perfbin | 同名命令组 / T-A64 | 6872 | `a385632aa007bd4b712f7e76072143a49fc71dae8badfc47671baa38caca4812` |
| `a64-probe.perfbin` | AArch64 | 5.1.4/5.10 probe section rejection | 合成；源 counting.c | 同名命令组 / T-A64 | 6952 | `cf0b89e2a53cadab44d89ce154eff3f50f368e1004fde6621b37e5ab52253482` |
| `a64-probe.stripped.perfbin` | AArch64 | 5.1.4/5.10 probe section rejection | 合成；源 a64-probe.perfbin | 同名命令组 / T-A64 | 2640 | `b59b9a6f70111da54df5cb7948cc3dab8e7a84a5ded3d37b54647dea11edd564` |
| `arm-count.perfbin` | ARM/Thumb；见 golden | 5.4/5.10 unroll, two inline call sites, nested inline; 5.7 ISA | 合成；源 counting.c | 同名命令组 / T-ARM | 5100 | `4370b10c4933c6bf54d9cbc9732f2571054a6877b9bbe18214a83de59aa70a66` |
| `arm-count.perfscript` | perf 文本 | 5.3.1 / 5.7 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output; p_offset=0x000298, p_vaddr=0x00001298, off=0x39c => VA=0x139c | 手写/摘录；见素材说明 | 67 | `7f2db1950a003871c62bf0a83fa347e690b7977d6cd0985d6e5ec332caa080f4` |
| `arm-literal.perfbin` | ARM/Thumb；见 golden | 5.7.2/5.10 hand-known ISA/mapping boundaries | 合成；源 arm-literal.s | 同名命令组 / T-ARM | 5400 | `1b6ceee72579d4ef7f780199536ff0869be4f90bc50263a4071a0da3ae94eff2` |
| `arm-literal.s` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 703 | `6a886f018e01d971cd95b9459ec80bc3604172afedf7be4e6b9dd32880a47c70` |
| `bad-a64-end.perfbin` | AArch64 | 5.7.2/5.10 boundary negative (well-formed DWARF container) | 合成；源 bad-a64-end.s | 同名命令组 / T-A64 | 5912 | `c3512d7ee145f8355defee594b7440d3bb17e7708245aba8e4f5d15d5fe4bedb` |
| `bad-a64-end.s` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 621 | `68cbb4682cfd924db050fe103b98091a8664ed4b7433d5d31e5de56fc0c17d88` |
| `bad-a64-start.perfbin` | AArch64 | 5.7.2/5.10 boundary negative (well-formed DWARF container) | 合成；源 bad-a64-start.s | 同名命令组 / T-A64 | 5912 | `7906cba77182eec5c45e4c6986d975b016376ed07f552a9523602e091be5bd0f` |
| `bad-a64-start.s` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 625 | `cfe23c121aed7fa6d30d1f690afa5dc484f6bbef8eb4e0e4324387b5b9d8b5f1` |
| `bad-arm-start.perfbin` | ARM/Thumb；见 golden | 5.7.2/5.10 boundary negative (well-formed DWARF container) | 合成；源 bad-arm-start.s | 同名命令组 / T-ARM | 5592 | `df63f7bdb24a15b99d3d75b6672a183690d3a6ea27b5983a13333c0a06572fce` |
| `bad-arm-start.s` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 1582 | `166ee05d3d0d1c7aae8c305d15b2a475789cb73cdcf7239a22d61365b1e8e2a9` |
| `bad-conflict.perfbin` | ARM/Thumb；见 golden | 5.7.2/5.10 boundary negative (well-formed DWARF container) | 合成；源 bad-conflict.s | 同名命令组 / T-ARM | 5388 | `317924dd837164d3503dfb482d17e84aee82411e99063c70dd8deb6069a16f18` |
| `bad-conflict.s` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 633 | `59648d3c5c76631298fa1b1f46082e145f3f5763e454add84054d1cb0e583908` |
| `bad-no-map.perfbin` | ARM/Thumb；见 golden | 5.7.2/5.10 boundary negative (well-formed DWARF container) | 合成；源 bad-no-map.s | 同名命令组 / T-ARM | 5348 | `7536db5db1977d81c6f7529ffea75513446cb57a6be965847b30921184ac05e9` |
| `bad-no-map.s` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 570 | `497af692face93cc2128b990c1f22dbf78819848c166065132ea3c3e03466e52` |
| `bad-thumb-end.perfbin` | ARM/Thumb；见 golden | 5.7.2/5.10 boundary negative (well-formed DWARF container) | 合成；源 bad-thumb-end.s | 同名命令组 / T-ARM | 5592 | `46d629cebf6d89fff4ece21c700918094611046da05f529c7623b3124589c7a0` |
| `bad-thumb-end.s` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 1578 | `4d6e6e6bf983c30af09f921b37eef1590de3666c1268147b646b385fec7dfb24` |
| `bad-thumb-start.perfbin` | ARM/Thumb；见 golden | 5.7.2/5.10 boundary negative (well-formed DWARF container) | 合成；源 bad-thumb-start.s | 同名命令组 / T-ARM | 5592 | `4fedb8d6a3ec3ee6f166eaf2747a6d493244252245a123090f00a66fd3fb2ff2` |
| `bad-thumb-start.s` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 1582 | `2d7e0ab6159303775c1c7a14aec1e7a8bd70cd39d28f9043593cf43640bf4de5` |
| `boundaries.debug` | ARM/Thumb；见 golden | 5.7.2/5.10 hand-known ISA/mapping boundaries | 合成；源 boundaries.perfbin | 同名命令组 / T-ARM | 5528 | `2bc1e2753cb454a9dc0098c6d82911bd02f461538beeff826da6454523f6f3b2` |
| `boundaries.perfbin` | ARM/Thumb；见 golden | 5.7.2/5.10 hand-known ISA/mapping boundaries | 合成；源 boundaries.s | 同名命令组 / T-ARM | 5584 | `ec5ebb5145c9a429148ba08bdd0ef7c81ee0c04d70cdae312dd51810174c4c9b` |
| `boundaries.s` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 1578 | `7d637876e7d69e912330ed7891eff013ce60425d4d9071eb191811531f549a00` |
| `boundaries.stripped.perfbin` | ARM/Thumb；见 golden | 5.7.2/5.10 hand-known ISA/mapping boundaries | 合成；源 boundaries.perfbin | 同名命令组 / T-ARM | 4928 | `07f6a5734a3dde2e997193ce193e3f6ab18e72025a21cb32ca075c3f224a1471` |
| `boundary-after_data_a32.perfbin` | ARM/Thumb；见 golden | 5.7.2/5.10 hand-known ISA/mapping boundaries | 合成；源 boundary-after_data_a32.s | 同名命令组 / T-ARM | 5592 | `4213bcb10b7367de65afd0a9e1cabddb6e37b9bc09078577ba7f9cc83c89fa5c` |
| `boundary-after_data_a32.s` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 1583 | `b9b9d09cc753fff16e94f32c669e7d8537c25ed03d5298bfbc238986cdf85d3f` |
| `boundary-at_state.perfbin` | ARM/Thumb；见 golden | 5.7.2/5.10 hand-known ISA/mapping boundaries | 合成；源 boundary-at_state.s | 同名命令组 / T-ARM | 5588 | `77743102ef67d36db9b1ba1f40962355ad750bea3026bdcb8d14f05c7eef1c5d` |
| `boundary-at_state.s` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 1577 | `44386cb58fd212d63ecfd72c7892bc6c823c986679d6271345008bc4c0ad0622` |
| `boundary-before_state.perfbin` | ARM/Thumb；见 golden | 5.7.2/5.10 hand-known ISA/mapping boundaries | 合成；源 boundary-before_state.s | 同名命令组 / T-ARM | 5592 | `2605a81da10738f34e2df128958f7780baf2c9fc746a8429f3a597445ec7c48a` |
| `boundary-before_state.s` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 1580 | `19e32672cacb1e240ab1e75da687542d1e58988f8d4e4c68f5ab645c2f265c96` |
| `boundary-discontinuous.perfbin` | ARM/Thumb；见 golden | 5.7.2/5.10 hand-known ISA/mapping boundaries | 合成；源 boundary-discontinuous.s | 同名命令组 / T-ARM | 5600 | `db843e8b9f71e4361cdae95a9c659a396c124f07f8c95bd815df81728ccf74a5` |
| `boundary-discontinuous.s` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 1612 | `a3814fa410096221641b7a8325d3c2d644f40c0e152f45031046adfa2290d33e` |
| `boundary-golden.json` | 说明/golden | 5.3/5.7.2/5.10；复现与人工预期 | 本轮记录 | 手写/摘录；见素材说明 | 3549 | `3ea33f704b33d36ea0370e67a277cb25039870bd4440d72a10dd5c52f5790971` |
| `commands.txt` | 说明/golden | 5.3/5.7.2/5.10；复现与人工预期 | 本轮记录 | 手写/摘录；见素材说明 | 57792 | `cb6e52372c223e1a3e0ed030706f6de5db71a742f5194fdc502418fdafe20822` |
| `counting.c` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 755 | `738df4cf695b7c0f78f30bb0344e4339f56df46f3f7482422de7c6406ffc2b90` |
| `different.c` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 50 | `f62605e2c535c44a95ef593ba917d09dd08befa89e1860f09f08085ae2d0ad6a` |
| `multi-load.lds` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 473 | `5d0dea8ab8c4a9b40d5eab7db4a236bed7b4831c624ac8003e87d59401e2c926` |
| `multi-load.s` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 242 | `d7585362987ed31181e4ef283ca56954bd5f89c106ac2f8113d7b7f3f1b2a6b6` |
| `other/a64-pie.perfbin` | AArch64 | 5.3.2/5.3.3 identity mismatch / missing ID | 合成；源 different.c | 同名命令组 / T-A64 | 2992 | `37418b08b4d0da8045ebcc717a6ae97cc2609a38b8b8305d7c536d74909e3898` |
| `paired-addresses.json` | 说明/golden | 5.3/5.7.2/5.10；复现与人工预期 | 本轮记录 | 手写/摘录；见素材说明 | 1646 | `130c0f81c17b6c35e54a245ddd42edb3c2b95d67e4accdf610e17fcb176dd097` |
| `probe-debug.debug` | AArch64 | 5.1.4/5.10 probe section rejection | 合成；源 a64-probe.debug | 同名命令组 / T-A64 | 6872 | `a385632aa007bd4b712f7e76072143a49fc71dae8badfc47671baa38caca4812` |
| `probe-debug.perfbin` | AArch64 | 5.1.4/5.10 probe section rejection | 合成；源 a64-probe.stripped.perfbin | 同名命令组 / T-A64 | 2640 | `b59b9a6f70111da54df5cb7948cc3dab8e7a84a5ded3d37b54647dea11edd564` |
| `probe-desc-only.debug` | AArch64 | 5.1.4/5.10 probe section rejection | 合成；源 a64-probe.debug | 同名命令组 / T-A64 | 6256 | `327ccae5253107fefa6798e7fe17580f9e83ee8df93fa599d7e1649fe7ac52d9` |
| `probe-desc-only.perfbin` | AArch64 | 5.1.4/5.10 probe section rejection | 合成；源 a64-probe.perfbin | 同名命令组 / T-A64 | 2944 | `274ff8684dead5488852300854fc35ec1d5809312d6607cbc25718da3e91592c` |
| `probe-run.debug` | AArch64 | 5.1.4/5.10 probe section rejection | 合成；源 a64-probe.debug | 同名命令组 / T-A64 | 6256 | `327ccae5253107fefa6798e7fe17580f9e83ee8df93fa599d7e1649fe7ac52d9` |
| `probe-run.perfbin` | AArch64 | 5.1.4/5.10 probe section rejection | 合成；源 a64-probe.perfbin | 同名命令组 / T-A64 | 3208 | `2694f0f10e486e56b7fe05c7f66b2315c8c2233d50b41557a5b98a3244f92a9d` |
| `pure-a64.perfbin` | AArch64 | 5.7.2/5.10 hand-known ISA/mapping boundaries | 合成；源 pure-a64.s | 同名命令组 / T-A64 | 5912 | `12868b7bc185c73c712f528ba0fe66ef8db6b199250e51c117b9621fce144f92` |
| `pure-a64.s` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 618 | `11e994feebf1889b6a55ccb2bfe13b69375f94b2d3d3ec3b22c1d2df04698220` |
| `pure-arm.perfbin` | ARM/Thumb；见 golden | 5.7.2/5.10 hand-known ISA/mapping boundaries | 合成；源 pure-arm.s | 同名命令组 / T-ARM | 5372 | `6e01c948670736c31bab59d7877c36aca91fe08bef089d7b2cd767231c81b0b9` |
| `pure-arm.s` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 618 | `854a6c57f065a00a95a00171a15ecce380de5596c489997c33dea4cf7a23fc1e` |
| `real-deleted.perfscript` | perf 文本 | 5.2.2 / 5.3 | real: docs/probe/evidence/07/04_board.txt:623; exact line, no changes | 手写/摘录；见素材说明 | 112 | `fcc81c936c7daba68e0438e47ccc1807fe44b0d1a4c8a9b5823fa57c9ed3777e` |
| `real-empty-buildid.txt` | perf 文本 | 5.2.2 / 5.3 | real: docs/probe/evidence/05/02_perf_formats_mapping.txt:106; exact line, no changes | 手写/摘录；见素材说明 | 74 | `b70c35f676eb4808f504051aacf0f968f6841818b16ed83a3dc886aad80d7f20` |
| `real-kernel.perfscript` | perf 文本 | 5.2.2 / 5.3 | real: docs/probe/evidence/05/02_perf_formats_mapping.txt:292; exact line, no changes | 手写/摘录；见素材说明 | 73 | `c365c493edbffdfb888f31a91e743a50823c5f968bb2c371d099837a0ea7b025` |
| `real-lost.perfscript` | perf 文本 | 5.2.2 / 5.3 | real: docs/probe/evidence/06/04_lost_cleanup.txt:193; exact line, no changes | 手写/摘录；见素材说明 | 42 | `ac77ed492d3fd2e6ebb8a74d59b52a6d060981227ef5a6c77e6ac8e884ca5105` |
| `real-mmap2-buildid.perfscript` | perf 文本 | 5.2.2 / 5.3 | real: docs/probe/evidence/05/02_perf_formats_mapping.txt:719; exact line, no changes | 手写/摘录；见素材说明 | 142 | `0112b0528fcb8a302551752521b2e005730179157ce9835936d89e9276413634` |
| `real-mmap2-inode.perfscript` | perf 文本 | 5.2.2 / 5.3 | real: docs/probe/evidence/05/02_perf_formats_mapping.txt:288; exact line, no changes | 手写/摘录；见素材说明 | 121 | `ace6f5a54ac11fb302b92d0b453ae97a8897c8e35dc6bc5e23162fde73427b3c` |
| `real-module-mmap.perfscript` | perf 文本 | 5.2.2 / 5.3 | real: docs/probe/evidence/05/02_perf_formats_mapping.txt:278; exact line, no changes | 手写/摘录；见素材说明 | 127 | `f9252605b2d845fe9c2c7ad72b73539440ed2f4febfea6c73795f712ffc266f7` |
| `real-module-sample.perfscript` | perf 文本 | 5.2.2 / 5.3 | real: docs/probe/evidence/07/04_board.txt:756; exact line, no changes | 手写/摘录；见素材说明 | 118 | `744b772cb05bcade8a3c5da0e34568ef2f7520f3e9f749ceed73f10434297eb7` |
| `real-negative-pid.perfscript` | perf 文本 | 5.2.2 / 5.3 | real: docs/probe/evidence/09/02_sampling_formats.txt:902; exact line, no changes | 手写/摘录；见素材说明 | 74 | `481bd2d824e3d27bf00dd5b0a500e56cf7985236c1ffc3072ede7821f5d894ba` |
| `real-sample.perfscript` | perf 文本 | 5.2.2 / 5.3 | real: docs/probe/evidence/05/02_perf_formats_mapping.txt:398; exact line, no changes | 手写/摘录；见素材说明 | 97 | `3172922e4e2fe7b33ea9e53a4643507f7533cdd8b46870ce7104ba442141b3d2` |
| `real-vdso.perfscript` | perf 文本 | 5.2.2 / 5.3 | real: docs/probe/evidence/05/02_perf_formats_mapping.txt:724; exact line, no changes | 手写/摘录；见素材说明 | 69 | `0ce190ac0dfc17e5df7356dbd9233b3c82eaf9a6d455da5168b3fa2acecb40f1` |
| `section-adjacent.lds` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 67 | `e12c82acf5d846c624be2ffa0e5c2409bb4175d7f36f784d65a73f4ebe2acd96` |
| `section-adjacent.perfbin` | ARM/Thumb；见 golden | 5.7.2/5.10 hand-known ISA/mapping boundaries | 合成；源 section-state.s | 同名命令组 / T-ARM | 9356 | `a7c3d82354cdf81e484ccc2e1c5e353d74540cb3faa2cab9f63d0982eed6a763` |
| `section-same-address.lds` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 67 | `cd3a62d0cd2420519fa179915acd5b873ce366a174f7665f271bc251958e6c45` |
| `section-same-address.perfbin` | ARM/Thumb；见 golden | 5.7.2/5.10 hand-known ISA/mapping boundaries | 合成；源 section-state.s | 同名命令组 / T-ARM | 9352 | `78e4f26075616d7c39fef277760c4c0ba125b988947b70611ac982279b994c15` |
| `section-state.s` | 源/链接脚本 | 5.3/5.4/5.7.2/5.10；对应同名或清单中的 ELF | 手写合成 | 手写/摘录；见素材说明 | 703 | `1f7fc0e7a1c15762ba766c64dacb342850fcaa4094de833a0d9213e5d80c09f3` |
| `synthetic-event-modifier.perfscript` | perf 文本 | 5.2.2 / 5.2.3 / 5.10 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output | 手写/摘录；见素材说明 | 62 | `2c09b73cd094a2b5463298331076f243b5ed4340c4b58b2883f841e352a1b636` |
| `synthetic-invalid-pid.perfscript` | perf 文本 | 5.2.2 / 5.2.3 / 5.10 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output | 手写/摘录；见素材说明 | 60 | `4ffed7926a933f9d76ab9c68427ab6e30ef845d7b139df18ee4d8e4b23f3e18b` |
| `synthetic-invalid-tid.perfscript` | perf 文本 | 5.2.2 / 5.2.3 / 5.10 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output | 手写/摘录；见素材说明 | 60 | `8dc24aa4d10d8315afcb04a4966aeec37e975e06c937b4ba5bcec848c50e4b3e` |
| `synthetic-missing-dsoff.perfscript` | perf 文本 | 5.2.2 / 5.2.3 / 5.10 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output | 手写/摘录；见素材说明 | 53 | `af9abe3d3512eeb0cd401a55163fac8d625b4732a3fa4f1e1978da9ae1f1e6b5` |
| `synthetic-multiple-events.perfscript` | perf 文本 | 5.2.2 / 5.2.3 / 5.10 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output | 手写/摘录；见素材说明 | 119 | `bfd5185e1c734af480504ffb83297806fbafca1e5cf9c45240dbd76d646f123d` |
| `synthetic-path-parentheses.perfscript` | perf 文本 | 5.2.2 / 5.2.3 / 5.10 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output | 手写/摘录；见素材说明 | 75 | `24b9fe2e42e51a57b9043e94e7de2a724ff9ef929949918f2e9dd1f008652f53` |
| `synthetic-path-plus.perfscript` | perf 文本 | 5.2.2 / 5.2.3 / 5.10 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output | 手写/摘录；见素材说明 | 68 | `12836842e60a70a760516453a00a36133125415ada30ca16af32d28197a964e3` |
| `synthetic-path-spaces.perfscript` | perf 文本 | 5.2.2 / 5.2.3 / 5.10 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output | 手写/摘录；见素材说明 | 71 | `fb8d107e8f02071f885c0594c829b43b8894238f74410274a25abce016caadfd` |
| `synthetic-truncated.perfscript` | perf 文本 | 5.2.2 / 5.2.3 / 5.10 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output | 手写/摘录；见素材说明 | 58 | `c349f77064e1369125659d6d12716cc97b2ce4872d0a75f54a7e9e541efda714` |
| `synthetic-unknown-line.perfscript` | perf 文本 | 5.2.2 / 5.2.3 / 5.10 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output | 手写/摘录；见素材说明 | 26 | `0f5c62e1d3886e135d52a426a14bb1853e5703cb2d3d91d9f65ab3c0f2d3ee63` |
| `synthetic-unknown.perfscript` | perf 文本 | 5.2.2 / 5.2.3 / 5.10 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output | 手写/摘录；见素材说明 | 44 | `43022805660cf9502c5c0b17b9cea5c65771a0456cca84600f13aebf7bc6ff2e` |
| `synthetic-with-brstack.perfscript` | perf 文本 | 5.2.2 / 5.2.3 / 5.10 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output | 手写/摘录；见素材说明 | 84 | `7017f7f8067daa635a7c0aea41db40116e769b4d1e1594dea6f5ab186972db89` |
| `synthetic-zero-period.perfscript` | perf 文本 | 5.2.2 / 5.2.3 / 5.10 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output | 手写/摘录；见素材说明 | 54 | `e70f8723ad1c691b436f4b6a43469dff8fe259c0f05c157ac049e57a7b720ac8` |
| `thumb-count.debug` | Thumb | 5.3.4/5.7.2 split-debug equivalence | 合成；源 thumb-count.perfbin | 同名命令组 / T-ARM | 4908 | `daa88acd1bb13a573b4a53cd3ff8ef897f9360e345713491c855ee76e3786856` |
| `thumb-count.perfbin` | Thumb | 5.4/5.10 unroll, two inline call sites, nested inline; 5.7 ISA | 合成；源 counting.c | 同名命令组 / T-ARM | 4960 | `3de2b6621e572b26123638d8127d375374ccd9bc52a240ebc5b8e90391ce0230` |
| `thumb-count.perfscript` | perf 文本 | 5.3.1 / 5.7 | synthetic: src/linux-rpi/tools/perf/builtin-script.c:833,2271-2279,2324-2340; util/map.c:472-486 (v6.12.80); malformed cases intentionally violate this grammar, not claimed perf output; p_offset=0x000298, p_vaddr=0x00001298, off=0x344 => VA=0x1344 | 手写/摘录；见素材说明 | 69 | `e5f80ef2d3d42ffa5f09ded03aec4d76fdfdc912b67b6193a7b410dc1d908084` |
| `thumb-count.stripped.perfbin` | Thumb | 5.3.4/5.7.2 split-debug equivalence | 合成；源 thumb-count.perfbin | 同名命令组 / T-ARM | 1956 | `10d67bb418ffe9079424deb2d060bb514d010650a5bd7b9e16cd4dc7dfd3efcf` |
| `thumb-no-attributes.perfbin` | Thumb | 5.7.2/5.10 hand-known ISA/mapping boundaries | 合成；源 thumb-count.perfbin | 同名命令组 / T-ARM | 4812 | `215cc0eb67daf8303573d3dc15d08a0f093b4d05a22427700fe367a84234f136` |
| `tools.txt` | 说明/golden | 5.3/5.7.2/5.10；复现与人工预期 | 本轮记录 | 手写/摘录；见素材说明 | 7767 | `73fb813ff27b05ecec8dd3b26db9cba764d6b313b6f4da2110ea44e5084800ee` |

## 4. 已知边界、配套地址与验证限度

`boundaries.s` 的 `.text` 从 0x1000 开始，下表是人工 golden；GBS objcopy 导出的原始字节与写入的十六进制序列完全相同。readelf 验证映射符号的类型/绑定/所属节，dwarfdump 验证各 DWARF 容器合法。原始输出见 [ELF 检查](evidence/01/05_elf_inspection.txt)，断言结果见 [素材验证](evidence/01/04_fixture_checks.txt)。

| 相对 .text 偏移 | 内容 | 长度/状态 |
|---|---|---|
| 0 | Thumb NOP；`$t.1` | 2 |
| 2 | MOV.W | 4 |
| 6 | IT EQ | 2 |
| 8 | IT 块内指令 | 2 |
| 10 | TBB | 4 |
| 14–17 | `$d.literal`，`00 bf 00 bf`，误当代码可解成合法 NOP | 数据，不计指令 |
| 18 | `$t.hot`，TBH | 4 |
| 22–23 | `$d.table` | 数据，不计指令 |
| 24、28 | `$a.arm`，A32 mov/bx | 各 4 |
| 32、34 | `$t.tail`，Thumb NOP/bx | 各 2 |

完整已知起点为 `0,2,6,8,10,18,24,28,32,34`。另有纯 A32 `$a`、纯 AArch64 `$x` 与 A32 literal pool（数据字 `e1a00000` 恰为合法指令）。

| 专用素材 | DWARF 范围/人工预期 |
|---|---|
| boundary-before_state | [0x1002,0x100a)，起点 0x1002/0x1006/0x1008；最近 `$t` 在函数前 |
| boundary-at_state | [0x1012,0x1016)，起点 0x1012；映射符号与函数同址 |
| boundary-discontinuous | [0x1002,0x1006) + [0x1022,0x1024)，起点 0x1002/0x1022；前缀 0x1020 只证明边界，不计入函数 |
| boundary-after_data_a32 | [0x1018,0x1020)，起点 0x1018/0x101c |
| bad-thumb-start / bad-thumb-end | 起点/终点 0x1004 切进 0x1002 的 32 位指令；拒绝 |
| bad-arm-start / bad-a64-start | 0x101a / 0x1002 不按 4 字节对齐；拒绝 |
| bad-a64-end | 0x1006 截断指令；拒绝 |
| bad-conflict / bad-no-map | 同节同址 `$a/$t` 冲突 / 无起始映射；启用边界功能时拒绝 |
| section-adjacent | `.plt` 的 `$d` 止于 0x1004；`.text` 的 `$t` 从 0x1004 起，状态不可跨节继承 |
| section-same-address | `.plt/.text` 故意同址 0x1000，各自不同状态；用于节分组单元素材 |

最后一种使用显式 `--no-check-sections`，只验证按节区分状态，**不是唯一 PT_LOAD 归属的正向端到端输入**。边界专用手写 DWARF 只提供函数范围，不提供行级 profile 所需的完整行表；后续边界单元测试与 C 素材的行计数集成测试应分别使用。本轮只准备素材，未宣称尚未实现的 IP 模式已经通过这些测试。

多可执行段的共享库：RX 段 `(p_offset,p_vaddr,p_filesz)` 分别为 `(0x1000,0x10000,8)`、`(0x2000,0x30000,8)`。手算 `vaddr=p_vaddr+(off-p_offset)`：

| 文件 | dsoff | 预期 ELF VA |
|---|---|---|
| a64-multi-load | 0x1000 / 0x1004 | 0x10000 / 0x10004 |
| a64-multi-load | 0x2000 / 0x2004 | 0x30000 / 0x30004 |
| a64-multi-load | 0x1800 | 无可执行段；落段失败 |
| a64-pie | 0x3f4 | 0x13f4；RX offset=0x2f0、VA=0x12f0 |
| a64-16k | 0x4a4 | 0x44a4；RX offset=0x3a0、VA=0x43a0 |
| a64-64k | 0x4a4 | 0x104a4；RX offset=0x3a0、VA=0x103a0 |
| thumb-count | 0x344 | 0x1344；RX offset=0x298、VA=0x1298 |
| arm-count | 0x39c | 0x139c；RX offset=0x298、VA=0x1298 |

16K/64K 素材的实际 PT_LOAD 对齐分别为 0x4000/0x10000。配套 `.perfscript` 与 `paired-addresses.json` 随补丁提交；没有用页掩码计算偏移，也没有对样本地址清 Thumb 位（只在静态符号定位时解释符号状态位）。

身份与拆分：五套原始/strip-all 运行文件/only-keep-debug 文件的 build-id 完全相同，调试文件代码节为 NOBITS。SHA1 为 20 字节，`a64-fast` 明确用 **lld `--build-id=fast`** 得到 8 字节 ID。去 note 的同文件、仅运行文件有 ID、仅调试文件有 ID、两者均无 ID、同名不同内容不同 ID 均可由清单组合；对应配对见素材说明。

probe 的三对素材显式用 objcopy keep/remove 构造“两节仅运行文件”“两节仅调试文件”“只剩 desc”；不能据此宣称 Tizen RPM 实际拆分位置挂账已关闭。FS 素材有非零 FS discriminator，标记在原始及 debug `.symtab` 中；此例 strip 后标记还保留在 `.dynsym`，不声称覆盖“运行文件所有符号表均无标记”。

计数素材有强制 4 倍展开、两处 middle 内联、各自两层 leaf 内联；[GBS dwarfdump 原文](evidence/01/11_counting_dwarf.txt)实际有 6 个 inline DIE，middle 的调用行分别为 16/17。没有实际执行的计数值；后续人工计数需按设计 duplication factor 处理，不能用本轮构造替代 profile 质量验收。

真实文本素材来自证据 05–09，逐片段记录原文件:行号且不改原文；合成文本按本地 perf 6.12.80 源码格式手写。`([unknown])` 标明源码推导，截断行/period=0/pid 或 tid 小于 -1 等只在所列负对照中使用，不伪称板上输出。没有把 LOST_SAMPLES 加成受支持的正例。

## 5. C1 比对基线

脚本：[tools/profgen/c1_baseline.py](../../../tools/profgen/c1_baseline.py)。清单：[c1-baseline.json](../../../tools/profgen/c1-baseline.json)。[逐命令完整 stderr](evidence/01/06_c1_stderr.txt) 保留原文；清单记录原 RUN、来源行、展开后 argv、cwd、格式、退出码、profile 字节数与 SHA、stderr SHA、stdout SHA。将 `command` 首个 `llvm-profgen` token 替换成顶层 `launch_prefix` 即为实际完整命令（loader 路径与库同 00 报告 4.3）。不对测得字节做路径替换或其他归一化。

扫描范围是现有 `lit.local.cfg` 的全部四种后缀 `.test/.ll/.s/.yaml`，递归排除 Inputs；50 个测试中抽出 127 条 llvm-profgen RUN。展开 `%S/%s/%p/%T/%t`，拼接续行；去除后续 FileCheck 管道、shell 重定向与 `not` 包装，记录工具真实退出码。执行必要的 echo/cp/mkdir、GBS 工具 yaml2obj/llvm-objcopy/llvm-dwp 准备步骤，跳过 FileCheck/diff/llvm-profdata 的结果检查；未知 shell 语法直接失败，不静默跳过。没有执行 lit 的 XFAIL/REQUIRES 判定，故这不是 lit 通过率。

每条原样运行，再追加 text/extbinary/gcc/binary 四种格式。binary 固定对全部命令重放，是 C1 的超集：普通非 CS、非 probe 的格式覆盖之外，CS/probe 或诊断路径只多记录拒绝/提前退出行为，不将其当作支持 binary 输出的证据。固定矩阵避免新工具改变输出类型时测试范围自动缩小。gcc 仅用作行为对照，不能将退出 0 或存在文件认定为写出了 gcc profile。

**127 条原命令 + 508 条格式变体 + 1 条纯 IP 负对照 = 636 次/遍；两遍共 1,272 次，全部一致。** 另对两遍归档的 stdout/stderr/profile 做实际 bytes 比较，结果见 [摘要](evidence/01/10_c1_summary.json)。没有观察到非确定输出，不隐藏失败。

| 运行类别 | 次数/遍 | 退出 0 | 退出 1 | 非空输出文件/流数（不等同有效目标格式） |
|---|---:|---:|---:|---:|
| original | 127 | 120 | 7 | 112 |
| text | 127 | 120 | 7 | 111 |
| extbinary | 127 | 120 | 7 | 113 |
| binary | 127 | 69 | 58 | 62 |
| gcc | 127 | 30 | 97 | 23 |

原样命令的 7 个失败逐条如下（完整 stderr 在证据中）：

| 测试:RUN 行 | 原因/范围 |
|---|---|
| afdo-with-vtable-pie.test:8 | 原测试 `not` 负对照，data-access 不支持 context-sensitive trace 或 pseudo-probe 映射组合 |
| afdo-with-vtable-pie.test:13 | 原测试 `not` 负对照，data-access 不支持 context-sensitive trace 或 pseudo-probe 映射组合 |
| afdo-with-vtable.test:7 | 原测试 `not` 负对照，data-access 不支持 context-sensitive trace 或 pseudo-probe 映射组合 |
| afdo-with-vtable.test:11 | 原测试 `not` 负对照，data-access 不支持 context-sensitive trace 或 pseudo-probe 映射组合 |
| cs-preinline-cost.test:3 | 测试 REQUIRES asserts；当前工具 assertions=No，拒绝 debug-only 参数 |
| cs-preinline-cost.test:6 | 同上，保留真实失败，不模拟 assertions 构建 |
| invalid-perfscript.test:1 | 原测试标记 XFAIL:*；当前 reader 报 Invalid perf script input |

gcc 的 30 个退出 0 包含 raw profile、只反汇编、skip-symbolization 等不经过 sample writer 的路径；其余 97 个实际退出 1。binary 的 CS/probe 写出错误亦原样保留。`profile_sha256=null` 表示没产生可读取输出；空文件的 SHA 为真实空文件 SHA，不能混为无输出。两个原有 `/dev/null` 目标保留为系统空设备（非项目文件），其命令在参数解析失败后退出。

纯 IP 负对照使用 05 证据中 20 条原始样本（具体行号在清单），配已知可读的原有 x86 ELF，避免先被 ARM 支持限制挡住；没有新选项。两遍退出 1、无 profile，stderr 原文（末尾有换行）：

```text
llvm-profgen: error: Invalid perf script input!
```

后续每个补丁重跑（先在既定环境构建候选工具；下列命令本身不构建）：

```bash
cd /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent
export TMPDIR="$PWD/temp/tmp"
nice -n 19 ionice -c3 python3 tools/profgen/c1_baseline.py --expected-tool-sha '' --manifest temp/profgen-c1-candidate.json --compare tools/profgen/c1-baseline.json
```

默认工具路径保持 `temp/llvm-profgen-enh/build/bin/llvm-profgen`；scratch 路径必须保持相同，避免绝对文件名改变 stderr。新清单写入 temp，已提交基线不覆盖。比较范围为 test/行/格式、profile SHA、stderr SHA、退出码，stdout 同时存档但 C1 的 help/version 不作候选输出承诺。读取既有纯 IP 的行为同样参与比较。若矩阵数量、原测试内容或工具环境改变，先说明原因，不能直接替换基线。

profile、每遍原始 stderr/stdout 仍在 `temp/profgen-c1-baseline/pass1/`、`pass2/`，不提交。开发重放器早期曾拒绝含 shell 检查链的准备行及 `/dev/null` 目标；修正的是项目重放器，未改 LLVM，早期日志留在 `temp/profgen-patch1/c1-run-attempt*.log`，最终基线只采用最后完整两遍。最终固定矩阵前的 556 行试跑与复查亦保留日志，统计不与最终 636 行混用。

## 6. lit 可运行性（未补建）

[工具/配置盘点](evidence/01/07_lit_inventory.txt)：`llvm-lit`、FileCheck、not、count、yaml2obj、llvm-objcopy、llvm-dwp、llvm-profgen、llvm-profdata 都存在；**缺 `build/test/lit.site.cfg.py`**。CMakeCache 的 `LLVM_INCLUDE_TESTS=OFF`、`LLVM_BUILD_TESTS=OFF`，assertions=No；已有 site configs 全属于 OpenMP，不能拿来运行 LLVM/profgen 套件。

按本轮要求没有运行 lit，没有构建、重配或改 spec。因此 PASS/FAIL/UNSUPPORTED 数量为“未取得”，不是 0/0/0，也不能把 RUN 重放结果当成 lit 全通过。C1 的完整验收仍需后续补齐 lit 环境；新素材此轮没有 RUN，不存在新功能通过率。

最小补齐建议（未执行）：在同一 GBS x86_64 root、同一 worktree/build 和原有 CMake 参数基础上，改本地构建配置为 `LLVM_INCLUDE_TESTS=ON` 生成 LLVM site config；无需开启全部单元测试构建。当前辅助二进制齐全，先尝试只生成配置与运行 profgen 目录；若缺目标再仅构建 `llvm-profgen FileCheck not count yaml2obj llvm-objcopy llvm-dwp`。估算配置 1–5 分钟，缺失小工具目标补建 5–20 分钟（缓存/机器负载会影响；未测量）。启用 assertions 的行为另需相应工具构建，不能冒充现有基线。

CMake/测试命令对已有可写 build 目录本身不要求 sudo；进入 GBS buildroot/chroot 或经 depanneur 调用的平台步骤可能需要 sudo，须按现有 sudo 配置由用户执行。此轮没有调用任何 sudo，也没有索要密码。不能直接在主机用缺失平台库的辅助工具替代上述环境。

## 7. 交付状态与剩余事项

没有发现冻结规则无法构造素材的情形，未改设计。已知限制分别记录：同址多节只作边界单元输入；无行表手写 DWARF 只作函数边界输入；objcopy 的 probe 组合不是平台真实拆分证据；assertions 测试当前只基线化错误行为；lit 配置缺失，尚未验收整套 lit；本轮未新增外部 perf/板上集成验证。

`[unknown]` 源码格式素材本轮已补。新 LLVM 默认 build-id、aarch64 Tizen debuginfo 的 `$x/$d`、真实 probe 拆分位置、DWARF5 与 BUILD 产物 ID 证据仍按 STATUS 挂账，不由合成素材替代。下一步等待补丁 2 授权；Agent 设计与开发仍在 llvm-profgen 增强完成后。

生成脚本、对象、完整 readelf/dwarfdump JSON 等大中间文件留在 `temp/profgen-patch1/`；正式报告和证据中的单文件均小于 1 MB。边界例外：无新增项目文件边界例外；没有访问 Downloads、开发板或其他外部项目输入。
