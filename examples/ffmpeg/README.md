# FFmpeg profiling example

Gerrit project: platform/upstream/ffmpeg. Source baseline:
5fe76358596f66e955f005094e6f34ca525ab23d (FFmpeg 8.0.1).

The [profiling.patch](profiling.patch) preserves platform optflags, appends -fdebug-info-for-profiling and -funique-internal-linkage-names, selects -mthumb or -marm for ARMv7, explicitly uses clang and links with -Wl,--build-id=sha1. The added --enable-thumb and --disable-thumb values end with a space because the original spec appends --extra-cflags without a leading separator. Patch SHA-256: 0c94e54d252ad1ecbc625f629af090b257edba4cd3753d76352fd031486243b6.

ARMv7 Thumb and A32 baseline builds are **Verified**: fresh roots, normal non-incremental GBS, 23 binary RPMs per variant, exit 0. Packaged libavcodec/libavutil runtime and debuginfo build IDs match, and readelf reads their debug information and line tables. A later [manual Thumb pilot](../../docs/03_reports/m1_ffmpeg_rpi4_thumb_pilot.md) also verified profile consumption, two-video correctness and a paired performance result. **Thumb profile consumption is Verified**. **A32 profile consumption and AArch64 builds/profile consumption remain Not verified**.

## Configuration and baseline builds

Use [ffmpeg-target.conf.in](../gbs/ffmpeg-target.conf.in). All effective GBS fields are included, with filesystem paths replaced by @PROJECT@. Tested repositories:

- Base: tizen-base-toolchain_20261030.120529.
- Unified: tizen-unified-toolchain_20261104.125239.
- Target clang package: 22.1.8-4.1; rpm-build: 4.14.1.1-1.9.

Set PROJECT to an absolute writable project directory and DOCS to this documentation directory. Source access requires existing Gerrit credentials. No credentials are included.

~~~bash
export PROJECT=/path/to/project
export DOCS=/path/to/this/documentation
export GERRIT_USER=your_gerrit_account
mkdir -p "$PROJECT/scratch/ffmpeg-gbs-tmp" "$PROJECT/build"
python3 - "$DOCS/examples/gbs/ffmpeg-target.conf.in" \
  "$PROJECT/ffmpeg-target.conf" "$PROJECT" <<'PYCONFIG'
from pathlib import Path
import sys
Path(sys.argv[2]).write_text(Path(sys.argv[1]).read_text().replace("@PROJECT@", sys.argv[3]))
PYCONFIG
export TARGET_CONF="$PROJECT/ffmpeg-target.conf"

git clone "ssh://$GERRIT_USER@review.tizen.org:29418/platform/upstream/ffmpeg" "$PROJECT/ffmpeg"
git -C "$PROJECT/ffmpeg" checkout --detach 5fe76358596f66e955f005094e6f34ca525ab23d
git -C "$PROJECT/ffmpeg" apply --check "$DOCS/examples/ffmpeg/profiling.patch"
git -C "$PROJECT/ffmpeg" apply "$DOCS/examples/ffmpeg/profiling.patch"
cd "$PROJECT/ffmpeg"
gbs -c "$TARGET_CONF" build -A armv7l --spec ffmpeg.spec --include-all \
  --buildroot "$PROJECT/build/ffmpeg-thumb" --threads 1 \
  --define '_smp_mflags -j2' --define 'profile_isa thumb'
# Run after Thumb completes, with a separate fresh root.
gbs -c "$TARGET_CONF" build -A armv7l --spec ffmpeg.spec --include-all \
  --buildroot "$PROJECT/build/ffmpeg-a32" --threads 1 \
  --define '_smp_mflags -j2' --define 'profile_isa a32'
~~~

These are ordinary GBS invocations; use the host's configured build environment. Keep V, MAKEFLAGS and MFLAGS free of unintended overrides. Resource controls are optional wrappers around the same command, for example:

