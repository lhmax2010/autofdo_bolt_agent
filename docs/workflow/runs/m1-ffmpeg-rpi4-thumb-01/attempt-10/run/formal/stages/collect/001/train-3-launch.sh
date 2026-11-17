#!/bin/bash
set -u
child=
sampler=
finish() { rc=$?; trap - EXIT; if test -n "$child"; then kill -TERM "$child" 2>/dev/null || :; wait "$child" 2>/dev/null || :; fi; if test -n "$sampler"; then kill -TERM "$sampler" 2>/dev/null || :; wait "$sampler" 2>/dev/null || :; fi; printf "%s\n" "$rc" > /opt/afdo_agent/work/m1-ffmpeg-rpi4-thumb-01/control-train-3/exit; }
trap finish EXIT
trap "exit 143" TERM
trap "exit 130" INT
printf "%s\n" "$$" > /opt/afdo_agent/work/m1-ffmpeg-rpi4-thumb-01/control-train-3/pid
export LD_LIBRARY_PATH=/opt/afdo_agent/variants/m1-ffmpeg-rpi4-thumb-01-BASE/usr/lib:/opt/afdo_agent/lib
export DEPLOY_MANIFEST=/opt/afdo_agent/tools/workflow-m1-ffmpeg-rpi4-thumb-01/BASE-manifest.json
export WF_STANDALONE_SAMPLER=/opt/afdo_agent/tools/workflow-m1-ffmpeg-rpi4-thumb-01/telemetry.sh
export WF_CAPABILITIES=/opt/afdo_agent/tools/workflow-m1-ffmpeg-rpi4-thumb-01/capabilities.tsv
if test -n "${WF_STANDALONE_SAMPLER:-}"; then taskset -c 0 bash "$WF_STANDALONE_SAMPLER" /opt/afdo_agent/work/m1-ffmpeg-rpi4-thumb-01/control-train-3/telemetry.tsv "$WF_CAPABILITIES" & sampler=$!; sleep 1; fi
bash /opt/afdo_agent/tools/workflow-m1-ffmpeg-rpi4-thumb-01/collect.sh /opt/afdo_agent/work/m1-ffmpeg-rpi4-thumb-01/train-3 /opt/afdo_agent/tools/perf 1000003 3 600 bash /opt/afdo_agent/tools/workflow-m1-ffmpeg-rpi4-thumb-01/timed.sh train /opt/afdo_agent/variants/m1-ffmpeg-rpi4-thumb-01-BASE /opt/afdo_agent/inputs/bbb_720p_h264_60s.mp4 /opt/afdo_agent/work/m1-ffmpeg-rpi4-thumb-01/train-3/result & child=$!
wait "$child"; rc=$?
child=
if test -n "$sampler"; then sleep 2; fi
exit "$rc"
