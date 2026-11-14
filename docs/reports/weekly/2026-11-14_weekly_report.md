# Weekly Report: AutoFDO / PGO / BOLT Optimization for Tizen

Week of Nov 9-14, 2026

## Summary

This week we completed the first stage of our plan: the LLVM profile generator (llvm-profgen) can now build optimization profiles on Raspberry Pi 4 and Raspberry Pi 5 boards running Tizen, even though neither board can record branch history. The change is built as a normal Tizen LLVM package, verified, and published on a Tizen Gerrit sandbox branch, together with a self-contained delivery package (build guide, board setup guide and a demonstration).

We also completed the design of the next stage, an end-to-end optimization workflow, and started its first milestone: optimizing FFmpeg on Raspberry Pi 4. The first FFmpeg board builds found a small defect in our example build script, which we will fix next week. Actual speed-ups have not been measured yet; that is the goal of the first milestone.

## Background

Profile-guided optimization lets the compiler arrange and optimize code based on how a program actually runs. It typically improves performance of large, branch-heavy code such as video codecs. There are three common techniques:

- **Instrumented PGO** builds a special version of the program that counts every branch, runs it on a training workload, then rebuilds with the counts. It is accurate, but the instrumented build is slow and must be run separately on the device.
- **AutoFDO (sample-based PGO)** samples the normal program with the CPU's performance counters while it runs, then converts the samples into a profile. It needs no special build, so profiles can be collected from realistic runs.
- **BOLT** rewrites an already-linked binary, reordering functions and code blocks for better instruction-cache use.

The standard AutoFDO tooling expects the CPU to record branch history (for example Intel LBR or Arm BRBE). Our target boards, Raspberry Pi 4 (Cortex-A72, 32-bit Tizen) and Raspberry Pi 5 (Cortex-A76, 64-bit Tizen), cannot record branch history; our board probes confirmed this. They can only sample the address of the instruction being executed. The existing llvm-profgen could not use such samples, so we had to extend it before any AutoFDO work on Tizen could start.

## Our plan

We build the capability in layers, each one using the layer before it: first a tool that can turn board samples into profiles, then a workflow that runs the whole optimization loop for a package, then a reusable skill package that runs and interprets the workflow, and finally an automated optimization agent.

**llvm-profgen → Workflow (M1–M4) → Skill (M5) → Agent**, with kernel optimization as a separate track.

| Stage | Content | Status |
| --- | --- | --- |
| 1. llvm-profgen | Instruction-sample mode for AutoFDO | **Delivered** |
| 2. Workflow, M1 | FFmpeg on Raspberry Pi 4 | **In progress** |
| 2. Workflow, M2 | FFmpeg on Raspberry Pi 5, plus instrumented PGO on both boards | Planned |
| 2. Workflow, M3 | GStreamer (packages with several libraries) | Planned |
| 2. Workflow, M4 | BOLT post-link optimization on Raspberry Pi 5 | Planned |
| 3. Skill, M5 | Reusable instructions and scripts that run the workflow and interpret its results | Planned |
| 4. Agent | Automated optimization agent built on the skill and the workflow | Planned |
| Separate track | Kernel optimization | Method to be decided |

BOLT is limited to the 64-bit board because it does not support 32-bit Arm. Kernel optimization is separate because the current tool handles user-space code only.

## Completed: instruction-sample mode for llvm-profgen

We added a new input mode to llvm-profgen that builds a standard LLVM sample profile from instruction-address samples alone. It covers user-space programs and libraries on 64-bit Arm (Raspberry Pi 5) and 32-bit Arm in both Thumb-2 and A32 instruction sets (Raspberry Pi 4). The change is nine patches to the tool, its tests and its documentation; nothing else in LLVM is touched.

### How it works

1. On the board, Linux perf samples the hardware cycles counter while the workload runs, and records which library each sample falls in, with that library's build ID.
2. The samples are exported as text on the board and copied to the build host.
3. On the host, llvm-profgen converts each sample's position inside the library file into a code address, then uses the debug information of the same build to find the source line, including lines inlined from other functions.
4. The tool writes the profile in the format the compiler reads, plus a quality report in JSON.
5. The package is rebuilt with the profile (`-fprofile-sample-use`).

### Safety features

- **Identity checks.** The tool compares build IDs from the board with the binaries on the host and refuses to build a profile for a different build. A profile for the wrong binary would silently mis-optimize code.
- **Strict input checking.** Malformed or incomplete input stops the tool with a clear reason instead of producing a partial profile.
- **Quality report.** Records how many samples were found, how many could be used, why the rest were excluded (kernel code, other libraries, unknown code, lost samples), and whether optional minimum thresholds were met.
- **Safe failure.** On any error, an existing profile is left untouched and the report states where and why the run failed.

### Conversion settings

