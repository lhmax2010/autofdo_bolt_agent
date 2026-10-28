#!/bin/bash
# Detachment repair is syntax-checked only; validate on the next authorized build.
set -Eeuo pipefail

readonly WORKDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent
readonly WORKTREE=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/linux-rpi-pmuv3
readonly SOURCE=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/src/linux-rpi
readonly EXPECTED_HEAD=c27f160de761bb55f64672ceac642698a6e93684
readonly GBS_HOME=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/gbs-home
readonly GBS_CONFIG=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/gbs/gbs_rpi4_image.conf
readonly GBS_TMP=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/gbs-tmp-pmuv3
readonly BUILDROOT=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-RPI4-PMUV3
readonly LOGDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/logs
readonly LOG=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/logs/build_pmuv3.log
readonly STATUS=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/logs/build_pmuv3.status
readonly PIDFILE=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/logs/build_pmuv3.pid
readonly LOCK=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/logs/build_pmuv3.lock
readonly CONFIG_SHA256=c4dfc2d24398e7f8afb1d6d10dc9161a2a9e40c88d59a9b21ccda2ad8b05a945
# depanneur 0.16.30 data/gbs:1-13 grants NOPASSWD to its build commands.
# No privileged command is executed by this wrapper. GBS invokes sudo internally.
export TMPDIR=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/tmp
mkdir -p "$TMPDIR" "$LOGDIR"

