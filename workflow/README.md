# AutoFDO workflow reference

Run `"$PY" -m afdo_wf explain STAGE` after setting up the checkout as described
in the [workflow skill](../skills/afdo-workflow/SKILL.md). For each stage, the CLI
lists its inputs, outputs, gates and board operations.

## Job inputs and receipts

Use `doctor` for local diagnostics, then use `init` with the package and media manifests to create a draft. Complete its
`missing_for_run` list with the approved device identity, tool paths and
SHA-256 values, the pinned source and build settings, and measurement seeds.
The FFmpeg package files identify the source revision, profiling patch and build
unit. Supply the pinned GBS configuration and snapshot evidence when the runner
will freeze dependencies. For an existing frozen repository, supply the
resolved build configuration, package list and repository ID.

`status` inspects the original job and receipts. `run --dry-run` prints the plan
without running the stages. `run --stop-after afdo-audit` stops after the
candidate build and audit. `--redo` archives the selected receipt and
invalidates its dependents. Resume verifies direct inputs, outputs and
upstream receipts. A cleanup journal binds the board identity and records
owned changes and artifacts.

The executor uses `-j2` and `--threads 1` in a 6 GiB maximum, 5 GiB high and
200% CPU scope. Each GBS invocation takes a shared lock. The job can set
`host.gbs_lock` if another build tool on the host uses a different shared path
inside the workspace. Use `gbs_waits` in build receipts to inspect contention,
other builders and resource checks.

## Build the host profile tools

Use the LLVM 22.1.8 source with the nine IP-mode patches supplied by the
maintainer. The verified source is Tizen LLVM
`c8942ae1b53099a78a97dca2b64427af6e58432b` in `platform/upstream/llvm`, based on
`f999bd406c0a70fe8107aa992164fe6945c5d46a`. Use the standard package spec from
that source and a maintainer-provided GBS configuration with Base and Unified
Toolchain repositories pinned to available snapshots for x86_64. The verified
build used Base `20261030.120529` and Unified `20261104.125239`.

Set `LLVM_SOURCE`, `GBS_CONF` and `LLVM_BUILD_ROOT` to the local checkout,
configuration file and unused build-root path. On a provisioned x86_64 build
host run a normal, full build:

```bash
(
  cd "$LLVM_SOURCE"
  gbs -c "$GBS_CONF" build -A x86_64 --spec llvm.spec \
    --buildroot "$LLVM_BUILD_ROOT" --threads 1 \
    --define '_smp_mflags -j4' --define 'mlgo_build_jobs 4'
)
```

The `llvm` RPM has `usr/bin/llvm-profgen` and `usr/bin/llvm-profdata`. The
`libllvm` RPM supplies the shared library. Extract the RPMs with `rpm2cpio`
and `cpio` into a new directory. Use a compatible loader and library path
from the same build environment if the host cannot run the extracted tools
directly. Verify `--version` for both tools and check that
`llvm-profgen --help` lists `--ip-samples` and `--quality-report`. Pin the
paths and SHA-256 values in the job. If the original snapshots are gone, use
available fixed snapshots and validate converter outputs before using the
new binaries in experiments.

## Board script interface

The workflow invokes the scripts in `board/` using Bash. They journal
session changes, run the workload under a program watchdog, verify the
deployed and loaded libraries, collect telemetry, and verify pulled files
before deleting experiment outputs. The FFmpeg package declares its
decode hook, timing hook, and decoder-process matcher in
`packages/ffmpeg/workloads/`. Profiling mode and interpretation rules are
documented in the [skill](../skills/afdo-workflow/SKILL.md).
