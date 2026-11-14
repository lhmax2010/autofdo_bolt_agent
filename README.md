# Tizen user-space profiling and optimization

## 0. Quick start: host-only

This is the shortest path from source to a tested profile. It needs no board. Set PROJECT and DOCS to absolute paths on your machine; DOCS is the directory containing this README.

```bash
export PROJECT=/path/to/project
export DOCS=/path/to/this/documentation
export GERRIT_USER=your_gerrit_account
mkdir -p "$PROJECT/scratch/gbs-tmp"
export TMPDIR="$PROJECT/scratch/gbs-tmp"
git clone --single-branch --branch sandbox/lhmax2025/afdo_profgen \
  "ssh://${GERRIT_USER}@review.tizen.org:29418/platform/upstream/llvm" "$PROJECT/llvm"
git -C "$PROJECT/llvm" checkout --detach c8942ae1b53099a78a97dca2b64427af6e58432b

python3 - "$DOCS/examples/gbs/llvm-release.conf.in" "$PROJECT" <<'PY'
from pathlib import Path
import sys
source, project = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
(project / "release.conf").write_text(source.read_text().replace("@PROJECT@", str(project)))
PY

cd "$PROJECT/llvm"
gbs -c "$PROJECT/release.conf" build -A x86_64 --spec llvm.spec \
  --buildroot "$PROJECT/build/llvm-root" --threads 1 \
  --define '_smp_mflags -j4' --define 'mlgo_build_jobs 4'

export RPMDIR="$PROJECT/build/llvm-root/local/repos/tizen_unified_standard/x86_64/RPMS"
export ROOT="$PROJECT/build/llvm-root/local/BUILD-ROOTS/scratch.x86_64.0"
export EXTRACTED="$PROJECT/extracted"
bash "$DOCS/demo/extract_tool.sh" "$RPMDIR" "$EXTRACTED" "$ROOT"
bash "$DOCS/demo/run_host_demo.sh" "$PROJECT/llvm" "$EXTRACTED" "$ROOT" "$PROJECT/demo-output"
```

The build root and extraction/demo output directories should be new. Compare the output to [the executed demo](docs/04_demo.md): both examples report conversion ok, one target and usable sample, one written position, identity unverified and sampling adequacy unknown. The identity waiver is for these synthetic fixtures only.

For this documentation revision, the already verified release source/build artifacts were reused; extraction, version/help and demo commands were executed again. LLVM was not rebuilt. Full build instructions reproduce the prior successful normal build configuration; see section 4 for remaining host-environment limitations.

## 1. Overview and roadmap

| Component | Status |
|---|---|
| llvm-profgen IP mode | Delivered (limited scope): user-space AArch64 and ARMv7 Thumb-2/A32 |
| Optimization workflow | Planned / Not implemented |
| BOLT on RPi5 | Planned / Not implemented |
| Skill and Agent | Planned / Not implemented |
| Kernel | Separate track; method to be decided |

| Component / milestone | Sequence and acceptance | Status |
|---|---|---|
| llvm-profgen IP mode | User-space DWARF IP on AArch64 and ARMv7 Thumb-2/A32; functional release checks passed | Delivered (limited scope) |
| M1 | FFmpeg on RPi4: reproducible collection, identity checks, conversion, rebuild, correctness and timed comparison | Planned / Not implemented |
| M2 | FFmpeg on RPi5, plus instrumented PGO on both boards; equivalent artifact and result contracts | Planned / Not implemented |
| M3 | GStreamer package profiles and multi-library collection/rebuild | Planned / Not implemented |
| M4 | BOLT on RPi5 only; relocation/identity checks, host conversion and correctness/timing | Planned / Not implemented |
| M5 Skill | Reusable SKILL.md instructions plus scripts that run workflow stages and interpret results | Planned / Not implemented |
| Agent | After the skill: select packages, run the workflow through the skill, report results; builds on both layers | Planned / Not implemented |
| Kernel | Separate track; method to be decided; current llvm-profgen delivery has no kernel support | Planned / Not implemented |

