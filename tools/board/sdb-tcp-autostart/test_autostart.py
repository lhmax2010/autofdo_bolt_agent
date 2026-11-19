import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from sdb_tcp_autostart import CONFIG, DROPIN, LINK, SOCKET, STATE

HERE = Path(__file__).resolve().parent


class StagedTree(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.vendor = self.root / "usr/lib/systemd/system"
        self.vendor.mkdir(parents=True)
        for unit in (SOCKET, "sdbd.service", "connman.service"):
            (self.vendor / unit).write_text(f"[Unit]\nDescription={unit}\n")
        (self.vendor / "multi-user.target.wants").mkdir()
        (self.vendor / "multi-user.target.wants/connman.service").symlink_to("../connman.service")
        (self.root / "etc/systemd/system").mkdir(parents=True)
        (self.root / "var/lib/connman").mkdir(parents=True)

    def run_entry(self, action, *options):
        argv = [str(HERE / action), "--root", str(self.root)]
        if action == "install":
            argv += ["--cidr", "192.0.2.7/24", "--interface", "eth1", "--port", "27202"]
        return subprocess.run(argv + list(options), text=True, capture_output=True, check=False)

    def test_dry_run_is_read_only(self):
        before = sorted(self.root.rglob("*"))
        plan = self.run_entry("install")
        self.assertEqual(plan.returncode, 0, plan.stderr)
        changes = json.loads(plan.stdout)["changes"]
        self.assertEqual(set(changes), {CONFIG, DROPIN, LINK})
        self.assertTrue(all(c["original"] is None for c in changes.values()))
        self.assertEqual(sorted(self.root.rglob("*")), before)

    def test_apply_reapply_uninstall_restore(self):
        before = sorted(self.root.rglob("*"))
        result = self.run_entry("install", "--apply", "--gateway", "192.0.2.1")
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads((self.root / STATE).read_text())
        self.assertEqual(state, json.loads(result.stdout))
        self.assertIn("DeviceName=eth1\nIPv4=192.0.2.7/255.255.255.0/192.0.2.1", (self.root / CONFIG).read_text())
        self.assertIn("ListenStream=192.0.2.7:27202\nBindToDevice=eth1\nFreeBind=yes", (self.root / DROPIN).read_text())
        self.assertTrue((self.root / LINK).is_symlink())
        reapplied = self.run_entry("install", "--apply", "--gateway", "192.0.2.1")
        self.assertEqual(reapplied.stdout, result.stdout)
        self.assertEqual(self.run_entry("uninstall").returncode, 0)
        self.assertTrue((self.root / STATE).exists())
        self.assertEqual(self.run_entry("uninstall", "--apply").returncode, 0)
        self.assertEqual(self.run_entry("uninstall", "--apply").returncode, 0)
        self.assertEqual(sorted(self.root.rglob("*")), before)

    def test_vendor_socket_link_is_recognized(self):
        wants = self.vendor / "sockets.target.wants"
        wants.mkdir()
        (wants / SOCKET).symlink_to(f"../{SOCKET}")
        result = self.run_entry("install", "--apply")
        self.assertEqual(result.returncode, 0)
        self.assertIn("EXISTS/REVIEW:", result.stdout)
        self.assertFalse((self.root / STATE).exists())

    def test_foreign_network_config_is_preserved(self):
        existing = self.root / "var/lib/connman/ethernet_external"
        existing.mkdir()
        settings = existing / "settings"
        settings.write_text("existing test settings")
        result = self.run_entry("install", "--apply")
        self.assertIn("EXISTS/REVIEW:", result.stdout)
        self.assertEqual(settings.read_text(), "existing test settings")
        self.assertFalse((self.root / STATE).exists())

    def test_external_edit_blocks_rollback_before_deleting(self):
        self.assertEqual(self.run_entry("install", "--apply").returncode, 0)
        (self.root / DROPIN).write_text("external edit")
        result = self.run_entry("uninstall", "--apply")
        self.assertEqual(result.returncode, 2)
        self.assertIn("changed outside this tool", result.stderr)
        self.assertTrue((self.root / LINK).is_symlink())
        self.assertTrue((self.root / CONFIG).exists())
        self.assertTrue((self.root / STATE).exists())

    def test_resume_partial_install_and_uninstall(self):
        self.assertEqual(self.run_entry("install", "--apply").returncode, 0)
        (self.root / CONFIG).unlink()
        self.assertEqual(self.run_entry("install", "--apply").returncode, 0)
        self.assertTrue((self.root / CONFIG).is_file())
        (self.root / LINK).unlink()
        self.assertEqual(self.run_entry("uninstall", "--apply").returncode, 0)
        self.assertFalse((self.root / CONFIG).exists())

    def test_refuse_symlink_directory_and_invalid_params(self):
        outside = self.root.parent
        (self.root / "var/lib/connman").rmdir()
        (self.root / "var/lib/connman").symlink_to(outside)
        self.assertEqual(self.run_entry("install", "--apply").returncode, 2)
        self.assertEqual(self.run_entry("install", "--port", "99999").returncode, 2)
        self.assertFalse((self.root / STATE).exists())


class VerifyEntry(unittest.TestCase):
    def check_listener(self, listener, expected_status):
        with tempfile.TemporaryDirectory() as fixture:
            commands = {
                "ip": "printf '2: eth1 inet 192.0.2.7/24 scope global eth1\\n'\n",
                "netstat": f"printf '%s\\n' '{listener}'\n",
                "systemctl": "exit 1\n",
            }
            for name, body in commands.items():
                command = Path(fixture) / name
                command.write_text("#!/bin/sh\n" + body)
                command.chmod(0o755)
            run = subprocess.run(
                [str(HERE / "verify"), "192.0.2.7", "27202", "eth1"], text=True, capture_output=True,
                env={**os.environ, "PATH": fixture + os.pathsep + os.environ["PATH"]}, check=False,
            )
        self.assertEqual(run.returncode, expected_status, run.stderr)
        return run.stdout

    def test_custom_listener_is_recognized(self):
        self.assertTrue(self.check_listener("tcp 0 0 0.0.0.0:27202 0.0.0.0:* LISTEN", 0).startswith("EXISTS:"))

    def test_other_port_does_not_match(self):
        result = self.check_listener("tcp 0 0 192.0.2.7:27203 0.0.0.0:* LISTEN", 1)
        self.assertTrue(result.startswith("ABSENT:"))


if __name__ == "__main__":
    unittest.main()
