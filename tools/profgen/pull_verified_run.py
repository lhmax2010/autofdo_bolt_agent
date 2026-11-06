#!/usr/bin/env python3
"""Pull one completed RUN, validate every byte, then remove only that exact RUN.

All failures propagate before deletion. The caller must stop the workload first.
SDB directory pulls place contents directly in the empty destination directory.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shlex
import subprocess


def parse_manifest(text, remote):
    result = {}
    for line in text.splitlines():
        m = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
        if not m or not m[2].startswith(remote + '/'):
            raise ValueError('Malformed/outside manifest entry: ' + line)
        rel = m[2][len(remote) + 1:]
        p = PurePosixPath(rel)
        if '..' in p.parts or p.is_absolute() or rel in result:
            raise ValueError('Duplicate/unsafe manifest path: ' + rel)
        result[rel] = m[1]
    if not result:
        raise ValueError('Empty manifest refused')
    return result


def pull_verify_delete(remote, local, manifest, pull, reread_manifest, delete):
    """Injectable transport; delete is called only after both full comparisons."""
    if not re.fullmatch(r'/opt/afdo_agent/work/eval-[A-Za-z0-9_-]+', remote):
        raise ValueError('RUN must be an exact /opt/afdo_agent/work/eval-* path')
    local = Path(local)
    if local.exists():
        raise ValueError('Destination must not exist; never merge separate pulls')
    expected = parse_manifest(manifest, remote)
    local.mkdir(parents=True)
    pull(remote, local)
    actual = {}
    for p in local.rglob('*'):
        if p.is_symlink():
            raise ValueError('Pulled symlink refused: ' + str(p))
        if p.is_file():
            with p.open('rb') as stream:
                actual[p.relative_to(local).as_posix()] = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != expected:
        raise ValueError('SHA/file-set mismatch; deletion forbidden: ' + repr(sorted(k for k in actual.keys() | expected.keys() if actual.get(k) != expected.get(k))))
    if parse_manifest(reread_manifest(), remote) != expected:
        raise ValueError('Remote manifest changed after pull; deletion forbidden')
    delete(remote)
    return {'remote': remote, 'host': str(local), 'files': actual,
            'all_verified_before_delete': True, 'deleted': True}


class SDB:
    def __init__(self, device, audit_path=None):
        self.device = device
        work = Path(__file__).resolve().parents[2]
        self.audit_path = Path(audit_path) if audit_path else work / 'temp/sdb-transport.jsonl'
        self.audit_path.resolve().relative_to(work)
        self.retry_count = 0

    def audit(self, record):
        record['time'] = datetime.datetime.now().astimezone().isoformat()
        with self.audit_path.open('a') as stream:
            stream.write(json.dumps(record) + '\n')

    def call(self, args):
        command = ['sdb', '-s', self.device] + args
        p = subprocess.run(command, text=True, capture_output=True)
        self.audit(dict(kind='command', command=command, transport_rc=p.returncode,
                        stdout=p.stdout, stderr=p.stderr))
        if p.returncode:
            raise RuntimeError('SDB transport failed; no retry: ' + repr(command))
        return p.stdout

    def shell(self, command, *, read_only=False):
        previous = []
        for attempt in range(3 if read_only else 1):
            out = self.call(['shell', '( ' + command + ' ); r=$?; printf "\\n__RC=%s\\n" "$r"'])
            m = re.search(r'\n__RC=(\d+)\s*$', out)
            self.audit(dict(kind='shell_result', command=command, read_only=read_only,
                            attempt=attempt, remote_rc=int(m[1]) if m else None))
            if m:
                if int(m[1]):
                    raise RuntimeError('Remote command failed; no retry: ' + out)
                result = out[:m.start()].strip()
                if any(value != result for value in previous):
                    raise RuntimeError('Read-only retry output changed; stop: ' + command)
                return result
            previous.append(out.strip())
            if read_only and attempt < 2:
                self.retry_count += 1
                self.audit(dict(kind='retry', command=command, retry=attempt + 1,
                                reason='missing remote exit marker, read-only'))
        raise RuntimeError('Missing remote exit marker; stop: ' + command)

    def manifest(self, remote):
        q = shlex.quote(remote)
        canonical = self.shell('readlink -f ' + q, read_only=True)
        if canonical != remote:
            raise ValueError('Remote RUN alias refused')
        links = self.shell('find ' + q + ' -type l -print', read_only=True)
        if links:
            raise ValueError('Remote symlink refused: ' + links)
        # Batched -exec propagates a failed SHA child to find's exit status;
        # the semicolon form can return success despite unreadable files.
        script = 'for f; do sha256sum -- "$f" || exit; done'
        return self.shell('find ' + q + ' -type f -exec /bin/bash -c ' +
                          shlex.quote(script) + ' _ {} +', read_only=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--device', required=True)
    p.add_argument('--remote', required=True)
    p.add_argument('--local', required=True, type=Path)
    p.add_argument('--receipt', required=True, type=Path)
    a = p.parse_args()
    # Host outputs must stay within this project; resolve existing parent aliases.
    work = Path(__file__).resolve().parents[2]
    for v in [a.local, a.receipt]:
        v.resolve().relative_to(work)
    sdb = SDB(a.device)
    if not re.fullmatch(r'/opt/afdo_agent/work/eval-[A-Za-z0-9_-]+', a.remote):
        raise ValueError('Unsafe RUN path')
    manifest = sdb.manifest(a.remote)
    a.receipt.with_suffix('.manifest.txt').write_text(manifest + '\n')
    result = pull_verify_delete(
        a.remote, a.local, manifest,
        lambda remote, local: sdb.call(['pull', remote, str(local) + '/']),
        lambda: sdb.manifest(a.remote),
        lambda remote: sdb.shell('rm -rf -- ' + shlex.quote(remote) + ' && test ! -e ' + shlex.quote(remote)))
    a.receipt.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