Package owners provide benchmark and data-collection methods through package profiles.

Validated: normal release build, strict input/address/identity/failure behavior, prior integration checks, fixed C1 output regression, IP profile/JSON preservation and the host demo.

Not validated: statistical quality equivalence, optimal defaults, performance gains, the proposed workflow automation, BOLT, skill or Agent. Explicit max/none/none/none is a conservative calling policy; it is not a claim that defaults were statistically validated.

[Introduction](docs/01_introduction.md) | [IP design](docs/02_design/llvm_profgen_ip_mode_design_summary.md) | [Workflow plan](docs/02_design/workflow_design_overview.md) | [Delivery report](docs/03_reports/llvm_profgen_delivery.md)

## 2. Prerequisites

| Requirement | Tested / recommended |
|---|---|
| Host | Ubuntu 24.04.5 LTS, x86_64 |
| GBS | 2.1.1; existing working Tizen build environment and privileges |
| Python | 3.12.3 tested; scripts use the standard library |
| Source access | Tizen Gerrit account; registered SSH public key; reachable review.tizen.org port 29418 |
| Utilities | git, bash, curl, rpm, rpm2cpio, cpio, readelf, sha256sum |
| Board access | sdb compatible with the Tizen image; not required for the host demo |
| Memory | At least 16 GiB host RAM; at least 14 GiB available recommended for the full build |
| Disk | At least 100 GiB free is a conservative planning allowance, not a measured minimum |
| Optional resource control | systemd user scopes, nice and ionice |
| Media preparation | ffmpeg with libx264, ffprobe, Python zipfile support |

Register your SSH public key with Gerrit and verify source access with git ls-remote. Use your organization's SSH host-key verification procedure. Credential provisioning and GBS installation are **Not documented yet** here; this guide assumes those prerequisites work. It contains no account secrets.

## 3. Get and identify the source

Project: platform/upstream/llvm. Sandbox: sandbox/lhmax2025/afdo_profgen.
Tip: c8942ae1b53099a78a97dca2b64427af6e58432b.
Base: f999bd406c0a70fe8107aa992164fe6945c5d46a.

```bash
git -C "$PROJECT/llvm" rev-parse HEAD
git -C "$PROJECT/llvm" log --reverse --format='%H %s' \
  f999bd406c0a70fe8107aa992164fe6945c5d46a..HEAD
git -C "$PROJECT/llvm" diff --exit-code f999bd406c0a70fe8107aa992164fe6945c5d46a \
  -- packaging/llvm.spec
```

The last command should report no change. The log must contain these nine commits:

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

## 4. Build the host tool

The complete [GBS configuration template](examples/gbs/llvm-release.conf.in) is:

```ini
[general]
tmpdir = @PROJECT@/scratch/gbs-tmp
profile = profile.tizen_unified_standard
buildroot = @PROJECT@/build/llvm-root

[profile.tizen_unified_standard]
repos = repo.base-standard, repo.unified-standard

[repo.base-standard]
url=https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261030.120529/repos/standard/packages/

[repo.unified-standard]
url=https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/tizen-unified-toolchain_20261104.125239/repos/standard/packages/
```

Replace @PROJECT@ with your absolute project path as in quick start. All effective fields match the tested configuration except filesystem paths. **No configuration fields are omitted.** The URLs use fixed snapshots. Metadata is at packages/repodata/repomd.xml; it is shared across architectures, rather than residing under packages/x86_64/repodata.

Use the normal non-incremental command in quick start. --threads 1 selects one package build, _smp_mflags -j4 bounds normal compilation, and mlgo_build_jobs 4 bounds the spec's separate MLGO job setting. There is no test-spec overlay, incremental or short-circuit flag.

Optional resource-limited form:

```bash
nice -n 19 ionice -c3 systemd-run --user --scope \
  -p MemoryMax=10G -p CPUQuota=400% \
  gbs -c "$PROJECT/release.conf" build -A x86_64 --spec llvm.spec \
  --buildroot "$PROJECT/build/llvm-root" --threads 1 \
  --define '_smp_mflags -j4' --define 'mlgo_build_jobs 4'
```

