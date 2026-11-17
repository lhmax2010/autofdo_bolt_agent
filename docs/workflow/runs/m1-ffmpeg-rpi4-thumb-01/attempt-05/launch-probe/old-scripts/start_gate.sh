#!/bin/bash
set -eu
here=${0%/*}; . "$here/common.sh"
capabilities=$1; log=$2
safe_path "$capabilities"; step_log "$log"
waited=0
while :; do
    ready=1; count=0
    while IFS="$(printf '\t')" read -r kind path; do
        test "$kind" = temperature || continue
        case "$path" in /sys/*) ;; *) exit 2;; esac
        value=$(cat "$path")
        case "$value" in ''|*[!0-9]*) exit 3;; esac
        printf '%s\t%s\t%s\n' "$(date -u +%s)" "$path" "$value"
        count=$((count+1))
        test "$value" -le 60000 || ready=0
    done < "$capabilities"
    test "$count" -gt 0 || exit 3
    test "$ready" -eq 1 && exit 0
    test "$waited" -lt 600 || exit 3
    sleep 30; waited=$((waited+30))
done
