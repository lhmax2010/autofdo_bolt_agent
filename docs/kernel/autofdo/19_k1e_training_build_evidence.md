# K1e 训练、K-AFDO 与 K-BASE-S 构建

三会话、两个 GBS 构建、消费与布局验收已完成。0008 已推送并读回。K1f 等待 PM 审核。

RPi4 板上操作仅限已部署的 K-BASE tryboot、采集和 PLAT 回程。本轮无 boot_a 或 p6 写入。 [证据索引](evidence/k1e-index.json)

## 0008 的禁用路径与参数作用域

两个宏均未定义时，`rpmspec -P` 的 ARM32 和 arm64 展开文本分别与 K-BASE 逐字节相同。
带 `kernel_localversion -kbase` 的复查也通过。下表为两个可选宏都缺省时的 SHA-256。

| 架构 | K-BASE 与 0008 共有的展开 SHA-256 | 带 LOCALVERSION 的共有展开 SHA-256 |
| --- | --- | --- |
| armv7l | `ba7acbb2d8946dc322b24d13725cc47aebbcddcbc74850d7b3a198aeb6b61afd` | `3ba0e16947b4a2e3e96579c5ee28cc2766d18dac3d8b9d1681faf39aa5c519ce` |
| aarch64 | `0822f92d8c505193e3da4c0c58c274a0ccbb3041cf5a11e40be2be17f1f16871` | `f6d3c80a17b27d79a560aed8c8466dd5cf67cc845f335eea1fe5b989c4d31605` |

启用 profile 宏时，RPM Source2001 提供文件，构建导出 `CLANG_AUTOFDO_PROFILE` 并打印 SHA。启用链接宏时，Kbuild 只在顶层 vmlinux 链接及其 kallsyms 多遍链接中增加参数。变量作用域探针保留全部原链接选项，模块目标展开值一致。LLD 22.1.8 接受 `--shuffle-sections=.text*=20261120`。
补丁 SHA-256 `ec209a521fd849824537ccc89c3b15b9473783fc4b6133e076f7c883b2a15499`。[0008 补丁](patches/kernel/0008-packaging-opt-in-autofdo-and-link-flags.patch)

## 训练会话与 IP 提取

每会话先核对 build-id、规范化 FDT、cmdline、十个模块及 D-Bus/dlog，再以 2.91% 连续 30 秒开窗。
需要时以 powersave 冷却。每段在 performance 稳定三秒后确认开窗温度 ≤60°C，采集后恢复原 governor。每个 `perf.data` 保存 boot ID、GNU build-id 证据、evlist、各 CPU 计数和 LOST 输出。

| 会话 | K-BASE boot ID | tryboot 重连 | PLAT 重连 | 回程 boot ID | 收据 |
| --- | --- | ---: | ---: | --- | --- |
| 1 | `5b4df82a-ce8d-4376-b664-0d14155124e6` | 52.181 s（automatic） | 62.162 s（automatic） | `90e27435-15b7-4793-bba0-bc865b20c8aa` | 通过 |
| 2 | `eddc86ae-3b0e-4750-ba11-802b737a7c7d` | 190.391 s（host SDB restart） | 62.161 s（automatic） | `c7774ce5-1447-4b40-a9c2-c4d3d0da9eb7` | 通过 |
| 3 | `5c7e480e-1afc-4d49-b2f1-a7e76d519b01` | 190.388 s（host SDB restart） | 52.236 s（automatic） | `6be260d9-4276-4261-8df8-e66a91ee96b6` | 通过 |

三个正常回程均核对 PLAT U-Boot 命令行、build-id `395733b9…`、tryboot=0 和 UID 5001。第三会话回程后保持 PLAT，governor 恢复为 schedutil。

