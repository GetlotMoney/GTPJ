# 模块 Trial 协议

模块 trial 放在：

```text
experiments/module_trials/
```

权威 idea 记录放在：

```text
idea_tree/ideas/IDEA-xxxx_short_name/IDEA.md
```

模块代码改动必须遵守：

```text
docs/workflow/code_interface_contract.md
docs/workflow/innovation_code_review_protocol.md
```

分支和 tag 命名必须带 base version：

```text
code_branch: dev/v1-idea-0001-trial-001-short-name
code_tag: trial/v1/idea-0001/trial-001
```

`code_tag` 是 trial 级代码快照，不是 attempt 级结果标签。一个 `TRIAL-xxx`
最多使用一个 trial 级 `code_tag` 来标识这条实现线；`ATTEMPT-xxx` 不创建 git tag。

其中 `v1` 表示这个 trial 的代码来源是 `v1` baseline tag。临时分支仍从当前
`main` 开出，以继承最新账本；如果当前 `main` 代码不是 `v1`，只恢复代码层到
`v1`，不要恢复账本层。
如果 trial 成功，它可以被提升为新的 `v2`、`v3` 或后续版本。

必需结构：

```text
experiments/module_trials/IDEA-xxxx_short_name/
|-- IDEA.md              # trial-local pointer to the source idea file
`-- TRIAL-001_short_name/
    |-- README.md
    |-- ATTEMPTS.md
    |-- framework_diagram.md
    |-- implementation.md
    |-- code.diff
    |-- idea_intent_check.md
    |-- interface_precheck.md
    |-- review_round_1.md
    |-- review_round_2.md
    `-- attempts/
        `-- ATTEMPT-001/
            |-- config.yaml
            |-- manifest.yaml
            |-- result.yaml
            |-- quality_check.md
            |-- result.md
```

每个 trial 必须记录：

- source idea file
- base version
- base code tag
- version-specific idea score
- framework diagram path and glossary
- insertion point
- input contract
- output contract
- shape invariants
- config switch and baseline-off path
- 如果触碰 loss/evaluation，记录对应 contract
- 最低验证证据
- code branch
- code tag
- attempts table
- best attempt id
- changed files
- implementation summary
- framework diagram with every key variable and method explained
- Review 0 idea/source intent check
- Review 1 design/interface precheck
- Review 2 code diff pre-run review
- Review 3 post-run evidence review
- quality check decision
- result
- `trial_decision`
- `promotion_decision`

## Trial-internal attempts

The same module trial may include multiple attempts, but they must stay within the same implementation hypothesis.

Use `ATTEMPTS.md` as the human-readable index for trial-internal parameter tuning, narrow follow-up ablations, confirmation/reruns, and debug-fix reruns.

Trial-internal tuning and ablation are required parts of judging whether a new module is useful. They stay inside the trial because they answer:

```text
在同一个模块实现假设下，这个模块怎样设置才公平？
这个模块内部哪些局部因素真的有贡献？
当前 best attempt 是否能 clean confirmation？
```

They are not version-level tune or ablation runs. Do not record them under `experiments/vX/tune/`,
`experiments/vX/ablation/`, or `experiments/vX/confirmation/` unless the task is explicitly a standalone
baseline-version experiment outside the module trial.

Recommended table:
```text
| Attempt ID | Type | Parameter / Change | Old | New | Seed | U | S | H | ZS | Best epoch | Log artifact | Decision | Directory |
```

Recommended `Type` values:
```text
param_tune / ablation / confirmation / rerun / anchor_followup / debug_fix
```

Each `attempts/ATTEMPT-xxx/` directory should keep its own:
- `config.yaml`
- `manifest.yaml`
- `result.yaml`
- `quality_check.md`
- `result.md`

Before any real attempt run, trial-internal bookkeeping follows the same two-stage evidence rule:

## Innovation code review gate

如果 module trial 会把 idea、论文机制、官方代码或本地创新改成实际代码，必须先通过
`docs/workflow/innovation_code_review_protocol.md`：

```text
Review 0 -> idea_intent_check.md
Review 1 -> interface_precheck.md
Review 2 -> review_round_1.md + interface_check.md + quality_check.md
Review 3 -> review_round_2.md + agent_summary.md
```

这些文件是轻量审查凭证，允许进入 GitHub。完整长报告、日志和大文件仍进入 Warehouse。

### Framework diagram gate

新 module trial 的框架图是实现说明的一部分，不是可选插图。

每个新 trial 必须在 `README.md` 的 `## Framework Diagram` 中引用对应目录下的
`framework_diagram.md`。如果同时生成 HTML 视图，稳定小型 HTML 可以放在 trial 目录；
临时或较大的 HTML 进入 `GTPJ_Warehouse/diagrams/`，`framework_diagram.md` 记录
`file:///D:/...` 链接、artifact id、哈希或说明。

`framework_diagram.md` 必须解释：

- 每个图中变量的来源、shape、含义、是否参与梯度、train/eval 差异；
- 每个图中方法/模块的代码位置、输入、输出、职责和开关条件；
- 主 forward 链路、辅助 loss 链路、teacher/target/source、detach/梯度边界；
- 每个 loss 在流程中的读取位置，不能只把 loss 名集中列在末尾；
- 代码实际流程与 idea/设计图是否一致，不一致时必须显式标注 “code vs intent”。

