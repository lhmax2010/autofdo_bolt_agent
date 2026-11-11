"""Serial resource-gated runner. No formal sample profile inputs permitted."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

WORK = Path(__file__).resolve().parents[2]
ROOT = WORK / "temp/GBS-ROOT-LLVM-X86/local/BUILD-ROOTS/scratch.x86_64.0"


def platform(tool):
    return [str(ROOT / "lib64/ld-linux-x86-64.so.2"),
            "--library-path", f"{ROOT}/lib64:{ROOT}/usr/lib64",
            str(ROOT / "usr/bin" / tool)]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1048576), b""):
            h.update(b)
    return h.hexdigest()


def available():
    raw = Path("/proc/meminfo").read_text()
    return raw, int(next(s.split()[1] for s in raw.splitlines()
                        if s.startswith("MemAvailable:"))) * 1024


def run(label, command, tier="light"):
    out = WORK / "docs/profgen/eval/prep/evidence" / label
    out.mkdir(exist_ok=False)
    raw, memory = available()
    (out / "meminfo-0000.txt").write_text(raw)
    (out / "loadavg.txt").write_text(Path("/proc/loadavg").read_text())
    threshold, limit = (10, "8G") if tier == "coverage" else (4, "3G")
    metadata = {"command": command, "tier": tier, "limit": limit, "cpu_quota": "200%",
                "started": datetime.datetime.now().astimezone().isoformat(),
                "admission_memavailable": memory}
    (out / "command.json").write_text(json.dumps(metadata, indent=2) + "\n")
    if memory < threshold * 1024**3:
        metadata["status"] = "not_started_resource_gate"
        (out / "result.json").write_text(json.dumps(metadata, indent=2) + "\n")
        print(json.dumps(metadata))
        return 75
    # --worker is itself inside the capped scope, including any subprocess.
    worker = [sys.executable, str(Path(__file__).resolve()), "--worker", str(out), *command]
    start = time.monotonic()
    with (out / "scope.log").open("w") as log:
        result = subprocess.run(["nice", "-n", "19", "ionice", "-c3",
                                 "systemd-run", "--user", "--scope", "-q",
                                 "-p", "MemoryMax=" + limit, "-p", "CPUQuota=200%",
                                 *worker], stdout=log, stderr=subprocess.STDOUT)
    metadata.update(exit_code=result.returncode, elapsed_seconds=time.monotonic()-start,
                    status="success" if result.returncode == 0 else "failed",
                    ended=datetime.datetime.now().astimezone().isoformat())
    for name in ["stdout.txt", "stderr.txt"]:
        if (out/name).exists():
            metadata[name+"_sha256"] = sha(out/name)
    (out / "result.json").write_text(json.dumps(metadata, indent=2)+"\n")
    print(json.dumps(metadata))
    return result.returncode


def worker(out, command):
    out = Path(out)
    cg = next(s[3:] for s in Path("/proc/self/cgroup").read_text().splitlines()
              if s.startswith("0::"))
    peak = Path("/sys/fs/cgroup") / cg.lstrip("/") / "memory.peak"
    high, lowest, strikes, samples = 0, None, 0, 0
    start = time.monotonic()
    with (out/"stdout.txt").open("w") as stdout, (out/"stderr.txt").open("w") as stderr:
        p = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True)
        next_poll = 0
        next_live = 0
        terminated = False
        while True:
            elapsed = time.monotonic()-start
            if elapsed >= next_poll:
                raw, memory = available()
                (out/f"meminfo-{samples+1:04d}.txt").write_text(raw)
                samples += 1
                lowest = memory if lowest is None else min(lowest, memory)
                strikes = strikes + 1 if memory < 3 * 1024**3 else 0
                if strikes >= 2:
                    os.killpg(p.pid, 15)
                    terminated = True
                next_poll = elapsed + 60
            if peak.exists():
                high = max(high, int(peak.read_text()))
            if elapsed >= next_live:
                (out/"resources-live.json").write_text(json.dumps(
                    {"scope":cg,"memory_peak_bytes":high,"min_memavailable":lowest,
                     "elapsed_seconds":elapsed,"resource_terminated":terminated},indent=2)+"\n")
                next_live = elapsed + 1
            rc = p.poll()
            if rc is not None:
                break
            time.sleep(0.1)
    if peak.exists():
        high = max(high, int(peak.read_text()))
    (out/"resources.json").write_text(json.dumps(
        {"scope": cg, "memory_peak_bytes": high, "min_memavailable": lowest,
         "resource_terminated": terminated, "exit_code": rc}, indent=2)+"\n")
    print("ALL-END 已结束", datetime.datetime.now().astimezone().isoformat(), rc)
    return rc if rc >= 0 else 128-rc


if __name__ == "__main__":
    if sys.argv[1] == "--worker":
        sys.exit(worker(sys.argv[2], sys.argv[3:]))
    p = argparse.ArgumentParser()
    p.add_argument("--label", required=True)
    p.add_argument("--tier", choices=["light", "coverage"], default="light")
    p.add_argument("command", nargs=argparse.REMAINDER)
    a = p.parse_args()
    sys.exit(run(a.label, a.command, a.tier))
