# TV 板 .13 的 K1a perf 临时部署与停止记录

2026-11-18，经 SDB 4.2.25 选择既有连接 `192.168.108.13:26101`。板子仍为 Novatek NT72671D、armv7l，与上次只读探测匹配。K1a 的 perf 和两项依赖已临时上传并核对，但动态加载器以 127 退出。本轮按部署停止条件结束，PMU 计数和两段内核采样均未开始。 [前次探测](09_board_probe_192.168.108.13.md) · [证据索引](evidence/10-tv13-perf-probe/index.json) · [结果](evidence/10-tv13-perf-probe/result.json)

## 共用板检查

开始前保存主机 `sdb devices` 原文，当时仅列出 .13。普通 shell UID 5001，governor 为 performance。初始 loadavg 为 `28.14 28.26 28.35`，上传前复查 load1 为 28.36，切 root 前复查为 28.34。上一轮报告 09 没有保存 loadavg 数字，本轮无法作数字上的跨次比较。高负载均值通过进程状态进一步核对。当时 28 个 D 状态线程主要是板上驱动和服务线程，两秒 `/proc/stat` 差分的总 CPU 空闲约 90.1%。主要后台线程与上次快照相符。筛查发现的 `MLBX_TEST_Thread` 为 PPID 2 的零 CPU 内核线程，`sleep` 为常驻 `pm_monitor.sh` 子进程。未观察到外部 perf、gdb 或用户测试负载。各次检查只有一条已建立的 26101 TCP 连接，同一 SDB 服务背后的其他客户端无法通过此计数排除。

本轮以进程、CPU 差分和 SDB TCP 快照共同判断可以进入部署。脚本另以 load1 大于 31、或除探测命令外出现 ps CPU 占用达 5% 的进程作为保守暂停信号，这两个值是本次检查用的启发值。没有触发 10 分钟等待。数据阶段未到达，无数据丢弃或重试。 [命令、退出状态与输出](evidence/10-tv13-perf-probe/evidence.json)

## 部署与失败证据

perf 来源为 `temp/rpms/perf-extract/usr/bin/perf`，SHA 与 K1a `baseline-rpi4-02/setup-shas.txt` 中板上工具相同。主机 `readelf` 确认 ELF32 ARM EABI5 soft-float 和解释器 `/lib/ld-linux.so.3`。直接 NEEDED 包括 libunwind、libunwind-arm、pthread、rt、m、dl、z、elf、dw、crypto、LLVM、stdc++、lzma、gcc_s、libc 和加载器。板上能找到除 libLLVM 外的直接依赖并读到 ELF32 文件头。libLLVM 间接依赖的 `libxml2.so.16` 也缺失，从已有 armv7l RPM `temp/gbs-deps-archive/ffmpeg-armv7l-20261114/libxml2-2.15.1-1.12.armv7l.rpm` 解包到主机工作区。缺失的两项只部署到同一临时目录，采用该目录作为 LD_LIBRARY_PATH。

| 部署文件 | SHA-256 |
|---|---|
| perf | `41b9b9a0d41da1b2a600c84ffa482ea05c52af54af094f5c6a2bf52d6aa13138` |
| libLLVM.so.22.1 | `49fcc90da72ac2eabd7bbdb0a71566ea2284a532f98730ca46496782f30fb69e` |
| libxml2.so.16 | `c654d9d5df44f906d0446a51c8507ec74a605191eb9f840883f003962dcd6487` |
| branch-0 | `1c51f5ec8cf84082f0b239b142ed396f10b79d2ec2fea7222c996b51873b1c70` |
| branch-1 | `3d43d2eb08abeaa9ead7ab8ebc9986c95b6d68639c48cad74898fc1b6c37ea92` |

1. 创建目录前登记 `/tmp/afdo_probe-tv13-pmu-20261118`。所有 push 成功，但 UID 5001 的 `sha256sum` 五项均报 `Permission denied`，已清理目录。
2. 单文件探测复现。普通 shell 能看到文件名，`stat`、`chmod`、读 SHA 均报权限拒绝。目录改成 0755 后仍失败，已再次核验删除。
3. 重建同一已登记路径，以普通会话推送相同五个文件，短暂切 root 只做读核对。root `ls -laZ` 可见目录标签 `User::Shell`、上传文件标签 `System`，五项 SHA 全部匹配。随后在临时目录内执行 `LD_LIBRARY_PATH=<该目录> /lib/ld-linux.so.3 --list ./perf`。如下是退出原文。SDB 客户端返回 0，板上命令返回 127。

```text
./perf: error while loading shared libraries: ./perf: failed to map segment from shared object
__TV_RC__=127
```

失败发生在加载器映射 `./perf` 时，动态依赖闭包和符号版本兼容性尚未完整验证。事后只读 mountinfo 显示 `/tmp` 为 tmpfs，已显示的挂载选项没有 `noexec`。映射失败的具体原因未确定。到达停止条件后随即恢复并清理，`perf --version`、`perf list hw`、`perf list raw` 均未执行。主机 readelf、板上查库、root 核 SHA、错误原文和最终状态见证据。 [部署证据](evidence/10-tv13-perf-probe/evidence.json)

## 计数与采样状态

主机用已有 LLVM 工具汇编和链接了两份静态 A32 程序，并保存源码、反汇编和 ELF 头。两版均循环 `N=67,108,864` 次，循环末尾 `bne` 被采纳 `N−1` 次，退出前未采纳一次。第二版每次迭代还经过 `cmp r0,r0` 与一条恒未采纳的 `bne`，共额外 `N` 次未采纳分支。程序未在板上执行。

| 请求结果 | 本轮状态 |
|---|---|
| CPU3 两版各 5 次 `cycles,instructions,r08,r0c,r10,r11,r12,r21` | 0/10，未开始 |
| `r0c` 对已采纳分支数的比例与偏差，未采纳分支是否计入 | 无计数，无法判定 |
| `r08` 与指令数、`r21` 支持情况、`:u/:k` | 无计数，无法判定 |
| 空闲 UI 30 秒和负载 30 秒的 system-wide cycles 采样 | 0/2，未开始 |
| 用户态/内核份额、内核前 30、IRQ 恢复函数份额、汇编符号推断份额 | 无样本，无法计算 |

本轮未读取、传输或归档 kallsyms。没有生成 perf.data。

## 清理与边界

三个部署及权限探测路径实例均使用同一个预登记绝对路径，结束后逐次删除并验证不存在。最后一次 `sdb root off` 返回 `Switched to 'sdk user' account mode`，即时检查和最终复查均是 UID 5001。最终 `performance`、`perf_event_paranoid=2`、`kptr_restrict=1`，SDB 原连接保留，板上仍有一条已建立的 26101 TCP 连接。

一次事后 mountinfo 查询的调用继承了主机 heredoc 标准输入，SDB 输出回显了后续文本。该原件保留，改用关闭标准输入的独立只读调用核对最终状态。没有在授权临时目录外写入项目产物，SDB 或系统自身日志未审计。只使用 .13，独立结果 worktree 与 origin/main 同步后提交。 [清理证据](evidence/10-tv13-perf-probe/evidence.json)