Expected duration on the tested host was 79m40s, 7637 Ninja steps, exit 0. Peak cgroup memory was 10 GiB with reclaim pressure but no OOM. Running this simplified command from a newly provisioned host is **Not verified**; the configuration and build arguments are those of the successful release.

Snapshots can be deleted. Check the directories and repomd.xml before building. If removed, select available fixed IDs, record actual dependency versions and repeat functional/output regression. Binary SHA equality is not expected after dependency changes. The [delivery report](docs/03_reports/llvm_profgen_delivery.md) identifies the versions used here.

## 5. Extract and verify

The llvm RPM installs /usr/bin/llvm-profgen and llvm-profdata. libLLVM is in the libllvm RPM. No host RPM installation is needed:

```bash
bash "$DOCS/demo/extract_tool.sh" "$RPMDIR" "$EXTRACTED" "$ROOT"
sha256sum "$EXTRACTED/usr/bin/llvm-profgen"
LOADER="$ROOT/lib64/ld-linux-x86-64.so.2"
LIBS="$EXTRACTED/usr/lib64:$ROOT/lib64:$ROOT/usr/lib64"
"$LOADER" --library-path "$LIBS" "$EXTRACTED/usr/bin/llvm-profgen" --version
"$LOADER" --library-path "$LIBS" "$EXTRACTED/usr/bin/llvm-profgen" --help
```

The extraction script requires a new destination; if quick start already ran it, run the last four verification commands rather than extracting again.

Release SHA-256: **67ad21faba787d276a80673c1f324f7c0591d28d76bd37a8bd57de0d86426be6**.
Version contains LLVM version 22.1.8 and Optimized build. Help must list ip-samples, ip-aggregation, ip-skid, ip-zero-fill, ip-head-samples and quality-report.

This tool and its debug file have no build-ID under the unchanged spec; .gnu_debuglink CRC matches. This does not waive the build-ID requirement for the programs being sampled.

## 6. Test

```bash
bash "$DOCS/demo/run_host_demo.sh" "$PROJECT/llvm" "$EXTRACTED" "$ROOT" "$PROJECT/demo-output-new"
```

See [actual output and per-field expectations](docs/04_demo.md). Both examples use synthetic input from the sandbox tree, not captured data.

Prior acceptance ran the llvm-profgen lit suite: 84 PASS, 1 UNSUPPORTED, 1 XFAIL, 0 FAIL. The normal release spec does not build/run tests. A separate test-enabled build can normally run `ninja check-llvm-profgen`, or the build's llvm-lit on its configured llvm-profgen test directory; the exact standalone source-build recipe and dependencies are **Not verified** for this release environment. Do not invoke lit directly on unconfigured source tests and interpret missing substitutions as tool failures.

## 7. Board setup

Historical working configurations:

| Board | Image snapshot / build ID | Kernel |
|---|---|---|
| RPi4 Cortex-A72, armv7l | tizen-unified-toolchain_20261028.105834_tizen-headed-armv7l | 6.12.80-arm-rpi4-v7l, Oct 28 12:18:25 UTC 2026 |
| RPi5 Cortex-A76, aarch64 | tizen-unified-toolchain_20261028.105834_tizen-headed-aarch64 | 6.12.80-arm64-rpi4-v8, Oct 28 12:37:44 UTC 2026 |
| Later RPi4 data collection | tizen-unified-toolchain_20261104.160709 | 6.12.80-arm-rpi4-v7l, Nov 4 17:05:36 UTC 2026 |

These identify tested historical images, not guaranteed current download availability. Installation/flashing instructions and the current cooling installation are **Not documented yet**.

