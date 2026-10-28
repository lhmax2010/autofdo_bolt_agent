# RPi4 PMUv3 构建结果与替代证据验收

更新：2026-10-28（Asia/Shanghai）。**构建验收通过**：depanneur success 记录、HTML 成功状态、15 个二进制 RPM + 1 个 SRPM 的实存/时间/哈希/日志逐项对应，三项条件全部满足。普通版最终配置与同镜像基线 5,649 项对比，唯一变化为 ARM_PMUV3=n→y；RT 仍为 n。安装说明见 [02_pmuv3_install.md](02_pmuv3_install.md)。

**GBS 真实退出码未取得，验收依据是用户授权的上述替代证据。** 原 status 不改，不补 ALL-END，不把日志推断为 GBS_EXIT=0。本轮没有运行构建、修改 spec/GBS 配置或连接开发板；包装脚本仅静态修复。编译器命令的原日志证据有一项限制，见第 8 节。

以下第 1–4 节保留此前异常停止记录，描述的是当时状态；后文为最新授权下的验收。

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

文件不存在，无法给出大小、修改时间或末尾 50 行；不是无读权限，没有提权。当时没有继续寻找或读取移走后的日志；本轮已按新授权核查 success 日志。

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

日志宣称写出 15 个二进制 RPM 和 1 个 SRPM，清单就在上面的 Wrote 行中。当时尚未逐文件核查；本轮核验结果见后文。

## 5. 替代验收命令与 depanneur 证据

路径均相对 WORKDIR。完整机器可读清单：`temp/pmuv3-verify/acceptance.json`（不提交）；关键内容完整转录于本报告。读取命令：

```sh
export TMPDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/tmp
cd /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent
find temp/GBS-ROOT-RPI4-PMUV3/local/repos/tizen_unified_standard/armv7l/logs -maxdepth 3 -printf '%y %p\n'
stat temp/GBS-ROOT-RPI4-PMUV3/local/repos/tizen_unified_standard/armv7l/logs/success/rpi4-linux-kernel-6.12.80-0/log.txt
tail -n 30 temp/GBS-ROOT-RPI4-PMUV3/local/repos/tizen_unified_standard/armv7l/logs/success/rpi4-linux-kernel-6.12.80-0/log.txt
cat temp/GBS-ROOT-RPI4-PMUV3/local/repos/tizen_unified_standard/armv7l/index.html
nice -n 19 ionice -c3 find temp/GBS-ROOT-RPI4-PMUV3/local/repos/tizen_unified_standard/armv7l/RPMS temp/GBS-ROOT-RPI4-PMUV3/local/repos/tizen_unified_standard/armv7l/SRPMS -type f -exec stat --format='%n %s %y' {} \; -exec sha256sum {} \;
```

目录结构（`index.html` 实际位于 logs 的父目录）：

```text
logs/
├── fail/                         # 空，没有失败包
└── success/
    └── rpi4-linux-kernel-6.12.80-0/
        └── log.txt
```

成功日志大小 **972595 bytes**，修改时间 **2026-10-28T12:30:30.119019+08:00**。最后 30 行（仅去除行尾空白）：

```text
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
```

HTML 本次包状态行与汇总（仅去除行尾空白）：

```html
<html>

<head>
<title>GBS Build Report</title>
<style>
.failed { color: red }
.succeeded { color: green }
table {
    border-collapse:collapse;
    margin-bottom: 1em;
}

th { background-color: #F3F3F3 }
td, th {
    border: 1px solid grey;
    padding: 3px
}

table.middle th { text-align: left }

</style>

</head>

<body>


<h1 align="center" >GBS Local Full Build Report</h1>

<p><B>Profile:</B> tizen_unified_standard</p>
<p><B>Arch:</B> armv7l</p>
<p><B>Start Time:</B> 2026-10-28 11:56 +0800
</p>
<p><B>GBS Version:</B> 2.1.0
</p>

<h3>Build Status Summary</h3>

<table class = middle>
    <tr>
        <th>Total Packages</th>
        <th>succeeded Packages</th>
        <th>Export Error Packages</th>
        <th>Expansion Error Packages</th>
        <th>Build Error Packages</th>
    </tr>
    <tr>
        <td>1</td>
        <td>1</td>
        <td>0</td>
        <td>0</td>
        <td>0</td>
    </tr>
</table>







<h3>Build Statis Details</h3>
<table class = middle>
    <thead>
        <tr>
            <th>Package Name</th>
            <th>Package Path</th>
            <th>Build Status</th>
        </tr>
    </thead>
    <tbody>

          <tr>
            <td>rpi4-linux-kernel</td>
            <td>/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/linux-rpi-pmuv3</td>

                <td><a href=logs/success/rpi4-linux-kernel-6.12.80-0/log.txt class = succeeded> Succeeded </a> </td>

          </tr>

    </tbody>
</table>
</body>

</html>

```

