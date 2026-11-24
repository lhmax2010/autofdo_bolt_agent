# K1f-1e 共用模块树与符号排序重放

[证据索引](evidence/24-k1f-1e/index.json)

## 签名门禁与去除 BTF

K-BASE 的 `CONFIG_MODULE_SIG` 和 `CONFIG_SECURITY_LOCKDOWN_LSM` 未启用。`CONFIG_MODULE_SIG_FORCE`、`CONFIG_MODULE_SIG_ALL` 的依赖未满足，因此两项均未出现在归档 `.config`。52 个 RPM 模块与 6 个额外模块的 `modinfo -F sig_id` 均为空。先在 PLAT 读取运行态，再以原模块树启动 K-BASE 读取同一组接口，普通重启回 PLAT 后才写入。两个启动均为 `modules_disabled=0`，均未暴露 lockdown 和 sig_enforce 接口。签名强制门禁通过。 [主机签名清单](evidence/24-k1f-1e/signature-host.tsv) · [PLAT 运行态](evidence/24-k1f-1e/signature-plat.json) · [K-BASE 运行态](evidence/24-k1f-1e/signature-kbase.json)

采用冻结工具链的 LLVM objcopy 22.1.8。58 个模块均移除 `.BTF`。6 个外置模块另外含 `.BTF.base`，该节存放 split BTF 的基座描述，一并移除。未发现 `.BTF.ext`，共移除 **401,017 B** 的节载荷。逐个保存 `readelf -SW` 的前后输出，并按 ELF 节名称比较类型、标志、地址、链接与信息字段、对齐、条目大小和实际载荷。保留的节只有 `.shstrtab` 有字节变化。可执行代码、重定位、符号表与 `.strtab`、build-id note 均逐字节一致。58 个模块的 vermagic、srcversion、depends、sig_id 一致。以原 K-BASE `System.map` 执行 `depmod -b <staging> -e -F <System.map> 6.12.80-arm-rpi4-v7l-kbase`，退出 0，索引及其余 14 项普通文件 SHA 一致。原模块树保留于 K1d-c 主机归档。 [逐模块节差异及 SHA](evidence/24-k1f-1e/stripped-modules.json)

p6 写前两个目录的拓扑和逐文件 SHA 均匹配归档。在 2026-11-23 23:23:50 至 23:23:53 PST 的写入窗口，只替换任务目录 `/usr/lib/modules/6.12.80-arm-rpi4-v7l-kbase/` 下 58 个普通模块文件。每个 `.tmp` 保留原属主及权限，完成 fsync 和 SHA 核对后原子替换，随后读回 SHA。sync 后 p6 恢复 `ext4 ro,relatime`。只读复核 K-BASE 的 72 个文件均与新清单一致，PLAT 的 73 个原文件及目录拓扑均与原清单一致。 [替换读回](evidence/24-k1f-1e/p6-replaced-file-shas.txt) · [K-BASE 最终 SHA](evidence/24-k1f-1e/p6-kbase-stripped.sha256) · [PLAT 最终 SHA](evidence/24-k1f-1e/p6-plat-after.sha256) · [p6 挂载](evidence/24-k1f-1e/p6-mount-final.txt)

## 板上复验

**K-BASE 与 K-AFDO 均通过板上验收。** 两次直启均为 `armv7l`、`6.12.80-arm-rpi4-v7l-kbase`、`tryboot=1`。正式 cmdline 与 K1d-b 直启逐字节一致。FDT 经 dtc 反编译，排除 `kaslr-seed`、`rng-seed`、`rsts` 后逐字节一致，两次原始 rsts 均为 `0x20`。挂载布局、HDMI 连接、enlightenment、网络、dlog 与 D-Bus 均通过。

| 启动 | Build ID | 首条可用 sdb 命令 | 定向 disconnect / connect | 本次之后回 PLAT |
| --- | --- | ---: | ---: | ---: |
| K-BASE 签名检查，原模块树 | `96766cfcbff8c33d83ca38152ad02f6a02dd44d4` | 58.320 s | 2 / 2 | 75.420 s |
| K-BASE 复验，共用模块树 | `96766cfcbff8c33d83ca38152ad02f6a02dd44d4` | 58.181 s | 2 / 2 | 72.493 s |
| K-AFDO 完整验收，共用模块树 | `43ba5d455daec5da17e7521048767cdace012c91` | 58.551 s | 2 / 2 | 64.327 s |

