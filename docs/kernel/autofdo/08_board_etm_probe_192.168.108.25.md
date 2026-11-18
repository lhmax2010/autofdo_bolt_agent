# 新研究板 ETM / PMU 只读能力探测（192.168.108.25）

探测时间：2026-11-18 07:34起（America/Los_Angeles；原始连接时间15:34:42 UTC）。唯一目标 `192.168.108.25:26101`。首次连接成功，未重试。使用独立工作树 `temp/etm-probe-wt`，基于 origin/main `580dddd`；不在主工作区提交，不读取或处理主工作区的 index.lock，不操作 K0 工作树。

## 结论（三层）

| 层 | 结论 | 证据与限制 |
|---|---|---|
| 硬件 ETM 与 sink | **未知** | 运行中设备树没有匹配的 CoreSight/ETM/PTM/funnel/replicator/TMC/ETB/ETR/TPIU compatible；未暴露不等于硅片没有，不能从 CPU 型号推定实现或连线。没有读硬件寄存器。 |
| 内核驱动 | **当前未暴露可用的 CoreSight 链** | `/sys/bus/coresight/devices/` 不存在，event_source 无 `cs_etm`，没有已识别 sink；配置文件不可得，无法区分未编译、未描述、未探测等原因。PMU 设备则已注册。 |
| perf / OpenCSD 解码链 | **当前不可验收** | PATH及所查常见目录没有可用 perf，版本和 libopencsd 构建选项未知；/opt 部分目录权限不足，不能声称整机绝无该文件。未进行 trace/解码。 |

当前不能据此选择 ETM 采集方案。A2 可列出已暴露 PMU 事件，但事件计数与语义仍未实测，不标为“方案 A2 已验证”。

## 身份与环境

证据：[identity.txt](evidence/08-board-etm-192.168.108.25/identity.txt)、[detail.txt](evidence/08-board-etm-192.168.108.25/detail.txt)；相邻 `.stdout/.stderr` 保存原始字节，`*-command.sh` 为实际发送的只读命令。

| 项目 | 实测 |
|---|---|
| model | Novatek NT72671D |
| CPU | Hardware: Novatek Cortex-A53；4核（processor 0–3）；implementer 0x41、part 0xd03、revision 4 |
| 执行架构 | cpuinfo architecture 7；uname armv7l，**当前内核为32位**，不把芯片名称当作64位内核证据 |
| 内核 | `Linux localhost 6.12.60 #1 SMP PREEMPT Mon Nov 16 20:15:36 UTC 2026 armv7l GNU/Linux` |
| 系统 | Tizen10/TV 10.0.0 (arm) |
| 镜像 BUILD_ID | `T-KSU2EJAKUC-0101-PERF-202611171009`（tizen-release与os-release一致） |
| tizen-build.conf | TZ_BUILD_ARCH=arm；TZ_BUILD_ID=latest；TZ_BUILD_DATE=20261117_015231，不能把latest当固定snapshot |
| 权限 | 前后均uid=5001(owner)，没有root on/off操作 |
| perf_event_paranoid | 2，未改动 |
| `/proc/config.gz` | 不存在，ls退出2；CONFIG_CORESIGHT*、CONFIG_ARM_PMU*、CONFIG_HW_PERF_EVENTS、CONFIG_THUMB2_KERNEL、CONFIG_STRICT_DEVMEM均**未知**，不是判为n |

**身份描述差异：** `/proc/device-tree/compatible` 为 `novatek,nt72671d`、`nvt,ca53`；但四个 `/proc/device-tree/cpus/cpu@{0,1,2,3}/compatible` 均为 `arm,cortex-a7`，`/proc/device-tree/pmu/compatible` 为 `arm,cortex-a7-pmu`，注册 PMU 名为 `armv7_cortex_a7`。原文保留，不擅自修正设备树或认定事件映射一定适配真实CPU。

## CoreSight、设备树与 perf

