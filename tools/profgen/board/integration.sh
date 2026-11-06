#!/bin/bash
# Additional first-round integration and bounded LOST RUNs; no system mutation.
set -Eeuo pipefail
HERE=${BASH_SOURCE[0]%/*}
source "$HERE/common.sh"
assert_board rpi4
MODE=${1:?mode}
case "$MODE" in lost|fork|exec|deleted|module|system) ;; *) exit 2;; esac
new_run
telemetry_pid=; maps_pid=; hash_pid=; child_pid=; run_complete=0
cleanup() {
    rc=$?; trap - EXIT HUP INT TERM
    (( rc != 0 || run_complete == 1 )) || rc=1
    for p in "$telemetry_pid" "$maps_pid" "$hash_pid" "$child_pid"; do
        [[ -z $p ]] || { kill -TERM "$p" 2>/dev/null || true; wait "$p" 2>/dev/null || true; }
    done
    [[ ! -p $RUN/frames.pipe ]] || rm "$RUN/frames.pipe"
    printf 'EXIT %s\nALL-END %s %s\n' "$rc" "$(date -Ins)" "$([[ $rc == 0 ]] && echo OK || echo FAILED)" >>"$RUN/status"
    exit "$rc"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
telemetry_loop & telemetry_pid=$!
export LLVM_PROFILE_FILE="$RUN/setup-%m-%p.profraw"
EVENT=(-e cycles -c 1000003)
RECORD=("${PERF[@]}" record --buildid-mmap)
if [[ $MODE == lost ]]; then
    load_variant "$BASE/eval-manifest.tsv" ffmpeg-thumb-S
    FRAMES=${2:?frame bound}; COPIES=${3:-1}
    [[ $FRAMES =~ ^[1-9][0-9]*$ && ${#FRAMES} -le 5 && $COPIES =~ ^[12]$ ]] || exit 2
    gst-inspect-1.0 identity >"$RUN/identity-plugin.txt"
    grep -q eos-after "$RUN/identity-plugin.txt"
    # Hash all decoded bytes without storing uncompressed frames on disk.
    mkfifo "$RUN/frames.pipe"
    sha256sum "$RUN/frames.pipe" >"$RUN/decoded.sha256" & hash_pid=$!
    exec 8>"$RUN/frames.pipe"
    CMD=(gst-launch-1.0 -q filesrc "location=$BASE/media/bbb_1080p_h264_60s.mp4" '!' qtdemux '!' h264parse '!' avdec_h264 max-threads=1 '!' video/x-raw,format=I420 '!' identity "eos-after=$FRAMES" '!' filesink "location=$RUN/frames.pipe" sync=false)
    EVENT=(-e cycles -c 10007 -m 1)
    if [[ $COPIES == 2 ]]; then
        RECORD+=(-a)
        CMD=(/bin/bash -c 'set -e; "$@" & p=$!; "$@"; wait "$p"' _ "${CMD[@]}")
    fi
else
    export LD_LIBRARY_PATH="$BASE/work:$BASE/lib"
    CMD=("$BASE/tools/integration/cases" "$MODE")
    if [[ $MODE == module ]]; then
        lsmod >"$RUN/modules.txt"
        if grep -q '^kdbus ' "$RUN/modules.txt"; then
            CMD=(/bin/bash -c 'set -e; /opt/afdo_agent/tools/integration/cases fork & p=$!; for ((i=0;i<500;i++)); do dbus-send --system --print-reply --dest=org.freedesktop.DBus / org.freedesktop.DBus.ListNames >/dev/null; done; wait "$p"')
            printf 'loaded kdbus; ordinary DBus ListNames calls\n' >"$RUN/module-choice"
        else
            CMD=("$BASE/tools/integration/cases" fork)
            printf 'kdbus unavailable; no module loading or synthetic module claim\n' >"$RUN/module-choice"
        fi
        RECORD+=(-a); EVENT=(-e cycles -c 100003)
    elif [[ $MODE == system ]]; then
        CMD=("$BASE/tools/integration/cases" fork);RECORD+=(-a)
    elif [[ $MODE == deleted ]]; then
        # Host has freshly pushed and SHA-checked only this test library copy.
        rm -f "$BASE/work/deleted.ready" "$BASE/work/deleted.go"
        "$BASE/tools/integration/deleted" >"$RUN/deleted.stdout" 2>"$RUN/deleted.stderr" & child_pid=$!
        for ((i=0;i<100;i++)); do [[ ! -s $BASE/work/deleted.ready ]] || break; sleep .1; done
        [[ -s $BASE/work/deleted.ready ]] || exit 3
        cat "/proc/$child_pid/maps" >"$RUN/deleted.maps"
        RECORD+=(-p "$child_pid")
        CMD=(/bin/bash -c ': > /opt/afdo_agent/work/deleted.go; sleep .1')
    fi
fi
printf '%q ' "${CMD[@]}" >"$RUN/command"; printf '\n' >>"$RUN/command"
LAUNCH=(/bin/bash -c 'printf "%s\n" "$$" >"$1"; shift; exec "$@"' _ "$RUN/target.pid" "${CMD[@]}")
# Maps are raw observations; exec can replace the image between snapshots.
(
    for ((i=0;i<1000;i++)); do
        if [[ -s $RUN/target.pid ]]; then
            read -r pid <"$RUN/target.pid"
            [[ $pid =~ ^[0-9]+$ ]] || exit 3
            [[ ! -r /proc/$pid/maps ]] || cat "/proc/$pid/maps" >"$RUN/maps-$i"
        fi
        sleep .05
    done
) & maps_pid=$!
set +e
{ time -p LC_ALL=C "${RECORD[@]}" "${EVENT[@]}" -o "$RUN/perf.data" -- "${PERF[@]}" stat -x ';' -e cycles,instructions,task-clock -o "$RUN/perf-stat.csv" -- "${LAUNCH[@]}"; } >"$RUN/workload.stdout" 2>"$RUN/record.stderr"
rc=$?;set -e
printf 'RECORD_EXIT %s\n' "$rc" >"$RUN/status"
[[ $rc == 0 ]] || exit "$rc"
if [[ -n $child_pid ]]; then wait "$child_pid"; child_pid=; fi
exec 8>&-
if [[ -n $hash_pid ]]; then wait "$hash_pid"; hash_pid=; fi
"${PERF[@]}" evlist -v -i "$RUN/perf.data" >"$RUN/evlist.txt" 2>"$RUN/evlist.stderr"
LC_ALL=C "${PERF[@]}" script -i "$RUN/perf.data" --show-mmap-events --show-lost-events -F pid,tid,event,period,ip,dsoff >"$RUN/perfscript.txt" 2>"$RUN/perfscript.stderr"
"${PERF[@]}" buildid-list -i "$RUN/perf.data" >"$RUN/buildid-list.txt" 2>"$RUN/buildid-list.stderr"
"${PERF[@]}" report --stdio --sort dso -i "$RUN/perf.data" >"$RUN/report.txt" 2>"$RUN/report.stderr"
if [[ $MODE == lost ]]; then
    awk -v id="$TARGET_ID" -v path="$TARGET" '$1==id && $2==path {found=1} END {exit !found}' "$RUN/buildid-list.txt"
fi
kill -TERM "$maps_pid" "$telemetry_pid";wait "$maps_pid" 2>/dev/null || true;wait "$telemetry_pid" 2>/dev/null || true
maps_pid=;telemetry_pid=
finish_run
run_complete=1
