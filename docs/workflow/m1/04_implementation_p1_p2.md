# M1 第一、二阶段主机实现与验收（design v0.3）

日期：2026-11-16。入库提交 `db8f687`；v0.3 为最终设计，不再评审，后续变更由用户决定。文档移动前后 SHA-256 均为 `1d8fdfb319a9faf9a1660c7905c2d59a8749ef708afaf8d4b832c1f9fbbe999a`。同时登记 hq `efb6b506d770dafba271b82960c1eb8e04377150` 已审阅、可发布；本轮未修改 hq。

本轮完成主机模块/合成验收、板上脚本静态检查、唯一授权的 Thumb `with_autofdo=1 + afdo_diag=1` 诊断构建。**没有接板、部署、采集、性能测量或质量矩阵；不是自动化 M1 全流程验收。** CLI 的板上阶段仍明确限定 dry-run，这是本轮授权的接口边界。

## 1. 模块与条文对应

使用 Python 3.12.3 标准库，无第三方依赖、未安装软件。入口说明与 job 字段见 [workflow README](../../../workflow/README.md)。

| 模块 | 设计条款与实现 | 本轮验收 |
|---|---|---|
| [config](../../../workflow/afdo_wf/config.py) | §6：schema v1；未知字段/枚举、ISA/宏矛盾、period/freq、train/test SHA+segment 重叠、非有限值、hook JSON 与 higher 拒绝 | 正负夹具；真实 package.toml 结构加载 |
| [receipts](../../../workflow/afdo_wf/receipts.py) | §13：原子 flush/fsync 收据、直接输入与上游 SHA DAG、resume 重验、redo 后代失效、cleanup_pending、verified-pull 先于精确目录删除 | 改名不变但内容变化、写失败、删除前/后崩溃、SDB drop、不同板身份、redo collect→rebuild |
| [build](../../../workflow/afdo_wf/build.py) | §9.4：独占工作流锁、新 root、-j2/threads1、独立 scope、启动门禁、60秒资源采样，只停本任务单元；元数据/RPM SHA、createrepo_c 冻结接口、RPM/ELF manifest | 资源边界/低内存两次/低磁盘、元数据篡改、冻结失败；一次真实离线构建 |
| [buildlock](../../../workflow/afdo_wf/buildlock.py) | §9.1：recorded-switches 去重集合+config.mak；verbose-make 多重集合且必须形式/取证产物相同；包/header、源码/patch/spec/布局/宏/GBS/冻结仓库比较 | 漂移/取证不全拒绝；真实两目标311/97命令及5项设置比较 |
| [profgen](../../../workflow/afdo_wf/profgen.py) | §5 S4：清单实路径生成锚定regex、显式max/none/none/none、退出码/quality门禁、诊断身份不得发布、七字段口径锁、DSO内合并后跨DSO树碰撞检查与SHA锁定 | 命令/regex、身份与非零退出、不同内联树/相同树、候选输出保护；本轮不重转真实采集 |
| [consumption](../../../workflow/afdo_wf/consumption.py) | §5 S5：标准库流式解析LLVM YAML子集；object_to_target唯一归属；每目标正数AppliedSamples、准确profile选项路径/chroot SHA、.text差异 | 双目标/单目标/零样本/缺源码/错路径/损坏YAML；408份真实目标记录全量解析 |
| [stats](../../../workflow/afdo_wf/stats.py) | §8：平衡种子顺序、N公式、成对log比、20,000 bootstrap、expm1端点、t/中位数辅报、20%上限、缺失、敏感性、遥测窗口与优先级、重试历史 | 评审B反例、恰好±ε/跨界/界内/镜像、缺失、20%边界；原15 block独立调用复现 |
| [report](../../../workflow/afdo_wf/report.py) | §5 S7：同一结构写report.json/report.md；必需字段、有限数、消费/oracle/build-lock/身份不足不发布；固定免责声明 | 缺字段/非有限数不写、诊断数据不能发布 |
| [CLI](../../../workflow/afdo_wf/cli.py) | §12：10个命令（含run），9个阶段；host job API、收据恢复、redo；板上接口强制dry-run | dry-run全部阶段、不允许live board阶段、错误收据 |
| [board contracts](../../../workflow/afdo_wf/board.py) | §5 S6/§13：每个must-load与全部已映射deploy-set、oracle、注入transport的root/governor finally恢复 | 系统库混用、空oracle、S3/S6失败、SIGTERM、待恢复身份变化 |

