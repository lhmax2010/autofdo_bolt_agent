#!/bin/bash
set -u
child=
sampler=
finish() { rc=$?; trap - EXIT; if test -n "$child"; then kill -TERM "$child" 2>/dev/null || :; wait "$child" 2>/dev/null || :; fi; if test -n "$sampler"; then kill -TERM "$sampler" 2>/dev/null || :; wait "$sampler" 2>/dev/null || :; fi; printf "%s\n" "$rc" > /opt/afdo_agent/work/m1-ffmpeg-rpi4-thumb-01/control-formal-sintel-1080p-60-8-try0-AFDO/exit; }
trap finish EXIT
trap "exit 143" TERM
trap "exit 130" INT
printf "%s\n" "$$" > /opt/afdo_agent/work/m1-ffmpeg-rpi4-thumb-01/control-formal-sintel-1080p-60-8-try0-AFDO/pid
export LD_LIBRARY_PATH=/opt/afdo_agent/variants/m1-ffmpeg-rpi4-thumb-01-AFDO/usr/lib:/opt/afdo_agent/lib
export DEPLOY_MANIFEST=/opt/afdo_agent/tools/workflow-m1-ffmpeg-rpi4-thumb-01/AFDO-manifest.json
if test -n "${WF_STANDALONE_SAMPLER:-}"; then taskset -c 0 bash "$WF_STANDALONE_SAMPLER" /opt/afdo_agent/work/m1-ffmpeg-rpi4-thumb-01/control-formal-sintel-1080p-60-8-try0-AFDO/telemetry.tsv "$WF_CAPABILITIES" & sampler=$!; sleep 1; fi
bash /opt/afdo_agent/tools/workflow-m1-ffmpeg-rpi4-thumb-01/measure.sh /opt/afdo_agent/work/m1-ffmpeg-rpi4-thumb-01/formal-sintel-1080p-60-8-try0-AFDO /opt/afdo_agent/tools/perf 3 0 /opt/afdo_agent/tools/workflow-m1-ffmpeg-rpi4-thumb-01/capabilities.tsv 600 bash /opt/afdo_agent/tools/workflow-m1-ffmpeg-rpi4-thumb-01/timed.sh test-secondary /opt/afdo_agent/variants/m1-ffmpeg-rpi4-thumb-01-AFDO /opt/afdo_agent/inputs/sintel_1080p_h264_60s.mp4 /opt/afdo_agent/work/m1-ffmpeg-rpi4-thumb-01/formal-sintel-1080p-60-8-try0-AFDO/result & child=$!
wait "$child"; rc=$?
child=
if test -n "$sampler"; then sleep 2; fi
exit "$rc"
