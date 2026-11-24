# RPi5 M2a - FFmpeg AutoFDO

Source experiment: M2a, Raspberry Pi 5 (AArch64).
Read-only report copy. Host paths and private evidence references have been omitted.

profgen explicit conservative strategy; defaults not statistically validated

ToS is primary; Sintel is secondary, without multiple-comparison correction.
Publishable under the M1 gates: **true**.

| Input | Pilot BASE CV | N | Relative wall time | Bootstrap 95% CI | t 95% CI | Verdict |
|---|---:|---:|---:|---|---|---|
| sintel-1080p-60 | 0.978% | 40 | +0.162% | -0.258%, +0.692% | -0.331%, +0.657% | equivalent |
| tos-720p-60 | 1.186% | 40 | +0.117% | -0.155%, +0.401% | -0.174%, +0.408% | equivalent |

## Telemetry and paired-run checks

| Input | Flagged blocks | Flagged rounds BASE / AFDO | Imbalance difference / threshold | Technical retries | Effective MHz BASE / AFDO | Differences >0.5% |
|---|---:|---:|---:|---:|---:|---|
| sintel-1080p-60 | 0 | 0 / 0 | 0 / 4 | 0 | 2399.80 / 2399.78 | False |
| tos-720p-60 | 0 | 0 / 0 | 0 / 4 | 0 | 2399.78 / 2399.76 | False |

Voltage and firmware throttling history: unknown.

| Input | Variant | Start median / max C | Window min / median / max C |
|---|---|---|---|
| sintel-1080p-60 | BASE | 38.88 / 40.80 | 36.95 / 41.90 / 44.65 |
| sintel-1080p-60 | AFDO | 39.15 / 40.25 | 37.50 / 41.90 / 45.20 |
| tos-720p-60 | BASE | 39.42 / 40.80 | 38.60 / 42.45 / 45.20 |
| tos-720p-60 | AFDO | 39.70 / 41.35 | 38.60 / 42.45 / 44.65 |

## Conversion, consumption and registered deviation

Locked profile SHA-256: `db4d4c196cde3afb20803580ed5317d83a7d4a95f0d8f830c5394f1536b99d5a`.
Six conversions had verified identity. See report.json for the disclosure and per-target AppliedSamples.
S5 used a one-run audit path correction from `usr/lib/gcc` to `usr/lib64/gcc`. The sealed platform file and thresholds stayed unchanged.

Plan SHA, seed, pilot, clean sensitivity, round and release-gate records are in report.json.
