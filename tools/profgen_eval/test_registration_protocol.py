"""Synthetic Q.5 #10 receipts, SHA chains, controlled gate and recovery fixtures."""
import copy
import unittest
from registration_protocol import *


class SyntheticStore:
    def __init__(self):self.blobs={};self.pushed=set();self.current={}
    def put(self,data,pushed=True):
        h=digest(data);self.blobs[h]=copy.deepcopy(data);self.current[h]=copy.deepcopy(data)
        if pushed:self.pushed.add(h)
        return dict(sha256=h,path='synthetic/'+h,commit='1'*40)
    def read(self,ref):
        h=ref['sha256']
        if h not in self.pushed:raise ValueError('evidence_not_pushed')
        d=copy.deepcopy(self.blobs[h])
        if digest(d)!=h:raise ValueError('evidence_blob_sha_mismatch')
        return d

    def verify_current(self,ref):
        if digest(self.current[ref['sha256']])!=ref['sha256']:raise ValueError('working_artifact_not_registered')
        return True


def fixture():
    store=SyntheticStore();condition=digest({'load':'fixed-synthetic'})
    slots=[dict(slot=str(i),phase='old' if i<5 else 'new',origin='existing' if i<5 else 'future',
                run_id='old-'+str(i) if i<5 else None,originals=['old-sha-'+str(i)] if i<5 else [],conditions_sha256=condition) for i in range(15)]
    protocol=dict(slots_sha256=digest(slots),phase_counts={'old':5,'new':10},conditions_sha256=condition,
      registered_at=100,limits=dict(min_free_bytes=1000,stop_temperature=80,start_temperature=70),
      identity=dict(model='RPi4',arch='armv7l',kernel='fixed',build_id='fixed'),
      retry_whitelist={'synthetic_nonstop': ['collector_explicit_failure','original_invalidated']},scripts_sha256='code-sha')
    events=[]
    for i in range(5):
        r=store.put(dict(run_id='old-'+str(i),originals=['old-sha-'+str(i)]))
        p=dict(kind='initialization',slot=str(i),run_id='old-'+str(i),originals=['old-sha-'+str(i)],conditions_sha256=condition,
          collection_receipt=r,reception_receipt=r,collected_at=10,imported_at=101,automatic_outcome='success')
        events=chain_append(events,p)
    return protocol,slots,events,store


def attempt(protocol,slot='5',number=1,**changes):
    facts=dict(exit_code=0,stderr_saved=True,transfer_complete=True,sha_match=True,stop_errors=[],
      boot_id='boot',monotonic=200,positive_evidence={})
    facts.update(changes)
    return dict(kind='attempt',slot=slot,run_id='new-'+slot,attempt=number,attempt_id=slot+'-'+str(number),
      collected_at=200,received_at=201,command=['synthetic','collector'],originals=['new-sha-'+slot],
      conditions_sha256=protocol['conditions_sha256'],facts=facts,automatic_outcome=attempt_outcome(facts,protocol['retry_whitelist']))


def complete(protocol,events):
    for i in range(5,15):events=chain_append(events,attempt(protocol,str(i)))
    return events


def recovery_fixture(reason='space'):
    protocol,slots,events,store=fixture()
    stop=attempt(protocol,exit_code=1)
    events=chain_append(events,stop);stop_sha=events[-1]['sha256']
    action=dict(kind={'space':'space_check_failed','thermal':'thermal_stop','manual':'manual_stop'}[reason],
      attempt_id=stop['attempt_id'],boot_id='boot',monotonic=200)
    common=dict(attempt_id=stop['attempt_id'],boot_id='boot')
    fault=dict(common,monotonic=200,available_bytes=900 if reason=='space' else 2000,temperatures=[81 if reason=='thermal' else 60],
      recorded_by_failure_handler=True,stop_action=action)
    current=dict(common,monotonic=220,available_bytes=2000,temperatures=[60])
    identity=dict(common,monotonic=221,observed=protocol['identity'])
    recovery=dict(kind='recovery',slot='5',stop_sha256=stop_sha,reason=reason,
      conditions_sha256=protocol['conditions_sha256'],fault=store.put(fault),current=store.put(current),identity=store.put(identity))
    if reason=='manual':recovery['resume_instruction']='synthetic explicit resume'
    return protocol,slots,events,store,recovery