RPi4 requires CONFIG_ARM_PMUV3=y in arch/arm/configs/tizen_bcm2711_defconfig, alongside PERF_EVENTS/HW_PERF_EVENTS support. The tested configuration change added that one line; comparison to the same image baseline found only that option changed among 5649 configuration values. Cortex-A72's PMU is matched by arm_pmuv3, whose default was ARM64, so ARM32 needed an explicit setting. No arm64 defconfig change is required by this fix. Kernel Gerrit project is platform/kernel/linux-rpi; the exact merged branch/commit carrying the change is **Not documented yet**. Do not treat a local patch ID as proof of a merged image.

### perf and deployment

Tested perf version: 6.12.80, from linux-kernel-perf-6.12.80-0.<arch>.rpm in the Tizen Unified repositories. RPi5 used Unified 20261027.063617 with Base 20261026.051209; these older snapshots may no longer exist. RPi4's perf package VCS identified platform/kernel/linux-rpi at 21645b17c0d913e2ba7e10fbc9c993d286b3f57d. Use matching architecture packages and check dynamic dependencies on your image.

Historical extracted perf SHA values:
- armv7l: 41b9b9a0d41da1b2a600c84ffa482ea05c52af54af094f5c6a2bf52d6aa13138
- aarch64: d23f11a13d5b0b21fc1957a883eb0025c80f9a26bcde360b7031b4d3b1348949

libLLVM.so.22.1 is required; other dependencies, including libxml2.so.16, resolved from the tested image. Run ldd again on your image rather than assuming the same dependency closure.

```bash
# Host: PERF_RPM and BOARD_LLVM_RPM are matching target-architecture packages.
mkdir -p "$PROJECT/board-tools" "$PROJECT/board-libs"
rpm2cpio "$PERF_RPM" | (cd "$PROJECT/board-tools" && cpio -idm --no-absolute-filenames)
rpm2cpio "$BOARD_LLVM_RPM" | (cd "$PROJECT/board-libs" && cpio -idm --no-absolute-filenames)
sdb devices
sdb -s "$SERIAL" shell 'cat /proc/device-tree/model; uname -m; uname -r'
sdb -s "$SERIAL" root on
sdb -s "$SERIAL" shell 'mkdir -p /opt/afdo_agent/tools /opt/afdo_agent/lib /opt/afdo_agent/variants /opt/afdo_agent/inputs /opt/afdo_agent/work'
sdb -s "$SERIAL" push "$PROJECT/board-tools/usr/bin/perf" /opt/afdo_agent/tools/perf
# ARMv7 libraries use usr/lib; AArch64 libraries use usr/lib64.
sdb -s "$SERIAL" push "$BOARD_LIBLLVM_FILE" /opt/afdo_agent/lib/libLLVM.so.22.1
sdb -s "$SERIAL" shell 'chmod 755 /opt/afdo_agent/tools/perf; LD_LIBRARY_PATH=/opt/afdo_agent/lib ldd /opt/afdo_agent/tools/perf; LD_LIBRARY_PATH=/opt/afdo_agent/lib /opt/afdo_agent/tools/perf --version'
```

Verify both transferred files with sha256sum on host and board. Match the device-tree model and architecture; RPi5's tested kernel string still contains rpi4-v8, so kernel text alone is not board identification. Deploy libraries by extraction/copy and LD_LIBRARY_PATH, not by replacing system libraries.

### Frequency, temperature and hardware event check

Run on the board:

```bash
for p in /sys/devices/system/cpu/cpufreq/policy*; do
  echo "$p"; cat "$p/scaling_governor" "$p/scaling_min_freq" "$p/scaling_max_freq" "$p/scaling_cur_freq"
done
for z in /sys/class/thermal/thermal_zone*; do
  echo "$z"; cat "$z/type" "$z/temp"
done
P=/opt/afdo_agent/tools/perf
export LD_LIBRARY_PATH=/opt/afdo_agent/lib
"$P" list hw
mkdir -p /opt/afdo_agent/work/hardware-check
"$P" --buildid-dir /opt/afdo_agent/work/hardware-check/buildid record \
  --buildid-mmap -e cycles -c 1000003 \
  -o /opt/afdo_agent/work/hardware-check/perf.data -- sleep 1
"$P" evlist -v -i /opt/afdo_agent/work/hardware-check/perf.data
```

