#!/bin/bash
set -u
set -m
limit=$1; shift
[[ $limit =~ ^[1-9][0-9]*$ ]] || exit 2
child=; guard=
cleanup() {
 rc=$?
 trap - EXIT
 for p in "$guard" "$child"; do
  [[ -z $p ]] || { kill -TERM -- "-$p" 2>/dev/null || true; }
 done
 exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM HUP
"$@" & child=$!
(sleep "$limit"; printf 'WATCHDOG_TIMEOUT %s\n' "$limit" >&2; kill -TERM -- "-$child" 2>/dev/null; sleep 5; kill -KILL -- "-$child" 2>/dev/null) & guard=$!
wait "$child"; rc=$?; child=
exit "$rc"
