#!/bin/bash
set -eu
here=${0%/*}; . "$here/common.sh"
run=$1; perf=$2; event=$3; cpu=$4; limit=$5; shift 5
safe_path "$run"; safe_path "$perf"
case "$event" in ''|*[!a-zA-Z0-9_.:/-]*) exit 2;; esac
case "$cpu:$limit" in *[!0-9:]*|:*|*:|*::*) exit 2;; esac
test ! -e "$run"; mkdir -p "$run"
export HOME="$run" TMPDIR="$run" XDG_CACHE_HOME="$run/cache" XDG_CONFIG_HOME="$run/config" XDG_STATE_HOME="$run/state"
export GST_REGISTRY_1_0="$run/registry.bin"
step_log "$run/count.log"
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
bash "$here/watchdog.sh" "$limit" "$perf" stat --no-big-num -x ';' -e "$event" -o "$run/count.csv" -- taskset -c "$cpu" "$@" & worker=$!
taskset -c "${WF_OBSERVER_CPU:-0}" bash "$here/observe_maps.sh" "$worker" "$run/maps" "$DEPLOY_MANIFEST" & observer=$!
wait "$worker"; rc=$?
worker=''
kill "$observer" 2>/dev/null || :; wait "$observer" 2>/dev/null || :
observer=''
set -e
printf '%s\n' "$rc" > "$run/count.exit"
exit "$rc"
