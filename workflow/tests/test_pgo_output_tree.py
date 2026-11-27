"""The measurement receipt streams raw outputs while leaving legacy receipts intact."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from afdo_wf import scheduler
from afdo_wf.common import GateError, sha256
from afdo_wf.receipts import Store


class PGOOutputTree(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.run = Path(temp.name)
        self.store = Store(self.run/'receipts')
        for stage in ('preflight', 'build', 'deploy', 'collect', 'convert', 'rebuild'):
            self.store.complete(stage, [], [])

    def test_pgo_measurement_binds_each_output_in_a_streamed_manifest(self):
        def measure(out, store):
            (out/'all-plans-lock.json').write_text('locked')
            (out/'raw').mkdir()
            for i in range(10):
                (out/'raw'/f'{i}.txt').write_text(str(i))
            return dict(pgo_evidence={'test': 'synthetic'})
        scheduler.execute(['measure'], {'measure': measure}, self.run/'stages', self.store.directory, [])
        receipt = self.store.verify('measure')
        tree = receipt['output_tree']
        self.assertEqual(tree['file_count'], 12)
        self.assertEqual(receipt['outputs'][tree['manifest']], sha256(tree['manifest']))
        damaged = Path(tree['root'])/'raw/3.txt'
        self.assertNotIn(str(damaged), receipt['outputs'])
        damaged.write_text('changed')
        with self.assertRaisesRegex(GateError, 'raw/3.txt'):
            self.store.verify('measure')
        damaged.write_text('3')
        Path(tree['manifest']).write_text('[]\n')
        with self.assertRaisesRegex(GateError, 'outputs-.*jsonl'):
            self.store.verify('measure')