## 6. 全部构建产物与时间窗口

以下每行都与外层日志的 `Wrote:` basename 一一对应；无缺失、无额外 RPM。前 15 个二进制位于 `temp/GBS-ROOT-RPI4-PMUV3/local/repos/tizen_unified_standard/armv7l/RPMS/`，源 RPM 位于同级 `SRPMS/`。窗口采用北京时间 **2026-10-28 11:56:53 至 12:31:00**，全部通过。时间不是哈希替代物；两者都已实测。重新读取包头和解包成功进一步核对内容。

| 文件 | 大小 bytes | mtime (+08:00) | SHA-256 | 日志匹配/窗口 |
|---|---:|---|---|---|
| arm-rpi4-linux-kernel-6.12.80-0.armv7l.rpm | 17606876 | 2026-10-28T12:29:29.601016+08:00 | `832a0241990bab9162cfd9455efc687215af4222011eeb8cf64ed8671e3af18c` | 通过/通过 |
| arm-rpi4-linux-kernel-btf-devel-6.12.80-0.armv7l.rpm | 610552 | 2026-10-28T12:30:04.552018+08:00 | `a5bad300c0128e1c9a10903a01ac963974ece70f22a3949184c144ebe88c08c9` | 通过/通过 |
| arm-rpi4-linux-kernel-devel-6.12.80-0.armv7l.rpm | 115483272 | 2026-10-28T12:29:49.601017+08:00 | `89f6c1128d24a2c852b4c2e605e58f6755903432ec031a112413a486cc272429` | 通过/通过 |
| arm-rpi4-linux-kernel-devel-debuginfo-6.12.80-0.armv7l.rpm | 75879656 | 2026-10-28T12:30:17.227018+08:00 | `b796849aa0e70e934d47e36075083587b47c61caf1476a70eac138877294b7e0` | 通过/通过 |
| arm-rpi4-linux-kernel-headers-6.12.80-0.armv7l.rpm | 2048912 | 2026-10-28T12:30:06.445018+08:00 | `07bf8bfd7b1dda6da5112b1f3a9aa572ea2a5846eae44b7fc4b60cc412124c64` | 通过/通过 |
| arm-rpi4-linux-kernel-modules-6.12.80-0.armv7l.rpm | 728000 | 2026-10-28T12:29:35.472017+08:00 | `c08a11d4f624097a3619e31d4cb4dc6fa23965441ba66307e440cd01a76057f2` | 通过/通过 |
| arm-rpi4-rt-linux-kernel-6.12.80-0.armv7l.rpm | 17689708 | 2026-10-28T12:29:34.984017+08:00 | `ef1895912bce3eb149a142971a274f8b32b96ab04555c2a02a56b888ec4b6292` | 通过/通过 |
| arm-rpi4-rt-linux-kernel-devel-6.12.80-0.armv7l.rpm | 112178932 | 2026-10-28T12:30:03.948018+08:00 | `1f6dc364d759c358a2c0f52943f816771b409a63857b2031da7727f1cf875f03` | 通过/通过 |
| arm-rpi4-rt-linux-kernel-devel-debuginfo-6.12.80-0.armv7l.rpm | 75477460 | 2026-10-28T12:30:27.023019+08:00 | `8b77c710b425ee844781d674076673c71222ca50690f166bd213823ec691a914` | 通过/通过 |
| arm-rpi4-rt-linux-kernel-modules-6.12.80-0.armv7l.rpm | 728680 | 2026-10-28T12:29:35.956017+08:00 | `5bf6810ba98a0ae28bee5480e878bca62636f8b6f15148bc93a736bfbcce4a48` | 通过/通过 |
| linux-kernel-bpftool-6.12.80-0.armv7l.rpm | 199784 | 2026-10-28T12:30:07.148018+08:00 | `be94422c73df3841bde67b1e8c8cc332485d8162f409d967dbd03e4340fe30d3` | 通过/通过 |
| linux-kernel-bpftool-debuginfo-6.12.80-0.armv7l.rpm | 197372 | 2026-10-28T12:30:27.280019+08:00 | `4a8c182eb8edbcdc837da17de9e473e1b42012c0cbd88eeb5606a3a386c13a26` | 通过/通过 |
| linux-kernel-perf-6.12.80-0.armv7l.rpm | 1116144 | 2026-10-28T12:30:07.027018+08:00 | `b5ada7e90cb32b924b537ce926cd75071b49ab6a1736be3cb194ca792f9b5afc` | 通过/通过 |
| linux-kernel-perf-debuginfo-6.12.80-0.armv7l.rpm | 195616 | 2026-10-28T12:30:27.165019+08:00 | `2b39882a0e9281bfd89243eba234e5fbeaa59a49ca1a9969140c462ba32e099f` | 通过/通过 |
| rpi4-linux-kernel-debugsource-6.12.80-0.armv7l.rpm | 18700932 | 2026-10-28T12:29:24.178016+08:00 | `663beb8572484996efa12e44eadafb224597165725b557a0723925069c2c1297` | 通过/通过 |
| rpi4-linux-kernel-6.12.80-0.src.rpm | 156311221 | 2026-10-28T12:29:17.279016+08:00 | `3851f832497708bf8659b3f4693123cc1cbdd164388f1c081be13ec6be2e30d8` | 通过/通过 |

