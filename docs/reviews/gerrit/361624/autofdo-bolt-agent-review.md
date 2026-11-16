# Review of Gerrit change 361624 (platform/upstream/llvm) from the AutoFDO / BOLT workflow's point of view

| Item | Content |
|---|---|
| Change | 361624, patch set 1, commit `da885208aeb5` "packaging: split tool subpackages into a standalone llvm-tools-subpkgs spec"; parent `61ef5d31` |
| Reviewed as | A user of the tool packages: the AutoFDO / instrumented PGO / BOLT workflow for Tizen packages (FFmpeg, GStreamer first; Linux kernel as a separate track) on Raspberry Pi 4 (armv7l, Thumb-2/A32) and Raspberry Pi 5 (aarch64), using the enhanced llvm-profgen on `sandbox/lhmax2025/afdo_profgen` |
| Material | The change's diff; the complete `llvm.spec` and `llvm-tools-subpkgs.spec` at `da885208` and `61ef5d31`; BOLT, Clang and LLD sources at `da885208`; read-only checks in existing Tizen build roots (package lists, RPM macros, `llvm-devel` file lists). 361624 itself was not built. The suggested follow-up patch in section 7 was applied on top of it and `llvm-tools-subpkgs.spec` was built for x86_64 with GBS in the normal Tizen build environment (section 7.2). |
| Revision | 4 (final): facts checked and co-reviewed by two further reviewers; section 7 now carries a complete follow-up patch, reviewed and verified by an x86_64 build |
| Verdict | **Acceptable for our workflow with changes.** The standalone `bolt` package is useful and in the right place for us. Seven items should change or be clarified before merge (section 5); a verified patch for most of them is in section 7. None blocks the AutoFDO part of our workflow. |

## 0. How the workflow uses the toolchain

All profile processing and binary rewriting happen on the **x86_64 build host**; the boards only run the workload and record samples.

1. Build the target package (GBS, clang 22) with profiling-friendly debug info and a linker build ID.
2. On the board, `perf record -e cycles` samples the workload; `perf script` exports text. The boards have no branch-record hardware, so every profile comes from instruction-address samples.
3. On the host, `llvm-profgen --ip-samples` (our enhancement) converts the export into a sample profile; `llvm-profdata` merges profiles.
4. The package is rebuilt with `-fprofile-sample-use` (AutoFDO) or `-fprofile-use` (instrumented PGO).
5. BOLT (RPi5 only): the host converts the same board samples into BOLT's pre-aggregated format, then runs `perf2bolt --pa -ba` and `llvm-bolt` on the aarch64 binary.

Host tools are extracted from the Tizen x86_64 RPMs into a private directory and identified by SHA-256; nothing is installed on the boards except files copied into a private directory. The host architecture does not limit the architecture of the ELF files processed.

## 1. Tools needed, architecture and package

| Tool | Needed on | Purpose | Package after 361624 | Status |
|---|---|---|---|---|
| `llvm-profgen` (with our IP mode) | x86_64 host | Sample profile from board samples | `llvm` (x86_64) | OK. Already in `llvm` in the parent commit (`/usr/bin/llvm-profgen`); 361624 does not change this. Our enhancement is not part of 361624 (section 2). |
| `llvm-profdata` | x86_64 host | Merge sample profiles and `.profraw` | `llvm` (x86_64) | OK |
| `llvm-readelf`, `llvm-objdump`, `llvm-dwarfdump`, `llvm-objcopy` | x86_64 host | Identity, section, debug-info checks | `llvm` (x86_64) | OK, unchanged |
| `libLLVM.so.22.1` | x86_64 host (for `bolt`); boards (Tizen `perf` links it) | Runtime library | `libllvm` | OK; pinning in section 4 |
| `clang` with `-fprofile-sample-use`, `-fprofile-generate/-use` | Build root | Consuming and instrumented builds | `clang` | OK, unchanged |
| compiler-rt profile runtime (`libclang_rt.profile-*.a`) | Build root, per target architecture | Linking `-fprofile-generate` builds | `compiler-rt` | File list unchanged by 361624; please confirm the armv7l and aarch64 archives are in the final packages |
| `llvm-bolt`, `perf2bolt`, `merge-fdata` | **x86_64 host only** | BOLT for RPi5 aarch64 binaries | new `bolt` (x86_64) | Right package. The x86_64 LLVM is built with `X86;ARM;AArch64;BPF`; BOLT's default targets (supported targets ∩ installed LLVM targets) therefore include AArch64. We ask only for an explicit per-architecture setting and a check (section 5, item 2). |
| `llvm-bolt-heatmap`, `llvm-bat-dump`, `llvm-boltdiff`, `llvm-bolt-binary-analysis` | x86_64 host, optional | Diagnostics | `bolt` (x86_64) | Fine |
| `libbolt_rt_instr.a` for **aarch64** | x86_64 host, as input to `llvm-bolt -instrument` | Optional instrumentation of RPi5 binaries (exact edge counts without branch records); not needed for the sample-based path | `bolt` (aarch64), planned by the spec | Final artifact to be verified. An x86_64 `llvm-bolt` finds its own x86_64 runtime by default, so instrumenting aarch64 binaries needs `-runtime-instrumentation-lib=<aarch64 archive>` (section 4.3) |
| `perf` | Boards (armv7l, aarch64) | Sampling | Not part of this change | Must remain available (section 4.2) |
| `llvm-profgen`, `llvm-profdata`, BOLT tools on armv7l or aarch64 | Not needed | — | — | We never run them on the boards |

