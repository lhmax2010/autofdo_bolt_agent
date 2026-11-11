"""v1.8 registration, append-only evidence and acquisition state gates.

Pure replay core, plus a Git blob verifier and atomic append-only JSONL writer.
No acquisition, profile loading, simulation or quality computation occurs here.
Schemas are explicit implementation choices; all evidence values must come from
sealed, SHA-checked documents. Synthetic fixtures use an in-memory blob store.
"""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess

CONTROLLED = {'M1','M2','M2b','M3','branch_probability_error','region_sensitivity','merge_sensitivity'}
IRRECOVERABLE = {'identity_mismatch','build_id_mismatch','sha_mismatch','hardware_event_error'}
TERMINAL = {'success','exhausted','stopped_missing'}


def encode(data):
    return json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()


def digest(data):return hashlib.sha256(encode(data)).hexdigest()


def chain_append(records,payload):
    validate_chain(records)
    record=dict(index=len(records),previous=records[-1]['sha256'] if records else None,payload=copy.deepcopy(payload))
    record['sha256']=digest(record)
    return records+[record]


def validate_chain(records):
    previous=None
    for i,r in enumerate(records):
        expected={k:v for k,v in r.items() if k!='sha256'}
        if r['index']!=i or r['previous']!=previous or digest(expected)!=r['sha256']:
            raise ValueError('broken_append_only_sha_chain')
        previous=r['sha256']
    return True


def validate_extension(old,new):
    validate_chain(old);validate_chain(new)
    if len(new)<len(old) or new[:len(old)]!=old:raise ValueError('pushed_append_only_history_rewritten')
    return True


def append_file(path,expected_tip,payload):
    """Serialize append under an advisory lock; reject replacement/truncation.

The complete previously pushed chain must additionally be checked by the caller
before appending. No rewrite-in-place or human override operation exists.
"""
    import fcntl
    path=Path(path)
    with path.open('a+b') as f:
        fcntl.flock(f,fcntl.LOCK_EX);f.seek(0)
        records=[json.loads(line) for line in f if line.strip()]
        validate_chain(records)
        tip=records[-1]['sha256'] if records else None
        if tip!=expected_tip:raise ValueError('append_tip_mismatch')
        new=chain_append(records,payload)[-1]
        f.seek(0,os.SEEK_END);f.write(encode(new)+b'\n');f.flush();os.fsync(f.fileno())
        return new


def decode_document(raw):
    try:
        data=json.loads(raw)
        if isinstance(data,dict) and {'index','previous','payload','sha256'}<=data.keys():
            validate_chain([data]);return [data]
        return data
    except json.JSONDecodeError:
        records=[json.loads(line) for line in raw.splitlines() if line.strip()]
        validate_chain(records)
        return records


class GitEvidence:
    """Read a locked blob only if its commit is present in origin/main history.

This verifier uses existing Git configuration; it never fetches or changes auth.
Callers refresh origin/main outside this read-only API before evaluation.
"""
    def __init__(self,repo):self.repo=Path(repo).resolve()
    def read(self,ref):
        path=Path(ref['path']);commit=ref['commit']
        if path.is_absolute() or '..' in path.parts or len(commit)!=40 or any(c not in '0123456789abcdef' for c in commit):
            raise ValueError('invalid_evidence_reference')
        p=subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=self.repo,capture_output=True)
        if p.returncode:raise ValueError('evidence_not_pushed')
        p=subprocess.run(['git','show',commit+':'+str(path)],cwd=self.repo,capture_output=True)
        if p.returncode or hashlib.sha256(p.stdout).hexdigest()!=ref['sha256']:raise ValueError('evidence_blob_sha_mismatch')
        data=decode_document(p.stdout)
        if isinstance(data,list) and data and isinstance(data[0],dict) and 'previous' in data[0] and 'sha256' in data[0]:
            validate_chain(data)
            # Pushed history must also be append-only. Rehashing an edited chain
            # does not excuse replacement of a previously committed event.
            history=subprocess.run(['git','rev-list','--reverse',commit,'--',str(path)],cwd=self.repo,capture_output=True,text=True,check=True)
            previous=[]
            for revision in history.stdout.splitlines():
                blob=subprocess.run(['git','show',revision+':'+str(path)],cwd=self.repo,capture_output=True)
                if blob.returncode:raise ValueError('append_only_file_deleted_in_history')
                observed=decode_document(blob.stdout);validate_extension(previous,observed);previous=observed
        return data

    def verify_current(self,ref):
        path=(self.repo/ref['path']).resolve()
        if not path.is_relative_to(self.repo):raise ValueError('locked_artifact_outside_worktree')
        h=hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda:f.read(1048576),b''):h.update(block)
        if h.hexdigest()!=ref['sha256']:raise ValueError('working_artifact_not_registered')
        return True


