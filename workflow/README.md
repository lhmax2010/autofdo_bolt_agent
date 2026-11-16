# AutoFDO workflow: M1 phases 1 and 2

Python 3.11+ standard library. Design: `docs/workflow/01_afdo_bolt_workflow_design_v0.3.md`.
These phases implement host contracts and board scripts. They **do not establish
live automated M1 acceptance**: board transport/orchestration is deliberately a
`--dry-run` interface until a separately authorized board-validation phase.
No command here installs packages or changes a Gerrit branch.

From the repository root:

```bash
export TMPDIR="$PWD/temp/tmp"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/workflow"
python3 -m unittest discover -s workflow/tests -v
python3 -m afdo_wf --help
```

Apply the host resource wrapper from STATUS to these commands. Heavy GBS work is
serial, -j2 / --threads 1, in a unique 6G/5G-high/200% scope. Its supervisor has a
separate 3G/200% limit. It checks 16 GiB available RAM, load < 0.6 * nproc and
50 GiB free disk before launch; every 60 s it records meminfo, load, disk and
cgroup memory. Only its own scope can be stopped. No automatic retry is made on
a compilation error. A new attempt requires an explicitly new buildroot.

## Stage interface

`python3 -m afdo_wf STAGE --package PACKAGE --inputs INPUTS --job JOB.json
--output OUTPUT --receipts RECEIPTS [--dry-run] [--redo]`

Stages: preflight, build, deploy, collect, convert, rebuild, measure, report,
restore; `run` traverses these stages. In phases 1/2, `run`, deploy, collect,
measure and restore require `--dry-run`. Dry runs write plans, never successful
stage receipts and never contact a board. Executing a board stage without that
flag fails before any host build is started. This intentionally prevents a
partial live `run` from being mistaken for end-to-end acceptance.

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

Receipts bind scripts, package/inputs, job-file contents, file-valued job inputs,
outputs and upstream receipts. Resume rehashes the dependency chain. `--redo`
archives and invalidates descendants; it never deletes an old buildroot.
`Cleanup` journals undo actions before mutation. `verified_pull` persists a
receipt before `delete_pulled` can invoke an exact-directory deletion callback.
A dropped connection leaves pending actions and requires the same board identity
on the next restore attempt.

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
  **all mapped deploy-set** checks, independent oracle comparison. No real SDB
  adapter is enabled in this phase.

Design v0.3 says a flag rate that "differs clearly" caps the verdict but gives
no numerical test. `stats.analyze` therefore requires an explicit
`clear_flag_imbalance` assessment; absent assessment caps at inconclusive. It
never silently chooses a new threshold. This needs an owner/PM policy for future
automated measurement. The authorized historical regression below reproduces
numbers, not a new qualification decision.

## Board scripts (not deployed in this phase)

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

No live-board reliability claim follows from `bash --posix -n`. The host-only
negative watchdog test launches only its own synthetic process group. shellcheck
is optional when already installed; this host does not have it.

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
