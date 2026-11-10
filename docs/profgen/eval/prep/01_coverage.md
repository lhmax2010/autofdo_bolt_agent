# N.5 #13 覆盖参考处理：阶段记录

状态：**部分完成，随 #16 身份阻塞停止**。本轮没有打开任何正式 sample profile（包括 CALIBRATION），没有生成 U 或正式质量指标；只处理 C 覆盖参考与静态文件。

## 已完成的核对

| 对象 | 文件数 | 完整 DA 行 / 正计数行 | 按设计键合并的源函数 | 空 main view | DA 与 segments 差异 |
|---|---:|---:|---:|---:|---:|
|spike-thumb|1|126 / 116|11|0|0|
|spike-a32|1|126 / 116|11|0|0|
|ffmpeg-thumb|498|114750 / 8716|5890|0|0|
|ffmpeg-a32|498|114750 / 8716|5890|0|0|

生产参考取平台 llvm-cov export -format=lcov 的 DA，JSON segments 只用于独立复算。四份均逐行相等。源函数按规范化文件、去文件前缀和 .__uniq.<digits> 的名字、主文件代码区域最小行合并；最大行作为终点。宏按 ExpansionRegion 与 FileID 区分，不排除整个物理文件。

- 命令、真实退出码、stderr、scope 峰值：evidence/spike-{thumb,a32}-lcov/、evidence/ffmpeg-thumb-lcov/、evidence/ffmpeg-a32-lcov-admitted/。
- 完整 FFmpeg lcov 被按原始字节顺序分片，索引 stdout.parts.json；拼接 SHA 与原输出一致。Thumb/A32 lcov SHA 同为 285d1104dcfbd1995f762b150480690e7eb63a0a40fad2725fd0ca6279450cfc。
- 两份 spike lcov SHA 同为 49bb9c484fb7f5499824df0cde8101adc7f1c17db2c274ba0d51d0e368a1009e。
- 派生完整静态表放 evidence/*-coverage-tables/；index 记录各 CSV 分片 SHA、原始派生 JSON SHA。不是 sample profile 表。
- 版本为工作目录 GBS 平台 LLVM 22.1.8：evidence/version-llvm-cov/。
- 四次 export 都出现 profile data may be out of date - object is newer，原文保留。对象为后来合成的 unstripped 副本；未把此 mtime 警告隐藏，也未把它当身份匹配证明。运行与调试原件 SHA 对 evidence/11/08_artifacts.json 全部相符，见 input-sha256.json。

## summary 的交叉核对尚未闭合

须区分 DA 文件视图与函数 summary。spike 的完整 DA 为126/116，JSON与lcov summary均为119/109；FFmpeg完整DA为114750/8716，既有summary为112206/8298。两种输出各自一致，**不能强行要求完整DA条数等于summary，也不能用summary替换DA**。

spike DA 中12–15行位于宏定义，超出主文件函数代码范围；仅用闭区间筛选也不能说明其余差异。依据 CoverageSummaryInfo.cpp:100–110，函数 summary 经 getCoverageForFunction 构造；lcov DA 经 getCoverageForFile 的行迭代器导出。范围、宏展开和视图差异的逐项分解尚未完成，因此本项不宣称 N.5 #13 全部验收通过。全部差异文件与原始数字见 evidence/coverage-summary.json。

## HasMultipleRegions 与夹具

llvm-cov show --use-color 的行计数列在 hasMultipleRegions() 时为品红色（SourceCoverageViewText.cpp:222）。从原始 ANSI 输出提取17行，与 segments 算法完全一致，见 has-multiple-regions-check.json、spike-thumb-api-show/。这使用平台 Coverage API 的显示结果，不把两份 Python 实现互相比对冒充独立核对。

7项合成 JSON-layout 单元夹具通过，0失败；不是实际编译的测量：
1. 三CU同一static inline，只有一个执行：合并后FNDA为1、三副本保留。
2. 宏内部循环与同文件普通函数：FileID区分，宏行不扩大主函数范围。
3. 同一模板文件以两个名字包含：保持两个函数身份。
4. 两个已执行函数同一物理行：保持两个身份，供下游歧义排除，未在本轮冒充U验收。
5. 空main view：显式未决状态，不默认为文件0。
6. main view不是文件0：按ExpansionRegion标记选择。
7. 多region、gap与跨行延续：延续不冒充region起点。

命令：python3 tools/profgen_eval/test_coverage_reference.py；日志 coverage-fixtures-compact/。完整N.5 #16夹具尚未实施，不能把这7项称为整个阶段通过。

## 资源与存储

所有命令受 user scope 限制，nice19/ionice idle。覆盖导出门槛10GiB，8G/200%；轻任务3G/200%，串行。A32首次未满足门槛，没有启动export；稍后满足时首次实际导出成功。无OOM、无资源终止。
已保存最低MemAvailable=9.808773GiB；最大已观测cgroup memory.peak=1.934326GiB。详见 resource-summary.json 与各任务原始 meminfo。任务均短于60秒，监测器仍实现每60秒保存与连续低内存终止。

新证据全部在本目录，完整派生表拆成小体积文本。初版重复存储全部文件列表的中间JSON过大，已改为紧凑字段/文本分片，不改原始C导出。复算命令在每个任务 command.json，打包命令 python3 tools/profgen_eval/pack_static_evidence.py；全部文件SHA见 artifact-sha256.json。

## 剩余

等待身份规则裁决；恢复后补完 summary/main-file 范围核对，#16全夹具及闭合对应表，再生成U与③。ToS输入参考未推进。本轮未修改设计或 LLVM。
