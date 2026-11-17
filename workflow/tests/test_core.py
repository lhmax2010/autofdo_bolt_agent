"""Synthetic fixtures only. Real pilot regression is an explicitly separate script."""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from afdo_wf import config,receipts,build,buildlock,consumption,profgen,stats,board,report,cli
from afdo_wf.common import GateError,save,sha256,json_load

ROOT=Path(__file__).resolve().parents[2]

class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'temp',prefix='wf-test-');self.d=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def file(self,name,text='synthetic'):
        p=self.d/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);return p

class ConfigTests(Fixture):
    def setUp(self):super().setUp();self.c=config.load(ROOT/'workflow/packages/ffmpeg/package.toml')
    def test_real_declaration_valid(self):self.assertEqual(self.c['collect']['runs'],3)
    def test_unknown_sections(self):
        for k in config.FIELDS:
            if k=='source':obj=self.c['package']['source']
            elif k=='thresholds':obj=self.c['targets'][0]['thresholds']
            elif k in ['targets','build_units']:obj=self.c[k][0]
            else:obj=self.c if not k else self.c[k]
            obj['typo']=1
            with self.assertRaises(GateError):config.validate(self.c)
            del obj['typo']
    def test_period_and_freq(self):
        self.c['collect']['freq']=999
        with self.assertRaises(GateError):config.validate(self.c)
    def test_higher(self):
        self.c['measure']['better']='higher'
        with self.assertRaises(GateError):config.validate(self.c)
    def test_mixed_isa(self):
        self.c['build_units'][0]['macros']['profile_isa']='a32'
        with self.assertRaises(GateError):config.validate(self.c)
    def test_unknown_capture(self):
        self.c['command_capture']['method']='guess'
        with self.assertRaises(GateError):config.validate(self.c)
    def test_bad_target_unit(self):
        self.c['targets'][0]['build_unit']='other'
        with self.assertRaises(GateError):config.validate(self.c)
    def test_input_overlap(self):
        t=(ROOT/'workflow/packages/ffmpeg/inputs.toml').read_text();inp=config.load_inputs(ROOT/'workflow/packages/ffmpeg/inputs.toml')
        t=t.replace(inp[1]['sha256'],inp[0]['sha256'])
        with self.assertRaises(GateError):config.load_inputs(self.file('inputs.toml',t))
    def test_nonoverlapping_segments(self):
        t=(ROOT/'workflow/packages/ffmpeg/inputs.toml').read_text();inp=config.load_inputs(ROOT/'workflow/packages/ffmpeg/inputs.toml')
        t=t.replace(inp[1]['sha256'],inp[0]['sha256']);pos=t.index('start = 0',t.index('[[inputs]]',t.index('[[inputs]]')+1));t=t[:pos]+t[pos:].replace('start = 0','start = 60',1)
        self.assertEqual(len(config.load_inputs(self.file('inputs.toml',t))),len(inp))
    def test_nonfinite_hook(self):
        with self.assertRaises(GateError):config.hook_result(self.file('x.json','{"metric_value":NaN}'))
    def test_hook_nonjson(self):
        with self.assertRaises(ValueError):config.hook_result(self.file('x','EOS OK'))
    def test_hook_eos(self):
        d=dict(status='ok',eos=True,frames=1,bytes=3,digest='a'*64,metric_value=1,metric_unit='seconds');save(self.d/'r',d);config.hook_result(self.d/'r')
        d['eos']=False;save(self.d/'r',d)
        with self.assertRaises(GateError):config.hook_result(self.d/'r')

