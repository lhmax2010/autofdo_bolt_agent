# TV 板 .13：root 下的 perf、PMU 计数与内核采样

2026-11-18（America/Los_Angeles），目标 `192.168.108.13:26101`。K1a 的 **perf 6.12.80 在 /root 可运行**，两项补充依赖均由任务目录加载。CPU3 系统级 cycles 有计数。规定的 A32 进程级计数没有有效事件读数。两段 system-wide record 都成功写出数据，随后因共享状态标记丢弃，未用于份额分析。 [前次 /tmp 部署停止记录](10_tv13_perf_pmu_probe.md) · [结果与证据索引](evidence/12-tv13-root-perf/index.json)

## 共用检查和部署

主机开始和结束的 `sdb devices` 均显示 .13 为 `device`。每阶段前检查 `ps`、loadavg、SDB TCP 连接和 governor。起始 loadavg 为 `28.47 28.31 28.34`，与上轮约 28 的已知驱动线程基线接近。当时只有一条已建立的 26101 TCP 连接，无法据此排除同一 SDB 服务背后的客户端复用。

- 初始 root 视角的 `ps` 以生存期平均值将 Enlightenment 标成高活动。实时差分中，它在 3.03 秒内增加 0 tick，同一窗口 `source-service` 增加 71 tick（CLK_TCK=250，约单核 9.4%）。两者的可执行路径为系统 `/usr/bin`，以实时差分复核其活动。前置驱动首次暂停后退出并恢复 root，未部署和测量。
- A2 槽位中，`source-service` 在一个 0.13 秒观察间隔增加 10 tick，折合约单核 30.8%，超过本次保守检查使用的 25%。其后 1.14 秒增量为 33 tick，整个观察范围约单核 13.5%。保留原始判定，丢弃 A2 槽位且不补测。没有据此认定他人使用。
- 继续前发现 `scs_reporter` 的生存期平均值触发前置阈值，等待 600 秒后复查通过。随后前置检查又误报同一系统服务链的短寿命子进程，累计 CPU 显示 `00:00:00`。修正误报后，只启动此前未开始的槽位，保留原门禁和原始记录。四次 root 交接均以 root off 和 UID 5001 收尾。

每次创建前登记 `/root/afdo_probe-tv13-20261118`。部署来源沿用报告 10，五个二进制/库及两个本轮脚本全部板上 SHA 匹配。设置 `LD_LIBRARY_PATH`、HOME、TMPDIR 和 build-id 缓存路径到该目录。`/lib/ld-linux.so.3 --list ./perf` 退出 0，无缺失项。其余依赖由系统库加载，以下两项从任务目录加载。

| 文件 | SHA-256 |
|---|---|
| perf | `41b9b9a0d41da1b2a600c84ffa482ea05c52af54af094f5c6a2bf52d6aa13138` |
| libLLVM.so.22.1 | `49fcc90da72ac2eabd7bbdb0a71566ea2284a532f98730ca46496782f30fb69e` |
| libxml2.so.16 | `c654d9d5df44f906d0446a51c8507ec74a605191eb9f840883f003962dcd6487` |

`perf list hw` 显示 cycles、instructions、branches、branch-misses 等通用事件。完整 `perf list` 显示 `rNNN` 描述符和 `armv7_cortex_a7` 的 PMU 事件，其中 `pc_write_retired`、`inst_retired`、`cpu_cycles`、`br_mis_pred` 均列出。单独的 `perf list raw` 只列出 raw_syscalls tracepoints，原文保留。 [加载器、清单与命令](evidence/12-tv13-root-perf/final-run.json)

## A32 PMU 计数

两份静态程序与上轮相同，CPU3 绑定，N=67,108,864。A 版循环末尾 `bne` 采纳 N−1 次、未采纳一次。B 版每次迭代额外执行相等比较和一条恒未采纳的 `bne`，因此两版具有相同的采纳数，B 多 N 次未采纳条件分支。

```sh
taskset -c 3 ./perf stat -x , -e cycles,instructions,r08,r0c,r10,r11,r12,r21 -- ./branch-0
taskset -c 3 ./perf stat -x , -e cycles,instructions,r08,r0c,r10,r11,r12,r21 -- ./branch-1
```

