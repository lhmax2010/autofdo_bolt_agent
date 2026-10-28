#!/bin/bash
# Run this file with /bin/bash; never source it into an interactive shell.
set -euo pipefail
export TMPDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/tmp
readonly SCRIPT_ID=05_board_verify_after_reboot
readonly LOGDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/logs
step=$SCRIPT_ID
finish() {
    local rc=$? now
    trap - EXIT
    trap '' INT TERM HUP
    set +e
    now=$(date --iso-8601=seconds)
    if (( rc == 0 )); then
        printf 'END %s OK\n' "$now"
        [[ ! -d $LOGDIR ]] || printf 'END %s OK\n' "$now" > "$LOGDIR/$SCRIPT_ID.status"
    else
        printf 'END %s FAILED %s\n' "$now" "$step"
        [[ ! -d $LOGDIR ]] || printf 'END %s FAILED %s\n' "$now" "$step" > "$LOGDIR/$SCRIPT_ID.status"
    fi
    exit "$rc"
}
trap finish EXIT
trap 'step="$SCRIPT_ID:line=$LINENO"' ERR
trap 'step="$SCRIPT_ID:INT"; exit 130' INT
trap 'step="$SCRIPT_ID:TERM"; exit 143' TERM
trap 'step="$SCRIPT_ID:HUP"; exit 129' HUP
mkdir -p "$TMPDIR" "$LOGDIR"
readonly LOG="$LOGDIR/$SCRIPT_ID.$(date +%Y%m%dT%H%M%S%z).log"
exec > >(tee -a "$LOG") 2>&1
printf 'START %s %s\nLOG %s\n' "$(date --iso-8601=seconds)" "$SCRIPT_ID" "$LOG"

# Check remote shell status explicitly; SDB transport status alone is insufficient.
board_shell() {
    local output transport_rc=0
    output=$(sdb -s 192.168.108.26:26101 shell "$1
rc=\$?
printf '\n__AFDO_RC__%s\n' \"\$rc\"
exit \"\$rc\"") || transport_rc=$?
    printf '%s\n' "$output"
    (( transport_rc == 0 )) || return "$transport_rc"
    tr -d '\r' <<< "$output" | grep -qx '__AFDO_RC__0'
}
board_identity() {
    step="$SCRIPT_ID:board-identity"
    board_shell 'model=$(cat /proc/device-tree/model | tr -d "\000"); printf "MODEL %s\n" "$model"; case "$model" in "Raspberry Pi 4 Model B"*) true ;; *) echo "STOP: not Raspberry Pi 4" >&2; false ;; esac'
    step=$SCRIPT_ID
}

sdb connect 192.168.108.26
sdb -s 192.168.108.26:26101 root on
board_identity
step="$SCRIPT_ID:kernel-and-pmu"
board_shell '
set +e
release=$(uname -r); release_rc=$?
version=$(uname -v); version_rc=$?
printf "COMMAND uname -r\n%s\nREMOTE_EXIT %s\nCOMMAND uname -v\n%s\nREMOTE_EXIT %s\n" "$release" "$release_rc" "$version" "$version_rc"
printf "COMMAND ls /sys/bus/event_source/devices/\n"
ls /sys/bus/event_source/devices/; events_rc=$?; printf "REMOTE_EXIT %s\n" "$events_rc"
printf "COMMAND ls -l /sys/bus/platform/devices/pmu/driver\n"
ls -l /sys/bus/platform/devices/pmu/driver; link_rc=$?; printf "REMOTE_EXIT %s\n" "$link_rc"
printf "COMMAND readlink /sys/bus/platform/devices/pmu/driver\n"
driver=$(readlink /sys/bus/platform/devices/pmu/driver); driver_rc=$?
printf "%s\nREMOTE_EXIT %s\n" "$driver" "$driver_rc"
printf "COMMAND dmesg | grep -i -E pmu|perf.*event\n"
dmesg_text=$(dmesg 2>&1); dmesg_rc=$?
if [ "$dmesg_rc" -eq 0 ]; then printf "%s\n" "$dmesg_text" | grep -i -E "pmu|perf.*event"; filter_rc=$?; else printf "%s\n" "$dmesg_text"; filter_rc=NOT_RUN; fi
printf "DMESG_EXIT %s FILTER_EXIT %s\n" "$dmesg_rc" "$filter_rc"
if [ "$version_rc" -ne 0 ] || [ "$version" != "#1 SMP Wed Oct 28 04:12:26 UTC 2026" ] || [ "$release_rc" -ne 0 ] || [ "$release" != "6.12.80-arm-rpi4-v7l" ]; then
    echo "RESULT NEW_KERNEL_NOT_ACTIVE; STOP ENTIRE TASK; NO ROLLBACK OR SAMPLING"
    false
elif [ "$driver_rc" -eq 0 ] && [ "$link_rc" -eq 0 ] && [ "${driver##*/}" = armv8-pmu ]; then
    echo "RESULT HARDWARE_PMU_REGISTERED; SAMPLING_SCOPE software+hardware"
    true
else
    echo "RESULT HARDWARE_PMU_NOT_RESTORED; SAMPLING_SCOPE software-only; NO ROLLBACK"
    true
fi'
