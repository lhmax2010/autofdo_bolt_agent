#!/bin/bash
set -eu
out=$1; root=$2; here=${0%/*}; . "$here/common.sh"
safe_path "$out"
: > "$out/sha-cache.tsv"; : > "$out/hash-attempts.tsv"
seen='|'; sequence=1
while :; do
    queue="$out/hash-queue/$sequence.ready"
    if test ! -f "$queue"; then
        test ! -f "$out/observer.done" || break
        sleep .05; continue
    fi
    while read -r pid start dev inode path; do
        key="$dev $inode $path"
        case "$seen" in *"|$key|"*) continue;; esac
        printf '%s\t%s\t%s\n' "$dev" "$inode" "$path" >> "$out/hash-encounters.tsv"
        if ! kill -0 "$root" 2>/dev/null; then printf 'process ended before hash: %s %s\n' "$pid" "$key" >> "$out/hash-errors.log"; continue; fi
        major=${dev%:*}; minor=${dev#*:}
        expected_dev=$(( ((16#$major & 4095)<<8) | (16#$minor & 255) | ((16#$minor & ~255)<<12) | ((16#$major & ~4095)<<32) ))
        before=$(stat -Lc '%d %i' "$path" 2>> "$out/hash-errors.log") || continue
        if test "$before" != "$expected_dev $inode"; then printf 'identity mismatch before hash: %s %s\n' "$key" "$before" >> "$out/hash-errors.log"; continue; fi
        read -r begin unused < /proc/uptime
        seen="$seen$key|"
        printf '%s\t%s\t%s\n' "$dev" "$inode" "$path" >> "$out/hash-attempts.tsv"
        digest=$(sha256sum "$path" 2>> "$out/hash-errors.log") || continue
        after=$(stat -Lc '%d %i' "$path" 2>> "$out/hash-errors.log") || continue
        if test "$before" != "$after" || ! kill -0 "$root" 2>/dev/null; then printf 'identity changed or round ended during hash: %s\n' "$key" >> "$out/hash-errors.log"; continue; fi
        read -r end unused < /proc/uptime
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$dev" "$inode" "$path" "${digest%% *}" "$pid" "$start" "$begin" "$end" >> "$out/sha-cache.tsv"
    done < "$queue"
    sequence=$((sequence+1))
done