Workflow note (no request to HQ): unlike the x86_64 `llvm` tools we use today, which are linked statically (`LLVM_LINK_LLVM_DYLIB=OFF` on x86_64), the standalone `bolt` links `libLLVM.so`. Our BOLT preflight will extract `bolt` together with `libllvm` from the same build and record both SHAs.

Kernel track: the current tools add no kernel requirement (llvm-profgen does not produce kernel profiles; upstream kernel BOLT support is x86-only).

## 2. llvm-profgen in the main `llvm` package

**Effect of 361624:** none for llvm-profgen. It ships in `llvm` in the parent commit and still does; the commit message's "moves into the main llvm package" refers to an interim split in earlier patch sets of this series. Our delivery path is unchanged: extract the tool from the x86_64 `llvm` RPM.

**Cost:** any llvm-profgen change needs a full LLVM package build. Our clean build of the accepted baseline took 79 min 40 s on our build host; with clang bootstrap, ThinLTO and the ML inliner on the current development branch, it is expected to take several hours.

**Standalone tools spec instead?** Feasible in principle, since llvm-profgen uses only libraries exported by `libLLVM.so`, but it would need:
- the tool disabled in the main build, because `LLVMExports.cmake` exports it as an imported executable and checks the file exists;
- provider version pinning (section 4.1);
- separate handling of its lit tests, which run naturally in the main tree.

How long a standalone build would take was not measured.

**Recommendation:** keep llvm-profgen in `llvm`. Separately from 361624, we propose taking our nine-patch series (sandbox `afdo_profgen`, tip `c8942ae1`) into the llvm source at a regular LLVM release. The patches touch only llvm-profgen sources, tests and documentation, and applied cleanly to `tizen_base` at `61ef5d31` (checked 2026-11-14). Until then, the workflow uses our build from the sandbox commit, identified by SHA-256, and its preflight checks that `llvm-profgen --help` offers `--ip-samples`.

## 3. BOLT on armv7l, and where BOLT tools run

- **BOLT for armv7l is not useful to us.** BOLT's supported targets are AArch64, X86 and RISC-V, not ARM, so it cannot rewrite the 32-bit ARM binaries on RPi4. Whether a 32-bit host could run BOLT for other targets was not tested, and we have no such use case.
- **The two armv7l changes must be withdrawn together.** To build armv7l BOLT, the change widens armv7l `LLVM_TARGETS_TO_BUILD` from `ARM;BPF` to `ARM;AArch64;X86;BPF`. With only `ARM;BPF`, BOLT's target set would be empty and its configure step stops with "BOLT_TARGETS_TO_BUILD is empty". So removing armv7l BOLT and reverting the target list must happen in the same change.
- **Effect of keeping the expansion.** armv7l packages are compiled by the x86_64 cross compiler (`clang-accel`), so the expansion does not change how our packages are compiled. It adds AArch64 and X86 back-ends to the armv7l `libLLVM`, which grows on armv7l images and tool trees that install or update `libllvm`. Our board `perf` loads that library. Size and build-time increases were not measured.
- **Boards need no BOLT tools.** `perf2bolt` and `llvm-bolt` run only on the x86_64 build host. Our workflow does not need `perf` on the host either: board samples are converted to the pre-aggregated format and passed with `perf2bolt --pa`.

**Ask:** withdraw armv7l BOLT and the armv7l target expansion together, unless another consumer needs them; if kept, name that consumer in the commit message.

## 4. Package requirements

### 4.1 libllvm version pinning

- `bolt` uses LLVM's C++ APIs through `libLLVM.so` but has `Requires: libllvm` without a version. RPM already generates `libLLVM.so.22.1(LLVM_22.1)`, which prevents mixing across LLVM minor versions. A pin additionally guards against ABI changes from Tizen-local patches within 22.1.x.
- `llvm-tools-subpkgs` is a separate source package with its own release number. `%{version}-%{release}` inside it expands to the **tools package's** release (for example `22.1.8-1`), not `libllvm`'s (for example `22.1.8-4.1`), so an exact pin written that way would make `bolt` uninstallable. Do not use it.
- Do not compute the provider release with `%(rpm -q libllvm)` at spec-parse time either: OBS parses specs for dependency resolution outside the build root, so it would read the wrong system.
- Two workable options; HQ chooses:
  - **A (simple):** `Requires: libllvm = %{version}` plus the automatic SONAME dependency. Pin the BuildRequires to `%{version}`, assert in `%build` that the installed `llvm`, `llvm-devel`, `llvm-static-devel`, `libllvm` and `libomp` share one version-release, and print it into the build log.
  - **B (strict):** a project-maintained macro `llvm_provider_evr` (for example `22.1.8-4.1`), visible to both the scheduler and `rpmbuild`, used in BuildRequires and in `bolt`'s Requires, with the same `%build` assertion. Every `llvm` release then needs a matching update and rebuild of the tools package.
