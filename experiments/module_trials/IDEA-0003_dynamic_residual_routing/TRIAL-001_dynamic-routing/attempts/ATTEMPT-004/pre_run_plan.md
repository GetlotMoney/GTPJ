# ATTEMPT-004 Pre-Run Plan

## Scope

- Trial: IDEA-0003 / TRIAL-001 Dynamic Residual Routing
- Subject id: ATTEMPT-004
- Planned server run: RUN-20260702-0002-dr018-confirm-ablate50-2gpu
- Workflow profile: dr018-confirm-ablate
- Base version: v5
- Batch size: 64
- Config epochs field: 30
- Planned train epochs: 50
- Epoch schedule source: lr_stages
- LR stages: 20 + 20 + 10
- Seed: 5
- GPUs: 0,1

## Mini Start Card

```yaml
owner_phrase: 用现在的规范流程跑50组实验，创新和调参由 workflow 决定
task_type: mixed_experiment_campaign / trial-internal confirmation + ablation + tune + probe
base_version: v5
target: ATTEMPT-003 DR-018 direction_sample_h48_w0.5_a0.003
subject_id: ATTEMPT-004
evidence_state: interface_precheck_passed
writes: attempts/ATTEMPT-004 + Warehouse runtime artifacts after run
agent_mode: real_multi_agent
agent_instance_mode: temporary_subagent
gates: clean freeze commit, GZSL hard rules, epoch disclosure, artifact boundary, Top-3 checkpoint retention
next_action: generate frozen batch from the pre-run freeze commit, sync server, start two-GPU runner
```

## Rationale

ATTEMPT-003 produced a strong single result:

- DR-018 `direction_sample_h48_w0.5_a0.003`: H=74.86, U=73.10, S=76.71.
- DR-023 reproduced at mean H=74.60 over 3 runs.
- Static v5 control reproduced at mean H=74.49 over 3 runs.

This is `tune_promising`, not `min3_confirmed`. ATTEMPT-004 is designed to test whether
DR-018 is reproducible and whether the dynamic direction gate contributes beyond fixed
v5-like routing.

The initial launch id `RUN-20260702-0001-dr018-confirm-ablate50-2gpu` failed before any
training because the runner tried to call `conda` in a non-interactive server environment.
That failure is classified as a runner environment issue, not method evidence. The formal
rerun id after the runner fix is `RUN-20260702-0002-dr018-confirm-ablate50-2gpu`.

## Job Budget

50 total frozen jobs:

- 12 repeat / confirmation jobs:
  - DR-018 exact config x4.
  - DR-019 neighbor x3.
  - DR-016 neighbor x2.
  - DR-023 reproduced direction anchor x3.
- 10 ablation / control jobs:
  - static v5 control x3.
  - dynamic_fixed_all x2.
  - DR-018 with only `dynamic_direction_mode=fixed` x3.
  - DR-018 with `dynamic_gate_anchor_lambda=0.0` x2.
- 22 narrow direction tune jobs:
  - h48 grid around `weight_s2v` 0.45/0.475/0.50/0.525/0.55 and anchor 0.001/0.003/0.005.
  - h40/h56 neighborhood with `weight_s2v` 0.45/0.50/0.55 and anchor 0.003.
- 6 trial-internal mechanism probes:
  - direction + local.
  - direction + PSE.
  - local + direction + PSE.

The mechanism probes remain within TRIAL-001 because they only combine existing legal
dynamic routing switches. They are exploratory and cannot create a new version or promotion
claim by themselves.

## DR-018 Frozen Config

```yaml
use_dynamic_routing: true
dynamic_local_mode: fixed
dynamic_icsa_mode: fixed
dynamic_direction_mode: sample
dynamic_pse_mode: fixed
dynamic_gate_hidden: 48
dynamic_gate_anchor_lambda: 0.003
weight_s2v: 0.5
batch_size: 64
```

## Minimal Direction Ablation

The smallest legal direction-gate ablation changes only:

```yaml
dynamic_direction_mode: fixed
```

It must keep `use_dynamic_routing=true`, `dynamic_local_mode=fixed`,
`dynamic_icsa_mode=fixed`, `dynamic_pse_mode=fixed`, `dynamic_gate_hidden=48`,
`dynamic_gate_anchor_lambda=0.003`, and `weight_s2v=0.5`.

`use_dynamic_routing=false` is only the whole-module static sentinel and must not replace
the direction-gate ablation.

## Decision Gates

`min3_confirmed` for DR-018 requires:

- at least 3 clean repeats from the frozen DR-018 config;
- mean H >= 74.55;
- min H >= 74.40;
- max H - min H <= 0.50;
- no obvious U/S collapse.

`ablation_supported` requires:

- dynamic DR-018 mean H exceeds fixed-direction ablation mean H by at least 0.15;
- at least 2/3 comparable pairs are positive where pairing is available;
- U or S mean does not collapse by more than about 0.50 without compensating balance.

`stopped_repeat_unstable` if:

- repeat range exceeds 0.50;
- repeat mean fails to exceed the reference boundary;
- the best value is high but at least one repeat drops materially below the reference.

`stopped_ablation_not_supported` if:

- dynamic minus fixed-direction mean H is below +0.10;
- fixed/static controls match or exceed the dynamic gate;
- ablation is not single-factor.

## Evidence Boundary

Formal evidence can come only from:

- frozen plan/config generated from the pre-run freeze commit;
- server `summary.csv`, `summary.jsonl`, `batch_status.json`, `plan.json`, `events.jsonl`;
- Warehouse artifact URI/hash/size;
- ATTEMPT-004 `manifest.yaml`, `result.yaml`, `result.md`, `quality_check.md`, `agent_summary.md`;
- `TRANSITIONS.jsonl` and `evidence_routing.yaml`.

The 22 tune jobs and 6 probe jobs can produce `valid_single_run` or `tune_promising` only.
They cannot produce `confirmed`, `baseline-grade`, or `promotion` evidence without later
repeat and quality checks.

## Guardrails

- Keep `batch_size=64`.
- Do not use `dynamic_pse_mode=sample`.
- Keep dynamic ICSA frozen except the profile's explicit legal fixed settings.
- Do not change dataset split, class order, label mapping, metric semantics, evaluator, or logits contract.
- Retain only the Top-3 model checkpoints after completion.
- Do not promote from this batch unless repeat and ablation transitions both pass.

## Planned Commands

Generate the batch after this pre-run plan is committed:

```bash
python workflow/gtpj_workflow.py plan-dynamic-routing-batch \
  --trial-dir experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing \
  --base-config experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-004/config.yaml \
  --profile dr018-confirm-ablate \
  --run-id RUN-20260702-0002-dr018-confirm-ablate50-2gpu \
  --jobs 50 \
  --gpus 0,1 \
  --base-version v5 \
  --seed 5 \
  --python /data/lby/.conda/envs/dvsr_gpu/bin/python \
  --controller-python /usr/bin/python3
```

Then sync the frozen commit to `lab4090:/data/lby/projects/cv_project/GTPJ` and start the
formal rerun path after the runner fix:

```bash
cd /data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260702-0002-dr018-confirm-ablate50-2gpu
bash start_batch.sh
```