两个变体均加载 10/10 个模块。模块列表与 PLAT 直启一致，`brcmfmac`、`brcmutil`、`btbcm`、`dm_bow`、`extcon_usb_fixed`、`hci_uart`、`inform_reboot`、`kdbus`、`logger`、`proc_tsm` 均来自已核对 SHA 的任务目录。运行态模块 build-id 与归档一致，vermagic 匹配。两次采样温度均为 58.426 °C。dmesg 无新增 Oops、BUG、WARNING、模块加载失败或 BTF 错误签名。告警级日志有既有类别的 journald 上次关闭、sdbd `oom_adj` 弃用，以及 audit 抑制计数。K-BASE 本次由 `extcon_usb_fixed` 首先触发 out-of-tree taint，参照由 `inform_reboot` 触发。 [K-BASE 验收](evidence/24-k1f-1e/kbase-direct-summary.json) · [K-AFDO 验收](evidence/24-k1f-1e/kafdo-direct-summary.json) · [K-BASE 日志差异](evidence/24-k1f-1e/kbase-direct-dmesg-warning-delta.txt) · [K-AFDO 日志差异](evidence/24-k1f-1e/kafdo-direct-dmesg-warning-delta.txt)

K-AFDO 以 `perf stat -a -e cycles:k,cycles:u,instructions:k -- sleep 5` 得到 **270,845,656 / 35,218,587 / 99,522,773**，三项计数覆盖率均为 100%。CPU3 单轮冒烟中，pipe 500,000 次 **12.444 s**，mmfault 64 MiB × 59 **9.649826 s**、966,660 个 minor faults，forkexec 12,774 次 **14.520811 s**。 [PMU 与冒烟收据](evidence/24-k1f-1e/kafdo-smoke-smoke.stdout)

最终回到 PLAT U-Boot 路径，build-id `395733b9c917cb98309b39cc3ec379c03ac36b3f`，`tryboot=0`，boot ID `47709bd0-ba29-4fe8-a8d7-a6133c7ecfa6`，原 cmdline SHA `1a132093c6e7220e981bd54c1a6a7bf780a19927c9787d3c9dcb7149eff106b4`，root off、UID 5001。boot_a 首尾 418 项 SHA 一致，原有 413 个文件均通过。任务试启动配置停在正式 `cmdline-afdo.txt` 与 `zImage-kafdo`。boot_a 剩余 1,374,208 B。 [PLAT 最终身份](evidence/24-k1f-1e/plat-final.json) · [boot_a 最终 SHA](evidence/24-k1f-1e/boot-a-final.sha256)

## K-BASE-S 符号排序文件重放

