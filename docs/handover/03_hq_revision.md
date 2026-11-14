# HQ 全面修订与发布检查（2026-11-14）

## 1. 结果与边界

hq 已推送：**498724fed8796da4190a458c01b95b9f65e334d5**，提交信息 Update llvm-profgen delivery documentation，父提交9a34528ff2bd9804a10b4c38b2b8fbc936a5cddd；未改写历史、未force。远端核验相同。[推送原文](evidence/03/hq-push.txt)、[远端核验](evidence/03/hq-remote.txt)。

本轮只改对外文档/示例、结果仓库检查器和状态。未构建LLVM/FFmpeg、未接板、未推Gerrit、未打开正式sample profile、未登记修正案3。仅用已有发布RPM与合成demo输入，不重跑质量矩阵、性能或历史真实输入。设计v1.8与既有证据不改；原temp/hq-release-20261114保持不动，在新temp/hq-revised-20261114检出上修改。只在新检出删除用户指定的中文副本和直拷workflow文档，Git历史保留。

长期规则第10–15条已写入STATUS；第8条澄清历史“待PM审阅”标签不进入对外文件。保护的三个本地配置未读、未add、未修改。

## 2. 自动门禁

入口：python3 tools/hq/check_hq.py TREE --json AUDIT，Python标准库。递归检查文件名/文本的CJK、全角字符、禁词和实际工作目录，其他非ASCII字符警告；检查URL允许域名、相对链接的目录边界/存在性、链接逃逸；非UTF8文件拒绝。不扫描.git管理目录。白名单精确匹配文件、行号、完整行、原因和代码。

本次：**0违规、0警告、19条相对链接有效，白名单空**。[推送前结果](evidence/03/prepush-check.json)。函数名main不匹配“main branch”，无需豁免。ASCII检查不等同自然语言识别，全部11个文本文件另做人工内容核对。

13个测试方法全通过，包含逐禁词subtest、AI词边界、CJK/全角、其他非ASCII警告、URL欺骗、相对/引用/HTML链接、symlink、工作目录、非UTF8、精确单行白名单等。[最终输出](evidence/03/checker-tests-final3.txt)。初次测试发现白名单JSON的line字段冲突，已改为line_number后重跑；[原失败输出](evidence/03/checker-tests.txt)保留。

旧文件扫描失败是预期；完整结果16MB留temp，[摘要与SHA](evidence/03/before-check-summary.json)。未将旧违规清单发布到hq。

两个脚本bash -n通过，15个Markdown Bash命令块只作语法检查，未执行板上命令；[逐块结果](evidence/03/markdown-shell-syntax.json)。git diff --check对示例.patch的标准空白上下文行提示空格，这是嵌入统一diff格式；除该patch外检查通过，patch本身应用检查通过；[原提示](evidence/03/git-diff-check.txt)。

## 3. 内容与取证

- 去掉当前HQ树中的中文设计原文和直拷workflow，改为英文概要；本仓库设计不改。
- README覆盖0–10节，保留Gerrit项目/基线/九补丁commit，去除内部仓库、分支、commit、路径、工具/模型名和流程状态。
- README/Introduction列出workflow→skill→Agent、M1–M5、内核独立路径和包维护者责任；除profgen外均Planned / Not implemented。
- 保留构建、C1/IP/lit替代验收和既有RPi4集成、LOST、avg核对数字，不扩大统计质量/性能结论。
- GBS模板与实际发布配置仅tmpdir/buildroot路径不同，无省略字段；[逐字段证据](evidence/03/configuration-equivalence.json)。
- FFmpeg示例基线：Gerrit platform/upstream/ffmpeg，5fe76358596f66e955f005094e6f34ca525ab23d。patch应用检查通过，实际应用字节相等；ARMv7/AArch64有/无profile消费共4项rpmspec语法检查退出0，无构建。[来源](evidence/03/ffmpeg-origin-chain.json)、[补丁检查](evidence/03/ffmpeg-patch-check.json)、[语法检查](evidence/03/spec-parse.json)。
- 板端信息只据既有probe/05、probe/09、kernel/03与06、impl/14；媒体据media/README.md和evidence/11/09_media.json；交付据delivery/01_release.md与impl/12。未读取新板况，未把本地PMUv3提交伪称已合入Gerrit。

