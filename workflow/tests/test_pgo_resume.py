from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from afdo_wf import job_commands, pgo, pgo_resume
from afdo_wf.common import GateError,save,sha256
from afdo_wf.receipts import Store


class PGOResume(unittest.TestCase):
    def setUp(self):
        directory=TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root=Path(directory.name)
        self.job=self.root/'historical.json'
        self.input=self.root/'trained'
        self.input.write_text('sealed')
        old=dict(method='pgo',host=dict(shared_host_recovery=True,recovery_io_pressure_waived=True),
                 media={'training':'unchanged'},output=str(self.root/'run'))
        save(self.job,old)
        self.store=Store(self.root/'receipts')
        for step in ('preflight','build','deploy','collect'):
            self.store.complete(step,[self.job,self.input],[])
        self.next=deepcopy(old)
        self.next['host'].pop('recovery_io_pressure_waived')
        self.next['pgo_collision_policy']=pgo.ZERO_DSO_POLICY
        self.next['pgo_resume_after_collect']=dict(job=str(self.job),receipt_sha256=sha256(self.store.path('collect')))

    def test_resume_original_inputs_with_retired_waiver(self):
        pgo_resume.after_collect(self.next,self.store,self.root)

    def test_changed_media_is_rejected(self):
        self.next['media']['training']='changed'
        with self.assertRaisesRegex(GateError,'changed a locked input'):
            pgo_resume.after_collect(self.next,self.store,self.root)

    def test_changed_historical_content_is_rejected(self):
        self.input.write_text('changed')
        with self.assertRaisesRegex(GateError,'content changed'):
            pgo_resume.after_collect(self.next,self.store,self.root)

    def test_waiver_cannot_be_carried_forward(self):
        self.next['host']['recovery_io_pressure_waived']=True
        with self.assertRaisesRegex(GateError,'changed a locked input'):
            pgo_resume.after_collect(self.next,self.store,self.root)

    def test_platform_relocation_must_keep_exact_content(self):
        actual = self.root/'original-platform.toml'
        actual.write_text('platform settings')
        moved = self.root/'continuation-platform.toml'
        moved.write_bytes(actual.read_bytes())
        self.next.update(platform='example', config_sha256={
            'platform':dict(path=str(actual),sha256=sha256(actual))})
        with patch.object(job_commands.platforms,'profile_path',return_value=moved):
            job_commands.validate_locks(self.next)
            moved.write_text('different platform settings')
            with self.assertRaisesRegex(GateError,'initialized configuration changed'):
                job_commands.validate_locks(self.next)

    def test_resume_s5_with_new_seeds_only(self):
        original=self.root/'converted-job.json'
        save(original,self.next)
        self.store.complete('convert',[original],[])
        self.store.complete('rebuild',[original],[],dict(consumption={'passed':True}))
        measure=dict(self.next,order_seed=2026112740,bootstrap_seed=2026112750,
                     pgo_resume_after_rebuild=dict(job=str(original),receipt_sha256=sha256(self.store.path('rebuild'))))
        pgo_resume.after_rebuild(measure,self.store,self.root)
        measure['serial']='wrong board'
        with self.assertRaisesRegex(GateError,'changed a locked input'):
            pgo_resume.after_rebuild(measure,self.store,self.root)