- `Version: 22.1.8` is hard-coded in `llvm-tools-subpkgs.spec`. Keep it tied to `llvm.spec`; the `%build` assertion detects drift.

### 4.2 perf on the boards

- Tizen `perf` for armv7l and aarch64 must stay available, with hardware PMU support in the kernel (RPi4 needs `CONFIG_ARM_PMUV3=y`).
- `perf` links `libLLVM.so.22.1`. A `libllvm` update requires a matching `perf` rebuild when the SONAME or the ABI that `perf` uses changes; otherwise the verified pair can stay. Our workflow records both SHAs and repeats its perf and cycles preflight after any update.

### 4.3 BOLT runtime for aarch64

- Keep `libbolt_rt_instr.a` and `libbolt_rt_hugify.a` in the aarch64 `bolt` package.
- The x86_64 package's runtime archives are x86_64-only. To instrument aarch64 binaries on an x86_64 host, extract the aarch64 archive and pass it explicitly:
  ```
  rpm2cpio bolt-<ver>.aarch64.rpm | cpio -id ./usr/lib64/libbolt_rt_instr.a
  llvm-bolt -instrument -runtime-instrumentation-lib=<path> …
  ```
- Documenting this is enough for us. Alternatively, a copy could ship as `/usr/lib/bolt/aarch64/libbolt_rt_instr.a` in the x86_64 package.

### 4.4 debuginfo, build IDs and link flags for the tools

- Welcome: `-Wl,--build-id=sha1` for the LLVM toolchain binaries (applied in the `_toolchain` configuration branch) and for the standalone BOLT build. Today's released llvm-profgen has no build ID.
- **Mechanism:** GBS runs `rpmbuild` with `_build_create_debug 1` and injects the debug packages itself; the late `%define debug_package %{nil}` in the new spec only prevents a second copy. `find-debuginfo.sh` runs from `__debug_install_post`, not `__os_install_post` as the spec comment says.
- **Compiler flags reach BOLT.** Tizen's build prelude exports the distribution `CFLAGS`/`CXXFLAGS` (including `-g2 -gdwarf-4`, stack protector and `_FORTIFY_SOURCE`), and CMake takes them from the environment because the spec does not set `CMAKE_C(XX)_FLAGS`.
- **Linker flags do not.** CMake adds the environment `LDFLAGS` only to its default linker flags, and the spec sets `CMAKE_EXE_LINKER_FLAGS`/`CMAKE_SHARED_LINKER_FLAGS` to `-Wl,--build-id=sha1` explicitly. So the distribution policy `-Wl,-z,relro,--as-needed -Wl,--gc-sections` is dropped, and the BOLT tools are expected to have no `GNU_RELRO` segment, unlike `llvm-profgen`, `libLLVM` and the other tools in the same build root. This follows from CMake's code; 361624 as-is was not built. The fix is to prepend `$LDFLAGS` (section 7).
- **Result with the section 7 patch (x86_64 build):**
  - the debug files are in **`bolt-debuginfo`**, because Tizen names the debug package after the subpackage, and sources are in `llvm-tools-subpkgs-debugsource`; no `llvm-tools-subpkgs-debuginfo` RPM is produced;
  - the five BOLT executables and their debug files have matching build IDs;
  - the debug files contain the BOLT compile units (for example `bolt/lib/Core/BinaryFunction.cpp`), and the debugsource package contains the BOLT sources;
  - all five executables have `GNU_RELRO`.

### 4.5 Build IDs for the packages we optimize (separate change)

- Sampled programs and libraries need a linker build ID; today we add `-Wl,--build-id=sha1` in each package's spec.
- Building clang with `-DENABLE_LINKER_BUILD_ID=ON` makes the clang driver pass `--build-id` on its ELF link paths. In this LLD, a bare `--build-id` means SHA-1.
- This covers packages linked through the clang driver; it does not cover GCC builds, direct linker invocations or builds that override the option. Even so, it is the change that most simplifies profiling FFmpeg, GStreamer and other packages without per-package spec edits.
- Because it changes the output of every affected package, it should be a separate change with platform-wide notice.

## 5. Items to change, and requests to HQ

