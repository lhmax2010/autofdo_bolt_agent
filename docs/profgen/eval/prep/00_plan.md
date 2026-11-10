# v1.5 登记前准备第一阶段计划

设计 SHA-256：be18d105d5711861b08517004d97eb40de5fb37b92213202cddd6b759fa9e636。
归档提交：dba4de162eab5058f16dfed8445da93ea058e49a。

本阶段不打开、转换或计算正式 sample profile（包括 CALIBRATION）的任何量，不连接板子。仅允许静态 ELF/调试文件、C 构建覆盖参考、源码，以及补丁9已有转换报告中的成功/失败记录。不改 LLVM、设计、补丁或资格判定。修订3尚未登记。

## 执行顺序与验收

| 顺序 / N.5项 | 输入 | 产物 | 验收 |
|---|---|---|---|
| 1 / #13 | evidence/11/08_artifacts.json 中 S/C 运行与调试文件；既有 C profdata、整体覆盖 JSON；LLVM22.1.8 CoverageMapping.cpp | tools/profgen_eval/ 覆盖处理代码与夹具；evidence/coverage_*；01_coverage.md | spike 的 lcov DA 与独立 JSON segments 行计数逐行相等；main view / CodeRegion 范围、宏 FileID、跨 CU 副本合并及全部规定夹具通过；HasMultipleRegions 与平台 Coverage API 输出核对 |
| 2 / #16 | S/C ELF 的完整 DWARF；覆盖函数记录；源码与编译/链接记录 | 完整身份清单、外部 CU 清单、跨侧对应表、夹具及02_identity.md | 清单独立于采样及映射范围；命名遵守 getSubroutineName(LinkageName)；单候选同时核对定义声明位置和非零行集合；全部条目有封闭结论，缺证据不得推定 not_instrumented |
| 3 / #6,#15及静态映射依赖 | 上述清单、静态指令/行表/内联关系、C参考；仅只读已有转换报告中的可用性 | U、完整排除原因集合、权重、对象登记表及03_registry.md | ①②③③′、n_eff、K仅从参考和静态U计算；损失互斥分桶之和等于ΣR(C)−ΣR(U)；任一③<50%立即停止并报告，50%–80%明确标示 |

对象先枚举 FFmpeg Thumb/A32、spike Thumb/A32 的训练 C 参考；ToS 的 FFmpeg Thumb C 参考作为不同输入单列，不能以训练参考代替。以现有产物是否齐备作清单，不使用 S 采样内容选择函数、地址或样本。

#5中静态地址关系是U计算的依赖；本轮不得执行其 CALIBRATION 冒烟。未在本轮指定的统计模拟、板上与修订3登记不执行。若完整身份或静态映射所需规则不明确，先保存原始证据并停下来请求裁决，不用临时启发式给出③。

## 输入边界与资源

- 工具来自 WORKDIR 内 GBS root，Python仅用标准库，不安装依赖。
- 静态清单入口：docs/profgen/impl/evidence/11/08_artifacts.json。
- C参考入口：temp/board-round1-retry/training-profdata/ 下名称以 train-/test- 开头且 stage 为 C 的 profdata；不读取 R/G5 或任何 sample profile。
- 既有 JSON：temp/coverage-whole-8g-20261109/{thumb,a32}.coverage.json，以及 temp/quality-round1/train-spike-{thumb,a32}-C.coverage-confirmed.json。
- 轻任务启动 MemAvailable≥4GiB，每任务 systemd user scope 3G/200%，nice19/ionice idle，串行。
- 覆盖导出启动 MemAvailable≥10GiB，每任务 scope 8G/200%；不足时不启动。任何持续任务每60秒保存完整 meminfo；连续两次<3GiB终止自己的任务，保存原始记录。资源门槛不是放宽设计数据验收的依据。
- 所有新产物与证据写入本目录/evidence，代码写 tools/profgen_eval；每项保存生成命令与SHA-256清单，不把正式S输入纳入哈希扫描。
- 每完成一项，更新STATUS并独立提交推送。未完成项注明原因，不宣称登记就绪。

## 归档记录

Downloads仅发现02_llvm_profgen_enhance_design_v1.5.md；移入前后SHA一致，无重复副本；旧版本未改。工作区原有三项配置保持未跟踪且未读取。
