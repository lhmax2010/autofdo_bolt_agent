# Review of 361624 suggested fix v2 (Claude Code)

| Item | Content |
|---|---|
| Object | `suggested-fix/361624-suggested-fix-v2.patch` (SHA-256 `b0b1a05f…f2e9`), applied on `da885208` as `d509bc12` in `temp/verify-361624-fix-v2-20261116/source` |
| Read | v2 patch; spec after v2 (line numbers below refer to it); `verification.md` §1–6; original `llvm.spec` / `llvm-tools-subpkgs.spec`; `own.diff`; `facts_check.md`; previous `review_Codex.md` / `review_claude_code.md` |
| Also inspected, read-only | `temp/verify-361624-fix-20261116/root-x86_64-retry-executor` (RPM macros, CMake modules, `bolt-build/CMakeCache.txt`, built `llvm-bolt`); the LLVM release build log in `temp/GBS-ROOT-LLVM-RELEASE-20261114c`; repository primaries in `temp/verify-361624-fix-20261116/repository-check/`; host `/usr/bin/depanneur` and `/usr/lib/build/Build/Rpm.pm` (gbs 2.1.1) |
| Not done | No GBS build, no installation, no Gerrit action, no hq change, no board access. Host `cmake` is absent, so CMake behaviour is taken from the build root's CMake modules plus the existing CMake cache, not from a new experiment. |

## Verdict: approve with changes

The packaging logic of v2 is correct: ExclusiveArch, version pinning, the provider check, per-arch BOLT targets, the `--version` check, the libdir suffix, and the two `llvm.spec` reverts. The changes are needed because v2's new debuginfo comment and `verification.md` §4.3 rest on a build environment that differs from a normal GBS/OBS build. The x86_64 verification build replaced Tizen's `__spec_build_pre`, so the distribution `CFLAGS`/`CXXFLAGS` were never exported.

In a normal Tizen build, CMake picks those flags up from the environment, so BOLT **is** compiled with `-g2 -gdwarf-4`. The comment ("without -g … no source-level DWARF … debugsource is empty") would then put a false statement into HQ's spec. The premise "llvm.spec's release build also drops -g" is not true for Tizen builds either.

**Must change before the suggestion is sent:**

1. **B1:** rewrite the debuginfo comment so it no longer claims "no -g / empty debugsource".
2. **M1:** re-run the x86_64 verification with Tizen's build prelude kept, and withdraw `verification.md` §4.3 item 1 and the §6.3 wording that rests on it.

**Recommended:**

- **M2:** pass `$LDFLAGS`; the BOLT binaries are the only ones checked that lack RELRO.
- **m1:** keep the "scan-build needs clang" note.
- **m2:** tell the author which commit-message lines to update.

## Findings

### B1 (blocker): the v2 debuginfo comment describes an artifact of the verification harness, not the real build

**Where:** spec after v2, lines 70–76.

**Evidence.**

1. **Tizen's build prelude exports the distribution flags.** Tizen's RPM macros (`usr/lib/rpm/tizen/macros:229-232`, same SHA-256 `f0f991bd…ebc8` in the LLVM release root and in the verification root) define:

   ```
   %__spec_build_pre\
   %{___build_pre}\
   %{set_build_flags};\
   ```

   `%set_build_flags` (`usr/lib/rpm/macros:1057-1060`) exports `CFLAGS`/`CXXFLAGS` from `%{optflags}` and `LDFLAGS` from `%build_ldflags`. buildconf line 364 has `%__optflags … -g2 -gdwarf-4 … -frecord-gcc-switches`; line 384 has `%build_ldflags -Wl,-z,relro,--as-needed …`.
