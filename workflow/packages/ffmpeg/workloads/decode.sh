#!/bin/bash
# Untimed correctness hook; fixed pipeline, actual bytes/frames/hash, JSON output.
set -eu
set -o pipefail
role=$1; variant=$2; input=$3; result=$4
case "$variant:$input:$result" in /opt/afdo_agent/*:/opt/afdo_agent/*:/opt/afdo_agent/*) ;; *) exit 2;; esac
case "$variant:$input:$result" in *'/../'*|*'/..') exit 2;; esac
case "$role" in train|pilot|test|tuning|conformance) ;; *) exit 2;; esac
test ! -e "$result"; test ! -e "$result.i420"
export LD_LIBRARY_PATH="$variant/usr/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
TIMEFORMAT='%R'
{ time gst-launch-1.0 -e filesrc "location=$input" '!' qtdemux '!' h264parse '!' avdec_h264 max-threads=1 '!' video/x-raw,format=I420,width=1280,height=720,framerate=30/1 '!' filesink "location=$result.i420" > "$result.decode.log" 2>&1; } 2> "$result.seconds"
grep -q 'Got EOS' "$result.decode.log"
bytes=$(stat -c '%s' "$result.i420")
seconds=$(cat "$result.seconds")
case "$bytes" in ''|*[!0-9]*) exit 3;; esac
case "$seconds" in ''|*[!0-9.]*) exit 3;; esac
test "$bytes" -gt 0; test "$((bytes % 1382400))" -eq 0
frames=$((bytes / 1382400))
digest=$(sha256sum "$result.i420"); digest=${digest%% *}
printf '{"status":"ok","eos":true,"frames":%s,"bytes":%s,"digest":"%s","metric_value":%s,"metric_unit":"seconds"}\n' "$frames" "$bytes" "$digest" "$seconds" > "$result"
# Caps/threads are fixed above and are recorded by the host oracle adapter.
