---
name: afdo-workflow
description: Use afdo_wf for Tizen package AutoFDO and PGO experiment work, including FFmpeg on RPi4 armv7l and RPi5 aarch64. Plan or run the build, sample, convert, rebuild, paired measurement, and report stages. Inspect receipts, resume a run, or interpret results.
---

# Tizen package profiling workflow

## Setup and authorization

Start from a fresh clone of the `release` branch. Use a new directory for this workflow.
If the workspace entry in `.clinerules/workflows/afdo-workflow.md` does not
register automatically, open this file directly and follow it.

```bash
git clone --single-branch --no-tags --branch release "$REPOSITORY" afdo-workflow
cd afdo-workflow
```

Set `REPOSITORY` to the remote supplied by the maintainer. `WORKDIR` is the clone root, or the primary worktree of that clone if you use a linked worktree. Run the rest of the commands from the checkout root.

```bash
WORKDIR=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
export WORKDIR
export PYTHONPATH="$PWD/workflow"
export PYTHONDONTWRITEBYTECODE=1
PY=${PY:-python3}
has_required_python() {
  command -v "$1" >/dev/null 2>&1 &&
    "$1" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'
}
if ! has_required_python "$PY"; then
  PY=
  for candidate in python3.11 python3.12; do
    if has_required_python "$candidate"; then
      PY=$candidate
      break
    fi
  done
  if [ -z "$PY" ]; then
    printf '%s\n' 'environment [4] Python 3.11 or newer is required.' >&2
    exit 4
  fi
fi
export PY
```

