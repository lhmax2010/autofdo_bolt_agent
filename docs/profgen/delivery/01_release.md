# llvm-profgen 第一批有限范围发布记录

> 最新状态（2026-11-14，第二次配置准备，见§8）：PM已允许更换固定依赖快照，二进制SHA不要求与补丁9相同，验收以输出回归为准。但新指定Base URL为200、Unified URL为404，未通过启动门禁，本次没有运行GBS。下面§1–7保留第一次尝试的历史记录；“需相同依赖来源”的旧停止条件已由本次PM决定替代。当前仍无发布产物与发布回归结果。

2026-11-14。本轮**发布未完成，停在GBS仓库解析阶段**：已完成基线决定、两个独立树的补丁应用、源码等价核对；固定配置的两个snapshot URL返回HTTP 404，GBS退出1，未产生发布RPM。不得把本报告作为发布产物已验收的证明。

## 1. 范围、基线与本轮结论

依据[范围决定](00_scope_decision.md)及其第4节，发布基线是 `f999bd406c0a70fe8107aa992164fe6945c5d46a`，不是 `tizen_base` 新tip `61ef5d31ca91025c414c748477bef0c64ddfa67c`。后者三个提交只涉及打包及bootstrap/ThinLTO，不把其策略变化混入本次交付。

交付目标为补丁1–9的用户态DWARF IP路径：aarch64、armv7l Thumb-2/A32；不含pseudo-probe、原生`--perfdata`、内核profile或BOLT。CLI不改：`--ip-aggregation`仍必填，head/zero-fill/skid默认none；workflow明确传max/none/none/none，称“显式保守策略”，不是“默认值已验证”。三个质量门槛可选且无默认，由workflow的各包配置决定。

**统计质量等价与性能收益未验证。** 设计§10步骤5–7延期而非取消。预注册与既有证据保留，未登记修正案3；未来同对象workflow期间profile接触仍须按Q.5第17项披露。本轮没有连接板子、运行质量矩阵/性能测量或打开正式sample profile。

| 本轮验收项 | 实际结果 |
|---|---|
| 前向兼容应用 | 新tip上9/9干净应用；没有构建该树 |
| 发布树应用 | f999上9/9干净应用；最终工作区干净 |
| C2 / spec | 229文件，11724增加/20删除；只在允许目录；spec与f999相同 |
| 源码等价 | 源码/测试/CommandGuide共358文件，与补丁9开发树SHA逐项一致，差异0 |
| 正常非增量GBS | 已尝试，仓库解析失败，退出1；编译、Ninja、打包均未开始 |
| 发布RPM、安装路径、工具SHA/build-id、debug身份、version/help | 未执行：没有发布产物，不用旧增量RPM冒充 |
| 发布工具C1 | 未执行：没有发布工具 |
| 素材及14份历史导出与开发工具的逐字节比较 | 未执行：没有发布工具；不声称0差异 |
| lit替代依据 | 源码等价已闭合；引用既有补丁9正式%check结果，不在发布spec加入测试 |

## 2. 干净发布树与补丁序列

目录：`temp/llvm-profgen-release/`。从`src/llvm`执行`git clone --local --no-checkout`，检出f999，再按文件名顺序分别`git am`0001–0009。未squash、未amend，git am生成的消息和提交原样保留。命令均带`-c gc.auto=0 -c maintenance.auto=false`，提交身份为Hao Lin <hao.lin@samsung.com>。本地clone未设置任何Gerrit推送；无LLVM push。

发布树HEAD：`c8942ae1b53099a78a97dca2b64427af6e58432b`。git am的普通邮件主题解析生成的标题见原始日志；没有二次编辑消息。补丁邮件文件本身未修改。

