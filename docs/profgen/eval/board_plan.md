# 第一批板上评估计划（准备稿，未连接开发板）

本计划用于当前已冻结的 DWARF IP 路径；不能把主机素材、合成 profile 或本计划当成板上质量/收益结果。执行前必须确认最终构建清单验收完毕，并提供**不同视频内容**的测试输入。构建结果及阻塞项以 [报告 11](../impl/11_eval_prep.md) 为准。

## 1. 对象、变体与目录

每个对象分别构建 S、R、C、G5；RPi4 Thumb、RPi4 A32、RPi5 aarch64 各一套，spike 和 FFmpeg 共 24 个生成侧构建。A32 做全部四类，是第 5.8.9 条“一组 A32 附加覆盖”的保守实施选择：保留同 ISA 的 IR、coverage 与正常 PGO 对照，避免把 Thumb 参考拿来比较 A32。它不是设计新增的普遍必选范围。

- S：正常 optflags + profiling debug/唯一内部名 + 显式 SHA1 build-id，无 probe。
- R：IR 插桩，生成 `-fprofile-generate -mllvm -disable-preinline`，消费 `-fprofile-use` 同样关闭预内联。
- C：前端插桩 `-fprofile-instr-generate -fcoverage-mapping`，供 llvm-cov 行级参考。
- G5：IR 插桩，正常 flags，生成 `-fprofile-generate`；训练后再以 `-fprofile-use` 构建优化对照，不关闭预内联。

**本轮 G5 产物是训练用生成版，不是已消费 profile 的优化版。** G1–G4 与 G5-use 要等板上采集完成，在主机上用相同源码相对路径/flags/匹配产物再构建；不能把插桩开销当作优化收益。R/C 不合并，R/G5 分开。

部署只解包、复制到 `/opt/afdo_agent/variants/<id>/{bin,lib}`，不安装 RPM，不碰 `/usr`、`/boot`。复制该变体整套 FFmpeg 运行库，保留相对 SONAME 链接；GStreamer 系统插件通过 `LD_LIBRARY_PATH=<variant>/lib:/opt/afdo_agent/lib` 使用这些库。不要混放不同变体的 libavcodec/libavutil 等。同架构 perf 与 libLLVM 沿用已验证部署。

脚本放 `/opt/afdo_agent/scripts/`，包括 common.sh、collect.sh、measure.sh。清单 TSV 放 `/opt/afdo_agent/eval-manifest.tsv`，无表头，每行 9 列：

```text
variant_id<TAB>arch<TAB>object<TAB>stage<TAB>program<TAB>libdir<TAB>target_ELF<TAB>SHA256<TAB>SHA1_build_id
```

所有路径都在 `/opt/afdo_agent/`，不带空白；arch 为 armv7l/aarch64，object 为 spike/ffmpeg；stage 为 S/R/C/G5（生成）或 USE（消费）。FFmpeg 的 program 字段填 `gst-launch-1.0`，target_ELF 填该目录中 libavcodec 的实体文件；spike 填自己的可执行文件。哈希/ID取最终运行 RPM，**不能取 BUILD 目录文件**。主机产物核对表用于生成清单；清单与工具、库、视频要经 SDB push 后再次 SHA 校验。本计划不执行这些操作。

本机可从本轮已核验产物准备payload（不连接板子、不安装RPM；目标目录必须尚不存在）：

```bash
nice -n 19 ionice -c3 python3 tools/profgen/prepare_board_bundle.py temp/eval-prep11/artifact-summary.json temp/eval-prep11/payload-rpi4 --arch armv7l
nice -n 19 ionice -c3 python3 tools/profgen/prepare_board_bundle.py temp/eval-prep11/artifact-summary.json temp/eval-prep11/payload-rpi5 --arch aarch64
```

只部署其中`variants/`、`scripts/`、`eval-manifest.tsv`到`/opt/afdo_agent/`；`unpacked/`留主机。ARM应有8条、AArch64应有4条FFmpeg/spike各自清单项（合计16/8），若完整构建未完成不得把局部清单当作全套。

## 2. 身份与权限门禁

RPi4：device-tree model 为 Raspberry Pi 4，uname -m=armv7l，release 含 rpi4/v7l。RPi5：model 为 Raspberry Pi 5，arch=aarch64，release 匹配已登记的 arm64-rpi4-v8 系列。旧设备别名可能仍叫 rpi4，不用 SDB 别名认板。脚本首先断言，不符退出，不创建目录。IP 暂用用户登记的 192.168.108.26，换板后重新确认，不凭 IP 判型。

