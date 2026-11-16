# AutoFDO / PGO / BOLT Workflow — Design v0.2

| Item | Content |
|---|---|
| Version | v0.2, 2026-11-16. Supersedes v0.1. |
| Status | For one confirmation review round; open points after that are decided by the user. |
| Inputs | v0.1; reviews `docs/workflow/reviews/v0.1_claude_code.md` (reviewer A) and `v0.1_Codex.md` (reviewer B); M1 build record `docs/workflow/m1/01_ffmpeg_target_build.md`; `docs/profgen/delivery/00_scope_decision.md`, `01_release.md` |
| Main changes | Experiment build lock and frozen dependency repository (§9); loaded-library verification for every measured process (§5 S6); independent correctness oracle (§8.2); paired-block statistics with balanced order and four verdicts (§8); per-second telemetry gates (§8.4); package profile schema v1 (§6); explicit comparison graph for PGO and BOLT (§3); receipt DAG and recovery (§13); BOLT packaging and converter contract (§10). Disposition of every review item: Appendix A. |
| Publication | Section 14 of v0.1 is removed. Publication follows the STATUS.md long-term rules (Gerrit sandbox for LLVM; English-only `hq` files checked by `tools/hq/check_hq.py`). |

---

## 1. Purpose and scope

The workflow turns "a Tizen package + a board + workloads" into an optimized build and a measured, correctness-checked comparison, using stage commands that a person, the skill (M5) or later the agent can run.

| Method | Boards | Packages | Milestone |
|---|---|---|---|
| AutoFDO from IP sampling (`cycles`, no branch stack) | RPi4 (armv7l Thumb-2/A32), RPi5 (aarch64) | FFmpeg, then GStreamer | M1 (FFmpeg, RPi4), M2a (FFmpeg, RPi5), M3 (GStreamer) |
| Instrumented PGO | RPi4, RPi5 | FFmpeg | M2b |
| BOLT (basic-sample mode) | RPi5 only | FFmpeg | M4 |

M2 is split: **M2a** (AutoFDO on RPi5) first, **M2b** (instrumented PGO on both boards) second, so the first RPi5 result has the fewest new variables. The published roadmap numbering (M1–M5) is unchanged.

**Out of scope (v1):** kernel (separate track, §15), Chromium, LTO, iterative re-profiling of optimized builds, pseudo-probe, statistical validation of profgen defaults (deferred by the scope decision), generic plug-in frameworks, cross-package parallel scheduling.

## 2. Principles

1. **Package-agnostic core, owner-provided package profiles** (§6). The core contains no FFmpeg-, GStreamer- or kernel-specific logic.
2. **One experiment, one build lock.** All variants of an experiment are built from the same source, spec, macros, toolchain and frozen dependency repository (§9). The A/B difference is *proven* to be the profile by gates, not assumed.
3. **Measure what was deployed.** Every measured process is checked against the declared must-load set (§5 S6).
4. **Correctness before speed, against an independent oracle** (§8.2).
5. **Pre-registered measurement.** Rounds, order, inputs, seed and verdict rules are locked before the first timed round; no rounds are added after seeing results (§8).
6. **Training, tuning and test inputs are separate** and checked for overlap by SHA and segment.
7. **Identity.** Sampled targets: runtime/debug build-id per the delivered IP contract. Tools, scripts and data: SHA-256 (the delivered llvm-profgen has no build-id; record `none`).
8. **Fail-stop with a reason; clean up on every exit path** (§13).
9. **Honest reporting.** Verdicts include `inconclusive`; every report states that profgen runs with the explicit conservative strategy (`max/none/none/none`), not validated defaults.
10. **Project rules stay in force** (STATUS.md 最高原则 and long-term rules): files only in WORKDIR, no installs, board writes only under `/opt/afdo_agent/`, no RPM installation on the board, host build resource profile (§9.4).

## 3. Variants and comparison graph

| Variant | Definition |
|---|---|
| `BASE` | Common flags = platform `%{optflags}` + `-fdebug-info-for-profiling -funique-internal-linkage-names` + `-Wl,--build-id=sha1`, built with the experiment lock |
| `AFDO` | `BASE` + `-fprofile-sample-use=<locked profile>` (+ coverage diagnostic options, §5 S5) |
| `PGOGEN` | `BASE` + `-fprofile-generate` (compile and link) |
| `PGO` | `BASE` + `-fprofile-use=<locked profdata>` |
| `BOLT-IN` | Parent variant (`BASE` or `AFDO`) built with `-Wl,--emit-relocs` and `--define '_rpm_strip_disable 1'` (keeps `.symtab` and `.rela.text`) |
| `BOLT` | `llvm-bolt` output of `BOLT-IN` |
| `BASE-r` | `BASE` rebuilt in the same frozen repository at the time `AFDO` is built (reproducibility check, §9.3) |
| `PLAT` | The board's own system package; used only as correctness oracle, never measured |