| # | Item | Effect | Request |
|---|---|---|---|
| 1 | armv7l BOLT and the armv7l target expansion | No BOLT use on armv7l; larger armv7l `libLLVM` on images that update it (loaded by perf on RPi4); longer armv7l LLVM builds | Withdraw both **together** (section 3), or name the consumer |
| 2 | BOLT targets of the standalone build are implicit | Not a defect today (x86_64 LLVM has AArch64), but a future target-list change would silently remove the AArch64 support our BOLT step needs | Per-architecture `BOLT_TARGETS_TO_BUILD` (x86_64: `X86;AArch64`; aarch64: `AArch64`) and a target check (section 7.1). Setting `X86;AArch64` on all architectures would make aarch64 configure fail. |
| 3 | `bolt` requires an unversioned `libllvm` | Within 22.1.x a different Tizen build of libLLVM could be paired with BOLT | Option A or B of section 4.1 (not `%{version}-%{release}` in the tools spec) |
| 4 | New `Requires: python3` on `llvm` | Gives no tool its interpreter (see below), but pulls python3 into every build root that lacks it, on every architecture | Delete the line (see below) |
| 5 | `LLVM_LIBDIR_SUFFIX=64` hard-coded in the standalone spec; a comment assumes `/usr/lib64/cmake/llvm` | Wrong on 32-bit builds: armv7l uses `/usr/lib` and `/usr/lib/cmake/llvm`, and i586 builds `i686-tizen-linux`. The suffix sets BOLT's output library directory. Build outcome not tested. | Derive the suffix from `%{_lib}` as `llvm.spec` does, and fix the comment; moot for the architectures excluded under item 1 / section 7.1 |
| 6 | Scope: nine separate commits squashed into one change | Not only packaging: BOLT libraries switch to the LLVM dylib, and X86 table and helper copies are added for the standalone build. Hard to review and revert piecewise; the build-ID part is wanted on its own | Split (section 7.4), and provide smoke and regression evidence for the standalone dylib build, including an AArch64 rewrite and the pre-aggregated `S`-record path |
| 7 | Link flags: explicit `CMAKE_*_LINKER_FLAGS` replace the distribution `LDFLAGS` | BOLT tools are built without `-z relro`, `--as-needed` and `--gc-sections` (section 4.4) | Prepend `$LDFLAGS` (section 7) |

Details for item 4:
- `analyze-build`, `scan-build`, `scan-build-py` and `scan-view` were already in `llvm` in the parent commit, without any python3 dependency; 361624 only adds `Requires: python3`.
- The interpreters don't match it either: `scan-build`, `ccc-analyzer` and `c++-analyzer` are Perl, and `scan-view` calls `python`, not `python3`.
- The python3 tools need `libscanbuild`, which `%install` deletes (`rm -rf %{buildroot}/usr/lib/libscanbuild/*`), and `scan-view`'s modules are packaged in `llvm-devel`. So the new line makes no tool work.
- Meanwhile the buildconf's `Support: clang llvm-devel` applies to every package, and both require `llvm`. Our armv7l FFmpeg build root has no python3, so it would gain python3 and its dependencies, as would every other root without it. On OBS this is also expected to make python3 changes trigger wide rebuilds; this follows from general OBS behaviour and was not checked on Tizen OBS.
- **Preferred fix:** delete the line, which restores the parent's behaviour.
- `Recommends: python3` is valid syntax in Tizen's RPM 4.14.1.1. But weak dependencies are only hints to the package manager, so they guarantee neither outcome in build roots or on installed systems; use it only if HQ checks its solver policy.
- If HQ wants the analyzer tools to actually work, that is a separate change: a complete analyzer subpackage (section 7.3).

Smaller notes:
- The three `Obsoletes` (`clang-analyzer`, `llvm-xray`, `llvm-prof-tools`) name packages that do not exist in the parent commit. If they were never published, drop them. If they were, test upgrades from their published versions. `Obsoletes` is not `Provides`.
- `ExclusiveArch: x86_64 aarch64` (section 7) also excludes i586, where the current patch is expected to fail anyway (no `bolt_rt` target, wrong libdir suffix), and riscv64, which BOLT supports. In the Base snapshot we checked, `llvm` exists only for aarch64, armv7l and x86_64, and no published package requires `bolt` or its tools; HQ should still confirm the consumer matrix and decide whether riscv64 should be kept (it would need a RISCV target branch).
- The `bolt` description mentions only LBR/PT profiles. BOLT also works from sampled addresses without branch records (`perf2bolt -ba`, pre-aggregated profiles), which is how it is used on Arm boards.
- The comments about `llvm-static-devel` contradict each other: it is a BuildRequires (lines 12–15), but a build comment says it "is not installed here" (lines 67–69).
- `Requires: compiler-rt` on the `bolt` runtime package is unnecessary: the built `bolt` RPM works without it (section 7.2). `BuildRequires: compiler-rt` has no stated reason either, since `bolt_rt` is built freestanding with cleared flags; please explain or remove it.
- If the suggested changes are adopted, the 361624 commit message lines about armv7l BOLT and the python3 Requires need updating.

**Not blocking:** the AutoFDO and instrumented PGO parts of our workflow do not depend on this change. Merging it will still change toolchain packages (releases, build IDs, possibly the armv7l `libLLVM`); our workflow handles that by starting new experiments with a newly frozen dependency set.

## 6. Summary of requests to HQ

