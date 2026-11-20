#!/bin/bash
# Streaming oracle: no multi-gigabyte raw file is retained on the board.
set -euo pipefail
here=${0%/*}; . "$here/common.sh"
out=$1; variant=$2; input=$3
safe_path "$out"; safe_path "$input"
test ! -e "$out"; mkdir -p "$out"
export HOME="$out" TMPDIR="$out" XDG_CACHE_HOME="$out/cache" GST_REGISTRY_1_0="$out/registry.bin" LC_ALL=C
if test "$variant" = PLAT; then unset LD_LIBRARY_PATH; else
    safe_path "$variant"; export LD_LIBRARY_PATH="$variant/${WF_RUNTIME_LIB:-usr/lib}:${WF_PERF_LIB:-/opt/afdo_agent/lib}"
fi
hp=''; cp=''; gp=''
cleanup() {
    rc=$?; trap - EXIT
    for p in "$hp" "$cp" "$gp"; do
        if test -n "$p"; then kill "$p" 2>/dev/null || :; wait "$p" 2>/dev/null || :; fi
    done
    rm -f "$out/raw.pipe" "$out/hash.pipe"
    exit "$rc"
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
mkfifo "$out/raw.pipe" "$out/hash.pipe"
sha256sum "$out/hash.pipe" > "$out/decoded.sha256" & hp=$!
(tee "$out/hash.pipe" < "$out/raw.pipe" | wc -c > "$out/decoded.bytes") & cp=$!
gst-launch-1.0 -v filesrc "location=$input" '!' qtdemux '!' h264parse '!' avdec_h264 max-threads=1 '!' video/x-raw,format=I420 '!' identity name=framecounter silent=false '!' filesink "location=$out/raw.pipe" sync=false > "$out/gst.log" 2>&1 & gp=$!
for ((i=0;i<500;i++)); do
    if test -r "/proc/$gp/maps" && grep -q libavcodec.so "/proc/$gp/maps" && grep -q libavutil.so "/proc/$gp/maps"; then
        cat "/proc/$gp/maps" > "$out/decoder.maps"; break
    fi
    kill -0 "$gp" 2>/dev/null || break
    sleep .02
done
wait "$gp"; gp=''
wait "$cp"; cp=''
wait "$hp"; hp=''
grep -q 'Got EOS' "$out/gst.log"
test -s "$out/decoder.maps"
grep -c 'last-message = chain' "$out/gst.log" > "$out/decoded.frames"
awk 'NF>=6 && $6 ~ /^\/opt\/afdo_agent\// {print $6}' "$out/decoder.maps" | sort -u |
while IFS= read -r path; do sha256sum "$path"; done > "$out/mapped-sha256.txt"
