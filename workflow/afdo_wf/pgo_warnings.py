"""Bind instrumented profile names and build diagnostics to FFmpeg objects."""
from collections import Counter
from pathlib import Path, PurePosixPath
import re
import shlex
import struct
import zlib

from .common import require, sha256

OUTDATED = 'profile-instr-out-of-date'
UNPROFILED = 'profile-instr-unprofiled'
POLICY = {OUTDATED: {'target_limit': 0}, UNPROFILED: {'protected_top': 20},
          'other_profile_warnings': 'record'}
OBJECT = re.compile(r'(?:CC|CXX|OBJCC|HOSTCC|AS)\s+([^\s]+\.o)$')
MAKE_ACTION = re.compile(r'(?:HOSTLD|LD|AR|STRIP|GEN|INSTALL|COPY|CP|X86ASM)\s+.+')
GBS_PREFIX = re.compile(r'^\[\s*\d+s\]\s?')
MAKEFLAGS_EXPORT = re.compile(r'''^\[\s*\d+s\] \+ export (['"]?MAKEFLAGS=[^\n]*)$''', re.M)
WARNING = re.compile(r'\bwarning:\s*(.*?)(?:\s+\[-W([^]]+)\])?\s*$')
BACKEND_PREFIX = re.compile(r'^(.+?\.(?:c|cc|cpp|cxx|m|mm)):\s+(.*)$')


def validate(policy):
    require(type(policy) is dict and policy == POLICY
            and type(policy[OUTDATED]['target_limit']) is int
            and type(policy[UNPROFILED]['protected_top']) is int,
            'preregister the target and top-20 PGO warning policy before a live run')


def object_name(path):
    value = PurePosixPath(path)
    if not value.is_absolute() and '..' not in value.parts and value.suffix == '.o':
        return value.as_posix()
    return None


def sections(path, section):
    """Read a named section from an ELF32/ELF64 relocatable object."""
    with path.open('rb') as file:
        ident = file.read(16)
        if not ident.startswith(b'\x7fELF'):
            return None
        require(len(ident) == 16 and ident[4] in (1, 2) and ident[5] in (1, 2),
                'invalid profile object ELF header: '+str(path))
        endian = '<' if ident[5] == 1 else '>'
        wide = ident[4] == 2
        header = struct.unpack(endian+('HHIQQQIHHHHHH' if wide else 'HHIIIIIHHHHHH'),
                               file.read(48 if wide else 36))
        require(header[0] == 1, 'profile object is not ELF relocatable: '+str(path))
        shoff, shsize, count, names_index = header[5], *header[-3:]
        size = path.stat().st_size
        if not shoff:
            return None
        require(shsize == (64 if wide else 40) and 0 < names_index < count
                and shoff + count*shsize <= size, 'invalid ELF section table: '+str(path))
        file.seek(shoff)
        entries = list(struct.iter_unpack(endian+('IIQQQQIIQQ' if wide else 'IIIIIIIIII'),
                                         file.read(count*shsize)))
        def contents(entry):
            offset, length = entry[4:6]
            require(offset+length <= size, 'invalid ELF section range: '+str(path))
            file.seek(offset)
            return file.read(length)
        names = contents(entries[names_index])
        for entry in entries:
            offset = entry[0]
            end = names.find(b'\0',offset)
            require(end != -1, 'invalid ELF section name: '+str(path))
            if names[offset:end] == section:
                return contents(entry)
    return None


def profile_names(data):
    """Decode LLVM 22's ULEB128 lengths and optional zlib profile-name records."""
    def length(offset):
        value = 0
        for shift in range(0, 64, 7):
            require(offset < len(data), 'truncated profile-name length')
            byte = data[offset]
            offset += 1
            value |= (byte & 0x7f) << shift
            if byte < 128:
                return value, offset
        require(False, 'invalid profile-name length')

    result = set()
    offset = 0
    while offset < len(data):
        size, offset = length(offset)
        compressed, offset = length(offset)
        end = offset + (compressed or size)
        require(size > 0 and end <= len(data), 'invalid profile-name payload')
        raw = zlib.decompress(data[offset:end]) if compressed else data[offset:end]
        require(len(raw) == size, 'profile-name size mismatch')
        names = raw.decode().split('\x01')
        require(all(names), 'empty LLVM profile name')
        result.update(names)
        offset = end
        while offset < len(data) and data[offset] == 0:
            offset += 1
    return result


