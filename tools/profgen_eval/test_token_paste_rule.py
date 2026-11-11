"""Synthetic compiler-evidence fixtures; never presented as measured API output."""
import copy
import unittest
from token_paste_rule import prove
from macro_function_rule import classify_macro
from test_macro_function_rule import positive


def loc(file,offset,fid=1,macro=False,scratch=False,raw=None):
    return dict(file=file,offset=offset,file_id=fid,is_macro=macro,is_scratch=scratch,
                raw=offset if raw is None else raw,presumed_file="<scratch space>" if scratch else file,
                line=10,column=1)


def tok(text,where,kind="identifier",arg=False):
    return dict(text=text,kind=kind,length=len(text),location=where.copy(),spelling=where.copy(),
                expansion=loc("src/a.c",20),isMacroArgExpansion=arg,trace=[])


def fixture(levels=1):
    # Each nesting level has its own callback and definition. Innermost argument
    # is directly written in a single MacroArgs slot; outer operands are scratch.
    macros=[];callbacks=[];invocations=[]
    current=tok("put",loc("src/a.c",24))
    for i in range(levels):
        name="PASTE"+str(i);base=1000+i*100;call=20+i*100
        begin=loc("src/a.c",call);end=loc("src/a.c",call+30)
        inv=dict(begin=begin,end=end)
        body=[tok("x",loc("macro.h",base,2)),tok("##",loc("macro.h",base+2,2),"hashhash"),
              tok("_z",loc("macro.h",base+5,2))]
        for b,n in zip(body,[0,-1,-1]):b["parameter_num"]=n
        b=loc("macro.h",base,50+i,True,raw=9000+i*100)
        e=loc("macro.h",base+5,50+i,True,raw=9005+i*100)
        owner=dict(macro=name,instance_range=inv,file_id=50+i)
        result=tok(current["text"]+"_z",loc("",200+i,100+i,True,True,10000+i),arg=True)
        result["spelling"]=loc("",200+i,10,False,True)
        result["trace"]=[dict(immediate_spelling=result["spelling"],
            immediate_expansion=dict(begin=b,end=e),begin_owner=owner,end_owner=copy.deepcopy(owner))]
        m=dict(name=name,name_location=begin,invocation=inv,definition=dict(begin=loc("macro.h",base-5,2),end=loc("macro.h",base+10,2)),
            msvc_compat=False,_raw_line=i+1,body=body,arguments=[[current]],
            argument_slots=[dict(slot=0,count=1,copied_in_macroexpands=True,method="MacroArgs::getUnexpArgument",
                invocation=inv,name_raw=begin["raw"],token_raws=[current["location"]["raw"]],
                begin=current["spelling"].copy(),end_exclusive=dict(current["spelling"],offset=current["spelling"]["offset"]+current["length"]))],
            paste_fragments=[dict(begin=body[0]["location"],end=body[-1]["location"],prefix_lexing=[
                dict(text=current["text"],kind="identifier",whole_token=True),
                dict(text=result["text"],kind="identifier",whole_token=True)])])
        macros.append(m);callbacks.append(dict(name=name,invocation=inv));invocations.append(dict(name=name,range=inv))
        current=result
    context=dict(macro_callbacks=callbacks,invocations=invocations,coverage_main_file="macro.h",
        chain=dict(invocation_argument_ranges=[dict(file="src/a.c",begin=24,end=26)],
                   definition_body_ranges=[dict(file="chain.h",begin=300,end=310)]))
    return current,context,macros


def retarget_argument(t,c,ms,new):
    m=ms[0];m["arguments"][0]=[new]
    t["text"]=new["text"]+"_z"
    m["paste_fragments"][0]["prefix_lexing"]=[dict(text=new["text"],kind="identifier",whole_token=True),
                                            dict(text=t["text"],kind="identifier",whole_token=True)]