cycles must have type=0 and config=0. A workload run must also produce nonzero cycles samples. Software cpu-clock is not a substitute. Missing hardware access, unresolved dependencies or unexpected identity require correction before collection.

For repeatable comparisons save each governor value, set performance for collection/measurement and restore each saved value on exit. A shell-session example:

```bash
SAVE=/opt/afdo_agent/work/governor-save
mkdir -p "$SAVE"
for p in /sys/devices/system/cpu/cpufreq/policy*; do
  cat "$p/scaling_governor" > "$SAVE/${p##*/}"
  printf 'performance\n' > "$p/scaling_governor"
done
restore_governors() {
  for p in /sys/devices/system/cpu/cpufreq/policy*; do
    cat "$SAVE/${p##*/}" > "$p/scaling_governor"
  done
}
trap restore_governors EXIT
```

Use effective cooling, record frequency/temperature during runs and preserve firmware throttle/undervoltage readings when available. Missing indicators remain unknown. Finish the session with governors restored and restore the original root state (for a session started unprivileged: sdb -s "$SERIAL" root off from the host).

## 8. End-to-end manual AutoFDO: FFmpeg

**Performance gains not yet validated.** The [FFmpeg example](examples/ffmpeg/README.md) supplies a spec patch and exact fixed source revision in Gerrit platform/upstream/ffmpeg. It appends profiling DWARF/unique-name flags, selects Thumb/A32, adds SHA-1 build-ID and optionally consumes a sample profile inside the build root. ARMv7 Thumb and A32 baseline builds are verified using the [target GBS configuration](examples/gbs/ffmpeg-target.conf.in): Unified 20261104.125239 / Base 20261030.120529, clang 22.1.8-4.1, fresh roots, -j2, exits 0. Measured times were 303.08 and 314.09 seconds. The example gives exact commands and runtime/debug build-ID checks; packaged libavcodec/libavutil identities match and their DWARF/line tables are readable. AArch64 and profile-consuming builds remain **Not verified**.

### Training and test media

Training: Blender Foundation / Big Buck Bunny, CC-BY 3.0; public source:
https://download.blender.org/demo/movies/BBB/bbb_sunflower_1080p_30fps_normal.mp4.zip
License/background: https://peach.blender.org/about/

| File | SHA-256 |
|---|---|
| Source ZIP | e320fef389ec749117d0c1583945039266a40f25483881c2ff0d33207e62b362 |
| bbb_sunflower_1080p_30fps_normal.mp4 | ae51005850b0ff757fe60c3dd7a12d754d3cd2397d87d939b55235e457f97658 |
| bbb_720p_h264_60s.mp4 | b5e116b9d01cec8e7f697041c53575d36bd96a5928e40faa69e731f9ae2d00a4 |

Extract the MP4 with Python zipfile or an existing unzip utility, then reproduce the 300-360 second segment:

```bash
ffmpeg -nostdin -hide_banner -ss 300 -i bbb_sunflower_1080p_30fps_normal.mp4 \
  -t 60 -an -vf scale=1280:720,setsar=1,fps=30 -c:v libx264 \
  -preset veryfast -profile:v high -pix_fmt yuv420p \
  -b:v 4M -maxrate 4M -bufsize 8M -threads 2 -filter_threads 1 \
  -movflags +faststart bbb_720p_h264_60s.mp4
sha256sum bbb_720p_h264_60s.mp4
```

The recorded segment is 60s, 1280x720, 30fps, High profile, level 3.1. Encoder/version differences can change bytes; record the actual generated checksum and use identical input bytes for comparisons.

A separate test source was Tears of Steel, Blender Foundation / Mango Open Movie Project, CC-BY 3.0:
https://download.blender.org/demo/movies/ToS/tears_of_steel_720p.mov
Source SHA efa9062d9cdb7a338e40ad530dfdf234806743f29ae6a1a136b97ece4e588e8f.
The same 300-360 second encoding recipe yielded test-segment SHA 280fbd41f8772491ebe784aa19a3caed3bb1e8b2e64daef1d2a5a284d1f38ad1.
License/background: https://mango.blender.org/sharing/

