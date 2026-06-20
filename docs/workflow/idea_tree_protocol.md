# Idea Tree Protocol

`idea_tree/` is the strict source for module innovation.

Rules:

- Every module trial must have an `idea_id`.
- No `idea_id`, no `dev/idea-*` branch.
- Tune and ablation questions do not directly become idea nodes.
- `idea_tree/INDEX.md` is the human-readable master index. It must show each
  idea folder path and the current version score. This is the first file to
  read when deciding what to try next.
- `idea_tree/idea_tree.json` is the machine-readable registry. It must contain
  the same `idea_id`, `idea_dir`, global score, and per-version scores.
- Each idea must have its own file at `idea_tree/ideas/IDEA-xxxx_slug/IDEA.md`.
- Every module idea must record `source_type`, `source_ref`, and `source_status`.
- Valid `source_type` values are `paper`, `user`, `observation`,
  `cross_domain`, and `hybrid`.
- If the source is unclear, set `source_status: unknown` and do not start a
  trial until the source is verified or the idea is explicitly accepted as a
  local heuristic.
- Idea ranking is framework-version specific. Use `version_scores.<version>.score`
  for the current baseline version. Do not assume a v1 score applies to v2.
- Cross-version reuse is allowed. When an idea may apply to multiple versions,
  add multiple `version_scores` entries and describe what must change for each
  version.
- If the active framework is `v2`, the same idea can stay in the tree, but its
  trial must use `version_scores.v2`. A `v1` score is evidence, not permission.
- A module trial must select one base version first. The selected base version
  determines which score, risks, and constraints are used for review.
- Rejected ideas stay in the tree with evidence and lower priority.
- Old experiment results are not migrated.
- Old ideas may be rewritten as fresh `candidate` nodes.

Required idea fields are defined in `idea_tree/schema.json`.

## Score Fields

Use a 0-100 scale:

- `global_score`: long-term idea value across the project.
- `version_scores.<version>.score`: priority for a concrete framework version.
- `version_scores.<version>.applicability`: `direct`, `needs_adaptation`,
  `unclear`, or `not_applicable`.
- `version_scores.<version>.rationale`: why the score applies to that version.
- `version_scores.<version>.blockers`: source, interface, data, or risk blockers.

Sorting for the current work window is:

```text
current version score
then source_status
then risk
then cost
```

## Current-Version Processing

The active framework is declared by `idea_tree.json.current_version`.

When choosing the next module trial:

1. Open `idea_tree/INDEX.md`.
2. Use the current version score, not `global_score`, as the primary order.
3. Open the selected idea file and check source, blockers, and transfer notes.
4. Start a trial only for one explicit base version.
5. Record the trial under `experiments/module_trials/IDEA-xxxx_slug/`.

When a new framework version is created:

1. Keep the old idea node.
2. Add `version_scores.vX`.
3. Set `applicability` for that version.
4. Explain the interface or module changes in `transfer_notes`.
5. Run `python workflow/gtpj_workflow.py set-current-version --version vX`.

The helper refuses to switch `current_version` if any idea is missing the new
`version_scores.vX` entry. Use `not_applicable` with score `0` when an idea
clearly cannot transfer to the new framework.
