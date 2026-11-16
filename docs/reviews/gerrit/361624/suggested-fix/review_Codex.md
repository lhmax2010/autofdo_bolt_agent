# Review of 361624 suggested-fix v2 — Codex

**Verdict: approve with changes.** The previously identified Release-pinning and aarch64 target-selection errors are fixed. The recorded x86_64 build and smoke tests are credible evidence for the executable changes; v2 changes only comments. No new build blocker was found. Correct the comments identified below before sending the suggestion, and raise the compiler-flag policy question explicitly with the author. This is approval to submit a suggested fix, not certification of every Tizen build architecture or downstream ABI combination.

## Baseline and work performed

- Ran `git pull --ff-only origin main`: `Already up to date.` HEAD: `1db923863635a02522a01e42f3c279bd40f81406`. The required directory and `verification.md` section **“6. v2（仅注释）复核”** were present.
- Reviewed **`361624-suggested-fix-v2.patch`**, SHA-256 `b0b1a05f67fb50a37c1351e776ff0a92c2dfd1f6e08be65068d1d5be0790f2e9`, against original change `da885208aeb52f55c448ff46873d242346727522`. Read `verification.md`, both original specs, `own.diff`, `facts_check.md`, and both previous reviews. The previous review documents are context, not the object approved here.
- Line references below use the **spec after applying v2**, available in `temp/verify-361624-fix-v2-20261116/source`, commit `d509bc12ee2f824025b3e54331257936a8dfc33a`. `tools.spec` abbreviates its `packaging/llvm-tools-subpkgs.spec`. Evidence paths are relative to this suggested-fix directory unless otherwise specified.
- Checked the recorded compile flags, provider check, installed-package list, RPM dependencies/file lists, version output, loader resolution, debug sections/DWARF, and smoke-test records. Independently compared the saved v1/v2 expanded build/install/files sections: all six comparisons were byte-identical, consistent with `evidence/v2/equivalence.json`.
- Read the installed GBS/depanneur architecture filter and upstream OBS source. Scanned the two archived repository primary metadata files for bolt providers and reverse **runtime** dependencies. Queried actual optflags read-only using the successful build root's RPM loader, libraries, macros, RPM_CONFIGDIR and HOME, under `nice -n 19 ionice -c 3`.
- No GBS build, installation, board access, Gerrit operation, commit or push. No patch, spec, hq, or existing evidence was changed. Only this review is added. No live Tizen OBS reverse-dependency graph or architecture build was queried; these limitations are explicit below.

## 1. ExclusiveArch, GBS/OBS, and consumers

**The restriction is effective; it is not merely documentary.**

| Architecture | Effect of v2 | Assessment |
|---|---|---|
| x86_64 | Included; BOLT targets X86 and AArch64 | Matches the workflow and the successful build. |
| aarch64 | Included; BOLT target AArch64 | Macro selection is correct; native/target-root build remains untested. |
| armv7l | Excluded | Appropriate for this workflow. Restoring LLVM to ARM/BPF would otherwise leave no supported BOLT target. |
| i586 / i686 | Excluded | Reasonable for this package scope. In the original spec the unconditional non-armv7l `ninja bolt bolt_rt` would request a runtime not enabled by the normal 32-bit host default. This is a source-derived risk, not a measured i586 failure. |
| riscv64 | Excluded | A deliberate support-policy reduction, **not** a consequence of “32-bit hosts unsupported.” BOLT has a RISCV backend and its runtime default permits riscv64. HQ must own this scope decision. |

**GBS evidence:** `/usr/lib/python3/dist-packages/gitbuildsys/cmd_build.py`, `prepare_depanneur_cmd`, delegates to depanneur. `/usr/bin/depanneur:1047–1055` parses the spec and, when its first selected architecture is absent from `exclarch`, prints `build arch not compatible: ...` and skips that package. Thus an excluded source package does not reach compilation through this path. This does not establish a universal exit status for a whole GBS invocation containing only excluded packages; that invocation was not run.

