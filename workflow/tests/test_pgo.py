"""Host-only synthetic checks for the instrumented PGO stages."""
import copy
from contextlib import redirect_stdout, redirect_stderr
import io
import json
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from afdo_wf import cli, live, pgo, report
from afdo_wf.common import GateError, json_load, save, sha256

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {'libavcodec':'a'*40, 'libavutil':'b'*40}
IDS = {identity: name for name, identity in TARGETS.items()}


def show(ids, functions, version=10):
    body = ['Counters:']
    for name in functions:
        body.extend([f'  {name}:', '    Hash: 0x0000000000000010',
                     '    Counters: 2', '    Block counts: [0, 23]'])
    body.extend(['Instrumentation level: IR  entry_first = 0',
                 f'Functions shown: {len(functions)}', 'Binary IDs: ', *ids,
                 f'Profile version: {version}'])
    return '\n'.join(body)+'\n'


def lock():
    return {key:str(key) for key in ('source_commit','patch_sha','spec_sha','source_layout',
            'frozen_repo_id','resolved_buildconf_sha','gbs_version','gbs_config_sha')} | dict(
            packages=['clang 22.1.8','compiler-rt 22.1.8'], capture_method='recorded-switches',
            commands={target:[['clang','-O2', target+'.c']] for target in TARGETS},
            settings=dict(CC=['clang'], CFLAGS=['-O2'], ASFLAGS=[], LDFLAGS=['-shared'], SHFLAGS=[]),
            macros={'with_pgo_deps':'1'})


