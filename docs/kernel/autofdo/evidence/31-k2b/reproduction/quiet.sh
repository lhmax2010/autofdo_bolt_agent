#!/bin/bash
set -euo pipefail
export LC_ALL=C
d=$1
[[ "$d" == /opt/afdo_agent/k2b-kgcov/* ]]
[[ "$(id -u)" == 0 ]]
[[ "$(uname -r)" == 6.12.80-arm-rpi4-v7l-kgcov ]]
[[ "$(cat /proc/sys/kernel/random/boot_id)" == "$(cat "$d/direct/boot-id")" ]]
out="$d/quiet-gate.tsv"
read -r _ a b c idle wait rest < /proc/stat
before_total=$((a+b+c+idle+wait))
read -r cpu < /proc/stat
read -r utc _ < /proc/uptime
for ((i=1,streak=0;i<=120;i++)); do
    sleep 5
    latest=$(head -1 /proc/stat)
    read -r time _ < /proc/uptime
    result=$(awk -v old="$cpu" -v new="$latest" 'BEGIN {
      split(old,a); split(new,b); total=0;
      for(i=2;i<=9;i++) total+=b[i]-a[i];
      busy=(total-(b[5]-a[5])-(b[6]-a[6])) / total * 100;
      printf "%.6f %d\n",busy,busy<2.91;
    }')
    read -r percent quiet <<< "$result"
    printf '%s\t%s\t%s\t%s\n' "$time" "$percent" "$quiet" "$(cat /sys/class/thermal/thermal_zone0/temp)" >> "$out"
    ps -eo pid,pcpu,comm --sort=-pcpu | head -6 >> "$d/quiet-top5.txt" || :
    if [[ "$quiet" == 1 ]]; then ((streak+=1)); else streak=0; fi
    if ((streak>=6)); then
        date -u +%FT%TZ > "$d/QUIET_OK"
        grep -E '^(MemTotal|MemFree|MemAvailable|Slab|KernelStack|PageTables):' /proc/meminfo > "$d/meminfo.quiet"
        echo QUIET_OK
        exit 0
    fi
    cpu=$latest
done
echo QUIET_GATE_TIMEOUT >&2
exit 76