短采的 16,742 条带栈记录经独立折叠与 perf `-G` 投影逐字节一致，含同 IP 的用户态内联帧处理。训练保留 `-g`，转换时使用 `perf script -G`。带栈短采及 K1d-c 冒烟未进入训练合并。录制使用 `perf record -a -e cycles -c 1000003 --buildid-mmap -N -g`。
第二、第三会话直启的 180 秒诊断显示板侧 ping 和 TCP 均可达。确认主机无其他 SDB 客户端后分别重启一次主机服务，恢复目标与先前已连接的端点。
会话 1 的 mmfault 包装脚本在板上成功退出并拉回数据后出现主机解析错误。用板端退出码、完成标记、boot ID、数据 SHA、governor 和 UID 独立复核，保留该段原始数据及错误。
ToS 复用 K1a 归档的 M1 BASE 库（tar SHA `bc351378313b…`）与输入 `280fbd41f877…`，使用同一单线程 GStreamer 解码管线，重复原 60 秒期输入以覆盖 120 秒采样窗。该接触仅用于复现媒体负载。
其余负载固定为 CPU3 上的 pipe（250,000 loops）、32 MiB mmfault（118 次/批）、48 MiB tmpfs 读写和 syscall basic。预登记负载窗为 60/60/60/30/120 秒。表中录制跨度另含 perf 启动与收尾。

## 质量门禁与组成

每段独立用补丁 10 和 K-BASE 原始 vmlinux 转换。策略为 `--ip-weight=sample --ip-aggregation=max --ip-head-samples=none --ip-zero-fill=none --ip-skid=none`。完整命令存于各段。
可用 C 行取保守下界。将 profgen 可用样本数与 LLVM 符号化确认的 C/C 头文件行样本取集合交集下界。歧义样本按 462 个名字和所有原始 DWARF 帧计入上界，分母用 profgen 可用样本数。空 LOST 列表细化为可见丢失记录数 0，工具的丢失完整性仍为 unknown。

| 会话/负载 | 录制跨度 s | 起跑 °C | 内核样本 | CPU3（内核） | CPU3（全记录） | 可用 C 行下界 | 映像外 | IRQ 0/+4 | 汇编 | 未符号化 | C 且非 IRQ | 歧义上界 | LOST 记录 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| session-01/pipe | 63 | 55.017 | 94,201 | 90.01% | 89.92% | 70,997 | 0.00% | 59.81% | 7.15% | 0.00% | 36.81% | 1.30% | 0 |
| session-01/mmfault | 62 | 56.965 | 100,999 | 87.39% | 86.96% | 42,376 | 0.00% | 50.22% | 19.71% | 0.00% | 30.09% | 0.85% | 0 |
| session-01/tmpfs | 63 | 56.478 | 99,686 | 88.10% | 87.26% | 24,976 | 0.00% | 35.84% | 34.35% | 0.00% | 29.91% | 1.55% | 0 |
| session-01/syscall | 32 | 56.478 | 29,902 | 93.81% | 95.36% | 0 | 0.00% | 48.84% | 59.49% | 0.00% | 37.14% | 0.19% | 0 |
| session-01/tos | 123 | 56.965 | 11,139 | 13.87% | 94.03% | 7,296 | 0.00% | 49.34% | 10.13% | 0.00% | 41.02% | 1.05% | 0 |
| session-02/pipe | 63 | 55.991 | 94,415 | 89.98% | 89.84% | 70,993 | 0.00% | 60.30% | 6.95% | 0.00% | 36.38% | 1.42% | 0 |
| session-02/mmfault | 62 | 56.965 | 101,292 | 87.20% | 86.69% | 41,253 | 0.00% | 50.14% | 20.27% | 0.00% | 29.61% | 0.88% | 0 |
| session-02/tmpfs | 62 | 56.965 | 99,630 | 88.21% | 87.34% | 24,554 | 0.00% | 35.92% | 34.66% | 0.00% | 29.51% | 1.50% | 0 |
| session-02/syscall | 32 | 57.452 | 29,009 | 93.65% | 95.37% | 0 | 0.00% | 45.55% | 59.96% | 0.00% | 36.52% | 0.23% | 0 |
| session-02/tos | 124 | 56.965 | 10,819 | 14.75% | 94.22% | 7,085 | 0.00% | 49.67% | 10.20% | 0.00% | 40.62% | 1.01% | 0 |
| session-03/pipe | 63 | 55.504 | 94,290 | 89.89% | 89.77% | 71,058 | 0.00% | 59.69% | 7.01% | 0.00% | 36.95% | 1.35% | 0 |
| session-03/mmfault | 62 | 55.991 | 101,427 | 87.13% | 86.65% | 42,350 | 0.00% | 50.31% | 19.64% | 0.00% | 30.07% | 0.87% | 0 |
| session-03/tmpfs | 62 | 57.452 | 99,704 | 88.10% | 87.28% | 26,171 | 0.00% | 36.29% | 33.82% | 0.00% | 30.02% | 1.57% | 0 |
| session-03/syscall | 32 | 56.478 | 32,521 | 93.91% | 95.13% | 0 | 0.00% | 46.05% | 55.27% | 0.00% | 41.37% | 0.08% | 0 |
| session-03/tos | 124 | 56.478 | 11,419 | 13.81% | 93.91% | 7,496 | 0.00% | 50.15% | 10.32% | 0.00% | 40.17% | 1.05% | 0 |
| 合计 | — | — | 1,010,453 | 86.44% | 90.73% | 436,605 | 0.00% | 48.41% | 23.69% | 0.00% | 32.92% | 1.18% | 0 |

