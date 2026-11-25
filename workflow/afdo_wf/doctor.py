"""Read-only local diagnostics for preparing a workflow job."""
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

from . import build
from .common import sha256


def tool_version(name, flag):
    path = shutil.which(name)
    if path is None:
        return 'missing', dict(check=name, detail='executable not found on PATH')
    row = dict(check=name, path=path)
    try:
        result = subprocess.run([path, flag], capture_output=True, text=True, errors='replace', timeout=10)
    except (OSError, subprocess.TimeoutExpired) as error:
        return 'unknown', dict(row, detail=str(error))
    version = (result.stdout.strip() or result.stderr.strip()).splitlines()
    if result.returncode != 0 or not version:
        return 'unknown', dict(row, exit_code=result.returncode, detail='version query did not succeed')
    return 'ok', dict(row, version=version[0])


def file_identity(check, entry, key):
    if not isinstance(entry, dict):
        return 'unknown', dict(check=check, detail='malformed tool lock')
    path, expected = entry.get(key), entry.get('sha256')
    if not isinstance(path, str) or not path or not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
        return 'unknown', dict(check=check, detail='expected a path and a lowercase SHA-256')
    file = Path(path)
    row = dict(check=check, path=path, expected_sha256=expected)
    try:
        if not file.is_file():
            return 'missing', row
        actual = sha256(file)
    except FileNotFoundError:
        return 'missing', row
    except OSError as error:
        return 'unknown', dict(row, detail=str(error))
    return ('ok' if actual == expected else 'mismatch'), dict(row, sha256=actual)


def inspect(workdir, job=None):
    report = {name: [] for name in ('ok', 'missing', 'mismatch', 'unknown')}
    report['ok'].append(dict(check='python', path=sys.executable, version=platform.python_version()))
    for name, flag in (('git', '--version'), ('sdb', 'version'), ('gbs', '--version')):
        state, row = tool_version(name, flag)
        report[state].append(row)

    try:
        sample = build.resources(workdir)
    except (OSError, TypeError, ValueError) as error:
        report['unknown'].append(dict(check='host_resources', workdir=str(workdir), detail=str(error)))
    else:
        for name, checks in build.startup_checks(sample).items():
            report['ok' if checks['passed'] else 'mismatch'].append(dict(check=name, **checks, workdir=str(workdir)))

    if job is None:
        return report

    tools = job.get('tools')
    if isinstance(tools, dict) and tools:
        for name, entry in sorted(tools.items()):
            state, row = file_identity('tools.' + name, entry, 'path')
            report[state].append(row)
    else:
        report['unknown'].append(dict(check='tools', detail='job has no host tool locks'))
    board_tools = job.get('board_tools')
    if isinstance(board_tools, list) and board_tools:
        for index, entry in enumerate(board_tools):
            state, row = file_identity(f'board_tools[{index}]', entry, 'source')
            report[state].append(row)
    else:
        report['unknown'].append(dict(check='board_tools', detail='job has no local copies of locked board tools'))
    return report
