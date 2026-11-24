#!/bin/bash
set -u
out="${BASH_SOURCE[0]%/*}"
export TMPDIR="${out%/*}/tmp"
export PYTHONDONTWRITEBYTECODE=1
export PATH="${out%/*}/m2a-resume-20261123/bin:$PATH"
export PYTHONPATH="$PWD/workflow"
date -u +%FT%TZ > "$out/start.utc"
python3 -u "$out/launch.py" > "$out/run.log" 2>&1
rc=$?
printf 'exit_code=%s\n' "$rc" > "$out/end.txt"
date -u +%FT%TZ >> "$out/end.txt"
exit "$rc"