2. **CMake reads them on the first configure.** `usr/share/cmake/Modules/CMakeCXXInformation.cmake:98` has `set(CMAKE_CXX_FLAGS_INIT "$ENV{CXXFLAGS} …")`, and `CMakeCInformation.cmake:94` has the same for `CFLAGS`. `CMakeInitializeConfigs.cmake:10` stores the value with `set(… CACHE STRING)`. The spec does not pass `-DCMAKE_C(XX)_FLAGS`, so the environment flags become `CMAKE_CXX_FLAGS`, and Release appends `-O3 -DNDEBUG` after them.
3. **The verification build replaced the prelude.** Its command (`verification.md` lines 71–72) used `--define '__spec_build_pre %{___build_pre}; ninja() {…}; …'`, which drops `%{set_build_flags}`.
   - The build log confirms it: `build-executor-retry/build.log` lines 483–545 show only the `AR`/`CC`/`MAKEFLAGS` exports and no `CFLAGS`. The LLVM release log (`…/logs/success/llvm-22.1.8-1/log.txt` lines 466–468) shows `+ CFLAGS='-Os … -g2 -gdwarf-4 …'` / `+ export CFLAGS` immediately after `cd /home/abuild/rpmbuild/BUILD`.
   - The verification CMake cache confirms it too: `bolt-build/CMakeCache.txt` has `CMAKE_CXX_FLAGS:STRING=` (empty) and `CMAKE_CXX_FLAGS_RELEASE:STRING=-O3 -DNDEBUG`. That is the "-O3 -DNDEBUG only" observed in `compile-flags-excerpt.txt`.
4. **361624 itself assumes distro flags reach the standalone build.** Its `bolt/CMakeLists.txt` passes `-DCMAKE_C_FLAGS=` / `-DCMAKE_CXX_FLAGS=` to the `bolt_rt` ExternalProject, with the comment "distro optflags inherited from the environment conflict with them (e.g. -msse4.2 with -mgeneral-regs-only)".
5. **The stated rationale is also wrong for Tizen.** The comment says "as llvm.spec does for its release build". `llvm.spec` lines 11–16 set `llvm_release_build 0` whenever `_toolchain` is defined, and buildconf line 163 always defines `%_toolchain` (see also `facts_check.md` §4.2). So the `-g`-stripping block (`llvm.spec` lines 192–200) does not run in GBS/OBS. The release log line 506 passes `-DCMAKE_C_FLAGS=… -g2 -gdwarf-4 …` to CMake.

**Impact.** In a normal GBS/OBS build, `bolt-debuginfo` is expected to contain BOLT source CUs and `llvm-tools-subpkgs-debugsource` is expected to be non-empty, which is the opposite of what the comment says. This is inferred from the macros and CMake code above, not from a new build. The comment would be wrong in HQ's tree.

**Answer to the question in item 6.**
- Not adding `-g` is fine, and I agree our workflow does not need BOLT source-level debugging.
- The patch does not need `-g`, because the normal build already gets it from `%optflags`.
- What must change is the reason given and the factual claims in the comment.
- The second question ("the standalone spec does not pass CFLAGS/CXXFLAGS") rests on the same harness artifact. Compiler flags do reach CMake. The real gap is the linker flags; see M2.

**Change (relative to the spec after v2):**

```diff
@@ -67,13 +67,12 @@
 # and fail with "package already exists". NOTE: keep percent signs out of
 # this comment -- rpmbuild expands macros even in comment lines.
-# find-debuginfo.sh still runs from __debug_install_post and moves the
-# separated debug files into bolt-debuginfo, named after the bolt
-# subpackage. BOLT is compiled with the CMake Release flags only, without
-# -g, as llvm.spec does for its release build, so these files hold symbol
-# tables but no source-level DWARF, and llvm-tools-subpkgs-debugsource is
-# empty. The build-id linker flags in the build section tie each debug
-# file to its binary.
+# find-debuginfo.sh still runs from __debug_install_post and moves the
+# separated debug files into bolt-debuginfo, named after the bolt
+# subpackage; sources go to llvm-tools-subpkgs-debugsource. Compiler
+# flags, including the debug options, come from the distribution CFLAGS
+# and CXXFLAGS that the build section exports and CMake reads. The
+# build-id linker flags in the build section tie each debug file to its
+# binary.
 %define debug_package %{nil}
```

