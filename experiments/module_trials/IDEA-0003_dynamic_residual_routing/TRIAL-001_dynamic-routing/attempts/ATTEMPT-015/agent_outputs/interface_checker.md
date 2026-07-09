# Interface Checker Output

role_key: `interface_checker`
agent_instance_id: `019f405c-8b4e-72d0-b93a-8c03b76522e1`
thread_title: `ATTEMPT-015 | Interface Checker`
decision: `allow`

## Files Reviewed

- `workflow/gtpj_workflow.py`
- `tests/test_gtpj_workflow.py`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/config.yaml`
- `docs/workflow/reference/GZSL_HARD_RULES.md`
- GTPJ train/model/dataset helper interface files on the current repo path

## Conclusion

The `h76-hotspot100-tune` profile fixes `dynamic_direction_mode=sample`, `dynamic_gate_hidden=48`, `random_seed=5`, and only changes `weight_s2v` plus `dynamic_gate_anchor_lambda`.

No dataset split, class order, label mapping, GZSL metric, training logits, eval logits, or unsupported `dynamic_pse_mode` change was found.
