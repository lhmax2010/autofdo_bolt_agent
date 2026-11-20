"""Host stage CLI. Board stages are explicit dry-run interfaces in phases 1/2."""
import argparse
from pathlib import Path
import subprocess
import sys
from . import config, build, buildlock, profgen, consumption, stats, report
from .common import GateError, require, json_load, save, sha256
from .receipts import Store, DAG

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
        result=build.execute(args,job['source'],job['workdir'],out/'execution',job.get('env'),job.get('wait_seconds',172800))
        require(result['status']=='success','GBS failed; see execution/result.json','environment')
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

def main(argv=None):
    p=argparse.ArgumentParser(description='AutoFDO workflow phases 1/2; board stages require --dry-run')
    p.add_argument('stage',choices=[*DAG,'run'])
    p.add_argument('--package');p.add_argument('--inputs');p.add_argument('--job',required=True)
    p.add_argument('--output');p.add_argument('--receipts')
    p.add_argument('--dry-run',action='store_true');p.add_argument('--redo',action='store_true')
    p.add_argument('--stop-after', choices=[stage for stage in DAG if stage != 'restore'] + ['afdo-audit'])
    args=p.parse_args(argv)
    if args.stop_after and args.stage != 'run':
        p.error('--stop-after requires run')
    stop = 'rebuild' if args.stop_after == 'afdo-audit' else args.stop_after
    job=json_load(args.job)
    if job.get('live') and not args.dry_run:
        from .live import Experiment
        try:
            require(args.stage=='run','live experiment starts through run')
            Experiment(job,args.job).run(stop)
            return 0
        except BaseException as e:
            save(Path(job['output'])/('failure-'+str(__import__('time').time_ns())+'.json'),dict(error=repr(e),reason=getattr(e,'reason','error')))
            print(str(e),file=sys.stderr);return getattr(e,'code',1)
    args.package=args.package or job.get('package')
    args.output=args.output or job.get('output')
    args.receipts=args.receipts or job.get('receipts')
    require(args.package and args.output and args.receipts,'package/output/receipts required')
    store=Store(args.receipts)
    try:
        package=config.load(args.package)
        if args.inputs:config.load_inputs(args.inputs)
        job=json_load(args.job)
        stages=list(DAG) if args.stage=='run' else [args.stage]
        if stop:
            stages=stages[:stages.index(stop)+1]
        # No partial live run followed by discovering the board interface is dry-only.
        require(args.dry_run or not (set(stages)&BOARD),'board orchestration is dry-run only in phases 1/2','environment')
        for stage in stages:
            out=Path(args.output)/stage
            if args.dry_run:
                save(out/'plan.json',dict(stage=stage,mode='dry-run',board_contact=False,dependencies=DAG[stage],package_sha256=sha256(args.package),job=job.get(stage,job)))
                continue
            if args.redo:store.redo(stage);store.restart(stage)
            if store.path(stage).exists():
                old=store.verify(stage)
                for path in [args.package,args.job,*([args.inputs] if args.inputs else [])]:
                    require(old['inputs'].get(str(Path(path).resolve()))==sha256(path),'resume invoked with different input; redo required')
                continue
            for dependency in DAG[stage]:store.verify(dependency)
            out.mkdir(parents=True,exist_ok=True)
            result=host_stage(stage,package,job.get(stage,job),out)
            save(out/'result.json',result)
            direct=[args.package,args.job,*([args.inputs] if args.inputs else []),*job.get('input_files',[])]
            # Bind every implementation script as well as package/workload files.
            direct+=list(Path(__file__).parent.glob('*.py'))
            direct+=list(Path(args.package).parent.rglob('*.sh'))
            direct+=list(Path(args.package).parent.rglob('*.patch'))
            # Hash existing file-valued job fields, including manifests and locks.
            def job_files(value):
                if isinstance(value,dict):
                    for v in value.values():yield from job_files(v)
                elif isinstance(value,list):
                    for v in value:yield from job_files(v)
                elif isinstance(value,str) and len(value)<4096:
                    try:
                        if Path(value).is_file():yield value
                    except OSError:pass
            direct+=list(job_files(job))
            outputs=[x for x in out.rglob('*') if x.is_file()]
            store.complete(stage,direct,outputs,result)
        return 0
    except Exception as e:
        if args.stage!='run':store.failed(args.stage,e)
        else:save(Path(args.receipts)/'run.failure.json',dict(status='failed',reason=getattr(e,'reason','error'),error=str(e)))
        print(str(e),file=sys.stderr);return getattr(e,'code',1)
