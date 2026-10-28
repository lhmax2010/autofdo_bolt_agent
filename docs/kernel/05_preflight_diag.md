# 安装预检失败的只读诊断

日期：2026-10-28（Asia/Shanghai）。**判定 A：两个普通内核包都没有出现在板上的 RPM 数据库中，现有模块目录也没有 RPM 归属，符合内核/模块随镜像直接写入而非当前 RPM 管理的状态。** 本轮不追溯镜像制作/刷写的具体工序，不把“未注册于 RPM”扩大成对历史安装过程的证明。

## 结论与限制

- `rpm -q arm-rpi4-linux-kernel`、`rpm -q arm-rpi4-linux-kernel-modules` 均原样返回 `package ... is not installed`，真实远端退出码均 **1**；指定 queryformat 再查也同样为 1。
- RPM 全集关键词筛选只找到 firmware-update-system-ui、firmware-update-system-ui-common、util-linux；未找到另名/RT 内核、模块、RPi、U-Boot 或 bootloader 包。rpm -qa 与 grep 的退出码分别为 **0、0**。
- 模块目录和 modules.dep 的 rpm -qf 均返回 `is not owned by any package`，退出码 **1**；`ls -la /lib/modules/` 可见 6.12.80-arm-rpi4-v7l 目录。
- `/boot` **未挂载**：awk 返回 0、输出为空。没有挂载，没有查询 /boot 文件归属/哈希；因此没有解出旧 zImage，也无法判断板上启动文件与旧 RPM 是否逐字节一致。
- 运行内核为 `6.12.80-arm-rpi4-v7l`，`uname -v` 为 `#1 SMP Thu Oct 22 06:42:32 UTC 2026`；当前命令行是 `bootmode=normal partition_ab=a`。
- 本机两个旧 RPM 均为 `6.12.80-0.armv7l`，VCS 为镜像基线 `platform/kernel/linux-rpi#21645b17c0d913e2ba7e10fbc9c993d286b3f57d`。它们的 **BUILDTIME 原始值均为 0**，date 格式显示 1970-01-01，不能用来验证 2026-10-22 的内核编译时间；见第 4 节。

上轮预检要求两个包已安装且 VERSION-RELEASE.ARCH 都等于 6.12.80-0.armv7l；本轮证据说明先决条件“已安装”就不成立。不是已经发现了不同版本/架构（B），不是只缺一个（C），也未发现另名包（D）。仅报告状态，不提出或实施安装方案修改。

## 1. 采集方式与身份

工作目录为 `/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent`。原始字节形式的 SDB stdout/stderr 与完整执行包装保存在 `temp/pmuv3-diag/queries.json`，执行记录在 `probe.log`；本报告转录所有请求的原始输出，仅统一 CRLF，并把 device-tree model 的 NUL 显示为 `[NUL]`。空输出明确写为空，没有截掉错误文字。

每条远端命令在子 shell 结束后立即读取 `$?` 并追加 `__AFDO_DIAG_RC__<退出码>`，以这个真实退出码判定；同时记录 SDB transport exit。SDB shell 将板上 stdout/stderr 合并到传输输出，故不伪称板上 stderr 单独为空；下列“SDB stderr”仅指本机客户端 stderr。没有把非零查询退出当成执行器故障或安装授权。

远端包装形式：

```sh
( 原查询命令 )
r=$?
printf '\n__AFDO_DIAG_RC__%s\n' "$r"
exit "$r"
```

RPM 全集筛选额外在 rpm 一侧向 stderr 写 `__RPM_QA_RC__`，外层标记仍记录 grep/管线退出码；没有依赖默认管线退出码推断 rpm 是否成功。完整包装见下文。

```sh
sdb connect 192.168.108.26
```

原始输出：

```text
192.168.108.26:26101 is already connected
```

主机退出码：**0**。

stderr：空。

```sh
cat /proc/device-tree/model
```

原始输出：

```text
Raspberry Pi 4 Model B Rev 1.5[NUL]
```

真实远端退出码：**0**；SDB transport exit：0。

SDB stderr：空。

```sh
id -u
```

原始输出：

```text
0
```

真实远端退出码：**0**；SDB transport exit：0。

SDB stderr：空。

板上已有 root（id -u=0），本轮没有再切换账户模式。

## 2. 板上包查询与文件归属

```sh
rpm -q arm-rpi4-linux-kernel
```

原始输出：

```text
package arm-rpi4-linux-kernel is not installed
```

