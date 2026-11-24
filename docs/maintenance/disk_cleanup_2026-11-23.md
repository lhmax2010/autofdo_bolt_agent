# WORKDIR 磁盘清理（2026-11-23）

直接清理了 177 项，按可回收的分配块保守估计 **56.93 GB（53.02 GiB）**。另有 53 项需要用户执行脚本，估计可释放 **10.71 GB（9.98 GiB）**。

## 盘点与互斥

开工时未发现本项目的 GBS、rpmbuild、perf 或 SDB 客户端。共享 SDB 后台服务继续运行。持有 `temp/host-gbs.lock`，并在删除前核对进程、挂载、路径设备号、inode 与 Git 跟踪状态。全部操作限制在 WORKDIR。没有接板或执行 sudo。 [互斥凭证](evidence/2026-11-23/project-and-lock.json)

`du -x -B1 --threshold=209715200` 记录了 977 个不小于 200 MiB 的目录，附修改时间、属主 UID 和任务。与 2026-11-17 清单逐路径对比，有 859 个 `temp/` 路径本轮首次列出。该标记不代表创建日期。祖先和子目录大小重叠。盘点记录 84 条路径权限诊断，大小为可读下界。 [目录清单](evidence/2026-11-23/inventory-200m.tsv) · [诊断](evidence/2026-11-23/du-before.stderr)

| 上次清单未列出的较大顶层目录 | 可读分配 GiB | 属主 UID |
|---|---:|---:|
| `temp/kernel-afdo-k1` | 65.39 | 1000 |
| `temp/m1-ffmpeg-rpi4-thumb-01` | 33.23 | 1000 |
| `temp/kernel-afdo-k0` | 4.51 | 1000 |
| `temp/disk-cleanup-20261123` | 1.47 | 1000 |
| `temp/m2a-rpi5-wt` | 1.35 | 1000 |
| `temp/board13-probe-wt` | 1.35 | 1000 |
| `temp/etm-probe-wt` | 1.34 | 1000 |

## 空间与目标

清理前 WORKDIR 可读分配量为 234.68 GB。与上次脚本核对的 18 个旧 chroot 路径本轮均已不存在，不重复计入。 [旧路径复查](evidence/2026-11-23/historical-root-crosscheck.json)

| 时点 | /home 可用字节 | GiB |
|---|---:|---:|
| 开工 | 32,217,583,616 | 30.00 |
| 本次删除前 | 299,164,065,792 | 278.62 |
| 本次删除后 | 356,094,615,552 | 331.64 |

开工到结束的分区可用空间变化为 +323,877,031,936 B，其中本次删除前已有 +266,946,482,176 B 变化，不归为本项目清理。直接清理估计排除了目标外仍存在硬链接的内容。 本轮删除期间 df 增量为 56.93 GB。清理后 WORKDIR 可读分配总量为 **180.93 GB（168.51 GiB）**，比盘点时少 53.75 GB，另有 84 条不可读路径诊断。 距 400 GB 目标仍差 **343.07 GB**。若脚本全部执行成功，计划合计为 67.65 GB，仍差 332.35 GB。 [开工 df](evidence/2026-11-23/df-before.txt) · [本次删除前 df](evidence/2026-11-23/df-predelete.txt) · [本次删除后 df](evidence/2026-11-23/df-after.txt) · [WORKDIR 实测](evidence/2026-11-23/du-after.tsv)

## 保全和链接重放

K-BASE、K-AFDO、K-BASE-S 与 PLAT 归档产物、冻结仓库、媒体、原始采集及转换证据、M1 attempt-11 完整目录、源码和 Git 跟踪文件保留。已提交文本证据按 Git 对象索引文件路径，候选另外检查跟踪状态和用途。 [扫描统计](evidence/2026-11-23/evidence-scan.json)

保全了 13 个 LLVM 工具、依赖及配置文件到 `temp/preserved/`，逐项核对 SHA-256。M1/M2a 收据使用的加载器、运行库及工具原路径保留。 [工具清单](evidence/2026-11-23/preserved-tools.json)

