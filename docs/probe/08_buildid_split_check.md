# 带 build-id 的 FFmpeg 调试拆分核对（v0.5）

日期：2026-10-30（Asia/Shanghai）。**核心验证通过：运行文件与调试文件都有可读的SHT_NOTE，build-id完整字节串相同，为 `f960461f63c852474257f51267b7b543afffdc9c`（20字节）。** `.build-id` 两个链接均正确。没有连接开发板、修改LLVM或设计正文，没有开始增强实现。

证据：[E1 构建与警告](evidence/08/01_build.txt)、[E2 ELF与链接](evidence/08/02_elf_split.txt)，新增合计39,326字节，小于150KB。`W=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent`，`T=W/temp/v05`；完整输出与大文件仅留temp。

## 0. v0.5归档

指定源 `/home/linhao/Downloads/02_llvm_profgen_enhance_design_v0.5.md` 在移动前通过SHA-256与第一行前缀校验；第一行是 `# llvm-profgen 增强设计（第一批详细设计 + 第二、三批规划）`。

SHA-256：**1e70bac98024bfa45dc5505bb315565fd7a1591c9cfcf5ba0e24747b3d45a8cf**。

用 `mv -T` 移入 [设计v0.5](../profgen/design/02_llvm_profgen_enhance_design_v0.5.md)，移动后再次核对哈希，Downloads原文件已不存在。v0.1–v0.4与其他Downloads文件不动。已读取STATUS、07第1节、v0.5第9节与附录D；只验证发布前显式SHA-1选项，不代替新LLVM发布后默认build-id的复核。

## 1. 带build-id的FFmpeg构建

### 1.1 唯一改动与基线

在07的 `temp/v04/ffmpeg` worktree创建临时分支 `afdo/v05-buildid`，基线为07相同提交 `5fe76358596f66e955f005094e6f34ca525ab23d`。唯一改动是 `packaging/ffmpeg.spec:247` 在configure调用中新增：

```diff
+    --extra-ldflags="-Wl,--build-id=sha1" \
```

临时FFmpeg提交为 `8a50cbfdc1383a34b781756c73c6252d86e6e1ad`（Hao Lin <hao.lin@samsung.com>），`git diff`确认仅1文件、1行新增（全文E1）。此提交只保留本地，不推FFmpeg/Gerrit；结果仓库仅提交设计归档、报告、证据和STATUS。`src/ffmpeg`前后干净，原spec不动；LLVM未改。

没有追加profiling、优化或其他链接选项。前后 `ffbuild/config.mak` 的 **CFLAGS逐字相同**；LDFLAGS移除新增的 `-Wl,--build-id=sha1` 后与07相同（按空白分词对照）。T/config_before.mak、T/config_after.mak及E1保留带行号原文。平台optflags仍含-mthumb，FFmpeg原有追加的-O3等保持原样。

### 1.2 GBS执行

`temp/gbs/gbs_v05_ffmpeg.conf`是07配置副本，复用专用 `temp/GBS-ROOT-V04-FFMPEG` 和原tmpdir，未修改config/。Base与Unified均沿用07的reference仓库，完整URL在E1。07两份原libavcodec RPM先保留至 `temp/v04/baseline-rpms/`，原已解包ELF和07日志不动；新两份RPM另存T/rpms。

构建前未发现其他ninja/clang/gbs/make重任务。整段worker用setsid脱离会话，GBS用setsid --wait；只给GBS及子进程设置专用HOME/GIT_CONFIG_NOSYSTEM，nice19/ionice3，单包threads1、make -j10（nproc20的一半）。实际命令与worker见E1。

| 开始→结束（+08:00） | 时长 | GBS真实退出码 | 结束标记 |
|---|---:|---:|---|
| 21:19:37→21:20:41 | 64秒 | 0 | ALL-END 2026-10-30T21:20:41+08:00 OK |

无失败重跑。status和带时间结束标记已打印到构建日志；启动输出最后单独列出：

```sh
tail -n 20 /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/v05/logs/ffmpeg.log
cat /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/v05/logs/ffmpeg.status
```