主机核心不嵌入 FFmpeg 的视频管道。FFmpeg 的包配置、720p hook、source/patch 位于 `workflow/packages/ffmpeg/`。配置沿用试跑：Thumb、cycles/1000003、3次、period_unit=1000003、CPU3、超时600秒、预热2、blocks=15、ε=1%；无额外质量阈值，min_target_share=0表示试跑未设置该政策，不将设计中的示例阈值冒充已批准值。inputs.toml 记录 BBB/ToS SHA、片段内0–60秒及oracle；原素材来自整片300–360秒，ToS不是全新holdout。

## 2. 测试与静态验收

- **94 个 unittest 全部通过**，完整名称/输出见 [synthetic-tests.log](evidence/09/synthetic-tests.log)。单元数据为合成夹具（包括构造的YAML、ELF命令输出、收据、maps、遥测）；配置加载使用交付的package.toml。不会读取真实sample profile或连接板子。
- 历史计时复现是显式单独的 [reproduce_pilot.py](../../../workflow/tests/reproduce_pilot.py)，不混入“合成”单元测试名义。只读旧plan/rounds/blocks JSON，未重算profgen受控质量量。
- 全部12个board/workload脚本通过 `bash --posix -n`；旧Bash无 `${var,,}`、不依赖timeout命令。shellcheck在本机不存在，未安装；未把语法检查说成板上运行验收。
- watchdog负例仅启动本任务自己的合成 `sleep` 进程组，超时退出非零；没有信号发送给其他构建或板子。
- `git diff --cached --check` 对普通代码/文档通过；完整检查仅报告两个补丁文件中的空白上下文行（unified diff 的单空格上下文前缀），保留原始patch/diff及其SHA，不改写这些行。
- [validation.json](evidence/09/validation.json)记录命令与退出码。最终轻量验证scope峰值 33,681,408 B，执行 5.367 秒。

发现并修正的实现问题均保留记录：早期测试把run错计为第10个阶段（命令10、阶段9）；真实LLVM记录Pass为 `sample-profile-impl`；DebugLoc的Column会折到下一行。后两项原始异常见 [首次解析失败](evidence/09/parser-initial-failure.txt)、[折行失败](evidence/09/parser-wrapped-location-failure.txt)。依据本地LLVM22.1.8 `llvm/include/llvm/Transforms/Utils/SampleProfileLoaderBaseImpl.h:56,434,479`，修正解析并添加折行正例，没有修改LLVM、放宽正数/来源门禁或再次构建。

## 3. 试跑统计复现

采样实现固定为 `random.Random(seed).choices`，线性percentile，bootstrap 20,000次；顺序先构造8个AB/7个BA再按原seed shuffle。两个区间端点先expm1，再与相对ε比较。缺失、异常块规则不靠替换原始数据补齐。

| 量 | 15个正式block | 13个干净block敏感性 |
|---|---:|---:|
| 相对耗时估计 | -2.565157872% | -2.537450726% |
| bootstrap 95% CI | [-2.859136595%, -2.256299179%] | [-2.867768694%, -2.193959062%] |
| 变换后的t区间 | [-2.906041866%, -2.223077078%] | [-2.928897340%, -2.144425575%] |
| 数值判定 | faster | faster |

15个block的顺序、两组原始秒数和输入SHA见 [pilot-reproduction.json](evidence/09/pilot-reproduction.json)。三位小数复现 **−2.565%、[−2.859%, −2.256%]**；BASE CV为 0.365635424%。这是对已授权历史数值的回归，不是新实验或重新判资格。

