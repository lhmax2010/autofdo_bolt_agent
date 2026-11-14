# M1 首项交付：FFmpeg目标构建（2026-11-14）

> 最新结果见第9节：去掉V=1、-j2及独立资源监督下，Thumb/A32均构建成功，RPM身份与DWARF核对通过；hq已更新，待PM审阅。此前失败记录和证据保留。

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

## 8. 授权修正fix1与两变体构建（2026-11-14，失败停止）

### 8.1 只改新增两行，其他源码/spec保持原样

PM授权在补丁新增的--disable-thumb与--enable-thumb之后各补一个空格。新文件为temp/m1-target-20261114/profiling-fix1.patch；原文件、原检出、旧buildroot全部保留。

~~~diff
-+CONFIGURE_OPTIONS="$CONFIGURE_OPTIONS --disable-thumb"
++CONFIGURE_OPTIONS="$CONFIGURE_OPTIONS --disable-thumb "
-+CONFIGURE_OPTIONS="$CONFIGURE_OPTIONS --enable-thumb"
++CONFIGURE_OPTIONS="$CONFIGURE_OPTIONS --enable-thumb "
~~~

| 文件 | SHA-256 |
|---|---|
| 原profiling.patch | 297133bda02da82f55c6007b3bd6e4e3391176596162dfb7b068f7d2d191416c |
| profiling-fix1.patch | 0c94e54d252ad1ecbc625f629af090b257edba4cd3753d76352fd031486243b6 |
| 新检出应用后的spec | 0e611e7eb95ada2c024dbea379821c5b109383f1545bcb0c86ef85f238740c27 |

[新补丁](evidence/03/profiling-fix1.patch)、[精确diff](evidence/03/fix1/patch-diff.txt)、[两行断言](evidence/03/fix1/patch-validation.json)。其余新增内容逐项检查：CFLAGS附加值前有空格；profile_flags各选项分开；profile_use作为独立CFLAGS项；CC/CXX不是选项字符串拼接；extra-ldflags为独立configure参数。未发现另一处同类粘连，不作额外修改。[检查记录](evidence/03/fix1/patch-review.json)。

在全新temp/m1-target-20261114/ffmpeg-fix1检出5fe76358596f66e955f005094e6f34ca525ab23d，git apply --check与git apply均退出0。完整命令和SHA见[准备记录](evidence/03/fix1/source-prepare.json)、[原日志](evidence/03/fix1/prepare.log)。构建结束后重新核验新旧patch/spec均未变化，[最终核对](evidence/03/final-source-check.json)。

### 8.2 构建命令、退出码与错误归因

沿用ffmpeg-armv7l.conf，SHA 2bc10fa0e93c9d094481129a9bc88f32974d44eeff2635cba2eef8a2fcf966b7；Unified20261104.125239 / Base20261030.120529不变。全新root分别为：

- temp/GBS-ROOT-FFMPEG-M1-THUMB-20261114-FIX1
- temp/GBS-ROOT-FFMPEG-M1-A32-20261114-FIX1

实际执行的GBS命令如下，工作目录为ffmpeg-fix1；没有incremental/short-circuit：

~~~sh
gbs -c "$WORKDIR/temp/m1-target-20261114/ffmpeg-armv7l.conf" \
  build -A armv7l --spec ffmpeg.spec --include-all \
  --buildroot "$WORKDIR/temp/GBS-ROOT-FFMPEG-M1-THUMB-20261114-FIX1" \
  --threads 1 --define '_smp_mflags -j4 V=1' --define 'profile_isa thumb'

gbs -c "$WORKDIR/temp/m1-target-20261114/ffmpeg-armv7l.conf" \
  build -A armv7l --spec ffmpeg.spec --include-all \
  --buildroot "$WORKDIR/temp/GBS-ROOT-FFMPEG-M1-A32-20261114-FIX1" \
  --threads 1 --define '_smp_mflags -j4 V=1' --define 'profile_isa a32'
~~~

**上述V=1放置方式是执行器错误，不是推荐命令。**它由本任务执行器沿用上一轮命令引入，不是PM要求，也不是补丁新增内容。第7节“V=1只要求显示实际命令”的判断被本次日志证伪：_smp_mflags还进入find-debuginfo.sh，该脚本把V=1当作路径。因此不能将本轮打包失败归咎于修正版补丁。

