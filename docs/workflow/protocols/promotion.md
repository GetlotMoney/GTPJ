# Automatic Promotion

Promotion 表示一个干净的框架/代码语义状态被接受为新的正式 baseline 版本。
promotion 会创建版本材料和版本 tag，但不会自动执行 `activate-version`。

纯调参不是 promotion。如果一次运行只改变 config 或超参数，它可以成为现有 `vX`
下的 confirmed config/reference，但不能创建新的正式 `vY`。

## Owner Standing Rule: Min3 Auto Promotion

从 2026-06-29 起，一个候选只有同时满足以下条件，才算可复现：

- 同一个 `source_job_id` 至少有 3 次成功 repeat；
- 每次 repeat 都是 completed/ok，并且有有效 U/S/H/ZS 指标；
- repeat 使用相同 code/config/evaluation contract；
- class order、seen/unseen split、label mapping、logits shape 和 metric semantics
  没有变化，或已经显式审计。

满足这些条件后，候选可以升级为 `baseline_grade` evidence。只有当该候选同时包含
框架/代码语义变化时，才允许自动 promotion 到下一个正式版本。如果只是 pure tune/config-only，
必须保留在父版本下作为 confirmed config/reference。

对 min3-confirmed 候选，正式结果行使用成功 repeat 中 H 最高的一次。该行记录为
`confirmed_H` / official H，并从同一次 repeat 取 official U/S/ZS。仍然必须记录
`H_mean`、`H_min`、`H_max` 和 repeat count 作为稳定性证据。单次高分不能在 min3
confirmation cluster 通过前成为 `confirmed_H`。

如果同时存在多个 min3-confirmed 候选，优先按 `confirmed_H` 选择最强 confirmed
config/reference，并用 repeat stability（`H_mean`、`H_min`、spread）作为护栏或平局判定。
不要把纯调参变成新的 `vX`。

## GitHub Push Boundary

promotion 在检查通过后可以创建本地文件、commit 和本地 tag。除非 owner 在验证后明确要求
（explicitly asks），否则不能把分支或 tag push 到 GitHub；硬标记：must not push。

即使 owner 明确批准 push，也仍然不允许：

- force-push;
- deleting remote refs;
- rewriting history;
- changing active code aliases;
- running `activate-version`.

## Promotion Does Not Activate Code

`promotion` 只创建类似 `v4` 的正式 version/tag。

`activate-version vX` 是单独动作。只有执行它之后，当前 runtime alias 或 active config
才能切换。如果还没有执行 `activate-version`，必须记录：

```text
active_main_update: not_activated
```

## Trigger Fields

result 记录以下字段后，才可以进入 automatic promotion：

```text
promotion_decision: promote
promote_to: vX
evidence_level: baseline_grade
confirmation_status: confirmed
```

对 min3 auto promotion，当上面的 min3 规则满足后，source confirmation 可以从
`confirmation_grade` 升级为 `baseline_grade`。对纯调参来说，这个升级只表示 confirmed
config/reference，仍然不能授权新的正式版本。

如果 owner 在没有 `baseline_grade` evidence 的情况下接受或激活某个候选，必须记录为
`owner_activated_unconfirmed` 或其它明确 provisional status。promotion gates 通过前，
不能把它转换成 confirmed formal version。

## Hard Gates

所有 gate 必须通过：

- source experiment/trial 记录 parent version、code source、branch、commit、
  config、command、metrics 和 artifact evidence；
- source experiment/trial 包含框架/代码语义变化；pure tune 必须留在现有版本下；
- source evidence 不能只是单次高点；
- 已记录或可推断 `dirty_state: clean` 和 `git_dirty: false`；
- metrics 包含 U、S、H、ZS、seed、best epoch 和 comparison reference；
- `best_observed_H`, `confirmed_H`, and `confirmation_status` are distinct;
- external artifact id、URI、sha256 和 size 已记录；
- `quality_check.md` 没有 blocking issue；
- GitHub 不包含 raw logs、checkpoints、generated figures 或 caches；
- target config 可以冻结到 `config/versions/vX.yaml`；
- 打 tag 和任何 owner 授权 push 前，当前 working tree 必须 clean。

任一 hard gate 失败时，不得创建正式版本。记录：

```text
promotion_decision: blocked
```

## Automatic Actions

所有 gate 通过后，Coordinator 应该：

1. Create a promotion branch from current `main`.
2. Copy or create the promoted config at `config/versions/vX.yaml`.
3. Create `experiments/vX/` and `experiments/vX/baseline/`.
4. Update `experiments/VERSION_TREE.md`.
5. Update `experiments/EXPERIMENT_REGISTRY.md`.
6. Update `docs/PROJECT_STATUS.md`.
7. 按需更新 `README.md` 和其它轻量索引。
8. Update helper canonical baseline metadata.
9. Run validation.
10. Commit the promotion ledger.
11. Create local tag `vX`.
12. Do not push the promotion branch or tag to GitHub unless the owner explicitly
    asks after validation.
13. Do not change active code aliases unless `activate-version vX` is explicitly
    requested.

## Required Version Record Fields

Every new version must record:

```text
version:
parent_version:
parent_tag:
code_tag:
ledger_source:
ledger_source_commit:
source_experiment:
source_trial:
change_type:
config_snapshot:
baseline_result:
known_risks:
confirmation_requirement:
evidence_level:
best_observed_H:
confirmed_H:
confirmation_status:
active_main_update: not_activated | activated_by_owner | owner_accepted_current_tag
```
