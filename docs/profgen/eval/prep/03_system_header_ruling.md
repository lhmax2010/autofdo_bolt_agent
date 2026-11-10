# 裁决1执行：系统头证据、夹具与剩余身份阻塞

裁决原文：[rulings.md](rulings.md)，已先提交并推送42925cce108de42b6a8dfc69a6d0c17d0254e643。本轮不改设计正文，不打开任何正式sample profile，不连接板子。修订3未登记。

## 1. 四项正面证据

| 项 | 实际核对 | 结果 |
|---|---|---|
| ① CU实际编译命令及两侧系统头目录 | 每个FFmpeg S/C日志各626条C编译命令，spike各1条；逐条提取系统目录/target覆盖选项，均无额外覆盖。读取保留root的clang.cfg，与日志中/usr/bin/clang.cfg及22.1.8版本对应；对Thumb/A32、S/C各自运行同一root的clang -v | 两侧一致；判定时还要求该CU源文件在S/C两侧实际编译命令中，并且producer为该clang |
| ② 未打开系统头覆盖与源码 | C实际编译命令没有system-headers-coverage形式的开关；clang.cfg仅target与resource-dir。源码默认false及跳过条件见下 | 通过 |
| ③ 全局覆盖文件表 | FFmpeg每侧498文件、spike每侧1文件，逐项按完整目录边界检查三类系统目录 | 命中0；未触发全局停止 |
| ④ 无参考候选 | 同一规范化定义文件与去约定后缀的名字进行查找；先查候选，再应用新状态。有候选返回原对应规则 | 新状态仅赋予无候选、四项证据完整的记录 |

各对象两侧一致的系统目录（GBS根视图）：

- /usr/lib/clang/22/include
- /usr/local/include
- /usr/include

实际命令无-isystem/--sysroot/target等覆盖参数；原clang.cfg为-target armv7l-tizen-linux-gnueabi、-resource-dir /usr/lib/clang/22。本机探测在保留的GBS root外通过其emul加载器调用该clang，显式将sysroot与resource-dir重定位到WORKDIR内；--no-default-config阻止读取主机配置，再显式重现上述target/resource参数。原始-v输出全部目录均位于保留root中，归一化时只去掉这个已知root前缀；没有使用主机头文件或仅凭路径猜测。此次是保留工具链的默认目录复核，不冒充构建时已保存的-v日志。

源码：src/llvm/clang/lib/CodeGen/CoverageMappingGen.cpp:49–52（SystemHeadersCoverage默认false）、:1575–1579（系统头函数体不传播覆盖区域）。原文与文件SHA随证据保存。

证据：
- evidence/ruling1/header-evidence.json：两侧目录、命令索引、全局文件表检查；
- evidence/ruling1/*-commands.json：实际编译命令、日志路径/行号/SHA、clang.cfg及compiler SHA（若已拆分，按相邻parts索引重组）；
- evidence/ruling1-headers-*/：-v完整stdout/stderr、argv、真实退出码和资源原文；
- evidence/ruling1/coverage-skip-source.txt：源码摘录；
- 输入为已有静态表和C参考，没有重新导出覆盖，没有读取S采样文件。

## 2. 夹具与实现边界

实现位于tools/profgen_eval/system_header_rule.py；10项合成夹具全部通过，0失败，见evidence/ruling1-fixtures/stderr.txt：

1. 四证据均完整 → system_header_no_reference。
2. decl_file在目录外或只是/usr/include-other前缀相像 → 未决。
3. S/C目录不同 → 未决。
4. 覆盖全局文件表含系统头文件 → 明确抛错、停止。
5. 有参考候选 → 原规则，不套用新状态。
6. 系统头内联进已执行用户函数 → 组仍在映射范围。
7. 纯系统头顶层组 → known_out_of_scope。
8. 系统头、not_instrumented、未执行参考的混合组 → known_out_of_scope。
9. 任一正面证据缺失 → 未决。
10. 组内还有未决身份 → 不得声称known_out_of_scope。

这里验证了组规则的合成语义，**尚未构造真实映射表或任何条目指标**。原有身份规则与not_instrumented条件未放宽。完整对应表中只有此次四项核对通过的行被新闭合。

## 3. 完整清单更新后的状态

