# llvm-profgen IP mode: design summary

Status: limited functional delivery; statistical quality and performance validation deferred.

The [Chinese v1.8 source](original/02_llvm_profgen_enhance_design_v1.8.md) is reproduced unchanged. This English summary is a usage guide, not a replacement for its detailed contracts. The limited-delivery decision defers the quality matrix, performance/staleness experiment and second-stage default freeze; it does not cancel them.

## Input and address conversion

IP mode requires explicit `--ip-samples`, `--binary`, a strict perf-script text input and an explicit aggregation choice. It supports samples, MMAP/MMAP2 and LOST records in the prescribed export format. Other records are rejected. Raw perf.data input is not admitted for IP mode. Select a complete event name when the export contains multiple events.

A sample's dsoff is a file offset, not a load-relative virtual address. The tool finds its unique executable PT_LOAD and computes ELF address = p_vaddr + (dsoff - p_offset), validating the segment bounds. It does not clear bits on sample PCs to conceal inconsistencies. Kernel and special DSO names are classified separately. PID -1 is unknown and never matches a selected PID.

MMAP2 and buildid-list provide input-side identity evidence. Matching runtime and debug files are required; known mismatch or ambiguity fails. Missing input evidence gives unverified and requires explicit `--allow-missing-build-id`. Verified means identity evidence passed, not that sampling quality is adequate. A deleted suffix is preserved for regex matching; regex searches the raw path, so use ^ and $ for full-path matching.

## Options and counting

| Option | Values / default |
|---|---|
| --ip-samples | off unless explicitly enabled |
| --ip-weight | period (default), sample |
| --ip-period-unit | positive uint64, otherwise target-period median before symbolization/skid; invalid with sample weight |
| --ip-aggregation | sum, max, avg; **no default during evaluation, explicit choice required** |
| --ip-head-samples | none (default), entry-estimate |
| --ip-zero-fill | none (default), sampled-functions |
| --ip-skid | none (default), prev-inst |
| --ip-event | exact event; automatic only for a single event |
| --binary-match-regex | raw-DSO substring search; otherwise binary-name matching |
| --perf-buildid-list | optional identity evidence |
| --quality-report | optional JSON destination; required by the planned workflow |
| --ip-min-usable-ratio | optional, no default |
| --ip-min-target-samples | optional, no default |
| --ip-max-lost-ratio | optional, no default |
| --allow-missing-build-id | false |
| --format | extbinary (default), text, binary; GCC writer unsupported here |
| --use-md5 | false; extbinary only |
| --pid | no filter by default; negative value rejected |

With sample weighting, each sample contributes one. With period weighting, contribution is normalized by P_ref. Counts include DWARF duplication factors. Sum aggregates contributions; max selects the largest address contribution for a key; avg divides the integer numerator by P_ref times the number of instructions mapped to that key, including unobserved and duplicated instructions. Multiplications check overflow; rounding is half-up once per key, and a sampled key is at least one. Function totals are independent of aggregation and do not become entry counts.

A zero leaf or non-leaf line makes an IP sample unusable; missing non-leaf line counts have their own quality-report subcounter. This prevents wrapped, invalid callsite offsets. Inline contexts are retained for valid samples.

## Boundaries and ARM

Avg, sampled-functions zero fill and prev-inst request boundaries only for functions with usable samples. Sum/max with none options do not enumerate them. Instruction bytes come from the runtime ELF; mapping symbols come from runtime/debug .symtab, with corresponding sections matched by name and address range. Mapping state is section-local; data ranges are excluded, conflicting or missing mapping state fails the requested boundary operation.

A32/A64 use aligned four-byte stepping. Thumb advances from its mapping anchor using 16/32-bit lengths; a function intersection may not start inside or truncate an instruction. Boundary failures are reported for all affected functions and fail the conversion, rather than silently falling back.

For GNU AS Thumb DWARF odd-address ranges, the IP-only ARM32 little-endian rule clears range-endpoint low bits only when the normalized start has Thumb mapping state. At that start only, the symbolizer uses the original odd alias while the sample/key address remains unchanged. Original/alias leaf file, line and discriminator must agree. Mapping metadata unavailable during this normalization is reported with a warning; on-demand boundary operations still fail when their prerequisites are absent.

## Output and failure contract

Quality schema version is 1. Its top-level fields are schema_version, tool, input, event, semantics, identity, mapping, samples, isa, boundaries, lost, throttle, ratios, sanity, coverage, thumb_dwarf_normalization, consumer_hints, warnings and verdict. Full field definitions live in the sandbox CommandGuide.

Unknown is represented explicitly as "unknown"; confirmed absence uses "none" or documented null, not an empty string. Check exit status first, then verdict.conversion, failure_stage/reason, identity and the optional threshold checks. Sampling adequacy is unknown or insufficient; lack of a failed threshold is not proof of adequate sampling. LOST L/(L+S) uses exported records, which can include sideband losses. Overflow produces unknown plus W_LOST_RATIO_OVERFLOW rather than failing conversion.

Success exits zero; failure is nonzero. On failure, an old profile stays unchanged. A non-conflicting failure atomically replaces the report with failure JSON. Path conflicts (output '-', output/report aliases, or aliases of inputs) are rejected before loading ELF or creating temporary outputs, and neither output is written. Failure to write/commit the report preserves an old report and diagnoses stderr. Do not mistake an old successful report for this invocation's success. The two output files are not a crash-atomic transaction.

## Support and limitations

Supported: AArch64 and ARMv7 little-endian Thumb-2/A32 user-space ELF with sufficient DWARF. Separate debug identity is checked. Optional boundary features require usable mapping symbols.

Not delivered: pseudo-probe builds, IP perf.data ingestion, kernel profiles, BOLT. Same-name static functions can still merge by profile name; use unique internal linkage names in profiling builds. GNU normalization and non-leaf-line exclusion are functional repairs, not evidence for a statistical default. The legacy LBR path is protected by C1 regression.