脚本拒绝 /opt 的 ro/noexec 挂载以及指向目录外的路径；无 findmnt 时停止，先人工用挂载信息核实，不自动换目录。工具/脚本/临时文件都不在 /tmp 执行。身份通过后保存镜像 BUILD_ID、uname -v、RPM 包数、/opt 占用、governor、频率、thermal、pswpin/pswpout和后台负载。节流使用 vcgencmd get_throttled；工具缺失明确记 unknown，不能声称无节流。

以下操作**本轮全部未执行**，开板时由用户决定。必须先备份再改，测量结束恢复；不默认要求关闭安全设置或所有后台服务。

| 操作 | 命令/作用 | root 与恢复 |
|---|---|---|
| SDB root | `sdb -s 192.168.108.26:26101 root on`，提供系统 perf 权限 | 需设备支持；事先记录原状态，若原为 off 则结束 `sdb -s 192.168.108.26:26101 root off` |
| 固定 governor | 见下面完整保存/设置块，减少频率噪声 | 写 sysfs 通常需 root；逐 policy 恢复原字符串 |
| perf_event_paranoid | 原值读 `/proc/sys/kernel/perf_event_paranoid`；仅非 root 确实被拒绝且用户同意时才 `printf '0\n' > /proc/sys/kernel/perf_event_paranoid` | 保存到 opt 下后原值写回；root 已能采样时不改 |
| 符号可见性 | 默认不改 kptr_restrict；模块样本若因权限无法归属，记录未知 | 若用户决定修改，先保存原值，再写 0，结束恢复；不作为用户态采样前提 |
| perf 本身 | 系统级 `perf record -a`/高频 lost 压力会增加负载 | root 或相应 capability；进程结束即释放事件，不修改内核配置 |
| 部署/清理 | mkdir、SDB push、SHA校验，以及拉回后删除本轮 RUN 目录 | 仅 /opt/afdo_agent；不覆盖原系统库，删除本轮目录恢复磁盘占用 |
| 可选 CPU 亲和性 | `taskset -c 0 <decoder>`、校验进程另置 CPU1 | 通常自身进程无需 root，进程退出恢复；若采用，所有组固定同一策略并记录，不把两者同时绑同一核 |

用户选择固定 governor 后，在已经通过身份断言的 root shell 中执行：

```bash
mkdir -p /opt/afdo_agent/state
: > /opt/afdo_agent/state/governors.tsv
for p in /sys/devices/system/cpu/cpufreq/policy*/scaling_governor; do
    [ -r "$p" ] || continue
    printf '%s\t%s\n' "$p" "$(cat "$p")" >> /opt/afdo_agent/state/governors.tsv
done
[ -s /opt/afdo_agent/state/governors.tsv ] || exit 1
while IFS="$(printf '\t')" read -r p old; do
    printf 'performance\n' > "$p" || exit 1
done < /opt/afdo_agent/state/governors.tsv
# 测量结束或出错后恢复：
while IFS="$(printf '\t')" read -r p old; do
    printf '%s\n' "$old" > "$p" || exit 1
done < /opt/afdo_agent/state/governors.tsv
```

perf 参数若需改变，先 `cat /proc/sys/kernel/perf_event_paranoid > /opt/afdo_agent/state/perf_event_paranoid`，恢复为 `cat /opt/afdo_agent/state/perf_event_paranoid > /proc/sys/kernel/perf_event_paranoid`；kptr_restrict 同法保存/恢复对应文件。没有必要不改。脚本本身不写 sysfs/sysctl、不 remount、不重启、不装卸 RPM。

## 3. 两块板的执行顺序与估时

下列时间是规划估算，不是测量值；长视频和插桩开销可能延长。每次换板重新部署正确架构、重新断言。

| 阶段 | RPi4（Thumb 主评估 + A32 附加） | RPi5（aarch64） | 产物/门禁 |
|---|---:|---:|---|
| 身份、空间、工具/插件、库SHA/ID、热稳态 | 10–20分钟 | 10–15分钟 | 不符停止；预估至少留 4GB 可用空间，实测不足则先缩小批次，不自行删除旧数据 |
| spike校准、S采样与R/C/G5训练 | 20–40分钟 | 15–25分钟 | rounds先调至每次10–20秒，三种预算各>=5独立采样；相同输入校验值一致 |
| FFmpeg训练输入的S采样、R/C/G5训练、固定/频率/LOST | 30–60分钟 | 20–40分钟 | 完整data/script/buildid-list、profraw、加载映像核验 |
| 真实fork/exec/deleted/module/-1集成 | 15–30分钟 | 15–25分钟 | 独立身份/地址事实，不能用构造文本代替 |
| 收尾拉回/哈希/清理 | 10–20分钟 | 10–15分钟 | 验证主机收到全部大文件后，才删除板上本轮RUN目录 |
| **第一轮采集小计** | **约85–170分钟** | **约70–120分钟** | 不含等待主机消费构建 |
| 消费构建后测试视频交错测量 | 30–70分钟 | 20–45分钟 | 每组1预热丢弃 + 至少10保留轮；按实际入围组数延长 |

