"""Instrumented PGO identity, merge, and consumption gates."""
from pathlib import Path
import re

from . import buildlock, pgo_frozen
from .common import require, save, sha256

VARIANTS = ('BASE', 'AFDO', 'PGOGEN', 'PGO')
CONTROLS = ('BASE', 'AFDO')
PROFILE_NAME = 'pgo.profdata'
RAW_MAGIC = frozenset({0xff6c70726f667281, 0xff6c70726f665281})
INDEX_MAGIC = 0x8169666f72706cff
RAW_NAME = re.compile(r'[0-9]+_[0-9]+-([1-9][0-9]*)\.profraw')
BUILD_ID = re.compile(r'[a-f0-9]{40}')
SHA = re.compile(r'[a-f0-9]{64}')
PGO_MACROS = {'PGOGEN': {'with_pgogen': '1'}, 'PGO': {'with_pgo': '1'}}
COMMON_MACROS = {'with_pgo_deps': '1'}


def method(job, package=None):
    value = job.get('method', 'autofdo')
    require(value in ('autofdo', 'pgo'), 'unsupported workflow method')
    if value == 'pgo' and package is not None:
        require(package.get('pgo'), 'package does not declare PGO settings')
        require(package['collect']['runs'] == 3, 'instrumented PGO requires three training runs')
        require(package['command_capture']['method'] == 'recorded-switches', 'instrumented PGO requires recorded-switches')
    return value


def archive_lock(lock):
    require(isinstance(lock, dict) and set(lock) == {'path', 'sha256'}
            and isinstance(lock['path'], str) and Path(lock['path']).is_absolute()
            and isinstance(lock['sha256'], str) and SHA.fullmatch(lock['sha256']),
            'AFDO profile needs an absolute path and SHA-256')
    path = Path(lock['path'])
    require(path.is_file() and sha256(path) == lock['sha256'], 'locked AFDO profile SHA mismatch', 'identity', 3)
    return path


def macros(variant, unit, diag_macros, split=None):
    require(variant in (*VARIANTS, 'BASE-r'), 'unknown build variant')
    require(not {'with_pgogen','with_pgo','with_pgo_deps',pgo_frozen.MACRO} & unit['macros'].keys(),
            'instrumented PGO macros are reserved for variant selection')
    result = dict(unit['macros'])
    if split is None:
        result.update(COMMON_MACROS)
    elif variant == 'PGOGEN':
        result[pgo_frozen.MACRO] = split['runtime']['evr']
    if variant == 'AFDO':
        result.update(unit['consume_macro'])
        result.update(diag_macros)
    result.update(PGO_MACROS.get(variant, {}))
    return result


def runtime_symbols(symbols):
    return any(
        len(parts) >= 8 and parts[0].rstrip(':').isdigit()
        and parts[6].isdigit() and parts[7] == '__llvm_profile_runtime'
        for line in symbols.splitlines() if (parts := line.split())
    )


def check_runtime(symbols_by_target, targets):
    require(set(symbols_by_target) == set(targets) and targets, 'missing PGOGEN target ELF evidence')
    result = {target: runtime_symbols(symbols) for target, symbols in symbols_by_target.items()}
    require(all(result.values()), 'PGOGEN profile runtime missing: ' + ', '.join(k for k,v in result.items() if not v))
    return result


def runtime_command_provenance(lock, archive_commands):
    # Shared DSOs carry recorded-switches strings from statically linked objects.
    # Strip only exact records proven to come from the selected support archive.
    known = {tuple(row) for row in archive_commands}
    require(known, 'compiler-rt command provenance missing')
    keep = {}
    excluded = {}
    for target, rows in lock['commands'].items():
        keep[target] = [row for row in rows if tuple(row) not in known]
        excluded[target] = [row for row in rows if tuple(row) in known]
        require(keep[target], 'no package compile command remains: '+target)
    return {**lock, 'commands':keep}, excluded


def profile_use_path(settings):
    used = {option.split('=', 1)[1] for option in settings['CFLAGS'] if option.startswith('-fprofile-use=')}
    require(len(used) == 1, 'missing or ambiguous PGO compiler option')
    path, = used
    value = Path(path)
    require(value.is_absolute() and '..' not in value.parts and value.name == PROFILE_NAME,
            'unsafe indexed profile staged path')
    return value


