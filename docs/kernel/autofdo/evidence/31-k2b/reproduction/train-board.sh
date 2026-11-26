#!/bin/bash
set -euo pipefail
export LC_ALL=C LD_LIBRARY_PATH=/opt/afdo_agent/lib
task=/opt/afdo_agent/k2b-kgcov
scope=$1
action=$2
[[ $scope =~ ^session-0[123](-retry|-resume)?$ ]]
session=$task/$scope
tmp=$session/tmp
mnt=$session/debugfs
proc_temp=/sys/class/thermal/thermal_zone0/temp
policy=/sys/devices/system/cpu/cpufreq/policy0
build_prefix=home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/build/arm-rpi4
[[ $(id -u) == 0 ]]
[[ $(tr -d '\000' </proc/device-tree/serial-number) == 100000004694d889 ]]
[[ $(uname -r) == 6.12.80-arm-rpi4-v7l-kgcov ]]
[[ $(cat /proc/sys/kernel/random/boot_id) == "$(cat "$session/direct/boot-id")" ]]
case $action in
    init)
        [[ -s "$session/QUIET_OK" ]]
        mkdir "$tmp" "$mnt"
        mount -t tmpfs -o size=192M,mode=0700,nosuid,nodev,exec tmpfs "$tmp"
        cleanup=1
        trap 'if ((cleanup)); then if mountpoint -q "$mnt"; then umount "$mnt"; fi; umount "$tmp"; fi' EXIT
        mkdir "$tmp/BASE" "$tmp/bench"
        tar -xf "$task/BASE.tar" -C "$tmp/BASE"
        [[ -f "$tmp/BASE/usr/lib/libavcodec.so.62.11.100" ]]
        [[ -s /opt/afdo_agent/inputs/tos_720p_h264_60s.mp4 ]]
        sha256sum /opt/afdo_agent/inputs/tos_720p_h264_60s.mp4 > "$session/tos.sha256"
        grep -Fx "280fbd41f8772491ebe784aa19a3caed3bb1e8b2e64daef1d2a5a284d1f38ad1  /opt/afdo_agent/inputs/tos_720p_h264_60s.mp4" "$session/tos.sha256"
        if [[ -d /sys/kernel/debug/gcov && -w /sys/kernel/debug/gcov/reset ]]; then
            gcov=/sys/kernel/debug/gcov
        else
            mount -t debugfs -o nosuid,nodev,noexec debugfs "$mnt"
            gcov="$mnt/gcov"
        fi
        [[ -w "$gcov/reset" ]]
        printf '%s\n' "$gcov" > "$session/debugfs.path"
        find "$gcov" -type f -name '*.gcda' | sort > "$session/gcda-at-boot.paths"
        [[ -s "$session/gcda-at-boot.paths" ]]
        while IFS= read -r relative; do
            [[ -f "$gcov/$build_prefix/$relative" ]]
        done < "$task/expected-gcda.txt"
        grep -Fx "$gcov/$build_prefix/fs/pipe.gcda" "$session/gcda-at-boot.paths"
        grep -Fx "$gcov/$build_prefix/mm/highmem.gcda" "$session/gcda-at-boot.paths"
        cleanup=0
        echo GCOV_INIT_OK
        exit 0
        ;;
    cleanup)
        if mountpoint -q "$mnt"; then umount "$mnt"; fi
        if mountpoint -q "$tmp"; then umount "$tmp"; fi
        echo GCOV_CLEANUP_OK
        exit 0
        ;;
esac
gcov=$(cat "$session/debugfs.path")
[[ $gcov == "$mnt/gcov" || $gcov == /sys/kernel/debug/gcov ]]
mountpoint -q "$tmp"
[[ -w "$gcov/reset" ]]
load=$action
perf=/opt/afdo_agent/tools/perf
mm=/opt/afdo_agent/k1d-a-20261118/closeout-20261119/mmfault
case $load in
    pipe) seconds=60; cmd=("$perf" bench sched pipe -l 250000) ;;
    mmfault) seconds=60; cmd=("$mm" 32 118) ;;
    tmpfs) seconds=60; cmd=(bash "$task/tmpfs-load.sh" "$tmp/bench/tmpfs.payload") ;;
    syscall) seconds=30; cmd=("$perf" bench syscall basic -l 20000000) ;;
    tos)
        seconds=120
        export LD_LIBRARY_PATH="$tmp/BASE/usr/lib:$LD_LIBRARY_PATH" GST_REGISTRY_UPDATE=no
        export GST_REGISTRY="$tmp/bench/gstreamer-registry.bin"
        cmd=(gst-launch-1.0 -e filesrc location=/opt/afdo_agent/inputs/tos_720p_h264_60s.mp4 '!' qtdemux '!' h264parse '!' \
             avdec_h264 max-threads=1 '!' video/x-raw,format=I420 '!' fakesink sync=false)
        ;;
    *) exit 64 ;;