def top_rows(text):
    rows = re.findall(r'^  (.+), max count = (\d+)$', text, re.M)
    require(len(rows) == 20 and len({name for name, _ in rows}) == len(rows),
            'expected 20 uniquely named functions in llvm-profdata show --topn=20')
    require([int(count) for _, count in rows] == sorted((int(count) for _, count in rows), reverse=True),
            'llvm-profdata top-20 order is invalid')
    return [dict(function=name, max_count=int(count)) for name, count in rows]


def attribute_top(root, top):
    """Use the profile names emitted in PGOGEN objects, including local names."""
    root = Path(root).resolve()
    owners = {row['function']: [] for row in top}
    for path in sorted(root.rglob('*.o')):
        if path.is_symlink() or not path.is_file():
            continue
        raw = sections(path, b'__llvm_prf_names')
        if raw is None:
            continue
        for name in profile_names(raw) & owners.keys():
            owners[name].append(path)
    result = []
    for row in top:
        paths = owners[row['function']]
        require(len(paths) == 1, 'ambiguous or absent PGOGEN object for hot function '+row['function'])
        path, = paths
        result.append(dict(row, object=path.relative_to(root).as_posix(), pgogen_object_sha256=sha256(path)))
    return result


def compile_objects(log, source_root):
    """Record the %build targets from GNU make output grouped by target."""
    compiled = {}
    for lineno, original in enumerate(log.splitlines(), 1):
        line = GBS_PREFIX.sub('', original).strip()
        hit = OBJECT.fullmatch(line)
        if hit:
            active = object_name(hit[1])
            path = Path(source_root)/(active or '')
            if active and path.is_file():
                compiled[active] = lineno
    return compiled


def has_target_output_sync(log):
    for assignment in MAKEFLAGS_EXPORT.findall(log):
        try:
            value = shlex.split(assignment)[0].removeprefix('MAKEFLAGS=')
        except ValueError:
            continue
        if '--output-sync=target' in value.split():
            return True
    return False


def audit(log, policy, mapping, compiled, top):
    validate(policy)
    require(has_target_output_sync(log),
            'PGO build log lacks compiler output synchronization proof')
    warnings = []
    active = None
    for lineno, original in enumerate(log.splitlines(), 1):
        line = GBS_PREFIX.sub('', original).strip()
        hit = OBJECT.fullmatch(line)
        if hit:
            active = object_name(hit[1])
        elif line.startswith('Executing(') or line.startswith('+') or MAKE_ACTION.fullmatch(line):
            active = None
        match = WARNING.search(line)
        if not match:
            continue
        message, option = match.groups()
        backend = BACKEND_PREFIX.fullmatch(message) if option == 'backend-plugin' else None
        backend_detail = None
        if backend:
            if ('function control flow change detected (hash mismatch)' in backend[2]
                    or 'Inconsistent number of counts in ' in backend[2]):
                backend_detail = 'flow-mismatch'
            elif ('no profile data available for function' in backend[2]
                  or 'function not found in profile' in backend[2]):
                backend_detail = 'missing-function'
        if option and option.startswith('profile-instr-'):
            kind = option
        elif backend_detail or re.search(r'\b(?:profile data|instrumentation profile)\b',message,re.I):
            kind = option or 'other-profile-warning'
        else:
            continue
        obj = active if active in compiled else None
        target = next((owner for prefix, owner in mapping.items() if obj and obj.startswith(prefix)),None)
        warnings.append(dict(kind=kind, option=option, line=lineno, object=obj, target=target,
                             backend_detail=backend_detail, raw=original))
    hot_objects = {row['object'] for row in top}
    outdated = [event for event in warnings if event['kind'] == OUTDATED
                and (event['target'] is not None or event['object'] is None)]
    unprofiled = [event for event in warnings if event['kind'] == UNPROFILED
                  and (event['object'] in hot_objects or event['object'] is None)]
    missing_hot = sorted(hot_objects - compiled.keys())
    return dict(passed=not outdated and not unprofiled and not missing_hot,
                counts=dict(Counter(row['kind'] for row in warnings)),
                records=warnings, outdated_gate=outdated, unprofiled_gate=unprofiled,
                missing_hot_compile_objects=missing_hot, top20=top)