Do not include "debugsource is empty" or "no DWARF" in any form until the corrected rebuild (M1) shows what is actually produced.

### M1 (major; must be done before claiming "verified"): the x86_64 verification is not representative

**Evidence.**
- **%build prelude:** see B1 point 3.
- **%install prelude:** the override also replaced Tizen's `__spec_install_pre` (`tizen/macros:234-239`: `___build_pre`, optional `STRIP_DEFAULT_PACKAGE`, `rm -rf`/`mkdir -p "$RPM_BUILD_ROOT"`). `_enable_binutils_strip` is not defined in that root, and the build root was new, so that part is very likely harmless.
- **Effect of the %build difference:** the compiler flags, and with them the `llvm-bolt` SHA-256, the 5 build-ids, the debuginfo contents and the debugsource contents in `verification.md` §4.1/§4.3, all come from a non-standard environment.
- **What the difference does not affect:**
  - the packaging logic: package names, file list, Requires, provider check, `--version` check;
  - the AArch64/x86_64 rewrite smoke tests. These remain valid as tests of the BOLT logic, but not of the binary that HQ would ship.

**Impact.**
- `verification.md` §4.3 item 1 ("这来自原spec的Release构建方式") and §6.3 ("BOLT源码DWARF未生成、debugsource为空保持真实有效") are not supported. This review's new evidence for overturning them is B1 points 1–5.
- The risk that the real flags break the build is low but not zero:
  - `-Os` is overridden by the later `-O3`;
  - `-fexceptions` is overridden by LLVM's later `-fno-exceptions`, as the verification `FLAGS =` line shows `-O3 -DNDEBUG -std=c++17 -fno-exceptions`;
  - `-D_FORTIFY_SOURCE=2`, `-march=nehalem -msse4.2`, `-frecord-gcc-switches` and `-Wall` are added.

**Change (harness, not patch).** Rebuild x86_64 once with the Tizen prelude reproduced and only the Ninja limit added:

```
--define '__spec_build_pre %{___build_pre}; %{set_build_flags}; ninja() { command /usr/bin/ninja -j2 %{lua:print(string.char(34,36,64,34))}; }; export CMAKE_BUILD_PARALLEL_LEVEL=2'
--define '__spec_install_pre %{___build_pre}; %__rm -rf "$RPM_BUILD_ROOT"; %__mkdir_p "$RPM_BUILD_ROOT"; ninja() { command /usr/bin/ninja -j2 %{lua:print(string.char(34,36,64,34))}; }; export CMAKE_BUILD_PARALLEL_LEVEL=2'
```

Then assert:
1. `+ export CFLAGS` appears in the %build trace.
2. `CMAKE_CXX_FLAGS` in `bolt-build/CMakeCache.txt` equals x86_64 `%optflags`.
3. The `.debug` files have BOLT CUs, and debugsource is non-empty (or record what it really is).
4. The runtime/debug build-ids still pair.
5. The provider check and `--version` checks still pass.
6. Re-run the two smoke rewrites on the new binary.

Before starting the GBS run, check `rpmspec --eval '%__spec_build_pre'` against the Tizen definition.

### M2 (major for HQ, minor for our workflow): distribution `LDFLAGS` are dropped, and the BOLT binaries lack RELRO

**Where:** spec after v2, lines 113–114 (unchanged from 361624).

**Evidence.**
- `CMakeCommonLanguageInclude.cmake:9-13` appends `$ENV{LDFLAGS}` only to `CMAKE_*_LINKER_FLAGS_INIT`, which is then stored with `set(… CACHE)`. The explicit `-DCMAKE_EXE_LINKER_FLAGS="-Wl,--build-id=sha1"` therefore wins, even when `LDFLAGS` is exported.
- The verification cache shows `CMAKE_EXE_LINKER_FLAGS:STRING=-Wl,--build-id=sha1`.
- `readelf -lW` on the verified `bolt-build/bin/llvm-bolt` shows **no `GNU_RELRO`** segment. In the same root, `llvm-profgen`, `llvm-readelf`, `libLLVM.so.22.1`, `cmake` and `ninja` each have one.

