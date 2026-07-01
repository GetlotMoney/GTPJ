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

角色别名必须映射到稳定 `role_key`，避免侧栏显示名、summary 名称和规范名互相漂移：

```yaml
role_aliases:
  Workflow Coordinator:
    role_key: coordinator
    zh_name: 工作流总控
  Campaign Planner:
    role_key: campaign_planner
    zh_name: Campaign 规划
  Experiment Runner:
    role_key: runner
    zh_name: 实验运行者
  Runner Monitor:
    role_key: runner_monitor
    zh_name: 运行监控
  Log Analyst:
    role_key: log_analyst
    zh_name: 日志分析
  Log Metric Parser:
    role_key: log_analyst
    zh_name: 日志指标解析
  Quality Checker:
    role_key: quality_checker
    zh_name: 质量检查
  Evidence Quality Checker:
    role_key: quality_checker
    zh_name: 证据质量检查
  Result Analyst:
    role_key: result_analyst
    zh_name: 结果分析
  Result Comparator:
    role_key: result_analyst
    zh_name: 结果比较
  Interface Checker:
    role_key: interface_checker
    zh_name: 接口检查
  Reviewer:
    role_key: reviewer
    zh_name: 复核者
  Warehouse Registrar:
    role_key: warehouse_registrar
    zh_name: Warehouse 登记
```

实验类型：

- `tune`
- `ablation`
- `innovation`
- `confirmation`
- `promotion`
