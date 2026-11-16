# Review of Gerrit change 361624 (platform/upstream/llvm) from the AutoFDO / BOLT workflow's point of view

| Item | Content |
|---|---|
| Change | 361624, patch set 1, commit `da885208aeb5` "packaging: split tool subpackages into a standalone llvm-tools-subpkgs spec" |
| Reviewed as | A user of the tool packages: the AutoFDO / instrumented PGO / BOLT workflow for Tizen packages (FFmpeg, GStreamer first; Linux kernel as a separate track) on Raspberry Pi 4 (armv7l, Thumb-2/A32) and Raspberry Pi 5 (aarch64), using the enhanced llvm-profgen on `sandbox/lhmax2025/afdo_profgen` |
| Material | The change's own diff and the complete `llvm.spec` / `llvm-tools-subpkgs.spec` at that commit; read-only facts checked in existing Tizen build roots (package lists, RPM macros, `llvm-devel` file lists). 361624 itself was not built. |
| Revision | 2 (facts checked: build-root contents, LLVM target lists, debuginfo mechanism, armv7l library paths) |
| Verdict | **Acceptable for our workflow with changes.** The new standalone `bolt` package is useful and in the right place. Six items should change or be clarified before merge (section 5); none blocks the AutoFDO part of the workflow. |

## 0. How the workflow uses the toolchain

All profile processing and binary rewriting happen on the **x86_64 build host**; the boards only run the workload and record samples.

1. Build the target package (GBS, clang 22) with profiling-friendly debug info and a linker build ID.
2. On the board, `perf record -e cycles` samples the workload; `perf script` exports text. The boards have no branch-record hardware, so every profile is built from instruction-address samples.
3. On the host, `llvm-profgen --ip-samples` (our enhancement) converts the export into a sample profile; `llvm-profdata` merges profiles.
4. The package is rebuilt with `-fprofile-sample-use` (AutoFDO) or `-fprofile-use` (instrumented PGO, profiles from `-fprofile-generate` runs).
5. BOLT (RPi5 only): the host converts the same board samples into BOLT's pre-aggregated format, then runs `perf2bolt --pa -ba` and `llvm-bolt` on the aarch64 binary.

The host tools are extracted from the Tizen x86_64 RPMs and identified by SHA-256; nothing is installed on the boards except files copied into a private directory.

## 1. Tools needed, architecture and package

| Tool | Needed on | Purpose in the workflow | Package after 361624 | Status |
|---|---|---|---|---|
| `llvm-profgen` (with our IP mode) | x86_64 host | Sample profile from board samples | `llvm` (x86_64) | OK. Unchanged versus the accepted baseline, where `llvm-profgen` is already in `llvm`. Our enhancement is not in 361624 (see section 2). |
| `llvm-profdata` | x86_64 host | Merge sample profiles; merge `.profraw` for instrumented PGO | `llvm` (x86_64) | OK |
| `llvm-readelf`, `llvm-objdump`, `llvm-dwarfdump`, `llvm-objcopy` | x86_64 host | Identity, section and debug-info checks | `llvm` (x86_64) | OK, unchanged |
| `libLLVM.so.22.1` | x86_64 host (tools that link it); boards (Tizen `perf` links it) | Runtime library | `libllvm` | OK. See section 4 for pinning and for the armv7l size change. |
| `clang` with `-fprofile-sample-use`, `-fprofile-generate/-use` | Build root (target armv7l / aarch64) | Consuming builds and instrumented builds | `clang` | OK, unchanged |
| compiler-rt profile runtime (`libclang_rt.profile-*.a`) | Build root, per target architecture | Linking `-fprofile-generate` builds | `compiler-rt` (target arch) | Unchanged; please confirm the armv7l and aarch64 archives are shipped |
| `llvm-bolt`, `perf2bolt`, `merge-fdata` | **x86_64 host only** | BOLT for RPi5 aarch64 binaries | new `bolt` (x86_64) | Right package. The x86_64 LLVM is built with `X86;ARM;AArch64;BPF`, so BOLT's default target set (supported targets ∩ installed LLVM targets) includes AArch64. We ask only for an explicit setting and a check to keep it that way (section 5, item 2). |
| `llvm-bolt-heatmap`, `llvm-bat-dump`, `llvm-boltdiff`, `llvm-bolt-binary-analysis` | x86_64 host, optional | Diagnostics | `bolt` (x86_64) | Fine |
| `libbolt_rt_instr.a` for **aarch64** | x86_64 host, as input to `llvm-bolt -instrument` | Optional: BOLT instrumentation of RPi5 binaries to get exact edge counts, since the boards have no branch records | `bolt` (aarch64) only | Present in the aarch64 package. An x86_64 host must extract it from the aarch64 RPM and pass `-runtime-instrumentation-lib`; see section 4. |
| `perf` | Boards (armv7l, aarch64) | Sampling | Not part of this change (kernel tools package) | Must remain available; it depends on `libllvm` (section 4) |
| `llvm-profgen`, `llvm-profdata`, BOLT tools on armv7l or aarch64 | Not needed | — | — | We never run them on the boards |