~~~bash
nice -n 19 ionice -c3 systemd-run --user --scope \
  -p MemoryMax=6G -p MemoryHigh=5G -p CPUQuota=200% \
  gbs -c "$TARGET_CONF" build -A armv7l --spec ffmpeg.spec --include-all \
    --buildroot "$PROJECT/build/ffmpeg-thumb-limited" --threads 1 \
    --define '_smp_mflags -j2' --define 'profile_isa thumb'
~~~

Choose either the plain invocation or the optional wrapper, not both for the same output root. The measured runs used serial builds, at least 16 GiB available RAM and 50 GiB free disk at startup. A scope limits resources but is not a complete monitoring or retry service. Select limits appropriate to the host and retain exit codes and resource logs.

Measured wall times, including fresh-root dependency setup, were **303.08 seconds (Thumb)** and **314.09 seconds (A32)**. Peak build cgroup memory was about 2.05 GiB; no OOM or resource-triggered restart occurred. Times depend on host load, network and caches.

Do not put V=1 in _smp_mflags: RPM also passes that macro to find-debuginfo.sh, which can interpret V=1 as a directory. Accepted commands use only -j2. Verbose compile commands for the same patched spec confirmed both profiling flags and the correct effective ISA for C sources. Handwritten assembly uses separate flags and can retain its own ISA state.

Snapshots can be deleted. Preserve dependencies from the first build and use the archived-set procedure below for later builds of the same experiment. If the archive is incomplete and its snapshot is gone, a new fixed repository combination requires a new experiment with both control and candidate rebuilt. Do not pair a new candidate with an old control. This template is verified for ARMv7 only.

## Verify packaged identities and debug information

