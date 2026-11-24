"""Synthetic foreground/cleanup acceptance; no board access."""
import json,os,signal,subprocess,tempfile,time,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from afdo_wf.live import foreground_script,Experiment,TechnicalFailure,paired_block
from afdo_wf.receipts import Cleanup
from afdo_wf.transport import SDB
from afdo_wf.common import GateError,sha256

class ForegroundTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']);self.d=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def script(self,cmd):
  f=self.d/'launch.sh';f.write_text(foreground_script(str(self.d),cmd));return f
 def test_foreground_success_blocks_and_records(self):
  start=time.monotonic();r=subprocess.run(['bash',self.script(['bash','-c','sleep .1'])]);self.assertEqual(r.returncode,0)
  self.assertGreaterEqual(time.monotonic()-start,.1);self.assertEqual((self.d/'exit').read_text(),'0\n')
 def test_nonzero_load_status_recorded(self):
  r=subprocess.run(['bash',self.script(['bash','-c','exit 17'])]);self.assertEqual(r.returncode,17);self.assertEqual((self.d/'exit').read_text(),'17\n')
 def test_sampler_stopped_on_script_exception(self):
  load=self.d/'load.sh';pid=self.d/'sampler';stopped=self.d/'stopped'
  load.write_text('sleep 60 & p=$!\necho "$p" > '+str(pid)+'\ntrap \'kill "$p"; wait "$p" 2>/dev/null; echo yes > '+str(stopped)+"' EXIT\nexit 7\n")
  r=subprocess.run(['bash',self.script(['bash',str(load)])]);self.assertEqual(r.returncode,7);self.assertTrue(stopped.exists())
  with self.assertRaises(ProcessLookupError):os.kill(int(pid.read_text()),0)
 def test_interrupt_stops_owned_sampler(self):
  load=self.d/'load.sh';ready=self.d/'ready';stopped=self.d/'stopped'
  load.write_text('sleep 60 & p=$!\ntrap \'kill "$p" 2>/dev/null; wait "$p" 2>/dev/null; echo yes > '+str(stopped)+'\' EXIT\ntrap "exit 143" TERM\necho yes > '+str(ready)+'\nwait "$p"\n')
  child=subprocess.Popen(['bash',self.script(['bash',str(load)])])
  try:
   deadline=time.monotonic()+5
   while not ready.exists() and time.monotonic()<deadline:time.sleep(.01)
   self.assertTrue(ready.exists());child.terminate();self.assertEqual(child.wait(5),143);self.assertTrue(stopped.exists())
  finally:
   if child.poll() is None:child.kill();child.wait()
 def experiment(self):
  e=object.__new__(Experiment);e.d=self.d;e.remote='/opt/afdo_agent/work/synthetic';e.scripts='/opt/afdo_agent/tools/synthetic';e.job={};e.cleanup=Cleanup(self.d/'cleanup',{})
  t=Mock();t.wait_hook=None;t.shell.side_effect=lambda c,*a,**kw:'1000000' if c.startswith('df ') else '0' if c.startswith('cat ') else ''
  e.transport=t;return e
 def test_launch_foreground_and_timeout_budget(self):
  e=self.experiment();e.launch('one',['bash','synthetic'],self.d,timeout=30)
  calls=[c for c in e.transport.shell.call_args_list if c.kwargs.get('timeout')]
  self.assertEqual(len(calls),1);self.assertEqual(calls[0].kwargs['timeout'],150)
  self.assertTrue(calls[0].args[0].startswith('bash '));self.assertNotIn(' & ',calls[0].args[0])
 def test_timeout_preserves_pending_process_and_data(self):
  e=self.experiment();old=e.transport.shell.side_effect
  def run(c,*a,**kw):
   if kw.get('timeout'):raise subprocess.TimeoutExpired('sdb',150)
   return old(c,*a,**kw)
  e.transport.shell.side_effect=run
  with self.assertRaises(TechnicalFailure):e.launch('one',['false'],self.d,timeout=30)
  self.assertTrue(any(a['kind']=='process' for a in e.cleanup.data['cleanup_pending']))
 def test_transport_interruption_preserves_pending(self):
  e=self.experiment();old=e.transport.shell.side_effect
  def run(c,*a,**kw):
   if kw.get('timeout'):raise GateError('missing exit marker')
   return old(c,*a,**kw)
  e.transport.shell.side_effect=run
  with self.assertRaises(TechnicalFailure):e.launch('one',['false'],self.d)
  self.assertEqual(len(e.cleanup.data['cleanup_pending']),3)
 def test_whole_block_retry_not_single_round(self):
  calls=[];fail=[]
  def run(label,attempt):
   calls.append((label,attempt))
   if label=='AFDO' and attempt==0:raise TechnicalFailure('synthetic disconnect')
   return label
  self.assertEqual(paired_block(['BASE','AFDO'],run,lambda *a:fail.append(a)),dict(BASE='BASE',AFDO='AFDO'))
  self.assertEqual(calls,[('BASE',0),('AFDO',0),('BASE',1),('AFDO',1)]);self.assertEqual(len(fail),1)
 def test_no_third_attempt_or_correctness_retry(self):
  failures=[]
  with self.assertRaises(TechnicalFailure):paired_block(['BASE'],lambda *a:(_ for _ in ()).throw(TechnicalFailure('timeout')),lambda *a:failures.append(a))
  self.assertEqual(len(failures),2)
  failures=[]
  with self.assertRaises(GateError):paired_block(['BASE'],lambda *a:(_ for _ in ()).throw(GateError('oracle')),lambda *a:failures.append(a))
  self.assertEqual(failures,[])
 def test_deploy_tar_registered_before_failed_push(self):
  e=self.experiment();f=self.d/'BASE.tar';f.write_text('synthetic tar')
  def fail(*a):
   self.assertEqual(e.cleanup.data['cleanup_pending'][0]['remote'],e.remote+'/BASE.tar');raise GateError('partial push')
  e.transport.push.side_effect=fail
  with self.assertRaises(GateError):e.push_owned(f,e.remote+'/BASE.tar')
  self.assertEqual(e.cleanup.data['cleanup_pending'][0]['members']['']['sha256'],sha256(f))
 def test_host_delete_requires_unchanged_original_and_board(self):
  e=self.experiment();f=self.d/'tar';f.write_text('synthetic');a=e.host_artifact(e.remote+'/BASE.tar',{'':dict(kind='file',source=str(f),sha256=sha256(f))})
  t=object.__new__(SDB);calls=[]
  def shell(cmd,readonly=False):
   calls.append(cmd)
   if cmd.startswith('if '):return 'yes'
   if cmd.startswith('sha256sum'):return '0'*64+'  file'
   return ''
  t.shell=shell
  with self.assertRaises(GateError):t.undo(a)
  self.assertFalse(any(c.startswith('rm ') for c in calls))
  t.shell=lambda c,readonly=False: 'yes' if c.startswith('if ') else sha256(f)+' file' if c.startswith('sha256sum') else calls.append(c) or ''
  t.undo(a);self.assertTrue(any(c.startswith('rm -rf -- /opt/afdo_agent/work/synthetic/BASE.tar') for c in calls))
 def test_partial_directory_only_verified_members_removed(self):
  e=self.experiment();f=self.d/'lib';f.write_text('synthetic')
  a=e.host_artifact('/opt/afdo_agent/variants/synthetic',{'lib':dict(kind='file',source=str(f),sha256=sha256(f))},True)
  t=object.__new__(SDB);calls=[]
  def shell(cmd,readonly=False):
   calls.append(cmd)
   if cmd.startswith('if '):return 'yes'
   if cmd.startswith('cd '):return 'f\tunexpected\n'
   return ''
  t.shell=shell
  with self.assertRaises(GateError):t.undo(a)
  self.assertFalse(any(c.startswith('rm ') for c in calls))
 def test_host_registration_rejects_preexisting_unowned_path(self):
  e=self.experiment();e.transport.shell.side_effect=GateError('already exists')
  with self.assertRaises(GateError):e.host_artifact('/opt/afdo_agent/variants/other',{},True)
  self.assertEqual(e.cleanup.data['cleanup_pending'],[])
 def test_host_missing_after_partial_creation_is_noop(self):
  t=object.__new__(SDB);t.shell=Mock(return_value='no')
  t.undo(dict(kind='host_artifact',remote='/opt/afdo_agent/work/synthetic/BASE.tar',members={},directory=False))
  self.assertEqual(t.shell.call_count,1)
 def test_real_compact_caps_old_failure_new_pass(self):
  import re
  from afdo_wf.live import check_caps
  raw=(Path(__file__).parent/'fixtures/rpi4-oracle-caps.txt').read_text().strip()
  compact='I420,1280x720,30/1,progressive,1/1'
  self.assertIsNone(re.search(r'format=\([^)]*\)([^,; ]+)',compact))
  self.assertTrue(check_caps(compact,raw))
  for wrong in [compact.replace('I420','NV12'),compact.replace('30/1','24/1'),compact.replace('progressive','interleaved'),compact.replace('1/1','2/1')]:
   with self.subTest(wrong=wrong),self.assertRaises(GateError):check_caps(wrong,raw)
 def test_real_capability_blank_line_old_failure_new_pass(self):
  from afdo_wf.live import capability_text
  raw=(Path(__file__).parent/'fixtures/rpi4-capabilities-double-newline.tsv').read_text()
  self.assertEqual(raw.splitlines()[-1],'')
  fixed=capability_text(raw)
  self.assertTrue(all(line for line in fixed.splitlines()))
  self.assertEqual([x for x in raw.splitlines() if x],fixed.splitlines())
