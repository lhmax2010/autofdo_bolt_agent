# AutoFDO and BOLT for Tizen

**First HQ draft — awaiting PM review.** This branch is an orphan documentation/demo publication branch. It contains no LLVM source tree, captured perf data, profiles, raw evidence or binary tools.

## 1. Overview

| Component | Status |
|---|---|
| llvm-profgen DWARF IP mode | Delivered, limited functional scope |
| AutoFDO / PGO workflow | Design under multi-AI review; Planned (milestone M1) |
| BOLT | Planned, RPi5 only |
| Kernel profiling | Not supported yet |
| Skill / Agent | Planned after workflows |

[Introduction](docs/01_introduction.md) · [Design summary](docs/02_design/llvm_profgen_ip_mode_design_summary.md) · [Delivery report](docs/03_reports/llvm_profgen_delivery.md) · [Host demo](docs/04_demo.md)

**Statistical quality equivalence and performance gains have not been validated.** Explicit max aggregation with skid/zero-fill/head set to none is a conservative caller policy, not a validated default.

## 2. Source locations

- Gerrit project: **platform/upstream/llvm**, host **review.tizen.org**, port 29418.
- Branch: **sandbox/lhmax2025/afdo_profgen**.
- Exact tip: **c8942ae1b53099a78a97dca2b64427af6e58432b**.
- Base: **f999bd406c0a70fe8107aa992164fe6945c5d46a**.
- Internal main source: **41bae45466b853cee173fe80189f2f44b0500b95**.
- This HQ commit: use `git rev-parse HEAD`; the literal is filled on a later update to avoid a self-referential hash.

| Patch | Commit | Subject |
|---|---|---|
| 1 | d1ba7bb9ddc6bc4e00d6bc860fff0f7d9d488d31 | Add test inputs for IP sample mode |
| 2 | a361351e360ae15e9e352db727d177f5dcaf9ba4 | Add IP sample reader and dsoff address conversion |
| 3 | 792c7a7fad1945ceb5a0670a75970c441bc50360 | Add build-id identity checks for IP sample mode |
| 4 | e802e2546e9f02433260856fa86a50a5108367a0 | Generate line-level profiles from IP samples |
| 5 | 3e9b77e2998efc02cda786c3a77a0c3d2be75fc4 | Enumerate instruction boundaries on demand for IP samples |
| 6 | 34787d22b5cf31e2e54e737f5627f6e891c83277 | Add quality reports and failure contracts for IP samples |
| 7 | 7a2d54a7458f2e8dd25539e8cf6f3293f53d57de | Document IP mode and finalize options and reports |
| 8 | 91be904558efbfa391872bc12a0e5662e3905129 | Normalize GNU AS Thumb DWARF addresses in IP mode |
| 9 | c8942ae1b53099a78a97dca2b64427af6e58432b | Exclude IP samples with missing non-leaf callsite lines |

## 3. Host setup

The release host used Ubuntu 24.04.5 LTS x86_64, GBS 2.1.1, Python 3.12.3, git, curl, rpm/rpm2cpio/cpio and readelf. Use your existing authorized Gerrit/GitHub credentials; this repository contains none. Board work additionally requires an existing compatible sdb and board-architecture perf plus its shared libraries; host-only demonstration does not use sdb.

GBS supplies the target toolchain/dependencies. A user systemd manager must support resource-limited scopes. The release used 10 GiB / 400% and -j4; start a full build only with at least 14 GiB MemAvailable. Allow at least 100 GiB free disk as a conservative planning allowance for source, build roots, RPMs and verification clones (not a measured minimum). Lightweight checks use a 3 GiB / 100% scope and start with at least 4 GiB MemAvailable. Do not install missing prerequisites implicitly.

Choose an absolute WORKDIR on local storage. Keep sources, configuration, caches, temporary files and outputs beneath it. Credentials stay in your existing authentication setup.

## 4. Build from the sandbox (normal, non-incremental)

These commands describe the validated release configuration. The host demo below was actually executed with the resulting RPM tool; a second build was not run just for this README.

