# RPi4 当前镜像软件采样实测

日期：2026-10-28（Asia/Shanghai）。板型 Raspberry Pi 4 Model B Rev 1.5，armv7l，root（id -u=0）。运行内核仍为 `6.12.80-arm-rpi4-v7l`，`#1 SMP Thu Oct 22 06:42:32 UTC 2026`。没有替换内核、安装/卸载 RPM、挂载/remount、重启或改动 /boot。

**结论：软件采样和程序级 DSO 归属支持；当前镜像硬件 cycles 不支持。** 指定 cycles 的 record 返回 0，但数据实际是 perf 回退后的 cpu-clock，不能把成功退出或样本存在当作硬件能力证明。strip 库只能有限解析符号，且多数已解析样本属于 PLT 入口。

全部命令、真实远端退出码、stderr 与必要输出见 [14_rpi4_sampling.txt](evidence/14_rpi4_sampling.txt)，以下按该文件的 `=== 项目名 ===` 定位。完整原始 JSON（含 wrapper 和分离的 stdout/stderr）保存在 WORKDIR/temp/sampling-current/；没有把 perf.data 拉回本机。SDB 的传输退出码另列，判定使用紧接板上命令取得的 `$?`，不以 SDB 返回 0 代替远端成功。建立工作目录前和最终清理后的查询采用 SDB 合并输出，并如实标记 combined。

## 1. 部署目录与可执行性

| 检查/命令 | 关键输出、真实退出码 | 结论/证据项 |
|---|---|---|
| cat /proc/device-tree/model；id -u | Raspberry Pi 4 Model B Rev 1.5；0；均 exit 0 | 板型/root 符合；model、id |
| rm -rf /tmp/afdo_probe && test ! -e /tmp/afdo_probe | exit 0 | 上轮安装脚本目录已删除；cleanup_install |
| findmnt -T /opt -n -o TARGET,SOURCE,FSTYPE,OPTIONS | /opt /dev/mmcblk0p3 ext4 rw,relatime；exit 0 | 可写且没有 noexec；opt_mount |
| df -h /opt /tmp | /opt 1.3G、可用 1.2G；/tmp 1.9G；exit 0 | 空间记录；space |
| /usr/bin/true 复制到 /opt/afdo_agent/work/ 后执行 | exit 0 | 执行正对照通过；exec_opt |
| /usr/bin/true 复制到 /tmp/afdo_true_noexec_control 后执行 | exit 126，Permission denied | /tmp noexec 负对照符合；exec_tmp |
| 删除两个 true 拷贝并验证 | exit 0 | true_cleanup；最终 final_tmp_clean 也通过 |

实际 `/opt` 是独立的 `/dev/mmcblk0p3` ext4 挂载点，不是根分区；仍使用用户明确授权的固定目录 `/opt/afdo_agent/`，未自行换目录。初始目录不存在（ls exit 2），随后建立 tools、lib、work。两个执行对照拷贝在测试后立即删除；/tmp 的短暂写入是用户明确要求的负对照例外。

本轮全部 perf 命令使用以下环境和前缀（原始证据逐项列出参数；此处为已执行记录，work 已清空）：

```sh
export LD_LIBRARY_PATH=/opt/afdo_agent/lib
export HOME=/opt/afdo_agent/work/home
export TMPDIR=/opt/afdo_agent/work/tmp
export PERF_CONFIG=/opt/afdo_agent/work/perfconfig
export GST_REGISTRY=/opt/afdo_agent/work/registry.bin
export XDG_CACHE_HOME=/opt/afdo_agent/work/cache
# 下文 P 代表此完整命令前缀：
nice -n 19 ionice -c3 /opt/afdo_agent/tools/perf --buildid-dir /opt/afdo_agent/work/buildid
```

PERF_CONFIG 指向 work 下新建的空文件，HOME/TMPDIR/cache/buildid 均为 work 下目录。媒体、registry、查询临时输出和采样数据均落在 work 内。

## 2. 工具校验与依赖验收

使用 [02_rpi4_pmu_probe.md](02_rpi4_pmu_probe.md) 已校验的解包文件。主机在推送前 sha256sum、SDB push、板上 sha256sum 均退出 0，哈希一致（证据 local_sha / push / remote_sha 项）。只部署 perf 主程序和 libLLVM，不安装 RPM、不推送 perl。

`LD_DEBUG=libs P --version` 退出 0，输出 `perf version 6.12.80`。解析记录包含 libLLVM 的 `calling init: /opt/afdo_agent/lib/libLLVM.so.22.1`，并成功 `transferring control: /opt/afdo_agent/tools/perf`；补充 ldd 退出 0，全部 NEEDED 都解析为真实路径，无 not found。libLLVM 的 libxml2.so.16 等依赖使用板上现有 /lib 文件。本轮所用 record/report/evlist 子命令没有出现缺 perl 错误。完整库映射及 LD_DEBUG 必要摘录见 dependencies、ldd。

