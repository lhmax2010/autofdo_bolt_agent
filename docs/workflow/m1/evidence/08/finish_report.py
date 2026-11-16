from pathlib import Path
from collections import Counter
import json,datetime,hashlib
D=Path(__file__).parent;E=Path('docs/workflow/m1/evidence/08');M=D/'measurement'
assert json.loads((M/'result.json').read_text())['success']
assert json.loads((D/'cleanup/result.json').read_text())['success']
s=json.loads((M/'statistics.json').read_text());g=json.loads((D/'build/gates.json').read_text());c=json.loads((D/'cleanup/result.json').read_text());plan=json.loads((M/'plan.json').read_text())
pct=lambda x:f'{100*x:+.3f}%'
text=(D/'report_static.md').read_text()
text+='| 目标 | RUN | 目标样本 | 可用 | DWARF 函数内无可写行 | DWARF 函数外（含汇编/PLT） |\n|---|---:|---:|---:|---:|---:|\n'
for x in json.loads((D/'conversion/compact-summary.json').read_text()):
 dso,run=x['file'].split('-run');text+=f"| {dso} | {run.split('.')[0]} | {x['target']} | {x['usable']} | {x['no_line']} | {x['outside']} |\n"
text+='\n上述后三列构成目标样本的互斥分解；PLT、no_cu、in_cu_no_subprogram 是函数外项的细分，不能重复相加。全部质量报告随证据保留；未映射目标样本为 0。\n\n'
text+='代码来源以独立 llvm-symbolizer 22.1.8 查询实际目标地址，按 PT_LOAD 换算并处理 Thumb 位。用函数定义源路径识别 C/头文件函数，用 `.S/.s/.asm` 行表见证识别汇编，其余保守列为其他函数外；不凭函数名猜测汇编。汇总为：\n\n| 目标 | 总目标样本 | DWARF C/头文件函数 | 汇编源行见证 | 其他函数外 |\n|---|---:|---:|---:|---:|\n'
shares=json.loads((D/'code-shares/summary.json').read_text())
for dso in ['libavcodec','libavutil']:
 a=[x for x in shares if x['dso']==dso];total=sum(x['total'] for x in a);cnt=Counter()
 for x in a:cnt.update(x['categories'])
 text+=f"| {dso} | {total} | {cnt['dwarf_c_cpp_function']} ({cnt['dwarf_c_cpp_function']/total:.3%}) | {cnt['assembly_source_witness']} ({cnt['assembly_source_witness']/total:.3%}) | {cnt['other_or_outside_dwarf_function']} ({cnt['other_or_outside_dwarf_function']/total:.3%}) |\n"
text+='\n汇编见证主要在 DWARF 函数外，所以上表的汇编列与上一表“函数外”有包含关系；不是把行表存在当作可写 profile。DWARF 函数内也有无可写行的损失。libavutil 三轮合计仅 325 个目标样本，这一稀疏性如实保留。详细地址分类、查询参数与工具 SHA 见 `evidence/08/code-shares/`。\n\n'
text+='''### 8.4 离线构建、构建锁与消费证据

把 BASE 实际下载的 108 个 RPM 逐份 SHA 校验后复制为本次冻结仓库，用 createrepo_c 建索引。初次 file:// 入口及随后仅增加 buildconf 的入口均在 GBS 仓库解析阶段失败（寻找 builddata/build.xml），没有编译；保留两次失败记录。最终使用 `--skip-conf-repos -R <本地目录> -D <原归档buildconf>`，没有切换 snapshot 或依赖版本。GBS 配置的路径/入口 SHA 与原在线配置不同，源代码、spec、宏、解析后 buildconf 与包集合按门禁核对；不把两个不同配置文件说成字节相同。

四次完整构建（主构建 BASE-r/AFDO，独立取证 BASE-r/AFDO）均使用新 root、串行 `--threads 1 --define '_smp_mflags -j2'`，MemoryMax=6G、MemoryHigh=5G、CPUQuota=200%、nice19、ionice-c3。启动门禁为 MemAvailable≥16 GiB、load1<0.6×nproc、磁盘≥50 GiB；等待上限本轮取 600 秒。运行中每60秒检查低内存与磁盘，仅允许停止本任务单元。资源采样、全部命令和退出码在 build 证据中；没有修改其他构建。主构建另有 cgroup 采样；取证构建未单独保存结束瞬间的 memory.peak，不将主构建峰值冒充全轮峰值。

四次完整构建各有8条既有debugedit DWARF5诊断，均非致命；原文单列保存，不宣称debugsource路径改写完整。

补丁 SHA `0c94e54d252ad1ecbc625f629af090b257edba4cd3753d76352fd031486243b6`、spec SHA `0e611e7eb95ada2c024dbea379821c5b109383f1545bcb0c86ef85f238740c27` 均保持不变。profile 仅作为 Source2000 放入 packaging/autofdo.extbinary；没有加入覆盖诊断选项。

'''
text+='| 构建 | 秒数 | GBS 退出码 |\n|---|---:|---:|\n'
for prefix in ['', 'forensic/']:
 for v in ['base-r','afdo']:
  r=json.loads((D/'build'/prefix/v/'result.json').read_text());text+=f"| {prefix+v} | {r['seconds']:.3f} | {r['exit']} |\n"
