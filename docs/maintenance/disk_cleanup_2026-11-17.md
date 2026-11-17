# 磁盘清理核查：2026-11-17

范围仅WORKDIR；未执行删除。B类需要的“无进程使用”条件未能完整证实，因此按“拿不准保留”跳过。当前空间已满足50GiB启动门槛，C类决定不阻塞M1。

## 清理前后

前：

```text
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       1.8T  1.6T  106G  94% /home
```
后：

```text
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       1.8T  1.6T  106G  94% /home
```

删除总量 **0 B**，未使用sudo，未卸载挂载，未停止其他进程。前后空间变化由文件系统上的其他活动及本次日志引起，不计为清理收益。
du两次均退出1：有root拥有的目录权限不足，可读WORKDIR约160.15GiB、temp约146.73GiB，大小为下界。原始命令、stdout/stderr在temp/disk-cleanup-20261117/。
findmnt当前命名空间未见WORKDIR挂载；/proc有979项cwd/root/fd/maps读取被拒，无法证明所有候选均无人使用。未获授权扩展sudo读取，不用不完整检查作为删除依据。

## ≥200MiB目录清单（祖先/后代重叠，不可相加）

| 路径 | GiB（下界） | 修改时间 | 所属任务 | 分类 |
|---|---:|---|---|---|
| docs | 0.835 | 2026-11-16T06:25:03.304294-08:00 | 历史内核/工具链/其他 | retained |
| docs/profgen | 0.819 | 2026-11-14T00:09:11.427544-08:00 | profgen评估/实现 | retained |
| src | 12.484 | 2026-10-27T01:52:36.933835-07:00 | 历史内核/工具链/其他 | A |
| src/gstreamer | 0.561 | 2026-10-27T01:51:52.121833-07:00 | 历史内核/工具链/其他 | A |
| src/linux-rpi | 4.800 | 2026-10-27T01:34:49.814908-07:00 | 历史内核/工具链/其他 | A |
| src/llvm | 6.978 | 2026-10-27T00:37:12.279655-07:00 | 历史内核/工具链/其他 | A |
| temp/GBS-ROOT-FFMPEG-M1-A32-20261114 | 1.518 | 2026-11-14T04:38:55.850186-08:00 | M1试跑/实现/构建 | B-skipped |
| temp/GBS-ROOT-FFMPEG-M1-A32-20261114-FIX1 | 1.658 | 2026-11-14T05:30:55.492470-08:00 | M1试跑/实现/构建 | B-skipped |
| temp/GBS-ROOT-FFMPEG-M1-A32-20261114-FIX1/local | 1.658 | 2026-11-14T05:31:06.815310-08:00 | M1试跑/实现/构建 | B-skipped |
| temp/GBS-ROOT-FFMPEG-M1-A32-20261114/local | 1.518 | 2026-11-14T04:39:05.541187-08:00 | M1试跑/实现/构建 | B-skipped |
| temp/GBS-ROOT-FFMPEG-M1-THUMB-20261114 | 1.397 | 2026-11-14T04:34:49.995176-08:00 | M1试跑/实现/构建 | B-skipped |
| temp/GBS-ROOT-FFMPEG-M1-THUMB-20261114-FIX1 | 1.651 | 2026-11-14T05:26:06.651298-08:00 | M1试跑/实现/构建 | B-skipped |
| temp/GBS-ROOT-FFMPEG-M1-THUMB-20261114-FIX1/local | 1.651 | 2026-11-14T05:26:17.422299-08:00 | M1试跑/实现/构建 | B-skipped |
| temp/GBS-ROOT-FFMPEG-M1-THUMB-20261114/local | 1.397 | 2026-11-14T04:35:00.767177-08:00 | M1试跑/实现/构建 | B-skipped |
| temp/GBS-ROOT-LLVM-RELEASE-20261114c | 26.536 | 2026-11-14T01:10:30.561690-08:00 | 历史内核/工具链/其他 | A |
| temp/GBS-ROOT-LLVM-RELEASE-20261114c/local | 26.536 | 2026-11-14T01:12:25.136694-08:00 | 历史内核/工具链/其他 | A |
| temp/GBS-ROOT-LLVM-X86 | 2.202 | 2026-10-28T05:33:46.546169-07:00 | 历史内核/工具链/其他 | A |
| temp/GBS-ROOT-LLVM-X86/local | 2.202 | 2026-10-28T05:33:53.256169-07:00 | 历史内核/工具链/其他 | A |
| temp/GBS-ROOT-RPI4-PMUV3 | 8.698 | 2026-10-27T20:56:59.781939-07:00 | 历史内核/工具链/其他 | B-skipped |
| temp/GBS-ROOT-RPI4-PMUV3/local | 8.698 | 2026-10-27T21:02:18.311952-07:00 | 历史内核/工具链/其他 | B-skipped |
| temp/GBS-ROOT-RPI4-SPIKE | 1.738 | 2026-10-29T08:40:05.470040-07:00 | 历史内核/工具链/其他 | B-skipped |
| temp/GBS-ROOT-RPI4-SPIKE/local | 1.738 | 2026-10-29T08:40:13.288041-07:00 | 历史内核/工具链/其他 | B-skipped |
| temp/GBS-ROOT-RPI5-SPIKE | 2.078 | 2026-10-28T04:15:29.164983-07:00 | 历史内核/工具链/其他 | B-skipped |
| temp/GBS-ROOT-RPI5-SPIKE/local | 2.078 | 2026-10-28T04:15:36.976983-07:00 | 历史内核/工具链/其他 | B-skipped |
| temp/GBS-ROOT-V04-FFMPEG | 2.603 | 2026-10-30T05:35:59.480030-07:00 | 历史内核/工具链/其他 | B-skipped |
| temp/GBS-ROOT-V04-FFMPEG/local | 2.603 | 2026-10-30T05:36:09.288030-07:00 | 历史内核/工具链/其他 | B-skipped |
| temp/autofdo | 0.535 | 2026-10-28T04:11:39.673135-07:00 | 历史内核/工具链/其他 | retained |
| temp/autofdo/testdata | 0.437 | 2026-10-28T04:11:39.672974-07:00 | 历史内核/工具链/其他 | retained |
| temp/board-round1 | 0.459 | 2026-11-05T04:11:09.252538-08:00 | profgen评估/实现 | A |
| temp/board-round1-patch8 | 0.868 | 2026-11-05T09:39:14.754319-08:00 | profgen评估/实现 | retained |
| temp/board-round1-patch8/runs | 0.792 | 2026-11-05T09:33:52.630306-08:00 | profgen评估/实现 | retained |
| temp/board-round1-resume2 | 0.293 | 2026-11-05T05:25:56.396716-08:00 | profgen评估/实现 | A |
| temp/board-round1-retry | 1.507 | 2026-11-05T21:16:56.896980-08:00 | profgen评估/实现 | C |
| temp/board-round1-retry/extras-fixed | 0.252 | 2026-11-05T21:05:21.104470-08:00 | profgen评估/实现 | retained |
| temp/board-round1-retry/extras-system | 0.219 | 2026-11-05T21:10:52.366966-08:00 | profgen评估/实现 | retained |
| temp/board-round1-retry/runs | 0.896 | 2026-11-05T20:54:06.769467-08:00 | profgen评估/实现 | retained |
| temp/coverage-whole-8g-20261109 | 0.571 | 2026-11-09T00:34:47.429889-08:00 | 历史内核/工具链/其他 | A |
| temp/eval-prep11 | 1.905 | 2026-11-04T01:01:13.939657-08:00 | profgen评估/实现 | C |
| temp/eval-prep11/all-elf | 0.675 | 2026-11-04T00:58:20.428393-08:00 | profgen评估/实现 | retained |
| temp/eval-prep11/build | 0.355 | 2026-11-04T00:56:06.754645-08:00 | profgen评估/实现 | retained |
| temp/eval-prep11/verified | 0.404 | 2026-11-04T00:57:57.441114-08:00 | profgen评估/实现 | retained |
| temp/gbs-deps-archive | 0.435 | 2026-11-14T04:46:03.336203-08:00 | 历史内核/工具链/其他 | A |
| temp/gbs-deps-archive/ffmpeg-armv7l-20261114 | 0.253 | 2026-11-14T05:36:51.065424-08:00 | 历史内核/工具链/其他 | A |
| temp/gerrit-361624-ssh | 3.670 | 2026-11-16T09:30:45.801736-08:00 | 361624验证 | A |
| temp/gerrit-361624-ssh/objects | 3.613 | 2026-11-16T09:30:45.795736-08:00 | 361624验证 | A |
| temp/linux-rpi-pmuv3 | 1.610 | 2026-10-27T05:13:23.344116-07:00 | 历史内核/工具链/其他 | A |
| temp/linux-rpi-pmuv3-am-check | 1.610 | 2026-10-28T01:13:50.832860-07:00 | 历史内核/工具链/其他 | C |
| temp/linux-rpi-pmuv3-am-check/drivers | 1.055 | 2026-10-28T01:13:49.065415-07:00 | 历史内核/工具链/其他 | C |
| temp/linux-rpi-pmuv3-gerrit | 1.610 | 2026-10-28T01:08:28.794402-07:00 | 历史内核/工具链/其他 | C |
| temp/linux-rpi-pmuv3-gerrit/drivers | 1.055 | 2026-10-28T01:08:12.692533-07:00 | 历史内核/工具链/其他 | C |
| temp/linux-rpi-pmuv3/drivers | 1.055 | 2026-10-27T05:13:15.421047-07:00 | 历史内核/工具链/其他 | A |
| temp/llvm-profgen-enh | 23.323 | 2026-10-28T06:23:29.598288-07:00 | profgen评估/实现 | A |
| temp/llvm-profgen-enh/build | 20.650 | 2026-11-06T06:00:49.427227-08:00 | profgen评估/实现 | A |
| temp/llvm-profgen-enh/clang | 0.449 | 2026-10-28T05:30:40.782290-07:00 | profgen评估/实现 | A |
| temp/llvm-profgen-enh/llvm | 1.326 | 2026-10-28T05:30:50.800107-07:00 | profgen评估/实现 | A |
| temp/llvm-profgen-enh/mlgo_verify_assets | 0.237 | 2026-06-21T17:00:00-07:00 | profgen评估/实现 | A |
| temp/llvm-profgen-forward-20261114 | 2.441 | 2026-11-14T00:37:03.474733-08:00 | profgen评估/实现 | C |
| temp/llvm-profgen-forward-20261114/clang | 0.449 | 2026-11-14T00:36:37.667036-08:00 | profgen评估/实现 | retained |
| temp/llvm-profgen-forward-20261114/llvm | 1.326 | 2026-11-14T00:36:58.771360-08:00 | profgen评估/实现 | C |
| temp/llvm-profgen-release | 6.961 | 2026-11-14T00:37:37.802951-08:00 | profgen评估/实现 | C |
| temp/llvm-profgen-release/.git | 4.540 | 2026-11-14T02:37:09.688896-08:00 | profgen评估/实现 | C |
| temp/llvm-profgen-release/clang | 0.449 | 2026-11-14T00:37:17.216925-08:00 | profgen评估/实现 | retained |
| temp/llvm-profgen-release/llvm | 1.326 | 2026-11-14T00:37:33.928329-08:00 | profgen评估/实现 | C |
| temp/llvm-profgen-sandbox-verify-20261114 | 2.789 | 2026-11-14T02:39:36.815042-08:00 | profgen评估/实现 | C |
| temp/llvm-profgen-sandbox-verify-20261114/.git | 0.368 | 2026-11-14T02:39:37.776902-08:00 | profgen评估/实现 | retained |
| temp/llvm-profgen-sandbox-verify-20261114/clang | 0.449 | 2026-11-14T02:39:04.226650-08:00 | profgen评估/实现 | retained |
| temp/llvm-profgen-sandbox-verify-20261114/llvm | 1.326 | 2026-11-14T02:39:29.311256-08:00 | profgen评估/实现 | C |
| temp/m1-pilot-v02-20261116 | 6.115 | 2026-11-16T01:59:55.642663-08:00 | M1试跑/实现/构建 | C |
| temp/m1-pilot-v02-20261116/build | 6.013 | 2026-11-16T01:53:07.524647-08:00 | M1试跑/实现/构建 | C |
| temp/m1-target-20261114 | 3.661 | 2026-11-14T06:20:17.204427-08:00 | M1试跑/实现/构建 | C |
| temp/m1-target-20261114/weekend-j2 | 3.440 | 2026-11-14T06:42:08.922479-08:00 | M1试跑/实现/构建 | C |
| temp/media_src | 1.669 | 2026-11-16T11:04:34.242959-08:00 | 历史内核/工具链/其他 | C |
| temp/prep-identity-gate | 0.615 | 2026-11-10T21:09:29.005101-08:00 | profgen评估/实现 | retained |
| temp/prep-identity-gate/ordinary-full-checks | 0.556 | 2026-11-10T20:09:47.290959-08:00 | profgen评估/实现 | retained |
| temp/prep-ruling2 | 0.305 | 2026-11-10T19:23:17.739848-08:00 | profgen评估/实现 | retained |
| temp/prep-ruling3-4 | 2.246 | 2026-11-10T23:24:54.293423-08:00 | profgen评估/实现 | C |
| temp/prep-ruling3-4/first-full-identity-evidence | 0.256 | 2026-11-10T23:04:12.967128-08:00 | profgen评估/实现 | retained |
| temp/prep-ruling3-4/revision1-provisional | 0.310 | 2026-11-10T23:16:44.483404-08:00 | profgen评估/实现 | retained |
| temp/prep-static-gate | 0.814 | 2026-11-10T21:52:18.677203-08:00 | profgen评估/实现 | retained |
| temp/prep-v17 | 0.767 | 2026-11-11T04:52:22.841203-08:00 | profgen评估/实现 | retained |
| temp/prep-v18 | 0.403 | 2026-11-11T05:47:19.379333-08:00 | profgen评估/实现 | retained |
| temp/profgen-baseline-tool | 1.079 | 2026-11-01T19:01:36.357946-08:00 | profgen评估/实现 | A |
| temp/profgen-patch5 | 0.425 | 2026-11-02T22:21:43.408850-08:00 | profgen评估/实现 | retained |
| temp/profgen-patch8 | 0.221 | 2026-11-05T07:43:38.667044-08:00 | profgen评估/实现 | A |
| temp/profgen-patch8-amend | 1.115 | 2026-11-05T19:12:05.869195-08:00 | profgen评估/实现 | C |
| temp/profgen-patch9 | 1.094 | 2026-11-06T06:23:14.807280-08:00 | profgen评估/实现 | C |
| temp/profgen-patch9/prebuild-tool | 1.085 | 2026-11-06T04:36:14.520026-08:00 | profgen评估/实现 | C |
| temp/registration-batch1 | 1.916 | 2026-11-11T06:36:04.679450-08:00 | profgen评估/实现 | C |
| temp/registration-batch1/detail-tables | 0.196 | 2026-11-11T06:36:06.502189-08:00 | profgen评估/实现 | retained |
| temp/registration-batch1/ffmpeg-a32 | 0.833 | 2026-11-11T06:32:09.266440-08:00 | profgen评估/实现 | retained |
| temp/registration-batch1/ffmpeg-thumb | 0.865 | 2026-11-11T06:31:55.566440-08:00 | profgen评估/实现 | retained |
| temp/round1-thumb-line0 | 0.349 | 2026-11-05T06:02:17.211803-08:00 | 历史内核/工具链/其他 | retained |
| temp/rpi4-prefreeze | 0.242 | 2026-10-29T08:55:51.036078-07:00 | 历史内核/工具链/其他 | retained |
| temp/v04 | 0.207 | 2026-10-30T06:19:37.117134-07:00 | 历史内核/工具链/其他 | retained |
| temp/verify-361624-fix-20261116 | 12.627 | 2026-11-16T08:01:09.976523-08:00 | 361624验证 | B-skipped |
| temp/verify-361624-fix-20261116/root-x86_64 | 4.879 | 2026-11-16T07:41:20.828476-08:00 | 361624验证 | B-skipped |
| temp/verify-361624-fix-20261116/root-x86_64-retry-executor | 5.293 | 2026-11-16T07:50:16.405497-08:00 | 361624验证 | B-skipped |
| temp/verify-361624-fix-20261116/source | 2.419 | 2026-11-16T07:16:31.679536-08:00 | 361624验证 | B-skipped |
| temp/verify-361624-fix-v2-20261116 | 2.420 | 2026-11-16T08:12:51.278903-08:00 | 361624验证 | B-skipped |
| temp/verify-361624-fix-v2-20261116/source | 2.419 | 2026-11-16T08:10:12.406544-08:00 | 361624验证 | B-skipped |
| temp/verify-361624-fix-v3-20261116 | 9.037 | 2026-11-16T10:04:31.301816-08:00 | 361624验证 | B-skipped |
| temp/verify-361624-fix-v3-20261116/root-x86_64 | 6.062 | 2026-11-16T09:48:44.012779-08:00 | 361624验证 | B-skipped |
| temp/verify-361624-fix-v3-20261116/source | 2.419 | 2026-11-16T09:30:44.220100-08:00 | 361624验证 | B-skipped |
| temp/verify-361624-fix-v3-20261116/verification | 0.555 | 2026-11-16T10:00:39.567807-08:00 | 361624验证 | B-skipped |
| temp/workflow-p1p2-20261116 | 1.521 | 2026-11-16T05:26:15.147154-08:00 | M1试跑/实现/构建 | C |
| temp/workflow-p1p2-20261116/root-afdo-diag | 1.362 | 2026-11-16T05:03:30.869100-08:00 | M1试跑/实现/构建 | B-skipped |

