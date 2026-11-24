# M5 · release 分支与新机器验收

`release` 是供新机器克隆的独立分支，初始树以 `d04eba6a8dfce0de2a04694fdf5667b3f2e09479` 的 workflow 为基础。首次推送的提交为 `c9462eaf5ca65d349a6afee1a1dacbe693caa666`，树为 `a949898ded713a98e98dabcb72ef4c27d173058c`。创建分支和验收只用 Git。本次未创建 tag 或 GitHub Release，`hq` 保持原 tip。

## 内容及逐文件检查

| 路径 | 文件数 | 内容 |
| --- | ---: | --- |
| `README.md` | 1 | 英文用途、从克隆开始的步骤、前提、示例和测试 |
| `skills/afdo-workflow/` | 1 | 与 main 逐字节相同的 SKILL.md |
| `workflow/afdo_wf/` | 22 | CLI、工作流、构建、收据、统计及传输 |
| `workflow/board/` | 13 | 板上采集、进程观察、校验与清理脚本 |
| `workflow/packages/` | 7 | 两板 FFmpeg 配置、输入清单、补丁及负载脚本 |
| `workflow/platforms/` | 2 | RPi4 armv7l 与 RPi5 aarch64 |
| `workflow/tests/` | 36 | 单元测试、合成与轻量文本夹具、可选档案回放 |
| `workflow/README.md`、`workflow/.gitignore` | 2 | 工作流说明、主机 profile 工具构建说明及忽略规则 |
| `examples/` | 4 | M1 attempt-11 与 M2a 各一份 Markdown 和 JSON 报告 |

88 个跟踪文件共 853,412 字节，最大文件 166,529 字节。逐文件检查路径、ASCII 英文、私有标识与主机路径，检查相对链接和锚点 12 处，均通过。标准 RPM chroot 的 `/home/abuild/rpmbuild/` 与 `example.invalid` 合成数据仍用于测试。FFmpeg 补丁中的空白上下文行与遥测双换行夹具原样保留。分支无原始运行目录、媒体、冻结仓库或二进制。整理树和远端克隆的逐文件 SHA-256 与 Git 树一致。[逐文件清单](evidence/release-branch-files.json)

两份示例报告为只读副本。复制时省略原主机路径和内部证据引用，保持 JSON 的估计值、区间、判定、质量信息和板型身份。M1 Markdown 增加由 JSON 生成的两组结果摘要，M2a Markdown 保留原结果表。原报告在复制后复核 SHA 一致。[原件与验收索引](evidence/release-branch-acceptance.json)

## 新机器演练

[同步技能](../../../skills/afdo-workflow/SKILL.md)共 177 行，SHA-256 为 `d9d558c9a2a74ceb6a2beb7d71a9ec2d841d4307befd0af81f1aa4626f2aa25d`。从 release 的新克隆使用，克隆根为 WORKDIR。技能增补主机与板上前提、三段媒体的来源和 SHA、第九阶段 `restore`，并给出缺失媒体的退出码和报错。示例链接在 release 树内可直接打开；`status` 和 resume 需要保存原作业和收据的主机。

- 从远端全新克隆到 `temp/release-check-2026-11-24/`，仅克隆 release。设置与演练使用克隆内的配置、示例和独立临时目录。
- 九个阶段的 `explain` 均成功。合成草稿的 dry-run 与阶段表的九个条目顺序一致。
- 按技能读取两份 Markdown 和对应 JSON。ToS 的历史判定仍为 M1 `faster`（约 -1.92%）和 M2a `equivalent`（约 +0.12%）。
- 按技能用缺失媒体执行 RPi5 `init`，退出 2，输出 `required local file missing` 和 `bbb_720p_h264_60s.mp4` 的路径。草稿和运行目录均未创建。
- 克隆内执行 216 项测试，213 通过、0 失败、3 项因缺少原始档案显式跳过，耗时 39.418 秒。跳过项是 attempt-05 的 maps、attempt-06 的 maps 与部署收据、attempt-07 的编译取证。release README 写明可选档案路径的传入方式，其余测试使用克隆内夹具和合成输入。[验收结果与原始日志 SHA](evidence/release-branch-acceptance.json)

演练在原主机的全新克隆中执行。未接板、未启动 GBS，封存运行保持原样。