**Comparison graph.** Every candidate has exactly one registered control; reports carry both ELF SHA-256 values, not only names.

| Candidate | Control | Milestone | Meaning |
|---|---|---|---|
| `AFDO` | `BASE` (or `BASE-r`, §9.3) | M1, M2a, M3 | AutoFDO gain |
| `PGO` | `BASE` | M2b | Instrumented PGO gain |
| `BOLT` | `BOLT-IN` (same parent) | M4 | Pure BOLT gain |
| `BOLT` (parent `AFDO`) | `BASE` | M4, optional | Labelled "combined AFDO+BOLT gain", never "BOLT gain" |

A configuration that names any other control for these candidates is rejected.

## 4. End-to-end flow

```
S0 preflight ─► S1 build BASE (+ freeze repo) ─► S2 deploy ─► S3 collect (training inputs, R runs)
                                                                     │
S8 restore & clean ◄─ S7 report ◄─ S6 measure ◄─ S5 rebuild AFDO (+ BASE-r) ◄─ S4 convert, gate, merge

PGO path (§11):  S1 PGOGEN ─► S2 ─► S3' train → profraw ─► S4' merge ─► S5' PGO ─► S6
BOLT path (§10): S1 BOLT-IN ─► S2 ─► S3 ─► S4'' convert → perf2bolt → llvm-bolt ─► S2 ─► S6 (control BOLT-IN)
```

Board-state changes made in any stage are undone by session cleanup on every exit path (§13.3); S8 is also a re-entrant command.

## 5. Stages

### S0 Preflight

- **Host:** GBS version and configuration SHA; Python ≥ 3.11 (`tomllib`; host has 3.12.3); release `llvm-profgen` / `llvm-profdata` SHA-256 match the delivery record, plus SHA of the loader and libLLVM they run with; resource gates (§9.4).
- **Board identity:** device-tree model, `uname -m`, kernel release, and `TZ_BUILD_ID` from `/etc/tizen-build.conf`, asserted against the experiment record. A different image ends the experiment's measurement validity (new S0, new measurement).
- **Board tools:** `/opt/afdo_agent` exec and writable; perf SHA and `perf version`; libLLVM SHA.
- **Hardware cycles:** a short `perf record -e cycles`, then `perf evlist -v` parsed for event name, `type=0` and `config=0` together. Otherwise stop.
- **Telemetry capability manifest** per board (§8.4): which frequency, temperature and voltage-alarm sources exist. Missing throttle sources are recorded as `unknown`, never as "not throttled". RPi4 has no `vcgencmd` and no firmware `get_throttled` node; RPi5 capability is checked at its first S0.
- **Session state saved** for restoration: root state, each policy's governor.

### S1 Build

- Build through the package profile's build unit (§6): spec patch + macros (`profile_isa`, `with_autofdo`, …), `--define '_smp_mflags -j2'` only (never `V=1`; RPM passes `_smp_mflags` to `find-debuginfo.sh`).
- **First build of an experiment** resolves the dependency union of **all planned variants** from the pinned online snapshot, archives it and freezes it as a local repository (§9.2). All later builds of the experiment use only that repository. For M1, BASE and AFDO have the same BuildRequires, so BASE's downloaded set is the union; PGOGEN (M2b) and BOLT-IN (M4) add their extra packages when those experiments start.
- Output: runtime and debuginfo RPMs and an artifact manifest from the **packaged** files: path, SHA-256, build-id, ISA, SONAME, real file name (e.g. `libavcodec.so.62.11.100`).
- Gates: target ELFs have SHA-1 build-ids equal to their debug files; build lock written (§9.1).
- debugedit diagnostics (e.g. "DWARF version 5 unhandled", seen as non-fatal in every FFmpeg build so far) are recorded verbatim with counts; they do not by themselves fail the build or change compile flags.

### S2 Deploy

- Extract runtime RPMs on the host; push the package profile's `deploy_set` (all DSOs of the package that must come from the same build, e.g. all FFmpeg `lib*` because of their `avpriv_*` private interfaces) to `/opt/afdo_agent/variants/<experiment>/<variant>/`; verify SHA-256 on the board.
- Debug files stay on the host. Nothing is written to `/usr`.

