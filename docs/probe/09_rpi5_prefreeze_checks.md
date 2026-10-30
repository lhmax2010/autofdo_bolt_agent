# RPi5 v0.5 冻结前核实：dsoff、buildid-mmap 与页大小

日期：2026-10-30（Asia/Shanghai）。仅验证与记录；未修改 LLVM、设计文档或开始实现，无 GBS 构建、无板上 RPM 安装/卸载、remount、重启或 /tmp 执行。

| 核实项 | 本轮结论 | 与 v0.5 / 05 对照 |
|---|---|---|
| 页大小 / cycles | 4096；type=0/config=0，固定周期数据 7,617 样本 | 页大小与 05 相同；符合硬件采样前提 |
| 单进程 dsoff / 可执行 PT_LOAD | 5,865/5,865，均 100% | 与 05 一致 |
| 双进程 | 两个不同加载基址，14,331/14,331 均 100% | 与 05 一致 |
| buildid-mmap | libc MMAP2 ID 与 ELF 20 字节 ID 一致；buildid-list 非空 | 与 v0.5 和 05 实测一致 |
| period | 固定周期一致；频率模式 2,431 种取值 | 与 v0.5 和 05 一致 |
| 新格式事实 | 一条系统级内核样本 pid/tid 为 `-1/-1` | 05 未记录此例；v0.5 未明确负值语义，见“对设计的影响” |

证据：[E1 环境与清理](evidence/09/01_environment_cleanup.txt)、[E2 采集与格式](evidence/09/02_sampling_formats.txt)、[E3 地址、ELF、身份与周期](evidence/09/03_mapping_buildid_period.txt)，共 **122,412 字节**。每段含原命令、stdout/stderr、真实退出码；SDB transport 返回码单列。建立 work 前与清理后的输出为 SDB 合并流；建立 work 后分别捕获输出，随后立即保存远端 `$?`，不以管道 head/SDB 退出码冒充 perf 返回值。

大文件、完整导出、JSON 及本轮一次性分析脚本均位于 `WORKDIR/temp/rpi5-prefreeze/`（下称 T），WORKDIR=`/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent`。以下 P 表示完整前缀 `nice -n 19 ionice -c3 /opt/afdo_agent/tools/perf --buildid-dir /opt/afdo_agent/work/buildid`，F 表示 `/opt/afdo_agent/work/`。

## 1. 环境

### 1.1 身份、镜像和页大小

最初 SDB connect 输出失败但进程退出 0；devices 无设备、ping 两包无回复、身份查询 transport exit1。没有把它认作成功。用户确认开机后重连成功，先断言 `uname -m=aarch64`，内核匹配 `6.12.*-arm64-rpi4-v8`；实际 **6.12.80-arm64-rpi4-v8** 与 04 相同。model=Raspberry Pi 5 Model B Rev 1.1，随后 root on 成功、id -u=0。证据 E1 connect/identity/root_*。

- `uname -a`：`Linux localhost 6.12.80-arm64-rpi4-v8 #1 SMP PREEMPT Wed Oct 28 12:37:44 UTC 2026 aarch64 GNU/Linux`。
- BUILD_ID=`tizen-unified-toolchain_20261028.105834_tizen-headed-aarch64`，比 04 的 20261027.063617 更新；不宣称是同一镜像。
- `getconf PAGESIZE`：**4096**，exit0；与 05 的 armv7l 相同，补齐本板未知项。
- `findmnt -T /opt`：`/opt /dev/mmcblk0p3 ext4 rw,relatime`；可写且无 noexec。未改变挂载。

板端 perf report 的墙上时间约比主机记录晚一小时；保留原文，不用两端时间相减计算耗时。

### 1.2 恢复工具与依赖

重刷后 `/opt/afdo_agent/` 不存在（原查询 exit1，E1 existing/disk_before）；从 04 已核验的本机解包副本重新推送。工具来源仍是 Unified 20261027.063617 与 Base 20261026.051209，而非声称来自新镜像快照。主机/板上 SHA-256 与 04 完全一致；`LD_DEBUG=libs P --version` 和 `ldd` 均 exit0，依赖全部解析，perf=6.12.80。