## 4. afdo_diag 补丁与唯一诊断构建

在fix1上只增加如下3行（[完整差异](evidence/09/spec-delta.diff)），无原spec绕过：

```spec
%if 0%{?afdo_diag}
%global profile_use %{profile_use} -fsave-optimization-record=yaml -foptimization-record-passes=sample-profile
%endif
```

新 [profiling.patch](../../../workflow/packages/ffmpeg/build/profiling.patch) SHA-256：`6dd4736e86d7ab34630eca09357b79eab7835f7d7a2de0108b38c6c7d093dc09`。旧fix1 SHA `0c94e54d252ad1ecbc625f629af090b257edba4cd3753d76352fd031486243b6` 不变。新patch对5fe76358原index的 `git apply --cached --check` 通过；with_autofdo/afdo_diag的4种0/1组合rpmspec展开均符合预期，见 [patch-checks.json](evidence/09/patch-checks.json)。

在 `temp/workflow-p1p2-20261116/ffmpeg/` 独立检出构建，使用试跑归档的108个RPM及resolved buildconf，逐包SHA和安装后header SHA核对一致；原源码树、旧root、旧证据均保留。实际GBS命令（外层资源scope见 [build-command.json](evidence/09/build-command.json)）：

```bash
gbs -c "$WORKDIR/temp/workflow-p1p2-20261116/frozen.conf" build \
  -A armv7l --spec ffmpeg.spec --include-all \
  --skip-conf-repos \
  -R "$WORKDIR/temp/m1-pilot-v02-20261116/build/repo" \
  -D "$WORKDIR/temp/m1-pilot-v02-20261116/build/repo/tizen_unified_standard.conf" \
  --buildroot "$WORKDIR/temp/workflow-p1p2-20261116/root-afdo-diag" \
  --threads 1 --define '_smp_mflags -j2' \
  --define 'profile_isa thumb' --define 'with_autofdo 1' --define 'afdo_diag 1'
```

| 构建核对 | 结果 |
|---|---|
| GBS退出码 / 墙钟 | **0 / 118.865秒** |
| 启动门禁 / 资源停止 / 重试 | 立即通过 / 0 / 0 |
| 记录中最低MemAvailable | 19,599,581,184 B（18.254 GiB） |
| 最终cgroup峰值 / swap峰值 | 1,695,338,496 B（约1.579 GiB）/ 0 |
| RPM / 目标优化记录文件 | 23个二进制RPM / 408份opt.yaml |
| 冻结安装包 | 108条，与试跑逐行一致 |
| chroot profile | `61f03b59262e3ce7ce758219d65848a33b5a0549131c362a6769ad10386f2cf2`，一致 |

[资源原文](evidence/09/build-resources.json)、[结果](evidence/09/build-result.json)、[systemd最终资源字段](evidence/09/scope-final-journal.json)保存。实际scope为6G/MemoryHigh5G/CPU200%、nice19/ionice-c3；监督service与其他任务隔离，结束inactive/0。构建模块随后补了child结束前落盘最终峰值，已用合成子进程测试，未为此重跑GBS；本次实际峰值由systemd的 `MEMORY_PEAK` 精确复核，和运行中最大读数相同。

## 5. consumption 与构建证据

| 目标 | C命令条数 | 正数AppliedSamples记录 | runtime = debug build-id | 判定 |
|---|---:|---:|---|---|
| libavcodec | 311 | 1921 | `e72d7101bd7b5bb7b5f8274e9e4ac8d9cf752b12` | verified |
| libavutil | 97 | 51 | `6b982e6eb71726a9ba987772210b26dbeacaee64` | verified |

