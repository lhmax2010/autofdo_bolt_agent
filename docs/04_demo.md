# Host-only demo

No board is required. Use the release RPMs and the fixed Gerrit sandbox source identified in the [README](../README.md). The script references existing sandbox fixtures; it does not ship copied LLVM files.

## Run

Set DOCS, PROJECT, ROOT and EXTRACTED as in README quick start. ROOT is the GBS scratch root and EXTRACTED contains the extracted llvm and libllvm RPMs. The output directory must not already exist.

```bash
bash "$DOCS/demo/run_host_demo.sh" "$PROJECT/llvm" "$EXTRACTED" "$ROOT" "$PROJECT/demo-output"
```

The script verifies the source HEAD, converts the AArch64 a64-pie and Thumb thumb-count fixtures, reads each profile with llvm-profdata show --sample --all-functions, and prints report fields. It uses explicit max aggregation with no skid, zero-fill or head estimate. Missing build-ID is deliberately allowed for these synthetic fixtures, never implied for production inputs.

Optional resource control, when user scopes are available:

```bash
nice -n 19 ionice -c3 systemd-run --user --scope -p MemoryMax=3G -p CPUQuota=100% \
  bash "$DOCS/demo/run_host_demo.sh" "$PROJECT/llvm" "$EXTRACTED" "$ROOT" "$PROJECT/demo-output-limited"
```

## Expected output

Executed using the release SHA documented in the README. Exit status: 0.

```text
=== a64-pie ===
Function: main: 1, 0, 1 sampled lines
Samples collected in the function's body {
  0: 1
}
No inlined callsites in this function
{"conversion": "ok", "identity": "unverified", "sampling_adequacy": "unknown", "target_samples": 1, "usable_samples": 1, "written_positions": 1}
=== thumb-count ===
Function: main: 1, 0, 1 sampled lines
Samples collected in the function's body {
  0: 1
}
No inlined callsites in this function
{"conversion": "ok", "identity": "unverified", "sampling_adequacy": "unknown", "target_samples": 1, "usable_samples": 1, "written_positions": 1}
```

Each example creates extbinary, quality.json, stdout, stderr and show.txt files. Compare function main, total 1, head 0, body line-offset 0 count 1, no inline callsites, one target/usable sample and one written position. Identity unverified follows missing identity evidence in the fixture; conversion success is not a statement of sufficient sample size.

## Actual report fragment

The following is the complete verdict and samples portion of a64-pie.quality.json from this execution. The Thumb example's two objects are identical. No paths or fields in these objects were rewritten.

```json
{
  "verdict": {
    "conversion": "ok",
    "failure_stage": null,
    "fallback_callback_count": 0,
    "identity": "unverified",
    "lost_ratio_check": "not_evaluated",
    "reason": null,
    "sample_threshold_check": "not_evaluated",
    "sampling_adequacy": "unknown",
    "usable_ratio_check": "not_evaluated"
  },
  "samples": {
    "after_event": {
      "normalized_weight": {
        "denominator": 1000003,
        "numerator": 1000003
      },
      "period_sum": 1000003,
      "sample_count": 1
    },
    "after_pid": {
      "normalized_weight": {
        "denominator": 1000003,
        "numerator": 1000003
      },
      "period_sum": 1000003,
      "sample_count": 1
    },
    "input_total": {
      "sample_count": 1
    },
    "kernel": {
      "normalized_weight": {
        "denominator": 1000003,
        "numerator": 0
      },
      "period_sum": 0,
      "sample_count": 0
    },
    "other_dso": {
      "normalized_weight": {
        "denominator": 1000003,
        "numerator": 0
      },
      "period_sum": 0,
      "sample_count": 0
    },
    "other_dso_top20": [],
    "pid_unknown": {
      "normalized_weight": {
        "denominator": 1000003,
        "numerator": 0
      },
      "period_sum": 0,
      "sample_count": 0
    },
    "skid_unadjusted": {
      "normalized_weight": {
        "denominator": 1000003,
        "numerator": 0
      },
      "period_sum": 0,
      "sample_count": 0
    },
    "skid_unadjusted_reasons": {
      "data_or_state_change": "unknown",
      "first_instruction": "unknown",
      "predecessor_no_line": "unknown",
      "range_gap": "unknown"
    },
    "target": {
      "counts": {
        "normalized_weight": {
          "denominator": 1000003,
          "numerator": 1000003
        },
        "period_sum": 1000003,
        "sample_count": 1
      },
      "in_cu_no_subprogram": {
        "normalized_weight": {
          "denominator": 1000003,
          "numerator": 0
        },
        "period_sum": 0,
        "sample_count": 0
      },
      "in_func_no_line": {
        "nonleaf_line_zero": {
          "normalized_weight": {
            "denominator": 1000003,
            "numerator": 0
          },
          "period_sum": 0,
          "sample_count": 0
        },
        "normalized_weight": {
          "denominator": 1000003,
          "numerator": 0
        },
        "period_sum": 0,
        "sample_count": 0
      },
      "no_cu": {
        "normalized_weight": {
          "denominator": 1000003,
          "numerator": 0
        },
        "period_sum": 0,
        "sample_count": 0
      },
      "outside_dwarf_func": {
        "normalized_weight": {
          "denominator": 1000003,
          "numerator": 0
        },
        "period_sum": 0,
        "sample_count": 0
      },
      "outside_symtab_top20": [],
      "plt": {
        "normalized_weight": {
          "denominator": 1000003,
          "numerator": 0
        },
        "period_sum": 0,
        "sample_count": 0
      },
      "unmapped_in_target": {
        "normalized_weight": {
          "denominator": 1000003,
          "numerator": 0
        },
        "period_sum": 0,
        "sample_count": 0
      },
      "usable": {
        "normalized_weight": {
          "denominator": 1000003,
          "numerator": 1000003
        },
        "period_sum": 1000003,
        "sample_count": 1
      }
    },
    "unmapped": {
      "normalized_weight": {
        "denominator": 1000003,
        "numerator": 0
      },
      "period_sum": 0,
      "sample_count": 0
    },
    "written_positions": 1
  }
}
```

A ratio denominator is a normalization unit, not an execution count. No configured adequacy threshold failed, but a tiny synthetic example cannot prove sampling adequacy; unknown is expected.

## Verification boundary

README sections 0, 5 and 6 were exercised using the already fetched fixed source and existing release build products. The tool was extracted anew, SHA/version/help checked and both demo conversions and profile reads executed. The source clone and normal build had succeeded in release verification; this documentation update did not repeat the network clone or LLVM build. No board commands, new FFmpeg build or performance comparison were executed.
