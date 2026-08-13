# 执行卡：混合实验 Campaign

用于一次规划 tune、ablation、innovation、confirmation 的组合任务。

## 最短闭环

1. 把请求拆成四类 workstream，但每个真实训练仍只对应所属实验参数矩阵中的一行 `RUN-xxx`。
2. 先固定共享基线、预算、停止条件和 GPU 串行顺序。
3. 每个 workstream 按自己的 V6 执行卡运行，不建立平行结果账本或专用控制器。
4. 每个 RUN 结果直接回填所属 `experiments/vX/<type>/`；campaign 只保存轻量索引。
5. 汇总 completed/running/pending/failed、best single、进入复现的候选和下一步。

需要 exact repeat 的候选固定 `repeat_type: exact_repeat`、`original_seed`、`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`、`restore_target_H`、`near_miss_tolerance_H` 和 `near_miss_not_restored`。`seed_sweep`、`score_search`、`multi_seed_stability` 必须写 `not_confirmation_evidence: true`。

当前通用规则见 `START_HERE.md` 和 `WORKFLOW_KERNEL.md`。
