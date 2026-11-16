#!/bin/bash
set -Eeuo pipefail
ROOT=/opt/afdo_agent; W=$ROOT/work/m1p-v02-20261116; R=$W/train-$1
mkdir "$R" "$R/home" "$R/tmp" "$R/cache" "$R/buildid" "$R/maps"
export HOME=$R/home TMPDIR=$R/tmp XDG_CACHE_HOME=$R/cache GST_REGISTRY_1_0=$R/registry.bin GST_REGISTRY_UPDATE=no PERF_CONFIG=$R/perf.conf LC_ALL=C LD_LIBRARY_PATH=$ROOT/variants/m1p-base/lib:$ROOT/lib
cp "$W/base-bbb/registry.bin" "$R/registry.bin"
tp=;mp=;pp=
cleanup() { rc=$?; trap - EXIT; for p in "$tp" "$mp" "$pp"; do [[ -z $p ]] || { kill "$p" 2>/dev/null || true; wait "$p" 2>/dev/null || true; }; done; echo "$rc" > "$R/exit"; exit "$rc"; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM HUP
for ((i=0;i<=20;i++)); do
 hot=0
 for z in /sys/class/thermal/thermal_zone*/temp; do t=$(cat "$z"); ((t<=60000)) || hot=1; done
 ((hot==0)) && break
 ((i<20)) || exit 44
 sleep 30
done
# Both observer processes pinned to CPU0. Every observation carries /proc/uptime monotonic time.
taskset -c 0 bash -c '
 R=$1
 while :; do
  read -r ts rest < /proc/uptime
  printf "%s" "$ts"
  for f in /sys/devices/system/cpu/cpufreq/policy*/scaling_cur_freq /sys/devices/system/cpu/cpufreq/policy*/cpuinfo_cur_freq /sys/class/thermal/thermal_zone*/temp /sys/class/hwmon/hwmon*/in0_lcrit_alarm; do
   printf " %s=" "$f"; v=$(cat "$f") || v=unknown; printf "%s" "$v"
  done
  printf "\n"
  sleep 1
 done' _ "$R" > "$R/telemetry.txt" 2> "$R/telemetry.stderr" & tp=$!
taskset -c 0 bash -c '
 R=$1
 while [[ ! -f $R/gst.pid ]]; do sleep .02; done
 p=$(cat "$R/gst.pid")
 while kill -0 "$p" 2>/dev/null; do
  # Enumerate descendants recursively; thread maps share their process address space.
  ids=$p; todo=$p
  while [[ -n $todo ]]; do
   more=
   for q in $todo; do
    for c in $(cat /proc/$q/task/$q/children 2>/dev/null); do more="$more $c"; done
   done
   ids="$ids $more"; todo=$more
  done
  for q in $ids; do
   if [[ -r /proc/$q/maps ]]; then
    cat /proc/$q/maps > "$R/maps/$q.current" 2>/dev/null || continue
    if grep -q libavcodec.so "$R/maps/$q.current" && grep -q libavutil.so "$R/maps/$q.current"; then
     if [[ ! -f $R/maps/$q.loaded ]]; then cp "$R/maps/$q.current" "$R/maps/$q.loaded"; cat /proc/$q/cmdline > "$R/maps/$q.cmdline"; fi
    fi
   fi
  done
  sleep .1
 done' _ "$R" > "$R/maps-watch.stdout" 2> "$R/maps-watch.stderr" & mp=$!
P=("$ROOT/tools/perf" --buildid-dir "$R/buildid")
"${P[@]}" record --buildid-mmap -e cycles -c 1000003 -o "$R/perf.data" -- taskset -c 3 bash -c 'echo $$ > "$1"; shift; exec "$@"' _ "$R/gst.pid" gst-launch-1.0 -v filesrc location="$ROOT/inputs/bbb_720p_h264_60s.mp4" ! qtdemux ! h264parse ! avdec_h264 max-threads=1 ! video/x-raw,format=I420 ! fakesink sync=false > "$R/gst.log" 2> "$R/record.stderr" & pp=$!
wait "$pp"; pp=
wait "$mp"; mp=
kill "$tp"; wait "$tp" || true; tp=
grep -q 'Got EOS' "$R/gst.log"
"${P[@]}" evlist -v -i "$R/perf.data" > "$R/evlist.txt" 2> "$R/evlist.stderr"
"${P[@]}" script -i "$R/perf.data" --show-mmap-events --show-lost-events -F pid,tid,event,period,ip,dsoff > "$R/perfscript.txt" 2> "$R/perfscript.stderr"
"${P[@]}" buildid-list -i "$R/perf.data" > "$R/buildid-list.txt" 2> "$R/buildid-list.stderr"
sha256sum "$ROOT"/variants/m1p-base/lib/*.so.* > "$R/runtime.sha256"
