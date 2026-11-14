# M1 首项交付：FFmpeg目标构建预检（2026-11-14）

## 1. 停止点

**两次sdb devices均为空，尚不能查询RPi4/RPi5当前镜像。三个变体未启动构建；本轮只完成主机准备和只读取证。**

已向用户请求设备可查询信息。不能把历史板况当作当前板况，也不能把“当前镜像未知”视为“同镜像snapshot已不可用”从而跳过首选规则。待两板可查询后，先运行用户允许的model/uname/tizen-release或build-ID读取，再按规则正式选择仓库。没有执行sdb connect、root、push、挂载或任何板上命令。

| 对象 | model / uname / 镜像build ID | 原因 |
|---|---|---|
| RPi4 | 未知 | 主机SDB列表无设备 |
| RPi5 | 未知 | 主机SDB列表无设备 |

原文：[第一次设备列表](evidence/01/sdb-devices.txt)、[第二次设备列表](evidence/01/sdb-devices-second.txt)。

## 2. Snapshot只读核查（候选，不是正式选择）

实时读取Base目录并逐个读取packages目录和repodata/repomd.xml，全部返回HTTP 200且元数据可解析：

| Base固定ID | packages | repomd |
|---|---|---|
| 20261013.024319 | 200 | 200 |
| 20261030.061318 | 200 | 200 |
| 20261030.120529 | 200 | 200 |
| 20261109.032334 | 200 | 200 |
| 20261111.130848 | 200 | 200 |

用户指定回退Unified **20261104.125239** 的目录/元数据也均为200。**仅当首选镜像snapshot无法使用时**，依规则对应Base为**20261030.120529**（不晚于该Unified且通过检查的最新Base）。本轮未正式选用。

候选完整URL：
- Base：https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261030.120529/repos/standard/packages/
- Unified：https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261104.125239/repos/standard/packages/

两候选仓库的primary.xml.gz实际下载并按repomd的SHA-256校验；Base包含armv7l/aarch64/x86_64的clang **22.1.8-4.1**，VCS为platform/upstream/llvm#f999bd406c0a70fe8107aa992164fe6945c5d46a。Unified的文件表没有clang包。这只是仓库可供版本，尚无实际依赖解析/安装，不能声称构建使用了该版本。

[请求时间/HTTP/退出码/摘要](evidence/01/snapshot-requests.json)、[目录清单](evidence/01/snapshot-candidates.json)、[clang版本](evidence/01/candidate-clang.json)、[大文件路径与SHA](evidence/01/raw-index.json)。元数据位于packages/repodata，共享多架构；目标架构确实在primary中。

## 3. 源码与补丁准备

- 独立检出：temp/m1-target-20261114/ffmpeg。
- 基线：platform/upstream/ffmpeg，5fe76358596f66e955f005094e6f34ca525ab23d。
- 补丁取自已审阅hq提交498724fed8796da4190a458c01b95b9f65e334d5中的examples/ffmpeg/profiling.patch，用git show读取原字节。
- patch SHA：297133bda02da82f55c6007b3bd6e4e3391176596162dfb7b068f7d2d191416c。
- git apply --check及应用均成功；spec SHA：10d7930c0f7f2a2772bd04798ad49a5b551636b2ccabda069ea5d90f89923878。
- 仅此新检出的packaging/ffmpeg.spec有补丁预期修改；没有改patch/spec绕过问题，src及此前检出未动。未下载或打开正式profile。

[准备记录](evidence/01/source-prepare.json)、[原日志](evidence/01/source-prepare.log)。with_autofdo=1未构建；先前4项rpmspec语法展开的证据仍可引用[HQ修订spec解析](../../../handover/evidence/03/spec-parse.json)，不把解析当作消费构建成功。

## 4. 三个变体与依赖存档

| 变体 | 状态 | 构建墙钟/退出码 | 编译参数、RPM、build-ID核对 |
|---|---|---|---|
| armv7l profile_isa=thumb | 未开始 | 不适用 | 未取得 |
| armv7l profile_isa=a32 | 未开始 | 不适用 | 未取得 |
| aarch64 | 未开始 | 不适用 | 未取得 |

