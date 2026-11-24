# K1f-1b PLAT 恢复取证、ARM32 静态核对与启动验证

终态 **STOP**。K-BASE-S 的周末失败未定位到具体启动阶段。该次启动没有现场 HDMI 观察。

[收据索引](evidence/21-k1f-1b/index.json) · [链接区间表](evidence/21-k1f-1b/regions.tsv) · [静态检查门禁](evidence/21-k1f-1b/static-gate.json)

## PLAT 恢复与归档复核

在专用 worktree fetch/rebase 后核对主线含磁盘清理提交 `8ff3613d`。共享服务已在 26099 监听。原 sdb 客户端链接指向已删除的文件，从该共享进程的可执行 inode 提取同 SHA 的客户端至本任务目录。调用前确认共享 PID 276783，拒绝启动或重启服务。

RPi4 现场断电恢复后的 boot ID 为 `50cd0836-3920-48fd-b6f7-f1e1d074c465`，PLAT build-id `395733b9c917cb98309b39cc3ec379c03ac36b3f`，ARMv7l、U-Boot、tryboot=0，cmdline SHA-256 `1a132093c6e7220e981bd54c1a6a7bf780a19927c9787d3c9dcb7149eff106b4`。只读 boot_a 418/418（原文件 413 + 任务文件 5），p6 K-BASE 模块目录 72/72。卸载 boot_a，root off 后复核 UID 5001。

| 归档核对组 | SHA 项数 | 不符 |
| --- | ---: | ---: |
| manifests | 4 | 0 |
| K-BASE | 963 | 0 |
| K-AFDO | 46 | 0 |
| K-BASE-S | 46 | 0 |
| maps | 3 | 0 |
| cleanup_elf | 6 | 0 |
| K-BASE relink kit | 5946 | 0 |
| K-AFDO relink kit | 5946 | 0 |
| K-BASE-S relink kit | 5946 | 0 |

清理报告锚定三个 relink manifest。K-BASE 归档明细来自 K1c 的已锚定 manifest，另两个来自 K1e artifacts 索引。六份原始 ELF 的 SHA 同时对照了清理报告。沿用 K1e 链接 map，并逐个核对其原 SHA。

## K-BASE-S 失败启动取证

周末发出 tryboot 后，首个 TCP 探测仍命中旧系统。TCP 随即断开，后续 49 次探测均未恢复，到 300 秒停止。取证时 journal 有持久目录，`journalctl --list-boots` 只列出三个历史 boot ID 及本次恢复后的 PLAT，最新历史记录属于 K1e。缺少可归属周末失败的 boot ID，所以无该次完整 journal 可导出。