class ReceiptTests(Fixture):
    def chain(self):
        s=receipts.Store(self.d/'receipts');p=self.file('input')
        for stage in receipts.DAG:s.complete(stage,[p],[],{})
        return s,p
    def test_roundtrip(self):s,p=self.chain();self.assertEqual(s.verify('report')['status'],'complete')
    def test_same_name_changed(self):
        s,p=self.chain();p.write_text('changed')
        with self.assertRaises(GateError):s.verify('report')
    def test_redo_descendants(self):
        s,p=self.chain();a=s.redo('collect');self.assertIn('rebuild',a);self.assertNotIn('build',a)
        with self.assertRaises(GateError):s.verify('report')
        s.verify('build')
    def test_receipt_write_failure(self):
        s=receipts.Store(self.d/'r')
        with patch('afdo_wf.receipts.save',side_effect=OSError('disk')):
            with self.assertRaises(OSError):s.complete('preflight',[],[])
        self.assertFalse(s.path('preflight').exists())
    def test_verified_delete_failure_injection(self):
        f=self.file('pulled/x');receipt=self.d/'pull';called=[]
        with self.assertRaises(GateError):receipts.verified_pull(receipt,f.parent,{'x':'0'*64},'/opt/afdo_agent/work/one')
        self.assertFalse(receipt.exists());self.assertFalse(called)
    def test_pull_crash_before_after_delete(self):
        f=self.file('pulled/x');receipt=self.d/'pull';called=[]
        receipts.verified_pull(receipt,f.parent,{'x':sha256(f)},'/opt/afdo_agent/work/one')
        def delete(p):called.append(p)
        with patch('afdo_wf.receipts.save',side_effect=OSError('crash after remote delete')):
            with self.assertRaises(OSError):receipts.delete_pulled(receipt,delete)
        self.assertEqual(json_load(receipt)['status'],'verified')
        receipts.delete_pulled(receipt,delete);self.assertEqual(called,['/opt/afdo_agent/work/one']*2)
    def test_different_board(self):
        c=receipts.Cleanup(self.d/'j',{'model':'one'});c.register(dict(kind='root',previous=False))
        with self.assertRaises(GateError):c.restore({'model':'two'},lambda x:None)
    def test_drop_pending(self):
        c=receipts.Cleanup(self.d/'j',{});c.register(dict(kind='root',previous=False))
        self.assertTrue(c.restore({},lambda x:(_ for _ in ()).throw(OSError('sdb drop'))))
        self.assertEqual(len(json_load(self.d/'j')['cleanup_pending']),1)

class BuildTests(Fixture):
    def test_resource_start_bounds(self):
        r=dict(mem_available=16*build.GIB,load1=1,nproc=4,disk_free=50*build.GIB);self.assertTrue(build.can_start(r))
        for k,v in [('mem_available',16*build.GIB-1),('load1',2.4),('disk_free',50*build.GIB-1)]:self.assertFalse(build.can_start({**r,k:v}))
    def test_stop_two_low(self):
        r=dict(mem_available=5*build.GIB,disk_free=50*build.GIB)
        self.assertEqual(build.stop_needed(r,0),(1,False));self.assertEqual(build.stop_needed(r,1),(2,True))
    def test_stop_disk(self):self.assertTrue(build.stop_needed(dict(mem_available=20*build.GIB,disk_free=19*build.GIB),0)[1])
    def test_command_limits_and_offline(self):
        u=dict(arch='armv7l',spec='packaging/a.spec')
        a=build.command('cfg','src',self.d/'new',u,{'profile_isa':'thumb'},'repo','conf')
        self.assertIn('_smp_mflags -j2',a);self.assertNotIn('V=1',' '.join(a));self.assertIn('--skip-conf-repos',a)
        with self.assertRaises(GateError):build.command('c','s',self.d,u,{})
    def test_no_resource_macro_override(self):
        with self.assertRaises(GateError):build.command('c','s',self.d/'new',{}, {'_smp_mflags':'-j99'})
    def test_recorded_switches_dedup(self):
        c=buildlock.recorded_switches('  [ 0] clang -c a.c\n [ 20] clang -c a.c');self.assertEqual(len(set(map(tuple,c))),1)
    def test_capture_incomplete(self):
        with self.assertRaises(GateError):buildlock.recorded_switches('CC foo.o')
    def test_normalize_only_declared(self):
        a=['clang','-O2','-fprofile-sample-use=x',*buildlock.DIAGNOSTICS,'a.c'];self.assertEqual(buildlock.normalize(a),('clang','-O2','a.c'))
        self.assertIn('-O3',buildlock.normalize(['clang','-O3']))
    def lock(self):
        return dict(source_commit='a',patch_sha='b',spec_sha='c',source_layout='src',frozen_repo_id='r',resolved_buildconf_sha='x',gbs_version='1',packages=['a 1','b 2'],macros={'profile_isa':'thumb'},gbs_config_sha='conf',capture_method='recorded-switches',commands={'codec':[['clang','-O2','a.c']]},settings={k:['x'] for k in ['CC','CFLAGS','ASFLAGS','LDFLAGS','SHFLAGS']})
    def test_buildlock_equal(self):
        a=self.lock();b=copy.deepcopy(a);b['commands']['codec'][0]+=['-fprofile-sample-use=x'];self.assertTrue(buildlock.compare(a,b)['passed'])
    def test_buildlock_detects_drift(self):
        for k in ['source_layout','spec_sha','patch_sha','frozen_repo_id']:
            a=self.lock();b=copy.deepcopy(a);b[k]='bad';self.assertFalse(buildlock.compare(a,b)['passed'])
    def test_package_header_drift(self):
        a=self.lock();b=copy.deepcopy(a);b['packages'][0]='a different-sha';self.assertFalse(buildlock.compare(a,b)['passed'])
    def test_verbose_artifact_required(self):
        a=self.lock();a['capture_method']='verbose-make'
        with self.assertRaises(GateError):buildlock.compare(a,a)
    def test_make_settings_complete(self):
        self.assertEqual(len(buildlock.make_settings('\n'.join(k+' = x' for k in ['CC','CFLAGS','ASFLAGS','LDFLAGS','SHFLAGS']))),5)
        with self.assertRaises(GateError):buildlock.make_settings('CC = clang')
    def test_base_r_control(self):self.assertEqual(buildlock.reproducible_control({'codec':'a'},{'codec':'b'}),'BASE-r')

