import unittest
from macro_function_rule import classify_macro, resolve_tu_prefix
from system_header_rule import group_scope

def chain_fixture():
    # All locations are synthetic; not evidence for any real compiler record.
    defs=[dict(name="OUTER",file="src/a.c",line=2),dict(name="INNER",file="include/macro.h",line=4)]
    return dict(ast_sha256="synthetic",token_sha256="synthetic",compiler_command=["fixture-clang"],
                definitions=defs,compiler_definitions=defs.copy(),
                tokens=[dict(text=";",spelling=dict(file="include/macro.h",offset=100),
                             expansion=dict(file="src/a.c",line=10),isMacroArgExpansion=False)],
                invocation_argument_ranges=[dict(file="src/a.c",begin=210,end=220)],
                definition_body_ranges=[dict(file="src/a.c",begin=30,end=80),dict(file="include/macro.h",begin=90,end=110)])


def positive():
    return dict(internal=True,pgo_name="src/a.c:_ZL3foov.__uniq.12",s_linkage="_ZL3foov.__uniq.12",
                s_cu_source="src/a.c",s_decl_file="src/a.c",s_decl_line=10,
                c_decl_file="src/a.c",c_decl_line=10,c_definition_verified=True,
                code_files=["include/macro.h"],coverage_main_file="include/macro.h",
                macro_invocation_verified=True,macro_definition_verified=True,
                macro_definition_file="include/macro.h",ordinary_same_name_other_file=True,fnda=3,compiler_ast_chain=chain_fixture())

class MacroTests(unittest.TestCase):
    def test_all_four(self):
        self.assertEqual(classify_macro(positive())["conclusion"],"macro_generated_function")
    def test_tu_differs(self):
        r=positive();r["pgo_name"]="other/a.c:"+r["s_linkage"]
        self.assertIsNone(classify_macro(r)["conclusion"])
    def test_basename_is_not_full_cu(self):
        r=positive();r["pgo_name"]="a.c:"+r["s_linkage"]
        self.assertIn("tu_prefix_not_equal_to_cu_source", classify_macro(r)["reasons"])
    def test_suffix_differs(self):
        r=positive();r["pgo_name"]=r["pgo_name"].replace(".12", ".13")
        self.assertIsNone(classify_macro(r)["conclusion"])
    def test_decl_differs(self):
        for k,v in [("c_decl_file","b.c"),("c_decl_line",11)]:
            r=positive();r[k]=v
            self.assertIsNone(classify_macro(r)["conclusion"])
    def test_code_in_decl_goes_to_original(self):
        r=positive();r["code_files"].append("src/a.c")
        self.assertEqual(classify_macro(r)["route"],"original_correspondence_rules")
    def test_not_macro_call(self):
        r=positive();r["macro_invocation_verified"]=False
        self.assertIsNone(classify_macro(r)["conclusion"])
    def test_external_uniqueness(self):
        r=positive();r.update(internal=False,pgo_name="foo",s_linkage="foo",coverage_name_count=1,s_top_definition_count=1)
        self.assertEqual(classify_macro(r)["conclusion"],"macro_generated_function")
        for k in ("coverage_name_count", "s_top_definition_count"):
            bad=r.copy();bad[k]=2
            self.assertIsNone(classify_macro(bad)["conclusion"])
    def test_executed_macro_inline_user(self):
        r=classify_macro(positive())
        self.assertEqual(group_scope([r["scope_role"],"reference_executed"]),"in_mapping_scope")
        self.assertFalse(r["in_u"]);self.assertFalse(r["in_c_denominator"])
    def test_nested_macro_not_silently_accepted(self):
        r=positive();del r["compiler_ast_chain"]
        self.assertIn("compiler_token_evidence_missing",classify_macro(r)["reasons"])
    def test_missing_evidence(self):
        for k in ("c_definition_verified", "macro_invocation_verified", "compiler_ast_chain", "ordinary_same_name_other_file"):
            r=positive();del r[k]
            self.assertIsNone(classify_macro(r)["conclusion"])

