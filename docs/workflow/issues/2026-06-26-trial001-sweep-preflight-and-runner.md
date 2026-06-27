# 2026-06-26 TRIAL-001 Sweep Preflight And Runner Issues

## Scope

- Trial: `TRIAL-001_clip_a_self_residual_seenonly`
- Planned sweep: `ATTEMPT-009` through `ATTEMPT-028`
- Planned follow-up: L2SP/text-anchor as a separate `TRIAL-002`
- Environment: `dvsr_gpu`
- Artifact boundary: raw logs/checkpoints/receipts stay in `GTPJ_Warehouse`; Git records lightweight evidence only.

## ISSUE-20260626-001: PowerShell heredoc mismatch

Status: fixed

Symptom:

- A Bash-style heredoc was used in PowerShell:

```powershell
python - <<'PY'
```

- PowerShell returned:

```text
Missing file specification after redirection operator
```

Impact:

- No repository files were changed.
- No training was started.
- The cost was one failed read-only command.

Root Cause:

- PowerShell does not support Bash heredoc syntax.

Resolution:

- Use one of these Windows-safe forms:

```powershell
python -c "print('single line only')"
```

or a temporary script file under `$env:TEMP`, or an existing workflow helper.

Prevention:

- Treat PowerShell as the default shell for GTPJ commands.
- Use `python -c` only for single-line expressions.
- For multi-line logic, prefer `workflow/gtpj_workflow.py` helper code or a temporary script.

Helper Candidate:

- Not required unless this recurs in generated commands.

## ISSUE-20260626-002: L2SP belongs to a new trial, not TRIAL-001 tuning

Status: guarded before run

Symptom:

- The plan mixed two different experiment types:
  - `ATTEMPT-009..028`: TRIAL-001 internal parameter tuning.
  - L2SP/text-anchor: a new loss mechanism with `lambda_l2sp`.

Impact:

- Putting `lambda_l2sp` into TRIAL-001 would mix "parameter tuning" with "new loss mechanism".
- That would make the trial evidence hard to interpret and could violate the module-trial boundary.

Root Cause:

- TRIAL-001 implementation scope does not include L2SP/text-anchor.
- A new loss changes training semantics, so it is a new implementation hypothesis.

Resolution:

- Keep `ATTEMPT-009..028` limited to existing TRIAL-001 knobs.
- Run L2SP/text-anchor as `TRIAL-002`, with its own implementation contract and attempt table.

Prevention:

- Numeric-only changes such as heads, dropout, inner/outer ratio, seed, or scheduler stay inside the same trial.
- Changes to forward path, loss, eval, label mapping, split, logits shape, or metric semantics require a new trial.

Helper Candidate:

- Add a guard that rejects nonzero `lambda_l2sp` when `trial_id=TRIAL-001`.

## ISSUE-20260626-003: Post-run overhead must be helper-first

Status: active policy

Symptom:

- After training, most time was spent synchronizing:
  - `manifest.yaml`
  - `result.yaml`
  - `result.md`
  - `quality_check.md`
  - `ATTEMPTS.md`
  - Warehouse artifact registry
  - trial root summaries

Impact:

- Manual post-processing becomes slower than training.
- Manual edits increase the risk of drift between root summary, attempt result, registry, and Warehouse.

Root Cause:

- The evidence chain has many required destinations.
- Without helper-first entry, repeated bookkeeping becomes manual synchronization.

Resolution:

- Use `record-module-attempt` for module-trial attempts.
- Use `--dry-run` first to verify parsed metrics, artifact paths, hashes, sizes, and decisions.
- Only manually edit trial root summaries when the attempt changes the trial-level conclusion.

Prevention:

- Freeze config and planned `ATTEMPTS.md` rows before running.
- Batch-register completed attempts after the run rather than hand-editing each result live.
- Any repeated manual field should become a helper output.

Helper Candidate:

- Extend `record-module-attempt` to optionally update trial root summaries when `--mark-best` is passed.

## ISSUE-20260626-004: Multi-line `python -c` is fragile in PowerShell

Status: fixed

Symptom:

- Multi-line Python logic was passed through `python -c`.
- PowerShell argument handling produced:

```text
SyntaxError: unexpected character after line continuation character
```

Impact:

- No files were changed.
- The check failed once and slowed verification.

Root Cause:

- `python -c` is reliable for compact one-liners, not multi-line inspection logic in PowerShell.

Resolution:

- Move multi-line checks into:
  - an existing helper,
  - a temporary script in `$env:TEMP`,
  - or a short single-line expression when genuinely simple.

Prevention:

- Do not paste multi-line Python into PowerShell `python -c`.
- If a check is useful twice, convert it into `workflow/gtpj_workflow.py`.

Helper Candidate:

- Add a `validate-attempt-configs` helper if config validation repeats.

## ISSUE-20260626-005: Runtime state must stay under `.gtpj_runtime/`

Status: fixed

Symptom:

- A temporary root-level file was created:

```text
.gtpj_current_run_id.txt
```

Impact:

- The file was not committed.
- It did not affect code or config, but it violated the runtime-state boundary.

Root Cause:

- A temporary run id was written to the repo root for shell reuse.

Resolution:

- Delete `.gtpj_current_run_id.txt`.
- Keep runtime state under `.gtpj_runtime/`, which is ignored by Git.

Prevention:

- Use PowerShell variables for short-lived shell values.
- Use `.gtpj_runtime/` for persistent runtime state.
- Never create root-level temporary runtime files.

Helper Candidate:

- Add runtime-state path checks to `audit-boundary`.

## ISSUE-20260626-006: Background runner must capture launch-time errors

Status: fixed before training

Symptom:

- The background batch runner process exited quickly.
- No `status.json` or `events.jsonl` was created.
- The launch-time stdout/stderr was not captured at first.

Impact:

- Training did not start.
- No raw log or checkpoint was produced.
- Runner lock state had to be verified before continuing.

Root Cause:

- A PowerShell path expression mixed `Join-Path` arguments and string concatenation:

```powershell
$RunDir = Join-Path $Repo '.gtpj_runtime\runs\' + $RunId
```

- `Start-Process` did not redirect launch-time stdout/stderr.

Resolution:

- Use explicit path grouping:

```powershell
$RunDir = Join-Path $Repo ('.gtpj_runtime\runs\' + $RunId)
```

- Redirect launch logs:

```text
launch_stdout.log
launch_stderr.log
```

Prevention:

- After launching a background runner, immediately check:
  - process status,
  - `status.json`,
  - `events.jsonl`,
  - `launch_stderr.log`.
- If no runtime state appears within 30 seconds, treat it as launch failure, not as training in progress.

Helper Candidate:

- Add a runner launch wrapper that refuses to report success until runtime state exists.
