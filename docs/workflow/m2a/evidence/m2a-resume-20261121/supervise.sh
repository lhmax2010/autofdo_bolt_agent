#!/bin/bash
export TMPDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/tmp
export PYTHONDONTWRITEBYTECODE=1
python3 /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2a-resume-20261121/launch.py >/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2a-resume-20261121/run.log 2>&1
rc=$?
printf "exit_code=%s\n" "$rc" >/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2a-resume-20261121/end.txt
date -u +%FT%TZ >>/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2a-resume-20261121/end.txt
exit "$rc"