text+='''
构建锁全部通过：

- 原 BASE、BASE-r、AFDO，以及两次取证 root 的 108 条 `rpm -qa`（含 SHA256HEADER）排序后逐行相同。
- 独立取证只通过 `--define '__make /usr/bin/make V=1'` 打开命令打印，未放入 `_smp_mflags`。两侧各 698 条实际编译/链接命令，去掉 profile-use 参数后按命令多重集合比较，差异 0（并行打印顺序不是语义）。完整 argv、原始 build.log 与差异清单保存。
- 每侧取证产物与主构建的六个运行库、目标库调试文件 SHA/build-id 相同。因此用取证命令补足主构建简略 CC/AS 日志的证据，并没有把取证产物换入 A/B。
- BASE-r 的全部六个运行库 SHA 与原 BASE 相同；两个目标的 build-id 也相同，最终对照仍为 BASE。4,866 份 C/头文件/汇编源文件（含生成文件）在 BASE-r/AFDO 中逐字节相同。
- AFDO 取证日志有 627 条命令带 profile-use；chroot 内 profile SHA 等于锁定值。两个目标库 `.text` SHA 均改变，runtime/debug build-id 成对一致且不同于 BASE。默认输出中 profile 相关编译警告为 0；这不是消费证据，消费证据是前述 flag、profile SHA 和代码变化。

| 目标 | BASE = BASE-r build-id | AFDO build-id |
|---|---|---|
| libavcodec | `805376f248504d2084e3e95470810873ffc3655a` | `5aef89343bc6a870b6760c3d492206bbb8adc286` |
| libavutil | `bb5b41f743b9b07bb38cc5007f7deb6516256579` | `1908c55105184d14beeb1e7076816dd1c994658c` |

[门禁结果](evidence/08/build/gates.json)、[生成源比较](evidence/08/build/generated-source-comparison.json)、[主构建消费记录](evidence/08/build/afdo/consumption.json)。

### 8.5 测量计划、原始轮次与最终正确性

'''
text+=f"计划在 **{plan['time']}** 写入并 fsync，测量计划 SHA 为 `{json.loads((M/'plan-receipt.json').read_text())['sha256']}`。2 个预热 block（每个 BASE/AFDO 各一次），正式 N=15；顺序种子 20261116，bootstrap 种子 2026111601，20,000 次、ε=1%。A=BASE，B=AFDO：\n\n`{' '.join(plan['order'])}`\n\n"
text+='''每轮固定 CPU3、相同 I420 caps、ToS60、fakesink sync=false；perf stat 记录 task-clock/cycles/instructions，墙钟为 Bash time 包裹 perf stat 的秒数（三位小数）。CPU0 采样器记录单调时间、两种频率、温度与欠压。固定冷却5秒，再按≤60°C启动门禁等待；轮内温度<80°C、所有频率读数=1500000 kHz、欠压0、含起止端点的间隔≤2秒。计时轮没有输出 hash；库文件 SHA 在计时结束后核验。所有解码进程 maps 均验证目标库来自本变体。

板上无 timeout 命令，使用现有 Bash 的独立进程组 watchdog，仅终止本任务子进程组，先通过1秒超时负例。第一次 AFDO oracle 启动又遇到旧 Bash 不支持 `${variant,,}`，在解码开始前失败；改为显式分支后重做。两项设置失败均保留，且各次退出都恢复 root/governor，不算正式 block 重采。

'''
rounds=json.loads((M/'rounds.json').read_text());blocks=json.loads((M/'blocks.json').read_text());text+='| block | 顺序 | BASE 秒 | AFDO 秒 | 标记 | 使用 attempt |\n|---|---|---:|---:|---|---:|\n'
for b in blocks:
 r=[x for x in rounds if not x['warmup'] and x['block']==b['block'] and x['attempt']==b['selected_attempt']];a=next(x for x in r if x['variant']=='base');z=next(x for x in r if x['variant']=='afdo');flags=sorted(set(a['flags']+z['flags']));text+=f"| {b['block']} | {plan['order'][b['block']-1]} | {a['wall_seconds']:.3f} | {z['wall_seconds']:.3f} | {', '.join(flags) or '无'} | {b['selected_attempt']} |\n"
