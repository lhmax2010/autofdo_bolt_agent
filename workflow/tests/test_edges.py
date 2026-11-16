"""Additional synthetic negative cases from v0.3 contracts."""
from pathlib import Path
import subprocess
from unittest.mock import patch
from test_core import Fixture,ROOT
from afdo_wf import stats,build,buildlock,consumption,config,report,cli
from afdo_wf.common import GateError,save,json_load,sha256

class EvidenceEdges(Fixture):
    def test_freeze_copy(self):
        p=self.file('a.rpm');c=self.file('conf');dest=self.d/'archive'
        def fake(argv,**kw):return subprocess.CompletedProcess(argv,0,'ok','')
        with patch('afdo_wf.build.shutil.which',return_value='/existing/createrepo_c'):
            m=build.freeze([p],c,dest,{'base':'fixed'},fake)
        self.assertFalse(m['offline_reproducible']);self.assertEqual(sha256(dest/m['packages'][0]['file']),sha256(p))
    def test_freeze_metadata_failure(self):
        with patch('afdo_wf.build.shutil.which',return_value='/existing/tool'):
            with self.assertRaises(GateError):build.freeze([self.file('a')],self.file('conf'),self.d/'repo',{},lambda a,**k:subprocess.CompletedProcess(a,1,'','failed'))
    def test_pinned_metadata(self):
        rpm=self.file('p.rpm');primary=self.file('primary.xml','<metadata xmlns="http://linux.duke.edu/metadata/common"><package><checksum type="sha256">'+sha256(rpm)+'</checksum><location href="p.rpm"/></package></metadata>')
        repomd=self.file('repomd.xml','<repomd xmlns="http://linux.duke.edu/metadata/repo"><data type="primary"><checksum type="sha256">'+sha256(primary)+'</checksum></data></repomd>')
        self.assertEqual(build.verify_repository_metadata(repomd,primary,{'p.rpm':rpm})['verified_rpms'],1)
        primary.write_text('changed')
        with self.assertRaises(GateError):build.verify_repository_metadata(repomd,primary,{'p.rpm':rpm})
    def test_rpm_header_required(self):
        def fake(a,**kw):return subprocess.CompletedProcess(a,0,'p-1-1.armv7l (none)\n','')
        with self.assertRaises(GateError):build.rpm_manifest(self.d,fake)
    def test_child_final_peak(self):
        p=self.d/'child.json'
        r=subprocess.run(['python3',str(ROOT/'workflow/afdo_wf/build_child.py'),str(p),'python3','-c','pass'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0);self.assertGreater(json_load(p)['memory_peak'],0)
    def test_consumption_profile_path(self):
        p=self.file('profile');remark=self.file('x.yaml',"--- !Analysis\nPass: sample-profile-impl\nName: AppliedSamples\nFunction: f\nDebugLoc: { File: f.c, Line: 1, Column: 1 }\nArgs:\n  - NumSamples: '1'\n...\n")
        x=consumption.evaluate(['x'],{'x/':'x'},[('x/a.o',remark)],{'x':[['clang','-fprofile-sample-use=/wrong']]},sha256(p),p,{'x':'before'},{'x':'after'},profile_option_path='/right')
        self.assertFalse(x['passed'])
    def test_chroot_sha_reject(self):
        with self.assertRaises(GateError):consumption.evaluate([],{},[],{},'0'*64,self.file('p'),{}, {},profile_option_path='/p')
    def test_zero_text_change(self):
        p=self.file('profile')
        x=consumption.evaluate(['x'],{'x/':'x'},[],{'x':[['clang','-fprofile-sample-use=/p']]},sha256(p),p,{'x':'same'},{'x':'same'},profile_option_path='/p')
        self.assertIn('no target text change',x['targets']['x']['reasons'])
    def test_empty_coverage_warning_not_application(self):
        p=self.file('r','--- !Analysis\nPass: sample-profile-impl\nName: AppliedSamples\nDebugLoc: { File: f.c, Line: 1, Column: 1 }\nFunction: f\nArgs:\n  - NumSamples: nope\n...\n')
        with self.assertRaises(GateError):list(consumption.records(p))
    def test_balanced_order_exact(self):
        self.assertEqual(['AB' if x[0]=='BASE' else 'BA' for x in stats.order(15,20261116)],['BA','BA','BA','AB','AB','AB','AB','AB','BA','BA','AB','AB','BA','BA','AB'])
    def test_order_rows_independent(self):
        rows=stats.order(15,1);rows[0][0]='changed'
        self.assertTrue(all('changed' not in r for r in rows[1:]))
    def test_retry_once_whole_block(self):
        rows=[dict(id=1,attempt=1,failure='timeout',measurement_obtained=False),dict(id=1,attempt=2,complete=True)]
        self.assertEqual(stats.select_attempts(rows,1),[rows[1]])
    def test_retry_measured_forbidden(self):
        with self.assertRaises(GateError):stats.select_attempts([dict(id=1,attempt=1,complete=True),dict(id=1,attempt=2,complete=True)],1)
    def test_correctness_not_retry(self):
        with self.assertRaises(GateError):stats.select_attempts([dict(id=1,attempt=1,failure='correctness')],1)
    def test_retry_more_than_once(self):
        with self.assertRaises(GateError):stats.select_attempts([dict(id=1,attempt=i) for i in [1,2,3]],1)
    def test_window_bracketing(self):
        cap={'frequency':['f'],'temperature':['t']}
        r=[dict(time=i+.1,frequency={'f':1500},temperature={'t':59}) for i in range(5)]
        self.assertEqual(stats.telemetry(r,1.2,3,1500,cap)['classification'],'clean')
    def test_query_missing_and_alarm_priority(self):
        text='SAMPLE\t0\n0\tfrequency\tf\tunknown\n0\tvoltage\tv\t1\nEND\t0\nSAMPLE\t1\n'
        rows=stats.parse_telemetry_tsv(text);x=stats.telemetry(rows,1,2,1500,dict(frequency=['f'],temperature=['t'],voltage=['v']))
        self.assertEqual(x['classification'],'telemetry_anomaly');self.assertTrue(x['missing'])
    def test_exact_twenty_percent_not_capped(self):
        rows=[dict(id=i,complete=True,control=10,candidate=8,control_flag='telemetry_missing' if i==1 else 'clean') for i in range(1,6)]
        self.assertEqual(stats.analyze(rows,5,1,clear_flag_imbalance=False,repetitions=100)['primary']['verdict'],'faster')
    def test_flag_imbalance_cap(self):
        rows=[dict(id=i,complete=True,control=10,candidate=8) for i in range(1,6)]
        self.assertEqual(stats.analyze(rows,5,1,clear_flag_imbalance=True,repetitions=100)['primary']['verdict'],'inconclusive')
    def test_no_board_shell_forbidden_construct(self):
        for p in (ROOT/'workflow/board').glob('*.sh'):
            text=p.read_text();self.assertNotIn('${var,,}',text);self.assertNotIn('timeout ',text)
            r=subprocess.run(['bash','--posix','-n',str(p)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
