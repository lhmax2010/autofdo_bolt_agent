# K1d-c 续：补齐 extra 模块、p6 写入与 K-BASE 首启

2026-11-20（PST），RPi4 `192.168.108.26:26101`，序列号 `100000004694d889`。

**K-BASE 已启动，十个模块均从 K-BASE 模块树加载。验收在 FDT 原始 SHA-256 门禁停止。** 两份 FDT 的差异为 `/chosen/kaslr-seed` 的 8 字节和 `/chosen/compatible` 的 1 个对齐填充字节。普通重启已恢复 U-Boot PLAT。PMU、冒烟 profile、三个基准和 K1d-d 留待门禁通过后执行。[证据索引](evidence/k1d-c-extra-index.json)

## 六个模块的来源与构建

板上用 `modinfo` 读取六个模块，并用 `rpm -qf` 查询 `/lib/modules` 路径和解析后的 `/usr/lib/modules` 路径。六个文件均无 RPMDB 归属记录，license 均为 `GPL`，`depends` 均为空。PLAT vermagic 均为 `6.12.80-arm-rpi4-v7l SMP mod_unload modversions ARMv7 p2v8`。设备当前加载的六个模块与 [17 号预检](17_k1d_c_kbase_preflight.md)记录一致。

K-BASE 原构建使用的固定 Unified Toolchain snapshot 为 `20261104.125239`，Base Toolchain 为 `20261030.120529`。从同一 Unified snapshot 取得以下包，二进制 RPM 的 SHA 与该 snapshot 的 primary metadata 一致。源码包的 VCS 为 `platform/kernel/linux-tizen-modules-source#25797e8af7ed95a5783bbe84c11959560aaf7e92`，打包 recipe 与 RPi4 二进制包的 VCS 为 `platform/kernel/linux-tizen-modules#458baad02d812098938663971d1b8560a4813375`。[冻结仓库](https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261104.125239/repos/standard/)

| 包 | SHA-256 |
| --- | --- |
| `linux-tizen-modules-source-11.0.0-0.armv7l.rpm` | `ef770d5e8af0532fe4f80748a699e13710025fb0c1218f6504bc9eee1d80dbf5` |
| `linux-tizen-modules-source-11.0.0-0.src.rpm` | `79e45d2aaecd6c7f6dcbe4d4d0a1904628d7e204771e04d10df867bd0f166c91` |
| `linux-tizen-modules-11.0.0-0.src.rpm` | `9c7726daa8d14e0dfa59703d3c2e6019e077723a50b367ad4184c350ed233cdc` |
| `linux-tizen-modules-rpi4-11.0.0-0.armv7l.rpm` | `9bfa8c8e09b07eb3c8529739f78d896def839380a5621de540d0a2f6994d9ee4` |

冻结的 RPi4 二进制包与板上六个模块的 `srcversion` 全部相同。五个文件 SHA 也相同，`kdbus.ko` 的板上 SHA `1186ce63…`，包内 SHA `580d3ff0…`。重建使用冻结源码及其 spec，源码版本据 `srcversion` 交叉核对。

以 07 归档的 `arm-rpi4-linux-kernel-devel-6.12.80-0.armv7l.rpm` 解包树为目标，SHA-256 `be884286706c8b85eac177911cffe604ebffcee78ea5136f54420545fad2fdbd`。沿用构建根的 Clang/LLD 22.1.8 与 pahole 1.29。用冻结 SRPM spec 第 246–272 行的 RPi4 配置，包括 `THREAD_GROUP_CPUTIME_SUPPORT=1`、自带头文件以及 Clang warning flag 清理。只编译指定六项，`BUILD_zlogger=n`。构建目标 `ARCH=arm LLVM=1 LD=ld.lld`，Clang 实际目标为 `arm-linux-gnueabi`。环境固定为 `KBUILD_BUILD_TIMESTAMP='Wed Nov 18 14:59:26 UTC 2026'`、`KBUILD_BUILD_USER=abuild`、`KBUILD_BUILD_HOST=linhao-linux`、`KBUILD_BUILD_VERSION=1`、`LOCALVERSION=-kbase`。

