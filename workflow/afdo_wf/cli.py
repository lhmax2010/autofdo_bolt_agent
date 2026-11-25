"""AutoFDO workflow commands and their public exit contract."""
import argparse
from contextlib import contextmanager
import fcntl
import signal
from pathlib import Path
import subprocess
import sys
import time
from . import config, build, buildlock, profgen, consumption, doctor, job_commands, pgo, report, scheduler
from .common import GateError, StopRequested, canonical, require, json_load, save, sha256
from .exits import EXIT_CODES, failure_record
from .receipts import Store
from .stages import DAG, RUN_STAGES, STOP_ALIASES

BOARD={'deploy','collect','measure','restore'}

def host_stage(stage,package,job,out):
    if stage=='preflight':
        tools=job.get('tools',{})
        require(set(tools)>={'profgen','profdata','loader','libLLVM'},'required tool locks absent')
        for name,t in tools.items():require(sha256(t['path'])==t['sha256'],'tool SHA mismatch: '+name)
        return dict(config_valid=True,tools=tools,board='not contacted')
    if stage in ['build','rebuild']:
        unit=next(b for b in package['build_units'] if b['id']==job['build_unit'])
        macros={**unit['macros']}
        if stage=='rebuild':macros.update(unit['consume_macro']);macros.update(package['consumption']['diag_macro'])
        args=build.command(job['config'],job['source'],job['root'],unit,macros,job.get('repo'),job.get('buildconf'))
        result = build.execute(args, job['source'], job['workdir'], out/'execution', job.get('env'),
                               host=job.get('host'), workflow=job.get('experiment', 'workflow'), stage=stage)
        require(result['status']=='success','GBS failed; see execution/result.json',result.get('reason','environment'))
        # Build success alone is never a completed build receipt.
        pairs=job.get('artifact_pairs')
        if not pairs:
            require(job.get('rpm_packages'),'explicit runtime/debuginfo RPM package names required')
            selected=[]
            for rpm in Path(job['root']).glob('local/repos/*/*/RPMS/*.rpm'):
                q=subprocess.run(['rpm','-qp','--qf','%{NAME}',str(rpm)],capture_output=True,text=True)
                require(q.returncode==0,'RPM name query failed')
                if q.stdout in job['rpm_packages']:selected.append(rpm)
            require(selected,'declared RPMs absent')
            result['rpms']=build.extract_packages(selected,out/'extracted')
            pairs={}
            for target in package['targets']:
                if target['build_unit']!=unit['id']:continue
                runtime=(out/'extracted'/target['package_path']).resolve()
                require(runtime.is_relative_to((out/'extracted').resolve()),'runtime link escapes package root')
                debug=out/'extracted/usr/lib/debug'/runtime.relative_to((out/'extracted').resolve())
                pairs[target['id']]=dict(runtime=str(runtime),debug=str(debug)+'.debug')
        result['artifacts']={t:build.elf_manifest(v['runtime'],v['debug'],unit['isa']) for t,v in pairs.items()}
        if stage=='rebuild':
            result['buildlock']=buildlock.compare(json_load(job['control_lock']),json_load(job['candidate_lock']))
            require(result['buildlock']['passed'],'build-lock failure')
            result['consumption']=consumption.evaluate(**json_load(job['consumption_job']))
            require(result['consumption']['passed'],'consumption unverified')
        return result
    if stage=='convert':
        results=[]
        for item in job['runs']:
            artifact=item['artifact'];profile=out/(item['id']+'.extbinary');quality=out/(item['id']+'.quality.json')
            args=profgen.command(job['profgen'],artifact,item['perfscript'],item['buildids'],profile,quality,package['collect']['period_unit'],item.get('thresholds'),package['identity']['allow_unverified_identity'])
            result=profgen.convert(args,profile,quality,allow_unverified=package['identity']['allow_unverified_identity'])
            results.append(dict(**result,path=str(profile),dso=item['dso'],merge_key=item['merge_key']))
        lock=profgen.merge(job['profdata'],results,out/'package.extbinary',out/'merge')
        return dict(conversions=results,profile_lock=lock)
    if stage=='report':return report.write(out,json_load(job['report_input']))
    require(False,'stage not implemented')