### S3 Collect (AutoFDO and BOLT)

For each of `R` training runs (package profile):
- Run environment from the package profile, with `HOME`, `TMPDIR`, `XDG_*`, perf build-id dir, GStreamer registry and outputs all under the run directory.
- `perf record --buildid-mmap -e cycles -c <period>` around the training workload (`period` xor `freq`; M1 and M4 use fixed `-c`).
- During the run, save `/proc/<pid>/maps` of every workload process and verify the must-load set (as S6).
- Export on the board: `perf script --show-mmap-events --show-lost-events -F pid,tid,event,period,ip,dsoff`, `perf buildid-list`, `perf evlist -v`.
- Pull, write and persist the **verified-pull receipt first**, then delete exactly that run directory on the board and record the deletion result.
- Workload exit code, EOS and the training oracle (§8.2) must pass, otherwise the run is invalid.

### S4 Convert, gate, merge (AutoFDO)

Per run and per target DSO:

```
llvm-profgen --ip-samples --binary=<packaged runtime ELF> --debug-binary=<packaged debug ELF> \
  --perfscript=<export> --perf-buildid-list=<list> --binary-match-regex=<derived real board path> \
  --ip-event=cycles --ip-weight=period --ip-period-unit=<package fixed unit> \
  --ip-aggregation=max --ip-skid=none --ip-zero-fill=none --ip-head-samples=none \
  --format=extbinary --output=<profile> --quality-report=<report.json> \
  [--ip-min-usable-ratio=… --ip-min-target-samples=… --ip-max-lost-ratio=…]   # package policy
```

- The match regex is derived from the S1 manifest's real file path, not written by hand.
- Gates: exit 0; `verdict.conversion == ok`; `verdict.identity == verified`; package threshold checks. `--allow-missing-build-id` is added only when the package sets `allow_unverified_identity = true`; such runs are diagnostic only and cannot produce a published gain. Known identity conflicts always fail.
- **Merge order:** first across runs for the same `(build lock, ISA, DSO, event, weight, period unit, workload policy)`; multiple training inputs combine as raw count sums of equal, declared repetitions unless the profile declares weights.
- **Cross-DSO merge** into one package profile is allowed only after a collision check: function and context names present in more than one DSO profile are listed; any collision whose bodies differ stops the stage (PM decides: split consumption or restrict targets). Static functions carry unique-linkage suffixes, so collisions are expected to be rare; the check makes this verified rather than assumed.
- Report per target: target, usable and excluded sample counts by reason, and the share of samples in DWARF-covered C code vs assembly vs outside DWARF functions. This share is the upper bound on what AutoFDO can affect (FFmpeg has 54 hand-written `.S` files per build).
- The merged profile is locked (SHA-256) before S5.

### S5 Rebuild

- `AFDO`: same build unit and frozen repository; the locked profile staged at a fixed read-only path inside the build root (FFmpeg: `Source2000: autofdo.extbinary`), its SHA verified inside the chroot.
- Coverage diagnostics on the AFDO build only: `-mllvm -sample-profile-check-record-coverage=<N>` and `-mllvm -sample-profile-check-sample-coverage=<N>` (each with its own `-mllvm`; default 0 = off; per function, warns below N%). Package fields `record_coverage_warn_percent`, `sample_coverage_warn_percent` (M1: 100 = report every matched function), `fail_on_coverage_warning` (M1: false). Optionally `-mllvm -report-profile-staleness`.
- **Positive consumption evidence is required**: coverage warnings that name target functions (proving the profile matched), and target DSOs whose code differs from BASE. "No warnings" is never evidence of consumption.
- Profi stays at the driver default (the driver adds `-sample-profile-use-profi` whenever `-fprofile-sample-use` is given).
- `BASE-r` is built in the same step (§9.3).
- Build-lock gates (§9.1) between BASE (or BASE-r) and AFDO.

### S6 Measure

Measurement rules are in §8. Per timed process:
- Read `/proc/<pid>/maps` (all workload processes, including children) and verify **every** must-load DSO comes from the variant directory with the manifest SHA. Any must-load DSO from another variant or from `/usr` invalidates the run and stops the experiment (exit 3).
- GStreamer: per-variant `GST_PLUGIN_SYSTEM_PATH_1_0` (variant plug-in dir first, then system), per-variant `GST_REGISTRY_1_0`, generated in the variant's warm-up; timed rounds run with `GST_REGISTRY_UPDATE=no`; factory→plug-in file mapping checked after warm-up.