**OBS evidence:** upstream OBS 2.10.34 `src/backend/bs_srcserver` sets the package's error/status to `excluded` when the configured target architecture is absent from `exclarch`; it uses the project target override when present. See the [upstream architecture filter](https://github.com/openSUSE/open-build-service/blob/2.10.34/src/backend/bs_srcserver#L1598-L1601). The deployed Tizen OBS version and live project overrides are **unverified**, so this is a code-backed explanation, not a claim to have observed this change's remote status. In particular, successful `rpmspec -P/-q` queries on armv7l/i586 in verification §2 do not authorize a build.

**Consumer check:** streamed `temp/verify-361624-fix-20261116/repository-check/{base,unified}-primary.xml.gz`. Results:

| Archived metadata | armv7l packages | i586 packages | riscv64 packages | bolt/llvm-tools-subpkgs providers | Named/file runtime dependencies on bolt tools |
|---|---:|---:|---:|---:|---:|
| Base 20261030.120529 | 537 | 5 | 8 | 0 | 0 |
| Unified 20261104.125239 | 3046 | 0 | 1 | 0 | 0 |

The scan also covered x86_64, aarch64 and noarch entries, and searched `bolt`, `llvm-bolt`, `perf2bolt` and `merge-fdata` dependency names/file paths. This supports **“no such published runtime consumer found in these snapshots”**, not “no other package depends on bolt.” Source BuildRequires, current OBS projects, internal packages and scripts invoking unlisted tools were not covered. The original new spec's existence also does not prove previous packages were published. A current HQ consumer check is required before adopting the reduced platform matrix, but it need not block sending a clearly scoped suggestion.

### F1 — minor: the architecture comment omits the intentional riscv64 exclusion

**Location:** tools.spec:8–10. **Impact:** the comment explains 32-bit exclusion but can mislead the author about why a supported 64-bit architecture disappears. No evidence here justifies saying riscv64 is technically unsupported.

**Required comment correction, relative to the v2-applied spec:**

```diff
-# BOLT runs on the build host and rewrites 64-bit ELF files only; it cannot
-# optimize 32-bit ARM. Building it for 32-bit hosts is not supported here.
+# Package scope for this proposal: x86_64 and aarch64 build hosts.
+# It excludes armv7l/i586 and also riscv64; the latter is a packaging
+# scope choice, not a lack of upstream BOLT support. Confirm the platform
+# consumer matrix before adopting this restriction.
 ExclusiveArch: x86_64 aarch64
```

Do not simply add riscv64 to the whitelist without also adding a `RISCV` target branch and validating that package/runtime path. Conversely, this workflow does not require adding riscv64 support now.

## 2. Version constraints and the provider consistency check

**Acceptable as a version-level dependency plus a build-root consistency check, not as exact runtime-provider pinning.**

- `BuildRequires: ... = %{version}` and `Requires: libllvm = %{version}` avoid the previous mistake of substituting the **tools** Release for the provider Release. The built `bolt-22.1.8-1` correctly requires `libllvm = 22.1.8` while using provider `22.1.8-4.1`; see verification §4.1 and `evidence/verification/bolt-requires.stdout`.
- tools.spec:89–98 checks `llvm-config --version` and equal **Version-Release strings** for llvm, llvm-devel, llvm-static-devel, libllvm and libomp. In an ordinary single-architecture root containing those subpackages from one LLVM build, their names differ but their Version-Release should not: no false rejection is demonstrated, and the successful build is a positive example.
- A dependency solver can legally select different Releases because the BuildRequires omit Release; the loop will then reject that root. This is intentional fail-closed enforcement of the stronger build policy, not a contradiction in RPM syntax. Such a root might be ABI-compatible, but it does not meet the stated same-provider requirement. A future independently packaged libomp would require revisiting the policy rather than silently dropping the check.
- Multilib duplicate installs, Epoch differences and same-Version-Release packages with different contents are not fully represented by this query. They are outside the recorded clean-root case; the string comparison must not be advertised as a universal package-identity proof.
- The line `BOLT is built against LLVM provider 22.1.8-4.1` is printed **before CMake/build**, so alone it proves only that the preceding queries passed. `build.log:511–545` shows the individual results; the subsequent successful configure/build, installed-package record, metadata identifying the f999bd40 provider, `ldd.stdout`, `--version`, and smoke tests together support the tested build. The log line alone does not prove linking, package byte identity, or arbitrary future runtime compatibility.

