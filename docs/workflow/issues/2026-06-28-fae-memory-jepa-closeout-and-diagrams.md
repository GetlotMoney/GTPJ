# 2026-06-28 FAE-memory JEPA Closeout And Diagram Issues

## Scope

- Trial: `IDEA-0002_fae_memory_jepa / TRIAL-001_fae_memory_jepa`
- Branch: `dev/v2-idea-0002-trial-001-fae-memory-jepa`
- Result commit: `c5bbfe4 trial: record fae-memory jepa result`
- Trial tag: `trial/v2/idea-0002/trial-001`
- Result: `H=73.82`, `delta_H=-0.47` vs active v2 `H=74.29`
- Decision: `revise`, no promotion

## ISSUE-20260628-010: Post-run closeout still required too much manual root-ledger sync

Status: active

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

- Add `sync-trial-summary --trial-dir ... --attempt-id ... --decision ...`.
- It should update trial root result/quality/README, module-trial index, and idea-tree status from one source of truth.

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

- Extend `validate` to warn when a formal `experiments/vX/VERSION.md` lacks `## Version Flow`.
- Extend `new-trial` templates to ensure every new trial includes `## Trial Flow`.

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