1. Withdraw armv7l BOLT and the armv7l `LLVM_TARGETS_TO_BUILD` expansion together, or name their consumer.
2. Set `BOLT_TARGETS_TO_BUILD` per architecture and add a target check.
3. Pin `bolt` to its LLVM provider with option A or B of section 4.1; do not use the tools spec's own `%{release}`.
4. Delete the new `Requires: python3` from `llvm`; treat a working analyzer package as a separate change.
5. Derive `LLVM_LIBDIR_SUFFIX` from `%{_lib}`.
6. Keep the distribution `LDFLAGS` in the BOLT link flags.
7. Correct the debug-package comment (`bolt-debuginfo`, `find-debuginfo.sh` from `__debug_install_post`).
8. Split the change; provide smoke and regression evidence for the standalone dylib build, including an aarch64 build.
9. Document the aarch64 `libbolt_rt_instr.a` for use on an x86_64 host.
10. Explain or remove the three `Obsoletes` and `BuildRequires: compiler-rt`; state the intended support for i586 and riscv64; update the commit message if the changes are adopted.
11. Separately: enable `ENABLE_LINKER_BUILD_ID` in clang, and plan to take the llvm-profgen IP-sample patch series into a regular LLVM release.

Items 1 to 7 are implemented by the patch in section 7, using option A for item 3.

## 7. Suggested patch

### 7.1 Patch

The patch applies with `git am` on top of 361624 (`da885208`). It changes only `packaging/llvm-tools-subpkgs.spec` and `packaging/llvm.spec`:

- `llvm-tools-subpkgs.spec`:
  - `ExclusiveArch: x86_64 aarch64`, with the riscv64 exclusion stated as a scope choice;
  - BuildRequires pinned to `%{version}`; `bolt` requires `libllvm = %{version}`; `Requires: compiler-rt` removed;
  - a `%build` check that `llvm`, `llvm-devel`, `llvm-static-devel`, `libllvm` and `libomp` share one Version-Release in the build root (a version-level check, not a byte-identity check);
  - per-architecture `BOLT_TARGETS_TO_BUILD` and a registered-target check on `llvm-bolt --version`;
  - `LLVM_LIBDIR_SUFFIX` derived from `%{_lib}`; the armv7l branches removed;
  - `$LDFLAGS` kept in the linker flags;
  - corrected comments and `bolt` description; one redundant `rm` removed.
- `llvm.spec`: armv7l targets back to `ARM;BPF`; the new `Requires: python3` removed, keeping a corrected note that scan-build (Perl) needs clang at runtime.

The author line is a placeholder; the change owner should take the content into their own commit.