正常输出文件全部 uid=1000、mode=0644；`find local/repos -type f -name '*.rpm'` 返回 0、16 行、无 stderr。修复后的扫描只读取目录/文件元数据，不读取 RPM 内容，root 属主本身不妨碍扫描；前提是父目录可读且可遍历。本次未声称实测了不可读的 root 私有目录；若以后权限拒绝，pipefail 会使 RPM_LIST_EXIT 非零并判 FAILED，不 sudo 补救。构建根中的 readelf 等文件实际为 root 属主且可执行，已成功读取产物（第 8 节）。

## 7. 普通版、RT 和镜像基线配置

解包使用本机 `rpm2cpio 包 | cpio -id --quiet ./boot/kernel/devel/kernel-devel-变体/.config`，工作目录分别在 `temp/pmuv3-verify/arm-rpi4/` 与 `arm-rpi4-rt/`；两级退出码均为 0。本机工具仅解容器，不分析指令集。

| 证据文件:行号 | 原文 |
|---|---|
| temp/pmuv3-verify/arm-rpi4/boot/kernel/devel/kernel-devel-arm-rpi4/.config:5 | CONFIG_CC_VERSION_TEXT="clang version 22.1.8" |
| 同上:118 | # CONFIG_PREEMPT_RT is not set |
| 同上:500 | CONFIG_HW_PERF_EVENTS=y |
| 同上:5957 | CONFIG_ARM_PMUV3=y |
| temp/pmuv3-verify/arm-rpi4-rt/boot/kernel/devel/kernel-devel-arm-rpi4-rt/.config:5 | CONFIG_CC_VERSION_TEXT="clang version 22.1.8" |
| 同上:118 | CONFIG_PREEMPT_RT=y |
| 同上:505 | CONFIG_HW_PERF_EVENTS=y |
| 同上:5996 | # CONFIG_ARM_PMUV3 is not set |

RT 核验结论：**没有启用 PMUv3**。这是 RPM 实证，不再根据“没有改 RT 输入”推断。精确源码 `temp/linux-rpi-pmuv3/packaging/linux-rpi.spec:5、:198` 指定独立 `tizen_bcm2711_rt_defconfig`，成功日志第 9376 行实际执行该目标；该输入文件 `arch/arm/configs/tizen_bcm2711_rt_defconfig:11` 为 CONFIG_PREEMPT_RT=y，未包含 ARM_PMUV3。此前“这次会从已修改普通 defconfig 叠加 rt.config”的说法不符合本次实际命令和产物；生成 RT defconfig 的历史流程不等于本次构建流程。

基线取自镜像固定 Unified 快照的 `arm-rpi4-linux-kernel-devel-6.12.80-0.armv7l.rpm`，VCS 为 `21645b17c0d913e2ba7e10fbc9c993d286b3f57d`。URL 与哈希（下载后用快照 primary 元数据核对 SHA-256，通过）：

- [arm-rpi4-linux-kernel](https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261022.054557/repos/standard/packages/armv7l/arm-rpi4-linux-kernel-6.12.80-0.armv7l.rpm)：`c0282c7388fcaf020f6ec2bdee78191a22fbb2f4a1903378ca74bf8739f4da98`。
- [arm-rpi4-linux-kernel-devel](https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261022.054557/repos/standard/packages/armv7l/arm-rpi4-linux-kernel-devel-6.12.80-0.armv7l.rpm)：`ee3d526772b025c5e82eecfd519d6dd6160458b7251fd03e3ba4e1affc7e8f4a`。
- [arm-rpi4-linux-kernel-modules](https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261022.054557/repos/standard/packages/armv7l/arm-rpi4-linux-kernel-modules-6.12.80-0.armv7l.rpm)：`8234b9bea41af489d72777896ec7b6b8e0ec20312b178156242d8cc0fceae560`。

