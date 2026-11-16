# FFmpeg AutoFDO pilot on Raspberry Pi 4 Thumb

## What was tested

FFmpeg 8.0.1 H.264 software decoding was tested on a Raspberry Pi 4 Model B Rev 1.5 running 32-bit Tizen, with ARMv7 Thumb-2 C code. Decoding used one thread through GStreamer's avdec_h264, pinned to CPU3. The image was tizen-unified-toolchain_20261104.160709 and the kernel was 6.12.80-arm-rpi4-v7l. The target compiler was Clang 22.1.8.

This was a manual run of the workflow steps. Workflow automation remains in progress; no automated workflow command is delivered by this result.

| Role | Video | Segment and encoding | SHA-256 |
|---|---|---|---|
| Training | Big Buck Bunny | 300-360 seconds, 1280x720, H.264 High, 30 fps | b5e116b9d01cec8e7f697041c53575d36bd96a5928e40faa69e731f9ae2d00a4 |
| Test | Tears of Steel | 300-360 seconds, 1280x720, H.264 High, 30 fps | 280fbd41f8772491ebe784aa19a3caed3bb1e8b2e64daef1d2a5a284d1f38ad1 |

The videos have different content. Both are Blender Foundation open movies; source and license links and the segment recipe are in the [media instructions](../../README.md#training-and-test-media).

The steps were:

1. Reuse the packaged baseline libraries built with profiling-friendly DWARF, unique internal linkage names and SHA-1 build IDs.
2. Collect three independent training runs with hardware cycles, --buildid-mmap and period 1000003. Export complete perf text and build-ID lists.
3. Convert each run for libavcodec and libavutil with the released llvm-profgen. The explicit conservative strategy was --ip-aggregation=max --ip-skid=none --ip-zero-fill=none --ip-head-samples=none, with period weighting and --ip-period-unit=1000003. All six conversions reported conversion=ok and identity=verified.
4. Sum the three profiles per library, verify that the two libraries have no common top-level profile keys, then merge them into one locked package profile. Its SHA-256 was 61f03b59262e3ce7ce758219d65848a33b5a0549131c362a6769ad10386f2cf2.
5. Rebuild with -fprofile-sample-use, check correctness, and measure the baseline and optimized libraries on the test video.

## How the comparison was kept fair

All builds used the same frozen dependency set: 108 installed package records, including RPM header hashes, were identical across the original baseline, its repeat build, the AutoFDO build and two command-recording builds. The source, patch, spec and relative source layout were held fixed.

Each command-recording build contained 698 compile/link commands. Their argument multisets were identical after removing only the sample-profile option; 627 AutoFDO commands carried that option. The profile inside the build environment matched the locked SHA. The .text sections of both target libraries changed, and each packaged runtime/debug pair had matching build IDs.

Rebuilding the baseline from the frozen set produced byte-identical copies of all six FFmpeg runtime libraries, so the original baseline remained the control. The command-recording builds produced the same artifacts as their corresponding measured builds.

Every timed decoder process had its loaded libavcodec and libavutil paths checked in process maps. The deployed library checksums matched the intended variant. Libraries were copied into separate directories and selected with LD_LIBRARY_PATH; no system libraries or installed packages were replaced.

## Correctness

PLAT means the board's system FFmpeg libraries, used through the same GStreamer decoder as an independent reference. PLAT, BASE and AFDO decoded both videos to identical I420 output: 1800 frames and 2488320000 bytes per video, at 1280x720, 30/1 fps, progressive scan and square pixels.

| Video | Decoded-output SHA-256 |
|---|---|
| Big Buck Bunny | 3a4c3820c576697edd4ca34f3532c8af8ffaf04687955c5d6b35215b9b06c814 |
| Tears of Steel | 4c2610c37b7790240c9158277981ed9c3ac81399e3e9df554ffebb2d2ff80c4e |

Checks were performed before and after timing. They establish equality on these two workloads, not complete decoder conformance. Timed runs used fakesink sync=false; output hashing was outside the timed region.

## Measurement method

The plan fixed 15 paired blocks before timing, after two discarded warm-up blocks. Each block contained one BASE and one AFDO run. A=BASE and B=AFDO; a fixed seed (20261116) produced eight AB and seven BA blocks. No formal rounds were added or replaced.

CPU3 ran the decoder; CPU0 ran the telemetry observer. The governor was performance with a 1.5 GHz setting. Runs waited for a start temperature at or below 60 C, with a fixed five-second cool-down. One-second telemetry recorded temperature, scaling and reported current frequency, undervoltage alarm and monotonic timestamps. Complete readings stayed at 1.5 GHz with no undervoltage alarm; the highest observed temperature was 63.296 C.

For each block, r = ln(AFDO seconds / BASE seconds). The estimate is exp(mean r) - 1; its interval is a paired-block percentile bootstrap with 20000 resamples and seed 2026111601. The faster threshold was a 95% interval entirely below -1%. A t interval and ratio of medians were secondary statistics.

## Results

| Block | Order | BASE seconds | AFDO seconds | Telemetry flag |
|---|---|---:|---:|---|
| 1 | BA | 30.839 | 30.332 | None |
| 2 | BA | 30.997 | 30.200 | None |
| 3 | BA | 30.884 | 30.021 | None |
| 4 | AB | 30.755 | 30.060 | None |
| 5 | AB | 31.057 | 29.978 | None |
| 6 | AB | 30.787 | 29.922 | None |
| 7 | AB | 30.728 | 29.944 | None |
| 8 | AB | 30.740 | 30.199 | None |
| 9 | BA | 30.950 | 30.002 | None |
| 10 | BA | 30.715 | 29.882 | None |
| 11 | AB | 30.753 | 30.005 | Incomplete final telemetry line |
| 12 | AB | 31.009 | 29.934 | None |
| 13 | BA | 30.861 | 30.090 | None |
| 14 | BA | 30.947 | 30.001 | Incomplete final telemetry line |
| 15 | AB | 30.894 | 30.475 | None |

| Statistic | Result |
|---|---|
| Estimate, AFDO relative to BASE | -2.565% elapsed time |
| Paired-block bootstrap 95% CI | [-2.859%, -2.256%] |
| Verdict | **faster** |
| Secondary t interval | [-2.906%, -2.223%] |
| Secondary ratio of medians minus one | -2.774% |
| Baseline run-to-run coefficient of variation | 0.37% |
| Clean-block sensitivity, 13 blocks | -2.537%; 95% CI [-2.868%, -2.194%]; faster |
| Median effective CPU frequency, BASE / AFDO | 1499.804 / 1499.801 MHz |

The two variants' effective frequencies were effectively equal: the cycles/task-clock median differed by -0.000220%, well below the 0.5% confounding-risk threshold. Blocks 11 and 14 had incomplete final telemetry lines on the AFDO run. Both remained in the primary analysis and were excluded only in the separately reported sensitivity analysis. No missing or technically retried formal blocks were recorded.

Here, "2.6% faster" is shorthand for approximately 2.6% lower elapsed time under this test, not a claim about all workloads or peak throughput.

## Interpretation

About 30% of libavcodec's sampled cycles had source-line witnesses in handwritten assembly (34637 of 114448 target samples, 30.264%). AutoFDO's C/C++ sample-profile optimization does not rewrite those assembly routines. This limits the part of the workload directly addressed by the compiler optimization; it is not a measured upper bound on possible speedup.

libavutil had only 325 target samples across all three training runs, of which 239 were usable. Its sparse sampling should not be interpreted as evidence of a separate library-level speedup. Profile conversion success and verified identity do not establish sampling adequacy.

## Limitations and verification

- One board, one test video and single-threaded decoding. No A32 or AArch64 performance result is established here.
- Tears of Steel had been used during earlier tool development; it was not a fresh holdout. Broader input and conformance coverage remains necessary.
- Firmware throttle history was not readable on this board. Available telemetry showed no anomaly in complete readings; this does not prove that throttling never occurred.
- The telemetry observer's overhead was not independently measured. Both variants used the same observer. Two truncated telemetry records remain flagged.
- The explicit conservative profile policy is not a statistical validation of llvm-profgen defaults. Statistical profile-quality equivalence remains unvalidated.
- Results were independently re-checked from the recorded evidence by the project team: profile generation and merging reproduced the same bytes, build identities and command comparisons agreed, and statistics and oracle records agreed. Missing early command transcripts and unavailable historical firmware state could not be reconstructed.

Detailed raw evidence is retained by the project team. See the [FFmpeg build example](../../examples/ffmpeg/README.md) for frozen-dependency rebuilding and identity checks, and the [workflow plan](../02_design/workflow_design_overview.md) for automation still to be implemented.
