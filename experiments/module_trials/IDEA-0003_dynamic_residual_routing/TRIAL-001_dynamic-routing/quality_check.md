# Quality Check

```text
runtime: lab4090 post-run
quality_check_mode: STRICT
decision: revise
promotion_decision: rejected
evidence_level: valid_single_batch
confirmation_status: not_promoted
run_id: RUN-20260630-0005-dynroute50-2gpu
```

## Scope

Files and artifacts checked:

- `model/MyModel.py`
- `train_GTPJ_CUB.py`
- `workflow/gtpj_workflow.py`
- `tests/test_fae_memory_jepa.py`
- `tests/test_gtpj_workflow.py`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/config.yaml`
- `/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260630-0005-dynroute50-2gpu`
- `/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/module_trial/TRIAL-001/batch-RUN-20260630-0005-dynroute50-2gpu`

## Findings

- The 50-job server batch completed with 50 completed / 0 failed.
- The best overall job was the static v5 control, DR-001, at H=74.40.
- The best dynamic single job was DR-008, `local_class_h24`, at H=74.39.
- The best dynamic repeat source averaged H=74.23 over 5 repeats, below v4 confirmed H=74.47 and v5 repeat mean H=74.44.
- Direction gates produced the best follow-up signal: DR-023 reached H=74.38 with U=72.26 and S=76.63.
- Dynamic ICSA and broad combinations were unstable in this profile and should not be promoted.
- The batch summary files were copied from runtime storage into Warehouse summary storage and hashes were recorded.
- Server checkpoint retention was applied: 100 model checkpoint files were reduced to the top 3 by H.
- Raw logs, configs, status files, and summary artifacts remain outside Git; Git records pointers, hashes, and decisions only.
- `docs/diagrams/` is unrelated pre-existing untracked local content and remains excluded from this branch.

## Blocking Issues

None for recording the trial result.

Promotion is blocked because the repeat evidence does not exceed the reference targets.

## Checkpoint Retention Evidence

Retention policy:

```text
keep_scope: model weight files only
keep_count: 3
ranking_key: batch H descending
deleted_model_checkpoint_files: 97
retained_model_checkpoint_files: 3
```

Retained checkpoints:

| Job | H | SHA256 | Size bytes | Relative path |
|---|---:|---|---:|---|
| DR-001 | 74.40 | `56a3907af2bad5c7c33d930540de0e1e858348992c9c8d8c8c74ad1652b88729` | 102639770 | `attempt-001/logs/best_model_CUB_2026-06-30_16-11-11_H7440.pth` |
| DR-008 | 74.39 | `c6d3c89c6d66a918125bdbb064a752db2f0f88f18413c3721499a1e8c31a716c` | 102790288 | `attempt-008/logs/best_model_CUB_2026-06-30_16-38-54_H7439.pth` |
| DR-023 | 74.38 | `2799423888b755bf3db7d20045ab1f8f9f104adde55af152de69b35f8ae1c7e6` | 102790544 | `attempt-023/logs/best_model_CUB_2026-06-30_18-01-09_H7438.pth` |

## Artifact Hashes

| File | SHA256 | Size bytes |
|---|---|---:|
| `summary.csv` | `a32a748e55f810b9d1a6fa7d9f0d2cd0c7d2ab85adc41241266a6dcd4049cf20` | 15387 |
| `summary.jsonl` | `05f4e8804c9d60917acd6d20ac475b19218c2fc2974f08541beeb2c18c078905` | 37856 |
| `batch_status.json` | `5f32239fd3c94cade94b84a934b2f825f49261ee0a35bf089fbef113a5e02b44` | 36645 |
| `plan.json` | `6a10b493342024e23f60695cec23a9f98671521f5f9fff4319ee773b665cf0ca` | 27470 |
| `events.jsonl` | `b0e13f26dbf4e3c17406c6c19f0f6cc717ef19c717997df4bade2840b5defec5` | 19187 |

## Quality Checklist

- [x] Code snapshot and base version are explicit.
- [x] Config copy is saved in the trial directory.
- [x] Runtime batch status is lightweight and ignored by Git.
- [x] Batch summary files are copied into Warehouse and hash-recorded.
- [x] Server model checkpoint retention applied after the batch.
- [x] No eval/class order/logits shape change is declared or observed.
- [x] Seen/unseen split, label mapping, class order, and metric calculation are unchanged.
- [x] GitHub does not include raw logs, checkpoints, or generated runtime outputs.
- [x] Promotion decision is blocked/rejected in the ledger.

## Verification

Previously passed on this branch:

```bash
python -m pytest tests/test_fae_memory_jepa.py
python -m pytest tests/test_gtpj_workflow.py -q -k dynamic_routing
python -m py_compile model/MyModel.py workflow/gtpj_workflow.py train_GTPJ_CUB.py
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py audit-boundary
git diff --check
```

Post-run evidence commands:

```bash
python workflow/gtpj_workflow.py dynamic-routing-status --run-dir %TEMP%/gtpj-RUN-20260630-0005-dynroute50-2gpu
python workflow/gtpj_workflow.py analyze-dynamic-routing-batch --run-dir %TEMP%/gtpj-RUN-20260630-0005-dynroute50-2gpu --top-k 12
ssh -o ClearAllForwardings=yes lab4090 sha256sum <batch summary files>
```
