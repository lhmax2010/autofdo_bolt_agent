# K1f-1c FDT 复判、K-BASE-S 诊断重试与 K-AFDO 首启

终态 **RECOVERY_REQUIRED**。报告记录本轮已取得的验收和回程证据。

[证据索引](evidence/22-k1f-1c/index.json) · [FDT 比较脚本](evidence/22-k1f-1c/fdt-compare.py) · [K-BASE 回溯收据](evidence/22-k1f-1c/known-good.json)

## FDT 规则补充与 K-BASE 回溯

依据 PM 决定，规范化比较排除 `/chosen/kaslr-seed`、`/chosen/rng-seed` 和 `/chosen/bootloader/rsts`。原始 FDT 和 rsts 保留在各 boot 收据。其他属性逐字节比较。仅诊断启动按 PM 的 cmdline 豁免，把同一命令行在 `/chosen/bootargs` 中的副本一并归为 cmdline，记录原值和差异。正式 K-AFDO 启动仍严格比较该属性。

K1f-1b 归档的 K-BASE build-id 为 `96766cfcbff8c33d83ca38152ad02f6a02dd44d4`。参考 rsts 为 `0x20`，观测为 `0x1020`，按新规则两份 DTS 的 SHA-256 均为 `74f40dd34b8b23c6355718f70e36cc98cba5c0fd6dfd10e617f29d24924589d2`。其余验收已通过，K-BASE 判定为已知良好，复用原证据。

## K-BASE-S 一次诊断 tryboot

发令前核对了 PLAT build-id、U-Boot、tryboot=0、原始 cmdline 和 UID 5001。

boot_a 的诊断发布逐文件比对原 413 项。正式 cmdline 无 `quiet`，诊断版只追加 `console=tty1 loglevel=8 ignore_loglevel`。tryboot 指向 `zImage-kbase-s` 与 `cmdline-diag.txt`。原子发布和只读读回通过。板上没有 diff 工具，主机对拉回的原始字节生成 diff 并核对。 [cmdline 差异](evidence/22-k1f-1c/cmdline.patch) · [tryboot 差异](evidence/22-k1f-1c/tryboot.patch)

发令时间 `2026-11-23T22:27:46.648-08:00`，定向 disconnect 1 次、connect 0 次。
第 180 秒附近，ICMP 2 次均未响应，TCP 探测仍在 SYN-SENT。
到 **300.000 s** 未取得新 boot ID，进入 `RECOVERY_REQUIRED`。

现场 HDMI 未取得用户描述。


## K-AFDO 正式 cmdline 首启

未发起该次 tryboot。

## 最终状态

最后一次只读读回记录 boot_a 为 419 项，空闲 **1,234,944 B**。诊断配置仍在，tryboot 指向 `zImage-kbase-s` 和 `cmdline-diag.txt`。PLAT 回程和最终 UID 等待现场断电上电后核验。

本轮共享主机 sdb 服务重启 **0** 次。A/A 和布局测量均未启动。
