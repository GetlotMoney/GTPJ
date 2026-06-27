# Result Analyst Memory

## Standing Lessons

- keep/reject/rerun/promote 不能只看单个 H。
- 同时看 U、S、H、ZS、baseline delta、配置成本和是否需要 confirmation。
- trial 内部 attempt 的好结果不等于正式 baseline promotion。

## Recurrent Failure Modes

- 把 trial best tag 当成正式版本 tag。
- 忽略 U/S 差距，导致看不出 seen/unseen 偏移。
- 把 debug/smoke 或 dirty-tree run 当正式证据。

## Required Checks

- baseline comparison
- U/S/H/ZS
- seed and run_commit
- clean/dirty status
- trial decision versus promotion decision
- next action 是否写清。

## Update Rules

结果解释、promotion 边界或 next action 反复混乱时更新本文件。