两变体串行由独立systemd service监督，每个构建scope 10G/400%、nice19/ionice-c3、启动MemAvailable≥14GiB，60秒保存meminfo/cgroup峰值。没有使用上一轮失效的nohup方式。[监督启动证据](evidence/03/fix1/supervisor-start-proof.txt)、[监督脚本](evidence/03/fix1/build_supervisor.py)、[构建脚本](evidence/03/fix1/build_worker.py)。

| 变体 | 起止时间（UTC−08） | 墙钟（秒） | GBS退出码 | 结果 |
|---|---|---:|---:|---|
| Thumb | 05:26:02.446061–05:30:51.033144 | 288.587 | 1 | 已编译/链接，调试包处理失败 |
| A32 | 05:30:51.117642–05:35:39.820129 | 288.702 | 1 | 已编译/链接，同样失败 |

两变体实际构建墙钟合计577.289秒（约9分37秒，不含收尾取证）。精确起止与真实退出码以[Thumb结果](evidence/03/fix1/build-thumb/result.json)、[A32结果](evidence/03/fix1/build-a32/result.json)为准；GBS及scope退出码均为1。每份日志有带时间的“已结束/失败”和ALL-END。两变体失败后都未重试、未进一步修改补丁/spec。

共同失败原文（完整行号分别见[Thumb摘录](evidence/03/fix1/build-thumb/failure-excerpts.txt)、[A32摘录](evidence/03/fix1/build-a32/failure-excerpts.txt)）：

~~~text
+ /usr/lib/rpm/find-debuginfo.sh -j4 V=1 --build-id-seed 8.0.1-1 ... -S debugsourcefiles.list ...
/usr/lib/rpm/find-debuginfo.sh: line 241: V=1/debugsources.list: No such file or directory
/usr/lib/rpm/find-debuginfo.sh: line 242: V=1/debugfiles.list: No such file or directory
error: Could not open %files file .../debugsourcefiles.list: No such file or directory
~~~

另有独立诊断，不能遗漏：

~~~text
/usr/lib/rpm/debugedit: ...libavcodec.so.62.11.100: Unknown debugging section .debug_line_str
/usr/lib/rpm/debugedit: ...libavcodec.so.62.11.100: DWARF version 5 unhandled
~~~

libavutil也有同类DWARF5诊断。后续候选处理是让_smp_mflags只包含-j4，把verbose设置放在只影响make的环境/参数中；这是执行器修正方向，本轮不执行重建。debugedit兼容性仍须核查，不能承诺移除V=1后一定成功，也不能修改spec去绕过当前诊断。根据本轮失败门禁，保留原件后停止。

### 8.3 编译参数核对与未完成的产物验收

从每个完整日志提取实际clang命令，以最后出现的-mthumb/-marm核对有效ISA（平台optflags可能先含-mthumb）。每侧560条libav系列C源码编译命令均包含两项profiling选项；libavcodec/libavutil各保存2条完整原文。

| 变体 | 实际C编译命令 | profiling两项 | 有效ISA | 编译参数核对 |
|---|---:|---|---|---|
| Thumb | 560 | 全部包含 | -mthumb | 通过（限C编译命令） |
| A32 | 560 | 全部包含 | -marm | 通过（限C编译命令） |

[Thumb结果](evidence/03/fix1/build-thumb/compile-validation.json)及[原文](evidence/03/fix1/build-thumb/compile-excerpts.txt)；[A32结果](evidence/03/fix1/build-a32/compile-validation.json)及[原文](evidence/03/fix1/build-a32/compile-excerpts.txt)。

每侧另有54条手写.S的clang汇编命令，没有上述CFLAGS中的profiling选项或显式-mthumb/-marm；不将它们冒充C编译参数通过，不声称Thumb库全部是Thumb代码。[Thumb汇编命令](evidence/03/fix1/build-thumb/assembly-excerpts.txt)、[A32汇编命令](evidence/03/fix1/build-a32/assembly-excerpts.txt)。第一版日志检查错误地对C和.S统一断言，退出1；修正检查器后分开报告，原失败日志和两个检查器都保留。只修取证脚本，没有修改构建参数、补丁或重跑构建。