```patch
From 941abd8798bc24405151f1fa1df988498b6cb46d Mon Sep 17 00:00:00 2001
From: AutoFDO workflow review <review@example.invalid>
Date: Mon, 16 Nov 2026 23:11:16 +0800
Subject: [PATCH] packaging: suggested follow-up for 361624 (standalone BOLT
 pinning, per-arch targets, no armv7l BOLT, no python3 Requires)

- llvm-tools-subpkgs: build bolt for x86_64 and aarch64 only; per-arch
  BOLT targets; pin LLVM providers to the package version and check that
  they share one Version-Release in the build root; derive the libdir
  suffix from the architecture; check the registered BOLT targets.
- Keep the distribution LDFLAGS when adding the build-id linker flag.
- llvm.spec: armv7l LLVM targets back to ARM;BPF; drop the new runtime
  Requires: python3 (scan-build is Perl, the python3 analyzer modules are
  removed in install).
---
 packaging/llvm-tools-subpkgs.spec | 98 ++++++++++++++++++++-----------
 packaging/llvm.spec               |  9 ++-
 2 files changed, 69 insertions(+), 38 deletions(-)

diff --git a/packaging/llvm-tools-subpkgs.spec b/packaging/llvm-tools-subpkgs.spec
index 6ea1035..0978f5f 100644
--- a/packaging/llvm-tools-subpkgs.spec
+++ b/packaging/llvm-tools-subpkgs.spec
@@ -5,25 +5,37 @@ Release:    1
 License:    NCSA
 Group:      Development/Tools
 Source0:    llvm-22.1.8.tar.gz
+# Package scope: x86_64 and aarch64 build hosts. armv7l and i586 are
+# excluded. riscv64 is also excluded, as a packaging scope choice and not
+# for lack of upstream BOLT support: it would need its own RISCV target
+# branch below and its own validation. Confirm the consumer matrix first.
+ExclusiveArch: x86_64 aarch64
 BuildRequires: cmake
 BuildRequires: ninja
-BuildRequires: llvm
-BuildRequires: llvm-devel
+BuildRequires: llvm = %{version}
+BuildRequires: llvm-devel = %{version}
 # llvm-static-devel: llvm-devel's LLVMExports.cmake validates the static
 # imported targets (libLLVM*.a) at configure time; without the archives
 # present, find_package(LLVM) aborts before bolt can link the dylib.
-BuildRequires: llvm-static-devel
+BuildRequires: llvm-static-devel = %{version}
 # libomp: the exported target "omp" in LLVMExports-release.cmake references
 # /usr/lib64/libomp.so; the configure-time existence check aborts without it.
-BuildRequires: libomp
+BuildRequires: libomp = %{version}
 # zlib-devel, libxml2-devel: the exported LLVM targets reference ZLIB::ZLIB
 # and LibXml2::LibXml2 in their link interfaces (bolt standalone build)
 BuildRequires: zlib-devel
 BuildRequires: libxml2-devel
 BuildRequires: clang
-BuildRequires: libllvm
+BuildRequires: libllvm = %{version}
 BuildRequires: compiler-rt
 
+# BOLT targets per build architecture: each must exist in the installed LLVM.
+%ifarch x86_64
+%global bolt_targets X86;AArch64
+%else
+%global bolt_targets AArch64
+%endif
+
 %description
 Standalone subpackages for LLVM debugging and analysis tools:
  - bolt: BOLT post-link binary optimizer, built standalone against the
@@ -38,13 +50,17 @@ rebuilding this package (minutes), not the multi-hour LLVM build.
 %package -n bolt
 Summary: BOLT post-link binary optimizer
 License: NCSA
-Requires: libllvm
-Requires: compiler-rt
+# Same LLVM version; rpm also generates the libLLVM.so.22.1(LLVM_22.1)
+# dependency. The provider release is intentionally not pinned: this
+# package has its own release number, which must not be used for libllvm.
+# ABI compatibility across libllvm releases stays a provider policy.
+Requires: libllvm = %{version}
 
 %description -n bolt
 BOLT is a post-link binary optimizer that reorders code in the final
-binary or DSO based on runtime profile data (perf LBR/PT samples) to
-improve instruction cache and TLB utilization.
+binary or DSO based on runtime profile data (perf LBR/PT samples, or
+sampled instruction addresses without branch records via perf2bolt -ba)
+to improve instruction cache and TLB utilization.
 
 %prep
 %setup -q -n llvm-22.1.8
@@ -54,19 +70,38 @@ improve instruction cache and TLB utilization.
 # itself; the standard debug_package macro would add them a second time
 # and fail with "package already exists". NOTE: keep percent signs out of
 # this comment -- rpmbuild expands macros even in comment lines.
-# Debuginfo IS still generated (find-debuginfo.sh runs in
-# __os_install_post): bolt-debuginfo and the debugsource package are
-# produced. The -Wl,--build-id=sha1 linker flags above make the bolt
-# binaries debug-correlatable.
+# find-debuginfo.sh still runs from __debug_install_post and moves the
+# separated debug files into bolt-debuginfo, named after the bolt
+# subpackage; sources go to llvm-tools-subpkgs-debugsource. Compiler
+# flags, including the debug options, come from the distribution CFLAGS
+# and CXXFLAGS that the build section exports and CMake reads. The
+# build-id linker flags in the build section tie each debug file to its
+# binary.
 %define debug_package %{nil}
 
 %build
 # ---- A. BOLT built standalone against the installed toolchain ----
 # Standalone detection: CMAKE_SOURCE_DIR == bolt source dir
-# => BOLT_BUILT_STANDALONE=TRUE, find_package(LLVM) finds /usr/lib64/cmake/llvm.
-# LLVM_LINK_LLVM_DYLIB=ON is mandatory: Tizen ships libLLVM.so (libllvm) and
-# only STATIC IMPORTED targets in llvm-devel; the static component archives
-# live in llvm-static-devel which is not installed here.
+# => BOLT_BUILT_STANDALONE=TRUE, find_package(LLVM) finds the installed
+# LLVM CMake package under the architecture libdir.
+# LLVM_LINK_LLVM_DYLIB=ON is mandatory: BOLT must link libLLVM.so (libllvm);
+# llvm-static-devel is installed only because the exported targets are
+# validated at configure time.
+#
+# Require one provider Version-Release for these packages in this build
+# root; all of them come from llvm.spec (drop libomp here if it ever gets
+# its own source package). This is not a byte-identity check.
+test "$(llvm-config --version)" = "%{version}" || exit 1
+llvm_evr=""
+for p in llvm llvm-devel llvm-static-devel libllvm libomp; do
+    e=$(rpm -q --qf '%%{VERSION}-%%{RELEASE}' "$p") || exit 1
+    if [ -n "$llvm_evr" ] && [ "$e" != "$llvm_evr" ]; then
+        echo "LLVM provider mismatch: $p $e, expected $llvm_evr"
+        exit 1
+    fi
+    llvm_evr=$e
+done
+echo "LLVM provider Version-Release consistency check passed: $llvm_evr"
 mkdir -p bolt-build
 cd bolt-build
 cmake \
@@ -77,23 +112,24 @@ cmake \
     -DCMAKE_C_COMPILER=clang \
     -DCMAKE_CXX_COMPILER=clang++ \
     -DCMAKE_INSTALL_PREFIX=/usr \
-    -DLLVM_LIBDIR_SUFFIX=64 \
+    -DLLVM_LIBDIR_SUFFIX=`echo %{_lib} | sed s/lib//g` \
     -DLLVM_ENABLE_RTTI=ON \
     -DLLVM_LINK_LLVM_DYLIB=ON \
