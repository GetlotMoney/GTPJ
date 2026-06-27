# Review 0: Idea / Source Intent

review_round: Review 0
role: Reader/Planner
agent_instance_type: sub_agent
idea_id: IDEA-0002
base_version: v2
decision: allow

## Conclusion

source_type: user
source_status: local_heuristic
source_decision: acceptable

IDEA-0002 is acceptable as an owner local heuristic. The record has an owner-dated source, a reproducible code observation, v2 rationale, hypothesis, implementation scope, risk, and selected/trialing stage. It is not a paper-verified source, but it is sufficient to enter Review 1 design/interface review.

## Hypothesis Check

hypothesis_status: clear

The core hypothesis is clear: visual target uses pre-FAE `patch_z.detach()`, visual context moves to FAE-backed memory, and text condition continues to use CLIP-A-self adapted `all_text[labels] -> cross_tf.embed_text`. The goal is to make positive JEPA gradients cover FAE visual memory without changing logits, eval, label mapping, seen/unseen split, class order, or metric semantics.

## Idea / Trial Boundary

boundary_decision: create IDEA-0002 / TRIAL-001, not an IDEA-0001 internal attempt

IDEA-0001 is the CLIP-A-self text prototype adapter already active in v2. This change alters the AG-JEPA visual context and gradient coverage path, making it a new auxiliary-loss / visual-memory regularization hypothesis rather than a CLIP-A-self parameter change or narrow ablation.

## Main Risks

- `target` and `context` live at different representation depths and may be unstable.
- With `lastvit_select_k=32`, mask, `patch_z`, and FAE context must use the same selected patch set.
- Positive JEPA loss must prove nonzero gradient on `cross_tf.fae.*`; otherwise the idea goal is not implemented.
- Negative branch should keep visual context detached in the first implementation.
- Switch-off path must recover current AG-JEPA behavior.
- Formal Runner requires clean worktree and pre-run freeze commit.

## Blocking Issues

None for Review 0 source intent.

## Required Next Gates

- Review 1: Interface Checker must confirm insertion point, shape, switch-off path, and gradient probe plan.
- Review 2: Implemented diff must pass code/interface/quality review before Runner.
- Runner: only starts after Review 2 allow, clean worktree, and explicit run_commit.

## Evidence Refs

- `idea_tree/ideas/IDEA-0002_fae_memory_jepa/IDEA.md`
- `D:/backup/Documents/Myself/GTPJ_Research/ideas/IDEA-0002_fae_memory_jepa/idea_full.md`
- `model/MyModel.py`

memory_used: yes
memory_sources: docs/workflow/agents/shared_roles/reader_planner/memory.md
verified_against_current_repo: yes
