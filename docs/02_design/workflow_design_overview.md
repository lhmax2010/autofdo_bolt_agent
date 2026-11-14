# Optimization workflow design overview

All workflow components below are Planned / Not implemented. Only the limited llvm-profgen IP-mode component is delivered. This document describes the complete implementation plan.

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
2. Build: package hook generates runtime and debug packages. Record packaged ELF SHA/build-ID/ISA. Check compiler options in actual commands.
3. Deploy: extract on the host, copy variant files under /opt/afdo_agent, verify checksums and runtime maps.
4. Collect: hardware cycles with build-ID mmap records, full text export and telemetry. Pull and validate complete manifests.
5. Convert: explicit max/none/none/none policy; inspect process exit, conversion verdict, identity and package-selected thresholds. Lock period units before merging profiles.
6. Rebuild: use the locked profile, preserve source paths/flags and retain consumer diagnostics.
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

Declarations include target DSOs, architecture, build hooks, training and test input SHA values, cycles period/frequency, number of runs, a fixed profile period unit, optional quality gates, benchmark metric, warmups, measurement rounds, tolerance and correctness check. Owners supply benchmark and data-collection methods. Initial configuration uses Python standard-library TOML support when available, with JSON as a compatibility alternative. Threshold examples are package policies, never built-in proof of sampling adequacy.

## Measurement

Plan at least ten pilot baseline rounds, then fix the round count:
N = min(40, max(10, ceil(2 * (1.96 * 1.2533 * CV / 0.005)^2))).
CV is estimated from the pilot. Interleave variant rounds, remove declared warmups and preserve raw telemetry and correctness results. Do not add rounds after examining a favorable result.

For lower-is-better decode time, report median relative difference and a bootstrap 95% interval. With package tolerance epsilon (proposed default 1%), an interval wholly below -epsilon supports faster, wholly above +epsilon supports slower, otherwise the result is inconclusive. Frequency/throttle uncertainty must be reported; different images or thermal conditions cannot be silently pooled. Performance gains not yet validated.

The manual example is a functional starting point, not implementation or validation of this measurement engine.

## BOLT on RPi5

Build host llvm-bolt/perf2bolt separately with LLVM_ENABLE_PROJECTS=bolt and LLVM_TARGETS_TO_BUILD="X86;AArch64". The Tizen LLVM spec does not build these tools. Input must retain relocations (-Wl,--emit-relocs) and runtime symbols; verify packaged identities first.

A planned perfscript2bolt converter will consume the board's complete text export without host perf, validate the target build-ID and convert dsoff to ELF addresses using the same rules as profgen. It will write BOLT pre-aggregated basic-sample input (E cycles and S <address> <count> records), then run perf2bolt --pa -ba -p <aggregated-input> <ELF> -o <fdata>. This converter is Not implemented. The downstream llvm-bolt rewrite option set will be fixed during M4 trials, followed by correctness and timed comparison.

Basic samples provide hotness without branch edges, so gains can be small. AArch64 non-relocation mode is not fully supported; Tizen shared-library rewriting is Not verified. Keep rewritten output separate and validate layout and relocations.

## Milestones and acceptance

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

M1 acceptance requires a resumable end-to-end FFmpeg run, deterministic manifests, no silent identity mismatch, valid sample consumption, matching decode checksum and a measured result with uncertainty. M2 repeats these contracts on RPi5 and on both instrumented paths. M3 extends the same contracts across the package/library set. M4 adds BOLT-specific relocation and rewrite validation. M5 must run and explain these stages through the same scripts without duplicating their logic. The Agent must preserve the skill/workflow contracts, record its choices and surface failures rather than weakening checks.
