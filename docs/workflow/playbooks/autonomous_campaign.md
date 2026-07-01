# 执行卡：全自动研究 Campaign

用于长期目标：用户只给论文来源、评估标准、安全边界和实验标准，工作流接管剩余过程。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
WORKFLOW_ROUTER.md
autonomous_research_campaign.md
如果请求包含多种实验类型，再读 mixed_experiment_campaign_protocol.md
```

## 用户输入

```text
论文/来源范围
评估指标和 baseline
安全边界
实验预算和停止条件
升版标准
最终交付标准
```

## 工作流负责

```text
论文读取
来源复核
idea 发现和排序
实验规划
代码修改
服务器运行
证据登记
repeat/confirmation
promotion proposal
最终结果和代码报告
```

## Agent 形态

使用 campaign-scoped real multi-agent。只有在可见长周期总控/监控连续性确实有用时，才额外加 `persistent_thread`。

正式证据仍然以文件为准。

## 最终交付

```text
最终实验表
最佳已确认框架和参数
失败方向及原因
代码/config diff 摘要
Warehouse artifact 索引
升版建议
剩余风险
```