def sealed(ref,reader):
    # reader verifies the byte SHA, not a caller-provided "pushed" boolean.
    return reader.read(ref)


def validate_slots(protocol,slots):
    if digest(slots)!=protocol['slots_sha256']:raise ValueError('slot_table_tampered')
    if len(slots)!=15 or len({s['slot'] for s in slots})!=15:raise ValueError('exactly_15_unique_slots_required')
    phases={}
    for s in slots:
        phases[s['phase']]=phases.get(s['phase'],0)+1
        if s['origin'] not in ('existing','future'):raise ValueError('invalid_slot_origin')
        if s['conditions_sha256']!=protocol['conditions_sha256']:raise ValueError('slot_conditions_changed')
        if s['origin']=='existing' and (not s.get('originals') or not s.get('run_id')):raise ValueError('old_input_not_registered')
        if s['origin']=='future' and (s.get('originals') or s.get('run_id')):raise ValueError('future_slot_already_has_input')
    if phases!=protocol['phase_counts'] or any(n<2 for n in phases.values()):raise ValueError('phase_plan_mismatch')
    if any(s['origin']=='existing' for s in slots) and sum(s['origin']=='existing' for s in slots)<5:
        raise ValueError('fewer_than_5_existing_runs_must_not_be_used')
    return True


def attempt_outcome(facts,whitelist):
    """Stop conditions precede success and whitelist retry; no inference by absence."""
    if facts.get('conversion_failure') or facts.get('telemetry_only'):
        raise ValueError('conversion_or_telemetry_not_acquisition_recovery')
    errors=set(facts.get('stop_errors',[]))
    if errors & IRRECOVERABLE:return 'paused_stop'
    if facts.get('transfer_complete') and facts.get('sha_match') is False:return 'paused_stop'
    if facts.get('transfer_interrupted') and facts.get('remote_originals_intact'):
        return 'transfer_pending'
    if facts.get('transfer_complete') and facts.get('sha_match') is False:return 'paused_stop'
    if not facts.get('stderr_saved'):return 'paused_stop'
    if facts['exit_code']==0 and facts.get('transfer_complete') and facts.get('sha_match') is True and not errors:
        return 'success'
    reason=facts.get('retry_reason')
    required=whitelist.get(reason)
    evidence=facts.get('positive_evidence',{})
    if not errors and reason and required and all(evidence.get(k) is True for k in required):return 'retryable'
    return 'paused_stop'