class ConsumptionTests(Fixture):
    def remark(self,n=3,loc=True):
        return '--- !Passed\nPass: sample-profile-impl\nName: AppliedSamples\n'+('DebugLoc: { File: a.c, Line: 5, Column: 2 }\n' if loc else '')+f"Function: foo\nArgs:\n  - NumSamples: '{n}'\n...\n"
    def evaluate(self,n=3,both=True):
        a=self.file('a.yaml',self.remark(n));b=self.file('b.yaml',self.remark(n));p=self.file('profile')
        return consumption.evaluate(['codec','util'],{'codec/':'codec','util/':'util'},[('codec/a.o',a)]+([('util/b.o',b)] if both else []),{x:[['clang','-fprofile-sample-use=/SOURCES/p','a.c']] for x in ['codec','util']},sha256(p),p,{'codec':'old','util':'old'},{'codec':'new','util':'new'},profile_option_path='/SOURCES/p')
    def test_both_targets(self):self.assertTrue(self.evaluate()['passed'])
    def test_wrapped_debug_location(self):
        text=self.remark().replace('Line: 5, Column: 2','Line: 5, \n     Column: 2')
        self.assertEqual(list(consumption.records(self.file('wrapped',text)))[0]['DebugLoc']['Line'],5)
    def test_zero_samples(self):self.assertFalse(self.evaluate(0)['passed'])
    def test_only_one_target(self):self.assertFalse(self.evaluate(both=False)['passed'])
    def test_truncated_yaml(self):
        with self.assertRaises(GateError):list(consumption.records(self.file('r',self.remark().replace('...\n',''))))
    def test_no_source(self):
        with self.assertRaises(GateError):list(consumption.records(self.file('r',self.remark(loc=False))))
    def test_wrong_object(self):
        with self.assertRaises(GateError):consumption.target_for_object('else/a.o',{'codec/':'codec'})
    def test_multiple_mappings(self):
        with self.assertRaises(GateError):consumption.target_for_object('codec/sub/a.o',{'codec/':'codec','codec/sub/':'util'})
    def test_warning_not_evidence(self):
        p=self.file('r','--- !Missed\nPass: sample-profile\nName: Coverage\n...\n');self.assertEqual(list(consumption.records(p)),[])

