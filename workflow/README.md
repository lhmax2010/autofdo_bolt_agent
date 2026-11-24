# AutoFDO workflow

Python 3.11+ standard library. The [workflow design](../docs/workflow/01_afdo_bolt_workflow_design_v0.3.md) defines the stage contracts. M1 and M2a exercised the live runner. The [M5 CLI and skill draft](../docs/workflow/m5/01_cli_and_skill.md) documents operator commands and exit codes.

From the repository root:

```bash
export TMPDIR="$PWD/temp/tmp"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/workflow"
python3 -m unittest discover -s workflow/tests -v
python3 -m afdo_wf --help
```

The GBS executor uses `-j2` / `--threads 1` in a unique 6G/5G-high/200% scope. Follow the host's shared lock and resource procedures in [STATUS](../docs/STATUS.md).

## Stage interface

```bash
python3 -m afdo_wf status --job "$JOB"
python3 -m afdo_wf explain measure
python3 -m afdo_wf run --job "$JOB" --dry-run
```

Status and dry-run print JSON to stdout. The dry-run can also preview a stopped run such as `--stop-after afdo-audit`. See the M5 reference for `init` and the separate `--redo STAGE` command. Live jobs execute through `run`; it verifies the receipt chain and reconciles the cleanup journal against the identified board. The legacy host stage interface accepts the job and explicit `--package`, `--inputs`, `--output` and `--receipts` paths when needed.

Receipts bind direct inputs, outputs and upstream receipts. Redo commits an invalidation receipt after archiving exact previous receipt bytes, then the next run makes new attempts. Cleanup uses journaled ownership and verified-pull receipts.

## Legacy host job fields

Jobs are JSON data, not shell snippets. Missing evidence is an error:

- preflight: `tools` maps profgen/profdata/loader/libLLVM to `{path, sha256}`.
- build: `build_unit`, `config`, `source`, new `root`, `workdir`; frozen builds
  also have `repo`, `buildconf`. `rpm_packages` explicitly lists runtime/debug
  package names to extract (never install); target runtime paths come from the
  package declaration. Alternatively `artifact_pairs` supplies packaged files.
  `env` may supply the experiment's isolated GBS environment, and `wait_seconds`
  bounds the launch wait. Reserve `_smp_mflags` and `__make` to the executor.
- rebuild: build fields plus `control_lock`, `candidate_lock`, `consumption_job`.
  Lock generation/capture and diagnostic evidence are separate host adapters;
  the CLI never fills absent evidence with a successful-build assumption.
  `buildlock.recorded_switches` / `make_settings` or `verbose_commands` produce
  the command evidence. Keep formal/forensic artifact hashes in verbose locks.
- convert: tool argv arrays `profgen`, `profdata`; `runs` entries with `id`,
  `dso`, `artifact`, `perfscript`, `buildids`, optional `thresholds`, `merge_key`.
  Artifacts contain runtime/debug paths and the exact deployed real `board_path`.
  Merge keys are `(build_lock, ISA, DSO, event, weight, period_unit, workload_policy)`.
  Repetitions must be explicit; equal repetitions sum by default. Identical
  cross-DSO trees are listed; differing bodies stop the merge.
- report: `report_input` names a complete structured payload (see
  `report.REQUIRED`). Missing identity/consumption/oracle/build-lock evidence
  blocks publication. The report always states the conservative-policy limit.

## Host module contracts

- config: closed schema v1, TOML parsing, roles/segments/oracles and strict JSON
  hook protocol. FFmpeg files describe the historical RPi4 Thumb pilot; unset
  quality thresholds and zero min_target_share preserve that pilot's policy.
- build: guarded execution, pinned-metadata checksum verification, dependency
  archive creation, RPM records and packaged ELF manifests. An archive is not
  labelled offline-reproducible until a successful new-root rebuild proves it.
- buildlock: recorded command sets are de-duplicated; verbose command lists are
  multisets and require byte-identical forensic/formal artifacts. Candidate-only
  option removal is explicit. RPM header hashes and source/spec/patch/layout,
  macros, repository/buildconf and GBS identities are bound.
- consumption: streaming parser for the Clang optimization-record subset,
  accepting sample-profile and sample-profile-impl AppliedSamples records;
  unsupported relevant syntax fails closed. Attribution is from a build-relative
  object path through object_to_target. At least one positive record per target,
  exact staged profile option and SHA, and changed target .text are required.
- stats: balanced seeded order; paired log ratios; percentile block bootstrap
  using `random.Random.choices` and linear interpolation; transformed t interval;
  strict relative-epsilon verdicts; primary/sensitivity split; telemetry-window
  bracketing and anomaly > missing > clean priority; retry-history validation.
- board: injectable session transport, identity-before-restore, must-load and
  **all mapped deploy-set** checks and independent oracle comparison.

## Board scripts

Invoke with `bash`. They use old-Bash-compatible constructs, per-step logs,
process-group watchdogs and only experiment-owned paths. `session.sh` saves and
restores governors; the host session adapter owns initial root-state restoration.
`collect.sh` and `measure.sh` require `DEPLOY_MANIFEST`; observers retain maps and
SHAs for the entire workload descendant tree. Host validation filters the
package's workload processes and applies must-load/deploy-set gates before a
stage can complete. A maps error is retained, never treated as a successful gate.

The telemetry capability TSV contains `(frequency|temperature|voltage, sysfs
path)`. Temperatures are raw millidegrees; the parser converts them to Celsius.
Window data must bracket start-1s and exit+1s. Missing capability values, gaps and
truncation stay visible. Cool-down/start-temperature checks save their readings.
`decode.sh` is an untimed FFmpeg JSON oracle hook for the declared 720p inputs;
`timed.sh` is the lower-level fakesink workload command, not an oracle producer.
The timing adapter checks exit/EOS rather than inventing frame hashes.

The host-only negative watchdog test launches its own synthetic process group. See the M1 and M2a evidence for live acceptance.

## Regression and diagnostic build

```bash
python3 workflow/tests/reproduce_pilot.py \
  --evidence docs/workflow/m1/evidence/08/measurement \
  --output temp/YOUR-NEW-DIRECTORY/pilot-reproduction.json
```

This separate test reads only the explicitly authorized saved timing JSON. The
unit suite otherwise uses synthetic fixtures. It does not read sample profiles.
The diagnostic build uses the existing locked pilot profile solely for compiler
consumption verification; no new profile, board run or quality matrix is made.
See `docs/workflow/m1/04_implementation_p1_p2.md` for commands, evidence and limits.
