role_key: result_analyst
thread_title: ATTEMPT-018 | Result Analyst
decision: allow

# files_reviewed

- `AGENTS.md`
- `docs/workflow/START_HERE.md`
- `docs/workflow/WORKFLOW_KERNEL.md`
- `docs/workflow/playbooks/confirmation.md`
- `docs/workflow/agents/shared_roles/result_analyst/profile.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-017/result.yaml`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/task_start_card.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/pre_run_plan.md`

# decision_rules

本文件只给结果分析口径，不代表正式 Runner 已获准启动。正式启动仍必须由 Coordinator / Runner Monitor / Interface Checker / Evidence Quality Checker 等角色完成 `agent_runtime.yaml`、`validate-agent-runtime`、`multi-agent-preflight`、pre-run allow、干净冻结状态和服务器预检。

ATTEMPT-018 的目标是严格复现 ATTEMPT-017 的 best single：`A017DR095 / DR-095`，源结果为 `H=75.11, U=73.00, S=77.36, ZS=82.12, best_epoch=48`。本轮必须是 `exact_repeat`，固定 `original_seed: 5`、固定配置、固定数据/cache、训练日程、batch size 和评估口径；任何 seed 或参数变化都只能写成 `seed_sweep`、`score_search` 或 `multi_seed_stability`，且必须标注 `not_confirmation_evidence: true`。

`restored` 的边界：至少一个 clean completed/ok exact repeat 达到 `H >= 75.11`。一旦命中，记录 `best_hit: true`、`best_single_H` 和 `best_observed_H` 为本轮 clean repeat 最高 H，并按 `early_stop_on_best_hit: true` 停止后续 pending repeat。`restored` 回答的是“原始 best single 有没有原样跑回来”。

`near_miss_not_restored` 的边界：没有任何 clean exact repeat 达到 `H >= 75.11`，但至少一个 clean repeat 落在 `near_miss_tolerance_H: 0.2` 内，即 `74.91 <= H < 75.11`。这只能说明效果接近、有希望；在 5 次上限前不能停止，达到 5 次上限后也不能写成 restored、confirmation passed、stable confirmed 或 promotion evidence。

`not_restored` 的边界：同一候选最多 5 次 clean exact repeat 后仍无 `H >= 75.11`，且 best repeat 未进入 near-miss 区间时，收口为 `not_restored`。如果因为失败、接口语义不清、评估路径漂移、日志缺失或质量门阻塞导致不足以形成 clean exact repeat，不能硬判 `not_restored`，应转为 blocked / invalid / inconclusive，等待质量或运行角色定性。

`stable_confirm` 的边界：它不是单次命中，而是同一 `original_seed`、同一配置、同一评估语义下的 clean repeats 满足预设稳定性门槛，并能公开报告 mean/min/max/range。若只因首次命中就提前停止，本轮最多支持 `restored` / `best_hit`，不能自动写 `stable_confirm: true`。若有多条 clean repeat 在停止前已经完成，也必须完整报告弱 repeat，不能只展示最高值。

`best single` 与 `promotion-facing repeat mean` 必须分开：`best single` 是本轮 clean repeat 的最高单次 H，用来回答“有没有还原到过”；`promotion-facing repeat mean` 或 `confirmed_H` 是稳定确认口径，用来回答“能不能作为 baseline / promotion / paper claim 证据”。promotion 和 baseline claim 默认比较 repeat mean / confirmed_H，不能只凭 best repeat 或 `best_observed_H`。

ATTEMPT-017 的 DR-095 目前只能作为 `valid_single_run` 和 exact repeat 源候选；它不是 confirmation evidence。ATTEMPT-018 如果只拿到一次 clean 命中，可记录 restored / best_hit，但 promotion-facing 仍应写为未建立稳定 repeat mean，除非另有完整稳定性证据和质量门通过。

# blocking_issues

- 本 Result Analyst 规则准备本身未发现阻断项。
- 若后续 Runner 启动前缺少 `agent_runtime.yaml`、真实左侧命名线程、pre-run allow、`validate-agent-runtime`、`multi-agent-preflight` 或 clean pre-run freeze，则正式 confirmation 必须阻断。
- 若后续结果里出现 seed、配置、数据/cache、epoch schedule、batch size、评估脚本、label mapping、seen/unseen split、class order、logits shape 或 metric semantics 漂移，则该结果不能进入 restored / stable_confirm / promotion-facing 证据。

# non_blocking_warnings

- 当前任务是预备判定标准，未启动 Runner、未读取本轮运行日志，因此不能提前判断 ATTEMPT-018 是否 restored。
- `near_miss_not_restored` 很容易被误读成“基本复现”；本轮账本必须明确它不是复现通过，也不是停止理由，除非已经达到 5 次硬上限。
- 如果 5 个 repeat 并行/排队执行，命中后仍可能已有额外 completed repeat；这些结果不能隐藏，应纳入结果摘要，但是否构成 `stable_confirm` 仍取决于预设稳定性门槛和质量门。
- 当前仓库存在既有 dirty/untracked 状态；这不是本文件的写入阻断，但正式 Runner 启动应由对应角色重新检查并按 workflow 决定是否阻断。

# uncovered_scope

- 未读取 ATTEMPT-018 未来的 `result.yaml`、raw logs、Warehouse artifacts、batch status、events、server screen 状态或 completed job 输出，因为本线程任务是预跑结果判定标准。
- 未验证服务器 GPU、run 目录、screen、远端同步、artifact hash、checkpoint retention 或实际停止机制。
- 未执行 `validate-agent-runtime`、`multi-agent-preflight`、`git diff --check`、workflow validate 或任何测试命令。
- 未做 promotion 决策、版本 tag 决策、baseline claim 决策或论文 claim 决策；这些必须等待正式结果、质量检查和必要的稳定性证据。
