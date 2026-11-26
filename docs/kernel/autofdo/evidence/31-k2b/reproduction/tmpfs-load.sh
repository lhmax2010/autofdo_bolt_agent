#!/bin/bash
set -euo pipefail
file=$1
[[ $file =~ ^/opt/afdo_agent/k2b-kgcov/session-0[123](-retry)?/tmp/bench/tmpfs\.payload$ ]]
trap 'rm -f -- "$file"' EXIT
dd if=/dev/zero of="$file" bs=1048576 count=48
[[ $(stat -c %s "$file") == 50331648 ]]
dd if="$file" of=/dev/null bs=1048576 count=48
