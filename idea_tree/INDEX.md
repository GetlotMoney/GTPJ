# Idea Index

Current experiment version view: `idea_tree/versions/v5.md`

This is the human-readable global idea list. Detailed per-version selection state lives under `idea_tree/versions/`.
`idea_tree.json` remains the machine-readable source.

| Idea | Title | Idea file | Source status | Global score | Covered versions | Global status | Next action |
|---|---|---|---|---:|---|---|---|
| `IDEA-0001` | CLIP-A-self text prototype adapter | `idea_tree/ideas/IDEA-0001_clip_a_self_text_prototype/IDEA.md` | verified | 82.0 | `v1`, `v2`, `v3`, `v4`, `v5` | validated | Use GTPJ-v5 as the active mainline; future tuning can inspect PSE/BVSA weight sensitivity while comparing repeat mean against v4 confirmed_H=74.45. |
| `IDEA-0003` | Dynamic Residual Routing | `idea_tree/ideas/IDEA-0003_dynamic_residual_routing/IDEA.md` | local_heuristic | 78.0 | `v5` | selected | TRIAL-001 ATTEMPT-001 did not promote; run a `principled-followup` batch focused on direction/local/PSE gates with ICSA fixed. |
| `IDEA-0002` | FAE-memory JEPA auxiliary loss | `idea_tree/ideas/IDEA-0002_fae_memory_jepa/IDEA.md` | local_heuristic | 72.0 | `v2`, `v3`, `v4`, `v5` | validated | Use GTPJ-v5 as the active mainline. Next work should tune from config/versions/v5.yaml and compare repeat mean against v4 confirmed_H=74.45. |

## Usage Rules

- This file is an index, not an experiment priority queue.
- When starting a trial for a base version, read `idea_tree/versions/<base_version>.md`.
- Git records lightweight ledgers and artifact pointers; raw runtime logs and checkpoints live in Warehouse.