| 保留路径 | 来源包 / 本机副本 | SHA-256 |
|---|---|---|
| `/opt/afdo_agent/tools/perf` | linux-kernel-perf-6.12.80-0.aarch64；temp/rpms-aarch64/perf-extract/usr/bin/perf | `d23f11a13d5b0b21fc1957a883eb0025c80f9a26bcde360b7031b4d3b1348949` |
| `/opt/afdo_agent/lib/libLLVM.so.22.1` | libllvm-22.1.8-1.5.aarch64；temp/rpms-aarch64/llvm-extract/usr/lib64/libLLVM.so.22.1 | `06b9971c974f113b16ea49c988b6481f20272e70ba36040358735fa6c91af007` |

所有 perf 调用应用 `LC_ALL=C`、`LD_LIBRARY_PATH=/opt/afdo_agent/lib`；HOME=F/home、TMPDIR=F/tmp、PERF_CONFIG=F/perfconfig（空文件）、GST_REGISTRY=F/registry.bin、XDG_CACHE_HOME=F/cache。缓存和数据只写 F；完整环境见 E1/E2 命令。

### 1.3 硬件事件

`P record -e cycles -c 1000003 -o F/fixed.data -- L`，exit0，real=2.15s，采集 **7,617 样本**。`P evlist -v -i F/fixed.data`，exit0，`type: 0 (PERF_TYPE_HARDWARE)`、`config: 0 (PERF_COUNT_HW_CPU_CYCLES)`；没有软件回退。report exit0、Total Lost Samples=0。与 04/05 一致。E2 fixed_record/evlist/report。

## 2. 负载与目标

`command -v gst-launch-1.0 && gst-inspect-1.0 avdec_h264` exit0；实际使用 H.264 解码，目标 DSO 为 **/usr/lib64/libavcodec.so.62.11.100**，无需 spike 或重新构建。媒体 `media/bbb_720p_h264_60s.mp4` 推至 F，同步核对 SHA-256=`b5e116b9d01cec8e7f697041c53575d36bd96a5928e40faa69e731f9ae2d00a4`。

L 与 05 A.3 完全相同：

```sh
gst-launch-1.0 -q filesrc location=/opt/afdo_agent/work/bbb_720p_h264_60s.mp4 ! qtdemux ! h264parse ! avdec_h264 ! identity eos-after=300 ! fakesink sync=false
```

约 300 帧、10 秒媒体内容，不是强制 10 秒墙上运行。单进程、双进程、频率、buildid 四次 record 均 exit0；双进程显式 wait 两个解码进程，均 exit0。E1 gst/sha_media、E2 *_record。插件扫描的非本管线警告原文保留 E1，未安装包。与 05 相同负载、不同架构库，结果不用于性能 A/B。

## 3. dsoff 与地址换算

### 3.1 原始语法

所有数据在板上使用下面的固定字段投影，未增减字段（P 内的 buildid-dir 与 nice/ionice 仍保留）：

```sh
LC_ALL=C perf script -i <data> --show-mmap-events --show-lost-events -F pid,tid,event,period,ip,dsoff
```

四次导出均 exit0、stderr 空。E2 保存 fixed 前 200 行、固定和双进程各前 20 条目标样本原文；完整流为 T/{fixed,multi,freq,buildid}_dsoff.txt，并保留同名 .data，推拉两端 SHA 均一致。

实际顺序是 **pid/tid、period、event:、ip、(DSO+offset)**；pid/tid 用 `/` 相连，ip 是无0x前缀的十六进制，dsoff 为路径后 `+0x` 十六进制，与 05/5.2.2 一致。64位地址比 armv7l 更长；字段间空白宽度变化不能按固定列宽理解。

```text
   2085/2085    PERF_RECORD_MMAP2 2085/2085: [0xffffb25c0000(0x75c000) @ 0 b3:02 1290 3403977211]: r-xp /usr/lib64/libavcodec.so.62.11.100
   2085/2091       1000003 cycles:      ffffb2939c10 (/usr/lib64/libavcodec.so.62.11.100+0x379c10)
    458/458        1000003  cycles:      ffff994cd360 ([vdso]+0x360)
```

