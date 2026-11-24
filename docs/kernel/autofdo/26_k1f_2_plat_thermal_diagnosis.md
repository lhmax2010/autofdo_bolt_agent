# K1f-2 PLAT 温度排查

**本次空闲温度回到历史范围，未复现 67.7–72.5 °C 的热态。** 30 分钟 CPU 温度为 **53.556–55.991 °C**，中位 **55.017 °C**。本轮观测不能唯一归因上次升温。

## 采集与板子状态

2026-11-24 美国太平洋时间 `01:56:12.197` 至 `02:26:12.197`。板载 uptime 覆盖 1800.07 s，每 10 秒取样，含首尾 **181 点**，生成 **180 个区间**。Raspberry Pi 4 Model B Rev 1.5，串号 `100000004694d889`，PLAT `6.12.80-arm-rpi4-v7l armv7l`，build-id `395733b9c917cb98309b39cc3ec379c03ac36b3f`。boot ID 始终为 `656d98ce-abdc-47e2-9f04-deffc0979c68`，U-Boot、tryboot=0、原 cmdline。仅用临时 SDB root 读取进程与 debugfs，结束 root off 且 UID 5001。共享 SDB 监听 PID 276783 前后一致。前置能力探索单独保留，正式统计只用连续 30 分钟。 [30 分钟原始计数、读数与前五进程](evidence/26-k1f-2-thermal/measurements.jsonl.gz) · [结束身份](evidence/26-k1f-2-thermal/identity-after.json) · [身份与数据源](evidence/26-k1f-2-thermal/board-methods.txt)

全板忙时由相邻 `/proc/stat` 的前八项差分，扣除 idle 与 iowait，再除以四核总时长。`/proc/<pid>/stat` 按 PID 与 starttime 对齐，utime+stime 以 100 ticks/s 换算，进程 100% 对应一个 CPU 核。只对两端可识别的进程算差分。只读采样自身的 SDB 流量会计入观测负载。仓库原件保留计算所需的全部原始计数，主机原始 stdout 另有全字段 SHA。 [统计数据](evidence/26-k1f-2-thermal/summary.json) · [证据索引](evidence/26-k1f-2-thermal/index.json)

## 温度、频率与负载

CPU 首末点 **55.504 / 55.504 °C**，p90 **55.504 °C**。同一 CPU thermal 驱动的 hwmon 入口范围 **53.556–55.991 °C**，中位 55.017 °C。全板忙时中位 **2.462%**，p90 **2.656%**，最高 **2.829%**，180 个区间中 180 个低于 2.91%。1 分钟 loadavg 中位 0.14，范围 0.00–0.91。

| 采集区间 | CPU 温度 min / 中位 / max（°C） | 全板忙时中位 / p90 / 最大 |
| --- | ---: | ---: |
| 第 1 个 10 分钟 | 54.043 / 55.017 / 55.991 | 2.410 / 2.613 / 2.700% |
| 第 2 个 10 分钟 | 53.556 / 55.017 / 55.991 | 2.487 / 2.659 / 2.829% |
| 第 3 个 10 分钟 | 54.043 / 55.017 / 55.504 | 2.504 / 2.703 / 2.826% |

四核共用 policy0，配置最小 600 MHz、最大 1,500 MHz。逐核文件顺序读取，频率切换可落在读取之间。

| CPU | scaling_cur_freq MHz（读数次数） | cpuinfo_cur_freq MHz（读数次数） | governor |
| --- | --- | --- | --- |
| 0 | 900 (3) / 1000 (5) / 1100 (127) / 1200 (42) / 1300 (1) / 1400 (1) / 1500 (2) | 800 (2) / 900 (6) / 1000 (9) / 1100 (60) / 1200 (84) / 1300 (16) / 1400 (3) / 1500 (1) | schedutil |
| 1 | 900 (3) / 1000 (4) / 1100 (120) / 1200 (50) / 1300 (2) / 1400 (2) | 800 (4) / 900 (7) / 1000 (15) / 1100 (59) / 1200 (74) / 1300 (18) / 1400 (4) | schedutil |
| 2 | 900 (4) / 1000 (3) / 1100 (107) / 1200 (60) / 1300 (3) / 1400 (2) / 1500 (2) | 800 (4) / 900 (7) / 1000 (23) / 1100 (61) / 1200 (72) / 1300 (11) / 1400 (2) / 1500 (1) | schedutil |
| 3 | 900 (4) / 1000 (5) / 1100 (93) / 1200 (69) / 1300 (6) / 1400 (2) / 1500 (2) | 800 (4) / 900 (9) / 1000 (27) / 1100 (66) / 1200 (63) / 1300 (10) / 1400 (2) | schedutil |

