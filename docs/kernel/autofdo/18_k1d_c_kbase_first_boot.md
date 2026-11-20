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
