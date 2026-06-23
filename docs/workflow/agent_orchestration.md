# Agent 编排和长期管理

GitHub 保存长期规则。本地 `gtpj-workflow` skill 保存执行入口。两边规则必须同步。

## 长期 Agent 定义

长期保存的是 agent 角色、职责、读写边界、模板和交接格式。每次任务可以启动对应 agent 实例，
但不能依赖旧上下文记忆来维持正确性。

推荐本地 skill 结构：

```text
C:\Users\Administrator\.codex\skills\gtpj-workflow\
|-- SKILL.md
`-- references/
    |-- tune.md
    |-- ablation.md
    |-- innovation.md
    |-- confirmation.md
    |-- promotion.md
    |-- agent_registry.md
    `-- agents/
        |-- coordinator/
        |   |-- profile.md
        |   `-- handoff_template.md
        |-- reader_planner/
        |   |-- profile.md
        |   `-- recommendation_template.md
        |-- runner/
        |   |-- profile.md
        |   `-- run_report_template.md
        |-- implementer/
        |   |-- profile.md
        |   `-- implementation_report_template.md
        |-- interface_checker/
        |   |-- profile.md
        |   `-- interface_check_template.md
        |-- quality_checker/
        |   |-- profile.md
        |   `-- quality_check_template.md
        |-- log_analyst/
        |   |-- profile.md
        |   `-- metrics_report_template.md
        |-- result_analyst/
        |   |-- profile.md
        |   `-- decision_template.md
        `-- reviewer/
            |-- profile.md
            `-- review_template.md
```

每个 agent 文件夹至少包含：

- 定位；
- 适用实验类型；
- 必须先读的文件；
- 可以做什么；
- 禁止做什么；
- 输出格式；
- 交接格式。

## 角色

`Coordinator`

- 唯一总控。
- 分配 experiment ID、trial ID、分支和任务。
- 最后写账本、删除临时分支、执行自动 promotion。
- 唯一可以决定是否进入下一阶段。

`Reader / Planner`

- 读取 config、baseline、历史实验、idea tree 和相关论文。
- 给建议，不跑训练，不改 main。

`Runner`

- 按确认命令跑实验。
- 同一时间只允许一个 Runner 占用 GPU。
- 不负责解释是否 promotion。

`Implementer`

- 负责消融或创新中的代码改动。
- 只能改被分配的代码路径。
- 不能同时有多个 Implementer 改同一 trial 或同一实验代码路径。

`Interface Checker`

- 检查 shape、输入输出、loss、logits、labels、class order、mask 和 config 开关。
- 消融和创新必需。

`Quality Checker`

- 检查证据完整性、config、日志、结果、dirty state 和允许改动范围。

`Log Analyst`

- 解析日志，整理 U/S/H/ZS、best epoch、失败阶段和日志路径。

`Result Analyst`

- 判断 keep / reject / rerun / needs_confirmation / promote / blocked。

`Reviewer`

- 独立审查整条实验链，找污染、遗漏和误判。

## 四类实验编排

调参：

```text
Coordinator -> Reader -> 用户选择 -> Runner -> Log Analyst + Quality Checker -> Coordinator
```

训练串行，一次只跑一个。

消融：

```text
Coordinator -> Reader -> Implementer -> Interface Checker -> Runner -> Log Analyst + Quality Checker + Result Analyst -> Coordinator
```

消融可以改代码，但代码是临时实验代码，不自动进 `main`。

创新：

```text
Coordinator -> Reader -> Implementer -> Interface Checker -> Runner -> Quality Checker + Result Analyst + Reviewer -> Coordinator
```

创新 trial 从选中的 idea 开始，不从总创意表直接启动。

重新复现：

```text
Coordinator -> Runner -> Log Analyst + Quality Checker -> Coordinator
```

严格还原 config、seed、命令和数据口径。

Promotion：

```text
Coordinator -> Quality Checker + Interface Checker + Result Analyst -> Coordinator
```

当 `promotion_decision: promote` 且硬门通过时，Coordinator 自动创建本地版本材料和本地 tag。

## 禁止事项

- 多个 agents 同时写同一个 `INDEX.md`。
- 多个 agents 同时改同一实验代码路径。
- Runner 并行抢同一块 GPU。
- 非 Coordinator 删除分支、合并分支、创建 tag。
- 非用户明确要求时 push 到 GitHub。

## 同步规则

本文件和本地 `gtpj-workflow` skill 必须保持同一口径。

修改 workflow 规范时：

1. 先更新 GitHub 文档。
2. 同步更新本地 skill 的 `SKILL.md` 或 `references/`。
3. 运行 skill 校验。
4. 运行仓库验证。
5. 提交并推送 GitHub 文档。