def mutate_evidence(store,recovery,field,change):
    d=store.read(recovery[field]);change(d);recovery[field]=store.put(d)


class ProtocolFixtures(unittest.TestCase):
    def test_old5_new10_all_legal(self):
        p,s,e,r=fixture();v=replay(p,s,complete(p,e),r)
        self.assertTrue(v['terminal']);self.assertEqual(len(v['successes']),15)
    def test_old_run_missing_initialization(self):
        p,s,e,r=fixture();v=replay(p,s,complete(p,e[:-1]),r)
        self.assertFalse(v['terminal']);self.assertNotIn('4',v['successes'])
    def test_tampered_slots(self):
        p,s,e,r=fixture();s[0]['phase']='new'
        with self.assertRaisesRegex(ValueError,'tampered'):replay(p,s,e,r)
    def test_old_masquerades_new(self):
        p,s,e,r=fixture();a=attempt(p);a['collected_at']=10
        with self.assertRaisesRegex(ValueError,'masquerading'):replay(p,s,chain_append(e,a),r)
    def test_duplicate_original_in_two_slots(self):
        p,s,e,r=fixture();a=attempt(p);a['originals']=['old-sha-0']
        with self.assertRaisesRegex(ValueError,'two_slots'):replay(p,s,chain_append(e,a),r)
    def test_sixteenth_slot(self):
        p,s,e,r=fixture();a=attempt(p,'15')
        with self.assertRaisesRegex(ValueError,'unregistered_slot'):replay(p,s,chain_append(e,a),r)
    def test_success_twice(self):
        p,s,e,r=fixture();e=chain_append(e,attempt(p));e=chain_append(e,attempt(p,number=2))
        with self.assertRaisesRegex(ValueError,'terminal'):replay(p,s,e,r)
    def test_manual_outcome_override(self):
        p,s,e,r=fixture();a=attempt(p,exit_code=1);a['automatic_outcome']='success'
        with self.assertRaisesRegex(ValueError,'manual_outcome'):replay(p,s,chain_append(e,a),r)
    def test_unknown_nonzero_stops(self):
        p,s,e,r=fixture();v=replay(p,s,chain_append(e,attempt(p,exit_code=1)),r)
        self.assertTrue(v['paused']);self.assertEqual(v['states']['5']['state'],'paused_stop')
    def test_whitelist_positive_evidence_retries(self):
        p,s,e,r=fixture();a=attempt(p,exit_code=1,retry_reason='synthetic_nonstop',positive_evidence=dict(collector_explicit_failure=True,original_invalidated=True))
        v=replay(p,s,chain_append(e,a),r);self.assertEqual(v['states']['5']['state'],'ready');self.assertEqual(v['states']['5']['attempts'],1)
    def test_whitelist_missing_positive_evidence_stops(self):
        p,s,e,r=fixture();a=attempt(p,exit_code=1,retry_reason='synthetic_nonstop')
        self.assertTrue(replay(p,s,chain_append(e,a),r)['paused'])
    def test_overheat_nonzero_stops_not_retry(self):
        p,s,e,r=fixture();a=attempt(p,exit_code=1,stop_errors=['thermal'])
        self.assertEqual(replay(p,s,chain_append(e,a),r)['states']['5']['state'],'paused_stop')
    def test_stderr_missing_stops(self):
        p,s,e,r=fixture();self.assertTrue(replay(p,s,chain_append(e,attempt(p,stderr_saved=False)),r)['paused'])
    def test_transfer_only_does_not_consume_attempt(self):
        p,s,e,r=fixture();a=attempt(p,transfer_complete=False,transfer_interrupted=True,remote_originals_intact=True)
        e=chain_append(e,a);b=attempt(p);b['kind']='transfer';e=chain_append(e,b)
        v=replay(p,s,e,r);self.assertEqual(v['states']['5']['attempts'],1);self.assertEqual(v['states']['5']['state'],'success')
    def test_transfer_cannot_replace_original(self):
        p,s,e,r=fixture();a=attempt(p,transfer_complete=False,transfer_interrupted=True,remote_originals_intact=True)
        e=chain_append(e,a);b=attempt(p);b['kind']='transfer';b['originals']=['other-sha']
        with self.assertRaisesRegex(ValueError,'same_originals'):replay(p,s,chain_append(e,b),r)
    def test_complete_transfer_sha_mismatch_stops(self):
        p,s,e,r=fixture();self.assertTrue(replay(p,s,chain_append(e,attempt(p,sha_match=False)),r)['paused'])
    def test_retry_four_failures_exhausted(self):
        p,s,e,r=fixture()
        for i in range(1,5):e=chain_append(e,attempt(p,number=i,exit_code=1,retry_reason='synthetic_nonstop',positive_evidence=dict(collector_explicit_failure=True,original_invalidated=True)))
        self.assertEqual(replay(p,s,e,r)['states']['5']['state'],'exhausted')
        with self.assertRaisesRegex(ValueError,'terminal'):replay(p,s,chain_append(e,attempt(p,number=5)),r)
    def test_three_plus_twelve_not_admitted(self):
        p,s,e,r=fixture()
        for x in s[3:5]:x.update(origin='future',phase='new',run_id=None,originals=[])
        p.update(slots_sha256=digest(s),phase_counts={'old':3,'new':12})
        with self.assertRaisesRegex(ValueError,'fewer_than_5'):validate_slots(p,s)