-    -DCMAKE_EXE_LINKER_FLAGS="-Wl,--build-id=sha1" \
-    -DCMAKE_SHARED_LINKER_FLAGS="-Wl,--build-id=sha1" \
+    -DCMAKE_EXE_LINKER_FLAGS="$LDFLAGS -Wl,--build-id=sha1" \
+    -DCMAKE_SHARED_LINKER_FLAGS="$LDFLAGS -Wl,--build-id=sha1" \
     -DBOLT_INCLUDE_TESTS=OFF \
-%ifarch armv7l
-    -DBOLT_ENABLE_RUNTIME=OFF \
-%endif
+    -DBOLT_TARGETS_TO_BUILD="%{bolt_targets}" \
     -DLLVM_INCLUDE_TESTS=OFF
-# bolt: driver + tools; bolt_rt: runtime archives (ExternalProject).
-# CMake enables the runtime only on x86_64/aarch64/riscv64 hosts, so armv7l
-# builds just the driver. The runtime is for instrumenting x86/aarch64 targets.
-%ifarch armv7l
-ninja bolt
-%else
+# bolt: driver + tools; bolt_rt: runtime archives (ExternalProject) for the
+# build architecture.
 ninja bolt bolt_rt
+# Target registration check, kept in the build section so it also runs
+# when the check section is skipped. It does not test a rewrite.
+LC_ALL=C ./bin/llvm-bolt --version > bolt-version.txt 2>&1 || { cat bolt-version.txt; exit 1; }
+cat bolt-version.txt
+grep -Eq '^[[:space:]]*aarch64[[:space:]]+-' bolt-version.txt
+%ifarch x86_64
+grep -Eq '^[[:space:]]*x86-64[[:space:]]+-' bolt-version.txt
 %endif
 
 %install
@@ -102,8 +138,6 @@ cd bolt-build
 DESTDIR=%{buildroot} ninja install
 # The internal bolt static libs are build artifacts, not shipped content.
 rm -f %{buildroot}%{_libdir}/libLLVMBOLT*.a
-# LLVM_LIBDIR_SUFFIX=64 installs the internal archives to lib64 instead.
-rm -f %{buildroot}%{_prefix}/lib64/libLLVMBOLT*.a
 # perf2bolt and llvm-boltdiff are aliases of llvm-bolt: upstream installs them
 # as symlinks (bolt/tools/driver/CMakeLists.txt), and llvm-bolt selects its
 # mode from the name it is invoked as. Separate copies also collided on
@@ -125,8 +159,6 @@ cd ..
 %{_prefix}/bin/llvm-bolt-binary-analysis
 %{_prefix}/bin/llvm-bat-dump
 %{_prefix}/bin/merge-fdata
-%ifnarch armv7l
 %{_libdir}/libbolt_rt_instr.a
 %{_libdir}/libbolt_rt_hugify.a
-%endif
 
diff --git a/packaging/llvm.spec b/packaging/llvm.spec
index 14cdea4..ee17a9e 100644
--- a/packaging/llvm.spec
+++ b/packaging/llvm.spec
@@ -73,10 +73,9 @@ BuildRequires: clang, llvm, libllvm
 
 
 Requires: libllvm = %{version}-%{release}
-# scan-build and scan-view are Python scripts (formerly in clang-analyzer)
-# scan-build also needs clang installed at runtime; llvm does not require it
-# (requiring clang here would make llvm and clang depend on each other)
-Requires: python3
+# scan-build (Perl) also needs clang installed at runtime; llvm does not
+# require it (requiring clang here would make llvm and clang depend on
+# each other)
 # clang-analyzer, llvm-xray and llvm-prof-tools used to be separate
 # subpackages (llvm-tools-subpkgs.spec) that owned these files; llvm takes them over
 Obsoletes: clang-analyzer <= %{version}-%{release}
@@ -285,7 +284,7 @@ cmake \
 %endif
 %ifarch armv7l
     -DCMAKE_BUILD_TYPE=MinSizeRel \
-    -DLLVM_TARGETS_TO_BUILD='ARM;AArch64;X86;BPF' \
+    -DLLVM_TARGETS_TO_BUILD='ARM;BPF' \
     -DLLVM_TARGET_ARCH="ARM" \
 %endif
 %ifarch aarch64
-- 
2.43.0