## 3. 事件实测与能力

| 命令（P 为上述完整前缀） | 退出码、关键输出 | 判定/证据项 |
|---|---|---|
| P --version | 0；perf version 6.12.80 | 可执行；version |
| P list sw | 0；cpu-clock、task-clock 等软件事件 | 软件事件可枚举；list_sw |
| P list hw | 0；输出为空 | 没有可枚举的硬件事件；list_hw |
| P record -e cpu-clock -F 999 -a -o /opt/afdo_agent/work/s1.data -- sleep 3 | 0；12,012 samples | 软件系统采样支持；software_system |
| P report -i /opt/afdo_agent/work/s1.data --stdio --sort dso（展示前 40 行） | 0；event cpu-clock，Lost Samples 0，99.58% [kernel.kallsyms] | 确有样本；software_system_report |
| P record -e cycles -a -o /opt/afdo_agent/work/h1.data -- sleep 2 | **0**；32,106 samples，无失败提示 | 不能据此判硬件支持；cycles_negative |
| P evlist -v -i /opt/afdo_agent/work/h1.data；P report --stdio --header-only -i 同文件 | 均 0；实际 cpu-clock: type 1、config 0；header 保留原请求 -e cycles | 硬件请求已回退软件；cycles_evlist、cycles_header |
| P report --stdio --sort dso -i /opt/afdo_agent/work/h1.data | 0；event cpu-clock、32K 样本 | 再次确认数据不是 cycles；cycles_report |

为什么负对照没有按预期报错：`src/linux-rpi/tools/perf/util/evsel.c:3212–3231` 的 fallback 在 cycles 打开失败为 ENOENT/ENXIO/ENODEV 时，改用 PERF_TYPE_SOFTWARE；系统级用 PERF_COUNT_SW_CPU_CLOCK，进程级用 TASK_CLOCK。该源码与本次 evlist/report 实际事件相符；具体触发的 errno 未由本次非 verbose 输出取得，不能虚构。当前事件源目录只有 breakpoint、kprobe、software、tracepoint、uprobe，没有硬件 PMU（current_kernel）。这个回退结果可作为新镜像的对照，届时必须核对数据实际事件类型，不只检查退出码。

| 能力 | 结论 | 证据与范围 |
|---|---|---|
| perf 可用性 | 支持 | /opt 部署后版本、依赖及实际命令成功 |
| 软件采样 | 支持 | 系统级 12,012 样本，两个解码场景都有样本 |
| 硬件 cycles | 不支持（当前镜像） | 无硬件 PMU，cycles 请求实际回退为软件 cpu-clock |
| 程序级 DSO 归属 | 支持 | libavcodec 等 DSO 可区分；下面给出样本计数占比 |
| 符号解析 | 支持（有限） | 导出符号及 PLT 名称可见；绝大多数 libavcodec 样本仍为地址，不能支持完整内部热点函数归属 |

## 4. 解码计时与采样开销

素材为本机 media/ 下已有的 60 秒 BBB H.264 两档视频。推送与两端 SHA-256 均成功：

| 文件 | SHA-256 |
|---|---|
| bbb_720p_h264_60s.mp4 | b5e116b9d01cec8e7f697041c53575d36bd96a5928e40faa69e731f9ae2d00a4 |
| bbb_1080p_h264_60s.mp4 | 31f72f11eb0566e0265358a14294e5dbddf13fce4ce1507d8872b04c2596a6da |

720p 三次无 perf，每次实际命令如下；1080p 替换文件名为 bbb_1080p_h264_60s.mp4 执行一次。所有管线正常 EOS、退出 0。环境沿用上文，计时使用 shell `time -p`，包含程序启动/管线结束时间。

```sh
time -p nice -n 19 ionice -c3 gst-launch-1.0 filesrc location=/opt/afdo_agent/work/bbb_720p_h264_60s.mp4 ! qtdemux ! h264parse ! avdec_h264 ! fakesink sync=false
```

720p 带 perf 一次，1080p 对应文件名和 s3.data 各一次：

```sh
time -p nice -n 19 ionice -c3 /opt/afdo_agent/tools/perf --buildid-dir /opt/afdo_agent/work/buildid record -e cpu-clock -F 999 -o /opt/afdo_agent/work/s2.data -- gst-launch-1.0 filesrc location=/opt/afdo_agent/work/bbb_720p_h264_60s.mp4 ! qtdemux ! h264parse ! avdec_h264 ! fakesink sync=false
```

