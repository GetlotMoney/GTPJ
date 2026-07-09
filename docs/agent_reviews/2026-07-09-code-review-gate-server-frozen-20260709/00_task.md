task_id: code-review-gate-server-frozen-20260709
task_title: 代码审核不被 server_frozen_runner 豁免
scope: workflow/helper/skill gate: server_frozen_runner 只豁免训练运行期命名线程，不豁免代码、workflow、helper、template、训练配置生成逻辑的代码审核；同时拒绝 spawn_agent/right_sidebar 伪 thread id
risk_level: high
validation_profile: default-core
owner_participation: not_required
review_required: true
review_tier: strict-3
claude_rounds_required: 3
review_reason: 涉及 formal Runner 启动前安全门、代码审核门、skill mirror consistency 和 agent_runtime id 校验
acceptance_gates:
- machine_gates_passed: true
- codex_named_thread_pre_review: pass
- claude_rounds_required: 3
- unresolved_blocking_issues: 0
