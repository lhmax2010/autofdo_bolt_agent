# M5 收尾 · 冷启动复验

两份异机只读测试完成。原结果可以检查与解释，缺失媒体时 `init` 按预期停止。本轮修订从独立 worktree 提交，验证只涉及主机。

## 修订和证据

| 项目 | 位置 | 核对 |
| --- | --- | --- |
| Python 版本 | [入口](../../../workflow/afdo_wf/__main__.py)、[技能设置](../../../skills/afdo-workflow/SKILL.md#setup-and-authorization) | CLI 在加载需要 Python 3.11 的模块前检查版本。模拟 3.10.9，退出 4 且未导入 CLI 或 tomllib。本机只有 Python 3.12.3。技能通过 `PY` 选择已存在的解释器，测试了回退到 3.12 和无合格解释器时退出 4。 |
| 媒体获取 | [技能输入段](../../../skills/afdo-workflow/SKILL.md#where-the-inputs-live)、[媒体清单](evidence/cold-start-media.json) | `media` 为孤立分支。三个原文件按 95,000,000 字节上限核对，从远端回读，逐个匹配 inputs.toml。 |
| 草稿与字段 | release 的 `examples/ffmpeg-rpi5-draft/`、[技能字段表](../../../skills/afdo-workflow/SKILL.md#fill-in-the-draft) | 用真实三片生成 job 和九阶段 dry-run。示例用变量占位替换主机路径。字段表覆盖 RPi4 和 RPi5 草稿的全部 `missing_for_run` 项，并给出审查清单。 |
| 只读诊断 | [doctor 实现](../../../workflow/afdo_wf/doctor.py)、[测试](../../../workflow/tests/test_doctor.py) | 列出 Python、Git、SDB、GBS 版本和资源读数，提供 job 时验证本地主机及板侧工具副本的 SHA。仅运行版本查询和本地读取。缺失、指纹不匹配、无法检查均有对应分类；退出 0 表示诊断完成。 |
| 已验证环境与 LLVM 来源 | [技能版本表](../../../skills/afdo-workflow/SKILL.md#verified-run-environments) | 记录工具版本、板镜像、Gerrit sandbox 与交付工具 SHA。M1 的 SDB 客户端版本未找到当轮取证，表中明示。M2a 的记录为 4.2.25，本轮主机的只读诊断读到 4.2.36。 |
| 工作流入口 | `.clinerules/workflows/afdo-workflow.md` | 单段链接到技能。采用 Cline 官方说明的 workspace Markdown 工作流路径。ClineSR 部署能否识别仍待在该服务器核验。[官方路径说明](https://cline.bot/blog/stop-adding-rules-when-you-need-workflows) |

版本取证来自 [M1 验收](../m1/05_m1_board_e2e.md)、[M1 主机版本](../m1/evidence/09/validation.json)、[M2a 准备](../m2a/01_rpi5_preparation.md)、[M2a 的 SDB 客户端记录](../m2a/evidence/m2a-resume-20261123/sdb-client-version.txt)、[RPi5 perf 验证](../../probe/evidence/16_rpi5_perf_deployment.txt) 与 [LLVM 交付](../../profgen/delivery/01_release.md)。

## media 回读

远端 tip `16c572a6d31cdab2a14548005941a270de480307`。除下表四项外，分支无其他跟踪文件。Sintel 的大文件警告出现，push 退出 0。[推送警告原文](evidence/cold-start-media-push-warnings.txt)

| 文件 | 字节 | SHA-256 |
| --- | ---: | --- |
| `bbb_720p_h264_60s.mp4` | 30,023,879 | `b5e116b9d01cec8e7f697041c53575d36bd96a5928e40faa69e731f9ae2d00a4` |
| `tos_720p_h264_60s.mp4` | 29,964,461 | `280fbd41f8772491ebe784aa19a3caed3bb1e8b2e64daef1d2a5a284d1f38ad1` |
| `sintel_1080p_h264_60s.mp4` | 60,471,233 | `b1c762e322350cecb04a38509050d320892ff8cbc8b2a7113418d5ecba4ad843` |
| `ATTRIBUTION.md` | 1,296 | `7615aa6190a594e63c6daba4b076ca060537342e05081facb5bdace96d93cb5c` |

## 全新克隆验收

从远端到新目录获取 release `afa3e8eed5e98454c8966b89bb3f86255503cba6`。按技能在旁边克隆 media，执行 `doctor`、`init`、`run --dry-run`，三个命令均退出 0。九个阶段均执行了 `explain` 核对，draft 的字段和值与示例对应，实验名由文件名生成。两份 dry-run 在替换主机路径后相同。草稿缺少工具锁时，`doctor --job` 报告 unknown。

实际诊断时内存为 16,224,133,120 字节（低于 16 GiB），load1 为 15.0825（上限 12），磁盘剩余 297,195,872,256 字节。两条资源门禁按原条件报告 mismatch。诊断和起草仍完成，且未生成运行目录或接触设备。冷启动只使用新克隆和旁边的媒体克隆，没有读原工作区的 temp 运行数据。[验收索引](evidence/cold-start-acceptance.json)

release 的 94 个文件合计 886,373 字节，逐文件内容检查及 19 个相对链接检查通过，远端回读 tree 和文件 SHA 均匹配。入口路径按本轮要求加入，入口文件正文只有技能链接。GitHub 仓库 URL、内部主机路径、会话信息和内部发布分支引用均未进入 release。[逐文件检查](evidence/cold-start-release-files.json)

全新克隆运行 223 项测试，220 通过、0 失败、3 项缺少原始档案按预期跳过，耗时 188.829 秒。三项分别依赖 attempt-05 maps、attempt-06 maps 与部署收据、attempt-07 编译取证，随后在独立工作树对原档案复验 3/3 通过。M1 封存回放 48/48 通过。未修改封存运行，未接板或启动 GBS。

## M5 验收后文字修正

用户确认 ClineSR 第二轮冷启动通过检查、解释、doctor、init 与 dry-run，M5 验收完成。本文修订说明与两份工具锁示例随验收入库。

| 反馈 | 修改位置 |
| --- | --- |
| 版本与偏离记录 | 技能 `Verified run environments` 说明其他版本可用但未经验证，实际运行优先采用已验证组合，偏离记录在实验中。doctor 报告检测到的版本，版本表由操作者核对。 |
| SDB 批准 | 技能 `Setup and authorization` 与 `Board identity and SDB` 明确所有通过 SDB 接触板子的操作均须事前批准，包含只读探测。 |
| 工具锁 | 技能 `Record and verify tool locks` 给出对准备好的工具链文件执行的 realpath 与 sha256sum 命令。M1 与 M2a 的封存作业各提供四个主机锁和两个板侧工具锁。示例只导出文件名、SHA 和需要的板侧目标路径。 |
| 媒体署名 | 技能 `Where the inputs live` 指出 media 检出中的 ATTRIBUTION.md。 |
| 草稿门禁 | 技能说明无 job 的 doctor 全部 ok 只覆盖主机，设置 draft=false 前必须执行并通过带 job 的检查。 |
| 工作流入口 | ClineSR 上的 `.clinerules/workflows/afdo-workflow.md` 可能不会自动注册。技能与 release README 给出直接打开 SKILL.md 的入口。 |

两份样例的 12 个锁对实际文件重新计算 SHA-256，均与封存作业一致。封存作业文件保持原字节。技能的 12 个 Bash 代码块通过语法检查，记录工具锁的命令用已封存 profgen 实测通过。修改范围仅为文档和示例数据。

在 release 独立 worktree 运行全量测试，223/223 通过（含三项档案复验），耗时 1353.590 秒。逐文件检查覆盖 96 个文件和 21 处相对链接。两分支的 SKILL.md 与两份示例字节一致。
