# Idea Index

Current experiment-version view: `idea_tree/versions/v2.md`.

This is the human-readable global idea list. Use `idea_tree/versions/<base_version>.md` for version-specific next actions.

| Idea | Title | Idea file | Source status | Global score | Versions | Global status | Next action |
|---|---|---|---|---:|---|---|---|
| `IDEA-0001` | CLIP-A-self text prototype adapter | `idea_tree/ideas/IDEA-0001_clip_a_self_text_prototype/IDEA.md` | verified | 82.0 | `v1`, `v2` | validated | Run GTPJ-v2 confirmation and U/S gap analysis before manuscript-grade claims; then continue v2 tune or ablation from `config/versions/v2.yaml`. |
| `IDEA-0002` | FAE-memory JEPA auxiliary loss | `idea_tree/ideas/IDEA-0002_fae_memory_jepa/IDEA.md` | local_heuristic | 72.0 | `v2` | weakened | TRIAL-001 ATTEMPT-001 completed as valid single-run evidence but underperformed v2 (H=73.82, delta_H=-0.47). Do not promote; continue only with a targeted ATTEMPT-002 param/ablation if the owner wants to keep exploring the mechanism. |

## Usage

- This file is a global list, not a version-priority queue.
- For choosing a trial under a base version, read `idea_tree/versions/<base_version>.md`.
- `idea_tree.json` is the machine-readable source of truth.