esac
out=$session/$load
mkdir "$out"
export HOME="$tmp/bench" TMPDIR="$tmp/bench" XDG_CACHE_HOME="$tmp/bench/cache"
export XDG_CONFIG_HOME="$tmp/bench/config" XDG_STATE_HOME="$tmp/bench/state"
printf '%q ' taskset -c 3 "${cmd[@]}" > "$out/workload.argv"
printf '\n' >> "$out/workload.argv"
read -r governor < "$policy/scaling_governor"
printf '%s\n' "$governor" > "$out/governor.before"
same() {
    local a b
    a=$(sha256sum -- "$1") || return
    b=$(sha256sum -- "$2") || return
    [[ ${a%% *} == "${b%% *}" ]]
}
group=''
stop_load() {
    if [[ -n "$group" ]]; then
        kill -TERM -- "-$group" 2>/dev/null || :
        wait "$group" 2>/dev/null || :
        group=''
    fi
}
cleanup() {
    local rc=$?
    trap - EXIT HUP INT TERM
    stop_load
    printf '%s\n' "$governor" > "$policy/scaling_governor" || rc=75
    cat "$policy/scaling_governor" > "$out/governor.after"
    same "$out/governor.before" "$out/governor.after" || rc=75
    if [[ -f "$tmp/bench/tmpfs.payload" ]]; then rm -- "$tmp/bench/tmpfs.payload"; fi
    date -u +%FT%TZ > "$out/cleanup-at"
    printf '%s\n' "$rc" > "$out/exit"
    exit "$rc"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 143' TERM
trap 'exit 130' INT
stamp() {
    read -r up _ < /proc/uptime
    read -r current < "$proc_temp"
    read -r freq < "$policy/scaling_cur_freq"
    read -r actual < "$policy/scaling_governor"
    printf '%s\t%s\t%s\t%s\t%s\n' "$up" "$1" "$current" "$freq" "$actual" >> "$out/telemetry.tsv"
}
switch() {
    printf '%s\n' "$1" > "$policy/scaling_governor"
    [[ $(cat "$policy/scaling_governor") == "$1" ]]
    stamp switch
}
deadline=$((SECONDS+600))
ready=0
while ((SECONDS < deadline)); do
    read -r t < "$proc_temp"
    if ((t<=60000)); then
        switch performance
        sleep 3
        stamp stabilized
        read -r t < "$proc_temp"
        if ((t<=60000)); then ready=1; break; fi
    fi
    [[ $(cat "$policy/scaling_governor") == powersave ]] || switch powersave
    stamp cooling
    sleep 5
done
((ready)) || exit 76
cat /proc/modules > "$out/modules.before"
cp /proc/meminfo "$out/meminfo.before"
stamp prestart
read -r t < "$proc_temp"
((t<=60000)) || exit 76
date -u +%FT%TZ > "$out/reset-at"
echo 1 > "$gcov/reset"
read -r begin _ < /proc/uptime
printf '%s\n' "$begin" > "$out/workload-start.uptime"
setsid bash -c '
    set -euo pipefail
    while :; do taskset -c 3 "$@"; done
' load "${cmd[@]}" > "$out/workload.log" 2>&1 &
group=$!
for ((i=0;i<seconds;i++)); do
    kill -0 "$group"
    stamp run
    read -r t < "$proc_temp"
    ((t < 80000)) || exit 77
    sleep 1
done
kill -0 "$group"
stop_load
read -r end _ < /proc/uptime
printf '%s\n' "$end" > "$out/workload-stop.uptime"
date -u +%FT%TZ > "$out/export-start"
exportdir=$tmp/export-$load
mkdir "$exportdir"
find "$gcov" -type f -name '*.gcda' | sort > "$out/gcda-source.paths"
same "$session/gcda-at-boot.paths" "$out/gcda-source.paths"
while IFS= read -r node; do
    relative=${node#"$gcov"/}
    [[ $relative != "$node" && $relative != /* && $relative != *../* ]]
    mkdir -p "$exportdir/$(dirname "$relative")"
    cat "$node" > "$exportdir/$relative"
    [[ $(head -c 8 "$exportdir/$relative") == 'adcg*11B' ]]
done < "$out/gcda-source.paths"
date -u +%FT%TZ > "$out/export-read-finished"
(
    cd "$exportdir"
    find . -type f -exec sha256sum {} + | sort -k2 > "$out/gcda.sha256"
    tar --owner=0 --group=0 --numeric-owner -cf "$tmp/$load.gcda.tar" .
)
(
    cd "$tmp"
    sha256sum "$load.gcda.tar" > "$out/archive.sha256"
)
date -u +%FT%TZ > "$out/archive-finished"
cat /proc/modules > "$out/modules.after"
cut -d" " -f1 "$out/modules.before" > "$out/module-names.before"
cut -d" " -f1 "$out/modules.after" > "$out/module-names.after"
same "$out/module-names.before" "$out/module-names.after"
cp /proc/meminfo "$out/meminfo.after"
rm -rf -- "$exportdir"
echo GCOV_SEGMENT_OK