| 对象 | 有代码DIE总数 | 新状态闭合 | 同名异定义文件 | 外部CU来源待证 | 有候选、原规则核对未完成 |
|---|---:|---:|---:|---:|---:|
|spike-thumb|17|2|0|0|15|
|spike-a32|17|2|0|0|15|
|ffmpeg-thumb|28149|1236|34|38|26841|
|ffmpeg-a32|28190|1242|34|38|26876|

表中DIE含内联实例，不能当成独立函数数或采样计数。每一行完整保留在evidence/ruling1/<对象>-conclusions/complete-inventory-*.csv，conclusion空值确实表示未决；没有把“有候选”冒充已闭合。“同名异定义文件”等是未决原因分类，不是擅自新增的封闭状态。

按用户第二条停止条件，发现裁决1之外的未决类别后停止。故上表最后一列的定义身份、叶子行集合等原规则验证也未继续，不声称完整身份验收通过；它们与新发现的结构性阻塞分列。

### 3.1 同名但文件不同：每侧34个DIE

全部producer为clang22.1.8；来源分布每侧相同：

| S侧声明文件 | 数量 |
|---|---:|
| libavcodec/arm/hpeldsp_init_arm.c | 6 |
| libavcodec/pel_template.c | 14 |
| libavcodec/hpeldsp.c | 12 |
| libavcodec/rv40dsp.c | 2 |

例如_ZL22ff_put_pixels16_x2_armPhPKhii（省略约定.__uniq.后缀）：
S与C调试信息的声明文件均为libavcodec/arm/hpeldsp_init_arm.c；覆盖侧按findMainViewFileID得到的主文件是libavcodec/pixels.h，代码范围28–32。同名不能抹去文件差异；v1.5明确要求此类由裁决表决定。

34个DIE的同名异文件参考候选目前FNDA均为0。但这不免除完整身份门禁，也不能擅自归为“参考侧未执行”。证据：remaining-categories.json、other-file-example.json，以及evidence/ruling1-other-file-{S,C}/stdout.txt；完整名单在blocking-no-candidate.json。

需裁决：这类宏生成函数的定义文件差异应如何以静态源码、两侧DWARF和覆盖区域证明并记录对应；本轮没有按名字或近邻行号强配。

### 3.2 GNU外部CU：每侧38个DIE仍待现有规则的来源证据

33个GNU AS DIE（如__divsi3、__aeabi_*）、5个GNU C DIE（如__fixdfdi、__udivmoddi4，libgcc2.c）。尚未生成带构建/链接正面证据的外部CU登记表，故保持未决，不仅凭GNU producer打not_instrumented。GNU AS缺的是函数decl_file，不能据此误称CU源文件字段一定缺失；该组仍须按原规则核对CU及来源。

这类目前是证据未闭合，不表示必须修改设计。停止后没有继续补外部来源。完整CU与producer来自前轮静态清单，清单引用保留在每条记录中。

## 4. U、门槛与静态代码规模

未生成U、排除权重、①②③③′、n_eff、K或损失分桶。停止原因是身份门禁，不是测得③<50%。

用户要求的“映射范围内叶子为system_header_no_reference的地址数与代码字节数”记为**未计算**：真实映射范围依赖全部身份结论及名字闭包，当前尚未建立；不能拿全局DIE数、DWARF区间字节数或样本数充当这个统计。全静态清单中已闭合的系统头文件/函数列表已保存在conclusion-summary.json，仅供查阅，不冒充映射范围规模。

## 5. 资源、产物与挂账

全部命令使用3G/200% user scope、nice19/ionice idle、串行；未启动重构建或覆盖导出。ruling1/resources.json及各scope记录MemAvailable与实读memory.peak；无OOM或资源终止。新产物SHA与生成命令见ruling1/artifact-sha256.json。

下一步等待同名异文件规则裁决；随后仍须补原规则定义/行集合验证、外部CU证据及N.5完整夹具，不能直接跳到③。覆盖summary交叉核对挂账保留。修订3未登记，正式sample profile始终未打开。

资源摘要：已保存最低MemAvailable=9.425247GiB；最大实读cgroup memory.peak=0.127079GiB；资源终止=0。所有任务短于60秒，scope监测仍保留60秒采样逻辑。

补充计数口径：按“规范化decl_file、去后缀名字、decl_line”去重，仅用于展示，每侧同名异文件类别为30个身份，外部CU待证类别为38个身份；完整DIE与别名/副本均保留，不以展示去重改变对应规则。证据：distinct-unresolved-identities.json。