### 1.3 实际链接命令

同07方法，只读轮询 `ps -ww -eo pid,args` 捕获21:20:22实际clang链接进程（T/link_observed.txt:2，E1），含：

```text
armv7l-tizen-linux-gnueabi-clang -shared -Wl,-soname,libavcodec.so.62
-Wl,-Bsymbolic -Wl,--version-script,libavcodec/libavcodec.ver
-Llibavcodec -Llibavdevice -Llibavfilter -Llibavformat -Llibavutil -Llibswscale -Llibswresample
-Wl,--build-id=sha1 -Wl,-z,relro -Wl,-z,now -Wl,--as-needed -Wl,-z,noexecstack
-Wl,-rpath-link=:libswresample:libswscale:libavfilter:libavdevice:libavformat:libavcodec:libavutil
-Qunused-arguments -o libavcodec/libavcodec.so.62 @libavcodec/libavcodec.so.62.objs
-lavutil -pthread -lm -latomic -lm -latomic -pthread
```

原make输出为静默LD行；完整参数的来源是实际进程观察，不冒充verbose构建日志或make -n推导。日志T/logs/ffmpeg.log:251的configure参数也确认带入同一选项。符合v0.5第9节发布前显式生成build-id的路径。

## 2. 拆分产物核对

### 2.1 note类型、可读性与值

将 `libavcodec-8.0.1-1.armv7l.rpm` 与 `libavcodec-debuginfo-8.0.1-1.armv7l.rpm` 以rpm2cpio/cpio解包到同一 `T/extract` 根（pipefail，exit0），用于同时检查运行文件和调试链接。RPM哈希、大小及完整文件清单见E2。

使用工作目录内 `temp/GBS-ROOT-RPI5-SPIKE/local/BUILD-ROOTS/scratch.aarch64.0/emul/usr/bin/readelf` 与该GBS root的配套loader/libs，执行 `-n/-SW/-sW/-A`，均exit0。没有使用本机安装的ELF工具。

| 项目 | 运行文件 | 调试文件 |
|---|---|---|
| 解包相对路径 | usr/lib/libavcodec.so.62.11.100 | usr/lib/debug/usr/lib/libavcodec.so.62.11.100.debug |
| note节名 | .note.gnu.build-id | .note.gnu.build-id |
| readelf -SW类型 | NOTE（SHT_NOTE） | NOTE（SHT_NOTE） |
| note是否NOBITS | 否 | 否 |
| note节长度 | 0x24（36字节） | 0x24（36字节） |
| GNU note描述数据长度 | 0x14（20字节） | 0x14（20字节） |
| build-id值 | `f960461f63c852474257f51267b7b543afffdc9c` | `f960461f63c852474257f51267b7b543afffdc9c` |
| 可读/完整相等 | 是 | 是，20字节全部一致 |

注意36字节是整个ELF note节大小，**build-id本身为20字节**，不混用两者。按完整字节串比较，不把20字节写成未来所有工具链的固定长度。

运行文件SHA-256=`ba6f821afc9d7d96630aedb8fc00914d71dcfb9e8973a396edf4eb6e7f5f80de`；调试文件SHA-256=`747916edc1bccd8a8a9ffddcec0d4d8fcbb0d255166396f57968dfd9c35a2afd`。SHA不同符合split-debug文件形态，不影响两份note的build-id一致性。调试文件的代码节仍为NOBITS，note没有随代码节变为NOBITS。此结论符合v0.5本轮待验证预期。

### 2.2 debuginfo RPM中的.build-id链接

`rpm -qplv`确认debuginfo RPM确实包含以下两个符号链接（E2），目录和文件名对应完整ID的前2位/剩余位：

| 链接（相对/usr/lib/debug/.build-id） | RPM内链接文本 | 解包后核对 |
|---|---|---|
| f9/60461f63c852474257f51267b7b543afffdc9c | ../../../../../usr/lib/libavcodec.so.62.11.100 | 指向运行文件，存在，SHA与该文件相同 |
| f9/60461f63c852474257f51267b7b543afffdc9c.debug | ../../../../../usr/lib/debug/usr/lib/libavcodec.so.62.11.100.debug | 指向对应.debug，存在，SHA与该文件相同 |

