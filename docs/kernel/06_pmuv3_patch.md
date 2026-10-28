# ARM PMUv3 Gerrit 补丁

日期：2026-10-28。按用户后续澄清，**最新 tizen 基线仅修改普通 defconfig，一文件一行新增；RT 共用该配置并继承 PMUv3**。本轮没有运行 make、构建或启动新内核，没有向 Gerrit 推送。原手工安装方案已取消，scripts/pmuv3_install/ 保留为历史资料、不再使用。

补丁：[0001-ARM-configs-tizen_bcm2711-enable-ARM_PMUV3.patch](../../patches/0001-ARM-configs-tizen_bcm2711-enable-ARM_PMUV3.patch)。由用户合入 Gerrit 并发起 Quickbuild 生成新镜像。

## 1. 基线与旧镜像差异

- 在原源码树执行 `nice -n 19 ionice -c3 git -C src/linux-rpi fetch origin`，退出 0，输出为空；只更新远端引用/对象，未切换原工作树。
- fetch 后 `origin/tizen`：**`42aeefac58edeb081aff440f0b60be71cbe49755`**。
- 原工作树 HEAD 也为该提交；开始/结束 git status --porcelain 为空。没有修改原检出文件。
- 新 worktree：`temp/linux-rpi-pmuv3-gerrit`，分支 `afdo/pmuv3-gerrit`；本地内核提交：`2834afb2f85a6ef0905de18ed5b4a4ef7059635e`。
- 镜像基线：`21645b17c0d913e2ba7e10fbc9c993d286b3f57d`。

`git diff --numstat 21645b17c0d913e2ba7e10fbc9c993d286b3f57d origin/tizen -- arch/arm/configs/`：

```text
0	542	arch/arm/configs/tizen_bcm2711_rt_defconfig
```

唯一目录差异是删除旧 RT defconfig；普通 defconfig 在两个基线中完全相同。中间提交 `d5ef43b342dcbcbddb464bc20deae6ced6ed7193`（configs: packaging: modularize defconfig with RT and LSM fragments）将独立 RT 配置改为普通配置加片段。最新 HEAD 还包含 Hailo 驱动改动；不能把之前的镜像基线构建声称为对最新 HEAD 的构建验证。

旧镜像 21645b17 的 spec 使用独立 `tizen_bcm2711_rt_defconfig`（历史实际 RT 包未启用 PMUv3，见 [03](03_pmuv3_build_result.md)）；**最新 tizen 分支已改为普通 defconfig 叠加 rt.config**。因此按当前 spec/片段生成的新镜像，普通版和 RT 版都会启用 PMUv3。这是基于配置依赖与片段的静态结论，本轮没有生成新的 .config 或做板上验证。

## 2. 修改与菜单顺序

只在 `arch/arm/configs/tizen_bcm2711_defconfig:469` 加 `CONFIG_ARM_PMUV3=y`，放在 CONFIG_GENERIC_PHY=y 后、CONFIG_ANDROID_BINDER_IPC=y 前。以下行号均相对新 worktree、当前基线（defconfig 则含一行修改）：

- `drivers/Kconfig:196` 引入 drivers/phy/Kconfig，`:202` 引入 drivers/perf/Kconfig，`:208` 引入 drivers/android/Kconfig。
- `drivers/phy/Kconfig:8` 定义 GENERIC_PHY；现有 defconfig `:468` 为 CONFIG_GENERIC_PHY=y，后面的 `:470` 为 CONFIG_ANDROID_BINDER_IPC=y。
- 这是两个最邻近的、文件中已有的菜单配置项；中间 powercap/mcb 等菜单没有已列出的配置项。按 Kconfig 遍历顺序插入，而非放在文件开头 PROFILING 旁。
- 不运行 savedefconfig，不改 arm64、RT 片段、spec 或其他源码文件。

```diff
@@ -466,6 +466,7 @@ CONFIG_RASPBERRYPI_POWER=y
 CONFIG_PWM=y
 CONFIG_PWM_BCM2835=y
 CONFIG_GENERIC_PHY=y
+CONFIG_ARM_PMUV3=y
 CONFIG_ANDROID_BINDER_IPC=y
 CONFIG_ANDROID_BINDERFS=y
 CONFIG_DAX=y
```

## 3. RT 与所有可选叠加片段核对

