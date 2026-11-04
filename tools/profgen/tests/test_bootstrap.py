import importlib.util
from pathlib import Path
import unittest

p = Path(__file__).resolve().parents[1] / 'bootstrap_equivalence.py'
spec = importlib.util.spec_from_file_location('bootstrap', p)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class BootstrapTests(unittest.TestCase):
    def test_constant_equal(self):
        r = b.evaluate([10]*5, [10]*5, 0, resamples=1000)
        self.assertEqual(r['difference']['ci95'], [0, 0])
        self.assertEqual(r['verdict'], 'equivalent')

    def test_known_difference(self):
        r = b.evaluate([10]*5, [11]*5, .5, resamples=1000)
        self.assertEqual(r['difference']['ci95'], [1, 1])
        self.assertEqual(r['relative_benefit_percent']['ci95'], [-10, -10])
        self.assertEqual(r['verdict'], 'insufficient_evidence')

    def test_relative_epsilon(self):
        r = b.evaluate([100]*5, [99]*5, 1.1, metric='relative-benefit-percent', resamples=1000)
        self.assertEqual(r['relative_benefit_percent']['ci95'], [1, 1])
        self.assertEqual(r['verdict'], 'equivalent')

    def test_paired(self):
        r = b.evaluate([10, 11, 12, 13, 14], [10.5, 11.5, 12.5, 13.5, 14.5], .6,
                       statistic='mean', paired=True, resamples=1000)
        self.assertEqual(r['difference']['ci95'], [.5, .5])
        self.assertEqual(r['verdict'], 'equivalent')

    def test_deterministic_and_crosses(self):
        args = ([1, 2, 3, 4, 5], [1, 3, 3, 4, 6], .01)
        r = b.evaluate(*args, resamples=1000)
        self.assertEqual(r, b.evaluate(*args, resamples=1000))
        self.assertEqual(r['verdict'], 'insufficient_evidence')
        self.assertLess(r['difference']['ci95'][0], 0)
        self.assertGreater(r['difference']['ci95'][1], 0)

    def test_zero_reference(self):
        r = b.evaluate([0]*5, [0]*5, 0, resamples=1000)
        self.assertEqual(r['difference']['ci95'], [0, 0])
        self.assertEqual(r['verdict'], 'equivalent')
        self.assertIsNone(r['relative_benefit_percent']['ci95'])
        r = b.evaluate([0]*5, [0]*5, 1, metric='relative-benefit-percent', resamples=1000)
        self.assertEqual(r['verdict'], 'insufficient_evidence')

    def test_invalid_inputs(self):
        for ref, candidate, epsilon in [([1]*4, [1]*5, 1),
                                         ([1]*5, [1]*5, -1), ([float('nan')]*5, [1]*5, 1)]:
            with self.subTest(ref=ref, epsilon=epsilon), self.assertRaises(ValueError):
                b.evaluate(ref, candidate, epsilon, resamples=1000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
