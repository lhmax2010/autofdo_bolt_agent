"""Strict data and durable output primitives."""
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile

class StopRequested(BaseException):
    """A control-flow stop, never an OSError/EINTR that I/O may retry."""
    def __init__(self, signum):
        super().__init__('signal '+str(signum))
        self.code=128+signum
        self.reason='interrupted'

class GateError(ValueError):
    def __init__(self, message, reason='gate', code=2):
        super().__init__(message)
        self.reason, self.code = reason, code

class TechnicalFailure(GateError):
    def __init__(self, message, reason='environment'):
        super().__init__(message, reason)


def require(condition, message, reason='gate', code=2):
    if not condition:
        raise GateError(message, reason, code)

def sha256(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def finite_tree(value):
    if isinstance(value, float):
        require(math.isfinite(value), 'non-finite number')
    elif isinstance(value, dict):
        for v in value.values():
            finite_tree(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            finite_tree(v)

def json_load(path):
    def bad(s):
        raise GateError('invalid JSON number: '+s)
    return json.loads(Path(path).read_text(), parse_constant=bad)

def canonical(value):
    finite_tree(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2)+'\n'

def atomic_write(path, content, *, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.'+path.name+'.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb' if isinstance(content, bytes) else 'w') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        if exclusive:
            os.link(name, path)  # Atomically publish a new file without replacing an existing one.
        else:
            os.replace(name, path)
        d = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(d)
        finally:
            os.close(d)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def save(path, value):
    atomic_write(path, canonical(value))

def positive(value, label, integer=False, zero=False):
    require(type(value) in ((int,) if integer else (int, float)), label+' has wrong type')
    require(math.isfinite(value) and (value >= 0 if zero else value > 0), label+' out of range')
    return value