| 补丁 | 邮件文件SHA-256 | 发布树提交 |
|---|---|---|
| 0001 | `7f2bc5b677492cdac6b82d682afb8f49029d3edbe029a1ba3fcd9ec0431d14c2` | `d1ba7bb9ddc6bc4e00d6bc860fff0f7d9d488d31` |
| 0002 | `d2db36a3765419d7d423510544a4fd0a47ad331c4a12ac1befa12052485a87bb` | `a361351e360ae15e9e352db727d177f5dcaf9ba4` |
| 0003 | `0eba5c805a1451eaf54583604cc1d112d2482663edfb28831237081e8c372108` | `792c7a7fad1945ceb5a0670a75970c441bc50360` |
| 0004 | `e8685bfcfc78f6e8ccccf9f8997fc4c283c35269c0a9850a24bfc0a343b503df` | `e802e2546e9f02433260856fa86a50a5108367a0` |
| 0005 | `fbc63b990a7cba1d07f8957fda920ebddb00eebebd1e1fec9257c9883050887e` | `3e9b77e2998efc02cda786c3a77a0c3d2be75fc4` |
| 0006 | `4002e01eaf449713b14deff4ec682d294d76e2cf7d15f60836dc4842c6e744f3` | `34787d22b5cf31e2e54e737f5627f6e891c83277` |
| 0007 | `78502de2024560efc8c1cd0536ebd16a049fc4f9313ef23fb514d265f50d3c60` | `7a2d54a7458f2e8dd25539e8cf6f3293f53d57de` |
| 0008 | `5e9444529afc778493deed02005c298aa23d6bbf44ced36ad72b0127a6cc6d6c` | `91be904558efbfa391872bc12a0e5662e3905129` |
| 0009 | `85842645dfcab06c3973e17194bf67d6a5bdaf52ffcb1bac92883eca72a36347` | `c8942ae1b53099a78a97dca2b64427af6e58432b` |

完整路径见[补丁清单](evidence/01/patch-manifest.json)，每次clone/checkout/am/status/diffstat的命令、退出码、耗时、原文见[操作记录](evidence/01/tree-operations.json)。两棵树的0003各出现一次同样的尾空白警告（`ff `，原补丁素材），仍退出0、无冲突；未自动修空白或改补丁。

等价方法：对源码目录`llvm/tools/llvm-profgen/`、测试目录`llvm/test/tools/llvm-profgen/`、`llvm/docs/CommandGuide/llvm-profgen.rst`的全部git跟踪文件，先核对路径集合，再按文件字节计算SHA-256，358/358一致。[逐文件证据](evidence/01/source-equivalence.json) / [汇总](evidence/01/source-summary.json)。spec SHA为 `7962d176484920de6138d70c7e8a8e1764dfada6655abf0332e9748167e889fd`，与`git show f999bd40:packaging/llvm.spec`原文一致；没有加入LLVM_INCLUDE_TESTS或%check。

`src/llvm`与`temp/llvm-profgen-enh`的HEAD、全部refs摘要、相对HEAD的diff摘要、spec摘要前后均相同：[前](evidence/01/original-trees.json) / [后](evidence/01/original-trees-after.json)。开发树的本地spec测试修改与现有build保留；并非在开发树撤销。开发工具SHA复核仍为 `2e8895afce661b5fdc8cacab2b3323496fca51af7bd7b51c3753aa8328b7d0d5`。

Gerrit sandbox：**项目名 `platform/upstream/llvm` / 分支：待用户确认 / commit ID：待推送**。上述本地发布HEAD只是候选，不是远端已发布ID。本轮未推任何Gerrit/LLVM引用，也未建hq分支。

## 3. 后续 rebase 说明

保留目录：`temp/llvm-profgen-forward-20261114/`。从`temp/llvm-upstream-query-20261114/`本地克隆，检出`61ef5d31ca91025c414c748477bef0c64ddfa67c`，依次应用相同邮件。9/9无冲突，最终HEAD `938292aaa49aade90325bb8d675cbe81bfcfa46d`，工作区干净。

| 补丁 | 前向应用结果 | 新tip临时树提交 |
|---|---|---|
| 0001 | 干净，退出0 | `9f5d813155f67348de3c612a387c477174cf23e7` |
| 0002 | 干净，退出0 | `9d00a626403bdbbf6a179443a4498e7ec29adb52` |
| 0003 | 干净，退出0 | `8c047651667fad72584a5a595cfd1bc1ca8dac46` |
| 0004 | 干净，退出0 | `028eaa1bf209df8c927ac4317a70609f2723cb17` |
| 0005 | 干净，退出0 | `51e2136398d7bdd28d4cace1b2200314a2c6527a` |
| 0006 | 干净，退出0 | `401739a1cae588f1f9a9f78ea8b973f973544d56` |
| 0007 | 干净，退出0 | `ed2618abb273d0775c27b597566730eb4c267858` |
| 0008 | 干净，退出0 | `6988aec7f293262892fc5627d5e381a95acb093a` |
| 0009 | 干净，退出0 | `938292aaa49aade90325bb8d675cbe81bfcfa46d` |

