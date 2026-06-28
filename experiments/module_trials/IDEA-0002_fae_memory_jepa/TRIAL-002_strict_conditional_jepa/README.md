# TRIAL-002_strict_conditional_jepa

```text
trial_id: TRIAL-002
idea_id: IDEA-0002
base_version: v2
base_code_tag: v2
branch_source: dev/v2-idea-0002-trial-001-attempt-002-strict-conditional-jepa
idea_source_file: idea_tree/ideas/IDEA-0002_fae_memory_jepa/IDEA.md
idea_title: FAE-memory JEPA auxiliary loss
version_score: 72.0
applicability: needs_adaptation
code_branch: dev/v2-idea-0002-trial-002-strict-conditional-jepa
code_tag: trial/v2/idea-0002/trial-002
code_commit: c8daa9cb68edcaca3226fe8af3f7fb54757903e4
trial_decision: owner_accepted_to_v3
promotion_decision: owner_accepted_stochastic_tag
baseline_grade_promotion_decision: blocked
promote_to: v3
evidence_level: valid_single_run
best_observed_H: 74.27
confirmed_H: pending
confirmation_status: needs_confirmation
changed_files:
run_config: experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-002_strict_conditional_jepa/attempts/ATTEMPT-004/config.yaml
log_artifact_id: log:v2:module_trial:TRIAL-002:attempt-004
log_uri: warehouse://gtpj/runs/v2/module_trial/TRIAL-002/attempt-004/logs/training_log_CUB_2026-06-28_20-46-21.txt
log_sha256: 9d6dfb11c97ccab8cdab23608364f8efd81825390bc1773e10a0fbd18e415b3a
log_size_bytes: 91977
manifest: manifest.yaml
result_yaml: result.yaml
result_md: result.md
idea_intent_check: idea_intent_check.md
interface_precheck: interface_precheck.md
review_round_1: review_round_1.md
interface_check: interface_check.md
review_round_2: review_round_2.md
agent_summary: agent_summary.md
framework_diagram: framework_diagram.md
```

## Boundary Correction

TRIAL-002 was split out from TRIAL-001 because the strict path changes the trial implementation hypothesis:

- TRIAL-001 is the keep-only FAE-memory JEPA variant.
- TRIAL-002 is the strict main-path `jepa_memory` context plus conditional AG-JEPA text variant.

The historical runs originally recorded as TRIAL-001 ATTEMPT-002/003 are re-registered here as TRIAL-002 ATTEMPT-001/002. The raw logs and checkpoints are copied into TRIAL-002 Warehouse locations so later audits can follow the corrected trial identity.

## Changed Files

| File | Change | Code layer? |
|---|---|---|
| `model/MyModel.py` | Add `jepa_context_mode=fae_main_memory` and `jepa_text_mode=conditional` path | yes |
| `train_GTPJ_CUB.py` | Log JEPA context/text mode in training header | yes |
| `tests/test_fae_memory_jepa.py` | Add main-path memory and conditional-text probes | no |
| `config/GTPJ_cub_gzsl.yaml` | Make branch-local default config explicit for `fae_main_memory + conditional` | no |
| `attempts/ATTEMPT-001/config.yaml` | Strict main-path memory + conditional AG-JEPA text first run | no |
| `attempts/ATTEMPT-002/config.yaml` | Clean confirmation rerun of ATTEMPT-001 config | no |
| `attempts/ATTEMPT-003/config.yaml` | Same-config confirmation rerun; did not confirm 74-level result | no |
| `attempts/ATTEMPT-004/config.yaml` | Same-config confirmation rerun; reached 74-level result again | no |
| `attempts/ATTEMPT-005/config.yaml` | Reproducibility diagnosis with strict determinism and dedicated batch RNG | no |
| `attempts/ATTEMPT-006/config.yaml` | Exact deterministic rerun of ATTEMPT-005 | no |
| `attempts/ATTEMPT-007/config.yaml` | Seed-42 deterministic diagnosis rerun | no |
| `attempts/ATTEMPT-008/config.yaml` | Exact seed-42 deterministic diagnosis rerun of ATTEMPT-007 | no |
| `attempts/ATTEMPT-009/config.yaml` | Clean seed-42 deterministic rerun after config/diagram freeze | no |
| `attempts/ATTEMPT-010/config.yaml` | Exact clean rerun of ATTEMPT-009 | no |

## Results

