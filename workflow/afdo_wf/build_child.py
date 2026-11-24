"""Capture final in-scope memory peak before the transient cgroup disappears."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

def main(args):
    destination=Path(args[0]);start=time.monotonic()
    rc=subprocess.run(args[1:]).returncode
    group=Path('/proc/self/cgroup').read_text().split('::',1)[1].strip()
    cg=Path('/sys/fs/cgroup'+group)
    data=dict(exit_code=rc,seconds=time.monotonic()-start,
              memory_peak=int((cg/'memory.peak').read_text()),memory_events=(cg/'memory.events').read_text())
    with destination.open('w') as f:
        json.dump(data,f);f.write('\n');f.flush();os.fsync(f.fileno())
    return rc

if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