class RecoveryFixtures(unittest.TestCase):
    def check_failure(self,case,field,change,reason=None):
        p,s,e,r,v=recovery_fixture(case);mutate_evidence(r,v,field,change)
        with self.assertRaises(ValueError):replay(p,s,chain_append(e,v),r)
    def test_unknown_stop_with_valid_causal_evidence(self):
        p,s,e,r,v=recovery_fixture();e=chain_append(e,v)
        a=attempt(p,number=2);a['recovery_sha256']=e[-1]['sha256']
        result=replay(p,s,chain_append(e,a),r);self.assertEqual(result['states']['5']['state'],'success')
    def test_narrative_only_not_evidence(self):
        p,s,e,r,v=recovery_fixture();v.pop('fault');v['description']='it was full'
        with self.assertRaises((KeyError,ValueError)):replay(p,s,chain_append(e,v),r)
    def test_space_df_normal(self):self.check_failure('space','fault',lambda d:d.update(available_bytes=2000))
    def test_temperature_timestamp_outside_ten_seconds(self):self.check_failure('thermal','fault',lambda d:d.update(monotonic=180))
    def test_space_not_restored(self):self.check_failure('space','current',lambda d:d.update(available_bytes=900))
    def test_temperature_not_restored(self):self.check_failure('thermal','current',lambda d:d.update(temperatures=[75]))
    def test_high_temperature_without_causal_stop(self):self.check_failure('thermal','fault',lambda d:d.update(stop_action=None))
    def test_unassociated_high_temperature_ends_missing(self):
        p,s,e,r,v=recovery_fixture('thermal');mutate_evidence(r,v,'fault',lambda d:d.update(stop_action=None))
        with self.assertRaises(ValueError):replay(p,s,chain_append(e,v),r)
        done=replay(p,s,chain_append(e,dict(kind='stopped_missing',reason='no_associated_action')),r)
        self.assertTrue(done['terminal']);self.assertEqual(done['states']['5']['state'],'stopped_missing')
    def test_hardware_overrides_thermal(self):
        p,s,e,r,v=recovery_fixture('thermal');p0=e[-1]['payload'];p0['facts']['stop_errors']=['hardware_event_error','thermal']
        e=chain_append(e[:-1],p0);v['stop_sha256']=e[-1]['sha256']
        with self.assertRaisesRegex(ValueError,'irrecoverable'):replay(p,s,chain_append(e,v),r)
        e=chain_append(e,dict(kind='stopped_missing',reason='hardware_event_error'))
        result=replay(p,s,e,r);self.assertTrue(result['terminal']);self.assertEqual(sum(x['state']=='stopped_missing' for x in result['states'].values()),10)
    def test_manual_command_other_attempt(self):self.check_failure('manual','fault',lambda d:d['stop_action'].update(attempt_id='other'))
    def test_failure_handler_did_not_save_evidence(self):self.check_failure('space','fault',lambda d:d.update(recorded_by_failure_handler=False))
    def test_fixed_fault_correct_association(self):
        for reason in ['space','thermal','manual']:
            p,s,e,r,v=recovery_fixture(reason);self.assertFalse(replay(p,s,chain_append(e,v),r)['paused'])
    def test_success_without_recovery(self):
        p,s,e,r,v=recovery_fixture()
        with self.assertRaisesRegex(ValueError,'before_pushed_recovery'):replay(p,s,chain_append(e,attempt(p,number=2)),r)
    def test_recovery_changes_conditions(self):
        p,s,e,r,v=recovery_fixture();v['conditions_sha256']='changed'
        with self.assertRaisesRegex(ValueError,'protocol_change'):replay(p,s,chain_append(e,v),r)
    def test_stop_on_fourth_cannot_recover(self):
        p,s,e,r,v=recovery_fixture();last=e[-1]['payload'];e=e[:-1]
        for i in range(1,4):e=chain_append(e,attempt(p,number=i,exit_code=1,retry_reason='synthetic_nonstop',positive_evidence=dict(collector_explicit_failure=True,original_invalidated=True)))
        last.update(attempt=4,attempt_id='5-4');e=chain_append(e,last);v['stop_sha256']=e[-1]['sha256']
        with self.assertRaisesRegex(ValueError,'attempt_limit'):replay(p,s,chain_append(e,v),r)
    def test_stopped_missing_is_terminal(self):
        p,s,e,r,v=recovery_fixture();e=chain_append(e,dict(kind='stopped_missing',reason='cannot_verify'))
        with self.assertRaisesRegex(ValueError,'terminal'):replay(p,s,chain_append(e,attempt(p,number=2)),r)
    def test_telemetry_or_conversion_not_recovery(self):
        p,s,e,r=fixture()
        for kw in [dict(telemetry_only=True),dict(conversion_failure=True)]:
            with self.assertRaisesRegex(ValueError,'not_acquisition'):attempt(p,**kw)
    def test_identity_recheck_mandatory(self):self.check_failure('space','identity',lambda d:d['observed'].update(kernel='other'))
    def test_unpushed_recovery_evidence(self):
        p,s,e,r,v=recovery_fixture();r.pushed.remove(v['fault']['sha256'])
        with self.assertRaisesRegex(ValueError,'not_pushed'):replay(p,s,chain_append(e,v),r)