### Deploy, collect and export

Extract baseline libavcodec and its matching library dependencies under a local runtime directory; keep matching packaged debuginfo on the host. Transfer the runtime tree and media:

```bash
sdb -s "$SERIAL" push "$BASELINE_RUNTIME" /opt/afdo_agent/variants/baseline
sdb -s "$SERIAL" push bbb_720p_h264_60s.mp4 /opt/afdo_agent/inputs/bbb_720p_h264_60s.mp4
```

Check the actual resulting directory layout and full SHA manifest. For RPi4 set the library directory to usr/lib; use usr/lib64 on RPi5. On the board, after the setup checks:

```bash
set -euo pipefail
RUN=/opt/afdo_agent/work/collect-new
mkdir -p "$RUN/buildid" "$RUN/cache"
export LC_ALL=C HOME="$RUN" TMPDIR="$RUN" XDG_CACHE_HOME="$RUN/cache"
export GST_REGISTRY="$RUN/registry.bin"
export LD_LIBRARY_PATH=/opt/afdo_agent/variants/baseline/usr/lib:/opt/afdo_agent/lib
P=/opt/afdo_agent/tools/perf
"$P" --buildid-dir "$RUN/buildid" record --buildid-mmap -e cycles -c 1000003 \
  -o "$RUN/perf.data" -- gst-launch-1.0 -q \
  filesrc location=/opt/afdo_agent/inputs/bbb_720p_h264_60s.mp4 \
  ! qtdemux ! h264parse ! avdec_h264 max-threads=1 \
  ! video/x-raw,format=I420 ! fakesink sync=false
"$P" evlist -v -i "$RUN/perf.data" > "$RUN/evlist.txt"
"$P" --buildid-dir "$RUN/buildid" script -i "$RUN/perf.data" \
  --show-mmap-events --show-lost-events -F pid,tid,event,period,ip,dsoff > "$RUN/perfscript.txt"
"$P" --buildid-dir "$RUN/buildid" buildid-list -i "$RUN/perf.data" > "$RUN/buildid-list.txt"
```

During the workload save /proc/<decoder-pid>/maps and verify the actual libavcodec path/build-ID. Keep complete perf.data, unfiltered text, stderr/exit codes and environment records. Pull the whole run, check every SHA and file path, then remove only that verified run directory. The commands describe the established collection form; this documentation update did not connect a board.

### Convert on the host

```bash
mkdir -p "$PROJECT/results"
PROFGEN=("$ROOT/lib64/ld-linux-x86-64.so.2" --library-path \
  "$EXTRACTED/usr/lib64:$ROOT/lib64:$ROOT/usr/lib64" "$EXTRACTED/usr/bin/llvm-profgen")
"${PROFGEN[@]}" --ip-samples \
  --binary="$PROJECT/inputs/libavcodec.so" \
  --debug-binary="$PROJECT/inputs/libavcodec.so.debug" \
  --perfscript="$PROJECT/inputs/perfscript.txt" \
  --perf-buildid-list="$PROJECT/inputs/buildid-list.txt" \
  --binary-match-regex='^/opt/afdo_agent/variants/baseline/usr/lib/libavcodec\.so\.62\.11\.100$' \
  --ip-event=cycles --ip-weight=period --ip-period-unit=1000003 \
  --ip-aggregation=max --ip-skid=none --ip-zero-fill=none --ip-head-samples=none \
  --format=extbinary --output="$PROJECT/results/profile.extbinary" \
  --quality-report="$PROJECT/results/quality.json"
```

Adjust the exact regex and event to the captured path/name; use usr/lib64 for AArch64. Fixed period unit is a package policy example. Optional usable/target/LOST thresholds belong to the package configuration. Verify conversion and identity before consumption; missing-ID allowance is not a production default.