~~~bash
RPM_DIR="$PROJECT/build/ffmpeg-thumb/local/repos/tizen_unified_standard/armv7l/RPMS"
sha256sum "$RPM_DIR"/*.rpm
EXTRACT="$PROJECT/extracted/ffmpeg-thumb"
mkdir -p "$EXTRACT"
set -o pipefail
for package in libavcodec libavcodec-debuginfo libavutil libavutil-debuginfo; do
  rpm2cpio "$RPM_DIR/$package-8.0.1-1.armv7l.rpm" |
    (cd "$EXTRACT" && cpio -idm --no-absolute-filenames)
done
readelf -n "$EXTRACT/usr/lib/libavcodec.so.62.11.100"
readelf -n "$EXTRACT/usr/lib/debug/usr/lib/libavcodec.so.62.11.100.debug"
readelf -n "$EXTRACT/usr/lib/libavutil.so.60.8.100"
readelf -n "$EXTRACT/usr/lib/debug/usr/lib/libavutil.so.60.8.100.debug"
readelf -SW "$EXTRACT/usr/lib/debug/usr/lib/libavcodec.so.62.11.100.debug"
readelf --debug-dump=info "$EXTRACT/usr/lib/debug/usr/lib/libavcodec.so.62.11.100.debug" \
  > "$PROJECT/extracted/thumb-info.txt"
readelf --debug-dump=rawline "$EXTRACT/usr/lib/debug/usr/lib/libavcodec.so.62.11.100.debug" \
  > "$PROJECT/extracted/thumb-lines.txt"
~~~

Repeat for A32 using separate extraction/output directories, and check both libraries. Require equal 40-hex-digit build IDs for runtime/debug pairs. Debug dumps can be large. Tested packaged IDs:

| Variant | Library | Runtime = debug SHA-1 build ID |
|---|---|---|
| Thumb | libavcodec | 805376f248504d2084e3e95470810873ffc3655a |
| Thumb | libavutil | bb5b41f743b9b07bb38cc5007f7deb6516256579 |
| A32 | libavcodec | bdc2a972e0bb357ca144d082f72519e7bed19813 |
| A32 | libavutil | 2f63cff726697e7395f75d14c0f96b43e14a6a58 |

Both variants contain mixed DWARF: libavcodec has 313 version-4 and 52 version-5 compilation units; libavutil has 99 version-4 and 2 version-5 units. readelf successfully read .debug_info and .debug_line. No standalone llvm-profgen load-only check was performed.

## Building from an archived dependency set

The Thumb pilot rebuilt successfully in fresh roots using the original 108 downloaded dependency packages. BASE-r took 120.02 seconds and AFDO 124.34 seconds. All six BASE-r runtime libraries were byte-identical to BASE. The archive is reusable after online snapshots disappear; keeping only the FFmpeg output RPMs is not sufficient.

Retain the resolved buildconf, the actual dependency RPMs and their checksums from the first baseline build. For the tested GBS layout, dependencies are under the fresh root's local/cache directories and the resolved configuration is in the scratch build root. Use only a root belonging to this experiment, with the complete union of dependencies needed by its variants. The following copies existing files; it does not download missing packages:

~~~bash
export BASE_ROOT="$PROJECT/build/ffmpeg-thumb"
export FROZEN="$PROJECT/archive/ffmpeg-thumb-deps"
mkdir -p "$FROZEN"
python3 - "$BASE_ROOT/local/cache" "$FROZEN" <<'PYARCHIVE'
from pathlib import Path
import hashlib, shutil, sys
cache, dest = map(Path, sys.argv[1:])
def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()
packages = sorted(cache.rglob("*.rpm"))
if not packages:
    raise SystemExit("No cached dependency RPMs; stop")
for package in packages:
    target = dest / package.name
    if target.exists() and digest(target) != digest(package):
        raise SystemExit("Conflicting cached RPM: " + package.name)
    shutil.copy2(package, target)
    if digest(target) != digest(package):
        raise SystemExit("Archive checksum mismatch: " + package.name)
PYARCHIVE
cp "$BASE_ROOT/local/BUILD-ROOTS/scratch.armv7l.0/tizen_unified_standard.conf" \
  "$FROZEN/tizen_unified_standard.conf"
(cd "$FROZEN" && sha256sum ./*.rpm tizen_unified_standard.conf > SHA256SUMS)
createrepo_c --workers 2 "$FROZEN"
(cd "$FROZEN" && sha256sum -c SHA256SUMS)

cd "$PROJECT/ffmpeg"
gbs -c "$TARGET_CONF" build -A armv7l --spec ffmpeg.spec --include-all \
  --skip-conf-repos -R "$FROZEN" -D "$FROZEN/tizen_unified_standard.conf" \
  --buildroot "$PROJECT/build/ffmpeg-base-r-frozen" --threads 1 \
  --define '_smp_mflags -j2' --define 'profile_isa thumb'
~~~

Use a new archive directory and fresh build roots. createrepo_c must already be available. Keep snapshot IDs, resolution time and the exact installed package manifest alongside the archive. Reject an incomplete archive instead of fetching replacement versions. --skip-conf-repos prevents use of configuration repositories; -R names the local package directory and -D supplies the resolved build configuration. In the tested GBS version, putting a file:// URL in the configuration alone failed repository/build metadata resolution. The explicit -R/-D invocation succeeded.

A cache can contain packages not used by the build if its root was reused. Start with a fresh baseline root, identify the actual downloaded set, and compare each subsequent build root's installed records, including header hashes:

~~~bash
mkdir -p "$PROJECT/results"
rpm --root "$PROJECT/build/ffmpeg-base-r-frozen/local/BUILD-ROOTS/scratch.armv7l.0" \
  -qa --qf '%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH} %{SHA256HEADER}\n' | sort \
  > "$PROJECT/results/base-r-packages.txt"
~~~

Use the same read-only query for the original BASE and AFDO roots, with separate output files, then compare them line by line. Reading the RPM database may require the privileges used for GBS. Also compare source/patch/spec hashes, relative source paths, resolved buildconf and compile/link argument multisets. Normalize only explicitly declared candidate options. If BASE-r is not byte-identical to BASE, record the difference and use a newly validated BASE-r as the control; do not silently reuse the old control.

## Profile consumption: Thumb Verified

With with_autofdo=1 the unchanged spec consumes packaging/autofdo.extbinary as Source2000 inside the build root. The Thumb pilot used the frozen dependencies above and the locked profile SHA 61f03b59262e3ce7ce758219d65848a33b5a0549131c362a6769ad10386f2cf2.

~~~bash
mkdir -p "$PROJECT/results"
cp "$PROJECT/results/profile.extbinary" "$PROJECT/ffmpeg/packaging/autofdo.extbinary"
sha256sum "$PROJECT/ffmpeg/packaging/autofdo.extbinary"
cd "$PROJECT/ffmpeg"
gbs -c "$TARGET_CONF" build -A armv7l --spec ffmpeg.spec --include-all \
  --skip-conf-repos -R "$FROZEN" -D "$FROZEN/tizen_unified_standard.conf" \
  --buildroot "$PROJECT/build/ffmpeg-afdo-frozen" --threads 1 \
  --define '_smp_mflags -j2' --define 'profile_isa thumb' --define 'with_autofdo 1'
~~~

The input is the package profile: merge repeated runs per target library, check cross-library function/context collisions, then merge the libraries in a recorded order. Keep the checkout free of unrelated files because --include-all includes the spec change and Source2000. Preserve source-relative paths and all non-profile compiler options.

Verify actual consumption, rather than treating an absence of warnings as proof:

1. Compare installed packages and normalized compiler/linker argv with BASE-r. In the pilot, both command lists had 698 entries; 627 AFDO commands contained -fprofile-sample-use, and all remaining arguments matched as multisets.
2. Hash the profile in the build root's rpmbuild/SOURCES directory and match the locked input. Read that path from the recorded compiler command, without substituting another host file.
3. Extract runtime and debuginfo packages and use the readelf -n checks above. Each pair must match; AFDO target IDs must differ from BASE. Compare .text SHA-256 as additional evidence of generated-code change.
4. Record profile warnings and coverage diagnostics under the selected experiment policy. The pilot's default compiler output had no profile-related warnings, but no extra coverage-warning options were enabled; sampling adequacy was not established.
5. Verify the variant paths in every decoder process's maps and tie library checksums/build IDs to the deployment manifest. Require the independent correctness oracle to pass before timing.

| Library | BASE build ID | AFDO build ID |
|---|---|---|
| libavcodec | 805376f248504d2084e3e95470810873ffc3655a | 5aef89343bc6a870b6760c3d492206bbb8adc286 |
| libavutil | bb5b41f743b9b07bb38cc5007f7deb6516256579 | 1908c55105184d14beeb1e7076816dd1c994658c |

Both .text hashes changed, while runtime/debug IDs matched within each variant. Verbose command-recording builds produced identical artifacts to their corresponding measured builds. When extra command evidence is required, use a separate build with --define '__make /usr/bin/make V=1' and prove artifact equality; never put V=1 into _smp_mflags.

## Known limitations

Each successful ARMv7 build emitted eight debugedit diagnostics: "DWARF version 5 unhandled" and "Unknown debugging section .debug_line_str", for libavcodec, libavutil, libswresample and libswscale. They were nonfatal. Packaged build IDs and readable debug/line sections were verified for libavcodec and libavutil; this is not proof that all version-5 source paths were rewritten correctly or debugsource is complete.

A32 profile consumption and AArch64 builds/profile consumption remain **Not verified**. The measured result applies only to RPi4 Thumb, two-video correctness and a single ToS test workload. The test video was previously used in tool development, firmware throttle history was unavailable, and two telemetry records were incomplete. Workflow automation is **Planned; not implemented**. Detailed raw evidence is retained by the project team.
