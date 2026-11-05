#!/bin/bash
# Usage: collect.sh rpi4|rpi5 sample-fixed|sample-freq|lost|R|C|G5 variant manifest input
set -Eeuo pipefail
HERE=${BASH_SOURCE[0]%/*}
source "$HERE/common.sh"
assert_board "${1:?board}"
MODE=${2:?mode}; ID=${3:?variant}; MANIFEST=${4:?manifest}; INPUT=${5:?video or spike rounds}
case "$MODE" in sample-fixed|sample-freq|lost|R|C|G5) ;; *) echo 'Unknown collection mode' >&2; exit 2 ;; esac
REPEATS=${COLLECT_REPEATS:-1}
[[ $REPEATS =~ ^[1-9][0-9]*$ && ${#REPEATS} -le 4 ]] || exit 2
new_run
load_variant "$MANIFEST" "$ID"
case "$MODE:$STAGE" in sample-*:S|lost:S|R:R|C:C|G5:G5) ;; *) echo 'Wrong variant stage' >&2; exit 2 ;; esac
hash_pid=; maps_pid=; telemetry_pid=
cleanup() {
    rc=$?
    trap - EXIT
    [[ -z $telemetry_pid ]] || { kill -TERM "$telemetry_pid" 2>/dev/null || true; wait "$telemetry_pid" 2>/dev/null || true; }
    [[ -z $hash_pid ]] || { kill -TERM "$hash_pid" 2>/dev/null || true; wait "$hash_pid" 2>/dev/null || true; }
    [[ -z $maps_pid ]] || { kill -TERM "$maps_pid" 2>/dev/null || true; wait "$maps_pid" 2>/dev/null || true; }
    [[ ! -p $RUN/frames.pipe ]] || rm "$RUN/frames.pipe"
    printf 'EXIT %s\nALL-END %s %s\n' "$rc" "$(date -Ins)" "$([[ $rc == 0 ]] && echo OK || echo FAILED)" >>"$RUN/status"
}
trap cleanup EXIT
telemetry_loop & telemetry_pid=$!
if [[ $OBJECT == ffmpeg ]]; then
    mkfifo "$RUN/frames.pipe"
    sha256sum "$RUN/frames.pipe" >"$RUN/decoded.sha256" & hash_pid=$!
    exec 8>"$RUN/frames.pipe"
fi
command_for "$INPUT" "$RUN/frames.pipe"
export LLVM_PROFILE_FILE="$RUN/$MODE-%m-%p.profraw"
watch_maps "$RUN/target.pid" "$RUN/target.maps" "$TARGET" & maps_pid=$!
LAUNCH=(/bin/bash -c 'printf "%s\n" "$$" >"$1"; shift; exec "$@"' _ "$RUN/target.pid" "${CMD[@]}")
if (( REPEATS > 1 )); then
    LAUNCH=(/bin/bash -c 'set -e; n=$1; shift; for ((i=0;i<n;i++)); do "$@"; done' _ "$REPEATS" "${LAUNCH[@]}")
fi
printf '%q ' "${LAUNCH[@]}" >"$RUN/command"; printf '\n' >>"$RUN/command"
if [[ $MODE == sample-* || $MODE == lost ]]; then
    EVENT=(-e cycles -c 1000003)
    [[ $MODE != sample-freq ]] || EVENT=(-e cycles -F 1000)
    [[ $MODE != lost ]] || EVENT=(-e cycles -c 10007 -m 1)
    set +e
    { time -p "${PERF[@]}" record --buildid-mmap "${EVENT[@]}" -o "$RUN/perf.data" -- "${LAUNCH[@]}"; } >"$RUN/workload.stdout" 2>"$RUN/record.stderr"
    rc=$?; set -e
    printf 'RECORD_EXIT %s\n' "$rc" >"$RUN/status"
    [[ $rc == 0 ]] || exit "$rc"
    "${PERF[@]}" evlist -v -i "$RUN/perf.data" >"$RUN/evlist.txt" 2>"$RUN/evlist.stderr"
    LC_ALL=C "${PERF[@]}" script -i "$RUN/perf.data" --show-mmap-events --show-lost-events -F pid,tid,event,period,ip,dsoff >"$RUN/perfscript.txt" 2>"$RUN/perfscript.stderr"
    "${PERF[@]}" buildid-list -i "$RUN/perf.data" >"$RUN/buildid-list.txt" 2>"$RUN/buildid-list.stderr"
    awk -v id="$TARGET_ID" -v path="$TARGET" '$1==id && $2==path {found=1} END {exit !found}' "$RUN/buildid-list.txt" || { echo 'Recorded build-id/path did not match target' >&2; exit 3; }
    grep 'PERF_RECORD_LOST' "$RUN/perfscript.txt" >"$RUN/lost-excerpt.txt" || true
else
    set +e
    { time -p "${LAUNCH[@]}"; } >"$RUN/workload.stdout" 2>"$RUN/workload.stderr"
    rc=$?; set -e
    printf 'WORKLOAD_EXIT %s\n' "$rc" >"$RUN/status"
    [[ $rc == 0 ]] || exit "$rc"
    count=$(find "$RUN" -maxdepth 1 -name "$MODE-*.profraw" -type f | wc -l)
    [[ -n $count && $count -gt 0 ]] || { echo 'No profraw produced' >&2; exit 3; }
fi
exec 8>&-
wait "$maps_pid"; maps_pid=
if [[ -n $hash_pid ]]; then wait "$hash_pid"; hash_pid=; fi
kill -TERM "$telemetry_pid"; wait "$telemetry_pid" 2>/dev/null || true
telemetry_pid=
finish_run
