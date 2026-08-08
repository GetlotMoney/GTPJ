# 候选框架验证规范审核记录

```yaml
review_tier: review-1
subject: SYS-WORKFLOW-V5 candidate-framework-validation-tree
scope: documentation_governance_only
status: pass_with_independent_codex_fallback
owner_approval: 2026-08-08，确认创新候选必须完成自身验证后才能晋级
server_training_touched: false
new_training_started: false
promotion_or_baseline_claim: false
```

## 本次要解决什么

旧说明把所有实验都写成直接从正式模板开始，无法严谨地验证“已经改过代码的创新候选”内部组件。本次明确两条起点：普通版本级实验从正式模板开始；候选内部实验从同一冻结候选提交独立开始。

候选没有完成完整对照、参数结论、必要消融和确认时，必须保持 `blocked`，不能直接生成新的正式框架。

## 审查过程

| 阶段 | 实例 | 结论 | 处理 |
|---|---|---|---|
| 前置只读审查 | `019fe14b-32f3-7000-8cbf-06e795acaa7f` | 请求修改：缺候选字段、晋级硬门、旧状态同步 | 已补齐候选根/子实验字段、四项晋级门和 `V5-ABLATION-001` 完成状态 |
| 差异只读审查 | `019fe153-e359-7922-aaac-fe4731af2cd7` | 请求修改：旧 trial 仍可直接升版本、入口仍引向 `new-trial` | 已把旧 trial/dev 降为历史回查，并改写 README、Quick Start、Router、启动卡 |
| 一致性只读审查 | `019fe15b-ae3c-7ee2-adc7-0673e0611b68` | 请求修改：旧 helper 仍要求实验分支包含 `main` | 已明确该 helper 不能启动新的正式实验，等待单独的模板绑定 helper 升级 |
| 最终只读验收 | `019fe15e-9528-7590-b2b5-a663f7ed73dc` | 通过 | 候选冻结、四项门、旧入口禁用和 helper 禁用说明一致 |

以上实例均已在完成后关闭；它们只读审查，没有编辑文件、启动训练或操作远端。

## 机器检查

```text
git diff --check                                      pass
conda run -n dvsr_gpu python workflow/gtpj_workflow.py validate
                                                       validate-ok
conda run -n dvsr_gpu python workflow/gtpj_workflow.py audit-boundary
                                                       audit-boundary-ok
关键入口旧规则检索                               无直接冲突
```

本发布分支的历史 helper 尚不含 `validate-ai-cross-review` 命令，因此不能伪造该命令通过。Claude Code 未在本次调用：owner 没有单独授权可能产生费用的外部审核；按项目 fallback 规则，使用了独立的只读 Codex 审查实例。这个限制不放宽任何训练、promotion 或 baseline 门槛。

## 最终决定

可以合并本次“规范与账本”文档更新到 `main`。合并后：

- `main` 采用候选框架验证树作为正式规范；
- 不启动新 GPU 训练，不碰服务器；
- 当前发布版 helper 不能创建新的正式模板实验或候选子实验；
- 模板绑定 helper 升级必须单独审核、测试和发布后，才允许用工具启动下一项正式实验。