| 场景 | real 秒 | user 秒 | sys 秒 | 退出码 |
|---|---:|---:|---:|---:|
| 720p 无 perf #1 | 13.47 | 29.81 | 1.24 | 0 |
| 720p 无 perf #2 | 11.43 | 29.36 | 0.65 | 0 |
| 720p 无 perf #3 | 12.04 | 29.57 | 0.65 | 0 |
| 720p 带 perf | 12.35 | 30.01 | 0.96 | 0 |
| 1080p 无 perf #1 | 23.29 | 64.60 | 1.23 | 0 |
| 1080p 带 perf | 24.43 | 66.92 | 1.47 | 0 |

| 场景 | 无 perf 次数 | real 均值 | real 最大−最小 | 带 perf real | 开销 | 保存样本 | 丢失样本 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 720p | 3 | 12.3133s | 2.04s | 12.35s | +0.30% | 26,158 | 0 |
| 1080p | 1 | 23.2900s | 0.00s | 24.43s | +4.89% | 15,416 | 1,034 |

开销公式：`(带 perf real / 无 perf real 均值 − 1) × 100%`。1080p 仅一次基线，范围 0 是单个观测的算术结果，不代表没有波动。720p 第一次包含新 registry 扫描，stderr 提示非本管线必需的 libgstcairo.so 因 libGLESv2.so.2 缺失而未加载；avdec_h264 管线仍成功。没有安装缺失库。三个基线已有 2.04 秒波动，所以 +0.30% 仅为本轮观测差，不是统计显著的固定开销。

**1080p 有丢样**：perf 提示 `Processed 16450 samples and lost 6.29%`，report 保存 15,416、丢失 1,034。后续占比只使用保存的样本，不能保证代表完整工作负载。按指定次数完成，没有自行调参/加跑。720p 丢失为 0。

原始计时/stderr：baseline_720p_1/2/3、sample_720p、baseline_1080p_1、sample_1080p。事件核对分别为 720p_evlist、1080p_evlist；均为 cpu-clock。

## 5. DSO 与符号统计

执行 `P report --stdio --sort dso -i 文件`，展示前 30 行；以及 `P report --stdio --sort dso,sym -i 文件`，展示前 40 行。两个分辨率均退出 0，摘录在证据 720p_dso/symbols 与 1080p_dso/symbols。为保留 report 本身真实退出码，先完整捕获输出再截取展示，没有使用 head 的退出码掩盖 perf 失败。