真实远端退出码：**1**；SDB transport exit：0。

SDB stderr：空。

```sh
rpm -q arm-rpi4-linux-kernel-modules
```

原始输出：

```text
package arm-rpi4-linux-kernel-modules is not installed
```

真实远端退出码：**1**；SDB transport exit：0。

SDB stderr：空。

```sh
rpm -q --qf '%{NAME} %{VERSION}-%{RELEASE}.%{ARCH} %{BUILDTIME:date} %{VCS}\n' arm-rpi4-linux-kernel
```

原始输出：

```text
package arm-rpi4-linux-kernel is not installed
```

真实远端退出码：**1**；SDB transport exit：0。

SDB stderr：空。

```sh
rpm -q --qf '%{NAME} %{VERSION}-%{RELEASE}.%{ARCH} %{BUILDTIME:date} %{VCS}\n' arm-rpi4-linux-kernel-modules
```

原始输出：

```text
package arm-rpi4-linux-kernel-modules is not installed
```

真实远端退出码：**1**；SDB transport exit：0。

SDB stderr：空。

```sh
rpm -qa --qf '%{NAME} %{VERSION}-%{RELEASE}.%{ARCH}\n' | grep -i -E 'kernel|linux|rpi|u-boot|firmware|bootloader'
```

原始输出：

```text
firmware-update-system-ui 1.2.13-0.armv7l
util-linux 2.41.2-1.6.armv7l
firmware-update-system-ui-common 1.2.13-0.armv7l
__RPM_QA_RC__0
```

真实远端退出码：**0**；SDB transport exit：0。

SDB stderr：空。

上项实际加低优先级和组件退出码的包装如下，`__RPM_QA_RC__0` 是采集标记，不是包名：

```sh
(
(nice -n 19 ionice -c3 rpm -qa --qf '%{NAME} %{VERSION}-%{RELEASE}.%{ARCH}\n'; r=$?; printf '__RPM_QA_RC__%s\n' "$r" >&2; exit "$r") | grep -i -E 'kernel|linux|rpi|u-boot|firmware|bootloader'
)
r=$?
printf "\n__AFDO_DIAG_RC__%s\n" "$r"
exit "$r"
```

```sh
rpm -qf /lib/modules/6.12.80-arm-rpi4-v7l
```

原始输出：

```text
file /lib/modules/6.12.80-arm-rpi4-v7l is not owned by any package
```

真实远端退出码：**1**；SDB transport exit：0。

SDB stderr：空。

```sh
rpm -qf /lib/modules/6.12.80-arm-rpi4-v7l/modules.dep
```

原始输出：

```text
file /lib/modules/6.12.80-arm-rpi4-v7l/modules.dep is not owned by any package
```

真实远端退出码：**1**；SDB transport exit：0。

SDB stderr：空。

## 3. /boot、运行内核与模块目录

```sh
awk '$2=="/boot"' /proc/mounts
```

原始输出：

```text
(空输出)
```

真实远端退出码：**0**；SDB transport exit：0。

SDB stderr：空。

**未挂载。** 按本轮指令跳过 `rpm -qf /boot/zImage /boot/config.txt /boot/u-boot.bin` 与 `sha256sum /boot/zImage /boot/config.txt`，不访问未挂载目录来代替真实启动分区，不执行任何 mount。

```sh
uname -r
```

原始输出：

```text
6.12.80-arm-rpi4-v7l
```

真实远端退出码：**0**；SDB transport exit：0。

SDB stderr：空。

```sh
uname -v
```

原始输出：

```text
#1 SMP Thu Oct 22 06:42:32 UTC 2026
```

真实远端退出码：**0**；SDB transport exit：0。

SDB stderr：空。

```sh
cat /proc/cmdline
```

原始输出：

```text
cgroup_enable=memory vc_mem.mem_base=0x3ec00000 vc_mem.mem_size=0x40000000 swiotlb=8192 8250.nr_uarts=1 dma.dmachans=0x7f35 bcm2709.serial=0xed6687d3 snd_bcm2835.enable_compat_alsa=0 snd_bcm2835.enable_hdmi=1 bcm2709.uart_clock=48000000 dwc_otg.lpm_enable=0  bootmode=normal partition_ab=a console=ttyS0,115200n8 earlycon=uart8250,mmio32,0xfe215040 loglevel=4 
```

真实远端退出码：**0**；SDB transport exit：0。

SDB stderr：空。