固定种子 `20261120`。解析 K-BASE map 中 `.text` 输出下所有 2,949 个非空输入节，用归档 ELF `.symtab` 的 `STT_FUNC` 地址匹配。2,937 个输入节有函数，各选一个代表。优先选在同一输入节唯一匹配的名字，再按符号绑定类型、地址及名字排序。6 个输入节只有同名候选，核对这些名字的所有定义均在 `.text` 的合格输入节内。先对 2,937 个代表记录洗牌，再按首次出现去重，得到 2,935 行。同名定义共用 LLD 优先级。12 个没有函数符号的输入节未列入。原始重复行探针引发 2 条重复名警告，去重保留首次排名。 [排序文件](evidence/24-k1f-1e/symbol-order.txt) · [生成器](evidence/24-k1f-1e/choose-order.py) · [LLD 22.1.8 排序实现](https://github.com/llvm/llvm-project/blob/llvmorg-22.1.8/lld/ELF/Writer.cpp#L1015-L1078)

使用 K-BASE relink-kit 的原始 Kbuild 对象、链接脚本和冻结 LLD 22.1.8。从空 kallsyms 生成输入，执行 `vmlinux1`、重生 BTF、第一和第二轮 kallsyms、`vmlinux2` 及最终链接。每次 LLD 均使用同一排序文件。使用冻结的 pahole 1.29 参数重生 detached BTF，装入归档 BTF ELF 对象的同一节。最终运行 `resolve_btfids`、生成 System.map、再运行 `sorttable`。System.map 与第二轮 kallsyms 输入逐字节相同。构建日志已有的 BPF kfunc 警告在重放中复现。最终三个 LLD 调用均为 0 警告，其中未找到符号为 0。排序文件 SHA-256 `6d8e0e7c632efed15d6169d6116eeeff8baa5b4ba57ab3d89e14f8f9de021b0c`。重放 ELF build-id `d7d426edd6618ac6078d8bd6d4706d8bf703bad5`。 [每步 argv](evidence/24-k1f-1e/relink-argv.jsonl) · [产物 SHA 与 LLD 结果](evidence/24-k1f-1e/relink-summary.json)

| 核对项 | 重放结果 |
| --- | --- |
| 输入节顺序 | `.text` 内 2,936 / 2,949 个非空节的相对序号改变，**99.56%**，无增减。其余输出节的共同非空输入顺序一致。 |
| 导出表与 CRC | 普通组 6,547 条，GPL 组 7,166 条。两组均严格按名称排列，CRC 与同槽符号及 `Module.symvers` 一一匹配。`module_layout` 的二分查找命中普通组索引 3905。 |
| initcall / setup / 参数 | 930 个 initcall 输入、3 个 console initcall 输入、97 个 `.init.setup` 输入和 166 个 `__param` 输入的顺序和集合一致。 |
| 异常与 unwind | `__ex_table` 最终 220 条全部排序且指向可执行指令。64,243 条 EXIDX 的 PREL31 目标严格递增。指令目标和 extab 指针均有效，保留两条合法结尾标记。55,659 条 mcount 地址已排序。 |
| idmap | 区间仍为 `0xc0200000–0xc020003c`，两项同处一个 4 KiB 页。`head.o` 和 `proc-v7.o` 两个输入节在区间内交换顺序。 |
| 冷热区 | 热区仍为空，边界 `0xc021b000`。冷区仍为 104,564 B、156 个输入节，成员一致。起止地址均后移 20 B，由 `0xc02013e8–0xc021ac5c` 至 `0xc02013fc–0xc021ac70`。 |
| ARM fixup | 17,769 条 SMP alternatives 指向可执行代码或 13 处已识别数据字段。13 处数据的符号、原值和替换值一致。344 条 PV 表记录的指令目标均有效。 |

该方案通过主机端静态验收。idmap 的内部顺序变化须在修正版实际首启中覆盖。 [全部输出节和 ARM 检查](evidence/24-k1f-1e/symbol-order-audit.json)

### 正式 GBS 构建方案

1. 在 0008 基础上新增可选宏 `kernel_vmlinux_symbol_order`，用 `%if 0%{?kernel_vmlinux_symbol_order:1}` 守住新增的 `Source2002` 声明及 `%build` 注入。GBS 输入携带已登记的符号排序文件，并核对 Source2002 内实际文件 SHA。由 spec 把 `--symbol-ordering-file=%{SOURCE2002}` 追加到现有 `KBUILD_VMLINUX_EXTRA_LDFLAGS` 路径。该变量在 0008 中只进入顶层 `LDFLAGS_vmlinux`，涵盖中间及最终 vmlinux 链接。用稳定 basename 归档，检查 GBS 内绝对路径可读。布局对照只定义此新宏。 [0008](patches/kernel/0008-packaging-opt-in-autofdo-and-link-flags.patch)
2. 构建前对照当前 0008 spec 与新 spec。在相同目标和冻结 RPM 宏环境中令三个可选宏均未定义，`rpmspec -P` 输出用 `cmp` 逐字节验收。启用排序的展开结果核对 Source、SHA 断言和最终输出。固定原 K-BASE 编译工具、snapshot、依赖、`.config`、`LOCALVERSION=-kbase` 与 KBUILD 构建身份。
3. 正式构建后逐对象比较编译 argv 与 K-BASE，并检查模块链接 argv。逐遍核对顶层 LLD 仅增加已锁定的 `--symbol-ordering-file` 参数。归档实际 argv、map、System.map、原始 vmlinux、zImage、模块 ABI 与 SHA。要求最终 System.map 与 kallsyms 收敛版本相同，导出表严格按名称排序、CRC 配对且 `module_layout` 可查，initcall、setup、param、异常表、unwind、idmap、冷热节边界及文本变化通过本节核对。复核版本和 modversion 一致，实际首启使用同一去除 BTF 的模块树，再验收 10 个模块、显示和服务。
4. 此方案仅在主机做重放验证。待 PM 决定后执行 spec 修改、正式 GBS 构建和修正版板上试启动。

## 控制台附件与停止点

尚未收到 K-BASE-S 的完整控制台日志文件。上一轮的用户故障描述原文已归档。 [K1f-1d 用户描述](evidence/23-k1f-1d/user-console-description.txt)

本轮共享主机 sdb 服务重启 0 次。完成主机重放和板上单轮冒烟后停在 PM 审核点。A/A 与正式比较尚未开始。