合并输入数 15。按负载合计可用 C 行样本下界为 pipe 213,048，mmfault 125,979，tmpfs 75,701，各自超过 50,000，无需追加会话。syscall 与 ToS 只报告。
门禁判定 `passed`。各段身份 verified，映像外不超过 1%，FS discriminator 为 true。中断窗口按 04 的 A32 方法在同一核心符号内取 0/+4 B 并集，分母含模块样本。模块不扫指令。
有符号但来源语言不明的样本另计，合计 182；上表的未符号化列只计无命名符号的 IP。
通过后按 1:1 权重使用 `llvm-profdata merge --sample --extbinary` 求和。锁定 SHA-256 `d3e2f945ef17530a49d0bfe3bb754ae41cea1e4da7532342a05907d175a96208`。

### 合计前 30 个内核函数

| 函数 | 内核样本 | 占全部内核样本 | 汇编样本 | IRQ 恢复窗口 | 歧义名样本 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `_raw_spin_unlock_irqrestore` | 186,876 | 18.49% | 0 | 186,876 | 0 |
| `__memset / memset / mmioset` | 75,043 | 7.43% | 75,043 | 0 | 0 |
| `arch_local_irq_enable` | 67,925 | 6.72% | 0 | 67,925 | 0 |
| `vector_swi` | 62,368 | 6.17% | 62,368 | 50,776 | 0 |
| `kunmap_local_indexed` | 45,419 | 4.49% | 0 | 0 | 0 |
| `finish_task_switch` | 45,211 | 4.47% | 0 | 44,971 | 0 |
| `__copy_from_user_std` | 42,985 | 4.25% | 42,985 | 0 | 0 |
| `__memcpy / memcpy / mmiocpy` | 42,136 | 4.17% | 42,136 | 0 | 0 |
| `__kmap_local_pfn_prot` | 35,172 | 3.48% | 0 | 0 | 0 |
| `handle_mm_fault` | 24,823 | 2.46% | 0 | 12,838 | 0 |
| `percpu_counter_add_batch` | 21,060 | 2.08% | 0 | 19,616 | 0 |
| `__rseq_handle_notify_resume` | 18,967 | 1.88% | 0 | 0 | 0 |
| `do_page_fault` | 18,844 | 1.86% | 0 | 18,121 | 0 |
| `ktime_get_coarse_real_ts64` | 18,782 | 1.86% | 0 | 0 | 0 |
| `memcg1_commit_charge` | 15,587 | 1.54% | 0 | 14,604 | 0 |
| `try_charge_memcg` | 13,979 | 1.38% | 0 | 12,147 | 0 |
| `shmem_add_to_page_cache` | 10,266 | 1.02% | 0 | 9,417 | 0 |
| `arm_copy_from_user` | 9,534 | 0.94% | 0 | 0 | 0 |
| `filemap_remove_folio` | 9,502 | 0.94% | 0 | 8,492 | 0 |
| `do_work_pending` | 9,408 | 0.93% | 0 | 8,471 | 0 |
| `get_page_from_freelist` | 9,221 | 0.91% | 0 | 0 | 0 |
| `__audit_syscall_entry` | 8,324 | 0.82% | 0 | 0 | 0 |
| `__mem_cgroup_charge` | 8,313 | 0.82% | 0 | 6,072 | 0 |
| `get_mem_cgroup_from_mm` | 6,304 | 0.62% | 0 | 3,647 | 0 |
| `_raw_spin_lock_irqsave` | 6,253 | 0.62% | 0 | 0 | 0 |
| `pipe_write` | 6,000 | 0.59% | 0 | 3,296 | 0 |
| `__audit_syscall_exit` | 5,808 | 0.57% | 0 | 0 | 0 |
| `__percpu_counter_limited_add` | 5,409 | 0.54% | 0 | 5,004 | 0 |
| `migrate_enable` | 5,251 | 0.52% | 0 | 0 | 0 |
| `uncharge_folio` | 4,769 | 0.47% | 0 | 3,418 | 0 |

