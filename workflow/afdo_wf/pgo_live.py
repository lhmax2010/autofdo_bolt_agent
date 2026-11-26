"""Live stage adapters for the instrumented PGO method."""
from pathlib import Path
import re
import shlex

from . import board, buildlock, pgo, pgo_frozen, pgo_warnings, report
from .common import GateError, json_load, require, save, sha256

q = shlex.quote


class InstrumentedPGO:
    def pgo_preflight(self, out, store):
        result = self.preflight(out, store)
        events = self.transport.shell(
            "for f in /sys/bus/event_source/devices/arm*/events/*; do "
            'test ! -f "$f" || printf "%s\\n" "$f"; done', True)
        remote = self.remote + '/pgo-event-probe'
        self.register_run(remote, out/'mechanism-event-probe')
        self.transport.shell('mkdir ' + q(remote))
        manifest = {}
        for label, events_for_label in pgo.event_candidates(events).items():
            attempts = []
            selected = None
            for index, event in enumerate(events_for_label):
                logfile = remote + '/' + label + '-' + str(index) + '.csv'
                argv = shlex.join([self.perf_path, 'stat', '--no-big-num', '-x', ';', '-e', event,
                                   '-o', logfile, '--', 'taskset', '-c', str(self.platform.cpu), 'sleep', '0.05'])
                response = self.transport.shell(
                    'LC_ALL=C ' + self.perf_environment + ' ' + argv + ' >' + q(logfile+'.stdout')
                    + ' 2>' + q(logfile+'.stderr') + '; rc=$?; printf "%s\\n" "$rc"', True).strip()
                text = self.transport.shell('test ! -f ' + q(logfile) + ' || cat ' + q(logfile), True)
                counted = pgo.count_value(text) if response == '0' else None
                attempts.append(dict(event=event, exit=response, count=counted))
                if counted is not None:
                    selected = event
                    break
            manifest[label] = dict(selected=selected, probes=attempts)
        self.pull_run(remote, out/'mechanism-event-probe')
        save(out/'mechanism-events.json', manifest)
        result['mechanism_events'] = manifest
        result['pgo_evidence'] = dict(event_manifest=manifest)
        return result

    def pgogen_build_ids(self, variant, out):
        root = Path(variant['extracted']).resolve()
        identities = {}
        paths = {path.resolve() for pattern in self.package['runtime']['deploy_set'] for path in root.glob(pattern)}
        by_path = {Path(a['path']).resolve(): name for name,a in variant['artifacts'].items()}
        for library in sorted(paths):
            require(library.is_relative_to(root), 'PGOGEN runtime path escapes extracted RPM')
            raw = self.host(['readelf', '-nW', library], out).stdout.decode()
            ids = re.findall(r'Build ID:\s*([0-9a-f]{40})\b', raw)
            require(len(ids) == 1 and ids[0] not in identities, 'PGOGEN library build ID missing or ambiguous')
            identities[ids[0]] = by_path.get(library, library.name)
        require(set(by_path.values()) <= set(identities.values()), 'PGOGEN target build ID evidence incomplete')
        return identities

    def pgo_build(self, out, store):
        split = self.job.get('pgo_frozen')
        frozen = split['common'] if split else self.freeze_dependencies(out)
        instrumented = split['pgogen'] if split else frozen
        variants = {}
        for name in ('BASE','PGOGEN'):
            location = out/name
            location.mkdir()
            variants[name] = self.build_variant(name, location, frozen=instrumented if name=='PGOGEN' else frozen, stage='build')
        base, generation = (variants[name] for name in ('BASE','PGOGEN'))
        symbols = {target: self.host(['readelf','-sW', artifact['debug_path']],out).stdout.decode()
                   for target,artifact in generation['artifacts'].items()}
        runtime = pgo.check_runtime(symbols,generation['artifacts'])
        identity = self.pgogen_build_ids(generation, out)
        scratch = Path(generation['scratch']).resolve()
        declared = self.package['pgo']['runtime_archive']
        archive = (scratch/declared).resolve()
        require(archive.is_file() and archive.is_relative_to(scratch), 'pinned compiler-rt archive is absent')
        arch = self.package['build_units'][0]['arch']
        owner = self.host(['rpm','--dbpath',scratch/'var/lib/rpm','-qf','--qf','%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}',
                           '/'+declared],out).stdout.decode().strip()
        expected = split['runtime']['installed_record'].split()[0] if split else 'compiler-rt-22.1.8-4.1.'+arch
        require(owner == expected, 'unexpected compiler-rt package owning profile archive')
        commands = buildlock.recorded_switches(self.host(['readelf','-p','.GCC.command.line',archive],out).stdout.decode())
        relevant, excluded = pgo.runtime_command_provenance(generation['lock'], commands)
        save(out/'compiler-rt-command-provenance.json', dict(rpm=owner, archive=declared, sha256=sha256(archive),
             archive_records=commands, linked_records=excluded, original_lock_preserved=True))
        if split:
            relevant = self.audit_linked_atexit(base,generation,relevant,symbols,archive,out)
            relevant = pgo_frozen.pgogen_lock(base['lock'],relevant,split)
            save(out/'pgogen-dependency-deviation.json',split)
        lock = pgo.compare(base['lock'], relevant, 'PGOGEN')
        evidence = dict(runtime=runtime, build_ids=identity, build_lock=lock, runtime_rpm=owner,
                        archive_sha256=sha256(archive), runtime_records={k:len(rows) for k,rows in excluded.items()})
        save(out/'pgogen-gates.json', evidence)
        require(lock['passed'], 'PGOGEN build-lock differences: '+str(lock['differences']))
        return {**base, 'frozen': frozen, 'generation': generation, 'pgo_evidence': evidence,
                'bound_files': sorted({str(file) for lock in (frozen,instrumented)
                                                     for file in Path(lock['repo']).rglob('*') if file.is_file()})
                               + [item['path'] for result in variants.values() for item in result['rpms']]}

    def audit_linked_atexit(self,base,generation,candidate,symbols,runtime,out):
        runtime_symbols = self.host(['readelf','-Ws',runtime],out).stdout.decode()
        if not re.search(r'\bUND\s+atexit$',runtime_symbols,re.M):
            return candidate
        defined = r'\bFUNC\s+LOCAL\s+DEFAULT\s+\d+\s+atexit$'
        if not all(re.search(defined,text,re.M) for text in symbols.values()):
            return candidate
        relative = self.platform.runtime_lib+'/libc_nonshared.a'
        scratch = Path(generation['scratch'])
        support = scratch/relative
        digest = sha256(support)
        require(digest==sha256(Path(base['scratch'])/relative),'PGOGEN libc support archive changed')
        owner = self.host(['rpm','--dbpath',scratch/'var/lib/rpm','-qf','--qf',
                           '%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH} %{SHA256HEADER}','/'+relative],
                          out).stdout.decode().strip()
        require(owner.startswith('glibc-devel-') and owner in base['lock']['packages'],
                'PGOGEN libc support archive is not from the frozen baseline')
        obj = out/'glibc-atexit.o'
        obj.write_bytes(self.host(['ar','p',support,'atexit.oS'],out).stdout)
        raw = self.host(['readelf','-p','.GCC.command.line',obj],out).stdout.decode()
        records = buildlock.recorded_switches(raw)
        compared,excluded = pgo_frozen.linked_atexit_lock(base['lock'],candidate,records)
        save(out/'linked-atexit-provenance.json',dict(rpm=owner,archive=relative,archive_sha256=digest,
             object_sha256=sha256(obj),records=records,excluded=excluded,original_lock_preserved=True))
        return compared

    def pgo_deploy(self, out, store):
        result = self.deploy(out, store)
        build = self.details(store, 'build')
        deployment = self.deploy_variant(build['generation'], out)
        deployment['variant'] = 'PGOGEN'
        if self.platform.prepare_only:
            self.check_board_dependencies(build['generation'], out/'PGOGEN-compatibility')
        for item in self.inputs:
            actual = self.oracle('PGOGEN-' + item['id'], item, deployment, out)
            board.oracle_check(result['oracles'][item['id']], actual)
        result['generation'] = deployment
        return result

    def pgo_collect(self, out, store):
        deployment = self.details(store, 'deploy')['generation']
        item = next(item for item in self.inputs if item['role'] == 'train')
        runs = []
        for index in range(1, self.package['collect']['runs']+1):
            name = 'pgo-train-' + str(index)
            remote = self.remote + '/' + name
            self.transport.shell(shlex.join(['bash', self.scripts+'/start_gate.sh',
                                             self.scripts+'/capabilities.tsv', remote+'-temperature.log']))
            argv = ['bash', self.scripts+'/pgo_train.sh', remote, str(self.platform.cpu), '600',
                    'bash', self.scripts+'/timed.sh', 'train', deployment['remote'], item['path'], remote+'/result']
            env = self.workload_environment(deployment, self.scripts+'/PGOGEN-manifest.json')
            self.launch(name, argv, out, env, timeout=1200)
            local = self.pull_run(remote, Path(out)/name)
            exit_code = int((local/'collect.exit').read_text())
            require(exit_code == 0 and 'Got EOS' in (local/'collect.log').read_text(), 'PGOGEN training failed')
            self.verify_maps(local, deployment, item['path'])
            decoder, = json_load(local/'maps/decoder-check.json')['candidates']
            profiles = pgo.read_inventory(local, decoder['pid'], exit_code)
            self.oracle(name+'-correctness', item, deployment, out)
            runs.append(dict(id=name, local=str(local), pid=decoder['pid'], exit_code=exit_code, profiles=profiles))
            save(out/'training-runs.json', runs)
        return dict(runs=runs, pgo_evidence=dict(completed=len(runs), profraw_files=sum(len(r['profiles']) for r in runs)))

    def pgo_convert(self, out, store):
        build = self.details(store,'build')
        runs = self.details(store,'collect')['runs']
        def profdata(args):
            output = self.host([*self.job['profdata'], *args], out)
            require(output.returncode == 0, 'llvm-profdata rejected instrumentation profile')
            return output.stdout.decode()
        result = pgo.merge_profiles(runs, build['pgo_evidence']['build_ids'],
                                    build['artifacts'], out/pgo.PROFILE_NAME, profdata)
        ranking = profdata(['show', '--topn=20', result['profile']])
        (out/'profdata-top20.txt').write_text(ranking)
        top = pgo_warnings.attribute_top(build['generation']['build_source'], pgo_warnings.top_rows(ranking))
        result['lock']['top20'] = top
        save(out/'pgo-profile-lock.json', result['lock'])
        result['pgo_evidence'] = {key:result['lock'][key] for key in ('sha256','raw_version','indexed_version','coverage','top20')}
        return result

    def pgo_rebuild(self, out, store):
        base = self.details(store,'build')
        converted = self.details(store,'convert')
        archive = pgo.archive_lock(self.job['afdo_profile'])
        require(sha256(converted['profile']) == converted['lock']['sha256'], 'indexed PGO profile changed', 'identity', 3)
        variants = {}
        for name, profile in [('BASE-r', None), ('AFDO', archive), ('PGO', converted['profile'])]:
            location = out/name
            location.mkdir()
            variants[name] = self.build_variant(name, location, profile, base['frozen'])
        repeat, afdo, candidate = (variants[variant] for variant in ('BASE-r','AFDO','PGO'))
        gates = {
            'BASE-r': buildlock.compare(base['lock'], repeat['lock'], exact=(), value_options=(), candidate_macros=()),
            'PGOGEN': base['pgo_evidence']['build_lock'],
            'AFDO': buildlock.compare(base['lock'], afdo['lock']),
            'PGO': pgo.compare(base['lock'], candidate['lock'], 'PGO'),
        }
        save(out/'buildlock.json', gates)
        require(all(result['passed'] for result in gates.values()), 'instrumented build-lock check failed')
        afdo_audit = out/'AFDO-audit'
        afdo_audit.mkdir()
        afdo_receipt = self.audit_sample_profile(base, afdo, dict(lock=self.job['afdo_profile']), afdo_audit)
        profile_path = pgo.profile_use_path(candidate['lock']['settings'])
        staged = Path(candidate['scratch'])/profile_path.relative_to('/')
        log = (out/'PGO/execution/build.log').read_text(errors='replace')
        compiled = pgo_warnings.compile_objects(log, candidate['build_source'])
        warnings = pgo_warnings.audit(log, self.job['pgo_warning_policy'],
                                     self.package['consumption']['object_to_target'], compiled, converted['lock']['top20'])
        save(out/'pgo-warning-audit.json',warnings)
        matched = pgo.consumption(converted['lock'], staged, base['text'], candidate['text'], warnings)
        save(out/'pgo-consumption.json', matched)
        require(warnings['passed'], 'PGO warning build-lock gate failed: '+str(out/'pgo-warning-audit.json'))
        require(matched['passed'], 'PGO consumption gate failed')
        identity = lambda variant: {target:{key:item[key] for key in ('sha256','debug_sha256','build_id')}
                                    for target,item in variant['artifacts'].items()}
        control = buildlock.reproducible_control(identity(base), identity(repeat))
        save(out/'base-repeat.json', dict(identical=control == 'BASE', base=identity(base), repeat=identity(repeat)))
        require(control == 'BASE', 'BASE-r and BASE ELF identities differ')
        deployed = self.details(store,'deploy')
        deployments = {
            'BASE': deployed['deployment'] if control == 'BASE' else self.deploy_variant(repeat,out),
            'AFDO': self.deploy_variant(afdo,out),
            'PGO': self.deploy_variant(candidate,out),
        }
        for label, variant in deployments.items():
            variant['variant'] = control if label == 'BASE' else label
            for item in self.inputs:
                actual = self.oracle('pgo-audit-'+label+'-'+item['id'], item, variant, out)
                board.oracle_check(deployed['oracles'][item['id']], actual)
        return dict(control=control, deployments=deployments, buildlock=gates, candidate=candidate,
                    consumption=dict(passed=True, pgo=matched, afdo=afdo_receipt),
                    pgo_evidence=dict(control=control, afdo_profile_sha256=self.job['afdo_profile']['sha256'],
                                      warning_counts=matched['warning_counts'], coverage=matched['coverage']),
                    bound_files=[item['path'] for variant in variants.values() for item in variant['rpms']])

    def mechanism_counts(self, deployments, preflight, out, item):
        result = dict(diagnostic_only=True, event_manifest=preflight['mechanism_events'], variants={})
        for label, deployment in deployments.items():
            rows = {}
            for metric, availability in preflight['mechanism_events'].items():
                event = availability['selected']
                if event is None:
                    rows[metric] = dict(status='unavailable')
                    continue
                name = 'pgo-count-'+label+'-'+metric
                remote = self.remote+'/'+name
                env = self.workload_environment(deployment, self.scripts+'/'+deployment['variant']+'-manifest.json')
                argv = ['bash', self.scripts+'/pgo_count.sh', remote, self.perf_path, event,
                        str(self.platform.cpu), '600', 'bash', self.scripts+'/timed.sh', item['role'],
                        deployment['remote'], item['path'], remote+'/result']
                try:
                    self.launch(name, argv, out, env, timeout=1200)
                    local = self.pull_run(remote, out/name)
                    require('Got EOS' in (local/'count.log').read_text(), 'mechanism workload EOS missing')
                    self.verify_maps(local, deployment, item['path'])
                    row = pgo.count_value((local/'count.csv').read_text())
                    require(row is not None, 'mechanism count unavailable')
                    rows[metric] = dict(status='counted', selected=event, **row)
                except GateError as error:
                    rows[metric] = dict(status='failed', selected=event, reason=str(error))
            result['variants'][label] = rows
        save(out/'mechanism-counts.json', result)
        return result

    def pgo_measure(self, out, store):
        preflight = self.details(store,'preflight')
        deployments = self.details(store,'rebuild')['deployments']
        plat = self.details(store,'deploy')['oracles']
        oracles = {}
        def check(point):
            for label, deployment in deployments.items():
                for item in self.inputs:
                    name = 'pgo-'+point+'-'+label+'-'+item['id']
                    actual = self.oracle(name, item, deployment, out)
                    board.oracle_check(plat[item['id']], actual)
                    oracles[name] = actual
        with self.transport.technical_operations():
            check('pre')
            injection = self.failure_cleanup_test(out, preflight, deployments['BASE'])
            telemetry = self.telemetry_check_test(out, preflight, deployments['BASE'])
            comparisons = {}
            rounds = []
            per_comparison = sum(item['role'] in ('test', 'test-secondary') for item in self.inputs)
            for index, control in enumerate(pgo.CONTROLS):
                group = 'pgo-vs-'+control.lower()
                location = out/group
                location.mkdir()
                pair_results, rows = self.measure_pairs(deployments[control], deployments['PGO'], location, preflight,
                                                        group=group, seed_offset=per_comparison*index, primary=index==0)
                comparisons[group] = pair_results
                rounds.extend(rows)
            check('post')
            tos = next(item for item in self.inputs if item['role'] == 'test')
            mechanisms = self.mechanism_counts(deployments, preflight, out, tos)
        return dict(comparisons=comparisons, rounds=rounds, oracles=oracles, mechanism_counts=mechanisms,
                    injection=injection, telemetry_check=telemetry,
                    pgo_evidence=dict(comparisons=list(comparisons), mechanisms='diagnostic only'))

    def pgo_report(self, out, store):
        measured = self.details(store,'measure')
        rebuilt = self.details(store,'rebuild')
        converted = self.details(store,'convert')
        preflight = self.details(store,'preflight')
        primary = next(row for row in measured['comparisons']['pgo-vs-base'].values() if row['plan']['primary'])
        data = dict(method='pgo', experiment_id=self.job['experiment'],
                    build_lock=dict(passed=True, checks=rebuilt['buildlock']), board_identity=preflight['identity'],
                    telemetry_manifest=preflight['capabilities'], tools=self.job['tools'],
                    artifacts=rebuilt['candidate']['artifacts'], quality={'instrumentation':converted['quality']},
                    code_shares={'status':'diagnostic only'}, consumption=rebuilt['consumption'],
                    oracle=dict(passed=True,records=measured['oracles']),
                    measurement_plan={group:{key:row['plan'] for key,row in items.items()}
                                      for group,items in measured['comparisons'].items()},
                    rounds=measured['rounds'], statistics=primary['statistics'], comparisons=measured['comparisons'],
                    mechanism_counts=measured['mechanism_counts'],
                    pgo_evidence=dict(profile=converted['pgo_evidence'], audit=rebuilt['pgo_evidence']),
                    limitations=['One '+self.platform.report_label+'; single-threaded decode; ToS primary; '
                                 'Sintel supplementary; no multiple-comparison correction'],
                    cleanup_pending=self.cleanup.data['cleanup_pending'])
        return report.write(out,data)
