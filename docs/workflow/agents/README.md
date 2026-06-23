# Workflow Agents

本目录是 GTPJ 长期 agent 编排的权威来源。

```text
shared_roles/       # 共享角色定义，只写一次
by_experiment/      # 每类实验如何调用共享角色
```

规则：

- 共享角色只在 `shared_roles/` 定义。
- 每个实验类型有自己的 `by_experiment/<type>/agents/README.md`。
- 实验类型目录只写调用顺序、启用角色、禁用角色和关键检查，不复制角色定义。
- 本地 `gtpj-workflow` skill 必须镜像本目录。

实验类型：

- `tune`
- `ablation`
- `innovation`
- `confirmation`
- `promotion`