两root的二进制RPM清单均为空：[Thumb](evidence/03/fix1/build-thumb/rpm-manifest.json)、[A32](evidence/03/fix1/build-a32/rpm-manifest.json)。因此**打包后的libavcodec/libavutil SHA-1 build-id与debuginfo一致性尚未验收**；不以构建中间产物代替。无成功RPM/library SHA清单。AArch64与with_autofdo=1消费构建本轮均未启动。

### 8.4 原件、依赖、资源与交付状态

完整构建日志各超过1MB，保留在temp/m1-target-20261114/fix1/build-{thumb,a32}/build.log，不进git。SHA：

- Thumb：59cf7a4e76babb1e02546683f0f0281d21322bbc21ae7ea459cfa0fa28658183
- A32：a29525e1989e9eb90a4ca7f82dec68ec3c31f9d6504012bc02adfe6cb5d31f5f

所有证据路径、大小、SHA见[source-index](evidence/03/source-index.json)。本次108个依赖与先前归档集合相同，仍为271,003,299 B；复制核验完成，新增manifest-fix1-thumb.json与manifest-fix1-a32.json，旧manifest不改。[归档摘要](evidence/03/archive-summary.json)。

| 变体 | 最低MemAvailable（B） | cgroup memory.peak（B） | max / oom / oom_kill |
|---|---:|---:|---|
| Thumb | 21,003,026,432 | 2,200,326,144 | 0 / 0 / 0 |
| A32 | 21,004,312,576 | 2,222,645,248 | 0 / 0 / 0 |

没有资源门禁暂停或终止；每60秒原始meminfo和resources.jsonl已保存。收尾取证峰值566,599,680 B、退出0，早先检查器退出1原文同时保留。[构建与监督单元全部inactive/dead](evidence/03/units-final.txt)。新worker所需的fix1/gbs-tmp目录在启动后补建，GBS当时仍处于正常导出/元数据阶段；配置指向的原gbs-tmp始终存在，日志没有因此失败，时间顺序不隐瞒。

本轮只修改main报告/STATUS并添加新证据，不改既有证据、设计、原patch/spec/root，不操作任何开发板、不查询RPi5、不推Gerrit、不读profile。hq更新前提未满足，保持498724fed8796da4190a458c01b95b9f65e334d5，未替换hq补丁、未新增配置、未将任何Not verified改为已验证。完成失败取证后停止，等待构建执行器与打包诊断处理指令。

## 9. 周末无人值守J2重建（2026-11-14，成功完成）

### 9.1 历史成功构建的只读核查

未构建前检查temp/eval-prep11/build/ffmpeg-thumb-S.log与ffmpeg-a32-S.log，两份都出现8条debugedit诊断：4条“DWARF version 5 unhandled”及4条“Unknown debugging section .debug_line_str”，涉及libavcodec、libavutil、libswresample、libswscale。两日志最终均GBS_EXIT 0、ALL-END OK，历史报告11也保存了成功RPM；这些诊断当时非致命，不据诊断文本直接推断本次失败。

旧编译命令CFLAGS有-g2、-gdwarf-4及-g；.S采用独立汇编选项-g。只读旧打包libavcodec调试ELF，readelf记录每侧325个DWARF4 CU、52个DWARF5 CU，退出0。没有对旧产物作任何修改，也没有读取profile。[历史日志摘录/原件SHA/命令/DWARF计数](evidence/04/historical-check.json)。

| 工具 | 历史成功构建 | 本轮依赖 | 是否相同 |
|---|---|---|---|
| clang包 | 22.1.8-1.6.armv7l | 22.1.8-4.1.armv7l | 上游版本同22.1.8，release不同 |
| debugedit所属rpm-build | 4.14.1.1-1.9.armv7l（以历史日志为准） | 4.14.1.1-1.9.armv7l | 包版本号相同，包及程序字节不同 |

旧缓存中另有rpm-build的1.8包，不将其当作历史本次日志使用的1.9包。只把指定RPM中的debugedit提取到本任务目录比SHA，没有安装/运行旧工具；旧root/cache只作本步骤取证，不用于新构建。