```bash
export WORKDIR=/absolute/path/to/your/workdir
mkdir -p "$WORKDIR/temp/tmp" "$WORKDIR/temp/gbs-home" "$WORKDIR/temp/gbs-tmp"
export TMPDIR="$WORKDIR/temp/tmp"
cd "$WORKDIR"
# Use your existing authorized Gerrit account; never embed a password or token.
git clone --single-branch --branch sandbox/lhmax2025/afdo_profgen \
  "ssh://${GERRIT_USER}@review.tizen.org:29418/platform/upstream/llvm" llvm-release
git -C llvm-release checkout --detach c8942ae1b53099a78a97dca2b64427af6e58432b
test -z "$(git -C llvm-release diff -- packaging/llvm.spec)"

cat > "$WORKDIR/release.conf" <<EOF
[general]
tmpdir = $WORKDIR/temp/gbs-tmp
profile = profile.tizen_unified_standard
buildroot = $WORKDIR/temp/GBS-ROOT-LLVM-RELEASE
[profile.tizen_unified_standard]
repos = repo.base-standard, repo.unified-standard
[repo.base-standard]
url=https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261030.120529/repos/standard/packages/
[repo.unified-standard]
url=https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261104.125239/repos/standard/packages/
EOF

test "$(awk '/MemAvailable/ {print $2}' /proc/meminfo)" -ge 14680064
test ! -e "$WORKDIR/temp/GBS-ROOT-LLVM-RELEASE"
cd "$WORKDIR/llvm-release"
nice -n 19 ionice -c3 systemd-run --user --scope \
  -p MemoryMax=10G -p CPUQuota=400% \
  env HOME="$WORKDIR/temp/gbs-home" TMPDIR="$WORKDIR/temp/gbs-tmp" \
  GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_COUNT=2 \
  GIT_CONFIG_KEY_0=gc.auto GIT_CONFIG_VALUE_0=0 \
  GIT_CONFIG_KEY_1=maintenance.auto GIT_CONFIG_VALUE_1=false \
  SUDO_ASKPASS=/bin/false \
  gbs -c "$WORKDIR/release.conf" build -A x86_64 --spec llvm.spec \
  --buildroot "$WORKDIR/temp/GBS-ROOT-LLVM-RELEASE" --threads 1 \
  --define '_smp_mflags -j4' --define 'mlgo_build_jobs 4' </dev/null
```

Record every 60 seconds the full meminfo and cgroup memory.peak; record free/uptime every 600 seconds. Stop only your build if MemAvailable stays below 3 GiB for two samples. Preserve the real GBS exit and a timestamped ALL-END on success or failure. The validated supervised command took **79m40s** and 7637 Ninja steps, exit 0; duration depends on the host.

Both packages directories returned HTTP 200, and their shared `repodata/repomd.xml` included x86_64 content. Metadata is not under `packages/x86_64/repodata`. These are fixed IDs, not latest aliases.

**Snapshots are periodically deleted.** If unavailable, record current fixed snapshot IDs and their actual dependency versions, rebuild, and repeat output regressions. Do not expect the same binary SHA across dependency changes. The release dependency archive is retained internally, not included in hq.

RPMs appear in `$WORKDIR/temp/GBS-ROOT-LLVM-RELEASE/local/repos/tizen_unified_standard/x86_64/RPMS/`. llvm-profgen is in the `llvm` RPM at `/usr/bin/llvm-profgen`; libLLVM is in `libllvm`. Extract rather than installing on the host:

```bash
set -euo pipefail
RPMDIR="$WORKDIR/temp/GBS-ROOT-LLVM-RELEASE/local/repos/tizen_unified_standard/x86_64/RPMS"
mkdir "$WORKDIR/temp/extracted"
cd "$WORKDIR/temp/extracted"
rpm2cpio "$RPMDIR/llvm-22.1.8-1.x86_64.rpm" | cpio -idm --no-absolute-filenames
rpm2cpio "$RPMDIR/libllvm-22.1.8-1.x86_64.rpm" | cpio -idm --no-absolute-filenames
sha256sum usr/bin/llvm-profgen
```

This release's extracted tool SHA-256 is **67ad21faba787d276a80673c1f324f7c0591d28d76bd37a8bd57de0d86426be6**. Runtime/debug build IDs are absent under the unchanged LLVM spec; debuglink CRC was verified. The unresolved linker-default follow-up is separate from target-program identity requirements.

## 5. Board setup (documentation only; not run for this release)

Use a compatible Tizen image, matching perf/libLLVM architecture, and adequate cooling. RPi4 needs a kernel with usable hardware cycles/PMU support (the project used a PMUv3-enabled configuration); do not substitute cpu-clock. Verify model, architecture and kernel, not an IP address:

```bash
sdb devices
sdb -s "$SERIAL" shell 'cat /proc/device-tree/model; uname -m; uname -r'
# RPi4: Raspberry Pi 4, armv7l, kernel identifying rpi4/v7l.
# RPi5: Raspberry Pi 5, aarch64, appropriate rpi5 kernel.
```

Use only `/opt/afdo_agent/` for board writes: tools/, lib/, variants/<variant>/, inputs/, work/<run>/. Extract runtime RPMs on the host, then `sdb push` the selected files; do not install RPMs, remount, reboot or alter system libraries. Preserve root/governor initial state and restore on all exits. Privileged operations require separate authorization.

