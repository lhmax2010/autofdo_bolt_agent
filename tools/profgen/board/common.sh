#!/bin/bash
# Sourced only by board entry points. No device state changes.
set -Eeuo pipefail
BASE=/opt/afdo_agent
# External-command inventory: review all scripts in this directory, including
# substitutions, pipelines, array commands and the /bin/bash workload launcher.
# time, kill, read, test, printf, wait, command and source are Bash builtins/keywords.
BOARD_REQUIRED_COMMANDS=(
    /bin/bash awk cat cut date df find findmnt grep gst-inspect-1.0
    gst-launch-1.0 mkdir mkfifo ps readlink rm rpm sha256sum sleep tr uname wc
    /opt/afdo_agent/tools/perf
)
preflight_dependencies() {
    local cmd missing=0
    for cmd in "${BOARD_REQUIRED_COMMANDS[@]}"; do
        if command -v "$cmd"; then
            printf 'DEPENDENCY_OK %s\n' "$cmd"
        else
            printf 'DEPENDENCY_MISSING %s\n' "$cmd" >&2
            missing=1
        fi
    done
    (( missing == 0 ))
}
assert_performance() {
    local p found=0 value
    for p in /sys/devices/system/cpu/cpufreq/policy*/scaling_governor; do
        [[ -r $p ]] || continue
        found=1
        value=$(<"$p")
        [[ $value == performance ]] || { echo "Governor is not performance: $p=$value" >&2; return 2; }
    done
    (( found == 1 )) || { echo 'No readable governor' >&2; return 2; }
}
compare_rpm_counts() {
    local before=$1 after=$2
    # Bound the integer before Bash arithmetic so malformed/overflowing input
    # cannot compare equal accidentally. Normal RPM counts are many orders lower.
    [[ $before =~ ^[0-9]+$ && $after =~ ^[0-9]+$ && ${#before} -le 18 && ${#after} -le 18 ]] || {
        echo 'RPM counts must be nonempty decimal integers (at most 18 digits)' >&2; return 2;
    }
    (( 10#$before == 10#$after )) || { echo "RPM count changed: $before -> $after" >&2; return 3; }
}
assert_board() {
    local expected=${1:?board required} model arch release
    model=$(tr -d '\000' </proc/device-tree/model)
    arch=$(uname -m)
    release=$(uname -r)
    [[ -n $model && -n $arch && -n $release ]] || { echo 'Identity unavailable' >&2; exit 2; }
    case "$expected:$model:$arch:$release" in
      rpi4:Raspberry\ Pi\ 4*:armv7l:*rpi4*|rpi4:Raspberry\ Pi\ 4*:armv7l:*v7l*) ;;
      rpi5:Raspberry\ Pi\ 5*:aarch64:*arm64-rpi4-v8*) ;;
      *) printf 'Identity mismatch: %s / %s / %s\n' "$model" "$arch" "$release" >&2; exit 2 ;;
    esac
    printf 'IDENTITY %s / %s / %s\n' "$model" "$arch" "$release"
    [[ $(readlink -f "$BASE") == "$BASE" ]] || { echo 'Deployment base alias refused' >&2; exit 2; }
}
inside() {
    local path
    path=$(readlink -f -- "$1")
    [[ -n $path && $path == "$BASE/"* ]] || { echo "Outside deployment base: $1" >&2; exit 2; }
    printf '%s\n' "$path"
}
new_run() {
    local stamp opts
    preflight_dependencies
    assert_performance
    if command -v findmnt >/dev/null; then
        opts=$(findmnt -n -o OPTIONS -T "$BASE")
        [[ -n $opts ]] || { echo 'Mount options unknown' >&2; exit 2; }
        case ",$opts," in *,ro,*|*,noexec,*) echo "Unsuitable mount: $opts" >&2; exit 2 ;; esac
    else
        echo 'findmnt required for prepared evaluation scripts; stop without writing' >&2; exit 2
    fi
    stamp=$(date +%Y%m%dT%H%M%S)
    [[ -n $stamp ]] || exit 2
    mkdir -p "$BASE/work"
    inside "$BASE/work" >/dev/null
    RUN="$BASE/work/eval-$stamp-$$"
    mkdir "$RUN"
    export HOME="$RUN/home" TMPDIR="$RUN/tmp" XDG_CACHE_HOME="$RUN/cache"
    export GST_REGISTRY="$RUN/registry.bin" PERF_CONFIG="$RUN/perf.conf"
    # Plugin inspection/scanning may load an instrumented DSO before collection.
    export LLVM_PROFILE_FILE="$RUN/setup-%m-%p.profraw"
    mkdir "$HOME" "$TMPDIR" "$XDG_CACHE_HOME" "$RUN/buildid"
    : >"$PERF_CONFIG"
    PERF=("$BASE/tools/perf" --buildid-dir "$RUN/buildid")
    df -h "$BASE" >"$RUN/df.before"
    uname -a >"$RUN/uname"
    uname -v >>"$RUN/uname"
    cat /proc/version >"$RUN/proc-version"
    if [[ -r /proc/config.gz ]]; then
        sha256sum /proc/config.gz >"$RUN/kernel-config.sha256"
    elif [[ -r /boot/config-$(uname -r) ]]; then
        sha256sum "/boot/config-$(uname -r)" >"$RUN/kernel-config.sha256"
    else
        echo 'unknown: no readable kernel configuration' >"$RUN/kernel-config.sha256"
    fi
    cat /proc/swaps >"$RUN/swaps.before"
    for z in /sys/block/zram*/mm_stat /sys/block/zram*/stat; do
        [[ ! -r $z ]] || { printf '%s ' "$z"; cat "$z"; }
    done >"$RUN/zram.before"
    cat /etc/os-release >"$RUN/os-release"
    [[ ! -r /etc/tizen-build.conf ]] || cat /etc/tizen-build.conf >"$RUN/tizen-build.conf"
    rpm -qa | wc -l >"$RUN/rpm-count.before"
    snapshot "$RUN/environment.before"
}
snapshot() {
    {
        date -Ins
        cat /proc/loadavg
        awk '$1=="pswpout" || $1=="pswpin"' /proc/vmstat
        for f in /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor /sys/class/thermal/thermal_zone*/temp /sys/class/thermal/thermal_zone*/type; do
            [[ ! -r $f ]] || { printf '%s ' "$f"; cat "$f"; }
        done
        if [[ -n ${THROTTLE_NODE:-} && $THROTTLE_NODE == /sys/* && -r $THROTTLE_NODE ]]; then
            printf 'throttling_node=%s value=' "$THROTTLE_NODE"; cat "$THROTTLE_NODE"
        else
            echo 'throttling=unknown (no readable firmware sysfs node)'
        fi
        ps -eo pid,comm,pcpu
    } >"$1" 2>&1
}
load_variant() {
    local manifest=$1 wanted=$2 row count
    manifest=$(inside "$manifest")
    count=$(awk -F '\t' -v id="$wanted" '$1==id {n++} END {print n+0}' "$manifest")
    [[ $count == 1 ]] || { echo "Expected one manifest entry: $wanted" >&2; exit 2; }
    row=$(awk -F '\t' -v id="$wanted" '$1==id' "$manifest")
    [[ -n $row ]] || exit 2
    IFS=$'\t' read -r VARIANT ARCH OBJECT STAGE PROGRAM LIBDIR TARGET TARGET_SHA TARGET_ID <<<"$row"
    [[ $ARCH == "$(uname -m)" ]] || { echo 'Manifest architecture mismatch' >&2; exit 2; }
    LIBDIR=$(inside "$LIBDIR"); TARGET=$(inside "$TARGET")
    [[ -f $TARGET ]] || exit 2
    local actual
    actual=$(sha256sum "$TARGET"); actual=${actual%% *}
    [[ -n $actual && $actual == "$TARGET_SHA" ]] || { echo 'Target SHA mismatch' >&2; exit 2; }
    [[ $TARGET_ID =~ ^[0-9a-f]{40}$ ]] || { echo 'Expected SHA1 build-id required' >&2; exit 2; }
    export LD_LIBRARY_PATH="$LIBDIR:$BASE/lib"
    if [[ $OBJECT == spike ]]; then
        PROGRAM=$(inside "$PROGRAM")
        [[ -x $PROGRAM ]] || exit 2
    elif [[ $OBJECT == ffmpeg ]]; then
        command -v gst-launch-1.0 >/dev/null
        gst-inspect-1.0 avdec_h264 >"$RUN/gst-inspect-$VARIANT.txt" 2>&1
        grep -q max-threads "$RUN/gst-inspect-$VARIANT.txt" || { echo 'Decoder thread property unavailable' >&2; exit 2; }
    else
        echo 'Unknown object' >&2; exit 2
    fi
    export LD_LIBRARY_PATH="$LIBDIR:$BASE/lib"
}
command_for() {
    local input=$1 checksum_fifo=$2
    if [[ $OBJECT == spike ]]; then
        [[ $input =~ ^[1-9][0-9]*$ ]] || { echo 'Positive spike rounds required' >&2; exit 2; }
        CMD=("$PROGRAM" "$input")
    else
        input=$(inside "$input")
        [[ -f $input ]] || exit 2
        CMD=(gst-launch-1.0 -q filesrc "location=$input" '!' qtdemux '!' h264parse '!' avdec_h264 max-threads=1 '!' video/x-raw,format=I420 '!' filesink "location=$checksum_fifo" sync=false)
    fi
}
watch_maps() {
    local pidfile=$1 output=$2 target=$3 pid actual
    for ((i=0;i<500;i++)); do
        if [[ -s $pidfile ]]; then
            read -r pid <"$pidfile"
            [[ $pid =~ ^[0-9]+$ ]] || return 2
            if [[ -r /proc/$pid/maps ]]; then
                cat "/proc/$pid/maps" >"$output"
                if awk -v path="$target" '$6==path && NF==6 {found=1} END {exit !found}' "$output"; then
                    actual=$(sha256sum "$target"); actual=${actual%% *}
                    [[ $actual == "$TARGET_SHA" ]] || return 3
                    printf 'PID %s TARGET %s SHA %s EXPECTED_BUILD_ID %s\n' "$pid" "$target" "$actual" "$TARGET_ID" >"$output.verified"
                    return 0
                fi
            fi
        fi
        sleep .02
    done
    echo 'Target mapping not observed' >"$output.failure"
    return 4
}
finish_run() {
    snapshot "$RUN/environment.after"
    df -h "$BASE" >"$RUN/df.after"
    rpm -qa | wc -l >"$RUN/rpm-count.after"
    compare_rpm_counts "$(<"$RUN/rpm-count.before")" "$(<"$RUN/rpm-count.after")"
    printf 'RESULTS %s\n' "$RUN"
}

telemetry_loop() {
    local seq=0
    mkdir "$RUN/telemetry"
    while :; do
        snapshot "$RUN/telemetry/$seq.txt"
        seq=$((seq+1))
        sleep 1
    done
}
