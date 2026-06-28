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
trial_decision: keep
promotion_decision: blocked
promote_to:
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
| `attempts/ATTEMPT-001/config.yaml` | Strict main-path memory + conditional AG-JEPA text first run | no |
| `attempts/ATTEMPT-002/config.yaml` | Clean confirmation rerun of ATTEMPT-001 config | no |
| `attempts/ATTEMPT-003/config.yaml` | Same-config confirmation rerun; did not confirm 74-level result | no |
| `attempts/ATTEMPT-004/config.yaml` | Same-config confirmation rerun; reached 74-level result again | no |

## Results

| Dataset | Seed | U | S | H | ZS | Best epoch | Log |
|---|---:|---:|---:|---:|---:|---:|---|
| CUB | 5 | 71.22 | 77.60 | 74.27 | 81.38 | 33 | `log:v2:module_trial:TRIAL-002:attempt-004` |

## Confirmation Gate

| Attempt | Role | H | Decision |
|---|---|---:|---|
| ATTEMPT-002 | first clean confirmation | 74.24 | keep |
| ATTEMPT-003 | second same-config rerun | 73.81 | not_confirmed |
| ATTEMPT-004 | third same-config rerun | 74.27 | keep |

The repeated confirmation evidence is mixed. Latest observed best is `H=74.27`, but stability is not proven because ATTEMPT-003 dropped to `H=73.81`. Tuning, promotion, and tagging remain blocked until the owner explicitly accepts this variance or requests a new confirmation strategy.

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
  A4 --> Warehouse["Warehouse log/checkpoints/receipt"]
  Warehouse --> Attempt["attempt-local manifest/result/quality"]
  Attempt --> R3["Review 3: post-run evidence"]
  R3 --> Decision["trial_decision: keep; confirmation gate mixed; promotion_decision: blocked"]
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

TRIAL-002 remains a keep-worthy idea, but the confirmation gate is mixed: ATTEMPT-003 produced `H=73.81`, while ATTEMPT-004 produced `H=74.27`. This blocks the planned 10-run tuning sweep, formal promotion, and tagging until the owner explicitly accepts the observed variance or asks for a new confirmation strategy. The active v2 comparison value also remains an unconfirmed `best_observed_H=74.29`.
