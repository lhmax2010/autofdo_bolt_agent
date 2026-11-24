#!/bin/bash
set -eu
here=${0%/*}; . "$here/common.sh"
pid=$1; out=$2; manifest=$3
case "$pid" in ''|*[!0-9]*) exit 2;; esac
safe_path "$out"; safe_path "$manifest"
test ! -e "$out"; mkdir -p "$out"
cat "/proc/$pid/maps" > "$out/maps.txt"
# SHA every mapped deployment file; host checks must_load AND deploy_set globs.
awk 'NF>=6 && $6 ~ /^\/opt\/afdo_agent\// {print $6}' "$out/maps.txt" | sort -u > "$out/mapped-paths.txt"
while IFS= read -r path; do
    safe_path "$path"; sha256sum "$path"
done < "$out/mapped-paths.txt" > "$out/mapped-sha256.txt"
# System paths are deliberately retained in maps.txt for host rejection.