运行 `make -C <devel> M=<module-source> ARCH=arm LLVM=1 LD=ld.lld CFLAGS_MODULE=-I<module-source>/include V=1 -j2 modules`。ARM32 devel 辅助程序通过构建根与 `qemu-arm-static` 运行。首轮遇到 `recordmcount: Exec format error`，补齐该辅助程序及 `genksyms` 的宿主机包装后，第二轮退出 0，墙钟 10.62 秒，`time -v` 最大 RSS 136,732 KiB。scope 限制为 6G/5G/200%，`nice -n 19 ionice -c3`。保留原始 `.ko`，交付树按 spec 使用 `llvm-strip --strip-debug`，逐项验证 `.BTF`、build-id 和 vermagic。构建未触及 K-BASE 内核产物。

| 模块 | PLAT、冻结 RPM 和重建共有的 srcversion | PLAT modinfo author | K-BASE 模块 build-id |
| --- | --- | --- | --- |
| `dm_bow` | `4032DDBA159B1A65579E8C5` | 空 | `6c2518583566b7e2c0ffe403547637ad54800739` |
| `extcon_usb_fixed` | `D3550FFCA82775E116F5712` | Marek Szyprowski | `9a12f46f54245abb4915bd02d883ea0125b2fd04` |
| `inform_reboot` | `E834BDD9D19EFB1067B3D56` | 空 | `e98eeab35145066cadc2b0633a2e6a9a98664f6e` |
| `kdbus` | `82BF5E4477A92EF05AD9A1B` | 空 | `619bf97b1d5023d5c5b05cbb22b0b6fd5ab8b928` |
| `logger` | `399ECEA94E242CAEC4C1FFE` | Robert Love | `41cb571fae756089a824ea5f5030f8b2df89810d` |
| `proc_tsm` | `4AAA2EAB4A1F60715A4F1E3` | 空 | `72bb1d20d115eddbbf6b96e7e9073c55a21e3058` |

六个重建模块的 vermagic 均为 `6.12.80-arm-rpi4-v7l-kbase SMP mod_unload modversions ARMv7 p2v8`。按 PLAT 的 `extra/` 结构合并，包括 `extra/kdbus/kdbus.ko`。52 个 K-BASE RPM 模块与 6 个重建模块合并后执行 `depmod -b <staging> -F <K-BASE System.map> 6.12.80-arm-rpi4-v7l-kbase`，退出 0，stderr 为空。树清单含 121 项，72 个普通文件记录 SHA。tar 大小 3,788,800 B，SHA-256 `2b04e40c500437213a660125c09d24874ce978dffbb2f0026de195e6c7894ca0`。

## p6 和 boot_a 写入

`/lib/modules` 指向 `/usr/lib/modules`，由 `/dev/mmcblk0p6`（`PARTLABEL=module_a`，ext4）挂载，初始选项 `ro,relatime`。板上 `/etc/fstab` 缺失，systemd 挂载项来源为 `/proc/self/mountinfo`。归档 initramfs 的 `usr/sbin/init` 第 257 行按槽位取 `module${P_SUFFIX}`，第 487 行只读挂载，第 490–496 行将挂载移入 rootfs。ext4 验证为 clean，随后实际 remount 也成功。

| p6 数据 | 字节 |
| --- | ---: |
| 原始分区 | 33,554,432 |
| `df` 容量 / 已用 / 可用（写入前） | 19,861,504 / 4,116,480 / 14,999,552 |
| PLAT 模块目录 `du` | 4,530,176 |
| K-BASE staging 逻辑大小 / 估算分配 | 3,697,794 / 4,038,656 |
| 写入前 1.2× 空间门槛 | 4,846,388 |
| K-BASE 板上目录 `du` / 写入后分区可用 | 4,534,272 / 10,956,800 |

写入前以只读状态复核 p6 的 PLAT 清单、K-BASE 目录不存在、boot_a 的 413 个原文件及 K1d-b 新增四个文件。p6 仅新增 `/lib/modules/6.12.80-arm-rpi4-v7l-kbase/`，在 `rw` 挂载期间解包、逐文件比对与 `syncfs`，随后 remount `ro`。只读后第二次核对 K-BASE 清单和 72 个 SHA，PLAT 的 123 项清单与 73 个文件 SHA 写前写后完全相同。板上实际分配也满足写前空间的 1.2× 条件。

boot_a 写前空闲 16,465,920 B。按 2,048 B 簇，写入中最低预计 1,497,088 B。新增 `zImage-kbase` 14,965,104 B（SHA-256 `e1751c8305ba06578ac2f2198a86f4456647660f488bcda67ccbadc4a3acefc8`）。替换任务自有 `tryboot.txt`，只把 `kernel=zImage-plat-direct` 改为 `kernel=zImage-kbase`，新 SHA-256 `c2730b8559db753aedc81644fee4b641836dc9e9fb3d5e065af856bff0e68d79`。经 `.tmp`、fsync、SHA、rename、syncfs、读回后再次只读挂载核对 418 个文件，除新增镜像和获准替换的配置外，其余 416 个文件 SHA 相同。最终剩余 1,499,136 B，boot_a 已卸载。

