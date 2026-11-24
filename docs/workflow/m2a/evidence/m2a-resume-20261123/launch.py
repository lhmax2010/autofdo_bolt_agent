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
OUT = WORK / 'temp/m2a-resume-20261123'
CODE = WORK / 'temp/m2a-rpi5-wt/workflow'
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
WAIT_CAP = 8 * 3600
CADENCE = 600
spent = 0.0
current_gate_deadline = None


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def add_wait(label, seconds):
    global spent
    spent += max(0, seconds)
    with (OUT / 'wait-budget.jsonl').open('a') as log:
        log.write(json.dumps(dict(at=utc(), operation=label, seconds=seconds,
                                  total_wait_seconds=spent, limit_seconds=WAIT_CAP))+'\n')
        log.flush()
        os.fsync(log.fileno())


def remaining():
    return max(0.0, WAIT_CAP - spent)


def wait_for_host(workdir, destination, timeout=10800, interval=600, exclusive=False):
    global current_gate_deadline
    start = time.monotonic()
    require(remaining() > 0, 'shared cumulative wait budget exhausted', 'environment')
    current_gate_deadline = start + remaining()
    try:
        return ORIGINAL_WAIT(workdir, destination, remaining(), CADENCE, exclusive=True)
    finally:
        current_gate_deadline = None
        add_wait('initial host gate', time.monotonic() - start)


def execute(argv, source, workdir, out, env=None, wait_seconds=172800, experiment=None, exclusive=False):
    global current_gate_deadline
    require(experiment is None, 'no resource waiver authorized')
    require(Path(workdir).resolve() == WORK, 'wrong WORKDIR')
    require(argv[0] == 'gbs' and argv[argv.index('--threads')+1] == '1' and '_smp_mflags -j2' in argv,
            'GBS build invocation does not match authorized limits')
    phase = str(Path(out).relative_to(WORK))
    lock = (WORK / 'temp/host-gbs.lock').open('a+')
    evidence = OUT / ('lock-' + str(time.time_ns()) + '.json')
    state = dict(workflow='m2a-rpi5', phase=phase, pid=os.getpid(), requested_utc=utc(), samples=[])
    state['remaining_wait_seconds'] = remaining()
    acquired = False
    start = time.monotonic()
    try:
        while True:
            slack = remaining() - (time.monotonic() - start)
            require(slack > 0, 'shared GBS lock wait exhausted eight-hour cumulative budget', 'environment')
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except BlockingIOError:
                state['samples'].append(dict(time=utc(), status='lock_busy', other_builds=active_builds()))
                save(evidence, state)
                time.sleep(min(CADENCE, slack))
        add_wait(phase+' lock', time.monotonic() - start)
        state.update(acquired_utc=utc(), status='held', remaining_wait_seconds=remaining())

        def write_holder():
            lock.seek(0)
            lock.truncate()
            lock.write(json.dumps({k: v for k, v in state.items() if k != 'samples'}) + '\n')
            lock.flush()
            os.fsync(lock.fileno())

        write_holder()
        save(evidence, state)
        require(remaining() > 0, 'shared GBS host wait budget exhausted', 'environment')
        current_gate_deadline = time.monotonic() + remaining()
        result = ORIGINAL(argv, source, workdir, out, env, remaining(), exclusive=True)
        add_wait(phase+' readiness gate', result.get('wait_seconds', result['elapsed_seconds']))
        state.update(build_status=result.get('status'), build_exit_code=result.get('exit_code'),
                     unit=result.get('unit'), remaining_wait_seconds=remaining())
        return result
    finally:
        current_gate_deadline = None
        if not acquired:
            add_wait(phase+' lock', time.monotonic() - start)
        state.update(status='released' if acquired else 'not_acquired', ended_utc=utc())
        try:
            if acquired:
                write_holder()
            save(evidence, state)
        finally:
            lock.close()


def can_start(r, experiment=None):
    require(experiment is None, 'no resource waiver authorized')
    if current_gate_deadline is not None and time.monotonic() >= current_gate_deadline:
        return False
    if not r.get('other_builds'):
        r.update(build.resources(WORK))
    return not r.get('other_builds') and r['mem_available'] >= 16 * build.GIB and r['load1'] < 12 and r['disk_free'] >= 50 * build.GIB


def main():
    build.active_builds = active_builds
    build.can_start = can_start
    build.execute = execute
    build.wait_for_host = wait_for_host
    # Leave the original failure receipt and verified S0 receipt intact.
    def failed(self, stage, error):
        save(self.directory / (stage + '.failure-' + str(time.time_ns()) + '.json'),
             dict(stage=stage, status='failed', reason=getattr(error, 'reason', 'error'), error=str(error)))
    Store.failed = failed
    from afdo_wf.cli import main as cli
    return cli(['run', '--job', str(WORK / 'temp/m2a-rpi5-prep-20261119/continuation/job.json'), '--stop-after', 'afdo-audit'])


if __name__ == '__main__':
    raise SystemExit(main())
