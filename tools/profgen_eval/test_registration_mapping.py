"""Synthetic Q.5 #5 fixtures; no collected profile input or quality metric."""
import copy
import json
import unittest
import tempfile
import contextlib
import io
from pathlib import Path
from unittest.mock import patch
from run_scoped import WORK
from registration_mapping_checks import (
    compare_relations, classify_entry, classify_synthetic_run, frozen_sha,
    validate_correspondence, whole_group_unavailable, previous_instruction,
    line_has_ambiguous_key)
from registration_address_check import independent_key


def key(name='f.__uniq.1', line=2, disc=0):
    return [[name, line, disc]]


def enc(k):
    return json.dumps(k, separators=(',', ':'))


def relation(address=100, k=None, source=None):
    return dict(group='f', address=address, key=k or key(),
                source=source or ['a.c', 12, 0], excluded=None)


def frame(name='f.__uniq.1', line=12, start=10, disc=0):
    return dict(FunctionName=name, Line=line, StartLine=start, Discriminator=disc)


def actual_selection(categories, fnda):
    """Exercise the existing static selection entry point on synthetic DIEs."""
    import static_gate_data as gate
    inventory={};bridge={};checks={}
    for i,category in enumerate(categories,1):
        name='f.__uniq.1' if i==1 else 'inline'
        inventory[i]=dict(raw_name=name,decl_file='a.c',decl_line='10',category=category,
                          conclusion=category)
        bridge[i]=dict(name=name,decl_file='a.c',decl_line=10,top_die=1)
        checks[i]=dict(candidate_ids=[i-1])
    refs=[dict(fnda=n) for n in fnda]
    with tempfile.TemporaryDirectory(dir=WORK/'temp/tmp') as directory:
        root=Path(directory);reference=root/'reference.lcov';reference.write_text('synthetic')
        (root/'synthetic-inventory.jsonl').write_text('synthetic')
        with patch.object(gate,'data',return_value=(refs,{}, {},inventory,checks,reference)), \
             patch.object(gate,'bridge_inventory',return_value=bridge), \
             patch.object(gate,'OUT',root),patch.object(gate,'TEMP',root), \
             contextlib.redirect_stdout(io.StringIO()):
            gate.select('synthetic')
        return json.loads((root/'synthetic-selected-groups.json').read_text())


class Relations(unittest.TestCase):
    def setUp(self):
        self.reference=[relation(), relation(102), relation(104,key(line=3),['a.c',13,0])]
    def test_missing_cold_address(self):
        self.assertEqual(len(compare_relations(self.reference,self.reference[:-1])),1)
    def test_delete_collision_unchanged_key_set(self):
        altered=self.reference[1:]
        self.assertEqual({enc(r['key']) for r in self.reference},{enc(r['key']) for r in altered})
        self.assertEqual(len(compare_relations(self.reference,altered)),1)
    def test_swap_key_values(self):
        altered=copy.deepcopy(self.reference)
        altered[0]['source'],altered[2]['source']=altered[2]['source'],altered[0]['source']
        self.assertEqual(len(compare_relations(self.reference,altered)),2)
    def test_prev_inst_wrong_by_one(self):
        instructions=[dict(address=100,size=2,range=0),dict(address=102,size=4,range=0),dict(address=106,size=2,range=0)]
        p=previous_instruction(106,instructions);self.assertEqual(p,102)
        self.assertTrue(compare_relations([relation(106,key(line=p))],[relation(106,key(line=p+1))]))
    def test_prev_inst_range_and_data_not_crossed(self):
        xs=[dict(address=100,size=2,range=0),dict(address=104,size=2,range=0),dict(address=106,size=2,range=1)]
        self.assertEqual(previous_instruction(104,xs),104)
        self.assertEqual(previous_instruction(106,xs),106)
    def test_same_key_distinct_source(self):
        self.assertTrue(line_has_ambiguous_key([[('a.c',12),('b.c',12)]]))
    def test_same_key_same_source(self):
        self.assertFalse(line_has_ambiguous_key([[('a.c',12),('a.c',12)]]))
    def test_raw_discriminators_same_written_key(self):
        self.assertNotEqual(2,130)
        self.assertEqual(independent_key([frame(disc=2)]),independent_key([frame(disc=130)]))
    def test_thumb_alias_query_preserves_sample_address(self):
        raw=relation(100);query={100:101}
        actual=relation(100,independent_key([frame()]))
        self.assertEqual(query[100],101);self.assertEqual(compare_relations([raw],[actual]),[])
    def test_nonleaf_zero_excluded(self):
        self.assertIsNone(independent_key([frame(),frame(name='outer',line=0)]))
    def test_leaf_zero_excluded(self):
        self.assertIsNone(independent_key([frame(line=0)]))
    def test_offset_collision(self):
        self.assertEqual(independent_key([frame(line=12)]),independent_key([frame(line=65548)]))
        self.assertTrue(compare_relations([relation(source=['a.c',12,0])],[relation(source=['a.c',65548,0])]))
    def test_distinct_build_paths_cannot_silently_compare_equal(self):
        self.assertTrue(compare_relations([relation(source=['/buildA/a.c',12,0])],[relation(source=['/buildB/a.c',12,0])]))
    def test_ambiguous_and_normal_key_same_line(self):
        self.assertTrue(line_has_ambiguous_key([[('a.c',12)],[('a.c',12),('b.c',20)]]))