The automatic `libLLVM.so.22.1(LLVM_22.1)` dependency protects the named shared-library/symbol-version requirement. It does not encode every downstream C++ ABI change under that name. A later provider Release with Version 22.1.8 remains installable. For the workflow, retaining the verified BOLT/libLLVM pair and their SHAs addresses deployment reproducibility; for general distribution, HQ must maintain compatibility or rebuild/restrict consumers when needed.

### F2 — minor: distinguish a version-level policy from exact identity

**Location:** tools.spec:51–54,88–99. **Impact:** the current “one LLVM build” comment and past-tense log can overstate what the checks establish. This is not a request to reinstate the incorrect own-Release dependency or a host-side parse-time RPM query.

**Required clarification:**

```diff
 # Same LLVM version; rpm also generates the libLLVM.so.22.1(LLVM_22.1)
-# dependency. The tools package has its own release number, so the
-# release of libllvm cannot be expressed with this spec's own macros.
+# dependency. This intentionally does not pin the provider Release;
+# ABI compatibility across allowed Releases remains a provider policy.
+# The tools package's Release must not be used as the provider Release.
 Requires: libllvm = %{version}
@@
-# All LLVM provider packages must come from one LLVM build.
+# Require equal provider Version-Release strings in this clean build root.
+# Record package provenance separately; this is not a byte-identity check.
@@
-echo "BOLT is built against LLVM provider $llvm_evr"
+echo "LLVM provider Version-Release consistency check passed: $llvm_evr"
```

The log wording change is diagnostic only, but unlike the comment-only v2 delta it changes the expanded build script. Do not describe a revised script as byte-identical to v2; it needs a small updated parsing/log expectation check, not an automatic full rebuild requirement.

## 3. BOLT targets and version checks

**Pass.** tools.spec:30–35,116 selects `X86;AArch64` on x86_64 and `AArch64` on the other allowed architecture. The whitelist makes the else branch safe for this matrix. The saved aarch64 expansion confirms no X86 requirement. Target names match LLVM 22.1.8's BOLT CMake checks (`bolt/CMakeLists.txt:69–90` at da885208).

The actual `evidence/verification-smoke/bolt-version.txt` contains:

```text
  Registered Targets:
    aarch64    - AArch64 (little endian)
    ...
    x86-64     - 64-bit X86: EM64T and AMD64
```

The anchored regular expressions in tools.spec:125–127 match those exact entries; requiring whitespace after `aarch64` avoids accidentally accepting only `aarch64_32` or `aarch64_be`. The process status is checked before grep. `build.log:483` shows `/bin/sh -e`, and lines 767–768 show both successful grep commands, so failure is not silently ignored in the recorded Tizen build. Putting this in `%build` also avoids dependence on whether `%check` runs.

Registered aliases such as `x86` or `aarch64_32` are not proof that BOLT can rewrite every associated ELF ABI. The current check claims target registration, not that broader capability. No change needed.

## 4. LLVM_LIBDIR_SUFFIX and installation paths

**Pass.** tools.spec:110 uses the same backtick/`sed s/lib//g` expression as the original llvm.spec's CMake command. On the two allowed architectures `_lib=lib64`, so it yields 64. The saved expansions and the actual x86_64 configure command agree.

`evidence/verification/rpm-list-0.stdout` contains the seven tool paths under `/usr/bin` and both runtime archives under `/usr/lib64`; this is the expected path layout under the original standalone spec's hard-coded 64 on x86_64. The v1/v2 install and files expansions are byte-identical. **No before/after build of unmodified 361624 was performed**, so this verifies unchanged path intent and the new artifact paths, not byte identity with original-patch RPMs.

