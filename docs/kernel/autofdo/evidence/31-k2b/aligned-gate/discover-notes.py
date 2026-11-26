from pathlib import Path
import hashlib
import json
import sys

root = Path(sys.argv[1])
markers = ('kernel/sched','kernel/locking','fs','mm','lib','kernel')
members = {line.removeprefix('./') for line in (root/'vmlinux-a-members.txt').read_text().splitlines()}
notes = root/'gcno'
linked, remaining = [], []
for file in sorted(notes.rglob('*.gcno')):
    relative = file.relative_to(notes)
    assert str(relative.parent) in markers, relative
    with file.open('rb') as handle:
        assert handle.read(8) == b'oncg*11B', relative
        handle.seek(0)
        row = dict(file=str(relative), sha256=hashlib.file_digest(handle,'sha256').hexdigest(),
                   bytes=file.stat().st_size)
    (linked if str(relative.with_suffix('.o')) in members else remaining).append(row)
assert all(any(Path(row['file']).parent == Path(directory) for row in linked) for directory in markers)
assert {'fs/pipe.gcno','mm/highmem.gcno'} <= {row['file'] for row in linked}
(root/'gcno-map.json').write_text(json.dumps({'linked':linked,'other':remaining},indent=2)+'\n')
(root/'expected-gcda.txt').write_text(''.join(str(Path(row['file']).with_suffix('.gcda'))+'\n' for row in linked))
