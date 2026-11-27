"""Checks for a replacement profile runtime scoped to PGOGEN."""
import unittest

from afdo_wf import pgo, pgo_frozen
from afdo_wf.common import GateError


class FrozenRuntime(unittest.TestCase):
    split={'common':{'repo_id':'original','frozen_packages':['base']},
           'pgogen':{'repo_id':'instrumented'},
           'runtime':{'evr':'22.1.8-1.6','installed_record':'runtime'}}

    def test_only_pgogen_gets_a_runtime_release(self):
        unit={'macros':{},'consume_macro':{'with_autofdo':'1'}}
        for name in (*pgo.VARIANTS,'BASE-r'):
            macros=pgo.macros(name,unit,{'afdo_diag':'1'},self.split)
            self.assertNotIn('with_pgo_deps',macros)
            self.assertEqual(macros.get('pgo_runtime_evr'),'22.1.8-1.6' if name=='PGOGEN' else None)

    def test_only_the_declared_installed_delta_is_normalized(self):
        base={'frozen_repo_id':'original','packages':['base']}
        candidate={'frozen_repo_id':'instrumented','packages':['runtime','base'],
                   'macros':{'with_pgogen':'1','pgo_runtime_evr':'22.1.8-1.6'}}
        self.assertEqual(pgo_frozen.pgogen_lock(base,candidate,self.split),
                         dict(base,macros={'with_pgogen':'1'}))
        candidate['packages'].append('extra')
        with self.assertRaisesRegex(GateError,'exceeds the approved'):
            pgo_frozen.pgogen_lock(base,candidate,self.split)

    def test_wrong_instrumented_repository_is_rejected(self):
        base={'frozen_repo_id':'original','packages':['base']}
        candidate={'frozen_repo_id':'unapproved','packages':['runtime','base'],'macros':{}}
        with self.assertRaisesRegex(GateError,'repository lock mismatch'):
            pgo_frozen.pgogen_lock(base,candidate,self.split)

    def test_only_the_new_exact_atexit_record_is_attributed(self):
        original=['GNU','original']
        exact=['GNU','known atexit object']
        unknown=['GNU','extra object']
        base={'commands':{'lib':[['clang'],original]}}
        generation={'commands':{'lib':[['clang'],original,exact,unknown]}}
        filtered,removed=pgo_frozen.linked_atexit_lock(base,generation,[original,exact])
        self.assertEqual(removed,{'lib':[exact]})
        self.assertEqual(filtered['commands']['lib'],[['clang'],original,unknown])
        self.assertIn(exact,generation['commands']['lib'])
