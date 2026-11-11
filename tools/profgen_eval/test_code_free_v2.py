"""Synthetic facts for the descriptive-only code_free v2 rules."""
import unittest
from code_free_v2_rules import classify
def node(kind,a,b,start=0,end=200,**extra):
    return dict(kind=kind,begin_line=a,end_line=b,begin_offset=start,end_offset=end,**extra)
def token(kind,start=100,end=101):return dict(kind=kind,offset=start,end_offset=end)
def c(nodes=(),tokens=(),labels=(),available=True):
    return classify(12,{10},list(nodes),list(tokens),list(labels),available)
class DescriptiveV2(unittest.TestCase):
    def test_01_only_close_brace(self):self.assertEqual(c(tokens=[token("r_brace")])["category"],"structural_line")
    def test_02_only_else(self):self.assertEqual(c(tokens=[token("else")])["reason"],"else")
    def test_03_case_label(self):
        ts=[token("case",100,104),token("numeric_constant",105,106),token("colon",106,107)]
        self.assertEqual(c(tokens=ts,labels=[dict(begin_offset=100,end_offset=107)])["category"],"structural_line")
    def test_04_call_argument_continuation(self):
        self.assertEqual(c([node("CallExpr",10,14)],[token("raw_identifier")])["category"],"expr_continuation")
    def test_05_condition_continuation(self):
        r=c([node("IfStmt",10,30),node("BinaryOperator",10,14,start=5,end=120)],[token("ampamp")])
        self.assertEqual(r["category"],"expr_continuation");self.assertEqual(r["witness"]["kind"],"BinaryOperator")
    def test_06_folded_assignment(self):
        r=c([node("BinaryOperator",12,12,semantic_kind="assignment")],[token("raw_identifier"),token("equal",102,103)])
        self.assertEqual(r["category"],"own_stmt_no_code");self.assertEqual(r["statement_kind"],"assignment")
    def test_07_close_brace_and_statement(self):
        r=c([node("CallExpr",12,12,start=103)],[token("r_brace"),token("raw_identifier",103,104),token("l_paren",104,105)])
        self.assertEqual(r["category"],"own_stmt_no_code")
    def test_08_asm_first(self):
        self.assertEqual(c([node("GCCAsmStmt",10,14)],[token("string_literal")])["category"],"asm_interior")
    def test_09_other_compound_not_continuation(self):
        self.assertEqual(c([node("CompoundStmt",10,30)],[token("raw_identifier")])["category"],"other")
    def test_10_unavailable(self):self.assertEqual(c(available=False)["category"],"ast_unavailable")
    def test_11_comment_only(self):self.assertEqual(c()["reason"],"blank_or_comment_only")
    def test_12_control_whole_not_continuation(self):
        for kind in ("IfStmt","ForStmt","WhileStmt","SwitchStmt","DoStmt"):
            self.assertEqual(c([node(kind,10,30)],[token("raw_identifier")])["category"],"other")
    def test_13_start_on_continuation_line(self):
        r=c([node("CallExpr",10,14),node("IntegerLiteral",12,12,start=100,end=101)],[token("numeric_constant")])
        self.assertEqual(r["category"],"own_stmt_no_code")
    def test_14_inner_eligible_node(self):
        r=c([node("ReturnStmt",10,14),node("CallExpr",10,13,start=10,end=130)],[token("r_paren")])
        self.assertEqual(r["witness"]["kind"],"CallExpr")
    def test_15_decl_continuation(self):
        self.assertEqual(c([node("VarDecl",10,14)],[token("comma")])["category"],"expr_continuation")
    def test_16_label_and_call_not_structural(self):
        ts=[token("raw_identifier",100,101),token("colon",101,102),token("raw_identifier",103,104)]
        r=c([node("CallExpr",12,12,start=103)],ts,[dict(begin_offset=100,end_offset=102)])
        self.assertEqual(r["category"],"own_stmt_no_code")
    def test_17_function_container_not_guessed(self):
        r=c([node("FunctionDecl",10,30)],[token("hash")])
        self.assertEqual(r["category"],"other")
        self.assertIn("eligibility_unavailable",r["reason"])
if __name__=="__main__":unittest.main()
