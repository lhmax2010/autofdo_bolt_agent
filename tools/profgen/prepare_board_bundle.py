#!/usr/bin/env python3
"""Prepare a local deployment payload from verified evaluation RPMs; no SDB.

Manifest IDs/SHA come from verify_artifacts' paired-runtime/debuginfo checks.
This does not install RPMs or touch a board. Run separately per architecture.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

W = Path('/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent')


def workspace(path):
    p = path.resolve()
    if not p.is_relative_to(W):
        raise ValueError('Path outside workspace: ' + str(p))
    return p


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('summary', type=Path)
    p.add_argument('destination', type=Path, help='New directory under WORKDIR/temp')
    p.add_argument('--arch', choices=['armv7l', 'aarch64'], required=True)
    a = p.parse_args()
    rows = [r for r in json.loads(workspace(a.summary).read_text()) if r['arch'] == a.arch]
    dest = workspace(a.destination)
    if not dest.is_relative_to(W / 'temp') or dest.exists() or not rows:
        p.error('Expected nonempty verified rows and a new temp destination')
    dest.mkdir(parents=True)
    manifest = []
    for row in rows:
        name = row['id']
        runtime = workspace(Path(row['runtime']['path']))
        sha = hashlib.sha256(runtime.read_bytes()).hexdigest()
        bid = row['runtime']['build_id']
        if sha != row['runtime']['sha256'] or bid != row['debug']['build_id']:
            raise ValueError('Verified input changed: ' + name)
        variant = dest / 'variants' / name
        libdir = variant / 'lib'; libdir.mkdir(parents=True)
        bindir = variant / 'bin'; bindir.mkdir()
        if name.startswith('spike-'):
            target = bindir / 'eval-spike'
            shutil.copy2(runtime, target)
            obj = 'spike'
        else:
            # Extract only associated runtime library RPMs. Keep raw extraction in temp.
            rpm_dir = workspace(Path(row['rpms'][0]).parent)
            unpack = dest / 'unpacked' / name; unpack.mkdir(parents=True)
            rpms = [x for x in rpm_dir.glob('lib*.rpm') if '-devel-' not in x.name
                    and '-debuginfo-' not in x.name and '-debugsource-' not in x.name]
            if not rpms:
                raise ValueError('No runtime RPMs: ' + name)
            for rpm in rpms:
                process = subprocess.Popen(['rpm2cpio', str(rpm)], stdout=subprocess.PIPE)
                result = subprocess.run(['cpio', '-idm', '--no-absolute-filenames'],
                                        stdin=process.stdout, cwd=unpack, capture_output=True)
                process.stdout.close()
                rc = process.wait()
                if rc or result.returncode:
                    raise RuntimeError('RPM unpack failed: ' + str(rpm))
            for source in (unpack / 'usr').glob('lib*/*.so*'):
                if source.is_symlink():
                    link = source.readlink()
                    if link.is_absolute() or '..' in link.parts:
                        raise ValueError('Unexpected library symlink: ' + str(source))
                    (libdir / source.name).symlink_to(link)
                elif source.is_file():
                    shutil.copy2(source, libdir / source.name)
            target = libdir / runtime.name
            if hashlib.sha256(target.read_bytes()).hexdigest() != sha:
                raise ValueError('Payload target differs: ' + name)
            obj = 'ffmpeg'
        board = Path('/opt/afdo_agent')
        board_target = board / target.relative_to(dest)
        manifest.append('\t'.join([name, a.arch, obj, row['variant'],
                                   str(board_target) if obj == 'spike' else '/usr/bin/gst-launch-1.0',
                                   str(board / libdir.relative_to(dest)), str(board_target), sha, bid]))
    (dest / 'eval-manifest.tsv').write_text('\n'.join(manifest) + '\n')
    shutil.copytree(W / 'tools/profgen/board', dest / 'scripts')
    print(json.dumps({'payload': str(dest), 'variants': len(rows), 'arch': a.arch,
                      'deploy_only': ['variants/', 'scripts/', 'eval-manifest.tsv'],
                      'do_not_deploy': ['unpacked/'], 'board_contacted': False}, indent=2))


if __name__ == '__main__':
    main()
