#!/bin/bash
set -u
child=
sampler=
finish() { rc=$?; trap - EXIT; if test -n "$child"; then kill -TERM "$child" 2>/dev/null || :; wait "$child" 2>/dev/null || :; fi; if test -n "$sampler"; then kill -TERM "$sampler" 2>/dev/null || :; wait "$sampler" 2>/dev/null || :; fi; printf "%s\n" "$rc" > /opt/afdo_agent/work/synthetic/control/exit; }
trap finish EXIT
trap "exit 143" TERM
trap "exit 130" INT
printf "%s\n" "$$" > /opt/afdo_agent/work/synthetic/control/pid
if test -n "${WF_STANDALONE_SAMPLER:-}"; then taskset -c 0 bash "$WF_STANDALONE_SAMPLER" /opt/afdo_agent/work/synthetic/control/telemetry.tsv "$WF_CAPABILITIES" & sampler=$!; sleep 1; fi
bash round.sh & child=$!
wait "$child"; rc=$?
child=
if test -n "$sampler"; then sleep 2; fi
exit "$rc"
