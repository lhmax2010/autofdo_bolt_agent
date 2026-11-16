#!/bin/bash
# Host owns root restoration; this wrapper restores governors on every exit.
set -eu
here=${0%/*}; . "$here/common.sh"
saved=$1; model=$2; arch=$3; kernel=$4; image=$5; shift 5
safe_path "$saved"; assert_identity "$model" "$arch" "$kernel" "$image"; precheck
test ! -e "$saved"; mkdir -p "$saved"
restore() {
    rc=$?
    trap - EXIT INT TERM
    failed=0
    for f in "$saved"/policy*; do
        test -f "$f" || continue
        p=${f##*/}
        value=$(cat "$f")
        test -n "$value" || { failed=1; continue; }
        printf '%s\n' "$value" > "/sys/devices/system/cpu/cpufreq/$p/scaling_governor" || failed=1
        test "$(cat "/sys/devices/system/cpu/cpufreq/$p/scaling_governor")" = "$value" || failed=1
    done
    printf 'exit=%s restore_failed=%s\n' "$rc" "$failed" > "$saved/restore.log"
    test "$failed" -eq 0 || rc=3
    exit "$rc"
}
trap restore EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
for p in /sys/devices/system/cpu/cpufreq/policy*; do
    test -d "$p" || continue
    cat "$p/scaling_governor" > "$saved/${p##*/}"
    printf '%s\n' performance > "$p/scaling_governor"
    test "$(cat "$p/scaling_governor")" = performance
 done
"$@"