PLAT 下未发现 `/sys/fs/pstore`、systemd pstore 存档或可归属失败的固件日志。设备树的 bootloader 属性只描述本次 PLAT，tryboot 值为 0。用户确认周末未观察屏幕。固件未跳转、内核早期停止、内核后期或用户态网络未就绪，这三种阶段仍无法区分。[Raspberry Pi 的 tryboot 说明](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#fail-safe-os-updates-tryboot)

## ARM32 原始 ELF 与 link map

解析归档 ARM ELF32 的节、符号、A32 mapping symbols 及表项。三个普通版使用同一份预处理 ARM 链接脚本。以 script 符号、System.map 及经 SHA 核对的原始链接 map 交叉验证。区间表列出每个版本的 62 个已配对区间，完整 JSON 记录 182 个候选赋值标记及按链接 map 输入项编号的集合，178 个实际符号与 System.map 一致。编译配置下未产生 hyp-idmap 和独立 exception-text 标记。

| 检查 | K-BASE | K-BASE-S | K-AFDO |
| --- | ---: | ---: | ---: |
| idmap 地址区间 | `0xc0200000..0xc020003c` | `0xc0200000..0xc020003c` | `0xc0200000..0xc020003c` |
| idmap 字节 / 单页 | 60 / 是 | 60 / 是 | 60 / 是 |
| 解码的 .head.text A32 直接分支 | 25 | 25 | 25 |
| 异常表记录 / 逆序 / 非指令目标 | 220 / 0 / 0 | 220 / 0 / 0 | 222 / 0 / 0 |
| unwind 索引条目 / 逆序 / 越界 | 64,120 / 0 / 0 | 64,244 / 0 / 0 | 62,297 / 0 / 0 |
| 无精确同址索引的函数起点 | 1,610 | 1,353 | 1,585 |
| SMP alt 指令目标 / 合法数据目标 | 17,756 / 13 | 17,756 / 13 | 18,047 / 13 |
| PV 地址表有效 A32 补丁点 | 344 | 344 | 354 |
| jump table 验证条目 | 5,276 | 5,276 | 5,406 |
| 链接器 thunk 数 | 312 | 170 | 223 |
| zImage 字节 | 14,965,104 | 15,168,416 | 15,031,504 |

PREL31 解码后的索引单调递增，起点落在可执行节或 CANTUNWIND 区间终止处。索引在此内核上并非与每个 ELF 函数符号一一对应。非内联描述符的 PREL31 落点均在 unwind 表内。异常表采用 ARM 绝对地址项，并检查源指令与 fixup 均为 A32。SMP alt 的 13 个数据目标在三个镜像中模式一致，分别为 `smp_on_up`、`v7wbi_tlb_fns+8` 和 11 个 CPU proc-info flags 槽。PV 表每项都解析到映射符号标明的 A32 指令，符合 ADD/SUB/MOV/MVN/MOVW 补丁编码类别。每份 zImage 的 gzip 负载都和原 ELF 的入口、文本、notes 及关键表逐字节匹配。[Arm EHABI](https://github.com/ARM-software/abi-aa/blob/main/ehabi32/ehabi32.rst#6-index-table-entries)

共享输入项按对象和输入节名关联。两个变体相对基线均为 **0** 项跨既有标记区间或改变输出节归属。K-BASE-S 输入集合完整一致。K-AFDO 出现 893 个新增、23 个消失的带区间输入键，其中 501 项为 .text、391 项为 .ARM.unwind_tab、1 项为 .data，逐项保留在索引定位的完整 JSON。

| 变体 | .init.text 内 thunk 地址 / 字节 | .exit.text 内 thunk 地址 / 字节 |
| --- | --- | --- |
| K-BASE | `0xc2453598` / 4,832 | `0xc2459778` / 160 |
| K-BASE-S | `0xc2453598` / 2,432 | `0xc2458e18` / 288 |
| K-AFDO | `0xc24539b4` / 3,520 | `0xc24596b4` / 48 |

在 MMU 打开前使用的 `__fixup_a_pv_table`，K-BASE 为 `0xc022dd88`，K-BASE-S 为 `0xc0b1f948`，K-AFDO 为 `0xc02d30f4`。三者在 `.head.text` 中的直接分支均正确解析到对应 A32 入口，没有在 head 或 idmap 中发现 thunk。

### 可疑差异排序

1. **K-BASE-S 的文本顺序及内核后期行为。** shuffle 更换大量函数地址，也将物理地址修补函数移远。编码、目标、区间和指令地址表均通过复核。启动路径时序或依赖地址的运行时行为仍需要现场证据。
2. **K-BASE-S 的链接器合成内容。** init/exit thunk 和 unwind 区间有变化，但落点未越界，早期入口无新增 veneer。这些变化可影响后期路径，优先级低于大范围布局变化。
3. **K-BASE-S 的固件载荷差异或一次性异常。** 镜像比 K-BASE 大 203,312 B，格式、负载 SHA、镜像内关键数据和 FAT 读回正常。现场缺少失败时固件或串口日志，无法排除加载或供电异常。


K-AFDO 的剩余风险按优先级为：一、profile 改变启动期代码生成与冷热布局。二、init/exit thunk 和 unwind 合成数据变化。三、固件加载额外 66,400 B。结构检查未发现高风险违规项。实际部署仍取决于 K-BASE 启动门禁。

## 板上启动和回程

### K-BASE

阶段状态 `STOP`。
原始原因 `Stop('boot acceptance failed: k1f1b-kbase')`。
首条确认新 boot ID 的命令在发令后 58.231 s 成功，定向 disconnect 2 次、connect 2 次。
boot ID `fb4bb98f-c355-436b-910b-1922588da79a`，build-id `96766cfcbff8c33d83ca38152ad02f6a02dd44d4`，tryboot=1、U-Boot=False。cmdline 匹配=True，规范化 FDT 匹配=False，模块列表匹配=True，HDMI/网络=True，dlog=True，D-Bus=True。新增严重 dmesg 签名 0 条。
规范化 DTS 的唯一差异为 `/chosen/bootloader/rsts`，参考 `0x20`，本次 `0x1020`，异或 `0x1000`。断电恢复后首次 PLAT 的同一字段为 `0x1000`。Raspberry Pi 文档将 `rsts` 定义为启动时的原始 `PM_RSTS` 值。按现行 FDT 门禁保留差异并停止。K-AFDO 未部署，K-BASE-S 镜像保留。[差异摘要](evidence/21-k1f-1b/fdt-drift.json) · [Raspberry Pi 配置文档](https://www.raspberrypi.com/documentation/computers/config_txt.html)
普通重启回程在 68.444 s 建立会话。PLAT build-id、U-Boot、tryboot=0 和原始 cmdline 通过。root off 后 UID 5001。

### K-AFDO

未进入该次启动。

共享 sdb 服务重启 0 次。本轮完成 K-BASE 启动和 PLAT 回程核对。K-AFDO 冒烟、A/A 和布局测量均未执行。
