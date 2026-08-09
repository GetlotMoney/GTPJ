# 第一轮：历史真实性与实验有效性

```text
reviewer: experiment_validity_review
decision: allow
```

## 初审阻断

V5 动态路由参数表明确写着 `legacy_code_ref_not_preserved:ATTEMPT-006`，但最初的 `EXPERIMENT.yaml` 用宽泛 Trial 目录充当历史代码引用，会让人误以为准确代码仍可恢复。

## 修复与复核

- 改为 `historical_code_ref: not_preserved; evidence=IDEA-0003/TRIAL-001/ATTEMPT-006/INNOV-001..002`；
- 新增回归检查，参数表写明代码未保留时，禁止登记宽泛目录；
- 把检查接入正式框架账本校验；
- 审核者确认 V5 参数矩阵未改，历史 `module_trials` 子树哈希前后完全相同。

审核结论：历史真实性阻断已关闭。后续运行入口修复没有改动该事实；主助手又在最终 `fd69219` 上复核了相同子树哈希。