@contextmanager
def writer_lock(receipts):
    receipts.mkdir(parents=True, exist_ok=True)
    with (receipts / '.writer.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise GateError('another command owns this run receipt directory', 'lock-timeout') from exc
        yield


def host_run(args, job, selected, package_path, inputs_path, output, receipts):
    package = config.load(package_path)
    if inputs_path:
        config.load_inputs(inputs_path)
    require(not set(selected) & BOARD, 'board orchestration requires a live job', 'environment')
    direct = [package_path, args.job, *([inputs_path] if inputs_path else []), *job.get('input_files', [])]
    direct += list(Path(__file__).parent.glob('*.py'))
    direct += list(Path(package_path).parent.rglob('*.sh'))
    direct += list(Path(package_path).parent.rglob('*.patch'))

    def job_files(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key != 'gbs_lock':  # Shared runtime state is not a content-bound input.
                    yield from job_files(child)
        elif isinstance(value, list):
            for child in value:
                yield from job_files(child)
        elif isinstance(value, str) and len(value) < 4096:
            try:
                if Path(value).is_file():
                    yield value
            except OSError:
                pass

    direct += list(job_files(job))
    settings = {stage: {**job, **job.get(stage, {})} for stage in selected}
    handlers = {s: (lambda out, store, s=s: host_stage(s, package, settings[s], out)) for s in selected}
    scheduler.execute(selected, handlers, output / 'stages', receipts, direct, first_output=output)


def execute(args, job, selected, package, inputs, output, receipts):
    require(output and receipts and package, 'job needs package, output and receipt paths')
    require(not job.get('draft'), 'complete the job draft and set draft=false before running')
    job_commands.validate_locks(job)
    if pgo.method(job) == 'pgo':
        require(job.get('live'), 'instrumented PGO requires a live job')
        pgo.method(job, config.load(package))
        pgo.validate_thresholds(job.get('pgo_warning_limits'))
        pgo.archive_lock(job.get('afdo_profile'))
    if job.get('live'):
        require(args.stage == 'run', 'live experiment starts through run')
        require(receipts.is_relative_to(Path(job['workdir']).resolve()), 'receipt directory outside workdir')
    with writer_lock(receipts):
        def stopped(signum, _frame):
            raise StopRequested(signum)
        previous_term = signal.signal(signal.SIGTERM, stopped)
        try:
            if job.get('live'):
                from .live import Experiment
                runner = Experiment(job, args.job)
                runner.run(selected[-1] if args.stop_after else None)
            else:
                host_run(args, job, selected, package, inputs, output, receipts)
        except (Exception, StopRequested, KeyboardInterrupt) as exc:
            record = failure_record(exc)
            _, pending = job_commands.cleanup_pending(output, receipts)
            if pending:
                record['cause'] = dict(reason=record['reason'], error=record['error'])
                record['reason'] = 'recovery-required'
                record['exit_code'] = EXIT_CODES['recovery-required']
                record['cleanup_pending'] = len(pending)
            failure = output / ('failure-' + str(time.time_ns()) + '.json')
            save(failure, record)
            print(f"{record['reason']} [{record['exit_code']}] {exc}", file=sys.stderr)
            return record['exit_code']
        finally:
            signal.signal(signal.SIGTERM, previous_term)
    return EXIT_CODES['success']


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(EXIT_CODES['usage'], 'usage [64] ' + message + '\n')


def main(argv=None):
    parser = Parser(description='Run and inspect AutoFDO experiments.')
    parser.add_argument('stage', nargs='?', choices=[*DAG, 'run', 'status', 'init', 'explain', 'doctor'])
    parser.add_argument('explained_stage', nargs='?', choices=[*DAG, *STOP_ALIASES])
    parser.add_argument('--job', help='Job JSON (draft destination for init)')
    parser.add_argument('--package')
    parser.add_argument('--inputs')
    parser.add_argument('--output')
    parser.add_argument('--receipts')
    parser.add_argument('--method', choices=('autofdo','pgo'), help='Method for init or explain')
    parser.add_argument('--platform', help='Board profile when initializing a job')
    parser.add_argument('--workdir')
    parser.add_argument('--experiment')
    parser.add_argument('--media', action='append', default=[], metavar='ID=FILE')
    parser.add_argument('--media-dir')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--redo', choices=RUN_STAGES, metavar='STAGE')
    parser.add_argument('--reason', help='Operator reason to bind to the redo receipt')
    parser.add_argument('--stop-after', choices=[*RUN_STAGES, *STOP_ALIASES])
    args = parser.parse_args(argv)
    try:
        require(args.method is None or args.stage in ('init','explain'), '--method requires init or explain', 'usage')
        require(args.stage == 'explain' or args.explained_stage is None, 'unexpected stage argument', 'usage')
        require(not args.stop_after or args.stage == 'run', '--stop-after requires run', 'usage')
        require(not args.reason or args.redo, '--reason requires --redo', 'usage')
        require(not args.redo or args.stage in (None, 'run') and not args.dry_run and not args.stop_after,
                '--redo is a separate archive operation', 'usage')
        require(not args.dry_run or args.stage in (*DAG, 'run'), '--dry-run requires a stage or run', 'usage')
        if args.stage == 'explain':
            require(args.explained_stage, 'explain requires a stage', 'usage')
            name = STOP_ALIASES.get(args.explained_stage, args.explained_stage)
            print(canonical(job_commands.explain(name, args.method or 'autofdo')), end='')
            return EXIT_CODES['success']
        if args.stage == 'init':
            print(canonical(job_commands.initialize(args)), end='')
            return EXIT_CODES['success']
        if args.stage == 'doctor':
            job = json_load(args.job) if args.job else None
            require(not args.job or isinstance(job, dict), 'job must be a JSON object')
            workdir = Path(args.workdir or (job or {}).get('workdir') or Path.cwd()).resolve()
            print(canonical(doctor.inspect(workdir, job)), end='')
            return EXIT_CODES['success']
        require(args.job and (args.stage or args.redo), 'command and --job are required', 'usage')
        job = json_load(args.job)
        require(isinstance(job, dict), 'job must be a JSON object')
        package, inputs, output, receipts = job_commands.paths(args, job)
        if args.redo:
            require(output and receipts, 'job needs output and receipt paths')
            if job.get('live'):
                require(receipts.is_relative_to(Path(job['workdir']).resolve()), 'receipt directory outside workdir')
            with writer_lock(receipts):
                _, pending = job_commands.cleanup_pending(output, receipts)
                require(not pending, 'cleanup_pending must be resolved before redo', 'recovery-required')
                store = Store(receipts)
                affected = store.redo(args.redo, args.reason or 'operator requested redo')
                binding = store.redo_bindings()[args.redo]
            print(canonical(dict(status='invalidated', stages=[s for s in DAG if s in affected], **binding)), end='')
        elif args.stage == 'status':
            require(output and receipts, 'job needs output and receipt paths')
            status = job_commands.status(output, receipts)
            if pgo.method(job) == 'pgo':
                status.update(method='pgo', variants=list(pgo.VARIANTS), comparisons=pgo.comparison_metadata())
            print(canonical(status), end='')
        else:
            selected = list(DAG if args.dry_run else RUN_STAGES) if args.stage == 'run' else [args.stage]
            if args.stop_after:
                stop = STOP_ALIASES.get(args.stop_after, args.stop_after)
                selected = selected[:selected.index(stop) + 1]
            if args.dry_run:
                print(canonical(job_commands.plan(args, job, selected)), end='')
            else:
                return execute(args, job, selected, package, inputs, output, receipts)
        return EXIT_CODES['success']
    except (Exception, StopRequested, KeyboardInterrupt) as exc:
        record = failure_record(exc)
        print(f"{record['reason']} [{record['exit_code']}] {exc}", file=sys.stderr)
        return record['exit_code']
