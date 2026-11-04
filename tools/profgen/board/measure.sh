#!/bin/bash
# Usage: measure.sh rpi4|rpi5 manifest test-video G0 G1 [G2 ...]
# The manifest must label baseline S and trained variants USE; never R/C/G5 generators.
set -Eeuo pipefail
HERE=${BASH_SOURCE[0]%/*}
source "$HERE/common.sh"
assert_board "${1:?board}"
MANIFEST=${2:?manifest}; VIDEO=${3:?test video}; shift 3
(( $# >= 2 )) || { echo 'At least two interleaved groups required' >&2; exit 2; }
GROUPS_TO_RUN=("$@")
new_run
VIDEO=$(inside "$VIDEO")
sha256sum "$VIDEO" >"$RUN/input.sha256"
hash_pid=; maps_pid=; telemetry_pid=
cleanup() {
    rc=$?; trap - EXIT
    [[ -z $telemetry_pid ]] || { kill -TERM "$telemetry_pid" 2>/dev/null || true; wait "$telemetry_pid" 2>/dev/null || true; }
    [[ -z $hash_pid ]] || { kill -TERM "$hash_pid" 2>/dev/null || true; wait "$hash_pid" 2>/dev/null || true; }
    [[ -z $maps_pid ]] || { kill -TERM "$maps_pid" 2>/dev/null || true; wait "$maps_pid" 2>/dev/null || true; }
    printf 'ALL-END %s %s EXIT=%s\n' "$(date -Ins)" "$([[ $rc == 0 ]] && echo OK || echo FAILED)" "$rc" >>"$RUN/status"
}
trap cleanup EXIT
telemetry_loop & telemetry_pid=$!
# One discarded warm-up per group; then ten saved rounds, rotating group order.
for ((round=0;round<=10;round++)); do
    for ((j=0;j<${#GROUPS_TO_RUN[@]};j++)); do
        index=$(((j+round)%${#GROUPS_TO_RUN[@]})); group=${GROUPS_TO_RUN[index]}
        load_variant "$MANIFEST" "$group"
        [[ $OBJECT == ffmpeg && ( $STAGE == S || $STAGE == USE ) ]] || { echo 'Measurement needs baseline or trained-use FFmpeg libraries' >&2; exit 2; }
        tag="$RUN/round-$round-$group"
        snapshot "$tag.before"
        mkfifo "$tag.pipe"
        sha256sum "$tag.pipe" >"$tag.decoded.sha256" & hash_pid=$!
        command_for "$VIDEO" "$tag.pipe"
        watch_maps "$tag.pid" "$tag.maps" "$TARGET" & maps_pid=$!
        set +e
        { time -p "${PERF[@]}" stat -e cycles,instructions -o "$tag.stat" -- /bin/bash -c 'echo "$$" >"$1"; shift; exec "$@"' _ "$tag.pid" "${CMD[@]}"; } >"$tag.stdout" 2>"$tag.stderr"
        rc=$?; set -e
        printf '%s %s %s %s\n' "$round" "$group" "$rc" "$([[ $round == 0 ]] && echo WARMUP_DISCARD || echo KEEP)" >>"$RUN/rounds.tsv"
        [[ $rc == 0 ]] || exit "$rc"
        wait "$maps_pid"; maps_pid=
        wait "$hash_pid"; hash_pid=
        rm "$tag.pipe"
        snapshot "$tag.after"
        digest=$(cut -d' ' -f1 "$tag.decoded.sha256")
        [[ -n $digest ]] || exit 3
        if [[ -f $RUN/expected-decoded.sha256 ]]; then
            [[ $digest == "$(cat "$RUN/expected-decoded.sha256")" ]] || { echo 'Decoded output mismatch' >&2; exit 3; }
        else
            printf '%s\n' "$digest" >"$RUN/expected-decoded.sha256"
        fi
    done
done
kill -TERM "$telemetry_pid"; wait "$telemetry_pid" 2>/dev/null || true
telemetry_pid=
finish_run