def validate_recovery(stop,recovery,reader,protocol):
    if stop['attempt']>=4:raise ValueError('attempt_limit_cannot_recover')
    if set(stop['facts'].get('stop_errors',[])) & IRRECOVERABLE or (stop['facts'].get('transfer_complete') and stop['facts'].get('sha_match') is False):raise ValueError('irrecoverable_stop')
    if recovery['stop_sha256']!=stop['event_sha256']:raise ValueError('wrong_stop_reference')
    if recovery['conditions_sha256']!=protocol['conditions_sha256']:raise ValueError('recovery_is_protocol_change')
    fault=sealed(recovery['fault'],reader);current=sealed(recovery['current'],reader);identity=sealed(recovery['identity'],reader)
    for d in (fault,current,identity):
        if d['attempt_id']!=stop['attempt_id'] or d['boot_id']!=stop['facts']['boot_id']:
            raise ValueError('recovery_attempt_or_boot_mismatch')
        if not math.isfinite(d['monotonic']):raise ValueError('invalid_evidence_time')
    if abs(fault['monotonic']-stop['facts']['monotonic'])>10:raise ValueError('fault_outside_10_second_window')
    if not fault.get('recorded_by_failure_handler'):raise ValueError('failure_handler_evidence_missing')
    if current['monotonic']<=fault['monotonic'] or identity['monotonic']<current['monotonic']:
        raise ValueError('stale_recovery_evidence')
    action=fault.get('stop_action');reason=recovery['reason']
    if not action or action['attempt_id']!=stop['attempt_id'] or action['boot_id']!=stop['facts']['boot_id']:
        raise ValueError('no_associated_stop_action')
    if abs(action['monotonic']-stop['facts']['monotonic'])>10:raise ValueError('stale_stop_action')
    limits=protocol['limits']
    if reason=='space':
        if action['kind']!='space_check_failed' or fault['available_bytes']>=limits['min_free_bytes']:
            raise ValueError('space_cause_not_proven')
    elif reason=='thermal':
        if action['kind']!='thermal_stop' or not fault['temperatures'] or max(fault['temperatures'])<limits['stop_temperature']:
            raise ValueError('thermal_cause_not_proven')
    elif reason=='manual':
        if action['kind']!='manual_stop' or not recovery.get('resume_instruction'):
            raise ValueError('manual_cause_or_resume_not_proven')
    else:raise ValueError('unregistered_recovery_reason')
    finite_state = [fault['available_bytes'],current['available_bytes'],*fault['temperatures'],*current['temperatures']]
    if any(isinstance(x,bool) or not math.isfinite(x) for x in finite_state):raise ValueError('nonfinite_recovery_state')
    if current['available_bytes']<limits['min_free_bytes'] or not current['temperatures'] or max(current['temperatures'])>=limits['start_temperature']:
        raise ValueError('start_conditions_not_restored')
    if identity['observed']!=protocol['identity']:raise ValueError('identity_recheck_failed')
    return True


def replay(protocol,slots,events,reader):
    validate_slots(protocol,slots);validate_chain(events)
    states={s['slot']:dict(state='ready',attempts=0,slot=s) for s in slots}
    originals={};successes={};paused=False
    for record in events:
        e=record['payload'];kind=e['kind']
        if kind=='stopped_missing':
            if not paused:raise ValueError('end_without_stop')
            for st in states.values():
                if st['state'] not in TERMINAL:st['state']='stopped_missing'
            paused=False;continue
        if kind=='recovery':
            st=states[e['slot']]
            if st['state']!='paused_stop' or not paused:raise ValueError('recovery_without_active_stop')
            validate_recovery(st['stop'],e,reader,protocol)
            st['state']='ready';st['recovery_sha256']=record['sha256'];paused=False;continue
        sid=e['slot']
        if sid not in states:raise ValueError('unregistered_slot')
        st=states[sid];slot=st['slot']
        if st['state'] in TERMINAL:raise ValueError('terminal_slot_is_immutable')
        if paused:raise ValueError('attempt_before_pushed_recovery')
        if e['conditions_sha256']!=protocol['conditions_sha256']:raise ValueError('changed_acquisition_conditions')
        if kind=='initialization':
            if slot['origin']!='existing' or st['attempts'] or e['run_id']!=slot['run_id'] or e['originals']!=slot['originals']:
                raise ValueError('invalid_old_run_initialization')
            for ref in ['collection_receipt','reception_receipt']:
                proof=sealed(e[ref],reader)
                if proof['run_id']!=slot['run_id'] or proof['originals']!=slot['originals']:
                    raise ValueError('initialization_receipt_identity_mismatch')
            if not e.get('imported_at') or e['collected_at']>=protocol['registered_at']:
                raise ValueError('old_run_masquerading_as_new')
            outcome='success';st['attempts']=1
        elif kind in ('attempt','transfer'):
            if slot['origin']=='existing':raise ValueError('existing_run_requires_initialization')
            if kind=='transfer':
                if st['state']!='transfer_pending' or e['attempt']!=st['attempts'] or e['attempt_id']!=st['attempt_id']:
                    raise ValueError('transfer_must_reference_same_attempt')
                if e['originals']!=st['pending_originals'] or e['run_id']!=st['pending_run_id']:
                    raise ValueError('transfer_must_keep_same_originals')
            else:
                if st['state']=='transfer_pending':raise ValueError('transfer_failure_is_not_recapture')
                if type(e['attempt']) is not int or e['attempt']!=st['attempts']+1 or e['attempt']>4:raise ValueError('attempt_sequence_or_limit')
                if st.get('recovery_sha256') and e.get('recovery_sha256')!=st['recovery_sha256']:raise ValueError('missing_recovery_reference')
                st['attempts']=e['attempt'];st['attempt_id']=e['attempt_id']
            if e['collected_at']<protocol['registered_at']:raise ValueError('old_run_masquerading_as_new')
            outcome=attempt_outcome(e['facts'],protocol['retry_whitelist'])
        else:raise ValueError('unknown_event_kind')
        if e['automatic_outcome']!=outcome:raise ValueError('manual_outcome_override')
        if outcome=='success':
            if not e['originals'] or len(set(e['originals']))!=len(e['originals']):raise ValueError('success_without_unique_originals')
            for original in e['originals']:
                if original in originals and originals[original]!=sid:raise ValueError('one_original_two_slots')
                originals[original]=sid
            st['state']='success';successes[sid]=e
        elif outcome=='paused_stop':
            st['state']='paused_stop';paused=True
            st['stop']=dict(e,event_sha256=record['sha256'])
        elif outcome=='transfer_pending':
            st['state']='transfer_pending';st['pending_originals']=e['originals'];st['pending_run_id']=e['run_id']
        else:st['state']='exhausted' if st['attempts']==4 else 'ready'
    return dict(states=states,successes=successes,originals=originals,
                terminal=all(st['state'] in TERMINAL for st in states.values()),paused=paused)