## B类删除清单及跳过项

删除清单为空。以下为候选范围，不能对整个外层目录执行rm（含RPM/日志）；本轮也未删除其子root：

- temp/GBS-ROOT-FFMPEG-M1-A32-20261114：1.518GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/GBS-ROOT-FFMPEG-M1-A32-20261114-FIX1：1.658GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/GBS-ROOT-FFMPEG-M1-A32-20261114-FIX1/local：1.658GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/GBS-ROOT-FFMPEG-M1-A32-20261114/local：1.518GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/GBS-ROOT-FFMPEG-M1-THUMB-20261114：1.397GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/GBS-ROOT-FFMPEG-M1-THUMB-20261114-FIX1：1.651GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/GBS-ROOT-FFMPEG-M1-THUMB-20261114-FIX1/local：1.651GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/GBS-ROOT-FFMPEG-M1-THUMB-20261114/local：1.397GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/GBS-ROOT-RPI4-PMUV3：8.698GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/GBS-ROOT-RPI4-PMUV3/local：8.698GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/GBS-ROOT-RPI4-SPIKE：1.738GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/GBS-ROOT-RPI4-SPIKE/local：1.738GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/GBS-ROOT-RPI5-SPIKE：2.078GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/GBS-ROOT-RPI5-SPIKE/local：2.078GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/GBS-ROOT-V04-FFMPEG：2.603GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/GBS-ROOT-V04-FFMPEG/local：2.603GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/verify-361624-fix-20261116：12.627GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/verify-361624-fix-20261116/root-x86_64：4.879GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/verify-361624-fix-20261116/root-x86_64-retry-executor：5.293GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/verify-361624-fix-20261116/source：2.419GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/verify-361624-fix-v2-20261116：2.420GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/verify-361624-fix-v2-20261116/source：2.419GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/verify-361624-fix-v3-20261116：9.037GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/verify-361624-fix-v3-20261116/root-x86_64：6.062GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/verify-361624-fix-v3-20261116/source：2.419GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/verify-361624-fix-v3-20261116/verification：0.555GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- temp/workflow-p1p2-20261116/root-afdo-diag：1.362GiB，跳过；可重建候选，但/proc占用检查不完整；不能把内含RPM/日志/原始调试证据一并删除。
- 失败共享克隆 attempt-02/ffmpeg 与 temp/tmp 旧临时项：跳过，进程占用检查不完整。

