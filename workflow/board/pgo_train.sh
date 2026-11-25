#!/bin/bash
set -eu
here=${0%/*}; . "$here/common.sh"
run=$1; cpu=$2; limit=$3; shift 3
safe_path "$run"
case "$cpu:$limit" in *[!0-9:]*|:*|*:|*::*) exit 2;; esac
test ! -e "$run"
mkdir -p "$run/setup" "$run/raw"
export HOME="$run" TMPDIR="$run" XDG_CACHE_HOME="$run/cache" XDG_CONFIG_HOME="$run/config" XDG_STATE_HOME="$run/state"
export GST_REGISTRY_1_0="$run/registry.bin"
export LLVM_PROFILE_FILE="$run/setup/%m-%p.profraw"
bash "$here/watchdog.sh" "$limit" gst-inspect-1.0 avdec_h264 > "$run/setup/registry.log" 2>&1
test -s "$GST_REGISTRY_1_0"
export GST_REGISTRY_UPDATE=no
export LLVM_PROFILE_FILE="$run/raw/%m-%p.profraw"
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
bash "$here/watchdog.sh" "$limit" taskset -c "$cpu" "$@" & worker=$!
taskset -c "${WF_OBSERVER_CPU:-0}" bash "$here/observe_maps.sh" "$worker" "$run/maps" "$DEPLOY_MANIFEST" & observer=$!
wait "$worker"; rc=$?
worker=''
kill "$observer" 2>/dev/null || :; wait "$observer" 2>/dev/null || :
observer=''
set -e
printf '%s\n' "$rc" > "$run/collect.exit"
test "$rc" -eq 0 || exit "$rc"
(
    cd "$run/raw"
    find . -maxdepth 1 -type f -name '*.profraw' -printf '%f\n' | LC_ALL=C sort > "$run/raw.members"
    while IFS= read -r file; do
        case "$file" in ''|*[!0-9_.a-z-]*) exit 2;; esac
        sha256sum -- "$file"
    done < "$run/raw.members" > "$run/raw.sha256"
)
test -s "$run/raw.sha256"
