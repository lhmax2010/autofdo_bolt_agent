# M2b 阶段 A · 插桩 PGO 方法与运行时核查

依据 workflow v0.3 §3、§9、§11、§14 M2b 与 §16 第 5 项。本阶段只做主机实现、元数据核查和测试。上板、正式 GBS 构建、训练和性能测量留待 PM 审核后的阶段。

## PM 决定（2026-11-25）

1. 同一冻结依赖、源码、补丁和 spec 下比较 BASE、AFDO、PGOGEN、PGO。AFDO 用 M1 RPi4 或 M2a RPi5 已锁定的 profile 及其 SHA，重建参考变体，不重新采样。M1 的 profile SHA 为 `bab0130ccf4b72952092cfbdcd0c19b820bb2e85cb7843d9ecff667225be8485`，M2a 为 `db4d4c196cde3afb20803580ed5317d83a7d4a95f0d8f830c5394f1536b99d5a`。编译及链接均通过 FFmpeg configure 传入 `-fprofile-generate`，PGO 编译使用 `-fprofile-use=<锁定 profdata>`。
2. ToS 720p 上以 PGO 对 BASE 为主，PGO 对 AFDO 为次；Sintel 1080p 补充两组比较。各组单独预试定 N、锁定种子和计划，沿用 M1 配对、ε=1%、四种判定、遥测与标记失衡规则。不做多重比较校正。
3. 先 RPi5 AArch64，RPi4 ARMv7 Thumb-2 在内核轨道 K1f-3 完成后进行。
4. BBB 720p 训练三次，与既有 FFmpeg 训练管线相同。采集使用 `LLVM_PROFILE_FILE=<run dir>/%m-%p.profraw`；准备与插件扫描单独存放。合并只读取本代、正常退出的 decoder 进程生成的清单成员。
5. PGOGEN 要求每个目标 DSO 有已定义的 profile runtime，训练每轮覆盖两目标 DSO，退出 0。原始和索引格式由已锁定的 llvm-profdata 读取并记录版本。PGO 构建的诊断需在预登记上限内，两个声明热目标 DSO 的 `.text` 有变化，记录函数覆盖率。首次 PGO 构建前由 PM 确认上限。PGOGEN 和 PGO 命令差异只允许各自声明的 profile 选项。
6. 完成配对计时后，按 preflight 的事件清单在 ToS 上对 BASE、AFDO、PGO 做独立的只计数运行。报告 cycles、instructions、L1I refill、L1I TLB refill、分支误预测和可用的前端停顿指标。事件无读数标记不可用，机制计数不参与判定。

## 固定快照与依赖

从 Base `20261030.120529` 和 Unified `20261104.125239` 实时获取共享 repomd、primary 和 filelists。两个 repomd 返回 HTTP 200。四个索引文件按各自 repomd 的 SHA-256 校验。用 filelists 的 pkgid 关联 primary 中的架构、版本、RPM 和包 SHA。[元数据与依赖证据](evidence/runtime-and-dependencies.json)

| 架构 | 仓库与 provider | 文件 | Clang |
| --- | --- | --- | --- |
| armv7l | Base `compiler-rt-22.1.8-4.1.armv7l` | `/usr/lib/clang/22/lib/linux/libclang_rt.profile-arm.a` | `clang-22.1.8-4.1.armv7l` |
| aarch64 | Base `compiler-rt-22.1.8-4.1.aarch64` | `/usr/lib64/clang/22/lib/linux/libclang_rt.profile-aarch64.a` | `clang-22.1.8-4.1.aarch64` |

两种架构的 Clang 与 runtime 均为同一 `22.1.8-4.1` 和同一 LLVM 源码修订，Unified 未见对应 provider。两个架构门禁通过。这一结论来自仓库包元数据。

FFmpeg spec 以固定源码 5fe76358 及原 profiling 补丁为基础制作 `profiling-pgo.patch`。保留 ARM NEON、ISA 和 SHA-1 build-id。两种架构用已验证的 Tizen `rpmspec` 查询原 BASE、独立 PGOGEN，以及加入共有依赖宏的四种正式变体。相对原 BASE，PGOGEN 唯一新增直接 BuildRequires 为 `compiler-rt = 22.1.8-4.1`。代码要求四种变体使用同一依赖并集，解析、构建走原有共享锁。

| 架构 | 既有冻结 RPM 数 | 元数据推导的新增包 | 预期新集合 |
| --- | ---: | --- | ---: |
| armv7l | 108 | compiler-rt | 109 |
| aarch64 | 109 | compiler-rt | 110 |

上表结合固定快照 primary 中的 Provides 与封存安装清单。compiler-rt 的全部 RPM Requires 在各自旧冻结集合中已有提供者；实际 GBS 解析和离线验证留给后续执行。本轮 `rpmspec -P` 也展开了两种架构的 PGOGEN/PGO spec。原始 XML、归档 SHA 与执行器原文保存在 WORKDIR 下 `temp/m2b-stage-a/metadata/` 和 `temp/m2b-stage-a/spec/`。

## 实现与门禁