def compare(control, candidate, variant):
    """Normalize only the options declared for this instrumented build."""
    require(variant in PGO_MACROS, 'unknown instrumented variant')
    settings = candidate['settings']
    if variant == 'PGOGEN':
        option = '-fprofile-generate'
        require(option in settings['CFLAGS'] and option in settings['LDFLAGS'],
                'PGOGEN requires instrumentation at compile and link time')
    else:
        option = '-fprofile-use=' + str(profile_use_path(settings))
    for target, rows in candidate['commands'].items():
        require(any(option in row for row in rows), 'missing PGO compiler option: ' + target)
    return buildlock.compare(control, candidate, exact=(option,), value_options=(),
                             candidate_macros=tuple(PGO_MACROS[variant]))


def read_inventory(directory, pid, exit_code):
    """Read the explicit board inventory for the completed training decoder."""
    require(type(exit_code) is int and exit_code == 0, 'PGOGEN training process did not exit normally')
    require(re.fullmatch(r'[1-9][0-9]*', str(pid)), 'missing decoder PID')
    directory = Path(directory)
    rows = []
    seen = set()
    for line in (directory/'raw.sha256').read_text().splitlines():
        fields = line.split()
        require(len(fields) == 2 and SHA.fullmatch(fields[0]), 'malformed profraw inventory')
        digest, name = fields
        match = RAW_NAME.fullmatch(name)
        require(match is not None and match[1] == str(pid) and name not in seen,
                'profile filename is not an exact member for the completed decoder PID')
        path = directory/'raw'/name
        require(not path.is_symlink() and path.is_file() and sha256(path) == digest, 'profraw inventory SHA mismatch')
        rows.append(dict(path=str(path.resolve()), sha256=digest, bytes=path.stat().st_size))
        seen.add(name)
    require(rows, 'training profraw inventory is empty')
    require(seen == {p.name for p in (directory/'raw').iterdir()}, 'unlisted profraw training output')
    return rows


def show_profile(path, kind, execute):
    with Path(path).open('rb') as f:
        magic = f.read(8)
    values = {int.from_bytes(magic, byteorder) for byteorder in ('little', 'big')}
    expected = RAW_MAGIC if kind == 'raw' else {INDEX_MAGIC}
    require(len(magic) == 8 and values & expected, 'incorrect ' + kind + ' profile magic')
    text = execute(['show', '--profile-version', '--binary-ids', '--all-functions', '--counts', str(path)])
    version = re.search(r'^Profile version: ([1-9][0-9]*)$', text, re.M)
    count = re.search(r'^Functions shown: ([1-9][0-9]*)$', text, re.M)
    require(version and count and re.search(r'^Instrumentation level: IR(?: |$)', text, re.M),
            'llvm-profdata did not show the expected IR instrumentation profile')
    binary_ids = re.search(r'^Binary IDs:[ \t]*\n((?:[0-9a-f]+\n)+)', text+'\n', re.M)
    require(binary_ids is not None, 'instrumentation profile build ID absent', 'identity', 3)
    lines = re.findall(
        r'^  (.+):\n    Hash: (0x[0-9a-f]+)\n    Counters: ([0-9]+)\n    Block counts: \[([0-9, ]*)\]$',
        text, re.M)
    records = {(name, signature): any(int(x) for x in counters.split(',')) for name, signature, _, counters in lines if counters}
    require(len(records) == int(count[1]), 'incomplete instrumentation function records')
    require(all(len(counters.split(',')) == int(n) for _, _, n, counters in lines),
            'instrumentation counter list length mismatch')
    return dict(version=int(version[1]), ids=binary_ids[1].splitlines(), records=records)