逐段前 30 和原始 CPU 计数见质量门禁 JSON，由证据索引定位。

## 构建门禁、消费与布局

构建使用 Clang/LLD 22.1.8、固定 Base `20261030.120529`、Unified `20261104.125239`、同一集合 130 RPM、新 buildroot、`-j2`、6G/5G/200%、nice19 和 ionice idle。S0 为 MemAvailable ≥16 GiB、load1 <0.6×可用 CPU、磁盘 ≥50 GiB，并等待其他 GBS/rpmbuild 清空。
K-AFDO 与 K-BASE-S 使用 `LOCALVERSION=-kbase`、`KBUILD_BUILD_TIMESTAMP=Wed Nov 18 14:59:26 UTC 2026`、`abuild`、`linhao-linux` 和构建号 1。

K-AFDO 首次 GBS 尝试退出 1，耗时 303.53 秒。在源码导出后、编译前，GBS 的两层 shell 对时间戳引用处理失败。保持 0008 和 profile 不变，改为 RPM 展开时生成 shell 引号。主机 RPM 与冻结 ARM RPM 均验证了完整时间戳，重试使用新 buildroot。

- K-AFDO GBS 状态 `passed`，退出码 0，墙钟 5915.90 s，cgroup 峰值 5,371,228,160 B。
  3,237 项编译命令通过。唯一编译参数增量为 `-fprofile-sample-use=/home/abuild/rpmbuild/SOURCES/linux-rpi-k1e.prof`，出现在 3,052 条命令中。130 个依赖、版本、.config、14130 项符号 CRC、52 个模块 vermagic 通过。
  ARM32 vmlinux build-id `43ba5d455daec5da17e7521048767cdace012c91`，SHA-256 `feed27508f9223ec8fe25082e4adf1820c04f897ca079328e616304b84760f2e`。vmlinux.a 成员顺序与 K-BASE 一致，归档 16 个 RPM。最终链接 argv 与成员清单见索引。
- K-BASE-S GBS 状态 `passed`，退出码 0，墙钟 4617.83 s，cgroup 峰值 5,372,243,968 B。
  3,237 项编译命令通过。与 K-BASE 的编译命令相同。130 个依赖、版本、.config、14130 项符号 CRC、52 个模块 vermagic 通过。
  ARM32 vmlinux build-id `a78e6ca8956db526ba91d5856369fc1a7f15b5fd`，SHA-256 `3ce89c719b6c348d062b6b65d80f1842593b082adf824bcc2d99ebcbb05fefdc`。vmlinux.a 成员顺序与 K-BASE 一致，归档 16 个 RPM。最终链接 argv 与成员清单见索引。