## 4. 实际执行和未验证事项

| README节 | 本轮执行 | 限制 |
|---|---|---|
| 0 | 复用既有独立sandbox检出，核对HEAD/九提交/spec；用已有RPM提取与demo | 不重复网络克隆、不重新构建LLVM |
| 4 | 配置逐字段比较 | 新主机的简化命令Not verified；先前正常构建79分40秒证据保留 |
| 5 | 新目录解出llvm/libllvm；SHA/version/help通过 | 不安装RPM |
| 6 | AArch64、Thumb转换和profdata show、JSON断言通过 | 本轮不跑lit或构建测试树 |
| 7 | 有证据的命令/版本写入文档 | 不接板，不执行sdb或任何板上命令 |
| 8 | patch应用、spec语法 | 不构建FFmpeg、不消费profile、不计时、不重新下载/转码 |

[源码核验](evidence/03/source-verification.json)、[提取输出](evidence/03/extraction-output.log)、[demo输出](evidence/03/demo-output.log)。工具SHA仍为67ad21faba787d276a80673c1f324f7c0591d28d76bd37a8bd57de0d86426be6。两demo均conversion=ok、identity=unverified、sampling_adequacy=unknown，target=usable=written_positions=1。README第9节摘录实值，docs/04_demo.md保留完整verdict/samples；原对象[ARM64](evidence/03/a64-pie-expected-objects.json)、[Thumb](evidence/03/thumb-count-expected-objects.json)。

Not documented yet：GBS安装/账号开通、镜像刷写、当前散热、PMUv3已合入的准确Gerrit分支/commit、能复现历史FFmpeg依赖的当前目标配置。
Not verified：新主机简化GBS命令、独立lit构建步骤、新FFmpeg示例完整构建及消费/性能、BOLT共享库重写、workflow自动化。没有用旧变体构建冒充新示例验收。

## 5. 文件清单

共11文件，**63,722字节**，不含.git。[逐文件SHA](evidence/03/hq-files.json)。

| 路径 | 字节 |
|---|---:|
| README.md | 25780 |
| demo/extract_tool.sh | 1063 |
| demo/run_host_demo.sh | 2011 |
| docs/01_introduction.md | 2889 |
| docs/02_design/llvm_profgen_ip_mode_design_summary.md | 6829 |
| docs/02_design/workflow_design_overview.md | 7021 |
| docs/03_reports/llvm_profgen_delivery.md | 6591 |
| docs/04_demo.md | 6727 |
| examples/ffmpeg/README.md | 2962 |
| examples/ffmpeg/profiling.patch | 1316 |
| examples/gbs/llvm-release.conf.in | 533 |

## 6. 资源与边界

所有命令串行，nice19/ionice-c3，systemd用户scope 3G/100%（不超过3G/200%），启动前MemAvailable≥4GiB。提取/demo/验证记录的cgroup峰值**175,828,992 B**；采样最低MemAvailable **23,387,074,560 B**，无OOM、暂停或资源终止。[摘要](evidence/03/summary.json)。不足一分钟的任务保留启动原文及最终峰值；监测器按60秒采样，不将稀疏采样称为全时最低值。

工作目录之外仅读取用户指定任务附件；未发现本轮生成工作目录外的项目文件。未删除既有temp目录。大扫描/解包/原始demo保留temp/hq-revision-20261114-work并登记SHA。新证据每个小于1MB。

hq提交/远端已核验；本报告、检查器和STATUS同一提交推送。完成后停止。
