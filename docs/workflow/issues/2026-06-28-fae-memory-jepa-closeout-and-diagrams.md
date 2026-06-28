# 2026-06-28 FAE-memory JEPA Closeout And Diagram Issues

## Scope

- Trial: `IDEA-0002_fae_memory_jepa / TRIAL-001_fae_memory_jepa`
- Branch: `dev/v2-idea-0002-trial-001-fae-memory-jepa`
- Result commit: `c5bbfe4 trial: record fae-memory jepa result`
- Trial tag: `trial/v2/idea-0002/trial-001`
- Result: `H=73.82`, `delta_H=-0.47` vs active v2 `H=74.29`
- Decision: `revise`, no promotion

## ISSUE-20260628-010: Post-run closeout still required too much manual root-ledger sync

Status: fixed

Symptom:

- `record-module-attempt` successfully wrote attempt-local evidence and Warehouse registrations.
- Coordinator still had to manually synchronize root-level trial files and higher-level indexes:

```text
README.md
result.yaml
result.md
quality_check.md
review_round_2.md
agent_summary.md
experiments/module_trials/INDEX.md
idea_tree/idea_tree.json
idea_tree/versions/v2.md
idea_tree/INDEX.md
```

Impact:

- The run itself was straightforward, but post-run bookkeeping took longer than expected.
- Manual synchronization created temporary stale-ledger findings during Review 3.
- Owner experience felt slower than a simple experiment should feel.

Root Cause:

- The helper covers attempt-local evidence well, but does not yet fully update trial-root summaries, idea-tree summaries, and module-trial indexes.
- Review 3 correctly found stale `agent_summary` / index state while the Coordinator was still closing the evidence loop.

Resolution:

- Root trial summary, Review 3 files, idea-tree state, and module-trial index were manually synchronized.
- Added `sync-trial-summary` to `workflow/gtpj_workflow.py` so future attempt-local evidence can be synchronized into the trial root summary, module-trial index, and idea-tree views with one command.
- Extended `validate` so formal version records and module trial READMEs must carry the required Mermaid flow sections.
- Final checks passed:

```text
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py audit-boundary
python workflow/gtpj_workflow.py validate-remote
git diff --check
python -m unittest tests.test_fae_memory_jepa
python -m unittest tests.test_gtpj_workflow
```

Prevention:

- Next module-trial run should use `record-module-attempt --dry-run` first, then formal record.
- Immediately after recording, run a fixed closeout checklist:

```text
attempt-local files
trial root README/result/quality
Review 3 files
module_trials/INDEX.md
idea_tree files
Warehouse registry/hash check
validate/audit-boundary/validate-remote
```

Helper Candidate:

- Implemented:

```text
python workflow/gtpj_workflow.py sync-trial-summary --trial-dir ... --attempt-id ... --decision ...
```

- It updates trial root `manifest.yaml`, `result.yaml`, `result.md`, `quality_check.md`, README summary fields, `experiments/module_trials/INDEX.md`, and idea-tree machine/human views from the attempt-local manifest/result.

## ISSUE-20260628-011: Workflow diagram standard was missing

Status: fixed

Symptom:

- Owner expected each version to have a workflow / version flow diagram.
- Repository had text-based version trees, but no dedicated flow diagram standard and no explicit per-version Mermaid diagram requirement.
- Search found no committed `.drawio`, `.mmd`, `.svg`, `.png`, `.jpg`, `.jpeg`, or `.html` workflow diagram assets in the repository.

Impact:

- Workflow felt harder to understand than necessary.
- New windows / new agents had to infer version flow from scattered text files.
- The difference between version flow, trial flow, and artifact flow was not visible enough.

Root Cause:

- `versioning.md` required version metadata but did not require a visual flow section.
- Existing templates did not reserve a `Version Flow` or `Trial Flow` section.

Resolution:

- Added `docs/workflow/workflow_diagrams.md`.
- Added `## Version Flow` to `experiments/v1/VERSION.md` and `experiments/v2/VERSION.md`.
- Added Mermaid flow templates to:

