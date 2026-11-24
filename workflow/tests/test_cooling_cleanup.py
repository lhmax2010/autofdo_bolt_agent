"""Synthetic cooling and cleanup tests, with immutable attempt-09 stop evidence."""
import json,os,shutil,subprocess,tempfile,unittest
from pathlib import Path
from afdo_wf.transport import SDB
from afdo_wf.receipts import Cleanup
from afdo_wf.common import GateError,require,sha256
from afdo_wf.stats import telemetry

class CoolingTests(unittest.TestCase):
 def gate(self,temperature):
  with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as tmp:
   d=Path(tmp);shutil.copyfile(Path(__file__).parents[1]/'board/start_gate.sh',d/'start_gate.sh')
   (d/'common.sh').write_text('safe_path() { :; }\nstep_log() { exec >"$1" 2>&1; }\n')
   (d/'cap').write_text('temperature\t/sys/synthetic/temp\n')
   (d/'cat').write_text('#!/bin/bash\nprintf "%s\\n" "'+str(temperature)+'"\n')
   (d/'sleep').write_text('#!/bin/bash\nexit 0\n')
   for n in ['cat','sleep']:(d/n).chmod(0o755)
   r=subprocess.run(['bash',d/'start_gate.sh',d/'cap',d/'gate.log'],capture_output=True,env={**os.environ,'PATH':str(d)+':'+os.environ['PATH']},timeout=10)
   return r.returncode,(d/'gate.log').read_text().splitlines()
 def test_cooling_target_boundary_58(self):
  rc,lines=self.gate(58000);self.assertEqual(rc,0);self.assertEqual(len(lines),1)
 def test_cooling_target_timeout_unchanged_600_seconds(self):
  rc,lines=self.gate(59000);self.assertEqual(rc,3);self.assertEqual(len(lines),21)
 def test_cooling_margin_does_not_change_design_verdict(self):
  def classify(t):return telemetry([dict(time=x,temperature={'t':t}) for x in [0,1,2,3]],1,2,1500000,{'temperature':['t']})['classification']
  self.assertEqual(classify(59),'clean');self.assertEqual(classify(60),'clean');self.assertEqual(classify(60.374),'telemetry_anomaly');self.assertEqual(classify(80),'telemetry_anomaly')

class FakeSDB(SDB):
 def __init__(self,d):
  super().__init__('synthetic',d/'transport');self.uid=False;self.calls=[];self.present=True;self.digest='';self.link='lib.so.1';self.raw_sha=None
 def identity(self):return {'board':'synthetic'}
 def root_state(self):return self.uid
 def root(self,on):self.calls.append(('root',on));self.uid=on
 def shell(self,cmd,readonly=False,timeout=900):
  self.calls.append(('shell',cmd))
  if cmd.startswith('if test -e '):return 'yes' if self.present else 'no'
  require(self.uid,'Permission denied (synthetic attempt-09)')
  if 'find . -mindepth' in cmd:return 'd\tusr\nd\tusr/lib\nf\tusr/lib/lib.so.1\nl\tusr/lib/lib.so\n'
  if cmd.startswith('readlink '):return self.link
  if cmd.startswith('sha256sum '):return self.raw_sha if self.raw_sha is not None else self.digest+'  /opt/afdo_agent/variants/synthetic/usr/lib/lib.so.1'
  if cmd.startswith('rm -rf -- '):self.present=False;return ''
  raise AssertionError(cmd)

class CleanupTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']);self.d=Path(self.tmp.name);self.t=FakeSDB(self.d)
  source=self.d/'lib.so.1';source.write_bytes(b'synthetic library');self.t.digest=sha256(source)
  self.c=Cleanup(self.d/'cleanup.json',self.t.identity())
  self.c.register(dict(kind='host_artifact',remote='/opt/afdo_agent/variants/synthetic',directory=True,verification=str(self.d/'verify.json'),members={
   'usr/lib/lib.so.1':dict(kind='file',source=str(source),sha256=sha256(source)),
   'usr/lib/lib.so':dict(kind='link',target='lib.so.1')}))
 def tearDown(self):self.tmp.cleanup()
 def test_attempt09_root_off_legacy_fails_new_cleanup_passes(self):
  raw=json.loads((Path(__file__).parent/'fixtures/attempt09-cleanup-stop.json').read_text())
  self.assertEqual(raw['uid'],'5001');self.assertTrue(any('Permission denied' in e for e in raw['errors']));self.assertIn('list index out of range',raw['errors'])
  self.assertTrue(self.c.restore(self.t.identity(),self.t.undo));self.assertTrue(self.c.data['cleanup_pending'])
  self.assertEqual(self.t.restore_cleanup(self.c),[]);self.assertFalse(self.c.data['cleanup_pending']);self.assertFalse(self.t.uid);self.assertFalse(self.t.present)
  self.assertEqual([x for x in self.t.calls if x[0]=='root'],[('root',True),('root',False)])
  self.assertTrue(list((self.d/'cleanup-sessions').glob('*.json')))
 def test_link_is_verified_without_following(self):
  self.assertEqual(self.t.restore_cleanup(self.c),[])
  sha_calls=[x[1] for x in self.t.calls if x[0]=='shell' and x[1].startswith('sha256sum')]
  self.assertEqual(len(sha_calls),1);self.assertTrue(sha_calls[0].endswith('lib.so.1'))
 def test_changed_link_keeps_pending_restores_root(self):
  self.t.link='wrong-target';self.assertTrue(self.t.restore_cleanup(self.c));self.assertTrue(self.t.present);self.assertFalse(self.t.uid);self.assertTrue(self.c.data['cleanup_pending'])
 def test_empty_sha_is_explicit_failure_not_index_error(self):
  self.t.raw_sha='';errors=self.t.restore_cleanup(self.c)
  self.assertTrue(any('missing or malformed deployment SHA' in e for e in errors));self.assertFalse(any('list index' in e for e in errors));self.assertFalse(self.t.uid);self.assertTrue(self.t.present)
 def test_existing_root_on_is_not_switched_off(self):
  self.t.uid=True;self.assertEqual(self.t.restore_cleanup(self.c),[]);self.assertTrue(self.t.uid);self.assertFalse([x for x in self.t.calls if x[0]=='root'])
 def test_restore_root_failure_not_retried(self):
  original=self.t.root
  def root(on):
   if not on:self.t.calls.append(('root-failed',False));raise GateError('synthetic root off failure')
   original(on)
  self.t.root=root;self.assertTrue(self.t.restore_cleanup(self.c));self.assertEqual(self.t.calls.count(('root-failed',False)),1);self.assertTrue(self.c.data['cleanup_pending'])

class TemporaryIdentityTests(unittest.TestCase):
 def test_new_attempt_has_new_temporary_id(self):
  from afdo_wf.live import temporary_experiment_id
  with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as tmp:
   a=Path(tmp)/'attempt-09/measure/001/check';b=Path(tmp)/'attempt-10/measure/001/check'
   # Old fixed suffix collides despite new job/output. New identity does not.
   old=lambda p:'m1-telemetry-check'
   self.assertEqual(old(a),old(b))
   self.assertNotEqual(temporary_experiment_id('m1','telemetry-check',a),temporary_experiment_id('m1','telemetry-check',b))
   self.assertEqual(temporary_experiment_id('m1','telemetry-check',b),temporary_experiment_id('m1','telemetry-check',b))
 def test_temporary_purpose_and_stage_attempt_separate(self):
  from afdo_wf.live import temporary_experiment_id
  with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as tmp:
   a=Path(tmp)/'001';b=Path(tmp)/'002'
   ids={temporary_experiment_id('m1',kind,p) for kind in ['cleanup-test','telemetry-check'] for p in [a,b]}
   self.assertEqual(len(ids),4)