def merge_profiles(runs, identities, targets, output, execute):
    """Merge the exact SHA-bound decoder inventory; version checks use llvm-profdata."""
    require(len(runs) == 3 and len({r['id'] for r in runs}) == len(runs), 'expected three independent PGOGEN runs')
    require(targets and all(BUILD_ID.fullmatch(key) for key in identities)
            and set(targets) <= set(identities.values()), 'incomplete PGOGEN build ID inventory')
    members = []
    versions = set()
    functions = {}
    used = set()
    merged_ids = set()
    for run in runs:
        directory = Path(run['local'])
        inventory = read_inventory(directory, run['pid'], run['exit_code'])
        require(inventory == run['profiles'], 'collected raw inventory changed')
        found = set()
        for row in inventory:
            path = row['path']
            require(path not in used, 'duplicate PGOGEN raw merge input')
            used.add(path)
            profile = show_profile(path, 'raw', execute)
            require(len(profile['ids']) == 1 and profile['ids'][0] in identities,
                    'raw profile does not identify one known PGOGEN binary', 'identity', 3)
            build_id, = profile['ids']
            require(build_id not in found, 'duplicate PGOGEN binary in a training run')
            found.add(build_id)
            merged_ids.add(build_id)
            target = identities[build_id]
            keys = set(profile['records'])
            require(target not in functions or functions[target] == keys,
                    'PGOGEN function set differs between training runs')
            functions[target] = keys
            versions.add(profile['version'])
            members.append(dict(row, run=run['id'], pid=run['pid'], build_id=build_id, binary=target,
                                raw_version=profile['version']))
        require(set(targets) <= {identities[key] for key in found}, 'PGOGEN run is missing profraw for a target DSO')
    require(len(versions) == 1, 'inconsistent raw profile versions')
    output = Path(output)
    require(not output.exists(), 'indexed profile output already exists')
    save(output.parent/'profraw-merge-manifest.json', members)
    def verify_members():
        require(all(sha256(row['path']) == row['sha256'] for row in members), 'profraw input changed during conversion')
    verify_members()
    execute(['merge', '-o', str(output), *[row['path'] for row in members]])
    verify_members()
    indexed = show_profile(output, 'indexed', execute)
    require(set(indexed['ids']) == merged_ids, 'indexed profile binary IDs differ from raw inputs', 'identity', 3)
    coverage = {}
    for target in targets:
        keys = functions[target]
        require(keys and keys <= indexed['records'].keys(), 'indexed profile omitted target functions')
        require(not any(keys & other for name, other in functions.items() if name != target),
                'target DSO function attribution is ambiguous')
        covered = sum(indexed['records'][key] for key in keys)
        coverage[target] = dict(instrumented_functions=len(keys), covered_functions=covered, ratio=covered/len(keys))
    lock = dict(path=str(output), sha256=sha256(output), raw_version=next(iter(versions)),
                indexed_version=indexed['version'], coverage=coverage, inputs=members)
    save(output.parent/'pgo-profile-lock.json', lock)
    return dict(profile=str(output), lock=lock, quality=dict(publishable=True, identity='verified',
                                                            compatible=True, target_coverage=coverage))


def consumption(lock, staged, base_text, candidate_text, warnings):
    require(Path(staged).is_file() and sha256(staged) == lock['sha256'],
            'staged indexed profile SHA mismatch', 'identity', 3)
    require(base_text and set(base_text) == set(candidate_text) == set(lock['coverage']),
            'incomplete PGO target evidence')
    changed = {target: digest != candidate_text[target] for target, digest in base_text.items()}
    return dict(passed=all(changed.values()) and warnings['passed'],
                warning_counts=warnings['counts'], warning_audit=warnings,
                changed_text=changed, coverage=lock['coverage'], staged_sha256=lock['sha256'])


def comparison_metadata():
    return [
        dict(id='pgo-vs-base', control='BASE', candidate='PGO', primary=True),
        dict(id='pgo-vs-afdo', control='AFDO', candidate='PGO', primary=False),
    ]


