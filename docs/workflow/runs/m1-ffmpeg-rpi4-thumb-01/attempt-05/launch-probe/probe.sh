#!/bin/bash
set -u
out=$1
printf "%s\n" "$$" > "$out/pid"
date +%s > "$out/start"
sleep 20
date +%s > "$out/end"
printf "0\n" > "$out/exit"
