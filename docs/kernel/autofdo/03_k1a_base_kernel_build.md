# K1a：板用 BASE 内核构建与部署方案

**结果：BASE 构建通过。最终尝试 04 的 GBS 退出 0，墙钟 4,047.18 秒（67 分 27 秒），产出 15 个二进制 RPM + 1 个 SRPM。原始 vmlinux 与 zImage 身份一致；RPM devel/debuginfo 经标准后处理重算 build-id，须区别使用（见 §3）。未接板、未刷写。**

本轮仅在主机构建；未连接、刷写或重启 RPi4。源码固定为 `platform/kernel/linux-rpi@0fac5de6a63091d141ad1cd3ed9d9e92b8dde708`（K，含 `f240c280` force_reclaim 修正及 PMUv3）。spec、defconfig 和源码均不修改，不加入 AutoFDO 补丁或 profile。K0 的 conditional go 仍适用于后续优化内核；BASE 构建本身不证明 AutoFDO 可用或性能获益。

## 1. 来源、固定仓库与命令

从已取得的 K 本地仓库 `temp/kernel-afdo-k0/linux-rpi-board` 用 `git clone --local --no-checkout` 建立任务独立源码目录，再 detached checkout K；本轮没有访问 Gerrit。构建前 Git 工作树干净。与 K0 相同的 SHA-256：

| 输入 | SHA-256 |
|---|---|
| `packaging/linux-rpi.spec` | `03cc402251ff955763eea39a653e6cd986a9b06d85950236d3eeee958c9d30ff` |
| `arch/arm/configs/tizen_bcm2711_defconfig` | `8b028bc13db383c97eb01d0897206ef8d23e767d6bbd7cee34bc79b7234ab55d` |

