#!/usr/bin/env python3
"""Hand-written LLVM IR cases and real-Clang smoke, no LLVM binary required."""
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('matcher', HERE.parent / 'match_ir_semantics.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class SemanticTests(unittest.TestCase):
    def test_fixtures(self):
        for case in json.loads((HERE / 'ir/expectations.json').read_text()):
            with self.subTest(case=case['name']):
                ref = m.Module((HERE / ('ir/' + case['name'] + '-ref.ll')).read_text())
                sample = m.Module((HERE / ('ir/' + case['name'] + '-sample.ll')).read_text())
                result = m.compare(ref, sample, case['depth'])
                if case['reason']:
                    self.assertEqual(len(result['strict_pairs']), 0)
                    self.assertGreater(result['reason_counts'].get(case['reason'], 0), 0)
                else:
                    self.assertEqual(len(result['strict_pairs']), 1)
                    if case['name'] == 'inverse':
                        self.assertEqual(result['strict_pairs'][0]['successor_pairing'], [1, 0])
                    if case['name'] == 'zero-reference':
                        self.assertEqual(result['probability_denominator'], 0)
                    else:
                        self.assertTrue(all(x == 0 for x in result['strict_pairs'][0]['probability_errors']))

    def test_normalization_preserves_flags(self):
        arg = ('arg', 'i1', 0)
        one = ('constant', 'i1', 1)
        plain = ('xor', 'i1', (), 'i1', arg, one)
        flagged = ('xor', 'i1', ('disjoint',), 'i1', arg, one)
        self.assertEqual(m.normalized_condition(plain), ('not', arg))
        self.assertEqual(m.normalized_condition(flagged), flagged)
        self.assertNotEqual(m.normalized_condition(plain), m.normalized_condition(flagged))

    def test_real_diagnostic_summaries(self):
        text = (HERE / 'ir/equal-ref.ll').read_text()
        zero = "(0/2) of callsites' profile are invalid and (0/150) of samples are discarded due to callsite location mismatch.\n"
        r = m.compare(m.Module(zero + text), m.Module(text))
        self.assertEqual(len(r['strict_pairs']), 1)
        r = m.compare(m.Module(zero.replace('(0/150)', '(1/150)') + text), m.Module(text))
        self.assertIn('f', r['excluded_functions'])
        for diag in ["warning: Profile in f partially ignored, possibly due to the lack of a return path.",
                     "warning: no profile data available for function f"]:
            r = m.compare(m.Module(diag + "\n" + text), m.Module(text))
            self.assertIn('f', r['excluded_functions'])

    def test_unsupported_header_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported function header'):
            m.Module('define i32 @f(\n')
        with self.assertRaisesRegex(ValueError, 'No function definitions'):
            m.Module('')
        with self.assertRaisesRegex(ValueError, 'Unterminated function'):
            m.Module('define i32 @f() {\n')

    def test_function_exclusion(self):
        mod = m.Module((HERE / 'ir/equal-ref.ll').read_text())
        r = m.compare(mod, mod, diagnostics=["warning: profile for function 'f' is out of date"])
        self.assertIn('f', r['excluded_functions'])
        self.assertEqual(r['strict_pairs'], [])
        self.assertEqual(r['strict_ratios']['reference'], 0)
        self.assertIsNone(r['eligible_strict_ratios']['reference'])

    def test_unknown_diagnostic_scope(self):
        mod = m.Module((HERE / 'ir/equal-ref.ll').read_text())
        r = m.compare(mod, mod, diagnostics=['warning: profile mismatch (function unavailable)'])
        self.assertIn('f', r['excluded_functions'])

    def test_discriminator_and_inline_location(self):
        text = (HERE / 'ir/equal-ref.ll').read_text() + '\n!8 = !DILexicalBlockFile(scope: !0, file: !1, discriminator: 7)\n'
        for replacement in ['line: 2, column: 3, scope: !8',
                            'line: 2, column: 3, scope: !0, inlinedAt: !3']:
            r = m.compare(m.Module(text), m.Module(text.replace('line: 2, column: 3, scope: !0', replacement)))
            self.assertEqual(r['strict_pairs'], [])
            self.assertIn('no_candidate', r['reason_counts'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