**Impact.**
- The BOLT tools miss the platform's `-z relro,--as-needed` policy (`%build_ldflags`, buildconf line 384).
- `llvm.spec` also sets linker flags explicitly, but it links with lld, which applies RELRO by default.
- This is pre-existing in 361624, not introduced by v2. The author can either take the change below or answer it as a question.

**Change:**

```diff
@@ -111,6 +111,6 @@
     -DLLVM_ENABLE_RTTI=ON \
     -DLLVM_LINK_LLVM_DYLIB=ON \
-    -DCMAKE_EXE_LINKER_FLAGS="-Wl,--build-id=sha1" \
-    -DCMAKE_SHARED_LINKER_FLAGS="-Wl,--build-id=sha1" \
+    -DCMAKE_EXE_LINKER_FLAGS="$LDFLAGS -Wl,--build-id=sha1" \
+    -DCMAKE_SHARED_LINKER_FLAGS="$LDFLAGS -Wl,--build-id=sha1" \
     -DBOLT_INCLUDE_TESTS=OFF \
```

Side effect: `--as-needed` and `--gc-sections` also apply. Verify both in the M1 rebuild: `GNU_RELRO` present, `ldd` clean, smoke tests pass.

### m1 (minor): v2 deletes the "scan-build needs clang at runtime" note that 361624 added on purpose

**Evidence.** The patch's `llvm.spec` hunk (patch lines 175–178) removes three comment lines. Two of them carry the content of 361624 sub-commit `c7edd8f43c66` ("note that scan-build needs clang at runtime"). Only the "Python scripts" claim was wrong: `scan-build` is Perl, as the previous round's `review_claude_code.md` R3 showed.

**Change (relative to `llvm.spec` after v2):**

```diff
@@ -74,5 +74,8 @@
 Requires: libllvm = %{version}-%{release}
+# scan-build (Perl) also needs clang installed at runtime; llvm does not
+# require it (requiring clang here would make llvm and clang depend on
+# each other)
 # clang-analyzer, llvm-xray and llvm-prof-tools used to be separate
```

### m2 (minor): the 361624 commit message will contradict the adopted fix

Sub-commit bullets `3abe328e2c30` ("build profiling tools and BOLT for armv7l") and `d3f74e4f484d` ("add Obsoletes and python3 Requires to llvm") will no longer describe the change. The cover note to the author should ask for them to be updated. The patch itself is fine.

### n1 (nit): stale or redundant install comment and command

Spec after v2, lines 134–137: with `ExclusiveArch: x86_64 aarch64`, `%{_libdir}` is `/usr/lib64`, so the two `rm -f` lines target the same path, and the comment "LLVM_LIBDIR_SUFFIX=64 installs … instead" no longer explains anything.

```diff
@@ -134,5 +134,4 @@
 # The internal bolt static libs are build artifacts, not shipped content.
 rm -f %{buildroot}%{_libdir}/libLLVMBOLT*.a
-# LLVM_LIBDIR_SUFFIX=64 installs the internal archives to lib64 instead.
-rm -f %{buildroot}%{_prefix}/lib64/libLLVMBOLT*.a
```

Optional, and harmless if kept.

### n2 (nit): `BuildRequires: compiler-rt` (line 28) has no stated reason

`bolt_rt` is built freestanding with cleared flags, and the verification log does not show compiler-rt being used. Ask the author, or leave it in place.

## Answers to the eight checks

### 1. ExclusiveArch

- **GBS.** `/usr/bin/depanneur:1049-1051`: if the build arch is not in `exclarch`, it prints `warning: <name>: build arch not compatible: x86_64 aarch64` and skips the spec (`next`). It does not fail.
  - The arch compared is the first entry of the arch policy (`depanneur:597-609`): `armv7l` gives `armv7l`, `-A i586` gives `i686`, `riscv64` gives `riscv64`. None of these is listed, so all three are skipped.
  - In a project build, `llvm.spec` still builds on those arches.
  - Not tested: the exit status of a GBS run whose only spec is skipped.