- For inspection and drafting, use Git and Python 3.11 or later. If setup reports exit 4, report the interpreter prerequisite and stop. Use an existing interpreter.
- For a live run, have SDB, GBS and the Tizen build environment, the target board and image, the matching board perf tool and libraries, and the package source, build configuration and dependency inputs. Get the project-patched `llvm-profgen` and matching `llvm-profdata` from the maintainer or build them using the [repository build instructions](../../workflow/README.md#build-the-host-profile-tools).
- You can run `doctor`, `status`, `explain`, `run --dry-run`, and `init` for a new draft, and read existing reports without further approval.
- Get explicit user approval before any SDB operation that contacts the board, including a read-only identity probe or reconnect. Also get approval for a board-contacting run or resume, `--redo`, and any board state change. Confirm the target and the operation in that approval.
- Keep sealed configurations, receipts, and run directories read-only. Use a separate mutable run for new work. Keep workflow-owned board writes under `/opt/afdo_agent/` and preserve the cleanup journal. Do not install RPMs on the board. Delete run directories only after verified-pull through the workflow. Stop only processes owned by this experiment.
- Launch only modes supported by the current CLI and package configuration. The archived FFmpeg examples below use AutoFDO.

## Verified run environments

The table lists the combinations verified for the recorded runs. Prefer these
combinations for live runs. You may use other versions and must record any
deviation in the experiment record as unverified. `doctor` checks availability
and minimum requirements and reports detected versions. Compare those
versions with the table yourself.

| Component | M1 RPi4 Thumb | M2a RPi5 AArch64 |
| --- | --- | --- |
| Python and GBS | Python 3.12.3, GBS 2.1.1 | Python 3.12.3, GBS 2.1.1 |
| SDB client | Version not captured for this run | 4.2.25 |
| Clang and host LLVM profile tools | 22.1.8 | 22.1.8 |
| Board perf | 6.12.80, armv7l | 6.12.80, aarch64 |
| Board image build ID | `tizen-unified-toolchain_20261104.160709` | `tizen-unified-toolchain_20261118.083201` |

The verified LLVM source is Gerrit project `platform/upstream/llvm`, sandbox branch
`sandbox/lhmax2025/afdo_profgen`, commit `c8942ae1b53099a78a97dca2b64427af6e58432b`.
Use [workflow/README.md](../../workflow/README.md#build-the-host-profile-tools) for the build
instructions. The recorded binaries have these SHA-256 values:

| Tool | SHA-256 |
| --- | --- |
| `llvm-profgen` | `67ad21faba787d276a80673c1f324f7c0591d28d76bd37a8bd57de0d86426be6` |
| `llvm-profdata` | `1700cc8924ba608c773a73b7550025189e5e2af3a994ef58ddc6009933d0977e` |

## Stage map

| Stage | Purpose | Board contact |
| --- | --- | --- |
| `preflight` | Check host readiness, device identity, tools, inputs, and sampling capability. | Yes |
| `build` | Freeze dependencies and build the baseline package. | No |
| `deploy` | Deploy the baseline and establish correctness against the platform oracle. | Yes |
| `collect` | Capture baseline training samples and verify their identity. | Yes |
| `convert` | Convert samples, check quality, and merge a locked profile. | No |
| `rebuild` | Rebuild and audit the control and profile-consuming candidate. | Only when the job includes an AFDO audit, to deploy and perform untimed correctness checks. |
| `measure` | Run the preregistered paired comparison and check correctness and telemetry. | Yes |
| `report` | Write the report after receipt and cleanup checks. | No |
| `restore` | Restore the original root and governor state, stop experiment-owned processes, and clean up verified-pull artifacts under the cleanup journal. | Yes, as session cleanup or pending recovery. |

Use `"$PY" -m afdo_wf explain STAGE` for stage inputs, gates, board operations, outputs, and receipt fields. The enclosing live run can contact the board for session setup and cleanup even when it reuses stage receipts. Report any `cleanup_pending` and recheck board identity before resuming cleanup in a later authorized session.

## Host build coordination

The CLI uses `$WORKDIR/temp/host-gbs.lock` with `flock`. Each GBS invocation, including dependency resolution, takes an exclusive lock. The PGO measurement stage takes a shared lock across pilots, formal rounds, and mechanism counts. Other shared board timing sessions can proceed on their own authorized boards while exclusive host work waits. The combined wait for the lock and other builders is limited to eight hours.

Before launching GBS the CLI also rechecks the startup resource gates: `MemAvailable >= 16 GiB`, one-minute load average `< 12`, and at least `50 GiB` free on the `WORKDIR` filesystem. It rechecks unmet conditions every ten minutes and reports a gate failure after at most three hours of resource waiting.

Inspect `gbs_waits` in a build receipt or `status`. PGO measurement records its shared holder and resource checks in `measurement-lock.json` and checks I/O PSI full avg60 <20% before timing. Locks are released when their operation finishes, fails, or is cancelled. Report the wait records on exit 8.

## Board identity and SDB

Get user approval before contacting the board, including for the identity probe below. An IP address or alias can refer to a replacement board. Before a live run, resume, or board state change, check the model, architecture and image build ID against the job's `identity`. Check the kernel too when the job pins it. Use the approved endpoint for the identity probe and stop on any mismatch.

If the authorized target disconnects, limit recovery to that endpoint. `SERIAL` is the approved SDB endpoint, including the port when required.

```bash
sdb disconnect "$SERIAL"
sdb connect "$SERIAL"
sdb -s "$SERIAL" shell 'tr -d "\000" < /proc/device-tree/model; printf "\n"; uname -m; uname -r; sed -n "s/^TZ_BUILD_ID=//p" /etc/tizen-build.conf'
```

Reassert identity after reconnecting. If reconnect or identity verification fails, stop and report it. Never run `sdb kill-server` or restart the shared SDB service. Leave other devices and connections alone.

## Where the inputs live

Use these configuration files from the checkout.

| Input | RPi4 FFmpeg | RPi5 FFmpeg |
| --- | --- | --- |
| Package TOML | `workflow/packages/ffmpeg/package.toml` | `workflow/packages/ffmpeg/package-rpi5.toml` |
| Input manifest (`--inputs`) | `workflow/packages/ffmpeg/inputs.toml` | Same |
| Board profile (`--platform`) | `rpi4-armv7l` in `workflow/platforms/rpi4-armv7l.toml` | `rpi5-aarch64` in `workflow/platforms/rpi5-aarch64.toml` |

Obtain the exact clips from the separate media checkout. Each is an H.264 segment prepared from a Blender Foundation open movie under CC BY 3.0. The input manifest supplies these expected SHA-256 values. `init` checks every file.

| Role | Clip and source | SHA-256 |
| --- | --- | --- |
| Training | `bbb_720p_h264_60s.mp4`, Big Buck Bunny, Sunflower edition | `b5e116b9d01cec8e7f697041c53575d36bd96a5928e40faa69e731f9ae2d00a4` |
| Primary test | `tos_720p_h264_60s.mp4`, Tears of Steel, Mango Open Movie Project | `280fbd41f8772491ebe784aa19a3caed3bb1e8b2e64daef1d2a5a284d1f38ad1` |
| Secondary test | `sintel_1080p_h264_60s.mp4`, Sintel, Durian Open Movie Project; scaled to 1920x1080 | `b1c762e322350cecb04a38509050d320892ff8cbc8b2a7113418d5ecba4ad843` |

Use a new sibling directory to fetch the media, or choose a fresh directory under
`$WORKDIR/temp` and set `MEDIA_DIR` to it. The media checkout contains `ATTRIBUTION.md` with the original sources, credits, license and clip edits.

```bash
REPOSITORY=$(git remote get-url origin)
MEDIA_DIR="$(dirname "$WORKDIR")/ffmpeg-media"
git clone --single-branch --no-tags -b media "$REPOSITORY" "$MEDIA_DIR"
```

The maintainer can also provide a verified frozen dependency archive and its build configuration for jobs that use one. A new RPi5 preparation job resolves and freezes its dependencies as part of its build stage.

## Create, inspect, resume, and redo

Run local diagnostics before drafting:

```bash
"$PY" -m afdo_wf doctor
```

`doctor` prints `ok`, `missing`, `mismatch` and `unknown` lists. Exit 0 means
the scan completed. Even if every result is `ok`, a scan without a job only
covers host checks. Missing live tools or unmet build gates still permit
drafting. Job readiness requires the job-specific check below.

Keep the three files together in `MEDIA_DIR`, or supply a separate `--media ID=FILE` for each input. This RPi5 example uses a new draft path and an unused run directory. For RPi4, use `--platform rpi4-armv7l` and `workflow/packages/ffmpeg/package.toml`.

```bash
JOB="$WORKDIR/jobs/ffmpeg-rpi5.json"
RUN_DIR="$WORKDIR/runs/ffmpeg-rpi5"
"$PY" -m afdo_wf init --workdir "$WORKDIR" --platform rpi5-aarch64 \
  --package workflow/packages/ffmpeg/package-rpi5.toml \
  --inputs workflow/packages/ffmpeg/inputs.toml --media-dir "$MEDIA_DIR" \
  --job "$JOB" --output "$RUN_DIR"
```

If a file is absent, `init` exits 2 with `required local file missing` and the path. If the SHA differs, it exits 3 with `media SHA does not match manifest` and the input ID. In either case it leaves the draft and run paths unused. Ask for the exact file and retry init once it is available. After a successful init, preview the draft.

```bash
"$PY" -m afdo_wf run --job "$JOB" --dry-run
"$PY" -m afdo_wf explain preflight
```

The [RPi5 draft and preview](../../examples/ffmpeg-rpi5-draft/README.md) illustrate the
output shapes with placeholder paths. Create your own draft with `init`.

### Fill in the draft

| Key in `missing_for_run` | Format and source |
| --- | --- |
| `serial` | Approved SDB selector string, with port when needed. Confirm the selected device. |
| `identity` | Object with `model`, `arch`, `kernel` and `build_id` strings from the identity probe above. The hint beside `identity` in the list describes these fields. |
| `tools` | Object keyed by `profgen`, `profdata`, `loader` and `libLLVM` with `{path, sha256}` entries. Use absolute local paths and lowercase SHA-256 from the prepared profile toolchain. |
| `board_tools` | Array of `{source, target, sha256}` entries. Use absolute local copies of the correct perf and dependencies, their hashes, and platform target paths under `/opt/afdo_agent/`. |
| `source`, `patch` | Absolute source checkout directory and patch file. Follow the package TOML revision and patch and prepare the spec in the checkout. |
| `config` | Absolute path to the GBS configuration with pinned Tizen repositories. Obtain the architecture-specific configuration from the build environment. |
| `build_environment` | Object of environment variable names to strings for the isolated build environment. Use the host build setup and directories for this job. |
| `rpm_packages` | Array of exact runtime and debuginfo RPM names for the package and library targets. Check the package's spec. |
| `profgen`, `profdata` | Non-empty argv arrays of strings from the locked toolchain. Include the loader and its library path when required, then the relevant tool path. |
| `order_seed`, `bootstrap_seed` | Integers selected and preregistered by the experimenter before measurements. |
| `rpmspec` (RPi5) | Non-empty argv array of strings invoking the configured `rpmspec`, with its loader and macro environment as needed. Use the Tizen build environment. |
| `snapshots`, `snapshot_evidence` (RPi5) | Object mapping repository names to fixed snapshot IDs, and absolute path to the saved metadata and snapshot evidence. Obtain both from the selected build repositories. |
| `repo`, `repo_id`, `buildconf` (RPi4) | Absolute path to the frozen repository, its recorded identifier string, and absolute path to the resolved build configuration. Obtain them from the verified freeze manifest. |
| `frozen_packages` (RPi4) | Array of sorted `NAME-VERSION-RELEASE.ARCH SHA256HEADER` rows from the frozen installed package receipt. |

### Record and verify tool locks

In the prepared toolchain, locate the actual loader, libLLVM shared library,
`llvm-profgen` and `llvm-profdata` used by the job. For each file, set
`TOOL_FILE` to its local path:

```bash
realpath -- "$TOOL_FILE"
sha256sum -- "$TOOL_FILE"
```

Record the resolved absolute path as `path` and the first field from
`sha256sum` as `sha256` in `tools`. Hash the local board tools the same way
and record their local paths as `source` and approved board paths as `target`.
See the recorded [M1 armv7l locks](../../examples/m1-rpi4-thumb/tool-locks.json)
and [M2a AArch64 locks](../../examples/m2a-rpi5-aarch64/tool-locks.json).
They list file names, hashes and the board installation targets. Use your
own local paths when filling the draft.

Review the identity and authorization, exact media, source and build inputs,
dependency freeze evidence, seeds and fresh output paths. Before setting
`draft=false`, run and pass the job-specific check:

```bash
"$PY" -m afdo_wf doctor --job "$JOB"
```

Confirm the required host checks and every declared host and board tool lock
appear under `ok`. Resolve any missing, mismatched or unknown required check
first. Preview the completed job with dry-run and review the board operations
with the user before running it.

For an interrupted run, inspect the same job on the host that has the original run directory and artifacts. A report copy alone cannot provide receipt status or resume a run. Set `JOB` to that job file and `STAGE` to the stage you want to inspect.

```bash
"$PY" -m afdo_wf status --job "$JOB"
"$PY" -m afdo_wf explain "$STAGE"
"$PY" -m afdo_wf run --job "$JOB" --dry-run
```

Use `stage_order`, receipt paths, `input_sha`, `upstream_sha`, and failure reasons. Report any `cleanup_pending`, and verify the target's identity before any restoration in the next approved session. Follow exit 7 below if recovery is required. After approval and with matching inputs and cleared blockers, resume using the same job and `run`. The runner revalidates receipts before reuse.

For an explicitly approved redo on a mutable job, record why the stage must run again.

```bash
"$PY" -m afdo_wf --redo "$STAGE" --reason "$REASON" --job "$JOB"
"$PY" -m afdo_wf status --job "$JOB"
"$PY" -m afdo_wf run --job "$JOB" --dry-run
```

Record the redo receipt path and affected stages. Redo archives receipts and invalidates the selected stage and its dependents. A subsequent authorized `run` executes the plan.

## Instrumented PGO

Use the same setup and approval steps. Add `--method pgo` to the FFmpeg
`init` command. Preview the draft with `run --dry-run` and inspect a stage
with `"$PY" -m afdo_wf explain collect --method pgo`. Use `status --job` for
the comparison names and any recorded PGO evidence. Host-only validation
does not establish package build or board acceptance.

- Prepare the source with `workflow/packages/ffmpeg/build/profiling-pgo.patch`.
  Enter the verified snapshot configuration and metadata for the dependency
  union. It includes the target `compiler-rt` package that matches Clang.
- Set `afdo_profile` to the local absolute path and SHA-256 of the previous
  locked AutoFDO profile for this board and ISA. The workflow rebuilds the
  AFDO reference with the common dependency and command lock.
- Enter `pgo_warning_limits` as an object with non-negative integer limits
  for `profile-instr-unprofiled` and `profile-instr-out-of-date`. Confirm and
  record both limits before any PGO build.
- BASE and PGOGEN build from one frozen dependency set. Three training runs
  use PGOGEN. The workflow checks runtime symbols, collects exact raw
  manifests for the completed decoder, and verifies binary IDs before
  merging with `llvm-profdata`. Setup and plug-in scanner output stays
  outside the training input set.
- Rebuild audits PGO consumption of the locked indexed profile, compiler
  warnings, target code changes and per-target function coverage. Measure
  uses separate locked plans for PGO versus BASE and PGO versus AFDO. ToS
  is primary for the BASE comparison. Sintel results are supplementary.
  Report the mechanism counts separately from paired timing verdicts.

## Exit codes

| Code | Reason | Action |
| ---: | --- | --- |
| 0 | `success` | Continue within the approved scope. Inspect per-stage state and the cleanup journal even if `status` itself succeeds. |
| 1 | `error` | Stop and report the error, receipt path, and relevant logs. |
| 2 | `gate` | Stop and report the failed condition and evidence. Do not retry or relax the gate. |
| 3 | `identity` | Stop. Report the expected and observed identity before any further board operations. |
| 4 | `environment` | Stop and report the unmet resource, tool, build, or transport condition. |
| 5 | `correctness` | Stop and preserve the failing output and oracle evidence. |
| 6 | `board-unreachable` | Try only the target-specific disconnect and connect procedure if authorized. Stop and report if it fails. Recheck identity before any approved resume. |
| 7 | `recovery-required` | Stop and report pending actions and their receipt. Ask the user to power-cycle the board on site. In the next approved session verify identity before restoring, and check that the journal is cleared before proceeding. |
| 8 | `lock-timeout` | Stop and report the lock, observed owners or builders, and wait records. Leave other holders alone. |
| 64 | `usage` | Correct the command using `"$PY" -m afdo_wf --help` and the relevant `explain` output. |
| 130 | `user-abort` | Report the last completed stage and cleanup state. Wait for fresh approval before resuming a live run. |

## Interpret a report

Open the `report.md` bound to the completed report receipt. Use `report.json` for fields omitted from the rendered summary. Report the primary comparison, relative wall-time change, paired bootstrap 95% CI, verdict, and limitations. Keep secondary comparisons labeled. Negative wall-time change means the candidate took less time.

Use the preregistered epsilon of 1% for these experiments.

| Verdict | Meaning |
| --- | --- |
| `faster` | The entire CI lies strictly below -1%. |
| `slower` | The entire CI lies strictly above +1%. |
| `equivalent` | The entire CI lies strictly between -1% and +1%. |
| `inconclusive` | The CI meets or crosses a boundary, or a result gate caps the verdict. |

`publishable=true` means the report passed the workflow publication gates for build lock, conversion quality, consumption, correctness, and cleanup. A publishable result can be inconclusive. If `publishable=false`, report the blockers with the diagnostic result.

Flagged complete pairs remain in the primary analysis. Compare the clean-pair sensitivity result and report counts and causes. Missing pairs, more than 20% flagged or missing pairs, or an absolute difference in variant flagged-round counts of at least `max(2, ceil(0.1 * N))` cap the primary verdict at `inconclusive`. `N` is the planned number of pairs. Report missing telemetry or explicit `unknown` values as unknown.

## Read-only report examples

These copies are available from any fresh clone. They contain the measurements and verdicts with host-specific references omitted. The original job, receipts and artifacts remain with the experiment.

```bash
cat examples/m1-rpi4-thumb/report.md
cat examples/m2a-rpi5-aarch64/report.md
```

- [M1 attempt-11, RPi4 Thumb](../../examples/m1-rpi4-thumb/report.json). ToS reported -1.92% relative wall time, rounded from the report, with verdict `faster`. The bootstrap interval lies entirely below -1%.
- [M2a, RPi5 AArch64](../../examples/m2a-rpi5-aarch64/report.json). ToS reported +0.12% relative wall time, rounded from the report, with verdict `equivalent`. The bootstrap interval lies within +/-1%.
