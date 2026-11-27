import unittest

from afdo_wf import build
from afdo_wf.common import GateError


class SharedHostLimits(unittest.TestCase):
    def test_startup_io_gate_is_opt_in_and_strict(self):
        ready = dict(mem_available=16*build.GIB, load1=8, disk_free=50*build.GIB)
        self.assertTrue(build.can_start(ready))
        self.assertTrue(build.can_start(dict(ready, io_full_avg60=19.99)))
        self.assertFalse(build.can_start(dict(ready, io_full_avg60=20.0)))

    def test_shared_host_stops_after_sustained_pressure(self):
        sample = dict(mem_available=16*build.GIB, disk_free=50*build.GIB, io_full_avg60=70)
        self.assertEqual(build.stop_needed(sample, 0), (1, False))
        self.assertEqual(build.stop_needed(sample, 1), (2, True))
        self.assertEqual(build.stop_needed(dict(sample, io_full_avg60=0), 1), (0, False))
        self.assertEqual(build.stop_needed(dict(sample, mem_available=7*build.GIB), 1), (2, True))
        self.assertEqual(build.stop_needed(dict(mem_available=7*build.GIB, disk_free=50*build.GIB), 1), (0, False))

    def test_recovery_limits_are_explicit(self):
        self.assertFalse(build.recovery_limits({}))
        self.assertTrue(build.recovery_limits({'shared_host_recovery': True}))
        with self.assertRaises(GateError):
            build.recovery_limits({'shared_host_recovery': 'yes'})

    def test_waiver_only_affects_io_pressure(self):
        host = dict(shared_host_recovery=True, recovery_io_pressure_waived=True)
        self.assertTrue(build.io_pressure_waived(host))
        with self.assertRaises(GateError):
            build.io_pressure_waived({'recovery_io_pressure_waived': True})
        sample = dict(mem_available=16*build.GIB, disk_free=50*build.GIB, load1=4,
                      io_full_avg60=85, io_pressure_waived=True)
        self.assertTrue(build.can_start(sample))
        self.assertEqual(build.stop_needed(sample, 1), (0, False))
        self.assertFalse(build.can_start(dict(sample, mem_available=15*build.GIB)))
        self.assertEqual(build.stop_needed(dict(sample, mem_available=7*build.GIB), 1), (2, True))
