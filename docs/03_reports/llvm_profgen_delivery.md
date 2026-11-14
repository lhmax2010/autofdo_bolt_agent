# Limited llvm-profgen delivery

Status: first HQ draft, awaiting PM review. Internal main source commit: 41bae45466b853cee173fe80189f2f44b0500b95.

## Source and reproducibility

Gerrit project platform/upstream/llvm, branch sandbox/lhmax2025/afdo_profgen, tip c8942ae1b53099a78a97dca2b64427af6e58432b. Base f999bd406c0a70fe8107aa992164fe6945c5d46a. The nine original git-am commits are listed in the [README](../../README.md).

All nine patches also applied cleanly to newer tizen_base tip 61ef5d31ca91025c414c748477bef0c64ddfa67c in a separate forward-check tree. That tree was not built. Its three upstream changes concern packaging/bootstrap/ThinLTO; this release deliberately uses the accepted f999 snapshot.

The release spec is unchanged from the base. Changes are confined to llvm-profgen source, tests and CommandGuide. 358 source/test/document files match the patch-9 acceptance tree byte for byte. A fresh fetch of only the published sandbox branch reproduced those hashes.

## Normal release build

- Host: Ubuntu 24.04.5 LTS, GBS 2.1.1; x86_64 target.
- Unified: tizen-unified-toolchain_20261104.125239.
- Base: tizen-base-toolchain_20261030.120529, newest live valid Base no later than Unified.
- Normal, non-incremental, fresh root, original spec; -j4, 10 GiB / 400% scope, nice 19 / ionice class 3.
- Start 2026-11-14 01:10:26 PST; finish 02:30:06 PST; wall time 4780.358 seconds; GBS exit 0; 7637 Ninja steps.
- 22 binary RPMs plus one SRPM. llvm-profgen is /usr/bin/llvm-profgen in llvm-22.1.8-1.x86_64.rpm.
- Tool SHA-256: **67ad21faba787d276a80673c1f324f7c0591d28d76bd37a8bd57de0d86426be6**.
- Runtime and debug file have no build-id under this unchanged spec. The .gnu_debuglink name and full debug-file CRC match (2847750365). This is debuglink identity evidence, not a claimed matching build-id.
- --version and --help pass under the GBS loader, LLVM 22.1.8.
- Build memory.peak 10 GiB, max-limit events 14050, OOM / OOM-kill zero. Minimum sampled MemAvailable 20,526,964,736 bytes.

122 actual dependency RPMs (195,060,672 bytes) were archived internally with checksums; all selected downloads came from Base. The configured Unified metadata was live and valid but supplied none of the selected dependencies. No old-cache fallback was used.

| Dependency | Patch-9 retained root | Release root |
|---|---|---|
| gcc | 14.2.0-1.6 | 14.2.0-1.14 |
| binutils | 2.43-1.6 | 2.43-1.15 |
| cmake | 3.31.2-1.6 | 3.31.2-1.6 |
| python3 | 3.14.2-1.6 | 3.14.2-1.10 |
| ninja | 1.13.1-1.5 | 1.13.1-1.15 |

Snapshots expire. If removed, choose and record currently available fixed snapshots and repeat output regression; binary equality to this release is not required. Dependency versions and stripping can change binary hashes.

## Validation

- C1: two passes of 636 cases each; zero baseline differences, identical passes.
- IP: 14 historical exports and 18 fixture/format combinations, each run with the patch-9 development tool and release tool (64 calls). Profiles identical. Each quality JSON differed only in tool.arguments[0]; replacing that one executable path made raw JSON bytes identical.
- Historical exports retain four successful conversions and ten expected generate/no-usable-samples failures. This is behavior preservation, not fourteen successful profiles.
- Release spec does not run lit. Source equality plus prior patch-9 acceptance substitutes for a new lit run: 84 PASS, 1 UNSUPPORTED, 1 XFAIL, 0 FAIL (86 total). No claim of release %check execution.
- The [host demo](../04_demo.md) uses this release executable and sandbox fixtures.

Detailed raw evidence remains in the internal main repository and host archive; it is intentionally not copied into hq.

## Earlier RPi4 integration and real-input checks

These are previous recorded results, not a new board session or performance comparison:

| Check | Recorded result |
|---|---|
| Fork without exec | 10,007 target samples; inherited mapping/address checks agree; verified |
| Exec to a different image | 4,939 + 1,085 samples; zero cross-image address misattribution; both verified |
| Deleted test library | 95/95 addresses agree; default identity failure, explicit missing-ID waiver remains unverified |
| Kernel modules | 151,691 kernel samples; independent DSO classification agrees; excluded from user target |
| System-wide unknown PID | 16 real -1/-1 samples; never match a selected PID |
| Real [unknown] DSO | 335 samples classified unmapped |
| Complete high-LOST export | 423 LOST records, L=58,343, S=1,190,755; L/(L+S)=58,343/1,249,098; independent recount agrees |
| Real Thumb avg check | 3 hotspots, 11,525 instruction starts, 715 keys; GNU-based independent calculation agrees |
| Patch-9 non-leaf line-zero correction | 70 logical groups / 106 physical originals reconverted; exactly 2,736 samples excluded; allowed changes audited |

These establish functional behavior. **Statistical quality equivalence and performance gains remain unvalidated.** Board telemetry qualification and final quality/performance matrices are separate. Historical RUNs are not automatically suitable for new thermal/kernel conditions.

## Delivery limits

User-space DWARF IP only: AArch64 and ARMv7 Thumb-2/A32. No pseudo-probe, perf.data input, kernel profile or BOLT in this delivery. Aggregation has no default; explicit max/none/none/none is a conservative calling policy, not a validated default. All three thresholds are optional and owned by future package configuration.

Explicit -Wl,--build-id=sha1 is required for sampled program builds until the linker-default follow-up is closed. ARMv7 pseudo-probe compilation has a known Clang crash. Some historical inputs exist only in the host archive. No amendment 3 was registered and no new quality matrix/performance test was run for this release.