固定采用 [LLVM 发布 §9](../../profgen/delivery/01_release.md#9-指定unified按规则选base的发布重试2026-11-14) 已用组合，两个仓库的 packages/repodata/repomd.xml 与 primary 均 HTTP 200，primary 的摘要与 repomd 一致；没有使用 latest 或 snapshot 回退。

- Base：`https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261030.120529/repos/standard/packages/`
- Unified：`https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261104.125239/repos/standard/packages/`

元数据列出 ARMv7l clang/LLVM `22.1.8-4.1`。实际 GBS 为 **2.1.1**，depanneur **0.16.30**，不同于旧 PMUv3 构建的 GBS 2.1.0。已解析并归档 130 个依赖 RPM，130/130 文件 SHA 与固定 primary 元数据匹配；实际 buildroot 的 130 个安装记录、最终缓存与归档 RPM 已逐一核对；索引见 §3。

以下路径相对于主工作目录；`BASE` 仅用于说明命令：

```sh
BASE=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/base-0fac5de6
# 由任务专用 run-build-04.py 设置隔离的 HOME/XDG/TMPDIR 并在 source 中执行：
gbs -c "$BASE/gbs-04.conf" build -A armv7l --spec linux-rpi.spec \
  --buildroot "$BASE/gbs-root-04" --threads 1 --define '_smp_mflags -j2' \
  --define '__spec_build_cmd /usr/bin/env JOBS=2 %{___build_cmd}' \
  --define '__spec_install_cmd /usr/bin/env JOBS=2 %{___build_cmd}'
# 外层实际启动：
nice -n 19 ionice -c3 systemd-run --user --unit=kernel-k1a-base-0fac5de6-04 \
  --property=MemoryMax=6G --property=MemoryHigh=5G \
  --property=CPUQuota=200% --property=RemainAfterExit=yes \
  /usr/bin/nice -n 19 /usr/bin/ionice -c3 /usr/bin/python3 "$BASE/run-build-04.py"
```

新建 `gbs-root-04`，不复用旧 scratch。任务 HOME 只承载本轮 GBS 配置，不修改用户级配置；不读取或修改受保护的三份项目 GBS 配置。buildconf 默认 `_toolchain=clang`，由原 spec 条件导出 `LLVM=1`。原 spec 同时构建普通和 RT 两套，因此保留两套输出；未来 RPi4 部署仅选择普通内核及普通 modules RPM，不安装 RT。

## 2. 资源与实际构建结果

启动门禁完整保留：MemAvailable ≥16 GiB，load1 < 0.6×可用 CPU 数，磁盘可用 ≥50 GiB，且没有其他 GBS/rpmbuild/depanneur 任务；启动等待最多 1 小时。每 60 秒采样；连续两次 MemAvailable <6 GiB 或磁盘 <20 GiB 则终止本任务。未借用 M1 的内存豁免，未改 workflow 文件或共享构建锁。

首次尝试（01）启动 MemAvailable `20,088,741,888 B`，load1 `1.8345` / 20 CPU，磁盘 `177,592,524,800 B`。cgroup 实测 memory.max=`6442450944`、memory.high=`5368709120`、cpu.max=`200000 100000`。专用 wrapper 在子进程结束后取得真实 GBS 退出码，并在自身尚处于 cgroup 时保存 memory.peak、memory.events、cpu.stat 和 ALL-END。

首次尝试的上述启动资源保留。过程异常与修正：

| 尝试 | 结果 | 证据/修正 |
|---|---|---|
| 01 | 主动停止，未完成；停止前约 642.27 秒，cgroup memory.peak `4,241,526,784 B`；未取得 GBS 数字退出码 | 原 spec 传 `-j2`，但 `tools/perf/Makefile:19` unexport MAKEFLAGS，`:27–31` 默认 JOBS=主机在线 CPU，`:65` 递归 `-j$(JOBS)`，日志实际为 `-j20`。停止本任务 unit，确认 GBS/depanneur/rpmbuild/make/clang 均已退出。原 result 中 running 是遗留状态，以另存的 stop-parallelism 收据为准，不补写成功或 ALL-END。 |
| 02 | wrapper 退出 1，GBS 未启动 | 尝试硬链接 root 所有缓存时 EPERM；完整错误和 ALL-END 保留。没有修改权限或安装软件。 |
| 03 | 主动停止，GBS `-15`，墙钟 `936.689711 秒`，未完成 | `_smp_mflags -j2 JOBS=2` 已使 perf 实际使用 -j2；进一步静态核对发现 RPM macros:184 也传该宏给 find-debuginfo.sh，其 :211–214 会将 JOBS=2 当作 BUILDDIR 并停止参数解析，因此在打包前停止。完整中断收据与 ALL-END 保留。 |
| 04 | **GBS 0，成功；4,047.180740 秒** | `_smp_mflags` 恢复纯 -j2，以 RPM `__spec_build_cmd` / `__spec_install_cmd` 在原脚本执行命令前加 `/usr/bin/env JOBS=2`，并行度环境覆盖同时作用于 perf build/install；不改变默认 script body 或 debuginfo 参数。新 root 仅复制已验证依赖缓存，不复用编译输出。 |

`JOBS=2` 是该 perf Makefile 文档明确支持的并行度覆盖（`:25`）。最终采用环境变量，而不是把它混入 _smp_mflags；已对固定 snapshot 的 RPM macros 做展开检查，build/install 为 `/usr/bin/env JOBS=2 /bin/sh -e`，debug 后处理不含 JOBS=2。该资源调度参数不修改 spec/defconfig 或编译优化选项。所有尝试均保留 16 GiB 启动门槛和原资源限额，01 的错误并行度曾发生，不能称整轮始终为两任务。

最终尝试 04 的真实收据位于 `logs-04/result.json`、`logs-04/ALL-END`，摘要与日志 SHA 见 [构建索引](03_k1a_base_kernel_build.index.json)。

| 最终尝试 04 | 实测 |
|---|---|
| GBS 退出码 / 墙钟 | **0 / 4047.180740 秒**（67 分 27 秒；不含约 4.6 秒缓存复制等准备） |
| UTC 起止 | wrapper 启动 2026-11-18 03:59:48；结束 05:07:20（主机时区均为 2026-11-17） |
| 启动门禁 | MemAvailable 19,953,070,080 B（18.58 GiB），load1 2.7090/20 CPU，磁盘 162,953,703,424 B；等待 0.0105 秒 |
| cgroup 内存峰值 | **5,372,125,184 B（5.003181 GiB）** |
| 最低主机 MemAvailable / 磁盘可用 | 18,786,455,552 B（17.50 GiB）/ 148,215,156,736 B |
| CPU | cgroup 累计 6098.587 CPU 秒；相邻资源采样区间最高 1.9915 核（非瞬时峰值） |
| memory.events | high=14579；max=0、oom=0、oom_kill=0；MemoryHigh 的软限制触发了回收/节流，未触发终止门禁 |
| 实际调度 | 抽查 GBS/rpmbuild/make/clang 共 11 个进程，全部 nice=19、I/O=idle；build/install 两次 perf 均打印 -j2，find-debuginfo 实际参数为纯 -j2 |

清理时 sudo 直接卸载被拒（`sudo: a password is required`）原文保留。核对主机 build 工具的 `--kill` 及 killchroot 实现后，使用其已有无密码授权的正式清理入口，仅针对本任务已中止的 01/03 root 清理；8 个遗留 proc/devpts/tmpfs 挂载已全部消失。04 的 GBS 正常清理，构建 cgroup 最终无进程，已停止退出后的 unit；没有本任务构建进程或挂载遗留，源码、产物与日志保留。

原样构建出现 PCIe `clkreq_cntl`、VC4 `txp_crtc`、brcmfmac 数组边界等编译警告，以及 bpftool/部分 devel 辅助工具缺 build-id 的打包警告。未据此修改源码；这些警告不等于已证实运行故障，运行影响未验证。内核 vmlinux 和全部模块的 build-id 已独立验证。

## 3. 配置、产物和二进制身份

普通版实际 `.config` 共 5,649 项；K defconfig 的 544 个显式要求全部一致（未出现在最终配置中的禁用项按 n 比较）。导出到 buildroot 的 spec 和 defconfig SHA 也与源仓库一致。配置 SHA-256 为 `62e3b8512d8bd4a336410a9468afd8c1ed338b9030dc69c754dbccf888617ba5`。

| 核对项 | 实际结果 |
|---|---|
| 编译器 | `CONFIG_CC_VERSION_TEXT="clang version 22.1.8"`，CLANG_VERSION=220108，CC_IS_CLANG=y；Linux banner 为 clang 22.1.8 / LLD 22.1.8 |
| LLVM 开关 | 实际 `%build` 日志执行 `export LLVM=1` |
| PMUv3 | `CONFIG_ARM_PMUV3=y` |
| Thumb2 | `# CONFIG_THUMB2_KERNEL is not set` |
| DWARF | DEBUG_INFO=y、DEBUG_INFO_DWARF4=y；原始 ELF 的 2,951 个编译单元版本全部为 4 |
| BTF / LTO | DEBUG_INFO_BTF=y、LTO_NONE=y |
| 实际编译命令 | 保存 `init/.main.o.cmd`，clang `--target=arm-linux-gnueabi -O2 -g -gdwarf-4`；没有 profile-use 参数 |

普通版离线身份：

| 产物 | 身份 |
|---|---|
| 未剥离 `vmlinux` build-id | `25599043a52ba8e5edf2f7bf4e9bb51aaf9d65a3` |
| `vmlinux` SHA-256 | `02bbef6771300aae8dfcb49ee1955a0ad8e1ebd80d47cc431d606a3163285411` |
| `zImage` SHA-256 | `6fe1818825307be9b1fdf52fbf0e55ba1d2cb013e655aee2e0136c9239f3f73e` |
| 原始 `Image` SHA-256 | `f5d8ce617088f4da098e04d24b68d7ec7396774c7c5bfd4b234365ac9a2ef1af` |
| `.debug_info` / `.BTF` | 215,081,476 / 6,478,326 bytes，均存在 |

核验按 K 的 `arch/arm/boot/Makefile:13,53–60` 和 `arch/arm/boot/compressed/Makefile:155–156` 展开：从 ELF 分节与 PT_LOAD 的装载地址重建 binary Image，逐字节相同；piggy_data 解 gzip 后也与 Image 完全相同；整个 piggy_data 唯一出现在 zImage 偏移 33353，Image 中包含同一 GNU build-id note。ARM32 zImage 解出的内核载荷是原始 Image，不假称它是 ELF。

初次核验脚本仅按 VMA 匹配 PT_LOAD，遇到 `.vectors` / `.vectors.bhb.*` 的相同 VMA、不同 LMA 得到假不一致；根据 readelf 的段/节映射补上文件 offset 匹配后完整字节比较通过。初次失败、修正脚本与通过收据均保留；未修改任何内核产物。普通版原始 vmlinux、System.map、config、Image/zImage、生成头已额外复制至 `prepackage/arm-rpi4/`，用于与最终归档交叉核验。

预期 `uname -r`：`6.12.80-arm-rpi4-v7l`；预期 `uname -v`：`#1 SMP Wed Nov 18 04:24:45 UTC 2026`。构建用户/主机为 `abuild@linhao-linux`，该 UTC 时间对应主机时区 2026-11-17。二进制中实际的完整 Linux banner（预期 `/proc/version`，末尾换行省略）：

```text
Linux version 6.12.80-arm-rpi4-v7l (abuild@linhao-linux) (clang version 22.1.8, LLD 22.1.8) #1 SMP Wed Nov 18 04:24:45 UTC 2026
```

全部二进制、RPM、原始日志与完整清单只保留在 `temp/kernel-afdo-k1/base-0fac5de6/`；Git 只记录报告、索引和 SHA。依赖索引见 [130 个 RPM 及固定仓库元数据](03_k1a_base_kernel_build.dependencies.json)。RPM/debuginfo 与模块身份核验结果如下。不能用源码提交或相同 uname-r 代替二进制 build-id；也不把旧采样 `395733b9…` 配对到本次构建。

### 3.1 RPM 与启动内核身份：明确的不一致边界

| 对象 | 普通版 build-id | RT build-id |
|---|---|---|
| 原始未剥离 vmlinux / zImage 内核 | `25599043a52ba8e5edf2f7bf4e9bb51aaf9d65a3` | `73d5a4a6dc10f70ed3db5eaab6fb0c58e1f846e9` |
| devel RPM 的剥离 vmlinux / 配套 vmlinux.debug | `f2a8fd676792328428c76ccc3b32e21206ead3ad` | `bfe85324f4a639bb38aa8a6528e338f6048f79b9` |

**RPM vmlinux.debug 的 build-id 不等于实际启动内核的 build-id。** 这是本次实际检测结果，不标成三者全一致。固定 snapshot 的 RPM macros 默认向 find-debuginfo 传 `--build-id-seed 6.12.80-0`，debugedit 在 BUILDROOT 内对 devel 副本重算 ID；源码构建目录及压缩的启动内核未被重写。两套 RPM devel ELF 与对应 debug ELF 的 ID 各自匹配，前者已无 .debug_info、后者含 .debug_info；devel ELF 除 `.notes` 外的所有有内容装载节，在地址、大小和内容 SHA 上均与原始 vmlinux 一致。

**后续内核 perf/llvm-profgen 使用 `artifacts/arm-rpi4/vmlinux` 这一份原始、带 DWARF 且 ID=25599043… 的 ELF。** 不将 RPM debug 文件当成它的同 build-id 替代品，不改 note 强制配对，也不配对旧样本 395733b9…。本轮保持原 spec/RPM 策略，不关闭 seed 来改变打包基线。

两套 RPM 的 zImage/zImage_rt 均与各自构建输出 SHA 相同；普通 RPM 的 RPi4 DTB 也相同。普通与 RT 各 52 个 `.ko`，共 104 个，均有 build-id；每个 installed/stripped RPM 模块与对应未剥离构建模块的 build-id 相同，文件 SHA 因剥离可不同。逐模块路径、两种 SHA 与 build-id 收入 [构建身份索引](03_k1a_base_kernel_build.index.json)。RT 同样 PMUv3=y、Thumb2=n、DWARF4=y，仅保留产物，未来部署不选择 RT。

### 3.2 产物索引与部署输入

- [完整身份、资源、RPM、模块与原始日志索引](03_k1a_base_kernel_build.index.json)。
- [1,971 个归档/核验普通文件的 SHA-256](03_k1a_base_kernel_build.artifacts.json)，涵盖未剥离 vmlinux、System.map、Image/zImage、DTB/overlays、全部模块、全部 RPM 及从 RPM 解出的检查副本。RPM 的 SHA 同时覆盖其文件元数据和符号链接。
- [130 个依赖 RPM 与 snapshot 元数据](03_k1a_base_kernel_build.dependencies.json)。依赖实体在 `dependencies/`，完整 buildroot 在 `gbs-root-04/`，原始外层及包日志在 `logs-04/` 和 `gbs-root-04/local/repos/tizen_unified_standard/armv7l/logs/`；前三次尝试原件保留。

普通版额外关键摘要：

| 文件（相对 artifact_root） | SHA-256 |
|---|---|
| `artifacts/arm-rpi4/System.map` | `b6251f41e505aaf140c69f5e8216375f0c58d25e0daa2d188e3f478bba0cb453` |
| `artifacts/arm-rpi4/arch/arm/boot/dts/broadcom/bcm2711-rpi-4-b.dtb` | `a0561668ec520b0605cdc8b7be6844365ce44f569f363e85f3d7332e1989d6ed` |
| `artifacts/rpms/arm-rpi4-linux-kernel-6.12.80-0.armv7l.rpm` | `347238446d41a552da28bf542c0aaa5e07145fdc20ca5ce18efdaffce4445440` |
| `artifacts/rpms/arm-rpi4-linux-kernel-modules-6.12.80-0.armv7l.rpm` | `1e30ee0d11e501982069014cf61bb32502bd9c40793e415a9dedaa34af91462d` |

两个普通部署 RPM 的 `rpm -qp --scripts` 输出均为空；RT 包含移动启动镜像的脚本，因此不能安装/卸载 RT 来切换普通版。源码 clone 最终 HEAD 仍为 K、工作树干净；额外保存的两套 prepackage 文件均与最终原始产物 SHA 相同。

## 4. RPi4 刷写方案（未执行，另需用户确认）

依据 [旧构建记录](../03_pmuv3_build_result.md)、[部署与回滚记录](../02_pmuv3_install.md) 和本次未修改的 K spec。旧脚本带旧 RPM SHA、uname 时间及板身份断言，**不能直接运行旧脚本部署本次 BASE**；后续获授权时先按本报告产物索引生成新的专用脚本并静态核验。M1 已完成是用户本轮提供的前提，不在本轮接板复核。

### 4.1 用户确认与预检

1. 用户明确确认安装本次 BASE、板为 RPi4、维护窗口及可用物理恢复手段；本轮构建授权不包括这些板上步骤。重新确认 serial、device-tree model、`uname -a`、`/proc/version`、当前运行 build-id、现装 kernel/modules RPM NEVRA、内核镜像及模块摘要。
2. 检查实际挂载、UUID、分区和 active slot。旧方案仅验证过 root p2、boot p1(vfat)、slot a；不同布局停止重新制定方案，不能照抄设备号。确认没有 RT 包、并行 RPM/FOTA 更新；根/boot 的可写性或空间不满足即停止，不自动 remount。
3. 对照包文件列表、脚本、SHA 和板上启动配置。普通包覆盖 `/boot/zImage`、`/boot/bcm*.dtb`（包括 `bcm2711-rpi-4-b.dtb`）、`/boot/overlays/*.dtb*`、`/boot/config.txt`、`start*.elf`、`fixup*.dat`、`LICENCE.broadcom`；modules 包覆盖 `/lib/modules/6.12.80-arm-rpi4-v7l/`。**config.txt 非 noreplace，必须事先比较并明确保留板上必要定制。**
4. 历史启动链为 config.txt 的 `kernel=u-boot.bin` → U-Boot/boot.scr 的 `kernel=zImage` → `bootz`。重新核对这条链及 cmdline；`cmdline.txt`、`boot.scr.uimg`、`uboot.env`、`u-boot.bin` 不属于本次两个包，不应被安装改变。不同链不能套用历史哈希。

### 4.2 备份与安装前门禁

1. 保存整个 boot 分区文件树、完整普通模块目录（含索引、符号链接和元数据）、挂载/UUID/slot、RPM 查询与验证输出、uname/version/运行 build-id。另准备**与当前安装完全匹配**的旧普通 kernel/modules 两个 RPM 并校验 SHA；不能默认旧 C 构建就是当前板的恢复包。
2. 如板上先暂存 `/tmp`，必须在任何安装前拉回主机的任务专用 backup，校验每个归档 SHA、可读性与文件清单。主机备份在验收及回退窗口结束前保留；不能把会随重启消失的 /tmp 当唯一备份。记录 `BACKUP_VERIFIED`，缺任一恢复输入即不安装。
3. 仅上传本次**普通 kernel 和普通 modules**两个明确文件，板上再次 SHA 校验；先 `rpm -Uvh --test --replacepkgs <kernel.rpm> <modules.rpm>`，成功才执行同样参数去掉 `--test`。禁止通配安装、`--force`、`--nodeps`、安装/卸载 RT 包。普通包脚本需用本次 `rpm -qp --scripts` 再核实；RT 的 post/preun 会移动启动镜像，不能借它切换内核。
4. 事务后核对 zImage、DTB/overlays、模块与索引；确认 config.txt 及固件已符合事先审阅的部署计划，U-Boot/环境/启动脚本/cmdline 保持预期。必要的 config 定制恢复必须由已审核方案明确列出，不能失败后即兴修改。`sync` 后停止在重启前；此时 uname 仍表示旧运行内核。
5. **用户自行重启并配置网络，再告知就绪。** 不自动 reboot；安装失败或启动前校验失败均停止，不自动回退。

### 4.3 用户重启后验收

以下是后续板上待执行命令意图，本轮未执行：

```sh
uname -r
uname -v
cat /proc/version
cat /sys/kernel/notes > running-kernel.notes
sha256sum /boot/zImage /boot/bcm2711-rpi-4-b.dtb
ls /sys/bus/event_source/devices/
readlink -f /sys/bus/platform/devices/pmu/driver
perf stat -e cycles:u -- sh -c 'i=0; while [ "$i" -lt 1000000 ]; do i=$((i+1)); done'
perf stat -a -e cycles:k -- sleep 3
```

实际 PMU sysfs 路径以已确认的设备树为准。`/sys/kernel/notes` 是原始 ELF note 流，并非 ELF 文件；拉回后按 ARM32 little-endian note 结构解析 GNU NT_GNU_BUILD_ID，与本次 vmlinux 的完整 ID 比较（不能直接对原始 notes 用 readelf 当 ELF）。核对 uname-r、完整 uname-v、编译器/主机/时间与本报告，磁盘 zImage SHA 和运行 build-id 都通过才能认定 BASE 已启动。模块按本次 manifest 校验，必要时通过各模块 `/sys/module/<name>/notes/.note.gnu.build-id` 验证加载实例。

在未来获授权拉回 `running-kernel.notes` 后，主机可用下面的离线命令作强断言（本轮未执行板上采集）：

```sh
python3 - running-kernel.notes <<'PYNOTES'
import struct, sys
from pathlib import Path
raw = Path(sys.argv[1]).read_bytes()
offset, ids = 0, []
while offset + 12 <= len(raw):
    namesz, descsz, kind = struct.unpack_from('<III', raw, offset)
    offset += 12
    assert offset + namesz <= len(raw)
    owner = raw[offset:offset + namesz].rstrip(b'\0')
    offset += (namesz + 3) & ~3
    assert offset + descsz <= len(raw)
    desc = raw[offset:offset + descsz]
    offset += (descsz + 3) & ~3
    if owner == b'GNU' and kind == 3:
        ids.append(desc.hex())
assert ids == ['25599043a52ba8e5edf2f7bf4e9bb51aaf9d65a3'], ids
print('RUNNING_BASE_BUILD_ID_OK', ids[0])
PYNOTES
```

PMU 必须绑定 armv8-pmu/A72 事件源，硬件 `cycles` 事件可用；两次 perf stat 返回 0、无 `<not supported>` / `<not counted>`，计数为正，且未回退 cpu-clock/task-clock 才通过。`cycles:k` 若无有效内核负载导致计数不足，应由 owner 选择明确的 syscall 基准再验收，不把零计数判成功。本轮不执行采样或生成 profile。旧方案允许 software-only 的“验收结束”标记，**不能作为本轮硬件 PMU 的通过条件**。

### 4.4 失败恢复原内核

- **板仍可访问：** 用户另行确认回退后，核对主机备份及匹配的旧两个普通 RPM，先恢复 RPM 包状态，再恢复归档内原 boot 和完整模块树（包括原配置），校验旧 zImage/模块 SHA 与启动链；不复制整套 RPM 数据库，不操作 RT。由用户再次重启，复核旧运行 build-id/uname、模块和原功能。
- **无法启动或无法联网：** 用户断电并取出 SD 卡接读卡器。按备份 UUID/容量确认卡与 boot/root 分区，先由用户安全卸载现有挂载，再在任务专用恢复目录挂载、恢复 boot 和模块；不能盲用主机 `/dev/sdX` 或覆盖其他磁盘。核对旧摘要、sync、卸载成功后用户装卡上电、恢复网络。离线恢复文件并未修复 RPM 数据库摘要；联网后再经授权用匹配旧 RPM 完成包状态恢复及定制复核。
- 物理取卡、断电/上电、重启、网络配置以及需要密码的主机挂载由用户确认/操作；任一步失败保留日志与现场，不继续自动修改。

## 5. 已验证与未验证

已验证：K 源码/spec/defconfig 身份；固定 snapshot 元数据、130 个安装依赖及 RPM SHA；真实 GBS 退出 0、资源限制/采样/结束收据；普通版配置；两套原始 vmlinux 的 DWARF4/build-id 与 zImage 载荷；普通板用 DTB；全部 104 个模块 build-id；全部 16 个 RPM 与原始日志保留；RPM devel/debug 的 ID 重算差异；文档中的 notes 解析命令已用本次 vmlinux 提取的原始 notes 离线验证；本任务进程/挂载清理完成。

未验证：板上安装/运行、实时 boot 布局与当前恢复包、运行时 build-id、模块加载、PMU cycles、备份恢复与物理回滚、性能、内存占用、编译警告的运行影响、AutoFDO 转换/重建、位级可复现构建。K1a 不包含 profile 采集或优化内核，不能以本次构建成功宣称上述结果已通过。下一步仅在用户另行确认后执行 §4 的部署预检/备份/安装，用户手动重启与配置网络后再验收。