- CoreSight devices 路径不存在；event_source 只有 `armv7_cortex_a7`、`breakpoint`、`software`、`tracepoint`。
- 全部可读 compatible 文件逐个列出；匹配结果见 [device-tree-matches.json](evidence/08-board-etm-192.168.108.25/device-tree-matches.json)，匹配节点0个。完整节点路径与compatible在detail.txt。
- 初次dmesg宽匹配包含PMUMON及无关文本，不能算ETM证据；第二次限定CoreSight相关词边界后无匹配（grep=1）。这是当前ring buffer结果，不保证覆盖开机日志全历史。
- `command -v perf` 退出1；`perf --version`、`perf version --build-options`、`perf list` 均报 `perf: command not found`。串联shell末尾标记退出0只说明shell执行完成，**不表示这些子命令成功**。
- 额外只读查找 `/bin /sbin /usr/bin /usr/sbin /usr/local/bin /opt` 下名字为perf的文件，无结果；/opt中权限拒绝原文保留。没有安装、下载、推送或编译工具。
- **短trace未执行**：没有cs_etm、可用sink或perf，不满足用户条件；没有强行开启root、sink或驱动。数据量不适用（未生成数据），分支/指令解码结果未验证。没有在板上创建临时文件，故无临时清理对象。

## PMU事件（A2）

PMU路径 `/sys/bus/event_source/devices/armv7_cortex_a7`，type=8，`format/event` 为 `config:0-7`。这是动态PMU type，不等于通用hardware type=0。以下仅是内核暴露的事件别名；没有perf，按用户“不安装/不推工具”要求不做perf stat，也不使用猜测的原始事件号代替计数。

| 请求事件 | 可见性 | 编码/说明 | 几秒计数 |
|---|---|---|---|
| branch-instructions | perf通用事件列表不可得；sysfs无同名别名 | 不能从其他branch事件直接推定等价 | 未执行，perf缺失 |
| branch-misses | perf通用事件列表不可得；sysfs无同名别名 | 有 `br_mis_pred=0x10`，但未证明通用别名映射/实际计数 | 未执行 |
| br_retired | sysfs无此确切别名 | 不以br_immed_retired或pc_write_retired冒充 | 未执行 |
| pc_write_retired | sysfs存在 | event=0x0C | 未执行 |
| inst_retired | sysfs存在 | event=0x08 | 未执行 |
| br_immed_retired | sysfs存在（附加观察） | event=0x0D | 未执行 |
| br_return_retired | sysfs存在（附加观察） | event=0x0E | 未执行 |
| br_pred / br_mis_pred | sysfs存在（附加观察） | 0x12 / 0x10 | 未执行 |
| cpu_cycles | sysfs存在（附加观察） | event=0x11 | 未执行 |

其他全部events、format、PMU链接与type原文在detail.txt。PMUMON日志不等于本任务perf计数验证；没有做任何采样实验。

## 边界、资源与提交

只连接并显式选择.25；没有连接/操作.26、.13或其他设备，没有kill-server、安装、重启、挂载、写系统配置或状态开关。全部板上命令只读，没有显式文件写入。SDB服务自身及设备日志是否产生内部状态写入未做全机审计，不能承诺为零；未创建或删除其他会话文件。

主机命令nice19、ionice-c3、systemd scope 3G/200%，串行；连接前MemAvailable≥4GiB。开始meminfo与报告scope的memory.peak见证据。较早短scope峰值未保留，整任务峰值未知。首条规则读取命令遗漏显式TMPDIR导出，未有意生成临时文件；之后统一指向WORKDIR/temp/tmp，未审计系统命令内部缓存，不隐瞒该缺口。

原始输出、命令、派生可读文本和SHA清单随本报告提交；新证据只属本任务，不修改旧证据、设计、hq或Gerrit。提交前在独立工作树检查其index锁并pull/rebase；主工作区index锁完全不碰。完成后停止。
