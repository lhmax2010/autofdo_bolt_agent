"""Synthetic parser fixtures: no real profile reads."""
import unittest
from registration_calibration import entry_keys

class SmokeParserFixtures(unittest.TestCase):
    def test_inline_context_and_explicit_zero(self):
        src=['f:99:0',' 1: 7',' 2.3: g:92','  4: 0']
        self.assertEqual(list(entry_keys(src)),[(2,[['f',1,0]]),(4,[['f',2,3],['g',4,0]])])
    def test_no_body_value_in_result(self):
        a=list(entry_keys(['f:10:0',' 1: 10']))
        b=list(entry_keys(['f:9999999:9',' 1: 9999999']))
        self.assertEqual(a,b)
    def test_raw_unique_name_preserved(self):
        self.assertEqual(list(entry_keys(['f.__uniq.123:1:0',' 1: 1']))[0][1][0][0],'f.__uniq.123')
    def test_malformed_depth_is_error(self):
        with self.assertRaises(ValueError):list(entry_keys(['f:1:0','   1: 1']))

if __name__=='__main__':unittest.main()