- **OBS.** OBS uses the same parser (`Build/Rpm.pm:483-485` fills `exclarch`). The standard behaviour is the state "excluded" for those repositories. This was not observed on Tizen OBS.
- **Consumers.** Neither pinned snapshot has any package named `bolt` or any requires/provides entry naming `bolt`, `perf2bolt`, `llvm-bolt` or `merge-fdata`: 0 matches in both `base-primary.xml.gz` and `unified-primary.xml.gz`. `bolt` is new in 361624, so nothing can depend on it yet.
- **Dropping i586/riscv64.** Acceptable. In the Base snapshot, `llvm`/`libllvm`/`clang` exist only for aarch64, armv7l and x86_64. i586 has only 5 `*-64bit` compat packages, and riscv64 only accel/qemu packages. So `BuildRequires: llvm = %{version}` cannot be met on i586/riscv64 there anyway. Only these two snapshots were checked. If HQ later wants riscv64 BOLT, it needs `%ifarch riscv64` with `bolt_targets RISCV`.

### 2. Version pinning and provider check

- **Correct in a legitimate environment.**
  - The `%%{VERSION}` escaping expands to `'%{VERSION}-%{RELEASE}'` (build.log lines 516–545).
  - Under `sh -e`, any failing `rpm -q` exits.
  - All five packages come from one `llvm.spec`, so a legitimate root has one EVR.
- **What the loop actually adds.** Some links are already enforced by RPM: `clang` requires `llvm = V-R` (`llvm.spec:121`), and `llvm` requires `libllvm = V-R` (line 75). `llvm-devel` and `llvm-static-devel` require only `llvm = V` (lines 98 and 106), and `libomp` has no link at all. So the loop adds real protection for `llvm-devel`, `llvm-static-devel` and `libomp`.
- **False positives.** I found none in practice. Theoretical cases: a package installed twice (does not happen in GBS/OBS roots), or `libomp` later moving to its own source package with its own release. In that case the loop must drop `libomp`; worth a one-line comment, nit.
- **Is the log line enough?** For the positive path, yes. The `sh -x` trace (build.log lines 516–545) shows each of the five `rpm -q` results and each comparison, not only the final echo, and `installed-packages.stdout` agrees. The mismatch path was never exercised, but it is three lines of shell and correct by inspection.
- **Limitation.** This is a build-time guarantee only. The shipped `bolt` requires `libllvm = 22.1.8` plus `libLLVM.so.22.1(LLVM_22.1)(64bit)` (`bolt-requires.stdout`), so install-time pairing across 22.1.8 releases is allowed. That is the intended trade-off.

### 3. BOLT targets and the `--version` check

- **Matches LLVM 22 output.** `TargetRegistry::printRegisteredTargetsForVersion` (`llvm/lib/MC/TargetRegistry.cpp:200-212` at `da885208`) prints four spaces, the name, padding to the longest name, then `" - "`. So `^[[:space:]]*aarch64[[:space:]]+-` and `^[[:space:]]*x86-64[[:space:]]+-` always have at least one space before `-`. `bolt-version.txt` shows `    aarch64    - AArch64 (little endian)` and `    x86-64     - 64-bit X86: EM64T and AMD64`.
- **The output reflects BOLT's targets.** `llvm-bolt` initializes only the targets in `TargetConfig.def` (`llvm-bolt.cpp:185-193`). `bolt-version.txt` accordingly lists no `arm`/`thumb`/`bpf`, even though x86_64 libLLVM has ARM and BPF.
- **aarch64.** The `%else` branch gives `AArch64`, which satisfies `bolt/CMakeLists.txt:86-91`. The x86-64 grep is correctly inside `%ifarch x86_64`. On aarch64 this was parsed only (`verification.md` §2), not built.

### 4. LLVM_LIBDIR_SUFFIX