### S7 Report

`report.json` (machine-readable; the skill and agent rely on it) and `report.md`: experiment ID and build lock; board identity and telemetry manifest; tool and artifact identities; per-target quality summary and code-share bounds; consumption evidence; correctness oracle results; the pre-registered measurement plan; all raw rounds with telemetry flags; primary verdict and sensitivity analyses; limitations including the fixed sentence "profgen explicit conservative strategy; defaults not statistically validated".

### S8 Restore and clean

Re-entrant: restore saved governors and root state, stop only this experiment's processes, remove only verified-pulled run directories. Also run automatically by session cleanup (§13.3).

## 6. Package profile, schema v1

A thin schema, not a plug-in framework. Directory `workflow/packages/<name>/` (owner-maintained):

```
package.toml
build/profiling.patch          # spec patch (FFmpeg: the hq example patch)
workloads/*.sh                 # hooks: fixed argv, JSON result on a file descriptor/path
inputs.toml                    # input files: SHA-256, segment, role
```

Example (threshold and share values are illustrative; the owner sets them before S3):

```toml
schema_version = 1

[package]
name = "ffmpeg"
owner = "TBD"
source = { gerrit = "platform/upstream/ffmpeg", commit = "5fe76358596f66e955f005094e6f34ca525ab23d" }

[[build_units]]
id = "ffmpeg-armv7l-thumb"
spec = "packaging/ffmpeg.spec"
patch = "build/profiling.patch"
arch = "armv7l"
isa = "thumb"                         # thumb | a32 | a64
macros = { profile_isa = "thumb" }
consume_macro = { with_autofdo = "1" }
profile_staging = "packaging/autofdo.extbinary"

[[targets]]                           # profiled and optimized
id = "libavcodec"
build_unit = "ffmpeg-armv7l-thumb"
package_path = "usr/lib/libavcodec.so.62"   # real file and regex derived from the S1 manifest
thresholds = { min_usable_ratio = "0.5", min_target_samples = 20000, max_lost_ratio = "0.01" }

[runtime]
deploy_set = ["usr/lib/libav*.so*", "usr/lib/libsw*.so*"]   # must come from one build
must_load = ["libavcodec", "libavutil"]                     # checked in every timed process
env = { LC_ALL = "C" }
plugin_dirs = []                                            # GStreamer: variant plug-in dirs
cpu_affinity = 3
timeout_s = 600

[collect]
event = "cycles"
period = 1000003                      # xor freq
runs = 3
period_unit = 1000003
min_target_share = 0.2                # DWARF-covered share in targets; below it: report only, no AFDO

[collect.rpi5]
period = 1000003

[identity]
allow_unverified_identity = false

[consumption]
record_coverage_warn_percent = 100
sample_coverage_warn_percent = 100
fail_on_coverage_warning = false

[measure]
metric = "seconds"                    # M1: positive wall time only
better = "lower"
warmup = 2
blocks = "pilot"                      # or an integer; locked before S3 (SHA in receipt)
epsilon = 0.01
```

`inputs.toml` lists every input with SHA-256, segment (start, duration), role (`train`, `pilot`, `test`, `tuning`, `conformance`), and its oracle (§8.2). The core rejects: overlapping train/test (same SHA and overlapping segment), mixed ISA in one build unit, `period` and `freq` together, unknown keys or enum values, hooks returning non-JSON or non-finite values, `better = "higher"` until its transform is implemented.

**Hook protocol:** argv `<hook> <role> <variant-dir> <input> <result.json>`; `result.json` = `{status, eos, frames, bytes, digest, metric_value, metric_unit}`. Values are never parsed from free stdout.

## 7. Initial package profiles

| Package | Targets | Training | Measurement | Notes |
|---|---|---|---|---|
| **FFmpeg** (M1, M2) | libavcodec, libavutil | BBB 720p 60 s segment, `avdec_h264 max-threads=1`, I420, `sync=false` | ToS 60 s segment, same pipeline | ToS was used in the earlier profgen evaluation; it is disclosed as not a pristine holdout. A second test clip with a different encoding profile (Main or CAVLC, 1080p) is chosen and locked before M1's first consuming build. |
| **GStreamer** (M3) | Proposed: libgstreamer-1.0, libgstbase-1.0, libgstvideo-1.0, `gstreamer-1.0/libgstvideoconvertscale.so`; final set after the census | Raw-video pipeline (`filesrc` of I420 or `videotestsrc` fixed pattern) → `videoconvert ! videoscale` → fixed caps | Different raw input/size | M3 starts with a hotspot census on BASE (DSO sample shares). Build units are spec macros (`plugin=core/base`) or sub-packages of one spec, locked by the owner. If ORC is active, report its share and do not change ORC settings for the primary result. |
| **Kernel** | — | — | — | Separate track (§15). |