class ProfgenTests(Fixture):
    def test_literal_regex(self):
        a=dict(board_path='/opt/afdo_agent/variants/x/libfoo.so.1',path='elf',debug_path='debug')
        cmd=profgen.command(['tool'],a,'perf','ids','out','q',1000003)
        self.assertIn('--binary-match-regex=^/opt/afdo_agent/variants/x/libfoo\\.so\\.1$',cmd)
        self.assertTrue(all(x in cmd for x in profgen.POLICY))
    def test_gate(self):self.assertTrue(profgen.gate(0,dict(verdict=dict(conversion='ok',identity='verified')))['publishable'])
    def test_failed_identity(self):
        with self.assertRaises(GateError):profgen.gate(0,dict(verdict=dict(conversion='ok',identity='mismatch')))
    def test_nonzero(self):
        with self.assertRaises(GateError):profgen.gate(1,{})
    def test_unverified_never_publish(self):self.assertFalse(profgen.gate(0,dict(verdict=dict(conversion='ok',identity='unverified')),True)['publishable'])
    def test_inline_tree_collision(self):
        a=profgen.text_functions('foo:3:1\n 1: bar:3\n  1: 3\n');b=profgen.text_functions('foo:3:1\n 1: bar:3\n  2: 3\n')
        with self.assertRaises(GateError):profgen.collisions({'a':a,'b':b})
    def test_identical_collision(self):self.assertTrue(profgen.collisions({'a':{'foo':'same'},'b':{'foo':'same'}})[0]['identical'])

class StatsTests(Fixture):
    def test_reviewer_example(self):
        r=math.log(1.010025);self.assertEqual(stats.log_verdict([r-.000001,r+.000001]),'slower')
    def test_exact_epsilon(self):
        for ci in [[-.02,-.01],[.01,.02],[-.01,.009],[-.009,.01]]:self.assertEqual(stats.verdict(ci),'inconclusive')
    def test_mirrors_and_cross(self):
        for ci,v in [([-.03,-.02],'faster'),([.02,.03],'slower'),([-.009,.009],'equivalent'),([-.02,.02],'inconclusive')]:self.assertEqual(stats.verdict(ci),v)
    def test_bad_ci(self):
        for ci in [[float('nan'),1],[2,1]]:
            with self.assertRaises(GateError):stats.verdict(ci)
    def test_balanced_order(self):
        x=stats.order(15,20261116);self.assertEqual(sum(r[0]=='BASE' for r in x),8);self.assertEqual(x,stats.order(15,20261116))
    def test_multivariant_rotation(self):self.assertEqual(len(stats.order(12,1,('A','B','C'))),12)
    def test_t_quantile(self):self.assertAlmostEqual(stats.t975(14),2.144786688,places=7)
    def test_missing_caps(self):
        b=[dict(id=1,complete=True,control=10,candidate=8),dict(id=2,complete=True,control=10,candidate=8)]
        self.assertEqual(stats.analyze(b,3,1,repetitions=100)['primary']['verdict'],'inconclusive')
    def test_flag_cap(self):
        b=[dict(id=i,complete=True,control=10,candidate=8,control_flag='telemetry_missing') for i in range(1,6)]
        self.assertEqual(stats.analyze(b,5,1,repetitions=100)['primary']['verdict'],'inconclusive')
    def test_unknown_imbalance_not_assumed(self):
        b=[dict(id=i,complete=True,control=10,candidate=8) for i in range(1,4)]
        self.assertEqual(stats.analyze(b,3,1,repetitions=100)['flag_imbalance']['difference'],0)
    def test_budget(self):self.assertEqual(stats.budget([10]*10),10)
    def test_telemetry_priority(self):
        cap=dict(frequency=['f'],temperature=['t'],voltage=['v'])
        rows=[dict(time=i,frequency={'f':1500},temperature={'t':59},voltage={'v':0}) for i in range(4)]
        self.assertEqual(stats.telemetry(rows,1,2,1500,cap)['classification'],'clean')
        rows[2]['frequency']['f']=1400;rows[0]['voltage']={}
        x=stats.telemetry(rows,1,2,1500,cap);self.assertEqual(x['classification'],'telemetry_anomaly');self.assertTrue(x['missing'])
    def test_truncated_window(self):
        x=stats.telemetry([dict(time=1)],1,2,1500,dict(frequency=['f'],temperature=['t']));self.assertEqual(x['classification'],'telemetry_missing')
    def test_effective_frequency(self):self.assertFalse(stats.effective_frequency([dict(control=dict(cycles=1500000,task_clock_ms=1),candidate=dict(cycles=1500000,task_clock_ms=1))])['confounding_risk'])