def admit_computation(request,registration_ref,reader):
    """Call BEFORE touching any real input or computing any controlled quantity.

Requires an already-pushed calculation-intent chain entry, not a promise to log
later. The same permit covers primary and sensitivity branches; unknown quality
quantities are controlled by default rather than silently exempted.
"""
    if request.get('data_kind')=='synthetic':
        if registration_ref or request.get('originals') or request.get('input_files') or request.get('receipts'):
            raise ValueError('synthetic_gate_does_not_accept_real_input_references')
        return dict(synthetic=True)
    if not registration_ref:raise ValueError('amendment3_not_registered_and_pushed')
    registration=sealed(registration_ref,reader)
    if registration['kind']!='amendment3':raise ValueError('not_amendment3')
    protocol=sealed(registration['protocol'],reader);slots=sealed(registration['slots'],reader)
    for ref in registration['locked_artifacts']:
        sealed(ref,reader);reader.verify_current(ref)
    events=sealed(request['receipts'],reader);log=sealed(request['calculation_log'],reader)
    validate_chain(log)
    if not log:raise ValueError('calculation_log_missing')
    intent=log[-1]['payload']
    for field in ['originals','configuration','scripts_sha256','quantity','time']:
        if intent[field]!=request[field]:raise ValueError('calculation_intent_mismatch:'+field)
    if request['scripts_sha256']!=protocol['scripts_sha256']:raise ValueError('analysis_code_not_registered')
    result=replay(protocol,slots,events,reader)
    if result['paused']:raise ValueError('acquisition_paused_stop')
    if not set(request['originals'])<=result['originals'].keys():raise ValueError('originals_not_in_successful_slots')
    if any(st['slot']['origin']=='existing' and st['state']!='success' for st in result['states'].values()):
        raise ValueError('existing_run_missing_initialization_receipt')
    if request.get('interpretation') and not result['terminal']:raise ValueError('all_slots_must_have_terminal_receipts')
    return dict(synthetic=False,registration_sha256=registration_ref['sha256'],
                intent_sha256=log[-1]['sha256'],all_slots_terminal=result['terminal'])


def compute_guarded(request,registration_ref,reader,operation):
    """The operation may open data only after the permit is obtained."""
    permit=admit_computation(request,registration_ref,reader)
    return operation(permit)
