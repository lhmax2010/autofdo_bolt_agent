#!/bin/bash
set -eu
here=${0%/*}; . "$here/common.sh"
run=$1; perf=$2; period=$3; cpu=$4; limit=$5; shift 5
safe_path "$run"; safe_path "$perf"
case "$period:$cpu:$limit" in *[!0-9:]*|:*|*:|*::*) exit 2;; esac
test ! -e "$run"; mkdir -p "$run"
export HOME="$run" TMPDIR="$run" XDG_CACHE_HOME="$run/cache" XDG_CONFIG_HOME="$run/config" XDG_STATE_HOME="$run/state"
export GST_REGISTRY_1_0="$run/registry.bin"
# Caller sets LD_LIBRARY_PATH and plugin dirs from verified manifest.
step_log "$run/collect.log"
test -n "${DEPLOY_MANIFEST:-}"; safe_path "$DEPLOY_MANIFEST"
worker=''; observer=''
cleanup() {
    if test -n "$observer"; then kill "$observer" 2>/dev/null || :; wait "$observer" 2>/dev/null || :; fi
    if test -n "$worker"; then kill "$worker" 2>/dev/null || :; wait "$worker" 2>/dev/null || :; fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
set +e
bash "$here/watchdog.sh" "$limit" "$perf" --buildid-dir "$run/buildid" record --buildid-mmap -e cycles -c "$period" -o "$run/perf.data" -- taskset -c "$cpu" "$@" & worker=$!
taskset -c "${WF_OBSERVER_CPU:-0}" bash "$here/observe_maps.sh" "$worker" "$run/maps" "$DEPLOY_MANIFEST" & observer=$!
wait "$worker"; rc=$?
worker=''
kill "$observer" 2>/dev/null || :; wait "$observer" 2>/dev/null || :; observer=''
set -e
printf '%s\n' "$rc" > "$run/collect.exit"
test "$rc" -eq 0 || exit "$rc"
"$perf" --buildid-dir "$run/buildid" script -i "$run/perf.data" --show-mmap-events --show-lost-events -F pid,tid,event,period,ip,dsoff > "$run/perf.script" 2> "$run/script.stderr"
"$perf" buildid-list -i "$run/perf.data" > "$run/buildid-list.txt" 2> "$run/buildid.stderr"
"$perf" evlist -v -i "$run/perf.data" > "$run/evlist.txt" 2> "$run/evlist.stderr"
