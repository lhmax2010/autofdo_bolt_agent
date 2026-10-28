# PMUv3 内核构建执行记录：进程退出，ALL-END 缺失

更新时间：2026-10-28（Asia/Shanghai）。**按用户最新例外规则停止监测、等待指示，没有进入第二段产物核验或安装说明。** 日志报告构建成功，但包装脚本的状态收尾缺失，不能将状态改写为 OK。

## 1. 判定与关键证据

北京时间 13:12:59 首次例外检查发现目标进程不存在；13:14:08 复核并保存证据：

```text
$ ps -o pid,ppid,pgid,stat,etime,pcpu,rss,args -p 98602,98603
EXIT=1
    PID    PPID    PGID STAT     ELAPSED %CPU   RSS COMMAND
```

`ps -eo pid,ppid,pgid,stat,etime,pcpu,args` 返回 0；按 98602/98603 递归 PPID 链筛选，MATCHING_ROWS=0。为避免把父进程消失直接等同于没有孤儿进程，同一快照还按本任务 worktree、buildroot、配置和脚本路径匹配，排除诊断进程及其祖先后，MATCHING_ROWS=0。没有发现仍在运行的本任务 gbs/depanneur/build/make/clang 进程；不存在可供读取消耗的目标 PID，不能伪写其 CPU 为 0%。已失去父子链且命令不带任务路径的进程无法仅凭这份快照追溯，未扩大检查其他任务。

找到的 scratch 为：

`temp/GBS-ROOT-RPI4-PMUV3/local/BUILD-ROOTS/scratch.armv7l.0`

其中 `.build.log` 的 stat 和 tail -n 50 均返回 1，原始错误：

```text
stat: cannot statx 'temp/GBS-ROOT-RPI4-PMUV3/local/BUILD-ROOTS/scratch.armv7l.0/.build.log': No such file or directory
tail: cannot open 'temp/GBS-ROOT-RPI4-PMUV3/local/BUILD-ROOTS/scratch.armv7l.0/.build.log' for reading: No such file or directory
```

文件不存在，无法给出大小、修改时间或末尾 50 行；不是无读权限，没有提权。没有继续寻找或读取移走后的日志。

外层日志末尾明确包含：

```text
[ 1692s] linhao-linux finished "build linux-rpi.spec" at Wed Oct 28 04:30:30 UTC 2026.
info: finished building rpi4-linux-kernel
info: *** Build Status Summary ***
=== Total succeeded built packages: (1) ===
```

对应北京时间 **12:30:30**。这证明日志报告 spec 构建成功，不能恢复已经消失的 GBS 进程的真实退出码，也不能解释包装 worker 为什么没有写结束标记。本轮未诊断或修改脚本。

原始检查文本保存在 `temp/pmuv3-monitor/stop_evidence.txt`，原日志/状态保留在 `temp/logs/`。没有结束任何进程，没有修改 status、脚本、配置或 spec，没有重新构建，也没有连接开发板。

## 2. 执行与监测过程

原样执行的命令：

```sh
/bin/bash /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/scripts/build_pmuv3_kernel.sh
```

前台返回 0；预检通过；nproc=20、make -j10、GBS --threads 1；worker PID=98602，GBS PID=98603。脚本记录开始时间 **11:56:53+08:00**；日志中的 spec 完成时间 **12:30:30+08:00**，相隔 33 分 37 秒。包装任务结束时间未知，未写 END/GBS_EXIT 数字。重跑次数 **0**：没有观察到需要重跑的临时网络失败。

| 检查时间（北京时间） | 观察 |
|---|---|
| 11:57 左右 | RUNNING，GBS 将 worktree 识别为 git，开始导出 |
| 11:59:53 左右 | 仍在导出阶段 |
| 12:03:44 左右 | 下载推进到约 58/130，已越过导出阶段；这次检查晚于计划第 6 分钟约 51 秒 |
| 12:05:54（第 9 分钟） | 下载到 130/130，未见 sudo 或网络错误 |
| 12:08:53（第 12 分钟） | 内核 CC/AR 编译进行中 |
| 12:11:53（第 15 分钟） | 驱动/模块编译进行中 |
| 12:21:53（第 25 分钟） | 普通/RT devel 文件处理及 debuginfo 打包；vdso 已 strip 警告 |
| 12:31:53、12:41:53、12:51:53、13:01:53、13:11:53 | status 一直 RUNNING；日志末尾一直是输出目录信息，无 ALL-END |
| 13:12:59、13:14:08 | 用户批准的只读例外检查；两个 PID、子孙链、任务路径匹配均无结果，按新规则停止 |

