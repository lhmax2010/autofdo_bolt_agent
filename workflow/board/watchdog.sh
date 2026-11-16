#!/bin/bash
# Only the setsid process group created here may be signalled.
set -eu
seconds=$1; shift
case "$seconds" in ''|*[!0-9]*|0) exit 2;; esac
child='';watch=''
cleanup() {
    if test -n "$watch"; then kill "$watch" 2>/dev/null || :; wait "$watch" 2>/dev/null || :; fi
    if test -n "$child"; then
        kill -TERM -- "-$child" 2>/dev/null || :
        sleep 1
        kill -KILL -- "-$child" 2>/dev/null || :
        wait "$child" 2>/dev/null || :
    fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
run_group() {
setsid "$@" & child=$!
(
    sleep "$seconds"
    kill -TERM -- "-$child" 2>/dev/null || exit 0
    sleep 1
    kill -KILL -- "-$child" 2>/dev/null || :
) & watch=$!
wait "$child"
}
set +e
TIMEFORMAT='%R'
if test -n "${WF_WALL_FILE:-}"; then
    case "$WF_WALL_FILE" in /opt/afdo_agent/*) ;; *) exit 2;; esac
    { time run_group "$@"; } 2> "$WF_WALL_FILE"
    rc=$?
else
    run_group "$@"; rc=$?
fi
set -e
# Keep child until cleanup: descendants may still exist in this process group.
exit "$rc"
