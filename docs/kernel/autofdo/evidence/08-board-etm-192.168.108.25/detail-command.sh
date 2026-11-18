printf '\n=== device-tree compatible inventory ===\n'
find -L /proc/device-tree -type f -name compatible -exec sh -c 'for f do printf "NODE %s\n" "$f"; tr "\000" "\n" < "$f"; done' sh {} +
printf '\n=== config existence ===\n'; ls -l /proc/config.gz; printf 'rc=%s\n' "$?"
printf '\n=== perf search ===\n'; printf 'PATH=%s\n' "$PATH"; command -v perf; printf 'path_lookup_rc=%s\n' "$?"
for d in /bin /sbin /usr/bin /usr/sbin /usr/local/bin /opt; do if test -d "$d"; then find "$d" -name perf -print; printf 'find_rc=%s directory=%s\n' "$?" "$d"; fi; done
printf '\n=== PMU sysfs ===\n'; for d in /sys/bus/event_source/devices/*; do echo "PMU $d"; ls -la "$d/"; for f in "$d/type" "$d/cpumask" "$d/events/"* "$d/format/"* "$d/caps/"*; do if test -f "$f"; then echo "FILE $f"; cat "$f"; fi; done; done
printf '\n=== precise CoreSight dmesg ===\n'; dmesg | grep -iE 'coresight|(^|[^a-z])(etm|ptm|funnel|replicator|tmc|etb|etr|tpiu)([^a-z]|$)'; printf 'grep_rc=%s\n' "$?"
printf '\n=== final identity ===\n'; id; printf '\n__ETM_DETAIL_DONE__\n'
