#!/bin/bash
# Fixed-argv workload; machine result is produced/validated by host oracle adapter.
set -eu
role=$1; variant=$2; input=$3; result=$4
case "$variant:$input:$result" in /opt/afdo_agent/*:/opt/afdo_agent/*:/opt/afdo_agent/*) ;; *) exit 2;; esac
export LD_LIBRARY_PATH="$variant/${WF_RUNTIME_LIB:-usr/lib}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
case "$role" in train|pilot|test|test-secondary|tuning|conformance) ;; *) exit 2;; esac
# Do not fabricate frames/digest from stdout. The caller must supply oracle
# extraction for untimed filesink runs; a bare fakesink run is not an oracle.
exec gst-launch-1.0 -e filesrc "location=$input" '!' qtdemux '!' h264parse '!' avdec_h264 max-threads=1 '!' video/x-raw,format=I420 '!' fakesink sync=false