### 进程

下表按入榜期间累计 ticks 排序。`sdbd` 也处理本轮每 10 秒的读取。`runner` 是进程计数中的 `comm`，原始数据保留 PID。显示、合成和媒体分组以进程 `comm` 匹配，统计 CPU 时间。

| 进程 | 前五名次数 | 入榜区间平均 / 最高 CPU% |
| --- | ---: | ---: |
| `runner` | 180 | 2.034% / 2.700% |
| `sdbd` | 180 | 0.717% / 1.301% |
| `sugov:0` | 180 | 0.363% / 0.502% |
| `enlightenment` | 179 | 0.355% / 0.501% |
| `dlog_logger` | 154 | 0.221% / 0.300% |
| `systemd` | 21 | 0.167% / 0.300% |
| `buxton2d` | 3 | 0.200% / 0.200% |

| 进程组 | 区间 CPU% 中位 / p90 / 最大 |
| --- | ---: |
| enlightenment/compositor | 0.396 / 0.400 / 0.501% |
| graphics workers | 0.000 / 0.100 / 0.200% |
| media workers/userspace | 0.000 / 0.000 / 0.000% |
| deviced | 0.000 / 0.100 / 0.200% |
| TV application/services | 2.080 / 2.400 / 2.700% |

## 显示、GPU 与电源