class Instrumented(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory(dir=os.environ['TMPDIR'])
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def runs(self, targets=TARGETS, pid=40):
        rows = []
        for number in range(3):
            path = self.root/('train-'+str(number))
            raw = path/'raw'
            raw.mkdir(parents=True)
            checks = []
            for index, (target, _) in enumerate(targets.items()):
                profile = raw/f'{index}_0-{pid+number}.profraw'
                profile.write_bytes((0xff6c70726f667281).to_bytes(8,'little') + target.encode())
                checks.append(f'{sha256(profile)}  {profile.name}')
            (path/'raw.sha256').write_text('\n'.join(checks)+'\n')
            rows.append(dict(id=path.name, local=str(path), pid=pid+number, exit_code=0,
                             profiles=pgo.read_inventory(path,pid+number,0)))
        return rows

    def executor(self,args):
        if args[0] == 'merge':
            self.merge_argv = args
            Path(args[2]).write_bytes(pgo.INDEX_MAGIC.to_bytes(8,'little'))
            return ''
        path = Path(args[-1])
        if path.suffix == '.profdata':
            return show(list(IDS), list(TARGETS), 13)
        target = path.read_bytes()[8:].decode()
        return show([TARGETS[target]], [target])

    def test_pgogen_runtime_requires_definition_in_each_target(self):
        defined = ' 12: 0000000 4 OBJECT LOCAL DEFAULT 23 __llvm_profile_runtime'
        undefined = defined.replace('23 __llvm','UND __llvm')
        with self.assertRaisesRegex(GateError,'runtime missing'):
            pgo.check_runtime(dict(libavcodec=defined,libavutil=undefined),TARGETS)
        self.assertTrue(all(pgo.check_runtime(dict.fromkeys(TARGETS,defined),TARGETS).values()))

    def test_command_lock_allows_only_the_declared_instrumentation(self):
        base=lock()
        generation=copy.deepcopy(base)
        generation['macros']['with_pgogen']='1'
        generation['settings']['CFLAGS'].append('-fprofile-generate')
        generation['settings']['LDFLAGS'].append('-fprofile-generate')
        for rows in generation['commands'].values():
            rows[0].append('-fprofile-generate')
        self.assertTrue(pgo.compare(base,generation,'PGOGEN')['passed'])
        generation['commands']['libavutil'][0].append('-funroll-loops')
        self.assertFalse(pgo.compare(base,generation,'PGOGEN')['passed'])
        generation['settings']['LDFLAGS'].remove('-fprofile-generate')
        with self.assertRaisesRegex(GateError,'compile and link'):
            pgo.compare(base,generation,'PGOGEN')

    def test_exact_compiler_rt_command_is_attributed_without_mutating_lock(self):
        base=lock()
        generation=copy.deepcopy(base)
        generation['settings']['CFLAGS'].append('-fprofile-generate')
        generation['settings']['LDFLAGS'].append('-fprofile-generate')
        runtime = ['clang','-O3','-c','compiler-rt/lib/profile/InstrProfiling.c']
        for rows in generation['commands'].values():
            rows[0].append('-fprofile-generate')
            rows.append(runtime)
        filtered, excluded = pgo.runtime_command_provenance(generation,[runtime])
        self.assertTrue(pgo.compare(base,filtered,'PGOGEN')['passed'])
        self.assertEqual(excluded['libavcodec'],[runtime])
        self.assertIn(runtime,generation['commands']['libavcodec'])

    def test_unproven_runtime_looking_command_is_still_a_build_lock_difference(self):
        base=lock()
        generation=copy.deepcopy(base)
        generation['settings']['CFLAGS'].append('-fprofile-generate')
        generation['settings']['LDFLAGS'].append('-fprofile-generate')
        for rows in generation['commands'].values():
            rows[0].append('-fprofile-generate')
            rows.append(['clang','-O1','compiler-rt/lib/profile/InstrProfiling.c'])
        known=[['clang','-O3','compiler-rt/lib/profile/InstrProfiling.c']]
        filtered, excluded = pgo.runtime_command_provenance(generation,known)
        self.assertFalse(pgo.compare(base,filtered,'PGOGEN')['passed'])
        self.assertEqual(excluded['libavcodec'],[])

    def test_indexed_use_rejects_any_other_profile_or_flag(self):
        base=lock()
        candidate=copy.deepcopy(base)
        option='-fprofile-use=/staged/pgo.profdata'
        candidate['settings']['CFLAGS'].append(option)
        for rows in candidate['commands'].values():
            rows[0].append(option)
        self.assertTrue(pgo.compare(base,candidate,'PGO')['passed'])
        candidate['commands']['libavcodec'][0].append('-fprofile-use=/other/pgo.profdata')
        self.assertFalse(pgo.compare(base,candidate,'PGO')['passed'])

    def test_raw_merge_binds_inputs_and_records_versions_and_coverage(self):
        runs=self.runs()
        result=pgo.merge_profiles(runs,IDS,TARGETS,self.root/'pgo.profdata',self.executor)
        self.assertEqual(self.merge_argv[3:], [r['path'] for run in runs for r in run['profiles']])
        self.assertEqual(result['lock']['raw_version'],10)
        self.assertEqual(result['lock']['indexed_version'],13)
        self.assertEqual(result['lock']['coverage']['libavcodec']['ratio'],1)
        self.assertEqual(sha256(result['profile']),result['lock']['sha256'])

    def test_missing_profraw_for_one_dso_rejected(self):
        runs=self.runs({'libavcodec':TARGETS['libavcodec']})
        with self.assertRaisesRegex(GateError,'missing profraw'):
            pgo.merge_profiles(runs,IDS,TARGETS,self.root/'pgo.profdata',self.executor)

    def test_failed_process_rejected(self):
        runs=self.runs()
        runs[1]['exit_code']=143
        with self.assertRaisesRegex(GateError,'exit normally'):
            pgo.merge_profiles(runs,IDS,TARGETS,self.root/'pgo.profdata',self.executor)

    def test_scanner_pid_and_glob_inventory_rejected(self):
        run=self.runs()[0]
        local=Path(run['local'])
        with self.assertRaisesRegex(GateError,'decoder PID'):
            pgo.read_inventory(local,123,0)
        (local/'raw.sha256').write_text('0'*64+'  *.profraw\n')
        with self.assertRaisesRegex(GateError,'exact member'):
            pgo.read_inventory(local,run['pid'],0)

    def test_unlisted_training_output_rejected(self):
        run=self.runs()[0]
        (Path(run['local'])/'raw'/'unlisted.profraw').touch()
        with self.assertRaisesRegex(GateError,'unlisted'):
            pgo.read_inventory(run['local'],run['pid'],0)

    def test_unknown_or_multiple_binary_ids_rejected(self):
        runs=self.runs()
        for ids in (['c'*40], list(IDS)):
            with self.subTest(ids=ids), self.assertRaisesRegex(GateError,'known PGOGEN'):
                pgo.merge_profiles(runs,IDS,TARGETS,self.root/'pgo.profdata',
                                   lambda args: show(ids,['example']))

    def test_profdata_reader_failure_rejects_incompatible_raw(self):
        runs=self.runs()
        def execute(args):
            raise GateError('llvm-profdata unsupported raw version')
        with self.assertRaisesRegex(GateError,'unsupported raw version'):
            pgo.merge_profiles(runs,IDS,TARGETS,self.root/'pgo.profdata',execute)
        self.assertFalse((self.root/'pgo.profdata').exists())

    def test_mixed_raw_versions_rejected(self):
        runs=self.runs()
        def execute(args):
            return self.executor(args).replace('Profile version: 10','Profile version: 9') if 'train-2' in args[-1] else self.executor(args)
        with self.assertRaisesRegex(GateError,'inconsistent raw'):
            pgo.merge_profiles(runs,IDS,TARGETS,self.root/'pgo.profdata',execute)

    def test_consumption_thresholds_and_changed_text(self):
        indexed=self.root/'pgo.profdata'
        indexed.write_bytes(b'fixture')
        evidence=dict(sha256=sha256(indexed),coverage=dict.fromkeys(TARGETS,1))
        logs='file.c:8: warning: profile data may be out of date [-Wprofile-instr-out-of-date]'
        limits=dict.fromkeys(pgo.DIAGNOSTICS,0)
        with self.assertRaisesRegex(GateError,'preregister'):
            pgo.consumption(logs,{},evidence,indexed,{}, {})
        def assess(new_text):
            return pgo.consumption(logs,limits,evidence,indexed,dict.fromkeys(TARGETS,'base'),new_text)
        self.assertFalse(assess(dict.fromkeys(TARGETS,'candidate'))['passed'])
        limits['profile-instr-out-of-date']=1
        self.assertFalse(assess(dict(libavcodec='candidate',libavutil='base'))['passed'])
        self.assertTrue(assess(dict.fromkeys(TARGETS,'candidate'))['passed'])

    def test_mechanisms_have_native_preference_and_only_counts(self):
        candidates=pgo.event_candidates('/sys/bus/event_source/devices/armv8_cortex_a76/events/l1i_cache_refill')
        self.assertEqual(candidates['l1i-refill'][0],'armv8_cortex_a76/l1i_cache_refill/')
        self.assertEqual(pgo.count_value('0;;cycles;12;100\n')['count'],0)
        self.assertIsNone(pgo.count_value('<not supported>;;cycles;0;0'))

    def invoke(self,args):
        output,error=io.StringIO(),io.StringIO()
        with redirect_stdout(output),redirect_stderr(error):
            status=cli.main(args)
        return status,json.loads(output.getvalue()) if output.getvalue() else None,error.getvalue()

    def test_operator_pgo_init_dry_run_status_explain(self):
        package=ROOT/'packages/ffmpeg/package-rpi5.toml'
        original=(ROOT/'packages/ffmpeg/inputs.toml').read_text()
        for digest,name in zip(re.findall(r'^sha256 = "([0-9a-f]+)"',original,re.M),
                               ('bbb_720p_h264_60s.mp4','tos_720p_h264_60s.mp4','sintel_1080p_h264_60s.mp4')):
            media=self.root/name
            media.write_text(name)
            original=original.replace(digest,sha256(media))
        inputs=self.root/'inputs.toml'
        inputs.write_text(original)
        job=self.root/'job.json'
        output=self.root/'run'
        rc, value, error=self.invoke(['init','--method','pgo','--job',str(job),'--package',str(package),
                          '--platform','rpi5-aarch64','--inputs',str(inputs),'--media-dir',str(self.root),
                          '--output',str(output),'--workdir',str(self.root)])
        self.assertEqual(rc,0,error)
        self.assertIn('pgo_warning_limits',value['missing_for_run'])
        self.assertIn('afdo_profile',value['missing_for_run'])
        rc, plan, error=self.invoke(['run','--dry-run','--job',str(job)])
        self.assertEqual(rc,0,error)
        self.assertFalse(plan['board_contact'])
        self.assertEqual(plan['variants'],list(pgo.VARIANTS))
        rc, status, _=self.invoke(['status','--job',str(job)])
        self.assertEqual(rc,0)
        self.assertEqual(status['comparisons'],plan['comparisons'])
        rc, stage, _=self.invoke(['explain','convert','--method','pgo'])
        self.assertEqual(rc,0)
        self.assertIn('locked indexed profile and merge manifest',stage['outputs'])
        self.assertFalse(output.exists())

    def test_distinct_pair_plans_reuse_measurement_engine(self):
        runner=object.__new__(live.Experiment)
        runner.inputs=[dict(id='tos',role='test'),dict(id='sintel',role='test-secondary')]
        runner.job=dict(order_seed=100,bootstrap_seed=200)
        runner.package=dict(measure=dict(epsilon=.01,warmup=1))
        runner.cleanup=SimpleNamespace(data={'cleanup_pending':[]})
        observed=[]
        def timed(name, item, deployment, out, preflight):
            observed.append(name)
            seconds=9 if deployment['variant']=='PGO' else 10
            return dict(wall_seconds=seconds,variant=deployment['variant'],
                        telemetry=dict(classification='clean'),perf={'task-clock':1,'cycles':1000000})
        runner.timed=timed
        with patch('afdo_wf.live.stats.budget',return_value=10):
            for index,control in enumerate(pgo.CONTROLS):
                group='pgo-vs-'+control.lower()
                out=self.root/group
                out.mkdir()
                comp, rows=runner.measure_pairs(dict(variant=control),dict(variant='PGO'),out,{},
                                              group=group,seed_offset=index*2,primary=index==0)
                self.assertEqual(comp['tos']['plan']['order_seed'],100+index*2)
                self.assertEqual(comp['sintel']['plan']['bootstrap_seed'],201+index*2)
                self.assertEqual(comp['tos']['plan']['primary'],index==0)
                self.assertEqual(len(rows),40)
                self.assertEqual(json_load(out/'tos-plan-lock.json')['sha256'],sha256(out/'tos-plan.json'))
                self.assertEqual(set(comp['tos']['plan']['order'][0]),{control,'PGO'})
        self.assertEqual(len(observed),len(set(observed)))

    def test_pgo_markdown_reports_comparisons_and_diagnostic_counts(self):
        payload=dict.fromkeys(report.REQUIRED,{})
        payload.update(method='pgo', experiment_id='pgo-fixture', limitations=[], cleanup_pending=[],
                       quality={'pgo':{'publishable':True}}, build_lock={'passed':True},
                       consumption={'passed':True}, oracle={'passed':True},
                       statistics={'primary':{'verdict':'faster'}}, mechanism_counts=dict(diagnostic_only=True))
        comp=dict(tos=dict(plan=dict(N=10),statistics=dict(primary=dict(
                                    estimate=-.02,bootstrap_CI95=[-.021,-.019],verdict='faster'))))
        payload['comparisons']={group:copy.deepcopy(comp) for group in ('pgo-vs-base','pgo-vs-afdo')}
        result=report.write(self.root,payload)
        self.assertTrue(result['publishable'])
        rendered=(self.root/'report.md').read_text()
        self.assertIn('| pgo-vs-afdo | tos | 10 |',rendered)
        self.assertIn('## Mechanism counts',rendered)
