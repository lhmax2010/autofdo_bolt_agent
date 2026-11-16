# Introduction

RPi4 uses Cortex-A72; RPi5 uses Cortex-A76. Project probes found no usable branch-recording input in the tested Tizen configurations on either board. Hardware cycles sampling was available once the RPi4 PMU configuration was corrected. These observations concern the tested systems, not every possible processor/kernel configuration.

The existing llvm-profgen branch-stack flow cannot consume those instruction-pointer samples directly. The delivered extension accepts strict exported perf text, converts DSO file offsets to ELF addresses, verifies identity and uses DWARF to generate LLVM sample profiles.

```text
Board perf IP sampling
  -> complete text export and build-ID list
  -> host llvm-profgen with packaged runtime/debug ELF
  -> sample profile and quality report
  -> rebuild with -fprofile-sample-use
  -> correctness check and timed comparison
```

Functional validation includes parsing, address conversion, identity, counting, failure contracts, instruction boundaries and host output regression. A manual RPi4 Thumb FFmpeg AutoFDO pilot measured 2.565% lower elapsed time on its ToS test video, with a 95% interval of [-2.859%, -2.256%] and matching output on both declared videos. See the [pilot report](03_reports/m1_ffmpeg_rpi4_thumb_pilot.md). Statistical profile-quality equivalence, optimal defaults and general performance gains beyond that workload have not been validated. The delivery does not claim that sampled counts are execution counts.

## Roadmap

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

Workflow automation is still planned, not implemented; the first measured result came from manually executing its stages. M2a extends AutoFDO to RPi5 before M2b adds instrumented PGO on both boards.

The planned workflow makes the low-level operations repeatable. The skill packages the workflow instructions and scripts for reuse. The later Agent automates package selection and execution through that same interface. The layers complement one another.

Read the [workflow overview](02_design/workflow_design_overview.md), [IP design summary](02_design/llvm_profgen_ip_mode_design_summary.md), [delivery report](03_reports/llvm_profgen_delivery.md) and [host demo](04_demo.md).
