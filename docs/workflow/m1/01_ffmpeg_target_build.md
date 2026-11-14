# M1 首项交付：FFmpeg目标构建（2026-11-14）

> 最新结果见第7节：RPi4已查询；Thumb基础设施中断，A32在configure阶段失败；RPi5用户周一确认后提供。第1–6节保留为第一次预检的历史记录。

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

[准备记录](evidence/01/source-prepare.json)、[原日志](evidence/01/source-prepare.log)。with_autofdo=1未构建；先前4项rpmspec语法展开的证据仍可引用[HQ修订spec解析](../../handover/evidence/03/spec-parse.json)，不把解析当作消费构建成功。

## 4. 三个变体与依赖存档

| 变体 | 状态 | 构建墙钟/退出码 | 编译参数、RPM、build-ID核对 |
|---|---|---|---|
| armv7l profile_isa=thumb | 未开始 | 不适用 | 未取得 |
| armv7l profile_isa=a32 | 未开始 | 不适用 | 未取得 |
| aarch64 | 未开始 | 不适用 | 未取得 |

未创建新的GBS buildroot，未生成正式目标配置，未执行GBS命令。待仓库选择完成后，配置采用[已核验的完整字段结构](../../handover/evidence/03/configuration-equivalence.json)，仅填入本任务最终仓库和独立tmpdir/buildroot。构建将使用正常全新root、-j4和10G/400% scope；启动MemAvailable≥14GiB，不查SwapFree；运行中连续两次低于3GiB终止本任务进程。现阶段没有可宣称“已验证”的完整构建命令或配置。

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

## 7. RPi4接通后恢复：ARM构建停止，AArch64等待周一

### 7.1 板子与仓库选择

用户通知RPi4接通后，通过已有端点建立主机SDB连接，再读取六项允许的信息。只读取model、uname -m/-r/-v、tizen-release和tizen-build.conf；没有开root、改governor、push、perf、挂载或任何板上写操作。先前空设备列表仅说明没有主机SDB连接，不证明板子断电。

| 项目 | RPi4实读 |
|---|---|
| model | Raspberry Pi 4 Model B Rev 1.5 |
| uname -m | armv7l |
| uname -r | 6.12.80-arm-rpi4-v7l |
| uname -v | #1 SMP Wed Nov 4 17:05:36 UTC 2026 |
| 镜像 | tizen-unified-toolchain_20261104.160709_tizen-headed-armv7l |
| TZ_BUILD_ID | tizen-unified-toolchain_20261104.160709 |

[命令、时间与传输退出码](evidence/02/board-check-02/queries.json)、[release原文](evidence/02/board-check-02/query-4.stdout)、[build配置原文](evidence/02/board-check-02/query-5.stdout)。SDB进程退出码为0；没有向受限的远端命令追加shell退出码标记，不把传输退出码冒充单独的远端退出码。

当前镜像snapshot 20261104.160709的packages目录与repomd.xml实时请求均404；按授权回退规则，ARM正式选用 **Unified 20261104.125239 / Base 20261030.120529**，没有配对偏离。可用元数据证据见第2节；当前镜像不可用的[请求原文](evidence/02/board-check-02/image-repo.json)和[正式选择记录](evidence/02/selection-armv7l.json)已保存。

用户最新答复：**RPi5的信息等周一确认后提供。**本轮不将RPi4镜像套给RPi5，不选择AArch64仓库、不启动AArch64构建。PMUv3提交结论仍为第5节：仅在sandbox找到，不能写成已合入accepted或当前内核的构建来源。

### 7.2 实际配置、命令与退出记录

完整无凭据配置：[ffmpeg-armv7l.conf](evidence/02/ffmpeg-armv7l.conf)。内容如下；WORKDIR展开为本项目绝对路径：

~~~ini
[general]
tmpdir = <WORKDIR>/temp/m1-target-20261114/gbs-tmp
profile = profile.tizen_unified_standard
buildroot = <WORKDIR>/temp/GBS-ROOT-FFMPEG-M1-THUMB-20261114

[profile.tizen_unified_standard]
repos = repo.base-standard, repo.unified-standard

[repo.base-standard]
url = https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261030.120529/repos/standard/packages/

[repo.unified-standard]
url = https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261104.125239/repos/standard/packages/
~~~

