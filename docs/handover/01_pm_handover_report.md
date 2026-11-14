# PM 交接核对（2026-11-14，只读调查）

本报告交接给只能通过 GitHub 访问本结果仓库的 Claude。基线为 `main` 的 `e171e1d0136e001bd4c004a125461e278de6985b`，本轮 `git ls-remote origin refs/heads/main` 返回同一值。现行设计为 [v1.8](../profgen/design/02_llvm_profgen_enhance_design_v1.8.md)，SHA-256 `ae667bd61470118179f6876c912285b7c57ab22518640c2af9f42103ad428e59`。以下“已完成”指证据对应的范围；估时是规划估计，不是新测量。

本轮没有执行 sdb、连接板子、构建、运行模拟/质量矩阵/性能测试，也没有打开任何真实 sample profile（含 CALIBRATION）。只读了文档、源码、已有命令/遥测时间日志、文件清单及 Git/进程状态；`perf --version` 仅作主机工具可用性检查。只新增本报告、更新 STATUS，不改设计或既有证据。`config/`、`gbs_gcc.conf`、`gbs_llvm.conf` 未读取、未改动。下文命令均为交接示例，本轮没有执行其中的采集、转换、构建命令。

## A. 当前停止点

### A.1 最后完成的任务、进程与主机产物

区间模拟已于 **2026-11-14 08:27:17 +08:00** 完成，随后停止；最近一次完成审计提交为 `e171e1d0136e001bd4c004a125461e278de6985b`。

| 阶段 | 完成情况 | 已推送提交 |
|---|---|---|
| 验收分层 t | 122/122 场景，各 10⁶ 次；全部通过 | `14a487d988a6140c15a68da3b24c14d5c2247634` |
| 包络与 B 组报告 | 150/150 行，各 10,000 次；不改变验收开关 | `00db40a9e6721d496e6eba845f1047a043bc17de` |
| 完成审计 | 锁、结果 SHA 链、发布字节和结束记录核对一致 | `e171e1d0136e001bd4c004a125461e278de6985b` |

`quality_equivalence_enabled=true`；最低验收覆盖率 94.3934%，非零 Δ 的最高判等价比例 2.8226%，两项 A4 都是 100% 退化、0% 等价。总墙钟 129161.888 秒（35小时52分42秒），计算 scope 峰值 62,971,904 B。历史最低 MemAvailable 为 1,463,853,056 B，仅一条低于 3GiB，没有触发当时“连续两条低于 3GiB”的停止规则；不能称全程内存充裕。证据：[07报告§6、§11](../profgen/eval/prep/07_interval_simulation.md)、[完成审计](../profgen/eval/prep/evidence/registration-checks/simulation/phased/completion-audit.json)。

本轮 `ps -eo pid,stat,etime,args` 与 `systemctl --user list-units --type=scope --state=running` 未发现项目模拟/GBS/llvm-profgen 任务继续运行或挂起；只有本轮只读检查的短 scope 及桌面应用 scope。此为检查时快照，不承诺其他会话之后不会启动任务。既有模拟 PID 2324969 的结束另有上述完成审计。未停止或操作其他人的进程。

`temp/` 是可复现性的重要组成部分，不能因“不在 GitHub”而删除。下列是本轮确认存在的目录及其已有仓库索引，不是新任务输出：

| 主机位置（WORKDIR 相对路径） | 内容/状态 | GitHub 可读入口 |
|---|---|---|
| `temp/interval-simulation/formal-001/` | 完整结果、资源全文、进度、结束与发布收据；已完成 | 07报告、`evidence/registration-checks/simulation/phased/` |
| `temp/llvm-profgen-enh/` | LLVM 开发树 HEAD `15a5ec3f46283ad2eccaecf97b2eac2a0e43d65c`；正式补丁9工具。**仅已跟踪的本地修改是 packaging/llvm.spec**；另有未跟踪的 debugfiles/debuglinks/debugsourcefiles/debugsources/elfbins 列表、RPM manifests、`mlgo_verify_assets/` | [15报告](../profgen/impl/15_patch9_nonleaf_line0.md)、[spec差异](../profgen/impl/evidence/02/03_spec_local.diff) |
| `temp/profgen-baseline-tool/`、`temp/profgen-patch8-amend/`、`temp/profgen-patch9/` | 原工具存档、构建/C1/重放材料，不能用新工具覆盖旧基线 | [02报告](../profgen/impl/02_lit_env.md)、[13报告](../profgen/impl/13_patch8_thumb_dwarf.md)、15报告 |
| `temp/board-round1*`、`temp/frequency-disambiguation/` | 原始 perf、遥测、训练 profraw、收据及诊断；本轮不打开 profile | [12报告§16](../profgen/impl/12_board_round1.md)、[14报告](../profgen/impl/14_ffmpeg_frequency_diag.md) |
| `temp/eval-prep11/`、`temp/coverage-whole-8g-20261109/` | 24项生成侧构建、RPM/debug、完整命令和整体覆盖导出 | [11报告§7–10](../profgen/impl/11_eval_prep.md)、[quality_round1](../profgen/eval/quality_round1.md) |
| `temp/prep-*`、`temp/registration-batch1/`、`batch2/`、`batch3/`（后两者也带 `registration-` 前缀） | 大 AST/token、DWARF/行表、身份表、静态地址关系、合成转换；摘要、路径及 SHA 已登记 | [05静态报告](../profgen/eval/prep/05_identity_gate_and_coverage.md)、[06核对表](../profgen/eval/prep/06_registration_checklist.md) |
| `temp/CodingSystem/` | 框架旧快照，非已实现的业务框架 | E节 |

这些目录包含尚未提交的大原件，但其摘要已提交；不能把 `temp/` 中全部草稿视为已验收代码。根仓库开始时仅有三个获准的 untracked 配置项。结果仓库可下载的是补丁、脚本和证据摘要，GitHub clone 本身不能恢复所有实验原件。

### A.2 有效待办与历史文字