先 spike 的 aggregation × skid × weight，再 libavcodec 的 zero-fill/head；默认值只能据测试视频上的质量、差值CI/等价区间与收益决定。正式 ε、噪声剔除阈值、样本预算需要在看到组间效果前确定。bootstrap 默认独立重采样；采用配对必须提前声明配对设计，不把“交错”自动解释成配对。

## 4. 采集与消费接口

脚本入口（部署完成且清单存在后，以下路径可直接使用）：

```bash
/bin/bash /opt/afdo_agent/scripts/collect.sh rpi4 sample-fixed ffmpeg-thumb-S /opt/afdo_agent/eval-manifest.tsv /opt/afdo_agent/media/bbb_720p_h264_60s.mp4
/bin/bash /opt/afdo_agent/scripts/collect.sh rpi4 sample-freq ffmpeg-thumb-S /opt/afdo_agent/eval-manifest.tsv /opt/afdo_agent/media/bbb_720p_h264_60s.mp4
/bin/bash /opt/afdo_agent/scripts/collect.sh rpi4 R ffmpeg-thumb-R /opt/afdo_agent/eval-manifest.tsv /opt/afdo_agent/media/bbb_720p_h264_60s.mp4
/bin/bash /opt/afdo_agent/scripts/collect.sh rpi4 C ffmpeg-thumb-C /opt/afdo_agent/eval-manifest.tsv /opt/afdo_agent/media/bbb_720p_h264_60s.mp4
/bin/bash /opt/afdo_agent/scripts/collect.sh rpi4 G5 ffmpeg-thumb-G5 /opt/afdo_agent/eval-manifest.tsv /opt/afdo_agent/media/bbb_720p_h264_60s.mp4
/bin/bash /opt/afdo_agent/scripts/collect.sh rpi4 lost ffmpeg-thumb-S /opt/afdo_agent/eval-manifest.tsv /opt/afdo_agent/media/bbb_1080p_h264_60s.mp4
```

RPi5用 `rpi5` 与 `ffmpeg-a64-*`；A32用`ffmpeg-a32-*`；spike用`spike-<isa>-<stage>`并把最后参数改为经校准的正整数 rounds。执行命令相同，必须再次检查清单arch。脚本不会把硬件cycles失败切换成软件事件。

每次采集均使用 `--buildid-mmap`，固定间隔 `cycles -c 1000003` 或频率 `cycles -F 1000`；负载与预算最终按样本量选定。导出严格为：

```text
LC_ALL=C perf --buildid-dir <RUN>/buildid script -i <RUN>/perf.data --show-mmap-events --show-lost-events -F pid,tid,event,period,ip,dsoff
```

完整文本落盘，**不通过 grep/awk 过滤主导出**；另保存 evlist、buildid-list、stderr、真实退出码。LOST 模式用1080p、`-c 10007 -m 1`；若不足，在下一次明确执行两个并发解码负载的系统级录制，仍保留完整文本，不仅保留LOST行。不能保证首次一定丢样；没有就记无，并保留尝试记录。用于补齐06挂账的必须是LOST较多且完整保留的一份。

采集和每轮测量在运行中保存 `/proc/<pid>/maps`，必须命中清单中的目标实体路径（不接受 deleted 作为正常组加载），核对该文件SHA与主机记录的build-id绑定；采样数据的 buildid-list 再直接核对 ID+路径。每秒记录频率、thermal、节流状态、pswpout与负载。训练时 `LLVM_PROFILE_FILE=<RUN>/<stage>-%m-%p.profraw`，避免多个插桩 DSO 相互覆盖。

GStreamer管线固定 H.264软解、max-threads=1、I420，解码字节经 `/opt/...` FIFO 交给 sha256sum，不把数GB裸帧落盘。性能轮次也做校验，校验进程可能产生背压；wall time因此是包含校验流程影响的端到端指标，不能声称纯解码耗时。perf stat只跟踪解码进程的cycles/instructions作为辅助。若校验成为瓶颈，应在所有组统一校验策略后重跑，不事后只剔除不利轮次。

