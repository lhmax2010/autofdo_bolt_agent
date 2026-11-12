# Q.5 第17项：登记前真实输入披露（追加记录）

## 第二批 CALIBRATION 冒烟：打开前

本轮授权只做基准配置转换与条目分类计数，不计算任何质量或受控量。
输入范围为 `temp/board-round1-resume2/calibration-runs.json` 登记的四个成功校准运行：cal-thumb、cal-a32、cal-ffmpeg-thumb、cal-ffmpeg-a32。每个对象一份；不包括正式矩阵、失败校准或其他试采。

完整路径及接收时 SHA 在 [disclosure-before.json](evidence/registration-checks/batch2/disclosure-before.json)，在打开 perf 文本前写入。SHA 来自原有收据，执行时再核验。perf.data 只登记来源，不打开；旧 profile.extbinary 不打开、不比较、不覆盖。

转换固定为 max / skid=none / weight=period / head=none / zero-fill=none / text。新 profile 仅用于条目分类，生成后先按字节算 SHA、写入单独 before-classification 披露，再解析条目。仅保存各类条目数与流程退出码，不累计 body 权重，不生成任何以 U 为分母的量。

后续实际打开清单、失败或完成情况将在本节后追加；本披露不是修正案3，也不代替第17项的全部历史披露。

## 第二批实际执行结果

四份均按事先披露转换、分类成功（退出码0），未对齐均0。实际语义读取的profile只有`temp/registration-batch2/{cal-thumb,cal-a32,cal-ffmpeg-thumb,cal-ffmpeg-a32}/baseline.proftext`，各自SHA在对应`before-classification.json`中，早于分类读取记录。

读取原件：仅disclosure-before列出的四份perfscript.txt和四份buildid-list.txt，收据SHA复核一致。旧profile与perf.data均未打开；其他真实profile均未打开。新质量报告由工具正常转换产生，仅留存，未用于任何指标分析。

计算内容仅为：转换阶段退出码、分类阶段退出码、写出body条目的类别个数（含静态排除原因）。没有累计body计数，没有比例或指标。总表及逐条细节见[smoke-summary.json](evidence/registration-checks/batch2/smoke-summary.json)与06报告§9.1。第6项另外读取历史**命令/退出报告**以列可用性，未读取报告指向的profile；这不属于新开真实profile。

未登记修正案3。本清单仅补本次专项授权的披露，历史上其他授权任务曾读取的数据须在第17项总体核销时按既有日志汇总，不把本清单说成历史上从未读取。

## 第三批历史总体披露（只读既有元数据）

完整逐路径表：evidence/registration-checks/batch3/historical-profile-disclosure-000.csv与001.csv；尝试清单historical-conversion-attempts-000.csv，来源清单historical-disclosure-sources-000.csv；各分片SHA在historical-disclosure-summary.json。合并616个路径、1139次转换尝试、1759份元数据来源。410个路径有历史读取/哈希核对记录；其余只披露输出尝试，实际生成/打开状态未知。不重新打开真实profile核实或重算SHA。

|历史阶段|已有计算/读取的量|证据依据|
|---|---|---|
|补丁4–9完整导出验收|profile字节SHA、确定性、函数/调用树/计数正确性；quality报告层级|实现报告06–15及所引用full/real转换元数据，逐路径见CSV|
|第一轮正式S转换与重转|target/usable/ISA/各层质量报告、非叶子line0与无效调用点、写出位置及字节比较|12报告、quality_round1及evidence/16、p9-formal-reconversion保留命令/报告|
|真实avg核对|三个热点函数独立n(k)与avg逐键对照，sum/max对照|evidence/12/31_real_avg_independent.json及12报告；本批不重算|
|补丁9重转|106份sample与20份period输出的profile字节/调用树/total/body/调用点比较、2736条移出样本核对|quality_round1及补丁9重转元数据；路径/量逐条记录|
|第二批CALIBRATION|4份基准转换、条目分类个数、阶段与退出码；不计算body总量/比例/指标|本文件原披露与batch2/cal-*；本批只合并记录|
|G0预试|待第12项完成后补充|本批未执行|

本表披露历史实际记录，不把过去的计数正确性验证包装成从未打开profile；也不把失败尝试当作成功读取。扫描失败0，但未保留的日志无法由本表反证不存在，证据不足项显式未知。没有在本批重新打开CALIBRATION或其他真实profile，没有计算任何真实质量指标或受控量。
