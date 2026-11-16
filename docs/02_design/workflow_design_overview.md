# Optimization workflow design overview

This overview reflects design v0.2. Workflow automation is **Planned; not implemented**. The limited llvm-profgen IP-mode component is delivered, and a manual M1 run has produced the [first measured RPi4 Thumb result](../03_reports/m1_ffmpeg_rpi4_thumb_pilot.md): 2.6% lower elapsed time on one test workload. A successful manual run does not mark the planned command interfaces or recovery engine as implemented.

## Purpose and scope

Turn a Tizen package, a matching board and a repeatable workload into reproducible artifacts and a correctness-checked measured comparison. Initial targets are user-space FFmpeg and GStreamer, ARMv7 on RPi4 and AArch64 on RPi5. Kernel optimization is a separate undecided track. Initial workflows exclude LTO, pseudo-probe and iterative collection from already optimized binaries.

## Build variants

| Variant | Definition |
|---|---|
| Baseline | Package optimization flags plus profiling-friendly DWARF, unique linkage names and explicit SHA-1 build-ID |
| AutoFDO | Baseline flags plus -fprofile-sample-use with a locked profile |
| Instrumented training | Normal optimization flags plus -fprofile-generate (IR instrumentation) |
| Instrumented optimized | Same source/options plus -fprofile-use with merged training data |
| BOLT input | Baseline with -Wl,--emit-relocs and an unstripped runtime ELF; RPi5 only |
| BOLT optimized | Host-rewritten BOLT input, deployed as a separate variant |

These are engineering variant names, not implemented command-line interfaces.

## Stages and contracts

1. Prepare: select package, tool revisions, target image, input checksums and board identity.
2. Build: freeze the complete dependency RPM set and resolved buildconf, then generate runtime and debug packages in fresh roots. Record installed package/header hashes, source/patch/spec identities, source layout and actual compiler/linker arguments.
3. Deploy: extract on the host, copy variant files under /opt/afdo_agent and verify checksums. Every timed decoder must load the intended target libraries; process maps and file SHA/build IDs are checked against its variant manifest.
4. Collect: hardware cycles with build-ID mmap records, full text export and telemetry. Pull and validate complete manifests.
5. Convert: explicit max/none/none/none policy; inspect process exit, conversion verdict, identity and package-selected thresholds. Lock period units before merging profiles.
6. Rebuild: use the locked profile and frozen dependencies; run BASE-r once to verify reproducibility. Compare package lists and compiler/linker argument multisets, removing only declared candidate options. Preserve source paths/flags and retain consumer diagnostics. A build-lock mismatch stops the experiment.
7. Measure: correctness before speed; interleaved rounds, warmup handling, frequency/temperature monitoring and raw results.
8. Report: artifact identities, commands, conditions, estimates and limitations. A failed stage cannot silently resume with different inputs.

The instrumented path replaces sampling/conversion with profraw capture and llvm-profdata merge. Package hooks keep the core independent of codecs or build systems.

## Package profile

```text
packages/<package>/
  package.toml
  build/spec_overlay.patch
  workloads/train.sh
  workloads/bench.sh
  workloads/check.sh
  inputs.toml
```

Declarations include target DSOs, architecture, build hooks, training and test input SHA values, cycles period/frequency, number of runs, a fixed profile period unit, optional quality gates, benchmark metric, warmups, measurement rounds, tolerance and correctness check. Owners supply benchmark and data-collection methods. Configuration uses Python 3.11 or later and standard-library TOML parsing; there is no JSON configuration fallback. Threshold examples are package policies, never built-in proof of sampling adequacy.

## Frozen dependencies and build-lock checks