分别在新root执行正常GBS构建，无incremental/short-circuit；命令工作目录为temp/m1-target-20261114/ffmpeg：

~~~sh
gbs -c "$WORKDIR/temp/m1-target-20261114/ffmpeg-armv7l.conf" \
  build -A armv7l --spec ffmpeg.spec --include-all \
  --buildroot "$WORKDIR/temp/GBS-ROOT-FFMPEG-M1-THUMB-20261114" \
  --threads 1 --define '_smp_mflags -j4 V=1' --define 'profile_isa thumb'

gbs -c "$WORKDIR/temp/m1-target-20261114/ffmpeg-armv7l.conf" \
  build -A armv7l --spec ffmpeg.spec --include-all \
  --buildroot "$WORKDIR/temp/GBS-ROOT-FFMPEG-M1-A32-20261114" \
  --threads 1 --define '_smp_mflags -j4 V=1' --define 'profile_isa a32'
~~~

V=1只要求显示实际命令；没有修改补丁/spec。GBS环境隔离和实际绝对路径见[Thumb命令](evidence/02/build-thumb/command.json)、[A32命令](evidence/02/build-a32/command.json)。调用前验证源码/spec SHA、root不存在、MemAvailable≥14GiB；scope 10G/400%，nice19/ionice-c3，串行。

| 变体 | 起止时间（UTC−08） | 墙钟 | 真实GBS退出码 | 结论 |
|---|---|---:|---|---|
| Thumb | 04:34:45–04:38:28.704543 | 约223.7秒，人工停止前区间 | 未取得（null） | 监督进程丢失后停止自身scope；不计构建成功 |
| A32 | 04:38:51.756222–04:42:48.362540 | 236.606秒 | 1 | %prep/configure失败，未进入编译 |
| AArch64 | 未开始 | 不适用 | 不适用 | 等待用户周一提供RPi5信息 |

Thumb首次后台启动未进入worker；第二次GBS已启动，但外层启动命令结束后监督器和worker消失，GBS仍存活。原始进程/cgroup记录见[orphan-processes](evidence/02/build-thumb/orphan-processes.json)。这说明监督失效；未取得导致监督器消失的确切信号证据，不推断为OOM。只停止本任务Thumb scope，原root与日志保留，**没有重跑该变体**，结果JSON及日志明确记录真实退出码未知。初次启动说明见[launcher-note](evidence/02/launcher-note.txt)。A32改用独立systemd service监督其build scope，监督和60秒记录正常，真实退出码1。最终[三个单元均inactive/dead](evidence/02/units-final.txt)。

完整日志：[Thumb](evidence/02/build-thumb/build.log)、[A32](evidence/02/build-a32/build.log)；原始路径、字节数与SHA统一见[source-index](evidence/02/source-index.json)。日志均有带时间的“已结束”与ALL-END；Thumb不能补造GBS退出码。

### 7.3 A32失败原文与验收边界

A32日志原文：

~~~text
[  222s] Unknown option "--disable-thumb--extra-cflags=-mfpu=neon".
[  222s] See ./configure --help for available options.
[  222s] error: Bad exit status from /var/tmp/rpm-tmp.mplenp (%prep)
~~~

这里/var/tmp是WORKDIR内GBS构建root的路径，不是在宿主/tmp执行项目程序。补丁应用后spec第247行设置CONFIGURE_OPTIONS的--disable-thumb，第255行直接紧接--extra-cflags=-mfpu=neon，连接处缺分隔空格。[源码原文](evidence/02/spec-excerpt.txt)。这解释了此次A32实际报错；Thumb未到该阶段，不把同类推测写成Thumb已实测的失败原因。

日志可见CFLAGS展开包含-fdebug-info-for-profiling、-funique-internal-linkage-names、-marm，CC/CXX被设为clang/clang++，configure链接参数含-Wl,--build-id=sha1；**尚未出现目标源码编译命令，不能算选项编译生效验收通过**。两变体二进制RPM清单均为空：[Thumb](evidence/02/build-thumb/rpm-manifest.json)、[A32](evidence/02/build-a32/rpm-manifest.json)。没有可核对的libavcodec/libavutil runtime/debuginfo/build-id，没有profile消费验证。