常规检查只使用 cat status 和 tail -n 5 外层日志。前 15 分钟后按 10 分钟间隔检查；之后因用户明确批准的进程退出分支提前停止，没有等到 8 小时上限，也没有把 RUNNING 当作进程仍存活的证据。

## 3. build_pmuv3.status 全文（原样保留）

```text
START 2026-10-28T11:56:53+08:00
HEAD c27f160de761bb55f64672ceac642698a6e93684
PHASE BUILDING
GBS_PID 98603
GBS_EXIT RUNNING
```

**缺少 ALL-END、END 和数字 GBS_EXIT。** 不补写、不推断为 0。

## 4. 外层 build_pmuv3.log 最后 50 行（仅去除行尾空白）

```text
[ 1615s] Processing files: linux-kernel-bpftool-debuginfo-6.12.80-0.armv7l
[ 1615s] Aptk: PG1hbmlmZXN0PgogPHJlcXVlc3Q+CiAgICA8ZG9tYWluIG5hbWU9Il8iLz4KIDwv
[ 1615s] cmVxdWVzdD4KPC9tYW5pZmVzdD4K
[ 1615s]
[ 1615s] warning: Missing build-id in /home/abuild/rpmbuild/BUILDROOT/rpi4-linux-kernel-6.12.80-0.arm/usr/lib/debug/usr/sbin/bpftool.debug
[ 1615s] Provides: linux-kernel-bpftool-debuginfo = 6.12.80-0 linux-kernel-bpftool-debuginfo(armv7l-32) = 6.12.80-0
[ 1615s] Requires(rpmlib): rpmlib(CompressedFileNames) <= 3.0.4-1 rpmlib(FileDigests) <= 4.6.0-1 rpmlib(PayloadFilesHavePrefix) <= 4.0-1
[ 1615s] Recommends: rpi4-linux-kernel-debugsource(armv7l-32) = 6.12.80-0
[ 1615s] Checking for unpackaged file(s): /usr/lib/rpm/check-files /home/abuild/rpmbuild/BUILDROOT/rpi4-linux-kernel-6.12.80-0.arm
[ 1619s] Wrote: /home/abuild/rpmbuild/SRPMS/rpi4-linux-kernel-6.12.80-0.src.rpm
[ 1626s] Wrote: /home/abuild/rpmbuild/RPMS/armv7l/rpi4-linux-kernel-debugsource-6.12.80-0.armv7l.rpm
[ 1631s] Wrote: /home/abuild/rpmbuild/RPMS/armv7l/arm-rpi4-linux-kernel-6.12.80-0.armv7l.rpm
[ 1636s] Wrote: /home/abuild/rpmbuild/RPMS/armv7l/arm-rpi4-rt-linux-kernel-6.12.80-0.armv7l.rpm
[ 1637s] Wrote: /home/abuild/rpmbuild/RPMS/armv7l/arm-rpi4-linux-kernel-modules-6.12.80-0.armv7l.rpm
[ 1637s] Wrote: /home/abuild/rpmbuild/RPMS/armv7l/arm-rpi4-rt-linux-kernel-modules-6.12.80-0.armv7l.rpm
[ 1651s] Wrote: /home/abuild/rpmbuild/RPMS/armv7l/arm-rpi4-linux-kernel-devel-6.12.80-0.armv7l.rpm
[ 1665s] Wrote: /home/abuild/rpmbuild/RPMS/armv7l/arm-rpi4-rt-linux-kernel-devel-6.12.80-0.armv7l.rpm
[ 1666s] Wrote: /home/abuild/rpmbuild/RPMS/armv7l/arm-rpi4-linux-kernel-btf-devel-6.12.80-0.armv7l.rpm
[ 1668s] Wrote: /home/abuild/rpmbuild/RPMS/armv7l/arm-rpi4-linux-kernel-headers-6.12.80-0.armv7l.rpm
[ 1669s] Wrote: /home/abuild/rpmbuild/RPMS/armv7l/linux-kernel-perf-6.12.80-0.armv7l.rpm
[ 1669s] Wrote: /home/abuild/rpmbuild/RPMS/armv7l/linux-kernel-bpftool-6.12.80-0.armv7l.rpm
[ 1679s] Wrote: /home/abuild/rpmbuild/RPMS/armv7l/arm-rpi4-linux-kernel-devel-debuginfo-6.12.80-0.armv7l.rpm
[ 1689s] Wrote: /home/abuild/rpmbuild/RPMS/armv7l/arm-rpi4-rt-linux-kernel-devel-debuginfo-6.12.80-0.armv7l.rpm
[ 1689s] Wrote: /home/abuild/rpmbuild/RPMS/armv7l/linux-kernel-perf-debuginfo-6.12.80-0.armv7l.rpm
[ 1689s] Wrote: /home/abuild/rpmbuild/RPMS/armv7l/linux-kernel-bpftool-debuginfo-6.12.80-0.armv7l.rpm
[ 1689s] Executing(%clean): /bin/sh -e /var/tmp/rpm-tmp.q87Dxg
[ 1689s] + umask 022
[ 1689s] + cd /home/abuild/rpmbuild/BUILD
[ 1689s] + /bin/rm -rf /home/abuild/rpmbuild/BUILDROOT/rpi4-linux-kernel-6.12.80-0.arm
[ 1690s] + cd rpi4-linux-kernel-6.12.80
[ 1690s] + rm -rf /home/abuild/rpmbuild/BUILDROOT/rpi4-linux-kernel-6.12.80-0.arm
[ 1690s] + exit 0
[ 1690s] ... checking for files with abuild user/group
[ 1692s]
[ 1692s] linhao-linux finished "build linux-rpi.spec" at Wed Oct 28 04:30:30 UTC 2026.
[ 1692s]
info: finished building rpi4-linux-kernel
info: updating local repo
info: *** Build Status Summary ***
=== Total succeeded built packages: (1) ===
info: generated html format report:
     /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-RPI4-PMUV3/local/repos/tizen_unified_standard/armv7l/index.html
info: generated RPM packages can be found from local repo:
     /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-RPI4-PMUV3/local/repos/tizen_unified_standard/armv7l/RPMS
info: generated source RPM packages can be found from local repo:
     /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-RPI4-PMUV3/local/repos/tizen_unified_standard/armv7l/SRPMS
info: build logs can be found in:
     /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-RPI4-PMUV3/local/repos/tizen_unified_standard/armv7l/logs
info: build roots located in:
     /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-RPI4-PMUV3/local/BUILD-ROOTS/scratch.armv7l.*
```

日志宣称写出 15 个二进制 RPM 和 1 个 SRPM，清单就在上面的 Wrote 行中。未逐文件核查实存、SHA-256、RPM 内容或最终配置，不能将此作为安装验收通过。

## 5. 尚未执行的第二段

- 尚未从普通/RT devel RPM 提取最终配置；CONFIG_ARM_PMUV3、CONFIG_HW_PERF_EVENTS 的实际值以及配置差异均待核对。
- 01 文档原来由“没有直接改 RT 配置”推断“RT 没有 PMUv3”过强，现已更正为待验证。用户指出 RT 可能由普通 defconfig 叠加 rt.config 生成，必须用实际 RT RPM 确认。
- 尚未核对本次实际 clang 命令、LLVM=1 行号或用 GBS root 工具读取新 ELF 的 .comment。
- 未生成 `02_pmuv3_install.md`；没有给出未经产物核验的安装、重启或回退命令。

下一步等待用户指示是否允许诊断收尾标记缺失，以及在什么验收依据下进入产物核查。已完成的构建日志和产物目录保留，不自动重跑或清理。