Kernel track: the kernel is out of scope for the current tools (llvm-profgen does not produce kernel profiles; upstream kernel BOLT support is x86-only). It adds no package requirement today; if a kernel method is chosen later, the same host-side tools apply.

## 2. llvm-profgen in the main `llvm` package

**Effect of 361624.** Relative to the accepted baseline, nothing changes for llvm-profgen: it already ships in `llvm` (`/usr/bin/llvm-profgen`). The commit message's "moves into the main llvm package" undoes an interim split from earlier patch sets of this series. Our delivery path stays the same: extract the tool from the x86_64 `llvm` RPM.

**Cost.** Any llvm-profgen change still needs a full LLVM package build. Our clean build of the accepted baseline took about 80 minutes on our build host; with clang bootstrap, ThinLTO and the ML inliner enabled on the current development branch, expect several hours, and a full LLVM release.

**Would the standalone tools spec be better?** Technically feasible: llvm-profgen uses only LLVM libraries exported by `libLLVM.so`, so it could be built in minutes like BOLT. But:

- It must then be disabled in the main build (`LLVM_TOOL_LLVM_PROFGEN_BUILD=OFF`), otherwise `LLVMExports.cmake` references a file that `llvm` no longer ships, the configure-time check that this change already works around.
- It needs exact `libllvm` version pinning (the tool uses non-stable C++ APIs).
- Its lit tests run naturally only in the main tree; our validation relied on them.

**Recommendation:** keep llvm-profgen in the main `llvm` package. Ask HQ to take our nine-patch series (sandbox `afdo_profgen`, tip `c8942ae1`) into the llvm source at a regular LLVM release, so the stock tool gains `--ip-samples`. Our patches touch only llvm-profgen sources, tests and documentation; they apply cleanly to the current `tizen_base` tip. Until then, the workflow uses our own build from the sandbox commit, identified by SHA-256. Revisit a standalone llvm-profgen only if profgen fixes need a release cadence faster than LLVM's.

Workflow consequence (no package change needed): preflight checks that `llvm-profgen --help` offers `--ip-samples` and records the tool SHA, so a stock tool is detected rather than misused.

## 3. BOLT on armv7l, and where BOLT tools run

- **BOLT for armv7l is not useful to us.** BOLT cannot rewrite 32-bit ARM binaries, so it cannot optimize anything on RPi4. Running `llvm-bolt` on an armv7l machine to process aarch64 or x86 binaries is not a use case we have, and BOLT is not designed or tested for 32-bit hosts.
- **The cost is not limited to BOLT.** To build armv7l BOLT, the change widens armv7l `LLVM_TARGETS_TO_BUILD` from `ARM;BPF` to `ARM;AArch64;X86;BPF`. That enlarges the armv7l `libLLVM.so` on every armv7l image and lengthens the armv7l LLVM build. Our board `perf` loads `libLLVM.so.22.1`, so RPi4 images carry the larger library for no benefit to us.
- **Boards need no BOLT tools.** `perf2bolt` and `llvm-bolt` run only on the x86_64 build host. Our workflow does not even need `perf` on the host: board samples are converted to BOLT's pre-aggregated format and passed with `perf2bolt --pa`.

**Ask:** drop BOLT for armv7l and revert the armv7l target expansion, unless another consumer needs them; if kept, state that consumer in the commit message.

## 4. Package requirements