- 历史1.9 debugedit SHA：dc4b5b156b83034d301e3031bfbdbe53fad480b42bd31264c2f8281b6756e52d。
- fix1/当前仓库1.9 debugedit SHA：3e19fa64b50dc718f4518b94c8589f29ebe0a2ea48fafcf8004d8bd16e78905f。

[二进制比较](evidence/04/debugedit-binary-comparison.json)。不把同版本号误写为工具相同；本轮实际下载依赖清单见[Thumb](evidence/04/thumb-attempt-0/dependencies.json)、[A32](evidence/04/a32-attempt-0/dependencies.json)。

### 9.2 隔离、资源门禁与实际命令

本任务目录temp/m1-target-20261114/weekend-j2，新检出ffmpeg基线5fe76358596f66e955f005094e6f34ca525ab23d，应用原fix1补丁。patch SHA仍为0c94e54d252ad1ecbc625f629af090b257edba4cd3753d76352fd031486243b6，spec SHA仍为0e611e7eb95ada2c024dbea379821c5b109383f1545bcb0c86ef85f238740c27，复用第8节同SHA实际编译参数核对，不重新引入V=1。

仓库配置仍为Unified20261104.125239 / Base20261030.120529。原ffmpeg-armv7l.conf不动；资源规则优先，派生配置**只修改tmpdir和默认buildroot的路径**，其余字段完全一致，CLI再指定本变体的新root。[配置](evidence/04/ffmpeg-armv7l.conf)、[配置/源码SHA及准备命令](evidence/04/preparation.json)。

GBS独立HOME、TMPDIR/TMP/TEMP、XDG目录、CCACHE_DIR均在weekend-j2内；缓存位于本次独立root。没有使用另一构建或旧root的HOME/tmpdir/缓存进行构建。仅历史核查读取了用户明确要求的旧日志、RPM及ELF。没有kill、调整、停止任何非本任务进程；不执行sudo系统设置、drop_caches、swapoff、sysctl或服务/主机重启。

实际GBS核心命令（分别在本任务ffmpeg检出运行）：

~~~sh
gbs -c "$WORKDIR/temp/m1-target-20261114/weekend-j2/ffmpeg-armv7l.conf" \
  build -A armv7l --spec ffmpeg.spec --include-all \
  --buildroot "$WORKDIR/temp/m1-target-20261114/weekend-j2/roots/thumb-attempt-0" \
  --threads 1 --define '_smp_mflags -j2' --define 'profile_isa thumb'

gbs -c "$WORKDIR/temp/m1-target-20261114/weekend-j2/ffmpeg-armv7l.conf" \
  build -A armv7l --spec ffmpeg.spec --include-all \
  --buildroot "$WORKDIR/temp/m1-target-20261114/weekend-j2/roots/a32-attempt-0" \
  --threads 1 --define '_smp_mflags -j2' --define 'profile_isa a32'
~~~

独立systemd service串行监督两个scope；每scope MemoryMax=6G、MemoryHigh=5G、CPUQuota=200%，nice19/ionice-c3，_smp_mflags中没有V=1，也清除了继承的V/MAKEFLAGS/MFLAGS。[worker](evidence/04/worker.py)、[supervisor](evidence/04/supervisor.py)、[Thumb实读限额](evidence/04/thumb-attempt-0/effective-limits.json)、[A32实读限额](evidence/04/a32-attempt-0/effective-limits.json)。监督服务本身另限256MiB/25%，不承载编译。

启动条件逐变体核对MemAvailable≥16GiB、load1<nproc×0.6、磁盘≥50GiB；不满足才600秒复查，上限48小时。运行每60秒保存meminfo全文、load、磁盘及memory.current/peak/events；低于6GiB连续两次或磁盘低于20GiB时仅停止本任务对应scope，重新门禁、另起root，最多2次资源性重试。此次**两个启动检查都立即通过，等待0次、资源停止0次、重试0次**。[门禁原文](evidence/04/gate.jsonl)、[策略边界检查](evidence/04/monitor-policy-check.json)。没有刻意制造低内存/磁盘满，也不声称实际停止重试分支已压测。

