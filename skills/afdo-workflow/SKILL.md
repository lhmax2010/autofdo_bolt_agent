---
name: afdo-workflow
description: Use afdo_wf for Tizen package AutoFDO and PGO experiment work, including FFmpeg on RPi4 armv7l and RPi5 aarch64. Plan or run the build, sample, convert, rebuild, paired measurement, and report stages. Inspect receipts, resume a run, or interpret results.
---

# Tizen package profiling workflow

## Setup and authorization

Start at the root of a checkout or linked worktree with Python 3.11 or later. `WORKDIR` is the main project directory that holds `temp/` and the original run artifacts. The checkout supplies the workflow code.

```bash
WORKDIR=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
export WORKDIR
export PYTHONPATH="$PWD/workflow"
export PYTHONDONTWRITEBYTECODE=1
```

- You can run `status`, `explain`, `run --dry-run`, and `init` for a new draft, and read existing reports without further approval.
- Get explicit user approval for every board-contacting `run`, including a resume, for `--redo`, and for any operation that changes board state. Confirm the job and target in that approval.
- Keep sealed configurations, receipts, and run directories read-only. Use a separate mutable run for new work. Keep workflow-owned board writes under `/opt/afdo_agent/` and preserve the cleanup journal. Do not install RPMs on the board. Delete run directories only after verified-pull through the workflow. Stop only processes owned by this experiment.
- Launch only modes supported by the current CLI and package configuration. The archived FFmpeg examples below use AutoFDO.

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

Use `python3 -m afdo_wf explain STAGE` for stage inputs, gates, board operations, outputs, and receipt fields. The enclosing live run can contact the board for session setup and cleanup even when it reuses stage receipts.

## Host build coordination

The CLI acquires `$WORKDIR/temp/host-gbs.lock` with `flock` for each GBS invocation, including dependency resolution. It records the holder, waits for other `gbs` or `rpmbuild` processes across all users, and releases the lock when the invocation finishes, fails, or is cancelled. The combined wait for the lock and other builders is limited to eight hours.

Before launching GBS the CLI also rechecks the startup resource gates: `MemAvailable >= 16 GiB`, one-minute load average `< 12`, and at least `50 GiB` free on the `WORKDIR` filesystem. It rechecks unmet conditions every ten minutes and reports a gate failure after at most three hours of resource waiting.

Inspect `gbs_waits` in the stage receipt or `status` output. Report the wait records on exit 8. Avoid GBS builds on the same host during timed board measurement.

## Board identity and SDB

An IP address or alias can refer to a replacement board. Before a live run, resume, or board state change, check the model, architecture and image build ID against the job's `identity`. Check the kernel too when the job pins it. Use the approved endpoint for the identity probe and stop on any mismatch.

If the authorized target disconnects, limit recovery to that endpoint. `SERIAL` is the approved SDB endpoint, including the port when required.

```bash
sdb disconnect "$SERIAL"
sdb connect "$SERIAL"
sdb -s "$SERIAL" shell 'tr -d "\000" < /proc/device-tree/model; printf "\n"; uname -m; uname -r; sed -n "s/^TZ_BUILD_ID=//p" /etc/tizen-build.conf'
```

Reassert identity after reconnecting. If reconnect or identity verification fails, stop and report it. Never run `sdb kill-server` or restart the shared SDB service. Leave other devices and connections alone.

## Where the inputs live

Use these paths relative to the checkout for configuration and relative to `WORKDIR` for local artifacts.

| Input | RPi4 FFmpeg | RPi5 FFmpeg |
| --- | --- | --- |
| Package TOML | `workflow/packages/ffmpeg/package.toml` | `workflow/packages/ffmpeg/package-rpi5.toml` |
| Input manifest (`--inputs`) | `workflow/packages/ffmpeg/inputs.toml` | Same |
| Board profile (`--platform`) | `rpi4-armv7l` in `workflow/platforms/rpi4-armv7l.toml` | `rpi5-aarch64` in `workflow/platforms/rpi5-aarch64.toml` |
| Frozen dependency archive | `temp/m1-pilot-v02-20261116/build/repo/` | `temp/gbs-deps-archive/m2a-ffmpeg-rpi5-aarch64-01/` |

The frozen archives are references for reproducing the recorded jobs. Use the job's repository receipt and manifest to check the archive and build configuration. A new RPi5 preparation job resolves and freezes its own dependencies before building.

The three FFmpeg clips live in separate directories, so pass one `--media ID=FILE` per clip. The draft checks each file against the input manifest.

### Preview an FFmpeg RPi5 draft

Use the setup block first. Choose an unused preview directory under `WORKDIR/temp`.

