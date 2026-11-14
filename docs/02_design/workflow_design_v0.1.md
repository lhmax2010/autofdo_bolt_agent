Status: under multi-AI review

# AutoFDO / PGO / BOLT Workflow — Design v0.1 (draft for review)

| Item | Content |
|---|---|
| Version | v0.1, 2026-11-14 |
| Status | Draft for multi-AI review (one review round, then one confirmation round; PM consolidates and decides). |
| Owner | PM/design: Claude. Implementation and board execution: Codex. |
| Order | llvm-profgen first-batch delivery (limited scope) → **this workflow** → skill (SKILL.md + scripts) → Agent |
| Inputs | `docs/handover/01_pm_handover_report.md`, `docs/profgen/delivery/00_scope_decision.md`, design v1.8 §5.9 (performance method), `docs/profgen/eval/board_plan.md`, `tools/profgen/board/*`, `tools/profgen/eval_build.py`, `prepare_board_bundle.py`, `pull_verified_run.py` |

---

## 1. Purpose and scope

The workflow turns "a Tizen package + a board + a workload" into an optimized build and a measured result, using scripts that a person, a skill, or later an Agent can run stage by stage.

**In scope (v1):**

| Method | Boards | Packages | Notes |
|---|---|---|---|
| AutoFDO from IP sampling (`cycles`, no branch stack) | RPi4 (armv7l, Thumb-2/A32), RPi5 (aarch64) | FFmpeg, GStreamer | Uses the delivered llvm-profgen IP mode with the explicit conservative strategy |
| Instrumented PGO (`-fprofile-generate` / `-fprofile-use`) | RPi4, RPi5 | FFmpeg, GStreamer | Comparison point and fallback when AutoFDO gives no gain |
| BOLT (basic-sample mode, no LBR) | **RPi5 only** | FFmpeg first | BOLT does not support armv7l. Milestone M4 |

**Out of scope (v1):** kernel (separate track, §11), Chromium, LTO builds, iterative re-profiling of optimized builds, pseudo-probe, statistical validation of profgen defaults (deferred by the scope decision), submitting profiles to package repositories.

## 2. Principles

1. **Package-agnostic core, owner-provided package profiles.** The core never contains FFmpeg-, GStreamer- or kernel-specific logic. Everything package-specific (flag injection, target libraries, workloads, metrics, correctness checks, thresholds) lives in a package profile (§6) that the package owner will maintain. We write the first version of each.
2. **Training and measurement inputs are different.** Profiles are collected on training inputs and measured on test inputs, so the reported gain is not inflated by over-fitting.
3. **Every artifact is identified.** Builds, libraries, profiles and tools are recorded by SHA-256 and build-id. A stage refuses inputs whose identity does not match its receipt.
4. **Fail-stop with a reason.** Any failed gate stops the run with a machine-readable reason. No silent fallback (for example, `cycles` silently becoming `cpu-clock`).
5. **Resumable stages.** Each stage writes a receipt; a run can resume from the last completed stage. Nothing is overwritten silently.
6. **Reuse what is proven.** Board deployment, collection, pull-and-verify and build scripts from the profgen evaluation are the starting point.
7. **Honest reporting.** Results are "faster / slower / inconclusive" with a confidence interval. Every report states that profgen runs with the explicit conservative strategy, not validated defaults.
8. **Project rules stay in force.** STATUS.md 最高原则: all host files inside WORKDIR, no pip/npm/apt installs, `nice -n 19 ionice -c3` and resource gates for heavy host jobs; board writes only under `/opt/afdo_agent/` (never `/tmp`, which is noexec), no RPM installation on the board.

## 3. Variants

| Variant | Build | Purpose |
|---|---|---|
| `BASE` | Platform `%{optflags}` + `-fdebug-info-for-profiling -funique-internal-linkage-names` + `-Wl,--build-id=sha1` | Sampled build and performance baseline. Same flags as `AFDO` except the profile, so the A/B difference is the profile only |
| `AFDO` | `BASE` + `-fprofile-sample-use=<locked profile>` | AutoFDO-optimized build |
| `PGOGEN` | Platform flags + `-fprofile-generate` | Instrumented training build (not measured for performance) |
| `PGO` | Platform flags + `-fprofile-use=<profdata>` | Instrumented-PGO optimized build |
| `BOLT-IN` | Chosen input variant (`BASE` or `AFDO`) linked with `-Wl,--emit-relocs`, runtime ELF kept unstripped | Input to BOLT (RPi5) |
| `BOLT` | `llvm-bolt` output of `BOLT-IN` | BOLT-optimized binary |
| `PLAT` (optional) | Unmodified platform build | Shows the cost of the profiling flags themselves; off by default |

