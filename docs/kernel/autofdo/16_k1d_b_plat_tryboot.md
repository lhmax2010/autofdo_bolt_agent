# K1d-b：PLAT 副本固件直启

## 2026-11-19 PST 写入前核对

**状态：等待确认只在新 `tryboot.txt` 增加 `arm_64bit=0`。** 目标仍经 U-Boot 运行 PLAT。启动分区已完成只读核对，写入及两次重启尚未执行。

本轮目标为 `192.168.108.26:26101`，DT serial `100000004694d889`，运行 `6.12.80-arm-rpi4-v7l`、build-id `395733b9c917cb98309b39cc3ec379c03ac36b3f`。当前 boot ID 为 `e3c3050e-86dd-4d6a-b452-bd08ebafd9c9`，DT 的 `tryboot=0`、`u-boot,version=2025.10-g136798fd1-TIZEN.org`，HDMI-A-1 已连接且显示栈在运行。现场原始 cmdline、FDT、分区挂载、模块与 dmesg 作为对照。运行 FDT SHA-256 为 `b8628c49d4876750f6faf09b1e1f338d8904485657c6c7ceb06397c2290672a2`。[核对原件](evidence/k1d-b-index.json)

| 核对项 | 结果 |
| --- | --- |
| 归档镜像 | boot_a SHA-256 `ec89fb505f4e3a49e35b2044ab19bb4dd69388a53a3bdf5d6e8384a725ab5c9d` 通过。离线逐文件重算 413 项 SHA，均与 K1d-a 清单相同。 |
| 现场清单 | `/dev/mmcblk0p1`、FAT UUID `404C-7537`、PARTUUID `8cf5ae0c-2697-2540-9e74-bfb6482324c0`。只读挂载采集的 415 个条目及 413 个文件 SHA 均与归档一致。核对后卸载，SDB 复核 UID 5001。 |
| FAT 容量 | 实测空闲 39,010,304 B，每簇 2,048 B。四个拟新增文件合计实占 22,544,384 B，预计剩 **16,465,920 B（15.70 MiB）**，通过 512 KiB 下限。两份主机候选配置落在同一簇大小。 |

## 新文件与配置范围

| 拟新增文件 | 字节 | 主机侧来源和 SHA-256 |
| --- | ---: | --- |
| `zImage-plat-direct` | 14,905,760 | 精确从归档 boot_a 提取，SHA 与现场 `zImage` 相同，为 `d5345f13eada3a3aab8b2fca9f511c608469f708d83a6a2445882e68241cc9af`。 |
| `initramfs-afdo.gz` | 7,632,283 | 逐字节匹配归档 `ramdisk_a` 的 gzip 成员，解压后与 K1d-a CPIO 相同。SHA 为 `ea6c57b47cce3427abcb820c4da7682be52e50e8ac6e9c3dc40c1be4ce235eaf`。 |
| `cmdline-afdo.txt` | 360 | K1d-a §7 已入库草案，SHA 为 `7a6915f4e2bd45a318f7f891dc2a1c0a6c37b87c4c8f175a8c1e03dcabba3917`。 |
| `tryboot.txt` | 1,790 / 1,802 | 主机候选各自从归档 `config.txt` 生成。严格三处变更版与增加 ARM32 行版的 diff 和 SHA 均已留档。 |

官方说明 RPi4 在默认模式下选择 64 位，已知标准内核名可影响自动选择。此 PLAT zImage 为 ARM32，自定义名 `zImage-plat-direct` 不属于标准命名。现有 `config.txt` 无显式 `arm_64bit`；现场普通路径成功运行 ARM32 U-Boot，不能由此确定固件将对该自定义 zImage 采用同一模式。K1d-a §7 的直启草案已提出 `arm_64bit=0`。本轮允许的 `tryboot.txt` 三项文本改动未列这行，已请求用户确认后再开始写入。[Raspberry Pi 启动配置](https://www.raspberrypi.com/documentation/computers/config_txt.html#arm_64bit)

目标板的 coreutils 6.9 的 `sync` 无文件参数，`mv` 也无 `-n`。已在主机用 Clang 22.1.8 准备仅用于写入步骤的辅助程序，分别调用 `fsync`、`renameat2(RENAME_NOREPLACE)` 和 `syncfs`。主机 QEMU 验证了文件同步、拒绝覆盖、成功发布和文件系统同步。板上计划在专用 tmpfs 自检，FAT 写入期间才临时 RW 挂载。尚未在板上执行辅助程序。[候选文件、工具和收据](evidence/k1d-b-index.json)

tryboot 标记、固件追加的 cmdline、直启 FDT、启动稳定性、五分钟安静基线以及普通重启回程均待实机验证。当前现场仍保留原 U-Boot 路径，启动分区未写入。