Instruction samples can be combined in several ways, for example how to merge samples that map to the same source line, or whether to correct for the CPU reporting a slightly later instruction than the one that triggered the sample. We use the most conservative choice for each: no estimation and no correction. Which settings give the best real speed-up will be decided from actual measurements in the workflow, rather than from statistical analysis of the profiles alone. We prepared a detailed statistical evaluation method that compares sample-based profiles with exact reference profiles; it remains available if a formal quality comparison is needed later.

### How we verified it

- **Normal package build.** We built the Tizen LLVM package from a clean state with the unchanged official build recipe (about 80 minutes). The new tool comes out of the regular package.
- **No change to existing behavior.** We ran the tool's existing branch-history input paths with the original tool and the new one and compared every output. They are identical, so current users are not affected.
- **Same results as during development.** Real FFmpeg captures from Raspberry Pi 4 and the synthetic test inputs gave byte-identical profiles from the released tool and from the development build that we validated in detail.
- **Board checks done earlier.** On Raspberry Pi 4 we confirmed correct handling of processes that fork or start a different program, samples that fall in kernel code (excluded), samples in unknown code, lost samples during heavy load, and Thumb-2 code. Independent calculations agreed with the tool in each case.
- **Automated tests.** The tool's own test suite passes with the new tests included.

## Completed: source publication and delivery package

**Source.** The nine patches are on the Tizen Gerrit sandbox branch `sandbox/lhmax2025/afdo_profgen` of `platform/upstream/llvm`, exactly as built and verified. They sit on the accepted Tizen LLVM 22.1.8 baseline. The current development branch `tizen_base` has three newer commits that only change how the LLVM package itself is built; our patches also apply cleanly on top of them, so moving forward later is straightforward. A fresh checkout of the sandbox branch was compared file by file with the verified source and matches.

**Delivery package.** A self-contained documentation and demo package lets anyone reproduce the work without access to our internal systems:

- an introduction and the complete roadmap;
- a step-by-step guide: prerequisites, getting the source from Gerrit, building with GBS, extracting and checking the tool;
- a demonstration that runs on the build host without a board and shows the expected output;
- a board setup guide for Raspberry Pi 4 and 5 (image, kernel requirement, deploying perf, checking the hardware counter, temperature and CPU frequency);
- a manual end-to-end AutoFDO example for FFmpeg;
- a guide to reading the quality report, a troubleshooting section and a list of known limitations;
- a summary of the tool design and of the planned workflow.

## Completed: optimization workflow design

We designed a workflow that takes a Tizen package, a board and a workload, and produces an optimized build plus a measured, correctness-checked comparison with the original. The design is at version 0.1 and goes to design review next week.

### Stages

1. **Preflight:** check the board's identity, the hardware cycles counter, cooling, CPU frequency settings and the tool versions.
2. **Build** the baseline package with profiling-friendly debug information and a build ID on every library.
3. **Deploy** it to a private directory on the board, without touching system libraries.
4. **Collect** samples while a training workload runs, and copy them back with checksums.
5. **Convert** them to a profile with llvm-profgen and check the quality report against the package's minimum requirements.
6. **Rebuild** the package with the profile.
7. **Measure** the baseline and optimized builds on a different test workload, alternating between them over many rounds.
8. **Report** the result, all identities and the conditions of the run.

Instrumented PGO uses the same stages with an instrumented training build. BOLT on Raspberry Pi 5 adds a step that rewrites the binary after linking.

### Design choices

- **Package owners provide their own benchmarks.** The workflow core contains no FFmpeg-, GStreamer- or kernel-specific logic. Each package has a small profile: which libraries to optimize, the training workload, the measurement benchmark and its metric, the correctness check and the quality thresholds. We write the first versions; the FFmpeg, GStreamer and kernel owners can then supply more accurate workloads and measurements.
- **Fair comparison.** The baseline and optimized builds differ only in the profile. Training and measurement use different input videos, so the result is not inflated by tuning to one input.
- **Correctness before speed.** Every measurement round checks the output (for example the checksum of the decoded video) against the baseline. A faster but wrong build is never reported as a gain.
- **Clear verdict.** The result is reported as faster, slower or inconclusive, with a 95% confidence interval. The number of rounds is fixed in advance from the measured run-to-run variation, between 10 and 40.
- **Controlled conditions.** Each round starts only when the board is cool enough and running at a fixed CPU frequency; rounds that violate this are repeated or excluded and reported.
- **Reproducibility.** Every build, library, profile and tool is recorded by checksum and build ID. Exact repository snapshots are pinned and the downloaded dependencies archived, because public Tizen snapshots are removed after a few weeks.
- **BOLT without branch history.** BOLT normally needs branch records. On Raspberry Pi 5 we will convert the same instruction samples into BOLT's simple input format with a small converter, so no perf installation on the build host is needed. Gains may be smaller than with branch records.

## In progress: FFmpeg board builds and RPi4 counter support