checks=[json.loads(p.read_text()) for p in M.glob('post-*-oracle.json')];assert len(checks)==6 and all(x['match'] for x in checks)
text+=f"\n正式 block 完整 {len(blocks)}/15；标记 {len(s['flagged_blocks'])}，缺失 {len(s['missing_blocks'])}，技术故障记录 {len(list(M.glob('*-failure.json')))}。计时前 AFDO 两片与 PLAT oracle 一致；计时后 PLAT/BASE/AFDO × BBB/ToS 六次复核全部一致，仍是每片1,800帧、2,488,320,000字节及8.2的SHA。caps 审计及 maps 原文随证据保存。\n\n"
text+='[计划](evidence/08/measurement/plan.json)、[全部轮次](evidence/08/measurement/rounds.json)、[block选择记录](evidence/08/measurement/blocks.json)。每轮目录包含 perf stat、墙钟、caps/EOS、maps、遥测和启动温度检查原文；本轮未独立测量遥测采样器开销，两变体使用同一观察方式。\n\n### 8.6 统计与判定\n\n'
a=s['primary'];text+=f"Python 标准库，按 block 配对 `r_i=ln(T_AFDO/T_BASE)`，主估计 `exp(mean(r))-1`。标记轮次仍在主分析；干净 block 单独做敏感性分析。\n\n- **主判定：{a['verdict']}**。主估计 **{pct(a['estimate'])}**。\n- block bootstrap 95% CI：**[{pct(a['bootstrap_CI95'][0])}, {pct(a['bootstrap_CI95'][1])}]**。\n- t 区间（次要）：[{pct(a['t_CI95'][0])}, {pct(a['t_CI95'][1])}]；中位数之比−1：{pct(a['median_ratio_minus_one'])}。\n- BASE CV：{s['baseline_CV']:.4%}，供以后估计 N，本轮没有据此增减轮数。\n- cycles/task-clock 中位有效频率：BASE {s['effective_frequency_MHz']['base']:.3f} MHz，AFDO {s['effective_frequency_MHz']['afdo']:.3f} MHz；相对差 {100*s['effective_frequency_relative_difference']:+.6f}%；{'标记混杂风险' if s['confounding_risk'] else '未超过0.5%混杂风险阈值'}。\n"
cs=s['clean_sensitivity'];text+=f"- 干净 block：n={cs['n']}，判定 {cs['verdict']}，估计 {pct(cs['estimate'])}，bootstrap CI [{pct(cs['bootstrap_CI95'][0])}, {pct(cs['bootstrap_CI95'][1])}]。\n\n"
text+='[统计原文](evidence/08/measurement/statistics.json)。第11、14个block均为AFDO轮的采样器终止半行，原脚本记telemetry_unknown；完整读数未观察到频率/温度/欠压异常，不将截断读数当作正常。两组保留在主分析，敏感性分析不替代主判定。统计脚本 SHA 在计时前锁定；等价、快、慢、超额标记、缺失的合成夹具均通过。没有观察中途效果来补采、改顺序或改 N。\n\n### 8.7 恢复、证据与限制\n\n'
text+=f"最终 uid={c['final_uid']}，governor 为 `{c['final_governors']}`，RPM计数 {c['rpm_count']}；cleanup_pending={c['cleanup_pending']}。本轮 work 目录先打包拉回、校验 SHA、持久化收据，再复核远端清单并删除。保留 `/opt/afdo_agent/variants/m1p-base/` 与 `/opt/afdo_agent/variants/m1p-afdo/`，其真实文件 SHA 清单位于[清理结果](evidence/08/cleanup/result.json)。没有清理任何其他任务目录。\n\n"
text+='''完整阶段脚本、实际 argv、构建日志、样本与质量报告、原始测量/遥测、oracle、收据和文件 SHA 见 [证据索引](evidence/08/index.json) 与 [校验清单](evidence/08/sha256.json)。大文本使用 .gz 保存原字节。主机工作目录为 `temp/m1-pilot-v02-20261116/`；RPM、buildroot、原始 perf.data 与最终板上 work 归档保留在其中，没有提交 LLVM 源码或二进制构建树。

记录限制：早期公共日志复用了 operations.json，导致第一阶段部分逐条 SDB stdout 被覆盖；保留原阶段脚本、独立 identity/evlist/状态/部署清单，并在采集前重新逐项验证工具、视频与所有 BASE 文件 SHA。此处不声称早期每条 stdout 都保留。取证构建的结束瞬间 cgroup peak 未记录。SDB 使用已有服务，未观察到本轮启动新服务；没有为核查其内部状态而访问项目外的源码/配置或清理外部文件。

本结果只覆盖这两个输入与这块板上的 FFmpeg Thumb pilot，不能外推为完整解码器正确性或普遍性能收益。训练和测试是不同视频/SHA；ToS 在之前 profgen 工作中使用过，不称为全新未接触 holdout。profgen explicit conservative strategy; defaults not statistically validated。本轮没有质量矩阵或 M1/M2 等质量指标计算，也没有登记预注册修订3。

### 8.8 Q.5 第17项与提交范围

所有本轮生成/读取的六份单 RUN profile、两份 DSO 合并 profile、锁定 package profile，以及文本检查、编译器消费的对象/时间/用途，见[接触登记](evidence/08/conversion/Q5-17-profile-access.json)。编译器消费时间范围用 command/result 文件时间及资源日志界定；目的为本次 workflow 消费、冲突与构建锁验证，未来质量评估必须披露此接触。

本轮只提交 main 的本报告、STATUS 与 evidence/08；不修改设计、hq、Gerrit或他人评审文件。最终 commit 与推送核验在执行汇报中给出。
'''
report=Path('docs/workflow/m1/02_manual_pilot_rpi4_thumb.md');assert '## 8. 按 v0.2' not in report.read_text();report.write_text(report.read_text().rstrip()+'\n\n'+text)
status=Path('docs/STATUS.md');old=status.read_text();marker='## RPi4 环境恢复通过';i=old.index(marker)
entry=f"""## M1 RPi4 Thumb AutoFDO 端到端试跑完成（2026-11-16）

- [试跑报告第8节](workflow/m1/02_manual_pilot_rpi4_thumb.md)：3次BBB训练、6次转换均conversion=ok/identity=verified；锁定profile SHA `61f03b59262e3ce7ce758219d65848a33b5a0549131c362a6769ad10386f2cf2`，显式max/none/none/none。采样充分性unknown，默认值未统计验证。
- 原BASE、BASE-r、AFDO的108条包/SHA256HEADER相同；独立V=1取证各698条命令去掉profile参数后相同，取证产物与主构建一致。BASE-r与BASE相同，仍用BASE作对照；AFDO两目标代码/build-id不同，runtime/debug匹配，消费profile SHA一致。
- PLAT/BASE/AFDO在两片上的前后正确性全部通过。固定15个AB/BA block，标记{len(s['flagged_blocks'])}、缺失{len(s['missing_blocks'])}；主判定 **{a['verdict']}**，耗时变化 **{pct(a['estimate'])}**，bootstrap 95% CI **[{pct(a['bootstrap_CI95'][0])}, {pct(a['bootstrap_CI95'][1])}]**。有效频率差{100*s['effective_frequency_relative_difference']:+.6f}%，{'有' if s['confounding_risk'] else '无'}>0.5%混杂标记。仅对本pilot解释，不外推默认值或普遍收益。
- root恢复uid5001、policy0=schedutil，cleanup_pending为空；本轮work已校验拉回后删除，BASE/AFDO variants保留。Q.5#17对象/时间/用途及原始测量、遥测、命令、配置失败与执行器更正均归档evidence/08。早期SDB日志覆盖和取证峰值缺口已披露，关键SHA重核通过。未操作RPi5、hq、Gerrit，未改patch/spec。

"""
status.write_text(old[:i]+entry+old[i:]);print('report and STATUS updated')