class SyntheticPasteTests(unittest.TestCase):
    def check(self,data,reason=None):
        t,c,ms=data;r=prove(t,c,ms)
        if reason is None:self.assertEqual(r["status"],"proved",r.get("reason_codes"))
        else:self.assertIn(reason,r["reason_codes"]);self.assertEqual(r["status"],"unresolved")
        return r
    def test_01_parameter_paste_literal(self):self.check(fixture())
    def test_02_two_level_scratch_operand(self):
        r=self.check(fixture(2));self.assertEqual(r["operands"][0]["subproof"]["status"],"proved")
    def test_03_argument_from_other_chain_definition(self):
        t,c,ms=fixture();a=tok("8",loc("chain.h",305,20,True),"numeric_constant",True)
        retarget_argument(t,c,ms,a);self.check((t,c,ms))
    def test_04_argument_from_outside_chain(self):
        t,c,ms=fixture();a=tok("8",loc("third.h",305,20,True),"numeric_constant",True)
        retarget_argument(t,c,ms,a);self.check((t,c,ms),"paste_argument_source_outside_chain")
    def test_05_stringification(self):
        t,c,ms=fixture();ms[0]["body"][1]["kind"]="hash"
        self.check((t,c,ms),"paste_stringification")
    def test_06_multitoken_argument(self):
        t,c,ms=fixture();ms[0]["arguments"][0].append(tok("extra",loc("src/a.c",28)))
        self.check((t,c,ms),"paste_multitoken_argument")
    def test_07_placemarker(self):
        t,c,ms=fixture();ms[0]["arguments"][0]=[];self.check((t,c,ms),"paste_empty_argument")
    def test_08_tampered_text(self):
        t,c,ms=fixture();t["text"]="tampered";self.check((t,c,ms),"paste_text_mismatch")
    def test_09_endpoint_outside_definition(self):
        t,c,ms=fixture();ms[0]["definition"]["begin"]["offset"]+=6
        self.check((t,c,ms),"paste_endpoint_outside_definition")
    def test_10_recursion_depth(self):self.check(fixture(10),"paste_recursion_depth_exceeded")
    def test_11_nonunique_layer(self):
        t,c,ms=fixture();t["trace"]*=2;self.check((t,c,ms),"paste_layer_not_unique")
    def test_12_direct_exact_slot(self):
        r=self.check(fixture());o=r["operands"][0]
        self.assertEqual(o["proof_path"],"direct_unexpanded_argument_slot")
        self.assertFalse(o["token"]["isMacroArgExpansion"])
        self.assertEqual(o["slot_evidence"]["slot"],0)
    def test_13_wrong_slot(self):
        t,c,ms=fixture();ms[0]["argument_slots"][0]["token_raws"]=[99]
        self.check((t,c,ms),"direct_argument_slot_mismatch")
    def test_14_same_file_outside_slot(self):
        t,c,ms=fixture();ms[0]["argument_slots"][0]["begin"]["offset"]+=1
        self.check((t,c,ms),"direct_argument_outside_slot")
    def test_15_instance_outside_chain(self):
        t,c,ms=fixture();c["macro_callbacks"]=[]
        self.check((t,c,ms),"paste_instance_not_in_function_chain")
    def test_16_formal_classifier_integration(self):
        t,c,ms=fixture();r=positive();chain=r["compiler_ast_chain"]
        t["expansion"]=dict(file="src/a.c",line=10);chain["tokens"]=[t]
        c["macros"]=ms;chain["paste_context"]=c
        self.assertEqual(classify_macro(r)["conclusion"],"macro_generated_function")
        self.assertEqual(chain["paste_proofs"][0]["status"],"proved")
    def test_17_missing_slot_evidence(self):
        t,c,ms=fixture();del ms[0]["argument_slots"]
        self.check((t,c,ms),"direct_argument_slot_missing")
    def test_18_cross_fileid(self):
        t,c,ms=fixture();ms[0]["arguments"][0][0]["spelling"]["file_id"]=99
        self.check((t,c,ms),"direct_argument_cross_fileid")
    def test_19_physical_body_unchanged(self):
        r=positive();r["compiler_ast_chain"]["paste_context"]={}
        t=r["compiler_ast_chain"]["tokens"][0];t["spelling"]["file"]="src/a.c"
        self.assertEqual(classify_macro(r)["route"],"original_correspondence_rules")

if __name__=="__main__":unittest.main(verbosity=2)
