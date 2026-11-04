#!/bin/bash
# Sequential evaluation builds; execute only after every preflight variant passed.
set -Eeuo pipefail
W=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent
export TMPDIR="$W/temp/tmp" PYTHONDONTWRITEBYTECODE=1
D="$W/temp/eval-prep11"
case "${1:-}" in
 --dry-run) shift; exec python3 "$W/tools/profgen/eval_build.py" --dry-run "$@" ;;
 --worker) shift; exec python3 "$W/tools/profgen/eval_build.py" "$@" ;;
 '') ;;
 --object) [[ $# == 2 && ( $2 == spike || $2 == ffmpeg ) ]] || exit 2 ;;
 *) echo 'Usage: eval_build.sh [--dry-run] [--object spike|ffmpeg]' >&2; exit 2 ;;
esac
mkdir -p "$D/build"
exec 9>"$D/build/lock"
flock -n 9 || { echo 'Evaluation worker already running' >&2; exit 1; }
setsid --fork /bin/bash "$W/tools/profgen/eval_build.sh" --worker "$@" 9>&9 >"$D/build/worker.log" 2>&1 </dev/null
echo "Evaluation worker started; artifacts: $D/build"
printf '\ntail -n 20 %s\ncat %s\n' "$D/build/worker.log" "$D/build/status"