### Rebuild and compare

Follow the example patch's Source2000 procedure to rebuild with -fprofile-sample-use. Preserve source-relative paths, architecture and base flags. Verify packaged runtime/debug identities and keep both variants.

First compare decoded-output SHA for baseline and optimized libraries using an I420 filesink output (or a FIFO hashed concurrently). Then time otherwise identical pipelines with /usr/bin/time and alternate the LD_LIBRARY_PATH of baseline and optimized variants. Exclude fixed warmups, run at least ten interleaved rounds, retain every round and its correctness/thermal/frequency data. Use the planned [measurement method](docs/02_design/workflow_design_overview.md) for intervals and interpretation. Exact timed runner automation and FFmpeg profile-consuming performance results are **Not verified**. Performance gains not yet validated.

## 9. Read the result

Check process exit before reading JSON. Below is an actual projection of the demo report (complete verdict, selected sample counters; the [demo report](docs/04_demo.md) includes the complete samples object). Values are copied from the executed AArch64 demo; Thumb is identical:

```json
{
  "verdict": {
    "conversion": "ok",
    "failure_stage": null,
    "fallback_callback_count": 0,
    "identity": "unverified",
    "lost_ratio_check": "not_evaluated",
    "reason": null,
    "sample_threshold_check": "not_evaluated",
    "sampling_adequacy": "unknown",
    "usable_ratio_check": "not_evaluated"
  },
  "samples": {
    "input_total": {
      "sample_count": 1
    },
    "target": {
      "counts": {
        "normalized_weight": {
          "denominator": 1000003,
          "numerator": 1000003
        },
        "period_sum": 1000003,
        "sample_count": 1
      },
      "usable": {
        "normalized_weight": {
          "denominator": 1000003,
          "numerator": 1000003
        },
        "period_sum": 1000003,
        "sample_count": 1
      }
    },
    "written_positions": 1
  }
}
```

| Condition / field | Interpretation |
|---|---|
| exit 0, verdict.conversion=ok | Conversion completed |
| nonzero exit | Failure; do not trust an old report left on disk |
| verdict.identity=verified | Identity evidence agrees; not proof of adequate samples |
| unverified | Missing evidence explicitly allowed; not a production default |
| usable_ratio_check / sample_threshold_check / lost_ratio_check | Optional package-policy checks |
| failure_stage, reason | Failure location and diagnosis |
| sampling_adequacy=unknown | No general proof of adequacy; unspecified or satisfied gates cannot establish it |
| sampling_adequacy=insufficient | A configured sufficiency-related check failed |
| throttle fields unknown | Board telemetry still needs separate qualification |

Failures preserve an old profile. Non-path-conflict failures atomically replace failure JSON. Output/report/input alias conflicts and output '-' write neither output. Report write/commit failure can leave the previous report. The profile/report pair is not a crash-atomic transaction.

## 10. Troubleshooting and known limitations

- Always specify aggregation. Max with none/none/none is explicit policy, not validated defaults.
- Thresholds are optional; no failed threshold does not prove adequate sampling.
- Link sampled programs with -Wl,--build-id=sha1; the linker-default follow-up remains open.
- Use packaged runtime/debug pairs; BUILD artifacts can have different identities.
- Avg, zero filling and prev-inst need usable mapping symbols and provable boundaries.
- ARMv7 pseudo-probe compilation has a known crash; pseudo-probe, IP perf.data input and kernel profiles are outside delivery.
- BOLT is planned for RPi5 only and is not provided by the delivered tool package.
- Current board condition, a fresh host provisioning recipe, standalone lit recipe and full consumption of the new FFmpeg example are not verified as detailed above.
- FFmpeg ARMv7 packaging emitted eight nonfatal debugedit DWARF 5 diagnostics per variant. Runtime/debug IDs and readable sections passed for libavcodec/libavutil; complete debugsource/path rewriting is not established. See the [FFmpeg limitations](examples/ffmpeg/README.md#known-limitations).
- Detailed raw evidence is retained by the project team.
