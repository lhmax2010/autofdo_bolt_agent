#!/bin/bash
set -Eeuo pipefail
R=/opt/afdo_agent/work/m1p-v02-20261116
name=$1; input=$2; variant=$3
O=$R/$name
mkdir "$O" "$O/home" "$O/tmp" "$O/cache"
export HOME=$O/home TMPDIR=$O/tmp XDG_CACHE_HOME=$O/cache GST_REGISTRY_1_0=$O/registry.bin LC_ALL=C
case "$variant" in PLAT) unset LD_LIBRARY_PATH ;; BASE) export LD_LIBRARY_PATH=/opt/afdo_agent/variants/m1p-base/lib ;; AFDO) export LD_LIBRARY_PATH=/opt/afdo_agent/variants/m1p-afdo/lib ;; *) exit 2 ;; esac
hp=;cp=;gp=
cleanup() { rc=$?; trap - EXIT; for p in "$hp" "$cp" "$gp"; do [[ -z $p ]] || { kill "$p" 2>/dev/null || true; wait "$p" 2>/dev/null || true; }; done; rm -f "$O/raw.pipe" "$O/hash.pipe"; exit "$rc"; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM HUP
mkfifo "$O/raw.pipe" "$O/hash.pipe"
sha256sum "$O/hash.pipe" > "$O/decoded.sha256" & hp=$!
(tee "$O/hash.pipe" < "$O/raw.pipe" | wc -c > "$O/decoded.bytes") & cp=$!
gst-launch-1.0 -v filesrc location="$input" ! qtdemux ! h264parse ! avdec_h264 max-threads=1 ! video/x-raw,format=I420 ! identity name=framecounter silent=false ! filesink location="$O/raw.pipe" sync=false > "$O/gst.log" 2>&1 & gp=$!
for ((i=0;i<500;i++)); do
 if [[ -r /proc/$gp/maps ]] && grep -q 'libavcodec.so' /proc/$gp/maps && grep -q 'libavutil.so' /proc/$gp/maps; then cat /proc/$gp/maps > "$O/decoder.maps"; break; fi
 kill -0 "$gp" 2>/dev/null || break
 sleep .02
done
wait "$gp"; gp=
wait "$cp"; cp=
wait "$hp"; hp=
grep -q 'Got EOS' "$O/gst.log"
test -s "$O/decoder.maps"
grep -c 'last-message = chain' "$O/gst.log" > "$O/frame-notifications.count" || true
cat "$O/decoded.sha256" "$O/decoded.bytes" "$O/frame-notifications.count"