| 状态 | 项目 | 依据 |
|---|---|---|
| 仍有效 | Q.5 #12 板上记录器/散热/G0预试，#17 G0披露尾项，#18 每板N，#19 修订3与锁/槽位/收据登记 | 06报告最新总表、设计Q.5；当前 **17项完成、17部分、12/18/19未开始** |
| 仍有效 | 质量矩阵、消费构建、性能/过期复用、第二阶段默认值/阈值冻结 | 设计§10步骤5–7 |
| 仍有效 | 非增量前撤销 llvm.spec 两处测试改动；正式正常GBS及发布补丁整理 | STATUS挂账、02/15报告 |
| 仍有效/外部条件 | LLVM发布后默认build-id复核；ARM probe编译崩溃；CodingSystem后续版本与实现 | STATUS挂账、10/11报告；本轮没查询新发布包或框架远端 |
| 已关闭 | GNU AS Thumb首地址/别名查询、映射不可用降级；非叶子line0处理 | 补丁8/9、13/15报告；不是仍待PM决定的实现缺陷 |
| 已关闭 | 高LOST完整导出、真实avg三热点核对、真实unknown样本、五项板上集成 | 12报告§12/16；旧06遗失原件仍不可追溯，闭合用的是新完整采集 |
| 已关闭 | head补零兜底、IP选项枚举化、身份裁决1–4及v1.8静态门禁 | 07/09实现报告、05静态报告§14 |
| 已完成但不得扩大结论 | 四对象avg/prev-inst合成全地址转换；静态“表内可登记”；模拟开关true | 06第三批、07模拟；不是修订3已登记或真实质量等价 |
| 已被后续规则替代 | “等待v1.6三家评审”、旧C仅C构建、旧code_free分类、12小时模拟门槛 | v1.8 O.2.3/Q、07报告；历史记录保留，不当当前待办 |
| 已过时 | STATUS早期“P9待构建”“35/70”“LOST/avg未关闭”、旧批次Q.5完成数 | 12/15报告末节、06最新总表与07完成记录优先 |

特别注意：原质量 ε=±0.01、默认独立抽样、性能证据不足再加轮数，已被 v1.8 的 **质量±0.02、RUN配对/分层、每层15、性能固定N** 等条款替代。④ body比例依然是登记后RUN级量，登记前不能拿静态DA/地址数代替。正式S历史转换与CALIBRATION披露已有专门记录；STATUS某些早期“未读取任何profile”是当轮范围陈述，不是项目历史从未读取的声明。[披露表](../profgen/eval/prep/17_profile_disclosure.md)

## B. 增强交付剩余工作

### B.1 依赖与估时

以下时间均为规划值；板子当前状态、本轮未测试的新记录器开销、正式非增量构建耗时均未知。不能把估计写成验收成绩。

| 工作 | 前置条件与阻塞 | 板子 | 主机/板上时间估计及依据 |
|---|---|---|---|
| Q.5 #12 | 用户确认散热片+风扇；四核60秒低于75°C；root cpuinfo_cur_freq；完整/授权unknown的kmsg路径；30秒四核前后校准；解码+采样器时序及<0.5%开销；G0≥10预试轮 | 每块拟评估板都需要 | 主机脚本整合/审查半天–1天；每板预留1–3小时（估计）。尚未板上验收，不能直接复用旧collect脚本宣称满足v1.8 |
| Q.5 #17剩余 | 616历史profile路径/1139尝试已披露；补G0条件、轮数、原始耗时、开销 | 依赖#12 | 主机约1–2小时整理；不重读历史profile |
| Q.5 #18 | #12有效预试；按公式固定每板N；预试无法完成时N=40只解决预算，不豁免其他板上前提 | 依赖#12 | 主机不足1小时；见B.3公式 |
| Q.5 #19 | 重验静态产物/代码/模块SHA、17披露、模拟结果；完整槽位与旧原件初始化收据；协议与参数全部锁定 | 本身否 | 主机半天–1天清单审计（估计）；需PM确认登记内容，推送成功才允许受控量 |
| 登记后RUN补采 | #19；板子身份/同阶段条件、遥测、空间和收据状态机 | 是 | RPi4原14层补140逻辑RUN，旧负载时间估计见B.2；RPi5无可复用正式RUN，先校准后估时 |
| 5.8质量矩阵 | 补采、已推送收据和终态；固定对象/映射/U；共用统计模块SHA一致 | 计算本身否 | 主机预留1–3天串行转换/分类/20k bootstrap与报告（估计，未跑正式矩阵不能给实测时长） |
| 5.9消费与性能/过期复用 | 候选参数、明确登记矩阵、训练/测试分开、散热门禁、消费者诊断 | 两板 | 消费构建估计半天–2天，受GBS资源限制；板上以B.3公式预算，不能沿用老“10轮不够继续加” |
| 第二阶段冻结 | 质量/性能证据、失败/未定义项、默认值和门槛决策；或明确另行批准缩减交付范围 | 评审本身否 | PM/评审时间未知；本轮无权跳过 |
| §10步骤9 | 撤销spec本地测试改动；补丁序列审查/重放；发布配置正常非增量GBS；非★事项确认 | 主机为主 | 至少预留一个完整构建窗口，准确耗时未知；P9增量1079.586秒不能当全量估时。Gerrit方式/时间仍由用户决定 |

质量矩阵应按 v1.8 §5.8.6 的**单因素对基准**清单，不是早期全笛卡尔积：基准 max/none/period；sum、avg、prev-inst 单独比较；sample只在频率层比较；最终组合对基准只作描述。head/补零由5.9消费与性能评估，不能用不变的M1/M2“选优”。K<50仅描述；n_eff为null走显式分支；开关true不证明工作模型在真实对象成立。静态③(C)为spike Thumb/A32 99.991434%/99.991339%，FFmpeg 84.981617%/84.729001%；FFmpeg③(C_dc)约49.93%/49.88%，评价域局限必须随结论给出。[设计§5.8](../profgen/design/02_llvm_profgen_enhance_design_v1.8.md)、[05§14](../profgen/eval/prep/05_identity_gate_and_coverage.md)

### B.2 分层、旧RUN与补采时间

v1.8 §5.8.6把“有效RUN”定义为采集完成且原件通过拉回校验的逻辑RUN，**不等于遥测干净**。第一轮70组/106物理段可作为旧阶段的候选；每层5个，则预期旧5+新10，不因62 unknown/8异常就自动把旧阶段清空。#19仍须逐个导入并核对原件SHA和接收凭据，本轮没有重新哈希/打开采样原件，所以这里是**证据支持的候选70，尚未正式登记70**。每段不算独立RUN。层内旧有效数不足5时全部15新采，不能3+12。

