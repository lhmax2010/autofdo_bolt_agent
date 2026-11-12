"""Batch3 clause index and provenance; only metadata/static/synthetic outputs."""
import ast,collections,json,re,subprocess
from pathlib import Path
from run_scoped import WORK,sha
from registration_address_check import BASE,TOOL,TOOL_SHA,dump

OUT=BASE/"registration-checks/batch3"
DESIGN=WORK/"docs/profgen/design/02_llvm_profgen_enhance_design_v1.8.md"


def main():
    assert sha(TOOL)==TOOL_SHA
    lines=DESIGN.read_text().splitlines();records=[]
    tests={}
    for path in (WORK/"tools/profgen_eval").glob("test_*.py"):
        tree=ast.parse(path.read_text())
        tests[path.stem]={n.name:n.lineno for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name.startswith("test_")}
    def row(item,clause,implementation,refs,status="PASS"):
        linked=[]
        for module,names in refs:
            for name in names.split():
                assert name in tests[module],(module,name)
                linked.append(f"tools/profgen_eval/{module}.py:{tests[module][name]}#{name}")
        records.append(dict(item=item,clause=clause,implementation=implementation,fixtures=linked,result=status))
    perf="test_registration_performance";tele="test_registration_telemetry";ordinary="test_ordinary_identity_rule"
    identity="test_registration_identity";mapping="test_registration_mapping"
    for clause,names in [
        ("从登记矩阵自动校验每组参数","test_matrix_complete test_each_group_parameters test_lto_requires_same_parameters test_G0_G5"),
        ("缺少补零对照时拒绝输出补零默认值已验证；小矩阵须披露固定项与未评估交互","test_small_matrix_no_default_claim test_omission_must_be_disclosed"),
        ("质量与性能统计量、ε、停止规则不混用；关闭质量判读不改变性能规则","test_quality_rules_rejected test_disable_quality_leaves_performance test_insufficient_no_extension"),
        ("超过登记N拒绝新轮次","test_N_exhausted test_normal_round"),
        ("CV .5%→13，1%→40，0→10，缺失/NaN/Infinity→40；四位有效数字","test_cv_half_percent test_cv_one_percent test_cv_zero test_cv_missing test_cv_nan test_cv_infinity test_cv_four_significant_digits"),
        ("预试离群不剔除；预热移除；旧镜像不用于CV；G0预试不进入正式轮次","test_outlier_is_retained test_warmup_removed test_old_image_not_cv test_pretrial_excluded test_warmup_excluded")]:
        row("11",clause,"tools/profgen_eval/registration_performance.py",[(perf,names)])
    telemetry_names=[
        "test_alarm_transient","test_alarm_late_driver_update","test_undervoltage_two_seconds_after_workload",
        "test_outside_log_clock_looks_inside","test_log_gap test_EPIPE","test_query_failure_boot_sticky",
        "test_cpuinfo_deviation_then_recovery","test_policy_max_drop","test_calibration_1_44","test_calibration_slow_and_1_44",
        "test_calibration_1_015 test_calibration_1_025 test_calibration_time_boundaries","test_busy98_warning","test_busy98_low_still_abnormal test_busy98_invalid_still_unknown",
        "test_24_intervals","test_one_invalid_interval","test_all_truncated test_early_exit test_PMU_not_counted",
        "test_first_seq37_reject_admission test_log_gap test_save_failed_does_not_advance","test_boot_change_without_restart",
        "test_recorder_output_invalid","test_buffer_wrap_between_endpoints","test_empty_log_window","test_endpoints_cross_boot",
        "test_first_seq37_reject_admission","test_background_saved_undervoltage_no_new_endpoint","test_policy_missing_after_workload",
        "test_post_calibration_abnormal_whole_batch","test_one_hot_other_unknown_missing_post","test_temperature_75",
        "test_hot_and_missing_sensor","test_gap_1_5 test_gap_1_6 test_gap_3_0 test_gap_3_01","test_three_gaps",
        "test_each_sensor_separate","test_no_postworkload_readings","test_unknown_reading test_read_timeout test_invalid_temperature test_temperature_75",
        "test_MAD_floor_identical15","test_frequency_outlier_flag_only","test_frequency_confounding","test_all_normal",
        "test_hot_and_missing_sensor","test_all_normal"]
    clauses=lines[662].split("情形：",1)[1].split("；")
    assert len(clauses)==len(telemetry_names)
    for i,(clause,names) in enumerate(zip(clauses,telemetry_names)):
        status="PASS"
        if i==37:status="PASS; 四核原件重放abnormal，见telemetry-replay-summary.json"
        if i==38:status="PASS; 每RUN独立缺失，未借用其他RUN传感器"
        if i==39:status="离线PASS，旧标签SHA未变；加装散热后的板上正对照留第12项，本批不执行"
        row("14 / 5.9.5",clause,"tools/profgen_eval/registration_telemetry.py",[(tele,names)],status)
    row("14 / Q.5",lines[2154],"tools/profgen_eval/registration_telemetry.py",[(tele,
        "test_prior_authorization_still_unknown test_posthoc_authorization_rejected test_later_normal_cannot_clear_unknown test_real_nonblocking_fd_EAGAIN test_blocking_fd_rejected test_mock_sysfs_directory")])
    idnames=[
      [(ordinary,"test_brace_on_next_line test_three_line_signature")],
      [(ordinary,"test_codex_conditional_wrong_definition")],
      [(ordinary,"test_empty_lines_not_vacuous_proof")],
      [("test_ruling34","test_19_rev2_nonleaf_zero_empty_evidence_exempt test_20_rev2_nonleaf_zero_outside_not_exempt test_21_rev2_nonleaf_zero_mixed_files_not_exempt")],
      [("test_v17_rules","test_missing_range test_top_boundary_failure test_deleted_instance_record test_symbolization_failure test_missing_record_cannot_receive_zero_exemption")],
      [(ordinary,"test_signature_line")],[(ordinary,"test_line_in_other_definition")],[(identity,"test_variant_mismatch")],
      [(ordinary,"test_linkage_precedence test_specification_and_abstract_origin"),(identity,"test_only_MIPS")],
      [(ordinary,"test_same_decl_different_body_ambiguous test_no_nearest_candidate")],
      [(mapping,"test_hot_parent_normal_and_ambiguous_inline")],
      [(identity,"test_GNU_C_positive test_GNU_AS_positive"),(mapping,"test_known_outside_group")],
      [(ordinary,"test_external_group_does_not_hide_executed_inline")],
      [(ordinary,"test_unique_suffix_only"),(identity,"test_omitted_suffix_normalization_missing")],
      [(identity,"test_mangling_mismatch test_omitted_suffix_normalization_missing")],
      [(identity,"test_unresolved_outside_static test_unresolved_clone test_tiny_unresolved_no_matched_outer test_full_inventory_not_selection")],
      [(identity,"test_CU_filename_wrong test_producer_missing test_producer_parse_failed")],
      [(identity,"test_reference_candidate_before_external")],[(identity,"test_clang_missing_coverage_is_unresolved")],
      [(identity,"test_partial_path_normalization_fails")],
      [(mapping,"test_two_translation_units_one_executed"),(ordinary,"test_unexecuted_reference")],
      [],[]]
    clauses=lines[2156].split("夹具：",1)[1].split(" | ")[0].split("；")
    assert len(clauses)==len(idnames)
    for i,(clause,refs) in enumerate(zip(clauses,idnames)):
        row("16",clause,"tools/profgen_eval/registration_identity.py; ordinary_identity_rule.py; dwarf_inventory.py; ruling34_rules.py; v17_rules.py; registration_mapping_checks.py",refs,
            "PASS; identity-audit-summary.json（四对象同名范围外均0）" if i==21 else
            "PASS; *-external-CUs-*.csv（FFmpeg各10 CU，spike0）" if i==22 else "PASS (synthetic; existing tests retained)")
    row("6 / avg","同SHA合成全地址avg/none、avg/prev-inst；仅分类和可用性","tools/profgen_eval/registration_avg_availability.py",[],
        "PASS; 8 conversions; avg-plan.json / *-classification.json")
    row("17","历史打开清单与计算内容；合并CALIBRATION披露，G0待12","tools/profgen_eval/registration_history_disclosure.py",[],
        "metadata-only disclosure; G0待第12项；失败/未证实生成的路径单列")
    dump(OUT/"clause-mapping.json",dict(design_sha256=sha(DESIGN),records=records))
    text=["# Q.5 第三批逐条对应","", "|项目|条文原文/拆分|实现|夹具与结果|","|---|---|---|---|"]
    for r in records:
        text.append("|"+ "|".join(str(v).replace("|","\\|").replace("\n"," ") for v in
          (r["item"],r["clause"],r["implementation"],"; ".join(r["fixtures"])+"; "+r["result"]))+"|")
    (OUT/"clause-mapping.md").write_text("\n".join(text)+"\n")
    # Existing tests / static artifacts are not edited.
    git=["git","-c","gc.auto=0","-c","maintenance.auto=false"]
    old=subprocess.check_output(git+["ls-tree","-r","--name-only","c5ad459","tools/profgen_eval"],text=True).splitlines()
    unchanged=[]
    for f in old:
        if not Path(f).name.startswith("test_"):continue
        original=subprocess.check_output(git+["show","c5ad459:"+f])
        assert original==(WORK/f).read_bytes(),f
        unchanged.append(f)
    draft=OUT/"object-seal-draft.json"
    dump(OUT/"validation-summary.json",dict(old_test_files_unchanged=unchanged,formal_tool_sha256=sha(TOOL),
        design_sha256=sha(DESIGN),object_draft_sha256=sha(draft),clauses=len(records),
        old_object_draft_sha256=sha(BASE/"registration-checks/batch2/object-seal-draft.json"),
        tests_output="tests-acceptance/stderr.txt",not_amendment3=True))
    print(json.dumps(dict(clauses=len(records),original_test_files=len(unchanged))))


if __name__=="__main__":main()
