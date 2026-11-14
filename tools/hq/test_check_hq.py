#!/usr/bin/env python3
"""Synthetic publication-policy checks; all fixtures stay under the workspace."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

W = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("checker", W / "tools/hq/check_hq.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

class PolicyTests(unittest.TestCase):
    def setUp(self):
        parent = W / "temp/hq-check-tests"
        parent.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=parent)
        self.root = Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()
    def scan(self, text):
        (self.root / "README.md").write_text(text)
        return checker.check_tree(self.root)
    def test_all_forbidden_words(self):
        for word in checker.LITERALS:
            with self.subTest(word=word):
                self.assertFalse(self.scan(word.upper())["passed"])
    def test_ai_boundaries(self):
        for text in ["AI", "ai-generated", "multi-ai", "use Ai."]:
            with self.subTest(text=text):
                self.assertFalse(self.scan(text)["passed"])
        self.assertTrue(self.scan("main maintain plain identifier")["passed"])
    def test_cjk_and_fullwidth(self):
        for text in ["\u4e2d", "\uff0c", "\u3002", "\u30a2", "\ud55c"]:
            with self.subTest(text=text):
                self.assertFalse(self.scan(text)["passed"])
    def test_non_ascii_warning(self):
        r = self.scan("caf\u00e9")
        self.assertTrue(r["passed"])
        self.assertEqual(len(r["warnings"]), 1)
    def test_main_function_is_not_banned(self):
        r = self.scan("Function: main: 1, 0, 1 sampled lines")
        self.assertTrue(r["passed"])
        self.assertEqual(r["whitelist_used"], [])
    def test_urls(self):
        for url in ["https://review.tizen.org/gerrit/", "https://download.tizen.org/a",
                    "ssh://user@review.tizen.org:29418/platform/upstream/llvm",
                    "https://download.blender.org/demo/movies/"]:
            with self.subTest(url=url):
                self.assertTrue(self.scan(url)["passed"])
        for url in ["https://example.com/", "https://download.tizen.org.evil.test/",
                    "https://name:pass@download.tizen.org/", "[x](javascript:alert)"]:
            with self.subTest(url=url):
                self.assertFalse(self.scan(url)["passed"])
    def test_relative_links(self):
        (self.root / "other.md").write_text("Text")
        self.assertTrue(self.scan("[x](other.md#anchor)")["passed"])
        self.assertFalse(self.scan("[x](absent.md)")["passed"])
        self.assertFalse(self.scan("[x](../outside.md)")["passed"])
        self.assertFalse(self.scan("[x](%2e%2e/outside.md)")["passed"])
    def test_reference_and_html_links(self):
        self.assertFalse(self.scan("[ref]: ../outside.md")["passed"])
        self.assertFalse(self.scan('<a href="../outside.md">x</a>')["passed"])
    def test_symlink_escape(self):
        (self.root / "link").symlink_to(self.root.parent)
        self.assertFalse(self.scan("Text")["passed"])
    def test_binary(self):
        (self.root / "binary").write_bytes(b"\xff")
        self.assertFalse(self.scan("Text")["passed"])
    def test_path_name(self):
        (self.root / "github.txt").write_text("Text")
        self.assertFalse(self.scan("Text")["passed"])
    def test_workspace_path(self):
        self.assertFalse(self.scan(str(W))["passed"])
    def test_exact_line_whitelist(self):
        checker.LINE_ALLOWLIST[("README.md", 1)] = {
            "line": "AI", "codes": ["forbidden:ai"], "reason": "Synthetic whitelist test"}
        try:
            self.assertTrue(self.scan("AI")["passed"])
            self.assertFalse(self.scan("AI changed")["passed"])
            self.assertFalse(self.scan("\nAI")["passed"])
        finally:
            checker.LINE_ALLOWLIST.clear()

if __name__ == "__main__":
    unittest.main()
