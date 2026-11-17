#!/bin/bash
set -u
bash /opt/afdo_agent/tools/workflow-m1-ffmpeg-rpi4-thumb-01/watchdog.sh 600 bash /opt/afdo_agent/tools/workflow-m1-ffmpeg-rpi4-thumb-01/oracle.sh /opt/afdo_agent/work/m1-ffmpeg-rpi4-thumb-01/PLAT-bbb-720p-60 PLAT /opt/afdo_agent/inputs/bbb_720p_h264_60s.mp4
rc=$?
printf "%s\n" "$rc" > /opt/afdo_agent/work/m1-ffmpeg-rpi4-thumb-01/control-PLAT-bbb-720p-60/exit
exit "$rc"
