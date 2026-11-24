#!/bin/bash
set -eu
daemon_pid=276783
if [[ $(readlink "/proc/$daemon_pid/exe" 2>/dev/null) != '/home/linhao/tizen-studio/tools/sdb (deleted)' ]]; then
    printf 'Shared SDB daemon is unavailable; refusing implicit server restart.\n' >&2
    exit 125
fi
case "${1-}" in
    devices) [[ $# == 1 ]] ;;
    connect|disconnect) [[ $# == 2 && $2 == 192.168.108.25:26101 ]] ;;
    -s) [[ $# -ge 3 && $2 == 192.168.108.25:26101 ]] ;;
    *) printf 'SDB operation outside this run boundary.\n' >&2; exit 125 ;;
esac
exec "${BASH_SOURCE[0]%/*}/sdb-client" "$@"