## C类建议（等待用户决定，不删除）

| 路径 | GiB | 用途与重建代价 |
|---|---:|---|
| temp/board-round1-retry | 1.507 | profgen评估/实现；源码/构建树通常可重建，但需先辨别唯一证据；评估原始采集不可由源码重建，须保留或另行归档。耗时未经重新估算。 |
| temp/eval-prep11 | 1.905 | profgen评估/实现；源码/构建树通常可重建，但需先辨别唯一证据；评估原始采集不可由源码重建，须保留或另行归档。耗时未经重新估算。 |
| temp/linux-rpi-pmuv3-am-check | 1.610 | 历史内核/工具链/其他；源码/构建树通常可重建，但需先辨别唯一证据；评估原始采集不可由源码重建，须保留或另行归档。耗时未经重新估算。 |
| temp/linux-rpi-pmuv3-gerrit | 1.610 | 历史内核/工具链/其他；源码/构建树通常可重建，但需先辨别唯一证据；评估原始采集不可由源码重建，须保留或另行归档。耗时未经重新估算。 |
| temp/llvm-profgen-forward-20261114 | 2.441 | profgen评估/实现；源码/构建树通常可重建，但需先辨别唯一证据；评估原始采集不可由源码重建，须保留或另行归档。耗时未经重新估算。 |
| temp/llvm-profgen-release | 6.961 | profgen评估/实现；源码/构建树通常可重建，但需先辨别唯一证据；评估原始采集不可由源码重建，须保留或另行归档。耗时未经重新估算。 |
| temp/llvm-profgen-sandbox-verify-20261114 | 2.789 | profgen评估/实现；源码/构建树通常可重建，但需先辨别唯一证据；评估原始采集不可由源码重建，须保留或另行归档。耗时未经重新估算。 |
| temp/m1-pilot-v02-20261116 | 6.115 | M1试跑/实现/构建；源码/构建树通常可重建，但需先辨别唯一证据；评估原始采集不可由源码重建，须保留或另行归档。耗时未经重新估算。 |
| temp/m1-target-20261114 | 3.661 | M1试跑/实现/构建；源码/构建树通常可重建，但需先辨别唯一证据；评估原始采集不可由源码重建，须保留或另行归档。耗时未经重新估算。 |
| temp/media_src | 1.669 | 历史内核/工具链/其他；源码/构建树通常可重建，但需先辨别唯一证据；评估原始采集不可由源码重建，须保留或另行归档。耗时未经重新估算。 |
| temp/prep-ruling3-4 | 2.246 | profgen评估/实现；源码/构建树通常可重建，但需先辨别唯一证据；评估原始采集不可由源码重建，须保留或另行归档。耗时未经重新估算。 |
| temp/profgen-patch8-amend | 1.115 | profgen评估/实现；源码/构建树通常可重建，但需先辨别唯一证据；评估原始采集不可由源码重建，须保留或另行归档。耗时未经重新估算。 |
| temp/profgen-patch9 | 1.094 | profgen评估/实现；源码/构建树通常可重建，但需先辨别唯一证据；评估原始采集不可由源码重建，须保留或另行归档。耗时未经重新估算。 |
| temp/registration-batch1 | 1.916 | profgen评估/实现；源码/构建树通常可重建，但需先辨别唯一证据；评估原始采集不可由源码重建，须保留或另行归档。耗时未经重新估算。 |
| temp/workflow-p1p2-20261116 | 1.521 | M1试跑/实现/构建；源码/构建树通常可重建，但需先辨别唯一证据；评估原始采集不可由源码重建，须保留或另行归档。耗时未经重新估算。 |
- temp/media_src/Sintel.2010.1080p.mkv：1,180,090,590字节（1.099GiB），官方可重新下载；本次历史下载约133秒，未来可达性/耗时未知。输出测试片必须保留。

## WORKDIR外仅观察

从/proc的cwd链接观察到 /home/linhao/Toolchain/development/llvm-optimize；未遍历、du、读取其项目文件或触碰它。大小未知，不把全文件系统其余用量归因于该项目。

## 证据

classification.json逐目录记录真实路径、符号链接、当前挂载和可见占用；process-and-mounts.json列出不可读项。原件在temp/disk-cleanup-20261117/，提交时保留摘要与SHA索引。

补充口径：C表中的父目录只表示需要决定其内部可重建部分的范围，不是整目录删除建议。
其中m1-pilot/build/repo、所有RPM/日志/证据原件等A类内容永远优先保留。
两次du的硬链接计数次序及扫描期间变化可能造成同一路径数值不同；保留两份原文，不把目录相加或差值算作清理收益。
清理前Available=113,591,267,328 B，后=113,576,747,008 B；本次没有删除，约13.85MiB变化不归因于清理。
提交证据位于 [evidence/disk-cleanup-20261117](evidence/disk-cleanup-20261117/index.json)。
