# K1d-c：K-BASE 首启预检

## 结论

**STOP，发生在写入前。** K-BASE 普通版模块 RPM 能提供 PLAT 直启所加载十个模块中的四个。其余六个只在当前 PLAT 的 `extra/` 中核实到，vermagic 的首字段为 `6.12.80-arm-rpi4-v7l`。K-BASE 验收要求十个模块均由 `6.12.80-arm-rpi4-v7l-kbase` 模块树提供。已核对的 K-BASE 归档不足以满足该条件。需要六个模块对应 K-BASE 的构建产物才能按现行条件继续。[证据索引](evidence/k1d-c-index.json)

未写任何板上持久分区，未替换 `tryboot.txt`，未向板卡发出重启。当前仍是 K1d-b 回程的 U-Boot PLAT，boot ID `ae70026a-42df-4628-b9ae-9178012556b0`，运行 build-id `395733b9c917cb98309b39cc3ec379c03ac36b3f`，`tryboot=0`。只读取证后已执行 `sdb root off`，复核 UID 5001，boot_a 已卸载。

## 主机产物与模块准备

[07 构建归档](07_k1c_kbase_build.md)的 artifact manifest SHA 与原索引一致，以下四项从该清单逐字节重算核对。原始 vmlinux GNU build-id 为 `96766cfcbff8c33d83ca38152ad02f6a02dd44d4`。模块目标 release 为 `6.12.80-arm-rpi4-v7l-kbase`。

| 文件 | 大小（B） | SHA-256 |
| --- | ---: | --- |
| zImage | 14,965,104 | `e1751c8305ba06578ac2f2198a86f4456647660f488bcda67ccbadc4a3acefc8` |
| 原始 vmlinux | 347,054,628 | `41b5e16396f72314ca56b5f46dabb82bdd9c8581a3ba6894801a9e45b1678265` |
| System.map | 4,621,108 | `496a62ab4b0f2b1bda862035e6b2cd9d2c2b44718e624b2ac350b936d498802c` |
| arm-rpi4 模块 RPM | 731,336 | `8e3b377f4f004e93c3d8f2f72103a74f3f9af1ee2fed318ea15d42acb1fc7163` |

用 `rpm2cpio` 解包到主机 staging。执行 `depmod -b <staging> -F <K-BASE System.map> 6.12.80-arm-rpi4-v7l-kbase`，退出 0，stderr 无输出。用 `modinfo` 核对 52 个模块的 vermagic 均以预期 release 开头。生成的模块树有 66 个普通文件的 SHA、目录和符号链接清单。暂存 tar 为 3,543,040 B，SHA-256 `5743cd81bf23d55e7be97251d6ffbca515cfb4619ff8f39b54ae35014bc1348a`。这份 tar 是已验证的 K-BASE 内核 RPM 模块集，仍缺下节的六个模块。[主机产物及 depmod 收据](evidence/k1d-c-index.json)

## PLAT 模块来源与板上空间

复读 PLAT `/proc/modules`，十个名字与 [K1d-b 的 PLAT 固件直启](16_k1d_b_plat_tryboot.md)相同。其中 `brcmfmac`、`brcmutil`、`btbcm`、`hci_uart` 在 K-BASE 普通版内核 RPM 中。六个缺项的文件名也未出现在本次 K-BASE 归档的任何 RPM 里。板上 `modinfo` 定位到下列文件，均有 PLAT vermagic。对其返回路径执行 `rpm -qf` 均未返回所属包。逐文件 SHA 与原始命令输出见索引。

| 缺项 | PLAT 模块树内路径 |
| --- | --- |
| dm_bow | `extra/dm-bow.ko` |
| extcon_usb_fixed | `extra/extcon-usb-fixed.ko` |
| inform_reboot | `extra/inform-reboot.ko` |
| kdbus | `extra/kdbus/kdbus.ko` |
| logger | `extra/logger.ko` |
| proc_tsm | `extra/proc-tsm.ko` |

`/lib/modules` 解析为 `/usr/lib/modules`，当前由槽 A 的独立 ext4 分区 `/dev/mmcblk0p6` 以 `ro` 挂载，空闲 14,999,552 B。目标 release 目录不存在。后续新增模块目录的实际目的地为 p6。归档的 PLAT initramfs 不含 `.ko`，其中的 `/init` 从模块分区调用 modprobe，不能补充本次缺项。[板上只读模块取证](evidence/k1d-c-index.json)

boot_a 只读复核通过，**413 个原文件与 K1d-b 新增 4 个文件**的 SHA 及 419 条目录清单均与 K1d-b 回程收据一致。实测空闲 **16,465,920 B**。按 2,048 B 簇估算，zImage-kbase 需 14,966,784 B。替换 tryboot 时短暂并存旧文件及 `.tmp` 后仍有 **1,497,088 B**，最终预计 **1,499,136 B**，通过 512 KiB 下限。未将草案写板：

```diff
--- K1d-b tryboot.txt
+++ K1d-c tryboot.txt draft
@@ -52 +52 @@
-kernel=zImage-plat-direct
+kernel=zImage-kbase
```

## 未执行的运行验收和 K1d-d

未进入 K-BASE 启动，故新 boot ID、实时 FDT 与 cmdline、dmesg 差异、模块加载、HDMI、五分钟安静基线、PMU 正计数、冒烟 profile 质量与前十函数及各基准单轮墙钟均待测。PLAT 无需执行回程重启。

K1d-d 未达推送前提，未连接 Gerrit 执行写操作。以下为审阅到的七个**当前本地**提交主题。基线为 `0fac5de6a63091d141ad1cd3ed9d9e92b8dde708`，tip 为 `7fffbec570692c925cbf1f58ea9b1cd1a5d78ac8`，tree 为 `0766b898b7b0583c14fa3a09ddb3164bd3b4f4f3`。上游五项原作者均为 Rong Xu，本地两项作者 Hao Lin 与已发布的 LLVM 补丁作者邮箱一致。全文已留档。当前前五项尚未在消息中记录原上游 ID，首条消息有 GitHub URL。验收通过后需在供推送的副本中满足消息约束，并逐项核对 tree 和 SHA 对应关系。[本地提交消息检查](evidence/k1d-c-index.json)

| 当前 SHA | 上游 SHA | 当前提交主题 |
| --- | --- | --- |
| `81f9c0f680d6` | `315ad8780a12` | kbuild: Add AutoFDO support for Clang build |
| `538b438ff131` | `0043ecea2399` | vmlinux.lds.h: Adjust symbol ordering in text output section |
| `5afab829f803` | `db0b2991ae1a` | vmlinux.lds.h: Add markers for text_unlikely and text_hot sections |
| `085cb6e00998` | `0847420f5e49` | AutoFDO: Enable -ffunction-sections for the AutoFDO build |
| `56c8dc3c5071` | `2fd65f7afd5a` | AutoFDO: Enable machine function split optimization for AutoFDO |
| `e23625e56c23` | 本地 | ARM: enable Clang AutoFDO without function splitting |
| `7fffbec57069` | 本地 | ARM: configs: enable Tizen RPi4 AutoFDO training |