没有构建、测试或修改新tip的spec；干净应用只证明文本/补丁应用兼容，不证明新bootstrap/ThinLTO发布构建兼容。新增三个打包提交的路径证据见[分支查询报告](../../handover/02_llvm_branch.md)。本目录保留，未替代f999发布基线。

## 4. 正常非增量GBS尝试与阻塞

复用补丁9已用配置 `temp/gbs/gbs_llvm_x86_baseline.conf`，SHA `9044bdbf6914980e3f5f4af0f5e491632211e15bb05bddbed5b16ee1b95a745a`；未改内容。为保留原开发环境，命令级`--buildroot`指定全新`temp/GBS-ROOT-LLVM-RELEASE-20261114`，不在旧root清理或重建；由于仓库发现失败，新root目录尚未创建。

完整GBS命令（工作目录是独立发布树；由资源scope内worker执行）：

```bash
W=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent
cd "$W/temp/llvm-profgen-release"
HOME="$W/temp/gbs-home" GIT_CONFIG_NOSYSTEM=1 \
TMPDIR="$W/temp/gbs-tmp-llvm-x86" SUDO_ASKPASS=/bin/false \
GIT_CONFIG_COUNT=2 GIT_CONFIG_KEY_0=gc.auto GIT_CONFIG_VALUE_0=0 \
GIT_CONFIG_KEY_1=maintenance.auto GIT_CONFIG_VALUE_1=false \
gbs -c "$W/temp/gbs/gbs_llvm_x86_baseline.conf" build -A x86_64 \
  --spec llvm.spec --buildroot "$W/temp/GBS-ROOT-LLVM-RELEASE-20261114" \
  --threads 1 --define '_smp_mflags -j4' --define 'mlgo_build_jobs 4'
```

没有`--incremental`、`--noinit`、`--short-circuit`、`--clean`或spec修改。GBS专用HOME隔离仅用于GBS派生进程；结果仓库提交/推送使用正常认证环境。`sudo -n true`需要密码，但`sudo -n -l`显示GBS所需的`/usr/bin/build`等专用免密授权；因此未索要密码，实际失败也非sudo认证。无密码提示交互。

- 时间：北京时间2026-11-14 **16:39:53.720664–16:40:01.030441**；原始日志使用主机时区`-08:00`，UTC时刻相同。
- 墙钟：**7.310秒**；GBS真实退出码1，scope退出码1。
- 阶段：`generate repositories`，Ninja步数0（尚未启动）；RPM清单为空，工具/库SHA与build-id未产生。
- 日志：`temp/profgen-release-20261114/build.log`，SHA `884b4657a6911a7f07bef739a6366bded1cfd730b11b88a58cf93a89d52f86e4`，全文[入库日志](evidence/01/build.log)，结尾有时间、真实退出码、`已结束`和`ALL-END`。
- [命令JSON](evidence/01/build-command.json)、[构建结果](evidence/01/build-result.json)、[worker](evidence/01/build_worker.py)、[监督器](evidence/01/build_supervisor.py)。监督器会在scope异常退出时也写结束状态；此次正常捕获了非零GBS退出。

原始错误：

```text
error: <gbs>no available repositories found for arch x86_64 under the following repos:
https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261026.051209/repos/standard/packages/
https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261027.063617/repos/standard/packages/
```

随后对两地址各一次只读`curl --head --location --connect-timeout 10 --max-time 20 --retry 0`，均返回**HTTP/1.1 404 Not Found**（curl本身退出0只表示请求成功，不表示HTTP成功）。[完整请求与原文](evidence/01/repository-probe.json)。没有重试构建、切换其他日期仓库、使用旧增量RPM，或修改%files/spec绕过。继续发布需要恢复这两个固定快照，或由PM批准并核验一个可重建相同依赖的归档仓库/完整缓存方案；不同依赖快照不是本轮自动替换项。