| 阶段 | PGO 工作流 |
| --- | --- |
| init / preflight | `init --method pgo` 写入方法及缺项。live 在接板前要求 `afdo_profile` 的绝对路径和 SHA、确认过的 `pgo_warning_limits`。沿用主机及板子门禁，并保存各机制事件的可用性。 |
| build / deploy | 同一冻结依赖下构建 BASE、PGOGEN，检查编译和链接开关、目标 DSO 中定义的 runtime 符号及全部部署库的 build-id。两变体与 PLAT 做独立正确性核对。 |
| collect / convert | 每轮分离 registry/插件扫描，记录退出、唯一 decoder PID 及带 SHA 的 raw 清单。核对 profile magic、llvm-profdata 版本读数、build-id 和函数记录。只把逐项验过的清单路径交给 merge。计算每个目标 DSO 的已执行和可插桩函数数，拒绝归属歧义。 |
| rebuild | BASE-r 重建核对，AFDO 用旧锁定 profile 并走原消费审计，PGO 使用新锁定索引。核对 chroot 内 SHA、编译诊断上限和目标 DSO `.text`；复用构建锁比较。板上测量前准备正确性 oracle。 |
| measure / report | 两组比较复用同一配对测量、重试、遥测和统计函数，各输入保存独立计划。完成计时及 post-oracle 后分别保存机制计数。报告同时呈现两组结果及诊断计数。 |
| status / explain | `status` 显示 PGO 变体、比较组和现有 PGO 证据。 `explain STAGE --method pgo` 和 dry-run 展示方法对应的门禁、输入及产物。 |

两种警告上限均无默认值。首次 PGO 构建前需要 PM 确认 `profile-instr-unprofiled` 与 `profile-instr-out-of-date` 的允许计数。真实 PGOGEN 包、profile runtime 在板上 DSO 中的输出、构建诊断和前端事件可用性都要在后续阶段以实测验收。未修改 M1/M2a 封存运行。


## 主机验收

- 新增 18 项 PGO 测试，覆盖每个 DSO 的 runtime 见证、profile 清单和 PID、异常退出、版本和 build-id、拒绝通配路径及未登记成员、构建锁额外选项、消费警告上限与 `.text` 变化、两组配对计划、报告和 CLI。PGOGEN 静态链接会把 runtime 对象自己的编译记录带进 `.GCC.command.line`。审计保存原始命令集合与 runtime 归档 SHA，只按已锁定 RPM 所属归档中的逐项精确匹配识别运行库记录；其他额外选项仍导致失败。
- 主机 x86_64 合成冒烟使用两个插桩 DSO、三个正常退出的进程和六份真实 profraw，在发布版 llvm-profdata 上通过读取、身份校验及精确清单合并。读到的 raw 版本字段为 `0x010000000000000a`（格式版本 10，带 IR 标记），indexed 版本为 13；两 DSO 各覆盖 1/1 函数。[合成冒烟证据](evidence/native-profdata-smoke.json)
- RPi5 草稿 `m2b-ffmpeg-rpi5-aarch64-01` 的 `init --method pgo`、`run --dry-run`、`status`、`explain rebuild --method pgo` 均通过；三份媒体 SHA 已核对。清单列出四个变体、两组比较和九个阶段。待绑定的实机输入包括身份、构建和工具锁、快照证据、种子、M2a AFDO profile 锁和 PM 警告上限。草稿没有创建阶段收据。[RPi5 草稿证据](evidence/rpi5-draft.json)
- 完整工作流回归 241/241 通过（既有 223 项、新增 18 项，无跳过）；两个板上脚本通过 `bash -n`。release 全树核查覆盖 102 个文件及 21 个相对链接，违规数为 0。两分支的 `SKILL.md` 逐字节一致。
- M1 attempt-11 回放 48 项全部通过，包含既有采集、构建、转换命令与收据字段。[M1 回放证据](evidence/m1-replay.json)

本轮停止在阶段 A。PM 确认两个警告上限并审核实现后，阶段 B 先做 RPi5 上的实际冻结、构建、训练与测量验收。

## 阶段 B PM 决定（2026-11-25）

阶段 A 的全局警告计数上限被以下按编译单元的规则替代。RPi5 job 的 `pgo_warning_policy` 锁定了这份规则。

1. `profile-instr-out-of-date` 在包配置声明的目标库编译单元中必须为 0。非目标编译单元只记录。目标库出现此警告时，构建锁失败。
2. `profile-instr-unprofiled` 记录总数和完整清单，无总量上限。使用发布版 `llvm-profdata show --topn=20` 按最大内部块计数确定前 20 个函数。用 PGOGEN 原始对象中编译器写入的 `__llvm_prf_names` 把函数精确关联到对象和编译单元。20 个函数的编译单元都须在 PGO 构建中得到核对；任何一个出现在 unprofiled 清单中均失败。
3. `profile-instr-missing` 与其他 profile 诊断只记录，包括 IR 后端单独报告的告警。警告审计保留诊断选项、原文、构建日志行号及归属。
4. PGO 的 GNU make 输出按目标串行写入日志，编译仍用 `-j2`；此设置只用于保全编译单元与诊断的对应。编译器选项仍由既有构建锁审计。缺失或歧义的热函数来源，以及无法核实归属的两类受控诊断，会作为证据不完整阻断审计。
5. 本轮要求 BASE-r 与 BASE 两个目标库的运行文件 SHA、调试文件 SHA 和 build-id 均一致，审计通过才进行非计时 oracle。许可只到 `--stop-after rebuild`。

RPi5 新 serial 为 `192.168.108.13:26101`，以型号、架构、镜像和内核四项标识断言身份。[阶段 B 执行记录](02_rpi5_execution.md)