硬规则：

- 没有 Review 0 和 Review 1，不得开始实现；
- 没有 Review 2 通过，不得启动正式 Runner；
- 代码修复后必须重做相关 review；
- 没有 Review 3，不得把结果标成 best、promote 或主线候选；
- 如果真实多 agents 工具不可用，本任务不得冒充 `real_multi_agent`，只能阻断或降级为 debug/smoke。

### `pre-run freeze commit`

Before Runner starts, first freeze into Git:

- the target `attempts/ATTEMPT-xxx/config.yaml`
- the planned row in `ATTEMPTS.md`
- any required task-start card or attempt note that explains what this run will do

Hard rules:

- Runner must start from a clean worktree after this commit;
- the attempt `run_commit` must point to this freeze commit;
- this commit must not pre-fill the run's `manifest.yaml`, `result.yaml`, `result.md`, `quality_check.md`, metrics, or artifact registration.

### `post-run result commit`

After the attempt finishes, write the attempt-local:

- `manifest.yaml`
- `result.yaml`
- `result.md`
- `quality_check.md`

and then update the trial root summary and indexes in a separate result-bookkeeping step.

After the attempt finishes and before result bookkeeping is considered complete, apply checkpoint retention:

- keep at most 3 model checkpoints for the attempt, batch, or run;
- keep the top 3 by the attempt's primary validation metric, defaulting to GZSL-H;
- delete only model weight files such as `.pth`, `.pt`, `.ckpt`, or `.safetensors`;
- never delete raw logs, configs, manifests, results, quality checks, runner receipts, events, summaries, or
  Warehouse registry entries;
- if more than 3 checkpoints must be kept for promotion, reproducibility diagnosis, or owner-requested audit,
  record the exception in the attempt `quality_check.md`.

Rules:
- `TRIAL-001` is one implementation line for one idea, not one training run.
- `ATTEMPT-001`, `ATTEMPT-002`, and later rows are repeated runs or small controlled variations inside that same trial.
- Numeric-only changes such as ratio, lambda, temperature, dropout, seed, or scheduler stay inside the same trial as `param_tune`.
- A narrow diagnostic ablation that only helps explain the current trial may stay in the same trial as `ablation`.
- A clean rerun that confirms the current best attempt may stay in the same trial as `confirmation`.
- If the change becomes a new implementation hypothesis, a new forward path, or a new loss mechanism, open `TRIAL-002` instead of extending `TRIAL-001`.
- The trial root `README.md`, `result.yaml`, and `quality_check.md` should point to the current decision-driving `best_attempt_id` rather than trying to inline every attempt detail.
- Trial-internal attempts must not create git tags. Record the attempt with `best_attempt_id`,
  `attempts/ATTEMPT-xxx/`, `run_commit`, `record_commit`, and Warehouse artifact ids.
- Existing historical trials with only one root-level attempt may remain readable as legacy evidence, but any new attempt added after this rule should be recorded in `ATTEMPTS.md`.
- If a real attempt run starts while the worktree is dirty, or before the attempt config and planned `ATTEMPTS.md` row are frozen into Git, the result cannot be treated as promotion-ready evidence; at most it may be recorded as debug or `revise`.
- If same-config, same-seed confirmation attempts disagree across the decision boundary, record `mixed_confirmation`.
  The next attempt must be a reproducibility diagnosis or deterministic confirmation before any 10-run tune sweep.
  Keep model semantics frozen; only expose or enable controls such as `strict_determinism`,
  `use_dedicated_batch_rng`, and `batch_sampling_seed`, and ensure the training log prints those runtime states.

`trial_decision`：

```text
reject / revise / combine / promote
```

`promotion_decision`：

```text
not_applicable / promote / blocked / rejected
```

只有 `trial_decision: promote` 且 `promotion_decision: promote` 时，trial 才会进入
`docs/workflow/promotion.md` 的自动 promotion gate。
`H` 提升但证据不完整时，必须写 `revise`、`blocked` 或 `rejected`，不能写 `promote`。
单次最高 attempt 必须记录为 `best_observed_H`；只有 clean confirmation 或质量门要求的
多 run 稳定性通过后，才能升级为 `confirmed_H` 或 `baseline_grade`。
`mixed_confirmation` 状态下，`best_observed_H` 可以保留，但 `confirmed_H` 必须保持 `pending`。

Promotion 必填证据：

- parent version / parent tag；
- trial code tag；
- trial tag 指向 README 中记录的 code_commit；
- baseline H、trial H、delta H；
- `evidence_level: baseline_grade`；
- `best_observed_H`、`confirmed_H` 和 `confirmation_status`；
- U/S/ZS、best epoch、seed；
- config 副本路径；
- 外部日志 artifact id、URI、sha256、size 和保留位置；
- class order、seen/unseen split、logits shape、metric calculation 未改变的说明；
- switch-off 等价检查；
- `experiments/vX/VERSION.md`、`experiments/VERSION_TREE.md`、`docs/PROJECT_STRUCTURE.md`
  和 `idea_tree/idea_tree.json` 更新记录。