RPi4 普通目标的 release 为 `6.12.80-arm-rpi4-v7l-kbase`，版本元数据与 K-BASE 一致。随包构建的 RT 目标共用 PM 指定的固定时间戳，历史 K-BASE RT 的时间戳为 15:19:44 UTC。
14/14 个选中对象的 .text SHA 发生变化。20/20 个热 C 函数有正值 AppliedSamples。这些诊断来自所选对象的独立编译重放，覆盖门槛 N=100。

| 函数 | 对象 | AppliedSamples 正值条数 | NumSamples 合计 | 记录和样本覆盖诊断 | 热区 |
| --- | --- | ---: | ---: | --- | --- |
| `finish_task_switch` | `kernel/sched/core.o` | 25 | 135592 | 记录无短缺告警 / 样本无短缺告警 | 否 / 是 / 否 |
| `kunmap_local_indexed` | `mm/highmem.o` | 67 | 133191 | 记录 22/23（95%） / 样本 43894/44649（98%） | 否 / 是 / 否 |
| `__kmap_local_pfn_prot` | `mm/highmem.o` | 66 | 101483 | 记录 20/22（90%） / 样本 33513/33984（98%） | 否 / 是 / 否 |
| `percpu_counter_add_batch` | `lib/percpu_counter.o` | 6 | 60531 | 记录 2/3（66%） / 样本 20177/20275（99%） | 否 / 是 / 否 |
| `ktime_get_coarse_real_ts64` | `kernel/time/timekeeping.o` | 23 | 53860 | 记录 6/9（66%） / 样本 17137/18362（93%） | 否 / 是 / 否 |
| `__rseq_handle_notify_resume` | `kernel/rseq.o` | 146 | 51377 | 记录 46/49（93%） / 样本 17055/17161（99%） | 否 / 是 / 否 |
| `memcg1_commit_charge` | `mm/memcontrol-v1.o` | 8 | 45656 | 记录 2/3（66%） / 样本 15148/15254（99%） | 否 / 是 / 否 |
| `try_charge_memcg` | `mm/memcontrol.o` | 45 | 27088 | 记录 13/15（86%） / 样本 856/13114（6%） | 否 / 是 / 否 |
| `handle_mm_fault` | `mm/memory.o` | 369 | 34818 | 记录 114/119（95%） / 样本 11550/11656（99%） | 否 / 是 / 否 |
| `shmem_add_to_page_cache` | `mm/shmem.o` | 55 | 30254 | 记录 17/18（94%） / 样本 10052/10101（99%） | 否 / 是 / 否 |
| `arm_copy_from_user` | `arch/arm/lib/uaccess_with_memcpy.o` | 20 | 27797 | 记录 6/7（85%） / 样本 8973/9412（95%） | 否 / 是 / 否 |
| `filemap_remove_folio` | `mm/filemap.o` | 42 | 28290 | 记录 14/15（93%） / 样本 9432/9439（99%） | 否 / 是 / 否 |
| `get_page_from_freelist` | `mm/page_alloc.o` | 91 | 23910 | 记录 29/32（90%） / 样本 7682/8202（93%） | 否 / 是 / 否 |
| `__mem_cgroup_charge` | `mm/memcontrol.o` | 40 | 22761 | 记录 13/15（86%） / 样本 7617/7663（99%） | 否 / 是 / 否 |
| `__audit_syscall_entry` | `kernel/auditsc.o` | 49 | 18041 | 记录 15/16（93%） / 样本 5701/6170（92%） | 否 / 是 / 否 |
| `_raw_spin_lock_irqsave` | `kernel/locking/spinlock.o` | 5 | 11733 | 记录 1/2（50%） / 样本 3489/4122（84%） | 否 / 否 / 否 |
| `get_mem_cgroup_from_mm` | `mm/memcontrol.o` | 40 | 17971 | 记录 12/14（85%） / 样本 5959/6006（99%） | 否 / 是 / 否 |
| `__percpu_counter_limited_add` | `lib/percpu_counter.o` | 9 | 15483 | 记录 3/4（75%） / 样本 5161/5182（99%） | 否 / 是 / 否 |
| `__audit_syscall_exit` | `kernel/auditsc.o` | 12 | 12666 | 记录 4/5（80%） / 样本 3732/4696（79%） | 否 / 是 / 否 |
| `migrate_enable` | `kernel/sched/core.o` | 26 | 11449 | 记录 8/9（88%） / 样本 3247/4101（79%） | 否 / 是 / 否 |