The first build resolves the dependency union for all variants in an experiment, archives the RPMs with checksums and snapshot IDs, and preserves the resolved buildconf. Later builds use only that set. An archive is called offline-reproducible only after a fresh-root rebuild succeeds. The [FFmpeg example](../../examples/ffmpeg/README.md#building-from-an-archived-dependency-set) gives the tested --skip-conf-repos -R <directory> -D <buildconf> entry.

Record and compare installed package/header-hash lists, source/patch/spec hashes, macros, source path layout, resolved build configuration and compiler/linker argument multisets. Only declared candidate-specific flags may differ. BASE-r checks whether the frozen rebuild reproduces BASE byte for byte; otherwise a newly validated BASE-r is the control and the difference is reported. A different snapshot or incomplete archive cannot silently change one side of a comparison.

## Independent correctness oracle

PLAT, the board's system FFmpeg decoder, provides the per-input oracle: input SHA/segment, I420 caps, thread count, expected frames, bytes and output digest. BASE and every candidate must match it before and after timing. A correctness mismatch fails the experiment. For non-bit-exact packages, the owner must declare tolerances in advance.

Timed rounds use a non-blocking sink, with the same caps, exit-status and end-of-stream checks; hashing remains outside timing. The result states which inputs the oracle covered rather than claiming complete decoder correctness.

## Measurement

Lock the candidate/control pairs, inputs, oracle, warmups, block count N, balanced AB/BA order and seed, tolerance and analysis version before timing. A block contains one run of each compared variant. The design's proposed N budget uses at least ten BASE pilot rounds:

N = min(40, max(10, ceil(2 * (1.96 * 1.2533 * CV / 0.005)^2))).

This is a budget, not a power guarantee. The first manual pilot instead fixed N=15 in advance; it did not select N from interim effects. No blocks are added after timing begins.

For positive, lower-is-better time, compute paired r_i = ln(T_candidate,i / T_control,i). Report exp(mean r) - 1, with a 95% block-bootstrap interval from 20000 resamples and a fixed seed. Report a t interval and ratio of medians as secondary statistics. With epsilon (normally 1%):

| Verdict | Rule |
|---|---|
| faster | CI upper bound < -epsilon |
| slower | CI lower bound > +epsilon |
| equivalent | Entire CI strictly inside (-epsilon, +epsilon) |
| inconclusive | All other cases |

Telemetry-flagged blocks stay in the primary analysis; show clean-block sensitivity separately. Missing blocks make the verdict inconclusive (incomplete). If flagged or missing blocks exceed 20% of N, or their rate differs clearly between variants, cap the verdict at inconclusive. A pre-listed technical failure with no measurement may be retried once as a whole block, retaining the original attempt; correctness failure is not a retry opportunity. With multiple candidates, name a primary comparison and state that no multiple-comparison correction is applied.

Pin the workload to its declared CPU and the one-second telemetry sampler to another CPU. Monitor available scaling/current frequency, all thermal zones, undervoltage alarm and monotonic timestamps. Default gates are start temperature <=60 C, in-run maximum <80 C, fixed frequency in every reading, zero undervoltage alarm and no sampling gap >2 seconds. Restore governors on exit. Compare median cycles/task-clock effective frequencies; a difference above 0.5% flags confounding risk. Unreadable throttle history stays unknown: say "no anomaly observed in available telemetry", not "not throttled". The planned formal runner also measures sampler overhead; that overhead was not independently measured in the manual pilot.

The manual result is evidence for its declared workload, not implementation of the planned reusable measurement and recovery engine. A broader test/conformance set remains planned.

## BOLT on RPi5

Build host llvm-bolt/perf2bolt separately with LLVM_ENABLE_PROJECTS=bolt and LLVM_TARGETS_TO_BUILD="X86;AArch64". The Tizen LLVM spec does not build these tools. Input must retain relocations (-Wl,--emit-relocs) and runtime symbols; verify packaged identities first.

A planned perfscript2bolt converter will consume the board's complete text export without host perf, validate the target build-ID and convert dsoff to ELF addresses using the same rules as profgen. It will write BOLT pre-aggregated basic-sample input (E cycles and S <address> <count> records), then run perf2bolt --pa -ba -p <aggregated-input> <ELF> -o <fdata>. This converter is Not implemented. The downstream llvm-bolt rewrite option set will be fixed during M4 trials, followed by correctness and timed comparison.

Basic samples provide hotness without branch edges, so gains can be small. AArch64 non-relocation mode is not fully supported; Tizen shared-library rewriting is Not verified. Keep rewritten output separate and validate layout and relocations.

## Milestones and acceptance

| Component / milestone | Sequence and acceptance | Status |
|---|---|---|
| llvm-profgen IP mode | User-space DWARF IP on AArch64 and ARMv7 Thumb-2/A32; functional release checks passed | Delivered (limited scope) |
| M1 | FFmpeg on RPi4: reproducible collection, identity checks, conversion, rebuild, correctness and timed comparison | First measured result: FFmpeg AutoFDO on RPi4 Thumb, 2.6% faster (manual run of the workflow steps); workflow automation in progress |
| M2a | FFmpeg AutoFDO on RPi5 (AArch64), with board-specific telemetry and the same artifact/result contracts | Planned; not implemented |
| M2b | Instrumented PGO for FFmpeg on RPi4 and RPi5, after M2a | Planned; not implemented |
| M3 | GStreamer package profiles and multi-library collection/rebuild | Planned / Not implemented |
| M4 | BOLT on RPi5 only; relocation/identity checks, host conversion and correctness/timing | Planned / Not implemented |
| M5 Skill | Reusable SKILL.md instructions plus scripts that run workflow stages and interpret results | Planned / Not implemented |
| Agent | After the skill: select packages, run the workflow through the skill, report results; builds on both layers | Planned / Not implemented |
| Kernel | Separate track; method to be decided; current llvm-profgen delivery has no kernel support | Planned / Not implemented |

Package owners provide benchmark and data-collection methods through package profiles.

M1 acceptance requires a resumable end-to-end FFmpeg run, deterministic manifests, no silent identity mismatch, valid sample consumption, matching decode checksum and a measured result with uncertainty. M2a repeats these contracts for AutoFDO on RPi5; M2b then adds IR-instrumented PGO on both boards. M3 extends the same contracts across the package/library set. M4 adds BOLT-specific relocation and rewrite validation. M5 follows a stable workflow interface after M2a and must run and explain these stages through the same scripts without duplicating their logic. The Agent must preserve the skill/workflow contracts, record its choices and surface failures rather than weakening checks.