There is no surviving armv7l package whose layout must be fixed after the whitelist exclusion. The duplicate cleanup of the same lib64 internal archives is harmless for the allowed architectures. No change needed.

## 5. Changes to llvm.spec

**Accept for this bounded suggestion, with the existing analyzer limitation retained.**

- Restoring armv7l `LLVM_TARGETS_TO_BUILD` to `ARM;BPF` is paired correctly with excluding armv7l BOLT. It leaves the host x86_64 X86/ARM/AArch64/BPF targets unchanged. It does remove cross-target capability from the armv7l LLVM package; an HQ consumer relying on that newly proposed expansion would need a separate decision. It does not remove ARM/Thumb support used by this workflow.
- Deleting the newly added runtime `Requires: python3` restores the parent dependency policy. The saved llvm.spec expansion diffs in `evidence/parse-tizen/` show unchanged BuildRequires: LLVM itself still has its Python build dependency. The BOLT standalone build used the already published provider, so it is not evidence that this modified main spec was built.
- The change does not move or repair analyzer scripts. As documented in both previous reviews, scan-build is Perl, scan-view uses an unqualified `python` shebang, and Python analyzer modules/ownership already have gaps. Removing the new Requires is therefore acceptable as a rollback of dependency expansion, **not** a claim that analyzer functionality is complete without Python. A functioning analyzer package remains separate work. There is no reason to add Recommends here as an unverified substitute.
- Other 361624 changes—BOLT CMake/helpers, build-id flags, DESTDIR install and MLGO handling—remain in place. Main LLVM cross-target/package regression tests remain a merge/release responsibility, not a claim established by the BOLT-only build.

## 6. Debug artifacts and distribution compiler flags

### F3 — minor: qualify “no source-level DWARF” and the llvm.spec analogy

**Location:** tools.spec:70–76. **Evidence:** verification §4.3 and `evidence/verification/llvm-bolt-debug-sections.txt:34–41` show `.debug_info`, `.debug_line` and `.symtab`; `llvm-bolt-dwarf-info.txt:12,32,224,250,262` names glibc start/ABI/init/crt files. It has **no BOLT source CUs**, not literally no source-level DWARF. `rpm-list-2.stdout` is `(contains no files)`; the actual package names and matching runtime/debug build IDs are correctly reported in verification §4.1. The real `bolt-debuginfo` evidence supersedes the earlier parse-only expectation, as verification already explains.

**Impact:** no workflow failure, but the new explanatory comment is broader than the evidence. Furthermore, llvm.spec removes `-g` under `llvm_release_build=1` (`llvm.spec:191–200` before this fix); `_toolchain` sets that variable to 0 (`11–16`). A package called a “release build” in an operational report does not necessarily take that macro branch. This agrees with facts_check §4.2 rather than overturning it.

**I agree that this suggestion need not add `-g`.** The workflow needs correct rewriting and artifact identity, not source-level debugging of BOLT itself. Deliberately accepting symbol-only BOLT debugging is reasonable. It should be a stated choice, not an assumption that every LLVM GBS build drops debug information.

**Required comment-only correction:**

```diff
 # find-debuginfo.sh still runs from __debug_install_post and moves the
 # separated debug files into bolt-debuginfo, named after the bolt
-# subpackage. BOLT is compiled with the CMake Release flags only, without
-# -g, as llvm.spec does for its release build, so these files hold symbol
-# tables but no source-level DWARF, and llvm-tools-subpkgs-debugsource is
-# empty. The build-id linker flags in the build section tie each debug
-# file to its binary.
+# subpackage. In the verified x86_64 Release build, BOLT sources were
+# compiled without -g: the debug files contain symbol tables but no BOLT
+# source-level DWARF. Some linked CRT DWARF remains; debugsource was empty.
+# Source-level BOLT debugging is not required by the consuming workflow.
+# The build-id linker flags tie each debug file to its binary.
```

