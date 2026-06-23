# Tune Agents

调参只改变参数，不改变模型结构。训练串行，一次只跑一个 Runner。

## 启用角色

```text
Coordinator
Reader / Planner
Runner
Log Analyst
Quality Checker
```

## 禁用角色

```text
Implementer
Interface Checker
Reviewer
```

除非 Coordinator 明确发现调参请求已经变成代码结构改动，否则不启用这些角色。

## 编排

```text
Coordinator -> Reader/Planner -> 用户选择 -> Runner -> Log Analyst + Quality Checker -> Coordinator
```

## 关键规则

- Reader / Planner 先给最多 3 个调参建议。
- 用户只能选择 1 个建议进入本轮运行。
- Runner 只跑用户选中的一个实验。
- 当前版本从 `main` 开 `exp/vX-tune-...`。
- 历史版本从 `vX` tag 开临时运行分支。
- 长期证据只写 `experiments/vX/tune/`。
- 历史版本跑完证据回当前 `main`，然后删除临时运行分支。
- 如记录 `promotion_decision: promote` 和 `promote_to`，转交 promotion agents。
