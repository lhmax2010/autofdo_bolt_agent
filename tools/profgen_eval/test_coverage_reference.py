"""Synthetic JSON-layout fixtures (not measurements, not sample profiles)."""
import json
import unittest
from coverage_reference import function_records, lines_from_segments, main_file_id

def f(name, count=1, file="header.h", start=3, end=9):
    return {"name": name, "count": count, "filenames": [file],
            "regions": [[start, 1, end, 2, count, 0, 0, 0]]}

class CoverageTests(unittest.TestCase):
    def test_three_cu_static_inline_one_executed(self):
        records = [f("header.h:foo.__uniq."+str(i), int(i==1)) for i in range(3)]
        m, e, _ = function_records(records)
        self.assertEqual(len(m), 1)
        self.assertEqual((m[0]["fnda"], len(m[0]["copies"])), (1, 3))
        self.assertFalse(e)

    def test_macro_internal_loop_and_ordinary_function_same_file(self):
        x = f("caller", file="same.c", start=20, end=25)
        x["filenames"].append("same.c")
        x["regions"] += [[22, 1, 22, 8, 1, 0, 1, 1],
                         [2, 1, 4, 2, 100, 1, 0, 0]]
        m, _, macros = function_records([x, f("ordinary", file="same.c", start=30,end=35)])
        self.assertEqual((m[0]["start"],m[0]["end"]), (20,25))
        self.assertEqual(len(m), 2)
        self.assertEqual(macros[0]["expansion_file_id"], 1)

    def test_template_included_with_two_names(self):
        m, _, _ = function_records([f("template.h:alpha"), f("template.h:beta")])
        self.assertEqual([x["name"] for x in m], ["alpha", "beta"])

    def test_two_executed_functions_same_physical_line(self):
        m, _, _ = function_records([f("a", start=7, end=7),f("b",start=7,end=7)])
        # They remain two identities, allowing downstream overlap exclusion.
        self.assertEqual(len([x for x in m if x["fnda"] > 0 and x["start"]<=7<=x["end"]]),2)

    def test_empty_main_view(self):
        x=f("recursive_expansion")
        x["regions"]=[[1,1,1,2,7,0,0,1]]
        self.assertIsNone(main_file_id(x))
        m, e, _=function_records([x])
        self.assertEqual(m,[])
        self.assertEqual(e[0]["reason"],"no_main_view")
        self.assertEqual(e[0]["status"],"unresolved_requires_correspondence")

    def test_main_file_not_zero(self):
        x=f("f")
        x["filenames"]=["macro.h","actual.c"]
        x["regions"]=[[20,1,23,2,1,1,0,0],[21,1,21,2,1,1,0,1],[1,1,9,2,8,0,0,0]]
        self.assertEqual(main_file_id(x),1)
        m,_,_=function_records([x])
        self.assertEqual((m[0]["file"],m[0]["start"],m[0]["end"]),("actual.c",20,23))

    def test_multiple_regions_gap_and_continuation(self):
        counts, multi=lines_from_segments([
            [1,1,3,True,True,False],[1,2,7,True,True,False],
            [3,1,9,True,True,True],[4,1,0,False,True,False]])
        self.assertEqual(multi,[1])
        self.assertEqual(counts,{1:7,2:7,3:7})
        # No region entry on line2: continuation is not a second region.

if __name__=="__main__":
    unittest.main(verbosity=2)
