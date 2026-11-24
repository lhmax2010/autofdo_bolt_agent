"""Synthetic process-tree/identity cases plus the unchanged attempt-05 evidence."""
import json,os,subprocess,tempfile,unittest
from pathlib import Path
from afdo_wf import board
from afdo_wf.common import GateError

W=Path(__file__).resolve().parents[2]
class ProcessTreeTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']);self.d=Path(self.tmp.name)
  self.rule=json.loads((W/'workflow/packages/ffmpeg/workloads/decoder.json').read_text())
  self.manifest={n+'.so.1':dict(id=n,board_path='/opt/afdo_agent/variants/BASE/'+n+'.so.1',sha256='a'*64) for n in ['libavcodec','libavutil']}
 def tearDown(self):self.tmp.cleanup()
 def snapshot(self,seq,pid,decoder=True,wrong=False,complete=True):
  d=self.d/(str(seq)+'-'+str(pid));d.mkdir()
  samples=self.d/'samples.tsv'
  rows=dict(line.split() for line in samples.read_text().splitlines()) if samples.exists() else {}
  rows[str(seq)]=str(seq/10)
  samples.write_text(''.join(k+' '+v+'\n' for k,v in sorted(rows.items(),key=lambda x:int(x[0]))))
  args=[self.rule['executable']]+[x.replace('{input}','/opt/afdo_agent/inputs/test') for x in self.rule['argv']] if decoder else ['bash','watchdog.sh']
  (d/'cmdline.txt').write_bytes(b'\0'.join(x.encode() for x in args)+b'\0')
  (d/'identity.txt').write_text(f'{pid} 20 10 10 99 1.23\n');(d/'complete').write_text('1' if complete else '0')
  (d/'maps.txt').write_text(''.join('1-2 r-xp 0 00:00 0 '+('/usr/lib/'+n if wrong else v['board_path'])+'\n' for n,v in self.manifest.items()))
  (d/'mapped-sha256.txt').write_text(''.join(v['sha256']+'  '+v['board_path']+'\n' for v in self.manifest.values()))
  return d
 def check(self):return board.decoder_maps(self.d,self.manifest,['libavcodec','libavutil'],['libav*.so*'],self.rule,'/opt/afdo_agent/inputs/test')
 def test_short_decoder_present_only_one_sample(self):
  self.snapshot(1,10,False);self.snapshot(2,10,False);self.snapshot(2,30);self.snapshot(3,10,False);self.snapshot(3,30)
  self.assertEqual(self.check(),2)
 def test_only_root_fails(self):
  self.snapshot(1,10,False)
  with self.assertRaises(GateError):self.check()
 def test_system_library_fails(self):
  self.snapshot(1,30,wrong=True)
  with self.assertRaises(GateError):self.check()
 def test_multiple_candidates_fail(self):
  self.snapshot(1,30);self.snapshot(2,31)
  with self.assertRaises(GateError):self.check()
 def test_read_failure_not_success(self):
  d=self.snapshot(1,30,complete=False);(d/'errors.log').write_text('cat: /proc/30/maps: No such file or directory\n')
  with self.assertRaises(GateError):self.check()
  self.assertEqual(json.loads((self.d/'decoder-check.json').read_text())['incomplete_snapshots'],[str(d)])
 def test_wrong_pipeline_fails(self):
  d=self.snapshot(1,30);(d/'cmdline.txt').write_bytes((d/'cmdline.txt').read_bytes().replace(b'max-threads=1',b'max-threads=2'))
  with self.assertRaises(GateError):self.check()
 def test_three_level_stat_tree_and_unrelated_excluded(self):
  proc=self.d/'proc';proc.mkdir()
  for pid,ppid,comm in [(10,1,'watchdog bash'),(20,10,'perf'),(30,20,'gst-launch'),(40,1,'other (task)')]:
   d=proc/str(pid);d.mkdir();(d/'stat').write_text(f'{pid} ({comm}) S {ppid} 10 10 '+ '0 '*15+'99\n')
  cmd='. "$1"; proc_table "$2" "$3" "$4"; proc_descendants 10 "$3"'
  r=subprocess.run(['bash','--posix','-c',cmd,'test',str(W/'workflow/board/proc_tree.sh'),str(proc),str(self.d/'table'),str(self.d/'errors')],capture_output=True,text=True,check=True)
  self.assertEqual({x.split()[0] for x in r.stdout.splitlines()},{'10','20','30'})
 def test_proc_read_error_raw_preserved(self):
  proc=self.d/'proc';(proc/'42').mkdir(parents=True);(proc/'42/stat').mkdir()
  subprocess.run(['bash','-c','. "$1"; proc_table "$2" "$3" "$4"','test',str(W/'workflow/board/proc_tree.sh'),str(proc),str(self.d/'table'),str(self.d/'errors')],check=True)
  self.assertIn('stat read failed', (self.d/'errors').read_text());self.assertIn('directory',(self.d/'errors').read_text())
 def test_attempt05_all_30_still_rejected(self):
  archive=os.environ.get('AFDO_WF_ATTEMPT05_MAPS')
  if not archive:
   self.skipTest('original attempt-05 map snapshots require AFDO_WF_ATTEMPT05_MAPS')
  files=list(Path(archive).glob('*/maps.txt'));self.assertEqual(len(files),30)
  argv={x['snapshot']:x['argv'] for x in json.loads((W/'workflow/tests/fixtures/attempt05-root-cmdlines.json').read_text())}
  for i,f in enumerate(files):
   d=self.snapshot(i,20061,False);(d/'maps.txt').write_bytes(f.read_bytes())
   (d/'cmdline.txt').write_bytes('\0'.join(argv[f.parent.name]).encode())
  with self.assertRaises(GateError):self.check()
 def test_buildid_cross_evidence(self):
  a={k:dict(build_id='abc') for k in ['libavcodec','libavutil']}
  good=''.join('abc '+v['board_path']+'\n' for v in self.manifest.values())
  self.assertEqual(len(board.check_perf_buildids(good,a,self.manifest)),2)
  with self.assertRaises(GateError):board.check_perf_buildids(good.replace('abc','def',1),a,self.manifest)

 def test_cadence_exact_five_seconds_and_excess(self):
  (self.d/'samples.tsv').write_text('1 0.0\n2 5.0\n')
  self.assertEqual(board.observer_cadence(self.d)['max_gap_seconds'],5.)
  (self.d/'samples.tsv').write_text('1 0.0\n2 5.01\n')
  with self.assertRaises(GateError):board.observer_cadence(self.d)
 def test_real_attempt06_cadence_now_allowed(self):
  # Frozen numeric gap from the original samples.tsv; synthetic test copy.
  (self.d/'samples.tsv').write_text('1 0.00\n2 1.16\n')
  self.assertEqual(board.observer_cadence(self.d)['max_gap_seconds'],1.16)
 def test_signal_stop_not_swallowed_by_communicate(self):
  source="""import os,signal,subprocess,sys
from afdo_wf.common import StopRequested
kind=sys.argv[1]
def stop(s,f):
 if kind=='old':raise InterruptedError('signal')
 raise StopRequested(s)
signal.signal(signal.SIGTERM,stop)
p=subprocess.Popen([sys.executable,'-c','import os,time,signal;time.sleep(.1);os.kill(os.getppid(),signal.SIGTERM);time.sleep(.2)'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:
 p.communicate();print('continued')
except StopRequested:
 print('stopped')
finally:
 if p.poll() is None:p.terminate()
 p.wait()
"""
  old=subprocess.run(['python3','-c',source,'old'],capture_output=True,text=True,check=True)
  new=subprocess.run(['python3','-c',source,'new'],capture_output=True,text=True,check=True)
  self.assertEqual(old.stdout.strip(),'continued');self.assertEqual(new.stdout.strip(),'stopped')

 def test_single_full_snapshot_is_insufficient(self):
  self.snapshot(1,30)
  with self.assertRaises(GateError):self.check()
 def test_non_decoder_foreign_library_rejected(self):
  self.snapshot(1,10,decoder=False,wrong=True);self.snapshot(1,30);self.snapshot(2,30)
  with self.assertRaises(GateError):self.check()
