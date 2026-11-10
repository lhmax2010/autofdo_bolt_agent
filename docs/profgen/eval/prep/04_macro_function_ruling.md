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