This corrects the comment using evidence already in verification; it does not dispute the recorded build, empty debugsource, or v1/v2 equivalence.

### F4 — major, inherited author-policy question: omission of optflags is broader than omission of -g

**Location:** tools.spec:102–117; original standalone spec has the same omission. **Evidence:** the actual successful root's read-only macro query returned `_toolchain=clang` and:

```text
-Os -ffunction-sections -fdata-sections -fstack-protector
-Wno-unused-command-line-argument -Wno-error=unused-but-set-variable
-Wno-error=unused-command-line-argument -momit-leaf-frame-pointer
-g2 -gdwarf-4 -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions
-Wformat -Wformat-security -fmessage-length=0 -frecord-gcc-switches
-fdiagnostics-color=never -m64 -march=nehalem -msse4.2 -mfpmath=sse
-fasynchronous-unwind-tables -fno-omit-frame-pointer -g
```

Reproduction source: successful root `temp/verify-361624-fix-20261116/root-x86_64-retry-executor/local/BUILD-ROOTS/scratch.x86_64.0`, its loader/rpmspec and macros, `--target x86_64-tizen-linux --eval '%{optflags}'`; RPM_CONFIGDIR and HOME point into that root. The query exited 0. The corresponding policies are also visible in `../evidence/x86_64-buildconf-full.conf:143–170,364–371`.

The recorded BOLT compile rule in `evidence/verification/compile-flags-excerpt.txt` instead has:

```text
FLAGS = -O3 -DNDEBUG -std=c++17 -fno-exceptions -funwind-tables
```

**Impact:** besides intentional debug/optimization choices, the rule lacks explicit distro stack protection and FORTIFY, format diagnostics, command-line recording, section-splitting, and the distro CPU/frame-pointer/asynchronous-unwind settings. Some are security or diagnosis policy, some performance/ISA policy; losing `-march=nehalem` is not by itself evidence of incorrect code. LLVM intentionally supplies `-fno-exceptions`; blindly copying the conflicting distro exception option is not a meaningful fix. Nor does the absence of these flags establish an exploitable defect from this review. Do not infer anything about PIE/RELRO from optflags that do not contain those options.

**Yes, raise this with the author.** “No source debugging required” does not by itself justify dropping hardening options. This is inherited from the original standalone spec, so I do **not** require changing its executable build flags in this comment-fix submission. Require either an explicit policy decision or a separately validated follow-up before treating the package as compliant with HQ's compiler-flag policy.

The main llvm.spec also deliberately filters some x86_64 options before passing CFLAGS/CXXFLAGS to CMake, including stack-protector and frame-pointer options. Therefore, the question is which explicit policy BOLT should use, not an assumption that llvm.spec preserves every distro flag or that all flags must be copied unchanged.

If the author chooses to carry distro flags while preserving O3 and no BOLT-source DWARF, a candidate relative to v2 is:

```diff
 echo "BOLT is built against LLVM provider $llvm_evr"
+# Preserve the checked distro flags except optimization/debug selection.
+# CMake Release supplies -O3; the separate freestanding runtime keeps its
+# existing explicit empty C/CXX flag sets in bolt/CMakeLists.txt.
+bolt_distro_flags=""
+for flag in %{optflags}; do
+    case "$flag" in
+        -O*|-g|-g[0-9]|-gdwarf-*|-ggdb*) ;;
+        *) bolt_distro_flags="$bolt_distro_flags $flag" ;;
+    esac
+done
 mkdir -p bolt-build
@@
     -DCMAKE_CXX_COMPILER=clang++ \
+    -DCMAKE_C_FLAGS="$bolt_distro_flags" \
+    -DCMAKE_CXX_FLAGS="$bolt_distro_flags" \
     -DCMAKE_INSTALL_PREFIX=/usr \
```

This candidate assumes the token-form optflags actually queried above; it is **not built or approved as behavior-equivalent**. It needs compile-rule inspection, hardening/target-flag review, rebuild and smoke tests. Keep the existing runtime flag isolation introduced by 361624; propagating distro ISA flags into the freestanding runtime previously caused conflicts. Adapt the first context line if F2's diagnostic wording is adopted.