连接器三项的逐点分布如下。deviced.service active/running，PID 442，display-manager.service active/running，PID 539。`GetDisplayCount` 返回 1（181 点），显示索引 0 的 `GetBrightness` 返回 0（181 点），这两个 D-Bus 结果均记录全程。板载 `device_display_get_state` 从 VCONF `memory/pm/state` 读值，实机函数把原值 `1` 映射到正常显示状态。该项补充采集从样点 8 起，**173 个点均为正常显示**，最初 8 个点仍有 DRM、deviced 服务与 D-Bus 读数。 [Tizen 显示 API](https://docs.stg.tizen.org/application/native/api/common/9.0/group__CAPI__SYSTEM__DEVICE__DISPLAY__MODULE.html) · [板载 getter 的只读取证](evidence/26-k1f-2-thermal/deviced-get-state.txt)

| DRM 连接器 | status | enabled | DPMS |
| --- | --- | --- | --- |
| card0-HDMI-A-1 | connected (181) | enabled (181) | On (181) |
| card0-HDMI-A-2 | disconnected (181) | disabled (181) | On (181) |
| card0-Writeback-1 | unknown (181) | disabled (181) | On (181) |

`vcgencmd` 未找到，因而它的 `get_throttled`、`measure_temp`、`measure_volts` 读数为 **unknown**。温度用内核 thermal/hwmon。以下为 `/sys/kernel/debug/clk/*/clk_rate` 的替代时钟读数。固件时钟驱动用 `GET_CLOCK_RATE` 获取速率，H.264 用共同 clock framework 的 `h264` 节点。速率与引用计数是时钟状态，无法量化 GPU 或编解码引擎利用率。 [Raspberry Pi 时钟驱动](https://github.com/raspberrypi/linux/blob/rpi-6.12.y/drivers/clk/bcm/clk-raspberrypi.c#L192-L205) · [Raspberry Pi 工具接口](https://www.raspberrypi.com/documentation/computers/os.html#vcgencmd)

| 时钟 | MHz（读数次数） | clk_enable_count（读数次数） |
| --- | --- | --- |
| arm | 600 (26) / 700 (7) / 800 (5) / 900 (3) / 1000 (11) / 1100 (70) / 1200 (31) / 1300 (8) / 1400 (4) / 1500 (16) | 0 (181) |
| core | 500 (181) | 2 (181) |
| v3d | 250 (181) | 1 (181) |
| h264 | 499.999998 (181) | 0 (181) |
| isp | 250 (181) | 0 (181) |
| hevc | 250 (181) | 0 (181) |

`rpi_volt/in0_lcrit_alarm` 读数分布为 **0（181 点）**。该节点仅反映内核驱动最近一次轮询得到的欠压告警位。内核日志也未找到欠压或降频条目，完整固件降频及历史状态仍未知。没有读到板载风扇转速或环境温度。 [Raspberry Pi hwmon 实现](https://github.com/raspberrypi/linux/blob/rpi-6.12.y/drivers/hwmon/raspberrypi-hwmon.c#L28-L86) · [本机热接口](evidence/26-k1f-2-thermal/thermal-interface.txt) · [当前启动日志筛选](evidence/26-k1f-2-thermal/journal-thermal.txt)

## 历史对照与判断

| 参考 | CPU 温度最小 / 中位 / 最大（°C） | 本次中位减参考中位或单点（°C） |
| --- | ---: | ---: |
| K1a HDMI 接入后的 10 分钟空闲，schedutil | 53.556 / 54.530 / 55.504 | +0.487 |
| K1a 60°C 门禁重试前空闲，performance | 58.426 / 59.400 / 59.887 | -4.383 |
| K1d-a PLAT 普通重启 1，schedutil | 54.530 / 55.991 / 58.426 | -0.974 |
| K1d-a PLAT 普通重启 2，schedutil | 54.530 / 55.991 / 58.426 | -0.974 |
| K1d-a PLAT 普通重启 3，schedutil | 54.530 / 55.504 / 56.478 | -0.487 |
| K1f-1e 两个 tryboot 的核对快照 | 两次均为 58.426 | -3.409 |

K1a HDMI 后的连接器和 governor 与本轮一致。K1a 10 分钟温度段的频率范围为 600–1,500 MHz。K1a 无法直接读到 enlightenment 的 PID tick，当时只能用整板值给它上界。K1d-a 三次重启的前五记录中，enlightenment 入榜时的单核 CPU 中位约 0.6%，峰值 0.8–1.0%。本轮按所有区间的直接读数计算，媒体进程包括 `media-server` 与 `pipewire`。K1d-a 稳态整板 p90 为 2.112–2.311%，本轮为 2.656%，采样时 SDB 也在入榜。K1f-1e 两次快照确认了 HDMI 和显示服务，只有瞬时温度。三组历史证据均无可比的逐点 GPU 时钟。 [K1a HDMI](04_k1a_baseline.md) · [K1d-a 安静基线](11_k1d_a_boot_chain.md) · [K1f-1e](24_k1f_1e_shared_modules_and_symbol_order.md) · [历史曲线与进程核算](evidence/26-k1f-2-thermal/historical.json)

K1f-2 热态时，安静门禁区间的整板忙时已低于 2.91%，K-BASE 在 powersave 600 MHz 的冷却窗口仍最低 67.679 °C。同一 PLAT boot ID 在回程快照为 72.549 °C，本轮中位低了 **17.532 °C**。本轮显式记录的 CPU、显示与媒体活动均未显示持续异常，CPU 频率也随 schedutil 变化。因此，持续的 CPU 过载、enlightenment 忙等或卡在低频缺少支持。热态没有同步 GPU 时钟、电压或固件状态，无法排除当时短暂的板上活动。日志索引也未保留 K-BASE 热态的 boot ID。现场观察原文为“都没看到什么变化”，未观察到风扇、摆放、周边热源或画面明显变化。**数据支持这是一次已消退的热态，外部散热条件与板上瞬态均未证实，具体根因未定。** [K1f-2 停止收据](evidence/25-k1f-2/aa-stop-receipt.json) · [现场观察](evidence/26-k1f-2-thermal/onsite-observation.txt) · [留存启动记录](evidence/26-k1f-2-thermal/journal-boots.txt)