- 两目标所有归属C命令都有准确的 `-fprofile-sample-use=/home/abuild/rpmbuild/SOURCES/autofdo.extbinary` 及两项记录选项。chroot文件SHA与锁定输入一致。
- 408份目标opt.yaml全量处理，按build-relative对象路径映射至对应DSO。正数记录不是perf样本总量，不将其用于质量量或采样充分性判定。实例含Function、源码位置、NumSamples及对象路径，见 [consumption.json](evidence/09/consumption.json)。
- 两目标`.text`均不同于BASE，**均与原试跑AFDO的`.text`逐字节SHA一致**：本轮诊断选项没有改变这两个目标的代码段。新runtime/debug身份一致；整体ELF/build-id与旧AFDO不同不冒称全文件相同。
- recorded-switches方式：两侧311/97条归属C命令，删除仅声明的profile/diagnostic选项后集合差异0；config.mak的CC/CFLAGS/ASFLAGS/LDFLAGS/SHFLAGS全部一致，见 [command-comparison.json](evidence/09/command-comparison.json)。verbose-make方法本轮只做合成门禁测试，真实698条等价证据来自已存试跑，未新增取证构建。
- 本轮仅按授权做一次诊断消费构建，补丁较旧BASE多了afdo_diag定义，**不把这次与旧BASE的比较冒称“新版完整实验的patch SHA相等”**。正式自动化实验需同新版补丁的BASE/BASE-r/AFDO与完整build lock；不能跳过该门禁。
- 既有debugedit DWARF5诊断保留在原始构建日志，构建成功；不宣称debugsource所有路径改写完整。RPM和目标ELF/SHA见 [rpms.json](evidence/09/rpms.json)、[artifacts.json](evidence/09/artifacts.json)。

## 6. 板上脚本与恢复范围

`workflow/board/`提供会话governor保存/恢复、部署SHA、进程组watchdog、完整perf导出、后代进程maps、逐秒遥测、开跑温度门禁和计时轮。只接受 `/opt/afdo_agent/` 输出路径，root保存/恢复由注入的host session transport负责。代码在主机做语法/合成测试；没有sdb或板上动作。

现阶段live transport和单命令端到端调度未启用；`run --dry-run`写全部阶段计划，不制造完成收据。后续板上验收还需真实工具/能力预检、plugin factory/registry核验、每工作负载PID清单与maps门禁、遥测窗口实际采样、观测开销、verified-pull/SDB断连恢复等。未接板的部分不写成已验收。

## 7. 已知限制与待用户决定

1. v0.3“两个变体的标记率明显不同”没有数值判据。本实现保留显式 `clear_flag_imbalance` 输入；缺少评估时封顶inconclusive，不自行定阈值。后续正式自动化测量需要用户/PM固定该政策。
2. 第二段不同编码配置测试片仍按设计§16由用户/owner选择；本轮仅复用已授权锁定profile验证诊断构建，不代替正式M1输入登记。
3. YAML解析器是LLVM opt-record所需的安全子集，不是通用YAML；相关字段不支持或不完整时失败，不猜测。已对本次408份真实记录验收。
4. shellcheck未安装；板上脚本未部署或运行。phase1/2通过不等于§14自动化M1通过。
5. 构建日志、1.16MB命令明细、原始opt.yaml/RPM只留temp；仓库保存索引SHA与摘要。原始失败取证也保留。本轮没有改变设计、既有报告/证据、hq、Gerrit或保护的本地配置。

## 8. 输入披露与索引

按Q.5第17项，唯一读取/复制/编译消费的真实profile是原试跑锁定package profile，目的为本任务明确授权的诊断消费验证；没有新生成sample profile，没有质量矩阵。历史15 block回归只读计时JSON。时间、路径、SHA与用途见 [profile-access.json](evidence/09/profile-access.json)。

所有代码和证据SHA、生成命令/原始大文件路径见 [index.json](evidence/09/index.json)。生产代码在 `workflow/`；本轮prepare/verify/final-check脚本保存在 `temp/workflow-p1p2-20261116/` 并登记SHA。原root、旧编译器、原工具和所有既有temp目录均未删除。