class BoardTests(Fixture):
    def test_all_deploy_set(self):
        manifest={'libcodec.so.1':dict(id='codec',board_path='/opt/afdo_agent/variants/a/libcodec.so.1',sha256='a')}
        line='1-2 r-xp 0 0:0 1 /opt/afdo_agent/variants/a/libcodec.so.1\n'
        board.check_maps(line,manifest,['codec'],['lib*.so*'],{'/opt/afdo_agent/variants/a/libcodec.so.1':'a'})
        with self.assertRaises(GateError):board.check_maps(line+'1-2 r-xp 0 0:0 1 /usr/lib/libswscale.so.1\n',manifest,['codec'],['lib*.so*'],{'/opt/afdo_agent/variants/a/libcodec.so.1':'a'})
    def test_oracle(self):
        x=dict(frames=2,bytes=3,digest='a',caps='I420',threads=1)
        board.oracle_check(x,dict(**x,status='ok',eos=True))
        with self.assertRaises(GateError):board.oracle_check(x,dict(**{**x,'frames':0},status='ok',eos=True))
    def test_session_failure_restores(self):
        class Transport:
            changes=[]
            def identity(self):return {'model':'synthetic'}
            def root_state(self):return False
            def root(self,v):self.changes.append(('root',v))
            def governors(self):return {'policy0':'schedutil'}
            def governor(self,p,v):self.changes.append((p,v))
            def undo(self,a):self.changes.append(('undo',a))
        t=Transport()
        with self.assertRaises(RuntimeError):
            with board.session(t,t.identity(),self.d/'cleanup'):raise RuntimeError('S3/S6 failed')
        self.assertEqual(json_load(self.d/'cleanup')['cleanup_pending'],[])
        self.assertEqual(t.changes[-1][1]['kind'],'root')
    def test_sigterm_restore(self):
        import signal
        class T:
            def identity(self):return {}
            def root_state(self):return True
            def governors(self):return {}
            def undo(self,a):pass
        with self.assertRaises(board.StopRequested):
            with board.session(T(),{},self.d/'c'):signal.raise_signal(signal.SIGTERM)
    def test_watchdog_negative(self):
        # Host synthetic child only; no board commands or sysfs access.
        r=subprocess.run(['bash','--posix',str(ROOT/'workflow/board/watchdog.sh'),'1','bash','-c','sleep 30'],capture_output=True,text=True,timeout=8)
        self.assertNotEqual(r.returncode,0)
    def test_cli_dry_run(self):
        job=self.file('job','{}')
        rc=cli.main(['run','--package',str(ROOT/'workflow/packages/ffmpeg/package.toml'),'--job',str(job),'--output',str(self.d/'out'),'--receipts',str(self.d/'receipts'),'--dry-run'])
        self.assertEqual(rc,0);self.assertEqual(len(list((self.d/'out').glob('*/plan.json'))),9)
    def test_cli_no_live_board(self):
        job=self.file('job','{}')
        self.assertNotEqual(cli.main(['deploy','--package',str(ROOT/'workflow/packages/ffmpeg/package.toml'),'--job',str(job),'--output',str(self.d/'out'),'--receipts',str(self.d/'r')]),0)

class ReportTests(Fixture):
    def test_missing_fields(self):
        with self.assertRaises(GateError):report.write(self.d,{})
        self.assertFalse((self.d/'report.json').exists())
    def test_diagnostic_cannot_publish(self):
        d={k:{} for k in report.REQUIRED};d.update(experiment_id='synthetic',limitations=[],rounds=[],cleanup_pending=[],quality={'x':{'publishable':False}},consumption={'passed':True},oracle={'passed':True},statistics={'primary':{'verdict':'faster'}})
        result=report.write(self.d,d);self.assertFalse(result['publishable']);self.assertEqual(result['statistics']['primary']['verdict'],'inconclusive')
    def test_nonfinite_no_output(self):
        d={k:{} for k in report.REQUIRED};d['x']=float('inf')
        with self.assertRaises(GateError):report.write(self.d,d)
        self.assertFalse((self.d/'report.json').exists())

if __name__=='__main__':unittest.main()