其中普通 kernel/modules 两个原包也已保留在 `temp/pmuv3-verify/baseline/` 供回退；不会推送到 GitHub。基线配置：`temp/pmuv3-verify/baseline/config/boot/kernel/devel/kernel-devel-arm-rpi4/.config`。逐个比较所有 `CONFIG_*=值` 和 `# CONFIG_* is not set`，双方均 **5,649** 项，无缺失项，唯一差异：

```diff
# 两个配置均在第 5957 行；HW_PERF_EVENTS 第 500 行均为 y
-# CONFIG_ARM_PMUV3 is not set
+CONFIG_ARM_PMUV3=y
```

无额外自动依赖变化。比较输出：`temp/pmuv3-verify/config_diff.json`。这验证镜像仓库基线的完整配置；不声称重新读取了运行中板上的配置。

## 8. clang、链接器与内核身份

成功日志相对路径：`temp/GBS-ROOT-RPI4-PMUV3/local/repos/tizen_unified_standard/armv7l/logs/success/rpi4-linux-kernel-6.12.80-0/log.txt`。

- `1924`：`[  258s] + export LLVM=1`
- `1925`：`[  258s] + LLVM=1`
- `9376`：`[  641s] + make O=build/arm-rpi4-rt tizen_bcm2711_rt_defconfig -j10`
- `14211`：`[  956s] + export LLVM=1`

**日志完整 clang 命令行：未取得。** 本次 Kbuild 默认 quiet 输出 `CC init/main.o`，对日志搜索 `clang.*(-c |--target| -o )` 无匹配，不能伪造一条带日志行号的编译命令。补充采用本次构建实际保存的 Kbuild 命令记录：

`temp/GBS-ROOT-RPI4-PMUV3/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/build/arm-rpi4/init/.main.o.cmd:1`：

```text
savedcmd_init/main.o := clang -Wp,-MMD,init/.main.o.d -nostdinc -I/home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/arch/arm/include -I./arch/arm/include/generated -I/home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/include -I./include -I/home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/arch/arm/include/uapi -I./arch/arm/include/generated/uapi -I/home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/include/uapi -I./include/generated/uapi -include /home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/include/linux/compiler-version.h -include /home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/include/linux/kconfig.h -include /home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/include/linux/compiler_types.h -D__KERNEL__ --target=arm-linux-gnueabi -fintegrated-as -Werror=unknown-warning-option -Werror=ignored-optimization-argument -Werror=option-ignored -Werror=unused-command-line-argument -mlittle-endian -D__LINUX_ARM_ARCH__=7 -fmacro-prefix-map=/home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/= -std=gnu11 -fshort-wchar -funsigned-char -fno-common -fno-PIE -fno-strict-aliasing -fno-dwarf2-cfi-asm -mtp=cp15 -mabi=aapcs-linux -mfpu=vfp -funwind-tables -meabi gnu -Wa,-W -march=armv7-a -msoft-float -Uarm -fno-delete-null-pointer-checks -O2 -fstack-protector-strong -ftrivial-auto-var-init=zero -pg -fstrict-flex-arrays=3 -fno-strict-overflow -fno-stack-check -fno-builtin-wcslen -fno-builtin-wcslen -Wall -Wextra -Wundef -Werror=implicit-function-declaration -Werror=implicit-int -Werror=return-type -Werror=strict-prototypes -Wno-format-security -Wno-trigraphs -Wno-frame-address -Wno-address-of-packed-member -Wmissing-declarations -Wmissing-prototypes -Wframe-larger-than=1024 -Wno-gnu -Wno-format-overflow-non-kprintf -Wno-format-truncation-non-kprintf -Wno-default-const-init-unsafe -Wvla -Wno-pointer-sign -Wcast-function-type -Wno-unterminated-string-initialization -Wimplicit-fallthrough -Werror=date-time -Werror=incompatible-pointer-types -Wenum-conversion -Wunused -Wno-unused-but-set-variable -Wno-unused-const-variable -Wno-format-overflow -Wno-override-init -Wno-pointer-to-enum-cast -Wno-tautological-constant-out-of-range-compare -Wno-unaligned-access -Wno-enum-compare-conditional -Wno-missing-field-initializers -Wno-type-limits -Wno-shift-negative-value -Wno-enum-enum-conversion -Wno-sign-compare -Wno-unused-parameter -g -gdwarf-4 -fno-function-sections -fno-data-sections -I/home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/init -Iinit    -DKBUILD_MODFILE='"init/main"' -DKBUILD_BASENAME='"main"' -DKBUILD_MODNAME='"main"' -D__KBUILD_MODNAME=kmod_main -c -o init/main.o /home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/init/main.c
```

