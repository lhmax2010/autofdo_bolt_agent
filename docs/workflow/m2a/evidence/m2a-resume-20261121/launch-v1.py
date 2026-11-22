"""One-run PM launch policy; original receipt-bound runner files stay unchanged."""
import datetime
import fcntl
import json
import os
from pathlib import Path
import pwd
import re
import sys
import time

WORK = Path('/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent')
OUT = WORK / 'temp/m2a-resume-20261121'
CODE = WORK / 'temp/m2a-rpi5-wt/workflow'
DEADLINE = datetime.datetime(2026, 11, 22, 5, tzinfo=datetime.timezone.utc).timestamp()
sys.path.insert(0, str(CODE))
from afdo_wf import build
from afdo_wf.common import require, save
from afdo_wf.receipts import Store


def redact(words):
    result = []
    hide = False
    for word in words:
        if hide:
            result.append('[REDACTED]')
            hide = False
            continue
        if re.search(r'(?i)(password|passwd|token|secret|credential|authorization)', word):
            if '=' in word:
                word = word.split('=', 1)[0] + '=[REDACTED]'
            else:
                hide = True
        word = re.sub(r'(https?://)[^/@\s]+:[^/@\s]+@', r'\1[REDACTED]@', word)
        result.append(word)
    return result


def active_builds():
    rows = []
    for p in Path('/proc').iterdir():
        if not p.name.isdecimal() or int(p.name) == os.getpid():
            continue
        errors = {}
        try:
            name = (p / 'comm').read_text().strip()
        except FileNotFoundError:
            continue
        except PermissionError as e:
            name = ''
            errors['comm'] = str(e)
        try:
            words = [os.fsdecode(x) for x in (p / 'cmdline').read_bytes().split(b'\0') if x]
        except FileNotFoundError:
            continue
        except PermissionError as e:
            words = []
            errors['argv'] = str(e)
        if not ({name, *(Path(x).name for x in words[:2])} & {'gbs', 'rpmbuild'}):
            continue
        row = dict(pid=int(p.name), comm=name, argv=redact(words), errors=errors)
        try:
            row['user'] = pwd.getpwuid(p.stat().st_uid).pw_name
        except (OSError, KeyError) as e:
            errors['user'] = str(e)
        try:
            row['cwd'] = os.readlink(p / 'cwd')
        except OSError as e:
            errors['cwd'] = str(e)
        try:
            ticks = int((p / 'stat').read_text().rsplit(')', 1)[1].split()[19])
            boot = int(re.search(r'^btime (\d+)', Path('/proc/stat').read_text(), re.M)[1])
            row['started_utc'] = datetime.datetime.fromtimestamp(boot + ticks / os.sysconf('SC_CLK_TCK'), datetime.timezone.utc).isoformat()
        except OSError as e:
            errors['started_utc'] = str(e)
        rows.append(row)
    return sorted(rows, key=lambda x: x['pid'])


ORIGINAL = build.execute
ORIGINAL_WAIT = build.wait_for_host


def wait_for_host(workdir, destination, timeout=10800, interval=600, exclusive=False):
    require(time.time() < DEADLINE, 'absolute GBS wait deadline reached', 'environment')
    return ORIGINAL_WAIT(workdir, destination, max(0, DEADLINE-time.time()), 600, exclusive)


def execute(argv, source, workdir, out, env=None, wait_seconds=172800, experiment=None, exclusive=False):
    require(experiment is None, 'no resource waiver authorized')
    phase = str(Path(out).relative_to(WORK))
    lock = (WORK / 'temp/host-gbs.lock').open('a+')
    evidence = OUT / ('lock-' + str(time.time_ns()) + '.json')
    state = dict(workflow='m2a-rpi5', phase=phase, pid=os.getpid(), deadline_utc='2026-11-22T05:00:00Z', samples=[])
    acquired = False
    try:
        while True:
            require(time.time() < DEADLINE, 'absolute GBS wait deadline reached', 'environment')
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except BlockingIOError:
                state['samples'].append(dict(time=time.time(), status='lock_busy'))
                save(evidence, state)
                time.sleep(min(600, max(0, DEADLINE - time.time())))
        state.update(acquired_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), status='held')
        lock.seek(0)
        lock.truncate()
        lock.write(json.dumps({k: v for k, v in state.items() if k != 'samples'}) + '\n')
        lock.flush()
        os.fsync(lock.fileno())
        save(evidence, state)
        return ORIGINAL(argv, source, workdir, out, env, max(0, DEADLINE-time.time()), exclusive=True)
    finally:
        state.update(status='released' if acquired else 'not_acquired', ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        save(evidence, state)
        lock.close()


def can_start(r, experiment=None):
    require(time.time() < DEADLINE, 'absolute GBS wait deadline reached', 'environment')
    if 'other_builds' in r and not r['other_builds']:
        r.update(build.resources(WORK))
    return r['mem_available'] >= 16 * build.GIB and r['load1'] < 12 and r['disk_free'] >= 50 * build.GIB


def main():
    build.active_builds = active_builds
    build.can_start = can_start
    build.execute = execute
    build.wait_for_host = wait_for_host
    # Existing failure receipt is historical evidence, as are successful receipts.
    def failed(self, stage, error):
        save(self.directory / (stage + '.failure-' + str(time.time_ns()) + '.json'),
             dict(stage=stage, status='failed', reason=getattr(error, 'reason', 'error'), error=str(error)))
    Store.failed = failed
    from afdo_wf.cli import main as cli
    return cli(['run', '--job', str(WORK / 'temp/m2a-rpi5-prep-20261119/continuation/job.json'), '--stop-after', 'afdo-audit'])


if __name__ == '__main__':
    raise SystemExit(main())