```bash
PREVIEW="$WORKDIR/temp/m5-init-check-$(date +%F)"
python3 -m afdo_wf init --workdir "$WORKDIR" --platform rpi5-aarch64 \
  --package workflow/packages/ffmpeg/package-rpi5.toml \
  --inputs workflow/packages/ffmpeg/inputs.toml \
  --media "bbb-720p-60=$WORKDIR/media/bbb_720p_h264_60s.mp4" \
  --media "tos-720p-60=$WORKDIR/temp/board-round1/tos_720p_h264_60s.mp4" \
  --media "sintel-1080p-60=$WORKDIR/temp/media_src/sintel_1080p_h264_60s.mp4" \
  --job "$PREVIEW/job.json" --output "$PREVIEW/run"
python3 -m afdo_wf run --job "$PREVIEW/job.json" --dry-run
```

## Create, inspect, resume, and redo

Generate a job draft using the package and input TOML files, the board profile, and the local media. For media stored together, use `--media-dir` as below. Choose an unused job path and run directory. `PLATFORM` is `rpi4-armv7l` or `rpi5-aarch64` for the examples here.

```bash
python3 -m afdo_wf init --package "$PACKAGE" --inputs "$INPUTS" \
  --platform "$PLATFORM" --media-dir "$MEDIA_DIR" --workdir "$WORKDIR" \
  --job "$JOB" --output "$RUN_DIR"
python3 -m afdo_wf run --job "$JOB" --dry-run
python3 -m afdo_wf explain preflight
```

Fill the draft's `missing_for_run` fields with the authorized board identity, tool locks, source and build settings, and seeds. Set `draft=false` after review. Preview again and inspect the planned inputs and board operations before an approved `python3 -m afdo_wf run --job "$JOB"`.

For an interrupted run, first inspect the same job.

```bash
python3 -m afdo_wf status --job "$JOB"
python3 -m afdo_wf explain "$STAGE"
python3 -m afdo_wf run --job "$JOB" --dry-run
```

Use `stage_order`, receipt paths, `input_sha`, `upstream_sha`, and failure reasons. Report any `cleanup_pending`, and verify the target's identity before any restoration in the next approved session. Follow exit 7 below if recovery is required. After approval and with matching inputs and cleared blockers, resume using the same job and `run`. The runner revalidates receipts before reuse.

For an explicitly approved redo on a mutable job, record why the stage must run again.

```bash
python3 -m afdo_wf --redo "$STAGE" --reason "$REASON" --job "$JOB"
python3 -m afdo_wf status --job "$JOB"
python3 -m afdo_wf run --job "$JOB" --dry-run
```

Record the redo receipt path and affected stages. Redo archives receipts and invalidates the selected stage and its dependents. A subsequent authorized `run` executes the plan.

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
| 64 | `usage` | Correct the command using `python3 -m afdo_wf --help` and the relevant `explain` output. |
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

## Sealed run examples

Use the setup block above. These are the actual paths relative to `WORKDIR`. Run the following read-only commands from the checkout. The original artifacts must be present in that workspace.

```bash
M1_JOB="$WORKDIR/temp/m1-ffmpeg-rpi4-thumb-01/attempt-11/job.json"
M2A_JOB="$WORKDIR/temp/m2a-rpi5-prep-20261119/continuation/job.json"
printf '\n--- M1 status ---\n'
python3 -m afdo_wf status --job "$M1_JOB"
printf '\n--- M1 dry-run ---\n'
python3 -m afdo_wf run --job "$M1_JOB" --dry-run
printf '\n--- M2a status ---\n'
python3 -m afdo_wf status --job "$M2A_JOB"
printf '\n--- M2a dry-run ---\n'
python3 -m afdo_wf run --job "$M2A_JOB" --dry-run
printf '\n--- Explain measure ---\n'
python3 -m afdo_wf explain measure
printf '\n--- Explain report ---\n'
python3 -m afdo_wf explain report
printf '\n--- M1 report ---\n'
cat "$WORKDIR/temp/m1-ffmpeg-rpi4-thumb-01/attempt-11/formal/stages/report/001/report.md"
printf '\n--- M2a report ---\n'
cat "$WORKDIR/temp/m2a-rpi5-prep-20261119/continuation/formal-attempt-01/stages/report/001/report.md"
```

- **M1 ToS** reported -1.92% relative wall time, rounded from the report, with verdict `faster`. Its bootstrap CI lies entirely below -1%.
- **M2a ToS** reported +0.12% relative wall time, rounded from the report, with verdict `equivalent`. Its bootstrap CI lies within +/-1%.