资源：启动门禁MemAvailable≥14GiB，不查SwapFree；构建scope 10GiB/400%，nice19/ionice-c3，-j4。监督器为轻量3GiB/100%scope。构建内每60秒保存meminfo，每600秒输出free/uptime；此次仅7秒，保存启动采样，尚未到下一周期。已记录最低MemAvailable **22680793088 B**，build cgroup `memory.peak` **49094656 B**；OOM、OOM kill均0，无内存门禁终止。启动后有磁盘低于4GiB的保护，未触发。检查结束两scope均inactive/dead，没有遗留本轮构建进程：[最终核对](evidence/01/final-checks.json)。不能将一次短构建启动的峰值当作全量LLVM编译资源需求。

## 5. 回归证据与尚未执行的验收

发布树源码等价可以按用户授权替代本轮发布spec内的lit，但**不能替代新二进制C1和IP回归**。补丁9既有正式%check为86项：84 PASS、1 UNSUPPORTED、1 XFAIL、0 FAIL；C1两遍各636条、0差异。14历史输入当时各两遍确定，4份成功profile相同、10份既有generate/no usable samples失败保持；不能称14份都成功生成。出处：[补丁9报告](../impl/15_patch9_nonleaf_line0.md)，[lit](../impl/evidence/15/07_lit.json)，[C1](../impl/evidence/15/08_c1.json)，[重放](../impl/evidence/15/09_historical_replay.json)。本轮未重跑这些输入。

恢复构建后的待验收项：

1. 记录全部RPM SHA与包含profgen的RPM安装路径，解包工具及实际libLLVM；核对runtime/debuginfo身份、工具SHA/build-id、GBS加载器下version/help。
2. 用`tools/profgen/c1_baseline.py --compare tools/profgen/c1-baseline.json`、发布工具SHA及实际库目录，固定矩阵与既有基线比较，要求0差异，不覆盖基线。
3. 对补丁1素材及同一14历史输入，使用相同参数比较发布工具与补丁9开发工具的profile与质量JSON。仅标识/路径差异可作为预期项，并逐字段列出；任一非预期差异停止，不改补丁/spec。

## 6. 面向workflow的使用说明（既有工具契约，非本轮执行）

