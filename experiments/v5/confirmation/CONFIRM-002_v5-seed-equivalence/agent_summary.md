# Agent 工作摘要

```text
experiment_id: V5-CONFIRM-002
run_id: pending
base_version: v5
base_template_commit: 2f5fa5e631ef82658d4bac587cdfd17f3534cb35
code_branch: exp/v5/confirmation/confirm-002-v5-seed-equivalence
code_commit: pending_candidate_commit
activation_mode: code_repair_pre_run
agent_instance_mode: temporary_read_only_reviewers
lifecycle: implementation_and_pre_run_review
required_roles: Coordinator, Implementer, Interface Checker, Quality Checker, Reviewer
required_real_agents: 4
agent_set: /root, /root/r5_recovery_audit, /root/scientific_semantics_review, /root/release_reliability_review
runner_status: not_started
formal_gpu_status: blocked_until_exact_freeze_and_server_zero_step
warehouse_report_artifacts: none_new
final_decision: code_candidate_pass_formal_gpu_blocked_until_freeze
review_rounds: 3
review_reason: 改动会改变模型初始化和训练轨迹，属于核心训练语义变更
```

## Coordinator / Implementer

```text
agent: /root
actions:
  - 从冻结 MODEL-V5-TEMPLATE-V1 的准确提交创建独立 CONFIRM-002 分支
  - 先添加会失败的同 seed 初始化测试，确认旧代码在 SGMP/ICSA 处失败
  - 在历史准确位置实现两个临时 Linear 的随机数兼容消耗
  - 明确两个对象不注册、不进入 forward、优化器和 checkpoint
  - 创建 README、implementation、code.diff、interface_check 和五行参数矩阵
machine_validation:
  - 修复前专项测试 FAIL，列出 SGMP/ICSA 六个不一致状态
  - 修复后专项测试 PASS
  - 全部 unittest 290/290 PASS（包含2项真实512→768 probe测试）
  - 可复用 probe 在实际 512→768 尺寸 active_state_mismatches=0，post_rng_equal=true
  - 错误 formal candidate commit 负测返回 BLOCK/exit 1
  - workflow validate/consistency/framework ledgers/templates/audit boundary 全部 PASS
decision: PASS_CODE_CANDIDATE
```

## 第一轮：随机数与代码可靠性

```text
agent: /root/r5_recovery_audit
mode: independent_read_only
decision: PASS
findings:
  - 临时 Linear 的位置、尺寸和顺序与历史 v5 完全一致
  - 全部活跃 state、模型构造后 CPU RNG、连续三次 randperm 完全相同
  - named_parameters/state_dict/AdamW 均不存在两个历史无用层
  - 把 helper 临时替换为空函数后测试会再次失败，排除假阳性
  - code.diff 与实际代码和测试 diff 逐字相同
remaining_gate: 在服务器固定 Python 下用准确候选提交运行正式模式零步指纹
```

## 第二轮：科学语义

```text
agent: /root/scientific_semantics_review
mode: independent_read_only
code_decision: PASS
initial_plan_decision: BLOCK_THEN_FIXED
initial_findings:
  - 单次 H>=74.40 不能证明修复，因为未修复组本来已有一次 H=74.48
  - 本轮不是 exact_repeat，result.yaml 也不能继续引用通用 74.54/74.44 基线
fix_response:
  - 主判据改为全部活跃 state 与 post-model RNG 精确一致
  - GPU 五次全部完成，报告 U/S/H/ZS 的 mean/min/max/range，不按 best hit 提前停止
  - repeat_type 改为标准 same_seed_repeat，并标记 diagnostic_subtype=code_repair、not_confirmation_evidence=true
  - 结果参考改为未修复均值 74.270 与老 V5 均值 74.462
final_incremental_review: PASS_CODE_CANDIDATE；正式GPU因尚未冻结继续BLOCK
```

## 第三轮：实验治理与可运行性

```text
agent: /root/release_reliability_review
mode: independent_read_only
branch_and_ledger_decision: PASS
formal_launch_decision: BLOCK_UNTIL_FREEZE
findings:
  - 分支、HEAD、模板分支和冻结 Tag 准确绑定 2f5fa5e，Tag 未移动
  - 五行 CSV 均为30列，job_id/run_id唯一，repeat_of有效，未伪造GPU结果
  - 缺少 repeat_type 等复跑字段；agent_summary 角色与实际代码改动不符
  - 正式命令、服务器环境、冻结提交和 frozen 状态尚未生成，因此现在不应启动GPU
fix_response:
  - 已补标准 same_seed_repeat、code_repair 子类型、非确认边界、seed、次数上限和不提前停止规则
  - 已如实启用并记录 Implementer、Interface Checker 与 Reviewer
  - 命令、环境和冻结提交继续保持 pending，等服务器零步指纹和候选提交完成后再生成
final_incremental_review: PASS_CODE_CANDIDATE；正式GPU因尚未冻结继续BLOCK
```

## 尚未启动的角色

```text
Runner: 未启动；没有GPU任务、收据或新Warehouse目录
Log Analyst: 等正式训练日志产生后启用
Result Analyst: 等五次U/S/H/ZS全部回填后启用
```

## 当前边界

三路审核不能代替服务器测试。当前只允许形成代码候选提交；在正式开跑前还必须完成：

1. 服务器实际 `512→768` 零步指纹；
2. 绑定准确候选提交的增量复核；
3. 明确服务器 Python/CUDA、训练命令和数据清单；
4. 把五行参数矩阵从 draft 冻结，并提交干净的 pre-run freeze commit；
5. 通过正式 Runner 启动门后才占用 GPU。