来源：[12§16](../profgen/impl/12_board_round1.md)、[70组索引](../profgen/impl/evidence/12/56_matrix_summary.json)、[第三批遥测重放](../profgen/eval/prep/evidence/registration-checks/batch3/telemetry-replay-summary.json)。旧标签31/28/11保留；新规则重放8异常/62未知/0干净，干净子集仅描述。

| RPi4对象/输入 | 比较层 | 旧逻辑RUN | 计划总槽位 | 预期补采 |
|---|---|---:|---:|---:|
| spike Thumb | 固定低/中/高 + 中档频率，共4层 | 20 | 60 | 40 |
| spike A32 | 同上4层 | 20 | 60 | 40 |
| FFmpeg Thumb BBB | 同上4层 | 20 | 60 | 40 |
| FFmpeg Thumb ToS | 中档固定1层 | 5 | 15 | 10 |
| FFmpeg A32 BBB | 中档固定1层 | 5 | 15 | 10 |
| 合计 | 14层 | 70（106物理段） | 210 | 140 |

本轮仅读每组索引指向的 `record.stderr` 中 `time -p` 的 `real`，合并同一逻辑RUN的物理段，未读profile/perf文本或重新计算质量指标。下表为既有运行管道的墙钟（含perf/负载管道开销），不含导出、传输、SHA、冷却、未来新增校准；每层5个时间都可取得。单位秒：

| 变体 / 模式 / 输入 / 预算 | n | 最短 / 中位 / 最长（秒） |
|---|---:|---:|
| ffmpeg-a32-S / sample-fixed / bbb / 100000 | 5 | 183.18 / 183.21 / 184.22 |
| ffmpeg-thumb-S / sample-fixed / bbb / 20000 | 5 | 61.56 / 61.59 / 61.62 |
| ffmpeg-thumb-S / sample-fixed / bbb / 100000 | 5 | 182.23 / 183.17 / 183.20 |
| ffmpeg-thumb-S / sample-fixed / bbb / 400000 | 5 | 729.68 / 730.76 / 731.71 |
| ffmpeg-thumb-S / sample-fixed / tos / 100000 | 5 | 192.19 / 192.25 / 193.20 |
| ffmpeg-thumb-S / sample-freq / bbb / 100000 | 5 | 243.74 / 243.83 / 244.79 |
| spike-a32-S / sample-fixed / bbb / 20000 | 5 | 15.35 / 15.36 / 15.38 |
| spike-a32-S / sample-fixed / bbb / 100000 | 5 | 72.62 / 72.64 / 73.64 |
| spike-a32-S / sample-fixed / bbb / 400000 | 5 | 274.12 / 274.22 / 289.68 |
| spike-a32-S / sample-freq / bbb / 100000 | 5 | 111.79 / 112.80 / 115.83 |
| spike-thumb-S / sample-fixed / bbb / 20000 | 5 | 15.35 / 15.35 / 15.38 |
| spike-thumb-S / sample-fixed / bbb / 100000 | 5 | 71.61 / 72.66 / 73.66 |
| spike-thumb-S / sample-fixed / bbb / 400000 | 5 | 273.17 / 274.19 / 286.56 |
| spike-thumb-S / sample-freq / bbb / 100000 | 5 | 113.81 / 114.84 / 115.87 |

上述中位数加总×每层新增10，负载窗口约 **7.07 小时**；实际RPi4建议预留 **10–16小时板上窗口**（估计，分批传输/冷却/前后校准及新散热改变速率会变化）。失败重采受登记尝试上限约束，不靠无限加时达标。相同预算不保证旧时长能达到，先校准；多个采集段仍只占一个槽位。

RPi5正式评估RUN候选为0：04/09是探测，不是与新S/参考同身份的正式RUN。若采用spike aarch64四层、FFmpeg aarch64 BBB四层及ToS中档一层的对称计划，则9×15=135新逻辑RUN；**这只是矩阵建议，未登记，最终层清单须PM确认**。RPi5当前同负载速率未知，不用RPi4时长伪装RPi5实测预算。

### B.3 性能、过期复用和板子条件