## K-BASE 启动与停止点

`systemctl --no-block reboot "0 tryboot"` 于 00:32:57 PST 发出，52.194 秒后恢复第一条 SDB 只读命令。按规程立即断开本设备，之后每 10 秒轮询重连。两次重启均在 120 秒前恢复，无需追加断开或重启主机 SDB 服务。

| 验收项 | 实测 |
| --- | --- |
| boot ID | `ae70026a-42df-4628-b9ae-9178012556b0` → `8f8c0020-0c8a-4f78-9fb4-b0e0622f4705` |
| 内核身份 | `96766cfcbff8c33d83ca38152ad02f6a02dd44d4`，`6.12.80-arm-rpi4-v7l-kbase`，`armv7l`，四核 CPU architecture 7 |
| 固件与挂载 | `tryboot=1`，无 U-Boot 标记。rootfs 为 p2 槽 A，p6 仍只读，各板载分区挂载与 PLAT 直启一致 |
| cmdline | 与 PLAT 直启原件逐字节一致，SHA-256 `60c4e06d6dbb9bfbc64bd1967efb973c1e7a93f331b90d03c6f98c2cadd0b82c` |
| FDT | raw SHA-256 `2a6dc67c3f7b7cd70634fbe5401a8b3619fa5cee3c183396e75ec82d4ac5e5e3`，预期 `b8564e4258c6c1a7fc59c825770f06cfddbd8999ea39b99f946f9667d37ee8e0`，门禁失败 |
| 模块 | 与 PLAT 直启恰好相同的 10 个名字。全部 `modinfo` 路径与 vermagic 来自 K-BASE release，运行时 sysfs GNU build-id note 逐个匹配部署文件 |
| 显示、网络、温度 | HDMI connected，显示服务 active，enlightenment 运行，eth0 和 SDB 正常。采证瞬时 73.523°C／74.497°C |
| dlog、D-Bus | `logger` 已加载，`/dev/log_main` 存在，`dlogutil -t 20` 成功读到本次 boot 的 SDB 日志。`kdbus` 已加载且在用，系统总线 `ListNames` 返回成功。PLAT 回包的 16 个 well-known 名称均在 K-BASE 回包中，包括 `org.tizen.engine-loader`、`org.tizen.FocusServer` 和 `org.tizen.update.manager` |

先用 raw SHA 作验收，再离线解析诊断。两份 FDT 长度 58,325 B，节点集合、内存保留表和 `linux,initrd-start/end` 一致。结构化属性仅 `/chosen/kaslr-seed` 不同。九处原始字节差异位于零基偏移 2355（`/chosen:compatible` 对齐填充）及 2444–2451（八字节 seed）。报告保留原始门禁结果，诊断脚本仅在主机比较已有文件。

`dmesg` 无新增 Oops、BUG、WARNING 或模块加载失败。去时间戳后，警告及更高优先级日志的差异逐项如下，完整日志和 85 行全级别差异见索引。

- 首次外置模块 taint 消息由 `inform_reboot` 变为 `extcon_usb_fixed`。两边均加载外置模块。
- 两边都有 systemd-journald 报告 journal 未干净关闭并替换文件，进程 PID 不同。
- K-BASE 额外有 `kauditd_printk_skb: 19 callbacks suppressed`，表示内核 audit 日志限速。
- 两边都有 sdbd-user 使用已弃用的 `oom_adj` 提示，PID 不同。

本地自动判定初版额外把 D-Bus 标成失败，原因是脚本误把总线自身名称当作 `ListNames` 数组必需项。原始双方回包均正常，响应头的 sender 为 `org.freedesktop.DBus`。改为据成功退出、method return、sender 和已注册的 Tizen 服务核验后，唯一失败项为 raw FDT SHA。回程首次离线分析引用了旧取证目录中缺失的 CPU architecture 文件，改用 K1d-b 已归档的 U-Boot 基准字节后复算通过。两次修正均使用同一批板上原件。

## PLAT 回程与未执行项