- **Same idiom as `llvm.spec`.** `` `echo %{_lib} | sed s/lib//g` `` is character-for-character the same as `llvm.spec:323`. Parse results give `64` on x86_64 and aarch64 (`verification.md` §2 table).
- **Install paths unchanged.** The verification compile defines contain `-DCMAKE_INSTALL_FULL_LIBDIR="/usr/lib64"`, and the RPM list has `/usr/lib64/libbolt_rt_{instr,hugify}.a`. No pre-patch package was built, but the CMake input value is identical to the old literal `64` on both allowed arches, so the paths are identical.

### 5. llvm.spec changes

- **armv7l targets.** `ARM;BPF` is exactly the parent value (`own.diff` `-` line). It is also the value in the f999 baseline (`f999bd40:packaging/llvm.spec:222`), from which the released armv7l `llvm-22.1.8-4.1` was built. Nothing else in 361624 needs armv7l X86/AArch64: the only armv7l consumer was standalone BOLT, now excluded. The X86 mnemonic-table changes serve the x86_64 BOLT X86 target.
- **python3.** Removing `Requires: python3` changes only metadata: `verification.md` §2 shows only that Requires differs. `BuildRequires: python3`/`python3-devel` stay. No other part of 361624 uses the runtime dependency.
- **Comments.** The surviving comments are fine, apart from m1.

### 6. Debuginfo

See B1. Short form:
- The comment's factual claims and its "as llvm.spec does" rationale are wrong for normal Tizen builds.
- Not adding `-g` is the right call, because the normal build already has `-g2`.
- The CFLAGS question is moot; the real gap is `LDFLAGS` (M2).
- Missing in normal builds: the `%build_ldflags` set `-Wl,-z,relro,--as-needed -Wl,--gc-sections`.
- Not missing: the `%optflags` set, which reaches CMake through the environment: `-Os … -fstack-protector … -g2 -gdwarf-4 -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -Wformat -Wformat-security -frecord-gcc-switches -m64 -march=nehalem -msse4.2 -mfpmath=sse -fasynchronous-unwind-tables -fno-omit-frame-pointer`.
- In the verification build, both sets were missing.

### 7. Deleted content

- **armv7l branches.** Removed consistently: the `BOLT_ENABLE_RUNTIME=OFF` flag, the separate `ninja bolt`, and the `%ifnarch armv7l` around the runtime archives. On both allowed arches, `BOLT_ENABLE_RUNTIME` defaults to ON (`bolt/CMakeLists.txt:93-102`, host x86_64/aarch64, not cross-compiling under qemu-user), so `bolt_rt` exists and the archives are produced (confirmed on x86_64: `rpm-list-0.stdout`).
- **`Requires: compiler-rt`.** Removed correctly; `bolt-requires.stdout` has no compiler-rt.
- **Leftovers.** n1 (redundant `rm`/comment) and n2 (`BuildRequires: compiler-rt`). Nothing functional is missing.

### 8. Verification sufficiency

- **x86_64.** Must be re-run (M1). This is the one mandatory addition.
- **aarch64 build.** Low-to-medium risk; not required before sending, if the cover note says "aarch64 parsed, not built".
  - Remaining risks: running under qemu-user, with compilation through the x86_64 `clang-accel`; the `bolt_rt` runtime for aarch64; the `--version` check under qemu.
  - Each of these is standard upstream configuration. The AArch64 BOLT target is already exercised on x86_64 by the AArch64 rewrite smoke test.
- **Full `llvm.spec` build.** Not required. Both changes restore parent or baseline values that already built and shipped as 22.1.8-4.1 (armv7l `ARM;BPF`), or are metadata-only (`Requires`).

## Must change (summary)

1. **B1:** replace the debuginfo comment (diff above). Do not state "no -g", "no DWARF" or "debugsource empty".
2. **M1:** re-run the x86_64 verification with `%{set_build_flags}` in the %build prelude (and the Tizen %install prelude). Re-establish SHA-256, build-ids, debuginfo/debugsource contents and the smoke tests. Correct `verification.md` §4.3 item 1 and §6.3.

Recommended: M2 (`$LDFLAGS`), m1 (keep the clang note), m2 (commit-message note to the author), n1, n2.