def stage_metadata(name, default):
    descriptions = {
        'preflight': ('Check the pinned AFDO profile, PGO warning policy and available mechanism events.',
                      ['AFDO profile path and SHA-256', 'preregistered PGO warning policy'],
                      ['locked AFDO SHA and PGO warning policy', 'perf event availability'],
                      ['mechanism event manifest']),
        'build': ('Freeze the four-variant dependency union and build BASE and PGOGEN.',
                  ['PGO spec patch and compiler-rt from the pinned snapshot'],
                  ['PGOGEN compile and link options', 'profile runtime in every target DSO'],
                  ['PGOGEN ELF manifest and build-lock audit']),
        'deploy': ('Verify PLATFORM, BASE and PGOGEN before instrumented training.',
                   ['PGOGEN build-ID inventory'], ['PGOGEN loaded-library identity and correctness'],
                   ['PGOGEN deployment and isolated setup artifacts']),
        'collect': ('Collect three manifest-bound PGOGEN training runs.',
                    ['declared training clip', 'PGOGEN build IDs and decoder process evidence'],
                    ['normal exit, decoder PID and raw inventory SHA'],
                    ['explicit profraw inventories and decoder identities']),
        'convert': ('Merge the checked instrumented profiles with llvm-profdata.',
                    ['profile inventories and PGOGEN build IDs'],
                    ['raw/indexed version, binary IDs and target function coverage'],
                    ['locked indexed profile and merge manifest']),
        'rebuild': ('Build AFDO from the locked historical profile and audit PGO.',
                    ['AFDO SHA lock, indexed PGO SHA lock and warning policy'],
                    ['variant build-lock differences, PGO warnings, profile SHA and changed target text'],
                    ['AFDO and PGO runtimes and per-target consumption']),
        'measure': ('Measure PGO against BASE and AFDO, then count mechanisms separately.',
                    ['audited BASE, PGO and AFDO', 'preflight mechanism event manifest'],
                    ['separate locked plans per comparison and input'],
                    ['paired estimates and diagnostic mechanism counts']),
        'report': ('Report both paired comparisons and their diagnostic counts.',
                   ['both paired comparisons and the mechanism event evidence'],
                   ['measurements and advisory counts kept separate'],
                   ['paired verdicts, coverage, warnings and mechanism counts']),
    }
    if name not in descriptions:
        return default
    purpose, inputs, gates, outputs = descriptions[name]
    board_operations = {
        'collect': ['prepare the plug-in registry separately', 'run and observe PGOGEN training',
                    'pull and verify the raw profile inventory'],
        'deploy': ['deploy BASE and PGOGEN', 'check all variants against the platform oracle'],
        'rebuild': ['deploy AFDO and PGO', 'verify untimed correctness'],
    }
    return {**default, 'purpose': purpose,
            'inputs': inputs if name in ('collect','convert') else [*default['inputs'], *inputs],
            'gates': gates if name in ('collect','convert') else [*default['gates'], *gates],
            'outputs': outputs if name in ('collect','convert') else [*default['outputs'], *outputs],
            'board_operations': board_operations.get(name, default['board_operations'])}


def count_value(text):
    rows = [line.split(';') for line in text.splitlines() if len(line.split(';')) >= 3]
    if len(rows) != 1 or not re.fullmatch(r'[0-9]+', rows[0][0].strip()):
        return None
    row, = rows
    return dict(count=int(row[0]), event=row[2].strip(), running=row[3].strip() if len(row)>3 else None,
                running_percent=row[4].strip() if len(row)>4 else None)


def event_candidates(pmu_files):
    aliases = {
        'cycles': ('cpu_cycles', 'cycles'),
        'instructions': ('inst_retired', 'instructions'),
        'l1i-refill': ('l1i_cache_refill', 'L1-icache-load-misses'),
        'l1i-tlb-refill': ('l1i_tlb_refill', 'iTLB-load-misses'),
        'branch-misprediction': ('br_mis_pred', 'branch-misses'),
        'frontend-stall': ('stall_frontend', 'stalled-cycles-frontend'),
        'frontend-stall-slots': ('stall_slot_frontend', None),
    }
    pmu = re.compile(r'^/sys/bus/event_source/devices/(arm[^/]+)/events/([a-z0-9_]+)$')
    events = [match.groups() for line in pmu_files.splitlines() if (match := pmu.fullmatch(line))]
    return {label: list(dict.fromkeys([f'{name}/{event}/' for name,event in events if event==alias]
                 + ([generic] if generic else []))) for label,(alias,generic) in aliases.items()}
