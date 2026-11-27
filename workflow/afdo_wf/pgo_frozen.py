"""Use the sealed baseline and one explicitly approved PGOGEN runtime."""
from pathlib import Path
import re

from .common import json_load, require, sha256

MACRO = 'pgo_runtime_evr'


def verify(split, workdir, arch):
    workdir = Path(workdir).resolve()

    def checked(path):
        value = Path(path).resolve()
        require(value.is_relative_to(workdir) and value.is_file(), 'frozen PGO input outside workdir or absent')
        return value

    runtime = split['runtime']
    version = runtime['evr']
    require(re.fullmatch(r'22\.1\.8-[0-9]+(?:\.[0-9]+)*',version), 'unsupported replacement compiler-rt release')
    name = 'compiler-rt-' + version + '.' + arch
    require(re.fullmatch(re.escape(name)+r' [0-9a-f]{64}',runtime['installed_record']),
            'replacement compiler-rt RPM header identity missing')
    require(runtime['tier']==2 and runtime['applies_to']==['PGOGEN'], 'unexpected replacement runtime scope')
    proof=checked(runtime['verification_path'])
    require(sha256(proof)==runtime['verification_sha256'], 'runtime verification evidence changed', 'identity',3)

    sets = {}
    inputs = [proof]
    for key in ('common','pgogen'):
        lock = split[key]
        repo = Path(lock['repo']).resolve()
        manifest_path = checked(repo/'manifest.json')
        conf = checked(lock['buildconf'])
        meta = checked(repo/'repodata/repomd.xml')
        manifest = json_load(manifest_path)
        require(sha256(manifest_path)==lock['repo_id'] and sha256(conf)==manifest['buildconf_sha256']
                and sha256(meta)==lock['repomd_sha256'],
                'frozen PGO repository identity changed: '+key,'identity',3)
        if key=='pgogen':
            require(manifest.get('pgo_runtime_deviation') == runtime,'runtime deviation missing from frozen manifest')
        items = {}
        for package in manifest['packages']:
            digest=package['sha256']
            require(re.fullmatch(r'[0-9a-f]{64}',digest) and package['file']==digest+'.rpm',
                    'invalid pinned RPM filename')
            rpm=checked(repo/package['file'])
            require(sha256(rpm)==digest and package['name'] not in items,
                    'frozen RPM mismatch: '+package['name'],'identity',3)
            items[package['name']]=digest
        sets[key]=items
        inputs.extend([manifest_path,conf,meta])
    extra = name + '.rpm'
    require(len(sets['common'])==109 and extra not in sets['common']
            and sets['pgogen']=={**sets['common'], extra:runtime['sha256']},
            'only the declared compiler-rt RPM may differ in PGOGEN','identity',3)
    common=split['common']['frozen_packages']
    pgogen=split['pgogen']['frozen_packages']
    require(len(common)==len(set(common))==109 and len(pgogen)==110
            and sorted(pgogen)==sorted([*common,runtime['installed_record']]),
            'invalid installed package lock for PGOGEN','identity',3)
    return inputs


def pgogen_lock(base, candidate, split):
    common=split['common']
    generation=split['pgogen']
    require(base['frozen_repo_id']==common['repo_id'] and candidate['frozen_repo_id']==generation['repo_id'],
            'PGOGEN repository lock mismatch')
    record=split['runtime']['installed_record']
    require(sorted(base['packages'])==sorted(common['frozen_packages'])
            and record not in base['packages']
            and sorted(candidate['packages'])==sorted([*base['packages'],record]),
            'PGOGEN installed package difference exceeds the approved runtime')
    macros=dict(candidate['macros'])
    require(macros.pop(MACRO,None)==split['runtime']['evr'], 'PGOGEN runtime macro mismatch')
    return dict(candidate,packages=base['packages'],frozen_repo_id=base['frozen_repo_id'],macros=macros)



def linked_atexit_lock(base, candidate, commands):
    """Attribute the exact atexit producer record without hiding package commands."""
    proof = {tuple(row) for row in commands if row[:1]==['GNU']}
    require(proof, 'linked atexit producer record absent')
    retained = {}
    excluded = {}
    for target, rows in candidate['commands'].items():
        original = {tuple(row) for row in base['commands'][target]}
        extra = proof - original
        retained[target] = [row for row in rows if tuple(row) not in extra]
        excluded[target] = [row for row in rows if tuple(row) in extra]
    return dict(candidate,commands=retained), excluded