未创建新的GBS buildroot，未生成正式目标配置，未执行GBS命令。待仓库选择完成后，配置采用[已核验的完整字段结构](../../../handover/evidence/03/configuration-equivalence.json)，仅填入本任务最终仓库和独立tmpdir/buildroot。构建将使用正常全新root、-j4和10G/400% scope；启动MemAvailable≥14GiB，不查SwapFree；运行中连续两次低于3GiB终止本任务进程。现阶段没有可宣称“已验证”的完整构建命令或配置。

没有实际下载的构建依赖RPM，因此未生成ffmpeg-armv7l-20261114或ffmpeg-aarch64-20261114依赖存档；仅保留仓库元数据。依赖包版本清单、RPM/library SHA、SHA-1 build-ID与debuginfo一致性均待构建后核查。本轮不修改hq的Not documented yet / Not verified条目。

## 5. PMUv3提交只读查询

在temp/m1-target-20261114/kernel-query独立clone/fetch，未更新src/linux-rpi。远端refs完整清单保存；内容历史实际查询以下五分支：

| 分支 | 当前tip | CONFIG_ARM_PMUV3修改提交 |
|---|---|---|
| tizen | 42aeefac58edeb081aff440f0b60be71cbe49755 | 未找到 |
| tizen_dev | 8158e5b0ed5ac74a80099d5e1af2f8f5b67e612a | 未找到 |
| accepted/tizen_unified | 42aeefac58edeb081aff440f0b60be71cbe49755 | 未找到 |
| accepted/tizen_unified_toolchain | 42aeefac58edeb081aff440f0b60be71cbe49755 | 未找到 |
| sandbox/lhmax2025/kernel_optimization | b11f669e0cb1c1e26d878430b998d6486c5476a1 | **0fac5de6a63091d141ad1cd3ed9d9e92b8dde708** |

找到的提交标题ARM: configs: tizen_bcm2711: enable ARM_PMUV3，在arch/arm/configs/tizen_bcm2711_defconfig加CONFIG_ARM_PMUV3=y；author日期2026-10-28 16:13:43 +08:00，commit日期2026-10-28 17:56:15 +08:00。上述sandbox tip包含该设置；其余四分支tip均没有此设置。

这证明提交已进入远端sandbox，**不证明已进入tizen/accepted**，也不能据此推断当前板上镜像。其他远端分支仅ls-remote列举，不宣称查完其历史。[分支/提交结果](evidence/01/pmuv3-query.json)、[原始提交diff](evidence/01/pmuv3-0fac5de6a63091d141ad1cd3ed9d9e92b8dde708.patch)、[完整refs](evidence/01/kernel-heads.txt)。

## 6. 资源、边界与交付状态

所有命令串行nice19/ionice-c3、3G/100%用户scope、启动前MemAvailable≥4GiB。元数据下载解析有实时监测，peak 21,495,808 B、采样最低MemAvailable 23,939,182,592 B，无OOM/资源停止；这不是全部短查询scope的全时峰值。[监测结果](evidence/01/metadata-result.json)。未启动重任务。

第一次sdb devices自动启动了主机SDB服务（端口26099），原始输出已保留。没有设备连接，也未发送任何板上命令。SDB服务可能写宿主默认日志；具体路径和是否产生新文件本轮未取得证据，不宣称为零，未读取/删除工作目录外文件。用户需使设备可查询后继续。

读取构建监督器时一次路径拼写使用build-worker.py而实际为build_worker.py，退出2；随后按正确路径只读读取。一次过宽temp文件名扫描遇到旧root权限错误，主动终止本任务该rg进程，未改变原文件。二者均不是GBS构建失败。

main本轮仅登记预检、阻塞和证据。hq未修改/未推送；不推任何Gerrit分支、不安装软件、不改设计与既有证据、不删除既有temp目录。恢复前提是两板可读查询，或用户明确修订首选snapshot规则。
