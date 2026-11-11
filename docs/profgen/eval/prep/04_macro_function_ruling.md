# 裁决1修正、裁决2及补充1：静态身份核对（宏实参位置停止）

## 1. 当前状态与提交

- 裁决1修正已提交推送：f8f141f1767d77fe2ebbba56c5962c8237cadb4d。
- 裁决2原文已先提交推送：099a78ce1e858666b23cfa2fd79537d6e58289d9。
- 裁决2补充1已先提交推送：0c603bde8312fea2f8887638550dfdf10e138285。
- 原文见[rulings.md](rulings.md)。不改设计、不改LLVM，不连接板子；未打开任何正式sample profile、CALIBRATION原件或其量。修订3未登记。
- 本轮停止于补充1③的AST语句拼写位置条件：宏实参自身的拼写位置不在覆盖主文件，不能擅自忽略。等待用户裁决，不进入U/③。原规则全部候选核对尚未完成，不把未做的检查报告为通过。

## 2. 裁决1修正与复核

apply_header_ruling.py不再把clang_v_verified、coverage_disabled_verified、skip_source_verified设为常量。recheck_header_evidence.py读取保存的逐侧-v真实退出码、stderr SHA与搜索目录、实际命令数组及源码条件，重新写入header-evidence.json的每对象S/C记录。proof_from_record要求两侧每项都是布尔true；任一缺失、false或非布尔值均不放行。

11项测试通过。新增测试对真实header-evidence.json的内存副本逐对象、逐侧删除或置假三字段，再经JSON序列化/读取路径分类；所有原已闭合系统头记录均变为未决，原文件不被测试篡改。完整重跑结果spike各2、FFmpeg Thumb1236、A321242，与修正前一致。

证据：evidence/ruling1-fix-evidence/、ruling1-fix-tests/、ruling1-fix-apply/count-comparison.json；三个标志与原始证明路径在evidence/ruling1/header-evidence.json。旧artifact-sha256.json是历史快照；本轮manifest另存。

## 3. PGO basename来源与显式映射

LLVM22.1.8源码：

- clang/lib/Driver/ToolChains/Clang.cpp:5447–5448设置-main-file-name；:8532–8535的getBaseInputName调用sys::path::filename。
- clang/lib/CodeGen/CodeGenPGO.cpp:39–44将CodeGenOpts.MainFileName传给getPGOFuncName。
- llvm/lib/ProfileData/InstrProf.cpp:303–323：内部链接函数的名字是FileName + ':' + linkage name。

因此实际命令的输入libavcodec/arm/hpeldsp_init_arm.c产生hpeldsp_init_arm.c:前缀。不是路径规范化丢目录，也不是按同名猜测。完整源码摘录：evidence/ruling2/basename-source.txt。

evidence/ruling2/ffmpeg-{thumb,a32}-prefix-map.json逐项保存前缀、完整CU、命令日志路径/行号/原文、完整linkage、C与S最终ELF有代码DIE证据。只在命令与最终库CU/代码定义有联系时登记；多个同basename的CU须用完整linkage（含.__uniq.）唯一消歧。本轮34/34两侧均通过。名字后缀未删掉后再比较。

## 4. 宏AST：取得的证据与不能闭合的原因

### 4.1 AST重现方法

以每个C构建日志的实际编译命令为基础，只删除-c/-o和依赖文件写出选项，改为-fsyntax-only及AST导出；所有-D/-U、ISA、优化、插桩与coverage参数保持。Clang与加载器来自FFmpeg GBS root；sysroot/resource-dir重定位到WORKDIR内，不读取主机头文件。

使用temp/eval-prep11/ffmpeg原评估源码、temp/eval-prep11/build/ffmpeg-<模式>-C/config.h、对应libavutil-devel RPM里的avconfig.h。config_components.h逐宏对照本次C构建保存的config.mak中CONFIG_*或!CONFIG_*=yes，全部一致才使用；证明及SHA在<模式>-config-components.json。前置头目录仅用于找回生成头；源码目录优先于devel公共头目录。