用户要求“失败停止该变体，不修改patch/spec绕过”，因此本轮止于取证。patch/spec SHA与第3节完全相同，[核对记录](evidence/02/spec-unchanged.json)。with_autofdo=1仍只引用第3节已完成的rpmspec解析。后续若要修补示例，需要另行指令；当前HQ保持原样，不能把README的Not verified改成已验证。

### 7.4 实际依赖与存档

两个root均下载108个RPM，文件名/SHA集合完全相同，全部从选定Base下载，Unified来源0，未知来源0。逐包名称-版本-release-架构、URL和SHA见[Thumb归档清单](evidence/02/build-thumb/dependency-archive.json)、[A32归档清单](evidence/02/build-a32/dependency-archive.json)。这是实际下载的构建依赖，不是成功产物清单。

| 包 | 实际下载版本 |
|---|---|
| clang | 22.1.8-4.1.armv7l |
| clang-accel-x86_64-armv7l | 0.4-2.3.armv7l |
| gcc | 14.2.0-1.14.armv7l |
| binutils | 2.43-1.16.armv7l |

cmake/python3/ninja不在这108个RPM内，不虚列安装版本。clang RPM版本与发布llvm-profgen所基于的LLVM 22.1.8一致；尚未完成FFmpeg编译，不能据此声称profile消费兼容性已通过。

去重存档 **temp/gbs-deps-archive/ffmpeg-armv7l-20261114/**，108个RPM共 **271,003,299 B**，每份复制前后SHA一致，源缓存不变；另保留两个manifest和GBS解析后的buildconf。[archive-summary](evidence/02/archive-summary.json)列出manifest/buildconf SHA。不创建AArch64空存档冒充已下载。

后续把存档用作本地仓库的示例（本轮未执行元数据生成或离线重建，不声称已验证）：

~~~sh
archive="$WORKDIR/temp/gbs-deps-archive/ffmpeg-armv7l-20261114"
createrepo_c "$archive" # 仅使用已有工具，不安装
# 在WORKDIR内新建conf，general仍指定独立tmpdir/buildroot；
# profile=tizen_unified_standard，repos只设repo.ffmpeg-cache；
# [repo.ffmpeg-cache] url=file://<archive绝对路径>
gbs -c "$WORKDIR/temp/gbs/ffmpeg-armv7l-cache.conf" build -A armv7l \
  --spec ffmpeg.spec --include-all -D "$archive/tizen_unified_standard.conf" \
  --buildroot "$WORKDIR/temp/GBS-ROOT-FFMPEG-CACHE-NEW" \
  --threads 1 --define '_smp_mflags -j4 V=1' --define 'profile_isa a32'
~~~

必须先验证manifest、取得失败项处理授权并使用新的root；原样重建仍会遇到当前spec的configure错误。snapshot会删除，归档只保留这次解析结果，不能承诺覆盖后续变体新增依赖。

### 7.5 资源与停止状态

A32每60秒保存meminfo原文，最低MemAvailable **24,064,823,296 B**，cgroup实读memory.peak **2,010,705,920 B**，memory.events的max/oom/oom_kill均0；没有内存或磁盘门禁终止。[A32结果](evidence/02/build-a32/result.json)、[逐次资源](evidence/02/build-a32/resources.jsonl)。

Thumb监督失败期间60秒监测缺口如实保留：停止前实读cgroup峰值 **661,307,392 B**，不能宣称连续监测完整或缺口内最低可用内存已知。中断后没有重跑。归档两个轻任务峰值分别562,987,008 B、271,618,048 B，最低MemAvailable分别23,914,958,848 B、23,798,030,336 B，均退出0、OOM0。本轮上述有记录任务最高cgroup峰值2,010,705,920 B；不把scope峰值相加或冒充宿主峰值。

两构建已结束，scope无残留；所有root、失败日志、原证据保留。没有碰板上状态、安装板上RPM、读取真实profile、跑质量矩阵/性能测试或推送Gerrit。主机SDB服务仍沿用第6节记录的边界例外，不声称没有宿主工具日志。hq **498724fed8796da4190a458c01b95b9f65e334d5** 保持不变；Thumb与AArch64成功的更新前提尚未满足。下一步等待A32失败处理指令与周一RPi5信息。