After identity, dependency and SHA checks, establish the authorized performance governor setting. Then record hardware cycles and inspect `perf evlist -v`; the cycles selector must show **type=0, config=0**. Root does not justify changing perf_event_paranoid or kptr_restrict automatically. Check temperature, actual frequency and available firmware throttle/undervoltage indicators. Missing indicators remain unknown; do not label a run clean merely because the governor says performance.

Record /proc/PID/maps and buildid-list to prove which library was loaded. Debug files remain on the host; use packaged runtime/debug counterparts, not a possibly different BUILD-directory link result.

## 6. Running

### (a) Host-only demo

See [demo instructions and actual expected output](docs/04_demo.md). It uses AArch64 and Thumb synthetic fixtures already in the sandbox checkout, with no board connection.

### (b) Manual AutoFDO flow

**Build flags.** The proven FFmpeg method is a local evaluation-spec overlay preserving %{optflags}, with GBS --define selecting ISA/variant. It does not rewrite a user's GBS configuration. Append these to CFLAGS:

```text
-fdebug-info-for-profiling -funique-internal-linkage-names
-mthumb   (RPi4 Thumb)   or -marm (RPi4 A32)
```

AArch64 uses its target defaults. Append `-Wl,--build-id=sha1` to FFmpeg configure's --extra-ldflags. Keep source-relative paths consistent across variants. The tested FFmpeg generation builds used O3 via configure and no LTO.

The internal overlay selects `--define 'eval_isa thumb|a32|a64'` and `--define 'eval_variant S|R|C|G5'`. R uses -fprofile-generate -mllvm -disable-preinline; C uses -fprofile-instr-generate -fcoverage-mapping; G5 uses -fprofile-generate. They are distinct builds. Their overlay is not shipped here as an implemented workflow.

**Deploy and collect.** After separately approved board setup, the following is the historical RPi4 command form (substitute a unique RUN and approved media):

```bash
export LC_ALL=C
export RUN=/opt/afdo_agent/work/NEW_RUN
mkdir -p "$RUN/buildid"
export HOME="$RUN" TMPDIR="$RUN" XDG_CACHE_HOME="$RUN/cache"
export GST_REGISTRY="$RUN/gst-registry.bin"
export LD_LIBRARY_PATH=/opt/afdo_agent/variants/ffmpeg-thumb-S/usr/lib:/opt/afdo_agent/lib
P=/opt/afdo_agent/tools/perf
mkfifo "$RUN/decoded.fifo"
sha256sum "$RUN/decoded.fifo" > "$RUN/decoded.sha256" &
hasher=$!
"$P" --buildid-dir "$RUN/buildid" record --buildid-mmap -e cycles -c 1000003 \
  -o "$RUN/perf.data" -- "$P" --buildid-dir "$RUN/buildid" stat \
  -x ';' -e cycles,instructions,task-clock -o "$RUN/perf-stat.csv" -- \
  gst-launch-1.0 -q filesrc location=/opt/afdo_agent/inputs/bbb_720p_h264_60s.mp4 \
  ! qtdemux ! h264parse ! avdec_h264 max-threads=1 \
  ! video/x-raw,format=I420 ! filesink location="$RUN/decoded.fifo" sync=false
wait "$hasher"
"$P" --buildid-dir "$RUN/buildid" evlist -v -i "$RUN/perf.data" > "$RUN/evlist.txt"
"$P" --buildid-dir "$RUN/buildid" script -i "$RUN/perf.data" \
  --show-mmap-events --show-lost-events -F pid,tid,event,period,ip,dsoff > "$RUN/perfscript.txt"
"$P" --buildid-dir "$RUN/buildid" buildid-list -i "$RUN/perf.data" > "$RUN/buildid-list.txt"
```

The historical RPi5 probe used the same record/export fields with a 300-frame workload:

```bash
export LD_LIBRARY_PATH=/opt/afdo_agent/lib
"$P" --buildid-dir "$RUN/buildid" record --buildid-mmap -e cycles -c 1000003 \
  -o "$RUN/perf.data" -- gst-launch-1.0 -q \
  filesrc location=/opt/afdo_agent/inputs/bbb_720p_h264_60s.mp4 \
  ! qtdemux ! h264parse ! avdec_h264 ! identity eos-after=300 ! fakesink sync=false
"$P" --buildid-dir "$RUN/buildid" script -i "$RUN/perf.data" \
  --show-mmap-events --show-lost-events -F pid,tid,event,period,ip,dsoff > "$RUN/perfscript.txt"
"$P" --buildid-dir "$RUN/buildid" buildid-list -i "$RUN/perf.data" > "$RUN/buildid-list.txt"
```

That old RPi5 probe used the system libavcodec. For a new variant use its usr/lib64 in LD_LIBRARY_PATH and verify maps/build-id; do not reuse old addresses with a new ELF. Preserve complete raw perf.data, unfiltered exports, stderr, exit codes and telemetry. Pull files and compare the complete SHA manifest before deleting only the exact run directory. The internal collection scripts are tools/profgen/board/{common,collect,measure,integration}.sh in main; they are not a completed M1 workflow.