```text
experiments/templates/VERSION_template.md
experiments/templates/TRIAL_README_template.md
```

- Updated workflow indexes and structure docs to reference the new standard.

Prevention:

- Every future `experiments/vX/VERSION.md` must include `## Version Flow`.
- Every new module trial README must include `## Trial Flow`.
- Mermaid-in-Markdown is the GitHub authoritative flow diagram format.

Helper Candidate:

- Implemented:
  - `validate` now fails if a formal `experiments/vX/VERSION.md` lacks `## Version Flow`.
  - `validate` now fails if a module trial README lacks `## Trial Flow`.
  - `new-trial` now emits a default `## Trial Flow` Mermaid section.

## ISSUE-20260628-012: Full innovation review is correct but too heavy for simple reruns

Status: policy-clarified

Symptom:

- Owner asked why a simple run or reproduction can feel slower than doing it manually.
- The FAE-memory JEPA task was not a simple rerun: it changed model/loss data flow and therefore correctly triggered innovation Review 0-3.
- However, the same ceremony must not be applied to pure read-only checks or quick local reruns.

Impact:

- If the workflow over-classifies a simple rerun as full innovation, it wastes time.
- If it under-classifies a code-changing idea, it risks invalid evidence.

Root Cause:

- The workflow has strict gates, but the fast path needs to be stated more clearly in day-to-day operation.

Resolution:

- Current rules already separate:

```text
quick_local
valid_single_run
confirmation_grade
innovation / module trial
```

- For this run, full review was appropriate because code semantics changed.

Prevention:

- When owner says "复现一下" without requesting formal evidence, default to `quick_local` and do not create full innovation evidence.
- When owner says "把这个 idea 实现，跑训练，全流程按照规范", use full innovation flow.
- Start every run summary with the classification and expected overhead.

Helper Candidate:

- Add a `classify-request` helper or lightweight `workflow status --task` output that prints the expected path and estimated bookkeeping overhead.

## ISSUE-20260628-013: Agent summary and Review 3 drift after root sync

Status: fixed

Symptom:

- `sync-trial-summary` synchronized trial root `manifest/result/quality`, module index, and idea-tree state.
- `agent_summary.md` and `review_round_2.md` could still describe an older attempt.
- `closeout-check` could return OK even when those two human-facing review files were stale.

Impact:

- Owner could see contradictory evidence: root result points to the latest attempt, while agent/review summaries still mention an older attempt.
- New agents could inherit stale wording and explain the current code or result incorrectly.
- The workflow was not fully automatic because Coordinator still had to remember to rewrite the review summary.

Root Cause:

- `record-module-attempt` correctly wrote attempt-local evidence.
- `sync-trial-summary` originally treated `review_round_2.md` and `agent_summary.md` as manual narrative files rather than root closeout ledgers.
- `closeout-check` verified attempt/root/index/idea/Warehouse closure but did not require current-attempt agent/review evidence.

Resolution:

- `sync-trial-summary` now writes current-attempt `review_round_2.md` from the attempt manifest/result/artifact ids.
- `sync-trial-summary` now writes current-attempt `agent_summary.md` from the same evidence.
- `closeout-check` now requires both files and verifies:
  - their first text block has `attempt_id: ATTEMPT-xxx`;
  - the attempt id matches the closeout target;
  - current artifact ids are referenced;
  - known stale markers such as `No training result has been recorded` are absent.
- `tests.test_gtpj_workflow` covers stale summary overwrite and closeout acceptance.

Prevention:

- After every module-trial attempt:

```text
record-module-attempt
sync-trial-summary
closeout-check
```

- Do not manually patch `agent_summary.md` or `review_round_2.md` for ordinary closeout when the helper can derive them from attempt evidence.
- Long sub-agent reports can stay external, but GitHub root summaries must be regenerated from current attempt evidence.

Helper Candidate:

- Implemented in `workflow/gtpj_workflow.py`:
  - current-attempt Review 3 generator;
  - current-attempt agent summary generator;
  - closeout hard gate for stale agent/review files.
