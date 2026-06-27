# Progress Dashboard 协议

GTPJ 可以使用一个本地网页看板展示实验进度、agent 进度、GPU/Runner 状态和证据完整性。

核心边界：

```text
GitHub 文档和 experiments/ = 长期治理事实源和轻量结果索引
GTPJ_Warehouse = raw artifacts 长期事实源
agents = 执行者
.gtpj_runtime/ = 运行中状态
网页看板 = 只读展示层
```

网页看板不直接启动训练、不删除分支、不打 tag、不执行 promotion、不 push GitHub。

## Runtime 目录

运行中状态写入本地目录：

```text
.gtpj_runtime/
`-- runs/
    `-- RUN-YYYYMMDD-NNN/
        |-- status.json
        `-- events.jsonl
```

`.gtpj_runtime/` 是本地生成状态目录，不进入 Git。

实验结束后，长期轻量证据必须写回仓库账本，raw artifacts 留在 Warehouse：

```text
experiments/vX/tune/
experiments/vX/ablation/
experiments/vX/confirmation/
experiments/module_trials/
idea_tree/
docs/
```

## Coordinator 职责

每次用户明确启动某类实验后，Coordinator 必须：

1. 检查 Git 状态和 workflow 规则。
2. 创建或选择一个 `run_id`。
3. 创建 `.gtpj_runtime/runs/<run_id>/status.json`。
4. 创建 `.gtpj_runtime/runs/<run_id>/events.jsonl`。
5. 在每个关键阶段更新 `status.json`。
6. 在每个关键动作后追加 `events.jsonl`。
7. 实验结束后，把长期轻量证据写回 `experiments/`、`idea_tree/` 或 `docs/`；
   raw logs、checkpoint 和 generated figures 只写 Warehouse。

如果当前任务只是规划、审查或解释，不真正启动实验，不得创建 runtime run。

## status.json 最小字段

```json
{
  "run_id": "RUN-20260624-001",
  "experiment_type": "tune",
  "experiment_id": "TUNE-001",
  "base_version": "v1",
  "base_code_tag": "v1",
  "branch": "exp/v1-tune-001-topo008",
  "stage": "running",
  "gpu": "locked",
  "agents": {
    "coordinator": "waiting_runner",
    "reader_planner": "done",
    "runner": "running",
    "log_analyst": "idle",
    "quality_checker": "idle"
  },
  "evidence": {
    "readme": "missing",
    "config": "present",
    "log_artifact": "pending",
    "manifest": "pending",
    "quality_check": "pending",
    "result_yaml": "pending"
  },
  "metrics": {
    "U": null,
    "S": null,
    "H": null,
    "ZS": null,
    "best_epoch": null
  },
  "decision": "pending",
  "promotion_decision": "not_applicable"
}
```

字段可以扩展，但第一版看板不能依赖未定义字段才能工作。

## status.json 类型扩展字段

不同实验类型可以在 `details` 下补充展示字段。看板可以读取这些字段，但缺失时必须显示为
`unknown` 或 `not_applicable`，不能因此停止展示基础状态。

调参：

```text
details.parameter
details.old_value
details.new_value
details.candidate_count
```

消融：

```text
details.disabled_module
details.disabled_factor
details.switch_key
details.bypass_location
```

创新：

```text
details.idea_id
details.trial_id
details.idea_version_stage
details.trial_decision
```

重新复现：

```text
details.seed
details.dataset_split
details.cache_fingerprint
```

## events.jsonl 格式

每行一个 JSON 事件：

```json
{"time":"2026-06-24T10:00:00+08:00","agent":"coordinator","event":"run_created","message":"Created tune run RUN-20260624-001"}
{"time":"2026-06-24T10:05:00+08:00","agent":"runner","event":"started","message":"Started training command"}
```

事件只记录轻量摘要和路径，不复制大日志内容。

## 通用阶段

所有实验可以使用这些阶段：

```text
planning
waiting_user_choice
branch_ready
implementation
interface_check
running
log_parsed
result_analysis
quality_checked
reviewed
recorded
promotion_gate
done
blocked
failed
```

不是每类实验都需要所有阶段。看板应按实验类型隐藏不适用阶段。

## 四类实验联动

调参：

```text
Coordinator -> Reader/Planner -> 用户选择 -> Runner -> Log Analyst + Quality Checker -> Coordinator
```

看板重点显示：

- 最多 3 个候选建议；
- 用户选择的一个候选；
- Runner 串行和 GPU lock；
- `experiments/vX/tune/` 轻量证据完整性和 Warehouse artifact 状态。

消融：

```text
Coordinator -> Reader/Planner -> Implementer -> Interface Checker -> Runner -> Log Analyst + Quality Checker + Result Analyst -> Coordinator
```

看板重点显示：

- `disabled_module` 或 `disabled_factor`；
- `switch_key` 或旁路位置；
- `implementation.md`、`code.diff`、`interface_check.md` 是否存在；
- 接口检查是否通过；
- `experiments/vX/ablation/` 轻量证据完整性和 Warehouse artifact 状态。

创新：

```text
Coordinator -> Reader/Planner -> Implementer -> Interface Checker -> Runner -> Quality Checker + Result Analyst + Reviewer -> Coordinator
```

看板重点显示：

- `idea_id`、`trial_id` 和 base version；
- 是否来自 `idea_tree/versions/<base_version>.md` 的 selected idea；
- Review 0-3：`idea_intent_check.md`、`interface_precheck.md`、`review_round_1.md`、`review_round_2.md`；
- `activation_mode: real_multi_agent` 和必须独立执行的 reviewer roles；
- off switch、shape、loss、eval、logits 和 class order 检查；
- `experiments/module_trials/` 轻量证据完整性；
- `trial_decision` 和 `promotion_decision`。

重新复现：

```text
Coordinator -> Runner -> Log Analyst + Quality Checker -> Coordinator
```

看板重点显示：

- 固定 `base_code_tag`、config、seed、split 和 cache 口径；
- U/S/H/ZS、best epoch、log artifact；
- `experiments/vX/confirmation/` 轻量证据完整性；
- 复现失败原因和下一步建议。

## GPU / Runner 规则

- 同一块 GPU 同一时间只允许一个 Runner。
- Runner 开始前把 `gpu` 设置为 `locked`。
- Runner 结束、失败或被人工停止后，把 `gpu` 设置为 `free` 或 `unknown`。
- 多个 Reader、Log Analyst、Quality Checker 可以并行，Runner 不并行抢同一块 GPU。

## Promotion 联动

当实验记录写出：

```text
promotion_decision: promote
promote_to: vX
```

Coordinator 进入 `promotion_gate` 阶段，并按 `docs/workflow/promotion.md` 检查硬门。

看板只展示 gate 状态和阻塞项；不能由网页直接创建 tag、合并分支或 push。

## 看板实现边界

第一版推荐：

```text
后端：Python FastAPI
前端：React / Vite
刷新：2 秒轮询
数据源：status.json、events.jsonl、experiments/ 账本和 Git 状态
```

第一版不做：

- 网页启动训练；
- 网页 push；
- 网页删除分支；
- 网页打 tag；
- 网页执行 promotion；
- 网页直接编辑 GitHub 文档。
