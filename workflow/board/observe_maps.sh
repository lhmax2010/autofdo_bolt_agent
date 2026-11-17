#!/bin/bash
# Full descendant tree via stat PPID; does not depend on pgrep or children files.
set -eu
here=${0%/*}; . "$here/common.sh"; . "$here/proc_tree.sh"
root=$1; out=$2; manifest=$3
safe_path "$out"; safe_path "$manifest"; mkdir -p "$out"
trap 'exit 0' TERM INT
sequence=0
while kill -0 "$root" 2>/dev/null; do
    sequence=$((sequence+1))
    read -r stamp unused < /proc/uptime
    printf '%s %s\n' "$sequence" "$stamp" >> "$out/samples.tsv"
    proc_table /proc "$out/tree-$sequence.tsv" "$out/enumeration-errors.log"
    proc_descendants "$root" "$out/tree-$sequence.tsv" > "$out/selected-$sequence.tsv"
    while read -r pid ppid pgid sid start; do
        snap="$out/$sequence-$pid"
        mkdir -p "$snap"
        printf '%s %s %s %s %s %s\n' "$pid" "$ppid" "$pgid" "$sid" "$start" "$stamp" > "$snap/identity.txt"
        ok=1
        for field in stat comm cmdline maps; do
            if cat "/proc/$pid/$field" > "$snap/$field.txt" 2>> "$snap/errors.log"; then :; else
                printf 'read failed /proc/%s/%s\n' "$pid" "$field" >> "$snap/errors.log"; ok=0
            fi
        done
        if cat "/proc/$pid/stat" > "$snap/stat-after.txt" 2>> "$snap/errors.log"; then
            read -r line < "$snap/stat-after.txt"; tail=${line##*) }; set -- $tail
            if test "$#" -lt 20 || test "${20}" != "$start"; then ok=0; printf 'PID identity changed\n' >> "$snap/errors.log"; fi
        else ok=0; printf 'process exited during snapshot\n' >> "$snap/errors.log"; fi
        awk 'NF>=6 && $6 ~ /^\/opt\/afdo_agent\// {print $6}' "$snap/maps.txt" | sort -u > "$snap/mapped-paths.txt"
        : > "$snap/mapped-sha256.txt"
        while IFS= read -r path; do
            if sha256sum "$path" >> "$snap/mapped-sha256.txt" 2>> "$snap/errors.log"; then :; else ok=0; fi
        done < "$snap/mapped-paths.txt"
        printf '%s\n' "$ok" > "$snap/complete"
    done < "$out/selected-$sequence.tsv"
    sleep .1
done
