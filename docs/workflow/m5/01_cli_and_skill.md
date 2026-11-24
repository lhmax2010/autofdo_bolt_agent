# M5 第一阶段 · CLI 定稿与技能初稿

依据 [workflow v0.3 §12–14](../01_afdo_bolt_workflow_design_v0.3.md#12-code-layout-and-interface-m1-minimum)。验证在独立 worktree 中进行。真实演练只读取 M1 attempt-11 和 M2a 的封存产物，未连接开发板、未启动 GBS、未执行 redo 或 live run。

## CLI 定稿

命令均以 `python3 -m afdo_wf` 开头。从仓库根目录设置 `PYTHONPATH="$PWD/workflow"`。只读演练用 `PYTHONDONTWRITEBYTECODE=1` 或 `python3 -B`，使 Python 本身也不生成缓存文件。

| 子命令 | 输入与结果 |
| --- | --- |
| `status --job JOB.json` | 打印按 `stage_order` 排列的 DAG 状态、收据路径、失败原因码及直接输入和上游收据 SHA 核对。状态为 `completed`、`invalidated`、`pending`、`failed` 或 `cleanup_pending`。 |
| `--redo STAGE --job JOB.json [--reason TEXT]` | 对可变作业执行单独的归档操作。将该阶段和所有下游的现有收据归档，并返回失效收据的路径、SHA 与受影响阶段。 |
| `run --job JOB.json --dry-run` | 打印工作计划、输入、各阶段门禁、计划动作及预计板上操作。支持 `--stop-after afdo-audit` 等停止点。结果只在 stdout。 |
| `init --package PACKAGE.toml --inputs INPUTS.toml --platform PLATFORM --job JOB.json --output RUN_DIR` | 结合 `--media-dir DIR` 或可重复的 `--media ID=FILE` 生成 job 草稿。可指定 `--workdir DIR` 与 `--experiment ID`。打印草稿 SHA 与须填写的主机、板子及运行字段。 |
| `explain STAGE` | 打印阶段的用途、依赖、输入、门禁、产物、预计板上操作与收据字段。与 dry-run 共用 [阶段元数据](../../../workflow/afdo_wf/stages.py)。 |

`status` 核查现有记录。它用 `input_sha` 和 `upstream_sha` 分别报告直接输入与上游收据的匹配结果。历史失败保留在 `last_failure` 或 `last_run_failure`。已完成的失败重试仍按有效成功收据显示。S8 来自最终清理记录及 journal，可显示 `cleanup_pending`。运行时继续重验完整收据链及所有绑定产物。对真实归档的 dry-run 列出可复用记录，并回读已登记的计时种子；其 `planned_live_session` 字段列出实际执行时的设备会话步骤。

`init` 使用现有 TOML 校验器，检查配置及本地素材存在、素材 SHA、每个 build unit 的 ISA/架构与板型、CPU 绑定。训练、调优、测试三类之间按同 SHA 的半开时间段检查交叠，主次测试都属于测试类。只新建草稿文件，原 job 和 run output 均保留。草稿列出须填写的板子身份、工具、源与构建环境、`profgen` 参数和种子。核对这些字段后设置 `draft=false`。包、输入与板型文件的 SHA 在 dry-run 及 run 时复核。

## Redo 归档

同一 run 的 mutating CLI 命令由收据目录内的 writer flock 串行化。若 cleanup journal 仍有待办，redo 返回 `recovery-required`。归档路径为 `receipts/redo/<UTC 时间戳>-<唯一后缀>/`，逐字节保存旧成功与失败收据。最后原子提交 `receipt.json`，含各阶段的 `invalidated` 状态、理由、原路径、归档文件名和 SHA；未提交完的目录不改变阶段状态。

下一次 run 先复核可复用前缀，按 DAG 从无有效收据的阶段生成新尝试。每份替代收据的 `redo` 字段绑定归档收据路径、SHA 与原因。归档和旧日志保留。恢复部署时，保留有效的预检脚本和上游变体，已失效尝试的主机部署清单原件留入独立历史目录。旧的 `history/` 失效记录仍可识别。

## 退出码

| 退出码 | 原因码 | 含义 |
| ---: | --- | --- |
| 0 | `success` | 命令成功。状态查询成功时仍可能显示失败的阶段。 |
| 1 | `error` | 未分类的程序、I/O 或数据错误。 |
| 2 | `gate` | 输入、收据或流程门禁不通过。 |
| 3 | `identity` | 板子、库、profile 或素材身份不匹配。 |
| 4 | `environment` | 资源、工具、构建或未细分的传输环境失败。 |
| 5 | `correctness` | 解码退出、EOS、帧或 oracle 验证失败。 |
| 6 | `board-unreachable` | 目标未在线，或 SDB 明确报告找不到设备、离线或连接被拒绝等。 |
| 7 | `recovery-required` | 清理待办仍存在，先按恢复流程处理。 |
| 8 | `lock-timeout` | 作业 writer lock、构建锁冲突或限时等待外部构建失败。 |
| 64 | `usage` | 命令用法错误。 |
| 130 | `user-abort` | 捕获的 SIGINT、SIGTERM 或用户中断。 |

[退出码实现](../../../workflow/afdo_wf/exits.py)统一归一化结果。已进入 mutating run 的失败记录包含 `reason`、`exit_code` 和错误文本。若失败后仍有清理待办，run 以 7 退出并在 `cause` 保存原始原因。参数校验和未取得 writer lock 的失败仅输出诊断。历史收据维持原字节，查询时把旧 `interrupted` 解释为 `user-abort`。操作系统直接强制终止进程时，由系统报告退出结果。

## 技能初稿

英文 [SKILL.md](../../../skills/afdo-workflow/SKILL.md) 位于指定目录。正文包括授权与主机共享构建锁、init 和 dry-run、新运行、状态与恢复、redo、报告解读。阶段详情交给 `explain`，实例引用已封存的 M1 和 M2a。技能无辅助脚本。已通过 skill-creator 的格式校验，实际运行演练留待 PM 审核后决定。

## 纯主机验收

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| workflow 测试 | 203 项通过，含 187 项既有测试和 16 项新增测试。原 dry-run 测试改验 stdout 及文件不变。 | [测试日志](evidence/workflow-tests.log) |
| M1 命令和收据回放 | 48/48，回放六个阶段。 | [回放记录](evidence/m1-replay-summary.json) |
| M1 attempt-11 只读演练 | S0–S7 已完成，直接输入和上游 SHA 全匹配，S8 清理待办为 0。计划与封存种子一致。 | [status](evidence/m1-status.json) · [dry-run](evidence/m1-dry-run.json) |
| M2a 只读演练 | S0–S7 已完成，直接输入和上游 SHA 全匹配，S8 清理待办为 0。计划采用封存 S6 的顺序与 bootstrap 种子，包括此次运行的种子覆盖。 | [status](evidence/m2a-status.json) · [dry-run](evidence/m2a-dry-run.json) |
| explain 与文件不变核对 | 每份封存运行的九个阶段均和计划的元数据一致。封存 job、配置、journal 和收据的 SHA、大小和 mtime 未改变。 | [验收索引](evidence/sealed-acceptance.json) · [explain 示例](evidence/explain-measure.json) |
| init 与功能级只读预览 | RPi5 配置和实际三份素材通过 SHA 检查，新草稿的九阶段计划打印到 stdout，run output 未创建。 | [init 结果](evidence/init-result.json) · [草稿预览](evidence/init-dry-run.json) |

本阶段停止等待 PM 审核。

## PM 审核修订 · SKILL.md 自足化

本轮只修订英文 [SKILL.md](../../../skills/afdo-workflow/SKILL.md) 与本说明。CLI 沿用已通过审核的版本。

| 审核项 | SKILL.md 位置 | 修订 |
| --- | --- | --- |
| 1. 适用范围 | 第 3 行 | frontmatter 说明 Tizen AutoFDO/PGO、FFmpeg、两种板型与实验用途。 |
| 2. 八阶段地图 | 第 24–37 行 | 每段的职责、板上接触及 `explain` 用法。 |
| 3. 授权边界 | 第 8–22、61–93 行 | 区分可直接执行的主机命令与须明确批准的 live run、resume、redo 和板子状态变更。 |
| 4. 共享构建锁 | 第 39–45 行 | 每次 GBS 持锁、持有者记录、让行规则、8 小时等待与 S0 三小时资源复查。 |
| 5. SDB 与身份 | 第 47–59 行 | 只重连目标，以型号、架构和镜像核验身份。 |
| 6. 退出码动作 | 第 95–109 行 | 每个退出码与处置步骤并列，技能可直接查阅。 |
| 7. 结果解读 | 第 111–126、153–154 行 | 四种判定、±1% 区间、可发布性、遥测标记与 M1/M2a 示例。 |
| 8. 封存路径 | 第 128–151 行 | M1 attempt-11、M2a 的实际 job 和报告相对路径。 |
| 9. 安全规则 | 第 8–22、77–83、105 行 | 封存只读、不在板上安装 RPM、verified-pull、清理与恢复前身份核验。 |
| 10. 篇幅与语言 | 全文 154 行 | 英文，阶段细节通过 `explain` 查看。 |

在独立 worktree 逐字执行了技能的 Setup 与 Sealed run examples 命令块。两份封存运行的 `status` 均显示 8 个业务阶段完成，直接输入与上游 SHA 匹配，清理待办为 0。两次 dry-run 的 9 条计划均可复用，`explain measure`、`explain report` 与计划元数据一致。两份读出的 report.md 均匹配其收据绑定的 SHA；M1 ToS 为 **−1.92% / faster**，M2a ToS 为 **+0.12% / equivalent**。前后核对的 31 份封存文件的 SHA、大小和修改时间一致。

workflow 全量测试 **203/203** 通过，M1 回放 **48/48** 通过。验收为纯主机，只读演练后停止。 [本轮验收摘要](evidence/skill-review-acceptance.json)