**Convert on the host** using the packaged target ELF/debug and captured text. Define `PROFGEN` as a shell array so the correct GBS loader/library paths are preserved:

```bash
ROOT="$WORKDIR/temp/GBS-ROOT-LLVM-RELEASE/local/BUILD-ROOTS/scratch.x86_64.0"
EXTRACTED="$WORKDIR/temp/extracted"
PROFGEN=("$ROOT/lib64/ld-linux-x86-64.so.2" --library-path \
  "$EXTRACTED/usr/lib64:$ROOT/lib64:$ROOT/usr/lib64" "$EXTRACTED/usr/bin/llvm-profgen")
mkdir -p "$WORKDIR/temp/output"
"${PROFGEN[@]}" --ip-samples \
  --binary="$WORKDIR/inputs/libavcodec.so" \
  --debug-binary="$WORKDIR/inputs/libavcodec.so.debug" \
  --perfscript="$WORKDIR/inputs/perfscript.txt" \
  --perf-buildid-list="$WORKDIR/inputs/buildid-list.txt" \
  --binary-match-regex='^/opt/afdo_agent/variants/ffmpeg-thumb-S/usr/lib/libavcodec\.so\.62\.11\.100$' \
  --ip-event=cycles --ip-weight=period --ip-period-unit=1000003 \
  --ip-aggregation=max --ip-skid=none --ip-zero-fill=none --ip-head-samples=none \
  --format=extbinary --output="$WORKDIR/temp/output/profile.extbinary" \
  --quality-report="$WORKDIR/temp/output/quality.json"
```

Replace the regex with the actual full DSO path (usr/lib64 on AArch64); event names are exact, so cycles:u differs from cycles. The fixed period unit is a package policy example, not a tool default. Add optional usable/target/LOST gates only according to your package policy. Missing-ID waiver is not the production default.

**Consume.** In the package's consumption-spec overlay retain the same base/profiling flags and add `-fprofile-sample-use=<absolute locked profile>` to CFLAGS; build the matching architecture with GBS. For a standalone source the form is:

```bash
clang -O3 -g -fdebug-info-for-profiling -funique-internal-linkage-names \
  -fprofile-sample-use=/absolute/path/to/locked.extbinary -c workload.c -o workload.o
```

Use the target GBS clang, target flags and original build system. FFmpeg G1–G4 consumption builds and performance gains are **not yet validated**; this is a manual recipe, not a completed FFmpeg workflow. LTO is outside the initial workflow design.

### (c) Workflow commands

**Planned (milestone M1).** No workflow command is implemented or shipped in this branch. See [workflow design v0.1](docs/02_design/workflow_design_v0.1.md).

## 7. Read the result

Check process exit status before JSON. Success is zero and verdict.conversion=ok; failure is nonzero. Inspect verdict.identity, usable_ratio_check, sample_threshold_check, lost_ratio_check, failure_stage and reason. Verified identity is not adequate sampling. sampling_adequacy remains unknown or insufficient; throttle fields do not replace board telemetry.

Failures preserve an old profile. Non-conflicting failures atomically replace the quality report with failed JSON; path aliases/output '-' write neither output. Report-write/commit failure can leave an old report: never trust it instead of the invocation exit code. See [contract details](docs/02_design/llvm_profgen_ip_mode_design_summary.md).

## 8. Package owners

Planned under [workflow design §6](docs/02_design/workflow_design_v0.1.md). Each package supplies package.toml, spec-overlay/build hooks, train/benchmark/check scripts and a hashed train/test input manifest. Owners choose target DSOs, fixed period unit, optional gates, metric, rounds and correctness check. Core workflow code will remain package-independent. FFmpeg and GStreamer are proposed first package profiles, not shipped implementations.

## 9. Troubleshooting and limitations

- Aggregation has no default; always pass it. Max/none/none/none is explicit policy, not statistically validated defaults.
- All three quality gates are optional; absent gates do not mean sampling is sufficient.
- Explicitly link sampled programs with -Wl,--build-id=sha1. The LLVM linker-default follow-up is not closed.
- Keep packaged runtime/debug files together. A BUILD artifact may differ from the packaged identity.
- Avg/zero-fill/prev-inst require valid mapping symbols and instruction boundaries; stripping .symtab can make these fail.
- ARMv7 pseudo-probe compilation is known to crash; pseudo-probe and IP perf.data input are outside delivery.
- BOLT is planned only for RPi5; kernel profiles are not supported.
- No statistical quality-equivalence or performance-gain claim. Cooling/current board state was not checked in this host-only release.
- Some detailed inputs and dependency archives remain internal to the host; hq intentionally does not carry them.
