# Idea Tree

This directory is the source of truth for module innovation.

Use `inbox.md` for rough ideas. Move only selected ideas into a stable
`IDEA-xxxx` node.

No module trial can start without an idea node.

## Required Structure

```text
idea_tree/
|-- INDEX.md                 # human-readable master ranking
|-- idea_tree.json           # machine-readable idea registry
|-- ideas/
|   `-- IDEA-0001_short_name/
|       `-- IDEA.md          # source, hypothesis, version scores, constraints
|-- queues/                  # current execution queues derived from the index
`-- sources/                 # paper/source indexes
```

## Ranking Rule

Ideas are ranked per framework version, not only globally.

```text
global_score = long-term value estimate
version_scores.v1.score = usefulness for GTPJ-v1
version_scores.v2.score = usefulness for GTPJ-v2
```

The active framework version uses its own score column. An idea can be useful
for multiple versions with different scores and different implementation notes.

Use `INDEX.md` as the current decision board. Use each
`ideas/IDEA-xxxx_slug/IDEA.md` file as the source and rationale record. Start a
trial only after the selected version score, source status, blockers, and
transfer notes have been checked.