主机接收 profraw 后用对应GBS root的llvm-profdata merge，只选实际负载的`R-*.profraw`、`C-*.profraw`或`G5-*.profraw`，各类型分别合并；`setup-*.profraw`来自gst-inspect/插件扫描，保留审计但不混入训练。R使用后转储pgo-instr-use，sample侧转储sample-profile并关闭sample loader inlining；工具 `match_ir_semantics.py` 加两侧诊断，遇到未匹配/部分忽略函数整体排除。C的实际RPM拆分把`__llvm_covmap`/`__llvm_covfun`保存在debuginfo，不能直接只给llvm-cov运行文件或.debug：运行文件无covmap，debug的`__llvm_prf_names`为NOBITS，单读debug会报function name is empty。先用GBS root的`eu-unstrip -o <combined> <runtime> <debug>`合成匹配对象，再用`llvm-cov export <combined> -instr-profile=<C.profdata>`。三ISA合成对象的reader已用无关合成profile检查可读（不是计数验收）；真实计数匹配仍需板上训练后验收，本轮不伪造。

## 5. 性能测量与集成用例

待 G0 与训练后 G1–G5 入围库部署、清单标记 USE 后：

```bash
/bin/bash /opt/afdo_agent/scripts/measure.sh rpi4 /opt/afdo_agent/eval-manifest.tsv /opt/afdo_agent/media/test_h264.mp4 G0 G1 G5-use
```

上述组名是消费阶段清单约定，**当前生成侧清单不能直接执行此命令**；缺组时脚本拒绝，不用R/C/G5生成版替代。RPi5同法。每组一次预热丢弃、10轮保留，轮次内轮转组顺序；原始time/perf-stat/校验和、每轮前后环境及逐秒telemetry全部保存。先预注册异常标准（换出增加、节流、温度/频率越界），报告剔除前后两套结果，禁止只保存均值或清除异常原始轮次。

集成用例另开RUN，不与性能样本混合：

| 用例 | 计划操作与必须保存的事实 |
|---|---|
| fork不exec | 复用07已知小程序或按相同源重建，父子同段计算；完整采样，检查子进程无自身MMAP2时的继承、两pid计数、独立地址换算 |
| exec不同映像 | 同pid先A后exec B；保留COMM/MMAP2/样本完整导出用于诊断，分别按两目标核对exec前后映像；若主导出出现设计不接受的记录，单列，不过滤冒充已接受 |
| 运行中替换库 | 测试专用共享库放本轮work目录，加载后仅删除/替换该测试副本；保存真实`(deleted)`样本和MMAP2、旧新ID，绝不动部署正式库或系统库 |
| 内核模块 | 只读lsmod；选择已加载、能由普通网络/文件读取操作触发的模块，系统级cycles录制；不modprobe/卸载模块。无样本则记未知，不构造成功 |
| 系统级-1/-1 | 单独`-a`短录制，保存真实-1样本与原始PID字段；没有则如实记录，不伪造 |

## 6. 输入、数据量与清理

当前可用输入都来自同一BBB影片：720p与1080p都是300–360秒内容，不能分别当作独立训练/测试。原始634.6秒影片也不是另一部视频。已核对元数据与SHA，清单见报告11。训练暂用已有720p，1080p用于压力/分辨率敏感性；测试视频待用户提供另一部独立H.264内容。可选方案是用户提供有权使用的独立片源，再按相同编码条件转码；或另生成固定种子的独立动态场景作为合成泛化试验，但不能把它称为真实视频泛化。本轮不下载、不生成新视频。

每次普通采样预计 data数MB–数十MB、完整文本约10–100MB；高LOST尝试可能data数十MB、文本数百MB。profraw大小随FFmpeg被插桩函数数变化，预留数百MB；逐秒环境与每轮日志通常<10MB。运行库与输入再占数百MB。按每板4GB可用空间起步，先读df和首份文件大小再调整批次。两板第一轮总主机留存预估1–4GB；不作为硬门槛保证。

每次保存RPM数量和/opt前后df。主机拉回全部perf.data、完整perfscript、buildid-list、profraw和日志，核对SHA后才清理对应 `/opt/afdo_agent/work/eval-*` 实际RUN目录；先列出确认，再只删除本轮目录。保留脚本/工具/库供消费轮复用；整个实验结束的完整删除命令为 `rm -rf /opt/afdo_agent`，仅在用户确认不再需要这些部署文件后执行。恢复用户允许修改的governor/sysctl，确认RPM数量未变，记录最终磁盘占用。
