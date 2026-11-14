# FFmpeg profiling example

Gerrit project: platform/upstream/ffmpeg. Source baseline:
5fe76358596f66e955f005094e6f34ca525ab23d (FFmpeg 8.0.1).

The [profiling.patch](profiling.patch) preserves platform optflags, appends -fdebug-info-for-profiling and -funique-internal-linkage-names, selects -mthumb or -marm for ARMv7, explicitly uses clang and links with -Wl,--build-id=sha1. The added --enable-thumb and --disable-thumb values end with a space because the original spec appends --extra-cflags without a leading separator. Patch SHA-256: 0c94e54d252ad1ecbc625f629af090b257edba4cd3753d76352fd031486243b6.

ARMv7 Thumb and A32 baseline builds are **Verified**: fresh roots, normal non-incremental GBS, 23 binary RPMs per variant, exit 0. Packaged libavcodec/libavutil runtime and debuginfo build IDs match, and readelf reads their debug information and line tables. This does not establish runtime decoding correctness or performance gains. AArch64 and profile-consuming builds remain **Not verified**.

## Configuration and baseline builds

Use [ffmpeg-target.conf.in](../gbs/ffmpeg-target.conf.in). All effective GBS fields are included, with filesystem paths replaced by @PROJECT@. Tested repositories:

- Base: tizen-base-toolchain_20261030.120529.
- Unified: tizen-unified-toolchain_20261104.125239.
- Target clang package: 22.1.8-4.1; rpm-build: 4.14.1.1-1.9.

Set PROJECT to an absolute writable project directory and DOCS to this documentation directory. Source access requires existing Gerrit credentials. No credentials are included.

~~~bash
mkdir -p "$PROJECT/scratch/ffmpeg-gbs-tmp" "$PROJECT/scratch/ffmpeg-tmp" \
  "$PROJECT/scratch/ffmpeg-home" "$PROJECT/scratch/ffmpeg-cache" \
  "$PROJECT/scratch/ffmpeg-config" "$PROJECT/scratch/ffmpeg-state" "$PROJECT/build"
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

build_baseline() {
  isa="$1"
  nice -n 19 ionice -c3 systemd-run --user --scope \
    -p MemoryMax=6G -p MemoryHigh=5G -p CPUQuota=200% \
    env -u V -u MAKEFLAGS -u MFLAGS \
    HOME="$PROJECT/scratch/ffmpeg-home" TMPDIR="$PROJECT/scratch/ffmpeg-tmp" \
    TMP="$PROJECT/scratch/ffmpeg-tmp" TEMP="$PROJECT/scratch/ffmpeg-tmp" \
    XDG_CACHE_HOME="$PROJECT/scratch/ffmpeg-cache" \
    XDG_CONFIG_HOME="$PROJECT/scratch/ffmpeg-config" \
    XDG_STATE_HOME="$PROJECT/scratch/ffmpeg-state" \
    CCACHE_DIR="$PROJECT/scratch/ffmpeg-cache/ccache" \
    GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_COUNT=2 \
    GIT_CONFIG_KEY_0=gc.auto GIT_CONFIG_VALUE_0=0 \
    GIT_CONFIG_KEY_1=maintenance.auto GIT_CONFIG_VALUE_1=false \
    SUDO_ASKPASS=/bin/false \
    gbs -c "$TARGET_CONF" build -A armv7l --spec ffmpeg.spec --include-all \
      --buildroot "$PROJECT/build/ffmpeg-$isa" --threads 1 \
      --define '_smp_mflags -j2' --define "profile_isa $isa"
}
build_baseline thumb
# Recheck resource headroom before the second build.
build_baseline a32
~~~

Run serially with fresh roots. Before each build, require MemAvailable >=16 GiB, one-minute load < nproc * 0.6, and free project disk >=50 GiB. Monitor every 60 seconds. Stop only the build's own scope if MemAvailable is below 6 GiB twice consecutively or disk free falls below 20 GiB. Do not interfere with other builds. The commands above show the invocation, not an unattended monitoring/retry service.

Measured wall times, including fresh-root dependency setup, were **303.08 seconds (Thumb)** and **314.09 seconds (A32)**. Peak build cgroup memory was about 2.05 GiB; no OOM or resource-triggered restart occurred. Times depend on host load, network and caches.

Do not put V=1 in _smp_mflags: RPM also passes that macro to find-debuginfo.sh, which can interpret V=1 as a directory. Accepted commands use only -j2. Verbose compile commands for the same patched spec confirmed both profiling flags and the correct effective ISA for C sources. Handwritten assembly uses separate flags and can retain its own ISA state.

Snapshots can be deleted. Check packages/repodata/repomd.xml before building. If removed, select available fixed repositories, record versions, and repeat build-ID/debug-information and functional checks. Do not assume host-tool configuration is evidence of a target build. This template is verified for ARMv7 only.

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

## Profile consumption: Not verified

With with_autofdo=1 the spec consumes autofdo.extbinary as Source2000 inside the build root. Syntax expansion was checked; a full consuming build was not run.

~~~bash
cp "$PROJECT/results/profile.extbinary" "$PROJECT/ffmpeg/packaging/autofdo.extbinary"
sha256sum "$PROJECT/ffmpeg/packaging/autofdo.extbinary"
cd "$PROJECT/ffmpeg"
# Use the same isolated HOME/TMPDIR and resource controls as for the baseline.
gbs -c "$TARGET_CONF" build -A armv7l --spec ffmpeg.spec --include-all \
  --buildroot "$PROJECT/build/ffmpeg-autofdo" --threads 1 \
  --define '_smp_mflags -j2' --define 'profile_isa thumb' --define 'with_autofdo 1'
~~~

Keep the checkout free of unrelated files: --include-all includes the spec change and Source2000. Compare decoded-output checksums and consumer coverage diagnostics before performance conclusions. Performance gains not yet validated.

## Known limitations

Each successful ARMv7 build emitted eight debugedit diagnostics: "DWARF version 5 unhandled" and "Unknown debugging section .debug_line_str", for libavcodec, libavutil, libswresample and libswscale. They were nonfatal. Packaged build IDs and readable debug/line sections were verified for libavcodec and libavutil; this is not proof that all version-5 source paths were rewritten correctly or debugsource is complete.

AArch64 and profile-consuming builds remain **Not verified**. No board deployment, decoding test or performance measurement was performed for these outputs. Detailed raw evidence is retained by the project team.
