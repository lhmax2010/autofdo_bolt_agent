#!/bin/bash
set -eu
out=$1
i=0
while :; do
 stamp=$(cut -d" " -f1 /proc/uptime)
 for p in /sys/class/thermal/thermal_zone*/temp; do printf "%s\t%s\t%s\n" "$stamp" "$p" "$(cat "$p")"; done >> "$out/temperature.tsv"
 test "$i" -lt 60 || break
 sleep 10; i=$((i+1))
done
