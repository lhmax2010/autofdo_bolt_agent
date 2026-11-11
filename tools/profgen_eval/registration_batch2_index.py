"""Build clause-to-code/test evidence from saved test logs. No profile reader."""
import ast
import collections
import json
import re
from pathlib import Path
from run_scoped import WORK, sha
from registration_address_check import dump

BASE=WORK/'docs/profgen/eval/prep/evidence/registration-checks/batch2'
DESIGN=WORK/'docs/profgen/design/02_llvm_profgen_enhance_design_v1.8.md'

M7=[
 ('line_metrics','n15_k9_all_sample_zero'),('line_metrics','single_positive_hot'),
 ('line_metrics','positive_tie_cutoff'),('line_metrics','positive_shortfall_no_zero_padding'),
 ('line_metrics','total_zero'),('line_metrics interpretation','empty_u'),('interpretation','undefined_k'),
 ('interpretation','null_neff_k5 null_neff_k49 null_neff_k50'),('interpretation','null_neff_k80_every_gate'),
 ('interpretation','neff_exact_three_joint'),('line_metrics','ten_line_sensitivity_empty'),
 ('hot_reference','exact_eighty_percent just_cross_eighty_percent')]
M8=[('merge_lines','complementary_contexts'),('merge_lines','inline_two_sites_different_branches'),
 ('merge_lines','multiple_regions_and_discriminators'),('merge_lines','unexecuted_template_same_line'),
 ('merge_lines','multiple_regions_and_discriminators')]
M10=[
 ('paired_differences','pairs_order_by_id'),('paired_differences assess_paired_metrics','one_sided_missing_and_failed missing_pair_not_reweighted_in_adapter'),
 ('paired_differences','one_sided_missing_and_failed'),('paired_differences','multiple_segments_one_run'),
 ('interpretation','five_runs_no_interpretation'),('phase_diagnostics validate_slots','three_plus_twelve_flat_counterexample three_plus_twelve_not_admitted'),
 ('phase_diagnostics','half_grid_positive_and_negative'),('phase_diagnostics','translation'),
 ('phase_diagnostics','resolution_exact resolution_nextafter resolution_below'),('phase_diagnostics','small_real_variation'),
 ('phase_diagnostics','fraction_sum_order'),('phase_diagnostics stratified_t','constant_nonzero_phase single_phase_flat'),
 ('stratified_t','stratified_mean_is_ordinary'),('stratified_t','single_phase_paired_t t_quantile_exact_df1_df2'),
 ('finite','nonfinite_never_silently_dropped'),('intervals_joint interpretation','envelope_iff_double_pass'),
 ('interpretation','model_identifier_required'),('interpretation','global_false_all_objects_and_sensitivity'),
 ('outliers','outlier_normal_and_isolated'),
 ('validate_slots replay admit_computation validate_chain','old5_new10_all_legal old_initialization_missing_blocks_interpretation tampered_slots old_masquerades_new duplicate_original_in_two_slots sixteenth_slot success_twice manual_outcome_override fourteenth_slot_not_terminal broken_log_chain unpushed_receipts'),
 ('attempt_outcome replay','unknown_nonzero_stops whitelist_positive_evidence_retries overheat_nonzero_stops_not_retry stderr_missing_stops transfer_only_does_not_consume_attempt complete_transfer_sha_mismatch_stops'),
 ('validate_recovery replay','unknown_stop_with_valid_causal_evidence narrative_only_not_evidence space_df_normal temperature_timestamp_outside_ten_seconds space_not_restored temperature_not_restored unassociated_high_temperature_ends_missing hardware_overrides_thermal manual_command_other_attempt failure_handler_did_not_save_evidence fixed_fault_correct_association success_without_recovery recovery_changes_conditions stop_on_fourth_cannot_recover stopped_missing_is_terminal hardware_overrides_thermal telemetry_or_conversion_not_recovery'),
 ('admit_computation compute_guarded','pre_registration_m3_or_branch_rejected post_registration_missing_calculation_log failed_gate_does_not_open_inputs'),
 ('comparisons','fixed_interval_no_weight_comparison'),('admit_computation','synthetic_allowed')]


