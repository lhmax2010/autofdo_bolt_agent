#!/bin/bash
set -eu
here=${0%/*}; . "$here/common.sh"
out=$1; capabilities=$2
safe_path "$out"; safe_path "$capabilities"; test ! -e "$out"
# capabilities TSV: frequency|temperature|voltage<TAB>read-only sysfs path.
# Each SAMPLE/END envelope permits detection of a truncated final line.
trap 'exit 0' TERM INT
while :; do
    stamp=$(awk '{print $1}' /proc/uptime)
    printf 'SAMPLE\t%s\n' "$stamp" >> "$out"
    while IFS="$(printf '\t')" read -r kind path; do
        case "$kind:$path" in frequency:/sys/*|temperature:/sys/*|voltage:/sys/*) ;; *) exit 2;; esac
        if value=$(cat "$path" 2>/dev/null); then
            printf '%s\t%s\t%s\t%s\n' "$stamp" "$kind" "$path" "$value" >> "$out"
        else
            printf '%s\t%s\t%s\tunknown\n' "$stamp" "$kind" "$path" >> "$out"
        fi
    done < "$capabilities"
    printf 'END\t%s\n' "$stamp" >> "$out"
    sleep 1
done
