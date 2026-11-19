#!/usr/bin/env python3
"""Stage or roll back a TCP SDB boot configuration in an offline Tizen tree."""

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import stat
import tempfile

STATE = "etc/systemd/system/.k1-sdb-tcp-autostart.json"
SOCKET = "sdbd_tcp.socket"
CONFIG = "var/lib/connman/k1-sdb-tcp-ethernet.config"
DROPIN = f"etc/systemd/system/{SOCKET}.d/70-k1-lab-listener.conf"
LINK = f"etc/systemd/system/sockets.target.wants/{SOCKET}"
DROPIN_DIR = str(Path(DROPIN).parent)
LINK_DIR = str(Path(LINK).parent)
MANAGED = {CONFIG, DROPIN, LINK}
PARENTS = {DROPIN_DIR, LINK_DIR}
BASES = ("etc/systemd/system", "usr/lib/systemd/system", "lib/systemd/system")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def present(path):
    return path.exists() or path.is_symlink()


def safe(root, relative):
    path = root / relative
    if any(parent.is_symlink() for parent in path.parents if parent != root and root in parent.parents):
        raise ValueError(f"symlink directory in managed path: {relative}")
    return path


def describe(path):
    if not present(path):
        return None
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        return {"kind": "symlink", "sha256": digest(os.fsencode(os.readlink(path)))}
    if stat.S_ISREG(mode):
        return {"kind": "file", "sha256": digest(path.read_bytes()), "mode": stat.S_IMODE(mode)}
    raise ValueError(f"unsupported file type: {path}")


def specification(cidr, interface, port, gateway=None):
    ip = ipaddress.IPv4Interface(cidr)
    if "/" not in cidr or ip.ip.is_unspecified or ip.ip.is_multicast or ip.ip.is_loopback:
        raise ValueError("provide an interface IPv4 address with /prefix")
    if ip.network.prefixlen < 31 and ip.ip in (ip.network.network_address, ip.network.broadcast_address):
        raise ValueError("address must be usable on the selected subnet")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,14}", interface) or not 1 <= port <= 65535:
        raise ValueError("invalid interface name or port")
    ipv4 = f"{ip.ip}/{ip.netmask}"
    if gateway:
        gw = ipaddress.IPv4Address(gateway)
        if gw not in ip.network or gw == ip.ip or gw.is_unspecified or gw.is_multicast:
            raise ValueError("gateway must be distinct and in the interface subnet")
        if ip.network.prefixlen < 31 and gw in (ip.network.network_address, ip.network.broadcast_address):
            raise ValueError("gateway must be usable on the selected subnet")
        ipv4 += f"/{gw}"
    return {
        CONFIG: ("file", f"[service_k1_sdb_ethernet]\nType=ethernet\nDeviceName={interface}\nIPv4={ipv4}\n"),
        DROPIN: ("file", f"[Socket]\nListenStream=\nListenStream={ip.ip}:{port}\nBindToDevice={interface}\nFreeBind=yes\n"),
        LINK: ("symlink", f"/usr/lib/systemd/system/{SOCKET}"),
    }