1. **libllvm version pinning.**
   - `bolt` has `Requires: libllvm` without a version, but uses LLVM's non-stable C++ APIs. Use `Requires: libllvm = %{version}-%{release}` (as `llvm` already does), and pin the BuildRequires on `llvm`, `llvm-devel` and `libllvm` to the same version.
   - `llvm-tools-subpkgs.spec` hard-codes `Version: 22.1.8`; keep it tied to `llvm.spec`, for example from a shared macro, so the two cannot drift.
2. **perf on the boards.**
   - Tizen `perf` for armv7l and aarch64 must stay available with hardware PMU support in the kernel (RPi4 needs `CONFIG_ARM_PMUV3=y`).
   - Because `perf` links `libLLVM.so.22.1`, any `libllvm` change must rebuild `perf` in the same release, and the armv7l library size change from section 3 reaches the board through this dependency.
3. **bolt_rt on aarch64.**
   - The aarch64 `bolt` package ships `libbolt_rt_instr.a` and `libbolt_rt_hugify.a`; keep them.
   - The x86_64 package's runtime archives are x86_64-only, so instrumenting aarch64 binaries on the x86_64 host needs the aarch64 archive. Either document extracting it from the aarch64 RPM, or ship it for cross use, for example as `/usr/lib/bolt/aarch64/libbolt_rt_instr.a` in the x86_64 package. Both are acceptable to us; a documented path is enough.
