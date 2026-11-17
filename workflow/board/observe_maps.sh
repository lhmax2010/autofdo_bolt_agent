#!/bin/bash
# Full descendant tree via stat PPID; does not depend on pgrep or children files.
set -eu
here=${0%/*}; . "$here/common.sh"; . "$here/proc_tree.sh"
root=$1; out=$2; manifest=$3
safe_path "$out"; safe_path "$manifest"; mkdir -p "$out"
mkdir -p "$out/hash-queue"
hasher=''
finish() { printf 'done\n' > "$out/observer.done"; if test -n "$hasher"; then wait "$hasher" || :; fi; }
trap finish EXIT
trap 'exit 0' TERM INT
bash "$here/hash_maps.sh" "$out" "$root" & hasher=$!
sequence=0
while kill -0 "$root" 2>/dev/null; do
    sequence=$((sequence+1))
    read -r stamp unused < /proc/uptime
    printf '%s %s\n' "$sequence" "$stamp" >> "$out/samples.tsv"
    proc_table /proc "$out/tree-$sequence.tsv" "$out/enumeration-errors.log"
    proc_descendants "$root" "$out/tree-$sequence.tsv" > "$out/selected-$sequence.tsv"
    : > "$out/hash-queue/$sequence.pending"
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
        awk 'NF>=6 && $6 ~ /^\/opt\/afdo_agent\// {print $4, $5, $6}' "$snap/maps.txt" | sort -u > "$snap/mapped-identities.tsv"
        while read -r dev inode path; do
            printf '%s %s %s %s %s\n' "$pid" "$start" "$dev" "$inode" "$path" >> "$out/hash-queue/$sequence.pending"
        done < "$snap/mapped-identities.tsv"
        printf '%s\n' "$ok" > "$snap/complete"
    done < "$out/selected-$sequence.tsv"
    mv "$out/hash-queue/$sequence.pending" "$out/hash-queue/$sequence.ready"
    sleep .1
done