| Dataset | Seed | U | S | H | ZS | Best epoch | Log |
|---|---:|---:|---:|---:|---:|---:|---|
| CUB | 5 | 71.22 | 77.60 | 74.27 | 81.38 | 33 | `log:v2:module_trial:TRIAL-002:attempt-004` |

ATTEMPT-009 and ATTEMPT-010 are retained as clean seed-42 stochastic-variance evidence: `H=74.14` and `H=74.01`.

## Confirmation Gate

| Attempt | Role | H | Decision |
|---|---|---:|---|
| ATTEMPT-002 | first clean confirmation | 74.24 | keep |
| ATTEMPT-003 | second same-config rerun | 73.81 | not_confirmed |
| ATTEMPT-004 | third same-config rerun | 74.27 | keep |
| ATTEMPT-005 | deterministic diagnosis rerun | 73.79 | not_confirmed |
| ATTEMPT-006 | exact deterministic diagnosis rerun | 73.91 | not_confirmed |
| ATTEMPT-007 | seed-42 deterministic diagnosis rerun | 73.94 | not_confirmed |
| ATTEMPT-008 | exact seed-42 deterministic diagnosis rerun | 73.83 | not_confirmed |
| ATTEMPT-009 | clean seed-42 deterministic rerun after config/diagram freeze | 74.14 | variance_evidence |
| ATTEMPT-010 | exact clean rerun of ATTEMPT-009 | 74.01 | variance_evidence |

The repeated confirmation evidence is mixed. Best observed strict result remains `H=74.27`, but stability is not proven because ATTEMPT-003 dropped to `H=73.81`; seed-5 deterministic diagnosis produced `H=73.79` and `H=73.91`; seed-42 deterministic diagnosis produced `H=73.94`, `H=73.83`, `H=74.14`, and `H=74.01`. The owner explicitly accepted this stochastic variance on 2026-06-28 and requested a formal `GTPJ-v3` tag. `confirmed_H` remains pending.

## Trial Flow

```mermaid
flowchart TD
  Idea["IDEA-0002: FAE-memory JEPA"] --> R0["Review 0: idea/source intent"]
  R0 --> R1["Review 1: design/interface"]
  R1 --> Impl["Implement strict main-path jepa_memory + conditional AG-JEPA text"]
  Impl --> R2["Review 2: code diff pre-run"]
  R2 --> A1["ATTEMPT-001 valid_single_run"]
  A1 --> A2["ATTEMPT-002 clean confirmation"]
  A2 --> A3["ATTEMPT-003 same-config rerun: not_confirmed"]
  A3 --> A4["ATTEMPT-004 same-config rerun: keep"]
  A4 --> A5["ATTEMPT-005 deterministic diagnosis: not_confirmed"]
  A5 --> A6["ATTEMPT-006 deterministic rerun: not_confirmed"]
  A6 --> A7["ATTEMPT-007 seed-42 deterministic diagnosis: not_confirmed"]
  A7 --> A8["ATTEMPT-008 seed-42 deterministic rerun: not_confirmed"]
  A8 --> Warehouse["Warehouse log/checkpoints/receipt"]
  Warehouse --> Attempt["attempt-local manifest/result/quality"]
  Attempt --> R3["Review 3: post-run evidence"]
  R3 --> Decision["trial_decision: owner_accepted_to_v3; best_observed_H=74.27; confirmed_H=pending"]
```

## Framework Diagram

```text
path: framework_diagram.md
html_view: file:///D:/Backup/Documents/Myself/GTPJ_Warehouse/diagrams/IDEA-0002_fae_memory_jepa_code_vs_intent.html
code_vs_intent: TRIAL-002 tests strict main-path jepa_memory plus conditional AG-JEPA text.
```

## Innovation Code Review

```text
Review 0: idea_intent_check.md
Review 1: interface_precheck.md
Review 2: review_round_1.md + interface_check.md + quality_check.md
Review 3: review_round_2.md + agent_summary.md
activation_mode: real_multi_agent for the original code semantic change; later frozen reruns use role_only Runner execution.
```

## Decision

TRIAL-002 is owner-accepted as `GTPJ-v3` by explicit stochastic-variance decision on 2026-06-28. ATTEMPT-004 remains the best observed strict result at `H=74.27`; deterministic and seed-42 reruns reached `H=73.79`, `H=73.91`, `H=73.94`, `H=73.83`, `H=74.14`, and `H=74.01`. This supports a formal owner tag but keeps `confirmed_H=pending` and blocks baseline-grade manuscript claims until a future confirmation/multi-seed protocol upgrades the evidence.
