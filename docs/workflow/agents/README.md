# Workflow Agents

本目录是 GTPJ 长期 agent 编排的权威来源。

```text
shared_roles/       # 共享角色定义和长期角色记忆
by_experiment/      # 每类实验如何调用共享角色
long_term_memory.md # 长期 agent 记忆协议
```

规则：

- 共享角色只在 `shared_roles/` 定义。
- 每个共享角色必须同时有 `profile.md` 和 `memory.md`。
- 每个实验类型有自己的 `by_experiment/<type>/agents/README.md`。
- 实验类型目录只写调用顺序、启用角色、禁用角色和关键检查，不复制角色定义。
- 本地 `gtpj-workflow` skill 必须镜像本目录。
- 长期 agent = `profile.md` + `memory.md` + 调用协议 + 历史 `agent_summary.md` + issues。
- 临时 sub-agent / reviewer 实例是本轮 workflow 或 campaign 的活上下文；正式结果解释、best 选择和 promotion 必须回到文件化证据。
- `persistent_thread` 是跨 workflow 的可选活上下文，不是正式证据源。

实验类型：

- `tune`
- `ablation`
- `innovation`
- `confirmation`
- `promotion`
