"""Resume the sealed M2a job. Apply only the S6 seeds and S7 evidence rendering."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time

from afdo_wf import build, report, stats
from afdo_wf.cli import main
from afdo_wf.common import require, save, sha256
from afdo_wf.live import Experiment
from afdo_wf.receipts import Store
from afdo_wf.transport import SDB

OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent/'m2a-rpi5-prep-20261119/continuation/job.json'
EVIDENCE = 'docs/workflow/m2a/evidence/m2a-resume-20261123'
TARGET = '192.168.108.25:26101'
MEASURE = Experiment.measure_impl
REPORT = Experiment.report
WRITE = report.write
INVOKE = SDB.invoke

def forbidden(*args, **kwargs):
    require(False, 'S6/S7-only run cannot build or redo a sealed stage')

def run_measure(self, out, store):
    tests = sorted((x for x in self.inputs if x['role'] in ['test','test-secondary']),
                   key=lambda x:x['role']!='test')
    require([(x['id'], x['role']) for x in tests] == [('tos-720p-60','test'),('sintel-1080p-60','test-secondary')],
            'unexpected comparison list or ordering')
    sealed = self.job
    require(self.job_path == SOURCE and sealed['serial'] == TARGET, 'wrong sealed job')
    seeds = {x['id']: dict(order=2026112340+i, bootstrap=2026112350+i) for i,x in enumerate(tests)}
    save(out/'measurement-invocation.json', dict(seeds=seeds, source_sha256=sha256(SOURCE),
         launch_sha256=sha256(Path(__file__)), timestamp_utc=datetime.now(timezone.utc).isoformat()))
    self.job = dict(sealed, order_seed=2026112340, bootstrap_seed=2026112350)
    try:
        measured = MEASURE(self,out,store)
        plat = store.verify('deploy')['details']['oracles']
        for name, actual in measured['oracles'].items():
            key = re.sub(r'^(?:pre|post)-(?:control|candidate)-','',name)
            for field in ('eos','digest','frames','bytes','caps'):
                require(actual[field]==plat[key][field], 'S6 oracle differs from archived PLAT: '+name, 'correctness',3)
        return measured
    finally:
        self.job = sealed

def read_temperatures(rounds):
    temperatures = []
    starts = []
    for row in rounds:
        rows = stats.parse_telemetry_tsv((Path(row['local'])/'telemetry.tsv').read_text())
        by_kind = [(r['time'], v) for r in rows for v in r['temperature'].values() if v is not None]
        temperatures.extend(v for stamp,v in by_kind if row['start']-1 <= stamp <= row['end']+1)
        if any(stamp <= row['start'] for stamp,_ in by_kind):
            latest = max(stamp for stamp,_ in by_kind if stamp <= row['start'])
            starts.append(max(v for stamp,v in by_kind if stamp==latest))
    def summary(values):
        return dict(count=len(values),minimum=min(values),median=statistics.median(values),maximum=max(values)) if values else dict(count=0)
    return dict(window_c=summary(temperatures), start_c=summary(starts))

def report_run(self,out,store):
    measured=store.verify('measure')['details']
    store.verify('rebuild')
    old=store.verify('convert')['details']
    require(not self.cleanup.data['cleanup_pending'],'cleanup pending after S6')
    first_attempt = OUT.parent/'m2a-resume-20261123'
    collect_version = json.loads((first_attempt/'profile-quality-summary.json').read_text())
    formal=Path(self.job['output'])
    measure_dir=Path(measured['rounds'][0]['local']).parent
    summary={}
    for key,comparison in measured['comparisons'].items():
        plan=comparison['plan']
        lock=json.loads((measure_dir/(key+'-plan-lock.json')).read_text())
        require(sha256(measure_dir/(key+'-plan.json'))==lock['sha256'],'measurement plan SHA changed')
        pilots=[r['wall_seconds'] for r in comparison['pilots']]
        rounds=[r for r in measured['rounds'] if r['input']==key]
        by_variant={label:[r for r in rounds if r['variant']==variant] for label,variant in
                    [('BASE',plan['control']),('AFDO',plan['candidate'])]}
        require(len(pilots)==10 and all(len(rs)==plan['N'] for rs in by_variant.values()),'measurement plan incomplete')
        launches=[]
        signature='( bash '+self.remote+'/control-formal-'+key+'-'
        for transcript in self.transport.logs.glob('*.json'):
            record=json.loads(transcript.read_text())
            if len(record['argv'])==5 and record['argv'][3]=='shell' and record['argv'][-1].startswith(signature):
                launches.append(record['start'])
        require(len(launches)>=len(rounds) and lock['time']<min(launches),
                'formal transport launches are not bound to a preceding plan lock')
        failed = [json.loads(p.read_text()) for p in sorted(measure_dir.glob(key+'-*-failed-*.json'))]
        summary[key]=dict(primary=plan['primary'], plan_sha256=lock['sha256'], order_seed=plan['order_seed'],
                          bootstrap_seed=plan['bootstrap_seed'], pilot_rounds=len(pilots),
                          pilot_base_cv=statistics.stdev(pilots)/statistics.mean(pilots), N=plan['N'],
                          statistics=comparison['statistics'], effective_frequency=comparison['effective_frequency'],
                          technical_retries=failed, plan_lock_host_epoch=lock['time'], first_formal_launch_host_epoch=min(launches), temperature={t:read_temperatures(rs) for t,rs in by_variant.items()},
                          round_flags={t:{flag:sum(r['telemetry']['classification']==flag for r in rs) for flag in
                            ('clean','telemetry_missing','telemetry_anomaly')} for t,rs in by_variant.items()})
    disclosure=dict(locked_profile_sha256=old['lock']['sha256'], profile_quality=collect_version,
                    use='M2a training, conversion, consumption and functional preparation',
                    records=json.loads((formal/'stages/convert/001/Q5-17.json').read_text()),
                    consumption_receipt_sha256=sha256(store.path('rebuild')))
    deviation=dict(stage='S5',component='AArch64 GCC support-object provenance', reason='configuration pointed to usr/lib/gcc; the frozen GCC RPM places the four GCC support objects in usr/lib64/gcc',
                   scope='one S5 audit restart only. Source commands and build-lock criteria unchanged. S6/S7 did not query GCC support objects or use a modified sealed configuration.',
                   evidence_commit='4dbfdba1cf8bb85c047f00dd8357109019b21743',
                   evidence=[EVIDENCE+'/gcc-support-path-regression.json',EVIDENCE+'/gcc-support-path.json'],
                   rebuild_receipt_sha256=sha256(store.path('rebuild')))
    def write(directory,data):
        data=dict(data, comparison_summary=summary, conversion_disclosure=disclosure,
                  registered_deviations=[deviation], telemetry_unavailable=['voltage','firmware_throttling_history'],
                  prechecks=dict(injection=measured['injection'],nonformal=measured['telemetry_check']))
        result=WRITE(directory,data)
        def percent(x):return f'{100*x:+.3f}%'
        m=['# RPi5 M2a — FFmpeg AutoFDO', '', report.DISCLAIMER, '',
           'ToS is primary; Sintel is secondary, without multiple-comparison correction.',
           'Publishable under the M1 gates: **'+str(result['publishable']).lower()+'**.', '',
           '| Input | Pilot BASE CV | N | Relative wall time | Bootstrap 95% CI | t 95% CI | Verdict |',
           '|---|---:|---:|---:|---|---|---|']
        for name, row in summary.items():
            p=row['statistics']['primary']
            m.append(f"| {name} | {row['pilot_base_cv']:.3%} | {row['N']} | {percent(p['estimate'])} | "+
                     f"{', '.join(map(percent,p['bootstrap_CI95']))} | {', '.join(map(percent,p['t_CI95']))} | {p['verdict']} |")
        m+=['','## Telemetry and paired-run checks','',
            '| Input | Flagged blocks | Flagged rounds BASE / AFDO | Imbalance difference / threshold | Technical retries | Effective MHz BASE / AFDO | Differences >0.5% |',
            '|---|---:|---:|---:|---:|---:|---|']
        for name, row in summary.items():
            s=row['statistics'];i=s['flag_imbalance'];f=row['effective_frequency']
            m.append(f"| {name} | {s['flagged']} | {i['counts']['control']} / {i['counts']['candidate']} | "+
                     f"{i['difference']} / {i['threshold']} | {len(row['technical_retries'])} | "+
                     f"{f['mhz']['control']:.2f} / {f['mhz']['candidate']:.2f} | {f['confounding_risk']} |")
        m+=['','Voltage and firmware throttling history: unknown.','',
            '| Input | Variant | Start median / max °C | Window min / median / max °C |',
            '|---|---|---|---|']
        def temps(d,ks): return ' / '.join(f'{d[k]:.2f}' for k in ks) if d['count'] else 'unknown'
        for name,row in summary.items():
            for variant,t in row['temperature'].items():
                m.append(f"| {name} | {variant} | {temps(t['start_c'],('median','maximum'))} | "+
                         f"{temps(t['window_c'],('minimum','median','maximum'))} |")
        m+=['','## Conversion, consumption and registered deviation','',
            'Locked profile SHA-256: `'+disclosure['locked_profile_sha256']+'`.',
            'Six conversions had verified identity. See report.json for the disclosure and per-target AppliedSamples.',
            'S5 used a one-run audit path correction from `usr/lib/gcc` to `usr/lib64/gcc`. '
            'The sealed platform file and thresholds stayed unchanged. Source: '+deviation['evidence_commit']+'.',
            '', 'Plan SHA, seed, pilot, clean sensitivity, round and release-gate records are in report.json.']
        (Path(directory)/'report.md').write_text('\n'.join(m)+'\n')
        return result
    report.write=write
    try:
        return REPORT(self,out,store)
    finally:
        report.write=WRITE

def reconnect(serial):
    records=[]
    for command in ('disconnect','connect'):
        command_result=subprocess.run(['sdb',command,serial],capture_output=True,text=True,timeout=30)
        records.append(dict(command=command,status=command_result.returncode,
                            stdout=command_result.stdout,stderr=command_result.stderr))
    save(OUT/('sdb-reconnect-'+str(time.time_ns())+'.json'),records)
    require(records[-1]['status']==0 and 'connected to '+serial in records[-1]['stdout'],
            'target SDB reconnection failed','environment')

def logged_invoke(self,args,timeout=900):
    # Reconnect only on explicit transport evidence. Send no mutating command twice.
    require(self.serial==TARGET,'foreign SDB target')
    try:
        return INVOKE(self,args,timeout)
    finally:
        final=self.logs/('%06d'%self.sequence)
        outputs=[p.read_text(errors='replace') for p in [final.with_suffix('.stdout'),final.with_suffix('.stderr')] if p.exists()]
        if any(re.search(r"(?im)^error: (target not found|device (?:not found|offline)|connection reset|closed)", s) for s in outputs):
            reconnect(self.serial)

if __name__=='__main__':
    assert SOURCE.is_file() and (OUT/'prerequisites.json').is_file()
    build.execute=forbidden
    Experiment.build_base=forbidden
    Experiment.rebuild=forbidden
    Experiment.measure_impl=run_measure
    Experiment.report=report_run
    SDB.invoke=logged_invoke
    raise SystemExit(main(['run','--job',str(SOURCE)]))