核对在两份RPM共同解包根内进行，按相对链接真实解析并验证目标，不仅比较文件名。符合预期。

### 2.3 find-debuginfo/debugedit警告

本轮 `T/logs/ffmpeg.log:1480`：

```text
+ /usr/lib/rpm/find-debuginfo.sh -j10 --build-id-seed 8.0.1-1 --unique-debug-src-base ffmpeg-8.0.1-1.arm -S debugsourcefiles.list /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1
```

`:1508–1509`仍有libavcodec警告（带时间前缀的原文及其他库警告在E1）：

```text
/usr/lib/rpm/debugedit: /home/abuild/rpmbuild/BUILDROOT/ffmpeg-8.0.1-1.arm/usr/lib/libavcodec.so.62.11.100: Unknown debugging section .debug_line_str
/usr/lib/rpm/debugedit: /home/abuild/rpmbuild/BUILDROOT/ffmpeg-8.0.1-1.arm/usr/lib/libavcodec.so.62.11.100: DWARF version 5 unhandled
```

与07相同的DWARF5问题仍出现；这次没有07的No build ID note found/Missing build-id警告。构建成功与两个note一致只验证本次身份字段，**不证明debugedit已正确修写DWARF5源码路径或完整行表质量**。该风险已列入v0.5附录D，本轮没有修工具或源码。

### 2.4 映射符号与ARM属性

按.symtab、正则 `^\$[atdx](?:\.\d+)?$` 统计；原始readelf输出留T/*symbols.txt，摘要与命令见E2。

| 项目 | 07运行文件 | 本轮运行文件 | 07.debug | 本轮.debug |
|---|---|---|---|---|
| .symtab | 无 | 无 | 有 | 有 |
| $a | 不可得 | 不可得 | 27 | 27 |
| $t | 不可得 | 不可得 | 5882 | **5883** |
| $d | 不可得 | 不可得 | 6489 | 6489 |
| .ARM.attributes | 无 | 无 | 有 | 有 |

保留方式与07一致；**数量并非完全相同：.text多一个$t（5861→5862），.plt仍21个**。没有把该差异隐藏成“数量一致”，也没有从数量变化臆测具体优化原因。CFLAGS未变、LDFLAGS仅增build-id已经独立核对；新增note后的ELF布局与07不必相同。不重做边界核对；属性原文仍含ARMv7、Thumb-2、VFPv3、NEONv1。

## 对设计的影响

- 核心build-id拆分预期通过：两份均为可读SHT_NOTE、20字节完全一致，两个链接正确，补齐07没有有ID正例的缺口。
- 与07数量对照的差异为$t多1；这不违反v0.5“调试文件提供映射符号”的要求，不宣称重新验证了所有指令边界。
- DWARF5 debugedit警告仍在，与v0.5已登记风险一致。除上述数量变化，没有发现本次身份拆分验证与v0.5预期矛盾的结果。
- 本轮为旧工具链显式SHA-1路径；新LLVM发布后仍须原样构建复核默认build-id及split结果，不从本次结果推断默认长度/取值。剩余RPi5核实项为dsoff、--buildid-mmap、页大小。本次没有执行后续实现或板上操作。

## 保存与边界

新RPM在T/rpms、解包树在T/extract，原始命令JSON/ELF输出在T，日志T/logs，临时FFmpeg分支在temp/v04/ffmpeg；构建根复用temp/GBS-ROOT-V04-FFMPEG。07原两份RPM保留temp/v04/baseline-rpms，07既有解包ELF/报告/证据不动。原src/ffmpeg、src/llvm保持干净。

本次指定Downloads文件的读取与移动属于用户授权例外；未触碰其他Downloads文件。没有新增已知其他边界例外，不修改认证。本轮未连接开发板，无板上占用变化需要记录。