每板固定 `N=min(40,max(10,ceil(2*(1.96*1.2533*CV/0.005)^2)))`。CV用散热后G0≥10预试、去预热但不剔除离群的样本标准差/均值，先保留4位有效数字；无法预试N=40。CV 0.5%→13、1%→40。正式每组交错N轮、丢弃预热，性能中位数相对差ε=±1%，到N仍不确定就报证据不足，不加轮。[设计§5.9、Q.5 #11/#12/#18](../profgen/design/02_llvm_profgen_enhance_design_v1.8.md)、[06第三批](../profgen/eval/prep/06_registration_checklist.md)

| 组 | 消费配置 |
|---|---|
| G0 | 不用profile |
| G1/G2 | IP head=none，profi分别true/false |
| G3/G4 | IP head=entry-estimate，profi分别false/true |
| G5 | IR插桩PGO，正常flags，使用-fprofile-use；已有的G5生成侧二进制不等于G5-use |
| G6 | probe构建不用profile；子方案开销对照 |

每个入围聚合/skid组合，G1–G4各展开zero-fill none/sampled-functions。若仅一个候选且G6可用，每板 **11N** 次正式解码（G0/G5/G6各N，加8N IP）；两板同N时22N，即220–880次。不同N用11(N4+N5)；若有多个候选k，每板为(3+8k)N；A32额外矩阵另计。G7只在probe准入后；ARM probe崩溃使RPi4 G6/G7不能默认列为已具备。缩小矩阵须登记未覆盖交互，不可宣布未测默认值已验证。

按旧RPi4单次BBB管道约61.6秒，仅11组N=10–40约1.9–7.5小时/板（规划量级，**不外推RPi5性能**）；校准、预热、冷却、传输另计。已有S/R/C/G5 **生成侧**24项构建累计：spike240.03秒、FFmpeg2288.20秒；不是未来消费构建的保证。[11报告§9](../profgen/impl/11_eval_prep.md)

过期复用须做纯行号移动、热点CFG改动、调用点插入/删除；每种比较无profile、旧profile关salvage、旧profile开salvage、新采profile四组，保存匹配/checksum/high-staleness诊断。至少3×4N/板的解码计划量级（是否复用对照须登记）；还需变更源码构建、新采样和消费验证，估计每板另1–2工作日，准确未知。旧profile原无显著收益时“收益保留比例”不适用。不能把普通build-id校验错误当消费端过期复用。[设计§5.9.6](../profgen/design/02_llvm_profgen_enhance_design_v1.8.md)

**RPi4散热是否已加装：未知，没有安装及复测通过记录。** 最后诊断达到80.341°C、sysfs有600MHz；按当轮判定规则正式结论为 **unknown**（低频仅连续2区间，非规则要求3；完整固件时钟来源缺失），不是已确认固件降频。v1.8离线新规则判该诊断异常，两者不矛盾。最后有证据的恢复是root off、schedutil、RPM1232不变。当前板状态未知，本轮不接板。[14报告末节](../profgen/impl/14_ffmpeg_frequency_diag.md)

最后记录的RPi4环境：total_mem=1600、MemTotal1,507,996KiB，resourced运行、未见reclaimd，zram lzo-rle/disksize617,676,800B。它不是用户背景中“zram65%/关闭resourced swap”的已证实基线。仍须下一会话身份、内核、环境重新断言，不把恢复记录当现况。[14报告状态取证](../profgen/impl/14_ffmpeg_frequency_diag.md)

RPi5最后探测：Raspberry Pi 5 Model B Rev1.1、aarch64、6.12.80-arm64-rpi4-v8、页4096；dsoff单/双进程、buildid-mmap通过。aarch64生成侧RPM已构建，未部署/训练成完整正式评估数据；需用户提供板子就绪、身份与新镜像确认、工具/库SHA复验、参考R/C/G5训练、对应静态对象与Q.5门禁、散热与G0。现在是否在线、已装散热、缓存工具仍在，均未知。[09探测](../probe/09_rpi5_prefreeze_checks.md)、11报告、设计§10步骤5。

### B.4 步骤9与“直接保守默认交付”

非★清单按当前证据分别处理：

- **尚未闭合**：新LLVM包开启ENABLE_LINKER_BUILD_ID并发布后的原样构建、默认build-id与拆分复核；本轮没查新包，不能宣称已发布/已验证。
- **已闭合**：aarch64 Tizen debug映射符号；probe节拆分位置按aarch64证据+架构无关检测裁决闭合；真实unknown（12报告335条）；新aarch64小包DWARF5逐行/抽样符号化/comp_dir、BUILD/RPM ID差异补证。
- **保留局限**：旧08 FFmpeg同次BUILD产物已缺失，不能声称原次实验已复现；新小包证据只能证明相应输入。armv7l probe崩溃是§10步骤8子方案阻塞，不阻塞已验收DWARF路径。

证据：[10报告§4.3](../profgen/impl/10_host_verification.md)、[11报告裁决](../profgen/impl/11_eval_prep.md)、[12报告§16](../profgen/impl/12_board_round1.md)、STATUS挂账。

**技术判断（不是批准省略评估）**：补丁1–9的DWARF/IP核心链已完成；设计§10步骤4也明确“已完成”。最后正式验收86项lit=84 PASS/1 UNSUPPORTED/1 XFAIL/0 FAIL，C1两遍各636条0差异、14历史导出重放通过。没有证据表明还缺一个地址读取/身份/计数/报告核心模块。[15报告](../profgen/impl/15_patch9_nonleaf_line0.md)

若PM另行决定仅按 max/none/none/none 交付，仍有这些具体工作：

1. **接口定稿**：当前 `llvm-profgen.cpp:266–267` 在未显式给 `--ip-aggregation` 时拒绝，尚没有max默认；`rst:139–160`把聚合与head/zero/skid写为评估/暂定接口。若“采用默认”指省略参数也生效，就需独立授权改实现、帮助、负例和文档，并重新lit/C1；若只是workflow显式传max，则无需改变此行为，但必须称显式策略，不能声称CLI默认已经改好。
2. **质量门槛决策**：三个IP质量阈值目前都是可选、无评估默认；保守四元组没有给出它们的发布政策。需明确是否保持可选、怎样标注sampling_adequacy unknown；不能把退出0当充分质量证明。
3. **发布构建与补丁清理**：撤销本地spec测试改动（不连带删其他文件），在干净起点按0001–0009应用验证、确认没有spec/临时物、正常非增量GBS产出及安装/拆分身份核对；补充新产物回归。短路/增量RPM不自动成为正式交付包。
4. **上项非★与支持声明**：处理默认build-id外部依赖及证据局限；限制为已准入的DWARF用户态IP路径，不顺带承诺probe、原生perfdata、内核profile或BOLT。
5. **验收范围决定**：现行设计仍要求步骤5/6再第二阶段冻结，不能由开发者单方面跳至9。可以形成明确的缩减交付决策并保留“性能收益与正式质量矩阵未验证”，但不能写成已证明统计等价/默认最优。

## C. 工具使用与构建/部署

### C.1 正式补丁9工具

本轮重新算工具SHA，仍为 `2e8895afce661b5fdc8cacab2b3323496fca51af7bd7b51c3753aa8328b7d0d5`。工具位于 `temp/llvm-profgen-enh/build/bin/llvm-profgen`；不能直接假设主机libLLVM版本兼容。依 [c1_baseline.py:28–30](../../tools/profgen/c1_baseline.py) 使用GBS加载器和库：

```bash
W=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent
export TMPDIR="$W/temp/tmp"
L="$W/temp/llvm-profgen-enh"
R="$W/temp/GBS-ROOT-LLVM-X86/local/BUILD-ROOTS/scratch.x86_64.0"
# 在获准处理该输入且通过资源门禁之后运行；本轮不执行。
nice -n 19 ionice -c3 systemd-run --user --scope -p MemoryMax=3G -p CPUQuota=100% \
  "$R/lib64/ld-linux-x86-64.so.2" \
  --library-path "$L/build/lib64:$R/lib64:$R/usr/lib64" \
  "$L/build/bin/llvm-profgen" \
  --ip-samples --binary="$W/temp/INPUT/runtime/libavcodec.so" \
  --debug-binary="$W/temp/INPUT/debug/libavcodec.so.debug" \
  --perfscript="$W/temp/INPUT/perfscript.txt" \
  --perf-buildid-list="$W/temp/INPUT/buildid-list.txt" \
  --binary-match-regex='^/opt/afdo_agent/variants/VARIANT/usr/lib/libavcodec\.so\.62\.11\.100$' \
  --ip-event=cycles --ip-weight=period --ip-aggregation=max \
  --ip-skid=none --ip-zero-fill=none --ip-head-samples=none \
  --format=extbinary --output="$W/temp/OUTPUT/profile.extbinary" \
  --quality-report="$W/temp/OUTPUT/quality.json"
```

`INPUT/OUTPUT/VARIANT`是占位符，须换成同build-id运行/调试实体和实际板上DSO原路径；aarch64通常是usr/lib64。事件名以导出为准，cycles:u不等于cycles。输出目录须事先获准并存在，输出不得与任何输入或彼此同文件。固定P_ref合并时显式加 `--ip-period-unit=<正整数>`，不能盲目把不同数据的自动中位数当相同单位。示例不表示获准现在处理正式输入。

| 选项 | 含义、当前默认/限制 |
|---|---|
| `--ip-samples` | 显式开启，默认off；不开时走原LBR路径 |
| `--binary` / `--debug-binary` / `--dwp` | binary必需；同身份debug/dwp可选；指令字节来自运行ELF |
| `--perfscript` | 严格文本；IP模式拒绝perfdata |
| `--ip-event` | 默认不指定；只有一个事件可自动选，多事件必须选完整名字 |
| `--ip-weight=period\|sample` | 默认period；period_sum归一化或sample_count |
| `--ip-period-unit` | 正uint64；默认目标样本原period下中位数（符号化/skid前）；sample权重不能给此项 |
| `--ip-aggregation=sum\|max\|avg` | **无默认，必须显式给出**；avg需可证明边界 |
| `--ip-head-samples=none\|entry-estimate` | 默认none；head不是total；正total估计最低1 |
| `--ip-zero-fill=none\|sampled-functions` | 默认none；仅有usable样本函数补零、total不变 |
| `--ip-skid=none\|prev-inst` | 默认none；同范围/映射区间前驱且有可用行才调整，否则原址并计数 |
| `--binary-match-regex` | 默认按binary realpath文件名；正则为原路径子串搜索、含deleted，需整串匹配时加^/$ |
| `--perf-buildid-list` | 可选路径级身份补证，不等于逐样本MMAP绑定 |
| `--allow-missing-build-id` | 默认false；只放行缺证据为unverified，不放行冲突 |
| `--quality-report` | 默认不写；建议workflow要求提供并检查 |
| `--ip-min-usable-ratio` | 可选、无默认；原始usable/target权重比门槛 |
| `--ip-min-target-samples` | 可选、无默认；零target/usable仍独立失败 |
| `--ip-max-lost-ratio` | 可选、无默认；unknown不因此失败；只针对导出LOST诊断比 |
| `--format` / `--use-md5` | 实际默认extbinary；支持text/binary/extbinary；md5默认false、仅extbinary生效；GCC在writer创建时报错 |
| `--pid` | 默认不筛选；只匹配该PID，非自动子进程集合，负数拒绝、永不匹配-1 |

比率语法为0、1或0后1–9位小数（如0.95），精确整数分数比较。已有trim/density、show-mmap-events等仍可用，但正式分析参数要锁定。CS/stack/probe显示、unsymbolized、skip-symbolization、use-offset/base、update-total、fill-zero-for-all、populate-symbol-list、kernel、canonical-fname等选项IP模式明确拒绝；完整清单见补丁7带入的 `llvm/docs/CommandGuide/llvm-profgen.rst:209–231`。其中 `--use-dwarf-correlation` 不能绕过probe节拒绝。

隐藏接口 `--show-ip-address-counts`、`--show-ip-boundaries`、`--ip-test-inject-failure` 只用于验收；**注入选项及其rsp/单双横线/分离值等写法不得进入正式评估**。证据：[第一批准入核对](../profgen/eval/prep/06_registration_checklist.md)、[0007文档补丁](../../patches/profgen/0007-llvm-profgen-Document-IP-mode-and-finalize-options-and-reports.patch)、[0009](../../patches/profgen/0009-llvm-profgen-Exclude-IP-samples-with-missing-non-lea.patch)。

### C.2 板上perf与负载（历史有效命令，非本轮执行）

两板均用各自架构的 `/opt/afdo_agent/tools/perf` 与 `/opt/afdo_agent/lib/libLLVM.so.22.1`；不能混推架构。所有HOME/TMPDIR/PERF_CONFIG/GST_REGISTRY/XDG_CACHE_HOME/cache/output置于该专用目录；先完成身份、依赖、SHA、root/governor门禁，才允许采集。正式硬件cycles不可用须停止，**不能因工具通用文档提到cpu-clock就切软件事件**。

RPi4第一轮实际命令结构（`collect.sh:47–57`，固定中档例；EVENT换成`-F 1000`为频率模式）：

```bash
P=/opt/afdo_agent/tools/perf
RUN=/opt/afdo_agent/work/NEW_RUN
export LC_ALL=C LD_LIBRARY_PATH=/opt/afdo_agent/variants/ffmpeg-thumb-S/usr/lib:/opt/afdo_agent/lib
"$P" --buildid-dir "$RUN/buildid" record --buildid-mmap -e cycles -c 1000003 \
  -o "$RUN/perf.data" -- "$P" --buildid-dir "$RUN/buildid" stat \
  -x ';' -e cycles,instructions,task-clock -o "$RUN/perf-stat.csv" -- <负载命令>
"$P" --buildid-dir "$RUN/buildid" evlist -v -i "$RUN/perf.data"
"$P" --buildid-dir "$RUN/buildid" script -i "$RUN/perf.data" \
  --show-mmap-events --show-lost-events -F pid,tid,event,period,ip,dsoff > "$RUN/perfscript.txt"
"$P" --buildid-dir "$RUN/buildid" buildid-list -i "$RUN/perf.data" > "$RUN/buildid-list.txt"
```

实际负载由 [common.sh:161起](../../tools/profgen/board/common.sh) 产生：`gst-launch-1.0 -q filesrc location=<BBB或ToS> ! qtdemux ! h264parse ! avdec_h264 max-threads=1 ! video/x-raw,format=I420 ! filesink location=<RUN内FIFO> sync=false`；FIFO另一端SHA256，确保解码结果可核对。`collect.sh`另保存target PID/maps、全部stderr/返回码、环境与分段。**这些第一轮脚本尚不能代替Q.5 #12的新遥测板上验收。**

RPi5报告09实际300帧负载示例（四次fixed/multi/freq/buildid都成功；buildid一份加该开关）：

```bash
export LC_ALL=C LD_LIBRARY_PATH=/opt/afdo_agent/lib
/opt/afdo_agent/tools/perf --buildid-dir "$RUN/buildid" record \
  --buildid-mmap -e cycles -c 1000003 -o "$RUN/perf.data" -- \
  gst-launch-1.0 -q filesrc location=/opt/afdo_agent/work/bbb_720p_h264_60s.mp4 \
  ! qtdemux ! h264parse ! avdec_h264 ! identity eos-after=300 ! fakesink sync=false
/opt/afdo_agent/tools/perf --buildid-dir "$RUN/buildid" script -i "$RUN/perf.data" \
  --show-mmap-events --show-lost-events -F pid,tid,event,period,ip,dsoff > "$RUN/perfscript.txt"
/opt/afdo_agent/tools/perf --buildid-dir "$RUN/buildid" buildid-list -i "$RUN/perf.data" > "$RUN/buildid-list.txt"
```

RPi5探测用的是系统`/usr/lib64/libavcodec.so.62.11.100`，不是新评估S库；不得用09样本套新build-id。导出字段顺序按perf打印为pid/tid、period、完整event、ip、`(DSO+0x文件偏移)`；保留全部映射/LOST/特殊样本，不加brstack、不筛选。[09§2–5](../probe/09_rpi5_prefreeze_checks.md)、[12§16](../profgen/impl/12_board_round1.md)

### C.3 质量报告与失败契约

schema_version=1；顶层为 `tool,input,event,semantics,identity,mapping,samples,isa,boundaries,lost,throttle,ratios,sanity,coverage,thumb_dwarf_normalization,consumer_hints,warnings,verdict`（加schema_version）。计数为整数；比率保存分子/分母；未知为`"unknown"`，确认不存在用`"none"`，特定成功failure字段为null，不用空字符串。数组排序和逐字段定义在0007文档及0008/0009增补；15报告396字段路径核对双向差集空。

主要消费规则：先看进程退出码，再看 `verdict.conversion`（ok/failed）、`failure_stage`、`reason`；核对 `verdict.identity`/identity详细证据、usable_ratio_check、sample_threshold_check、lost_ratio_check。`sampling_adequacy`只有insufficient/unknown，不因全部门槛没报错就输出“采样充分”；throttle未知，**工具质量JSON不是板上遥测资格判定器**。verified表示有ID身份依据，unverified表示缺证据获准继续；已知不匹配/歧义会失败。`thumb_dwarf_normalization`记录GNU AS范围/别名一致性和不可用原因；`samples`含nonleaf_line_zero排除。

正常成功exit0；失败非0（验收通常1，但调用方不要依赖所有失败只有1）。不创建/不覆盖旧profile；非路径冲突失败应原子替换失败JSON。输出为`-`、profile/report互为别名或与输入别名时：加载ELF/建临时文件前拒绝，两输出都不写；这是故意不写失败报告的唯一路径冲突例外。报告自身写/提交失败也可能无新报告，旧报告保留，stderr说明，不能凭旧ok报告宣布成功。profile临时文件最后rename；报告与profile不是断电原子的双文件事务。证据：[08质量/失败契约](../profgen/impl/08_patch6_report.md)、[09整理](../profgen/impl/09_patch7_report.md)、[15报告](../profgen/impl/15_patch9_nonleaf_line0.md)；本地 `IPQualityReport.cpp:453–823`。

### C.4 FFmpeg实际注入与部署

实测采用 **本地评估spec宏 + GBS --define选择变体**，不是修改用户根目录gbs配置。`temp/eval-prep11/ffmpeg/packaging/ffmpeg.spec`保留平台`%{optflags}`：

```text
%global eval_common -fdebug-info-for-profiling -funique-internal-linkage-names
R:  %global eval_instrument -fprofile-generate -mllvm -disable-preinline
C:  %global eval_instrument -fprofile-instr-generate -fcoverage-mapping
G5: %global eval_instrument -fprofile-generate
S:  eval_instrument为空
Thumb: eval_arch=-mthumb / --enable-thumb
A32:   eval_arch=-marm / --disable-thumb
CFLAGS="%{optflags} -fPIC ..."
CFLAGS="$CFLAGS -D__TIZEN__ -DTIZEN_FEATURE_LIBAV %{eval_common} %{eval_arch} %{eval_instrument}"
./configure ... --extra-ldflags="-Wl,--build-id=sha1 %{eval_instrument}" ...
```

`tools/profgen/eval_build.py:75–77`用 `gbs -c <WORKDIR内已核验配置> build ... --define 'eval_isa thumb|a32|a64' --define 'eval_variant S|R|C|G5'`；并行度由当前任务资源授权决定，不能照旧脚本默认擅自开大。实际值以build-manifest为准。FFmpeg configure追加O3，spike平台Os；已完成12种架构/类型代表源文件选项核对才全量构建；本次产物**无LTO**。源码/编译命令跨变体路径一致策略、工具/runtime与生成侧ID见[11§7–10及05/05b证据](../profgen/impl/11_eval_prep.md)、[构建执行器](../../tools/profgen/eval_build.py)。

**`-fprofile-sample-use`在最终FFmpeg G1–G4尚未实施消费构建**，不能编造“已经运行的FFmpeg命令”。下一轮按同一spec的显式消费变体增加 `-fprofile-sample-use=<锁定profile>`，保留两项profiling flags，并依设计加 `-fno-sample-profile-use-profi -mllvm -sample-profile-use-profi=<bool>`、salvage开关/覆盖陈旧诊断。若未来开LTO，链接也带sample-use及lld `-Wl,-mllvm,...`；生成侧只改CFLAGS不够。已完成的小C消费验证在[10§2](../profgen/impl/10_host_verification.md)，不能替代FFmpeg消费验收。

板上不rpm安装：主机解包runtime RPM后推到 `/opt/afdo_agent/variants/`，按清单SHA核对，运行时LD_LIBRARY_PATH选择变体；读/proc/PID/maps和buildid-list确认实际目标库。debug留主机，必须与RPM runtime同ID；BUILD链接物ID可能经打包改变。脚本：[common/collect/measure/integration](../../tools/profgen/board/)、[board_plan](../profgen/eval/board_plan.md)。BBB/ToS训练测试材料与SHA见11媒体证据及12报告；只在专用目录写profraw、perf、registry/cache。拉回→实际路径存在→全量SHA一致→只删除清单确切RUN，任一步失败不删；root/governor最后恢复。未来真实板操作仍需单独任务授权。

## D. BOLT只读事实

本地 `src/llvm` HEAD=`f999bd406c0a70fe8107aa992164fe6945c5d46a`，以下是该快照事实，不是新BOLT构建验收。核心源码SHA见末表，GitHub PM可据这些路径和摘录复核，不能假设结果仓库包含完整src树。

1. **Tizen spec当前不构建BOLT**：`src/llvm/packaging/llvm.spec:241`的 `LLVM_ENABLE_PROJECTS="clang;lldb;clang-tools-extra;lld;compiler-rt;openmp"`没有bolt。x86_64目标列表`:218`包括X86/ARM/AArch64/BPF，只说明后端可用，不等于llvm-bolt/perf2bolt已打包。
2. **源码能力支持主机构建处理AArch64的BOLT**：`bolt/README.md:12–14,55`明确X86-64/AArch64 ELF与 `LLVM_TARGETS_TO_BUILD="X86;AArch64"`、`LLVM_ENABLE_PROJECTS="bolt"`；`bolt/CMakeLists.txt:65`支持集为AArch64/X86/RISCV。可作为另一个主机构建方案，不能用ARMv7目标支持推导BOLT支持Thumb。依赖、主机链接成功和Tizen目标可优化性均尚未实测，本轮不构建。
3. **主机PATH的perf目前不可用**：`/usr/bin/perf --version`退出2，stderr为 `WARNING: perf not found for kernel 6.17.0-1033`，建议linux-tools-6.17.0-1033-oem等安装。本轮没有安装；没有穷举工作目录外其他perf，也没做硬件权限试录。不能称主机已可执行perf2bolt原生perf.data流程。
4. **`perf2bolt -ba`默认仍调用perf**：`DataAggregator.cpp:48–54`的ba是basic-events别名；`:195–215`在没有pa/预给文本时查找perf并运行 `script -F pid,event,ip`，还要映射/任务/build-id侧信息。它不是llvm-profgen的dsoff读取器，不能直接把本项目导出原文当已兼容输入。
5. **有不依赖主机perf的源码路径，未在项目端到端验证**：
   - `--pa`：`:120–128,195–198,338–340`明确跳过perf和perf.data魔数约束；`:1269–1372`接受 `E <event>`、`S <location> <count>`，S进入BasicSamples。仓库自身fixture `bolt/test/X86/Inputs/pre-aggregated-basic.txt`有 `E cycles`、`S 4005f0 1`；`pre-aggregated-perf.test`含对应测试。可在板上导出后，由经过身份/地址验证的转换器得到预聚合地址计数，再 `perf2bolt --pa -ba -p <预聚合文本> <同一未strip ELF> -o <fdata>`。**转换器尚未实现/验收**；须确认PIE/DSO地址归一化、build-id、多映射、事件及sample/period语义，不伪造缺失的分支边。
   - 直接fdata：`DataAggregator.cpp:2215–2225`输出 `no_lbr [events]`与位置/hits；`DataReader.cpp:1041–1059`支持读取。以后可做独立转换器生成basic fdata，或先pa→perf2bolt生成fdata；不能拿AutoFDO行级profile冒充BOLT块/地址profile。
   - 隐藏 `--perf-script-events`也跳过perf；但`:414–418`是 **`ParsingBuf = opts::ReadPerfEvents`**（直接文本字符串，不是自动读取文件名），同一选项用于不同解析流程。这里只登记源码存在，不推荐当现成板上文本文件接口。
6. **emit-relocs/保留符号表可行性**：链接器选项与BOLT支持有依据（README:12–14,122），本项目可设计独立aarch64 BOLT变体，最终链接加 `-Wl,--emit-relocs`，保留同一最终ELF的symtab与relocations，部署到/opt。**现有RPM runtime经strip、debug代码为NOBITS，不等于适合BOLT的未strip运行ELF**；需调整该变体的打包/保留策略并验证ID与可执行性，不能仅打开emit-relocs就声称已可用。Tizen实际保留、共享库改写与RPi5运行尚无验收；本轮不改spec。
7. **AArch64限制**：`RewriteInstance.cpp:2280–2282`实际是警告 `non-relocation mode for AArch64 is not fully supported`，不是证明完全支持，也不是所有输入一律硬拒绝。应优先具备relocations的路径。无LBR/SPE/BRBE时只有IP热度，不等于完整边/执行次数；代码/数据混排、汇编、间接跳转、异常处理/调试更新、ABI和部署兼容都需独立验证。BOLT README还要求未strip符号表，指出与GCC `-freorder-blocks-and-partition`不兼容。Tizen最终对象的实际限制未知，不能从aarch64后端存在推导收益。

## E. CodingSystem与skill

本轮只读本地 `temp/CodingSystem`：HEAD仍是 **287d51c674e2b7d38605098338ff94fc8bb4e4fa**，没有拉取框架远端。因此以下是本地主机可证的版本，**远端2026-11-14最新进度未知**。

- HLD `docs/00_Framework_HLD_v1.0_draft_frozen.md`为v1.0-draft-frozen、DRAFT FREEZE；正式contract v1.0仍要求真实Compiler Agent消费、五类fixture、兼容矩阵等条件。
- `docs/01_Contract_Spec_v0.11.md`为v0.11 Draft/复审中，包契约 `contract_version="1.0.0.dev1"`。`git ls-tree`中的framework/agents实际全为.gitkeep，包括framework/skill；不能说框架、SDK或Agent已实现。
- 这里的 **Skill是HTTP服务契约**：`Contract_Spec:317–322`的POST /runs、POST /runs/{id}/patches、GET状态/结果、cancel；有request_id幂等、鉴权与错误码。`HLD:403`写明 `framework/skill/ # Skill HTTP server`。它不是已经定义好的某个CLI的SKILL.md包格式，不能把两种skill概念混为一谈。
- 可供GitHub PM直接复核的固定源码：[CodingSystem快照](https://github.com/lhmax2010/CodingSystem/tree/287d51c674e2b7d38605098338ff94fc8bb4e4fa)；本项目的[06框架证据](../probe/evidence/06_codingsystem.txt)已有版本、契约与代码树摘录。业务指南/最终契约/实现后续进展仍待核查。

主机只做PATH存在性检查：`codex`→`/home/linhao/.local/bin/codex`，`claude`→`/home/linhao/.bun/bin/claude`，`cline` CLI不在PATH。VS Code Insiders在运行，但不能据此证明Cline扩展已安装或可用；也没测试任何AI登录/调用。

关于目录约定：本会话提供的技能目录元数据列有 `.codex/skills`、`.agents/skills`及插件技能缓存，技能入口是SKILL.md；这是**会话提供的目录信息，不是本轮读取主机目录所得，也不是项目已选定的skill规范**。为遵守WORKDIR边界，未读取这些工作区外技能/认证/编辑器配置；Codex CLI具体版本启用哪些搜索目录、Cline的目录格式与安装状态均未核实。后续workflow→skill设计应先选消费者，再确认其实际接口，不能以CodingSystem HTTP契约替代CLI安装格式。

## F. 交接意见（建议，不改变设计或授权）

1. 最重要的是把“工具正确性已验收”“静态可对齐”“质量统计”“真实收益”拆开报告。补丁9、C1/独立GNU核对、消费端诊断提供正确性证据；模拟开关只验证登记场景，不能代替真实RUN、评价域说明与性能。
2. 若继续完整评估，优先解决Q.5 #12和散热，再锁#17/18/19；不要先算真实指标再补预注册。旧70组仍可能用于旧阶段，旧遥测unknown不应被伪造为合格；两个阶段的混合总体不能外推为新散热条件独立结果。
3. 可简化的是非主结论的实验扩展：BFI/IR分支概率只描述；create_llvm_prof、工具链升级复用属于可选；probe尚未准入应独立处理。缩小G1–G4交互矩阵或跳过步骤5/6必须PM明确改变交付范围，不能悄悄删组后宣称默认已验证。
4. 主要风险：RPi4散热/共享内核环境变化；完整kmsg和采样器自身扰动；大批temp原件只有主机副本；远端报告保留历史而“最新状态”分散；FFmpeg只有约一半C_dc参考DA进入可测量域；少RUN/稀有事件及阶段退化；不同toolchain/build-id静默混用；把BOLT源码支持误当Tizen可交付。
5. 我建议先由PM在“完成既定评估”与“有限范围DWARF工具交付、显式保守策略、无收益声明”之间作清晰范围决定。两者都不能省略身份、旧输出保全、LBR回归及干净发布构建。之后按本轮用户指定顺序：**llvm-profgen增强完成 → AutoFDO/BOLT workflow → skill → Agent**。

## G. 主机只读取证与边界

源码仅从WORKDIR读取，未重编Clang或LLVM。BOLT/开发树文件未必在结果仓库跟踪，所以这里封存本轮只读SHA以便下一位开发者定位；不上传整个源码树：

| WORKDIR路径 | SHA-256 |
|---|---|
| `src/llvm/packaging/llvm.spec` | `7962d176484920de6138d70c7e8a8e1764dfada6655abf0332e9748167e889fd` |
| `src/llvm/bolt/CMakeLists.txt` | `cc11c0c511d034a4d8b921c77f1c55fcfd350ca9eb469b1c6d82bfe03ca4fa6a` |
| `src/llvm/bolt/lib/Profile/DataAggregator.cpp` | `4d092be8245353b3636e056676db601345e8197aa5c4cfd5f22b34541a68275f` |
| `src/llvm/bolt/lib/Profile/DataReader.cpp` | `09288d1b9a7e23013216f7e0a3cb350c7bff6ad6d7aa69f78f2f0d84f1efb949` |
| `src/llvm/bolt/lib/Rewrite/RewriteInstance.cpp` | `7d4523fc5584b34a17fb9b3b5b11da46df050a62f57818d75e61b2a343aa2b66` |
| `temp/llvm-profgen-enh/llvm/tools/llvm-profgen/llvm-profgen.cpp` | `dc705790bcdd4ca61161d1c3a02f987faa6f1fdbe47d1b181234ca6af5eea1d5` |
| `temp/llvm-profgen-enh/llvm/docs/CommandGuide/llvm-profgen.rst` | `94c9145446abf0fba8bff6bb9ac336e6a9c991f3543131d3897ce80190bd9bbf` |
| `temp/eval-prep11/ffmpeg/packaging/ffmpeg.spec` | `6e26e32c6598379bbba64a7a3b280c3de435a31a49f311c2237a428af472da91` |
| `docs/profgen/impl/evidence/12/56_matrix_summary.json` | `53b5d26b24944b77ec6d95f9b617f716757764f0619bcfda66dd66e997059451` |

当前工具SHA另见C.1。源码行号绑定这些SHA，不宣称上游最新版本行号相同。后续仅提交本报告与STATUS；不推LLVM、Gerrit或llvm-optimize。没有本轮板上状态变更、无root/governor恢复动作；最后历史恢复状态与现在未知明确分开。

本轮所有主机命令在nice19/ionice-c3、systemd user scope 3GiB/100%下串行执行，启动前检查MemAvailable≥4GiB。首次保存的可用内存读数为23,730,276KiB；本报告保存的首读与生成scope两点中最低为23,761,817,600 B（不是全程最低值）。报告生成scope的资源快照如下。早期短scope结束后未连续封存memory.peak，因此**本轮全部短命令的完整峰值未知**，不把最后一个scope值冒充全轮峰值；未发生scope OOM或资源门禁拒绝。失败诊断已如实记载：主机perf版本命令exit2；少数定位旧文件名的rg返回不存在，随后以实际路径定位，未执行构建或修复工具。

```json
{
  "checked_at": "2026-11-14T15:21:45.232068+08:00",
  "MemAvailable_bytes": 23761817600,
  "scope": "/user.slice/user-1000.slice/user@1000.service/app.slice/run-r745009995c4e4f939ee26f9719a8c641.scope",
  "memory.peak_bytes": 16506880,
  "memory.max": "3221225472",
  "cpu.max": "100000 100000",
  "note": "本次报告生成scope的只读资源快照；不代表早期短scope峰值"
}
```

交接完成后停止；不登记修正案3，不执行下一个评估项目。
