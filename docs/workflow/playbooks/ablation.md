# 执行卡：消融 Ablation

正式入口固定为 `experiments/vX/ablation/INDEX.md`，人看编号为 `VX-ABLATION-xxx`。
必须从 `framework/vX` 开 `exp/vX/ablation/...` 分支；每个对照是一行 `RUN-xxx`。
消融只回答模块贡献，不生成子框架。

用于移除、替换、关闭或隔离既有组件。普通消融不新增方法模块；如果需要新增或改写
module、forward、loss、eval、data view 或接口语义，必须改走 innovation / module trial。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
docs/workflow/reference/GZSL_HARD_RULES.md
docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
docs/workflow/protocols/experiment_protocol.md
docs/workflow/protocols/code_interface_contract.md
产生 raw artifact 时读 docs/workflow/protocols/ARTIFACT_REGISTRATION.md
```

如果消融发生在 module trial 内部，还要读：

```text
docs/workflow/protocols/module_trial_protocol.md
```

## 角色

正式默认角色：

```text
总控 (Coordinator)
阅读/规划 (Reader/Planner)
接口检查 (Interface Checker)
运行监控 (Runner Monitor)
日志分析 (Log Analyst)
证据质量检查 (Evidence Quality Checker)
结果比较 (Result Comparator)
```

只有需要添加关闭开关、旁路或空路径时才加入 `实现者 (Implementer)`。如果实现者要新增或改写
方法模块，本任务必须停止并重新路由为 innovation / module trial。

正式 Runner 启动前必须写 `agent_runtime.yaml` 并通过 `validate-agent-runtime` 和
`multi-agent-preflight`。
Interface / Quality / Runner Monitor 没有独立 allow/pass 时，不得把消融结果作为正式证据。

## 阻断门

- label mapping、seen/unseen split、class order、logits shape 或 metric semantics 不清楚。
- 消融暗中改变了目标组件之外的东西。
- 消融需要新增或改写模块代码、forward、loss、eval、data view 或接口语义；这种情况不是普通消融。
- 要和 unconfirmed baseline 比较，却没有标出这个边界。

ablation 只有在组件贡献证据成立时才能进入 `ablation_supported`；如果消融不支持贡献，必须记录
`stopped_ablation_not_supported` 或 `rejected` transition。

## 参数矩阵（2026-08-04 起）

消融也必须逐任务登记到 `PARAMETER_MATRIX.csv`：每行写清关掉或替换了哪个因素、对照是什么、随机种子、配置指纹、结果和最终判断。批次摘要不能替代逐行表。重复运行相同消融时必须标明 `repeat_of`，完整规则见 `docs/workflow/protocols/parameter_matrix_protocol.md`。