| 事件 | A 的 4 个保留槽位 | B 的 5 个保留槽位 | 判断 |
|---|---|---|---|
| cycles、instructions | 全部 `<not counted>` | 全部 `<not counted>` | 无进程级读数 |
| r08 | 同上 | 同上 | 指令计数比例与偏差无定义 |
| r0c | 同上 | 同上 | 无法判定是否仅计已采纳分支 |
| r10、r11、r12 | 同上 | 同上 | 无进程级读数 |
| r21 | 同上 | 同上 | 无法判断不支持与否 |
| cycles:u/k、instructions:u/k、r0c:u/k | 另外执行一次 B 的分权限检查，六项均 `<not counted>` | | 本次未取得分权限读数 |

所有指定槽位的板上命令均退出 0，但保留槽位的事件运行时间均为 0 ns，运行率 0.00%。`<not counted>` 不计为数值 0，也不归为 `<not supported>`。另一次独立诊断 `perf stat -x , -a -C 3 -e cycles -- sleep 1` 取得 **288,887,329 cycles**，运行时间 879,595,921 ns，运行率 87.00%。这确认内核在该次系统级 CPU3 范围能提供 cycles 读数。进程级事件不计数的原因尚未定位。包括分权限和诊断在内共 36 次频率读数全为 **1350 MHz**。 [逐槽位结果](evidence/12-tv13-root-perf/result.json)

## 系统级采样

以 root 执行 `perf record --no-buildid-cache --no-buildid -a -e cycles -c 1000003 -o <文件> -- sleep 30`。空闲轮开始前 DRM 的 LVDS 为 connected/enabled，未发送 UI 操作。负载轮先测 sched pipe 100,000 loops 用时 2.294 秒，然后以 CPU3 绑定运行 1,482,127 loops 的两进程 bench。父 bench `Cpus_allowed_list=3`，子进程继承，record 结束时 bench 仍存活，最终自然结束。

| 轮次 | record 退出码 | 命令起止间隔 | perf 报告写入 | 频率 | 样本资格 |
|---|---:|---:|---:|---|---|
| 空闲 UI | 0 | 31.09 秒 | 4.083 MB | 29/29 读数为 1350 MHz | 丢弃 |
| CPU3 sched pipe | 0 | 31.16 秒 | 4.964 MB | 32/32 读数为 1350 MHz，含 bench 收尾 | 丢弃 |

间隔基于板上 uptime，包含 perf 初始化和收尾。负载 bench 自报耗时 34.948 秒，两段均无补测。监控在空闲和负载轮分别记录未归入本任务的 `acm-watcher`（PID 2319、3250，PPID 1131），`ps` 生存期平均值短时为 5.5%/5.4%，因此触发保守标记。进程是否来自他人会话未知。监控还误把本任务的 `record.sh`、`sched-pipe`、`perf-exec` 归为外部进程，父子 PID 可证这些是自身进程。该实现缺口单独登记，两段原始排除判定保留，均未解码。

正式接受样本段为 **0/2**。用户态/内核样本比例、内核前 30、IRQ 恢复符号的样本占比、按符号名推断的汇编例程份额均无有效输入。主机仅在内存中读取一次 kallsyms 以备符号化，未获得非零文本地址。该调用没有板上退出码哨兵，无法进一步区分是否读取失败或地址不可用。全文未落盘，也未归档未接受的 perf 数据。 [两段 record、频率与排除原文](evidence/12-tv13-root-perf/record-transcripts.json)

## 清理

最后一次板上删除 `/root/afdo_probe-tv13-20261118` 后，以路径及符号链接均不存在验证，返回 `verified-absent`。随后 root off，并复核 **UID 5001**、governor **performance**、`perf_event_paranoid=2`、`kptr_restrict=1`。原 .13 SDB 连接保留。记录仅针对 .13，未结束其他进程。SDB 内部日志及系统服务自身写入未审计。独立 worktree 同步后提交。 [收尾证据](evidence/12-tv13-root-perf/final-run.json)
