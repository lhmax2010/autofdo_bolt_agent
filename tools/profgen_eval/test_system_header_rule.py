import unittest
from system_header_rule import classify, group_scope, validate_global_files, proof_from_record
import copy
import csv
import json
from pathlib import Path

def evidence():
    return dict(commands_verified=True,clang_v_verified=True,
                s_dirs=["/usr/include","/usr/lib/clang/22/include"],
                c_dirs=["/usr/lib/clang/22/include","/usr/include"],
                coverage_disabled_verified=True,skip_source_verified=True,
                global_coverage_file_check_passed=True)

class RulingTests(unittest.TestCase):
    def test_all_four_positive(self):
        self.assertEqual(classify("/usr/include/bits/string_fortified.h",[],evidence())["conclusion"],
                         "system_header_no_reference")
    def test_outside_or_prefix_lookalike(self):
        for path in ["/project/header.h","/usr/include-other/header.h"]:
            self.assertIsNone(classify(path,[],evidence())["conclusion"])
    def test_s_c_dirs_differ(self):
        e=evidence();e["c_dirs"]=["/different"]
        self.assertIsNone(classify("/usr/include/a.h",[],e)["conclusion"])
    def test_global_file_presence_stops(self):
        with self.assertRaisesRegex(ValueError,"coverage_file_in_system_directory"):
            validate_global_files(["/project/a.c","/usr/include/a.h"],evidence()["s_dirs"])
    def test_candidate_goes_to_original_rule(self):
        r=classify("/usr/include/a.h",[{"name":"a"}],evidence())
        self.assertEqual(r["route"],"original_correspondence_rules")
        self.assertIsNone(r["conclusion"])
    def test_executed_user_outer_stays_in_scope(self):
        self.assertEqual(group_scope(["system_header_no_reference","reference_executed"]),
                         "in_mapping_scope")
    def test_system_only_outer_out_of_scope(self):
        self.assertEqual(group_scope(["system_header_no_reference"]),"known_out_of_scope")
    def test_mixed_closed_out_of_scope(self):
        self.assertEqual(group_scope(["system_header_no_reference","not_instrumented",
                                      "reference_unexecuted"]),"known_out_of_scope")
    def test_missing_any_positive_evidence(self):
        for flag in ["commands_verified","clang_v_verified","coverage_disabled_verified",
                     "skip_source_verified","global_coverage_file_check_passed"]:
            e=evidence();e[flag]=False
            self.assertIsNone(classify("/usr/include/a.h",[],e)["conclusion"])
    def test_unresolved_does_not_close_group(self):
        self.assertIsNone(group_scope(["system_header_no_reference",None]))

class RetainedEvidenceTests(unittest.TestCase):
    def test_missing_or_false_per_side_field_unresolves_all_related_records(self):
        base=Path("docs/profgen/eval/prep/evidence/ruling1")
        records=json.loads((base/"header-evidence.json").read_text())
        for obj, record in records.items():
            related=[]
            for p in (base/(obj+"-conclusions")).glob("complete-inventory-*.csv"):
                with p.open() as f:
                    related.extend(r for r in csv.DictReader(f)
                                   if r["conclusion"]=="system_header_no_reference")
            self.assertTrue(related)
            for side in ("S", "C"):
                for field in ("clang_v_verified", "coverage_disabled_verified", "skip_source_verified"):
                    for missing in (True, False):
                        altered=copy.deepcopy(record)
                        if missing:
                            del altered["sides"][side][field]
                        else:
                            altered["sides"][side][field]=False
                        # Same JSON deserialization path; original evidence stays intact.
                        altered=json.loads(json.dumps(altered))
                        proof=proof_from_record(altered, True)
                        self.assertTrue(all(classify(r["decl_file"], [], proof)["conclusion"] is None
                                            for r in related), (obj, side, field, missing))

if __name__=="__main__":
    unittest.main(verbosity=2)
