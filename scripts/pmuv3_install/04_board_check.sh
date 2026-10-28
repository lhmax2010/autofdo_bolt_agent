#!/bin/bash
# Run this file with /bin/bash; never source it into an interactive shell.
set -euo pipefail
export TMPDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/tmp
readonly SCRIPT_ID=04_board_check
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

board_identity
/bin/bash /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/pmuv3-install/run-board.sh check
