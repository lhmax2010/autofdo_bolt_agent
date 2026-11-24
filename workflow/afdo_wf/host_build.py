"""Coordinate GBS with the shared host flock and the resource gates."""
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import pwd
import re
import time

from .common import canonical, require, save
from .exits import failure_reason

BUILD_STAGES = ('build', 'rebuild')
WAIT_FILE = 'gbs-wait.json'
COORDINATION_LIMIT = 8 * 3600
RESOURCE_LIMIT = 3 * 3600
POLL_INTERVAL = 600


def utc(timestamp=None):
    return datetime.fromtimestamp(time.time() if timestamp is None else timestamp, timezone.utc).isoformat()


def lock_path(workdir, host=None):
    require(host is None or isinstance(host, dict), 'host configuration must be an object')
    name = (host or {}).get('gbs_lock', 'temp/host-gbs.lock')
    require(isinstance(name, str) and name.strip(), 'host.gbs_lock must be a path')
    base = Path(workdir).resolve()
    path = (base / name).resolve()
    require(path != base and path.is_relative_to(base), 'GBS lock must be inside WORKDIR')
    return path


def visible_value(read, field, errors):
    try:
        return read()
    except OSError as exc:
        errors[field] = str(exc)
        return None


def redact_argv(argv):
    """Preserve process identification while suppressing credential arguments."""
    result = []
    secret = False
    for arg in argv:
        arg = re.sub(r'(://)[^/@\s]+@', r'\1<redacted>@', arg)
        key, separator, _ = arg.partition('=')
        if secret:
            result.append('<redacted>')
            secret = False
        elif key.startswith('-') and re.search(r'(password|passwd|token|credential|secret|api[-_]?key)', key, re.I):
            result.append(key + '=<redacted>' if separator else arg)
            secret = not separator
        else:
            result.append(arg)
    return result


def active_builds(proc=Path('/proc')):
    """Read visible GBS/rpmbuild processes regardless of their owner."""
    boot = re.search(r'^btime (\d+)$', (proc / 'stat').read_text(), re.M)
    require(boot is not None, '/proc/stat does not provide boot time', 'environment')
    boot = int(boot[1])
    ticks = os.sysconf('SC_CLK_TCK')
    found = []
    for directory in proc.iterdir():
        if not directory.name.isdecimal():
            continue
        errors = {}
        comm = visible_value(lambda: (directory / 'comm').read_text(errors='replace').strip(), 'comm', errors)
        args = visible_value(lambda: (directory / 'cmdline').read_bytes(), 'argv', errors)
        argv = [word.decode(errors='replace') for word in args.rstrip(b'\0').split(b'\0')] if args else []
        names = [comm, *(Path(word).name for word in argv[:1])]
        if argv and Path(argv[0]).name.startswith(('python', 'pypy')) and len(argv) >= 2:
            names.append(Path(argv[1]).name)
        executable = next((name for name in names if name in ('gbs', 'rpmbuild')), None)
        if executable is None:
            continue
        stat = visible_value(lambda: (directory / 'stat').read_text(), 'started_utc', errors)
        fields = stat.rsplit(')', 1)[-1].split() if stat else []
        if fields and fields[0] in ('Z', 'X'):
            continue
        started = utc(boot + int(fields[19]) / ticks) if len(fields) > 19 else None
        status = visible_value(lambda: (directory / 'status').read_text(), 'user', errors)
        uids = re.search(r'^Uid:\s+(\d+)\s+(\d+)', status, re.M) if status else None
        uid = int(uids[2]) if uids else None
        if uid is None:
            errors.setdefault('user', 'effective UID is unavailable')
        try:
            user = pwd.getpwuid(uid).pw_name if uid is not None else None
        except KeyError:
            user = str(uid)
        cwd = visible_value(lambda: os.fsencode(os.readlink(directory / 'cwd')).decode(errors='replace'), 'cwd', errors)
        found.append(dict(pid=int(directory.name), executable=executable, uid=uid, user=user,
                          started_utc=started, cwd=cwd, argv=redact_argv(argv) if args is not None else None,
                          unavailable=errors))
    return sorted(found, key=lambda row: row['pid'])


def observed_owner(lock):
    lock.seek(0)
    info = lock.read(16384).strip()
    try:
        return json.loads(info)
    except ValueError:
        return info or None


class BuildCoordination:
    def __init__(self, path, output, workflow, stage, invocation):
        self.path = path
        self.output = output
        self.workflow = workflow
        self.stage = stage
        self.invocation = invocation
        self.lock = None
        self.acquired = False
        self.waiting = None
        self.remaining = dict(coordination=COORDINATION_LIMIT, resources=RESOURCE_LIMIT)
        self.record = dict(path=str(path), workflow=workflow, stage=stage, invocation=invocation,
                           owner=None, started_utc=utc(), checks=[], limits_seconds=self.remaining.copy())

    def check(self, phase, **data):
        self.record['checks'].append(dict(phase=phase, time_utc=utc(), **data))
        save(self.output, self.record)

    def account_wait(self):
        if self.waiting is not None:
            budget, start = self.waiting
            now = time.monotonic()
            self.remaining[budget] -= now - start
            self.waiting = budget, now

    def check_deadline(self, budget):
        reason = 'gate' if budget == 'resources' else 'lock-timeout'
        require(self.remaining[budget] > 0, 'GBS startup timeout: ' + budget, reason,
                2 if reason == 'gate' else 8)
    def pause(self, budget):
        self.account_wait()
        self.waiting = budget, time.monotonic()
        self.check_deadline(budget)
        time.sleep(min(POLL_INTERVAL, self.remaining[budget]))

    def end_wait(self, *, require_in_time=False):
        self.account_wait()
        if require_in_time and self.waiting is not None:
            budget, _ = self.waiting
            if self.remaining[budget] < 0:
                self.check_deadline(budget)
        self.waiting = None

    def acquire(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = self.path.open('a+', encoding='utf-8', errors='replace')
        while True:
            try:
                fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                self.check('shared-lock', ready=False, observed_owner=observed_owner(self.lock))
                self.pause('coordination')
            else:
                self.acquired = True
                self.end_wait(require_in_time=True)
                break
        self.record['owner'] = dict(workflow=self.workflow, stage=self.stage, invocation=self.invocation,
                                    pid=os.getpid(), started_utc=utc())
        self.lock.seek(0)
        self.lock.truncate()
        self.lock.write(canonical(self.record['owner']))
        self.lock.flush()
        os.fsync(self.lock.fileno())
        self.check('shared-lock', ready=True)

    def ready(self, read_resources, can_start):
        while True:
            builders = active_builds()
            self.check('other-builds', ready=not builders, processes=builders)
            if builders:
                self.pause('coordination')
                continue
            sample = read_resources()
            ready = can_start(sample)
            self.check('resources', ready=ready, readings={k: v for k, v in sample.items() if k != 'meminfo'})
            if ready:
                self.end_wait(require_in_time=True)
                return sample
            self.pause('resources')

    def finish(self, error):
        self.end_wait()
        if self.lock is not None:
            self.lock.close()  # Keep the inode and the last owner's metadata for flock peers.
        self.record.update(ended_utc=utc(), released=self.acquired,
                           waited_seconds={key: self.record['limits_seconds'][key] - remaining
                                           for key, remaining in self.remaining.items()},
                           outcome='success' if error is None else failure_reason(error))
        save(self.output, self.record)
