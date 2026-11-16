#!/bin/bash
set -eu
here=${0%/*}; . "$here/common.sh"
manifest=$1; log=$2
safe_path "$manifest"; step_log "$log"
# Manifest is SHA256<TAB>absolute path; built on host from packaged real files.
while IFS="$(printf '\t')" read -r expected path; do
    safe_path "$path"; test -f "$path"
    actual=$(sha256sum "$path"); actual=${actual%% *}
    test "$actual" = "$expected" || { echo "SHA mismatch: $path"; exit 3; }
    printf 'verified\t%s\t%s\n' "$expected" "$path"
done < "$manifest"