`[kernel.kallsyms]` 不带偏移；`[vdso]` 带偏移；本轮四份数据均未出现 `([unknown])`。另有一条 `-1/-1` 样本，详见下文；不把该内核样本当作未知 DSO。

### 3.2 逐样本公式与 PT_LOAD

临时脚本 `T/analyze.py` 按导出顺序维护同 pid 的 MMAP2，取最近一条覆盖 IP 的映射，并独立检查路径与 `ip - start + pgoff == dsoff`。这是验证脚本，不是 LLVM 实现。固定数据 **5,865/5,865（100%）** 一致，超过 1000 条；全部目标样本参与，无抽样或过滤错误。

从板上拉取目标实体 ELF 至 T/libavcodec，两端 SHA-256=`0aaecd3a290fdedb6fa0ba6088fd49cea8635bf7d89c1cbe94efe5506cc63166`。使用工作区内 `temp/GBS-ROOT-RPI5-SPIKE/local/BUILD-ROOTS/scratch.aarch64.0/emul/usr/bin/readelf`，并以该 root 的 x86_64 loader/库启动；未用本机工具链。`readelf -h/-lW/-n` 均 exit0，完整命令见 E3。

| 可执行 PT_LOAD | p_offset | p_vaddr | p_filesz | p_align |
|---|---|---|---|---|
| 唯一 R E 段 | 0 | 0 | 0x4b649c | 0x10000 |

按 `p_offset ≤ off < p_offset+p_filesz` 选段，再算 `vaddr=p_vaddr+(off-p_offset)`：固定 **5,865/5,865 唯一落段，100%**，无不一致样本。例子含 ip/start/pgoff/off/vaddr，见 E3 analysis results。与 05 一致，仍未覆盖**可执行段** p_offset≠p_vaddr；本库 RW 段虽是 0x4b64a0/0x4c64a0，但不是代码段，不能计作该覆盖。段对齐 64KiB 与实际页大小 4KiB 不矛盾，不需要页掩码。

### 3.3 双进程

用同一 shell 启动两个 L 后 wait；外层 `P record -a -e cycles -c 1000003 ... -- sh -c ...`（E2 multi_record 完整命令）。两个进程均 exit0：

| pid | libavcodec 映射起点 | 样本 | dsoff 公式一致 | 唯一落同一可执行段 |
|---|---|---:|---:|---:|
| 2178 | 0xffff81ee0000 | 7,174 | 7,174 / 100% | 7,174 / 100% |
| 2179 | 0xffff8eaf0000 | 7,157 | 7,157 / 100% | 7,157 / 100% |
| 合计 | 两个基址不同 | 14,331 | 14,331 / 100% | 14,331 / 100% |

两者文件偏移均落在同一个 `[0, 0x4b649c)` 可执行 PT_LOAD 范围。系统级流也含已有进程 911/916 的映射，未误当本轮解码进程；目标样本只有上述两个 pid。总计 26,778 条系统样本，report丢样为0；辅助 dummy:u 是映射事件来源，不是 cycles 回退。与 05 的多进程归一化结果一致。

## 4. --buildid-mmap

`P record --buildid-mmap -e cycles -c 1000003 -o F/buildid.data -- L` **exit0**、real=2.14s；完整 stderr 在 E2 buildid_record。导出计数7,226样本、report无丢样。与05一样，libavcodec没有build-id，MMAP2仍打印设备号/inode/generation；本轮用同一解码数据中的 **libc** 做非空ID正例，符合用户指定的可选目标。

```text
   2386/2386    PERF_RECORD_MMAP2 2386/2386: [0xffffb2ff0000(0x199000) @ 0 <8b45bf5b6a314fc498c8c73f164d6259c895405b>]: r-xp /usr/lib64/libc.so.6
```