`packaging/linux-rpi.spec:4` 定义共用配置名称；`:187` 设置 BASE_CONFIG；`:194`–195 给 RT 追加 `kernel/configs/rt.config %{?lsm_fragment}`；`:200` 执行 merge_config.sh，`:201` olddefconfig。LSM 选择位于 `:171`–178：dev_sel=1 使用 selinux.config，否则 dev_wos=1 使用 nosmack.config，否则不追加 LSM 片段。

逐行读取并搜索 `CONFIG_(PERF_EVENTS|HW_PERF_EVENTS|ARM_PMU|ARM_PMUV3|CPU_V7)`：三个片段 **均无设置或取消任何一项，无冲突**。完整片段证据如下（保留各文件行号，避免只凭 grep 空输出作结论）：

`kernel/configs/rt.config`：

```text
1: CONFIG_PREEMPT_RT=y
2: # CONFIG_RT_GROUP_SCHED is not set
```

`kernel/configs/selinux.config`：

```text
1: CONFIG_LSM_MMAP_MIN_ADDR=65536
2: CONFIG_SECURITY_NETWORK=y
3: CONFIG_SECURITYFS=y
4: CONFIG_NETLABEL=y
5: CONFIG_SECURITY_SELINUX=y
6: CONFIG_SECURITY_SELINUX_BOOTPARAM=y
7: CONFIG_SECURITY_SELINUX_BOOTPARAM_VALUE=1
8: CONFIG_SECURITY_SELINUX_DISABLE=y
9: CONFIG_SECURITY_SELINUX_DEVELOP=y
10: CONFIG_SECURITY_SELINUX_AVC_STATS=y
11: CONFIG_SECURITY_SELINUX_CHECKREQPROT_VALUE=0
12: CONFIG_DEFAULT_SECURITY_SELINUX=y
13: CONFIG_DEFAULT_SECURITY="selinux"
14: # CONFIG_DEFAULT_SECURITY_SMACK is not set
15: # CONFIG_SECURITY_SELINUX_POLICYDB_VERSION_MAX is not set
16: # CONFIG_SECURITY_SMACK is not set
```

`kernel/configs/nosmack.config`：

```text
1: CONFIG_SECURITY=y
2: CONFIG_SECURITY_NETWORK=y
3: CONFIG_NETLABEL=y
4: # CONFIG_SECURITY_SMACK is not set
5: # CONFIG_SECURITY_SMACK_APPEND_SIGNALS is not set
6: # CONFIG_DEFAULT_SECURITY_SMACK is not set
7: CONFIG_DEFAULT_SECURITY_DAC=y
8: CONFIG_DEFAULT_SECURITY=""
```

## 4. 依赖条件（静态核查；未执行 make）

普通版与 RT 使用同一基础文件，前述三个片段不覆盖该依赖链：

| 条件 | 文件:行号与依据 |
|---|---|
| ARM=y | arch/arm/Kconfig:2–4，ARM 默认 y |
| PROFILING=y | arch/arm/configs/tizen_bcm2711_defconfig:33 |
| HAVE_PERF_EVENTS=y | arch/arm/Kconfig:128，ARM select HAVE_PERF_EVENTS |
| PERF_EVENTS=y | init/Kconfig:1899–1902，依赖 HAVE_PERF_EVENTS，default y if PROFILING |
| MMU / ARCH_MULTI_V7 / CPU_V7 | arch/arm/Kconfig:318–320，MMU 默认 y；arch/arm/Kconfig.platforms:42–46，ARCH_MULTI_V7 默认 y 并 select CPU_V7；基础 defconfig 没有取消这些项 |
| ARM_PMU=y | drivers/perf/Kconfig:6–7 的菜单依赖 PERF_EVENTS；:58–61 依赖 ARM/ARM64，default y |
| HW_PERF_EVENTS=y | arch/arm/Kconfig:1275–1277，def_bool y，依赖 ARM_PMU |
| ARM_PMUV3 可启用 | drivers/perf/Kconfig:146–149，HW_PERF_EVENTS && ((ARM && CPU_V7) || ARM64)，default ARM64；此次显式 y |

驱动匹配依据：`drivers/perf/arm_pmuv3.c:1383` 包含 arm,cortex-a72-pmu；`drivers/perf/arm_v7_pmu.c:1947`–1959 的匹配表没有 A72。`arch/arm/boot/dts/broadcom/bcm2711.dtsi:436` 的 PMU compatible 为 arm,cortex-a72-pmu，`:470` 等 CPU 节点为 arm,cortex-a72。

