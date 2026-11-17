#!/bin/bash
# Observe the task's descendant tree. No process outside it is signalled.
set -eu
here=${0%/*}; . "$here/common.sh"
root=$1; out=$2; manifest=$3
safe_path "$out"; safe_path "$manifest"; mkdir -p "$out"
trap 'exit 0' TERM INT
sequence=0
walk() {
    local pid children child
    pid=$1
    test -d "/proc/$pid" || return 0
    if test -r "/proc/$pid/maps"; then
        bash "$here/maps.sh" "$pid" "$out/$sequence-$pid" "$manifest" || printf 'maps failed %s\n' "$pid" >> "$out/errors.log"
        cat "/proc/$pid/cmdline" > "$out/$sequence-$pid/cmdline" 2>/dev/null || :
    fi
    if test -r "/proc/$pid/task/$pid/children"; then
        children=$(cat "/proc/$pid/task/$pid/children")
        for child in $children; do walk "$child"; done
    fi
}
while kill -0 "$root" 2>/dev/null; do
    sequence=$((sequence+1));walk "$root";sleep 1
done