拉回 `/usr/lib64/libc.so.6` 至 T/libc，SHA-256=`e28a87adc858f1f166ab7d781621f6afc79a2fef83323c19d66e64e003b6ee90`。GBS readelf -n：**8b45bf5b6a314fc498c8c73f164d6259c895405b**，20字节；MMAP2格式为 `@ 0 <十六进制ID>`，**1/1映射与ELF完全一致**。E3 libc_* / buildid MMAP2 / comparison。

`P buildid-list -i F/buildid.data` 和默认 `F/fixed.data` 均 exit0，全文在 E3：

- buildid-mmap 数据：libc、动态加载器、内核等有非空ID；libavcodec等库的路径前ID列为空。**buildid-list并非空输出**。
- 默认数据：libc、加载器、内核、vdso列出非空ID；没有列出libavcodec的有效ID。
- 两份list中的libc均为上述同一ID。与05 B.6及v0.5一致，不把list非空当作逐映射身份来源；libavcodec身份仍缺失，不能因libc匹配而称目标库身份通过。

## 5. period

| 模式 | 样本数 | sample_type | period分布 |
|---|---:|---|---|
| `-c 1000003` fixed | 7,617 | IP\|TID\|TIME | 全部1000003，单一值 |
| `-F 1000` freq | 2,581 | IP\|TID\|TIME\|PERIOD，freq=1 | 2,431个不同值，min1、max62,618,756 |

频率模式按 `[1,10)、[10,100)、…、[10^7,10^8)` 的条数依次为 **40、8、8、5、6、4、2440、70**，总和2581。完整取值频数在 T/fixed_periods.tsv、T/freq_periods.tsv；E3保留区间分布、top20，E2保留evlist原文。与05和v0.5固定周期回退attr、频率逐样本变化的行为一致；分布数值不同属于负载/架构运行结果，不是格式差异。

## 对设计的影响（仅事实，不改设计）

1. **新观察：系统级样本 pid/tid 可以打印为负值。** T/multi_dsoff.txt:11718 原文为：

   ```text
     -1/-1         1000003  cycles:  ffff80008008ed38 ([kernel.kallsyms])
   ```

   v0.5 5.2.2 写十进制pid/tid、5.2.3要求严格解析，但没有明确这个负值例子及语义；05未展示此例。不能假设只含无符号数字。临时分析最初的无符号正则因此漏计1条，改为接受符号后总数26,778与record一致；两版JSON留T，目标样本统计完全不变。不推断其产生原因，不修改LLVM/设计或扩展为实现。
2. 页大小、dsoff公式/多进程、特殊DSO偏移形式、buildid-mmap与list、period均符合v0.5及05实测；本轮未发现这些项的行为冲突。可执行p_offset≠p_vaddr仍没有板上正例，不能把RW段当作补齐；按设计仍由离线素材覆盖。
3. 未出现([unknown])，仍须按源码格式编写素材并注明来源；本轮只记录此剩余项，不开始lit实现。新LLVM发布后的原样构建复核仍待执行。设计未因验证完成自动冻结。

## 清理与边界

| /opt（df -k，KiB） | 已用 | 可用 | 使用率 |
|---|---:|---:|---:|
| 部署前 | 26,064 | 1,279,552 | 2% |
| 清理前快照 | 142,328 | 1,163,288 | 11% |
| 清理后 | 96,816 | 1,208,800 | 8% |

已执行 `find /opt/afdo_agent/work -mindepth 1 -delete` 并验证为空（WORK_EMPTY，exit0）；视频、四份data、导出文本、registry/cache、查询文件均删除。work目录4KiB，专用目录共70,400KiB；仅保留1.2的perf/libLLVM供后续使用，哈希再验一致。完整删除命令供后续用户决定：`rm -rf /opt/afdo_agent`，本轮未执行。RPM数量前后均 **1249**。E1 cleanup/disk_after/retained/rpm_*。

所有本轮主机项目输入/输出在WORKDIR，无新增已知边界例外；既有SDB共享daemon外部日志的历史审计限制保留，本轮未读取外部文件或重启服务，不能确认其隐式写入。板上写入只在/opt/afdo_agent，没有Downloads例外读取。本轮不涉及GBS构建，因而无构建结束标记。
