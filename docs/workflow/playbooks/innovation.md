# 执行卡：创新 / Module Trial

用于把论文机制或新想法落成可验证的模型、forward、loss、data view 或接口改动。

## 最短闭环

1. 明确 `base_code_tag`、机制假设、接入点和最小改动；没有明确基线时只做 idea discovery。
2. 选择最窄的 `module_template_selection.md` 模板，写 `module_source.md` 和实现契约。
3. 在 `PARAMETER_MATRIX` 中登记基线与首个真实 RUN，先做接口/shape/梯度/数据/评估机器检查。
4. 代码通过机器测试后，由两个不同只读子 Agent 依次完成两轮对抗式审核；两轮绑定同一 `reviewed_code_id`。
5. 从 clean、冻结的唯一 commit 运行到独立 RUN 目录，回填 U/S/H/ZS 和结论。

探索性 debug/smoke 只能证明链路可运行，不能作为 keep、best、confirmation 或 promotion 证据。

## 创新拆解与输出

```text
Paper -> Claim / Mechanism -> Hypothesis -> Attachment Point -> Trial -> Run
```

每项创新写入所属框架的 `experiments/vX/innovation/INNOVATION-xxx/`；创新经过 confirmation 并由 owner 接纳后，才注册新的同级正式框架和 Tag。需要长期推理时写入 Research；raw logs 和 checkpoint 写入 Warehouse。

`探索 / 正式分界`、`formal_evidence_allowed`、`validate-trial-meta`、`strict_template_entry` 等旧字段只用于读取历史记录，不是 V6 默认门。当前通用规则见 `START_HERE.md` 和 `WORKFLOW_KERNEL.md`。