## 4. End-to-end flow

```
 S0 preflight ─► S1 build BASE ─► S2 deploy ─► S3 collect (train inputs, R runs)
                                                     │
                                                     ▼
 S7 report ◄─ S6 measure (test inputs, A/B) ◄─ S5 rebuild AFDO ◄─ S4 convert + gate + merge
     │
     └─► S8 restore & clean

 PGO path:  S1 PGOGEN ─► S2 ─► S3' train → profraw ─► S4' llvm-profdata merge ─► S5' PGO ─► S6
 BOLT path: S1 BOLT-IN ─► S2 ─► S3 collect ─► S4'' perfscript → BOLT pre-aggregated → perf2bolt → llvm-bolt ─► S2 ─► S6
```

One CLI subcommand per stage, plus `run` that chains them (§8).

## 5. Stages

### S0 Preflight

Host: GBS config inside WORKDIR is the verified one; release `llvm-profgen` (built from the recorded Gerrit sandbox commit, §14) and `llvm-profdata` SHA-256 match the delivery record (`docs/profgen/delivery/01_release.md`); disk space and `MemAvailable` above the configured minimums.

Board (per run, recorded in the receipt):
- Identity asserted from device-tree model, `uname -m` and kernel release; never from the SDB alias or IP.
- `/opt/afdo_agent` mounted exec and writable; required tools present with the expected SHA (perf, libLLVM).
- Hardware `cycles` really available: a short `perf record -e cycles` followed by `perf evlist -v` must show `type=0, config=0`. Otherwise stop.
- Root available; CPU governor set to `performance` for the run and restored in S8.
- Cooling check: idle temperature below `T_idle_max`; a 60-second four-core load stays below `T_load_max` (defaults 75 °C, per design v1.8 Q.5 #12). Record throttling state where the board can report it, otherwise `unknown`.

### S1 Build

- GBS build through the package profile's build hook, with `--define` selecting the variant. Flag injection follows the method already proven for FFmpeg: a local evaluation spec overlay that keeps `%{optflags}` and appends variant macros. The user's GBS configuration is never edited.
- Output: runtime RPMs + debuginfo RPMs, an artifact manifest (path, SHA-256, build-id, ISA) taken from the **packaged** files, not the BUILD directory. A target ELF without a build-id fails the stage.

### S2 Deploy

Unpack runtime RPMs on the host, push to `/opt/afdo_agent/variants/<run_id>/<variant>/`, verify SHA-256 on the board against the manifest. Libraries are selected with `LD_LIBRARY_PATH`; nothing goes to `/usr`. Debug files stay on the host.

### S3 Collect (AutoFDO and BOLT)

For each of `R` training runs (package profile, default 3):
- `perf record --buildid-mmap -e cycles -c <period>` (or `-F <freq>` if the profile says so) around the training workload.
- Export on the board: `perf script --show-mmap-events --show-lost-events -F pid,tid,event,period,ip,dsoff`, `perf buildid-list`, and the target process maps.
- Pull to the host and verify SHA-256 of every file; delete the board run directory only after a verified pull (`pull_verified_run.py` behaviour).
- Workload exit code and correctness output are checked; a failed workload invalidates the run.

### S4 Convert, gate, merge (AutoFDO)

For each training run and each target DSO:

```
llvm-profgen --ip-samples --binary=<runtime ELF> --debug-binary=<debug ELF> \
  --perfscript=<export> --perf-buildid-list=<list> --binary-match-regex=<board path regex> \
  --ip-event=cycles --ip-weight=period --ip-period-unit=<fixed per package> \
  --ip-aggregation=max --ip-skid=none --ip-zero-fill=none --ip-head-samples=none \
  --format=extbinary --output=<profile> --quality-report=<report.json> \
  [--ip-min-usable-ratio=… --ip-min-target-samples=… --ip-max-lost-ratio=…]   # from package profile
```

Gate on: exit code 0; `verdict.conversion == ok`; identity `verified` (unverified only if the package profile explicitly allows it); the package's threshold checks. `--ip-period-unit` is fixed per package so that runs merge in the same unit.

Merge all runs and all target DSOs of the package into one profile: `llvm-profdata merge --sample --extbinary`. The merged profile is **locked** (SHA-256 recorded) before S5.

### S5 Rebuild

`AFDO` = `BASE` flags + `-fprofile-sample-use=<locked profile>`. Profi stays at the clang default (on for non-LTO). Collect consumer diagnostics: the profile record/sample coverage warnings (`-mllvm -sample-profile-check-record-coverage=<N>` / `-sample-profile-check-sample-coverage=<N>`; Codex to confirm the exact options in clang 22.1.8) and save them with the run. Low coverage is reported, and fails the stage only if the package profile sets a minimum.

### S6 Measure

- Variants compared on the **test inputs**: `BASE` vs `AFDO` (and `PGO`, `BOLT` when built).
- Order: interleaved rounds (A B A B … or a fixed Latin-square order for more than two variants), warm-up rounds discarded.
- Rounds `N`: from the package profile, or from a pilot of ≥ 10 `BASE` rounds with design v1.8's formula `N = min(40, max(10, ceil(2·(1.96·1.2533·CV/0.005)²)))`. No extra rounds after `N`.
- Per-round gates: start temperature below `T_start`, governor/frequency as set, no new throttling. An invalid round is repeated once; if it fails again it is excluded and counted in the report.
- Correctness: the package's check (for example the decoded-output SHA-256 must equal the `BASE` reference) on every round. Any mismatch fails the run; a faster but wrong build is never reported as a gain.
- Statistic: median relative difference per variant against `BASE`, with a bootstrap 95% CI. Verdict with `ε` from the package profile (default 1%): **faster** if the CI lies entirely beyond −ε, **slower** if entirely beyond +ε, otherwise **inconclusive**.

### S7 Report

`report.json` (machine-readable, for the skill and Agent) and `report.md`:
environment and board identity; tool and artifact identities; per-run profgen quality summary; consumer diagnostics; the measurement table (median, CI, verdict, valid/invalid rounds); fixed limitations text, including "profgen explicit conservative strategy; defaults not statistically validated".

### S8 Restore and clean

Restore governor and any changed board state, remove the run directory on the board after verified pulls, keep the host run directory.

### PGO path

`PGOGEN` build → deploy → run the training workload with `LLVM_PROFILE_FILE=<board run dir>/%p-%m.profraw` → pull and verify → `llvm-profdata merge` → `PGO` build with `-fprofile-use` → S6. Instrumented PGO is already proven on small programs on both boards; FFmpeg/GStreamer is new.

### BOLT path (RPi5, milestone M4)

1. **Tools:** build `llvm-bolt` and `perf2bolt` on the host from `src/llvm` (`LLVM_ENABLE_PROJECTS=bolt`, `LLVM_TARGETS_TO_BUILD="X86;AArch64"`) inside WORKDIR. The Tizen LLVM package does not build BOLT.
2. **Input build:** `BOLT-IN` links with `-Wl,--emit-relocs` and keeps the runtime ELF unstripped. This needs a packaging change in the package profile (keep or re-attach the symbol table for the BOLT variant), verified by identity checks.
3. **Profile without host perf:** collect as S3, then a new converter `perfscript2bolt` turns the board export into BOLT's pre-aggregated format (`E cycles` plus `S <address> <count>` lines). It reuses the same identity and `dsoff → ELF address` rules as profgen and only counts samples from the target DSO's build-id. Then `perf2bolt --pa -ba -p <pre-aggregated> <ELF> -o <fdata>`.
4. **Optimize:** `llvm-bolt <ELF> -data=<fdata> -o <out>` with a conservative option set (function and block reordering; final set chosen during M4 trials), deploy, S6.
5. **Known risks:** basic-sample mode gives hotness without edges, so gains may be small; AArch64 non-relocation mode is not fully supported (hence `--emit-relocs`); shared-library rewriting on Tizen is untested.

## 6. Package profile (owner-provided)

Each package has a directory `workflow/packages/<name>/` that the owner can replace:

```
workflow/packages/ffmpeg/
  package.toml          # declarations below
  build/spec_overlay.*  # how variant flags are injected into the spec
  workloads/train.sh    # training workload (runs on the board)
  workloads/bench.sh    # measurement benchmark (runs on the board), prints the metric
  workloads/check.sh    # correctness check
  inputs.toml           # input files with SHA-256, split into train / test
```

`package.toml` (TOML, because Python's standard-library `tomllib` reads it without installing anything; JSON as fallback if the host Python is older than 3.11):

```toml
[package]
name = "ffmpeg"
spec_packages = ["ffmpeg"]            # GBS packages to build
owner = "TBD"

[targets]                             # DSOs to profile / optimize
armv7l  = ["usr/lib/libavcodec.so.62", "usr/lib/libavutil.so.60"]
aarch64 = ["usr/lib64/libavcodec.so.62", "usr/lib64/libavutil.so.60"]

[collect]
event = "cycles"
period = 1000003                      # or freq = 1000
runs = 3
period_unit = 1000003                 # fixed --ip-period-unit for merging

[gates]
min_usable_ratio = "0.5"              # passed to llvm-profgen; empty = not used
min_target_samples = 20000
max_lost_ratio = "0.01"
allow_unverified_identity = false
min_profile_coverage_percent = 0      # S5 consumer diagnostics; 0 = report only

[measure]
metric = "seconds"                    # printed by bench.sh
better = "lower"
warmup = 2
rounds = "auto"                       # or an integer
epsilon = 0.01
correctness = "workloads/check.sh"

[boards]
supported = ["rpi4", "rpi5"]
bolt = ["rpi5"]
```

The core passes a fixed environment to the scripts (variant library path, run directory, input paths) and reads only their exit codes and declared outputs.

## 7. Initial package profiles

| Package | Targets | Training workload | Measurement benchmark | Correctness |
|---|---|---|---|---|
| **FFmpeg** | libavcodec, libavutil | `gst-launch-1.0 filesrc ! qtdemux ! h264parse ! avdec_h264 max-threads=1 ! filesink` on the BBB clip | Same pipeline on the ToS clip, wall time | SHA-256 of decoded I420 output equals `BASE` |
| **GStreamer** | libgstreamer-1.0, libgstbase-1.0, libgstvideo-1.0, videoconvert/videoscale plugins | Decode + `videoconvert ! videoscale` to a different format and size (train clip) | Same pipeline on the test clip, wall time | SHA-256 of converted output equals `BASE` |
| **Kernel** | vmlinux (later) | — | — | Profile written for structure only; not run in v1 (§11) |

GStreamer covers several GBS packages (core and plugins-base). Its build hook builds all of them, and S4 merges one profile per GBS package. These are first proposals for the owners to refine.

## 8. Code layout and interface

Workflow code lives in the results repository:

```
workflow/
  afdo_wf/                 # Python 3, standard library only
    cli.py                 # subcommands below
    config.py  receipts.py  board.py (sdb)  gbs.py  profgen.py  bolt.py  stats.py  report.py
  board/                   # scripts pushed to /opt/afdo_agent/scripts (evolved from tools/profgen/board)
  packages/<name>/         # package profiles (§6)
  tests/                   # unit tests with synthetic inputs; no board needed
```

CLI (`python3 -m afdo_wf …`):

```
preflight --board rpi4|rpi5
build     --package P --variant BASE|AFDO|PGOGEN|PGO|BOLT-IN [--profile FILE]
deploy    --run RUN --variant V
collect   --run RUN [--mode afdo|pgo]
convert   --run RUN
rebuild   --run RUN --variant AFDO|PGO
bolt      --run RUN                      # M4
measure   --run RUN --variants BASE,AFDO[,PGO,BOLT]
report    --run RUN
run       --package P --board B --method afdo|pgo|bolt   # chains all stages, resumable
status    --run RUN
```

Run directory (host, inside WORKDIR, not committed): `runs/<run_id>/` containing `state.json`, one receipt per stage (command, start and end time, exit code, input and output SHA-256), artifacts, pulled board data and reports. Summaries of runs that matter are committed under `docs/workflow/runs/`.

Exit codes: 0 success, 2 gate failed (reason in the receipt), 3 identity mismatch, 4 board or environment problem, 1 other error. The skill and the Agent rely on these codes and on `report.json`.

## 9. Run state and resumability

`state.json` records the completed stages and their receipt SHA. `run` resumes after the last completed stage and re-verifies the identities of that stage's outputs before continuing. A stage never overwrites an existing output; re-running a stage needs `--redo <stage>`, which archives the old outputs.

## 10. Milestones

| Milestone | Content | Acceptance |
|---|---|---|
| **M1** | FFmpeg AutoFDO end-to-end on RPi4 (Thumb) | `run` completes all stages from one command; correctness passes; report with verdict and CI (any sign is acceptable); resume tested by interrupting after S3 |
| **M2** | FFmpeg on RPi5 (aarch64) + PGO path on both boards | Same as M1 for RPi5; `PGO` variant measured alongside `AFDO` |
| **M3** | GStreamer package profile | Multi-package build and per-package merge; report as M1 |
| **M4** | BOLT on RPi5 (FFmpeg) | Host BOLT build, `perfscript2bolt` converter with unit tests, BOLT variant correct and measured |
| **M5** | Skill | `SKILL.md` + scripts folder that runs the workflow (§12) |
| Kernel | Decision only | Choose method (§11) |

Each milestone ends with a Codex report and a STATUS update; PM reviews before the next milestone.

## 11. Kernel track (not in v1)

The delivered llvm-profgen does not produce kernel profiles (vmlinux and modules are batch 2, design §6.1), and the board kernel source (6.12.80) has no AutoFDO config option. Options to evaluate later: (a) implement profgen batch 2 for vmlinux; (b) a different method for the kernel. The kernel package profile is reserved so that the structure is ready.

## 12. Skill (M5, outline)

A folder containing `SKILL.md` and the workflow scripts. `SKILL.md` tells the AI: when to use the skill, the preconditions (preflight), the stage commands in order, how to read exit codes and `report.json`, which failures to stop on and report rather than work around, and the project rules (WORKDIR boundary, no installs, board directory). Its detailed design follows after M1, when the CLI is stable.

## 13. Open questions

1. Host Python version (needed for `tomllib`; otherwise JSON configs).
2. Exact clang 22.1.8 options for consumer coverage diagnostics (S5).
3. GStreamer: which GBS packages and plugin libraries are in scope for the first profile.
4. Whether `vcgencmd get_throttled` (or another throttling source) is available on both Tizen images.
5. Test clip for GStreamer and a second test clip for FFmpeg (different content from training).
6. Gerrit sandbox branch name for the LLVM patches, and who pushes to it (the project rule so far: Codex does not push Gerrit).
7. Language of the HQ branch documents (default: English).

## 14. Publication: HQ branch and Gerrit sandbox

Results are published to the HQ through a dedicated GitHub branch; LLVM source changes are published only through a Gerrit sandbox branch.

**LLVM (Gerrit sandbox).** The llvm-profgen patches (and later any BOLT-related LLVM change) are pushed to a Gerrit **sandbox** branch of the Tizen llvm project. The result repositories never contain an LLVM source tree. The README records, for every delivered state: the Gerrit project, the sandbox branch, the commit ID, the base commit (`f999bd40…` today) and the SHA-256 of the built `llvm-profgen`. Anyone reproducing the work fetches that commit and builds it with GBS.

**HQ branch (GitHub).** An orphan branch `hq` in this repository (no shared history with `main`, so it stays small and contains no raw evidence) holds a self-contained, curated copy for the HQ GitHub:

```
README.md                  # see below
docs/
  01_introduction.md       # background, goals, what was achieved, limitations
  02_design/               # llvm-profgen design (final version + short summary), workflow design
  03_reports/              # curated reports: profgen delivery and validation summary, workflow milestone reports
  04_demo.md               # demo walkthrough with expected output
workflow/                  # workflow code and package profiles (§6, §8)
demo/                      # host-only demo: small fixtures + script running llvm-profgen IP mode (no board needed),
                           # then a board demo using the workflow `run` command
```

**README contents (required):**
1. What the project is and what is delivered, with a status table per component (profgen, workflow milestones, BOLT, kernel).
2. Source locations: Gerrit project, sandbox branch, commit ID(s), base commit; this repository's `hq` commit.
3. Host setup: OS, GBS and its configuration, `sdb`, Python version, disk and memory needs; no package installation beyond the documented prerequisites.
4. Building llvm-profgen from the sandbox commit with GBS (normal, non-incremental), locating the tool in the RPMs, verifying its SHA-256.
5. Board setup for RPi4 and RPi5: image requirement (PMUv3 for RPi4), `/opt/afdo_agent` layout, perf deployment, hardware `cycles` check, cooling check.
6. Running: the host-only demo, then each workflow stage and `run`, with example commands and expected outputs.
7. Reading results: `report.json` and `report.md`, verdicts, quality-report fields, exit codes.
8. Adding or changing a package profile (for package owners).
9. Troubleshooting and known limitations (explicit conservative profgen strategy, defaults not statistically validated, BOLT RPi5 only, kernel not supported yet).

**Update rule.** `main` remains the full working history with all evidence. Codex refreshes `hq` at each delivery point (profgen release, each milestone) with one curated commit whose message names the source `main` commit and the Gerrit sandbox commit. Nothing is copied to `hq` without PM review.