```

### 7.2 Verification

The patch was applied to `da885208` and `llvm-tools-subpkgs.spec` was built for x86_64 with GBS, using the same frozen repositories as the released LLVM 22.1.8 packages and Tizen's unmodified build prelude; the only addition was a limit of two parallel build jobs.

| Check | Result |
|---|---|
| Spec parsing (Tizen `rpmspec` and macros) | x86_64 and aarch64: expected package list, BuildRequires, `bolt` Requires, BOLT targets and libdir suffix `64`. armv7l and i586 fall outside `ExclusiveArch`. `llvm.spec`: only the armv7l target list and the `python3` Requires change. |
| Build | GBS exit 0, 11 minutes wall time, peak memory 5.0 GiB |
| Provider check | All five LLVM packages at `22.1.8-4.1`; check passed |
| Compiler and linker flags | The CMake cache holds the distribution `CFLAGS`/`CXXFLAGS` (with `-g2 -gdwarf-4`) and `-Wl,-z,relro,--as-needed -Wl,--gc-sections -Wl,--build-id=sha1`. BOLT sources compile with the distribution flags followed by `-O3 -DNDEBUG`; `bolt_rt` keeps the empty flags set by 361624. |
| Registered targets | `llvm-bolt --version` lists `aarch64` and `x86-64` |
| Packages | `bolt`, `bolt-debuginfo`, `llvm-tools-subpkgs-debugsource`. `bolt` contains the seven tools and `/usr/lib64/libbolt_rt_instr.a`, `/usr/lib64/libbolt_rt_hugify.a`; it requires `libllvm = 22.1.8` and `libLLVM.so.22.1(LLVM_22.1)(64bit)`, not compiler-rt. |
| Debug information | Five build-ID pairs between executables and debug files match; BOLT compile units present; debugsource contains the BOLT sources |
| Linking and start-up | All five executables have `GNU_RELRO`; `ldd` resolves everything against the same build's `libllvm`; `--version` runs |
| Rewrite smoke tests | The built x86_64 `llvm-bolt`, without a profile, rewrote a minimal static AArch64 ELF and a minimal static x86_64 ELF (both linked with `--emit-relocs`) in relocation mode; both outputs disassemble, and the rewritten x86_64 program returns the same exit code as the original |

Not verified: an aarch64 build of `llvm-tools-subpkgs.spec`; a full `llvm.spec` build (the two changes restore the parent's armv7l target list and remove a runtime dependency); behaviour on OBS; rewriting a real workload, the `perf2bolt` pre-aggregated path and instrumentation.

### 7.3 Working analyzer tools (separate change)

If working analyzer tools are wanted, a separate change can add a `clang-analyzer` subpackage built from the same source. It must own:
- all entry points (`scan-build`, `scan-build-py`, `analyze-build`, `intercept-build`, `scan-view`);
- the `libexec` analyzer scripts;
- `libscanbuild`, no longer deleted at install;
- `share/scan-build` and `share/scan-view`, excluded from `llvm-devel`'s `%{_prefix}/share/*`.

It would declare `Requires: clang = %{version}-%{release}`, `perl` and `python3`, change the `scan-view` shebang to `python3`, and be tested in a minimal root with only the analyzer and its dependencies. Since these scripts are not CMake-exported targets, nothing forces them to stay in `clang` or `llvm`.

### 7.4 Separate follow-up changes

- `-DENABLE_LINKER_BUILD_ID=ON` for clang (section 4.5), with platform-wide notice.
- Split 361624 into:
  - (a) build-ID linker flags;
  - (b) the standalone BOLT package for x86_64/aarch64, with its dylib and X86 helper changes;
  - (c) package moves and `Obsoletes`;
  - (d) the MLGO incremental-build fix and the `DESTDIR` install change.

  Keep their build dependencies in order.

## 8. Verification status

| Statement | Basis |
|---|---|
| llvm-profgen and llvm-profdata already in `llvm` in the parent | Parent `llvm.spec` file list |
| LLVM targets: x86_64 `X86;ARM;AArch64;BPF`, aarch64 `AArch64;BPF` | `llvm.spec` at `da885208` |
| BOLT target selection and its error messages | `bolt/CMakeLists.txt` at `da885208` |
| `llvm` and `clang` in package build roots; python3 absent in the armv7l FFmpeg root, present in the x86_64 LLVM root | Package lists of existing Tizen build roots; buildconf `Support` |
| analyzer interpreters, `libscanbuild` removal, file ownership | Sources and spec at `da885208` and `61ef5d31` |
| Debug-package injection, the late `%{nil}`, distribution flags in the build prelude | Tizen RPM macros, GBS-generated macros and build logs |
| armv7l `%{_lib}=lib`, `/usr/lib/cmake/llvm` | `rpm --eval` in an armv7l root; `llvm-devel` armv7l file list |
| No published `bolt` consumers; `llvm` absent for i586 and riscv64 | Primary metadata of the frozen Base and Unified snapshots |
| Section 7 patch: parsing, x86_64 build, packages, dependencies, debug files, link flags, smoke tests | Section 7.2 |
| **Not verified** | Any build of 361624 as submitted (including the expected missing `GNU_RELRO`); an aarch64 build; a full `llvm.spec` build; OBS weak-dependency policy and rebuild behaviour; size and time effects of the armv7l target expansion; 32-bit host behaviour of BOLT; BOLT on a real workload |