00:34:14 PST 发出普通 reboot。62.159 秒后 SDB 重连，boot ID `d4cc6a04-0a0c-44c7-ab14-cb20ad08b274`，build-id `395733b9c917cb98309b39cc3ec379c03ac36b3f`，`tryboot=0`，U-Boot 版本属性存在。cmdline 与原始 U-Boot PLAT 逐字节一致，SHA-256 `1a132093c6e7220e981bd54c1a6a7bf780a19927c9787d3c9dcb7149eff106b4`。最终复核 root off、UID 5001，p6 只读、boot_a 无挂载。任务新增的 K-BASE 模块目录、`zImage-kbase` 和更新后的 `tryboot.txt` 均保留。

五分钟安静窗口、PMU 正计数、perf 冒烟 profile 与前十函数、pipe/mmfault/forkexec 单轮均未执行。K1d-d 的七项提交消息整理与 Gerrit sandbox 推送依赖完整验收，本轮未执行。[现有本地提交清单](17_k1d_c_kbase_preflight.md#未执行的运行验收和-k1d-d)

## 收尾

2026-11-20（PST）使用已部署的 `zImage-kbase`、`tryboot.txt` 和 K-BASE 模块树复跑。boot_a 与 p6 本轮无写入。[收尾证据索引](evidence/k1d-c-closeout-index.json)

### FDT 门禁与回溯

用原 K-BASE devel 包中的 DTC `1.7.0-gbcd02b52` 执行 `dtc -I dtb -O dts`。规范化只删除根节点下 `/chosen` 的 `kaslr-seed` 和 `rng-seed`，保留其余 DTS 字节；二进制对齐填充不进入 DTS。用 `cmp` 对照 K1d-b PLAT 直启。若出现其他属性差异，判定失败并保留差异供 PM 审阅。

| FDT 输入 | 判定 |
| --- | --- |
| K1d-b PLAT 直启归档 | 基准 |
| 18 号报告首次 K-BASE 直启归档 | 回溯逐字节一致 |
| 本轮 K-BASE 直启 | 逐字节一致 |

三份规范化 DTS 均为 67,917 B，SHA-256 为 `66dcc57d2f30bc0a2a7258d9d799b83f05acd663259e14cff9871525437bf237`。没有额外需排除的属性。首次启动的原始 SHA 失败收据保留在上文。

### K-BASE 验收

00:41:31 PST 发出 `systemctl --no-block reboot "0 tryboot"`，52.232 秒后 SDB 恢复。核对 boot ID 从 `d4cc6a04-0a0c-44c7-ab14-cb20ad08b274` 变为 `148ff51a-dc8a-4aa3-a2bd-8088f60bc6d2`。内核 build-id 为 `96766cfcbff8c33d83ca38152ad02f6a02dd44d4`，release 为 `6.12.80-arm-rpi4-v7l-kbase`，机器为 `armv7l`，四核 CPU architecture 均为 7，固件属性 `tryboot=1`。cmdline 与 K1d-b PLAT 直启逐字节一致。rootfs 为槽 A，p6 只读，各板载分区挂载不变。

十个模块重复通过路径、vermagic 与运行时 build-id 检查。HDMI、enlightenment 和 eth0 正常，`dlogutil` 读取本次启动日志成功，D-Bus `ListNames` 返回成功。对照 PLAT 直启的 dmesg 无新增 Oops、BUG、WARNING 或模块加载失败。警告差异再次为外置模块首次 taint 的模块名、journald 和 sdbd-user 的 PID 差异、audit 限速。完成采样及基准后重读 dmesg 和模块列表，无新增上述故障，模块名仍为同一组。

安静基线覆盖 300.00 秒、61 个点，第一次连续 30 秒全板忙时低于 2.91% 的窗口在开机 61.91 秒结束。全窗中位数 1.911%，p90 2.601%，峰值 26.403% 出现在 uptime 86.91 秒附近。温度中位数 71.575°C，范围 70.114–74.497°C。后续冒烟和单轮只判断能否运行，沿用当时的 governor，无性能偏差结论。

`perf stat -a -e cycles:k,cycles:u,instructions:k -- sleep 5` 三个计数均为正，CSV 中各事件运行比例 100%。

| 事件 | 计数 |
| --- | ---: |
| `cycles:k` | 183,677,695 |
| `cycles:u` | 28,199,970 |
| `instructions:k` | 66,100,130 |

### 冒烟 profile 与 IRQ 恢复窗口

`perf record -a -e cycles -c 1000003 --buildid-mmap -N` 在 CPU3 上运行 pipe 10 秒。主机以补丁 10（`8392aa945cb9`）的 `llvm-profgen --ip-samples --kernel` 转换，用 K-BASE 原始未剥离 vmlinux，传入 perf script 的 mmap、build-id list 与采样事件，输出 extbinary。记录 SHA-256 为 `a262e8045b28d747ccd32a4d435e9ba7ea7d4d07446e9cf90d78b61c5da70cf5`，profile SHA-256 为 `eb89e807b368dc65e59c704fb7fc75257a66eb533628e204551b4163b18bea04`。

转换为 `ok`，身份 `verified`，`fs_discriminator=true`。共 16,485 个样本，其中内核 15,592（含模块），vmlinux 目标 15,591，跳过 1 个模块样本。映像外 0/15,591（0.00%），函数内缺行号 839，写入 614 个位置。质量报告标注固定 period、样本密度低，丢失完整性和采样充分性均为 unknown。本次 profile 只用于冒烟验收。

按 [04 的 IRQ 恢复窗口方法](04_k1a_baseline.md#k1c-评审补充irq-恢复窗口与-c-源码份额)，用采样前后 kallsyms 和模块映射，核得 `_text` slide 为 0。用 K-BASE vmlinux 的可执行 PT_LOAD 字节及 core text 范围识别 A32 `cpsie i` 与 `msr CPSR_c,Rn`。在同一核心符号内统计 IP 距指令 0 或 +4 B 的并集，分母是全部 15,592 个 K 模式样本（含模块）。模块不扫描指令窗口。

| 窗口 | 样本 | 内核份额 |
| --- | ---: | ---: |
| 显式 IRQ 函数名 | 5,678 | 36.42% |
| CPSIE 0/+4 B | 4,435 | 28.44% |
| MSR 0/+4 B | 5,018 | 32.18% |
| 并集 0/+4 B | 9,453 | 60.63% |
| 并集 0/+4/+8 B | 9,481 | 60.81% |

最大点位在 `_raw_spin_unlock_irqrestore` 的 `0xc151ca68`，紧随指令 `0xc151ca6c` 有 4,690 个样本。份额表示靠近候选开 IRQ 指令的 PC；`msr` 的寄存器值与实际中断到达时间不在采样记录中。

按内核 IP 和 profile 写入权重各列前十。左表占比使用全部 K 模式样本，右表来自 `llvm-profdata show --sample`。

| 内核 IP 函数 | 样本（占比） | Profile 函数 | 写入权重 |
| --- | ---: | --- | ---: |
| `_raw_spin_unlock_irqrestore` | 4,690（30.08%） | `_raw_spin_unlock_irqrestore` | 4,690 |
| `finish_task_switch` | 2,396（15.37%） | `finish_task_switch` | 2,396 |
| `__rseq_handle_notify_resume` | 990（6.35%） | `arch_local_irq_enable` | 988 |
| `arch_local_irq_enable` | 988（6.34%） | `__rseq_handle_notify_resume` | 919 |
| `vector_swi` | 707（4.53%） | `__kmap_local_pfn_prot` | 585 |
| `__kmap_local_pfn_prot` | 604（3.87%） | `kunmap_local_indexed` | 583 |
| `kunmap_local_indexed` | 587（3.76%） | `arm_copy_from_user` | 383 |
| `do_work_pending` | 503（3.23%） | `pipe_write` | 232 |
| `arm_copy_from_user` | 383（2.46%） | `arm_copy_to_user` | 199 |
| `pipe_write` | 348（2.23%） | `arm_clear_user` | 194 |

### 基准单轮与 PLAT 回程

| 基准 | 参数（均绑 CPU3） | 墙钟 | 结果 |
| --- | --- | ---: | --- |
| pipe | `perf bench sched pipe -l 500000` | 12.421 s | 完成，40,423 ops/s |
| mmfault | 64 MiB，59 次 | 9.940 s | 完成，966,660 minor faults |
| forkexec | 12,774 次，既有静态 `empty` 子程序 | 14.721 s | 完成 |

00:49:04 PST 发出普通 reboot，62.161 秒后 SDB 恢复。K-BASE 启动和 PLAT 回程都只用本设备断开和轮询重连，未触发 120 秒追加断开或主机 SDB 服务重启。回程 boot ID 为 `d1defd54-5562-42d6-a0e0-d553e4b21f6a`，U-Boot 标记存在，PLAT build-id `395733b9c917cb98309b39cc3ec379c03ac36b3f`，`tryboot=0`。cmdline 与原始 PLAT 逐字节一致。最后 `sdb root off` 并复核 UID 5001，p6 只读，boot_a 无挂载，新增文件保留。

### K1d-d Gerrit sandbox

全部验收及 PLAT 回程通过后，以 `lhmax2025` 新建 `sandbox/lhmax2025/afdo_kernel_arm32`。用 `git ls-remote` 读回，并 fetch 该引用复核 tip 与 tree。tip 为 `67b7b28df8906b11201ae103a8a7072bed6d4538`，tree 为 `0766b898b7b0583c14fa3a09ddb3164bd3b4f4f3`，七项提交的共同基线为 `0fac5de6a63091d141ad1cd3ed9d9e92b8dde708`。逐个核对七个 tree 与本地构建时提交一致。五份上游消息与原始补丁逐字节核对后追加 `Upstream:`，保留 Rong Xu 作者身份及原链接。两个本地提交保留 Hao Lin 的英文消息。Gerrit 提示部分主题行过长，保留原文，分支创建成功。推送内容仅含 linux-rpi 的七项提交。

| K-BASE 本地 SHA | Gerrit SHA |
| --- | --- |
| `81f9c0f680d6` | `157104238b9a` |
| `538b438ff131` | `fad5da00a2a3` |
| `5afab829f803` | `bcbe11783b66` |
| `085cb6e00998` | `3e3ec0bdb8a6` |
| `56c8dc3c5071` | `3ea8cd5b466d` |
| `e23625e56c23` | `5908bdf40f72` |
| `7fffbec57069` | `67b7b28df890` |

<details>
<summary>七条最终提交信息全文</summary>

#### 1. `157104238b9a`

```text
kbuild: Add AutoFDO support for Clang build

Add the build support for using Clang's AutoFDO. Building the kernel
with AutoFDO does not reduce the optimization level from the
compiler. AutoFDO uses hardware sampling to gather information about
the frequency of execution of different code paths within a binary.
This information is then used to guide the compiler's optimization
decisions, resulting in a more efficient binary. Experiments
showed that the kernel can improve up to 10% in latency.

The support requires a Clang compiler after LLVM 17. This submission
is limited to x86 platforms that support PMU features like LBR on
Intel machines and AMD Zen3 BRS. Support for SPE on ARM 1,
 and BRBE on ARM 1 is part of planned future work.

Here is an example workflow for AutoFDO kernel:

1) Build the kernel on the host machine with LLVM enabled, for example,
       $ make menuconfig LLVM=1
    Turn on AutoFDO build config:
      CONFIG_AUTOFDO_CLANG=y
    With a configuration that has LLVM enabled, use the following
    command:
       scripts/config -e AUTOFDO_CLANG
    After getting the config, build with
      $ make LLVM=1

2) Install the kernel on the test machine.

3) Run the load tests. The '-c' option in perf specifies the sample
   event period. We suggest     using a suitable prime number,
   like 500009, for this purpose.
   For Intel platforms:
      $ perf record -e BR_INST_RETIRED.NEAR_TAKEN:k -a -N -b -c <count> \
        -o <perf_file> -- <loadtest>
   For AMD platforms:
      The supported system are: Zen3 with BRS, or Zen4 with amd_lbr_v2
     For Zen3:
      $ cat proc/cpuinfo | grep " brs"
      For Zen4:
      $ cat proc/cpuinfo | grep amd_lbr_v2
      $ perf record --pfm-events RETIRED_TAKEN_BRANCH_INSTRUCTIONS:k -a \
        -N -b -c <count> -o <perf_file> -- <loadtest>

4) (Optional) Download the raw perf file to the host machine.

5) To generate an AutoFDO profile, two offline tools are available:
   create_llvm_prof and llvm_profgen. The create_llvm_prof tool is part
   of the AutoFDO project and can be found on GitHub
   (https://github.com/google/autofdo), version v0.30.1 or later. The
   llvm_profgen tool is included in the LLVM compiler itself. It's
   important to note that the version of llvm_profgen doesn't need to
   match the version of Clang. It needs to be the LLVM 19 release or
   later, or from the LLVM trunk.
      $ llvm-profgen --kernel --binary=<vmlinux> --perfdata=<perf_file> \
        -o <profile_file>
   or
      $ create_llvm_prof --binary=<vmlinux> --profile=<perf_file> \
        --format=extbinary --out=<profile_file>

   Note that multiple AutoFDO profile files can be merged into one via:
      $ llvm-profdata merge -o <profile_file>  <profile_1> ... <profile_n>

6) Rebuild the kernel using the AutoFDO profile file with the same config
   as step 1, (Note CONFIG_AUTOFDO_CLANG needs to be enabled):
      $ make LLVM=1 CLANG_AUTOFDO_PROFILE=<profile_file>

Co-developed-by: Han Shen <shenhan@google.com>
Signed-off-by: Han Shen <shenhan@google.com>
Signed-off-by: Rong Xu <xur@google.com>
Suggested-by: Sriraman Tallam <tmsriram@google.com>
Suggested-by: Krzysztof Pszeniczny <kpszeniczny@google.com>
Suggested-by: Nick Desaulniers <ndesaulniers@google.com>
Suggested-by: Stephane Eranian <eranian@google.com>
Tested-by: Yonghong Song <yonghong.song@linux.dev>
Tested-by: Yabin Cui <yabinc@google.com>
Tested-by: Nathan Chancellor <nathan@kernel.org>
Reviewed-by: Kees Cook <kees@kernel.org>
Tested-by: Peter Jung <ptr1337@cachyos.org>
Signed-off-by: Masahiro Yamada <masahiroy@kernel.org>

Upstream: 315ad8780a129e82e2c5c65ee6e970d91a577acb
```

#### 2. `fad5da00a2a3`

```text
vmlinux.lds.h: Adjust symbol ordering in text output section

When the -ffunction-sections compiler option is enabled, each function
is placed in a separate section named .text.function_name rather than
putting all functions in a single .text section.

However, using -function-sections can cause problems with the
linker script. The comments included in include/asm-generic/vmlinux.lds.h
note these issues.:
  “TEXT_MAIN here will match .text.fixup and .text.unlikely if dead
   code elimination is enabled, so these sections should be converted
   to use ".." first.”

It is unclear whether there is a straightforward method for converting
a suffix to "..".

This patch modifies the order of subsections within the text output
section. Specifically, it changes current order:
  .text.hot, .text, .text_unlikely, .text.unknown, .text.asan
to the new order:
  .text.asan, .text.unknown, .text_unlikely, .text.hot, .text

Here is the rationale behind the new layout:

The majority of the code resides in three sections: .text.hot, .text,
and .text.unlikely, with .text.unknown containing a negligible amount.
.text.asan is only generated in ASAN builds.

The primary goal is to group code segments based on their execution
frequency (hotness).

First, we want to place .text.hot adjacent to .text. Since we cannot put
.text.hot after .text (Due to constraints with -ffunction-sections,
placing .text.hot after .text is problematic), we need to put
.text.hot before .text.

Then it comes to .text.unlikely, we cannot put it after .text (same
-ffunction-sections issue) . Therefore, we position .text.unlikely
before .text.hot.

.text.unknown and .tex.asan follow the same logic.

This revised ordering effectively reverses the original arrangement (for
.text.unlikely, .text.unknown, and .tex.asan), maintaining a similar level
of affinity between sections.

It also places .text.hot section at the beginning of a page to better
utilize the TLB entry.

Note that the limitation arises because the linker script employs glob
patterns instead of regular expressions for string matching. While there
is a method to maintain the current order using complex patterns, this
significantly complicates the pattern and increases the likelihood of
errors.

This patch also changes vmlinux.lds.S for the sparc64 architecture to
accommodate specific symbol placement requirements.

Co-developed-by: Han Shen <shenhan@google.com>
Signed-off-by: Han Shen <shenhan@google.com>
Signed-off-by: Rong Xu <xur@google.com>
Suggested-by: Sriraman Tallam <tmsriram@google.com>
Suggested-by: Krzysztof Pszeniczny <kpszeniczny@google.com>
Tested-by: Yonghong Song <yonghong.song@linux.dev>
Tested-by: Yabin Cui <yabinc@google.com>
Tested-by: Nathan Chancellor <nathan@kernel.org>
Reviewed-by: Kees Cook <kees@kernel.org>
Signed-off-by: Masahiro Yamada <masahiroy@kernel.org>

Upstream: 0043ecea2399ffc8bfd99ed9dbbe766e7c79293c
```

#### 3. `bcbe11783b66`

```text
vmlinux.lds.h: Add markers for text_unlikely and text_hot sections

Add markers like __hot_text_start, __hot_text_end, __unlikely_text_start,
and __unlikely_text_end which will be included in System.map. These markers
indicate how the compiler groups functions, providing valuable information
to developers about the layout and optimization of the code.

Co-developed-by: Han Shen <shenhan@google.com>
Signed-off-by: Han Shen <shenhan@google.com>
Signed-off-by: Rong Xu <xur@google.com>
Suggested-by: Sriraman Tallam <tmsriram@google.com>
Tested-by: Yonghong Song <yonghong.song@linux.dev>
Tested-by: Yabin Cui <yabinc@google.com>
Tested-by: Nathan Chancellor <nathan@kernel.org>
Reviewed-by: Kees Cook <kees@kernel.org>
Signed-off-by: Masahiro Yamada <masahiroy@kernel.org>

Upstream: db0b2991ae1aac5ca985ec6fd8ff9bd9b2126c9b
```

#### 4. `3e3ec0bdb8a6`

```text
AutoFDO: Enable -ffunction-sections for the AutoFDO build

Enable -ffunction-sections by default for the AutoFDO build.

With -ffunction-sections, the compiler places each function in its own
section named .text.function_name instead of placing all functions in
the .text section. In the AutoFDO build, this allows the linker to
utilize profile information to reorganize functions for improved
utilization of iCache and iTLB.

Co-developed-by: Han Shen <shenhan@google.com>
Signed-off-by: Han Shen <shenhan@google.com>
Signed-off-by: Rong Xu <xur@google.com>
Suggested-by: Sriraman Tallam <tmsriram@google.com>
Tested-by: Yonghong Song <yonghong.song@linux.dev>
Tested-by: Yabin Cui <yabinc@google.com>
Tested-by: Nathan Chancellor <nathan@kernel.org>
Reviewed-by: Kees Cook <kees@kernel.org>
Signed-off-by: Masahiro Yamada <masahiroy@kernel.org>

Upstream: 0847420f5e499a7ab518942fff71482179290163
```

#### 5. `3ea8cd5b466d`

```text
AutoFDO: Enable machine function split optimization for AutoFDO

Enable the machine function split optimization for AutoFDO in Clang.

Machine function split (MFS) is a pass in the Clang compiler that
splits a function into hot and cold parts. The linker groups all
cold blocks across functions together. This decreases hot code
fragmentation and improves iCache and iTLB utilization.

MFS requires a profile so this is enabled only for the AutoFDO builds.

Co-developed-by: Han Shen <shenhan@google.com>
Signed-off-by: Han Shen <shenhan@google.com>
Signed-off-by: Rong Xu <xur@google.com>
Suggested-by: Sriraman Tallam <tmsriram@google.com>
Suggested-by: Krzysztof Pszeniczny <kpszeniczny@google.com>
Tested-by: Yonghong Song <yonghong.song@linux.dev>
Tested-by: Yabin Cui <yabinc@google.com>
Tested-by: Nathan Chancellor <nathan@kernel.org>
Reviewed-by: Kees Cook <kees@kernel.org>
Signed-off-by: Masahiro Yamada <masahiroy@kernel.org>

Upstream: 2fd65f7afd5a73b685a1651cb651ade120b53e15
```

#### 6. `5908bdf40f72`

```text
ARM: enable Clang AutoFDO without function splitting

Select the 6.13 architecture capability. Clang 22 supports ARM
sample-profile use but rejects machine function splitting for ARM.
Keep the compiler and ThinLTO linker MFS options specific to x86,
the existing supported architecture in this backport, and only use
them with a profile.

Keep global function sections off for ARM. The existing explicit
hot and unlikely patterns place profiled sections in the main text
output. Restrict AutoFDO's general TEXT_MAIN wildcard to x86 so
it does not claim normal ARM special sections prematurely.

The five upstream patches apply without textual conflicts. These
changes adapt their compiler and linker behavior for ARM32.

Signed-off-by: Hao Lin <hao.lin@samsung.com>
```

#### 7. `67b7b28df890`

```text
ARM: configs: enable Tizen RPi4 AutoFDO training

Enable AutoFDO in the existing BCM2711 defconfig merged by the spec
for the regular and RT builds. Keep CONFIG_LOCALVERSION and the
existing target-specific localversion file as the release prefix.

Allow an optional kernel_localversion RPM macro to set LOCALVERSION
in both spec phases and extend the modules package paths. The old
paths end in -v7l or -v8 and would miss modules with a build suffix.
Use -kbase for the training build so its modules can coexist with
the original release. An unset macro preserves the existing paths.

Signed-off-by: Hao Lin <hao.lin@samsung.com>
```

</details>