4. **debuginfo and build IDs for the tools.**
   - Welcome: `-Wl,--build-id=sha1` for the LLVM toolchain binaries and for the standalone BOLT build (today's released llvm-profgen has no build ID).
   - Mechanism (checked): GBS runs `rpmbuild` with `_build_create_debug 1` and injects the debug package when `%package`/`%prep` are parsed; the new spec's `%define debug_package %{nil}` comes after `%package -n bolt` and does not clear it. A macro-level parse lists `llvm-tools-subpkgs-debuginfo` and `-debugsource`; the earlier `llvm` release did produce `llvm-debuginfo`.
   - Please confirm from a real build that the BOLT binaries' debug files exist (expected in `llvm-tools-subpkgs-debuginfo`, not a package named `bolt-debuginfo`) and that their build IDs match the shipped binaries.
   - The spec comment says `find-debuginfo.sh` runs in `__os_install_post`; it runs from `__debug_install_post`. Please correct the comment.
5. **Build IDs for the packages we optimize (not in this change).**
   - Sampled programs and libraries need a linker build ID; today we add `-Wl,--build-id=sha1` through each package's spec.
   - Please build clang with `-DENABLE_LINKER_BUILD_ID=ON`, so every Tizen package gets a build ID by default. This is the single change that most simplifies profiling FFmpeg, GStreamer and later other packages without per-package spec edits.

## 5. Items that complicate the workflow, and requests to HQ

| # | Item | Effect on us | Request |
|---|---|---|---|
| 1 | armv7l BOLT and the armv7l target expansion | Larger armv7l libLLVM on RPi4 images (loaded by perf); longer armv7l builds; no BOLT use on armv7l | Remove both, or name the consumer that needs them |
| 2 | BOLT targets of the x86_64 standalone build are implicit | Not a defect today: the x86_64 LLVM includes AArch64, so the default BOLT targets include it. But a future change to the LLVM target list would silently remove the AArch64 support our BOLT step needs | Safeguard: set `-DBOLT_TARGETS_TO_BUILD="X86;AArch64"` explicitly and add a `%check` that `llvm-bolt --version` lists the aarch64 target |
| 3 | `bolt` requires an unversioned `libllvm` | A partial repository update can pair BOLT with a different libLLVM | Exact version-release pinning (section 4.1) |
| 4 | `llvm` now `Requires: python3` (scan-build/scan-view moved into it) | `llvm` is in target-architecture build roots through `clang` and `llvm-devel` (both require it). Our armv7l FFmpeg build root (108 packages) has no python3; after this change it would pull python3 and its dependencies. (The x86_64 LLVM build root already has python3 for LLVM's own build.) Configure scripts may behave differently when python3 is present, and package build roots change across the update. | `Recommends: python3` instead of `Requires`, or keep scan-build/scan-view in a separate subpackage (as `clang-analyzer` was) |
| 5 | `LLVM_LIBDIR_SUFFIX=64` is hard-coded in the standalone spec, also for armv7l; a spec comment assumes `/usr/lib64/cmake/llvm` | Checked: on armv7l `%{_lib}` is `lib`, `%{_libdir}` is `/usr/lib`, and LLVM's CMake package is in `/usr/lib/cmake/llvm`. The suffix sets BOLT's output library directory, so armv7l output paths would be wrong; whether the build fails was not tested | Derive the suffix from the architecture (§7.1) and fix the comment, or drop the armv7l build (item 1) |
| 6 | Scope: nine logically separate commits squashed into one change (packaging split, BOLT standalone fixes, armv7l tools, build-id flags, MLGO incremental fix, install changes) | Hard to review and revert piecewise. The build-id part is wanted on its own; the armv7l part is not wanted. | Split into separate changes, at least: (a) build-id linker flags, (b) standalone BOLT package for x86_64/aarch64, (c) package file moves, (d) armv7l changes |

Smaller notes:

- The `bolt` description mentions only LBR/PT profiles. BOLT also works from sample addresses (`perf2bolt -ba`, pre-aggregated `S` records), which is how it is used on Arm boards without branch records; the description could say so.
- The comments around `llvm-static-devel` contradict each other: it is declared as BuildRequires, while a build comment says it "is not installed here". Clarify which is true; it pulls large archives into the build root.
- `Requires: compiler-rt` on `bolt` looks unnecessary for the driver tools; only the instrumentation runtime relates to it.

**Not blocking:** the AutoFDO and instrumented PGO parts of our workflow do not depend on this change. llvm-profgen, llvm-profdata and libLLVM stay where they are. BOLT (our milestone M4, RPi5 only) benefits from a packaged x86_64 `llvm-bolt` with AArch64 support, provided items 2 and 3 are addressed.

## 6. Summary of requests to HQ

1. Drop armv7l BOLT and revert the armv7l `LLVM_TARGETS_TO_BUILD` expansion (or justify them).
2. Keep AArch64 in the x86_64 `bolt` package explicitly (safeguard) and verify it with a `%check`.
3. Pin `bolt` to `libllvm = %{version}-%{release}` and pin its BuildRequires; tie the tools spec version to `llvm.spec`.
4. Avoid adding `python3` to target-architecture build roots through `llvm` (`Recommends: python3`, or keep scan-build in a subpackage).
5. Fix the hard-coded `LLVM_LIBDIR_SUFFIX=64` for non-64-bit architectures.
6. Split the change into reviewable parts; keep the build-id part.
7. Confirm from a real build that the BOLT debug files (in `llvm-tools-subpkgs-debuginfo`) and `llvm-debuginfo` match the shipped binaries' build IDs; fix the `find-debuginfo.sh` comment.
8. Document or package the aarch64 `libbolt_rt_instr.a` for use on an x86_64 host.
9. Separately: enable `ENABLE_LINKER_BUILD_ID` in clang, and plan to take the llvm-profgen IP-sample patch series (sandbox `afdo_profgen`) into a regular LLVM release.

## 7. Suggested changes to the patch

Minimal edits that address sections 4 and 5. They are proposals for the change owner; spec context lines may need adjusting to the final patch set.

### 7.1 `packaging/llvm-tools-subpkgs.spec`

```diff
 Name:       llvm-tools-subpkgs
 Version:    22.1.8
+# BOLT is useful only where it can run on the build host for 64-bit targets;
+# it cannot optimize 32-bit ARM binaries.
+ExclusiveArch: x86_64 aarch64
 ...
-BuildRequires: llvm
-BuildRequires: llvm-devel
-BuildRequires: libllvm
+BuildRequires: llvm = %{version}
+BuildRequires: llvm-devel = %{version}
+BuildRequires: libllvm = %{version}
 ...
 %package -n bolt
 Summary: BOLT post-link binary optimizer
 License: NCSA
-Requires: libllvm
-Requires: compiler-rt
+# BOLT links non-stable LLVM C++ APIs from libLLVM.so.
+Requires: libllvm = %{version}-%{release}
 ...
 %build
+# The tools must be built against the same LLVM release as this spec.
+test "$(llvm-config --version)" = "%{version}" || { echo "llvm-config version mismatch"; exit 1; }
 mkdir -p bolt-build
 ...
-    -DLLVM_LIBDIR_SUFFIX=64 \
+    -DLLVM_LIBDIR_SUFFIX=%(echo %{_lib} | sed 's/^lib//') \
+    -DBOLT_TARGETS_TO_BUILD="X86;AArch64" \
 ...
-%ifarch armv7l
-    -DBOLT_ENABLE_RUNTIME=OFF \
-%endif
     -DLLVM_INCLUDE_TESTS=OFF
-%ifarch armv7l
-ninja bolt
-%else
 ninja bolt bolt_rt
-%endif
+
+%check
+# The x86_64 package must be able to process RPi5 (aarch64) binaries.
+./bolt-build/bin/llvm-bolt --version | grep -qi aarch64
+./bolt-build/bin/llvm-bolt --version | grep -qi x86-64
 ...
 %files -n bolt
 ...
-%ifnarch armv7l
 %{_libdir}/libbolt_rt_instr.a
 %{_libdir}/libbolt_rt_hugify.a
-%endif
```

Version coupling: as an alternative to the `llvm-config` check, both specs can read the version from one shared file in `packaging/`, but the check above is enough to stop a mismatched build.

Description: add "also works from sampled addresses without branch records (`perf2bolt -ba`, pre-aggregated profiles)" to `%description -n bolt`.

### 7.2 `packaging/llvm.spec`

```diff
 %ifarch armv7l
     -DCMAKE_BUILD_TYPE=MinSizeRel \
-    -DLLVM_TARGETS_TO_BUILD='ARM;AArch64;X86;BPF' \
+    -DLLVM_TARGETS_TO_BUILD='ARM;BPF' \
     -DLLVM_TARGET_ARCH="ARM" \
 %endif
```

python3 in build roots, two options:

1. **Smallest change:** keep the scripts in `llvm`/`clang`, make the dependency weak, so build roots do not pull python3 while installed systems still get it:

   ```diff
   -Requires: python3
   +Recommends: python3
   ```

2. **Cleaner:** restore a `clang-analyzer` subpackage owning `scan-build`, `scan-view`, the `libexec` analyzer scripts and their `share/` data, with `Requires: clang = %{version}-%{release}, python3`; drop `Requires: python3` and the `clang-analyzer` Obsoletes from `llvm`. If the files must stay in `clang` because of CMake exports (as the commit message says), use option 1.

### 7.3 Separate follow-up changes (not in 361624)

- **Default build IDs for all packages:** add `-DENABLE_LINKER_BUILD_ID=ON` to the clang configuration. This changes every package's output (it adds `.note.gnu.build-id`), so it should be its own change with platform-wide notice.
- **aarch64 BOLT runtime on x86_64 hosts:** document `rpm2cpio bolt-<ver>.aarch64.rpm | cpio -id ./usr/lib64/libbolt_rt_instr.a` and `llvm-bolt -instrument -runtime-instrumentation-lib=<path>`, or ship a copy as `/usr/lib/bolt/aarch64/libbolt_rt_instr.a` in the x86_64 package.
- **Split** 361624 into: (a) build-id linker flags, (b) standalone BOLT package (x86_64/aarch64), (c) package file moves with Obsoletes, (d) the MLGO incremental-build fix and the `DESTDIR` install change.

### 7.4 Facts checked for revision 2

| Question | Finding | Effect on this review |
|---|---|---|
| Is `llvm` in package build roots; is python3 already there? | `llvm` and `clang` are in both checked roots (pulled by `clang`/`llvm-devel`); armv7l FFmpeg root: no python3; x86_64 LLVM root: python3 present | Item 5.4 narrowed to target-architecture roots without python3 |
| LLVM targets | x86_64 `X86;ARM;AArch64;BPF`; aarch64 `AArch64;BPF` | Item 5.2 is a safeguard, not a defect |
| debuginfo with `debug_package %{nil}` | GBS injects the debug package before the late `%{nil}`; macro parse lists `llvm-tools-subpkgs-debuginfo`; the real RPM is unverified | Section 4.4 asks for confirmation from a real build and a comment fix |
| armv7l library paths | `%{_lib}=lib`, `%{_libdir}=/usr/lib`, `/usr/lib/cmake/llvm/LLVMConfig.cmake` | Item 5.5 confirmed for output paths; build failure not claimed |

Still unverified (needs a real build of 361624): the final debuginfo package contents and build-ID pairing, and whether an armv7l build of the standalone spec succeeds.