### FFmpeg builds for the boards

The first step of milestone M1 is a reproducible FFmpeg build for the boards with profiling options enabled. We prepared a small change to the FFmpeg package build script. It keeps the platform's normal optimization flags and adds richer debug information for profiling, unique names for file-local functions, a build ID on every library, Clang as the compiler, and an option to choose the Thumb-2 or A32 instruction set on 32-bit Arm.

The Raspberry Pi 4 board runs Tizen image `tizen-unified-toolchain_20261104.160709`. Its package repository has already been removed from the public server, so we built against the closest available repositories, which provide the same Clang 22.1.8 compiler. Two 32-bit builds were attempted:

- **A32 build:** stopped while configuring FFmpeg. Our build-script change appends the instruction-set option without a separating space, so FFmpeg receives two options joined into one and rejects it. The fix is a one-character change. The log already showed the expected profiling flags, compiler and build-ID option.
- **Thumb-2 build:** interrupted by a failure of the host-side process that monitors long builds, not by a build error. It will be rerun.

The 64-bit build for Raspberry Pi 5 starts once the board's current image is confirmed on Monday. All packages downloaded for the 32-bit builds are archived so the build can be repeated after the public snapshot disappears.

### Hardware cycles counter on Raspberry Pi 4

On 32-bit Tizen for Raspberry Pi 4, the kernel did not enable the Cortex-A72 performance counter driver, so AutoFDO sampling was impossible. One line in the kernel configuration (`CONFIG_ARM_PMUV3=y` in `tizen_bcm2711_defconfig`) fixes this; no other configuration value changes. The change is on the kernel sandbox branch `sandbox/lhmax2025/kernel_optimization` (commit `0fac5de6`) and is not yet in the main Tizen kernel branches. Images built without it cannot run AutoFDO collection on Raspberry Pi 4.

## Open technical issues

| Issue | Effect | How we handle it |
| --- | --- | --- |
| Missing space in the FFmpeg build-script change | The A32 build stops at configure; the same script is in the FFmpeg example of the delivery package | Fix the script, complete the builds, update the example |
| Public Tizen package snapshots are removed after a few weeks | A build cannot be repeated later from the same repositories; this already happened for the board image | Pin exact snapshot IDs and archive every downloaded dependency with the build; part of the workflow design |
| Hardware counter kernel change only on a sandbox branch | Other Raspberry Pi 4 images may lack the counter needed for sampling | Decide whether to propose the one-line change for the main Tizen kernel branch |
| Conversion settings chosen conservatively, not tuned | The profile may not yet give the best possible speed-up | Compare settings by real speed in the workflow |
| No speed-up measured yet | No performance claim can be made | First baseline vs AutoFDO comparison is the goal of milestone M1 |
| Build IDs are not yet generated by default in the Tizen toolchain settings | Programs to be sampled must add the build-ID link option explicitly | Our build-script changes add it; follow up with the platform toolchain |

## Next steps

1. **FFmpeg board builds:** fix the build-script change, complete the Thumb-2, A32 and 64-bit builds, and confirm that every library carries a matching build ID in its runtime and debug packages. Then update the FFmpeg example in the delivery package.
2. **Workflow design:** review version 0.1 and publish version 0.2, adding the snapshot pinning and dependency archiving rules.
3. **Milestone M1:** run FFmpeg AutoFDO end to end on Raspberry Pi 4: collect samples during H.264 decoding of a training video, build the profile, rebuild FFmpeg, and measure decoding time on a different test video against the baseline. This gives our first measured result.
4. **Kernel counter support:** decide how to bring the Raspberry Pi 4 performance-counter configuration into the main Tizen kernel branch.

## Reference: source locations and versions

| Item | Value |
| --- | --- |
| LLVM Gerrit project and branch | `platform/upstream/llvm`, `sandbox/lhmax2025/afdo_profgen` |
| Branch tip | `c8942ae1b53099a78a97dca2b64427af6e58432b` |
| Baseline (accepted Tizen LLVM 22.1.8) | `f999bd406c0a70fe8107aa992164fe6945c5d46a` |
| Released llvm-profgen checksum (SHA-256) | `67ad21faba787d276a80673c1f324f7c0591d28d76bd37a8bd57de0d86426be6` |
| Package repositories used | `tizen-base-toolchain_20261030.120529`, `tizen-unified-toolchain_20261104.125239` |
| Target compiler | Clang 22.1.8 |
| FFmpeg source | `platform/upstream/ffmpeg` at `5fe76358` (FFmpeg 8.0.1) |
| Kernel counter change | `platform/kernel/linux-rpi`, `sandbox/lhmax2025/kernel_optimization`, commit `0fac5de6` |
| Boards | Raspberry Pi 4 (Cortex-A72, 32-bit Tizen), Raspberry Pi 5 (Cortex-A76, 64-bit Tizen) |