## 7. Removed branches and dependencies

**Pass for the selected architecture matrix.**

- Removing the armv7l runtime-OFF and ninja branches is consistent with excluding armv7l. Native Linux x86_64/aarch64 builds enable bolt_rt by default in BOLT's CMake; both runtime archives remain listed. A genuine cross-CMake build with `CMAKE_CROSSCOMPILING` set is a different configuration, not proven by this native/GBS case.
- The actual RPM has no `compiler-rt` runtime Requires and successfully starts/rewrites under the recorded provider. BuildRequires compiler-rt is retained. This deletion does not remove either libbolt_rt archive or require deploying compiler-rt to the boards.
- Removing `%ifnarch armv7l` from `%files` is correct with the whitelist. `rpm-list-0.stdout` verifies both archives. `perf2bolt` and `llvm-boltdiff` aliases are retained; five real tool/debug IDs match according to the artifact record.
- No additional missing installed file is demonstrated. Actual aarch64 packaging, and any future widening of ExclusiveArch, still need their own validation. No additional patch requested here.

## 8. Verification sufficiency and residual risk

**Sufficient to submit a bounded suggestion after the required clarifications; insufficient to claim all-architecture release readiness.**

I accept verification §6.3's **v1/v2 build-equivalence conclusion within its stated scope**. It is backed by the exact comment-only source diff and equal expanded scripts/file lists, not merely by stripping all comments and assuming equivalence. Rebuilding solely because of these v2 comments would not add useful evidence.

The x86_64 build validates dependency resolution, actual linking and RPM layout. The AArch64 minimal ELF rewrite validates an x86_64 BOLT processing an AArch64 input; it does **not** validate an aarch64-host BOLT build or execution of the rewritten AArch64 program. Neither smoke test exercises the full perf2bolt pre-aggregated profile path, a real FFmpeg DSO, instrumentation, or performance. These limits agree with verification §§4.2 and 6.3.

- **aarch64 tools build: moderate residual risk.** Per-architecture target selection is fixed and parsed, but runtime compilation, native ABI/linking, dependency availability and final packaging remain untested. Required before publishing aarch64 artifacts, not mandatory before sending this suggested patch with that limit disclosed.
- **Full llvm.spec build: limited incremental risk from this fix, broader original-change risk remains.** It restores a previously used ARM/BPF target set and removes a newly added runtime dependency, while saved expansion diffs show no other changes. It is not a test of 361624's entire LLVM/MLGO/DESTDIR/build-id modifications. Required in the author's merge/release matrix; no need to demand another multi-hour build merely to submit the suggestion.
- **Excluded architectures and consumers: policy gate, not solved by building x86_64 again.** HQ should confirm the current project consumer matrix before final architecture exclusion. Archived runtime metadata cannot supply the missing live source-dependency answer.
- **Version-only runtime policy: no blanket compatibility proof.** Keep the tested pair for the workflow and verify/rebuild on provider ABI changes. Neither the provider echo nor a SONAME match certifies every allowed Release.

## Required changes and final verdict

Before sending the suggestion:

1. **F1:** explicitly identify riscv64 exclusion as a scope decision; include the limited consumer-check result and request HQ confirmation, without claiming there are no consumers anywhere.
2. **F2:** clarify that the check establishes provider Version-Release consistency, not exact runtime pinning or completed linking; correct the premature log wording.
3. **F3:** say “no BOLT source-level DWARF,” allow the observed CRT DWARF, and remove the ambiguous general analogy to LLVM release builds.
4. Raise **F4** as an author policy question. No `-g` addition or optflags implementation is required in this suggestion; any functional flag follow-up must be validated separately.

No blocker found. Findings: **1 major inherited policy question, 3 minor clarifications, 0 nits**. No new aarch64 or full-LLVM GBS build is required before submitting the suggestion, provided the remaining validation limits and platform decision are explicit.

**Final verdict: approve with changes.**