末列顺序为 K-BASE / K-AFDO / K-BASE-S。N=100 时编译器只在覆盖率不足 100% 时报告诊断，有正值且无短缺告警的项以此标记。
Clang 22.1.8 的 YAML 将这些记录归入 `sample-profile-impl`。首轮统计只接受设计稿中的总类名，漏读正值，修正后以实际 pass 名统计。同一位置可在重放流水线中多次报告，NumSamples 合计用于核对消费，原始训练样本数见上节。
覆盖缺口来自对应编译阶段尚未应用的 profile 位置键，包括内联上下文。例如 `try_charge_memcg` 在 `mm/memcontrol.c:2169` 报 13/15 条记录、856/13,114 个样本。首组 YAML 的函数体匹配缺少偏移 2 和 15，权重 111 和 12,147 恰好等于样本缺口 12,258。同一对象的后续 YAML 记录显示两个位置均已应用。其余短缺诊断按编译器的汇总口径报告。20 个函数均匹配到正值。

- K-AFDO 与 K-BASE 共有 2,890 个非空文本输入节，其中 2,875 个共同顺序位置不同。第 1 位从 `vmlinux.a(init/main.o):.text.unlikely.` 移到 `vmlinux.a(kernel/signal.o):.text.unlikely.`。
- K-BASE-S 与 K-BASE 共有 2,897 个非空文本输入节，其中 2,895 个共同顺序位置不同。第 1 位从 `vmlinux.a(init/main.o):.text.unlikely.` 移到 `vmlinux.a(net/mac80211/mlme.o):.text.unlikely.`。

K-BASE-S 的最终链接 argv 去掉预登记 shuffle 参数后与 K-BASE 相同，冷热归组一致。K-AFDO 既有编译期冷热节变化，也有默认 LLD 调用图排序可读取的新输入，map 的顺序差异包含两者。
三份最终链接 map 均以归档输入重放，仅追加 `-Map=` 并把产物写入诊断目录。映射明细包括 .text 子节去向和 ARM head/idmap/entry、exidx/extab、init/exit 区间。
首轮 map 解析误把局部标签当成输出节。按 LLD 的 Out/In/Symbol 列重读原始 map 后，K-BASE-S 的所有冷热输入对象、节名、大小与输出节均与 K-BASE 相同。
三份预处理后的 ARM 链接脚本 SHA-256 均为 `ef55872dc0eb242876de96d2855c9ee1ed6abd932b8e29bda70b9d56d8f40213`。
- K-BASE ARM 特殊节去向与 K-BASE 一致，越出冷热边界的输入节 0 个，重放 build-id `96766cfcbff8c33d83ca38152ad02f6a02dd44d4`。
- K-AFDO ARM 特殊节去向与 K-BASE 一致，越出冷热边界的输入节 0 个，重放 build-id `43ba5d455daec5da17e7521048767cdace012c91`。
- K-BASE-S ARM 特殊节去向与 K-BASE 一致，越出冷热边界的输入节 0 个，重放 build-id `a78e6ca8956db526ba91d5856369fc1a7f15b5fd`。