def main():
    code={};tests={};counts=collections.Counter()
    for name in ['registration_statistics','registration_protocol']:
        p=WORK/'tools/profgen_eval'/(name+'.py')
        for node in ast.walk(ast.parse(p.read_text())):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                code[node.name]=dict(path=str(p.relative_to(WORK)),line=node.lineno)
    test_log=(BASE/'tests-acceptance-final/stderr.txt').read_text()
    for name in ['test_registration_statistics','test_registration_protocol','test_registration_calibration']:
        p=WORK/'tools/profgen_eval'/(name+'.py')
        for cls in ast.parse(p.read_text()).body:
            if not isinstance(cls,ast.ClassDef):continue
            for fn in cls.body:
                if not isinstance(fn,ast.FunctionDef) or not fn.name.startswith('test_'):continue
                full=name+'.'+cls.name+'.'+fn.name
                assert fn.name+' ('+full+') ... ok' in test_log,full
                tests[fn.name[5:]]=dict(fixture=full,path=str(p.relative_to(WORK)),line=fn.lineno,result='PASS',synthetic=True)
                counts[cls.name]+=1
    lines=DESIGN.read_text().splitlines();mapping=[]
    for item,line,items in [(7,2148,M7),(8,2149,M8),(10,2151,M10)]:
        clauses=lines[line-1].split('|')[2].strip().split('；')
        assert len(clauses)==len(items)
        for i,(clause,(functions,fixtures)) in enumerate(zip(clauses,items),1):
            mapping.append(dict(item=item,clause=i,original=clause,design_line=line,
              implementation=[dict(function=f,**code[f]) for f in functions.split()],
              fixtures=[tests[f] for f in fixtures.split()],result='PASS'))
    dump(BASE/'clause-mapping.json',dict(design=str(DESIGN.relative_to(WORK)),design_sha256=sha(DESIGN),clauses=mapping,
      tests_by_class=counts,all_added_tests=list(tests.values()),test_log_sha256=sha(BASE/'tests-acceptance-final/stderr.txt')))
    md=['# Q.5 第7、8、10项逐条验收','', '全部为 synthetic；未运行第9项模拟。原文按分号展开（含括号内分号），复合条款的每个子例均列测试。','',
        '|条文|原文|实现位置|夹具|结果|','|---|---|---|---|---|']
    for r in mapping:
        impl='<br>'.join(x['path']+':'+str(x['line'])+' '+x['function'] for x in r['implementation'])
        fixtures='<br>'.join(x['fixture'] for x in r['fixtures'])
        md.append('|'+str(r['item'])+'.'+str(r['clause'])+'|'+r['original'].replace('|',r'\|')+'|'+impl+'|'+fixtures+'|PASS|')
    (BASE/'clause-mapping.md').write_text('\n'.join(md)+'\n')
    resources=[dict(path=str(p.relative_to(WORK)),**json.loads(p.read_text())) for p in BASE.glob('*/resources.json')]
    admissions=[int(next(l.split()[1] for l in p.read_text().splitlines() if l.startswith('MemAvailable:')))*1024 for p in BASE.rglob('*meminfo*.txt')]
    extra=BASE/'git-autogc-monitor.json'
    if extra.exists():
        gc=json.loads(extra.read_text());assert not gc['still_running']
        admissions += [int(next(l.split()[1] for l in r['meminfo'].splitlines() if l.startswith('MemAvailable:')))*1024 for r in gc['records']]
        resources.append(dict(path=str(extra.relative_to(WORK)),memory_peak_bytes=max(int(r['settings']['memory.peak']) for r in gc['records']),resource_terminated=False,min_memavailable=min(admissions),automatic_git_maintenance=True))
    dump(BASE/'resource-summary.json',dict(scopes=resources,min_memavailable=min(admissions+[x['min_memavailable'] for x in resources]),
      peak_cgroup_bytes=max(x['memory_peak_bytes'] for x in resources),resource_terminated=any(x['resource_terminated'] for x in resources),
      limit='3G',cpu='200%',nice=19,ionice='-c3',serial=True))
    files=[]
    for path in sorted(BASE.rglob('*')):
        if path.is_file() and path.name!='manifest.json':
            assert path.stat().st_size<1000000, path
            files.append(dict(path=str(path.relative_to(WORK)),bytes=path.stat().st_size,sha256=sha(path)))
    sources=[]
    for name in ['registration_availability','registration_batch2_index','registration_calibration','registration_calibration_detail','registration_protocol','registration_statistics','test_registration_calibration','test_registration_protocol','test_registration_statistics']:
        path=WORK/'tools/profgen_eval'/(name+'.py');sources.append(dict(path=str(path.relative_to(WORK)),sha256=sha(path)))
    raw=[]
    for path in BASE.glob('cal-*/before-classification.json'):
        d=json.loads(path.read_text());raw.append(dict(path=d['path'],sha256=d['sha256'],purpose='CALIBRATION entry classification only'))
    dump(BASE/'manifest.json',dict(base_commit='ef57cd80630fe17c987b57370af7fcb519b2d0a1',
      evidence=files,sources=sources,raw_temp_outputs=raw,tests=410,original_tests=296,new_tests=sum(counts.values()),
      no_amendment3=True,no_board=True,no_non_calibration_profiles_opened=True))
    print(json.dumps(dict(clauses=len(mapping),tests_by_class=counts,added_tests=sum(counts.values()))))

if __name__=='__main__':main()
