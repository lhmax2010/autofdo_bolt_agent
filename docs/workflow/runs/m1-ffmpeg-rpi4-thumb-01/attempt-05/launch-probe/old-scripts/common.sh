#!/bin/bash
# Source only. All persistent writes are restricted to the experiment tree.
set -eu
set -o pipefail
safe_path() {
    case "$1" in /opt/afdo_agent/*) ;; *) echo 'unsafe output path' >&2; return 2;; esac
    case "$1" in *'/../'*|*'/..'|*'/./'*) return 2;; esac
}
step_log() {
    safe_path "$1"
    test ! -e "$1" || { echo 'step log already exists' >&2; return 2; }
    mkdir -p "${1%/*}"
    exec >"$1" 2>&1
}
assert_identity() {
    test "$(cat /proc/device-tree/model | tr -d '\000')" = "$1"
    test "$(uname -m)" = "$2"
    test "$(uname -r)" = "$3"
    test "$(sed -n 's/^TZ_BUILD_ID=//p' /etc/tizen-build.conf | tr -d '\"')" = "$4"
}
precheck() {
    missing=''
    for c in cat tr uname sed mkdir sha256sum chmod ldd setsid sleep kill date awk readlink taskset bash sort grep stat; do
        command -v "$c" >/dev/null 2>&1 || missing="$missing $c"
    done
    test -z "$missing" || { echo "missing commands:$missing" >&2; return 2; }
}
