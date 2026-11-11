"""Synthetic ruling3-rev1 fixtures; never reads formal RUN data."""
import collections,unittest
from ruling3_union import union_domain,classify_line
from ruling34_static import measures,profile_key
F="/synthetic.c"
def k(n):return F,n
def ast(kind,a,b):return dict(file=F,kind=kind,begin_line=a,end_line=b)
class UnionRuling(unittest.TestCase):
    def test_01_S_only_enters_C(self):
        c,a,b=union_domain({k(10)},set(),{k(10)})
        self.assertEqual(c,{k(10)});self.assertFalse(a);self.assertEqual(b,c)
    def test_02_neither_is_code_free(self):
        c,_,_=union_domain({k(10)},set(),set())
        self.assertEqual({k(10)}-c,{k(10)})
    def test_03_C_only_no_key_is_loss(self):
        c,_,_=union_domain({k(10)},{k(10)},set())
        u,_,s=measures({k(10):9},{x:{0} for x in c},{k(10):{"no_key_line"}},set())
        self.assertFalse(u);self.assertEqual(s["loss_buckets"],[dict(reasons=["no_key_line"],lines=1,DA=9)])
    def test_04_nonleaf_zero_does_not_decide_C(self):
        frames=[dict(name="leaf",line=10,start_line=1,base_discriminator=0),
                dict(name="parent",line=0,start_line=1,base_discriminator=0)]
        self.assertIsNone(profile_key(frames))
        c,_,_=union_domain({k(10)},set(),{k(10)})
        u,_,s=measures({k(10):9},{x:{0} for x in c},{k(10):{"no_key_line"}},set())
        self.assertEqual(s["R_C"],9);self.assertFalse(u)
    def test_05_asm_interior_priority(self):
        r=classify_line(F,12,{k(10)},[ast("GCCAsmStmt",10,14),ast("CompoundStmt",1,20)],True)
        self.assertEqual(r["category"],"asm_interior")
    def test_06_multiline_call_arguments(self):
        r=classify_line(F,12,{k(10)},[ast("CallExpr",10,14)],True)
        self.assertEqual(r["category"],"stmt_continuation");self.assertEqual(r["witness"]["kind"],"CallExpr")
    def test_07_multiline_condition(self):
        r=classify_line(F,12,{k(10)},[ast("BinaryOperator",10,14)],True)
        self.assertEqual(r["category"],"stmt_continuation");self.assertEqual(r["witness"]["kind"],"BinaryOperator")
    def test_08_unavailable_is_not_other(self):
        self.assertEqual(classify_line(F,12,set(),[],False)["category"],"ast_unavailable")
    def test_09_macro_outside_original_not_admitted(self):
        c,_,_=union_domain({k(10)},{k(20)},{k(20)})
        self.assertFalse(c)
    def test_10_no_other_c_line_is_other(self):
        self.assertEqual(classify_line(F,12,set(),[ast("CallExpr",10,14)],True)["category"],"other")
if __name__=="__main__":unittest.main()