Thumb与A32各5个CU的AST最终全部退出0。完整生成命令、源/配置/编译器SHA、AST路径/SHA保存在evidence/ruling2/{thumb,a32}-ast4-commands.json；大AST留temp/prep-ruling2/*.ast4.json。原始失败也保留：debugsource RPM缺所需源码；第一次头路径排列选中了devel common.h；缺config_components.h；随后按上文修正重现驱动。它们是证据准备脚本问题，不是原C构建失败或OOM。三个失败未改变构建产物。

### 4.2 逐项核对

| 每个FFmpeg对象 | 数量（有代码DIE） |
|---|---:|
| 需裁决的宏函数 | 34 |
| TU前缀映射及完整linkage通过 | 34 |
| S/C定义声明文件、行号一致 | 34 |
| 覆盖在decl_file中无代码区域，代码全部在pixels.h | 34 |
| AST语句范围有不在pixels.h的端点 | 34 |
| 本轮宏函数闭合 | 0 |

C侧有14个条目的函数只留下内联代码；声明位置通过其抽象来源解析，不能因没有独立带代码subprogram就误判不同定义。首次审计只看C独立subprogram得到20/34，这个脚本漏项已修正为全部代码DIE，第二次34/34；两次执行记录均保存。

完整列表：ffmpeg-{thumb,a32}-macro-audit.json。所有记录FNDA=0，但不因此免除身份门禁，不把它们自动归为参考侧未执行。

### 4.3 完整例子与待裁决点

示例ff_put_pixels16_x2_arm，源码调用在libavcodec/arm/hpeldsp_init_arm.c:38；CALL_2X_PIXELS定义在pixels.h:34，转到CALL_2X_PIXELS_MACRO（pixels.h:26–32）。AST原文：

```text
CallExpr <libavcodec/arm/hpeldsp_init_arm.c:38:48, ./libavcodec/pixels.h:30:34>
CallExpr <libavcodec/arm/hpeldsp_init_arm.c:38:48, ./libavcodec/pixels.h:31:42>
IntegerLiteral <libavcodec/arm/hpeldsp_init_arm.c:38:78> 'int' 8
```

函数体调用语句的第一个token是宏实参ff_put_pixels8_x2_arm；其拼写位置在展开处，而括号、参数及语句结构来自pixels.h。JSON中的expansionLoc.isMacroArgExpansion=true；token导出也明确给出Spelling=hpeldsp_init_arm.c:38:48。两次独立的AST/token查询退出0。

原文：macro-example-ast.txt、macro-example-tokens.txt（保留完整token流行号）；完整JSON例子：thumb-example-ast-expanded.json、thumb-example-coverage.json；命令：macro-example-commands.json。

每侧6个直接宏函数共12个这样的语句端点来自decl_file；另外28个函数共56个端点来自token-paste的<scratch space>；全部被AST标为isMacroArgExpansion。完整中间宏链的正面验收尚未闭合，不能仅凭文本搜索宣称证明完毕。

需裁决：是否仅允许AST明确标记为宏实参展开的位置来自展开处/拼接缓冲，同时仍严格要求非实参的语句结构、运算符与覆盖代码区域在主文件。当前没有采用该候选规则。按补充1③文字及负例，混合拼写位置不能直接满足正例；原普通规则又是同名异文件，仍未决。

18项规则辅助函数夹具通过（原裁决11项、补充7项，含两层链、定义不符、无AST、语句在decl_file、basename多CU与链接证据缺失）。两层链夹具使用明确标为合成的AST位置结构，仅验证判定逻辑，不能替代真实宏链的编译器证据。证据：evidence/ruling2-tests/stderr.txt。生产宏审计没有用这些合成证据闭合任何真实函数。

## 5. GNU外部CU来源

保留GBS root内归档：temp/GBS-ROOT-V04-FFMPEG/local/BUILD-ROOTS/scratch.armv7l.0/usr/lib/gcc/armv7l-tizen-linux-gnueabi/14.2.0/libgcc.a。

SHA256：78574a3635978ec43b9b000cb083994ae6a8f5a5c96963f0a297d4369298e9dd。

平台llvm-ar t完整输出在libgcc-members.txt。10个成员为_arm_addsubdf3.o、_arm_addsubsf3.o、_divsi3.o、_dvmd_lnx.o、_fixdfdi.o、_fixsfdi.o、_fixunsdfdi.o、_fixunssfdi.o、_udivmoddi4.o、_udivsi3.o。每个成员通过平台llvm-ar提取、llvm-dwarfdump读取，原件与完整dump保留temp/prep-ruling2/libgcc/，SHA、命令及全部CU属性保存在external-cu-members.json。

每侧38个DIE（33 GNU AS、5 GNU C）均唯一匹配成员中的完整函数名、CU源文件与producer。CU源文件用comp_dir作词法解析；不存在参考候选，且不在覆盖文件表中。按原规则记not_instrumented，没有新增状态。

S实际链接命令的日志/行号、保留编译器默认库路径与-###结果在external-cu-register.json及ffmpeg-*-link-driver.txt。-print-libgcc-file-name选中的/lib/gcc/.../libgcc.a与上述/usr/lib/gcc/...归档经samefile确认同一文件。明确局限：历史链接命令含@response，原response未保留；-###检查以空response代替，仅确认该命令的编译器默认runtime与搜索路径，不冒充历史linker map。最终ELF的CU/函数与归档成员匹配作为链接来源的第二项正面证据。

## 6. 完整身份清单与停止范围

| 对象 | 系统头闭合 | 宏函数闭合 | not_instrumented | 原规则有候选待核对 | 宏实参位置未决 | 未决合计 |
|---|---:|---:|---:|---:|---:|---:|
| spike Thumb |2|0|0|15|0|15|
| spike A32 |2|0|0|15|0|15|
| FFmpeg Thumb |1236|0|38|26841|34|26875|
| FFmpeg A32 |1242|0|38|26876|34|26910|

数量单位为代码DIE，包含内联实例，不冒充独立函数数。macro34去重为30个定义身份；没有依据这一展示去重改变规则。原规则单候选闭合数与多候选歧义数本轮均**未验收**，不是0个实际对象，也不是默认通过；在宏条件需要裁决后未继续其全量定义/叶子行集合检查。完整行索引：ruling2/<对象>-inventory/index.json，逐行引用原完整清单和本次增量证据，未丢弃任何记录。

U、排除权重、①②③③′、n_eff、K、分桶损失、映射范围内系统头/宏函数的地址与字节统计均未计算。没有以身份未闭合的集合估计门槛，也没有声称③达标或不达标。

## 7. 资源与证据

全部任务串行、nice19/ionice idle、3G/200% user scope；任务通过≥4GiB启动检查。原文meminfo、scope实读峰值、命令、真实退出码、ALL-END见ruling1-fix-*与ruling2-*任务目录。资源摘要见ruling2/resources-summary.json；没有OOM、资源暂停或终止。最高峰值不是程序RSS，而是cgroup memory.peak（含子进程与缓存）。

本轮脚本与证据SHA索引：ruling2/artifact-sha256.json。单个提交文件小于1MB。边界例外：无；三个用户配置未读取、未修改、未暂存。

## 7. 裁决2补充2：逐token实测与停止（2026-11-10）

裁决原文已单独提交并推送 **56c7cc7a9b4a62f8a70b9ced1149fa6c1c4361db**，见
[rulings.md](rulings.md)。没有修改设计正文；仍未打开任何正式 sample profile，
未连接板子，未计算 U、③或其他受控量。

### 7.1 方法：直接读取API，不从AST节点推定token标志

标准 `clang -dump-tokens` 只输出kind、文本、位置等，不输出
`isMacroArgExpansion`（Preprocessor.cpp:236–261）；AST的节点位置不足以替代
每个token。新增Python驱动的外部取证插件
[compiler_token_evidence.py](../../../../tools/profgen_eval/compiler_token_evidence.py)，
使用GBS内的Clang/libclang-cpp 22.1.8、现有源码/生成头文件；没有修改或构建LLVM。

取证注册 `Preprocessor::setTokenWatcher`（Preprocessor.h:1355–1362）、
`PPCallbacks::MacroExpands`；对每个最终函数体token直接调用
`SourceManager::isMacroArgExpansion`、`getSpellingLoc`、
`getExpansionLoc`，保存逐层 immediate spelling/expansion、宏名和布尔值。
ASTConsumer同时记录函数体左右花括号的SourceLocation，按它们在最终token流中的
唯一位置截取整个函数体（包括花括号），不只检查AST语句端点。

每个实际宏展开实例通过**原始SourceLocation区间**与token的展开链关联；不能只按
宏名或file:line关联，因为同一template会在不同位深下重复包含。外层调用实参范围
取自MacroArgs的unexpanded tokens；宏定义体取自MacroInfo tokens，范围采用
首、末token起始offset的闭区间（不是把整行都视为合法实参）。每个宏定义位置还与
源码的对应 `#define` 行核对。原始位置绝不清洗成另一文件；scratch的真实
`getFilename` 为空、presumed filename为 `<scratch space>`，保留两者。

输入使用此前验证的五个CU、Thumb/A32各五条实际C编译命令及相同预处理定义。
原命令、日志行号与头文件重建依据仍见
`evidence/ruling2/{thumb,a32}-ast4-commands.json`；
本轮插件参数与真实退出码见
`evidence/ruling2/{thumb,a32}-token-api-commands.json`，十条最终命令均退出0。
原始AST与逐token JSONL留在 `temp/prep-ruling2/`；每份证据保存路径和SHA。
版本与源码原文见
[compiler-version.json](evidence/ruling2/supplement2/compiler-version.json)、
[compiler-source.txt](evidence/ruling2/supplement2/compiler-source.txt)。
未读取C/S编译以外的sample数据。

### 7.2 完整示例与实际结果

| 对象 | 待核宏函数DIE | 闭合 | 未决 | 每侧scratch token数 | 所有这些记录FNDA之和 |
|---|---:|---:|---:|---:|---:|
| FFmpeg Thumb | 34 | 6 | 28 | 56 | 0 |
| FFmpeg A32 | 34 | 6 | 28 | 56 | 0 |

闭合的六个名字为：
`ff_put_pixels16_x2_arm`、`ff_put_pixels16_y2_arm`、
`ff_put_pixels16_xy2_arm`、`ff_put_no_rnd_pixels16_x2_arm`、
`ff_put_no_rnd_pixels16_y2_arm`、`ff_put_no_rnd_pixels16_xy2_arm`。
完整linkage（含.__uniq.）、CU、声明位置、FNDA及对应结论见
[Thumb逐项表](evidence/ruling2/supplement2/ffmpeg-thumb-results.json)、
[A32逐项表](evidence/ruling2/supplement2/ffmpeg-a32-results.json)。
六个闭合记录均reference_unexecuted，不进入U/C；没有FNDA>0的闭合宏函数，
其评价域外已执行DA之和为0。FNDA为0**不能**替代身份核对，另外28个仍未决。

**直接调用实例** `ff_put_pixels16_x2_arm`：
`hpeldsp_init_arm.c:38` → `pixels.h:34 CALL_2X_PIXELS` →
`pixels.h:26–31 CALL_2X_PIXELS_MACRO`。
整个函数体28个token，其中24个拼写在pixels.h，4个跨文件token为
`ff_put_pixels8_x2_arm`两次（38:48）、`8`两次（38:78），
四个的API布尔值均为true，均在该次调用的实参范围内。补充2条件通过。
完整28-token表：
[example-01-all-body-tokens.tsv](evidence/ruling2/supplement2/example-01-all-body-tokens.tsv)；
含原始位置、完整trace、实参范围、宏定义源码、原始AST/token路径与SHA的完整证据：
[ffmpeg-thumb-01-tokens.json](evidence/ruling2/supplement2/ffmpeg-thumb-01-tokens.json)。

**PIXOP2两层链实例** `put_pixels16_x2_8_c`：
`hpeldsp.c:333 PIXOP2`（定义38–325）→
`pixels.h:34 CALL_2X_PIXELS` → `pixels.h:26–31 CALL_2X_PIXELS_MACRO`。
函数体28个token；24个在pixels.h，两个数字 `8` 拼写在hpeldsp.c:310:16，
isMacroArgExpansion=true且在已记录的PIXOP2定义体内，**这两个已按补充2通过**。
另两个 `put_pixels8_x2_8_c` 的实际拼写位置是
`<scratch space>:90:1`，isMacroArgExpansion=true，但不在允许的两类源码范围内。
因此整个函数仍未决。完整token表：
[example-18-all-body-tokens.tsv](evidence/ruling2/supplement2/example-18-all-body-tokens.tsv)；
完整证据：
[ffmpeg-thumb-18-tokens.json](evidence/ruling2/supplement2/ffmpeg-thumb-18-tokens.json)。

**DEF_PEL链实例** `put_pixels16_8_c`（h264qpel.c中的pel_template.c:78）：
38个body token；包含来自pel_template.c:72的中间宏实参和
bit_depth_template.c:79的pixel定义。所有非主文件token的宏实参标志均为true；
两个被调用名字 `put_pixels8_8_c` 拼写在
`<scratch space>:58:1`，未通过允许位置检查。
[完整38-token表](evidence/ruling2/supplement2/example-07-all-body-tokens.tsv)、
[完整证据](evidence/ruling2/supplement2/ffmpeg-thumb-07-tokens.json)。
其余28个未决DIE逐项也都保存完整token证据；没有仅用抽样代表全部函数。

### 7.3 为什么必须停下

28个函数每个都有两个token满足“宏实参=true”，却不满足补充2①的**拼写位置限制**。
这是Clang的真实token拼接表示，不能由本轮自行归入某个宏定义体：

- `src/llvm/clang/lib/Lex/TokenLexer.cpp:792–799` 将粘接后的文本通过
  `PP.CreateString` 放入scratch buffer；:817–819断言其原始位置为scratch。
- `src/llvm/clang/lib/Lex/Preprocessor.cpp:486–495` 中CreateString分配scratch位置。
- 原文与SHA已存 `compiler-source.txt`。SourceManager的macro argument标志并不保证
  最终拼写位置是物理源码文件。

按“任一正面证据缺失仍未决”的规则，判为
`argument_spelling_outside_allowed_ranges`，**没有新增闭合状态**。
用户要求的“DEF_PEL/PIXOP2真实两层链闭合”目前不能通过；这不是把预期改成通过：
规则夹具中“不含拼接、实参确实位于中间定义体”的正例通过，
真实拼接实例作为停止证据保持未决。宏参数的普通中间传递已支持，未授权的是
`##`生成的scratch拼写。

待人工裁决的候选方向：是否另立严格的token-paste来源证据规则，要求编译器证明每个
`##`操作数来自已允许的调用实参/定义体且拼接结果精确一致。**本轮没有实施该规则，
没有用trace或文本搜索替换真实spelling**。也可以继续将这些条目保留未决；
在完整身份门禁未闭合前不能计算U或③。

### 7.4 实现、夹具与完整清单

`macro_function_rule.py` 删除旧的“仅macro_definition_verified即可闭合”旁路；
必须具备compiler AST、逐token证据。缺少任一token的布尔标志即未决；
非实参拼写在decl_file时转原规则；实参位置超出调用范围/展开链定义体时未决。
`audit_macro_tokens.py` 用真实证据执行判定，保留原清单每个DIE，不用FNDA过滤身份。

[最终27项测试原文](evidence/ruling2-supp2-fixtures-final/stderr.txt)：27通过、0失败。
包含原裁决的TU/linkage/声明/唯一性/组范围，补充1的前缀唯一性/宏链/缺AST，
补充2的实参范围、第三文件、缺标志、非实参在decl_file、scratch拒绝；
另直接读真实证据检验ff_put实例闭合、两种真实拼接实例保持未决。
合成夹具均注明synthetic，不冒充编译器实测。
既有裁决1修复的11项夹具与闭合数沿用已验收结果；本轮未改该实现。

| 对象 | 裁决1已闭合 | 裁决2已闭合 | 外部CU已闭合 | 宏scratch未决 | 原规则候选核对未完成 | 未决总数 |
|---|---:|---:|---:|---:|---:|---:|
| spike Thumb | 2 | 0 | 0 | 0 | 15 | 15 |
| spike A32 | 2 | 0 | 0 | 0 | 15 | 15 |
| FFmpeg Thumb | 1236 | 6 | 38 | 28 | 26841 | 26869 |
| FFmpeg A32 | 1242 | 6 | 38 | 28 | 26876 | 26904 |

[完整闭合汇总](evidence/ruling2/supplement2/closure-summary.json)。
新的完整清单在同目录 `<object>-inventory/index.json` 及CSV分片，索引保存前版SHA，
所有原始属性与候选仍在原清单，不把“有候选”当作已闭合单候选。
原规则单候选/多候选歧义最终数量尚未验收；因新的scratch门禁停止，没有继续这些工作。
GNU外部CU每侧38、libgcc10成员的证据与上一节相同，本轮不重复构建或改变not_instrumented规则。
U、排除清单、对象登记表、③损失分解、映射范围内系统头/宏函数静态地址与字节数均未计算。

### 7.5 资源、失败记录与复现

全程串行，nice19/ionice-c3，systemd scope 3G/200%；启动前均≥4GiB。
本轮记录最低MemAvailable **8056033280字节（7.502766GiB）**，最高cgroup memory.peak **578240512字节（0.538528GiB）**，无OOM、无资源暂停/终止。

[资源汇总](evidence/ruling2/supplement2/resources-summary.json)；
每条run_scoped目录保留命令、原始meminfo、loadavg、stdout/stderr与ALL-END。
所有新增文件均小于1MB；原始大AST/token只留temp。

过程中的本地辅助代码失败如实保留：
1. 插件初稿JSON显式构造语法编译失败，修正后构建成功。
2. 插件初稿让Recorder随PluginASTAction销毁，callback引用失效导致崩溃；
   改为callback/consumer共同持有shared_ptr，最终十条命令成功。不是FFmpeg/LLVM缺陷；
   原始退出139诊断与保存路径见 `thumb-token-api-attempt1-commands.json`。
3. 一次shell引用错误，命令尚未执行，无文件更改；改用here-doc。
4. 首次打包证据重复保存tokens/完整callbacks，触发单文件1MB自检；
   改为token仅存一份、完整callback原文保留temp及SHA，仓库仅存必要位置与原文引用。
5. 按宏名/file:line筛链会混入同template其他包含实例；
   最终按原始展开区间ID精确关联，十份原始输出无需重跑，闭合数未改变。

最终生成命令（在WORKDIR内，外层统一nice/ionice/systemd scope；细节见对应command.json）：
```text
python3 tools/profgen_eval/compiler_token_evidence.py build
python3 tools/profgen_eval/compiler_token_evidence.py thumb
python3 tools/profgen_eval/compiler_token_evidence.py a32
python3 tools/profgen_eval/audit_macro_tokens.py
python3 -m unittest discover -s tools/profgen_eval -p test_macro_function_rule.py -v
python3 tools/profgen_eval/package_token_evidence.py
```
文件SHA与生成命令入口见 `evidence/ruling2/supplement2/artifact-manifest.json`。
边界例外：无项目输入/产出越界；未读取三项用户配置，未改LLVM源码、设计正文、认证。
系统工具及其systemd scope/cgroup运行记录属于既有资源限额机制。

## 8. 裁决2补充3：拼接来源证明与规则7停止（2026-11-11）

补充3原文与前提核验已先提交并推送 **d79e285**。本轮只读取静态源码、ELF/DWARF清单、
C覆盖参考及既有编译证据；没有打开正式sample profile、没有连接板子，也没有修改或
重编GBS Clang本体。

### 8.1 前提核验：通过，但GBS源码目录当前已卸载bind

GBS root 的 `home/abuild/rpmbuild/BUILD/llvm-22.1.8` 当前为空。首次直接读取该目录
下TokenLexer.cpp得到FileNotFoundError，没有伪称从空目录读到源码。
按00构建报告:17、47、155确认实际bind来源为 `temp/llvm-profgen-enh`；
其TokenLexer.cpp与 `src/llvm` 及提交f999bd406c0a70fe8107aa992164fe6945c5d46a中的
同一文件逐字节SHA一致：
`9c28632bf5d819bcc80d16e8a5138053cef359e0afeb1c714d4fc7ec067c20b4`。
没有执行挂载、GBS构建或改动源码。

`TokenLexer::pasteTokens`：
- :749保存初始左操作数的StartLoc；
- :895取最后一个右操作数token的起始位置EndLoc；
- :903–911将两者映射/回溯到当前MacroFID；
- :913–914调用createExpansionLoc，将scratch拼写与完整##表达式范围组合。
这支持补充3第2条要求的范围语义，E并非表达式结束后的地址。

[源码与SHA原文](evidence/ruling2/supplement3/compiler-source.txt)、
[前提核验记录](evidence/ruling2/supplement3/prerequisite.json)。

### 8.2 API取证扩展与边界

`compiler_token_evidence.py`仍是外部只读取证插件的Python驱动：
新增FileID、B/E的实际宏owner与immediate invocation range，
MacroExpands回调的name_location raw、MSVCCompat、MacroInfo::getParameterNum、
回调时复制的MacroArgs::getUnexpArgument tokens，以及各拼接前缀的Clang Lexer kind。
文本由Preprocessor::getSpelling取得，词法判断调用Clang Lexer与LookUpIdentifierInfo。
不以正则或宏名搜索替代拼接实例、片段或操作数来源。

本轮单独使用 `temp/prep-ruling2/token-api-supplement3/`，
未覆盖补充2的原始输出。Thumb/A32各五个CU命令退出0，编译参数与前轮实际C命令相同，
只增加插件取证字段。命令、raw输出路径/SHA与退出码：
`evidence/ruling2/supplement3/{thumb,a32}-token-api-commands.json`。

`inspect_token_paste.py`是**静态证明检查草稿**，不是已验收的新身份判定入口。
它按API原始位置找到唯一拼接层/宏实例、定义片段、形参槽与实参，检查逐级文本和kind，
递归保存子证明。没有接入 `macro_function_rule.py` 的正式闭合路径；
该文件本轮未改，补充2对物理文件token的判定保持原样。
原因是两个必过实例在规则7处均无法通过，不能先把规则扩大再宣布实现完成。

拼接会使最终token位置链不再携带所有实参展开细节，因此必须读取**已复制的实参token
自己的API位置链**。首轮检查遗漏了BIT_DEPTH这个实参依赖，报告过14个
`paste_argument_source_outside_chain`；修正检查器后，使用其实际
MacroExpands回调和raw展开区间补齐依赖（非文本推断），该额外原因全部消失。
首轮/最终输出均保留在 `paste-inspection/`、`paste-inspection2/`。
当前唯一停止原因是下述直接调用实参的FileID标志。

### 8.3 两个必过实例的逐层证明：1–6通过，7未通过

**PIXOP2：ffmpeg-thumb-18，put_pixels16_x2_8_c**

| 项目 | 实测 |
|---|---|
| 唯一拼接层 | 1层，immediate spelling为scratch FileID |
| X | PIXOP2，回调name_location raw=22758，B/E同FileID=17362 |
| 定义片段 | hpeldsp.c:309:16–26，`OPNAME ## _pixels8_x2_8_c` |
| 参数 | getParameterNum(OPNAME)=0；MacroArgs[0]恰好一个token `put` |
| 文本与kind | `put` + `_pixels8_x2_8_c` = `put_pixels8_x2_8_c`；各前缀及结果均identifier |
| **第7条失败** | `put`的raw=22765，FileID位置，spelling=hpeldsp.c:333:8，isMacroArgExpansion=false |
| 位置范围 | 确实处于该次调用实参范围，但不在coverage主文件pixels.h |

**DEF_PEL：ffmpeg-thumb-07，put_pixels16_8_c**

1. 外层X=FUNC3，invocation raw=2148574100，定义片段
   `a ## _ ## b ## c`，四个操作数分别是内层scratch `put_pixels8`、
   定义字面 `_`、BIT_DEPTH展开的 `8`、`_c`。
   文本精确拼成 `put_pixels8_8_c`，前缀均identifier。
2. 对a递归：X=DEF_PEL，invocation raw=1065185，定义片段
   `OPNAME ## _pixels8`；文本精确拼成 `put_pixels8`。
3. **递归最终失败**：MacroArgs[0]是直接调用的 `put`，
   raw=1065193，FileID位置，spelling=pel_template.c:78:9，
   isMacroArgExpansion=false；它在调用实参范围，却不在pixels.h。
4. b的 `8`：isMacroArgExpansion=true，spelling=h264qpel.c:26:19。
   通过实参自己的API位置链取得BIT_DEPTH定义体，来源检查通过。
   c的 `_c`：isMacroArgExpansion=true，位于bit_depth_template.c:102:38的链上定义体，
   来源检查通过。不是BIT_DEPTH或递归文本的问题。

完整逐层记录（含L、B/E、X、定义token、每个操作数完整位置链、拼接前缀、递归子证明）：
- [PIXOP2完整JSON](evidence/ruling2/supplement3/ffmpeg-thumb-18-paste-proof.json)；
  [逐层可读摘要](evidence/ruling2/supplement3/example-18-proof.txt)。
- [DEF_PEL完整JSON](evidence/ruling2/supplement3/ffmpeg-thumb-07-paste-proof.json)；
  [逐层可读摘要](evidence/ruling2/supplement3/example-07-proof.txt)。
- 第三个独立源码位置实例：[rv40dsp PIXOP2完整JSON](evidence/ruling2/supplement3/ffmpeg-thumb-33-paste-proof.json)，
  直接实参put在rv40dsp.c:265:8，raw=13657，同样false；
  [摘要](evidence/ruling2/supplement3/example-33-proof.txt)。

### 8.4 具体冲突与候选裁决方向

补充3第5(a)条要求复制**未展开**实参，直接写在调用处的实参因此仍是物理FileID。
`SourceManager.cpp:984–986`对非MacroID直接返回false；
`MacroArgs.h:78–81`注明getUnexpArgument返回未展开token。
宏实参展开位置稍后才由TokenLexer.cpp:1053、1090等位置创建。
代码原文已追加到 `compiler-source.txt`，与API实测相符。

按第7条“用该token自己的位置链按补充2规则”及“非实参须在coverage主文件”，
这类token必然失败，具体原因码：
**`paste_argument_nonmacro_outside_main`**。
没有把MacroArgs槽位证据等价成SourceManager标志true，也没有因为FNDA=0而跳过。

候选裁决方向（尚未实施）：仅对通过唯一X/形参槽取得的未展开实参，
允许“MacroArgs来源＋精确落在该次调用实参范围”作为额外来源证明，保留真实false标志；
其他来源、缺失证据、链外文件依旧拒绝。是否接受由用户决定。
本轮已提出此精确问题，未收到裁决前不改规则、不推进身份门禁。

### 8.5 全量结果、测试与未完成项

| 对象 | 检查记录 | scratch token | 新闭合 | 未决 | 原因码分布 | FNDA>0 |
|---|---:|---:|---:|---:|---|---:|
| FFmpeg Thumb | 28 | 56 | 0 | 28 | paste_argument_nonmacro_outside_main:28 | 0 |
| FFmpeg A32 | 28 | 56 | 0 | 28 | paste_argument_nonmacro_outside_main:28 | 0 |

未抽样；[全量汇总](evidence/ruling2/supplement3/paste-inspection-summary.json)，
逐项文件为 `ffmpeg-{thumb,a32}-paste-inspection.json`，每个函数都有独立证明JSON与SHA。

- 原27项测试文件未改，重跑27 PASS、0 FAIL，见
  [原文](evidence/ruling2/supplement3/original-27-tests/stderr.txt)。
- 两个规定的真实正例均FAIL；另一个独立来源实例同样FAIL。
  `record_paste_stop.py`实际以非零码1退出，没有把“正确识别停止原因”伪装成正例通过。
  [断言结果](evidence/ruling2/supplement3/real-example-assertions.json)、
  [退出码](evidence/ruling2/supplement3/required-real-assertions/result.json)。
- 新增11项合成夹具尚未实施/验收：在真实正例发现规则7冲突后停止；
  不声明补充3实现完成，也不声明真实例验收通过。
- 普通候选、U、①②③③′、n_eff、K、损失分解与静态代码规模未继续。
  新报告 [05_identity_gate_and_coverage.md](05_identity_gate_and_coverage.md)记录门禁现状。

### 8.6 资源与复现

所有执行串行、nice19/ionice-c3、systemd scope 3G/200%，启动前MemAvailable≥4GiB。
已记录最低MemAvailable 10861895680字节（10.115929GiB），最高cgroup memory.peak 633831424字节（0.590302GiB），无OOM或资源终止。

[资源原文与汇总](evidence/ruling2/supplement3/resources-summary.json)。
run_scoped目录逐项保存命令、开始/结束时间、meminfo、loadavg、真实退出码和ALL-END。
本轮所有任务不足60秒，均有起始资源快照。

复现入口（仍需外层nice/ionice/3G scope，见各command.json）：
```text
python3 tools/profgen_eval/compiler_token_evidence.py build
python3 tools/profgen_eval/compiler_token_evidence.py thumb
python3 tools/profgen_eval/compiler_token_evidence.py a32
python3 tools/profgen_eval/inspect_token_paste.py
python3 -m unittest discover -s tools/profgen_eval -p test_macro_function_rule.py -v
python3 tools/profgen_eval/record_paste_stop.py
```
最后一条在本轮证据下预期退出1，因为用户规定必须通过的实际正例未通过。
SHA清单：`evidence/ruling2/supplement3/artifact-manifest.json`。
没有新增已知项目文件边界例外，没有改动三项用户配置、认证或任何LLVM源码；
没有推送LLVM/Gerrit或llvm-optimize。


### 8.7 补充3修订1：正式闭合与验收（2026-11-11）

修订1已照录[裁决文件](rulings.md)，独立提交b17c93f。上面的停止记录保留。
本轮只用静态编译器/ELF/覆盖参考证据，没有读取正式sample profile。

实现：`compiler_token_evidence.py`在MacroExpands回调复制MacroArgs每个槽位的token，
用getSpellingLoc和Token::getLength给出半开区间、raw值、FileID、槽位号及调用实例；
没有搜索文本或逗号，也不使用所有实参的总范围。
`token_paste_rule.py`实现补充3第1–8条与修订1的三路来源判定；
`macro_function_rule.py`只在原补充2不允许的scratch token上调用此证明。
旧物理函数体token路径不变，证据缺失仍未决。
`apply_paste_ruling.py`真正调用classify_macro，未使用inspect草稿结果替代身份判定。

| 对象 | 本轮检查记录 | 新闭合 | 未决 | FNDA>0 | (i)MacroID操作数 | (ii)直接槽位操作数 | (iii)scratch FileID操作数 |
|---|---:|---:|---:|---:|---:|---:|---:|
| FFmpeg Thumb | 28 | 28 | 0 | 0 | 84 | 56 | 0 |
| FFmpeg A32 | 28 | 28 | 0 | 0 | 84 | 56 | 0 |

操作数统计按每次证明出现计数，包含递归子证明，不是去重地址数；定义体字面不在三类实参中。
每侧既有6条宏记录也重跑通过，宏对应合计34条。全部闭合的组范围角色均reference_unexecuted。
[全量摘要](evidence/ruling2/supplement3/rev1/macro-summary.json)、
[闭合总表](evidence/ruling2/supplement3/rev1/closure-summary.json)。

三个正例逐层证明：
- [thumb-18 PIXOP2](evidence/ruling2/supplement3/rev1/example-18-proof.txt)：
  OPNAME##字面，put来自hpeldsp.c:333第0槽，direct_unexpanded_argument_slot，保留false。
- [thumb-07 DEF_PEL](evidence/ruling2/supplement3/rev1/example-07-proof.txt)：
  FUNC3的内层scratch操作数递归到DEF_PEL，put来自pel_template.c:78第0槽走(ii)；
  8与_c走(i)，BIT_DEPTH与中间宏定义体的API链仍完整保存。
- [thumb-33 PIXOP2](evidence/ruling2/supplement3/rev1/example-33-proof.txt)：
  rv40dsp.c:265的put同样经唯一槽位证明。

每份摘要链接完整proof JSON（L、B/E、X、定义片段、操作数位置链、槽位raw/offset、文本比较、子证明）。
[真实断言](evidence/ruling2/supplement3/rev1/real-example-assertions.json)全部PASS，
record_paste_stop.py已改为正例断言，实际退出0；旧停止文件不覆盖。

测试：原27项文件不改，27/27通过；新增19项synthetic证据夹具通过（规定的①–⑮，加正式classifier接入、槽位缺证、跨FileID、物理函数体旧规则4项）。
真实正例另计3项。第一次新增夹具有1项因Python字典共享引用导致先触发另一拒绝条件，
修正为只篡改操作数spelling FileID后19/19通过；失败输出保留，未改生产规则迁就夹具。
命令、真实退出码、完整stderr分别见rev1/tests-initial、tests-paste、tests-paste-final、real-positive-assertions。

插件构建退出0；Thumb/A32各5个实际C编译命令退出0；未重编或修改Clang本体。
原始AST/token留在temp/prep-ruling2/token-api-supplement3-rev1/，
命令、大小、SHA在rev1/{thumb,a32}-token-api-commands.json；每个提交文件小于1MB。
资源串行3G/200%，nice19/ionice-c3，门禁≥4GiB；见rev1/resources-summary.json。
普通候选核对下一步进行，不把有候选当闭合。U及③尚未计算。


### 8.7.4 后续身份门禁（本轮补充）

补充3修订1验收提交为fd4b5b5。随后普通候选全量核对已完成，
没有剩余未决；但FFmpeg Thumb/A32的identity_ambiguous参考DA超过
v1.5规定的1%门槛。详细单候选行范围证据、必然损失分桶与未完成的U项目
见[05报告§5–7](05_identity_gate_and_coverage.md)。
这不是补充3证明失败，也没有按FNDA=0绕过任何宏证据。
