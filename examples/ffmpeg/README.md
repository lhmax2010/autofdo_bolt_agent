# FFmpeg profiling example

Gerrit project: platform/upstream/ffmpeg. Source baseline:
5fe76358596f66e955f005094e6f34ca525ab23d (FFmpeg 8.0.1).

The supplied [profiling.patch](profiling.patch) applies cleanly to packaging/ffmpeg.spec at that revision. It preserves platform optflags, appends -fdebug-info-for-profiling and -funique-internal-linkage-names, selects -mthumb or -marm for ARMv7, explicitly uses clang and links with -Wl,--build-id=sha1. With with_autofdo=1 it consumes autofdo.extbinary as Source2000, so the profile is available inside the build root rather than referring to a host-only absolute path.

Patch application was checked. Host rpmspec syntax parsing also passed for ARMv7 and AArch64, with and without profile consumption; this is not a target build. Full builds using this newly packaged example, including the profile-consuming variant, are **Not verified**. Earlier equivalent generation flags were tested, but that does not establish acceptance of this example patch or performance gains.

```bash
git clone "ssh://${GERRIT_USER}@review.tizen.org:29418/platform/upstream/ffmpeg" "$PROJECT/ffmpeg"
git -C "$PROJECT/ffmpeg" checkout --detach 5fe76358596f66e955f005094e6f34ca525ab23d
git -C "$PROJECT/ffmpeg" apply --check "$DOCS/examples/ffmpeg/profiling.patch"
git -C "$PROJECT/ffmpeg" apply "$DOCS/examples/ffmpeg/profiling.patch"

# TARGET_CONF must select a matching target repository and Clang 22.1.8.
cd "$PROJECT/ffmpeg"
gbs -c "$TARGET_CONF" build -A armv7l --spec ffmpeg.spec --include-all \
  --buildroot "$PROJECT/build/ffmpeg-baseline" --threads 1 \
  --define '_smp_mflags -j4' --define 'profile_isa thumb'

# After collecting and converting against the packaged baseline:
cp "$PROJECT/results/profile.extbinary" packaging/autofdo.extbinary
sha256sum packaging/autofdo.extbinary
gbs -c "$TARGET_CONF" build -A armv7l --spec ffmpeg.spec --include-all \
  --buildroot "$PROJECT/build/ffmpeg-autofdo" --threads 1 \
  --define '_smp_mflags -j4' --define 'profile_isa thumb' --define 'with_autofdo 1'
```

Use -A aarch64 for RPi5; the patch does not add ARMv7 ISA switches there. For RPi4 A32 use profile_isa a32. --include-all includes the local spec patch and Source2000; keep this checkout free of unrelated files. Use fresh roots and distinguish the resulting baseline/optimized RPMs by output directory and checksums.

A currently available target-repository configuration that reproduces the historical FFmpeg dependency set is **Not documented yet**. The x86_64 LLVM-tool configuration is not a validated substitute for target FFmpeg configuration. Before building, verify clang --version and required target dependencies in the selected GBS environment. No target build was executed for this documentation update.

Do not infer correctness from a successful compile alone: inspect actual flags, runtime/debug build IDs, consumer coverage diagnostics and decoded-output checksums. Performance gains not yet validated.