### 9.3 构建结果与非致命诊断

| 变体 | 开始（本地UTC−08） | 结束 | 墙钟秒 | GBS退出码 | armv7l二进制RPM数 |
|---|---|---|---:|---:|---:|
| thumb | 2026-11-14T06:22:18.730309-08:00 | 2026-11-14T06:27:21.812036-08:00 | 303.082 | 0 | 23 |
| a32 | 2026-11-14T06:27:22.290345-08:00 | 2026-11-14T06:32:36.383456-08:00 | 314.093 | 0 | 23 |

两次墙钟合计617.175秒（约10分17秒），包含各自全新root下载/初始化，串行无交叠。真实GBS退出码、scope退出码均0；worker、scope日志与监督日志均有带时间的ALL-END/已结束记录。[总结束记录](evidence/04/terminal.json)、[Thumb命令与环境](evidence/04/thumb-attempt-0/command.json)、[A32命令与环境](evidence/04/a32-attempt-0/command.json)。

每变体仍有8条debugedit诊断，对4个文件各2条：

- libavcodec.so.62.11.100
- libavutil.so.60.8.100
- libswresample.so.6.1.100
- libswscale.so.9.1.100

原文仍为“DWARF version 5 unhandled”与“Unknown debugging section .debug_line_str”，本次非致命，不加-gdwarf-4、不改spec或补丁绕过。[Thumb逐条诊断](evidence/04/thumb-attempt-0/artifact-validation.json)、[A32逐条诊断](evidence/04/a32-attempt-0/artifact-validation.json)。find-debuginfo.sh实际收到-j2而不含V=1，[Thumb打包摘录](evidence/04/thumb-build-excerpts.json)、[A32打包摘录](evidence/04/a32-build-excerpts.json)。第8节由错误V=1宏引发的打包阻塞，在本次正确命令下消除。

### 9.4 打包ELF与DWARF验收

每变体23个RPM的路径、字节数与SHA见[Thumb RPM清单](evidence/04/thumb-attempt-0/rpms.json)、[A32 RPM清单](evidence/04/a32-attempt-0/rpms.json)。分别提取libavcodec/libavutil与其独立debuginfo子包，使用打包后的文件核对，不使用BUILD中间文件冒充。

| 变体 | 库 | runtime = debug SHA-1 build-id（40个十六进制字符） | 核对 |
|---|---|---|---|
| thumb | libavcodec | 805376f248504d2084e3e95470810873ffc3655a | 一致 |
| thumb | libavutil | bb5b41f743b9b07bb38cc5007f7deb6516256579 | 一致 |
| a32 | libavcodec | bdc2a972e0bb357ca144d082f72519e7bed19813 | 一致 |
| a32 | libavutil | 2f63cff726697e7395f75d14c0f96b43e14a6a58 | 一致 |

| 变体 | 文件 | SHA-256 |
|---|---|---|
| thumb | libavcodec runtime | 07da98e1c92253c34271ec55d97a112419e8f19bbf59c5d38c33c0af4ad0e742 |
| thumb | libavcodec debug | a4d351e3a2262c0cda1c2d7958ad2ae3d784d211ef176ec712ff2712f5eadd85 |
| thumb | libavutil runtime | 6b3abb7faed64f62d9afb293148558eccd39c194b85ac4d842b6005f380c4d44 |
| thumb | libavutil debug | 75347f751e97064b8c2a61bae264216b15917ce308db36cf2741debf8d69f090 |
| a32 | libavcodec runtime | 8810ee31a55284a9236c20eaa2e01b4a60b6abffca5cd6b199be321deaf50971 |
| a32 | libavcodec debug | 76a215bd4e982509389e1da29c008c29fdc4a4b813b75bda242d7b132cc73a48 |
| a32 | libavutil runtime | 598e06c2a3387a30c1afd940ae68347420a0051518199e9fc97b17273fc8bf91 |
| a32 | libavutil debug | f8f560a9f4da5b16001891f156e74bbd9143b00bd873fcb56547a0072feef112 |

