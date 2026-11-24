---
name: afdo-workflow
description: Operate or inspect an AutoFDO experiment through afdo_wf. Use for job drafting, stage planning, authorized execution or recovery, receipt inspection, and interpreting the paired measurement report.
---

# AutoFDO workflow

Use the workflow from an existing project checkout with Python 3.11 or later. Set the module path and disable bytecode writes for read-only inspection.

```bash
export PYTHONPATH="$PWD/workflow"
export PYTHONDONTWRITEBYTECODE=1
```

Before any live run, confirm it is authorized for the exact board, image and job. Follow the host's shared GBS lock procedure and keep the workflow's resource gates in force. Follow the target-only SDB recovery procedure. Never restart the shared SDB service. Stop and report any failed gate, identity mismatch, correctness failure or `recovery-required` (`RECOVERY_REQUIRED`). Preserve logs and report `unknown` values as unknown.

## Start a new job

```bash
python3 -m afdo_wf init --package "$PACKAGE" --inputs "$INPUTS" \
  --platform "$PLATFORM" --media-dir "$MEDIA_DIR" --workdir "$WORKDIR" \
  --job "$JOB" --output "$RUN_DIR"
python3 -m afdo_wf run --job "$JOB" --dry-run
python3 -m afdo_wf explain preflight
```

Use `missing_for_run` to complete the draft with the authorized host and board settings. Set `draft` to `false` after review. Preview again and check the declared paths, platform, stage actions and board operations. Run only with live authorization.

```bash
python3 -m afdo_wf run --job "$JOB"
```

## Inspect or resume

```bash
python3 -m afdo_wf status --job "$JOB"
python3 -m afdo_wf explain "$STAGE"
python3 -m afdo_wf run --job "$JOB" --dry-run
```

Inspect receipt paths, input and upstream SHA results, and failure reasons. For an authorized resume with matching inputs and cleared recovery conditions, run the same job again. The runner verifies receipts before reuse. Consult the [exit-code contract](../../docs/workflow/m5/01_cli_and_skill.md#退出码) when a command fails.

Use redo only for an authorized rerun of a mutable job. Preserve sealed configurations, runs and receipts.

```bash
python3 -m afdo_wf --redo "$STAGE" --reason "$REASON" --job "$JOB"
python3 -m afdo_wf status --job "$JOB"
python3 -m afdo_wf run --job "$JOB" --dry-run
```

Record the archive receipt path and invalidated stages. Once authorized, use `run` to perform the rerun.

## Read a report

```bash
python3 -m afdo_wf explain report
```

Open the `report.md` bound to the completed report receipt. Report its primary verdict, relative change, confidence interval, `publishable` value and limitations. Use the report's labels for secondary comparisons. Preserve `inconclusive` and `unknown` as written.

For the sealed [M1 attempt-11](../../docs/workflow/m1/05_m1_board_e2e.md) or [M2a](../../docs/workflow/m2a/02_runner_and_afdo_audit.md) example, substitute the archived job path available in your workspace. Read the report and use the read-only commands below.

```bash
python3 -m afdo_wf status --job "$M1_JOB"
python3 -m afdo_wf status --job "$M2A_JOB"
python3 -m afdo_wf explain measure
python3 -m afdo_wf explain report
```