## 8. Measurement and statistics

### 8.1 Plan locked before the first timed round

Locked in the S6 receipt: candidate/control pairs, inputs and oracles, warm-up count, number of blocks `N`, the AB/BA order table and its seed, ε, and the analysis version.

- **Block** = one timed round of every compared variant on the same input.
- **Order:** two variants use a pre-generated balanced AB/BA sequence (counts differ by at most 1); more variants use a balanced rotation; the realised table is saved.
- **N:** from a pilot of ≥ 10 BASE rounds with the v0.1 formula `N = min(40, max(10, ceil(2·(1.96·1.2533·CV/0.005)²)))`. This is a budget, not a power guarantee. No blocks are added after the first timed block.

### 8.2 Correctness oracle

- **Oracle per input:** input SHA and segment, caps (format, width, height), thread count, expected frame count and output bytes, output SHA-256.
- **Independent reference:** the oracle digest is produced by decoding with `PLAT` (the board's system FFmpeg). H.264 decoding is bit-exact, so `BASE` must match `PLAT`; a mismatch stops the experiment before any measurement. If a package's output is not bit-exact, the owner declares a per-element tolerance before the first run.
- **Every variant** must match the oracle (digest, frame count, non-empty, EOS) on training and test inputs in untimed correctness runs before and after the timed blocks, using the same pipeline as the timed rounds except the sink.
- **Timed rounds** use a non-blocking sink (`fakesink sync=false`) with the same caps and check exit status and EOS; hashing never runs inside a timed round.
- **Conformance set (optional field, recommended before an external report):** 3–5 short clips with other encoding profiles, untimed.
- The report states the oracle's coverage: it proves equality on the declared workloads, not full decoder correctness.

### 8.3 Statistics and verdict

- For each complete block i: `r_i = ln(T_candidate,i / T_control,i)` (paired within the block).
- **Primary estimate:** `mean(r)`, reported as `exp(mean r) − 1`; 95% CI from a block bootstrap (20,000 resamples, fixed seed saved) of `mean(r)`. A t-interval and the ratio of medians are reported as secondary statistics.
- **Verdict** with ε (default 1%):
  - `faster`: CI upper bound < −ε
  - `slower`: CI lower bound > +ε
  - `equivalent`: CI entirely within (−ε, +ε)
  - `inconclusive`: otherwise
- More than one candidate: each against its own control; the report states that no multiple-comparison correction is applied, and one primary comparison is named in advance.
- **Raw data are never replaced.** A block with a pre-listed technical failure (no measurement obtained: crash, timeout, sdb drop) is retried once as a whole; the failed attempt is kept. Correctness failure fails the experiment.
- **Telemetry-flagged blocks** (§8.4) stay in the primary analysis and are flagged. A sensitivity analysis on clean complete blocks is reported alongside. If flagged or missing blocks exceed 20% of N, or their rate differs clearly between variants, the primary verdict is capped at `inconclusive` with the reason.
- Missing blocks: report descriptive statistics of what exists; verdict `inconclusive (incomplete)`.

### 8.4 Telemetry and environment

- The workload runs pinned (`taskset`, package `cpu_affinity`; RPi4 single-thread FFmpeg: CPU3). A 1-second sampler, pinned to another core, records `scaling_cur_freq`, `cpuinfo_cur_freq` (root), all thermal zones, the undervoltage alarm where present (RPi4 `rpi_volt` `in0_lcrit_alarm`), and a monotonic timestamp.
- **Gates per round:** start temperature ≤ `T_start` (default 60 °C, wait up to 10 min); maximum temperature in the round < `T_max` (default 80 °C); frequency equal to the fixed value in every sample; undervoltage alarm 0; no sampler gap > 2 s. A violation flags the block.
- `perf stat` cycles and task-clock per round; if the effective frequency (cycles/task-clock) of the two variants differs by more than 0.5% (median), the report marks "confounding risk".
- Fixed cool-down between rounds; the governor is set to `performance` for the experiment and restored on exit.
- Throttle state that cannot be read is reported as `unknown`; the report says "no anomaly observed in available telemetry", never "not throttled". The first formal measurement on each board measures the sampler's own overhead once.

## 9. Build lock and reproducibility

### 9.1 Build lock (`build-lock.json`, per variant)

Source commit and patch SHA; spec and macro values; GBS version and configuration SHA; the resolved buildconf; frozen repository ID; `rpm -qa --qf '%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH} %{SHA256HEADER}\n'` of the build root; the full extracted compile and link command lists (C, assembly, link); source path layout.

**Gates between candidate and control:**
1. Package lists identical line by line.
2. Compile and link commands identical after removing the declared candidate-only options (`-fprofile-sample-use=…`, coverage options; for PGO: `-fprofile-generate`/`-fprofile-use=…`; for BOLT-IN: `--emit-relocs`, strip-disable).
3. Source, patch, spec SHA and source path layout identical (path changes alter unique-linkage names).

A failed gate stops S5 (exit 2).

### 9.2 Frozen dependency repository

- The first build of an experiment resolves the dependency union of all planned variants (PGOGEN may need the compiler-rt profile runtime package) from the pinned snapshot, verified by reading `repomd.xml`/primary and checksums, not by directory HTTP 200.
- The downloaded RPMs are archived content-addressed under `temp/gbs-deps-archive/<experiment>/` with a SHA list, source snapshot IDs and resolution time, then turned into a local repository (`createrepo_c`, if present on the host; otherwise stop and report). Every build of the experiment uses only this `file://` repository.
- RPMs are not committed; their manifest is (`docs/workflow/runs/<experiment>/`).
- The archive is called "offline-reproducible" only after one rebuild from it in a new root has succeeded (§9.3).

### 9.3 Rebuild check (`BASE-r`)

When AFDO is built, BASE is rebuilt in the same frozen repository (`BASE-r`). If target SHA-256 and build-ids equal BASE's, the build is reproducible and BASE is the control. If they differ, `BASE-r` becomes the control (same environment as AFDO) and the report records why. M1 performs this once as the offline-rebuild validation.

### 9.4 Snapshot loss and host resources

- If the archive is incomplete and the snapshot is gone, the experiment stops. Moving to a new snapshot creates a **new experiment ID** and rebuilds every control and candidate; new candidates are never paired with old controls.
- Host build profile (verified in M1): serial builds, `_smp_mflags -j2`, `--threads 1`, `systemd-run --user --scope -p MemoryMax=6G -p MemoryHigh=5G -p CPUQuota=200%`, `nice -n 19 ionice -c3`; start gate MemAvailable ≥ 16 GiB, 1-min load < 0.6 × nproc, disk ≥ 50 GiB; stop only this build's unit if MemAvailable < 6 GiB twice or disk < 20 GiB; never touch other processes.

## 10. BOLT on RPi5 (M4)

1. **Tools:** host `llvm-bolt` and `perf2bolt` built from `src/llvm` (`LLVM_ENABLE_PROJECTS=bolt`, `LLVM_TARGETS_TO_BUILD="X86;AArch64"`) inside WORKDIR, identified by SHA.
2. **BOLT-IN packaging:** `-Wl,--emit-relocs` and `--define '_rpm_strip_disable 1'`. Gates: the deployed file has `.symtab` and `.rela.text` (`readelf -S`); one final ELF carries code, symbols and relocations (no re-attached metadata from another file); `llvm-bolt` log has no non-relocation-mode warning (AArch64 is fully supported only in relocation mode).
3. **Converter `perfscript2bolt` (fixed period only):** checks event and period per record; filters by the target build-id with the same mapping, lifetime and PT_LOAD rules as profgen (`VA = p_vaddr + dsoff − p_offset`); each valid sample counts 1; aggregates by VA; writes `E cycles` and `S <hex VA> <count>`; records dropped/unknown/LOST counts and a count-conservation check. `perf2bolt --pa` does not validate build-ids, so filtering is the converter's job. These counts are sampled hotness, not execution counts.
4. `perf2bolt --pa -ba -p <aggregated> <BOLT-IN ELF> -o <fdata>` (`-ba` is required for `S` records); the aggregated file and fdata are bound to the BOLT-IN SHA.
5. **Option selection:** on `tuning` inputs only, then locked; the test set is measured once with the locked options. M4 starts with one AArch64 DSO and a basic, correctness-checked rewrite before enabling reordering.
6. **Identity after BOLT:** `llvm-bolt` changes the build-id (BuildIDRewriter flips the last bit by default); variants are identified by SHA-256; debug association is re-recorded, never inherited.
7. **Control:** `BOLT-IN` (§3). A correct `inconclusive` result is a valid M4 outcome.

Converter unit tests: samples from other DSOs filtered; multiple PT_LOAD; `p_memsz > p_filesz`; PIE/DSO load bias; remapping of the same path with a new build-id; period change; count overflow; build-id mismatch rejected.

## 11. Instrumented PGO (M2b)

- `PGOGEN` = BASE + `-fprofile-generate` in CFLAGS **and** link flags (FFmpeg `--extra-ldflags`); gate: target DSOs contain the profile runtime (e.g. `__llvm_profile_runtime`).
- Training with `LLVM_PROFILE_FILE=<run dir>/%m-%p.profraw`; set-up and plug-in-scanner profraw are kept separate from training output; only profraw from this generation's identified binaries and completed processes is merged (no directory globbing of history).
- `llvm-profdata merge` → locked profdata → `PGO` = BASE + `-fprofile-use`; control `BASE`.
- Small-program PGO results on the boards do not count as package-level acceptance.

## 12. Code layout and interface (M1 minimum)

```
workflow/
  afdo_wf/        # Python ≥ 3.11, standard library only (tomllib)
  board/          # board scripts pushed to /opt/afdo_agent/scripts
  packages/<name>/
  tests/          # synthetic tests, no board needed
```

**Reuse boundary:** the identity checks, verified-pull logic and command semantics of `tools/profgen/board/*`, `prepare_board_bundle.py` and `pull_verified_run.py` are reused; their fixed paths, resource settings (e.g. `nproc/2`) and FFmpeg/spike special cases are not. Paths, resources and package choices come from the package profile and the host profile (§9.4).

**M1 commands** (`python3 -m afdo_wf …`): `preflight`, `build`, `deploy`, `collect`, `convert`, `rebuild`, `measure`, `report`, `restore`, `run` (chains all, resumable). Exit codes: 0 success; non-zero with a reason code in the receipt (`gate`, `identity`, `environment`, `correctness`, `error`). `status`, `--redo` archiving details and finer exit codes are finalised in M5 when the CLI is stable.

## 13. Receipts, recovery and cleanup

1. **Receipt DAG.** Each stage receipt records the SHA of every direct input: scripts, package profile, build lock, inputs, board session, upstream receipts. Resume re-verifies the chain; changed content under an unchanged file name invalidates the dependent stages.
2. **Redo** invalidates all descendants; an invalidated stage cannot be reused as completed.
3. **Session cleanup.** Board state changes (root, governor, background samplers) are registered when made and undone in a `finally` path on success, failure, SIGTERM or error. If the board is unreachable, the receipt records `cleanup_pending`; the next session re-verifies board identity before restoring anything. Only this experiment's processes are stopped; only verified-pulled directories are deleted.

Acceptance tests: failure in S3/S6, SIGTERM, sdb drop, receipt write failure, crash before/after remote deletion, redo of S3 invalidating S5, changed package.toml, changed file content with the same name, a different board behind the same sdb alias.

## 14. Milestones

| Milestone | Content | Acceptance |
|---|---|---|
| **M1** | FFmpeg AutoFDO on RPi4 (Thumb), one primary test input | `run` completes from one command with resume tested after S3; build-lock gates pass; `BASE-r` offline rebuild check done; BASE matches PLAT oracle; every timed process passes must-load checks; positive consumption evidence; pre-registered measurement with verdict and CI (any verdict is acceptable); cleanup verified after an injected failure |
| **M2a** | FFmpeg AutoFDO on RPi5 (aarch64) | As M1; RPi5 telemetry manifest established |
| **M2b** | Instrumented PGO, FFmpeg, both boards | PGOGEN runtime gate; profraw generation tracking; `PGO` vs `BASE` measured with M1 rules |
| **M3** | GStreamer | Hotspot census; build units and must-load/plug-in checks; per-DSO merge with collision check; report as M1 |
| **M4** | BOLT on RPi5 (FFmpeg, one DSO first) | Converter with unit tests; packaging gates; tuning/test separation; `BOLT` vs `BOLT-IN` measured |
| **M5** | Skill (`SKILL.md` + scripts) | Runs and explains the stages through the same commands without duplicating their logic; written after M2a, when the CLI is stable |
| Agent | After M5 | Uses the skill; records its choices; surfaces failures rather than weakening checks |

**M1 implementation order:** build lock and frozen repository → BASE/AFDO with consumption evidence → must-load and oracle checks → locked measurement plan and statistics → receipts, recovery and cleanup.

The manual M1 pilot (`docs/workflow/m1/02_manual_pilot_rpi4_thumb.md`) is run with these rules and provides the first measured result and the pilot CV for N.

## 15. Kernel track

Separate track; the delivered llvm-profgen does not produce kernel profiles and the board kernel has no AutoFDO option. Method and package fields are designed when the method is chosen.

## 16. Open questions

1. Second FFmpeg test clip (encoding profile, licence, SHA) — owner or PM choice before M1's first consuming build.
2. Conformance clips for §8.2 (optional in M1).
3. RPi5 telemetry sources (answered at M2a S0).
4. GStreamer build units and final targets (M3 census).
5. Package of the compiler-rt profile runtime in the Tizen repositories (M2b).
6. Whether `createrepo_c` is available on the host (M1 S1; otherwise PM decides).

---

## Appendix A. Review disposition

Reviewer A = `v0.1_claude_code.md`; reviewer B = `v0.1_Codex.md`. Status: **Accepted**, **Partly accepted**, **Deferred**.

| Item | Summary | Status | Where in v0.2 |
|---|---|---|---|
| A-S1, B-I1 | BASE/AFDO are separate builds without a lock; snapshot drift | Accepted | §9.1–9.4, §5 S1/S5 |
| A-S2, B-I3 | Measured process may load other libraries/plug-ins; shared GStreamer registry; FFmpeg private ABI | Accepted | §5 S2/S3/S6, §6 `[runtime]` |
| B-S1, A-I3 | Statistic, order and invalid-round rules not a coherent contract | Accepted with merge: paired log ratios (A) + balanced seeded order, block bootstrap, no replacement of raw data (B); four verdicts incl. `equivalent` only when the CI lies within ±ε | §8.1, §8.3 |
| A-I1, B-I4 | Oracle not independent; empty/short output could match; hashing inside timed rounds | Accepted: PLAT oracle + full oracle fields; correctness separated from timing | §8.2 |
| A-I2, B-I5 | Throttling unobservable on RPi4; only start temperature checked | Accepted | §5 S0, §8.4 |
| A-I4, B-I6 | Package profile lacks ISA, real paths, deploy set, runtime env, hook protocol, input roles | Accepted (thin schema v1) | §6 |
| A-I5, B-I9 | BOLT stripping, converter contract, build-id handling, control | Accepted | §3, §10 |
| A-I6 | Snapshot deletion; archive never rebuilt offline | Accepted | §9.2–9.4 |
| B-I2, A-G5 | PGO/BOLT controls wrong | Accepted (comparison graph) | §3, §11 |
| B-I7 | Merged profile across DSOs without collision check | Accepted | §5 S4 |
| B-I8, A-G1 | Coverage options semantics; no positive consumption evidence; Profi wording | Accepted | §5 S5 |
| B-I10 | Cleanup only at S8; redo does not invalidate descendants; delete-before-receipt | Accepted | §13, §5 S3 |
| B-G1 | Tools without build-id | Accepted | §2.7, §5 S0 |
| B-G2 | `allow_unverified_identity` flag not wired | Accepted (diagnostic only) | §5 S4 |
| B-G3 | Historical scripts carry fixed paths and resources | Accepted | §12, §9.4 |
| A-G2 | cycles check by name+type+config; perf version | Accepted | §5 S0 |
| A-G3 | Assembly hotspots bound the gain | Accepted | §5 S4, §7 |
| A-G4 | GStreamer target choice by census; raw-video input; ORC | Accepted | §7 |
| A-G6 | Simplifications | Partly accepted: JSON fallback removed; PLAT only as oracle; minimal CLI; kernel placeholder removed; skill after M2a. PGO stays in M2 as M2b (not moved to M3) to keep the published roadmap numbering | §1, §6, §12, §14, §15 |
| A §13, B §5 | Open-question answers (Python 3.12.3; coverage options; no `vcgencmd` on RPi4; Gerrit done; English) | Accepted | §5, §16 |
| B §5.5 | ToS not a pristine holdout | Accepted (disclosed) | §7 |
| A (unverified) | v1.8 §5.9 clause numbers, aarch64 packaging, ORC, compiler-rt package | Deferred to the milestone where each is needed | §16 |
