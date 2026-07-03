# Interface Checker Output

role: interface_checker
agent_instance_id: 019f287c-65c3-74b3-b01b-84a8d3d83d38
display_name: Singer / DR035 Interface Checker
decision: allow

## Checked Files

- `pre_run_plan.md`
- `config.yaml`
- `manifest.yaml`
- `quality_check.md`
- `agent_runtime.yaml`
- `workflow/gtpj_workflow.py`
- `tests/test_gtpj_workflow.py`

## Findings

- ATTEMPT-007 correctly targets ATTEMPT-004 DR-035 `direction_sample_h48_w0.525_a0.005` as `same_seed_min3_exact_repeat`.
- `source_seed=5`; pre-run plan, manifest, result stub, helper profile, and test all expect three jobs with seeds `[5, 5, 5]`.
- No ATTEMPT-005 seeds 6/7/8 are reused as exact repeat.
- Planned GZSL split, class order, label mapping, logits shape, evaluator, and GZSL U/S/H/ZS metric semantics are unchanged.
- Helper-generated DR035 jobs fix `local=fixed`, `icsa=fixed`, `direction=sample`, `pse=fixed`, `hidden=48`, `anchor=0.005`, `weight_s2v=0.525`.
- Warning: `config.yaml` is the base config; Runner must inspect generated `configs/DR-001.yaml`, `DR-002.yaml`, and `DR-003.yaml` after batch planning.

## Required Before Runner

- Generate the frozen batch and inspect the generated per-job configs before launch.
- Update runtime gate pre-run checks to allow/pass.
- Re-run `validate-agent-runtime --path agent_runtime.yaml`.
- Do not start while the Runner Monitor reports the v5 run is still occupying GPU slots.
