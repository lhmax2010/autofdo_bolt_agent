"""Synthetic API records for v1.7 O.2.2 operand-role regressions."""
import copy
import unittest
from test_token_paste_rule import fixture, loc, tok
from token_paste_rule import prove


def renamed():
    t, c, ms = fixture()
    m = ms[0]
    m["body"][0]["text"] = "OPNAME"
    m["body"][2]["text"] = "_pixels8"
    t["text"] = "put_pixels8"
    m["paste_fragments"][0]["prefix_lexing"][-1]["text"] = t["text"]
    return t, c, ms


class V17PasteTests(unittest.TestCase):
    def test_opname_literal_role_before_fileid(self):
        t, c, ms = renamed()
        r = prove(t, c, ms)
        self.assertEqual(r["status"], "proved", r)
        self.assertEqual(r["operands"][1]["proof_path"], "definition_body")
        self.assertFalse(r["operands"][1]["token"]["isMacroArgExpansion"])
        self.assertEqual(r["operands"][0]["proof_path"],
                         "direct_unexpanded_argument_slot")

    def test_a_underscore_b_c(self):
        t, c, ms = fixture()
        m = ms[0]
        body = []
        for i, text in enumerate(["a", "##", "_", "##", "b", "##", "c"]):
            b = tok(text, loc("macro.h", 1000 + i, 2),
                    "hashhash" if text == "##" else "identifier")
            b["parameter_num"] = {0: 0, 4: 1, 6: 2}.get(i, -1)
            body.append(b)
        m["body"] = body
        for n, text in enumerate(["put", "pixels", "8"]):
            a = tok(text, loc("src/a.c", 24 + n * 8),
                    "numeric_constant" if text == "8" else "identifier")
            if n == 0:
                m["arguments"][0] = [a]
            else:
                m["arguments"].append([a])
            slot = copy.deepcopy(m["argument_slots"][0])
            slot.update(slot=n, token_raws=[a["location"]["raw"]],
                        begin=a["spelling"].copy(),
                        end_exclusive=dict(a["spelling"],
                                           offset=a["spelling"]["offset"] + len(text)))
            if n == 0:
                m["argument_slots"][0] = slot
            else:
                m["argument_slots"].append(slot)
        t["trace"][0]["immediate_expansion"]["end"]["offset"] = 1006
        t["trace"][0]["immediate_expansion"]["end"]["raw"] = 9006
        t["text"] = "put_pixels8"
        f = m["paste_fragments"][0]
        f["end"] = body[-1]["location"]
        f["prefix_lexing"] = [
            dict(text=s, kind="identifier", whole_token=True)
            for s in ["put", "put_", "put_pixels", "put_pixels8"]]
        r = prove(t, c, ms)
        self.assertEqual(r["status"], "proved", r)
        self.assertEqual([o["proof_path"] for o in r["operands"]],
                         ["direct_unexpanded_argument_slot", "definition_body",
                          "direct_unexpanded_argument_slot",
                          "direct_unexpanded_argument_slot"])

    def test_same_text_from_other_definition_rejected(self):
        t, c, ms = renamed()
        ms[0]["body"][2]["spelling"] = loc("another_macro.h", 1005, 9)
        r = prove(t, c, ms)
        self.assertEqual(r["status"], "unresolved")
        self.assertIn("paste_literal_outside_definition", r["reason_codes"])