用 **GBS root 内平台 readelf**（ARM ELF，root 所有）在本机 qemu-arm-static 下读取新 vmlinux，不使用主机 readelf 代替，不 chroot、不 sudo：

```text
COMMAND: qemu-arm-static -L temp/GBS-ROOT-RPI4-PMUV3/local/BUILD-ROOTS/scratch.armv7l.0 temp/GBS-ROOT-RPI4-PMUV3/local/BUILD-ROOTS/scratch.armv7l.0/usr/bin/readelf -p .comment temp/GBS-ROOT-RPI4-PMUV3/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/build/arm-rpi4/vmlinux
EXIT: 0

String dump of section '.comment':
  [     1]  clang version 22.1.8
  [    16]  Linker: LLD 22.1.8

```

内核 .comment 确认 clang 22.1.8、LLD 22.1.8。最终配置、保存的实际命令、ELF 三者一致；日志命令缺口仍如上保留。原 vmlinux SHA-256：`a54e68a3acf550e361dc2bd41df90358ebbd4fa50ad1b507a2a7e023779624ad`。

本次普通版身份（均在上述 build/arm-rpi4 目录）：

- `include/generated/utsrelease.h:1`：`6.12.80-arm-rpi4-v7l`。
- `include/generated/utsversion.h:1`：`#1 SMP Wed Oct 28 04:12:26 UTC 2026`（不是构建结束时间）。
- `include/generated/compile.h:4`：`clang version 22.1.8, LLD 22.1.8`。
- 从普通 kernel RPM 提取的 `temp/pmuv3-verify/normal-boot/boot/zImage`：SHA-256 `a1cf2077f2053f2d779b39a0d9d7482bc636ecb38d5c07caf305fc0889207cd6`。

## 9. ALL-END 缺失诊断与静态修复

status 已有 PHASE BUILDING、GBS_PID 98603，说明状态写入者至少活到 GBS 启动之后。随后两个目标 PID 消失；GBS 的成功日志/RPM 保留，包装状态停在 RUNNING。旧脚本只给 GBS 使用 setsid，收尾子 shell 仍留在调用者的会话中，因而存在“GBS 继续运行而收尾者先被回收”的生命周期缺口。

按用户指定将本次异常按 **包装脚本收尾进程被提前回收** 处理。**具体由命令执行环境在命令返回后回收后台进程/进程组，仍属推断**：现有工具说明没有给出这种清理保证，已保存 ps 没有死亡原因/信号证据，也无存活期的 PGID/SID 记录可反证其他原因。没有做影响其他进程的实验，不能声称已证实是某一 SIGTERM/SIGKILL 或回收机制。

静态修复 `scripts/build_pmuv3_kernel.sh`：整个 worker 由 `setsid --fork /bin/bash ... --worker` 启动，传递 fd 9 锁、重定向三个标准流；worker 写 PID 确认后前台交接；GBS 使用 `setsid --wait`，worker 的 wait 保留真实退出码，即使 setsid 内部 fork 也不误把启动器退出当作构建结束。信号和 EXIT trap 仍负责原子写状态，扫描错误写 FAILED。没有修改现有 build_pmuv3.status/日志，没有重跑。

`bash -n scripts/build_pmuv3_kernel.sh` 返回 0。**修复未经运行验证，下次构建时验证**。setsid 解决会话依附问题，不能承诺抵抗执行器按 cgroup/全子孙清理、SIGKILL、断电或磁盘不可写。

## 10. 交付边界

安装/回退文档只允许普通 kernel+modules；RT、不相关工具、devel/debug 包均不安装。普通 RPM 没有 %post/%preun；config.txt 是直接覆盖的 payload，详细副作用、启动链与备份范围见 02 文档。所有板上步骤由用户运行，本轮未访问板。

原 src/linux-rpi 与 PMUv3 worktree 检出文件保持干净；config/ 两份原配置和固定快照配置未改。无新已知工作区外写入；历史 `/tmp/sdb.log` 例外仍见 STATUS 与 probe/evidence/07_boundary.txt。没有声称进行完整系统调用审计。
