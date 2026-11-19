#!/bin/sh
export LC_ALL=C
echo "WATCH_ROOT $$"
snapshot() {
 printf 'TREE '; cut -d' ' -f1 /proc/uptime
 printf 'LOAD '; cat /proc/loadavg
 printf 'FREQ '; cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq
 printf 'SDB_TCP '; awk 'NR>1 && toupper($2) ~ /:65F5$/ && $4=="01" {n++} END {print n+0}' /proc/net/tcp /proc/net/tcp6
 ps -eo pid,ppid,user:24,pcpu,time,comm
 echo TREE_END
}
snapshot
"$@" &
job=$!
echo "WORK_ROOT $job"
while kill -0 "$job" 2>/dev/null; do
 snapshot
 if test -f "$PWD/pmumon.start"; then
  # Compare new kernel log lines against the last pre-stage uptime.
  newest="$(cat "$PWD/pmumon.start")"
  dmesg | awk -v start="$newest" '/\[PMUMON\]/ && tolower($0) ~ /error|failed|failure|fatal|overflow warning/ {
   t=$0; sub(/^\[[[:space:]]*/, "", t); sub(/\].*/, "",t); if ((t+0)>start) print
  }' > "$PWD/pmumon.live-errors"
  if test -s "$PWD/pmumon.live-errors"; then
   cat "$PWD/pmumon.live-errors"
   echo "PMUMON_LIVE_ERROR"
   kill -INT "$job" 2>/dev/null
   wait "$job"
   exit 92
  fi
 fi
 sleep 1
done
wait "$job"
rc=$?
snapshot
exit "$rc"