| ARM 区间（左闭右开） | K-BASE | K-AFDO | K-BASE-S |
| --- | --- | --- | --- |
| .head.text | `0xc0008000..0xc00082c0` | `0xc0008000..0xc00082c0` | `0xc0008000..0xc00082c0` |
| idmap | `0xc0200000..0xc020003c` | `0xc0200000..0xc020003c` | `0xc0200000..0xc020003c` |
| entry | `0xc020003c..0xc020112c` | `0xc020003c..0xc0201140` | `0xc020003c..0xc020112c` |
| ARM.exidx | `0xc219b6e0..0xc2218aa0` | `0xc217d6f0..0xc21f71b8` | `0xc219b6e0..0xc2218e80` |
| ARM.extab | `0xc2218aa0..0xc22971a8` | `0xc21f71b8..0xc2271c78` | `0xc2218e80..0xc2297588` |
| .init.text | `0xc24003c0..0xc2454878` | `0xc24003c0..0xc2454774` | `0xc24003c0..0xc2453f18` |
| .exit.text | `0xc2454878..0xc2459818` | `0xc2454774..0xc24596e4` | `0xc2453f18..0xc2458f38` |

特殊节的输出归属和链接脚本规则一致。上表标出实际地址与长度变化。K-BASE-S 的 init 区少 2,400 B，等于 map 中链接器生成的 thunk 从 4,832 B 降到 2,432 B。exit 区 thunk 从 160 B 增至 288 B。两变体的 head、idmap、`_etext`、`__init_begin` 与 `__init_end` 起止锚点均与 K-BASE 一致。

| 变体 | .text | .rodata | .data | .bss | 文本对齐余量 | _end − _stext (B) | 2 MiB 档位 | zImage B | 热/冷 B | call-graph 对象 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| K-BASE | 20,049,052 | 5,158,333 | 1,874,160 | 592,080 | 922,468 | 40,254,608 | 20 | 14,965,104 | 0 / 104,564 | 0 |
| K-AFDO | 20,158,720 | 5,123,029 | 1,874,160 | 589,072 | 812,800 | 40,250,512 | 20 | 15,031,504 | 529,492 / 267,680 | 332 |
| K-BASE-S | 20,049,228 | 5,158,333 | 1,874,160 | 592,080 | 922,292 | 40,254,608 | 20 | 15,168,416 | 0 / 104,564 | 0 |

文本对齐余量按 K1c 口径为 `_etext − (.text 起址 + .text 大小)`。档位为 `ceil((_end − _stext) / 2 MiB)`。
计划共用的 K-BASE 模块树共 58 个模块，含 6 个 extra 模块。`.text` 合计 758,936 B，含 `.text.*` 合计 766,396 B。

| 变体 | 热区间 | 冷区间 | 热节 B / 节数 / 函数符号 | 冷节 B / 节数 / 函数符号 |
| --- | --- | --- | ---: | ---: |
| K-BASE | `0xc021b000..0xc021b000` | `0xc02013e8..0xc021ac5c` | 0 / 0 / 0 | 104,564 / 156 / 395 |
| K-AFDO | `0xc0243000..0xc02c4454` | `0xc02013fc..0xc024299c` | 529,492 / 258 / 874 | 267,680 / 399 / 1,153 |
| K-BASE-S | `0xc021b000..0xc021b000` | `0xc02013e8..0xc021ac5c` | 0 / 0 / 0 | 104,564 / 156 / 395 |

K-AFDO 2 MiB 档位与 K-BASE 相同。

## Gerrit 与停止点

0008 以快进方式追加到 `sandbox/lhmax2025/afdo_kernel_arm32`。读回 tip 和 tree 均等于本地，保留原父提交。Gerrit 提示提交标题超过 50 字符，推送成功。

- `tip=3a2602c3e12c11c4bf32f2415b02fdf8fe1ee75a`
- `tree=c7bb2aa6b3c4af19893b6a208be06eb5a5c4b926`
- `parent=67b7b28df8906b11201ae103a8a7072bed6d4538`

K-AFDO 与 K-BASE-S 均未部署，K1f 等待 PM 审核。
