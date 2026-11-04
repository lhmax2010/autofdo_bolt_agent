#!/usr/bin/env python3
"""Serial GBS builds; independent logs, resource samples and terminal status.

Only GBS receives HOME/GIT_CONFIG_NOSYSTEM. No terminal input or sudo prompting
is arranged. Catchable interruption terminates only this worker's GBS group.
SIGKILL/power loss cannot be handled by a process-level finally block.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

W = Path('/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent')
D = W / 'temp/eval-prep11'
B = D / 'build'
GBS_STARTED = False
LAST_GBS_RC = 'NOT_STARTED'


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec='seconds')


def resources():
    with (B / 'resources.txt').open('a') as f:
        f.write(now() + '\n')
        f.flush()
        for cmd in [['free', '-m'], ['uptime']]:
            subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=True)


def main():
    global GBS_STARTED, LAST_GBS_RC
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--object', choices=['spike', 'ffmpeg'])
    args = parser.parse_args()
    count = subprocess.check_output(['nproc'], text=True).strip()
    if not count or not count.isdigit() or int(count) < 1:
        raise RuntimeError('nproc did not return a positive integer')
    jobs = max(1, int(count) // 2)
    manifest = json.loads((D / 'build-manifest.json').read_text())
    if args.object:
        manifest = [x for x in manifest if x['object'] == args.object]
    scope = json.loads((D / 'preflight-scope.json').read_text())
    if hashlib.sha256((D / 'preflight-summary.json').read_bytes()).hexdigest() != scope['preflight_summary_sha256']:
        raise RuntimeError('Preflight summary changed')
    checked = json.loads((D / 'preflight-summary.json').read_text())
    required = {(x['isa'], x['variant']) for x in manifest}
    passed = {(x['mode'], x['variant']) for x in checked
              if x['compile_exit'] == x['driver_exit'] == x.get('record_exit') == 0
              and all(x.get('checks', {}).values())}
    if required != passed:
        raise RuntimeError('Missing/failed representative preflight: ' + repr(required - passed))
    commands = []
    for row in manifest:
        for key in ['source', 'config', 'root']:
            if not Path(row[key]).is_relative_to(W) or not Path(row[key]).exists():
                raise RuntimeError('Invalid workspace path: ' + row[key])
        head = subprocess.check_output(['git', '-C', row['source'], 'rev-parse', 'HEAD'], text=True).strip()
        if not head or head != scope['sources'][row['source']]:
            raise RuntimeError('Source changed since representative preflight: ' + row['source'])
        if hashlib.sha256(Path(row['config']).read_bytes()).hexdigest() != scope['configs'][row['config']]:
            raise RuntimeError('GBS configuration changed since preflight')
        clean = subprocess.check_output(['git', '-C', row['source'], 'status', '--porcelain'], text=True)
        if clean:
            raise RuntimeError('Uncommitted evaluation source: ' + row['source'])
        cmd = ['setsid', '--wait', 'nice', '-n', '19', 'ionice', '-c3', 'gbs', '-c', row['config'],
               'build', '--overwrite', '-A', row['arch'], '--threads', '1', '--define', f'_smp_mflags -j{jobs}',
               '--define', 'eval_isa ' + row['isa'], '--define', 'eval_variant ' + row['variant']]
        commands.append((row, cmd))
    if args.dry_run:
        for row, cmd in commands:
            print(json.dumps(dict(id=row['id'], cwd=row['source'], command=cmd), ensure_ascii=False))
        return 0
    B.mkdir(exist_ok=True)
    started = now()
    results = []
    process = None
    error = None
    current = None
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    def interrupted(sig, frame):
        raise InterruptedError('Signal ' + str(sig))
    signal.signal(signal.SIGINT, interrupted)
    signal.signal(signal.SIGTERM, interrupted)
    try:
        (B / 'status').write_text(f'START {started}\nPHASE PREFLIGHT_COMPLETE\n')
        for row, cmd in commands:
            # Check other sessions before starting each variant. Never kill them.
            while True:
                names = subprocess.check_output(['ps', '-eo', 'stat=,comm='], text=True).splitlines()
                heavy = [n.split()[1] for n in names if len(n.split()) == 2 and not n.split()[0].startswith('Z') and n.split()[1] in
                         {'ninja', 'make', 'gbs', 'depanneur', 'clang', 'clang-22', 'ld.lld'}]
                if not heavy:
                    break
                print('WAIT_OTHER_BUILD', now(), heavy, flush=True)
                (B / 'status').write_text(f'START {started}\nWAIT_OTHER_BUILD {now()} {heavy!r}\n')
                resources()
                time.sleep(600)
            current = dict(id=row['id'], start=now(), command=cmd, gbs_exit='NOT_STARTED')
            (B / 'status').write_text(f'START {started}\nRUNNING {row["id"]} {current["start"]}\n')
            print('BUILD_START', json.dumps(current), flush=True)
            resources()
            start_epoch = time.time()
            tick = time.monotonic()
            env = os.environ.copy()
            env.update(HOME=str(W / 'temp/gbs-home'), GIT_CONFIG_NOSYSTEM='1')
            with (B / (row['id'] + '.log')).open('w') as log:
                process = subprocess.Popen(cmd, cwd=row['source'], env=env, stdin=subprocess.DEVNULL,
                                           stdout=log, stderr=subprocess.STDOUT)
                GBS_STARTED = True
                LAST_GBS_RC = 'RUNNING'
                while process.poll() is None:
                    time.sleep(2)
                    if time.monotonic() - tick >= 600:
                        resources()
                        tick = time.monotonic()
                LAST_GBS_RC = process.wait()
                current.update(gbs_exit=LAST_GBS_RC, end=now(), seconds=time.time() - start_epoch)
            process = None
            saved = B / row['id']
            saved.mkdir(exist_ok=True)
            artifacts = []
            for p in sorted((Path(row['root']) / 'local/repos').rglob('*.rpm')):
                if p.stat().st_mtime < start_epoch - 2:
                    continue
                dest = saved / p.name
                shutil.copyfile(p, dest)
                artifacts.append(dict(path=str(dest), bytes=dest.stat().st_size,
                                      sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
            current['rpms'] = artifacts
            root = Path(row['root']) / 'local/BUILD-ROOTS' / ('scratch.' + row['arch'] + '.0')
            builddir = root / 'home/abuild/rpmbuild/BUILD' / ('eval-spike-1.0' if row['object'] == 'spike' else 'ffmpeg-8.0.1')
            for rel in ['ffbuild/config.mak', 'config.h']:
                p = builddir / rel
                if p.exists():
                    shutil.copyfile(p, saved / p.name)
            results.append(current)
            current['artifact_check'] = bool(artifacts)
            verdict = 'OK' if current['gbs_exit'] == 0 and artifacts else 'FAILED'
            end = f'ALL-END {current["end"]} {verdict}'
            with (B / (row['id'] + '.log')).open('a') as f:
                f.write(f'\nGBS_EXIT {current["gbs_exit"]}\n{end}\n')
            (B / (row['id'] + '.status')).write_text(json.dumps(current, indent=2) + '\n' + end + '\n')
            print('BUILD_END', json.dumps(current), end, flush=True)
            (B / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
            if current['gbs_exit'] != 0:
                raise RuntimeError('GBS failed: ' + row['id'])
            if not artifacts:
                raise RuntimeError('GBS returned success but no new RPM: ' + row['id'])
            current = None
        resources()
    except BaseException as e:
        error = repr(e)
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            rc = process.wait()
            LAST_GBS_RC = rc
            if current is not None:
                current.update(gbs_exit=rc, end=now())
        if current is not None and current not in results:
            results.append(current)
            end = f'ALL-END {now()} FAILED'
            with (B / (current['id'] + '.log')).open('a') as f:
                f.write(f'\nGBS_EXIT {current["gbs_exit"]}\n{end}\n')
            (B / (current['id'] + '.status')).write_text(json.dumps(current, indent=2) + '\n' + end + '\n')
    finally:
        summary = dict(start=started, end=now(), error=error, results=results,
                       not_started=[r['id'] for r, c in commands if r['id'] not in {x['id'] for x in results}])
        (B / 'results.json').write_text(json.dumps(summary, indent=2) + '\n')
        end = f'ALL-END {now()} ' + ('FAILED' if error else 'OK')
        (B / 'status').write_text(json.dumps(summary, indent=2) + '\n' + end + '\n')
        print(end, 'ERROR', error, flush=True)
    return 1 if error else 0


if __name__ == '__main__':
    try:
        exit_code = main()
    except BaseException as exc:
        if '--dry-run' in sys.argv or isinstance(exc, SystemExit):
            raise
        # Also terminate a preflight/worker bookkeeping failure explicitly.
        # Preserve the last observed real rc; never invent a successful build.
        B.mkdir(parents=True, exist_ok=True)
        stamp = now()
        failure = dict(end=stamp, phase='worker' if GBS_STARTED else 'preflight', error=repr(exc),
                       gbs_exit=LAST_GBS_RC, results=[])
        marker = f'ALL-END {stamp} FAILED'
        (B / 'status').write_text(json.dumps(failure, indent=2) + '\n' + marker + '\n')
        print(marker, 'GBS_EXIT', LAST_GBS_RC, repr(exc), flush=True)
        exit_code = 1
    raise SystemExit(exit_code)