def gate_fixture():
    p,s,e,r=fixture();e=complete(p,e)
    reg=r.put(dict(kind='amendment3',protocol=r.put(p),slots=r.put(s),locked_artifacts=[r.put({'static':'synthetic'})]))
    request=dict(data_kind='real',originals=['new-sha-5'],configuration='max',scripts_sha256='code-sha',quantity='M3',time=300,interpretation=True,receipts=r.put(e))
    log=chain_append([], {k:request[k] for k in ['originals','configuration','scripts_sha256','quantity','time']})
    request['calculation_log']=r.put(log)
    return p,s,e,r,reg,request


class GateFixtures(unittest.TestCase):
    def test_pre_registration_m3_or_branch_rejected(self):
        for q in ['M3','branch_probability_error']:
            with self.assertRaisesRegex(ValueError,'not_registered'):admit_computation(dict(data_kind='real',quantity=q),None,SyntheticStore())
    def test_post_registration_missing_calculation_log(self):
        p,s,e,r,reg,req=gate_fixture();req['calculation_log']=r.put([])
        with self.assertRaisesRegex(ValueError,'log_missing'):admit_computation(req,reg,r)
    def test_valid_gated_computation(self):
        p,s,e,r,reg,req=gate_fixture();self.assertTrue(admit_computation(req,reg,r)['all_slots_terminal'])
    def test_fourteenth_slot_not_terminal(self):
        p,s,e,r,reg,req=gate_fixture();req['receipts']=r.put(e[:-1])
        with self.assertRaisesRegex(ValueError,'terminal_receipts'):admit_computation(req,reg,r)
    def test_broken_log_chain(self):
        p,s,e,r,reg,req=gate_fixture();log=r.read(req['calculation_log']);log[0]['previous']='x';req['calculation_log']=r.put(log)
        with self.assertRaisesRegex(ValueError,'broken_append'):admit_computation(req,reg,r)
    def test_unpushed_receipts(self):
        p,s,e,r,reg,req=gate_fixture();r.pushed.remove(req['receipts']['sha256'])
        with self.assertRaisesRegex(ValueError,'not_pushed'):admit_computation(req,reg,r)
    def test_append_only_file_tip_and_bytes(self):
        import time
        folder=Path('temp/registration-batch2/synthetic-protocol-files');folder.mkdir(parents=True,exist_ok=True)
        path=folder/(str(time.time_ns())+'.jsonl')
        a=append_file(path,None,dict(quantity='synthetic-M3'));before=path.read_bytes()
        append_file(path,a['sha256'],dict(quantity='synthetic-M2'))
        self.assertTrue(path.read_bytes().startswith(before));validate_chain([json.loads(x) for x in path.read_text().splitlines()])
        original=path.read_bytes()
        with self.assertRaises(ValueError):append_file(path,None,dict(quantity='override'))
        self.assertEqual(path.read_bytes(),original)
    def test_json_nan_not_serializable(self):
        with self.assertRaises(ValueError):chain_append([],dict(value=float('nan')))
    def test_rehashed_history_edit_rejected(self):
        old=chain_append([],dict(event='first'));new=chain_append([],dict(event='edited'))
        validate_chain(new)
        with self.assertRaisesRegex(ValueError,'history_rewritten'):validate_extension(old,new)
    def test_git_blob_and_append_only_ancestry(self):
        import time
        folder=Path('temp/registration-batch2/synthetic-protocol-files')/(str(time.time_ns())+'-repo')
        folder.mkdir(parents=True)
        def git(*args):
            return subprocess.check_output(['git',*args],cwd=folder,stderr=subprocess.PIPE,text=True).strip()
        git('init','-q','-b','main')
        def commit(data):
            blob=b''.join(encode(row)+b'\n' for row in data);(folder/'events.json').write_bytes(blob)
            git('add','--','events.json')
            git('-c','user.name=Hao Lin','-c','user.email=hao.lin@samsung.com','-c','commit.gpgsign=false','commit','-q','-m','synthetic fixture')
            rev=git('rev-parse','HEAD');git('update-ref','refs/remotes/origin/main',rev)
            return dict(path='events.json',sha256=hashlib.sha256(blob).hexdigest(),commit=rev)
        first=chain_append([],dict(event='original'));ref=commit(first);reader=GitEvidence(folder)
        self.assertEqual(reader.read(ref),first)
        extended=chain_append(first,dict(event='second'));self.assertEqual(reader.read(commit(extended)),extended)
        rewrite=chain_append([],dict(event='changed'));ref=commit(rewrite)
        with self.assertRaisesRegex(ValueError,'history_rewritten'):reader.read(ref)
    def test_unpushed_registration(self):
        p,s,e,r,reg,req=gate_fixture();r.pushed.remove(reg['sha256'])
        with self.assertRaisesRegex(ValueError,'not_pushed'):admit_computation(req,reg,r)
    def test_synthetic_allowed(self):self.assertEqual(admit_computation(dict(data_kind='synthetic'),None,SyntheticStore()),dict(synthetic=True))
    def test_synthetic_label_cannot_carry_real_originals(self):
        with self.assertRaisesRegex(ValueError,'real_input_references'):
            admit_computation(dict(data_kind='synthetic',originals=['real-sha']),None,SyntheticStore())
    def test_old_initialization_missing_blocks_interpretation(self):
        p,s,e,r,reg,req=gate_fixture();records=[x['payload'] for x in e if x['payload'].get('slot')!='0'];chain=[]
        for record in records:chain=chain_append(chain,record)
        req['receipts']=r.put(chain)
        with self.assertRaisesRegex(ValueError,'initialization_receipt'):admit_computation(req,reg,r)
    def test_current_locked_script_changed(self):
        p,s,e,r,reg,req=gate_fixture();h=r.read(reg)['locked_artifacts'][0]['sha256']
        r.current[h]={'static':'changed'}
        with self.assertRaisesRegex(ValueError,'working_artifact'):admit_computation(req,reg,r)
    def test_script_hash_changed(self):
        p,s,e,r,reg,req=gate_fixture();req['scripts_sha256']='new'
        with self.assertRaises(ValueError):admit_computation(req,reg,r)
    def test_failed_gate_does_not_open_inputs(self):
        touched=[]
        with self.assertRaises(ValueError):compute_guarded(dict(data_kind='real'),None,SyntheticStore(),lambda permit:touched.append(True))
        self.assertEqual(touched,[])
    def test_duplicate_log_payload_mutation_detected(self):
        log=chain_append([],dict(quantity='M3'));log=chain_append(log,dict(quantity='M2'));log[0]['payload']['quantity']='M1'
        with self.assertRaises(ValueError):validate_chain(log)


if __name__=='__main__':unittest.main()