`temp/kernel-afdo-k0/relink-kits/` 保存最终 argv、薄归档与成员、链接脚本、`.config`、`Module.symvers` 及已核验的原版 LLD。按用户指定的 SHA 或 build-id 判定。

| 变体 | 配置 | 归档和重放 build-id | 逐字节相同 |
|---|---|---|---|
| K-BASE | arm-rpi4 | `96766cfcbff8c33d83ca38152ad02f6a02dd44d4` | 否 |
| K-BASE | arm-rpi4-rt | `3a7f29050e83d65db4f959bff4c4f21bede2f0e8` | 否 |
| K-AFDO | arm-rpi4 | `43ba5d455daec5da17e7521048767cdace012c91` | 否 |
| K-AFDO | arm-rpi4-rt | `0f588e3aaff2032324c0072bc926a95ed796744b` | 否 |
| K-BASE-S | arm-rpi4 | `a78e6ca8956db526ba91d5856369fc1a7f15b5fd` | 否 |
| K-BASE-S | arm-rpi4-rt | `a073822ff2ec8b71662294a0d5311ddfeed48a76` | 否 |

[重放记录](evidence/2026-11-23/relink-summary.json) · [SHA 与原件索引](evidence/2026-11-23/index.json) · [释放本轮重放副本](evidence/2026-11-23/discarded-replay-copies.json)

## 直接删除