以下示例来自[交接报告C节](../../handover/01_pm_handover_report.md#c-工具使用与构建部署)及既有板上记录。本轮不接板；未来操作须有任务授权、身份/权限/空间门禁，目标ELF与调试文件须来自实际安装产物并同身份。采集与profile输出不等于质量或性能验证。

### 6.1 RPi4 / RPi5历史可用采集与严格导出

RPi4，固定间隔示例；`RUN`、媒体路径及变体路径换成已授权目录，使用variant环境，运行时须核对maps/build-id：

```bash
P=/opt/afdo_agent/tools/perf
RUN=/opt/afdo_agent/work/NEW_RUN
export LC_ALL=C LD_LIBRARY_PATH=/opt/afdo_agent/variants/ffmpeg-thumb-S/usr/lib:/opt/afdo_agent/lib
"$P" --buildid-dir "$RUN/buildid" record --buildid-mmap -e cycles -c 1000003 \
  -o "$RUN/perf.data" -- "$P" --buildid-dir "$RUN/buildid" stat \
  -x ';' -e cycles,instructions,task-clock -o "$RUN/perf-stat.csv" -- \
  gst-launch-1.0 -q filesrc location=/opt/afdo_agent/work/bbb_720p_h264_60s.mp4 \
  ! qtdemux ! h264parse ! avdec_h264 max-threads=1 ! video/x-raw,format=I420 \
  ! filesink location="$RUN/decoded.fifo" sync=false
```

FIFO需按既有`tools/profgen/board/common.sh`建立并由校验和进程读取；不是单独粘贴即可执行的采集脚本。RPi5历史报告09的短负载（系统/usr/lib64库，不能套到新build-id）：

```bash
P=/opt/afdo_agent/tools/perf
export LC_ALL=C LD_LIBRARY_PATH=/opt/afdo_agent/lib
"$P" --buildid-dir "$RUN/buildid" record --buildid-mmap -e cycles -c 1000003 \
  -o "$RUN/perf.data" -- gst-launch-1.0 -q \
  filesrc location=/opt/afdo_agent/work/bbb_720p_h264_60s.mp4 \
  ! qtdemux ! h264parse ! avdec_h264 ! identity eos-after=300 ! fakesink sync=false
```

两板共用严格导出字段；保留全映射/LOST/特殊DSO，不过滤，不带brstack：

```bash
"$P" --buildid-dir "$RUN/buildid" script -i "$RUN/perf.data" \
  --show-mmap-events --show-lost-events -F pid,tid,event,period,ip,dsoff > "$RUN/perfscript.txt"
"$P" --buildid-dir "$RUN/buildid" buildid-list -i "$RUN/perf.data" > "$RUN/buildid-list.txt"
"$P" --buildid-dir "$RUN/buildid" evlist -v -i "$RUN/perf.data" > "$RUN/evlist.txt"
```

stderr、退出码、原始perf.data、实际加载映像与环境记录也要保存。硬件cycles不可用不切软件事件。板上采用解包复制至`/opt/afdo_agent/variants/`并以LD_LIBRARY_PATH选库，不装卸RPM；debug留主机。具体脚本[collect.sh](../../../tools/profgen/board/collect.sh)、[common.sh](../../../tools/profgen/board/common.sh)。

### 6.2 profgen显式保守策略

此例使用仍已验收的开发工具路径，仅说明接口；本轮没有新发布工具路径。workflow接入发布RPM后应替换工具与libLLVM路径、核验SHA，不能宣称下例是本轮发布产物：

```bash
W=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent
R="$W/temp/GBS-ROOT-LLVM-X86/local/BUILD-ROOTS/scratch.x86_64.0"
L="$W/temp/llvm-profgen-enh/build"
export TMPDIR="$W/temp/tmp"
nice -n 19 ionice -c3 systemd-run --user --scope -p MemoryMax=3G -p CPUQuota=100% \
  "$R/lib64/ld-linux-x86-64.so.2" --library-path "$L/lib64:$R/lib64:$R/usr/lib64" \
  "$L/bin/llvm-profgen" --ip-samples \
  --binary="$W/temp/INPUT/runtime/libavcodec.so" \
  --debug-binary="$W/temp/INPUT/debug/libavcodec.so.debug" \
  --perfscript="$W/temp/INPUT/perfscript.txt" \
  --perf-buildid-list="$W/temp/INPUT/buildid-list.txt" \
  --binary-match-regex='^/opt/afdo_agent/variants/VARIANT/usr/lib/libavcodec\.so\.62\.11\.100$' \
  --ip-event=cycles --ip-weight=period --ip-aggregation=max \
  --ip-skid=none --ip-zero-fill=none --ip-head-samples=none \
  --format=extbinary --output="$W/temp/OUTPUT/profile.extbinary" \
  --quality-report="$W/temp/OUTPUT/quality.json"
```

INPUT/OUTPUT/VARIANT是占位符，aarch64通常usr/lib64；正则匹配原始DSO路径，完整匹配需^/$。event必须是实际完整事件名，含修饰符时不能截短。period默认取目标原始样本period的下中位数为P_ref；需要跨输入统一单位时显式指定`--ip-period-unit`，sample权重不能给此项。此说明不授权处理正式评估profile。

### 6.3 JSON判定与退出契约

schema_version=1。先看当前进程退出码和`verdict.conversion`，再查`verdict.identity`及`identity`证据、`usable_ratio_check`、`sample_threshold_check`、`lost_ratio_check`。成功退出0，失败非0（不假定所有错误都只返回1）；`failure_stage`/`reason`解释失败。三个阈值`--ip-min-usable-ratio`、`--ip-min-target-samples`、`--ip-max-lost-ratio`可选、无默认，workflow按包决定。

`sampling_adequacy`仅insufficient/unknown，退出0和verified身份不代表统计质量充分。工具的throttle未知，不替代板上资格判断。未知字段用unknown，确认不存在用none，成功failure字段可null；详细schema在补丁7–9的CommandGuide。报告包含输入/身份、语义、映射、样本、ISA、边界、LOST、覆盖、GNU Thumb规范化、warnings/verdict；非叶子line0排除有独立子项。

失败时旧profile保持不变；非路径冲突失败原子替换失败JSON。路径冲突（两个输出互为别名、输出与输入别名、output为`-`）在加载/建临时文件前拒绝，两种输出都不写，是故意不写失败报告的唯一例外。报告自身写入/提交失败可能无新JSON，旧报告保留，必须看本次stderr/退出码，不能复用旧ok报告判成功。profile与report不是断电原子的双文件事务。

## 7. 已知局限与下一停止点

- 发布构建当前被固定依赖snapshot的404阻塞。无新工具、RPM或发布回归结果；必须先解决同依赖来源可恢复性，再继续三.3–三.5。
- 聚合方式没有CLI默认；显式保守策略没有统计最优/等价或性能收益结论。三个门槛仍由workflow包配置决定。
- `ENABLE_LINKER_BUILD_ID`发布后复核未闭合；被采样构建仍须显式`-Wl,--build-id=sha1`，并以安装产物的ID核对debug，不只看BUILD中ELF。
- armv7l Clang 22.1.8 probe构建崩溃挂账保留，本批不交付probe。
- 部分temp原始输入、GBS root、开发二进制和源树仅在主机；结果仓库不包含LLVM源码树。可公开复核的小证据在[evidence索引](evidence/01/index.json)，每个文件小于1MB。
- 旧开发spec测试改动保留供复现；独立发布spec已干净。未修改设计v1.8或既有验收证据，未删除任何temp目录，未触碰三个受保护本地配置。

本轮保存上述事实后停止，等待固定依赖仓库恢复或新的明确依赖来源决定。不是等待Gerrit推送授权来继续构建；本轮始终不推LLVM/Gerrit。

## 8. 更换固定snapshot的授权与预检停止（2026-11-14）

### 8.1 本轮PM决定及新配置

PM允许用当前可用的固定snapshot重试。发布基线仍为f999，发布树HEAD仍为 `c8942ae1b53099a78a97dca2b64427af6e58432b`，启动前核对工作区干净；不改spec、不重放补丁。编译依赖不同可能导致工具二进制SHA与补丁9不同，这是预期；仍须C1为0差异、IP profile及质量JSON与开发工具逐字节一致（工具路径/SHA等标识差异逐项说明），不得放宽输出回归。

从旧配置复制生成 `temp/gbs/gbs_llvm_x86_release.conf`，只替换两条仓库URL，未改其他字节，原配置保留：

| 项目 | SHA-256 |
|---|---|
| 原 `gbs_llvm_x86_baseline.conf` | `9044bdbf6914980e3f5f4af0f5e491632211e15bb05bddbed5b16ee1b95a745a` |
| 新 `gbs_llvm_x86_release.conf` | `44df6f67a6897a9d0537e931fded5e8bcf3b1e95f8e47ff1afe1d4dd95a270ff` |

[配置diff](evidence/02/config.diff) / [路径与SHA](evidence/02/config.json)。没有使用latest别名，也没有读取根目录受保护的三项配置。

### 8.2 地址预检原文与停止点

2026-11-14 00:53:46–00:53:47 PST（HTTP Date为08:53:46–08:53:47 GMT），每个地址执行一次 `curl --head --location --connect-timeout 10 --max-time 30 --retry 0 --write-out '\nHTTP_STATUS=%{http_code}\n' URL`：

| 仓库 | 固定snapshot | HTTP结果 |
|---|---|---|
| Base | `tizen-base-toolchain_20261111.130848` | **200 OK** |
| Unified | `tizen-unified-toolchain_20261003.102419` | **404 Not Found** |

完整URL：

```text
https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261111.130848/repos/standard/packages/
https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261003.102419/repos/standard/packages/
```

两次curl进程均退出0，但第二次HTTP失败；不能用curl退出0充当地址可用。完整命令、响应头、stdout/stderr见[snapshot-head.json](evidence/02/snapshot-head.json)。PM此前对Unified可用性的描述与本次实测不同，此处仅记录指定地址结果，不猜测应使用哪个ID或尝试其他组合。

因“构建前两地址均200”未满足，本次**未启动GBS**、未进行依赖解析/编译/打包。GBS退出码与墙钟均为“不适用（未运行）”，不能沿用第一次的1/7.310秒。本次预检执行器因非200断言退出1，结束状态见[preflight-result.json](evidence/02/preflight-result.json)和[带时间ALL-END](evidence/02/end.log)。没有重试、修改spec或用旧依赖缓存绕过。

构建原计划：在独立发布树使用新conf、全新 `temp/GBS-ROOT-LLVM-RELEASE-20261114b`，正常非增量GBS、10G/400%scope、-j4；没有创建该buildroot。本轮仅轻量串行任务，3G/100%scope、nice19/ionice-c3、启动MemAvailable≥4GiB。[内存原文及库存任务peak](evidence/02/inventory-resource.json)；短命令测量不代表完整构建峰值。

### 8.3 旧依赖缓存与版本（只读，未使用）

在 `temp/GBS-ROOT-LLVM-X86/local/cache/` 下保留 **122个RPM文件，总计195,048,240字节（约186.012MiB）**，扫描无权限/读取错误。本轮仅列文件路径和大小，不复制、不用作新构建输入。[完整清单](evidence/02/old-cache.json)。这些是原补丁9构建根现存缓存；“缓存存在”不证明每个文件都参与了补丁9那次构建，也不证明它们足以完成离线正常构建。

通过 `sudo -n /usr/sbin/chroot <旧root> /usr/bin/rpm -q` 只读查询原root，退出0，无密码交互。以下为保留的补丁9构建root当前安装版本；不是本轮解析出的新依赖。没有把该现状凭空当作逐包历史安装日志。

| 工具 | 原补丁9构建root现存名称-版本-release（x86_64） | 新发布依赖 |
|---|---|---|
| gcc | gcc-14.2.0-1.6 | 未解析 |
| binutils | binutils-2.43-1.6 | 未解析 |
| cmake | cmake-3.31.2-1.6 | 未解析 |
| python3 | python3-3.14.2-1.6 | 未解析 |
| ninja | ninja-1.13.1-1.5 | 未解析 |

[原始查询命令与输出](evidence/02/old-dependency-versions.json)。由于新构建未启动，实际解析包清单、逐包来源仓库及新旧差异还不能填写；没有虚构版本一致性。

### 8.4 产物、存档、回归与后续发布

- 没有新RPM、安装产物SHA/build-id或version/help结果；没有运行发布C1或素材/14历史输入重放，不能记为回归通过。
- 成功后预定存档位置为 `temp/gbs-deps-archive/llvm-release-20261114/`，**本轮未创建依赖存档、未复制任何依赖RPM**，大小不适用。待实际下载依赖齐全后才能生成SHA清单及可核查的本地仓库重建命令；不把旧缓存当作本次存档。
- 本轮停止，故不执行条件性的Gerrit sandbox推送或hq创建。`sandbox/lhmax2025/afdo_profgen`是本轮用户提及的唯一允许后续目标，不能把它理解为当前已推送。此前“sandbox推送＋hq第一版”指令全文在当前会话/仓库未找到，已请求补充；这不影响本次明确的URL停止结论。
- 已知局限更新（PM要求原文）：**“Tizen snapshot 会被定期删除；本次构建所用 snapshot ID 如下，被删除后用当前 snapshot 重建，llvm-profgen 为纯源码改动，以工具输出回归为准”。** 本次“所用”ID指§8.2的计划配置，实际未构建；换用当前snapshot仍须固定ID、留存依赖清单并通过完整输出回归，不能自动切latest或跳过门禁。
- 等待用户提供可用的固定Unified URL或确认服务恢复后再继续；本轮不尝试其他snapshot组合。既有证据、设计v1.8、补丁、原开发树和所有既有temp目录均保留。

本轮证据索引：[evidence/02/index.json](evidence/02/index.json)。

证据容器检查：config.diff的两条空白上下文行保留标准unified diff的单空格前缀，Git将其报告为新增文件尾空白；原始diff不删改。除该证据容器外的本次文件通过diff --check，详见[evidence/02/diff-check.json](evidence/02/diff-check.json)。
