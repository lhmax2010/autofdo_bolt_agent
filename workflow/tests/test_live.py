import json,math,os,re,subprocess,tempfile,unittest
from pathlib import Path
from afdo_wf import stats,build
from afdo_wf.common import GateError
from afdo_wf.transport import SDB,board_path

class LiveTests(unittest.TestCase):
    def test_imbalance_thresholds(self):
        for n in [10,15,40]:
            threshold=max(2,math.ceil(.1*n))
            for difference in [1,threshold-1,threshold]:
                with self.subTest(n=n,difference=difference):
                    rows=[dict(id=i,complete=True,control=10,candidate=8,
                          candidate_flag='telemetry_missing' if i<=difference else 'clean')
                          for i in range(1,n+1)]
                    r=stats.analyze(rows,n,1,repetitions=20)
                    self.assertEqual(r['flag_imbalance']['threshold'],threshold)
                    self.assertEqual('flag imbalance' in r['primary'].get('cap_reasons',[]),difference>=threshold)
    def test_no_manual_override(self):
        with self.assertRaises(TypeError):stats.analyze([],10,1,clear_flag_imbalance=False)
    def test_one_experiment_memory_waiver(self):
        r=dict(mem_available=8*build.GIB,load1=0,nproc=4,disk_free=100*build.GIB)
        self.assertFalse(build.can_start(r))
        self.assertFalse(build.can_start(r,'another-experiment'))
        self.assertTrue(build.can_start(r,'m1-ffmpeg-rpi4-thumb-01'))
        for k,v in [('load1',2.4),('disk_free',49*build.GIB)]:
            x={**r,k:v};self.assertFalse(build.can_start(x,'m1-ffmpeg-rpi4-thumb-01'))
    def test_runtime_protection_unchanged(self):
        r=dict(mem_available=5*build.GIB,disk_free=100*build.GIB)
        self.assertEqual(build.stop_needed(r,0),(1,False))
        self.assertEqual(build.stop_needed(r,1),(2,True))
    def test_transport_read_retry(self):
        with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as td:
            calls=[]
            def run(argv,**kw):
                calls.append(argv);marker=re.search('__WF_RC_[a-f0-9]+__',argv[-1])[0]
                return subprocess.CompletedProcess(argv,0,b'abc\n' if len(calls)==1 else ('abc\n'+marker+'0\n').encode(),b'')
            s=SDB('test',td,run)
            self.assertEqual(s.shell('cat file',True),'abc');self.assertEqual(s.retries,1)
    def test_mutation_never_retries(self):
        with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as td:
            calls=[]
            def run(argv,**kw):calls.append(argv);return subprocess.CompletedProcess(argv,0,b'',b'')
            with self.assertRaises(GateError):SDB('test',td,run).shell('state change')
            self.assertEqual(len(calls),1)
    def test_path_boundary(self):
        for p in ['/usr/a','/opt/afdo_agent/work/../tools/a','/opt/afdo_agent/variants/a']:
            with self.assertRaises(GateError):board_path(p,True)

    def test_scheduler_resume_preserves_completed_stages(self):
        from afdo_wf import scheduler
        from afdo_wf.common import save
        with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as td:
            root=Path(td);inp=root/'input';inp.write_text('fixed');calls=[]
            def one(out,store):calls.append('preflight');return {'ok':True}
            def fail(out,store):calls.append('build-fail');raise InterruptedError('synthetic SIGTERM')
            with self.assertRaises(InterruptedError):
                scheduler.execute(['preflight','build'],dict(preflight=one,build=fail),root/'out',root/'receipts',[inp])
            def build_ok(out,store):calls.append('build-ok');return {'ok':True}
            scheduler.execute(['preflight','build'],dict(preflight=one,build=build_ok),root/'out',root/'receipts',[inp])
            self.assertEqual(calls,['preflight','build-fail','build-ok'])
            self.assertEqual(len(list((root/'out/build').iterdir())),2)
    def test_cleanup_process_before_pull_and_root_last(self):
        from afdo_wf.receipts import Cleanup
        with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as td:
            c=Cleanup(Path(td)/'cleanup.json',{})
            for kind in ['root','governor','process','run']:c.register(dict(kind=kind))
            order=[];c.restore({},lambda a:order.append(a['kind']))
            self.assertEqual(order,['process','run','governor','root'])
    def test_changed_read_retry_rejected(self):
        with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as td:
            calls=[]
            def run(argv,**kw):
                calls.append(argv);marker=re.search('__WF_RC_[a-f0-9]+__',argv[-1])[0]
                return subprocess.CompletedProcess(argv,0,b'old\n' if len(calls)==1 else ('new\n'+marker+'0\n').encode(),b'')
            with self.assertRaises(GateError):SDB('test',td,run).shell('read',True)
    def test_secondary_input_overlap(self):
        from afdo_wf import config
        root=Path(__file__).resolve().parents[2]
        path=root/'workflow/packages/ffmpeg/inputs.toml'
        inputs=config.load_inputs(path)
        with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as td:
            p=Path(td)/'inputs.toml';p.write_text(path.read_text().replace(inputs[2]['sha256'],inputs[0]['sha256']))
            with self.assertRaises(GateError):config.load_inputs(p)