| 路径 | 分配字节 | 所属任务 | 依据 |
|---|---:|---|---|
| `temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/rpmbuild/BUILD/llvm-22.1.8/build/lib64` | 10,320,642,048 | GBS-ROOT-LLVM-RELEASE-20261114c | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/kernel-afdo-k1/k1e/kafdo/gbs-root/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD` | 6,943,277,056 | K-AFDO | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，链接包复核通过，无文件级证据引用，逐项复核进程与路径 |
| `temp/kernel-afdo-k1/k1e/kbase-s/gbs-root/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD` | 6,923,902,976 | K-BASE-S | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，链接包复核通过，无文件级证据引用，逐项复核进程与路径 |
| `temp/kernel-afdo-k1/kbase/gbs-root-01/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD` | 6,922,305,536 | K-BASE | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，链接包复核通过，无文件级证据引用，逐项复核进程与路径 |
| `temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/rpmbuild/BUILD/llvm-22.1.8/build/tools` | 5,192,499,200 | GBS-ROOT-LLVM-RELEASE-20261114c | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/rpmbuild/BUILD/llvm-22.1.8/build/lib` | 2,911,739,904 | GBS-ROOT-LLVM-RELEASE-20261114c | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/kernel-afdo-k1/base-0fac5de6/gbs-root-03/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD` | 2,235,088,896 | kernel-afdo-k1 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/kernel-afdo-k1/base-0fac5de6/gbs-root/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD` | 1,745,776,640 | kernel-afdo-k1 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/kernel-afdo-k1/base-0fac5de6/gbs-root-04/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/drivers` | 1,133,092,864 | kernel-afdo-k1 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/rpmbuild/BUILD/llvm-22.1.8/llvm/test/CodeGen` | 650,670,080 | GBS-ROOT-LLVM-RELEASE-20261114c | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/Sema/CMakeFiles/obj.clangSema.dir` | 400,351,232 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/kernel-afdo-k1/base-0fac5de6/gbs-root-04/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/build/arm-rpi4-rt/drivers` | 372,649,984 | kernel-afdo-k1 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/kernel-afdo-k1/base-0fac5de6/gbs-root-04/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/build/arm-rpi4/drivers` | 362,500,096 | kernel-afdo-k1 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/CodeGen/CMakeFiles/LLVMCodeGen.dir` | 309,215,232 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/AST/CMakeFiles/obj.clangAST.dir` | 305,885,184 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-tidy/bugprone/CMakeFiles/obj.clangTidyBugproneModule.dir` | 290,488,320 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/kernel-afdo-k1/k1e/kafdo-attempt-01/gbs-root/local/cache` | 286,892,032 | kernel-afdo-k1 | 下载缓存全部 RPM 与保留存档逐文件 SHA 相同，无文件级证据引用，逐项复核进程与路径 |
| `temp/kernel-afdo-k1/base-0fac5de6/gbs-root-04/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/build/arm-rpi4-rt/net` | 284,909,568 | kernel-afdo-k1 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/kernel-afdo-k1/base-0fac5de6/gbs-root-04/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/build/arm-rpi4/net` | 283,791,360 | kernel-afdo-k1 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/CodeGen/CMakeFiles/obj.clangCodeGen.dir` | 257,953,792 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/rpmbuild/BUILD/llvm-22.1.8/mlgo_verify_assets` | 254,070,784 | GBS-ROOT-LLVM-RELEASE-20261114c | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/m1-ffmpeg-rpi4-thumb-01/attempt-04/formal/roots/BASE-1794901378698205738/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD` | 215,969,792 | m1-ffmpeg-rpi4-thumb-01 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/m1-ffmpeg-rpi4-thumb-01/attempt-07/formal/roots/BASE-1794912888403444845/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD` | 215,965,696 | m1-ffmpeg-rpi4-thumb-01 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/m1-ffmpeg-rpi4-thumb-01/attempt-05/formal/roots/BASE-1794904911981754568/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD` | 215,961,600 | m1-ffmpeg-rpi4-thumb-01 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/m1-ffmpeg-rpi4-thumb-01/attempt-05/formal/roots/BASE-1794905383231205756/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD` | 215,961,600 | m1-ffmpeg-rpi4-thumb-01 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/m1-ffmpeg-rpi4-thumb-01/attempt-10/formal/roots/BASE-r-1794938821554829153/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD` | 215,961,600 | m1-ffmpeg-rpi4-thumb-01 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/m1-ffmpeg-rpi4-thumb-01/attempt-04/formal/roots/BASE-1794900996034141318/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD` | 215,957,504 | m1-ffmpeg-rpi4-thumb-01 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/m1-ffmpeg-rpi4-thumb-01/attempt-07/formal/roots/BASE-r-1794914645386359759/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD` | 215,957,504 | m1-ffmpeg-rpi4-thumb-01 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/m1-ffmpeg-rpi4-thumb-01/attempt-08/formal/roots/BASE-1794915301903391291/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD` | 215,957,504 | m1-ffmpeg-rpi4-thumb-01 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/m1-ffmpeg-rpi4-thumb-01/attempt-09/formal/roots/BASE-1794929894326191894/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD` | 215,957,504 | m1-ffmpeg-rpi4-thumb-01 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/m1-ffmpeg-rpi4-thumb-01/attempt-09/formal/roots/BASE-r-1794931264553126939/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD` | 215,957,504 | m1-ffmpeg-rpi4-thumb-01 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/m1-ffmpeg-rpi4-thumb-01/attempt-06/formal/roots/BASE-1794908524854947931/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD` | 215,953,408 | m1-ffmpeg-rpi4-thumb-01 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/m1-ffmpeg-rpi4-thumb-01/attempt-08/formal/roots/BASE-r-1794917244870824256/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD` | 215,953,408 | m1-ffmpeg-rpi4-thumb-01 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/m1-ffmpeg-rpi4-thumb-01/attempt-10/formal/roots/BASE-1794937343443701945/local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/BUILD` | 215,953,408 | m1-ffmpeg-rpi4-thumb-01 | GBS 临时编译或打包树，最终 artifacts/RPM 与已登记输入留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clangd/CMakeFiles/obj.clangDaemon.dir` | 210,501,632 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/StaticAnalyzer/Checkers/CMakeFiles/obj.clangStaticAnalyzerCheckers.dir` | 202,330,112 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-tidy/modernize/CMakeFiles/obj.clangTidyModernizeModule.dir` | 180,834,304 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-tidy/readability/CMakeFiles/obj.clangTidyReadabilityModule.dir` | 169,078,784 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Analysis/CMakeFiles/LLVMAnalysis.dir` | 166,764,544 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Target/X86/CMakeFiles/LLVMX86CodeGen.dir` | 155,205,632 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Transforms/Scalar/CMakeFiles/LLVMScalarOpts.dir` | 152,944,640 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Transforms/IPO/CMakeFiles/LLVMipo.dir` | 143,843,328 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Target/AArch64/CMakeFiles/LLVMAArch64CodeGen.dir` | 121,786,368 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Transforms/Utils/CMakeFiles/LLVMTransformUtils.dir` | 117,997,568 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Transforms/Vectorize/CMakeFiles/LLVMVectorize.dir` | 109,944,832 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/IR/CMakeFiles/LLVMCore.dir` | 108,261,376 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/Driver/CMakeFiles/obj.clangDriver.dir` | 102,957,056 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/ExecutionEngine/Orc/CMakeFiles/LLVMOrcJIT.dir` | 101,466,112 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lld/ELF/CMakeFiles/lldELF.dir` | 90,292,224 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/CodeGen/SelectionDAG/CMakeFiles/LLVMSelectionDAG.dir` | 78,311,424 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/StaticAnalyzer/Core/CMakeFiles/obj.clangStaticAnalyzerCore.dir` | 76,795,904 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-tidy/cppcoreguidelines/CMakeFiles/obj.clangTidyCppCoreGuidelinesModule.dir` | 75,251,712 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Target/ARM/CMakeFiles/LLVMARMCodeGen.dir` | 74,985,472 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/Serialization/CMakeFiles/obj.clangSerialization.dir` | 73,531,392 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-tidy/misc/CMakeFiles/obj.clangTidyMiscModule.dir` | 73,056,256 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/utils/TableGen/CMakeFiles/llvm-tblgen.dir` | 72,994,816 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/Frontend/CMakeFiles/obj.clangFrontend.dir` | 69,505,024 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Target/CMakeFiles/lldbTarget.dir` | 67,428,352 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/ASTMatchers/Dynamic/CMakeFiles/obj.clangDynamicASTMatchers.dir` | 63,668,224 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Transforms/Instrumentation/CMakeFiles/LLVMInstrumentation.dir` | 60,633,088 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/ObjectYAML/CMakeFiles/LLVMObjectYAML.dir` | 58,646,528 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Support/CMakeFiles/LLVMSupport.dir` | 57,561,088 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-tidy/abseil/CMakeFiles/obj.clangTidyAbseilModule.dir` | 54,648,832 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/Analysis/CMakeFiles/obj.clangAnalysis.dir` | 54,218,752 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Passes/CMakeFiles/LLVMPasses.dir` | 53,432,320 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/Basic/CMakeFiles/obj.clangBasic.dir` | 52,883,456 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-tidy/performance/CMakeFiles/obj.clangTidyPerformanceModule.dir` | 52,338,688 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/ExecutionEngine/JITLink/CMakeFiles/LLVMJITLink.dir` | 52,178,944 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Commands/CMakeFiles/lldbCommands.dir` | 51,671,040 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/tools/lldb-dap/CMakeFiles/lldbDAP.dir` | 51,142,656 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/API/CMakeFiles/liblldb.dir` | 50,524,160 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Transforms/InstCombine/CMakeFiles/LLVMInstCombine.dir` | 48,836,608 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clangd/refactor/tweaks/CMakeFiles/obj.clangDaemonTweaks.dir` | 45,486,080 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/ProfileData/CMakeFiles/LLVMProfileData.dir` | 44,617,728 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Plugins/Instruction/RISCV/CMakeFiles/lldbPluginInstructionRISCV.dir` | 42,893,312 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Object/CMakeFiles/LLVMObject.dir` | 42,872,832 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Core/CMakeFiles/lldbCore.dir` | 40,595,456 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-tidy/utils/CMakeFiles/obj.clangTidyUtils.dir` | 39,862,272 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/llvm-readobj/CMakeFiles/llvm-readobj.dir` | 39,788,544 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/Parse/CMakeFiles/obj.clangParse.dir` | 39,301,120 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/CodeGen/GlobalISel/CMakeFiles/LLVMGlobalISel.dir` | 39,063,552 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/Tooling/Refactoring/CMakeFiles/obj.clangToolingRefactoring.dir` | 39,018,496 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lld/MachO/CMakeFiles/lldMachO.dir` | 37,728,256 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/CodeGen/AsmPrinter/CMakeFiles/LLVMAsmPrinter.dir` | 37,244,928 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/DebugInfo/PDB/CMakeFiles/LLVMDebugInfoPDB.dir` | 36,610,048 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/utils/TableGen/Common/CMakeFiles/obj.LLVMTableGenCommon.dir` | 36,327,424 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/utils/TableGen/CMakeFiles/clang-tblgen.dir` | 35,844,096 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/libclang/CMakeFiles/libclang.dir` | 34,217,984 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lld/COFF/CMakeFiles/lldCOFF.dir` | 34,037,760 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-doc/CMakeFiles/obj.clangDoc.dir` | 33,718,272 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/MC/CMakeFiles/LLVMMC.dir` | 32,800,768 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-tidy/google/CMakeFiles/obj.clangTidyGoogleModule.dir` | 32,448,512 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/DebugInfo/LogicalView/CMakeFiles/LLVMDebugInfoLogicalView.dir` | 31,346,688 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Plugins/SymbolFile/DWARF/CMakeFiles/lldbPluginSymbolFileDWARF.dir` | 31,195,136 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/Lex/CMakeFiles/obj.clangLex.dir` | 31,141,888 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Plugins/ExpressionParser/Clang/CMakeFiles/lldbPluginExpressionParserClang.dir` | 29,913,088 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-tidy/android/CMakeFiles/obj.clangTidyAndroidModule.dir` | 29,896,704 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/DebugInfo/DWARF/CMakeFiles/LLVMDebugInfoDWARF.dir` | 29,356,032 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/llvm-pdbutil/CMakeFiles/llvm-pdbutil.dir` | 28,712,960 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Interpreter/CMakeFiles/lldbInterpreter.dir` | 27,336,704 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Plugins/Language/CPlusPlus/CMakeFiles/lldbPluginCPlusPlusLanguage.dir` | 26,955,776 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/obj2yaml/CMakeFiles/obj2yaml.dir` | 26,005,504 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/Format/CMakeFiles/obj.clangFormat.dir` | 25,632,768 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Symbol/CMakeFiles/lldbSymbol.dir` | 25,530,368 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/llvm-reduce/CMakeFiles/llvm-reduce.dir` | 24,068,096 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Plugins/Process/gdb-remote/CMakeFiles/lldbPluginProcessGDBRemote.dir` | 23,162,880 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/Analysis/FlowSensitive/CMakeFiles/obj.clangAnalysisFlowSensitive.dir` | 22,781,952 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Target/BPF/CMakeFiles/LLVMBPFCodeGen.dir` | 22,638,592 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/ObjCopy/CMakeFiles/LLVMObjCopy.dir` | 22,540,288 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/ExtractAPI/CMakeFiles/obj.clangExtractAPI.dir` | 22,503,424 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/LTO/CMakeFiles/LLVMLTO.dir` | 22,458,368 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/llvm-objdump/CMakeFiles/llvm-objdump.dir` | 22,163,456 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Plugins/SymbolFile/NativePDB/CMakeFiles/lldbPluginSymbolFileNativePDB.dir` | 19,873,792 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/ASTMatchers/CMakeFiles/obj.clangASTMatchers.dir` | 19,812,352 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-tidy/llvm/CMakeFiles/obj.clangTidyLLVMModule.dir` | 19,603,456 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/DebugInfo/CodeView/CMakeFiles/LLVMDebugInfoCodeView.dir` | 19,472,384 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Host/CMakeFiles/lldbHost.dir` | 19,451,904 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Utility/CMakeFiles/lldbUtility.dir` | 18,952,192 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/llvm-exegesis/lib/CMakeFiles/LLVMExegesis.dir` | 18,907,136 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/Index/CMakeFiles/obj.clangIndex.dir` | 18,296,832 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-tidy/objc/CMakeFiles/obj.clangTidyObjCModule.dir` | 18,255,872 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/DWARFLinker/Parallel/CMakeFiles/LLVMDWARFLinkerParallel.dir` | 18,198,528 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Breakpoint/CMakeFiles/lldbBreakpoint.dir` | 17,887,232 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Target/X86/MCTargetDesc/CMakeFiles/LLVMX86Desc.dir` | 17,444,864 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Plugins/Process/Utility/CMakeFiles/lldbPluginProcessUtility.dir` | 17,240,064 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-tidy/CMakeFiles/obj.clangTidy.dir` | 17,006,592 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lld/wasm/CMakeFiles/lldWasm.dir` | 16,736,256 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/Analysis/FlowSensitive/Models/CMakeFiles/obj.clangAnalysisFlowSensitiveModels.dir` | 16,429,056 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Transforms/Coroutines/CMakeFiles/LLVMCoroutines.dir` | 15,491,072 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/Tooling/CMakeFiles/obj.clangTooling.dir` | 15,478,784 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/llvm-cov/CMakeFiles/llvm-cov.dir` | 15,335,424 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/ValueObject/CMakeFiles/lldbValueObject.dir` | 15,249,408 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/TableGen/CMakeFiles/LLVMTableGen.dir` | 15,138,816 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/llvm-xray/CMakeFiles/llvm-xray.dir` | 14,811,136 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/DataFormatters/CMakeFiles/lldbDataFormatters.dir` | 14,643,200 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Bitcode/Reader/CMakeFiles/LLVMBitReader.dir` | 14,344,192 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Expression/CMakeFiles/lldbExpression.dir` | 14,098,432 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/Tooling/Transformer/CMakeFiles/obj.clangTransformer.dir` | 13,778,944 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-tidy/fuchsia/CMakeFiles/obj.clangTidyFuchsiaModule.dir` | 13,656,064 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/AsmParser/CMakeFiles/LLVMAsmParser.dir` | 13,500,416 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/Tooling/Syntax/CMakeFiles/obj.clangToolingSyntax.dir` | 13,463,552 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Frontend/OpenMP/CMakeFiles/LLVMFrontendOpenMP.dir` | 13,287,424 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/APINotes/CMakeFiles/obj.clangAPINotes.dir` | 13,258,752 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/Analysis/LifetimeSafety/CMakeFiles/obj.clangAnalysisLifetimeSafety.dir` | 13,086,720 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/TextAPI/CMakeFiles/LLVMTextAPI.dir` | 12,988,416 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/include-cleaner/lib/CMakeFiles/obj.clangIncludeCleaner.dir` | 12,976,128 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/bugpoint/CMakeFiles/bugpoint.dir` | 12,746,752 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-tidy/altera/CMakeFiles/obj.clangTidyAlteraModule.dir` | 12,537,856 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Bitcode/Writer/CMakeFiles/LLVMBitWriter.dir` | 12,382,208 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/llvm-jitlink/CMakeFiles/llvm-jitlink.dir` | 12,337,152 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-tidy/hicpp/CMakeFiles/obj.clangTidyHICPPModule.dir` | 12,328,960 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/utils/TableGen/Basic/CMakeFiles/obj.LLVMTableGenBasic.dir` | 12,222,464 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/dsymutil/CMakeFiles/dsymutil.dir` | 12,181,504 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/Target/AArch64/MCTargetDesc/CMakeFiles/LLVMAArch64Desc.dir` | 12,115,968 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Plugins/LanguageRuntime/ObjC/AppleObjCRuntime/CMakeFiles/lldbPluginAppleObjCRuntime.dir` | 12,050,432 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/MC/MCParser/CMakeFiles/LLVMMCParser.dir` | 12,042,240 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/modularize/CMakeFiles/modularize.dir` | 12,038,144 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/Interpreter/CMakeFiles/obj.clangInterpreter.dir` | 11,997,184 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/ExecutionEngine/Orc/TargetProcess/CMakeFiles/LLVMOrcTargetProcess.dir` | 11,948,032 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/SandboxIR/CMakeFiles/LLVMSandboxIR.dir` | 11,554,816 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-tidy/portability/CMakeFiles/obj.clangTidyPortabilityModule.dir` | 11,243,520 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/ExecutionEngine/RuntimeDyld/CMakeFiles/LLVMRuntimeDyld.dir` | 11,223,040 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/InstallAPI/CMakeFiles/obj.clangInstallAPI.dir` | 11,038,720 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/llvm-profdata/CMakeFiles/llvm-profdata.dir` | 10,645,504 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/DebugInfo/GSYM/CMakeFiles/LLVMDebugInfoGSYM.dir` | 10,559,488 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/projects/openmp/runtime/src/CMakeFiles/obj.omp.dir` | 10,297,344 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Plugins/Language/ObjC/CMakeFiles/lldbPluginObjCLanguage.dir` | 10,256,384 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Plugins/Process/Linux/CMakeFiles/lldbPluginProcessLinux.dir` | 10,022,912 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/llvm-mca/CMakeFiles/llvm-mca.dir` | 10,014,720 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/llvm-remarkutil/CMakeFiles/llvm-remarkutil.dir` | 9,900,032 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/lib/DependencyScanning/CMakeFiles/obj.clangDependencyScanning.dir` | 9,850,880 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/CAS/CMakeFiles/LLVMCAS.dir` | 9,416,704 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/ProfileData/Coverage/CMakeFiles/LLVMCoverage.dir` | 9,125,888 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-include-fixer/find-all-symbols/CMakeFiles/obj.findAllSymbols.dir` | 8,896,512 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/lldb/source/Plugins/TypeSystem/Clang/CMakeFiles/lldbPluginTypeSystemClang.dir` | 8,880,128 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/lib/ExecutionEngine/Orc/Debugging/CMakeFiles/LLVMOrcDebugging.dir` | 8,634,368 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |
| `temp/llvm-profgen-enh/build/tools/clang/tools/extra/clang-tidy/llvmlibc/CMakeFiles/obj.clangTidyLLVMLibcModule.dir` | 8,634,368 | llvm-profgen-enh | 已结束 CMake 构建的目标中间目录，工具安装、输入和归档留存，无文件级证据引用，逐项复核进程与路径 |

[删除回执](evidence/2026-11-23/direct-results.jsonl)

## 待执行脚本

`temp/disk-cleanup-20261123/sudo-delete.sh` 的 SHA-256 为 `be17af68ced39cd9df2be91c85403d812516d0fab8882bce11722860dd5e4025`。脚本先打印所有路径与合计，并要求从终端输入 `yes`。执行时复核路径前缀、共享锁、进程、挂载和保全 SHA。每条删除命令都有理由、大小和分类。已通过 `bash -n` 与 `--preview`。 [计划全表](evidence/2026-11-23/delete-plan.json)

- m1-ffmpeg-rpi4-thumb-01 有 47 项，共 9.00 GB。
- kernel-afdo-k1 有 6 项，共 1.72 GB。

有 43 个候选因证据引用、权限不足、挂载或存在受保护产物而保留。命中证据或继续使用的构建根按可验证的子目录清理。 [保留明细](evidence/2026-11-23/blocked.json)

[完整证据索引](evidence/2026-11-23/index.json)
