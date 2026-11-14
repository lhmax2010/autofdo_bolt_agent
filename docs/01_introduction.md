# Introduction

Status: first HQ draft, awaiting PM review.

The RPi4 and RPi5 environments used by this project do not provide the branch-stack input expected by the existing llvm-profgen flow. The delivered extension accepts exported instruction-pointer samples and uses ELF file offsets and DWARF information to produce LLVM sample profiles. It does not reconstruct branch traces or claim that sampled counts are execution counts.

The limited delivery consists of nine commits on the Tizen LLVM Gerrit sandbox. It covers user-space AArch64 and little-endian ARMv7 Thumb-2/A32 code. It adds strict text parsing, conservative identity checks, address conversion, profile counting, optional instruction-boundary features, and a machine-readable quality/failure report.

The normal non-incremental release build and fixed output regressions passed. Historical board integration and independent address/average checks are summarized in the [delivery report](03_reports/llvm_profgen_delivery.md). These are functional checks. **Statistical quality equivalence and performance gains have not been validated.**

The call-site policy recommended for the future workflow is explicit: max aggregation, no skid correction, no zero filling, and no head estimate. It is not a statistically validated default; the CLI still requires aggregation to be specified.

The next work is AutoFDO/PGO and BOLT workflows, then skills (SKILL.md plus scripts), then an Agent. Workflow design is under review. BOLT is planned only for RPi5 in that design, and kernel profiling is outside this delivery.

Start with the [host-only demo](04_demo.md), then read the [design summary](02_design/llvm_profgen_ip_mode_design_summary.md). Board collection requires separately approved access and appropriate hardware, cooling and identity checks.
