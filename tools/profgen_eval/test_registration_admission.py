"""Synthetic argv cases; no profiles or response files are opened."""
import unittest
from registration_admission import validate_generation_argv

class Admission(unittest.TestCase):
    def test_rsp(self):
        with self.assertRaisesRegex(ValueError,"response_file"): validate_generation_argv(["tool","@missing.rsp"])
    def test_single_equals(self):
        with self.assertRaisesRegex(ValueError,"test_injection"): validate_generation_argv(["tool","-ip-test-inject-failure=symbolize"])
    def test_double_equals(self):
        with self.assertRaisesRegex(ValueError,"test_injection"): validate_generation_argv(["tool","--ip-test-inject-failure=symbolize"])
    def test_single_separate(self):
        with self.assertRaisesRegex(ValueError,"test_injection"): validate_generation_argv(["tool","-ip-test-inject-failure","symbolize"])
    def test_double_separate(self):
        with self.assertRaisesRegex(ValueError,"test_injection"): validate_generation_argv(["tool","--ip-test-inject-failure","symbolize"])
    def test_empty_injection(self):
        with self.assertRaisesRegex(ValueError,"test_injection"): validate_generation_argv(["tool","--ip-test-inject-failure="])
    def test_ordinary(self):
        self.assertTrue(validate_generation_argv(["tool","--ip-samples","--output=x"]))
    def test_filename_not_option(self):
        self.assertTrue(validate_generation_argv(["tool","--binary=some-ip-test-inject-failure-file"]))