```sh
ls -la /lib/modules/
```

原始输出：

```text
total 156
dr-xr-xr-x  6 root root   4096 Oct 22 20:10 .
dr-xr-xr-x 85 root root 106496 Oct 27 16:17 ..
drwxr-xr-x  4 root root   4096 Oct 22 20:10 6.12.80-arm-rpi4-v7l
drwx------  2 root root  16384 Oct 22 20:09 lost+found
drwxr-xr-x  2 root root   4096 Oct 22 20:10 modprobe.d
drwxr-xr-x  2 root root   4096 Oct 22 20:10 modules-load.d
```

真实远端退出码：**0**；SDB transport exit：0。

SDB stderr：空。

## 4. 本机旧 RPM 比对

以下 rpm -qp 只读取 WORKDIR 内两个既有旧包；没有读取外部项目文件，没有下载或安装。

```sh
rpm -qp --qf '%{NAME} %{VERSION}-%{RELEASE}.%{ARCH} %{BUILDTIME:date} %{VCS}\n' /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-verify/baseline/arm-rpi4-linux-kernel-6.12.80-0.armv7l.rpm
```

原始输出：

```text
arm-rpi4-linux-kernel 6.12.80-0.armv7l Thu Jan  1 08:00:00 1970 platform/kernel/linux-rpi#21645b17c0d913e2ba7e10fbc9c993d286b3f57d
```

主机退出码：**0**。

stderr：空。

```sh
rpm -qp --qf '%{NAME} %{VERSION}-%{RELEASE}.%{ARCH} %{BUILDTIME:date} %{VCS}\n' /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-verify/baseline/arm-rpi4-linux-kernel-modules-6.12.80-0.armv7l.rpm
```

原始输出：

```text
arm-rpi4-linux-kernel-modules 6.12.80-0.armv7l Thu Jan  1 08:00:00 1970 platform/kernel/linux-rpi#21645b17c0d913e2ba7e10fbc9c993d286b3f57d
```

主机退出码：**0**。

stderr：空。

```sh
rpm -qp --qf '%{NAME} BUILDTIME=%{BUILDTIME}\n' /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-verify/baseline/arm-rpi4-linux-kernel-6.12.80-0.armv7l.rpm
```

原始输出：

```text
arm-rpi4-linux-kernel BUILDTIME=0
```

主机退出码：**0**。

stderr：空。

```sh
rpm -qp --qf '%{NAME} BUILDTIME=%{BUILDTIME}\n' /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-verify/baseline/arm-rpi4-linux-kernel-modules-6.12.80-0.armv7l.rpm
```

原始输出：

```text
arm-rpi4-linux-kernel-modules BUILDTIME=0
```

主机退出码：**0**。

stderr：空。

时间比对：

| 来源 | 时间/数值 | 解释 |
|---|---|---|
| 旧 kernel RPM BUILDTIME | 0；Thu Jan 1 08:00:00 1970 | 本机 +08:00 对 Unix epoch 的 date 显示 |
| 旧 modules RPM BUILDTIME | 0；Thu Jan 1 08:00:00 1970 | 同上 |
| 板上 uname -v 编译时间 | Thu Oct 22 06:42:32 UTC 2026 | 北京时间 2026-10-22 14:42:32 |

两种时间 **不对应**。BUILDTIME=0 没有提供可用于比对的真实打包日期；没有据此认定旧 RPM 不匹配，也没有声称确认了某种归零策略。VCS/包版本与镜像基线一致只说明本机包的元数据来源，不能代替板上 zImage 的哈希验证。

zImage 比对状态：**未执行 / 未知**。触发条件“/boot 已挂载且取得 zImage 哈希”不成立，所以未从旧 RPM 提取镜像；不以先前缓存文件或 uname 相同冒充本轮哈希对应结论。

## 5. 范围与停止

本轮仅执行上述板上只读查询及主机 RPM 头读取，未修改/推送任何板上脚本，未重跑 02，未安装/卸载、挂载/remount、重启、备份或采样。前轮 `/tmp/afdo_probe/` 的脚本保持原样，未清理。安装方案与脚本均不修改。

已完成本轮诊断，停止等待用户指示；不自动恢复此前安装授权。

边界记录：历史 `/tmp/sdb.log` 仍为 400 B，mtime `2026-10-28 12:01:10.724948977 +0800`，与前轮一致（`temp/pmuv3-diag/boundary.txt`）。无新增已知工作区外写入；没有进行全系统调用审计。
