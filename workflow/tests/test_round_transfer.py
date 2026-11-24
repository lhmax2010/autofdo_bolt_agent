"""Synthetic transport/cleanup and immutable attempt-08 telemetry regression."""
import io,json,os,shutil,subprocess,tarfile,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
from afdo_wf.common import TechnicalFailure,GateError,sha256,save
from afdo_wf.transport import SDB,extract_verified
from afdo_wf.live import paired_block,preserve_partial
from afdo_wf.receipts import Cleanup,verified_pull
from afdo_wf.stats import parse_telemetry_tsv,telemetry

class TransferTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']);self.d=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def test_signal_pull_whole_block_retry_and_preservation(self):
  calls=[];partial=self.d/'round-try0-AFDO';partial.mkdir();(partial/'bytes').write_bytes(b'partial')
  t=SDB('synthetic',self.d/'logs',runner=lambda *a,**kw:subprocess.CompletedProcess(a,-13,b'partial',b''))
  def run(label,attempt):
   calls.append((label,attempt))
   if label=='AFDO' and not attempt:t.invoke(['pull','remote','local'])
   return label
  def failed(n,pair,e):preserve_partial(self.d,'round-try0-',self.d/'failed-attempt-0')
  with t.technical_operations():self.assertEqual(paired_block(['BASE','AFDO'],run,failed),{'BASE':'BASE','AFDO':'AFDO'})
  self.assertEqual(calls,[('BASE',0),('AFDO',0),('BASE',1),('AFDO',1)])
  self.assertEqual((self.d/'failed-attempt-0/round-try0-AFDO/bytes').read_bytes(),b'partial')
  self.assertEqual(json.loads((self.d/'logs/000001.json').read_text())['exit_code'],-13)
 def test_second_failure_stops(self):
  count=[]
  def run(*args):count.append(args);raise TechnicalFailure('synthetic SIGPIPE')
  with self.assertRaises(TechnicalFailure):paired_block(['BASE','AFDO'],run,lambda *a:None)
  self.assertEqual(count,[('BASE',0),('BASE',1)])
 def test_transport_push_shell_nonzero(self):
  for cmd in ['push','shell']:
   with self.subTest(cmd=cmd):
    t=SDB('synthetic',self.d/cmd,runner=lambda *a,**kw:subprocess.CompletedProcess(a,1,b'',b'error'))
    with t.technical_operations(),self.assertRaises(TechnicalFailure):t.invoke([cmd,'x'])
 def test_transport_timeout(self):
  def fail(*a,**kw):raise subprocess.TimeoutExpired(a,1,output=b'partial')
  t=SDB('synthetic',self.d/'timeout',runner=fail)
  with t.technical_operations(),self.assertRaises(TechnicalFailure):t.invoke(['pull','x'])
  self.assertEqual((self.d/'timeout/000001.stdout').read_bytes(),b'partial')
 def test_remote_nonzero_and_missing_marker(self):
  for body in ['failure','\nTOKEN7\n']:
   t=SDB('synthetic',self.d/str(len(body)))
   t.invoke=lambda *a:(0,body,'')
   with t.technical_operations(),self.assertRaises(TechnicalFailure):t.shell('false',readonly=True)
   self.assertEqual(t.retries,0)
 def archive(self,items):
  p=self.d/('input-'+str(len(list(self.d.glob('input*'))))+'.tar')
  with tarfile.open(p,'w') as t:
   for name,content in items.items():
    m=tarfile.TarInfo('./'+name);m.size=len(content);t.addfile(m,io.BytesIO(content))
  return p
 def test_archive_valid(self):
  import hashlib
  p=self.archive({'a':b'one','sub/b':b'two'});manifest={k:hashlib.sha256(v).hexdigest() for k,v in {'a':b'one','sub/b':b'two'}.items()}
  extract_verified(p,self.d/'out',manifest);self.assertEqual((self.d/'out/sub/b').read_bytes(),b'two')
 def test_member_missing(self):
  p=self.archive({'a':b'one'})
  with self.assertRaises(TechnicalFailure):extract_verified(p,self.d/'out',{'a':__import__('hashlib').sha256(b'one').hexdigest(),'missing':'1'*64})
 def test_unpack_failure(self):
  p=self.d/'bad.tar';p.write_bytes(b'invalid')
  with self.assertRaises(TechnicalFailure):extract_verified(p,self.d/'out',{})
 def test_path_escape_rejected(self):
  p=self.archive({'../escape':b'x'})
  with self.assertRaises(TechnicalFailure):extract_verified(p,self.d/'out',{'../escape':'0'*64})
  self.assertFalse((self.d/'escape').exists())
 def fake_pull(self,bad=False):
  source=self.d/'bundle';source.mkdir();data=source/'payload';data.write_bytes(b'payload')
  shutil.copyfile(self.archive({'payload':b'payload'}),source/'round.tar')
  (source/'members.sha256').write_text(sha256(data)+'  ./payload\n')
  (source/'archive.sha256').write_text(('0'*64 if bad else sha256(source/'round.tar'))+'  round.tar\n'+sha256(source/'members.sha256')+'  members.sha256\n')
  t=object.__new__(SDB);t.journal=Cleanup(self.d/'cleanup.json',{});calls=[]
  def shell(command,*a,**kw):
   calls.append(command)
   return (source/'members.sha256').read_text() if command.startswith('cd ') and 'find ' in command else ''
  t.shell=shell
  def invoke(argv):shutil.copyfile(source/Path(argv[1]).name,argv[2]);return 0,'',''
  t.invoke=invoke
  return t,calls
 def test_tar_sha_mismatch_preserves_board_and_partial(self):
  t,calls=self.fake_pull(True)
  with self.assertRaises(TechnicalFailure):t.pull('/opt/afdo_agent/work/synthetic',self.d/'out',self.d/'receipt')
  self.assertFalse(any(c.startswith('rm ') for c in calls));self.assertTrue(t.journal.data['cleanup_pending'])
  self.assertEqual(len(list(self.d.glob('out.transfer-*'))),1)
 def test_tar_and_members_verified_before_delete(self):
  t,calls=self.fake_pull();r=t.pull('/opt/afdo_agent/work/synthetic',self.d/'out',self.d/'receipt')
  self.assertEqual(Path(r['local_root']),self.d/'out');self.assertTrue(json.loads((self.d/'receipt').read_text())['deleted'])
  self.assertEqual(t.journal.data['cleanup_pending'],[]);self.assertEqual(sum(c.startswith('rm ') for c in calls),2)
 def test_parent_closes_child_after_child_failure(self):
  local=self.d/'parent';(local/'child').mkdir(parents=True);(local/'child/a').write_bytes(b'a')
  parent=self.d/'parent.json';verified_pull(parent,local,{'child/a':sha256(local/'child/a')},'/opt/afdo_agent/work/parent')
  r=json.loads(parent.read_text());r['deleted']=True;save(parent,r)
  c=Cleanup(self.d/'cleanup',{});pa=dict(kind='run',remote='/opt/afdo_agent/work/parent',receipt=str(parent));ch=dict(kind='run',remote='/opt/afdo_agent/work/parent/child',receipt=str(self.d/'absent'))
  c.register(pa);c.register(ch)
  def undo(a):
   if a==ch:raise TechnicalFailure('child pull failed')
  self.assertEqual(c.restore({},undo),[]);self.assertEqual(c.data['cleanup_pending'],[])
  proof=json.loads(next((self.d/'cleanup-resolutions').glob('*.json')).read_text());self.assertEqual(proof['closed'][0]['covered_files'],1)
 def test_parent_not_deleted_does_not_close(self):
  p=self.d/'parent';save(p,dict(status='verified',deleted=False))
  c=Cleanup(self.d/'cleanup',{});c.register(dict(kind='run',remote='/opt/afdo_agent/work/x/y',receipt='missing'))
  self.assertEqual(c.reconcile_parent(p),[]);self.assertEqual(len(c.data['cleanup_pending']),1)
 def test_preserve_does_not_move_verified_directory(self):
  p=self.d/'round-ok';p.mkdir();save(Path(str(p)+'.pull.json'),dict(status='verified'))
  self.assertEqual(preserve_partial(self.d,'round-',self.d/'failed'),{});self.assertTrue(p.exists())