| 变体 | 调试库 | DWARF4 CU数 | DWARF5 CU数 | readelf info / rawline退出码 | stderr |
|---|---|---:|---:|---|---|
| thumb | libavcodec | 313 | 52 | 0 / 0 | 空 |
| thumb | libavutil | 99 | 2 | 0 / 0 | 空 |
| a32 | libavcodec | 313 | 52 | 0 / 0 | 空 |
| a32 | libavutil | 99 | 2 | 0 / 0 | 空 |

两库.debug_info、.debug_line均存在并可读取。所有readelf命令、输出流大小及SHA、原文开头和stderr均保存；大段readelf输出只流式计算SHA，不写入仓库，调试ELF原件留在本任务extracted目录。检查器[verify_artifacts.py](evidence/04/verify_artifacts.py)，[轻量核对结果](evidence/04/verification/terminal.json)。

**局限**：可读与身份相同不等于debugsource完整，也不证明debugedit已正确改写全部DWARF5源码路径。发布llvm-profgen没有本轮已验证的纯加载ELF+DWARF、又不执行采样转换的独立入口，因此按用户允许的分支跳过该可选检查并说明；未构造额外采样、未读取正式profile。AArch64与profile消费构建仍未验证。

### 9.5 资源与安全收尾

[资源摘要](evidence/04/resource-summary.json)及两个attempt目录的60秒原始记录：

- 最低MemAvailable：25,751,736,320 B（约23.98GiB）。
- 最高1分钟loadavg：2.47216796875，nproc=20，启动门槛为12。
- 最低WORKDIR磁盘可用：206,662,979,584 B（约192.47GiB）。
- 最大构建cgroup memory.peak：2,196,312,064 B（约2.05GiB）；Thumb峰值2,196,312,064 B，A32峰值2,180,231,168 B。
- 两scope的high/max/oom/oom_kill均0；无资源暂停、停止或重试。
- 两项轻量产物核对串行，合计7.01秒，独立3G/2G高水位/100% scope峰值93,896,704 B；开始前同样通过三项资源门禁，无资源事件。

[所有本任务构建/核对单元已inactive/dead](evidence/04/units-final.txt)。没有操作另一GBS任务、开发板、RPi5、Gerrit或系统设置；不安装宿主软件（只有正常GBS依赖进入本任务新root）、不删除任何旧目录、不改设计或既有证据。GBS日志中的/home/abuild等路径位于WORKDIR内chroot，不是向宿主该路径创建项目文件。systemd运行时单元状态由用户要求的systemd工具管理；项目日志/产物均显式写入WORKDIR。

文档准备曾误读不存在的示例模板文件名，退出1后改为只列examples/gbs文件名确认；未改文件、未触碰保护配置。一次编辑工具脚本发生插值错误，在执行shell前终止，重写后成功，不影响构建或证据。均不冒充GBS失败。

### 9.6 main / hq交付

hq的更新只包含4个授权文件：README.md、examples/ffmpeg/README.md、examples/ffmpeg/profiling.patch、examples/gbs/ffmpeg-target.conf.in。补丁与fix1 SHA相同；配置使用@PROJECT@占位，除路径外与实际配置字段逐项相等。写入-j2命令、实测时长、build-id检查方法、非致命DWARF5诊断与局限；AArch64、profile消费继续Not verified。

hq提交 **2c962454a4186a40ba8e9fabb7df0e5b8ae1cb59** 已普通推送并核验远端，状态为 **待 PM 审阅**（只在main记录）。无force/Gerrit推送。[推送原文](evidence/04/hq-push.json)、[远端核验](evidence/04/hq-result.json)。check_hq.py通过：0违规、0警告、22个链接有效；3个bash代码块bash -n通过，无执行示例中的额外构建。[发布检查](evidence/04/hq-check.json)、[shell语法](evidence/04/hq-shell-checks.json)、[配置等价](evidence/04/hq-template-equivalence.json)。

所有小证据位于evidence/04，单文件<1MB；原始构建日志、RPM、ELF、大文件均留temp/m1-target-20261114/weekend-j2/，完整[原件与SHA索引](evidence/04/source-index.json)。两变体交付验证完成，现停止；剩余事项为PM审阅、周一确认RPi5以及未来消费/性能验证，不自动开始。