def record(content):
    kind, text = content
    meta = {"kind": kind, "sha256": digest(text.encode())}
    if kind == "file":
        meta["mode"] = 0o644
    return meta


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_file(path, contents, mode):
    fd, filename = tempfile.mkstemp(prefix=".k1-sdb-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(filename, path)
    finally:
        os.unlink(filename)
    sync_dir(path.parent)


@contextmanager
def locked_tree(root):
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def boot_links(root, unit):
    for base in BASES:
        for suffix in ("wants", "requires"):
            yield from (root / base).glob(f"*.{suffix}/{unit}")


def assert_supported(root):
    vendor = root / "usr/lib/systemd/system"
    for unit in (SOCKET, "sdbd.service", "connman.service"):
        if not (vendor / unit).is_file():
            raise ValueError(f"missing supported Tizen vendor unit: {unit}")
    if not any(path.is_symlink() for path in boot_links(root, "connman.service")):
        raise ValueError("ConnMan boot activation not established")
    for dirname in ("etc/systemd/system", "var/lib/connman"):
        if not safe(root, dirname).is_dir() or safe(root, dirname).is_symlink():
            raise ValueError(f"expected real directory in mounted tree: {dirname}")


def check_existing(root):
    # The Tizen vendor link is often present even when systemctl reports disabled.
    sockets = list(boot_links(root, SOCKET))
    overrides = [
        path for base in BASES
        for path in (root / base).glob(f"{SOCKET}.d/*.conf")
    ]
    alternative_units = []
    for base in BASES:
        for pattern in ("*sdb*.service", "*sdb*.socket", "*sdb*.timer"):
            alternative_units.extend(
                path for path in (root / base).glob(pattern)
                if path.name not in {SOCKET, "sdbd.service", "sdbd.socket", "udev-sdb-init.service"}
            )
    replacement = root / "etc/systemd/system" / SOCKET
    provisioning = (*safe(root, "var/lib/connman").glob("*.config"),
                    *safe(root, "var/lib/connman").glob("ethernet*"))
    return [p for p in (*sockets, *overrides, *alternative_units, replacement, *provisioning) if present(p)]


def load_state(root):
    path = safe(root, STATE)
    if not present(path):
        return None
    if path.is_symlink() or not path.is_file():
        raise ValueError("manifest is not a regular file")
    state = json.loads(path.read_text())
    changes = state["changes"]
    if (state["version"] != 1 or set(changes) != MANAGED or
            not set(state["created_dirs"]) <= PARENTS or
            any(change["original"] is not None for change in changes.values())):
        raise ValueError("invalid manifest")
    return state


def precheck_managed(root, state):
    for name, change in state["changes"].items():
        path = safe(root, name)
        current = describe(path)
        if current is not None and current != change["new"]:
            raise ValueError(f"managed file changed outside this tool: /{name}")
    for name in state["created_dirs"]:
        path = safe(root, name)
        if present(path) and (path.is_symlink() or not path.is_dir()):
            raise ValueError(f"managed directory replaced: /{name}")


def install(root, contents, apply):
    assert_supported(root)
    state = load_state(root)
    changes = {name: {"original": None, "new": record(value)} for name, value in contents.items()}
    if state is None:
        prior = check_existing(root)
        prior.extend(safe(root, name) for name in contents if present(safe(root, name)))
        if prior:
            paths = ", ".join(f"/{path.relative_to(root)}" for path in sorted(set(prior)))
            print(f"EXISTS/REVIEW: board has existing network or SDB configuration: {paths}")
            return
        dirs = sorted(name for name in PARENTS if not present(safe(root, name)))
        state = {"version": 1, "created_dirs": dirs, "changes": changes}
        if apply:
            atomic_file(safe(root, STATE), (json.dumps(state, indent=2) + "\n").encode(), 0o600)
    elif state["changes"] != changes:
        raise ValueError("parameters differ from the existing manifest")
    precheck_managed(root, state)
    if not apply:
        print(json.dumps(state, indent=2))
        return
    for name in state["created_dirs"]:
        path = safe(root, name)
        if not path.exists():
            path.mkdir(mode=0o755)
            sync_dir(path.parent)
    for name, (kind, text) in contents.items():
        path = safe(root, name)
        if not present(path):
            if kind == "symlink":
                path.symlink_to(text)
                sync_dir(path.parent)
            else:
                atomic_file(path, text.encode(), 0o644)
        if describe(path) != changes[name]["new"]:
            raise ValueError(f"post-install SHA or mode mismatch: /{name}")
    print(json.dumps(state, indent=2))


def uninstall(root, apply):
    state = load_state(root)
    if state is None:
        print("ABSENT: no installer manifest")
        return
    precheck_managed(root, state)
    for name in state["created_dirs"]:
        directory = safe(root, name)
        if directory.is_dir() and any(str(child.relative_to(root)) not in MANAGED for child in directory.iterdir()):
            raise ValueError(f"unmanaged entries in /{name}; review before rollback")
    if not apply:
        print(json.dumps(state, indent=2))
        return
    for name in reversed(tuple(state["changes"])):
        path = safe(root, name)
        if present(path):
            path.unlink()
            sync_dir(path.parent)
        if describe(path) != state["changes"][name]["original"]:
            raise ValueError(f"rollback verification failed: /{name}")
    for name in reversed(state["created_dirs"]):
        path = safe(root, name)
        if path.exists():
            path.rmdir()
            sync_dir(path.parent)
    path = safe(root, STATE)
    path.unlink()
    sync_dir(path.parent)
    print("RESTORED: managed entries verified absent")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("install", "uninstall"):
        options = sub.add_parser(command)
        options.add_argument("--root", required=True, type=Path, help="offline root tree, never /")
        options.add_argument("--apply", action="store_true", help="write the staged changes")
        if command == "install":
            options.add_argument("--cidr", required=True)
            options.add_argument("--interface", required=True)
            options.add_argument("--port", required=True, type=int)
            options.add_argument("--gateway")
    args = parser.parse_args()
    try:
        root = args.root.resolve(strict=True)
        if root == Path("/") or not root.is_dir():
            raise ValueError("--root must be an offline directory other than /")
        with locked_tree(root):
            if args.command == "install":
                install(root, specification(args.cidr, args.interface, args.port, args.gateway), args.apply)
            else:
                uninstall(root, args.apply)
    except (OSError, KeyError, ValueError, TypeError) as error:
        parser.exit(2, f"ERROR: {error}\n")


if __name__ == "__main__":
    main()