## 5. 其他 32 位 Tizen 配置清单

执行 `git ls-tree -r --name-only origin/tizen arch/arm/configs/ | rg '/tizen_'`（两项退出 0），完整结果只有一个文件：

| 文件 | 目标 | ARMv8 核心 | 本补丁 |
|---|---|---|---|
| arch/arm/configs/tizen_bcm2711_defconfig | BCM2711 / RPi4（spec:10–14；defconfig:34–35 启用 BCM 家族） | **是，Cortex-A72，AArch32 内核** | 加一行 |

最新基线没有其他 `arch/arm/configs/tizen_*` 文件，因此没有额外 A53/A72 配置可交给用户选择。旧 tizen_bcm2711_rt_defconfig 已删除，不把已删除文件或 arm64 配置列成现存 32 位候选。不扩展本补丁范围。

## 6. 提交说明全文

```
ARM: configs: tizen_bcm2711: enable ARM_PMUV3

The BCM2711 Cortex-A72 PMU is matched by arm_pmuv3 through the
arm,cortex-a72-pmu entry in drivers/perf/arm_pmuv3.c. The arm_v7_pmu
match table has no Cortex-A72 entry. ARM_PMUV3 defaults to ARM64 in
drivers/perf/Kconfig, leaving the driver disabled in the 32-bit build.
The current armv7l image consequently has no hardware perf events
and its device-tree PMU node has no bound driver.

Enable ARM_PMUV3 in the 32-bit BCM2711 defconfig. The RT variant is
generated from the same defconfig plus kernel/configs/rt.config, so
it inherits this option. Leave the arm64 configuration unchanged.

An ordinary kernel was previously built from the running image's
source baseline, 21645b17c0d913e2ba7e10fbc9c993d286b3f57d. Comparing
all 5649 configuration values with that image's devel RPM found only
CONFIG_ARM_PMUV3 changing from disabled to y. See the project report
docs/kernel/03_pmuv3_build_result.md in lhmax2010/autofdo_bolt_agent.
This patch on the latest tizen baseline has not been built or booted.

Change-Id: I2f00e4cca847dae70fb9e99f3948ed3df699f05f
Signed-off-by: Hao Lin <hao.lin@samsung.com>
```

现有仓库 commit-msg hook 自动加了 Change-Id，保留用于本补丁的 Gerrit 提交流程；没有推送 Gerrit。Signed-off-by 为最后一条 trailer。

## 7. 验证结果

- `git diff origin/tizen..afdo/pmuv3-gerrit --stat`：

```text
 arch/arm/configs/tizen_bcm2711_defconfig | 1 +
 1 file changed, 1 insertion(+)
```

- `git format-patch -1 --stdout` 生成交付补丁。
- 另建独立、干净的 `temp/linux-rpi-pmuv3-am-check` detached worktree，起点为同一最新基线；应用前 git status --porcelain 为空。
- `git am /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/patches/0001-ARM-configs-tizen_bcm2711-enable-ARM_PMUV3.patch` 返回 0：

```text
Applying: ARM: configs: tizen_bcm2711: enable ARM_PMUV3
```

- 应用后 status 为空；`git diff --exit-code afdo/pmuv3-gerrit HEAD` 返回 0，应用结果树完全一致。日志在 temp/pmuv3-gerrit/am_*.txt。
- 额外 checkpatch 默认模式报告 1 error、0 warning，仅是“Remove Gerrit Change-Id's before submitting upstream”。本补丁目的地是 Gerrit，因此保留 Change-Id；使用 `--no-tree --ignore GERRIT_CHANGE_ID` 再查返回 0，0 errors、0 warnings。原始输出都保留在 temp/pmuv3-gerrit/checkpatch*.txt，不声称默认检查无错误。
- 本机缺 flex，本轮没有调用 make、savedefconfig、配置生成或任何编译。先前已构建的是镜像精确基线的普通内核；其最终 5,649 个配置项只改变 ARM_PMUV3，引用 [03_pmuv3_build_result.md](03_pmuv3_build_result.md)。最新补丁/RT 新镜像的动态验证由用户 Quickbuild 后再做。

补丁 SHA-256：`620c35409023bfcf881cafb8a91c20d84a26d625e6d14dc8aba644a32a4ca55e`。