class TelemetryTests(unittest.TestCase):
 def test_real_old_windows_and_synthetic_handshake_counterfactual(self):
  root=Path(__file__).parent/'fixtures/attempt08-telemetry';rows=json.loads((root/'windows.json').read_text());missing={'pilot':0,'formal':0}
  for r in rows:
   samples=parse_telemetry_tsv((root/(r['name']+'.tsv')).read_text());cap={k:list(samples[0][k]) for k in ['frequency','temperature','voltage']};fixed=next(iter(samples[0]['frequency'].values()))
   old=telemetry(samples,r['start'],r['end'],fixed,cap);self.assertEqual(old['classification'],r['classification'])
   if old['classification']=='telemetry_missing':missing['pilot' if r['name'].startswith('pilot') else 'formal']+=1
   # Counterfactual schedule only; never rewrite/relabel real measurements.
   from copy import deepcopy
   synthetic=deepcopy(samples);new_start=max(r['start'],r['first']+1.1);new_end=r['end']+(new_start-r['start'])
   last=deepcopy(synthetic[-1]);last['time']=max(synthetic[-1]['time']+1,new_end+1.1);synthetic.append(last)
   self.assertNotIn('missing window edge',telemetry(synthetic,new_start,new_end,fixed,cap)['missing'])
  self.assertEqual(missing,{'pilot':6,'formal':3})
 def test_actual_shell_handshake_covers_design_window(self):
  with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as tmp:
   d=Path(tmp);board=Path(__file__).parents[1]/'board'
   for f in ['measure.sh','telemetry.sh']:shutil.copyfile(board/f,d/f)
   (d/'common.sh').write_text('safe_path() { :; }\nstep_log() { :; }\n')
   (d/'start_gate.sh').write_text('exit 0\n');(d/'watchdog.sh').write_text('sleep .2\n')
   (d/'observe_maps.sh').write_text('trap "exit 0" TERM\nwhile :; do sleep .1; done\n')
   (d/'cap').write_text('');(d/'manifest').write_text('{}')
   env=dict(os.environ,DEPLOY_MANIFEST=str(d/'manifest'));cpu=min(os.sched_getaffinity(0))
   r=subprocess.run(['bash',d/'measure.sh',d/'run','/fake/perf',str(cpu),str(cpu),d/'cap','30','true'],env=env,capture_output=True,timeout=20)
   self.assertEqual(r.returncode,0,r.stderr.decode());samples=parse_telemetry_tsv((d/'run/telemetry.tsv').read_text())
   start=float((d/'run/start.monotonic').read_text());end=float((d/'run/end.monotonic').read_text())
   self.assertEqual(telemetry(samples,start,end,0,{})['classification'],'clean')
   self.assertTrue((d/'run/telemetry.done').exists())