class SupplementTests(unittest.TestCase):
    def command(self, source, linkage):
        return dict(source=source,compile_log="fixture.log",compile_line=1,
                    linked_elf_code_dies=["0x1"],definition_linkages=[linkage])
    def test_basename_single_cu(self):
        r=positive();r["pgo_name"]="a.c:"+r["s_linkage"]
        r["tu_compile_evidence"]=[self.command("src/a.c",r["s_linkage"])]
        self.assertEqual(classify_macro(r)["conclusion"],"macro_generated_function")
    def test_multiple_cu_needs_unique_full_linkage(self):
        commands=[self.command("a/x.c","foo.__uniq.1"),self.command("b/x.c","foo.__uniq.2")]
        self.assertEqual(resolve_tu_prefix("x.c","foo.__uniq.1",commands),"a/x.c")
        commands[1]["definition_linkages"]=["foo.__uniq.1"]
        self.assertIsNone(resolve_tu_prefix("x.c","foo.__uniq.1",commands))
    def test_unlinked_command_cannot_prove_tu(self):
        c=self.command("src/a.c","foo");c["linked_elf_code_dies"]=[]
        self.assertIsNone(resolve_tu_prefix("a.c","foo",[c]))
    def chain(self):
        return chain_fixture()
    def test_two_level_chain(self):
        r=positive();r["compiler_ast_chain"]=self.chain()
        self.assertEqual(classify_macro(r)["conclusion"],"macro_generated_function")
    def test_definition_disagrees_with_compiler(self):
        r=positive();r["compiler_ast_chain"]=self.chain();r["compiler_ast_chain"]["compiler_definitions"]=[]
        self.assertIsNone(classify_macro(r)["conclusion"])
    def test_text_only_is_unresolved(self):
        r=positive();r["compiler_ast_chain"]=self.chain();del r["compiler_ast_chain"]["ast_sha256"]
        self.assertIsNone(classify_macro(r)["conclusion"])
    def test_statement_spelling_in_decl_routes_original(self):
        r=positive();r["compiler_ast_chain"]=self.chain()
        r["compiler_ast_chain"]["tokens"][0]["spelling"]["file"]="src/a.c"
        self.assertEqual(classify_macro(r)["route"],"original_correspondence_rules")


    def test_callsite_arguments(self):
        r=positive();c=r["compiler_ast_chain"]
        for text,offset in [("ff_put_pixels8_x2_arm",210),("8",220)]:
            c["tokens"].append(dict(text=text,spelling=dict(file="src/a.c",offset=offset),
                                    expansion=dict(file="src/a.c",line=10),isMacroArgExpansion=True))
        self.assertEqual(classify_macro(r)["conclusion"],"macro_generated_function")
    def test_intermediate_definition_argument(self):
        r=positive();r["compiler_ast_chain"]["tokens"].append(dict(text="8",
            spelling=dict(file="src/a.c",offset=50),expansion=dict(file="src/a.c",line=10),isMacroArgExpansion=True))
        self.assertEqual(classify_macro(r)["conclusion"],"macro_generated_function")
    def test_argument_third_file_unresolved(self):
        r=positive();t=r["compiler_ast_chain"]["tokens"][0]
        t.update(isMacroArgExpansion=True,spelling=dict(file="third.h",offset=50))
        self.assertIn("argument_spelling_outside_allowed_ranges",classify_macro(r)["reasons"])
    def test_missing_macro_argument_flag(self):
        r=positive();del r["compiler_ast_chain"]["tokens"][0]["isMacroArgExpansion"]
        self.assertIn("macro_argument_flag_missing",classify_macro(r)["reasons"])
    def test_scratch_not_reassigned_to_source(self):
        r=positive();t=r["compiler_ast_chain"]["tokens"][0]
        t.update(isMacroArgExpansion=True,spelling=dict(file="",presumed_file="<scratch space>",is_scratch=True,offset=50))
        self.assertIn("argument_spelling_outside_allowed_ranges",classify_macro(r)["reasons"])
    def test_outside_same_file_argument_interval(self):
        r=positive();t=r["compiler_ast_chain"]["tokens"][0]
        t.update(isMacroArgExpansion=True,spelling=dict(file="src/a.c",offset=300))
        self.assertIsNone(classify_macro(r)["conclusion"])


class RealTokenEvidenceTests(unittest.TestCase):
    """Read static compiler evidence only; never a sample profile."""
    def test_direct_call_real_evidence(self):
        import json
        from pathlib import Path
        p=Path(__file__).resolve().parents[2]/"docs/profgen/eval/prep/evidence/ruling2/supplement2/ffmpeg-thumb-01-tokens.json"
        r=json.loads(p.read_text())
        self.assertEqual(classify_macro(r["identity_record"])["conclusion"],"macro_generated_function")
        ts=r["identity_record"]["compiler_ast_chain"]["tokens"]
        cross=[t for t in ts if t["spelling"]["file"]!="libavcodec/pixels.h"]
        self.assertEqual(len(ts),28);self.assertEqual(len(cross),4)
        self.assertTrue(all(t["isMacroArgExpansion"] is True for t in cross))
    def test_real_nested_scratch_is_unresolved(self):
        import json
        from pathlib import Path
        base=Path(__file__).resolve().parents[2]/"docs/profgen/eval/prep/evidence/ruling2/supplement2"
        for name in ["ffmpeg-thumb-07-tokens.json","ffmpeg-thumb-18-tokens.json"]:
            r=json.loads((base/name).read_text())
            self.assertIsNone(classify_macro(r["identity_record"])["conclusion"])
            ts=r["identity_record"]["compiler_ast_chain"]["tokens"]
            self.assertEqual(sum(t["spelling"]["is_scratch"] for t in ts),2)
    def test_real_missing_flag_unresolved(self):
        import json
        from pathlib import Path
        p=Path(__file__).resolve().parents[2]/"docs/profgen/eval/prep/evidence/ruling2/supplement2/ffmpeg-thumb-01-tokens.json"
        r=json.loads(p.read_text());del r["identity_record"]["compiler_ast_chain"]["tokens"][1]["isMacroArgExpansion"]
        self.assertIn("macro_argument_flag_missing",classify_macro(r["identity_record"])["reasons"])

if __name__=="__main__":
    unittest.main(verbosity=2)