class Classification(unittest.TestCase):
    def setUp(self):
        self.names={'f.__uniq.1','f','g','inline','header','macro'}
        self.groups={'f.__uniq.1':'mapping_range','f':'known_out_of_scope','g':'mapping_range'}
        self.mapping={enc(key()):dict(status='reference_executed',in_U=True)}
        self.static=dict(names=sorted(self.names),groups=self.groups,mapping=self.mapping,
                         exclusions=['x'],U=['a.c:12'],weights={'a.c:12':3})
    def classify(self,k,**kw):
        return classify_entry(k,self.names,self.groups,self.mapping,**kw)
    def run_entries(self,entries,**kw):
        return classify_synthetic_run(entries,self.names,self.groups,self.mapping,**kw)
    def test_known_outside_group(self):
        self.assertEqual(self.classify(key('f')),('out_of_scope','known_out_of_scope'))
    def test_unknown_name(self):
        self.assertEqual(self.classify(key('unknown')),('unaligned','unknown_name'))
    def test_name_closure_all_inline_frames(self):
        self.assertEqual(self.classify(key()+key('not-in-ELF')),('unaligned','unknown_name'))
    def test_stripped_unique_suffix_even_if_outside_name_exists(self):
        self.assertEqual(self.classify(key(),effective_key=key('f')),('unaligned','raw_key_changed'))
    def test_two_translation_units_one_executed(self):
        self.names.add('f.__uniq.2');self.groups['f.__uniq.2']='known_out_of_scope'
        self.assertEqual(self.classify(key())[0],'in_U')
        self.assertEqual(self.classify(key('f.__uniq.2'))[0],'out_of_scope')
    def test_tiny_unaligned_count_still_undefined(self):
        self.assertFalse(self.run_entries([(key(),10**9),(key(line=999),1)])['defined'])
    def test_boundary_exclusion_not_undefined(self):
        r=self.run_entries([(key(),4)],unavailable={'f.__uniq.1'})
        self.assertTrue(r['defined']);self.assertEqual(r['entries'][0][0],'boundary_unavailable')
    def test_boundary_whole_same_name_group(self):
        self.assertTrue(whole_group_unavailable([{'boundary_available':True},{'boundary_available':False}]))
        self.assertEqual(self.classify(key(),unavailable={'f.__uniq.1'})[0],'boundary_unavailable')
    def test_excluded_parent_with_hot_inline(self):
        k=key()+key('inline')
        self.mapping[enc(k)]=dict(status='reference_executed',in_U=True)
        self.assertEqual(self.classify(k,unavailable={'f.__uniq.1'})[0],'boundary_unavailable')
    def test_small_FNDA_large_loop_DA_not_filter(self):
        ref={'FNDA':1,'DA':10**9};self.assertLess(ref['FNDA'],ref['DA'])
        self.assertEqual(actual_selection(['reference_executed'],[ref['FNDA']]),['f.__uniq.1'])
        self.assertEqual(self.classify(key())[0],'in_U')
    def test_only_ambiguous_candidate_group_kept(self):
        self.assertEqual(actual_selection(['identity_ambiguous'],[1]),['f.__uniq.1'])
        self.mapping[enc(key())]=dict(status='identity_ambiguous',in_U=False)
        self.assertEqual(self.classify(key()),('aligned_outside_U','identity_ambiguous'))
    def test_hot_parent_normal_and_ambiguous_inline(self):
        self.assertEqual(actual_selection(['reference_executed','identity_ambiguous'],[20,1]),['f.__uniq.1'])
        k=key()+key('inline');self.mapping[enc(k)]=dict(status='identity_ambiguous')
        self.assertEqual([self.classify(x)[0] for x in [key(),k]],['in_U','aligned_outside_U'])
    def test_nonexistent_key_in_ambiguous_group(self):
        self.mapping[enc(key())]=dict(status='identity_ambiguous')
        self.assertEqual(self.classify(key(line=999)),('unaligned','unmapped_key'))
    def test_pending_registration_fails(self):
        with self.assertRaisesRegex(ValueError,'reference_unresolved'):validate_correspondence(['reference_executed','pending'])
    def test_pending_not_downgraded_at_runtime(self):
        self.groups['f.__uniq.1']='pending'
        self.assertEqual(self.classify(key()),('unaligned','reference_unresolved'))
    def test_zero_fill_not_quality_input(self):
        with self.assertRaisesRegex(ValueError,'zero_fill'):self.run_entries([(key(),0)],zero_fill='sampled-functions')
    def test_system_header_in_mapping_group(self):
        self.mapping[enc(key())]=dict(status='system_header_no_reference')
        self.assertEqual(self.classify(key()),('aligned_outside_U','system_header_no_reference'))
    def test_executed_macro_in_mapping_group(self):
        self.mapping[enc(key())]=dict(status='macro_generated_function')
        self.assertEqual(self.classify(key()),('aligned_outside_U','macro_generated_function'))
    def test_special_status_does_not_bypass_key_check(self):
        for status in ['macro_generated_function','system_header_no_reference','identity_ambiguous']:
            self.mapping[enc(key())]=dict(status=status)
            self.assertEqual(self.classify(key(line=999)),('unaligned','unmapped_key'))
    def test_special_only_group_is_known_outside(self):
        self.mapping[enc(key('f'))]=dict(status='system_header_no_reference')
        self.assertEqual(self.classify(key('f'))[0],'out_of_scope')
    def test_different_hit_functions_static_sha_unchanged(self):
        before=frozen_sha(self.static)
        self.run_entries([(key(),3)]);self.run_entries([(key('g'),5)])
        self.assertEqual(frozen_sha(self.static),before)
    def test_drop_all_hot_entries_static_sha_unchanged(self):
        before=frozen_sha(self.static)
        self.run_entries([(key(),10**9)]);self.run_entries([])
        self.assertEqual(frozen_sha(self.static),before)
    def test_add_explicit_zero_static_sha_unchanged(self):
        before=frozen_sha(self.static)
        result=self.run_entries([(key(),0)])
        self.assertEqual(result['entries'],[('in_U','in_U')]);self.assertEqual(frozen_sha(self.static),before)
    def test_budget_static_sha_unchanged(self):
        before=frozen_sha(self.static)
        for n in [1,20000,400000]:self.run_entries([(key(),n)])
        self.assertEqual(frozen_sha(self.static),before)


if __name__=='__main__':unittest.main()
