"""Observer revision: synthetic cache/injection and immutable attempt-06 replay."""
import contextlib,json,os,shutil,signal,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
from afdo_wf import board
from afdo_wf.common import StopRequested,TechnicalFailure
from afdo_wf.live import Experiment,paired_block
W=Path(__file__).resolve().parents[2]
class ObserverRevisionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']);self.d=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def test_hash_once_for_duplicate_file_identity(self):
  scripts=self.d/'scripts';scripts.mkdir();out=self.d/'out';out.mkdir();(out/'hash-queue').mkdir()
  shutil.copyfile(W/'workflow/board/hash_maps.sh',scripts/'hash_maps.sh')
  (scripts/'common.sh').write_text('safe_path() { test -d "$1"; }\n')
  f=self.d/'library';f.write_bytes(b'synthetic library')
  st=f.stat();dev=f'{os.major(st.st_dev):02x}:{os.minor(st.st_dev):02x}'
  raw=Path('/proc/self/stat').read_text();start=raw[raw.rfind(')')+2:].split()[19]
  row=f'{os.getpid()} {start} {dev} {st.st_ino} {f}\n'
  for seq in [1,2,3]:(out/f'hash-queue/{seq}.ready').write_text(row+row)
  (out/'observer.done').write_text('done\n')
  count=self.d/'calls';wrapper=scripts/'sha256sum'
  wrapper.write_text('#!/bin/bash\nprintf "hash\\n" >> "'+str(count)+'"\nexec /usr/bin/sha256sum "$@"\n');wrapper.chmod(0o755)
  env=dict(os.environ,PATH=str(scripts)+':'+os.environ['PATH'])
  subprocess.run(['bash','--posix',str(scripts/'hash_maps.sh'),str(out),str(os.getpid())],env=env,check=True,capture_output=True)
  self.assertEqual(len(count.read_text().splitlines()),1)
  self.assertEqual(len((out/'hash-attempts.tsv').read_text().splitlines()),1)
  self.assertEqual(len((out/'sha-cache.tsv').read_text().splitlines()),1)
 def test_attempt06_full_identity_passes_revised_rule(self):
  archive=os.environ.get('AFDO_WF_ATTEMPT06_RUN')
  if not archive:
   self.skipTest('original attempt-06 maps and deployment receipt require AFDO_WF_ATTEMPT06_RUN')
  run=Path(archive)
  raw=run/'stages/collect/001/train-1/maps'
  # Read immutable originals; all generated checks go into a new synthetic workspace.
  maps=self.d/'maps';shutil.copytree(raw,maps)
  deploy=json.loads((run/'receipts/deploy.json').read_text())['details']['deployment']
  rule=json.loads((W/'workflow/packages/ffmpeg/workloads/decoder.json').read_text())
  count=board.decoder_maps(maps,deploy['manifest'],['libavcodec','libavutil'],['libav*.so*','libsw*.so*'],rule,'/opt/afdo_agent/inputs/bbb_720p_h264_60s.mp4')
  self.assertEqual(count,26)
  self.assertAlmostEqual(json.loads((maps/'cadence-check.json').read_text())['max_gap_seconds'],1.16)
 def test_gap_failure_is_technical_block_retry(self):
  (self.d/'samples.tsv').write_text('1 0\n2 5.01\n')
  with self.assertRaises(TechnicalFailure):board.observer_cadence(self.d)
  attempts=[]
  with self.assertRaises(TechnicalFailure):paired_block(['BASE'],lambda *a:board.observer_cadence(self.d),lambda *a:attempts.append(a))
  self.assertEqual(len(attempts),2)
 def test_nonfinite_or_nonincreasing_time_is_technical(self):
  for rows in ['1 NaN\n2 1\n','1 1\n2 1\n','1 2\n2 1\n']:
   (self.d/'samples.tsv').write_text(rows)
   with self.assertRaises(TechnicalFailure):board.observer_cadence(self.d)
 def test_independent_injected_path_executes_and_cleans_synthetic(self):
  e=object.__new__(Experiment);e.d=self.d;e.w=W;e.scripts='/opt/afdo_agent/tools/synthetic'
  e.job=dict(package=str(W/'workflow/packages/ffmpeg/package.toml'),injection=dict(preflight=dict(capabilities={'frequency':['synthetic-frequency']}),deployment=dict(variant='BASE',manifest={}),input={'id':'synthetic'}))
  marks=[]
  @contextlib.contextmanager
  def session():
   marks.append('entered')
   try:yield
   finally:marks.append('restored')
  e.session=session;e.ensure_work=Mock();e.host_artifact=Mock();e.transport=Mock();e.push_owned=Mock()
  e.timed=Mock(side_effect=StopRequested(signal.SIGTERM))
  with self.assertRaises(StopRequested):e.injected_run()
  self.assertEqual(marks,['entered','restored']);e.timed.assert_called_once()
  pushed=[Path(x.args[0]).name for x in e.push_owned.call_args_list]
  self.assertIn('hash_maps.sh',pushed);self.assertIn('timed.sh',pushed);self.assertIn('manifest.json',pushed)
