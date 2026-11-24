#!/bin/bash
set -eu
here=${0%/*}; . "$here/common.sh"
run=$1; perf=$2; cpu=$3; observer_cpu=$4; capabilities=$5; limit=$6; shift 6
safe_path "$run"; safe_path "$perf"; safe_path "$capabilities"
test ! -e "$run"; mkdir -p "$run"
export HOME="$run" TMPDIR="$run" XDG_CACHE_HOME="$run/cache" XDG_CONFIG_HOME="$run/config" XDG_STATE_HOME="$run/state"
export GST_REGISTRY_UPDATE=no
step_log "$run/measure.log"
test -n "${DEPLOY_MANIFEST:-}"; safe_path "$DEPLOY_MANIFEST"
sleep 5
bash "$here/start_gate.sh" "$capabilities" "$run/start-gate.log"
sampler=''; observer=''; worker=''
cleanup() {
    if test -n "$observer"; then kill "$observer" 2>/dev/null || :; wait "$observer" 2>/dev/null || :; fi
    if test -n "$worker"; then kill "$worker" 2>/dev/null || :; wait "$worker" 2>/dev/null || :; fi
    if test -n "$sampler"; then kill "$sampler" 2>/dev/null || :; wait "$sampler" 2>/dev/null || :; fi; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
taskset -c "$observer_cpu" bash "$here/telemetry.sh" "$run/telemetry.tsv" "$capabilities" "$run/telemetry.ready" "$run/telemetry.request" "$run/telemetry.done" & sampler=$!
checks=0
while test ! -s "$run/telemetry.ready"; do
    kill -0 "$sampler"; sleep 0.1; checks=$((checks+1)); test "$checks" -lt 100
done
# Preserve the design's start-1 / end+1 window, not merely the load interval.
while ! awk -v first="$(cat "$run/telemetry.ready")" '{exit !($1 >= first+1)}' /proc/uptime; do sleep 0.1; done
awk '{print $1}' /proc/uptime > "$run/start.monotonic"
export WF_WALL_FILE="$run/wall.txt"
set +e
bash "$here/watchdog.sh" "$limit" "$perf" stat -x ';' -o "$run/perf-stat.csv" -e task-clock,cycles,instructions -- taskset -c "$cpu" "$@" & worker=$!
taskset -c "$observer_cpu" bash "$here/observe_maps.sh" "$worker" "$run/maps" "$DEPLOY_MANIFEST" & observer=$!
wait "$worker"; rc=$?
worker=''
kill "$observer" 2>/dev/null || :; wait "$observer" 2>/dev/null || :; observer=''
set -e
awk '{print $1}' /proc/uptime > "$run/end.monotonic"
awk '{printf "%.2f\n", $1+1}' "$run/end.monotonic" > "$run/telemetry.request.tmp"
mv "$run/telemetry.request.tmp" "$run/telemetry.request"
checks=0
while test ! -s "$run/telemetry.done"; do
    kill -0 "$sampler"; sleep 0.1; checks=$((checks+1)); test "$checks" -lt 100
done
wait "$sampler"; sampler=''
printf '%s\n' "$rc" > "$run/measure.exit"
exit "$rc"
