#!/bin/bash
set -eu
measure=$1; shift
run=$1
set +e
bash "$measure" "$@"
rc=$?
set -e
i=0
while :; do
 stamp=$(cut -d" " -f1 /proc/uptime); ready=1
 for p in /sys/class/thermal/thermal_zone*/temp; do v=$(cat "$p"); printf "%s\t%s\t%s\n" "$stamp" "$p" "$v"; test "$v" -le 56000 || ready=0; done >> "$run/cooldown.tsv"
 test "$ready" -eq 0 || break
 test "$i" -lt 60 || break
 sleep 10; i=$((i+1))
done
exit "$rc"
