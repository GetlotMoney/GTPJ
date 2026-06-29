# GTPJ-v4

```text
version: v4
baseline_name: GTPJ-v4
status: confirmed
code_tag: v4
parent_version: v3
parent_tag: v3
change_type: tune_config
based_on_trial: none
source_experiment: experiments/v3/confirmation/CONFIRM-001_local_v3_054_min3
source_candidate: local-v3-054
source_run: RUN-20260629-1722-server-gpu0-local-top2-min3
source_run_commit: 13529cb1d3ed8405e2f5cbb4832eff8d1c78db16
ledger_source: promote/v3-to-v4-local-v3-054
code_source: v3 code + confirmed tuned config
config: experiments/v4/config.yaml
baseline_evidence: experiments/v4/baseline/
evidence_level: baseline_grade
best_observed_H: 74.47
confirmed_H: 74.45
confirmation_status: confirmed
active_main_update: not_activated
owner_decision_date: 2026-06-29
owner_decision: min3-confirmed candidates automatically promote to formal versions; do not auto activate code.
```

## Current Modules

- Frozen CLIP ViT-L/14@336px backbone
- GPT text description prototypes
- PSE / CLIP-A-self sentence-level text prototype adapter
- FGVD geometry-aware visual memory
- BVSA bidirectional visual-semantic alignment
- ICSA conditional text adaptation
- SGMP auxiliary training

## Change From Base

`GTPJ-v4` promotes the min3-confirmed `local-v3-054` tuned configuration on top of `GTPJ-v3`:

- `pse_outer_ratio` / `clip_a_self_outer_ratio`: `0.15 -> 0.5`
- `local_weight`: `0.3 -> 0.1`

No model code, class order, seen/unseen split, label mapping, logits shape, or GZSL metric semantics are changed by this promotion.

## Results

| Dataset | Repeats | U mean | S mean | H values | confirmed_H | best_observed_H | ZS mean |
|---|---:|---:|---:|---|---:|---:|---:|
| CUB GZSL | 3 | 71.54 | 77.61 | 74.46 / 74.42 / 74.47 | 74.45 | 74.47 | 81.30 |

```text
evidence_level: baseline_grade
best_observed_H: 74.47
confirmed_H: 74.45
confirmation_status: confirmed
```

## Quality Notes

- The source confirmation completed 3 clean server repeats with H metrics.
- The GitHub record stores only config/result/manifest/quality evidence; raw logs and receipts remain in Warehouse.
- `GTPJ-v4` is a formal confirmed version. It does not automatically run `activate-version`.

## Version Tree Position

```text
parent_version: v3
children: none yet
notes: v4 = v3 code + local-v3-054 confirmed tuned config.
```

## Version Flow

```mermaid
flowchart TD
  V3["GTPJ-v3 tag v3<br/>best_observed_H=74.27<br/>confirmed_H=pending"] --> Tune["local-v3-054 tuned config"]
  Tune --> R1["rep01 H=74.46"]
  Tune --> R2["rep02 H=74.42"]
  Tune --> R3["rep03 H=74.47"]
  R1 --> V4["GTPJ-v4 tag v4<br/>confirmed_H=74.45"]
  R2 --> V4
  R3 --> V4
  V4 --> Active["active_main_update: not_activated"]
```

## Allowed Experiment Types

- `tune/`
- `ablation/`
- `confirmation/`