# Only an internal worker with the inherited lock may bypass foreground checks.
worker_mode=0
if [[ ${1:-} == --worker ]]; then
    [[ $# == 3 && $3 =~ ^[1-9][0-9]*$ ]] || exit 2
    [[ /proc/$$/fd/9 -ef "$LOCK" ]] || exit 2
    flock -n 9 || exit 2
    worker_mode=1
else
    # A concurrent launch must not overwrite the active run's log/status.
    exec 9>"$LOCK"
    if ! flock -n 9; then
        printf 'ERROR: another PMUv3 build wrapper owns %s; left its log/status intact.\n' "$LOCK" >&2
        exit 1
    fi
fi

start_time=$(date --iso-8601=seconds)
phase=PREFLIGHT
gbs_exit=NOT_STARTED
gbs_pid=
handoff=0
failure_reason=

finish() {
    local wrapper_exit=$? end_time verdict=FAILED inventory_exit=0
    # The foreground parent transfers both status ownership and lock to the worker.
    if (( handoff )); then return; fi
    trap - EXIT
    trap '' INT TERM HUP
    set +e
    end_time=$(date --iso-8601=seconds)
    if [[ $phase == COMPLETED && $gbs_exit == 0 && $wrapper_exit == 0 ]]; then
        verdict=OK
    fi
    {
        printf 'START %s\nEND %s\nHEAD %s\nPHASE %s\nGBS_EXIT %s\nWRAPPER_EXIT %s\n' \
            "$start_time" "$end_time" "$EXPECTED_HEAD" "$phase" "$gbs_exit" "$wrapper_exit"
        printf 'REASON %s\nRPM-LIST-BEGIN\n' "${failure_reason:-none}"
        # Metadata-only scan: root ownership is harmless if directories are searchable.
        # Permission errors propagate through pipefail to RPM_LIST_EXIT/FAILED.
        # Only the dedicated output repository; exclude dependency RPMs.
        if [[ -d $BUILDROOT/local/repos ]]; then
            nice -n 19 ionice -c3 find "$BUILDROOT/local/repos" -type f -name '*.rpm' -print | LC_ALL=C sort
            inventory_exit=$?
        else
            printf '(none)\n'
        fi
        printf 'RPM-LIST-END\nRPM_LIST_EXIT %s\n' "$inventory_exit"
        if (( inventory_exit != 0 )); then verdict=FAILED; fi
        printf 'ALL-END %s %s\n' "$end_time" "$verdict"
    } > "$STATUS.$BASHPID.tmp"
    mv -f -- "$STATUS.$BASHPID.tmp" "$STATUS"
}

on_signal() {
    local signal=$1 code=$2
    trap '' INT TERM HUP
    phase=INTERRUPTED
    failure_reason="received $signal"
    if [[ -n $gbs_pid ]]; then
        # setsid gives the GBS job its own group; do not signal other sessions.
        # Root descendants may reject this user's signal; depanneur also handles TERM.
        kill -TERM -- "-$gbs_pid" 2>/dev/null || kill -TERM "$gbs_pid" 2>/dev/null || true
        if wait "$gbs_pid"; then gbs_exit=0; else gbs_exit=$?; fi
    fi
    exit "$code"
}
trap finish EXIT
trap 'on_signal INT 130' INT
trap 'on_signal TERM 143' TERM
trap 'on_signal HUP 129' HUP

fail() {
    failure_reason=$1
    printf 'ERROR: %s\n' "$failure_reason" >&2
    exit 1
}

if (( worker_mode )); then
    start_time=$2
    jobs=$3
    phase=BUILDING
    # The complete worker owns a new session, all stdio, and the inherited fd 9.
    trap '' HUP
    printf '%s\n' "$BASHPID" > "$PIDFILE.tmp"
    mv -f -- "$PIDFILE.tmp" "$PIDFILE"
    printf 'START %s\nHEAD %s\nWORKER_PID %s\n' "$start_time" "$EXPECTED_HEAD" "$BASHPID"
    cd "$WORKTREE"
    # --wait propagates the program exit status even if setsid has to fork.
    setsid --wait /usr/bin/env -u VIRTUAL_ENV -u GIT_CONFIG_GLOBAL -u GIT_CONFIG_SYSTEM \
        -u GIT_CONFIG -u GIT_CONFIG_COUNT \
        HOME="$GBS_HOME" GIT_CONFIG_NOSYSTEM=1 TMPDIR="$GBS_TMP" \
        XDG_CONFIG_HOME="$GBS_HOME/.config" XDG_CACHE_HOME="$GBS_HOME/.cache" \
        nice -n 19 ionice -c3 /usr/bin/gbs -c "$GBS_CONFIG" build -A armv7l \
        --threads 1 --define "_smp_mflags -j$jobs" </dev/null &
    gbs_pid=$!
    printf 'START %s\nHEAD %s\nPHASE BUILDING\nWORKER_PID %s\nGBS_PID %s\nGBS_EXIT RUNNING\n' \
        "$start_time" "$EXPECTED_HEAD" "$BASHPID" "$gbs_pid" > "$STATUS"
    printf 'GBS_PID %s\nCOMMAND: HOME=%s GIT_CONFIG_NOSYSTEM=1 nice -n 19 ionice -c3 /usr/bin/gbs -c %s build -A armv7l --threads 1 --define "_smp_mflags -j%s"\n' \
        "$gbs_pid" "$GBS_HOME" "$GBS_CONFIG" "$jobs"
    if wait "$gbs_pid"; then gbs_exit=0; else gbs_exit=$?; fi
    phase=COMPLETED
    if (( gbs_exit != 0 )); then failure_reason='GBS returned a nonzero exit code'; fi
    exit "$gbs_exit"
fi

[[ $# == 0 ]] || fail 'This script accepts no arguments.'
for tool in git nice ionice gbs depanneur dpkg-query nproc df ps awk sha256sum cmp setsid find sort date flock sleep; do
    command -v "$tool" >/dev/null || fail "Required system command missing: $tool"
done
[[ -d $WORKTREE ]] || fail "Missing worktree: $WORKTREE"
branch=$(git -C "$WORKTREE" symbolic-ref --short HEAD) || fail 'Cannot read worktree branch.'
[[ $branch == afdo/pmuv3 ]] || fail "Wrong worktree branch: $branch"
head=$(git -C "$WORKTREE" rev-parse HEAD) || fail 'Cannot read worktree HEAD.'
[[ $head == "$EXPECTED_HEAD" ]] || fail "Unexpected worktree HEAD: $head"
changes=$(nice -n 19 ionice -c3 git -C "$WORKTREE" status --porcelain) || fail 'Cannot inspect worktree status.'
[[ -z $changes ]] || fail "Worktree is not clean: $changes"
changes=$(nice -n 19 ionice -c3 git -C "$SOURCE" status --porcelain) || fail 'Cannot inspect original source status.'
[[ -z $changes ]] || fail "Original source is not clean: $changes"
[[ -f $GBS_HOME/.gbs.conf && ! -L $GBS_HOME/.gbs.conf ]] || fail 'Dedicated HOME .gbs.conf is missing or a symlink.'
cmp -s "$GBS_HOME/.gbs.conf" <(printf '[general]\ntmpdir = %s\n' "$GBS_TMP") || fail 'Dedicated HOME .gbs.conf differs from the prepared minimal configuration.'
[[ ! -e /etc/gbs.conf && ! -L /etc/gbs.conf ]] || fail '/etc/gbs.conf exists; stop to avoid merging system GBS configuration.'
[[ -f $GBS_CONFIG && ! -L $GBS_CONFIG ]] || fail 'Pinned GBS configuration is missing or a symlink.'
printf '%s  %s\n' "$CONFIG_SHA256" "$GBS_CONFIG" | sha256sum --check --status || fail 'Pinned GBS configuration has changed.'
# GBS also searches .repo ancestors for configuration. Refuse unexpected inputs.
ancestor=$WORKTREE
while :; do
    if [[ -e $ancestor/.repo && -e $ancestor/.gbs.conf ]]; then
        fail "Unexpected repo-tool configuration at $ancestor/.gbs.conf"
    fi
    [[ $ancestor == / ]] && break
    ancestor=${ancestor%/*}
    [[ -n $ancestor ]] || ancestor=/
done
installed_gbs=$(dpkg-query -W -f='${Version}' gbs) || fail 'Cannot identify installed GBS version.'
installed_depanneur=$(dpkg-query -W -f='${Version}' depanneur) || fail 'Cannot identify installed depanneur version.'
[[ $installed_gbs == 2.1.0 && $installed_depanneur == 0.16.30 ]] || fail 'Tool versions differ from the sudo/configuration source review; recheck before building.'
printf 'Disk space (informational; no threshold):\n'
df -h "$WORKDIR"
printf '\nExisting GBS processes (informational; no action taken):\n'
ps -eo pid,ppid,args | awk '/[g]bs/ && !/awk/ { print; found=1 } END { if (!found) print "(none)" }'
cpus=$(nproc)
[[ $cpus =~ ^[0-9]+$ && $cpus -gt 0 ]] || fail 'nproc did not return a positive CPU count.'
jobs=$((cpus / 2))
(( jobs >= 1 )) || jobs=1
printf '\nCPU count=%s; make jobs=%s; GBS package threads=1.\n' "$cpus" "$jobs"
printf 'depanneur 0.16.30 ships NOPASSWD rules; skipping sudo -v. No password is expected.\n'
printf 'If local sudo policy differs, the detached build cannot prompt and will report FAILED.\n'
mkdir -p "$GBS_TMP" "$GBS_HOME/.config" "$GBS_HOME/.cache"
printf 'START %s\nHEAD %s\nPHASE STARTING\nGBS_EXIT NOT_STARTED\n' "$start_time" "$EXPECTED_HEAD" > "$STATUS"

# Detach the entire status-owning worker, not just GBS. fd 9 stays open across exec.
# No shell job-control is enabled; the GBS setsid child can be waited for directly.
rm -f -- "$PIDFILE"
handoff=1
if ! setsid --fork /bin/bash "$WORKDIR/scripts/build_pmuv3_kernel.sh" \
    --worker "$start_time" "$jobs" 9>&9 > "$LOG" 2>&1 </dev/null; then
    handoff=0
    fail 'Could not start the detached worker.'
fi
# Wait only for the worker acknowledgement, never for the build in the foreground.
for ((attempt=0; attempt<100; attempt++)); do
    [[ -s $PIDFILE ]] && break
    sleep 0.1
done
if [[ ! -s $PIDFILE ]]; then
    printf 'ERROR: worker acknowledgement missing; inspect %s and %s; do not relaunch blindly.\n' "$LOG" "$STATUS" >&2
    exit 1
fi
read -r worker_pid < "$PIDFILE"
printf 'Background worker PID=%s; kernel HEAD=%s\n' "$worker_pid" "$EXPECTED_HEAD"
printf 'To request interruption: kill -TERM %s\n' "$worker_pid"
printf '\n'
# Keep these as the final foreground output, ready to copy.
printf 'tail -f %s\ncat %s\n' "$LOG" "$STATUS"
