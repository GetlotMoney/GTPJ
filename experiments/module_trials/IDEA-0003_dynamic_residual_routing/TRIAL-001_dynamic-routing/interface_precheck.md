# Innovation Review

```text
review_round: Review 1
role: Interface Checker
agent_instance_type: main_agent_precheck
inputs_checked: model/MyModel.py; tests/test_fae_memory_jepa.py; train_GTPJ_CUB.py; workflow/gtpj_workflow.py; config/versions/v5.yaml
independence_scope: interface contract before/while implementation
findings: Dynamic routing may be inserted at four scalar route points while preserving tensor contracts. PSE gate produces [C_seen, 1]. ICSA gate produces [B, 1] or [B, C_seen]. Direction/local gates produce [B, 1] or [B, C]. all_text_cond must remain the BVSA input when bvsa_text_mode=conditional.
blocking_issues: none
non_blocking_issues: ICSA gate receives no immediate task gradient while meta_net output is zero-initialized; tests should verify the path with a nonzero meta_net nudge and preserve v5 initialization.
decision: allow
evidence_refs: tests/test_fae_memory_jepa.py dynamic routing tests; model/MyModel.py DynamicRoutingGate design
memory_used: no
memory_sources:
verified_against_current_repo: yes
```

Pre-run Review 2 must re-check:

- `use_dynamic_routing=false` switch-off behavior.
- `dynamic_*_mode=fixed` equivalence to fixed v5 scalars.
- Train logits `[B（图片/样本数量）, n_seen（训练 seen 类数量）]`.
- Eval logits `[B（图片/样本数量）, C（全部类别数量）]`.
- No changes to class order, seen/unseen split, label mapping, or metric calculation.
