# Host-only demo

This demo uses the delivered RPM tool and two synthetic fixtures in the exact sandbox checkout. It does not connect to a board, read captured profiles, or measure performance.

## Run

Set WORKDIR and HQ_TREE to your own absolute paths. EXTRACTED is the directory populated by the RPM extraction in the README; ROOT is the corresponding GBS scratch root. The final argument must be a new directory.

```bash
export TMPDIR="$WORKDIR/temp/tmp"
test "$(awk '/MemAvailable/ {print $2}' /proc/meminfo)" -ge 4194304
nice -n 19 ionice -c3 systemd-run --user --scope \
  -p MemoryMax=3G -p CPUQuota=100% \
  bash "$HQ_TREE/demo/run_host_demo.sh" \
  "$WORKDIR/llvm-release" "$WORKDIR/temp/extracted" \
  "$WORKDIR/temp/GBS-ROOT-LLVM-RELEASE/local/BUILD-ROOTS/scratch.x86_64.0" \
  "$WORKDIR/temp/demo-new"
```

The script requires sandbox tip c8942ae1b53099a78a97dca2b64427af6e58432b. It reads Inputs/ip-mode/a64-pie.perfbin and thumb-count.perfbin with their perfscript texts from that checkout; no LLVM files are copied into hq. It writes extbinary profiles, quality JSON, stdout/stderr and llvm-profdata show output only in the new output directory.

The fixtures have no input-side build-ID evidence. The script explicitly permits missing evidence for this synthetic demo. Identity remains unverified. Real collection should normally require verified identity and must not copy this waiver blindly.

## Expected output

Actually executed on 2026-11-14 with release SHA-256 67ad21faba787d276a80673c1f324f7c0591d28d76bd37a8bd57de0d86426be6; exit 0. No second LLVM build was performed. Both examples have one target sample and one usable sample.

```text
=== a64-pie ===
Function: main: 1, 0, 1 sampled lines
Samples collected in the function's body {
  0: 1
}
No inlined callsites in this function
{"conversion": "ok", "identity": "unverified", "sampling_adequacy": "unknown", "target_samples": 1, "usable_samples": 1, "written_positions": 1}
=== thumb-count ===
Function: main: 1, 0, 1 sampled lines
Samples collected in the function's body {
  0: 1
}
No inlined callsites in this function
{"conversion": "ok", "identity": "unverified", "sampling_adequacy": "unknown", "target_samples": 1, "usable_samples": 1, "written_positions": 1}
```

Measured demo scope wall time: 1.001 seconds; memory.peak: 12,701,696 bytes; no OOM. These are functional demonstration timings, not performance results.

[Back to README](../README.md)
