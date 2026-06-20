# Idea Tree Protocol

`idea_tree/` is the strict source for module innovation.

Rules:

- Every module trial must have an `idea_id`.
- No `idea_id`, no `dev/idea-*` branch.
- Tune and ablation questions do not directly become idea nodes.
- Rejected ideas stay in the tree with evidence and lower priority.
- Old experiment results are not migrated.
- Old ideas may be rewritten as fresh `candidate` nodes.

Required idea fields are defined in `idea_tree/schema.json`.