精确计数另外使用 `P report --stdio --sort dso,sym --show-nr-samples --percent-limit 0 --field-separator ';' -i 文件`（均退出 0），汇总全部行的 sample count。汇总分别等于 26,158 和 15,416，与保存总数一致。下表占比为 **样本数/保存总样本数**，不是默认 report 按 period 加权的 Overhead 百分比，因此与摘录百分比可能不同。全量计数输出在 temp/sampling-current/*_counted_symbols.json，统计在 statistics.json；发布证据保留汇总与可辨名称计数。

曾尝试 `perf script -F dso,sym`：退出 0，但本次仅产生与样本数相同的空行，未得到可用符号字段；没有用空行统计解析率，改用上述完整 report 计数。

### 720p 前 10 个 DSO

| DSO | 样本数 | 样本占比 |
|---|---:|---:|
| libavcodec.so.62.11.100 | 22,863 | 87.4035% |
| libc.so.6 | 1,996 | 7.6306% |
| [kernel.kallsyms] | 894 | 3.4177% |
| libavutil.so.60.8.100 | 85 | 0.3249% |
| libgstreamer-1.0.so.0.2411.0 | 83 | 0.3173% |
| libglib-2.0.so.0.8000.5 | 47 | 0.1797% |
| libgstlibav.so | 38 | 0.1453% |
| libgstvideo-1.0.so.0.2411.0 | 36 | 0.1376% |
| libgstbase-1.0.so.0.2411.0 | 28 | 0.1070% |
| libgobject-2.0.so.0.8000.5 | 19 | 0.0726% |

### 1080p 前 10 个 DSO

| DSO | 样本数 | 样本占比 |
|---|---:|---:|
| libavcodec.so.62.11.100 | 13,527 | 87.7465% |
| libc.so.6 | 1,179 | 7.6479% |
| [kernel.kallsyms] | 553 | 3.5872% |
| libgstreamer-1.0.so.0.2411.0 | 29 | 0.1881% |
| libavutil.so.60.8.100 | 27 | 0.1751% |
| libglib-2.0.so.0.8000.5 | 22 | 0.1427% |
| libgstbase-1.0.so.0.2411.0 | 20 | 0.1297% |
| libgstvideo-1.0.so.0.2411.0 | 15 | 0.0973% |
| libgstlibav.so | 14 | 0.0908% |
| ld-linux.so.3 | 8 | 0.0519% |

### 两个目标库的符号解析

“有名称”包括非地址符号和 @plt；纯十六进制地址/[unknown] 为未知。为避免夸大函数解析能力，PLT 单独列出，非 PLT 才是本轮可辨的普通函数符号样本。

| 场景/库 | 库内样本 | 有名称 | 有名称占库内样本 | 其中 PLT | 非 PLT 名称 | 未解析 |
|---|---:|---:|---:|---:|---:|---:|
| 720p / libavcodec.so.62.11.100 | 22,863 | 125 | 0.5467% | 117 | 8 | 22,738 |
| 720p / libgstlibav.so | 38 | 11 | 28.9474% | 11 | 0 | 27 |
| 1080p / libavcodec.so.62.11.100 | 13,527 | 116 | 0.8575% | 115 | 1 | 13,411 |
| 1080p / libgstlibav.so | 14 | 5 | 35.7143% | 5 | 0 | 9 |

720p libavcodec 的非 PLT 名称样本仅 av_packet_free=3、av_bsf_receive_packet=2、av_packet_unref=2、av_codec_is_decoder=1；1080p 仅 av_packet_unref=1。libgstlibav 本轮能辨的名称全部是 PLT，**没有解析出其内部函数样本**。已 strip 库不足以支持完整函数热点分析；本轮不下载 debuginfo 或修改库文件。

## 6. 清理与保留文件

工作目录清理命令实际已执行、退出 0：

```sh
nice -n 19 ionice -c3 find /opt/afdo_agent/work -mindepth 1 -delete && test -z "$(find /opt/afdo_agent/work -mindepth 1 -print -quit)" && ls -la /opt/afdo_agent/work
```

输出只含 `.` / `..`。视频、s1/s2/s3/h1.data、registry、cache、HOME/TMPDIR 内容、查询临时输出和 perfconfig 均已删除。没有拉回 perf.data；只有文本证据在主机。`rpm -qa` 先单独验证成功再计数，开始/结束均为 **1,252**；两个计数命令退出 0。未执行 RPM 安装/卸载。

板上仅保留以下两个部署文件（retained 项再次 SHA-256 验证成功）：

| 路径 | 大小 B | 来源包 | SHA-256 |
|---|---:|---|---|
| /opt/afdo_agent/tools/perf | 2,992,296 | linux-kernel-perf-6.12.80-0.armv7l | 41b9b9a0d41da1b2a600c84ffa482ea05c52af54af094f5c6a2bf52d6aa13138 |
| /opt/afdo_agent/lib/libLLVM.so.22.1 | 33,641,876 | libllvm-22.1.8-1.6.armv7l | 49fcc90da72ac2eabd7bbdb0a71566ea2284a532f98730ca46496782f30fb69e |

来源仓库（原 RPM 校验及依赖版本依据见 [02](02_rpi4_pmu_probe.md)）：

- perf：https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261022.054557/repos/standard/packages/
- libLLVM：https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261020.074527/repos/standard/packages/

需要完整删除部署时使用下列命令；本轮按要求保留工具，**没有执行此命令**：

```sh
rm -rf /opt/afdo_agent
```

## 7. 边界例外与证据预算

- 已知主机历史边界例外：`/tmp/sdb.log`，由既有共享 SDB daemon 使用；本轮末尾 stat 为 400 B、mtime `2026-10-28 12:01:10.724948977 +0800`，与本轮开始前记录一致。没有删除文件、重启共享服务或扩大工作区外扫描；不能由元数据不变证明完整 syscall 审计。是否改变共享服务日志位置需由用户协调。
- 用户明确授权的板上例外：清理旧 `/tmp/afdo_probe/`，并在 `/tmp/afdo_true_noexec_control` 做一次执行负对照后立即删除；其余本轮写入均位于 `/opt/afdo_agent/`。最终验证两个 /tmp 路径均不存在。没有新增已知的未授权边界例外。
- 正常 Git 推送认证按长期规则使用，不隔离、不修改全局配置。原手工安装方案取消，未调用 scripts/pmuv3_install/。

本轮证据 14 为 32,945 B；docs/probe/evidence/*.txt 全部合计 **149,956 B**，低于 150,000 B。为满足本轮总限额，04/05/06/08 历史证据保留必要结论片段、源码行号与退出码，移除重复长输出；各文件头附原完整证据的固定提交 raw 链接，本机完整副本在 temp/sampling-current/evidence-original/。这不是重新执行或改写旧探测结论。
