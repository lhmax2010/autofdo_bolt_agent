# AutoFDO Workflow: Weekly Report

Week of 2026-11-16 to 2026-11-20

## 1. Summary

- **M1 is complete.** The automated workflow ran FFmpeg AutoFDO on RPi4 (Thumb-2) from one command, end to end. Both test videos decode significantly faster with the AutoFDO build:

  | Test input | Decode wall-time change | 95% CI | Verdict |
  |---|---:|---|---|
  | Tears of Steel 720p (primary) | **−1.92%** | [−2.35%, −1.45%] | faster |
  | Sintel 1080p (secondary) | **−1.49%** | [−1.86%, −1.19%] | faster |

- **M2a (FFmpeg AutoFDO on RPi5, aarch64) has started.**
  - the workflow now supports both boards;
  - the RPi5 passed the environment checks;
  - the package snapshot is selected.

  The builds are next.

## 2. Roadmap Status

| Milestone | Content | Status |
|---|---|---|
| M1 | FFmpeg AutoFDO, RPi4 (armv7l, Thumb-2) | **Done** |
| M2a | FFmpeg AutoFDO, RPi5 (aarch64) | **In progress**: board checks passed; builds next |
| M2b | Instrumented PGO, FFmpeg, both boards | Planned |
| M3 | GStreamer | Planned |
| M4 | BOLT on RPi5 (FFmpeg, one library first) | Planned |
| M5 | Packaged skill: runs and explains the workflow stages | Planned after M2a |

## 3. Completed This Week

### 3.1 M1 acceptance (FFmpeg on RPi4)

Every acceptance item of the workflow design (v0.3) passed in one run:

- **One command for all stages:** environment check, build, deploy, training collection, profile conversion, optimized build, paired measurement and report. A deliberate interruption after conversion resumed from the same command without redoing completed stages.
- **Build lock:**
  - the rebuilt baseline and the AutoFDO build differ only in the profile options;
  - all 108 frozen dependency packages were verified against the lock;
  - the baseline rebuild was byte-identical to the original.
- **Correctness:** decoder output matched the platform's own FFmpeg on three inputs before and after training, and before and after timing.
- **Profile consumption:** the compiler reported positive applied samples, with 1,959 records in `libavcodec` and 70 in `libavutil`. The profile identity and code-difference gates passed.
- **Library identity:** every timed process was checked to load the intended libraries, across 90 checked runs.
- **Measurement:**
  - paired AB/BA blocks with block bootstrap (20,000 resamples) and a 1% equivalence margin;
  - the number of blocks was pre-registered from a pilot, with 21 blocks for the primary input and 10 for the secondary;
  - every accepted run was clean, with no telemetry flags, no imbalance and no missing data;
  - the CPU frequency was the same for both builds (difference below 0.0003%).
- **Cleanup:** all deployed files were removed, and the board's settings and package count were restored and verified.

Workflow rules added and validated during M1:
- **Imbalance rule:** if the two builds differ by at least max(2, ⌈0.1·N⌉) telemetry-flagged runs, the verdict is capped at inconclusive.
- **Cooling margin:** the start temperature limit is 60 °C, with cooling down to 58 °C.
- **Telemetry handshake:** start and end markers around every timing window.
- **One transfer archive per round:** each round's results come back in a single archive, and a failed transfer counts as a technical failure with one retry per block.
- **Process-tree observation:** the whole decoder process tree is observed, not only the root process.
- **Separate cleanup privilege path:** cleanup runs on its own privilege path.

### 3.2 Multi-board workflow (M2a preparation)

- **Per-board profiles:** the RPi4 (armv7l) and the RPi5 (aarch64) each have their own profile: architecture, library paths, code-mode labels, tool deployment paths, telemetry sources and CPU pinning. Nothing board-specific is hard-coded any more.
- **New option `--stop-after <stage>`:** the run can stop at a review point (for example after the AutoFDO build audit) and resume later from there.
- **Regression:** replaying the archived M1 run reproduced the same scripts, build commands, paths and receipt fields (48 comparisons). The full test suite passes (186 tests).

### 3.3 RPi5 environment (M2a stage S0)

- **Board identity:** Raspberry Pi 5 (Cortex-A76, aarch64), image `tizen-unified-toolchain_20261118.083201`.
- **Tools:** `perf`, its libraries and hardware cycle sampling are verified.
- **Telemetry:** CPU frequency and temperature are readable. Voltage, undervoltage and firmware throttling sources are recorded as unknown.
- **Thermal headroom:** the board idles at 33–36 °C and is back to about 41 °C within 0.25 s after load, so the 60 °C start limit is easy to meet.
- **Display:** HDMI is connected and the display stack is running, matching the product setup.
- **Snapshot:** the board image's own package snapshot is no longer available. We use the same Base (`20261030.120529`) and Unified (`20261104.125239`) snapshots as M1; both provide aarch64 packages, including Clang 22.1.8. Compatibility with the board's libraries is checked after the first build.

### 3.4 Toolchain

- **`llvm-profgen`:** the IP-sample mode (9 patches on the Gerrit sandbox `sandbox/lhmax2025/afdo_profgen`) is the conversion tool for M1 and M2a. A 10th patch adds kernel profiles and is used by the kernel AutoFDO track.
- **Gerrit change 361624:** a build-verified fix was provided for the BOLT packaging in `llvm.spec`, for the change author and HQ reviewers.

## 4. Issues and Decisions

| Issue | Decision |
|---|---|
| The host is shared by several projects; builds need at least 16 GiB of free memory | The memory gate is not relaxed. Builds wait for it (re-check every 10 minutes, up to 3 hours). Our two tracks (workflow and kernel) serialize their builds with a shared lock. Other projects' builds are judged only by the resource gate |
| The host `sdb` transport can stall after a board reboot (the board itself is fine) | Standard recovery: disconnect and reconnect only our device first. A host `sdb` server restart is the last resort, only when no one else's `sdb` command is running, at most once per failure |
| Board IP addresses changed when boards were swapped | Every stage asserts board model and architecture before any action; device aliases are not trusted |

## 5. Plan for Next Week

1. **M2a:** freeze the aarch64 dependencies, build the baseline, check library compatibility on the RPi5, collect training samples (3 runs), convert, build the AutoFDO version and audit consumption. Then run the paired measurement on Tears of Steel (primary) and Sintel (secondary) under the M1 rules, and report.
2. **M2b preparation:** check the compiler-rt profile runtime packages for instrumented PGO on both boards.
3. **M5 preparation:** once M2a confirms the multi-board command-line interface is stable, start the skill that runs and explains the stages.

## 6. Risks

| Risk | Mitigation |
|---|---|
| Build windows on the shared host may delay M2a | Lock-based ordering between our tracks; long wait limits; builds take about 2 minutes each for FFmpeg |
| aarch64 consumption not yet proven | Applied-sample and code-difference gates as in M1 before any measurement |
| RPi5 telemetry gaps (no voltage or throttle source) | Recorded as unknown, never as "not throttled"; frequency is checked in every timing window |
