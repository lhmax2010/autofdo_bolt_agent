#!/bin/bash
set -u
out="${BASH_SOURCE[0]%/*}"
export TMPDIR="${out%/*}/tmp"
export PYTHONDONTWRITEBYTECODE=1
export PATH="$out/bin:$PATH"
date -u +%FT%TZ > "$out/runner-start.utc"
python3 -u "$out/launch.py" > "$out/run.log" 2>&1
rc=$?
printf 'exit_code=%s\n' "$rc" > "$out/end.txt"
date -u +%FT%TZ >> "$out/end.txt"
exit "$rc"
